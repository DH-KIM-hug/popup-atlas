"""「늑대와 일곱 아기염소」 (wolf_goats) adaptation tables for tools/story/seed_script.py (plan: game/stories/wolf_goats/PLAN.md).

Phase 1 (2026-11-23): plan, script, shared art, first playable wiring (handler game/stories/wolf_goats/fx.gd).

Source: 톡톡's wolf_goats has the play script (voice_script_el.json: taps on the mother / wolf / stones, the youngest
hidden by a tap, belly taps) and the READ-MODE script (read_script_el.json, scenes R01-R10, every line recorded in
read_narration_el.js). The pop-up book follows the READ script (story first: no quizzes, no counting, no moral) and
borrows only the play script's first-tap instructions, each voiced once (wg_044, 046, 047, 049, 050, 051).

Softening as in the read script (톡톡 TALES_PLAN_2.md): the swallowing happens off screen (the camera is on the clock,
where the youngest peeks out; we hear it), the kids are unhurt in a warm belly, the mother's body hides the opening,
the wolf falls into the well and runs away soaking wet (he does not die).
"""
import math as _m

TALE_ID = "wolf_goats"
TITLE = "늑대와 일곱 아기염소"
PREFIX = "wg"
MORAL = ""  # no moral (user: the book tells the tale); the read script's closing moral wg_r1005 is not used
READ_SCRIPT = True

# ---------------------------------------------------------------- line adaptations
CHANGED = {}
SEG_KEEP = {}
# read lines trimmed to some of their segs (clips reused, nothing to record): narrator tags the picture already shows
READ_SEG_KEEP = {
    "wg_r0105": [0],   # the kids' "네, 엄마!" only ("아기 염소들이 큰 소리로 대답했어요." dropped)
    "wg_r0205": [0],   # the eldest's "목소리가 굵고 거칠어. 우리 엄마가 아니야!" only
    "wg_r0206": [0],   # "저리 가요, 늑대!" only
    "wg_r0307": [0],   # "그럼 문틈으로 발을 보여 주세요!" only
    "wg_r0403": [0],   # the wolf's "에취!" only (the flour puff shows it)
    "wg_r0501": [0],   # "숨자, 숨자!" only (the taps hide them under the quilt, in the basket, under the table)
    "wg_r0705": [0],   # the youngest's "엄마, 조심조심이요." only (v2 pace: not used)
    "wg_r0803": [0],
    "wg_r0504": [0],   # v2 pace: the wolf's "어디 숨었나? 다 찾아낼 테다!" only (he searches on screen)   # v2 pace: the kids' "엄마!" only (six of them jump out on screen)
}
NEW_LINES = {
    # wolf_goats' narrator is the same ElevenLabs voice as witch_candy's (pFZP5JQG7iQjIQuC4Bku): witch_candy's recorded
    # cover / replay clips (same text) are reused (game/audio/voice/wolf_goats/recorded.json), nothing to record
    "wg_n01": [["nar", "그림책을 톡 눌러서 펼쳐 볼까요?", None, "[cheerful, inviting, warm, cosy Halloween night]"]],
    "wg_n02": [["nar", "또 보고 싶으면 '다시 보기'를 톡!", None, "[cheerful, inviting]"]],
}
# No counting: "하나, 둘, 셋… 아기 염소들이 폴짝폴짝 뛰어나왔어요." — the count sits before a 0.5 s pause (silencedetect
# 1.70-2.21 s); the clip is trimmed from 2.0 s (80 ms fade-in): "아기 염소들이 폴짝폴짝 뛰어나왔어요." (nothing recorded)
TRIM = {
    "wg_r0802": ("아기 염소들이 폴짝폴짝 뛰어나왔어요.", "res://audio/voice/wolf_goats/nar_c56b61c056_t.mp3",
                 "audio/el/wolf_goats/nar_c56b61c056.mp3 (trimmed from 2.0 s: the count dropped)"),
}
TRIM_SEG = {}
DROPPED = set()
K6 = ["kid1", "kid2", "kid3", "kid4", "kid5", "kid6"]
KIDS = K6 + ["baby"]


def _all(pose, who=KIDS):
    return {k: pose for k in who}


LINE_META = {
    "wg_n01": {}, "wg_n02": {},
    "wg_r0100": {"expr": {**_all("calm"), "mom": "calm"}},
    "wg_r0103": {"expr": {"mom": "warn"}},
    "wg_r0104": {"expr": {"mom": "warn", **_all("look_up", K6)}},
    "wg_r0105": {"expr": {**_all("joy", K6), "baby": "calm"}},
    "wg_r0106": {"expr": {}},
    "wg_r0200": {"expr": {**_all("scared", K6), "baby": "worried"}},
    # v2: "knock" (he knocks as he calls); the front "shout" figure turned invisible on the door step after the side
    # knock pose (the wolf vanished for the whole line in the v2 tests; logged as an open engine issue)
    "wg_r0202": {"expr": {"wolf": "knock"}},
    "wg_r0205": {"expr": {"kid1": "suspicious"}},
    "wg_r0206": {"expr": {**_all("shout", K6)}},
    "wg_r0302": {"expr": {"wolf": "hungry"}},
    "wg_r0303": {"expr": {"wolf": "munch"}},
    "wg_r0304": {"expr": {"wolf": "sweet"}},
    "wg_r0306": {"expr": {"wolf": "sweet"}},
    "wg_r0307": {"expr": {"kid1": "suspicious"}},
    "wg_r0308": {"expr": {**_all("shout", K6)}},
    "wg_r0402": {"expr": {"wolf": "paw_show"}},
    "wg_r0403": {"expr": {"wolf": "sneeze"}},
    "wg_r0405": {"expr": {**_all("joy", K6), "baby": "calm"}},
    "wg_r0500": {"expr": {"wolf": "search", **_all("scared", K6), "baby": "worried"}},
    "wg_r0501": {"expr": {**_all("scared", K6)}},
    "wg_r0504": {"expr": {"wolf": ["search", "sniff"]}},
    "wg_r0601": {"expr": {"mom": "shocked"}},
    "wg_r0603": {"expr": {"mom": "call"}},
    "wg_r0604": {"expr": {"baby": ["joy_jump", "calm"], "mom": "hug"}},
    "wg_r0605": {"expr": {"baby": "cry", "mom": "hug"}},
    "wg_r0607": {"expr": {"mom": "ready", "baby": "worried"}},
    "wg_r0701": {"expr": {"wolf": "sleep_full"}},
    "wg_r0704": {"expr": {"mom": "shush"}},
    "wg_r0705": {"expr": {"baby": "whisper"}},
    "wg_r0801": {"expr": {"mom": "kneel_cut"}},
    "wg_r0803": {"expr": {**_all("joy", K6), "mom": "hug"}},
    "wg_r0804": {"expr": {"mom": "ready"}},
    "wg_r0807": {"expr": {"mom": "kneel_sew"}},
    "wg_r0901": {"expr": {"wolf": "groggy", **_all("scared"), "mom": "shocked"}},
    "wg_r0902": {"expr": {"wolf": "groggy"}},
    "wg_r0904": {"expr": {"wolf": "peer_well"}},
    "wg_r0907": {"expr": {"wolf": "wet"}},
    "wg_r1001": {"expr": {**_all("dance", K6), "baby": "joy_jump", "mom": "dance"}},
    "wg_r1004": {"expr": {**_all("joy", K6), "baby": "calm", "mom": "dance"}},
}

# ---------------------------------------------------------------- stage
HANDLER = "res://stories/wolf_goats/fx.gd"
BACKDROP = True
INSIDE_FRAMING = "manual"
EXTRA = {"ground_style": "paper", "spacing": True, "overlap_check": True, "pop_in": False,
         # v2 (glides in / out through the front wall filled the frame with the door leaf and the wall's inside face):
         # the facade and the door fold away 0.55 in front of the wall, the inside face waits until the camera is in
         "inside_margin": 0.7, "inside_door_hide": True,
         # intended contacts (reason): the mother kneels in front of the sleeping wolf so her body hides the opening
         # (read script: "가르는 순간은 엄마 몸이 가린다"); the wolf leans over the well rim and drops into it
         # the kids hop out of the sleeping wolf's belly (they start inside his footprint, by design)
         "overlap_ok": [["mom", "wolf"], ["wolf", "kid1"], ["wolf", "kid2"], ["wolf", "kid3"], ["wolf", "kid4"],
                        ["wolf", "kid5"], ["wolf", "kid6"], ["wolf", "well"], ["wolf", "well_rim"], ["wolf", "oak"],
                        # the two kids dive into the laundry basket (its card turns into the hiding variant)
                        ["kid3", "basket"], ["kid4", "basket"]]
                       + [[r, f] for f in ["room_floor", "room_rug"]  # the room floor + rug (wave 1)
                          for r in ["kid1", "kid2", "kid3", "kid4", "kid5", "kid6", "baby", "mom", "wolf"]],
         "kid_voice": "kid3"}

COT_YAW = -30.0
SHOTS = {"story": [3.4, 12.0, 0.28, 20.0], "close": [2.9, 12.0, 0.32, 20.0],
         "crane_high": [9.0, 36.0, 0.3, 24.0, 0.0],
         "establish": [6.0, 17.0, 0.35, 24.0, -8.0],
         "medium": [2.4, 9.0, 0.3, 22.0, 6.0], "two_shot": [2.0, 8.0, 0.3, 24.0, -10.0],
         "face": [1.3, 6.0, 0.3, 22.0, 0.0],
         "track": [3.4, 24.0, 0.25, 22.0, 0.0],             # following the wolf along the road, above the verge
         "house": [2.8, 12.0, 0.4, 28.0, COT_YAW],         # straight on to the cottage from its path
         "door_ots": [1.35, 9.0, 0.3, 30.0, COT_YAW + 28.0],  # over the wolf's shoulder onto the door
         "door_low": [1.1, 3.0, 0.28, 34.0, COT_YAW - 12.0],  # low at the doorstep: the wolf looming at the door
         # inside the cottage (camera just behind the hidden front wall), in the cottage's frame
         # v2: the room is shot from just in front of the front wall (inside_margin folds the facade and the door
         # away there), a longer lens and lower: the kids read bigger and the wolf in the room stays clear of the lens
         # (v1 [0.8, 32, 0.12, 64]: a high wide view from right behind the wall, the kids small, the wolf a giant)
         "room": [1.1, 24.0, 0.14, 54.0, COT_YAW],
         "room_wide": [1.25, 26.0, 0.14, 62.0, COT_YAW],
         "door_in": [0.45, 28.0, 0.24, 56.0, COT_YAW + 180.0],  # turned round inside: the door (paw under it)
         "clock_close": [0.42, 8.0, 0.34, 40.0, COT_YAW + 14.0],
         "stall": [1.5, 10.0, 0.3, 28.0, -12.0],
         "mill": [2.2, 12.0, 0.4, 28.0, 8.0],
         # the meadow by the oak and the well (spread B)
         # v2: higher (16 -> 23 deg) and turned left: from low a raised meadow tier on the right stood in the
         # foreground like a green slab
         "tree_wide": [5.2, 23.0, 0.45, 26.0, -22.0],
         "tree_two": [2.0, 9.0, 0.25, 26.0, 12.0],
         # v2: the six kids out of the belly stand in front of it; a higher, wider two-shot keeps the front row whole
         # (tree_two cut them off at the frame's bottom edge, faces filling the lens)
         "pop_wide": [2.9, 17.0, 0.2, 30.0, 10.0],
         # v2: wide enough that the kids' leaps land in frame (1.15 / fov 30 cut them off mid-air, blurred)
         "belly": [2.1, 20.0, 0.1, 34.0, 6.0],
         "well_wide": [3.6, 18.0, 0.3, 26.0, 4.0],
         "well_low": [1.5, 6.0, 0.28, 30.0, -10.0],
         "pull_back": [10.5, 26.0, 0.3, 24.0, 0.0]}

ROLES_LABEL = {"mom": "엄마 염소", "wolf": "늑대", "baby": "막내"}
# per-tale heights (the cottage door is 0.51 tall at scale 1.25): stage scale 1.3 -> mom 0.40, wolf 0.44, kids ~0.19
KID_H = {"kid1": 0.178, "kid2": 0.173, "kid3": 0.166, "kid4": 0.16, "kid5": 0.155, "kid6": 0.15}  # v2: x1.1
CAST = {
    "mom": {"kind": "actor", "skin": "goat_mom", "height": 0.31, "views": ["front", "side", "back"], "label": "엄마 염소"},
    "wolf": {"kind": "actor", "skin": "wolf", "height": 0.335, "views": ["front", "side", "back"], "label": "늑대 (shared)"},
    "baby": {"kind": "actor", "skin": "goat_baby", "height": 0.13, "views": ["front", "side", "back"], "label": "막내"},
}
for _i, _k in enumerate(K6, start=1):
    CAST[_k] = {"kind": "actor", "skin": f"goat_kid_{_i}", "height": KID_H[_k], "views": ["front", "side", "back"],
                "label": f"아기 염소 {_i}"}
UI = {
    "cover": [["cast_goat_mom_calm", 230], ["cast_goat_kid_1_calm", 120], ["cast_goat_baby_calm", 100]],
    "end": [["cast_goat_mom_dance", 230], ["cast_goat_kid_3_dance", 120], ["cast_goat_baby_joy_jump", 110]],
    "speakers": {"mom": ["엄마 염소", "c8473c", "cast_goat_mom_calm"], "kid": ["아기 염소", "e0a030", "cast_goat_kid_1_calm"],
                 "wolf": ["늑대", "6b6f7a", "cast_wolf_calm"]},
}


def rot(c, dx, dz, yaw):
    """A point dx right / dz in front of c in a piece turned by yaw degrees (stage frame [right, toward])."""
    t = _m.radians(yaw)
    return [round(c[0] + dx * _m.cos(t) + dz * _m.sin(t), 3), round(c[1] - dx * _m.sin(t) + dz * _m.cos(t), 3)]


def _e(card, at, name, scale=1.0, **kw):
    e = {"card": card, "at": at, "stage": "full", "name": name, "scale": scale, "clear": 0.6}
    e.update(kw)
    return e


# ---------------------------------------------------------------- spread A: the goats' home (seed 2, view 0)
# The road (probed, view-0 frame [right, toward]): from (-0.6, 0.9) through (0, 0) to (0.75, -3.3), over the plank bridge
# at -3.6..-4.2 and on. The cottage stands right of the road, turned to face it (yaw -30), with a body and its room
# inside the footprint (the camera glides in through the closed front wall); a stepping-stone path from its door to the
# road. Up the road on the left, the little market stall (chalk); over the bridge, the windmill (flour).
COT = [1.85, -1.1]
HOUSE_SCALE = 1.25
FLOOR_LIFT = 0.065  # a 0.05 meadow tier crosses the right half of the cottage footprint (probe_ground_tn.gd seed=2
# view=0: the front edge stands on the low side), so the one floor sheet lifts over the tier top plus its cover patches
HOME = {"cottage": COT}
_IN = {"door": (0.0, 0.32), "door_in": (0.0, -0.22), "wall_in": (0.0, -0.015), "in_back": (0.0, -1.07), "in_floor": (0.0, -0.02),
       "in_rug": (0.0, -0.33), "in_focus": (0.0, -0.72), "in_clock": (-0.78, -0.97), "in_bed": (0.58, -0.93),
       "in_table": (-0.4, -0.86), "in_chair": (0.2, -0.86), "in_basket": (0.82, -0.5), "in_stove": (-0.88, -0.42),
       # v2: the family stands deep in the room (the camera just inside the front wall looks down on them; the wolf in
       # the doorway stays behind the lens); the mother behind the gap in the kids' row
       "in_mom": (0.0, -0.72), "in_mom2": (0.05, -0.45), "in_wolf": (0.0, -0.24), "in_search": (0.05, -0.42),
       "in_baby2": (-0.35, -0.55), "in_clock_front": (-0.64, -0.82),
       "bed_front": (0.55, -0.76), "table_front": (-0.4, -0.72), "basket_front": (0.68, -0.42),
       "basket_via": (0.64, -0.72),
       "wolf_door": (0.1, 0.34), "door_view": (0.0, 0.9), "wolf_step": (0.0, 0.2)}
for _nm, (_dx, _dz) in _IN.items():
    HOME[_nm] = rot(COT, _dx, _dz, COT_YAW)
# the kids in a row with a gap on the door's axis (the mother walks out through it, the wolf comes in through it)
for _k, _x in zip(KIDS, [-0.68, -0.51, -0.34, -0.17, 0.17, 0.34, 0.51]):  # v2: a wider step (bigger kids)
    HOME[f"in_{_k}"] = rot(COT, _x, -0.58, COT_YAW)
# v2 (pace: the first full run took 7:32): the stall and the mill stand across the road from the cottage, a few steps
# away, so the wolf's errands are short camera moves, not long walks
HOME.update({"est": [0.2, -1.0], "road_near": [-0.45, 0.85], "road_door": [0.65, -0.6], "road_mid": [0.15, -0.35],
             "road_far": [0.78, -3.2], "road_mid2": [0.42, -1.5], "stall": [-0.9, -0.5], "wolf_stall": [-0.5, -0.22], "mill": [-1.35, -1.95],
             "sack": [-0.72, -1.65], "wolf_mill": [-0.45, -1.42], "road_mill": [0.35, -1.3], "errand": [-0.3, -0.9]})
SET_A = [
    _e("story_wg_cottage_00", "cottage", "cottage", HOUSE_SCALE, yaw=COT_YAW, clear=1.6, door_in=True,
       box={"depth": 1.1, "body": True}),
    # wave 1 (2026-11-24, felt removal): the room floor is ONE plain paper plank sheet laid flat over the whole footprint
    # (front wall to back wall, 2.06 wide, one plane: two sheets at their own ground heights met in a step where a
    # meadow tier crosses the house), registered as a floor so the meadow never shows through, and one cut-paper rag
    # rug on top (was the floorboards card with a woolly braided rug, laid twice, the meadow showing between)
    {"card": "story_wg_floor_02", "at": "in_floor", "stage": "full", "flat": True, "floor": True, "name": "room_floor",
     "scale": HOUSE_SCALE, "clear": 0, "lift": FLOOR_LIFT, "thick": 0.0015, "edge": "#6b3a1c", "yaw": COT_YAW},
    {"card": "story_wg_floor_01", "at": "in_rug", "stage": "full", "flat": True, "floor": True, "name": "room_rug",
     "scale": HOUSE_SCALE, "clear": 0, "lift": 0.003, "thick": 0.0012, "edge": "#8a3b20", "yaw": COT_YAW},
    {"card": "story_wg_cottage_03", "at": "in_back", "stage": "full", "name": "room_back", "scale": HOUSE_SCALE,
     "clear": 0, "yaw": COT_YAW},
    {"card": "story_wg_cottage_04", "at": "wall_in", "stage": "full", "name": "wall_in", "scale": HOUSE_SCALE,
     "clear": 0, "yaw": COT_YAW + 180.0, "inside_only": True},
    {"card": "story_wg_cottage_04o", "at": "wall_in", "stage": "full", "name": "wall_in_open", "scale": HOUSE_SCALE,
     "clear": 0, "yaw": COT_YAW + 180.0, "inside_only": True},
    _e("story_wg_room_00", "in_clock", "clock", clear=0, yaw=COT_YAW),
    _e("story_wg_hide_00", "in_clock", "clock_eyes", stage=0, clear=0, yaw=COT_YAW),
    _e("story_wg_hide_01", "in_clock", "clock_kid", stage=0, clear=0, yaw=COT_YAW),
    _e("story_wg_room_01", "in_clock", "clock_open", stage=0, clear=0, yaw=COT_YAW),
    _e("story_wg_room_02", "in_bed", "bed", clear=0, yaw=COT_YAW),
    _e("story_wg_hide_02", "in_bed", "bed_hide", stage=0, clear=0, yaw=COT_YAW),
    _e("story_wg_room_07", "in_bed", "bed_mess", stage=0, clear=0, yaw=COT_YAW),
    _e("story_wg_room_04", "in_table", "table", clear=0, yaw=COT_YAW),
    _e("story_wg_hide_03", "in_table", "table_hide", stage=0, clear=0, yaw=COT_YAW),
    _e("story_wg_room_09", "in_table", "table_mess", stage=0, clear=0, yaw=COT_YAW),
    _e("story_wg_room_05", "in_chair", "chair", clear=0, yaw=COT_YAW),
    _e("story_wg_room_06", "in_chair", "chair_mess", stage=0, clear=0, yaw=COT_YAW),
    _e("story_wg_room_03", "in_basket", "basket", clear=0, yaw=COT_YAW),
    _e("story_wg_hide_04", "in_basket", "basket_hide", stage=0, clear=0, yaw=COT_YAW),
    _e("story_wg_room_08", "in_basket", "basket_mess", stage=0, clear=0, yaw=COT_YAW),
    _e("story_wg_room_11", "in_stove", "stove", clear=0, yaw=COT_YAW),
    # up the road: the stall with the chalk (left), the windmill with its flour sacks (over the bridge, right)
    _e("story_wg_meadow_05", "stall", "stall", clear=0.7),
    _e("village_houses_05", "mill", "mill", 1.25, clear=1.0),
    _e("story_wg_fx_00", "sack", "sack", clear=0.3),
    _e("village_props_27", [-0.95, -1.45], "sacks", clear=0.2),
]
# stepping stones from the door to the road (houses face the road; a short path from each door)
_d0 = rot(COT, 0.0, 0.42, COT_YAW)
for _k in range(8):  # straight from the doorstep to the road's edge
    _nm = f"cot_st{_k}"
    _f = _k / 7.0
    HOME[_nm] = [round(_d0[0] + (HOME["road_door"][0] + 0.15 - _d0[0]) * _f, 3),
                 round(_d0[1] + (HOME["road_door"][1] - _d0[1]) * _f, 3)]
    SET_A.append({"card": ["stream_water_21", "stream_water_22"][_k % 2], "at": _nm, "stage": "full", "name": _nm,
                  "scale": 0.5, "clear": 0.08, "yaw": COT_YAW})


def _home(**kw):
    sp = {"seed": 2, "view": 0, "place": "home", "light": "", "spots": HOME, "set": SET_A, "focus": "est"}
    sp.update(kw)
    return sp


# ---------------------------------------------------------------- spread B: the oak and the well (seed 2, view 4)
# The road (view-4 frame): (-0.6, 0.9) -> (0, 0) -> (0.35, -1.5) -> (-0.6, -4.8). The big oak right of the road, the
# wolf asleep in its shade; the old well beyond it; a hedge across the road where the family stands back to watch.
OAK = [2.4, -2.15]
WELL = [1.12, -2.35]
# v3: the whole sleeping scene sits left of the meadow's terrace step (a raised ground edge near x 2.5 hid kids behind
# it and stood in the tree_two lens; ground steps are not set pieces, so the overlap check cannot see them)
TREE = {"oak": OAK, "well": WELL, "well_rim": [WELL[0], WELL[1] + 0.03], "hedge": [3.65, -1.35],
        "wolf_sleep": [1.55, -1.45], "belly": [1.55, -1.43], "mom_kneel": [1.42, -1.22], "baby_by": [1.02, -1.02],
        "mom_near": [1.0, -0.82], "baby_near": [0.74, -0.76], "road_near": [-0.5, 0.95], "road_bend": [0.1, -0.2],
        "stones": [1.88, -1.82],  # v4: behind the sleeping wolf, clear of the meadow terrace step on the right
        "tree_focus": [1.4, -1.4], "well_focus": [1.0, -1.9],
        "wolf_well": [0.84, -2.15], "wolf_wet": [0.55, -1.85], "road_far": [-0.4, -4.4], "road_mid": [0.3, -2.0],
        "watch_mom": [1.28, -0.8], "watch_baby": [1.02, -1.02],
        "watch_baby2": [0.98, -0.62]}  # v2: the youngest beside the mother in the well beat (she hid behind her)
for _i, _k in enumerate(K6):  # where each kid lands when it pops out of the belly
    # v2: every kid hops out to the camera side of the belly, right of the kneeling mother (no flight over her)
    # v3: the first pair flies furthest (front row), the last pair lands nearest the belly: no flight crosses a kid
    TREE[f"pop_{_k}"] = [[1.6, 2.0, 1.75, 2.15, 1.9, 2.3][_i], [-0.45, -0.45, -0.72, -0.72, -1.0, -1.0][_i]]
    # v2 pace: the family stands back by the hedge on the right, a few steps away (not across the road)
    TREE[f"watch_{_k}"] = TREE[f"pop_{_k}"]  # v3: the kids stay where they landed (no run across the meadow)
    # the dance row in front of the well, in the same left-to-right order as they stand (no paths cross)
    # v2: the left end moved right (at x 0.4 / 0.68 two kids stood in the oak's deep shade and read grey)
    TREE[f"dance_{_k}"] = [[0.66, 1.34, 0.88, 1.6, 1.1, 1.86][_i], [-1.65, -1.72, -1.72, -1.65, -1.65, -1.72][_i]]
TREE["dance_mom"] = [1.14, -2.0]
TREE["dance_baby"] = [0.42, -1.08]  # v2: left of the row, off the kids' paths (kid1 crossed in front of her)
SET_B = [
    _e("story_wg_meadow_00", "oak", "oak", 1.0, clear=1.0, yaw=-12.0),
    _e("story_wg_meadow_01", "well", "well", 1.0, clear=0.8),
    _e("story_wg_meadow_02", "well_rim", "well_rim", 1.0, clear=0, stage=0),
    _e("story_wg_meadow_03", "hedge", "hedge", 1.0, clear=0.5),
    _e("story_wg_fx_05", "stones", "stone_a", 1.0, clear=0.2),
    _e("story_wg_fx_07", [TREE["stones"][0] + 0.22, TREE["stones"][1] - 0.02], "stone_b", 1.0, clear=0.1),
    # v2: an open lawn between the camera stations and the oak (a template hill card stood in the tree_two lens)
    _e("meadow_field_25", [1.35, 0.25], "clearing", 0.3, clear=9.0),
]


def _tree(**kw):
    sp = {"seed": 2, "view": 4, "place": "tree", "light": "late", "spots": TREE, "set": SET_B, "focus": "tree_focus"}
    sp.update(kw)
    return sp


# ---------------------------------------------------------------- beats
IN_KIDS = {k: f"in_{k}" for k in KIDS}
BEATS = [
    {"id": "cover", "title": "늑대와 일곱 아기염소", "spread": None, "steps": [{"do": "cover", "prompt": "wg_n01"}]},
    # 1 -- the goats' cottage: mother's warning, she goes out to the meadow
    {"id": "home", "title": "엄마의 당부", "spread": _home(light=""),
     "enter": {"who": {**_all("calm"), "mom": "calm"}, "at": {**IN_KIDS, "mom": "in_mom"}},
     "steps": [
        {"do": "cam", "shot": "establish", "at": "est", "from": "crane_high", "rate": 0.9, "wait": 0.3},
        {"do": "say", "line": "wg_r0100"},
        {"do": "cam", "shot": "room", "at": "in_focus", "rate": 1.2, "wait": 0.3, "settle": 0.7},
        {"do": "fx", "fx": "kids_hop", "wait": 0.6},
        {"do": "tap_steps", "target": "mom", "prompt": "wg_046", "hint": "wg_046", "shot": "room",
         "steps": [{"fx": "mom_warn"}]},
        {"do": "say", "line": "wg_r0103"},
        {"do": "say", "line": "wg_r0104"},
        {"do": "say", "line": "wg_r0105"},
        {"do": "pose", "who": "mom", "pose": "wave"},
        {"do": "go_out", "who": ["mom"], "house": "cottage", "to": "road_door", "shot": "house", "line": "wg_r0106",
         "then": {"to": "road_mid", "exit": True, "speed": 0.75}}]},
    # 2 -- knock knock: the wolf's rough voice; the kids see through it
    {"id": "knock", "title": "똑똑똑!", "spread": _home(light="afternoon"),
     "enter": {"who": {**_all("calm")}, "at": IN_KIDS},
     "steps": [
        {"do": "cam", "shot": "establish", "at": "est", "rate": 1.0, "wait": 0.3},
        {"do": "walk", "who": "wolf", "from": "road_mid", "to": "wolf_door", "via": ["road_door"], "speed": 0.8,
         "follow": "wolf", "shot": "track"},
        {"do": "fx", "fx": "knock", "wait": 0.2},
        {"do": "cam", "shot": "door_ots", "at": "wolf_door", "rate": 1.2, "wait": 0.6, "settle": 0.5},
        {"do": "say", "line": "wg_r0202"},
        {"do": "cam", "shot": "room", "at": "in_focus", "rate": 2.0, "wait": 0.1, "settle": 0.6},
        {"do": "say", "line": "wg_r0205"},
        {"do": "say", "line": "wg_r0206"}]},
    # 3 -- the chalk: up the road to the stall, two crunchy taps, a sweet voice
    {"id": "chalk", "title": "분필과 늑대", "spread": _home(light="afternoon"),
     "enter": {"who": {**_all("calm"), "wolf": "calm"}, "at": {**IN_KIDS, "wolf": "wolf_door"}},
     "steps": [
        {"do": "cam", "shot": "track", "at": "wolf_door", "rate": 1.8, "wait": 0.1, "settle": 0.85},
        {"do": "walk", "who": "wolf", "to": "wolf_stall", "via": ["road_door", "road_mid"], "speed": 0.9,
         "follow": "wolf", "shot": "track"},
        {"do": "pose", "who": "wolf", "pose": "hungry"},
        {"do": "cam", "shot": "stall", "at": ["wolf_stall", "stall"], "rate": 1.6, "wait": 0.1, "settle": 0.3},
        {"do": "say", "line": "wg_r0302"},
        {"do": "tap_steps", "target": "wolf", "prompt": "wg_050", "hint": "wg_050", "shot": "stall",
         "steps": [{"fx": "munch:1", "wait": 0.7}, {"fx": "munch:2", "wait": 0.7}]},
        {"do": "say", "line": "wg_r0303"},
        {"do": "fx", "fx": "voice_ding", "wait": 0.3},
        {"do": "walk", "who": "wolf", "to": "wolf_door", "via": ["road_mid", "road_door"], "speed": 0.9,
         "follow": "wolf", "shot": "track", "line": "wg_r0304"},
        {"do": "pose", "who": "wolf", "pose": "sweet"},
        {"do": "cam", "shot": "door_ots", "at": "wolf_door", "rate": 1.8, "wait": 0.1, "settle": 0.5},
        {"do": "fx", "fx": "knock", "wait": 0.8},
        {"do": "say", "line": "wg_r0306"},
        {"do": "cam", "shot": "room", "at": "in_focus", "rate": 2.0, "wait": 0.1, "settle": 0.6},
        {"do": "say", "line": "wg_r0307"},
        # v8 (CAM_JUMP: every inside -> outside turn through the doorway came out at ~3.0 deg a frame): the dark paw
        # is shown from outside, the wolf holding it up at the door, like the white paw later
        {"do": "fx", "fx": "show_paw", "wait": 0.1},
        {"do": "cam", "shot": "door_low", "at": "wolf_door", "rate": 1.2, "wait": 0.1, "settle": 0.5},
        {"do": "say", "line": "wg_r0308"}]},
    # 4 -- the floury paw: off to the mill over the bridge, a tap on the sack, back to the door, "에취!"
    {"id": "paw", "title": "하얀 발", "spread": _home(light="late"),
     "enter": {"who": {**_all("calm"), "wolf": "calm"}, "at": {**IN_KIDS, "wolf": "wolf_door"}},
     "steps": [
        {"do": "cam", "shot": "track", "at": "wolf_door", "rate": 1.0, "wait": 0.1, "settle": 0.8},
        {"do": "walk", "who": "wolf", "to": "wolf_mill", "via": ["road_door", "road_mill"],
         "speed": 0.7, "pose": "run_cycle", "follow": "wolf", "shot": "track", "line": "wg_r0400"},
        {"do": "pose", "who": "wolf", "pose": "hungry"},
        {"do": "tap_steps", "target": "sack", "shot": "mill", "steps": [{"fx": "flour", "wait": 1.0}]},
        {"do": "walk", "who": "wolf", "to": "wolf_door", "via": ["road_mill", "road_door"],
         "speed": 1.0, "pose": "flour", "follow": "wolf", "shot": "track"},
        # v5 (CAM_JUMP at the 180-degree turns inside / outside): the white paw is shown from outside -- the wolf
        # crouches at the door and slips his floury paw into the gap
        {"do": "pose", "who": "wolf", "pose": "paw_show"},
        {"do": "cam", "shot": "door_low", "at": "wolf_door", "rate": 1.2, "wait": 0.1, "settle": 0.5},
        {"do": "say", "line": "wg_r0402"},
        {"do": "cam", "shot": "door_ots", "at": "wolf_door", "rate": 1.2, "wait": 0.1, "settle": 0.4},
        {"do": "fx", "fx": "sneeze", "wait": 0.1},
        {"do": "say", "line": "wg_r0403"},
        {"do": "cam", "shot": "room", "at": "in_focus", "rate": 2.0, "wait": 0.1, "settle": 0.6},
        {"do": "say", "line": "wg_r0405"}]},
    # 5 -- hide and seek: the wolf bursts in; the kids hide (taps); the youngest into the clock; off-screen gulps
    {"id": "hide", "title": "숨바꼭질", "spread": _home(light="late"),
     "enter": {"who": {**_all("joy", K6), "baby": "calm", "wolf": "search"}, "at": {**IN_KIDS, "wolf": "wolf_step"}},
     "steps": [
        # v2 (audit: the turned-round door shot swung 180 degrees inside, CAM_JUMP, and the glide passed through the
        # side wall; the wolf filled the lens): the kids open the door, the wolf goes in seen from outside, then the
        # camera follows him in through the front wall and the room shows him among the scared kids
        {"do": "cam", "shot": "door_ots", "at": "wolf_door", "rate": 1.6, "wait": 0.1, "settle": 0.5},
        {"do": "go_inside", "who": ["wolf"], "house": "cottage", "house_facing": True, "climb_steps": True,
         "door_clear": True, "to": {"wolf": "in_wolf"}, "speed": 0.65, "keep_open": True},
        {"do": "fx", "fx": "wolf_in", "wait": 0.1},
        {"do": "cam", "shot": "room", "at": "in_focus", "rate": 1.6, "wait": 0.1, "settle": 0.6},
        {"do": "say", "line": "wg_r0500"},
        {"do": "say", "line": "wg_r0501"},
        {"do": "tap_each", "targets": ["bed", "table", "basket"],
         "react": {"bed": ["-", "hide:bed"], "table": ["-", "hide:table"], "basket": ["-", "hide:basket"]}},
        {"do": "tap_steps", "target": "baby", "prompt": "wg_047", "hint": "wg_047", "shot": "room",
         "steps": [{"fx": "clock_hide", "wait": 1.6}]},
        {"do": "walk", "who": "wolf", "to": "in_search", "speed": 0.4, "pose": "flour"},
        {"do": "say", "line": "wg_r0504"},
        {"do": "cam", "shot": "clock_close", "at": "in_clock", "rate": 1.6, "wait": 0.1, "settle": 0.6},
        {"do": "fx", "fx": "swallow", "wait": 0.2},
        {"do": "say", "line": "wg_r0506"},
        # v2 (audit: an 18 s clock close-up while the wolf left off screen): the camera backs out through the front
        # wall to the cottage and the full-bellied wolf waddles out of the open door, down the path and off up the
        # road with the camera following him, under the narrator's reassurance
        {"do": "cam", "shot": "room_wide", "at": "in_focus", "rate": 1.4, "wait": 0.5},
        {"do": "cam", "shot": "house", "at": "door_view", "rate": 0.8, "wait": 0.1, "settle": 0.6},
        {"do": "go_out", "who": ["wolf"], "house": "cottage", "to": "road_door", "pose": "heavy", "shot": "house",
         "keep_open": True, "speed": 0.55, "line": "wg_r0507",
         "then": {"to": "road_far", "exit": True, "speed": 0.75, "follow": "track"}}]},
    # 6 -- the mother comes home: the mess, the call, the youngest out of the clock
    {"id": "mother", "title": "엄마가 왔어요", "spread": _home(light="dusk"),
     "enter": {"who": {}, "at": {}, "state": "mess"},
     "steps": [
        # v2 (audit: she reached a shut door and vanished; 13 s before the first line): she comes home up the road
        # under the narration, the door stands open (the doorway is cut now), she goes in, the camera follows
        {"do": "cam", "shot": "track", "at": "road_mid", "rate": 1.4, "wait": 0.1, "settle": 0.8},
        {"do": "walk", "who": "mom", "from": "road_mid2", "to": "door_view", "via": ["road_mid", "road_door"],
         "speed": 0.85, "follow": "mom", "shot": "track", "line": "wg_r0601"},
        {"do": "cam", "shot": "house", "at": "door_view", "rate": 1.6, "wait": 0.1},
        {"do": "pose", "who": "mom", "pose": "shocked", "wait": 0.2},
        {"do": "go_inside", "who": ["mom"], "house": "cottage", "house_facing": True, "climb_steps": True,
         "door_clear": True, "to": {"mom": "in_mom2"}, "speed": 0.6, "keep_open": True},
        {"do": "cam", "shot": "room_wide", "at": "in_focus", "rate": 1.6, "wait": 0.1, "settle": 0.6},
        {"do": "say", "line": "wg_r0603"},
        {"do": "cam", "shot": "room", "at": ["in_clock", "in_mom2"], "rate": 1.4, "wait": 0.1, "settle": 0.6},
        {"do": "tap_steps", "target": "clock", "shot": "room", "steps": [{"fx": "clock_out", "wait": 0.2}]},
        {"do": "cam", "shot": "room", "at": "in_focus", "rate": 1.2, "wait": 0.1, "settle": 0.5},
        {"do": "say", "line": "wg_r0604"},
        {"do": "say", "line": "wg_r0605"},
        {"do": "say", "line": "wg_r0607"}],
     "kid_voice": "baby"},
    # 7 -- under the oak: the wolf asleep, mother and the youngest tiptoe up
    {"id": "tree", "title": "나무 아래", "spread": _tree(light="late"),
     "enter": {"who": {"wolf": "sleep_full"}, "at": {"wolf": "wolf_sleep"}},
     "steps": [
        {"do": "cam", "shot": "tree_wide", "at": "tree_focus", "from": "crane_high", "rate": 0.9, "wait": 0.6},
        {"do": "fx", "fx": "snore_on", "wait": 0.6},
        {"do": "say", "line": "wg_r0701"},
        {"do": "walk", "who": ["mom", "baby"], "from": "road_bend", "to": {"mom": "mom_near", "baby": "baby_near"},
         "speed": 0.55, "follow": "mom", "shot": "tree_wide"},
        {"do": "pose", "who": "mom", "pose": "shush", "left": 0},
        {"do": "cam", "shot": "tree_two", "at": ["mom_near", "wolf_sleep"], "rate": 1.6, "wait": 0.1, "settle": 0.5},
        {"do": "say", "line": "wg_r0704"},
        ],
     "kid_voice": "baby"},
    # 8 -- the belly: scissors (her body hides it), three taps let the kids out, stones in, stitched shut
    {"id": "belly", "title": "늑대 배", "spread": _tree(light="late"),
     "enter": {"who": {"wolf": "sleep_full", "mom": "shush", "baby": "whisper"},
               "at": {"wolf": "wolf_sleep", "mom": "mom_near", "baby": "baby_near"}},
     "steps": [
        {"do": "walk", "who": ["mom", "baby"], "to": {"mom": "mom_kneel", "baby": "baby_by"}, "speed": 0.32},
        {"do": "pose", "who": "mom", "pose": "kneel_cut", "left": 0},
        {"do": "cam", "shot": "belly", "at": ["belly", "belly", "pop_kid3"], "rate": 1.4, "wait": 0.1, "settle": 0.5},
        {"do": "fx", "fx": "snip", "wait": 0.2},
        {"do": "say", "line": "wg_r0801"},
        {"do": "tap_steps", "target": "belly", "prompt": "wg_049", "hint": "wg_049", "shot": "belly",
         "steps": [{"fx": "belly_pop:1", "wait": 0.6}, {"fx": "belly_pop:2", "wait": 0.6},
                   {"fx": "belly_pop:3", "wait": 0.9}]},
        {"do": "cam", "shot": "pop_wide", "at": ["belly", "pop_kid3"], "rate": 1.6, "wait": 0.1, "settle": 0.5},
        {"do": "say", "line": "wg_r0803"},
        {"do": "pose", "who": "mom", "pose": "ready"},
        {"do": "say", "line": "wg_r0804"},
        {"do": "tap_steps", "target": "stones", "prompt": "wg_051", "hint": "wg_051", "shot": "pop_wide",
         "steps": [{"fx": "stone:1", "wait": 0.8}, {"fx": "stone:2", "wait": 1.0}]},
        {"do": "pose", "who": "mom", "pose": "kneel_sew", "left": 0},
        {"do": "cam", "shot": "belly", "at": "belly", "rate": 1.6, "wait": 0.1, "settle": 0.5},
        {"do": "fx", "fx": "sew", "wait": 0.1},
        {"do": "say", "line": "wg_r0807"},
        {"do": "fx", "fx": "stitched", "wait": 0.6}],
     "kid_voice": "kid3"},
    # 9 -- the well: the family stands back by the hedge; the heavy wolf wakes, waddles to the well, splash, runs away
    {"id": "well", "title": "우물가", "spread": _tree(light="dusk"),
     "enter": {"who": {"wolf": "sleep_stones", **_all("calm"), "mom": "calm"},
               "at": {"wolf": "wolf_sleep", "mom": "mom_kneel", "baby": "baby_by",
                      **{k: f"pop_{k}" for k in K6}}, "state": "stones"},
     "steps": [
        {"do": "cam", "shot": "tree_wide", "at": "tree_focus", "rate": 1.2, "wait": 0.1},
        {"do": "walk", "who": ["mom", "baby"], "to": {"mom": "watch_mom", "baby": "watch_baby2"}, "speed": 0.45},
        {"do": "pose", "who": KIDS, "pose": "scared"},
        {"do": "fx", "fx": "wake", "wait": 0.8},
        {"do": "cam", "shot": "tree_two", "at": ["wolf_sleep", "wolf_sleep", "watch_mom"], "rate": 1.6, "wait": 0.1, "settle": 0.5},
        {"do": "say", "line": "wg_r0902"},
        {"do": "walk", "who": "wolf", "to": "wolf_well", "speed": 0.38, "pose": "heavy", "follow": "wolf",
         "shot": "well_wide"},
        {"do": "pose", "who": "wolf", "pose": "peer_well", "left": 0},
        {"do": "cam", "shot": "well_low", "at": ["wolf_well", "well"], "rate": 1.6, "wait": 0.1, "settle": 0.5},
        {"do": "say", "line": "wg_r0904"},
        {"do": "fx", "fx": "fall_well", "wait": 1.4},
        {"do": "say", "line": "wg_r0906"},
        {"do": "fx", "fx": "wet_out", "wait": 1.0},
        {"do": "cam", "shot": "tree_two", "at": "wolf_wet", "rate": 2.0, "wait": 0.1, "settle": 0.5},
        {"do": "say", "line": "wg_r0907"},
        {"do": "cam", "shot": "well_wide", "at": "road_mid", "rate": 1.4, "wait": 0.1},
        {"do": "walk", "who": "wolf", "to": "road_far", "via": ["road_mid"], "speed": 0.9, "pose": "wet",
         "exit": True, "line": "wg_r0908"}]},
    # 10 -- all together at the well: dance (taps), the end
    {"id": "together", "title": "모두 모였어요", "spread": _tree(light="dusk"),
     "enter": {"who": {**_all("joy", K6), "baby": "calm", "mom": "calm"},
               "at": {**{k: f"watch_{k}" for k in K6}, "baby": "watch_baby2", "mom": "watch_mom"}},
     "steps": [
        # v2 pace: everyone walks to the dance at once (two groups, no paths cross)
        # v2: they dance where they stand on the meadow (the walk to the well left the frame and crossed in the file)
        {"do": "cam", "shot": "pop_wide", "at": ["watch_mom", "pop_kid4"], "rate": 1.2, "wait": 0.1, "settle": 0.6},
        {"do": "fx", "fx": "dance_on", "wait": 0.2},
        {"do": "say", "line": "wg_r1001"},
        {"do": "tap_each", "targets": ["kid2", "kid5", "baby"], "prompt": "wg_044", "hint": "wg_044",
         "react": {"kid2": ["dance"], "kid5": ["dance"], "baby": ["joy_jump"]}},
        {"do": "say", "line": "wg_r1004"},
        {"do": "end", "after": "wg_n02", "close_book": True}]},
]

# ---------------------------------------------------------------- sound
SOUND = {
    "catalog": "res://audio/sound_catalog.json",
    "light_beds": {"": "day", "morning": "day", "afternoon": "afternoon", "late": "late", "dusk": "dusk",
                   "night": "night"},
    "fx": {"kids_hop": "wg.marimba_3", "mom_warn": "ui.pop", "knock": "wg.knock", "munch": "wg.crunch",
           "voice_ding": "wg.ding", "paw_in": "sm.paper_rustle", "flour": "wc.poof", "sneeze": "wc.poof",
           "hide": "sm.scurry", "clock_hide": "wg.ding", "swallow": None, "clock_out": "wg.pop", "snore_on": None,
           "snip": "wg.snip", "belly_pop": "wg.pop", "stone": "wg.stone", "sew": None, "stitched": "wg.ding",
           "wake": "wg.sleepy", "fall_well": "wg.whistle_down", "wet_out": "wg.brass", "dance_on": "wc.sparkle",
           "wolf_in": "wg.door_heavy"},
    "steps": {"cover": {"on_open": {"music": "intro_happiness", "fade": 0.2}}, "page_turn": "paper.page_turn",
              "go_inside": {"door_open": "door.open", "door_shut": "door.shut"},
              "end": {"close_book": "paper.book_close", "music_fade_on_replay": 2.0}},
    "footsteps": {"mom": "pig", "kid1": "pig", "kid2": "pig", "kid3": "pig", "kid4": "pig", "kid5": "pig",
                  "kid6": "pig", "baby": "pig", "wolf": "wolf"},
}
_BEAT_SOUND = {"cover": {"music": None, "bed": None},
               "home": {"music": "home", "bed": "@light", "emitters": ["trees"]},
               "knock": {"music": "wolf", "bed": "@light", "emitters": ["trees"]},
               "chalk": {"music": "wolf", "bed": "@light", "emitters": ["trees"]},
               "paw": {"music": "wolf", "bed": "@light", "emitters": ["trees"]},
               "hide": {"music": "chimney", "bed": "@light"},
               "mother": {"music": "night", "bed": "@light"},
               "tree": {"music": "night", "bed": "@light", "emitters": ["trees"]},
               "belly": {"music": "build", "bed": "@light", "emitters": ["trees"]},
               "well": {"music": "chimney", "bed": "@light", "emitters": ["trees"]},
               "together": {"music": "ending", "bed": "@light", "emitters": ["trees"]}}
for _b in BEATS:
    if _b["id"] in _BEAT_SOUND:
        _b["sound"] = _BEAT_SOUND[_b["id"]]
