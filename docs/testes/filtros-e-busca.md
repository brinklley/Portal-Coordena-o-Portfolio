# Testes: Filtros e busca

Cobre `tests/test_filtros.py` (7 testes). Desde a decisão `0034`, existe um único campo "ID ou
descrição" (`#fBusca`) — substituiu os antigos campos separados "Iniciativa (ID ou nome)" e "Ir para
qualquer ID". Ver `docs/telas.md`.

## Regra: filtro de responsável busca em qualquer parte do nome, sem acento

**Garante que**: o filtro multiseleção de responsável (`#fOwner`) encontra nomes buscando por
substring, ignorando acentuação (ex.: "conceicao" encontra "Conceição").

- **Dado**: fixture `responsaveis.xlsx`, busca "conceicao" no `#msSearch`.
- **Então (sucesso)**: todos os itens visíveis na lista contêm "Conceição"; selecionar "Todos"
  (`#msAll`) resulta em `S.f.owners.size` igual à contagem de itens filtrados.
- **Cenário de falha coberto**: uma busca sem acento não encontraria responsáveis com nome
  acentuado, obrigando o usuário a digitar o acento exato.
- **Teste**: `test_responsaveis_busca_em_qualquer_parte_do_nome`

## Regra: o campo único filtra por ID (qualquer nível) ou por texto (qualquer nível)

**Garante que**: digitar um ID de qualquer nível da hierarquia (iniciativa, release, épico ou item
de time) no campo único filtra o quadro para mostrar só a cadeia daquele ID; digitar um texto que só
bate com o título de um item de nível mais baixo (ex.: um item de time) também revela a cadeia dele
— diferente do campo antigo "Iniciativa", que só buscava por nome de iniciativa.

- **Dado**: `times.xlsx`, um ID de épico válido; ou o título de um item de time vinculado a um
  épico válido.
- **Quando**: preenche `#fBusca` com o ID do épico, ou com o título do item.
- **Então (sucesso)**: só a iniciativa dona da cadeia daquele ID/texto fica visível
  (`S.V.visIni`); `activeFilters().length === 1`; o campo ganha a classe `active`; para o caso de
  texto, `S.V.visOp` contém a chave do item encontrado.
- **Cenário de falha coberto**: um texto que batesse só com um item de time (não com nome de
  iniciativa) não encontraria nada, mesmo o item existindo nos dados carregados.
- **Testes**: `test_filtro_unico_por_id_de_epico_mostra_so_a_cadeia`,
  `test_filtro_unico_por_texto_busca_em_qualquer_nivel`
- **Relacionado**: decisão `0034-filtro-unico-id-ou-descricao.md`.

## Regra: um ID bloqueado por outro filtro ativo esvazia o quadro, com diagnóstico explicando o motivo

**Garante que**: se outro filtro ativo (ex.: responsável) já exclui o dono do ID digitado, o quadro
fica vazio — e o diagnóstico automático de "nenhum resultado" explica qual filtro está bloqueando,
em vez de um aviso separado do campo de busca.

- **Dado**: `responsaveis.xlsx`, filtro de responsável ativo (ex.: "guzzo"), e um ID de iniciativa
  cujo responsável não bate com o filtro.
- **Quando**: digita esse ID em `#fBusca` e pressiona Enter.
- **Então (sucesso)**: a mensagem em `#fmsg` cita "Responsável da iniciativa"; clicar no link de
  diagnóstico (`[data-diag^='show:']`) navega até o item mesmo assim (`S.path.ini` = o ID); o campo
  único continua como o único filtro ativo (`activeFilters().length === 1`), diferente dos outros
  filtros, que foram limpos.
- **Cenário de falha coberto**: o quadro ficaria vazio sem nenhuma explicação de qual filtro está
  escondendo o item buscado, obrigando o usuário a testar filtro por filtro manualmente.
- **Teste**: `test_ir_para_id_aponta_o_filtro_que_esconde`
- **Relacionado**: decisão `0034`.

## Regra: texto sem nenhuma correspondência mostra o estado vazio com diagnóstico

**Garante que**: um texto de busca que não bate com nada mostra a mensagem "Nenhum item" (não uma
tela em branco sem explicação).

- **Dado**: `responsaveis.xlsx`, `#fBusca = "texto que nao existe"`.
- **Então (sucesso)**: `.empty-state` contém "Nenhum item".
- **Cenário de falha coberto**: uma busca sem resultado deixaria o quadro simplesmente em branco,
  sem indicar se é um problema de filtro ou de dado inexistente.
- **Teste**: `test_diagnostico_quando_o_filtro_zera_o_quadro`

## Regra: limpar a busca desfaz a seleção/drill-down que a própria busca criou

**Garante que**: limpar o campo `#fBusca` (inclusive pelo "×" nativo do input) não só remove o
filtro, mas também desfaz a navegação (`S.path`) que o Enter da busca havia criado — o quadro volta
ao estado neutro, não fica preso mostrando só o que a busca tinha selecionado.

- **Dado**: `times.xlsx`, busca por um ID de épico com Enter (fixa `S.path.epi` e `S.f.q`).
- **Quando**: limpa o campo (`page.fill("#fBusca", "")`).
- **Então (sucesso)**: `S.f.q === ""`; `JSON.stringify(S.path) === "{}"`;
  `activeFilters().length === 0`.
- **Cenário de falha coberto** (bug relatado pelo usuário): limpar a busca tirava o filtro mas
  deixava o quadro preso mostrando só a iniciativa que a busca havia selecionado via Enter — o
  usuário via um quadro "vazio pela metade" sem entender por quê.
- **Teste**: `test_limpar_a_busca_desfaz_a_selecao_que_ela_criou`
- **Relacionado**: decisão `0035-limpar-busca-desfaz-selecao-que-ela-criou.md`.

## Regra: trocar a busca por outro ID também desfaz a seleção anterior

**Garante que**: a mesma correção da regra acima também se aplica ao trocar a busca (sem precisar
limpar primeiro) — digitar um novo ID, mesmo sem apertar Enter, já desfaz a seleção que o ID
anterior tinha criado.

- **Dado**: `times.xlsx`, dois IDs de épico válidos (`a`, `b`); busca `a` com Enter (fixa
  `S.path.epi = a`); depois preenche `#fBusca` com `b` sem Enter.
- **Então (sucesso)**: `JSON.stringify(S.path) === "{}"`; `S.f.q === b`.
- **Cenário de falha coberto**: trocar de busca manteria a navegação antiga ativa junto com o novo
  filtro de texto, misturando dois estados inconsistentes.
- **Teste**: `test_trocar_a_busca_por_outro_id_tambem_desfaz_a_selecao_anterior`
- **Relacionado**: decisão `0035`.

## Regra: ir para um ID fora da cadeia válida não aplica o filtro nem zera o quadro

**Garante que**: clicar num link de ID (ex.: o épico dentro da Visão Analítica) cujo alvo não existe
nos dados, ou existe mas está fora da cadeia válida (ex.: um épico órfão, sem release/iniciativa —
decisão `0036`), nunca aplica o ID como filtro "ID ou descrição" — esse filtro nunca teria resultado no
quadro, então aplicá-lo só trocaria o que o usuário já estava vendo por "Nada corresponde aos filtros".
Só um aviso informativo aparece (com um atalho para "Investigar por que não aparece"), sem mexer em
`S.f` nem no restante da tela.

- **Dado**: `f4p.xlsx` carregado, time CORE com Roadmap interno selecionado, um épico órfão (`valid:
  false`, sem release/iniciativa) cadastrado com um ID numérico, a Visão Analítica aberta mostrando
  esse épico com o aviso "OBS: SEM INICIATIVA e SEM RELEASE".
- **Quando**: clica no ID do épico dentro da Visão Analítica.
- **Então (sucesso)**: `S.f` continua byte a byte igual a antes do clique (`S.f.q` continua vazio); o
  aviso (`#fmsg`) cita "fora da cadeia válida" e traz o botão "Investigar por que não aparece".
- **Cenário de falha coberto** (bug relatado pelo cliente): o clique aplicava o ID como filtro "ID ou
  descrição", que nunca bate com nada no quadro para um épico órfão — o quadro, que podia estar
  mostrando conteúdo real, virava "Nada corresponde aos filtros", com dois avisos quase idênticos
  sobrepostos (o diagnóstico automático de `render()` e a mensagem da própria navegação), e o usuário
  precisava "Limpar filtros" para voltar ao que estava vendo.
- **Teste**: `test_ir_para_epico_orfao_nao_aplica_filtro_nem_zera_o_quadro`
- **Relacionado**: decisão [`0064`](../decisoes/0064-gotoid-nao-aplica-filtro-para-id-invalido.md).

## Regra: recarregar os dados preserva o filtro de Time, sem travar os painéis

**Garante que**: depois de uma nova carga (Azure DevOps "atualizar os dados", ou uma nova importação)
com o filtro de **Time** já selecionado, se aquele time ainda existir nos dados recarregados, o
`<select>` continua mostrando o time **e** `S.f.team` continua de fato preenchido com ele — os dois
nunca ficam dessincronizados. Selecionar um Roadmap (interno ou executivo) logo depois já habilita
Visão analítica, Report F4P e Actionable normalmente, sem precisar reselecionar o Time.

- **Dado**: `f4p.xlsx` carregado; filtro de Time = `CORE` (via `<select>`); recarrega os mesmos dados
  (`carregar()` de novo, simulando "atualizar os dados" do Azure DevOps); depois seleciona um Roadmap
  interno.
- **Então (sucesso)**: `<select>#fTeam` e `S.f.team` continuam `"CORE"` depois da recarga;
  `activeFilters().length === 2` depois de selecionar o Roadmap; `#anTab`, `#f4pTab` e `#actTab` ficam
  habilitados.
- **Cenário de falha coberto** (bug relatado pelo usuário): `fillTeamFilter()` preservava o valor do
  `<select>` de Time entre uma carga e outra, mas rodava **antes** do reset de `S.f` em
  `fillFilters()`, que zerava `S.f.team` por baixo — o `<select>` continuava mostrando o time
  selecionado, mas o estado interno não tinha mais nenhum time, então escolher um Roadmap em seguida
  não bastava para habilitar os painéis (eles exigem Time **e** Roadmap): o usuário via "1 filtro
  ativo" mesmo com o Time aparentemente selecionado na tela.
- **Teste**: `test_recarregar_dados_com_time_selecionado_nao_trava_os_paineis`
- **Relacionado**: decisão `0057-filtro-de-time-sincroniza-apos-recarga.md`.
