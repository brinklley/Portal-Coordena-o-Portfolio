# Filtros e busca — guia do usuário

## O que é

A barra de filtros, no topo do quadro, controla o que aparece nas quatro faixas (Iniciativas,
Releases, Épicos, Operacional dos times) e também habilita os painéis laterais (Visão Analítica,
Report F4P, Actionable). Além dos filtros, um mecanismo de diagnóstico ajuda a responder "por que esse
item não está aparecendo?" sem precisar testar filtro por filtro manualmente.

## Como funciona

### Os filtros (somam-se — E lógico)

| Filtro | O que faz |
|---|---|
| **Roadmap executivo** | Mostra só iniciativas daquele semestre (`AnoSemestreRoadmap`). |
| **Responsável da iniciativa** | Múltipla escolha, busca por qualquer parte do nome, sem acento (ex.: "conceicao" encontra "Conceição"). Filtra só pela iniciativa — não restringe releases, épicos nem itens além do que a cadeia da iniciativa já implica. |
| **Roadmap interno** | Mostra só épicos cujo Target Date cai naquele semestre. |
| **Time** | Dinâmico — lista times cadastrados mesmo sem carga ainda. Restringe a cadeia a épicos com pelo menos um item daquele time, e os itens mostrados àquele time. |
| **ID ou descrição** (campo único) | Ver abaixo. |

Todos os filtros se somam: um item só aparece se passar em **todos** os filtros ativos ao mesmo tempo.
Os filtros ativos ficam destacados na barra; "Limpar filtros (N)" remove todos de uma vez.

### Campo único "ID ou descrição"

Um único campo substitui o que antes eram dois campos separados (um para "Iniciativa" e outro para "Ir
para qualquer ID"). Ele funciona de duas formas:

- **Por ID exato**: digite o ID de qualquer nível (iniciativa, release, épico ou item de time) — o
  campo revela a cadeia inteira até a iniciativa daquele ID.
- **Por texto**: digite parte do título — casa com o título em **qualquer nível** da hierarquia, não
  só em nomes de iniciativa. Se o texto só bate com o título de um item de time (não com a iniciativa
  nem com níveis acima), a cadeia dele até a iniciativa ainda é revelada, mas só aquele item específico
  fica em destaque dentro do épico.

Ao digitar, o filtro já se aplica ao vivo. Apertar **Enter** também tenta navegar (abrir/rolar) até o
item, quando a busca é um ID. O campo fica salvo como filtro ativo, igual aos demais, até ser limpo —
inclusive pelo "×" nativo do próprio input.

### Diagnóstico de quadro vazio

Quando os filtros ativos não deixam nenhum resultado, o quadro mostra um diagnóstico — não só uma tela
em branco. Ele explica qual filtro zerou o resultado e quantas iniciativas apareceriam sem cada um.
Para um ID que existe mas não aparece na busca, o diagnóstico percorre as mesmas etapas da
"Investigação por ID" (abaixo) e diz exatamente qual delas falhou, com um botão para remover o filtro
culpado e ir direto até o item.

### "+N ocultos": revelar irmãos escondidos pelo filtro

Com pelo menos um filtro ativo, um card visível pode ter irmãos (mesmo nível, mesmo pai) que o filtro
esconde sem deixar rastro nenhum. Um botão pequeno `+N ocultos` aparece no cabeçalho da faixa de
Iniciativas, Releases ou Épicos **só quando há de fato algo oculto** naquela faixa — nunca "por via das
dúvidas". Clicar:

- Revela os irmãos ocultos, esmaecidos (mesmo estilo visual das iniciativas fora de foco), na coluna do
  fluxo que teriam normalmente, com a linha de conexão até o pai.
- Vira `−N ocultos`; clicar de novo esconde.
- A contagem no cabeçalho da faixa (o número ao lado de "Épicos", por exemplo) e as estatísticas
  **não** incluem os revelados — só a lista visual ganha mais cards.

Um card revelado é clicável, mas abre o painel de detalhes em vez de navegar até ele — como ele
continua fora do filtro ativo, "entrar" nele seria desfeito de novo pela mesma regra que o esconde.
Fica ligado entre navegações, como preferência, até você mesmo desligar ou até o novo recorte não ter
mais nada oculto para mostrar.

### Investigação por ID

Quando um ID digitado não aparece, a investigação percorre as etapas abaixo, nesta ordem, e para na
**primeira** que falhar — o motivo mostrado é sempre o real, não um motivo genérico:

1. **Retornou nos dados?** Se não: ou o ID nunca veio de nenhuma fonte carregada, ou foi excluído como
   "Removed" na carga do Azure DevOps.
2. **Foi reconhecido?** (tem título, vínculo mínimo esperado para o nível).
3. **Tem cadeia válida / passa na regra de exibição?** (ex.: iniciativa concluída sem nenhuma release
   nunca aparece, mesmo com "Mostrar itens sem desdobramento" ligado).
4. **Passa nos filtros ativos?** (Roadmap, Responsável, Time, ID/descrição de outro campo).
5. **Está recolhido na lista?** (iniciativa escondida porque outra está selecionada e "Manter todas as
   iniciativas visíveis" está desligado — ver `docs/guia-usuario/quadro.md`).

Cada etapa citada no diagnóstico já aponta a correção certa (ex.: "ligue Manter todas as iniciativas
visíveis", em vez de só "item não visível").

## Perguntas frequentes ("não está batendo com o que eu esperava")

### "Digitei o título de um item do time no campo de busca e nada apareceu"

Confira se o texto bate exatamente com parte do **título** do item (não com o ID, não com outros
campos). O campo busca em qualquer nível, mas só pelo título/ID — não por responsável, tag ou outro
atributo (esses têm filtro próprio).

### "O quadro ficou vazio depois que digitei um ID, mas eu sei que ele existe"

O diagnóstico de quadro vazio explica a causa exata: se for outro filtro (ex.: Responsável) que exclui
o dono daquele ID, a mensagem cita qual filtro é e oferece um link para remover o bloqueio e ir até o
item mesmo assim. Veja "Investigação por ID" acima para as cinco causas possíveis, na ordem em que são
checadas.

### "Limpei a busca, mas o quadro ficou preso mostrando só um pedaço — não voltou ao normal"

Isso seria um bug, não o comportamento esperado: limpar o campo (inclusive pelo "×" nativo) também
desfaz a navegação que o Enter da busca tinha aberto — o quadro deveria voltar ao estado neutro por
completo, não ficar "vazio pela metade" mostrando só o que a busca havia selecionado. Da mesma forma,
digitar um **novo** ID por cima de uma busca anterior (mesmo sem apertar Enter) já desfaz a navegação
antiga. Se isso não acontecer, é uma regressão a reportar.

### "Depois de atualizar os dados do Azure DevOps, o filtro de Time que eu tinha selecionado desapareceu"

Uma recarga (nova importação, ou "atualizar os dados" do Azure DevOps) preserva o filtro de **Time**
se aquele time ainda existir nos dados recarregados — os demais filtros (Roadmap, Responsável, ID ou
descrição) são sempre limpos numa recarga, de propósito, porque podem não fazer mais sentido com dados
novos. Se o time que você tinha selecionado não existe mais na nova carga, o filtro volta para "Todos
os times".

### "Vejo um botão '+N ocultos' mas não sei o que ele faz"

Avisa que existem irmãos daquele card (mesmo nível, mesmo pai) escondidos pelo filtro ativo no momento
— sem ele, você não teria como saber que existe mais coisa ali além do que está na tela. Clicar revela
os irmãos ocultos esmaecidos; clicar de novo esconde outra vez. Ver "+N ocultos" acima.

## Cenários

### Campo único busca por ID em qualquer nível

**Cenário de sucesso: ID de épico revela a cadeia inteira**
- Dado um ID de épico válido, vinculado a uma release e iniciativa
- Quando o usuário digita esse ID no campo "ID ou descrição"
- Então só a iniciativa dona daquele épico fica visível no quadro, com a cadeia completa até ele

**Cenário de comportamento inesperado: texto que só bate com item de time, não com iniciativa**
- Dado um título que existe só num item de time, vinculado a um épico válido
- Quando o usuário digita esse título no campo
- Então a cadeia até a iniciativa daquele épico é revelada mesmo assim — o campo busca em qualquer
  nível, não só em nomes de iniciativa (diferente do campo antigo que esta busca única substituiu)

### Diagnóstico aponta o filtro que esconde um ID buscado

**Cenário de sucesso: nenhum outro filtro bloqueia**
- Dado nenhum filtro de Responsável/Time/Roadmap ativo
- Quando o usuário busca um ID válido
- Então o item aparece normalmente, sem nenhum diagnóstico de bloqueio

**Cenário de comportamento inesperado: filtro de Responsável esconde o dono do ID buscado**
- Dado um filtro de Responsável já ativo, que exclui o responsável da iniciativa buscada
- Quando o usuário digita o ID dessa iniciativa e aperta Enter
- Então o quadro mostra o diagnóstico citando "Responsável da iniciativa" como o filtro bloqueando, com
  um link que navega até o item mesmo assim

### Limpar a busca desfaz a navegação que ela havia criado

**Cenário de sucesso: campo vazio volta o quadro ao estado neutro**
- Dado uma busca por ID com Enter (que abriu a cadeia daquele item)
- Quando o usuário limpa o campo (digitando ou pelo "×")
- Então nenhum filtro continua ativo e a navegação criada pela busca é desfeita por completo

**Cenário de comportamento inesperado (bug corrigido): quadro ficava preso na seleção antiga**
- Dado a mesma busca por ID com Enter
- Quando o campo é limpo
- Então, sem a correção, o quadro continuaria mostrando só a iniciativa que a busca tinha selecionado
  — um "quadro vazio pela metade" sem explicação visível

## Regras de negócio relacionadas

- `docs/regras-de-negocio.md` §3.1 (Filtros), §3.2 ("+N ocultos"), §2 e §3 (Validade e Visibilidade —
  base da Investigação por ID).
- Decisões: [`0034`](../decisoes/0034-filtro-unico-id-ou-descricao.md) (campo único),
  [`0035`](../decisoes/0035-limpar-busca-desfaz-selecao-que-ela-criou.md) (limpar busca desfaz
  seleção), [`0050`](../decisoes/0050-itens-ocultos-pelo-filtro.md) ("+N ocultos"),
  [`0057`](../decisoes/0057-filtro-de-time-sincroniza-apos-recarga.md) (filtro de Time sobrevive a
  recarga).
- Detalhe exaustivo de cobertura de teste:
  [`docs/testes/filtros-e-busca.md`](../testes/filtros-e-busca.md),
  [`docs/testes/itens-ocultos-pelo-filtro.md`](../testes/itens-ocultos-pelo-filtro.md),
  [`docs/testes/hierarquia-e-modelo.md`](../testes/hierarquia-e-modelo.md) (mecanismo de investigação).
