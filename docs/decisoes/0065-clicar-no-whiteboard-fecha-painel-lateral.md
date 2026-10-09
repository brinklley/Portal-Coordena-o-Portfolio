# 0065 · Clicar no whiteboard fecha o painel lateral aberto (Visão Analítica/Report F4P/Actionable)

## Contexto

O usuário relatou: com a Visão Analítica (ou Report F4P/Actionable) aberta, ele frequentemente clica
na área do whiteboard esperando que o painel feche — comportamento comum em menus/painéis laterais —,
mas isso não acontecia. A única forma de fechar era ir até o botão "«" no canto do painel, pouco óbvio
quando o painel ocupa boa parte da tela (`width:min(1180px,96vw)`) e some atrás dele a maior parte do
quadro.

## Decisão

Um clique em qualquer lugar do whiteboard (`#viewport`, que contém `#board`) — num card ou em área
vazia — fecha o painel lateral que estiver aberto no momento (`AN.open`/`F4P.open`/`ACT.open`).
Clicar num card continua funcionando normalmente (seleciona a iniciativa/release/épico, abre o
painel de detalhes quando aplicável); fechar o painel lateral é um efeito a mais do clique, não uma
substituição do comportamento existente.

**Arrastar o quadro (pan) não conta como clique**: a área vazia do whiteboard já é arrastável para
reposicionar a visão (zoom/pan), e um clique nativo do navegador ainda dispara ao soltar o botão do
mouse mesmo depois de um arrasto longo, sem limite de distância por padrão. Sem distinguir os dois
casos, reorganizar a visão enquanto a Visão Analítica está aberta fecharia o painel a cada arrasto —
o oposto do que o usuário quer ao consultar o painel lado a lado com o quadro. `vp` (o container do
whiteboard, já usado para zoom/pan em `src/js/08-whiteboard-zoom-foco.js`) passou a marcar `panMoved`
quando o deslocamento entre o `pointerdown` e o `pointermove` passa de 4px; o listener que fecha o
painel ignora o clique quando `panMoved` está ligado.

## Consequências

- `src/js/08-whiteboard-zoom-foco.js`: nova variável `panMoved`, resetada a cada `pointerdown` e
  ligada em `pointermove` quando o deslocamento passa de 4px.
- `src/js/09-interacao-e-responsaveis.js`: novo listener de `click` em `vp` que fecha o painel aberto,
  ignorando quando `panMoved` está ligado.
- Arrastar uma ilha solta (`.movable`, decisão `0040`) já tem seu próprio tratamento de `pointerdown`
  com `stopPropagation()`/`preventDefault()` em `src/js/10-ilhas.js`, suprimindo o `click` sintético
  do navegador nesse caso — não precisou de nenhum ajuste adicional.
- `tests/test_quadro_iniciativas.py` ganhou 3 testes: clicar em área vazia fecha o painel aberto;
  clicar num card também fecha, mantendo a seleção normal; arrastar (pan) não fecha, mas um clique
  simples logo depois fecha normalmente.
