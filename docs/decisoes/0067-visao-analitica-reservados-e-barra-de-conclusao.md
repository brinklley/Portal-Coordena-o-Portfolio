# 0067 · Visão analítica: "Capacidade" vira "Reservados" + barra de conclusão por número

## Contexto

O usuário pediu duas mudanças no cabeçalho da Visão analítica (`docs/regras-de-negocio.md` §10),
anexando um print do painel com a linha "Entregas previstas: Capacidade 29 US / Projetada 49 US"
anotada:

1. Trocar o termo **"Capacidade"** por **"Reservados"** no rótulo exibido ao usuário.
2. Logo abaixo dessa linha, mostrar visualmente **quanto já foi entregue** de cada um dos dois
   números (Reservados e Projetada) — uma barra de progresso com a porcentagem, calculada como
   "quantos dos itens daquela soma já estão com status entregue". Exemplo dado pelo usuário: se
   Reservados é 10 itens e 2 já estão entregues, a barra mostra 20% preenchido.

## Decisões

1. **Renomeação, só o rótulo exibido.** O código já usava internamente o nome `reservados` para esse
   mesmo subconjunto (`itens.filter(hasTag)`, `src/js/15-visao-analitica.js`) e a linha de cada épico
   já mostra "N reservado(s)" — "Capacidade" era, na prática, o único lugar do painel que usava um
   termo diferente para o mesmo conceito. Trocar o rótulo do cabeçalho para "Reservados" alinha os
   dois níveis (cabeçalho e linha) sem precisar de nenhuma decisão nova de cálculo.
   Os campos internos (`d.cap`, `row.reservados`, `CFG.anTag`, `data-an-items="cap"`) **não** mudaram
   de nome — é puramente cosmético, renomear tudo internamente só aumentaria o diff sem nenhum
   ganho (e arriscaria confundir com `CFG.anTag`, que já se chama "tag de capacidade do roadmap" em
   outro sentido: a tag que marca um item como reservado, não o rótulo da UI).
   Atualizado em todo lugar que o texto "Capacidade" aparecia como esse mesmo rótulo visível ao
   usuário: o `<h3>` do painel, o título do modal de itens, a nota de rodapé da tabela, a ajuda do
   campo em Configurações › Visão analítica, `docs/regras-de-negocio.md` §10, `docs/telas.md`
   (Visão analítica e a referência cruzada no Actionable) e `docs/guia-usuario/visao-analitica.md`.
   Textos que usam "capacidade" como conceito genérico (ex.: "tag de capacidade do roadmap",
   `docs/configuracoes.md`, decisões antigas como `0048`) não foram tocados — não são o rótulo sendo
   renomeado, e editar decisões históricas (`docs/decisoes/`) não documentaria nada de novo.

2. **Barra de conclusão, calculada com o mesmo critério de "entregue" já usado em todo o portal.**
   `anData()` já expõe `capItems`/`projItems` (os itens exatos somados em cada número, usados pelo
   modal de transparência). A barra usa exatamente esses mesmos conjuntos, filtrando por
   `catOf(o) === "vazao"` — o mesmo critério usado pela coluna Status (`allVazao`), pelo Report F4P e
   pelo Actionable para decidir se um item está entregue. `anData()` ganhou dois campos novos,
   `capDone`/`projDone` (contagem de itens de `capItems`/`projItems` já em Vazão), para que o cálculo
   siga a mesma fonte única já estabelecida pela decisão `0027` (o número do cabeçalho é sempre
   derivado dos itens, nunca uma contagem à parte).
   Percentual arredondado (`Math.round`), igual ao padrão já usado no zoom do quadro
   (`Math.round(Z * 100)`). Com soma 0 (nenhum item), a barra mostra `"--"` em vez de `"0%"` — "0%
   entregue" sugeriria trabalho pendente que não existe; `"--"` é consistente com o mesmo padrão já
   usado no painel para "sem dado" (ex.: CycleTime máximo do time, `d.L.max ? ... : "--"`).

## Consequências

- `src/js/15-visao-analitica.js`: `anData()` retorna `capDone`/`projDone`; `renderAnalytics()` renomeia
  o rótulo do cabeçalho e insere `<div class="an-progress">` (duas colunas, `data-an-prog="cap"` /
  `="proj"`) entre o `<h3>` e os KPIs existentes.
- `src/js/19-tela-configuracoes.js`: ajuda do campo `anTag` usa "Reservados" em vez de "Capacidade".
- `src/styles.css`: novas classes `.an-progress`/`.an-prog-col`/`.an-prog-label`/`.an-prog-bar`.
- Testes novos em `tests/test_visao_analitica.py`: percentual calculado corretamente para Reservados e
  Projetada (casos distintos, já que um item pode entrar em Projetada sem entrar em Reservados), e o
  caso de soma zero mostrando "--".
- Documentação: `docs/regras-de-negocio.md` §10, `docs/testes/visao-analitica.md`, `docs/telas.md`
  (Visão analítica + referência cruzada no Actionable), `docs/guia-usuario/visao-analitica.md`.
