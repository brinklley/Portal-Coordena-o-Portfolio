# 0029 — Visão analítica: agrupador por categoria (Backlog/Discovery/WIP/Vazão) na coluna Status

## Contexto

O usuário pediu, com um print do card de épico no quadro anexado como referência, que a coluna Status
da Visão analítica ganhasse uma nova linha com "o mesmo agrupador que é usado no card épico" — a
legenda de contagem por categoria (quadradinho colorido + rótulo + número) que já aparece no `c-meta`
do card de épico no quadro principal (`src/js/06-renderizacao.js`), distinta da barra de distribuição
compacta (`distBar`, mostrada no rodapé do mesmo card). O objetivo, nas palavras do usuário: dar ao
usuário uma visão de como os itens do épico estão distribuídos no fluxo, direto na tabela.

## Decisões

1. **Qual "agrupador" reaproveitar**: o card de épico tem dois elementos distintos — `distBar(m)` (uma
   barra compacta de traços coloridos, cuja contagem só aparece no tooltip) e a legenda do `c-meta`
   (quadradinho colorido + rótulo + número, sempre visível, incluindo categorias com contagem zero). O
   print de referência do usuário mostra claramente a segunda forma (contagens visíveis, inclusive "WIP
   0"), então foi essa que reaproveitei — não a barra compacta, que esconderia justamente as categorias
   zeradas que o print evidencia.
2. **Extração para reuso** (`distGroup(m)`): a legenda já existia, mas inline dentro do template do card
   de épico (`src/js/06-renderizacao.js`). Extraí para uma função própria (`distGroup`, em `src/js/
   05-estado-e-calculos.js`, ao lado de `distBar`/`phaseOf`, que já são os utilitários de métricas por
   épico) e troquei o card de épico para chamá-la — saída **idêntica** ao HTML anterior (mesmas classes,
   mesmos textos, mesma ordem), então não é uma mudança visual no quadro, só elimina a duplicação que
   surgiria ao reaproveitar a mesma legenda na Visão analítica.
3. **Fonte dos números**: cada linha da Visão analítica já calcula `epiMetrics(e, team)` (variável `m`),
   que já filtra os itens do épico **pelo time em análise** — a mesma fonte usada pelo QTD/Capacidade/
   Projetada (decisão `0027`). `distGroup(m)` usa exatamente esse `m`, então o agrupador da linha conta
   só os itens daquele time, nunca de outro time que também tenha itens vinculados ao mesmo épico.
4. **Sempre as 4 categorias, mesmo com zero**: seguindo o comportamento já existente do card de épico
   (que sempre mostra Backlog/Discovery/WIP/Vazão, mesmo zerados) — consistente com o print de
   referência do usuário.

## Consequências

- `src/js/05-estado-e-calculos.js`: nova função `distGroup(m)`.
- `src/js/06-renderizacao.js`: card de épico agora chama `distGroup(m)` em vez do HTML inline (saída
  idêntica).
- `src/js/15-visao-analitica.js`: nova linha (`<div class="an-dist">`) na célula de Status, chamando
  `distGroup(m)`.
- `src/styles.css`: nova classe `.an-table .an-dist` (layout da linha na tabela da Visão analítica);
  reaproveita a classe `.sq`/`.sq.none/.disc/.wip/.vaz` já existente para os quadradinhos coloridos.
- Testes em `tests/test_visao_analitica.py`: agrupador mostrando as 4 categorias (inclusive zero) com as
  contagens certas, e contando só os itens do time em análise quando o épico tem itens de mais de um
  time. A suíte completa (incluindo os testes do quadro que exercitam o card de épico) segue verde,
  confirmando que a extração de `distGroup` não mudou a saída existente.
- Documentação: `docs/regras-de-negocio.md` §10, `docs/telas.md`.
