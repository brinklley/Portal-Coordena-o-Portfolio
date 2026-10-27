# 0071 — Report F4P: tipo do quadrante Technical Story passa a ser configurável

## Contexto

O usuário habilitou o artefato "Activity" em Configurações › Report F4P, na lista de tipos considerados
para CycleTime/Variabilidade/Vazão (`CFG.f4p.types`), esperando que itens desse tipo contassem no
Vazão Realizado do time. Ao abrir o Report F4P, o painel passou a mostrar o aviso "Conferência
divergente" (decisão `0030`) para os times com itens do tipo Activity entregues — o próprio usuário
reportou o aviso como se fosse um bug, com o print do painel e do texto de ajuda da tela de
Configurações.

Investigação (ver `docs/decisoes/0030-report-f4p-quadrante-user-story.md`): a conferência está correta,
e é exatamente para isto que ela existe — `CFG.f4p.types` (Vazão) é um recorte que **deveria** ser
coberto, por convenção, pela soma de Technical Story (até aqui, tipo fixo "technical story") + User
Story (`CFG.f4p.usTypes`). Um tipo novo incluído em `CFG.f4p.types` sem entrar em nenhuma das outras
duas listas é exatamente o "erro de configuração" que a decisão `0030` quis sinalizar, não escondê-lo.

Mas o pedido do usuário é legítimo: ele quer contar "Activity" na Vazão **e** manter a regra de soma
TS + User Story, sem o aviso — ele só não tinha como dizer ao Portal a que "Activity" equivale para
fins da conferência, porque, dos três recortes, só Technical Story não tinha uma lista de tipos
configurável (User Story já tinha, desde a `0030`; Vazão também, desde o início).

Perguntado sobre os caminhos possíveis (tornar Technical Story configurável; reaproveitar `usTypes`;
criar um terceiro grupo "Outros" automático na conferência), o usuário escolheu o primeiro: tornar o
tipo do quadrante Technical Story configurável, no mesmo padrão de `usTypes`.

## Decisões

1. **Novo campo `CFG.f4p.tsTypes`** (padrão `["technical story"]`), com checkboxes próprios na tela de
   Configurações (`data-f4ptstype`), no mesmo padrão de `CFG.f4p.usTypes` — configuração própria,
   independente de `CFG.f4p.types` (Vazão/CT/Variabilidade) e de `CFG.f4p.usTypes` (User Story).
   `f4pTsOps`/`f4pTsRealizado`/`f4pTsCell` passam a usar `f4pTsTypes()` (análogo a `f4pUsTypes()`) em
   vez do tipo fixo `norm(o.type) === "technical story"`.
2. **Nenhuma terceira categoria "Outros" automática na conferência**: a soma continua sendo exatamente
   Technical Story + User Story Planejado + User Story Não planejado — o que muda é só que Technical
   Story agora reconhece uma lista de tipos, não um único tipo fixo. Isso preserva 100% a sinalização de
   divergência da decisão `0030`: um tipo incluído em `CFG.f4p.types` que não estiver em `tsTypes` nem em
   `usTypes` ainda diverge e ainda aciona o aviso — a diferença é que agora o usuário tem como resolver
   (incluir o tipo em uma das duas listas) em vez de só poder reverter a configuração da Vazão. A opção
   de um bucket "Outros" automático foi descartada de propósito: ela tornaria a soma sempre igual à
   Vazão por construção, esvaziando o propósito da conferência (nunca mais pegaria uma configuração
   realmente inconsistente).
3. **Reaproveitamento em outros lugares que citavam "Technical Story (tipo fixo)"**: a fatia "Technical
   Story" da Distribuição Vazão por mês do Actionable (decisão `0044`, §13.2) também usava o tipo fixo
   diretamente (`norm(o.type) === "technical story"`) — passou a usar `f4pTsTypes()`, para não divergir
   do critério do próprio quadrante Technical Story que o texto de ajuda já dizia reaproveitar.

## Consequências

- `src/js/01-configuracao-e-regras.js`: novo campo `CFG.f4p.tsTypes` (padrão `["technical story"]`) em
  `cfgDefaults`/`normCfg`.
- `src/js/19-tela-configuracoes.js`: nova lista de checkboxes para tipos de Technical Story
  (`data-f4ptstype`), com `readForm` coletando `d.f4p.tsTypes`; texto de ajuda da lista de Vazão
  atualizado (deixou de dizer que Technical Story é fixo) e novo texto de ajuda explicando a relação com
  a Conferência divergente.
- `src/js/23-report-f4p.js`: `f4pTsTypes()` (análogo a `f4pUsTypes()`); `f4pTsOps` usa a nova lista;
  comentários da conferência cruzada atualizados; texto da nota do painel (`renderF4P`) atualizado.
- `src/js/24-actionable.js`: `actDistBuckets` usa `f4pTsTypes()` em vez do tipo fixo.
- Testes em `tests/test_report_f4p.py`: tipos configuráveis de Technical Story (independente de
  `CFG.f4p.types`), padrão e exportação de `tsTypes`, e um novo teste de conferência cruzada confirmando
  que incluir um tipo extra (ex. "Activity") em `CFG.f4p.types` **e** em `CFG.f4p.tsTypes` não aciona mais
  o aviso de divergência.
- Documentação: `docs/regras-de-negocio.md` §12.5, §12.8 e §13.2; `docs/configuracoes.md`;
  `docs/telas.md`; `docs/testes/report-f4p/technical-story.md` e `user-story.md`.
