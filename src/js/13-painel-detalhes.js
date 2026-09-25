/* ---------------- painel de detalhes ---------------- */
function alertsFor(lvl, ent){
  const M = S.model, V = S.V, team = S.f.team, out = [];
  const opsOf = e => e.ops.map(k => M.ops.get(k)).filter(o => (!team || o.team === team) && V.visOp.has(o.key));
  const divText = e => `O Target Date (${fmt(e.target)}) cai em ${e.interno}, mas a iniciativa está comprometida no roadmap executivo de ${e.exec}.`;
  const divAct = "Ou o prazo do épico precisa ser antecipado, ou o compromisso executivo precisa ser revisto. Alinhe com o responsável pela iniciativa antes que vire atraso percebido.";
  const addOps = ops => ops.forEach(o => (o.reasons || []).forEach(r => out.push({...r, pre:`#${o.id} ${o.team}`, go:o.id, action:null, op:o})));
  if (lvl === "op"){ (ent.reasons || []).forEach(r => out.push({...r, op:ent})); }
  else if (lvl === "epi"){ if (ent.diverge) out.push({lv:"alert", label:"Roadmap", kind:"div", text:divText(ent), action:divAct}); if (ent.valid) addOps(opsOf(ent)); }
  else {
    const epis = lvl === "rel"
      ? ent.epis.filter(id => V.visEpi.has(id)).map(id => M.epis.get(id))
      : ent.rels.filter(id => V.visRel.has(id)).flatMap(rid => M.rels.get(rid).epis.filter(id => V.visEpi.has(id)).map(id => M.epis.get(id)));
    epis.forEach(e => { if (e.diverge) out.push({lv:"alert", label:"Roadmap", kind:"div", pre:`Épico #${e.id}`, go:e.id, text:divText(e)}); });
    epis.forEach(e => addOps(opsOf(e)));
  }
  return out.sort((a,b) => RANK[b.lv] - RANK[a.lv]);
}
function meterHtml(m){
  // escala até o outlier (ou 1,5× o máximo), com marcas no CT máximo e no outlier
  const top = Math.max(m.out || 0, m.max * 1.5, m.ct);
  const w = x => Math.min(100, x / top * 100);
  const col = m.out && m.ct >= m.out ? "var(--outlier)" : m.ct > m.max ? "var(--alert)" : m.ct >= (m.warn || Infinity) ? "var(--warn)" : "var(--ok)";
  return `<div class="meter" role="img" aria-label="CT ${m.ct} de ${m.max} dias"><span style="width:${w(m.ct)}%;background:${col}"></span><i class="mk" style="left:${w(m.max)}%" title="CT máximo"></i>${m.out ? `<i class="mk" style="left:${w(m.out)}%;opacity:.3" title="Outlier"></i>` : ""}</div>
    <div class="meter-lab"><span>CT atual ${m.ct} d (${pctOf(m.ct, m.max)}% da meta)</span><span>máx. ${m.max} d${m.out ? ` · outlier ${m.out} d` : ""}</span></div>`;
}
/* resumo para épicos, releases e iniciativas: onde agir primeiro */
function summaryHtml(list){
  const ops = list.filter(x => x.op);
  if (!ops.length && !list.some(x => x.kind === "div")) return "";
  const b = [];
  const late = ops.filter(x => x.kind === "ct" && (x.lv === "alert" || x.lv === "outlier"));
  if (late.length){
    const sum = late.reduce((a, x) => a + (x.over || 0), 0), top = [...late].sort((a, c) => (c.over || 0) - (a.over || 0))[0];
    const open = late.filter(x => x.op.ready && !x.op.deploy).length;
    b.push(`<b>${late.length} ${late.length === 1 ? "item acima" : "itens acima"} do CT máximo</b>${sum ? `, somando ${dd(sum)} de atraso` : ""}; ${open ? `${open} ${open === 1 ? "ainda está aberto" : "ainda estão abertos"}` : "todos já concluídos"}. O maior é <b>#${esc(top.op.id)}</b> (${esc(top.op.team)}) com ${dd(top.op.ct)} de CT.`);
  }
  const near = ops.filter(x => x.kind === "ct" && x.lv === "warn");
  if (near.length) b.push(`<b>${near.length} ${near.length === 1 ? "item perto" : "itens perto"} do limite</b>: agir ${near.length === 1 ? "nele" : "neles"} agora evita novos atrasos.`);
  const stuck = ops.filter(x => x.kind === "stuck");
  if (stuck.length){ const s = [...stuck].sort((a, c) => c.stuck - a.stuck)[0];
    b.push(`<b>${stuck.length} ${stuck.length === 1 ? "item parado" : "itens parados"}</b> na mesma coluna; o mais antigo está há ${dd(s.stuck)} em “${esc(s.op.stName)}”.`); }
  (CFG.tags || []).forEach(tg => {
    const hits = ops.filter(x => x.kind === "tag" && x.tag === tg.id); if (!hits.length) return;
    const teams = [...new Set(hits.map(x => x.op.team))].join(", ");
    const chip = `<span class="tchp" style="background:${tg.color};color:${inkOn(tg.color)}">${esc(tg.name)}</span>`;
    if (tg.when === "target"){
      const dated = hits.filter(x => x.target).sort((a, c) => a.target - c.target);
      b.push(`${chip} <b>${hits.length} ${hits.length === 1 ? "item" : "itens"}</b> no nível operacional (${esc(teams)})${dated.length ? `; a data mais próxima é ${fmtL(dated[0].target)}, no time ${esc(dated[0].op.team)}` : "; data não informada na planilha"}.`);
    } else {
      const old = hits.filter(x => x.since).sort((a, c) => a.since - c.since)[0];
      const verb = tg.id === "blocked" ? (hits.length === 1 ? "bloqueado" : "bloqueados") : tg.id === "paused" ? (hits.length === 1 ? "pausado" : "pausados") : tg.id === "urgent" ? (hits.length === 1 ? "priorizado" : "priorizados") : "marcados";
      b.push(`${chip} <b>${hits.length} ${hits.length === 1 ? "item" : "itens"} ${verb}</b> no nível operacional (${esc(teams)})${old ? `; o mais antigo desde ${fmtL(old.since)}, no time ${esc(old.op.team)}` : ""}.`);
    }
  });
  const dv = list.filter(x => x.kind === "div");
  if (dv.length) b.push(`<b>${dv.length} ${dv.length === 1 ? "épico com" : "épicos com"} Target Date fora do roadmap executivo</b>.`);
  let tip = "";
  if (ops.some(x => x.tag === "blocked")) tip = "Sugestão: comece pelos bloqueios. Enquanto um item está bloqueado, o CycleTime dele e o do épico continuam correndo.";
  else if (late.some(x => x.op.ready && !x.op.deploy)) tip = "Sugestão: comece pelos itens em atraso ainda abertos, do maior para o menor, e evite puxar trabalho novo até destravá-los.";
  else if (near.length) tip = "Sugestão: priorize terminar os itens perto do limite antes de iniciar novos.";
  else if (stuck.length) tip = "Sugestão: leve os itens parados para a daily e descubra o que falta para andarem.";
  else if (dv.length) tip = "Sugestão: alinhe as datas dos épicos com o compromisso executivo da iniciativa.";
  return `<div class="al-sum"><h5>Resumo</h5><ul>${b.map(x => `<li>${x}</li>`).join("")}</ul>${tip ? `<div style="margin-top:6px;color:var(--ink-2)">${tip}</div>` : ""}</div>`;
}
function alertsHtml(list, lvl){
  if (!list.length) return `<div class="al-ok">Sem alertas.</div>`;
  const MAX = 15, cnt = lv => list.filter(x => x.lv === lv).length;
  const parts = [[cnt("outlier"),"outlier","outliers"],[cnt("alert"),"alerta","alertas"],[cnt("warn"),"atenção","atenções"],[cnt("info"),"aviso","avisos"]].filter(x => x[0]).map(([n,a,b]) => `${n} ${n === 1 ? a : b}`);
  const head = `<div class="sub">Alertas <span style="font-weight:400;color:var(--ink-3)">${parts.join(", ")}</span></div>`;
  const own = lvl === "op";   // no próprio item: medidor e sugestão completos
  const item = x => `<li class="al ${x.lv}">${x.kind === "tag" ? `<span class="tchp" style="background:${x.color};color:${inkOn(x.color)};margin-right:6px">${esc(x.label)}</span>` : ""}<span class="lv"${x.kind === "tag" ? ' style="display:none"' : ""}>${x.label || (x.lv === "outlier" ? "Outlier" : x.lv === "alert" ? "Alerta" : "Atenção")}</span>${x.pre ? `<button data-goid="${esc(x.go)}">${esc(x.pre)}</button>` : ""}
    <span class="txt">${esc(x.text)}</span>${own && x.meter ? meterHtml(x.meter) : ""}${x.action ? `<span class="act"><b>O que fazer:</b> ${esc(x.action)}</span>` : ""}</li>`;
  return head + (lvl !== "op" ? summaryHtml(list) : "") + `<ul class="alerts">${list.slice(0, MAX).map(item).join("")}</ul>`
    + (list.length > MAX ? `<div class="al-more">e mais ${list.length - MAX}. Abra os níveis abaixo ou clique nos itens para ver todos.</div>` : "");
}
/* itens do épico agrupados por categoria (Backlog, Discovery, WIP, Vazão), para conferir os números */
function catItemsHtml(e){
  const m = epiMetrics(e, S.f.team); if (!m.n) return "";
  const cat = o => { const c = catOf(o); return c === "vazao" ? "vaz" : c; };
  const groups = [["none","Backlog"],["disc","Discovery"],["wip","WIP"],["vaz","Vazão"]].map(([c, lab]) => [c, lab, m.recs.filter(o => cat(o) === c)]);
  return `<div class="sub">Itens por categoria${S.f.team ? ` (só ${esc(S.f.team)})` : ""}</div>` + groups.filter(g => g[2].length).map(([c, lab, list]) =>
    `<div class="catg"><div class="catg-h"><i class="sq ${c}"></i>${lab} <b>${list.length}</b></div><ul>${list.map(o =>
      `<li><button data-goid="${esc(o.id)}">#${esc(o.id)}</button> ${esc(o.title)} <span class="catg-col">${esc(o.team)} · ${esc(o.stName)}</span></li>`).join("")}</ul></div>`).join("")
    + `<p class="catg-tip">A categoria de cada coluna é definida em Configurações.</p>`;
}
const idList = (ops, max = 4) => ops.slice(0, max).map(o => "#" + o.id).join(", ") + (ops.length > max ? ` e mais ${ops.length - max}` : "");
function agText(m){
  if (m.ag) return `${fmtL(m.ag)} (última saída entre todos os ${m.n} itens)`;
  if (!m.n) return "--";
  return `-- (${m.agMissing.length} de ${m.n} ${m.n === 1 ? "item" : "itens"} ainda sem saída: ${idList(m.agMissing)})`;
}
/* como o CT do épico foi calculado: entrada, saída e itens considerados */
function ctExplainHtml(m){
  const c = (m.ctFromOp || m.recs[0] || {}).ctCols;
  const ent = c ? c.entry : "READY", sai = c ? c.exit : "Deploy";
  let h = `<div class="sub">Como o CT foi calculado</div><div class="ctx-box">`;
  if (!m.ctN) return h + `Nenhum item do tipo ${esc(ctTypesLabel())} vinculado a este épico${S.f.team ? " neste time" : ""}; por isso o CT fica vazio.</div>`;
  if (!m.ctFrom) return h + `Os ${m.ctN} itens do tipo ${esc(ctTypesLabel())} ainda não chegaram na coluna de entrada do CT (“${esc(ent)}”).</div>`;
  const tl = `<div class="ctx-tl"><div><span>Início</span><b>${fmtL(m.ctFrom)}</b><small>entrada de <button data-goid="${esc(m.ctFromOp.id)}">#${esc(m.ctFromOp.id)}</button> em “${esc(ent)}”</small></div>
    <div class="ctx-arrow"><b>${m.ct} ${m.ct === 1 ? "dia" : "dias"}</b></div>
    <div><span>Fim</span><b>${m.ctTo ? fmtL(m.ctTo) : "hoje"}</b><small>${m.ctTo ? `saída de <button data-goid="${esc(m.ctToOp.id)}">#${esc(m.ctToOp.id)}</button> em “${esc(sai)}”` : `ainda em andamento`}</small></div></div>`;
  h += tl + `<p>O CT vai da primeira entrada à última saída entre os <b>${m.ctN} ${m.ctN === 1 ? "item" : "itens"}</b> do tipo ${esc(ctTypesLabel())}${m.ctN < m.n ? ` (de ${m.n} itens do épico)` : ""}.`;
  if (!m.ctTo) h += ` Como ${m.ctOpen.length === 1 ? "1 item ainda não saiu" : `${m.ctOpen.length} itens ainda não saíram`} (${idList(m.ctOpen)}), o fim é hoje e o CT continua correndo.`;
  h += `</p>`;
  if (!m.ag && m.agMissing.length && m.ctTo) h += `<p class="muted">O Ag. Deploy fica vazio porque considera todos os tipos de item, e ${idList(m.agMissing)} ainda não ${m.agMissing.length === 1 ? "saiu" : "saíram"}.</p>`;
  return h + `</div>`;
}
function openDetail(key){
  S.detailKey = key;
  const M = S.model; const [lvl, ...rest] = key.split(":"); const id = lvl === "op" ? rest.slice(1).join(":") : rest.join(":");
  let title = "", kv = [], chainArr = [], flow = null, ctBlock = "";
  const ent = lvl === "ini" ? M.inis.get(id) : lvl === "rel" ? M.rels.get(id) : lvl === "epi" ? M.epis.get(id) : M.ops.get(key);
  if (!ent) return;
  const flowBar = (stages, st, c) => `<div class="flowbar" style="--lvlc:${c}">${stages.map((s,k)=>`<span class="${k <= st ? "done" : ""}" title="${esc(s)}"></span>`).join("")}</div><div class="flowlab"><span>${esc(stages[0])}</span><span>${esc(st >= 0 ? stages[st] : "Sem status")}</span></div>`;
  if (lvl === "ini"){
    title = "Iniciativa";
    kv = [["Status", ent.st >= 0 ? M.stages.ini[ent.st] : "Sem status"], ["Situação pelos filhos", SIT_LABEL[iniPhase(ent, S.V)]], ["Responsável", ent.owner ?? "--"], ["Roadmap executivo", ent.exec ?? "--"], ["Releases", ent.rels.length]];
    flow = flowBar(M.stages.ini, ent.st, "var(--ini)");
  } else if (lvl === "rel"){
    title = "Release";
    kv = [["Status", ent.st >= 0 ? M.stages.rel[ent.st] : "Sem status"], ["Situação pelos filhos", SIT_LABEL[relPhase(ent, S.V)]], ["Responsável", ent.owner ?? "--"], ["Épicos", ent.epis.length]];
    flow = flowBar(M.stages.rel, ent.st, "var(--rel)");
  } else if (lvl === "epi"){
    title = "Épico";
    const m = epiMetrics(ent, S.f.team);
    kv = [["Status", ent.st >= 0 ? M.stages.epi[ent.st] : "Sem status"], ["Target Date", fmt(ent.target)], ["Roadmap interno", ent.interno ?? "--"], ["Roadmap executivo", ent.exec ?? "--"],
      ["Fase", PHASE_LABEL[m.phase]], ["Itens nos times", m.n + (S.f.team ? ` (só ${S.f.team})` : "")], ["Backlog / outras colunas", m.none], ["Discovery (iniciados, fora do WIP)", m.disc], ["WIP (em aberto)", m.wip], ["Vazão (concluídos)", m.vaz], ["Ag. Deploy", agText(m)]];
    ctBlock = ctExplainHtml(m);
    if (!ent.valid) kv.unshift(["Atenção", "Épico inválido: sem título ou Parent sem Release correspondente"]);
    flow = flowBar(M.stages.epi, ent.st, "var(--epi)");
  } else {
    title = "Item do time " + ent.team;
    const st = stageIndex(M.stages.op, ent.stName);
    kv = [["Status", ent.stName], [`Entrada do CT (${ent.ctCols ? ent.ctCols.entry : "--"})`, fmt(ent.ready)], [`Saída do CT (${ent.ctCols ? ent.ctCols.exit : "--"})`, fmt(ent.deploy)], ["CycleTime", ent.ct != null ? ent.ct + (ent.deploy ? " dias" : " dias (em andamento)") : "--"]];
    if (!M.epis.has(ent.epicoId)) kv.unshift(["Atenção", `Órfão: ID_EPICO_UNICRED ${ent.epicoId ?? "vazio"} não existe na aba Épico`]);
    flow = flowBar(M.stages.op, st, "var(--op)");
  }
  // rastreabilidade (de baixo para cima)
  let cur = {lvl, ent};
  while (cur){
    const e = cur.ent;
    if (cur.lvl === "op"){ chainArr.push({c:"var(--op)", k:e.key, label:`#${e.id} ${e.title}`, key:`ID_EPICO_UNICRED = ${e.epicoId ?? "vazio"}`});
      const p = M.epis.get(e.epicoId); cur = p ? {lvl:"epi", ent:p} : null; }
    else if (cur.lvl === "epi"){ chainArr.push({c:"var(--epi)", k:"epi:"+e.id, label:`#${e.id} ${e.title ?? "(sem título)"}`, key:`Parent = ${e.parent ?? "vazio"}`});
      const p = M.rels.get(e.parent); cur = p ? {lvl:"rel", ent:p} : null; }
    else if (cur.lvl === "rel"){ chainArr.push({c:"var(--rel)", k:"rel:"+e.id, label:`#${e.id} ${e.title}`, key:`Parent = ${e.parent ?? "vazio"}`});
      const p = M.inis.get(e.parent); cur = p ? {lvl:"ini", ent:p} : null; }
    else { chainArr.push({c:"var(--ini)", k:"ini:"+e.id, label:`#${e.id} ${e.title}`, key:`AnoSemestreRoadmap = ${e.exec ?? "--"}`}); cur = null; }
  }
  chainArr.reverse();
  $("dTitle").textContent = title;
  $("dBody").innerHTML = `<h4 style="margin:0 0 4px;font-size:15px">${esc(ent.title ?? "(sem título)")}</h4>
    <div style="font-size:12px;color:var(--ink-2)">ID ${esc(ent.id)}${ent.link ? ` · <a href="${esc(ent.link)}" target="_blank" rel="noopener" style="color:var(--ini)">abrir no Azure DevOps ↗</a>` : ""}</div>
    ${flow}
    ${alertsHtml(alertsFor(lvl, ent), lvl)}
    <dl class="kv">${(ent.type ? [["Tipo", ent.type]] : []).concat(kv).map(([a,b])=>`<dt>${esc(a)}</dt><dd>${esc(b)}</dd>`).join("")}</dl>
    ${(() => { const sel = ((CFG.fields || {})[lvl] || []), names = (M.fieldsAvail || {})[lvl] || {}, ks = sel.filter(k => names[k]);
      return ks.length ? `<div class="sub">Campos adicionais</div><dl class="kv">${ks.map(k => `<dt>${esc(names[k])}</dt><dd>${esc(fmtField(k, (ent.x || {})[k]))}</dd>`).join("")}</dl>` : ""; })()}
    ${lvl === "epi" ? ctBlock + catItemsHtml(ent) : ""}
    <div class="sub">Por que está aqui</div>
    <ul class="chain">${chainArr.map(x=>`<li style="--c:${x.c}"><button data-goto="${esc(x.k)}">${esc(x.label)}</button><span class="key">${esc(x.key)}</span></li>`).join("")}</ul>`;
  $("dBody").querySelectorAll("[data-goto]").forEach(b => b.onclick = () => { const k = b.dataset.goto; const [l,...r] = k.split(":"); gotoId(l === "op" ? r.slice(1).join(":") : r.join(":")); });
  $("dBody").querySelectorAll("[data-goid]").forEach(b => b.onclick = () => gotoId(b.dataset.goid));
  openDrawer();
}
function laneBox(ln){
  // caixa do conteúdo do nível (níveis centralizados ou fileiras de ilhas)
  const parts = [...ln.querySelectorAll(":scope > .lane-inner, .isl-row")].map(pos);
  if (!parts.length) return pos(ln);
  return {l:Math.min(...parts.map(p=>p.l)), r:Math.max(...parts.map(p=>p.r)), t:pos(ln).t, b:pos(ln).b};
}
const smooth = () => matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth";
function revealLane(lvl){
  requestAnimationFrame(() => requestAnimationFrame(() => {
    const ln = $("lane-" + lvl); if (!ln) return;
    const bx = laneBox(ln);
    const left = ((bx.l + bx.r) / 2) * Z - vp.clientWidth / 2;
    vp.scrollTo({top: bx.t * Z - 24, left: Math.max(0, left), behavior: smooth()});
  }));
}
function focusIsland(team){
  const el = board.querySelector(`.island[data-team="${cssEsc(team)}"]`); if (!el) return;
  const p = pos(el), w = p.r - p.l, h = p.b - p.t;
  const z = Math.max(0.35, Math.min(1, (vp.clientWidth - 60) / w, (vp.clientHeight - 60) / h));
  setZoom(z);
  const left = ((p.l + p.r) / 2) * Z - vp.clientWidth / 2;
  const top = h * Z < vp.clientHeight - 40 ? ((p.t + p.b) / 2) * Z - vp.clientHeight / 2 : p.t * Z - 30;
  vp.scrollTo({left: Math.max(0, left), top: Math.max(0, top), behavior: smooth()});
  el.classList.remove("flash"); void el.offsetWidth; el.classList.add("flash");
}
function renderTeamNav(){
  const nav = $("tnav"), list = $("lane-op") ? (S.opTeams || []) : [];
  nav.hidden = $("tnavSep").hidden = list.length < 2;
  nav.innerHTML = list.length < 2 ? "" : `<span class="lbl">Ir para</span>` +
    [...list].sort((a,b)=>a.team.localeCompare(b.team,"pt-BR")).map(x => `<button class="tchip" data-team="${esc(x.team)}">${esc(x.team)}<span class="n">${x.n}</span></button>`).join("");
}
$("tnav").addEventListener("click", e => { const b = e.target.closest(".tchip"); if (b) focusIsland(b.dataset.team); });

