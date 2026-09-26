# 0012 — Report F4P: ilustrações reais fornecidas pelo usuário

## Contexto

A decisão `0011` optou por ícones SVG inline originais em vez de reproduzir o slide de referência, por não termos os arquivos de imagem e por cautela com direitos de imagem. O usuário depois enviou as próprias imagens do slide (recortadas: "Healthy Range", "Fitness Criteria · KPIs", "have a target & are temporary", "Vanity Metrics" e o logo "F4P") e pediu para usá-las no relatório.

## Decisão

- As 4 imagens de selo passam a aparecer **uma vez por grupo de quadrantes** (como no slide original), acima dos cards — não mais como ícone pequeno dentro de cada card:
  - "Healthy Range" → Variabilidade + Eficiência de fluxo.
  - "have a target & are temporary" → Roadmap–Épicos + Vazão.
  - "Fitness Criteria · KPIs" → CycleTime.
  - "Vanity Metrics" → Urgente + Technical Story + User Story.
- O logo "F4P" aparece ao lado do título do painel (`#f4pTitle`).
- Os 4 ícones SVG inline da decisão `0011` foram removidos do código.

## Implementação

O portal continua sendo **um único arquivo HTML sem dependências externas em tempo de execução** (regra do `CLAUDE.md`), então as imagens não podem ser carregadas de URL: elas são **arquivos PNG versionados** em `src/assets/f4p/*.png` (reduzidos e recomprimidos a partir do que o usuário enviou: redimensionados para a largura de exibição e quantizados para poucas cores, já que são ilustrações de poucas cores sólidas — de ~108 KB para ~13,5 KB somando as 5 imagens) e o **build** (`scripts/build.mjs`) as lê, converte para base64 e gera `const F4P_ASSETS = {...}` no topo do JavaScript final, com uma chave por arquivo (`healthy-range.png` → `F4P_ASSETS.healthyRange` etc.). `src/js/23-report-f4p.js` referencia `F4P_ASSETS.<chave>` em tags `<img>`.

## Consequências

- `dist/mapa_portfolio.html` cresce ~20 KB (de ~0,87 MB para ~0,89 MB) — aceitável.
- Trocar uma ilustração no futuro é só substituir o PNG em `src/assets/f4p/` (mesmo nome de arquivo) e rodar `npm run build`; não precisa mexer no build script nem no JS, a menos que o nome do arquivo mude.
- Os arquivos-fonte ficam versionados no repositório (não são dados reais da empresa, são material de design fornecido pelo usuário para o relatório).
