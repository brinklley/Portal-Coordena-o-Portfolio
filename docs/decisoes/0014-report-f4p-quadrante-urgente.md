# 0014 — Report F4P: Quadrante Urgente (meta vs. realizado)

## Contexto

`docs/backlog/report-f4p.md` deixava o Quadrante Urgente (gestão da Classe de Serviço Expedite) "em definição", com uma lista de perguntas em aberto. O usuário respondeu num brainstorm; esta decisão registra as respostas e uma limitação técnica de dados que exigiu uma escolha específica de como aplicá-las.

## Decisões

1. **O que conta como "urgente"**: itens com uma tag configurável — não fixa na tag "URGENTE" — representando a Classe de Serviço Expedite. Nova configuração `CFG.f4p.expediteTag` (Configurações › Report F4P), um dropdown com as tags já cadastradas (`CFG.tags`), padrão a tag "URGENTE" (`id:"urgent"`). Ao contrário de CycleTime/Variabilidade, **conta itens de qualquer tipo** — não usa `CFG.f4p.types`.

2. **Meta**: número inteiro configurável **por time** (`CFG.f4p.teams[time].urgentMeta`, igual ao padrão já usado para a variabilidade mínima/máxima), representando o teto de itens Expedite aceitável no semestre. Sem meta cadastrada para um time, o quadrante mostra "--" e não colore o Realizado (nem verde, nem vermelho) — não há um padrão numérico sensato para "aceitável", ao contrário da Variabilidade (1.5–3.5).

3. **Realizado — limitação de dados e a solução**: o usuário pediu para contar "itens com a tag, não importando o estado no fluxo" — mas isso só é reconstruível com precisão para o **semestre em curso**, porque o portal só enxerga o estado *atual* das tags (não existe histórico de "quando esta tag foi aplicada a este item"). Perguntado especificamente sobre semestre já encerrado, o usuário decidiu: usar a contagem de itens **fechados** (têm `o.deploy`, a mesma data de saída do CT) dentro do período daquele semestre. Ou seja:
   - Semestre em curso (ou nenhum reconhecido no filtro): contagem **ao vivo** — todos os itens com a tag, abertos ou fechados, sem filtro de data.
   - Semestre já encerrado: só os itens com a tag cujo `o.deploy` caiu dentro do período do semestre.
   - Semestre futuro: painel inteiro desabilitado (regra já existente, decisão `0013`).

4. **Cor do Realizado**: vermelho quando ultrapassa a Meta, verde quando está na meta ou abaixo — confirmado como o usuário descreveu ("a meta é ficar abaixo da meta").

5. **Tendência (▲/▼/◆)**: o usuário pediu uma seta baseada nos "últimos 6 meses", sempre relativa a hoje — **independente do semestre selecionado no filtro** para a Meta/Realizado (esses dois sinais respondem a perguntas diferentes: "estamos dentro do teto deste semestre?" vs. "a tendência recente é de alta ou baixa?"). Adotado: comparar itens Expedite **fechados** nos últimos 3 meses contra os 3 meses anteriores a esses (mesma restrição de dados do item 3 — só dá pra comparar histórico usando datas de fechamento, itens ainda abertos não entram nessa conta). Sem margem de tolerância: mais no trimestre recente → ▲; menos → ▼; exatamente igual → ◆.

6. **Cor da seta de tendência**: neutra (cinza, classe `.f4p-trend`), não segue o vermelho/verde da Meta — a seta indica só direção, a cor de alerta já está no número do Realizado.

## Consequências

- Nova configuração no CFG: `f4p.expediteTag` (string, id de tag) e `f4p.teams[time].urgentMeta` (inteiro ≥ 0, independente de `min`/`max`). Ambos entram automaticamente em exportação/importação (mesma serialização do resto do `CFG`).
- `src/js/23-report-f4p.js`: `f4pExpediteOps`, `f4pUrgentRealizado`, `f4pUrgentTrend`, `f4pUrgentCell`.
- `src/js/01-configuracao-e-regras.js`: `f4pUrgentMetaOf`, `f4pExpediteTag`, `f4pTagName`.
- Testes em `tests/test_report_f4p.py` usam itens sintéticos adicionados ao `Map` de operações (times fictícios como `F4P_TREND_UP`), sem tocar nos itens que já existem na fixture — mesmo cuidado de outras decisões, para não quebrar referências que os épicos da fixture têm para os próprios itens.
- Se no futuro o portal passar a guardar histórico de mudança de tags, a contagem do semestre encerrado (item 3) e a tendência (item 5) podem ser refeitas usando a data real de aplicação da tag, em vez da data de fechamento do item — hoje é a melhor aproximação possível com os dados disponíveis.
