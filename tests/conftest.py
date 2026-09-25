"""Infraestrutura dos testes: abre dist/mapa_portfolio.html num Chromium sem interface.
Pré-requisitos: npm run build · python3 tests/gerar_fixtures.py · python3 -m playwright install chromium
"""
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

def carregar(pg, nome):
    """Carrega uma planilha de fixtures/ pelo botão 'Carregar planilha'."""
    pg.set_input_files("#file", str(FIX / nome))
    pg.wait_for_function(f'document.getElementById("srcLabel").textContent.includes("{nome}")', timeout=60000)
    pg.wait_for_timeout(300)
