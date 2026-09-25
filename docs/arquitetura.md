# Arquitetura

## Restrições (não negociáveis)

1. **Um único arquivo HTML**, aberto com dois cliques, **sem servidor** e **sem internet obrigatória** (a biblioteca SheetJS vai embutida).
2. Nenhum dado sai do computador, exceto as chamadas que o próprio usuário dispara ao Azure DevOps.
3. Tokens nunca são persistidos.
4. O código não pode conter a sequência `</script>` (quebraria o HTML único). O build verifica.

## Código-fonte

`src/index.html` (estrutura, com marcadores `/*__CSS__*/`, `/*__XLSX__*/`, `/*__APP__*/`), `src/styles.css` e `src/js/*.js`. O build junta os `.js` **em ordem alfabética**, num único script global (sem módulos): a ordem dos prefixos numéricos importa.

| Arquivo | Conteúdo |
|---|---|
| 00-cabecalho | resumo das regras, fluxos padrão (`FLOW`), níveis |
| 01-configuracao-e-regras | `CFG`, padrões, limites, categorias por time, CT por colunas, saúde/alertas (`recomputeHealth`) |
| 02-utilitarios | normalização, datas, codificação |
| 03-leitura-planilha-csv | leitura de planilha e CSV (detecção, reparo) |
| 04-modelo | `buildModel`: abas → iniciativas, releases, épicos, itens; validade; vínculos |
| 05-estado-e-calculos | estado `S`, métricas do épico, fase, visibilidade (`computeVisible`) |
| 06-renderizacao | `render`, níveis, ilhas, cards |
| 07-barbantes | desenho e roteamento dos barbantes |
| 08 a 14 | whiteboard, interação, ilhas, filtros e diagnóstico, investigação, painel de detalhes, minimapa |
| 15-visao-analitica | painel da visão analítica |
| 16 a 19 | higiene, filtros e carga da planilha, dados de exemplo, tela de configurações |
| 20 a 22 | Azure: conexões e fontes, carga, janela de progresso e cache |

## Fluxo de dados

```
planilha / CSV / Azure  →  "abas" {headers, rows, flow?}  →  buildModel()  →  recomputeHealth()  →  computeVisible()  →  render()
```

- `S` (estado da tela), `CFG` (configuração), `AZ` (sessão do Azure, com tokens em memória).
- Após salvar configurações: `recomputeHealth()` + `render()`.

## Build e testes

- `npm run build` → `dist/mapa_portfolio.html`.
- `npm run check` → sintaxe do código juntado.
- `npm test` → build + `pytest` (Playwright/Chromium) com dados fictícios e Azure simulado.
- Antes de qualquer entrega: build, check e testes verdes.
