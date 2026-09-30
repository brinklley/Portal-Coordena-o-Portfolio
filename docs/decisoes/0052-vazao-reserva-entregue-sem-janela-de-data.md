# 0052 — Vazão: Reserva entregue deixa de exigir entrega dentro do período exato do semestre

## Contexto

O usuário mandou um print do modal "Vazão · MOBILE · reserva · 2º semestre 2026" (Report F4P, quadrante
5) mostrando o item #44575 ("Tela de configurações - Vincular login automático com biometria do
dispositivo"), com Situação "Vazão · 28/04/2026" — ou seja, entregue no **1º semestre de 2026**, fora do
período filtrado (2º semestre). O item aparecia corretamente na lista de **Reserva** (que desde a
decisão `0048` não olha mais data, só tag + tipo + compromisso do épico com o roadmap), mas o usuário
observou que ele **não** contava na **Reserva entregue**, mesmo já estando entregue — quebrando a
conferência cruzada com a Visão analítica, que também não aplica essa janela de data.

Pedido do usuário (resumido): contar esse item na Reserva entregue mesmo que a data de entrega esteja
fora do período do roadmap filtrado, desde que o **épico pai** esteja dentro do compromisso de roadmap
(Interno ou Executivo) do semestre selecionado — para que Visão analítica e Report F4P "batam os dados
entregues".

## Diagnóstico

`f4pVazaoReservaEntregueItems(team, st)` (`src/js/23-report-f4p.js`) delegava para `f4pVazaoOps(team,
st)` — a mesma função que define o **Realizado**, cuja regra (decisão `0022`) exige `o.deploy` dentro do
período exato do semestre (`f4pExactSemesterWindow`). Isso fazia a Reserva entregue herdar essa
exigência de data mesmo depois da decisão `0048` ter tirado essa mesma restrição da Reserva — deixando
as duas listas (Reserva e Reserva entregue) com critérios de data inconsistentes entre si, e a Reserva
entregue inconsistente com a Capacidade da Visão analítica (que nunca teve essa janela).

## Decisão

Redefinir `f4pVazaoReservaEntregueItems` como o subconjunto da própria **Reserva**
(`f4pVazaoReservaItems`, decisão `0048`) que já está na categoria de fluxo **Vazão** (`catOf(o) ===
"vazao"`), sem nenhuma checagem de data:

```js
function f4pVazaoReservaEntregueItems(team, st){
  return f4pVazaoReservaItems(team, st).filter(o => catOf(o) === "vazao");
}
```

Como a Reserva já exige tipo (`CFG.ctTypes`), tag de capacidade (`CFG.anTag`) e épico comprometido com o
semestre selecionado (`f4pEpiCompromissoBate`), a Reserva entregue passa a ser um subconjunto da Reserva
**por construção** (antes só coincidia numericamente, por acaso de configuração — os dois conjuntos
partiam de bases diferentes, `CFG.ctTypes` vs. `CFG.f4p.types`).

**O Realizado não muda.** Ele mede algo diferente por definição — vazão de calendário do semestre
(quanto foi entregue dentro do período, independente de estar ou não no roadmap) — e continua exigindo
`o.deploy` dentro da janela exata. Um item como o #44575 do relato passa a contar na Reserva e na
Reserva entregue, mas continua fora do Realizado do 2º semestre (ele entrou no Realizado do 1º
semestre, quando foi de fato entregue).

Também ajustados:
- Rótulo do modal de clique da Reserva entregue: trocado de `f4pExactSemesterLabel(st)` (intervalo de
  datas) para `semLong(f4pSemester())` ("2º semestre 2026") — mesmo ajuste que a decisão `0048` já tinha
  feito para o modal da Reserva, já que o número deixou de depender de uma janela de datas.
- Texto de ajuda (tooltip) do quadrante, reescrito para não descrever mais a Reserva entregue como
  "subconjunto do Realizado".

## Consequência

Reserva e Reserva entregue do Report F4P voltam a bater com a Capacidade/Status da Visão analítica em
qualquer cenário de item entregue fora da janela exata do semestre, mas com o épico comprometido com o
roadmap filtrado — o problema relatado pelo usuário. O Realizado continua com seu propósito original
(vazão por calendário) e não foi alterado.
