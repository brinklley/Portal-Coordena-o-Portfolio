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
  const baseMonths = actBurnupMonths(st);
  /* Decisão `0058`: "Entregue"/"Faltam" (resumo clicável, abaixo do gráfico) não dependem de a entrega
     ter caído dentro do período exato do semestre — mesma razão da decisão `0052` (Report F4P, Reserva
     entregue): um item da Reserva já em Vazão é entregue, ponto, mesmo que a saída tenha sido adiantada
     ou tardia em relação ao semestre comprometido; "Faltam" significa só o que de fato ainda não chegou
     em Vazão. */
  const entregues = capItems.filter(o => catOf(o) === "vazao");
  const entreguesN = entregues.length;
  const faltamItems = capItems.filter(o => catOf(o) !== "vazao");
  const escopo = capItems.length;
  /* Decisão `0060` (revê a metade "depois do fim" da `0059`): em vez de encaixar uma entrega tardia no
     último mês do eixo (um mês que não é o real), o gráfico ESTENDE o eixo X com os meses seguintes de
     verdade, até cobrir a entrega mais tardia — e uma linha vertical ("fim do semestre") marca onde o
     período comprometido de fato terminou, para o usuário ver que os pontos à direita dela são entregas
     fora do período. O lado "antes do início" continua como na `0059`: uma entrega adiantada é encaixada
     no 1º mês do eixo (não há "meses anteriores" reais para mostrar nem faz sentido estender pra trás). */
  let months = baseMonths, semEndIdx = null, extended = false;
  if (st.end && baseMonths.length){
    let maxDeploy = null;
    entregues.forEach(o => { if (o.deploy && o.deploy > st.end && (!maxDeploy || o.deploy > maxDeploy)) maxDeploy = o.deploy; });
    if (maxDeploy){
      const last = baseMonths[baseMonths.length - 1];
      const extra = (maxDeploy.getFullYear() - last.getFullYear()) * 12 + (maxDeploy.getMonth() - last.getMonth());
      if (extra > 0){
        months = baseMonths.slice();
        for (let i = 1; i <= extra; i++) months.push(new Date(last.getFullYear(), last.getMonth() + i, 1));
        semEndIdx = baseMonths.length - 1;
        extended = true;
      }
    }
  }
  const inicioPrimeiroMes = months.length ? months[0] : null;
  const mesEfetivo = o => !o.deploy ? null : o.deploy < inicioPrimeiroMes ? inicioPrimeiroMes : o.deploy;
  const cumulative = months.map(m => {
    const fim = new Date(m.getFullYear(), m.getMonth() + 1, 0);
    return entregues.filter(o => { const d = mesEfetivo(o); return d && d <= fim; }).length;
  });
  return {months, escopo, cumulative, capItems, entregues, entreguesN, faltamItems, faltam: faltamItems.length, semEndIdx, extended};
}
/* Linha vertical "fim do semestre" (decisão `0060`): marca, num gráfico de linha (Burnup Reserva, CFD),
   onde o período comprometido terminou de verdade, quando o eixo foi estendido além dele por causa de
   uma entrega tardia — posicionada a meio caminho entre o último ponto real do semestre e o primeiro
   ponto estendido (mesmo espírito visual da linha "hoje" já existente no CFD). */
function actSemEndLine(xOf, idx, mT, ph){
  if (idx == null) return "";
  const x = ((xOf(idx) + xOf(idx + 1)) / 2).toFixed(1);
  return `<line class="act-sem-end" x1="${x}" x2="${x}" y1="${mT}" y2="${mT + ph}"></line><text class="act-sem-end-label" x="${x}" y="${mT - 2}" text-anchor="middle">fim do semestre</text>`;
}
function actBurnupSvg(data){
  const {months, escopo, cumulative, semEndIdx, extended} = data;
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
  const semEndLine = extended ? actSemEndLine(xOf, semEndIdx, mT, ph) : "";
  return `<svg class="act-chart act-burnup" viewBox="0 0 ${W} ${H}" role="img" aria-label="Burnup da reserva do roadmap">
    ${yAxis}${xLabels}
    <path class="act-line act-line-escopo" d="${pathOf(escopoVals)}"></path>
    <path class="act-line act-line-entregue" d="${pathOf(cumulative)}"></path>
    ${dotsOf(cumulative, "act-dot-ok")}
    ${semEndLine}
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

/* Itens "tardios" (decisão `0060`): entregues (categoria Vazão) depois do fim do semestre selecionado,
   mas cujo épico está comprometido com o roadmap deste time+semestre (mesmo conjunto de épicos da coluna
   "Projetada" da Visão analítica, §10 — `anData().projItems`; não exige a tag de capacidade do roadmap,
   ao contrário do Burnup Reserva). Usado só para decidir até onde estender o eixo X do CFD e da
   Distribuição Vazão por mês além do semestre — o Burnup Reserva tem sua própria regra (`actBurnupData`),
   baseada só nos itens que ele mesmo mostra (a Reserva, `capItems`), não neste helper. */
function actLateDeliveries(st, ad){
  st = st || f4pSemesterState();
  if (!st.end) return [];
  ad = ad || anData();
  return ad.projItems.filter(o => catOf(o) === "vazao" && o.deploy && o.deploy > st.end);
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
/* Decisão `0060`: se há item "tardio" (helper `actLateDeliveries`, definido acima) entregue além dos 6
   meses do semestre, os meses seguintes reais entram no eixo também — mesma extensão do Burnup Reserva
   e do CFD, só que aqui, por ser um gráfico de barras (não uma linha contínua), não há linha vertical:
   o mês extra ganha um ícone de alerta junto ao rótulo (`actDistData`/`actDistRow`, abaixo). */
function actDistMonths(st){
  st = st || f4pSemesterState();
  const sem = f4pSemester(), start = f4pSemStart(sem);
  if (!start) return [];
  const months = [];
  for (let i = 0; i < 6; i++) months.push(new Date(start.getFullYear(), start.getMonth() + i, 1));
  let maxDeploy = null;
  actLateDeliveries(st).forEach(o => { if (!maxDeploy || o.deploy > maxDeploy) maxDeploy = o.deploy; });
  if (maxDeploy){
    const last = months[5];
    const extra = (maxDeploy.getFullYear() - last.getFullYear()) * 12 + (maxDeploy.getMonth() - last.getMonth());
    for (let i = 1; i <= extra; i++) months.push(new Date(last.getFullYear(), last.getMonth() + i, 1));
  }
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
  return actDistMonths(st).map((month, idx) => {
    const {items, us, ts, demais} = actDistBuckets(team, month);
    const total = items.length;
    return {month, total, us, ts, demais, late: idx >= 6,
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
  /* Decisão `0060`: mês além do semestre (entrega tardia de um item cujo épico está comprometido com o
     roadmap) — ícone de alerta junto ao rótulo do mês, sem linha vertical (ver comentário em
     `actDistMonths`). */
  const alertIcon = d.late ? `<span class="act-dist-late-icon" title="Fora do semestre selecionado — aparece porque um item de um épico comprometido com este roadmap foi entregue neste mês.">⚠</span>` : "";
  return `<div class="act-dist-row"><span class="act-dist-month">${esc(mesLabel)}${alertIcon}</span><div class="act-dist-bar" role="img" aria-label="${esc(mesLabel)}: ${d.total} ${d.total === 1 ? "item" : "itens"} na amostra">${bar}</div></div>`;
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
   diminui (dentro do escopo do semestre — ver `actCfdOps`). Configurável se conta itens do tipo bug
   (`CFG.act.cfdIncludeBugs`, padrão `true` — quando desligado, exclui os tipos de `CFG.act.bugTypes`, a
   mesma lista do quadrante Distribuição Vazão por mês). Decisões `0045`, `0046` (Vazão passou a iniciar
   em 0 no início do semestre, excluindo itens já entregues antes dele). */
function actCfdWeeksBlock(from, to){
  const weeks = [];
  let cursor = from;
  while (cursor <= to){
    const fimBruto = new Date(cursor.getFullYear(), cursor.getMonth(), cursor.getDate() + 6);
    weeks.push({from: cursor, to: fimBruto < to ? fimBruto : to});
    cursor = new Date(cursor.getFullYear(), cursor.getMonth(), cursor.getDate() + 7);
  }
  return weeks;
}
/* semanas do semestre selecionado, sem nenhuma extensão — exatamente o comportamento de antes da
   decisão `0060` (usado por `actCfdSemEndIdx`, abaixo, para achar a fronteira entre o período real e as
   semanas estendidas). */
function actCfdBaseWeeks(st){
  st = st || f4pSemesterState();
  const {from, to} = f4pExactSemesterWindow(st);
  return (from && to) ? actCfdWeeksBlock(from, to) : [];
}
/* Decisão `0060`: se há item "tardio" (`actLateDeliveries`) entregue depois do fim das semanas base, o
   eixo X é estendido com semanas reais seguintes (começando no dia seguinte ao fim do semestre) até
   cobrir a entrega mais tardia — em vez de o CFD simplesmente não ter onde mostrar essa entrega. Uma
   linha vertical "fim do semestre" marca a fronteira (`actCfdSemEndIdx` + `actSemEndLine`, em
   `actCfdSvg`). */
function actCfdWeeks(st){
  st = st || f4pSemesterState();
  const base = actCfdBaseWeeks(st);
  if (!base.length) return base;
  const to = base[base.length - 1].to;
  let maxDeploy = null;
  actLateDeliveries(st).forEach(o => { if (o.deploy > to && (!maxDeploy || o.deploy > maxDeploy)) maxDeploy = o.deploy; });
  if (!maxDeploy) return base;
  const extraStart = new Date(to.getFullYear(), to.getMonth(), to.getDate() + 1);
  return base.concat(actCfdWeeksBlock(extraStart, maxDeploy));
}
function actCfdSemEndIdx(st){
  const base = actCfdBaseWeeks(st);
  return base.length ? base.length - 1 : null;
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
/* itens do time relevantes para o CFD do semestre selecionado: exclui os que já estavam em Vazão no dia
   anterior ao início do semestre — itens de negócio já resolvidos antes do período, que só inflariam a
   faixa de Vazão com histórico alheio ao semestre em análise (melhoria pedida pelo usuário depois de ver
   o gráfico dominado por esse histórico: "a vazão deveria iniciar em 0 no primeiro dia do semestre").
   Itens ainda não entregues, e itens entregues dentro do próprio semestre selecionado, continuam
   contando normalmente — só o que já estava pronto ANTES do período some do gráfico inteiro (não só da
   faixa de Vazão), já que deixaram de ser parte do fluxo em análise. */
function actCfdOps(team, st){
  st = st || f4pSemesterState();
  const {from} = f4pExactSemesterWindow(st);
  const c = teamCfg(team);
  const diaAnterior = from ? new Date(from.getFullYear(), from.getMonth(), from.getDate() - 1) : null;
  let ops = [...S.model.ops.values()].filter(o => o.team === team && (!diaAnterior || actCfdCategoriaEm(o, diaAnterior, c) !== "vazao"));
  if (CFG.act.cfdIncludeBugs === false){
    const bugs = actBugTypes();
    ops = ops.filter(o => !(o.type && bugs.has(norm(o.type))));
  }
  return ops;
}
function actCfdData(team, st){
  st = st || f4pSemesterState();
  const weeks = actCfdWeeks(st);
  const ops = actCfdOps(team, st), c = teamCfg(team);
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
/* Num semestre em curso, o "morro" só é desenhado até a semana atual (inclusive) — o restante não
   precisa ser construído, já que não há dado real depois de hoje (nenhuma data de coluna cai no
   futuro); em vez de deixar as faixas achatadas como projeção (como a Distribuição Vazão por mês faz de
   propósito, §13.2), o CFD marca uma linha vertical "hoje" no limite e deixa o resto do período em
   branco. O eixo X continua mostrando o semestre inteiro (mesmas marcas de início/fim), só a área
   desenhada é que para em hoje. Num semestre já encerrado, desenha o período inteiro normalmente (não
   há "resto" para deixar de construir). Decisão `0047`. */
function actCfdSvg(data, st){
  if (!data.length) return `<div class="an-empty">Sem semanas no período para calcular.</div>`;
  st = st || f4pSemesterState();
  const n = data.length;
  let cutoff = n - 1, hojeIdx = null;
  if (st.kind === "current"){
    hojeIdx = data.findIndex(w => TODAY >= w.from && TODAY <= w.to);
    if (hojeIdx < 0) hojeIdx = n - 1;
    cutoff = hojeIdx;
  }
  const W = 460, H = 240, mL = 34, mR = 14, mT = 12, mB = 22;
  const pw = W - mL - mR, ph = H - mT - mB;
  const maxY = Math.max(...data.map(d => d.nenhum), 1) * 1.15;
  const xOf = i => n === 1 ? mL + pw / 2 : mL + (i / (n - 1)) * pw;
  const yOf = v => mT + ph - (v / maxY) * ph;
  const drawn = data.slice(0, cutoff + 1);
  const areaPath = (top, bottom) => {
    if (top.length < 2) return "";
    const up = top.map((v, i) => `${i === 0 ? "M" : "L"}${xOf(i).toFixed(1)},${yOf(v).toFixed(1)}`).join(" ");
    const down = bottom.slice().reverse().map((v, i) => `L${xOf(bottom.length - 1 - i).toFixed(1)},${yOf(v).toFixed(1)}`).join(" ");
    return `${up} ${down} Z`;
  };
  const curve = key => drawn.map(d => d[key]);
  const zero = drawn.map(() => 0);
  const vazao = curve("vazao"), wip = curve("wip"), disc = curve("disc"), nenhum = curve("nenhum");
  const bands = [
    {cls:"act-cfd-vazao", d: areaPath(vazao, zero)},
    {cls:"act-cfd-wip", d: areaPath(wip, vazao)},
    {cls:"act-cfd-disc", d: areaPath(disc, wip)},
    {cls:"act-cfd-nenhum", d: areaPath(nenhum, disc)}];
  const yTicks = [0, Math.round(maxY)];
  const yAxis = yTicks.map(v => `<text class="act-axis" x="${mL - 6}" y="${(yOf(v) + 3).toFixed(1)}" text-anchor="end">${v}</text><line class="act-grid" x1="${mL}" x2="${mL + pw}" y1="${yOf(v).toFixed(1)}" y2="${yOf(v).toFixed(1)}"></line>`).join("");
  const xAxis = `<text class="act-axis" x="${mL}" y="${H - 6}" text-anchor="start">${esc(fmtDM(data[0].from))}</text><text class="act-axis" x="${mL + pw}" y="${H - 6}" text-anchor="end">${esc(fmtDM(data[n - 1].to))}</text>`;
  const hoje = hojeIdx == null ? "" :
    `<line class="act-cfd-hoje" x1="${xOf(hojeIdx).toFixed(1)}" x2="${xOf(hojeIdx).toFixed(1)}" y1="${mT}" y2="${mT + ph}"></line><text class="act-cfd-hoje-label" x="${xOf(hojeIdx).toFixed(1)}" y="${mT - 2}" text-anchor="middle">hoje</text>`;
  const semEndIdx = actCfdSemEndIdx(st);
  const semEndLine = (semEndIdx != null && semEndIdx < n - 1 && semEndIdx < cutoff) ? actSemEndLine(xOf, semEndIdx, mT, ph) : "";
  const hit = drawn.map((d, i) => {
    const x0 = n === 1 ? mL : i === 0 ? mL : (xOf(i - 1) + xOf(i)) / 2;
    const x1 = n === 1 ? mL + pw : i === n - 1 ? mL + pw : i === cutoff ? xOf(i) : (xOf(i) + xOf(i + 1)) / 2;
    const tip = `${fmtL(d.from)} a ${fmtL(d.to)} · Nenhum: ${d.bandNenhum} · Discovery: ${d.bandDisc} · WIP: ${d.bandWip} · Vazão: ${d.bandVazao}`;
    return `<rect class="act-cfd-hit" x="${x0.toFixed(1)}" y="${mT}" width="${(x1 - x0).toFixed(1)}" height="${ph}"><title>${esc(tip)}</title></rect>`;
  }).join("");
  return `<svg class="act-chart act-cfd" viewBox="0 0 ${W} ${H}" role="img" aria-label="Diagrama de fluxo cumulativo">
    ${yAxis}
    ${bands.map(b => b.d ? `<path class="act-cfd-band ${b.cls}" d="${b.d}"></path>` : "").join("")}
    ${hit}
    ${hoje}
    ${semEndLine}
    ${xAxis}
  </svg>`;
}
function actCfdCard(data, st){
  return `<div class="act-cfd-wrap">
    <div class="act-cfd-legend">
      <span class="act-leg act-cfd-l-nenhum">Nenhum</span>
      <span class="act-leg act-cfd-l-disc">Discovery</span>
      <span class="act-leg act-cfd-l-wip">WIP</span>
      <span class="act-leg act-cfd-l-vazao">Vazão</span>
    </div>
    ${actCfdSvg(data, st)}
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
    `Reservado: itens com a tag <b>${esc(CFG.anTag || "ROADMAP")}</b> nos épicos do roadmap ${esc(S.f.int ? "interno" : "executivo")} do time (mesmo conjunto da Capacidade da Visão analítica, §10) — inclui itens em qualquer status, não só os já entregues. Entregue: subconjunto já na categoria de fluxo Vazão, mesmo que a entrega tenha caído fora do período exato do semestre (adiantada ou tardia). Faltam: o restante do Reservado que ainda não entrou em Vazão, de forma nenhuma. Uma entrega antes do início do semestre entra no 1º mês do gráfico. Uma entrega depois do fim estende o eixo X com os meses seguintes reais, até cobrir a entrega mais tardia — uma linha vertical "fim do semestre" marca onde o período comprometido terminou, para diferenciar o que foi entregue dentro dele do que veio depois. Sem histórico de quando cada item entrou no roadmap, a linha Reservado é sempre a contagem atual (uma reta), não uma evolução real do escopo. Clique em "reservado", "entregue" ou "faltam" para ver os itens de cada grupo.`);
  const distData = actDistData(team, st);
  const distTemMesTardio = distData.some(d => d.late);
  const distCard = actCard("Distribuição Vazão por mês", actDistCard(team, distData),
    `Para cada mês do semestre ${esc(semLong(f4pSemester()))}, dos itens entregues (Vazão) do time — exceto os tipos de bug (${esc((CFG.act.bugTypes || []).join(", ") || "nenhum tipo marcado")}) — % User Story (${esc((CFG.f4p.usTypes || []).join(", ") || "nenhum tipo marcado")}), % Technical Story (tipo fixo) e % demais tipos entregues. Um mês sem nenhum item na amostra (inclui os meses ainda não decorridos, no semestre em curso) mostra uma barra cinza com 0%.${distTemMesTardio ? ` Mês marcado com ⚠: fora do semestre selecionado — aparece porque um item de um épico comprometido com este roadmap foi entregue depois do período; o cálculo desse mês continua olhando todas as entregas do time naquele mês civil, sem filtrar por épico, igual aos demais.` : ""} Clique numa fatia para ver os itens dela.`);
  const cfdData = actCfdData(team, st);
  const cfdCard = actCard("CFD (Cumulative Flow Diagram)", actCfdCard(cfdData, st),
    `Para cada semana do semestre ${esc(semLong(f4pSemester()))} (blocos de 7 dias a partir do 1º dia do semestre), quantos itens do time já chegaram a cada categoria de fluxo — Nenhum (criados), Discovery, WIP e Vazão — usando as datas reais de entrada em cada coluna do quadro. Não entram itens já entregues (Vazão) antes do início do semestre selecionado, para a Vazão refletir o que aconteceu dentro do período, não o histórico acumulado de negócio já resolvido antes dele. Vazão fica na base (cresce pra cima); Nenhum no topo é sempre o total de itens (do escopo do semestre) já criados até aquela semana (nunca diminui).${st.kind === "current" ? " Num semestre em curso, o gráfico só desenha até a semana atual (marcada por uma linha vertical \"hoje\") — o restante do período fica em branco, em vez de projetar uma continuação achatada." : ""} Se um item de um épico comprometido com este roadmap for entregue depois do fim do semestre, o eixo X estende com as semanas seguintes reais até cobrir essa entrega, com uma linha vertical "fim do semestre" marcando a fronteira. ${CFG.act.cfdIncludeBugs === false ? "Itens do tipo bug não entram na amostra (desligado em Configurações)." : "Itens do tipo bug entram na amostra (padrão)."} Passe o mouse sobre o gráfico para ver os valores de cada semana.`);
  $("actBody").innerHTML = `<div class="act-quad-grid">${ctCard}${buCard}${distCard}${cfdCard}</div>
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
