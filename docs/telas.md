# Telas e funcionalidades

## Quadro (whiteboard)

- Níveis empilhados e centralizados: Iniciativas → Releases → Épicos → Operacional dos times. Clicar num card abre o nível abaixo; "Abrir cadeia completa" abre tudo.
- **Ilhas**: cada nível e cada time é uma ilha com borda. Times distribuídos em fileiras equilibradas (maiores primeiro). Colunas com mais de 6 itens quebram em subcolunas.
- **Barbantes** ligam pai e filho; cor = saúde do filho. No modo cadeia completa, épico → ilha do time (agregado) e, com foco num épico, item a item.
- **Ancorar/soltar ilhas**: soltas, podem ser arrastadas; ao ancorar, um roteador (A* numa grade) redesenha os barbantes contornando as ilhas.
- **Zoom/arrastar**, **minimapa**, **navegador de times** ("Ir para"), iniciativas recolhidas quando uma é selecionada.
- **Etapas vazias** (opção, ligada por padrão) e **itens sem desdobramento** (opção, ligada por padrão).

## Filtros e busca

- Filtros: Roadmap executivo, Responsável (busca por qualquer parte do nome, múltipla escolha), Roadmap interno, Time (dinâmico: inclui times cadastrados sem carga), Iniciativa (ID ou nome).
- Filtros ativos ficam destacados; "Limpar filtros (N)".
- **Ir para qualquer ID**: abre a cadeia até o item. Se estiver escondido, o aviso ao lado do campo diz qual filtro esconde e oferece limpar e ir; se for regra de exibição, oferece a investigação.
- **Diagnóstico de quadro vazio**: explica qual filtro zerou o resultado e quantas iniciativas aparecem sem cada um.

## Investigação por ID

Percorre as etapas e para na primeira que falhar: retornou nos dados (ou foi excluído como Removed, ou não veio da fonte) → reconhecido → cadeia válida / regra de exibição → filtros → recolhido.

## Painel de detalhes

Alertas com diagnóstico, medidor e "O que fazer"; resumo nos pais; campos; "Como o CT foi calculado" (épico); itens por categoria (épico); campos adicionais; rastreabilidade ("Por que está aqui"); link para o Azure DevOps.

## Visão analítica

Painel lateral (aba "Visão analítica") habilitado com Time + Roadmap. Tabela no formato do slide de roadmap do time, ordenável, com "Copiar tabela". Regras em `docs/regras-de-negocio.md` §10.

## Report F4P

Em construção. Especificação: `docs/backlog/report-f4p.md`.

## Higiene de dados

Relatório de importação, carga do Azure, órfãos, épicos inválidos, releases sem iniciativa.

## Configurações

Ver `docs/configuracoes.md`.

## Carga do Azure DevOps

Botão "Azure DevOps": pede tokens das organizações usadas, mostra o plano de execução (terminal), pede mapeamento de colunas antigas na primeira carga. Ver `docs/integracao-azure.md`.
