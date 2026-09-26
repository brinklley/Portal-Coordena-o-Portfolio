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
