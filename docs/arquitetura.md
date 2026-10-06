# Arquitetura

## Restrições (não negociáveis)

1. **Um único arquivo HTML**, aberto com dois cliques, **sem servidor**. Internet e uma conexão com o Azure DevOps são obrigatórias no primeiro acesso e em toda atualização de dados (ver decisão `0032`); sem conexão, o portal só permite consultar os dados já carregados/guardados neste navegador.
2. Nenhum dado sai do computador, exceto as chamadas que o próprio usuário dispara ao Azure DevOps.
3. Tokens nunca são persistidos.
4. O código não pode conter a sequência `</script>` (quebraria o HTML único). O build verifica.

## Código-fonte

`src/index.html` (estrutura, com marcadores `/*__CSS__*/` e `/*__APP__*/`), `src/styles.css` e `src/js/*.js`. O build junta os `.js` **em ordem alfabética**, num único script global (sem módulos): a ordem dos prefixos numéricos importa. Alguns números ficaram sem arquivo (03, 18) depois da remoção da carga por planilha (decisão `0032`) — não precisam ser preenchidos, só a ordem importa.

| Arquivo | Conteúdo |
|---|---|
| 00-cabecalho | resumo das regras, fluxos padrão (`FLOW`), níveis |
| 01-configuracao-e-regras | `CFG`, padrões, limites, categorias por time, CT por colunas, saúde/alertas (`recomputeHealth`) |
| 02-utilitarios | normalização, datas, codificação |
| 04-modelo | `buildModel`: abas → iniciativas, releases, épicos, itens; validade; vínculos |
| 05-estado-e-calculos | estado `S`, métricas do épico, fase, visibilidade (`computeVisible`) |
| 06-renderizacao | `render`, níveis, ilhas, cards |
| 07-barbantes | desenho e roteamento dos barbantes |
| 08 a 14 | whiteboard, interação, ilhas, filtros e diagnóstico, investigação, painel de detalhes, minimapa |
| 15-visao-analitica | painel da visão analítica |
| 16 a 19 | higiene, filtros e carga (`loadTables`), tela de configurações (2 abas: Azure DevOps sempre acessível; Configurações gerais travada até a 1ª carga) |
| 20 a 22 | Azure: conexões e fontes, carga, janela de progresso e cache — única fonte de dados do portal |

## Fluxo de dados

```
Azure DevOps  →  "abas" {headers, rows, flow}  →  buildModel()  →  recomputeHealth()  →  computeVisible()  →  render()
```

- `S` (estado da tela), `CFG` (configuração), `AZ` (sessão do Azure, com tokens em memória).
- Após salvar configurações: `recomputeHealth()` + `render()`.

## Build e testes

- `npm run build` → `dist/mapa_portfolio.html`.
- `npm run check` → sintaxe do código juntado.
- `npm test` → build + `pytest` (Playwright/Chromium) com dados fictícios e Azure simulado.
- Antes de qualquer entrega: build, check e testes verdes.

## Relatório diário offline (`scripts/relatorio/`)

Fora do portal (que continua sendo um único HTML sem servidor): um gerador em Python + Playwright que abre `dist/mapa_portfolio.html` num Chromium sem interface, carrega os dados pelo `azRun` e captura o que as funções do próprio portal calculam (decisão `0063`). Gera um HTML único offline com menu lateral.

| Arquivo | Conteúdo |
|---|---|
| `gerar_relatorio.py` | CLI: carga, escolha do roadmap vigente e dos times comprometidos, captura da Visão Analítica, montagem do arquivo |
| `ponte_azure.py` | Atende as chamadas do portal ao Azure com o PAT de `AZURE_DEVOPS_PAT_<ORG>`; o navegador nunca vê o token |
| `modelo.html` | Casca (menu lateral de 3 grupos) com o CSS do portal embutido |

`--fonte simulado` usa o Azure simulado dos testes (`fixtures/relatorio.xlsx`); `--fonte azure` usa o Azure real. Saída em `dist/relatorio/` (nunca versionar).
