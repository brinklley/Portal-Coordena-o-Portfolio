# 0033 — Filtro por BoardId nas colunas do histórico; revisão do mapeamento em Configurações

## Contexto

O usuário reportou, com prints da tela "Colunas renomeadas ou removidas", a sensação de que ela
mostra colunas que não pertencem ao board sendo carregado: nomes genéricos como "New"/"Closed"/
"Active" repetidos várias vezes, com contagens grandes e diferentes, para uma fonte cujo board real
("FL2 - Portfolio de Iniciativas UBR") nunca teve colunas com esses nomes. Pediu duas coisas: (1)
investigar se essas colunas realmente pertencem ao board da fonte ou se há vazamento/duplicação de
colunas de outro board; (2) uma forma de revisitar e ajustar o mapeamento depois de salvo — hoje, uma
vez clicado "Salvar mapeamento e montar o quadro", não existe mais nenhum lugar para voltar nessa
escolha.

## Diagnóstico

`azUnknown()` e `azDates()` (`src/js/21-azure-carga.js`) processam **todo** o `BoardLocations` de cada
revisão do Analytics (`WorkItemRevisions`), sem filtrar por board/time. A query nunca pedia nem
filtrava pelo campo `BoardId` dessa entidade.

Pesquisei a documentação oficial da entidade `WorkItemBoardLocation` do Analytics (via busca —
`learn.microsoft.com` está bloqueado neste ambiente para leitura direta; usei o espelho em
`raw.githubusercontent.com/MicrosoftDocs/azure-devops-docs`) e confirmei que ela tem os campos
**`BoardId`** e **`BoardName`**: o histórico de um item pode legitimamente aparecer em mais de um
board, porque a mesma Area Path pode estar incluída na configuração de mais de um time
simultaneamente. Isso bate com o sintoma relatado: nomes padrão de processo sem customização
(New/Active/Closed) repetidos várias vezes com contagens grandes e distintas é o padrão esperado de
**colunas vazadas de outros times** cujo board nunca foi customizado — não de um único board
reconfigurado repetidas vezes (que, ao contrário, consolidaria sob poucos `ColumnId`s com vários
nomes históricos).

Isso não é só cosmético: `azDates()` usa a mesma fonte (`BoardLocations`) para calcular as datas de
cada coluna do CT. Um usuário que mapeasse manualmente uma dessas colunas "fantasma" para uma coluna
real, pensando ser uma renomeação legítima do próprio board, injetaria datas erradas no cálculo do
Cycle Time.

**Limite honesto desta correção**: não há como testar contra uma organização real do Azure DevOps
neste ambiente. O diagnóstico é o mais provável dado o sintoma relatado e a documentação oficial da
entidade, e a correção foi validada com um cenário simulado equivalente (`board_leak` em
`tests/azure_simulado.py`), mas **pede confirmação do usuário no ambiente real** antes de ser
considerada definitivamente resolvida.

## Decisões

1. **Buscar o id do próprio board da fonte.** `azLoadSource()` já chamava
   `GET .../_apis/work/boards/{nível}/columns` (aceita nome amigável como `{nível}`); adicionei uma
   chamada irmã sem `/columns`, que retorna o objeto do board incluindo seu `id` — guardado em
   `L.boardId`. Se a chamada falhar por qualquer motivo, a carga segue **sem** o filtro (mais
   tolerante do que travar a fonte inteira por causa disto): `!L.boardId || b.BoardId === L.boardId`.
2. **Pedir `BoardId` na query do Analytics**: `$expand=BoardLocations($select=ColumnId,ColumnName,Done,LaneName,BoardId)`.
3. **Um único ponto de filtro, `azOwnLocs(L, v)`**, usado tanto em `azUnknown()` (o que entra na tela
   de mapeamento) quanto em `azDates()` (o que entra no cálculo do CT) — não duplica a regra em dois
   lugares.
4. Isso **reduz** o volume de colunas na tela de mapeamento; colunas genuinamente do próprio board
   (renomeadas de verdade) continuam aparecendo normalmente.

### Revisão do mapeamento depois de salvo

`CFG.azure.maps[fonte][id]` guardava só a decisão (chave da coluna atual, ou `""` para Ignorar), sem
nome nem contagem — não dava para mostrar nada útil numa tela de revisão. Acrescentei
`CFG.azure.mapMeta[fonte][id] = {names, n}`, escrito por `azMapFor()` a cada carga (reaproveita os
mesmos dados que `azUnknown()` já calcula, só passa a guardá-los).

Em Configurações › Azure DevOps, cada fonte com mapeamento salvo ganhou um botão "Mapeamento de
colunas (N)" que expande uma tabela editável: coluna do histórico (nome e contagem, via `mapMeta`),
um seletor para reassociar a uma coluna atual do quadro (busca as colunas ao abrir, via a mesma
`azStages()` já usada ao cadastrar uma fonte operacional) e um botão para remover a entrada. Segue a
mesma convenção do resto da tela: edita o rascunho (`DRAFT.azure.maps`/`mapMeta`) e só aplica de
verdade ao clicar em "Salvar" — não é uma ação separada com efeito imediato.

## Testes

- `tests/azure_simulado.py`: cada quadro simulado ganha um `board_id` estável; toda entrada de
  `BoardLocations` simulada carrega o `BoardId` do seu próprio board; o endpoint
  `GET .../_apis/work/boards/{nível}` (sem `/columns`) passou a ser simulado, devolvendo esse id.
  Novo cenário opcional `board_leak=True` (mesmo padrão de `item_removido`/`coluna_antiga`, exige
  `TIME CORE` na fixture): injeta, no histórico do primeiro item do CORE, uma entrada extra de
  `BoardLocations` com um `BoardId` diferente (fictício) e `ColumnName` genérico ("New").
- `tests/test_azure.py::test_board_leak_e_filtrado_por_boardid`: confirma que `L.boardId` foi lido,
  que a entrada vazada está presente em `BoardLocations` mas ausente de `azOwnLocs()`, e que não
  aparece em `azUnknown()`. Como `carregar()` chama `azRun()` sem o passo de clicar no diálogo de
  mapeamento, esse teste já travaria/expiraria sozinho se o filtro estivesse quebrado ou ausente.
- `tests/test_azure.py::test_revisao_de_mapeamento_de_colunas`: com o cenário `coluna_antiga`, salva
  um mapeamento pela tela de carga, abre Configurações › Azure DevOps, confirma que o botão
  "Mapeamento de colunas (1)" aparece, troca a associação pela tabela de revisão, salva e confirma
  que persistiu em `CFG.azure.maps`.

## Pendências

- Confirmar no ambiente real do Azure DevOps que o vazamento de `BoardLocations` de outros times era
  de fato a causa da tela de mapeamento mostrando colunas inesperadas, e que o filtro por `BoardId`
  resolve o sintoma relatado.
