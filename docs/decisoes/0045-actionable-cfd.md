# 0045 — Actionable ganha o quarto quadrante: CFD (Cumulative Flow Diagram)

## Contexto

O usuário pediu o último quadrante do Actionable: um CFD clássico. O pedido original: "eixo Y por
semana", começando na primeira semana do semestre selecionado e terminando no último dia do semestre;
empilhamento por Nenhum (Backlog), Discovery, WIP e Vazão; configurável se conta itens do tipo bug
(padrão: conta); tooltip ao passar o mouse com os valores da semana. Pediu explicitamente para eu
perguntar em caso de dúvida.

Quatro pontos genuinamente ambíguos foram fechados com o usuário via `AskUserQuestion` antes de
implementar (todas as opções recomendadas foram escolhidas):

1. **Orientação do gráfico**: "eixo Y por semana" bateria literalmente com o layout "deitado" do
   quadrante Distribuição Vazão por mês (linhas = semanas). Mas um CFD é universalmente reconhecido
   como um gráfico de área empilhada com o tempo fluindo da esquerda pra direita (eixo X) e a contagem
   acumulada no eixo Y — inclusive nas ferramentas como ActionableAgile já citadas neste projeto (ver
   decisão do quadrante Eficiência de Fluxo do Report F4P, §12.9). Confirmado o formato clássico: X =
   semanas, Y = contagem acumulada.
2. **Definição de "semana"**: blocos fixos de 7 dias a partir do 1º dia do semestre (1/jan ou 1/jul),
   terminando exatamente no último dia do semestre (a última semana pode ter menos de 7 dias) — em vez
   de semanas de calendário reais (segunda a domingo), que fariam a primeira/última semana do gráfico
   incluir dias fora do semestre selecionado.
3. **Ordem de empilhamento**: Vazão na base (crescendo pra cima), Nenhum no topo — estilo
   ActionableAgile, a mesma ferramenta de referência já citada no Report F4P — em vez da ordem inversa.
4. **Toggle de bugs**: reaproveitar a lista `CFG.act.bugTypes` já existente (decisão `0044`, quadrante
   Distribuição Vazão por mês) com um novo booleano `CFG.act.cfdIncludeBugs` (padrão `true`), em vez de
   uma lista de tipos independente para este quadrante.

## Como o CFD foi reconstruído com os dados já existentes

Diferente dos demais quadrantes calculados do portal (que sempre leem o estado **atual** de cada item),
um CFD precisa saber em qual categoria de fluxo cada item estava em **cada semana passada** — uma
reconstrução histórica. Investigando o modelo (`buildModel`, `src/js/04-modelo.js`), cada item já guarda
`o.fd`: um mapa `nome da coluna → data de entrada`, preenchido para toda coluna do fluxo do time que o
item já passou. A regra de como essas datas são calculadas (decisão `0006`, `docs/integracao-azure.md`
§ "Datas das colunas: regra validada") garante duas propriedades cruciais para o CFD funcionar sem gaps:

- **A primeira coluna recebe a data de criação do item** — todo item tem pelo menos uma data registrada
  desde que existe, mesmo que nunca tenha saído do Backlog.
- **Colunas puladas herdam a data da próxima coluna em que o item entrou** — não há "buracos" no meio
  do caminho percorrido por um item; a cada coluna alcançada, todas as anteriores já têm data.

Com isso, a categoria de um item numa data T é calculável sem nenhum dado novo: a categoria da coluna
mais avançada (maior índice na ordem do fluxo do time) cuja data de entrada é `<= T`
(`actCfdCategoriaEm`). Isso é lido diretamente do modelo já carregado — não é um cálculo aproximado nem
uma nova integração com o Azure DevOps.

## Implementação

`src/js/24-actionable.js`:

- `actCfdWeeks(st)`: gera os blocos de 7 dias do semestre selecionado (`f4pExactSemesterWindow`), do 1º
  dia até o último (a última semana pode ser mais curta).
- `actCfdOps(team)`: itens do time, com ou sem os tipos de `CFG.act.bugTypes` conforme
  `CFG.act.cfdIncludeBugs`.
- `actCfdCategoriaEm(o, T, c)`: a categoria do item `o` na data `T`, usando `o.fd` e a ordem/categorias
  do fluxo do time (`teamCfg(team)`) — `null` se o item ainda não existia em `T`.
- `actCfdData(team, st)`: para cada semana, conta quantos itens já chegaram a cada categoria (ou além) —
  `nenhum`/`disc`/`wip`/`vazao` são contagens cumulativas "chegou a esta categoria ou além"; `bandNenhum`/
  `bandDisc`/`bandWip`/`bandVazao` são as diferenças entre elas (o que aparece de fato em cada faixa do
  gráfico).
- `actCfdSvg(data)`: gráfico de área empilhada em SVG — 4 `<path>` (um por faixa), eixo Y com
  min/max, eixo X com a primeira/última data. A transparência por hover usa retângulos invisíveis (um
  por semana) com um `<title>` nativo do SVG — mesmo mecanismo já usado pelos pontos do quadrante
  CycleTime (`actScatterSvg`), sem precisar de um tooltip customizado em JS.
- `actCfdCard(data)`: legenda + gráfico.

`src/js/01-configuracao-e-regras.js`: `CFG.act.cfdIncludeBugs` (booleano, padrão `true`), normalizado
com o mesmo padrão de outros booleanos opt-out do portal (`azure.excludeRemoved`).

`src/js/19-tela-configuracoes.js`: novo checkbox na seção "Actionable" já criada pela decisão `0044`.

## Um bug pego durante a implementação: colisão de classe CSS

O wrapper HTML do card e o `<svg>` do gráfico originalmente compartilhavam a classe `act-cfd` (seguindo,
por engano, o padrão `act-chart act-cfd` do SVG mas reaproveitando o mesmo nome pro contêiner externo).
Como a regra CSS `.act-cfd{display:flex;...}` batia nos dois elementos, o SVG também recebia
`display:flex`, o que quebrava seu layout. Corrigido renomeando o wrapper para `act-cfd-wrap` — pego
durante a validação visual (screenshot num Chromium headless), antes de qualquer teste automatizado
rodar, e adicionado como uma checagem a mais para os próximos gráficos SVG deste painel.

## Por que os meses/semanas futuras "funcionam sozinhas"

Ao contrário da Distribuição Vazão por mês (decisão `0044`), que precisou de uma regra explícita para
tratar meses futuros como "sem registro" (barra cinza), o CFD não precisou de nenhuma lógica especial:
como nenhuma data em `o.fd` é maior que hoje, `actCfdCategoriaEm` para uma semana futura devolve
exatamente a mesma categoria que devolveria para hoje — as faixas simplesmente ficam **achatadas** da
semana atual até o fim do semestre, sem nenhum item "aparecendo do nada". É uma consequência natural do
algoritmo de reconstrução, não uma regra adicional.

## Testes

`tests/test_actionable.py`: nova seção cobrindo — geração das semanas em blocos de 7 dias cobrindo o
semestre inteiro; reconstrução da categoria de um item numa data (`actCfdCategoriaEm`, incluindo colunas
puladas); as 4 faixas somando exatamente o total de itens já criados; o total (`nenhum`) nunca diminui
ao longo das semanas; toggle de bugs (padrão conta, desligável); aparição no painel com a legenda de 4
cores; conteúdo do tooltip (`<title>`) ao passar o mouse; checkbox de configuração com padrão marcado e
persistência ao salvar/exportar. O teste `test_quadrante_4_mostra_em_definicao` foi renomeado para
`test_os_4_quadrantes_tem_regra_definida` (não sobra mais nenhum "em definição").
