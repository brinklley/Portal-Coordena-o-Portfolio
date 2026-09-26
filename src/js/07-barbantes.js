/* ---------------- barbantes ----------------
   Posições calculadas pelo layout (offsets), não pela área visível:
   o barbante sempre vai de card a card, mesmo fora da tela ou com zoom. */
function pos(el){
  let x = 0, y = 0, e = el;
  while (e && e !== board){ x += e.offsetLeft; y += e.offsetTop; e = e.offsetParent; }
  return {l:x, t:y, r:x + el.offsetWidth, b:y + el.offsetHeight, w:el.offsetWidth};
}
/* Cada barbante é montado em peças pequenas: trechos retos são linhas simples (div)
   e curvas são SVGs pequenos. Evita superfícies gigantes que o navegador corta. */
function dedupe(pts){ return pts.filter((p,i) => i === 0 || Math.abs(p[0]-pts[i-1][0]) > .5 || Math.abs(p[1]-pts[i-1][1]) > .5); }
function lineEl(s, e, st){
  const w = st.w, x = Math.min(s[0], e[0]) - w/2, y = Math.min(s[1], e[1]) - w/2;
  const W = Math.abs(e[0]-s[0]) + w, H = Math.abs(e[1]-s[1]) + w;
  return `<div class="ln" style="left:${x}px;top:${y}px;width:${W}px;height:${H}px;background:${st.c};opacity:${st.op}"></div>`;
}
function curveEl(d, pts, st){
  const pad = 4 + st.w;
  const xs = pts.map(p=>p[0]), ys = pts.map(p=>p[1]);
  const x = Math.min(...xs) - pad, y = Math.min(...ys) - pad;
  const W = Math.max(...xs) - Math.min(...xs) + pad*2, H = Math.max(...ys) - Math.min(...ys) + pad*2;
  return `<svg class="s" style="left:${x}px;top:${y}px" width="${W}" height="${H}" viewBox="${x} ${y} ${W} ${H}"><path d="${d}" fill="none" stroke="${st.c}" stroke-width="${st.w}" stroke-linecap="round" opacity="${st.op}"/></svg>`;
}
function orthoEls(pts, st, R){
  const P = dedupe(pts); if (P.length < 2) return "";
  const n = P.length, cut = [];
  for (let i = 1; i < n - 1; i++){
    const [x0,y0] = P[i-1], [x1,y1] = P[i], [x2,y2] = P[i+1];
    const d1 = Math.hypot(x1-x0, y1-y0), d2 = Math.hypot(x2-x1, y2-y1), rr = Math.min(R, d1/2, d2/2);
    cut[i] = {a:[x1 + (x0-x1)*rr/d1, y1 + (y0-y1)*rr/d1], b:[x1 + (x2-x1)*rr/d2, y1 + (y2-y1)*rr/d2]};
  }
  let h = "";
  for (let i = 0; i < n - 1; i++){
    const s = i === 0 ? P[0] : cut[i].b, e = i + 1 === n - 1 ? P[n-1] : cut[i+1].a;
    h += lineEl(s, e, st);
  }
  for (let i = 1; i < n - 1; i++){
    const {a, b} = cut[i];
    h += curveEl(`M${a[0]},${a[1]} Q${P[i][0]},${P[i][1]} ${b[0]},${b[1]}`, [a, P[i], b], st);
  }
  return h;
}
/* Roteador para layout livre: grade sobre o whiteboard, ilhas como obstáculos.
   Custo favorece linhas retas (penaliza curvas) e afasta barbantes de épicos diferentes
   do mesmo corredor; barbantes do mesmo pai podem seguir juntos (feixe). */
const ROUTE = {key:"", cache:new Map()};
function makeRouter(boxes, pts){
  const G = 20, M = 260, INF = 6;
  const xs = [...boxes.flatMap(b=>[b.l,b.r]), ...pts.map(p=>p[0])], ys = [...boxes.flatMap(b=>[b.t,b.b]), ...pts.map(p=>p[1])];
  const minX = Math.min(...xs) - M, minY = Math.min(...ys) - M;
  const W = Math.ceil((Math.max(...xs) + M - minX) / G) + 1, H = Math.ceil((Math.max(...ys) + M - minY) / G) + 1, N = W * H;
  const block = new Uint8Array(N);
  boxes.forEach(b => {
    const x0 = Math.max(0, Math.floor((b.l - INF - minX) / G)), x1 = Math.min(W - 1, Math.ceil((b.r + INF - minX) / G));
    const y0 = Math.max(0, Math.floor((b.t - INF - minY) / G)), y1 = Math.min(H - 1, Math.ceil((b.b + INF - minY) / G));
    for (let y = y0; y <= y1; y++) for (let x = x0; x <= x1; x++) block[y * W + x] = 1;
  });
  const gS = new Float64Array(N), stamp = new Int32Array(N), from = new Int32Array(N), dirA = new Int8Array(N), closed = new Int32Array(N);
  const used = new Uint16Array(N), usedBy = new Int32Array(N).fill(-1);
  let run = 0;
  const cellOf = (x, y) => [Math.min(W-1, Math.max(0, Math.round((x - minX) / G))), Math.min(H-1, Math.max(0, Math.round((y - minY) / G)))];
  const DX = [1,-1,0,0], DY = [0,0,1,-1];
  function route(p0, p1, pid){
    run++;
    const [sx, sy] = cellOf(p0[0], p0[1]), [ex, ey] = cellOf(p1[0], p1[1]);
    const s = sy * W + sx, e = ey * W + ex;
    const hx = i => Math.abs((i % W) - ex) + Math.abs(((i / W) | 0) - ey);
    // heap binário (f, índice)
    const hf = [], hi = [];
    const push = (f, i) => { hf.push(f); hi.push(i); let k = hf.length - 1; while (k){ const q = (k - 1) >> 1; if (hf[q] <= hf[k]) break; [hf[q],hf[k]] = [hf[k],hf[q]]; [hi[q],hi[k]] = [hi[k],hi[q]]; k = q; } };
    const pop = () => { const i = hi[0], lf = hf.pop(), li = hi.pop(); if (hf.length){ hf[0] = lf; hi[0] = li; let k = 0; for(;;){ const l = 2*k+1, r = l+1; let m = k; if (l < hf.length && hf[l] < hf[m]) m = l; if (r < hf.length && hf[r] < hf[m]) m = r; if (m === k) break; [hf[m],hf[k]] = [hf[k],hf[m]]; [hi[m],hi[k]] = [hi[k],hi[m]]; k = m; } } return i; };
    stamp[s] = run; gS[s] = 0; from[s] = -1; dirA[s] = -1; push(hx(s), s);
    let found = false, guard = 0;
    while (hf.length && guard++ < 150000){
      const c = pop();
      if (closed[c] === run) continue; closed[c] = run;
      if (c === e){ found = true; break; }
      const cx = c % W, cy = (c / W) | 0;
      for (let d = 0; d < 4; d++){
        const nx = cx + DX[d], ny = cy + DY[d];
        if (nx < 0 || ny < 0 || nx >= W || ny >= H) continue;
        const n = ny * W + nx;
        if (block[n] && n !== e) continue;
        if (closed[n] === run) continue;
        let cost = 1 + (dirA[c] >= 0 && dirA[c] !== d ? 4 : 0) + (used[n] && usedBy[n] !== pid ? 1.5 : 0);
        const ng = gS[c] + cost;
        if (stamp[n] !== run || ng < gS[n]){ stamp[n] = run; gS[n] = ng; from[n] = c; dirA[n] = d; push(ng + hx(n), n); }
      }
    }
    if (!found) return null;
    const cells = []; for (let c = e; c !== -1; c = from[c]) cells.push(c);
    cells.reverse();
    cells.forEach(c => { used[c]++; usedBy[c] = pid; });
    // só os cantos, em pixels
    let pts2 = [];
    cells.forEach((c, k) => {
      if (k > 0 && k < cells.length - 1 && dirA[c] === dirA[cells[k+1]]) return;
      pts2.push([minX + (c % W) * G, minY + ((c / W) | 0) * G]);
    });
    // encaixa as pontas exatamente nos pontos de saída/chegada, mantendo tudo ortogonal
    const snap = (arr, P, fromStart) => {
      if (arr.length < 2) return;
      const i0 = fromStart ? 0 : arr.length - 1, i1 = fromStart ? 1 : arr.length - 2;
      const vertical = Math.abs(arr[i1][0] - arr[i0][0]) < Math.abs(arr[i1][1] - arr[i0][1]);
      if (vertical) arr[i1][0] = P[0]; else arr[i1][1] = P[1];
      arr[i0] = [P[0], P[1]];
    };
    if (pts2.length === 1) pts2 = [[p0[0], p0[1]], [p1[0], p1[1]]];
    snap(pts2, p0, true); snap(pts2, p1, false);
    const out = [pts2[0]];
    for (let k = 1; k < pts2.length; k++){
      const pr = out[out.length - 1], q = pts2[k];
      if (Math.abs(pr[0] - q[0]) > .5 && Math.abs(pr[1] - q[1]) > .5) out.push([q[0], pr[1]]);
      out.push(q);
    }
    return out;
  }
  return {route};
}
function drawStrings(){
  const sv = $("strings"), pv = $("pins"); if (!sv) return;
  const color = {ok:"var(--ok)", warn:"var(--warn)", alert:"var(--alert)", outlier:"var(--outlier)"};
  const chain = S.focus ? chainKeys(S.focus) : null;
  const P = new Map(), byLane = new Map();
  board.querySelectorAll(".card").forEach(c => {
    const p = pos(c); P.set(c.dataset.key, p);
    const ln = c.closest(".island") || c.closest(".lane"); if (!byLane.has(ln)) byLane.set(ln, []); byLane.get(ln).push(p);
  });
  // com ilhas de time movidas pelo usuário, não há fileiras automáticas para contornar
  const autoTeams = !Object.entries(S.offsets).some(([k,o]) => k.startsWith("isl:") && (o.x || o.y));
  // layout livre e ancorado: barbantes contornam as ilhas (roteamento recalculado e guardado em cache)
  const smart = S.anchored && Object.keys(S.offsets).length > 0;
  let router = null;
  if (smart){
    const boxes = [...board.querySelectorAll("[data-move]")].map(pos);
    const key = JSON.stringify(boxes.map(b => [b.l,b.t,b.r,b.b].map(Math.round))) + "|" + JSON.stringify(S.links);
    if (key !== ROUTE.key){ ROUTE.key = key; ROUTE.cache = new Map(); ROUTE.router = makeRouter(boxes, []); ROUTE.pids = new Map(); }
    router = ROUTE.router;
  }
  // fileiras de ilhas: corredores livres entre as ilhas de cada fileira
  const rowsEl = [...board.querySelectorAll(".isl-row")];
  const rowsInfo = rowsEl.map(r => {
    const isl = [...r.querySelectorAll(":scope > .island")].map(pos).sort((a,b)=>a.l-b.l);
    const top = Math.min(...isl.map(i=>i.t)), bottom = Math.max(...isl.map(i=>i.b));
    const free = []; let prev = -1e6;
    isl.forEach(i => { free.push([prev, i.l - 16]); prev = i.r + 16; });
    free.push([prev, 1e6]);
    return {top, bottom, free};
  });
  const corridor = (row, x) => {
    let best = null, bd = Infinity;
    row.free.forEach(([a,b]) => { if (b - a < 12) return; const c = Math.min(Math.max(x, a + 6), b - 6); const d = Math.abs(c - x); if (d < bd){ bd = d; best = c; } });
    return best ?? x;
  };
  board.querySelectorAll(".island").forEach(c => P.set(c.dataset.key, pos(c)));
  const sameCol = (a, b) => Math.abs(a.l - b.l) < 2;
  // portas: cada barbante que chega numa ilha entra num ponto diferente do topo
  const portN = new Map(), portI = new Map();
  S.links.forEach(([, ck]) => { if (ck.startsWith("isl:")) portN.set(ck, (portN.get(ck) || 0) + 1); });
  let out = "", pins = "";
  S.links.forEach(([pk, ck, h], idx) => {
    const pe = board.querySelector(`[data-key="${cssEsc(pk)}"]`), ce = board.querySelector(`[data-key="${cssEsc(ck)}"]`);
    if (!pe || !ce) return;
    const a = P.get(pk), b = P.get(ck);
    const lp = pe.closest(".lane"), lc = ce.closest(".lane");
    const bP = pos(pe.closest("[data-move]") || lp), bC = pos(ce.closest("[data-move]") || lc);
    const rowEl = ce.closest(".isl-row"), ri = rowEl && autoTeams && !smart ? rowsEl.indexOf(rowEl) : 0;
    const yA = bP.b + (smart ? 26 : 12), yB = ri > 0 ? rowsInfo[0].top - 16 : bC.t - (smart ? 26 : 16);
    const gp = pe.closest(".island") || lp, gc = ce.closest(".island") || lc;
    const below = byLane.get(gp).some(o => o !== a && sameCol(o, a) && o.t > a.t);
    const above = !ck.startsWith("isl:") && (byLane.get(gc) || []).some(o => o !== b && sameCol(o, b) && o.t < b.t);
    let start, part1, xs, end, part2, xe;
    if (!below){ xs = (a.l + a.r) / 2; start = [xs, a.b]; part1 = [start, [xs, yA]]; }
    else { xs = a.r + 15; start = [a.r, a.t + 20]; part1 = [start, [xs, a.t + 20], [xs, yA]]; }
    if (ck.startsWith("isl:")){
      const n = portN.get(ck), i = portI.get(ck) || 0; portI.set(ck, i + 1);
      const span = Math.min(b.r - b.l - 60, n * 26);
      xe = (b.l + b.r) / 2 - span / 2 + (n > 1 ? span * i / (n - 1) : span / 2);
      end = [xe, b.t]; part2 = [[xe, yB], end];
    }
    else if (!above){ xe = (b.l + b.r) / 2; end = [xe, b.t]; part2 = [[xe, yB], end]; }
    else { xe = b.l - 15; end = [b.l, b.t + 20]; part2 = [[xe, yB], [xe, b.t + 20], end]; }
    // destino numa fileira de baixo: desce pelos corredores entre as ilhas das fileiras de cima
    let xm = xe, via = [];
    if (ri > 0){
      const jit = ((idx % 5) - 2) * 4;
      const cs = []; for (let k = 0; k < ri; k++) cs.push(corridor(rowsInfo[k], xe + jit));
      xm = cs[0]; via = [[cs[0], yB]];
      let g = yB;
      for (let k = 0; k < ri; k++){
        g = rowsInfo[k].bottom + 36;
        via.push([cs[k], g]); via.push([k + 1 < ri ? cs[k + 1] : xe, g]);
      }
      part2[0] = [xe, g];
    }
    const dim = chain && !(chain.has(pk) && chain.has(ck));
    const st = {c:color[h], w: dim ? 1.2 : 2.2, op: dim ? .16 : .92};
    const ym = (yA + yB) / 2;
    const fresh = S.animateLevel && S.animateLevel === ck.split(":")[0] ? " fresh" : "";
    let mid = null;
    if (router){
      const rk = `${pk}>${ck}`;
      if (!ROUTE.cache.has(rk)){
        if (!ROUTE.pids.has(pk)) ROUTE.pids.set(pk, ROUTE.pids.size);
        ROUTE.cache.set(rk, router.route([xs, yA], [xe, yB], ROUTE.pids.get(pk)));
      }
      mid = ROUTE.cache.get(rk);
    }
    out += `<div class="lk${fresh}">` + (mid
      ? orthoEls([...part1, ...mid, ...part2], st, 12)
      : orthoEls(part1, st, 12)
        + curveEl(`M${xs},${yA} C${xs},${ym} ${xm},${ym} ${xm},${yB}`, [[xs,yA],[xm,yB]], st)
        + orthoEls([...via, ...part2], st, 12)) + `</div>`;
    if (!dim) pins += `<div class="pin" style="left:${start[0]}px;top:${start[1]}px;background:${st.c}"></div><div class="pin" style="left:${end[0]}px;top:${end[1]}px;background:${st.c}"></div>`;
  });
  sv.innerHTML = out; pv.innerHTML = pins;
  S.animateLevel = null;
}
const cssEsc = s => (window.CSS && CSS.escape) ? CSS.escape(s) : s.replace(/"/g,'\\"');
let raf = 0; const redraw = () => { cancelAnimationFrame(raf); raf = requestAnimationFrame(() => { updateSizer(); drawStrings(); drawMinimap(); }); };
window.addEventListener("resize", redraw);

