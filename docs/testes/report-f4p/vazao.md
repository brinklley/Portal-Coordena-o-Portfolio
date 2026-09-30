# Testes: Report F4P — Quadrante 5 (Vazão: reserva vs. reserva entregue vs. realizado)

Ver `docs/testes/report-f4p/README.md` para as regras compartilhadas. Regras de negócio: §12.6.
Decisões `0022`–`0024`, `0043`, `0048`, `0052`.

Realizado usa o mesmo critério de "entregue" (categoria de fluxo Vazão) do Technical Story, com os
**tipos configurados para o CT** do próprio Report F4P (`CFG.f4p.types`, padrão User Story e Technical
Story). Reserva (decisão `0048`) é a **mesma capacidade do roadmap** da Visão analítica (§10) — itens
dos tipos `CFG.ctTypes` com a tag de capacidade (`CFG.anTag`) cujo épico está comprometido com o
roadmap selecionado, em **qualquer status**, não mais um subconjunto do Realizado. Reserva entregue
(decisão `0043`, redefinida pela `0052`) é um terceiro número, subconjunto da própria **Reserva** já
entregue (categoria Vazão) — **sem exigir data de entrega dentro do período exato do semestre**.

## Regra: Realizado conta só tipos configurados e já entregues

**Garante que**: `f4pVazaoRealizadoItems` conta itens dos tipos em `CFG.f4p.types` (User Story,
Technical Story por padrão) que já estão na categoria Vazão — um tipo fora da lista (ex.: Internal
Bug) ou um item não entregue não contam.

- **Dado**: User Story entregue (conta), Technical Story entregue (conta), Internal Bug entregue
  (tipo não configurado, não conta), User Story em Backlog (não entregue, não conta).
- **Então (sucesso)**: `2` itens.
- **Teste**: `test_vazao_conta_so_tipos_configurados_e_entregues`
- **Relacionado**: decisão `0022-report-f4p-quadrante-vazao.md`.

## Regra: Reserva conta qualquer status do item, desde que o épico esteja comprometido (tag configurável, case-insensitive)

**Garante que** (decisão `0048`): Reserva não exige mais que o item já tenha sido entregue — conta
Backlog, WIP e Vazão igualmente, desde que tenha a tag de capacidade (`CFG.anTag`, comparada sem
diferenciar maiúsculas/minúsculas) E o épico vinculado esteja comprometido com o roadmap selecionado.

- **Dado**: 1 item em Backlog e 1 em WIP, ambos com a tag `ROADMAP`/`Roadmap` (case diferente) e
  vinculados a um épico comprometido com o semestre selecionado; 1 item já em Vazão, sem tag.
- **Então (sucesso)**: `{reserva: 2, realizado: 1}` — a Reserva conta os dois reservados (qualquer
  status); o Realizado conta só o entregue (com ou sem tag).
- **Teste**: `test_vazao_reserva_conta_qualquer_status_do_epico_comprometido`
- **Teste da tag configurável**: `test_vazao_reserva_usa_tag_de_capacidade_configuravel` — trocar
  `CFG.anTag` para `"CAPACIDADE"` faz só a nova tag contar (a antiga `ROADMAP` deixa de contar).
- **Cenário de falha coberto**: um time que padronizou uma tag diferente do padrão `ROADMAP`
  continuaria vendo a Reserva contar pela tag antiga, subestimando a capacidade real reservada.

## Regra: Reserva bate com a Capacidade da Visão analítica

**Garante que** (decisão `0048`, o pedido original do usuário): a Reserva deste quadrante e a
Capacidade da Visão analítica (§10) somam exatamente o mesmo conjunto de itens para o mesmo time e
semestre — mesmos tipos (`CFG.ctTypes`), mesma tag (`CFG.anTag`) e mesmo critério de compromisso do
épico com o roadmap selecionado.

- **Dado**: um time com 3 itens reservados (Backlog, WIP e Vazão, todos com a tag e o épico
  comprometido com o roadmap executivo selecionado) e 1 item sem tag (fora dos dois números).
- **Então (sucesso)**: `anData().cap === f4pVazaoReservaItems(team, st).length` (ambos `3`).
- **Teste**: `test_vazao_reserva_bate_com_capacidade_da_visao_analitica`
- **Cenário de falha coberto**: antes da `0048`, a Reserva só contava itens já entregues no calendário
  exato do semestre (`CFG.f4p.types`), enquanto a Capacidade soma itens de qualquer status dos épicos
  comprometidos com o roadmap (`CFG.ctTypes`) — dois recortes diferentes que raramente convergiam,
  gerando a divergência relatada pelo usuário (ex.: Capacidade 14 vs. Reserva 0 num time que ainda não
  tinha entregue nada do que reservou).

## Regra: Reserva exige épico comprometido; Realizado não

**Garante que**: diferente do Realizado (que só olha a data de entrega dentro do calendário do
semestre), a Reserva exige que o próprio épico do item esteja comprometido com o roadmap selecionado —
um item tagueado sem `epicoId` (ou cujo épico não bate esse compromisso) conta no Realizado
normalmente, mas fica fora da Reserva.

- **Teste**: `test_vazao_reserva_exige_epico_comprometido_mas_realizado_nao`

## Regra: ignora itens não entregues; janela é o período exato do semestre

**Garante que**: mesma lógica de "entregue" e de janela do Technical Story (categoria Vazão +
`f4pExactSemesterWindow`).

- **Testes**: `test_vazao_ignora_itens_em_backlog_discovery_ou_wip`,
  `test_vazao_semestre_atual_ignora_entregues_antes_do_inicio_do_semestre`,
  `test_vazao_semestre_passado_conta_so_entregues_no_periodo`
- **Relacionado**: decisão `0017` (janela exata), `0020` (critério de entregue).

## Regra: tendência soma o WIP ao mês corrente contra a média (arredondada para cima) dos anteriores

**Garante que**: mesma regra da decisão `0023` documentada no README — aqui aplicada especificamente
ao Vazão, com WIP contado só dos tipos configurados do time.

- **Exemplos-padrão** (idênticos aos do README, aplicados a `f4pVazaoTrend`):
  - Média 1, mês atual 0, +3 WIP: `▲` — `test_vazao_tendencia_soma_wip_ao_mes_atual_exemplo_melhora`
  - Média 2, mês atual 0, +1 WIP: `▼` — `test_vazao_tendencia_soma_wip_ao_mes_atual_exemplo_piora`
  - Média 3, mês atual 2, +1 WIP: `◆` — `test_vazao_tendencia_soma_wip_ao_mes_atual_exemplo_estavel`
  - Média bruta 1,5→2, mês atual 2 sem WIP: `◆` — `test_vazao_tendencia_media_arredonda_sempre_pra_cima`
- **Casos sem WIP (comparação simples de meses)**:
  `test_vazao_tendencia_ultimo_mes_acima_da_media_melhora`,
  `test_vazao_tendencia_ultimo_mes_abaixo_da_media_piora`,
  `test_vazao_tendencia_igual_aos_meses_anteriores_fica_neutra`,
  `test_vazao_tendencia_sem_meses_anteriores_fica_neutra` (semestre recém-começado: sem meses
  anteriores, fica neutro).
- **WIP conta só tipos configurados do time**: `test_vazao_wip_conta_so_tipos_configurados_do_time`
  — um tipo não configurado ou um item de outro time não entram na contagem de WIP.
- **Relacionado**: decisão `0023-report-f4p-vazao-tendencia-com-wip.md`.

## Regra: a seta de tendência é colorida por Realizado vs. Reserva (não pela direção ▲▼◆)

**Garante que**: a cor da seta é verde quando Realizado ≥ Reserva, vermelha quando Realizado <
Reserva — uma dimensão de cor independente da direção ▲/▼/◆. Antes da decisão `0048` o caso vermelho
não era alcançável (Reserva era sempre subconjunto do Realizado, decisão `0022`); agora que Reserva é
a capacidade do roadmap em qualquer status, os três casos (maior, igual e menor) são testáveis.

- **Testes**: `test_vazao_seta_de_tendencia_fica_verde_quando_realizado_maior_que_reserva`,
  `test_vazao_seta_de_tendencia_fica_verde_quando_realizado_igual_reserva`,
  `test_vazao_seta_de_tendencia_fica_vermelha_quando_realizado_menor_que_reserva` — item reservado
  (tag + épico comprometido) ainda em WIP: conta na Reserva, mas nada foi entregue ainda.
- **Relacionado**: decisões `0024-report-f4p-vazao-cor-da-seta-por-realizado-vs-reserva.md` e
  `0048-vazao-reserva-bate-com-capacidade-analitica.md`.

## Regra: clique no Realizado e na Reserva abrem listas distintas, cada uma navegável

**Garante que**: clicar no Realizado mostra todos os itens entregues do time no período; clicar na
Reserva mostra só o subconjunto com a tag — cada item navega ao quadro como no padrão compartilhado.

- **Testes**: `test_vazao_clique_no_realizado_abre_lista_e_permite_navegar`,
  `test_vazao_clique_na_reserva_mostra_so_os_com_a_tag`

## Regra: Reserva entregue é o subconjunto da Reserva já entregue (categoria Vazão)

**Garante que** (decisão `0043`, redefinida pela `0052`): `f4pVazaoReservaEntregueItems` filtra a
própria `f4pVazaoReservaItems` (não mais o Realizado) pela categoria de fluxo Vazão — como a Reserva já
exige tipo (`CFG.ctTypes`), tag de capacidade e épico comprometido com o semestre selecionado (via
`f4pEpiCompromissoBate`, o mesmo critério interno/executivo do Roadmap – Épicos, sem alterar aquele
quadrante), Reserva entregue passa a ser subconjunto da Reserva **por construção**, e um item entregue
cujo épico não bate o compromisso continua fora **dos dois** números, Reserva e Reserva entregue.

- **Dado**: Roadmap Interno selecionado, 2 itens entregues com a tag de capacidade, um cujo épico tem
  `interno` igual ao semestre selecionado (bate), outro cujo épico aponta para outro semestre.
- **Então (sucesso)**: `{reserva: 1, reservaEntregue: 1}` — os dois números já excluem o item cujo
  épico aponta pra outro semestre.
- **Teste (critério Interno)**: `test_vazao_reserva_entregue_bate_com_compromisso_interno_do_proprio_epico`
- **Teste (critério Executivo)**: `test_vazao_reserva_entregue_usa_iniciativa_quando_roadmap_executivo_ativo`
  — sobe Épico → Release → Iniciativa e compara `AnoSemestreRoadmap` (`i.exec`), ignorando o Target
  Date do próprio épico, exatamente como o Roadmap – Épicos faz no critério Executivo.
- **Cenário de falha coberto**: sem esse filtro, um item entregue no período mas cujo compromisso de
  roadmap é de outro semestre contaria como "reserva do semestre selecionado" só por ter a tag —
  exatamente o problema de conceito reportado pelo usuário ao comparar com o Analytics (um item entregue
  em agosto, encaixando no 2º semestre por data, mas mapeado no roadmap para o 1º semestre).

## Regra: épico sem compromisso registrado, ou item sem épico vinculado, ficam fora da Reserva e da Reserva entregue (caso de borda)

**Garante que**: um épico sem Target Date preenchido (critério Interno) — ou um item sem
`epicoId`/apontando para um épico inexistente — não bate com nenhum semestre; desde a decisão `0048`
isso já tira o item da própria Reserva (que também exige compromisso do épico), não só da Reserva
entregue como antes. O item continua contando normalmente no Realizado (que não olha compromisso de
épico, só data de entrega).

- **Testes**: `test_vazao_reserva_entregue_exclui_epico_sem_compromisso_registrado`
  (`{reserva: 0, reservaEntregue: 0}`), `test_vazao_reserva_entregue_exclui_reserva_sem_epico_vinculado`
  (idem)
- **Cenário de falha coberto**: sem essa checagem explícita, um épico incompleto (dado ausente) poderia
  ser tratado como "bate com qualquer semestre" por uma comparação frouxa (`undefined === undefined`),
  inflando a Reserva e a Reserva entregue com itens sem garantia real de compromisso — decisão explícita
  do usuário ao ser consultado sobre este caso de borda: conta como "outro semestre"/fora dos dois
  números.
- **Relacionado**: decisões `0043`, `0048`.

## Regra: Reserva entregue não exige entrega dentro do período exato do semestre

**Garante que** (decisão `0052`): um item da Reserva (tag + tipo + épico comprometido com o semestre
selecionado) já entregue (categoria Vazão) conta na Reserva entregue **mesmo que `o.deploy` caia fora
do período exato do semestre** (`f4pExactSemesterWindow`) — diferente do Realizado, que continua
exigindo a entrega dentro dessa janela.

- **Dado**: item com a tag de capacidade, tipo em `CFG.ctTypes`, épico comprometido com o semestre
  selecionado (Interno), entregue (Vazão) **antes** do início do período exato do semestre.
- **Então (sucesso)**: `{reserva: 1, reservaEntregue: 1, realizado: 0}` — conta na Reserva e na Reserva
  entregue, mas não no Realizado (que exige a data dentro da janela exata).
- **Teste**: `test_vazao_reserva_entregue_inclui_item_entregue_fora_do_periodo_exato_do_semestre`
- **Cenário de falha coberto**: o usuário reportou (via Report F4P) um item marcado como reserva do
  roadmap, com status Vazão (entregue), que aparecia corretamente na Reserva mas sumia da Reserva
  entregue por ter sido entregue fora do período filtrado — inconsistência com a Visão analítica, que
  não aplica essa janela de data à Capacidade/entrega. Antes da `0052`, `f4pVazaoReservaEntregueItems`
  delegava para `f4pVazaoOps` (que exige a janela exata), herdando essa restrição sem necessidade.

## Regra: clique na Reserva entregue mostra só os itens com compromisso no semestre selecionado

**Teste**: `test_vazao_clique_na_reserva_entregue_mostra_so_os_com_compromisso_no_semestre`

## Regra: o quadrante aparece calculado no painel, com os 3 números (Reserva | Reserva entregue | Realizado)

**Teste**: `test_vazao_aparece_calculado_no_painel`
