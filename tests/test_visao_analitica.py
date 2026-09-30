"""Visão analítica do roadmap do time (docs/regras-de-negocio.md §10). Decisão 0027: Projetada e
Capacidade passam a ser sempre a soma dos números mostrados por épico na tabela (não uma contagem à
parte), a linha do épico mostra a quantidade reservada, e os dois números do cabeçalho ficam clicáveis
(mesma transparência do Report F4P: abrem a lista dos itens exatos que entram na soma). Decisão 0028:
removido o badge redundante "X US" da linha (já coberto pela coluna QTD); QTD e "reservado" de cada
linha também ficam clicáveis, abrindo a lista dos itens daquele épico especificamente."""
from conftest import carregar

def _setup_epico(page, *, team, itens, sem, tag=None):
    """Monta uma cadeia sintética Iniciativa → Release → Épico → itens do time, e habilita o filtro
    de Time + Roadmap executivo para o semestre dado. `itens` é uma lista de dicts (stName, tags, deploy)."""
    page.evaluate("""(args)=>{
      const {team, itens, sem, tag} = args;
      S.model.teamFlow[team] = ["Backlog", "WIP", "Vazao"];
      CFG.flow[norm(team)] = {cat:{wip:"wip", vazao:"vazao"}, ct:[]};
      const opKeys = itens.map((it, idx) => {
        const k = `${team}_op${idx}`;
        S.model.ops.set(k, {id:k, title:"Item "+idx, team, type:"User Story", stName: it.stName, deploy: it.deploy ? new Date(it.deploy) : null,
          ready: it.stName !== "Backlog" ? new Date(2026,0,1) : null, tags: it.tags || []});
        return k;
      });
      const iniId = `INI_${team}`, relId = `REL_${team}`, epiId = `EPI_${team}`;
      S.model.inis.set(iniId, {id:iniId, valid:true, title:"Iniciativa "+team, exec:sem, owner:null, rels:[relId]});
      S.model.rels.set(relId, {id:relId, valid:true, title:"Release "+team, parent:iniId, epis:[epiId]});
      S.model.epis.set(epiId, {id:epiId, valid:true, title:"Épico "+team, parent:relId, target:null, interno:null, st:0, ops:opKeys, type:"Epic"});
      S.f.team = team; S.f.exec = sem;
      render();
    }""", {"team": team, "itens": itens, "sem": sem, "tag": tag})

def test_projetada_e_soma_do_qtd_dos_epicos_da_tabela(page):
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      const sem = semestre(TODAY);
      return sem;
    }""")
    _setup_epico(page, team="AN_PROJ", sem=r, itens=[
        {"stName": "Backlog"}, {"stName": "WIP"}, {"stName": "Vazao", "deploy": "2026-01-05"},
    ])
    d = page.evaluate("anData()")
    assert d["proj"] == 3
    assert sum(row["qtd"] for row in d["rows"]) == d["proj"]

def test_capacidade_e_soma_dos_reservados_dos_epicos_da_tabela(page):
    carregar(page, "f4p.xlsx")
    sem = page.evaluate("semestre(TODAY)")
    _setup_epico(page, team="AN_CAP", sem=sem, itens=[
        {"stName": "Backlog", "tags": ["ROADMAP"]},
        {"stName": "WIP", "tags": ["ROADMAP"]},
        {"stName": "WIP", "tags": []},
    ])
    d = page.evaluate("anData()")
    assert d["cap"] == 2
    assert sum(len(row["reservados"]) for row in d["rows"]) == d["cap"]

def test_capacidade_usa_a_tag_configuravel(page):
    carregar(page, "f4p.xlsx")
    sem = page.evaluate("semestre(TODAY)")
    page.evaluate("()=>{ CFG.anTag = 'CAPACIDADE'; }")
    _setup_epico(page, team="AN_CAP2", sem=sem, itens=[
        {"stName": "Backlog", "tags": ["CAPACIDADE"]},
        {"stName": "Backlog", "tags": ["ROADMAP"]},   # tag antiga: não conta mais
    ])
    d = page.evaluate("anData()")
    page.evaluate("()=>{ CFG.anTag = 'ROADMAP'; }")
    assert d["cap"] == 1

def test_linha_do_epico_mostra_quantidade_reservada(page):
    carregar(page, "f4p.xlsx")
    sem = page.evaluate("semestre(TODAY)")
    _setup_epico(page, team="AN_ROW", sem=sem, itens=[
        {"stName": "Backlog", "tags": ["ROADMAP"]},
        {"stName": "WIP", "tags": []},
    ])
    page.click("#anTab")
    txt = page.inner_text("#anBody")
    assert "1 reservado" in txt

def test_clique_na_capacidade_abre_lista_so_dos_itens_com_a_tag(page):
    carregar(page, "f4p.xlsx")
    sem = page.evaluate("semestre(TODAY)")
    _setup_epico(page, team="AN_CLK_CAP", sem=sem, itens=[
        {"stName": "Backlog", "tags": ["ROADMAP"]},
        {"stName": "WIP", "tags": []},
    ])
    page.click("#anTab")
    page.click('button[data-an-items="cap"]')
    assert page.is_visible("#f4pItemsBg")
    assert page.locator("#f4pItemsBody tbody tr").count() == 1
    assert "Backlog" in page.inner_text("#f4pItemsBody")

def test_clique_na_projetada_abre_lista_com_todos_os_itens(page):
    carregar(page, "f4p.xlsx")
    sem = page.evaluate("semestre(TODAY)")
    _setup_epico(page, team="AN_CLK_PROJ", sem=sem, itens=[
        {"stName": "Backlog"}, {"stName": "WIP"}, {"stName": "Vazao", "deploy": "2026-02-10"},
    ])
    page.click("#anTab")
    page.click('button[data-an-items="proj"]')
    assert page.is_visible("#f4pItemsBg")
    assert page.locator("#f4pItemsBody tbody tr").count() == 3
    assert "Vazão" in page.inner_text("#f4pItemsBody")   # situação segue catOf, igual ao Report F4P
    assert "10/02/2026" in page.inner_text("#f4pItemsBody")   # Vazão mostra a data de saída

def test_clique_no_item_do_modal_fecha_a_visao_analitica_e_navega(page):
    carregar(page, "f4p.xlsx")
    sem = page.evaluate("semestre(TODAY)")
    _setup_epico(page, team="AN_CLK_GO", sem=sem, itens=[{"stName": "Backlog"}])
    alvo_id = page.evaluate("() => [...S.model.ops.values()].find(o => o.team === 'AN_CLK_GO').id")
    page.click("#anTab")
    page.click('button[data-an-items="proj"]')
    assert page.is_visible("#f4pItemsBg")
    page.click(f'button[data-f4p-go="{alvo_id}"]')
    assert not page.is_visible("#f4pItemsBg")
    assert not page.is_visible("#anPanel.open")
    assert page.evaluate("document.getElementById('fBusca').value") == alvo_id

# Decisão 0028: a linha do épico não mostra mais "X US" (redundante com a coluna QTD); QTD e
# "reservado" da linha ficam clicáveis, abrindo a lista dos itens daquele épico especificamente
# (diferente dos números do cabeçalho, que somam todos os épicos da tabela).

def test_linha_nao_mostra_mais_o_badge_x_us(page):
    carregar(page, "f4p.xlsx")
    sem = page.evaluate("semestre(TODAY)")
    _setup_epico(page, team="AN_ROW9", sem=sem, itens=[{"stName": "Backlog"}, {"stName": "WIP"}])
    page.click("#anTab")
    assert "US" not in page.inner_text("#anBody")

def _setup_dois_epicos_mesmo_time(page, *, team, sem):
    """Um único time com dois épicos, cada um com seus próprios itens — usado para confirmar que o
    clique em QTD/reservado de uma linha não mistura itens do épico vizinho (mesmo time)."""
    page.evaluate("""(args)=>{
      const {team, sem} = args;
      S.model.teamFlow[team] = ["Backlog", "WIP", "Vazao"];
      CFG.flow[norm(team)] = {cat:{wip:"wip", vazao:"vazao"}, ct:[]};
      const mk = (id, stName, tags) => S.model.ops.set(id, {id, title:id, team, type:"User Story", stName, deploy:null, ready:null, tags: tags || []});
      mk(team+"_e1_op0", "Backlog", ["ROADMAP"]); mk(team+"_e1_op1", "WIP", []);
      mk(team+"_e2_op0", "Backlog", ["ROADMAP"]);
      S.model.inis.set("INI_"+team, {id:"INI_"+team, valid:true, title:"Iniciativa", exec:sem, owner:null, rels:["REL_"+team]});
      S.model.rels.set("REL_"+team, {id:"REL_"+team, valid:true, title:"Release", parent:"INI_"+team, epis:["EPI1_"+team, "EPI2_"+team]});
      S.model.epis.set("EPI1_"+team, {id:"EPI1_"+team, valid:true, title:"Épico 1", parent:"REL_"+team, target:null, interno:null, st:0, ops:[team+"_e1_op0", team+"_e1_op1"], type:"Epic"});
      S.model.epis.set("EPI2_"+team, {id:"EPI2_"+team, valid:true, title:"Épico 2", parent:"REL_"+team, target:null, interno:null, st:0, ops:[team+"_e2_op0"], type:"Epic"});
      S.f.team = team; S.f.exec = sem;
      render();
    }""", {"team": team, "sem": sem})

def test_clique_no_qtd_da_linha_abre_so_os_itens_daquele_epico(page):
    carregar(page, "f4p.xlsx")
    sem = page.evaluate("semestre(TODAY)")
    _setup_dois_epicos_mesmo_time(page, team="AN_QTD", sem=sem)
    page.click("#anTab")
    page.click('button[data-an-epi="EPI1_AN_QTD"][data-an-epi-items="qtd"]')
    assert page.is_visible("#f4pItemsBg")
    ids = page.locator("#f4pItemsBody .idb").all_inner_texts()
    assert set(ids) == {"AN_QTD_e1_op0", "AN_QTD_e1_op1"}   # só os itens do Épico 1, não do Épico 2
    assert "Épico EPI1_AN_QTD" in page.inner_text("#f4pItemsTitle")

def test_clique_no_reservado_da_linha_abre_so_os_itens_reservados_daquele_epico(page):
    carregar(page, "f4p.xlsx")
    sem = page.evaluate("semestre(TODAY)")
    _setup_dois_epicos_mesmo_time(page, team="AN_RES", sem=sem)
    page.click("#anTab")
    page.click('button[data-an-epi="EPI1_AN_RES"][data-an-epi-items="res"]')
    assert page.is_visible("#f4pItemsBg")
    ids = page.locator("#f4pItemsBody .idb").all_inner_texts()
    assert set(ids) == {"AN_RES_e1_op0"}   # só o item com a tag, do Épico 1 (não o WIP do Épico 1 nem o do Épico 2)
    assert "Reservado" in page.inner_text("#f4pItemsTitle")

# Decisão 0029: a coluna Status ganha uma nova linha com o mesmo agrupador (Backlog/Discovery/WIP/
# Vazão, com quadradinho colorido e contagem) já usado no card do épico no quadro — reaproveitando
# `distGroup(m)` (extraído do card do épico, src/js/06-renderizacao.js, para src/js/
# 05-estado-e-calculos.js) em vez de duplicar a lógica de contagem por categoria.

def test_status_mostra_o_agrupador_por_categoria_do_card_do_epico(page):
    carregar(page, "f4p.xlsx")
    sem = page.evaluate("semestre(TODAY)")
    _setup_epico(page, team="AN_DIST", sem=sem, itens=[
        {"stName": "Backlog"}, {"stName": "Backlog"},
        {"stName": "WIP"},
        {"stName": "Vazao", "deploy": "2026-01-05"}, {"stName": "Vazao", "deploy": "2026-01-06"}, {"stName": "Vazao", "deploy": "2026-01-07"},
    ])
    page.click("#anTab")
    txt = page.inner_text("#anBody")
    assert "Backlog 2" in txt
    assert "Discovery 0" in txt   # mostra a categoria mesmo com contagem zero, igual ao card do épico
    assert "WIP 1" in txt
    assert "Vazão 3" in txt

def _setup_epico_orfao(page, *, team, sem, itens):
    """Épico sem release/iniciativa (valid:false), com itens do time e Target Date no semestre dado
    — usado para testar a inclusão desses épicos na Visão analítica quando filtrando por roadmap
    interno (decisão 0036)."""
    page.evaluate("""(args)=>{
      const {team, itens, sem} = args;
      S.model.teamFlow[team] = ["Backlog", "WIP", "Vazao"];
      CFG.flow[norm(team)] = {cat:{wip:"wip", vazao:"vazao"}, ct:[]};
      const opKeys = itens.map((it, idx) => {
        const k = `${team}_op${idx}`;
        S.model.ops.set(k, {id:k, title:"Item "+idx, team, type:"User Story", stName: it.stName, deploy: it.deploy ? new Date(it.deploy) : null,
          ready: it.stName !== "Backlog" ? new Date(2026,0,1) : null, tags: it.tags || []});
        return k;
      });
      const epiId = `EPIORFAO_${team}`;
      S.model.epis.set(epiId, {id:epiId, valid:false, title:"Épico órfão "+team, parent:null, target:null, interno:sem, st:0, ops:opKeys, type:"Epic"});
      S.f.team = team; S.f.int = sem; S.f.exec = "";
      render();
    }""", {"team": team, "itens": itens, "sem": sem})

def test_epico_orfao_aparece_no_roadmap_interno_com_aviso(page):
    """Decisão 0036: um épico sem release/iniciativa vinculada, mas com itens do time e Target Date
    no semestre do roadmap interno filtrado, aparece na Visão analítica com o aviso
    "OBS: SEM INICIATIVA e SEM RELEASE", em vez de simplesmente sumir do relatório."""
    carregar(page, "f4p.xlsx")
    sem = page.evaluate("semestre(TODAY)")
    _setup_epico_orfao(page, team="AN_ORFAO", sem=sem, itens=[{"stName": "Backlog"}, {"stName": "WIP"}])
    d = page.evaluate("anData()")
    assert d["proj"] == 2
    assert any(row["orphan"] for row in d["rows"])
    page.click("#anTab")
    assert "OBS: SEM INICIATIVA e SEM RELEASE" in page.inner_text("#anBody")

def test_epico_orfao_nao_aparece_no_roadmap_executivo(page):
    """O aviso só faz sentido para o roadmap interno (o épico não tem iniciativa pra herdar um
    roadmap executivo) — filtrando só por executivo, o épico órfão continua fora, como antes."""
    carregar(page, "f4p.xlsx")
    sem = page.evaluate("semestre(TODAY)")
    page.evaluate("""(args)=>{
      const {team, sem} = args;
      S.model.teamFlow[team] = ["Backlog", "WIP", "Vazao"];
      CFG.flow[norm(team)] = {cat:{wip:"wip", vazao:"vazao"}, ct:[]};
      S.model.ops.set(team+"_op0", {id:team+"_op0", title:"Item", team, type:"User Story", stName:"Backlog", deploy:null, ready:null, tags:[]});
      S.model.epis.set("EPIORFAO2_"+team, {id:"EPIORFAO2_"+team, valid:false, title:"Épico órfão", parent:null, target:null, interno:sem, st:0, ops:[team+"_op0"], type:"Epic"});
      S.f.team = team; S.f.exec = sem; S.f.int = "";
      render();
    }""", {"team": "AN_ORFAO2", "sem": sem})
    d = page.evaluate("anData()")
    assert d["rows"] == []

def test_status_agrupador_conta_so_os_itens_do_time_filtrado(page):
    """epiMetrics(e, team) já filtra por time (mesma fonte usada pelo QTD/Capacidade/Projetada), então
    o agrupador da coluna Status só conta os itens do time em análise, não os de outros times."""
    carregar(page, "f4p.xlsx")
    sem = page.evaluate("semestre(TODAY)")
    page.evaluate("""(sem)=>{
      S.model.teamFlow.AN_DIST_A = ["Backlog", "WIP", "Vazao"];
      S.model.teamFlow.AN_DIST_B = ["Backlog", "WIP", "Vazao"];
      CFG.flow.an_dist_a = {cat:{wip:"wip", vazao:"vazao"}, ct:[]};
      CFG.flow.an_dist_b = {cat:{wip:"wip", vazao:"vazao"}, ct:[]};
      S.model.ops.set("da1", {id:"da1", title:"A1", team:"AN_DIST_A", type:"User Story", stName:"WIP", deploy:null, ready:null, tags:[]});
      S.model.ops.set("db1", {id:"db1", title:"B1", team:"AN_DIST_B", type:"User Story", stName:"Vazao", deploy:new Date(2026,0,5), ready:new Date(2026,0,1), tags:[]});
      S.model.inis.set("INI_D", {id:"INI_D", valid:true, title:"Iniciativa", exec:sem, owner:null, rels:["REL_D"]});
      S.model.rels.set("REL_D", {id:"REL_D", valid:true, title:"Release", parent:"INI_D", epis:["EPI_D"]});
      S.model.epis.set("EPI_D", {id:"EPI_D", valid:true, title:"Épico compartilhado", parent:"REL_D", target:null, interno:null, st:0, ops:["da1", "db1"], type:"Epic"});
      S.f.team = "AN_DIST_A"; S.f.exec = sem;
      render();
    }""", sem)
    page.click("#anTab")
    txt = page.inner_text("#anBody")
    assert "WIP 1" in txt
    assert "Vazão 0" in txt   # o item Vazão é do outro time (AN_DIST_B): não entra na contagem do AN_DIST_A

# Decisão 0049. A fase/coluna mostradas na coluna Status passaram a considerar só os itens com a tag de
# capacidade (Reserva) — antes olhavam qualquer item vinculado ao épico pelo time, o que podia mostrar
# "WIP" (de um item fora da reserva) enquanto o item de fato reservado ainda estava em Discovery/Backlog,
# levando o usuário a achar que o trabalho reservado já estava andando. O agrupador por categoria
# (Backlog/Discovery/WIP/Vazão, logo abaixo) continua somando todos os itens, com ou sem a tag.

def test_status_usa_so_o_item_reservado_mais_avancado_nao_qualquer_item_do_time(page):
    carregar(page, "f4p.xlsx")
    sem = page.evaluate("semestre(TODAY)")
    _setup_epico(page, team="AN_ST_RES", sem=sem, itens=[
        {"stName": "Backlog", "tags": ["ROADMAP"]},   # reservado: é este que deve valer no Status
        {"stName": "WIP"},                            # não reservado, mais avançado — não deve valer
    ])
    d = page.evaluate("anData()")
    row = d["rows"][0]
    assert row["reservaPhase"] == "backlog"
    assert row["farName"] == "Backlog"
    page.click("#anTab")
    assert "WIP 1" in page.inner_text("#anBody table tbody tr td:nth-child(3)")   # agrupador ainda conta o não reservado

def test_status_mostra_sem_reserva_quando_nenhum_item_tem_a_tag(page):
    carregar(page, "f4p.xlsx")
    sem = page.evaluate("semestre(TODAY)")
    _setup_epico(page, team="AN_ST_NORES", sem=sem, itens=[{"stName": "WIP"}])   # item existe, mas sem a tag
    d = page.evaluate("anData()")
    assert d["rows"][0]["reservaPhase"] == "vazio"
    page.click("#anTab")
    row_txt = page.inner_text("#anBody table tbody tr td:nth-child(3)")
    assert "Sem reserva" in row_txt
    assert "WIP 1" in row_txt   # o agrupador continua contando o item, só a fase muda

def test_status_mostra_entregue_quando_so_os_reservados_ja_estao_em_vazao(page):
    """O inverso do caso acima: se TODOS os itens reservados já estão em Vazão, o Status mostra
    "Entregue" mesmo que exista um item não reservado ainda aberto (que só aparece no agrupador)."""
    carregar(page, "f4p.xlsx")
    sem = page.evaluate("semestre(TODAY)")
    _setup_epico(page, team="AN_ST_ENT", sem=sem, itens=[
        {"stName": "Vazao", "deploy": "2026-01-05", "tags": ["ROADMAP"]},
        {"stName": "Backlog"},   # não reservado, ainda aberto — não deve impedir o "Entregue"
    ])
    d = page.evaluate("anData()")
    assert d["rows"][0]["reservaPhase"] == "fechado"
    page.click("#anTab")
    row_txt = page.inner_text("#anBody table tbody tr td:nth-child(3)")
    assert "Entregue" in row_txt
    assert "Backlog 1" in row_txt

def test_status_ordena_pela_fase_da_reserva_nao_pela_fase_de_todos_os_itens(page):
    """anSorted ordena a coluna Status pela mesma fase agora exibida (reservaPhase) — um épico cuja
    fase "de todos os itens" seria WIP, mas cuja Reserva está só em Backlog, ordena como Backlog."""
    carregar(page, "f4p.xlsx")
    sem = page.evaluate("semestre(TODAY)")
    _setup_epico(page, team="AN_ST_SORT", sem=sem, itens=[
        {"stName": "Backlog", "tags": ["ROADMAP"]},   # reservado: fase real é Backlog
        {"stName": "WIP"},                            # não reservado: não deve valer pro sort
    ])
    r = page.evaluate("""()=>{
      AN.sort = "status"; AN.dir = 1;
      const d = anData();
      return anSorted(d.rows).map(row => row.reservaPhase);
    }""")
    assert r == ["backlog"]

def test_status_ordena_entregue_primeiro_depois_wip_discovery_backlog_e_sem_reserva_por_ultimo(page):
    """Decisão 0053: pedido do usuário para priorizar visualmente os épicos com trabalho mais adiantado
    — a ordem padrão (AN.dir = 1, coluna Status) passa a ser Entregue, WIP, Discovery, Backlog e por
    último Sem reserva, em vez da ordem antiga (WIP, Discovery, Backlog, Sem reserva, Entregue)."""
    carregar(page, "f4p.xlsx")
    sem = page.evaluate("semestre(TODAY)")
    r = page.evaluate("""(sem)=>{
      const team = "AN_ST_ORDEM";
      S.model.teamFlow[team] = ["Backlog", "Discovery", "WIP", "Vazao"];
      CFG.flow[norm(team)] = {cat:{discovery:"disc", wip:"wip", vazao:"vazao"}, ct:[]};
      const fases = [
        {sufixo:"backlog", itens:[{stName:"Backlog", tags:["ROADMAP"]}]},
        {sufixo:"vazio", itens:[{stName:"Backlog", tags:[]}]},
        {sufixo:"discovery", itens:[{stName:"Discovery", tags:["ROADMAP"]}]},
        {sufixo:"fechado", itens:[{stName:"Vazao", deploy:new Date(2026,0,5), tags:["ROADMAP"]}]},
        {sufixo:"wip", itens:[{stName:"WIP", tags:["ROADMAP"]}]},
      ];
      fases.forEach(f => {
        const iniId = `INI_ORD_${f.sufixo}`, relId = `REL_ORD_${f.sufixo}`, epiId = `EPI_ORD_${f.sufixo}`;
        const opKeys = f.itens.map((it, idx) => {
          const k = `${team}_${f.sufixo}_op${idx}`;
          S.model.ops.set(k, {id:k, title:"Item", team, type:"User Story", stName: it.stName, deploy: it.deploy || null,
            ready: it.stName !== "Backlog" ? new Date(2026,0,1) : null, tags: it.tags || []});
          return k;
        });
        S.model.inis.set(iniId, {id:iniId, valid:true, title:"Ini", exec:sem, owner:null, rels:[relId]});
        S.model.rels.set(relId, {id:relId, valid:true, title:"Rel", parent:iniId, epis:[epiId]});
        S.model.epis.set(epiId, {id:epiId, valid:true, title:"Epi "+f.sufixo, parent:relId, target:null, interno:null, st:0, ops:opKeys, type:"Epic"});
      });
      S.f.team = team; S.f.exec = sem;
      render();
      AN.sort = "status"; AN.dir = 1;
      const d = anData();
      return anSorted(d.rows).map(row => row.reservaPhase);
    }""", sem)
    assert r == ["fechado", "wip", "discovery", "backlog", "vazio"]

def test_id_ou_descricao_nao_filtra_epicos_so_destaca_a_linha_correspondente(page):
    """Decisão 0054: pedido do usuário — a Visão analítica (assim como o Report F4P e o Actionable) só
    deve filtrar por roadmap (interno ou executivo), time ou responsável; o campo "ID ou descrição"
    (S.f.q) não deve reduzir a lista de épicos aqui, só destacar (hl) a linha correspondente."""
    carregar(page, "f4p.xlsx")
    sem = page.evaluate("semestre(TODAY)")
    r = page.evaluate("""(sem)=>{
      const team = "AN_Q1";
      S.model.teamFlow[team] = ["Backlog", "Vazao"];
      CFG.flow[norm(team)] = {cat:{vazao:"vazao"}, ct:[]};
      ["a", "b"].forEach(suf => {
        const iniId = `INI_Q_${suf}`, relId = `REL_Q_${suf}`, epiId = `EPI_Q_${suf}`, opId = `${team}_op_${suf}`;
        S.model.ops.set(opId, {id:opId, title:"Item "+suf, team, type:"User Story", stName:"Backlog", deploy:null, ready:null, tags:[]});
        S.model.inis.set(iniId, {id:iniId, valid:true, title:"Ini "+suf, exec:sem, owner:null, rels:[relId]});
        S.model.rels.set(relId, {id:relId, valid:true, title:"Rel "+suf, parent:iniId, epis:[epiId]});
        S.model.epis.set(epiId, {id:epiId, valid:true, title:"Epico "+suf, parent:relId, target:null, interno:null, st:0, ops:[opId], type:"Epic"});
      });
      S.f.team = team; S.f.exec = sem; S.f.q = "";
      render();
      const semQ = anData().rows.length;
      S.f.q = "EPI_Q_a";
      render();
      const d = anData();
      return {semQ, comQ: d.rows.length, hl: d.rows.map(row => ({id: row.e.id, hl: row.hl}))};
    }""", sem)
    assert r["semQ"] == 2
    assert r["comQ"] == 2   # continua mostrando os dois épicos, não filtra
    hl_map = {x["id"]: x["hl"] for x in r["hl"]}
    assert hl_map["EPI_Q_a"] is True
    assert hl_map["EPI_Q_b"] is False

def test_id_de_item_do_time_tambem_destaca_o_epico_pai(page):
    """O destaque (decisão 0054) reaproveita o mesmo alcance do filtro q do quadro: bater com o ID de um
    item de time vinculado ao épico também destaca a linha do épico, não só um match direto no próprio
    épico/iniciativa."""
    carregar(page, "f4p.xlsx")
    sem = page.evaluate("semestre(TODAY)")
    r = page.evaluate("""(sem)=>{
      const team = "AN_Q2";
      S.model.teamFlow[team] = ["Backlog", "Vazao"];
      CFG.flow[norm(team)] = {cat:{vazao:"vazao"}, ct:[]};
      S.model.ops.set("AN_Q2_item", {id:"AN_Q2_item", title:"Item do time", team, type:"User Story", stName:"Backlog", deploy:null, ready:null, tags:[]});
      S.model.inis.set("INI_Q2", {id:"INI_Q2", valid:true, title:"Ini", exec:sem, owner:null, rels:["REL_Q2"]});
      S.model.rels.set("REL_Q2", {id:"REL_Q2", valid:true, title:"Rel", parent:"INI_Q2", epis:["EPI_Q2"]});
      S.model.epis.set("EPI_Q2", {id:"EPI_Q2", valid:true, title:"Epico", parent:"REL_Q2", target:null, interno:null, st:0, ops:["AN_Q2_item"], type:"Epic"});
      S.f.team = team; S.f.exec = sem; S.f.q = "AN_Q2_item";
      render();
      return anData().rows.map(row => ({id: row.e.id, hl: row.hl}));
    }""", sem)
    assert r == [{"id": "EPI_Q2", "hl": True}]

def test_filtro_responsavel_utilizavel_com_o_painel_aberto(page):
    """Bug relatado pelo usuário: com o painel da Visão analítica aberto, o filtro "Time" e "Roadmap
    interno" (campos <select> nativos) funcionavam, mas "Responsável da iniciativa" (popup próprio,
    #msPop) não — o painel (#anPanel, z-index 46) ficava por cima do popup (que herdava o z-index 45
    de dentro de .top, cuja própria pilha de empilhamento ficava abaixo do painel), bloqueando o clique
    nas opções. Um <select> nativo não sofre disso (o navegador sempre desenha por cima)."""
    carregar(page, "f4p.xlsx")
    page.evaluate("()=>{ S.f.team=S.model.teams[0]; S.f.exec=semestre(TODAY); render(); }")
    page.click("#anTab")
    assert page.evaluate("AN.open") is True
    page.click("#fOwner")
    page.click("#msList .ms-item >> nth=0")   # falha (timeout) se o painel intercepta o clique
    assert page.evaluate("S.f.owners.size") == 1
