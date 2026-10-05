# 0060 — Actionable: Burnup Reserva e CFD estendem o eixo para entrega tardia; Distribuição ganha alerta

## Contexto

Depois da decisão `0059` (o gráfico do Burnup Reserva passou a sempre terminar no mesmo total do resumo
"Entregue", encaixando uma entrega fora do período no mês mais próximo do próprio eixo X), o usuário
mandou um novo print e disse: "Mas o gráfico burnup continua não batendo". O pedido, desta vez, não era
mais sobre o total bater — era sobre **onde** a entrega aparece: "nos casos que existe itens cards
entregues após o semestre deve ser adicionado os meses subsequentes [reais] mas desde que o item card
épico esteja dentro do semestre selecionado do roadmap [...] adicionando uma linha vertical sinalizando
o último dia do semestre [...] para que o usuário possa visualizar que houve itens entregues após essa
linha". Ou seja: em vez de **encaixar** a entrega tardia artificialmente num mês que não é o real (a
correção da `0059`), o gráfico deveria **estender o eixo X** com os meses/semanas reais seguintes, com
uma linha vertical marcando onde o semestre comprometido terminou de fato.

O usuário também pediu a mesma extensão no **CFD** (outro quadrante com eixo baseado em tempo), e uma
exceção explícita na **Distribuição Vazão por mês**: por ser um gráfico de barras (não uma linha
contínua), não faz sentido desenhar uma linha vertical ali — em vez disso, o mês extra ganha um ícone de
alerta junto ao rótulo do mês.

## Decisão

Duas perguntas de design foram resolvidas com o usuário antes da implementação:

1. **Gatilho da extensão no CFD e na Distribuição** (quadrantes que hoje não filtram por épico/roadmap,
   só por time): **qualquer item do épico comprometido** com o roadmap do time+semestre selecionado
   (mesmo critério da coluna "Projetada" da Visão analítica, §10 — `anData().projItems`), **não**
   restrito à tag de capacidade do roadmap (`CFG.anTag`). Novo helper compartilhado:
   `actLateDeliveries(st, ad)` em `src/js/24-actionable.js`, usado pelo CFD e pela Distribuição. O
   **Burnup Reserva não usa este helper** — continua com sua própria regra, baseada só nos itens que ele
   mesmo mostra (`entregues`, subconjunto de `capItems`), como já era desde a `0058`/`0059`.
2. **Entrega antes do início do semestre**: continua com o comportamento da `0059`, inalterado —
   encaixada no 1º mês do eixo, sem estender para trás nem linha de início. O pedido do usuário foi só
   sobre entregas **depois** do fim.

### Burnup Reserva (`actBurnupData`)

Remove a cláusula "depois do fim → clampa no último mês" de `mesEfetivo` (mantém só "antes do início →
clampa no 1º mês"). Em vez disso, calcula a maior data de entrega de `entregues` que ultrapassa
`st.end`; havendo, estende `months` com os meses seguintes reais até cobrir essa data, e marca
`semEndIdx` (índice do último mês real do semestre) + `extended:true` no objeto retornado — usado por
`actBurnupSvg` para desenhar a linha vertical.

### CFD (`actCfdWeeks`)

O loop de construção de semanas foi fatorado em `actCfdWeeksBlock(from, to)` (mesmo algoritmo de antes,
parametrizado) + `actCfdBaseWeeks(st)` (as semanas do semestre, sem extensão — idêntico ao
`actCfdWeeks` de antes da `0060`, preservando os testes já existentes de "blocos de 7 dias"). O novo
`actCfdWeeks(st)` pega as semanas base e, se houver item tardio (`actLateDeliveries`), concatena um novo
bloco de semanas começando no dia seguinte ao fim do semestre até cobrir a entrega mais tardia.
`actCfdSemEndIdx(st)` expõe o índice da fronteira, usado por `actCfdSvg` para a linha vertical.
`actCfdData`/`actCfdOps` não mudaram — já operam sobre o array que `actCfdWeeks` devolve.

### Linha vertical "fim do semestre"

Helper compartilhado `actSemEndLine(xOf, idx, mT, ph)`, usado pelo Burnup Reserva e pelo CFD — desenha
uma linha + rótulo "fim do semestre" a meio caminho entre o último ponto real do semestre e o primeiro
ponto estendido (mesmo espírito visual da linha "hoje" já existente no CFD, decisão `0047`). CSS nova
classe `.act-sem-end`/`.act-sem-end-label`, reaproveitando o token de cor `--warn` já existente.

### Distribuição Vazão por mês (exceção)

`actDistMonths(st)` continua gerando os 6 meses fixos do semestre e, havendo item tardio
(`actLateDeliveries`), acrescenta os meses seguintes reais — mesma lógica de extensão do Burnup/CFD. O
mês extra usa **exatamente a mesma regra** de qualquer outro mês do quadrante (todas as entregas Vazão
do time naquele mês civil, sem filtrar por épico) — o épico comprometido só decide **se** o mês aparece,
não o que entra na barra dele, para não introduzir uma inconsistência de filtro entre meses do mesmo
gráfico. `actDistData` marca `late:true` nos meses além do 6º; `actDistRow` acrescenta um ícone de
alerta (⚠, com `title` explicativo) junto ao rótulo do mês — **sem** linha vertical.

## Consequência

Uma entrega tardia de um item cujo épico está comprometido com o roadmap do semestre selecionado agora
aparece no seu **mês/semana real** no Burnup Reserva e no CFD (em vez de artificialmente encaixada no
último ponto do eixo original), com uma linha vertical "fim do semestre" diferenciando visualmente o
período comprometido do que veio depois. Isso substitui só a metade "depois do fim" da decisão `0059` —
a metade "antes do início" (clamp no 1º mês) continua valendo sem alteração. Na Distribuição Vazão por
mês, o mesmo tipo de entrega tardia passa a aparecer como um mês extra sinalizado com ⚠, em vez de
simplesmente desaparecer do gráfico (comportamento de antes da `0060`, já que nenhum mês além dos 6 fixos
existia no eixo).
