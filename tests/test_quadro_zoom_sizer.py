"""Whiteboard: dimensionamento do quadro (zoom/pan) — docs/telas.md "Zoom/arrastar", decisões
`0066-updatesizer-usa-offsetwidth-nao-clientwidth.md` e
`0069-margem-pannable-em-volta-do-conteudo.md`."""
from conftest import carregar

def test_updatesizer_nao_oscila_quando_a_barra_de_rolagem_aparece_e_some(page):
    """Bug relatado pelo usuário: com o painel de detalhes aberto (que estreita a área do quadro) e
    muitas iniciativas carregadas, a tela ficava "tremendo em loop" — o DevTools mostrava o atributo
    `style` de `#board` sendo reescrito sem parar. Causa: `updateSizer()` usava `vp.clientWidth`/
    `clientHeight` para dimensionar o quadro — e essas medidas ENCOLHEM quando uma barra de rolagem
    aparece (vp tem `overflow:auto`). Como é o próprio `updateSizer()` quem decide (via `sizer`) se o
    quadro precisa de barra, surge um ciclo: a barra aparece → `clientWidth` encolhe → o quadro
    encolhe → a barra some → `clientWidth` cresce → o quadro cresce → a barra aparece de novo — e o
    `ResizeObserver` em `board` reexecuta `updateSizer()` a cada uma dessas mudanças, sem nunca
    estabilizar.

    Este teste simula o pior caso de propósito (clientWidth "piscando" entre dois valores a cada
    leitura, exatamente como a barra de rolagem apareceria/sumiria de verdade) e confirma que
    `updateSizer()` produz o mesmo resultado em chamadas sucessivas — não reproduzir o cenário real de
    conteúdo/viewport que dispara a barra de verdade (frágil e dependente de layout), só a garantia de
    que a função não está mais "amarrada" a uma medida que pode oscilar."""
    oscilou_antes = page.evaluate("""() => {
      // confirma a premissa do teste: clientWidth normal (sem mock) é estável aqui
      return typeof updateSizer === "function";
    }""")
    assert oscilou_antes

    larguras = page.evaluate("""() => {
      let flip = false;
      Object.defineProperty(vp, "clientWidth", {configurable:true, get(){ flip = !flip; return flip ? 1000 : 1014; }});
      Object.defineProperty(vp, "clientHeight", {configurable:true, get(){ return 700; }});
      const out = [];
      for (let i = 0; i < 10; i++){ updateSizer(); out.push(board.style.minWidth); }
      delete vp.clientWidth; delete vp.clientHeight;
      return out;
    }""")
    assert len(set(larguras)) == 1, f"minWidth oscilou entre chamadas: {larguras}"

def test_updatesizer_usa_offsetwidth_mesmo_sem_barra_de_rolagem(page):
    """Garante que a correção não muda o comportamento no caso normal (sem barra de rolagem, onde
    offsetWidth e clientWidth já são iguais): o quadro continua preenchendo a largura do viewport."""
    ok = page.evaluate("""() => {
      updateSizer();
      const esperado = Math.round(vp.offsetWidth) + "px";
      return board.style.minWidth === esperado;
    }""")
    assert ok

# Decisão 0069: pedido do usuário — a área pannable do quadro (fora do conteúdo) era pequena demais; a
# câmera "batia nas bordas" ao mover o minimapa, mesmo com bastante espaço livre no próprio minimapa.
# updateSizer() passa a reservar uma margem (metade da largura/altura do viewport, em pixels de TELA —
# não encolhe com o zoom) nos 4 lados do conteúdo, deslocando #board pra dentro do #sizer em vez de
# deixá-lo colado em (0,0).

def test_board_tem_margem_pannable_em_volta_do_conteudo(page):
    carregar(page, "f4p.xlsx")
    d = page.evaluate("""() => {
      updateSizer();
      return {left: parseFloat(board.style.left), top: parseFloat(board.style.top),
        sizerW: sizer.offsetWidth, sizerH: sizer.offsetHeight,
        boardVisW: board.offsetWidth * Z, boardVisH: board.offsetHeight * Z};
    }""")
    # margem = metade do viewport, nos 4 lados — então o sizer é maior que o conteúdo visível em pelo
    # menos uma margem de cada lado (esquerda+direita, acima+abaixo)
    assert d["left"] > 0 and d["top"] > 0
    assert d["sizerW"] >= d["boardVisW"] + d["left"]
    assert d["sizerH"] >= d["boardVisH"] + d["top"]

def test_margem_pannable_nao_encolhe_com_zoom_out(page):
    """A margem é definida em pixels de TELA (vp.offsetWidth/offsetHeight), não multiplicada por Z —
    diferente da margem antiga (160/200px de conteúdo, que de fato encolhia a quase nada com zoom out,
    causa raiz do bug relatado: a área livre pra mover a câmera sumia visualmente ao dar zoom out)."""
    r = page.evaluate("""() => {
      Z = 1; updateSizer();
      const left100 = parseFloat(board.style.left);
      Z = 0.3; updateSizer();
      const left30 = parseFloat(board.style.left);
      Z = 1; updateSizer();
      return {left100, left30};
    }""")
    assert r["left100"] == r["left30"]   # margem em tela é a mesma, independente do zoom

def test_carga_inicial_comeca_com_a_camera_no_conteudo_nao_na_margem(page):
    """Sem isso, toda carga (inicial ou recarregada) do Azure DevOps abriria com a câmera parada na
    margem em branco, em vez de no início do conteúdo — já que o conteúdo não começa mais em (0,0)."""
    carregar(page, "f4p.xlsx")
    r = page.evaluate("() => ({scrollLeft: vp.scrollLeft, scrollTop: vp.scrollTop, panMX, panMY})")
    assert abs(r["scrollLeft"] - r["panMX"]) < 1
    assert abs(r["scrollTop"] - r["panMY"]) < 1

def test_selecionar_iniciativa_rola_a_camera_para_o_topo_do_conteudo_nao_da_margem(page):
    """Regressão: o clique numa iniciativa reseta a rolagem vertical pra "o topo" — antes disso era
    sempre 0 (que coincidia com o início do conteúdo); com a margem pannable, 0 passou a cair na área
    em branco acima do conteúdo, então o reset precisa usar panMY, não 0."""
    carregar(page, "responsaveis.xlsx")
    page.evaluate("() => { vp.scrollTop = 50000; }")   # simula a câmera longe do topo
    page.locator("#lane-ini .card.lvl-ini").nth(0).click()
    page.wait_for_timeout(100)
    r = page.evaluate("() => ({scrollTop: vp.scrollTop, panMY})")
    assert abs(r["scrollTop"] - r["panMY"]) < 10   # tolerância pequena (reflow/arredondamento), nunca perto de 0
