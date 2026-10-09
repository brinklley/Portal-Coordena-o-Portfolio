# Guia do usuário — por funcionalidade

Esta pasta é para quem **usa** o Portal (coordenador, PM, responsável de time), não para quem
desenvolve nele. O objetivo é um único lugar para buscar resposta quando uma tela não mostra o que
você esperava — por exemplo: "selecionei o time mas o menu do Report F4P não habilita" ou "um card
está em 'Aguard. Deploy' mas a Visão Analítica mostra Status 'Entregue'".

## Diferença para as outras pastas de documentação

O portal já tem duas outras pastas de documentação, cada uma para um público diferente:

- `docs/regras-de-negocio.md` — a regra de negócio em si, densa, organizada por número de seção.
  Referência completa, não pensada para leitura corrida.
- `docs/testes/` — o que a suíte automatizada garante que continua verdade, voltado para quem mantém
  o código e os testes.
- **`docs/guia-usuario/`** (esta pasta) — a mesma regra, em linguagem direta, organizada por
  funcionalidade e por pergunta ("por que não está batendo com o que eu esperava"), com exemplos
  concretos. Termos técnicos do domínio (CycleTime, Vazão, Reserva...) aparecem quando necessários,
  sempre explicados na primeira vez.

Cada documento aqui **linka** para a seção exata de `docs/regras-de-negocio.md` e para a decisão em
`docs/decisoes/` que explica o motivo — em vez de reescrever a regra inteira, para não existirem duas
versões da mesma regra que podem divergir com o tempo. Quem quiser o detalhe técnico exaustivo segue
o link até `docs/testes/`.

## Como usar

1. Encontre o documento da funcionalidade onde a dúvida está (índice abaixo).
2. Leia **"Perguntas frequentes"** — é a seção pensada exatamente para "não está batendo com o que eu
   esperava". Se sua dúvida está ali, a resposta já cita a configuração ou a regra responsável.
3. Se quiser ver a regra "em ação" com um exemplo passo a passo, veja **"Cenários"** — Dado/Quando/Então,
   com um caso que funciona como o esperado e um caso que mostra o motivo de um resultado diferente do
   esperado.
4. Para o texto oficial da regra (ou se a dúvida não está nas perguntas frequentes), siga os links de
   **"Regras de negócio relacionadas"** no fim do documento.

## Índice

| Arquivo | Funcionalidade |
|---|---|
| [`quadro.md`](quadro.md) | Quadro (whiteboard) — tela principal, navegação e painel de detalhes |
| [`filtros-e-busca.md`](filtros-e-busca.md) | Filtros e busca — campo único, "+N ocultos" e investigação por ID |
| [`configuracoes.md`](configuracoes.md) | Configurações — as 2 abas, validações, exportar/importar |
| [`azure-devops.md`](azure-devops.md) | Conectar e carregar dados do Azure DevOps — conexões, fontes, mapeamento, higiene de dados |
| [`visao-analitica.md`](visao-analitica.md) | Visão Analítica — tabela de roadmap por time e semestre |
| [`report-f4p.md`](report-f4p.md) | Report F4P — os 8 quadrantes de indicadores, todos os times |
| [`actionable.md`](actionable.md) | Actionable — os 4 quadrantes de métricas acionáveis por time |
| [`relatorio-diario.md`](relatorio-diario.md) | Relatório diário — o arquivo offline gerado automaticamente com os 3 painéis acima |

Cobre a tela principal, os filtros, as configurações, a carga do Azure DevOps e os 3 painéis
analíticos, além do relatório diário — as áreas onde esse tipo de dúvida mais acontece. Fora do
escopo por ora: investigação por ID como tela própria (está dentro de `filtros-e-busca.md`), e
qualquer outra funcionalidade pontual não listada acima — use `docs/regras-de-negocio.md` e
`docs/telas.md` para essas.
