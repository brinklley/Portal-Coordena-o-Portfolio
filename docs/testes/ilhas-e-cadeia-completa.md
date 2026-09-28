# Testes: Ilhas soltas no whiteboard (cadeia completa)

Cobre `tests/test_ilhas_e_cadeia_completa.py` (3 testes). Trata do recurso de "soltar" ilhas
(`#fAnchor` desmarcado) e arrastá-las livremente pelo whiteboard, no modo "Abrir cadeia completa". Ver
`docs/telas.md` ("Ancorar/soltar ilhas"); decisão `0040`.

## Regra: uma posição arrastada é descartada quando o filtro muda o que aparece

**Garante que**: soltar uma ilha (`#fAnchor` desmarcado) e arrastá-la grava um deslocamento fixo em
pixels (`S.offsets[chave]`) a partir da posição que ela tinha no momento do arrasto. Como esse
deslocamento é relativo à posição natural daquele momento — não ao conteúdo em si — trocar um filtro
que muda a altura das seções acima da ilha (Time, busca "ID ou descrição", Roadmap executivo/interno,
Responsável) descarta o deslocamento: uma posição pensada para uma cadeia não necessariamente cabe
numa cadeia diferente.

- **Dado**: uma ilha de time solta manualmente (`S.offsets['isl:MOBILE'] = {x:0, y:-1300}`).
- **Quando**: troca o filtro de Time (`#fTeam`).
- **Então (sucesso)**: `S.offsets` fica vazio.
- **Cenário de falha coberto**: o board "Operacional dos times" aparecia visualmente por cima dos
  boards de Iniciativa/Release/Épico — a posição arrastada enquanto o usuário via uma cadeia grande
  ficava fixa em pixels mesmo depois de um filtro reduzir bastante o que aparece acima dela.
- **Teste**: `test_offset_de_ilha_solta_e_descartado_quando_o_filtro_muda`
- **Relacionado**: decisão `0040-offsets-de-ilhas-descartados-por-contexto.md`.

## Regra: uma posição arrastada também é descartada ao trocar de iniciativa

**Garante que**: a mesma invalidação vale para navegar para outra iniciativa (voltar à raiz e
selecionar outra) — a posição só faz sentido para a cadeia que estava sendo vista quando a ilha foi
arrastada, nunca para uma iniciativa diferente.

- **Dado**: mesmo tipo de deslocamento manual, numa iniciativa A.
- **Quando**: volta à raiz e seleciona uma iniciativa B diferente.
- **Então (sucesso)**: `S.offsets` fica vazio.
- **Teste**: `test_offset_de_ilha_solta_e_descartado_ao_trocar_de_iniciativa`
- **Relacionado**: decisão `0040`.

## Regra: uma posição arrastada sobrevive a um re-render sem mudança de contexto

**Garante que**: a invalidação é específica de mudanças que afetam o que aparece (filtro, busca,
iniciativa) — um re-render disparado por algo que não muda o conteúdo (ex.: alternar "Mostrar etapas
vazias") não apaga o trabalho manual do usuário.

- **Dado**: mesmo tipo de deslocamento manual.
- **Quando**: desmarca "Mostrar etapas vazias" (`#fEmpty`), sem mexer em filtro, busca ou iniciativa.
- **Então (sucesso)**: `S.offsets` continua com o mesmo valor de antes.
- **Cenário de falha coberto**: uma correção "ingênua" que limpasse `S.offsets` em todo `render()`
  apagaria qualquer arranjo manual a cada interação, mesmo sem nenhuma mudança de conteúdo — a
  correção real depende de comparar uma assinatura do que molda o quadro, não de zerar sempre.
- **Teste**: `test_offset_de_ilha_solta_persiste_entre_renders_sem_mudanca_de_contexto`
- **Relacionado**: decisão `0040`.
