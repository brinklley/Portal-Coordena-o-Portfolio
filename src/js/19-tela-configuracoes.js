/* ---------------- início ---------------- */
/* ---------- tela de configurações ---------- */
let DRAFT = null;
function cfgForm(err){
  const M = S.model, d = DRAFT;
  const teams = cfgTeams(d);
  const stages = M ? M.stages.op : [];
  const names = stages.map(norm);
  const def = defaultSets(stages);
  const rs = resolveSets(d, stages), custom = rs.custom;
  const ctSel = new Set(Array.isArray(d.ctCols) && d.ctCols.length ? d.ctCols : ctDefaultCols(stages));
  const disc = new Set(rs.disc), wip = new Set(rs.wip), vaz = new Set(rs.vazao);
  const teamUses = s => teams.filter(tm => stagesOf(tm, d).some(x => norm(x) === norm(s))).length;
  const num = (k, f, lab, tm) => { const v = (d.teams[k] || {})[f]; return `<input type="number" min="1" step="1" data-team="${esc(k)}" data-f="${f}" value="${v ?? ""}" placeholder="${f === "stuck" ? "geral" : "—"}" aria-label="${lab} do time ${esc(tm)}">`; };
  $("cfgBody").innerHTML = `<div id="azSec"></div>
    <h4>Alertas por time (CT planejado)</h4>
    <p class="help">Preencha o <b>CT máximo</b> para o time passar a usar os próprios limites. <b>Atenção</b> vale para itens em andamento; <b>atraso</b> (acima do CT máximo) e <b>outlier</b> valem também para itens concluídos. Os valores devem crescer: atenção &lt; CT máximo &lt; outlier. Em branco no CT máximo, o time usa a regra geral abaixo.</p>
    ${!teams.length ? `<div class="az-lock">Nenhum time para configurar ainda. Os times aparecem aqui depois que você carregar uma planilha ou cadastrar fontes de times operacionais do Azure DevOps (seção no topo desta tela).${S.isDemo ? " Os times dos dados de exemplo não entram na configuração." : ""}</div>` : ""}
    <table class="ctab" ${teams.length ? "" : "hidden"}><thead><tr><th>Time</th><th>Atenção (dias)</th><th>CT máximo, atraso (dias)</th><th>Outlier (dias)</th><th>Parado na coluna (dias)</th></tr></thead><tbody>
    ${teams.map(tm => { const k = norm(tm); return `<tr><td>${esc(tm)} <span class="muted">${hasData(tm) ? `${[...M.ops.values()].filter(o => o.team === tm).length} itens` : "ainda sem carga"}</span></td>
      <td>${num(k,"warn","Atenção",tm)}</td><td>${num(k,"max","CT máximo",tm)}</td><td>${num(k,"out","Outlier",tm)}</td><td>${num(k,"stuck","Parado na coluna",tm)}</td></tr>`; }).join("") || `<tr><td colspan="5" class="muted">Carregue uma planilha para ver os times.</td></tr>`}
    </tbody></table>
    ${err ? `<p class="cfg-err" role="alert">${esc(err)}</p>` : ""}
    <h4>Regra geral (times sem CT planejado)</h4>
    <p class="help">Vale só para itens em andamento dos times sem CT máximo preenchido. “Parado na mesma coluna” vale para todos os times sem valor próprio e considera apenas itens em colunas de WIP.</p>
    <div class="grid3">
      <label>Atenção a partir de (dias)<input type="number" min="1" id="cfgWarn" value="${d.warnDays}"></label>
      <label>Alerta de atraso a partir de (dias)<input type="number" min="1" id="cfgAlert" value="${d.alertDays}"></label>
      <label>Outlier a partir de (dias)<input type="number" min="1" id="cfgOut" value="${d.outlierDays}"></label>
      <label>Parado na mesma coluna a partir de (dias)<input type="number" min="1" id="cfgStuck" value="${d.stuckDays}"></label>
    </div>
    <h4>Visão analítica</h4>
    <p class="help">Usada no painel analítico (abre pela aba à esquerda quando há um Time e um Roadmap no filtro). <b>Capacidade</b> conta os itens com a tag abaixo; <b>Projetada</b> e <b>QTD</b> contam todos. O <b>dead line</b> é o fim do semestre (menos os dias informados abaixo) menos o CT máximo do time. As contagens usam os mesmos tipos de item marcados em “Tipos considerados no CT do épico”.</p>
    <div class="grid3">
      <label title="Também usada pelo quadrante Vazão do Report F4P (Reserva)">Tag que marca a capacidade do roadmap<input type="text" id="cfgAnTag" value="${esc(d.anTag || "")}" style="width:200px"></label>
      <label>Coluna da iniciativa com Capex/Opex<input type="text" id="cfgAnCol" value="${esc(d.anClassCol || "")}" style="width:240px"></label>
      <label title="Use quando o semestre operacional termina antes do último dia do calendário (ex.: congelamento de fim de ano)">Dias antes do fim do semestre<input type="number" min="0" id="cfgAnFreeze" value="${d.anFreeze || 0}" style="width:120px"></label>
    </div>
    <h4>Report F4P</h4>
    <p class="help">Painel Report F4P (aba à esquerda, junto com a Visão analítica): mostra sempre todos os times carregados. O quadrante <b>CycleTime</b> usa o CT máximo por time (tabela “Alertas por time” acima); os campos abaixo valem para a amostra do P95/P50, para a faixa esperada de <b>Variabilidade</b> (P95 ÷ P50), para a meta de <b>Urgente</b> e de <b>Technical Story</b> de cada time, e para os tipos considerados pelo <b>Vazão</b> (Reserva/Realizado — a tag de capacidade é a mesma da Visão analítica, acima). Sem valor por time, Variabilidade usa o padrão 1.5–3.5, Urgente fica sem meta (sem cor de alerta) e Technical Story usa o padrão 6.</p>
    <div class="grid3">
      <label>Período do P95/P50 (meses)<input type="number" min="1" id="cfgF4pMonths" value="${d.f4p.months}" style="width:100px"></label>
      <label>Tag da Classe de Serviço Expedite (quadrante Urgente)<select id="cfgF4pExpedite" style="width:200px">${(d.tags || []).map(tg => `<option value="${esc(tg.id)}" ${tg.id === (d.f4p.expediteTag || "urgent") ? "selected" : ""}>${esc(tg.name)}</option>`).join("") || `<option value="">Nenhuma tag cadastrada</option>`}</select></label>
    </div>
    <div class="typelist">${typesFound().map(([ty, n]) => `<label><input type="checkbox" data-f4ptype="${esc(norm(ty))}" ${(d.f4p.types || []).includes(norm(ty)) ? "checked" : ""}> ${esc(ty)} <span class="muted">${n}</span></label>`).join("") || `<span class="muted">Carregue uma planilha para ver os tipos.</span>`}</div>
    <p class="help">Os tipos acima valem para CycleTime, Variabilidade e Vazão. O quadrante Urgente conta itens da tag Expedite acima de <b>qualquer</b> tipo; Technical Story conta só itens desse tipo, fixo.</p>
    <p class="help">Tipos de <b>épico</b> (não de item de time) considerados pelo quadrante <b>Roadmap – Épicos</b>; padrão Epic.</p>
    <div class="typelist">${typesByLevel("epi").map(([ty, n]) => `<label><input type="checkbox" data-f4pepitype="${esc(norm(ty))}" ${(d.f4p.epiTypes || []).includes(norm(ty)) ? "checked" : ""}> ${esc(ty)} <span class="muted">${n}</span></label>`).join("") || `<span class="muted">Carregue uma planilha com a coluna Work Item Type nos épicos para ver os tipos.</span>`}</div>
    <p class="help">Tipos considerados pelo quadrante <b>User Story (planejado vs não planejado)</b>; padrão User Story — configuração própria, independente da lista de tipos acima.</p>
    <div class="typelist">${typesFound().map(([ty, n]) => `<label><input type="checkbox" data-f4pustype="${esc(norm(ty))}" ${(d.f4p.usTypes || []).includes(norm(ty)) ? "checked" : ""}> ${esc(ty)} <span class="muted">${n}</span></label>`).join("") || `<span class="muted">Carregue uma planilha para ver os tipos.</span>`}</div>
    <table class="ctab" ${teams.length ? "" : "hidden"}><thead><tr><th>Time</th><th>Variabilidade mínima</th><th>Variabilidade máxima</th><th>Meta de Urgente (Expedite) no semestre</th><th>Meta de Technical Story no semestre</th></tr></thead><tbody>
    ${teams.map(tm => { const k = norm(tm), v = d.f4p.teams[k] || {};
      return `<tr><td>${esc(tm)}</td>
        <td><input type="number" min="0.1" step="0.1" data-f4pteam="${esc(k)}" data-f4pf="min" value="${v.min ?? ""}" placeholder="1,5" aria-label="Variabilidade mínima de ${esc(tm)}"></td>
        <td><input type="number" min="0.1" step="0.1" data-f4pteam="${esc(k)}" data-f4pf="max" value="${v.max ?? ""}" placeholder="3,5" aria-label="Variabilidade máxima de ${esc(tm)}"></td>
        <td><input type="number" min="0" step="1" data-f4pteam="${esc(k)}" data-f4pf="urgentMeta" value="${v.urgentMeta ?? ""}" placeholder="sem meta" aria-label="Meta de Urgente de ${esc(tm)}"></td>
        <td><input type="number" min="0" step="1" data-f4pteam="${esc(k)}" data-f4pf="tsMeta" value="${v.tsMeta ?? ""}" placeholder="6" aria-label="Meta de Technical Story de ${esc(tm)}"></td></tr>`; }).join("") || `<tr><td colspan="5" class="muted">Carregue uma planilha para ver os times.</td></tr>`}
    </tbody></table>
    <h4>Tipos considerados no CT do épico</h4>
    <p class="help">O CycleTime mostrado nos cards de épico usa só os itens dos tipos marcados. Os alertas de cada item continuam valendo para todos os tipos.</p>
    <div class="typelist">${typesFound().map(([ty, n]) => `<label><input type="checkbox" data-cttype="${esc(norm(ty))}" ${(d.ctTypes || []).includes(norm(ty)) ? "checked" : ""}> ${esc(ty)} <span class="muted">${n}</span></label>`).join("") || `<span class="muted">Carregue uma planilha para ver os tipos.</span>`}</div>
    <h4>Tags cadastradas</h4>
    <p class="help">Itens dos times com estas tags (coluna Tags) ganham a cor de fundo no fluxo. Os itens ainda abertos também geram alerta nos cards pai (épico, release e iniciativa). BLOCKED também é reconhecido pela coluna Blocked, e o “desde” vem da coluna Blocked Days. Para as demais, o “desde” é a data em que o item entrou na coluna atual; “para o dia” usa a coluna Target Date, quando existir.</p>
    <table class="ctab" id="tagTable"><thead><tr><th>Tag</th><th>Também reconhece</th><th>Cor</th><th>Alerta nos pais</th><th>Data</th><th></th></tr></thead><tbody>
    ${(d.tags || []).map((tg, i) => `<tr data-tag="${i}" data-id="${esc(tg.id)}">
      <td><input type="text" data-f="name" value="${esc(tg.name)}" style="width:110px" aria-label="Nome da tag"></td>
      <td><input type="text" data-f="aliases" value="${esc((tg.aliases || []).join(", "))}" style="width:170px" aria-label="Outros nomes da tag"></td>
      <td><input type="color" data-f="color" value="${esc(tg.color)}" aria-label="Cor da tag"> <span class="tchp" style="background:${tg.color};color:${inkOn(tg.color)}">${esc(tg.name)}</span></td>
      <td><select data-f="level">${[["alert","Alerta"],["warn","Atenção"],["info","Aviso"],["none","Nenhum"]].map(([v,l]) => `<option value="${v}" ${tg.level === v ? "selected" : ""}>${l}</option>`).join("")}</select></td>
      <td><select data-f="when"><option value="since" ${tg.when !== "target" ? "selected" : ""}>desde</option><option value="target" ${tg.when === "target" ? "selected" : ""}>para o dia</option></select></td>
      <td><button type="button" class="x" data-del="${i}" aria-label="Remover tag ${esc(tg.name)}">×</button></td></tr>`).join("")}
    </tbody></table>
    <button type="button" class="btn" id="tagAdd" style="margin-top:8px">Adicionar tag</button>
    <h4>Cor da faixa do card por tipo</h4>
    <p class="help">A cor vale só para a faixa no topo do card, para identificar o tipo de relance (por exemplo, User Story × Internal Bug). Tipos sem cor escolhida usam a cor padrão do nível.</p>
    ${typeColorForm(d)}
    <h4>Campos adicionais nos cards</h4>
    <p class="help">Escolha colunas da planilha para aparecer no corpo dos cards, abaixo das informações padrão, e no painel de detalhes. As informações padrão continuam sempre visíveis; as colunas do fluxo não entram na lista.</p>
    ${fieldsForm(d)}
    <h4>Configuração do fluxo dos times</h4>
    <p class="help">Cada aba mostra só as colunas do fluxo daquele time, na ordem real. Para cada coluna, escolha como ela conta nos cards de épico: <b>Discovery</b> (já começou, mas ainda não entrou no WIP), <b>WIP</b> (trabalho em aberto) ou <b>Vazão</b> (concluído). Em <b>Entra no CT</b>, o CycleTime do item começa na <b>primeira</b> coluna marcada e termina na <b>última</b>.</p>
    ${flowTabsHtml(d)}`;
  azRender();
}
/* lê o formulário para o rascunho; devolve mensagem de erro (ou null) */
function readForm(){
  const d = DRAFT; let err = null;
  $("cfgBody").querySelectorAll("input.bad").forEach(i => i.classList.remove("bad"));
  const rows = {};
  $("cfgBody").querySelectorAll("input[data-team]").forEach(inp => {
    const k = inp.dataset.team, v = parseInt(inp.value, 10);
    (rows[k] ||= {})[inp.dataset.f] = v > 0 ? v : undefined;
  });
  Object.entries(rows).forEach(([k, r]) => {
    const clean = Object.fromEntries(Object.entries(r).filter(([,v]) => v > 0));
    if (Object.keys(clean).length) d.teams[k] = clean; else delete d.teams[k];
    const bad = f => $("cfgBody").querySelector(`input[data-team="${cssEsc(k)}"][data-f="${f}"]`).classList.add("bad");
    if (!clean.max && (clean.warn || clean.out)){ err = err || "Para usar atenção ou outlier por time, preencha também o CT máximo desse time."; bad("max"); }
    if (clean.max && clean.warn && clean.warn >= clean.max){ err = err || "A atenção precisa ser menor que o CT máximo."; bad("warn"); }
    if (clean.max && clean.out && clean.out <= clean.max){ err = err || "O outlier precisa ser maior que o CT máximo."; bad("out"); }
  });
  const num = (id, def) => { const v = parseInt($(id).value, 10); return v > 0 ? v : def; };
  d.warnDays = num("cfgWarn", 30); d.alertDays = num("cfgAlert", 60); d.outlierDays = num("cfgOut", 90); d.stuckDays = num("cfgStuck", 10);
  if (d.warnDays >= d.alertDays || d.alertDays >= d.outlierDays){ err = err || "Na regra geral, os valores devem crescer: atenção < atraso < outlier."; ["cfgWarn","cfgAlert","cfgOut"].forEach(id => $(id).classList.add("bad")); }
  if ($("azFEpic")){ const A = azCfgOf(d); A.fields.epic = $("azFEpic").value.trim() || "ID_EPICO_UNICRED"; A.fields.roadmap = $("azFRoad").value.trim() || "AnoSemestreRoadmap"; A.excludeRemoved = $("azRem").checked; }
  d.anTag = $("cfgAnTag").value.trim() || "ROADMAP"; d.anClassCol = $("cfgAnCol").value.trim(); d.anFreeze = Math.max(0, parseInt($("cfgAnFreeze").value, 10) || 0);
  d.ctTypes = [...$("cfgBody").querySelectorAll("input[data-cttype]")].filter(i => i.checked).map(i => i.dataset.cttype)
    .concat((d.ctTypes || []).filter(x => !$("cfgBody").querySelector(`input[data-cttype="${cssEsc(x)}"]`)));
  d.f4p.months = (() => { const v = parseInt($("cfgF4pMonths").value, 10); return v > 0 ? v : 6; })();
  d.f4p.expediteTag = $("cfgF4pExpedite").value || "urgent";
  d.f4p.types = [...$("cfgBody").querySelectorAll("input[data-f4ptype]")].filter(i => i.checked).map(i => i.dataset.f4ptype)
    .concat((d.f4p.types || []).filter(x => !$("cfgBody").querySelector(`input[data-f4ptype="${cssEsc(x)}"]`)));
  d.f4p.epiTypes = [...$("cfgBody").querySelectorAll("input[data-f4pepitype]")].filter(i => i.checked).map(i => i.dataset.f4pepitype)
    .concat((d.f4p.epiTypes || []).filter(x => !$("cfgBody").querySelector(`input[data-f4pepitype="${cssEsc(x)}"]`)));
  d.f4p.usTypes = [...$("cfgBody").querySelectorAll("input[data-f4pustype]")].filter(i => i.checked).map(i => i.dataset.f4pustype)
    .concat((d.f4p.usTypes || []).filter(x => !$("cfgBody").querySelector(`input[data-f4pustype="${cssEsc(x)}"]`)));
  const f4pRows = {};
  $("cfgBody").querySelectorAll("input[data-f4pteam]").forEach(inp => {
    const k = inp.dataset.f4pteam, f = inp.dataset.f4pf, raw = parseFloat(inp.value.replace(",", "."));
    (f4pRows[k] ||= {})[f] = (f === "urgentMeta" || f === "tsMeta") ? (raw >= 0 ? raw : undefined) : (raw > 0 ? raw : undefined);
  });
  d.f4p.teams = {};
  Object.entries(f4pRows).forEach(([k, r]) => {
    const bad = f => $("cfgBody").querySelector(`input[data-f4pteam="${cssEsc(k)}"][data-f4pf="${f}"]`).classList.add("bad");
    const entry = {};
    if (r.min !== undefined || r.max !== undefined){
      if (r.min === undefined || r.max === undefined){ err = err || "Para a variabilidade de um time, preencha o mínimo e o máximo juntos."; bad(r.min === undefined ? "min" : "max"); }
      else if (r.min >= r.max){ err = err || "A variabilidade mínima precisa ser menor que a máxima."; bad("min"); }
      else { entry.min = r.min; entry.max = r.max; }
    }
    if (r.urgentMeta !== undefined) entry.urgentMeta = r.urgentMeta;
    if (r.tsMeta !== undefined) entry.tsMeta = r.tsMeta;
    if (Object.keys(entry).length) d.f4p.teams[k] = entry;
  });
  $("cfgBody").querySelectorAll("input[data-tc-lvl]").forEach(i => {
    const l = i.dataset.tcLvl, k = i.dataset.tcType; d.typeColors[l] = d.typeColors[l] || {};
    if (i.value.toLowerCase() === LVL_HEX[l].toLowerCase()) delete d.typeColors[l][k]; else d.typeColors[l][k] = i.value;
  });
  ["ini","rel","epi","op"].forEach(l => {
    const boxes = [...$("cfgBody").querySelectorAll(`input[data-fld-lvl="${l}"]`)];
    if (boxes.length) d.fields[l] = boxes.filter(b => b.checked).map(b => b.dataset.fld);
  });
  d.tags = [...$("cfgBody").querySelectorAll("#tagTable tbody tr")].map(tr => {
    const g = f => tr.querySelector(`[data-f="${f}"]`).value;
    const name = g("name").trim();
    return name ? {id: tr.dataset.id, name, aliases: g("aliases").split(",").map(s => s.trim()).filter(Boolean), color: g("color"), level: g("level"), when: g("when")} : null;
  }).filter(Boolean);
  const panels = [...$("cfgBody").querySelectorAll(".fpanel:not([data-empty])")];
  if (S.model && panels.length){
    const same = (a, b) => a.length === b.length && a.every(x => b.includes(x));
    const pure = cfgDefaults(), flow = {}, badTeams = [];
    panels.forEach(p => {
      const tm = p.dataset.teamName, k = p.dataset.flteam, cur = readFlowPanel(p), def = teamFlowCfg(tm, pure);
      const isDef = def.n.every((x, i) => cur.cat[x] === def.cat[i]) && same(cur.ct, def.ct);
      if (!isDef) flow[k] = cur;
      if (cur.ct.length < 2){
        badTeams.push(tm);
        p.querySelectorAll("input[data-ctcol]").forEach(i => i.classList.add("bad"));
        $("cfgBody").querySelector(`.ftab[data-ftab="${cssEsc(tm)}"]`).classList.add("bad");
      }
    });
    if (badTeams.length) err = err || `No fluxo ${badTeams.length === 1 ? "do time" : "dos times"} ${badTeams.join(", ")}, marque ao menos duas colunas em “Entra no CT” (a de entrada e a de saída). As abas com problema estão em vermelho.`;
    // a configuração passa a ser por time; a antiga (única para todos) deixa de valer
    d.flow = flow; d.wip = null; d.vazao = null; d.disc = null; d.ctCols = null;
  }
  return err;
}
const LVL_NAME = {ini:"Iniciativas", rel:"Releases", epi:"Épicos", op:"Operacional dos times"};
function typesByLevel(lvl){
  if (!S.model) return [];
  const src = lvl === "ini" ? S.model.inis : lvl === "rel" ? S.model.rels : lvl === "epi" ? S.model.epis : S.model.ops;
  const c = {}; src.forEach(o => { if (o.type) c[o.type] = (c[o.type] || 0) + 1; });
  return Object.entries(c).sort((a, b) => b[1] - a[1]);
}
function typeColorForm(d){
  const lv = ["ini","rel","epi","op"].map(l => [l, typesByLevel(l)]).filter(([, ts]) => ts.length);
  if (!lv.length) return `<p class="muted">A planilha não tem a coluna Work Item Type.</p>`;
  return lv.map(([l, ts]) => `<div class="tcgrp"><div class="tcgrp-h" style="border-left-color:${LVL_HEX[l]}">${LVL_NAME[l]}</div><div class="tcgrid">${ts.map(([ty, n]) => {
    const k = norm(ty), c = (d.typeColors[l] || {})[k] || LVL_HEX[l];
    return `<label class="tcitem"><input type="color" data-tc-lvl="${l}" data-tc-type="${esc(k)}" value="${esc(c)}" aria-label="Cor do tipo ${esc(ty)} em ${LVL_NAME[l]}"><span class="tcprev" style="border-top-color:${esc(c)}"></span>${esc(ty)} <span class="muted">${n}</span></label>`; }).join("")}</div></div>`).join("");
}
function fieldsForm(d){
  const av = S.model ? S.model.fieldsAvail : null;
  if (!av) return `<p class="muted">Carregue uma planilha para ver as colunas.</p>`;
  return ["ini","rel","epi","op"].map(l => { const ks = Object.entries(av[l] || {}); if (!ks.length) return "";
    return `<div class="tcgrp"><div class="tcgrp-h" style="border-left-color:${LVL_HEX[l]}">${LVL_NAME[l]}</div><div class="typelist">${ks.map(([k, name]) =>
      `<label><input type="checkbox" data-fld-lvl="${l}" data-fld="${esc(k)}" ${(d.fields[l] || []).includes(k) ? "checked" : ""}> ${esc(name)}</label>`).join("")}</div></div>`; }).join("");
}
const CAT_LABEL = {none:"Nenhum", disc:"Discovery", wip:"WIP", vazao:"Vazão"};
function flowTabsHtml(d){
  const M = S.model; if (!M) return `<p class="muted">Carregue uma planilha para configurar o fluxo dos times.</p>`;
  const teams = cfgTeams(d), cur = teams.includes(S.cfgTab) ? S.cfgTab : teams[0];
  if (!teams.length) return `<div class="az-lock">Nenhum time para configurar ainda. Os times aparecem aqui depois que você carregar uma planilha ou cadastrar fontes de times operacionais do Azure DevOps (seção no topo desta tela).${S.isDemo ? " Os times dos dados de exemplo não entram na configuração." : ""}</div>`;
  const tabs = `<div class="ftabs" role="tablist">${teams.map(tm => `<button type="button" role="tab" class="ftab${tm === cur ? " on" : ""}" aria-selected="${tm === cur}" data-ftab="${esc(tm)}">${esc(tm)} <span class="muted">${stagesOf(tm, d).length ? `${stagesOf(tm, d).length} colunas` : "sem colunas"}${hasData(tm) ? "" : " · sem carga"}</span></button>`).join("")}</div>`;
  const panels = teams.map(tm => {
    const c = teamFlowCfg(tm, d), k = norm(tm), ctS = new Set(c.ct);
    if (!c.stages.length) return `<div class="fpanel" role="tabpanel" data-flteam="${esc(k)}" data-team-name="${esc(tm)}" data-empty="1" ${tm === cur ? "" : "hidden"}>
      <div class="az-lock">As colunas do quadro de ${esc(tm)} ainda não foram lidas. Conecte a organização desta fonte nesta sessão (seção Azure DevOps, no topo) para buscá-las automaticamente, ou faça a carga dos dados.</div></div>`;
    const count = {}; M.ops.forEach(o => { if (o.team === tm){ const s = norm(o.stName); count[s] = (count[s] || 0) + 1; } });
    const rows = c.stages.map((s, i) => { const n = c.n[i], v = c.cat[i];
      return `<tr data-stage="${esc(n)}" data-cat="${v}"><td class="fnum"><span class="fnb">${i + 1}</span></td><td>${esc(s)}</td><td><span class="rg" role="radiogroup" aria-label="${esc(s)}">
        ${["none","disc","wip","vazao"].map(val => `<label class="cat-${val}"><input type="radio" name="fl_${esc(k)}_${i}" value="${val}" ${v === val ? "checked" : ""}>${CAT_LABEL[val]}</label>`).join("")}
      </span></td><td style="text-align:center"><input type="checkbox" data-ctcol="${esc(n)}" ${ctS.has(n) ? "checked" : ""} aria-label="${esc(s)} entra no CT"></td>
      <td class="muted" style="text-align:right">${count[n] ? `${count[n]} ${count[n] === 1 ? "item" : "itens"}` : ""}</td></tr>`; }).join("");
    return `<div class="fpanel" role="tabpanel" data-flteam="${esc(k)}" data-team-name="${esc(tm)}" ${tm === cur ? "" : "hidden"}>
      <div class="fvis">${flowVisHtml(c.stages, c.cat, c.ct, c.n)}</div>
      <table class="ctab"><thead><tr><th>#</th><th>Coluna do fluxo de ${esc(tm)}</th><th>Conta como</th><th>Entra no CT</th><th style="text-align:right">Itens hoje</th></tr></thead><tbody>${rows}</tbody></table>
      ${teams.length > 1 ? `<button type="button" class="btn" data-fcopy="${esc(k)}" style="margin-top:8px">Aplicar estas marcações aos outros times (colunas com o mesmo nome)</button>` : ""}
    </div>`; }).join("");
  return tabs + panels;
}
/* visual do fluxo: um bloco por coluna, colorido pela categoria, com a faixa do CT embaixo */
function flowVisHtml(stages, cat, ct, n){
  const ctS = new Set(ct), idx = n.map((x, i) => ctS.has(x) ? i : -1).filter(i => i >= 0);
  const a = idx.length ? idx[0] : -1, b = idx.length ? idx[idx.length - 1] : -1;
  const span = (c) => { const ii = cat.map((x, i) => x === c ? i : -1).filter(i => i >= 0); return ii.length ? `${esc(stages[ii[0]])} → ${esc(stages[ii[ii.length - 1]])}` : "nenhuma coluna"; };
  return `<div class="fstrip">${stages.map((s, i) => `<span class="fb ${cat[i]}${i >= a && i <= b && a >= 0 ? " inct" : ""}" title="${i + 1}. ${esc(s)}: ${CAT_LABEL[cat[i]]}${ctS.has(n[i]) ? ", entra no CT" : ""}"><em>${i + 1}</em></span>`).join("")}</div>
    <div class="fsum">
      <span><i class="sq disc"></i>Discovery: ${span("disc")}</span>
      <span><i class="sq wip"></i>WIP: ${span("wip")}</span>
      <span><i class="sq vaz"></i>Vazão: ${span("vazao")}</span>
      <span><i class="ctbar"></i>CT: ${a >= 0 && b > a ? `${esc(stages[a])} → ${esc(stages[b])}` : `<b style="color:var(--alert)">marque ao menos duas colunas</b>`}</span>
    </div>`;
}
function readFlowPanel(p){
  const cat = {}, ct = [];
  p.querySelectorAll("tr[data-stage]").forEach(tr => { const s = tr.dataset.stage; cat[s] = tr.querySelector("input[type=radio]:checked").value; if (tr.querySelector("input[data-ctcol]").checked) ct.push(s); });
  return {cat, ct};
}
function ctSummary(d){
  if (!S.model) return "";
  const rows = S.model.teams.map(tm => { const c = ctColsOf(tm, d);
    return `<li><b>${esc(tm)}</b>: ${c ? `${esc(c.entry)} → ${esc(c.exit)}` : `<span style="color:var(--alert)">nenhuma coluna marcada no fluxo deste time; o CT fica vazio</span>`}</li>`; });
  return `<div class="ctsum-h">Resultado por time (entrada → saída do CT)</div><ul>${rows.join("")}</ul>`;
}
function typesFound(){
  if (!S.model) return [];
  const c = {}; S.model.ops.forEach(o => { if (o.type) c[o.type] = (c[o.type] || 0) + 1; });
  return Object.entries(c).sort((a, b) => b[1] - a[1]);
}
$("cfgBody").addEventListener("click", e => {
  const del = e.target.closest("[data-del]"), add = e.target.closest("#tagAdd");
  if (!del && !add) return;
  readForm();
  if (del) DRAFT.tags.splice(+del.dataset.del, 1);
  if (add) DRAFT.tags.push({id:"t" + Date.now(), name:"NOVA TAG", aliases:[], color:"#A7F3D0", level:"info", when:"since"});
  cfgForm(); $("cfgBody").querySelector("#tagTable tbody tr:last-child input")?.focus();
});
$("cfgBody").addEventListener("change", e => {
  const p = e.target.closest(".fpanel"); if (!p) return;
  if (e.target.type === "radio"){ const tr = e.target.closest("tr[data-stage]"); if (tr) tr.dataset.cat = e.target.value; }
  const c = readFlowPanel(p), tc = teamFlowCfg(p.dataset.teamName, {flow:{[p.dataset.flteam]:c}});
  p.querySelector(".fvis").innerHTML = flowVisHtml(tc.stages, tc.cat, tc.ct, tc.n);
  if (e.target.matches("input[data-ctcol]")){ p.querySelectorAll("input[data-ctcol].bad").forEach(i => i.classList.remove("bad")); }
});
$("cfgBody").addEventListener("click", e => {
  const tab = e.target.closest(".ftab");
  if (tab){
    S.cfgTab = tab.dataset.ftab;
    $("cfgBody").querySelectorAll(".ftab").forEach(b => { const on = b === tab; b.classList.toggle("on", on); b.setAttribute("aria-selected", on); });
    $("cfgBody").querySelectorAll(".fpanel").forEach(pp => pp.hidden = pp.dataset.teamName !== S.cfgTab);
    return;
  }
  const cp = e.target.closest("[data-fcopy]");
  if (cp){
    const src = readFlowPanel(cp.closest(".fpanel")); let n = 0;
    $("cfgBody").querySelectorAll(".fpanel").forEach(pp => {
      if (pp === cp.closest(".fpanel")) return;
      pp.querySelectorAll("tr[data-stage]").forEach(tr => {
        const s = tr.dataset.stage; if (!(s in src.cat)) return;
        tr.querySelector(`input[type=radio][value="${src.cat[s]}"]`).checked = true;
        tr.querySelector("input[data-ctcol]").checked = src.ct.includes(s); n++;
      });
      const c = readFlowPanel(pp), tc = teamFlowCfg(pp.dataset.teamName, {flow:{[pp.dataset.flteam]:c}});
      pp.querySelector(".fvis").innerHTML = flowVisHtml(tc.stages, tc.cat, tc.ct, tc.n);
    });
    toast(`Marcações aplicadas em ${n} colunas de mesmo nome nos outros times. Confira cada aba antes de salvar.`, 5000);
  }
});
$("cfgBody").addEventListener("input", e => {
  if (e.target.matches("input[data-tc-lvl]")) e.target.parentElement.querySelector(".tcprev").style.borderTopColor = e.target.value;
  if (e.target.matches('#tagTable input[data-f="color"], #tagTable input[data-f="name"]')){
    const tr = e.target.closest("tr"), chip = tr.querySelector(".tchp"), col = tr.querySelector('[data-f="color"]').value;
    chip.style.background = col; chip.style.color = inkOn(col); chip.textContent = tr.querySelector('[data-f="name"]').value;
  }
});
function openCfg(){ AZ.form = null; DRAFT = JSON.parse(JSON.stringify(CFG)); cfgForm(); $("cfgBg").hidden = false; const f = $("cfgBody").querySelector("input"); if (f) f.focus(); azFillMissingStages(); }
function closeCfg(){ $("cfgBg").hidden = true; DRAFT = null; $("btnCfg").focus(); }
$("btnCfg").onclick = openCfg;
$("cfgClose").onclick = $("cfgCancel").onclick = closeCfg;
$("cfgBg").addEventListener("pointerdown", e => { if (e.target === $("cfgBg")) closeCfg(); });
$("cfgBg").addEventListener("keydown", e => { if (e.key === "Escape"){ e.stopPropagation(); closeCfg(); } });
$("cfgReset").onclick = () => { DRAFT = {...cfgDefaults(), azure: DRAFT.azure}; cfgForm(); };
$("cfgSave").onclick = () => {
  const err = readForm();
  if (err){ const isBox = i => i.type === "radio" || i.type === "checkbox";
    const vals = [...$("cfgBody").querySelectorAll("input, select")].map(i => isBox(i) ? i.checked : i.value);
    cfgForm(err); [...$("cfgBody").querySelectorAll("input, select")].forEach((i,k) => { if (isBox(i)) i.checked = vals[k]; else i.value = vals[k]; });
    readForm(); const f = $("cfgBody").querySelector("input.bad"); if (f) f.focus(); return; }
  CFG = DRAFT; const ok = saveCfg(); fillTeamFilter();
  closeCfg(); recomputeHealth(); ROUTE.key = "";
  const k = S.detailKey; render(); if (k) openDetail(k);
  toast(ok ? "Configurações salvas neste navegador." : "Configurações aplicadas. Este navegador não permitiu guardar; use Exportar para não perder.", 5000);
};
$("cfgWipe").onclick = async () => {
  const c = await azCacheLoad(), A = azCfgOf(CFG);
  const itens = [
    "todas as configurações: alertas por time, fluxo dos times, tags, cores, campos adicionais e visão analítica",
    A.orgs.length ? `as conexões com o Azure DevOps (${A.orgs.map(o => o.org).join(", ")}) e ${A.sources.length} fonte(s) de dados, com os mapeamentos de colunas` : "",
    c ? `os dados carregados do Azure guardados neste navegador (${esc(c.label || "última carga")})` : "",
    Object.keys(AZ.tokens).length ? "os tokens informados nesta sessão" : ""].filter(Boolean);
  azModal(`<h3>Limpar tudo e reiniciar</h3>
    <p class="help">O portal vai voltar ao estado do primeiro acesso, com os dados de exemplo. Isto não pode ser desfeito. Será apagado deste navegador:</p>
    <ul class="wipe-list">${itens.map(x => `<li>${x}</li>`).join("")}</ul>
    <p class="help">Nada é apagado no Azure DevOps nem nas planilhas. Para poder restaurar as configurações depois, exporte-as antes (os tokens não vão no arquivo).</p>
    <div class="az-actions"><button class="btn" id="wipeExport">Exportar configurações antes</button><span style="flex:1"></span>
      <button class="btn" id="wipeCancel">Cancelar</button><button class="btn danger-solid" id="wipeGo">Apagar tudo e reiniciar</button></div>`);
  $("wipeCancel").onclick = azClose;
  $("wipeExport").onclick = () => {
    const blob = new Blob([JSON.stringify(CFG, null, 2)], {type:"application/json"}), a = document.createElement("a");
    a.href = URL.createObjectURL(blob); a.download = "configuracao_mapa_portfolio.json"; document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(a.href), 2000);
    $("wipeExport").textContent = "Configurações exportadas ✓";
  };
  $("wipeGo").onclick = () => { $("wipeGo").disabled = true; $("wipeGo").textContent = "Apagando..."; wipeAll(); };
  $("wipeCancel").focus();
};
$("cfgExport").onclick = () => {
  if (readForm()) return toast("Corrija os valores destacados antes de exportar.");
  const blob = new Blob([JSON.stringify(DRAFT, null, 2)], {type:"application/json"});
  const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = "configuracao_mapa_portfolio.json";
  document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(a.href), 2000);
};
$("cfgImport").onchange = e => {
  const f = e.target.files[0]; if (!f) return;
  f.text().then(txt => {
    try { const j = JSON.parse(txt); DRAFT = normCfg(j); cfgForm(); toast("Configuração importada. Confira e clique em Salvar."); }
    catch(err){ toast("Arquivo de configuração inválido."); }
  });
  e.target.value = "";
};

