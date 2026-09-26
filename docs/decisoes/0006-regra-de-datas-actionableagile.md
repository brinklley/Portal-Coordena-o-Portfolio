# 0006 · Regra das datas de coluna (compatível com a ActionableAgile)

**Contexto.** As datas de entrada em cada coluna precisam bater com a planilha exportada hoje.
**Decisão.** Colunas do quadro atual por ID; primeira coluna = data de criação; primeira entrada; colunas puladas herdam a próxima; volta apaga as colunas à frente; parte Done de coluna que deixou de ser dividida vai para a seguinte; colunas antigas ignoradas salvo mapeamento.
**Consequências.** 100% de igualdade nos itens que só avançaram; diferenças residuais em itens que saíram do quadro e voltaram.
