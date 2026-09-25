/* ---------- Report F4P (Business Outcomes – Productivity) ---------- */
/* Painel lateral com o mesmo comportamento da Visão analítica (docs/backlog/report-f4p.md).
   Quadrantes 1 (CycleTime) e 2 (Variabilidade) têm regra fechada; os demais aguardam definição
   e aparecem como "em definição". Ícones abaixo são ilustrações originais (inline SVG, sem
   dependências externas), inspiradas no slide de referência, não uma cópia dele. */
const F4P = {open:false};
const F4P_ICONS = {
  range: `<svg viewBox="0 0 40 16" width="30" height="12" aria-hidden="true"><rect x="1" y="6" width="38" height="4" rx="2" fill="#4B5A66"/><rect x="13" y="6" width="14" height="4" rx="2" fill="#3FB27F"/><circle cx="20" cy="8" r="5" fill="#fff"/></svg>`,
  dial: `<svg viewBox="0 0 36 20" width="28" height="16" aria-hidden="true"><path d="M2 18 A16 16 0 0 1 10 4.14" stroke="#B9352B" stroke-width="4" fill="none" stroke-linecap="round"/><path d="M10 4.14 A16 16 0 0 1 26 4.14" stroke="#3FB27F" stroke-width="4" fill="none" stroke-linecap="round"/><path d="M26 4.14 A16 16 0 0 1 34 18" stroke="#C98712" stroke-width="4" fill="none" stroke-linecap="round"/><line x1="18" y1="18" x2="14" y2="6.5" stroke="#fff" stroke-width="2" stroke-linecap="round"/><circle cx="18" cy="18" r="2" fill="#fff"/></svg>`,
  target: `<svg viewBox="0 0 20 20" width="16" height="16" aria-hidden="true"><circle cx="10" cy="10" r="8" fill="none" stroke="#9FB0DD" stroke-width="1.6"/><circle cx="10" cy="10" r="4.5" fill="none" stroke="#9FB0DD" stroke-width="1.6"/><circle cx="10" cy="10" r="1.6" fill="#fff"/></svg>`,
  net: `<svg viewBox="0 0 22 18" width="18" height="14" aria-hidden="true"><circle cx="4" cy="4" r="2.4" fill="#6FC1E8"/><circle cx="18" cy="4" r="2.4" fill="#6FC1E8"/><circle cx="11" cy="14" r="2.4" fill="#6FC1E8"/><line x1="6" y1="5.4" x2="16" y2="5.4" stroke="#8593A0" stroke-width="1.4"/><line x1="5.4" y1="6" x2="10" y2="12" stroke="#8593A0" stroke-width="1.4"/><line x1="16.6" y1="6" x2="12" y2="12" stroke="#8593A0" stroke-width="1.4"/></svg>`};
/* ordem e layout: 2 colunas, igual ao slide de referência */
const F4P_QUADS = {
  var:   {title:"Variabilidade (min vs atual vs max)", icon:"range", side:"l", done:true},
  eff:   {title:"Eficiência de fluxo (min vs atual vs max)", icon:"range", side:"l", done:false, goal:"Meta mínima 30%"},
  road:  {title:"Roadmap – Épicos (reserva vs roadmap entregue vs atual)", icon:"target", side:"l", done:false},
  vazao: {title:"Vazão (reserva vs realizado)", icon:"target", side:"l", done:false},
  ct:    {title:"CycleTime (reserva vs atual)", icon:"dial", side:"r", done:true},
  urg:   {title:"Urgente (meta vs realizado)", icon:"net", side:"r", done:false},
  ts:    {title:"Technical Story (meta vs realizado)", icon:"net", side:"r", done:false},
  us:    {title:"User Story (planejado vs não planejado)", icon:"net", side:"r", done:false}};
const F4P_ORDER = ["var", "eff", "road", "vazao", "ct", "urg", "ts", "us"];

/* time é lido dos dados carregados (todos, não só o filtrado): a mesma lista que aparece nas colunas do quadro */
function f4pTeams(){ return S.model ? [...S.model.teams] : []; }
function f4pTypes(){ return new Set((CFG.f4p.types || []).map(norm)); }
/* amostra: itens concluídos (com data de saída do CT) dos tipos configurados, saída nos últimos N meses, de todos os itens do time */
function f4pSample(team){
  const types = f4pTypes(), months = CFG.f4p.months || 6;
  const cutoff = new Date(TODAY.getFullYear(), TODAY.getMonth() - months, TODAY.getDate());
  return [...S.model.ops.values()].filter(o => o.team === team && o.type && types.has(norm(o.type)) && o.deploy && o.ct != null && o.deploy >= cutoff);
}
function f4pMetrics(team){
  const cts = f4pSample(team).map(o => o.ct).sort((a, b) => a - b), n = cts.length;
  const p95 = n ? percentil(cts, .95) : null, p50 = n ? percentil(cts, .5) : null;
  return {n, p95, p50, varr: (p50 > 0) ? p95 / p50 : null};
}
function f4pCtCell(team){
  const L = limitsOf(team), m = f4pMetrics(team);
  const tip = `Amostra: ${m.n} ${m.n === 1 ? "item" : "itens"} concluídos nos últimos ${CFG.f4p.months || 6} meses${m.n ? ` · P50 ${dec1(m.p50)} dias` : ""}${L.planned ? "" : " · time sem CT máximo planejado (usando o limite geral)"}`;
  if (m.p95 == null) return `<span title="${esc(tip)}"><span class="f4p-lo">${L.max}</span><span class="f4p-sep">|</span><span class="f4p-dash">--</span></span>`;
  const bad = L.max && m.p95 > L.max, arrow = bad ? "▼" : "▲", cls = bad ? "f4p-bad" : "f4p-good";
  return `<span title="${esc(tip)}"><span class="f4p-lo">${L.max}</span><span class="f4p-sep">|</span><b class="${cls}">${Math.round(m.p95)} ${arrow}</b></span>`;
}
function f4pVarCell(team){
  const R = f4pRangeOf(team), m = f4pMetrics(team);
  const tip = `Amostra: ${m.n} ${m.n === 1 ? "item" : "itens"}${m.n ? ` · P95 ${dec1(m.p95)} / P50 ${dec1(m.p50)} dias` : ""}`;
  if (m.varr == null) return `<span title="${esc(tip)}"><span class="f4p-lo">${dec1(R.min)}</span><span class="f4p-sep">|</span><span class="f4p-dash">--</span><span class="f4p-sep">|</span><span class="f4p-hi">${dec1(R.max)}</span></span>`;
  const bad = m.varr > R.max, low = m.varr < R.min, cls = bad ? "f4p-bad" : low ? "f4p-warn" : "f4p-good", arrow = (bad || low) ? "▼" : "▲";
  return `<span title="${esc(tip)}"><span class="f4p-lo">${dec1(R.min)}</span><span class="f4p-sep">|</span><b class="${cls}">${dec1(m.varr)} ${arrow}</b><span class="f4p-sep">|</span><span class="f4p-hi">${dec1(R.max)}</span></span>`;
}
const F4P_CELL = {var: f4pVarCell, ct: f4pCtCell};
function f4pCard(id, teams){
  const q = F4P_QUADS[id];
  const head = `<div class="f4p-card-h"><span class="f4p-ic">${F4P_ICONS[q.icon]}</span>${esc(q.title)}</div>${q.goal ? `<div class="f4p-goal">${esc(q.goal)}</div>` : ""}`;
  const thead = `<thead><tr>${teams.map(t => `<th>${esc(t)}</th>`).join("")}</tr></thead>`;
  if (!q.done) return `<div class="f4p-card">${head}<table class="f4p-tbl">${thead}
    <tbody><tr>${teams.map(() => `<td class="f4p-dash">--</td>`).join("")}</tr></tbody></table>
    <div class="f4p-note">Regra de cálculo ainda em definição.</div></div>`;
  return `<div class="f4p-card">${head}<table class="f4p-tbl">${thead}
    <tbody><tr>${teams.map(t => `<td>${F4P_CELL[id](t)}</td>`).join("")}</tr></tbody></table></div>`;
}
function f4pEnabled(){ return anEnabled(); }
function renderF4P(){
  const tab = $("f4pTab"), en = f4pEnabled();
  tab.disabled = !en;
  tab.title = en ? "Abrir o Report F4P (Business Outcomes – Productivity)" : "Selecione um Time e um Roadmap (interno ou executivo) nos filtros para habilitar";
  if (en && !tab.dataset.was){ tab.classList.remove("ready"); void tab.offsetWidth; tab.classList.add("ready"); }
  tab.dataset.was = en ? "1" : "";
  if (!en && F4P.open) closeF4P();
  if (!F4P.open) return;
  const teams = f4pTeams();
  $("f4pTitle").innerHTML = `<h2>Report F4P <span class="f4p-sem">Business Outcomes – Productivity</span></h2><h3>${esc(semLong(S.f.int || S.f.exec))}</h3>`;
  if (!teams.length){ $("f4pBody").innerHTML = `<div class="an-empty">Nenhum time carregado para calcular o relatório.</div>`; return; }
  const left = F4P_ORDER.filter(id => F4P_QUADS[id].side === "l"), right = F4P_ORDER.filter(id => F4P_QUADS[id].side === "r");
  $("f4pBody").innerHTML = `<div class="f4p-grid">
      <div class="f4p-col">${left.map(id => f4pCard(id, teams)).join("")}</div>
      <div class="f4p-col">${right.map(id => f4pCard(id, teams)).join("")}</div>
    </div>
    <div class="an-note">Mostra sempre todos os times carregados (${esc(teams.join(", "))}), mesmo com um time diferente selecionado no filtro — o filtro só habilita o acesso a este painel. CycleTime e Variabilidade usam itens dos tipos ${esc((CFG.f4p.types || []).join(", ") || "nenhum tipo marcado")} concluídos nos últimos ${CFG.f4p.months || 6} meses. Os demais quadrantes aguardam a definição da regra de cálculo.</div>`;
}
function placeF4P(){ const h = document.querySelector(".top").offsetHeight; $("f4pPanel").style.top = h + "px"; $("f4pPanel").style.height = `calc(100% - ${h}px)`; }
function openF4P(){ if (!f4pEnabled()) return; if (AN.open) closeAnalytics(); F4P.open = true; placeF4P(); $("f4pPanel").classList.add("open"); $("f4pPanel").setAttribute("aria-hidden","false"); $("f4pTab").setAttribute("aria-expanded","true"); renderF4P(); $("f4pClose").focus(); }
function closeF4P(){ F4P.open = false; $("f4pPanel").classList.remove("open"); $("f4pPanel").setAttribute("aria-hidden","true"); $("f4pTab").setAttribute("aria-expanded","false"); }
$("f4pTab").onclick = openF4P;
$("f4pClose").onclick = () => { closeF4P(); $("f4pTab").focus(); };
window.addEventListener("resize", () => { if (F4P.open) placeF4P(); });
$("f4pPanel").addEventListener("keydown", e => { if (e.key === "Escape"){ e.stopPropagation(); closeF4P(); $("f4pTab").focus(); } });
