#!/bin/sh
# House bodies (2026-11-23): short 1200x900 clips of the beats where each tale's houses show most.
#   tools/story/house_clips.sh OUT_DIR [tale:beat:seconds ...]   (absolute movie paths; import first)
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
G=/Applications/Godot.app/Contents/MacOS/Godot
OUT="$(cd "$1" 2>/dev/null && pwd || (mkdir -p "$1" && cd "$1" && pwd))"; shift
LIST="${*:-sun_wind:bet:22 three_pigs:wolf_straw:28 witch_candy:invite:28 sunmoon:morning:22 sunmoon:rich_house:16 wolf_goats:home:24 patjuk:winter:24 turnip:seed:22}"
"$ROOT/tools/story/with_godot.sh" "$G" --headless --path "$ROOT/game" --import > "$OUT/import.log" 2>&1
for item in $LIST; do
  T=$(echo $item | cut -d: -f1); B=$(echo $item | cut -d: -f2); SEC=$(echo $item | cut -d: -f3)
  AVI="$OUT/${T}_${B}.avi"; MP4="$OUT/${T}_${B}.mp4"
  FR=$(python3 -c "print(int(float('$SEC')*30))")
  "$ROOT/tools/story/with_godot.sh" "$G" --path "$ROOT/game" --resolution 1200x900 --fixed-fps 30 --write-movie "$AVI" \
    --quit-after "$FR" -- --tale="$T" --beat="$B" --autoplay > "$OUT/${T}_${B}.log" 2>&1
  ffmpeg -y -loglevel error -i "$AVI" -c:v libx264 -crf 26 -preset veryfast -pix_fmt yuv420p -c:a aac "$MP4" && mv "$AVI" ~/.Trash/ 2>/dev/null
  echo "$MP4 $(grep -c 'SCRIPT ERROR' "$OUT/${T}_${B}.log") errors"
done
