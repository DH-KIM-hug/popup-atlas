#!/bin/sh
# Orbit audit of every tale's houses (2026-11-23): tools/story/house_orbit_all.sh OUT_ROOT LABEL [tale ...]
# -> OUT_ROOT/<tale>/<tale>_audit.jpg (python3 tools/story/house_audit.py) and HOLES lines.
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
OUT="$1"; LABEL="$2"; shift 2
TALES="${*:-sun_wind three_pigs witch_candy sunmoon wolf_goats patjuk turnip}"
run() { "$ROOT/tools/story/house_orbit.sh" "$1" "$2" "$OUT/$1" "$3" "$4" | grep -E "ORBIT_DONE|ERROR|no set" ; }
for T in $TALES; do
  case $T in
    sun_wind) run sun_wind bet "" 3; run sun_wind sun_turn "" 3; run sun_wind ending "" 3 ;;
    three_pigs) run three_pigs home home_house 2; run three_pigs wolf_straw straw_house,wood_house,house 2 ;;
    witch_candy) run witch_candy invite shop,house_0,house_1,house_2,house_3,house_4,house_5,house_6,house_7,house_8,house_9,house_10,house_11,house_12 2 ;;
    sunmoon) run sunmoon morning cottage 2; run sunmoon rich_house rich_house 1 ;;
    wolf_goats) run wolf_goats home cottage,mill 2 ;;
    patjuk) run patjuk winter cottage 2 ;;
    turnip) run turnip seed house,barn 2 ;;
  esac
  python3 "$ROOT/tools/story/house_audit.py" "$OUT/$T" "$T" --label "$LABEL" | grep -v "^HOLES" 
done
