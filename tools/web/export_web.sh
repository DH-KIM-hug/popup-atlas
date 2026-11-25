#!/bin/sh
# Web build of the app (shelf first, every tale), see docs/WEB_BUILD.md.
#   tools/web/export_web.sh [--serve]      (--serve: also start the local server + tunnel, tools/web/serve.sh)
# 1. copies game/ to build/web_project/ (a throwaway copy; the real project and its iOS look are never touched)
# 2. in the copy, textures import as lossy WebP (WEB_Q, default 0.82) at WEB_SCALE (default 0.75) of their longest
#    side (tools/web/web_imports.py): pck ~405 -> ~100 MB (Godot web keeps the whole pck in browser memory) and tale
#    GPU memory ~850 -> ~480 MB, so an iPad Safari tab survives.
# 3. imports + exports the "Web" preset (no threads -> no COOP/COEP headers needed) to build/web/
# 4. splits index.pck into <= 90 MB parts for GitHub Pages (tools/web/split_pck.py) and gzips copies for serve.py
# Godot runs hold the project's slot (tools/story/with_godot.sh). Old build files are deleted (not moved to the Trash).
set -e
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="$ROOT/build/web"
PRJ="$ROOT/build/web_project"
mkdir -p "$OUT" "$PRJ"
rsync -a --delete --exclude .agent_out --exclude tools_tmp --exclude export_presets.cfg "$ROOT/game/" "$PRJ/"
cp "$ROOT/game/export_presets.cfg" "$PRJ/export_presets.cfg"
# Publish what is committed: game/ files other agents are still editing (uncommitted) go back to their HEAD version in
# the copy, so a half-done tale never reaches the public link. WEB_DIRTY=1 keeps the working tree as it is.
if [ "${WEB_DIRTY:-0}" != 1 ]; then
  git -C "$ROOT" diff --name-only HEAD -- game | while read -r f; do
    rel="${f#game/}"
    if git -C "$ROOT" cat-file -e "HEAD:$f" 2>/dev/null; then git -C "$ROOT" show "HEAD:$f" > "$PRJ/$rel"; echo "export uses HEAD: $f"
    else rm -f -- "$PRJ/$rel"; echo "export leaves out (not committed): $f"; fi
  done
fi
# Sound (web only): Godot 4.7.2's web "Sample" playback mis-orders buses added at runtime (AudioServer.add_bus() ->
# godot_audio_sample_bus_add(-1) -> Bus.move(id, -1) splices the new bus one slot early), so the sends SoundDirector
# sets wire Master back into a bus loop and nothing reaches the speakers. In the copy the same four buses exist from
# the start (default bus layout), so SoundDirector._setup_buses finds them and never calls add_bus().
cat > "$PRJ/default_bus_layout.tres" <<'TRES'
[gd_resource type="AudioBusLayout" format=3]

[resource]
bus/1/name = &"Voice"
bus/1/solo = false
bus/1/mute = false
bus/1/bypass_fx = false
bus/1/volume_db = 0.0
bus/1/send = &"Master"
bus/2/name = &"Music"
bus/2/solo = false
bus/2/mute = false
bus/2/bypass_fx = false
bus/2/volume_db = 0.0
bus/2/send = &"Master"
bus/3/name = &"Ambience"
bus/3/solo = false
bus/3/mute = false
bus/3/bypass_fx = false
bus/3/volume_db = 0.0
bus/3/send = &"Master"
bus/4/name = &"SFX"
bus/4/solo = false
bus/4/mute = false
bus/4/bypass_fx = false
bus/4/volume_db = 0.0
bus/4/send = &"Master"
TRES
python3 "$ROOT/tools/web/web_imports.py" "$PRJ" "${WEB_Q:-0.82}" "${WEB_SCALE:-0.75}"
for f in "$OUT"/index.*; do [ -f "$f" ] && rm -f -- "$f"; done  # old build: deleted for good (user 2026-11-25)
"$ROOT/tools/story/with_godot.sh" sh -c "godot --headless --path '$PRJ' --import >'$OUT/../web_import.log' 2>&1; \
  godot --headless --path '$PRJ' --export-release Web '$OUT/index.html' >'$OUT/../web_export.log' 2>&1"
[ -f "$OUT/index.pck" ] || { echo "export failed, see build/web_export.log"; exit 1; }
python3 "$ROOT/tools/web/split_pck.py" "$OUT"
for f in "$OUT"/index.wasm "$OUT"/index.js; do gzip -kf -6 "$f"; done
ls -la "$OUT"
[ "$1" = "--serve" ] && exec "$ROOT/tools/web/serve.sh"
exit 0
