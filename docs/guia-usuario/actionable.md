# Actionable — guia do usuário

## O que é

O Actionable é a grade de 4 gráficos de métricas acionáveis **de um time por vez** — diferente do
Report F4P (que sempre mostra os 4 times juntos), o Actionable é igual à Visão Analítica nesse ponto:
um time e um semestre do roadmap por vez. É a tela para acompanhar visualmente como a entrega do time
está evoluindo ao longo do semestre, não só o número final.

## Como habilitar

Mesma regra da Visão Analítica e do Report F4P: a aba "Actionable" só habilita com **Time** e
**Roadmap** (interno ou executivo) selecionados juntos nos filtros, e fica desabilitada se o semestre
escolhido ainda não começou.

## Os 4 quadrantes

1. **CycleTime** (dispersão): um ponto por item concluído (eixo X = data de entrega, eixo Y =
   CycleTime em dias), com as linhas de Reserva e Atual (P95) — mesma amostra do quadrante CycleTime
   do Report F4P. Pontos acima da Reserva ficam destacados. Clique num ponto para ir até o item.
2. **Distribuição Vazão por mês**: para cada mês do semestre, uma barra mostrando que fração do que
   foi entregue naquele mês é User Story, Technical Story ou "demais" (tipos de bug ficam de fora da
   conta). Mês sem entrega aparece como barra cinza "0,00%".
3. **Burnup Reserva**: gráfico clássico de burnup — uma linha reta com o total Reservado (mesmo
   conceito de Capacidade da Visão Analítica) e uma linha crescente com o Entregue acumulado mês a
   mês. "Faltam" é o que ainda não chegou em Vazão.
4. **CFD** (Cumulative Flow Diagram): área empilhada mostrando, semana a semana, quantos itens do
   time já passaram por cada categoria de fluxo (Nenhum, Discovery, WIP, Vazão) — reconstruído a
   partir do histórico real de quando cada item entrou em cada coluna, não do estado de hoje.

## Perguntas frequentes ("não está batendo com o que eu esperava")

### "Selecionei o Time, mas o menu continua desabilitado. Por quê?"

Falta o **Roadmap**. A aba só habilita com Time **e** Roadmap (interno ou executivo) selecionados
juntos. Veja "Como habilitar" acima.

### "No Burnup Reserva, um item em 'Faltam' já mostra Situação 'Vazão · DD/MM/AAAA'"

Isso não deveria mais acontecer: "Faltam" significa só itens que **ainda não** chegaram em Vazão —
qualquer item já em Vazão conta como "Entregue" no resumo, **mesmo que a entrega tenha caído fora do
período exato do semestre** (adiantada ou tardia). Se você ainda vir essa inconsistência, é sinal de
que algo não está atualizado — a regra atual não permite um item "Vazão" aparecer em "Faltam".

### "O gráfico do Burnup Reserva (ou do CFD) parece parar antes de chegar na linha de Reservado"

Verifique se existe uma **linha vertical "fim do semestre"** no gráfico — se existir, é sinal de que o
eixo foi **estendido** além do semestre original, porque um item de um épico comprometido com o
roadmap foi entregue depois do fim do período. O gráfico continua até o mês/semana real dessa entrega,
e a linha marca onde o semestre comprometido de fato terminou — os pontos à direita dela são entregas
fora do período, mas ainda contam no total. Se o gráfico "parece furado" sem essa linha aparecer, pode
ser que a entrega tardia pertença a um item do mesmo épico que não está na Reserva propriamente dita
(sem a tag de capacidade) — mesmo assim, ele deveria estender o eixo.

### "Um item entregue depois do fim do semestre não aparece em lugar nenhum do CycleTime do Actionable"

Ele aparece sim, mas como um **ponto extra** além da janela normal de amostra, com a mesma linha
vertical "fim do semestre" dos outros gráficos — só que esse ponto **não entra** no cálculo de Reserva
nem de Atual (P95): esses dois números continuam calculados só sobre a amostra original, igual ao
Report F4P (mudar isso mudaria também os números do Report F4P, que usa a mesma amostra). Ou seja: o
item aparece no gráfico, mas não altera as duas linhas de referência.

### "Um mês da Distribuição Vazão por mês tem um ícone de alerta (⚠) no rótulo"

Significa que esse mês está **além dos 6 meses normais** do semestre, e só apareceu porque um item de
um épico comprometido com o roadmap foi entregue nesse mês (fora do período). Diferente do Burnup
Reserva/CFD (que desenham uma linha vertical), aqui é um gráfico de barras — não há como "cortar"
visualmente, então o aviso vem como ícone no rótulo do mês. O conteúdo da barra desse mês segue a
mesma regra de qualquer outro mês (todas as entregas do time naquele mês civil), só a decisão de
**mostrar** o mês é que depende do item do épico comprometido.

## Cenários

### Habilitação da aba

**Cenário: Time sem Roadmap não habilita a aba**
- Dado que nenhum Roadmap (interno nem executivo) está selecionado
- Quando o usuário seleciona um Time
- Então a aba "Actionable" continua desabilitada

### Entrega tardia estende o gráfico em vez de desaparecer

**Cenário de sucesso: entrega dentro do semestre, sem extensão**
- Dado um item reservado entregue dentro do período do semestre selecionado
- Quando o Burnup Reserva é calculado
- Então o gráfico mostra a entrega no mês real, sem precisar estender o eixo, e sem a linha "fim do
  semestre"

**Cenário de comportamento inesperado: entrega depois do fim do semestre**
- Dado um item de um épico comprometido com o roadmap, entregue 2 meses depois do fim do semestre
  selecionado
- Quando o Burnup Reserva (ou o CFD) é calculado
- Então o gráfico estende o eixo até o mês/semana real dessa entrega, com uma linha vertical "fim do
  semestre" marcando onde o período comprometido terminou — a entrega continua contando, só não
  aparece no mês original do semestre

## Regras de negócio relacionadas

- `docs/regras-de-negocio.md` §13 (Actionable, com uma subseção por quadrante — §13.1 a §13.4).
- Decisões: `docs/decisoes/0041` (primeira versão), `0044` a `0047` (quadrantes 2 a 4), e a sequência
  mais recente sobre entrega tardia de item de épico comprometido —
  [`0058`](../decisoes/0058-burnup-entrega-fora-do-periodo-conta-como-entregue.md),
  [`0059`](../decisoes/0059-burnup-grafico-clampa-entrega-fora-do-periodo.md),
  [`0060`](../decisoes/0060-burnup-cfd-dist-estendem-eixo-para-entrega-tardia.md),
  [`0061`](../decisoes/0061-burnup-eixo-reage-a-qualquer-item-do-epico-comprometido.md),
  [`0062`](../decisoes/0062-cycletime-ganha-pontos-extras-para-entrega-tardia.md).
- Detalhe exaustivo de cobertura de teste: [`docs/testes/actionable.md`](../testes/actionable.md).
