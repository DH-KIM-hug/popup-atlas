#!/usr/bin/env python3
"""Quick still per beat of a tale (layout check): python3 tools/story/cap_beats.py TALE TAG FRAMES beat [beat...]
-> game/.agent_out/captures/story/<tale>_<tag>_<beat>.png (1366x1024, fixed step, autoplay, muted, no subs)."""
import sys
sys.path.insert(0, "/Users/house_of_4k2b/.claude/skills/scenario-godot-expert/scripts")
import gd_run
P = "/Users/house_of_4k2b/orca/popup-atlas/game"
tale, tag, frames = sys.argv[1], sys.argv[2], int(sys.argv[3])
for b in sys.argv[4:]:
    out = f"captures/story/{tale}_{tag}_{b}.png"
    r = gd_run.capture_scene(P, f"res://stories/{tale}/story.tscn", out=out, size=(1366, 1024), frames=frames, review=False,
                             args={"beat": b, "autoplay": True, "fixed": True, "mute": True, "subtitles": False})
    res = r.get("result") or {}
    errs = (r.get("parse_errors", []) + r.get("script_errors", []) + r.get("engine_errors", []))
    print(b, "ok" if r.get("ok") and res.get("ok") else "FAIL " + str(r.get("error"))[:300], (res.get("images") or [""])[0], flush=True)
    for p in r.get("prints", []):
        if p.startswith(("LINE", "BEAT", "SPREAD", "STORY")):
            print("   ", p[:160])
    for e in errs[:8]:
        print("  ERR", str(e)[:400])
