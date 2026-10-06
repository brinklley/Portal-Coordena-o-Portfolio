# Testes: Relatório diário (gerador offline)

Cobre `tests/test_relatorio.py` (11 testes). Decisão `0063`; código em `scripts/relatorio/`. O gerador roda como subprocesso (como a rotina agendada), contra o Azure simulado e a fixture fictícia `relatorio.xlsx`.

## Regra: o relatório é idêntico ao que o portal mostra

**Garante que**: o relatório nunca diverge da tela porque a regra não é reimplementada — o HTML gerado traz a mesma Capacidade/Projetada, os mesmos épicos na mesma ordem e o mesmo CycleTime que `anData()`/`anSorted()` no portal.

- **Dado**: fixture `relatorio.xlsx`, time MOBILE, roadmap interno vigente, mesmo fuso (Brasília).
- **Então (sucesso)**: o título "Entregas previstas: Capacidade X US / Projetada Y US", a lista de IDs de épico e os CycleTimes do arquivo gerado são iguais aos calculados no portal.
- **Cenário de falha coberto**: alguém reimplementar uma regra no gerador (ou filtrar diferente) e o e-mail mostrar números que não batem com a tela.
- **Teste**: `test_relatorio_reproduz_exatamente_a_visao_analitica_do_portal`

## Regra: Actionable e Report F4P também são idênticos ao portal

**Garante que**: os rótulos dos gráficos SVG, o resumo do Burnup e as células/colunas do Report F4P do arquivo gerado são os mesmos que o portal mostra para o mesmo time e roadmap; o Actionable traz os 3 gráficos em SVG e o F4P mostra os 4 times.

- **Cenário de falha coberto**: a captura perder ou alterar um quadrante; o F4P deixar de mostrar todos os times.
- **Teste**: `test_actionable_e_report_f4p_reproduzem_exatamente_o_portal`

## Regra: arquivo único, offline e sem interação enganosa

**Garante que**: o HTML não referencia nenhum recurso externo, tem os 3 grupos de menu, não tem botões/ordenação (nada clicável) e nenhuma frase manda clicar (Visão Analítica, Actionable e F4P) e existem as 3 seções.

- **Cenário de falha coberto**: anexo que abre em branco sem internet; números com cara de link que não fazem nada.
- **Teste**: `test_relatorio_e_um_arquivo_unico_offline_e_sem_interacao_enganosa`

## Regra: entradas inválidas abortam sem gerar arquivo parcial

**Garante que**: time sem Capacidade no roadmap, ou roadmap inexistente nos dados, encerram com erro claro e sem arquivo na saída.

- **Testes**: `test_time_sem_capacidade_no_roadmap_aborta_com_mensagem_clara`, `test_roadmap_inexistente_nos_dados_aborta`

## Regra: o PAT fica só na ponte

**Garante que**: a ponte troca o valor de enchimento pelo PAT real, responde o preflight CORS, converte o redirecionamento de login do Azure em 401, recusa organização sem PAT, e a ausência de variável de ambiente é reportada pelo **nome** da variável, nunca pelo valor de outra.

- **Cenário de falha coberto**: token vazando em log/mensagem ou entrando na página (decisão `0007`); PAT inválido virando "HTML de login" interpretado como dado.
- **Testes**: `test_ponte_troca_o_token_de_enchimento_pelo_pat_real_e_responde_cors`, `test_ponte_converte_redirecionamento_de_login_em_401_e_barra_org_sem_pat`, `test_pats_do_ambiente_exige_todas_as_orgs_e_nunca_mostra_valores`

## Regra: erro passageiro do Azure é repetido só na chamada que falhou

**Garante que**: 502/503/504 (ou falha de rede) são repetidos dentro da ponte e o portal nunca os vê; 401/403/404 passam direto e na hora; ao esgotar as tentativas, o erro é devolvido (a nova tentativa por fonte do portal continua como rede de segurança).

- **Cenário de falha coberto**: um único lote do histórico com 502 fazendo o portal refazer a fonte inteira (minutos), estourando o tempo da rotina; ou repetir indefinidamente um erro de acesso.
- **Teste**: `test_ponte_repete_so_a_chamada_com_erro_passageiro_e_nao_repete_erro_de_acesso`
