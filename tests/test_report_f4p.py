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
    """Nenhum quadrante fica mais "em definição" no painel atual (os 8 têm regra fechada, decisão 0031),
    mas o código genérico que renderiza esse estado continua coberto — útil se um quadrante futuro for
    adicionado sem regra ainda. Sinaliza um quadrante existente como não pronto diretamente no teste."""
    carregar(page, "f4p.xlsx")
    page.evaluate("()=>{ S.f.team='CORE'; S.f.exec=semestre(TODAY); F4P_QUADS.eff.done=false; render(); }")
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
    assert page.evaluate("document.getElementById('fBusca').value") == alvo_id

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
    assert page.evaluate("document.getElementById('fBusca').value") == alvo_id

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

# ---------------- Cor do ID por categoria de fluxo nos modais de itens (decisão 0049) ----------------
# O fundo do ID (.idb) no modal de itens (f4pItemsModal) era sempre verde (cor de Vazão), mesmo para
# itens em Backlog/Discovery/WIP — dando a entender que tudo já tinha sido entregue. Passa a usar a mesma
# paleta de categoria de fluxo (.fb, Configurações › Fluxo dos times) do resto do portal: neutro
# (Backlog), azul claro (Discovery), azul escuro (WIP) e verde (Vazão). Épicos (Roadmap – Épicos) não têm
# categoria de fluxo (catOf é de item operacional) — usam f4pEpiCatClass, uma regra própria.

def test_idb_usa_a_cor_da_categoria_de_fluxo_do_item(page):
    carregar(page, "times.xlsx")   # fluxo do CORE tem coluna de Discovery (Refinamento)
    page.evaluate("""()=>{
      const mk = (id, stName, deploy) => ({id, title:id, team:'CORE', stName, deploy: deploy || null});
      f4pItemsModal('teste', [
        mk('I1', 'Backlog'),
        mk('I2', 'Refinamento'),
        mk('I3', 'Em Desenvolvimento'),
        mk('I4', 'Fechado', new Date(2026,6,21)),
      ]);
    }""")
    classes = page.locator("#f4pItemsBody .idb").evaluate_all("els => els.map(e => e.className)")
    assert classes == ["idb none", "idb disc", "idb wip", "idb vazao"]

def test_idb_aceita_catFn_proprio_no_lugar_de_catOf(page):
    """f4pItemsModal aceita um catFn próprio (4º parâmetro) — usado pelo Roadmap – Épicos, que lista
    épicos, não itens operacionais (catOf não se aplica a eles)."""
    carregar(page, "times.xlsx")
    page.evaluate("""()=>{ f4pItemsModal('teste', [{id:'X1', title:'X1'}], null, () => 'wip'); }""")
    assert page.locator("#f4pItemsBody .idb").get_attribute("class") == "idb wip"

def test_f4pEpiCatClass_e_verde_so_quando_o_epico_esta_fechado(page):
    carregar(page, "f4p.xlsx")
    page.evaluate("""()=>{ S.model.stages.epi = ["Backlog", "Fechado"]; }""")
    r = page.evaluate("""()=>{
      return {aberto: f4pEpiCatClass({st:0}), fechado: f4pEpiCatClass({st:1}), semStatus: f4pEpiCatClass({st:-1})};
    }""")
    assert r == {"aberto": "none", "fechado": "vazao", "semStatus": "none"}

def test_clique_no_roadmap_epicos_colore_o_id_pela_coluna_do_proprio_quadro(page):
    carregar(page, "f4p.xlsx")
    page.evaluate("""()=>{
      S.model.stages.epi = ["Backlog", "Fechado"];
      const sem = semestre(TODAY);
      S.f.team = "CORE"; S.f.int = sem;
      S.model.ops.set("repi1", {team:"CORE"});
      S.model.epis.set("REPI1", {id:"REPI1", parent:null, target:null, interno:sem, st:1, stDate:null, ops:["repi1"], type:"Epic"});
      render();
    }""")
    page.click("#f4pTab")
    page.click('button[data-f4p-road-team="CORE"][data-f4p-road-set="roadmap"]')
    assert page.is_visible("#f4pItemsBg")
    assert page.locator("#f4pItemsBody .idb").get_attribute("class") == "idb vazao"   # épico fechado

# ---------------- Quadrante 5 · Vazão (reserva vs. reserva entregue vs. realizado) ----------------
# Decisão 0022 (Realizado) e 0048 (Reserva). Realizado: itens **entregues** (categoria de fluxo Vazão)
# dos tipos configurados para o CT (CFG.f4p.types, padrão User Story e Technical Story), cuja saída caiu
# no calendário exato do semestre selecionado — com ou sem a tag de capacidade. Reserva: a mesma
# capacidade do roadmap mostrada pela Visão analítica (§10) para o time — itens dos tipos CFG.ctTypes com
# a tag de capacidade (CFG.anTag) cujo épico está comprometido com o roadmap selecionado, em **qualquer
# status** (não só entregue). Por não depender mais do Realizado, Reserva deixou de ser, por construção,
# um subconjunto dele (decisão 0048, revendo a 0022).

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

def test_vazao_reserva_conta_qualquer_status_do_epico_comprometido(page):
    """Decisão 0048: diferente do Realizado, a Reserva não exige que o item já esteja entregue — conta
    todo item do time com a tag de capacidade cujo épico está comprometido com o roadmap selecionado,
    esteja ele em Backlog, WIP ou já em Vazão."""
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      S.model.teamFlow.F4P_VZ2 = ["Backlog", "WIP", "Vazao"];
      CFG.flow.f4p_vz2 = {cat:{wip:"wip", vazao:"vazao"}, ct:[]};
      const sem = semestre(TODAY);
      S.f.int = sem;
      S.model.epis.set("evz2", {id:"evz2", valid:true, parent:null, target:null, interno:sem, st:0, stDate:null, ops:[], type:"Epic"});
      S.model.ops.set("v1", {team:"F4P_VZ2", type:"User Story", stName:"Backlog", deploy:null, tags:["ROADMAP"], epicoId:"evz2"});
      S.model.ops.set("v2", {team:"F4P_VZ2", type:"User Story", stName:"WIP", deploy:null, tags:["Roadmap"], epicoId:"evz2"});   // mesma tag, outra caixa
      S.model.ops.set("v3", {team:"F4P_VZ2", type:"User Story", stName:"Vazao", deploy:new Date(), tags:[], epicoId:"evz2"});   // sem tag: não conta na reserva
      const st = f4pSemesterState();
      return {reserva: f4pVazaoReservaItems("F4P_VZ2", st).length, realizado: f4pVazaoRealizadoItems("F4P_VZ2", st).length};
    }""")
    assert r == {"reserva": 2, "realizado": 1}

def test_vazao_reserva_usa_tag_de_capacidade_configuravel(page):
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      S.model.teamFlow.F4P_VZ3 = ["Backlog", "Vazao"];
      CFG.flow.f4p_vz3 = {cat:{vazao:"vazao"}, ct:[]};
      CFG.anTag = "CAPACIDADE";
      const sem = semestre(TODAY);
      S.f.int = sem;
      S.model.epis.set("evz3", {id:"evz3", valid:true, parent:null, target:null, interno:sem, st:0, stDate:null, ops:[], type:"Epic"});
      S.model.ops.set("v1", {team:"F4P_VZ3", type:"User Story", stName:"Backlog", deploy:null, tags:["CAPACIDADE"], epicoId:"evz3"});
      S.model.ops.set("v2", {team:"F4P_VZ3", type:"User Story", stName:"Backlog", deploy:null, tags:["ROADMAP"], epicoId:"evz3"});   // tag antiga: não conta mais
      const n = f4pVazaoReservaItems("F4P_VZ3", f4pSemesterState()).length;
      CFG.anTag = "ROADMAP";
      return n;
    }""")
    assert r == 1

def test_vazao_reserva_bate_com_capacidade_da_visao_analitica(page):
    """O pedido original do usuário (decisão 0048): a Reserva deste quadrante deve bater com a
    Capacidade mostrada na Visão analítica (§10) para o mesmo time e semestre — as duas passaram a somar
    exatamente o mesmo conjunto de itens."""
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      const team = "F4P_VZCAP", sem = semestre(TODAY);
      S.model.teamFlow[team] = ["Backlog", "WIP", "Vazao"];
      CFG.flow[team.toLowerCase()] = {cat:{wip:"wip", vazao:"vazao"}, ct:[]};
      const opKeys = ["c0", "c1", "c2", "c3"];
      S.model.ops.set("c0", {team, type:"User Story", stName:"Backlog", deploy:null, tags:["ROADMAP"], epicoId:"EPI_VZCAP"});
      S.model.ops.set("c1", {team, type:"User Story", stName:"WIP", deploy:null, tags:["ROADMAP"], epicoId:"EPI_VZCAP"});
      S.model.ops.set("c2", {team, type:"Technical Story", stName:"Vazao", deploy:new Date(2026,0,10), tags:["ROADMAP"], epicoId:"EPI_VZCAP"});
      S.model.ops.set("c3", {team, type:"User Story", stName:"Backlog", deploy:null, tags:[], epicoId:"EPI_VZCAP"});   // sem tag: fora dos dois números
      S.model.inis.set("INI_VZCAP", {id:"INI_VZCAP", valid:true, title:"Ini", exec:sem, owner:null, rels:["REL_VZCAP"]});
      S.model.rels.set("REL_VZCAP", {id:"REL_VZCAP", valid:true, title:"Rel", parent:"INI_VZCAP", epis:["EPI_VZCAP"]});
      S.model.epis.set("EPI_VZCAP", {id:"EPI_VZCAP", valid:true, title:"Epi", parent:"REL_VZCAP", target:null, interno:null, st:0, ops:opKeys, type:"Epic"});
      S.f.team = team; S.f.exec = sem; S.f.int = "";
      render();
      return {cap: anData().cap, reserva: f4pVazaoReservaItems(team, f4pSemesterState()).length};
    }""")
    assert r["cap"] == 3
    assert r["reserva"] == r["cap"]

def test_vazao_reserva_exige_epico_comprometido_mas_realizado_nao(page):
    """Diferente do Realizado (que só olha a data de entrega dentro do calendário do semestre), a
    Reserva exige que o próprio épico do item esteja comprometido com o roadmap selecionado — um item
    tagueado sem épico vinculado (ou cujo épico não bate esse compromisso) conta no Realizado normalmente,
    mas fica fora da Reserva."""
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      S.model.teamFlow.F4P_VZ4B = ["Backlog", "Vazao"];
      CFG.flow.f4p_vz4b = {cat:{vazao:"vazao"}, ct:[]};
      S.f.int = semestre(TODAY);
      const hoje = new Date();
      S.model.ops.set("v1", {team:"F4P_VZ4B", type:"User Story", stName:"Vazao", deploy:hoje, tags:["ROADMAP"]});   // sem epicoId
      const st = f4pSemesterState();
      return {reserva: f4pVazaoReservaItems("F4P_VZ4B", st).length, realizado: f4pVazaoRealizadoItems("F4P_VZ4B", st).length};
    }""")
    assert r == {"reserva": 0, "realizado": 1}

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

# Decisão 0024 (atualizada pela 0048): a seta de tendência (não os números) é colorida por Realizado vs.
# Reserva — verde quando Realizado ≥ Reserva, vermelho quando Realizado < Reserva. Antes da 0048 o
# vermelho era inalcançável (Reserva era sempre um subconjunto do Realizado, por construção — decisão
# 0022); agora que Reserva é a capacidade do roadmap em qualquer status, os três casos passam a ser
# testáveis: Realizado maior, igual e menor que a Reserva.

def test_vazao_seta_de_tendencia_fica_verde_quando_realizado_maior_que_reserva(page):
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      S.model.teamFlow.F4P_VZ10 = ["Backlog", "Vazao"];
      CFG.flow.f4p_vz10 = {cat:{vazao:"vazao"}, ct:[]};
      const sem = semestre(TODAY);
      S.f.int = sem;
      S.model.epis.set("evz10", {id:"evz10", valid:true, parent:null, target:null, interno:sem, st:0, stDate:null, ops:[], type:"Epic"});
      const hoje = new Date();
      S.model.ops.set("v1", {team:"F4P_VZ10", type:"User Story", stName:"Vazao", deploy:hoje, tags:["ROADMAP"], epicoId:"evz10"});
      S.model.ops.set("v2", {team:"F4P_VZ10", type:"User Story", stName:"Vazao", deploy:hoje, tags:[], epicoId:"evz10"});
      return f4pVazaoCell("F4P_VZ10");
    }""")
    assert "f4p-trend f4p-good" in r
    assert "f4p-bad" not in r

def test_vazao_seta_de_tendencia_fica_verde_quando_realizado_igual_reserva(page):
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      S.model.teamFlow.F4P_VZ11 = ["Backlog", "Vazao"];
      CFG.flow.f4p_vz11 = {cat:{vazao:"vazao"}, ct:[]};
      const sem = semestre(TODAY);
      S.f.int = sem;
      S.model.epis.set("evz11", {id:"evz11", valid:true, parent:null, target:null, interno:sem, st:0, stDate:null, ops:[], type:"Epic"});
      const hoje = new Date();
      S.model.ops.set("v1", {team:"F4P_VZ11", type:"User Story", stName:"Vazao", deploy:hoje, tags:["ROADMAP"], epicoId:"evz11"});   // único item, com a tag e o épico comprometido: reserva == realizado
      return f4pVazaoCell("F4P_VZ11");
    }""")
    assert "f4p-trend f4p-good" in r
    assert "f4p-bad" not in r

def test_vazao_seta_de_tendencia_fica_vermelha_quando_realizado_menor_que_reserva(page):
    """Caso novo, só alcançável depois da decisão 0048: um item reservado (tag + épico comprometido)
    ainda em WIP conta na Reserva, mas nada foi entregue ainda — Realizado (0) < Reserva (1)."""
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      S.model.teamFlow.F4P_VZ12 = ["Backlog", "WIP", "Vazao"];
      CFG.flow.f4p_vz12 = {cat:{wip:"wip", vazao:"vazao"}, ct:[]};
      const sem = semestre(TODAY);
      S.f.int = sem;
      S.model.epis.set("evz12", {id:"evz12", valid:true, parent:null, target:null, interno:sem, st:0, stDate:null, ops:[], type:"Epic"});
      S.model.ops.set("v1", {team:"F4P_VZ12", type:"User Story", stName:"WIP", deploy:null, tags:["ROADMAP"], epicoId:"evz12"});
      return f4pVazaoCell("F4P_VZ12");
    }""")
    assert "f4p-trend f4p-bad" in r
    assert "f4p-good" not in r

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
    assert page.evaluate("document.getElementById('fBusca').value") == alvo_id

def test_vazao_clique_na_reserva_mostra_so_os_com_a_tag(page):
    """Decisão 0048: a Reserva não depende mais de data de entrega, então o item nem precisa estar
    entregue — só precisa ter a tag de capacidade e um épico comprometido com o roadmap selecionado."""
    carregar(page, "f4p.xlsx")
    page.evaluate("""()=>{
      S.f.team='CORE'; S.f.exec=semestre(TODAY);
      const sem = semestre(TODAY);
      S.model.inis.set("INI_VZCLICK", {id:"INI_VZCLICK", valid:true, title:"Ini", exec:sem, owner:null, rels:["REL_VZCLICK"]});
      S.model.rels.set("REL_VZCLICK", {id:"REL_VZCLICK", valid:true, title:"Rel", parent:"INI_VZCLICK", epis:["EPI_VZCLICK"]});
      S.model.epis.set("EPI_VZCLICK", {id:"EPI_VZCLICK", valid:true, title:"Epi", parent:"REL_VZCLICK", target:null, interno:null, st:0, ops:[], type:"Epic"});
      const ops = [...S.model.ops.values()].filter(o=>o.team==='CORE').slice(0, 2);
      ops[0].type = 'User Story'; ops[0].tags = ['ROADMAP']; ops[0].epicoId = 'EPI_VZCLICK';
      ops[1].type = 'User Story'; ops[1].tags = []; ops[1].epicoId = 'EPI_VZCLICK';
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
    assert "Vazão (reserva vs reserva entregue vs realizado)" in page.inner_text("#f4pBody")
    assert page.evaluate("f4pVazaoCell('CORE')").count("f4p-sep") == 2

# Decisão 0043: Reserva entregue é o subconjunto da Reserva cujo épico vinculado tem compromisso de
# roadmap (Interno ou Executivo, conforme o filtro) batendo com o semestre selecionado — mesmo critério
# já usado pelo Roadmap – Épicos (f4pRoadmapEpis) para decidir se um épico "está no Roadmap" do
# semestre, reaproveitado aqui sem alterar aquele quadrante.

def test_vazao_reserva_entregue_bate_com_compromisso_interno_do_proprio_epico(page):
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      S.model.teamFlow.F4P_VZRE1 = ["Backlog", "Vazao"];
      CFG.flow.f4p_vzre1 = {cat:{vazao:"vazao"}, ct:[]};
      const sem = semestre(TODAY);
      S.f.int = sem;
      const hoje = new Date();
      S.model.epis.set("evre1", {id:"evre1", parent:null, target:null, interno:sem, st:0, stDate:null, ops:[], type:"Epic"});
      S.model.epis.set("evre2", {id:"evre2", parent:null, target:null, interno:"2099 1", st:0, stDate:null, ops:[], type:"Epic"});   // outro semestre
      S.model.ops.set("v1", {team:"F4P_VZRE1", type:"User Story", stName:"Vazao", deploy:hoje, tags:["ROADMAP"], epicoId:"evre1"});   // compromisso bate
      S.model.ops.set("v2", {team:"F4P_VZRE1", type:"User Story", stName:"Vazao", deploy:hoje, tags:["ROADMAP"], epicoId:"evre2"});   // compromisso de outro semestre
      const st = f4pSemesterState();
      return {reserva: f4pVazaoReservaItems("F4P_VZRE1", st).length, reservaEntregue: f4pVazaoReservaEntregueItems("F4P_VZRE1", st).length};
    }""")
    # Desde a decisão 0048, a própria Reserva já exige compromisso do épico — v2 (compromisso de outro
    # semestre) fica fora dos dois números, não só da Reserva entregue.
    assert r == {"reserva": 1, "reservaEntregue": 1}

def test_vazao_reserva_entregue_usa_iniciativa_quando_roadmap_executivo_ativo(page):
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      S.model.teamFlow.F4P_VZRE2 = ["Backlog", "Vazao"];
      CFG.flow.f4p_vzre2 = {cat:{vazao:"vazao"}, ct:[]};
      const sem = semestre(TODAY);
      S.f.int = ""; S.f.exec = sem;
      const hoje = new Date();
      S.model.rels.set("rvre1", {id:"rvre1", parent:"ivre1", epis:[]});
      S.model.inis.set("ivre1", {id:"ivre1", exec:sem, rels:["rvre1"]});
      S.model.rels.set("rvre2", {id:"rvre2", parent:"ivre2", epis:[]});
      S.model.inis.set("ivre2", {id:"ivre2", exec:"2099 1", rels:["rvre2"]});   // outro semestre
      S.model.epis.set("evre3", {id:"evre3", parent:"rvre1", target:null, interno:"", st:0, stDate:null, ops:[], type:"Epic"});
      S.model.epis.set("evre4", {id:"evre4", parent:"rvre2", target:null, interno:"", st:0, stDate:null, ops:[], type:"Epic"});
      S.model.ops.set("v1", {team:"F4P_VZRE2", type:"User Story", stName:"Vazao", deploy:hoje, tags:["ROADMAP"], epicoId:"evre3"});
      S.model.ops.set("v2", {team:"F4P_VZRE2", type:"User Story", stName:"Vazao", deploy:hoje, tags:["ROADMAP"], epicoId:"evre4"});
      const st = f4pSemesterState();
      const r = {reserva: f4pVazaoReservaItems("F4P_VZRE2", st).length, reservaEntregue: f4pVazaoReservaEntregueItems("F4P_VZRE2", st).length};
      S.f.exec = "";
      return r;
    }""")
    # Mesma observação da decisão 0048: v2 (iniciativa de outro semestre) já não entra na Reserva.
    assert r == {"reserva": 1, "reservaEntregue": 1}

def test_vazao_reserva_entregue_exclui_epico_sem_compromisso_registrado(page):
    """Caso de borda (decisões 0043/0048): um épico sem Target Date (Interno) não bate com nenhum
    semestre — desde a 0048, isso já tira o item da Reserva (que também exige compromisso), não só da
    Reserva entregue."""
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      S.model.teamFlow.F4P_VZRE3 = ["Backlog", "Vazao"];
      CFG.flow.f4p_vzre3 = {cat:{vazao:"vazao"}, ct:[]};
      S.f.int = semestre(TODAY);
      const hoje = new Date();
      S.model.epis.set("evre5", {id:"evre5", parent:null, target:null, interno:"", st:0, stDate:null, ops:[], type:"Epic"});   // sem Target Date
      S.model.ops.set("v1", {team:"F4P_VZRE3", type:"User Story", stName:"Vazao", deploy:hoje, tags:["ROADMAP"], epicoId:"evre5"});
      const st = f4pSemesterState();
      return {reserva: f4pVazaoReservaItems("F4P_VZRE3", st).length, reservaEntregue: f4pVazaoReservaEntregueItems("F4P_VZRE3", st).length};
    }""")
    assert r == {"reserva": 0, "reservaEntregue": 0}

def test_vazao_reserva_entregue_exclui_reserva_sem_epico_vinculado(page):
    """Item reservado sem epicoId (ou apontando pra um épico inexistente) não tem como ter compromisso
    de roadmap — desde a decisão 0048 isso já tira o item da Reserva, não só da Reserva entregue."""
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      S.model.teamFlow.F4P_VZRE4 = ["Backlog", "Vazao"];
      CFG.flow.f4p_vzre4 = {cat:{vazao:"vazao"}, ct:[]};
      S.f.int = semestre(TODAY);
      const hoje = new Date();
      S.model.ops.set("v1", {team:"F4P_VZRE4", type:"User Story", stName:"Vazao", deploy:hoje, tags:["ROADMAP"]});   // sem epicoId
      const st = f4pSemesterState();
      return {reserva: f4pVazaoReservaItems("F4P_VZRE4", st).length, reservaEntregue: f4pVazaoReservaEntregueItems("F4P_VZRE4", st).length};
    }""")
    assert r == {"reserva": 0, "reservaEntregue": 0}

def test_vazao_clique_na_reserva_entregue_mostra_so_os_com_compromisso_no_semestre(page):
    carregar(page, "f4p.xlsx")
    alvo_id = page.evaluate("""()=>{
      S.f.team='CORE'; S.f.int=semestre(TODAY);
      [...S.model.ops.values()].filter(o=>o.team==='CORE').forEach(o => { o.deploy = null; });
      const dentro = new Date(f4pSemesterState().start.getTime() + 5 * 864e5);
      const ops = [...S.model.ops.values()].filter(o=>o.team==='CORE').slice(0, 2);
      S.model.epis.set("evreclick1", {id:"evreclick1", parent:null, target:null, interno:semestre(TODAY), st:0, stDate:null, ops:[], type:"Epic"});
      S.model.epis.set("evreclick2", {id:"evreclick2", parent:null, target:null, interno:"2099 1", st:0, stDate:null, ops:[], type:"Epic"});
      ops[0].type = 'User Story'; ops[0].deploy = dentro; ops[0].tags = ['ROADMAP']; ops[0].epicoId = 'evreclick1';
      ops[1].type = 'User Story'; ops[1].deploy = dentro; ops[1].tags = ['ROADMAP']; ops[1].epicoId = 'evreclick2';
      render();
      return ops[0].id;
    }""")
    page.click("#f4pTab")
    page.click('button[data-f4p-vazao-reserva-entregue-team="CORE"]')
    assert page.is_visible("#f4pItemsBg")
    assert page.locator("#f4pItemsBody tbody tr").count() == 1
    assert alvo_id in page.inner_text("#f4pItemsBody")

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
    assert page.evaluate("document.getElementById('fBusca').value") == alvo_id

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

# Decisão 0043: Reservado/Planejado (outro semestre) são uma segunda partição, desta vez dentro do
# Planejado — mesmo critério de "compromisso de roadmap bate com o semestre selecionado" usado pela
# Reserva entregue do Vazão (reaproveitando f4pEpiCompromissoBate/f4pRoadmapEpis).

def test_us_reservado_e_planejado_outro_semestre_sao_particao_exata_do_planejado(page):
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      S.model.teamFlow.F4P_USRE1 = ["Backlog", "Vazao"];
      CFG.flow.f4p_usre1 = {cat:{vazao:"vazao"}, ct:[]};
      const sem = semestre(TODAY);
      S.f.int = sem;
      const hoje = new Date();
      S.model.epis.set("eusre1", {id:"eusre1", parent:null, target:null, interno:sem, st:0, stDate:null, ops:[], type:"Epic"});
      S.model.epis.set("eusre2", {id:"eusre2", parent:null, target:null, interno:"2099 1", st:0, stDate:null, ops:[], type:"Epic"});
      S.model.ops.set("u1", {team:"F4P_USRE1", type:"User Story", stName:"Vazao", deploy:hoje, tags:["ROADMAP"], epicoId:"eusre1"});   // reservado
      S.model.ops.set("u2", {team:"F4P_USRE1", type:"User Story", stName:"Vazao", deploy:hoje, tags:["ROADMAP"], epicoId:"eusre2"});   // outro semestre
      S.model.ops.set("u3", {team:"F4P_USRE1", type:"User Story", stName:"Vazao", deploy:hoje, tags:["ROADMAP"]});                     // sem épico: outro semestre
      S.model.ops.set("u4", {team:"F4P_USRE1", type:"User Story", stName:"Vazao", deploy:hoje, tags:[]});                              // não planejado
      const st = f4pSemesterState();
      return {
        reservado: f4pUsReservadoItems("F4P_USRE1", st).length,
        planejadoOutro: f4pUsPlanejadoOutroSemestreItems("F4P_USRE1", st).length,
        planejado: f4pUsPlanejadoItems("F4P_USRE1", st).length,
        naoPlanejado: f4pUsNaoPlanejadoItems("F4P_USRE1", st).length,
      };
    }""")
    assert r == {"reservado": 1, "planejadoOutro": 2, "planejado": 3, "naoPlanejado": 1}

def test_us_reservado_usa_compromisso_executivo_da_iniciativa(page):
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      S.model.teamFlow.F4P_USRE2 = ["Backlog", "Vazao"];
      CFG.flow.f4p_usre2 = {cat:{vazao:"vazao"}, ct:[]};
      const sem = semestre(TODAY);
      S.f.int = ""; S.f.exec = sem;
      const hoje = new Date();
      S.model.rels.set("rusre1", {id:"rusre1", parent:"iusre1", epis:[]});
      S.model.inis.set("iusre1", {id:"iusre1", exec:sem, rels:["rusre1"]});
      S.model.epis.set("eusre3", {id:"eusre3", parent:"rusre1", target:null, interno:"", st:0, stDate:null, ops:[], type:"Epic"});
      S.model.ops.set("u1", {team:"F4P_USRE2", type:"User Story", stName:"Vazao", deploy:hoje, tags:["ROADMAP"], epicoId:"eusre3"});
      const st = f4pSemesterState();
      const r = {reservado: f4pUsReservadoItems("F4P_USRE2", st).length, planejadoOutro: f4pUsPlanejadoOutroSemestreItems("F4P_USRE2", st).length};
      S.f.exec = "";
      return r;
    }""")
    assert r == {"reservado": 1, "planejadoOutro": 0}

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

def test_us_clique_no_reservado_abre_lista_e_permite_navegar(page):
    carregar(page, "f4p.xlsx")
    alvo_id = page.evaluate("""()=>{
      S.f.team='CORE'; S.f.int=semestre(TODAY);
      [...S.model.ops.values()].filter(o=>o.team==='CORE').forEach(o => { o.deploy = null; });
      const alvo = [...S.model.ops.values()].find(o=>o.team==='CORE');
      S.model.epis.set("eusres1", {id:"eusres1", parent:null, target:null, interno:semestre(TODAY), st:0, stDate:null, ops:[], type:"Epic"});
      alvo.type = 'User Story'; alvo.tags = ['ROADMAP']; alvo.epicoId = 'eusres1';
      alvo.deploy = new Date(f4pSemesterState().start.getTime() + 5 * 864e5);
      render();
      return alvo.id;
    }""")
    page.click("#f4pTab")
    page.click('button[data-f4p-us-team="CORE"][data-f4p-us-set="reservado"]')
    assert page.is_visible("#f4pItemsBg")
    rows = page.locator("#f4pItemsBody tbody tr")
    assert rows.count() == 1
    assert alvo_id in page.inner_text("#f4pItemsBody")
    page.click(f'button[data-f4p-go="{alvo_id}"]')
    assert not page.is_visible("#f4pItemsBg")
    assert not page.is_visible("#f4pPanel.open")
    assert page.evaluate("document.getElementById('fBusca').value") == alvo_id

def test_us_clique_no_planejado_outro_semestre_mostra_os_com_compromisso_divergente(page):
    """Decisão 0043: item com a tag mas cujo épico aponta compromisso pra outro semestre (ou sem
    compromisso registrado) cai em 'Planejado (outro semestre)', não em 'Reservado'."""
    carregar(page, "f4p.xlsx")
    page.evaluate("""()=>{
      S.f.team='CORE'; S.f.int=semestre(TODAY);
      [...S.model.ops.values()].filter(o=>o.team==='CORE').forEach(o => { o.deploy = null; });
      const dentro = new Date(f4pSemesterState().start.getTime() + 5 * 864e5);
      const ops = [...S.model.ops.values()].filter(o=>o.team==='CORE').slice(0, 2);
      S.model.epis.set("eusout1", {id:"eusout1", parent:null, target:null, interno:"2099 1", st:0, stDate:null, ops:[], type:"Epic"});
      ops[0].type = 'User Story'; ops[0].deploy = dentro; ops[0].tags = ['ROADMAP']; ops[0].epicoId = 'eusout1';   // outro semestre
      ops[1].type = 'User Story'; ops[1].deploy = dentro; ops[1].tags = ['ROADMAP'];   // sem epicoId: também conta como "outro semestre"
      render();
    }""")
    page.click("#f4pTab")
    page.click('button[data-f4p-us-team="CORE"][data-f4p-us-set="planejadooutro"]')
    assert page.is_visible("#f4pItemsBg")
    assert page.locator("#f4pItemsBody tbody tr").count() == 2

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
    assert "User Story (reservado vs planejado outro semestre vs não planejado)" in page.inner_text("#f4pBody")
    assert page.evaluate("f4pUsCell('CORE')").count("f4p-sep") == 2

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

# ---------------- Quadrante 8 · Eficiência de fluxo (min vs atual vs max) ----------------
# Decisão 0031. Eficiência do Fluxo = Touch Time ÷ (Touch Time + Waiting Time) × 100, pela classificação
# de cada coluna do fluxo do time (Configurações › Fluxo dos times, novo campo `time`: "touch"/"wait").
# Estilo "Queueing Stages" do Actionable Agile (ferramenta de Analytics citada pelo usuário como
# referência): o usuário marca só as colunas de Fila de espera (waiting time); as demais contam como touch
# time automaticamente — não existe um terceiro estado "sem classificação". Reaproveita f4pWindow (decisão
# 0013, mesma janela do CycleTime/Variabilidade — últimos N meses no semestre em curso, período exato no
# já encerrado), não f4pExactSemesterWindow como os demais quadrantes "por semestre".

def _dias_atras(page, n):
    return page.evaluate(f"() => new Date(TODAY.getTime() - {n} * 864e5)")

def _setup_item_eff(page, *, team, op_id, fd_offsets, deploy_offset=None, tipo="User Story", tags=None):
    """fd_offsets: dict coluna(normalizada) -> dias atrás de hoje. deploy_offset: dias atrás para o.deploy
    (None = item ainda aberto, sem Vazao)."""
    page.evaluate("""(args)=>{
      const {team, opId, fdOffsets, deployOffset, tipo, tags} = args;
      const fd = {}; Object.entries(fdOffsets).forEach(([k, v]) => { fd[k] = new Date(TODAY.getTime() - v * 864e5); });
      S.model.ops.set(opId, {id:opId, title:opId, team, type:tipo, stName:"Vazao",
        deploy: deployOffset != null ? new Date(TODAY.getTime() - deployOffset * 864e5) : null,
        ready: null, fd, tags: tags || []});
    }""", {"team": team, "opId": op_id, "fdOffsets": fd_offsets, "deployOffset": deploy_offset, "tipo": tipo, "tags": tags or []})

def _setup_flow_eff(page, team, stages, time_map, cat_map=None):
    page.evaluate("""(args)=>{
      const {team, stages, timeMap, catMap} = args;
      S.model.teamFlow[team] = stages;
      CFG.flow[norm(team)] = {cat: catMap || {}, ct:[], time: timeMap};
      S.flowCache = {};   // teamCfg/catOf/flowTimeOf têm cache por time; sem isso, um time já carregado
                          // (ex.: CORE) manteria a configuração antiga até a próxima recomputeHealth().
    }""", {"team": team, "stages": stages, "timeMap": time_map, "catMap": cat_map})

def test_eff_calcula_touch_dividido_por_touch_mais_wait(page):
    carregar(page, "f4p.xlsx")
    _setup_flow_eff(page, "F4P_EFF1", ["Backlog", "Analise", "Dev", "Espera", "QA", "Vazao"],
                     {"analise": "touch", "dev": "touch", "espera": "wait", "qa": "touch"}, {"vazao": "vazao"})
    _setup_item_eff(page, team="F4P_EFF1", op_id="op1", deploy_offset=1, fd_offsets={
        "backlog": 20, "analise": 19, "dev": 17, "espera": 9, "qa": 4, "vazao": 1})
    r = page.evaluate("""()=>{
      S.f.team = "F4P_EFF1"; S.f.exec = semestre(TODAY);
      return f4pEffPct("F4P_EFF1", f4pWindow(f4pSemesterState()).from, f4pWindow(f4pSemesterState()).to);
    }""")
    # touch: Backlog->Analise (1, sem marcação = touch) + Analise->Dev (2) + Dev->Espera (8) + QA->Vazao (3) = 14
    # wait: Espera->QA (5). O trecho Vazao->hoje não conta: o item já foi entregue (categoria Vazão), o
    # relógio da eficiência para na entrega. 14/(14+5) = 73,68%
    assert abs(r - (14 / 19 * 100)) < 1e-6

def test_eff_colunas_sem_fila_de_espera_marcada_contam_como_touch(page):
    """Estilo Actionable Agile (ferramenta de Analytics citada pelo usuário como referência): só se marca a
    Fila de espera; as demais colunas contam como touch time automaticamente — não existe mais um estado
    "sem classificação" separado."""
    carregar(page, "f4p.xlsx")
    _setup_flow_eff(page, "F4P_EFF2", ["Backlog", "Dev", "Vazao"], {"dev": "touch"}, {"vazao": "vazao"})
    _setup_item_eff(page, team="F4P_EFF2", op_id="op1", deploy_offset=1, fd_offsets={"backlog": 10, "dev": 8, "vazao": 1})
    r = page.evaluate("""()=>{
      const st = f4pSemesterState(); S.f.team="F4P_EFF2"; S.f.exec=semestre(TODAY);
      const {from, to} = f4pWindow(f4pSemesterState());
      return f4pItemDurations([...S.model.ops.values()].find(o=>o.id==='op1'), from, to);
    }""")
    # Backlog não está marcado como Fila de espera: conta como touch (2 dias). Dev->Vazao (7 dias) também é touch.
    assert r == {"touch": 9, "wait": 0}

def test_eff_pega_todos_os_itens_nao_so_concluidos(page):
    """'Deve-se pegar todos os itens do fluxo de cada time' — um item ainda aberto (sem Vazao) também
    contribui com o touch/wait já acumulado até agora."""
    carregar(page, "f4p.xlsx")
    _setup_flow_eff(page, "F4P_EFF3", ["Backlog", "Dev", "Vazao"], {"dev": "touch"}, {"vazao": "vazao"})
    page.evaluate("""()=>{
      S.model.ops.set("aberto", {id:"aberto", title:"Aberto", team:"F4P_EFF3", type:"User Story", stName:"Dev",
        deploy:null, ready:null, fd:{backlog:new Date(TODAY.getTime()-10*864e5), dev:new Date(TODAY.getTime()-5*864e5)}, tags:[]});
    }""")
    r = page.evaluate("""()=>{
      S.f.team="F4P_EFF3"; S.f.exec=semestre(TODAY);
      const {from, to} = f4pWindow(f4pSemesterState());
      return f4pEffPct("F4P_EFF3", from, to);
    }""")
    assert r == 100.0   # só touch (Dev até hoje), sem nenhum wait

def test_eff_usa_tipos_configuraveis_com_todos_por_padrao(page):
    carregar(page, "f4p.xlsx")
    _setup_flow_eff(page, "F4P_EFF4", ["Backlog", "Dev", "Vazao"], {"dev": "touch"}, {"vazao": "vazao"})
    _setup_item_eff(page, team="F4P_EFF4", op_id="us1", tipo="User Story", deploy_offset=1, fd_offsets={"backlog": 10, "dev": 5, "vazao": 1})
    _setup_item_eff(page, team="F4P_EFF4", op_id="bug1", tipo="Internal Bug", deploy_offset=1, fd_offsets={"backlog": 10, "dev": 5, "vazao": 1})
    r = page.evaluate("""()=>{
      S.f.team="F4P_EFF4"; S.f.exec=semestre(TODAY);
      const {from, to} = f4pWindow(f4pSemesterState());
      const comTodos = f4pEffOps("F4P_EFF4").length;
      CFG.f4p.effTypes = ["user story"];
      const soUserStory = f4pEffOps("F4P_EFF4").length;
      CFG.f4p.effTypes = [];
      return {comTodos, soUserStory};
    }""")
    assert r == {"comTodos": 2, "soUserStory": 1}

def test_eff_recorta_duracao_pela_janela_do_semestre(page):
    """Item cujo intervalo de coluna começa antes da janela e termina depois dela: só a parte dentro da
    janela [from, to] entra na soma (recorte, não exclusão do item inteiro)."""
    carregar(page, "f4p.xlsx")
    _setup_flow_eff(page, "F4P_EFF5", ["Backlog", "Dev", "Vazao"], {"dev": "touch"}, {"vazao": "vazao"})
    r = page.evaluate("""()=>{
      const from = new Date(TODAY.getFullYear(), TODAY.getMonth() - 1, 1), to = new Date(TODAY.getFullYear(), TODAY.getMonth(), 1);
      const antesDaJanela = new Date(from.getTime() - 10 * 864e5), dentroDoFim = new Date(to.getTime() - 2 * 864e5);
      const o = {id:"op1", team:"F4P_EFF5", type:"User Story", fd:{dev:antesDaJanela, vazao:dentroDoFim}};
      return f4pItemDurations(o, from, to);
    }""")
    # intervalo real Dev->Vazao é maior, mas só a parte dentro de [from, to] conta
    assert r["touch"] == page.evaluate("""()=>{
      const from = new Date(TODAY.getFullYear(), TODAY.getMonth() - 1, 1), to = new Date(TODAY.getFullYear(), TODAY.getMonth(), 1);
      return days(from, new Date(to.getTime() - 2 * 864e5));
    }""")

def test_eff_janela_reaproveita_f4pwindow_nao_a_exata_do_semestre(page):
    """Diferente de Urgente/Technical Story/Vazão/Roadmap-Épicos/User Story (f4pExactSemesterWindow),
    Eficiência de fluxo usa f4pWindow — a mesma janela rolante do CycleTime/Variabilidade."""
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      S.f.exec = semestre(TODAY);
      const stAtual = f4pSemesterState();
      const janelaEff = f4pWindow(stAtual), janelaCt = f4pWindow(stAtual), janelaExata = f4pExactSemesterWindow(stAtual);
      return {iguaisCt: +janelaEff.from === +janelaCt.from, diferenteDaExata: +janelaEff.from !== +janelaExata.from};
    }""")
    assert r == {"iguaisCt": True, "diferenteDaExata": True}

def test_eff_sem_item_no_periodo_mostra_travessao(page):
    """Sem nenhum item do time no período (aqui, um time sem carga nenhuma), a eficiência fica "--" — não
    existe mais o caso de "nenhuma coluna classificada", já que colunas sem marcação contam como touch."""
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      S.f.team="TIME_SEM_ITEM_EFF"; S.f.exec=semestre(TODAY);
      const {from, to} = f4pWindow(f4pSemesterState());
      return f4pEffPct("TIME_SEM_ITEM_EFF", from, to);
    }""")
    assert r is None

def test_eff_cor_verde_dentro_da_faixa_e_vermelha_fora(page):
    carregar(page, "f4p.xlsx")
    _setup_flow_eff(page, "F4P_EFF6", ["Backlog", "Dev", "Espera", "Vazao"], {"dev": "touch", "espera": "wait"}, {"vazao": "vazao"})
    # ~50% (dentro de 30-55): Backlog (sem marcação = touch) + Dev = 100 dias touch, Espera = 99 dias wait
    _setup_item_eff(page, team="F4P_EFF6", op_id="dentro", deploy_offset=1, fd_offsets={"backlog": 200, "dev": 155, "espera": 100, "vazao": 1})
    r = page.evaluate("""()=>{
      S.f.team="F4P_EFF6"; S.f.exec=semestre(TODAY);
      return f4pEffCell("F4P_EFF6");
    }""")
    assert "f4p-good" in r and "f4p-bad" not in r
    # zera e recria com uma proporção fora da faixa (10% touch)
    page.evaluate("()=>{ S.model.ops.delete('dentro'); }")
    _setup_item_eff(page, team="F4P_EFF6", op_id="fora", deploy_offset=1, fd_offsets={"backlog": 110, "dev": 101, "espera": 91, "vazao": 1})
    r2 = page.evaluate("()=>f4pEffCell('F4P_EFF6')")
    assert "f4p-bad" in r2 and "f4p-good" not in r2

def test_eff_min_max_ficam_em_linha_propria(page):
    """Decisão 0038: min/max ficam numa <span class="f4p-eff-mm"> separada, numa linha abaixo do
    valor principal — antes vinham lado a lado (min|atual|max) na mesma linha, o que quebrava o
    layout com vários times (a célula é bem mais larga aqui do que em Variabilidade, por causa do
    "%" e por não ter casa decimal fixa)."""
    carregar(page, "f4p.xlsx")
    _setup_flow_eff(page, "F4P_EFF_MM", ["Backlog", "Dev", "Espera", "Vazao"], {"dev": "touch", "espera": "wait"}, {"vazao": "vazao"})
    _setup_item_eff(page, team="F4P_EFF_MM", op_id="mm1", deploy_offset=1, fd_offsets={"backlog": 200, "dev": 155, "espera": 100, "vazao": 1})
    r = page.evaluate("""()=>{
      S.f.team="F4P_EFF_MM"; S.f.exec=semestre(TODAY);
      return f4pEffCell("F4P_EFF_MM");
    }""")
    assert 'class="f4p-eff-mm"' in r
    assert r.index("data-f4p-eff-team") < r.index('class="f4p-eff-mm"')   # valor principal vem antes da linha de min/max
    assert r.index('class="f4p-eff-mm"') < r.index("f4p-lo")              # min/max ficam dentro dessa linha, não soltos

def test_eff_usa_faixa_min_max_configuravel_por_time(page):
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      CFG.f4p.teams.f4p_eff7 = {effMin: 10, effMax: 20};
      const R = f4pEffRangeOf("F4P_EFF7");
      delete CFG.f4p.teams.f4p_eff7;
      return R;
    }""")
    assert r == {"min": 10, "max": 20}

def test_eff_tendencia_ultimos_2_meses_melhor_fica_positiva(page):
    carregar(page, "f4p.xlsx")
    _setup_flow_eff(page, "F4P_EFFT1", ["Backlog", "Dev", "Espera", "Vazao"], {"dev": "touch", "espera": "wait"}, {"vazao": "vazao"})
    # item antigo (fora dos ultimos 2 meses, mas dentro do periodo de 6 meses): baixa eficiencia (muito wait)
    _setup_item_eff(page, team="F4P_EFFT1", op_id="antigo", deploy_offset=100, fd_offsets={"backlog": 130, "dev": 125, "espera": 105, "vazao": 100})
    # item recente (dentro dos ultimos 2 meses): alta eficiencia (quase só touch)
    _setup_item_eff(page, team="F4P_EFFT1", op_id="recente", deploy_offset=1, fd_offsets={"backlog": 20, "dev": 19, "espera": 2, "vazao": 1})
    r = page.evaluate("""()=>{
      S.f.team="F4P_EFFT1"; S.f.exec=semestre(TODAY);
      const {from, to} = f4pWindow(f4pSemesterState());
      return f4pEffTrend("F4P_EFFT1", from, to);
    }""")
    assert r == "▲"

def test_eff_tendencia_ultimos_2_meses_pior_fica_negativa(page):
    carregar(page, "f4p.xlsx")
    _setup_flow_eff(page, "F4P_EFFT2", ["Backlog", "Dev", "Espera", "Vazao"], {"dev": "touch", "espera": "wait"}, {"vazao": "vazao"})
    # item antigo (fora dos últimos 2 meses): alta eficiência (touch 19, wait 6) — só entra na média do
    # período inteiro, não nos últimos 2 meses.
    _setup_item_eff(page, team="F4P_EFFT2", op_id="antigo", deploy_offset=100, fd_offsets={"backlog": 130, "dev": 125, "espera": 106, "vazao": 100})
    # item recente (dentro dos últimos 2 meses): baixa eficiência (touch 2, wait 16) — sozinho, arrasta a
    # eficiência dos últimos 2 meses (11%) bem abaixo da eficiência do período inteiro (49%, com o antigo).
    _setup_item_eff(page, team="F4P_EFFT2", op_id="recente", deploy_offset=1, fd_offsets={"backlog": 20, "dev": 19, "espera": 17, "vazao": 1})
    r = page.evaluate("""()=>{
      S.f.team="F4P_EFFT2"; S.f.exec=semestre(TODAY);
      const {from, to} = f4pWindow(f4pSemesterState());
      return f4pEffTrend("F4P_EFFT2", from, to);
    }""")
    assert r == "▼"

def test_eff_tendencia_sem_diferenca_fica_neutra(page):
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      const st = {kind:"current", start:new Date(TODAY.getFullYear(), TODAY.getMonth(), 1), end:new Date(TODAY.getFullYear(), TODAY.getMonth() + 6, 0)};
      const {from, to} = f4pWindow(st);
      return f4pEffTrend("F4P_EFFT_VAZIO", from, to);
    }""")
    assert r == "◆"

def test_eff_clique_no_numero_abre_lista_e_permite_navegar(page):
    carregar(page, "f4p.xlsx")
    _setup_flow_eff(page, "CORE", ["Backlog", "Ready / pronto para dev", "Pronto para Deploy", "Fechado"],
                     {"ready / pronto para dev": "touch", "pronto para deploy": "wait"}, {"fechado": "vazao"})
    _setup_item_eff(page, team="CORE", op_id="eff_click", deploy_offset=1, fd_offsets={
        "backlog": 20, "ready / pronto para dev": 15, "pronto para deploy": 5, "fechado": 1})
    page.evaluate("""()=>{ S.f.team='CORE'; S.f.exec=semestre(TODAY); render(); }""")
    page.click("#f4pTab")
    page.click('button[data-f4p-eff-team="CORE"]')
    assert page.is_visible("#f4pItemsBg")
    assert "eff_click" in page.inner_text("#f4pItemsBody")
    assert "Touch" in page.inner_text("#f4pItemsBody") and "Wait" in page.inner_text("#f4pItemsBody")
    page.click('button[data-f4p-go="eff_click"]')
    assert not page.is_visible("#f4pItemsBg")
    assert not page.is_visible("#f4pPanel.open")
    assert page.evaluate("document.getElementById('fBusca').value") == "eff_click"

def test_eff_aparece_calculado_no_painel(page):
    carregar(page, "f4p.xlsx")
    page.evaluate("()=>{ S.f.team='CORE'; S.f.exec=semestre(TODAY); render(); }")
    page.click("#f4pTab")
    assert "Eficiência de fluxo (min vs atual vs max)" in page.inner_text("#f4pBody")
    assert "Regra de cálculo ainda em definição." not in page.inner_text("#f4pBody")

def test_configuracao_eff_types_tem_padrao_vazio_todos_os_tipos(page):
    r = page.evaluate("()=>{ const c = normCfg({}); return c.f4p.effTypes; }")
    assert r == []

def test_configuracao_eff_min_max_tem_padrao_30_55(page):
    r = page.evaluate("()=>f4pEffRangeOf('TIME_SEM_CONFIG')")
    assert r == {"min": 30, "max": 55}

def test_configuracao_eff_persiste_e_entra_na_exportacao(page):
    carregar(page, "times.xlsx")
    page.evaluate("()=>{ CFG.f4p.effTypes = ['user story']; CFG.f4p.teams.core = {effMin: 20, effMax: 60}; }")
    page.click("#btnCfg")
    with page.expect_download() as d:
        page.click("#cfgExport")
    txt = open(d.value.path(), encoding="utf-8").read()
    assert '"effTypes"' in txt and '"effMin": 20' in txt and '"effMax": 60' in txt

def test_configuracao_touch_wait_por_coluna_persiste(page):
    """A UI de Configurações › Fluxo dos times grava a marcação de Fila de espera por coluna em
    CFG.flow[time].time ("wait"/"touch"), separada da categoria (Discovery/WIP/Vazão). Estilo Actionable
    Agile: só se marca a Fila de espera; as demais colunas ficam "touch" automaticamente."""
    carregar(page, "f4p.xlsx")
    page.click("#btnCfg")
    page.evaluate("""()=>{ document.querySelector('input[data-timewait="pronto para deploy"]').click(); }""")
    page.click("#cfgSave")
    r = page.evaluate("()=>CFG.flow.core.time")
    assert r["pronto para deploy"] == "wait"
    assert r["ready / pronto para dev"] == "touch"
    assert r["backlog"] == "touch"

def test_flow_time_of_le_classificacao_por_coluna(page):
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      CFG.flow.core = {cat:{}, ct:[], time:{"pronto para deploy":"wait"}};
      S.flowCache = {};   // CORE já foi lido antes (carga inicial); sem isso o cache do teamCfg fica velho
      const r = {deploy: flowTimeOf("CORE", "Pronto para Deploy"), ready: flowTimeOf("CORE", "Ready / Pronto para DEV"), backlog: flowTimeOf("CORE", "Backlog")};
      delete CFG.flow.core;
      S.flowCache = {};
      return r;
    }""")
    assert r == {"deploy": "wait", "ready": "touch", "backlog": "touch"}
