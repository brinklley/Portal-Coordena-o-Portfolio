#!/usr/bin/env python3
"""Gera o relatório do portfólio em um único HTML offline (primeira etapa: Visão Analítica de UM time).

As regras de negócio NÃO são reimplementadas aqui: o script abre `dist/mapa_portfolio.html` num Chromium
sem interface, carrega os dados pelo mesmo caminho da tela (`azRun`), aplica os mesmos filtros (Time +
Roadmap) e captura o que as MESMAS funções do portal calculam e desenham (`anData`/`renderAnalytics`).
Depois só embute esse resultado numa casca com menu lateral, com o estilo do próprio portal e sem
bibliotecas externas.

Fontes de dados (`--fonte`):
  azure     Azure DevOps de verdade. Exige uma variável de ambiente por organização com o PAT
            (`AZURE_DEVOPS_PAT_<ORG>`, ex.: AZURE_DEVOPS_PAT_VSUNICRED). O PAT fica só neste processo.
  simulado  Azure simulado dos testes (tests/azure_simulado.py), alimentado por uma fixture fictícia de
            fixtures/. Serve para validar o pipeline sem dados reais nem token.

Uso:
  python3 scripts/relatorio/gerar_relatorio.py --config configuracao_mapa_portfolio.json --fonte azure --time MOBILE
  python3 scripts/relatorio/gerar_relatorio.py --config configuracao_mapa_portfolio.json --fonte simulado --fixture times.xlsx
"""
import argparse, html, json, re, sys
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from playwright.sync_api import sync_playwright

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
DIST = RAIZ / "dist" / "mapa_portfolio.html"
FUSO = ZoneInfo("America/Sao_Paulo")

# Frase da nota de rodapé da Visão Analítica que só faz sentido na tela interativa (números clicáveis).
FRASE_CLICAVEL = re.compile(r"\s*Os números do cabeçalho.*?quando entregue\)\.", re.S)

JS_CARREGAR = """async () => {
  azRun();
  const t0 = Date.now();
  while (Date.now() - t0 < 900000) {
    if (document.getElementById('srcLabel').textContent.includes('Azure DevOps')) return {ok:true};
    const ok = document.getElementById('azMapOk');           // colunas novas/antigas no histórico: segue o padrão (ignorar)
    if (ok && !ok.closest('[hidden]')) ok.click();
    const falha = document.querySelector('#azp .azp-bad');
    if (falha && document.getElementById('azCancel')) return {ok:false, erro: document.getElementById('azp').innerText.slice(0, 1500)};
    await new Promise(r => setTimeout(r, 400));
  }
  return {ok:false, erro:'tempo esgotado esperando a carga do Azure DevOps'};
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

JS_VISAO = """(a) => {
  S.f.team = a.time; S.f.int = a.interno; S.f.exec = a.executivo; S.f.q = ''; S.f.owners = new Set();
  openAnalytics();
  if (!AN.open) return {erro: 'a Visão analítica não habilitou (time/roadmap sem dados?)'};
  const d = anData();
  const titulo = $('anTitle').cloneNode(true), corpo = $('anBody').cloneNode(true);
  [titulo, corpo].forEach(raiz => {
    raiz.querySelectorAll('button').forEach(b => {          // no arquivo estático nada é clicável
      const s = document.createElement('span'); s.className = b.className; s.title = b.title; s.textContent = b.textContent; b.replaceWith(s); });
    raiz.querySelectorAll('[data-sort]').forEach(x => x.removeAttribute('data-sort'));
  });
  closeAnalytics();
  return {titulo: titulo.innerHTML, corpo: corpo.innerHTML, capacidade: d.cap, projetada: d.proj, epicos: d.rows.length, semestre: semLong(a.interno || a.executivo)};
}"""


def ler_config(caminho):
    cfg = json.loads(Path(caminho).read_text(encoding="utf-8"))
    if "azure" not in cfg:
        raise SystemExit(f"{caminho}: não parece uma exportação de configuração do Portal (sem a chave 'azure').")
    return cfg


def preparar_fonte(pg, cfg, args):
    """Ajusta `cfg.azure` e a rota de rede conforme a fonte. Devolve o texto de origem p/ o relatório."""
    if args.fonte == "simulado":
        sys.path.insert(0, str(RAIZ / "tests"))
        from azure_simulado import AzureSimulado, fontes_de
        sim = AzureSimulado(args.fixture)
        pg.route(re.compile(r"https://(analytics\.)?dev\.azure\.com/.*"), sim.rota)
        fontes = fontes_de(sim)
        cfg["azure"].update(orgs=[{"org": o} for o in sorted({f["org"] for f in fontes})], sources=fontes, maps={}, mapMeta={})
        cfg["flow"] = {}   # o fluxo da configuração descreve os quadros REAIS; os quadros fictícios usam o fluxo padrão
        tokens = {o["org"]: "token-simulado" for o in cfg["azure"]["orgs"]}
        return tokens, "Azure simulado (dados fictícios)"
    from ponte_azure import Ponte, pats_do_ambiente, ENCHIMENTO
    orgs = sorted({s["org"] for s in cfg["azure"]["sources"]})
    ponte = Ponte(pats_do_ambiente(orgs))
    pg.route(re.compile(r"https://(analytics\.)?dev\.azure\.com/.*"), ponte.rota)
    return {o: ENCHIMENTO for o in orgs}, "Azure DevOps"


def montar_secao(sid, dados):
    return (f'<section class="rel-sec" id="{sid}" aria-label="Visão Analítica · {html.escape(dados["time"])}">\n'
            f'<div class="an-head"><div class="an-title">{dados["titulo"]}</div></div>\n'
            f'<div class="an-body">{dados["corpo"]}</div>\n</section>')


def gerar(args):
    if not DIST.exists():
        raise SystemExit("Falta o dist/mapa_portfolio.html: rode `npm run build` antes.")
    cfg = ler_config(args.config)
    agora = datetime.now(FUSO)
    with sync_playwright() as p:
        navegador = p.chromium.launch()
        ctx = navegador.new_context(viewport={"width": 1500, "height": 950}, timezone_id="America/Sao_Paulo", locale="pt-BR")
        pg = ctx.new_page()
        erros = []
        pg.on("pageerror", lambda e: erros.append(str(e)))
        pg.goto(DIST.as_uri())
        pg.wait_for_timeout(400)
        tokens, origem = preparar_fonte(pg, cfg, args)
        # Configuração do Portal (sem token). `saveCfg` grava só no localStorage deste navegador descartável.
        pg.evaluate("([j, tokens]) => { CFG = normCfg(j); saveCfg(); Object.entries(tokens).forEach(([o, t]) => AZ.tokens[o] = t); }", [cfg, tokens])
        r = pg.evaluate(JS_CARREGAR)
        if not r["ok"]:
            raise SystemExit("A carga do Azure DevOps não terminou:\n" + r["erro"])
        pg.wait_for_timeout(300)
        # uma fonte que falha não derruba a carga (o portal segue com o resto): para um relatório diário isso
        # seria dado faltando sem aviso, então aqui qualquer fonte ausente aborta a geração.
        faltam = pg.evaluate("""() => { const ok = new Set(AZ.raw.map(L => L.src.id)); return azCfgOf(CFG).sources.filter(s => !ok.has(s.id)).map(s => `${s.org}/${s.alias || s.team}`); }""")
        if faltam:
            raise SystemExit("Fontes do Azure DevOps que não carregaram (relatório não gerado): " + ", ".join(faltam))

        vigente = pg.evaluate("semestre(TODAY)")
        roadmap = args.roadmap or vigente
        opcoes = pg.evaluate("[...document.getElementById(%r).options].map(o => o.value).filter(Boolean)" % ("fInt" if args.tipo_roadmap == "interno" else "fExec"))
        if roadmap not in opcoes:
            raise SystemExit(f"O roadmap {roadmap!r} não existe nos dados carregados. Disponíveis: {', '.join(opcoes) or '(nenhum)'}")
        rm = {"interno": roadmap if args.tipo_roadmap == "interno" else "", "executivo": roadmap if args.tipo_roadmap == "executivo" else ""}

        comprometidos = [t for t in pg.evaluate(JS_TIMES, rm) if t["capacidade"] > 0]
        print(f"Roadmap {roadmap} ({args.tipo_roadmap}) · times comprometidos: " +
              (", ".join(f'{t["time"]} (cap {t["capacidade"]}/proj {t["projetada"]})' for t in comprometidos) or "nenhum"))
        alvo = args.time or (comprometidos[0]["time"] if comprometidos else None)
        if not alvo:
            raise SystemExit("Nenhum time comprometido (com itens reservados) neste roadmap.")
        if alvo not in {t["time"] for t in comprometidos}:
            raise SystemExit(f"O time {alvo!r} não está comprometido no roadmap {roadmap}. Comprometidos: {', '.join(t['time'] for t in comprometidos)}")

        dados = pg.evaluate(JS_VISAO, {"time": alvo, **rm})
        if "erro" in dados:
            raise SystemExit(dados["erro"])
        dados["time"] = alvo
        dados["corpo"] = FRASE_CLICAVEL.sub("", dados["corpo"])
        ctx.close(); navegador.close()
    if erros:
        raise SystemExit("Erros de JavaScript no portal durante a geração: " + "; ".join(erros))

    sid = "va-" + re.sub(r"[^a-z0-9]+", "-", alvo.lower()).strip("-")
    menu = ('  <h2>Visão Analítica</h2>\n' f'  <a href="#{sid}">{html.escape(alvo)}<small>{dados["capacidade"]} US capacidade · {dados["epicos"]} épicos</small></a>\n'
            '  <h2>Actionable</h2>\n  <span class="off">em construção<small>próxima etapa</small></span>\n'
            '  <h2>Report F4P</h2>\n  <span class="off">em construção<small>próxima etapa</small></span>')
    css = (RAIZ / "src" / "styles.css").read_text(encoding="utf-8")
    modelo = (AQUI / "modelo.html").read_text(encoding="utf-8")
    saida = (modelo.replace("__DATA_CURTA__", agora.strftime("%d/%m/%Y")).replace("__GERADO_EM__", agora.strftime("%d/%m/%Y às %H:%M"))
             .replace("__ROADMAP__", html.escape(dados["semestre"])).replace("__MENU__", menu)
             .replace("__SECOES__", montar_secao(sid, dados)).replace("/*__CSS__*/", css))
    if re.search(r"<script[^>]*src=|<link[^>]*href=\"http|@import|https?://[^\"')\s]*\.(js|css)", saida):
        raise SystemExit("O relatório referenciou recurso externo, o que quebraria o requisito de arquivo único offline.")
    pasta = Path(args.saida); pasta.mkdir(parents=True, exist_ok=True)
    arq = pasta / f"relatorio_portfolio_{agora.strftime('%Y-%m-%d')}_{re.sub(r'[^A-Za-z0-9]+', '-', alvo).strip('-')}.html"
    arq.write_text(saida, encoding="utf-8")
    print(f"Origem dos dados: {origem}\nGerado: {arq} ({arq.stat().st_size / 1024:.0f} KB) · {dados['epicos']} épicos · Capacidade {dados['capacidade']} / Projetada {dados['projetada']}")
    return arq


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--config", required=True, help="exportação da configuração do Portal (JSON, sem token)")
    ap.add_argument("--fonte", choices=["azure", "simulado"], default="azure")
    ap.add_argument("--fixture", default="times.xlsx", help="(simulado) fixture de fixtures/ que alimenta o Azure simulado")
    ap.add_argument("--time", help="nome do time como no Portal (padrão: o primeiro time comprometido)")
    ap.add_argument("--roadmap", help='semestre, ex.: "2026 2º Semestre" (padrão: o vigente hoje)')
    ap.add_argument("--tipo-roadmap", choices=["interno", "executivo"], default="interno")
    ap.add_argument("--saida", default=str(RAIZ / "dist" / "relatorio"), help="pasta de saída (dist/ está no .gitignore: nunca versionar dados reais)")
    gerar(ap.parse_args(argv))


if __name__ == "__main__":
    sys.path.insert(0, str(AQUI))
    main()
