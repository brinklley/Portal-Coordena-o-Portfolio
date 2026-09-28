# Testes: Visão analítica do roadmap do time

Cobre `tests/test_visao_analitica.py` (14 testes). Ver `docs/regras-de-negocio.md` §10; decisões
`0027`, `0028`, `0029`, `0036`.

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
