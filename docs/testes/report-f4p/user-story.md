# Testes: Report F4P — Quadrante 7 (User Story: reservado vs. planejado outro semestre vs. não planejado) + conferência cruzada

Ver `docs/testes/report-f4p/README.md` para as regras compartilhadas. Regras de negócio: §12.8.
Decisões `0030`, `0043`, `0071`, `0072`.

Mesmo critério de "entregue" (categoria de fluxo Vazão) do Technical Story/Vazão, mas com **tipos
próprios** (`CFG.f4p.usTypes`, padrão `["user story"]`, independentes de `CFG.f4p.types` do CT).
**Diferença estrutural do Vazão**: Planejado + Não planejado são uma **partição exata** do conjunto
entregue (com/sem a tag de capacidade) — não um subconjunto como Reserva ⊆ Realizado no Vazão. O
Planejado, por sua vez, se divide numa segunda partição (decisão `0043`): Reservado (o épico vinculado
tem compromisso de roadmap no mesmo semestre selecionado) e Planejado (outro semestre) (o restante) —
o mesmo critério da Reserva entregue do Vazão (§12.6), sem mudar o total de Planejado nem a conferência
cruzada.

## Regra: conta só tipos configurados (próprios, independentes do CT) e já entregues

**Garante que**: `f4pUsOps` usa `CFG.f4p.usTypes`, não `CFG.f4p.types` — mudar um não afeta o outro.

- **Testes**: `test_us_conta_so_tipos_configurados_e_entregues`,
  `test_us_usa_tipos_configuraveis_proprios_independentes_do_ct` (troca `usTypes` para `["feature"]`
  e confirma que "User Story" comum deixa de contar, sem afetar `CFG.f4p.types`).
- **Cenário de falha coberto**: reaproveitar `CFG.f4p.types` (do CT) faria uma mudança de
  configuração do CycleTime alterar sem querer a contagem do quadrante User Story.

## Regra: Planejado e Não planejado são uma partição exata (sem sobreposição)

**Garante que**: cada item entregue está em exatamente um dos dois grupos — a soma de Planejado +
Não planejado é sempre igual ao total entregue.

- **Dado**: 2 itens com a tag de capacidade (case diferente, ambos "planejados"), 1 sem tag ("não
  planejado").
- **Então (sucesso)**: `{planejado: 2, naoPlanejado: 1, total: 3}` — `2 + 1 === 3`.
- **Teste**: `test_us_planejado_e_nao_planejado_sao_particao_exata`
- **Teste da tag configurável**: `test_us_usa_tag_de_capacidade_configuravel` (mesma tag `CFG.anTag`
  da Visão analítica/Vazão).
- **Cenário de falha coberto**: se a lógica tratasse Planejado como subconjunto (como no Vazão) em
  vez de partição, um item poderia aparecer contado nos dois grupos ou em nenhum, quebrando a soma
  que a conferência cruzada depende.

## Regra: ignora não entregues; janela exata do semestre (mesmo padrão dos demais "por semestre")

**Testes**: `test_us_ignora_itens_em_backlog_discovery_ou_wip`,
`test_us_semestre_atual_ignora_entregues_antes_do_inicio_do_semestre`,
`test_us_semestre_passado_conta_so_entregues_no_periodo`

## Regra: tendência soma WIP ao mês corrente (mesmos exemplos-padrão do Vazão)

**Testes**: `test_us_tendencia_soma_wip_ao_mes_atual_exemplo_melhora` (▲),
`test_us_tendencia_soma_wip_ao_mes_atual_exemplo_piora` (▼),
`test_us_tendencia_soma_wip_ao_mes_atual_exemplo_estavel` (◆),
`test_us_tendencia_sem_meses_anteriores_fica_neutra`,
`test_us_wip_conta_so_tipos_configurados_do_time` (WIP usa `usTypes`, filtra por time).
**Relacionado**: decisão `0023` (regra compartilhada, ver README).

## Regra: Reservado e Planejado (outro semestre) são uma partição exata do Planejado

**Garante que**: `f4pUsReservadoItems`/`f4pUsPlanejadoOutroSemestreItems` reaproveitam o mesmo critério
interno/executivo do Roadmap – Épicos (`f4pEpiCompromissoBate`, igual à Reserva entregue do Vazão,
§12.6) para dividir o Planejado — sem tocar no quadrante Roadmap – Épicos nem no total de Planejado
usado pela conferência cruzada (decisão `0043`).

- **Dado**: Roadmap Interno selecionado; 1 item planejado cujo épico bate com o semestre (Reservado),
  1 item planejado cujo épico aponta pra outro semestre, 1 item planejado **sem** `epicoId` (também cai
  em "outro semestre" — caso de borda, decisão explícita do usuário), 1 item sem a tag (Não planejado).
- **Então (sucesso)**: `{reservado: 1, planejadoOutro: 2, planejado: 3, naoPlanejado: 1}` — a soma
  `reservado + planejadoOutro === planejado` sempre.
- **Teste**: `test_us_reservado_e_planejado_outro_semestre_sao_particao_exata_do_planejado`
- **Teste do critério Executivo**: `test_us_reservado_usa_compromisso_executivo_da_iniciativa` — sobe
  Épico → Release → Iniciativa e compara `AnoSemestreRoadmap` (`i.exec`), igual ao Roadmap – Épicos no
  critério Executivo.
- **Cenário de falha coberto**: exatamente o problema de conceito reportado pelo usuário ao comparar
  com o Analytics — um item com a tag de capacidade contaria como "reservado do semestre selecionado"
  mesmo com o épico apontando pra um compromisso de roadmap diferente (ex.: entrega em agosto, 2º
  semestre por data, mas roadmap mapeado no 1º semestre).

## Regra: clique no Reservado/Planejado (outro semestre)/Não planejado abre a lista correspondente, navegável

**Testes**: `test_us_clique_no_reservado_abre_lista_e_permite_navegar`,
`test_us_clique_no_planejado_outro_semestre_mostra_os_com_compromisso_divergente`,
`test_us_clique_no_nao_planejado_mostra_so_os_sem_a_tag`

## Regra: o quadrante aparece calculado no painel (3 números: Reservado | Planejado outro semestre | Não planejado); tipos configuráveis persistem e exportam

**Testes**: `test_us_aparece_calculado_no_painel`,
`test_configuracao_us_types_tem_padrao_user_story`,
`test_configuracao_us_types_persiste_e_entra_na_exportacao`

---

## Conferência cruzada: Vazão × Technical Story × User Story (decisões `0030`, `0071`, `0072`)

**Garante que**: para qualquer time, Vazão Realizado é sempre igual à soma de Technical Story
Realizado + User Story Planejado + User Story Não planejado + Demais — mesmo universo de itens
entregues no período, só recortado por tipo em cada quadrante (mais o restante, "Demais", que nenhum
dos dois cobre). Essa é uma validação explícita pedida pelo usuário para dar confiança de que os
quadrantes, calculados de forma independente, não divergem. Aqui "User Story Planejado" é o **total**
(`f4pUsPlanejadoItems`, agregado interno usado só pelo cálculo, não exibido diretamente na UI desde a
decisão `0043`) — a soma de Reservado + Planejado (outro semestre) não muda esse total, então a
conferência continua batendo sem alteração de cálculo.

- **Exemplo exato dado pelo usuário**: MOBILE com 38 no Vazão Realizado = 27 Technical Story + 4
  User Story planejado + 7 User Story não planejado + 0 Demais (27+4+7+0=38).
- **Dado**: 27 itens Technical Story, 4 User Story com tag ROADMAP, 7 User Story sem tag, todos
  entregues no período.
- **Então (sucesso)**: `f4pReconciliacao()` para o time retorna
  `{team, vazao:38, ts:27, planejado:4, naoPlanejado:7, demais:0, soma:38, ok:True}`.
- **Teste**: `test_reconciliacao_bate_com_o_exemplo_exato_do_usuario`

### Regra: tipo extra na Vazão conta automaticamente como "Demais", sem exigir configuração adicional

**Garante que**: `f4pDemaisItems(team, st)` soma, dentro do Vazão Realizado (`f4pVazaoRealizadoItems`,
já filtrado por `CFG.f4p.types`), os itens cujo tipo **não** está em `CFG.f4p.tsTypes` nem em
`CFG.f4p.usTypes`. Isso faz a soma da conferência bater **por construção** quando `CFG.f4p.types` tem um
tipo a mais que os outros dois quadrantes não cobrem — sem exigir que o usuário replique a configuração
numa segunda lista. Decisão `0072`, correção de curso da `0071`: o usuário reportou, com um exemplo real
em produção, que ainda precisava configurar o tipo extra duas vezes (na Vazão e em `tsTypes`/`usTypes`)
para a conferência parar de "divergir" — e que, mesmo quando divergia, não dava pra ver quantos itens
formavam a diferença.

- **Dado**: `CFG.f4p.types` inclui `"internal bug"` além dos tipos padrão (`CFG.f4p.tsTypes`/
  `usTypes` continuam no padrão); 1 Internal Bug entregue + 1 User Story sem tag entregue.
- **Então (sucesso)**: `{team, vazao:2, ts:0, planejado:0, naoPlanejado:1, demais:1, soma:2, ok:True}`
  — a soma bate (2=2) porque o Internal Bug entra em "Demais", não precisa de configuração extra.
- **Teste**: `test_reconciliacao_tipo_extra_na_vazao_conta_como_demais_sem_divergir`
- **Cenário de falha coberto**: antes da `0072`, esse mesmo cenário resultava em `ok:False` sem
  explicar a diferença — o usuário via o aviso de divergência mas não tinha como saber que "1 item"
  era a causa, nem contava-lo em lugar nenhum.

### Regra: divergência real (soma maior que o Vazão Realizado) continua sinalizada

**Garante que**: "Demais" só absorve itens que o próprio Vazão Realizado já contava — não existe
"demais negativo". A conferência ainda sinaliza `ok:False` quando `CFG.f4p.tsTypes` ou
`CFG.f4p.usTypes` contam um item cujo tipo `CFG.f4p.types` (Vazão) não cobre, ou quando o mesmo tipo
está nas duas listas (`tsTypes` e `usTypes`) ao mesmo tempo — nesses casos a soma ultrapassa o Vazão
Realizado, e isso continua sendo um erro de configuração de verdade (decisão `0030`, "divergência é
sinalizada, não escondida" — segue valendo para este caso).

- **Dado**: `CFG.f4p.tsTypes` inclui `"technical solution"`, mas `CFG.f4p.types` (Vazão) não; 1
  Technical Solution entregue (conta em Technical Story, não no Vazão) + 1 User Story sem tag
  entregue.
- **Então (sucesso)**: `{team, vazao:1, ts:1, planejado:0, naoPlanejado:1, demais:0, soma:2, ok:False}`
  — a soma (2) ultrapassa o Vazão (1).
- **Teste**: `test_reconciliacao_sinaliza_divergencia_quando_ts_ou_us_contam_item_fora_da_vazao`

### Regra: incluir o tipo extra em Technical Story (ou User Story) continua funcionando como antes

**Garante que**: a decisão `0071` (Technical Story com lista de tipos própria) continua valendo —
incluir o tipo extra também em `CFG.f4p.tsTypes` (ou `usTypes`) faz o item contar especificamente
como Technical Story (ou User Story), em vez de cair em "Demais". Útil quando o tipo extra deve entrar
também na meta do quadrante Technical Story, por exemplo — "Demais" é só o resultado automático de
**não** fazer essa atribuição explícita.

- **Dado**: `CFG.f4p.types` e `CFG.f4p.tsTypes` incluem `"activity"` (além dos tipos padrão); 1 Activity
  entregue (agora conta como Technical Story, não como Demais) + 1 User Story sem tag entregue.
- **Então (sucesso)**: `{team, vazao:2, ts:1, planejado:0, naoPlanejado:1, demais:0, soma:2, ok:True}`.
- **Teste**: `test_reconciliacao_nao_sinaliza_quando_tipo_extra_entra_em_ts_types`
- **Relacionado**: decisão `0071-f4p-technical-story-tipo-configuravel.md`.

### Regra: clique no "Demais" abre a lista exata dos itens

**Garante que**: mesma transparência do resto do Report F4P — o número de "Demais" é clicável e abre
só os itens que compõem essa contagem (nem os de Technical Story, nem os de User Story).

- **Teste**: `test_reconciliacao_clique_no_demais_abre_a_lista_exata_dos_itens`

### Regra: o banner vermelho (divergência real) e o banner azul (itens "Demais") aparecem de forma independente

**Garante que**: `.f4p-recon` (vermelho) só é renderizado para times com `ok:False` (erro real, ver
regra acima); `.f4p-recon-info` (azul, informativo) só é renderizado para times com `ok:True` e
`demais > 0`. Nenhum dos dois aparece quando a configuração está sem tipos extras.

- **Teste do banner vermelho**: `test_reconciliacao_banner_vermelho_so_aparece_quando_ha_divergencia_real`
  — divergência real (tipo em `tsTypes` fora de `CFG.f4p.types`) mostra o banner; corrigir a
  configuração faz o banner sumir.
- **Teste do banner azul**: `test_reconciliacao_banner_info_aparece_so_quando_ha_itens_demais` — tipo
  extra na Vazão sem configuração adicional mostra só o banner azul (nunca o vermelho, já que a soma
  bate); removê-lo da configuração faz o banner sumir.
