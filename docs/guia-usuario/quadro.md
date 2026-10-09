# Quadro (whiteboard) — guia do usuário

## O que é

É a tela principal do Portal: a visualização em cadeia **Iniciativa → Release → Épico → itens dos
times**, organizada em faixas ("ilhas") ligadas por linhas de conexão ("barbantes"). É de onde você
navega para qualquer outra funcionalidade (filtros, painéis, configurações) — as outras telas deste
guia são, em geral, complementos que você abre a partir daqui.

## Como funciona

### Níveis e navegação

- Quatro faixas lado a lado: Iniciativas, Releases, Épicos e Operacional dos times.
- Clicar num card abre o nível abaixo dele (ex.: clicar numa iniciativa mostra as releases dela).
  "Abrir cadeia completa" abre os quatro níveis de uma vez, com os times agregados numa ilha própria
  por time.
- Com a Visão Analítica, o Report F4P ou o Actionable abertos, clicar em qualquer lugar do quadro —
  num card ou numa área vazia — fecha o painel, sem precisar ir até o botão "«" no canto dele. Um
  card clicado continua respondendo normalmente (abre o nível abaixo, seleciona). Arrastar o quadro
  (pan) não fecha o painel — só um clique de verdade, sem arrastar.
- Cada nível, e cada time (no modo cadeia completa), é uma **ilha** com borda própria. Times são
  distribuídos em fileiras equilibradas (os maiores primeiro); uma coluna do fluxo com mais de 6 itens
  quebra automaticamente em subcolunas, para não ficar uma lista vertical enorme.
- **Barbantes** ligam um card ao pai dele; a cor do barbante é a saúde do filho (ver "Painel de
  detalhes" abaixo — mesma escala de alerta). No modo cadeia completa, o barbante liga o épico à ilha
  do time (agregado); com um épico em foco, liga item a item.

### Organizar o quadro manualmente

- **Zoom/arrastar** o quadro inteiro, **minimapa** (canto da tela) para se orientar em cadeias
  grandes, e um **navegador de times** ("Ir para") para saltar direto a um time.
- **Ancorar/soltar ilhas**: por padrão as ilhas ficam ancoradas (um roteador em grade redesenha os
  barbantes contornando as ilhas automaticamente). Soltando uma ilha, você pode arrastá-la livremente
  para organizar a tela como preferir.
- Essa posição arrastada é um **deslocamento relativo** ao lugar que a ilha tinha no momento do
  arrasto — não uma coordenada fixa do conteúdo. Por isso ela só vale para a combinação atual de
  filtros, busca e iniciativa selecionada: mudar qualquer um deles descarta as posições manuais, já
  que uma posição pensada para uma cadeia pode sobrepor conteúdo diferente numa cadeia menor ou maior.
  Alternar uma opção que não muda o que está visível (ex.: "Mostrar etapas vazias") não descarta nada.

### Lista de Iniciativas: recolhida ou todas visíveis

- Por padrão, selecionar uma iniciativa recolhe a lista para mostrar só ela — útil com muitas
  iniciativas na tela.
- A opção **"Manter todas as iniciativas visíveis"** (desligada por padrão) muda esse comportamento: a
  lista continua mostrando **todas** as iniciativas do filtro atual, com a selecionada destacada (borda
  de foco) e as demais esmaecidas — para você voltar e continuar analisando as próximas sem perder o
  lugar. É uma preferência da sua sessão, não do item selecionado: continua ligada ao trocar de
  iniciativa, até você mesmo desligá-la.

### Etapas vazias e itens sem desdobramento

Duas opções na barra de filtros, ligadas por padrão:

- **Mostrar etapas vazias**: mantém colunas do fluxo sem nenhum item visíveis no quadro (em vez de
  comprimir, mostrando só as colunas com algo dentro).
- **Mostrar itens sem desdobramento**: uma iniciativa sem nenhuma release (ou uma release sem nenhum
  épico) ainda aparece no quadro, com um selo "sem release"/"sem épico" — exceto se já estiver na
  última coluna do fluxo (concluída), caso em que ela simplesmente não aparece, por já estar fechada
  sem nunca ter tido desdobramento. Desligando a opção, só a cadeia completa (com desdobramento válido)
  aparece.

## Painel de detalhes

Clicar em qualquer card (iniciativa, release, épico ou item de time) abre o painel de detalhes, pela
lateral da tela. Ele reúne, para aquele item:

- **Alertas** com diagnóstico (ex.: "já consumiu 90% do CT máximo…"), um medidor visual e "O que
  fazer" — nunca só o nome do alerta, sempre a ação sugerida.
- **Resumo** (nos pais — épico, release, iniciativa): agrupa os alertas dos filhos e sugere a
  prioridade (bloqueios primeiro).
- **Campos** do item e **campos adicionais** configuráveis (Configurações › Campos adicionais).
- No épico: **"Como o CT foi calculado"** — qual item deu a data de início, qual deu a data de fim, e
  a contagem de itens por categoria de fluxo (Backlog/Discovery/WIP/Vazão).
- **Rastreabilidade** ("Por que está aqui"): explica o vínculo do item com o pai (ex.: por qual campo
  ele foi ligado ao épico).
- **Link direto para o Azure DevOps** daquele item.

## Perguntas frequentes ("não está batendo com o que eu esperava")

### "Arrastei uma ilha para organizar o quadro, mas da próxima vez que abri ela voltou ao lugar"

Esperado: a posição arrastada é relativa à cadeia que estava visível no momento do arrasto (filtro,
busca e iniciativa selecionada). Mudar qualquer um desses três descarta a posição manual — ela não faz
sentido automaticamente numa cadeia diferente, que pode ter outra altura ou outro conteúdo no mesmo
lugar. Ligar/desligar uma opção que não muda o que aparece (ex.: "Mostrar etapas vazias") não descarta
a posição.

### "Liguei 'Manter todas as iniciativas visíveis' e cliquei em outra iniciativa — a lista recolheu de novo?"

Não deveria: é uma preferência da sua sessão, não algo ligado à seleção atual. Selecionar outra
iniciativa move o destaque (borda de foco) para a nova selecionada, mas a lista continua mostrando
todas, com as demais esmaecidas. Se a lista recolher mesmo assim, confira se o checkbox "Manter todas
as iniciativas visíveis" realmente ficou marcado.

### "Uma iniciativa aparece com o selo 'sem release' em vez de 'aberto'"

É o comportamento esperado quando ela não tem nenhuma release vinculada (ou nenhuma válida) — o selo
avisa que falta desdobramento, em vez de mostrar "aberto" como se o trabalho já tivesse uma release em
andamento. O mesmo vale para uma release com o selo "sem épico". Se a opção "Mostrar itens sem
desdobramento" estiver desligada, esses casos somem do quadro em vez de aparecer com o selo.

### "O painel de detalhes mostra um alerta amarelo (atenção) em vez de vermelho (atraso) para um item que já está demorando bastante"

Os limites de CycleTime (quando vira "atenção", "atraso" ou "outlier") são configuráveis **por time**
em Configurações › Fluxo dos times — sem essa configuração, vale a regra geral (30/60/90 dias). Um item
que parece demorado para você pode ainda estar dentro do limite de "atenção" daquele time específico.
Veja `docs/guia-usuario/configuracoes.md` para como ajustar esses limites.

## Cenários

### Posição manual de uma ilha some ao mudar o filtro

**Cenário de sucesso: posição sobrevive a uma mudança que não afeta o conteúdo**
- Dado uma ilha solta e arrastada manualmente
- Quando o usuário liga/desliga "Mostrar etapas vazias" (sem mudar filtro, busca ou iniciativa)
- Então a posição arrastada continua exatamente onde foi deixada

**Cenário de comportamento inesperado: posição é descartada ao mudar o filtro**
- Dado a mesma ilha solta e arrastada
- Quando o usuário troca o filtro de Time
- Então a posição arrastada é descartada — a ilha volta à posição automática da nova cadeia

### "Manter todas as iniciativas visíveis" não reseta ao trocar de seleção

**Cenário de sucesso: preferência persiste entre seleções**
- Dado "Manter todas as iniciativas visíveis" ligado e uma iniciativa selecionada
- Quando o usuário clica em outra iniciativa da lista
- Então a opção continua ligada, a lista continua mostrando todas, e o destaque de foco move para a
  nova selecionada

**Cenário de comportamento inesperado (como era antes desta opção existir): cada seleção recolhia a lista**
- Dado o link antigo "Mostrar todas" (substituído por este checkbox)
- Quando o usuário selecionava outra iniciativa
- Então a lista recolhia de novo, obrigando a clicar "Mostrar todas" repetidamente — por isso a opção
  atual existe como preferência persistente, não como estado da seleção

## Regras de negócio relacionadas

- `docs/regras-de-negocio.md` §3 (Visibilidade no quadro — regra B), §6.2 (CT do épico), §7
  (Categorias de coluna e fase), §8 (Alertas), §9 (Tags cadastradas).
- Decisões: [`0003`](../decisoes/0003-regra-b-itens-sem-desdobramento.md) (itens sem desdobramento),
  [`0021`](../decisoes/0021-manter-iniciativas-visiveis.md) (manter iniciativas visíveis),
  [`0040`](../decisoes/0040-offsets-de-ilhas-descartados-por-contexto.md) (ilhas soltas — posição
  descartada por contexto), [`0065`](../decisoes/0065-clicar-no-whiteboard-fecha-painel-lateral.md)
  (clicar no whiteboard fecha o painel lateral aberto).
- Detalhe exaustivo de cobertura de teste:
  [`docs/testes/hierarquia-e-modelo.md`](../testes/hierarquia-e-modelo.md),
  [`docs/testes/quadro-e-selecao.md`](../testes/quadro-e-selecao.md),
  [`docs/testes/ilhas-e-cadeia-completa.md`](../testes/ilhas-e-cadeia-completa.md),
  [`docs/testes/ct-alertas-tags.md`](../testes/ct-alertas-tags.md).
