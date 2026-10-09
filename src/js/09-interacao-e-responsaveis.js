/* ---------------- interação ---------------- */
/* clicar em qualquer lugar do whiteboard (inclusive num card) fecha o painel lateral aberto (Visão
   Analítica, Report F4P ou Actionable) — decisão `0065`: o usuário clicava ali esperando esse efeito,
   sem saber que precisava ir até o botão "«". Ignora cliques que vieram de um arrastar (pan do quadro
   ou de uma ilha solta) — ver `panMoved` em 08-whiteboard-zoom-foco.js. */
vp.addEventListener("click", () => {
  if (panMoved) return;
  if (AN.open) closeAnalytics();
  else if (F4P.open) closeF4P();
  else if (ACT.open) closeActionable();
});
board.addEventListener("click", e => {
  const c = e.target.closest(".card"); if (!c) return;
  const key = c.dataset.key; const [lvl, ...rest] = key.split(":"); const id = rest.join(":");
  // card revelado por "+N ocultos" (decisão 0050): está fora do filtro ativo (não em V), então só
  // abre o painel de detalhes (openDetail olha direto no modelo, sem depender de V) — tentar navegar
  // até ele setaria S.path pra um id que o guard de render() descarta de novo, por não estar em V.
  const inFilter = lvl === "ini" ? S.V.visIni.has(id) : lvl === "rel" ? S.V.visRel.has(id) : lvl === "epi" ? S.V.visEpi.has(id) : true;
  if (!inFilter){ openDetail(key); return; }
  const scrollNext = next => { S.animateLevel = next; };
  if (S.expand && lvl !== "ini"){
    S.focus = S.focus === key ? null : key;
    render(); openDetail(key); return;
  }
  if (lvl === "ini"){
    if (S.path.ini === id){ S.path = {}; S.expand = false; S.focus = null; S.pathQueryId = null; closeDrawer(); render(); return; }
    S.path = {ini:id}; S.pathQueryId = null; S.focus = null; scrollNext("rel"); vp.scrollTop = 0;
  } else if (lvl === "rel"){
    if (S.path.rel === id){ delete S.path.rel; delete S.path.epi; render(); return; }
    S.path.rel = id; delete S.path.epi; scrollNext("epi");
  } else if (lvl === "epi"){
    if (S.path.epi === id){ delete S.path.epi; render(); return; }
    S.path.epi = id; scrollNext("op");
  }
  render(); openDetail(key);
  const next = {ini:"rel", rel:"epi", epi:"op"}[lvl];
  if (next) revealLane(next);
});

/* "+N ocultos"/"− N ocultos" por faixa (decisão `0050`): alterna S.showHidden[lvl], que controla se os
   irmãos ocultados pelo filtro ativo entram (esmaecidos, .dim) na faixa daquele nível. Fica ligado entre
   navegações (mesmo padrão de S.showAllIni) — só não aparece de novo se não houver mais nada oculto. */
board.addEventListener("click", e => {
  const t = e.target.closest("[data-hide-toggle]"); if (!t) return;
  const lvl = t.dataset.hideToggle;
  S.showHidden[lvl] = !S.showHidden[lvl];
  render();
});

$("btnExpand").onclick = () => { S.expand = !S.expand; S.focus = null; if (!S.expand){ delete S.path.rel; delete S.path.epi; } S.animateLevel = S.expand ? "epi" : null; render(); };
$("btnClear").onclick = () => { S.path = {}; S.expand = false; S.focus = null; S.pathQueryId = null; closeDrawer(); render(); };
["fExec","fInt","fTeam"].forEach(id => $(id).onchange = e => { S.f[{fExec:"exec",fInt:"int",fTeam:"team"}[id]] = e.target.value; S.lastFilterEl = e.target; render(); });
$("fBare").onchange = e => { S.showBare = e.target.checked; render(); };
$("fEmpty").onchange = e => { S.showEmpty = e.target.checked; render(); };
$("fShowAllIni").onchange = e => { S.showAllIni = e.target.checked; render(); };
/* ---------- seletor múltiplo de responsáveis, com busca ---------- */
let msKb = -1;
function msLabel(){
  const sel = S.f.owners, b = $("fOwner");
  const names = (S.ownerList || []).filter(o => sel.has(o.k)).map(o => o.label);
  $("msLabel").textContent = !sel.size ? "Todos" : sel.size === 1 ? names[0] : `${sel.size} responsáveis`;
  b.title = names.join("\n");
  b.classList.toggle("active", sel.size > 0);
  $("msCount").textContent = sel.size ? `${sel.size} marcado${sel.size > 1 ? "s" : ""}` : "";
}
function hl(label, q){
  if (!q) return esc(label);
  // destaca o trecho encontrado, ignorando acentos e maiúsculas
  const n = norm(label); const i = n.indexOf(q);
  if (i < 0) return esc(label);
  const map = []; let acc = "";
  [...label].forEach((ch, idx) => { const c = norm(ch) || (ch === " " ? " " : ""); for (const _ of c) map.push(idx); acc += c; });
  const chars = [...label], s = map[i], e = map[Math.min(i + q.length - 1, map.length - 1)] + 1;
  return esc(chars.slice(0,s).join("")) + "<mark>" + esc(chars.slice(s,e).join("")) + "</mark>" + esc(chars.slice(e).join(""));
}
function msVisible(){
  const q = norm($("msSearch").value);
  return (S.ownerList || []).filter(o => !q || norm(o.label).includes(q));
}
function msRender(){
  const q = norm($("msSearch").value), sel = S.f.owners;
  const list = msVisible();
  const row = o => `<label class="ms-item" role="option" aria-selected="${sel.has(o.k)}"><input type="checkbox" value="${esc(o.k)}" ${sel.has(o.k) ? "checked" : ""}><span class="nm" title="${esc(o.label)}">${hl(o.label, q)}</span><span class="n" title="iniciativas">${o.n}</span></label>`;
  let h = "";
  if (!list.length) h = `<div class="ms-empty">Nenhum responsável contém “${esc($("msSearch").value)}”.</div>`;
  else if (!q && sel.size){
    const a = list.filter(o => sel.has(o.k)), b = list.filter(o => !sel.has(o.k));
    h = `<div class="ms-sep">Marcados</div>` + a.map(row).join("") + (b.length ? `<div class="ms-sep">Demais</div>` + b.map(row).join("") : "");
  } else h = list.map(row).join("");
  $("msList").innerHTML = h;
  msKb = -1;
  msLabel();
}
function openMs(){ $("msPop").hidden = false; $("fOwner").setAttribute("aria-expanded","true"); msRender(); $("msSearch").focus(); }
function closeMs(){ $("msPop").hidden = true; $("fOwner").setAttribute("aria-expanded","false"); }
function msApply(){ msLabel(); S.lastFilterEl = $("fOwner"); render(); }
$("fOwner").onclick = () => $("msPop").hidden ? openMs() : closeMs();
$("msSearch").oninput = msRender;
$("msList").addEventListener("change", e => {
  const k = e.target.value; e.target.checked ? S.f.owners.add(k) : S.f.owners.delete(k);
  e.target.closest(".ms-item").setAttribute("aria-selected", e.target.checked);
  msApply(); $("msSearch").focus();
});
$("msAll").onclick = () => { msVisible().forEach(o => S.f.owners.add(o.k)); msRender(); msApply(); };
$("msNone").onclick = () => { S.f.owners.clear(); msRender(); msApply(); };
$("msSearch").addEventListener("keydown", e => {
  const items = [...$("msList").querySelectorAll(".ms-item")];
  if (e.key === "ArrowDown" || e.key === "ArrowUp"){
    e.preventDefault(); if (!items.length) return;
    msKb = (msKb + (e.key === "ArrowDown" ? 1 : -1) + items.length) % items.length;
    items.forEach((it,i) => it.classList.toggle("kb", i === msKb)); items[msKb].scrollIntoView({block:"nearest"});
  } else if (e.key === "Enter"){
    e.preventDefault();
    const it = items[msKb >= 0 ? msKb : (items.length === 1 ? 0 : -1)];
    if (it){ const cb = it.querySelector("input"); cb.checked = !cb.checked; cb.dispatchEvent(new Event("change", {bubbles:true})); if (items.length > 1 && msKb < 0) return; }
    $("msSearch").select();
  } else if (e.key === "Escape"){ e.stopPropagation(); closeMs(); $("fOwner").focus(); }
});
document.addEventListener("pointerdown", e => { if (!$("msPop").hidden && !e.target.closest("#ms")) closeMs(); });

