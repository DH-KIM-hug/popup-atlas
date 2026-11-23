#!/bin/sh
# Web build of the app (shelf first, every tale), see docs/WEB_BUILD.md.
#   tools/web/export_web.sh [--serve]      (--serve: also start the local server + tunnel, tools/web/serve.sh)
# 1. copies game/ to build/web_project/ (a throwaway copy; the real project and its iOS look are never touched)
# 2. in the copy, textures import as lossy WebP (WEB_Q, default 0.82) at WEB_SCALE (default 0.75) of their longest
#    side (tools/web/web_imports.py): pck ~405 -> ~100 MB (Godot web keeps the whole pck in browser memory) and tale
#    GPU memory ~850 -> ~480 MB, so an iPad Safari tab survives.
# 3. imports + exports the "Web" preset (no threads -> no COOP/COEP headers needed) to build/web/
# 4. splits index.pck into <= 90 MB parts for GitHub Pages (tools/web/split_pck.py) and gzips copies for serve.py
# Godot runs hold the project's slot (tools/story/with_godot.sh). Old outputs go to ~/.Trash.
set -e
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="$ROOT/build/web"
PRJ="$ROOT/build/web_project"
mkdir -p "$OUT" "$PRJ"
rsync -a --delete --exclude .agent_out --exclude tools_tmp --exclude export_presets.cfg "$ROOT/game/" "$PRJ/"
cp "$ROOT/game/export_presets.cfg" "$PRJ/export_presets.cfg"
python3 "$ROOT/tools/web/web_imports.py" "$PRJ" "${WEB_Q:-0.82}" "${WEB_SCALE:-0.75}"
STAMP=$(date +%Y%m%d_%H%M%S)
for f in "$OUT"/index.*; do [ -e "$f" ] && mv "$f" "$HOME/.Trash/web_${STAMP}_$(basename "$f")"; done
"$ROOT/tools/story/with_godot.sh" sh -c "godot --headless --path '$PRJ' --import >'$OUT/../web_import.log' 2>&1; \
  godot --headless --path '$PRJ' --export-release Web '$OUT/index.html' >'$OUT/../web_export.log' 2>&1"
[ -f "$OUT/index.pck" ] || { echo "export failed, see build/web_export.log"; exit 1; }
python3 "$ROOT/tools/web/split_pck.py" "$OUT"
for f in "$OUT"/index.wasm "$OUT"/index.js; do gzip -kf -6 "$f"; done
ls -la "$OUT"
[ "$1" = "--serve" ] && exec "$ROOT/tools/web/serve.sh"
exit 0
