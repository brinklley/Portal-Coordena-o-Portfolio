# 0051 — Investigação: P95 do CycleTime parece alto demais com poucos itens acima da Reserva

## Status: investigação em aberto — hipótese bem fundamentada, não confirmada com dados reais

## Contexto

O usuário mandou um print do quadrante CycleTime (dispersão) do Actionable, time MOBILE, 1º semestre
2026: 39 itens na amostra, Reserva (CT máximo do time) em 60d, só **2 pontos** visivelmente acima da
Reserva (em vermelho, um perto de 78d e outro perto de 100d) — e a linha "Atual (P95)" marcada em
**78d**. A pergunta: como só 2 itens acima da Reserva conseguem levar o P95 a 78d — isso está correto?

## Investigação

### O quadrante Actionable e o Report F4P usam exatamente a mesma amostra

`actCtScatterData` (`src/js/24-actionable.js:16-23`) chama `f4pSample`/`limitsOf` — as mesmas funções
do quadrante CycleTime do Report F4P (§12.2) — e calcula `atual = percentil(cts, .95)` sobre o **mesmo
array** `cts` que vira os pontos do gráfico (`items`). Não há descompasso entre o que é desenhado e o
que alimenta o P95 — confirmado lendo o código, não é uma hipótese.

### Como `percentil()` posiciona o P95 numa amostra de 39 itens

`percentil(a, p)` (`src/js/02-utilitarios.js:47-51`) usa interpolação linear (`PERCENTIL.INC` do
Excel): `rank = p × (n-1)`. Para n=39 e p=0,95: `rank = 0,95 × 38 = 36,1` — um número **fixo, que não
depende dos valores da amostra**, só do tamanho dela. Isso posiciona o P95 **entre o 3º maior e o 2º
maior item** (índices 36 e 37, com 39 itens = índices 0–38), com peso **90% no 3º maior e 10% no 2º
maior**. Verificado rodando a função real:

```
n=39, rank (0-indexed) = 36.1 -> interpola entre índice 36 (3º maior) e 37 (2º maior), peso = 0.10
```

**O maior item da amostra (o outlier mais extremo) não entra na conta.** Essa é a explicação geral de
por que "poucos itens acima da Reserva" não é incompatível, em tese, com um P95 elevado — a estatística
não olha "quantos" itens estão acima de um limiar, olha uma posição específica perto do topo.

### O teto matemático, aplicado ao caso do usuário

Só que, aplicando essa fórmula ao cenário descrito (Reserva 60d, só 2 itens **estritamente** acima dela,
maior item da amostra ≈100d, conforme o print), o teto do P95 fica bem abaixo de 78d:

```
3º maior = 50 -> P95 = 52.8
3º maior = 55 -> P95 = 57.3
3º maior = 60 -> P95 = 61.8   (3º maior no limite exato da Reserva)
```

Com o 3º maior no máximo possível sem ultrapassar a Reserva (60d) e o 2º maior en torno de 78-100d, o
P95 (peso 90% no 3º maior) não passa de ~62d — bem longe dos 78d exibidos.

## Conclusão (provisória)

**Não encontrei bug no código** — `percentil()`, `f4pSample` e `actCtScatterData` calculam exatamente o
que a documentação diz, sem descompasso de amostra. A explicação mais provável para o P95 exibido (78d)
não bater com o teto calculado a partir de "só 2 itens acima da Reserva" é que **existe um 3º item na
amostra com CT alto o bastante (perto de ~74-78d) para explicar o resultado** — mesmo que ele não tenha
aparecido destacado em vermelho no print (por estar sobreposto a outro ponto no gráfico, ou por uma
leitura visual imprecisa de "só 2 pontos" a partir de uma imagem).

**Não pude confirmar com números exatos**: o usuário não tinha como extrair os CTs exatos dos itens no
momento (precisaria clicar/passar o mouse nos pontos do gráfico — já é possível, cada ponto tem
`<title>` com ID, CT e data de entrega). Fica em aberto até haver esse dado real para comparar contra o
cálculo esperado.

## Próximo passo, se o usuário quiser fechar isso

Com os CTs exatos dos 3 itens mais altos da amostra (ordenados, o 1º/2º/3º maior), dá pra calcular o
P95 esperado com a fórmula acima e comparar com o valor exibido — se bater, confirma que é só um 3º
item alto que passou despercebido no print; se não bater, é evidência real de bug (amostra errada, `n`
diferente do exibido, ou erro na função). Sem código alterado nesta investigação.
