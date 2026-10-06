"""Ponte para o Azure DevOps de verdade (execução agendada, sem terminal interativo).

O portal roda no Chromium sem interface e chama o Azure como sempre (cabeçalho `Authorization` com o
token da organização). Aqui interceptamos essas chamadas e as repassamos de um processo Python, com o
PAT lido de variável de ambiente (`AZURE_DEVOPS_PAT_<ORGANIZAÇÃO>`, ex.: `AZURE_DEVOPS_PAT_VSUNICRED`):

- o token nunca entra na página (no navegador só existe um valor de enchimento em `AZ.tokens`), logo
  nunca é salvo em localStorage/IndexedDB nem aparece em log — coerente com a decisão 0007;
- a verificação de TLS continua ligada (usa o pacote de CAs do ambiente, que inclui a do proxy).
"""
import base64, os, re
from urllib.parse import urlsplit

import requests

CORS = {"Access-Control-Allow-Origin": "*", "Access-Control-Allow-Headers": "authorization,content-type",
        "Access-Control-Allow-Methods": "GET,POST,OPTIONS"}
ENCHIMENTO = "token-so-na-ponte"   # o que o portal acha que é o token; a ponte troca pelo PAT real


def var_do_token(org):
    return "AZURE_DEVOPS_PAT_" + re.sub(r"[^A-Z0-9]", "_", org.upper())


def pats_do_ambiente(orgs):
    """{org: pat}. Falha com mensagem clara (sem mostrar valores) se faltar algum."""
    faltando = [var_do_token(o) for o in orgs if not os.environ.get(var_do_token(o), "").strip()]
    if faltando:
        raise SystemExit("Faltam variáveis de ambiente com o PAT: " + ", ".join(faltando) +
                         ". Cadastre-as como secrets do ambiente da rotina.")
    return {o: os.environ[var_do_token(o)].strip() for o in orgs}


class Ponte:
    def __init__(self, pats):
        self.pats = pats
        self.sessao = requests.Session()
        self.chamadas = 0

    def _org(self, url):
        sp = urlsplit(url)
        seg = [s for s in sp.path.split("/") if s]
        return seg[0] if seg else ""

    def rota(self, route):
        req = route.request
        if req.method == "OPTIONS":
            return route.fulfill(status=200, headers=CORS, body="")
        org = self._org(req.url)
        pat = self.pats.get(org)
        if not pat:
            return route.fulfill(status=403, headers=CORS, body=f"organização {org} sem PAT configurado")
        auth = "Basic " + base64.b64encode(f":{pat}".encode()).decode()
        hdr = {"Authorization": auth}
        if req.post_data:
            hdr["Content-Type"] = req.headers.get("content-type", "application/json")
        self.chamadas += 1
        try:
            r = self.sessao.request(req.method, req.url, headers=hdr, data=req.post_data_buffer, allow_redirects=False, timeout=180)
        except requests.RequestException as e:
            return route.fulfill(status=502, headers=CORS, body=f"falha de rede: {type(e).__name__}")
        # o Azure responde 302 para a tela de login quando o PAT é inválido/sem escopo: vira 401 para o portal
        status = 401 if r.status_code in (301, 302, 303, 307, 308) else r.status_code
        return route.fulfill(status=status, headers={**CORS, "Content-Type": r.headers.get("Content-Type", "application/json")}, body=r.content)
