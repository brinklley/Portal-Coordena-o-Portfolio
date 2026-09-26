# 0025 — Report F4P: Quadrante 6, Roadmap – Épicos (roadmap vs. roadmap entregue vs. atual)

## Contexto

Com Vazão implementado e ajustado (decisões `0022`–`0024`), o usuário pediu o próximo quadrante do
grupo "Have a target & are temporary": Roadmap – Épicos, descrevendo as regras em texto e anexando um
mockup do slide de referência (tabela com valores diferentes por time, ex.: CORE "10|05|04 ▲", MOBILE
"07|06|06 ▲") e um recorte do cabeçalho do quadrante. O pedido inicial foi cancelado pelo próprio
usuário antes de qualquer mudança ("cancele o último comando") e reenviado logo em seguida com a regra
do "Atual" bem mais detalhada — a versão reenviada é a que este documento registra.

## Decisões

1. **Nível de dados**: diferente de todos os quadrantes anteriores (CycleTime, Variabilidade, Urgente,
   Technical Story, Vazão — todos sobre `S.model.ops`, os itens operacionais dos times), este quadrante
   opera sobre os **cards do quadro de Épicos** (`S.model.epis`). "Fechado" aqui é a **última coluna do
   próprio quadro de Épicos** (`e.st === S.model.stages.epi.length - 1`, função `f4pEpiClosed`) — um
   conceito de posição no board, não a categoria de fluxo operacional (`catOf`) de nenhum time, que não
   existe neste nível (o board de Épicos não tem Discovery/WIP/Vazão, só as colunas que o cliente
   configurar). Para ter uma "data de fechamento" comparável a `o.deploy`, `buildModel` (`src/js/
   04-modelo.js`) passou a computar `e.stDate` (a data da coluna atualmente ocupada pelo épico), do
   mesmo jeito que já fazia para `o.stDate` nos itens operacionais.

2. **Por time, apesar de a regra não mencionar times explicitamente**: o texto do pedido nunca fala em
   "por time", mas o mockup mostra valores diferentes em cada coluna — confirmando que, como todo o
   resto do Report F4P, o quadrante é por time. Um épico "pertence" a um time se tiver pelo menos um
   item operacional daquele time vinculado (`f4pEpiHasTeam`, mesma ideia de `S.model.teams`/colunas do
   quadro, aplicada por épico).

3. **Tipos de épico considerados**: nova configuração própria, `CFG.f4p.epiTypes` (padrão **`["epic"]`**
   — "Epic"), **independente** de `CFG.f4p.types` (que é dos itens operacionais dos times, usado por
   CycleTime/Variabilidade/Vazão). O pedido fala em "artefatos mapeados nas configurações" para este
   quadrante especificamente, então mereceu campo e checkbox próprios em Configurações › Report F4P
   (`src/js/19-tela-configuracoes.js`), em vez de reaproveitar a lista existente.

4. **"Roadmap"**: cards do conjunto acima (tipo + item do time) dentro do semestre selecionado no filtro
   (Roadmap interno tem prioridade sobre o executivo, igual ao resto do Report F4P — `f4pSemester`),
   contando **todos os estágios** (aberto ou fechado), únicos por ID. O critério de "estar no semestre"
   muda conforme qual Roadmap está ativo — pedido explícito do usuário, os dois métodos usam critérios
   diferentes:
   - **Roadmap Interno** selecionado: usa o **Target Date do próprio épico** (`e.interno`, calculado no
     build do modelo) — o vínculo com a iniciativa é irrelevante aqui.
   - **Roadmap Executivo** selecionado: sobe até a iniciativa e desce de novo — **Iniciativa** (cujo
     `AnoSemestreRoadmap`/`i.exec` é o semestre selecionado) → **Release** → **Épico**, usando o vínculo
     do épico com a iniciativa — o Target Date do próprio épico é irrelevante aqui.

5. **"Roadmap entregue"**: subconjunto do "Roadmap" acima (mesmo critério interno/executivo) que já está
   **fechado** (`f4pEpiClosed`).

6. **"Atual"**: a parte mais detalhada do pedido reenviado — épicos do conjunto de dados (tipo + item do
   time) que estão **fechados** e cujo `e.stDate` cai dentro do **período exato do semestre selecionado**
   (`f4pExactSemesterWindow`, a mesma janela do Urgente/Technical Story/Vazão), **independente** do
   critério do Roadmap: não olha o Target Date do próprio épico (pedido explícito: "sem levar em
   consideração o Target Date no filtro", para o caso Interno) nem o vínculo com a iniciativa (pedido
   explícito: "não devem ser levados em consideração o vínculo com as iniciativas", para o caso
   Executivo) — a mesma lógica vale para os dois roadmaps. É uma contagem **independente**, não um
   subconjunto do "Roadmap" (`f4pAtualEpis` não reaproveita `f4pRoadmapEpis`, é um filtro direto sobre
   `S.model.epis`).

7. **Tendência**: o usuário pediu para seguir "as mesmas regras inspiracionais do quadrante Vazão
   (reserva vs. realizado)... adaptando para que seja utilizado o fluxo de épicos e os artefatos EPIC na
   lógica" — sem novos exemplos numéricos exatos desta vez. Interpretação adotada, espelhando a decisão
   `0023` ponto a ponto: separa o "Atual" por mês corrido dentro do período (só os meses já decorridos,
   no semestre em curso) e compara o **mês corrente mais os épicos do Roadmap ainda abertos**
   (`f4pRoadmapAbertosEpis` — o equivalente ao "WIP" operacional do Vazão, já que o board de Épicos não
   tem uma categorização Discovery/WIP/Vazão própria: "ainda não chegou na última coluna" é a definição
   mais direta de "em progresso" neste nível) contra a **média** (arredondada sempre para cima) dos
   meses anteriores. Sem meses anteriores para comparar, fica ◆.
   > Como no Vazão original (decisão `0022`, corrigida pela `0023`), esta é a parte com mais graus de
   > liberdade de interpretação — sem exemplos numéricos exatos para conferir contra, é o ponto mais
   > provável de precisar de um ajuste em uma rodada seguinte, assim que o usuário vir o quadrante em uso.

8. **Nome da primeira coluna**: o pedido original usa tanto "Reserva" (por analogia ao Vazão) quanto
   "Roadmap" (no texto e no mockup) para descrever a mesma contagem. O mockup e o cabeçalho anexado
   deixam claro que o rótulo correto é **"Roadmap"**, não "Reserva" — diferente do Vazão, aqui não existe
   uma "tag de capacidade" separando um subconjunto: o próprio conceito de "estar no roadmap" (pelo
   Target Date ou pelo vínculo com a iniciativa) já é a contagem inteira. O título do card em
   `F4P_QUADS.road` foi ajustado de "reserva vs..." para "roadmap vs..." para bater com o mockup.

9. **Transparência**: os três números (Roadmap, Roadmap entregue, Atual) são clicáveis e abrem a lista
   dos épicos exatos de cada contagem, mesmo padrão dos demais quadrantes (`gotoId` para navegar até o
   item). A coluna "Situação" da lista usa uma função própria (`f4pEpiSituacao`), diferente da
   `f4pItemSituacao` (categoria de fluxo por time) usada pelos quadrantes que operam sobre itens
   operacionais — aqui mostra a **coluna do próprio quadro de Épicos**, com a data de saída quando o
   épico estiver fechado. `f4pItemsModal` ganhou um terceiro parâmetro opcional (`situacaoFn`) para
   suportar as duas formas de item sem duplicar o modal.

## Consequências

- `src/js/01-configuracao-e-regras.js`: novo campo `CFG.f4p.epiTypes` (padrão `["epic"]`) em
  `cfgDefaults`/`normCfg`.
- `src/js/04-modelo.js`: novo campo `e.stDate` no objeto de épico (`buildModel`), calculado como a data
  da coluna atualmente ocupada — mesma lógica já usada para `o.stDate` nos itens operacionais.
- `src/js/19-tela-configuracoes.js`: nova lista de checkboxes para tipos de épico (`data-f4pepitype`,
  reaproveitando `typesByLevel("epi")`), com `readForm` coletando `d.f4p.epiTypes`.
- `src/js/23-report-f4p.js`: `f4pEpiTypeOk`, `f4pEpiClosed`, `f4pEpiHasTeam`, `f4pRoadmapEpis`,
  `f4pRoadmapEntregueEpis`, `f4pRoadmapAbertosEpis`, `f4pAtualEpis`, `f4pRoadmapTrend`,
  `f4pRoadmapEpiCell`, `f4pEpiSituacao`; `f4pItemsModal` generalizado com o parâmetro `situacaoFn`; novo
  atributo de clique no modal (`data-f4p-road-team`/`data-f4p-road-set`); `F4P_QUADS.road` marcado
  `done:true` com o título ajustado para "roadmap vs roadmap entregue vs atual".
- Testes em `tests/test_report_f4p.py` (seção "Quadrante 6 · Roadmap – Épicos"): branch interno (Target
  Date do próprio épico) e executivo (vínculo via iniciativa) isolados um do outro, "Roadmap entregue"
  como subconjunto fechado, independência do "Atual" em relação a ambos os critérios do Roadmap, filtro
  por tipo de épico configurável, filtro por vínculo com o time, as três direções de tendência
  (melhora/piora/estável) e o caso sem meses anteriores, clique nos três números com navegação até o
  item e Situação pela coluna do próprio quadro de Épicos, além dos testes de configuração (padrão e
  exportação de `epiTypes`).
- Documentação: `docs/regras-de-negocio.md` §12.7 (nova, renumerando "Demais quadrantes" para §12.8),
  `docs/backlog/report-f4p.md`, `docs/configuracoes.md`, `docs/telas.md`, `CLAUDE.md` (próxima tarefa do
  Report F4P, agora só Eficiência de fluxo ou User Story).
