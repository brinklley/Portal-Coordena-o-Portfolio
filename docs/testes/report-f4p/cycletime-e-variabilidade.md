# Testes: Report F4P — Quadrantes 1–2 (CycleTime e Variabilidade)

Ver `docs/testes/report-f4p/README.md` para as regras compartilhadas (janela `f4pWindow`, habilitação
do painel). Regras de negócio: §12.2 (CycleTime) e §12.3 (Variabilidade). Decisões `0011`–`0013`.

## Regra: P95/P50 por interpolação linear (PERCENTIL.INC, estilo planilha)

**Garante que**: `percentil(lista, p)` reproduz exatamente `PERCENTIL.INC` do Excel/Sheets
(interpolação linear entre os dois valores mais próximos, não o método "nearest-rank"), e devolve
`null` para lista vazia.

- **Dado**: `CTS = [10, 20, 25, 30, 35, 40, 45, 50, 60, 100]` (mesma amostra de
  `tests/gerar_fixtures.py::f4p`), com P95 e P50 calculados manualmente (`82.0` e `37.5`).
- **Então (sucesso)**: `percentil(CTS, .95)` ≈ 82,0; `percentil(CTS, .5)` ≈ 37,5;
  `percentil([], .5) === null`.
- **Cenário de falha coberto**: um método de percentil diferente (ex.: "nearest-rank") produziria um
  número que não bate com o que o usuário calcularia na planilha original, quebrando a conferência
  cruzada.
- **Teste**: `test_percentil_por_interpolacao_linear`

## Regra: CycleTime (P95) e Variabilidade (P95/P50) do time batem com cálculo independente

**Garante que**: `f4pMetrics(team)` devolve `p95` (CycleTime, quadrante 1), `p50` e `varr = p95/p50`
(Variabilidade, quadrante 2), calculados exatamente com a mesma amostra e fórmula validadas acima.

- **Dado**: `f4p.xlsx`, time CORE com os `CTS` conhecidos.
- **Então (sucesso)**: `m.n === len(CTS)`; `m.p95` ≈ 82,0; `m.p50` ≈ 37,5; `m.varr` ≈
  `82,0/37,5`.
- **Cenário de falha coberto**: um erro na amostragem (itens incluídos/excluídos errado) mudaria a
  contagem `n` e, por consequência, os dois percentis — o teste trava a conferência ponta a ponta.
- **Teste**: `test_p95_p50_conferidos_com_calculo_independente`
- **Relacionado**: regras-de-negocio.md §12.2–§12.3.

## Regra: amostra usa janela rolante no semestre em curso, e o período exato num semestre encerrado

**Garante que**: sem semestre selecionado, ou com o semestre em curso, a amostra usada por CT e
Variabilidade é a janela rolante dos últimos N meses (`f4pWindow`); com um semestre já encerrado
selecionado, a amostra passa a ser só o período daquele semestre (ancorada, não mais rolante).

- **Dado (semestre em curso)**: sem filtro de semestre, e depois com o semestre atual selecionado —
  os dois casos devem dar o mesmo resultado.
- **Então (sucesso)**: `n`, `p95`, `p50` e `varr` idênticos nos dois casos.
- **Dado (semestre passado)**: um item com `deploy` no meio do semestre anterior (`ct:40`) e outro no
  semestre atual (`ct:999`, deve ficar de fora), filtro `S.f.int` = semestre anterior.
- **Então (sucesso)**: `f4pEnabled() === true`; métricas = `{n:1, p95:40, p50:40, varr:1.0}` — só o
  item do semestre anterior entrou.
- **Cenário de falha coberto**: selecionar um semestre encerrado continuaria usando a janela rolante
  de hoje, misturando dados de fora do período que o usuário pediu para analisar; ou o contrário — o
  semestre em curso ficaria restrito ao período exato, perdendo a janela rolante que faz sentido
  para um período ainda em andamento.
- **Testes**: `test_amostra_do_semestre_atual_usa_janela_corrida`,
  `test_amostra_ancora_no_semestre_passado_ja_encerrado`
- **Relacionado**: decisão `0013`; `docs/testes/report-f4p/README.md` (janelas compartilhadas).

## Regra: CT acima do máximo do time colore a célula de vermelho

**Garante que**: a célula de CT no painel reflete o mesmo limite `max` configurado por time
(§8.1), pintando de vermelho quando ultrapassado.

- **Dado**: `CFG.teams = {core: {max: 20}}`, `recomputeHealth()`.
- **Então (sucesso)**: existe ao menos uma célula com a classe `.f4p-bad` no painel.
- **Cenário de falha coberto**: o painel calcularia o CT corretamente mas não sinalizaria
  visualmente quando ele está fora do limite aceitável do time.
- **Teste**: `test_ct_acima_do_maximo_fica_vermelho`

## Regra: validação de configuração — variabilidade mínima precisa ser menor que a máxima

**Garante que**: o formulário de Configurações › Report F4P bloqueia salvar se `min >= max` para a
faixa de Variabilidade de um time, com mensagem explicando o motivo (mesmo padrão de validação de
`docs/testes/configuracoes.md`).

- **Dado**: `min=4`, `max=3` para o CORE.
- **Então (sucesso)**: `.cfg-err` contém "variabilidade mínima precisa ser menor"; `#cfgBg`
  continua visível (não salvou).
- **Cenário de falha coberto**: uma faixa min/max invertida seria salva e nunca classificaria
  corretamente uma célula como dentro ou fora da faixa.
- **Teste**: `test_valida_variabilidade_minima_maior_que_maxima`

## Regra: configuração de meses da janela e faixa min/max por time persiste e exporta

**Garante que**: `CFG.f4p.months` (tamanho da janela rolante) e `CFG.f4p.teams[time].min/max`
(faixa de Variabilidade) sobrevivem a `saveCfg()` e aparecem no JSON de `#cfgExport`.

- **Dado**: `cfgF4pMonths = 9`, `min=2`, `max=4` para o CORE.
- **Então (sucesso)**: o JSON exportado contém `"months": 9`, `"min": 2`, `"max": 4`; depois de
  salvar, `CFG.f4p.months === 9` e `CFG.f4p.teams.core === {min:2, max:4}`.
- **Cenário de falha coberto**: a configuração de janela/faixa se perderia ao recarregar a página ou
  não seria transferível entre máquinas via exportação.
- **Teste**: `test_configuracao_f4p_persiste_e_entra_na_exportacao`

## Regra: importar configuração antiga sem F4P usa os padrões

**Garante que**: `normCfg({})` preenche os padrões de F4P quando o campo não existe na configuração
importada: 6 meses, tipos `["user story", "technical story"]`, tag de expedição `"urgent"`, sem
metas por time.

- **Teste**: `test_importar_configuracao_antiga_sem_f4p_usa_padrao`
- **Cenário de falha coberto**: importar uma configuração salva antes do Report F4P existir
  quebraria o painel por falta de um campo esperado, em vez de cair graciosamente nos padrões.
