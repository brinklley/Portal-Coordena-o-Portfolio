# 0034 — Filtro único "ID ou descrição", substituindo Iniciativa e "Ir para qualquer ID"

## Contexto

O usuário pediu uma melhoria de UX: havia dois campos de busca separados nos filtros — "Iniciativa
(ID ou nome)", que filtrava o quadro mas só reconhecia ID ou nome de **iniciativa**, e "Ir para
qualquer ID", que navegava até qualquer nível (release, épico ou item de time) mas só por **ID
exato**, sem filtrar o quadro nem persistir como filtro ativo. Pediu para juntar os dois num único
campo que filtre por qualquer ID informado e também pela descrição do card, em qualquer nível.

Antes de implementar, perguntei duas coisas por ser uma mudança de comportamento visível: (1) o que
fazer quando o ID digitado for de release/épico/item de time — o usuário escolheu que isso também
vire um **filtro persistente** (aparece em "filtros ativos", pode ser limpo), em vez de só uma
navegação pontual; (2) o alcance da busca por texto — o usuário escolheu buscar o título em
**qualquer nível**, não só no de iniciativa.

## Decisões

1. **Um único campo** ("ID ou descrição", `#fBusca`), substituindo `#fIni` e `#goto` em
   `src/index.html`. Estado: `S.f.q` (era `S.f.ini`).
2. **`computeVisible()`** (`05-estado-e-calculos.js`) generaliza o casamento: para cada épico válido,
   casa o ID (exato) ou o texto (substring, sem acento/maiúsculas) contra iniciativa, release, épico
   e cada item de time. Quem casa no nível de iniciativa/release/épico revela a cadeia inteira
   (mesmo comportamento de antes para busca por iniciativa); quando só itens de time casam dentro de
   um épico que não casou por si, só esses itens aparecem na lista do épico (o filtro de Time já usava
   esse mesmo mecanismo de inclusão parcial). Itens sem desdobramento (releases sem épico, iniciativas
   sem release) seguem a mesma regra, no nível deles.
3. **`gotoId()`** (`12-investigacao.js`) passa a: (a) aplicar a busca como o filtro persistente
   (`setQueryFilter`) antes de qualquer coisa; (b) só tentar resolver/navegar quando a busca for
   numérica (`nid(q)` só dígitos) — texto livre só filtra, sem tentar "achar por ID" nem mostrar
   "ID não encontrado". Reaproveitada por todos os pontos que já usavam a função para "ver no quadro"
   (painel de detalhes, Visão analítica, Report F4P), que agora também aplicam o filtro ao navegar —
   consistente, e evita manter duas implementações de resolução de ID.
4. **Corrida entre dois avisos no mesmo `#fmsg`**: como `gotoId()` agora chama `render()` (via
   `setQueryFilter`) antes de checar se o item está visível, e o próprio `render()` já tinha um
   mecanismo automático que mostra o diagnóstico de "quadro vazio" via `requestAnimationFrame`
   quando o filtro zera o resultado (`06-renderizacao.js`), as duas coisas competiam pelo mesmo
   `#fmsg` — e o `requestAnimationFrame` (assíncrono) sempre vencia, sobrescrevendo a mensagem que
   `gotoId()` tentava mostrar. Como um ID específico, quando bloqueado por outro filtro, **sempre**
   zera o quadro inteiro (o próprio ID já restringe tudo ao seu redor — não sobra outra iniciativa
   pra mostrar), esse é o caminho mais comum, não um caso raro. Solução: `gotoId()` agora checa
   `S.V.visIni.size` logo após aplicar o filtro e, se o quadro ficou totalmente vazio, **não** mostra
   nada por conta própria — deixa o diagnóstico automático (`diagnoseEmpty`/`diagHtml`) explicar,
   já que ele roda de qualquer forma. `gotoId()` só mostra sua própria mensagem quando o quadro
   **não** fica vazio (outro item ainda visível) mas o alvo específico continua escondido — caso mais
   raro (ex.: coincidência de ID/texto entre itens de cadeias diferentes).
5. **`diagnoseEmpty()`/`diagHtml()`** (`11-filtros-e-diagnostico.js`) generalizados dos 4 tipos de
   diagnóstico (ID inválido/fora da cadeia, regra de exibição, escondido por outro filtro, texto sem
   resultado) para qualquer nível, não só iniciativa — reaproveitando `findAny()`/`resolvePath()`
   (novas, em `12-investigacao.js`) e a `blockingFilters()` já existente. O botão "Remover esse
   filtro e mostrar #ID" agora também navega até o item (chama `gotoId()` de novo depois de limpar
   os filtros bloqueadores), igualando o resultado ao antigo botão "Limpar filtros e ir" do `#goto`.

## Consequência aceita

Ir até um ID bloqueado por outro filtro (ex.: filtro de Responsável escondendo uma iniciativa) agora
sempre passa pelo diagnóstico de "quadro vazio" (com sua tela de "Nada corresponde aos filtros"),
em vez de um aviso pontual ao lado do campo — mudança de forma, não de informação: a mesma explicação
(quais filtros bloqueiam) e a mesma ação de um clique (remover e mostrar) continuam disponíveis.

## Testes

`tests/test_filtros.py`: `test_ir_para_id_aponta_o_filtro_que_esconde` atualizado para o novo fluxo
(diagnóstico automático em vez do aviso antigo ao lado do campo; o filtro "q" continua ativo depois
de navegar, ao contrário do comportamento anterior do `#goto`, que não deixava filtro nenhum). Dois
testes novos:
`test_filtro_unico_por_id_de_epico_mostra_so_a_cadeia` (ID de nível mais profundo filtra e persiste)
e `test_filtro_unico_por_texto_busca_em_qualquer_nivel` (texto que só bate com item de time também
filtra). Os testes que clicavam em links "ver no quadro" (Report F4P, Visão analítica) e checavam
`#goto` foram atualizados para `#fBusca`.
