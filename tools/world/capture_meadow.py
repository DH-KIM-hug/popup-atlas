#!/usr/bin/env python3
"""Capture meadow views.  python3 tools/world/capture_meadow.py TAG [frames] [view ...]
-> game/captures/meadow_TAG_v<n>.png (1366x1024), prints MEADOW line + errors + look metrics."""
import sys, json, subprocess
sys.path.insert(0, "/Users/house_of_4k2b/.claude/skills/scenario-godot-expert/scripts")
import gd_run
P = "/Users/house_of_4k2b/orca/popup-atlas/game"
tag = sys.argv[1]
frames = int(sys.argv[2]) if len(sys.argv) > 2 else 170
views = [int(v) for v in sys.argv[3:]] or [0, 1, 2, 3, 4, 5]
for v in views:
    out = f"captures/meadow_{tag}_v{v}.png"
    r = gd_run.capture_scene(P, f"res://scenes/world/cap/meadow_v{v}.tscn", out=out, size=(1366, 1024), frames=frames, review=False)
    res = r.get("result") or {}
    print(v, "ok" if r.get("ok") and res.get("ok") else "FAIL", [p for p in r.get("prints", []) if "MEADOW" in p], flush=True)
    for e in (r.get("script_errors", []) + r.get("engine_errors", []) + r.get("shader_errors", []))[:6]:
        print("  ERR", str(e)[:400])
    m = subprocess.run(["python3", "/Users/house_of_4k2b/orca/popup-atlas/tools/look/look_metrics.py", (res.get("images") or [""])[0]], capture_output=True, text=True)
    print("  ", m.stdout.strip()[:600], flush=True)
