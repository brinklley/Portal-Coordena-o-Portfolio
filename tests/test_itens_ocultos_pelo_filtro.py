""""+N ocultos" no quadro (docs/regras-de-negocio.md §3, decisão 0050): quando um filtro ativo esconde
irmãos de Iniciativa/Release/Épico, um botão minimalista no cabeçalho da faixa avisa quantos e permite
revelá-los esmaecidos (.dim), sem precisar limpar o filtro para saber que eles existem."""
from conftest import carregar

def _setup_epico_dividido(page, *, team_visivel="TIME_A", team_oculto="TIME_B"):
    """1 iniciativa → 1 release → 2 épicos: um com item do `team_visivel`, outro só com item do
    `team_oculto`. Filtrando por `team_visivel`, o 2º épico fica de fora de V.visEpi (não tem nenhum
    item do time filtrado) — mas segue existindo no modelo (`r.epis`), então some do quadro só por
    causa do filtro, o cenário que o toggle "+N ocultos" existe para cobrir."""
    page.evaluate("""(args)=>{
      const {teamVisivel, teamOculto} = args;
      S.model.inis.set("INI_H", {lvl:"ini", id:"INI_H", valid:true, title:"Iniciativa Teste", exec:"2026 2", owner:null, rels:["REL_H"]});
      S.model.rels.set("REL_H", {lvl:"rel", id:"REL_H", valid:true, title:"Release Teste", parent:"INI_H", st:0, epis:["EPI_H1","EPI_H2"]});
      S.model.epis.set("EPI_H1", {lvl:"epi", id:"EPI_H1", valid:true, title:"Épico Visível", parent:"REL_H", target:null, interno:null, st:0, ops:["oph1"], type:"Epic"});
      S.model.epis.set("EPI_H2", {lvl:"epi", id:"EPI_H2", valid:true, title:"Épico Oculto", parent:"REL_H", target:null, interno:null, st:0, ops:["oph2"], type:"Epic"});
      S.model.ops.set("oph1", {id:"oph1", title:"Item A", team:teamVisivel, epicoId:"EPI_H1", type:"User Story", stName:"Backlog", deploy:null, tags:[]});
      S.model.ops.set("oph2", {id:"oph2", title:"Item B", team:teamOculto, epicoId:"EPI_H2", type:"User Story", stName:"Backlog", deploy:null, tags:[]});
      if (!S.model.teams.includes(teamVisivel)) S.model.teams.push(teamVisivel);
      if (!S.model.teams.includes(teamOculto)) S.model.teams.push(teamOculto);
      S.f.team = teamVisivel;
      S.path = {ini:"INI_H", rel:"REL_H"};
      render();
    }""", {"teamVisivel": team_visivel, "teamOculto": team_oculto})

def test_sem_filtro_ativo_nenhum_toggle_aparece(page):
    carregar(page, "f4p.xlsx")
    assert page.locator("[data-hide-toggle]").count() == 0

def test_toggle_aparece_e_revela_epico_oculto_pelo_filtro_de_time(page):
    carregar(page, "f4p.xlsx")
    _setup_epico_dividido(page)
    toggle = page.locator('#lane-epi [data-hide-toggle="epi"]')
    assert toggle.inner_text() == "+ 1 ocultos"
    assert page.locator("#lane-epi .card.lvl-epi").count() == 1   # só o visível, antes de revelar
    assert page.locator("#lane-epi .card.dim").count() == 0

    toggle.click()
    page.wait_for_timeout(150)
    assert toggle.inner_text() == "− 1 ocultos"
    assert page.locator("#lane-epi .card.lvl-epi").count() == 2   # visível + revelado
    dim = page.locator("#lane-epi .card.dim")
    assert dim.count() == 1
    assert dim.get_attribute("data-key") == "epi:EPI_H2"
    assert "Épico Oculto" in dim.inner_text()

    toggle.click()   # esconde de novo
    page.wait_for_timeout(150)
    assert toggle.inner_text() == "+ 1 ocultos"
    assert page.locator("#lane-epi .card.dim").count() == 0

def test_contagem_do_cabecalho_nao_conta_os_revelados(page):
    """O "1" ao lado de "Épicos" no cabeçalho da faixa é o total VISÍVEL (filtrado) — continua 1 mesmo
    com o oculto revelado, pra não sugerir que o filtro deixou de valer."""
    carregar(page, "f4p.xlsx")
    _setup_epico_dividido(page)
    page.click('#lane-epi [data-hide-toggle="epi"]')
    page.wait_for_timeout(150)
    assert page.inner_text("#lane-epi h2").strip().startswith("Épicos")
    assert page.evaluate("document.querySelector('#lane-epi h2 span:last-child').textContent.trim()") == "1"

def test_toggle_revela_release_oculta_pelo_filtro_de_time(page):
    """Mesmo mecanismo, um nível acima: uma release cujo único épico não tem item do time filtrado
    some da faixa de Releases, mas o toggle "+N ocultos" ali revela ela esmaecida."""
    carregar(page, "f4p.xlsx")
    page.evaluate("""()=>{
      S.model.inis.set("INI_R", {lvl:"ini", id:"INI_R", valid:true, title:"Iniciativa Teste", exec:"2026 2", owner:null, rels:["REL_RA","REL_RB"]});
      S.model.rels.set("REL_RA", {lvl:"rel", id:"REL_RA", valid:true, title:"Release Visível", parent:"INI_R", st:0, epis:["EPI_RA"]});
      S.model.rels.set("REL_RB", {lvl:"rel", id:"REL_RB", valid:true, title:"Release Oculta", parent:"INI_R", st:0, epis:["EPI_RB"]});
      S.model.epis.set("EPI_RA", {lvl:"epi", id:"EPI_RA", valid:true, title:"Épico A", parent:"REL_RA", target:null, interno:null, st:0, ops:["opra"], type:"Epic"});
      S.model.epis.set("EPI_RB", {lvl:"epi", id:"EPI_RB", valid:true, title:"Épico B", parent:"REL_RB", target:null, interno:null, st:0, ops:["oprb"], type:"Epic"});
      S.model.ops.set("opra", {id:"opra", title:"Item A", team:"TIME_A", epicoId:"EPI_RA", type:"User Story", stName:"Backlog", deploy:null, tags:[]});
      S.model.ops.set("oprb", {id:"oprb", title:"Item B", team:"TIME_B", epicoId:"EPI_RB", type:"User Story", stName:"Backlog", deploy:null, tags:[]});
      if (!S.model.teams.includes("TIME_A")) S.model.teams.push("TIME_A");
      if (!S.model.teams.includes("TIME_B")) S.model.teams.push("TIME_B");
      S.f.team = "TIME_A";
      S.path = {ini:"INI_R"};
      render();
    }""")
    toggle = page.locator('#lane-rel [data-hide-toggle="rel"]')
    assert toggle.inner_text() == "+ 1 ocultos"
    assert page.locator("#lane-rel .card.lvl-rel").count() == 1
    toggle.click()
    page.wait_for_timeout(150)
    assert page.locator("#lane-rel .card.lvl-rel").count() == 2
    dim = page.locator("#lane-rel .card.dim")
    assert dim.count() == 1
    assert dim.get_attribute("data-key") == "rel:REL_RB"

def test_toggle_revela_iniciativa_oculta_pelo_filtro_de_time(page):
    """No topo da hierarquia (sem "pai" — a faixa de Iniciativas é sempre uma lista única), o toggle
    cobre iniciativas inteiras escondidas pelo filtro atual."""
    carregar(page, "f4p.xlsx")
    page.evaluate("""()=>{
      S.model.inis.set("INI_IA", {lvl:"ini", id:"INI_IA", valid:true, title:"Iniciativa Visível", exec:"2026 2", owner:null, rels:["REL_IA"]});
      S.model.inis.set("INI_IB", {lvl:"ini", id:"INI_IB", valid:true, title:"Iniciativa Oculta", exec:"2026 2", owner:null, rels:["REL_IB"]});
      S.model.rels.set("REL_IA", {lvl:"rel", id:"REL_IA", valid:true, title:"Release A", parent:"INI_IA", st:0, epis:["EPI_IA"]});
      S.model.rels.set("REL_IB", {lvl:"rel", id:"REL_IB", valid:true, title:"Release B", parent:"INI_IB", st:0, epis:["EPI_IB"]});
      S.model.epis.set("EPI_IA", {lvl:"epi", id:"EPI_IA", valid:true, title:"Épico A", parent:"REL_IA", target:null, interno:null, st:0, ops:["opia"], type:"Epic"});
      S.model.epis.set("EPI_IB", {lvl:"epi", id:"EPI_IB", valid:true, title:"Épico B", parent:"REL_IB", target:null, interno:null, st:0, ops:["opib"], type:"Epic"});
      S.model.ops.set("opia", {id:"opia", title:"Item A", team:"TIME_A", epicoId:"EPI_IA", type:"User Story", stName:"Backlog", deploy:null, tags:[]});
      S.model.ops.set("opib", {id:"opib", title:"Item B", team:"TIME_B", epicoId:"EPI_IB", type:"User Story", stName:"Backlog", deploy:null, tags:[]});
      if (!S.model.teams.includes("TIME_A")) S.model.teams.push("TIME_A");
      if (!S.model.teams.includes("TIME_B")) S.model.teams.push("TIME_B");
      S.f.team = "TIME_A";
      render();
    }""")
    # a faixa de Iniciativas é global (sem "pai" só desta cadeia sintética), então o próprio fluxo
    # real do fixture pode ter outras iniciativas sem nenhum item de TIME_A — não fixamos a contagem
    # exata do toggle, só que a Iniciativa Oculta especificamente aparece esmaecida ao revelar.
    toggle = page.locator('#lane-ini [data-hide-toggle="ini"]')
    assert "ocultos" in toggle.inner_text()
    assert page.locator('#lane-ini .card[data-key="ini:INI_IB"]').count() == 0
    toggle.click()
    page.wait_for_timeout(150)
    dim = page.locator('#lane-ini .card.dim[data-key="ini:INI_IB"]')
    assert dim.count() == 1
    assert "Iniciativa Oculta" in dim.inner_text()

def test_toggle_nao_aparece_quando_nao_ha_nada_oculto_naquele_nivel(page):
    """O filtro pode estar ativo e ainda assim não esconder nada NESTA faixa específica — o toggle só
    aparece quando há de fato algo oculto ali, nunca "por via das dúvidas"."""
    carregar(page, "f4p.xlsx")
    page.evaluate("""()=>{
      S.model.inis.set("INI_S", {lvl:"ini", id:"INI_S", valid:true, title:"Iniciativa Só Um Time", exec:"2026 2", owner:null, rels:["REL_S"]});
      S.model.rels.set("REL_S", {lvl:"rel", id:"REL_S", valid:true, title:"Release Só Um Time", parent:"INI_S", st:0, epis:["EPI_S"]});
      S.model.epis.set("EPI_S", {lvl:"epi", id:"EPI_S", valid:true, title:"Épico Só Um Time", parent:"REL_S", target:null, interno:null, st:0, ops:["ops1"], type:"Epic"});
      S.model.ops.set("ops1", {id:"ops1", title:"Item", team:"TIME_A", epicoId:"EPI_S", type:"User Story", stName:"Backlog", deploy:null, tags:[]});
      if (!S.model.teams.includes("TIME_A")) S.model.teams.push("TIME_A");
      S.f.team = "TIME_A";
      S.path = {ini:"INI_S", rel:"REL_S"};
      render();
    }""")
    assert page.locator('#lane-rel [data-hide-toggle="rel"]').count() == 0
    assert page.locator('#lane-epi [data-hide-toggle="epi"]').count() == 0

def test_preferencia_de_revelar_fica_ligada_entre_navegacoes(page):
    """Mesmo padrão de #fShowAllIni: revelar os ocultos de um nível é uma preferência, não um estado
    ligado à release/época em foco no momento — muda de release e continua revelando, se a nova também
    tiver algo oculto."""
    carregar(page, "f4p.xlsx")
    page.evaluate("""()=>{
      S.model.inis.set("INI_P", {lvl:"ini", id:"INI_P", valid:true, title:"Ini", exec:"2026 2", owner:null, rels:["REL_P1","REL_P2"]});
      S.model.rels.set("REL_P1", {lvl:"rel", id:"REL_P1", valid:true, title:"Release 1", parent:"INI_P", st:0, epis:["EPI_P1A","EPI_P1B"]});
      S.model.rels.set("REL_P2", {lvl:"rel", id:"REL_P2", valid:true, title:"Release 2", parent:"INI_P", st:0, epis:["EPI_P2A","EPI_P2B"]});
      ["EPI_P1A","EPI_P1B","EPI_P2A","EPI_P2B"].forEach((id, i) => {
        S.model.epis.set(id, {lvl:"epi", id, valid:true, title:"Épico "+id, parent: i < 2 ? "REL_P1" : "REL_P2", target:null, interno:null, st:0, ops:["op_"+id], type:"Epic"});
        S.model.ops.set("op_"+id, {id:"op_"+id, title:"Item", team: i % 2 === 0 ? "TIME_A" : "TIME_B", epicoId:id, type:"User Story", stName:"Backlog", deploy:null, tags:[]});
      });
      if (!S.model.teams.includes("TIME_A")) S.model.teams.push("TIME_A");
      if (!S.model.teams.includes("TIME_B")) S.model.teams.push("TIME_B");
      S.f.team = "TIME_A";
      S.path = {ini:"INI_P", rel:"REL_P1"};
      render();
    }""")
    page.click('#lane-epi [data-hide-toggle="epi"]')
    page.wait_for_timeout(150)
    assert page.locator("#lane-epi .card.dim").count() == 1
    page.click('button.card.lvl-rel[data-key="rel:REL_P2"]')
    page.wait_for_timeout(150)
    assert page.evaluate("S.showHidden.epi") is True
    assert page.locator("#lane-epi .card.dim").count() == 1   # revelando de novo, sem precisar clicar

def test_card_oculto_revelado_abre_detalhes_em_vez_de_navegar(page):
    """Diferente de um card normal, clicar num card revelado (fora do filtro ativo) não tenta
    "entrar" nele — isso setaria S.path para um id fora de V, que o guard de render() descartaria de
    novo (o filtro continua excluindo esse item). Em vez disso, abre só o painel de detalhes."""
    carregar(page, "f4p.xlsx")
    _setup_epico_dividido(page)
    page.click('#lane-epi [data-hide-toggle="epi"]')
    page.wait_for_timeout(150)
    page.click('.card.lvl-epi.dim[data-key="epi:EPI_H2"]')
    page.wait_for_timeout(150)
    assert page.evaluate("S.path.epi") is None
    assert page.evaluate("S.detailKey") == "epi:EPI_H2"
    assert "with-drawer" in page.get_attribute("body", "class")
