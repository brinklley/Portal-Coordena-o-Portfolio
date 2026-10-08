"""Gerador do relatório diário (scripts/relatorio/) — etapa 1: Visão Analítica de UM time. Decisão 0063.
O gerador roda como subprocesso, exatamente como a rotina agendada o chamará, contra o Azure simulado
(fixture fictícia `relatorio.xlsx`) e a configuração mínima abaixo — nunca contra dados reais."""
import asyncio, base64, json, re, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
import pytest
from conftest import ROOT, carregar

sys.path.insert(0, str(ROOT / "scripts" / "relatorio"))
import ponte_azure

def _exec(corrotina):
    """roda a corrotina num thread próprio: a sessão síncrona do Playwright (fixture `browser`) já ocupa o loop deste thread"""
    with ThreadPoolExecutor(1) as ex: return ex.submit(asyncio.run, corrotina).result()

GERADOR = ROOT / "scripts" / "relatorio" / "gerar_relatorio.py"
CFG_MINIMA = {"anTag": "ROADMAP", "azure": {"orgs": [], "sources": []}}

def _rodar(tmp_path, *extra, check=True):
    cfg = tmp_path / "config.json"; cfg.write_text(json.dumps(CFG_MINIMA), encoding="utf-8")
    r = subprocess.run([sys.executable, str(GERADOR), "--config", str(cfg), "--fonte", "simulado", "--fixture", "relatorio.xlsx",
                        "--saida", str(tmp_path / "saida"), *extra], capture_output=True, text=True, timeout=300)
    if check: assert r.returncode == 0, r.stderr + r.stdout
    return r

@pytest.fixture(scope="module")
def gerado(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("relatorio")
    r = _rodar(tmp, "--time", "MOBILE")
    arq = re.search(r"Gerado: (.+?\.html)", r.stdout).group(1)
    return {"arq": arq, "html": open(arq, encoding="utf-8").read(), "saida": r.stdout}

def test_relatorio_reproduz_exatamente_a_visao_analitica_do_portal(browser, gerado):
    # mesmo fuso do gerador (Brasília): "hoje" muda o CycleTime dos itens abertos, então precisa ser o mesmo dia
    page = browser.new_context(viewport={"width": 1500, "height": 950}, timezone_id="America/Sao_Paulo", locale="pt-BR").new_page()
    page.goto((ROOT / "dist" / "mapa_portfolio.html").as_uri()); page.wait_for_timeout(400)
    carregar(page, "relatorio.xlsx")
    esperado = page.evaluate("""() => {
      S.f.team = 'MOBILE'; S.f.int = semestre(TODAY); S.f.exec = ''; S.f.q = '';
      const d = anData(); return {cap:d.cap, proj:d.proj, ids: anSorted(d.rows).map(r => r.e.id), cts: anSorted(d.rows).map(r => r.m.ct)}; }""")
    assert esperado["cap"] > 0 and len(esperado["ids"]) > 3
    rel = page.context.new_page(); rel.goto("file://" + gerado["arq"])
    assert rel.inner_text("#va-mobile .an-title h3").replace("\n", " ") == f"Entregas previstas: Capacidade {esperado['cap']} US / Projetada {esperado['proj']} US"
    assert rel.eval_on_selector_all("#va-mobile .an-table tbody tr .ep .idb", "els => els.map(e => e.textContent)") == esperado["ids"]
    assert rel.eval_on_selector_all("#va-mobile .an-table .ct-ok, #va-mobile .an-table .ct-bad", "els => els.map(e => e.textContent)") == [f"CycleTime: {c if c is not None else '--'} Dias" for c in esperado["cts"]]
    page.context.close()

def test_actionable_e_report_f4p_reproduzem_exatamente_o_portal(browser, gerado):
    page = browser.new_context(viewport={"width": 1500, "height": 950}, timezone_id="America/Sao_Paulo", locale="pt-BR").new_page()
    page.goto((ROOT / "dist" / "mapa_portfolio.html").as_uri()); page.wait_for_timeout(400)
    carregar(page, "relatorio.xlsx")
    portal = page.evaluate("""() => {
      S.f.team = 'MOBILE'; S.f.int = semestre(TODAY); S.f.exec = ''; S.f.q = '';
      const texto = sel => [...document.querySelectorAll(sel)].map(e => e.textContent.trim().replace(/\\s+/g, ' '));
      openActionable(); const barras = [...document.querySelectorAll('#actBody .act-dist-row')].map(l => { const bar = l.querySelector('.act-dist-bar'); return [...bar.children].map(c => Math.round(c.getBoundingClientRect().width / bar.getBoundingClientRect().width * 100)); });
      const estilos = [...document.querySelectorAll('#actBody .act-dist-seg')].map(c => c.getAttribute('style'));
      const act = {barras, estilos, graficos: document.querySelectorAll('#actBody svg').length, rotulos: texto('#actBody svg text'), resumo: texto('#actBody .act-summary')}; closeActionable();
      openF4P(); const f4p = {celulas: texto('#f4pBody .f4p-tbl td'), colunas: texto('#f4pBody .f4p-tbl th')}; closeF4P();
      return {act, f4p}; }""")
    rel = page.context.new_page(); rel.goto("file://" + gerado["arq"])
    txt = lambda sel: rel.eval_on_selector_all(sel, "els => els.map(e => e.textContent.trim().replace(/\\s+/g, ' '))")
    assert portal["act"]["graficos"] == 3 and rel.locator("#act-mobile svg").count() == 3     # dispersão, burnup, CFD (a Distribuição é de barras em HTML)
    rel.evaluate("location.hash = '#act-mobile'"); rel.wait_for_timeout(200)       # só a seção aberta tem largura medível
    barras = rel.evaluate("""() => [...document.querySelectorAll('#act-mobile .act-dist-row')].map(l => { const bar = l.querySelector('.act-dist-bar'); return [...bar.children].map(c => Math.round(c.getBoundingClientRect().width / bar.getBoundingClientRect().width * 100)); })""")
    estilos = rel.eval_on_selector_all("#act-mobile .act-dist-seg", "els => els.map(c => c.getAttribute('style'))")
    assert barras == portal["act"]["barras"]                                  # larguras proporcionais iguais às do portal
    assert estilos == portal["act"]["estilos"] and all(e and "flex" in e for e in estilos) and estilos   # o style inline (largura) sobrevive à conversão botão → texto
    assert txt("#act-mobile svg text") == portal["act"]["rotulos"]
    assert portal["act"]["resumo"] and "reservado" in portal["act"]["resumo"][0]          # não vazio: antes comparava duas listas vazias
    assert txt("#act-mobile .act-summary") == portal["act"]["resumo"]
    assert txt("#f4p .f4p-tbl td") == portal["f4p"]["celulas"] and len(portal["f4p"]["celulas"]) > 8
    assert sorted(set(txt("#f4p .f4p-tbl th"))) == sorted(set(portal["f4p"]["colunas"])) and {"MOBILE", "CORE", "IB", "BO"} <= set(txt("#f4p .f4p-tbl th"))
    page.context.close()

def test_relatorio_e_um_arquivo_unico_offline_e_sem_interacao_enganosa(gerado):
    h = gerado["html"]
    assert not re.search(r"<script[^>]*\ssrc=|<link[^>]*\shref=|@import|(src|href)=\"https?:", h), "recurso externo quebra o arquivo único"
    for grupo in ("Visão Analítica", "Actionable", "Report F4P"):
        assert f"<h2>{grupo}</h2>" in h
    tabela = h[h.index('<table class="an-table"'):h.index("</table>")]
    assert "<button" not in tabela and "data-sort" not in tabela      # nada clicável no arquivo estático
    assert not re.search(r"[Cc]lique|clicáv", re.sub(r"<style.*?</style>", "", h, flags=re.S)), "sobrou frase que manda clicar"
    assert 'id="va-mobile"' in h and 'id="act-mobile"' in h and 'id="f4p"' in h and 'data-sort' not in h
    assert "Azure simulado" in gerado["saida"]

def test_time_sem_capacidade_no_roadmap_aborta_com_mensagem_clara(tmp_path):
    r = _rodar(tmp_path, "--time", "NAO_EXISTE", check=False)
    assert r.returncode != 0 and "não está comprometido" in r.stderr
    assert not (tmp_path / "saida").exists()           # nenhum arquivo parcial

def test_roadmap_inexistente_nos_dados_aborta(tmp_path):
    r = _rodar(tmp_path, "--roadmap", "1999 1º Semestre", check=False)
    assert r.returncode != 0 and "não existe nos dados carregados" in r.stderr

class _Rota:
    def __init__(self, metodo, url, hdr=None, corpo=None):
        self.request = type("Req", (), {"method": metodo, "url": url, "headers": hdr or {}, "post_data": corpo, "post_data_buffer": corpo.encode() if corpo else None})()
        self.resp = None
    async def fulfill(self, **kw): self.resp = kw

class _Resp:
    def __init__(self, status, corpo=b"{}"): self.status_code, self.content, self.headers = status, corpo, {"Content-Type": "application/json"}

def test_ponte_troca_o_token_de_enchimento_pelo_pat_real_e_responde_cors(monkeypatch):
    visto = {}
    ponte = ponte_azure.Ponte({"vsunicred": "PAT-DE-TESTE"})
    monkeypatch.setattr(ponte.sessao, "request", lambda m, u, **kw: visto.update(m=m, u=u, **kw) or _Resp(200, b'{"ok":1}'))
    pre = _Rota("OPTIONS", "https://dev.azure.com/vsunicred/_apis/projects"); _exec(ponte.rota(pre))
    assert pre.resp["status"] == 200 and pre.resp["headers"]["Access-Control-Allow-Origin"] == "*" and not visto
    r = _Rota("POST", "https://dev.azure.com/vsunicred/p/_apis/wit/wiql", {"authorization": "Basic " + base64.b64encode(b":" + ponte_azure.ENCHIMENTO.encode()).decode(), "content-type": "application/json"}, '{"q":1}')
    _exec(ponte.rota(r))
    assert visto["headers"]["Authorization"] == "Basic " + base64.b64encode(b":PAT-DE-TESTE").decode()
    assert visto["allow_redirects"] is False and r.resp["status"] == 200 and r.resp["body"] == b'{"ok":1}'

def test_ponte_converte_redirecionamento_de_login_em_401_e_barra_org_fora_da_configuracao(monkeypatch):
    ponte = ponte_azure.Ponte({"vsunicred": "x"})
    monkeypatch.setattr(ponte.sessao, "request", lambda *a, **k: _Resp(302, b"<html>login</html>"))
    r = _Rota("GET", "https://dev.azure.com/vsunicred/_apis/projects"); _exec(ponte.rota(r)); assert r.resp["status"] == 401
    outra = _Rota("GET", "https://dev.azure.com/outraorg/_apis/projects"); _exec(ponte.rota(outra)); assert outra.resp["status"] == 403

def test_pats_do_ambiente_le_so_o_que_existe_e_sem_pat_a_ponte_nao_envia_authorization(monkeypatch):
    monkeypatch.setenv("AZURE_DEVOPS_PAT_VSUNICRED", " segredo "); monkeypatch.delenv("AZURE_DEVOPS_PAT_UNICREDBR", raising=False)
    pats = ponte_azure.pats_do_ambiente(["unicredbr", "vsunicred"])
    assert pats == {"unicredbr": None, "vsunicred": "segredo"}
    visto = {}
    ponte = ponte_azure.Ponte(pats)
    monkeypatch.setattr(ponte.sessao, "request", lambda m, u, **kw: visto.update(kw) or _Resp(200))
    _exec(ponte.rota(_Rota("GET", "https://dev.azure.com/unicredbr/_apis/projects")))
    assert "Authorization" not in visto["headers"]      # o proxy do ambiente injeta a credencial dessa organização

def test_verificar_aborta_nomeando_a_organizacao_sem_acesso(monkeypatch):
    ponte = ponte_azure.Ponte({"unicredbr": None, "vsunicred": "x"})
    monkeypatch.setattr(ponte.sessao, "get", lambda u, **kw: _Resp(200 if "/unicredbr/" in u else 302))
    with pytest.raises(SystemExit) as e: ponte.verificar(["unicredbr", "vsunicred"])
    assert "vsunicred" in str(e.value) and "unicredbr," not in str(e.value) and "x" != str(e.value)

def test_ponte_atende_chamadas_em_paralelo(monkeypatch):
    """O portal dispara até 4 chamadas ao mesmo tempo; a ponte não pode serializá-las (o histórico do Analytics é lento)."""
    import time
    ponte = ponte_azure.Ponte({"unicredbr": None})
    monkeypatch.setattr(ponte.sessao, "request", lambda *a, **k: time.sleep(0.5) or _Resp(200))
    async def quatro():
        t = time.time()
        await asyncio.gather(*[ponte.rota(_Rota("GET", f"https://dev.azure.com/unicredbr/x{i}")) for i in range(4)])
        return time.time() - t
    assert _exec(quatro()) < 1.2       # em série seriam ~2s

def test_ponte_repete_so_a_chamada_com_erro_passageiro_e_nao_repete_erro_de_acesso(monkeypatch):
    """502/503/504 do Azure são repetidos dentro da ponte (o portal nunca vê); 401 e 404 passam direto na hora."""
    respostas = iter([_Resp(502), _Resp(503), _Resp(200, b'{"ok":1}')])
    ponte = ponte_azure.Ponte({"vsunicred": None}); ponte.espera = 0
    monkeypatch.setattr(ponte.sessao, "request", lambda *a, **k: next(respostas))
    r = _Rota("GET", "https://analytics.dev.azure.com/vsunicred/p/_odata/x"); _exec(ponte.rota(r))
    assert r.resp["status"] == 200 and r.resp["body"] == b'{"ok":1}' and ponte.retentativas == 2
    chamadas = []
    monkeypatch.setattr(ponte.sessao, "request", lambda *a, **k: chamadas.append(1) or _Resp(404))
    r = _Rota("GET", "https://dev.azure.com/vsunicred/p/_apis/y"); _exec(ponte.rota(r))
    assert r.resp["status"] == 404 and len(chamadas) == 1                  # erro "de verdade" não é repetido
    monkeypatch.setattr(ponte.sessao, "request", lambda *a, **k: _Resp(502))
    r = _Rota("GET", "https://dev.azure.com/vsunicred/p/_apis/z"); _exec(ponte.rota(r))
    assert r.resp["status"] == 502 and ponte.retentativas == 2 + (ponte_azure.TENTATIVAS - 1)    # desiste após o limite, devolvendo o erro

def _url_historico(ids, extra=""):
    return ("https://analytics.dev.azure.com/vsunicred/Proj/_odata/v4.0-preview/WorkItemRevisions?$filter=WorkItemId%20in%20(" + "%2C".join(map(str, ids)) + ")"
            "&$select=WorkItemId,Revision&$orderby=WorkItemId" + extra)

def _falso_analytics(max_ids):
    """consulta com mais de `max_ids` itens: 502 (gateway estourou); até isso: devolve 2 revisões por item"""
    def req(m, u, **kw):
        ids = [int(x) for x in re.findall(r"\d+", re.search(r"in%20\(([^)]*)\)", u).group(1).replace("%2C", ","))]
        if len(ids) > max_ids: return _Resp(502)
        return type("R", (_Resp,), {"json": lambda self: {"value": [{"WorkItemId": i, "Revision": n} for i in ids for n in (1, 2)]}})(200, b"{}")
    return req

def test_ponte_divide_o_lote_do_historico_quando_o_azure_da_502_e_remonta_a_resposta(monkeypatch):
    """O Analytics devolve 502 em consulta pesada (200 itens); repetir a mesma não adianta, então o lote é dividido ao meio."""
    ponte = ponte_azure.Ponte({"vsunicred": None}); ponte.espera = 0
    monkeypatch.setattr(ponte.sessao, "request", _falso_analytics(max_ids=2))
    r = _Rota("GET", _url_historico([12, 10, 14, 11, 13])); _exec(ponte.rota(r))   # ids fora de ordem: o resultado sai ordenado por WorkItemId, como no Azure
    corpo = json.loads(r.resp["body"])
    assert r.resp["status"] == 200 and "@odata.nextLink" not in corpo
    assert [(x["WorkItemId"], x["Revision"]) for x in corpo["value"]] == [(i, n) for i in (10, 11, 12, 13, 14) for n in (1, 2)]   # tudo, na ordem, sem duplicar
    assert ponte.divisoes >= 2

def test_ponte_nao_divide_pagina_seguinte_nem_esconde_item_que_nao_responde(monkeypatch):
    ponte = ponte_azure.Ponte({"vsunicred": None}); ponte.espera = 0
    chamadas = []
    monkeypatch.setattr(ponte.sessao, "request", lambda *a, **k: chamadas.append(1) or _Resp(502))
    r = _Rota("GET", _url_historico([1, 2, 3, 4], "&$skiptoken=abc")); _exec(ponte.rota(r))
    assert r.resp["status"] == 502 and len(chamadas) == ponte_azure.TENTATIVAS and ponte.divisoes == 0     # só repete; não divide página seguinte
    ponte.retentativas = 0; chamadas.clear()
    r = _Rota("GET", _url_historico([1, 2])); _exec(ponte.rota(r))                                          # nem um item sozinho responde: erro, não dado faltando
    assert r.resp["status"] == 502

def test_requirements_dev_lista_todas_as_dependencias_de_terceiros_do_gerador():
    """Achado no teste em produção da rotina: `requests` (usado pela ponte) não estava no requirements-dev.txt — no
    ambiente de quem desenvolve ele já existia por acaso, mas numa sessão nova a rotina quebrava com ModuleNotFoundError."""
    import ast
    pedido = (ROOT / "requirements-dev.txt").read_text(encoding="utf-8").lower()
    pacote = {"yaml": "pyyaml"}                                   # nome do import ≠ nome do pacote, se algum dia aparecer
    faltam = set()
    for arq in (ROOT / "scripts" / "relatorio").glob("*.py"):
        for no in ast.walk(ast.parse(arq.read_text(encoding="utf-8"))):
            nomes = [a.name for a in no.names] if isinstance(no, ast.Import) else [no.module] if isinstance(no, ast.ImportFrom) and no.module and no.level == 0 else []
            for n in nomes:
                raiz = n.split(".")[0]
                local = (ROOT / "scripts" / "relatorio" / f"{raiz}.py").exists() or raiz in ("azure_simulado",)    # módulos do próprio projeto
                if raiz not in sys.stdlib_module_names and not local and pacote.get(raiz, raiz).lower() not in pedido:
                    faltam.add(raiz)
    assert not faltam, f"importados pelo gerador mas ausentes de requirements-dev.txt: {sorted(faltam)}"
