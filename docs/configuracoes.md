# Configurações

Código: `src/js/01-configuracao-e-regras.js` (padrões e regras), `src/js/19-tela-configuracoes.js` (tela), `src/js/20-azure-conexoes-e-fontes.js` (seção Azure).
Testes: `tests/test_configuracoes.py`.

## Onde fica

- `localStorage["mapaPortfolio.config.v1"]` — objeto `CFG` (sem tokens).
- `IndexedDB "mapaPortfolioAzure"` — última carga do Azure.
- Tokens: somente em memória (`AZ.tokens`).
- **Exportar/Importar**: arquivo `.json` com o `CFG` (sem tokens). Importar converte formatos antigos (`normCfg`).

## Estrutura do `CFG` e padrões

| Chave | Padrão | Uso |
|---|---|---|
| `teams[time]` | `{}` | limites por time: `warn`, `max`, `out`, `stuck` (dias) |
| `warnDays`, `alertDays`, `outlierDays`, `stuckDays` | 30, 60, 90, 10 | regra geral para times sem CT máximo |
| `flow[time]` | `{}` | por time: `cat[coluna]` (none/disc/wip/vazao), `ct` (colunas do CT) e `time[coluna]` (touch/wait — marca a Fila de espera para o quadrante Eficiência de fluxo do Report F4P; sem marcação, a coluna é touch) |
| `ctCols`, `disc`, `wip`, `vazao` | `null` | formato antigo (único para todos os times); convertido ao salvar |
| `ctTypes` | user story, technical story, technical solution | tipos do CT do épico, QTD e capacidade |
| `tags` | BLOCKED, PAUSADO, URGENTE, DATA FIXA | tags cadastradas (nome, outros nomes, cor, nível, data) |
| `typeColors[nível][tipo]` | `{}` | cor da faixa do card por tipo |
| `fields[nível]` | `[]` | campos adicionais exibidos nos cards |
| `anTag`, `anClassCol`, `anFreeze` | ROADMAP, Classificação_Despesas_Comitê, 0 | visão analítica; `anTag` também é a tag de capacidade (Reserva) do quadrante Vazão do Report F4P |
| `f4p.months` | 6 | período (meses) da amostra do P95/P50 do Report F4P |
| `f4p.types` | user story, technical story | tipos considerados na amostra de CycleTime/Variabilidade e no Realizado/Reserva do quadrante Vazão do Report F4P |
| `f4p.epiTypes` | epic | tipos de **épico** (não de item de time) considerados pelo quadrante Roadmap – Épicos do Report F4P; configuração própria, independente de `f4p.types` |
| `f4p.usTypes` | user story | tipos considerados pelo quadrante User Story do Report F4P; configuração própria, independente de `f4p.types` e `f4p.epiTypes` |
| `f4p.effTypes` | `[]` (vazio = todos os tipos) | tipos considerados pelo quadrante Eficiência de fluxo do Report F4P; configuração própria — única do painel cujo padrão vazio significa "todos os tipos", em vez de cair num tipo fixo |
| `f4p.expediteTag` | urgent (id da tag URGENTE) | tag cadastrada que marca a Classe de Serviço Expedite, usada pelo quadrante Urgente |
| `f4p.teams[time]` | `{}` | por time: `min`/`max` da variabilidade esperada (padrão efetivo 1.5/3.5), `urgentMeta` (teto de itens Expedite no semestre; sem padrão), `tsMeta` (teto de itens Technical Story no semestre; padrão efetivo 6) e `effMin`/`effMax` da faixa de Eficiência de fluxo (padrão efetivo 30/55) |
| `azure.orgs` | `[]` | organizações (sem token) |
| `azure.sources` | `[]` | fontes: `id, role, org, project, team, level, alias, stages` |
| `azure.maps[fonte]` | `{}` | mapeamento de colunas antigas (`colunaId` ou `colunaId|Done` → coluna atual) |
| `azure.fields` | epic: ID_EPICO_UNICRED, roadmap: AnoSemestreRoadmap | nomes dos campos personalizados |
| `azure.excludeRemoved` | `true` | excluir itens no estado Removed |

## Validações ao salvar

- Por time: atenção < CT máximo < outlier; atenção ou outlier exigem CT máximo.
- Regra geral: atenção < atraso < outlier.
- Fluxo de cada time: pelo menos **duas** colunas em "Entra no CT"; as abas com problema ficam em vermelho.
- Report F4P: `min` e `max` da variabilidade de um time só valem preenchidos os dois juntos, e `min` < `max`. `urgentMeta` e `tsMeta` são independentes (podem ser preenchidos sem `min`/`max` nem um do outro), aceitam zero. `effMin`/`effMax` seguem a mesma regra da variabilidade: só valem preenchidos os dois juntos, com `effMin` < `effMax`.
- Com erro, nada é salvo e os valores digitados são preservados no formulário.

## Times listados na configuração

União dos times com dados carregados (planilha ou Azure) e dos cadastrados como fontes do Azure. **Times dos dados de exemplo não entram** (servem só ao quadro de demonstração).

## Botões do rodapé

- **Restaurar padrão**: volta regras (alertas, fluxo, tags, cores…) ao padrão; mantém conexões, fontes e dados.
- **Limpar tudo e reiniciar**: apaga configuração, conexões, fontes, mapeamentos, cache do Azure e tokens da sessão; recarrega como primeiro acesso. Oferece exportar antes.
