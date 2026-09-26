# 0017 — Report F4P Urgente: janela própria por período exato do semestre

## Contexto

Depois da correção da decisão `0015` (Realizado do semestre em curso passou a usar `f4pWindow`, a janela corrida dos últimos `CFG.f4p.months` meses a partir de hoje — a mesma regra geral do §12.1, usada por CycleTime/Variabilidade), o usuário revisou os dados em produção e encontrou um novo problema, desta vez na própria regra, não num bug de implementação: ao clicar no Realizado do time FL1 - Core_API (Meta = 3, Realizado = 4), a lista de itens considerados mostrava datas de fechamento em 28/04, 08/06, 15/07 e 09/08/2026 — com "2026 2º Semestre" (1/jul a 31/dez) selecionado no filtro, os itens de 28/04 e 08/06 são do **semestre anterior**, mas entraram na contagem porque caem dentro da janela corrida de 6 meses a partir de hoje.

## Decisão

O Realizado do Urgente **deixa de usar `f4pWindow`** (a janela geral do §12.1) e passa a ter uma janela própria, `f4pUrgentWindow` (`src/js/23-report-f4p.js`): sempre o **período exato do semestre selecionado no filtro** — 1/jan a 30/jun ou 1/jul a 31/dez —, esteja ele em curso ou já encerrado. Não há mais distinção de janela entre semestre em curso e semestre encerrado para este quadrante: os dois usam o mesmo cálculo (início e fim do semestre). Sem semestre reconhecido no filtro (caso extremo, sem `start`/`end`), cai na janela corrida de `f4pWindow` por segurança, mesmo padrão do resto do Report F4P nesse cenário.

Isso é uma divergência deliberada da regra geral do §12.1: enquanto CycleTime/Variabilidade continuam usando a janela corrida de N meses para o semestre em curso (decisão `0013`), o Urgente usa sempre o período exato do semestre. A meta do Urgente é um teto **por semestre** ("itens Expedite aceitáveis no semestre" — decisão `0014`), então a contagem tem que respeitar as fronteiras do semestre, não uma janela corrida que pode incluir dias do semestre anterior.

Continua valendo, sem mudança, a regra de itens abertos (contam sempre, qualquer que seja a data) e fechados (só contam com `o.deploy` dentro da janela) — decisão `0015`, item 2; só a janela usada para os fechados no semestre em curso mudou.

## Consequências

- `docs/regras-de-negocio.md` §12.1 deixa de listar Urgente entre os quadrantes que usam a regra geral, e §12.4 passa a descrever `f4pUrgentWindow` como a janela própria do quadrante.
- `f4pUrgentPeriodLabel` substitui `f4pPeriodLabel` no tooltip do Realizado, no título do modal de itens e na nota de rodapé do painel — todos passam a mostrar o período exato do semestre (ex.: "01/07/2026 a 31/12/2026"), nunca mais "últimos 6 meses", para o Urgente.
- Testes em `tests/test_report_f4p.py` atualizados: `test_urgente_semestre_atual_conta_abertos_e_fechados` e `test_urgente_semestre_atual_ignora_fechados_antes_do_inicio_do_semestre` (renomeado; antes testava a janela de meses, agora testa a fronteira do início do semestre) passam a usar o estado real do semestre em curso (`f4pSemesterState()`) em vez de um `{kind:"current"}` sem `start`/`end`.
- Se no futuro outro quadrante precisar de uma meta por semestre (não uma amostra geral), deve seguir este mesmo padrão — janela própria por período exato do semestre — em vez de reaproveitar `f4pWindow`.

> **Atualização (generalizada para o Technical Story)**: exatamente essa necessidade apareceu no Quadrante 4 (Technical Story) — ver `docs/decisoes/0018-report-f4p-quadrante-technical-story.md`. Em vez de reimplementar a mesma janela, `f4pUrgentWindow`/`f4pUrgentPeriodLabel` foram renomeadas para `f4pExactSemesterWindow`/`f4pExactSemesterLabel` (genéricas) e passaram a ser reaproveitadas pelos dois quadrantes, junto com uma nova função compartilhada para "o que conta como fechado dentro do período", `f4pSemesterGoalItems`.
