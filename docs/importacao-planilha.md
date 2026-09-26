# Importação por planilha

Código: `src/js/03-leitura-planilha-csv.js`, `src/js/04-modelo.js`, `src/js/17-filtros-e-carga-planilha.js`.
Testes: `tests/test_carga_planilha.py`.

## Entradas aceitas

- Uma planilha `.xlsx/.xlsm/.xls` com as abas em **formato tabela** ou com **CSV dentro das células** (cada linha do CSV numa célula da coluna A) — detectado **aba por aba**, automaticamente.
- Um ou mais arquivos `.csv` (cada arquivo vira uma aba com o nome do arquivo). Planilhas e CSVs podem ser selecionados juntos; se o mesmo nome de aba aparecer duas vezes, vale o último (registrado na Higiene).

## Abas e colunas

| Aba | Nome reconhecido | Colunas usadas |
|---|---|---|
| Iniciativa | começa com "iniciativa" | ID, Title, AnoSemestreRoadmap, Assigned To, Link, colunas do fluxo, demais (campos adicionais) |
| Release | começa com "release" | ID, Title, Parent, Assigned To, Link, fluxo |
| Épico | começa com "epico" (sem acento) | ID, Title, Parent, Target Date, Link, fluxo |
| Times | `TIME X` ou qualquer aba com `ID_EPICO_UNICRED` | ID, ID_EPICO_UNICRED, Title, Work Item Type, Tags, Blocked, Blocked Days, Target Date, Link, fluxo |

Nomes de abas e colunas são comparados sem acento e sem maiúsculas. Coluna `Work Item Type` em qualquer aba alimenta a cor da faixa por tipo.

## Detecção e leitura de CSV nas abas

- Uma aba é CSV se o cabeçalho está numa única célula, com separador e coluna `ID`, e ≥ 90% das linhas usam uma célula.
- Separador detectado entre vírgula, ponto e vírgula e tabulação.
- Codificação: arquivos `.csv` são lidos como UTF-8; se inválido, como Windows-1252. Textos com acentos quebrados ("PrÃ³ximos") são corrigidos (`fixEnc`).
- **Reconstrução de registros**: um novo registro começa numa linha iniciada por um ID numérico; linhas que não começam assim são continuação (quebra de linha dentro de aspas). Isso recupera registros que um leitor CSV comum perde quando a conversão do Excel quebra as aspas.
- **Reparo de aspas perdidas** (`repairRecord`): se o registro não tem o número de colunas do cabeçalho, tenta fechar uma aspa antes de um separador ou abrir uma aspa depois de um separador até acertar. Reparados vão para a Higiene.
- **Descartados**: registros truncados ou irreparáveis, listados na Higiene com o motivo.

## Datas

Aceitas: data do Excel, número serial do Excel, `dd/mm/aaaa`, `aaaa-mm-dd`. Valores não reconhecidos contam como vazios (e são contados na Higiene quando é o Target Date).

## Dados reais

Planilhas e exportações reais contêm dados da empresa e **não entram no Git** (`.gitignore`). Os testes usam `fixtures/`, gerado por `tests/gerar_fixtures.py`.
