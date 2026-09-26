"""CycleTime, alertas e tags (docs/regras-de-negocio.md, seções 4 a 6)."""
import datetime as dt, openpyxl
from conftest import carregar, FIX

def test_ct_do_item_entre_ready_e_pronto_para_deploy(page):
    carregar(page, "times.xlsx")
    ws = openpyxl.load_workbook(FIX / "times.xlsx")["TIME CORE"]
    cab = [c.value for c in ws[1]]
    for r in ws.iter_rows(min_row=2, values_only=True):
        d = dict(zip(cab, r))
        if d["READY / PRONTO PARA DEV"] and d["Pronto para Deploy"]:
            esperado = (d["Pronto para Deploy"].date() - d["READY / PRONTO PARA DEV"].date()).days
            assert page.evaluate(f"[...S.model.ops.values()].find(o=>o.team==='CORE'&&o.id==='{d['ID']}').ct") == esperado
            break

def test_alertas_por_limite_do_time(page):
    carregar(page, "times.xlsx")
    page.evaluate("()=>{ CFG.teams={core:{warn:1,max:2,out:5}}; recomputeHealth(); render(); }")
    kinds = page.evaluate("""(()=>{const c={}; [...S.model.ops.values()].filter(o=>o.team==='CORE').forEach(o=>o.reasons.forEach(r=>{c[r.lv+'/'+r.kind]=(c[r.lv+'/'+r.kind]||0)+1})); return c})()""")
    assert kinds.get("outlier/ct", 0) > 0          # CT ≥ outlier
    # todo item do CORE com CT ≥ 5 (outlier) é outlier; entre 3 e 4 é atraso; o time planejado avalia também os concluídos
    r = page.evaluate("""(()=>{const ops=[...S.model.ops.values()].filter(o=>o.team==='CORE'&&o.ct!=null);
      return {out:ops.filter(o=>o.ct>=5).every(o=>o.outlier), atraso:ops.filter(o=>o.ct>2&&o.ct<5).every(o=>o.overCt&&!o.outlier),
              ok:ops.filter(o=>o.ct<=2&&o.deploy).every(o=>!o.overCt&&!o.outlier), n:ops.length}})()""")
    assert r["n"] > 0 and r["out"] and r["atraso"] and r["ok"]

def test_tag_blocked_reconhecida(page):
    carregar(page, "times.xlsx")
    assert page.evaluate("[...S.model.ops.values()].filter(o=>o.tagHits.some(t=>t.id==='blocked')).length") > 0

def test_ct_do_epico_so_com_tipos_configurados(page):
    carregar(page, "times.xlsx")
    m = page.evaluate("(()=>{const e=[...S.model.epis.values()].find(e=>e.ops.length>3); const m=epiMetrics(e,''); return {n:m.n, ctN:m.ctN}})()")
    tipos = page.evaluate("(()=>{const e=[...S.model.epis.values()].find(e=>e.ops.length>3); return e.ops.map(k=>S.model.ops.get(k).type)})()")
    assert m["ctN"] == sum(t in ("User Story", "Technical Story") for t in tipos) and m["ctN"] < m["n"]
