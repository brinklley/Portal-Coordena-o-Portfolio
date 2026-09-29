/* ---------- configuração (guardada no navegador; exportável em .json) ---------- */
const CFG_KEY = "mapaPortfolio.config.v1";
const TAG_DEFAULTS = () => [
  {id:"blocked", name:"BLOCKED",   aliases:["blocked","bloqueado","impedido"], color:"#E57373", level:"alert", when:"since"},
  {id:"paused",  name:"PAUSADO",   aliases:["pausado","paused","pausa"],       color:"#4B5563", level:"warn",  when:"since"},
  {id:"urgent",  name:"URGENTE",   aliases:["urgente","urgent"],               color:"#FDE047", level:"info",  when:"since"},
  {id:"fixed",   name:"DATA FIXA", aliases:["data fixa","datafixa","fixed date"], color:"#7DD3FC", level:"info", when:"target"}];
const cfgDefaults = () => ({teams:{}, warnDays:30, alertDays:60, outlierDays:90, stuckDays:10, disc:null, wip:null, vazao:null,
  ctTypes:["user story","technical story","technical solution"], tags:TAG_DEFAULTS(),
  typeColors:{ini:{}, rel:{}, epi:{}, op:{}}, fields:{ini:[], rel:[], epi:[], op:[]}, ctCols:null, flow:{},
  anTag:"ROADMAP", anClassCol:"Classificação_Despesas_Comitê", anFreeze:10,
  f4p:{months:6, types:["user story","technical story"], expediteTag:"urgent", epiTypes:["epic"], usTypes:["user story"], effTypes:[], teams:{}},
  act:{bugTypes:["bug","internal bug","external bug"], cfdIncludeBugs:true},
  azure:{orgs:[], sources:[], maps:{}, mapMeta:{}, fields:{epic:"ID_EPICO_UNICRED", roadmap:"AnoSemestreRoadmap"}, excludeRemoved:true}});
/* aceita configurações antigas (ctMax + warnPct) e converte para limites por time */
function normCfg(j){
  const c = {...cfgDefaults(), ...j, teams:{...(j.teams || {})}};
  if (!Array.isArray(j.tags)) c.tags = TAG_DEFAULTS();
  if (!Array.isArray(j.ctTypes)) c.ctTypes = cfgDefaults().ctTypes;
  c.typeColors = {ini:{}, rel:{}, epi:{}, op:{}, ...(j.typeColors || {})};
  c.fields = {ini:[], rel:[], epi:[], op:[], ...(j.fields || {})};
  c.flow = {...(j.flow || {})};
  const f4pD = cfgDefaults().f4p, jf = j.f4p || {};
  c.f4p = {months: jf.months > 0 ? jf.months : f4pD.months,
    types: Array.isArray(jf.types) && jf.types.length ? jf.types : f4pD.types,
    expediteTag: typeof jf.expediteTag === "string" && jf.expediteTag ? jf.expediteTag : f4pD.expediteTag,
    epiTypes: Array.isArray(jf.epiTypes) && jf.epiTypes.length ? jf.epiTypes : f4pD.epiTypes,
    usTypes: Array.isArray(jf.usTypes) && jf.usTypes.length ? jf.usTypes : f4pD.usTypes,
    // vazio é uma configuração válida aqui (significa "todos os tipos", padrão do quadrante Eficiência
    // de fluxo) — diferente dos demais campos de tipo acima, que caem no padrão quando vazios.
    effTypes: Array.isArray(jf.effTypes) ? jf.effTypes : f4pD.effTypes,
    teams: {...(jf.teams || {})}};
  const actD = cfgDefaults().act, ja = j.act || {};
  c.act = {bugTypes: Array.isArray(ja.bugTypes) && ja.bugTypes.length ? ja.bugTypes : actD.bugTypes,
    cfdIncludeBugs: ja.cfdIncludeBugs !== false};
  const az = j.azure || {};   // tokens nunca fazem parte da configuração
  c.azure = {orgs:(az.orgs || []).map(o => ({org:o.org})), sources:az.sources || [], maps:az.maps || {}, mapMeta:az.mapMeta || {},
    fields:{epic:"ID_EPICO_UNICRED", roadmap:"AnoSemestreRoadmap", ...(az.fields || {})}, excludeRemoved: az.excludeRemoved !== false};
  if (j.ctMax) Object.entries(j.ctMax).forEach(([k, v]) => { if (!c.teams[k] && v > 0) c.teams[k] = {max:v, warn:Math.round(v * (j.warnPct || 80) / 100)}; });
  delete c.ctMax; delete c.warnPct;
  return c;
}
let CFG = (() => { try { const s = localStorage.getItem(CFG_KEY); if (s) return normCfg(JSON.parse(s)); } catch(e){} return cfgDefaults(); })();
/* limites efetivos de um time: os planejados dele ou a regra geral */
function limitsOf(team){
  const t = CFG.teams[norm(team)] || {};
  const planned = t.max > 0;
  return {planned, warn: planned ? t.warn : CFG.warnDays, max: planned ? t.max : CFG.alertDays,
    out: planned ? t.out : CFG.outlierDays, stuck: t.stuck > 0 ? t.stuck : CFG.stuckDays};
}
/* faixa de variabilidade esperada de um time (Report F4P): a planejada ou o padrão 1.5–3.5 */
function f4pRangeOf(team){
  const t = (CFG.f4p.teams || {})[norm(team)] || {};
  return {min: t.min > 0 ? t.min : 1.5, max: t.max > 0 ? t.max : 3.5, planned: t.min > 0 && t.max > 0};
}
/* meta de itens Expedite/Urgente do time no semestre (Report F4P): null quando o time não tem meta cadastrada */
function f4pUrgentMetaOf(team){
  const t = (CFG.f4p.teams || {})[norm(team)] || {};
  return t.urgentMeta != null && t.urgentMeta >= 0 ? t.urgentMeta : null;
}
/* meta de itens Technical Story do time no semestre (Report F4P): ao contrário de Urgente, tem padrão
   (6) — não fica sem meta/sem cor quando o time não cadastra um valor próprio. */
function f4pTsMetaOf(team){
  const t = (CFG.f4p.teams || {})[norm(team)] || {};
  return t.tsMeta != null && t.tsMeta >= 0 ? t.tsMeta : 6;
}
/* faixa esperada de Eficiência de Fluxo de um time (Report F4P), em pontos percentuais: a planejada ou
   o padrão 30–55. */
function f4pEffRangeOf(team){
  const t = (CFG.f4p.teams || {})[norm(team)] || {};
  return {min: t.effMin > 0 ? t.effMin : 30, max: t.effMax > 0 ? t.effMax : 55};
}
/* tag configurada como Classe de Serviço Expedite (Report F4P) e o nome dela pra exibir */
const f4pExpediteTag = () => CFG.f4p.expediteTag || "urgent";
const f4pTagName = id => (CFG.tags.find(t => t.id === id) || {}).name || id;
function saveCfg(){ try { localStorage.setItem(CFG_KEY, JSON.stringify(CFG)); return true; } catch(e){ return false; } }
/* Padrão: Vazão = de "Aguardando Deploy"/"Pronto para Deploy" até o fim; WIP = de "READY" até antes da Vazão. */
/* Padrão: Discovery = depois da primeira coluna (Backlog) até antes do WIP;
   WIP = de "READY" até antes da Vazão; Vazão = de "Aguardando/Pronto para Deploy" até o fim. */
function defaultSets(stages){
  const n = stages.map(norm);
  let v = n.findIndex(s => /aguard\w*( de| para)? deploy|pronto para deploy/.test(s));
  if (v < 0) v = n.length - 1;
  let w = n.findIndex(s => /^ready/.test(s)); if (w < 0 || w >= v) w = Math.min(1, v);
  return {disc: n.slice(Math.min(1, w), w), wip: n.slice(w, v), vazao: n.slice(v)};
}
/* conjuntos efetivos a partir de uma configuração (salva ou rascunho) */
function resolveSets(c, stages){
  const names = stages.map(norm), def = defaultSets(stages), has = a => Array.isArray(a) && a.some(x => names.includes(x));
  const custom = has(c.wip) || has(c.vazao) || has(c.disc);
  if (!custom) return {custom:false, ...def};
  const wip = (c.wip || []).filter(x => names.includes(x)), vazao = (c.vazao || []).filter(x => names.includes(x));
  // configurações antigas sem Discovery: usa o padrão nas colunas que não são WIP nem Vazão
  const disc = Array.isArray(c.disc) ? c.disc.filter(x => names.includes(x)) : def.disc.filter(x => !wip.includes(x) && !vazao.includes(x));
  return {custom:true, disc, wip, vazao};
}
/* Configuração do fluxo de um time: categoria de cada coluna e colunas do CT.
   Ordem de prioridade: configuração do próprio time > configuração antiga (única) > padrão. */
/* Times conhecidos: os que têm dados carregados e os cadastrados como fontes operacionais do Azure
   (estes aparecem na configuração mesmo antes da primeira carga). */
function cfgTeams(c){
  const list = S.model ? [...S.model.teams] : [];
  ((c || CFG).azure && (c || CFG).azure.sources || []).filter(s => s.role === "op").forEach(s => {
    const name = s.alias || s.team; if (!list.some(x => norm(x) === norm(name))) list.push(name);
  });
  return list;
}
/* Colunas do fluxo de um time: as dos dados carregados ou, antes da carga, as guardadas no cadastro da fonte. */
function stagesOf(team, c){
  const loaded = S.model && S.model.teamFlow[team];
  if (loaded && loaded.length) return loaded;
  const src = ((c || CFG).azure && (c || CFG).azure.sources || []).find(s => s.role === "op" && norm(s.alias || s.team) === norm(team));
  return (src && src.stages) || [];
}
const hasData = team => !!(S.model && S.model.teams.includes(team));
function teamFlowCfg(team, cfg){
  cfg = cfg || CFG;
  const stages = stagesOf(team, cfg), n = stages.map(norm);
  const t = (cfg.flow || {})[norm(team)];
  let cat;
  if (t && t.cat) cat = n.map(x => t.cat[x] || "none");
  else { const r = resolveSets(cfg, stages); cat = n.map(x => r.disc.includes(x) ? "disc" : r.wip.includes(x) ? "wip" : r.vazao.includes(x) ? "vazao" : "none"); }
  let ct;
  if (t && Array.isArray(t.ct)) ct = t.ct.filter(x => n.includes(x));
  else if (Array.isArray(cfg.ctCols) && cfg.ctCols.length) ct = cfg.ctCols.filter(x => n.includes(x));
  else { const a = n.indexOf(CT_DEF.entry), b = n.indexOf(CT_DEF.exit); ct = a >= 0 && b >= a ? n.slice(a, b + 1) : []; }
  // touch/waiting time (quadrante Eficiência de Fluxo, decisão 0031): estilo "Queueing Stages" do
  // Actionable Agile (ferramenta de Analytics citada pelo usuário como referência) — o usuário marca só as
  // colunas de Fila de espera (waiting time); as demais contam como Touch time automaticamente, sem um
  // terceiro estado "sem classificação".
  const time = t && t.time ? n.map(x => t.time[x] === "wait" ? "wait" : "touch") : n.map(() => "touch");
  return {stages, n, cat, ct, time};
}
function teamCfg(team){ S.flowCache = S.flowCache || {}; return S.flowCache[team] || (S.flowCache[team] = teamFlowCfg(team)); }
/* categoria da coluna em que o item está, pela configuração do time dele */
function catOf(o){ const c = teamCfg(o.team), i = c.n.indexOf(norm(o.stName)); return i >= 0 ? c.cat[i] : "none"; }
/* classificação de touch/waiting time de uma coluna do fluxo do time (Report F4P, Eficiência de Fluxo);
   sem marcação, a coluna é Touch time (só a Fila de espera precisa ser marcada). */
function flowTimeOf(team, colName){ const c = teamCfg(team), i = c.n.indexOf(norm(colName)); return i >= 0 ? c.time[i] : "touch"; }
function flowSets(){
  if (S.sets) return S.sets;
  const r = resolveSets(CFG, S.model.stages.op);
  S.sets = {disc: new Set(r.disc), wip: new Set(r.wip), vazao: new Set(r.vazao)};
  return S.sets;
}
const pctOf = (a, b) => Math.round(a / b * 100);
const fmtL = d => d ? d.toLocaleDateString("pt-BR", {day:"2-digit", month:"2-digit", year:"numeric"}) : "--";
const vezes = x => (Math.round(x * 10) / 10).toString().replace(".", ",") + "×";
const dd = n => `${n} ${Math.abs(n) === 1 ? "dia" : "dias"}`;
/* CT de cada item: entra na primeira coluna marcada do fluxo do time e sai na última.
   Padrão: de READY / PRONTO PARA DEV até Pronto para Deploy. */
const CT_DEF = {entry:"ready / pronto para dev", exit:"pronto para deploy"};
function ctDefaultCols(stages){
  const n = stages.map(norm), a = n.indexOf(CT_DEF.entry), b = n.indexOf(CT_DEF.exit);
  return a >= 0 && b >= a ? n.slice(a, b + 1) : [];
}
const ctCustom = () => (Array.isArray(CFG.ctCols) && CFG.ctCols.length > 0) || Object.values(CFG.flow || {}).some(t => Array.isArray(t.ct));
function ctColsOf(team, cfg){
  const tc = cfg === CFG ? teamCfg(team) : teamFlowCfg(team, cfg), flow = tc.stages, n = tc.n;
  const s = new Set(tc.ct), idx = n.map((x, i) => s.has(x) ? i : -1).filter(i => i >= 0);
  if (!idx.length) return null;
  const ai = idx[0], bi = idx[idx.length - 1];
  return {entry:flow[ai], exit:flow[bi], ai, bi};
}
function recomputeCt(){
  const cache = {};
  S.model.ops.forEach(o => {
    const c = (o.team in cache) ? cache[o.team] : (cache[o.team] = ctColsOf(o.team, CFG));
    o.ctCols = c;
    if (!c){ o.ready = null; o.deploy = null; o.ct = null; return; }
    const n = (S.model.teamFlow[o.team] || []).map(norm);
    // entrada: data da primeira coluna marcada (ou a primeira preenchida até a saída, se o item pulou a entrada)
    let start = o.fd[n[c.ai]] || null;
    for (let i = c.ai + 1; !start && i <= c.bi; i++) start = o.fd[n[i]] || null;
    // saída: data da última coluna marcada (ou a primeira coluna preenchida depois dela)
    let end = o.fd[n[c.bi]] || null;
    for (let i = c.bi + 1; !end && i < n.length; i++) end = o.fd[n[i]] || null;
    o.ready = start; o.deploy = end;
    o.ct = start ? days(start, end && end >= start ? end : TODAY) : null;
  });
}
const ctLabels = () => ctCustom() ? ["Início CT", "Fim CT"] : ["Ready", "Deploy"];
function recomputeHealth(){
  if (!S.model) return;
  S.flowCache = {};
  recomputeCt();
  S.sets = null;
  S.model.ops.forEach(o => {
    const r = [], L = limitsOf(o.team), wip = !!(o.ready && !o.deploy), ct = o.ct;
    const meta = L.planned ? `CT máximo de ${o.team}` : `limite geral`;
    const cfgTip = L.planned ? "" : ` ${o.team} ainda não tem CT planejado: configure o CT máximo do time para alertas mais precisos.`;
    // CycleTime: times planejados avaliam itens em andamento e concluídos; a regra geral, só os em andamento
    if (ct != null && (L.planned || wip)){
      const pct = L.max > 0 ? pctOf(ct, L.max) : null;
      const meter = L.max > 0 ? {ct, max:L.max, warn:L.warn, out:L.out} : null;
      if (L.out > 0 && ct >= L.out){
        r.push({lv:"outlier", kind:"ct", label:"Outlier", meter, over: L.max > 0 ? ct - L.max : 0,
          text: `CycleTime de ${dd(ct)}, ${L.max > 0 ? `${vezes(ct / L.max)} o ${meta} (${dd(L.max)}) e ` : ""}acima do ponto de outlier (${dd(L.out)}).`,
          action: wip
            ? "Item fora do padrão e ainda aberto: trate como prioridade, confirme se ainda faz sentido entregá-lo como está e considere dividi-lo."
            : "Item concluído muito fora do padrão: investigue a causa-raiz na retrospectiva. Outliers distorcem as médias e a previsibilidade do time."});
      } else if (L.max > 0 && ct > L.max){
        r.push({lv:"alert", kind:"ct", label:"Atraso", meter, over: ct - L.max,
          text: wip
            ? `Ultrapassou em ${dd(ct - L.max)} o ${meta}: está com ${dd(ct)} de CT atual, ${pct}% da meta de ${dd(L.max)}. Cada dia a mais amplia o atraso.`
            : `Concluído com ${dd(ct)} de CT, ${dd(ct - L.max)} acima do ${meta} (${dd(L.max)}), ${pct}% da meta.`,
          action: wip
            ? "Identifique o que está travando a finalização (dependência, revisão, ambiente) e avalie dividir o item para entregar valor antes."
            : "Vale entender por que passou do limite: o item era grande demais ou ficou esperando em alguma etapa?" + cfgTip});
      } else if (wip && L.warn > 0 && ct >= L.warn){
        r.push({lv:"warn", kind:"ct", label:"Atenção", meter,
          text: L.max > 0
            ? `Já consumiu ${pct}% do ${meta}: está com ${dd(ct)} de CT atual e a meta é ficar abaixo de ${dd(L.max)}. Restam ${dd(L.max - ct)} para não atrasar.`
            : `Em andamento há ${dd(ct)}.`,
          action: "Agir agora evita o atraso: verifique impedimentos, priorize a finalização em vez de começar itens novos e combine com o time o próximo passo." + cfgTip});
      }
    }
    // tags cadastradas (cor do card e alertas nos pais); alertas só para itens ainda abertos
    const tagNorm = o.tags.map(norm);
    o.tagHits = (CFG.tags || []).filter(tg => [tg.name, ...(tg.aliases || [])].map(norm).some(a => a && tagNorm.includes(a)) || (tg.id === "blocked" && o.blocked));
    const open = catOf(o) !== "vazao";
    if (open) o.tagHits.forEach(tg => {
      if (!tg.level || tg.level === "none") return;
      let since = o.stDate, sinceTxt = "";
      if (tg.id === "blocked" && o.blocked && o.blockedDays > 0){ since = new Date(TODAY.getFullYear(), TODAY.getMonth(), TODAY.getDate() - o.blockedDays); }
      else if (o.stDate) sinceTxt = `, na coluna “${o.stName}”`;
      const nd = since ? days(since, TODAY) : null;
      const desde = since ? `desde ${fmtL(since)} (há ${dd(nd)})${sinceTxt}` : "sem data de referência na planilha";
      let text, action;
      if (tg.when === "target"){
        if (o.target){ const left = days(TODAY, o.target);
          text = `Com ${tg.name.toLowerCase()} no time ${o.team} para o dia ${fmtL(o.target)} (${left >= 0 ? `faltam ${dd(left)}` : `venceu há ${dd(-left)}`}).`;
          action = left < 0 ? "A data já passou: combine com quem depende da entrega um novo compromisso e registre o motivo." : "Acompanhe o risco de não cumprir a data e antecipe impedimentos; se houver risco, avise cedo quem depende da entrega."; }
        else { text = `Com ${tg.name.toLowerCase()} no time ${o.team}, mas a data não está na planilha.`;
          action = "Inclua a coluna Target Date na exportação dos times para acompanhar o prazo aqui."; }
      } else if (tg.id === "blocked"){
        text = `Bloqueado no time ${o.team} ${desde}.`;
        action = "Bloqueio é tempo de ciclo perdido: identifique quem pode remover o impedimento e combine um prazo para destravar.";
      } else if (tg.id === "paused"){
        text = `Pausado no time ${o.team} ${desde}, para priorizar outro trabalho.`;
        action = "Confirme se a pausa ainda faz sentido e quando o item volta a andar; pausas longas escondem trabalho parado.";
      } else if (tg.id === "urgent"){
        text = `Priorizado como urgente no time ${o.team} ${desde}.`;
        action = "Garanta foco do time nele e evite que outros trabalhos concorram com a prioridade.";
      } else {
        text = `Marcado como “${tg.name}” no time ${o.team} ${desde}.`;
      }
      r.push({lv:tg.level, kind:"tag", tag:tg.id, tagName:tg.name, label:tg.name, color:tg.color, since, target:o.target, text, action});
    });
    // parado na mesma coluna: só para itens em colunas de WIP
    o.stuck = null;
    if (L.stuck > 0 && o.stDate && catOf(o) === "wip"){
      const d = days(o.stDate, TODAY);
      if (d >= L.stuck){
        o.stuck = d;
        r.push({lv:"warn", kind:"stuck", label:"Parado", stuck:d,
          text: `Sem avançar há ${dd(d)} na coluna “${o.stName}”, ${vezes(d / L.stuck)} o limite de ${dd(L.stuck)} para ${o.team}.`,
          action: "Item parado costuma indicar bloqueio, espera por outra pessoa ou fila na etapa. Pergunte na daily o que falta para ele andar e se alguém pode ajudar."});
      }
    }
    o.reasons = r; o.health = worst(r.map(x => x.lv));
    o.overCt = r.some(x => x.kind === "ct" && x.lv === "alert"); o.outlier = r.some(x => x.lv === "outlier");
  });
}

const LV = {ini:"Iniciativas", rel:"Releases", epi:"Épicos", op:"Operacional dos times"};
const LVC = {ini:"var(--ini)", rel:"var(--rel)", epi:"var(--epi)", op:"var(--op)"};
const RANK = {ok:0, info:0, warn:1, alert:2, outlier:3};
const worst = arr => arr.reduce((a,b)=> RANK[b]>RANK[a]?b:a, "ok");

