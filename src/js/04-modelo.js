/* ---------------- modelo ---------------- */
/* colunas que já aparecem por padrão em cada nível (não entram como campo adicional) */
const DEF_FIELDS = {
  ini:["id","title","link","anosemestreroadmap","assigned to","work item type"],
  rel:["id","title","link","assigned to","parent","work item type"],
  epi:["id","title","link","parent","target date","work item type"],
  op:["id","title","link","id_epico_unicred","work item type"]};
function extrasOf(H, r, flow){
  const skip = new Set(flow.map(c => c.i)), o = {};
  H.forEach((h, i) => { if (skip.has(i) || !filled(h)) return; if (filled(r[i])) o[norm(h)] = r[i]; });
  return o;
}
function addAvail(avail, lvl, H, flow){
  const skip = new Set(flow.map(c => c.i));
  H.forEach((h, i) => { if (skip.has(i) || !filled(h)) return; const k = norm(h); if (!DEF_FIELDS[lvl].includes(k) && !avail[lvl][k]) avail[lvl][k] = String(h).trim(); });
}
const typeOf = (H, r) => { const i = colIdx(H, "Work Item Type"); return i >= 0 && filled(r[i]) ? String(r[i]).trim() : null; };
const linkOf = (H, r) => { const i = colIdx(H, "Link"); return i >= 0 && filled(r[i]) && /^https?:\/\//i.test(String(r[i]).trim()) ? String(r[i]).trim() : null; };
function buildModel(tables){
  const names = Object.keys(tables);
  const find = key => names.find(n => norm(n) === key) || names.find(n => norm(n).startsWith(key));
  const sIni = find("iniciativa"), sRel = find("release"), sEpi = find("epico");
  // times: abas "TIME ..." ou qualquer outra aba que tenha a coluna ID_EPICO_UNICRED
  const sTeams = names.filter(n => ![sIni, sRel, sEpi].includes(n) &&
    (norm(n).startsWith("time ") || (tables[n].headers || []).some(h => norm(h) === "id_epico_unicred")));
  const missing = [];
  if (!sIni) missing.push("Iniciativa"); if (!sRel) missing.push("Release"); if (!sEpi) missing.push("Épico");
  if (!sTeams.length) missing.push("abas dos times (com a coluna ID_EPICO_UNICRED)");
  if (missing.length) throw new Error("Não encontrei as abas: " + missing.join(", ") + ".");

  const warn = {orphans:[], badEpi:[], relNoEpi:[], iniNoRel:[], flow:[], badDates:0};
  const avail = {ini:{}, rel:{}, epi:{}, op:{}};
  const getFlow = (sheet, lvl) => {
    const fl = tables[sheet].flow || FLOW[lvl];   // carga do Azure: primeira e última coluna reais do quadro
    const f = flowCols(tables[sheet].headers, fl.start, fl.end);
    if (!f) throw new Error(`Na aba "${sheet}" não encontrei as colunas de fluxo "${fl.start}" até "${fl.end}".`);
    return f;
  };

  // Iniciativas
  const T = tables[sIni], H = T.headers;
  const fIni = getFlow(sIni, "ini");
  const iId = colIdx(H,"ID"), iTitle = colIdx(H,"Title"), iSem = colIdx(H,"AnoSemestreRoadmap"), iAss = colIdx(H,"Assigned To");
  const inis = new Map();
  T.rows.forEach(r=>{
    const id = nid(r[iId]); if (!id) return;
    inis.set(id,{lvl:"ini", id, title: String(r[iTitle] ?? "(sem título)"), exec: filled(r[iSem]) ? String(r[iSem]).trim() : null,
      owner: iAss >= 0 && filled(r[iAss]) ? String(r[iAss]).replace(/<.*?>/g,"").trim() || null : null,
      st: statusOf(r,fIni), rels:[], row:r, link:linkOf(H, r), type:typeOf(H, r), x:extrasOf(H, r, fIni)});
  });

  // Releases
  const TR = tables[sRel], HR = TR.headers, fRel = getFlow(sRel,"rel");
  const rId = colIdx(HR,"ID"), rTitle = colIdx(HR,"Title"), rPar = colIdx(HR,"Parent"), rAss = colIdx(HR,"Assigned To");
  const rels = new Map();
  TR.rows.forEach(r=>{
    const id = nid(r[rId]); if (!id) return;
    rels.set(id,{lvl:"rel", id, title:String(r[rTitle] ?? "(sem título)"), parent:nid(r[rPar]),
      owner: rAss >= 0 && filled(r[rAss]) ? String(r[rAss]).replace(/<.*?>/g,"").trim() : null, st: statusOf(r,fRel), epis:[], link:linkOf(HR, r), type:typeOf(HR, r), x:extrasOf(HR, r, fRel)});
  });

  // Épicos
  const TE = tables[sEpi], HE = TE.headers, fEpi = getFlow(sEpi,"epi");
  const eId = colIdx(HE,"ID"), eTitle = colIdx(HE,"Title"), ePar = colIdx(HE,"Parent"), eTgt = colIdx(HE,"Target Date");
  const epis = new Map();
  TE.rows.forEach(r=>{
    const id = nid(r[eId]); if (!id) return;
    const tgt = eTgt >= 0 ? toDate(r[eTgt]) : null;
    if (eTgt >= 0 && filled(r[eTgt]) && !tgt) warn.badDates++;
    const st = statusOf(r,fEpi);
    const e = {lvl:"epi", id, title: filled(r[eTitle]) ? String(r[eTitle]) : null, parent: nid(r[ePar]),
      target: tgt, interno: semestre(tgt), st, stDate: st >= 0 ? toDate(r[fEpi[st].i]) : null, ops:[], link:linkOf(HE, r), type:typeOf(HE, r), x:extrasOf(HE, r, fEpi)};
    epis.set(id,e);
  });

  // Registros dos times
  const ops = new Map(); const teamStages = []; const teamFlow = {};
  sTeams.forEach(sheet=>{
    const TT = tables[sheet], HT = TT.headers;
    const f = getFlow(sheet,"op");
    teamStages.push(f.map(c=>c.name)); addAvail(avail, "op", HT, f);
    teamFlow[sheet.replace(/^time\s+/i,"").trim()] = f.map(c=>c.name);
    const oId = colIdx(HT,"ID"), oEpi = colIdx(HT,"ID_EPICO_UNICRED"), oTitle = colIdx(HT,"Title"), oType = colIdx(HT,"Work Item Type");
    const oReady = colIdx(HT,"READY / PRONTO PARA DEV"), oDep = colIdx(HT,"Pronto para Deploy");
    const oTags = colIdx(HT,"Tags"), oBlk = colIdx(HT,"Blocked"), oBlkD = colIdx(HT,"Blocked Days"), oTgt = colIdx(HT,"Target Date");
    const team = sheet.replace(/^time\s+/i,"").trim();
    TT.rows.forEach(r=>{
      const id = nid(r[oId]); if (!id) return;
      const fd = {}; f.forEach(c => { const d = toDate(r[c.i]); if (d) fd[norm(c.name)] = d; });
      const ready = oReady >= 0 ? toDate(r[oReady]) : null;
      const deploy = oDep >= 0 ? toDate(r[oDep]) : null;
      const ct = ready ? (deploy ? days(ready, deploy) : days(ready, TODAY)) : null;
      const st = statusOf(r,f);
      const o = {lvl:"op", id, key:`op:${team}:${id}`, team, sheet, fd, link:linkOf(HT, r), x:extrasOf(HT, r, f), title:String(r[oTitle] ?? "(sem título)").trim(),
        type: oType >= 0 && filled(r[oType]) ? String(r[oType]) : null,
        epicoId: nid(r[oEpi]), ready, deploy, ct, stName: st >= 0 ? f[st].name : "Sem status", stDate: st >= 0 ? toDate(r[f[st].i]) : null,
        tags: oTags >= 0 && filled(r[oTags]) ? String(r[oTags]).replace(/^\s*\[|\]\s*$/g, "").split(/[|;,]/).map(s => s.trim()).filter(Boolean) : [],
        blocked: oBlk >= 0 && /^(true|sim|1|yes|verdadeiro)$/i.test(String(r[oBlk] ?? "").trim()),
        blockedDays: oBlkD >= 0 && filled(r[oBlkD]) ? parseInt(r[oBlkD], 10) || 0 : 0,
        target: oTgt >= 0 ? toDate(r[oTgt]) : null};
      o.health = "ok"; o.reasons = [];
      ops.set(o.key,o);
    });
  });

  // União ordenada das etapas dos times
  const opStages = [];
  teamStages.forEach(list => list.forEach((s,k)=>{
    if (opStages.some(x => norm(x) === norm(s))) return;
    const prev = k > 0 ? opStages.findIndex(x => norm(x) === norm(list[k-1])) : -1;
    opStages.splice(prev + 1 || (k === 0 ? 0 : opStages.length), 0, s);
  }));

  // Validade (regras 13-15) e vínculos
  epis.forEach(e=>{
    e.valid = !!(e.id && e.title && e.parent && rels.has(e.parent));
    if (!e.valid) warn.badEpi.push(e);
    else rels.get(e.parent).epis.push(e.id);
  });
  /* Regra: toda iniciativa existe no portal; a release precisa de uma iniciativa como Parent.
     Iniciativa sem release e release sem épico aparecem com selo ("sem release" / "sem épico"),
     exceto as já concluídas (última coluna do fluxo). Ver computeVisible. */
  rels.forEach(r=>{
    r.valid = inis.has(r.parent);
    if (!r.valid) warn.relNoEpi.push({...r, reason: r.parent ? `Parent ${r.parent} não encontrado na aba Iniciativa` : "sem Parent"});
    else inis.get(r.parent).rels.push(r.id);
  });
  inis.forEach(i=>{ i.valid = true; });
  ops.forEach(o=>{
    const e = epis.get(o.epicoId);
    if (!e) warn.orphans.push(o);
    else e.ops.push(o.key);
  });

  // Roadmap executivo herdado e divergência
  epis.forEach(e=>{
    if (!e.valid) return;
    const r = rels.get(e.parent); const i = inis.get(r.parent);
    e.exec = i ? i.exec : null;
    e.diverge = !!(e.exec && e.interno && norm(e.exec) !== norm(e.interno));
  });

  const stages = {
    ini: fIni.map(c=>c.name), rel: fRel.map(c=>c.name), epi: fEpi.map(c=>c.name), op: opStages
  };
  const teams = sTeams.map(s => s.replace(/^time\s+/i,"").trim());
  addAvail(avail, "ini", H, fIni); addAvail(avail, "rel", HR, fRel); addAvail(avail, "epi", HE, fEpi);
  return {inis, rels, epis, ops, stages, teams, teamFlow, warn, fieldsAvail: avail, hasIniOwner: iAss >= 0, sheetNames:{sIni,sRel,sEpi,sTeams}};
}

