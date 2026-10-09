# Configurações — guia do usuário

## O que é

A tela onde você ajusta as regras do portal para a realidade de cada time: limites de alerta,
mapeamento de colunas do fluxo, tags, campos adicionais e os parâmetros do Report F4P. Também é onde
você cadastra as conexões com o Azure DevOps — esse pedaço específico tem seu próprio guia, em
`docs/guia-usuario/azure-devops.md`.

## Como acessar

Duas abas:

- **Azure DevOps** — conexões, organizações e fontes de dados. Sempre acessível, mesmo antes da
  primeira carga (é, inclusive, a tela que abre forçada no primeiro acesso ao portal — ver
  `docs/guia-usuario/azure-devops.md`).
- **Configurações gerais** — todo o resto: alertas por time, fluxo, tags, cores, campos adicionais,
  parâmetros do Report F4P. Fica **desabilitada** até a primeira carga de dados — antes disso não
  existem times, tipos nem colunas de fluxo reais para configurar.

## Como funciona

### O que dá para ajustar na aba Geral

| O que | Onde mexe |
|---|---|
| Limites de alerta por time (atenção, máximo, outlier, parado) | atrasa/acelera quando um item vira "atenção", "atraso" ou "outlier" (`docs/guia-usuario/quadro.md` § Painel de detalhes) |
| Fluxo de cada time (categoria de cada coluna: Nenhum/Discovery/WIP/Vazão; quais colunas entram no CycleTime; quais são "Fila de espera") | decide a fase dos épicos na Visão Analítica e no card do quadro, o CycleTime calculado, e a Eficiência de fluxo do Report F4P |
| Tipos considerados no CycleTime do épico (`ctTypes`) | também é a mesma lista usada pela Reserva do Report F4P e pelo Burnup Reserva do Actionable |
| Tags cadastradas (nome, cor, nível de alerta) | cor de fundo do card, alertas de tag |
| Campos adicionais exibidos nos cards | o que aparece no painel de detalhes além dos campos padrão |
| Tag de capacidade do roadmap (`anTag`, padrão `ROADMAP`) e "Dias antes do fim do semestre" (`anFreeze`) | decide o que conta como "reservado" na Visão Analítica e o dead line calculado |
| Parâmetros do Report F4P (meses da amostra, tipos considerados por quadrante, metas por time) | ver `docs/guia-usuario/report-f4p.md` |

### Validações ao salvar

A tela **não salva nada** se alguma regra básica for violada — a mensagem de erro aparece no topo e os
valores digitados continuam no formulário (nada se perde, você só precisa corrigir):

- Por time: limite de atenção < CT máximo < outlier.
- Fluxo de cada time: pelo menos **duas** colunas marcadas para "Entra no CT" (senão o CycleTime
  daquele time fica indefinido).
- Report F4P: `min`/`max` da variabilidade esperada só valem preenchidos os dois juntos, com `min` <
  `max`; o mesmo vale para a faixa de Eficiência de fluxo (`effMin`/`effMax`). As metas de Urgente e
  Technical Story são independentes — podem ser preenchidas isoladamente, inclusive com zero.

### Exportar/Importar e os botões do rodapé

- **Exportar**: gera um arquivo `.json` com toda a configuração — **nunca inclui o token** do Azure
  DevOps, mesmo que ele esteja em memória no momento da exportação (ver "Perguntas frequentes" abaixo).
  Serve para levar a configuração para outra máquina ou guardar backup.
- **Importar**: lê esse arquivo de volta, convertendo formatos antigos automaticamente se necessário.
- **Restaurar padrão**: volta as regras (alertas, fluxo, tags, cores…) para o padrão de fábrica — mantém
  as conexões, fontes e os dados já carregados intactos.
- **Limpar tudo e reiniciar**: apaga configuração, conexões, fontes, mapeamentos, o cache de dados do
  Azure e os tokens da sessão — volta o portal exatamente ao estado de primeiro acesso. Oferece
  exportar antes de apagar.

## Perguntas frequentes ("não está batendo com o que eu esperava")

### "Fui em Configurações e a aba Geral está desabilitada, cinza"

Esperado antes da primeira carga de dados: a aba Geral depende de saber quais times, tipos e colunas de
fluxo existem de verdade, o que só é possível depois de carregar algo do Azure DevOps pelo menos uma
vez. Carregue os dados pela aba Azure DevOps primeiro (`docs/guia-usuario/azure-devops.md`) — a aba
Geral libera automaticamente depois disso.

### "Cliquei em Salvar e nada foi salvo, só apareceu uma mensagem em vermelho"

É a validação funcionando como esperado — algo no formulário está inconsistente (ex.: limite de
"atenção" maior ou igual ao "máximo" de algum time, ou um time com menos de duas colunas marcadas para
CT). A mensagem cita qual time e qual regra. Nada é salvo até a inconsistência ser corrigida, e os
valores que você digitou continuam no formulário — não é preciso preencher tudo de novo.

### "Exportei a configuração para enviar para outra pessoa — o token do Azure vai nesse arquivo?"

Não, nunca. O token de acesso só existe em memória enquanto a aba do navegador está aberta — não é
salvo em lugar nenhum, nem no arquivo de configuração, nem no `localStorage`, nem no cache local
(ver `docs/decisoes/0007-token-nunca-salvo.md`). O arquivo exportado traz o nome das organizações e
fontes cadastradas, mas a credencial de acesso nunca viaja com ele.

### "Mudei o 'Dias antes do fim do semestre' e o dead line da Visão Analítica não mudou do jeito que eu esperava"

Esse campo entra direto na fórmula do dead line: `fim do semestre − dias antes do fim do semestre − CT
máximo do time`. O texto de ajuda ao lado do campo, na própria tela, mostra essa fórmula com um exemplo
numérico — vale reler se o resultado não bateu com a expectativa, porque o CT máximo do time (outro
campo, configurado por time) também entra na conta.

### "Cliquei em 'Limpar tudo e reiniciar' — perdi mesmo tudo?"

Sim, de propósito: configuração, conexões, fontes, mapeamentos de colunas antigas, o cache de dados do
Azure e os tokens da sessão são todos apagados, e o portal volta ao estado de primeiro acesso. A tela
oferece exportar a configuração antes de confirmar — se você não exportou antes de clicar, não há como
desfazer.

## Cenários

### Aba Geral libera depois da primeira carga

**Cenário de sucesso: primeira carga concluída libera a aba**
- Dado nenhuma carga de dados feita ainda
- Quando o usuário completa a primeira carga pela aba Azure DevOps
- Então a aba Configurações gerais deixa de estar desabilitada e mostra os times/colunas reais

**Cenário de comportamento inesperado: tentar configurar fluxo antes da primeira carga**
- Dado nenhuma carga de dados feita ainda
- Quando o usuário tenta abrir a aba Configurações gerais
- Então a aba continua desabilitada — não há nenhum time ou coluna de fluxo real para configurar ainda

### Validação de limites crescentes bloqueia o salvamento

**Cenário de sucesso: limites na ordem certa salvam normalmente**
- Dado um time com atenção = 30, máximo = 60, outlier = 90
- Quando o usuário salva
- Então a configuração é salva sem erro

**Cenário de comportamento inesperado: atenção maior que o máximo**
- Dado um time com atenção = 12 e máximo = 10 (invertido)
- Quando o usuário clica em Salvar
- Então aparece o erro "atenção precisa ser menor...", nada é salvo, e a tela de Configurações
  continua aberta com os valores digitados preservados

### Exportação nunca leva o token

**Cenário de sucesso: exportação traz organização, sem o token**
- Dado uma organização cadastrada com token válido em memória
- Quando o usuário clica em Exportar
- Então o arquivo gerado contém o nome da organização, mas não contém o valor do token em nenhum lugar

## Regras de negócio relacionadas

- `docs/configuracoes.md` (estrutura completa do `CFG`, todas as chaves e seus padrões).
- `docs/regras-de-negocio.md` §6 (CycleTime), §7 (Categorias de coluna e fase), §8.1 (Alertas de CT),
  §10 (Visão analítica — `anTag`/`anFreeze`).
- Decisões: [`0007`](../decisoes/0007-token-nunca-salvo.md) (token nunca salvo — regra
  não-negociável), [`0032`](../decisoes/0032-azure-devops-unica-fonte-de-dados.md) (as duas abas, gate
  do primeiro acesso), [`0037`](../decisoes/0037-dias-antes-do-semestre-ajuda-e-padrao-10.md) ("Dias
  antes do fim do semestre").
- Detalhe exaustivo de cobertura de teste:
  [`docs/testes/configuracoes.md`](../testes/configuracoes.md).
