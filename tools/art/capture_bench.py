#!/usr/bin/env python3
"""Capture art_bench views.  python3 tools/art/capture_bench.py TAG [view ...]  -> game/.agent_out/captures/art_TAG_v<n>.png"""
import sys
sys.path.insert(0, "/Users/house_of_4k2b/.claude/skills/scenario-godot-expert/scripts")
import gd_run
P = "/Users/house_of_4k2b/orca/popup-atlas/game"
tag = sys.argv[1]
views = [int(v) for v in sys.argv[2:]] or [0, 1, 2, 3, 4]
for v in views:
    sc = "res://scenes/art_bench/art_bench.tscn" if v == 0 else f"res://scenes/art_bench/art_bench_v{v}.tscn"
    r = gd_run.capture_scene(P, sc, out=f"captures/art_{tag}_v{v}.png", size=(1366, 1024), frames=20)
    res = r.get("result") or {}
    print(v, "ok" if r.get("ok") and res.get("ok") else "FAIL", [p for p in r.get("prints", []) if "ART_BENCH" in p],
          "errs", len(r.get("script_errors", [])), len(r.get("shader_errors", [])), len(r.get("engine_errors", [])), flush=True)
    for e in (r.get("script_errors", []) + r.get("engine_errors", []))[:5]:
        print("  ", str(e)[:300])
