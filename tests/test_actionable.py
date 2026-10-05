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

def test_ignora_filtro_de_id_ou_descricao_so_roadmap_time_e_responsavel_afetam(page):
    """Decisão 0054: Actionable (assim como Visão analítica e Report F4P) só deve ser afetado pelos
    filtros de roadmap (interno ou executivo), time e responsável — o campo "ID ou descrição" (S.f.q)
    não deve mudar os números deste painel."""
    carregar(page, "f4p.xlsx")
    _habilitar(page)
    sem_q = page.evaluate("actCtScatterData('CORE').items.length")
    page.evaluate("()=>{ S.f.q='999999'; render(); }")
    com_q = page.evaluate("actCtScatterData('CORE').items.length")
    assert sem_q == com_q and sem_q > 0

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

def test_scatter_item_tardio_de_epico_comprometido_aparece_como_ponto_extra(page):
    """Decisão 0062 (mesmo espírito das 0060/0061): depois da correção do Burnup Reserva e do CFD, o
    usuário mandou outro print mostrando que só o CycleTime continuava "preso" em junho, sem refletir
    uma entrega de julho do mesmo roadmap. A amostra de CycleTime (`f4pSample`, igual ao Report F4P
    §12.2) é definida por uma janela fixa — mudar essa janela mudaria a Reserva/Atual comparados no
    Report F4P também, então a correção não toca nela: um item concluído de um épico comprometido com o
    roadmap, entregue depois do fim da janela, aparece como ponto EXTRA no gráfico (eixo estendido, linha
    "fim do semestre"), mas Reserva e Atual (P95) continuam calculados só sobre a amostra original."""
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      const curStart = f4pSemStart(semestre(TODAY));
      const prevMid = new Date(curStart.getFullYear(), curStart.getMonth() - 3, 15);
      const prevSem = semestre(prevMid);
      const prevStart = f4pSemStart(prevSem);
      const dentro = new Date(prevStart.getFullYear(), prevStart.getMonth() + 1, 15);
      const tardia = new Date(prevStart.getFullYear(), prevStart.getMonth() + 6, 10);   // depois do fim da janela
      S.model.ops.set("p1", {id:"p1", title:"P1", team:"ACT_CT_TARDIO", type:"User Story", deploy:dentro, ct:30, tags:["ROADMAP"]});
      S.model.ops.set("p2", {id:"p2", title:"P2", team:"ACT_CT_TARDIO", type:"User Story", deploy:tardia, ct:45, tags:[]});
      S.model.inis.set("INI_P", {id:"INI_P", valid:true, title:"Ini", exec:prevSem, owner:null, rels:["REL_P"]});
      S.model.rels.set("REL_P", {id:"REL_P", valid:true, title:"Rel", parent:"INI_P", epis:["EPI_P"]});
      S.model.epis.set("EPI_P", {id:"EPI_P", valid:true, title:"Epi", parent:"REL_P", target:null, interno:null, st:0, ops:["p1", "p2"], type:"Epic"});
      S.model.teams.push("ACT_CT_TARDIO");
      S.f.team = "ACT_CT_TARDIO"; S.f.exec = prevSem;
      render();
      const d = actCtScatterData("ACT_CT_TARDIO");
      return {nAmostra: d.items.length, amostraIds: d.items.map(o=>o.id), atual: d.atual,
        tardiosIds: d.tardios.map(o=>o.id), extended: d.extended,
        svgTemP2: actScatterSvg(d).includes("P2 · CT 45d"),
        svgTemLinha: actScatterSvg(d).includes("act-sem-end")};
    }""")
    assert r["nAmostra"] == 1 and r["amostraIds"] == ["p1"]   # p2 nunca entra na amostra (fora da janela)
    assert r["atual"] == 30   # P95 de 1 item só — não conta p2
    assert r["tardiosIds"] == ["p2"]
    assert r["extended"] is True
    assert r["svgTemP2"] is True   # p2 aparece como ponto extra no gráfico
    assert r["svgTemLinha"] is True

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

def test_burnup_clique_em_faltam_abre_lista_dos_itens_ainda_nao_entregues(page):
    """Melhoria pedida pelo usuário depois de usar a 1ª versão: "faltam" também precisa ser clicável,
    igual a "reservado" e "entregue" — mostrando exatamente quais itens da Reserva ainda não chegaram
    em Vazão."""
    carregar(page, "f4p.xlsx")
    sem = page.evaluate("semestre(TODAY)")
    page.evaluate("""(sem)=>{
      S.model.teamFlow.ACT_FALTAM = ["Backlog", "WIP", "Vazao"];
      CFG.flow.act_faltam = {cat:{wip:"wip", vazao:"vazao"}, ct:[]};
      S.model.ops.set("g1", {id:"g1", title:"G1", team:"ACT_FALTAM", type:"User Story", stName:"Vazao", deploy:new Date(), ready:new Date(), tags:["ROADMAP"]});
      S.model.ops.set("g2", {id:"g2", title:"G2", team:"ACT_FALTAM", type:"User Story", stName:"Backlog", deploy:null, ready:null, tags:["ROADMAP"]});
      S.model.ops.set("g3", {id:"g3", title:"G3", team:"ACT_FALTAM", type:"User Story", stName:"WIP", deploy:null, ready:null, tags:["ROADMAP"]});
      S.model.inis.set("INI_G", {id:"INI_G", valid:true, title:"Ini", exec:sem, owner:null, rels:["REL_G"]});
      S.model.rels.set("REL_G", {id:"REL_G", valid:true, title:"Rel", parent:"INI_G", epis:["EPI_G"]});
      S.model.epis.set("EPI_G", {id:"EPI_G", valid:true, title:"Epi", parent:"REL_G", target:null, interno:null, st:0, ops:["g1","g2","g3"], type:"Epic"});
      S.model.teams.push("ACT_FALTAM");
      S.f.team = "ACT_FALTAM"; S.f.exec = sem;
      render();
    }""", sem)
    page.click("#actTab")
    page.wait_for_timeout(200)
    txt = page.inner_text(".act-summary")
    assert "3" in txt and "1" in txt and "2" in txt   # 3 reservados, 1 entregue, 2 faltam
    page.click('[data-act-items="faltam"]')
    assert page.is_visible("#f4pItemsBg")
    body = page.inner_text("#f4pItemsBody")
    assert "g2" in body and "g3" in body and "g1" not in body

def test_burnup_entrega_fora_do_periodo_do_semestre_ainda_conta_como_entregue(page):
    """Decisão 0058 (correção; revê a regra anterior, decisão 0041): um item da Reserva entregue depois
    que o semestre selecionado (já encerrado) fechou continua contando como "entregue" no resumo. Mesma
    razão da decisão 0052 (Report F4P, Reserva entregue): o usuário reportou o resumo "faltam" mostrando
    um item cuja Situação já lia "Vazão · DD/MM/AAAA" — "faltam" tem que significar só o que de fato
    ainda não foi entregue, nunca uma entrega tardia. Desde a decisão 0059, essa entrega tardia também
    é refletida no gráfico (encaixada no último mês do eixo X), para a linha terminar no mesmo total do
    resumo (ver `test_burnup_grafico_termina_no_mesmo_total_do_resumo_entregue`)."""
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      const curStart = f4pSemStart(semestre(TODAY));
      const prevMid = new Date(curStart.getFullYear(), curStart.getMonth() - 3, 15);
      const prevSem = semestre(prevMid);
      const prevEnd = curStart;   // primeiro dia do semestre atual == dia seguinte ao fim do anterior
      S.model.teamFlow.ACT_TARDIA = ["Backlog", "Vazao"];
      CFG.flow.act_tardia = {cat:{vazao:"vazao"}, ct:[]};
      S.model.ops.set("t1", {id:"t1", title:"T1", team:"ACT_TARDIA", type:"User Story", stName:"Vazao", deploy:prevEnd, ready:prevEnd, tags:["ROADMAP"]});   // entregue DEPOIS do fim do semestre anterior
      S.model.inis.set("INI_T", {id:"INI_T", valid:true, title:"Ini", exec:prevSem, owner:null, rels:["REL_T"]});
      S.model.rels.set("REL_T", {id:"REL_T", valid:true, title:"Rel", parent:"INI_T", epis:["EPI_T"]});
      S.model.epis.set("EPI_T", {id:"EPI_T", valid:true, title:"Epi", parent:"REL_T", target:null, interno:prevSem, st:0, ops:["t1"], type:"Epic"});
      S.model.teams.push("ACT_TARDIA");
      S.f.team = "ACT_TARDIA"; S.f.int = prevSem;
      render();
      const bu = actBurnupData();
      return {escopo: bu.escopo, entreguesN: bu.entreguesN, faltam: bu.faltam, faltamIds: bu.faltamItems.map(o=>o.id), entregueIds: bu.entregues.map(o=>o.id), cumulativeUltimoMes: bu.cumulative[bu.cumulative.length - 1]};
    }""")
    assert r["escopo"] == 1
    assert r["entreguesN"] == 1 and r["faltam"] == 0
    assert r["entregueIds"] == ["t1"] and r["faltamIds"] == []
    # decisão 0059: a entrega tardia é encaixada no último mês do gráfico, então a linha já reflete o
    # total entregue desde o fim do período, batendo com o resumo (ver teste dedicado abaixo).
    assert r["cumulativeUltimoMes"] == 1

def test_burnup_grafico_termina_no_mesmo_total_do_resumo_entregue(page):
    """Decisão 0059 (correção): o usuário relatou (print do time BO) o resumo mostrando "11 entregues"
    enquanto a linha do gráfico terminava visivelmente abaixo de 11 — a entrega de um item fora do
    período exato do semestre (decisão 0058: ainda conta como "entregue" no resumo) não tinha onde
    entrar no gráfico, então a linha nunca alcançava o total real. A linha agora sempre termina no mesmo
    valor de `entreguesN`: uma entrega antes do início do semestre entra no 1º mês do eixo X; uma depois
    do fim entra no último."""
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      const sem = semestre(TODAY);
      const curStart = f4pSemStart(sem);
      const antes = new Date(curStart.getFullYear(), curStart.getMonth() - 1, 15);   // antes do início
      const depois = new Date(curStart.getFullYear(), curStart.getMonth() + 7, 15);   // depois do fim (semestre tem 6 meses)
      const dentro = new Date(curStart.getFullYear(), curStart.getMonth() + 1, 15);
      S.model.teamFlow.ACT_BORDAS = ["Backlog", "Vazao"];
      CFG.flow.act_bordas = {cat:{vazao:"vazao"}, ct:[]};
      S.model.ops.set("x1", {id:"x1", title:"X1", team:"ACT_BORDAS", type:"User Story", stName:"Vazao", deploy:antes, ready:antes, tags:["ROADMAP"]});
      S.model.ops.set("x2", {id:"x2", title:"X2", team:"ACT_BORDAS", type:"User Story", stName:"Vazao", deploy:depois, ready:depois, tags:["ROADMAP"]});
      S.model.ops.set("x3", {id:"x3", title:"X3", team:"ACT_BORDAS", type:"User Story", stName:"Vazao", deploy:dentro, ready:dentro, tags:["ROADMAP"]});
      S.model.inis.set("INI_X", {id:"INI_X", valid:true, title:"Ini", exec:sem, owner:null, rels:["REL_X"]});
      S.model.rels.set("REL_X", {id:"REL_X", valid:true, title:"Rel", parent:"INI_X", epis:["EPI_X"]});
      S.model.epis.set("EPI_X", {id:"EPI_X", valid:true, title:"Epi", parent:"REL_X", target:null, interno:null, st:0, ops:["x1","x2","x3"], type:"Epic"});
      S.model.teams.push("ACT_BORDAS");
      S.f.team = "ACT_BORDAS"; S.f.exec = sem;
      render();
      const bu = actBurnupData();
      return {entreguesN: bu.entreguesN, cumulative: bu.cumulative};
    }""")
    assert r["entreguesN"] == 3
    assert r["cumulative"][0] == 1          # x1 (antes do início) já entra no 1º mês
    assert r["cumulative"][-1] == 3          # x2 (depois do fim) entra no último mês — bate com entreguesN
    assert max(r["cumulative"]) == r["entreguesN"]

def test_burnup_entrega_depois_do_fim_estende_o_eixo_em_vez_de_clampar(page):
    """Decisão 0060 (revê a metade "depois do fim" da 0059): em vez de encaixar a entrega tardia no
    último mês do eixo (um mês que não é o real), o gráfico agora ESTENDE o eixo X com os meses
    seguintes de verdade, até cobrir a entrega mais tardia, e marca a fronteira (semEndIdx/extended) —
    pedido do usuário depois de ver o print do time BO: a linha devia mostrar o mês real da entrega, com
    uma linha vertical sinalizando onde o semestre comprometido terminou. Usa um semestre já ENCERRADO
    (mesmo padrão da decisão 0058) para garantir os 6 meses cheios do semestre como base, independente
    de em que mês do semestre em curso os testes rodam."""
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      const curStart = f4pSemStart(semestre(TODAY));
      const prevMid = new Date(curStart.getFullYear(), curStart.getMonth() - 3, 15);
      const prevSem = semestre(prevMid);
      const prevStart = f4pSemStart(prevSem);
      const doisMesesDepois = new Date(prevStart.getFullYear(), prevStart.getMonth() + 7, 15);   // 2 meses após o fim (semestre tem 6 meses, índices 0-5)
      S.model.teamFlow.ACT_ESTENDE = ["Backlog", "Vazao"];
      CFG.flow.act_estende = {cat:{vazao:"vazao"}, ct:[]};
      S.model.ops.set("y1", {id:"y1", title:"Y1", team:"ACT_ESTENDE", type:"User Story", stName:"Vazao", deploy:doisMesesDepois, ready:doisMesesDepois, tags:["ROADMAP"]});
      S.model.inis.set("INI_Y", {id:"INI_Y", valid:true, title:"Ini", exec:prevSem, owner:null, rels:["REL_Y"]});
      S.model.rels.set("REL_Y", {id:"REL_Y", valid:true, title:"Rel", parent:"INI_Y", epis:["EPI_Y"]});
      S.model.epis.set("EPI_Y", {id:"EPI_Y", valid:true, title:"Epi", parent:"REL_Y", target:null, interno:null, st:0, ops:["y1"], type:"Epic"});
      S.model.teams.push("ACT_ESTENDE");
      S.f.team = "ACT_ESTENDE"; S.f.exec = prevSem;
      render();
      const bu = actBurnupData();
      return {monthsLen: bu.months.length, semEndIdx: bu.semEndIdx, extended: bu.extended,
        ultimoMesTime: bu.months[bu.months.length - 1].getTime(), mesRealEsperado: new Date(doisMesesDepois.getFullYear(), doisMesesDepois.getMonth(), 1).getTime(),
        cumulativeUltimo: bu.cumulative[bu.cumulative.length - 1]};
    }""")
    assert r["extended"] is True
    assert r["semEndIdx"] == 5   # último mês real do semestre (índice 5, 6 meses: 0..5)
    assert r["monthsLen"] == 8   # 6 meses do semestre + 2 meses estendidos até a entrega
    assert r["ultimoMesTime"] == r["mesRealEsperado"]   # o item aparece no seu mês REAL, não clampado
    assert r["cumulativeUltimo"] == 1

def test_burnup_sem_entrega_tardia_nao_estende_nem_mostra_linha(page):
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      const sem = semestre(TODAY);
      S.model.teamFlow.ACT_SEMTARDIA = ["Backlog", "Vazao"];
      CFG.flow.act_semtardia = {cat:{vazao:"vazao"}, ct:[]};
      const start = f4pSemStart(sem), dentro = new Date(start.getFullYear(), start.getMonth() + 1, 15);
      S.model.ops.set("z1", {id:"z1", title:"Z1", team:"ACT_SEMTARDIA", type:"User Story", stName:"Vazao", deploy:dentro, ready:dentro, tags:["ROADMAP"]});
      S.model.teams.push("ACT_SEMTARDIA");
      S.f.team = "ACT_SEMTARDIA"; S.f.exec = sem;
      render();
      const bu = actBurnupData();
      return {extended: bu.extended, semEndIdx: bu.semEndIdx, svgTemLinha: actBurnupSvg(bu).includes("act-sem-end")};
    }""")
    assert r == {"extended": False, "semEndIdx": None, "svgTemLinha": False}

def test_burnup_estende_mesmo_com_entrega_tardia_de_item_fora_da_reserva(page):
    """Decisão 0061 (correção da 0060): o usuário reportou, depois da 0060, que o Burnup Reserva ficava
    "preso" no último mês do semestre (jun) enquanto o CFD e a Distribuição já mostravam julho/agosto —
    print com "5 reservados · 5 entregues · 0 faltam" e a linha do Burnup já achatada no topo, sem a
    linha "fim do semestre" que os outros dois quadrantes mostravam. Causa: a extensão do Burnup só
    reagia a item da própria Reserva (`entregues`/`capItems`, com a tag ROADMAP); o item que disparava a
    extensão no CFD/Distribuição era de um tipo do CT mas SEM a tag — fazia parte do mesmo épico
    comprometido, mas não da Reserva. Correção: o gatilho da extensão passa a usar `actLateDeliveries`
    (qualquer item do épico comprometido, mesmo critério do CFD/Distribuição) — os números "Entregue"/
    "Faltam" do resumo continuam baseados só na Reserva, só o eixo passa a reagir ao épico inteiro."""
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      const curStart = f4pSemStart(semestre(TODAY));
      const prevMid = new Date(curStart.getFullYear(), curStart.getMonth() - 3, 15);
      const prevSem = semestre(prevMid);
      const prevStart = f4pSemStart(prevSem);
      const dentro = new Date(prevStart.getFullYear(), prevStart.getMonth() + 1, 15);
      const tardia = new Date(prevStart.getFullYear(), prevStart.getMonth() + 7, 10);   // bem depois do fim
      S.model.teamFlow.ACT_FORADARESERVA = ["Backlog", "Vazao"];
      CFG.flow.act_foradareserva = {cat:{vazao:"vazao"}, ct:[]};
      // n1: reservado (tag ROADMAP), entregue dentro do semestre — é o que o resumo "Entregue" mede
      S.model.ops.set("n1", {id:"n1", title:"N1", team:"ACT_FORADARESERVA", type:"User Story", stName:"Vazao", deploy:dentro, ready:dentro, tags:["ROADMAP"]});
      // n2: mesmo épico, mesmo tipo do CT, SEM a tag ROADMAP (fora da Reserva) — entregue bem depois do
      // fim do semestre; antes da 0061, não disparava a extensão do Burnup (só CFD/Distribuição reagiam)
      S.model.ops.set("n2", {id:"n2", title:"N2", team:"ACT_FORADARESERVA", type:"User Story", stName:"Vazao", deploy:tardia, ready:tardia, tags:[]});
      S.model.inis.set("INI_N", {id:"INI_N", valid:true, title:"Ini", exec:prevSem, owner:null, rels:["REL_N"]});
      S.model.rels.set("REL_N", {id:"REL_N", valid:true, title:"Rel", parent:"INI_N", epis:["EPI_N"]});
      S.model.epis.set("EPI_N", {id:"EPI_N", valid:true, title:"Epi", parent:"REL_N", target:null, interno:null, st:0, ops:["n1", "n2"], type:"Epic"});
      S.model.teams.push("ACT_FORADARESERVA");
      S.f.team = "ACT_FORADARESERVA"; S.f.exec = prevSem;
      render();
      const bu = actBurnupData();
      return {escopo: bu.escopo, entreguesN: bu.entreguesN, faltam: bu.faltam, entregueIds: bu.entregues.map(o=>o.id),
        extended: bu.extended, semEndIdx: bu.semEndIdx,
        ultimoMesTime: bu.months[bu.months.length - 1].getTime(), mesRealEsperado: new Date(tardia.getFullYear(), tardia.getMonth(), 1).getTime()};
    }""")
    assert r["escopo"] == 1 and r["entreguesN"] == 1 and r["faltam"] == 0   # só n1 é Reserva — números inalterados
    assert r["entregueIds"] == ["n1"]   # n2 nunca entra no "Entregue" (não é Reserva), só estende o eixo
    assert r["extended"] is True
    assert r["semEndIdx"] == 5
    assert r["ultimoMesTime"] == r["mesRealEsperado"]   # eixo chega no mês real da entrega de n2

def test_os_4_quadrantes_tem_regra_definida(page):
    carregar(page, "f4p.xlsx")
    _habilitar(page)
    page.click("#actTab")
    page.wait_for_timeout(200)
    titulos = page.evaluate("[...document.querySelectorAll('#actBody .f4p-card-h')].map(x=>x.textContent)")
    # ordem de leitura em linhas (decisão 0047): CT+Burnup na 1ª linha, Distribuição+CFD na 2ª —
    # diferente da ordem por coluna de antes, para os quadrantes 3 e 4 ficarem alinhados na mesma altura.
    assert titulos == ["CycleTime", "Burnup Reserva", "Distribuição Vazão por mês", "CFD (Cumulative Flow Diagram)"]
    assert page.locator("#actBody .an-empty", has_text="Regra de cálculo ainda em definição.").count() == 0

def test_quadrantes_3_e_4_ficam_alinhados_na_mesma_altura(page):
    """Melhoria pedida pelo usuário: os quadrantes 3 e 4 devem começar na mesma altura — antes, cada
    coluna empilhava seus dois quadrantes de forma independente, então uma diferença de altura entre os
    quadrantes 1 e 2 (que ficam acima) desalinhava o início dos quadrantes 3 e 4 (decisão 0047)."""
    carregar(page, "f4p.xlsx")
    _habilitar(page)
    page.click("#actTab")
    page.wait_for_timeout(200)
    tops = page.evaluate("[...document.querySelectorAll('#actBody .f4p-card')].map(c => c.getBoundingClientRect().top)")
    # ordem de leitura: [CT, Burnup, Distribuição, CFD] — linha 1 = CT+Burnup, linha 2 = Distribuição+CFD
    assert abs(tops[0] - tops[1]) < 1
    assert abs(tops[2] - tops[3]) < 1

# ---------------- Quadrante 3 · Distribuição Vazão por mês (decisão 0044) ----------------
# Para cada mês do semestre selecionado (do time em foco), dos itens ENTREGUES (Vazão) naquele mês —
# de qualquer tipo, exceto os tipos de bug configurados (CFG.act.bugTypes) — quanto % é User Story
# (mesmo critério do User Story do Report F4P, CFG.f4p.usTypes), quanto % é Technical Story (tipo fixo,
# mesmo critério do Technical Story do Report F4P) e quanto % é "demais" (o resto, sem bugs). Um mês
# sem nenhum item na amostra mostra uma barra cinza cheia com 0,00% — o gráfico sempre mostra os 6
# meses do semestre inteiro (não só os já decorridos).

def test_dist_meses_cobrem_o_semestre_inteiro_mesmo_em_curso(page):
    """Diferente do Burnup (que para em 'hoje' num semestre em curso), a Distribuição sempre mostra os
    6 meses inteiros do semestre selecionado — os ainda não decorridos entram como referência."""
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      const sem = semestre(TODAY);
      S.f.exec = sem;
      const start = f4pSemStart(sem);
      const meses = actDistMonths(f4pSemesterState());
      return {n: meses.length, primeiro: meses[0].getTime(), ultimoEsperado: new Date(start.getFullYear(), start.getMonth()+5, 1).getTime(), ultimo: meses[meses.length-1].getTime()};
    }""")
    assert r["n"] == 6
    assert r["ultimo"] == r["ultimoEsperado"]

def test_dist_classifica_user_story_technical_story_e_demais(page):
    carregar(page, "f4p.xlsx")
    sem = page.evaluate("semestre(TODAY)")
    r = page.evaluate("""(sem)=>{
      S.model.teamFlow.ACT_DIST1 = ["Backlog", "Vazao"];
      CFG.flow.act_dist1 = {cat:{vazao:"vazao"}, ct:[]};
      const start = f4pSemStart(sem), m0 = new Date(start.getFullYear(), start.getMonth(), 10);
      S.model.ops.set("d1", {id:"d1", title:"D1", team:"ACT_DIST1", type:"User Story", stName:"Vazao", deploy:m0, tags:[]});
      S.model.ops.set("d2", {id:"d2", title:"D2", team:"ACT_DIST1", type:"User Story", stName:"Vazao", deploy:m0, tags:[]});
      S.model.ops.set("d3", {id:"d3", title:"D3", team:"ACT_DIST1", type:"User Story", stName:"Vazao", deploy:m0, tags:[]});
      S.model.ops.set("d4", {id:"d4", title:"D4", team:"ACT_DIST1", type:"Technical Story", stName:"Vazao", deploy:m0, tags:[]});
      S.model.teams.push("ACT_DIST1");
      S.f.team = "ACT_DIST1"; S.f.exec = sem;
      render();
      const data = actDistData("ACT_DIST1", f4pSemesterState());
      return {total: data[0].total, usPct: data[0].usPct, tsPct: data[0].tsPct, demaisPct: data[0].demaisPct};
    }""", sem)
    assert r == {"total": 4, "usPct": 75, "tsPct": 25, "demaisPct": 0}

def test_dist_tipo_fora_de_user_story_e_technical_story_conta_como_demais(page):
    carregar(page, "f4p.xlsx")
    sem = page.evaluate("semestre(TODAY)")
    r = page.evaluate("""(sem)=>{
      S.model.teamFlow.ACT_DIST2 = ["Backlog", "Vazao"];
      CFG.flow.act_dist2 = {cat:{vazao:"vazao"}, ct:[]};
      const start = f4pSemStart(sem), m0 = new Date(start.getFullYear(), start.getMonth(), 10);
      S.model.ops.set("e1", {id:"e1", title:"E1", team:"ACT_DIST2", type:"User Story", stName:"Vazao", deploy:m0, tags:[]});
      S.model.ops.set("e2", {id:"e2", title:"E2", team:"ACT_DIST2", type:"Feature", stName:"Vazao", deploy:m0, tags:[]});
      S.model.ops.set("e3", {id:"e3", title:"E3", team:"ACT_DIST2", type:"Feature", stName:"Vazao", deploy:m0, tags:[]});
      S.model.teams.push("ACT_DIST2");
      S.f.team = "ACT_DIST2"; S.f.exec = sem;
      render();
      const b = actDistBuckets("ACT_DIST2", start);
      return {us: b.us.map(o=>o.id), ts: b.ts.map(o=>o.id), demais: b.demais.map(o=>o.id).sort()};
    }""", sem)
    assert r == {"us": ["e1"], "ts": [], "demais": ["e2", "e3"]}

def test_dist_exclui_tipos_bug_da_amostra(page):
    carregar(page, "f4p.xlsx")
    sem = page.evaluate("semestre(TODAY)")
    r = page.evaluate("""(sem)=>{
      S.model.teamFlow.ACT_DIST3 = ["Backlog", "Vazao"];
      CFG.flow.act_dist3 = {cat:{vazao:"vazao"}, ct:[]};
      const start = f4pSemStart(sem), m0 = new Date(start.getFullYear(), start.getMonth(), 10);
      S.model.ops.set("f1", {id:"f1", title:"F1", team:"ACT_DIST3", type:"User Story", stName:"Vazao", deploy:m0, tags:[]});
      S.model.ops.set("f2", {id:"f2", title:"F2", team:"ACT_DIST3", type:"Internal Bug", stName:"Vazao", deploy:m0, tags:[]});
      S.model.ops.set("f3", {id:"f3", title:"F3", team:"ACT_DIST3", type:"Bug", stName:"Vazao", deploy:m0, tags:[]});
      S.model.ops.set("f4", {id:"f4", title:"F4", team:"ACT_DIST3", type:"External Bug", stName:"Vazao", deploy:m0, tags:[]});
      S.model.teams.push("ACT_DIST3");
      S.f.team = "ACT_DIST3"; S.f.exec = sem;
      render();
      const items = actDistItems("ACT_DIST3", start);
      return items.map(o=>o.id);
    }""", sem)
    assert r == ["f1"]

def test_dist_tipos_bug_sao_configuraveis(page):
    carregar(page, "f4p.xlsx")
    sem = page.evaluate("semestre(TODAY)")
    r = page.evaluate("""(sem)=>{
      S.model.teamFlow.ACT_DIST4 = ["Backlog", "Vazao"];
      CFG.flow.act_dist4 = {cat:{vazao:"vazao"}, ct:[]};
      CFG.act.bugTypes = ["custom bug"];
      const start = f4pSemStart(sem), m0 = new Date(start.getFullYear(), start.getMonth(), 10);
      S.model.ops.set("g1", {id:"g1", title:"G1", team:"ACT_DIST4", type:"Internal Bug", stName:"Vazao", deploy:m0, tags:[]});   // não é mais bug configurado: conta como "demais"
      S.model.ops.set("g2", {id:"g2", title:"G2", team:"ACT_DIST4", type:"Custom Bug", stName:"Vazao", deploy:m0, tags:[]});      // agora é o tipo bug configurado: excluído
      S.model.teams.push("ACT_DIST4");
      S.f.team = "ACT_DIST4"; S.f.exec = sem;
      render();
      const items = actDistItems("ACT_DIST4", start).map(o=>o.id);
      CFG.act.bugTypes = ["bug", "internal bug", "external bug"];
      return items;
    }""", sem)
    assert r == ["g1"]

def test_dist_mes_sem_registro_mostra_zero_porcento_cinza(page):
    carregar(page, "f4p.xlsx")
    sem = page.evaluate("semestre(TODAY)")
    page.evaluate("""(sem)=>{
      S.model.teams.push("ACT_DIST5");
      S.f.team = "ACT_DIST5"; S.f.exec = sem;
      render();
    }""", sem)
    page.click("#actTab")
    page.wait_for_timeout(200)
    rows = page.locator(".act-dist-row")
    assert rows.count() == 6
    for i in range(6):
        row = rows.nth(i)
        assert row.locator(".act-dist-none").count() == 1
        assert "0,00%" in row.locator(".act-dist-none").inner_text()
        assert row.locator("button.act-dist-seg").count() == 0   # sem registro não é clicável

def test_dist_barra_sem_registro_nao_conta_bug_isolado_como_registro(page):
    """Um mês onde a única entrega é de um tipo bug (excluído por inteiro) também é 'sem registro'."""
    carregar(page, "f4p.xlsx")
    sem = page.evaluate("semestre(TODAY)")
    r = page.evaluate("""(sem)=>{
      S.model.teamFlow.ACT_DIST6 = ["Backlog", "Vazao"];
      CFG.flow.act_dist6 = {cat:{vazao:"vazao"}, ct:[]};
      const start = f4pSemStart(sem), m0 = new Date(start.getFullYear(), start.getMonth(), 10);
      S.model.ops.set("h1", {id:"h1", title:"H1", team:"ACT_DIST6", type:"Bug", stName:"Vazao", deploy:m0, tags:[]});
      S.model.teams.push("ACT_DIST6");
      S.f.team = "ACT_DIST6"; S.f.exec = sem;
      render();
      const data = actDistData("ACT_DIST6", f4pSemesterState());
      return data[0].total;
    }""", sem)
    assert r == 0

def test_dist_porcentagem_arredonda_para_duas_casas_decimais(page):
    carregar(page, "f4p.xlsx")
    sem = page.evaluate("semestre(TODAY)")
    r = page.evaluate("""(sem)=>{
      S.model.teamFlow.ACT_DIST7 = ["Backlog", "Vazao"];
      CFG.flow.act_dist7 = {cat:{vazao:"vazao"}, ct:[]};
      const start = f4pSemStart(sem), m0 = new Date(start.getFullYear(), start.getMonth(), 10);
      S.model.ops.set("i1", {id:"i1", title:"I1", team:"ACT_DIST7", type:"User Story", stName:"Vazao", deploy:m0, tags:[]});
      S.model.ops.set("i2", {id:"i2", title:"I2", team:"ACT_DIST7", type:"Feature", stName:"Vazao", deploy:m0, tags:[]});
      S.model.ops.set("i3", {id:"i3", title:"I3", team:"ACT_DIST7", type:"Feature", stName:"Vazao", deploy:m0, tags:[]});
      S.model.teams.push("ACT_DIST7");
      S.f.team = "ACT_DIST7"; S.f.exec = sem;
      render();
      return dec2(actDistData("ACT_DIST7", f4pSemesterState())[0].usPct);
    }""", sem)
    assert r == "33,33"

def test_dist_clique_em_cada_fatia_abre_so_os_itens_daquele_tipo_no_mes(page):
    carregar(page, "f4p.xlsx")
    sem = page.evaluate("semestre(TODAY)")
    page.evaluate("""(sem)=>{
      S.model.teamFlow.ACT_DIST8 = ["Backlog", "Vazao"];
      CFG.flow.act_dist8 = {cat:{vazao:"vazao"}, ct:[]};
      const start = f4pSemStart(sem), m0 = new Date(start.getFullYear(), start.getMonth(), 10);
      S.model.ops.set("j1", {id:"j1", title:"J1", team:"ACT_DIST8", type:"User Story", stName:"Vazao", deploy:m0, tags:[]});
      S.model.ops.set("j2", {id:"j2", title:"J2", team:"ACT_DIST8", type:"Technical Story", stName:"Vazao", deploy:m0, tags:[]});
      S.model.ops.set("j3", {id:"j3", title:"J3", team:"ACT_DIST8", type:"Feature", stName:"Vazao", deploy:m0, tags:[]});
      S.model.teams.push("ACT_DIST8");
      S.f.team = "ACT_DIST8"; S.f.exec = sem;
      render();
    }""", sem)
    page.click("#actTab")
    page.wait_for_timeout(200)
    page.click(".act-dist-seg.act-dist-us")
    assert page.is_visible("#f4pItemsBg")
    assert "j1" in page.inner_text("#f4pItemsBody") and "j2" not in page.inner_text("#f4pItemsBody") and "j3" not in page.inner_text("#f4pItemsBody")
    page.click("#f4pItemsClose")
    page.click(".act-dist-seg.act-dist-ts")
    assert "j2" in page.inner_text("#f4pItemsBody") and "j1" not in page.inner_text("#f4pItemsBody")
    page.click("#f4pItemsClose")
    page.click(".act-dist-seg.act-dist-demais")
    assert "j3" in page.inner_text("#f4pItemsBody") and "j1" not in page.inner_text("#f4pItemsBody")

def test_dist_aparece_no_painel_com_legenda(page):
    carregar(page, "f4p.xlsx")
    _habilitar(page)
    page.click("#actTab")
    page.wait_for_timeout(200)
    txt = page.inner_text("#actBody")
    assert "Distribuição Vazão por mês" in txt
    assert "User Story" in txt and "Technical Story" in txt and "Demais" in txt and "Sem registro" in txt

# Decisão 0060: se um item entregue (Vazão) cai num mês além dos 6 do semestre, mas pertence a um
# épico comprometido com o roadmap (mesmo critério do CFD/Burnup — `actLateDeliveries`), o mês extra
# aparece no quadrante, marcado com um ícone de alerta (⚠) junto ao rótulo — sem linha vertical (não se
# aplica a um gráfico de barras). O mês extra segue a MESMA regra de qualquer outro mês do quadrante
# (todas as entregas Vazão do time naquele mês civil, sem filtrar por épico) — só a decisão de MOSTRAR
# o mês é que depende do épico comprometido.

def test_dist_mes_extra_aparece_com_alerta_quando_ha_entrega_tardia_de_epico_comprometido(page):
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      const sem = semestre(TODAY);
      S.model.teamFlow.ACT_DIST_LATE = ["Backlog", "Vazao"];
      CFG.flow.act_dist_late = {cat:{vazao:"vazao"}, ct:[]};
      const start = f4pSemStart(sem), mesExtra = new Date(start.getFullYear(), start.getMonth() + 6, 10);
      // k1: pertence a um épico comprometido com o roadmap — é o que dispara o mês extra
      S.model.ops.set("k1", {id:"k1", title:"K1", team:"ACT_DIST_LATE", type:"User Story", stName:"Vazao", deploy:mesExtra, ready:mesExtra, tags:[]});
      // k2: mesmo mês extra, mas SEM vínculo com épico comprometido — ainda assim entra na barra (mesma
      // regra de qualquer mês do quadrante, que não filtra por épico)
      S.model.ops.set("k2", {id:"k2", title:"K2", team:"ACT_DIST_LATE", type:"Technical Story", stName:"Vazao", deploy:mesExtra, ready:mesExtra, tags:[]});
      S.model.inis.set("INI_K", {id:"INI_K", valid:true, title:"Ini", exec:sem, owner:null, rels:["REL_K"]});
      S.model.rels.set("REL_K", {id:"REL_K", valid:true, title:"Rel", parent:"INI_K", epis:["EPI_K"]});
      S.model.epis.set("EPI_K", {id:"EPI_K", valid:true, title:"Epi", parent:"REL_K", target:null, interno:null, st:0, ops:["k1"], type:"Epic"});
      S.model.teams.push("ACT_DIST_LATE");
      S.f.team = "ACT_DIST_LATE"; S.f.exec = sem;
      render();
      const data = actDistData("ACT_DIST_LATE", f4pSemesterState());
      return {n: data.length, late6: data[6] ? data[6].late : null, total6: data[6] ? data[6].total : null, lateAntes: data.slice(0, 6).every(d => !d.late)};
    }""")
    assert r["n"] == 7
    assert r["late6"] is True
    assert r["total6"] == 2   # k1 e k2, mesma regra de qualquer mês (sem filtrar por épico)
    assert r["lateAntes"] is True

def test_dist_icone_de_alerta_aparece_no_mes_extra_sem_linha_vertical(page):
    carregar(page, "f4p.xlsx")
    page.evaluate("""()=>{
      const sem = semestre(TODAY);
      S.model.teamFlow.ACT_DIST_ICON = ["Backlog", "Vazao"];
      CFG.flow.act_dist_icon = {cat:{vazao:"vazao"}, ct:[]};
      const start = f4pSemStart(sem), mesExtra = new Date(start.getFullYear(), start.getMonth() + 6, 10);
      S.model.ops.set("l1", {id:"l1", title:"L1", team:"ACT_DIST_ICON", type:"User Story", stName:"Vazao", deploy:mesExtra, ready:mesExtra, tags:[]});
      S.model.inis.set("INI_L", {id:"INI_L", valid:true, title:"Ini", exec:sem, owner:null, rels:["REL_L"]});
      S.model.rels.set("REL_L", {id:"REL_L", valid:true, title:"Rel", parent:"INI_L", epis:["EPI_L"]});
      S.model.epis.set("EPI_L", {id:"EPI_L", valid:true, title:"Epi", parent:"REL_L", target:null, interno:null, st:0, ops:["l1"], type:"Epic"});
      S.model.teams.push("ACT_DIST_ICON");
      S.f.team = "ACT_DIST_ICON"; S.f.exec = sem;
      render();
    }""")
    page.click("#actTab")
    page.wait_for_timeout(200)
    rows = page.locator(".act-dist-row")
    assert rows.count() == 7
    assert rows.nth(6).locator(".act-dist-late-icon").count() == 1
    for i in range(6):
        assert rows.nth(i).locator(".act-dist-late-icon").count() == 0
    # decisão 0061: o Burnup Reserva também reage ao mesmo item tardio (mesmo épico comprometido) e
    # desenha sua própria linha "fim do semestre" — mas a Distribuição (quadrante de barras) nunca tem
    # uma, então escopamos a checagem ao próprio card da Distribuição.
    assert page.locator(".act-dist .act-sem-end").count() == 0

def test_dist_nao_estende_quando_entrega_tardia_nao_pertence_a_epico_comprometido(page):
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      const sem = semestre(TODAY);
      S.model.teamFlow.ACT_DIST_NOEXT = ["Backlog", "Vazao"];
      CFG.flow.act_dist_noext = {cat:{vazao:"vazao"}, ct:[]};
      const start = f4pSemStart(sem), mesExtra = new Date(start.getFullYear(), start.getMonth() + 6, 10);
      // item tardio só vinculado ao time, sem épico comprometido com o roadmap
      S.model.ops.set("m1", {id:"m1", title:"M1", team:"ACT_DIST_NOEXT", type:"User Story", stName:"Vazao", deploy:mesExtra, ready:mesExtra, tags:[]});
      S.model.teams.push("ACT_DIST_NOEXT");
      S.f.team = "ACT_DIST_NOEXT"; S.f.exec = sem;
      render();
      return actDistMonths(f4pSemesterState()).length;
    }""")
    assert r == 6

def test_configuracao_act_bug_types_tem_padrao(page):
    r = page.evaluate("()=>{ const c = normCfg({}); return c.act.bugTypes; }")
    assert r == ["bug", "internal bug", "external bug"]

def test_configuracao_act_bug_types_persiste_e_entra_na_exportacao(page):
    carregar(page, "times.xlsx")
    page.evaluate("()=>{ CFG.act.bugTypes = ['bug', 'defeito']; }")
    page.click("#btnCfg")
    with page.expect_download() as d:
        page.click("#cfgExport")
    txt = open(d.value.path(), encoding="utf-8").read()
    assert '"bugTypes"' in txt and '"defeito"' in txt

# ---------------- Quadrante 4 · CFD - Cumulative Flow Diagram (decisão 0045) ----------------
# Para cada semana do semestre selecionado (blocos de 7 dias a partir do 1º dia, terminando exatamente
# no último dia do semestre), reconstrói quantos itens do time já chegaram a cada categoria de fluxo —
# Nenhum/Discovery/WIP/Vazão — usando as datas de entrada por coluna já guardadas no modelo (`o.fd`,
# decisão 0006). Empilhamento estilo ActionableAgile: Vazão na base, Nenhum no topo (nunca diminui).

def test_cfd_semanas_em_blocos_de_7_dias_cobrindo_o_semestre_inteiro(page):
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      const sem = semestre(TODAY);
      S.f.exec = sem;
      const st = f4pSemesterState();
      const weeks = actCfdWeeks(st);
      const totalDias = Math.round((st.end - st.start) / 864e5) + 1;
      return {
        n: weeks.length,
        primeiroInicioBateComSemestre: weeks[0].from.getTime() === st.start.getTime(),
        ultimoFimBateComSemestre: weeks[weeks.length - 1].to.getTime() === st.end.getTime(),
        todasAsSemanasMenosAUltimaTem7Dias: weeks.slice(0, -1).every(w => Math.round((w.to - w.from) / 864e5) === 6),
        nEsperado: Math.ceil(totalDias / 7),
      };
    }""")
    assert r["primeiroInicioBateComSemestre"] is True
    assert r["ultimoFimBateComSemestre"] is True
    assert r["todasAsSemanasMenosAUltimaTem7Dias"] is True
    assert r["n"] == r["nEsperado"]

def test_cfd_categoria_em_data_usa_a_coluna_mais_avancada_ate_aquela_data(page):
    """Reconstrução histórica: a categoria do item numa data T é a da coluna mais avançada cuja data de
    entrada (o.fd) é menor ou igual a T — null se o item ainda não existia (nem a 1ª coluna bateu)."""
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      S.model.teamFlow.CFD_CAT1 = ["Backlog", "Discovery", "WIP", "Vazao"];
      CFG.flow.cfd_cat1 = {cat:{discovery:"disc", wip:"wip", vazao:"vazao"}, ct:[]};
      S.model.teams.push("CFD_CAT1");
      render();
      const c = teamCfg("CFD_CAT1");
      const d1 = new Date(2026,0,1), d2 = new Date(2026,0,10), d3 = new Date(2026,0,20);
      const o = {team:"CFD_CAT1", fd:{backlog:d1, wip:d2, vazao:d3}};   // pulou Discovery: sem data nessa coluna
      return {
        antesDeCriado: actCfdCategoriaEm(o, new Date(2025,11,31), c),
        entreCriacaoEWip: actCfdCategoriaEm(o, new Date(2026,0,5), c),
        entreWipEVazao: actCfdCategoriaEm(o, new Date(2026,0,15), c),
        depoisDeVazao: actCfdCategoriaEm(o, new Date(2026,0,25), c),
      };
    }""")
    assert r == {"antesDeCriado": None, "entreCriacaoEWip": "none", "entreWipEVazao": "wip", "depoisDeVazao": "vazao"}

def test_cfd_bandas_somam_o_total_de_itens_ja_criados(page):
    """As 4 faixas (Nenhum/Discovery/WIP/Vazão) formam uma partição exata do total de itens já criados
    (nenhum) numa semana — nunca sobram nem faltam itens na soma das faixas."""
    carregar(page, "f4p.xlsx")
    sem = page.evaluate("semestre(TODAY)")
    r = page.evaluate("""(sem)=>{
      S.model.teamFlow.CFD_B1 = ["Backlog", "Discovery", "WIP", "Vazao"];
      CFG.flow.cfd_b1 = {cat:{discovery:"disc", wip:"wip", vazao:"vazao"}, ct:[]};
      const start = f4pSemStart(sem);
      S.model.ops.set("b1", {team:"CFD_B1", fd:{backlog:start}});                                              // fica em Nenhum
      S.model.ops.set("b2", {team:"CFD_B1", fd:{backlog:start, discovery:start}});                             // fica em Discovery
      S.model.ops.set("b3", {team:"CFD_B1", fd:{backlog:start, discovery:start, wip:start}});                  // fica em WIP
      S.model.ops.set("b4", {team:"CFD_B1", fd:{backlog:start, discovery:start, wip:start, vazao:start}});     // fica em Vazão
      S.model.teams.push("CFD_B1");
      S.f.team = "CFD_B1"; S.f.exec = sem;
      render();
      const w0 = actCfdData("CFD_B1", f4pSemesterState())[0];
      return {bandNenhum:w0.bandNenhum, bandDisc:w0.bandDisc, bandWip:w0.bandWip, bandVazao:w0.bandVazao, nenhum:w0.nenhum};
    }""", sem)
    assert r == {"bandNenhum": 1, "bandDisc": 1, "bandWip": 1, "bandVazao": 1, "nenhum": 4}

def test_cfd_total_criado_nunca_diminui_ao_longo_das_semanas(page):
    """'Nenhum' (o total acumulado de itens já criados) só pode crescer ou ficar igual de uma semana pra
    outra — é a propriedade que dá nome ao diagrama (cumulative flow)."""
    carregar(page, "f4p.xlsx")
    sem = page.evaluate("semestre(TODAY)")
    r = page.evaluate("""(sem)=>{
      S.model.teamFlow.CFD_MONO = ["Backlog", "Vazao"];
      CFG.flow.cfd_mono = {cat:{vazao:"vazao"}, ct:[]};
      const start = f4pSemStart(sem);
      const dia = n => new Date(start.getFullYear(), start.getMonth(), start.getDate() + n);
      S.model.ops.set("m1", {team:"CFD_MONO", fd:{backlog: dia(0)}});    // semana 0
      S.model.ops.set("m2", {team:"CFD_MONO", fd:{backlog: dia(8)}});    // semana 1
      S.model.ops.set("m3", {team:"CFD_MONO", fd:{backlog: dia(22)}});   // semana 3
      S.model.teams.push("CFD_MONO");
      S.f.team = "CFD_MONO"; S.f.exec = sem;
      render();
      const nenhum = actCfdData("CFD_MONO", f4pSemesterState()).map(d => d.nenhum);
      const monotonico = nenhum.every((v, i) => i === 0 || v >= nenhum[i - 1]);
      return {monotonico, primeiras4: nenhum.slice(0, 4)};
    }""", sem)
    assert r["monotonico"] is True
    assert r["primeiras4"] == [1, 2, 2, 3]

def test_cfd_conta_bugs_por_padrao_e_pode_ser_desligado(page):
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      S.model.ops.set("bug1", {id:"bug1", team:"CFD_BUG", type:"Bug", fd:{}});
      S.model.ops.set("us1", {id:"us1", team:"CFD_BUG", type:"User Story", fd:{}});
      S.model.teams.push("CFD_BUG");
      const comBugs = actCfdOps("CFD_BUG").map(o=>o.id).sort();
      CFG.act.cfdIncludeBugs = false;
      const semBugs = actCfdOps("CFD_BUG").map(o=>o.id).sort();
      CFG.act.cfdIncludeBugs = true;
      return {comBugs, semBugs};
    }""")
    assert r == {"comBugs": ["bug1", "us1"], "semBugs": ["us1"]}

# Melhoria pedida pelo usuário depois de usar a 1ª versão (decisão 0046): um item já entregue (Vazão)
# antes do semestre selecionado inflava a faixa de Vazão com histórico de negócio alheio ao período em
# análise, dominando o gráfico inteiro. Reserva entregue e Distribuição Vazão por mês já restringem
# "Vazão" ao semestre selecionado (via o.deploy); o CFD passou a seguir a mesma convenção.

def test_cfd_exclui_itens_ja_entregues_antes_do_semestre_selecionado(page):
    """Um item de negócio antigo — criado e entregue bem antes do semestre selecionado — não deve
    aparecer em NENHUMA faixa do CFD (nem Nenhum, nem Vazão): ele já não faz parte do fluxo deste
    período. Um item novo, criado dentro do semestre, continua contando normalmente."""
    carregar(page, "f4p.xlsx")
    sem = page.evaluate("semestre(TODAY)")
    r = page.evaluate("""(sem)=>{
      S.model.teamFlow.CFD_OLD = ["Backlog", "Discovery", "WIP", "Vazao"];
      CFG.flow.cfd_old = {cat:{discovery:"disc", wip:"wip", vazao:"vazao"}, ct:[]};
      const start = f4pSemStart(sem);
      const antesDoSemestre = new Date(start.getFullYear(), start.getMonth(), start.getDate() - 30);
      S.model.ops.set("old1", {team:"CFD_OLD", fd:{backlog:antesDoSemestre, discovery:antesDoSemestre, wip:antesDoSemestre, vazao:antesDoSemestre}});
      S.model.ops.set("new1", {team:"CFD_OLD", fd:{backlog:start}});
      S.model.teams.push("CFD_OLD");
      S.f.team = "CFD_OLD"; S.f.exec = sem;
      render();
      const w0 = actCfdData("CFD_OLD", f4pSemesterState())[0];
      return {nenhum: w0.nenhum, vazao: w0.vazao};
    }""", sem)
    assert r == {"nenhum": 1, "vazao": 0}

def test_cfd_nao_exclui_item_entregue_no_1o_dia_do_semestre(page):
    """Limite exato: um item entregue no PRÓPRIO 1º dia do semestre (não antes) continua contando —
    só o que foi entregue estritamente antes do início do período sai do gráfico."""
    carregar(page, "f4p.xlsx")
    sem = page.evaluate("semestre(TODAY)")
    r = page.evaluate("""(sem)=>{
      S.model.teamFlow.CFD_EDGE = ["Backlog", "Vazao"];
      CFG.flow.cfd_edge = {cat:{vazao:"vazao"}, ct:[]};
      const start = f4pSemStart(sem);
      S.model.ops.set("e1", {team:"CFD_EDGE", fd:{backlog:start, vazao:start}});
      S.model.teams.push("CFD_EDGE");
      S.f.team = "CFD_EDGE"; S.f.exec = sem;
      render();
      const w0 = actCfdData("CFD_EDGE", f4pSemesterState())[0];
      return {nenhum: w0.nenhum, vazao: w0.vazao};
    }""", sem)
    assert r == {"nenhum": 1, "vazao": 1}

def test_cfd_vazao_comeca_em_zero_e_cresce_com_entregas_dentro_do_semestre(page):
    """Consequência direta da exclusão acima: a Vazão do gráfico começa em 0 no início do semestre e só
    cresce conforme entregas acontecem dentro dele — em vez de já nascer alta com histórico acumulado."""
    carregar(page, "f4p.xlsx")
    sem = page.evaluate("semestre(TODAY)")
    r = page.evaluate("""(sem)=>{
      S.model.teamFlow.CFD_GROW = ["Backlog", "Vazao"];
      CFG.flow.cfd_grow = {cat:{vazao:"vazao"}, ct:[]};
      const start = f4pSemStart(sem);
      const dia = n => new Date(start.getFullYear(), start.getMonth(), start.getDate() + n);
      S.model.ops.set("g1", {team:"CFD_GROW", fd:{backlog:start, vazao:dia(10)}});
      S.model.ops.set("g2", {team:"CFD_GROW", fd:{backlog:start, vazao:dia(20)}});
      S.model.teams.push("CFD_GROW");
      S.f.team = "CFD_GROW"; S.f.exec = sem;
      render();
      return actCfdData("CFD_GROW", f4pSemesterState()).map(d => d.vazao).slice(0, 4);
    }""", sem)
    assert r == [0, 1, 2, 2]

# Melhoria pedida pelo usuário (decisão 0047): num semestre em curso, o CFD não precisa "construir o
# resto do morro" — desenha só até a semana atual, marcada por uma linha vertical "hoje"; o restante do
# período fica em branco em vez de projetar uma continuação achatada. Num semestre já encerrado não há
# "resto" (todo o período já é passado), então desenha tudo normalmente, sem linha "hoje".

def test_cfd_semestre_em_curso_mostra_linha_hoje_e_nao_desenha_alem_dela(page):
    carregar(page, "f4p.xlsx")
    sem = page.evaluate("semestre(TODAY)")
    page.evaluate("""(sem)=>{
      S.model.teamFlow.CFD_HOJE = ["Backlog", "Vazao"];
      CFG.flow.cfd_hoje = {cat:{vazao:"vazao"}, ct:[]};
      const start = f4pSemStart(sem);
      S.model.ops.set("h1", {team:"CFD_HOJE", fd:{backlog:start}});
      S.model.teams.push("CFD_HOJE");
      S.f.team = "CFD_HOJE"; S.f.exec = sem;
      render();
    }""", sem)
    page.click("#actTab")
    page.wait_for_timeout(200)
    assert page.locator(".act-cfd-hoje").count() == 1
    totalSemanas = page.evaluate("actCfdWeeks(f4pSemesterState()).length")
    hitCount = page.locator(".act-cfd-hit").count()
    assert hitCount < totalSemanas   # não desenha as semanas futuras do semestre em curso

def test_cfd_semestre_encerrado_nao_mostra_linha_hoje_e_desenha_tudo(page):
    carregar(page, "f4p.xlsx")
    page.evaluate("""()=>{
      const curStart = f4pSemStart(semestre(TODAY));
      const prevMid = new Date(curStart.getFullYear(), curStart.getMonth() - 3, 15);
      const prevSem = semestre(prevMid);
      S.model.teamFlow.CFD_PAST = ["Backlog", "Vazao"];
      CFG.flow.cfd_past = {cat:{vazao:"vazao"}, ct:[]};
      const start = f4pSemStart(prevSem);
      S.model.ops.set("p1", {team:"CFD_PAST", fd:{backlog:start}});
      S.model.teams.push("CFD_PAST");
      S.f.team = "CFD_PAST"; S.f.int = prevSem;
      render();
    }""")
    page.click("#actTab")
    page.wait_for_timeout(200)
    assert page.locator(".act-cfd-hoje").count() == 0
    totalSemanas = page.evaluate("actCfdWeeks(f4pSemesterState()).length")
    hitCount = page.locator(".act-cfd-hit").count()
    assert hitCount == totalSemanas

# Decisão 0060: se um item entregue (Vazão) depois do fim do semestre pertence a um épico comprometido
# com o roadmap do time+semestre selecionado (mesmo critério da coluna "Projetada" da Visão analítica —
# `anData().projItems`, não exige a tag ROADMAP), o CFD estende o eixo X com as semanas seguintes reais
# até cobrir essa entrega, com uma linha vertical "fim do semestre" marcando a fronteira. Um item
# entregue tarde mas SEM vínculo com um épico comprometido (só vinculado ao time) não dispara a
# extensão — prova que o gatilho é o épico comprometido, não qualquer item do time.

def test_cfd_estende_semanas_quando_ha_entrega_tardia_de_epico_comprometido(page):
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      const curStart = f4pSemStart(semestre(TODAY));
      const prevMid = new Date(curStart.getFullYear(), curStart.getMonth() - 3, 15);
      const prevSem = semestre(prevMid);
      const prevStart = f4pSemStart(prevSem);
      const tardia = new Date(prevStart.getFullYear(), prevStart.getMonth() + 6, 20);   // ~3 semanas depois do fim do semestre
      S.model.teamFlow.CFD_LATE = ["Backlog", "Vazao"];
      CFG.flow.cfd_late = {cat:{vazao:"vazao"}, ct:[]};
      S.model.ops.set("c1", {id:"c1", title:"C1", team:"CFD_LATE", type:"User Story", stName:"Vazao", deploy:tardia, ready:tardia, fd:{backlog:prevStart, vazao:tardia}, tags:[]});
      S.model.inis.set("INI_C", {id:"INI_C", valid:true, title:"Ini", exec:prevSem, owner:null, rels:["REL_C"]});
      S.model.rels.set("REL_C", {id:"REL_C", valid:true, title:"Rel", parent:"INI_C", epis:["EPI_C"]});
      S.model.epis.set("EPI_C", {id:"EPI_C", valid:true, title:"Epi", parent:"REL_C", target:null, interno:null, st:0, ops:["c1"], type:"Epic"});
      S.model.teams.push("CFD_LATE");
      S.f.team = "CFD_LATE"; S.f.exec = prevSem;
      render();
      const st = f4pSemesterState();
      const baseLen = actCfdBaseWeeks(st).length, weeks = actCfdWeeks(st);
      const data = actCfdData("CFD_LATE", st);
      return {baseLen, weeksLen: weeks.length, semEndIdx: actCfdSemEndIdx(st), vazaoUltimaSemana: data[data.length - 1].vazao};
    }""")
    assert r["weeksLen"] > r["baseLen"]
    assert r["semEndIdx"] == r["baseLen"] - 1
    assert r["vazaoUltimaSemana"] == 1

def test_cfd_nao_estende_quando_entrega_tardia_nao_pertence_a_epico_comprometido(page):
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      const curStart = f4pSemStart(semestre(TODAY));
      const prevMid = new Date(curStart.getFullYear(), curStart.getMonth() - 3, 15);
      const prevSem = semestre(prevMid);
      const prevStart = f4pSemStart(prevSem);
      const tardia = new Date(prevStart.getFullYear(), prevStart.getMonth() + 6, 20);
      S.model.teamFlow.CFD_LATE2 = ["Backlog", "Vazao"];
      CFG.flow.cfd_late2 = {cat:{vazao:"vazao"}, ct:[]};
      // item tardio só vinculado ao time, sem épico comprometido com o roadmap
      S.model.ops.set("c2", {id:"c2", title:"C2", team:"CFD_LATE2", type:"User Story", stName:"Vazao", deploy:tardia, ready:tardia, fd:{backlog:prevStart, vazao:tardia}, tags:[]});
      S.model.teams.push("CFD_LATE2");
      S.f.team = "CFD_LATE2"; S.f.exec = prevSem;
      render();
      const st = f4pSemesterState();
      return {baseLen: actCfdBaseWeeks(st).length, weeksLen: actCfdWeeks(st).length};
    }""")
    assert r["weeksLen"] == r["baseLen"]

def test_cfd_linha_fim_do_semestre_aparece_so_quando_estendido(page):
    carregar(page, "f4p.xlsx")
    page.evaluate("""()=>{
      const curStart = f4pSemStart(semestre(TODAY));
      const prevMid = new Date(curStart.getFullYear(), curStart.getMonth() - 3, 15);
      const prevSem = semestre(prevMid);
      const prevStart = f4pSemStart(prevSem);
      const tardia = new Date(prevStart.getFullYear(), prevStart.getMonth() + 6, 20);
      S.model.teamFlow.CFD_LINE = ["Backlog", "Vazao"];
      CFG.flow.cfd_line = {cat:{vazao:"vazao"}, ct:[]};
      S.model.ops.set("c3", {id:"c3", title:"C3", team:"CFD_LINE", type:"User Story", stName:"Vazao", deploy:tardia, ready:tardia, fd:{backlog:prevStart, vazao:tardia}, tags:[]});
      S.model.inis.set("INI_D", {id:"INI_D", valid:true, title:"Ini", exec:prevSem, owner:null, rels:["REL_D"]});
      S.model.rels.set("REL_D", {id:"REL_D", valid:true, title:"Rel", parent:"INI_D", epis:["EPI_D"]});
      S.model.epis.set("EPI_D", {id:"EPI_D", valid:true, title:"Epi", parent:"REL_D", target:null, interno:null, st:0, ops:["c3"], type:"Epic"});
      S.model.teams.push("CFD_LINE");
      S.f.team = "CFD_LINE"; S.f.exec = prevSem;
      render();
    }""")
    page.click("#actTab")
    page.wait_for_timeout(200)
    # decisão 0061: o Burnup Reserva também reage ao mesmo item tardio (mesmo épico comprometido),
    # então a linha aparece nos dois quadrantes — aqui confirmamos especificamente a do CFD.
    assert page.locator(".act-cfd-wrap .act-sem-end").count() == 1

def test_cfd_aparece_no_painel_com_legenda_e_grafico(page):
    carregar(page, "f4p.xlsx")
    _habilitar(page)
    page.click("#actTab")
    page.wait_for_timeout(200)
    txt = page.inner_text("#actBody")
    assert "CFD (Cumulative Flow Diagram)" in txt
    assert "Nenhum" in txt and "Discovery" in txt and "WIP" in txt and "Vazão" in txt
    assert page.locator(".act-cfd-band").count() == 4

def test_cfd_tooltip_mostra_os_valores_da_semana_ao_passar_o_mouse(page):
    carregar(page, "f4p.xlsx")
    sem = page.evaluate("semestre(TODAY)")
    page.evaluate("""(sem)=>{
      S.model.teamFlow.CFD_TIP = ["Backlog", "Discovery", "WIP", "Vazao"];
      CFG.flow.cfd_tip = {cat:{discovery:"disc", wip:"wip", vazao:"vazao"}, ct:[]};
      const start = f4pSemStart(sem);
      S.model.ops.set("t1", {team:"CFD_TIP", fd:{backlog:start}});
      S.model.ops.set("t2", {team:"CFD_TIP", fd:{backlog:start, discovery:start}});
      S.model.teams.push("CFD_TIP");
      S.f.team = "CFD_TIP"; S.f.exec = sem;
      render();
    }""", sem)
    page.click("#actTab")
    page.wait_for_timeout(200)
    tip = page.evaluate("document.querySelector('.act-cfd-hit').querySelector('title').textContent")
    assert "Nenhum: 1" in tip and "Discovery: 1" in tip and "WIP: 0" in tip and "Vazão: 0" in tip

def test_configuracao_cfd_include_bugs_tem_padrao_true(page):
    r = page.evaluate("()=>{ const c = normCfg({}); return c.act.cfdIncludeBugs; }")
    assert r is True

def test_configuracao_cfd_include_bugs_tem_checkbox_e_persiste_ao_salvar(page):
    carregar(page, "times.xlsx")
    page.click("#btnCfg")
    assert page.is_checked("#cfgActCfdBugs")   # padrão: contar bugs
    page.uncheck("#cfgActCfdBugs")
    page.click("#cfgSave"); page.wait_for_timeout(200)
    assert page.evaluate("CFG.act.cfdIncludeBugs") is False

def test_configuracao_cfd_include_bugs_entra_na_exportacao(page):
    carregar(page, "times.xlsx")
    page.click("#btnCfg")
    page.uncheck("#cfgActCfdBugs")
    with page.expect_download() as d:
        page.click("#cfgExport")
    txt = open(d.value.path(), encoding="utf-8").read()
    assert '"cfdIncludeBugs": false' in txt

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
