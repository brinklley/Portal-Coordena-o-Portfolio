"""Integração com o Azure DevOps (docs/integracao-azure.md), contra o Azure simulado.
Como o Azure DevOps é a única fonte de dados do portal, `carregar()` (tests/conftest.py) já
carrega tudo por aqui — este arquivo cobre o que `carregar()` não exercita: o primeiro acesso
(tela de conexão forçada), tokens não sobrevivendo à reabertura, e o diálogo de mapeamento de
colunas renomeadas (caso extremo opcional do simulado, não usado pela carga genérica)."""
import re
from conftest import carregar
from azure_simulado import AzureSimulado, fontes_de

RESUMO = """(()=>{const M=S.model; return {ini:[...M.inis.keys()].sort((a,b)=>a-b), rel:[...M.rels.keys()].sort((a,b)=>a-b), epi:[...M.epis.keys()].sort((a,b)=>a-b),
  times:Object.fromEntries(M.teams.map(t=>[t,[...M.ops.values()].filter(o=>o.team===t).length]))}})()"""

def azure(page):
    sim = AzureSimulado()
    page.route(re.compile(r"https://(analytics\.)?dev\.azure\.com/.*"), sim.rota)
    return sim

def test_conexao_so_e_salva_se_o_teste_passa(page):
    """Sem nenhuma carga prévia (nem cache no IndexedDB), o primeiro acesso já abre a tela de
    Configurações forçada, na aba Azure DevOps, com a aba Geral desabilitada."""
    azure(page)
    assert not page.evaluate("document.getElementById('cfgBg').hidden")
    assert not page.is_visible(".top") and not page.is_visible(".viewport")
    assert page.evaluate("document.querySelector('[data-cfgtab2=\"geral\"]').disabled")
    assert page.evaluate("!!document.querySelector('.az-lock')") and not page.evaluate("!!document.querySelector('.az-role')")
    page.fill("#azNewOrg", "org-times"); page.fill("#azNewTok", "token-errado"); page.click("#azAddOrg"); page.wait_for_timeout(300)
    assert page.evaluate("azCfgOf(DRAFT).orgs.length") == 0
    page.fill("#azNewOrg", "org-times"); page.fill("#azNewTok", "token-bom"); page.click("#azAddOrg"); page.wait_for_timeout(300)
    assert page.evaluate("azCfgOf(DRAFT).orgs.length") == 1 and page.evaluate("!!document.querySelector('.az-role')")

def test_carga_do_azure_monta_hierarquia_correta(page):
    """Substitui o antigo teste de comparação com a carga por planilha (removida): a carga do
    Azure é a única fonte, então valida diretamente a hierarquia e os pontos que a integração
    trata de forma especial (item Removido excluído, DADOS ligado pelo Parent com fluxo real
    terminando em "Pronto", não em "Fechado"). Iniciativa/Release/Épico de times.xlsx são fixos
    (não aleatórios) — ver tests/gerar_fixtures.py::times."""
    carregar(page, "times.xlsx", item_removido=True)
    r = page.evaluate(RESUMO)
    assert r["ini"] == ["1"]
    assert r["rel"] == ["10", "11", "12"]
    assert r["epi"] == ["100", "101", "102", "103", "110", "111", "112", "113", "120", "121", "122", "123"]
    assert set(r["times"]) == {"CORE", "IB", "BO", "MOBILE", "PAGAMENTOS", "DADOS", "CANAIS"}
    assert all(n > 0 for n in r["times"].values())
    notas = page.evaluate("S.importNotes.azure")
    assert "op:99999" in notas["removedIds"]                          # estado Removed excluído
    assert notas["byParent"] > 0                                      # DADOS ligado aos épicos pelo Parent
    assert page.evaluate("S.model.teamFlow.DADOS.at(-1)") == "Pronto"  # fluxo real do quadro, não nomes fixos

def test_mapeamento_de_colunas_renomeadas(page):
    """Caso extremo do simulado (`coluna_antiga=True`): uma coluna fora do quadro atual no
    histórico pede o diálogo de mapeamento antes de aplicar a carga. Não usa `carregar()` (que
    trava esperando esse diálogo ser confirmado) — dirige o fluxo de UI direto."""
    sim = AzureSimulado("times.xlsx", coluna_antiga=True)
    page.route(re.compile(r"https://(analytics\.)?dev\.azure\.com/.*"), sim.rota)
    fontes = fontes_de(sim); orgs = sorted({f["org"] for f in fontes})
    page.evaluate("""([orgs, fontes])=>{
      CFG.azure.orgs = orgs.map(o=>({org:o})); CFG.azure.sources = fontes; saveCfg();
      orgs.forEach(o => AZ.tokens[o] = 'token-bom');
    }""", [orgs, fontes])
    page.evaluate("openAzureLoadModal()"); page.wait_for_timeout(200); page.click("#azGo")
    page.wait_for_selector("#azMapOk", timeout=60000)
    assert "Coluna Antiga" in page.inner_text("#azBody")
    page.click("#azMapOk")
    page.wait_for_function('document.getElementById("srcLabel").textContent.includes("Azure DevOps")', timeout=60000)
    assert page.evaluate("!!S.model")

def test_tokens_nao_sobrevivem_a_reabertura(page):
    sim = azure(page)
    fonte_core = next(f for f in fontes_de(sim) if f["team"] == "CORE" and f["role"] == "op")
    page.evaluate("(f)=>{ CFG.azure.orgs=[{org:'org-times'}]; CFG.azure.sources=[f]; saveCfg(); AZ.tokens['org-times']='b'; }", fonte_core)
    page.reload(); page.wait_for_timeout(500)
    assert page.evaluate("Object.keys(AZ.tokens).length") == 0
    page.evaluate("openAzureLoadModal()"); page.wait_for_timeout(200)
    assert page.evaluate("[...document.querySelectorAll('[data-azl-tok]')].map(i=>i.dataset.azlTok)") == ["org-times"]
