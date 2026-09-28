# Pendências registradas

Revisado em 2026-09-28: o item "Report F4P" saiu da lista (os 8 quadrantes estão completos, sem
nenhum item de checklist em aberto em `report-f4p.md`) — ver `docs/backlog/entregas.md` para o
histórico de entregas por PR.

| # | Tema | Situação |
|---|---|---|
| 1 | Carga incremental do Azure | Cada atualização recarrega tudo. Ideia: filtrar o histórico por `ChangedDate` desde a última carga (o Analytics aceita). |
| 2 | IDs repetidos entre organizações | Hoje os itens são identificados só pelo número. Relevante se houver épicos em mais de uma organização. |
| 3 | Política de colunas antigas | O mapeamento já pode ser revisto e ajustado depois, em Configurações (decisão `0033`). Falta só decidir a política de origem: hoje o padrão é sempre "ignorar" colunas que não existem mais no quadro atual (igual à ActionableAgile); definir se o portal deve oferecer "mapear automaticamente" como alternativa configurável por organização. |
| 4 | Diferenças residuais das datas | ~4% dos itens do CORE que voltaram de coluna (saíram do quadro e voltaram ao Backlog). |
| 5 | Organização da tela de Configurações | Parcialmente resolvido (decisão `0032`): agora são 2 abas (Azure DevOps; Configurações gerais). A aba Geral ainda concentra muitas seções (Alertas, Fluxo, Tags, Aparência, Visão analítica, Report F4P); considerar dividir mais. |
| 6 | Testes de interface visual | A suíte cobre regras e fluxos; não há comparação de capturas de tela. |
