# 0008 · Fluxo real do quadro na carga do Azure

**Contexto.** Quadros do Open Finance terminam em "Concluído"/"Pronto", e não em "Fechado"; a carga falhava ("não encontrei as colunas de fluxo").
**Decisão.** Na carga do Azure, o fluxo é a primeira e a última coluna reais do quadro; nomes fixos só para planilhas. Vários quadros no mesmo nível têm as colunas unificadas.
**Consequências.** Times com colunas diferentes do padrão precisam configurar CT e categorias na aba do time.
