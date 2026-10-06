#!/usr/bin/env bash
# Passo único da rotina diária (sessão nova na nuvem): instala, compila e gera o relatório.
# Uso: bash scripts/relatorio/rotina.sh /caminho/para/config.json
# Mantém aqui (versionado) o "como rodar", para a rotina agendada não depender de comandos escritos no texto dela.
set -euo pipefail
[ $# -eq 1 ] || { echo "uso: bash scripts/relatorio/rotina.sh <config.json>" >&2; exit 2; }
cd "$(dirname "$0")/../.."
# `python3 -m pip` garante instalar no MESMO Python que roda o gerador (o `pip` solto pode ser de outro)
python3 -m pip install -q -r requirements-dev.txt 2>&1 | grep -v -i "warning" || true
npm install --silent --no-audit --no-fund
npm run build
exec python3 -u scripts/relatorio/gerar_relatorio.py --config "$1" --fonte azure --limite-min 45
