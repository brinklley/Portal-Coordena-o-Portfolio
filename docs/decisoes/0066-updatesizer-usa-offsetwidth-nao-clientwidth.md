# 0066 · `updateSizer()` usa `offsetWidth`/`offsetHeight`, não `clientWidth`/`clientHeight`

**Contexto.** O usuário relatou: com o roadmap interno, o time e o ID de um épico selecionados nos
filtros (e já funcionando), ao digitar o ID e apertar Enter (abrindo o painel de detalhes do épico) e
em seguida trocar o Time no filtro, a tela "ficou tremendo em loop". Não havia nenhum erro no console,
mas o DevTools mostrava o atributo `style` de `#board` sendo reescrito continuamente (o Elements panel
pisca ao detectar uma mutação de atributo).

**Diagnóstico.** O único código que escreve em `board.style` é `updateSizer()`
(`src/js/08-whiteboard-zoom-foco.js`), chamado por `redraw()` toda vez que o `ResizeObserver` (que
observa `board`) detecta uma mudança de tamanho nele:

```js
function updateSizer(){
  board.style.minWidth = (vp.clientWidth / Z) + "px";
  board.style.minHeight = (vp.clientHeight / Z) + "px";
  ...
}
```

`vp` (`.viewport`, o container do whiteboard) tem `overflow:auto` — `clientWidth`/`clientHeight`
**encolhem** quando uma barra de rolagem aparece (removendo o espaço que ela ocupa) e **crescem** de
volta quando ela some. O problema: é o próprio `updateSizer()`, através do tamanho que atribui a
`board` (e, por tabela, a `sizer`, o elemento que de fato decide se `vp` precisa de barra), quem
decide se essa barra vai aparecer ou não — fechando um ciclo: a barra aparece → `clientWidth` encolhe
→ `updateSizer()` encolhe o quadro → a barra deixa de ser necessária e some → `clientWidth` volta a
crescer → `updateSizer()` aumenta o quadro de novo → a barra volta a aparecer → repete. Cada mudança
de tamanho de `board` dispara o `ResizeObserver` de novo, que chama `redraw()` → `updateSizer()`,
sem nunca convergir.

Reproduzido de forma determinística (não depende de layout/viewport frágil): mockando `vp.clientWidth`
para alternar entre dois valores a cada leitura (simulando a barra de rolagem aparecendo/sumindo) e
chamando `updateSizer()` repetidamente, `board.style.minWidth` oscila perfeitamente em sincronia com
o mock — confirmando o mecanismo exato do ciclo.

O gatilho mais comum para esse cenário na prática: o painel de detalhes (`body.with-drawer`) estreita
`.viewport` em até 420px (`margin-right:min(420px,100%)`), e uma carga grande de dados (centenas de
iniciativas) deixa o cálculo de largura perto o bastante do limiar onde a barra de rolagem
aparece/some de fato — por isso o usuário via o problema só depois de abrir o painel de detalhes
(Enter num ID) e trocar o Time, não em cargas pequenas.

**Decisão.** `updateSizer()` passa a usar `vp.offsetWidth`/`vp.offsetHeight` em vez de
`vp.clientWidth`/`vp.clientHeight`. `offsetWidth`/`offsetHeight` incluem a barra de rolagem no
cálculo (não mudam dependendo dela estar visível ou não), rompendo o ciclo — o quadro fica, na pior
das hipóteses, ~14-17px mais largo/alto do que o estritamente visível quando há barra, o que é
imperceptível e não muda nenhum comportamento visível de zoom/pan.

## Consequências

- `src/js/08-whiteboard-zoom-foco.js`: `updateSizer()` usa `offsetWidth`/`offsetHeight`.
- `tests/test_quadro_zoom_sizer.py` (novo): simula a barra de rolagem "piscando" (mock determinístico
  de `clientWidth`) e confirma que `updateSizer()` não oscila mais; confirma também que o
  comportamento normal (sem barra) não muda.
- Os demais usos de `vp.clientWidth`/`clientHeight` no código (centralizar/ajustar zoom num card, o
  retângulo do minimapa, "Ajustar à tela") são leituras pontuais que não escrevem de volta no tamanho
  de `board` — não fazem parte do ciclo e não precisaram de ajuste.
