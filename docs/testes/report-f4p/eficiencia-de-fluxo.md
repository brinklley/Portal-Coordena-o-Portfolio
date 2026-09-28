# Testes: Report F4P — Quadrante 8 (Eficiência de fluxo: min vs. atual vs. max)

Ver `docs/testes/report-f4p/README.md` para as regras compartilhadas. Regras de negócio: §12.9.
Decisões `0031`, `0038`.

Eficiência de Fluxo = Touch Time ÷ (Touch Time + Waiting Time) × 100, pela classificação de cada
coluna do fluxo do time (Configurações › Fluxo dos times, campo `time`: `"touch"`/`"wait"`). Estilo
**"Queueing Stages" do Actionable Agile** (ferramenta de Analytics citada pelo usuário como
referência): o usuário marca só as colunas de **Fila de espera** (waiting time); as demais contam
como touch time automaticamente — não existe um terceiro estado "sem classificação". Reaproveita
`f4pWindow` (decisão `0013`, a mesma janela do CycleTime/Variabilidade), **não**
`f4pExactSemesterWindow` como os demais quadrantes "por semestre".

## Regra: touch dividido por (touch + wait), somando os trechos entre colunas classificadas

**Garante que**: cada trecho entre a entrada em uma coluna e a entrada na próxima é classificado
(touch ou wait) pela coluna de destino; a soma de todos os trechos touch dividida pela soma de touch
+ wait dá a eficiência.

- **Dado**: fluxo Backlog→Análise→Dev→Espera→QA→Vazão; Espera marcada `wait`; item com datas
  específicas em cada coluna.
- **Então (sucesso)**: touch = Backlog→Análise (1, sem marcação = touch) + Análise→Dev (2) +
  Dev→Espera (8) + QA→Vazão (3) = 14; wait = Espera→QA (5); eficiência = 14/(14+5) ≈ 73,68%. O
  trecho Vazão→hoje **não conta**: o relógio da eficiência para na entrega (item já categorizado
  como Vazão).
- **Teste**: `test_eff_calcula_touch_dividido_por_touch_mais_wait`
- **Relacionado**: decisão `0031-report-f4p-quadrante-eficiencia-de-fluxo.md`.

## Regra: colunas sem marcação de Fila de espera contam como touch automaticamente

**Garante que**: estilo Actionable Agile — só se marca a Fila de espera; as demais colunas ficam
"touch" sem precisar de nenhuma marcação explícita (não existe mais um terceiro estado "sem
classificação").

- **Dado**: fluxo Backlog→Dev→Vazão, só "Dev" marcada `touch` explicitamente (Backlog sem marcação).
- **Então (sucesso)**: `{touch: 9, wait: 0}` — Backlog conta como touch mesmo sem marcação.
- **Teste**: `test_eff_colunas_sem_fila_de_espera_marcada_contam_como_touch`
- **Cenário de falha coberto**: uma coluna esquecida de marcar (nem touch nem wait) ficaria fora do
  cálculo inteiro, subestimando o tempo total do fluxo, em vez de contar por padrão como touch.

## Regra: todos os itens do time entram, não só os concluídos

**Garante que**: um item ainda aberto (sem chegar à Vazão) também contribui com o touch/wait já
acumulado até agora — "deve-se pegar todos os itens do fluxo de cada time", não só os já entregues.

- **Dado**: item aberto, parado em "Dev" (sem marcação de wait no fluxo).
- **Então (sucesso)**: eficiência = 100% (só touch acumulado até agora, sem nenhum wait).
- **Teste**: `test_eff_pega_todos_os_itens_nao_so_concluidos`
- **Cenário de falha coberto**: excluir itens em andamento enviesaria a métrica para cima ou para
  baixo dependendo de quais itens (só os concluídos) sobrevivessem ao filtro, escondendo gargalos em
  itens ainda abertos.

## Regra: tipos configuráveis, com todos os tipos por padrão

**Garante que**: `CFG.f4p.effTypes` filtra por tipo quando preenchido; vazio (padrão) inclui todos
os tipos, diferente dos outros quadrantes (que têm um tipo padrão específico).

- **Testes**: `test_eff_usa_tipos_configuraveis_com_todos_por_padrao`,
  `test_configuracao_eff_types_tem_padrao_vazio_todos_os_tipos`

## Regra: a duração de cada item é recortada pela janela [from, to], não excluída inteira

**Garante que**: um item cujo intervalo de coluna começa antes da janela e termina depois dela entra
com só a parte dentro de `[from, to]` — recorte, não exclusão do item inteiro.

- **Teste**: `test_eff_recorta_duracao_pela_janela_do_semestre`

## Regra: usa `f4pWindow` (janela rolante), não a janela exata do semestre

**Garante que**: diferente de Urgente/Technical Story/Vazão/Roadmap-Épicos/User Story
(`f4pExactSemesterWindow`), a Eficiência de fluxo usa `f4pWindow` — a mesma janela rolante do
CycleTime/Variabilidade.

- **Então (sucesso)**: `f4pWindow(stAtual).from === f4pWindow(stAtual).from` (mesma função que o
  CT) e diferente de `f4pExactSemesterWindow(stAtual).from`.
- **Teste**: `test_eff_janela_reaproveita_f4pwindow_nao_a_exata_do_semestre`
- **Cenário de falha coberto**: usar a janela exata do semestre (como os outros 5 quadrantes)
  perderia a continuidade "rolante" que faz sentido para uma métrica de eficiência de processo (que
  não é um contador de entregas por período).
- **Relacionado**: `docs/testes/report-f4p/README.md` (as duas janelas compartilhadas).

## Regra: sem item do time no período, mostra travessão (não zero nem erro)

**Teste**: `test_eff_sem_item_no_periodo_mostra_travessao` — `f4pEffPct` retorna `None`.

## Regra: cor verde dentro da faixa min/max, vermelha fora

**Testes**: `test_eff_cor_verde_dentro_da_faixa_e_vermelha_fora`,
`test_eff_usa_faixa_min_max_configuravel_por_time` (padrão 30–55%, `test_configuracao_eff_min_max_tem_padrao_30_55`).

## Regra: min/max ficam numa linha própria, abaixo do valor principal (correção de layout)

**Garante que**: `f4pEffCell()` devolve o valor principal seguido de um
`<span class="f4p-eff-mm">min%|max%</span>` numa linha separada — não mais lado a lado
(`min|atual|max`) na mesma linha como em Variabilidade.

- **Então (sucesso)**: a string contém `class="f4p-eff-mm"`; o valor principal
  (`data-f4p-eff-team`) vem antes dessa `<span>`; min/max (`f4p-lo`) ficam dentro dela, não soltos.
- **Teste**: `test_eff_min_max_ficam_em_linha_propria`
- **Cenário de falha coberto** (reportado pelo usuário com print): com vários times, a célula
  "min% | atual% seta | max%" não cabia na largura da coluna e quebrava/sobrepunha a coluna vizinha
  — porcentagens de duas-três casas são bem mais largas que os decimais de uma casa da Variabilidade,
  o outro quadrante com min/max. `f4pVarCell()` (Variabilidade) não foi alterado — os decimais dela
  já cabem numa linha só, mudar sem necessidade criaria inconsistência visual entre os dois
  quadrantes.
- **Relacionado**: decisão `0038-eff-min-max-linha-propria.md`. Validação visual (sem sobreposição
  com 7 times) foi feita à parte, fora da suíte automatizada — screenshot manual.

## Regra: tendência compara os últimos 2 meses contra o resto do período (não trimestres)

**Garante que**: diferente da tendência de contagem (Urgente/Vazão/etc., que compara trimestres), a
Eficiência compara a eficiência média dos últimos 2 meses contra a do período inteiro de `f4pWindow`
— um item antigo de baixa eficiência não "esconde" uma queda recente se os últimos 2 meses piorarem
sozinhos, e vice-versa.

- **Testes**: `test_eff_tendencia_ultimos_2_meses_melhor_fica_positiva`,
  `test_eff_tendencia_ultimos_2_meses_pior_fica_negativa`,
  `test_eff_tendencia_sem_diferenca_fica_neutra`

## Regra: clique no número abre a lista com Touch/Wait de cada item, navegável

**Teste**: `test_eff_clique_no_numero_abre_lista_e_permite_navegar` — o modal mostra as colunas
Touch e Wait de cada item, além do padrão compartilhado de navegação.

## Regra: o quadrante aparece calculado no painel; configuração de tipos/faixa persiste

**Testes**: `test_eff_aparece_calculado_no_painel`, `test_configuracao_eff_persiste_e_entra_na_exportacao`

## Regra: marcação de Fila de espera por coluna persiste e é lida corretamente

**Garante que**: a UI de Configurações › Fluxo dos times grava a marcação por coluna em
`CFG.flow[time].time` (`"wait"`/`"touch"`), separada da categoria (Discovery/WIP/Vazão); colunas não
marcadas ficam `"touch"` automaticamente ao ler (`flowTimeOf`).

- **Testes**: `test_configuracao_touch_wait_por_coluna_persiste`, `test_flow_time_of_le_classificacao_por_coluna`
