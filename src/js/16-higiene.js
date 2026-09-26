/* ---------------- higiene de dados ---------------- */
function hygieneCount(){ const w = S.model.warn; return ((S.importNotes || {}).azure ? S.importNotes.azure.divergent.length : 0) + w.orphans.length + w.badEpi.length + w.relNoEpi.length + ((S.importNotes || {}).dropped || []).length; }
function importHygiene(){
  const n = S.importNotes;
  if (n && n.azure){
    const a = n.azure; let h = `<div class="hy-group"><h4>Carga do Azure DevOps</h4><p>${a.removed} ${a.removed === 1 ? "item no estado Removed foi excluído" : "itens no estado Removed foram excluídos"}.</p>`;
    if (a.divergent.length) h += `<p><b>${a.divergent.length} ${a.divergent.length === 1 ? "item com vínculo divergente" : "itens com vínculo divergente"}</b>: o campo ID_EPICO_UNICRED e o link Remote Related apontam para épicos diferentes (valeu o campo):</p><ul>${a.divergent.map(x => `<li>${esc(x.team)} #${esc(x.id)}: campo ${esc(x.campo)}, Remote Related ${esc(x.remoto)}</li>`).join("")}</ul>`;
    return h + `</div>`;
  }
  if (!n || (!n.csvSheets.length && !n.dropped.length && !n.replaced.length)) return "";
  let h = `<div class="hy-group"><h4>Importação da planilha</h4>`;
  if (n.csvSheets.length) h += `<p>Formato CSV detectado e convertido automaticamente em: ${n.csvSheets.map(c => `<b>${esc(c.sheet)}</b> (${c.rows} registros)`).join(", ")}.</p>`;
  if (n.fixed.length) h += `<p>${n.fixed.length} ${n.fixed.length === 1 ? "registro tinha" : "registros tinham"} aspas quebradas (por exemplo, título com quebra de linha) e ${n.fixed.length === 1 ? "foi reparado" : "foram reparados"}:</p><ul>${n.fixed.map(x => `<li>${esc(x.sheet)} #${esc(x.id)} ${esc(x.title)}</li>`).join("")}</ul>`;
  if (n.dropped.length) h += `<p style="margin-top:8px"><b>${n.dropped.length} ${n.dropped.length === 1 ? "registro ignorado" : "registros ignorados"}</b> por estarem danificados; exporte de novo da ferramenta de origem para recuperá-${n.dropped.length === 1 ? "lo" : "los"}:</p><ul>${n.dropped.map(x => `<li>${esc(x.sheet)} #${esc(x.id)} ${esc(x.title)} <span style="color:var(--ink-3)">(${esc(x.why)})</span></li>`).join("")}</ul>`;
  if (n.replaced.length) h += `<p style="margin-top:8px">Abas repetidas entre os arquivos (valeu a última): ${n.replaced.map(x => esc(x.sheet)).join(", ")}.</p>`;
  return h + `</div>`;
}
$("btnHygiene").onclick = () => {
  S.detailKey = null;
  const w = S.model.warn;
  const grp = (t, p, list, f) => `<div class="hy-group"><h4>${t} (${list.length})</h4><p>${p}</p>${list.length ? `<ul>${list.slice(0,300).map(f).join("")}</ul>` : ""}</div>`;
  $("dTitle").textContent = "Higiene de dados";
  $("dBody").innerHTML =
    importHygiene() +
    `<p style="font-size:13px;color:var(--ink-2);margin-top:0">Estes registros não aparecem no quadro porque falta uma chave que comprove o vínculo. Corrigir na origem faz eles aparecerem.</p>` +
    grp("Itens órfãos nos times", "ID_EPICO_UNICRED não corresponde a nenhum ID da aba Épico.", w.orphans, o => `<li>${esc(o.team)} #${esc(o.id)} ${esc(o.title)} <span style="color:var(--ink-3)">(épico ${esc(o.epicoId ?? "vazio")})</span></li>`) +
    grp("Épicos inválidos", "Sem título ou com Parent que não existe na aba Release.", w.badEpi, e => `<li>#${esc(e.id)} ${esc(e.title ?? "(sem título)")} <span style="color:var(--ink-3)">(Parent ${esc(e.parent ?? "vazio")})</span></li>`) +
    grp("Releases sem iniciativa", "O Parent da release não existe entre as iniciativas carregadas.", w.relNoEpi, r => `<li>#${esc(r.id)} ${esc(r.title)}${r.reason ? ` <span style="color:var(--ink-3)">(${esc(r.reason)})</span>` : ""}</li>`) +

    (w.badDates ? `<div class="hy-group"><h4>Datas não reconhecidas (${w.badDates})</h4><p>Target Date em formato que não é data; tratadas como vazias.</p></div>` : "");
  openDrawer();
};

