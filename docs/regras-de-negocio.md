# Regras de negócio

Este é o documento de referência das regras do Mapa do Portfólio. Quando uma regra mudar, atualize este arquivo **e** o teste correspondente em `tests/`, e registre o motivo em `docs/decisoes/`.

Código principal: `src/js/01-configuracao-e-regras.js`, `src/js/04-modelo.js`, `src/js/05-estado-e-calculos.js`.

---

## 1. Hierarquia e vínculos

```
Iniciativa  ←(Parent)─  Release  ←(Parent)─  Épico  ←(vínculo)─  Item de time
```

| Nível | Aba na planilha | Vínculo com o nível acima |
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

Na planilha, uma aba é de time se o nome começa com `TIME ` (o time é o restante do nome) **ou** se ela tem a coluna `ID_EPICO_UNICRED` (o time é o nome da aba). Na carga do Azure, o nome do time é o "nome no portal" definido na fonte.

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
| Iniciativa (ID ou nome) | ID exato ou parte do título (sem acento, sem maiúsculas) |

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

- **QTD**: itens dos tipos do CT, no time.
- **Capacidade**: itens do time com a tag de capacidade (padrão `ROADMAP`); **Projetada**: todos (dos tipos do CT).
- **Status**: fase do épico no time (+ coluna do item aberto mais avançado). **Flow**: Ready, Ag. Deploy e CT do épico no time; CT em vermelho acima do máximo.
- **Ref.**: roadmap interno (ou executivo) em formato `2S/26` e Capex/Opex (coluna configurável).
- **Dead line** = fim do semestre − "dias antes do fim do semestre" − CT máximo do time. Itens ainda fora do fluxo do CT são destacados (laranja a menos de 14 dias, vermelho após o prazo).

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

### 12.6 Vazão (reserva vs. realizado)

Gestão da entrega do time no período do roadmap selecionado. Decisão: `docs/decisoes/0022-report-f4p-quadrante-vazao.md`.

- **Filtro de dados**: itens dos **tipos configurados para o CT** (`CFG.f4p.types`, o mesmo campo de CycleTime/Variabilidade — padrão User Story e Technical Story; não é uma configuração própria), cuja categoria de fluxo atual (`catOf`, decisão `0019`) seja **Vazão** (entregue) — itens em Nenhum (Backlog), Discovery ou WIP não contam. Período: `f4pExactSemesterWindow` (o mesmo do Urgente/Technical Story) — 1/jan–30/jun ou 1/jul–31/dez do semestre selecionado no filtro (Roadmap interno tem prioridade sobre o executivo), esteja ele em curso ou já encerrado; `o.deploy` precisa cair dentro desse período.
- **Realizado**: todos os itens do conjunto acima, com ou sem a tag de capacidade.
- **Reserva**: subconjunto do Realizado cujo `o.tags` inclui a **tag que marca a capacidade do roadmap** (`CFG.anTag`, padrão "ROADMAP" — a mesma configuração já usada pela Visão analítica, §10, para a coluna Capacidade; casamento pelo texto da tag, não pelo id de uma tag cadastrada). Por construção, Reserva nunca é maior que Realizado — é um filtro sobre o mesmo conjunto, não uma contagem à parte.
- **Sem indicador de cor**: não há meta/teto configurável para este quadrante (Reserva é informativa, não um limite a não ultrapassar), então os números não ficam vermelhos nem verdes.
- **Tendência** (▲ melhora / ▼ piora / ◆ estável): separa o Realizado por mês corrido dentro do período do semestre — só os meses já decorridos, se o semestre estiver em curso (meses futuros não têm itens possíveis, então ficam de fora do cálculo em vez de contarem como zero) — e compara o último mês contra a **média** dos meses anteriores do mesmo período. Sem meses anteriores para comparar (semestre com um único mês decorrido), fica ◆.
- **Transparência**: tanto o número da Reserva quanto o do Realizado são clicáveis e abrem a lista dos itens exatos que entraram em cada contagem, igual aos demais quadrantes calculados (`gotoId` para navegar até o item).

### 12.7 Demais quadrantes

Eficiência de fluxo, Roadmap–Épicos e User Story ainda não têm regra de cálculo definida; aparecem no painel como "em definição", mantendo a mesma grade e as mesmas colunas de time dos quadrantes calculados.
