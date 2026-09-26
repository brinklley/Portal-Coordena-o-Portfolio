# 0010 · Dados reais fora do Git

**Contexto.** Planilhas exportadas e arquivos HAR contêm títulos, nomes de pessoas e links internos.
**Decisão.** Nunca versionar dados reais (`.gitignore` bloqueia `.xlsx`, `.csv`, `.har` fora de `fixtures/`). Testes usam dados fictícios gerados por `tests/gerar_fixtures.py` e o Azure simulado.
