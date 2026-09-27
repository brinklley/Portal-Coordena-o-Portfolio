"""Tela de configurações: validações, exportação sem token e limpeza (docs/configuracoes.md)."""
from conftest import carregar

def test_valida_limites_crescentes(page):
    carregar(page, "times.xlsx")
    page.click("#btnCfg"); page.wait_for_timeout(200)
    page.fill('input[data-team="core"][data-f="max"]', "10"); page.fill('input[data-team="core"][data-f="warn"]', "12")
    page.click("#cfgSave"); page.wait_for_timeout(200)
    assert "atenção precisa ser menor" in page.inner_text(".cfg-err")
    assert page.is_visible("#cfgBg")                    # não salvou

def test_ct_precisa_de_duas_colunas(page):
    carregar(page, "times.xlsx")
    page.click("#btnCfg"); page.click('.ftab[data-ftab="IB"]')
    page.evaluate("document.querySelectorAll('.fpanel[data-team-name=\"IB\"] input[data-ctcol]').forEach(i=>i.checked=false)")
    page.click("#cfgSave"); page.wait_for_timeout(200)
    assert "IB" in page.inner_text(".cfg-err")

def test_exportacao_nunca_leva_token(page):
    # sem carga ainda: a tela de Configurações já está forçada aberta (1º acesso)
    page.evaluate("()=>{ azCfgOf(DRAFT).orgs.push({org:'minha-org'}); AZ.tokens['minha-org']='SEGREDO-123'; }")
    with page.expect_download() as d:
        page.click("#cfgExport")
    txt = open(d.value.path(), encoding="utf-8").read()
    assert "minha-org" in txt and "SEGREDO-123" not in txt

def test_limpar_tudo_volta_ao_primeiro_acesso(page):
    # sem carga ainda: a tela de Configurações já está forçada aberta (1º acesso)
    page.evaluate("()=>{ CFG.teams={core:{max:60}}; saveCfg(); }")
    page.click("#cfgWipe"); page.wait_for_timeout(200)
    with page.expect_navigation():
        page.click("#wipeGo")
    page.wait_for_timeout(600)
    assert page.evaluate("localStorage.getItem(CFG_KEY)") is None
    assert page.evaluate("JSON.stringify(CFG.teams)") == "{}"
    # volta mesmo ao estado de 1º acesso: gate ativo, tela de conexão forçada
    assert page.evaluate("document.body.classList.contains('gate-active')")
    assert not page.evaluate("document.getElementById('cfgBg').hidden")
