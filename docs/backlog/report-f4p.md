# Report F4P

**Status**: Report F4P completo — os 8 quadrantes (CycleTime, Variabilidade, Urgente, Technical Story, Vazão, Roadmap – Épicos, User Story e Eficiência de fluxo) estão implementados. Ver `docs/regras-de-negocio.md` §12 e `docs/decisoes/0011` a `0031`.

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

Gestão da entrega do time no período do roadmap selecionado. Decisões: `docs/decisoes/0022-report-f4p-quadrante-vazao.md`, `docs/decisoes/0023-report-f4p-vazao-tendencia-com-wip.md` (tendência somando itens em WIP) e `docs/decisoes/0024-report-f4p-vazao-cor-da-seta-por-realizado-vs-reserva.md` (cor da seta). Regra completa: `docs/regras-de-negocio.md` §12.6.

Por time: `[Reserva] | [Realizado] [Tendência]`

- **Filtro**: itens dos tipos configurados para o CT (`CFG.f4p.types` — o mesmo campo de CycleTime/Variabilidade, não uma configuração própria; padrão User Story e Technical Story), já **entregues** (categoria de fluxo Vazão, igual ao Technical Story), com `o.deploy` dentro do período exato do semestre selecionado (`f4pExactSemesterWindow`, o mesmo do Urgente/Technical Story).
- **Realizado**: todos os itens do conjunto acima.
- **Reserva**: subconjunto do Realizado com a **tag de capacidade do roadmap** (`CFG.anTag`, padrão "ROADMAP" — a mesma configuração já usada pela Visão analítica, §10). Nunca maior que o Realizado, por ser um filtro sobre o mesmo conjunto.
- **Sem cor nos números**: não há meta/teto para este quadrante — Reserva é informativa, não um limite.
- **Tendência** (▲/▼/◆): separa o Realizado por mês corrido dentro do período (só os meses já decorridos, no semestre em curso) e compara o **mês corrente + itens hoje em WIP** contra a **média** (arredondada pra cima) dos meses anteriores do mesmo período (decisão `0023`). Sem meses anteriores para comparar, fica ◆.
- **Cor da seta**: verde quando Realizado ≥ Reserva, vermelho quando Realizado < Reserva (decisão `0024`) — não alcançável em uso normal, já que Reserva é sempre subconjunto do Realizado, mas implementada como salvaguarda visual.
- **Transparência**: tanto a Reserva quanto o Realizado são clicáveis e abrem a lista dos itens exatos de cada contagem.

## Quadrante 6 · ROADMAP – ÉPICOS (ROADMAP VS ROADMAP ENTREGUE VS ATUAL) — implementado

Único quadrante que opera sobre os **cards do quadro de Épicos** (`S.model.epis`), não sobre os itens operacionais dos times. Decisão: `docs/decisoes/0025-report-f4p-quadrante-roadmap-epicos.md`. Regra completa: `docs/regras-de-negocio.md` §12.7.

Por time: `[Roadmap] | [Roadmap entregue] | [Atual] [Tendência]`

- **Filtro**: épicos dos **tipos configurados para este quadrante** (`CFG.f4p.epiTypes`, configuração própria — padrão **Epic**, independente de `CFG.f4p.types`) com pelo menos um item operacional vinculado ao time.
- **Roadmap**: todos os épicos do conjunto acima dentro do semestre selecionado, qualquer estágio (aberto ou fechado). Semestre **Interno**: usa o Target Date do próprio épico. Semestre **Executivo**: usa o vínculo do épico com uma Iniciativa (via Release) cujo `AnoSemestreRoadmap` é o semestre selecionado — o Target Date do próprio épico é ignorado nesse caso.
- **Roadmap entregue**: subconjunto do Roadmap já **fechado** (última coluna do quadro de Épicos).
- **Atual**: épicos fechados cuja data de fechamento cai dentro do **período exato do semestre selecionado**, **independente** do critério do Roadmap (não olha Target Date nem vínculo com iniciativa, qualquer que seja o filtro de roadmap ativo) — contagem à parte, não um subconjunto do Roadmap.
- **Tendência** (▲/▼/◆): mesma regra do Vazão (decisão `0023`), adaptada para o fluxo de Épicos — mês corrente do Atual + épicos do Roadmap ainda abertos (o "WIP" deste quadrante) vs. média (arredondada pra cima) dos meses anteriores.
- **Transparência**: os três números são clicáveis e abrem a lista dos épicos exatos de cada contagem; a Situação mostra a coluna do próprio quadro de Épicos (não a categoria de fluxo operacional de nenhum time).

## Quadrante 7 · USER STORY (PLANEJADO VS NÃO PLANEJADO) — implementado

Mesmo critério de "entregue" do Technical Story/Vazão, mas com tipos próprios e uma divisão em partição. Decisão: `docs/decisoes/0030-report-f4p-quadrante-user-story.md`. Regra completa: `docs/regras-de-negocio.md` §12.8.

Por time: `[Planejado] | [Não planejado] [Tendência]`

- **Filtro**: itens dos tipos configurados para este quadrante (`CFG.f4p.usTypes`, configuração própria — padrão **User Story**, independente de `CFG.f4p.types` e de `CFG.f4p.epiTypes`), já **entregues** (categoria de fluxo Vazão), com `o.deploy` dentro do período exato do semestre selecionado (`f4pExactSemesterWindow`).
- **Planejado**: subconjunto do conjunto acima com a **tag de capacidade do roadmap** (`CFG.anTag`).
- **Não planejado**: o restante do conjunto acima, **sem** essa tag. Diferente do Vazão (Reserva ⊆ Realizado), aqui é uma **partição exata** — todo item entregue está num dos dois grupos, nunca nos dois.
- **Tendência** (▲/▼/◆): mesma regra do Vazão (decisão `0023`) — mês corrente do total (Planejado + Não planejado) + itens hoje em WIP vs. média (arredondada pra cima) dos meses anteriores.
- **Transparência**: tanto o Planejado quanto o Não planejado são clicáveis e abrem a lista dos itens exatos de cada contagem.
- **Conferência cruzada** (decisão `0030`): Vazão Realizado, Technical Story Realizado e User Story (Planejado + Não planejado) são três recortes por tipo do mesmo universo de itens entregues no período — a soma dos dois últimos deveria sempre bater com o primeiro, por time. Quando não bate (configuração de tipos inconsistente entre os três campos), o painel mostra um aviso destacado no topo com os números exatos de cada lado, por time, para o usuário investigar.

## Quadrante 8 · EFICIÊNCIA DE FLUXO (MIN VS ATUAL VS MAX) — implementado

Único quadrante que não olha a data de um único evento do item (entrega, fechamento), mas soma quanto tempo, dentro do período, cada item do fluxo passou em trabalho (touch time) e quanto passou parado numa fila (waiting time). Decisão: `docs/decisoes/0031-report-f4p-quadrante-eficiencia-de-fluxo.md`. Regra completa: `docs/regras-de-negocio.md` §12.9.

Por time: `[MIN] | [Atual] [Tendência] | [MAX]`

- **Fórmula**: Eficiência do Fluxo = Touch Time ÷ (Touch Time + Waiting Time) × 100.
- **Janela**: reaproveita `f4pWindow` (decisão `0013`, a mesma janela rolante do CycleTime/Variabilidade) — semestre em curso → últimos N meses (`CFG.f4p.months`) a partir de hoje; semestre já encerrado → período exato do semestre. **Diferente** dos demais quadrantes "por semestre" (Urgente, Technical Story, Vazão, Roadmap – Épicos, User Story), que usam `f4pExactSemesterWindow`.
- **Filtro**: todos os itens do fluxo do time (únicos, vinculados ao time — sem exigir conclusão), dos tipos configurados para este quadrante (`CFG.f4p.effTypes`, configuração própria); **vazio = todos os tipos** (padrão), ao contrário das demais listas de tipo do Report F4P, que caem num tipo fixo quando vazias.
- **Touch/Waiting time por coluna**: nova marcação em Configurações › Fluxo dos times — estilo "Queueing Stages" do Actionable Agile (ferramenta de Analytics usada como referência): o usuário marca só as colunas de **Fila de espera** (waiting time); as demais colunas contam como **touch time** automaticamente, sem um terceiro estado "sem classificação".
- **Cálculo por item**: cada coluna do fluxo do item vira um intervalo (da própria data até a data da próxima coluna preenchida, ou até hoje se ainda não avançou) classificado pela coluna onde o intervalo começa; só a parte do intervalo dentro da janela do período entra na soma (**recorte, não exclusão** do item inteiro). Exceção: se a última coluna com data é a de categoria Vazão (item já entregue), o intervalo não se estende até hoje — o relógio da eficiência para na entrega.
- **Agregação**: soma de touch e soma de wait de **todos** os itens do time no período (não a média das eficiências individuais) — pondera pelo tempo real de cada item.
- **MIN**/**MAX**: faixa esperada de eficiência, configurável por time (Configurações), padrão **30%**/**55%**.
- **Cor**: dentro da faixa MIN–MAX → verde; fora (para cima ou para baixo) → vermelho. Sem terceira cor.
- **Tendência** (▲/▼/◆): compara a eficiência do período inteiro selecionado com a eficiência só dos últimos 2 meses desse período — últimos 2 meses melhor (estritamente maior) → ▲; pior (estritamente menor) → ▼; igual, ou sem dado num dos dois lados → ◆ (o usuário pediu "🔹"; usei o "◆" já padronizado nos outros quadrantes deste painel, pela mesma consistência visual).
- **Sem item no período**: mostra "--" (não é 0% de eficiência, é ausência de dado).
- **Transparência**: o número Atual é clicável e abre a lista dos itens do time no período, com o touch/wait (já recortado pela janela) de cada um.

## Decisões adotadas (implementadas)

- Amostra CycleTime/Variabilidade: itens **concluídos** (com data de saída do CT) dos tipos configurados, de **todos** os itens do time (não filtrada por qual épico/iniciativa está no roadmap selecionado). **O período, porém, acompanha o semestre selecionado no filtro** (decisão `0013`, revisão do que este documento propunha originalmente): semestre em curso → últimos N meses a partir de hoje (janela corrida); semestre já encerrado → só as datas de saída dentro daquele semestre; semestre futuro → painel desabilitado (não há dados possíveis).
- Percentil por **interpolação linear** (igual ao `PERCENTIL.INC` do Excel) — função `percentil` em `src/js/02-utilitarios.js`.
- Indicadores: CT com P95 > máximo → ▼ vermelho; ≤ máximo → ▲ verde. Variabilidade > MAX → ▼ vermelho; dentro da faixa → ▲ verde; < MIN → ▼ laranja.
- P50 = 0 (ou amostra vazia) → variabilidade "--". O tamanho da amostra (n) e o P50 ficam no texto de apoio (`title`) da célula, não sempre visíveis.
- Ilustrações: as imagens reais do slide de referência (fornecidas pelo usuário), embutidas em base64 no build — não os SVGs originais cogitados inicialmente (decisão `0012`).
- Urgente: definição por tag configurável (não fixa em "URGENTE"), realizado sempre limitado ao período exato do semestre selecionado (abertos sempre contam; fechados só dentro do período), tendência por trimestres e cores conforme decisões `0014`, `0015` e `0017`.
- Technical Story: mesmo comportamento do Urgente, contando pelo tipo do item em vez de uma tag e com meta padrão 6 (não fica "sem meta"); sem tendência. A janela por período exato do semestre foi generalizada de `f4pUrgentWindow` para `f4pExactSemesterWindow`, reaproveitada pelos dois quadrantes (decisão `0018`). Depois de ver o quadrante em produção, o Realizado passou a contar só itens já entregues (categoria de fluxo Vazão) — itens em Backlog, Discovery ou WIP não contam mais, mesmo abertos há muito tempo (decisão `0020`, única divergência real do comportamento do Urgente).
- Situação na lista de itens (Urgente e Technical Story): categoria de fluxo do time (Backlog/Discovery/WIP/Vazão, com a data de saída na Vazão), pela mesma `catOf` usada no resto do portal, em vez de um "Aberto"/"Fechado" próprio do Report F4P (decisão `0019`).
- Vazão: mesmo critério de "entregue" do Technical Story (categoria de fluxo Vazão), mas com os tipos configurados para o CT (`CFG.f4p.types`) em vez de um tipo fixo; Reserva/Realizado por tag de capacidade (`CFG.anTag`, reaproveitada da Visão analítica) em vez de meta vs. realizado; números sem cor; Reserva e Realizado clicáveis (decisão `0022`). Tendência ajustada depois de ver o quadrante em produção: mês corrente somado aos itens hoje em WIP (trabalho a caminho de virar Vazão) contra a média dos meses anteriores, arredondada sempre pra cima (decisão `0023`). A seta da tendência (não os números) ganhou cor por Realizado vs. Reserva: verde se Realizado ≥ Reserva, vermelho se menor (decisão `0024`).
- Roadmap – Épicos: primeiro quadrante a operar sobre o quadro de Épicos em vez dos itens operacionais dos times; "fechado" é a última coluna do próprio quadro de Épicos (`e.st`), não `catOf`. Roadmap/Roadmap entregue seguem o Target Date do épico (semestre interno) ou o vínculo com a iniciativa via Release (semestre executivo); Atual é uma contagem independente, só pela data de fechamento no período do semestre, sem olhar Target Date nem iniciativa em nenhum dos dois casos. Tendência adaptada do Vazão (decisão `0023`), usando épicos do Roadmap ainda abertos como o "WIP" deste quadrante. Tipos de épico considerados por uma configuração própria (`CFG.f4p.epiTypes`, padrão Epic), independente de `CFG.f4p.types` (decisão `0025`).
- User Story: mesmo critério de "entregue" do Technical Story/Vazão, mas com tipos próprios (`CFG.f4p.usTypes`, padrão User Story); Planejado/Não planejado são uma partição exata (com/sem a tag de capacidade), não subconjunto/total como no Vazão. Tendência adaptada do Vazão (decisão `0023`). Adicionada uma conferência cruzada (Vazão Realizado = Technical Story Realizado + User Story Planejado + User Story Não planejado, por time) que sinaliza no painel quando a soma diverge — pedido explícito do usuário para detectar configuração de tipos inconsistente entre os três quadrantes (decisão `0030`).
- Eficiência de fluxo: único quadrante que soma duração recortada pela janela em vez de filtrar por uma única data do item; reaproveita `f4pWindow` (decisão `0013`), não `f4pExactSemesterWindow` como os quadrantes "por semestre" mais recentes. Touch/waiting time por coluna do fluxo é configurável estilo "Queueing Stages" do Actionable Agile (só se marca a Fila de espera; o resto é touch automaticamente, sem "sem classificação"). Tipos configuráveis com padrão vazio = todos os tipos (`CFG.f4p.effTypes`), diferente das demais listas de tipo do painel. MIN/MAX configuráveis por time (padrão 30%/55%); cor verde dentro da faixa, vermelha fora. Tendência própria (últimos 2 meses do período vs. o período inteiro), com "🔹" substituído por "◆" para manter a consistência visual dos outros quadrantes (decisão `0031`).

## Configuração implementada (seção "Report F4P" na tela de Configurações)

- Período do P95/P50 em meses (padrão 6) e tipos (padrão User Story e Technical Story) — valem para CycleTime, Variabilidade e Vazão.
- Tag da Classe de Serviço Expedite (padrão "URGENTE") — usada pelo quadrante Urgente.
- Tag de capacidade do roadmap (`CFG.anTag`, seção Visão analítica, padrão "ROADMAP") — reaproveitada pela Reserva do quadrante Vazão.
- Por time: variabilidade mínima (1.5) e máxima (3.5), com validação MIN < MAX; meta de Urgente (inteiro ≥ 0, opcional, independente da variabilidade); e meta de Technical Story (inteiro ≥ 0, opcional, padrão efetivo 6).
- Tipos de **épico** considerados pelo Roadmap – Épicos (`CFG.f4p.epiTypes`, padrão "Epic") — lista própria, independente da lista de tipos operacionais acima.
- Tipos considerados pelo **User Story** (`CFG.f4p.usTypes`, padrão "User Story") — lista própria, independente das outras duas.
- Tipos considerados pela **Eficiência de fluxo** (`CFG.f4p.effTypes`, padrão **vazio = todos os tipos**) — lista própria, única com esse padrão entre as do Report F4P.
- Por time: eficiência de fluxo mínima (30%) e máxima (55%), com validação MIN < MAX, junto com as demais colunas da tabela por time.
- Fluxo dos times (aba própria em Configurações): cada coluna ganha uma marcação **Fila de espera** (checkbox), separada da categoria Discovery/WIP/Vazão — usada só pela Eficiência de fluxo. Sem marcação, a coluna conta como touch time.

## Referências no código

- Painel: `src/js/23-report-f4p.js` (`f4pEnabled`, `renderF4P`, `openF4P`, `placeF4P`, `f4pSemesterState`, `f4pSample`, `f4pMetrics`, `f4pExpediteOps`, `f4pTsOps`, `f4pVazaoOps`, `f4pVazaoWipCount`, `f4pExactSemesterWindow`, `f4pUrgentRealizado`, `f4pUrgentTrend`, `f4pUrgentCell`, `f4pTsRealizado`, `f4pTsCell`, `f4pVazaoReservaItems`, `f4pVazaoRealizadoItems`, `f4pVazaoTrend`, `f4pVazaoCell`, `f4pItemSituacao`, `f4pEpiTypeOk`, `f4pEpiClosed`, `f4pEpiHasTeam`, `f4pRoadmapEpis`, `f4pRoadmapEntregueEpis`, `f4pRoadmapAbertosEpis`, `f4pAtualEpis`, `f4pRoadmapTrend`, `f4pRoadmapEpiCell`, `f4pEpiSituacao`, `f4pUsTypes`, `f4pUsOps`, `f4pUsPlanejadoItems`, `f4pUsNaoPlanejadoItems`, `f4pUsWipCount`, `f4pUsTrend`, `f4pUsCell`, `f4pReconciliacao`, `f4pReconciliacaoBanner`, `f4pEffTypes`, `f4pEffOps`, `f4pItemDurations`, `f4pEffPct`, `f4pEffTrend`, `f4pEffItemSituacao`, `f4pEffCell`), aba `#f4pTab` (dentro de `.side-tabs`) e painel `#f4pPanel` em `src/index.html`.
- Categoria de fluxo na lista de itens (Situação) e no filtro do Vazão: `catOf(o)` em `src/js/01-configuracao-e-regras.js` — a mesma função usada no restante do portal (itens por categoria do épico, alertas de "parado na coluna").
- Ilustrações: `src/assets/f4p/*.png`, embutidas como `F4P_ASSETS` (base64) por `scripts/build.mjs`.
- CT de cada item: `o.ct`, `o.ready`, `o.deploy` (calculados por `recomputeCt` conforme o fluxo do time, em `src/js/01-configuracao-e-regras.js`). Limites: `limitsOf(time)`; faixa de variabilidade: `f4pRangeOf(time)`; meta de Urgente: `f4pUrgentMetaOf(time)`; tag Expedite: `f4pExpediteTag()`; meta de Technical Story: `f4pTsMetaOf(time)`; tag de capacidade (Vazão): `CFG.anTag`; faixa de Eficiência de fluxo: `f4pEffRangeOf(time)`.
- Épico: `e.st`/`S.model.stages.epi` (posição no próprio quadro de Épicos, não `catOf`), `e.stDate` (data da coluna atual, calculada em `buildModel`, `src/js/04-modelo.js`), `e.interno` (semestre do Target Date), `e.exec` (semestre herdado da iniciativa via Release).
- Touch/waiting time de uma coluna do fluxo: `flowTimeOf(team, colName)` em `src/js/01-configuracao-e-regras.js` — lido de `CFG.flow[team].time`, escrito pela UI de Configurações › Fluxo dos times (`data-timewait` na tabela).
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
- [x] Seta de tendência do Vazão colorida por Realizado vs. Reserva (verde ≥, vermelho <), testada nos casos alcançáveis (Realizado maior e Realizado igual à Reserva).
- [x] Roadmap – Épicos: "Roadmap" segue o Target Date do próprio épico no semestre Interno e o vínculo com a iniciativa (via Release) no semestre Executivo, ignorando o outro critério em cada caso; testado nos dois modos com um épico que só entraria pelo critério certo.
- [x] "Roadmap entregue" é o subconjunto do Roadmap já fechado (última coluna do quadro de Épicos); "Atual" é uma contagem independente, só pela data de fechamento dentro do período do semestre, sem olhar Target Date nem vínculo com iniciativa em nenhum dos dois roadmaps — testado com épicos que provam a independência nos dois modos.
- [x] Filtro por tipo de épico configurável (`CFG.f4p.epiTypes`, padrão Epic) e por vínculo com o time (épico precisa ter item operacional do time), testados isoladamente.
- [x] Tendência do Roadmap – Épicos soma os épicos do Roadmap ainda abertos ao mês corrente do Atual e compara com a média (arredondada pra cima) dos meses anteriores, mesma regra do Vazão; testada com os três exemplos equivalentes (melhora, piora, estável) e sem meses anteriores.
- [x] Clique em qualquer um dos três números (Roadmap, Roadmap entregue, Atual) abre a lista dos épicos e navega até o item; Situação mostra a coluna do próprio quadro de Épicos, não a categoria de fluxo operacional.
- [x] User Story conta só itens dos tipos configurados (`CFG.f4p.usTypes`) já entregues (Vazão) no período; Planejado e Não planejado formam uma partição exata (soma = total entregue), testado com itens com e sem a tag.
- [x] Tendência do User Story soma os itens hoje em WIP ao mês corrente e compara com a média (arredondada pra cima) dos meses anteriores, mesma regra do Vazão; testada com os três exemplos equivalentes (melhora, piora, estável) e sem meses anteriores.
- [x] Clique no Planejado e no Não planejado abre a lista dos itens exatos e navega até o item.
- [x] Conferência cruzada: Vazão Realizado = Technical Story Realizado + User Story Planejado + User Story Não planejado, testada com o exemplo exato dado pelo usuário (38 = 27+4+7) e com um caso de configuração divergente, confirmando que o aviso aparece só quando a soma não bate.
- [x] Eficiência de fluxo usa a mesma janela do CycleTime/Variabilidade (`f4pWindow`), não a exata do semestre; testada comparando as duas janelas.
- [x] Touch/Waiting time por coluna configurável estilo "Fila de espera" (marca-se só a espera; o resto conta como touch automaticamente, sem estado "sem classificação"), persistido em `CFG.flow[time].time` e testado com colunas marcadas e não marcadas.
- [x] Cálculo por item soma o touch/wait de cada intervalo do fluxo recortado pela janela (não excluído por inteiro); testado com item cujo intervalo começa antes e termina depois da janela.
- [x] Item já entregue (última coluna com data é a de categoria Vazão) não soma tempo além da entrega, mesmo que o intervalo aberto até hoje seja grande.
- [x] Todos os itens do fluxo entram no cálculo, concluídos ou não; tipos configuráveis com padrão vazio = todos os tipos (`CFG.f4p.effTypes`), testado com e sem filtro de tipo.
- [x] Cor verde dentro da faixa MIN–MAX configurável por time (padrão 30%/55%), vermelha fora; testada nos dois casos.
- [x] Tendência compara a eficiência dos últimos 2 meses do período com a do período inteiro (▲ maior, ▼ menor, ◆ igual ou sem dado), testada nos três casos.
- [x] Sem item no período mostra "--"; clique no número Atual abre a lista dos itens com o touch/wait de cada um e navega até o item.
