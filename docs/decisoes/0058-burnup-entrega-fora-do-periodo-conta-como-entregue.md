# 0058 — Actionable: Burnup Reserva conta entrega fora do período como Entregue, não Faltam

## Contexto

O usuário mandou um print do quadrante Burnup Reserva (Actionable, time BO, "1º semestre 2026")
mostrando "2 faltam" e, ao clicar para ver os 2 itens, os dois já apareciam com Situação "Vazão ·
DD/07/2026" — ou seja, já entregues, só que no **2º semestre** (a data de saída caiu fora do 1º semestre
selecionado no burnup). Hipótese do usuário: a data de entrega cair no outro semestre é a causa, e o
correto seria mostrar os itens como entregues.

## Investigação

`actBurnupData()` (`src/js/24-actionable.js`, decisão `0041`) definia "Entregue" como o subconjunto da
Reserva (itens com a tag `ROADMAP`, qualquer status) cuja categoria de fluxo é Vazão **e** cuja saída
caiu dentro do período exato do semestre selecionado (`fimUltimoMes`, calculado a partir dos meses do
burnup). "Faltam" era o complemento — por construção, incluía tanto os itens genuinamente ainda abertos
quanto uma entrega tardia (fora do período). A hipótese do usuário se confirmou: os 2 itens eram
reservados para o 1º semestre, mas saíram no 2º — a regra antiga (deliberada, decisão `0041`,
comentada explicitamente no código: "um item entregue depois desse período... não conta como Entregue
deste período") classificava os dois como "faltam", mesmo já em Vazão.

Essa é exatamente a mesma situação que a decisão `0052` já corrigiu no Report F4P (quadrante Vazão,
"Reserva entregue"): lá, o usuário reportou o mesmo tipo de inconsistência (item reservado, já entregue,
mas fora do número de "entregue" por causa da janela de datas) e a correção removeu a exigência de
janela — "Reserva entregue" passou a ser só "item da Reserva já em Vazão", qualquer data. O Burnup
Reserva do Actionable tinha ficado para trás dessa mesma revisão.

## Decisão

"Entregue" (resumo clicável, não o gráfico) passa a ser só `catOf(o) === "vazao"`, sem nenhuma
exigência de data — mesma regra da Reserva entregue do Report F4P pós-`0052`. "Faltam" volta a
significar exclusivamente "ainda não chegou em Vazão" (`catOf(o) !== "vazao"`).

```js
const entregues = capItems.filter(o => catOf(o) === "vazao");
const entreguesN = entregues.length;
const faltamItems = capItems.filter(o => catOf(o) !== "vazao");
```

**O gráfico não muda.** A linha acumulada (`cumulative`, um ponto por mês do semestre) continua só
contando entregas que caem dentro dos meses do próprio semestre — não é uma limitação arbitrária, é
inerente ao gráfico: não existe um mês no eixo X para plotar uma entrega de outro semestre. Uma entrega
tardia soma no resumo "Entregue", mas não aparece destacada numa subida específica da linha.

## Consequência

Um item reservado para um semestre, mas entregue fora do período exato (adiantado ou tardio), sempre
conta como "Entregue" no resumo clicável do Burnup Reserva — nunca mais aparece em "Faltam" com a
Situação já mostrando "Vazão". `entregues.length + faltamItems.length === capItems.length` continua
valendo sempre (partição exata), só a regra que decide de qual lado cada item cai mudou.
