# Testes: Report F4P — regras compartilhadas

O Report F4P (`tests/test_report_f4p.py`, 113 testes — a maior suíte do projeto) cobre 8 quadrantes,
todos com regra de cálculo fechada (decisões `0011` a `0031`, mais `0038`). Ver
`docs/regras-de-negocio.md` §12, `docs/backlog/report-f4p.md`.

Este arquivo documenta o que é **compartilhado entre quadrantes** — a janela de datas, a convenção
de tendência, o padrão de clique-para-ver-itens e a habilitação do painel. Cada quadrante tem seu
próprio arquivo nesta pasta com as regras específicas dele:

- `cycletime-e-variabilidade.md` (Quadrantes 1–2)
- `urgente.md` (Quadrante 3)
- `technical-story.md` (Quadrante 4)
- `vazao.md` (Quadrante 5)
- `roadmap-epicos.md` (Quadrante 6)
- `user-story.md` (Quadrante 7, + conferência cruzada Vazão×TS×US)
- `eficiencia-de-fluxo.md` (Quadrante 8)

## Regra: o painel só habilita com Time E Roadmap selecionados

**Garante que**: o Report F4P (`#f4pTab`) fica desabilitado até que o usuário escolha um time E um
semestre de roadmap (interno ou executivo) — um dos dois filtros sozinho não é suficiente. Escolher
um semestre futuro (sem dados possíveis ainda) desabilita de novo e recolhe o painel se estiver
aberto.

- **Dado**: nenhum filtro, depois só time, depois time + semestre atual, depois semestre futuro (um
  ano à frente — sempre inalcançável no teste).
- **Então (sucesso)**: `#f4pTab` desabilitado nos dois primeiros casos; habilitado no terceiro
  (`F4P.open === true` depois do clique); ao trocar para o semestre futuro, `f4pEnabled() === false`
  e `F4P.open` volta a `false` sozinho (o painel se recolhe).
- **Cenário de falha coberto**: o painel ficaria acessível sem contexto suficiente para calcular
  nada (sem time ou sem semestre), ou continuaria aberto mostrando dados de um semestre que ainda
  não pode ter ocorrido.
- **Testes**: `test_aba_desabilitada_sem_time_e_roadmap`, `test_semestre_futuro_desabilita_e_fecha_o_painel`
- **Relacionado**: decisão `0011`.

## Regra: todos os times aparecem no painel, mesmo com um time filtrado no quadro

**Garante que**: o Report F4P sempre mostra a comparação entre todos os times do modelo (uma coluna
por time) — o filtro de time do quadro principal não restringe as colunas do relatório.

- **Dado**: `times.xlsx` (7 times), time CORE filtrado no quadro.
- **Então (sucesso)**: o número de colunas da tabela do F4P (`<th>`) bate com `S.model.teams.length`.
- **Cenário de falha coberto**: o relatório mostraria só o time filtrado, impossibilitando a
  comparação entre times que é o propósito do painel.
- **Teste**: `test_todos_os_times_aparecem_mesmo_com_time_filtrado`

## Regra: duas janelas de datas distintas, conforme o quadrante

**Garante que**: existem duas funções de janela, cada quadrante usa a que é certa para ele — misturar
as duas produz números que não batem com o período selecionado pelo usuário:

- **`f4pWindow`** (decisão `0013`) — janela **rolante**: sem semestre selecionado, ou com o
  semestre em curso, usa os últimos N meses (`CFG.f4p.months`, padrão 6) a partir de hoje. Com um
  semestre já encerrado selecionado, ancora no período exato daquele semestre. Usada por
  **CycleTime, Variabilidade e Eficiência de fluxo**.
- **`f4pExactSemesterWindow`** (decisão `0017`) — janela **exata do semestre selecionado**, mesmo
  quando é o semestre em curso (não usa janela rolante nunca). Usada por **Urgente, Technical
  Story, Vazão, Roadmap–Épicos e User Story**.
- **Teste explícito da diferença**: `test_eff_janela_reaproveita_f4pwindow_nao_a_exata_do_semestre`
  (em `eficiencia-de-fluxo.md`) confirma que as duas janelas divergem no semestre em curso.
- **Cenário de falha coberto**: trocar a janela de um quadrante pela outra por engano reintroduziria
  exatamente o bug da decisão `0017` — contar itens fechados antes do início do semestre selecionado
  (ver `urgente.md`).
- **Relacionado**: decisões `0013`, `0017`; regras-de-negocio.md §12.1.

## Regra: convenção de tendência ▲▼◆ é compartilhada por todos os quadrantes com tendência

**Garante que**: `▲` = melhora, `▼` = piora, `◆` = estável/neutro (incluindo quando não há meses
anteriores suficientes para comparar). A partir da decisão `0023`, os quadrantes com fluxo de itens
"a caminho" (Vazão, Roadmap–Épicos, User Story) somam o trabalho em WIP/aberto ao mês corrente antes
de comparar com a média dos meses anteriores — e essa média **sempre arredonda para cima**, para que
"empatar com a média" conte como estável, não como melhora por arredondamento.

- **Exemplos-padrão repetidos em cada quadrante aplicável** (mesmos números em Vazão, Roadmap–Épicos
  e User Story, decisão `0023`, exemplos exatos dados pelo usuário):
  - Média 1, mês atual 0, +3 no WIP/aberto: `0+3=3 > 1` → `▲`
  - Média 2, mês atual 0, +1: `0+1=1 < 2` → `▼`
  - Média 3, mês atual 2, +1: `2+1=3 == 3` → `◆`
  - Média bruta 1,5 (arredondada para 2), mês atual 2 sem WIP: `2 == 2` → `◆` (sem o
    arredondamento seria "melhora", `2 > 1,5`)
- **Cenário de falha coberto**: sem somar o WIP ao mês corrente, a tendência pareceria estável ou em
  queda mesmo com bastante trabalho a caminho de virar entrega; sem o arredondamento para cima, um
  empate contra uma média fracionária apareceria como melhora indevida.
- **Relacionado**: decisão `0023`; ver os testes espelhados em `vazao.md`, `roadmap-epicos.md` e
  `user-story.md`.

## Regra: clique nos números abre a lista exata de itens somados, com navegação

**Garante que**: todo número clicável do painel (Urgente, Technical Story, Vazão, Roadmap–Épicos,
User Story, Eficiência) abre um modal (`#f4pItemsBg`/`#f4pItemsBody`) com a lista exata dos itens
que entraram naquele cálculo — nunca uma amostra ou aproximação — e cada item tem um botão
(`data-f4p-go`) que fecha o modal, fecha o painel F4P e navega até o item no quadro
(`#fBusca` recebe o ID).

- **Situação exibida no modal**: para quadrantes que operam sobre itens de time (Urgente, Technical
  Story, Vazão, User Story, Eficiência), a Situação usa a categoria de fluxo real do time
  (`f4pItemSituacao`/`catOf`: Backlog/Discovery/WIP/Vazão, com a data quando aplicável) — decisão
  `0019`, **não** um "Aberto"/"Fechado" genérico do Report F4P. Para Roadmap–Épicos, que opera sobre
  o quadro de Épicos, a Situação é a própria coluna do quadro de Épicos.
- **Cor do ID no modal** (decisão `0049`): o fundo do ID (`.idb`) segue a mesma categoria mostrada na
  Situação — neutro (Backlog), azul (Discovery), azul escuro (WIP) ou verde (Vazão), mesma paleta de
  `.fb` (Configurações › Fluxo dos times). Antes era sempre verde (cor de Vazão), mesmo para itens
  ainda abertos, dando a entender que tudo já tinha sido entregue. `f4pItemsModal` aceita um `catFn`
  (4º parâmetro, padrão `catOf`); Roadmap–Épicos passa `f4pEpiCatClass` (verde só quando o épico está
  na última coluna do próprio quadro de Épicos, cinza neutro nas demais — `catOf` não existe pra
  épico).
- **Cenário de falha coberto**: o modal mostraria um subconjunto diferente do número clicado (quebra
  de confiança), ou a navegação deixaria o modal/painel aberto por cima do item encontrado, ou a
  Situação mostrada não bateria com a categoria usada no resto do portal, ou o ID ficaria sempre verde
  independente do status real do item.
- **Teste dedicado à função de situação**: `test_situacao_dos_itens_usa_categoria_do_fluxo_do_time`
  confere `f4pItemSituacao(o)` para cada categoria (Backlog/Discovery/WIP/Vazão com e sem data/sem
  coluna reconhecida) contra `times.xlsx` (fluxo do CORE com coluna de Discovery).
- **Testes da cor do ID**: `test_idb_usa_a_cor_da_categoria_de_fluxo_do_item`,
  `test_idb_aceita_catFn_proprio_no_lugar_de_catOf`, `test_f4pEpiCatClass_e_verde_so_quando_o_epico_esta_fechado`,
  `test_clique_no_roadmap_epicos_colore_o_id_pela_coluna_do_proprio_quadro`.
- **Relacionado**: decisão `0016` (lista de itens do Urgente, depois generalizada), `0019` (situação
  por categoria de fluxo), `0049` (cor do ID por categoria); ver os testes
  `test_..._clique_no_numero_abre_lista_e_permite_navegar` em cada arquivo de quadrante.

## Regra: configuração de cada quadrante persiste e entra na exportação

**Garante que**: toda configuração específica de quadrante (tipos de item considerados, metas por
time, faixas min/max, tag de expedição) é gravada em `CFG.f4p`, sobrevive a `saveCfg()` e aparece no
JSON exportado por `#cfgExport` — nunca fica só em memória.

- **Cenário de falha coberto**: uma configuração de meta ou tipo feita numa sessão se perderia ao
  recarregar a página, ou não seria transferível para outra máquina via exportação/importação.
- **Relacionado**: ver os testes `test_..._configuracao_..._persiste_e_entra_na_exportacao` em cada
  arquivo de quadrante; `docs/configuracoes.md`.

## Regra: configuração antiga sem F4P usa os padrões

**Garante que**: importar uma configuração exportada antes de algum campo de F4P existir não quebra
— `normCfg({})` preenche todos os padrões (meses=6, tipos padrão, tag `urgent`, sem metas por time).

- **Teste**: `test_importar_configuracao_antiga_sem_f4p_usa_padrao`
- **Cenário de falha coberto**: importar uma configuração de uma versão anterior do portal quebraria
  o painel F4P por falta de um campo esperado.

## Regra: quadrante sem regra fechada mostra travessão e nota (mecanismo genérico)

**Garante que**: mesmo que hoje os 8 quadrantes tenham regra fechada (decisão `0031`), o código que
trata um quadrante "em definição" continua funcionando — útil se um quadrante futuro for adicionado
sem regra ainda pronta.

- **Dado**: força `F4P_QUADS.eff.done = false` num quadrante existente, só para exercitar o caminho.
- **Então (sucesso)**: o texto "Regra de cálculo ainda em definição." aparece no painel.
- **Teste**: `test_quadrante_em_definicao_mostra_travessao_e_nota`
