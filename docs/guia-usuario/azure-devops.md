# Conectar e carregar dados do Azure DevOps — guia do usuário

## O que é

O Azure DevOps é a **única fonte de dados** do portal — não existe mais upload de planilha. Esta tela
(Configurações › Azure DevOps) é onde você cadastra o acesso às organizações e diz de onde vêm
Iniciativas, Releases, Épicos e os times operacionais, e também de onde você dispara a carga (ou
atualização) dos dados.

## Como acessar

- Pelo botão "Azure DevOps" na barra de ferramentas, em qualquer momento.
- **Primeiro acesso**: sem nenhuma carga ainda guardada neste navegador, o portal abre **direto** nesta
  tela, forçada, sem opção de fechar — todo o resto da interface fica escondido até a primeira carga
  terminar com sucesso.

## Como funciona

### Conexões e fontes

- **Conexão** = uma organização do Azure DevOps. Só é adicionada se o teste de conexão passar (lista
  de projetos + uma consulta de teste ao Analytics) — um token errado nunca fica salvo como se fosse
  válido.
- **Fonte** = organização + projeto + time + nível de backlog, com um papel: **Iniciativa** (1),
  **Release** (1), **Coordenação de Épico** (1 ou mais) ou **Time operacional** (1 ou mais — cada um
  vira uma aba de time no portal, com o nome que você escolher como "nome no portal").
- A seção de fontes só aparece depois de pelo menos uma organização conectada na sessão. Fontes de
  organizações sem token no momento ficam bloqueadas, mas continuam cadastradas.

### Token: nunca é salvo

O token de acesso (PAT) **nunca é persistido em lugar nenhum** — não no `localStorage`, não no cache
local, não no arquivo de configuração exportado. Ele fica só em memória enquanto a aba do navegador
está aberta, e é pedido de novo a cada vez que você for carregar dados. Escopos necessários, só
leitura: *Work Items (Read)* e *Analytics (Read)*. Ver `docs/decisoes/0007-token-nunca-salvo.md` — é
uma regra não-negociável do projeto.

### Carregar os dados

Clicar em "Carregar dados do Azure DevOps" mostra o plano de execução em formato de terminal — cada
etapa marcada `[✓]` concluída, `[⠋]` em andamento, `[ ]` pendente, `[✗]` erro, `[–]` pulada. Por baixo,
o portal busca, para cada fonte: a área do time, os níveis/tipos do backlog, as colunas reais do
quadro, os IDs dos itens, os campos de cada um, os vínculos entre eles, e o histórico de passagem por
cada coluna (para calcular datas e CycleTime). Nada disso exige nenhuma configuração prévia de nomes de
coluna — o portal lê o fluxo **real** de cada quadro.

### Mapeamento de colunas antigas

Se o histórico de um item citar uma coluna que não existe mais no quadro atual (foi renomeada ou
removida), a carga não ignora essa informação silenciosamente — ela pode distorcer as datas calculadas
do CycleTime. Na primeira carga de uma fonte com esse caso, um diálogo pede para você dizer, para cada
nome antigo, a qual coluna atual ele corresponde (ou "Ignorar"). Essa escolha fica salva — não é pedida
de novo em cargas futuras da mesma fonte.

**Revisão depois da carga**: em Configurações › Azure DevOps, cada fonte com mapeamento salvo mostra um
botão "Mapeamento de colunas (N)" — expande uma tabela com o nome e a contagem de cada coluna antiga,
um seletor para reassociar a escolha (ou ignorar), e um botão para remover a entrada. Dá para corrigir
um mapeamento errado sem precisar refazer a carga do zero.

### Higiene de dados

Depois de carregar, um relatório mostra o que a carga encontrou de "estranho" nos dados — não são
erros do portal, são avisos sobre o que está cadastrado no Azure DevOps:

- Itens no estado **Removed**, excluídos da carga (continuam contabilizados só para referência).
- **Vínculos divergentes**: um item cujo campo de vínculo com o épico e o Remote Related apontam para
  épicos diferentes — nesse caso, vale o campo, e o item entra nesta lista como aviso.
- **Itens órfãos**: item de time vinculado a um épico que não existe nos dados carregados.
- **Épicos inválidos**: sem título, ou cujo Parent não é uma release carregada.
- **Releases sem iniciativa**: Parent não é uma iniciativa carregada.

## Perguntas frequentes ("não está batendo com o que eu esperava")

### "Fechei e abri o portal de novo, e ele pediu o token outra vez"

Esperado, sempre: o token nunca é salvo entre sessões, de propósito (ver "Token: nunca é salvo" acima).
Reabrir a página (mesmo com as fontes já cadastradas e salvas) sempre exige o token de novo antes de
qualquer carga.

### "Uma coluna do fluxo antigo apareceu pedindo mapeamento — o que eu faço?"

Diga a qual coluna **atual** do quadro aquele nome antigo corresponde (ex.: "Teste Done" → "Pronto
para Deploy") ou escolha "Ignorar" se ela não tiver equivalente relevante para o cálculo de datas. Se
perceber depois que escolheu errado, não precisa refazer a carga — corrija em Configurações › Azure
DevOps, no botão "Mapeamento de colunas (N)" da fonte.

### "Recebi o erro TF400497 ao carregar um time"

É um aviso de configuração de iteração do backlog inválida **naquele time**, do lado do Azure DevOps —
não um erro do portal. Escolha outro time ou corrija a configuração de iteração diretamente no Azure
DevOps.

### "Recebi 401 ou 403 ao testar a conexão"

Token inválido, expirado, ou sem os escopos necessários (*Work Items (Read)* e *Analytics (Read)*).
Gere um novo PAT com esses escopos e teste a conexão de novo.

### "Um item aparece na Higiene de dados como órfão, mas eu sei que ele está vinculado a um épico"

Confira se o épico que ele deveria referenciar foi realmente carregado como fonte (papel "Coordenação
de Épico") — um item só deixa de ser órfão se o épico do seu vínculo também estiver entre os dados
carregados, não só existir no Azure DevOps.

## Cenários

### Conexão só é salva se o teste passar

**Cenário de sucesso: token válido com os escopos certos**
- Dado um token com os escopos *Work Items (Read)* e *Analytics (Read)*
- Quando o usuário testa a conexão com uma organização
- Então a organização é adicionada à lista de conexões da sessão

**Cenário de comportamento inesperado: token inválido**
- Dado um token incorreto ou sem os escopos necessários
- Quando o usuário tenta testar a conexão
- Então a conexão não é salva — a lista de organizações continua sem ela

### Coluna renomeada pede mapeamento antes de aplicar a carga

**Cenário de sucesso: coluna mapeada corretamente**
- Dado o histórico de um item citando uma coluna fora do quadro atual
- Quando o usuário mapeia essa coluna para a coluna atual correspondente e confirma
- Então a carga aplica o mapeamento e as datas de CycleTime consideram a coluna antiga corretamente

**Cenário de comportamento inesperado: mapeamento ignorado silenciosamente (sem esta tela)**
- Dado o mesmo histórico citando uma coluna fora do quadro atual
- Quando não existisse a tela de mapeamento
- Então a coluna antiga seria ignorada ou mal interpretada, distorcendo as datas de CycleTime
  calculadas a partir dela — por isso o diálogo de mapeamento existe antes de aplicar a carga

## Regras de negócio relacionadas

- `docs/integracao-azure.md` (funcionamento completo da carga, chamadas feitas, regra de datas).
- `docs/regras-de-negocio.md` §1 (Hierarquia e vínculos), §2 (Validade), §11 (Higiene de dados).
- Decisões: [`0006`](../decisoes/0006-regra-de-datas-actionableagile.md) (regra de datas das
  colunas), [`0007`](../decisoes/0007-token-nunca-salvo.md) (token nunca salvo),
  [`0032`](../decisoes/0032-azure-devops-unica-fonte-de-dados.md) (única fonte de dados, gate do
  primeiro acesso), [`0033`](../decisoes/0033-filtro-boardid-e-revisao-de-mapeamento.md) (filtro por
  BoardId e revisão de mapeamento).
- Detalhe exaustivo de cobertura de teste: [`docs/testes/azure-devops.md`](../testes/azure-devops.md).
