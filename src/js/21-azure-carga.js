/* ---------- carga de uma fonte ---------- */
function azKeys(cols){ const k = []; cols.forEach(c => { if (c.isSplit){ k.push({key:c.name + " Doing", id:c.id, done:"Doing"}); k.push({key:c.name + " Done", id:c.id, done:"Done"}); } else k.push({key:c.name, id:c.id, done:null}); }); return k; }
async function azLoadSource(src, st){
  const A = azCfgOf(CFG), org = src.org, base = `${azDev(org)}/${azSeg(src.project)}`, tbase = `${base}/${azSeg(src.team)}`;
  st.begin("disc");
  const tfv = await azFetch(org, `${tbase}/_apis/work/teamsettings/teamfieldvalues?${AZ_API}`);
  const bl = await azFetch(org, `${tbase}/_apis/work/backlogs?${AZ_API}`), lvl = bl.value.find(l => l.name === src.level);
  if (!lvl) throw new Error(`o nível de backlog "${src.level}" não existe mais no time ${src.team}`);
  const cols = (await azFetch(org, `${tbase}/_apis/work/boards/${azSeg(src.level)}/columns?${AZ_API}`)).value, keys = azKeys(cols);
  // id do próprio board (não só das colunas): usado para não confundir o histórico deste board com o
  // de outro time que também enxerga o mesmo item (mesma Area Path incluída em mais de um board) — ver
  // decisão 0033. Se a chamada falhar por algum motivo, a carga segue sem o filtro (mais tolerante que
  // travar a fonte inteira por causa disto).
  const boardId = await azFetch(org, `${tbase}/_apis/work/boards/${azSeg(src.level)}?${AZ_API}`).then(b => b.id, () => null);
  const F = await azFields(org), fEpic = F.find(A.fields.epic), fRoad = F.find(A.fields.roadmap), fClass = F.find(CFG.anClassCol || "");
  st.done("disc", `${tfv.values.length} área(s), ${cols.length} colunas, ${(lvl.workItemTypes || []).length} tipos`);
  st.begin("wiql");
  const q = s => `'${String(s).replace(/'/g, "''")}'`;
  const wiql = `SELECT [System.Id] FROM WorkItems WHERE (${tfv.values.map(v => `[System.AreaPath] ${v.includeChildren ? "UNDER" : "="} ${q(v.value)}`).join(" OR ")}) AND (${(lvl.workItemTypes || []).map(w => `[System.WorkItemType] = ${q(w.name)}`).join(" OR ")}) ORDER BY [System.Id] ASC`;
  const ids = (await azFetch(org, `${base}/_apis/wit/wiql?$top=20000&${AZ_API}`, {method:"POST", body:JSON.stringify({query:wiql})})).workItems.map(x => x.id);
  st.done("wiql", `${ids.length.toLocaleString("pt-BR")} itens`);
  st.begin("fields");
  const fields = ["System.Id","System.Title","System.WorkItemType","System.State","System.Tags","System.AssignedTo","System.Parent","System.AreaPath","System.IterationPath","Microsoft.VSTS.Common.Priority","Microsoft.VSTS.Scheduling.TargetDate", fEpic, fRoad, fClass].filter(Boolean);
  const chunks = []; for (let i = 0; i < ids.length; i += 200) chunks.push(ids.slice(i, i + 200));
  const items = new Map();
  await azPool(chunks.map(ch => async () => {
    const r = await azFetch(org, `${base}/_apis/wit/workitemsbatch?${AZ_API}`, {method:"POST", body:JSON.stringify({ids:ch, fields})});
    r.value.forEach(x => items.set(x.id, {id:x.id, f:x.fields || {}, remote:[]}));
  }), 4, (d, n) => st.prog("fields", `lote ${d} de ${n}`, d / n));
  st.done("fields", `${items.size.toLocaleString("pt-BR")} itens em ${chunks.length} lote(s)`);
  // links Remote Related só para itens operacionais sem o campo do épico preenchido
  if (src.role === "op"){
    st.begin("remote");
    const need = [...items.values()].filter(x => !x.f[fEpic] && !x.f["System.Parent"]).map(x => x.id), rc = []; for (let i = 0; i < need.length; i += 200) rc.push(need.slice(i, i + 200));
    await azPool(rc.map(ch => async () => {
      const r = await azFetch(org, `${base}/_apis/wit/workitemsbatch?${AZ_API}`, {method:"POST", body:JSON.stringify({ids:ch, $expand:"Relations"})});
      r.value.forEach(x => { const it = items.get(x.id); if (it) (x.relations || []).filter(rl => /remote/i.test(rl.rel)).forEach(rl => { const m = /(\d+)\s*$/.exec(rl.url || ""); if (m) it.remote.push(m[1]); }); });
    }), 4, (d, n) => st.prog("remote", `lote ${d} de ${n}`, d / n));
    st.done("remote", need.length ? `${need.length.toLocaleString("pt-BR")} itens sem o campo e sem Parent verificados` : "todos os itens têm o campo do épico ou Parent");
  }
  st.begin("hist");
  const an = `https://analytics.dev.azure.com/${azSeg(org)}/${azSeg(src.project)}/_odata/v4.0-preview/WorkItemRevisions`, revs = new Map(); let nrev = 0;
  await azPool(chunks.map(ch => async () => {
    let url = `${an}?$filter=${encodeURIComponent(`WorkItemId in (${ch.join(",")})`)}&$select=WorkItemId,Revision,ChangedDate,CreatedDate,State,TagNames&$expand=${encodeURIComponent("BoardLocations($select=ColumnId,ColumnName,Done,LaneName,BoardId)")}&$orderby=WorkItemId`;
    while (url){ const r = await azFetch(org, url); r.value.forEach(v => { if (!revs.has(v.WorkItemId)) revs.set(v.WorkItemId, []); revs.get(v.WorkItemId).push(v); nrev++; }); url = r["@odata.nextLink"] || null; }
  }), 4, (d, n) => st.prog("hist", `lote ${d} de ${n} · ${nrev.toLocaleString("pt-BR")} revisões`, d / n));
  st.done("hist", `${nrev.toLocaleString("pt-BR")} revisões`);
  revs.forEach(l => l.sort((a, b) => a.ChangedDate < b.ChangedDate ? -1 : a.ChangedDate > b.ChangedDate ? 1 : (a.Revision || 0) - (b.Revision || 0)));
  return {src, cols, keys, items, revs, refs:{epic:fEpic, road:fRoad, cls:fClass}, nrev, boardId};
}
/* só os BoardLocations do board desta fonte — descarta os de outro time que também enxerga o item
   (ver decisão 0033). Sem L.boardId (chamada nova falhou), não filtra nada — comportamento anterior. */
function azOwnLocs(L, v){ return (v.BoardLocations || []).filter(b => !L.boardId || b.BoardId === L.boardId); }
/* colunas do histórico que não existem no quadro atual (e partes Done de colunas que deixaram de ser divididas) */
function azUnknown(L){
  const cur = new Map(L.cols.map(c => [c.id, c])), unk = {};
  L.revs.forEach(list => list.forEach(v => azOwnLocs(L, v).forEach(b => {
    const c = cur.get(b.ColumnId); if (c && (c.isSplit || b.Done !== "Done")) return;
    const id = c ? `${b.ColumnId}|Done` : b.ColumnId, name = c ? `${c.name} (parte Done, de quando a coluna era dividida)` : b.ColumnName;
    const u = unk[id] || (unk[id] = {names:new Set(), n:0, splitDone:!!c}); u.names.add(name); u.n++;
  })));
  return unk;
}
function azMapFor(L){
  const A = azCfgOf(CFG), m = A.maps[L.src.id] = A.maps[L.src.id] || {}, unk = azUnknown(L), fresh = [];
  // guarda nome(s) e contagem de cada coluna vista, pra tela de revisão do mapeamento em Configurações
  // conseguir mostrar algo legível mesmo sem uma carga recente (o valor salvo em A.maps é só a chave
  // da coluna atual escolhida, sem nome nem contagem) — ver decisão 0033.
  const meta = A.mapMeta[L.src.id] = A.mapMeta[L.src.id] || {};
  Object.entries(unk).forEach(([id, u]) => { meta[id] = {names:[...u.names], n:u.n}; if (id in m) return; fresh.push(id);
    if (u.splitDone){ const j = L.keys.findIndex(k => k.id === id.split("|")[0]); m[id] = L.keys[j + 1] ? L.keys[j + 1].key : ""; } else m[id] = ""; });
  return {map:m, unk, fresh};
}
/* datas das colunas pela regra validada */
function azDates(L, map, id, created){
  const idx = Object.fromEntries(L.keys.map((k, i) => [k.key, i])), cur = new Map(L.cols.map(c => [c.id, c]));
  const keyOf = b => { const c = cur.get(b.ColumnId);
    if (c && !c.isSplit && b.Done === "Done") return map[`${b.ColumnId}|Done`] || null;
    const k = L.keys.find(k => k.id === b.ColumnId && (k.done === null || k.done === (b.Done === "Done" ? "Done" : "Doing")));
    return k ? k.key : (map[b.ColumnId] || null); };
  const first = {}; let prev = null;
  (L.revs.get(id) || []).forEach(v => {
    const k = azOwnLocs(L, v).map(keyOf).find(Boolean); if (!k || k === prev) return;
    if (prev !== null && idx[k] < idx[prev]) Object.keys(first).forEach(x => { if (idx[x] > idx[k]) delete first[x]; });
    if (!(k in first)) first[k] = String(v.ChangedDate).slice(0, 10); prev = k;
  });
  const out = L.keys.map(k => first[k.key] || "");
  if (created) out[0] = created;
  const ci = prev ? idx[prev] : -1; let nxt = "";
  for (let i = out.length - 1; i >= 0; i--){ if (out[i]) nxt = out[i]; else if (nxt && (ci < 0 || i < ci)) out[i] = nxt; }
  return out;
}
const azDay = iso => { if (!iso) return ""; const d = new Date(iso); return isNaN(d) ? "" : `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`; };
const azPerson = p => !p ? "" : typeof p === "string" ? p : `${p.displayName || ""}${p.uniqueName ? ` <${p.uniqueName}>` : ""}`;
/* monta a "aba" no formato da planilha */
function azSheet(L, map, notes, epiIds){
  const A = azCfgOf(CFG), role = L.src.role, R = L.refs;
  const extra = role === "ini" ? ["Work Item Type","Assigned To","AnoSemestreRoadmap", CFG.anClassCol || "Classificação_Despesas_Comitê","Tags"]
    : role === "rel" ? ["Work Item Type","Assigned To","Parent","Tags"]
    : role === "epi" ? ["Work Item Type","Assigned To","Parent","Target Date","Tags"]
    : ["Work Item Type","Tags","Blocked","Blocked Days","Priority","Area Path","Iteration Path","ID_EPICO_UNICRED"];
  const headers = ["ID","Title","Link", ...L.keys.map(k => k.key), ...extra], rows = [];
  L.items.forEach(it => {
    const l = L.revs.get(it.id) || [], last = l[l.length - 1], state = it.f["System.State"] || (last && last.State) || "";
    if (A.excludeRemoved && /^removed$/i.test(state)){ notes.removed++; (notes.removedIds = notes.removedIds || []).push(`${L.src.role}:${it.id}`); return; }
    const created = last && last.CreatedDate ? String(last.CreatedDate).slice(0, 10) : azDay(it.f["System.CreatedDate"]);
    const dates = azDates(L, map, it.id, created), tags = String(it.f["System.Tags"] || "").split(";").map(s => s.trim()).filter(Boolean);
    const blocked = tags.some(x => /^blocked$/i.test(x));
    let bdays = "";
    if (blocked){ let since = null; for (let i = l.length - 1; i >= 0; i--){ if (/\bblocked\b/i.test(l[i].TagNames || "")) since = l[i].ChangedDate; else break; } if (since) bdays = String(Math.max(0, days(new Date(since), TODAY))); }
    let epic = R.epic ? it.f[R.epic] : "";
    if (role === "op"){
      // vínculo com o épico: campo ID_EPICO_UNICRED > Parent (quando é um épico carregado, mesma organização) > link Remote Related
      const par = it.f["System.Parent"] ? String(it.f["System.Parent"]) : "";
      if (!epic && par && epiIds && epiIds.has(par)){ epic = par; notes.byParent = (notes.byParent || 0) + 1; }
      if (!epic && it.remote.length) epic = it.remote[0];
      else if (epic && it.remote.length && !it.remote.includes(String(epic))) notes.divergent.push({team:L.src.alias || L.src.team, id:it.id, campo:String(epic), remoto:it.remote.join(", ")});
    }
    const v = {"Work Item Type":it.f["System.WorkItemType"] || "", "Assigned To":azPerson(it.f["System.AssignedTo"]), "Parent":it.f["System.Parent"] || "",
      "Target Date":azDay(it.f["Microsoft.VSTS.Scheduling.TargetDate"]), "AnoSemestreRoadmap":R.road ? (it.f[R.road] || "") : "",
      [CFG.anClassCol || "Classificação_Despesas_Comitê"]:R.cls ? (it.f[R.cls] || "") : "", "Tags":tags.length ? `[${tags.join("| ")}]` : "",
      "Blocked":blocked ? "true" : "false", "Blocked Days":bdays, "Priority":it.f["Microsoft.VSTS.Common.Priority"] ?? "",
      "Area Path":it.f["System.AreaPath"] || "", "Iteration Path":it.f["System.IterationPath"] || "", "ID_EPICO_UNICRED":epic || ""};
    rows.push([String(it.id), it.f["System.Title"] || "", `${azDev(L.src.org)}/${azSeg(L.src.project)}/_workitems/edit/${it.id}`, ...dates, ...extra.map(k => v[k] ?? "")].map(x => x === "" ? null : x));
  });
  return {headers, rows, flow:{start:L.keys[0].key, end:L.keys[L.keys.length - 1].key, keys:L.keys.map(k => k.key)}};
}
/* várias fontes do mesmo nível (ex.: coordenações de épico) viram uma aba só */
function azMerge(sheets){
  if (sheets.length === 1) return sheets[0];
  // fluxo unificado: junta as colunas dos quadros na ordem, inserindo cada coluna nova depois da anterior do seu quadro
  const flow = [];
  sheets.forEach(s => (s.flow ? s.flow.keys : []).forEach((k, i, arr) => {
    if (flow.some(x => norm(x) === norm(k))) return;
    const prev = i ? flow.findIndex(x => norm(x) === norm(arr[i - 1])) : -1;
    flow.splice(prev >= 0 ? prev + 1 : (i === 0 ? 0 : flow.length), 0, k);
  }));
  const isFlow = h => flow.some(x => norm(x) === norm(h));
  const extra = []; sheets.forEach(s => s.headers.forEach(h => { if (!["ID","Title","Link"].includes(h) && !isFlow(h) && !extra.includes(h)) extra.push(h); }));
  const headers = ["ID","Title","Link", ...flow, ...extra];
  const rows = []; sheets.forEach(s => s.rows.forEach(r => rows.push(headers.map(h => { const i = s.headers.findIndex(x => norm(x) === norm(h)); return i >= 0 ? r[i] : null; }))));
  return {headers, rows, flow:{start:flow[0], end:flow[flow.length - 1], keys:flow}};
}
function azBuildTables(){
  const epiIds = new Set(); (AZ.raw || []).filter(L => L.src.role === "epi").forEach(L => L.items.forEach((_, id) => epiIds.add(String(id))));
  const notes = {removed:0, divergent:[]}, tables = {}, byRole = {ini:[], rel:[], epi:[]};
  AZ.raw.forEach(L => {
    const sh = azSheet(L, azMapFor(L).map, notes, epiIds);
    if (L.src.role === "op") tables[L.src.alias || L.src.team] = sh; else byRole[L.src.role].push(sh);
  });
  AZ_ROLES.filter(r => r.sheet).forEach(r => { if (byRole[r.id].length) tables[r.sheet] = azMerge(byRole[r.id]); });
  return {tables, notes};
}

