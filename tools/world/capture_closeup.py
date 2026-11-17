import sys, os, subprocess
sys.path.insert(0, "/Users/house_of_4k2b/.claude/skills/scenario-godot-expert/scripts")
import gd_run
P = "/Users/house_of_4k2b/orca/popup-atlas/game"
"""PE check close-ups.  python3 tools/world/capture_closeup.py TAG VIEW (cross|vfold|box|"ex,ey,ez,tx,ty,tz,fov")
-> game/.agent_out/captures/pe_TAG.png (1024x768) via scenes/world/cap/pe_closeup.tscn."""
tag, view, find = sys.argv[1], sys.argv[2], sys.argv[3]
os.environ["PE_VIEW"] = view
if find.count(",") >= 6:
    os.environ["PE_CAM"] = find; os.environ["PE_FIND"] = ""
else:
    os.environ["PE_FIND"] = find; os.environ["PE_CAM"] = ""
r = gd_run.capture_scene(P, "res://scenes/world/cap/pe_closeup.tscn", out=f"captures/pe_{tag}.png", size=(1024, 768), frames=170, review=False, camera="PeCam")
res = r.get("result") or {}
print(res.get("images"), [p for p in r.get("prints", []) if "PE_FIND" in p or "MEADOW" in p])
for e in (r.get("script_errors", []) + r.get("engine_errors", []) + r.get("shader_errors", []))[:6]:
    print("  ERR", str(e)[:300])
