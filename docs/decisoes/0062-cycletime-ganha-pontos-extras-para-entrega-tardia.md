# 0062 — Actionable: CycleTime também ganha pontos extras (e linha "fim do semestre") para entrega tardia

## Contexto

Depois da correção da decisão `0061` (Burnup Reserva passou a estender o eixo pelo mesmo critério do
CFD/Distribuição), o usuário mandou outro print confirmando que Burnup Reserva, CFD e Distribuição já
estavam consistentes entre si — todos mostrando julho — mas apontou que **só o CycleTime** continuava
preso em junho, sem nenhum ponto além do fim do semestre.

## Investigação

O quadrante CycleTime (`actCtScatterData`/`actScatterSvg`) nunca fez parte do escopo das decisões `0060`
e `0061` — ele reaproveita deliberadamente a mesma amostra e janela do quadrante CycleTime do Report F4P
(`f4pSample`/`f4pWindow`, decisão `0013`), e não tem conceito de "mês"/"semana" no eixo X: cada ponto é
um item individual, posicionado pela sua própria data de entrega dentro de uma janela de datas contínua
(`window.from` a `window.to`). Um item entregue depois de `window.to` simplesmente nunca entra na
amostra (`f4pSample` filtra `o.deploy <= to`) — não é um problema de eixo que "para cedo demais", é a
amostra em si que não inclui o item.

Mudar `f4pSample`/`f4pWindow` para incluir esses itens alteraria também os números "Reserva"/"Atual
(P95)" do quadrante CycleTime do **Report F4P** (§12.2), que reaproveita exatamente as mesmas funções —
um efeito colateral fora do pedido do usuário (ele só queria que o item tardio aparecesse "no gráfico do
Actionable", não uma mudança na métrica compartilhada com o Report F4P).

## Decisão

O CycleTime do Actionable ganha o mesmo tipo de extensão visual que o Burnup Reserva/CFD já têm, mas sem
tocar a amostra que define Reserva/Atual:

- **Itens "tardios"**: itens de um épico comprometido com o roadmap (`anData().projItems`), já
  concluídos (`o.ct != null`), dos mesmos tipos usados pela amostra (`CFG.f4p.types`), mas com
  `o.deploy` depois de `window.to` (fim da janela original).
- Esses itens aparecem como **pontos extras** no gráfico de dispersão — mesmo estilo visual dos pontos
  da amostra (cor conforme acima/abaixo da Reserva) — e o eixo X estende até a entrega mais tardia, com
  uma linha vertical "fim do semestre" marcando o limite real da janela original (`actSemEndLineAt`,
  generalização de `actSemEndLine` para um eixo de posição contínua, em vez de um índice categórico).
- **Reserva** e **Atual (P95)** continuam calculados só sobre `f4pSample` (a amostra original) — os
  pontos extras nunca entram nessas duas contas, preservando intacta a paridade com o Report F4P.

## Consequência

Os 4 quadrantes do Actionable agora reagem de forma visualmente consistente a uma entrega tardia de
qualquer item de um épico comprometido com o roadmap: Burnup Reserva e CFD estendem o eixo com uma linha
"fim do semestre"; CycleTime ganha pontos extras com a mesma linha; Distribuição Vazão por mês (gráfico
de barras) ganha um mês extra com ícone de alerta. Em nenhum dos quatro a métrica "oficial" do quadrante
(Entregue/Faltam no Burnup, Reserva/Atual no CycleTime) muda — só o contexto visual se amplia.
