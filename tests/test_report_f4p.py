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
    """Semestre em curso: aberto conta sempre; fechado conta se fechou dentro do período exato do
    semestre selecionado (f4pUrgentWindow, decisão 0017)."""
    carregar(page, "f4p.xlsx")
    n = page.evaluate("""()=>{
      S.f.exec = semestre(TODAY);
      const inicioDoSemestre = f4pSemesterState().start;
      S.model.ops.set("u1", {team:"F4P_URG2", type:"Bug", tagHits:[{id:"urgent"}], deploy:null});
      S.model.ops.set("u2", {team:"F4P_URG2", type:"Bug", tagHits:[{id:"urgent"}], deploy:new Date(inicioDoSemestre.getTime() + 5 * 864e5)});
      return f4pUrgentRealizado("F4P_URG2", f4pSemesterState());
    }""")
    assert n == 2

def test_urgente_semestre_atual_ignora_fechados_antes_do_inicio_do_semestre(page):
    """Regressão relatada pelo usuário: a contagem estava somando todo item que já teve a tag em
    qualquer momento da história do time (ex.: 249 itens num time que usa a tag raramente). A janela
    corrigida (decisão 0017) não é mais os últimos N meses a partir de hoje — é o período exato do
    semestre selecionado: um item fechado antes do primeiro dia do semestre em curso não conta, mesmo
    estando dentro da janela rolante de N meses que CycleTime/Variabilidade usam."""
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      S.f.exec = semestre(TODAY);
      const inicioDoSemestre = f4pSemesterState().start;
      const antesDoSemestre = new Date(inicioDoSemestre.getTime() - 864e5);    // véspera do início do semestre: não conta
      const depoisDoInicio = new Date(inicioDoSemestre.getTime() + 5 * 864e5); // dentro do semestre: conta
      S.model.ops.set("v1", {team:"F4P_URG4", tagHits:[{id:"urgent"}], deploy:antesDoSemestre});
      S.model.ops.set("v2", {team:"F4P_URG4", tagHits:[{id:"urgent"}], deploy:depoisDoInicio});
      S.model.ops.set("v3", {team:"F4P_URG4", tagHits:[{id:"urgent"}], deploy:null});           // aberto há qualquer tempo: conta
      return f4pUrgentRealizado("F4P_URG4", f4pSemesterState());
    }""")
    assert r == 2

def test_urgente_clique_no_numero_abre_lista_e_permite_navegar(page):
    """Melhoria pedida pelo usuário: clicar no Realizado mostra quais itens entraram na contagem, e cada
    um leva direto até o item no quadro."""
    carregar(page, "f4p.xlsx")
    alvo_id = page.evaluate("""()=>{
      S.f.team='CORE'; S.f.exec=semestre(TODAY);
      const alvo = [...S.model.ops.values()].find(o=>o.team==='CORE');
      alvo.tagHits = [...(alvo.tagHits||[]), CFG.tags.find(t=>t.id==='urgent')];
      alvo.deploy = new Date(f4pSemesterState().start.getTime() + 5 * 864e5);   // garante que cai dentro do semestre atual
      render();
      return alvo.id;
    }""")
    page.click("#f4pTab")
    page.click('button[data-f4p-urgent-team="CORE"]')
    assert page.is_visible("#f4pItemsBg")
    rows = page.locator("#f4pItemsBody tbody tr")
    assert rows.count() == 1
    assert alvo_id in page.inner_text("#f4pItemsBody")
    assert "Vazão" in page.inner_text("#f4pItemsBody")     # Situação segue a categoria do fluxo (decisão 0019), não "Fechado"
    page.click(f'button[data-f4p-go="{alvo_id}"]')
    assert not page.is_visible("#f4pItemsBg")
    assert not page.is_visible("#f4pPanel.open")           # o painel F4P também fecha, para não esconder o item
    assert page.evaluate("document.getElementById('goto').value") == alvo_id

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

# ---------------- Quadrante 4 · Technical Story (meta vs. realizado) ----------------
# Mesmo comportamento do Urgente (docs/decisoes/0018), mas conta itens pelo tipo "Technical Story" em
# vez de uma tag, e a meta tem padrão 6 em vez de ficar "sem meta" quando o time não cadastra a própria.

def test_ts_conta_so_itens_do_tipo_technical_story(page):
    carregar(page, "f4p.xlsx")
    n = page.evaluate("""()=>{
      S.model.ops.set("t1", {team:"F4P_TS1", type:"Technical Story"});
      S.model.ops.set("t2", {team:"F4P_TS1", type:"User Story"});
      S.model.ops.set("t3", {team:"F4P_TS1", type:"Bug"});
      S.f.exec = semestre(TODAY);
      return f4pTsRealizado("F4P_TS1");
    }""")
    assert n == 1

def test_ts_semestre_atual_conta_abertos_e_fechados(page):
    """Semestre em curso: aberto conta sempre; fechado conta se fechou dentro do período exato do
    semestre selecionado (mesma janela do Urgente, f4pExactSemesterWindow)."""
    carregar(page, "f4p.xlsx")
    n = page.evaluate("""()=>{
      S.f.exec = semestre(TODAY);
      const inicioDoSemestre = f4pSemesterState().start;
      S.model.ops.set("t1", {team:"F4P_TS2", type:"Technical Story", deploy:null});
      S.model.ops.set("t2", {team:"F4P_TS2", type:"Technical Story", deploy:new Date(inicioDoSemestre.getTime() + 5 * 864e5)});
      return f4pTsRealizado("F4P_TS2", f4pSemesterState());
    }""")
    assert n == 2

def test_ts_semestre_atual_ignora_fechados_antes_do_inicio_do_semestre(page):
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      S.f.exec = semestre(TODAY);
      const inicioDoSemestre = f4pSemesterState().start;
      const antesDoSemestre = new Date(inicioDoSemestre.getTime() - 864e5);    // véspera do início do semestre: não conta
      const depoisDoInicio = new Date(inicioDoSemestre.getTime() + 5 * 864e5); // dentro do semestre: conta
      S.model.ops.set("t1", {team:"F4P_TS3", type:"Technical Story", deploy:antesDoSemestre});
      S.model.ops.set("t2", {team:"F4P_TS3", type:"Technical Story", deploy:depoisDoInicio});
      S.model.ops.set("t3", {team:"F4P_TS3", type:"Technical Story", deploy:null});           // aberto há qualquer tempo: conta
      return f4pTsRealizado("F4P_TS3", f4pSemesterState());
    }""")
    assert r == 2

def test_ts_semestre_passado_conta_so_fechados_no_periodo(page):
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      const curStart = f4pSemStart(semestre(TODAY));
      const prevMid = new Date(curStart.getFullYear(), curStart.getMonth() - 3, 15);
      const prevSem = semestre(prevMid);
      S.model.ops.set("t1", {team:"F4P_TS4", type:"Technical Story", deploy:prevMid});    // fechado dentro do semestre anterior
      S.model.ops.set("t2", {team:"F4P_TS4", type:"Technical Story", deploy:null});       // ainda aberto
      S.model.ops.set("t3", {team:"F4P_TS4", type:"Technical Story", deploy:curStart});   // fechado, mas no semestre atual
      S.f.int = prevSem;
      return f4pTsRealizado("F4P_TS4", f4pSemesterState());
    }""")
    assert r == 1

def test_ts_clique_no_numero_abre_lista_e_permite_navegar(page):
    carregar(page, "f4p.xlsx")
    alvo_id = page.evaluate("""()=>{
      S.f.team='CORE'; S.f.exec=semestre(TODAY);
      const alvo = [...S.model.ops.values()].find(o=>o.team==='CORE');
      alvo.type = 'Technical Story';
      alvo.deploy = new Date(f4pSemesterState().start.getTime() + 5 * 864e5);   // garante que cai dentro do semestre atual
      render();
      return alvo.id;
    }""")
    page.click("#f4pTab")
    page.click('button[data-f4p-ts-team="CORE"]')
    assert page.is_visible("#f4pItemsBg")
    rows = page.locator("#f4pItemsBody tbody tr")
    assert rows.count() == 1
    assert alvo_id in page.inner_text("#f4pItemsBody")
    assert "Vazão" in page.inner_text("#f4pItemsBody")     # Situação segue a categoria do fluxo (decisão 0019), não "Fechado"
    page.click(f'button[data-f4p-go="{alvo_id}"]')
    assert not page.is_visible("#f4pItemsBg")
    assert not page.is_visible("#f4pPanel.open")
    assert page.evaluate("document.getElementById('goto').value") == alvo_id

def test_ts_meta_padrao_6_colore_vermelho_ou_verde(page):
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      for (let i = 1; i <= 6; i++) S.model.ops.set("m"+i, {team:"F4P_TS_META", type:"Technical Story", deploy:null});
      S.f.exec = semestre(TODAY);
      const naMeta = f4pTsCell("F4P_TS_META");             // 6 itens, sem meta cadastrada: usa o padrão 6 (6 <= 6)
      S.model.ops.set("m7", {team:"F4P_TS_META", type:"Technical Story", deploy:null});
      const acimaDaMeta = f4pTsCell("F4P_TS_META");        // 7 > 6 (padrão)
      CFG.f4p.teams.f4p_ts_meta = {tsMeta: 10};
      const metaPropria = f4pTsCell("F4P_TS_META");        // 7 <= 10 (meta própria do time)
      delete CFG.f4p.teams.f4p_ts_meta;
      return {naMeta, acimaDaMeta, metaPropria};
    }""")
    assert "f4p-good" in r["naMeta"] and "f4p-bad" not in r["naMeta"]
    assert "f4p-bad" in r["acimaDaMeta"]
    assert "f4p-good" in r["metaPropria"] and "f4p-bad" not in r["metaPropria"]

def test_ts_aparece_calculado_no_painel(page):
    carregar(page, "f4p.xlsx")
    page.evaluate("()=>{ S.f.team='CORE'; S.f.exec=semestre(TODAY); render(); }")
    page.click("#f4pTab")
    assert "Technical Story (meta vs realizado)" in page.inner_text("#f4pBody")
    assert "f4p-lo" in page.evaluate("f4pTsCell('CORE')")

def test_ts_configuracao_meta_persiste_e_entra_na_exportacao(page):
    carregar(page, "times.xlsx")
    page.click("#btnCfg")
    page.fill('input[data-f4pteam="core"][data-f4pf="tsMeta"]', "8")
    with page.expect_download() as d:
        page.click("#cfgExport")
    txt = open(d.value.path(), encoding="utf-8").read()
    assert '"tsMeta": 8' in txt
    page.click("#cfgSave"); page.wait_for_timeout(200)
    assert page.evaluate("CFG.f4p.teams.core.tsMeta") == 8

def test_ts_meta_zero_e_valida(page):
    carregar(page, "times.xlsx")
    page.click("#btnCfg")
    page.fill('input[data-f4pteam="core"][data-f4pf="tsMeta"]', "0")
    page.click("#cfgSave"); page.wait_for_timeout(200)
    assert page.evaluate("CFG.f4p.teams.core") == {"tsMeta": 0}

# ---------------- Situação dos itens (Urgente e Technical Story) ----------------
# Decisão 0019: a lista de itens (clique no Realizado) mostra a mesma categoria de coluna do resto do
# portal (Backlog/Discovery/WIP/Vazão, mapeada por time em Configurações — catOf/CAT_LABEL), não um
# "Aberto"/"Fechado" próprio do Report F4P.

def test_situacao_dos_itens_usa_categoria_do_fluxo_do_time(page):
    carregar(page, "times.xlsx")   # fluxo do CORE tem coluna de Discovery (Refinamento), ao contrário do f4p.xlsx
    r = page.evaluate("""()=>{
      const mk = (id, stName, deploy) => { const o = {id, team:'CORE', stName, deploy: deploy || null}; return f4pItemSituacao(o); };
      return {
        backlog: mk('SIT1', 'Backlog'),
        discovery: mk('SIT2', 'Refinamento'),
        wip: mk('SIT3', 'Em Desenvolvimento'),
        vazaoSemData: mk('SIT4', 'Pronto para Deploy'),
        vazaoComData: mk('SIT5', 'Fechado', new Date(2026, 6, 21)),
        semColuna: mk('SIT6', null),
      };
    }""")
    assert r["backlog"] == "Backlog"
    assert r["discovery"] == "Discovery"
    assert r["wip"] == "WIP"
    assert r["vazaoSemData"] == "Vazão"
    assert r["vazaoComData"] == "Vazão · 21/07/2026"
    assert r["semColuna"] == "Backlog"   # sem coluna reconhecida no fluxo do time: mesmo padrão de catOf ("none")
