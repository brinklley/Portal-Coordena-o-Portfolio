/* ---------- ilhas: ancorar / soltar e arrastar ---------- */
function applyOffsets(){
  board.querySelectorAll("[data-move]").forEach(el => {
    const o = S.offsets[el.dataset.move];
    el.style.left = o ? o.x + "px" : ""; el.style.top = o ? o.y + "px" : "";
    el.classList.toggle("movable", !S.anchored);
    el.title = S.anchored ? "" : "Arraste pela borda, cabeçalho ou área vazia para reposicionar";
  });
  $("btnLayout").disabled = !Object.keys(S.offsets).length;
}
$("fAnchor").onchange = e => {
  S.anchored = e.target.checked; applyOffsets();
  ROUTE.key = ""; redraw();
  toast(S.anchored
    ? (Object.keys(S.offsets).length ? "Ilhas ancoradas: barbantes reorganizados para contornar as ilhas." : "Ilhas ancoradas.")
    : "Ilhas soltas: arraste pela borda, cabeçalho ou área vazia para reposicionar.");
};
$("btnLayout").onclick = () => { S.offsets = {}; applyOffsets(); redraw(); toast("Layout automático restaurado."); };
let drag = null;
board.addEventListener("pointerdown", e => {
  if (S.anchored || e.button !== 0 || e.target.closest(".card,button,a,input,select")) return;
  const el = e.target.closest("[data-move]"); if (!el) return;
  e.preventDefault(); e.stopPropagation();
  const k = el.dataset.move, o = S.offsets[k] || {x:0, y:0}, p = pos(el);
  drag = {el, k, o0:{x:o.x, y:o.y}, x:e.clientX, y:e.clientY, base:{l:p.l - o.x, t:p.t - o.y}, id:e.pointerId, moved:false};
  el.setPointerCapture(e.pointerId); el.classList.add("dragging");
});
board.addEventListener("pointermove", e => {
  if (!drag) return;
  // converte o deslocamento da tela para o quadro (considera o zoom) e não deixa sair pela esquerda/topo
  const nx = Math.max(8 - drag.base.l, drag.o0.x + (e.clientX - drag.x) / Z);
  const ny = Math.max(8 - drag.base.t, drag.o0.y + (e.clientY - drag.y) / Z);
  drag.moved = true;
  S.offsets[drag.k] = {x:nx, y:ny};
  drag.el.style.left = nx + "px"; drag.el.style.top = ny + "px";
  redraw();
});
const endDrag = () => {
  if (!drag) return;
  drag.el.classList.remove("dragging");
  try { drag.el.releasePointerCapture(drag.id); } catch(_){}
  const o = S.offsets[drag.k];
  if (o && Math.abs(o.x) < 1 && Math.abs(o.y) < 1) delete S.offsets[drag.k];
  drag = null; applyOffsets(); redraw();
};
board.addEventListener("pointerup", endDrag); board.addEventListener("pointercancel", endDrag);

let tIni; $("fIni").oninput = e => { clearTimeout(tIni); tIni = setTimeout(()=>{ S.f.ini = e.target.value; S.lastFilterEl = $("fIni"); render(); }, 350); };
$("goto").addEventListener("keydown", e => { if (e.key === "Enter") gotoId(e.target.value.trim()); });

function renderCrumbs(){
  const M = S.model, p = S.path; const parts = [];
  parts.push(`<button data-c="root">Todas as iniciativas</button>`);
  if (p.ini) parts.push(`<span class="gt">›</span><button data-c="ini">#${esc(p.ini)} ${esc(M.inis.get(p.ini).title)}</button>`);
  if (S.expand) parts.push(`<span class="gt">›</span><span>cadeia completa</span>`);
  else {
    if (p.rel) parts.push(`<span class="gt">›</span><button data-c="rel">#${esc(p.rel)} ${esc(M.rels.get(p.rel).title)}</button>`);
    if (p.epi) parts.push(`<span class="gt">›</span><span>#${esc(p.epi)} ${esc(M.epis.get(p.epi).title)}</span>`);
  }
  $("crumbs").innerHTML = parts.join("");
}
$("crumbs").addEventListener("click", e => {
  const b = e.target.closest("button"); if (!b) return;
  const c = b.dataset.c;
  if (c === "root"){ S.path = {}; S.expand = false; S.focus = null; }
  if (c === "ini"){ S.path = {ini:S.path.ini}; S.expand = false; S.focus = null; }
  if (c === "rel"){ delete S.path.epi; }
  render();
});

