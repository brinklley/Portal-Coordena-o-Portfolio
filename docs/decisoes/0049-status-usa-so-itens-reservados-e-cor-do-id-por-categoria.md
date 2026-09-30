# 0049 — Visão analítica: Status usa só itens reservados; Report F4P: cor do ID por categoria de fluxo

## Contexto

Com prints da Visão analítica e do Report F4P, o usuário pediu duas melhorias num só PR:

1. Na Visão analítica, a coluna Status mostra a fase/coluna do item aberto mais avançado do épico
   considerando **qualquer item vinculado ao time**, não só os reservados pro roadmap (tag `ROADMAP`).
   Isso confunde: um item fora da reserva pode estar em WIP enquanto o item de fato reservado ainda
   está em Discovery — o usuário vê "WIP" e acha que o trabalho reservado já está andando, quando na
   verdade quem está andando é outro item, fora do escopo do roadmap selecionado.
2. No Report F4P, o ID de cada item nos modais de "ver itens" (`f4pItemsModal`) sempre tem fundo verde
   — mesma cor usada pra "Vazão"/entregue — mesmo quando o item está em Backlog, Discovery ou WIP. O
   usuário vê uma lista inteira de IDs verdes e interpreta que tudo já foi entregue.

## Melhoria 1 — Status considera só a Reserva

### Diagnóstico

`rowOf` (`anData()`, `src/js/15-visao-analitica.js`) calculava `farName` (a coluna do item aberto mais
avançado) e `m.phase` (a fase geral do épico) iterando **todos** os itens do time vinculados ao épico
(`m.recs`, de `epiMetrics(e, team)`) — sem olhar a tag de capacidade. O agrupador por categoria
(Backlog/Discovery/WIP/Vazão com contagem, `distGroup(m)`) logo abaixo, na mesma célula, usa a mesma
base `m` — e esse, sim, deve continuar contando todo mundo (é o "próximo campo" que o usuário pediu
para manter intocado: "onde está todos os itens vinculados com o épico sem importar a TAG").

### Correção

`rowOf` passou a calcular `far`/`farName` e uma nova fase (`reservaPhase`, via `phaseOf`) usando só
`reservados` (o mesmo subconjunto com a tag que já alimenta a Capacidade) — `distGroup(m)` continua
recebendo `m` (todos os itens), sem nenhuma mudança. `PH_TXT_RESERVA` é uma cópia de `PH_TXT` com
`vazio` trocado para **"Sem reserva"** em vez de "Sem itens" — como todo épico que chega em `rowOf` já
tem pelo menos um item do time (`V.visEpi`/a checagem de órfãos exigem isso), `reservaPhase === "vazio"`
nunca significa "épico sem itens", sempre "nenhum item com a tag". `anSorted` (ordenação pela coluna
Status) passou a usar `reservaPhase` em vez de `m.phase`, e o KPI "entregues" do cabeçalho também.

Consultei o usuário sobre esse rótulo (Sem reserva vs. reaproveitar Sem itens); escolheu o rótulo novo,
por clareza.

## Melhoria 2 — Cor do ID por categoria de fluxo

### Diagnóstico

`.f4p-items-tbl .idb` (usada por `f4pItemsModal`, compartilhada entre Report F4P, Visão analítica e
Actionable) tinha fundo verde (`#22C55E`) fixo, independente da categoria real do item — só a coluna
"Situação" ao lado mostrava a categoria de verdade.

### Correção

`.idb` ganhou 4 classes modificadoras (`none`/`disc`/`wip`/`vazao`), reaproveitando a mesma paleta já
usada por `.fb` (badges de coluna em Configurações › Fluxo dos times: `--c-none`/`--c-disc`/`--c-wip`/
`--c-vaz`). `f4pItemsModal(title, items, situacaoFn, catFn)` ganhou um 4º parâmetro opcional `catFn`
(padrão `o => catOf(o)`) que decide a classe de cada ID.

O único call site que não opera sobre itens de time é o Roadmap – Épicos (lista épicos, cuja "situação"
é a própria coluna do quadro de Épicos — `catOf` não se aplica). Consultei o usuário sobre a cor ali;
escolheu: verde só quando o épico está na última coluna do quadro de Épicos (fechado/entregue), cinza
neutro nas demais — nova função `f4pEpiCatClass(e)`, passada como `catFn` nesse call site.

`.an-table .idb` (o ID do **épico** na coluna "Evolução" da própria Visão analítica, e o hardcode de
cor na função de copiar tabela pro clipboard, `anCopy`) não foi tocado — fora do escopo pedido pelo
usuário ("no report-f4p").

## Testes

- `tests/test_visao_analitica.py`: `test_status_usa_so_o_item_reservado_mais_avancado_nao_qualquer_item_do_time`,
  `test_status_mostra_sem_reserva_quando_nenhum_item_tem_a_tag`,
  `test_status_mostra_entregue_quando_so_os_reservados_ja_estao_em_vazao`,
  `test_status_ordena_pela_fase_da_reserva_nao_pela_fase_de_todos_os_itens`.
- `tests/test_report_f4p.py`: `test_idb_usa_a_cor_da_categoria_de_fluxo_do_item`,
  `test_idb_aceita_catFn_proprio_no_lugar_de_catOf`,
  `test_f4pEpiCatClass_e_verde_so_quando_o_epico_esta_fechado`,
  `test_clique_no_roadmap_epicos_colore_o_id_pela_coluna_do_proprio_quadro`.

Confirmei que os 8 testes novos falham contra o código anterior a esta decisão (via `git stash`) antes
de restaurar a correção — os 4 de Melhoria 1 por falta do campo `reservaPhase`/valor errado, os 4 de
Melhoria 2 por `f4pEpiCatClass` não existir e pela classe do ID ficar sempre `idb` (sem modificador).
Validação visual via Playwright confirmando as cores renderizadas (cinza/azul/azul-escuro/verde) e o
Status mostrando "Discovery"/"Sem reserva" corretamente nos cenários do print do usuário.
