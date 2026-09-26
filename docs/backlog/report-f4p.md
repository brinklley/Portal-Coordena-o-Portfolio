# Report F4P

**Status**: Quadrantes 1 (CycleTime), 2 (Variabilidade) e 3 (Urgente) implementados — ver `docs/regras-de-negocio.md` §12 e `docs/decisoes/0011` a `0014`. **Próxima tarefa: escolher e especificar o próximo quadrante** entre Eficiência de fluxo, Roadmap–Épicos, Vazão, Technical Story ou User Story (seção "Quadrantes seguintes" abaixo) — mesmo processo dos anteriores: propor aqui, confirmar com o usuário, então codar.

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
- **Realizado**: abertos contam sempre (não importa há quanto tempo); fechados só contam se fecharam dentro da **mesma janela por semestre usada por CycleTime/Variabilidade** (`f4pWindow`, §12.1 — últimos N meses no semestre em curso, período exato no encerrado). Corrigido pela decisão `0015` depois de um bug em produção (a versão original não tinha corte de data no semestre em curso, somando todo item já tageado alguma vez na história do time) — e de uma correção intermediária errada (usar o início do semestre em vez da janela rolante já estabelecida).
- **Tendência** (▲/▼/◆): itens fechados nos últimos 3 meses vs. nos 3 meses anteriores, sempre a partir de hoje — independente do semestre selecionado no filtro. Sem margem de tolerância; cor neutra.
- Indicador de cor do Realizado: acima da meta → vermelho; na meta ou abaixo → verde.
- **Transparência** (decisão `0016`): o número do Realizado é clicável e abre a lista dos itens exatos contados (ID, título, aberto/fechado), cada um levando direto até o item no quadro.

## Decisões adotadas (implementadas)

- Amostra CycleTime/Variabilidade: itens **concluídos** (com data de saída do CT) dos tipos configurados, de **todos** os itens do time (não filtrada por qual épico/iniciativa está no roadmap selecionado). **O período, porém, acompanha o semestre selecionado no filtro** (decisão `0013`, revisão do que este documento propunha originalmente): semestre em curso → últimos N meses a partir de hoje (janela corrida); semestre já encerrado → só as datas de saída dentro daquele semestre; semestre futuro → painel desabilitado (não há dados possíveis).
- Percentil por **interpolação linear** (igual ao `PERCENTIL.INC` do Excel) — função `percentil` em `src/js/02-utilitarios.js`.
- Indicadores: CT com P95 > máximo → ▼ vermelho; ≤ máximo → ▲ verde. Variabilidade > MAX → ▼ vermelho; dentro da faixa → ▲ verde; < MIN → ▼ laranja.
- P50 = 0 (ou amostra vazia) → variabilidade "--". O tamanho da amostra (n) e o P50 ficam no texto de apoio (`title`) da célula, não sempre visíveis.
- Ilustrações: as imagens reais do slide de referência (fornecidas pelo usuário), embutidas em base64 no build — não os SVGs originais cogitados inicialmente (decisão `0012`).
- Urgente: definição por tag configurável (não fixa em "URGENTE"), realizado sempre limitado ao semestre selecionado (abertos sempre contam; fechados só dentro do período), tendência por trimestres e cores conforme decisões `0014` e `0015`.

## Configuração implementada (seção "Report F4P" na tela de Configurações)

- Período do P95/P50 em meses (padrão 6) e tipos (padrão User Story e Technical Story) — valem só para CycleTime/Variabilidade.
- Tag da Classe de Serviço Expedite (padrão "URGENTE") — usada pelo quadrante Urgente.
- Por time: variabilidade mínima (1.5) e máxima (3.5), com validação MIN < MAX; e meta de Urgente (inteiro ≥ 0, opcional, independente da variabilidade).

## Quadrantes seguintes (regras ainda em definição)

Eficiência de fluxo (MIN vs ATUAL vs MAX, meta mínima 30%), Roadmap – épicos (reserva vs roadmap entregue vs atual), Vazão (reserva vs realizado), Technical Story (meta vs realizado), User Story (planejado vs não planejado).

## Referências no código

- Painel: `src/js/23-report-f4p.js` (`f4pEnabled`, `renderF4P`, `openF4P`, `placeF4P`, `f4pSemesterState`, `f4pSample`, `f4pMetrics`, `f4pExpediteOps`, `f4pUrgentRealizado`, `f4pUrgentTrend`, `f4pUrgentCell`), aba `#f4pTab` (dentro de `.side-tabs`) e painel `#f4pPanel` em `src/index.html`.
- Ilustrações: `src/assets/f4p/*.png`, embutidas como `F4P_ASSETS` (base64) por `scripts/build.mjs`.
- CT de cada item: `o.ct`, `o.ready`, `o.deploy` (calculados por `recomputeCt` conforme o fluxo do time, em `src/js/01-configuracao-e-regras.js`). Limites: `limitsOf(time)`; faixa de variabilidade: `f4pRangeOf(time)`; meta de Urgente: `f4pUrgentMetaOf(time)`; tag Expedite: `f4pExpediteTag()`.
- Testes: `tests/test_report_f4p.py`; fixture com CTs conhecidos: `tests/gerar_fixtures.py::f4p`.

## Critérios de aceite

- [x] Aba desabilitada sem Time + Roadmap, ou com um semestre futuro selecionado; habilitada com Time + Roadmap (semestre em curso ou já encerrado); recolhe se um desses deixar de valer.
- [x] Todos os times carregados aparecem, mesmo com um time diferente filtrado.
- [x] P95/P50 conferidos contra um cálculo independente nos testes (fixture com CTs conhecidos), inclusive com a amostra ancorada num semestre já encerrado.
- [x] Configurações novas validadas (MIN < MAX; meta de Urgente independente) e persistidas; exportação/importação incluem os novos campos.
- [x] Urgente conta só itens com a tag configurada, de qualquer tipo; realizado ao vivo no semestre em curso e por fechamento no semestre encerrado; tendência por trimestres testada com casos de alta, queda e estabilidade.
