# 0072 — Report F4P: conferência cruzada soma automaticamente os itens "Demais"

## Contexto

Depois da decisão `0071` (Technical Story ganhou uma lista de tipos configurável, `CFG.f4p.tsTypes`), o
usuário testou em produção e reportou que o problema original continuava: habilitou "Activity" na lista
de tipos da Vazão (`CFG.f4p.types`) esperando que contasse no Vazão Realizado, e a "Conferência
divergente" continuou aparecendo — porque ele não tinha incluído "Activity" também em `CFG.f4p.tsTypes`
(a solução da `0071` exigia esse passo extra e explícito).

O pedido corrigido do usuário, com print em anexo (time MOBILE: Vazão Realizado 41, soma de Technical
Story + User Story = 25): "ao habilitar pra contar na vazão qualquer item card nas configurações deve
se somar no cálculo da divergência e não somente User Story e Technical Story (...) é preciso ver a
quantidade de demais itens que foram somados para chegar no 41 e assim também adicionar na regra do
cálculo da divergência."

Ou seja: o usuário não quer precisar replicar a configuração em duas listas (Vazão e Technical Story/
User Story) — ele quer que **qualquer tipo habilitado para contar na Vazão** seja automaticamente
somado na conferência, com visibilidade de quantos itens isso representa.

## Decisões

1. **Novo termo "Demais" na soma da conferência**: `f4pDemaisItems(team, st)` — itens do Vazão Realizado
   (`f4pVazaoRealizadoItems`, já filtrado por `CFG.f4p.types`) cujo tipo **não** está em `CFG.f4p.tsTypes`
   nem em `CFG.f4p.usTypes`. A soma da conferência passa a ser **Technical Story + User Story Planejado +
   User Story Não planejado + Demais**, e por construção (Demais é literalmente "o resto do Vazão
   Realizado") a soma bate automaticamente sempre que `CFG.f4p.types` tiver um tipo extra não mapeado em
   nenhuma das outras duas listas — sem exigir nenhuma configuração adicional do usuário.
2. **A conferência continua pegando erro real de configuração**: "Demais" só consegue somar itens que o
   próprio Vazão Realizado já contava — não existe "demais negativo". Então a soma ainda **pode**
   ultrapassar o Vazão Realizado (e a conferência ainda sinaliza `ok:false`, com o banner vermelho de
   antes) em dois casos que continuam sendo erro de configuração de verdade:
   - Um tipo presente em `CFG.f4p.tsTypes` ou `CFG.f4p.usTypes` mas **ausente** de `CFG.f4p.types` —
     Technical Story ou User Story contam um item que a Vazão nem contaria.
   - Um tipo presente em `CFG.f4p.tsTypes` **e** em `CFG.f4p.usTypes` ao mesmo tempo — o item é contado
     duas vezes (uma em cada quadrante).
3. **Novo aviso informativo, distinto do aviso de divergência**: quando "Demais" é maior que zero mas a
   soma bate (`ok:true`), não é mais um erro — é só informação para o usuário conferir se aquele tipo não
   deveria estar numa das duas listas. Um banner **azul/neutro** (`.f4p-recon-info`, diferente do
   vermelho `.f4p-recon` da divergência real) lista os times com itens "Demais", com a quantidade exata
   **clicável** (mesmo padrão de transparência do resto do painel — `data-f4p-recon-demais-team`, abre
   `f4pItemsModal` com os itens exatos). O banner vermelho de divergência real continua aparecendo **só**
   quando `ok:false` — a decisão `0030` ("divergência de configuração é sinalizada, não escondida") segue
   valendo para os casos que ainda são erro de verdade (item 2 acima); só deixou de tratar como erro o
   caso que, na prática, era apenas falta de uma segunda configuração redundante.
4. **`CFG.f4p.tsTypes`/`CFG.f4p.usTypes` continuam valendo** para quando o usuário quer que um tipo extra
   conte **especificamente** como Technical Story ou User Story (afetando a meta/realizado daqueles
   quadrantes e a distribuição do Actionable) — "Demais" é só o resultado automático de **não** fazer essa
   atribuição explícita, não uma alternativa que substitui `tsTypes`/`usTypes`.

## Consequências

- `src/js/23-report-f4p.js`: `f4pDemaisItems` (novo); `f4pReconciliacao` ganha os campos `demais` e soma
  `+ demais`; `f4pReconciliacaoBanner` passa a renderizar dois blocos independentes — `.f4p-recon`
  (vermelho, só quando `ok:false`) e `.f4p-recon-info` (azul, times com `demais > 0` e `ok:true`); novo
  caso no listener de clique do painel (`data-f4p-recon-demais-team`) abrindo a lista exata dos itens
  "Demais"; nota do painel (`renderF4P`) atualizada.
- `src/styles.css`: nova classe `.f4p-recon-info`.
- Testes em `tests/test_report_f4p.py`: a soma "Demais" cobrindo o exemplo real reportado (tipo extra na
  Vazão sem configuração adicional, soma bate automaticamente); divergência real continua sinalizada
  quando Technical Story/User Story contam um tipo fora de `CFG.f4p.types` ou duplicado entre as duas
  listas; clique no "Demais" abre a lista exata; os dois banners (vermelho/divergência real, azul/
  informativo) aparecem e somem de forma independente.
- Documentação: `docs/regras-de-negocio.md` §12.8; `docs/telas.md`; `docs/guia-usuario/report-f4p.md`;
  `docs/testes/report-f4p/user-story.md`.
