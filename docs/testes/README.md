# Documentação dos testes

Este é o contrato de regras que a suíte automatizada (`tests/`, 218 testes — pytest + Playwright)
protege. Cada arquivo aqui documenta, por domínio funcional, **o que cada regra garante, com que
entrada, o resultado esperado no caso de sucesso e o cenário de falha (bug ou regressão) que o teste
existe para impedir** — no estilo BDD (Dado/Quando/Então), citando a(s) função(ões) de teste que
cobrem a regra e a decisão/seção de `docs/regras-de-negocio.md` relacionada.

## Por que esta pasta existe

O portal já tem `docs/regras-de-negocio.md` (o que o sistema faz) e `docs/decisoes/` (por que cada
decisão foi tomada). Esta pasta é o terceiro pé: **o que os testes garantem que continua verdade**,
na granularidade de cenário de teste — não a regra de negócio em si (que já está documentada), mas o
contrato executável que a trava.

**Use esta pasta antes de implementar uma funcionalidade, melhoria ou correção.** O fluxo pretendido:

1. Antes de mudar comportamento, procure aqui se alguma regra documentada toca a área que você vai
   mexer.
2. Se a mudança pedida contraria uma regra aqui documentada, **isso é um sinal, não um obstáculo**:
   pare e entenda por que aquela regra existe (leia a decisão citada) antes de ajustar o teste.
   A pergunta certa é "essa regra de negócio deveria mudar, e por quê?", nunca "como faço esse teste
   passar?".
3. Se a mudança de fato exige revisar a regra, siga o fluxo do `CLAUDE.md`: atualize
   `docs/regras-de-negocio.md`, o teste correspondente e registre o motivo em `docs/decisoes/`
   (novo arquivo numerado) — e atualize também o arquivo desta pasta que documenta aquele teste.
4. Se a mudança é uma funcionalidade nova sem conflito com nenhuma regra existente, implemente
   normalmente e, ao final, adicione a documentação da nova regra aqui (mesmo padrão dos exemplos
   abaixo), como parte do fechamento do trabalho — não uma tarefa à parte.

Em suma: um teste falhando depois de uma mudança pedida não é sempre um teste desatualizado — pode
ser a suíte pegando exatamente o que ela foi escrita para pegar. Esta pasta existe para tornar
rápido decidir qual dos dois casos é.

## Convenção de cada entrada

Cada regra documentada segue este formato:

```markdown
## Regra: <nome curto e descritivo>

**Garante que**: <a regra de negócio protegida, em uma ou duas frases>

- **Dado**: <estado/entrada inicial>
- **Quando**: <ação, se houver>
- **Então (sucesso)**: <resultado esperado>
- **Cenário de falha coberto**: <o bug ou regressão que o teste impede de voltar>
- **Teste(s)**: `test_nome_da_funcao` (uma ou mais, quando cobrem variações próximas da mesma regra)
- **Relacionado**: decisão `NNNN`, regras-de-negocio.md §N
```

Os testes são **agrupados por regra/cenário de negócio**, não listados um a um — vários
`test_algo_variante_a`/`test_algo_variante_b` que testam a mesma regra sob ângulos diferentes
aparecem juntos na mesma entrada, cada um citado pelo nome exato da função.

## Índice

| Arquivo | Domínio | Testes | Regras de negócio |
|---|---|---|---|
| [`azure-devops.md`](azure-devops.md) | Integração e carga do Azure DevOps (única fonte de dados) | 6 | `docs/integracao-azure.md` |
| [`hierarquia-e-modelo.md`](hierarquia-e-modelo.md) | Hierarquia, validade e visibilidade (regra B) | 5 | §2, §3 |
| [`ct-alertas-tags.md`](ct-alertas-tags.md) | CycleTime do item/épico, alertas, tags | 4 | §6, §8, §9 |
| [`filtros-e-busca.md`](filtros-e-busca.md) | Filtros e o campo único "ID ou descrição" | 7 | `docs/telas.md` |
| [`quadro-e-selecao.md`](quadro-e-selecao.md) | Board de Iniciativas: recolher/manter visíveis | 6 | `docs/telas.md` |
| [`ilhas-e-cadeia-completa.md`](ilhas-e-cadeia-completa.md) | Whiteboard: ilhas soltas manualmente | 3 | `docs/telas.md` |
| [`configuracoes.md`](configuracoes.md) | Validações, exportação sem token, limpar tudo | 6 | `docs/configuracoes.md` |
| [`visao-analitica.md`](visao-analitica.md) | Visão analítica do roadmap do time | 15 | §10 |
| [`report-f4p/README.md`](report-f4p/README.md) | Report F4P — regras compartilhadas entre os 8 quadrantes | — | §12, §12.1 |
| [`report-f4p/cycletime-e-variabilidade.md`](report-f4p/cycletime-e-variabilidade.md) | F4P Quadrantes 1–2 | — | §12.2, §12.3 |
| [`report-f4p/urgente.md`](report-f4p/urgente.md) | F4P Quadrante 3 | — | §12.4 |
| [`report-f4p/technical-story.md`](report-f4p/technical-story.md) | F4P Quadrante 4 | — | §12.5 |
| [`report-f4p/vazao.md`](report-f4p/vazao.md) | F4P Quadrante 5 | — | §12.6 |
| [`report-f4p/roadmap-epicos.md`](report-f4p/roadmap-epicos.md) | F4P Quadrante 6 | — | §12.7 |
| [`report-f4p/user-story.md`](report-f4p/user-story.md) | F4P Quadrante 7 + conferência cruzada | — | §12.8 |
| [`report-f4p/eficiencia-de-fluxo.md`](report-f4p/eficiencia-de-fluxo.md) | F4P Quadrante 8 | — | §12.9 |
| [`actionable.md`](actionable.md) | Actionable: CycleTime, Distribuição Vazão por mês, Burnup Reserva e CFD | 45 | §13 |

O Report F4P (`tests/test_report_f4p.py`, 121 testes) é a maior suíte do projeto — por isso ganhou
subpasta própria, com um `README.md` de regras compartilhadas (janelas de data, convenção de
tendência, padrão de clique-para-ver-itens) e um arquivo por quadrante.

**Fora do escopo desta pasta**: `tests/conftest.py` (infraestrutura — abre `dist/mapa_portfolio.html`
num Chromium headless) e `tests/azure_simulado.py`/`tests/gerar_fixtures.py` (dados sintéticos de
apoio) não têm regra de negócio própria para documentar aqui.

## Como rodar

Ver `CLAUDE.md` (raiz do repositório) — resumo: `npm run build && npm test` (primeira vez, também
`pip install -r requirements-dev.txt` e `python3 -m playwright install chromium`).
