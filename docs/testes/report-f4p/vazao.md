# Testes: Report F4P — Quadrante 5 (Vazão: reserva vs. reserva entregue vs. realizado)

Ver `docs/testes/report-f4p/README.md` para as regras compartilhadas. Regras de negócio: §12.6.
Decisões `0022`–`0024`, `0043`.

Mesmo critério de "entregue" (categoria de fluxo Vazão) do Technical Story, mas usa os **tipos
configurados para o CT** (`CFG.f4p.types`, padrão User Story e Technical Story) em vez de um tipo
fixo. Reserva é o **subconjunto** do Realizado com a tag de capacidade do roadmap (`CFG.anTag`, a
mesma tag já usada na Visão analítica); Realizado é todo o conjunto, com ou sem a tag. Reserva
entregue (decisão `0043`) é um terceiro número, subconjunto da própria Reserva, cujo épico vinculado
tem compromisso de roadmap batendo com o semestre selecionado.

## Regra: Realizado conta só tipos configurados e já entregues

**Garante que**: `f4pVazaoRealizadoItems` conta itens dos tipos em `CFG.f4p.types` (User Story,
Technical Story por padrão) que já estão na categoria Vazão — um tipo fora da lista (ex.: Internal
Bug) ou um item não entregue não contam.

- **Dado**: User Story entregue (conta), Technical Story entregue (conta), Internal Bug entregue
  (tipo não configurado, não conta), User Story em Backlog (não entregue, não conta).
- **Então (sucesso)**: `2` itens.
- **Teste**: `test_vazao_conta_so_tipos_configurados_e_entregues`
- **Relacionado**: decisão `0022-report-f4p-quadrante-vazao.md`.

## Regra: Reserva é subconjunto do Realizado (tag configurável, case-insensitive)

**Garante que**: Reserva é sempre um subconjunto do Realizado — nunca maior, por construção — e a
tag de capacidade (`CFG.anTag`) é comparada sem diferenciar maiúsculas/minúsculas.

- **Dado**: 2 itens com a tag `ROADMAP`/`Roadmap` (case diferente, ambos contam), 1 sem tag.
- **Então (sucesso)**: `{reserva: 2, realizado: 3}`.
- **Teste**: `test_vazao_reserva_e_subconjunto_com_a_tag_de_capacidade`
- **Teste da tag configurável**: `test_vazao_usa_tag_de_capacidade_configuravel` — trocar
  `CFG.anTag` para `"CAPACIDADE"` faz só a nova tag contar (a antiga `ROADMAP` deixa de contar).
- **Cenário de falha coberto**: um time que padronizou uma tag diferente do padrão `ROADMAP`
  continuaria vendo a Reserva contar pela tag antiga, subestimando a capacidade real reservada.

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
Reserva — uma dimensão de cor independente da direção ▲/▼/◆. Como Reserva é sempre subconjunto do
Realizado (decisão `0022`), o caso vermelho não é alcançável no pipeline normal; os testes cobrem os
dois casos que a checagem `>=` realmente distingue.

- **Testes**: `test_vazao_seta_de_tendencia_fica_verde_quando_realizado_maior_que_reserva`,
  `test_vazao_seta_de_tendencia_fica_verde_quando_realizado_igual_reserva`
- **Relacionado**: decisão `0024-report-f4p-vazao-cor-da-seta-por-realizado-vs-reserva.md`.

## Regra: clique no Realizado e na Reserva abrem listas distintas, cada uma navegável

**Garante que**: clicar no Realizado mostra todos os itens entregues do time no período; clicar na
Reserva mostra só o subconjunto com a tag — cada item navega ao quadro como no padrão compartilhado.

- **Testes**: `test_vazao_clique_no_realizado_abre_lista_e_permite_navegar`,
  `test_vazao_clique_na_reserva_mostra_so_os_com_a_tag`

## Regra: Reserva entregue é o subconjunto da Reserva cujo épico tem compromisso de roadmap no semestre selecionado

**Garante que**: `f4pVazaoReservaEntregueItems` reaproveita o mesmo critério interno/executivo do
Roadmap – Épicos (`f4pRoadmapEpis`, via `f4pEpiCompromissoBate`) para decidir se o **épico vinculado**
(`o.epicoId`) de cada item da Reserva tem compromisso de roadmap batendo com o semestre selecionado —
sem alterar o quadrante Roadmap – Épicos em si, que continua intocado (decisão `0043`).

- **Dado**: Roadmap Interno selecionado, 2 itens reservados, um cujo épico tem `interno` igual ao
  semestre selecionado (bate), outro cujo épico aponta para outro semestre.
- **Então (sucesso)**: `{reserva: 2, reservaEntregue: 1}` — a Reserva continua contando os dois, só a
  Reserva entregue exclui o que aponta pra outro semestre.
- **Teste (critério Interno)**: `test_vazao_reserva_entregue_bate_com_compromisso_interno_do_proprio_epico`
- **Teste (critério Executivo)**: `test_vazao_reserva_entregue_usa_iniciativa_quando_roadmap_executivo_ativo`
  — sobe Épico → Release → Iniciativa e compara `AnoSemestreRoadmap` (`i.exec`), ignorando o Target
  Date do próprio épico, exatamente como o Roadmap – Épicos faz no critério Executivo.
- **Cenário de falha coberto**: sem esse filtro extra, um item entregue no período mas cujo compromisso
  de roadmap é de outro semestre contaria como "reserva do semestre selecionado" só por ter a tag —
  exatamente o problema de conceito reportado pelo usuário ao comparar com o Analytics (um item entregue
  em agosto, encaixando no 2º semestre por data, mas mapeado no roadmap para o 1º semestre).

## Regra: épico sem compromisso registrado, ou item sem épico vinculado, ficam fora da Reserva entregue (caso de borda)

**Garante que**: um épico sem Target Date preenchido (critério Interno) — ou um item reservado sem
`epicoId`/apontando para um épico inexistente — não bate com nenhum semestre; continua contando
normalmente na Reserva (e no Realizado), mas nunca soma à Reserva entregue.

- **Testes**: `test_vazao_reserva_entregue_exclui_epico_sem_compromisso_registrado`,
  `test_vazao_reserva_entregue_exclui_reserva_sem_epico_vinculado`
- **Cenário de falha coberto**: sem essa checagem explícita, um épico incompleto (dado ausente) poderia
  ser tratado como "bate com qualquer semestre" por uma comparação frouxa (`undefined === undefined`),
  inflando a Reserva entregue com itens sem garantia real de compromisso — decisão explícita do usuário
  ao ser consultado sobre este caso de borda: conta como "outro semestre"/fora da Reserva entregue.
- **Relacionado**: decisão `0043`.

## Regra: clique na Reserva entregue mostra só os itens com compromisso no semestre selecionado

**Teste**: `test_vazao_clique_na_reserva_entregue_mostra_so_os_com_compromisso_no_semestre`

## Regra: o quadrante aparece calculado no painel, com os 3 números (Reserva | Reserva entregue | Realizado)

**Teste**: `test_vazao_aparece_calculado_no_painel`
