# 0036 — Visão analítica mostra épicos sem release/iniciativa no roadmap interno

## Contexto

O usuário pediu, com prints da tela "Roadmap CORE 2º semestre 2026" (Visão analítica): quando o
filtro é por **roadmap interno**, épicos que têm itens vinculados no time e cujo próprio Target Date
cai naquele semestre devem aparecer no relatório **mesmo sem vínculo com Iniciativa e Release** —
hoje eles somem completamente, porque `computeVisible()` só inclui na lista de épicos visíveis
(`visEpi`) os que têm uma cadeia válida até a Iniciativa. Pediu também um aviso visível
("OBS: SEM INICIATIVA e SEM RELEASE") para o usuário perceber o problema e corrigir o vínculo no
Azure DevOps.

## Por que só a Visão analítica

Diferente do quadro principal (que não faz sentido mostrar sem a cadeia inteira — não há onde
"pendurar" o card), a Visão analítica já é uma tabela plana por épico, filtrada por Time + Roadmap.
Um épico com itens do time dentro do semestre filtrado é exatamente o tipo de dado que essa tela
existe para mostrar — hoje ele fica invisível por um problema de cadastro (Parent do épico não
aponta pra uma release válida), não porque não devesse aparecer. Faz sentido só para roadmap
**interno**: o roadmap interno vem do próprio Target Date do épico (`e.interno`), enquanto o
executivo é herdado da Iniciativa (`e.exec = i.exec`, calculado só para épicos válidos em
`buildModel`) — um épico sem Iniciativa não tem de onde herdar um executivo, então nunca poderia
aparecer filtrando por ele de qualquer forma.

## Implementação

`anData()` (`src/js/15-visao-analitica.js`) já construía uma linha por épico de `V.visEpi`
(reaproveitando `epiMetrics`, que só depende de `e.ops`, não da validade do épico). Extraí essa
construção para `rowOf(e, i)` (aceita `i` nulo) e, quando o filtro de **roadmap interno**
(`S.f.int`) está ativo, adiciono uma passada extra em `M.epis` procurando épicos `!e.valid` cujo
`e.interno` bate com o semestre filtrado e que têm pelo menos um item do time selecionado
(`e.ops` já é preenchido pelo `buildModel` independente da validade do épico — só depende do
`ID_EPICO_UNICRED` do item apontar pro ID dele). Essas linhas entram no mesmo array `rows`, com
`orphan:true`, e por isso contam normalmente nas somas de QTD/Capacidade/Projetada e nos KPIs do
cabeçalho — o objetivo é justamente parar de esconder esse trabalho da contagem.

Na tabela (`renderAnalytics()`), a linha `[IN][id] título` vira `OBS: SEM INICIATIVA e SEM RELEASE`
(um `<mark>` amarelo, mesmo padrão visual já usado no cabeçalho da tela) quando `r.orphan` — o botão
`[IN]` não existe pra essas linhas, já que não há iniciativa nenhuma pra abrir.

## Testes

`tests/test_visao_analitica.py`: `test_epico_orfao_aparece_no_roadmap_interno_com_aviso` (épico
`valid:false` com itens do time e `interno` no semestre filtrado aparece em `anData().rows`, conta
no `proj`, e a tela mostra o aviso) e `test_epico_orfao_nao_aparece_no_roadmap_executivo` (o mesmo
épico, filtrando só por executivo, continua fora — `anData().rows` vazio).
