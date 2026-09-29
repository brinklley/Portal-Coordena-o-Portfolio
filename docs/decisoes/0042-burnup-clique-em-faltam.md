# 0042 — Burnup Reserva: "faltam" também fica clicável

## Contexto

O usuário testou a primeira versão do Actionable (decisão `0041`) e reportou, com print, que
"reservado" e "entregue" abrem a lista dos itens exatos ao clicar, mas "faltam" não — quebrando a
mesma transparência que o resto do quadrante (e do Report F4P) já dá para todo número calculado.

## Correção

`actBurnupData()` passa a calcular também `faltamItems`: o complemento exato de `entregues` dentro de
`capItems` (por construção, `entregues.length + faltamItems.length === capItems.length` sempre) — em
vez de só o número `faltam` (`escopo − entreguesN`) que já existia. O número "faltam" no resumo do
quadrante vira um botão (`data-act-items="faltam"`), igual aos outros dois, abrindo o mesmo
`f4pItemsModal` com a lista de `faltamItems`.

## Ajuste de regra encontrado ao implementar (não só a UI)

Para "entregues + faltam" fechar exatamente com "reservado" (a mesma garantia que qualquer quadrante
de partição deste portal já mantém — ver User Story, `docs/regras-de-negocio.md` §12.8), "Entregue"
precisou passar a considerar só as entregas **dentro do período do semestre selecionado** — antes, a
lista de itens por trás do número "Entregue" (`entregues`) não tinha esse limite (só o número exibido,
`entreguesN`, calculado via `cumulative`, já era limitado aos meses do semestre). Isso significa que, na
versão anterior, um item entregue **depois** do semestre selecionado já ter encerrado (uma entrega
tardia) apareceria na lista aberta pelo clique em "Entregue", mesmo o número mostrado não contá-lo — um
item já entraria e sairia de "faltam" dependendo de qual dos dois (número ou lista) o usuário olhasse.

Com o ajuste, uma entrega tardia (fora do período do semestre selecionado) conta como **Faltam**, não
como **Entregue** — fazia sentido: o item estava previsto para aquele período, mas não chegou dentro
dele, então continua "faltando" do ponto de vista daquele burnup específico, mesmo já tendo sido
entregue depois. Não muda os números já exibidos em uso normal (a única diferença de comportamento
aparece nesse caso de borda, entrega fora do período do semestre selecionado).

## Testes

`tests/test_actionable.py`:
- `test_burnup_clique_em_faltam_abre_lista_dos_itens_ainda_nao_entregues`: confirma que o clique em
  "faltam" abre a lista certa (só os itens reservados ainda não entregues).
- `test_burnup_entrega_fora_do_periodo_do_semestre_conta_como_faltam`: cobre o ajuste de regra — um
  item entregue depois do fim do semestre selecionado (já encerrado) conta em `faltamItems`, não em
  `entregues`.
