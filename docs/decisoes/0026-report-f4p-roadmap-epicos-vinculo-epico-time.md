# 0026 — Report F4P: Roadmap – Épicos, reforço do vínculo épico↔time

## Contexto

Ainda no PR do Quadrante 6 (decisão `0025`), o usuário pediu explicitamente uma regra de negócio
adicional para deixar sem ambiguidade: a conexão entre um épico e um time deve ser **sempre** pelos
itens filhos (Parent → Child, isto é, `o.epicoId`/`ID_EPICO_UNICRED` no item operacional apontando para
o épico) — nunca por qualquer outro caminho (Target Date do épico, vínculo com a iniciativa do Roadmap
Executivo, etc.). O cenário de falha descrito: um épico aparecer contabilizado como "Roadmap entregue"
do time CORE quando, na prática, nenhum item dele é do CORE — todos são do MOBILE; nesse caso, o épico
deveria contar só para o MOBILE.

## Investigação

Antes de alterar código, verifiquei se essa regra já valia na implementação da decisão `0025`:
`f4pRoadmapEpis`, `f4pRoadmapEntregueEpis` e `f4pAtualEpis` já usam `f4pEpiHasTeam(e, team)` — que
checa exclusivamente os itens filhos do épico (`e.ops`, preenchido em `buildModel` a partir do
`ID_EPICO_UNICRED` de cada item) — em todos os três números, nos dois branches do Roadmap (interno e
executivo). Reproduzi o cenário de falha descrito pelo usuário (épico vinculado por Release/Iniciativa
ao Roadmap Executivo do CORE, mas com todos os itens filhos no MOBILE; e o mesmo pelo Target Date no
Roadmap Interno) e confirmei que o comportamento já é o esperado: o épico aparece só na contagem do
MOBILE, nunca na do CORE, nos três números (Roadmap, Roadmap entregue, Atual).

## Decisão

1. **Nenhuma mudança de código foi necessária** — a regra pedida já era garantida pela decisão `0025`.
   Em vez de mexer numa lógica que já está correta (risco de regressão sem benefício), reforcei a
   **documentação** (`docs/regras-de-negocio.md` §12.7, com o cenário de falha registrado explicitamente)
   e adicionei **testes de regressão** cobrindo exatamente o cenário descrito, nos dois branches do
   Roadmap e nos três números — que antes só tinham cobertura explícita para o branch Interno na função
   `f4pRoadmapEpis` (`test_roadmap_conta_so_epicos_com_item_do_time`).
2. Os novos testes travam o comportamento para o futuro: um épico com item vinculado só a um time nunca
   deve aparecer na contagem de outro time, mesmo estando dentro do Roadmap desse outro time por Target
   Date (Interno) ou por vínculo com a iniciativa (Executivo) — e o mesmo vale para "Atual", que já era
   independente do critério do Roadmap (decisão `0025`) mas ainda dependia do vínculo com o time.

## Consequências

- Sem mudança em `src/js/23-report-f4p.js` (comportamento já correto).
- `docs/regras-de-negocio.md` §12.7: parágrafo novo deixando explícito que o vínculo épico↔time é
  sempre pelos itens filhos, com o cenário de falha descrito pelo usuário.
- Testes novos em `tests/test_report_f4p.py`: épico com itens só de outro time, testado no branch
  Executivo (além do Interno, já coberto) e em "Atual" — confirmando que o épico conta para o time
  certo e nunca para o errado, nos três números.
