# Testes: Report F4P — Quadrante 6 (Roadmap – Épicos: roadmap vs. entregue vs. atual)

Ver `docs/testes/report-f4p/README.md` para as regras compartilhadas. Regras de negócio: §12.7.
Decisões `0025`, `0026`.

**Diferença estrutural dos demais quadrantes**: este opera sobre os cards do quadro de **Épicos**
(`S.model.epis`, `S.model.stages.epi`, `e.st`, `e.target`), não sobre `S.model.ops` (itens de time).
"Fechado" aqui é a última coluna do **próprio quadro de Épicos**, não a categoria de fluxo (`catOf`)
de nenhum time.

## Regra: Roadmap Interno usa o Target Date/semestre do próprio épico

**Garante que**: com o filtro de semestre **Interno** selecionado, "Roadmap" conta épicos cujo
`e.interno` (Target Date/semestre próprio) bate com o semestre filtrado — sem olhar o vínculo com
iniciativa.

- **Dado**: um épico com `interno` no semestre filtrado (conta) e outro com `interno` de outro
  semestre (não conta), ambos com item do mesmo time.
- **Teste**: `test_roadmap_interno_usa_target_date_do_proprio_epico`

## Regra: Roadmap Executivo usa o vínculo com a iniciativa, ignorando o Target Date do próprio épico

**Garante que**: com o filtro **Executivo** selecionado, "Roadmap" sobe Iniciativa → Release →
Épico pela iniciativa cujo `AnoSemestreRoadmap` bate com o semestre selecionado — independente do
Target Date/semestre do próprio épico.

- **Dado**: um épico com Target Date de outro semestre, mas vinculado (via release) a uma iniciativa
  do semestre selecionado (conta); um épico com Target Date do semestre selecionado, mas sem vínculo
  com nenhuma iniciativa do roadmap executivo (não conta).
- **Teste**: `test_roadmap_executivo_usa_vinculo_com_a_iniciativa_ignorando_target_date_do_epico`
- **Cenário de falha coberto**: os dois filtros (Interno/Executivo) usarem o mesmo critério
  misturaria roadmaps que têm fontes de verdade diferentes por natureza (compromisso do time vs.
  compromisso com a iniciativa executiva).

## Regra: Roadmap entregue é o subconjunto já fechado do Roadmap

**Teste**: `test_roadmap_entregue_e_subconjunto_ja_fechado` — de 2 épicos no Roadmap, só 1 fechado
(`st:1`) conta como entregue.

## Regra: "Atual" ignora Target Date e vínculo com iniciativa — conta só pela data de fechamento no período

**Garante que**: "Atual" tem um critério deliberadamente mais simples que "Roadmap": conta épicos
fechados dentro do período do semestre, mesmo que o Target Date/semestre do épico seja outro (filtro
Interno) ou que não tenha vínculo com nenhuma iniciativa (filtro Executivo) — pedido explícito do
usuário, para não perder do "Atual" um fechamento real só porque o cadastro não bate.

- **Testes**: `test_atual_ignora_target_date_no_filtro_interno`,
  `test_atual_ignora_vinculo_com_iniciativa_no_filtro_executivo`
- **Cenário de falha coberto**: um épico fechado de fato no período ficaria fora do "Atual" só por
  ter Target Date desatualizado ou faltar vínculo com iniciativa — mascarando entrega real.

## Regra: Roadmap filtra por tipo de épico configurado (padrão "Epic")

**Garante que**: só itens do(s) tipo(s) em `CFG.f4p.epiTypes` (padrão `["epic"]`) entram no Roadmap
— um tipo diferente (ex.: "User Story" usado como card no quadro de épicos) não conta, a menos que
seja adicionado à configuração.

- **Testes**: `test_roadmap_filtra_por_tipo_de_epico_configurado`,
  `test_roadmap_usa_tipos_de_epico_configuraveis`,
  `test_configuracao_epi_types_tem_padrao_epic`,
  `test_configuracao_epi_types_persiste_e_entra_na_exportacao`

## Regra: um épico só conta para o time dos seus itens filhos (nunca por Target Date ou iniciativa)

**Garante que**: o vínculo épico↔time é sempre decidido pelos itens filhos (Parent → Child) — nunca
pelo Target Date do épico nem pelo vínculo com a iniciativa — em todos os três números (Roadmap,
Roadmap entregue, Atual) e nos dois filtros (Interno e Executivo). Um épico com itens filhos de mais
de um time conta para cada time que tem item vinculado (não é "dono único"); um épico sem nenhum
item do time filtrado não conta para ele.

- **Cenário de falha coberto** (relatado pelo usuário): um épico aparecia contabilizado no time
  errado quando todos os seus itens filhos eram de outro time — ex.: um épico vinculado (via
  iniciativa do Roadmap Executivo) ao time CORE, mas cujos itens filhos eram todos do MOBILE, contava
  erroneamente para o CORE.
- **Testes** (cobrindo cada combinação número × filtro):
  `test_roadmap_conta_so_epicos_com_item_do_time` (caso básico: só conta para o time com item
  vinculado),
  `test_roadmap_executivo_epico_conta_so_para_o_time_dos_itens_filhos`,
  `test_roadmap_interno_epico_conta_so_para_o_time_dos_itens_filhos`,
  `test_roadmap_entregue_epico_conta_so_para_o_time_dos_itens_filhos`,
  `test_atual_epico_conta_so_para_o_time_dos_itens_filhos`,
  `test_roadmap_epico_com_itens_de_dois_times_conta_para_ambos`
- **Relacionado**: decisão `0026-report-f4p-roadmap-epicos-vinculo-epico-time.md` — a investigação
  confirmou que a decisão `0025` já implementava a regra corretamente; estes testes travam o
  comportamento explicitamente para os casos que ainda não tinham um teste dedicado.

## Regra: tendência soma épicos abertos ao mês corrente (mesmo padrão do Vazão)

**Garante que**: mesma regra da decisão `0023`, adaptada ao fluxo de Épicos — mês atual + épicos do
Roadmap ainda abertos vs. média (arredondada para cima) dos meses anteriores.

- **Testes**: `test_roadmap_tendencia_soma_abertos_ao_mes_atual_exemplo_melhora` (média 1, atual 0,
  +3 abertos → `▲`), `test_roadmap_tendencia_soma_abertos_ao_mes_atual_exemplo_piora` (média 2,
  atual 0, +1 → `▼`), `test_roadmap_tendencia_soma_abertos_ao_mes_atual_exemplo_estavel` (média 3,
  atual 2, +1 → `◆`), `test_roadmap_tendencia_sem_meses_anteriores_fica_neutra`.
- **Relacionado**: `docs/testes/report-f4p/README.md` (convenção compartilhada).

## Regra: clique nos três números abre a lista com a Situação do próprio quadro de Épicos

**Garante que**: diferente dos demais quadrantes, a Situação mostrada no modal é a coluna do próprio
quadro de Épicos (ex. "Backlog"), não a categoria de fluxo operacional (`catOf`) de nenhum time.

- **Teste**: `test_roadmap_clique_no_numero_abre_lista_de_epicos_com_situacao_do_proprio_quadro`

## Regra: o quadrante aparece calculado no painel

**Teste**: `test_roadmap_epicos_aparece_calculado_no_painel`
