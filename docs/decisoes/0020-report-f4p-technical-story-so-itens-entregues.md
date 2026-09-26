# 0020 — Report F4P Technical Story: só conta itens já entregues (categoria de fluxo Vazão)

## Contexto

Com o Quadrante 4 (Technical Story, decisão `0018`) e a Situação por categoria de fluxo (decisão `0019`) já implementados, o usuário revisou a regra em produção e apontou uma inconsistência: o Realizado do Technical Story herdava a regra do Urgente — itens abertos contam sempre, fechados só dentro do período do semestre — mas isso não fazia sentido para este quadrante. Pedido do usuário: "é necessário ajustar a regra... alterando para que esteja no filtro somente os itens que estão mapeados como Vazão (entregue), não fazendo parte do cálculo... os itens mapeados em Nenhum (backlog), Discovery ou WIP".

(O usuário se referiu ao quadrante como "Technical Solution" na mensagem, mas a única regra em ajuste no Report F4P é a do Quadrante 4, "Technical Story" — não existe quadrante "Technical Solution" no painel; "Technical Solution" é apenas um tipo de item usado em `CFG.ctTypes`, sem relação com este quadrante.)

## Decisão

O Realizado do Technical Story **deixa de contar itens abertos**. Só entram na contagem itens que:

1. são do tipo Technical Story (regra já existente, decisão `0018`);
2. estão na categoria de fluxo **Vazão** — a mesma classificação por coluna que a Situação já mostra (`catOf`, decisão `0019`), mapeada pelo usuário em Configurações › fluxo dos times; **e**
3. têm `o.deploy` dentro do período exato do semestre selecionado (`f4pExactSemesterWindow`, sem mudança).

Itens em Backlog (`none`), Discovery ou WIP **não contam**, mesmo que estejam abertos há muito tempo — ao contrário do Urgente, que continua contando itens abertos como risco em aberto. Essa é a única divergência real de regra entre os dois quadrantes agora: a meta do Urgente mede "quanto risco/exposição existe agora"; a meta do Technical Story mede "quanto foi entregue no período".

Um item cuja coluna está mapeada como Vazão mas que ainda não tem `o.deploy` preenchido (config incomum, mas possível — categoria de coluna e "Entra no CT" são configurações independentes, ver decisão `0019`) também não conta: sem uma data de saída, não há como confirmar que a entrega caiu dentro do semestre selecionado.

## Consequências

- `src/js/23-report-f4p.js`: `f4pTsItems` deixa de usar a função compartilhada `f4pSemesterGoalItems` (que mantém a regra "aberto sempre conta" do Urgente) e passa a filtrar diretamente por `catOf(o) === "vazao"` e `o.deploy` dentro do período.
- `f4pSemesterGoalItems` volta a ser usada só pelo Urgente; o comentário que a descrevia como compartilhada foi ajustado.
- Tooltip do Realizado, nota de rodapé do painel e comentários de código atualizados para descrever a nova regra do Technical Story separadamente da do Urgente.
- Testes em `tests/test_report_f4p.py` (seção "Quadrante 4"): reescritos para dar um fluxo próprio (Backlog/Discovery/WIP/Vazão) a cada time sintético via `S.model.teamFlow` + `CFG.flow`, permitindo testar a categoria de cada item com precisão; cobrem itens em cada categoria, a fronteira do início do semestre e o semestre já encerrado, todos agora exigindo a categoria Vazão para contar.
- `docs/regras-de-negocio.md` §12.5, `docs/backlog/report-f4p.md` atualizados para descrever a nova regra do Realizado.
