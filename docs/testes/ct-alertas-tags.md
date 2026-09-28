# Testes: CycleTime, alertas e tags

Cobre `tests/test_ct_alertas_tags.py` (4 testes). Ver `docs/regras-de-negocio.md` §6 (CycleTime),
§8 (Alertas) e §9 (Tags cadastradas).

## Regra: CT do item é a diferença entre Ready e Pronto para Deploy

**Garante que**: o CycleTime de um item de time é calculado em dias corridos entre a data em que
entrou em "READY / PRONTO PARA DEV" e a data em que chegou a "Pronto para Deploy" — usando as datas
reais da planilha/fonte, não uma contagem de dias úteis nem outra dupla de colunas.

- **Dado**: fixture `times.xlsx`, time CORE, um item com as duas datas preenchidas.
- **Quando**: o modelo calcula `o.ct` para esse item.
- **Então (sucesso)**: `o.ct` bate exatamente com `(Pronto para Deploy - READY/PRONTO PARA DEV).days`
  calculado independentemente a partir da planilha.
- **Cenário de falha coberto**: o CT usaria a data de criação do item ou de entrada no quadro em vez
  do marco "Ready", inflando ou reduzindo o tempo de ciclo real.
- **Teste**: `test_ct_do_item_entre_ready_e_pronto_para_deploy`
- **Relacionado**: regras-de-negocio.md §6.1; decisão `0006-regra-de-datas-actionableagile.md`.

## Regra: alertas de CT (atraso/outlier) seguem os limites configurados por time

**Garante que**: cada time tem seus próprios limites (`warn`/`max`) — itens com CT acima do `max`
viram `outlier`; entre o `warn` e o `max`, viram `atraso` (`overCt`); dentro do `warn`, ficam sem
alerta. Itens já concluídos (com deploy) também são avaliados, não só os ainda abertos.

- **Dado**: `CFG.teams = {core: {warn:1, max:2, out:5}}`, `recomputeHealth()`.
- **Então (sucesso)**: existe ao menos 1 item `outlier/ct`; todo item com `ct >= 5` está marcado
  `outlier`; todo item com `2 < ct < 5` está marcado `overCt` e não `outlier`; todo item concluído
  com `ct <= 2` não tem nenhum dos dois alertas.
- **Cenário de falha coberto**: um item com CT muito acima do limite apareceria só como "atraso"
  (severidade menor), escondendo um outlier real do time.
- **Teste**: `test_alertas_por_limite_do_time`
- **Relacionado**: regras-de-negocio.md §8.1.

## Regra: tag "blocked" é reconhecida a partir do histórico do item

**Garante que**: a tag "Blocked" (id `blocked`) aplicada a um item em algum momento do histórico é
detectada e aparece em `o.tagHits`, alimentando os alertas e o Report F4P (Urgente usa o mesmo
mecanismo de `tagHits` para a tag configurável de expedição).

- **Dado**: `times.xlsx` (contém itens com a tag Blocked em algum ponto do histórico).
- **Então (sucesso)**: existe ao menos 1 item com `o.tagHits.some(t => t.id === 'blocked')`.
- **Cenário de falha coberto**: uma tag aplicada e depois removida, ou aplicada num formato de nome
  ligeiramente diferente (maiúsculas, espaço), deixaria de ser reconhecida.
- **Teste**: `test_tag_blocked_reconhecida`
- **Relacionado**: regras-de-negocio.md §9.

## Regra: CT do épico só considera os tipos de item configurados para CT

**Garante que**: a métrica de CT agregada de um épico (`epiMetrics(e, '').ctN`) conta só os itens
dos tipos marcados para entrar no cálculo de CT (por padrão, User Story e Technical Story) —
excluindo tipos como Bug ou Internal Bug, mesmo que estejam vinculados ao épico.

- **Dado**: um épico com mais de 3 itens vinculados, de tipos variados.
- **Então (sucesso)**: `m.ctN` é igual à contagem de itens cujo tipo é "User Story" ou "Technical
  Story"; `m.ctN < m.n` (o total de itens do épico), confirmando que outros tipos existem mas foram
  excluídos do CT.
- **Cenário de falha coberto**: um Bug de suporte vinculado ao épico distorceria a média de CT do
  épico, mesmo não sendo um item de desenvolvimento típico.
- **Teste**: `test_ct_do_epico_so_com_tipos_configurados`
- **Relacionado**: regras-de-negocio.md §6.2; `docs/configuracoes.md` (tipos de CT por time).
