/* ---------- minimapa ---------- */
const MM = {on:true, scale:1, ox:0, oy:0};
function drawMinimap(){
  const box = $("minimap"); box.hidden = !MM.on || !S.model; $("mmOpen").hidden = MM.on || !S.model;
  if (box.hidden) return;
  const cv = $("mm"), W = sizer.offsetWidth / Z, H = sizer.offsetHeight / Z; if (!W || !H) return;
  const maxW = 220, maxH = 150;
  const s = Math.min(maxW / W, maxH / H);
  const cw = Math.max(60, Math.round(W * s)), ch = Math.max(40, Math.round(H * s));
  const dpr = window.devicePixelRatio || 1;
  if (cv.width !== cw * dpr || cv.height !== ch * dpr){ cv.width = cw * dpr; cv.height = ch * dpr; cv.style.width = cw + "px"; cv.style.height = ch + "px"; }
  MM.scale = s;
  const g = cv.getContext("2d"); g.setTransform(dpr,0,0,dpr,0,0);
  g.fillStyle = "#EEF1F3"; g.fillRect(0,0,cw,ch);
  g.strokeStyle = "#AEB8C1"; g.lineWidth = 1;
  /* decisão `0069`: pos(el) mede a posição relativa ao próprio #board, que agora fica deslocado
     (margem pannable, panMX/panMY) dentro do #sizer — soma o deslocamento (convertido pra unidade
     "equivalente sem zoom", a mesma que pos() usa) pra desenhar os cards alinhados com o retângulo do
     viewport abaixo (que já usa vp.scrollLeft/Top, medidos a partir da borda do próprio sizer). */
  const mxU = panMX / Z, myU = panMY / Z;
  board.querySelectorAll(".island").forEach(el => { const p = pos(el); g.fillStyle = "#FFFFFF"; g.fillRect((p.l+mxU)*s, (p.t+myU)*s, (p.r-p.l)*s, (p.b-p.t)*s); g.strokeRect((p.l+mxU)*s+.5, (p.t+myU)*s+.5, (p.r-p.l)*s, (p.b-p.t)*s); });
  const col = {ini:"#34489A", rel:"#16786A", epi:"#9A6512", op:"#5A6570"};
  board.querySelectorAll(".card").forEach(el => {
    const p = pos(el); g.globalAlpha = el.classList.contains("dim") ? .25 : 1;
    g.fillStyle = col[el.dataset.key.split(":")[0]] || "#5A6570";
    g.fillRect((p.l+mxU)*s, (p.t+myU)*s, Math.max(1.5,(p.r-p.l)*s), Math.max(1.5,(p.b-p.t)*s));
  });
  g.globalAlpha = 1;
  const vx = vp.scrollLeft / Z * s, vy = vp.scrollTop / Z * s, vw = vp.clientWidth / Z * s, vh = vp.clientHeight / Z * s;
  g.fillStyle = "rgba(52,72,154,.10)"; g.fillRect(vx, vy, vw, vh);
  g.strokeStyle = "#34489A"; g.lineWidth = 1.5; g.strokeRect(vx+.75, vy+.75, Math.max(4,vw-1.5), Math.max(4,vh-1.5));
}
let mmRaf = 0; const mmRedraw = () => { cancelAnimationFrame(mmRaf); mmRaf = requestAnimationFrame(drawMinimap); };
vp.addEventListener("scroll", mmRedraw, {passive:true});
function mmGo(e){
  const r = $("mm").getBoundingClientRect();
  const bx = (e.clientX - r.left) / MM.scale, by = (e.clientY - r.top) / MM.scale;
  vp.scrollLeft = bx * Z - vp.clientWidth / 2; vp.scrollTop = by * Z - vp.clientHeight / 2;
}
let mmDrag = false;
$("mm").addEventListener("pointerdown", e => { mmDrag = true; $("mm").setPointerCapture(e.pointerId); mmGo(e); });
$("mm").addEventListener("pointermove", e => { if (mmDrag) mmGo(e); });
$("mm").addEventListener("pointerup", () => { mmDrag = false; });
$("mmClose").onclick = () => { MM.on = false; drawMinimap(); };
$("mmOpen").onclick = () => { MM.on = true; drawMinimap(); };

