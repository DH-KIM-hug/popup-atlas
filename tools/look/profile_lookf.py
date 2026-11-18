#!/usr/bin/env python3
"""Profile meadow.tscn walking in the look-fable worktree. python3 tools/look/profile_lookf.py [metal|vulkan ...]"""
import sys; sys.path.insert(0, "/Users/house_of_4k2b/.claude/skills/scenario-godot-expert/scripts"); import gd_run
P = "/Users/house_of_4k2b/orca/popup-atlas-look/game"
for drv in (sys.argv[1:] or ["metal", "vulkan"]):
    r = gd_run.profile_scene(P, "res://scenes/world/meadow.tscn", seconds=6, size=(1366, 1024), driver=None if drv == "metal" else drv, csv=f"profile/lookf_{drv}.csv")
    res = r.get("result") or {}; st = (r.get("budget") or {}).get("stats") or {}
    print(drv, "ok" if r.get("ok") else "FAIL", "p50", st.get("p50_ms"), "p95", st.get("p95_ms"), "max", st.get("max_ms"), "hitches", st.get("hitches"), "draws", res.get("max_draw_calls"), "gpu_max", res.get("max_gpu_ms"), flush=True)
