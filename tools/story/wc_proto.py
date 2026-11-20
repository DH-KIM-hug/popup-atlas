#!/usr/bin/env python3
"""witch_candy world PROTOTYPE / look check: writes game/stories/witch_candy/proto/script.json, three still beats on
the real engine using the tale's own street layout (tools/story/tales/witch_candy.py STREET / SHOP_SET / SKY):
the establishing street, a street shot toward the shop, and the room inside the shop. Capture:
  godot --path game --resolution 1366x1024 --fixed-fps 30 --write-movie /tmp/s.avi --quit-after 460 -- \\
        --tale=witch_candy/proto --autoplay --beat=street
"""
import json, os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tales.witch_candy as T

SPREAD = T._street()
CAST = {r: {"kind": "actor", "skin": c["skin"]} for r, c in T.CAST.items()}
BEATS = [
    {"id": "street", "title": "할로윈 마을", "spread": SPREAD,
     "enter": {"who": {"kid": "excited", "rabbit": "calm", "bear": "calm", "fox": "calm"},
               "at": {"kid": "kids", "rabbit": [-0.25, 0.5], "bear": [0.15, 0.55], "fox": [-0.12, 0.7]}},
     "steps": [{"do": "cam", "shot": "establish", "at": "est", "wait": 3.0},
               {"do": "cam", "shot": "street", "at": "street_focus", "wait": 3.0}]},
    {"id": "room", "title": "사탕 가게", "spread": SPREAD,
     "enter": {"who": {"kid": "reach", "witch": "magic", "cat": "sit", "rabbit": "cheer", "bear": "calm", "fox": "calm"},
               "at": {"kid": "in_kid", "witch": "in_witch", "cat": "in_cat", "rabbit": "in_rabbit", "bear": "in_bear",
                      "fox": "in_fox"}},
     "steps": [{"do": "cam", "shot": "room", "at": "in_focus", "wait": 4.0}]},
]
BEATS.append(T.TOUR)
out = {"tale_id": "witch_candy_proto", "title": "사탕 마녀의 핼러윈 (prototype)", "backdrop": True, "shots": T.SHOTS,
       "cast": CAST, "ui": {"speakers": {}}, "voices": {}, "beats": BEATS, "lines": []}
p = os.path.join(ROOT, "game", "stories", "witch_candy", "proto", "script.json")
json.dump(out, open(p, "w"), ensure_ascii=False, indent=1)
print("wrote", p)
