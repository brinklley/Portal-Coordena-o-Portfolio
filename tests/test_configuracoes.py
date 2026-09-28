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

def test_dias_antes_do_semestre_padrao_e_10(page):
    """Decisão 0037: o padrão de "Dias antes do fim do semestre" passou de 0 para 10 dias, para
    já deixar uma folga sensata no cálculo do dead line em vez de nenhuma."""
    carregar(page, "times.xlsx")
    assert page.evaluate("CFG.anFreeze") == 10
    page.click("#btnCfg")
    assert page.evaluate("document.getElementById('cfgAnFreeze').value") == "10"

def test_ajuda_do_dias_antes_do_semestre_explica_o_calculo_do_deadline(page):
    """Decisão 0037: o texto de ajuda da Visão analítica deixa explícito que "Dias antes do fim do
    semestre" entra direto no cálculo do dead line, com a fórmula completa (inclui o CT máximo do
    time) e um exemplo numérico — não só a data de congelamento, sem explicar o impacto."""
    carregar(page, "times.xlsx")
    page.click("#btnCfg")
    txt = page.inner_text("#cfgTabGeral")
    assert "CT máximo do time" in txt
    assert "dead line" in txt.lower()

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
