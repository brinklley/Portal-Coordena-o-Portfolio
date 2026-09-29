# 0043 — Vazão ganha "Reserva entregue" e User Story divide o Planejado em Reservado/outro semestre

## Contexto

O usuário comparou os números do Report F4P com a nova funcionalidade do Analytics e identificou um
problema de conceito: os quadrantes **Vazão** e **User Story** tratavam "Reserva"/"Planejado" (itens
com a tag de capacidade do roadmap, `CFG.anTag`) como suficiente para dizer que um item estava
"reservado" para o semestre selecionado — sem checar se o **épico vinculado** ao item de fato tem
compromisso de roadmap **naquele mesmo semestre**. Exemplo dado pelo usuário: um item card entregue
(Vazão) no dia 1/agosto cai no 2º semestre por data de entrega, mas se o roadmap mapeado do seu épico
aponta compromisso pro 1º semestre, contar esse item como "reserva do 2º semestre" está incorreto — a
tag por si só não garante que o compromisso do roadmap é do período em análise.

Pedido teve duas partes:

1. **Vazão (reserva vs. realizado)** → acrescentar um terceiro número, "Reserva entregue": só os itens
   da Reserva cujo épico tem compromisso de roadmap (interno ou executivo, conforme o filtro) **igual**
   ao semestre selecionado.
2. **User Story (planejado vs. não planejado)** → dividir "Planejado" em "Reservado" (mesmo critério de
   compromisso batendo com o semestre) e "Planejado (outro semestre)" (tag presente, mas compromisso do
   épico aponta pra outro semestre — ou nenhum registrado). "Não planejado" continua com a mesma regra.

O usuário pediu explicitamente para perguntar antes de assumir qualquer regra não especificada, em vez
de adivinhar. Duas rodadas de perguntas fecharam o desenho:

- **Fonte do "compromisso de roadmap batendo com o semestre"**: reaproveitar exatamente a mesma
  comparação já usada pelo quadrante Roadmap – Épicos (`f4pRoadmapEpis`, §12.7) para decidir se um
  épico "está no Roadmap" do semestre selecionado — Interno compara o Target Date do próprio épico
  (`e.interno`); Executivo sobe Épico → Release → Iniciativa e compara o `AnoSemestreRoadmap` da
  iniciativa (`i.exec`). **O quadrante Roadmap – Épicos em si não foi alterado** — só a lógica de
  comparação foi extraída para uma função à parte e reaproveitada nos dois quadrantes deste PR (ponto
  que precisou de esclarecimento explícito do usuário durante a especificação, por uma resposta que
  pareceu preocupada em preservar aquele quadrante intocado).
- **Estrutura do Vazão**: aditiva, não substitutiva — Reserva continua exatamente como era (tag, sem
  checar compromisso), Realizado continua exatamente como era; "Reserva entregue" é um terceiro número
  novo, exibido como `Reserva | Reserva entregue | Realizado` (mesmo padrão visual `a|b|c` do
  Roadmap – Épicos).
- **Épico sem compromisso de roadmap registrado** (sem Target Date preenchido, no critério Interno; sem
  iniciativa vinculada ou sem `AnoSemestreRoadmap` preenchido, no critério Executivo): conta como
  "outro semestre" no User Story (não entra em Reservado) e fica **fora** da Reserva entregue do Vazão —
  mas continua contando normalmente nos números que já o incluíam antes (Reserva/Realizado no Vazão; o
  total agregado de Planejado no User Story, usado pela conferência cruzada).

## Implementação

`src/js/23-report-f4p.js`:

- Nova função `f4pEpiCompromissoBate(e, sem)`: mesma comparação Interno/Executivo do
  `f4pRoadmapEpis`, isolada para reuso — recebe um épico e um semestre, devolve se o compromisso do
  épico bate com esse semestre (`false` se o épico não existir, se o semestre não estiver definido, ou
  se o campo relevante — `e.interno` ou `i.exec` — não estiver preenchido).
- `f4pVazaoReservaEntregueItems(team, st)`: filtra `f4pVazaoReservaItems` pelos itens cujo épico
  (`S.model.epis.get(o.epicoId)`) bate com o semestre selecionado (`f4pSemester()`). `f4pVazaoCell`
  passa a exibir `Reserva | Reserva entregue | Realizado`, com um novo botão
  `data-f4p-vazao-reserva-entregue-team` e uma nova entrada no dispatcher de clique de
  `#f4pBody`, abrindo a mesma `f4pItemsModal`.
- `f4pUsReservadoItems(team, st)` e `f4pUsPlanejadoOutroSemestreItems(team, st)`: filtram
  `f4pUsPlanejadoItems` (mantida intacta, agora um agregado interno não exibido diretamente) pelo mesmo
  critério — bate/não bate. `f4pUsCell` passa a exibir
  `Reservado | Planejado (outro semestre) | Não planejado`, com `data-f4p-us-set` trocando o antigo
  valor único `"planejado"` por `"reservado"`/`"planejadooutro"` (o dispatcher de clique de `#f4pBody`
  foi atualizado para os três valores).
- Títulos atualizados em `F4P_QUADS`: `"Vazão (reserva vs reserva entregue vs realizado)"` e
  `"User Story (reservado vs planejado outro semestre vs não planejado)"`.
- `f4pReconciliacao()`/`f4pReconciliacaoBanner()` **não precisaram mudar de estrutura**: como
  Reservado + Planejado (outro semestre) é uma partição exata do Planejado total (nenhum item excluído,
  só reclassificado), a soma que a conferência cruzada valida (Technical Story Realizado + User Story
  Planejado + User Story Não planejado = Vazão Realizado) continua batendo sem alteração de cálculo — só
  o texto do banner foi ajustado para deixar claro que "User Story Planejado" ali é a soma de
  Reservado + Planejado (outro semestre), já que esses dois não aparecem mais somados como um único
  número na UI.

## Por que isso não é uma regressão da Reserva/Realizado do Vazão nem do Não planejado do User Story

Nenhuma das duas contagens pré-existentes muda de definição — Reserva, Realizado e Não planejado
continuam exatamente com a mesma regra de antes deste PR. O que muda é só um recorte **a mais**, dentro
de conjuntos que já existiam, usando um critério (compromisso de roadmap do épico) que o portal já
calculava para outro quadrante.

## Testes

`tests/test_report_f4p.py` (seções Vazão e User Story):

- Reserva entregue bate com o compromisso Interno do próprio épico (`e.interno`).
- Reserva entregue bate com o compromisso Executivo da iniciativa (`i.exec`, subindo Release → Épico).
- Reserva entregue exclui reserva cujo épico aponta pra outro semestre.
- Reserva entregue exclui reserva cujo épico não tem compromisso registrado (caso de borda).
- Clique em "Reserva entregue" abre a lista certa.
- Reservado/Planejado (outro semestre) formam partição exata do Planejado (soma bate sempre).
- Reservado usa o critério Interno; Planejado (outro semestre) cobre o critério Executivo divergente e o
  épico sem compromisso registrado.
- Clique em "Reservado" e em "Planejado (outro semestre)" abrem as listas certas.
- Reconciliação cruzada continua batendo sem alteração (teste existente, sem mudança de expectativa).
- Títulos dos dois quadrantes atualizados nos testes que verificam o texto exibido no painel.
