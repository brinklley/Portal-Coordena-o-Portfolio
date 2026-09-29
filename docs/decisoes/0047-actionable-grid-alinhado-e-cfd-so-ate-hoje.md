# 0047 — Actionable: grade alinhada por linha; CFD não desenha além de hoje num semestre em curso

## Contexto

Depois de usar a versão com os 4 quadrantes prontos (decisões `0045`/`0046`), o usuário pediu duas
melhorias num só PR:

1. Os quadrantes 3 (Distribuição Vazão por mês) e 4 (CFD) apareciam desalinhados — um começava mais
   acima que o outro — "causa um pouco de confusão".
2. No CFD, colocar uma linha vertical simulando a semana atual, e "o restante do morro não precisa ser
   construído quando o roadmap (interno ou executivo) selecionado é o semestre atual".

## Melhoria 1 — grade alinhada por linha

### Diagnóstico

`$("actBody").innerHTML` montava a grade como duas **colunas independentes**
(`<div class="f4p-col">${ctCard}${distCard}</div><div class="f4p-col">${buCard}${cfdCard}</div>`) —
cada coluna empilhava seus dois quadrantes com flexbox, sem nenhuma relação de altura com a coluna
vizinha. Como o card do Burnup Reserva tem um texto explicativo bem mais longo que o do CycleTime, a
coluna da direita ficava mais alta na 1ª linha — e como cada coluna empilha por conta própria, o 2º
quadrante da coluna esquerda (Distribuição Vazão por mês) começava ~400px mais acima que o 2º
quadrante da direita (CFD).

Esse layout (`f4p-grid`/`f4p-col`) é compartilhado com o Report F4P, que **depende** de colunas
independentes para os selos de grupo (`F4P_GROUPS`) atravessarem pares de quadrantes dentro da mesma
coluna — não dava pra simplesmente mudar o CSS compartilhado sem risco de quebrar aquele painel, que já
está em produção e testado.

### Correção

Nova classe própria do Actionable, `.act-quad-grid`: os 4 cards viram itens **diretos** do grid (sem
`.f4p-col` por dentro), na ordem de leitura (CycleTime, Burnup Reserva, Distribuição Vazão por mês,
CFD) — o posicionamento automático do CSS Grid preenche por linha (2 colunas), e o alinhamento padrão
(`stretch`) iguala a altura de cada item ao maior da mesma linha. Com isso, a 2ª linha sempre começa na
mesma altura para os dois quadrantes, não importa a diferença de altura entre os dois primeiros. O
`f4p-grid`/`f4p-col` do Report F4P não foi tocado.

## Melhoria 2 — CFD não desenha além de hoje num semestre em curso

### Leitura do pedido

"O restante do morro não precisa ser construído" — a versão anterior (decisão `0045`) desenhava as 26
semanas inteiras mesmo num semestre em curso, deixando as faixas achatadas (mesmo valor de hoje) nas
semanas futuras, como projeção. O usuário prefere que, para o semestre **em curso**, o gráfico
simplesmente **pare** em hoje — sem desenhar nem a projeção achatada — com uma linha vertical marcando
onde "hoje" fica dentro do semestre. O eixo X continua mostrando o semestre inteiro (mesmas marcas de
início/fim): só a área colorida é que não avança além da linha.

Num semestre **já encerrado**, não existe "resto" — o período inteiro já é passado — então o gráfico
continua desenhando tudo, sem linha "hoje" (não haveria o que marcar).

### Implementação

`actCfdSvg(data, st)` passa a receber o `st` (estado do semestre). Quando `st.kind === "current"`:
encontra o índice da semana que contém hoje (`hojeIdx`) e usa esse índice como limite (`cutoff`) para
os pontos das áreas (`areaPath`) e das caixas de hover (`act-cfd-hit`) — os cálculos de escala do eixo X
(`xOf`) continuam usando o total de semanas do semestre (`n`), então a posição de cada semana dentro do
eixo não muda; só menos pontos são efetivamente desenhados. Uma nova linha vertical tracejada
(`.act-cfd-hoje`) marca a posição de `hojeIdx`, com o rótulo "hoje" acima dela. Quando
`st.kind !== "current"` (semestre já encerrado), `cutoff` é sempre o último índice — comportamento
idêntico ao de antes, sem a linha.

`actCfdData`/`actCfdWeeks`/`actCfdOps` não mudaram — continuam calculando as 26 semanas inteiras e as 4
contagens normalmente; a mudança é só na hora de **desenhar** (`actCfdSvg`), reaproveitando os mesmos
dados.

## Testes

`tests/test_actionable.py`:
- `test_quadrantes_3_e_4_ficam_alinhados_na_mesma_altura`: compara o topo (`getBoundingClientRect().top`)
  dos 4 cards — confirma que a 1ª linha (CycleTime/Burnup) e a 2ª linha (Distribuição/CFD) começam,
  cada uma, na mesma altura entre si.
- `test_os_4_quadrantes_tem_regra_definida`: ajustado para a nova ordem de leitura no DOM (linha por
  linha, não mais coluna por coluna).
- `test_cfd_semestre_em_curso_mostra_linha_hoje_e_nao_desenha_alem_dela`: confirma a linha `.act-cfd-hoje`
  e que o número de caixas de hover (`.act-cfd-hit`) é menor que o total de semanas do semestre.
- `test_cfd_semestre_encerrado_nao_mostra_linha_hoje_e_desenha_tudo`: confirma que um semestre já
  encerrado não tem a linha "hoje" e desenha todas as semanas.

Confirmei que o teste de alinhamento falha claramente contra o código anterior (diferença de ~424px
entre os topos dos quadrantes 3 e 4, reproduzindo exatamente o problema relatado) antes de restaurar a
correção.
