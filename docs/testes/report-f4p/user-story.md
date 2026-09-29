# Testes: Report F4P — Quadrante 7 (User Story: reservado vs. planejado outro semestre vs. não planejado) + conferência cruzada

Ver `docs/testes/report-f4p/README.md` para as regras compartilhadas. Regras de negócio: §12.8.
Decisões `0030`, `0043`.

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

## Conferência cruzada: Vazão × Technical Story × User Story (decisão `0030`)

**Garante que**: para qualquer time, Vazão Realizado é sempre igual à soma de Technical Story
Realizado + User Story Planejado + User Story Não planejado — mesmo universo de itens entregues no
período, só recortado por tipo em cada quadrante. Essa é uma validação explícita pedida pelo usuário
para dar confiança de que os três quadrantes, calculados de forma independente, não divergem. Aqui
"User Story Planejado" é o **total** (`f4pUsPlanejadoItems`, agregado interno usado só pelo cálculo,
não exibido diretamente na UI desde a decisão `0043`) — a soma de Reservado + Planejado (outro
semestre) não muda esse total, então a conferência continua batendo sem alteração de cálculo.

- **Exemplo exato dado pelo usuário**: MOBILE com 38 no Vazão Realizado = 27 Technical Story + 4
  User Story planejado + 7 User Story não planejado (27+4+7=38).
- **Dado**: 27 itens Technical Story, 4 User Story com tag ROADMAP, 7 User Story sem tag, todos
  entregues no período.
- **Então (sucesso)**: `f4pReconciliacao()` para o time retorna
  `{team, vazao:38, ts:27, planejado:4, naoPlanejado:7, soma:38, ok:True}`.
- **Teste**: `test_reconciliacao_bate_com_o_exemplo_exato_do_usuario`

### Regra: divergência de configuração de tipos é sinalizada, não escondida

**Garante que**: se `CFG.f4p.types` (Vazão) conta um tipo que os outros dois quadrantes não cobrem
(ex.: um terceiro tipo além de Technical Story e dos tipos de User Story), a soma diverge — e é
exatamente esse erro de configuração que a conferência deve sinalizar (`ok: False`), em vez de
esconder a diferença.

- **Dado**: `CFG.f4p.types` inclui `"internal bug"` além dos tipos padrão; 1 Internal Bug entregue
  (conta só no Vazão) + 1 User Story sem tag entregue.
- **Então (sucesso)**: `{team, vazao:2, ts:0, planejado:0, naoPlanejado:1, soma:1, ok:False}` — a
  soma (1) não bate com o Vazão (2), a divergência real do Internal Bug.
- **Teste**: `test_reconciliacao_sinaliza_divergencia_quando_configuracao_de_tipos_diverge`
- **Cenário de falha coberto**: uma configuração de tipos inconsistente entre os quadrantes passaria
  despercebida — os três números pareceriam corretos individualmente, mas não bateriam entre si, e
  ninguém perceberia sem essa checagem explícita.

### Regra: o banner de divergência só aparece quando há divergência real

**Garante que**: `.f4p-recon` (o aviso visual) só é renderizado para times com `ok: False`; some
assim que a configuração volta a bater.

- **Dado**: um time com divergência de tipo (aparece o banner citando o time e "Vazão Realizado");
  depois `CFG.f4p.types` volta ao padrão e re-renderiza.
- **Então (sucesso)**: banner presente no primeiro caso; ausente depois da correção.
- **Teste**: `test_reconciliacao_banner_aparece_so_quando_ha_divergencia`
