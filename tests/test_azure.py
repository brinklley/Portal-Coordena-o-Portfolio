"""Integração com o Azure DevOps (docs/integracao-azure.md), contra o Azure simulado."""
import re
from conftest import carregar
from azure_simulado import AzureSimulado, FONTES

RESUMO = """(()=>{const M=S.model; return {ini:[...M.inis.keys()].sort(), rel:[...M.rels.keys()].sort(), epi:[...M.epis.keys()].sort(),
  times:Object.fromEntries(M.teams.map(t=>[t,[...M.ops.values()].filter(o=>o.team===t).length])),
  epicos:Object.fromEntries([...M.epis.values()].map(e=>{const m=epiMetrics(e,''); return [e.id,[m.n,m.ct,m.disc,m.wip,m.vaz]]}))}})()"""

def azure(page):
    sim = AzureSimulado()
    page.route(re.compile(r"https://(analytics\.)?dev\.azure\.com/.*"), sim.rota)
    return sim

def test_conexao_so_e_salva_se_o_teste_passa(page):
    azure(page)
    page.click("#btnCfg"); page.wait_for_timeout(200)
    assert page.evaluate("!!document.querySelector('.az-lock')") and not page.evaluate("!!document.querySelector('.az-role')")
    page.fill("#azNewOrg", "org-times"); page.fill("#azNewTok", "token-errado"); page.click("#azAddOrg"); page.wait_for_timeout(300)
    assert page.evaluate("azCfgOf(DRAFT).orgs.length") == 0
    page.fill("#azNewOrg", "org-times"); page.fill("#azNewTok", "token-bom"); page.click("#azAddOrg"); page.wait_for_timeout(300)
    assert page.evaluate("azCfgOf(DRAFT).orgs.length") == 1 and page.evaluate("!!document.querySelector('.az-role')")

def test_carga_do_azure_igual_a_planilha(page):
    carregar(page, "times.xlsx")
    planilha = page.evaluate(RESUMO)
    azure(page)
    page.evaluate("(f)=>{ CFG.azure.orgs=[{org:'org-portfolio'},{org:'org-times'}]; CFG.azure.sources=f; saveCfg(); AZ.tokens['org-portfolio']='a'; AZ.tokens['org-times']='b'; }", FONTES)
    page.click("#btnAz"); page.wait_for_timeout(200); page.click("#azGo")
    page.wait_for_selector("#azMapOk", timeout=60000)                 # coluna antiga no histórico → pede mapeamento
    assert "Coluna Antiga" in page.inner_text("#azBody")
    page.click("#azMapOk")
    page.wait_for_function('document.getElementById("srcLabel").textContent.includes("Azure DevOps")', timeout=60000)
    az = page.evaluate(RESUMO)
    assert az["ini"] == planilha["ini"] and az["rel"] == planilha["rel"] and az["epi"] == planilha["epi"]
    assert sorted(az["times"].items()) == sorted(planilha["times"].items())   # mesmos times, mesma quantidade de itens
    assert az["epicos"] == planilha["epicos"]                         # mesmas datas de coluna → mesmo CT e mesmas contagens
    notas = page.evaluate("S.importNotes.azure")
    assert "op:99999" in notas["removedIds"]                          # estado Removed excluído
    assert notas["byParent"] > 0                                      # DADOS ligado aos épicos pelo Parent
    assert page.evaluate("S.model.teamFlow.DADOS.at(-1)") == "Pronto"  # fluxo real do quadro, não nomes fixos

def test_tokens_nao_sobrevivem_a_reabertura(page):
    azure(page)
    page.evaluate("(f)=>{ CFG.azure.orgs=[{org:'org-times'}]; CFG.azure.sources=f.slice(4,5); saveCfg(); AZ.tokens['org-times']='b'; }", FONTES)
    page.reload(); page.wait_for_timeout(500)
    assert page.evaluate("Object.keys(AZ.tokens).length") == 0
    page.click("#btnAz"); page.wait_for_timeout(200)
    assert page.evaluate("[...document.querySelectorAll('[data-azl-tok]')].map(i=>i.dataset.azlTok)") == ["org-times"]
