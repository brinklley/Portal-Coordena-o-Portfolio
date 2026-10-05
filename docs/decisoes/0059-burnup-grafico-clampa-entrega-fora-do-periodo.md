# 0059 — Actionable: gráfico do Burnup Reserva encaixa entrega fora do período no mês mais próximo

## Contexto

O usuário mandou um novo print do quadrante Burnup Reserva (Actionable, time BO, "1º semestre 2026"),
agora depois da decisão `0058` já aplicada: o resumo lia "11 reservados · 11 entregues · 0 faltam",
mas a linha acumulada do gráfico terminava visivelmente **abaixo** da reta de Reservado em junho, com
uma chamada destacando a diferença entre onde a linha parava e onde o escopo estava. Mensagem do
usuário: "Mas o gráfico burnup continua não batendo".

## Investigação

Era consequência direta e esperada da própria decisão `0058`: ela tornou "Entregue" (o número do
resumo) independente de a saída ter caído dentro do período exato do semestre — qualquer entrega
(adiantada ou tardia) passou a contar. Só que o gráfico (`cumulative`, um ponto por mês do eixo X do
burnup) continuou, deliberadamente, só contando entregas cujo mês caía dentro dos meses do próprio
semestre — comentário explícito no código da `0058` dizia "não é uma limitação arbitrária, é inerente
ao gráfico: não existe um mês no eixo X para plotar uma entrega de outro semestre".

Essa escolha, defensável isoladamente, cria exatamente o sintoma relatado: assim que existe pelo menos
1 item cuja entrega caiu fora do período (contado em "Entregue" pela `0058`, mas sem mês para plotar),
`entreguesN` passa a ser maior do que o valor máximo que `cumulative` pode algum dia alcançar — a linha
nunca chega na reta de Reservado, mesmo com o resumo já mostrando 100% entregue (0 faltam). O gráfico
"parece furado"/inconsistente com o número ao lado dele, apesar de os dois estarem, cada um à sua
maneira, corretos.

## Decisão

O gráfico (`cumulative`) passa a sempre terminar no mesmo total do resumo "Entregue"
(`cumulative[cumulative.length - 1] === entreguesN`, sempre). Uma entrega fora do período do semestre
é "encaixada" no mês mais próximo **dentro do próprio eixo X** do gráfico:

- se a saída foi **antes** do início do semestre → conta a partir do 1º mês do gráfico;
- se a saída foi **depois** do fim do semestre → conta a partir do último mês do gráfico.

```js
const mesEfetivo = o => !o.deploy ? null
  : o.deploy < inicioPrimeiroMes ? inicioPrimeiroMes
  : o.deploy > fimUltimoMes ? fimUltimoMes
  : o.deploy;
const cumulative = months.map(m => {
  const fim = new Date(m.getFullYear(), m.getMonth() + 1, 0);
  return entregues.filter(o => { const d = mesEfetivo(o); return d && d <= fim; }).length;
});
```

A entrega continua contando (nunca deixa de aparecer no acumulado), só não aparece exatamente no mês
real em que aconteceu — que, por definição, nem existe no eixo X deste gráfico (ele só cobre os meses
do semestre selecionado).

## Consequência

O gráfico do Burnup Reserva sempre alcança, no seu último ponto, o mesmo número do resumo "Entregue" —
nunca mais fica "para baixo" da reta de Reservado quando o resumo já indica 100% entregue. Isso muda o
valor de `cumulative` no mês de borda para itens entregues fora do período (antes, esse mês não contava
a entrega; agora conta) — o teste da decisão `0058`
(`test_burnup_entrega_fora_do_periodo_do_semestre_ainda_conta_como_entregue`) foi atualizado para
refletir esse novo valor. Novo teste cobrindo o encaixe nas duas pontas do eixo X (entrega antes do
início e depois do fim do mesmo semestre):
`test_burnup_grafico_termina_no_mesmo_total_do_resumo_entregue`.
