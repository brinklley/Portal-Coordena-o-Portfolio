# Report F4P

**Status**: Quadrantes 1 (CycleTime), 2 (Variabilidade), 3 (Urgente), 4 (Technical Story) e 5 (Vazão) implementados — ver `docs/regras-de-negocio.md` §12 e `docs/decisoes/0011` a `0022`. **Próxima tarefa: escolher e especificar o próximo quadrante** entre Eficiência de fluxo, Roadmap–Épicos ou User Story (seção "Quadrantes seguintes" abaixo) — mesmo processo dos anteriores: propor aqui, confirmar com o usuário, então codar.

Tela "Report F4P" (BUSINESS OUTCOMES – PRODUCTIVITY), inspirada no slide usado pela gestão, com o mesmo comportamento da Visão analítica: **painel lateral recolhível, habilitado só quando o filtro tem um Time e um Roadmap (interno ou executivo)**, e desabilitado se o semestre selecionado ainda não começou (não há dados possíveis). O filtro só habilita o acesso; o relatório mostra **sempre todos os times carregados no momento** (`S.model.teams` — o mesmo conjunto das colunas do quadro; ver decisão `0011`, que optou por isso em vez dos times da tela de Configurações, pois esta última exclui os times dos dados de exemplo).

Cabeçalho: título + logo F4P + semestre do filtro de roadmap (ex.: "1º semestre 2026").

## Quadrante 1 · CYCLETIME (RESERVA VS ATUAL) — implementado

Por time: `[CT Máximo] | [P95]`

- **CT Máximo**: o CT máximo cadastrado para o time (Configurações › Alertas por time). Sem valor planejado, usa o limite geral e sinaliza no texto de apoio.
- **P95**: percentil 95 do CT dos itens dos tipos configurados (padrão **Technical Story** e **User Story**) na amostra do período (ver abaixo). Período e tipos configuráveis.

## Quadrante 2 · VARIABILIDADE (MIN VS ATUAL VS MAX) — implementado

Por time: `[MIN] | [Variabilidade] | [MAX]`

- **MIN**: variabilidade mínima esperada, por time, nas configurações. Padrão **1.5**.
- **MAX**: variabilidade máxima esperada, por time. Padrão **3.5**.
- **Variabilidade** = **P95 / P50** do CT (mesma amostra do quadrante 1), com **1 casa decimal**.

## Decisões adotadas (implementadas)

- Amostra: itens **concluídos** (com data de saída do CT) dos tipos configurados, de **todos** os itens do time (não filtrada por qual épico/iniciativa está no roadmap selecionado). **O período, porém, acompanha o semestre selecionado no filtro** (decisão `0013`, revisão do que este documento propunha originalmente): semestre em curso → últimos N meses a partir de hoje (janela corrida); semestre já encerrado → só as datas de saída dentro daquele semestre; semestre futuro → painel desabilitado (não há dados possíveis).
- Percentil por **interpolação linear** (igual ao `PERCENTIL.INC` do Excel) — função `percentil` em `src/js/02-utilitarios.js`.
- Indicadores: CT com P95 > máximo → ▼ vermelho; ≤ máximo → ▲ verde. Variabilidade > MAX → ▼ vermelho; dentro da faixa → ▲ verde; < MIN → ▼ laranja.
- P50 = 0 (ou amostra vazia) → variabilidade "--". O tamanho da amostra (n) e o P50 ficam no texto de apoio (`title`) da célula, não sempre visíveis.
- Ilustrações: as imagens reais do slide de referência (fornecidas pelo usuário), embutidas em base64 no build — não os SVGs originais cogitados inicialmente (decisão `0012`).

## Quadrante 3 · URGENTE (META VS REALIZADO) — implementado

Gestão da Classe de Serviço **Expedite**. Decisões e a limitação de dados por trás delas: `docs/decisoes/0014-report-f4p-quadrante-urgente.md`. Regra completa: `docs/regras-de-negocio.md` §12.4.

Por time: `[Meta] | [Realizado] [Tendência]`

- **Tag Expedite**: configurável (Configurações › Report F4P), qualquer tag já cadastrada; padrão a tag "URGENTE". Conta itens de **qualquer tipo** (não usa os tipos do CT).
- **Meta**: teto de itens Expedite no semestre, configurável por time; sem meta cadastrada, mostra "--" e não colore o Realizado.
- **Realizado**: abertos contam sempre (não importa há quanto tempo); fechados só contam se fecharam dentro de uma janela **própria do Urgente** (`f4pUrgentWindow`), diferente da janela geral de CycleTime/Variabilidade (`f4pWindow`, §12.1) — sempre o **período exato do semestre selecionado**, em curso ou já encerrado, nunca uma janela corrida de N meses. Corrigido pela decisão `0015` depois de um bug em produção (a versão original não tinha corte de data no semestre em curso, somando todo item já tageado alguma vez na história do time) — e de uma correção intermediária errada (usar o início do semestre em vez da janela rolante já estabelecida) — e ajustado de novo pela decisão `0017` depois que a janela corrida de N meses do semestre em curso se mostrou "vazando" itens fechados ainda no semestre anterior.
- **Tendência** (▲/▼/◆): itens fechados nos últimos 3 meses vs. nos 3 meses anteriores, sempre a partir de hoje — independente do semestre selecionado no filtro. Sem margem de tolerância; cor neutra.
- Indicador de cor do Realizado: acima da meta → vermelho; na meta ou abaixo → verde.
- **Transparência** (decisão `0016`): o número do Realizado é clicável e abre a lista dos itens exatos contados (ID, título, Situação), cada um levando direto até o item no quadro. Situação mostra a categoria de fluxo do time (Backlog/Discovery/WIP/Vazão), não um "Aberto"/"Fechado" próprio do quadrante (decisão `0019`).

## Quadrante 4 · TECHNICAL STORY (META VS REALIZADO) — implementado

Mesmo comportamento do Quadrante 3 (Urgente), com diferenças de negócio. Decisões: `docs/decisoes/0018-report-f4p-quadrante-technical-story.md` e `docs/decisoes/0020-report-f4p-technical-story-so-itens-entregues.md`. Regra completa: `docs/regras-de-negocio.md` §12.5.

Por time: `[Meta] | [Realizado]`

- **O que conta**: itens do **tipo Technical Story** — tipo fixo (não configurável, ao contrário dos tipos de CycleTime/Variabilidade), em vez de uma tag.
- **Meta**: teto de itens Technical Story no semestre, configurável por time; **padrão 6** quando o time não cadastra a própria (diferente do Urgente, que fica sem meta).
- **Realizado**: usa a mesma janela do Urgente (`f4pExactSemesterWindow`, decisões `0017`/`0018`), mas **diferente do Urgente** só conta itens já **entregues** — categoria de fluxo Vazão (`catOf`, decisão `0019`) — com `o.deploy` dentro do período; itens em Backlog, Discovery ou WIP não contam, mesmo abertos há muito tempo (decisão `0020`).
- Indicador de cor do Realizado: acima da meta → vermelho; na meta ou abaixo → verde. Sempre colorido (a meta nunca fica "sem valor").
- Sem seta de tendência (o usuário não pediu uma para este quadrante).
- **Transparência**: o número do Realizado é clicável e abre a lista dos itens exatos contados, igual ao Urgente — mesma Situação por categoria de fluxo.

## Quadrante 5 · VAZÃO (RESERVA VS REALIZADO) — implementado

Gestão da entrega do time no período do roadmap selecionado. Decisões: `docs/decisoes/0022-report-f4p-quadrante-vazao.md` e `docs/decisoes/0023-report-f4p-vazao-tendencia-com-wip.md` (tendência somando itens em WIP). Regra completa: `docs/regras-de-negocio.md` §12.6.

Por time: `[Reserva] | [Realizado] [Tendência]`

- **Filtro**: itens dos tipos configurados para o CT (`CFG.f4p.types` — o mesmo campo de CycleTime/Variabilidade, não uma configuração própria; padrão User Story e Technical Story), já **entregues** (categoria de fluxo Vazão, igual ao Technical Story), com `o.deploy` dentro do período exato do semestre selecionado (`f4pExactSemesterWindow`, o mesmo do Urgente/Technical Story).
- **Realizado**: todos os itens do conjunto acima.
- **Reserva**: subconjunto do Realizado com a **tag de capacidade do roadmap** (`CFG.anTag`, padrão "ROADMAP" — a mesma configuração já usada pela Visão analítica, §10). Nunca maior que o Realizado, por ser um filtro sobre o mesmo conjunto.
- **Sem cor de alerta**: não há meta/teto para este quadrante — Reserva é informativa, não um limite.
- **Tendência** (▲/▼/◆): separa o Realizado por mês corrido dentro do período (só os meses já decorridos, no semestre em curso) e compara o **mês corrente + itens hoje em WIP** contra a **média** (arredondada pra cima) dos meses anteriores do mesmo período (decisão `0023`). Sem meses anteriores para comparar, fica ◆.
- **Transparência**: tanto a Reserva quanto o Realizado são clicáveis e abrem a lista dos itens exatos de cada contagem.

## Decisões adotadas (implementadas)

- Amostra CycleTime/Variabilidade: itens **concluídos** (com data de saída do CT) dos tipos configurados, de **todos** os itens do time (não filtrada por qual épico/iniciativa está no roadmap selecionado). **O período, porém, acompanha o semestre selecionado no filtro** (decisão `0013`, revisão do que este documento propunha originalmente): semestre em curso → últimos N meses a partir de hoje (janela corrida); semestre já encerrado → só as datas de saída dentro daquele semestre; semestre futuro → painel desabilitado (não há dados possíveis).
- Percentil por **interpolação linear** (igual ao `PERCENTIL.INC` do Excel) — função `percentil` em `src/js/02-utilitarios.js`.
- Indicadores: CT com P95 > máximo → ▼ vermelho; ≤ máximo → ▲ verde. Variabilidade > MAX → ▼ vermelho; dentro da faixa → ▲ verde; < MIN → ▼ laranja.
- P50 = 0 (ou amostra vazia) → variabilidade "--". O tamanho da amostra (n) e o P50 ficam no texto de apoio (`title`) da célula, não sempre visíveis.
- Ilustrações: as imagens reais do slide de referência (fornecidas pelo usuário), embutidas em base64 no build — não os SVGs originais cogitados inicialmente (decisão `0012`).
- Urgente: definição por tag configurável (não fixa em "URGENTE"), realizado sempre limitado ao período exato do semestre selecionado (abertos sempre contam; fechados só dentro do período), tendência por trimestres e cores conforme decisões `0014`, `0015` e `0017`.
- Technical Story: mesmo comportamento do Urgente, contando pelo tipo do item em vez de uma tag e com meta padrão 6 (não fica "sem meta"); sem tendência. A janela por período exato do semestre foi generalizada de `f4pUrgentWindow` para `f4pExactSemesterWindow`, reaproveitada pelos dois quadrantes (decisão `0018`). Depois de ver o quadrante em produção, o Realizado passou a contar só itens já entregues (categoria de fluxo Vazão) — itens em Backlog, Discovery ou WIP não contam mais, mesmo abertos há muito tempo (decisão `0020`, única divergência real do comportamento do Urgente).
- Situação na lista de itens (Urgente e Technical Story): categoria de fluxo do time (Backlog/Discovery/WIP/Vazão, com a data de saída na Vazão), pela mesma `catOf` usada no resto do portal, em vez de um "Aberto"/"Fechado" próprio do Report F4P (decisão `0019`).
- Vazão: mesmo critério de "entregue" do Technical Story (categoria de fluxo Vazão), mas com os tipos configurados para o CT (`CFG.f4p.types`) em vez de um tipo fixo; Reserva/Realizado por tag de capacidade (`CFG.anTag`, reaproveitada da Visão analítica) em vez de meta vs. realizado; sem cor de alerta; Reserva e Realizado clicáveis (decisão `0022`). Tendência ajustada depois de ver o quadrante em produção: mês corrente somado aos itens hoje em WIP (trabalho a caminho de virar Vazão) contra a média dos meses anteriores, arredondada sempre pra cima (decisão `0023`).

## Configuração implementada (seção "Report F4P" na tela de Configurações)

- Período do P95/P50 em meses (padrão 6) e tipos (padrão User Story e Technical Story) — valem para CycleTime, Variabilidade e Vazão.
- Tag da Classe de Serviço Expedite (padrão "URGENTE") — usada pelo quadrante Urgente.
- Tag de capacidade do roadmap (`CFG.anTag`, seção Visão analítica, padrão "ROADMAP") — reaproveitada pela Reserva do quadrante Vazão.
- Por time: variabilidade mínima (1.5) e máxima (3.5), com validação MIN < MAX; meta de Urgente (inteiro ≥ 0, opcional, independente da variabilidade); e meta de Technical Story (inteiro ≥ 0, opcional, padrão efetivo 6).

## Quadrantes seguintes (regras ainda em definição)

Eficiência de fluxo (MIN vs ATUAL vs MAX, meta mínima 30%), Roadmap – épicos (reserva vs roadmap entregue vs atual), User Story (planejado vs não planejado).

## Referências no código

- Painel: `src/js/23-report-f4p.js` (`f4pEnabled`, `renderF4P`, `openF4P`, `placeF4P`, `f4pSemesterState`, `f4pSample`, `f4pMetrics`, `f4pExpediteOps`, `f4pTsOps`, `f4pVazaoOps`, `f4pVazaoWipCount`, `f4pExactSemesterWindow`, `f4pUrgentRealizado`, `f4pUrgentTrend`, `f4pUrgentCell`, `f4pTsRealizado`, `f4pTsCell`, `f4pVazaoReservaItems`, `f4pVazaoRealizadoItems`, `f4pVazaoTrend`, `f4pVazaoCell`, `f4pItemSituacao`), aba `#f4pTab` (dentro de `.side-tabs`) e painel `#f4pPanel` em `src/index.html`.
- Categoria de fluxo na lista de itens (Situação) e no filtro do Vazão: `catOf(o)` em `src/js/01-configuracao-e-regras.js` — a mesma função usada no restante do portal (itens por categoria do épico, alertas de "parado na coluna").
- Ilustrações: `src/assets/f4p/*.png`, embutidas como `F4P_ASSETS` (base64) por `scripts/build.mjs`.
- CT de cada item: `o.ct`, `o.ready`, `o.deploy` (calculados por `recomputeCt` conforme o fluxo do time, em `src/js/01-configuracao-e-regras.js`). Limites: `limitsOf(time)`; faixa de variabilidade: `f4pRangeOf(time)`; meta de Urgente: `f4pUrgentMetaOf(time)`; tag Expedite: `f4pExpediteTag()`; meta de Technical Story: `f4pTsMetaOf(time)`; tag de capacidade (Vazão): `CFG.anTag`.
- Testes: `tests/test_report_f4p.py`; fixture com CTs conhecidos: `tests/gerar_fixtures.py::f4p`.

## Critérios de aceite

- [x] Aba desabilitada sem Time + Roadmap, ou com um semestre futuro selecionado; habilitada com Time + Roadmap (semestre em curso ou já encerrado); recolhe se um desses deixar de valer.
- [x] Todos os times carregados aparecem, mesmo com um time diferente filtrado.
- [x] P95/P50 conferidos contra um cálculo independente nos testes (fixture com CTs conhecidos), inclusive com a amostra ancorada num semestre já encerrado.
- [x] Configurações novas validadas (MIN < MAX; meta de Urgente independente) e persistidas; exportação/importação incluem os novos campos.
- [x] Urgente conta só itens com a tag configurada, de qualquer tipo; realizado ao vivo no semestre em curso e por fechamento no semestre encerrado; tendência por trimestres testada com casos de alta, queda e estabilidade.
- [x] Technical Story conta só itens desse tipo; realizado com a mesma janela por período exato do semestre do Urgente; meta com padrão 6 testada com e sem valor próprio por time; clique no número abre a lista e navega até o item.
- [x] Technical Story ignora itens em Backlog, Discovery ou WIP no Realizado, mesmo abertos há muito tempo; conta só itens na categoria de fluxo Vazão com data de saída dentro do período (decisão `0020`), testado com item em cada categoria.
- [x] Situação na lista de itens (Urgente e Technical Story) mostra a categoria de fluxo do time (Backlog, Discovery, WIP ou Vazão com a data), testada com item em cada categoria.
- [x] Vazão conta só itens dos tipos configurados já entregues (Vazão) no período; Reserva é subconjunto do Realizado pela tag de capacidade, configurável; clique na Reserva e no Realizado abre a lista e navega até o item.
- [x] Tendência do Vazão soma os itens hoje em WIP ao mês corrente e compara com a média (arredondada pra cima) dos meses anteriores; testada com os três exemplos exatos dados pelo usuário (melhora, piora, estável) e com o efeito do arredondamento.
