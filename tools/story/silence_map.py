"""Silence map of a run (pace trims, 2026-11-24 witch_candy): every stretch > MIN s with no voice line playing, per beat.
    python3 tools/story/silence_map.py <tale> <run.log> [min_sec=3]
Line lengths come from the clip files in script.json (ffprobe); trim the long gaps (camera holds, slow walks, waits),
never the lines."""
import json, re, subprocess, sys

tale, log = sys.argv[1], sys.argv[2]
mn = float(sys.argv[3]) if len(sys.argv) > 3 else 3.0
d = json.load(open(f"game/stories/{tale}/script.json", encoding="utf-8"))


def adur(p):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                          p.replace("res://", "game/")], capture_output=True, text=True).stdout.strip()
    try:
        return float(out)
    except ValueError:
        return 0.0


dur = {}
for L in d["lines"]:
    for i, s in enumerate(L.get("segs", [])):
        if s.get("audio"):
            dur[(L["id"], i)] = adur(s["audio"])
ev = []
for m in re.finditer(r"^(SEG (\S+) (\d+) t=([\d.]+)|BEAT (\S+) t=([\d.]+)|STORY_DONE total=([\d.]+))", open(log).read(), re.M):
    if m.group(2):
        ev.append((float(m.group(4)), "seg", m.group(2), dur.get((m.group(2), int(m.group(3))), 0.0)))
    elif m.group(5):
        ev.append((float(m.group(6)), "beat", m.group(5), 0.0))
    else:
        ev.append((float(m.group(7)), "end", "(end)", 0.0))
ev.sort()
end = tot = 0.0
for t, k, n, du in ev:
    if k == "beat":
        print(f"--- {n} {t:.1f}")
        continue
    if t - end > mn:
        print(f"   gap {t - end:5.1f} s  {end:6.1f} -> {t:6.1f}  before {n}")
        tot += t - end
    end = max(end, t + du)
print(f"SILENCE_TOTAL {tot:.1f} s in gaps > {mn} s; story {ev[-1][0]:.1f} s")
