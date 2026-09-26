# 0021 — Quadro: manter todas as iniciativas visíveis (com foco na selecionada)

## Contexto

Ao selecionar um card no nível Iniciativas, a lista recolhe para mostrar só a selecionada (regra original, decisão `0003`-adjacente de UX do quadro); um link "Mostrar todas (N)" revelava as demais, mas isso resetava a cada nova seleção — escolher outra iniciativa sempre recolhia a lista de novo. O usuário descreveu um fluxo de trabalho comum: filtrar o quadro para um conjunto pequeno de iniciativas (ex.: 3), abrir a cadeia completa da primeira para analisar os filhos, voltar ao nível Iniciativas e continuar analisando as próximas — e pediu para conseguir ver, de forma clara, que ainda há outras iniciativas do filtro por analisar, sem perder de vista qual é a selecionada.

## Decisão

1. O link "Mostrar todas"/"Recolher as demais" (`data-act="allini"/"oneini"`) é substituído por um **checkbox persistente** nos filtros do topo: **"Manter todas as iniciativas visíveis"**, ao lado de "Mostrar itens sem desdobramento". **Desligado por padrão** — mesmo comportamento de hoje (lista recolhida na selecionada).

2. **Ligado**: a lista de Iniciativas continua mostrando **todas** as do filtro, mesmo com uma selecionada. A selecionada mantém a borda de foco (`.sel`, já usada em todo o quadro); as demais ficam com opacidade reduzida (`.card.dim`, a mesma classe já usada para esmaecer cards fora da cadeia no modo "cadeia completa" — decisão de reaproveitar em vez de criar uma variante nova de estilo).

3. **Diferente do comportamento anterior do link**: selecionar uma **outra** iniciativa não desliga mais o checkbox. É uma preferência de exibição (como "Mostrar etapas vazias"), não um estado por seleção — o usuário liga uma vez e continua vendo todas enquanto navega pelas iniciativas do filtro, com o foco visual acompanhando a seleção atual.

4. Preferência **de sessão**, não persistida (mesmo padrão de `S.showEmpty`/`S.showBare`): reinicia desligada a cada carregamento da página.

## Consequências

- `src/index.html`: novo checkbox `#fShowAllIni`.
- `src/js/09-interacao-e-responsaveis.js`: `$("fShowAllIni").onchange` liga `S.showAllIni`; removidos o `data-act` do clique nos cards e os resets de `S.showAllIni = false` ao selecionar uma iniciativa e ao "Limpar seleção" — a preferência agora só muda pelo próprio checkbox.
- `src/js/06-renderizacao.js`: o texto de contexto da lane Iniciativas passa a refletir os dois estados ("mostrando só a selecionada — marque..." / "mostrando todas — as outras N ficam sem foco"), sem os antigos botões de link; o card da Iniciativa ganha `dim` quando não é a selecionada e o checkbox está ligado.
- `src/js/12-investigacao.js`: o texto de investigação de um item "recolhido na lista" agora orienta a marcar o checkbox, em vez de citar o link removido.
- `src/styles.css`: removida a classe `.linkbtn`, que ficou sem uso.
- Nenhuma mudança na regra de **visibilidade** de dados (`docs/regras-de-negocio.md` §3) — o filtro em si não muda; isto é só sobre quais das iniciativas já visíveis aparecem recolhidas ou esmaecidas na lista.
