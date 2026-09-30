# 0048 — Vazão (Report F4P): Reserva passa a bater com a Capacidade da Visão analítica

## Contexto

O usuário reportou, com prints do quadrante "Vazão (reserva vs reserva entregue vs realizado)" e da
Visão analítica, que o primeiro número (Reserva) deveria bater com a "Capacidade" mostrada na Visão
analítica (§10) para o mesmo time — e não batia. Exemplo do print: time FL1 - App Visa Card,
Capacidade = 14 US na Visão analítica, mas Reserva = 0 no quadrante Vazão.

## Diagnóstico

Os dois números vinham de recortes diferentes por desenho, em três eixos:

1. **Status do item**: Capacidade (`anData()`, `src/js/15-visao-analitica.js`) soma itens de **qualquer
   status** (Backlog/Discovery/WIP/Vazão) dos épicos comprometidos com o roadmap selecionado. Reserva
   (`f4pVazaoReservaItems`, decisão `0022`) só contava itens **já entregues** (categoria de fluxo
   Vazão) — era, por construção, um subconjunto do Realizado.
2. **Escopo**: Capacidade olha para os **épicos** cujo compromisso de roadmap (Target Date do próprio
   épico, no Interno; `AnoSemestreRoadmap` da iniciativa, no Executivo) bate com o semestre
   selecionado — não importa quando o item foi entregue. Reserva olhava para **tudo que o time entregou
   dentro do calendário exato do semestre** (`o.deploy` na janela), sem checar se o épico do item estava
   de fato comprometido com aquele roadmap.
3. **Tipos considerados**: Capacidade usa `CFG.ctTypes` (padrão User Story, Technical Story e
   **Technical Solution**); Reserva usava `CFG.f4p.types` (padrão User Story e Technical Story, sem
   Technical Solution) — configurações independentes desde a decisão `0022`.

No exemplo do usuário, a interseção "entregue nesta janela E do épico certo E com a tag ROADMAP" deu
zero — não por bug de cálculo, mas porque três recortes diferentes raramente apontam pro mesmo
conjunto de itens.

## Decisão

Consultado sobre como corrigir (três opções: redefinir Reserva para igualar a Capacidade em qualquer
status; manter Reserva restrita a itens entregues mas exigir o compromisso do épico; ou só alinhar a
lista de tipos), o usuário escolheu a primeira: **Reserva passa a ser exatamente a mesma capacidade do
roadmap que a Visão analítica já calcula**, parametrizada por time (o Report F4P mostra todos os times
lado a lado, não só o selecionado no filtro de Time da Visão analítica).

Nova função `f4pRoadmapCapacityItems(team, sem)` em `src/js/23-report-f4p.js`: itens do time cujo tipo
está em `CFG.ctTypes` (via `anTypes()`, já definida em `15-visao-analitica.js`), com a tag de
capacidade (`CFG.anTag`, via `f4pCapacityTag()`), cujo épico (`o.epicoId`) tem compromisso de roadmap
batendo com o semestre selecionado (`f4pEpiCompromissoBate`, já usada pela Reserva entregue desde a
decisão `0043`) — em qualquer status. `f4pVazaoReservaItems(team, st)` passou a delegar pra essa
função; o parâmetro `st` (janela de datas) deixou de ser usado por Reserva, mas foi mantido na
assinatura pra não obrigar mudança nos call-sites existentes.

### Consequência: Reserva deixa de ser subconjunto do Realizado

Por não depender mais do que já foi entregue, Reserva **deixou de ser, por construção, um subconjunto
do Realizado** (invariante central da decisão `0022`). Isso muda dois comportamentos documentados:

- **Cor da seta de tendência** (decisão `0024`): a comparação Realizado vs. Reserva continua igual no
  código (`realizado.length >= reserva.length`), mas o vermelho (Realizado < Reserva) — antes
  inalcançável em uso normal — passa a ser um **alerta real**: o time reservou mais do que já entregou
  dentro do semestre. Ficou mais útil, não menos correto.
- **Reserva entregue** (decisão `0043`): antes era escrita como "subconjunto da Reserva cujo épico
  também bate o compromisso". Como a Reserva mudou de conjunto-base, `f4pVazaoReservaEntregueItems`
  passou a ser escrita direto sobre o Realizado (`f4pVazaoOps` filtrado por tag + compromisso) — **o
  resultado numérico não muda** (é a mesma interseção tag ∩ compromisso ∩ entregue de sempre), só a
  forma de calcular, para não herdar o novo escopo/tipos da Reserva.

`f4pVazaoOps`/`f4pVazaoRealizadoItems` (o Realizado) **não mudaram** — continuam usando `CFG.f4p.types`
e a janela exata do semestre, como antes da decisão `0022`.

## Ressalva assumida

A Reserva (e a Capacidade) não aplicam os filtros de Responsável da iniciativa (`S.f.owners`) ou de
busca (`S.f.q`) da Visão analítica/Whiteboard — nenhum quadrante do Report F4P nunca aplicou esses
filtros (eles mostram todos os times, não só o filtrado). Com o filtro de Responsável ligado, a
Capacidade mostrada na Visão analítica pode ficar menor que a Reserva do Report F4P para o mesmo time,
já que esta última sempre soma todos os responsáveis. Isso é consistente com o resto do painel, não uma
regressão desta correção.

## Testes

`tests/test_report_f4p.py` (seção "Quadrante 5 · Vazão"):
- `test_vazao_reserva_conta_qualquer_status_do_epico_comprometido` (substitui
  `test_vazao_reserva_e_subconjunto_com_a_tag_de_capacidade`): Reserva conta Backlog/WIP/Vazão
  igualmente, desde que tagueado e comprometido.
- `test_vazao_reserva_usa_tag_de_capacidade_configuravel` (substitui
  `test_vazao_usa_tag_de_capacidade_configuravel`): mesma regra da tag configurável, adaptada ao novo
  cálculo.
- `test_vazao_reserva_bate_com_capacidade_da_visao_analitica` (novo): compara diretamente
  `f4pVazaoReservaItems(...).length` com `anData().cap` para o mesmo time/semestre — o teste que prova
  o pedido original do usuário.
- `test_vazao_reserva_exige_epico_comprometido_mas_realizado_nao` (novo): contraste explícito entre os
  dois critérios.
- `test_vazao_seta_de_tendencia_fica_vermelha_quando_realizado_menor_que_reserva` (novo): o caso
  vermelho, agora alcançável.
- `test_vazao_clique_na_reserva_mostra_so_os_com_a_tag`: adaptado para vincular um épico comprometido
  (a Reserva agora depende disso).
- `test_vazao_reserva_entregue_*` (4 testes existentes, decisão `0043`): valores de `reserva` ajustados
  nos asserts — a própria Reserva agora já exclui o que a Reserva entregue excluía antes; `reservaEntregue`
  não muda em nenhum dos casos.

Confirmei que os 5 testes novos/com regra nova falham contra o código anterior a esta decisão
(restaurando `f4pVazaoReservaItems`/`f4pVazaoReservaEntregueItems` antigas via `git stash`) antes de
reaplicar a correção — em especial `test_vazao_reserva_bate_com_capacidade_da_visao_analitica`, que
falhava com `{cap: 3, reserva: 0}` na versão anterior, reproduzindo exatamente a divergência relatada.

## Achado à parte (fora do escopo desta correção)

Ao rodar a suíte completa, `tests/test_actionable.py::test_burnup_clique_em_faltam_abre_lista_dos_itens_ainda_nao_entregues`
falhou de forma reproduzível **mesmo no código anterior a esta mudança** (confirmado via `git stash`) —
aparenta ser um bug de fronteira de data (o teste usa `deploy: new Date()` no próprio dia da execução;
30/set é o último dia do mês). Não foi investigado nem corrigido aqui por ser um problema pré-existente,
sem relação com a Reserva do Vazão — reportado ao usuário separadamente.
