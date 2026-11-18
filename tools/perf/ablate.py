#!/usr/bin/env python3
"""python3 tools/perf/ablate.py [vulkan|metal] view variant... -> JSON (build ms, geometry audit, per-variant gpu/draws/prims)."""
import sys, json
sys.path.insert(0, "/Users/house_of_4k2b/.claude/skills/scenario-godot-expert/scripts"); import gd_run
P = "/Users/house_of_4k2b/orca/popup-atlas/game"
drv = sys.argv[1]; view = int(sys.argv[2]); variants = sys.argv[3:] or ["base"]
r = gd_run.run_script(P, "/Users/house_of_4k2b/orca/popup-atlas/tools/perf/ablate.gd", {"view": view, "variants": variants, "frames": 90},
                      headless=False, timeout=900, extra_args=None if drv == "metal" else ["--rendering-driver", drv])
print(json.dumps(r.get("result"), indent=1) if r.get("result") else r.get("error"), r.get("log", "")[-1500:] if not r.get("ok") else "")
