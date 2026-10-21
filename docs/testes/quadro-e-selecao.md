# Testes: Board de Iniciativas — recolher/manter visíveis

Cobre `tests/test_quadro_iniciativas.py` (12 testes). Trata do comportamento da lista de iniciativas
ao selecionar um card: por padrão recolhe para mostrar só a selecionada; com "Manter todas as
iniciativas visíveis" ligado, mostra todas, com foco (destaque) na selecionada; de clicar no
whiteboard para fechar o painel lateral aberto; e da largura ajustável do painel lateral. Ver
`docs/telas.md` e decisões `0021-manter-iniciativas-visiveis.md`,
`0065-clicar-no-whiteboard-fecha-painel-lateral.md` e
`0068-painel-lateral-largura-ajustavel.md`.

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

## Regra: clicar no whiteboard fecha o painel lateral aberto (Visão Analítica/Report F4P/Actionable)

**Garante que**: com um dos 3 painéis laterais aberto, um clique em qualquer lugar do quadro — card
ou área vazia — fecha o painel, sem precisar ir até o botão "«". O card clicado continua respondendo
normalmente (seleciona a iniciativa/release/épico). Um arrastar (pan) não conta como clique: o painel
só fecha num clique de verdade, sem deslocamento do mouse entre o pressionar e o soltar.

- **Dado**: Time e Roadmap selecionados, um dos painéis (Visão Analítica, Report F4P ou Actionable)
  aberto.
- **Quando**: o usuário clica no quadro — num card, ou numa área vazia.
- **Então (sucesso)**: o painel aberto fecha (`AN.open`/`F4P.open`/`ACT.open` vira `false`); se o
  clique foi num card, a seleção (`S.path`) é definida normalmente, como se o painel não estivesse
  aberto.
- **Cenário de falha coberto** (melhoria sugerida pelo usuário): antes, clicar no quadro com um
  painel aberto não tinha nenhum efeito sobre o painel — o usuário precisava reparar que existia um
  botão "«" no canto do painel e ir até ele, um movimento que não é óbvio quando o painel ocupa boa
  parte da tela.
- **Cenário de comportamento inesperado coberto**: arrastar o quadro (pan) com um painel aberto não
  fecha o painel — só um clique sem arrastar conta; senão, reorganizar a visão enquanto consulta a
  Visão Analítica fecharia o painel a cada arrasto, atrapalhando em vez de ajudar.
- **Testes**: `test_clicar_no_whiteboard_fecha_o_painel_lateral_aberto`,
  `test_clicar_num_card_fecha_o_painel_mas_mantem_o_comportamento_normal_do_clique`,
  `test_arrastar_o_quadro_nao_fecha_o_painel`
- **Relacionado**: decisão `0065-clicar-no-whiteboard-fecha-painel-lateral.md`.

## Regra: a largura do painel lateral é ajustável, com padrão menor que o antigo (decisão 0068)

**Garante que**: o painel (Visão Analítica/Report F4P/Actionable, compartilham `.an-panel`) tem largura
padrão de 760px (antes, fixo em `min(1180px, 96vw)`) e uma alça na borda direita (`.an-resize`)
permite arrastar entre 360px e 1180px — como o painel é `position:fixed` sobre o whiteboard (que
sempre renderiza em largura cheia, nunca encolhe), reduzir a largura do painel aumenta diretamente a
área do quadro visível ao lado dele.

- **Dado**: um dos painéis aberto, viewport de teste (1500px).
- **Então (sucesso)**: a largura do painel é 760px por padrão; arrastar a alça pra direita aumenta a
  largura; arrastar bem além do limite mínimo trava em 360px (nunca menos).
- **Cenário de falha coberto** (melhoria pedida pelo usuário, print anotado): com um painel aberto, a
  área visível do quadro ficava pequena demais para navegar sem bater nas bordas — o usuário precisava
  manter um painel aberto (para consultar números) e ao mesmo tempo mexer no quadro, mas não tinha
  espaço para as duas coisas.
- **Testes**: `test_painel_lateral_tem_largura_padrao_menor_que_a_antiga`,
  `test_arrastar_a_alca_redimensiona_o_painel_dentro_dos_limites`
- **A largura é uma preferência compartilhada pelos 3 painéis, e persiste entre sessões**: mudar a
  largura com a Visão Analítica aberta também muda o Report F4P e o Actionable (todos usam a mesma
  variável CSS `--an-w`); o valor escolhido é salvo em `localStorage` e aplicado na próxima abertura do
  Portal.
  - **Teste**: `test_largura_do_painel_persiste_e_vale_para_os_3_paineis`
- **Relacionado**: decisão `0068-painel-lateral-largura-ajustavel.md`.
