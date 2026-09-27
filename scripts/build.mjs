// Gera dist/mapa_portfolio.html: um único arquivo, sem servidor, com estilos e código embutidos.
// Uso: npm run build
import { readFileSync, writeFileSync, readdirSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const read = p => readFileSync(join(root, p), "utf8");
const strip = s => s.replace(/\n$/, "");   // cada fonte termina com uma quebra de linha, removida na junção

const shell = read("src/index.html");
const css = strip(read("src/styles.css"));
// ilustrações do Report F4P: viram data URI embutida (F4P_ASSETS), para o HTML final continuar num arquivo só
const f4pAssetDir = join(root, "src/assets/f4p");
const f4pAssets = Object.fromEntries(readdirSync(f4pAssetDir).filter(f => f.endsWith(".png")).map(f => {
  const key = f.replace(/\.png$/, "").replace(/-([a-z])/g, (_, c) => c.toUpperCase());
  const b64 = readFileSync(join(f4pAssetDir, f)).toString("base64");
  return [key, `data:image/png;base64,${b64}`];
}));
const f4pAssetsJs = `const F4P_ASSETS = ${JSON.stringify(f4pAssets)};\n`;
const js = f4pAssetsJs + readdirSync(join(root, "src/js")).filter(f => f.endsWith(".js")).sort()
  .map(f => strip(read(join("src/js", f)))).join("\n");

if (/<\/script/i.test(js)) throw new Error("O código contém </script>, o que quebraria o HTML de arquivo único.");
// replace com função: evita que "$&" e afins no código sejam interpretados
const out = shell.replace("/*__CSS__*/", () => css).replace("/*__APP__*/", () => js);

mkdirSync(join(root, "dist"), { recursive: true });
writeFileSync(join(root, "dist/mapa_portfolio.html"), out);
console.log(`dist/mapa_portfolio.html gerado (${(out.length / 1024 / 1024).toFixed(2)} MB)`);
