# Testes: Integração com o Azure DevOps

Cobre `tests/test_azure.py` (6 testes) contra o Azure simulado (`tests/azure_simulado.py`). O Azure
DevOps é a única fonte de dados do portal (decisão `0032`) — ver `docs/integracao-azure.md` para o
funcionamento completo da carga. A maioria das outras suítes usa `carregar()` (`tests/conftest.py`),
que já passa pelo pipeline real de carga (`azRun()`) contra o simulado; este arquivo cobre só o que
`carregar()` não exercita.

## Regra: primeiro acesso força a tela de conexão

**Garante que**: sem nenhuma carga prévia (sem cache no IndexedDB), o portal não mostra o quadro —
abre direto em Configurações › Azure DevOps, com a aba Geral desabilitada até a primeira carga bem
sucedida.

- **Dado**: nenhum dado carregado ainda (estado de 1º acesso).
- **Quando**: a página abre.
- **Então (sucesso)**: `#cfgBg` visível, `.top`/`.viewport` (o quadro) escondidos, a aba
  `[data-cfgtab2="geral"]` desabilitada; um token errado não é salvo (`azCfgOf(DRAFT).orgs.length`
  continua 0); um token válido é aceito e passa a mostrar o papel/role da organização.
- **Cenário de falha coberto**: o portal mostraria o quadro vazio ou permitiria configurar a aba
  Geral antes de existir qualquer fonte de dados válida — a conexão só é salva se o teste de
  conexão passar.
- **Teste**: `test_conexao_so_e_salva_se_o_teste_passa`
- **Relacionado**: decisão `0032`; `docs/configuracoes.md`.

## Regra: a carga do Azure monta a hierarquia correta

**Garante que**: o pipeline de carga (queries ao Analytics + `/_apis/work/boards`) resulta na mesma
hierarquia Iniciativa → Release → Épico → itens de time que o resto do portal espera, incluindo os
tratamentos especiais: itens no estado "Removed" excluídos, e vínculo por `Parent` (não só por
Area Path) quando um time (ex.: DADOS) não segue o quadro de iniciativas.

- **Dado**: fixture `times.xlsx` carregada com `item_removido=True` (ativa um item extra em estado
  Removed na simulação).
- **Quando**: `carregar(page, "times.xlsx", item_removido=True)`.
- **Então (sucesso)**: iniciativas/releases/épicos batem com os IDs fixos da fixture; os 7 times
  aparecem, todos com itens; o item Removido some do modelo (`S.importNotes.azure.removedIds`
  contém `"op:99999"`); o vínculo por `Parent` do time DADOS é contabilizado
  (`S.importNotes.azure.byParent > 0`); o fluxo real do quadro do time DADOS termina em "Pronto",
  não em "Fechado" (nomes fixos não são assumidos).
- **Cenário de falha coberto**: a carga incluiria itens excluídos/cancelados no quadro, ou
  assumiria nomes de coluna fixos em vez do fluxo real de cada quadro.
- **Teste**: `test_carga_do_azure_monta_hierarquia_correta`
- **Relacionado**: decisão `0008` (fluxo real do quadro), `docs/integracao-azure.md`.

## Regra: colunas fora do quadro atual pedem mapeamento antes de aplicar a carga

**Garante que**: quando o histórico de um item cita uma coluna que não existe mais no quadro atual
(renomeada ou removida), a carga não aplica a mudança silenciosamente — abre um diálogo pedindo que
o usuário diga para qual coluna atual aquele nome antigo deve mapear.

- **Dado**: simulado com `coluna_antiga=True` (injeta uma revisão citando "Coluna Antiga", fora do
  quadro atual).
- **Quando**: `openAzureLoadModal()` → `#azGo`.
- **Então (sucesso)**: aparece `#azMapOk` com "Coluna Antiga" listada em `#azBody`; confirmar
  (`#azMapOk`) aplica a carga normalmente.
- **Cenário de falha coberto**: a coluna antiga seria silenciosamente ignorada ou mal interpretada,
  distorcendo as datas de CT calculadas a partir dela.
- **Teste**: `test_mapeamento_de_colunas_renomeadas`
- **Relacionado**: decisão `0033`; `docs/integracao-azure.md`.

## Regra: histórico "vazado" de outro board é filtrado por `BoardId`

**Garante que**: o histórico de um item (`BoardLocations`) pode legitimamente aparecer em mais de um
board quando a mesma Area Path é incluída em times diferentes — a carga filtra essas entradas pelo
`BoardId` do próprio board da fonte antes de decidir quais colunas pedem mapeamento e antes de
calcular as datas de cada coluna (CT). Sem esse filtro, colunas de outro time vazam para a tela de
mapeamento e podem contaminar as datas do CT se o usuário mapear uma delas por engano.

- **Dado**: simulado com `board_leak=True` (injeta, no histórico de um item do CORE, uma entrada de
  `BoardLocations` extra com `BoardId` de outro board fictício e nome de coluna genérico).
- **Quando**: `carregar(page, "times.xlsx", board_leak=True)`.
- **Então (sucesso)**: `L.boardId` foi lido (o id do próprio board); das 2 entradas de
  `BoardLocations` do item, só 1 é "própria" (`azOwnLocs`); a coluna vazada
  (`"outro-time-new"`) não aparece entre as pendentes de mapeamento (`azUnknown`); a carga completa
  sem travar no diálogo de mapeamento.
- **Cenário de falha coberto**: sem o filtro por `BoardId`, a carga travaria pedindo mapeamento para
  colunas que nunca existiram no board da fonte, e uma data errada poderia entrar no cálculo de CT.
- **Teste**: `test_board_leak_e_filtrado_por_boardid`
- **Relacionado**: decisão `0033`.

## Regra: mapeamento salvo pode ser revisto depois, sem nova carga

**Garante que**: depois de confirmar um mapeamento de colunas renomeadas, a escolha pode ser revista
e ajustada em Configurações › Azure DevOps a qualquer momento, sem precisar refazer a carga.

- **Dado**: uma fonte já carregada com `coluna_antiga=True` (gerou uma entrada em
  `CFG.azure.maps[fonte]`).
- **Quando**: abre Configurações › Azure DevOps, clica em "Mapeamento de colunas (1)", troca a
  associação no `<select>` e salva.
- **Então (sucesso)**: o botão mostra a contagem certa de mapeamentos; a tabela expandida mostra a
  coluna antiga ("Coluna Antiga"); a nova associação escolhida persiste em
  `azCfgOf(CFG).maps[fonte][id]` depois de `#cfgSave`.
- **Cenário de falha coberto**: antes desta função, não havia nenhum jeito de corrigir um mapeamento
  errado sem apagar tudo e recarregar do zero.
- **Teste**: `test_revisao_de_mapeamento_de_colunas`
- **Relacionado**: decisão `0033`.

## Regra: tokens do Azure nunca sobrevivem a uma reabertura

**Garante que**: o token de acesso não é persistido em nenhum lugar (nem `localStorage`, nem
IndexedDB) — só existe em memória (`AZ.tokens`) enquanto a aba está aberta. Reabrir a página (mesmo
com a configuração de fontes já salva) exige o token de novo.

- **Dado**: uma fonte configurada e salva (`CFG.azure.sources`), com um token em `AZ.tokens`.
- **Quando**: `page.reload()`.
- **Então (sucesso)**: `AZ.tokens` volta vazio; o diálogo de carga lista a organização pedindo o
  token de novo (`[data-azl-tok]`).
- **Cenário de falha coberto**: um token persistido sobreviveria a uma reabertura da página ou a uma
  exportação de configuração, expondo credencial fora do controle do usuário.
- **Teste**: `test_tokens_nao_sobrevivem_a_reabertura`
- **Relacionado**: decisão `0007-token-nunca-salvo.md` (regra não-negociável do projeto).
