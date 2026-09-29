# Testes: Actionable (métricas acionáveis por time no período do roadmap)

Cobre `tests/test_actionable.py` (29 testes). Ver `docs/regras-de-negocio.md` §13; decisões `0041`, `0042`, `0044`.
Primeira versão (MVP): CycleTime, Distribuição Vazão por mês e Burnup Reserva têm regra definida; o
quarto quadrante segue "em definição".

## Regra: habilitado com Time + Roadmap, desabilitado num semestre futuro

**Garante que**: mesmo gate da Visão analítica/Report F4P — precisa de Time E Roadmap (interno ou
executivo); um semestre ainda não começado desabilita a aba e recolhe o painel se já estiver aberto.

- **Testes**: `test_aba_desabilitada_sem_time_e_roadmap`,
  `test_semestre_futuro_desabilita_e_fecha_o_painel`
- **Cenário de falha coberto**: o painel ficaria acessível sem contexto suficiente para calcular nada,
  ou continuaria mostrando dados de um semestre que ainda não pode ter ocorrido.

## Regra: a dispersão de CycleTime usa a mesma amostra e Reserva do Report F4P

**Garante que**: `actCtScatterData` não recalcula nada por conta própria — reaproveita `f4pSample`
(itens concluídos, tipos configurados, dentro da janela do semestre) e `limitsOf(time).max` como
Reserva, os mesmos usados pelo quadrante CycleTime do Report F4P (§12.2). O "Atual" do gráfico é o
mesmo P95 de `f4pMetrics`.

- **Então (sucesso)**: os IDs dos pontos do gráfico batem exatamente com os IDs de `f4pSample`; a
  Reserva bate com `limitsOf(time).max`; o Atual bate com `f4pMetrics(time).p95`.
- **Cenário de falha coberto**: o Actionable mostraria uma amostra ou uma Reserva diferentes das do
  Report F4P para o mesmo time e período, quebrando a conferência cruzada entre os dois painéis.
- **Testes**: `test_scatter_ct_usa_mesma_amostra_e_reserva_do_report_f4p`,
  `test_scatter_atual_e_o_p95_da_amostra`

## Regra: pontos acima da Reserva ficam destacados; sem itens, mostra mensagem

- **Teste**: `test_scatter_pontos_acima_da_reserva_ficam_destacados` — confirma a classe
  `.act-dot-bad` num ponto com CT acima da Reserva.
- **Teste**: `test_scatter_sem_itens_no_periodo_mostra_mensagem` — sem nenhum item concluído no
  período, mostra "Nenhum item concluído no período" em vez de um gráfico vazio.

## Regra: clicar num ponto do gráfico fecha o painel e navega até o item

**Garante que**: cada ponto é um link direto (`data-act-go`), igual ao padrão de transparência do
resto do portal — clicar fecha o Actionable e preenche `#fBusca` com o ID do item.

- **Teste**: `test_clique_no_ponto_do_scatter_fecha_o_painel_e_navega`

## Regra: a Distribuição Vazão por mês sempre mostra os 6 meses inteiros do semestre (decisão 0044)

**Garante que**: diferente do Burnup Reserva (que para em "hoje" num semestre em curso),
`actDistMonths` sempre devolve os 6 meses do semestre selecionado, do início ao fim — os meses ainda
não decorridos entram no gráfico como referência do que falta, não são escondidos.

- **Teste**: `test_dist_meses_cobrem_o_semestre_inteiro_mesmo_em_curso`
- **Cenário de falha coberto**: se o gráfico parasse em "hoje" como o Burnup, um semestre recém-começado
  mostraria só 1 ou 2 meses, escondendo a visão do período inteiro que o usuário pediu para acompanhar.

## Regra: cada item entregue no mês vira User Story, Technical Story ou "demais" (partição exata)

**Garante que**: `actDistBuckets` reaproveita os mesmos critérios dos quadrantes homônimos do Report
F4P — User Story = `CFG.f4p.usTypes` (§12.8); Technical Story = tipo fixo "technical story" (§12.5); o
resto (sem bugs, já excluídos antes) vira "demais". As três fatias somam sempre o total da amostra do
mês, sem sobreposição.

- **Dado**: 3 User Story + 1 Technical Story entregues no mês.
- **Então (sucesso)**: `{total: 4, usPct: 75, tsPct: 25, demaisPct: 0}`.
- **Teste**: `test_dist_classifica_user_story_technical_story_e_demais`
- **Teste do balde "demais"**: `test_dist_tipo_fora_de_user_story_e_technical_story_conta_como_demais`
  — um tipo qualquer (ex.: Feature) que não é bug, User Story nem Technical Story cai em "demais",
  confirmando que o balde é genuinamente residual (não restrito a `CFG.f4p.types`).

## Regra: tipos de bug são excluídos por inteiro da amostra, e são configuráveis

**Garante que**: itens cujo tipo está em `CFG.act.bugTypes` (padrão bug/internal bug/external bug) não
entram nem no total do mês, nem em nenhuma das três fatias — e a lista é configurável, como toda outra
lista de tipos do Report F4P.

- **Teste (padrão)**: `test_dist_exclui_tipos_bug_da_amostra` — Bug, Internal Bug e External Bug somem
  da amostra; só o User Story do mês conta.
- **Teste (configurável)**: `test_dist_tipos_bug_sao_configuraveis` — trocar `CFG.act.bugTypes` para
  `["custom bug"]` faz "Internal Bug" (não mais na lista) voltar a contar como "demais", e "Custom Bug"
  (o novo tipo configurado) ser excluído no lugar.
- **Cenário de falha coberto**: sem essa exclusão, um item de bug entraria no balde "demais" e distorceria
  a leitura de "quanto da entrega do mês é trabalho planejado (US/TS) vs. o resto" — misturar bug com
  "demais" tornaria a métrica pouco acionável, já que bug é outra categoria de trabalho.

## Regra: mês sem nenhum item na amostra mostra uma barra cinza fraca com "0,00%"

**Garante que**: um mês sem nenhuma entrega, ou cuja única entrega é de tipo bug (excluído por inteiro),
renderiza uma única fatia cinza (`.act-dist-none`), não clicável, ocupando a barra inteira, rotulada
"0,00%" — a mesma tratativa cobre, sem lógica extra, os meses ainda não decorridos de um semestre em
curso (regra do print de inspiração do usuário).

- **Teste**: `test_dist_mes_sem_registro_mostra_zero_porcento_cinza` — confirma as 6 linhas do gráfico,
  cada uma com a fatia cinza "0,00%" e nenhum botão clicável, para um time sem nenhum dado no semestre.
- **Teste (bug isolado)**: `test_dist_barra_sem_registro_nao_conta_bug_isolado_como_registro` — um mês
  cuja única entrega é Bug tem `total === 0` (não `1`), confirmando que a exclusão de bug acontece antes
  da contagem do total, não depois.

## Regra: a porcentagem de cada fatia arredonda para 2 casas decimais (vírgula)

**Garante que**: o rótulo usa `dec2` (nova função, mesmo padrão de `dec1` já existente) — 2 casas
decimais sempre, mesmo numa dízima periódica, com vírgula como separador decimal (padrão pt-BR do
resto do portal).

- **Dado**: 1 item User Story de 3 no total (1/3 = 33,333...%).
- **Então (sucesso)**: `"33,33"` — nem truncado, nem com mais ou menos casas decimais.
- **Teste**: `test_dist_porcentagem_arredonda_para_duas_casas_decimais`

## Regra: cada fatia é clicável separadamente, abrindo só os itens daquele tipo no mês

**Garante que**: User Story, Technical Story e "demais" abrem listas independentes (`f4pItemsModal`) —
clicar numa fatia não mistura itens dos outros tipos, mesmo mês.

- **Teste**: `test_dist_clique_em_cada_fatia_abre_so_os_itens_daquele_tipo_no_mes`
- **Cenário de falha coberto**: um clique único por mês (em vez de por fatia) obrigaria o usuário a abrir
  a Visão analítica/Report F4P e filtrar manualmente por tipo para saber quais itens formam cada
  porcentagem — quebrando o padrão de transparência por número já estabelecido no resto do portal.

## Regra: o quadrante aparece no painel com a legenda dos 4 tipos de fatia

**Teste**: `test_dist_aparece_no_painel_com_legenda`

## Regra: `CFG.act.bugTypes` tem padrão e persiste na exportação

**Testes**: `test_configuracao_act_bug_types_tem_padrao`,
`test_configuracao_act_bug_types_persiste_e_entra_na_exportacao`

## Regra: "Reservado" do Burnup é o mesmo conjunto da Capacidade da Visão analítica

**Garante que**: `actBurnupData().escopo` é exatamente `anData().cap` — itens com a tag de capacidade
do roadmap (`CFG.anTag`) nos épicos do roadmap do time+semestre, em **qualquer status**, não só os já
entregues (diferente da Reserva do quadrante Vazão do Report F4P, que só existe dentro do já entregue).

- **Dado**: 2 itens com a tag ROADMAP (um em Backlog, um em WIP) e 1 sem a tag.
- **Então (sucesso)**: `escopo === cap === 2`.
- **Cenário de falha coberto**: se o Burnup usasse a Reserva do Vazão do Report F4P em vez da
  Capacidade da Visão analítica, o escopo ficaria restrito ao que já foi entregue, e "quanto falta"
  nunca sairia de zero — o gráfico perderia o sentido.
- **Teste**: `test_burnup_reservado_e_o_mesmo_da_capacidade_da_visao_analitica`

## Regra: Entregue acumula mês a mês dentro do semestre

**Garante que**: o subconjunto do Reservado já na categoria de fluxo Vazão entra na contagem
acumulada a partir do mês em que foi entregue (inclusive), permanecendo nos meses seguintes; um item
nunca entregue nunca entra, mas continua contando no escopo (por isso "falta").

- **Dado**: 3 itens reservados — um entregue no 1º mês do semestre, um entregue no 2º mês, um ainda
  em Backlog.
- **Então (sucesso)**: `cumulative[0] === 1`, `cumulative[1] === 2`, `entreguesN === 2`,
  `faltam === 1`.
- **Cenário de falha coberto**: um item entregue apareceria só no mês exato da entrega (sem acumular
  para os meses seguintes), fazendo a linha de "entregue" cair em vez de só subir — o oposto de um
  burnup.
- **Teste**: `test_burnup_entregue_acumulado_por_mes`

## Regra: entrega no último dia do mês conta dentro desse mês (limite inclusivo)

**Garante que**: o corte de "fim do mês" usado para acumular o Entregue inclui o próprio último dia —
um item entregue nessa data não fica empurrado para o mês seguinte.

- **Dado**: um item entregue exatamente no último dia do primeiro mês do semestre.
- **Então (sucesso)**: `cumulative[0] === 1`.
- **Cenário de falha coberto**: um corte exclusivo (`<` em vez de `<=`) faria esse item só aparecer no
  mês seguinte, subestimando a entrega real do primeiro mês em um dia específico do calendário —
  exatamente o tipo de erro de limite que passa despercebido sem um teste dedicado.
- **Teste**: `test_burnup_entregue_no_ultimo_dia_do_mes_conta_nesse_mes`

## Regra: resumo do Burnup e transparência por clique — inclusive em "faltam"

**Garante que**: o resumo textual mostra Reservado/Entregue/Faltam, e os **três** números são
clicáveis, abrindo a lista dos itens exatos de cada grupo (mesmo modal `f4pItemsModal` do Report F4P)
— não só Reservado e Entregue.

- **Cenário de falha coberto** (melhoria pedida pelo usuário depois de usar a 1ª versão): "faltam"
  ficava sem a mesma transparência dos outros dois números — o usuário via quantos itens faltavam mas
  não tinha como saber **quais**, sem abrir a Visão analítica/Report F4P e cruzar manualmente.
- **Testes**: `test_burnup_resumo_mostra_reservado_entregue_e_faltam`,
  `test_burnup_clique_em_reservado_abre_lista_dos_itens_reservados`,
  `test_burnup_clique_em_faltam_abre_lista_dos_itens_ainda_nao_entregues`
- **Relacionado**: decisão `0042-burnup-clique-em-faltam.md`.

## Regra: uma entrega fora do período do semestre selecionado conta como Faltam, não como Entregue

**Garante que**: Entregue e Faltam formam uma partição exata do Reservado (`entregues.length +
faltamItems.length === capItems.length` sempre) — para isso, "Entregue" só considera itens cuja saída
caiu **dentro do período do semestre selecionado** (mesmo limite que já valia para o número exibido);
um item entregue depois desse período (ex.: um semestre encerrado cuja entrega só saiu no semestre
seguinte) conta em Faltam, não em Entregue.

- **Dado**: 1 item reservado de um semestre já encerrado, entregue no dia seguinte ao fim desse
  semestre (já no semestre seguinte).
- **Então (sucesso)**: `entreguesN === 0`, `faltam === 1`, o item aparece em `faltamItems`, não em
  `entregues`.
- **Cenário de falha coberto**: antes deste ajuste, a lista aberta ao clicar em "Entregue" não tinha
  esse limite de período (só o número exibido tinha) — uma entrega tardia apareceria na lista de
  "Entregue" mesmo não sendo contada no número, e ao mesmo tempo contaria como "falta" pelo número
  exibido: o item "existia e não existia" em Entregue dependendo de onde o usuário olhasse.
- **Teste**: `test_burnup_entrega_fora_do_periodo_do_semestre_conta_como_faltam`
- **Relacionado**: decisão `0042`.

## Regra: o quarto quadrante mostra "em definição"

**Garante que**: a estrutura fixa de 4 quadrantes em 2 colunas já existe desde a primeira versão,
mesmo sem regra definida para o último — mesmo padrão do Report F4P para um quadrante sem regra
fechada (`f4pCard`, "Regra de cálculo ainda em definição.").

- **Teste**: `test_quadrante_4_mostra_em_definicao`
- **Relacionado**: decisões `0041` ("Próximos passos"), `0044` (o terceiro quadrante ganhou regra).

## Regra: os três painéis laterais são mutuamente exclusivos

**Garante que**: abrir a Visão analítica ou o Report F4P fecha o Actionable, e abrir o Actionable
fecha os outros dois — mesma convenção já existente entre Visão analítica e Report F4P, estendida ao
terceiro painel.

- **Cenário de falha coberto**: dois painéis abertos ao mesmo tempo disputariam a mesma área da tela
  (mesma classe `.an-panel`, mesma posição), sobrepondo conteúdo.
- **Testes**: `test_abrir_visao_analitica_ou_f4p_fecha_o_actionable`,
  `test_abrir_actionable_fecha_visao_analitica_e_f4p`
