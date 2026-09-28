# 0037 — "Dias antes do fim do semestre": ajuda mais clara e padrão 10 dias

## Contexto

O usuário reportou um caso onde o dead line da Visão analítica ("07/SET") parecia errado com
"Dias antes do fim do semestre" configurado em 55. Investigação (ver conversa) confirmou que o
cálculo estava **correto**: `dead line = fim do semestre − "Dias antes do fim do semestre" − CT
máximo do time` (já documentado em `docs/regras-de-negocio.md` §10 e no próprio texto de ajuda da
tela) — o usuário só não tinha em mente que o CT máximo do time também entra na conta, não só o
valor configurado nesse campo. Não era um bug, então não abri PR de correção; perguntei o que fazer
e o usuário pediu, em vez de mudar a regra: uma explicação mais completa junto do campo (com a
fórmula e um exemplo) e trocar o padrão do campo de 0 para 10 dias.

## Decisões

1. **Padrão de `CFG.anFreeze` passa de 0 para 10 dias** (`cfgDefaults()`,
   `src/js/01-configuracao-e-regras.js`) — só afeta instalações novas ou importação de configurações
   antigas que não tragam o campo; quem já tem um valor salvo (mesmo 0) não é alterado.
2. **Texto de ajuda expandido** (`src/js/19-tela-configuracoes.js`, seção "Visão analítica"): antes
   a fórmula do dead line vinha resumida numa frase dentro do parágrafo geral da seção; agora tem um
   parágrafo próprio, logo abaixo do campo, com a fórmula completa, quando usar o campo (semestre
   operacional terminando antes do fim do calendário), o efeito de configurar um valor alto ou baixo
   demais, e um exemplo numérico com os mesmos valores do caso reportado (31/12, 55 dias, CT máximo
   60 → dead line 07/09) para o usuário conseguir validar o próprio cálculo. O `title` do campo
   também foi trocado de uma frase só sobre congelamento de fim de ano para apontar direto pra essa
   explicação.

## Testes

`tests/test_configuracoes.py`: `test_dias_antes_do_semestre_padrao_e_10` (config nova tem
`anFreeze === 10`, campo mostra "10") e `test_ajuda_do_dias_antes_do_semestre_explica_o_calculo_do_deadline`
(o texto da aba Configurações gerais menciona "CT máximo do time" e "dead line").
