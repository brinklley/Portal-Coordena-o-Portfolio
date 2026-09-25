# Report F4P

**Status**: Quadrantes 1 (CycleTime) e 2 (Variabilidade) implementados — ver `docs/regras-de-negocio.md` §12 e `docs/decisoes/0011-report-f4p-quadrantes-1-e-2.md`. Os demais quadrantes abaixo continuam "em definição" (próxima tarefa: definir a regra de cada um, um de cada vez).

Tela "Report F4P" (BUSINESS OUTCOMES – PRODUCTIVITY), inspirada no slide usado pela gestão, com o mesmo comportamento da Visão analítica: **painel lateral recolhível, habilitado só quando o filtro tem um Time e um Roadmap (interno ou executivo)**. O filtro só habilita o acesso; o relatório mostra **sempre todos os times ativos na configuração** (colunas CORE, MOBILE, IB, BO… são os times).

Cabeçalho: título + semestre do filtro de roadmap (ex.: "1º semestre 2026").

## Quadrante 1 · CYCLETIME (RESERVA VS ATUAL) — especificado

Por time: `[CT Máximo] | [P95]`

- **CT Máximo**: o CT máximo cadastrado para o time (Configurações › Alertas por time). Sem valor planejado, usar o limite geral e sinalizar.
- **P95**: percentil 95 do CT dos itens dos tipos **Technical Story** e **User Story** nos **últimos 6 meses**. Período e tipos configuráveis.

## Quadrante 2 · VARIABILIDADE (MIN VS ATUAL VS MAX) — especificado

Por time: `[MIN] | [Variabilidade] | [MAX]`

- **MIN**: variabilidade mínima esperada, por time, nas configurações. Padrão **1.5**.
- **MAX**: variabilidade máxima esperada, por time. Padrão **3.5**.
- **Variabilidade** = **P95 / P50** do CT (mesma amostra do quadrante 1), com **1 casa decimal**.

## Decisões propostas (confirmar com o usuário ao implementar)

- Amostra: itens **concluídos** (com data de saída do CT) cuja saída caiu nos últimos N meses (padrão 6), de **todos** os itens do time (não filtrada pelo roadmap).
- Percentil por **interpolação linear** (igual ao `PERCENTIL.INC` do Excel).
- Indicadores: CT com P95 > máximo → ▼ vermelho; ≤ máximo → ▲ verde. Variabilidade > MAX → ▼ vermelho; dentro da faixa → ▲ verde; < MIN → ▼ laranja.
- P50 = 0 → variabilidade "--". Mostrar o tamanho da amostra (n) e o P50 como apoio.

## Configuração nova (seção "Report F4P")

- Período do P95/P50 em meses (padrão 6) e tipos (padrão User Story e Technical Story).
- Por time: variabilidade mínima (1.5) e máxima (3.5).

## Quadrantes seguintes (regras virão depois; exibir como "em definição")

Eficiência de fluxo (MIN vs ATUAL vs MAX, meta mínima 30%), Roadmap – épicos (reserva vs roadmap entregue vs atual), Vazão (reserva vs realizado), Urgente (meta vs realizado), Technical Story (meta vs realizado), User Story (planejado vs não planejado).

## Referências no código

Reaproveitar o padrão da Visão analítica: `src/js/15-visao-analitica.js` (`anEnabled`, `renderAnalytics`, `openAnalytics`, `placeAnalytics`), a aba vertical `#anTab` e o painel `#anPanel` em `src/index.html`. CT de cada item: `o.ct`, `o.ready`, `o.deploy` (calculados por `recomputeCt` conforme o fluxo do time). Limites: `limitsOf(time)`.

## Critérios de aceite

- Aba desabilitada sem Time + Roadmap; habilitada com os dois; recolhe se um deles for removido.
- Todos os times da configuração aparecem, mesmo com um time filtrado.
- P95/P50 conferidos contra um cálculo independente nos testes (fixture com CTs conhecidos).
- Configurações novas validadas (MIN < MAX) e persistidas; exportação/importação incluem os novos campos.
