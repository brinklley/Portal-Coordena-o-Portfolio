# 0040 — Board "Operacional dos times" aparecia por cima de Iniciativa/Release/Épico

## Contexto

O usuário reportou, com print, o board "Operacional dos times" (a seção de baixo do whiteboard, no
modo cadeia completa) aparecendo sobreposto aos boards de Release, Iniciativa ou Épico, em vez de
abaixo deles.

## Diagnóstico

Desmarcando "Ilhas ancoradas" (`#fAnchor`, ligado por padrão), o usuário pode arrastar livremente
cada ilha (`.island`, uma por time, dentro do board "Operacional") ou cada nível inteiro
(`.lane-inner.isle`) pelo whiteboard. Cada arrasto grava um deslocamento fixo em pixels a partir da
posição que o elemento tinha **naquele momento** (`S.offsets[chave] = {x, y}`, aplicado depois via
`style.left`/`style.top` em `applyOffsets()`).

O problema: esse deslocamento nunca era descartado quando os filtros, a busca (campo "ID ou
descrição") ou a iniciativa selecionada mudam — mesmo que essas mudanças alterem completamente a
altura das seções acima da ilha (menos épicos, menos releases, um único time filtrado em vez de
vários). Como o deslocamento é um número fixo de pixels, não uma posição relativa ao conteúdo, uma
ilha arrastada para cima enquanto o usuário via uma cadeia grande podia acabar posicionada em cima do
conteúdo de uma cadeia bem menor, vista depois — exatamente o comportamento do print.

Não consegui reproduzir o cenário exato do usuário (não tenho acesso aos dados reais nem ao histórico
de cliques da sessão dele), mas o mecanismo foi confirmado de ponta a ponta: gravar manualmente um
`S.offsets` grande o bastante e depois trocar de time realmente deixa uma ilha sobreposta às seções
de cima, e a mesma sobreposição desaparece com a correção abaixo. Como "Ilhas ancoradas" vem ligado
por padrão, isso só afeta quem solta e arrasta alguma ilha deliberadamente — mas é exatamente o tipo
de exploração natural nesse whiteboard, então vale a correção mesmo sem uma reprodução 1:1 do caso
real. Pediria para o usuário confirmar depois de usar em produção.

## Correção

`render()` (`06-renderizacao.js`) agora calcula uma assinatura do que molda a forma do quadro —
iniciativa selecionada (`S.path.ini`) e os filtros que mudam quais iniciativas/releases/épicos/itens
aparecem (`S.f.team`, `S.f.q`, `S.f.exec`, `S.f.int`, `S.f.owners`) — via `offsetsSig()`
(`05-estado-e-calculos.js`). Sempre que essa assinatura muda em relação ao render anterior, `S.offsets`
é limpo. Mudanças que não alteram o que aparece (ex.: "Mostrar etapas vazias") não mexem na
assinatura, então uma posição arrastada de propósito continua no lugar entre um render e outro,
contanto que o usuário não tenha mudado filtro, busca ou iniciativa.

## Testes

`tests/test_ilhas_e_cadeia_completa.py`:
- `test_offset_de_ilha_solta_e_descartado_quando_o_filtro_muda`: grava um deslocamento manual, troca
  o filtro de Time, confirma que `S.offsets` esvazia.
- `test_offset_de_ilha_solta_e_descartado_ao_trocar_de_iniciativa`: mesma checagem, trocando de
  iniciativa selecionada em vez de filtro.
- `test_offset_de_ilha_solta_persiste_entre_renders_sem_mudanca_de_contexto`: confirma que um
  re-render sem nenhuma dessas mudanças não descarta a posição arrastada — a correção é específica de
  mudança de contexto, não uma limpeza geral a cada render.
