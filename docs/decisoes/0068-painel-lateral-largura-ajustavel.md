# 0068 · Largura do painel lateral (Visão analítica/Report F4P/Actionable) ajustável, padrão menor

## Contexto

O usuário pediu, anexando um print anotado: com um painel lateral aberto (Visão Analítica, no
exemplo) e navegando no quadro ao mesmo tempo, a área visível do whiteboard ficava pequena demais —
"batendo nas bordas". Pediu que a área útil do quadro fosse "no mínimo o dobro" para conseguir manter
mais coisas abertas ao mesmo tempo.

## Diagnóstico

`.an-panel` (classe compartilhada pelos 3 painéis — `anPanel`, `f4pPanel`, `actPanel`) é
`position:fixed;left:0` com largura fixa em `min(1180px, 96vw)`. O whiteboard (`.viewport`/`#board`)
**não encolhe** quando um desses painéis abre — diferente do painel de detalhes de um item
(`body.with-drawer .viewport{margin-right:...}`), os 3 painéis analíticos são um overlay fixo por cima
do quadro, que continua renderizado em largura cheia por trás. Na prática, isso significa que a área
"útil" do quadro que o usuário enxerga é exatamente `largura da janela − largura do painel` — com o
painel em até 1180px fixos, sobrava pouco em janelas de até ~1600-1900px de largura (comuns em laptops
e monitores não ultra-wide), exatamente o relatado.

Não existe uma única largura de painel que "dobre" a área do quadro para qualquer tamanho de tela: em
janelas estreitas, um painel bem menor (ex. 370px) seria necessário para a conta fechar; em janelas
muito largas, até o 1180px atual já deixa de sobra. Em vez de perseguir um número mágico fixo, a
solução dá ao usuário **controle direto** sobre essa divisão.

## Decisão

1. **Largura padrão caiu de 1180px para 760px** (`--an-w` em `:root`, `src/styles.css`) — já libera uma
   faixa relevante de quadro por padrão, sem precisar de nenhuma ação do usuário, e ainda cabe
   confortavelmente a grade de 2 colunas do Report F4P/Actionable (`.f4p-grid`/`.act-quad-grid`, que só
   quebra para 1 coluna abaixo de 820px) na maioria das larguras de tela.
2. **Alça de redimensionamento** (`.an-resize`, uma faixa de 12px na borda direita do painel, cursor
   `col-resize`): o usuário arrasta para ajustar entre **360px** (mínimo — ainda legível, o conteúdo que
   não couber rola horizontalmente via `overflow:auto`, já existente em `.an-body`) e **1180px**
   (máximo — o valor fixo antigo, para quem prefere a tabela/grade inteira visível sem rolar). Arrastar
   além dos limites trava neles, nunca ultrapassa.
3. **Preferência única, compartilhada pelos 3 painéis, persistente** (`localStorage`, chave
   `mapaPortfolioAnW`): como os 3 painéis compartilham a classe `.an-panel` e a variável CSS `--an-w`,
   redimensionar qualquer um deles vale para os outros dois também — faz sentido como uma única
   preferência de "quanto espaço eu quero para um painel lateral", não uma por painel. Guardada fora de
   `CFG` de propósito: é preferência de interface do navegador, não configuração de negócio (não deve
   ir na exportação/importação de configuração, que é para portar regras entre usuários/organizações,
   não hábitos de tela).

## Consequências

- `src/styles.css`: `--an-w:760px` em `:root`; `.an-panel` usa `width:min(var(--an-w),96vw)`; novas
  classes `.an-panel.resizing` (desliga a transição durante o arrasto) e `.an-resize` (a alça).
- `src/js/15-visao-analitica.js`: lógica de arrastar (pointerdown/pointermove/pointerup com
  `setPointerCapture`), aplicação via `document.documentElement.style.setProperty("--an-w", ...)`,
  leitura/gravação em `localStorage` — adicionada a uma alça por painel (`document.querySelectorAll(
  ".an-panel")`), então vale igualmente para Visão Analítica, Report F4P e Actionable sem duplicar
  código.
- Nenhuma mudança em `updateSizer()`/`redraw()` (`08-whiteboard-zoom-foco.js`): como o whiteboard nunca
  encolhe quando um painel analítico abre (diferente do drawer de detalhes), redimensionar o painel não
  muda o tamanho real do quadro — só quanto dele fica visível ao lado do painel.
- Testes novos em `tests/test_quadro_iniciativas.py`: largura padrão (760px), arrastar dentro dos
  limites (inclusive o clamp no mínimo), e a preferência compartilhada entre os 3 painéis.
- Documentação: `docs/telas.md` (parágrafo do Actionable, onde já ficam as regras compartilhadas dos 3
  painéis), `docs/guia-usuario/quadro.md`, `docs/testes/quadro-e-selecao.md`.
