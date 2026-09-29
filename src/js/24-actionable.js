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
  const months = actBurnupMonths(st);
  // fim do último mês calculado (fim do semestre, se encerrado; hoje, se em curso) — um item entregue
  // depois disso não conta como "entregue" DESTE semestre, mesmo já estando em Vazão: no burnup de um
  // semestre já encerrado, uma entrega tardia (fora do período) entra em "faltam", não em "entregue"
  // (era o esperado para este período, mas não chegou dentro dele).
  const fimUltimoMes = months.length ? new Date(months[months.length - 1].getFullYear(), months[months.length - 1].getMonth() + 1, 0) : null;
  const entreguesNoPeriodo = o => catOf(o) === "vazao" && o.deploy && (!fimUltimoMes || o.deploy <= fimUltimoMes);
  const entregues = capItems.filter(entreguesNoPeriodo);
  const cumulative = months.map(m => {
    const fim = new Date(m.getFullYear(), m.getMonth() + 1, 0);
    return entregues.filter(o => o.deploy <= fim).length;
  });
  const escopo = capItems.length, entreguesN = cumulative.length ? cumulative[cumulative.length - 1] : 0;
  // "faltam": o resto da Reserva que ainda não entrou em Vazão dentro do período — complemento exato
  // de entregues dentro de capItems (entregues + faltamItems = capItems sempre, por construção).
  const faltamItems = capItems.filter(o => !entreguesNoPeriodo(o));
  return {months, escopo, cumulative, capItems, entregues, entreguesN, faltamItems, faltam: faltamItems.length};
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
    <button type="button" class="f4p-real ${data.faltam > 0 ? "f4p-warn" : "f4p-good"}" data-act-items="faltam">${data.faltam}</button> falta${data.faltam === 1 ? "" : "m"}
  </div>`;
}

/* Quadrante 3 · Distribuição Vazão por mês: para cada mês do semestre selecionado (do time em foco),
   dos itens ENTREGUES (categoria de fluxo Vazão) naquele mês — de qualquer tipo, exceto os tipos de
   bug configurados (CFG.act.bugTypes, padrão bug/internal bug/external bug, excluídos por inteiro da
   amostra) — quanto % é User Story (mesmo critério do quadrante User Story do Report F4P, §12.8:
   `CFG.f4p.usTypes`), quanto % é Technical Story (mesmo critério do quadrante Technical Story do Report
   F4P, §12.5: tipo fixo "technical story") e quanto % é "demais" (o resto da amostra, sem bugs). Um mês
   sem nenhum item na amostra — sem entregas no mês, ou todas bug — mostra uma barra cinza cheia com
   "0,00%"; isso cobre, de propósito, os meses ainda não decorridos de um semestre em curso: o gráfico
   sempre mostra os 6 meses do semestre (não só os já decorridos), para o usuário ver de antemão o que
   ainda falta ao longo do período. Decisão `0044`. */
function actBugTypes(){ return new Set(((CFG.act && CFG.act.bugTypes) || []).map(norm)); }
function actDistMonths(st){
  st = st || f4pSemesterState();
  const sem = f4pSemester(), start = f4pSemStart(sem);
  if (!start) return [];
  const months = [];
  for (let i = 0; i < 6; i++) months.push(new Date(start.getFullYear(), start.getMonth() + i, 1));
  return months;
}
function actDistItems(team, month){
  const fim = new Date(month.getFullYear(), month.getMonth() + 1, 0);
  const bugs = actBugTypes();
  return [...S.model.ops.values()].filter(o => o.team === team && o.type && !bugs.has(norm(o.type)) && catOf(o) === "vazao" && o.deploy && o.deploy >= month && o.deploy <= fim);
}
function actDistBuckets(team, month){
  const items = actDistItems(team, month);
  const usTypes = f4pUsTypes();
  const us = items.filter(o => usTypes.has(norm(o.type)));
  const ts = items.filter(o => norm(o.type) === "technical story");
  const demais = items.filter(o => !usTypes.has(norm(o.type)) && norm(o.type) !== "technical story");
  return {items, us, ts, demais};
}
function actDistData(team, st){
  return actDistMonths(st).map(month => {
    const {items, us, ts, demais} = actDistBuckets(team, month);
    const total = items.length;
    return {month, total, us, ts, demais,
      usPct: total ? us.length / total * 100 : 0,
      tsPct: total ? ts.length / total * 100 : 0,
      demaisPct: total ? demais.length / total * 100 : 0};
  });
}
function actDistMonthKey(month){ return `${month.getFullYear()}-${String(month.getMonth() + 1).padStart(2, "0")}`; }
function actDistMonthFromKey(key){ const [y, m] = key.split("-").map(Number); return new Date(y, m - 1, 1); }
function actDistRow(team, d){
  const mesLabel = d.month.toLocaleDateString("pt-BR", {month:"short"}).replace(".", "");
  const monthKey = actDistMonthKey(d.month);
  const seg = (cls, set, pct) => pct <= 0 ? "" :
    `<button type="button" class="act-dist-seg act-dist-${cls}" style="flex:0 0 ${pct}%" data-act-dist-team="${esc(team)}" data-act-dist-month="${monthKey}" data-act-dist-set="${set}"><span>${dec2(pct)}%</span></button>`;
  const bar = d.total > 0
    ? `${seg("us", "us", d.usPct)}${seg("ts", "ts", d.tsPct)}${seg("demais", "demais", d.demaisPct)}`
    : `<span class="act-dist-seg act-dist-none" style="flex:0 0 100%">${dec2(0)}%</span>`;
  return `<div class="act-dist-row"><span class="act-dist-month">${esc(mesLabel)}</span><div class="act-dist-bar" role="img" aria-label="${esc(mesLabel)}: ${d.total} ${d.total === 1 ? "item" : "itens"} na amostra">${bar}</div></div>`;
}
function actDistCard(team, data){
  return `<div class="act-dist">
    <div class="act-dist-legend">
      <span class="act-leg act-dist-us">User Story</span>
      <span class="act-leg act-dist-ts">Technical Story</span>
      <span class="act-leg act-dist-demais">Demais</span>
      <span class="act-leg act-dist-none">Sem registro</span>
    </div>
    <div class="act-dist-rows">${data.map(d => actDistRow(team, d)).join("")}</div>
    <div class="act-dist-xaxis"><span>0%</span><span>100%</span></div>
  </div>`;
}

/* Quadrante 4 · CFD (Cumulative Flow Diagram): reconstrói, semana a semana, quantos itens do time já
   chegaram a cada categoria de fluxo (Nenhum/Discovery/WIP/Vazão), usando as datas de entrada por
   coluna já guardadas no modelo (`o.fd`, decisão `0006`: a primeira coluna recebe a data de criação do
   item, colunas puladas herdam a data da próxima em que o item entrou) — não um cálculo novo sobre os
   dados, só uma leitura histórica do que o modelo já guarda. Eixo X: semanas do semestre selecionado,
   em blocos fixos de 7 dias a partir do 1º dia do semestre, terminando exatamente no último dia (a
   última semana pode ter menos de 7 dias). Eixo Y: contagem acumulada. Empilhamento estilo
   ActionableAgile (já citado no quadrante Eficiência de Fluxo do Report F4P, §12.9): Vazão na base
   (cresce pra cima), Nenhum no topo — sempre o total de itens já criados até aquela semana, nunca
   diminui. Configurável se conta itens do tipo bug (`CFG.act.cfdIncludeBugs`, padrão `true` — quando
   desligado, exclui os tipos de `CFG.act.bugTypes`, a mesma lista do quadrante Distribuição Vazão por
   mês). Decisão `0045`. */
function actCfdWeeks(st){
  st = st || f4pSemesterState();
  const {from, to} = f4pExactSemesterWindow(st);
  if (!from || !to) return [];
  const weeks = [];
  let cursor = from;
  while (cursor <= to){
    const fimBruto = new Date(cursor.getFullYear(), cursor.getMonth(), cursor.getDate() + 6);
    weeks.push({from: cursor, to: fimBruto < to ? fimBruto : to});
    cursor = new Date(cursor.getFullYear(), cursor.getMonth(), cursor.getDate() + 7);
  }
  return weeks;
}
function actCfdOps(team){
  const ops = [...S.model.ops.values()].filter(o => o.team === team);
  if (CFG.act.cfdIncludeBugs !== false) return ops;
  const bugs = actBugTypes();
  return ops.filter(o => !(o.type && bugs.has(norm(o.type))));
}
/* categoria de um item numa data T: o índice mais avançado (maior) do fluxo do time cuja coluna tem
   data de entrada (`o.fd`) menor ou igual a T — null se o item ainda não tinha sido criado até T. */
function actCfdCategoriaEm(o, T, c){
  let idx = -1;
  for (let i = 0; i < c.n.length; i++){
    const d = (o.fd || {})[c.n[i]];
    if (d && d <= T) idx = i;
  }
  return idx >= 0 ? c.cat[idx] : null;
}
function actCfdData(team, st){
  const weeks = actCfdWeeks(st);
  const ops = actCfdOps(team), c = teamCfg(team);
  const RANK = {none:0, disc:1, wip:2, vazao:3};
  return weeks.map(w => {
    let nenhum = 0, disc = 0, wip = 0, vazao = 0;
    ops.forEach(o => {
      const cat = actCfdCategoriaEm(o, w.to, c);
      if (cat == null) return;
      nenhum++;
      const r = RANK[cat];
      if (r >= 1) disc++;
      if (r >= 2) wip++;
      if (r >= 3) vazao++;
    });
    return {from: w.from, to: w.to, nenhum, disc, wip, vazao,
      bandNenhum: nenhum - disc, bandDisc: disc - wip, bandWip: wip - vazao, bandVazao: vazao};
  });
}
function actCfdSvg(data){
  if (!data.length) return `<div class="an-empty">Sem semanas no período para calcular.</div>`;
  const W = 460, H = 240, mL = 34, mR = 14, mT = 12, mB = 22;
  const pw = W - mL - mR, ph = H - mT - mB, n = data.length;
  const maxY = Math.max(...data.map(d => d.nenhum), 1) * 1.15;
  const xOf = i => n === 1 ? mL + pw / 2 : mL + (i / (n - 1)) * pw;
  const yOf = v => mT + ph - (v / maxY) * ph;
  const curve = key => data.map(d => d[key]);
  const zero = data.map(() => 0);
  const areaPath = (top, bottom) => {
    const up = top.map((v, i) => `${i === 0 ? "M" : "L"}${xOf(i).toFixed(1)},${yOf(v).toFixed(1)}`).join(" ");
    const down = bottom.slice().reverse().map((v, i) => `L${xOf(bottom.length - 1 - i).toFixed(1)},${yOf(v).toFixed(1)}`).join(" ");
    return `${up} ${down} Z`;
  };
  const vazao = curve("vazao"), wip = curve("wip"), disc = curve("disc"), nenhum = curve("nenhum");
  const bands = [
    {cls:"act-cfd-vazao", d: areaPath(vazao, zero)},
    {cls:"act-cfd-wip", d: areaPath(wip, vazao)},
    {cls:"act-cfd-disc", d: areaPath(disc, wip)},
    {cls:"act-cfd-nenhum", d: areaPath(nenhum, disc)}];
  const yTicks = [0, Math.round(maxY)];
  const yAxis = yTicks.map(v => `<text class="act-axis" x="${mL - 6}" y="${(yOf(v) + 3).toFixed(1)}" text-anchor="end">${v}</text><line class="act-grid" x1="${mL}" x2="${mL + pw}" y1="${yOf(v).toFixed(1)}" y2="${yOf(v).toFixed(1)}"></line>`).join("");
  const xAxis = `<text class="act-axis" x="${mL}" y="${H - 6}" text-anchor="start">${esc(fmtDM(data[0].from))}</text><text class="act-axis" x="${mL + pw}" y="${H - 6}" text-anchor="end">${esc(fmtDM(data[n - 1].to))}</text>`;
  const hit = data.map((d, i) => {
    const x0 = n === 1 ? mL : i === 0 ? mL : (xOf(i - 1) + xOf(i)) / 2;
    const x1 = n === 1 ? mL + pw : i === n - 1 ? mL + pw : (xOf(i) + xOf(i + 1)) / 2;
    const tip = `${fmtL(d.from)} a ${fmtL(d.to)} · Nenhum: ${d.bandNenhum} · Discovery: ${d.bandDisc} · WIP: ${d.bandWip} · Vazão: ${d.bandVazao}`;
    return `<rect class="act-cfd-hit" x="${x0.toFixed(1)}" y="${mT}" width="${(x1 - x0).toFixed(1)}" height="${ph}"><title>${esc(tip)}</title></rect>`;
  }).join("");
  return `<svg class="act-chart act-cfd" viewBox="0 0 ${W} ${H}" role="img" aria-label="Diagrama de fluxo cumulativo">
    ${yAxis}
    ${bands.map(b => `<path class="act-cfd-band ${b.cls}" d="${b.d}"></path>`).join("")}
    ${hit}
    ${xAxis}
  </svg>`;
}
function actCfdCard(data){
  return `<div class="act-cfd-wrap">
    <div class="act-cfd-legend">
      <span class="act-leg act-cfd-l-nenhum">Nenhum</span>
      <span class="act-leg act-cfd-l-disc">Discovery</span>
      <span class="act-leg act-cfd-l-wip">WIP</span>
      <span class="act-leg act-cfd-l-vazao">Vazão</span>
    </div>
    ${actCfdSvg(data)}
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
    `Reservado: itens com a tag <b>${esc(CFG.anTag || "ROADMAP")}</b> nos épicos do roadmap ${esc(S.f.int ? "interno" : "executivo")} do time (mesmo conjunto da Capacidade da Visão analítica, §10) — inclui itens em qualquer status, não só os já entregues. Entregue: subconjunto já na categoria de fluxo Vazão dentro do período do semestre selecionado, acumulado mês a mês. Faltam: o restante do Reservado que ainda não entrou em Vazão dentro do período (inclui uma entrega tardia, fora do semestre, se houver). Sem histórico de quando cada item entrou no roadmap, a linha Reservado é sempre a contagem atual (uma reta), não uma evolução real do escopo. Clique em "reservado", "entregue" ou "faltam" para ver os itens de cada grupo.`);
  const distData = actDistData(team, st);
  const distCard = actCard("Distribuição Vazão por mês", actDistCard(team, distData),
    `Para cada mês do semestre ${esc(semLong(f4pSemester()))}, dos itens entregues (Vazão) do time — exceto os tipos de bug (${esc((CFG.act.bugTypes || []).join(", ") || "nenhum tipo marcado")}) — % User Story (${esc((CFG.f4p.usTypes || []).join(", ") || "nenhum tipo marcado")}), % Technical Story (tipo fixo) e % demais tipos entregues. Um mês sem nenhum item na amostra (inclui os meses ainda não decorridos, no semestre em curso) mostra uma barra cinza com 0%. Clique numa fatia para ver os itens dela.`);
  const cfdData = actCfdData(team, st);
  const cfdCard = actCard("CFD (Cumulative Flow Diagram)", actCfdCard(cfdData),
    `Para cada semana do semestre ${esc(semLong(f4pSemester()))} (blocos de 7 dias a partir do 1º dia do semestre), quantos itens do time já chegaram a cada categoria de fluxo — Nenhum (criados), Discovery, WIP e Vazão — usando as datas reais de entrada em cada coluna do quadro. Vazão fica na base (cresce pra cima); Nenhum no topo é sempre o total de itens já criados até aquela semana (nunca diminui). ${CFG.act.cfdIncludeBugs === false ? "Itens do tipo bug não entram na amostra (desligado em Configurações)." : "Itens do tipo bug entram na amostra (padrão)."} Passe o mouse sobre o gráfico para ver os valores de cada semana.`);
  $("actBody").innerHTML = `<div class="f4p-grid">
      <div class="f4p-col">${ctCard}${distCard}</div>
      <div class="f4p-col">${buCard}${cfdCard}</div>
    </div>
    <div class="an-note">Os 4 quadrantes do Actionable têm regra definida.</div>`;
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
    const which = btn.dataset.actItems;
    const items = which === "reserva" ? buData.capItems : which === "entregue" ? buData.entregues : buData.faltamItems;
    const label = which === "reserva" ? "reservado" : which === "entregue" ? "entregue" : "faltam";
    f4pItemsModal(`Burnup Reserva · ${S.f.team} · ${label} · ${semLong(f4pSemester())}`, items);
    return;
  }
  const distBtn = e.target.closest("[data-act-dist-set]");
  if (distBtn){
    const team = distBtn.dataset.actDistTeam, set = distBtn.dataset.actDistSet;
    const month = actDistMonthFromKey(distBtn.dataset.actDistMonth);
    const {us, ts, demais} = actDistBuckets(team, month);
    const items = set === "us" ? us : set === "ts" ? ts : demais;
    const label = set === "us" ? "User Story" : set === "ts" ? "Technical Story" : "Demais";
    const mesLabel = month.toLocaleDateString("pt-BR", {month:"long", year:"numeric"});
    f4pItemsModal(`Distribuição Vazão por mês · ${team} · ${label} · ${mesLabel}`, items);
  }
});
