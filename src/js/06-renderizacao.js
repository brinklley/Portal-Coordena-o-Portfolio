/* ---------------- renderização ---------------- */
const $ = id => document.getElementById(id);
const board = $("board");

function stageIndex(stages, name){ const n = norm(name); return stages.findIndex(s => norm(s) === n); }

function render(){
  const M = S.model;
  if (!M){ board.innerHTML = `<div class="empty-state"><h2>Nenhum dado carregado</h2><p>Conecte e carregue os dados pelo Azure DevOps.</p></div>`; return; }
  const V = computeVisible(); S.V = V;
  // descarta caminho que ficou fora do filtro
  if (S.path.ini && !V.visIni.has(S.path.ini)) { S.path = {}; S.expand = false; S.focus = null; S.pathQueryId = null; }
  if (S.path.rel && !V.visRel.has(S.path.rel)) { delete S.path.rel; delete S.path.epi; }
  if (S.path.epi && !V.visEpi.has(S.path.epi)) delete S.path.epi;
  // ilhas soltas manualmente (S.offsets) são um deslocamento fixo em pixels a partir da posição natural
  // da vez: se o que está acima delas muda de tamanho (outro filtro, outra iniciativa, outra busca), o
  // deslocamento antigo pode empurrar a ilha para cima do conteúdo novo. Como a posição só faz sentido
  // para a cadeia que estava sendo vista quando foi arrastada, ela é descartada sempre que a combinação
  // de filtros/caminho que molda o que aparece muda.
  const sig = offsetsSig();
  if (sig !== S.offsetsSig){ if (Object.keys(S.offsets).length) S.offsets = {}; S.offsetsSig = sig; }

  S.links = [];
  let html = "";
  const team = S.f.team;
  // itens ocultos só pelo(s) filtro(s) ativo(s) (decisão `0050`): comparado contra a visibilidade sem
  // nenhum filtro — um item ausente dos dois (épico inválido, sem itens, etc.) nunca apareceria de
  // qualquer forma, então não entra como "oculto pelo filtro". Só calculado quando há filtro ativo,
  // pra não pagar o custo de rodar computeVisible() de novo à toa.
  const VAll = activeFilters().length ? computeVisibleAll() : V;

  // Nível 1: Iniciativas
  const iniList = [...V.visIni].map(id => M.inis.get(id));
  const iniHidden = VAll === V ? [] : [...VAll.visIni].filter(id => !V.visIni.has(id)).map(id => M.inis.get(id));
  const collapsed = !!S.path.ini && !S.showAllIni;
  const iniShown = collapsed ? iniList.filter(i => i.id === S.path.ini) : iniList;
  const iniOthers = iniList.length - 1;
  const iniCtx = !S.path.ini || !iniOthers ? null : collapsed
    ? `mostrando só a selecionada — marque “Manter todas as iniciativas visíveis” para ver as outras ${iniOthers}`
    : `mostrando todas — as outras ${iniOthers} ficam sem foco`;
  html += lane("ini", iniShown, M.stages.ini, it => it.st >= 0 ? M.stages.ini[it.st] : null, iniCtx, statsIni(iniList, V), false, "", iniHidden);

  if (!iniList.length){
    S.emptyDiag = activeFilters().length ? diagnoseEmpty() : null;
    html += S.emptyDiag
      ? `<div class="empty-state diag"><h2>Nada corresponde aos filtros</h2><div class="diag-box">${diagHtml(S.emptyDiag)}</div></div>`
      : `<div class="empty-state"><h2>Nada corresponde aos filtros</h2><p>Remova um dos filtros acima para ver iniciativas. Lembre que os filtros se somam.</p></div>`;
  }

  // Nível 2: Releases
  if (S.path.ini){
    const ini = M.inis.get(S.path.ini);
    const relList = ini.rels.filter(id => V.visRel.has(id)).map(id => M.rels.get(id));
    const relHidden = VAll === V ? [] : ini.rels.filter(id => VAll.visRel.has(id) && !V.visRel.has(id)).map(id => M.rels.get(id));
    relList.forEach(r => S.links.push(["ini:"+ini.id, "rel:"+r.id, healthRel(r,V)]));
    if (S.showHidden.rel) relHidden.forEach(r => S.links.push(["ini:"+ini.id, "rel:"+r.id, healthRel(r,V)]));
    html += lane("rel", relList, M.stages.rel, it => it.st >= 0 ? M.stages.rel[it.st] : null,
      `da iniciativa #${esc(ini.id)} ${esc(ini.title)}`, statsRel(relList), false,
      !ini.rels.length ? "Iniciativa sem release: nenhuma release tem esta iniciativa como Parent." : "", relHidden);

    // Nível 3: Épicos
    const relSrc = S.expand ? relList : (S.path.rel ? [M.rels.get(S.path.rel)] : []);
    if (relSrc.length){
      const epiList = [], epiHidden = [];
      relSrc.forEach(r => r.epis.filter(id => V.visEpi.has(id)).forEach(id => {
        const e = M.epis.get(id); epiList.push(e); S.links.push(["rel:"+r.id, "epi:"+e.id, healthEpi(e)]);
      }));
      if (VAll !== V) relSrc.forEach(r => r.epis.filter(id => VAll.visEpi.has(id) && !V.visEpi.has(id)).forEach(id => {
        const e = M.epis.get(id); epiHidden.push(e);
        if (S.showHidden.epi) S.links.push(["rel:"+r.id, "epi:"+e.id, healthEpi(e)]);
      }));
      const ctx = S.expand ? `de todas as releases da iniciativa #${esc(ini.id)}` : `da release #${esc(relSrc[0].id)} ${esc(relSrc[0].title)}`;
      html += lane("epi", epiList, M.stages.epi, it => it.st >= 0 ? M.stages.epi[it.st] : null, ctx, statsEpi(epiList), false,
        relSrc.length === 1 && !relSrc[0].epis.length ? "Release sem épico: nenhum épico tem esta release como Parent." : "", epiHidden);

      // Nível 4: Operacional
      const epiSrc = S.expand ? epiList : (S.path.epi ? [M.epis.get(S.path.epi)] : []);
      if (epiSrc.length){
        const opList = [];
        // no modo cadeia completa: um barbante por épico × ilha do time; item a item só para o épico em foco
        let focusEpi = null;
        if (S.expand && S.focus){
          const [fl, ...fr] = S.focus.split(":");
          if (fl === "epi") focusEpi = fr.join(":");
          if (fl === "op"){ const fo = M.ops.get(S.focus); if (fo) focusEpi = fo.epicoId; }
        }
        epiSrc.forEach(e => {
          const mine = e.ops.filter(k => V.visOp.has(k)).map(k => M.ops.get(k));
          mine.forEach(o => opList.push(o));
          if (!S.expand || e.id === focusEpi){ mine.forEach(o => S.links.push(["epi:"+e.id, o.key, o.health])); return; }
          const byTeam = new Map();
          mine.forEach(o => { if (!byTeam.has(o.team)) byTeam.set(o.team, []); byTeam.get(o.team).push(o.health); });
          byTeam.forEach((hs, tm) => S.links.push(["epi:"+e.id, "isl:"+tm, worst(hs)]));
        });
        const ctx2 = S.expand ? `de todos os épicos da iniciativa #${esc(ini.id)}` : `do épico #${esc(epiSrc[0].id)} ${esc(epiSrc[0].title)}`;
        html += lane("op", opList, M.stages.op, it => it.stName, ctx2 + (team ? `, somente ${esc(team)}` : ""), statsOp(opList), true);
      } else if (!S.expand) {
        html += `<p class="hint">Clique em um épico para ver os itens dos times vinculados a ele.</p>`;
      }
    } else {
      html += `<p class="hint">Clique em uma release para descer para os épicos, ou use “Abrir cadeia completa”.</p>`;
    }
  } else if (iniList.length) {
    html += `<p class="hint">Clique em uma iniciativa para puxar o barbante até as releases.</p>`;
  }

  board.innerHTML = `<div id="strings"></div><div id="pins"></div>` + html;
  applyOffsets();
  applyFocus();
  renderCrumbs();
  $("btnExpand").disabled = !S.path.ini;
  $("btnExpand").classList.toggle("on", S.expand);
  $("btnExpand").textContent = S.expand ? "Voltar ao passo a passo" : "Abrir cadeia completa";
  $("btnHygiene").textContent = `Higiene de dados (${hygieneCount()})`;
  renderTeamNav();
  markActiveFilters();
  renderAnalytics();
  renderF4P();
  renderActionable();
  if (S.lastFilterEl){
    const el = S.lastFilterEl; S.lastFilterEl = null;
    if (!iniList.length && S.emptyDiag) requestAnimationFrame(() => showFmsg(el, diagHtml(S.emptyDiag)));
    else if (!$("fmsg").hidden && $("fmsg").dataset.src === "diag") hideFmsg();
  }
  redraw();
}

const WRAP_ROWS = 6;   // acima disso, a coluna quebra em subcolunas
function island(team, items){
  const M = S.model, stages = M.teamFlow[team] || M.stages.op;
  const by = new Map(stages.map(s => [norm(s), []])), none = [];
  items.forEach(o => { const k = norm(o.stName); by.has(k) ? by.get(k).push(o) : none.push(o); });
  let cols = [...(none.length ? [{name:"Sem status", items:none}] : []), ...stages.map(s => ({name:s, items:by.get(norm(s))}))];
  const nEmpty = cols.filter(c => !c.items.length).length;
  if (!S.showEmpty) cols = cols.filter(c => c.items.length);
  const sub = c => Math.max(1, Math.ceil(c.items.length / WRAP_ROWS));
  const tmpl = cols.map(c => c.items.length ? `${sub(c) * 200 + (sub(c) - 1) * 30}px` : "40px").join(" ");
  let g = `<div class="grid" style="grid-template-columns:${tmpl}">`;
  cols.forEach(c => g += `<div class="colhead ${c.items.length ? "" : "empty"}" title="${esc(c.name)}"><span>${esc(c.name)}</span><span class="n">${c.items.length || ""}</span></div>`);
  cols.forEach(c => {
    const w = c.items.length > WRAP_ROWS;
    g += `<div class="cell ${c.items.length ? "" : "empty"} ${w ? "wrap" : ""}"${w ? ` style="grid-template-rows:repeat(${WRAP_ROWS},auto)"` : ""}>${c.items.map(card).join("")}</div>`;
  });
  g += `</div>`;
  const wip = items.filter(o => o.ready && !o.deploy).length;
  const cts = items.map(o => o.ct).filter(v => v != null);
  const avg = cts.length ? Math.round(cts.reduce((a,b)=>a+b,0) / cts.length) + " d" : "--";
  const colW = cols.map(c => c.items.length ? sub(c) * 200 + (sub(c) - 1) * 30 : 40);
  const w = colW.reduce((a,b)=>a+b,0) + 30 * Math.max(0, cols.length - 1) + 35;
  return {team, n: items.length, w: Math.max(w, 330), html: `<div class="island" data-team="${esc(team)}" data-key="isl:${esc(team)}" data-move="isl:${esc(team)}"><div class="isl-head"><h3>${esc(team)} <span class="n">${items.length}</span></h3>
    ${!S.showEmpty && nEmpty ? `<span class="hidden-note">${nEmpty} ${nEmpty === 1 ? "etapa vazia oculta" : "etapas vazias ocultas"}</span>` : ""}
    <span class="st"><span><b>${wip}</b> em andamento</span><span>CT médio <b>${avg}</b></span></span></div>${g}</div>`};
}
/* Distribui as ilhas em fileiras equilibradas e centralizadas:
   maiores primeiro, first-fit decrescente, e a maior de cada fileira no meio. */
function packIslands(isls){
  const GAP = 44;
  const total = isls.reduce((a,i)=>a + i.w, 0) + GAP * Math.max(0, isls.length - 1);
  const maxW = Math.max(...isls.map(i=>i.w));
  const target = Math.max(maxW, Math.min(total, Math.max(2400, vp.clientWidth / Math.max(Z, .5))));
  const sorted = [...isls].sort((a,b) => b.w - a.w || b.n - a.n);
  const rows = [];
  sorted.forEach(i => {
    const r = rows.find(r => r.w + GAP + i.w <= target);
    if (r){ r.items.push(i); r.w += GAP + i.w; } else rows.push({w:i.w, items:[i]});
  });
  // dentro da fileira: maior no centro, as demais alternando lados
  rows.forEach(r => { const out = []; r.items.forEach((it,k) => k % 2 ? out.unshift(it) : out.push(it)); r.items = out.reverse(); });
  return rows;
}
function lane(lvl, items, stages, stageOf, ctx, stats, swim, emptyMsg, hidden){
  const M = S.model;
  hidden = hidden || [];
  const showingHidden = hidden.length && S.showHidden[lvl];
  if (swim){
    const teams = M.teams.filter(t => items.some(o => o.team === t));
    const rows = items.length ? packIslands(teams.map(t => island(t, items.filter(o => o.team === t)))) : [];
    S.opTeams = rows.flatMap(r => r.items).map(i => ({team:i.team, n:i.n}));
    const body = items.length ? `<div class="islands">${rows.map(r => `<div class="isl-row">${r.items.map(i => i.html).join("")}</div>`).join("")}</div>`
      : `<p class="hint" style="padding:6px 0">Nenhum item vinculado com os filtros atuais.</p>`;
    return `<section class="lane" data-lvl="${lvl}" id="lane-${lvl}"><div class="lane-inner">
    <header class="lane-head"><h2><span class="sw" style="background:${LVC[lvl]}"></span>${LV[lvl]} <span style="font-weight:400;color:var(--ink-3)">${items.length}</span></h2>
    ${ctx ? `<span class="ctx">${ctx}</span>` : ""}<span class="hidden-note">${teams.length} ${teams.length === 1 ? "time" : "times"}</span><div class="stats">${stats}</div></header></div>
    <div class="lane-scroll">${body}</div></section>`;
  }
  const byStage = new Map(); stages.forEach(s => byStage.set(norm(s), []));
  const noStatus = [];
  items.forEach(it => { const s = stageOf(it); if (s && byStage.has(norm(s))) byStage.get(norm(s)).push(it); else noStatus.push(it); });
  // itens ocultos pelo filtro (decisão `0050`), quando revelados: bucketados pela mesma coluna que
  // teriam se não estivessem filtrados, e desenhados junto com os visíveis (com `.dim`) — não entram em
  // `items`/`byStage`, então não afetam a contagem do cabeçalho nem as estatísticas da faixa.
  const hByStage = new Map(); stages.forEach(s => hByStage.set(norm(s), []));
  const hNoStatus = [];
  if (showingHidden) hidden.forEach(it => { const s = stageOf(it); if (s && hByStage.has(norm(s))) hByStage.get(norm(s)).push(it); else hNoStatus.push(it); });
  let cols = [...(noStatus.length || hNoStatus.length ? [{name:"Sem status", items:noStatus, hid:hNoStatus}] : []), ...stages.map(s => ({name:s, items:byStage.get(norm(s)), hid:hByStage.get(norm(s))}))];
  const nEmpty = cols.filter(c => !c.items.length).length;
  const hasContent = c => c.items.length || c.hid.length;
  if (!S.showEmpty && (items.length || showingHidden)) cols = cols.filter(hasContent);
  const widths = cols.map(c => hasContent(c) ? (lvl === "op" ? "200px" : "216px") : "40px");
  const tmpl = (swim ? "86px " : "") + widths.join(" ");

  let g = `<div class="grid" style="grid-template-columns:${tmpl}">`;
  if (swim) g += `<div></div>`;
  cols.forEach(c => g += `<div class="colhead ${hasContent(c) ? "" : "empty"}" title="${esc(c.name)}"><span>${esc(c.name)}</span><span class="n">${c.items.length || ""}</span></div>`);
  if (swim){
    const teams = M.teams.filter(t => items.some(o => o.team === t));
    teams.forEach((t,ti) => {
      if (ti) g += `<div class="rowline"></div>`;
      g += `<div class="teamlab">${esc(t)}</div>`;
      cols.forEach(c => { const its = c.items.filter(o => o.team === t); g += `<div class="cell ${c.items.length ? "" : "empty"}">${its.map(card).join("")}</div>`; });
    });
  } else {
    cols.forEach(c => g += `<div class="cell ${hasContent(c) ? "" : "empty"}">${c.items.map(it => card(it)).join("")}${c.hid.map(it => card(it, true)).join("")}</div>`);
  }
  g += `</div>`;
  const tf = S.f.team && lvl !== "ini" ? "" : "";
  const hideToggle = hidden.length ? `<button type="button" class="hide-toggle" data-hide-toggle="${lvl}" title="${hidden.length} ${hidden.length === 1 ? "item ocultado" : "itens ocultados"} pelo(s) filtro(s) ativo(s)">${S.showHidden[lvl] ? `− ${hidden.length} ocultos` : `+ ${hidden.length} ocultos`}</button>` : "";
  return `<section class="lane" data-lvl="${lvl}" id="lane-${lvl}"><div class="lane-inner isle" data-move="lvl:${lvl}" style="--lc:${LVC[lvl]}">
    <header class="lane-head"><h2><span class="sw" style="background:${LVC[lvl]}"></span>${LV[lvl]} <span style="font-weight:400;color:var(--ink-3)">${items.length}</span></h2>
    ${ctx ? `<span class="ctx">${ctx}</span>` : ""}${hideToggle}${!S.showEmpty && items.length && nEmpty ? `<span class="hidden-note">${nEmpty} ${nEmpty === 1 ? "etapa vazia oculta" : "etapas vazias ocultas"}</span>` : ""}<div class="stats">${stats}</div></header>
    <div class="lane-scroll">${items.length || showingHidden ? g : `<p class="hint" style="padding:6px 0">${emptyMsg || "Nenhum item vinculado com os filtros atuais."}</p>`}</div>${tf}</div></section>`;
}

function card(it, forceDim){
  const M = S.model, V = S.V, team = S.f.team;
  if (it.lvl === "ini"){
    const nRel = it.rels.filter(id => V.visRel.has(id)).length;
    const interno = [...new Set(it.rels.flatMap(rid => M.rels.get(rid).epis.filter(e=>V.visEpi.has(e)).map(e => M.epis.get(e).interno).filter(Boolean)))].sort();
    const div = interno.some(s => it.exec && norm(s) !== norm(it.exec));
    const h = healthIni(it, V);
    const sel = S.path.ini === it.id, dim = forceDim || (!sel && S.path.ini && S.showAllIni);
    return `<button class="card lvl-ini ${sel ? "sel" : dim ? "dim" : ""}" data-key="ini:${esc(it.id)}" style="${stripeStyle(it)}">
      <div class="c-top"><span class="c-id">#${esc(it.id)}</span>${it.type ? `<span class="c-type">${esc(it.type)}</span>` : ""}<span class="h ${h}" title="${hTitle(h)}"></span></div>
      <div class="c-title">${esc(it.title)}</div>
      ${it.owner ? `<div class="c-meta" style="margin:-2px 0 5px">${esc(it.owner)}</div>` : ""}
      <div class="c-meta"><span class="tag">Exec ${esc(shortSem(it.exec))}</span>${interno.length ? `<span class="tag ${div ? "div" : ""}" title="Roadmap interno (Target Date dos épicos)">Int ${interno.map(shortSem).join(", ")}</span>` : ""}</div>${extraHtml(it)}
      <div class="kids" style="align-items:center"><span>${nRel} ${nRel === 1 ? "release" : "releases"}</span>${(ph => `<span class="ph ${ph}" title="${SIT_TIP[ph]}">${SIT_LABEL[ph]}</span>`)(iniPhase(it, V))}</div></button>`;
  }
  if (it.lvl === "rel"){
    const nEpi = it.epis.filter(id => V.visEpi.has(id)).length;
    const h = healthRel(it, V);
    const sel = S.path.rel === it.id && !S.expand;
    return `<button class="card lvl-rel ${sel ? "sel" : forceDim ? "dim" : ""}" data-key="rel:${esc(it.id)}" style="${stripeStyle(it)}">
      <div class="c-top"><span class="c-id">#${esc(it.id)}</span>${it.type ? `<span class="c-type">${esc(it.type)}</span>` : ""}<span class="h ${h}" title="${hTitle(h)}"></span></div>
      <div class="c-title">${esc(it.title)}</div>
      <div class="c-meta">${it.owner ? `<span>${esc(it.owner)}</span>` : ""}</div>${extraHtml(it)}
      <div class="kids" style="align-items:center"><span>${nEpi} ${nEpi === 1 ? "épico" : "épicos"}</span>${(ph => `<span class="ph ${ph}" title="${SIT_TIP[ph]}">${SIT_LABEL[ph]}</span>`)(relPhase(it, V))}</div></button>`;
  }
  if (it.lvl === "epi"){
    const m = epiMetrics(it, team);
    const h = healthEpi(it);
    const sel = S.path.epi === it.id && !S.expand;
    return `<button class="card lvl-epi ${sel ? "sel" : forceDim ? "dim" : ""}" data-key="epi:${esc(it.id)}" style="${stripeStyle(it)}">
      <div class="c-top"><span class="c-id">#${esc(it.id)}</span>${it.type ? `<span class="c-type">${esc(it.type)}</span>` : ""}${team ? `<span class="tag team" title="Cálculos só com registros do time ${esc(team)}">visão ${esc(team)}</span>` : ""}<span class="h ${h}" title="${hTitle(h)}"></span></div>
      <div class="c-title">${esc(it.title)}</div>
      <div class="c-meta"><span>Target <b>${fmt(it.target)}</b></span><span title="${esc("CT" + ctRange(m) + ", " + ctTip(m))}">CT <b>${m.ct ?? "--"}</b>${m.ct != null ? " d" : ""}</span><span>Ag. Deploy <b>${fmt(m.ag)}</b></span>
      ${distGroup(m)}
      ${Object.keys(m.tagCount).length ? `<span class="tgs" style="margin:2px 0 0;width:100%">${(CFG.tags || []).filter(x => m.tagCount[x.id]).map(x => `<span class="tchp" style="background:${x.color};color:${inkOn(x.color)}" title="${m.tagCount[x.id]} ${m.tagCount[x.id] === 1 ? "item aberto" : "itens abertos"} com ${esc(x.name)} nos times">${esc(x.name)} ${m.tagCount[x.id]}</span>`).join("")}</span>` : ""}
      ${it.diverge ? `<span class="tag div" title="Roadmap interno diferente do executivo da iniciativa">Int ${esc(shortSem(it.interno))} ≠ Exec ${esc(shortSem(it.exec))}</span>` : ""}</div>${extraHtml(it)}
      <div class="kids" style="align-items:center">${distBar(m)}<span class="ph ${m.phase}" title="Fase pelos itens vinculados nos times">${PHASE_LABEL[m.phase]}</span></div></button>`;
  }
  // operacional: fundo pela primeira tag cadastrada encontrada
  const tg = (it.tagHits || []).find(x => x.color);
  const style = ` style="${tg ? `background:${tg.color};--tagfg:${inkOn(tg.color)};` : ""}${stripeStyle(it)}"`;
  return `<button class="card lvl-op${tg ? " tagged" + (inkOn(tg.color) === "#fff" ? " dark" : "") : ""}" data-key="${esc(it.key)}"${style}>
    <div class="c-top"><span class="c-id">#${esc(it.id)}</span><span>${esc(it.type ?? "")}</span><span class="h ${it.health}" title="${hTitle(it.health)}"></span></div>
    <div class="c-title">${esc(it.title)}</div>
    <div class="c-meta"><span title="${esc(it.ctCols ? "Entrada do CT: " + it.ctCols.entry : "")}">${ctLabels()[0]} <b>${fmt(it.ready)}</b></span><span title="${esc(it.ctCols ? "Saída do CT: " + it.ctCols.exit : "")}">${ctLabels()[1]} <b>${fmt(it.deploy)}</b></span><span>CT <b>${it.ct ?? "--"}</b>${it.ct != null ? " d" : ""}</span>${it.outlier ? `<span class="tag out" title="${esc(it.reasons[0].text)}">outlier</span>` : it.overCt ? `<span class="tag div" title="${esc(it.reasons[0].text)}">atraso no CT</span>` : ""}${it.stuck != null ? `<span class="tag stuck" title="Parado na mesma coluna">parado ${it.stuck} d</span>` : ""}</div>${extraHtml(it)}${(it.tagHits || []).length ? `<div class="tgs">${it.tagHits.map(x => `<span class="tchp" style="background:${x.color};color:${inkOn(x.color)}">${esc(x.name)}</span>`).join("")}</div>` : ""}</button>`;
}
/* cor de texto legível sobre um fundo */
function inkOn(hex){
  const m = /^#?([0-9a-f]{6})$/i.exec(hex || ""); if (!m) return "#1D2730";
  const n = parseInt(m[1], 16), c = [n >> 16, (n >> 8) & 255, n & 255].map(v => { v /= 255; return v <= .03928 ? v / 12.92 : Math.pow((v + .055) / 1.055, 2.4); });
  const L = .2126 * c[0] + .7152 * c[1] + .0722 * c[2];
  return L < .28 ? "#fff" : "#1D2730";
}
const LVL_HEX = {ini:"#34489A", rel:"#16786A", epi:"#9A6512", op:"#5A6570"};
const stripeOf = it => (it.type && (CFG.typeColors || {})[it.lvl] || {})[norm(it.type || "")] || null;
const stripeStyle = it => { const c = stripeOf(it); return c ? `border-top-color:${c};` : ""; };
function fmtField(key, v){
  if (!filled(v)) return "--";
  if (/date|data/.test(key)){ const d = toDate(v); if (d) return fmtL(d); }
  let s = String(v).trim();
  if (/^\[.*\]$/.test(s)) s = s.slice(1, -1).split("|").map(x => x.trim()).filter(Boolean).join(", ") || "--";
  s = s.replace(/\s*<[^>]*@[^>]*>/g, "");
  if (/^(true|false)$/i.test(s)) s = /^true$/i.test(s) ? "sim" : "não";
  return s || "--";
}
/* campos adicionais escolhidos nas Configurações, abaixo do conteúdo padrão do card */
function extraHtml(it){
  const sel = ((CFG.fields || {})[it.lvl] || []), names = (S.model.fieldsAvail || {})[it.lvl] || {};
  const list = sel.filter(k => names[k]); if (!list.length) return "";
  return `<div class="c-extra">${list.map(k => { const v = fmtField(k, (it.x || {})[k]);
    return `<div title="${esc(names[k])}: ${esc(v)}"><span>${esc(names[k])}</span><b>${esc(v)}</b></div>`; }).join("")}</div>`;
}
const hTitle = h => h === "outlier" ? "Outlier: clique no card para ver o motivo no painel de detalhes" : h === "alert" ? "Alerta: clique no card para ver o motivo no painel de detalhes" : h === "warn" ? "Atenção: clique no card para ver o motivo no painel de detalhes" : "No fluxo";

/* estatísticas por nível */
function statsIni(list, V){
  const last = S.model.stages.ini.length - 1;
  const done = list.filter(i => i.st === last).length;
  const al = list.filter(i => healthIni(i,V) === "alert").length;
  return `<span><b>${done}</b> concluídas</span><span><b>${al}</b> com alerta</span>`;
}
function statsRel(list){
  const last = S.model.stages.rel.length - 1;
  return `<span><b>${list.filter(r => r.st === last).length}</b> entregues</span>`;
}
function statsEpi(list){
  const cts = list.map(e => epiMetrics(e, S.f.team).ct).filter(v => v != null);
  const avg = cts.length ? Math.round(cts.reduce((a,b)=>a+b,0) / cts.length) : "--";
  return `<span>CycleTime médio <b>${avg}</b>${cts.length ? " d" : ""}</span><span><b>${list.filter(e=>e.diverge).length}</b> com roadmap divergente</span>`;
}
function statsOp(list){
  const wip = list.filter(o => o.ready && !o.deploy);
  const cts = list.map(o=>o.ct).filter(v=>v!=null);
  const avg = cts.length ? Math.round(cts.reduce((a,b)=>a+b,0)/cts.length) : "--";
  return `<span><b>${wip.length}</b> em andamento</span><span>CycleTime médio <b>${avg}</b>${cts.length ? " d" : ""}</span><span><b>${list.filter(o=>o.health!=="ok").length}</b> envelhecendo</span>`;
}

