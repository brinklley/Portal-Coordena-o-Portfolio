# 0022 — Report F4P: Quadrante 5, Vazão (reserva vs. realizado)

## Contexto

Com Urgente, Technical Story e a Situação por categoria de fluxo implementados (decisões `0014`–`0020`), o usuário pediu o próximo quadrante: Vazão, descrevendo as regras em um brainstorm e anexando o mockup do slide de referência.

## Decisões

1. **Filtro de dados**: itens dos **tipos configurados para o CT** (`CFG.f4p.types` — o mesmo campo já usado por CycleTime/Variabilidade, padrão User Story e Technical Story), **não** uma configuração nova — o usuário pediu explicitamente que os artefatos default fossem "User Story e Technical Story", que já é o padrão desse campo.

2. **O que conta como "entregue"**: mesmo critério do Technical Story (decisão `0020`) — categoria de fluxo atual **Vazão** (`catOf`), com `o.deploy` preenchido. Itens em Nenhum (Backlog), Discovery ou WIP não contam.

3. **Janela**: o usuário pediu "o range a partir do primeiro dia inicial do semestre e termina com o último dia do semestre selecionado" — a mesma regra do Urgente/Technical Story, `f4pExactSemesterWindow` (decisões `0017`/`0018`), reaproveitada sem alterações: sempre o período exato do semestre selecionado no filtro (Roadmap interno tem prioridade sobre o executivo), em curso ou já encerrado.

4. **Reserva vs. Realizado**: diferente de Meta vs. Realizado (Urgente/Technical Story), aqui os dois lados são contagens de itens, não uma meta configurada:
   - **Realizado** = todos os itens do conjunto do item 1–3 acima.
   - **Reserva** = subconjunto do Realizado cujo `o.tags` inclui a **tag que marca a capacidade do roadmap** — reaproveitando `CFG.anTag` (padrão "ROADMAP"), a mesma configuração já usada pela Visão analítica (§10) para a coluna "Capacidade", casada da mesma forma (`o.tags.map(norm).includes(norm(CFG.anTag))`, não por um id de tag cadastrada — `anTag` é um texto livre, diferente da tag Expedite do Urgente). O usuário pediu para reaproveitar "a configuração já existente", então nenhum campo novo foi criado.
   - Por construção, Reserva **nunca é maior** que Realizado (é um filtro sobre o mesmo conjunto, confirmando o que o usuário descreveu).

5. **Sem indicador de cor**: ao contrário de Urgente/Technical Story, não há meta/teto configurável aqui — o usuário não descreveu uma regra de "acima é ruim", e o mockup mostra os dois números em texto neutro. Os botões usam a classe `.f4p-real` (negrito, sublinhado, clicável) sem `.f4p-good`/`.f4p-bad`, então ficam na cor de texto padrão.

6. **Tendência**: o usuário pediu "mapear uma visão de realizado separado por meses... comparar do primeiro mês em direção ao último se o último mês está sinalizando, em comparação com os anteriores, melhora/piora/estabilidade". Interpretação adotada — a mais literal para "o último mês comparado com os anteriores": separar o Realizado em baldes por mês corrido dentro do período do semestre e comparar a contagem do **último mês** contra a **média** dos meses anteriores do mesmo período: mais que a média → ▲, menos → ▼, igual → ◆. Para um semestre **em curso**, só os meses já decorridos entram no cálculo — meses futuros do semestre não têm itens possíveis e, se contassem como zero, enviesariam a tendência para "piora" logo no início de um semestre novo (o mesmo tipo de cuidado já tomado com a janela do Urgente, decisão `0017`). Sem meses anteriores para comparar (semestre com um único mês decorrido), a tendência fica ◆ (neutra), não "sem dado".
   > Esta é a parte da regra com mais graus de liberdade de interpretação na descrição original; se não for exatamente o que o usuário tinha em mente, é o ponto mais provável de precisar de um ajuste — documentado aqui explicitamente para facilitar encontrar e corrigir.

7. **Transparência**: tanto a Reserva quanto o Realizado são clicáveis e abrem a lista dos itens exatos de cada contagem — diferente do Urgente/Technical Story, cuja Meta é um número configurado (não clicável, não tem uma lista de itens por trás).

## Consequências

- `src/js/23-report-f4p.js`: `f4pVazaoOps`, `f4pCapacityTag`, `f4pVazaoReservaItems`, `f4pVazaoRealizadoItems`, `f4pVazaoTrend`, `f4pVazaoCell`; dois novos atributos de clique no modal (`data-f4p-vazao-reserva-team`, `data-f4p-vazao-realizado-team`).
- Nenhuma configuração nova: reaproveita `CFG.f4p.types` (tipos) e `CFG.anTag` (tag de capacidade), ambos já existentes. `src/js/19-tela-configuracoes.js` só ganhou texto de ajuda atualizado explicando o reaproveitamento.
- Testes em `tests/test_report_f4p.py` (seção "Quadrante 5 · Vazão"): contagem por tipo+entrega, Reserva como subconjunto pela tag (inclusive tag reconfigurada), itens em Backlog/Discovery/WIP ignorados, fronteira do início do semestre, semestre encerrado, as três direções de tendência (melhora/piora/estável) e o caso sem meses anteriores, clique na Reserva e no Realizado com navegação até o item.
- Documentação: `docs/regras-de-negocio.md` §12.6 (nova), `docs/backlog/report-f4p.md`, `docs/configuracoes.md`, `docs/telas.md`, `CLAUDE.md` (próxima tarefa do Report F4P).
