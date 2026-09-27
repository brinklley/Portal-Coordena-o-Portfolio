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
  const origin = ["na carga do Azure DevOps", "a carga do Azure DevOps"];
  if (where.length) add(true, "Retornou nos dados", `Encontrado ${origin[0]}, na aba ${where.join(", ")}.`);
  else if (removed){ add(false, "Retornou do Azure, mas foi excluído na carga", `O item está no estado Removed e a opção “Excluir itens no estado Removed” está ligada (${roleName[removed.split(":")[0]]}).`,
      "Se ele não deveria estar removido, ajuste o estado no Azure DevOps. Para incluir itens removidos, desligue a opção em Configurações › Azure DevOps."); return steps; }
  else { add(false, "Não retornou nos dados", "A carga do Azure não trouxe este ID. A consulta de cada fonte busca só os itens da Area Path do time configurado e dos tipos do nível de backlog escolhido.",
      "No Azure DevOps, confira a Area Path e o tipo do item. Se o item aparece no quadro de outro time, ou se é de um tipo que não pertence ao nível configurado (ex.: Iniciativas), ajuste a fonte em Configurações › Azure DevOps ou o item no Azure. Depois, carregue de novo."); return steps; }
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
  if (lvl === "ini" && S.path.ini && S.path.ini !== id && !S.showAllIni) add(false, "Recolhido na lista", "Outra iniciativa está selecionada, e as demais ficam recolhidas.", "Marque “Manter todas as iniciativas visíveis” nos filtros, ou use “Ir para qualquer ID”.");
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

/* localiza um ID em qualquer nível (iniciativa, release, épico ou item de time) — decisão 0034 */
function findAny(id){
  const M = S.model;
  if (M.inis.has(id)) return {lvl:"ini", item:M.inis.get(id)};
  if (M.rels.has(id)) return {lvl:"rel", item:M.rels.get(id)};
  if (M.epis.has(id)) return {lvl:"epi", item:M.epis.get(id)};
  const op = [...M.ops.values()].find(o => o.id === id);
  return op ? {lvl:"op", item:op} : null;
}
/* monta o "target" (chave do card) e o "path" (cadeia até a iniciativa) de um achado de findAny();
   path fica null quando a cadeia está incompleta/inválida (ex.: release sem iniciativa) */
function resolvePath(found){
  const M = S.model, {lvl, item} = found;
  if (lvl === "ini") return {target:"ini:"+item.id, path:{ini:item.id}};
  if (lvl === "rel") return {target:"rel:"+item.id, path: (item.valid && M.inis.has(item.parent)) ? {ini:item.parent, rel:item.id} : null};
  if (lvl === "epi") return {target:"epi:"+item.id, path: item.valid ? {ini:M.rels.get(item.parent).parent, rel:item.parent, epi:item.id} : null};
  const e = M.epis.get(item.epicoId);
  return {target:item.key, path: (e && e.valid) ? {ini:M.rels.get(e.parent).parent, rel:e.parent, epi:e.id} : null};
}
/* aplica a busca como o filtro único (persistente, aparece em "filtros ativos") e, quando ela é
   um ID, também tenta rolar/abrir o item — decisão 0034. Texto livre (sem ID) só filtra: o
   diagnóstico de "nenhum resultado" (diagnoseEmpty) já cobre esse caso sem precisar navegar.
   Se o quadro inteiro ficar vazio, quem explica é o diagnóstico automático do render() (evita dois
   avisos disputando o mesmo #fmsg — um deles, agendado por requestAnimationFrame, sempre venceria). */
function gotoId(q){
  if (!S.model) return;
  q = (q || "").trim();
  setQueryFilter(q);
  if (!q) return;
  const id = nid(q);
  if (!id || !/^\d+$/.test(id)) return;
  const V = S.V;
  if (!V.visIni.size) return;
  const found = findAny(id);
  const anchor = $("fBusca");
  const inv = `<div class="acts"><button class="btn primary" data-investigate="${esc(id)}">Investigar por que não aparece</button></div>`;
  if (!found) return showFmsg(anchor, `<b>ID ${esc(q)} não encontrado</b> nos dados carregados.${inv}`, "info");
  const {target, path} = resolvePath(found);
  if (!path) return showFmsg(anchor, `<b>O ID ${esc(q)} existe, mas está fora da cadeia válida</b> (falta o vínculo com épico, release ou iniciativa), por isso não aparece no quadro.${inv}`, "info");
  const opKey = target.startsWith("op:") ? target : null;
  if (!pathVisible(V, path, opKey)){
    const act = activeFilters(), blk = blockingFilters(path, opKey);
    if (!blk.length && !pathVisible(withFilters({exec:"", owners:new Set(), int:"", team:"", q:""}, () => computeVisible()), path, opKey))
      return showFmsg(anchor, `<b>O ID ${esc(q)} existe, mas não aparece no quadro</b> por uma regra de exibição, e não por filtro.${inv}`, "info");
    const lines = (blk.length ? act.filter(([k]) => blk.includes(k)) : act).map(([k, v]) => `<li>${FILTER_LABEL[k]}: <b>${esc(v)}</b></li>`).join("");
    showFmsg(anchor, `<b>O ID ${esc(q)} está escondido pelos filtros ativos.</b> ${blk.length ? (blk.length === 1 ? "Este filtro esconde o item:" : "Estes filtros escondem o item:") : "A combinação destes filtros esconde o item:"}<ul>${lines}</ul>
      <div class="acts"><button class="btn primary" id="fmGo">Limpar filtros e ir para #${esc(q)}</button><button class="btn" id="fmNo">Manter filtros</button></div>`);
    $("fmGo").onclick = () => { hideFmsg(); clearFilters(); gotoId(q); };
    $("fmNo").onclick = hideFmsg;
    // destaca os filtros responsáveis
    (blk.length ? blk : act.map(a => a[0])).forEach(k => { const el = FILTER_EL[k]; const n = $(el); n.classList.remove("pulse"); void n.offsetWidth; n.classList.add("pulse"); });
    return;
  }
  hideFmsg();
  S.path = path; S.pathQueryId = id; S.expand = false; S.focus = null; S.animateLevel = "rel";
  render(); openDetail(target);
  requestAnimationFrame(()=>{ const el = board.querySelector(`[data-key="${cssEsc(target)}"]`); if (el){ el.scrollIntoView({block:"center", inline:"center"}); el.classList.add("flash"); redraw(); } });
}

