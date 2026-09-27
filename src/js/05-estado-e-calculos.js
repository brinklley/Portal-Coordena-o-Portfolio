/* ---------------- estado ---------------- */
const S = {model:null, f:{exec:"",owners:new Set(),int:"",team:"",q:""}, path:{}, pathQueryId:null, expand:false, focus:null, links:[], animateLevel:null, showEmpty:true, showBare:true, anchored:true, offsets:{}};

/* Fase do épico pelos itens vinculados:
   Fechado = todos em Vazão; WIP = algum em WIP (ou já entregou parte e o resto ainda não começou);
   Discovery = algum em Discovery e nenhum em WIP; Backlog = nenhum iniciado. */
function phaseOf(m){
  if (!m.n) return "vazio";
  if (m.vaz === m.n) return "fechado";
  if (m.wip > 0) return "wip";
  if (m.disc > 0) return "discovery";
  if (m.vaz > 0) return "wip";
  return "backlog";
}
const PHASE_LABEL = {vazio:"sem itens", backlog:"Backlog", discovery:"Discovery", wip:"WIP", fechado:"Fechado"};
/* legenda com a contagem por categoria (Backlog/Discovery/WIP/Vazão) do épico — o "agrupador" do card
   do épico no quadro (kids/c-meta); reaproveitado também pela Visão analítica (coluna Status). */
function distGroup(m){
  return `<span title="Itens vinculados em colunas configuradas como Nenhum (ainda não iniciados)"><i class="sq none"></i>Backlog <b>${m.none}</b></span><span title="Itens vinculados que já começaram, nas colunas configuradas como Discovery"><i class="sq disc"></i>Discovery <b>${m.disc}</b></span><span title="Itens vinculados nas colunas configuradas como WIP"><i class="sq wip"></i>WIP <b>${m.wip}</b></span><span title="Itens vinculados nas colunas configuradas como Vazão"><i class="sq vaz"></i>Vazão <b>${m.vaz}</b></span>`;
}
function distBar(m){
  if (!m.n) return `<span class="dist"></span>`;
  const parts = [["none", m.none, "Backlog/outras"], ["disc", m.disc, "Discovery"], ["wip", m.wip, "WIP"], ["vaz", m.vaz, "Vazão"]];
  const tip = `${m.n} ${m.n === 1 ? "item" : "itens"} nos times: ` + parts.filter(p => p[1]).map(p => `${p[2]} ${p[1]}`).join(", ");
  // até 30 itens: um traço por item; acima disso, faixas proporcionais
  const body = m.n <= 30
    ? parts.flatMap(([c, k]) => Array.from({length:k}, () => `<i class="${c}"></i>`)).join("")
    : parts.filter(p => p[1]).map(([c, k]) => `<i class="${c}" style="flex-grow:${k}"></i>`).join("");
  return `<span class="dist ${m.n > 30 ? "cont" : ""}" title="${esc(tip)}" role="img" aria-label="${esc(tip)}">${body}</span>`;
}
/* Situação herdada dos filhos: Fechado só quando todos os filhos visíveis estão Fechados;
   qualquer filho em Backlog, Discovery, WIP ou sem itens deixa o pai Aberto. */
function relPhase(r, V){
  if (!r.epis.length) return "semepi";
  const eps = r.epis.filter(id => V.visEpi.has(id)).map(id => S.model.epis.get(id));
  return eps.length && eps.every(e => epiMetrics(e, S.f.team).phase === "fechado") ? "fechado" : "aberto";
}
function iniPhase(i, V){
  if (!i.rels.length) return "semrel";
  const rs = i.rels.filter(id => V.visRel.has(id)).map(id => S.model.rels.get(id));
  return rs.length && rs.every(r => relPhase(r, V) === "fechado") ? "fechado" : "aberto";
}
const SIT_LABEL = {aberto:"Aberto", fechado:"Fechado", semrel:"sem release", semepi:"sem épico"};
const SIT_TIP = {aberto:"Aberto: há filhos que ainda não chegaram ao fim do fluxo", fechado:"Fechado: todos os filhos estão fechados",
  semrel:"Iniciativa sem release: nenhuma release tem esta iniciativa como Parent", semepi:"Release sem épico: nenhum épico tem esta release como Parent"};
const ctTypesLabel = () => (CFG.ctTypes || []).map(x => x.replace(/\b\w/g, c => c.toUpperCase())).join(", ") || "todos os tipos";
const ctRange = m => m.ctFrom ? ` de ${fmtL(m.ctFrom)} a ${m.ctTo ? fmtL(m.ctTo) : "hoje"}` : "";
const ctTip = m => m.ctN ? `calculado com ${m.ctN} ${m.ctN === 1 ? "item" : "itens"} do tipo ${ctTypesLabel()}` : `sem itens do tipo ${ctTypesLabel()} para calcular o CT`;
function epiMetrics(e, team){
  const recs = e.ops.map(k => S.model.ops.get(k)).filter(o => !team || o.team === team);
  if (!recs.length) return {n:0, ag:null, ct:null, ctN:0, ctOpen:[], agMissing:[], health:"ok", recs, disc:0, wip:0, vaz:0, none:0, phase:"vazio", tagCount:{}};
  const allDep = recs.every(o => o.deploy);
  const ag = allDep ? new Date(Math.max(...recs.map(o=>o.deploy))) : null;
  // CycleTime do épico: só itens dos tipos configurados (padrão: User Story e Technical Story)
  const ctSet = new Set((CFG.ctTypes || []).map(norm));
  const ctRecs = ctSet.size ? recs.filter(o => o.type && ctSet.has(norm(o.type))) : recs;
  const started = ctRecs.filter(o => o.ready);
  let ct = null, ctFrom = null, ctTo = null, ctFromOp = null, ctToOp = null, ctOpen = [];
  if (started.length){
    ctFromOp = started.reduce((a, o) => o.ready < a.ready ? o : a);
    ctFrom = ctFromOp.ready;
    ctOpen = ctRecs.filter(o => !o.deploy);
    if (!ctOpen.length){ ctToOp = ctRecs.reduce((a, o) => o.deploy > a.deploy ? o : a); ctTo = ctToOp.deploy; }
    ct = days(ctFrom, ctTo || TODAY);
  }
  const agMissing = recs.filter(o => !o.deploy);
  const cats = recs.map(catOf), cnt = c => cats.filter(x => x === c).length;
  const disc = cnt("disc"), wip = cnt("wip"), vaz = cnt("vazao"), none = recs.length - disc - wip - vaz;
  const tagCount = {}; recs.forEach((o, i) => (o.tagHits || []).forEach(tg => { if (cats[i] !== "vazao") tagCount[tg.id] = (tagCount[tg.id] || 0) + 1; }));
  return {n:recs.length, ag, ct, ctN:ctRecs.length, ctFrom, ctTo, ctFromOp, ctToOp, ctOpen, agMissing, health: worst(recs.map(o=>o.health)), recs, disc, wip, vaz, none, phase: phaseOf({n:recs.length, disc, wip, vaz}), tagCount};
}

/* Visibilidade: filtros cumulativos (AND) a partir dos Épicos válidos */
const lastStage = lvl => S.model.stages[lvl].length - 1;
const bareRel = r => r.valid && !r.epis.length && r.st !== lastStage("rel");     // release sem épico, não entregue
const bareIni = i => !i.rels.length && i.st !== lastStage("ini");                 // iniciativa sem release, não concluída
/* pode aparecer no quadro (com a opção ligada)? usado nas listas dos filtros */
const iniCanAppear = i => i.rels.some(id => { const r = S.model.rels.get(id); return r.epis.length || bareRel(r); }) || bareIni(i);
/* filtro único "ID ou descrição" (decisão 0034): substitui os antigos campos separados de
   Iniciativa (ID ou nome) e "Ir para qualquer ID". Casa por ID exato OU por texto no título,
   em qualquer nível (iniciativa, release, épico ou item de time) — quem casar revela a cadeia
   inteira até a iniciativa; quando só um item de time casa, só ele aparece na lista do épico. */
function computeVisible(){
  const M = S.model, f = S.f;
  const q = norm(f.q), qId = f.q ? nid(f.q) : null;
  const visEpi = new Set(), visRel = new Set(), visIni = new Set(), visOp = new Set();
  const qHit = (id, title) => !q || id === qId || norm(title).includes(q);
  const passIni = i => !(f.exec && norm(i.exec) !== norm(f.exec)) && !(f.owners.size && !f.owners.has(i.owner ? norm(i.owner) : "__none__"));
  M.epis.forEach(e=>{
    if (!e.valid) return;
    const r = M.rels.get(e.parent); if (!r.valid) return;
    const i = M.inis.get(r.parent); if (!i) return;
    if (!passIni(i)) return;
    if (f.int && norm(e.interno) !== norm(f.int)) return;
    if (f.team && !e.ops.some(k => M.ops.get(k).team === f.team)) return;
    const iniHit = qHit(i.id, i.title), relHit = qHit(r.id, r.title), epiHit = qHit(e.id, e.title);
    const opHits = e.ops.filter(k => qHit(M.ops.get(k).id, M.ops.get(k).title));
    if (!iniHit && !relHit && !epiHit && !opHits.length) return;
    visEpi.add(e.id); visRel.add(r.id); visIni.add(i.id);
    const showAll = iniHit || relHit || epiHit;
    e.ops.forEach(k => {
      if (f.team && M.ops.get(k).team !== f.team) return;
      if (!showAll && !opHits.includes(k)) return;
      visOp.add(k);
    });
  });
  // itens sem desdobramento: releases sem épico e iniciativas sem release (não concluídas);
  // os filtros de Time e Roadmap interno dependem dos épicos, então esses itens ficam de fora com eles
  if (S.showBare && !f.int && !f.team){
    M.rels.forEach(r => { if (!bareRel(r)) return; const i = M.inis.get(r.parent); if (!passIni(i)) return;
      if (!qHit(i.id, i.title) && !qHit(r.id, r.title)) return;
      visRel.add(r.id); visIni.add(i.id); });
    M.inis.forEach(i => { if (!bareIni(i) || !passIni(i)) return; if (!qHit(i.id, i.title)) return; visIni.add(i.id); });
  }
  return {visEpi, visRel, visIni, visOp};
}

/* saúde agregada (considerando visibilidade e filtro de time) */
function healthEpi(e){ const m = epiMetrics(e, S.f.team); return e.diverge ? "alert" : m.health; }
function healthRel(r, V){ return worst(r.epis.filter(id=>V.visEpi.has(id)).map(id=>healthEpi(S.model.epis.get(id)))); }
function healthIni(i, V){ return worst(i.rels.filter(id=>V.visRel.has(id)).map(id=>healthRel(S.model.rels.get(id), V))); }

