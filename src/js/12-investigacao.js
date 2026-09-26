/* ---------- investigação: por que um ID não aparece no quadro ---------- */
function investigate(q){
  const M = S.model, id = nid(q), steps = [], az = S.importNotes && S.importNotes.azure;
  const add = (ok, title, text, action) => steps.push({ok, title, text, action});
  const roleName = {ini:"Iniciativa", rel:"Release", epi:"Épico", op:"Item de time"};
  // 1. veio nos dados carregados?
  const where = [];
  Object.entries(S.tables || {}).forEach(([sheet, tb]) => { const i = (tb.headers || []).findIndex(h => norm(h) === "id");
    if (i >= 0 && tb.rows.some(r => nid(r[i]) === id)) where.push(sheet); });
  const removed = az && (az.removedIds || []).find(x => x.split(":")[1] === id);
  const origin = az ? ["na carga do Azure DevOps", "a carga do Azure DevOps"] : S.isDemo ? ["nos dados de exemplo", "os dados de exemplo"] : ["na planilha carregada", "a planilha carregada"];
  if (where.length) add(true, "Retornou nos dados", `Encontrado ${origin[0]}, na aba ${where.join(", ")}.`);
  else if (removed){ add(false, "Retornou do Azure, mas foi excluído na carga", `O item está no estado Removed e a opção “Excluir itens no estado Removed” está ligada (${roleName[removed.split(":")[0]]}).`,
      "Se ele não deveria estar removido, ajuste o estado no Azure DevOps. Para incluir itens removidos, desligue a opção em Configurações › Azure DevOps."); return steps; }
  else { add(false, "Não retornou nos dados", az
      ? "A carga do Azure não trouxe este ID. A consulta de cada fonte busca só os itens da Area Path do time configurado e dos tipos do nível de backlog escolhido."
      : `Este ID não está ${origin[0]}.`,
      az ? "No Azure DevOps, confira a Area Path e o tipo do item. Se o item aparece no quadro de outro time, ou se é de um tipo que não pertence ao nível configurado (ex.: Iniciativas), ajuste a fonte em Configurações › Azure DevOps ou o item no Azure. Depois, carregue de novo."
         : "Confira se a planilha é a mais recente e se o item está na aba certa."); return steps; }
  // 2. entrou no modelo?
  const ini = M.inis.get(id), rel = M.rels.get(id), epi = M.epis.get(id), op = [...M.ops.values()].find(o => o.id === id);
  const lvl = ini ? "ini" : rel ? "rel" : epi ? "epi" : op ? "op" : null;
  if (!lvl){ add(false, "Não foi reconhecido", "O ID está nos dados, mas numa aba que o portal não usa.", "Confira os nomes das abas (Iniciativa, Release, Épico e as abas dos times)."); return steps; }
  add(true, "Reconhecido pelo portal", `${roleName[lvl]}${lvl === "op" ? ` do time ${op.team}` : ""}: “${(ini || rel || epi || op).title || "(sem título)"}”.`);
  // 3. cadeia válida
  const bareOff = () => { add(false, "Oculto pela opção “Mostrar itens sem desdobramento”", "A opção está desligada na barra de filtros.", "Ligue a opção na barra de filtros."); return steps; };
  if (lvl === "ini"){
    if (!ini.rels.length){
      if (ini.st === lastStage("ini")){ add(false, "Iniciativa concluída sem release", "Iniciativas sem release que já estão na última coluna do fluxo ficam fora do quadro, para não trazer o histórico antigo do portfólio.", "Nenhuma ação é necessária, a menos que ela não devesse estar concluída."); return steps; }
      add(true, "Iniciativa sem release", "Nenhuma release tem esta iniciativa como Parent. Ela aparece no quadro com o selo “sem release”.");
      if (!S.showBare) return bareOff();
    } else if (!iniCanAppear(ini)){
      add(false, "Só tem releases entregues sem épico", `As ${ini.rels.length} release(s) vinculada(s) já estão entregues e não têm épico, por isso ficam fora do quadro, e a iniciativa junto.`, "Nenhuma ação é necessária se forem releases históricas."); return steps;
    } else add(true, "Vínculos", `${ini.rels.length} release(s) vinculada(s).`);
  }
  if (lvl === "rel"){
    if (!M.inis.has(rel.parent)){ add(false, "Fora da cadeia: iniciativa não encontrada", rel.parent ? `O Parent da release é #${rel.parent}, que não está entre as iniciativas carregadas.` : "A release não tem Parent.", "Vincule a release a uma iniciativa carregada, ou confira se a iniciativa está na fonte de Iniciativa."); return steps; }
    if (!rel.epis.length){
      if (rel.st === lastStage("rel")){ add(false, "Release entregue sem épico", "Releases sem épico que já estão na última coluna do fluxo ficam fora do quadro, para não trazer o histórico antigo.", "Nenhuma ação é necessária, a menos que ela não devesse estar entregue."); return steps; }
      add(true, "Release sem épico", `Ligada à iniciativa #${rel.parent}. Nenhum épico tem esta release como Parent; ela aparece com o selo “sem épico”.`);
      if (!S.showBare) return bareOff();
    } else add(true, "Cadeia válida", `Ligada à iniciativa #${rel.parent}, com ${rel.epis.length} épico(s).`);
  }
  if (lvl === "epi"){
    if (!epi.valid){ add(false, "Fora da cadeia: épico sem release válida", !epi.title ? "O épico está sem título." : epi.parent ? `O Parent do épico é #${epi.parent}, que não está entre as releases carregadas.` : "O épico não tem Parent.", "Vincule o épico a uma release carregada no Azure DevOps."); return steps; }
    add(true, "Cadeia válida", `Ligado à release #${epi.parent}.`);
  }
  if (lvl === "op"){
    const e = M.epis.get(op.epicoId);
    if (!e){ add(false, "Fora da cadeia: item órfão", op.epicoId ? `O ID_EPICO_UNICRED é ${op.epicoId}, que não está entre os épicos carregados.` : "O item está sem ID_EPICO_UNICRED (e sem link Remote Related).", "Preencha o campo ID EPICO UNICRED no item, com o ID de um épico carregado."); return steps; }
    if (!e.valid){ add(false, "Fora da cadeia: épico fora da cadeia", `O épico #${e.id} não está ligado a uma release válida.`, `Investigue o épico #${e.id}.`); return steps; }
    add(true, "Cadeia válida", `Ligado ao épico #${e.id}.`);
  }
  // 4. filtros
  const path = lvl === "ini" ? {ini:id} : lvl === "rel" ? {ini:rel.parent, rel:id} : lvl === "epi" ? {ini:M.rels.get(epi.parent).parent, rel:epi.parent, epi:id}
    : (() => { const e = M.epis.get(op.epicoId); return {ini:M.rels.get(e.parent).parent, rel:e.parent, epi:e.id}; })();
  const opKey = lvl === "op" ? op.key : null;
  if (!pathVisible(S.V, path, opKey)){
    const blk = blockingFilters(path, opKey), act = activeFilters();
    const bare = (lvl === "ini" && !ini.rels.length) || (lvl === "rel" && !rel.epis.length);
    add(false, "Escondido pelos filtros ativos", (blk.length ? act.filter(([k]) => blk.includes(k)) : act).map(([k, v]) => `${FILTER_LABEL[k]}: ${v}`).join("; ")
      + (bare && (S.f.team || S.f.int) ? ". Os filtros de Time e Roadmap interno dependem dos épicos, então itens sem desdobramento não aparecem com eles." : ""), "Remova esses filtros ou use “Limpar filtros”."); return steps;
  }
  add(true, "Visível com os filtros atuais", "Nenhum filtro esconde o item.");
  if (lvl === "ini" && S.path.ini && S.path.ini !== id && !S.showAllIni) add(false, "Recolhido na lista", "Outra iniciativa está selecionada, e as demais ficam recolhidas.", "Clique em “Mostrar todas” no nível de Iniciativas, ou use “Ir para qualquer ID”.");
  else add(true, "Deveria aparecer no quadro", "Use “Ir para qualquer ID” para ir até ele.");
  return steps;
}
function showInvestigation(q){
  const steps = investigate(q), fail = steps.find(s => !s.ok);
  $("dTitle").textContent = "Investigação do ID " + q; S.detailKey = null;
  $("dBody").innerHTML = `<p class="help" style="margin-top:0">Cada etapa, da origem dos dados até a tela. A investigação para na primeira etapa que falhar.</p>
    <ol class="inv">${steps.map(s => `<li class="${s.ok ? "ok" : "bad"}"><b>${s.ok ? "✓" : "✗"} ${esc(s.title)}</b><span>${esc(s.text)}</span>${s.action ? `<span class="inv-act"><b>O que fazer:</b> ${esc(s.action)}</span>` : ""}</li>`).join("")}</ol>
    ${!fail ? `<div class="acts"><button class="btn primary" data-inv-go="${esc(q)}">Ir para o item</button></div>` : ""}`;
  $("dBody").querySelectorAll("[data-inv-go]").forEach(b => b.onclick = () => gotoId(b.dataset.invGo));
  openDrawer();
}
document.addEventListener("click", e => { const b = e.target.closest("[data-investigate]"); if (b){ hideFmsg(); showInvestigation(b.dataset.investigate); } });

function gotoId(q){
  if (!q || !S.model) return;
  const M = S.model, V = S.V; const id = nid(q);
  let target = null, path = null;
  const opHit = [...M.ops.values()].find(o => o.id === id);
  if (M.inis.has(id)){ if (M.inis.get(id).valid) path = {ini:id}; target = "ini:"+id; }
  else if (M.rels.has(id)){ const r = M.rels.get(id); if (r.valid && M.inis.has(r.parent)) path = {ini:r.parent, rel:id}; target = "rel:"+id; }
  else if (M.epis.has(id)){ const e = M.epis.get(id); if (e.valid){ path = {ini:M.rels.get(e.parent).parent, rel:e.parent, epi:id}; } target = "epi:"+id; }
  else if (opHit){ const e = M.epis.get(opHit.epicoId); if (e && e.valid) path = {ini:M.rels.get(e.parent).parent, rel:e.parent, epi:e.id}; target = opHit.key; }
  const anchor = $("goto");
  const inv = `<div class="acts"><button class="btn primary" data-investigate="${esc(id)}">Investigar por que não aparece</button></div>`;
  if (!target) return showFmsg(anchor, `<b>ID ${esc(q)} não encontrado</b> nos dados carregados.${inv}`, "info");
  if (!path) return showFmsg(anchor, `<b>O ID ${esc(q)} existe, mas está fora da cadeia válida</b> (falta o vínculo com épico, release ou iniciativa), por isso não aparece no quadro.${inv}`, "info");
  const opKey = target.startsWith("op:") ? target : null;
  if (!pathVisible(V, path, opKey)){
    const act = activeFilters(), blk = blockingFilters(path, opKey);
    if (!blk.length && !pathVisible(withFilters({exec:"", owners:new Set(), int:"", team:"", ini:""}, () => computeVisible()), path, opKey))
      return showFmsg(anchor, `<b>O ID ${esc(q)} existe, mas não aparece no quadro</b> por uma regra de exibição, e não por filtro.${inv}`, "info");
    const lines = (blk.length ? act.filter(([k]) => blk.includes(k)) : act).map(([k, v]) => `<li>${FILTER_LABEL[k]}: <b>${esc(v)}</b></li>`).join("");
    showFmsg(anchor, `<b>O ID ${esc(q)} está escondido pelos filtros ativos.</b> ${blk.length ? (blk.length === 1 ? "Este filtro esconde o item:" : "Estes filtros escondem o item:") : "A combinação destes filtros esconde o item:"}<ul>${lines}</ul>
      <div class="acts"><button class="btn primary" id="fmGo">Limpar filtros e ir para #${esc(q)}</button><button class="btn" id="fmNo">Manter filtros</button></div>`);
    $("fmGo").onclick = () => { hideFmsg(); clearFilters(); gotoId(q); };
    $("fmNo").onclick = hideFmsg;
    // destaca os filtros responsáveis
    (blk.length ? blk : act.map(a => a[0])).forEach(k => { const el = {exec:"fExec", owners:"fOwner", int:"fInt", team:"fTeam", ini:"fIni"}[k]; const n = $(el); n.classList.remove("pulse"); void n.offsetWidth; n.classList.add("pulse"); });
    return;
  }
  hideFmsg();
  S.path = path; S.expand = false; S.focus = null; S.animateLevel = "rel";
  render(); openDetail(target);
  requestAnimationFrame(()=>{ const el = board.querySelector(`[data-key="${cssEsc(target)}"]`); if (el){ el.scrollIntoView({block:"center", inline:"center"}); el.classList.add("flash"); redraw(); } });
}

