# Mapa do Portfólio

Visualizador encadeado Iniciativa → Release → Épico → itens dos times, com carga direto do Azure DevOps (única fonte de dados — ver decisão `0032`). Entregue como **um único HTML**, sem servidor. Interface e documentação em **português do Brasil**.

## Comandos

- `npm install`
- `npm run build` → gera `dist/mapa_portfolio.html` (o arquivo entregue aos usuários)
- `npm run check` → sintaxe do código juntado
- `python3 tests/gerar_fixtures.py` → planilhas fictícias em `fixtures/`, usadas para alimentar o Azure simulado dos testes (não há mais upload de planilha no app)
- `python3 scripts/relatorio/gerar_relatorio.py --config <config.json> --fonte simulado --fixture relatorio.xlsx` → relatório diário offline em `dist/relatorio/` (decisão `0063`; `--fonte azure` usa os PATs `AZURE_DEVOPS_PAT_<ORG>`)
- `npm test` → build + testes (`pytest`, Playwright/Chromium). Primeira vez: `pip install -r requirements-dev.txt` e `python3 -m playwright install chromium`

## Regras de trabalho

- **Antes de concluir qualquer mudança: `npm run build`, `npm run check` e `npm test` verdes.**
- **Antes de implementar uma funcionalidade, melhoria ou correção, consulte `docs/testes/`**: é o contrato das regras de negócio que a suíte protege, por domínio. Se a mudança pedida contraria uma regra documentada lá, não é um teste a ajustar sem mais — entenda a decisão relacionada antes de mexer.
- Mudou uma regra de negócio? Atualize `docs/regras-de-negocio.md`, o teste correspondente em `tests/`, a entrada correspondente em `docs/testes/` e registre o motivo em `docs/decisoes/` (novo arquivo numerado).
- O código é um script global dividido em `src/js/NN-*.js`, juntado em **ordem alfabética**: respeite a ordem ao criar arquivos. Nada de módulos, `import`, bibliotecas externas em tempo de execução ou a sequência `</script>`.
- **Nunca** versione dados reais (planilhas exportadas, `.har`, prints com dados). Testes usam só `fixtures/` e `tests/azure_simulado.py`.
- **Nunca** persista tokens do Azure (nem em `localStorage`, `IndexedDB` ou exportação). Ver `docs/decisoes/0007-token-nunca-salvo.md`.
- Textos para o usuário: claros, sem jargão, dizendo o que aconteceu e o que fazer. Mensagens de alerta seguem o padrão diagnóstico + "O que fazer".

## Onde está cada coisa

- Regras de negócio: `docs/regras-de-negocio.md`
- Integração Azure DevOps (única fonte de dados): `docs/integracao-azure.md`
- Configurações (estrutura do `CFG`, padrões, validações, as 2 abas da tela): `docs/configuracoes.md`
- Telas e funcionalidades: `docs/telas.md`
- Arquitetura e mapa dos arquivos: `docs/arquitetura.md`
- Decisões e motivos: `docs/decisoes/`
- Documentação dos testes (o que cada teste garante, entrada/saída esperada, cenário de falha coberto): `docs/testes/`
- Guia do usuário por funcionalidade (linguagem simples, "por que não está batendo com o que eu esperava"): `docs/guia-usuario/`
- Report F4P (8 quadrantes, todos implementados): `docs/backlog/report-f4p.md`, decisões em `docs/decisoes/0011` a `0031`. Pendências gerais: `docs/backlog/pendencias.md`
