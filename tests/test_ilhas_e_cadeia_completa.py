"""Whiteboard da cadeia completa: ilhas soltas manualmente (docs/telas.md, "Ancorar/soltar ilhas")."""
from conftest import carregar

def _abrir_cadeia_completa(page):
    ini_id = page.evaluate("[...S.model.inis.values()].find(i => i.valid && i.rels.length).id")
    page.click(f'#lane-ini .card[data-key="ini:{ini_id}"]')
    page.wait_for_timeout(200)
    page.click("#btnExpand")
    page.wait_for_timeout(300)
    return ini_id

def test_offset_de_ilha_solta_e_descartado_quando_o_filtro_muda(page):
    """Bug relatado pelo usuário: o board "Operacional dos times" aparecia por cima dos boards de
    Iniciativa/Release/Épico. Causa: soltar uma ilha (desmarcar "Ilhas ancoradas" e arrastar) grava um
    deslocamento fixo em pixels (S.offsets) a partir da posição natural da ilha no momento do arrasto —
    e esse deslocamento nunca era descartado quando um filtro muda o que aparece acima dela (outro
    time, outra busca), deixando a ilha visualmente fora do lugar, podendo sobrepor o conteúdo novo."""
    carregar(page, "times.xlsx")
    _abrir_cadeia_completa(page)
    page.evaluate("""()=>{ S.anchored = false; applyOffsets(); S.offsets['isl:MOBILE'] = {x:0, y:-1300}; applyOffsets(); redraw(); }""")
    assert page.evaluate("Object.keys(S.offsets).length") == 1
    page.select_option("#fTeam", "MOBILE")
    page.wait_for_timeout(300)
    assert page.evaluate("Object.keys(S.offsets).length") == 0

def test_offset_de_ilha_solta_e_descartado_ao_trocar_de_iniciativa(page):
    """Mesma correção: navegar para outra iniciativa (voltar à raiz e escolher outra) também descarta
    os deslocamentos manuais — eles só fazem sentido para a cadeia que estava sendo vista quando a
    ilha foi arrastada."""
    carregar(page, "responsaveis.xlsx")   # várias iniciativas com release, diferente de times.xlsx (só 1)
    ini1 = _abrir_cadeia_completa(page)
    page.evaluate("""()=>{ S.anchored = false; applyOffsets(); S.offsets['isl:MOBILE'] = {x:0, y:-900}; applyOffsets(); redraw(); }""")
    assert page.evaluate("Object.keys(S.offsets).length") == 1
    ini2 = page.evaluate(f"[...S.model.inis.values()].find(i => i.valid && i.rels.length && i.id !== {ini1!r}).id")
    page.evaluate("()=>{ S.path = {}; S.expand = false; render(); }")
    page.wait_for_timeout(200)
    page.click(f'#lane-ini .card[data-key="ini:{ini2}"]')
    page.wait_for_timeout(200)
    assert page.evaluate("Object.keys(S.offsets).length") == 0

def test_offset_de_ilha_solta_persiste_entre_renders_sem_mudanca_de_contexto(page):
    """O descarte é específico de mudanças que afetam o que aparece (filtro, busca, iniciativa) — um
    re-render sem nenhuma dessas mudanças (ex.: alternar "Mostrar etapas vazias") não apaga a posição
    que o usuário arrastou de propósito."""
    carregar(page, "times.xlsx")
    _abrir_cadeia_completa(page)
    page.evaluate("""()=>{ S.anchored = false; applyOffsets(); S.offsets['isl:MOBILE'] = {x:5, y:5}; applyOffsets(); redraw(); }""")
    assert page.evaluate("Object.keys(S.offsets).length") == 1
    page.uncheck("#fEmpty")
    page.wait_for_timeout(200)
    assert page.evaluate("Object.keys(S.offsets).length") == 1
    assert page.evaluate("S.offsets['isl:MOBILE']") == {"x": 5, "y": 5}
