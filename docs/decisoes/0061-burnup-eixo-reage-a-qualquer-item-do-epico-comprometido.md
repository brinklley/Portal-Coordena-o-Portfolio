# 0061 — Actionable: eixo do Burnup Reserva reage a qualquer item do épico comprometido, não só a Reserva

## Contexto

Logo depois da decisão `0060` (Burnup Reserva e CFD passam a estender o eixo X com os meses/semanas
reais quando há entrega tardia, com uma linha vertical "fim do semestre"; Distribuição ganha um ícone de
alerta), o usuário mandou um novo print: o resumo do Burnup Reserva lia "5 reservados · 5 entregues ·
0 faltam", com a linha acumulada já achatada no topo desde maio — mas o eixo X continuava preso em
"jun", enquanto o CFD e a Distribuição Vazão por mês do **mesmo time e semestre**, no mesmo print, já
mostravam julho e agosto, cada um com sua própria sinalização (linha "fim do semestre" no CFD, ícone de
alerta na Distribuição).

## Investigação

A decisão `0060` implementou o gatilho da extensão do Burnup Reserva usando a própria Reserva
(`entregues`, subconjunto de `capItems` — itens com a tag `CFG.anTag`/"ROADMAP"), enquanto o CFD e a
Distribuição usaram, por pedido explícito do usuário (resposta à pergunta de esclarecimento feita antes
da implementação da `0060`), um gatilho mais amplo: `actLateDeliveries`, **qualquer** item de um épico
comprometido com o roadmap (`anData().projItems`), sem exigir a tag.

No cenário do print: o item que empurrava CFD/Distribuição para julho/agosto pertencia ao mesmo épico
dos 5 itens reservados, mas **não tinha** a tag de capacidade do roadmap — fazia parte da coluna
"Projetada" (todos os itens do CT do épico), não da coluna "Capacidade"/Reserva. Por isso só CFD e
Distribuição reagiam a ele; o Burnup, com seu gatilho restrito à Reserva, nunca via esse item e seu eixo
ficava parado no último mês do semestre original.

## Decisão

O gatilho de extensão do eixo do Burnup Reserva passa a usar o mesmo helper `actLateDeliveries` do
CFD/Distribuição — **qualquer** item de um épico comprometido com o roadmap, entregue depois do fim do
semestre, estende o eixo, com ou sem a tag de capacidade. Como `entregues` (Reserva, categoria Vazão) é
sempre um subconjunto de `actLateDeliveries`'s população base (`anData().projItems`) — todo item da
Reserva vem de algum item do épico, nunca o contrário — checar só o conjunto mais amplo já cobre os dois
casos, sem precisar verificar os dois separadamente.

```js
let maxDeploy = null;
actLateDeliveries(st, ad).forEach(o => { if (!maxDeploy || o.deploy > maxDeploy) maxDeploy = o.deploy; });
```

**O que não muda**: os números "Entregue"/"Faltam" do resumo clicável continuam baseados só na Reserva
(`capItems`/`entregues`) — a decisão `0058` não é revista por esta. Só o **comprimento do eixo X** (e,
por consequência, onde a linha "fim do semestre" aparece) passa a refletir qualquer entrega tardia do
épico, não só da Reserva.

## Consequência

Os 3 quadrantes de linha/semana do Actionable (Burnup Reserva, CFD) e o de barras (Distribuição) agora
reagem de forma consistente ao mesmo conjunto de itens "tardios" — uma entrega depois do fim do semestre
de qualquer item do épico comprometido com o roadmap estende o eixo nos três, mesmo quando esse item
específico não é parte da Reserva do Burnup. O resumo "Entregue"/"Faltam" do Burnup pode, portanto,
mostrar um total menor que o escopo visual do gráfico estendido — isso é esperado: o resumo mede só a
Reserva, o gráfico agora dá contexto do épico inteiro.
