// Gera dist/mapa_portfolio.html: um único arquivo, sem servidor, com estilos, código e a biblioteca SheetJS embutidos.
// Uso: npm run build
import { readFileSync, writeFileSync, readdirSync, mkdirSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath } from "node:url";

const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const read = p => readFileSync(join(root, p), "utf8");
const strip = s => s.replace(/\n$/, "");   // cada fonte termina com uma quebra de linha, removida na junção

const shell = read("src/index.html");
const css = strip(read("src/styles.css"));
const js = readdirSync(join(root, "src/js")).filter(f => f.endsWith(".js")).sort()
  .map(f => strip(read(join("src/js", f)))).join("\n");
const xlsx = read("node_modules/xlsx/dist/xlsx.full.min.js");

if (/<\/script/i.test(js) || /<\/script/i.test(xlsx)) throw new Error("O código contém </script>, o que quebraria o HTML de arquivo único.");
// replace com função: evita que "$&" e afins no código sejam interpretados
const out = shell.replace("/*__CSS__*/", () => css).replace("/*__APP__*/", () => js).replace("/*__XLSX__*/", () => xlsx);

mkdirSync(join(root, "dist"), { recursive: true });
writeFileSync(join(root, "dist/mapa_portfolio.html"), out);
console.log(`dist/mapa_portfolio.html gerado (${(out.length / 1024 / 1024).toFixed(2)} MB)`);
