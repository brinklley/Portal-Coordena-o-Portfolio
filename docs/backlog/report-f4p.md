# Report F4P

**Status**: Quadrantes 1 (CycleTime) e 2 (Variabilidade) implementados — ver `docs/regras-de-negocio.md` §12 e `docs/decisoes/0011` a `0013`. **Próxima tarefa: especificar e implementar o Quadrante Urgente (meta vs. realizado)** — ver seção própria abaixo. Os demais quadrantes continuam "em definição", um de cada vez depois desse.

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

## Configuração implementada (seção "Report F4P" na tela de Configurações)

- Período do P95/P50 em meses (padrão 6) e tipos (padrão User Story e Technical Story).
- Por time: variabilidade mínima (1.5) e máxima (3.5), com validação MIN < MAX.

## Próximo quadrante a especificar: URGENTE (META VS REALIZADO)

Ainda **sem regra definida** — isto é o que falta decidir antes de implementar (mesmo processo dos quadrantes 1 e 2: propor aqui, confirmar com o usuário, então codar):

- O que conta como "urgente"? Provavelmente a tag `URGENTE` já cadastrada (`docs/regras-de-negocio.md` §9), mas confirmar — os itens de qualquer tipo, ou só dos tipos do CT (User Story/Technical Story)?
- "Meta": um número fixo configurável por time (como MIN/MAX da Variabilidade)? Vem de outra fonte (ex.: SLA de atendimento)?
- "Realizado": contagem de itens urgentes concluídos no período? Ainda abertos também contam? Mesma janela de período do CycleTime (semestre em curso = últimos N meses; encerrado = período do semestre)?
- Indicador de cor: meta é um teto (realizado > meta é ruim) ou um piso (realizado < meta é ruim)? No slide de referência aparece com losango azul (◆), não seta ▲/▼ — usar o mesmo losango, ou manter o padrão ▲/▼ dos quadrantes 1 e 2?

## Quadrantes seguintes (depois de Urgente; regras ainda em definição)

Eficiência de fluxo (MIN vs ATUAL vs MAX, meta mínima 30%), Roadmap – épicos (reserva vs roadmap entregue vs atual), Vazão (reserva vs realizado), Technical Story (meta vs realizado), User Story (planejado vs não planejado).

## Referências no código

- Painel: `src/js/23-report-f4p.js` (`f4pEnabled`, `renderF4P`, `openF4P`, `placeF4P`, `f4pSemesterState`, `f4pSample`, `f4pMetrics`), aba `#f4pTab` (dentro de `.side-tabs`) e painel `#f4pPanel` em `src/index.html`.
- Ilustrações: `src/assets/f4p/*.png`, embutidas como `F4P_ASSETS` (base64) por `scripts/build.mjs`.
- CT de cada item: `o.ct`, `o.ready`, `o.deploy` (calculados por `recomputeCt` conforme o fluxo do time, em `src/js/01-configuracao-e-regras.js`). Limites: `limitsOf(time)`; faixa de variabilidade: `f4pRangeOf(time)`.
- Testes: `tests/test_report_f4p.py`; fixture com CTs conhecidos: `tests/gerar_fixtures.py::f4p`.

## Critérios de aceite

- [x] Aba desabilitada sem Time + Roadmap, ou com um semestre futuro selecionado; habilitada com Time + Roadmap (semestre em curso ou já encerrado); recolhe se um desses deixar de valer.
- [x] Todos os times carregados aparecem, mesmo com um time diferente filtrado.
- [x] P95/P50 conferidos contra um cálculo independente nos testes (fixture com CTs conhecidos), inclusive com a amostra ancorada num semestre já encerrado.
- [x] Configurações novas validadas (MIN < MAX) e persistidas; exportação/importação incluem os novos campos.
