# Relatório diário — guia do usuário

## O que é

Um **arquivo HTML único, offline**, gerado automaticamente todo dia útil de manhã, com uma cópia da
Visão Analítica e do Actionable de cada time comprometido no roadmap vigente, mais o Report F4P
(sempre os 4 times). Pensado para ser anexado a um e-mail e aberto sem precisar do Portal nem de
internet. Os números são calculados pelas **mesmas funções do Portal** (uma captura de tela "ao vivo"
num navegador sem interface, não um cálculo escrito de novo) — se bate na tela do Portal, bate no
relatório, sempre.

Diferente das outras telas deste guia, o relatório não é algo que você abre e navega: ele é entregue
pronto, uma vez por dia, como um arquivo.

## Como é gerado

Uma rotina agendada roda o gerador (`scripts/relatorio/gerar_relatorio.py`) nos dias úteis, de manhã.
Ela:

1. Abre o `dist/mapa_portfolio.html` (o mesmo arquivo que qualquer pessoa usaria) num navegador sem
   interface.
2. Carrega os dados do Azure DevOps pelo mesmo caminho da tela — uma credencial por organização, sem
   token chegando ao navegador (decisão `0063`).
3. Para o roadmap vigente (interno, por padrão), identifica os **times comprometidos** — times que têm
   pelo menos um item com Capacidade reservada (a tag `CFG.anTag`, a mesma da Visão Analítica, §10)
   nesse roadmap.
4. Para cada time comprometido: captura a Visão Analítica e o Actionable daquele time. Captura também
   o Report F4P uma única vez (ele já mostra os 4 times).
5. Monta tudo num único HTML com menu lateral — **Visão Analítica** (um item por time), **Actionable**
   (idem), **Report F4P** (fixo) — e entrega o arquivo.

Se **qualquer** fonte do Azure DevOps não carregar, a geração inteira é **abortada**, sem gerar arquivo
parcial — um relatório com um time faltando, sem aviso nenhum, seria pior que nenhum relatório.

## Perguntas frequentes ("não está batendo com o que eu esperava")

### "Um time que eu esperava ver não aparece no relatório"

O relatório só traz **times comprometidos** com o roadmap vigente — um time só entra se tiver pelo
menos um item com a tag de capacidade (`ROADMAP`, por padrão) reservado nesse semestre. Um time sem
nenhum item reservado (mesmo ativo no fluxo) não aparece na Visão Analítica nem no Actionable do
relatório — a mesma régua de "Reserva" da Visão Analítica (`docs/guia-usuario/visao-analitica.md`).
Ele continua aparecendo no Report F4P, que sempre mostra os 4 times.

### "Pedi a geração para um time específico e deu erro 'não está comprometido no roadmap'"

Mesma régua acima: mesmo pedindo um time explicitamente, ele só entra na Visão Analítica/Actionable do
relatório se tiver Capacidade reservada naquele roadmap. A mensagem de erro lista exatamente quais
times estão comprometidos no momento, para conferir.

### "O relatório não foi gerado hoje"

A geração **aborta por inteiro** se alguma fonte do Azure DevOps não carregar (erro de acesso,
indisponibilidade, etc.) — por desenho, nunca sai um relatório com um time faltando sem aviso. Se isso
acontecer, quem recebe a notificação da rotina vê a mensagem de erro exata (qual fonte falhou).

### "Clico num número do relatório e nada acontece"

É esperado: diferente do Portal (onde os números são clicáveis e abrem a lista de itens), o relatório é
um **arquivo estático** — botões viram texto, nada abre modal nem navega. Para investigar um item
específico, use o Portal diretamente.

### "Os números do relatório não batem com o que vejo no Portal agora"

O relatório é um retrato do momento em que foi gerado (de manhã, uma vez por dia) — se algo mudou no
Azure DevOps depois disso (um item entregue, uma tag adicionada), o Portal ao vivo já reflete essa
mudança, mas o relatório daquele dia, não. Para o dado mais atual, abra o Portal e atualize os dados do
Azure DevOps.

## Cenários

### Time comprometido entra no relatório; time sem reserva não entra

**Cenário de sucesso: time com item reservado aparece**
- Dado um time com pelo menos um item marcado com a tag de capacidade (`ROADMAP`) no roadmap vigente
- Quando o relatório é gerado
- Então a Visão Analítica e o Actionable desse time aparecem no menu do relatório

**Cenário de comportamento inesperado: time sem nenhuma reserva não aparece**
- Dado um time sem nenhum item marcado com a tag de capacidade no roadmap vigente (mesmo com itens
  ativos no fluxo)
- Quando o relatório é gerado
- Então a Visão Analítica e o Actionable desse time **não** aparecem no menu — só o Report F4P continua
  trazendo esse time, já que ele sempre mostra os 4

### Falha numa fonte do Azure aborta tudo, sem arquivo parcial

**Cenário de comportamento inesperado: uma fonte do Azure falha**
- Dado que uma das fontes configuradas no Azure DevOps não carrega (erro de acesso ou indisponibilidade)
- Quando o gerador tenta montar o relatório
- Então nenhum arquivo é gerado, e o erro mostra exatamente qual fonte falhou — não existe relatório
  "quase completo"

## Regras de negócio relacionadas

- Decisão [`0063`](../decisoes/0063-relatorio-diario-por-e-mail-pipeline-headless.md) — arquitetura
  completa do gerador, autenticação por ponte (PAT nunca chega ao navegador, decisão
  [`0007`](../decisoes/0007-token-nunca-salvo.md)), e o histórico de ajustes feitos depois do primeiro
  teste em produção.
- `docs/regras-de-negocio.md` §10 (Visão analítica — a mesma régua de "Reserva"/"Capacidade" decide
  quem é "time comprometido" aqui).
- Detalhe exaustivo de cobertura de teste: [`docs/testes/relatorio.md`](../testes/relatorio.md).
- Comando para gerar manualmente (ex.: para testar): ver seção "Comandos" do `CLAUDE.md` na raiz do
  repositório.
