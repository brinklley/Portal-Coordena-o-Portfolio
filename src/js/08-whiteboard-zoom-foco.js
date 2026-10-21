/* ---------------- whiteboard: zoom e arrastar ---------------- */
const vp = $("viewport"), sizer = $("sizer");
let Z = 1;
/* margem de espaço em branco pra navegar (decisão `0069`): fração do viewport reservada como margem
   PANNABLE em volta do conteúdo, nos 4 lados — ver PAN_MARGIN abaixo. panMX/panMY (recalculados a cada
   updateSizer()) são onde o conteúdo começa dentro do sizer — qualquer código que precise "rolar até o
   início do conteúdo" usa esses dois, nunca 0 (que agora cai na margem em branco). */
const PAN_MARGIN = 0.5;
let panMX = 0, panMY = 0;
/* usa offsetWidth/offsetHeight (não clientWidth/clientHeight) de propósito: client* encolhe quando a
   barra de rolagem aparece, e board.style.minWidth/minHeight é justamente o que decide, via sizer,
   se o viewport (overflow:auto) PRECISA de barra — ler client* aqui fecha um ciclo (barra aparece →
   client* encolhe → board encolhe → barra some → client* cresce → board cresce → barra aparece de
   novo…) que o ResizeObserver em board (abaixo) reexecuta a cada mudança, sem nunca estabilizar. Isso
   é o que o usuário via como a tela "tremendo em loop" — decisão `0066`. offset* inclui a barra no
   cálculo (não muda com ela presente ou não), rompendo o ciclo. */
function updateSizer(){
  board.style.minWidth = (vp.offsetWidth / Z) + "px";
  board.style.minHeight = (vp.offsetHeight / Z) + "px";
  board.style.transform = `scale(${Z})`;
  const ex = boardExtent();
  /* decisão `0069`: pedido do usuário — a área pannable do quadro (fora do conteúdo) era pequena
     demais, a câmera "batia nas bordas" ao mover o minimapa. Antes só existia uma margem pequena
     (160/200px de CONTEÚDO, não de tela — depois de multiplicada pelo zoom, encolhia a quase nada
     com zoom out) e só do lado direito/inferior; a esquerda/acima não tinha margem nenhuma (board
     ficava colado em left:0;top:0 do sizer). Agora a margem é sempre meia largura/altura do viewport,
     em PIXELS DE TELA (não encolhe/cresce com o zoom — por isso soma `mx`/`my` direto, sem multiplicar
     por `Z`: `left`/`top` do board não são afetados pelo `transform:scale()` dele mesmo, só o tamanho
     renderizado é), igual nos 4 lados. */
  panMX = vp.offsetWidth * PAN_MARGIN; panMY = vp.offsetHeight * PAN_MARGIN;
  board.style.left = panMX + "px";
  board.style.top = panMY + "px";
  sizer.style.width = (Math.max(board.offsetWidth, ex.r) * Z + panMX * 2) + "px";
  sizer.style.height = (Math.max(board.offsetHeight, ex.b) * Z + panMY * 2) + "px";
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

