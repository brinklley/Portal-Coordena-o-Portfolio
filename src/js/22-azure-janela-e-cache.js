/* ---------- janela da carga: tokens, progresso e mapeamento ---------- */
function azModal(html){ $("azBody").innerHTML = html; $("azBg").hidden = false; $("azBg").querySelector(".modal").style.width = "min(900px,100%)"; }
function azClose(){ $("azBg").hidden = true; }
$("azBg").addEventListener("pointerdown", e => { if (e.target === $("azBg") && !AZ.busy) azClose(); });
$("btnAz").onclick = () => {
  const A = azCfgOf(CFG);
  if (!A.sources.length){ toast("Configure as organizações e as fontes em Configurações › Azure DevOps.", 5000); openCfg(); return; }
  const miss = A.orgs.filter(o => A.sources.some(s => s.org === o.org) && !azConnected(o.org));
  azModal(`<h3>Carregar do Azure DevOps</h3>
    <p class="help">${A.sources.length} fonte(s) configurada(s): ${AZ_ROLES.map(r => { const n = A.sources.filter(s => s.role === r.id).length; return n ? `${r.name} (${n})` : ""; }).filter(Boolean).join(", ")}.</p>
    ${miss.length ? `<p class="help">Informe o token das organizações abaixo. Ele fica só na memória desta sessão.</p>
      <table class="ctab"><tbody>${miss.map((o, i) => `<tr><td><b>${esc(o.org)}</b></td><td><input type="password" autocomplete="off" data-azl-tok="${esc(o.org)}" placeholder="token (PAT)" style="width:240px"></td><td class="az-st" data-azl-st="${esc(o.org)}"></td></tr>`).join("")}</tbody></table>` : `<p class="az-ok">Todas as organizações estão conectadas nesta sessão.</p>`}
    <div class="az-actions"><button class="btn" id="azCancel">Cancelar</button><button class="btn primary" id="azGo">${miss.length ? "Conectar e carregar" : "Carregar"}</button></div>`);
  $("azCancel").onclick = azClose;
  $("azGo").onclick = azRun;
  const f = $("azBody").querySelector("input"); if (f) f.focus();
};
async function azRun(){
  const A = azCfgOf(CFG);
  // 1. validar tokens pendentes
  const tokRes = [];
  for (const inp of $("azBody").querySelectorAll("[data-azl-tok]")){
    const org = inp.dataset.azlTok, st = $("azBody").querySelector(`[data-azl-st="${cssEsc(org)}"]`), tok = inp.value.trim();
    if (!tok){ st.innerHTML = `<span class="az-bad">sem token: fontes ignoradas</span>`; tokRes.push({org, ok:false, msg:"sem token"}); continue; }
    st.textContent = "testando..."; const t1 = performance.now();
    try { AZ.projects[org] = await azTest(org, tok); AZ.tokens[org] = tok; st.innerHTML = `<span class="az-ok">conectada</span>`; tokRes.push({org, ok:true, ms:performance.now() - t1}); }
    catch(e){ st.innerHTML = `<span class="az-bad">${esc(e.message)}</span>`; tokRes.push({org, ok:false, msg:e.message}); }
  }
  const srcs = A.sources.filter(s => azConnected(s.org)), skipped = A.sources.filter(s => !azConnected(s.org));
  if (!srcs.length) return toast("Nenhuma organização conectou. Confira os tokens.", 5000);
  // 2. carga, com o plano de execução visível
  AZ.busy = true;
  const P = azPlan(srcs, skipped, tokRes);
  const raw = [];
  for (const s of srcs){
    const st = P.forSource(s);
    try { const L = await azLoadSource(s, st); raw.push(L); P.sourceDone(s, L); }
    catch(e){ st.fail(e.message); }
  }
  AZ.raw = raw;
  P.step("build").begin();
  const need = ["ini","rel","epi","op"].filter(r => !raw.some(L => L.src.role === r));
  if (need.length){ P.step("build").fail(`faltam dados de ${need.map(r => AZ_ROLES.find(x => x.id === r).name).join(", ")}; configure ou conecte essas fontes`); P.finish(false);
    $("azBody").insertAdjacentHTML("beforeend", `<div class="az-actions"><button class="btn" id="azCancel">Fechar</button></div>`); $("azCancel").onclick = azClose; AZ.busy = false; return; }
  // 3. mapeamento de colunas novas (se houver)
  const pend = raw.map(L => ({L, m:azMapFor(L)})).filter(x => x.m.fresh.length);
  AZ.busy = false;
  if (pend.length){ P.step("build").wait("aguardando o mapeamento de colunas renomeadas ou removidas"); P.finish(true); await new Promise(z => setTimeout(z, 900)); return azShowMapping(pend); }
  P.step("build").done("quadro montado"); P.finish(true);
  await new Promise(z => setTimeout(z, 700));
  azApply();
}
/* Plano de execução no formato terminal: todas as etapas visíveis, com status, resultado e tempo. */
const AZ_STEPS = [["disc","Descoberta: área, colunas do quadro e tipos",1],["wiql","Lista de itens (consulta WIQL)",1],["fields","Campos atuais dos itens",4],
  ["remote","Links Remote Related (itens sem o campo do épico e sem Parent)",2],["hist","Histórico do quadro (Analytics)",10]];
function azPlan(srcs, skipped, tokRes){
  const t0 = performance.now(), groups = [], all = [];
  const mk = (label, w) => { const s = {label, w, status:"pend", detail:"", frac:0, t0:0, t1:0}; all.push(s); return s; };
  if (tokRes.length || true){
    const g = {title:"Conexões", steps:[]};
    const orgs = [...new Set(srcs.map(s => s.org))];
    orgs.forEach(o => { const r = tokRes.find(x => x.org === o), s = mk(`Conexão com ${o}`, .3); s.status = "done"; s.detail = r ? "token validado" : "já conectada nesta sessão"; s.ms = r ? r.ms : 0; g.steps.push(s); });
    tokRes.filter(r => !r.ok).forEach(r => { const s = mk(`Conexão com ${r.org}`, 0); s.status = "fail"; s.detail = r.msg; g.steps.push(s); });
    groups.push(g);
  }
  const bySrc = new Map();
  srcs.forEach(src => {
    const role = AZ_ROLES.find(r => r.id === src.role), g = {title:`${role.name} · ${src.alias || src.team}`, sub:`${src.org} / ${src.project} / ${src.level}`, steps:[], map:{}};
    AZ_STEPS.filter(([k]) => k !== "remote" || src.role === "op").forEach(([k, label, w]) => { const s = mk(label, w); g.map[k] = s; g.steps.push(s); });
    groups.push(g); bySrc.set(src, g);
  });
  skipped.forEach(src => { const g = {title:`${AZ_ROLES.find(r => r.id === src.role).name} · ${src.alias || src.team}`, sub:`${src.org} / ${src.project}`, steps:[]};
    const s = mk("Fora desta carga: organização sem token nesta sessão", 0); s.status = "skip"; g.steps.push(s); groups.push(g); });
  const fin = {title:"Finalização", steps:[], map:{}}; fin.map.build = mk("Montar o quadro no portal", 1); fin.steps.push(fin.map.build); groups.push(fin);
  let finished = null;
  azModal(`<div class="azp-head"><h3>Carregando do Azure DevOps</h3><div class="azp-meta" id="azpMeta"></div></div>
    <div class="bar"><span id="azBar"></span></div><div class="azp" id="azp" role="log" aria-live="polite"></div>`);
  const SPIN = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"; let spin = 0;
  const fmtT = ms => { const s = Math.round(ms / 1000); return s < 60 ? `${s}s` : `${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`; };
  const mark = s => s.status === "done" ? `<b class="azp-ok">[✓]</b>` : s.status === "run" ? `<b class="azp-run">[${SPIN[spin % SPIN.length]}]</b>` : s.status === "fail" ? `<b class="azp-bad">[✗]</b>`
    : s.status === "wait" ? `<b class="azp-wait">[…]</b>` : s.status === "skip" ? `<b class="azp-dim">[–]</b>` : `<b class="azp-dim">[ ]</b>`;
  function draw(){
    const el = $("azp"); if (!el) return;
    const W = all.reduce((a, s) => a + s.w, 0), got = all.reduce((a, s) => a + s.w * (s.status === "done" || s.status === "skip" || s.status === "fail" || s.status === "wait" ? 1 : s.status === "run" ? s.frac : 0), 0);
    const p = W ? got / W : 0, el0 = (finished || performance.now()) - t0;
    const doneSrc = [...bySrc.values()].filter(g => g.steps.every(s => s.status !== "pend" && s.status !== "run")).length;
    const eta = !finished && p > .06 ? ` · restante ~${fmtT(el0 * (1 - p) / p)}` : "";
    $("azpMeta").textContent = `${doneSrc} de ${bySrc.size} fontes · ${fmtT(el0)} decorridos${eta}${finished ? " · concluído" : ""}`;
    $("azBar").style.width = Math.round((finished ? 1 : p) * 100) + "%";
    el.innerHTML = groups.map(g => `<div class="azp-g"><div class="azp-gt">── ${esc(g.title)}${g.sub ? ` <span class="azp-dim">${esc(g.sub)}</span>` : ""}</div>` +
      g.steps.map(s => `<div class="azp-l azp-${s.status}">${mark(s)} <span class="azp-lab">${esc(s.label)}</span>${s.detail ? `<span class="azp-det">${s.status === "fail" ? "erro: " : ""}${esc(s.detail)}</span>` : ""}<span class="azp-t">${s.status === "done" && s.t1 ? fmtT(s.t1 - s.t0) : s.status === "run" ? fmtT(performance.now() - s.t0) : ""}</span></div>`).join("") + `</div>`).join("");
    const run = el.querySelector(".azp-run"); if (run && !finished) run.closest(".azp-l").scrollIntoView({block:"nearest"});
  }
  const timer = setInterval(() => { spin++; if (!$("azp")) return clearInterval(timer); draw(); }, 120);
  const api = s => ({
    begin(){ s.status = "run"; s.t0 = performance.now(); s.frac = 0; draw(); },
    prog(text, f){ s.detail = text; s.frac = f; },
    done(text){ s.status = "done"; s.t1 = performance.now(); s.detail = text || s.detail; s.frac = 1; draw(); },
    fail(text){ s.status = "fail"; s.detail = text; draw(); },
    wait(text){ s.status = "wait"; s.detail = text; draw(); }});
  draw();
  return {
    forSource(src){ const g = bySrc.get(src);
      return {begin:k => api(g.map[k]).begin(), prog:(k, t, f) => api(g.map[k]).prog(t, f), done:(k, t) => api(g.map[k]).done(t),
        fail(msg){ const cur = g.steps.find(s => s.status === "run") || g.steps.find(s => s.status === "pend");
          if (cur){ cur.status = "fail"; cur.detail = msg; }
          g.steps.forEach(s => { if (s.status === "pend"){ s.status = "skip"; s.detail = "não executada por causa do erro acima"; } }); draw(); }}; },
    sourceDone(){ draw(); },
    step(k){ return api(fin.map[k]); },
    finish(ok){ finished = performance.now(); clearInterval(timer); draw(); }
  };
}
function azShowMapping(pend){
  azModal(`<h3>Colunas renomeadas ou removidas</h3>
    <p class="help">O histórico destes quadros tem colunas que não existem mais. Por padrão ficam ignoradas (como na ActionableAgile), e a parte Done de coluna que deixou de ser dividida vai para a coluna seguinte. O mapeamento fica salvo nas configurações de cada fonte.</p>
    <div class="az-map">${pend.map(({L, m}) => `<div class="az-role-h" style="margin-top:8px">${esc(L.src.alias || L.src.team)} <span class="muted">${esc(L.src.org)} / ${esc(L.src.level)}</span></div>
      <table class="ctab"><thead><tr><th>Coluna no histórico</th><th style="text-align:right">Registros</th><th>Associar à coluna atual</th></tr></thead><tbody>
      ${Object.entries(m.unk).filter(([id]) => m.fresh.includes(id)).sort((a, b) => b[1].n - a[1].n).map(([id, u]) => `<tr><td>${esc([...u.names].join(" / "))}</td><td style="text-align:right">${u.n}</td>
        <td><select data-azmap="${esc(L.src.id)}" data-col="${esc(id)}"><option value="">Ignorar</option>${L.keys.map(k => `<option ${m.map[id] === k.key ? "selected" : ""}>${esc(k.key)}</option>`).join("")}</select></td></tr>`).join("")}</tbody></table>`).join("")}</div>
    <div class="az-actions"><button class="btn primary" id="azMapOk">Salvar mapeamento e montar o quadro</button></div>`);
  $("azMapOk").onclick = () => {
    const A = azCfgOf(CFG);
    $("azBody").querySelectorAll("[data-azmap]").forEach(s => { (A.maps[s.dataset.azmap] = A.maps[s.dataset.azmap] || {})[s.dataset.col] = s.value; });
    saveCfg(); azApply();
  };
}
async function azApply(){
  const {tables, notes} = azBuildTables(), imp = newImport(); imp.azure = notes;
  saveCfg();                                                   // mapeamentos novos ficam salvos
  const when = new Date(), label = `Azure DevOps · ${when.toLocaleDateString("pt-BR")} ${when.toLocaleTimeString("pt-BR", {hour:"2-digit", minute:"2-digit"})}`;
  azClose();
  if (loadTables(tables, label, false, imp)) azCacheSave({tables, label, notes, when:when.toISOString()});
}

/* ---------- cache local dos dados (IndexedDB): cards e datas, nunca tokens ---------- */
function azDb(){ return new Promise((ok, no) => { const r = indexedDB.open("mapaPortfolioAzure", 1); r.onupgradeneeded = () => r.result.createObjectStore("dados"); r.onsuccess = () => ok(r.result); r.onerror = () => no(r.error); }); }
async function azCacheSave(v){ try { const db = await azDb(); const tx = db.transaction("dados", "readwrite"); tx.objectStore("dados").put(v, "ultima"); tx.oncomplete = tx.onerror = () => db.close(); } catch(e){} }
async function azCacheLoad(){ try { const db = await azDb(); return await new Promise(ok => { const q = db.transaction("dados").objectStore("dados").get("ultima"); q.onsuccess = () => { db.close(); ok(q.result || null); }; q.onerror = () => { db.close(); ok(null); }; }); } catch(e){ return null; } }
/* apaga tudo o que o portal guardou neste navegador e reinicia como no primeiro acesso */
async function wipeAll(){
  AZ.tokens = {}; AZ.projects = {}; AZ.fields = {}; AZ.raw = null;
  try { localStorage.removeItem(CFG_KEY); } catch(e){}
  await new Promise(ok => { try { const r = indexedDB.deleteDatabase("mapaPortfolioAzure"); r.onsuccess = r.onerror = r.onblocked = () => ok(); setTimeout(ok, 2500); } catch(e){ ok(); } });
  location.reload();
}

if (typeof XLSX === "undefined"){ $("btnTemplate").disabled = true; }
(async () => {
  const c = await azCacheLoad();
  if (c && c.tables){ const imp = newImport(); imp.azure = c.notes || null;
    if (loadTables(c.tables, `${c.label} (dados guardados neste navegador; clique em Azure DevOps para atualizar)`, false, imp)) return; }
  loadTables(demoTables(), "dados de exemplo", true);
})();

