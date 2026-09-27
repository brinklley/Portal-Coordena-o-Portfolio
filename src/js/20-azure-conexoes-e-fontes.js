/* =====================================================================
   Azure DevOps: carga de dados direto das APIs
   - Tokens só em memória (AZ.tokens); nunca vão para a configuração, o navegador ou a exportação.
   - Fontes: Iniciativa (1), Release (1), Coordenação de Épico (várias), Times operacionais (vários).
   - A carga monta as mesmas "abas" da planilha e usa loadTables(): o resto do portal não muda.
   ===================================================================== */
const AZ = {tokens:{}, projects:{}, fields:{}, raw:null, form:null};
const AZ_API = "api-version=6.0";
const AZ_ROLES = [
  {id:"ini", name:"Iniciativa", multi:false, sheet:"INICIATIVA"},
  {id:"rel", name:"Release", multi:false, sheet:"RELEASE"},
  {id:"epi", name:"Coordenação de Épico", multi:true, sheet:"EPICO"},
  {id:"op", name:"Times operacionais", multi:true, sheet:null}];
const azCfgOf = c => (c.azure = c.azure || {orgs:[], sources:[], maps:{}, fields:{epic:"ID_EPICO_UNICRED", roadmap:"AnoSemestreRoadmap"}, excludeRemoved:true});
const azSeg = s => encodeURIComponent(s);
const azDev = org => `https://dev.azure.com/${azSeg(org)}`;
const azConnected = org => !!AZ.tokens[org];

async function azFetch(org, url, opt = {}, token){
  const tok = token || AZ.tokens[org]; if (!tok) throw new Error(`a organização ${org} está sem token nesta sessão`);
  for (let t = 0; t < 5; t++){
    const r = await fetch(url, {...opt, headers:{Authorization:"Basic " + btoa(":" + tok), ...(opt.body ? {"Content-Type":"application/json"} : {})}});
    if (r.status === 429 || r.status === 503){ await new Promise(z => setTimeout(z, (+r.headers.get("Retry-After") || 2 ** t) * 1000)); continue; }
    const txt = await r.text();
    if (r.status === 401 || r.status === 403) throw new Error(`acesso negado (${r.status}): confira o token e os escopos Work Items (Read) e Analytics (Read)`);
    if (!r.ok){ const tf = /TF\d+[^"]*/.exec(txt); throw new Error(tf ? tf[0].slice(0, 180) : `HTTP ${r.status}`); }
    return txt ? JSON.parse(txt) : {};
  }
  throw new Error("limite de uso do Azure atingido; tente de novo em instantes");
}
/* executa tarefas com N chamadas simultâneas */
async function azPool(tasks, n, onDone){
  let i = 0, done = 0; const out = new Array(tasks.length);
  await Promise.all(Array.from({length:Math.min(n, tasks.length)}, async () => {
    while (i < tasks.length){ const k = i++; out[k] = await tasks[k](); done++; if (onDone) onDone(done, tasks.length); }
  }));
  return out;
}
/* teste de conexão: projetos (Work Items) + Analytics */
async function azTest(org, token){
  const p = await azFetch(org, `${azDev(org)}/_apis/projects?$top=500&${AZ_API}`, {}, token);
  try { await azFetch(org, `https://analytics.dev.azure.com/${azSeg(org)}/_odata/v4.0-preview/Projects?$select=ProjectName&$top=1`, {}, token); }
  catch(e){ throw new Error(`conectou, mas sem acesso ao Analytics (escopo Analytics (Read)): ${e.message}`); }
  return p.value.map(x => ({id:x.id, name:x.name})).sort((a, b) => a.name.localeCompare(b.name, "pt-BR"));
}
/* campos personalizados achados pelo nome (ex.: ID_EPICO_UNICRED -> Custom.ID_EPICO_UNICRED) */
const fkey = s => norm(s).replace(/[^a-z0-9]/g, "");
async function azFields(org){
  if (AZ.fields[org]) return AZ.fields[org];
  const r = await azFetch(org, `${azDev(org)}/_apis/wit/fields?${AZ_API}`), byName = {}, byRef = {};
  r.value.forEach(f => { byName[fkey(f.name)] = f.referenceName; byRef[fkey(f.referenceName.split(".").pop())] = f.referenceName; });
  return (AZ.fields[org] = {find: w => byName[fkey(w)] || byRef[fkey(w)] || null});
}

/* ---------- tela de configuração: conexões e fontes ---------- */
function azRender(){
  const box = $("azSec"); if (!box || !DRAFT) return;
  const A = azCfgOf(DRAFT), anyOn = A.orgs.some(o => azConnected(o.org));
  const orgRows = A.orgs.map((o, i) => `<tr><td><b>${esc(o.org)}</b></td>
    <td>${azConnected(o.org) ? `<span class="az-ok">Conectada nesta sessão</span>` : `<span class="az-wait">Aguardando token</span>`}</td>
    <td>${azConnected(o.org) ? "" : `<input type="password" autocomplete="off" data-az-tok="${i}" placeholder="token (PAT)" style="width:190px"> <button type="button" class="btn" data-az-test="${i}">Testar</button>`}</td>
    <td><button type="button" class="x" data-az-delorg="${i}" aria-label="Remover organização ${esc(o.org)}">×</button></td></tr>`).join("");
  let h = `<h4>Azure DevOps</h4>
    <p class="help">Conecte as organizações do Azure DevOps. O token (PAT) nunca é salvo: fica só na memória enquanto o portal estiver aberto, e precisa ser informado de novo a cada abertura. Escopos necessários, apenas leitura: <b>Work Items (Read)</b> e <b>Analytics (Read)</b>. Uma organização só é adicionada se o teste de conexão der certo.</p>
    <table class="ctab">${A.orgs.length ? `<thead><tr><th>Organização</th><th>Status</th><th></th><th></th></tr></thead>` : ""}<tbody>${orgRows}
      <tr><td><input type="text" id="azNewOrg" placeholder="nova organização (ex.: vsunicred)" style="width:220px" autocomplete="off"></td>
      <td colspan="2"><input type="password" id="azNewTok" placeholder="token (PAT)" style="width:190px" autocomplete="off"> <button type="button" class="btn primary" id="azAddOrg">Testar e adicionar</button></td><td></td></tr></tbody></table>
    <div id="azMsg" class="az-msg" role="status"></div>`;
  if (!anyOn){
    h += `<div class="az-lock">As fontes de dados ficam disponíveis depois que pelo menos uma organização conectar com sucesso nesta sessão.${A.sources.length ? ` Há ${A.sources.length} fonte(s) configurada(s), bloqueadas até o token da organização ser validado.` : ""}</div>`;
    box.innerHTML = h; return;
  }
  h += `<h4 style="margin-top:14px">Fontes de dados por nível</h4>
    <p class="help">Escolha de onde vêm os cards de cada nível. Iniciativa e Release têm uma fonte cada; Coordenação de Épico e Times operacionais aceitam várias. Área, colunas do quadro e tipos de item são descobertos automaticamente.</p>`;
  AZ_ROLES.forEach(role => {
    const list = A.sources.map((s, i) => [s, i]).filter(([s]) => s.role === role.id);
    h += `<div class="az-role"><div class="az-role-h">${role.name} <span class="muted">${role.multi ? "uma ou mais fontes" : "uma fonte"}</span></div>`;
    list.forEach(([s, i]) => {
      const on = azConnected(s.org);
      h += `<div class="az-src ${on ? "" : "locked"}">${on ? "" : `<span class="az-wait">Aguardando token</span> `}<b>${esc(s.org)}</b> / ${esc(s.project)} / ${esc(s.team)} / ${esc(s.level)}${s.alias ? ` <span class="muted">(aparece como <b>${esc(s.alias)}</b>)</span>` : ""}
        ${on ? `<button type="button" class="x" data-az-delsrc="${i}" aria-label="Remover fonte">×</button>` : ""}</div>`;
    });
    const canAdd = role.multi || !list.length;
    if (AZ.form && AZ.form.role === role.id) h += azFormHtml(role);
    else if (canAdd) h += `<button type="button" class="btn" data-az-add="${role.id}">Adicionar fonte</button>`;
    h += `</div>`;
  });
  h += `<h4 style="margin-top:14px">Campos e regras da carga</h4><div class="grid3">
      <label>Campo do vínculo com o épico (nome)<input type="text" id="azFEpic" value="${esc(A.fields.epic)}" style="width:200px"></label>
      <label>Campo do roadmap executivo (nome)<input type="text" id="azFRoad" value="${esc(A.fields.roadmap)}" style="width:200px"></label>
      <label style="flex-direction:row;align-items:center;gap:6px;margin-top:16px"><input type="checkbox" id="azRem" ${A.excludeRemoved ? "checked" : ""}> Excluir itens no estado Removed</label></div>
    <p class="help" style="margin-top:6px">As datas das colunas seguem a regra validada na prova de conceito: Backlog pela data de criação, primeira entrada em cada coluna, colunas puladas recebem a data da próxima e, quando o item volta, as colunas à frente são apagadas. Colunas de quadros antigos ficam ignoradas, salvo mapeamento seu (feito após a primeira carga e salvo aqui).</p>`;
  if (!S.model && A.sources.length) h += `<div class="az-actions" style="margin-top:14px"><button type="button" class="btn primary" id="azGateLoad">Carregar dados do Azure DevOps</button></div>`;
  box.innerHTML = h;
}
function azFormHtml(role){
  const F = AZ.form, A = azCfgOf(DRAFT), orgs = A.orgs.filter(o => azConnected(o.org));
  const opt = (arr, v, lab) => arr.map(x => `<option value="${esc(x)}" ${x === v ? "selected" : ""}>${esc(lab ? lab(x) : x)}</option>`).join("");
  return `<div class="az-form">
    <label>Organização<select id="azFOrg">${opt(orgs.map(o => o.org), F.org)}</select></label>
    <button type="button" class="btn" id="azFLoad">Carregar</button>
    ${F.projects ? `<label>Projeto<select id="azFProj"><option value="">escolha…</option>${opt(F.projects.map(p => p.name), F.project)}</select></label>` : ""}
    ${F.teams ? `<label>Time<select id="azFTeam"><option value="">escolha…</option>${opt(F.teams, F.team)}</select></label>` : ""}
    ${F.levels ? `<label>Nível de backlog<select id="azFLevel">${opt(F.levels.map(l => l.name), F.level, x => `${x} (${(F.levels.find(l => l.name === x).workItemTypes || []).length} tipos)`)}</select></label>` : ""}
    ${F.levels && role.id === "op" ? `<label>Nome do time no portal<input type="text" id="azFAlias" value="${esc(F.alias || "")}" placeholder="${esc(F.team || "")}" style="width:130px"></label>` : ""}
    ${F.levels ? `<button type="button" class="btn primary" id="azFSave">Adicionar</button>` : ""}
    <button type="button" class="btn" id="azFCancel">Cancelar</button>
    ${F.err ? `<div class="az-msg bad">${esc(F.err)}</div>` : ""}
  </div>`;
}
function azMsg(txt, bad){ const m = $("azMsg"); if (m){ m.textContent = txt; m.className = "az-msg" + (bad ? " bad" : ""); } }
$("cfgBody").addEventListener("click", async e => {
  const A = DRAFT && azCfgOf(DRAFT); if (!A) return;
  const b = e.target.closest("button"); if (!b || !e.target.closest("#azSec")) return;
  if (b.id === "azAddOrg"){
    const org = $("azNewOrg").value.trim(), tok = $("azNewTok").value.trim();
    if (!org || !tok) return azMsg("Informe a organização e o token.", true);
    if (A.orgs.some(o => norm(o.org) === norm(org))) return azMsg("Essa organização já está na lista.", true);
    azMsg(`Testando ${org}...`);
    try { AZ.projects[org] = await azTest(org, tok); AZ.tokens[org] = tok; A.orgs.push({org}); azRender(); azMsg(`${org} conectada: ${AZ.projects[org].length} projeto(s).`); }
    catch(err){ azMsg(`Não foi possível conectar em ${org}: ${err.message}. Nada foi salvo.`, true); }
    return;
  }
  if (b.dataset.azTest !== undefined){
    const o = A.orgs[+b.dataset.azTest], tok = document.querySelector(`[data-az-tok="${b.dataset.azTest}"]`).value.trim();
    if (!tok) return azMsg("Informe o token.", true);
    azMsg(`Testando ${o.org}...`);
    try { AZ.projects[o.org] = await azTest(o.org, tok); AZ.tokens[o.org] = tok; azRender(); azMsg(`${o.org} conectada.`); azFillMissingStages(); }
    catch(err){ azMsg(`Não foi possível conectar em ${o.org}: ${err.message}`, true); }
    return;
  }
  if (b.dataset.azDelorg !== undefined){
    const o = A.orgs[+b.dataset.azDelorg], used = A.sources.filter(s => s.org === o.org);
    if (used.length && !confirm(`${used.length} fonte(s) usam ${o.org} e também serão removidas. Continuar?`)) return;
    A.orgs.splice(+b.dataset.azDelorg, 1); A.sources = A.sources.filter(s => s.org !== o.org); delete AZ.tokens[o.org]; azRender(); return;
  }
  if (b.dataset.azDelsrc !== undefined){ const s = A.sources.splice(+b.dataset.azDelsrc, 1)[0]; azRefreshTeams(s && s.role === "op" ? `Fonte ${s.alias || s.team} removida.` : ""); return; }
  if (b.id === "azGateLoad"){
    // pré-carga: salva o rascunho direto (sem o botão "Salvar" da aba Geral, que nem existe ainda)
    const err = readForm();
    if (err){ cfgForm(err); return; }
    CFG = DRAFT; saveCfg(); fillTeamFilter();
    openAzureLoadModal();
    return;
  }
  if (b.dataset.azAdd){ const first = A.orgs.find(o => azConnected(o.org)); AZ.form = {role:b.dataset.azAdd, org:first && first.org}; azRender(); return; }
  if (b.id === "azFCancel"){ AZ.form = null; azRender(); return; }
  if (b.id === "azFLoad"){
    const F = AZ.form; F.org = $("azFOrg").value; F.err = null; F.teams = F.levels = null;
    F.projects = AZ.projects[F.org] || (AZ.projects[F.org] = await azTest(F.org).catch(err => { F.err = err.message; return null; }));
    azRender(); return;
  }
  if (b.id === "azFSave"){
    const F = AZ.form, lv = F.levels.find(l => l.name === $("azFLevel").value);
    const src = {id:"s" + Date.now(), role:F.role, org:F.org, project:F.project, team:F.team, level:lv.name,
      alias:F.role === "op" ? ($("azFAlias").value.trim() || F.team) : ""};
    if (A.sources.some(s => s.role === "op" && src.role === "op" && norm(s.alias || s.team) === norm(src.alias))){ F.err = `Já existe um time chamado "${src.alias}" no portal. Use outro nome.`; azRender(); return; }
    b.disabled = true; b.textContent = "Lendo colunas do quadro...";
    if (src.role === "op"){ try { src.stages = await azStages(src); } catch(err){ src.stages = []; } }
    A.sources.push(src); AZ.form = null;
    azRefreshTeams(src.role === "op" ? `${src.alias} adicionado: ${src.stages.length ? `${src.stages.length} colunas lidas do quadro. Já dá para configurar os alertas e o fluxo dele abaixo.` : "não foi possível ler as colunas agora; elas virão na carga."}` : "");
    return;
  }
});
$("cfgBody").addEventListener("change", async e => {
  if (!e.target.closest("#azSec") || !AZ.form) return;
  const F = AZ.form;
  try {
    if (e.target.id === "azFOrg"){ F.org = e.target.value; F.projects = F.teams = F.levels = null; azRender(); }
    if (e.target.id === "azFProj"){
      F.project = e.target.value; F.team = null; F.levels = null;
      const pr = F.projects.find(p => p.name === F.project);
      const r = await azFetch(F.org, `${azDev(F.org)}/_apis/projects/${azSeg(pr.id)}/teams?$top=500&${AZ_API}`);
      F.teams = r.value.map(x => x.name).sort((a, b) => a.localeCompare(b, "pt-BR")); F.err = null; azRender();
    }
    if (e.target.id === "azFTeam"){
      F.team = e.target.value; F.levels = null; F.err = null;
      try {
        const r = await azFetch(F.org, `${azDev(F.org)}/${azSeg(F.project)}/${azSeg(F.team)}/_apis/work/backlogs?${AZ_API}`);
        F.levels = r.value.sort((a, b) => b.rank - a.rank);
        const guess = {ini:/iniciativ/i, rel:/valor|release/i, epi:/epic/i, op:/stor|requirement/i}[F.role];
        F.level = (F.levels.find(l => guess.test(l.name)) || F.levels[0]).name;
      } catch(err){ F.err = /TF400497/.test(err.message) ? "A configuração de iteração do backlog deste time está inválida no Azure DevOps (TF400497). Escolha outro time ou peça ao administrador para revisar." : err.message; }
      azRender();
    }
    if (e.target.id === "azFAlias") F.alias = e.target.value;
  } catch(err){ F.err = err.message; azRender(); }
});

/* colunas do quadro de uma fonte, já com as divisões Doing/Done (mesmos nomes da carga) */
async function azStages(src){
  const r = await azFetch(src.org, `${azDev(src.org)}/${azSeg(src.project)}/${azSeg(src.team)}/_apis/work/boards/${azSeg(src.level)}/columns?${AZ_API}`);
  return azKeys(r.value).map(k => k.key);
}
/* redesenha a tela de configuração inteira sem perder o que o usuário já digitou */
function azRefreshTeams(msg){
  readForm(); cfgForm();
  if (msg) azMsg(msg);
}
/* fontes operacionais sem colunas guardadas (ex.: cadastradas antes): busca ao abrir a configuração, se a organização estiver conectada */
async function azFillMissingStages(){
  const A = DRAFT && azCfgOf(DRAFT); if (!A) return;
  const miss = A.sources.filter(s => s.role === "op" && !(s.stages && s.stages.length) && azConnected(s.org) && !hasData(s.alias || s.team));
  if (!miss.length) return;
  let ok = 0;
  for (const s of miss){ try { s.stages = await azStages(s); ok++; } catch(e){} }
  if (ok && !$("cfgBg").hidden) azRefreshTeams(`Colunas lidas para ${ok} time(s) cadastrado(s) ainda sem carga.`);
}
