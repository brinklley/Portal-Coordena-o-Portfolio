# 0030 — Report F4P: Quadrante 7, User Story (planejado vs. não planejado)

## Contexto

Com Roadmap – Épicos implementado e reforçado (decisões `0025`/`0026`), o usuário pediu o último
quadrante de contagem de itens do Report F4P: User Story (planejado vs. não planejado), descrevendo as
regras em texto e anexando o mockup do slide de referência. O pedido incluiu, de forma inédita entre os
quadrantes deste painel, uma exigência explícita de **validação cruzada**: os números de User Story
devem, somados aos de Technical Story, bater exatamente com o Realizado do Vazão — com um exemplo
numérico exato (time MOBILE: 38 no Vazão Realizado = 27 Technical Story + 4 User Story planejado + 7
User Story não planejado) e o pedido de sinalizar no próprio relatório quando essa soma divergir.

## Decisões

1. **Filtro de dados**: itens dos **tipos configurados para este quadrante** (`CFG.f4p.usTypes`,
   configuração própria — padrão `["user story"]`), cuja categoria de fluxo atual seja **Vazão**
   (`catOf`, mesmo critério de "entregue" do Technical Story/Vazão), com `o.deploy` dentro do
   `f4pExactSemesterWindow` (mesma janela do Urgente/Technical Story/Vazão/Roadmap-Épicos). O pedido diz
   "somente os artefatos mapeados nas configurações. Por default os artefatos selecionados devem ser
   USER STORY" — uma lista **configurável com default próprio**, diferente de `CFG.f4p.types` (CT/
   Variabilidade/Vazão, default User Story + Technical Story) e de `CFG.f4p.epiTypes` (Roadmap – Épicos,
   nível de épico). Por isso ganhou seu próprio campo de configuração, não um reaproveitamento.

2. **O que "Planejado"/"Não planejado" significam**: o pedido define os dois de forma direta —
   Planejado = item com a tag de capacidade do roadmap (`CFG.anTag`, a mesma do Vazão/Visão analítica);
   Não planejado = item **sem** essa tag. Isso os torna uma **partição exata** do conjunto entregue
   (Planejado + Não planejado = todo o entregue, sem sobreposição) — diferente do par Reserva/Realizado
   do Vazão, onde Reserva é subconjunto de Realizado (Realizado é o total, com ou sem a tag). Implementado
   como dois filtros complementares (`.filter(hasTag)` / `.filter(o => !hasTag(o))`) sobre o mesmo
   `f4pUsOps(team, st)`, garantindo a partição por construção.

3. **Sobre a definição elaborada de "Roadmap" no pedido**: o texto do usuário inclui uma explicação
   detalhada de como "Roadmap" funciona (Target Date do épico no Interno; traversal Iniciativa → Release
   → Épico no Executivo — a mesma definição já usada no Roadmap – Épicos, decisão `0025`) antes de
   descrever o filtro de dados deste quadrante. Interpretação adotada: essa é uma explicação de
   **terminologia geral** (o que "roadmap selecionado" significa em todo o Report F4P — Interno tem
   prioridade sobre o Executivo, `f4pSemester()`), reaproveitada do texto anterior, e **não** um pedido
   para filtrar os itens de User Story por uma segunda camada de "épico está no roadmap" além da janela
   de datas. Três evidências sustentam essa leitura:
   - O exemplo numérico de validação (38 = 27+4+7) só bate se User Story usar exatamente o mesmo
     filtro de população que Vazão/Technical Story (tipo + `catOf` + `o.deploy` na janela) — nenhum dos
     dois quadrantes de referência filtra por "épico no roadmap".
   - Os números do Roadmap – Épicos (contagem de épicos, ex. "07" para MOBILE) e os de Vazão/Technical
     Story/User Story (contagem de itens, ex. "38"/"27"/"11") operam em escalas completamente
     desconectadas no mockup — não há relação proporcional entre eles que sugira um filtro compartilhado.
   - O quadrante não tem uma terceira coluna "Roadmap" (só Planejado/Não planejado) — diferente do
     Roadmap – Épicos, que tem exatamente essa contagem como um dos três números.
   > Se essa leitura não bater com o esperado ao usar o quadrante, é o ponto mais provável de precisar
   > de um ajuste — documentado aqui explicitamente, seguindo a mesma prática das decisões anteriores.

4. **Tendência**: mesma regra inspiracional do Vazão (decisão `0023`) — separa o total entregue
   (Planejado + Não planejado) por mês corrido dentro do período e compara o mês corrente somado aos
   itens hoje em WIP (dos tipos configurados) contra a média (arredondada pra cima) dos meses anteriores.

5. **Conferência cruzada** (pedido explícito, novo tipo de regra no Report F4P): como Vazão, Technical
   Story e User Story são três "recortes por tipo" do mesmo universo de itens entregues no período, a
   soma **Technical Story Realizado + User Story Planejado + User Story Não planejado** deveria sempre
   igualar o **Vazão Realizado**, por time — mas isso só é garantido por **convenção entre três
   configurações independentes** (`CFG.f4p.types`, o tipo fixo do Technical Story, `CFG.f4p.usTypes`),
   não por um vínculo estrutural no código (nada impede o usuário de, por exemplo, adicionar um terceiro
   tipo em `CFG.f4p.types` sem que nenhum dos outros dois quadrantes o cubra). Implementado como
   `f4pReconciliacao()` (recalcula os quatro números por time e compara) e `f4pReconciliacaoBanner()`
   (renderiza um aviso destacado no topo do painel, **só quando há divergência** — nenhum time mostra
   nada quando a soma bate), listando o time e os números exatos de cada lado da conta, para investigação
   pelo usuário em vez de números silenciosamente inconsistentes.

## Consequências

- `src/js/01-configuracao-e-regras.js`: novo campo `CFG.f4p.usTypes` (padrão `["user story"]`) em
  `cfgDefaults`/`normCfg`.
- `src/js/19-tela-configuracoes.js`: nova lista de checkboxes para tipos de User Story
  (`data-f4pustype`), com `readForm` coletando `d.f4p.usTypes`.
- `src/js/23-report-f4p.js`: `f4pUsTypes`, `f4pUsOps`, `f4pUsPlanejadoItems`, `f4pUsNaoPlanejadoItems`,
  `f4pUsWipCount`, `f4pUsTrend`, `f4pUsCell`, `f4pReconciliacao`, `f4pReconciliacaoBanner`; novo
  atributo de clique no modal (`data-f4p-us-team`/`data-f4p-us-set`); `F4P_QUADS.us` marcado
  `done:true`; banner de conferência renderizado no topo do corpo do painel.
- `src/styles.css`: nova classe `.f4p-recon` (banner de divergência).
- Testes em `tests/test_report_f4p.py` (seção "Quadrante 7 · User Story"): contagem por tipo+entrega,
  partição exata (soma bate, sem sobreposição), tag configurável, tipos configuráveis próprios, itens em
  Backlog/Discovery/WIP ignorados, fronteiras de semestre (atual e encerrado), as três direções de
  tendência (melhora/piora/estável) e o caso sem meses anteriores, clique no Planejado e no Não
  planejado com navegação até o item, além dos testes de configuração (padrão e exportação de
  `usTypes`). Seção separada para a conferência cruzada: o exemplo numérico exato do usuário
  (38 = 27+4+7), um caso de configuração divergente (confirmando que o aviso aparece com os números
  certos) e a ausência do aviso quando a soma bate.
- Documentação: `docs/regras-de-negocio.md` §12.8 (nova, renumerando "Demais quadrantes" para §12.9),
  `docs/backlog/report-f4p.md`, `docs/configuracoes.md`, `docs/telas.md`, `CLAUDE.md` (Report F4P
  completo, exceto Eficiência de fluxo).
