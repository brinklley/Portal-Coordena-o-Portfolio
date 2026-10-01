# 0055 — Visão analítica: "Entregue" passa a considerar todos os itens, com alerta quando a Reserva já fechou mas o épico não

## Contexto

O usuário mandou dois prints da Visão analítica pedindo duas melhorias na coluna Status:

1. **Épico #612581** ("[IB] Rastreamento do cartão"): Status mostrava "Entregue" (2 reservados, ambos
   em Vazão), mas o agrupador por categoria logo abaixo mostrava "Backlog 1" — um item do épico, sem a
   tag ROADMAP, ainda parado em Backlog. Pedido: "Entregue" só deveria aparecer quando **todos** os
   itens vinculados ao épico estiverem em Vazão, não só os reservados; quando os reservados já
   entregaram mas existe pendência fora da reserva, deve aparecer um **alerta** sinalizando atenção.
2. **Épico #759863** (órfão, "0 reservados", todos os itens em Vazão): Status mostrava "Sem reserva".
   Pedido: se **todos** os itens vinculados já estão em Vazão, mesmo sem nenhuma tag ROADMAP, não há
   nada pendente para justificar "Sem reserva" — deve mostrar "Entregue".

Pedido explícito de documentação clara sobre como chegar em "Entregue" (atendido na seção §10 de
`docs/regras-de-negocio.md`).

## Conflito identificado e decisão do usuário

O pedido 1, levado ao pé da letra ("Entregue só pode ser identificado caso todos os itens estejam em
Vazão"), colidia com um teste e uma regra já existentes desde a decisão `0049`:
`test_status_mostra_entregue_quando_so_os_reservados_ja_estao_em_vazao`, cujo comentário dizia
explicitamente que um item não reservado ainda aberto "não deve impedir o Entregue". Perguntei ao
usuário se, nesse cenário (reserva 100% entregue, algo pendente fora dela), o selo deveria **continuar
"Entregue" com um ícone de alerta ao lado**, ou **deixar de ser "Entregue"** (texto substituído por um
aviso). O usuário escolheu a primeira opção: manter "Entregue" (o compromisso do roadmap foi cumprido)
e adicionar um ícone de alerta — preservando o teste e a regra da `0049` sem alteração de comportamento,
só adicionando o alerta por cima.

## Decisão

`rowOf()` (`src/js/15-visao-analitica.js`) passa a calcular, além da fase baseada só na Reserva
(`reservaPhaseBase`, lógica da `0049` inalterada), um segundo critério usando o total do épico (`m`, o
mesmo conjunto que o agrupador por categoria já soma — todos os itens do time, com ou sem a tag):

```js
const allVazao = m.n > 0 && m.vaz === m.n;
const reservaPhase = allVazao ? "fechado" : reservaPhaseBase;
const alert = !allVazao && reservaPhaseBase === "fechado";
```

- **`allVazao` verdadeiro** (todos os itens do épico, com ou sem tag, em Vazão) → `reservaPhase` é
  sempre `"fechado"` ("Entregue"), mesmo que não haja nenhum item reservado (`reservaPhaseBase` seria
  `"vazio"`/"Sem reserva" nesse caso) — resolve o pedido 2.
- **`allVazao` falso mas a Reserva já fechou** (`reservaPhaseBase === "fechado"`, ou seja, todo item com
  a tag está em Vazão) → `reservaPhase` continua `"fechado"` (mantém o teste da `0049`), mas `alert`
  liga — resolve o pedido 1 sem reverter a `0049`.
- Qualquer outro caso (Reserva ainda com item aberto, ou sem reserva e sem tudo entregue) → comportamento
  idêntico ao de antes da `0055`.

Na UI (`renderAnalytics()`), quando `alert` é verdadeiro, um ícone `⚠` (classe `st-alert`) aparece ao
lado do selo verde "Entregue", com `title` dizendo quantos itens (`m.n - m.vaz`) ainda estão pendentes
fora da reserva.

## Consequência

- Um épico com reserva 100% entregue mas algo pendente fora dela continua contando como "entregue" na
  KPI do topo do painel (coerente: o compromisso do roadmap foi cumprido) e na ordenação por Status
  (decisão `0053`), mas o alerta visual chama atenção para a pendência remanescente sem precisar abrir o
  épico.
- "Sem reserva" deixa de aparecer em qualquer épico 100% entregue — só é mostrado quando realmente há
  algo pendente para acompanhar e nenhum item está reservado para o roadmap.
- Nenhuma mudança na lógica das fases WIP/Discovery/Backlog (continuam olhando só a Reserva, decisão
  `0049`) nem na ordenação por Status (decisão `0053`, que só olha `reservaPhase`, inalterado nesses
  casos).
