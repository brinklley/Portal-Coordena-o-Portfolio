# 0070 · Selo de tag no card do épico fica clicável, abre a lista exata dos itens

## Contexto

O usuário relatou: um item card estava com a tag `PAUSADO`, a tag foi removida no Azure DevOps, e o
Portal continuou mostrando o selo `PAUSADO` — levantando a dúvida se o Portal estava lendo a tag ao
vivo ou de algum histórico. Pediu pra investigar e, se achado o problema, corrigir para todas as
regras que usam tag.

## Diagnóstico

Investigação completa do pipeline (carga do Azure DevOps → `04-modelo.js` → `01-configuracao-e-
regras.js` → telas): **o Portal já usa só o estado atual** (`System.Tags`, buscado ao vivo via
`_apis/wit/workitemsbatch`) para decidir se uma tag está presente — em todos os níveis e regras que
dependem de tag (cor/alerta do card operacional, Visão Analítica, Report F4P). O único lugar que lê o
histórico (`WorkItemRevisions`, via Analytics) é o cálculo de "há quantos dias está bloqueado", e só
entra em ação depois de confirmar, pelo dado ao vivo, que o item **está** bloqueado agora — não há
nenhuma mistura de dado histórico decidindo se uma tag está presente.

Com o print anexado pelo usuário, ficou claro o que de fato aconteceu: o card em questão era um
**Épico**, e o selo de tag que aparece nele (ex. `PAUSADO 1`) **não é a tag do próprio épico** — é um
**agregado**: quantos itens dos times vinculados ao épico, ainda abertos (fora da Vazão), têm aquela
tag (`epiMetrics().tagCount`, `src/js/05-estado-e-calculos.js`). O usuário conferiu a tag do épico em
si no Azure DevOps (vazia, como esperado — épicos não carregam esse tipo de tag) em vez do item
operacional específico que carrega a tag de verdade. O `title` (dica ao passar o mouse) do selo já
dizia "... nos times", mas passou despercebido.

## Decisão

Não havia bug de dado histórico pra corrigir — mas a confusão em si é um problema real de UX: o selo
do épico soma itens sem indicar **quais**, deixando o usuário sem como conferir rapidamente qual item
realmente carrega a tag. A correção é a mesma transparência já usada no Report F4P e na Visão
Analítica (decisões `0016`, `0022`, `0027`): o selo de tag do card do épico vira clicável e abre um
modal (`f4pItemsModal`, reaproveitado) com a lista exata dos itens que entram naquela soma — ID,
título e situação, cada um levando até o item no quadro.

## Consequências

- `src/js/06-renderizacao.js`: o selo de tag do card do épico ganha `data-epi-tag-epi`/`data-epi-tag-
  id`, `role="button"`, `tabindex="0"` e um `title` mais explícito ("não é a tag do próprio épico").
- `src/js/09-interacao-e-responsaveis.js`: novo `epiTagClick()` (clique e Enter/Espaço) abre o modal
  com a lista exata (mesmo filtro do agregado: só itens fora da Vazão, com a tag); checado antes da
  lógica de clique do card, pra clicar no selo não também selecionar/navegar o épico.
- `src/styles.css`: `.tchp.epi-tag` ganha `cursor:pointer` e destaque ao passar o mouse/focar.
- Testes novos em `tests/test_ct_alertas_tags.py`: o agregado conta só itens abertos; o modal mostra
  exatamente os itens certos (nem o sem tag, nem o já entregue com a mesma tag); clicar no selo não
  seleciona o épico.
- Documentação: `docs/regras-de-negocio.md` §9, `docs/testes/ct-alertas-tags.md`.
