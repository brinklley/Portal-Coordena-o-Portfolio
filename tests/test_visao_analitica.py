"""Visão analítica do roadmap do time (docs/regras-de-negocio.md §10). Decisão 0027: Projetada e
Capacidade passam a ser sempre a soma dos números mostrados por épico na tabela (não uma contagem à
parte), a linha do épico mostra a quantidade reservada, e os dois números do cabeçalho ficam clicáveis
(mesma transparência do Report F4P: abrem a lista dos itens exatos que entram na soma)."""
from conftest import carregar

def _setup_epico(page, *, team, itens, sem, tag=None):
    """Monta uma cadeia sintética Iniciativa → Release → Épico → itens do time, e habilita o filtro
    de Time + Roadmap executivo para o semestre dado. `itens` é uma lista de dicts (stName, tags, deploy)."""
    page.evaluate("""(args)=>{
      const {team, itens, sem, tag} = args;
      S.model.teamFlow[team] = ["Backlog", "WIP", "Vazao"];
      CFG.flow[norm(team)] = {cat:{wip:"wip", vazao:"vazao"}, ct:[]};
      const opKeys = itens.map((it, idx) => {
        const k = `${team}_op${idx}`;
        S.model.ops.set(k, {id:k, title:"Item "+idx, team, type:"User Story", stName: it.stName, deploy: it.deploy ? new Date(it.deploy) : null,
          ready: it.stName !== "Backlog" ? new Date(2026,0,1) : null, tags: it.tags || []});
        return k;
      });
      const iniId = `INI_${team}`, relId = `REL_${team}`, epiId = `EPI_${team}`;
      S.model.inis.set(iniId, {id:iniId, valid:true, title:"Iniciativa "+team, exec:sem, owner:null, rels:[relId]});
      S.model.rels.set(relId, {id:relId, valid:true, title:"Release "+team, parent:iniId, epis:[epiId]});
      S.model.epis.set(epiId, {id:epiId, valid:true, title:"Épico "+team, parent:relId, target:null, interno:null, st:0, ops:opKeys, type:"Epic"});
      S.f.team = team; S.f.exec = sem;
      render();
    }""", {"team": team, "itens": itens, "sem": sem, "tag": tag})

def test_projetada_e_soma_do_qtd_dos_epicos_da_tabela(page):
    carregar(page, "f4p.xlsx")
    r = page.evaluate("""()=>{
      const sem = semestre(TODAY);
      return sem;
    }""")
    _setup_epico(page, team="AN_PROJ", sem=r, itens=[
        {"stName": "Backlog"}, {"stName": "WIP"}, {"stName": "Vazao", "deploy": "2026-01-05"},
    ])
    d = page.evaluate("anData()")
    assert d["proj"] == 3
    assert sum(row["qtd"] for row in d["rows"]) == d["proj"]

def test_capacidade_e_soma_dos_reservados_dos_epicos_da_tabela(page):
    carregar(page, "f4p.xlsx")
    sem = page.evaluate("semestre(TODAY)")
    _setup_epico(page, team="AN_CAP", sem=sem, itens=[
        {"stName": "Backlog", "tags": ["ROADMAP"]},
        {"stName": "WIP", "tags": ["ROADMAP"]},
        {"stName": "WIP", "tags": []},
    ])
    d = page.evaluate("anData()")
    assert d["cap"] == 2
    assert sum(len(row["reservados"]) for row in d["rows"]) == d["cap"]

def test_capacidade_usa_a_tag_configuravel(page):
    carregar(page, "f4p.xlsx")
    sem = page.evaluate("semestre(TODAY)")
    page.evaluate("()=>{ CFG.anTag = 'CAPACIDADE'; }")
    _setup_epico(page, team="AN_CAP2", sem=sem, itens=[
        {"stName": "Backlog", "tags": ["CAPACIDADE"]},
        {"stName": "Backlog", "tags": ["ROADMAP"]},   # tag antiga: não conta mais
    ])
    d = page.evaluate("anData()")
    page.evaluate("()=>{ CFG.anTag = 'ROADMAP'; }")
    assert d["cap"] == 1

def test_linha_do_epico_mostra_quantidade_reservada(page):
    carregar(page, "f4p.xlsx")
    sem = page.evaluate("semestre(TODAY)")
    _setup_epico(page, team="AN_ROW", sem=sem, itens=[
        {"stName": "Backlog", "tags": ["ROADMAP"]},
        {"stName": "WIP", "tags": []},
    ])
    page.click("#anTab")
    txt = page.inner_text("#anBody")
    assert "1 reservado" in txt

def test_clique_na_capacidade_abre_lista_so_dos_itens_com_a_tag(page):
    carregar(page, "f4p.xlsx")
    sem = page.evaluate("semestre(TODAY)")
    _setup_epico(page, team="AN_CLK_CAP", sem=sem, itens=[
        {"stName": "Backlog", "tags": ["ROADMAP"]},
        {"stName": "WIP", "tags": []},
    ])
    page.click("#anTab")
    page.click('button[data-an-items="cap"]')
    assert page.is_visible("#f4pItemsBg")
    assert page.locator("#f4pItemsBody tbody tr").count() == 1
    assert "Backlog" in page.inner_text("#f4pItemsBody")

def test_clique_na_projetada_abre_lista_com_todos_os_itens(page):
    carregar(page, "f4p.xlsx")
    sem = page.evaluate("semestre(TODAY)")
    _setup_epico(page, team="AN_CLK_PROJ", sem=sem, itens=[
        {"stName": "Backlog"}, {"stName": "WIP"}, {"stName": "Vazao", "deploy": "2026-02-10"},
    ])
    page.click("#anTab")
    page.click('button[data-an-items="proj"]')
    assert page.is_visible("#f4pItemsBg")
    assert page.locator("#f4pItemsBody tbody tr").count() == 3
    assert "Vazão" in page.inner_text("#f4pItemsBody")   # situação segue catOf, igual ao Report F4P
    assert "10/02/2026" in page.inner_text("#f4pItemsBody")   # Vazão mostra a data de saída

def test_clique_no_item_do_modal_fecha_a_visao_analitica_e_navega(page):
    carregar(page, "f4p.xlsx")
    sem = page.evaluate("semestre(TODAY)")
    _setup_epico(page, team="AN_CLK_GO", sem=sem, itens=[{"stName": "Backlog"}])
    alvo_id = page.evaluate("() => [...S.model.ops.values()].find(o => o.team === 'AN_CLK_GO').id")
    page.click("#anTab")
    page.click('button[data-an-items="proj"]')
    assert page.is_visible("#f4pItemsBg")
    page.click(f'button[data-f4p-go="{alvo_id}"]')
    assert not page.is_visible("#f4pItemsBg")
    assert not page.is_visible("#anPanel.open")
    assert page.evaluate("document.getElementById('goto').value") == alvo_id
