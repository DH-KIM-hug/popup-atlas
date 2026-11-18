#!/usr/bin/env python3
"""Perf before/after captures. python3 tools/perf/capture.py TAG [views...]   (views 0-5 = meadow cap scenes, frame 170,
fixed 1/60 step; 'wind'/'sun' = story beats wind_turn / sun_turn after N frames, fixed, autoplay, mute)
-> game/captures/perf/TAG_<view>.png (1366x1024)."""
import sys, json
sys.path.insert(0, "/Users/house_of_4k2b/.claude/skills/scenario-godot-expert/scripts")
import gd_run
P = "/Users/house_of_4k2b/orca/popup-atlas/game"
tag = sys.argv[1]
views = sys.argv[2:] or ["0", "1", "2", "3", "4", "5"]
for v in views:
    out = f"captures/perf/{tag}_{v}.png"
    if v.isdigit():
        r = gd_run.capture_scene(P, f"res://scenes/world/cap/meadow_v{v}.tscn", out=out, size=(1366, 1024), frames=170, review=False)
    else:
        beat = {"wind": "wind_turn", "sun": "sun_turn"}[v]
        r = gd_run.capture_scene(P, "res://stories/sun_wind/story.tscn", out=out, size=(1366, 1024), frames=600, review=False,
                                 args={"beat": beat, "autoplay": True, "fixed": True, "mute": True, "subtitles": False})
    res = r.get("result") or {}
    errs = (r.get("script_errors", []) + r.get("engine_errors", []) + r.get("shader_errors", []))
    print(v, "ok" if r.get("ok") and res.get("ok") else "FAIL " + str(r.get("error"))[:300], (res.get("images") or [""])[0],
          [p for p in r.get("prints", []) if p.startswith(("MEADOW", "PERF", "SPREAD view"))][:3], flush=True)
    for e in errs[:5]:
        print("  ERR", str(e)[:300])
