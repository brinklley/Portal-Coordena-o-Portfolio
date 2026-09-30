# 0050 — "+N ocultos": revelar irmãos escondidos pelo filtro ativo, sem limpar o filtro

## Contexto

O usuário reportou (com print de uma release selecionada, mostrando "1 épico" no card e um único
épico na faixa de Épicos abaixo) que, navegando pelo quadro com um filtro ativo, não tinha como saber
que existiam outros épicos vinculados àquela release — o filtro simplesmente os esconde, sem deixar
rastro. Pediu um controle minimalista: um texto pequeno tipo `[+] itens ocultos` que aparece só quando
há algo oculto naquele grupo, revela os itens escondidos "sem foco" (esmaecidos) ao clicar, e volta a
`[-] itens ocultos` pra esconder de novo — aplicável nos níveis Iniciativa, Release e Épico.

## Diagnóstico

`computeVisible()` (`src/js/05-estado-e-calculos.js`) constrói os Sets `visIni`/`visRel`/`visEpi`
olhando só pra frente: um item que não passa no filtro simplesmente nunca entra no Set, e o
renderizador (`render()`/`lane()`, `src/js/06-renderizacao.js`) usa só esses Sets pra montar a lista de
cards de cada faixa — não existe hoje nenhum conceito de "presente mas fora do filtro", só "visível" ou
"ausente". Os próprios badges dos cards (`nRel`/`nEpi` em `card()`) já contam só o subconjunto visível
(`it.rels.filter(id => V.visRel.has(id))`), então nem o número no card avisa que existe mais coisa.

## Decisão

**"Oculto pelo filtro" = visível sem filtro nenhum, mas ausente com o filtro atual.** Em vez de tentar
adivinhar qual filtro específico é o culpado, `computeVisible()` passou a aceitar um `f` opcional
(padrão `S.f`), e uma nova função `computeVisibleAll()` chama `computeVisible()` com todos os filtros
zerados — o Set resultante (`VAll`) é "como o quadro ficaria sem filtro nenhum". Um item que está em
`VAll` mas não em `V` (a visibilidade normal, com o filtro de verdade) é exatamente o que o usuário
pediu: algo que o(s) filtro(s) ativo(s) está(ão) escondendo, não algo que nunca apareceria de qualquer
jeito (épico inválido, sem itens, etc. — esses ficam de fora dos dois Sets).

`render()` calcula essa comparação só quando há filtro ativo (`activeFilters().length`, evita rodar
`computeVisible()` duas vezes à toa) e monta três listas de "ocultos": iniciativas (a faixa toda, que
não tem pai), releases (filhas da iniciativa selecionada) e épicos (filhos da(s) release(s) em foco —
funciona também no modo "Abrir cadeia completa", somando os ocultos de todas as releases visíveis).

`lane()` ganhou um parâmetro `hidden` — quando `S.showHidden[nivel]` está ligado, os itens ocultos
entram nas mesmas colunas de fluxo que teriam normalmente, junto dos visíveis, mas com `card(it, true)`
(novo segundo parâmetro `forceDim`, reaproveitando a classe `.dim` que a iniciativa fora de foco já
usa). A contagem do cabeçalho da faixa e as estatísticas continuam calculadas só sobre os itens
visíveis (`items`), sem incluir os revelados — só a coluna do grid ganha mais cards. Quando há algo
oculto, um botão `+N ocultos`/`− N ocultos` aparece no cabeçalho da faixa (`.hide-toggle`, CSS minúsculo,
mesmo peso visual do `.ctx` ao lado) — sem nada oculto, o botão não é renderizado.

`S.showHidden = {ini:false, rel:false, epi:false}` é uma preferência por nível, no mesmo padrão de
`S.showAllIni`/"Manter todas as iniciativas visíveis": fica ligada entre navegações, não é resetada ao
trocar de release/iniciativa — só some de vista quando o novo recorte não tem mais nada oculto.

### Card revelado: clicável, mas não navegável

Um card revelado está, por definição, fora de `V` (o Set que o filtro ativo produz). O guard existente
em `render()` (`if (S.path.epi && !V.visEpi.has(S.path.epi)) delete S.path.epi;`, e equivalentes pra
`rel`/`ini`) descarta qualquer seleção que não esteja no Set filtrado — então deixar o clique setar
`S.path` normalmente resultaria num clique "sem efeito" (o próprio `render()` desfaria a seleção no
mesmo ciclo). Em vez disso, o handler de clique (`09-interacao-e-responsaveis.js`) checa se o item
clicado está em `V` antes de decidir o que fazer: se não estiver, só chama `openDetail(key)` (o painel
de detalhes, que olha direto no modelo — `M.inis`/`M.rels`/`M.epis` —, sem depender de `V`), sem tentar
navegar.

## Testes

`tests/test_itens_ocultos_pelo_filtro.py` (8 testes): toggle ausente sem filtro ativo; aparece e
revela o oculto nos três níveis (Iniciativa/Release/Épico); contagem do cabeçalho não muda ao revelar;
toggle não aparece quando não há nada oculto naquele nível específico (mesmo com filtro ativo em outro
lugar); preferência de revelar persiste entre navegações; card revelado abre detalhes em vez de
navegar. Confirmei que os 6 testes que dependem do toggle falham (timeout esperando o elemento) contra
o código anterior a esta decisão, via `git stash`, antes de restaurar a correção.

Verificação visual via Playwright: release com 2 épicos (1 do time filtrado, 1 de outro time) —
"+ 1 ocultos" aparece, clique revela o 2º épico esmaecido na coluna certa do fluxo, com a linha de
conexão até a release, e o toggle vira "− 1 ocultos".
