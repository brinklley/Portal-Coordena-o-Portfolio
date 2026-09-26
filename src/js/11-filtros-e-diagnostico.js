/* ---------- filtros ativos ---------- */
const FILTER_LABEL = {exec:"Roadmap executivo", owners:"Responsável da iniciativa", int:"Roadmap interno", team:"Time", ini:"Iniciativa (ID ou nome)"};
function activeFilters(){
  const f = S.f, out = [];
  if (f.exec) out.push(["exec", f.exec]);
  if (f.owners && f.owners.size){ const names = (S.ownerList || []).filter(o => f.owners.has(o.k)).map(o => o.label.replace(/\s*-\s*Unicred.*$/i, ""));
    out.push(["owners", names.length > 2 ? `${names.slice(0,2).join(", ")} e mais ${names.length - 2}` : names.join(", ")]); }
  if (f.int) out.push(["int", f.int]);
  if (f.team) out.push(["team", f.team]);
  if (f.ini && f.ini.trim()) out.push(["ini", f.ini.trim()]);
  return out;
}
function markActiveFilters(){
  const f = S.f;
  $("fExec").classList.toggle("active", !!f.exec); $("fInt").classList.toggle("active", !!f.int);
  $("fTeam").classList.toggle("active", !!f.team); $("fIni").classList.toggle("active", !!(f.ini && f.ini.trim()));
  const n = activeFilters().length;
  $("btnClearF").disabled = !n; $("nFilters").textContent = n || "";
}
function clearFilters(){
  S.f = {exec:"", owners:new Set(), int:"", team:"", ini:""};
  $("fExec").value = ""; $("fInt").value = ""; $("fTeam").value = ""; $("fIni").value = "";
  msLabel(); render();
}
$("btnClearF").onclick = () => { clearFilters(); hideFmsg(); toast("Filtros removidos."); };
/* quais filtros escondem um caminho: testa removendo um filtro por vez */
function pathVisible(V, path, opKey){
  return V.visIni.has(path.ini) && (!path.rel || V.visRel.has(path.rel)) && (!path.epi || V.visEpi.has(path.epi)) && (!opKey || V.visOp.has(opKey));
}
function blockingFilters(path, opKey){
  const act = activeFilters(), saved = S.f, res = [];
  act.forEach(([k]) => {
    S.f = {...saved, owners:new Set(saved.owners)};
    if (k === "owners") S.f.owners = new Set(); else S.f[k] = "";
    if (pathVisible(computeVisible(), path, opKey)) res.push(k);
  });
  S.f = saved;
  return res;
}
/* aviso ancorado logo abaixo de um campo */
let fmsgT = 0;
function showFmsg(anchor, html, kind){
  const m = $("fmsg"), r = anchor.getBoundingClientRect();
  m.dataset.src = /data-diag/.test(html) && !/fmGo/.test(html) ? "diag" : "goto";
  m.className = "fmsg" + (kind === "info" ? " info" : ""); m.innerHTML = `<button class="x" aria-label="Fechar aviso">×</button>` + html; m.hidden = false;
  const w = m.offsetWidth, left = Math.max(12, Math.min(r.left, innerWidth - w - 12));
  m.style.left = left + "px"; m.style.top = (r.bottom + 9) + "px";
  m.style.setProperty("--ax", Math.max(14, Math.min(w - 26, r.left + 24 - left)) + "px");
  m.querySelector(".x").onclick = hideFmsg;
  clearTimeout(fmsgT); fmsgT = setTimeout(hideFmsg, 15000);
}
function hideFmsg(){ $("fmsg").hidden = true; clearTimeout(fmsgT); }
document.addEventListener("pointerdown", e => { if (!$("fmsg").hidden && !e.target.closest("#fmsg,#goto,.filters")) hideFmsg(); });
window.addEventListener("resize", hideFmsg);
$("goto").addEventListener("input", hideFmsg);

/* ---------- por que os filtros não trouxeram nada ---------- */
const FILTER_EL = {exec:"fExec", owners:"fOwner", int:"fInt", team:"fTeam", ini:"fIni"};
function withFilters(patch, fn){
  const saved = S.f; S.f = {...saved, owners:new Set(saved.owners), ...patch};
  try { return fn(); } finally { S.f = saved; }
}
/* filtro de Time: times com dados + times cadastrados como fonte (marcados "sem carga"); mantém a seleção */
function fillTeamFilter(){
  const sel = $("fTeam"), cur = sel.value;
  sel.innerHTML = `<option value="">Todos os times</option>` + cfgTeams(CFG, true).map(tm => `<option value="${esc(tm)}">${esc(tm)}${hasData(tm) ? "" : " (sem carga)"}</option>`).join("");
  sel.value = [...sel.options].some(o => o.value === cur) ? cur : "";
  if (sel.value !== cur){ S.f.team = ""; }
}
function diagnoseEmpty(){
  const M = S.model, act = activeFilters(), res = {items:[], hint:null};
  act.forEach(([k, v]) => res.items.push({k, v, n: withFilters(k === "owners" ? {owners:new Set()} : {[k]:""}, () => computeVisible().visIni.size)}));
  const q = (S.f.ini || "").trim();
  if (q){
    const id = nid(q), op = [...M.ops.values()].find(o => o.id === id);
    if (M.inis.has(id)){
      const i = M.inis.get(id);
      const onlyBare = !i.rels.some(rid => S.model.rels.get(rid).epis.length);
      if (!i.valid) res.hint = {kind:"invalid", id, title:i.title};
      else if (!iniCanAppear(i) || (!S.showBare && onlyBare)) res.hint = {kind:"rule", id, title:i.title, off: iniCanAppear(i) && !S.showBare};
      else {
        const blk = [];
        act.filter(([k]) => k !== "ini").forEach(([k, v]) => { if (withFilters({ini:q, ...(k === "owners" ? {owners:new Set()} : {[k]:""})}, () => computeVisible().visIni.has(id))) blk.push([k, v]); });
        res.hint = {kind:"hidden", id, title:i.title, owner:i.owner, exec:i.exec, blk};
      }
    }
    else if (M.rels.has(id)) res.hint = {kind:"other", id, what:"uma release", title:M.rels.get(id).title};
    else if (M.epis.has(id)) res.hint = {kind:"other", id, what:"um épico", title:M.epis.get(id).title};
    else if (op) res.hint = {kind:"other", id, what:`um item do time ${op.team}`, title:op.title};
    else if (/^\d+$/.test(q)) res.hint = {kind:"none", id:q};
    else if (![...M.inis.values()].some(i => i.valid && norm(i.title).includes(norm(q)))) res.hint = {kind:"notext", q};
  }
  return res;
}
function diagHtml(d){
  if (S.f.team && !hasData(S.f.team))
    return `<b>O time ${esc(S.f.team)} ainda não tem dados carregados.</b><p style="margin:6px 0 0">Ele está cadastrado como fonte do Azure DevOps, mas a última carga não trouxe os itens dele. Faça uma nova carga para ele aparecer no quadro.</p>
      <div class="acts"><button class="btn primary" data-diag="azload">Carregar do Azure DevOps</button><button class="btn" data-diag="rm:team">Remover filtro Time</button></div>`;
  let h = `<b>Nenhuma iniciativa com os filtros ativos.</b>`;
  const x = d.hint;
  if (x){
    if (x.kind === "other") h += `<p style="margin:6px 0 0"><b>${esc(x.id)}</b> não é uma iniciativa: é ${x.what} (“${esc(x.title)}”). O campo “Iniciativa” busca só iniciativas; para achar qualquer ID, use “Ir para qualquer ID”.</p>`;
    else if (x.kind === "rule") h += `<p style="margin:6px 0 0">A iniciativa <b>#${esc(x.id)}</b> (“${esc(x.title)}”) existe, mas ${x.off ? "não tem desdobramento completo e a opção “Mostrar itens sem desdobramento” está desligada" : "fica fora do quadro por uma regra de exibição (por exemplo, concluída sem release)"}.</p>`;
    else if (x.kind === "invalid") h += `<p style="margin:6px 0 0">A iniciativa <b>#${esc(x.id)}</b> (“${esc(x.title)}”) existe, mas não aparece no quadro porque não tem nenhuma release com épico válido vinculado.</p>`;
    else if (x.kind === "hidden") h += `<p style="margin:6px 0 0">A iniciativa <b>#${esc(x.id)}</b> (“${esc(x.title)}”) existe${x.blk.length ? `, mas ${x.blk.map(([k, v]) => k === "owners" ? `o responsável dela é <b>${esc(x.owner || "(sem responsável)")}</b>, fora do filtro de responsável` : k === "exec" ? `o roadmap executivo dela é <b>${esc(x.exec || "--")}</b>` : `o filtro <b>${FILTER_LABEL[k]}: ${esc(v)}</b> a esconde`).join("; e ")}` : ", mas a combinação dos filtros a esconde"}.</p>`;
    else if (x.kind === "none") h += `<p style="margin:6px 0 0">Não existe nenhum registro com o ID <b>${esc(x.id)}</b> na planilha carregada.</p>`;
    else if (x.kind === "notext") h += `<p style="margin:6px 0 0">Nenhuma iniciativa tem “<b>${esc(x.q)}</b>” no nome ou no ID, mesmo sem os outros filtros.</p>`;
  }
  const useful = d.items.filter(i => i.n > 0);
  if (useful.length) h += `<p style="margin:8px 0 2px">Removendo um filtro:</p><ul style="margin-top:2px">${useful.map(i => `<li>sem o filtro <b>${FILTER_LABEL[i.k]}</b> = “${esc(i.v)}”: ${i.n === 1 ? "aparece 1 iniciativa" : `aparecem ${i.n} iniciativas`}</li>`).join("")}</ul>`;
  else if (d.items.length > 1) h += `<p style="margin:8px 0 0">Nenhum filtro sozinho explica o resultado: é a combinação deles.</p>`;
  const acts = [];
  if (x && x.kind === "other") acts.push(`<button class="btn primary" data-diag="goto:${esc(x.id)}">Ir para #${esc(x.id)}</button>`);
  if (x && x.kind === "hidden" && x.blk.length) acts.push(`<button class="btn primary" data-diag="show:${esc(x.id)}">Remover ${x.blk.length === 1 ? "esse filtro" : "esses filtros"} e mostrar #${esc(x.id)}</button>`);
  if (x && x.kind === "invalid") acts.push(`<button class="btn" data-diag="hyg">Abrir Higiene de dados</button>`);
  if (x && x.kind === "rule") acts.push(`<button class="btn primary" data-investigate="${esc(x.id)}">Investigar</button>`);
  if (!acts.length) useful.slice(0, 2).forEach(i => acts.push(`<button class="btn" data-diag="rm:${i.k}">Remover filtro ${FILTER_LABEL[i.k]}</button>`));
  acts.push(`<button class="btn" data-diag="clear">Limpar todos os filtros</button>`);
  return h + `<div class="acts">${acts.join("")}</div>`;
}
function removeFilter(k){
  if (k === "owners") S.f.owners = new Set(); else S.f[k] = "";
  if (k !== "owners") $(FILTER_EL[k]).value = "";
  msLabel();
}
document.addEventListener("click", e => {
  const b = e.target.closest("[data-diag]"); if (!b) return;
  const [a, arg] = b.dataset.diag.split(":"); hideFmsg();
  if (a === "clear"){ clearFilters(); return; }
  if (a === "rm"){ removeFilter(arg); S.lastFilterEl = $(FILTER_EL[arg]); render(); return; }
  if (a === "goto"){ removeFilter("ini"); render(); $("goto").value = arg; gotoId(arg); return; }
  if (a === "show"){ const d = S.emptyDiag; (d && d.hint && d.hint.blk || []).forEach(([k]) => removeFilter(k)); render(); return; }
  if (a === "hyg"){ $("btnHygiene").click(); }
  if (a === "azload"){ $("btnAz").click(); }
});

