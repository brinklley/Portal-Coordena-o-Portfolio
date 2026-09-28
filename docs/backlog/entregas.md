# Entregas por PR

Histórico de entregas mergeadas neste repositório, levantado a partir das pull requests do GitHub
(todas mergeadas em `develop` ou `claude/tender-newton-ba5bty`). PR #2 ("Merge pull request #1...")
não é uma entrega própria — é o merge inicial de `claude/tender-newton-ba5bty` em `develop` — e por
isso não entra na tabela.

**Categoria**: 🆕 Nova funcionalidade · 🔧 Melhoria · 🐛 Correção (FIX). PRs com mais de uma
categoria mostram as duas, na ordem em que aparecem no PR.

| PR | Data | Categoria | Entrega | Decisões |
|---|---|---|---|---|
| [#1](https://github.com/brinklley/Portal-Coordena-o-Portfolio/pull/1) | 26/09 | 🆕 | Migração do projeto para este repositório (visualizador Iniciativa→Release→Épico→times, arquivo único sem servidor) + base do Report F4P (painel, Quadrantes 1–2 ainda incompletos, ilustrações, os demais 6 quadrantes como "em definição") | `0001`–`0013` |
| [#3](https://github.com/brinklley/Portal-Coordena-o-Portfolio/pull/3) | 26/09 | 🆕 | Report F4P: completa os Quadrantes 1 (CycleTime) e 2 (Variabilidade), com amostragem sensível ao semestre selecionado | `0011`–`0013` |
| [#4](https://github.com/brinklley/Portal-Coordena-o-Portfolio/pull/4) | 26/09 | 🆕 | Report F4P: Quadrante 3, Urgente (meta vs. realizado) | `0014` |
| [#5](https://github.com/brinklley/Portal-Coordena-o-Portfolio/pull/5) | 26/09 | 🐛 | Urgente: o Realizado somava itens de qualquer época (não só do período do relatório) | `0015` |
| [#6](https://github.com/brinklley/Portal-Coordena-o-Portfolio/pull/6) | 26/09 | 🐛🔧 | Urgente: número Realizado não ficava vermelho acima da meta (bug de especificidade CSS); Realizado passa a usar o período exato do semestre, não mais uma janela corrida (ajuste de regra depois de revisão em produção) | `0017` |
| [#7](https://github.com/brinklley/Portal-Coordena-o-Portfolio/pull/7) | 26/09 | 🆕🔧 | Report F4P: Quadrante 4, Technical Story (meta vs. realizado); lista de itens passa a mostrar a categoria de fluxo real (Backlog/Discovery/WIP/Vazão) em vez de só Aberto/Fechado | `0018`, `0019` |
| [#8](https://github.com/brinklley/Portal-Coordena-o-Portfolio/pull/8) | 26/09 | 🐛 | Technical Story: Realizado contava itens abertos há muito tempo; passa a contar só itens já entregues (Vazão) | `0020` |
| [#9](https://github.com/brinklley/Portal-Coordena-o-Portfolio/pull/9) | 26/09 | 🔧 | Quadro: opção "Manter todas as iniciativas visíveis" (com foco na selecionada), em vez de a lista sempre recolher na selecionada | `0021` |
| [#10](https://github.com/brinklley/Portal-Coordena-o-Portfolio/pull/10) | 26/09 | 🆕🔧 | Report F4P: Quadrante 5, Vazão (reserva vs. realizado); tendência passa a somar itens em WIP ao mês corrente | `0022`, `0023` |
| [#11](https://github.com/brinklley/Portal-Coordena-o-Portfolio/pull/11) | 26/09 | 🔧 | Vazão: seta de tendência ganha cor por Realizado vs. Reserva | `0024` |
| [#12](https://github.com/brinklley/Portal-Coordena-o-Portfolio/pull/12) | 26/09 | 🆕🔧 | Report F4P: Quadrante 6, Roadmap – Épicos (roadmap vs. entregue vs. atual); Visão analítica ganha Projetada/Capacidade como soma por épico com clique para ver itens, e perde o badge redundante "X US" | `0025`–`0028` |
| [#13](https://github.com/brinklley/Portal-Coordena-o-Portfolio/pull/13) | 26/09 | 🔧 | Visão analítica: coluna Status ganha o agrupador por categoria (Backlog/Discovery/WIP/Vazão) já usado no card do épico | `0029` |
| [#14](https://github.com/brinklley/Portal-Coordena-o-Portfolio/pull/14) | 26/09 | 🆕 | Report F4P: Quadrante 7, User Story (planejado vs. não planejado), com conferência cruzada contra Vazão/Technical Story | `0030` |
| [#15](https://github.com/brinklley/Portal-Coordena-o-Portfolio/pull/15) | 27/09 | 🆕 | Report F4P: Quadrante 8, Eficiência de fluxo (min vs. atual vs. max) — **completa os 8 quadrantes do Report F4P** | `0031` |
| [#16](https://github.com/brinklley/Portal-Coordena-o-Portfolio/pull/16) | 27/09 | 🆕 | Azure DevOps vira única fonte de dados (carga por planilha/CSV e dados de exemplo removidos); Configurações passa a ter 2 abas, com a aba Geral bloqueada até a primeira carga | `0032` |
| [#17](https://github.com/brinklley/Portal-Coordena-o-Portfolio/pull/17) | 27/09 | 🐛🔧 | Corrige colunas de outro board vazando no diálogo de mapeamento (filtro por `BoardId`); nova aba em Configurações para rever mapeamentos salvos | `0033` |
| [#18](https://github.com/brinklley/Portal-Coordena-o-Portfolio/pull/18) | 27/09 | 🔧 | Unifica os filtros "Iniciativa (ID ou nome)" e "Ir para qualquer ID" num único campo "ID ou descrição", que busca por ID ou texto em qualquer nível | `0034` |
| [#19](https://github.com/brinklley/Portal-Coordena-o-Portfolio/pull/19) | 27/09 | 🐛 | Limpar o campo de busca não desfazia a seleção/drill-down que a própria busca tinha criado | `0035` |
| [#20](https://github.com/brinklley/Portal-Coordena-o-Portfolio/pull/20) | 28/09 | 🔧 | Visão analítica passa a mostrar épicos sem release/iniciativa vinculada quando o filtro é por roadmap interno, com aviso "OBS: SEM INICIATIVA e SEM RELEASE" | `0036` |
| [#21](https://github.com/brinklley/Portal-Coordena-o-Portfolio/pull/21) | 28/09 | 🔧 | Campo "Dias antes do fim do semestre": texto de ajuda explica a fórmula completa do dead line (com exemplo numérico); padrão muda de 0 para 10 dias | `0037` |
| [#22](https://github.com/brinklley/Portal-Coordena-o-Portfolio/pull/22) | 28/09 | 🐛 | Corrige o layout do quadrante Eficiência de fluxo, que quebrava/sobrepunha com vários times — min/max passa para uma linha própria | `0038` |

## Por categoria

- **🆕 Nova funcionalidade** (9): #1, #3, #4, #7, #10, #12, #14, #15, #16 — mais a base do Report
  F4P e a mudança para Azure DevOps como única fonte de dados, as duas maiores entregas do período.
- **🔧 Melhoria** (11): #6, #7, #9, #10, #11, #12, #13, #17, #18, #20, #21 — a maioria refinamentos
  do Report F4P e da Visão analítica depois de o usuário revisar dados reais em produção.
- **🐛 Correção (FIX)** (6): #5, #6, #8, #17, #19, #22 — a maior parte também no Report F4P, quase
  sempre encontrada ao comparar o cálculo com dados reais de produção.

## Marcos

- **PR #15**: os 8 quadrantes do Report F4P completos (ver `docs/backlog/report-f4p.md`).
- **PR #16**: Azure DevOps como única fonte de dados — fim da carga por planilha/CSV.
