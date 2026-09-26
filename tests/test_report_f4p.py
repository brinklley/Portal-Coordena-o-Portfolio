"""Report F4P: cálculo de P95/P50, habilitação do painel e configuração (docs/regras-de-negocio.md §12)."""
from conftest import carregar

CTS = [10, 20, 25, 30, 35, 40, 45, 50, 60, 100]   # mesmos valores de tests/gerar_fixtures.py::f4p
P95_ESPERADO = 82.0     # PERCENTIL.INC(CTS, 0.95) calculado à mão
P50_ESPERADO = 37.5     # PERCENTIL.INC(CTS, 0.5)

def test_percentil_por_interpolacao_linear(page):
    assert abs(page.evaluate(f"percentil({CTS}, .95)") - P95_ESPERADO) < 1e-9
    assert abs(page.evaluate(f"percentil({CTS}, .5)") - P50_ESPERADO) < 1e-9
    assert page.evaluate("percentil([], .5)") is None

def test_p95_p50_conferidos_com_calculo_independente(page):
    carregar(page, "f4p.xlsx")
    m = page.evaluate("f4pMetrics('CORE')")
    assert m["n"] == len(CTS)
    assert abs(m["p95"] - P95_ESPERADO) < 1e-6
    assert abs(m["p50"] - P50_ESPERADO) < 1e-6
    assert abs(m["varr"] - P95_ESPERADO / P50_ESPERADO) < 1e-6

def test_aba_desabilitada_sem_time_e_roadmap(page):
    carregar(page, "f4p.xlsx")
    assert page.is_disabled("#f4pTab")
    page.evaluate("()=>{ S.f.team='CORE'; render(); }")
    assert page.is_disabled("#f4pTab")                       # só o time não basta
    page.evaluate("()=>{ S.f.exec=semestre(TODAY); render(); }")   # semestre atual
    assert not page.is_disabled("#f4pTab")
    page.click("#f4pTab")
    assert page.evaluate("F4P.open") is True
    page.evaluate("()=>{ S.f.exec=''; render(); }")          # remove um dos dois: recolhe
    assert page.evaluate("F4P.open") is False

def test_todos_os_times_aparecem_mesmo_com_time_filtrado(page):
    carregar(page, "times.xlsx")                             # 7 times
    page.evaluate("()=>{ S.f.team='CORE'; S.f.exec=semestre(TODAY); render(); }")
    page.click("#f4pTab")
    n_teams = page.evaluate("S.model.teams.length")
    cols = page.evaluate("document.querySelector('#f4pBody .f4p-tbl thead').querySelectorAll('th').length")
    assert n_teams > 1 and cols == n_teams

def test_quadrante_em_definicao_mostra_travessao_e_nota(page):
    carregar(page, "f4p.xlsx")
    page.evaluate("()=>{ S.f.team='CORE'; S.f.exec=semestre(TODAY); render(); }")
    page.click("#f4pTab")
    assert "Regra de cálculo ainda em definição." in page.inner_text("#f4pBody")

def test_ct_acima_do_maximo_fica_vermelho(page):
    carregar(page, "f4p.xlsx")
    page.evaluate("()=>{ CFG.teams={core:{max:20}}; S.f.team='CORE'; S.f.exec=semestre(TODAY); recomputeHealth(); render(); }")
    page.click("#f4pTab")
    assert page.evaluate("document.querySelector('#f4pBody .f4p-bad') !== null")

def test_amostra_do_semestre_atual_usa_janela_corrida(page):
    """Sem semestre selecionado, ou com o semestre em curso, a amostra é a janela corrida (últimos N meses)."""
    carregar(page, "f4p.xlsx")
    sem_semestre = page.evaluate("f4pMetrics('CORE')")
    com_semestre_atual = page.evaluate("()=>{ S.f.team='CORE'; S.f.exec=semestre(TODAY); return f4pMetrics('CORE'); }")
    for m in (sem_semestre, com_semestre_atual):
        assert m["n"] == len(CTS)
        assert abs(m["p95"] - P95_ESPERADO) < 1e-6
        assert abs(m["p50"] - P50_ESPERADO) < 1e-6
        assert abs(m["varr"] - P95_ESPERADO / P50_ESPERADO) < 1e-6

def test_amostra_ancora_no_semestre_passado_ja_encerrado(page):
    """Semestre já encerrado selecionado no filtro: a amostra passa a ser só o período daquele semestre.
    Usa um time só desta amostra (F4P_TESTE), acrescentado ao Map de itens sem tocar nos demais, para não
    interferir nas referências que os épicos da fixture já têm para os próprios itens."""
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      const curStart = f4pSemStart(semestre(TODAY));
      const prevMid = new Date(curStart.getFullYear(), curStart.getMonth() - 3, 15);   // meio do semestre anterior
      const prevSem = semestre(prevMid);
      S.model.ops.set("f4pTestePassado", {team:"F4P_TESTE", type:"User Story", deploy:prevMid, ct:40});
      S.model.ops.set("f4pTesteAtual", {team:"F4P_TESTE", type:"User Story", deploy:curStart, ct:999});   // no semestre atual: deve ficar de fora
      S.f.team = "F4P_TESTE"; S.f.int = prevSem;
      return {enabled: f4pEnabled(), metrics: f4pMetrics("F4P_TESTE"), prevSem};
    }""")
    assert r["enabled"] is True
    assert r["metrics"] == {"n": 1, "p95": 40, "p50": 40, "varr": 1.0}

def test_semestre_futuro_desabilita_e_fecha_o_painel(page):
    carregar(page, "f4p.xlsx")
    page.evaluate("()=>{ S.f.team='CORE'; S.f.exec=semestre(TODAY); render(); }")
    page.click("#f4pTab")
    assert page.evaluate("F4P.open") is True
    page.evaluate("""()=>{
      const curStart = f4pSemStart(semestre(TODAY));
      const future = new Date(curStart.getFullYear(), curStart.getMonth() + 12, 1);   // um ano à frente: sempre futuro
      S.f.exec = semestre(future); render();
    }""")
    assert page.is_disabled("#f4pTab")
    assert page.evaluate("f4pEnabled()") is False
    assert page.evaluate("F4P.open") is False              # estava aberto: recolhe sozinho

def test_valida_variabilidade_minima_maior_que_maxima(page):
    carregar(page, "times.xlsx")
    page.click("#btnCfg")
    page.fill('input[data-f4pteam="core"][data-f4pf="min"]', "4")
    page.fill('input[data-f4pteam="core"][data-f4pf="max"]', "3")
    page.click("#cfgSave")
    assert "variabilidade mínima precisa ser menor" in page.inner_text(".cfg-err")
    assert page.is_visible("#cfgBg")                          # não salvou

def test_configuracao_f4p_persiste_e_entra_na_exportacao(page):
    carregar(page, "times.xlsx")
    page.click("#btnCfg")
    page.fill("#cfgF4pMonths", "9")
    page.fill('input[data-f4pteam="core"][data-f4pf="min"]', "2")
    page.fill('input[data-f4pteam="core"][data-f4pf="max"]', "4")
    with page.expect_download() as d:
        page.click("#cfgExport")
    txt = open(d.value.path(), encoding="utf-8").read()
    assert '"months": 9' in txt and '"min": 2' in txt and '"max": 4' in txt
    page.click("#cfgSave"); page.wait_for_timeout(200)
    assert page.evaluate("CFG.f4p.months") == 9
    assert page.evaluate("CFG.f4p.teams.core") == {"min": 2, "max": 4}

def test_importar_configuracao_antiga_sem_f4p_usa_padrao(page):
    padrao = page.evaluate("()=>{ const c = normCfg({}); return {months:c.f4p.months, types:c.f4p.types, teams:c.f4p.teams}; }")
    assert padrao == {"months": 6, "types": ["user story", "technical story"], "teams": {}}
