/* ---------------- whiteboard: zoom e arrastar ---------------- */
const vp = $("viewport"), sizer = $("sizer");
let Z = 1;
function updateSizer(){
  board.style.minWidth = (vp.clientWidth / Z) + "px";
  board.style.minHeight = (vp.clientHeight / Z) + "px";
  board.style.transform = `scale(${Z})`;
  const ex = boardExtent();
  sizer.style.width = (Math.max(board.offsetWidth, ex.r + 160) * Z) + "px";
  sizer.style.height = (Math.max(board.offsetHeight, ex.b + 200) * Z) + "px";
  sizer.style.backgroundSize = `${22 * Z}px ${22 * Z}px`;
  $("zLabel").textContent = Math.round(Z * 100) + "%";
}
function boardExtent(){
  let r = 0, b = 0;
  board.querySelectorAll("[data-move]").forEach(el => { const p = pos(el); r = Math.max(r, p.r); b = Math.max(b, p.b); });
  return {r, b};
}
function setZoom(z, cx, cy){
  z = Math.min(1.5, Math.max(0.12, z));
  if (cx === undefined){ cx = vp.clientWidth / 2; cy = vp.clientHeight / 2; }
  const bx = (vp.scrollLeft + cx) / Z, by = (vp.scrollTop + cy) / Z;
  Z = z; updateSizer();
  vp.scrollLeft = bx * Z - cx; vp.scrollTop = by * Z - cy;
}
function contentWidth(){
  let w = 0; board.querySelectorAll(".lane-inner, .isl-row").forEach(g => { w = Math.max(w, g.offsetWidth); });
  if (Object.keys(S.offsets).length) w = Math.max(w, boardExtent().r);
  return w + 60;
}
$("zIn").onclick = () => setZoom(Z * 1.15);
$("zOut").onclick = () => setZoom(Z / 1.15);
$("zLabel").onclick = () => setZoom(1);
$("zFit").onclick = () => { setZoom(Math.min(1, (vp.clientWidth - 10) / contentWidth()), 0, 0); vp.scrollLeft = Math.max(0, (vp.scrollWidth - vp.clientWidth) / 2); };
vp.addEventListener("wheel", e => {
  if (!(e.ctrlKey || e.metaKey)) return;
  e.preventDefault();
  const r = vp.getBoundingClientRect();
  setZoom(Z * (e.deltaY < 0 ? 1.1 : 1/1.1), e.clientX - r.left, e.clientY - r.top);
}, {passive:false});
let pan = null, panMoved = false;
vp.addEventListener("pointerdown", e => {
  panMoved = false;
  if (e.button !== 0 || e.target.closest(".card,button,a,input,select,.zoom,.movable")) return;
  pan = {x:e.clientX, y:e.clientY, sl:vp.scrollLeft, st:vp.scrollTop, id:e.pointerId};
  vp.setPointerCapture(e.pointerId); vp.classList.add("panning");
});
vp.addEventListener("pointermove", e => {
  if (!pan) return;
  if (Math.hypot(e.clientX - pan.x, e.clientY - pan.y) > 4) panMoved = true;
  vp.scrollLeft = pan.sl - (e.clientX - pan.x); vp.scrollTop = pan.st - (e.clientY - pan.y);
});
const endPan = () => { if (pan){ vp.releasePointerCapture(pan.id); pan = null; vp.classList.remove("panning"); } };
vp.addEventListener("pointerup", endPan); vp.addEventListener("pointercancel", endPan);
if (window.ResizeObserver) new ResizeObserver(redraw).observe(board);

/* ---------------- foco (modo cadeia completa) ---------------- */
function chainKeys(key){
  const set = new Set([key]);
  S.links.forEach(()=>{}); // links já refletem o que está visível
  let grew = true;
  // ancestrais
  let cur = key;
  while (true){ const l = S.links.find(x => x[1] === cur); if (!l) break; set.add(l[0]); cur = l[0]; }
  // descendentes
  while (grew){ grew = false; S.links.forEach(([p,c]) => { if (set.has(p) && !set.has(c) && isDesc(p, key)) { set.add(c); grew = true; } }); }
  return set;
}
function isDesc(p, root){ // p é o root ou descendente dele
  if (p === root) return true;
  let cur = p;
  while (true){ const l = S.links.find(x => x[1] === cur); if (!l) return false; if (l[0] === root) return true; cur = l[0]; }
}
function applyFocus(){
  if (!S.focus) return;
  const chain = chainKeys(S.focus);
  board.querySelectorAll(".card").forEach(c => {
    const k = c.dataset.key;
    const inLower = k.split(":")[0] !== "ini";
    if (inLower && !chain.has(k)) c.classList.add("dim");
    if (k === S.focus) c.classList.add("sel");
  });
}

