# 0023 — Report F4P Vazão: tendência soma itens em WIP ao mês corrente

## Contexto

A decisão `0022` implementou a tendência do Vazão como "último mês vs. média dos meses anteriores", sinalizando explicitamente que era a parte da regra original com mais graus de liberdade de interpretação. O usuário revisou e especificou o comportamento correto, com três exemplos numéricos exatos.

## Decisão

A tendência continua separando o Realizado por mês corrido dentro do período do semestre (só os meses já decorridos, no semestre em curso — regra inalterada da decisão `0022`), mas o cálculo muda em dois pontos:

1. **O mês corrente (ou o último mês do semestre, se já encerrado) passa a somar os itens hoje em WIP** do time (mesmos tipos configurados do quadrante, `CFG.f4p.types`) — uma contagem "ao vivo", sem filtro de período, feita por `f4pVazaoWipCount`. Itens em WIP ainda não viraram Vazão, mas sinalizam entrega a caminho; ignorá-los faria a tendência reagir tarde a uma retomada de ritmo (o time já está entregando mais, mas isso só apareceria no relatório um mês depois, quando os itens em WIP finalmente virassem Vazão).
2. **A média dos meses anteriores arredonda sempre para cima** (`Math.ceil`), não para o inteiro mais próximo.

A comparação final é: `mês corrente + itens em WIP` vs. `média (arredondada pra cima) dos meses anteriores` — maior → melhora (▲); menor → piora (▼); igual → estável (◆). Sem meses anteriores para comparar, continua ◆ (inalterado da decisão `0022`).

### Exemplos dados pelo usuário (usados como teste de aceite)

| Média dos meses anteriores | Mês corrente | Itens em WIP | Mês corrente + WIP | Resultado |
|---|---|---|---|---|
| 1 | 0 | 3 | 3 | ▲ melhora (3 > 1) |
| 2 | 0 | 1 | 1 | ▼ piora (1 < 2) |
| 3 | 2 | 1 | 3 | ◆ estável (3 = 3) |

## Consequências

- `src/js/23-report-f4p.js`: nova função `f4pVazaoWipCount(team)` — itens do time, dos tipos configurados, na categoria de fluxo `wip` (`catOf`), sem filtro de data. `f4pVazaoTrend` passa a somar esse valor ao mês corrente antes de comparar, e a arredondar a média com `Math.ceil`.
- Tooltip do Vazão atualizado para descrever a nova fórmula.
- Testes em `tests/test_report_f4p.py`: os três exemplos exatos do usuário, um caso específico confirmando o arredondamento sempre para cima (uma média bruta de 1,5 que, sem arredondar, daria "melhora", mas arredondada para 2 dá "estável"), e um teste confirmando que `f4pVazaoWipCount` só conta itens do time e dos tipos configurados.
- `docs/regras-de-negocio.md` §12.6 e `docs/backlog/report-f4p.md` atualizados para descrever a fórmula com WIP.
