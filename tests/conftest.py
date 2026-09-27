"""Infraestrutura dos testes: abre dist/mapa_portfolio.html num Chromium sem interface.
Pré-requisitos: npm run build · python3 tests/gerar_fixtures.py · python3 -m playwright install chromium
"""
import re
import pytest
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist" / "mapa_portfolio.html"
FIX = ROOT / "fixtures"

@pytest.fixture(scope="session")
def browser():
    assert DIST.exists(), "Rode `npm run build` antes dos testes."
    with sync_playwright() as p:
        b = p.chromium.launch()
        yield b
        b.close()

@pytest.fixture
def page(browser):
    ctx = browser.new_context(viewport={"width": 1500, "height": 950}, accept_downloads=True)
    pg = ctx.new_page()
    pg.errors = []
    pg.on("pageerror", lambda e: pg.errors.append(str(e)))
    pg.goto(DIST.as_uri())
    pg.wait_for_timeout(400)
    yield pg
    assert not pg.errors, f"Erros de JavaScript na página: {pg.errors}"
    ctx.close()

def carregar(pg, nome, **azure_kwargs):
    """Carrega uma fixture de fixtures/ como se fosse uma carga do Azure DevOps: simula o backend
    (tests/azure_simulado.py), registra as fontes das 4 funções e chama o pipeline real de carga
    (azRun), sem depender de clique de UI. `**azure_kwargs` repassa para AzureSimulado (ex.:
    item_removido=True) — por padrão nenhum caso extremo é ativado, senão o diálogo de mapeamento
    de colunas (#azMapOk) travaria a espera abaixo."""
    from azure_simulado import AzureSimulado, fontes_de
    sim = AzureSimulado(nome, **azure_kwargs)
    pg.route(re.compile(r"https://(analytics\.)?dev\.azure\.com/.*"), sim.rota)
    fontes = fontes_de(sim)
    orgs = sorted({f["org"] for f in fontes})
    pg.evaluate("""([orgs, fontes]) => {
      CFG.azure.orgs = orgs.map(o => ({org:o})); CFG.azure.sources = fontes; saveCfg();
      orgs.forEach(o => AZ.tokens[o] = 'test-token');
    }""", [orgs, fontes])
    pg.evaluate("azRun()")
    pg.wait_for_function('document.getElementById("srcLabel").textContent.includes("Azure DevOps")', timeout=60000)
    pg.wait_for_timeout(300)
