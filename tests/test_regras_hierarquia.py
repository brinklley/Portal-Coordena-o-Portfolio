"""Regras de exibição da hierarquia (docs/regras-de-negocio.md, seções 2 e 3)."""
from conftest import carregar

VIS = "({ini:[...S.V.visIni].sort(), rel:[...S.V.visRel].sort()})"

def test_regra_b_itens_sem_desdobramento(page):
    carregar(page, "desdobramento.xlsx")
    v = page.evaluate(VIS)
    assert v["ini"] == ["1", "2", "3"]                    # 4: concluída sem release → fora
    assert v["rel"] == ["10", "20", "21", "22"]           # 23: entregue sem épico → fora; 99: sem iniciativa → fora
    page.uncheck("#fBare"); page.wait_for_timeout(300)    # opção desligada: só a cadeia completa
    v = page.evaluate(VIS)
    assert v["ini"] == ["1", "2"] and v["rel"] == ["10", "20", "21"]

def test_selos_de_situacao(page):
    carregar(page, "desdobramento.xlsx")
    ph = page.evaluate("""({i1:iniPhase(S.model.inis.get('1'),S.V), i2:iniPhase(S.model.inis.get('2'),S.V), i3:iniPhase(S.model.inis.get('3'),S.V),
                          r20:relPhase(S.model.rels.get('20'),S.V), r21:relPhase(S.model.rels.get('21'),S.V), r22:relPhase(S.model.rels.get('22'),S.V)})""")
    assert ph == {"i1": "fechado", "i2": "aberto", "i3": "semrel", "r20": "fechado", "r21": "aberto", "r22": "semepi"}
    assert page.evaluate("S.model.warn.relNoEpi.map(r=>r.id)") == ["99"]

def test_filtros_de_time_mostram_so_cadeia_completa(page):
    carregar(page, "desdobramento.xlsx")
    page.select_option("#fTeam", "CORE"); page.wait_for_timeout(300)
    assert page.evaluate(VIS)["ini"] == ["1", "2"]

def test_fase_do_epico_pelos_itens(page):
    carregar(page, "desdobramento.xlsx")
    assert page.evaluate("epiMetrics(S.model.epis.get('200'),'').phase") == "fechado"
    assert page.evaluate("epiMetrics(S.model.epis.get('210'),'').phase") == "wip"

def test_investigacao_explica_a_regra(page):
    carregar(page, "desdobramento.xlsx")
    passos = page.evaluate("investigate('4').map(s=>[s.ok, s.title])")
    assert passos[-1] == [False, "Iniciativa concluída sem release"]
    passos = page.evaluate("investigate('3').map(s=>[s.ok, s.title])")
    assert [True, "Iniciativa sem release"] in passos and passos[-1][0] is True
    passos = page.evaluate("investigate('999999').map(s=>s.title)")
    assert passos == ["Não retornou nos dados"]
