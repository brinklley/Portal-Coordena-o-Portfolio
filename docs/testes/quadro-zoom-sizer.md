# Testes: Dimensionamento do quadro (zoom/pan)

Cobre `tests/test_quadro_zoom_sizer.py` (2 testes). Trata de `updateSizer()`
(`src/js/08-whiteboard-zoom-foco.js`), que dimensiona `#board` para o zoom/pan do whiteboard. Ver
`docs/telas.md` ("Zoom/arrastar") e decisão
[`0066`](../decisoes/0066-updatesizer-usa-offsetwidth-nao-clientwidth.md).

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
