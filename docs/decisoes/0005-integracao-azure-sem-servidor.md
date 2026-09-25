# 0005 · Integração direta com o Azure DevOps (brainstorm concluído)

**Contexto.** A planilha vinha de uma extensão (ActionableAgile) e precisava ser recarregada após cada ajuste no Azure. O brainstorm "azure devops" foi tratado como conceito em análise, com prova de conceito, e depois aprovado e incorporado.
**Decisão.** O navegador chama as APIs REST e o Analytics (OData) diretamente, usando PAT. Planilha e Azure convivem como formas de carga; o Azure gera os mesmos dados da planilha.
**Consequências.** Sem servidor; CORS confirmado em uso real. Carga completa por atualização (incremental é pendência).
