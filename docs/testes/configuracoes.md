# Testes: Tela de Configurações

Cobre `tests/test_configuracoes.py` (6 testes). Trata de validações de formulário, exportação de
configuração sem vazar credenciais, e o botão de limpar tudo. Ver `docs/configuracoes.md`.

## Regra: limites de alerta precisam ser crescentes (warn < max)

**Garante que**: o formulário de configuração por time não aceita salvar se o limite de "atenção"
(warn) for maior ou igual ao "máximo" (max) — a validação bloqueia o salvamento e explica o motivo.

- **Dado**: `times.xlsx`, abre Configurações, define `max=10` e `warn=12` para o CORE.
- **Quando**: clica em `#cfgSave`.
- **Então (sucesso)**: a mensagem de erro (`.cfg-err`) contém "atenção precisa ser menor"; a tela de
  Configurações continua aberta (`#cfgBg` visível) — nada foi salvo.
- **Cenário de falha coberto**: uma configuração inconsistente (limite de atenção maior que o
  máximo) seria salva e produziria alertas que nunca disparam na ordem esperada.
- **Teste**: `test_valida_limites_crescentes`
- **Relacionado**: regras-de-negocio.md §8.1.

## Regra: CT do time precisa de ao menos duas colunas marcadas

**Garante que**: um time precisa ter pelo menos duas colunas do fluxo marcadas para entrar no
cálculo de CT (início e fim) — desmarcar todas bloqueia o salvamento com erro nomeando o time.

- **Dado**: `times.xlsx`, aba do time IB, desmarca todos os checkboxes `[data-ctcol]`.
- **Quando**: `#cfgSave`.
- **Então (sucesso)**: `.cfg-err` contém "IB".
- **Cenário de falha coberto**: um time sem nenhuma coluna de CT marcada ficaria com CT
  indefinido/quebrado silenciosamente em vez de a UI pedir a correção no momento do salvamento.
- **Teste**: `test_ct_precisa_de_duas_colunas`

## Regra: a exportação de configuração nunca leva o token do Azure

**Garante que**: o arquivo de configuração exportado (JSON, para backup/compartilhamento) inclui os
dados de organizações e fontes, mas nunca o valor do token de acesso, mesmo que ele exista em
memória no momento da exportação.

- **Dado**: uma organização com token em `AZ.tokens`.
- **Quando**: clica em `#cfgExport`.
- **Então (sucesso)**: o arquivo baixado contém o nome da organização (`"minha-org"`), mas não
  contém o valor do token (`"SEGREDO-123"`).
- **Cenário de falha coberto**: exportar a configuração vazaria a credencial de acesso ao Azure
  DevOps para qualquer lugar que receba o arquivo — email, chat, repositório.
- **Teste**: `test_exportacao_nunca_leva_token`
- **Relacionado**: decisão `0007-token-nunca-salvo.md` — regra não-negociável do projeto.

## Regra: "Dias antes do fim do semestre" tem padrão 10 e ajuda explica o cálculo do dead line

**Garante que**: o campo `CFG.anFreeze` (usado no cálculo do dead line da Visão analítica) vem com
padrão 10 (não mais 0), e o texto de ajuda da aba Geral explica a fórmula completa (incluindo o CT
máximo do time), com exemplo numérico — não só descreve a data de congelamento sem o impacto.

- **Dado**: uma carga nova, sem configuração prévia de `anFreeze`.
- **Então (sucesso)**: `CFG.anFreeze === 10`; o campo `#cfgAnFreeze` mostra `"10"`; o texto de
  `#cfgTabGeral` cita "CT máximo do time" e a palavra "dead line" (case-insensitive).
- **Cenário de falha coberto**: o padrão zero deixaria nenhuma folga no cálculo do dead line por
  omissão; sem a explicação da fórmula, o usuário mudaria o valor sem entender o efeito real no
  cálculo.
- **Testes**: `test_dias_antes_do_semestre_padrao_e_10`,
  `test_ajuda_do_dias_antes_do_semestre_explica_o_calculo_do_deadline`
- **Relacionado**: decisão `0037-dias-antes-do-semestre-ajuda-e-padrao-10.md`.

## Regra: "Limpar tudo" apaga a configuração e volta ao estado de 1º acesso

**Garante que**: o botão de limpeza total (`#cfgWipe` → `#wipeGo`) remove a configuração do
`localStorage` e devolve o portal exatamente ao estado de primeiro acesso — gate ativo, tela de
conexão forçada — não a uma tela intermediária.

- **Dado**: `CFG.teams` populado e salvo.
- **Quando**: `#cfgWipe` → `#wipeGo`, aguarda navegação.
- **Então (sucesso)**: `localStorage.getItem(CFG_KEY)` é `null`; `CFG.teams` volta a `{}`;
  `document.body` tem a classe `gate-active`; `#cfgBg` não está mais escondido (conexão forçada de
  novo).
- **Cenário de falha coberto**: "limpar tudo" removeria os dados mas deixaria o portal num estado
  inconsistente (nem o quadro antigo, nem a tela de 1º acesso), exigindo recarregar manualmente.
- **Teste**: `test_limpar_tudo_volta_ao_primeiro_acesso`
- **Relacionado**: decisão `0032` (mecanismo de gate/1º acesso).
