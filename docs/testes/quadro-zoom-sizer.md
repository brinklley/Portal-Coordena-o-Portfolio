# Testes: Dimensionamento do quadro (zoom/pan)

Cobre `tests/test_quadro_zoom_sizer.py` (6 testes). Trata de `updateSizer()`
(`src/js/08-whiteboard-zoom-foco.js`), que dimensiona `#board`/`#sizer` para o zoom/pan do whiteboard.
Ver `docs/telas.md` ("Zoom/arrastar") e decisões
[`0066`](../decisoes/0066-updatesizer-usa-offsetwidth-nao-clientwidth.md) e
[`0069`](../decisoes/0069-margem-pannable-em-volta-do-conteudo.md).

## Regra: `updateSizer()` não oscila quando a barra de rolagem aparece e some

**Garante que**: `updateSizer()` usa uma medida do viewport (`offsetWidth`/`offsetHeight`) que não
muda dependendo de haver ou não barra de rolagem — evitando um ciclo onde o próprio tamanho que a
função atribui ao quadro decide se a barra aparece, e a barra aparecendo/sumindo muda a medida que a
função lê, nunca convergindo.

- **Dado**: `vp.clientWidth` mockado para alternar entre dois valores a cada leitura (simula a barra
  de rolagem aparecendo/sumindo de verdade).
- **Quando**: `updateSizer()` é chamado 10 vezes seguidas.
- **Então (sucesso)**: `board.style.minWidth` é o mesmo valor nas 10 chamadas.
- **Cenário de falha coberto** (bug relatado pelo usuário): com o painel de detalhes aberto
  (estreitando o quadro) e uma carga grande de dados, a tela "ficava tremendo em loop" — o DevTools
  mostrava o atributo `style` de `#board` sendo reescrito sem parar, sem nenhum erro no console.
  Reproduzido neste teste com o mock: antes da correção, `board.style.minWidth` oscilava em perfeita
  sincronia com o valor mockado de `clientWidth` (confirmado revertendo a correção e rodando o teste).
- **Teste**: `test_updatesizer_nao_oscila_quando_a_barra_de_rolagem_aparece_e_some`

## Regra: a correção não muda o comportamento quando não há barra de rolagem

**Garante que**: no caso comum (conteúdo cabe sem precisar de barra), `offsetWidth` e `clientWidth`
já são iguais — trocar um pelo outro não muda o tamanho que o quadro recebe.

- **Então (sucesso)**: `board.style.minWidth` continua igual a `vp.offsetWidth` (em pixels), sem
  nenhum mock.
- **Teste**: `test_updatesizer_usa_offsetwidth_mesmo_sem_barra_de_rolagem`

## Regra: margem pannable (meia tela) em volta do conteúdo, nos 4 lados (decisão 0069)

**Garante que**: `#board` fica deslocado dentro de `#sizer` por `vp.offsetWidth * 0.5` /
`vp.offsetHeight * 0.5` (`panMX`/`panMY`) — não mais colado em `(0,0)` — e `#sizer` cresce na mesma
medida além do conteúdo, nos 4 lados: sempre sobra espaço pra mover a câmera, sem bater na borda do
conteúdo imediatamente.

- **Então (sucesso)**: `board.style.left`/`top` são positivos (> 0); `#sizer` é pelo menos
  `conteúdo + margem` em largura e altura.
- **Cenário de falha coberto** (bug relatado pelo usuário, prints anotados do minimapa): antes, só
  existia uma margem pequena (de conteúdo, não de tela) à direita/abaixo — a câmera "batia nas bordas"
  tentando mover em qualquer direção, principalmente esquerda/acima (margem zero).
- **Teste**: `test_board_tem_margem_pannable_em_volta_do_conteudo`

## Regra: a margem não encolhe com o zoom out (decisão 0069)

**Garante que**: a margem é medida em pixels de **tela** (`vp.offsetWidth`/`offsetHeight`, sem
multiplicar por `Z`) — `board.style.left`/`top` ficam os mesmos em qualquer nível de zoom.

- **Cenário de falha coberto**: a margem antiga (`160`/`200px` de conteúdo) encolhia proporcionalmente
  ao zoom — em zoom bem reduzido (comum pra ver o quadro inteiro), virava poucos pixels reais de tela,
  imperceptível — exatamente o relatado pelo usuário.
- **Teste**: `test_margem_pannable_nao_encolhe_com_zoom_out`

## Regra: a carga de dados posiciona a câmera no conteúdo, não na margem (decisão 0069)

**Garante que**: como `#board` não começa mais em `(0,0)` do `#sizer`, `loadTables()` posiciona
`vp.scrollLeft`/`scrollTop` em `panMX`/`panMY` após a carga — senão a tela abriria mostrando só a
margem em branco.

- **Teste**: `test_carga_inicial_comeca_com_a_camera_no_conteudo_nao_na_margem`

## Regra: selecionar uma iniciativa rola para o topo do conteúdo, não da margem (decisão 0069)

**Garante que**: o reset de rolagem vertical ao selecionar uma iniciativa (antes, sempre `vp.scrollTop
= 0`) usa `panMY` — a mesma correção de "onde a margem está" se aplica a qualquer lugar do código que
antes assumia `0` como "início do conteúdo".

- **Cenário de falha coberto**: sem a correção, selecionar uma iniciativa com a câmera longe do topo
  rolaria para a margem em branco acima do conteúdo, não para o conteúdo em si.
- **Teste**: `test_selecionar_iniciativa_rola_a_camera_para_o_topo_do_conteudo_nao_da_margem`
