"""Actionable: métricas acionáveis por time no período do roadmap (docs/regras-de-negocio.md §13).
Primeira versão (MVP): só os quadrantes CycleTime e Burnup Reserva têm regra definida — decisão 0041."""
from conftest import carregar

def _habilitar(page, team="CORE", exec_=True):
    sem = "()=>semestre(TODAY)"
    if exec_:
        page.evaluate(f"()=>{{ S.f.team={team!r}; S.f.exec=semestre(TODAY); render(); }}")
    else:
        page.evaluate(f"()=>{{ S.f.team={team!r}; S.f.int=semestre(TODAY); render(); }}")

def test_aba_desabilitada_sem_time_e_roadmap(page):
    carregar(page, "f4p.xlsx")
    assert page.is_disabled("#actTab")
    page.evaluate("()=>{ S.f.team='CORE'; render(); }")
    assert page.is_disabled("#actTab")   # só o time não basta
    page.evaluate("()=>{ S.f.exec=semestre(TODAY); render(); }")
    assert not page.is_disabled("#actTab")
    page.click("#actTab")
    assert page.evaluate("ACT.open") is True

def test_semestre_futuro_desabilita_e_fecha_o_painel(page):
    carregar(page, "f4p.xlsx")
    _habilitar(page)
    page.click("#actTab")
    assert page.evaluate("ACT.open") is True
    page.evaluate("""()=>{
      const curStart = f4pSemStart(semestre(TODAY));
      const future = new Date(curStart.getFullYear(), curStart.getMonth() + 12, 1);
      S.f.exec = semestre(future); render();
    }""")
    assert page.is_disabled("#actTab")
    assert page.evaluate("actEnabled()") is False
    assert page.evaluate("ACT.open") is False

def test_scatter_ct_usa_mesma_amostra_e_reserva_do_report_f4p(page):
    """A dispersão de CycleTime reaproveita f4pSample/limitsOf — mesma amostra e Reserva do quadrante
    CycleTime do Report F4P (§12.2), não um cálculo próprio."""
    carregar(page, "f4p.xlsx")
    _habilitar(page)
    r = page.evaluate("""()=>{
      const d = actCtScatterData('CORE');
      const L = limitsOf('CORE');
      const sample = f4pSample('CORE');
      return {nPontos: d.items.length, nAmostra: sample.length, reserva: d.reserva, max: L.max,
              idsIguais: JSON.stringify(d.items.map(o=>o.id).sort()) === JSON.stringify(sample.map(o=>o.id).sort())};
    }""")
    assert r["nPontos"] == r["nAmostra"] and r["nPontos"] > 0
    assert r["reserva"] == r["max"]
    assert r["idsIguais"] is True

def test_scatter_atual_e_o_p95_da_amostra(page):
    carregar(page, "f4p.xlsx")
    _habilitar(page)
    r = page.evaluate("""()=>{
      const d = actCtScatterData('CORE');
      const m = f4pMetrics('CORE');
      return {atual: d.atual, p95: m.p95};
    }""")
    assert abs(r["atual"] - r["p95"]) < 1e-9

def test_scatter_pontos_acima_da_reserva_ficam_destacados(page):
    carregar(page, "f4p.xlsx")
    _habilitar(page)
    page.evaluate("()=>{ CFG.teams={core:{max:20}}; recomputeHealth(); }")
    page.click("#actTab")
    page.wait_for_timeout(200)
    r = page.evaluate("""()=>{
      const d = actCtScatterData('CORE');
      return {temAcima: d.items.some(o=>o.ct > d.reserva), temBadNaTela: document.querySelector('.act-dot-bad') !== null};
    }""")
    assert r["temAcima"] and r["temBadNaTela"]

def test_scatter_sem_itens_no_periodo_mostra_mensagem(page):
    carregar(page, "f4p.xlsx")
    page.evaluate("""()=>{
      S.model.teams.push('ACT_VAZIO');
      S.f.team = 'ACT_VAZIO'; S.f.exec = semestre(TODAY);
      render();
    }""")
    page.click("#actTab")
    assert "Nenhum item concluído no período" in page.inner_text("#actBody")

def test_clique_no_ponto_do_scatter_fecha_o_painel_e_navega(page):
    carregar(page, "f4p.xlsx")
    _habilitar(page)
    page.click("#actTab")
    page.wait_for_timeout(200)
    alvo = page.evaluate("document.querySelector('.act-dot').dataset.actGo")
    page.click(".act-dot >> nth=0")
    assert page.evaluate("ACT.open") is False
    assert page.evaluate("document.getElementById('fBusca').value") == alvo

def test_burnup_reservado_e_o_mesmo_da_capacidade_da_visao_analitica(page):
    """"Reservado" no burnup é o mesmo conjunto de itens da Capacidade da Visão analítica (§10) — itens
    com a tag de capacidade do roadmap, em qualquer status, não só os já entregues."""
    carregar(page, "f4p.xlsx")
    sem = page.evaluate("semestre(TODAY)")
    page.evaluate("""(sem)=>{
      S.model.teamFlow.ACT_RES = ["Backlog", "WIP", "Vazao"];
      CFG.flow.act_res = {cat:{wip:"wip", vazao:"vazao"}, ct:[]};
      S.model.ops.set("r1", {id:"r1", title:"R1", team:"ACT_RES", type:"User Story", stName:"Backlog", deploy:null, ready:null, tags:["ROADMAP"]});
      S.model.ops.set("r2", {id:"r2", title:"R2", team:"ACT_RES", type:"User Story", stName:"WIP", deploy:null, ready:null, tags:["ROADMAP"]});
      S.model.ops.set("r3", {id:"r3", title:"R3", team:"ACT_RES", type:"User Story", stName:"Backlog", deploy:null, ready:null, tags:[]});
      S.model.inis.set("INI_R", {id:"INI_R", valid:true, title:"Ini", exec:sem, owner:null, rels:["REL_R"]});
      S.model.rels.set("REL_R", {id:"REL_R", valid:true, title:"Rel", parent:"INI_R", epis:["EPI_R"]});
      S.model.epis.set("EPI_R", {id:"EPI_R", valid:true, title:"Epi", parent:"REL_R", target:null, interno:null, st:0, ops:["r1","r2","r3"], type:"Epic"});
      S.model.teams.push("ACT_RES");
      S.f.team = "ACT_RES"; S.f.exec = sem;
      render();
    }""", sem)
    r = page.evaluate("""()=>{
      const bu = actBurnupData();
      const an = anData();
      return {escopo: bu.escopo, cap: an.cap};
    }""")
    assert r["escopo"] == r["cap"] == 2   # r1 e r2 (com a tag), não r3

def test_burnup_entregue_acumulado_por_mes(page):
    """Entregue acumula mês a mês dentro do semestre: um item entregue em julho conta a partir de
    julho (inclusive); um ainda não entregue nunca entra na conta, mas segue contando no escopo."""
    carregar(page, "f4p.xlsx")
    sem = page.evaluate("semestre(TODAY)")
    page.evaluate("""(sem)=>{
      S.model.teamFlow.ACT_BU = ["Backlog", "Vazao"];
      CFG.flow.act_bu = {cat:{vazao:"vazao"}, ct:[]};
      const curStart = f4pSemStart(sem);
      const m0 = new Date(curStart.getFullYear(), curStart.getMonth(), 15);
      const m1 = new Date(curStart.getFullYear(), curStart.getMonth()+1, 15);
      S.model.ops.set("b1", {id:"b1", title:"B1", team:"ACT_BU", type:"User Story", stName:"Vazao", deploy:m0, ready:m0, tags:["ROADMAP"]});
      S.model.ops.set("b2", {id:"b2", title:"B2", team:"ACT_BU", type:"User Story", stName:"Vazao", deploy:m1, ready:m1, tags:["ROADMAP"]});
      S.model.ops.set("b3", {id:"b3", title:"B3", team:"ACT_BU", type:"User Story", stName:"Backlog", deploy:null, ready:null, tags:["ROADMAP"]});
      S.model.inis.set("INI_BU", {id:"INI_BU", valid:true, title:"Ini", exec:sem, owner:null, rels:["REL_BU"]});
      S.model.rels.set("REL_BU", {id:"REL_BU", valid:true, title:"Rel", parent:"INI_BU", epis:["EPI_BU"]});
      S.model.epis.set("EPI_BU", {id:"EPI_BU", valid:true, title:"Epi", parent:"REL_BU", target:null, interno:null, st:0, ops:["b1","b2","b3"], type:"Epic"});
      S.model.teams.push("ACT_BU");
      S.f.team = "ACT_BU"; S.f.exec = sem;
      render();
    }""", sem)
    r = page.evaluate("""()=>{
      const bu = actBurnupData();
      return {escopo: bu.escopo, cumulative: bu.cumulative, entreguesN: bu.entreguesN, faltam: bu.faltam};
    }""")
    assert r["escopo"] == 3
    assert r["cumulative"][0] == 1          # só b1 entregue no primeiro mês
    assert r["cumulative"][1] == 2          # b1 + b2 a partir do segundo mês
    assert r["entreguesN"] == 2
    assert r["faltam"] == 1                 # b3 nunca entra (ainda em Backlog)

def test_burnup_entregue_no_ultimo_dia_do_mes_conta_nesse_mes(page):
    """Um item entregue exatamente no último dia do mês precisa contar dentro desse mês (não só a
    partir do mês seguinte) — fim de mês é limite inclusivo."""
    carregar(page, "f4p.xlsx")
    sem = page.evaluate("semestre(TODAY)")
    page.evaluate("""(sem)=>{
      S.model.teamFlow.ACT_EDGE = ["Backlog", "Vazao"];
      CFG.flow.act_edge = {cat:{vazao:"vazao"}, ct:[]};
      const curStart = f4pSemStart(sem);
      const ultimoDia = new Date(curStart.getFullYear(), curStart.getMonth() + 1, 0);   // último dia do 1º mês
      S.model.ops.set("e1", {id:"e1", title:"E1", team:"ACT_EDGE", type:"User Story", stName:"Vazao", deploy:ultimoDia, ready:ultimoDia, tags:["ROADMAP"]});
      S.model.inis.set("INI_E", {id:"INI_E", valid:true, title:"Ini", exec:sem, owner:null, rels:["REL_E"]});
      S.model.rels.set("REL_E", {id:"REL_E", valid:true, title:"Rel", parent:"INI_E", epis:["EPI_E"]});
      S.model.epis.set("EPI_E", {id:"EPI_E", valid:true, title:"Epi", parent:"REL_E", target:null, interno:null, st:0, ops:["e1"], type:"Epic"});
      S.model.teams.push("ACT_EDGE");
      S.f.team = "ACT_EDGE"; S.f.exec = sem;
      render();
    }""", sem)
    r = page.evaluate("actBurnupData().cumulative")
    assert r[0] == 1

def test_burnup_resumo_mostra_reservado_entregue_e_faltam(page):
    carregar(page, "f4p.xlsx")
    _habilitar(page)
    page.click("#actTab")
    page.wait_for_timeout(200)
    txt = page.inner_text(".act-summary")
    assert "reservado" in txt and "entregue" in txt and "falta" in txt

def test_burnup_clique_em_reservado_abre_lista_dos_itens_reservados(page):
    carregar(page, "f4p.xlsx")
    sem = page.evaluate("semestre(TODAY)")
    page.evaluate("""(sem)=>{
      S.model.teamFlow.ACT_CLK = ["Backlog", "Vazao"];
      CFG.flow.act_clk = {cat:{vazao:"vazao"}, ct:[]};
      S.model.ops.set("c1", {id:"c1", title:"C1", team:"ACT_CLK", type:"User Story", stName:"Backlog", deploy:null, ready:null, tags:["ROADMAP"]});
      S.model.inis.set("INI_C", {id:"INI_C", valid:true, title:"Ini", exec:sem, owner:null, rels:["REL_C"]});
      S.model.rels.set("REL_C", {id:"REL_C", valid:true, title:"Rel", parent:"INI_C", epis:["EPI_C"]});
      S.model.epis.set("EPI_C", {id:"EPI_C", valid:true, title:"Epi", parent:"REL_C", target:null, interno:null, st:0, ops:["c1"], type:"Epic"});
      S.model.teams.push("ACT_CLK");
      S.f.team = "ACT_CLK"; S.f.exec = sem;
      render();
    }""", sem)
    page.click("#actTab")
    page.wait_for_timeout(200)
    page.click('[data-act-items="reserva"]')
    assert page.is_visible("#f4pItemsBg")
    assert "c1" in page.inner_text("#f4pItemsBody")

def test_quadrantes_3_e_4_mostram_em_definicao(page):
    carregar(page, "f4p.xlsx")
    _habilitar(page)
    page.click("#actTab")
    page.wait_for_timeout(200)
    titulos = page.evaluate("[...document.querySelectorAll('#actBody .f4p-card-h')].map(x=>x.textContent)")
    assert titulos == ["CycleTime", "Em definição", "Burnup Reserva", "Em definição"]
    assert page.locator("#actBody .an-empty", has_text="Regra de cálculo ainda em definição.").count() == 2

def test_abrir_visao_analitica_ou_f4p_fecha_o_actionable(page):
    """Os três painéis laterais (Visão analítica, Report F4P, Actionable) são mutuamente exclusivos —
    mesma convenção já usada entre Visão analítica e Report F4P."""
    carregar(page, "f4p.xlsx")
    _habilitar(page)
    page.click("#actTab")
    assert page.evaluate("ACT.open") is True
    page.evaluate("openAnalytics()")
    assert page.evaluate("ACT.open") is False and page.evaluate("AN.open") is True
    page.evaluate("closeAnalytics(); openActionable();")
    assert page.evaluate("ACT.open") is True
    page.evaluate("openF4P()")
    assert page.evaluate("ACT.open") is False and page.evaluate("F4P.open") is True

def test_abrir_actionable_fecha_visao_analitica_e_f4p(page):
    carregar(page, "f4p.xlsx")
    _habilitar(page)
    page.click("#anTab")
    assert page.evaluate("AN.open") is True
    page.evaluate("openActionable()")
    assert page.evaluate("AN.open") is False and page.evaluate("ACT.open") is True
