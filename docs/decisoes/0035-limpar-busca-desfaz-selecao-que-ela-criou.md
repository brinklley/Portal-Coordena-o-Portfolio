# 0035 — Limpar o campo "ID ou descrição" desfaz a seleção que ele criou

## Contexto

O usuário reportou uma regressão introduzida pela decisão `0034` (campo único "ID ou descrição"):
buscar por um ID, ver o quadro descer até ele (via Enter, que abre a cadeia inteira e destaca o
item), e depois limpar o campo pelo **"×" nativo** do `<input type="search">` — o filtro "ID ou
descrição" some da lista de filtros ativos, mas o quadro **continua preso** mostrando só aquela
iniciativa ("mostrando só a selecionada"), como se nada tivesse sido limpo de verdade.

## Diagnóstico

`gotoId()` (decisão `0034`) passou a, além de filtrar, também abrir a cadeia até o item encontrado
(`S.path`) quando a busca é um ID e ele está visível. Isso é novo: o antigo campo "Iniciativa (ID ou
nome)" nunca tocava `S.path`, só filtrava — então limpá-lo sempre bastava para voltar ao quadro
inteiro. `render()` só descarta `S.path.ini` quando a iniciativa selecionada **deixa de estar
visível** com os filtros atuais (`06-renderizacao.js`). Limpar a busca torna a lista de iniciativas
visíveis **maior**, não menor — a iniciativa que a busca tinha aberto continua lá dentro, então essa
regra nunca dispara, e a seleção feita pela própria busca fica "grudada" mesmo sem filtro nenhum
ativo.

## Correção

Novo campo `S.pathQueryId`: guarda o ID que fez `gotoId()` abrir a seleção atual (`null` quando a
seleção não veio de uma busca — clique em card, "Limpar seleção", migalhas de pão). Sempre que a
busca muda de valor (`setQueryFilter`, inclusive para vazio) ou os filtros são limpos
(`clearFilters`), se `S.pathQueryId` estiver preenchido e diferente do novo valor, a seleção
(`S.path`) é desfeita junto — `dropSearchSelectionIfStale()`, em `11-filtros-e-diagnostico.js`. Os
outros pontos que já mexiam em `S.path` por conta própria (clique num card, migalhas de pão, "Limpar
seleção", carregar dados de novo) também zeram `S.pathQueryId`, para uma seleção manual feita depois
de uma busca não ser derrubada por engano quando essa busca antiga for limpa.

## Testes

`tests/test_filtros.py`: `test_limpar_a_busca_desfaz_a_selecao_que_ela_criou` (limpar o campo — via
`page.fill("#fBusca", "")`, que dispara o mesmo evento `input` que o "×" nativo do navegador — volta
`S.path` a `{}`) e `test_trocar_a_busca_por_outro_id_tambem_desfaz_a_selecao_anterior` (trocar para
outro ID, mesmo só digitando, também desfaz a seleção anterior).
