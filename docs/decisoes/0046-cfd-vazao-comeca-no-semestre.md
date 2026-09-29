# 0046 — CFD: a Vazão passa a começar em 0 no início do semestre selecionado

## Contexto

Logo depois de usar a primeira versão do CFD (decisão `0045`), o usuário mandou um print: o gráfico
aparecia quase todo verde (faixa de Vazão) desde a primeira semana, com uma tooltip mostrando "Vazão:
2371" já na semana de 12/ago a 18/ago — um número muito maior que qualquer entrega plausível de uma
única semana. O pedido: "Acredito que o melhor seria a vazão iniciar em 0 no primeiro dia do semestre
assim retratando um CFD onde o usuário entenda como foi o comportamento dentro daquele semestre."

## Diagnóstico

A primeira versão do CFD (`actCfdCategoriaEm`) reconstrói a categoria de um item em qualquer data
usando `o.fd`, sem nenhum limite inferior — um item entregue anos atrás (antes até de o semestre
selecionado existir) já contava como "Vazão" desde a primeira semana do gráfico. Como o modelo carrega
o **histórico completo** de cada time (não só o período filtrado), o CFD estava mostrando a Vazão
**acumulada desde sempre**, não a vazão **daquele semestre** — o oposto do que um CFD "por período" deve
mostrar. Esse é exatamente o padrão já usado em todo o resto do Report F4P/Actionable para "Vazão"
(Vazão do Report F4P, §12.6; Distribuição Vazão por mês, §13.2): sempre restrita a itens cujo `o.deploy`
cai dentro do semestre selecionado — só o CFD, por ser uma reconstrução histórica em vez de um filtro
direto por `o.deploy`, tinha ficado de fora dessa convenção.

## Correção

`actCfdOps(team, st)` passa a excluir do universo do CFD **qualquer item que já estava em Vazão no dia
anterior ao início do semestre selecionado** (`actCfdCategoriaEm(o, diaAnterior, c) === "vazao"`) — não
só da faixa de Vazão, do gráfico **inteiro** (todas as 4 faixas, todas as semanas), porque esse item já
não faz parte do fluxo em análise neste período: é trabalho de um ciclo anterior, já concluído.

- Um item entregue **antes** do semestre selecionado: some do gráfico inteiro.
- Um item entregue **dentro** do próprio semestre (mesmo que criado bem antes dele): continua contando
  normalmente, inclusive na Vazão a partir da semana em que foi entregue — o limite é sempre pelo dia
  **anterior** ao início do semestre, então uma entrega no próprio 1º dia do semestre já conta.
- Um item ainda não entregue (em qualquer categoria aberta, criado antes ou durante o semestre):
  continua contando normalmente em Nenhum/Discovery/WIP — é trabalho real ainda em andamento no board,
  relevante para entender a dinâmica deste período.

Com isso, a Vazão do gráfico sempre começa em 0 (ou perto disso, se algo já foi entregue no primeiro
dia) na primeira semana do semestre, crescendo só com as entregas que de fato aconteceram dentro dele —
exatamente o pedido do usuário.

## Por que excluir do gráfico inteiro, e não só "zerar" a Vazão

Zerar só a Vazão sem tocar nas outras 3 faixas quebraria a partição: um item de negócio antigo,
"congelado" artificialmente numa categoria aberta (Nenhum/Discovery/WIP) que ele não ocupa mais de
verdade, inflaria essas faixas com trabalho que já não existe mais em aberto. A única forma consistente
de "esse item não é deste semestre" é ele sumir do cálculo inteiro, não só de uma faixa.

## Testes

`tests/test_actionable.py`: `test_cfd_exclui_itens_ja_entregues_antes_do_semestre_selecionado` (o
cenário exato do bug: item de negócio antigo some do gráfico, item novo criado no semestre continua
contando), `test_cfd_nao_exclui_item_entregue_no_1o_dia_do_semestre` (limite exato: entrega no próprio
primeiro dia não é excluída) e `test_cfd_vazao_comeca_em_zero_e_cresce_com_entregas_dentro_do_semestre`
(a consequência visível: a série de Vazão começa em 0 e sobe com as entregas do período). Validado
também visualmente, reproduzindo o cenário do print do usuário (2.000 itens de negócio antigos +
fluxo real dentro do semestre): antes da correção, o eixo Y chegava à casa dos milhares; depois, reflete
só os ~20 itens do fluxo real do período.
