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

# Decisão 0070: pedido do usuário — o selo de tag no card do épico ("PAUSADO 1") é um AGREGADO dos
# itens dos times vinculados a ele (não a tag do próprio épico), mas isso não ficava claro — o usuário
# checou o épico no Azure DevOps (sem tag nenhuma) e achou que o Portal estava errado. O título do selo
# já dizia "nos times", mas passou despercebido; agora o selo é clicável e abre a lista exata dos itens
# que entram naquela contagem (mesma transparência do Report F4P/Visão Analítica).

def _setup_epico_com_tag(page, *, team, sem=None):
    """Épico com 3 itens de time: 1 reservado+aberto com a tag PAUSADO (deve contar), 1 aberto sem
    tag (não deve contar) e 1 já entregue (Vazão) com a mesma tag PAUSADO (não deve contar — o selo só
    soma itens ainda abertos)."""
    page.evaluate("""(args)=>{
      const {team} = args;
      S.model.teamFlow[team] = ["Backlog", "WIP", "Vazao"];
      CFG.flow[norm(team)] = {cat:{wip:"wip", vazao:"vazao"}, ct:[]};
      const mk = (id, stName, tags, deploy) => S.model.ops.set(id, {id, title:"Item "+id, team, type:"User Story", stName,
        deploy: deploy ? new Date(2026,0,5) : null, ready: new Date(2026,0,1), tags: tags || []});
      mk(team+"_aberto_pausado", "Backlog", ["PAUSADO"], false);
      mk(team+"_aberto_sem_tag", "WIP", [], false);
      mk(team+"_entregue_pausado", "Vazao", ["PAUSADO"], true);
      const iniId = "INI_"+team, relId = "REL_"+team, epiId = "EPI_"+team;
      S.model.inis.set(iniId, {lvl:"ini", id:iniId, valid:true, title:"Iniciativa "+team, exec:null, owner:null, st:0, rels:[relId]});
      S.model.rels.set(relId, {lvl:"rel", id:relId, valid:true, title:"Release "+team, parent:iniId, st:0, epis:[epiId]});
      S.model.epis.set(epiId, {lvl:"epi", id:epiId, valid:true, title:"Épico "+team, parent:relId, target:null, interno:null, st:0,
        ops:[team+"_aberto_pausado", team+"_aberto_sem_tag", team+"_entregue_pausado"], type:"Epic"});
      S.f.team = ""; S.path = {ini:iniId, rel:relId}; S.expand = false;
      recomputeHealth(); render();
    }""", {"team": team})

def test_selo_de_tag_do_epico_conta_so_itens_abertos_dos_times(page):
    carregar(page, "f4p.xlsx")
    _setup_epico_com_tag(page, team="ETAG1")
    d = page.evaluate("epiMetrics(S.model.epis.get('EPI_ETAG1'), '').tagCount")
    assert d.get("paused") == 1   # só o item aberto com a tag; o entregue não entra

def test_clique_no_selo_da_tag_abre_a_lista_exata_dos_itens(page):
    """Mesma transparência do Report F4P/Visão Analítica: o modal mostra exatamente os itens que
    entram na contagem do selo — nem o item sem a tag, nem o item já entregue com a mesma tag."""
    carregar(page, "f4p.xlsx")
    _setup_epico_com_tag(page, team="ETAG2")
    page.click('[data-epi-tag-epi="EPI_ETAG2"][data-epi-tag-id="paused"]')
    assert page.is_visible("#f4pItemsBg")
    assert page.locator("#f4pItemsBody tbody tr").count() == 1
    assert "ETAG2_aberto_pausado" in page.inner_text("#f4pItemsBody")
    assert "ETAG2_entregue_pausado" not in page.inner_text("#f4pItemsBody")
    assert "ETAG2_aberto_sem_tag" not in page.inner_text("#f4pItemsBody")

def test_clique_no_selo_da_tag_nao_seleciona_o_epico(page):
    """O selo fica dentro do card do épico — clicar nele deve abrir só o modal, sem também disparar o
    comportamento normal de clique no card (selecionar/navegar o épico)."""
    carregar(page, "f4p.xlsx")
    _setup_epico_com_tag(page, team="ETAG3")
    assert page.evaluate("S.path.epi") != "EPI_ETAG3"
    page.click('[data-epi-tag-epi="EPI_ETAG3"][data-epi-tag-id="paused"]')
    assert page.evaluate("S.path.epi") != "EPI_ETAG3"

def test_ct_do_epico_so_com_tipos_configurados(page):
    carregar(page, "times.xlsx")
    m = page.evaluate("(()=>{const e=[...S.model.epis.values()].find(e=>e.ops.length>3); const m=epiMetrics(e,''); return {n:m.n, ctN:m.ctN}})()")
    tipos = page.evaluate("(()=>{const e=[...S.model.epis.values()].find(e=>e.ops.length>3); return e.ops.map(k=>S.model.ops.get(k).type)})()")
    assert m["ctN"] == sum(t in ("User Story", "Technical Story") for t in tipos) and m["ctN"] < m["n"]
