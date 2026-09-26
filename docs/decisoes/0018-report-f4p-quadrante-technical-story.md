# 0018 — Report F4P: Quadrante 4, Technical Story (meta vs. realizado)

## Contexto

Com Urgente (Quadrante 3) implementado e ajustado (decisões `0014`, `0015`, `0017`), o usuário pediu o próximo quadrante calculado: Technical Story, descrito como "praticamente o mesmo comportamento do quadrante Urgente", com as diferenças abaixo.

## Decisões

1. **O que conta**: itens do **tipo Technical Story**, em vez de uma tag — `norm(o.type) === "technical story"`. Tipo fixo, não configurável (ao contrário de `CFG.f4p.types`, que é só de CycleTime/Variabilidade, e da tag do Urgente, que é escolhida em Configurações).

2. **Meta**: número inteiro configurável **por time** (`CFG.f4p.teams[time].tsMeta`, mesmo padrão de `urgentMeta`), mas com uma diferença deliberada: o usuário pediu um **valor padrão de 6 itens** quando o time não cadastra a própria meta. Isso é o oposto do Urgente, que fica "sem meta" (e sem cor) nesse caso — para o Urgente não havia um padrão numérico sensato (decisão `0014`); para Technical Story, o usuário definiu um. Consequência prática: a célula de Technical Story **sempre** mostra uma meta e **sempre** colore o Realizado (nunca "--"), diferente do Urgente.

3. **Janela do Realizado**: o usuário pediu explicitamente "o filtro por semestre deve pegar o primeiro dia do semestre como entrada e o último dia do semestre como saída" — ou seja, a mesma janela por período exato do semestre que o Urgente já usa desde a decisão `0017`, não a janela corrida de N meses (`f4pWindow`, §12.1). Como agora dois quadrantes precisam exatamente da mesma regra, a função foi **generalizada**: `f4pUrgentWindow` (específica do Urgente) virou `f4pExactSemesterWindow` (genérica, `src/js/23-report-f4p.js`), usada por Urgente e Technical Story. Mesma coisa para o rótulo do período (`f4pUrgentPeriodLabel` → `f4pExactSemesterLabel`). O critério de o que conta como "fechado dentro do período" também foi extraído para uma função compartilhada, `f4pSemesterGoalItems(ops, st)`, usada por `f4pUrgentItems` e pela nova `f4pTsItems` — evita duas reimplementações divergentes do mesmo cálculo (o motivo do bug corrigido pela decisão `0015`).

4. **Cor do Realizado**: igual ao Urgente e ao CycleTime — vermelho quando ultrapassa a Meta, verde quando está na meta ou abaixo.

5. **Sem seta de tendência**: o usuário não pediu uma para este quadrante; ao contrário do Urgente, a célula de Technical Story não tem indicador de tendência.

6. **Transparência**: o número do Realizado é clicável e abre a lista dos itens exatos contados (mesmo modal do Urgente, `f4pItemsModal`), cada um levando direto até o item no quadro — igual à decisão `0016`.

## Consequências

- Nova configuração no CFG: `f4p.teams[time].tsMeta` (inteiro ≥ 0, independente de `min`/`max`/`urgentMeta`). Entra automaticamente em exportação/importação.
- `src/js/23-report-f4p.js`: `f4pTsOps`, `f4pTsItems`, `f4pTsRealizado`, `f4pTsCell`; `f4pExactSemesterWindow`/`f4pExactSemesterLabel` (renomeadas de `f4pUrgentWindow`/`f4pUrgentPeriodLabel`) e `f4pSemesterGoalItems` (extraída de `f4pUrgentItems`) passam a ser compartilhadas pelos dois quadrantes.
- `src/js/01-configuracao-e-regras.js`: `f4pTsMetaOf` (com o padrão 6, diferente de `f4pUrgentMetaOf`, que retorna `null` sem meta cadastrada).
- `src/js/19-tela-configuracoes.js`: nova coluna "Meta de Technical Story no semestre" na tabela de times do Report F4P.
- Testes em `tests/test_report_f4p.py` (seção "Quadrante 4 · Technical Story"), espelhando os testes do Urgente: contagem por tipo, janela por período exato do semestre (em curso e encerrado), meta com e sem valor próprio (testando o padrão 6), clique no número e navegação até o item, persistência da configuração.
- Documentação: `docs/regras-de-negocio.md` §12.5 (nova), `docs/backlog/report-f4p.md`, `docs/configuracoes.md`, `docs/telas.md`, `CLAUDE.md` (próxima tarefa) e ponteiro de atualização em `docs/decisoes/0017-report-f4p-urgente-periodo-exato-do-semestre.md`.
