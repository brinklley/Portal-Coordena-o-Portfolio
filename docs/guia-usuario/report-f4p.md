# Report F4P — guia do usuário

## O que é

O Report F4P é a grade de 8 indicadores (quadrantes) de "Business Outcomes – Productivity", sempre
mostrando **todos os times carregados de uma vez**, lado a lado — diferente da Visão Analítica e do
Actionable, que mostram um time por vez. É a tela para comparar times entre si num mesmo semestre:
quem está dentro da faixa esperada de CycleTime, quem tem itens Urgentes acima da meta, quanto cada
time já entregou do que reservou no roadmap, e assim por diante.

## Como habilitar

A aba "Report F4P" usa **a mesma regra de habilitação da Visão Analítica**: precisa de **Time** **e**
**Roadmap** (interno ou executivo) selecionados juntos nos filtros. Também fica desabilitada se o
semestre escolhido ainda não começou.

**Atenção a uma pegadinha comum**: mesmo que o filtro de **Time** seja obrigatório para habilitar a
aba, ele **não restringe o conteúdo do relatório** — uma vez aberto, o Report F4P sempre mostra **os 4
times carregados**, não só o selecionado. O filtro de Time, aqui, só serve para liberar o acesso à
aba; para ver só um time, use a Visão Analítica ou o Actionable.

## Os 8 quadrantes

1. **CycleTime** (reserva vs. atual): compara o CycleTime máximo esperado do time (Reserva) com o P95
   real da amostra de itens concluídos no período (Atual). P95 acima da reserva → seta vermelha
   para baixo; dentro → seta verde para cima.
2. **Variabilidade** (min/atual/max): quanto o P95 varia em relação ao P50 da mesma amostra — mede
   consistência, não só velocidade.
3. **Urgente** (meta vs. realizado): conta itens com a tag de Classe de Serviço Expedite (configurável,
   padrão "URGENTE") contra uma meta por time, no período exato do semestre selecionado — item aberto
   conta sempre; item fechado só conta se a saída caiu dentro do semestre.
4. **Technical Story** (meta vs. realizado): mesma lógica do Urgente, mas conta pelo **tipo** do item
   (Technical Story), com meta padrão de 6 por time, e só considera itens **já entregues** (categoria
   de fluxo Vazão) — um item aberto, não importa há quanto tempo, nunca conta aqui.
5. **Vazão** (reserva vs. reserva entregue vs. realizado): três números sobre entrega — "Reserva" é a
   mesma capacidade do roadmap da Visão Analítica (itens com a tag, de qualquer status); "Reserva
   entregue" é o subconjunto da Reserva já em Vazão (qualquer data de entrega); "Realizado" é tudo que
   foi entregue dentro do período exato do semestre, com ou sem a tag.
6. **Roadmap – Épicos** (roadmap vs. roadmap entregue vs. atual): o único quadrante que conta **épicos**
   (não itens de time) — quantos épicos estão no roadmap do semestre, quantos já fecharam, e quantos
   fecharam especificamente dentro do período exato do semestre.
7. **User Story** (reservado vs. planejado outro semestre vs. não planejado): mesma régua de "entregue"
   do Vazão/Technical Story, mas só para itens do tipo User Story, divididos por terem (ou não) a tag
   de reserva, e — entre os que têm — se o épico vinculado está comprometido com **este** semestre ou
   com outro.
8. **Eficiência de fluxo** (min/atual/max): Touch Time ÷ (Touch Time + Waiting Time) × 100, somando
   todos os itens do fluxo do time no período — mede quanto do tempo total é trabalho de verdade
   (Touch) versus fila de espera (Waiting, colunas marcadas como tal em Configurações).

## Perguntas frequentes ("não está batendo com o que eu esperava")

### "Selecionei o Time, mas o menu continua desabilitado. Por quê?"

Falta o **Roadmap**. A aba só habilita com Time **e** Roadmap (interno ou executivo) selecionados
juntos. Veja "Como habilitar" acima.

### "Selecionei um time específico, mas o relatório mostra todos os times mesmo assim"

Por desenho: o filtro de Time só **libera o acesso** à aba (a mesma exigência da Visão
Analítica/Actionable), mas **não filtra o conteúdo** do Report F4P — ele sempre mostra todos os 4
times carregados lado a lado, para permitir comparação entre eles. Se você quer ver só um time, use a
Visão Analítica ou o Actionable.

### "Technical Story (ou User Story) mostra 0, mas eu vejo itens desse tipo abertos no quadro"

Esses dois quadrantes só contam itens **já entregues** (categoria de fluxo Vazão) dentro do período
exato do semestre selecionado. Um item aberto — em Backlog, Discovery ou WIP — nunca conta no
Realizado, não importa há quanto tempo está aberto. Essa é uma régua diferente da do quadrante
Urgente, que conta item aberto normalmente.

### "A soma de Vazão não bate com Technical Story + User Story. O que isso significa?"

É um alerta de propósito, não um bug: um aviso aparece no topo do painel quando a soma **Technical
Story Realizado + User Story Planejado (Reservado + Planejado outro semestre) + User Story Não
planejado** não bate com o **Vazão Realizado** do mesmo time. Como os três quadrantes usam listas de
tipo configuráveis separadamente (`CFG.f4p.types` para Vazão/CycleTime, um tipo fixo para Technical
Story, `CFG.f4p.usTypes` para User Story), uma mudança de configuração num dos três sem ajustar os
outros produz essa divergência — o aviso mostra os números exatos de cada lado para investigar a
configuração de tipos.

### "Não entendo a diferença entre 'Reserva' e 'Reserva entregue' no quadrante Vazão"

**Reserva** é tudo que está comprometido com o roadmap deste semestre (tag de capacidade + épico
comprometido), **em qualquer status** — inclui itens ainda não entregues. **Reserva entregue** é só o
subconjunto da Reserva que já está em Vazão, **qualquer que seja a data** de entrega (mesmo entregue
fora do período exato do semestre). Já o **Realizado** é outra conta: tudo que foi entregue dentro do
período exato do semestre, com ou sem a tag de capacidade — pode incluir itens que a Reserva nem
considera.

### "Um épico aparece no Roadmap – Épicos de um time que eu não esperava"

O vínculo épico↔time é sempre pelos **itens filhos**: um épico só conta para um time se esse time
tiver pelo menos um item operacional vinculado a ele — mesmo que o épico tenha Target Date no semestre
certo ou esteja ligado à iniciativa certa, se nenhum item dele é desse time, ele não entra na conta
daquele time (entra só no(s) time(s) que de fato têm item vinculado).

### "Eficiência de fluxo mostra '--' em vez de uma porcentagem"

Acontece quando não há nenhum item do time no período considerado (Touch Time + Waiting Time = 0) —
não é "0% de eficiência", é ausência de dado para calcular. Confira se o time tem itens no fluxo dentro
da janela de datas do quadrante (os últimos N meses, ou o semestre exato se já encerrado).

## Cenários

### Habilitação depende de Time + Roadmap, mas o conteúdo ignora o Time

**Cenário: Time sem Roadmap não habilita a aba**
- Dado que nenhum Roadmap (interno nem executivo) está selecionado
- Quando o usuário seleciona um Time
- Então a aba "Report F4P" continua desabilitada

**Cenário: aba habilitada mostra todos os times, não só o selecionado**
- Dado que o usuário selecionou o Time "CORE" e um Roadmap
- Quando o Report F4P é aberto
- Então os 8 quadrantes mostram números para **todos** os times carregados (CORE, IB, BO, MOBILE),
  não só CORE

### Technical Story/User Story só contam item já entregue

**Cenário de sucesso: item entregue dentro do período conta no Realizado**
- Dado um item do tipo Technical Story entregue (categoria Vazão) dentro do período exato do semestre
  selecionado
- Quando o quadrante Technical Story calcula o Realizado
- Então esse item entra na contagem

**Cenário de comportamento inesperado: item aberto não conta, mesmo há meses no fluxo**
- Dado um item do tipo Technical Story em WIP há vários meses, ainda não entregue
- Quando o quadrante Technical Story calcula o Realizado
- Então esse item **não** entra na contagem — só itens já em Vazão contam, independente de quanto
  tempo um item aberto está parado

## Regras de negócio relacionadas

- `docs/regras-de-negocio.md` §12 (Report F4P, com uma subseção por quadrante — §12.1 a §12.9).
- Especificação completa de produto: `docs/backlog/report-f4p.md`.
- Decisões: `docs/decisoes/0011` a `0031` (uma por quadrante/ajuste), e as mais recentes que ainda se
  aplicam a este painel — `0043`, `0048`, `0049`, `0051`, `0052`.
- Detalhe exaustivo de cobertura de teste: [`docs/testes/report-f4p/README.md`](../testes/report-f4p/README.md)
  e os arquivos por quadrante na mesma pasta.
