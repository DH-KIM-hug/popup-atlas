#!/bin/sh
# Web look tuning (docs/WEB_BUILD.md "Look on the web"): one still per variant of a story moment, Mobile vs desktop
# Compatibility (the web renderer), all in ONE hold of the Godot slot (short runs, frame cap 900).
#   tools/web/look_variants.sh <outdir> <tale> <beat> <capture-at s> <variants file>
# variants file: one per line "<name>|<godot flags>|<user args>" (user args: e.g. --web-look,
# LookRig's web-only overrides; to try a value, change the WEB_* constant in look_rig.gd between batches).
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="$(mkdir -p "$1" && cd "$1" && pwd)"; TALE="$2"; BEAT="$3"; AT="$4"; VF="$(cd "$(dirname "$5")" && pwd)/$(basename "$5")"
G=/Applications/Godot.app/Contents/MacOS/Godot
cat > "$OUT/.run.sh" <<RUN
#!/bin/sh
while IFS='|' read -r NAME GF UA; do
  [ -z "\$NAME" ] && continue
  # shellcheck disable=SC2086
  "$G" --path "$ROOT/game" --resolution 1366x1024 --fixed-fps 30 --quit-after 900 \$GF -- --tale=$TALE --beat=$BEAT \\
    --autoplay --mute --app-capture="$OUT/\$NAME.png" --app-capture-at=$AT \$UA < /dev/null > "$OUT/\$NAME.log" 2>&1
  echo "\$NAME \$(grep -c 'SCRIPT ERROR' "$OUT/\$NAME.log") script errors"
done < "$VF"
RUN
chmod +x "$OUT/.run.sh"
"$ROOT/tools/story/slot_wait.sh" "$OUT/.run.sh"
