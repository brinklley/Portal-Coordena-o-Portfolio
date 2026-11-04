# 0073 — Burnup Reserva: selo de alerta no "Entregue" explica divergência com User Story do Report F4P

## Contexto

O usuário comparou o "Entregue" do Burnup Reserva (Actionable, §13.3) com o número "Reservado" do
quadrante User Story do Report F4P (§12.8) para o mesmo time (MOBILE) e o mesmo semestre, e viu números
diferentes: 6 no Burnup, 4 no Report F4P. Pediu pra investigar se havia um problema no cálculo.

Investigação: **não há bug** — os dois números medem coisas deliberadamente diferentes, cada uma já
documentada e testada no seu próprio quadrante:

- **Burnup Reserva · Entregue** usa o mesmo conjunto de "Reservados" da Visão analítica (§10): itens com
  a tag de capacidade do roadmap (`CFG.anTag`) nos épicos comprometidos, dos tipos de `CFG.ctTypes`
  (padrão User Story, Technical Story **e** Technical Solution), já entregues (Vazão) **em qualquer
  data** — mesmo fora do período exato do semestre (decisão `0058`).
- **User Story · Reservado** (Report F4P) usa só os tipos de `CFG.f4p.usTypes` (padrão só User Story),
  exige entrega **dentro do período exato do semestre** (`f4pExactSemesterWindow`), e exige que o épico
  vinculado tenha compromisso de roadmap batendo com o semestre selecionado (decisão `0043`).

O próprio usuário investigou e achou os dois itens da diferença: 1 item do tipo Technical Story (contado
no Burnup por `CFG.ctTypes`, fora do User Story por `CFG.f4p.usTypes`) e 1 item entregue em abril, antes
do início do semestre selecionado (contado no Burnup porque "Entregue" não exige a janela exata; fora do
User Story porque esse quadrante exige).

## Decisão

Em vez de unificar os dois critérios (quebraria a regra documentada e testada de cada quadrante — o
Burnup existe justamente para mostrar "tudo que foi reservado, incluindo o que saiu do período", e o
User Story do Report F4P existe para a conferência cruzada com Technical Story/Vazão, que depende da
janela exata), a melhoria pedida foi **tornar a diferença visível, item a item**, direto no modal que já
lista os itens do "Entregue": cada item ganha um pequeno selo de alerta (⚠, amarelo — mesma cor de
`.act-dist-late-icon`, decisão `0060`) quando ele **não** entraria no "Reservado" do User Story do Report
F4P, com um tooltip (`title`) explicando o motivo exato (tipo fora de `CFG.f4p.usTypes`, entrega fora do
período exato do semestre, ou os dois) — o usuário não precisa mais investigar manualmente item por item
pra entender a origem da discrepância entre as duas ferramentas/quadrantes.

`f4pItemsModal` (reaproveitado em Report F4P, Visão Analítica e Actionable) ganhou um 5º parâmetro
opcional, `warnFn(o)`: quando passado, abre uma coluna extra com o selo só nas linhas em que a função
devolve um texto; sem `warnFn` (todos os outros call sites existentes), a coluna nem aparece — mudança
aditiva, sem efeito nos demais modais.

## Consequências

- `src/js/23-report-f4p.js`: `f4pItemsModal` ganha o parâmetro `warnFn` opcional e a coluna de alerta
  condicional.
- `src/js/24-actionable.js`: `actBurnupEntregueWarn(o, st)` (os dois motivos de divergência com o
  "Reservado" do User Story); o clique em "entregue" do resumo do Burnup Reserva passa esse `warnFn` pro
  modal. Corrigido também um texto de ajuda esquecido da decisão `0071` (Distribuição Vazão por mês ainda
  dizia "Technical Story (tipo fixo)"; agora lista `CFG.f4p.tsTypes`).
- `src/styles.css`: nova classe `.f4p-items-warn`.
- Testes em `tests/test_actionable.py`: selo aparece só nos itens que realmente divergem (tipo fora de
  `usTypes`, entrega fora da janela exata, ou os dois motivos juntos) e não nos que contariam igual nos
  dois quadrantes; tooltip traz o motivo certo; os demais modais (`reserva`, `faltam`, e os do Report F4P/
  Visão Analítica) continuam sem a coluna extra.
- Documentação: `docs/regras-de-negocio.md` §13.3; `docs/telas.md`; `docs/testes/actionable.md`.
