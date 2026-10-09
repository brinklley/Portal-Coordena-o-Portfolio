"""Board de Iniciativas: recolher/manter visíveis com o foco na selecionada (docs/telas.md,
docs/decisoes/0021-manter-iniciativas-visiveis.md)."""
from conftest import carregar

def test_selecionar_recolhe_as_demais_por_padrao(page):
    carregar(page, "responsaveis.xlsx")   # 300 iniciativas
    assert not page.is_checked("#fShowAllIni")
    page.click("#lane-ini .card.lvl-ini >> nth=0")
    page.wait_for_timeout(200)
    assert page.locator("#lane-ini .card.lvl-ini").count() == 1
    assert "mostrando só a selecionada" in page.inner_text("#lane-ini .ctx")

def test_manter_todas_visiveis_mostra_todas_com_foco_na_selecionada(page):
    carregar(page, "responsaveis.xlsx")
    primeiro = page.locator("#lane-ini .card.lvl-ini").nth(0)
    alvo_key = primeiro.get_attribute("data-key")
    primeiro.click()
    page.check("#fShowAllIni")
    page.wait_for_timeout(200)
    n_total = page.evaluate("S.V.visIni.size")
    assert page.locator("#lane-ini .card.lvl-ini").count() == n_total
    assert page.locator("#lane-ini .card.lvl-ini.sel").count() == 1
    assert page.locator(f'#lane-ini .card.lvl-ini.sel[data-key="{alvo_key}"]').count() == 1
    assert page.locator("#lane-ini .card.lvl-ini.dim").count() == n_total - 1
    assert "mostrando todas" in page.inner_text("#lane-ini .ctx")

def test_selecionar_outra_iniciativa_mantem_o_checkbox_marcado(page):
    """Diferente do comportamento antigo do link "Mostrar todas": trocar de iniciativa selecionada
    não deve recolher a lista de novo — o checkbox é uma preferência, não um estado por seleção."""
    carregar(page, "responsaveis.xlsx")
    page.locator("#lane-ini .card.lvl-ini").nth(0).click()
    page.check("#fShowAllIni")
    page.wait_for_timeout(200)
    segundo = page.locator("#lane-ini .card.lvl-ini").nth(1)
    segundo_key = segundo.get_attribute("data-key")
    segundo.click()
    page.wait_for_timeout(200)
    assert page.is_checked("#fShowAllIni")
    n_total = page.evaluate("S.V.visIni.size")
    assert page.locator("#lane-ini .card.lvl-ini").count() == n_total
    assert page.locator(f'#lane-ini .card.lvl-ini.sel[data-key="{segundo_key}"]').count() == 1
    assert page.locator("#lane-ini .card.lvl-ini.dim").count() == n_total - 1

def test_desmarcar_volta_a_recolher(page):
    carregar(page, "responsaveis.xlsx")
    page.click("#lane-ini .card.lvl-ini >> nth=0")
    page.check("#fShowAllIni"); page.wait_for_timeout(200)
    page.uncheck("#fShowAllIni"); page.wait_for_timeout(200)
    assert page.locator("#lane-ini .card.lvl-ini").count() == 1
    assert page.locator("#lane-ini .card.lvl-ini.dim").count() == 0

def test_limpar_selecao_nao_desliga_a_preferencia(page):
    carregar(page, "responsaveis.xlsx")
    page.click("#lane-ini .card.lvl-ini >> nth=0")
    page.check("#fShowAllIni"); page.wait_for_timeout(200)
    page.click("#btnClear"); page.wait_for_timeout(200)
    assert page.is_checked("#fShowAllIni")

def test_investigacao_de_item_recolhido_orienta_o_checkbox(page):
    carregar(page, "responsaveis.xlsx")
    ids = page.evaluate("[...S.model.inis.values()].slice(0,2).map(i=>i.id)")
    page.evaluate("id => { S.path = {ini:id}; render(); }", ids[0])
    passos = page.evaluate("id => investigate(id).map(s=>[s.ok, s.title, s.action])", ids[1])
    assert [False, "Recolhido na lista"] in [[p[0], p[1]] for p in passos]
    acao = next(p[2] for p in passos if p[1] == "Recolhido na lista")
    assert "Manter todas as iniciativas visíveis" in acao

def _habilitar_painel(page, *, team, sem):
    """Monta uma cadeia sintética mínima (1 iniciativa com 1 card) e habilita Time + Roadmap
    executivo, suficiente para abrir Visão Analítica/Report F4P/Actionable e ter um card real no
    quadro para clicar."""
    page.evaluate("""(args)=>{
      const {team, sem} = args;
      S.model.teamFlow[team] = ["Backlog", "WIP", "Vazao"];
      CFG.flow[norm(team)] = {cat:{wip:"wip", vazao:"vazao"}, ct:[]};
      S.model.ops.set(team+"_op0", {id:team+"_op0", title:"Item", team, type:"User Story", stName:"WIP", deploy:null, ready:new Date(2026,0,1), tags:[]});
      S.model.inis.set("INI_"+team, {lvl:"ini", id:"INI_"+team, valid:true, title:"Iniciativa "+team, exec:sem, owner:null, st:0, rels:["REL_"+team]});
      S.model.rels.set("REL_"+team, {lvl:"rel", id:"REL_"+team, valid:true, title:"Release", parent:"INI_"+team, st:0, epis:["EPI_"+team]});
      S.model.epis.set("EPI_"+team, {lvl:"epi", id:"EPI_"+team, valid:true, title:"Épico", parent:"REL_"+team, target:null, interno:null, st:0, ops:[team+"_op0"], type:"Epic"});
      S.f.team = team; S.f.exec = sem;
      render();
    }""", {"team": team, "sem": sem})

def test_clicar_no_whiteboard_fecha_o_painel_lateral_aberto(page):
    """Melhoria sugerida pelo usuário: com a Visão Analítica (ou Report F4P/Actionable) aberta, clicar
    em qualquer lugar do quadro — fora do painel — fecha o painel, sem precisar ir até o botão "«"."""
    carregar(page, "f4p.xlsx")
    sem = page.evaluate("semestre(TODAY)")
    _habilitar_painel(page, team="QCLICK1", sem=sem)
    page.click("#anTab")
    assert page.evaluate("AN.open") is True
    # clique num ponto do whiteboard fora da faixa ocupada pelo painel (min(1180px, 96vw) de largura,
    # com o viewport padrão de 1500px dos testes — ver tests/conftest.py)
    page.mouse.click(1300, 700)
    page.wait_for_timeout(200)
    assert page.evaluate("AN.open") is False

def test_clicar_num_card_fecha_o_painel_mas_mantem_o_comportamento_normal_do_clique(page):
    """O card continua funcionando normalmente (seleciona a iniciativa) — fechar o painel é um efeito
    a mais do clique, não uma substituição do comportamento existente."""
    carregar(page, "f4p.xlsx")
    sem = page.evaluate("semestre(TODAY)")
    _habilitar_painel(page, team="QCLICK2", sem=sem)
    page.click("#f4pTab")
    assert page.evaluate("F4P.open") is True
    # clique real de DOM no primeiro card — o card renderizado fica atrás do painel aberto (que ocupa
    # a maior parte da largura no viewport de teste), então um clique "visível" do Playwright falharia
    # por obstrução; o .click() nativo dispara o mesmo evento que um clique de usuário, borbulhando
    # pelos mesmos listeners.
    page.evaluate("document.querySelector('.card').click()")
    page.wait_for_timeout(200)
    assert page.evaluate("F4P.open") is False
    assert page.evaluate("S.path.ini") == "INI_QCLICK2"

def test_arrastar_o_quadro_nao_fecha_o_painel(page):
    """Arrastar o quadro para outra posição (pan) não deve fechar o painel aberto — só um clique de
    verdade, sem deslocamento, conta como "clicar fora"."""
    carregar(page, "f4p.xlsx")
    sem = page.evaluate("semestre(TODAY)")
    _habilitar_painel(page, team="QCLICK3", sem=sem)
    page.click("#actTab")
    assert page.evaluate("ACT.open") is True
    page.mouse.move(1300, 700)
    page.mouse.down()
    page.mouse.move(1250, 650, steps=10)
    page.mouse.move(1200, 600, steps=10)
    page.mouse.up()
    page.wait_for_timeout(200)
    assert page.evaluate("ACT.open") is True
    # mas um clique simples (sem arrastar) logo em seguida já fecha normalmente
    page.mouse.click(1300, 700)
    page.wait_for_timeout(200)
    assert page.evaluate("ACT.open") is False
