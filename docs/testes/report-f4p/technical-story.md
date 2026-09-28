# Testes: Report F4P — Quadrante 4 (Technical Story: meta vs. realizado)

Ver `docs/testes/report-f4p/README.md` para as regras compartilhadas. Regras de negócio: §12.5.
Decisões `0018`–`0020`.

Mesmo padrão de meta/cor/clique do Urgente (`urgente.md`), mas conta itens pelo **tipo** "Technical
Story" (não por tag), e a meta padrão é **6** quando o time não cadastra a própria (o Urgente fica
"sem meta" nesse caso — diferença proposital entre os dois quadrantes).

## Regra: conta só itens do tipo Technical Story já entregues (categoria Vazão)

**Garante que**: diferente do Urgente (que conta abertos também), o Technical Story só conta itens
que já chegaram à categoria de fluxo Vazão (entregues) — itens em Backlog, Discovery ou WIP não
entram no Realizado, **mesmo abertos há muito tempo**.

- **Dado**: um item Technical Story entregue (conta), um User Story entregue (tipo errado, não
  conta), um Bug entregue (tipo errado, não conta).
- **Então (sucesso)**: `f4pTsRealizado(team) === 1`.
- **Dado (regra dos não entregues)**: itens Technical Story em Backlog/Discovery/WIP (não contam,
  mesmo abertos) e um em Vazão sem data de saída (`deploy:null`, também não conta — Vazão sem data
  não é considerado entregue).
- **Então (sucesso)**: `f4pTsRealizado(team, ...) === 1` (só o item Vazão com `deploy` preenchido).
- **Cenário de falha coberto** (regra pedida pelo usuário depois de ver o quadrante em produção): um
  item Technical Story parado há meses em WIP contaria como "realizado" só por estar velho, inflando
  a entrega real do time — a categoria de fluxo (não a idade) é o único critério de "entregue".
- **Testes**: `test_ts_conta_so_itens_do_tipo_technical_story_e_entregues`,
  `test_ts_ignora_itens_em_backlog_discovery_ou_wip`
- **Relacionado**: decisão `0020-report-f4p-technical-story-so-itens-entregues.md`.

## Regra: janela é o período exato do semestre selecionado (mesma lógica do Urgente)

**Garante que**: no semestre em curso, ignora entregues antes do início do semestre; num semestre
encerrado, conta só entregues dentro daquele período.

- **Testes**: `test_ts_semestre_atual_ignora_entregues_antes_do_inicio_do_semestre`,
  `test_ts_semestre_passado_conta_so_entregues_no_periodo`
- **Relacionado**: decisão `0017` (mesma janela exata usada pelo Urgente).

## Regra: clique no número abre a lista com a situação por categoria de fluxo

**Garante que**: segue o padrão compartilhado — Situação usa a categoria real (`catOf`), não
"Fechado" genérico.

- **Teste**: `test_ts_clique_no_numero_abre_lista_e_permite_navegar`
- **Relacionado**: decisão `0019`.

## Regra: meta padrão 6 (diferente do Urgente, que fica "sem meta" por padrão)

**Garante que**: sem meta própria cadastrada, o Technical Story usa o padrão 6 (não fica neutro) —
6 ou menos itens entregues → verde; mais que 6 → vermelho; com meta própria cadastrada, usa essa
meta em vez do padrão.

- **Dado**: 6 itens entregues (na meta padrão), depois 7 (acima do padrão), depois meta própria 10
  cadastrada (7 ≤ 10, dentro).
- **Então (sucesso)**: `f4p-good` sem `f4p-bad` no primeiro caso; `f4p-bad` no segundo;
  `f4p-good` sem `f4p-bad` no terceiro.
- **Cenário de falha coberto**: reaproveitar cegamente a lógica "sem meta = neutro" do Urgente faria
  o Technical Story nunca sinalizar cor nenhuma até o time cadastrar uma meta manualmente — a
  decisão de negócio pede um padrão sensato de saída.
- **Teste**: `test_ts_meta_padrao_6_colore_vermelho_ou_verde`
- **Teste complementar**: `test_ts_meta_zero_e_valida` — meta `0` explícita é válida e distinta de
  "usar o padrão 6".
- **Relacionado**: decisão `0018-report-f4p-quadrante-technical-story.md`.

## Regra: o quadrante aparece calculado no painel; meta persiste e exporta

**Testes**: `test_ts_aparece_calculado_no_painel`,
`test_ts_configuracao_meta_persiste_e_entra_na_exportacao`
