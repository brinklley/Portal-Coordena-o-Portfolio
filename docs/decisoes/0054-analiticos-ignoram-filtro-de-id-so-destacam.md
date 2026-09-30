# 0054 — Visão analítica, Report F4P e Actionable ignoram o filtro "ID ou descrição"; só destacam

## Contexto

O usuário reportou (print da tabela "Roadmap MOBILE 2º semestre 2026", Visão analítica) que digitar um
ID no campo "ID ou descrição" reduzia a tabela a uma única linha — escondendo os outros épicos do
time+roadmap selecionados. Pedido: nessas três telas (Visão analítica, Report F4P e Actionable), o
campo "ID ou descrição" **não deve filtrar**; só deve **destacar** a linha correspondente. Essas telas
devem continuar sendo afetadas só pelos filtros de **roadmap** (interno ou executivo), **time** e
**responsável** — os mesmos que já as habilitam (`anEnabled`/`f4pEnabled`/`actEnabled`).

## Diagnóstico

- **Visão analítica** (`anData()`, `src/js/15-visao-analitica.js`): montava as linhas a partir de
  `S.V.visEpi` — o conjunto de épicos visíveis no **quadro** (whiteboard), calculado por
  `computeVisible(S.f)` com **todos** os filtros de `S.f`, incluindo `q` ("ID ou descrição", decisão
  `0034`). Como o quadro usa `q` para reduzir a cadeia exibida (comportamento correto ali), a Visão
  analítica herdava esse mesmo corte sem querer — daí o bug relatado.
- **Report F4P** (`src/js/23-report-f4p.js`) e **Actionable** (`src/js/24-actionable.js`): investigação
  confirmou que **nenhuma** função de quadrante lê `S.V`/`computeVisible` — todas iteram
  `[...S.model.ops.values()].filter(o => o.team === team && ...)` direto. Ou seja, essas duas telas
  **já** cumpriam a regra pedida (nunca dependeram de `q`); não precisaram de nenhuma mudança de código.

## Decisão

**Visão analítica**: `anData()` passa a calcular a visibilidade dos épicos ignorando `q`
(`computeVisible({...S.f, q:""})`, mantendo `exec`/`int`/`team`/`owners` intactos) em vez de usar
`S.V`. Um novo `qHit(id, title)` (reaproveitando `norm`/`nid`, mesmo critério do filtro do quadro)
decide, por linha, se o épico, a iniciativa vinculada, ou algum item de time do épico bate com o texto
digitado — e marca `row.hl = true` nesse caso. `renderAnalytics()` aplica a classe CSS `hl` na `<tr>`
correspondente (fundo destacado, `src/styles.css`) e rola até a primeira linha destacada
(`scrollIntoView`) sempre que `S.f.q` estiver preenchido. Sem `q`, nada muda: todas as linhas aparecem
normalmente, nenhuma com destaque.

**Report F4P e Actionable**: nenhuma mudança de código — já estavam corretos. Adicionados testes de
regressão (`test_ignora_filtro_de_id_ou_descricao_so_roadmap_time_e_responsavel_afetam` em
`tests/test_report_f4p.py` e `tests/test_actionable.py`) confirmando que os números desses painéis não
mudam com `S.f.q` preenchido — trava esse comportamento contra uma regressão futura.

O filtro `q` no **quadro** (whiteboard) continua exatamente como era (decisão `0034`): reduzir a cadeia
visível ali é o comportamento certo e esperado, já que essa é a ferramenta de busca/navegação do
portal — a mudança desta decisão é só nas três telas analíticas, que têm um propósito diferente
(panorama do time no roadmap selecionado, não busca pontual).

## Consequência

Digitar um ID ou trecho de título no filtro "ID ou descrição" com a Visão analítica aberta continua
mostrando **todos** os épicos do time+roadmap selecionados, com a linha correspondente destacada e a
rolagem indo até ela — sem o usuário perder o panorama do conjunto inteiro. Report F4P e Actionable já
se comportavam assim; passam a ter essa garantia coberta por teste.
