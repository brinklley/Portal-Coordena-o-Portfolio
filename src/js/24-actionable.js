/* ---------- Actionable: métricas acionáveis por time no período do roadmap ----------
   Primeira versão (MVP/brainstorm): painel lateral com o mesmo comportamento da Visão analítica (um
   time por vez, habilitado com Time + Roadmap interno ou executivo — anEnabled()). Estrutura fixa de
   4 quadrantes em 2 colunas, inspirada no layout do Report F4P (f4p-grid/f4p-col/f4p-card); só os 2
   primeiros têm regra definida ainda — os outros dois ficam como "em definição" (mesmo padrão do
   Report F4P para um quadrante sem regra fechada, ver f4pCard). */
const ACT = {open:false};
function actEnabled(){ return anEnabled() && f4pSemesterState().kind !== "future"; }

/* Quadrante 1 · CycleTime: reaproveita a mesma amostra e regra do Report F4P §12.2 (CycleTime, reserva
   vs. atual) — f4pSample (itens concluídos, tipos configurados em CFG.f4p.types, dentro da janela do
   semestre — f4pWindow) e o CT máximo do time (limitsOf) como Reserva — só que aqui cada item vira um
   ponto do dispersão (X = data de entrega, Y = CT em dias), em vez de resumir tudo num único P95. O
   próprio P95 (o "Atual" do quadrante original) entra como uma segunda linha de referência, para
   comparar visualmente com a distribuição real por trás dele. */
function actCtScatterData(team, st){
  st = st || f4pSemesterState();
  const items = f4pSample(team, st);
  const L = limitsOf(team);
  const cts = items.map(o => o.ct).sort((a, b) => a - b);
  const atual = cts.length ? percentil(cts, .95) : null;
  return {items, reserva: L.max, planned: L.planned, atual, window: f4pWindow(st)};
}
function actScatterSvg(data){
  const {items, reserva, atual, window} = data;
  if (!items.length) return `<div class="an-empty">Nenhum item concluído no período para calcular.</div>`;
  const W = 460, H = 220, mL = 34, mR = 14, mT = 12, mB = 22;
  const pw = W - mL - mR, ph = H - mT - mB;
  const from = +window.from, to = +window.to, span = Math.max(to - from, 864e5);
  const maxCt = Math.max(reserva || 0, atual || 0, ...items.map(o => o.ct), 1) * 1.15;
  const xOf = d => mL + ((+d - from) / span) * pw;
  const yOf = v => mT + ph - (v / maxCt) * ph;
  const refLine = (v, cls, label) => v == null ? "" :
    `<line class="act-ref ${cls}" x1="${mL}" x2="${mL + pw}" y1="${yOf(v).toFixed(1)}" y2="${yOf(v).toFixed(1)}"></line>
     <text class="act-ref-label ${cls}" x="${mL + pw}" y="${(yOf(v) - 4).toFixed(1)}" text-anchor="end">${esc(label)}</text>`;
  const dots = items.map(o => {
    const bad = reserva != null && o.ct > reserva;
    return `<circle class="act-dot ${bad ? "act-dot-bad" : "act-dot-ok"}" cx="${xOf(o.deploy).toFixed(1)}" cy="${yOf(o.ct).toFixed(1)}" r="4" data-act-go="${esc(o.id)}" tabindex="0"><title>${esc(o.id)} · ${esc(o.title || "(sem título)")} · CT ${o.ct}d · ${fmtDM(o.deploy)}</title></circle>`;
  }).join("");
  const yTicks = [0, Math.round(maxCt)];
  const yAxis = yTicks.map(v => `<text class="act-axis" x="${mL - 6}" y="${(yOf(v) + 3).toFixed(1)}" text-anchor="end">${v}</text><line class="act-grid" x1="${mL}" x2="${mL + pw}" y1="${yOf(v).toFixed(1)}" y2="${yOf(v).toFixed(1)}"></line>`).join("");
  const xAxis = `<text class="act-axis" x="${mL}" y="${H - 6}" text-anchor="start">${fmtDM(window.from)}</text><text class="act-axis" x="${mL + pw}" y="${H - 6}" text-anchor="end">${fmtDM(window.to)}</text>`;
  return `<svg class="act-chart act-scatter" viewBox="0 0 ${W} ${H}" role="img" aria-label="Dispersão de CycleTime">
    ${yAxis}${xAxis}${refLine(reserva, "act-ref-reserva", `Reserva ${reserva ?? "--"}d`)}${refLine(atual, "act-ref-atual", `Atual (P95) ${atual != null ? Math.round(atual) : "--"}d`)}${dots}
  </svg>`;
}
function actCtLegend(data){
  const {reserva, atual, planned, items} = data;
  return `<div class="act-legend">
    <span class="act-leg act-ref-reserva">Reserva: ${reserva ?? "--"}d${planned ? "" : " (regra geral, sem CT planejado)"}</span>
    <span class="act-leg act-ref-atual">Atual (P95): ${atual != null ? Math.round(atual) + "d" : "--"}</span>
    <span class="act-leg-n">${items.length} ${items.length === 1 ? "item" : "itens"}</span>
  </div>`;
}

/* Quadrante 2 · Burnup Reserva: "reservado" é o mesmo conceito de Capacidade da Visão analítica (§10) —
   itens com a tag de capacidade do roadmap (CFG.anTag) nos épicos do roadmap do time+semestre
   selecionado, em QUALQUER status (não só os já entregues — ao contrário da Reserva do quadrante Vazão
   do Report F4P, que só existe dentro do que já foi entregue; sem incluir os ainda não entregues não
   haveria "quanto falta" pra mostrar). "Entregue" é o subconjunto desses itens já na categoria de fluxo
   Vazão, acumulado mês a mês dentro do semestre selecionado. Sem histórico de quando cada item entrou
   no roadmap, o escopo (linha Reservado) é sempre a contagem ATUAL — mostrado como uma reta no burnup,
   não como algo que pode ter crescido ao longo do semestre. */
function actBurnupMonths(st){
  st = st || f4pSemesterState();
  const sem = f4pSemester(), start = f4pSemStart(sem);
  if (!start) return [];
  const lastIdx = st.kind === "past" ? 5 : Math.min(5, (TODAY.getFullYear() - start.getFullYear()) * 12 + (TODAY.getMonth() - start.getMonth()));
  const months = [];
  for (let i = 0; i <= lastIdx; i++) months.push(new Date(start.getFullYear(), start.getMonth() + i, 1));
  return months;
}
function actBurnupData(st){
  st = st || f4pSemesterState();
  const capItems = anData().capItems;
  const entregues = capItems.filter(o => catOf(o) === "vazao" && o.deploy);
  const months = actBurnupMonths(st);
  const cumulative = months.map(m => {
    const fim = new Date(m.getFullYear(), m.getMonth() + 1, 0);
    return entregues.filter(o => o.deploy <= fim).length;
  });
  const escopo = capItems.length, entreguesN = cumulative.length ? cumulative[cumulative.length - 1] : 0;
  return {months, escopo, cumulative, capItems, entregues, entreguesN, faltam: Math.max(0, escopo - entreguesN)};
}
function actBurnupSvg(data){
  const {months, escopo, cumulative} = data;
  if (!months.length) return `<div class="an-empty">Sem meses no período para calcular.</div>`;
  const W = 460, H = 220, mL = 28, mR = 14, mT = 12, mB = 22;
  const pw = W - mL - mR, ph = H - mT - mB, n = months.length;
  const maxY = Math.max(escopo, ...cumulative, 1) * 1.15;
  const xOf = i => n === 1 ? mL + pw / 2 : mL + (i / (n - 1)) * pw;
  const yOf = v => mT + ph - (v / maxY) * ph;
  const pathOf = vals => vals.map((v, i) => `${i === 0 ? "M" : "L"}${xOf(i).toFixed(1)},${yOf(v).toFixed(1)}`).join(" ");
  const dotsOf = (vals, cls) => vals.map((v, i) => `<circle class="act-dot ${cls}" cx="${xOf(i).toFixed(1)}" cy="${yOf(v).toFixed(1)}" r="3.5"></circle>`).join("");
  const escopoVals = months.map(() => escopo);
  const yTicks = [0, Math.round(maxY)];
  const yAxis = yTicks.map(v => `<text class="act-axis" x="${mL - 6}" y="${(yOf(v) + 3).toFixed(1)}" text-anchor="end">${v}</text><line class="act-grid" x1="${mL}" x2="${mL + pw}" y1="${yOf(v).toFixed(1)}" y2="${yOf(v).toFixed(1)}"></line>`).join("");
  const xLabels = months.map((m, i) => `<text class="act-axis" x="${xOf(i).toFixed(1)}" y="${H - 6}" text-anchor="middle">${esc(m.toLocaleDateString("pt-BR", {month:"short"}).replace(".", ""))}</text>`).join("");
  return `<svg class="act-chart act-burnup" viewBox="0 0 ${W} ${H}" role="img" aria-label="Burnup da reserva do roadmap">
    ${yAxis}${xLabels}
    <path class="act-line act-line-escopo" d="${pathOf(escopoVals)}"></path>
    <path class="act-line act-line-entregue" d="${pathOf(cumulative)}"></path>
    ${dotsOf(cumulative, "act-dot-ok")}
  </svg>`;
}
function actBurnupSummary(data){
  return `<div class="act-summary">
    <button type="button" class="f4p-real" data-act-items="reserva">${data.escopo}</button> reservado${data.escopo === 1 ? "" : "s"}
    <span class="f4p-sep">·</span>
    <button type="button" class="f4p-real f4p-good" data-act-items="entregue">${data.entreguesN}</button> entregue${data.entreguesN === 1 ? "" : "s"}
    <span class="f4p-sep">·</span>
    <b class="${data.faltam > 0 ? "f4p-warn" : "f4p-good"}">${data.faltam}</b> falta${data.faltam === 1 ? "" : "m"}
  </div>`;
}

function actCard(title, bodyHtml, note){
  return `<div class="f4p-card"><div class="f4p-card-h">${esc(title)}</div><div class="act-card-body">${bodyHtml}</div>${note ? `<div class="f4p-note">${note}</div>` : ""}</div>`;
}
function actPlaceholderCard(title){
  return `<div class="f4p-card"><div class="f4p-card-h">${esc(title)}</div><div class="act-card-body"><div class="an-empty">Regra de cálculo ainda em definição.</div></div></div>`;
}

function renderActionable(){
  const tab = $("actTab"), en = actEnabled();
  tab.disabled = !en;
  tab.title = en ? "Abrir o Actionable"
    : !anEnabled() ? "Selecione um Time e um Roadmap (interno ou executivo) nos filtros para habilitar"
    : "O Actionable não está disponível para um semestre que ainda não começou (ainda não há dados para calcular).";
  if (en && !tab.dataset.was){ tab.classList.remove("ready"); void tab.offsetWidth; tab.classList.add("ready"); }
  tab.dataset.was = en ? "1" : "";
  if (!en && ACT.open) closeActionable();
  if (!ACT.open) return;
  const team = S.f.team, st = f4pSemesterState();
  $("actTitle").innerHTML = `<h2>Actionable <span class="f4p-sem">${esc(team)}</span></h2><h3>${esc(semLong(f4pSemester()))}</h3>`;
  const ctData = actCtScatterData(team, st);
  const buData = actBurnupData(st);
  const ctCard = actCard("CycleTime", actScatterSvg(ctData) + actCtLegend(ctData),
    `Dispersão de CycleTime dos itens concluídos (${esc((CFG.f4p.types || []).join(", ") || "nenhum tipo marcado")}) no período <b>${esc(f4pPeriodLabel(st))}</b> — mesma amostra e Reserva (CT máximo do time) do quadrante CycleTime do Report F4P (§12.2); Atual é o P95 da amostra. Pontos acima da Reserva ficam em destaque. Clique num ponto para ir até o item.`);
  const buCard = actCard("Burnup Reserva", actBurnupSummary(buData) + actBurnupSvg(buData),
    `Reservado: itens com a tag <b>${esc(CFG.anTag || "ROADMAP")}</b> nos épicos do roadmap ${esc(S.f.int ? "interno" : "executivo")} do time (mesmo conjunto da Capacidade da Visão analítica, §10) — inclui itens em qualquer status, não só os já entregues. Entregue: subconjunto já na categoria de fluxo Vazão, acumulado mês a mês. Sem histórico de quando cada item entrou no roadmap, a linha Reservado é sempre a contagem atual (uma reta), não uma evolução real do escopo. Clique em "reservado"/"entregue" para ver os itens.`);
  $("actBody").innerHTML = `<div class="f4p-grid">
      <div class="f4p-col">${ctCard}${actPlaceholderCard("Em definição")}</div>
      <div class="f4p-col">${buCard}${actPlaceholderCard("Em definição")}</div>
    </div>
    <div class="an-note">Primeira versão (MVP) do Actionable — só os quadrantes CycleTime e Burnup Reserva têm regra definida; os outros dois serão detalhados depois.</div>`;
}
function placeAct(){ const h = document.querySelector(".top").offsetHeight; $("actPanel").style.top = h + "px"; $("actPanel").style.height = `calc(100% - ${h}px)`; }
function openActionable(){ if (!actEnabled()) return; if (AN.open) closeAnalytics(); if (F4P.open) closeF4P(); ACT.open = true; placeAct(); $("actPanel").classList.add("open"); $("actPanel").setAttribute("aria-hidden","false"); $("actTab").setAttribute("aria-expanded","true"); renderActionable(); $("actClose").focus(); }
function closeActionable(){ ACT.open = false; $("actPanel").classList.remove("open"); $("actPanel").setAttribute("aria-hidden","true"); $("actTab").setAttribute("aria-expanded","false"); }
$("actTab").onclick = openActionable;
$("actClose").onclick = () => { closeActionable(); $("actTab").focus(); };
window.addEventListener("resize", () => { if (ACT.open) placeAct(); });
$("actPanel").addEventListener("keydown", e => { if (e.key === "Escape"){ e.stopPropagation(); closeActionable(); $("actTab").focus(); } });
$("actBody").addEventListener("click", e => {
  const dot = e.target.closest("[data-act-go]");
  if (dot){ closeActionable(); gotoId(dot.dataset.actGo); return; }
  const btn = e.target.closest("[data-act-items]");
  if (btn){
    const buData = actBurnupData();
    const which = btn.dataset.actItems, items = which === "reserva" ? buData.capItems : buData.entregues;
    f4pItemsModal(`Burnup Reserva · ${S.f.team} · ${which === "reserva" ? "reservado" : "entregue"} · ${semLong(f4pSemester())}`, items);
  }
});
