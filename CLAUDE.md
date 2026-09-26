# Mapa do Portfólio

Visualizador encadeado Iniciativa → Release → Épico → itens dos times, com carga por planilha ou direto do Azure DevOps. Entregue como **um único HTML**, sem servidor. Interface e documentação em **português do Brasil**.

## Comandos

- `npm install` (baixa a biblioteca SheetJS usada no build)
- `npm run build` → gera `dist/mapa_portfolio.html` (o arquivo entregue aos usuários)
- `npm run check` → sintaxe do código juntado
- `python3 tests/gerar_fixtures.py` → planilhas fictícias em `fixtures/`
- `npm test` → build + testes (`pytest`, Playwright/Chromium). Primeira vez: `pip install -r requirements-dev.txt` e `python3 -m playwright install chromium`

## Regras de trabalho

- **Antes de concluir qualquer mudança: `npm run build`, `npm run check` e `npm test` verdes.**
- Mudou uma regra de negócio? Atualize `docs/regras-de-negocio.md`, o teste correspondente em `tests/` e registre o motivo em `docs/decisoes/` (novo arquivo numerado).
- O código é um script global dividido em `src/js/NN-*.js`, juntado em **ordem alfabética**: respeite a ordem ao criar arquivos. Nada de módulos, `import`, bibliotecas externas em tempo de execução ou a sequência `</script>`.
- **Nunca** versione dados reais (planilhas exportadas, `.har`, prints com dados). Testes usam só `fixtures/` e `tests/azure_simulado.py`.
- **Nunca** persista tokens do Azure (nem em `localStorage`, `IndexedDB` ou exportação). Ver `docs/decisoes/0007-token-nunca-salvo.md`.
- Textos para o usuário: claros, sem jargão, dizendo o que aconteceu e o que fazer. Mensagens de alerta seguem o padrão diagnóstico + "O que fazer".

## Onde está cada coisa

- Regras de negócio: `docs/regras-de-negocio.md`
- Integração Azure DevOps: `docs/integracao-azure.md`
- Importação de planilha/CSV: `docs/importacao-planilha.md`
- Configurações (estrutura do `CFG`, padrões, validações): `docs/configuracoes.md`
- Telas e funcionalidades: `docs/telas.md`
- Arquitetura e mapa dos arquivos: `docs/arquitetura.md`
- Decisões e motivos: `docs/decisoes/`
- **Próxima tarefa: Report F4P — escolher e especificar o próximo quadrante** (Eficiência de fluxo ou User Story) → `docs/backlog/report-f4p.md` (Quadrantes 1, 2, 3, 4, 5 e 6 já implementados; decisões em `docs/decisoes/0011` a `0025`). Demais pendências: `docs/backlog/pendencias.md`
