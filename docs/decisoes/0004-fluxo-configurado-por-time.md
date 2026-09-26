# 0004 · Configuração do fluxo por time

**Contexto.** Cada time tem colunas próprias (ex.: BO usa "Em Desenv.", outros "Desenvolvimento Doing"); uma configuração única para todos gerava resultados errados.
**Decisão.** Categorias (Nenhum/Discovery/WIP/Vazão) e colunas do CT configuradas por time, em abas. Configuração antiga (única) é convertida.
**Consequências.** Métricas do épico, fase, alertas e CT consultam a configuração do time de cada item.
