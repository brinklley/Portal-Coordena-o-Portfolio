# 0032 — Azure DevOps como única fonte de dados; Configurações em 2 abas

## Contexto

O usuário pediu duas mudanças grandes e relacionadas: (1) desabilitar a carga por planilha/CSV,
mantendo só a carga pelo Azure DevOps — sem nenhuma carga anterior, o primeiro acesso deve abrir
direto a tela de cadastro de organização e token; (2) dividir a tela de Configurações em duas
abas — uma com a configuração do Azure (conexões, organização, cadastro das fontes de Iniciativa/
Release/Épico/Times), sempre acessível, e outra com as demais configurações, habilitada só depois
da primeira carga (antes disso não há times, tipos nem colunas de fluxo para configurar).

Pedi para confirmar antes de assumir, dado o tamanho da mudança. O usuário escolheu, para as quatro
perguntas feitas, a opção de maior escopo em todas: migrar a suíte de testes inteira para o Azure
simulado (não manter um caminho paralelo por planilha), remover os dados de exemplo e o botão de
baixar modelo por completo, bloquear o app inteiro (barra de ferramentas, quadro, painéis) até a
primeira carga, e atualizar a documentação da arquitetura removendo a garantia de "sem internet
obrigatória".

## Decisões

1. **`!!S.model` é a única fonte de verdade para "já carregou alguma vez"** — não criei uma flag
   nova (`S.everLoaded` ou similar). `S.model` só é atribuído em um único lugar do código inteiro
   (`loadTables()`, `17-filtros-e-carga.js`) e nunca é resetado para `null` depois. Isso já bastava
   porque `render()` (`06-renderizacao.js`) e os poucos listeners globais fora da tela de
   Configurações já toleravam `S.model` nulo antes desta mudança (mostrando um estado vazio ou
   simplesmente não fazendo nada) — o resto do código que assume `S.model` sempre preenchido
   (a maior parte de `05-estado-e-calculos.js`, `13-painel-detalhes.js`, `16-higiene.js`,
   `11-filtros-e-diagnostico.js` e a maioria das métricas do Report F4P) só é alcançável through
   a barra de ferramentas e o quadro — que ficam escondidos pelo gate.

2. **O bloqueio ("gate") é uma classe CSS no `<body>`, não uma tela nova**: `body.gate-active`
   esconde `.top` (barra), `.viewport` (quadro), `.zoom`, `.side-tabs` e `#crumbs` com
   `display:none !important`. `.zoom` e `.side-tabs` têm `display:flex` na própria classe — o
   atributo `hidden` (regra do user-agent) perde para regra de mesma especificidade do autor, então
   não bastaria escondê-los um por um com `hidden`. `#minimap`/`#mmOpen` não precisaram entrar na
   regra (já se escondem sozinhos quando `!S.model`, via `drawMinimap`), e os painéis laterais
   (`#anPanel`/`#f4pPanel`/`#drawer`) ficam fora da tela por `transform` até o usuário abri-los pela
   barra — que está escondida. `<body class="gate-active">` é o estado inicial no HTML, e
   `loadTables()` remove a classe no sucesso (idempotente, não atrapalha cargas seguintes). Nenhum
   wrapper `<div>` novo foi necessário: `body{display:flex;flex-direction:column}` já funcionava com
   os filhos diretos, sem seletores `body >` no CSS que quebrariam com a classe a mais.

3. **A tela de Configurações é reaproveitada como a própria tela de bloqueio**, em vez de criar uma
   tela de primeiro acesso separada. Já era o padrão do código: `19-tela-configuracoes.js` já
   tratava `!S.model` com textos de espera em vez de quebrar (`typesFound`, `typesByLevel`,
   `fieldsForm`, `flowTabsHtml`), `azRender()` já funcionava só com `DRAFT`/`AZ`, e
   `$("btnAz").onclick` já redirecionava para `openCfg()` quando não havia fontes configuradas.
   Faltava só completar esse padrão:
   - `cfgForm()` passou a renderizar duas abas (`data-cfgtab2="az"`/`"geral"`, estado `S.cfgTab2`,
     mesmo padrão do `S.cfgTab` já usado nas sub-abas de fluxo por time). A aba Geral vem
     `disabled` quando `!S.model`. As duas divs de aba ficam **sempre no DOM**, só `hidden` — nunca
     omitidas —, porque `readForm()` faz leituras diretas e sem guarda (`$("cfgWarn").value` etc.);
     se a aba sumisse do DOM, salvar quebraria com `TypeError`.
   - `closeCfg()` ganhou um guard único (`if (!S.model) return;`) que cobre, de graça, os botões
     Fechar/Cancelar, o clique no fundo, a tecla Esc **e** o fechamento automático no fim de
     `cfgSave` — sem isso, salvar a configuração do Azure em modo bloqueio fecharia a tela com o
     app inteiro ainda escondido.
   - `$("btnAz").onclick` virou a função nomeada `openAzureLoadModal()`, reaproveitada por um novo
     botão "Carregar dados do Azure DevOps" dentro da aba Azure quando `!S.model` e já há fontes
     cadastradas. Esse botão salva o rascunho direto (`readForm()` + `CFG = DRAFT` + `saveCfg()`)
     antes de abrir o modal de carga, em vez de exigir clicar em "Salvar" primeiro e depois no
     botão — evita um loop confuso, já que `openAzureLoadModal()` lê `CFG`, não `DRAFT`.
   - `azApply()` passou a fechar também a tela de Configurações (`closeCfg()`) quando ela estiver
     aberta, depois que `loadTables()` tiver sucesso — fecha a tela de bloqueio automaticamente ao
     terminar a primeira carga.

4. **Migração da suíte de testes**: a suíte inteira (141 chamadas a `carregar(page, "x.xlsx")` em 9
   arquivos, `test_report_f4p.py` sozinho com 106) carregava dados pelo upload de planilha
   (`#file`), o mesmo caminho que está sendo removido do app. Em vez de reescrever os 141 pontos de
   chamada, mantive a assinatura de `carregar(pg, nome, **azure_kwargs)` idêntica e troquei sua
   implementação por dentro: carrega a fixture pelo Azure simulado (`tests/azure_simulado.py`,
   generalizado para aceitar qualquer arquivo — antes só funcionava com `times.xlsx`), injeta
   `CFG.azure.orgs`/`sources`/`AZ.tokens` via `page.evaluate` e chama `azRun()` diretamente (sem
   clique de botão — mais rápido, e continua exercitando o pipeline real de carga:
   `azLoadSource`/`azBuildTables`/`loadTables`). Os 139 pontos de chamada fora de
   `test_azure.py`/`test_carga_planilha.py` não mudaram uma linha.
   - Os dois casos extremos do simulado (item no estado Removed, coluna renomeada no histórico —
     exigem uma fixture com "TIME CORE", como `times.xlsx`) viraram **flags opcionais**
     (`item_removido`/`coluna_antiga`), desligadas por padrão — senão o diálogo de mapeamento de
     colunas travaria as outras 138 chamadas genéricas esperando uma confirmação que ninguém dá.
   - `FONTES` (lista fixa de 10 fontes, hardcoded para os 6 times de `times.xlsx`) virou
     `fontes_de(sim)`, derivada dinamicamente de `sim.quadros` — funciona para qualquer fixture.
   - **Bug de generalização encontrado e corrigido durante a migração**: o campo Assigned To das
     Iniciativas/Releases/Épicos no simulado estava fixo em "Fulano de Tal", em vez de vir da
     própria linha da planilha. Isso não quebrava nada com `times.xlsx` (nenhum teste depende do
     Assigned To dela), mas quebrava `fixtures/responsaveis.xlsx` por completo — criada
     especificamente para stress-testar o filtro por responsável com ~280 nomes distintos. Corrigido
     com um novo helper `_pessoa(v)` que reconstrói `{displayName, uniqueName}` a partir do texto
     "Nome &lt;email&gt;" da coluna, o mesmo formato que `azPerson()` (`21-azure-carga.js`) espera
     para remontar essa coluna a partir do campo real do Azure. Achado rodando a suíte inteira contra
     o novo `carregar()` antes de virar a chave do boot — a suíte foi validada em duas etapas (com o
     boot ainda em modo planilha/demo, e só depois com o boot já trocado) exatamente para conseguir
     isolar esse tipo de problema de forma mais barata.
   - `tests/test_carga_planilha.py` foi apagado por completo: seus 3 testes cobriam só recursos
     removidos (dados de exemplo fora da configuração, parsing de planilha por upload, reparo de CSV
     dentro de célula). `tests/gerar_fixtures.py::csv_nas_abas` (única consumidora era esse arquivo)
     também foi removido.
   - `tests/test_azure.py` foi redesenhado: o teste de comparação com a carga por planilha (que não
     faz mais sentido existir sozinho) virou uma verificação direta da hierarquia esperada
     (`test_carga_do_azure_monta_hierarquia_correta`), com os mesmos pontos que o teste antigo
     comprovava (item Removido excluído, time DADOS ligado pelo Parent com fluxo real terminando em
     "Pronto", não "Fechado") — só que sem mais uma segunda carga por planilha para comparar contra.
     Ganhou também um teste dedicado ao diálogo de mapeamento de colunas renomeadas
     (`test_mapeamento_de_colunas_renomeadas`), que usa o fluxo de UI de verdade (clique em
     `#btnAz`/`#azGo`, espera por `#azMapOk`) já que `carregar()` não pode mais exercitar esse
     caminho.

5. **Remoção do código de planilha/CSV/demo/SheetJS**: apagados `src/js/03-leitura-planilha-csv.js`
   (parsing/reparo de CSV) e `src/js/18-dados-exemplo.js` (`demoTables()`); `newImport()` (única
   função reaproveitada pelo caminho do Azure) virou um objeto literal simples nos dois call sites
   que sobraram, já que sua única razão de existir (padronizar o formato `{csvSheets, fixed,
   dropped, replaced}`) desapareceu junto com o parsing de CSV. `scripts/build.mjs` e
   `package.json` pararam de embutir o SheetJS — o build caiu de 0,94 MB para 0,32 MB. Limpeza de
   código morto associado (`S.isDemo`, `cfgTeams(c, withDemo)`, `S.source`) nos arquivos que ainda
   citavam essas variáveis, e o painel de Higiene de dados perdeu o bloco de diagnóstico de
   importação por planilha (nunca mais teria conteúdo, já que a carga é sempre pelo Azure).
   `src/js/17-filtros-e-carga-planilha.js` foi renomeado para `src/js/17-filtros-e-carga.js`, já
   que não sobrou nada de "planilha" nele.

6. **Restrição de arquitetura revisada**: `docs/arquitetura.md` documentava como não-negociável
   "sem internet obrigatória (a biblioteca SheetJS vai embutida)". Essa garantia deixa de valer —
   o primeiro acesso e toda atualização de dados exigem internet e uma conexão com o Azure DevOps;
   só a navegação com dados já carregados/guardados no IndexedDB deste navegador continua
   funcionando offline. Documentado explicitamente na própria restrição, em vez de deixá-la
   silenciosamente incorreta.

7. **Decisão `0009` (times de exemplo fora da configuração) fica superada**: não existem mais dados
   de exemplo, então o cenário que aquela decisão resolvia não existe mais. Mantive o arquivo antigo
   sem editar (decisões são registro histórico, não documentação viva) e deixo essa nota aqui como
   ponteiro.

## Consequências

- App: `src/index.html`, `src/styles.css`, `src/js/17-filtros-e-carga.js` (renomeado),
  `src/js/19-tela-configuracoes.js`, `src/js/20-azure-conexoes-e-fontes.js`,
  `src/js/22-azure-janela-e-cache.js`, `src/js/01-configuracao-e-regras.js`,
  `src/js/11-filtros-e-diagnostico.js`, `src/js/12-investigacao.js`, `src/js/16-higiene.js`,
  `src/js/05-estado-e-calculos.js`, `src/js/06-renderizacao.js`; apagados
  `src/js/03-leitura-planilha-csv.js` e `src/js/18-dados-exemplo.js`; `scripts/build.mjs` e
  `package.json` sem a dependência do `xlsx`.
- Testes: `tests/conftest.py` (`carregar()` reescrita), `tests/azure_simulado.py` (generalizado),
  `tests/test_azure.py` (redesenhado), `tests/gerar_fixtures.py` (sem `csv_nas_abas`); apagado
  `tests/test_carga_planilha.py`. Suíte completa (150 testes) e `npm run build`/`npm run check`
  verdes.
- Documentação: `docs/arquitetura.md` (restrição 1, mapa de arquivos, diagrama de fluxo),
  `docs/configuracoes.md` (nova seção das 2 abas), `docs/telas.md` (nova seção "Primeiro acesso"),
  `docs/integracao-azure.md` (única fonte de dados), `docs/regras-de-negocio.md` §1.2,
  `CLAUDE.md`, `README.md`; apagado `docs/importacao-planilha.md`.
