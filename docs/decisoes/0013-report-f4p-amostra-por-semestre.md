# 0013 — Report F4P: a amostra do CT passa a depender do semestre selecionado

## Contexto

A decisão `0011` (confirmando o que `docs/backlog/report-f4p.md` propunha) definiu a amostra do CycleTime/Variabilidade como "os últimos N meses a partir de hoje, não filtrada pelo roadmap". Na prática, isso significava que trocar o filtro de Roadmap interno/executivo (semestre) nunca mudava os números do Report F4P — só mudava o título do painel e o quadro ao lado. O usuário reportou isso como bug ao comparar com a Visão analítica (que muda com o semestre) e, depois de confirmarmos que era comportamento intencional da decisão anterior, pediu para revisar a regra.

## Decisão

A amostra passa a depender de **qual semestre está selecionado** (Roadmap interno com prioridade sobre o executivo, mesma prioridade já usada no título do painel):

- **Semestre em curso** (contém a data de hoje) — comportamento inalterado: últimos `CFG.f4p.months` meses a partir de hoje. É o caso mais comum (acompanhar o time em tempo real).
- **Semestre já encerrado** — a amostra passa a ser só o período daquele semestre (1/jan a 30/jun, ou 1/jul a 31/dez), não mais uma janela corrida. Serve para consultar o F4P de um período fechado (ex.: fechamento do 1º semestre em julho).
- **Semestre futuro** — não é possível calcular nada (o período ainda não aconteceu), então a aba do Report F4P fica **desabilitada**; se o painel já estava aberto e o usuário troca para um semestre futuro, ele recolhe sozinho (mesmo padrão que já existe para "sem Time" ou "sem Roadmap").
- **Nenhum semestre reconhecido** no filtro (string que não bate com o formato `AAAA Nº Semestre`) — cai no mesmo caso do semestre em curso, por segurança (nunca deveria acontecer, já que a aba exige Roadmap preenchido para habilitar).

## Implementação

`f4pSemesterState()` (`src/js/23-report-f4p.js`) classifica o semestre do filtro em `current` / `past` / `future` comparando o início e o fim do semestre (`f4pSemStart`, novo; `semEnd`, já existia para a Visão analítica) com `TODAY`. `f4pSample` usa essa classificação para escolher o intervalo de datas de saída do CT considerado. `f4pEnabled` passa a exigir também que o semestre não seja `future`.

## Consequências

- Testes novos em `tests/test_report_f4p.py`: amostra do semestre em curso (comportamento antigo, preservado), amostra ancorada num semestre passado (item conhecido dentro do período conta, item fora não conta) e desabilitação/recolhimento no semestre futuro.
- Dois testes existentes que usavam o literal `"2026 2º Semestre"` para simular "qualquer semestre" passaram a usar `semestre(TODAY)` (o semestre atual, calculado em tempo de execução) — antes disso não importava qual string era usada, porque o roadmap não influenciava o cálculo; agora importa, e um literal fixo de 2026 viraria "semestre passado" (mudando de comportamento) assim que o ano virasse.
- `docs/regras-de-negocio.md` §12.1 atualizado com a tabela de períodos por tipo de semestre.
