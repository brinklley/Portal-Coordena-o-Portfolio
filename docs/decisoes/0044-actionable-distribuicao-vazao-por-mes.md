# 0044 — Actionable ganha o quadrante "Distribuição Vazão por mês"

## Contexto

O usuário pediu um terceiro quadrante para o painel Actionable, inspirado numa visualização do
Analytics (print anexo): para cada mês do semestre selecionado, uma barra 100% empilhada mostrando que
fração dos itens entregues (Vazão) naquele mês é User Story, Technical Story ou os demais tipos —
excluindo da amostra qualquer item de tipo bug (bug, internal bug, external bug). Pediu explicitamente
para eu perguntar antes de assumir qualquer regra não especificada.

O pedido definia com clareza: os três tipos de bucket (User Story/Technical Story/demais), a exclusão
de bugs, o rótulo "XX%" com 2 casas decimais em cada barra, a transparência por clique, a divisão do
eixo Y por mês do roadmap selecionado (interno ou executivo) e pelo time do filtro, o eixo X de 0% a
100%, e a regra explícita de barra cinza fraca com "0%" quando não há nenhum registro (incluindo os
meses futuros de um semestre em curso).

Quatro pontos ficaram em aberto e foram fechados com o usuário via `AskUserQuestion` antes de
implementar (todas as opções recomendadas foram escolhidas):

1. **Critério de User Story/Technical Story**: reaproveitar exatamente o mesmo critério já usado pelos
   quadrantes homônimos do Report F4P — Technical Story = tipo fixo `"technical story"` (§12.5);
   User Story = `CFG.f4p.usTypes` (§12.8, configurável, padrão `"user story"`) — em vez de criar uma
   configuração paralela e independente.
2. **Como definir "tipos bug"**: nova configuração própria `CFG.act.bugTypes` (padrão `["bug",
   "internal bug", "external bug"]`), no mesmo padrão de toda outra lista de tipos do portal
   (`f4p.types`/`usTypes`/`epiTypes`/`effTypes`) — configurável em Configurações › Configurações
   gerais, em vez de fixa no código.
3. **Universo do balde "demais"**: qualquer tipo entregue no mês que não seja bug, User Story nem
   Technical Story — um balde genuinamente residual, não restrito aos tipos configurados no CT
   (`CFG.f4p.types`, usado pelo Vazão/CycleTime do Report F4P).
4. **Transparência por fatia**: as três porcentagens de cada mês são clicáveis **separadamente**, cada
   uma abrindo só os itens daquele tipo, naquele mês — mesmo padrão de transparência por número já
   usado no resto do portal (`f4pItemsModal`), em vez de um clique único agregando os três tipos.

## Implementação

`src/js/24-actionable.js`:

- `actBugTypes()`: lê `CFG.act.bugTypes`, normalizado.
- `actDistMonths(st)`: sempre os **6 meses inteiros** do semestre selecionado
  (`f4pSemStart(sem)` até 5 meses depois) — diferente de `actBurnupMonths` (Burnup Reserva), que para
  em "hoje" num semestre em curso. Aqui os meses ainda não decorridos entram de propósito, para o
  usuário ver o que falta ao longo do período, não só o que já aconteceu.
- `actDistItems(team, month)`: itens do time, categoria de fluxo Vazão, `o.deploy` dentro do mês, de
  qualquer tipo exceto os tipos de `actBugTypes()`.
- `actDistBuckets(team, month)`: separa esses itens em `us` (`CFG.f4p.usTypes`), `ts` (tipo fixo
  `"technical story"`) e `demais` (o resto) — partição exata, sem sobreposição nem exclusão além dos
  bugs (já fora do conjunto de entrada).
- `actDistData(team, st)`: um registro por mês com `total` e as três porcentagens (`usPct`/`tsPct`/
  `demaisPct`), calculadas só quando `total > 0` (senão ficam em 0 — o mês vira a barra cinza).
- `actDistRow`/`actDistCard`: renderização em HTML/CSS (flexbox), não SVG como os outros dois
  quadrantes — uma barra 100% empilhada por mês, com uma fatia `<button>` por bucket não-vazio
  (`flex: 0 0 <pct>%`), rótulo "XX,XX%" (nova função `dec2`, mesmo padrão de `dec1` já existente:
  2 casas decimais, vírgula em vez de ponto). Um mês com `total === 0` — sem nenhuma entrega, ou todas
  bug — renderiza uma única fatia cinza fraca (`.act-dist-none`, não clicável) ocupando a barra inteira,
  rotulada "0,00%": essa é a mesma tratativa dos meses futuros de um semestre em curso (eles também têm
  `total === 0`, por não terem itens entregues ainda), então nenhuma lógica separada de "é mês futuro?"
  foi necessária — o comportamento cai naturalmente do critério de amostra vazia.
- Dispatcher de clique de `#actBody`: nova entrada para `[data-act-dist-set]` (valores `us`/`ts`/
  `demais`), recalculando `actDistBuckets` para o time e mês do botão clicado e abrindo `f4pItemsModal`
  com a lista exata.

`src/js/01-configuracao-e-regras.js`: `CFG.act.bugTypes`, com o mesmo padrão de normalização das
demais listas de tipo do Report F4P (`normCfg`).

`src/js/19-tela-configuracoes.js`: nova seção "Actionable" na aba Configurações gerais, com a lista de
tipos (`typesFound()`, mesma fonte usada pelas listas do Report F4P) marcáveis como bug.

`src/js/02-utilitarios.js`: nova `dec2(x)`, análoga a `dec1` já existente, mas com 2 casas decimais —
pedido explícito do usuário (diferente do inteiro sem casas decimais usado pelo quadrante Eficiência de
fluxo do Report F4P, §12.9).

## Por que HTML/CSS em vez de SVG

Os outros dois quadrantes do Actionable (CycleTime, Burnup Reserva) usam SVG (`<svg class="act-chart">`)
por serem gráficos de pontos/linhas com eixos numéricos contínuos. Aqui, cada barra é uma sequência de
poucos retângulos com texto centralizado dentro — um layout naturalmente resolvido por flexbox
(`flex: 0 0 <pct>%` em cada fatia dentro de uma barra `display:flex`), sem o texto de um `<svg:text>`
ficar sujeito aos problemas de centralização/clipping dentro de uma largura dinâmica. Os elementos
clicáveis também ficam naturalmente acessíveis como `<button>` reais, em vez de `<rect>`/`<text>` com
`tabindex` manual.

## Testes

`tests/test_actionable.py`: nova seção com testes cobrindo — os 6 meses inteiros do semestre mesmo em
curso (diferente do Burnup); classificação User Story/Technical Story/demais; exclusão de tipos bug
(padrão e configurado); mês sem nenhum registro (vazio, ou só bug) mostrando a barra cinza com 0,00%;
arredondamento de porcentagem para 2 casas decimais (caso de dízima, 33,33%); clique em cada uma das
três fatias abrindo só os itens daquele tipo naquele mês; a fatia "sem registro" não é clicável;
aparição no painel com a legenda; persistência/exportação de `CFG.act.bugTypes`. O teste
`test_quadrantes_3_e_4_mostram_em_definicao` foi renomeado para `test_quadrante_4_mostra_em_definicao`
e ajustado (só o último quadrante permanece "em definição").
