/* ---------- Report F4P (Business Outcomes – Productivity) ---------- */
/* Painel lateral com o mesmo comportamento da Visão analítica (docs/backlog/report-f4p.md).
   Quadrantes 1 (CycleTime), 2 (Variabilidade), 3 (Urgente) e 4 (Technical Story) têm regra fechada; os
   demais aguardam definição e aparecem como "em definição". As ilustrações (selo de cada grupo e o logo do
   cabeçalho) são as imagens fornecidas pelo usuário a partir do slide de referência, embutidas em
   base64 pelo build (F4P_ASSETS, gerado por scripts/build.mjs a partir de src/assets/f4p/*.png). */
const F4P = {open:false};
const F4P_QUADS = {
  var:   {title:"Variabilidade (min vs atual vs max)", side:"l", done:true},
  eff:   {title:"Eficiência de fluxo (min vs atual vs max)", side:"l", done:false, goal:"Meta mínima 30%"},
  road:  {title:"Roadmap – Épicos (reserva vs roadmap entregue vs atual)", side:"l", done:false},
  vazao: {title:"Vazão (reserva vs realizado)", side:"l", done:false},
  ct:    {title:"CycleTime (reserva vs atual)", side:"r", done:true},
  urg:   {title:"Urgente (meta vs realizado)", side:"r", done:true},
  ts:    {title:"Technical Story (meta vs realizado)", side:"r", done:true},
  us:    {title:"User Story (planejado vs não planejado)", side:"r", done:false}};
/* selo (imagem) por grupo de quadrantes, na ordem de exibição de cada coluna */
const F4P_GROUPS = [
  {side:"l", badge:"healthyRange",     alt:"Healthy range", quads:["var", "eff"]},
  {side:"l", badge:"targetTemporary",  alt:"Have a target & are temporary", quads:["road", "vazao"]},
  {side:"r", badge:"fitnessCriteria",  alt:"Fitness Criteria · KPIs", quads:["ct"]},
  {side:"r", badge:"vanityMetrics",    alt:"Vanity Metrics", quads:["urg", "ts", "us"]}];

/* time é lido dos dados carregados (todos, não só o filtrado): a mesma lista que aparece nas colunas do quadro */
function f4pTeams(){ return S.model ? [...S.model.teams] : []; }
function f4pTypes(){ return new Set((CFG.f4p.types || []).map(norm)); }
const f4pSemStart = s => { const m = /(\d{4})\s*(\d)/.exec(s || ""); return m ? new Date(+m[1], m[2] === "1" ? 0 : 6, 1) : null; };
/* semestre selecionado no filtro (interno tem prioridade sobre o executivo, igual ao cabeçalho do painel) e o que ele significa
   para a amostra: "current" (em curso) usa os últimos N meses a partir de hoje; "past" (já fechado) usa as datas do próprio
   semestre; "future" (ainda não começou) não tem dados possíveis, então o relatório fica desabilitado. */
function f4pSemester(){ return S.f.int || S.f.exec || ""; }
function f4pSemesterState(){
  const sem = f4pSemester(), start = f4pSemStart(sem), end = semEnd(sem);
  if (!start || !end) return {kind:"current", start:null, end:null};
  if (start > TODAY) return {kind:"future", start, end};
  if (end < TODAY) return {kind:"past", start, end};
  return {kind:"current", start, end};
}
/* Janela de datas padrão de qualquer amostra do Report F4P que dependa do semestre selecionado (regra
   geral, decisão 0013 — vale para todo quadrante calculado, não só CycleTime/Variabilidade; reaproveite
   esta função em vez de recriar a janela). Semestre em curso ou nenhum reconhecido: últimos N meses
   corridos a partir de hoje. Semestre já encerrado: o período exato daquele semestre. */
function f4pWindow(st){
  st = st || f4pSemesterState();
  const months = CFG.f4p.months || 6;
  const from = st.kind === "past" ? st.start : new Date(TODAY.getFullYear(), TODAY.getMonth() - months, TODAY.getDate());
  const to = st.kind === "past" ? st.end : TODAY;
  return {from, to};
}
/* amostra: itens concluídos (com data de saída do CT) dos tipos configurados, de todos os itens do time,
   dentro da janela de f4pWindow. */
function f4pSample(team, st){
  st = st || f4pSemesterState();
  const types = f4pTypes(), {from, to} = f4pWindow(st);
  return [...S.model.ops.values()].filter(o => o.team === team && o.type && types.has(norm(o.type)) && o.deploy && o.ct != null && o.deploy >= from && o.deploy <= to);
}
function f4pPeriodLabel(st){
  st = st || f4pSemesterState();
  return st.kind === "past" ? `${fmtL(st.start)} a ${fmtL(st.end)}` : `últimos ${CFG.f4p.months || 6} meses`;
}
function f4pMetrics(team){
  const st = f4pSemesterState();
  const cts = f4pSample(team, st).map(o => o.ct).sort((a, b) => a - b), n = cts.length;
  const p95 = n ? percentil(cts, .95) : null, p50 = n ? percentil(cts, .5) : null;
  return {n, p95, p50, varr: (p50 > 0) ? p95 / p50 : null};
}
function f4pCtCell(team){
  const L = limitsOf(team), m = f4pMetrics(team);
  const tip = `Amostra: ${m.n} ${m.n === 1 ? "item" : "itens"} concluídos (${f4pPeriodLabel()})${m.n ? ` · P50 ${dec1(m.p50)} dias` : ""}${L.planned ? "" : " · time sem CT máximo planejado (usando o limite geral)"}`;
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
/* itens do time com a tag Expedite/Urgente configurada, de qualquer tipo */
function f4pExpediteOps(team){
  const tag = f4pExpediteTag();
  return [...S.model.ops.values()].filter(o => o.team === team && (o.tagHits || []).some(t => t.id === tag));
}
/* itens do time do tipo Technical Story (Report F4P, Quadrante 4) */
function f4pTsOps(team){
  return [...S.model.ops.values()].filter(o => o.team === team && norm(o.type) === "technical story");
}
/* Janela por período exato do semestre — diferente de f4pWindow (CycleTime/Variabilidade, janela rolante
   de N meses no semestre em curso). Usada por quadrantes cuja meta é "por semestre" (não uma amostra
   geral): sempre 1/jan a 30/jun ou 1/jul a 31/dez, esteja o semestre em curso ou já encerrado. Criada para
   o Urgente depois que a janela rolante "vazou" itens fechados ainda no semestre anterior (decisão 0017)
   e reaproveitada pelo Technical Story (decisão 0018) pela mesma razão. Sem semestre reconhecido no
   filtro, cai na janela rolante de f4pWindow por segurança (mesmo padrão do resto do Report F4P nesse
   caso extremo). */
function f4pExactSemesterWindow(st){
  st = st || f4pSemesterState();
  return (st.start && st.end) ? {from: st.start, to: st.end} : f4pWindow(st);
}
function f4pExactSemesterLabel(st){
  const {from, to} = f4pExactSemesterWindow(st);
  return `${fmtL(from)} a ${fmtL(to)}`;
}
/* Itens que entram no Realizado de um quadrante "meta por semestre" (Urgente, Technical Story): abertos
   contam sempre (não importa desde quando — ainda estão em aberto, logo ainda são risco/trabalho agora).
   Fechados só contam dentro de f4pExactSemesterWindow — sem isso, a contagem somaria todo item já
   qualificado em qualquer momento da história do time, não só o deste período (o portal não guarda
   histórico de quando a tag foi aplicada ou o item virou Technical Story, só a data de fechamento). */
function f4pSemesterGoalItems(ops, st){
  st = st || f4pSemesterState();
  const {from, to} = f4pExactSemesterWindow(st);
  return ops.filter(o => (st.kind !== "past" && !o.deploy) || (o.deploy && o.deploy >= from && o.deploy <= to));
}
function f4pUrgentItems(team, st){ return f4pSemesterGoalItems(f4pExpediteOps(team), st); }
function f4pUrgentRealizado(team, st){ return f4pUrgentItems(team, st).length; }
function f4pTsItems(team, st){ return f4pSemesterGoalItems(f4pTsOps(team), st); }
function f4pTsRealizado(team, st){ return f4pTsItems(team, st).length; }
/* Tendência: itens Expedite fechados nos últimos 3 meses vs. nos 3 meses antes desses — sempre a
   partir de hoje, independente do semestre selecionado no filtro. Sem margem de tolerância: mais → ▲,
   menos → ▼, igual → ◆. */
function f4pUrgentTrend(team){
  const d3 = new Date(TODAY.getFullYear(), TODAY.getMonth() - 3, TODAY.getDate());
  const d6 = new Date(TODAY.getFullYear(), TODAY.getMonth() - 6, TODAY.getDate());
  const fechados = f4pExpediteOps(team).filter(o => o.deploy);
  const recente = fechados.filter(o => o.deploy > d3 && o.deploy <= TODAY).length;
  const anterior = fechados.filter(o => o.deploy > d6 && o.deploy <= d3).length;
  return recente > anterior ? "▲" : recente < anterior ? "▼" : "◆";
}
function f4pUrgentCell(team){
  const st = f4pSemesterState(), meta = f4pUrgentMetaOf(team), items = f4pUrgentItems(team, st), realizado = items.length, trend = f4pUrgentTrend(team);
  const cls = meta == null ? "" : realizado > meta ? "f4p-bad" : "f4p-good";
  const tip = `Tag: ${f4pTagName(f4pExpediteTag())} · itens abertos (qualquer data) + fechados em ${f4pExactSemesterLabel(st)} · tendência: fechados nos últimos 3 meses vs. nos 3 meses anteriores${meta == null ? " · time sem meta cadastrada" : ""} · clique no número para ver os itens`;
  return `<span title="${esc(tip)}"><span class="f4p-lo">${meta ?? "--"}</span><span class="f4p-sep">|</span><button type="button" class="f4p-real ${cls}" data-f4p-urgent-team="${esc(team)}">${realizado}</button> <span class="f4p-trend">${trend}</span></span>`;
}
/* Quadrante 4 · Technical Story: mesmo comportamento do Urgente (janela por período exato do semestre,
   cor vermelho/verde pela meta, clique no número abre a lista dos itens), mas conta itens pelo tipo
   "Technical Story" em vez de uma tag, e a meta tem padrão (6) em vez de ficar "sem meta" quando o time
   não cadastra a própria (decisão 0018). Sem seta de tendência: o usuário não pediu uma para este
   quadrante. */
function f4pTsCell(team){
  const st = f4pSemesterState(), meta = f4pTsMetaOf(team), items = f4pTsItems(team, st), realizado = items.length;
  const cls = realizado > meta ? "f4p-bad" : "f4p-good";
  const tip = `Tipo: Technical Story · itens abertos (qualquer data) + fechados em ${f4pExactSemesterLabel(st)} · clique no número para ver os itens`;
  return `<span title="${esc(tip)}"><span class="f4p-lo">${meta}</span><span class="f4p-sep">|</span><button type="button" class="f4p-real ${cls}" data-f4p-ts-team="${esc(team)}">${realizado}</button></span>`;
}
/* Situação de um item na lista de itens do Report F4P: mesma categoria de coluna do resto do portal
   (Backlog/Discovery/WIP/Vazão, mapeada por time em Configurações › fluxo — catOf/CAT_LABEL), em vez de
   um "Aberto"/"Fechado" próprio do Report F4P. Decisão 0019: mais coerente com o que o usuário já vê no
   quadro e no painel de detalhes (itens por categoria do épico). Vazão mostra também a data de saída,
   quando existir. */
const F4P_SIT_LABEL = {none:"Backlog", disc:"Discovery", wip:"WIP", vazao:"Vazão"};
function f4pItemSituacao(o){
  const cat = catOf(o), lab = F4P_SIT_LABEL[cat] || F4P_SIT_LABEL.none;
  return cat === "vazao" && o.deploy ? `${lab} · ${fmtL(o.deploy)}` : lab;
}
/* modal com a lista dos itens que compõem o Realizado (abre ao clicar no número) */
function f4pItemsModal(title, items){
  const rows = items.length ? items.map(o => `<tr><td><button type="button" class="idb" data-f4p-go="${esc(o.id)}">${esc(o.id)}</button></td>
      <td>${esc(o.title || "(sem título)")}</td>
      <td class="c">${esc(f4pItemSituacao(o))}</td></tr>`).join("")
    : `<tr><td colspan="3" class="muted">Nenhum item nesta contagem.</td></tr>`;
  $("f4pItemsTitle").textContent = title;
  $("f4pItemsBody").innerHTML = `<table class="ctab f4p-items-tbl"><thead><tr><th>ID</th><th>Título</th><th>Situação</th></tr></thead><tbody>${rows}</tbody></table>`;
  $("f4pItemsBg").hidden = false;
}
function closeF4PItems(){ $("f4pItemsBg").hidden = true; }
$("f4pItemsClose").onclick = closeF4PItems;
$("f4pItemsBg").addEventListener("pointerdown", e => { if (e.target === $("f4pItemsBg")) closeF4PItems(); });
$("f4pItemsBg").addEventListener("keydown", e => { if (e.key === "Escape"){ e.stopPropagation(); closeF4PItems(); } });
$("f4pItemsBody").addEventListener("click", e => {
  const g = e.target.closest("[data-f4p-go]");
  if (g){ closeF4PItems(); closeF4P(); $("goto").value = g.dataset.f4pGo; gotoId(g.dataset.f4pGo); }
});
$("f4pBody").addEventListener("click", e => {
  const st = f4pSemesterState();
  const btnU = e.target.closest("[data-f4p-urgent-team]");
  if (btnU){ const team = btnU.dataset.f4pUrgentTeam; f4pItemsModal(`Urgente · ${team} · ${f4pExactSemesterLabel(st)}`, f4pUrgentItems(team, st)); return; }
  const btnT = e.target.closest("[data-f4p-ts-team]");
  if (btnT){ const team = btnT.dataset.f4pTsTeam; f4pItemsModal(`Technical Story · ${team} · ${f4pExactSemesterLabel(st)}`, f4pTsItems(team, st)); }
});
const F4P_CELL = {var: f4pVarCell, ct: f4pCtCell, urg: f4pUrgentCell, ts: f4pTsCell};
function f4pCard(id, teams){
  const q = F4P_QUADS[id];
  const head = `<div class="f4p-card-h">${esc(q.title)}</div>${q.goal ? `<div class="f4p-goal">${esc(q.goal)}</div>` : ""}`;
  const thead = `<thead><tr>${teams.map(t => `<th>${esc(t)}</th>`).join("")}</tr></thead>`;
  if (!q.done) return `<div class="f4p-card">${head}<table class="f4p-tbl">${thead}
    <tbody><tr>${teams.map(() => `<td class="f4p-dash">--</td>`).join("")}</tr></tbody></table>
    <div class="f4p-note">Regra de cálculo ainda em definição.</div></div>`;
  return `<div class="f4p-card">${head}<table class="f4p-tbl">${thead}
    <tbody><tr>${teams.map(t => `<td>${F4P_CELL[id](t)}</td>`).join("")}</tr></tbody></table></div>`;
}
function f4pGroup(g, teams){
  return `<div class="f4p-group"><img class="f4p-badge" src="${F4P_ASSETS[g.badge]}" alt="${esc(g.alt)}">
    ${g.quads.map(id => f4pCard(id, teams)).join("")}</div>`;
}
function f4pEnabled(){ return anEnabled() && f4pSemesterState().kind !== "future"; }
function renderF4P(){
  const tab = $("f4pTab"), en = f4pEnabled();
  tab.disabled = !en;
  tab.title = en ? "Abrir o Report F4P (Business Outcomes – Productivity)"
    : !anEnabled() ? "Selecione um Time e um Roadmap (interno ou executivo) nos filtros para habilitar"
    : "O Report F4P não está disponível para um semestre que ainda não começou (ainda não há dados para calcular).";
  if (en && !tab.dataset.was){ tab.classList.remove("ready"); void tab.offsetWidth; tab.classList.add("ready"); }
  tab.dataset.was = en ? "1" : "";
  if (!en && F4P.open) closeF4P();
  if (!F4P.open) return;
  const teams = f4pTeams(), st = f4pSemesterState();
  $("f4pTitle").innerHTML = `<div class="f4p-title-row"><img class="f4p-logo" src="${F4P_ASSETS.f4pLogo}" alt="F4P">
    <div><h2>Report F4P <span class="f4p-sem">Business Outcomes – Productivity</span></h2><h3>${esc(semLong(f4pSemester()))}</h3></div></div>`;
  if (!teams.length){ $("f4pBody").innerHTML = `<div class="an-empty">Nenhum time carregado para calcular o relatório.</div>`; return; }
  const left = F4P_GROUPS.filter(g => g.side === "l"), right = F4P_GROUPS.filter(g => g.side === "r");
  $("f4pBody").innerHTML = `<div class="f4p-grid">
      <div class="f4p-col">${left.map(g => f4pGroup(g, teams)).join("")}</div>
      <div class="f4p-col">${right.map(g => f4pGroup(g, teams)).join("")}</div>
    </div>
    <div class="an-note">Mostra sempre todos os times carregados (${esc(teams.join(", "))}), mesmo com um time diferente selecionado no filtro — o filtro só habilita o acesso a este painel. CycleTime e Variabilidade usam itens dos tipos ${esc((CFG.f4p.types || []).join(", ") || "nenhum tipo marcado")} concluídos no período: <b>${esc(f4pPeriodLabel(st))}</b>${st.kind === "past" ? " (semestre selecionado, já encerrado)" : " (semestre selecionado ainda em curso, ou não reconhecido — usa a janela corrida)"}. Urgente conta itens com a tag <b>${esc(f4pTagName(f4pExpediteTag()))}</b> e Technical Story conta itens desse tipo, de resto com a mesma regra: os ainda abertos contam sempre, e os fechados só se fecharam dentro do período exato do semestre selecionado (<b>${esc(f4pExactSemesterLabel(st))}</b>) — sem histórico de quando cada item passou a se qualificar, não dá pra saber quem estava marcado antes disso. Os demais quadrantes aguardam a definição da regra de cálculo.</div>`;
}
function placeF4P(){ const h = document.querySelector(".top").offsetHeight; $("f4pPanel").style.top = h + "px"; $("f4pPanel").style.height = `calc(100% - ${h}px)`; }
function openF4P(){ if (!f4pEnabled()) return; if (AN.open) closeAnalytics(); F4P.open = true; placeF4P(); $("f4pPanel").classList.add("open"); $("f4pPanel").setAttribute("aria-hidden","false"); $("f4pTab").setAttribute("aria-expanded","true"); renderF4P(); $("f4pClose").focus(); }
function closeF4P(){ F4P.open = false; $("f4pPanel").classList.remove("open"); $("f4pPanel").setAttribute("aria-hidden","true"); $("f4pTab").setAttribute("aria-expanded","false"); }
$("f4pTab").onclick = openF4P;
$("f4pClose").onclick = () => { closeF4P(); $("f4pTab").focus(); };
window.addEventListener("resize", () => { if (F4P.open) placeF4P(); });
$("f4pPanel").addEventListener("keydown", e => { if (e.key === "Escape"){ e.stopPropagation(); closeF4P(); $("f4pTab").focus(); } });
