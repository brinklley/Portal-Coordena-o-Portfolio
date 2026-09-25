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
  $("fExec").innerHTML = opt(exec, "Todos"); $("fInt").innerHTML = opt(intr, "Todos"); fillTeamFilter();
  $("fIni").value = ""; $("goto").value = "";
  S.f = {exec:"", owners:new Set(), int:"", team:"", ini:""}; S.path = {}; S.expand = false; S.focus = null; S.offsets = {}; msLabel();
}
function loadTables(tables, label, isDemo, imp){
  S.isDemo = !!isDemo; S.tables = tables;
  S.importNotes = imp || newImport();
  try{
    S.model = buildModel(tables);
  }catch(err){ toast(err.message, 6000); return false; }
  recomputeHealth();
  $("srcLabel").textContent = label;
  $("notice").hidden = !isDemo;
  fillFilters(); closeDrawer(); render();
  if (!isDemo){
    const n = S.importNotes, extra = [];
    if (n.csvSheets.length) extra.push(`formato CSV detectado em ${n.csvSheets.length} ${n.csvSheets.length === 1 ? "aba" : "abas"}`);
    if (n.fixed.length) extra.push(`${n.fixed.length} ${n.fixed.length === 1 ? "registro reparado" : "registros reparados"}`);
    if (n.dropped.length) extra.push(`${n.dropped.length} ${n.dropped.length === 1 ? "registro ignorado" : "registros ignorados"} (veja Higiene de dados)`);
    toast(`Carregado: ${S.model.inis.size} iniciativas, ${S.model.epis.size} épicos, ${S.model.ops.size} itens de times${extra.length ? "; " + extra.join(", ") : ""}.`, extra.length ? 7000 : 3200);
  }
  return true;
}
$("file").onchange = async e => {
  const files = [...e.target.files]; e.target.value = "";
  if (!files.length) return;
  const imp = newImport(), tables = {};
  const put = (name, tb, from) => { if (tables[name]) imp.replaced.push({sheet:name, from}); tables[name] = tb; };
  try{
    for (const f of files){
      const buf = await f.arrayBuffer();
      if (/\.(csv|txt)$/i.test(f.name)){
        const name = f.name.replace(/\.[^.]+$/, "").trim();
        put(name, csvToTable(decodeText(buf).split(/\r?\n/), name, imp), f.name);
      } else {
        const wb = XLSX.read(new Uint8Array(buf), {type:"array", cellDates:false});
        Object.entries(tablesFromWorkbook(wb, imp)).forEach(([n, tb]) => put(n, tb, f.name));
      }
    }
  }catch(err){ return toast("Não consegui ler o arquivo. Confirme que é a planilha do Portal (.xlsx) ou arquivos .csv exportados.", 6000); }
  loadTables(tables, files.length === 1 ? files[0].name : `${files.length} arquivos`, false, imp);
};
$("btnDemo").onclick = () => loadTables(demoTables(), "dados de exemplo", true);
$("btnTemplate").onclick = () => {
  const t = demoTables(); const wb = XLSX.utils.book_new();
  Object.entries(t).forEach(([n, {headers, rows}]) => XLSX.utils.book_append_sheet(wb, XLSX.utils.aoa_to_sheet([headers, ...rows], {cellDates:true}), n));
  XLSX.writeFile(wb, "modelo_portal_portfolio.xlsx");
};

let tt; function toast(msg, ms=3200){ const t = $("toast"); t.textContent = msg; t.classList.add("show"); clearTimeout(tt); tt = setTimeout(()=>t.classList.remove("show"), ms); }

