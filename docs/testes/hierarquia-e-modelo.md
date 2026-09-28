# Testes: Hierarquia, validade e visibilidade

Cobre `tests/test_regras_hierarquia.py` (5 testes). Trata das regras de exibição da hierarquia
Iniciativa → Release → Épico → itens de time: quando cada nível é "válido", quando aparece no
quadro (regra B) e como o diagnóstico ("investigar") explica por que um item não aparece.
Ver `docs/regras-de-negocio.md` §2 (Validade) e §3 (Visibilidade no quadro — regra B).

## Regra: regra B — só entram no quadro itens com desdobramento válido

**Garante que**: uma Iniciativa só aparece no quadro se tiver ao menos uma Release válida (ou, com a
opção "mostrar avulsas" ligada, mesmo sem desdobramento — exceto se já concluída sem release, que
fica sempre fora). O mesmo vale em cascata para Release → Épico.

- **Dado**: fixture `desdobramento.xlsx`, com iniciativas/releases em diferentes situações: com
  cadeia completa, concluída sem release, sem release ainda aberta, release entregue sem épico,
  release sem iniciativa.
- **Quando**: o quadro renderiza com a opção "mostrar avulsas" (`#fBare`) ligada (padrão) e depois
  desligada.
- **Então (sucesso)**: com `#fBare` ligado, `S.V.visIni` = `["1","2","3"]` (a iniciativa 4,
  concluída sem release, fica de fora) e `S.V.visRel` = `["10","20","21","22"]` (a release 23,
  entregue sem épico, e a 99, sem iniciativa, ficam de fora); com `#fBare` desligado, só a cadeia
  completa aparece (`["1","2"]` / `["10","20","21"]`).
- **Cenário de falha coberto**: uma iniciativa concluída sem nenhuma release apareceria no quadro
  como se estivesse em andamento, ou uma release órfã (sem iniciativa) apareceria sem contexto.
- **Teste**: `test_regra_b_itens_sem_desdobramento`
- **Relacionado**: decisão `0003-regra-b-itens-sem-desdobramento.md`; regras-de-negocio.md §3.

## Regra: selos de situação (fase) refletem a regra B em cada card

**Garante que**: cada card do quadro mostra um selo textual consistente com a regra de visibilidade:
`fechado`, `aberto`, `semrel` (iniciativa sem release), `semepi` (release sem épico). Releases sem
iniciativa entram na lista de avisos (`S.model.warn.relNoEpi`, apesar do nome, cobre o aviso de vínculo
ausente).

- **Dado**: a mesma fixture `desdobramento.xlsx`.
- **Quando**: `iniPhase(...)` / `relPhase(...)` são chamados para cada card relevante.
- **Então (sucesso)**: iniciativa 1 → `fechado`; 2 → `aberto`; 3 → `semrel`; release 20 →
  `fechado`; 21 → `aberto`; 22 → `semepi`; a release 99 (sem iniciativa) aparece em
  `S.model.warn.relNoEpi`.
- **Cenário de falha coberto**: o selo mostraria "aberto" para uma iniciativa sem release nenhuma,
  escondendo um problema de cadastro que o usuário precisa corrigir na fonte.
- **Teste**: `test_selos_de_situacao`

## Regra: filtro de time só mostra a cadeia completa daquele time

**Garante que**: filtrar por um time específico restringe a visão às iniciativas que têm ao menos um
item daquele time na cadeia completa (não avulsas de outro contexto).

- **Dado**: `desdobramento.xlsx`, filtro `#fTeam = "CORE"`.
- **Então (sucesso)**: `S.V.visIni` = `["1","2"]`.
- **Cenário de falha coberto**: o filtro de time vazaria iniciativas sem nenhum item daquele time,
  ou esconderia iniciativas válidas do time filtrado.
- **Teste**: `test_filtros_de_time_mostram_so_cadeia_completa`

## Regra: fase do épico é derivada dos itens do próprio épico

**Garante que**: a fase de um épico (`fechado`/`wip`/etc.) vem da situação agregada dos itens de
time vinculados a ele (`epiMetrics(e, '').phase`), não de um campo próprio do épico.

- **Dado**: épicos `200` (todos os itens fechados) e `210` (com itens em andamento) na fixture.
- **Então (sucesso)**: `epiMetrics(epis.get('200'), '').phase === "fechado"`;
  `epiMetrics(epis.get('210'), '').phase === "wip"`.
- **Cenário de falha coberto**: um épico com todos os itens entregues continuaria marcado como em
  andamento, escondendo trabalho já concluído do roadmap.
- **Teste**: `test_fase_do_epico_pelos_itens`

## Regra: a investigação ("por que não aparece?") explica a regra B passo a passo

**Garante que**: `investigate(id)` percorre as condições da regra B em ordem e retorna, para cada
passo, se ele passou (`ok`) e o título explicando o que está sendo checado — terminando no motivo
real de exclusão (ou confirmando que o item é visível).

- **Dado**: iniciativa `4` (concluída sem release: deve falhar), iniciativa `3` (sem release, mas
  aberta: deve passar mesmo citando o passo "Iniciativa sem release"), ID `999999` (não existe nos
  dados carregados).
- **Então (sucesso)**: para `4`, o último passo é `[False, "Iniciativa concluída sem release"]`;
  para `3`, o passo "Iniciativa sem release" aparece como `True` e o último passo também é `True`
  (visível); para um ID inexistente, a única saída é `["Não retornou nos dados"]`.
- **Cenário de falha coberto**: o diagnóstico apontaria o motivo errado de exclusão (ex.: dizer que
  falta release quando na verdade o problema é a iniciativa estar concluída), confundindo o usuário
  sobre o que corrigir na fonte.
- **Teste**: `test_investigacao_explica_a_regra`
- **Relacionado**: `docs/telas.md` (tela de investigação).
