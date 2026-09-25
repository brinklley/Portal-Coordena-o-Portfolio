/* ---------- visão analítica do roadmap (time + roadmap) ---------- */
const AN = {open:false, sort:"status", dir:1};
const anEnabled = () => !!(S.model && S.f.team && (S.f.exec || S.f.int));
const semLong = s => { const m = /(\d{4})\s*(\d)/.exec(s || ""); return m ? `${m[2]}º semestre ${m[1]}` : (s || ""); };
const semShort = s => { const m = /(\d{4})\s*(\d)/.exec(s || ""); return m ? `${m[2]}S/${m[1].slice(2)}` : "--"; };
const PH_ORDER = {wip:0, discovery:1, backlog:2, vazio:3, fechado:4};
const PH_TXT = {vazio:"Sem itens", backlog:"Backlog", discovery:"Discovery", wip:"WIP", fechado:"Entregue"};
/* dead line: último dia do semestre (menos os dias de congelamento) menos o CT máximo do time */
function semEnd(s){ const m = /(\d{4})\s*(\d)/.exec(s || ""); if (!m) return null; return m[2] === "1" ? new Date(+m[1], 5, 30) : new Date(+m[1], 11, 31); }
function anDeadline(sem, max){
  const end = semEnd(sem); if (!end || !max) return null;
  const opEnd = new Date(end.getFullYear(), end.getMonth(), end.getDate() - (CFG.anFreeze || 0));
  return {end, opEnd, date:new Date(opEnd.getFullYear(), opEnd.getMonth(), opEnd.getDate() - max)};
}
function anTypes(){ return new Set((CFG.ctTypes || []).map(norm)); }
function anData(){
  const M = S.model, V = S.V, team = S.f.team, types = anTypes(), tag = norm(CFG.anTag || "ROADMAP");
  const isType = o => o.type && (!types.size || types.has(norm(o.type)));
  const ops = [...V.visOp].map(k => M.ops.get(k)).filter(o => o.team === team && isType(o));
  const cap = ops.filter(o => o.tags.map(norm).includes(tag)).length;
  const L = limitsOf(team);
  const classKey = norm(CFG.anClassCol || "");
  const rows = [...V.visEpi].map(id => M.epis.get(id)).map(e => {
    const m = epiMetrics(e, team), r = M.rels.get(e.parent), i = M.inis.get(r.parent);
    // coluna mais avançada entre os itens do épico no fluxo do time
    const flow = (M.teamFlow[team] || []).map(norm); let far = -1, farName = "";
    // item aberto mais avançado (os já concluídos não indicam onde o trabalho está)
    m.recs.filter(o => catOf(o) !== "vazao").forEach(o => { const k = flow.indexOf(norm(o.stName)); if (k > far){ far = k; farName = o.stName; } });
    const qtd = m.recs.filter(isType).length;
    const pending = m.recs.filter(o => isType(o) && !o.ready);   // ainda não entraram no fluxo do CT
    const cls = classKey && i.x ? fmtField(classKey, i.x[classKey]) : "--";
    return {e, i, m, qtd, farName, pending, ref: e.interno || i.exec, cls: cls === "--" ? "" : cls};
  });
  const dl = anDeadline(S.f.int || S.f.exec, L.max);
  return {team, ops, cap, proj: ops.length, L, rows, dl};
}
function anSorted(rows){
  const k = AN.sort, d = AN.dir;
  const val = r => k === "qtd" ? r.qtd : k === "ep" ? +r.e.id || 0 : k === "status" ? PH_ORDER[r.m.phase] * 1e4 - (r.m.ct || 0) : k === "ct" ? (r.m.ct ?? -1) : k === "ref" ? (r.ref || "") : 0;
  return [...rows].sort((a, b) => { const x = val(a), y = val(b); return (x > y ? 1 : x < y ? -1 : 0) * d; });
}
function renderAnalytics(){
  const tab = $("anTab"), en = anEnabled();
  tab.disabled = !en;
  tab.title = en ? "Abrir a visão analítica do roadmap do time" : "Selecione um Time e um Roadmap (interno ou executivo) nos filtros para habilitar";
  if (en && !tab.dataset.was){ tab.classList.remove("ready"); void tab.offsetWidth; tab.classList.add("ready"); }
  tab.dataset.was = en ? "1" : "";
  if (!en && AN.open) closeAnalytics();
  if (!AN.open) return;
  const d = anData(), rm = [S.f.int && `roadmap interno ${semLong(S.f.int)}`, S.f.exec && `roadmap executivo ${semLong(S.f.exec)}`].filter(Boolean).join(" · ");
  const over = d.proj > d.cap;
  $("anTitle").innerHTML = `<h2>Roadmap ${esc(d.team)} ${esc(semLong(S.f.int || S.f.exec))}</h2>
    <h3>Entregas previstas: Capacidade ${d.cap} US / Projetada ${over ? `<mark>${d.proj}</mark>` : d.proj} US</h3>
    <div class="an-kpis">
      <div class="an-kpi"><b>${d.L.max ? d.L.max + " DIAS" : "--"}</b><span>CycleTime máximo${d.L.planned ? "" : " (regra geral; o time não tem CT planejado)"}</span></div>
      ${d.dl ? (() => { const left = days(TODAY, d.dl.date);
        return `<div class="an-kpi" title="${esc(`${fmtL(d.dl.opEnd)}${CFG.anFreeze ? ` (fim do semestre ${fmtL(d.dl.end)} menos ${CFG.anFreeze} dias)` : " (fim do semestre)"} menos ${d.L.max} dias de CT máximo`)}"><b class="${left < 0 ? "dl-late" : ""}">${fmtDM(d.dl.date)}</b><span>Dead line para o último item entrar no fluxo${left >= 0 ? ` (faltam ${dd(left)})` : ` (passou há ${dd(-left)})`}</span></div>`; })() : ""}
      <div class="an-kpi"><b>${d.rows.length}</b><span>${d.rows.length === 1 ? "épico" : "épicos"} com itens do time</span></div>
      <div class="an-kpi"><b class="${d.dl && days(TODAY, d.dl.date) < 0 && d.rows.some(r => r.pending.length) ? "dl-late" : ""}">${d.rows.reduce((a, r) => a + r.pending.length, 0)}</b><span>itens ainda fora do fluxo do CT</span></div>
      <div class="an-kpi"><b>${d.rows.filter(r => r.m.phase === "fechado").length}</b><span>entregues</span></div>
      <div class="an-kpi"><b>${d.rows.filter(r => r.m.ct != null && d.L.max && r.m.ct > d.L.max).length}</b><span>acima do CT máximo</span></div>
    </div>`;
  if (!d.rows.length){ $("anBody").innerHTML = `<div class="an-empty">Nenhum épico com itens do time ${esc(d.team)} para os filtros atuais.</div>`; return; }
  const th = (k, lab) => `<th data-sort="${k}" ${AN.sort === k ? `aria-sort="${AN.dir > 0 ? "ascending" : "descending"}"` : ""}>${lab}</th>`;
  const rows = anSorted(d.rows).map(r => {
    const m = r.m, bad = m.ct != null && d.L.max && m.ct > d.L.max;
    return `<tr>
      <td class="c">${r.qtd}<br>${r.qtd === 1 ? "item" : "itens"}</td>
      <td class="ev"><span class="ep">[EP][<button class="idb" data-an-go="${esc(r.e.id)}">${esc(r.e.id)}</button>] ${esc(r.e.title || "")}</span> – <span class="us">${r.qtd} US</span><br>
        [IN][<button class="idi" data-an-go="${esc(r.i.id)}">${esc(r.i.id)}</button>] ${esc(r.i.title)}</td>
      <td class="c">${m.phase === "fechado" ? `<span class="st-ent">Entregue</span>` : PH_TXT[m.phase]}${r.farName && m.phase !== "fechado" ? `<span class="st-sub">${esc(r.farName)}</span>` : ""}</td>
      <td class="c fl">Ready: <b>${m.ctFrom ? fmtDM(m.ctFrom) : "--"}</b><br>Ag. Deploy: <b>${m.ctTo ? fmtDM(m.ctTo) : "--"}</b><br>
        <span class="${bad ? "ct-bad" : "ct-ok"}">CycleTime: ${m.ct ?? "--"} Dias</span>${r.pending.length && d.dl ? (() => { const left = days(TODAY, d.dl.date);
          return `<span class="dl ${left < 0 ? "late" : left <= 14 ? "near" : ""}" title="Itens do épico que ainda não entraram na coluna de entrada do CT">${r.pending.length} ${r.pending.length === 1 ? "item fora" : "itens fora"} do fluxo · entrar até ${fmtDM(d.dl.date)}</span>`; })() : ""}</td>
      <td class="c">${esc(semShort(r.ref))}<br>${esc(r.cls || "---")}</td></tr>`; }).join("");
  $("anBody").innerHTML = `<table class="an-table" id="anTable"><thead><tr>${th("qtd","QTD")}${th("ep","Evolução")}${th("status","Status")}${th("ct","Flow")}${th("ref","Ref.")}</tr></thead><tbody>${rows}</tbody></table>
    <div class="an-note">Épicos com itens do time ${esc(d.team)} dentro dos filtros atuais (${esc(rm)}). QTD, Capacidade e Projetada contam itens dos tipos ${esc(ctTypesLabel())}; Capacidade só os com a tag ${esc(CFG.anTag || "ROADMAP")}. Status e Flow seguem a configuração do fluxo do time; CycleTime em vermelho passa do CT máximo. Dead line = fim do semestre${CFG.anFreeze ? ` menos ${CFG.anFreeze} dias` : ""} menos o CT máximo; “itens fora do fluxo” ainda não chegaram na coluna de entrada do CT. Ref.: roadmap interno do épico (ou o executivo da iniciativa, se vazio) e ${esc(CFG.anClassCol || "classificação")} da iniciativa.</div>`;
}
const fmtDM = d => d ? d.toLocaleDateString("pt-BR", {day:"2-digit", month:"short"}).replace(".", "").replace(" de ", "/").toUpperCase() : "--";
function placeAnalytics(){ const h = document.querySelector(".top").offsetHeight; $("anPanel").style.top = h + "px"; $("anPanel").style.height = `calc(100% - ${h}px)`; }
function openAnalytics(){ if (!anEnabled()) return; AN.open = true; placeAnalytics(); $("anPanel").classList.add("open"); $("anPanel").setAttribute("aria-hidden","false"); $("anTab").setAttribute("aria-expanded","true"); renderAnalytics(); $("anClose").focus(); }
function closeAnalytics(){ AN.open = false; $("anPanel").classList.remove("open"); $("anPanel").setAttribute("aria-hidden","true"); $("anTab").setAttribute("aria-expanded","false"); }
$("anTab").onclick = openAnalytics;
$("anClose").onclick = () => { closeAnalytics(); $("anTab").focus(); };
window.addEventListener("resize", () => { if (AN.open) placeAnalytics(); });
$("anPanel").addEventListener("click", e => {
  const th = e.target.closest("th[data-sort]");
  if (th){ const k = th.dataset.sort; AN.dir = AN.sort === k ? -AN.dir : 1; AN.sort = k; renderAnalytics(); return; }
  const g = e.target.closest("[data-an-go]");
  if (g){ closeAnalytics(); $("goto").value = g.dataset.anGo; gotoId(g.dataset.anGo); }
});
$("anPanel").addEventListener("keydown", e => { if (e.key === "Escape"){ e.stopPropagation(); closeAnalytics(); $("anTab").focus(); } });
$("anCopy").onclick = () => {
  const tb = $("anTable"); if (!tb) return;
  const box = document.createElement("div"); box.style.cssText = "position:fixed;left:-9999px;top:0";
  box.innerHTML = $("anTitle").querySelector("h2").outerHTML + $("anTitle").querySelector("h3").outerHTML + tb.outerHTML;
  box.querySelectorAll("button").forEach(b => { const s = document.createElement("span"); s.textContent = b.textContent; s.style.cssText = b.classList.contains("idb") ? "background:#22C55E;padding:0 3px;font-weight:bold" : ""; b.replaceWith(s); });
  box.querySelectorAll("th").forEach(x => x.style.cssText = "background:#111;color:#fff;padding:8px;border:1px solid #fff");
  box.querySelectorAll("td").forEach((x, i) => x.style.cssText = "background:#E8E8E8;padding:8px;border:1px solid #fff;vertical-align:middle");
  box.querySelectorAll(".us").forEach(x => x.style.cssText = "background:#FDE047;font-weight:bold");
  box.querySelectorAll(".ct-bad").forEach(x => x.style.cssText = "color:#DC2626;font-weight:bold");
  box.querySelectorAll(".ct-ok").forEach(x => x.style.cssText = "color:#1D47C9;font-weight:bold");
  document.body.appendChild(box);
  const rg = document.createRange(); rg.selectNodeContents(box); const sel = getSelection(); sel.removeAllRanges(); sel.addRange(rg);
  let ok = false; try { ok = document.execCommand("copy"); } catch(_){}
  sel.removeAllRanges(); box.remove();
  toast(ok ? "Tabela copiada. Cole no PowerPoint, Excel ou e-mail." : "Não foi possível copiar automaticamente; selecione a tabela e use Ctrl+C.");
};

function placeDrawer(){ const h = document.querySelector(".top").offsetHeight; $("drawer").style.top = h + "px"; $("drawer").style.height = `calc(100% - ${h}px)`; }
window.addEventListener("resize", placeDrawer);
function openDrawer(){ placeDrawer(); $("drawer").classList.add("open"); $("drawer").setAttribute("aria-hidden","false"); document.body.classList.add("with-drawer"); redraw(); }
function closeDrawer(){ S.detailKey = null; $("drawer").classList.remove("open"); $("drawer").setAttribute("aria-hidden","true"); document.body.classList.remove("with-drawer"); redraw(); }
$("dClose").onclick = closeDrawer;
document.addEventListener("keydown", e => { if (e.key === "Escape") closeDrawer(); });

