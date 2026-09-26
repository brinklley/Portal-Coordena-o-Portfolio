# 0024 — Report F4P Vazão: cor da seta de tendência por Realizado vs. Reserva

## Contexto

O Vazão (decisões `0022`/`0023`) não colore os números da Reserva/Realizado — não há meta/teto configurável, então não fazia sentido um vermelho/verde nos valores em si. O usuário pediu um novo comportamento: colorir o **sinalizador de tendência** (▲/▼/◆) de acordo com a relação entre Realizado e Reserva, independente da direção da tendência.

## Decisão

A seta/losango de tendência do Vazão passa a ser colorida:

- **Verde** quando Realizado ≥ Reserva.
- **Vermelho** quando Realizado < Reserva.

Isso é independente do símbolo mostrado (▲/▼/◆) — a cor não segue a direção da tendência, segue a relação Realizado vs. Reserva. Os **números** da Reserva e do Realizado continuam sem cor (regra da decisão `0022`, inalterada); só a seta ganha cor.

### Nota sobre alcançabilidade

Por construção (decisão `0022`), Reserva é sempre um subconjunto do Realizado — o mesmo conjunto de itens filtrado pela tag de capacidade. Isso significa que `Realizado < Reserva` **nunca acontece** através do pipeline normal de cálculo: a condição vermelha, tal como pedida, não é alcançável com os dados de hoje. Implementamos a checagem exatamente como especificada mesmo assim, por ser uma salvaguarda visual barata e explicitamente pedida pelo usuário — se no futuro a definição de Reserva ou Realizado divergir dessa relação de subconjunto (por exemplo, se um dos dois passar a vir de uma fonte de dados diferente), a cor vermelha passa a ser alcançável e continua correta sem mudança de código.

## Consequências

- `src/js/23-report-f4p.js`: `f4pVazaoCell` calcula `realizado.length >= reserva.length ? "f4p-good" : "f4p-bad"` e aplica a classe ao `<span class="f4p-trend">`.
- `src/styles.css`: `.f4p-trend.f4p-good`/`.f4p-trend.f4p-bad` — precisam de especificidade composta porque `.f4p-good`/`.f4p-bad` são declaradas antes de `.f4p-trend` no arquivo (mesmo problema de ordem de declaração já corrigido para `.f4p-real` — decisão `0016`/PR de correção do Realizado do Urgente).
- Tooltip do Vazão atualizado para explicar a cor da seta.
- Testes em `tests/test_report_f4p.py`: os dois casos alcançáveis (Realizado maior que Reserva; Realizado igual à Reserva, todos os itens com a tag) confirmando `f4p-good` e a ausência de `f4p-bad`.
- `docs/regras-de-negocio.md` §12.6 e `docs/backlog/report-f4p.md` atualizados para descrever a cor da seta separadamente da regra de "sem cor nos números".
