# 0015 — Report F4P Urgente: corrige contagem sem limite de data no semestre em curso

## Contexto

Em produção (dados reais do Azure DevOps), o Quadrante Urgente mostrou números muito maiores do que o esperado (ex.: 249 itens para um time que usa a tag Expedite raramente, com Meta configurada em 3). O usuário suspeitou de contagem duplicada por ID.

## Investigação

- Checagem direta no console do navegador (`[...S.model.ops.values()].filter(...)`) confirmou: **nenhum ID duplicado** dentro do time — a hipótese de recontagem por ID não se confirmou, o `Map` de itens já é deduplicado por `time:id`.
- A amostra de itens contados mostrou tags **genuinamente** batendo (`['BO/Retaguarda','deploy','SUSTENTAÇÃO','urgente','v06']`, por exemplo) — não era falso positivo de correspondência de texto.
- A causa real: a decisão `0014` definiu o Realizado do semestre em curso como "contagem ao vivo, sem filtro de data" — ou seja, somava **todo item que já teve a tag em qualquer momento da história do time**, incluindo itens fechados há anos. Um time antigo acumula isso com o tempo mesmo usando a tag raramente por período.

## Primeira correção (errada) e o alerta do usuário

A primeira tentativa de correção limitou os itens fechados do semestre em curso ao período **desde o início do semestre selecionado** (ex.: 1/jul se "2026 2º Semestre" estiver em curso) até hoje. Isso resolvia o sintoma, mas o usuário apontou o problema certo: a decisão `0013` já tinha definido, para CycleTime/Variabilidade, que o semestre em curso usa uma **janela corrida dos últimos `CFG.f4p.months` meses a partir de hoje** — não os dias corridos desde o início do semestre. A primeira correção inventou uma terceira variante de janela em vez de reaproveitar a que já existia, quebrando a consistência entre quadrantes.

## Decisão final

1. A regra de janela por semestre (decisão `0013`) deixa de ser tratada como "regra do CycleTime/Variabilidade" e passa a ser a **regra geral de qualquer quadrante do Report F4P que precise de um período** — documentada como tal em `docs/regras-de-negocio.md` §12.1, e extraída para uma função só, `f4pWindow(st)` (`src/js/23-report-f4p.js`), que `f4pSample` (CycleTime/Variabilidade) e `f4pUrgentRealizado` (Urgente) passam a chamar em vez de recalcular a janela cada um do seu jeito.
2. Realizado do Urgente: **itens abertos** com a tag contam sempre (sem limite de data — continuam sendo risco agora, "não importa o estado" da resposta original do usuário). **Itens fechados** só contam se `o.deploy` cair dentro de `f4pWindow(st)`: últimos N meses corridos a partir de hoje (semestre em curso), ou o período exato do semestre (semestre já encerrado).

## Consequências

- Times antigos com uso histórico ocasional da tag Expedite não acumulam mais itens de anos atrás no Realizado do semestre em curso.
- Qualquer quadrante futuro que precise de uma amostra por período (Eficiência de fluxo, Vazão, etc.) deve chamar `f4pWindow`, não recriar a lógica — isso é agora explícito em `docs/regras-de-negocio.md` §12.1, exatamente para evitar que este tipo de divergência se repita.
- Teste de regressão em `tests/test_report_f4p.py` (`test_urgente_semestre_atual_ignora_fechados_fora_da_janela_de_meses`): item fechado fora da janela de N meses não conta; dentro da janela ou ainda aberto, conta.
