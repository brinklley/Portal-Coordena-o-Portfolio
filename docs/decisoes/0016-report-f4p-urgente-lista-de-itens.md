# 0016 — Report F4P Urgente: lista de itens por trás do Realizado

## Contexto

Depois de corrigir o bug de contagem (decisão `0015`), o usuário pediu uma melhoria de transparência no mesmo PR: poder ver **quais** cards entraram no número do Realizado, não só o total — útil tanto para conferir a conta quanto para agir sobre os itens.

## Decisão

O número do Realizado do quadrante Urgente passa a ser um botão clicável. Ao clicar, abre um modal (reaproveitando o padrão visual `.modal-bg`/`.modal` já usado por Configurações e pela carga do Azure) com uma tabela dos itens exatos considerados pela mesma regra da decisão `0015` (abertos sempre; fechados dentro da janela do semestre): ID, Título e Situação (Aberto, ou Fechado + data). Clicar no ID de um item fecha o modal e o painel Report F4P e leva até o item no quadro (`gotoId`, mesmo mecanismo do campo "Ir para qualquer ID" e dos links da Visão analítica).

## Implementação

- `f4pUrgentRealizado` foi separado em duas funções: `f4pUrgentItems(team, st)` (retorna a lista de itens) e `f4pUrgentRealizado` (agora só `.length` dela) — para o modal e a contagem sempre usarem exatamente os mesmos itens, sem duplicar a regra de filtro.
- Novo modal `#f4pItemsBg` em `src/index.html`; lógica em `src/js/23-report-f4p.js` (`f4pItemsModal`, `closeF4PItems`).

## Consequências

- Fica fácil generalizar esse "ver os itens" para outros quadrantes calculados (CycleTime, Variabilidade) no futuro, reaproveitando `f4pItemsModal` — hoje só o Urgente tem o botão porque foi o que pediram.
- Teste em `tests/test_report_f4p.py` (`test_urgente_clique_no_numero_abre_lista_e_permite_navegar`): confere que o modal mostra o item certo e que clicar nele navega e fecha os dois painéis.
