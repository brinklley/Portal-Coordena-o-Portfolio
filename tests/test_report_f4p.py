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
# Decisão 0020: diferente do Urgente, só conta itens já ENTREGUES (categoria de fluxo Vazão) — itens em
# Backlog, Discovery ou WIP não entram no Realizado, mesmo abertos há muito tempo. Os testes abaixo dão
# um fluxo próprio (Backlog/Discovery/WIP/Vazao) a cada time sintético via S.model.teamFlow + CFG.flow,
# para controlar a categoria de cada item independente dos dados aleatórios das fixtures.

def test_ts_conta_so_itens_do_tipo_technical_story_e_entregues(page):
    carregar(page, "f4p.xlsx")
    n = page.evaluate("""()=>{
      S.model.teamFlow.F4P_TS1 = ["Backlog", "Vazao"];
      CFG.flow.f4p_ts1 = {cat:{vazao:"vazao"}, ct:[]};
      const hoje = new Date();
      S.model.ops.set("t1", {team:"F4P_TS1", type:"Technical Story", stName:"Vazao", deploy:hoje});
      S.model.ops.set("t2", {team:"F4P_TS1", type:"User Story", stName:"Vazao", deploy:hoje});
      S.model.ops.set("t3", {team:"F4P_TS1", type:"Bug", stName:"Vazao", deploy:hoje});
      S.f.exec = semestre(TODAY);
      return f4pTsRealizado("F4P_TS1");
    }""")
    assert n == 1

def test_ts_ignora_itens_em_backlog_discovery_ou_wip(page):
    """Regra pedida pelo usuário depois de ver o quadrante em produção (decisão 0020): itens ainda não
    entregues não devem contar, nem mesmo os abertos há muito tempo — ao contrário do Urgente."""
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      S.model.teamFlow.F4P_TS2 = ["Backlog", "Discovery", "WIP", "Vazao"];
      CFG.flow.f4p_ts2 = {cat:{discovery:"disc", wip:"wip", vazao:"vazao"}, ct:[]};
      S.f.exec = semestre(TODAY);
      const hoje = new Date();
      S.model.ops.set("b1", {team:"F4P_TS2", type:"Technical Story", stName:"Backlog", deploy:null});
      S.model.ops.set("d1", {team:"F4P_TS2", type:"Technical Story", stName:"Discovery", deploy:null});
      S.model.ops.set("w1", {team:"F4P_TS2", type:"Technical Story", stName:"WIP", deploy:null});
      S.model.ops.set("v1", {team:"F4P_TS2", type:"Technical Story", stName:"Vazao", deploy:hoje});
      S.model.ops.set("v2", {team:"F4P_TS2", type:"Technical Story", stName:"Vazao", deploy:null});   // Vazão mas sem data de saída: não conta
      return f4pTsRealizado("F4P_TS2", f4pSemesterState());
    }""")
    assert r == 1

def test_ts_semestre_atual_ignora_entregues_antes_do_inicio_do_semestre(page):
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      S.model.teamFlow.F4P_TS3 = ["Backlog", "Vazao"];
      CFG.flow.f4p_ts3 = {cat:{vazao:"vazao"}, ct:[]};
      S.f.exec = semestre(TODAY);
      const inicioDoSemestre = f4pSemesterState().start;
      const antesDoSemestre = new Date(inicioDoSemestre.getTime() - 864e5);    // véspera do início do semestre: não conta
      const depoisDoInicio = new Date(inicioDoSemestre.getTime() + 5 * 864e5); // dentro do semestre: conta
      S.model.ops.set("t1", {team:"F4P_TS3", type:"Technical Story", stName:"Vazao", deploy:antesDoSemestre});
      S.model.ops.set("t2", {team:"F4P_TS3", type:"Technical Story", stName:"Vazao", deploy:depoisDoInicio});
      S.model.ops.set("t3", {team:"F4P_TS3", type:"Technical Story", stName:"Backlog", deploy:null});   // ainda aberto: não conta (decisão 0020)
      return f4pTsRealizado("F4P_TS3", f4pSemesterState());
    }""")
    assert r == 1

def test_ts_semestre_passado_conta_so_entregues_no_periodo(page):
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      S.model.teamFlow.F4P_TS4 = ["Backlog", "Vazao"];
      CFG.flow.f4p_ts4 = {cat:{vazao:"vazao"}, ct:[]};
      const curStart = f4pSemStart(semestre(TODAY));
      const prevMid = new Date(curStart.getFullYear(), curStart.getMonth() - 3, 15);
      const prevSem = semestre(prevMid);
      S.model.ops.set("t1", {team:"F4P_TS4", type:"Technical Story", stName:"Vazao", deploy:prevMid});   // entregue dentro do semestre anterior
      S.model.ops.set("t2", {team:"F4P_TS4", type:"Technical Story", stName:"Backlog", deploy:null});    // ainda aberto
      S.model.ops.set("t3", {team:"F4P_TS4", type:"Technical Story", stName:"Vazao", deploy:curStart});  // entregue, mas no semestre atual
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
      S.model.teamFlow.F4P_TS_META = ["Backlog", "Vazao"];
      CFG.flow.f4p_ts_meta = {cat:{vazao:"vazao"}, ct:[]};
      const hoje = new Date();
      for (let i = 1; i <= 6; i++) S.model.ops.set("m"+i, {team:"F4P_TS_META", type:"Technical Story", stName:"Vazao", deploy:hoje});
      S.f.exec = semestre(TODAY);
      const naMeta = f4pTsCell("F4P_TS_META");             // 6 itens entregues, sem meta cadastrada: usa o padrão 6 (6 <= 6)
      S.model.ops.set("m7", {team:"F4P_TS_META", type:"Technical Story", stName:"Vazao", deploy:hoje});
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

# ---------------- Quadrante 5 · Vazão (reserva vs. realizado) ----------------
# Decisão 0022. Mesmo critério de "entregue" do Technical Story (categoria de fluxo Vazão), mas usa os
# tipos configurados para o CT (CFG.f4p.types, padrão User Story e Technical Story) em vez de um tipo
# fixo. Reserva é o subconjunto do Realizado com a tag de capacidade do roadmap (CFG.anTag, já usada na
# Visão analítica); Realizado é todo o conjunto, com ou sem a tag.

def test_vazao_conta_so_tipos_configurados_e_entregues(page):
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      S.model.teamFlow.F4P_VZ1 = ["Backlog", "Vazao"];
      CFG.flow.f4p_vz1 = {cat:{vazao:"vazao"}, ct:[]};
      const hoje = new Date();
      S.model.ops.set("v1", {team:"F4P_VZ1", type:"User Story", stName:"Vazao", deploy:hoje, tags:[]});
      S.model.ops.set("v2", {team:"F4P_VZ1", type:"Technical Story", stName:"Vazao", deploy:hoje, tags:[]});
      S.model.ops.set("v3", {team:"F4P_VZ1", type:"Internal Bug", stName:"Vazao", deploy:hoje, tags:[]});   // tipo não configurado: não conta
      S.model.ops.set("v4", {team:"F4P_VZ1", type:"User Story", stName:"Backlog", deploy:null, tags:[]});   // não entregue: não conta
      S.f.exec = semestre(TODAY);
      return f4pVazaoRealizadoItems("F4P_VZ1", f4pSemesterState()).length;
    }""")
    assert r == 2

def test_vazao_reserva_e_subconjunto_com_a_tag_de_capacidade(page):
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      S.model.teamFlow.F4P_VZ2 = ["Backlog", "Vazao"];
      CFG.flow.f4p_vz2 = {cat:{vazao:"vazao"}, ct:[]};
      const hoje = new Date();
      S.model.ops.set("v1", {team:"F4P_VZ2", type:"User Story", stName:"Vazao", deploy:hoje, tags:["ROADMAP"]});
      S.model.ops.set("v2", {team:"F4P_VZ2", type:"User Story", stName:"Vazao", deploy:hoje, tags:["Roadmap"]});   // mesma tag, outra caixa
      S.model.ops.set("v3", {team:"F4P_VZ2", type:"User Story", stName:"Vazao", deploy:hoje, tags:[]});
      S.f.exec = semestre(TODAY);
      const st = f4pSemesterState();
      return {reserva: f4pVazaoReservaItems("F4P_VZ2", st).length, realizado: f4pVazaoRealizadoItems("F4P_VZ2", st).length};
    }""")
    assert r == {"reserva": 2, "realizado": 3}

def test_vazao_usa_tag_de_capacidade_configuravel(page):
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      S.model.teamFlow.F4P_VZ3 = ["Backlog", "Vazao"];
      CFG.flow.f4p_vz3 = {cat:{vazao:"vazao"}, ct:[]};
      CFG.anTag = "CAPACIDADE";
      const hoje = new Date();
      S.model.ops.set("v1", {team:"F4P_VZ3", type:"User Story", stName:"Vazao", deploy:hoje, tags:["CAPACIDADE"]});
      S.model.ops.set("v2", {team:"F4P_VZ3", type:"User Story", stName:"Vazao", deploy:hoje, tags:["ROADMAP"]});   // tag antiga: não conta mais
      S.f.exec = semestre(TODAY);
      const n = f4pVazaoReservaItems("F4P_VZ3", f4pSemesterState()).length;
      CFG.anTag = "ROADMAP";
      return n;
    }""")
    assert r == 1

def test_vazao_ignora_itens_em_backlog_discovery_ou_wip(page):
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      S.model.teamFlow.F4P_VZ4 = ["Backlog", "Discovery", "WIP", "Vazao"];
      CFG.flow.f4p_vz4 = {cat:{discovery:"disc", wip:"wip", vazao:"vazao"}, ct:[]};
      S.f.exec = semestre(TODAY);
      const hoje = new Date();
      S.model.ops.set("b1", {team:"F4P_VZ4", type:"User Story", stName:"Backlog", deploy:null, tags:[]});
      S.model.ops.set("d1", {team:"F4P_VZ4", type:"User Story", stName:"Discovery", deploy:null, tags:[]});
      S.model.ops.set("w1", {team:"F4P_VZ4", type:"User Story", stName:"WIP", deploy:null, tags:[]});
      S.model.ops.set("v1", {team:"F4P_VZ4", type:"User Story", stName:"Vazao", deploy:hoje, tags:[]});
      return f4pVazaoRealizadoItems("F4P_VZ4", f4pSemesterState()).length;
    }""")
    assert r == 1

def test_vazao_semestre_atual_ignora_entregues_antes_do_inicio_do_semestre(page):
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      S.model.teamFlow.F4P_VZ5 = ["Backlog", "Vazao"];
      CFG.flow.f4p_vz5 = {cat:{vazao:"vazao"}, ct:[]};
      S.f.exec = semestre(TODAY);
      const inicioDoSemestre = f4pSemesterState().start;
      const antesDoSemestre = new Date(inicioDoSemestre.getTime() - 864e5);
      const depoisDoInicio = new Date(inicioDoSemestre.getTime() + 5 * 864e5);
      S.model.ops.set("v1", {team:"F4P_VZ5", type:"User Story", stName:"Vazao", deploy:antesDoSemestre, tags:[]});
      S.model.ops.set("v2", {team:"F4P_VZ5", type:"User Story", stName:"Vazao", deploy:depoisDoInicio, tags:[]});
      return f4pVazaoRealizadoItems("F4P_VZ5", f4pSemesterState()).length;
    }""")
    assert r == 1

def test_vazao_semestre_passado_conta_so_entregues_no_periodo(page):
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      S.model.teamFlow.F4P_VZ6 = ["Backlog", "Vazao"];
      CFG.flow.f4p_vz6 = {cat:{vazao:"vazao"}, ct:[]};
      const curStart = f4pSemStart(semestre(TODAY));
      const prevMid = new Date(curStart.getFullYear(), curStart.getMonth() - 3, 15);
      const prevSem = semestre(prevMid);
      S.model.ops.set("v1", {team:"F4P_VZ6", type:"User Story", stName:"Vazao", deploy:prevMid, tags:[]});    // entregue dentro do semestre anterior
      S.model.ops.set("v2", {team:"F4P_VZ6", type:"User Story", stName:"Backlog", deploy:null, tags:[]});     // ainda aberto
      S.model.ops.set("v3", {team:"F4P_VZ6", type:"User Story", stName:"Vazao", deploy:curStart, tags:[]});   // entregue, mas no semestre atual
      S.f.int = prevSem;
      return f4pVazaoRealizadoItems("F4P_VZ6", f4pSemesterState()).length;
    }""")
    assert r == 1

def test_vazao_tendencia_ultimo_mes_acima_da_media_melhora(page):
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      S.model.teamFlow.F4P_VZ7 = ["Backlog", "Vazao"];
      CFG.flow.f4p_vz7 = {cat:{vazao:"vazao"}, ct:[]};
      const st = {kind:"current", start:new Date(TODAY.getFullYear(), TODAY.getMonth() - 2, 1), end:new Date(TODAY.getFullYear(), TODAY.getMonth() + 6, 0)};
      const m2 = new Date(TODAY.getFullYear(), TODAY.getMonth() - 2, 15), m1 = new Date(TODAY.getFullYear(), TODAY.getMonth() - 1, 15), m0 = new Date(TODAY.getFullYear(), TODAY.getMonth(), 1);
      S.model.ops.set("a1", {team:"F4P_VZ7", type:"User Story", stName:"Vazao", deploy:m2, tags:[]});
      S.model.ops.set("a2", {team:"F4P_VZ7", type:"User Story", stName:"Vazao", deploy:m1, tags:[]});
      for (let i = 0; i < 5; i++) S.model.ops.set("a3_"+i, {team:"F4P_VZ7", type:"User Story", stName:"Vazao", deploy:m0, tags:[]});
      return f4pVazaoTrend("F4P_VZ7", st);
    }""")
    assert r == "▲"

def test_vazao_tendencia_ultimo_mes_abaixo_da_media_piora(page):
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      S.model.teamFlow.F4P_VZ8 = ["Backlog", "Vazao"];
      CFG.flow.f4p_vz8 = {cat:{vazao:"vazao"}, ct:[]};
      const st = {kind:"current", start:new Date(TODAY.getFullYear(), TODAY.getMonth() - 2, 1), end:new Date(TODAY.getFullYear(), TODAY.getMonth() + 6, 0)};
      const m2 = new Date(TODAY.getFullYear(), TODAY.getMonth() - 2, 15), m1 = new Date(TODAY.getFullYear(), TODAY.getMonth() - 1, 15), m0 = new Date(TODAY.getFullYear(), TODAY.getMonth(), 1);
      for (let i = 0; i < 5; i++) S.model.ops.set("b2_"+i, {team:"F4P_VZ8", type:"User Story", stName:"Vazao", deploy:m2, tags:[]});
      for (let i = 0; i < 5; i++) S.model.ops.set("b1_"+i, {team:"F4P_VZ8", type:"User Story", stName:"Vazao", deploy:m1, tags:[]});
      S.model.ops.set("b0", {team:"F4P_VZ8", type:"User Story", stName:"Vazao", deploy:m0, tags:[]});
      return f4pVazaoTrend("F4P_VZ8", st);
    }""")
    assert r == "▼"

def test_vazao_tendencia_igual_aos_meses_anteriores_fica_neutra(page):
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      S.model.teamFlow.F4P_VZ9 = ["Backlog", "Vazao"];
      CFG.flow.f4p_vz9 = {cat:{vazao:"vazao"}, ct:[]};
      const st = {kind:"current", start:new Date(TODAY.getFullYear(), TODAY.getMonth() - 2, 1), end:new Date(TODAY.getFullYear(), TODAY.getMonth() + 6, 0)};
      const m2 = new Date(TODAY.getFullYear(), TODAY.getMonth() - 2, 15), m1 = new Date(TODAY.getFullYear(), TODAY.getMonth() - 1, 15), m0 = new Date(TODAY.getFullYear(), TODAY.getMonth(), 1);
      for (let i = 0; i < 2; i++) S.model.ops.set("c2_"+i, {team:"F4P_VZ9", type:"User Story", stName:"Vazao", deploy:m2, tags:[]});
      for (let i = 0; i < 2; i++) S.model.ops.set("c1_"+i, {team:"F4P_VZ9", type:"User Story", stName:"Vazao", deploy:m1, tags:[]});
      for (let i = 0; i < 2; i++) S.model.ops.set("c0_"+i, {team:"F4P_VZ9", type:"User Story", stName:"Vazao", deploy:m0, tags:[]});
      return f4pVazaoTrend("F4P_VZ9", st);
    }""")
    assert r == "◆"

def test_vazao_tendencia_sem_meses_anteriores_fica_neutra(page):
    """Semestre com só um mês decorrido (acabou de começar): não há meses anteriores para comparar."""
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      const st = {kind:"current", start:new Date(TODAY.getFullYear(), TODAY.getMonth(), 1), end:new Date(TODAY.getFullYear(), TODAY.getMonth() + 6, 0)};
      return f4pVazaoTrend("F4P_VZ_VAZIO", st);
    }""")
    assert r == "◆"

# Decisão 0023: a tendência passou a somar os itens hoje em WIP ao mês corrente (trabalho a caminho de
# virar Vazão), e a média dos meses anteriores arredonda sempre para cima. Os três casos abaixo são os
# exemplos exatos dados pelo usuário para especificar a regra.

def test_vazao_tendencia_soma_wip_ao_mes_atual_exemplo_melhora(page):
    """Média 1, mês atual 0, 3 itens em WIP: 0+3=3 > 1 → melhora."""
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      S.model.teamFlow.F4P_VZT1 = ["Backlog", "WIP", "Vazao"];
      CFG.flow.f4p_vzt1 = {cat:{wip:"wip", vazao:"vazao"}, ct:[]};
      const st = {kind:"current", start:new Date(TODAY.getFullYear(), TODAY.getMonth() - 1, 1), end:new Date(TODAY.getFullYear(), TODAY.getMonth() + 6, 0)};
      const mesAnterior = new Date(TODAY.getFullYear(), TODAY.getMonth() - 1, 15);
      S.model.ops.set("v1", {team:"F4P_VZT1", type:"User Story", stName:"Vazao", deploy:mesAnterior, tags:[]});   // média = 1
      for (let i = 0; i < 3; i++) S.model.ops.set("w"+i, {team:"F4P_VZT1", type:"User Story", stName:"WIP", deploy:null, tags:[]});
      return f4pVazaoTrend("F4P_VZT1", st);
    }""")
    assert r == "▲"

def test_vazao_tendencia_soma_wip_ao_mes_atual_exemplo_piora(page):
    """Média 2, mês atual 0, 1 item em WIP: 0+1=1 < 2 → piora."""
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      S.model.teamFlow.F4P_VZT2 = ["Backlog", "WIP", "Vazao"];
      CFG.flow.f4p_vzt2 = {cat:{wip:"wip", vazao:"vazao"}, ct:[]};
      const st = {kind:"current", start:new Date(TODAY.getFullYear(), TODAY.getMonth() - 1, 1), end:new Date(TODAY.getFullYear(), TODAY.getMonth() + 6, 0)};
      const mesAnterior = new Date(TODAY.getFullYear(), TODAY.getMonth() - 1, 10);
      for (let i = 0; i < 2; i++) S.model.ops.set("v"+i, {team:"F4P_VZT2", type:"User Story", stName:"Vazao", deploy:mesAnterior, tags:[]});   // média = 2
      S.model.ops.set("w0", {team:"F4P_VZT2", type:"User Story", stName:"WIP", deploy:null, tags:[]});
      return f4pVazaoTrend("F4P_VZT2", st);
    }""")
    assert r == "▼"

def test_vazao_tendencia_soma_wip_ao_mes_atual_exemplo_estavel(page):
    """Média 3, mês atual 2, 1 item em WIP: 2+1=3 == 3 → estável."""
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      S.model.teamFlow.F4P_VZT3 = ["Backlog", "WIP", "Vazao"];
      CFG.flow.f4p_vzt3 = {cat:{wip:"wip", vazao:"vazao"}, ct:[]};
      const st = {kind:"current", start:new Date(TODAY.getFullYear(), TODAY.getMonth() - 1, 1), end:new Date(TODAY.getFullYear(), TODAY.getMonth() + 6, 0)};
      const mesAnterior = new Date(TODAY.getFullYear(), TODAY.getMonth() - 1, 10), mesAtual = new Date(TODAY.getFullYear(), TODAY.getMonth(), 1);
      for (let i = 0; i < 3; i++) S.model.ops.set("v"+i, {team:"F4P_VZT3", type:"User Story", stName:"Vazao", deploy:mesAnterior, tags:[]});    // média = 3
      for (let i = 0; i < 2; i++) S.model.ops.set("c"+i, {team:"F4P_VZT3", type:"User Story", stName:"Vazao", deploy:mesAtual, tags:[]});      // mês atual = 2
      S.model.ops.set("w0", {team:"F4P_VZT3", type:"User Story", stName:"WIP", deploy:null, tags:[]});
      return f4pVazaoTrend("F4P_VZT3", st);
    }""")
    assert r == "◆"

def test_vazao_tendencia_media_arredonda_sempre_pra_cima(page):
    """Meses anteriores com 1 e 2 itens (média bruta 1,5): arredondada pra cima vira 2. Mês atual com 2
    itens e nenhum WIP fica igual à média arredondada (estável) — sem o arredondamento, seria "melhora"
    (2 > 1,5)."""
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      S.model.teamFlow.F4P_VZT4 = ["Backlog", "WIP", "Vazao"];
      CFG.flow.f4p_vzt4 = {cat:{wip:"wip", vazao:"vazao"}, ct:[]};
      const st = {kind:"current", start:new Date(TODAY.getFullYear(), TODAY.getMonth() - 2, 1), end:new Date(TODAY.getFullYear(), TODAY.getMonth() + 6, 0)};
      const m2 = new Date(TODAY.getFullYear(), TODAY.getMonth() - 2, 10), m1 = new Date(TODAY.getFullYear(), TODAY.getMonth() - 1, 10), m0 = new Date(TODAY.getFullYear(), TODAY.getMonth(), 1);
      S.model.ops.set("a", {team:"F4P_VZT4", type:"User Story", stName:"Vazao", deploy:m2, tags:[]});
      for (let i = 0; i < 2; i++) S.model.ops.set("b"+i, {team:"F4P_VZT4", type:"User Story", stName:"Vazao", deploy:m1, tags:[]});
      for (let i = 0; i < 2; i++) S.model.ops.set("c"+i, {team:"F4P_VZT4", type:"User Story", stName:"Vazao", deploy:m0, tags:[]});
      return f4pVazaoTrend("F4P_VZT4", st);
    }""")
    assert r == "◆"

def test_vazao_wip_conta_so_tipos_configurados_do_time(page):
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      S.model.teamFlow.F4P_VZT5 = ["Backlog", "WIP", "Vazao"];
      CFG.flow.f4p_vzt5 = {cat:{wip:"wip", vazao:"vazao"}, ct:[]};
      S.model.ops.set("w1", {team:"F4P_VZT5", type:"User Story", stName:"WIP", deploy:null, tags:[]});
      S.model.ops.set("w2", {team:"F4P_VZT5", type:"Internal Bug", stName:"WIP", deploy:null, tags:[]});   // tipo não configurado: não conta
      S.model.ops.set("w3", {team:"F4P_VZT5_OUTRO", type:"User Story", stName:"WIP", deploy:null, tags:[]});   // outro time: não conta
      return f4pVazaoWipCount("F4P_VZT5");
    }""")
    assert r == 1

# Decisão 0024: a seta de tendência (não os números) é colorida por Realizado vs. Reserva — verde
# quando Realizado ≥ Reserva, vermelho quando Realizado < Reserva. Como Reserva é sempre um subconjunto
# do Realizado (nunca maior, por construção — decisão 0022), a cor vermelha não é alcançável com o
# pipeline normal; os testes cobrem os dois casos que a checagem >= realmente distingue: Realizado maior
# e Realizado igual à Reserva (todos os itens com a tag).

def test_vazao_seta_de_tendencia_fica_verde_quando_realizado_maior_que_reserva(page):
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      S.model.teamFlow.F4P_VZ10 = ["Backlog", "Vazao"];
      CFG.flow.f4p_vz10 = {cat:{vazao:"vazao"}, ct:[]};
      const hoje = new Date();
      S.model.ops.set("v1", {team:"F4P_VZ10", type:"User Story", stName:"Vazao", deploy:hoje, tags:["ROADMAP"]});
      S.model.ops.set("v2", {team:"F4P_VZ10", type:"User Story", stName:"Vazao", deploy:hoje, tags:[]});
      S.f.exec = semestre(TODAY);
      return f4pVazaoCell("F4P_VZ10");
    }""")
    assert "f4p-trend f4p-good" in r
    assert "f4p-bad" not in r

def test_vazao_seta_de_tendencia_fica_verde_quando_realizado_igual_reserva(page):
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      S.model.teamFlow.F4P_VZ11 = ["Backlog", "Vazao"];
      CFG.flow.f4p_vz11 = {cat:{vazao:"vazao"}, ct:[]};
      const hoje = new Date();
      S.model.ops.set("v1", {team:"F4P_VZ11", type:"User Story", stName:"Vazao", deploy:hoje, tags:["ROADMAP"]});   // único item, com a tag: reserva == realizado
      S.f.exec = semestre(TODAY);
      return f4pVazaoCell("F4P_VZ11");
    }""")
    assert "f4p-trend f4p-good" in r
    assert "f4p-bad" not in r

def test_vazao_clique_no_realizado_abre_lista_e_permite_navegar(page):
    carregar(page, "f4p.xlsx")
    alvo_id = page.evaluate("""()=>{
      S.f.team='CORE'; S.f.exec=semestre(TODAY);
      [...S.model.ops.values()].filter(o=>o.team==='CORE').forEach(o => { o.deploy = null; });
      const alvo = [...S.model.ops.values()].find(o=>o.team==='CORE');
      alvo.type = 'User Story';
      alvo.deploy = new Date(f4pSemesterState().start.getTime() + 5 * 864e5);   // garante que cai dentro do semestre atual
      render();
      return alvo.id;
    }""")
    page.click("#f4pTab")
    page.click('button[data-f4p-vazao-realizado-team="CORE"]')
    assert page.is_visible("#f4pItemsBg")
    rows = page.locator("#f4pItemsBody tbody tr")
    assert rows.count() == 1
    assert alvo_id in page.inner_text("#f4pItemsBody")
    page.click(f'button[data-f4p-go="{alvo_id}"]')
    assert not page.is_visible("#f4pItemsBg")
    assert not page.is_visible("#f4pPanel.open")
    assert page.evaluate("document.getElementById('goto').value") == alvo_id

def test_vazao_clique_na_reserva_mostra_so_os_com_a_tag(page):
    carregar(page, "f4p.xlsx")
    page.evaluate("""()=>{
      S.f.team='CORE'; S.f.exec=semestre(TODAY);
      [...S.model.ops.values()].filter(o=>o.team==='CORE').forEach(o => { o.deploy = null; });
      const dentro = new Date(f4pSemesterState().start.getTime() + 5 * 864e5);
      const ops = [...S.model.ops.values()].filter(o=>o.team==='CORE').slice(0, 2);
      ops[0].type = 'User Story'; ops[0].deploy = dentro; ops[0].tags = ['ROADMAP'];
      ops[1].type = 'User Story'; ops[1].deploy = dentro; ops[1].tags = [];
      render();
    }""")
    page.click("#f4pTab")
    page.click('button[data-f4p-vazao-reserva-team="CORE"]')
    assert page.is_visible("#f4pItemsBg")
    assert page.locator("#f4pItemsBody tbody tr").count() == 1

def test_vazao_aparece_calculado_no_painel(page):
    carregar(page, "f4p.xlsx")
    page.evaluate("()=>{ S.f.team='CORE'; S.f.exec=semestre(TODAY); render(); }")
    page.click("#f4pTab")
    assert "Vazão (reserva vs realizado)" in page.inner_text("#f4pBody")
    assert "f4p-sep" in page.evaluate("f4pVazaoCell('CORE')")

# ---------------- Quadrante 6 · Roadmap – Épicos (roadmap vs roadmap entregue vs atual) ----------------
# Decisão 0025. Diferente dos demais quadrantes (que operam sobre S.model.ops), este opera sobre os
# cards do quadro de Épicos (S.model.epis / S.model.stages.epi / e.st / e.target). "Fechado" aqui é a
# última coluna do PRÓPRIO quadro de Épicos, não a categoria de fluxo (catOf) de nenhum time.

def test_roadmap_interno_usa_target_date_do_proprio_epico(page):
    """Semestre Interno selecionado: 'Roadmap' usa o Target Date/semestre do próprio épico (e.interno),
    sem olhar o vínculo com a iniciativa."""
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      S.model.stages.epi = ["Backlog", "Fechado"];
      const sem = semestre(TODAY);
      S.f.int = sem;
      S.model.ops.set("rop1", {team:"F4P_RD1"});
      S.model.ops.set("rop2", {team:"F4P_RD1"});
      S.model.epis.set("re1", {id:"re1", parent:null, target:TODAY, interno:sem, st:0, stDate:null, ops:["rop1"], type:"Epic"});
      S.model.epis.set("re2", {id:"re2", parent:null, target:null, interno:"2099 1", st:0, stDate:null, ops:["rop2"], type:"Epic"});   // outro semestre: não conta
      return f4pRoadmapEpis("F4P_RD1").map(e=>e.id);
    }""")
    assert r == ["re1"]

def test_roadmap_executivo_usa_vinculo_com_a_iniciativa_ignorando_target_date_do_epico(page):
    """Semestre Executivo selecionado: 'Roadmap' sobe Iniciativa → Release → Épico pela iniciativa com
    o AnoSemestreRoadmap selecionado, independente do Target Date/semestre do próprio épico."""
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      S.model.stages.epi = ["Backlog", "Fechado"];
      const sem = semestre(TODAY);
      S.f.exec = sem;
      S.model.ops.set("rop1", {team:"F4P_RD2"});
      S.model.ops.set("rop2", {team:"F4P_RD2"});
      // e1: Target Date de outro semestre, mas vinculado (via release) a uma iniciativa do semestre selecionado — conta
      S.model.epis.set("re1", {id:"re1", parent:"r1", target:null, interno:"2099 1", st:0, stDate:null, ops:["rop1"], type:"Epic"});
      S.model.rels.set("r1", {id:"r1", parent:"i1", epis:["re1"]});
      S.model.inis.set("i1", {id:"i1", exec:sem, rels:["r1"]});
      // e2: Target Date do semestre selecionado, mas SEM vínculo com nenhuma iniciativa do roadmap executivo — não conta
      S.model.epis.set("re2", {id:"re2", parent:null, target:TODAY, interno:sem, st:0, stDate:null, ops:["rop2"], type:"Epic"});
      return f4pRoadmapEpis("F4P_RD2").map(e=>e.id);
    }""")
    assert r == ["re1"]

def test_roadmap_entregue_e_subconjunto_ja_fechado(page):
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      S.model.stages.epi = ["Backlog", "Fechado"];
      const sem = semestre(TODAY);
      S.f.int = sem;
      S.model.ops.set("rop1", {team:"F4P_RD3"});
      S.model.ops.set("rop2", {team:"F4P_RD3"});
      S.model.epis.set("re1", {id:"re1", parent:null, target:TODAY, interno:sem, st:1, stDate:TODAY, ops:["rop1"], type:"Epic"});   // fechado
      S.model.epis.set("re2", {id:"re2", parent:null, target:TODAY, interno:sem, st:0, stDate:null, ops:["rop2"], type:"Epic"});   // aberto
      return {roadmap: f4pRoadmapEpis("F4P_RD3").length, entregue: f4pRoadmapEntregueEpis("F4P_RD3").length};
    }""")
    assert r == {"roadmap": 2, "entregue": 1}

def test_atual_ignora_target_date_no_filtro_interno(page):
    """'Atual' conta só pela data de fechamento dentro do período do semestre — mesmo um épico com
    Target Date/semestre diferente do selecionado (que não entraria no 'Roadmap') conta aqui, desde que
    tenha fechado dentro do período (pedido explícito do usuário: sem levar o Target Date em conta)."""
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      S.model.stages.epi = ["Backlog", "Fechado"];
      const sem = semestre(TODAY);
      S.f.int = sem;
      const st = f4pSemesterState();
      const dentro = new Date(st.start.getTime() + 5 * 864e5);
      S.model.ops.set("rop1", {team:"F4P_RD4"});
      S.model.epis.set("re1", {id:"re1", parent:null, target:null, interno:"2099 1", st:1, stDate:dentro, ops:["rop1"], type:"Epic"});
      return {roadmap: f4pRoadmapEpis("F4P_RD4").length, atual: f4pAtualEpis("F4P_RD4", st).length};
    }""")
    assert r == {"roadmap": 0, "atual": 1}

def test_atual_ignora_vinculo_com_iniciativa_no_filtro_executivo(page):
    """No filtro Executivo, 'Atual' também não olha o vínculo com iniciativa — um épico sem release/
    iniciativa (que não entraria no 'Roadmap' executivo) ainda conta em 'Atual' se fechou no período."""
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      S.model.stages.epi = ["Backlog", "Fechado"];
      const sem = semestre(TODAY);
      S.f.exec = sem;
      const st = f4pSemesterState();
      const dentro = new Date(st.start.getTime() + 5 * 864e5);
      S.model.ops.set("rop1", {team:"F4P_RD5"});
      S.model.epis.set("re1", {id:"re1", parent:null, target:null, interno:null, st:1, stDate:dentro, ops:["rop1"], type:"Epic"});   // sem parent/release/iniciativa
      return {roadmap: f4pRoadmapEpis("F4P_RD5").length, atual: f4pAtualEpis("F4P_RD5", st).length};
    }""")
    assert r == {"roadmap": 0, "atual": 1}

def test_roadmap_filtra_por_tipo_de_epico_configurado(page):
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      S.model.stages.epi = ["Backlog", "Fechado"];
      const sem = semestre(TODAY);
      S.f.int = sem;
      S.model.ops.set("rop1", {team:"F4P_RD6"});
      S.model.ops.set("rop2", {team:"F4P_RD6"});
      S.model.epis.set("re1", {id:"re1", parent:null, target:TODAY, interno:sem, st:0, stDate:null, ops:["rop1"], type:"Epic"});
      S.model.epis.set("re2", {id:"re2", parent:null, target:TODAY, interno:sem, st:0, stDate:null, ops:["rop2"], type:"User Story"});   // tipo não configurado: não conta
      return f4pRoadmapEpis("F4P_RD6").map(e=>e.id);
    }""")
    assert r == ["re1"]

def test_roadmap_usa_tipos_de_epico_configuraveis(page):
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      S.model.stages.epi = ["Backlog", "Fechado"];
      const sem = semestre(TODAY);
      S.f.int = sem;
      CFG.f4p.epiTypes = ["feature"];
      S.model.ops.set("rop1", {team:"F4P_RD7"});
      S.model.epis.set("re1", {id:"re1", parent:null, target:TODAY, interno:sem, st:0, stDate:null, ops:["rop1"], type:"Feature"});
      const n = f4pRoadmapEpis("F4P_RD7").length;
      CFG.f4p.epiTypes = ["epic"];
      return n;
    }""")
    assert r == 1

def test_roadmap_conta_so_epicos_com_item_do_time(page):
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      S.model.stages.epi = ["Backlog", "Fechado"];
      const sem = semestre(TODAY);
      S.f.int = sem;
      S.model.ops.set("rop1", {team:"F4P_RD8"});
      S.model.ops.set("rop2", {team:"F4P_RD8_OUTRO"});
      S.model.epis.set("re1", {id:"re1", parent:null, target:TODAY, interno:sem, st:0, stDate:null, ops:["rop1"], type:"Epic"});
      S.model.epis.set("re2", {id:"re2", parent:null, target:TODAY, interno:sem, st:0, stDate:null, ops:["rop2"], type:"Epic"});   // item de outro time: não conta
      return f4pRoadmapEpis("F4P_RD8").map(e=>e.id);
    }""")
    assert r == ["re1"]

def test_roadmap_tendencia_soma_abertos_ao_mes_atual_exemplo_melhora(page):
    """Mesmas regras inspiracionais da tendência do Vazão (decisão 0023), adaptadas para o fluxo de
    Épicos: mês atual + épicos do Roadmap ainda abertos vs. média dos meses anteriores.
    Média 1, mês atual 0, 3 abertos: 0+3=3 > 1 → melhora."""
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      S.model.stages.epi = ["Backlog", "Fechado"];
      const sem = semestre(TODAY);
      S.f.int = sem;
      const st = {kind:"current", start:new Date(TODAY.getFullYear(), TODAY.getMonth() - 1, 1), end:new Date(TODAY.getFullYear(), TODAY.getMonth() + 6, 0)};
      const mesAnterior = new Date(TODAY.getFullYear(), TODAY.getMonth() - 1, 15);
      S.model.ops.set("rop0", {team:"F4P_RDT1"});
      S.model.epis.set("re0", {id:"re0", parent:null, target:null, interno:sem, st:1, stDate:mesAnterior, ops:["rop0"], type:"Epic"});   // fechado no mês anterior: média = 1
      for (let i = 0; i < 3; i++){
        S.model.ops.set("ropw"+i, {team:"F4P_RDT1"});
        S.model.epis.set("rew"+i, {id:"rew"+i, parent:null, target:null, interno:sem, st:0, stDate:null, ops:["ropw"+i], type:"Epic"});   // ainda abertos: 3
      }
      return f4pRoadmapTrend("F4P_RDT1", st);
    }""")
    assert r == "▲"

def test_roadmap_tendencia_soma_abertos_ao_mes_atual_exemplo_piora(page):
    """Média 2, mês atual 0, 1 aberto: 0+1=1 < 2 → piora."""
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      S.model.stages.epi = ["Backlog", "Fechado"];
      const sem = semestre(TODAY);
      S.f.int = sem;
      const st = {kind:"current", start:new Date(TODAY.getFullYear(), TODAY.getMonth() - 1, 1), end:new Date(TODAY.getFullYear(), TODAY.getMonth() + 6, 0)};
      const mesAnterior = new Date(TODAY.getFullYear(), TODAY.getMonth() - 1, 10);
      for (let i = 0; i < 2; i++){
        S.model.ops.set("rop"+i, {team:"F4P_RDT2"});
        S.model.epis.set("re"+i, {id:"re"+i, parent:null, target:null, interno:sem, st:1, stDate:mesAnterior, ops:["rop"+i], type:"Epic"});   // fechados no mês anterior: média = 2
      }
      S.model.ops.set("ropw0", {team:"F4P_RDT2"});
      S.model.epis.set("rew0", {id:"rew0", parent:null, target:null, interno:sem, st:0, stDate:null, ops:["ropw0"], type:"Epic"});   // aberto: 1
      return f4pRoadmapTrend("F4P_RDT2", st);
    }""")
    assert r == "▼"

def test_roadmap_tendencia_soma_abertos_ao_mes_atual_exemplo_estavel(page):
    """Média 3, mês atual 2, 1 aberto: 2+1=3 == 3 → estável."""
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      S.model.stages.epi = ["Backlog", "Fechado"];
      const sem = semestre(TODAY);
      S.f.int = sem;
      const st = {kind:"current", start:new Date(TODAY.getFullYear(), TODAY.getMonth() - 1, 1), end:new Date(TODAY.getFullYear(), TODAY.getMonth() + 6, 0)};
      const mesAnterior = new Date(TODAY.getFullYear(), TODAY.getMonth() - 1, 10), mesAtual = new Date(TODAY.getFullYear(), TODAY.getMonth(), 1);
      for (let i = 0; i < 3; i++){
        S.model.ops.set("rop"+i, {team:"F4P_RDT3"});
        S.model.epis.set("re"+i, {id:"re"+i, parent:null, target:null, interno:sem, st:1, stDate:mesAnterior, ops:["rop"+i], type:"Epic"});   // fechados no mês anterior: média = 3
      }
      for (let i = 0; i < 2; i++){
        S.model.ops.set("ropc"+i, {team:"F4P_RDT3"});
        S.model.epis.set("rec"+i, {id:"rec"+i, parent:null, target:null, interno:sem, st:1, stDate:mesAtual, ops:["ropc"+i], type:"Epic"});   // fechados no mês atual: 2
      }
      S.model.ops.set("ropw0", {team:"F4P_RDT3"});
      S.model.epis.set("rew0", {id:"rew0", parent:null, target:null, interno:sem, st:0, stDate:null, ops:["ropw0"], type:"Epic"});   // aberto: 1
      return f4pRoadmapTrend("F4P_RDT3", st);
    }""")
    assert r == "◆"

def test_roadmap_tendencia_sem_meses_anteriores_fica_neutra(page):
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      const st = {kind:"current", start:new Date(TODAY.getFullYear(), TODAY.getMonth(), 1), end:new Date(TODAY.getFullYear(), TODAY.getMonth() + 6, 0)};
      return f4pRoadmapTrend("F4P_RD_VAZIO", st);
    }""")
    assert r == "◆"

def test_roadmap_clique_no_numero_abre_lista_de_epicos_com_situacao_do_proprio_quadro(page):
    """Clicar em qualquer um dos três números (Roadmap, Roadmap entregue, Atual) abre a lista dos
    épicos considerados, com a Situação sendo a coluna do próprio quadro de Épicos (não a categoria de
    fluxo operacional de nenhum time)."""
    carregar(page, "times.xlsx")
    alvo_id = page.evaluate("""()=>{
      S.model.stages.epi = ["Backlog", "Fechado"];
      const sem = semestre(TODAY);
      S.f.team = 'CORE'; S.f.int = sem;
      S.model.ops.set("rop1", {team:"CORE"});
      S.model.epis.set("re_click", {id:"re_click", parent:null, target:TODAY, interno:sem, st:0, stDate:null, ops:["rop1"], type:"Epic"});
      render();
      return "re_click";
    }""")
    page.click("#f4pTab")
    page.click('button[data-f4p-road-team="CORE"][data-f4p-road-set="roadmap"]')
    assert page.is_visible("#f4pItemsBg")
    assert alvo_id in page.inner_text("#f4pItemsBody")
    assert "Backlog" in page.inner_text("#f4pItemsBody")    # Situação = coluna do quadro de Épicos, não catOf
    page.click(f'button[data-f4p-go="{alvo_id}"]')
    assert not page.is_visible("#f4pItemsBg")
    assert not page.is_visible("#f4pPanel.open")
    assert page.evaluate("document.getElementById('goto').value") == alvo_id

def test_roadmap_epicos_aparece_calculado_no_painel(page):
    carregar(page, "f4p.xlsx")
    page.evaluate("()=>{ S.f.team='CORE'; S.f.exec=semestre(TODAY); render(); }")
    page.click("#f4pTab")
    assert "Roadmap – Épicos (roadmap vs roadmap entregue vs atual)" in page.inner_text("#f4pBody")
    assert "f4p-sep" in page.evaluate("f4pRoadmapEpiCell('CORE')")

def test_configuracao_epi_types_tem_padrao_epic(page):
    r = page.evaluate("()=>{ const c = normCfg({}); return c.f4p.epiTypes; }")
    assert r == ["epic"]

def test_configuracao_epi_types_persiste_e_entra_na_exportacao(page):
    carregar(page, "times.xlsx")
    page.evaluate("()=>{ CFG.f4p.epiTypes = ['epic', 'feature']; }")
    page.click("#btnCfg")
    with page.expect_download() as d:
        page.click("#cfgExport")
    txt = open(d.value.path(), encoding="utf-8").read()
    assert '"epiTypes"' in txt and '"feature"' in txt

# Decisão 0026: reforço do vínculo épico↔time — o vínculo é sempre pelos itens filhos (Parent → Child),
# nunca por Target Date do épico ou pelo vínculo com a iniciativa. Cenário de falha relatado pelo
# usuário: um épico aparecer contabilizado no time errado quando todos os seus itens filhos são de
# outro time. Investigação confirmou que a decisão 0025 já implementava a regra corretamente nos três
# números (Roadmap, Roadmap entregue, Atual) e nos dois branches (Interno e Executivo); os testes abaixo
# travam esse comportamento explicitamente, cobrindo os casos que ainda não tinham um teste dedicado.

def test_roadmap_executivo_epico_conta_so_para_o_time_dos_itens_filhos(page):
    """Cenário de falha do usuário: épico vinculado (via iniciativa do Roadmap Executivo) ao time CORE,
    mas cujos itens filhos são todos do MOBILE — deve contar só para o MOBILE, nunca para o CORE."""
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      S.model.stages.epi = ["Backlog", "Fechado"];
      const sem = semestre(TODAY);
      S.f.exec = sem;
      S.model.ops.set("mop1", {team:"F4P_V26_MOBILE"});
      S.model.epis.set("emix", {id:"emix", parent:"rmix", target:null, interno:null, st:0, stDate:null, ops:["mop1"], type:"Epic"});
      S.model.rels.set("rmix", {id:"rmix", parent:"imix", epis:["emix"]});
      S.model.inis.set("imix", {id:"imix", exec:sem, rels:["rmix"]});
      return {core: f4pRoadmapEpis("F4P_V26_CORE").map(e=>e.id), mobile: f4pRoadmapEpis("F4P_V26_MOBILE").map(e=>e.id)};
    }""")
    assert r == {"core": [], "mobile": ["emix"]}

def test_roadmap_interno_epico_conta_so_para_o_time_dos_itens_filhos(page):
    """Mesmo cenário de falha, mas no Roadmap Interno (Target Date do próprio épico): o vínculo com o
    time continua sendo só pelos itens filhos, não pelo Target Date."""
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      S.model.stages.epi = ["Backlog", "Fechado"];
      const sem = semestre(TODAY);
      S.f.int = sem;
      S.model.ops.set("mop2", {team:"F4P_V26B_MOBILE"});
      S.model.epis.set("emix2", {id:"emix2", parent:null, target:TODAY, interno:sem, st:0, stDate:null, ops:["mop2"], type:"Epic"});
      return {core: f4pRoadmapEpis("F4P_V26B_CORE").map(e=>e.id), mobile: f4pRoadmapEpis("F4P_V26B_MOBILE").map(e=>e.id)};
    }""")
    assert r == {"core": [], "mobile": ["emix2"]}

def test_roadmap_entregue_epico_conta_so_para_o_time_dos_itens_filhos(page):
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      S.model.stages.epi = ["Backlog", "Fechado"];
      const sem = semestre(TODAY);
      S.f.int = sem;
      S.model.ops.set("mop3", {team:"F4P_V26C_MOBILE"});
      S.model.epis.set("emix3", {id:"emix3", parent:null, target:TODAY, interno:sem, st:1, stDate:TODAY, ops:["mop3"], type:"Epic"});   // fechado
      return {core: f4pRoadmapEntregueEpis("F4P_V26C_CORE").map(e=>e.id), mobile: f4pRoadmapEntregueEpis("F4P_V26C_MOBILE").map(e=>e.id)};
    }""")
    assert r == {"core": [], "mobile": ["emix3"]}

def test_atual_epico_conta_so_para_o_time_dos_itens_filhos(page):
    """'Atual' já é independente do Target Date e do vínculo com iniciativa (decisão 0025), mas continua
    dependendo do vínculo com o time pelos itens filhos — mesmo cenário de falha, aplicado ao Atual."""
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      S.model.stages.epi = ["Backlog", "Fechado"];
      const sem = semestre(TODAY);
      S.f.int = sem;
      const st = f4pSemesterState();
      const dentro = new Date(st.start.getTime() + 5 * 864e5);
      S.model.ops.set("mop4", {team:"F4P_V26D_MOBILE"});
      S.model.epis.set("emix4", {id:"emix4", parent:null, target:null, interno:null, st:1, stDate:dentro, ops:["mop4"], type:"Epic"});
      return {core: f4pAtualEpis("F4P_V26D_CORE", st).map(e=>e.id), mobile: f4pAtualEpis("F4P_V26D_MOBILE", st).map(e=>e.id)};
    }""")
    assert r == {"core": [], "mobile": ["emix4"]}

def test_roadmap_epico_com_itens_de_dois_times_conta_para_ambos(page):
    """Um épico com itens filhos de mais de um time conta para cada time que efetivamente tem item
    vinculado — não é um "dono único"; a exclusão só vale para o time que não tem nenhum item."""
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      S.model.stages.epi = ["Backlog", "Fechado"];
      const sem = semestre(TODAY);
      S.f.int = sem;
      S.model.ops.set("cop1", {team:"F4P_V26E_CORE"});
      S.model.ops.set("mop5", {team:"F4P_V26E_MOBILE"});
      S.model.epis.set("emix5", {id:"emix5", parent:null, target:TODAY, interno:sem, st:0, stDate:null, ops:["cop1", "mop5"], type:"Epic"});
      return {core: f4pRoadmapEpis("F4P_V26E_CORE").map(e=>e.id), mobile: f4pRoadmapEpis("F4P_V26E_MOBILE").map(e=>e.id)};
    }""")
    assert r == {"core": ["emix5"], "mobile": ["emix5"]}

# ---------------- Quadrante 7 · User Story (planejado vs. não planejado) ----------------
# Decisão 0030. Mesmo critério de "entregue" (categoria de fluxo Vazão) do Technical Story/Vazão, mas
# com tipos próprios (CFG.f4p.usTypes, padrão User Story). Planejado/Não planejado são uma PARTIÇÃO do
# conjunto entregue (com/sem a tag de capacidade) — diferente do Vazão, onde Reserva é subconjunto do
# Realizado.

def test_us_conta_so_tipos_configurados_e_entregues(page):
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      S.model.teamFlow.F4P_US1 = ["Backlog", "Vazao"];
      CFG.flow.f4p_us1 = {cat:{vazao:"vazao"}, ct:[]};
      const hoje = new Date();
      S.model.ops.set("u1", {team:"F4P_US1", type:"User Story", stName:"Vazao", deploy:hoje, tags:[]});
      S.model.ops.set("u2", {team:"F4P_US1", type:"Technical Story", stName:"Vazao", deploy:hoje, tags:[]});   // tipo não configurado (default só User Story): não conta
      S.model.ops.set("u3", {team:"F4P_US1", type:"User Story", stName:"Backlog", deploy:null, tags:[]});      // não entregue: não conta
      S.f.exec = semestre(TODAY);
      return f4pUsOps("F4P_US1", f4pSemesterState()).length;
    }""")
    assert r == 1

def test_us_planejado_e_nao_planejado_sao_particao_exata(page):
    """Diferente do Vazão (Reserva ⊆ Realizado), aqui Planejado + Não planejado = todo o entregue, sem
    sobreposição: cada item está num dos dois grupos, nunca nos dois."""
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      S.model.teamFlow.F4P_US2 = ["Backlog", "Vazao"];
      CFG.flow.f4p_us2 = {cat:{vazao:"vazao"}, ct:[]};
      const hoje = new Date();
      S.model.ops.set("u1", {team:"F4P_US2", type:"User Story", stName:"Vazao", deploy:hoje, tags:["ROADMAP"]});
      S.model.ops.set("u2", {team:"F4P_US2", type:"User Story", stName:"Vazao", deploy:hoje, tags:["Roadmap"]});   // mesma tag, outra caixa
      S.model.ops.set("u3", {team:"F4P_US2", type:"User Story", stName:"Vazao", deploy:hoje, tags:[]});
      S.f.exec = semestre(TODAY);
      const st = f4pSemesterState();
      return {planejado: f4pUsPlanejadoItems("F4P_US2", st).length, naoPlanejado: f4pUsNaoPlanejadoItems("F4P_US2", st).length, total: f4pUsOps("F4P_US2", st).length};
    }""")
    assert r == {"planejado": 2, "naoPlanejado": 1, "total": 3}

def test_us_usa_tag_de_capacidade_configuravel(page):
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      S.model.teamFlow.F4P_US3 = ["Backlog", "Vazao"];
      CFG.flow.f4p_us3 = {cat:{vazao:"vazao"}, ct:[]};
      CFG.anTag = "CAPACIDADE";
      const hoje = new Date();
      S.model.ops.set("u1", {team:"F4P_US3", type:"User Story", stName:"Vazao", deploy:hoje, tags:["CAPACIDADE"]});
      S.model.ops.set("u2", {team:"F4P_US3", type:"User Story", stName:"Vazao", deploy:hoje, tags:["ROADMAP"]});   // tag antiga: não conta mais como planejado
      S.f.exec = semestre(TODAY);
      const st = f4pSemesterState();
      const r = {planejado: f4pUsPlanejadoItems("F4P_US3", st).length, naoPlanejado: f4pUsNaoPlanejadoItems("F4P_US3", st).length};
      CFG.anTag = "ROADMAP";
      return r;
    }""")
    assert r == {"planejado": 1, "naoPlanejado": 1}

def test_us_usa_tipos_configuraveis_proprios_independentes_do_ct(page):
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      S.model.teamFlow.F4P_US4 = ["Backlog", "Vazao"];
      CFG.flow.f4p_us4 = {cat:{vazao:"vazao"}, ct:[]};
      CFG.f4p.usTypes = ["feature"];
      const hoje = new Date();
      S.model.ops.set("u1", {team:"F4P_US4", type:"Feature", stName:"Vazao", deploy:hoje, tags:[]});
      S.model.ops.set("u2", {team:"F4P_US4", type:"User Story", stName:"Vazao", deploy:hoje, tags:[]});   // não é mais o tipo configurado
      S.f.exec = semestre(TODAY);
      const n = f4pUsOps("F4P_US4", f4pSemesterState()).length;
      CFG.f4p.usTypes = ["user story"];
      return n;
    }""")
    assert r == 1

def test_us_ignora_itens_em_backlog_discovery_ou_wip(page):
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      S.model.teamFlow.F4P_US5 = ["Backlog", "Discovery", "WIP", "Vazao"];
      CFG.flow.f4p_us5 = {cat:{discovery:"disc", wip:"wip", vazao:"vazao"}, ct:[]};
      S.f.exec = semestre(TODAY);
      const hoje = new Date();
      S.model.ops.set("b1", {team:"F4P_US5", type:"User Story", stName:"Backlog", deploy:null, tags:[]});
      S.model.ops.set("d1", {team:"F4P_US5", type:"User Story", stName:"Discovery", deploy:null, tags:[]});
      S.model.ops.set("w1", {team:"F4P_US5", type:"User Story", stName:"WIP", deploy:null, tags:[]});
      S.model.ops.set("v1", {team:"F4P_US5", type:"User Story", stName:"Vazao", deploy:hoje, tags:[]});
      return f4pUsOps("F4P_US5", f4pSemesterState()).length;
    }""")
    assert r == 1

def test_us_semestre_atual_ignora_entregues_antes_do_inicio_do_semestre(page):
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      S.model.teamFlow.F4P_US6 = ["Backlog", "Vazao"];
      CFG.flow.f4p_us6 = {cat:{vazao:"vazao"}, ct:[]};
      S.f.exec = semestre(TODAY);
      const inicioDoSemestre = f4pSemesterState().start;
      const antesDoSemestre = new Date(inicioDoSemestre.getTime() - 864e5);
      const depoisDoInicio = new Date(inicioDoSemestre.getTime() + 5 * 864e5);
      S.model.ops.set("u1", {team:"F4P_US6", type:"User Story", stName:"Vazao", deploy:antesDoSemestre, tags:[]});
      S.model.ops.set("u2", {team:"F4P_US6", type:"User Story", stName:"Vazao", deploy:depoisDoInicio, tags:[]});
      return f4pUsOps("F4P_US6", f4pSemesterState()).length;
    }""")
    assert r == 1

def test_us_semestre_passado_conta_so_entregues_no_periodo(page):
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      S.model.teamFlow.F4P_US7 = ["Backlog", "Vazao"];
      CFG.flow.f4p_us7 = {cat:{vazao:"vazao"}, ct:[]};
      const curStart = f4pSemStart(semestre(TODAY));
      const prevMid = new Date(curStart.getFullYear(), curStart.getMonth() - 3, 15);
      const prevSem = semestre(prevMid);
      S.model.ops.set("u1", {team:"F4P_US7", type:"User Story", stName:"Vazao", deploy:prevMid, tags:[]});
      S.model.ops.set("u2", {team:"F4P_US7", type:"User Story", stName:"Backlog", deploy:null, tags:[]});
      S.model.ops.set("u3", {team:"F4P_US7", type:"User Story", stName:"Vazao", deploy:curStart, tags:[]});
      S.f.int = prevSem;
      return f4pUsOps("F4P_US7", f4pSemesterState()).length;
    }""")
    assert r == 1

def test_us_tendencia_soma_wip_ao_mes_atual_exemplo_melhora(page):
    """Mesmo exemplo exato do Vazão (decisão 0023): média 1, mês atual 0, 3 itens em WIP: 0+3=3 > 1 → melhora."""
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      S.model.teamFlow.F4P_UST1 = ["Backlog", "WIP", "Vazao"];
      CFG.flow.f4p_ust1 = {cat:{wip:"wip", vazao:"vazao"}, ct:[]};
      const st = {kind:"current", start:new Date(TODAY.getFullYear(), TODAY.getMonth() - 1, 1), end:new Date(TODAY.getFullYear(), TODAY.getMonth() + 6, 0)};
      const mesAnterior = new Date(TODAY.getFullYear(), TODAY.getMonth() - 1, 15);
      S.model.ops.set("v1", {team:"F4P_UST1", type:"User Story", stName:"Vazao", deploy:mesAnterior, tags:[]});
      for (let i = 0; i < 3; i++) S.model.ops.set("w"+i, {team:"F4P_UST1", type:"User Story", stName:"WIP", deploy:null, tags:[]});
      return f4pUsTrend("F4P_UST1", st);
    }""")
    assert r == "▲"

def test_us_tendencia_soma_wip_ao_mes_atual_exemplo_piora(page):
    """Média 2, mês atual 0, 1 item em WIP: 0+1=1 < 2 → piora."""
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      S.model.teamFlow.F4P_UST2 = ["Backlog", "WIP", "Vazao"];
      CFG.flow.f4p_ust2 = {cat:{wip:"wip", vazao:"vazao"}, ct:[]};
      const st = {kind:"current", start:new Date(TODAY.getFullYear(), TODAY.getMonth() - 1, 1), end:new Date(TODAY.getFullYear(), TODAY.getMonth() + 6, 0)};
      const mesAnterior = new Date(TODAY.getFullYear(), TODAY.getMonth() - 1, 10);
      for (let i = 0; i < 2; i++) S.model.ops.set("v"+i, {team:"F4P_UST2", type:"User Story", stName:"Vazao", deploy:mesAnterior, tags:[]});
      S.model.ops.set("w0", {team:"F4P_UST2", type:"User Story", stName:"WIP", deploy:null, tags:[]});
      return f4pUsTrend("F4P_UST2", st);
    }""")
    assert r == "▼"

def test_us_tendencia_soma_wip_ao_mes_atual_exemplo_estavel(page):
    """Média 3, mês atual 2, 1 item em WIP: 2+1=3 == 3 → estável."""
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      S.model.teamFlow.F4P_UST3 = ["Backlog", "WIP", "Vazao"];
      CFG.flow.f4p_ust3 = {cat:{wip:"wip", vazao:"vazao"}, ct:[]};
      const st = {kind:"current", start:new Date(TODAY.getFullYear(), TODAY.getMonth() - 1, 1), end:new Date(TODAY.getFullYear(), TODAY.getMonth() + 6, 0)};
      const mesAnterior = new Date(TODAY.getFullYear(), TODAY.getMonth() - 1, 10), mesAtual = new Date(TODAY.getFullYear(), TODAY.getMonth(), 1);
      for (let i = 0; i < 3; i++) S.model.ops.set("v"+i, {team:"F4P_UST3", type:"User Story", stName:"Vazao", deploy:mesAnterior, tags:[]});
      for (let i = 0; i < 2; i++) S.model.ops.set("c"+i, {team:"F4P_UST3", type:"User Story", stName:"Vazao", deploy:mesAtual, tags:[]});
      S.model.ops.set("w0", {team:"F4P_UST3", type:"User Story", stName:"WIP", deploy:null, tags:[]});
      return f4pUsTrend("F4P_UST3", st);
    }""")
    assert r == "◆"

def test_us_tendencia_sem_meses_anteriores_fica_neutra(page):
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      const st = {kind:"current", start:new Date(TODAY.getFullYear(), TODAY.getMonth(), 1), end:new Date(TODAY.getFullYear(), TODAY.getMonth() + 6, 0)};
      return f4pUsTrend("F4P_US_VAZIO", st);
    }""")
    assert r == "◆"

def test_us_wip_conta_so_tipos_configurados_do_time(page):
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      S.model.teamFlow.F4P_UST5 = ["Backlog", "WIP", "Vazao"];
      CFG.flow.f4p_ust5 = {cat:{wip:"wip", vazao:"vazao"}, ct:[]};
      S.model.ops.set("w1", {team:"F4P_UST5", type:"User Story", stName:"WIP", deploy:null, tags:[]});
      S.model.ops.set("w2", {team:"F4P_UST5", type:"Technical Story", stName:"WIP", deploy:null, tags:[]});   // tipo não configurado: não conta
      S.model.ops.set("w3", {team:"F4P_UST5_OUTRO", type:"User Story", stName:"WIP", deploy:null, tags:[]});   // outro time: não conta
      return f4pUsWipCount("F4P_UST5");
    }""")
    assert r == 1

def test_us_clique_no_planejado_abre_lista_e_permite_navegar(page):
    carregar(page, "f4p.xlsx")
    alvo_id = page.evaluate("""()=>{
      S.f.team='CORE'; S.f.exec=semestre(TODAY);
      [...S.model.ops.values()].filter(o=>o.team==='CORE').forEach(o => { o.deploy = null; });
      const alvo = [...S.model.ops.values()].find(o=>o.team==='CORE');
      alvo.type = 'User Story'; alvo.tags = ['ROADMAP'];
      alvo.deploy = new Date(f4pSemesterState().start.getTime() + 5 * 864e5);
      render();
      return alvo.id;
    }""")
    page.click("#f4pTab")
    page.click('button[data-f4p-us-team="CORE"][data-f4p-us-set="planejado"]')
    assert page.is_visible("#f4pItemsBg")
    rows = page.locator("#f4pItemsBody tbody tr")
    assert rows.count() == 1
    assert alvo_id in page.inner_text("#f4pItemsBody")
    page.click(f'button[data-f4p-go="{alvo_id}"]')
    assert not page.is_visible("#f4pItemsBg")
    assert not page.is_visible("#f4pPanel.open")
    assert page.evaluate("document.getElementById('goto').value") == alvo_id

def test_us_clique_no_nao_planejado_mostra_so_os_sem_a_tag(page):
    carregar(page, "f4p.xlsx")
    page.evaluate("""()=>{
      S.f.team='CORE'; S.f.exec=semestre(TODAY);
      [...S.model.ops.values()].filter(o=>o.team==='CORE').forEach(o => { o.deploy = null; });
      const dentro = new Date(f4pSemesterState().start.getTime() + 5 * 864e5);
      const ops = [...S.model.ops.values()].filter(o=>o.team==='CORE').slice(0, 2);
      ops[0].type = 'User Story'; ops[0].deploy = dentro; ops[0].tags = ['ROADMAP'];
      ops[1].type = 'User Story'; ops[1].deploy = dentro; ops[1].tags = [];
      render();
    }""")
    page.click("#f4pTab")
    page.click('button[data-f4p-us-team="CORE"][data-f4p-us-set="naoplanejado"]')
    assert page.is_visible("#f4pItemsBg")
    assert page.locator("#f4pItemsBody tbody tr").count() == 1

def test_us_aparece_calculado_no_painel(page):
    carregar(page, "f4p.xlsx")
    page.evaluate("()=>{ S.f.team='CORE'; S.f.exec=semestre(TODAY); render(); }")
    page.click("#f4pTab")
    assert "User Story (planejado vs não planejado)" in page.inner_text("#f4pBody")
    assert "f4p-sep" in page.evaluate("f4pUsCell('CORE')")

def test_configuracao_us_types_tem_padrao_user_story(page):
    r = page.evaluate("()=>{ const c = normCfg({}); return c.f4p.usTypes; }")
    assert r == ["user story"]

def test_configuracao_us_types_persiste_e_entra_na_exportacao(page):
    carregar(page, "times.xlsx")
    page.evaluate("()=>{ CFG.f4p.usTypes = ['user story', 'feature']; }")
    page.click("#btnCfg")
    with page.expect_download() as d:
        page.click("#cfgExport")
    txt = open(d.value.path(), encoding="utf-8").read()
    assert '"usTypes"' in txt and '"feature"' in txt

# ---------------- Conferência cruzada Vazão × Technical Story × User Story (decisão 0030) ----------------
# O usuário pediu uma validação explícita: Vazão Realizado deve ser sempre igual à soma de Technical
# Story Realizado + User Story Planejado + User Story Não planejado (mesmo universo de itens entregues
# no período, recortado por tipo). Exemplo exato dado pelo usuário: MOBILE com 38 no Vazão Realizado,
# distribuídos em 27 Technical Story + 4 User Story planejado + 7 User Story não planejado (38 = 27+4+7).

def test_reconciliacao_bate_com_o_exemplo_exato_do_usuario(page):
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      S.model.teamFlow.MOBILE_RECON = ["Backlog", "WIP", "Vazao"];
      CFG.flow.mobile_recon = {cat:{wip:"wip", vazao:"vazao"}, ct:[]};
      S.model.teams.push("MOBILE_RECON");
      S.f.team = "MOBILE_RECON"; S.f.exec = semestre(TODAY);
      const hoje = new Date();
      for (let i = 0; i < 27; i++) S.model.ops.set("ts"+i, {team:"MOBILE_RECON", type:"Technical Story", stName:"Vazao", deploy:hoje, tags:[]});
      for (let i = 0; i < 4; i++) S.model.ops.set("usp"+i, {team:"MOBILE_RECON", type:"User Story", stName:"Vazao", deploy:hoje, tags:["ROADMAP"]});
      for (let i = 0; i < 7; i++) S.model.ops.set("usn"+i, {team:"MOBILE_RECON", type:"User Story", stName:"Vazao", deploy:hoje, tags:[]});
      render();
      return f4pReconciliacao().find(x => x.team === "MOBILE_RECON");
    }""")
    assert r == {"team": "MOBILE_RECON", "vazao": 38, "ts": 27, "planejado": 4, "naoPlanejado": 7, "soma": 38, "ok": True}

def test_reconciliacao_sinaliza_divergencia_quando_configuracao_de_tipos_diverge(page):
    """Se CFG.f4p.types (Vazão) contar um tipo que os outros dois quadrantes não cobrem (ex.: um
    terceiro tipo além de Technical Story e dos tipos de User Story), a soma diverge — e é exatamente
    esse erro de configuração que a conferência deve sinalizar."""
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      S.model.teamFlow.DIVERGE = ["Backlog", "Vazao"];
      CFG.flow.diverge = {cat:{vazao:"vazao"}, ct:[]};
      CFG.f4p.types = ["user story", "technical story", "internal bug"];
      S.model.teams.push("DIVERGE");
      S.f.team = "DIVERGE"; S.f.exec = semestre(TODAY);
      const hoje = new Date();
      S.model.ops.set("ib1", {team:"DIVERGE", type:"Internal Bug", stName:"Vazao", deploy:hoje, tags:[]});
      S.model.ops.set("us1", {team:"DIVERGE", type:"User Story", stName:"Vazao", deploy:hoje, tags:[]});
      render();
      const rec = f4pReconciliacao().find(x => x.team === "DIVERGE");
      CFG.f4p.types = ["user story", "technical story"];
      return rec;
    }""")
    assert r == {"team": "DIVERGE", "vazao": 2, "ts": 0, "planejado": 0, "naoPlanejado": 1, "soma": 1, "ok": False}

def test_reconciliacao_banner_aparece_so_quando_ha_divergencia(page):
    carregar(page, "f4p.xlsx")
    page.evaluate("""()=>{
      S.model.teamFlow.DIVERGE2 = ["Backlog", "Vazao"];
      CFG.flow.diverge2 = {cat:{vazao:"vazao"}, ct:[]};
      CFG.f4p.types = ["user story", "technical story", "internal bug"];
      S.model.teams.push("DIVERGE2");
      S.f.team = "DIVERGE2"; S.f.exec = semestre(TODAY);
      const hoje = new Date();
      S.model.ops.set("ib1", {team:"DIVERGE2", type:"Internal Bug", stName:"Vazao", deploy:hoje, tags:[]});
      render();
    }""")
    page.click("#f4pTab")
    assert page.locator(".f4p-recon").count() == 1
    assert "DIVERGE2" in page.inner_text(".f4p-recon")
    assert "Vazão Realizado" in page.inner_text(".f4p-recon")
    page.evaluate("()=>{ CFG.f4p.types = ['user story', 'technical story']; render(); }")
    assert page.locator(".f4p-recon").count() == 0
