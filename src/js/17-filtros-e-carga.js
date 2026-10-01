/* ---------------- filtros ---------------- */
function fillFilters(){
  const M = S.model;
  const exec = [...new Set([...M.inis.values()].filter(i=>iniCanAppear(i) && i.exec).map(i=>i.exec))].sort();
  const intr = [...new Set([...M.epis.values()].filter(e=>e.valid && e.interno).map(e=>e.interno))].sort();
  const opt = (list, all) => `<option value="">${all}</option>` + list.map(v=>`<option>${esc(v)}</option>`).join("");
  const om = new Map();
  M.inis.forEach(i => { if (!iniCanAppear(i)) return; const k = i.owner ? norm(i.owner) : "__none__";
    if (!om.has(k)) om.set(k, {k, label: i.owner || "(sem responsável)", n:0}); om.get(k).n++; });
  S.ownerList = [...om.values()].sort((a,b) => a.k === "__none__" ? 1 : b.k === "__none__" ? -1 : a.label.localeCompare(b.label,"pt-BR"));
  $("fOwnerBox").hidden = !M.hasIniOwner;
  $("msSearch").value = ""; closeMs();
  $("fExec").innerHTML = opt(exec, "Todos"); $("fInt").innerHTML = opt(intr, "Todos");
  $("fBusca").value = "";
  S.f = {exec:"", owners:new Set(), int:"", team:"", q:""}; S.path = {}; S.pathQueryId = null; S.expand = false; S.focus = null; S.offsets = {}; S.offsetsSig = null;
  /* decisão 0057: fillTeamFilter() roda por ÚLTIMO — ela decide sozinha o valor final de S.f.team
     (preserva a seleção anterior do <select> de Time se o time ainda existir nos dados recarregados,
     limpa senão). Chamá-la antes do reset acima deixava o <select> mostrando o time de antes enquanto
     S.f.team virava "" por baixo — depois de uma atualização do Azure DevOps com Time já selecionado,
     os painéis (Visão analítica/Report F4P/Actionable) ficavam presos desabilitados mesmo escolhendo
     um Roadmap em seguida, porque faltava o Time "de verdade" no estado. */
  fillTeamFilter();
  msLabel();
}
function loadTables(tables, label, imp){
  S.tables = tables;
  S.importNotes = imp;
  try{
    S.model = buildModel(tables);
  }catch(err){ toast(err.message, 6000); return false; }
  document.body.classList.remove("gate-active");
  recomputeHealth();
  $("srcLabel").textContent = label;
  fillFilters(); closeDrawer(); render();
  toast(`Carregado: ${S.model.inis.size} iniciativas, ${S.model.epis.size} épicos, ${S.model.ops.size} itens de times.`, 3200);
  return true;
}

let tt; function toast(msg, ms=3200){ const t = $("toast"); t.textContent = msg; t.classList.add("show"); clearTimeout(tt); tt = setTimeout(()=>t.classList.remove("show"), ms); }

