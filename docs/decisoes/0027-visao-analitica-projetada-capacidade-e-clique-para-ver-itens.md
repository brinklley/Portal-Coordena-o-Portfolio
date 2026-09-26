# 0027 — Visão analítica: Projetada/Capacidade como soma por épico, reservado por linha e clique para ver itens

## Contexto

Ainda no mesmo PR do Quadrante 6 do Report F4P, o usuário pediu, em paralelo, uma correção na **Visão
analítica** (painel existente desde antes do Report F4P, `docs/regras-de-negocio.md` §10), anexando um
print anotado do painel com setas ligando os números "Capacidade" e "Projetada" do cabeçalho às
quantidades ("US") de cada linha de épico, para deixar explícito que um número deve ser a soma do outro.

## Decisões

1. **Projetada = soma do QTD de cada épico da tabela.** Antes, `anData()` calculava `proj` como uma
   contagem independente sobre `S.V.visOp` (itens visíveis do time), separada do que cada linha da
   tabela mostra (`epiMetrics(e, team).recs`, filtrado pelos tipos do CT). Na prática os dois cálculos
   davam o mesmo número (o mesmo filtro de time+tipo se aplica aos dois), mas eram **duas fontes de
   verdade independentes** — um risco de divergência silenciosa se um dos dois lados mudasse sem o outro
   (foi exatamente esse tipo de duplicação que o usuário pediu para eliminar). `anData()` agora computa
   `itens` por linha primeiro e deriva `proj = soma dos itens de cada linha` — uma fonte só.
2. **Capacidade = soma do "reservado" de cada épico da tabela**, mesmo raciocínio: cada linha agora
   calcula `reservados` (subconjunto de `itens` com a tag de capacidade, `CFG.anTag`) e `cap` é a soma
   disso, não mais uma contagem à parte.
3. **Reservado por linha, visível na tabela**: a linha do épico agora mostra a quantidade reservada logo
   após a descrição do épico (antes do "– X US"), ex.: `[EP][123] Nome do épico 2 reservados – 6 US`.
   Sempre mostrado (mesmo "0 reservados"), para a coluna ficar previsível linha a linha.
4. **Clique para ver os itens** (mesma transparência já estabelecida no Report F4P — decisões `0016`,
   `0022`): os números "Capacidade" e "Projetada" do cabeçalho viraram botões (`data-an-items="cap"` /
   `"proj"`) que abrem um modal com a lista exata de itens de cada soma — ID, título e Situação. Em vez
   de duplicar o modal, reaproveitei `f4pItemsModal`/`f4pItemSituacao` do Report F4P (`src/js/
   23-report-f4p.js`): são funções genéricas, sem estado específico do F4P, e a Situação já mostra
   exatamente o pedido (Backlog/Discovery/WIP/Vazão, com a data de saída quando Vazão). Isso também
   exigiu generalizar o clique de navegação do modal (`data-f4p-go`), que antes só fechava o painel do
   Report F4P (`closeF4P`) — agora fecha **qualquer um dos dois** painéis que esteja aberto (Report F4P
   ou Visão analítica), já que o mesmo modal passou a ser usado pelos dois.
5. **Cópia para PowerPoint/Excel** (`anCopy`): os novos botões do cabeçalho são convertidos em texto
   simples na cópia, igual aos demais botões já tratados por essa função; o destaque em `<mark>` de
   "Projetada acima da Capacidade" foi mantido **fora** do botão (envolvendo-o), para não se perder
   quando o botão vira texto (a lógica de cópia usa `button.textContent`, que descartaria a marcação se
   ela estivesse dentro do próprio botão).

## Consequências

- `src/js/15-visao-analitica.js`: `anData()` reescrita (fonte única para Projetada/Capacidade, novo campo
  `reservados` por linha, `projItems`/`capItems` expostos para o modal); nova linha "reservado" na
  tabela; novo tratamento de clique (`data-an-items`) reaproveitando `f4pItemsModal`.
- `src/js/23-report-f4p.js`: o clique de navegação do modal de itens (`data-f4p-go`) agora fecha F4P e/ou
  Analytics, o que estiver aberto.
- `src/styles.css`: nova classe `.an-table .res` (badge do "reservado" por linha).
- Testes novos: `tests/test_visao_analitica.py` (arquivo novo — a Visão analítica não tinha testes
  dedicados antes): Projetada e Capacidade batendo com a soma das linhas, tag de capacidade
  configurável, badge "reservado" na linha, clique na Capacidade mostrando só os itens com a tag, clique
  na Projetada mostrando todos com a Situação (Vazão com data), e clique num item do modal fechando o
  painel e navegando até o item.
- Documentação: `docs/regras-de-negocio.md` §10, `docs/telas.md`.
