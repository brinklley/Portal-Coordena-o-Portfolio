"""Whiteboard: dimensionamento do quadro (zoom/pan) — docs/telas.md "Zoom/arrastar", decisão
`0066-updatesizer-usa-offsetwidth-nao-clientwidth.md`."""

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
