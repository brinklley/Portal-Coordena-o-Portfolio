/* ---------------- leitura da planilha ---------------- */
/* ---------- CSV: dentro das células (uma linha por célula na coluna A) ou arquivo .csv ---------- */
/* um registro CSV (pode conter quebras de linha dentro de aspas); aspas só abrem no início do campo */
function parseCsvRecord(s, d){
  const out = []; let f = "", q = false;
  for (let i = 0; i < s.length; i++){
    const c = s[i];
    if (q){ if (c === '"'){ if (s[i+1] === '"'){ f += '"'; i++; } else q = false; } else f += c; }
    else if (c === '"' && f === "") q = true;
    else if (c === d){ out.push(f); f = ""; }
    else f += c;
  }
  out.push(f);
  return {fields: out, open: q};
}
function detectDelim(line){
  const cand = [",", ";", "\t"];
  let best = ",", bn = 0;
  cand.forEach(d => { const n = parseCsvRecord(line, d).fields.length; if (n > bn){ bn = n; best = d; } });
  return best;
}
/* Repara aspas perdidas na conversão: tenta fechar uma aspa antes de um separador
   ou abrir uma aspa depois de um separador, até o registro ter o número certo de colunas. */
function repairRecord(s, d, N){
  const r0 = parseCsvRecord(s, d);
  if (!r0.open && r0.fields.length === N) return {fields:r0.fields};
  const pos = []; for (let i = 0; i < s.length; i++) if (s[i] === d) pos.push(i);
  if (pos.length < 400){
    for (const p of pos){ const r = parseCsvRecord(s.slice(0, p) + '"' + s.slice(p), d); if (!r.open && r.fields.length === N) return {fields:r.fields, fixed:true}; }
    for (const p of pos){ const r = parseCsvRecord(s.slice(0, p + 1) + '"' + s.slice(p + 1), d); if (!r.open && r.fields.length === N) return {fields:r.fields, fixed:true}; }
  }
  return {fields:r0.fields, bad:true};
}
/* texto CSV (linhas físicas) -> tabela; novos registros começam por um ID numérico */
function csvToTable(physLines, name, imp){
  const phys = physLines.map(l => fixEnc(String(l)).replace(/\r$/, ""));
  while (phys.length && !phys[0].trim()) phys.shift();
  const headerLine = (phys.shift() || "").replace(/^\uFEFF/, "");
  const d = detectDelim(headerLine);
  const headers = parseCsvRecord(headerLine, d).fields.map(h => h.trim());
  const N = headers.length;
  const dq = d === "\t" ? "\\t" : d.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  const startRe = new RegExp(`^\\s*"?\\d+"?\\s*${dq}`);
  const recs = []; let cur = null;
  phys.forEach(l => {
    if (cur === null || startRe.test(l)){ if (cur !== null) recs.push(cur); cur = l; }
    else cur += "\n" + l;   // continuação de um campo com quebra de linha
  });
  if (cur !== null) recs.push(cur);
  const rows = [];
  recs.forEach(s => {
    if (!s.replace(new RegExp(dq, "g"), "").trim()) return;
    const r = repairRecord(s, d, N), id = (r.fields[0] || "").trim();
    if (!r.bad){
      rows.push(r.fields.map(v => { const x = v.trim(); return x === "" ? null : x; }));
      if (r.fixed) imp.fixed.push({sheet:name, id, title:(r.fields[1] || "").trim()});
    } else {
      imp.dropped.push({sheet:name, id, title:(r.fields[1] || "").trim().slice(0, 90),
        why: r.fields.length < N ? `registro incompleto (${r.fields.length} de ${N} colunas)` : `colunas a mais (${r.fields.length} de ${N}), aspas não puderam ser reparadas`});
    }
  });
  imp.csvSheets.push({sheet:name, delim: d === "\t" ? "tab" : d, rows: rows.length});
  return {headers, rows};
}
/* aba é CSV dentro das células? cabeçalho numa única célula com separador e coluna ID */
function isCsvSheet(arr){
  if (!arr.length) return false;
  const first = arr[0].filter(filled);
  if (first.length !== 1 || typeof first[0] !== "string") return false;
  const d = detectDelim(first[0]), h = parseCsvRecord(first[0], d).fields.map(norm);
  if (h.length < 3 || !h.includes("id")) return false;
  const sample = arr.slice(1, 50);
  return sample.filter(r => r.filter(filled).length <= 1).length >= sample.length * 0.9;
}
function tablesFromWorkbook(wb, imp){
  const out = {};
  wb.SheetNames.forEach(name=>{
    const ws = wb.Sheets[name];
    const arr = XLSX.utils.sheet_to_json(ws,{header:1, raw:true, defval:null, blankrows:false});
    if (!arr.length) return;
    const nm = fixEnc(name).trim();
    if (isCsvSheet(arr)){
      out[nm] = csvToTable(arr.map(r => r.find(filled)).filter(v => v != null).flatMap(v => String(v).split(/\r?\n/)), nm, imp);
      return;
    }
    const headers = arr[0].map(h => typeof h === "string" ? fixEnc(h).trim() : h);
    const rows = arr.slice(1).map(r => r.map(v => typeof v === "string" ? fixEnc(v) : v))
                     .filter(r => r.some(filled));
    out[nm] = {headers, rows};
  });
  return out;
}
function decodeText(buf){
  const b = new Uint8Array(buf);
  try { return new TextDecoder("utf-8", {fatal:true}).decode(b); }
  catch(e){ return new TextDecoder("windows-1252").decode(b); }
}

