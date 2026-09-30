# Testes: "+N ocultos" — revelar irmãos escondidos pelo filtro ativo

Cobre `tests/test_itens_ocultos_pelo_filtro.py` (8 testes). Regras de negócio: §3.2. Decisão `0050`.

Com algum filtro ativo (Time, Roadmap, Responsável, ID/descrição), um card visível pode ter irmãos
(mesmo pai) que o filtro esconde sem deixar rastro. Um botão pequeno `+N ocultos` no cabeçalho da
faixa de Iniciativas, Releases ou Épicos avisa quando isso acontece e permite revelar os ocultos
esmaecidos (`.dim`), sem precisar limpar o filtro.

## Regra: sem filtro ativo, nenhum toggle aparece

**Garante que**: `[data-hide-toggle]` não existe em nenhuma faixa quando `S.f` está todo vazio — sem
filtro, `computeVisible()` e `computeVisibleAll()` são idênticos, então não há nada "oculto pelo
filtro" a avisar.

- **Teste**: `test_sem_filtro_ativo_nenhum_toggle_aparece`

## Regra: o toggle aparece e revela o épico escondido pelo filtro de Time

**Garante que**: uma release com dois épicos, um com item do time filtrado e outro só com item de
outro time — o segundo some da faixa de Épicos, mas o toggle `+ 1 ocultos` aparece e, ao clicar,
revela o card esmaecido (`.dim`), com o `data-key` certo. Clicar de novo esconde.

- **Dado**: release com `EPI_H1` (item do time filtrado) e `EPI_H2` (item de outro time), filtrando
  por Time = o time de `EPI_H1`.
- **Então (sucesso)**: toggle mostra `+ 1 ocultos`; 1 card visível. Clique → `− 1 ocultos`; 2 cards
  (1 normal + 1 `.dim` com `data-key="epi:EPI_H2"`). Clique de novo → volta a 1 card, sem `.dim`.
- **Cenário de falha coberto**: o usuário via só 1 épico na release e não tinha como saber que existia
  um segundo, escondido pelo filtro de Time — precisava limpar o filtro pra descobrir.
- **Teste**: `test_toggle_aparece_e_revela_epico_oculto_pelo_filtro_de_time`

## Regra: a contagem do cabeçalho da faixa não muda ao revelar

**Garante que**: o número ao lado do nome da faixa (ex.: "Épicos 1") continua contando só os itens que
passam no filtro — revelar os ocultos não infla essa contagem nem as estatísticas da faixa.

- **Teste**: `test_contagem_do_cabecalho_nao_conta_os_revelados`
- **Cenário de falha coberto**: o cabeçalho passaria a mostrar "Épicos 2" com o toggle ligado, dando a
  entender (incorretamente) que o filtro deixou de valer.

## Regra: mesmo mecanismo nos níveis Release e Iniciativa

**Garante que**: o toggle funciona igual um nível acima (uma release inteira escondida por não ter
nenhum épico com item do time filtrado) e no topo da hierarquia (uma iniciativa inteira escondida pelo
mesmo motivo) — não é uma regra só do nível Épico.

- **Teste (Release)**: `test_toggle_revela_release_oculta_pelo_filtro_de_time`
- **Teste (Iniciativa)**: `test_toggle_revela_iniciativa_oculta_pelo_filtro_de_time` — não fixa a
  contagem exata do toggle (a faixa de Iniciativas não tem "pai" só da cadeia sintética do teste, e o
  próprio fixture real pode ter outras iniciativas sem item do time filtrado); confirma só que a
  iniciativa oculta específica aparece esmaecida ao revelar.

## Regra: o toggle não aparece quando não há nada oculto naquele nível específico

**Garante que**: um filtro pode estar ativo e mesmo assim não esconder nada numa faixa específica — o
toggle daquela faixa não aparece "por via das dúvidas" só porque existe um filtro ligado em algum
lugar.

- **Dado**: uma release com um único épico, cujo único item já é do time filtrado — nada fica de fora
  nem no nível Release nem no nível Épico.
- **Então (sucesso)**: nenhum `[data-hide-toggle]` nas faixas de Release e Épico.
- **Cenário de falha coberto**: o toggle apareceria sempre que qualquer filtro estivesse ativo em
  qualquer lugar, mesmo sem nada para revelar ali — ruído visual desnecessário, indo contra o pedido
  explícito de "caso não tenha opções ocultas não deve mostrar a opção".
- **Teste**: `test_toggle_nao_aparece_quando_nao_ha_nada_oculto_naquele_nivel`

## Regra: a preferência de revelar fica ligada entre navegações

**Garante que**: `S.showHidden[nivel]` é uma preferência (mesmo padrão de `S.showAllIni`/"Manter todas
as iniciativas visíveis"), não um estado amarrado à release/iniciativa em foco no momento — trocar de
release mantém a preferência ligada, e os ocultos da nova release já aparecem revelados, sem precisar
clicar de novo.

- **Teste**: `test_preferencia_de_revelar_fica_ligada_entre_navegacoes`
- **Cenário de falha coberto**: cada navegação resetaria a preferência, obrigando o usuário a clicar
  "+N ocultos" de novo toda vez que trocasse de release/iniciativa.

## Regra: card revelado é clicável, mas abre detalhes em vez de navegar

**Garante que**: clicar num card revelado (fora do filtro ativo) abre o painel de detalhes
(`openDetail`, que olha direto no modelo, sem depender de `V`) em vez de tentar "entrar" nele — entrar
setaria `S.path` para um id fora de `V`, que o guard existente em `render()` descartaria de novo (o
filtro continua excluindo aquele item), deixando o clique sem efeito visível nenhum.

- **Então (sucesso)**: `S.path.epi` continua `null`; `S.detailKey` vira `"epi:EPI_H2"`; o painel de
  detalhes abre (`body` ganha a classe `with-drawer`).
- **Cenário de falha coberto**: sem esse cuidado, o clique pareceria não fazer nada (o guard de
  `render()` desfaria a seleção no mesmo render), confundindo mais do que ajudando.
- **Teste**: `test_card_oculto_revelado_abre_detalhes_em_vez_de_navegar`
