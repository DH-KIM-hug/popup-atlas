"""「라푼젤」 (rapunzel) adaptation tables for tools/story/seed_script.py (2026-11-23; plan in artifacts/game-progress.md,
handler game/stories/rapunzel/fx.gd).

Source: 톡톡's rapunzel has the play script (voice_script_el.json: bird / rabbit up-down quiz, long / short ribbon quiz)
and the READ-MODE script (read_script_el.json, scenes R01-R10, every line recorded in read_narration_el.js, all
ElevenLabs: nar Annie, rap Sora, gothel Matilda, father Namchun, mother Bella, prince Klamon; no Typecast roles).
The pop-up book follows the READ script (story first: no quizzes, no counting, no moral) and its softening (톡톡
TALES_PLAN_2.md / the read notes): the prince never jumps or loses his sight; Gothel's magic wind sets him down softly in
the grass; Gothel never shouts. The play script has no tap instructions to borrow (its taps are the quizzes), so the
five tap prompts are new narrator lines (rp_n03..n07, recorded 2026-11-23 with the read script's narrator voice), voiced
once each; the cover / replay prompts are recorded in the same voice (the other tales' clips are another narrator).

Places (page turns only where the place changes):
  home   the parents' cottage, a garden wall with a gate, the witch's rampion garden behind it (seed 5, view 4)
  forest the lone tower in a forest clearing (the building kit's 3D tower, kit preset rapunzel_tower: a slim shaft
         with the round room on top, corbelled out, a real window with a stone sill), the road through the wood and,
         down the road, a small cottage in a field (seed 4, view 0): the tower beats, the room at the top of the tower
         (v2: the camera follows the climber up the braid and dollies in through the window; no page of its own),
         the empty-tower beat and the reunion are camera moves on this one spread
Cut for pace (the picture tells it) or for the tale-not-lesson rule: r0102 r0103 r0105 r0200 r0203 r0205 r0207
r0302-r0305 (r0304 counts the animals) r0400 r0402 r0404-r0406 r0500 r0502 r0504 r0505 r0601 r0603-r0605 r0608 r0700
r0703 r0706-r0709 r0800 r0801 r0804 r0806 r0901 r0904 r0909 r1000-r1003 r1009 r1010 (the moral).
"""
import copy
import json as _json
import math as _m
import os as _os

TALE_ID = "rapunzel"
TITLE = "라푼젤"
PREFIX = "rp"
MORAL = ""  # no moral: the read script's r1010 is not used
READ_SCRIPT = True

CHANGED = {}
SEG_KEEP = {}
READ_SEG_KEEP = {}
NEW_LINES = {
    "rp_n01": [["nar", "그림책을 톡 눌러서 펼쳐 볼까요?", None, "[cheerful, inviting, warm]"]],
    "rp_n02": [["nar", "또 보고 싶으면 '다시 보기'를 톡!", None, "[cheerful, inviting]"]],
    "rp_n03": [["nar", "라푼젤 풀을 톡 눌러서 쑥 뽑아 봐요.", None, "[hushed, playful, inviting]"]],
    "rp_n04": [["nar", "마녀를 톡 눌러서 지팡이를 두드려 봐요.", None, "[warm, a little mysterious, inviting]"]],
    "rp_n05": [["nar", "창문을 톡 눌러서 머리카락을 내려 줘요.", None, "[warm, playful, inviting]"]],
    "rp_n06": [["nar", "라푼젤을 톡 누르면 노래를 불러요.", None, "[warm, gentle, inviting]"]],
    "rp_n07": [["nar", "두 사람을 톡 눌러서 손을 꼭 잡게 해 줘요.", None, "[warm, joyful, inviting]"]],
}
TRIM = {}
# one caption, one voice (ElevenLabs speech-to-text + silencedetect, tools/story/rp_trim.py): the prince's "라푼젤… 어디로
# 갔을까." clip says 라푼젤 five times before the question (11.2 s): 6.70-9.30 s kept; Rapunzel's "어머, 할머니가 아니네?" is
# said twice (5.3 s): the giggle + first take, 0-2.85 s. Nothing recorded.
TRIM_SEG = {"rp_r0907": {0: ("res://audio/voice/rapunzel/prince_8fbc9c7e0b_t.mp3",
                             "audio/el/rapunzel/prince_8fbc9c7e0b.mp3 (6.70-9.30 s: '라푼젤 어디로 갔을까?')")},
            "rp_r0704": {0: ("res://audio/voice/rapunzel/rap_0433eb0505_t.mp3",
                             "audio/el/rapunzel/rap_0433eb0505.mp3 (0-2.85 s: the giggle and the first take)")}}
DROPPED = set()

LINE_META = {k: {} for k in NEW_LINES}
LINE_META.update({
    "rp_r0100": {"expr": {"mother": "calm", "father": "calm"}},
    "rp_r0104": {"expr": {"mother": "longing", "father": "calm"}},
    "rp_r0106": {"expr": {"father": "promise", "mother": "happy"}},
    "rp_r0201": {"expr": {"father": "shock"}},
    "rp_r0202": {"expr": {"gothel": "point", "father": "shock"}},
    "rp_r0204": {"expr": {"gothel": "talk", "father": "sorry"}},
    "rp_r0205": {"expr": {"father": "sorry"}},
    "rp_r0206": {"expr": {"gothel": "cradle", "mother": "sad", "father": "sorry"}},
    "rp_r0300": {"expr": {"gothel": "calm"}},
    "rp_r0401": {"expr": {"gothel": "talk"}},
    "rp_r0503": {"expr": {"rap": "win_smile"}},
    "rp_r0602": {"expr": {"prince": "listen"}},
    "rp_r0606": {"expr": {"gothel": "calm"}},
    "rp_r0607": {"expr": {"gothel": "talk"}},
    "rp_r0609": {"expr": {"prince": "delighted"}},
    "rp_r0701": {"expr": {"prince": "call"}},
    "rp_r0703": {"expr": {"rap": "surprised", "prince": "calm"}},
    "rp_r0704": {"expr": {"rap": "surprised"}},
    "rp_r0705": {"expr": {"prince": "happy", "rap": "joy"}},
    "rp_r0802": {"expr": {"rap": "chatty", "gothel": "calm"}},
    "rp_r0803": {"expr": {"gothel": "cross"}},
    "rp_r0902": {"expr": {"prince": "call"}},
    "rp_r0905": {"expr": {"gothel": "win_stern"}},
    "rp_r0907": {"expr": {"prince": "sad"}},
    "rp_r1004": {"expr": {"prince": "delighted"}},
    "rp_r1005": {"expr": {"rap": "short_joy"}},
    "rp_r1006": {"expr": {"prince": "happy"}},
})

# ---------------------------------------------------------------- stage
HANDLER = "res://stories/rapunzel/fx.gd"
BACKDROP = True
EXTRA = {"ground_style": "paper", "spacing": True, "overlap_check": True, "pop_in": False,
         # intended contacts (reason): climbers hold the braid; the braid hangs against the tower; the prince lands
         # in the soft rose hedge; the two hold hands at the reunion; the father pulls the rampion he stands at;
         # the braid is Rapunzel's own hair (it runs from her head over the sill: v2)
         "overlap_ok": [["gothel", "braid"], ["prince", "braid"], ["braid", "tower"], ["prince", "hedge"],
                        ["rap", "prince"], ["father", "rampion"], ["rap", "tower"], ["gothel", "tower"],
                        ["prince", "tower"], ["rap", "braid"]]}

SHOTS = {"story": [3.0, 12.0, 0.26, 22.0], "close": [2.4, 12.0, 0.28, 20.0],
         "crane_high": [8.5, 34.0, 0.3, 24.0, 0.0],
         # home: the parents' cottage, the wall, the witch's garden
         "h_est": [5.0, 16.0, 0.35, 24.0, 0.0],
         "parents": [1.9, 8.0, 0.26, 26.0, -12.0],
         "garden": [2.4, 16.0, 0.2, 26.0, 8.0],           # over the wall into the garden
         "night_gate": [2.6, 12.0, 0.25, 26.0, -15.0],
         "rampion": [1.4, 12.0, 0.18, 28.0, 10.0],
         "caught": [1.8, 6.0, 0.3, 28.0, 20.0],           # the witch and the father across the bed
         "witch_low": [1.4, 3.0, 0.32, 30.0, -10.0],
         "door": [2.2, 9.0, 0.3, 26.0, -18.0],
         # forest: the tower (window / room shots: SHOTS.update below, from the kit tower's numbers)
         "tower_wide": [8.0, 9.0, 1.7, 28.0, 0.0],
         "tower_low": [4.2, 2.0, 1.25, 44.0, 14.0],        # low at the foot, looking up the wall to the window
         "witch_tap": [1.7, 9.0, 0.3, 26.0, 12.0],
         "braid_fall": [4.4, 3.0, 1.15, 42.0, 14.0],       # the braid running down the whole wall
         "climb": [2.2, 5.0, 0.22, 38.0, 16.0],            # following the climber up the braid
         "foot": [2.2, 9.0, 0.3, 26.0, 10.0],
         "road_in": [2.8, 11.0, 0.3, 24.0, -8.0],
         "hide": [2.6, 10.0, 0.45, 30.0, -20.0],             # the prince by the tree, the tower behind
         "float": [3.0, 6.0, 0.8, 40.0, 6.0],
         "float_hi": [3.0, 6.0, 1.45, 40.0, 6.0],  # v3: where the float starts (3/4 up the braid), then glides down with him   # v3: closer, the floating prince reads (v2: a speck)
         "track": [2.8, 14.0, 0.3, 26.0, 10.0],
         "field": [3.0, 11.0, 0.28, 28.0, 62.0],   # v3: turned off the tower (the cottage is "far away")
         "reunion": [1.7, 7.0, 0.27, 28.0, 45.0],
         "pull_back": [9.5, 26.0, 0.3, 24.0, 0.0]}

ROLES_LABEL = {"rap": "라푼젤", "gothel": "고텔", "prince": "왕자", "father": "아빠", "mother": "엄마"}
CAST = {
    "rap": {"kind": "actor", "skin": "rapunzel", "height": 0.31, "views": ["front", "side", "back"], "label": "라푼젤"},
    "gothel": {"kind": "actor", "skin": "gothel", "height": 0.34, "views": ["front", "side", "back"], "label": "고텔"},
    "prince": {"kind": "actor", "skin": "prince", "height": 0.38, "views": ["front", "side", "back"], "label": "왕자"},
    "father": {"kind": "actor", "skin": "peasant_father", "height": 0.37, "views": ["front", "side", "back"], "label": "아빠"},
    "mother": {"kind": "actor", "skin": "peasant_mother", "height": 0.35, "views": ["front"], "label": "엄마"},
}
UI = {
    "cover": [["cast_rapunzel_calm", 230], ["cast_prince_calm", 250]],
    "end": [["cast_rapunzel_short_happy", 210], ["cast_prince_happy", 250]],
    "speakers": {"rap": ["라푼젤", "c9a227", "cast_rapunzel_calm"], "gothel": ["고텔", "3f6b3a", "cast_gothel_calm"],
                 "prince": ["왕자", "c8322b", "cast_prince_calm"], "father": ["아빠", "7a5230", "cast_peasant_father_calm"],
                 "mother": ["엄마", "c8962a", "cast_peasant_mother_calm"]},
}


def _e(card, at, name, scale=1.0, **kw):
    e = {"card": card, "at": at, "stage": "full", "name": name, "scale": scale, "clear": 0.4}
    e.update(kw)
    return e


def rot(c, dx, dz, yaw):
    """A point dx right / dz in front of c in a piece turned by yaw° (stage frame [right, toward])."""
    t = _m.radians(yaw)
    return [round(c[0] + dx * _m.cos(t) + dz * _m.sin(t), 3), round(c[1] - dx * _m.sin(t) + dz * _m.cos(t), 3)]


# ---------------------------------------------------------------- page 1: home (seed 5, view 4)
# The road (probed: tools/story/probe_spots_wide.gd seed=5 4) runs x 0.3..0.6 from z 0.9 back to -2.4; the open meadow
# left of it holds the parents' cottage (front left, turned toward the road), a low stone wall across the lot with an
# iron gate, and behind it the witch's rampion garden and her crooked cottage.
HOME = {"h_focus": [-1.0, -1.5], "cottage": [-2.35, -1.05], "door": [-2.1, -0.75],
        "mother_at": [-1.38, -0.62], "father_at": [-1.05, -0.7], "parents": [-1.2, -0.66],
        "wall_l": [-1.75, -1.62], "wall_m": [-0.43, -1.62], "gate": [-1.08, -1.62], "gate_in": [-1.08, -1.4],
        "gate_out": [-1.08, -1.9], "bed": [-1.0, -2.35], "rampion": [-0.62, -2.12], "ramp_2": [-1.45, -2.18],
        "ramp_3": [-0.25, -2.4], "pull_at": [-0.78, -2.1], "witch_at": [-0.38, -2.2], "witch_house": [-1.1, -3.25],
        "garden_focus": [-0.8, -2.2], "caught": [-0.58, -2.15], "baby_at": [-0.95, -0.45], "f_back": [-1.68, -0.6],
        "m_door": [-1.35, -0.5], "m_night": [-1.85, -0.78]}
SET_HOME = [
    _e("village_houses_13", "cottage", "cottage", 1.15, yaw=30.0, clear=1.0),
    _e("fairytale_west_11", "wall_l", "wall_l", 1.25, clear=0.3),
    _e("fairytale_west_11", "wall_m", "wall_m", 1.25, clear=0.3),
    _e("fairytale_west_12", "gate", "gate", 0.95, clear=0.3),
    _e("story_rp_garden_02", "bed", "bed", 1.25, clear=0.5),
    _e("story_rp_garden_00", "rampion", "rampion", 1.1, clear=0.15),
    _e("story_rp_garden_01", "ramp_2", "ramp_2", 1.1, clear=0.15),
    _e("story_rp_garden_00", "ramp_3", "ramp_3", 1.0, clear=0.15),
    _e("fairytale_west_06", "witch_house", "witch_house", 1.1, clear=1.0),
]


def _home(**kw):
    sp = {"seed": 5, "view": 4, "place": "home", "light": "", "spots": HOME, "set": SET_HOME, "focus": "h_focus"}
    sp.update(kw)
    return sp


# ---------------------------------------------------------------- page 2: the forest (seed 4, view 0)
# Road (probed seed=4 0): x ~0.4 at z -1.5, x ~1.0 at z -3.0, bending left toward the reader (x -0.6 at z 0.6).
# The tower stands in the clearing left of the road; the hiding tree right of the road; the field cottage down the
# road at the front left (the prince walks out of the wood to it).
# v3: shot yaw θ puts the camera at (sin θ, cos θ)·d in the stage frame [right, toward]: screen right is
# (cos θ, -sin θ). prince_meet = rap_field + 0.27·right(45°) (side by side in the reunion two-shot), field_hear =
# prince_meet + 1.0·right(62°) (his run crosses the field shot sideways); at 62° the tower is ~55° off the axis.
TOWER = [-0.95, -2.25]
TOWER_SCALE = 1.0  # the kit preset is in world units: its top room fits the cast (v2)
KIT = "/Users/house_of_4k2b/orca/popup-atlas/game/art/buildings/kit.json"


def _tower_spec():
    """The kit's rapunzel_tower (a slim shaft, the round room on top corbelled out, a real window in a flat front with
    a stone sill ledge, open: no glass card). Read from the kit at seed time, so kit updates reach the tale on a
    reseed."""
    kit = _json.load(open(KIT))["kit"]
    sp = copy.deepcopy(kit["rapunzel_tower"])
    for p in sp["parts"]:
        for op in p.get("openings", []):
            op.pop("card", None)
            op["open"] = True
    return sp


def _tower_window():
    sp = _json.load(open(KIT))["kit"]["rapunzel_tower"]
    t = [p for p in sp["parts"] if p.get("openings")][0]
    op = t["openings"][0]
    k = TOWER_SCALE
    r, fl, base = t["r"] * k, t.get("flat", 0.0) * k, t.get("base", 0.0) * k
    face = (r * r - (fl * 0.5) ** 2) ** 0.5
    return {"r": r, "face": face, "inner": face - t["thick"] * k, "floor": base, "sill": base + op["y"] * k,
            "top": base + (op["y"] + op["h"]) * k, "w": op["w"] * k, "room_r": r - t["thick"] * k}


WIN = _tower_window()
TX, TZ = TOWER
# the room at the top of the tower: the window on its front (toward the reader), the camera dollies in along the
# window's axis (shots at r_focus: same focus, elevation and height, only the distance changes), the cast stands deep
FH = round(WIN["floor"] + 0.2, 3)  # room focus height (waist height of the cast standing on the room floor)
FOREST = {"tower": TOWER, "f_focus": [-0.6, -1.8],
          "win_foot": [TX, round(TZ + WIN["face"] + 0.14, 3)],   # under the window, in front of the braid
          "climb_at": [TX, round(TZ + WIN["face"] + 0.11, 3)],   # a climber's feet at the braid
          "win_at": [TX, round(TZ + WIN["face"], 3)],            # the window itself
          "r_focus": [TX, TZ - 0.35],
          # the pivot inside: the camera stays near the room's middle (TZ + 0.05), its focus 0.9 ahead in the view
          "pv_front": [TX, TZ - 0.7], "pv_side": [TX - 0.9, TZ + 0.2], "pv_win": [TX, TZ + 1.1],
          "r_rap": [TX + 0.17, TZ - 0.24], "r_prince": [TX - 0.15, TZ - 0.12], "r_gothel": [TX - 0.2, TZ - 0.2],
          "r_two": [TX, TZ - 0.18],
          "gothel_tap": [-0.55, -1.75], "gothel_call": [-0.62, -1.72], "rabbit": [-1.45, -1.75],
          "prince_in": [1.05, -3.3], "prince_mid": [0.45, -2.0], "prince_foot": [-0.5, -1.62],
          "prince_look": [-0.58, -1.6], "tree": [1.8, -2.35], "hide_at": [2.1, -2.1], "gothel_in": [1.0, -3.4],
          "gothel_mid": [0.4, -2.05], "hedge": [-0.3, -1.95], "land": [-0.42, -1.72],
          "road_bend": [0.0, -0.5], "field_in": [-0.45, 0.25], "f_cottage": [-1.75, 0.15], "rap_field": [-1.15, 0.5],
          "prince_meet": [-0.96, 0.31], "field_focus": [-1.0, 0.4], "flowers_1": [-1.5, 0.85], "flowers_2": [-1.95, 0.75],
          "track_mid": [0.2, -1.0], "lawn": [1.6, -1.15], "field_hear": [-0.49, -0.57]}
SET_FOREST = [
    {"build": _tower_spec(), "at": "tower", "name": "tower", "scale": TOWER_SCALE, "stage": 0, "clear": 1.0},
    _e("forest_broadleaf_00", "tree", "tree", 1.0, clear=0.4),
    _e("story_rp_garden_15", "hedge", "hedge", 1.0, clear=0.25),
    _e("farm_animals_16", "rabbit", "rabbit", 1.0, clear=0.15),
    # v3: the field cottage is a lot until the reunion (it pops up there: its thatch filled the corner of every
    # tower wide, and "far away in a field" read as "next to the tower")
    _e("village_houses_20", "f_cottage", "f_cottage", 1.0, yaw=35.0, clear=0.9, stage=0),
    _e("spring_blossom_16", "flowers_1", "flowers_1", 1.0, clear=0.15),
    _e("spring_blossom_07", "flowers_2", "flowers_2", 1.0, clear=0.15),
    # a small primrose patch whose big `clear` opens a lawn between the hiding spot and the "hide" shot's lens
    # (v1 review: template trees filled half the frame on "아, 저렇게 올라가는구나!")
    _e("spring_blossom_16", "lawn", "lawn", 0.8, clear=2.2),
]
SHOTS.update({
    # outside the window and inside the room share one focus (r_focus, deep in the room on the window's axis), one
    # elevation and height: going from one to the other only changes the distance, so the camera dollies straight
    # through the open window
    "window": [1.6, 8.0, FH, 34.0, 0.0],
    "window_side": [1.5, 8.0, round(WIN["sill"] + 0.1, 3), 34.0, 24.0],   # at win_at, a little from the side
    "climb_top": [2.2, 5.0, round(WIN["sill"] - 0.15, 3), 38.0, 16.0],     # at climb_at: the follow let go at the sill
    "room": [0.72, 8.0, FH, 62.0, 0.0],
    "room_snip": [0.78, 15.0, FH, 62.0, 0.0],   # v3: a little higher, so the cut braid on the floor clears the caption
    "room_low": [0.5, 4.0, round(FH - 0.03, 3), 58.0, -14.0],              # at r_rap
    "room_low_g": [0.45, 4.0, FH, 58.0, 10.0],                             # at r_gothel
    "room_two": [0.52, 6.0, FH, 60.0, 12.0],                               # at r_two
    # turning round inside, the camera pivots 0.2 in front of the room's middle, ≥ 0.45 from the cast (each shot's focus 0.9 ahead of it in the view:
    # pv_front / pv_side / pv_win; a turn about one near focus swung the lens through the cast, a 0.1 distance shook
    # with the hand-held drift and pulled the haze into the room): front -> side (the spinning wheel wall) -> the
    # window, with the braid's hook under the sill and the treetops far below
    "pivot": [0.9, 8.0, FH, 56.0, 0.0],
    "pivot_side": [0.9, 8.0, FH, 56.0, 90.0],
    "room_win": [0.9, 10.0, round(WIN["sill"] - 0.03, 3), 60.0, 180.0],
})
# the room's furniture is the handler's (fx.gd: bed, table, stool, spinning wheel, rug on the kit's plank floor)


def _forest(**kw):
    sp = {"built": ["tower"], "seed": 4, "view": 0, "place": "forest", "light": "afternoon", "spots": FOREST, "set": SET_FOREST,
          "focus": "f_focus"}
    sp.update(kw)
    return sp


SKY_NIGHT = {"bg": "#101a3a", "fog": "#24305e", "fog_energy": 0.7, "top": "#0d1636", "horizon": "#34477f",
             "stars": "story_sm_sky_09", "n": 14, "moon": "story_sm_sky_05", "moon_at": [-0.6, 10.5, 2.6, 1.6],
             "far": 17.0}


# ---------------------------------------------------------------- beats
BEATS = [
    {"id": "cover", "title": "라푼젤", "spread": None, "steps": [{"do": "cover", "prompt": "rp_n01"}]},
    # 1 -- the parents by their cottage; the witch's garden over the wall; the mother longs for the rampion
    {"id": "home", "title": "담 너머 텃밭", "spread": _home(light=""),
     "enter": {"who": {"mother": "calm", "father": "calm"}, "at": {"mother": "mother_at", "father": "father_at"}},
     "steps": [
        {"do": "cam", "shot": "h_est", "at": "h_focus", "from": "crane_high", "rate": 0.9, "wait": 0.9},
        {"do": "say", "line": "rp_r0100"},
        {"do": "cam", "shot": "garden", "at": "garden_focus", "rate": 1.2, "wait": 0.3, "settle": 0.6},
        {"do": "fx", "fx": "sparkle:rampion", "wait": 0.1},
        {"do": "say", "line": "rp_r0101"},
        {"do": "cam", "shot": "parents", "at": "parents", "rate": 1.3, "wait": 0.2, "settle": 0.6},
        {"do": "say", "line": "rp_r0104"},
        {"do": "say", "line": "rp_r0106"}]},
    # 2 -- night: the father slips through the gate; the tap pulls the rampion; the witch appears; the bargain
    {"id": "night", "title": "라푼젤 풀", "spread": _home(light="night", sky=SKY_NIGHT),
     "enter": {"who": {"father": "calm"}, "at": {"father": "father_at"},  # v3: the mother is indoors at night (her head filled the lens as the camera followed him)
               "hidden": {"gothel": "witch_at"}},
     "steps": [
        {"do": "cam", "shot": "night_gate", "at": "gate", "rate": 1.0, "wait": 0.4},
        {"do": "fx", "fx": "gate:open", "wait": 0.3},
        {"do": "walk", "who": "father", "via": ["gate_in", "gate_out"], "to": "pull_at", "speed": 0.3,
         "follow": "father", "shot": "night_gate"},
        {"do": "fx", "fx": "gate:close", "wait": 0.1},
        {"do": "cam", "shot": "rampion", "at": ["pull_at", "rampion"], "rate": 1.4, "wait": 0.2, "settle": 0.6},
        {"do": "tap_steps", "target": "rampion", "prompt": "rp_n03", "hint": "rp_n03",
         "steps": [{"fx": "pull_rampion", "wait": 0.6}]},
        {"do": "fx", "fx": "witch_appear", "wait": 0.5},
        {"do": "say", "line": "rp_r0201"},
        {"do": "cam", "shot": "witch_low", "at": "witch_at", "rate": 2.2, "shake": 0.5, "wait": 0.1, "settle": 0.5},
        {"do": "say", "line": "rp_r0202"},
        {"do": "cam", "shot": "caught", "at": ["pull_at", "witch_at"], "rate": 1.5, "wait": 0.1, "settle": 0.5},
        {"do": "say", "line": "rp_r0204"},
        {"do": "pose", "who": "father", "pose": "sorry", "wait": 0.6}]},  # pace: rp_r0205 cut (his bowed head)
    # 3 -- morning: the baby is born; the witch takes her
    {"id": "baby", "title": "아기", "spread": _home(light="late"),
     "enter": {"who": {"mother": "sad", "father": "sorry", "gothel": "cradle"},
               "at": {"mother": "m_door", "father": "f_back", "gothel": "baby_at"}},
     "steps": [
        {"do": "fx", "fx": "sparkle:baby_at", "wait": 0.2},
        {"do": "cam", "shot": "door", "at": ["baby_at", "m_door"], "rate": 1.0, "wait": 0.3, "settle": 0.6},
        {"do": "say", "line": "rp_r0206"},
        {"do": "fx", "fx": "vanish:gothel", "wait": 1.0}]},
    # 4 -- twelve years on: the witch taps her stick, the tower rises in the wood; Rapunzel at the window
    {"id": "tower", "title": "문 없는 탑", "spread": _forest(light="afternoon", built=[]),
     "enter": {"who": {"gothel": "calm"}, "at": {"gothel": "gothel_tap"}},
     "steps": [
        {"do": "cam", "shot": "tower_wide", "at": "tower", "from": "crane_high", "rate": 0.9, "wait": 0.6},
        {"do": "cam", "shot": "witch_tap", "at": ["gothel_tap", "tower"], "rate": 1.3, "wait": 0.2, "settle": 0.6},
        {"do": "say", "line": "rp_r0300"},
        {"do": "tap_steps", "target": "gothel", "prompt": "rp_n04", "hint": "rp_n04",
         "steps": [{"fx": "wand", "wait": 0.4}]},
        {"do": "cam", "shot": "tower_wide", "at": "tower", "rate": 1.4, "wait": 0.1},
        {"do": "fx", "fx": "tower_rise", "wait": 0.4},
        {"do": "say", "line": "rp_r0301"},
        {"do": "fx", "fx": "window:rap:win_smile", "wait": 0.3},
        {"do": "cam", "shot": "window", "at": "r_focus", "rate": 1.3, "wait": 0.2, "settle": 0.6}]},
    # 5 -- 라푼젤, 라푼젤, 머리를 내려 줘! the braid; the witch climbs
    {"id": "hair", "title": "머리를 내려요", "spread": _forest(light="afternoon"),
     "enter": {"who": {"gothel": "talk"}, "at": {"gothel": "gothel_call"}, "rp": {"window": {"rap": "win_smile"}}},
     "steps": [
        {"do": "cam", "shot": "tower_low", "at": ["gothel_call", "tower"], "rate": 1.2, "wait": 0.2, "settle": 0.6},
        {"do": "say", "line": "rp_r0401"},
        {"do": "cam", "shot": "window", "at": "r_focus", "rate": 1.4, "wait": 0.2, "settle": 0.6},
        {"do": "tap_steps", "target": "window", "prompt": "rp_n05", "hint": "rp_n05",
         "steps": [{"fx": "braid:down", "wait": 0.3}]},
        {"do": "cam", "shot": "braid_fall", "at": "win_foot", "rate": 1.2, "wait": 0.1},
        {"do": "say", "line": "rp_r0403"},
        {"do": "walk", "who": "gothel", "to": "climb_at", "speed": 0.2},
        {"do": "cam", "shot": "climb", "at": "climb_at", "rate": 1.2, "wait": 0.1},
        {"do": "climb_braid", "who": "gothel", "speed": 0.3, "cam": "climb"},
        {"do": "fx", "fx": "braid:up", "wait": 0.5}]},
    # 6 -- alone in the tower she sings at the window; the song drifts over the wood
    {"id": "song", "title": "탑 안의 노래", "spread": _forest(light="late"),
     "enter": {"who": {}, "rp": {"window": {"rap": "win_sing"}}},
     "steps": [
        {"do": "cam", "shot": "window_side", "at": "win_at", "rate": 1.0, "wait": 0.3, "settle": 0.6},
        {"do": "say", "line": "rp_r0501"},
        {"do": "tap_steps", "target": "window", "prompt": "rp_n06", "hint": "rp_n06",
         "steps": [{"fx": "notes", "wait": 0.1, "lines": ["rp_x_hum"]}]},
        {"do": "say", "line": "rp_r0503"}]},
    # 7 -- dusk: the prince hears the song; the witch comes, he hides; he sees how she climbs
    {"id": "prince", "title": "노랫소리", "spread": _forest(light="dusk"),
     "enter": {"who": {}, "rp": {"window": {"rap": "win_sing"}}},
     "steps": [
        {"do": "fx", "fx": "notes", "wait": 0.0},
        {"do": "cam", "shot": "road_in", "at": "prince_mid", "rate": 1.0, "wait": 0.2, "settle": 0.9},
        {"do": "walk", "who": "prince", "from": "prince_in", "to": "prince_mid", "speed": 0.3, "follow": "prince",
         "shot": "road_in", "line": "rp_r0600"},
        {"do": "pose", "who": "prince", "pose": "listen", "wait": 0.2},
        {"do": "say", "line": "rp_r0602"},
        {"do": "pose", "who": "prince", "pose": "look_up", "wait": 0.6},
        {"do": "walk", "who": "gothel", "from": "gothel_in", "to": "gothel_mid", "speed": 0.3, "async": True},
        {"do": "walk", "who": "prince", "to": "hide_at", "via": ["prince_mid"], "speed": 0.45, "pose": "run",
         "follow": "prince", "shot": "hide", "line": "rp_r0606"},
        {"do": "pose", "who": "prince", "pose": "hide", "left": 1, "wait": 0.1},
        {"do": "cam", "shot": "foot", "at": "gothel_mid", "rate": 1.4, "wait": 0.2, "settle": 0.8},  # v3: on her before she walks (OFF_FRAME)
        {"do": "walk", "who": "gothel", "to": "gothel_call", "speed": 0.3, "follow": "gothel", "shot": "foot"},
        {"do": "pose", "who": "gothel", "pose": "talk", "wait": 0.1},
        {"do": "cam", "shot": "tower_low", "at": ["gothel_call", "tower"], "rate": 1.2, "wait": 0.1, "settle": 0.5},
        {"do": "say", "line": "rp_r0607"},
        {"do": "fx", "fx": "window:rap:win_letdown", "wait": 0.2},
        {"do": "fx", "fx": "braid:down", "wait": 0.7},
        {"do": "walk", "who": "gothel", "to": "climb_at", "speed": 0.22},
        {"do": "cam", "shot": "climb", "at": "climb_at", "rate": 1.2, "wait": 0.1},
        {"do": "climb_braid", "who": "gothel", "speed": 0.36, "cam": "climb"},  # the second time: brisker
        {"do": "fx", "fx": "braid:up", "wait": 0.4},
        {"do": "cam", "shot": "hide", "at": "hide_at", "rate": 1.3, "wait": 0.1, "settle": 0.5},
        {"do": "pose", "who": "prince", "pose": "delighted", "hop": True, "wait": 0.1},
        {"do": "say", "line": "rp_r0609"}]},
    # 8 -- the next evening the prince calls; the braid; he climbs
    {"id": "climb", "title": "왕자가 올라와요", "spread": _forest(light="dusk"),
     "enter": {"who": {"prince": "call"}, "at": {"prince": "prince_look"}, "rp": {"window": {"rap": "win_smile"}}},
     "steps": [
        {"do": "cam", "shot": "tower_low", "at": ["prince_look", "tower"], "rate": 1.0, "wait": 0.3, "settle": 0.6},
        {"do": "say", "line": "rp_r0701"},
        {"do": "cam", "shot": "window", "at": "r_focus", "rate": 1.4, "wait": 0.2, "settle": 0.6},
        {"do": "tap_steps", "target": "window", "hint": "rp_n05", "steps": [{"fx": "braid:down", "wait": 0.3}]},
        {"do": "cam", "shot": "braid_fall", "at": "win_foot", "rate": 1.2, "wait": 0.6},
        {"do": "walk", "who": "prince", "to": "climb_at", "speed": 0.22},
        {"do": "cam", "shot": "climb", "at": "climb_at", "rate": 1.2, "wait": 0.1},
        {"do": "climb_braid", "who": "prince", "speed": 0.32, "cam": "climb", "line": "rp_r0702", "hold": True}]},
    # 9 -- the room at the top of the same tower: the prince climbs in over the sill, the camera follows him through
    # the window into the round room; Rapunzel's surprise; he asks her to come away (v2: no page turn)
    {"id": "meet", "title": "탑 꼭대기 방", "spread": _forest(light="dusk"),
     "enter": {"who": {"rap": "surprised"}, "at": {"rap": "r_rap"}, "keep": ["prince"],
               "rp": {"room": ["rap"], "braid": "hooked"}},
     "steps": [
        {"do": "cam", "shot": "window", "at": "r_focus", "from": "window", "rate": 1.2, "wait": 0.1, "settle": 0.7},
        {"do": "climb_in", "who": "prince", "to": "r_prince", "pose": "calm"},
        {"do": "cam", "shot": "room", "at": "r_focus", "rate": 0.9, "wait": 0.2, "settle": 0.9},
        {"do": "cam", "shot": "room_low", "at": "r_rap", "rate": 1.4, "wait": 0.1, "settle": 0.5},
        {"do": "say", "line": "rp_r0704"},
        {"do": "cam", "shot": "room_two", "at": "r_two", "rate": 1.3, "wait": 0.1, "settle": 0.5},
        {"do": "say", "line": "rp_r0705"}]},
    # 10 -- one day (the same room): the window from inside, the braid on its hook; the witch, not the prince;
    # "why are you heavier than the prince?" -- the scissors; she is taken far away
    {"id": "snip", "title": "싹둑", "spread": _forest(light="late"),
     "enter": {"who": {"rap": "chatty"}, "at": {"rap": "r_rap"}, "keep": ["prince"],
               "rp": {"room": ["rap"], "braid": "hooked"}},
     "steps": [
        {"do": "cam", "shot": "pivot", "at": "pv_front", "from": "pivot", "rate": 1.0, "wait": 0.0, "settle": 0.6},
        {"do": "cam", "shot": "pivot_side", "at": "pv_side", "rate": 1.0, "wait": 0.0, "settle": 0.6},
        {"do": "cam", "shot": "room_win", "at": "pv_win", "rate": 1.0, "wait": 1.2, "settle": 0.9},
        {"do": "fx", "fx": "room_swap:prince:gothel:r_gothel:calm", "wait": 0.3},
        {"do": "cam", "shot": "pivot_side", "at": "pv_side", "rate": 1.0, "wait": 0.0, "settle": 0.6},
        {"do": "cam", "shot": "pivot", "at": "pv_front", "rate": 1.0, "wait": 0.0, "settle": 0.6},
        {"do": "cam", "shot": "room", "at": "r_focus", "rate": 1.0, "wait": 0.2, "settle": 0.9},
        {"do": "say", "line": "rp_r0802"},
        {"do": "cam", "shot": "room_low_g", "at": "r_gothel", "rate": 1.8, "wait": 0.1, "shake": 0.4, "settle": 0.5},
        {"do": "say", "line": "rp_r0803"},
        {"do": "pose", "who": "gothel", "pose": "scissors", "wait": 0.2},
        {"do": "cam", "shot": "room_snip", "at": "r_focus", "rate": 1.3, "wait": 0.1, "settle": 0.5},
        {"do": "fx", "fx": "snip", "wait": 0.0},
        {"do": "say", "line": "rp_r0805"},
        {"do": "fx", "fx": "vanish:rap", "wait": 0.8},
        {"do": "fx", "fx": "vanish:gothel", "wait": 0.8}]},
    # 11 -- the empty tower: the cut braid on the hook; the witch at the window; the soft magic wind
    {"id": "empty", "title": "빈 탑", "spread": _forest(light="dusk"),
     "enter": {"who": {}, "hidden": {"gothel": "win_foot"}},
     "steps": [
        {"do": "cam", "shot": "window", "at": "r_focus", "rate": 1.0, "wait": 0.1, "settle": 0.9},
        {"do": "cam", "shot": "road_in", "at": "prince_mid", "rate": 1.0, "wait": 0.2, "settle": 0.9},
        {"do": "walk", "who": "prince", "from": "prince_in", "to": "prince_look", "via": ["prince_mid"], "speed": 0.34,
         "follow": "prince", "shot": "foot", "line": "rp_r0900"},
        {"do": "pose", "who": "prince", "pose": "call", "wait": 0.1},
        {"do": "cam", "shot": "tower_low", "at": ["prince_look", "tower"], "rate": 1.2, "wait": 0.1, "settle": 0.5},
        {"do": "say", "line": "rp_r0902"},
        {"do": "fx", "fx": "braid:hook", "wait": 0.2},
        {"do": "cam", "shot": "braid_fall", "at": "win_foot", "rate": 1.2, "wait": 0.1},
        {"do": "say", "line": "rp_r0903"},
        {"do": "walk", "who": "prince", "to": "climb_at", "speed": 0.24},
        {"do": "cam", "shot": "climb", "at": "climb_at", "rate": 1.2, "wait": 0.1},
        {"do": "climb_braid", "who": "prince", "speed": 0.3, "cam": "climb", "stop": 0.75},
        {"do": "fx", "fx": "window:gothel:win_stern", "wait": 0.2},
        {"do": "cam", "shot": "window_side", "at": "win_at", "rate": 1.4, "wait": 0.1, "settle": 0.5},
        {"do": "say", "line": "rp_r0905"},
        {"do": "fx", "fx": "window:gothel:win_wand", "wait": 0.2},
        {"do": "cam", "shot": "float_hi", "at": ["land", "win_foot"], "rate": 1.2, "wait": 0.1, "settle": 0.8},
        {"do": "fx", "fx": "wind_float", "wait": 0.0},
        {"do": "cam", "shot": "float", "at": ["land", "win_foot"], "rate": 0.55, "wait": 0.0},
        {"do": "say", "line": "rp_r0906"},
        {"do": "fx", "fx": "braid:up", "wait": 0.2},
        {"do": "fx", "fx": "window:gothel:", "wait": 0.1},
        {"do": "cam", "shot": "foot", "at": "land", "rate": 1.2, "wait": 0.1, "settle": 0.5},
        {"do": "say", "line": "rp_r0907"},
        {"do": "walk", "who": "prince", "via": ["track_mid", "road_bend"], "to": "field_hear", "speed": 0.42,
         "follow": "prince", "shot": "track", "line": "rp_r0908"}]},
    # 12 -- down the road out of the wood: the song again; the reunion by the little cottage
    {"id": "reunion", "title": "노래를 따라서", "spread": _forest(light="evening"),
     "enter": {"who": {"prince": "sad", "rap": "short_sing"}, "at": {"prince": "field_hear", "rap": "rap_field"},
               "left": {"rap": 0}},
     "steps": [
        {"do": "fx", "fx": "pop:f_cottage", "wait": 0.0},  # v3: the far cottage pops up as the page reaches it
        {"do": "cam", "shot": "field", "at": ["rap_field", "field_hear"], "rate": 1.1, "wait": 0.2, "settle": 0.5},
        {"do": "fx", "fx": "notes:rap", "wait": 0.1},
        {"do": "say", "line": "rp_x_hum"},
        {"do": "pose", "who": "prince", "pose": "delighted", "hop": True, "wait": 0.1},
        {"do": "say", "line": "rp_r1004"},
        {"do": "walk", "who": "prince", "to": "prince_meet", "speed": 0.5, "pose": "run", "follow": "prince",
         "shot": "field"},
        {"do": "pose", "who": "rap", "pose": "short_joy", "hop": True, "wait": 0.1},
        {"do": "cam", "shot": "reunion", "at": ["rap_field", "prince_meet"], "rate": 1.3, "wait": 0.1, "settle": 0.5},
        {"do": "say", "line": "rp_r1005"},
        {"do": "say", "line": "rp_r1006"},
        {"do": "tap_steps", "target": "rap", "prompt": "rp_n07", "hint": "rp_n07",
         "steps": [{"fx": "hold_hands", "wait": 0.6}]},
        {"do": "say", "line": "rp_r1007"},
        {"do": "cam", "shot": "field", "at": "field_focus", "rate": 1.2, "wait": 0.1},
        {"do": "say", "line": "rp_r1008"},
        {"do": "end", "after": "rp_n02", "close_book": True}]},
]
# v3 pace pass (6:35 -> toward 5 min, no line cut): camera glides a little quicker and lines follow sooner;
# walks and climbs at a brisker pace. Opening establishing cranes keep their slow rate.
def _pace(b):
    for k, st in enumerate(b.get("steps", [])):
        d = st.get("do")
        if d == "cam" and not (k == 0 and "from" in st and st.get("from") == "crane_high"):
            if float(st.get("rate", 2.4)) < 2.0:
                st["rate"] = round(min(2.0, float(st["rate"]) * 1.4), 2)
            if "settle" in st:
                st["settle"] = min(float(st["settle"]), 0.45)
            if float(st.get("wait", 0.6)) > 0.3:
                st["wait"] = round(float(st["wait"]) * 0.6, 2)
        elif d == "walk" and "speed" in st and st.get("pose") != "run":
            st["speed"] = round(max(float(st["speed"]), min(0.46, float(st["speed"]) * 1.4)), 2)
        elif d == "climb_braid":
            st["speed"] = round(float(st["speed"]) * 1.45, 2)


for _b in BEATS:
    _pace(_b)
for _b in BEATS:  # every page beat states where everyone stands (`--beat` starts, same-page changes)
    if _b["spread"] is not None:
        _b["enter"].setdefault("keep", [])

# ---------------------------------------------------------------- sound (SoundDirector ids; rp.* copied from 톡톡)
SOUND = {
    "catalog": "res://audio/sound_catalog.json",
    "light_beds": {"": "day", "afternoon": "afternoon", "late": "late", "dusk": "dusk", "night": "night",
                   "evening": "evening"},
    "fx": {"sparkle": "wc.sparkle", "gate": "rp.creak", "pull_rampion": "rp.pull", "witch_appear": "rp.magic",
           "wand": "rp.knock", "tower_rise": "rp.rise", "window": "wc.plop", "braid": "rp.slide",
           "notes": "rp.harp", "in_window": "wc.plop", "snip": "rp.snip", "vanish": "rp.magic",
           "wind_float": "rp.whoosh", "hold_hands": "rp.petals"},
    "steps": {"cover": {"on_open": {"music": "intro_magic", "fade": 0.2}}, "page_turn": "paper.page_turn",
              "end": {"close_book": "paper.book_close", "music_fade_on_replay": 2.0}},
    "footsteps": {"rap": "pig", "gothel": "pig", "prince": "pig", "father": "pig", "mother": "pig"},
}
_BEAT_SOUND = {"cover": {"music": None, "bed": None},
               "home": {"music": "rapunzel", "bed": "@light", "emitters": ["trees"]},
               "night": {"music": "night", "bed": "@light"},
               "baby": {"music": "rapunzel", "bed": "@light"},
               "tower": {"music": "rapunzel", "bed": "@light", "emitters": ["trees"]},
               "hair": {"music": "rapunzel", "bed": "@light", "emitters": ["trees"]},
               "song": {"music": "rp_song", "bed": "@light", "emitters": ["trees"]},
               "prince": {"music": "rapunzel", "bed": "@light", "emitters": ["trees"]},
               "climb": {"music": "rapunzel", "bed": "@light"},
               "meet": {"music": "rapunzel", "bed": "room"},
               "snip": {"music": "night", "bed": "room"},
               "empty": {"music": "night", "bed": "@light"},
               "reunion": {"music": "rp_song", "bed": "@light", "emitters": ["trees"]}}
for _b in BEATS:
    if _b["id"] in _BEAT_SOUND:
        _b["sound"] = _BEAT_SOUND[_b["id"]]
