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
    assert rel.inner_text(".an-title h3").replace("\n", " ") == f"Entregas previstas: Capacidade {esperado['cap']} US / Projetada {esperado['proj']} US"
    assert rel.eval_on_selector_all(".an-table tbody tr .ep .idb", "els => els.map(e => e.textContent)") == esperado["ids"]
    assert rel.eval_on_selector_all(".an-table .ct-ok, .an-table .ct-bad", "els => els.map(e => e.textContent)") == [f"CycleTime: {c if c is not None else '--'} Dias" for c in esperado["cts"]]
    page.context.close()

def test_relatorio_e_um_arquivo_unico_offline_e_sem_interacao_enganosa(gerado):
    h = gerado["html"]
    assert not re.search(r"<script[^>]*\ssrc=|<link[^>]*\shref=|@import|(src|href)=\"https?:", h), "recurso externo quebra o arquivo único"
    for grupo in ("Visão Analítica", "Actionable", "Report F4P"):
        assert f"<h2>{grupo}</h2>" in h
    tabela = h[h.index('<table class="an-table"'):h.index("</table>")]
    assert "<button" not in tabela and "data-sort" not in tabela      # nada clicável no arquivo estático
    assert "clicáveis" not in h                                       # a nota do rodapé não promete clique
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
