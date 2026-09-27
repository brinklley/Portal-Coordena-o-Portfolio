# Integração com o Azure DevOps

Código: `src/js/20-azure-conexoes-e-fontes.js`, `src/js/21-azure-carga.js`, `src/js/22-azure-janela-e-cache.js`.
Testes: `tests/test_azure.py` (contra `tests/azure_simulado.py`).

## Princípios

- **Única fonte de dados do portal** (decisão `0032`) — não há mais carga por planilha/CSV. Sem nenhuma carga guardada neste navegador, o portal abre forçado na tela de conexão (ver `docs/telas.md` § Primeiro acesso).
- **Sem servidor.** O navegador chama as APIs do Azure DevOps diretamente. `dev.azure.com` e `analytics.dev.azure.com` respondem com `Access-Control-Allow-Origin: *` e aceitam o cabeçalho `Authorization`, inclusive com a página aberta como arquivo local (origem `null`). Confirmado com HAR de uso real.
- **Token nunca é salvo** (ver `docs/decisoes/0007-token-nunca-salvo.md`): fica em `AZ.tokens`, só em memória. É pedido a cada abertura do portal, na hora de carregar. A exportação da configuração nunca leva tokens.
- **Escopos do PAT**, só leitura: *Work Items (Read)* e *Analytics (Read)*.

## Conexões e fontes

- **Conexão** = organização. Só é adicionada se o teste passar (`azTest`: lista de projetos + consulta ao Analytics).
- **Fonte** = organização + projeto + time + nível de backlog, com um papel:

| Papel | Quantidade | Vira a aba |
|---|---|---|
| Iniciativa | 1 | `INICIATIVA` |
| Release | 1 | `RELEASE` |
| Coordenação de Épico | 1 ou mais | `EPICO` (unificada) |
| Times operacionais | 1 ou mais | uma aba por time, com o "nome no portal" |

- A seção de fontes só aparece com pelo menos uma organização conectada na sessão. Fontes de organizações sem token ficam bloqueadas.
- Ao adicionar uma fonte operacional, as colunas do quadro são lidas e guardadas em `source.stages`, para configurar alertas e fluxo antes da primeira carga.

## Carga de uma fonte (`azLoadSource`)

Todas as chamadas usam `api-version=6.0`, lotes de 200 IDs e até 4 chamadas simultâneas (`azPool`), com repetição em 429/503.

| # | Etapa | Chamada |
|---|---|---|
| 1 | Área do time | `GET {org}/{projeto}/{time}/_apis/work/teamsettings/teamfieldvalues` |
| 2 | Níveis e tipos | `GET {org}/{projeto}/{time}/_apis/work/backlogs` |
| 3 | Colunas do quadro | `GET {org}/{projeto}/{time}/_apis/work/boards/{nível}/columns` |
| 4 | Campos personalizados | `GET {org}/_apis/wit/fields` (resolve nomes como `ID_EPICO_UNICRED` → `Custom.ID_EPICO_UNICRED`; a Classificação pode ter nome técnico em GUID) |
| 5 | Lista de itens | `POST {org}/{projeto}/_apis/wit/wiql?$top=20000` (Area Path da equipe + tipos do nível) |
| 6 | Campos atuais | `POST {org}/{projeto}/_apis/wit/workitemsbatch` |
| 7 | Links (só itens de time sem o campo e sem Parent) | `POST …/workitemsbatch` com `$expand: Relations` |
| 8 | Histórico do quadro | `GET analytics.dev.azure.com/{org}/{projeto}/_odata/v4.0-preview/WorkItemRevisions?$filter=WorkItemId in (…)&$expand=BoardLocations(…)` (segue `@odata.nextLink`) |

A tela de carga mostra o plano completo em formato de terminal: `[✓]` concluída (resultado e tempo), `[⠋]` em andamento (lote), `[ ]` pendente, `[✗]` erro, `[–]` pulada.

## Datas das colunas: regra validada

Validada contra a exportação da ActionableAgile (CORE, 2.469 itens): 100% nos itens que só andaram para a frente; ~92–96% no total. Decisão: `docs/decisoes/0006-regra-de-datas-actionableagile.md`.

1. Só contam as colunas do **quadro atual**, identificadas pelo **ID** (colunas renomeadas mantêm o ID).
2. A primeira coluna recebe a **data de criação** do item.
3. Vale a **primeira entrada** em cada coluna.
4. Colunas puladas herdam a data da **próxima** coluna em que o item entrou.
5. Quando o item **volta** para uma coluna anterior, as datas das colunas à frente são apagadas (recebem novas datas ao avançar de novo).
6. A parte **Done** de uma coluna que deixou de ser dividida vai, por padrão, para a coluna seguinte (ex.: "Teste Done" → "Pronto para Deploy").
7. Colunas de quadros antigos ficam **ignoradas** por padrão. Na primeira carga de cada fonte, o usuário pode mapeá-las; o mapeamento fica em `CFG.azure.maps[fonte]`.

Diferenças residuais conhecidas: itens que saíram do quadro e voltaram ao Backlog; mapeamentos manuais de colunas antigas diferentes dos da ActionableAgile.

## Montagem dos dados

- Cada fonte vira uma "aba" no formato interno usado por `buildModel` (`azSheet`), com o fluxo real (`flow: {start, end, keys}`).
- Itens no estado **Removed** são excluídos (opção configurável); os IDs ficam em `importNotes.azure.removedIds` para a investigação por ID.
- Vínculo do item de time com o épico: campo → Parent (se for épico carregado) → Remote Related.
- `Blocked` vem da tag Blocked; `Blocked Days` é contado pelo histórico de tags.
- Link de cada item: `https://dev.azure.com/{org}/{projeto}/_workitems/edit/{id}`.

## Cache local

Os dados montados (abas, rótulo, notas) ficam no IndexedDB `mapaPortfolioAzure` (chave `ultima`). Ao abrir, o portal mostra a última carga sem precisar de token. Nunca guarda tokens. "Limpar tudo e reiniciar" apaga o banco.

## Erros conhecidos

- **TF400497** (configuração de iteração do backlog inválida no time): tratado como aviso; escolher outro time ou corrigir no Azure.
- **401/403**: token inválido ou sem escopo.

## Limitações atuais

Ver `docs/backlog/pendencias.md` (carga incremental, IDs repetidos entre organizações, entre outras).
