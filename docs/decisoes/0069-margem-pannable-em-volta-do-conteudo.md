# 0069 · Margem pannable constante (em tela) em volta do conteúdo do quadro

## Contexto

Depois da decisão `0068` (largura ajustável dos painéis laterais), o usuário voltou com o mesmo pedido
de "mais espaço pra navegar", agora deixando claro (com prints anotados) que o problema não era a
largura do painel — era a própria área de navegação do **whiteboard**: mesmo sem nenhum painel aberto,
a câmera "batia nas bordas" ao tentar se mover (arrastando o quadro ou pelo minimapa), porque a área
pannable (`#sizer`, o container que define até onde dá pra rolar) era pouco maior que o próprio
conteúdo. Um dos prints mostra o minimapa com uma faixa cinza (a área pannable) grudada no conteúdo,
sem folga nenhuma pros lados — pediu que a área útil fosse "no mínimo o dobro", com espaço em branco
de sobra nos 4 lados.

## Diagnóstico

`updateSizer()` (`src/js/08-whiteboard-zoom-foco.js`) dimensionava `#sizer` como:

```js
sizer.style.width = (Math.max(board.offsetWidth, ex.r + 160) * Z) + "px";
sizer.style.height = (Math.max(board.offsetHeight, ex.b + 200) * Z) + "px";
```

Dois problemas, um mais grave que o outro:

1. **Só existia margem à direita/abaixo** (`+160`/`+200`) — `#board` ficava grudado em `left:0;top:0`
   dentro do `#sizer`, então não havia margem NENHUMA pra rolar a câmera pra esquerda ou pra cima além
   do próprio conteúdo.
2. **A margem (mesmo só nos 2 lados que tinha) encolhia a quase nada com zoom out.** `160`/`200` são
   medidos em pixels de **conteúdo** (a mesma unidade de `ex.r`/`ex.b`, que vem de `offsetLeft`/
   `offsetTop` — não afetados pelo `transform:scale()`), e só viram pixels de **tela** depois do
   `* Z` no final da expressão. Em zoom reduzido (ex.: `Z = 0.3`, comum pra ver o quadro inteiro),
   `160px` de margem de conteúdo vira só `48px` de margem real na tela — imperceptível, exatamente o
   que o segundo print do usuário mostrava (uma faixa de espaço em branco enorme ao redor da área
   cinza, mas a área cinza em si mal folga do conteúdo).

## Decisão

`updateSizer()` passa a reservar uma margem fixa em **pixels de tela** (não de conteúdo) — `metade da
largura/altura do viewport` — nos **4 lados** do conteúdo:

```js
const mx = vp.offsetWidth * PAN_MARGIN, my = vp.offsetHeight * PAN_MARGIN;   // PAN_MARGIN = 0.5
board.style.left = mx + "px"; board.style.top = my + "px";
sizer.style.width = (Math.max(board.offsetWidth, ex.r) * Z + mx * 2) + "px";
sizer.style.height = (Math.max(board.offsetHeight, ex.b) * Z + my * 2) + "px";
```

`left`/`top` de um elemento **não são afetados pelo `transform:scale()` dele mesmo** (o scale só muda o
tamanho renderizado, a partir do ponto de ancoragem definido por `left`/`top`) — por isso `mx`/`my`
somam direto, sem multiplicar por `Z`: o resultado é uma margem que **não encolhe nem cresce com o
zoom**, sempre proporcional ao viewport (meia tela de folga de cada lado, uma tela inteira a mais no
total em cada dimensão).

**Consequência colateral que precisou de correção**: como `#board` deixou de começar em `(0,0)` dentro
do `#sizer`, todo lugar que assumia "rolagem em `0` = início do conteúdo" ficou errado (passaria a
mostrar a margem em branco, não o conteúdo):

- **Carga de dados** (`loadTables()`, `src/js/17-filtros-e-carga.js`): sem ajuste, toda carga (inicial
  ou recarregada) abriria com a câmera parada na margem, em vez de no conteúdo. Corrigido chamando
  `updateSizer()` e posicionando `vp.scrollLeft/scrollTop` em `panMX`/`panMY` (as novas variáveis que
  guardam onde o conteúdo começa) logo após o primeiro `render()`.
- **Selecionar uma iniciativa** (`09-interacao-e-responsaveis.js`): resetava `vp.scrollTop = 0` pra
  voltar ao topo do quadro ao trocar de seleção — trocado por `vp.scrollTop = panMY`.
- **Minimapa** (`drawMinimap()`, `src/js/14-minimapa.js`): desenha cards/ilhas usando `pos(el)`, que
  mede a posição relativa ao próprio `#board` (não inclui o deslocamento de `#board` dentro do
  `#sizer`) — sem ajuste, os desenhos ficariam desalinhados com o retângulo do viewport (que usa
  `vp.scrollLeft`/`scrollTop`, medidos a partir da borda do `#sizer`). Corrigido somando `panMX/Z` e
  `panMY/Z` (convertendo a margem pra mesma unidade "sem zoom" que `pos()` usa) a cada posição
  desenhada.
- **"Ajustar à tela"** (`$("zFit")`) não precisou de ajuste: a margem é **simétrica** (mesma de cada
  lado), então a fórmula de centralização que já existia (`(scrollWidth - clientWidth) / 2`) já cai
  certinho no início do conteúdo por conta própria — a conta não mudou, só o resultado ficou correto
  de novo.

## Consequências

- `src/js/08-whiteboard-zoom-foco.js`: `PAN_MARGIN` (constante, 0.5) e `panMX`/`panMY` (recalculados a
  cada `updateSizer()`, única fonte de verdade de "onde o conteúdo começa" pro resto do código).
- `src/js/14-minimapa.js`: `drawMinimap()` ajustado para alinhar os desenhos com o novo deslocamento.
- `src/js/17-filtros-e-carga.js`: `loadTables()` posiciona a câmera em `panMX`/`panMY` após a carga.
- `src/js/09-interacao-e-responsaveis.js`: reset de rolagem ao selecionar iniciativa usa `panMY`.
- Testes novos em `tests/test_quadro_zoom_sizer.py`: margem presente nos 4 lados, margem não encolhe
  com zoom out, carga inicial começa com a câmera no conteúdo, seleção de iniciativa rola pro topo do
  conteúdo (não da margem).
- Documentação: `docs/telas.md` ("Zoom/arrastar"), `docs/testes/quadro-zoom-sizer.md`.
