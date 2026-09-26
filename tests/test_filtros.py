"""Filtros, busca por ID e diagnósticos (docs/telas.md)."""
from conftest import carregar

def test_responsaveis_busca_em_qualquer_parte_do_nome(page):
    carregar(page, "responsaveis.xlsx")
    page.click("#fOwner"); page.fill("#msSearch", "conceicao")        # sem acento, no meio do nome
    visiveis = page.evaluate("[...document.querySelectorAll('#msList .ms-item .nm')].map(x=>x.textContent)")
    assert visiveis and all("Conceição" in n for n in visiveis)
    page.click("#msAll"); page.mouse.click(700, 700); page.wait_for_timeout(300)
    assert page.evaluate("S.f.owners.size") == len(visiveis)

def test_ir_para_id_aponta_o_filtro_que_esconde(page):
    carregar(page, "responsaveis.xlsx")
    page.click("#fOwner"); page.fill("#msSearch", "guzzo"); page.click("#msAll"); page.mouse.click(700, 700); page.wait_for_timeout(300)
    alvo = page.evaluate("[...S.model.inis.values()].find(i=>i.owner && !/guzzo/i.test(i.owner)).id")
    page.fill("#goto", alvo); page.press("#goto", "Enter"); page.wait_for_timeout(300)
    msg = page.inner_text("#fmsg")
    assert "Responsável da iniciativa" in msg
    page.click("#fmGo"); page.wait_for_timeout(500)
    assert page.evaluate("S.path.ini") == alvo and page.evaluate("activeFilters().length") == 0

def test_diagnostico_quando_o_filtro_zera_o_quadro(page):
    carregar(page, "responsaveis.xlsx")
    page.fill("#fIni", "texto que nao existe"); page.wait_for_timeout(700)
    assert "Nenhuma iniciativa tem" in page.inner_text(".empty-state")
