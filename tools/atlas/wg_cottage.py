#!/usr/bin/env python3
"""「늑대와 일곱 아기염소」 goat cottage (2026-11-23, as tools/atlas/sm_cottage.py): fold bands + door leaf (tools/atlas/house_stages.py) and a body (side walls, back,
thatch slopes; tools/atlas/wc_house_bodies.py) for story_wg_cottage_00, merged into one stages.json entry, so the
cottage can stand turned toward the path with a body (checklist: angled houses have bodies) and a door that opens
onto a room built inside its footprint.

  python3 tools/atlas/wg_cottage.py [--sheet artifacts/wolf_goats/cottage_body.png]
"""
import json, os, subprocess, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import wc_house_bodies as B

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
CID = "story_wg_cottage_00"
B.OVERRIDE[CID] = 232  # the thatch eave line
subprocess.run([sys.executable, os.path.join(ROOT, "tools/atlas/house_stages.py"), f"{CID}:2"], check=True)
cat = {e["id"]: e for e in json.load(open(os.path.join(B.ATLAS, "catalog.json")))}
p = os.path.join(B.ATLAS, "story_wg_cottage", "stages", "stages.json")
st = json.load(open(p))
body, viz = B.build(CID, cat[CID])
for k in ("side_file", "roof_file", "gable"):
    st[CID][k] = body[k]
json.dump(st, open(p, "w"), indent=1)
print(CID, "bands", [(b["y0"], b["y1"]) for b in st[CID]["bands"]], "door", st[CID].get("door"), "gable", body["gable"])
