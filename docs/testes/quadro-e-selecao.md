# Testes: Board de Iniciativas — recolher/manter visíveis

Cobre `tests/test_quadro_iniciativas.py` (6 testes). Trata do comportamento da lista de iniciativas
ao selecionar um card: por padrão recolhe para mostrar só a selecionada; com "Manter todas as
iniciativas visíveis" ligado, mostra todas, com foco (destaque) na selecionada. Ver `docs/telas.md`
e decisão `0021-manter-iniciativas-visiveis.md`.

## Regra: selecionar uma iniciativa recolhe as demais por padrão

**Garante que**: com a preferência desligada (padrão), clicar num card de iniciativa esconde as
outras, mostrando só a selecionada — útil em listas grandes.

- **Dado**: `responsaveis.xlsx` (300 iniciativas), `#fShowAllIni` desmarcado.
- **Quando**: clica no primeiro card de `#lane-ini`.
- **Então (sucesso)**: só 1 card de iniciativa fica visível; o texto de contexto (`.ctx`) diz
  "mostrando só a selecionada".
- **Cenário de falha coberto**: a lista inteira continuaria visível mesmo depois da seleção,
  obrigando a rolar por centenas de cards para achar a selecionada.
- **Teste**: `test_selecionar_recolhe_as_demais_por_padrao`

## Regra: "Manter todas visíveis" mostra a lista inteira, com foco na selecionada

**Garante que**: ligar `#fShowAllIni` mantém todos os cards visíveis, mas destaca a selecionada
(classe `.sel`) e esmaece as demais (classe `.dim`), sem esconder nenhuma.

- **Dado**: `responsaveis.xlsx`, seleciona a primeira iniciativa, depois liga `#fShowAllIni`.
- **Então (sucesso)**: a contagem de cards visíveis bate com `S.V.visIni.size`; exatamente 1 card
  tem `.sel` (a selecionada); os demais (`n_total - 1`) têm `.dim`; o texto de contexto diz
  "mostrando todas".
- **Cenário de falha coberto**: a opção ligaria a exibição de todas, mas sem indicar visualmente
  qual delas está selecionada — perdendo o contexto do drill-down atual.
- **Teste**: `test_manter_todas_visiveis_mostra_todas_com_foco_na_selecionada`
- **Relacionado**: decisão `0021`.

## Regra: a preferência "manter visíveis" é do usuário, não da seleção atual

**Garante que**: trocar de iniciativa selecionada com a opção ligada não desliga a opção — ela é
uma preferência persistente da sessão, não um estado por seleção (diferente do comportamento antigo
do link "Mostrar todas", que recolhia de novo a cada nova seleção).

- **Dado**: `#fShowAllIni` ligado, primeira iniciativa selecionada.
- **Quando**: clica na segunda iniciativa da lista.
- **Então (sucesso)**: `#fShowAllIni` continua marcado; todos os cards continuam visíveis; a nova
  selecionada ganha `.sel`; as demais (`n_total - 1`) ganham `.dim`.
- **Cenário de falha coberto**: cada nova seleção resetaria a preferência do usuário, forçando-o a
  reativar "mostrar todas" repetidamente durante uma sessão de análise.
- **Teste**: `test_selecionar_outra_iniciativa_mantem_o_checkbox_marcado`

## Regra: desmarcar a opção volta a recolher a lista

**Garante que**: desligar `#fShowAllIni` volta ao comportamento padrão (só a selecionada visível,
sem nenhum `.dim` residual).

- **Dado**: uma iniciativa selecionada, `#fShowAllIni` ligado e depois desligado.
- **Então (sucesso)**: só 1 card de iniciativa visível; nenhum card com `.dim`.
- **Cenário de falha coberto**: desligar a opção deixaria cards esmaecidos residuais na tela, ou não
  recolheria de volta a lista completa.
- **Teste**: `test_desmarcar_volta_a_recolher`

## Regra: limpar a seleção não desliga a preferência "manter visíveis"

**Garante que**: o botão de limpar seleção (`#btnClear`) reseta o drill-down, mas não mexe na
preferência de exibição do usuário.

- **Dado**: iniciativa selecionada, `#fShowAllIni` ligado, clica em `#btnClear`.
- **Então (sucesso)**: `#fShowAllIni` continua marcado.
- **Cenário de falha coberto**: limpar a seleção reverteria silenciosamente uma preferência de
  interface que não tem relação direta com o que foi limpo.
- **Teste**: `test_limpar_selecao_nao_desliga_a_preferencia`

## Regra: a investigação de um item recolhido orienta a ligar a opção

**Garante que**: quando um item não aparece porque a lista está recolhida em outra seleção, a
investigação (`investigate`) explica esse motivo especificamente e orienta a ação corretiva: ligar
"Manter todas as iniciativas visíveis".

- **Dado**: duas iniciativas nos dados; a primeira selecionada via `S.path`, investiga a segunda.
- **Então (sucesso)**: os passos da investigação incluem `[False, "Recolhido na lista"]`; a ação
  sugerida para esse passo cita "Manter todas as iniciativas visíveis".
- **Cenário de falha coberto**: o diagnóstico diria só "item não visível" sem apontar que a causa é
  a lista recolhida, nem qual configuração resolve — o usuário teria que descobrir sozinho.
- **Teste**: `test_investigacao_de_item_recolhido_orienta_o_checkbox`
- **Relacionado**: `docs/testes/hierarquia-e-modelo.md` (mesmo mecanismo `investigate`).
