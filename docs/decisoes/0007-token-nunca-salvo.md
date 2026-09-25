# 0007 · Token (PAT) nunca é salvo

**Contexto.** Guardar o PAT no navegador ou no arquivo de configuração daria acesso ao Azure a quem obtivesse o arquivo ou a máquina.
**Decisão.** Token só em memória; pedido a cada abertura, na hora de carregar; exportação sem tokens; importação deixa organizações "Aguardando token". Os dados carregados ficam em cache (IndexedDB) para consulta sem token.
**Consequências.** O usuário digita o token a cada sessão em que for atualizar os dados.
