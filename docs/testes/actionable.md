# Testes: Actionable (métricas acionáveis por time no período do roadmap)

Cobre `tests/test_actionable.py` (15 testes). Ver `docs/regras-de-negocio.md` §13; decisão `0041`.
Primeira versão (MVP): só os quadrantes CycleTime e Burnup Reserva têm regra definida.

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

## Regra: resumo do Burnup e transparência por clique

**Garante que**: o resumo textual mostra Reservado/Entregue/Faltam, e os números de Reservado e
Entregue são clicáveis, abrindo a lista dos itens exatos (mesmo modal `f4pItemsModal` do Report F4P).

- **Testes**: `test_burnup_resumo_mostra_reservado_entregue_e_faltam`,
  `test_burnup_clique_em_reservado_abre_lista_dos_itens_reservados`

## Regra: quadrantes 3 e 4 mostram "em definição"

**Garante que**: a estrutura fixa de 4 quadrantes em 2 colunas já existe desde a primeira versão,
mesmo sem regra definida para os dois últimos — mesmo padrão do Report F4P para um quadrante sem
regra fechada (`f4pCard`, "Regra de cálculo ainda em definição.").

- **Teste**: `test_quadrantes_3_e_4_mostram_em_definicao`
- **Relacionado**: decisão `0041` ("Próximos passos").

## Regra: os três painéis laterais são mutuamente exclusivos

**Garante que**: abrir a Visão analítica ou o Report F4P fecha o Actionable, e abrir o Actionable
fecha os outros dois — mesma convenção já existente entre Visão analítica e Report F4P, estendida ao
terceiro painel.

- **Cenário de falha coberto**: dois painéis abertos ao mesmo tempo disputariam a mesma área da tela
  (mesma classe `.an-panel`, mesma posição), sobrepondo conteúdo.
- **Testes**: `test_abrir_visao_analitica_ou_f4p_fecha_o_actionable`,
  `test_abrir_actionable_fecha_visao_analitica_e_f4p`
