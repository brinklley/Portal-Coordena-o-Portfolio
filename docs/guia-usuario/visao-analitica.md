# Visão Analítica — guia do usuário

## O que é

A Visão Analítica mostra, para **um time** e **um semestre do roadmap** escolhidos nos filtros, uma
linha por épico com o volume de trabalho do time naquele épico e o quanto disso está formalmente
**reservado** no roadmap daquele semestre. É a tela para responder "como está o roadmap deste time
agora" — quantos itens, quantos estão garantidos, e em que fase cada épico está.

## Como habilitar

A aba "Visão Analítica" só fica clicável quando **dois filtros estão preenchidos ao mesmo tempo**:

1. **Time** — um time específico (não "todos").
2. **Roadmap** — interno **ou** executivo (um dos dois já basta, não precisa dos dois).

Selecionar só o Time, ou só o Roadmap, não habilita a aba — ela continua desabilitada (cinza) até os
dois estarem preenchidos juntos. Passe o mouse sobre a aba desabilitada: a dica mostrada diz
exatamente o que falta. A aba também fica desabilitada se o semestre escolhido ainda não começou (não
existe nenhum dado possível para mostrar ainda).

## Como funciona

- **QTD**: quantos itens do time, dos tipos considerados para CycleTime (configurados em
  Configurações), estão vinculados àquele épico.
- **Reservado** (número ao lado da descrição do épico): quantos desses itens têm a **tag de
  capacidade do roadmap** marcada no Azure DevOps (por padrão, a tag `ROADMAP`) — é esse subconjunto
  que conta como "garantido" para o roadmap do semestre selecionado.
- **Capacidade** e **Projetada** (números no topo, acima da tabela): a **soma**, de todos os épicos
  mostrados na tabela, do Reservado e do QTD de cada linha, respectivamente — nunca um total
  calculado à parte; se a tabela mudar (por causa de outro filtro), esses números mudam junto.
- **Status**: a fase do épico — Backlog, Discovery, WIP, Entregue ou "Sem reserva" — calculada **só
  sobre os itens reservados** do épico, não sobre todo o vínculo do time com ele. Isso evita que um
  item fora da reserva, mas mais adiantado no fluxo, faça o Status parecer mais avançado do que a
  reserva de fato está. **"Entregue" é a única fase que olha além da reserva**: se todos os itens
  reservados já foram entregues, mas o épico como um todo ainda tem outro item pendente fora da
  reserva, o Status mostra "Entregue" com um ícone de alerta (⚠) ao lado — o compromisso do roadmap
  foi cumprido, mas o épico não fechou de verdade.
- **Agrupador por categoria** (Backlog/Discovery/WIP/Vazão, numa linha própria abaixo do épico): soma
  **todos** os itens do time vinculados ao épico, com ou sem a tag de reserva — diferente do Status
  acima, que olha só a reserva.
- **Ref.** e **Dead line**: o semestre do roadmap (ex.: `2S/26`) e a data-limite calculada (fim do
  semestre, menos a folga de dias configurada, menos o CycleTime máximo do time).
- **Transparência**: clique em qualquer número — QTD, Reservado (de uma linha), ou Capacidade/Projetada
  (do topo) — para ver a lista exata dos itens que compõem aquela soma, cada um levando direto até o
  item no quadro.

## Perguntas frequentes ("não está batendo com o que eu esperava")

### "Selecionei o Time, mas o menu continua desabilitado. Por quê?"

Falta o **Roadmap**. A aba só habilita com Time **e** Roadmap (interno ou executivo) selecionados
juntos — nenhum dos dois sozinho é suficiente. Veja "Como habilitar" acima.

### "Um card está em 'Aguard. Deploy' no quadro, mas a Visão Analítica mostra Status 'Entregue'. Por quê?"

O Status não olha o **nome** da coluna onde o item está — ele olha a **categoria de fluxo** que essa
coluna recebeu em Configurações › Fluxo dos times (Nenhum, Discovery, WIP ou **Vazão**). Uma coluna
chamada "Aguard. Deploy" pode ter sido configurada com categoria **Vazão**, se, na prática daquele
time, chegar ali já significa "pronto, só falta o processo formal de deploy" — nesse caso, o item já
conta como entregue para efeito de Status, mesmo o nome da coluna sugerindo que ainda falta algo.
Confira o mapeamento de colunas do time em Configurações › Fluxo dos times para ver qual categoria
cada coluna do fluxo tem — é o mapeamento que decide, não o nome da coluna.

### "A Capacidade/Projetada no topo não bate com a conta que eu fiz manualmente olhando o quadro"

Capacidade e Projetada são sempre a **soma dos números que já aparecem nas linhas da tabela** — e a
tabela só mostra os épicos que passam pelos filtros ativos (time, roadmap, responsável). Se algum
filtro extra estiver ligado, a soma reflete só o que está visível na tela naquele momento, não o
total absoluto do time no portal inteiro.

### "Por que aparece 'Sem reserva' em um épico que tem item em andamento?"

"Reserva" exige que o item tenha, explicitamente, a **tag de capacidade do roadmap** marcada no Azure
DevOps (por padrão, `ROADMAP`). Um item pode estar ativo no fluxo (em WIP, por exemplo) sem ter essa
tag — ele continua contando no agrupador por categoria e no QTD, mas não entra na Reserva, e o Status
mostra "Sem reserva" até que algum item do épico receba a tag.

### "Por que aparece 'OBS: SEM INICIATIVA e SEM RELEASE' no lugar do nome do épico?"

É um épico sem release/iniciativa válida (por isso ele não aparece no quadro normal), mas que tem
itens do time filtrado e cujo Target Date cai no semestre do **Roadmap interno** selecionado — ele
ainda entra na Visão Analítica (e nas somas de QTD/Capacidade/Projetada), com esse aviso no lugar da
linha `[IN][id] título`. Só acontece com o Roadmap interno; no executivo esse épico não apareceria
(não há iniciativa da qual herdar um roadmap executivo).

## Cenários

### Habilitação da aba

**Cenário: Time selecionado sem Roadmap não habilita a aba**
- Dado que nenhum filtro de Roadmap (interno nem executivo) está selecionado
- Quando o usuário seleciona um Time no filtro
- Então a aba "Visão Analítica" continua desabilitada

**Cenário: Time e Roadmap juntos habilitam a aba**
- Dado que o usuário já selecionou um Time
- Quando o usuário também seleciona um Roadmap (interno ou executivo)
- Então a aba "Visão Analítica" fica habilitada e pode ser aberta

### Status "Entregue" depende do mapeamento da coluna, não do nome dela

**Cenário de sucesso: coluna mapeada como Vazão conta como entregue**
- Dado que a coluna "Aguard. Deploy" do time está configurada com categoria de fluxo **Vazão**
- E o único item reservado do épico está nessa coluna
- Quando a Visão Analítica calcula o Status do épico
- Então o Status mostra "Entregue" (ou "Entregue" com ⚠, se existir outro item pendente fora da
  reserva)

**Cenário de comportamento inesperado: mesma coluna, mapeamento diferente**
- Dado que a coluna "Aguard. Deploy" do time está configurada com categoria de fluxo **WIP** (não
  Vazão)
- E o único item reservado do épico está nessa coluna
- Quando a Visão Analítica calcula o Status do épico
- Então o Status mostra "WIP", não "Entregue" — mesmo nome de coluna do cenário acima, mas o
  mapeamento configurado é diferente, e é o mapeamento que decide

### "Entregue" com alerta quando sobra item fora da reserva

**Cenário de sucesso: tudo entregue, sem alerta**
- Dado um épico cujos itens reservados já estão todos em Vazão
- E o épico não tem nenhum outro item vinculado fora da reserva
- Quando a Visão Analítica calcula o Status
- Então o Status mostra "Entregue", sem ícone de alerta

**Cenário de comportamento inesperado: reserva cumprida, mas épico não fechou de verdade**
- Dado um épico cujos itens reservados já estão todos em Vazão
- E o épico tem outro item vinculado (sem a tag de reserva) ainda em Backlog, Discovery ou WIP
- Quando a Visão Analítica calcula o Status
- Então o Status mostra "Entregue ⚠" — o compromisso do roadmap foi cumprido, mas ainda falta algo no
  épico como um todo

## Regras de negócio relacionadas

- `docs/regras-de-negocio.md` §10 (Visão analítica) e §7 (Categorias de coluna e fase — o mapeamento
  que decide a categoria de cada coluna do fluxo).
- Decisões: [`0027`](../decisoes/0027-visao-analitica-projetada-capacidade-e-clique-para-ver-itens.md),
  [`0028`](../decisoes/0028-visao-analitica-remove-badge-us-e-clique-por-linha.md),
  [`0029`](../decisoes/0029-visao-analitica-agrupador-por-categoria-no-status.md),
  [`0036`](../decisoes/0036-visao-analitica-epico-orfao-roadmap-interno.md),
  [`0049`](../decisoes/0049-status-usa-so-itens-reservados-e-cor-do-id-por-categoria.md),
  [`0055`](../decisoes/0055-status-entregue-considera-todos-os-itens-com-alerta.md),
  [`0056`](../decisoes/0056-entregue-exige-item-de-tipo-do-ct.md).
- Detalhe exaustivo de cobertura de teste: [`docs/testes/visao-analitica.md`](../testes/visao-analitica.md).
