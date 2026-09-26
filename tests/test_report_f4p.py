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
    padrao = page.evaluate("()=>{ const c = normCfg({}); return {months:c.f4p.months, types:c.f4p.types, expediteTag:c.f4p.expediteTag, teams:c.f4p.teams}; }")
    assert padrao == {"months": 6, "types": ["user story", "technical story"], "expediteTag": "urgent", "teams": {}}

# ---------------- Quadrante 3 · Urgente (meta vs. realizado) ----------------

def test_urgente_conta_so_itens_com_a_tag_configurada(page):
    carregar(page, "f4p.xlsx")
    n = page.evaluate("""()=>{
      S.model.ops.set("u1", {team:"F4P_URG1", type:"Bug", tagHits:[{id:"urgent"}]});
      S.model.ops.set("u2", {team:"F4P_URG1", type:"Bug", tagHits:[]});
      S.model.ops.set("u3", {team:"F4P_URG1", type:"Bug", tagHits:[{id:"paused"}]});
      S.f.exec = semestre(TODAY);
      return f4pUrgentRealizado("F4P_URG1");
    }""")
    assert n == 1

def test_urgente_semestre_atual_conta_abertos_e_fechados(page):
    carregar(page, "f4p.xlsx")
    n = page.evaluate("""()=>{
      S.model.ops.set("u1", {team:"F4P_URG2", type:"Bug", tagHits:[{id:"urgent"}], deploy:null});
      S.model.ops.set("u2", {team:"F4P_URG2", type:"Bug", tagHits:[{id:"urgent"}], deploy:TODAY});
      return f4pUrgentRealizado("F4P_URG2", {kind:"current"});
    }""")
    assert n == 2

def test_urgente_semestre_atual_ignora_fechados_fora_da_janela_de_meses(page):
    """Regressão relatada pelo usuário: a contagem estava somando todo item que já teve a tag em
    qualquer momento da história do time (ex.: 249 itens num time que usa a tag raramente), porque o
    Realizado do semestre em curso não tinha corte de data para itens já fechados. A janela correta é a
    mesma regra geral do Report F4P (f4pWindow/decisão 0013): últimos CFG.f4p.months meses corridos a
    partir de hoje — a mesma que CycleTime/Variabilidade já usavam, não uma nova âncora no início do
    semestre (decisão 0015)."""
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      S.f.exec = semestre(TODAY);
      const meses = CFG.f4p.months || 6;
      const foraDaJanela = new Date(TODAY.getFullYear(), TODAY.getMonth() - meses - 1, 15);   // antes da janela de N meses
      const dentroDaJanela = new Date(TODAY.getFullYear(), TODAY.getMonth() - 1, 15);          // dentro da janela de N meses
      S.model.ops.set("v1", {team:"F4P_URG4", tagHits:[{id:"urgent"}], deploy:foraDaJanela});   // fechado fora da janela: não conta
      S.model.ops.set("v2", {team:"F4P_URG4", tagHits:[{id:"urgent"}], deploy:dentroDaJanela}); // fechado dentro da janela: conta
      S.model.ops.set("v3", {team:"F4P_URG4", tagHits:[{id:"urgent"}], deploy:null});           // aberto há qualquer tempo: conta
      return f4pUrgentRealizado("F4P_URG4");
    }""")
    assert r == 2

def test_urgente_semestre_passado_conta_so_fechados_no_periodo(page):
    """Sem histórico de quando a tag foi aplicada, um semestre já encerrado só pode contar o que fechou
    (tem o.deploy) dentro daquele período — itens ainda abertos, ou fechados fora do período, ficam de fora."""
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      const curStart = f4pSemStart(semestre(TODAY));
      const prevMid = new Date(curStart.getFullYear(), curStart.getMonth() - 3, 15);
      const prevSem = semestre(prevMid);
      S.model.ops.set("u1", {team:"F4P_URG3", type:"Bug", tagHits:[{id:"urgent"}], deploy:prevMid});    // fechado dentro do semestre anterior
      S.model.ops.set("u2", {team:"F4P_URG3", type:"Bug", tagHits:[{id:"urgent"}], deploy:null});       // ainda aberto
      S.model.ops.set("u3", {team:"F4P_URG3", type:"Bug", tagHits:[{id:"urgent"}], deploy:curStart});   // fechado, mas no semestre atual
      S.f.int = prevSem;
      return f4pUrgentRealizado("F4P_URG3");
    }""")
    assert r == 1

def test_urgente_tendencia_compara_trimestres(page):
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      const recente = new Date(TODAY.getFullYear(), TODAY.getMonth() - 1, 15);   // dentro dos últimos 3 meses
      const antigo = new Date(TODAY.getFullYear(), TODAY.getMonth() - 5, 15);    // entre 3 e 6 meses atrás
      S.model.ops.set("a1", {team:"F4P_TREND_UP", tagHits:[{id:"urgent"}], deploy:recente});
      S.model.ops.set("a2", {team:"F4P_TREND_UP", tagHits:[{id:"urgent"}], deploy:recente});
      S.model.ops.set("a3", {team:"F4P_TREND_UP", tagHits:[{id:"urgent"}], deploy:antigo});
      S.model.ops.set("b1", {team:"F4P_TREND_DOWN", tagHits:[{id:"urgent"}], deploy:recente});
      S.model.ops.set("b2", {team:"F4P_TREND_DOWN", tagHits:[{id:"urgent"}], deploy:antigo});
      S.model.ops.set("b3", {team:"F4P_TREND_DOWN", tagHits:[{id:"urgent"}], deploy:antigo});
      S.model.ops.set("c1", {team:"F4P_TREND_FLAT", tagHits:[{id:"urgent"}], deploy:recente});
      S.model.ops.set("c2", {team:"F4P_TREND_FLAT", tagHits:[{id:"urgent"}], deploy:antigo});
      return {up: f4pUrgentTrend("F4P_TREND_UP"), down: f4pUrgentTrend("F4P_TREND_DOWN"), flat: f4pUrgentTrend("F4P_TREND_FLAT")};
    }""")
    assert r == {"up": "▲", "down": "▼", "flat": "◆"}

def test_urgente_meta_colore_vermelho_verde_ou_neutro(page):
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      S.model.ops.set("m1", {team:"F4P_META", tagHits:[{id:"urgent"}], deploy:null});
      S.model.ops.set("m2", {team:"F4P_META", tagHits:[{id:"urgent"}], deploy:null});
      S.model.ops.set("m3", {team:"F4P_META", tagHits:[{id:"urgent"}], deploy:null});   // 3 itens ao vivo
      S.f.exec = semestre(TODAY);
      CFG.f4p.teams.f4p_meta = {urgentMeta: 5};
      const dentroDaMeta = f4pUrgentCell("F4P_META");           // 3 <= 5
      CFG.f4p.teams.f4p_meta = {urgentMeta: 2};
      const acimaDaMeta = f4pUrgentCell("F4P_META");            // 3 > 2
      delete CFG.f4p.teams.f4p_meta;
      const semMeta = f4pUrgentCell("F4P_META");
      return {dentroDaMeta, acimaDaMeta, semMeta};
    }""")
    assert "f4p-good" in r["dentroDaMeta"] and "f4p-bad" not in r["dentroDaMeta"]
    assert "f4p-bad" in r["acimaDaMeta"]
    assert "f4p-good" not in r["semMeta"] and "f4p-bad" not in r["semMeta"]

def test_urgente_aparece_calculado_no_painel(page):
    carregar(page, "f4p.xlsx")
    page.evaluate("()=>{ S.f.team='CORE'; S.f.exec=semestre(TODAY); render(); }")
    page.click("#f4pTab")
    assert "Urgente (meta vs realizado)" in page.inner_text("#f4pBody")
    assert "f4p-lo" in page.evaluate("f4pUrgentCell('CORE')")

def test_urgente_configuracao_tag_e_meta_persistem_e_entram_na_exportacao(page):
    carregar(page, "times.xlsx")
    page.click("#btnCfg")
    assert page.eval_on_selector("#cfgF4pExpedite", "el => el.value") == "urgent"
    page.select_option("#cfgF4pExpedite", "paused")
    page.fill('input[data-f4pteam="core"][data-f4pf="urgentMeta"]', "5")
    with page.expect_download() as d:
        page.click("#cfgExport")
    txt = open(d.value.path(), encoding="utf-8").read()
    assert '"expediteTag": "paused"' in txt and '"urgentMeta": 5' in txt
    page.click("#cfgSave"); page.wait_for_timeout(200)
    assert page.evaluate("CFG.f4p.expediteTag") == "paused"
    assert page.evaluate("CFG.f4p.teams.core.urgentMeta") == 5

def test_urgente_meta_zero_e_valida(page):
    carregar(page, "times.xlsx")
    page.click("#btnCfg")
    page.fill('input[data-f4pteam="core"][data-f4pf="urgentMeta"]', "0")
    page.click("#cfgSave"); page.wait_for_timeout(200)
    assert page.evaluate("CFG.f4p.teams.core") == {"urgentMeta": 0}
