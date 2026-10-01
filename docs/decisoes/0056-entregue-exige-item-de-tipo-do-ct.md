# 0056 — Visão analítica: "Entregue" exige pelo menos um item de tipo configurado para o CT

## Contexto

O usuário reportou um épico órfão (#737129, "[Gerenciador] Inclusão de informações de encargos do
cartão") mostrando QTD "0 itens" na Visão analítica, mas Status "Entregue" e o agrupador por categoria
logo abaixo mostrando "Vazão 1". Hipótese do usuário: como o épico não tem vínculo com release nem
iniciativa, o cálculo da coluna QTD não estaria encontrando o item vinculado, causando a informação
desalinhada.

## Investigação

`rowOf()` (`src/js/15-visao-analitica.js`) já separa dois conjuntos desde sempre:

- `itens` = `m.recs.filter(isType)` — só os itens dos **tipos configurados para o CT**
  (`CFG.ctTypes`, padrão User Story/Technical Story/Technical Solution). É esse conjunto que alimenta
  **QTD**, **Capacidade** e **Projetada**.
- `m` (de `epiMetrics`) = **todos** os itens do time no épico, **de qualquer tipo** — é esse conjunto
  que alimenta o agrupador por categoria (`distGroup`) logo abaixo da Status, e (desde a decisão `0055`)
  também a regra 1 de "Entregue" (`allVazao = m.n > 0 && m.vaz === m.n`).

O item do épico #737129 é do tipo **Spike** — confirmado pelo print do Azure DevOps anexado pelo
usuário — que **não está** em `CFG.ctTypes` por padrão. Por isso: `itens.length === 0` (QTD "0 itens",
correto: não há item de tipo relevante pra essa tabela), mas `m.n === 1` e `m.vaz === 1` (o Spike em
Vazão), então a regra 1 da decisão `0055` (`allVazao`) via esse item como "tudo entregue" e marcava
"Entregue" — gerando a informação desalinhada relatada.

**A hipótese do usuário (causa ligada a épico órfão/sem release-iniciativa) não se confirmou.**
`rowOf()` é executada de forma idêntica para épicos normais e órfãos — a única diferença é a origem da
iniciativa (`i`) usada para `ref`/`cls` e o aviso "OBS: SEM INICIATIVA e SEM RELEASE". O bug reproduz
igual num épico **normal** (com release e iniciativa válidas) cujo único item do time também seja de um
tipo fora de `CFG.ctTypes` — confirmado por um teste dedicado
(`test_entregue_nao_conta_item_de_tipo_fora_do_ct_epico_normal`). A causa real é a regra 1 da `0055`
usar `m` (todos os tipos) em vez do mesmo filtro de tipo que QTD/Capacidade/Projetada já usam.

## Decisão

Adicionar `itens.length > 0` como exigência da regra 1 (`allVazao`) da decisão `0055`:

```js
const allVazao = itens.length > 0 && m.n > 0 && m.vaz === m.n;
```

Com isso, um épico cujo único vínculo do time seja de um tipo fora de `CFG.ctTypes` nunca mais vira
"Entregue" só por esse item estar em Vazão — cai de volta na regra padrão (`reservaPhaseBase`, baseada
em `reservados`, que já é um subconjunto de `itens`), mostrando "Sem reserva" quando não há nenhum item
do CT reservado. As regras 2 (alerta) e 3 (sem reserva, mas tudo em Vazão — quando há pelo menos um item
do CT) continuam exatamente como na `0055`, já que ambas dependem de `reservados`/`reservaPhaseBase`, que
sempre foram filtrados por tipo.

## Consequência

- Nenhuma mudança para épicos cujo vínculo do time já é só de tipos do CT (o caso mais comum) — os
  testes da decisão `0055` continuam passando sem alteração.
- Um épico com QTD "0 itens" (nenhum vínculo de tipo relevante para o CT) nunca mais mostra "Entregue";
  mostra "Sem reserva", consistente com a contagem zero na QTD.
- Confirmado, com teste dedicado, que o comportamento é idêntico em épicos órfãos e normais — a causa
  nunca teve relação com o vínculo de release/iniciativa.
