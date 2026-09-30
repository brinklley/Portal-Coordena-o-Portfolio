# 0053 — Visão analítica: ordenação padrão da coluna Status prioriza Entregue, depois WIP, Discovery e Backlog

## Contexto

O usuário pediu, olhando a tabela "Roadmap CORE 2º semestre 2026" da Visão analítica: que a ordenação
por Status passasse a trazer primeiro os épicos já **entregues (Vazão)**, depois **WIP**, depois
**Discovery** e por último **Backlog** — para ajudar a priorizar visualmente o que está em foco (mais
adiantado primeiro).

## Diagnóstico

A ordenação padrão da tabela já era pela coluna Status (`AN = {sort:"status", dir:1}`), mas a prioridade
usada (`PH_ORDER` em `src/js/15-visao-analitica.js`) era `{wip:0, discovery:1, backlog:2, vazio:3,
fechado:4}` — ou seja, com a direção padrão (ascendente), a ordem exibida era **WIP, Discovery, Backlog,
Sem reserva e só por último Entregue**: o inverso do que o usuário queria, e sem nenhuma relação
evidente com "o que está mais perto de terminar".

## Decisão

Redefinir a prioridade da coluna Status para:

```js
const PH_ORDER = {fechado:0, wip:1, discovery:2, backlog:3, vazio:4};
```

Com a direção padrão (`AN.dir = 1`), a tabela passa a mostrar, do topo pro fim: **Entregue → WIP →
Discovery → Backlog → Sem reserva** — sem precisar de nenhum clique adicional, já que essa já era (e
continua sendo) a ordenação padrão ao abrir o painel. "Sem reserva" (nenhum item com a tag de capacidade
vinculado ao épico) fica por último, depois de Backlog, por ter ainda menos sinal de progresso que um
épico com item de fato reservado parado em Backlog.

O desempate dentro do mesmo grupo de Status continua o mesmo (maior CycleTime primeiro) — não fazia
parte do pedido e não há razão de negócio para mudar.

Clicar no cabeçalho da coluna continua invertendo a direção normalmente (agora mostrando Sem reserva →
Backlog → Discovery → WIP → Entregue), sem nenhuma mudança de comportamento além da nova prioridade
base.

## Consequência

Mudança isolada em uma única constante (`PH_ORDER`), sem efeito em nenhum outro cálculo — `PH_ORDER` só
é usada dentro de `anSorted` para a coluna "status"; `reservaPhase`, `PH_TXT`/`PH_TXT_RESERVA` (rótulos
exibidos) e o agrupador por categoria (`distGroup`) não mudam.
