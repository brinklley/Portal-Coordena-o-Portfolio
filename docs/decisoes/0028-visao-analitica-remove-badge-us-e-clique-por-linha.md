# 0028 — Visão analítica: remove o badge "X US" e adiciona clique por linha (QTD e reservado)

## Contexto

Depois de testar a decisão `0027` (Projetada/Capacidade como soma por épico, clique no cabeçalho), o
usuário pediu duas melhorias na mesma tela, com um print anotado mostrando que o "X US" ao lado da
descrição do épico é redundante com a coluna QTD (mesmo número, duas vezes na tela):

1. Remover o badge "X US" da linha do épico.
2. Tornar o QTD e o "reservado" de cada linha clicáveis, abrindo um modal com os itens daquele épico
   especificamente — mesma ideia de transparência da decisão `0027`, mas por linha em vez de só no
   total do cabeçalho.

## Decisões

1. **Remoção do "X US"**: a linha do épico já mostra a mesma quantidade na coluna QTD (a esquerda da
   tabela); mantê-la duas vezes não agregava informação. Removido o `<span class="us">` da linha; a
   classe CSS `.an-table .us` e o tratamento correspondente em `anCopy` (cópia para PowerPoint/Excel)
   foram removidos por ficarem sem uso.
2. **QTD e "reservado" da linha viram botões**: cada um abre `f4pItemsModal` com os itens daquele
   **épico específico** — `row.itens` (QTD) ou `row.reservados` (reservado) — diferente dos botões do
   cabeçalho (decisão `0027`), que somam **todos** os épicos da tabela. Implementado com um único
   handler de clique (`data-an-epi-items="qtd"|"res"` + `data-an-epi="<id do épico>"`), que busca a
   linha correspondente em `anData().rows` no momento do clique (mesmo padrão de recomputar sob demanda
   já usado pelos outros cliques deste painel e do Report F4P, em vez de guardar estado de render).
3. **Estilo do "reservado" como botão**: o badge já tinha uma classe própria (`.res`, fundo azul claro)
   antes de virar clicável; para não perder esse estilo, o botão combina `.f4p-real` (aparência clicável
   padrão do portal: negrito, sublinhado pontilhado) com `.res` — como `.an-table .res` tem
   especificidade maior que `.f4p-real` (duas classes contra uma), o fundo azul continua vencendo mesmo
   com o `all:unset` do `.f4p-real`. A cópia para PowerPoint (`anCopy`) foi ajustada para aplicar o
   estilo do `.res` no mesmo passo em que substitui os botões por texto simples (antes dependia de um
   segundo `querySelectorAll(".res")`, que deixou de encontrar elementos depois que o badge virou
   `<button>` em vez de `<span>`).

## Consequências

- `src/js/15-visao-analitica.js`: linha do épico sem o "– X US"; QTD e "reservado" agora são
  `<button data-an-epi-items>`; novo tratamento de clique no `$("anPanel")`; `anCopy` ajustado (estilo do
  `.res` embutido na substituição de botões, linha redundante removida).
- `src/styles.css`: removida a classe `.an-table .us` (sem uso).
- Testes em `tests/test_visao_analitica.py`: linha sem o texto "US", clique no QTD de uma linha mostrando
  só os itens daquele épico (não do épico vizinho, mesmo time), clique no "reservado" de uma linha
  mostrando só os itens reservados daquele épico.
- Documentação: `docs/regras-de-negocio.md` §10, `docs/telas.md`.
