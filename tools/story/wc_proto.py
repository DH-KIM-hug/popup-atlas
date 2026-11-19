#!/usr/bin/env python3
"""witch_candy phase-1 world PROTOTYPE: writes game/stories/witch_candy/proto/script.json (a two-beat tale on the real
engine: the Halloween street with the candy shop, then the camera inside the shop's room). Only existing engine
features (spread set / box / light / cam) + a tiny handler adding warm omni lights. Capture:
  godot --path game --resolution 1366x1024 --fixed-fps 30 --write-movie /tmp/s.avi --quit-after 260 -- \
        --tale=witch_candy/proto --beat=street --autoplay
"""
import json, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
SHOP = [1.05, -2.0]
S = {  # view 5 (seed 1): the road runs straight away from the camera at x -0.2..0.2
    "shop": SHOP, "est": [0.3, -1.0], "street_focus": [0.4, -1.5],
    "town": [-0.8, -1.7], "cottage_l": [-0.85, -0.45], "cottage_r": [0.8, -0.55],
    "lamp_l": [-0.4, -0.85], "lamp_r": [0.42, -1.45], "p1": [0.33, 0.05], "p2": [-0.32, 0.3], "p3": [0.62, -1.62],
    "p4": [1.52, -1.62], "stack": [-0.45, -1.35], "bunting": [-0.95, 0.05], "fence": [0.75, 0.25], "hay": [-1.15, 0.45],
    "broom": [1.72, -1.9], "moon": [-0.6, -7.0], "web": [-0.55, 0.35],
    "kid": [0.1, 0.35], "rabbit": [-0.12, 0.42], "bear": [0.3, 0.45], "fox": [-0.02, 0.6],
    # inside the shop (facade plane at z -2.0, room 1.0 deep)
    "in_back": [1.05, -2.97], "in_shelf": [0.68, -2.9], "in_pot": [1.1, -2.6], "in_counter": [1.5, -2.88],
    "in_cab": [0.62, -2.95], "in_focus": [1.05, -2.66], "in_beam": [1.05, -2.5],
    "in_kid": [0.84, -2.6], "in_witch": [1.4, -2.66], "in_cat": [1.18, -2.5], "in_rabbit": [0.5, -2.66],
    "in_bear": [0.64, -2.55], "in_fox": [0.38, -2.58],
}
SET = [
    {"card": "story_wc_shop_00", "at": "shop", "stage": "full", "name": "shop", "scale": 1.0, "clear": 2.2,
     "box": {"depth": 1.0, "side": "story_wc_shop_02", "floor": "story_wc_room_03"}},
    {"card": "story_wc_room_09", "at": "in_back", "stage": "full", "name": "room_back", "scale": 1.0, "clear": 0},
    {"card": "story_wc_room_04", "at": "in_shelf", "stage": "full", "name": "shelf", "scale": 1.0, "clear": 0},
    {"card": "story_wc_room_06", "at": "in_counter", "stage": "full", "name": "counter", "scale": 1.0, "clear": 0},
    {"card": "story_wc_room_07", "at": "in_pot", "stage": "full", "name": "hearth", "scale": 1.0, "clear": 0},
    {"card": "story_wc_pot_12", "at": "in_pot", "off": [0, 0.01], "stage": "full", "name": "logs", "scale": 1.0, "clear": 0},
    {"card": "story_wc_pot_14", "at": "in_pot", "off": [0, 0.02], "stage": "full", "name": "flame", "scale": 1.0, "clear": 0},
    {"card": "story_wc_pot_00", "at": "in_pot", "off": [0, 0.03], "stage": "full", "name": "pot", "scale": 1.0, "clear": 0,
     "lift": 0.05},
    {"card": "story_wc_room_08", "at": "in_beam", "stage": "full", "name": "beam", "scale": 1.0, "clear": 0, "lift": 0.42,
     "inside_only": True},
    {"card": "story_wc_shop_05", "at": "town", "stage": "full", "name": "town", "scale": 1.0},
    {"card": "story_wc_shop_06", "at": "cottage_l", "stage": "full", "name": "cottage_l", "scale": 1.0},
    {"card": "story_wc_halloween_13", "at": "lamp_l", "stage": "full", "name": "lamp_l", "scale": 1.0, "clear": 0.2},
    {"card": "story_wc_halloween_13", "at": "lamp_r", "stage": "full", "name": "lamp_r", "scale": 1.0, "clear": 0.2},
    {"card": "story_wc_halloween_01", "at": "p1", "stage": "full", "name": "p1", "scale": 1.0, "clear": 0.1},
    {"card": "story_wc_halloween_00", "at": "p2", "stage": "full", "name": "p2", "scale": 1.0, "clear": 0.1},
    {"card": "story_wc_halloween_02", "at": "p3", "stage": "full", "name": "p3", "scale": 0.8, "clear": 0},
    {"card": "story_wc_halloween_02", "at": "p4", "stage": "full", "name": "p4", "scale": 0.8, "clear": 0},
    {"card": "story_wc_halloween_03", "at": "stack", "stage": "full", "name": "stack", "scale": 1.0, "clear": 0.1},
    {"card": "story_wc_halloween_04", "at": "bunting", "stage": "full", "name": "bunting", "scale": 1.0, "clear": 0.3},
    {"card": "story_wc_halloween_14", "at": "fence", "stage": "full", "name": "fence", "scale": 1.0, "clear": 0.15},
    {"card": "story_wc_halloween_17", "at": "hay", "stage": "full", "name": "hay", "scale": 1.0, "clear": 0.2},
    {"card": "story_wc_halloween_15", "at": "broom", "stage": "full", "name": "broom", "scale": 1.0, "clear": 0},
    {"card": "story_wc_halloween_05", "at": "web", "stage": "full", "name": "web", "scale": 1.0, "clear": 0},
    {"card": "story_wc_halloween_10", "at": "moon", "stage": "full", "name": "moon", "scale": 6.0, "clear": 0, "lift": 1.2},
]
LIGHTS = [["lamp_l", 0.43, 1.6], ["lamp_r", 0.43, 1.6], ["p1", 0.06, 0.5, "#ffa040", 0.5], ["p2", 0.05, 0.5, "#ffa040", 0.5],
          ["stack", 0.1, 0.7, "#ffa040", 0.6], ["shop", 0.35, 1.4, "#ffb060", 1.2], ["town", 0.4, 0.9],
          ["cottage_l", 0.3, 0.8], ["in_pot", 0.12, 1.4, "#ff9a40", 1.0], ["in_focus", 0.55, 1.0, "#ffd29a", 1.4]]
SPREAD = {"seed": 1, "view": 5, "place": "street", "light": "night", "spots": S, "set": SET, "focus": "street_focus"}
CAST = {r: {"kind": "actor", "skin": s} for r, s in [("kid", "dahyun"), ("witch", "candy_witch"), ("cat", "hobak_cat"),
                                                       ("rabbit", "rabbit_kid"), ("bear", "bear_kid"), ("fox", "fox_kid")]}
SHOTS = {"establish": [8.0, 17.0, 0.3, 24.0, -4.0], "street": [5.0, 11.0, 0.32, 22.0, 6.0],
         "room": [0.5, 8.0, 0.24, 66.0, 0.0], "story": [3.7, 13.0, 0.28, 20.0]}
BEATS = [
    {"id": "street", "title": "초대장", "spread": SPREAD,
     "enter": {"who": {"kid": "excited", "rabbit": "calm", "bear": "calm", "fox": "calm"},
               "at": {"kid": "kid", "rabbit": "rabbit", "bear": "bear", "fox": "fox"}},
     "steps": [{"do": "cam", "shot": "establish", "at": "est", "wait": 3.0},
               {"do": "cam", "shot": "street", "at": "street_focus", "wait": 3.0}]},
    {"id": "room", "title": "사탕 가게", "spread": dict(SPREAD),
     "enter": {"who": {"kid": "reach", "witch": "magic", "cat": "sit", "rabbit": "cheer", "bear": "calm", "fox": "calm"},
               "at": {"kid": "in_kid", "witch": "in_witch", "cat": "in_cat", "rabbit": "in_rabbit", "bear": "in_bear",
                      "fox": "in_fox"}},
     "steps": [{"do": "cam", "shot": "room", "at": "in_focus", "wait": 4.0}]},
]
out = {"tale_id": "witch_candy_proto", "title": "사탕 마녀의 핼러윈 (prototype)", "handler": "res://stories/witch_candy/proto/fx.gd",
       "backdrop": True, "shots": SHOTS, "cast": CAST, "proto_lights": LIGHTS, "ui": {"speakers": {}},
       "voices": {}, "beats": BEATS, "lines": []}
p = os.path.join(ROOT, "game", "stories", "witch_candy", "proto", "script.json")
json.dump(out, open(p, "w"), ensure_ascii=False, indent=1)
print("wrote", p)
