# Testes: Report F4P — Quadrante 3 (Urgente: meta vs. realizado)

Ver `docs/testes/report-f4p/README.md` para as regras compartilhadas. Regras de negócio: §12.4.
Decisões `0014`–`0017`.

## Regra: Realizado conta só itens com a tag de expedição configurada

**Garante que**: o número "Realizado" conta só itens que têm a tag configurável de expedição
(`CFG.f4p.expediteTag`, padrão `urgent`) em `tagHits` — nenhum outro critério.

- **Dado**: 3 itens de um time: um com `tagHits:[{id:'urgent'}]`, um sem nenhuma tag, um com uma tag
  diferente (`paused`).
- **Então (sucesso)**: `f4pUrgentRealizado(team) === 1`.
- **Cenário de falha coberto**: itens com outras tags de prioridade (ex.: `paused`) contariam como
  urgentes, inflando o número sem relação com a tag que o time realmente usa para expedição.
- **Teste**: `test_urgente_conta_so_itens_com_a_tag_configurada`
- **Relacionado**: decisão `0014`.

## Regra: no semestre em curso, conta abertos (sempre) e fechados dentro do período exato do semestre

**Garante que**: um item com a tag urgente e ainda aberto conta sempre; um item fechado só conta se
o fechamento caiu dentro do período exato do semestre selecionado (`f4pExactSemesterWindow`, não a
janela rolante de N meses).

- **Então (sucesso)**: com um item aberto e um fechado dentro do semestre em curso,
  `f4pUrgentRealizado(team, f4pSemesterState()) === 2`.
- **Teste**: `test_urgente_semestre_atual_conta_abertos_e_fechados`

## Regra: itens fechados antes do início do semestre em curso não contam (regressão do usuário)

**Garante que**: um item fechado um dia antes do início do semestre em curso não entra no Realizado,
mesmo estando dentro da janela rolante de N meses que CycleTime/Variabilidade usam — a janela do
Urgente é o período exato do semestre, nunca a rolante.

- **Dado**: um item fechado na véspera do início do semestre (não conta), um fechado 5 dias depois
  do início (conta), um ainda aberto (conta, independente de quando a tag foi aplicada).
- **Então (sucesso)**: `f4pUrgentRealizado(team, ...) === 2`.
- **Cenário de falha coberto** (regressão real relatada pelo usuário): a contagem estava somando
  todo item que já teve a tag em qualquer momento da história do time (ex.: 249 itens num time que
  usa a tag raramente) — a janela errada (rolante em vez de exata) inflava o número de forma
  dramática.
- **Teste**: `test_urgente_semestre_atual_ignora_fechados_antes_do_inicio_do_semestre`
- **Relacionado**: decisão `0017-report-f4p-urgente-periodo-exato-do-semestre.md` — a correção mais
  citada como referência pelos outros quadrantes "por semestre" (ver README).

## Regra: semestre já encerrado conta só fechados dentro daquele período

**Garante que**: sem histórico de quando a tag foi aplicada, um semestre encerrado só pode contar o
que fechou (`o.deploy` preenchido) dentro daquele período — itens ainda abertos, ou fechados fora do
período, ficam de fora.

- **Dado**: um item fechado dentro do semestre anterior (conta), um ainda aberto (não conta), um
  fechado no semestre atual (não conta, é de outro período).
- **Então (sucesso)**: `f4pUrgentRealizado(team) === 1` com `S.f.int` = semestre anterior.
- **Teste**: `test_urgente_semestre_passado_conta_so_fechados_no_periodo`
- **Relacionado**: decisão `0017`.

## Regra: tendência compara os últimos 3 meses contra os 3 meses anteriores

**Garante que**: `f4pUrgentTrend(team)` retorna `▲`/`▼`/`◆` conforme a contagem dos últimos 3 meses
for maior, menor ou igual à dos 3 meses anteriores a esses.

- **Então (sucesso)**: 2 recentes vs. 1 antigo → `▲`; 1 recente vs. 2 antigos → `▼`; 1 recente vs. 1
  antigo → `◆`.
- **Teste**: `test_urgente_tendencia_compara_trimestres`
- **Relacionado**: `docs/testes/report-f4p/README.md` (convenção ▲▼◆ compartilhada).

## Regra: meta por time colore a célula (verde dentro, vermelho acima, neutro sem meta)

**Garante que**: `f4pUrgentCell(team)` usa `CFG.f4p.teams[time].urgentMeta` para colorir: Realizado
≤ meta → verde (`f4p-good`); Realizado > meta → vermelho (`f4p-bad`); sem meta cadastrada → nenhuma
cor (nem boa nem ruim).

- **Dado**: 3 itens urgentes ao vivo; meta 5 (dentro), depois meta 2 (acima), depois sem meta.
- **Então (sucesso)**: dentro da meta → `f4p-good` sem `f4p-bad`; acima → `f4p-bad`; sem meta →
  nem `f4p-good` nem `f4p-bad`.
- **Cenário de falha coberto**: um time sem meta cadastrada apareceria com uma cor (boa ou ruim) sem
  ter nenhuma meta real para comparar, dando um sinal falso de desempenho.
- **Teste**: `test_urgente_meta_colore_vermelho_verde_ou_neutro`
- **Teste complementar**: `test_urgente_meta_zero_e_valida` — meta explicitamente `0` é um valor
  válido e distinto de "sem meta" (não confundida com `undefined`/`null`).

## Regra: clique no número abre a lista de itens urgentes e permite navegar

**Garante que**: segue o padrão compartilhado de clique-para-ver-itens (ver README): mostra os itens
exatos contabilizados, com a Situação pela categoria de fluxo real (decisão `0019`), e cada item leva
até ele no quadro ao clicar.

- **Teste**: `test_urgente_clique_no_numero_abre_lista_e_permite_navegar`

## Regra: o quadrante aparece calculado no painel; configuração de tag e meta persiste

**Garante que**: o texto "Urgente (meta vs realizado)" e a classe de tamanho `f4p-lo` aparecem no
painel; a tag de expedição (`CFG.f4p.expediteTag`) e a meta por time (`urgentMeta`) sobrevivem a
`saveCfg()` e aparecem na exportação.

- **Testes**: `test_urgente_aparece_calculado_no_painel`,
  `test_urgente_configuracao_tag_e_meta_persistem_e_entram_na_exportacao`
