"""Carga por planilha: dados de exemplo, formato tabela e formato CSV nas abas (docs/importacao-planilha.md)."""
from conftest import carregar

def test_dados_de_exemplo_nao_viram_configuracao(page):
    assert page.evaluate("S.isDemo") is True
    assert page.is_visible("#notice")
    # os times de exemplo servem ao quadro, mas não entram na configuração por time
    assert page.evaluate("cfgTeams(CFG).length") == 0
    assert page.evaluate("cfgTeams(CFG, true).length") == 4

def test_planilha_tabela_monta_a_hierarquia(page):
    carregar(page, "times.xlsx")
    r = page.evaluate("({ini:S.model.inis.size, rel:S.model.rels.size, epi:S.model.epis.size, times:S.model.teams})")
    assert (r["ini"], r["rel"], r["epi"]) == (1, 3, 12)
    assert r["times"] == ["CORE", "IB", "BO", "MOBILE", "PAGAMENTOS", "DADOS", "CANAIS"]   # abas "TIME X" viram o time X

def test_csv_nas_abas_detecta_repara_e_descarta(page):
    carregar(page, "csv_nas_abas.xlsx")
    n = page.evaluate("S.importNotes")
    assert sorted(c["sheet"] for c in n["csvSheets"]) == ["CORE", "EPICO", "INICIATIVA", "RELEASE"]
    # aba sem o prefixo TIME é reconhecida como time pela coluna ID_EPICO_UNICRED
    assert page.evaluate("S.model.teams") == ["CORE"]
    # acentos corrigidos (UTF-8 lido como Windows-1252)
    assert page.evaluate("[...S.model.ops.values()].find(o=>o.id==='500').title") == "Item Próximo"
    # título com quebra de linha entre aspas: registro reconstruído; aspa perdida: registro reparado
    assert page.evaluate("S.model.rels.get('11').title").startswith("Título com quebra")
    assert [x["id"] for x in n["fixed"]] == ["12"]
    assert page.evaluate("S.model.rels.get('12').title") == "Aspa que a conversão não fechou"
    # registro truncado: descartado e listado na Higiene de dados
    assert [x["id"] for x in n["dropped"]] == ["502"]
