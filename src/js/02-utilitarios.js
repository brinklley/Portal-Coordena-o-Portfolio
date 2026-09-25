/* ---------------- utilitários ---------------- */
const norm = s => String(s ?? "").normalize("NFD").replace(/[\u0300-\u036f]/g,"").replace(/\s+/g," ").trim().toLowerCase();
const esc = s => String(s ?? "").replace(/[&<>"']/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const CP1252 = {"\u20AC":0x80,"\u201A":0x82,"\u0192":0x83,"\u201E":0x84,"\u2026":0x85,"\u2020":0x86,"\u2021":0x87,"\u02C6":0x88,"\u2030":0x89,"\u0160":0x8A,"\u2039":0x8B,"\u0152":0x8C,"\u017D":0x8E,"\u2018":0x91,"\u2019":0x92,"\u201C":0x93,"\u201D":0x94,"\u2022":0x95,"\u2013":0x96,"\u2014":0x97,"\u02DC":0x98,"\u2122":0x99,"\u0161":0x9A,"\u203A":0x9B,"\u0153":0x9C,"\u017E":0x9E,"\u0178":0x9F};
const dec = new TextDecoder("utf-8",{fatal:true});
function fixEnc(s){
  if (typeof s !== "string" || !/[ÃÂ]/.test(s)) return s;
  try{
    const bytes = new Uint8Array([...s].map(ch=>{
      const c = ch.charCodeAt(0);
      if (c < 256) return c;
      if (CP1252[ch] !== undefined) return CP1252[ch];
      throw new Error("x");
    }));
    const fixed = dec.decode(bytes);
    return /[ÃÂ]/.test(fixed) ? s : fixed;
  }catch(e){ return s; }
}
const filled = v => !(v === null || v === undefined || (typeof v === "string" && v.trim() === "") || (v instanceof Date && isNaN(v)));
function toDate(v){
  if (!filled(v)) return null;
  if (v instanceof Date) return new Date(v.getFullYear(), v.getMonth(), v.getDate());
  if (typeof v === "number"){
    if (v < 1 || v > 80000) return null;
    const d = new Date(Math.round((v - 25569) * 864e5));
    return new Date(d.getUTCFullYear(), d.getUTCMonth(), d.getUTCDate());
  }
  const s = String(v).trim();
  let m = s.match(/^(\d{1,2})\/(\d{1,2})\/(\d{2,4})/);
  if (m){ let y=+m[3]; if (y<100) y+=2000; const d=new Date(y, +m[2]-1, +m[1]); return isNaN(d)?null:d; }
  m = s.match(/^(\d{4})-(\d{2})-(\d{2})/);
  if (m){ const d=new Date(+m[1], +m[2]-1, +m[3]); return isNaN(d)?null:d; }
  return null;
}
const TODAY = (()=>{const d=new Date(); return new Date(d.getFullYear(), d.getMonth(), d.getDate());})();
const days = (a,b) => Math.round((b - a) / 864e5);
const fmt = d => d ? d.toLocaleDateString("pt-BR",{day:"2-digit",month:"2-digit",year:"2-digit"}) : "--";
const semestre = d => d ? `${d.getFullYear()} ${d.getMonth() < 6 ? 1 : 2}º Semestre` : null;
const shortSem = s => s ? s.replace(/º Semestre/i,"S").replace(/(\d{4}) (\d)S/,"$1 $2S") : "--";
function nid(v){
  if (!filled(v)) return null;
  if (typeof v === "number") return String(Math.trunc(v));
  const s = String(v).trim();
  return /^\d+(\.0+)?$/.test(s) ? String(parseInt(s,10)) : s;
}
/* percentil por interpolação linear, igual ao PERCENTIL.INC do Excel; array já ordenado ascendente */
function percentil(a, p){
  const n = a.length; if (!n) return null; if (n === 1) return a[0];
  const rank = p * (n - 1), lo = Math.floor(rank), hi = Math.ceil(rank);
  return lo === hi ? a[lo] : a[lo] + (rank - lo) * (a[hi] - a[lo]);
}
const dec1 = x => (x == null || isNaN(x)) ? "--" : (Math.round(x * 10) / 10).toFixed(1).replace(".", ",");
function colIdx(headers, name){ const n = norm(name); return headers.findIndex(h => norm(h) === n); }
function flowCols(headers, start, end){
  const ns = norm(start), ne = norm(end);
  let si = -1, ei = -1;
  headers.forEach((h,i)=>{ const n = norm(h); if (n === ns && si < 0) si = i; if (n === ne) ei = i; });
  if (si < 0 || ei < 0 || ei < si) return null;
  const cols = [];
  for (let i = si; i <= ei; i++) cols.push({i, name: String(headers[i] ?? `Coluna ${i+1}`).trim()});
  return cols;
}
function statusOf(row, flow){
  let last = -1;
  flow.forEach((c,k)=>{ if (filled(row[c.i])) last = k; });
  return last;   // -1 = Sem status
}

