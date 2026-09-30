# Testes: Visão analítica do roadmap do time

Cobre `tests/test_visao_analitica.py` (15 testes). Ver `docs/regras-de-negocio.md` §10; decisões
`0027`, `0028`, `0029`, `0036`, `0039`.

## Regra: Projetada é a soma do QTD de cada épico mostrado na tabela

**Garante que**: o número "Projetada" do cabeçalho não é uma contagem à parte — é sempre a soma
exata dos valores de QTD que aparecem nas linhas da própria tabela (transparência: o que está
somado é o que está visível).

- **Dado**: um épico sintético com 3 itens (Backlog, WIP, Vazão).
- **Então (sucesso)**: `d.proj === 3`; `soma(row.qtd para cada row) === d.proj`.
- **Cenário de falha coberto**: o número do cabeçalho divergiria da soma das linhas visíveis,
  quebrando a confiança do usuário no relatório (o total não bateria com o que ele pode conferir
  manualmente).
- **Teste**: `test_projetada_e_soma_do_qtd_dos_epicos_da_tabela`
- **Relacionado**: decisão `0027`.

## Regra: Capacidade é a soma dos itens reservados (com a tag) de cada épico

**Garante que**: "Capacidade" soma só os itens marcados com a tag configurável de roadmap
(`CFG.anTag`, padrão `ROADMAP`) — mesma tag usada no Report F4P (Vazão/User Story) — e essa tag é
configurável por organização.

- **Dado**: 3 itens, 2 com a tag ROADMAP.
- **Então (sucesso)**: `d.cap === 2`; a soma de `row.reservados.length` bate com `d.cap`; trocar
  `CFG.anTag` para `"CAPACIDADE"` faz só os itens com a nova tag contarem (a tag antiga deixa de
  contar).
- **Cenário de falha coberto**: a Capacidade contaria itens com a tag antiga mesmo depois do time
  trocar de convenção de tag, inflando o número reservado de forma incorreta.
- **Testes**: `test_capacidade_e_soma_dos_reservados_dos_epicos_da_tabela`,
  `test_capacidade_usa_a_tag_configuravel`
- **Relacionado**: decisão `0027`.

## Regra: a linha do épico mostra a quantidade reservada (sem o badge "X US")

**Garante que**: cada linha da tabela mostra "N reservado" para o próprio épico; o antigo badge "X
US" (redundante com a coluna QTD) foi removido.

- **Dado**: épico com 1 item marcado ROADMAP entre 2 itens.
- **Então (sucesso)**: `"1 reservado"` aparece no corpo da tabela (`#anBody`); a string `"US"` não
  aparece mais (isolada, como badge) em nenhuma linha.
- **Cenário de falha coberto**: a linha mostraria duas informações redundantes (badge "X US" e
  coluna QTD) sem indicar quantos itens daquele total estão reservados no roadmap.
- **Testes**: `test_linha_do_epico_mostra_quantidade_reservada`,
  `test_linha_nao_mostra_mais_o_badge_x_us`
- **Relacionado**: decisão `0028`.

## Regra: os números clicáveis do cabeçalho abrem a lista exata dos itens somados

**Garante que**: clicar em "Capacidade" ou "Projetada" no cabeçalho abre um modal com a lista exata
dos itens que entraram naquela soma (mesma transparência do Report F4P) — Capacidade mostra só os
com a tag; Projetada mostra todos, com a situação seguindo `catOf` (mesma categorização do resto do
portal) e, para itens em Vazão, a data de saída.

- **Dado**: épico com itens variados (com/sem tag, com/sem data de saída).
- **Quando**: clica em `button[data-an-items="cap"]` ou `="proj"`.
- **Então (sucesso)**: a contagem de linhas do modal bate exatamente com o subconjunto esperado; a
  situação exibida usa o rótulo de categoria (ex. "Vazão"), com a data de saída quando aplicável
  (`"10/02/2026"`).
- **Cenário de falha coberto**: o modal mostraria um conjunto de itens diferente do número clicado,
  ou usaria "Fechado"/"Aberto" genérico em vez da categoria real de fluxo do item.
- **Testes**: `test_clique_na_capacidade_abre_lista_so_dos_itens_com_a_tag`,
  `test_clique_na_projetada_abre_lista_com_todos_os_itens`
- **Relacionado**: decisão `0027`; `docs/testes/report-f4p/README.md` (mesmo padrão de transparência).

## Regra: clicar num item do modal fecha a Visão analítica e navega até ele no quadro

**Garante que**: cada item listado no modal é um link direto — clicar nele fecha tanto o modal
quanto o painel da Visão analítica e leva o usuário até aquele item no quadro principal (preenche
`#fBusca` com o ID).

- **Então (sucesso)**: depois do clique, `#f4pItemsBg` não está mais visível, `#anPanel` perde a
  classe `open`, e `#fBusca` contém o ID do item clicado.
- **Cenário de falha coberto**: o clique navegaria para o item mas deixaria o modal ou o painel
  analítico aberto por cima, escondendo o item recém-encontrado.
- **Teste**: `test_clique_no_item_do_modal_fecha_a_visao_analitica_e_navega`

## Regra: QTD e "reservado" de cada linha abrem só os itens daquele épico específico

**Garante que**: diferente dos números do cabeçalho (que somam todos os épicos da tabela), clicar em
QTD ou "reservado" de uma linha específica abre só os itens daquele épico — sem misturar itens de um
épico vizinho do mesmo time.

- **Dado**: um time com dois épicos, cada um com itens próprios.
- **Quando**: clica em `button[data-an-epi="EPI1_..."][data-an-epi-items="qtd"]` (ou `="res"`).
- **Então (sucesso)**: os IDs no modal são exatamente os do Épico 1 (nunca os do Épico 2); o título
  do modal cita o épico específico.
- **Cenário de falha coberto**: o clique na linha de um épico abriria itens de outro épico do mesmo
  time, misturando os conjuntos e invalidando a conferência item a item.
- **Testes**: `test_clique_no_qtd_da_linha_abre_so_os_itens_daquele_epico`,
  `test_clique_no_reservado_da_linha_abre_so_os_itens_reservados_daquele_epico`
- **Relacionado**: decisão `0028`.

## Regra: a coluna Status usa o mesmo agrupador por categoria do card do épico

**Garante que**: a coluna Status ganha uma linha com o agrupador (Backlog/Discovery/WIP/Vazão, com
quadradinho colorido e contagem), reaproveitando `distGroup(m)` do card do épico no quadro —
inclusive mostrando categorias com contagem zero (para manter a mesma "forma" visual do card).

- **Dado**: um épico com itens em cada categoria (2 Backlog, 0 Discovery, 1 WIP, 3 Vazão).
- **Então (sucesso)**: o texto mostra "Backlog 2", "Discovery 0" (mesmo zerado), "WIP 1", "Vazão 3".
- **Cenário de falha coberto**: uma categoria sem nenhum item ficaria simplesmente ausente da linha,
  quebrando a comparação visual com o card do épico no quadro (que sempre mostra as 4 categorias).
- **Teste**: `test_status_mostra_o_agrupador_por_categoria_do_card_do_epico`
- **Relacionado**: decisão `0029`.

## Regra: o agrupador de Status conta só os itens do time filtrado

**Garante que**: quando um épico é compartilhado entre times (itens de times diferentes vinculados
ao mesmo épico), o agrupador de categoria na Visão analítica conta só os itens do time em análise —
usa `epiMetrics(e, team)`, a mesma fonte já usada por QTD/Capacidade/Projetada.

- **Dado**: um épico com um item do time A (WIP) e um item do time B (Vazão), analisando o time A.
- **Então (sucesso)**: "WIP 1" aparece; "Vazão 0" aparece (o item Vazão é do outro time, não conta).
- **Cenário de falha coberto**: o agrupador contaria itens de outro time vinculados ao mesmo épico,
  inflando a categoria errada e divergindo do QTD (que já filtra por time corretamente).
- **Teste**: `test_status_agrupador_conta_so_os_itens_do_time_filtrado`
- **Relacionado**: decisão `0029`.

## Regra: a fase/coluna da Status considera só os itens reservados, não todo o vínculo do time (decisão 0049)

**Garante que**: a fase mostrada em texto (Backlog/Discovery/WIP/Entregue/"Sem reserva") e a coluna do
fluxo do item aberto mais avançado (`farName`) são calculadas só sobre a **Reserva** (itens com a tag
de capacidade, `reservados`) — não sobre todo o vínculo do time com o épico como antes. O agrupador
por categoria (regra acima) continua somando **todos** os itens, com ou sem a tag; só a fase/coluna em
texto muda.

- **Dado**: um item **reservado** (tag `ROADMAP`) em Backlog e um item **não reservado**, mais
  avançado, em WIP.
- **Então (sucesso)**: `reservaPhase === "backlog"` e `farName === "Backlog"` — o item em WIP (fora da
  reserva) não influencia a fase/coluna exibida, mesmo sendo o mais avançado do épico.
- **Cenário de falha coberto**: exatamente o problema relatado pelo usuário — um item fora da reserva
  em WIP fazia o Status mostrar "WIP", dando a entender que o trabalho *reservado* já estava andando,
  quando na verdade era outro item (fora do roadmap) que estava avançado.
- **Teste**: `test_status_usa_so_o_item_reservado_mais_avancado_nao_qualquer_item_do_time`

### Sem nenhum item reservado: "Sem reserva" (não "Sem itens")

**Garante que**: um épico com itens vinculados, mas nenhum com a tag de capacidade, mostra "Sem
reserva" na Status — rótulo próprio, diferente de "Sem itens" (que sugeriria um épico vazio).

- **Teste**: `test_status_mostra_sem_reserva_quando_nenhum_item_tem_a_tag`

### Todos os reservados já em Vazão: "Entregue", mesmo com item não reservado ainda aberto

**Garante que**: se todo item reservado do épico já está em Vazão, a Status mostra "Entregue" — um
item não reservado ainda aberto (Backlog/Discovery/WIP) não impede isso, só aparece no agrupador.

- **Teste**: `test_status_mostra_entregue_quando_so_os_reservados_ja_estao_em_vazao`

### Ordenação pela coluna Status usa a mesma fase exibida

**Garante que**: `anSorted` (clique no cabeçalho "Status") ordena pela fase da Reserva
(`reservaPhase`), não mais pela fase de todos os itens (`m.phase`) — consistente com o que a coluna
agora mostra.

- **Teste**: `test_status_ordena_pela_fase_da_reserva_nao_pela_fase_de_todos_os_itens`
- **Relacionado**: decisão `0049-status-usa-so-itens-reservados-e-cor-do-id-por-categoria.md`.

### Ordem padrão prioriza Entregue, depois WIP, Discovery, Backlog e por último Sem reserva

**Garante que** (decisão `0053`, pedido do usuário): a ordenação padrão da tabela (`AN.sort = "status"`,
`AN.dir = 1`) prioriza visualmente o trabalho mais adiantado — Entregue primeiro, depois WIP, Discovery,
Backlog e, por último, Sem reserva (nenhum item sequer reservado) — em vez da ordem antiga (WIP,
Discovery, Backlog, Sem reserva e só depois Entregue), que não ajudava o usuário a focar no que estava
mais perto da entrega.

- **Dado**: 5 épicos do mesmo time, um em cada fase de Status possível (Entregue, WIP, Discovery,
  Backlog, Sem reserva).
- **Então (sucesso)**: `anSorted` retorna nessa ordem: `["fechado", "wip", "discovery", "backlog",
  "vazio"]`.
- **Teste**: `test_status_ordena_entregue_primeiro_depois_wip_discovery_backlog_e_sem_reserva_por_ultimo`
- **Cenário de falha coberto**: com a ordem antiga, épicos já entregues apareciam no fim da tabela,
  misturados/atrás de épicos sem nenhuma reserva — o usuário precisava rolar a tabela toda pra achar o
  que já estava pronto, em vez de ver primeiro o que está em foco.
- **Relacionado**: decisão `0053-status-prioriza-entregue-depois-wip-discovery-backlog.md`.

## Regra: "ID ou descrição" não filtra a tabela — só destaca a linha correspondente

**Garante que** (decisão `0054`, pedido do usuário): esta tabela — assim como o Report F4P e o
Actionable — só é afetada pelos filtros de roadmap (interno ou executivo), time e responsável. O campo
"ID ou descrição" (`S.f.q`), que reduz a cadeia visível no quadro (whiteboard, §3.1), aqui **não** remove
nenhum épico da lista: `anData()` calcula a visibilidade dos épicos ignorando `q`
(`computeVisible({...S.f, q:""})`), e só marca `row.hl = true` na(s) linha(s) cujo épico, iniciativa ou
algum item de time vinculado bate com o texto digitado — mesmo alcance de match do filtro `q` do quadro
(ID exato ou parte do título), só que sem esconder o resto.

- **Dado**: dois épicos do mesmo time+roadmap; `S.f.q` com o ID de um deles.
- **Então (sucesso)**: `anData().rows.length` continua `2` (nenhum some), e só o épico que bate tem
  `hl: true`.
- **Teste**: `test_id_ou_descricao_nao_filtra_epicos_so_destaca_a_linha_correspondente`
- **Bate por item de time, não só por épico/iniciativa**: um ID de item vinculado ao épico também marca
  `hl: true` na linha do épico pai (o item em si não tem linha própria nesta tabela).
  - **Teste**: `test_id_de_item_do_time_tambem_destaca_o_epico_pai`
- **Cenário de falha coberto**: o usuário reportou (print da tabela "Roadmap MOBILE") que digitar um ID
  reduzia a tabela a uma única linha, escondendo os outros épicos do time+roadmap selecionados — o
  oposto do que essas telas devem fazer, já que aqui o objetivo é o panorama do time no roadmap, não uma
  busca pontual (que já existe no quadro).
- **Report F4P e Actionable**: nunca dependiam de `S.f.q` para nada — seus cálculos sempre iteraram
  `S.model.ops` direto, sem passar por `computeVisible`/`S.V`. Testes de regressão confirmam o número de
  itens de cada painel intacto com `S.f.q` preenchido:
  `test_ignora_filtro_de_id_ou_descricao_so_roadmap_time_e_responsavel_afetam` (em
  `tests/test_report_f4p.py` e em `tests/test_actionable.py`).
- **Relacionado**: decisão `0054-analiticos-ignoram-filtro-de-id-so-destacam.md`.

## Regra: épico órfão (sem release/iniciativa) aparece no roadmap interno, com aviso

**Garante que**: um épico sem vínculo de release/iniciativa, mas com Target Date/semestre próprio
(`e.interno`) dentro do semestre filtrado no roadmap interno, aparece na Visão analítica em vez de
simplesmente sumir do relatório — com o aviso "OBS: SEM INICIATIVA e SEM RELEASE".

- **Dado**: épico com `valid:false`, `parent:null`, `interno:<semestre atual>`, com itens de time.
- **Quando**: filtro por roadmap interno (`S.f.int`) naquele semestre.
- **Então (sucesso)**: `d.proj` conta os itens do épico órfão; `row.orphan === true` para ele; o
  texto renderizado contém "OBS: SEM INICIATIVA e SEM RELEASE".
- **Cenário de falha coberto**: trabalho real de um time (com itens ativos) desapareceria do
  relatório de capacidade só por falta de cadastro completo na hierarquia, subestimando a carga do
  time sem nenhum aviso.
- **Teste**: `test_epico_orfao_aparece_no_roadmap_interno_com_aviso`
- **Relacionado**: decisão `0036-visao-analitica-epico-orfao-roadmap-interno.md`.

## Regra: o aviso de épico órfão só vale para o roadmap interno, não o executivo

**Garante que**: filtrando só por roadmap executivo (que depende do vínculo com iniciativa), o épico
órfão continua fora — o aviso e a inclusão são exclusivos do filtro interno, porque só ali existe um
semestre próprio do épico para comparar.

- **Dado**: o mesmo tipo de épico órfão, mas com `S.f.exec` preenchido e `S.f.int` vazio.
- **Então (sucesso)**: `d.rows === []`.
- **Cenário de falha coberto**: o épico órfão vazaria também para o roadmap executivo, mesmo sem
  nenhuma iniciativa cujo AnoSemestreRoadmap pudesse justificar sua presença ali.
- **Teste**: `test_epico_orfao_nao_aparece_no_roadmap_executivo`
- **Relacionado**: decisão `0036`.

## Regra: o filtro "Responsável da iniciativa" é utilizável com o painel aberto

**Garante que**: o popup do filtro de responsável (`#msPop`) recebe cliques normalmente mesmo com a
Visão analítica (ou o Report F4P) aberta — nenhum painel lateral fica visualmente por cima dele a
ponto de bloquear o clique nas opções.

- **Dado**: painel da Visão analítica aberto (`AN.open === true`).
- **Quando**: clica em `#fOwner` e depois numa opção de `#msList .ms-item`.
- **Então (sucesso)**: `S.f.owners.size === 1` — a opção foi marcada.
- **Cenário de falha coberto**: um popup próprio (não um `<select>` nativo) preso dentro do contexto
  de empilhamento CSS da barra de filtros fica limitado ao `z-index` dessa barra, não ao `z-index` que
  o próprio popup declara — um painel lateral com `z-index` maior que a barra (mas menor que o que o
  popup pede) intercepta o clique mesmo o popup estando visualmente desenhado por cima.
- **Teste**: `test_filtro_responsavel_utilizavel_com_o_painel_aberto`
- **Relacionado**: decisão `0039-filtro-responsavel-atras-do-painel.md`.
