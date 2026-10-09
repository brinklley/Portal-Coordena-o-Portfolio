"""Filtros, busca por ID e diagnósticos (docs/telas.md)."""
from conftest import carregar

def test_responsaveis_busca_em_qualquer_parte_do_nome(page):
    carregar(page, "responsaveis.xlsx")
    page.click("#fOwner"); page.fill("#msSearch", "conceicao")        # sem acento, no meio do nome
    visiveis = page.evaluate("[...document.querySelectorAll('#msList .ms-item .nm')].map(x=>x.textContent)")
    assert visiveis and all("Conceição" in n for n in visiveis)
    page.click("#msAll"); page.mouse.click(700, 700); page.wait_for_timeout(300)
    assert page.evaluate("S.f.owners.size") == len(visiveis)

def test_ir_para_id_aponta_o_filtro_que_esconde(page):
    """Digitar um ID no filtro único que fica bloqueado por outro filtro ativo esvazia o quadro
    inteiro (decisão 0034: o próprio ID já restringe tudo ao redor dele) — quem explica é o
    diagnóstico automático de "nenhum resultado" (diagHtml), não um aviso à parte do campo."""
    carregar(page, "responsaveis.xlsx")
    page.click("#fOwner"); page.fill("#msSearch", "guzzo"); page.click("#msAll"); page.mouse.click(700, 700); page.wait_for_timeout(300)
    alvo = page.evaluate("[...S.model.inis.values()].find(i=>i.owner && !/guzzo/i.test(i.owner)).id")
    page.fill("#fBusca", alvo); page.press("#fBusca", "Enter"); page.wait_for_timeout(500)
    msg = page.inner_text("#fmsg")
    assert "Responsável da iniciativa" in msg
    page.click("[data-diag^='show:']"); page.wait_for_timeout(500)
    assert page.evaluate("S.path.ini") == alvo
    # o filtro único (decisão 0034) fica ativo depois de ir até o ID, diferente dos outros que foram limpos
    assert page.evaluate("activeFilters().length") == 1 and page.evaluate("S.f.q") == alvo

def test_ir_para_epico_orfao_nao_aplica_filtro_nem_zera_o_quadro(page):
    """Bug relatado pelo cliente: clicar no link do ID de um épico órfão (sem release/iniciativa
    vinculada, decisão 0036) dentro da Visão Analítica aplicava o ID como filtro "ID ou descrição" —
    um filtro que esse ID nunca vai satisfazer no quadro, já que o épico órfão não aparece lá — e
    deixava a tela presa em "Nada corresponde aos filtros", com o conteúdo real que o usuário estava
    vendo sumindo e dois avisos quase idênticos sobrepostos (o diagnóstico automático do render() e o
    da própria navegação). gotoId() agora resolve found/path ANTES de tocar no filtro: um ID fora da
    cadeia válida só mostra um aviso informativo, sem mexer em S.f nem no que já estava na tela."""
    carregar(page, "f4p.xlsx")
    sem = page.evaluate("semestre(TODAY)")
    page.evaluate("""(args)=>{
      const {team, sem} = args;
      S.model.ops.set("op_orfao_bug", {id:"op_orfao_bug", title:"Item do épico órfão", team, type:"User Story",
        stName: S.model.teamFlow[team][0], deploy:null, ready:new Date(2026,0,1), tags:[]});
      S.model.epis.set("971770", {id:"971770", valid:false, title:"["+team+"] Épico órfão de teste", parent:null,
        target:new Date(2026,0,15), interno:sem, st:0, ops:["op_orfao_bug"], type:"Epic"});
      S.f.team = team; S.f.int = sem; S.f.exec = ""; S.f.q = ""; S.f.owners = new Set();
      render();
    }""", {"team": "CORE", "sem": sem})
    filtros_antes = page.evaluate("JSON.stringify(S.f)")
    page.click("#anTab")
    page.click("[data-an-go='971770']")
    page.wait_for_timeout(500)
    # o filtro "ID ou descrição" nunca foi aplicado — os filtros continuam exatamente como antes
    assert page.evaluate("JSON.stringify(S.f)") == filtros_antes
    assert page.evaluate("S.f.q") == ""
    msg = page.inner_text("#fmsg")
    assert "fora da cadeia válida" in msg
    assert "Investigar por que não aparece" in msg

def test_diagnostico_quando_o_filtro_zera_o_quadro(page):
    carregar(page, "responsaveis.xlsx")
    page.fill("#fBusca", "texto que nao existe"); page.wait_for_timeout(700)
    assert "Nenhum item" in page.inner_text(".empty-state")

def test_filtro_unico_por_id_de_epico_mostra_so_a_cadeia(page):
    """O filtro único "ID ou descrição" (decisão 0034) substitui os antigos campos separados de
    Iniciativa e "Ir para qualquer ID": um ID de épico já filtra o quadro para a cadeia dele
    (escondendo as demais iniciativas) e fica salvo como filtro ativo, revisável e limpável."""
    carregar(page, "times.xlsx")
    epi_id = page.evaluate("[...S.model.epis.values()].find(e => e.valid).id")
    ini_esperada = page.evaluate(f"S.model.rels.get(S.model.epis.get('{epi_id}').parent).parent")
    page.fill("#fBusca", epi_id); page.wait_for_timeout(500)
    visiveis = page.evaluate("[...S.model.inis.keys()].filter(id => S.V.visIni.has(id))")
    assert visiveis == [ini_esperada]
    assert page.evaluate("activeFilters().length") == 1
    assert page.evaluate("document.getElementById('fBusca').classList.contains('active')")

def test_filtro_unico_por_texto_busca_em_qualquer_nivel(page):
    """Texto que só bate com o título de um item de time (não com nome de iniciativa) também
    filtra e revela a cadeia dele — antes, o campo Iniciativa só buscava por nome de iniciativa,
    e um texto assim não encontrava nada nesse campo."""
    carregar(page, "times.xlsx")
    op = page.evaluate("""() => { const o = [...S.model.ops.values()].find(o => { const e = S.model.epis.get(o.epicoId); return e && e.valid; });
      return {key:o.key, title:o.title}; }""")
    page.fill("#fBusca", op["title"]); page.wait_for_timeout(500)
    assert page.evaluate(f"S.V.visOp.has({op['key']!r})")

def test_limpar_a_busca_desfaz_a_selecao_que_ela_criou(page):
    """Bug relatado: limpar o campo (inclusive pelo "×" nativo do input — que dispara o mesmo
    evento "input" que page.fill("", ...) simula) tirava o filtro mas deixava o quadro preso
    mostrando só a iniciativa que a busca tinha selecionado via Enter (decisão 0035): a seleção
    feita pela própria busca (gotoId) precisa se desfazer junto quando a busca é limpa."""
    carregar(page, "times.xlsx")
    epi_id = page.evaluate("[...S.model.epis.values()].find(e => e.valid).id")
    page.fill("#fBusca", epi_id); page.press("#fBusca", "Enter"); page.wait_for_timeout(500)
    assert page.evaluate("S.path.epi") == epi_id and page.evaluate("S.f.q") == epi_id
    page.fill("#fBusca", ""); page.wait_for_timeout(500)
    assert page.evaluate("S.f.q") == ""
    assert page.evaluate("JSON.stringify(S.path)") == "{}"
    assert page.evaluate("activeFilters().length") == 0

def test_trocar_a_busca_por_outro_id_tambem_desfaz_a_selecao_anterior(page):
    """Mesma correção (decisão 0035): trocar a busca para outro ID, mesmo só digitando (sem
    Enter), também desfaz a seleção que a busca anterior tinha criado."""
    carregar(page, "times.xlsx")
    a, b = page.evaluate("[...S.model.epis.values()].filter(e => e.valid).map(e => e.id)")[:2]
    page.fill("#fBusca", a); page.press("#fBusca", "Enter"); page.wait_for_timeout(500)
    assert page.evaluate("S.path.epi") == a
    page.fill("#fBusca", b); page.wait_for_timeout(500)
    assert page.evaluate("JSON.stringify(S.path)") == "{}"
    assert page.evaluate("S.f.q") == b

def test_recarregar_dados_com_time_selecionado_nao_trava_os_paineis(page):
    """Decisão 0057: o usuário relatou que, depois de atualizar os dados do Azure DevOps com o filtro
    de Time já selecionado, o <select> continuava mostrando o time, mas escolher um Roadmap em seguida
    não habilitava Visão analítica/Report F4P/Actionable — "1 filtro ativo" aparecia (só o Roadmap),
    como se o Time tivesse sumido do estado sem sumir da tela. Causa: `fillTeamFilter()` preservava o
    valor do <select>, mas rodava ANTES do reset de `S.f` em `fillFilters()`, que zerava `S.f.team` por
    baixo — o <select> e o estado ficavam dessincronizados."""
    carregar(page, "f4p.xlsx")
    page.select_option("#fTeam", "CORE")
    assert page.evaluate("S.f.team") == "CORE"
    carregar(page, "f4p.xlsx")   # simula "atualizar os dados" do Azure DevOps (recarga do mesmo time)
    assert page.eval_on_selector("#fTeam", "el => el.value") == "CORE"
    assert page.evaluate("S.f.team") == "CORE"
    page.evaluate("()=>{ S.f.int = semestre(TODAY); render(); }")
    assert page.evaluate("activeFilters().length") == 2
    assert not page.is_disabled("#anTab")
    assert not page.is_disabled("#f4pTab")
    assert not page.is_disabled("#actTab")
