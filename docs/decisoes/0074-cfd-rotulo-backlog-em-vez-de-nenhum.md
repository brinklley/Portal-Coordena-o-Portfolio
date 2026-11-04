# 0074 — CFD (Actionable): rótulo "Backlog" em vez de "Nenhum", só neste gráfico

## Contexto

O usuário pediu, com print do quadrante CFD do Actionable, pra trocar o rótulo "Nenhum" (legenda,
tooltip ao passar o mouse e texto de ajuda) por "Backlog" — só nesse gráfico, não em todo o portal, onde
"Nenhum" é o rótulo padrão da categoria de fluxo pra itens que ainda não chegaram a Discovery/WIP/Vazão
(`catOf`/`CAT_LABEL`, usado em cards, Visão analítica, Report F4P etc.).

## Decisão

Mudança só de **rótulo de exibição**, dentro do CFD (`actCfdCard`/`actCfdSvg`, Actionable §13.4): a
legenda, o tooltip por semana e o texto de ajuda abaixo do gráfico passam a dizer "Backlog" onde diziam
"Nenhum". Nada mais muda — nem o cálculo, nem o modelo de dados, nem o resto do portal:

- A categoria de fluxo continua `"none"`/"Nenhum" em todo o resto do código (`catOf`, `CAT_LABEL`, os
  demais quadrantes do Report F4P/Actionable, os cards do quadro).
- Os nomes internos deste mesmo quadrante (`d.nenhum`, `d.bandNenhum`, as classes CSS
  `act-cfd-l-nenhum`/`act-cfd-nenhum`) foram deixados como estão — são identificadores internos, não
  texto visível, e renomeá-los seria churn sem necessidade, com risco de quebrar algo por engano.

Essa categoria "Nenhum" pode, na prática, incluir mais de uma coluna do fluxo do time além de uma
coluna literalmente chamada "Backlog" (qualquer coluna marcada "Nenhum" em Configurações › Fluxo dos
times) — "Backlog" aqui é só o nome mais comum/intuitivo pra essa faixa num CFD, não uma mudança na
regra de quais colunas entram nela.

## Consequências

- `src/js/24-actionable.js`: `actCfdCard` (legenda), `actCfdSvg` (tooltip por semana) e o texto de ajuda
  do card CFD passam a mostrar "Backlog".
- `docs/regras-de-negocio.md` §13.4: nota explicando que o rótulo de exibição do CFD é "Backlog", mesmo a
  categoria subjacente continuando "Nenhum".
- `docs/telas.md`: descrição do CFD atualizada.
- Sem mudança de teste automatizado: nenhum teste da suíte dependia do texto literal "Nenhum" na legenda/
  tooltip do CFD (os testes existentes usam os campos internos, como `bandNenhum`).
