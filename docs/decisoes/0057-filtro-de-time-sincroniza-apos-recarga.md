# 0057 — Filtro de Time fica dessincronizado do `<select>` depois de recarregar os dados

## Contexto

O usuário relatou (algumas vezes, segundo ele) que depois de clicar em "atualizar os dados" na
integração com o Azure DevOps, com o filtro de **Time** já selecionado antes da atualização, os menus
Visão analítica, Report F4P e Actionable não habilitavam. O `<select>` de Time continuava mostrando o
time selecionado depois da atualização; ao escolher um Roadmap interno em seguida, a barra de filtros
mostrava "1 filtro ativo" (só o Roadmap) em vez de 2, e os painéis continuavam desabilitados — eles
exigem Time **e** Roadmap (`anEnabled`/`f4pEnabled`/`actEnabled`).

## Investigação

`loadTables()` (chamada tanto por uma nova importação quanto por "atualizar os dados" do Azure DevOps,
`src/js/22-azure-janela-e-cache.js:133`) chama `fillFilters()`
(`src/js/17-filtros-e-carga.js`), que fazia, nesta ordem:

```js
$("fExec").innerHTML = opt(exec, "Todos"); $("fInt").innerHTML = opt(intr, "Todos"); fillTeamFilter();
$("fBusca").value = "";
S.f = {exec:"", owners:new Set(), int:"", team:"", q:""}; S.path = {}; ...
```

`fillTeamFilter()` (`src/js/11-filtros-e-diagnostico.js`) lê o valor atual do `<select>` de Time
**antes** de reconstruir as `<option>`, e tenta preservá-lo se o time ainda existir nos dados
recarregados:

```js
function fillTeamFilter(){
  const sel = $("fTeam"), cur = sel.value;
  sel.innerHTML = `<option value="">Todos os times</option>` + ...;
  sel.value = [...sel.options].some(o => o.value === cur) ? cur : "";
  if (sel.value !== cur){ S.f.team = ""; }   // só corrigia S.f.team no caso de LIMPAR
}
```

Essa função é chamada em **três** lugares: aqui, em `fillFilters()`; e depois de salvar Configurações
ou a fonte do Azure DevOps (`19-tela-configuracoes.js`, `20-azure-conexoes-e-fontes.js`) — nesses dois
últimos, `S.f` não é tocado por mais nada, então a lógica "só corrige no caso de limpar" é suficiente
(o valor já preservado do `<select>` já batia com `S.f.team`). **Mas dentro de `fillFilters()`**,
`fillTeamFilter()` roda **antes** da linha `S.f = {...}`, que zera `S.f.team` por cima — resultado: o
`<select>` continuava mostrando o time antigo (preservado corretamente), mas `S.f.team` virava `""`
por baixo. Dessincronização exatamente como o usuário descreveu.

## Decisão

Duas mudanças, as duas em `fillTeamFilter()`/`fillFilters()`:

1. `fillTeamFilter()` passa a **sempre** atribuir `S.f.team = sel.value` (o valor já resolvido do
   `<select>`, preservado ou limpo), não só no caso de limpar. Vira a única fonte de verdade: depois de
   chamada, `<select>` e `S.f.team` nunca divergem, **independente de quando for chamada** ou do que
   aconteceu com `S.f` antes dela. Nos outros dois call sites (Configurações, fonte do Azure), o
   comportamento é idêntico ao anterior (mudança sem efeito observável ali).
2. Em `fillFilters()`, a chamada a `fillTeamFilter()` passa a rodar **depois** do reset de `S.f`, não
   antes — assim o reset não tem mais chance de sobrescrever o que `fillTeamFilter()` acabou de decidir.

## Consequência

Depois de uma recarga de dados (nova importação ou atualização do Azure DevOps), o filtro de Time
permanece selecionado se aquele time ainda existir nos dados recarregados — `<select>` e `S.f.team`
sempre batem. Selecionar um Roadmap logo em seguida habilita os painéis normalmente, sem precisar
reselecionar o Time. Os demais filtros (Roadmap executivo/interno, Responsável, ID/descrição) continuam
sendo limpos numa recarga, como já era — essa decisão não muda isso, só corrige a dessincronização do
Time.
