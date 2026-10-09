# 0064 · `gotoId()` não aplica o filtro "ID ou descrição" para um ID inexistente ou fora da cadeia válida

**Contexto.** O cliente reportou: clicar no link do ID de um épico dentro da Visão Analítica — um
épico sem release/iniciativa vinculada (épico órfão, decisão `0036`, que a Visão Analítica mostra com
o aviso "OBS: SEM INICIATIVA e SEM RELEASE" quando filtrando por roadmap interno) — quebra o design do
whiteboard e deixa a tela "tremendo". Reproduzido com Playwright (fixture `f4p.xlsx`, time CORE com
conteúdo real no quadro, um épico órfão inserido com ID numérico, Visão Analítica aberta): o clique no
ID do épico não causa um laço de animação (nenhum aviso de `ResizeObserver`, nenhum erro de console,
nenhuma chamada repetida), mas produz um resultado bem pior do ponto de vista do usuário — o conteúdo
real que estava no quadro **desaparece**, substituído por "Nada corresponde aos filtros", com **dois**
avisos quase idênticos sobrepostos (o diagnóstico automático de `render()`, inline no quadro, e um
segundo popup flutuante agendado um quadro de animação depois). Essa troca abrupta de um quadro cheio
de conteúdo para uma tela vermelha de erro duplicada, junto da pequena defasagem de um frame entre os
dois avisos aparecerem, é o que o usuário descreveu como "tremendo a tela".

**Diagnóstico.** `gotoId()` (`src/js/12-investigacao.js`) chamava `setQueryFilter(q)` **antes** de
checar se o ID buscado sequer existe (`findAny`) ou resolve numa cadeia válida (`resolvePath`).
`setQueryFilter` aplica `q` como o filtro "ID ou descrição" (persistente, decisão `0034`) e já
renderiza o quadro com ele. Para um ID que não existe, ou que existe mas está fora da cadeia válida
(nenhum release/iniciativa — o próprio caso que a decisão `0036` passou a aceitar **só** na Visão
Analítica, nunca no quadro), esse filtro **nunca** vai casar com nada: o quadro inteiro zera. Como
consequência, a checagem seguinte em `gotoId()` (`if (!V.visIni.size) return;`) sempre disparava
primeiro nesses dois casos — o código mais específico logo abaixo (`!found`/`!path`, com a mensagem
certa via `showFmsg`) nunca era alcançado, virando efetivamente código morto. Quem explicava o quadro
vazio, então, era só o diagnóstico automático de `render()` (`S.emptyDiag`/`diagHtml`, agendado via
`requestAnimationFrame` especificamente para a busca ao vivo por texto, decisão `0034`) — que, por
coincidência, usa a mesma função `diagHtml()` e produzia um texto parecido com o que `gotoId()` teria
mostrado, só que **a mais**, sobre o conteúdo que já estava na tela, e com um frame de atraso.

**Decisão.** `gotoId()` passa a resolver `findAny`/`resolvePath` **antes** de chamar
`setQueryFilter(q)`, só para um `q` que é puramente numérico (texto livre continua aplicando o filtro
direto, decisão `0034` inalterada):

- **ID não encontrado nos dados** ou **encontrado mas fora da cadeia válida** (sem release/iniciativa)
  → mostra só o aviso informativo (`showFmsg`, com o atalho "Investigar por que não aparece") e
  **retorna sem tocar em `S.f` nem chamar `render()`** — o quadro e os filtros ativos continuam
  exatamente como estavam.
- **ID encontrado e com cadeia válida** → comportamento inalterado: aplica o filtro, verifica se algum
  outro filtro ainda esconde o resultado (mostrando qual, com a opção de limpar) e navega até o item.

**Consequências.** Clicar num link de ID inválido (épico órfão, item removido, ID digitado errado)
nunca mais descarta o que o usuário estava vendo no quadro — só avisa. `tests/test_filtros.py` ganhou
`test_ir_para_epico_orfao_nao_aplica_filtro_nem_zera_o_quadro`, reproduzindo o cenário relatado
(épico órfão + Visão Analítica aberta) e confirmando que `S.f` não muda. `docs/regras-de-negocio.md`
§3.1 documenta a regra.
