"""Ponte para o Azure DevOps de verdade (execução agendada, sem terminal interativo).

O portal roda no Chromium sem interface e chama o Azure como sempre (cabeçalho `Authorization` com o
token da organização). Aqui interceptamos essas chamadas e as repassamos de um processo Python.
O PAT de cada organização vem de uma de duas formas (a primeira que existir):

- variável de ambiente `AZURE_DEVOPS_PAT_<ORGANIZAÇÃO>` (ex.: AZURE_DEVOPS_PAT_VSUNICRED), para rodar fora da nuvem;
- credencial de API do ambiente da rotina: o proxy da rede injeta o cabeçalho por host + prefixo de caminho
  (ex.: dev.azure.com + /vsunicred/), então o PAT nem chega a este processo — a ponte só não envia `Authorization`.

Em qualquer dos casos:
- o token nunca entra na página (no navegador só existe um valor de enchimento em `AZ.tokens`), logo
  nunca é salvo em localStorage/IndexedDB nem aparece em log — coerente com a decisão 0007;
- a verificação de TLS continua ligada (usa o pacote de CAs do ambiente, que inclui a do proxy).
"""
import asyncio, base64, json, os, re, time
from urllib.parse import unquote, urlsplit

import requests

CORS = {"Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "authorization,content-type",
        "Access-Control-Allow-Methods": "GET,POST,OPTIONS"}
TENTATIVAS = 6   # por chamada, em 502/503/504 ou falha de rede
TENTATIVAS_ANTES_DE_DIVIDIR = 3   # histórico (Analytics): se repetir a mesma consulta pesada não resolve, divide o lote
IDS_NO_FILTRO = re.compile(r"(WorkItemId(?:%20|\+| )in(?:%20|\+| )\()([^)]*)(\))")
ENCHIMENTO = "token-so-na-ponte"   # o que o portal acha que é o token; a ponte troca pelo PAT real (ou o proxy injeta)


def var_do_token(org):
    return "AZURE_DEVOPS_PAT_" + re.sub(r"[^A-Z0-9]", "_", org.upper())


def pats_do_ambiente(orgs):
    """{org: pat ou None}. None = sem variável de ambiente: depende da credencial injetada pelo proxy."""
    return {o: (os.environ.get(var_do_token(o), "").strip() or None) for o in orgs}


class Ponte:
    def __init__(self, pats):
        self.pats = pats
        self.sessao = requests.Session()
        self.chamadas = 0
        self.retentativas = 0
        self.divisoes = 0
        self.espera = 2.0      # segundos × nº da tentativa, entre as novas tentativas de uma chamada
        self.bytes = 0
        self.t0 = time.time()

    def _org(self, url):
        seg = [s for s in urlsplit(url).path.split("/") if s]
        return seg[0] if seg else ""

    def _cabecalho(self, org):
        pat = self.pats[org]
        return {"Authorization": "Basic " + base64.b64encode(f":{pat}".encode()).decode()} if pat else {}

    def verificar(self, orgs):
        """Falha cedo, com mensagem clara, se alguma organização não autentica (PAT/credencial errados)."""
        ruins = []
        for o in orgs:
            try:
                r = self.sessao.get(f"https://dev.azure.com/{o}/_apis/projects?api-version=6.0&$top=1", headers=self._cabecalho(o), allow_redirects=False, timeout=60)
                ok = r.status_code == 200
            except requests.RequestException:
                ok = False
            if not ok:
                ruins.append(o)
        if ruins:
            raise SystemExit("Sem acesso ao Azure DevOps nas organizações: " + ", ".join(ruins) +
                             f". Confira a credencial de API do ambiente (host dev.azure.com e analytics.dev.azure.com, prefixo /<org>/) ou a variável {var_do_token('<org>')}.")

    async def rota(self, route):
        """Atende uma chamada do portal. Assíncrona: o portal dispara várias em paralelo (até 4) e o histórico do
        quadro (Analytics) é lento; atender uma por vez dividia a velocidade da carga por quatro."""
        req = route.request
        if req.method == "OPTIONS":
            return await route.fulfill(status=200, headers=CORS, body="")
        org = self._org(req.url)
        if org not in self.pats:
            return await route.fulfill(status=403, headers=CORS, body=f"organização {org} fora da configuração")
        hdr = self._cabecalho(org)
        if req.post_data:
            hdr["Content-Type"] = req.headers.get("content-type", "application/json")
        self.chamadas += 1
        dividivel = IDS_NO_FILTRO.search(req.url) is not None and "WorkItemRevisions" in req.url and req.method == "GET" and "skiptoken" not in req.url.lower()   # páginas seguintes não: dividir duplicaria linhas já lidas
        r, erro = await self._requisitar(req.method, req.url, hdr, req.post_data_buffer, TENTATIVAS_ANTES_DE_DIVIDIR if dividivel else TENTATIVAS)
        if dividivel and (r is None or r.status_code in (502, 503, 504)):
            # Erros passageiros do Azure (502/503/504) em consulta pesada do histórico: repetir a MESMA consulta não adianta
            # (o gateway estoura o tempo), então o lote de itens é dividido ao meio, recursivamente, e o resultado é remontado.
            ids = re.findall(r"\d+", unquote(IDS_NO_FILTRO.search(req.url).group(2)))   # unquote: o "2" de "%2C" não é um ID
            dados = await self._buscar_dividindo(req.url, hdr, ids)
            if dados is not None:
                self.bytes += len(dados)
                return await route.fulfill(status=200, headers={**CORS, "Content-Type": "application/json"}, body=dados)
        if r is None:
            return await route.fulfill(status=502, headers=CORS, body=f"falha de rede: {type(erro).__name__}")
        self.bytes += len(r.content)
        # o Azure responde 302 para a tela de login quando o PAT é inválido/sem escopo: vira 401 para o portal
        status = 401 if r.status_code in (301, 302, 303, 307, 308) else r.status_code
        return await route.fulfill(status=status, headers={**CORS, "Content-Type": r.headers.get("Content-Type", "application/json")}, body=r.content)

    async def _requisitar(self, metodo, url, hdr, corpo, tentativas):
        """(resposta|None, erro). Repete 502/503/504 e falha de rede, com espera crescente; o último erro é devolvido."""
        r = erro = None
        for tentativa in range(1, tentativas + 1):
            try:
                r = await asyncio.to_thread(self.sessao.request, metodo, url, headers=hdr, data=corpo, allow_redirects=False, timeout=180)
                erro = None
                if r.status_code not in (502, 503, 504): break
            except requests.RequestException as e:
                r, erro = None, e
            if tentativa < tentativas:
                self.retentativas += 1
                await asyncio.sleep(self.espera * tentativa)
        return r, erro

    async def _buscar_dividindo(self, url, hdr, ids):
        """JSON (bytes) com TODAS as linhas dos `ids`, buscadas em lotes menores; None se nem um item sozinho responder.
        Segue o @odata.nextLink dentro da ponte, então o portal recebe uma resposta única, sem paginação."""
        m = IDS_NO_FILTRO.search(url)
        sub = url[:m.start(2)] + "%2C".join(ids) + url[m.end(2):]
        r, _ = await self._requisitar("GET", sub, hdr, None, 2 if len(ids) > 1 else TENTATIVAS)
        if r is not None and r.status_code == 200:
            try:
                resp = r.json(); linhas = list(resp.get("value", []))
                while resp.get("@odata.nextLink"):
                    r, _ = await self._requisitar("GET", resp["@odata.nextLink"], hdr, None, TENTATIVAS)
                    if r is None or r.status_code != 200: raise ValueError("página seguinte falhou")
                    resp = r.json(); linhas += resp.get("value", [])
                return json.dumps({"value": linhas}).encode()
            except ValueError:
                pass
        if len(ids) < 2:
            return None
        self.divisoes += 1
        meio = len(ids) // 2
        a, b = await self._buscar_dividindo(url, hdr, ids[:meio]), await self._buscar_dividindo(url, hdr, ids[meio:])
        if a is None or b is None:
            return None
        # igual ao Azure: `$orderby=WorkItemId` (ordenação estável, então a ordem das revisões de cada item é mantida)
        return json.dumps({"value": sorted(json.loads(a)["value"] + json.loads(b)["value"], key=lambda x: x["WorkItemId"])}).encode()

    def resumo(self):
        return f"{self.chamadas} chamadas ao Azure ({self.retentativas} repetidas e {self.divisoes} lotes divididos por erro passageiro), {self.bytes / 1048576:.1f} MB, {int(time.time() - self.t0)}s"
