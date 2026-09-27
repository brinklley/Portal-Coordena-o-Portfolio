# Telas e funcionalidades

## Primeiro acesso

Sem nenhuma carga guardada neste navegador (`IndexedDB "mapaPortfolioAzure"` vazio), o portal abre
direto na tela de Configurações › Azure DevOps, forçada e sem opção de fechar — todo o resto da
interface (barra de ferramentas, quadro, painéis) fica escondido até terminar a primeira carga.
Cadastre a organização (token), as fontes de Iniciativa/Release/Épico/Times e clique em "Carregar
dados do Azure DevOps" dentro da própria tela. Depois da primeira carga, o portal libera o resto da
interface e a aba "Configurações gerais" (ver `docs/configuracoes.md`). Ver decisão `0032`.

## Quadro (whiteboard)

- Níveis empilhados e centralizados: Iniciativas → Releases → Épicos → Operacional dos times. Clicar num card abre o nível abaixo; "Abrir cadeia completa" abre tudo.
- **Ilhas**: cada nível e cada time é uma ilha com borda. Times distribuídos em fileiras equilibradas (maiores primeiro). Colunas com mais de 6 itens quebram em subcolunas.
- **Barbantes** ligam pai e filho; cor = saúde do filho. No modo cadeia completa, épico → ilha do time (agregado) e, com foco num épico, item a item.
- **Ancorar/soltar ilhas**: soltas, podem ser arrastadas; ao ancorar, um roteador (A* numa grade) redesenha os barbantes contornando as ilhas.
- **Zoom/arrastar**, **minimapa**, **navegador de times** ("Ir para"), iniciativas recolhidas quando uma é selecionada — a menos que "Manter todas as iniciativas visíveis" esteja ligada (opção, desligada por padrão): aí a lista de Iniciativas continua mostrando todas as do filtro, com a selecionada em foco (borda destacada) e as demais sem foco (esmaecidas), para o usuário conseguir voltar e continuar analisando as próximas sem perder o lugar. Selecionar outra iniciativa move o foco sem recolher a lista de novo. Ver `docs/decisoes/0021-manter-iniciativas-visiveis.md`.
- **Etapas vazias** (opção, ligada por padrão) e **itens sem desdobramento** (opção, ligada por padrão).

## Filtros e busca

- Filtros: Roadmap executivo, Responsável (busca por qualquer parte do nome, múltipla escolha), Roadmap interno, Time (dinâmico: inclui times cadastrados sem carga), **ID ou descrição** (campo único — decisão `0034`).
- **ID ou descrição**: casa por ID exato ou por texto no título, em qualquer nível (iniciativa, release, épico ou item de time) — quem casa revela a cadeia inteira até a iniciativa (só o item casado, quando o match é num item de time dentro de um épico que não casou por si). Ao digitar, filtra ao vivo; no Enter, também tenta rolar/abrir o item, se a busca for um ID. Fica salvo como filtro ativo, igual aos demais, até ser limpo.
- Filtros ativos ficam destacados; "Limpar filtros (N)".
- **Diagnóstico de quadro vazio**: explica qual filtro zerou o resultado e quantas iniciativas aparecem sem cada um; para um ID que existe mas não aparece, diz se é cadeia inválida, regra de exibição ou outro filtro escondendo, com um botão para remover e ir até ele.

## Investigação por ID

Percorre as etapas e para na primeira que falhar: retornou nos dados (ou foi excluído como Removed, ou não veio da fonte) → reconhecido → cadeia válida / regra de exibição → filtros → recolhido.

## Painel de detalhes

Alertas com diagnóstico, medidor e "O que fazer"; resumo nos pais; campos; "Como o CT foi calculado" (épico); itens por categoria (épico); campos adicionais; rastreabilidade ("Por que está aqui"); link para o Azure DevOps.

## Visão analítica

Painel lateral (aba "Visão analítica") habilitado com Time + Roadmap. Tabela no formato do slide de roadmap do time, ordenável, com "Copiar tabela". Capacidade e Projetada, no cabeçalho, são sempre a soma dos números mostrados nas linhas dos épicos (nunca uma contagem à parte) e são clicáveis: abrem a lista dos itens exatos que compõem cada soma (ID, título, situação — Backlog, Discovery, WIP ou Vazão, com a data quando Vazão), cada um levando direto até o item no quadro. A linha do épico mostra, logo após a descrição, quantos dos seus itens estão reservados (tag de capacidade do roadmap); o QTD e o "reservado" de cada linha também são clicáveis, mostrando só os itens daquele épico (não o total da tabela). A coluna Status ganha uma linha com o mesmo agrupador por categoria (Backlog/Discovery/WIP/Vazão, com quadradinho colorido e contagem) já usado no card do épico no quadro. Regras em `docs/regras-de-negocio.md` §10; decisões `0027`, `0028` e `0029`.

## Report F4P

Painel lateral (aba "Report F4P", ao lado da Visão analítica) habilitado com Time + Roadmap; o filtro só habilita o acesso, o relatório sempre mostra todos os times carregados. Grade de 8 quadrantes em 2 colunas, com os selos de cada grupo e o logo do cabeçalho ilustrados com as imagens do slide de referência. **CycleTime** e **Variabilidade** têm regra calculada (P95/P50 do CT, interpolação linear); o período da amostra acompanha o semestre selecionado no filtro (semestre em curso: últimos N meses; já encerrado: só aquele período; futuro: painel desabilitado). **Urgente** conta itens de uma tag configurável (Classe de Serviço Expedite) contra uma meta por time, sempre no período exato do semestre selecionado (1º ao último dia), com seta de tendência (últimos 3 meses vs. os 3 anteriores); clicar no número do Realizado abre a lista dos itens considerados (ID, título, situação — categoria de fluxo do time: Backlog, Discovery, WIP ou Vazão), cada um levando direto até o item no quadro. **Technical Story** tem o mesmo comportamento do Urgente, mas conta itens desse tipo (não uma tag), a meta tem padrão 6 por time, sem tendência, e só entram no Realizado itens já **entregues** (categoria de fluxo Vazão) — itens em Backlog, Discovery ou WIP não contam, mesmo abertos há muito tempo. **Vazão** também conta só itens entregues no período (dos tipos configurados para o CT), mas mostra Reserva (subconjunto com a tag de capacidade do roadmap) vs. Realizado (todo o conjunto) sem cor nos números, com tendência pelo mês corrente somado aos itens hoje em WIP vs. a média (arredondada pra cima) dos meses anteriores do período — a seta da tendência é colorida (verde se Realizado ≥ Reserva, vermelho se menor) — e Reserva e Realizado clicáveis. **Roadmap – Épicos** é o único quadrante que opera sobre os cards do quadro de Épicos (não os itens dos times): Roadmap conta épicos dos tipos configurados (`CFG.f4p.epiTypes`, padrão Epic) com item do time vinculado, dentro do semestre selecionado — pelo Target Date do próprio épico (Roadmap Interno) ou pelo vínculo com a iniciativa via Release (Roadmap Executivo); Roadmap entregue é o subconjunto já fechado (última coluna do quadro de Épicos); Atual conta só pela data de fechamento dentro do período do semestre, independente do critério do Roadmap; tendência com a mesma regra do Vazão (mês corrente + épicos do Roadmap ainda abertos vs. média dos meses anteriores); os três números são clicáveis. **User Story** usa os mesmos critérios de "entregue" do Technical Story/Vazão, mas com uma lista de tipos própria (`CFG.f4p.usTypes`, padrão User Story): Planejado é o subconjunto com a tag de capacidade; Não planejado é o restante sem a tag — os dois juntos somam todo o entregue (partição, não sobreposição como no Vazão); tendência com a mesma regra do Vazão; Planejado e Não planejado clicáveis. Uma **conferência cruzada** verifica, por time, se Vazão Realizado = Technical Story Realizado + User Story Planejado + User Story Não planejado; quando a soma diverge (configuração de tipos inconsistente entre os três quadrantes), um aviso aparece no topo do painel com os números exatos. **Eficiência de fluxo** (último quadrante, `[MIN] | [Atual] [Tendência] | [MAX]`) soma, para todos os itens do fluxo do time no período (reaproveitando a janela do CycleTime/Variabilidade, não a exata do semestre), quanto tempo cada um passou em trabalho (touch time) e quanto passou numa fila de espera (waiting time, marcada por coluna em Configurações › Fluxo dos times, estilo "Fila de espera" — as colunas não marcadas contam como touch time automaticamente); Eficiência = Touch ÷ (Touch + Waiting) × 100, com cor verde dentro da faixa MIN–MAX configurável por time (padrão 30%–55%) e vermelha fora, tendência comparando os últimos 2 meses do período com o período inteiro, e o número clicável abrindo a lista dos itens com o touch/wait de cada um. Todos os 8 quadrantes têm regra fechada. Regras em `docs/regras-de-negocio.md` §12; especificação completa em `docs/backlog/report-f4p.md`; decisões em `docs/decisoes/0011` a `0031`.

## Higiene de dados

Relatório da carga do Azure (itens Removidos excluídos, vínculos divergentes), órfãos, épicos inválidos, releases sem iniciativa.

## Configurações

Duas abas — Azure DevOps (sempre acessível) e Configurações gerais (travada até a 1ª carga). Ver `docs/configuracoes.md`.

## Carga do Azure DevOps

Botão "Azure DevOps" (barra de ferramentas, ou o botão equivalente dentro da tela de primeiro acesso): pede tokens das organizações usadas, mostra o plano de execução (terminal), pede mapeamento de colunas antigas na primeira carga. Única forma de carregar dados no portal — ver `docs/integracao-azure.md` e a decisão `0032`.
