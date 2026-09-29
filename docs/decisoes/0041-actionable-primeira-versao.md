# 0041 — Actionable: primeira versão (MVP), CycleTime e Burnup Reserva

## Contexto

O usuário pediu um novo menu expansível, "Actionable", com quadrantes de métricas para o período do
roadmap (interno ou executivo) e o time selecionados — inspirado no design do Report F4P. A estrutura
final prevista é 4 quadrantes em 2 colunas; só os dois primeiros (CycleTime e Burnup Reserva) foram
detalhados nesta rodada — os outros dois ficam para uma conversa futura.

Antes de implementar, levantei quatro decisões de design que não estavam claras no pedido original e
perguntei ao usuário em vez de assumir (CLAUDE.md e o próprio pedido explicitamente pediam isso):

1. Onde o menu deveria viver na interface.
2. O que exatamente o scatterplot do CycleTime plota (amostra, eixos).
3. O que conta como "reservado" no Burnup — o total/escopo do gráfico.
4. O formato do gráfico do Burnup.

O usuário escolheu, em cada uma, a opção que eu havia recomendado com base nas regras já existentes do
Report F4P e da Visão analítica (ver respostas abaixo).

## Decisões de design

### Onde o painel vive

Nova aba lateral (`#actTab`), ao lado de Visão analítica e Report F4P, com o mesmo gate de habilitação
(`anEnabled()`: Time + Roadmap interno ou executivo) e a mesma checagem de semestre futuro do Report
F4P (`f4pSemesterState().kind !== "future"`) — função própria `actEnabled()`, mesma lógica de
`f4pEnabled()`. Como a Visão analítica, mostra **um time por vez** (o selecionado no filtro), não todos
os times lado a lado como o Report F4P — os quadrantes MVP (dispersão de pontos, burnup) não fariam
sentido numa tabela com uma coluna por time.

Os três painéis (Visão analítica, Report F4P, Actionable) são mutuamente exclusivos: abrir um fecha os
outros dois (mesma convenção que já existia entre Visão analítica e Report F4P).

### Quadrante 1 · CycleTime (dispersão)

Em vez de inventar uma amostra ou regra própria, reaproveita literalmente `f4pSample`/`f4pMetrics`/
`limitsOf` do quadrante CycleTime do Report F4P (§12.2 de `docs/regras-de-negocio.md`) — a mesma
amostra (itens concluídos, tipos configurados, dentro da janela do semestre) e a mesma Reserva (CT
máximo do time). Cada item da amostra vira um ponto (X = data de entrega, Y = CT em dias) em vez de
resumir tudo num único P95; o P95 (o "Atual" do quadrante original) entra como uma segunda linha de
referência, para comparar a distribuição real por trás do número resumido.

### Quadrante 2 · Burnup Reserva

A parte mais delicada da conversa: o quadrante Vazão do Report F4P (§12.6) já tem um conceito de
"Reserva", mas ele só existe dentro do que **já foi entregue** — não dá para calcular "quanto falta"
a partir dele, porque por construção Reserva ⊆ Realizado. Para um burnup fazer sentido (mostrar quanto
falta), o "Reservado" (escopo) precisa incluir itens em qualquer status, entregues ou não — exatamente
o conceito de **Capacidade** já usado pela Visão analítica (§10): itens com a tag de capacidade do
roadmap (`CFG.anTag`) nos épicos do roadmap do time+semestre selecionado. Reaproveitei `anData()`
diretamente (`capItems`) em vez de duplicar essa lógica.

"Entregue" é o subconjunto desse conjunto já na categoria de fluxo Vazão, acumulado mês a mês dentro
do semestre selecionado (limite de fim de mês inclusivo — um item entregue no último dia do mês já
conta nesse mês). "Faltam" é a diferença.

**Limitação assumida, sem solução no momento**: o portal não guarda histórico de quando um item entrou
no roadmap (quando ganhou a tag de capacidade), então não há como saber se o escopo cresceu ao longo do
semestre — a linha do Reservado no burnup é sempre a contagem **atual**, mostrada como uma reta
constante, não uma curva real de "escopo ao longo do tempo" como um burnup clássico teria numa
ferramenta com histórico completo. Documentado explicitamente no texto de apoio do quadrante, não
escondido.

## Implementação

- `src/js/24-actionable.js` (novo arquivo, depois do Report F4P na ordem alfabética): estado `ACT`,
  gate `actEnabled()`, dados e SVG dos dois quadrantes, `renderActionable()`, abrir/fechar/exclusão
  mútua.
- Gráficos em **SVG puro**, sem biblioteca externa (regra do projeto: nada de bibliotecas externas em
  tempo de execução) — funções `actScatterSvg()`/`actBurnupSvg()` calculam a escala e desenham
  manualmente eixos, linhas de referência e pontos/linhas, no mesmo espírito das linhas do whiteboard
  (`07-barbantes.js`).
- Reaproveita o design visual do Report F4P (`.f4p-grid`, `.f4p-col`, `.f4p-card`, `.f4p-note`,
  `.f4p-real`) — só as classes específicas dos gráficos (`.act-*`) são novas.
- `f4pItemsModal()` (já existente) é reaproveitado para a transparência de clique nos números do
  Burnup, igual à Visão analítica e ao Report F4P.

## Limitação de interface encontrada (fora do escopo desta mudança)

Durante os testes, notei que a coluna de abas laterais (`.side-tabs`, `z-index:44`) fica **coberta**
por qualquer um dos três painéis quando aberto (`.an-panel`, `z-index:46`, ambos começando em
`left:0`) — ou seja, hoje não dá para clicar direto numa aba diferente para trocar de painel; é preciso
fechar o painel atual primeiro (botão «). Confirmei que isso já valia para Visão analítica ↔ Report F4P
antes desta mudança (nenhum teste existente clica num desses botões com o outro painel aberto) — não é
uma regressão desta PR, então não mexi nisso aqui. Vale considerar corrigir separadamente se incomodar
no uso real.

## Testes

`tests/test_actionable.py` (15 testes): gate de habilitação (com e sem semestre futuro), a dispersão de
CycleTime usa a mesma amostra/Reserva/Atual do Report F4P, pontos acima da Reserva destacados, clique
no ponto navega, o Reservado do Burnup bate com a Capacidade da Visão analítica, acumulado mês a mês
(incluindo o caso de borda do último dia do mês), resumo e cliques de transparência, os quadrantes 3 e
4 mostram "em definição", e a exclusão mútua entre os três painéis.

## Próximos passos

Quadrantes 3 e 4 do Actionable: a definir numa conversa futura com o usuário.
