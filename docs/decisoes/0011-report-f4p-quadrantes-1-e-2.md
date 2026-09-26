# 0011 — Report F4P: Quadrantes 1 e 2, times exibidos e ilustrações

## Contexto

`docs/backlog/report-f4p.md` especifica a tela Report F4P e lista, em "Decisões propostas", pontos a confirmar com o usuário ao implementar. O usuário aprovou seguir as decisões propostas no documento e forneceu um slide de referência (design) para o layout visual, autorizando criar ilustrações originais inspiradas nele em vez de reproduzi-lo literalmente.

## Decisões

1. **Times exibidos**: o documento diz "todos os times ativos na configuração". Interpretamos isso como **todos os times atualmente carregados** (`S.model.teams`), o mesmo conjunto que aparece como colunas no quadro — e não a lista da tela de Configurações (`cfgTeams`), que deliberadamente **exclui** os times dos dados de exemplo. Com a lista de Configurações, o Report F4P ficaria vazio sempre que o usuário estivesse vendo os dados de exemplo (o estado padrão da aplicação), o que não faz sentido para uma tela de relatório. Se o comportamento pretendido for "só os times com CT planejado nas configurações", é só trocar `f4pTeams()` em `src/js/23-report-f4p.js`.

2. **Decisões propostas do documento, adotadas como especificado**:
   - Amostra: itens concluídos (com `o.deploy`), dos tipos configurados, com saída nos últimos N meses, de **todos** os itens do time (sem filtrar pelo roadmap selecionado).
   - Percentil por interpolação linear, igual ao `PERCENTIL.INC` do Excel (função `percentil` em `src/js/02-utilitarios.js`).
   - Indicadores: CT com P95 > máximo → ▼ vermelho; ≤ máximo → ▲ verde. Variabilidade > máximo → ▼ vermelho; dentro da faixa → ▲ verde; < mínimo → ▼ laranja.
   - P50 = 0 (ou amostra vazia) → variabilidade "--"; o tamanho da amostra (n) e o P50 ficam no atributo `title` da célula (dica ao passar o mouse), em vez de sempre visíveis, para não poluir a grade com 8 quadrantes × N times.

3. **Ilustrações**: o slide de referência usa arte de um deck de consultoria (ícones "Healthy Range", "Fitness Criteria KPIs", "Vanity Metrics", cartões do produto) que não pertence à identidade visual do portal (hoje só tipografia e tabelas, sem imagens, para caber num único HTML sem dependências externas). Em vez de reproduzir essas imagens (o que exigiria embutir arquivos binários em base64, aumentando o HTML e destoando do restante da interface), criamos **4 ícones SVG inline originais**, pequenos (~200–400 bytes cada, sem gradientes nem filtros) e na paleta de cores já usada pelo portal:
   - "faixa/range" (Variabilidade, Eficiência de fluxo) — inspirado no medidor "Healthy Range".
   - "mostrador" (CycleTime) — inspirado no "Fitness Criteria KPIs".
   - "alvo" (Roadmap–Épicos, Vazão) — remete a "ter uma meta e ser temporário".
   - "rede" (Urgente, Technical Story, User Story) — remete a métricas de contagem ("Vanity Metrics").

   Cores dos indicadores reaproveitam a paleta existente: `#1E8E3E` (verde, mesmo tom já usado em "Entregue"/`idb` na Visão analítica) para ▲, `var(--alert)` para ▼ vermelho, `var(--warn)` para ▼ laranja — em vez do verde institucional do slide original.

4. **Quadrantes 3–8** ("em definição"): aparecem na mesma grade e com as mesmas colunas de time dos dois primeiros, mostrando "--" e uma nota "Regra de cálculo ainda em definição.", para já fixar o layout final e não exigir retrabalho quando as regras forem definidas (`docs/backlog/pendencias.md`).

> **Atualização**: o item 3 (ilustrações) foi substituído — ver `docs/decisoes/0012-report-f4p-ilustracoes-reais.md`. O usuário forneceu as imagens originais do slide de referência e pediu para usá-las; os SVGs inline descritos abaixo saíram do código.

## Consequências

- `f4pTeams()` isolado em uma função (`src/js/23-report-f4p.js`) para facilitar trocar a lista de times, se necessário.
- Nova seção de configuração "Report F4P" (`src/js/19-tela-configuracoes.js`): período do P95/P50, tipos considerados e variabilidade mínima/máxima por time — mesmo padrão visual das seções "Alertas por time" e "Visão analítica" já existentes.
- Duas abas laterais (Visão analítica e Report F4P) passam a coexistir; abrir uma fecha a outra (mesma faixa de tela, mesmo `left:0`). O botão-aba antes específico da Visão analítica (`.an-tab`) virou a classe genérica `.side-tab`, empilhada num contêiner `.side-tabs`.
