# 0038 — Report F4P: min/max da Eficiência de fluxo numa linha própria

## Contexto

O usuário reportou, com print, que o quadrante "Eficiência de fluxo (min vs atual vs max)" do
Report F4P quebrava o layout com vários times: a célula "min% | atual% seta | max%" não cabia na
largura da coluna e o "% | max%" final quebrava para uma segunda linha, desalinhado com o resto da
tabela. Sugeriu ajustar o espaçamento ou, como alternativa, diminuir a fonte de min/max.

## Diagnóstico

`f4pEffCell()` reaproveitava o mesmo padrão de `f4pVarCell()` (Variabilidade, o outro quadrante com
min/max): três partes lado a lado na mesma linha (`min|atual|max`). Mas os valores de Eficiência de
fluxo são porcentagens de duas ou três casas mais o símbolo `%` (ex. "100%"), bem mais largos que os
decimais de uma casa da Variabilidade (ex. "3,5") — com `table-layout:fixed` dividindo a largura
igualmente entre as colunas de time, a célula ficava larga demais para caber numa linha só assim que
havia mais de 4-5 times.

Testei primeiro só encolher a fonte de min/max e travar a quebra de linha (`white-space:nowrap`) —
funcionava com poucos times, mas com 7 (o caso real do maior conjunto de times já usado nos testes:
CORE, IB, BO, MOBILE, PAGAMENTOS, DADOS, CANAIS) o conteúdo simplesmente **transbordava por cima da
coluna vizinha**, pior que a quebra original.

## Correção

Em vez de forçar tudo numa linha só, `min|max` passa a ficar numa **linha própria**, abaixo do valor
principal: `<span class="f4p-eff-mm">min%|max%</span>`, com fonte menor (`10.5px`) e `display:block`.
O valor principal continua do mesmo tamanho de sempre — o que, como o próprio usuário notou, ajuda a
destacar ele. Como essa segunda linha não depende mais de caber ao lado do valor principal, o layout
não quebra com nenhuma quantidade razoável de times. `f4pVarCell()` (Variabilidade) não foi alterado:
os decimais dela já cabem numa linha só sem problema, e mudar sem necessidade só criaria uma
inconsistência visual entre os dois quadrantes.

## Testes

`tests/test_report_f4p.py::test_eff_min_max_ficam_em_linha_propria`: confirma que `f4pEffCell()`
devolve `<span class="f4p-eff-mm">` com o valor principal antes dela e min/max dentro dela — a
estrutura por trás do novo layout. Validação visual feita à parte (screenshot com 7 times, sem
sobreposição nem quebra).
