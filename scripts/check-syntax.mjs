// Confere a sintaxe do código juntado (mesma ordem do build), sem abrir o navegador.
import { readFileSync, readdirSync, writeFileSync, mkdtempSync } from "node:fs";
import { join, dirname } from "node:path";
import { tmpdir } from "node:os";
import { fileURLToPath } from "node:url";
import { execFileSync } from "node:child_process";
const root = join(dirname(fileURLToPath(import.meta.url)), "..");
const js = readdirSync(join(root, "src/js")).filter(f => f.endsWith(".js")).sort()
  .map(f => readFileSync(join(root, "src/js", f), "utf8").replace(/\n$/, "")).join("\n");
const tmp = join(mkdtempSync(join(tmpdir(), "mapa-")), "app.js");
writeFileSync(tmp, js);
execFileSync(process.execPath, ["--check", tmp], { stdio: "inherit" });
console.log("Sintaxe OK");
