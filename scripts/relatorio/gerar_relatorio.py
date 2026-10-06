#!/usr/bin/env python3
"""Gera o relatório do portfólio em um único HTML offline: Visão Analítica e Actionable por time comprometido + Report F4P.

As regras de negócio NÃO são reimplementadas aqui: o script abre `dist/mapa_portfolio.html` num Chromium
sem interface, carrega os dados pelo mesmo caminho da tela (`azRun`), aplica os mesmos filtros (Time +
Roadmap) e captura o que as MESMAS funções do portal calculam e desenham (`anData`/`renderAnalytics`).
Depois só embute esse resultado numa casca com menu lateral, com o estilo do próprio portal e sem
bibliotecas externas.

Fontes de dados (`--fonte`):
  azure     Azure DevOps de verdade. O PAT vem da credencial de API do ambiente (injetada pelo proxy)
            ou de `AZURE_DEVOPS_PAT_<ORG>`; nunca entra no navegador.
  simulado  Azure simulado dos testes (tests/azure_simulado.py), alimentado por uma fixture fictícia de
            fixtures/. Serve para validar o pipeline sem dados reais nem token.

Uso:
  python3 scripts/relatorio/gerar_relatorio.py --config configuracao_mapa_portfolio.json --fonte azure --time MOBILE
  python3 scripts/relatorio/gerar_relatorio.py --config configuracao_mapa_portfolio.json --fonte simulado --fixture times.xlsx
"""
import argparse, asyncio, html, json, re, sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from playwright.async_api import async_playwright

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
DIST = RAIZ / "dist" / "mapa_portfolio.html"
FUSO = ZoneInfo("America/Sao_Paulo")

JS_CARREGAR = """async (limiteMs) => {
  azRun();
  const t0 = Date.now();
  while (Date.now() - t0 < limiteMs) {
    if (document.getElementById('srcLabel').textContent.includes('Azure DevOps')) return {ok:true};
    const ok = document.getElementById('azMapOk');           // colunas novas/antigas no histórico: segue o padrão (ignorar)
    if (ok && !ok.closest('[hidden]')) ok.click();
    const falha = document.querySelector('#azp .azp-bad');
    if (falha && document.getElementById('azCancel')) return {ok:false, erro: document.getElementById('azp').innerText.slice(0, 1500)};
    await new Promise(r => setTimeout(r, 400));
  }
  return {ok:false, erro:'tempo esgotado esperando a carga do Azure DevOps'};
}"""

# Só na execução headless (o portal em si não muda): mais chamadas simultâneas nas listas de lotes (o portal fixa 4; o
# histórico do Analytics é o trecho mais lento) e nova tentativa por fonte, mostrando o motivo da falha no log.
JS_AJUSTES = """(n) => {
  const pool = azPool; azPool = (tarefas, _n, aoTerminar) => pool(tarefas, n, aoTerminar);
  const carregar = azLoadSource;
  azLoadSource = async (src, st) => {
    let ultimo;
    for (let t = 1; t <= 5; t++) {
      try { return await carregar(src, st); }
      catch (e) { ultimo = e; console.log(`[carga] ${src.org}/${src.alias || src.team}: tentativa ${t} de 5 falhou: ${e.message}`); await new Promise(r => setTimeout(r, 4000 * t)); }
    }
    throw ultimo;
  };
}"""

JS_TIMES = """(rm) => {
  const out = [];
  for (const tm of cfgTeams(CFG).filter(hasData)) {
    S.f.team = tm; S.f.int = rm.interno; S.f.exec = rm.executivo; S.f.q = ''; S.f.owners = new Set();
    const d = anData();
    out.push({time: tm, capacidade: d.cap, projetada: d.proj, epicos: d.rows.length});
  }
  S.f.team = ''; S.f.int = ''; S.f.exec = '';
  return out;
}"""

# Captura o painel REAL do portal (mesmas funções, mesmo HTML) e tira dele tudo o que só faz sentido com clique:
# botões viram texto, dicas "clique…" somem, frases de rodapé que mandam clicar são cortadas.
JS_PAINEL = r"""(a) => {
  const P = {
    va:  {abrir: () => openAnalytics(),   fechar: () => closeAnalytics(),   aberto: () => AN.open,  titulo: 'anTitle',  corpo: 'anBody'},
    act: {abrir: () => openActionable(),  fechar: () => closeActionable(),  aberto: () => ACT.open, titulo: 'actTitle', corpo: 'actBody'},
    f4p: {abrir: () => openF4P(),         fechar: () => closeF4P(),         aberto: () => F4P.open, titulo: 'f4pTitle', corpo: 'f4pBody'}}[a.painel];
  S.f.team = a.time; S.f.int = a.interno; S.f.exec = a.executivo; S.f.q = ''; S.f.owners = new Set();
  P.abrir();
  if (!P.aberto()) return {erro: `o painel ${a.painel} não habilitou para ${a.time} (time/roadmap sem dados ou semestre futuro?)`};
  const extra = a.painel === 'va' ? (d => ({capacidade: d.cap, projetada: d.proj, epicos: d.rows.length}))(anData()) : {};
  const titulo = $(P.titulo).cloneNode(true), corpo = $(P.corpo).cloneNode(true);
  const CLIQUE = /cliqu|clicáv|clic\b/i;
  [titulo, corpo].forEach(raiz => {
    raiz.querySelectorAll('button').forEach(b => {
      const s = document.createElement('span'); s.className = b.className; s.innerHTML = b.innerHTML;   // style inline (larguras das barras) e spans internos precisam sobreviver
      if (b.getAttribute('style')) s.setAttribute('style', b.getAttribute('style')); b.replaceWith(s); });
    raiz.querySelectorAll('[title]').forEach(x => { if (CLIQUE.test(x.title) || /^Ver (os )?itens/i.test(x.title)) x.removeAttribute('title'); });
    raiz.querySelectorAll('[data-sort]').forEach(x => x.removeAttribute('data-sort'));
    const w = document.createTreeWalker(raiz, NodeFilter.SHOW_TEXT);
    for (let n = w.nextNode(); n; n = w.nextNode()) {
      n.nodeValue = n.nodeValue
        .replace(/\s*·\s*[Cc]lique[^·.]*/g, '')
        .replace(/\s*[Cc]lique[^.]*\./g, '')
        .replace(/\s*Os números do cabeçalho.*?quando entregue\)\./gs, '');
    }
  });
  P.fechar();
  return {titulo: titulo.innerHTML, corpo: corpo.innerHTML, semestre: semLong(a.interno || a.executivo), ...extra};
}"""


def ler_config(caminho):
    cfg = json.loads(Path(caminho).read_text(encoding="utf-8"))
    if "azure" not in cfg:
        raise SystemExit(f"{caminho}: não parece uma exportação de configuração do Portal (sem a chave 'azure').")
    return cfg


class _Captura:
    """Adapta o Azure simulado (feito para a API síncrona) à API assíncrona: captura o `fulfill` e o repassa."""
    def __init__(self, route): self.request, self.resp = route.request, None
    def fulfill(self, **kw): self.resp = kw


async def preparar_fonte(pg, cfg, args):
    """Ajusta `cfg.azure` e a rota de rede conforme a fonte. Devolve (tokens de enchimento, texto de origem, ponte|None)."""
    padrao = re.compile(r"https://(analytics\.)?dev\.azure\.com/.*")
    if args.fonte == "simulado":
        sys.path.insert(0, str(RAIZ / "tests"))
        from azure_simulado import AzureSimulado, fontes_de
        sim = AzureSimulado(args.fixture)
        async def rota_sim(route):
            c = _Captura(route); sim.rota(c); await route.fulfill(**c.resp)
        await pg.route(padrao, rota_sim)
        fontes = fontes_de(sim)
        cfg["azure"].update(orgs=[{"org": o} for o in sorted({f["org"] for f in fontes})], sources=fontes, maps={}, mapMeta={})
        cfg["flow"] = {}   # o fluxo da configuração descreve os quadros REAIS; os quadros fictícios usam o fluxo padrão
        return {o["org"]: "token-simulado" for o in cfg["azure"]["orgs"]}, "Azure simulado (dados fictícios)", None
    from ponte_azure import Ponte, pats_do_ambiente, ENCHIMENTO
    orgs = sorted({s["org"] for s in cfg["azure"]["sources"]})
    pats = pats_do_ambiente(orgs)
    ponte = Ponte(pats)
    await asyncio.to_thread(ponte.verificar, orgs)
    print("Autenticação: " + ", ".join(f"{o} ({'variável de ambiente' if pats[o] else 'credencial do ambiente'})" for o in orgs), flush=True)
    await pg.route(padrao, ponte.rota)
    return {o: ENCHIMENTO for o in orgs}, "Azure DevOps", ponte


async def acompanhar(ponte, pg):
    """Uma linha de progresso a cada 30s (a janela do portal não atualiza de forma confiável sem tela)."""
    while True:
        await asyncio.sleep(30)
        print("  carregando… " + (ponte.resumo() if ponte else ""), flush=True)


ROTULO = {"va": "Visão Analítica", "act": "Actionable", "f4p": "Report F4P"}


def montar_secao(sid, painel, time, dados):
    rotulo = ROTULO[painel] + (f" · {time}" if time else "")
    return (f'<section class="rel-sec" id="{sid}" aria-label="{html.escape(rotulo)}">\n'
            f'<div class="an-head"><div class="an-title">{dados["titulo"]}</div></div>\n'
            f'<div class="an-body">{dados["corpo"]}</div>\n</section>')


async def gerar(args):
    if not DIST.exists():
        raise SystemExit("Falta o dist/mapa_portfolio.html: rode `npm run build` antes.")
    cfg = ler_config(args.config)
    agora = datetime.now(FUSO)
    async with async_playwright() as p:
        navegador = await p.chromium.launch()
        ctx = await navegador.new_context(viewport={"width": 1500, "height": 950}, timezone_id="America/Sao_Paulo", locale="pt-BR")
        pg = await ctx.new_page()
        erros = []
        pg.on("pageerror", lambda e: erros.append(str(e)))
        pg.on("console", lambda m: print(m.text, flush=True) if m.text.startswith("[carga]") else None)
        await pg.goto(DIST.as_uri())
        await pg.wait_for_timeout(400)
        tokens, origem, ponte = await preparar_fonte(pg, cfg, args)
        # Configuração do Portal (sem token). `saveCfg` grava só no localStorage deste navegador descartável.
        await pg.evaluate("([j, tokens]) => { CFG = normCfg(j); saveCfg(); Object.entries(tokens).forEach(([o, t]) => AZ.tokens[o] = t); }", [cfg, tokens])
        await pg.evaluate(JS_AJUSTES, args.simultaneas)
        andamento = asyncio.create_task(acompanhar(ponte, pg))
        try:
            r = await pg.evaluate(JS_CARREGAR, args.limite_min * 60 * 1000)
        finally:
            andamento.cancel()
        if ponte: print("Carga concluída: " + ponte.resumo(), flush=True)
        if not r["ok"]:
            raise SystemExit("A carga do Azure DevOps não terminou:\n" + r["erro"])
        await pg.wait_for_timeout(300)
        # uma fonte que falha não derruba a carga (o portal segue com o resto): para um relatório diário isso
        # seria dado faltando sem aviso, então aqui qualquer fonte ausente aborta a geração.
        faltam = await pg.evaluate("""() => { const ok = new Set(AZ.raw.map(L => L.src.id)); return azCfgOf(CFG).sources.filter(s => !ok.has(s.id)).map(s => `${s.org}/${s.alias || s.team}`); }""")
        if faltam:
            raise SystemExit("Fontes do Azure DevOps que não carregaram (relatório não gerado): " + ", ".join(faltam))

        vigente = await pg.evaluate("semestre(TODAY)")
        roadmap = args.roadmap or vigente
        opcoes = await pg.evaluate("[...document.getElementById(%r).options].map(o => o.value).filter(Boolean)" % ("fInt" if args.tipo_roadmap == "interno" else "fExec"))
        if roadmap not in opcoes:
            raise SystemExit(f"O roadmap {roadmap!r} não existe nos dados carregados. Disponíveis: {', '.join(opcoes) or '(nenhum)'}")
        rm = {"interno": roadmap if args.tipo_roadmap == "interno" else "", "executivo": roadmap if args.tipo_roadmap == "executivo" else ""}

        comprometidos = [t for t in await pg.evaluate(JS_TIMES, rm) if t["capacidade"] > 0]
        print(f"Roadmap {roadmap} ({args.tipo_roadmap}) · times comprometidos: " +
              (", ".join(f'{t["time"]} (cap {t["capacidade"]}/proj {t["projetada"]})' for t in comprometidos) or "nenhum"))
        existentes = {t["time"]: t for t in comprometidos}
        alvos = args.time or [t["time"] for t in comprometidos]
        if not alvos:
            raise SystemExit("Nenhum time comprometido (com itens reservados) neste roadmap.")
        for t in alvos:
            if t not in existentes:
                raise SystemExit(f"O time {t!r} não está comprometido no roadmap {roadmap}. Comprometidos: {', '.join(existentes)}")

        secoes = []   # (id, painel, time, dados)
        for painel in ("va", "act"):
            for t in alvos:
                d = await pg.evaluate(JS_PAINEL, {"painel": painel, "time": t, **rm})
                if "erro" in d:
                    raise SystemExit(d["erro"])
                secoes.append((f"{painel}-" + re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-"), painel, t, d))
        d = await pg.evaluate(JS_PAINEL, {"painel": "f4p", "time": alvos[0], **rm})   # o F4P mostra sempre todos os times carregados
        if "erro" in d:
            raise SystemExit(d["erro"])
        secoes.append(("f4p", "f4p", "", d))
        await ctx.close(); await navegador.close()
    if erros:
        raise SystemExit("Erros de JavaScript no portal durante a geração: " + "; ".join(erros))

    menu = []
    for painel in ("va", "act", "f4p"):
        menu.append(f"  <h2>{ROTULO[painel]}</h2>")
        for sid, pn, t, d in secoes:
            if pn != painel: continue
            sub = f'<small>{d["capacidade"]} US capacidade · {d["epicos"]} épicos</small>' if painel == "va" else ""
            menu.append(f'  <a href="#{sid}">{html.escape(t or "Todos os times")}{sub}</a>')
    css = (RAIZ / "src" / "styles.css").read_text(encoding="utf-8")
    modelo = (AQUI / "modelo.html").read_text(encoding="utf-8")
    semestre = secoes[0][3]["semestre"]
    saida = (modelo.replace("__DATA_CURTA__", agora.strftime("%d/%m/%Y")).replace("__GERADO_EM__", agora.strftime("%d/%m/%Y às %H:%M"))
             .replace("__ROADMAP__", html.escape(semestre)).replace("__MENU__", "\n".join(menu))
             .replace("__SECOES__", "\n".join(montar_secao(*x) for x in secoes)).replace("/*__CSS__*/", css))
    if re.search(r"<script[^>]*\ssrc=|<link[^>]*\shref=|@import|(src|href)=\"https?:", saida):
        raise SystemExit("O relatório referenciou recurso externo, o que quebraria o requisito de arquivo único offline.")
    pasta = Path(args.saida); pasta.mkdir(parents=True, exist_ok=True)
    nome = re.sub(r"[^A-Za-z0-9]+", "-", alvos[0]).strip("-") if len(alvos) == 1 else f"{len(alvos)}-times"
    arq = pasta / f"relatorio_portfolio_{agora.strftime('%Y-%m-%d')}_{nome}.html"
    arq.write_text(saida, encoding="utf-8")
    va = [x[3] for x in secoes if x[1] == "va"]
    print(f"Origem dos dados: {origem}\nGerado: {arq} ({arq.stat().st_size / 1024:.0f} KB) · seções: " + ", ".join(f"{ROTULO[x[1]]}{' ' + x[2] if x[2] else ''}" for x in secoes)
          + " · " + " / ".join(f"{x[2]} Capacidade {x[3]['capacidade']} Projetada {x[3]['projetada']}" for x in secoes if x[1] == "va"))
    return arq


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--config", required=True, help="exportação da configuração do Portal (JSON, sem token)")
    ap.add_argument("--fonte", choices=["azure", "simulado"], default="azure")
    ap.add_argument("--fixture", default="times.xlsx", help="(simulado) fixture de fixtures/ que alimenta o Azure simulado")
    ap.add_argument("--time", action="append", help="time como no Portal; pode repetir (padrão: todos os times comprometidos)")
    ap.add_argument("--roadmap", help='semestre, ex.: "2026 2º Semestre" (padrão: o vigente hoje)')
    ap.add_argument("--tipo-roadmap", choices=["interno", "executivo"], default="interno")
    ap.add_argument("--simultaneas", type=int, default=12, help="(azure) chamadas simultâneas por lista de lotes; o portal usa 4")
    ap.add_argument("--limite-min", type=int, default=60, help="tempo máximo da carga do Azure, em minutos")
    ap.add_argument("--saida", default=str(RAIZ / "dist" / "relatorio"), help="pasta de saída (dist/ está no .gitignore: nunca versionar dados reais)")
    asyncio.run(gerar(ap.parse_args(argv)))


if __name__ == "__main__":
    sys.path.insert(0, str(AQUI))
    main()
