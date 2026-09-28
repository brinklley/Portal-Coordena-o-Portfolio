# 0039 — Filtro "Responsável da iniciativa" ficava inutilizável com um painel lateral aberto

## Contexto

O usuário reportou: com a Visão analítica aberta, os filtros "Time" e "Roadmap interno" funcionavam
normalmente (o relatório recebia o novo valor), mas "Responsável da iniciativa" não — o clique nas
opções do popup simplesmente não fazia nada.

## Diagnóstico

"Time" e "Roadmap interno" são `<select>` nativos: o navegador desenha as opções por cima de
qualquer outro elemento da página, sem depender da pilha de `z-index` do CSS. "Responsável" é um
popup próprio (`#msPop`, dentro de `.ms`), sujeito às regras normais de empilhamento.

`#msPop` tem `z-index:45`. O painel da Visão analítica (`#anPanel`, mesma classe do Report F4P,
`.an-panel`) tem `z-index:46`. Isso por si só já explicaria o popup ficar embaixo do painel — mas o
problema real era mais sutil: `#msPop` é filho de `.top` (a barra de filtros), e `.top` tinha
`z-index:30`. Como `.top` é um elemento posicionado com `z-index` próprio, ele cria seu **próprio
contexto de empilhamento** — todo o conteúdo dentro dele, não importa o `z-index` que receba
internamente, fica limitado ao nível 30 quando comparado com elementos de fora de `.top` (como o
`#anPanel`, com z-index 46). Só subir o `z-index` do `#msPop` (como uma primeira tentativa chegou a
fazer) não resolvia nada, porque a comparação relevante acontece um nível acima, entre `.top` e
`#anPanel`.

Confirmado com Playwright: `Locator.click()` no popup falhava mesmo com o elemento "visível, habilitado
e estável", com o erro explícito "`<aside id=\"anPanel\">` subtree intercepts pointer events".

## Correção

`.top` passa a ter `z-index:47`, acima de `.an-panel`/`.f4p-panel` (46) e de `.side-tabs` (44,
os botões verticais de Visão analítica/Report F4P) — nenhum dos dois se sobrepõe normalmente à barra
de filtros, então a mudança não afeta a aparência em uso normal. `.fmsg` (48), `.drawer` (50),
`.toast` (60) e `.modal-bg` (70) continuam acima de `.top`, como já eram.

## Testes

`tests/test_visao_analitica.py::test_filtro_responsavel_utilizavel_com_o_painel_aberto`: abre a Visão
analítica e confirma que um clique numa opção do popup de Responsável realmente marca o filtro
(`S.f.owners.size == 1`) — falha (por timeout de clique interceptado) sem a correção.
