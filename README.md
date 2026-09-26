# Mapa do Portfólio

Portal para visualizar e gerir o portfólio em cadeia: **Iniciativas → Releases → Épicos → itens dos times**, num whiteboard com kanbans por nível, alertas de CycleTime, visão analítica por time e carga de dados por **planilha** ou direto do **Azure DevOps**.

É um **único arquivo HTML**: abra com dois cliques no Chrome ou Edge. Não precisa de servidor, e nenhum dado sai do computador (exceto as chamadas que você faz ao Azure DevOps).

## Para usar

Baixe `dist/mapa_portfolio.html` (gerado pelo build) e abra no navegador.

## Para desenvolver

```bash
npm install
pip install -r requirements-dev.txt
python3 -m playwright install chromium
python3 tests/gerar_fixtures.py
npm test
```

Estrutura, regras e decisões: veja `CLAUDE.md` e a pasta `docs/`.

## Segurança dos dados

Planilhas reais, exportações e arquivos `.har` **não devem ser versionados**. O `.gitignore` já bloqueia esses formatos fora de `fixtures/`.
