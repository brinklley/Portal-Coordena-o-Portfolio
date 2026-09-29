# Regras de negócio

Este é o documento de referência das regras do Mapa do Portfólio. Quando uma regra mudar, atualize este arquivo **e** o teste correspondente em `tests/`, e registre o motivo em `docs/decisoes/`.

Código principal: `src/js/01-configuracao-e-regras.js`, `src/js/04-modelo.js`, `src/js/05-estado-e-calculos.js`.

---

## 1. Hierarquia e vínculos

```
Iniciativa  ←(Parent)─  Release  ←(Parent)─  Épico  ←(vínculo)─  Item de time
```

| Nível | Aba (formato interno) | Vínculo com o nível acima |
|---|---|---|
| Iniciativa | `Iniciativa` / `INICIATIVA` | — |
| Release | `Release` / `RELEASE` | coluna `Parent` = ID da iniciativa |
| Épico | `Épico` / `EPICO` | coluna `Parent` = ID da release |
| Item de time | uma aba por time | ver 1.1 |

### 1.1 Vínculo do item de time com o épico

Ordem de prioridade (primeira que existir vale):

1. **Campo `ID_EPICO_UNICRED`** (organização vsunicred e planilhas).
2. **`Parent`**, somente quando o Parent é um épico carregado (times na mesma organização do épico, como os do projeto TI na unicredbr, onde o campo não existe).
3. **Link Remote Related** (vínculo entre organizações).

Quando o campo e o Remote Related apontam para épicos diferentes, vale o campo e o item é listado na Higiene de dados como "vínculo divergente".

### 1.2 Abas de time

Internamente, cada fonte de dados do Azure vira uma "aba" (mesmo formato de tabela usado por `buildModel`); uma aba é de time se o nome começa com `TIME ` (o time é o restante do nome) **ou** se ela tem a coluna `ID_EPICO_UNICRED` (o time é o nome da aba) — mas na prática o nome do time vem do "nome no portal" (alias) definido na fonte, na tela Configurações › Azure DevOps.

## 2. Validade (o item existe no portal?)

| Nível | Regra |
|---|---|
| Iniciativa | Sempre existe. |
| Release | Existe se o `Parent` é uma iniciativa carregada. Senão vai para a Higiene ("Releases sem iniciativa"). |
| Épico | Existe se tem título e o `Parent` é uma release carregada. Senão vai para a Higiene ("Épicos inválidos"). |
| Item de time | Se o épico do vínculo não existe, é "órfão" (Higiene). |

## 3. Visibilidade no quadro (regra B)

Decisão: `docs/decisoes/0003-regra-b-itens-sem-desdobramento.md`.

- **Cadeia completa** (iniciativa → release → épico): sempre aparece, respeitando os filtros.
- **Iniciativa sem release**: aparece com o selo **"sem release"**, exceto se estiver na **última coluna** do fluxo (concluída).
- **Release sem épico**: aparece com o selo **"sem épico"** e leva a sua iniciativa junto, exceto se estiver na **última coluna** (entregue).
- A opção **"Mostrar itens sem desdobramento"** (barra de filtros, ligada por padrão) liga/desliga os dois casos acima. Desligada, o quadro mostra só a cadeia completa.
- Com filtro de **Time** ou **Roadmap interno** ativo, itens sem desdobramento não aparecem (esses filtros dependem de épicos e itens de time).
- As listas dos filtros de Roadmap executivo e Responsável só consideram iniciativas que podem aparecer (`iniCanAppear`).

### 3.1 Filtros (somam-se: E lógico)

| Filtro | Aplica-se a |
|---|---|
| Roadmap executivo | `AnoSemestreRoadmap` da iniciativa |
| Responsável da iniciativa (múltiplo) | `Assigned To` da iniciativa; não filtra releases, épicos e itens |
| Roadmap interno | semestre do `Target Date` do épico |
| Time | épicos com pelo menos um item do time; itens só daquele time; métricas do épico passam a considerar só o time |
| ID ou descrição (decisão `0034`) | ID exato ou parte do título (sem acento, sem maiúsculas), em qualquer nível (iniciativa, release, épico ou item de time) — quem casa revela a cadeia até a iniciativa; quando só um item de time casa, os demais itens do épico continuam escondidos |

## 4. Fluxo e status

- **Status** = a última coluna do fluxo que está preenchida (tem data) no registro.
- **Planilha**: o fluxo de cada aba é identificado pelos nomes da primeira e da última coluna (`FLOW` em `src/js/00-cabecalho.js`):
  - Iniciativa: `Materialização da Oportunidade ou Solicitação` → `Concluído`
  - Release: `Inventário de Opções de Valor` → `Entregue`
  - Épico e times: `Backlog` → `Fechado`
- **Azure DevOps**: o fluxo é o do quadro real (primeira e última coluna reais), sem nomes fixos. Colunas divididas viram `Nome Doing` e `Nome Done`. Ver `docs/integracao-azure.md`.
- Vários quadros no mesmo nível (ex.: duas Coordenações de Épico) têm as colunas unificadas preservando a ordem.

## 5. Roadmap

- **Executivo**: `AnoSemestreRoadmap` da iniciativa (ex.: `2026 2º Semestre`).
- **Interno**: semestre do `Target Date` do épico (jan–jun = 1º, jul–dez = 2º).
- **Divergência**: roadmap interno do épico ≠ executivo da iniciativa → alerta "Roadmap" no épico e nos pais.

## 6. CycleTime (CT)

### 6.1 CT do item de time

- Configurado **por time** em Configurações › Fluxo dos times (coluna "Entra no CT").
- **Entrada** = primeira coluna marcada no fluxo do time; **saída** = última marcada.
- Padrão (sem configuração): `READY / PRONTO PARA DEV` → `Pronto para Deploy` (`CT_DEF`). Times cujo quadro não tem essas colunas ficam com CT vazio até serem configurados.
- Data de entrada: a da coluna de entrada; se vazia, a primeira coluna preenchida entre entrada e saída.
- Data de saída: a da coluna de saída; se vazia, a primeira coluna preenchida depois dela.
- **CT** = saída − entrada, em dias; sem saída, hoje − entrada (em andamento). Sem entrada, CT vazio.

### 6.2 CT do épico

- Considera só os itens dos **tipos configurados** (padrão: User Story, Technical Story, Technical Solution).
- **Início** = a menor data de entrada entre esses itens; **fim** = a maior data de saída, se **todos** já saíram; senão, hoje.
- O painel do épico explica o cálculo ("Como o CT foi calculado"): item e data de início, item e data de fim.
- **Ag. Deploy** = maior data de saída entre **todos** os itens (todos os tipos), somente se todos saíram. Por isso pode estar vazio mesmo com CT fechado.

## 7. Categorias de coluna e fase

Configuradas por time (aba do time em Configurações › Fluxo dos times): cada coluna é **Nenhum**, **Discovery**, **WIP** ou **Vazão**.

Padrão quando não configurado (`defaultSets`):
- Vazão: de `Aguardando/Pronto para Deploy` até o fim (se não houver, só a última coluna);
- WIP: de `READY` até antes da Vazão;
- Discovery: depois da primeira coluna até antes do WIP.

Cada coluna também pode ser marcada, independentemente da categoria acima, como **Fila de espera** (waiting time) — usado só pelo quadrante Eficiência de fluxo do Report F4P (§12.9). Estilo "Queueing Stages" do Actionable Agile (ferramenta de Analytics usada como referência): o usuário marca só as colunas de fila de espera; as demais colunas contam como **Touch time** (em trabalho) automaticamente, sem um terceiro estado "sem classificação".

**Card do épico**: contagens Backlog (Nenhum), Discovery, WIP e Vazão de todos os itens vinculados, barra de distribuição e **fase**:

| Fase | Regra |
|---|---|
| sem itens | nenhum item vinculado |
| Fechado | todos os itens em Vazão |
| WIP | algum item em WIP, ou parte em Vazão e o resto sem começar |
| Discovery | algum em Discovery e nenhum em WIP |
| Backlog | nenhum iniciado |

**Situação herdada** (release e iniciativa): `Fechado` se todos os filhos visíveis estão fechados; `Aberto` caso contrário; `sem épico` / `sem release` quando não há filhos.

## 8. Alertas

Níveis, do mais grave: `outlier` > `alert` (atraso, roadmap) > `warn` (atenção, parado, pausado) > `info` (avisos de tag). A saúde de um pai é o pior nível dos filhos visíveis.

### 8.1 CycleTime do item

| Situação | Time com CT planejado | Regra geral (time sem CT máximo) |
|---|---|---|
| Limites | por time: atenção, CT máximo, outlier, parado | 30 / 60 / 90 / 10 dias (editáveis) |
| Atenção | item **em andamento** com CT ≥ atenção | em andamento com CT ≥ 30 |
| Atraso | CT > máximo, **em andamento ou concluído** | em andamento com CT > 60 |
| Outlier | CT ≥ outlier, **em andamento ou concluído** | em andamento com CT ≥ 90 |

Validação: atenção < CT máximo < outlier.

### 8.2 Parado na coluna

Item em coluna **WIP** há mais dias que o limite (do time ou geral). A contagem parte da data da coluna atual.

### 8.3 Mensagens

Cada alerta traz: diagnóstico com a meta como referência (ex.: "Já consumiu 90% do CT máximo…"), medidor visual (no painel do item) e "O que fazer". Nos pais, um **Resumo** agrupa os alertas e sugere a prioridade (bloqueios primeiro).

## 9. Tags cadastradas

| Tag | Reconhece | Cor padrão | Alerta | Data |
|---|---|---|---|---|
| BLOCKED | blocked, bloqueado, impedido; coluna `Blocked` = true | #E57373 | alert | desde (via `Blocked Days`) |
| PAUSADO | pausado, paused, pausa | #4B5563 | warn | desde (data da coluna atual) |
| URGENTE | urgente, urgent | #FDE047 | info | desde (data da coluna atual) |
| DATA FIXA | data fixa, datafixa, fixed date | #7DD3FC | info | para o dia (`Target Date` do item, se existir) |

- O card do item ganha a cor de fundo da primeira tag encontrada (ordem da configuração) e o texto se ajusta para contraste.
- Alertas de tag só para itens **abertos** (fora da Vazão).
- Tags são editáveis e é possível cadastrar novas.

## 10. Visão analítica

Habilitada com **Time** e **Roadmap** (interno ou executivo) no filtro. Uma linha por épico com itens do time.

- **QTD**: itens dos tipos do CT, no time, do épico daquela linha.
- **Projetada**: sempre a **soma do QTD de cada épico** mostrado na tabela (nunca uma contagem à parte) — itens do time dos tipos do CT, de todos os épicos visíveis.
- **Capacidade**: sempre a **soma do "reservado" de cada épico** mostrado na tabela — subconjunto do QTD de cada épico cujo `o.tags` inclui a tag de capacidade (`CFG.anTag`, padrão `ROADMAP`). A linha do épico mostra essa quantidade reservada logo após a descrição do épico (decisão `0027`); o badge "X US" que ficava ao lado foi removido por ser redundante com a coluna QTD (decisão `0028`).
- **Transparência** (decisões `0027`/`0028`): tanto os dois números do cabeçalho (Capacidade e Projetada, somando todos os épicos) quanto o QTD e o "reservado" de **cada linha** (só os itens daquele épico) são clicáveis e abrem a lista dos itens exatos que entram na soma — ID, título e situação (Backlog, Discovery, WIP ou Vazão, com a data de saída quando Vazão) — mesmo modal e mesma navegação até o item do Report F4P (`f4pItemsModal`/`f4pItemSituacao`, reaproveitados).
- **Status**: fase do épico no time (+ coluna do item aberto mais avançado) e, numa linha própria, o mesmo **agrupador por categoria** (Backlog, Discovery, WIP e Vazão, com quadradinho colorido e contagem) já usado no card do épico no quadro (`distGroup`, decisão `0029`) — sempre as 4 categorias, mesmo com contagem zero, contando só os itens do time em análise (mesma base do QTD/Capacidade/Projetada). **Flow**: Ready, Ag. Deploy e CT do épico no time; CT em vermelho acima do máximo.
- **Ref.**: roadmap interno (ou executivo) em formato `2S/26` e Capex/Opex (coluna configurável).
- **Dead line** = fim do semestre − "dias antes do fim do semestre" − CT máximo do time. Itens ainda fora do fluxo do CT são destacados (laranja a menos de 14 dias, vermelho após o prazo).
- **Épicos sem release/iniciativa, filtrando por roadmap interno** (decisão `0036`): um épico sem release válida (por isso fora do quadro normal) ainda aparece aqui se tiver itens do time filtrado e o **Target Date** dele cair no semestre do roadmap interno selecionado — no lugar da linha `[IN][id] título`, mostra o aviso `OBS: SEM INICIATIVA e SEM RELEASE`, e entra normalmente nas somas de QTD/Capacidade/Projetada. Só vale para roadmap **interno** (o próprio Target Date do épico); no executivo não aparece, porque não há iniciativa da qual herdar um roadmap executivo.

## 11. Higiene de dados

Lista: importação (CSV detectado, registros reparados/descartados), carga do Azure (Removed excluídos, vínculos divergentes), itens órfãos, épicos inválidos e releases sem iniciativa.

## 12. Report F4P

Especificação completa: `docs/backlog/report-f4p.md`. Decisões de implementação: `docs/decisoes/0011-report-f4p-quadrantes-1-e-2.md`.

Habilitado com **Time** e **Roadmap** (interno ou executivo) no filtro, igual à Visão analítica — mas o filtro só libera o acesso ao painel: o relatório sempre mostra **todos os times carregados no momento** (`S.model.teams`, o mesmo conjunto das colunas do quadro), independente de qual time está selecionado. Semestre **futuro** (ainda não começou): a aba fica desabilitada (não há dados possíveis) e, se o painel já estiver aberto, recolhe sozinho.

### 12.1 Janela de datas por semestre (regra geral do Report F4P)

**Vale para qualquer quadrante calculado cuja amostra dependa de uma data de fechamento/saída, exceto quando o próprio quadrante documenta uma janela diferente** — hoje CycleTime e Variabilidade; qualquer quadrante novo que precise de um período deve reaproveitar esta mesma regra (função `f4pWindow` em `src/js/23-report-f4p.js`), não inventar uma variante própria (foi o que causou o bug corrigido pela decisão `0015`), a menos que tenha uma razão de negócio para divergir e documente essa divergência (é o caso de Urgente, Technical Story e Vazão, cuja meta é "por semestre" — ver §12.4, §12.5, §12.6 e decisões `0017`/`0018`/`0022`, função `f4pExactSemesterWindow`). O período depende do semestre escolhido no filtro (Roadmap interno tem prioridade sobre o executivo; `f4pSemesterState`):

| Semestre selecionado | Janela |
|---|---|
| Em curso (contém hoje), ou nenhum semestre reconhecido no filtro | Últimos **N meses** a partir de hoje (`CFG.f4p.months`, padrão 6) — janela corrida, **não** o início do semestre |
| Já encerrado (terminou antes de hoje) | Só as datas **dentro daquele semestre** (1/jan–30/jun ou 1/jul–31/dez) |
| Ainda não começou | Painel desabilitado (ver acima) |

Uso em CycleTime/Variabilidade: itens **concluídos** (com `o.deploy` preenchido) dos **tipos configurados** (`CFG.f4p.types`, padrão User Story e Technical Story), de **todos** os itens do time (não filtrada por qual épico/iniciativa está no roadmap selecionado), cuja data de saída cai dentro da janela acima.

### 12.2 CycleTime (reserva vs. atual)

- **Reserva**: CT máximo do time (`limitsOf(time).max`); sem CT planejado, usa o limite geral e sinaliza no texto de apoio.
- **Atual**: **P95** do CT da amostra, por **interpolação linear** (igual ao `PERCENTIL.INC` do Excel — função `percentil`).
- Indicador: P95 > reserva → ▼ vermelho; P95 ≤ reserva → ▲ verde. Sem amostra, mostra "--".

### 12.3 Variabilidade (min vs. atual vs. max)

- **Variabilidade** = P95 ÷ **P50** da mesma amostra, 1 casa decimal (`dec1`).
- **Min/Max esperados**: por time (`CFG.f4p.teams[time]`), padrão **1.5** / **3.5**.
- Indicador: acima do máximo → ▼ vermelho; dentro da faixa → ▲ verde; abaixo do mínimo → ▼ laranja.
- P50 = 0 ou sem amostra → "--"; o tamanho da amostra (n) e o P50 ficam disponíveis no texto de apoio (title) da célula.

### 12.4 Urgente (meta vs. realizado)

Gestão da Classe de Serviço **Expedite**. Decisões e limitação de dados: `docs/decisoes/0014-report-f4p-quadrante-urgente.md`, `docs/decisoes/0015-report-f4p-urgente-limite-de-data.md` (correção de um bug de contagem) e `docs/decisoes/0017-report-f4p-urgente-periodo-exato-do-semestre.md` (janela própria por período exato do semestre).

- **Tag Expedite**: qualquer uma das tags cadastradas (`docs/regras-de-negocio.md` §9), escolhida em Configurações › Report F4P (`CFG.f4p.expediteTag`, padrão a tag "URGENTE"). Um item conta se `o.tagHits` inclui essa tag — **de qualquer tipo** (não usa `CFG.f4p.types`, ao contrário de CycleTime e Variabilidade).
- **Meta**: número inteiro cadastrado por time (`CFG.f4p.teams[time].urgentMeta`), representando o teto de itens Expedite aceitável no semestre. Sem meta cadastrada, a célula mostra "--" e o Realizado fica sem cor de alerta (nem verde, nem vermelho).
- **Realizado**: usa uma janela **própria** (`f4pExactSemesterWindow`), diferente da janela geral do §12.1 — o **período exato do semestre selecionado** (1/jan–30/jun ou 1/jul–31/dez), esteja ele em curso ou já encerrado, nunca a janela corrida de N meses. Motivo (decisão `0017`): a janela corrida "vazava" itens fechados ainda dentro do semestre anterior para a contagem do semestre em curso. Sem semestre reconhecido no filtro, cai na janela corrida do §12.1 por segurança. O portal não guarda histórico de quando uma tag foi aplicada (só o estado atual e a data de fechamento), então:
  | Situação do item | Conta no Realizado? |
  |---|---|
  | Aberto (com a tag) | Sempre — não importa há quanto tempo está aberto |
  | Fechado (com a tag) | Só se a data de fechamento (`o.deploy`) cair dentro do período exato do semestre selecionado |
- Indicador de cor do número: Realizado > Meta → vermelho; Realizado ≤ Meta → verde; sem meta cadastrada → sem cor — mesma convenção do CycleTime (§12.2).
- **Tendência** (▲ aumentando / ▼ reduzindo / ◆ estável): compara quantos itens com a tag **fecharam** nos últimos 3 meses (a partir de hoje) contra os 3 meses anteriores a esses — sempre essa janela corrida de 6 meses, **independente do semestre selecionado no filtro**. Sem margem de tolerância: qualquer diferença já decide ▲ ou ▼; só empate exato é ◆. A cor da seta é neutra (não segue o vermelho/verde da Meta).
- **Transparência**: o número do Realizado é clicável e abre a lista dos itens exatos que entraram na contagem (ID, título, situação); cada ID leva direto até o item no quadro (`gotoId`). A coluna "Situação" mostra a **categoria da coluna atual** do item — Backlog, Discovery, WIP ou Vazão (com a data de saída, quando existir) — pela mesma configuração de fluxo por time usada no resto do portal (`catOf`, Configurações › fluxo dos times), não um "Aberto"/"Fechado" próprio do Report F4P (decisão `0019`). A contagem em si (o que entra no Realizado) continua decidida por `o.deploy` estar ou não preenchido, como na tabela acima — só a exibição na lista mudou.

### 12.5 Technical Story (meta vs. realizado)

Mesmo comportamento do Urgente (§12.4), mas conta itens pelo **tipo** do item em vez de uma tag, a meta tem um padrão numérico em vez de ficar "sem meta", e o Realizado só considera itens **já entregues**. Decisões: `docs/decisoes/0018-report-f4p-quadrante-technical-story.md` e `docs/decisoes/0020-report-f4p-technical-story-so-itens-entregues.md`.

- **O que conta**: itens cujo tipo é **Technical Story** (`norm(o.type) === "technical story"`) — tipo fixo, não usa `CFG.f4p.types` (que é só de CycleTime/Variabilidade) nem é configurável, ao contrário da tag do Urgente.
- **Meta**: número inteiro cadastrado por time (`CFG.f4p.teams[time].tsMeta`). **Padrão 6** quando o time não cadastra a própria meta — diferente do Urgente, que fica sem meta (e sem cor) nesse caso.
- **Realizado**: usa `f4pExactSemesterWindow` (período exato do semestre selecionado, em curso ou encerrado), mas **diferente do Urgente** só conta itens cuja categoria de fluxo atual (`catOf`, mesma classificação usada na Situação, §12.4/decisão `0019`) seja **Vazão** — e cujo `o.deploy` caia dentro desse período. Itens em Backlog, Discovery ou WIP **não contam**, mesmo abertos há muito tempo (decisão `0020`): a meta deste quadrante mede entrega no período, não risco em aberto.
- Indicador de cor do número: Realizado > Meta → vermelho; Realizado ≤ Meta → verde — sempre colorido (a meta nunca fica em branco).
- **Sem seta de tendência**: ao contrário do Urgente, este quadrante não tem indicador de tendência.
- **Transparência**: o número do Realizado é clicável e abre a lista dos itens exatos que entraram na contagem, igual ao Urgente — mesma coluna "Situação" por categoria de fluxo (`gotoId` para navegar até o item).

### 12.6 Vazão (reserva vs. reserva entregue vs. realizado)

Gestão da entrega do time no período do roadmap selecionado. Decisões: `docs/decisoes/0022-report-f4p-quadrante-vazao.md`, `docs/decisoes/0023-report-f4p-vazao-tendencia-com-wip.md` (tendência somando itens em WIP), `docs/decisoes/0024-report-f4p-vazao-cor-da-seta-por-realizado-vs-reserva.md` (cor da seta por Realizado vs. Reserva) e `docs/decisoes/0043-vazao-us-reserva-entregue-e-reservado-por-semestre.md` (campo Reserva entregue e o recorte Reservado/Planejado outro semestre do User Story).

- **Filtro de dados**: itens dos **tipos configurados para o CT** (`CFG.f4p.types`, o mesmo campo de CycleTime/Variabilidade — padrão User Story e Technical Story; não é uma configuração própria), cuja categoria de fluxo atual (`catOf`, decisão `0019`) seja **Vazão** (entregue) — itens em Nenhum (Backlog), Discovery ou WIP não contam. Período: `f4pExactSemesterWindow` (o mesmo do Urgente/Technical Story) — 1/jan–30/jun ou 1/jul–31/dez do semestre selecionado no filtro (Roadmap interno tem prioridade sobre o executivo), esteja ele em curso ou já encerrado; `o.deploy` precisa cair dentro desse período.
- **Realizado**: todos os itens do conjunto acima, com ou sem a tag de capacidade.
- **Reserva**: subconjunto do Realizado cujo `o.tags` inclui a **tag que marca a capacidade do roadmap** (`CFG.anTag`, padrão "ROADMAP" — a mesma configuração já usada pela Visão analítica, §10, para a coluna Capacidade; casamento pelo texto da tag, não pelo id de uma tag cadastrada). Por construção, Reserva nunca é maior que Realizado — é um filtro sobre o mesmo conjunto, não uma contagem à parte.
- **Reserva entregue** (decisão `0043`): subconjunto da Reserva cujo **épico vinculado** (`o.epicoId`) tem **compromisso de roadmap batendo com o semestre selecionado** — o mesmo critério interno/executivo já usado pelo Roadmap – Épicos (§12.7) para decidir se um épico "está no Roadmap" do semestre, reaproveitado aqui como comparação (não muda aquele quadrante): Roadmap Interno compara o Target Date do próprio épico (`e.interno`); Roadmap Executivo sobe Épico → Release → Iniciativa e compara o `AnoSemestreRoadmap` da iniciativa (`i.exec`). Uma reserva cujo épico aponta pra um compromisso de **outro semestre**, ou que **não tem compromisso registrado** (sem Target Date/sem iniciativa com `AnoSemestreRoadmap` preenchido), não entra na Reserva entregue — mas continua contando normalmente na Reserva e no Realizado. Por construção, Reserva entregue nunca é maior que Reserva.
- **Sem cor nos números**: não há meta/teto configurável para este quadrante (Reserva é informativa, não um limite a não ultrapassar), então os números da Reserva, Reserva entregue e do Realizado não ficam vermelhos nem verdes.
- **Tendência** (▲ melhora / ▼ piora / ◆ estável): separa o Realizado por mês corrido dentro do período do semestre — só os meses já decorridos, se o semestre estiver em curso (meses futuros não têm itens possíveis, então ficam de fora do cálculo em vez de contarem como zero) — e compara o **mês corrente** (ou o último mês do semestre, se já encerrado) **mais os itens hoje em WIP** contra a **média** dos meses anteriores do mesmo período, arredondada sempre **para cima** (decisão `0023`). Itens em WIP ainda não viraram Vazão, mas sinalizam entrega a caminho, então somam a favor da tendência mesmo antes de serem entregues. Sem meses anteriores para comparar (semestre com um único mês decorrido), fica ◆.
- **Cor da seta de tendência** (decisão `0024`): ao contrário dos números, a seta/losango da tendência é colorida — **verde** quando Realizado ≥ Reserva, **vermelho** quando Realizado < Reserva. Como Reserva é sempre um subconjunto do Realizado (item acima), a cor vermelha não é alcançável em uso normal; a checagem existe mesmo assim, por pedido explícito do usuário, como salvaguarda visual.
- **Transparência**: os três números (Reserva, Reserva entregue e Realizado) são clicáveis e abrem a lista dos itens exatos que entraram em cada contagem, igual aos demais quadrantes calculados (`gotoId` para navegar até o item).

### 12.7 Roadmap – Épicos (roadmap vs. roadmap entregue vs. atual)

Único quadrante que opera sobre os **cards do quadro de Épicos** (`S.model.epis`, `S.model.stages.epi`, `e.st`, `e.target`), não sobre os itens operacionais dos times como os demais quadrantes calculados. "Fechado", aqui, é a **última coluna do próprio quadro de Épicos** (`e.st === S.model.stages.epi.length - 1`, função `f4pEpiClosed`) — não a categoria de fluxo (`catOf`) de nenhum time, conceito que não existe neste nível. Decisões: `docs/decisoes/0025-report-f4p-quadrante-roadmap-epicos.md` e `docs/decisoes/0026-report-f4p-roadmap-epicos-vinculo-epico-time.md` (reforço do vínculo épico↔time).

- **Filtro de dados**: épicos dos **tipos configurados** para este quadrante (`CFG.f4p.epiTypes`, configuração própria — padrão **Epic** — independente de `CFG.f4p.types`, que é dos itens operacionais) com pelo menos um item operacional vinculado ao time em questão (`f4pEpiHasTeam`, mesma ideia de `S.model.teams`, aplicada por épico). **O vínculo épico↔time é sempre pelos itens filhos** (Parent → Child: `o.epicoId`/`ID_EPICO_UNICRED` no item, não uma associação direta do épico com um time) — vale para os três números (Roadmap, Roadmap entregue e Atual), nos dois roadmaps (interno e executivo). Um épico só entra na contagem de um time se **esse time** tiver pelo menos um item vinculado a ele; se todos os itens do épico forem de outro time, ele conta **só** para esse outro time, nunca para o primeiro — mesmo que o épico apareça no Roadmap do primeiro por Target Date ou por vínculo com a iniciativa (decisão `0026`).
- **Roadmap**: todos os épicos do conjunto acima dentro do semestre selecionado no filtro, **qualquer estágio** (aberto ou fechado), sem duplicidade (por ID). O critério de "estar no semestre" muda conforme qual Roadmap está ativo (Interno tem prioridade sobre o Executivo, igual ao resto do Report F4P — `f4pSemester`):
  | Roadmap selecionado | Critério de "estar no Roadmap" |
  |---|---|
  | Interno | Target Date do **próprio épico** cai no semestre selecionado (`e.interno`) — o vínculo com a iniciativa é irrelevante aqui |
  | Executivo | Épico vinculado (via Release) a uma **Iniciativa** cujo `AnoSemestreRoadmap` é o semestre selecionado — o Target Date do próprio épico é irrelevante aqui |
- **Roadmap entregue**: subconjunto do Roadmap acima (mesmo critério interno/executivo) que já está **fechado** (última coluna do quadro de Épicos).
- **Atual**: épicos do conjunto de dados (tipos configurados + item do time) que estão **fechados** e cuja data de fechamento (`e.stDate`, a data da própria coluna final do quadro de Épicos) cai dentro do **período exato do semestre selecionado** (`f4pExactSemesterWindow`, mesma janela do Urgente/Technical Story/Vazão) — **independente do critério do Roadmap**: não olha o Target Date do próprio épico nem o vínculo com a iniciativa, qualquer que seja o Roadmap (interno ou executivo) selecionado. É uma contagem à parte, não um subconjunto do Roadmap.
- **Tendência** (▲ melhora / ▼ piora / ◆ estável): mesma regra inspiracional do Vazão (§12.6, decisão `0023`), adaptada para o fluxo de Épicos — separa o Atual por mês corrido dentro do período (só os meses já decorridos, no semestre em curso) e compara o **mês corrente mais os épicos do Roadmap ainda abertos** (o "WIP" deste quadrante — épicos do Roadmap que ainda não chegaram na última coluna) contra a **média** dos meses anteriores, arredondada sempre para cima. Sem meses anteriores para comparar, fica ◆.
- **Transparência**: os três números (Roadmap, Roadmap entregue, Atual) são clicáveis e abrem a lista dos épicos exatos que entraram em cada contagem (`gotoId` para navegar até o item). A coluna "Situação" mostra a **coluna do próprio quadro de Épicos** (não a categoria de fluxo operacional de nenhum time), com a data de saída quando o épico estiver fechado.

### 12.8 User Story (reservado vs. planejado outro semestre vs. não planejado)

Mesmo critério de "entregue" do Technical Story/Vazão (categoria de fluxo Vazão, `catOf`), mas com uma lista de tipos própria e uma divisão em **partição** (não subconjunto/conjunto total como no Vazão). Decisões: `docs/decisoes/0030-report-f4p-quadrante-user-story.md` e `docs/decisoes/0043-vazao-us-reserva-entregue-e-reservado-por-semestre.md` (recorte Reservado/Planejado outro semestre).

- **Filtro de dados**: itens dos **tipos configurados para este quadrante** (`CFG.f4p.usTypes`, configuração própria — padrão **User Story** — independente de `CFG.f4p.types` e de `CFG.f4p.epiTypes`) cuja categoria de fluxo atual seja **Vazão** (entregue), cujo `o.deploy` caia dentro do **período exato do semestre selecionado** (`f4pExactSemesterWindow`, mesma janela do Urgente/Technical Story/Vazão).
- **Planejado** (agregado interno, não exibido diretamente): subconjunto do conjunto acima cujo `o.tags` inclui a **tag de capacidade do roadmap** (`CFG.anTag`, a mesma do Vazão/Visão analítica).
- **Não planejado**: o **restante** do conjunto acima — os itens **sem** essa tag. Diferente do Vazão (Reserva ⊆ Realizado), aqui Planejado e Não planejado formam uma **partição exata**: todo item entregue do tipo configurado está num dos dois grupos, nunca nos dois, e a soma dos dois é sempre igual ao total entregue.
- **Reservado / Planejado (outro semestre)** (decisão `0043`): o Planejado acima se divide, por sua vez, numa segunda **partição exata** — mesmo critério de "compromisso de roadmap batendo com o semestre selecionado" usado pela Reserva entregue do Vazão (§12.6): **Reservado** é o subconjunto do Planejado cujo épico vinculado (`o.epicoId`) tem compromisso de roadmap (Interno: Target Date do próprio épico; Executivo: `AnoSemestreRoadmap` da iniciativa, subindo Épico → Release → Iniciativa) no **mesmo semestre selecionado**; **Planejado (outro semestre)** é o restante do Planejado — inclui tanto um compromisso que aponta pra outro semestre quanto um épico **sem nenhum compromisso registrado**. A soma de Reservado + Planejado (outro semestre) é sempre igual ao Planejado total, então a conferência cruzada abaixo (que soma o Planejado como um todo) não muda com esse recorte.
- **Tendência** (▲ melhora / ▼ piora / ◆ estável): mesma regra inspiracional do Vazão (§12.6, decisão `0023`) — separa o total entregue (Planejado + Não planejado) por mês corrido dentro do período e compara o mês corrente mais os itens hoje em WIP (dos tipos configurados) contra a média (arredondada pra cima) dos meses anteriores.
- **Transparência**: os três números exibidos (Reservado, Planejado outro semestre e Não planejado) são clicáveis e abrem a lista dos itens exatos de cada contagem, igual aos demais quadrantes calculados.
- **Conferência cruzada** (decisão `0030`): como Vazão, Technical Story e User Story são três recortes por tipo do mesmo universo de itens entregues no período, a soma **Technical Story Realizado + User Story Planejado (Reservado + Planejado outro semestre) + User Story Não planejado** deveria sempre igualar o **Vazão Realizado** de cada time — isso só é garantido por convenção entre as três configurações de tipos (`CFG.f4p.types`, o tipo fixo do Technical Story e `CFG.f4p.usTypes`), não por um vínculo estrutural no código. Quando um time diverge (ex.: `CFG.f4p.types` passa a incluir um tipo que nenhum dos outros dois quadrantes cobre), o painel mostra um aviso destacado no topo, listando o time e os números exatos de cada lado da conta, para o usuário investigar a configuração — em vez de mostrar números inconsistentes sem sinalização.

### 12.9 Eficiência de fluxo (min vs. atual vs. max)

Último quadrante do Report F4P — com ele, os 8 quadrantes do painel têm regra fechada. Eficiência do Fluxo = **Touch Time ÷ (Touch Time + Waiting Time) × 100**. Decisão: `docs/decisoes/0031-report-f4p-quadrante-eficiencia-de-fluxo.md`.

- **Janela de datas**: diferente de Urgente/Technical Story/Vazão/Roadmap-Épicos/User Story (que usam `f4pExactSemesterWindow`), este quadrante reaproveita **`f4pWindow`** (§12.1, decisão `0013`) — a mesma janela do CycleTime/Variabilidade: últimos `CFG.f4p.months` meses (padrão 6) até hoje, se o semestre selecionado estiver em curso; o período exato do semestre, se já encerrado.
- **Filtro de dados**: **todos** os itens do fluxo do time, únicos, vinculados ao time — não só os concluídos (diferente de CycleTime/Variabilidade, que usam só itens com CT fechado). Tipos considerados: `CFG.f4p.effTypes`, configuração própria; **vazio significa todos os tipos** (padrão), ao contrário das demais listas de tipo do Report F4P.
- **Fila de espera / Touch time por coluna**: cada coluna do fluxo de cada time pode ser marcada em Configurações › Fluxo dos times como **Fila de espera** (waiting time), independente da categoria Discovery/WIP/Vazão (§7). Estilo "Queueing Stages" do Actionable Agile (ferramenta de Analytics citada pelo usuário como referência): o usuário marca só as colunas de fila; as demais colunas contam como **Touch time** automaticamente — não existe mais um terceiro estado "sem classificação" à parte.
- **Cálculo por item**: cada coluna preenchida do item vira um intervalo (da própria data até a data da próxima coluna preenchida, ou hoje, se o item ainda não avançou), somado ao total de Touch ou Waiting do time conforme a marcação da coluna onde o intervalo começa. Só a parte de cada intervalo que cai dentro da janela de datas conta (recorte, não exclusão do item inteiro) — um item que começou antes da janela ou ainda está aberto depois dela contribui só com a parcela dentro do período. **Exceção**: se a última coluna com data preenchida do item é da categoria Vazão (item já entregue), o intervalo dela não se estende até hoje — o relógio da eficiência para na entrega, para não somar como Touch/Waiting o tempo em que um item já concluído fica simplesmente parado no quadro.
- **Agregação**: soma de Touch e de Waiting de **todos** os itens do time no período (não a média das eficiências individuais), preservando o peso real de cada item. Sem nenhum item do time no período (Touch + Waiting = 0), mostra "--" — não é 0% de eficiência, é ausência de dado.
- **MIN/MAX**: faixa esperada configurável por time (`CFG.f4p.teams[time].effMin`/`effMax`), padrão **30%–55%**.
- **Cor**: dentro da faixa MIN–MAX → verde; fora (acima do máximo ou abaixo do mínimo) → vermelho — sem uma terceira cor intermediária, diferente da Variabilidade.
- **Tendência** (▲ melhora / ▼ piora / ◆ estável): compara a eficiência do período inteiro selecionado com a eficiência calculada só nos **últimos 2 meses** desse mesmo período — últimos 2 meses melhor → ▲; pior → ▼; igual (ou sem dado num dos dois lados) → ◆. Regra própria deste quadrante, não a mesma da tendência do Vazão (decisão `0023`).
- **Transparência**: o número atual é clicável e abre a lista dos itens exatos do time no período; a coluna "Situação" mostra o Touch/Waiting (já recortado pela janela) que cada item contribuiu para a soma.

## 13. Actionable

Painel lateral com o mesmo comportamento de habilitação da Visão analítica (§10) e do Report F4P (§12): habilitado com **Time** e **Roadmap** (interno ou executivo) no filtro, um time por vez (diferente do Report F4P, que sempre mostra todos os times). Semestre futuro: aba desabilitada, painel recolhe sozinho se já estiver aberto (mesma regra do Report F4P, `f4pEnabled`/`actEnabled`). Decisão: `docs/decisoes/0041-actionable-primeira-versao.md`.

**Primeira versão (MVP)**: estrutura fixa de 4 quadrantes em 2 colunas, inspirada no layout do Report F4P — só os dois primeiros têm regra definida; os outros dois aparecem como "Regra de cálculo ainda em definição" (mesmo padrão do Report F4P para um quadrante sem regra fechada) até serem detalhados.

### 13.1 CycleTime (dispersão)

Mesma amostra e mesma Reserva do quadrante CycleTime do Report F4P (§12.2) — não é um cálculo próprio: reaproveita `f4pSample` (itens concluídos, dos tipos configurados em `CFG.f4p.types`, dentro da janela do semestre selecionado — `f4pWindow`, §12.1) e o CT máximo do time (`limitsOf(time).max`) como Reserva.

- Cada item da amostra vira um ponto do gráfico de dispersão: eixo X = data de entrega (`o.deploy`), eixo Y = CycleTime em dias.
- Duas linhas de referência horizontais: **Reserva** (CT máximo do time) e **Atual** (P95 da amostra, mesmo cálculo do §12.2).
- Pontos acima da Reserva ficam destacados (mesma convenção de cor do Report F4P — vermelho para acima do limite, verde para dentro).
- **Transparência**: cada ponto é clicável e navega direto até o item (`gotoId`), fechando o painel.
- Sem itens concluídos no período, mostra uma mensagem em vez de um gráfico vazio.

### 13.2 Burnup Reserva

- **Reservado** (escopo do burnup): o mesmo conjunto de itens da **Capacidade** da Visão analítica (§10) — itens com a tag de capacidade do roadmap (`CFG.anTag`, padrão "ROADMAP") nos épicos do roadmap do time+semestre selecionado, em **qualquer status** (Backlog, Discovery, WIP ou Vazão) — não só os já entregues. Essa é uma diferença deliberada da Reserva do quadrante Vazão do Report F4P (§12.6), que só existe dentro do que já foi entregue: sem incluir os itens ainda não entregues, não haveria "quanto falta" para calcular.
- **Entregue**: subconjunto do Reservado cuja categoria de fluxo atual (`catOf`) é **Vazão**, com a saída caindo **dentro do período do semestre selecionado** (1/jan–30/jun ou 1/jul–31/dez; no semestre em curso, até hoje), acumulado mês a mês — um item entregue no último dia de um mês já conta dentro desse mês (limite inclusivo). Um item entregue **depois** desse período (ex.: um semestre já encerrado cuja entrega só saiu no semestre seguinte) não conta como Entregue **deste** período — estava previsto para ele, mas não chegou dentro do prazo.
- **Faltam**: o restante do Reservado que não é Entregue — complemento exato dentro do mesmo conjunto (Entregue + Faltam = Reservado sempre), não uma subtração à parte. Inclui, portanto, tanto os itens ainda não entregues quanto uma eventual entrega tardia fora do período (item acima).
- **Limitação assumida**: o portal não guarda histórico de quando um item entrou no roadmap, então a linha do Reservado no gráfico é sempre a contagem **atual**, mostrada como uma reta constante — não uma evolução real do escopo ao longo do semestre.
- **Transparência**: os números de Reservado, Entregue e **Faltam** são clicáveis e abrem a lista dos itens exatos de cada grupo, igual aos quadrantes calculados do Report F4P.
