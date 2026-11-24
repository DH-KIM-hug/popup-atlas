"""「팥죽할멈과 호랑이」 (patjuk) adaptation tables for tools/story/seed_script.py (plan: artifacts/game-progress.md
2026-11-23 patjuk entry; handler game/stories/patjuk/fx.gd).

Source: 톡톡's patjuk has the play script (voice_script_el.json: friends tapped in order, wrong-pick lines, "who is
hiding in ...?" quizzes) and the READ-MODE script (read_script_el.json, scenes R01-R10, recorded in
read_narration_el.js). The pop-up book follows the READ script (story first: no quizzes, no counting, no moral) and
borrows only the play script's first trap instruction ("알밤을 눌러 봐요!", pj_037), voiced once.

Softening as in the read script (톡톡 TALES_PLAN_2.md): the tiger is never hurt on screen (slapstick: a hot chestnut in
the eye, a nip, a slip, a poke, a bump), the carrier takes him off the page; the splash is far away at sea and he swims
off, a small sorry head on the waves.

Voices: nar (Lily) and tiger (Brian) are ElevenLabs; the granny and the seven helpers are Typecast clips (톡톡 voices
"tc"), so no new granny / helper lines can be made: every new line is the narrator's.

Places (page turns only where the place changes): the red-bean field (sunmoon's mountain road, view 4) and the
granny's cottage in winter (sunmoon's cottage spread, view 0): kitchen inside, yard in front, the sea beyond; the
camera moves between them on one spread.
"""
import copy
import math as _m

from tales import sunmoon as SM

TALE_ID = "patjuk"
TITLE = "팥죽할멈과 호랑이"
PREFIX = "pj"
MORAL = ""  # no moral: the read script's closing moral pj_r1005 is not used
READ_SCRIPT = True

# ---------------------------------------------------------------- line adaptations
CHANGED = {}
SEG_KEEP = {}
# read lines trimmed to some of their segs (clips reused, nothing to record): narrator tags the picture tells
READ_SEG_KEEP = {
    "pj_r0703": [0],   # the granny's "호랑아, 팥죽 먹기 전에 아궁이 불 좀 봐주렴." (he crouches at the fire on screen)
    "pj_r0801": [0],   # the tiger's "아야야!" (the back-step shows)
    "pj_r0805": [0],   # the tiger's "엉엉, 아파!" (he runs for the door on screen)
}
NEW_LINES = {
    # the narrator is the same ElevenLabs voice as witch_candy / wolf_goats (pFZP5JQG7iQjIQuC4Bku): their recorded
    # cover / replay clips (same text) are reused (game/audio/voice/patjuk/recorded.json)
    "pj_n01": [["nar", "그림책을 톡 눌러서 펼쳐 볼까요?", None, "[cheerful, inviting, warm, cosy Halloween night]"]],
    "pj_n02": [["nar", "또 보고 싶으면 '다시 보기'를 톡!", None, "[cheerful, inviting]"]],
    # first-tap instructions (voiced once; later taps of the kind show only the ring): recorded 2026-11-23 (approved)
    "pj_n03": [["nar", "할멈을 톡톡 눌러서 콕콕 김을 매 봐요!", None, "[warm, playful, inviting]"]],
    "pj_n04": [["nar", "가마솥을 톡 눌러서 팥죽을 한 그릇 건네요.", None, "[warm, playful, inviting]"]],
}
TRIM = {}
TRIM_SEG = {}
DROPPED = set()

HELP = ["bam", "jara", "ddong", "songgot", "jeolgu", "myeongseok", "jige"]
LINE_META = {
    "pj_n01": {}, "pj_n02": {}, "pj_n03": {}, "pj_n04": {},
    "pj_r0100": {"expr": {"halmi": "hoe_up"}},
    "pj_r0101": {"expr": {"halmi": "calm"}},
    "pj_r0102": {"expr": {"halmi": "hoe_up"}},
    "pj_r0201": {"expr": {"halmi": "scared", "tiger": ["roar", "demand"]}},
    "pj_r0202": {"expr": {"halmi": "scared"}},
    "pj_r0204": {"expr": {"halmi": ["plead", "sad"], "tiger": ["sly", "sly"]}},
    "pj_r0205": {"expr": {"halmi": "look_far"}},
    "pj_r0301": {"expr": {"halmi": "cry_stir"}},
    "pj_r0304": {"expr": {"halmi": "sad"}},
    "pj_r0400": {"expr": {"halmi": "calm"}},
    "pj_r0401": {"expr": {"halmi": "calm", "bam": ["calm", "act", "calm"]}},
    "pj_r0402": {"expr": {"halmi": "calm"}},
    "pj_r0501": {"expr": {"halmi": "calm"}},
    "pj_r0502": {"expr": {"halmi": "calm"}},
    "pj_r0503": {"expr": {"halmi": "calm"}},
    "pj_r0601": {"expr": {"halmi": "calm"}},
    "pj_r0604": {"expr": {"halmi": "whisper"}},
    "pj_r0605": {"expr": {"halmi": "whisper"}},
    "pj_r0606": {"expr": {"halmi": "whisper"}},
    "pj_r0701": {"expr": {"tiger": "roar"}},
    "pj_r0702": {"expr": {"tiger": "demand"}},
    "pj_r0703": {"expr": {"halmi": "call", "tiger": "sly"}},
    "pj_r0706": {"expr": {"tiger": ["eye_hurt", "eye_hurt"]}},
    "pj_r0707": {"expr": {"halmi": "hide"}},
    "pj_r0801": {"expr": {"tiger": "mouth_ouch"}},
    "pj_r0805": {"expr": {"tiger": "poked"}},
    "pj_r0806": {"expr": {"halmi": "hide"}},
    "pj_r0807": {"expr": {"tiger": "dazed"}},
    "pj_r0900": {"expr": {"tiger": "flat_bump"}},
    "pj_r0903": {"expr": {"tiger": "rolled_cry"}},
    "pj_r1001": {"expr": {"halmi": "cheer"}},
    "pj_r1002": {"expr": {"halmi": "hug"}},
    "pj_r1003": {"expr": {"halmi": "hug"}},
}

# ---------------------------------------------------------------- stage
HANDLER = "res://stories/patjuk/fx.gd"
BACKDROP = True
INSIDE_FRAMING = "manual"
EXTRA = {"theme": "korean", "ground_style": "paper", "inside_margin": 0.8,
         "spacing": True, "overlap_check": True, "pop_in": False,
         # intended contacts: the turtle biting the tiger's lip at the jar, the dung under his feet as he slips, the
         # awl under his bottom, the mortar landing on his head, the mat rolled round him, the carrier with him on its
         # back, the carrier leaning on the yard wall, the granny standing at her hearth / jar while she works
         "overlap_ok": [["tiger", "boulder"], ["tiger", "bam"], ["tiger", "jara"], ["tiger", "ddong"], ["tiger", "songgot"], ["tiger", "jeolgu"],
                        ["tiger", "myeongseok"], ["tiger", "jige"], ["jige", "wall_r"], ["tiger", "hearth"],
                        ["tiger", "muldok"], ["halmi", "hearth"], ["bam", "hearth"], ["jara", "muldok"],
                        ["songgot", "crack"], ["ddong", "kfloor"],
                        # wave 2: hiding places in plain sight: the dung lies flat on the floor behind the hearth, the
                        # mortar over the door behind the mat / carrier in low yard shots
                        ["ddong", "hearth"], ["jeolgu", "myeongseok"], ["jeolgu", "jige"]]}

SHOTS = copy.deepcopy(SM.SHOTS)
SHOTS.update({
    "field_est": [5.2, 20.0, 0.3, 24.0, 14.0],      # the bean field beside the mountain road, the ridges behind
    "field_med": [2.2, 9.0, 0.22, 24.0, 18.0],
    "field_low": [1.5, 4.0, 0.28, 30.0, -20.0],     # low: the tiger looming out from the boulder
    "field_two": [1.9, 10.0, 0.26, 26.0, 30.0],
    "hoe": [1.2, 16.0, 0.16, 26.0, 10.0],           # the hoe taps: granny and the bean rows big
    "road_up": [3.0, 14.0, 0.3, 26.0, 0.0],         # the tiger walking off up the mountain road
    "snow_est": [5.5, 22.0, 0.35, 26.0, -18.0],      # the cottage in winter, from the road
    # inside the kitchen (the cottage frame turned COT_YAW): the camera just behind the hidden front wall
    # wave 2 (gate audit v1: "the tiger is too close in the kitchen", heads cut off): the 0.57-tall tiger stands
    # ~0.6 from a camera that must stay behind the front wall, so the kitchen shots are wide lenses aimed from just
    # inside the front wall at the back wall, focus at the tiger's middle (his whole figure in frame)
    "kitchen": [0.8, 16.0, 0.27, 72.0, -40.0],
    "kitchen_low": [0.78, 8.0, 0.33, 72.0, -40.0],    # at k_low_l / k_low_r (deep spots: the camera stays inside)
    # the helpers come in on the floor: looking down from just inside the front wall, the floor mid-frame (they used
    # to arrive along the bottom edge under the caption)
    "kitchen_help": [0.74, 30.0, 0.12, 70.0, -40.0],
    "kitchen_floor": [0.8, 28.0, 0.24, 76.0, -40.0],  # the tiger and the floor traps (dung, crack) together
    # turned round: the door with the tiger AND the lintel above it (the mortar's drop), a wide lens
    "kitchen_door": [0.72, 6.0, 0.38, 78.0, 140.0],
    "door_drop": [1.35, 5.0, 0.36, 38.0, -40.0],     # outside: the open door, the lintel, the tiger bursting out
    "kitchen_side": [0.85, 10.0, 0.24, 60.0, 50.0],  # from the right side of the kitchen: the door AND the hearth
    "yard": [2.2, 14.0, 0.25, 30.0, -40.0],          # the yard in front of the cottage, facing the house
    "yard_wide": [3.6, 20.0, 0.3, 28.0, -30.0],
    "yard_low": [1.5, 6.0, 0.22, 32.0, -22.0],   # wave 2: from the right, the low yard wall no longer in front of her
    "night_arrive": [3.2, 32.0, 0.3, 30.0, -30.0],  # the tiger's night walk to the door seen from above the pines
    "carry": [1.7, 16.0, 0.25, 38.0, -85.0],
    # the throw and the swim from the yard side (the old sea shot looked from far round the corner; the glide back
    # to the yard for the feast swung over the page as a high flat view)
    "sea_view": [1.9, 13.0, 0.22, 36.0, -80.0],          # tracking the carrier from the yard to the shore
    "sea": [2.1, 12.0, 0.22, 36.0, -130.0],            # over the cottage roof to the sea behind it
    "pull_back": [10.5, 26.0, 0.3, 24.0, -30.0],
})

ROLES_LABEL = {"halmi": "할멈", "tiger": "호랑이", "bam": "알밤", "jara": "자라", "ddong": "쇠똥", "songgot": "송곳",
               "jeolgu": "절구", "myeongseok": "멍석", "jige": "지게"}
CAST = {
    "halmi": {"kind": "actor", "skin": "hanbok_granny", "views": ["front", "side", "back"], "label": "할멈 (granny)"},
    "tiger": {"kind": "actor", "skin": "tiger", "views": ["front", "side", "back"], "label": "호랑이 (tiger)"},
}
for _h in HELP:
    CAST[_h] = {"kind": "actor", "skin": "pj_" + _h, "views": ["front"], "label": ROLES_LABEL[_h]}
UI = {
    "cover": [["cast_hanbok_granny_calm", 170], ["cast_tiger_sly", 260]],
    "end": [["cast_hanbok_granny_cheer", 200], ["cast_pj_bam_calm", 80], ["cast_pj_jara_calm", 90]],
    "speakers": {"halmi": ["할멈", "3a4f9a", "cast_hanbok_granny_calm"], "halmi": ["할멈", "3a4f9a", "cast_hanbok_granny_calm"],
                 "tiger": ["호랑이", "e08a1e", "cast_tiger_calm"],
                 **{h: [ROLES_LABEL[h], "8a5a2e", f"cast_pj_{h}_calm"] for h in HELP}},
}
# the granny's role is "halmi", the voice script's speaker key (the stage finds a speaker's actor by that name)

spot, rot = SM.spot, SM.rot


def _e(card, at, name, scale=1.0, **kw):
    e = {"card": card, "at": at, "stage": "full", "name": name, "scale": scale, "clear": 0.6}
    e.update(kw)
    return e


# ---------------------------------------------------------------- spread A: the red-bean field (view 4, mountain road)
# Where sunmoon's rich house stood (beside the road below the first pass): a patch of bean bushes right of the road,
# a mossy boulder left of it (the tiger steps out from behind it), the pass ridges behind; the tiger leaves up the road.
Z0 = 0.9


def _rs(z, side=0.0):
    return spot(4, SM.road_x(z) + side, z)


FIELD = {"field": _rs(Z0, 0.85), "granny_at": _rs(Z0 + 0.05, 0.62), "hoe_at": _rs(Z0 + 0.12, 0.5),
         "boulder": _rs(Z0 - 0.35, -0.7), "tiger_at": _rs(Z0 - 0.2, -0.12), "tiger_out": _rs(Z0 - 0.75, 0.0),
         "road_away": _rs(-2.2, 0.0), "est": _rs(Z0 - 0.4, 0.25), "two": _rs(Z0 - 0.05, 0.25)}
SET_F = []
for k, (dz, side, card) in enumerate([(0.35, 0.95, "story_pj_field_00"), (-0.1, 1.05, "story_pj_field_01"),
                                       (0.55, 0.45, "story_pj_field_02"), (-0.3, 0.55, "story_pj_field_00"),
                                       (0.15, 1.35, "story_pj_field_02"), (-0.45, 1.25, "story_pj_field_01")]):
    FIELD[f"bean_{k}"] = _rs(Z0 + dz, side)
    SET_F.append(_e(card, f"bean_{k}", f"bean_{k}", clear=0.3))
FIELD["bean_band"] = _rs(Z0 - 0.75, 1.0)
FIELD["basket"] = _rs(Z0 + 0.3, 0.62)
SET_F += [_e("story_pj_field_03", "bean_band", "bean_band", clear=0.3),
          _e("story_pj_field_05", "basket", "basket", clear=0.15),
          _e("story_sm_mountain_04", "boulder", "boulder", clear=0.4)]
for nm in ["ridge_1_l", "ridge_1_r", "ridge_2_l", "ridge_2_r", "saddle", "far_ridge", "grass_1"]:
    FIELD[nm] = SM.ROAD_A[nm]
    SET_F += [e for e in SM.SET_A if e["name"] == nm]


def _field(**kw):
    sp = {"seed": 1, "view": 4, "place": "field", "light": "afternoon", "spots": FIELD, "set": SET_F, "focus": "est"}
    sp.update(kw)
    return sp


# ---------------------------------------------------------------- spread B: the cottage in winter (view 0)
# sunmoon's thatched cottage (body, door swinging in) with its room made the KITCHEN: the earthen back wall with the
# shelf, the clay hearth with the cauldron (left), the open water jar (right), an earthen floor; the yard in front
# (a stone-and-clay wall either side of the path), the sea beyond the house (the carrier takes the tiger there).
COT_YAW, COT = SM.COT_YAW, SM.COT
# r2 (first full run): the tiger (0.57 tall) did not fit sunmoon's room (0.62 deep, the camera 0.4 from the back
# wall); the cottage stands 1.3x (front line where it was, the body 0.95 deep), so the kitchen shots stand back far
# enough. Offsets in the cottage frame [right, toward]: inside z 0 (front wall) .. -0.95 (back wall).
S = 1.3
DX = -0.22 * S  # the door's x
HOME = {"road_by": SM.HOME["road_by"]}
for nm, (dx, dz) in {
        # the house, its door and path (the yard side keeps sunmoon's distances)
        "cottage": (0.0, 0.0), "door": (DX, 0.32), "door_in": (DX, -0.2), "step": (DX, 0.12), "path_end": (DX, 1.05),
        "wall_in": (0.0, -0.014), "front_focus": (-0.1, 0.6), "est": (0.1, -0.2), "door_out": (DX, 0.62),
        "jars": (-1.3, -0.85), "firewood": (1.2, -0.35), "fence_1": (-1.4, -1.6),
        # the kitchen
        "k_back": (0.0, -0.9), "k_floor": (0.0, -0.25), "k_floor2": (0.0, -0.7), "hearth": (-0.45, -0.8),
        "fire": (-0.45, -0.66), "jara_rim": (0.45, -0.66), "cauldron": (-0.45, -0.75), "muldok": (0.5, -0.78), "crack": (-0.26, -0.45),
        "k_focus": (0.0, -0.85), "k_low_l": (-0.3, -0.88), "k_low_r": (0.3, -0.88), "k_wood": (-0.8, -0.6), "k_basket": (-0.8, -0.3), "k_left": (-0.4, -0.5),
        "door_view": (-0.2, -0.12), "k_mid_r": (0.32, -0.38),
        "granny_k": (0.15, -0.8), "jeolgu_land": (DX + 0.3, 0.5), "granny_door": (-0.02, -0.28), "corner": (0.78, -0.7),
        "tiger_fire": (-0.16, -0.72), "tiger_jar": (0.24, -0.72), "dung": (-0.02, -0.55),
        "tiger_door": (DX, -0.14), "bam_k": (-0.6, -0.42), "granny_wait": (0.32, -0.55), "help_loop": (-0.08, -0.74), "jara_k": (0.26, -0.48), "help_in": (-0.05, -0.62),
        # wave 2: the mortar hides OUTSIDE over the door (it hops out of the open door and up), so its drop on the
        # tiger's head is shot from the yard as he bursts out (the inside of the front wall was a flat card with a
        # white base strip and the outer door's reveal lines showing through: "the mortar-climax wall frame")
        "lintel": (DX, 0.07),
        # the yard (in front of the house)
        "yard_c": (-0.08, 0.98), "y_granny": (-0.5, 0.55), "y_mat": (0.32, 0.66), "y_jige": (0.98, 0.55), "y_jige_via": (0.15, 0.38),
        "wall_l": (-0.78, 1.02), "wall_r": (0.6, 1.2), "y_tiger": (0.0, 0.8), "y_help_in": (DX, 1.35),
        "gate": (DX, 1.25), "y_focus": (0.0, 0.7), "y_feast": (0.12, 0.68), "y_out": (1.9, 1.3), "shore": (2.95, 0.6),
        "sea": (3.4, -0.4), "sea_splash": (3.2, -0.35), "snow_1": (-1.25, 0.55), "snow_2": (1.15, 0.45),
        "snow_3": (1.4, -1.2), "snow_4": (1.0, 1.55), "snow_5": (-1.45, -0.4), "stack": (1.35, 0.05)}.items():
    HOME[nm] = rot(COT, dx, dz, COT_YAW)
for k in range(4):
    HOME[f"cot_st{k}"] = rot(COT, DX, 0.42 + 0.15 * k, COT_YAW)

_cot = copy.deepcopy(next(e for e in SM.SET_B if e["name"] == "cottage"))
_cot.update({"scale": S, "box": {"depth": 0.95, "body": True}})
SET_H = [_cot,
         {"card": "story_sm_cottage_in_00", "at": "wall_in", "stage": "full", "name": "wall_in", "scale": S, "clear": 0,
          "yaw": COT_YAW + 180.0, "inside_only": True},
         _e("story_sm_yard_02", "jars", "jars", yaw=COT_YAW, clear=0.5),
         _e("story_sm_yard_07", "firewood", "firewood", yaw=COT_YAW, clear=0.3),
         _e("story_sm_yard_06", "fence_1", "fence_1", yaw=COT_YAW + 70.0, clear=0.3)]
for k in range(4):
    SET_H.append({"card": ["stream_water_21", "stream_water_22"][k % 2], "at": f"cot_st{k}", "stage": "full",
                  "name": f"cot_st{k}", "scale": 0.5, "clear": 0.08, "yaw": COT_YAW})
SET_H += [
    {"card": "story_pj_kitchen_00", "at": "k_back", "stage": "full", "name": "k_back", "scale": 1.35, "clear": 0,
     "yaw": COT_YAW},
    {"card": "story_pj_kitchen_05", "at": "k_floor", "stage": "full", "name": "kfloor", "scale": 1.4, "clear": 0,
     "yaw": COT_YAW, "flat": True, "lift": 0.021},
    {"card": "story_pj_kitchen_05", "at": "k_floor2", "stage": "full", "name": "kfloor2", "scale": 1.4, "clear": 0,
     "yaw": COT_YAW, "flat": True, "lift": 0.022},
    {"card": "story_pj_kitchen_02", "at": "hearth", "stage": "full", "name": "hearth", "scale": 1.3, "clear": 0,
     "yaw": COT_YAW, "light": [0.3, 0.3, 1.0, "#ff9a40", True]},
    {"card": "story_pj_kitchen_04", "at": "muldok", "stage": "full", "name": "muldok", "scale": 1.3, "clear": 0,
     "yaw": COT_YAW},
    {"card": "story_pj_kitchen_06", "at": "crack", "stage": "full", "name": "crack", "scale": 1.3, "clear": 0,
     "yaw": COT_YAW, "flat": True, "lift": 0.024},
    {"card": "story_sm_yard_07", "at": "k_wood", "stage": "full", "name": "k_wood", "scale": 0.9, "clear": 0,
     "yaw": COT_YAW + 90.0},
    {"card": "story_pj_field_05", "at": "k_basket", "stage": "full", "name": "k_basket", "scale": 1.2, "clear": 0,
     "yaw": COT_YAW + 90.0},
    _e("story_pj_yard_00", "wall_l", "wall_l", scale=0.8, yaw=COT_YAW, clear=0.4),
    _e("story_pj_yard_01", "wall_r", "wall_r", yaw=COT_YAW, clear=0.4),
    _e("story_pj_yard_02", "sea", "sea", scale=3.2, yaw=COT_YAW - 90.0, clear=1.6, allow_road=True),
]
for k, (nm, card) in enumerate([("snow_1", "story_pj_yard_06"), ("snow_2", "story_pj_yard_07"),
                                 ("snow_3", "story_pj_yard_07"), ("snow_4", "story_pj_yard_06"),
                                 ("snow_5", "story_pj_yard_06"), ("stack", "story_pj_yard_08")]):
    SET_H.append(_e(card, nm, nm, yaw=COT_YAW, clear=0.2))


def _home(**kw):
    sp = {"seed": 1, "view": 0, "place": "home", "light": "dusk", "spots": HOME, "set": SET_H, "focus": "front_focus",
          "sky": None}
    sp.update(kw)
    if sp.get("sky") is None:
        sp.pop("sky")
    return sp


SKY_NIGHT = SM.SKY_NIGHT
KITCHEN_HELP = ["bam", "jara", "ddong", "songgot", "jeolgu"]
HIDE = {"bam": "fire", "jara": "muldok", "ddong": "dung", "songgot": "crack", "jeolgu": "lintel"}


def helper(h, line, first=False, yard=False):
    """A helper's moment: in at the door (or the yard gate) during the narration, its quote, a tap on the cauldron
    (the granny's bowl in the yard) sends a bowl of porridge, then it goes to its hiding place under the last seg."""
    tap = {"do": "tap_steps", "target": "cauldron", "steps": [{"fx": f"give:{h}", "wait": 0.7}]}
    if yard:  # pace: in the yard the granny hands the bowl herself (no tap)
        tap = {"do": "fx", "fx": f"give:{h}", "wait": 0.8}
    if first:
        tap.update({"prompt": "pj_n04", "hint": "pj_n04"})
    cam = []  # r5: one wide kitchen shot for all (the side shot was a blank wall; inside, the door card stays shut)
    if h == "jeolgu":  # wave 2: it thumps out of the door and up over it: the camera goes out to the yard to see it
        # (turning round inside showed the inside of the front wall as a bare card; the glide out facing the back
        # wall is clean, and the yard beat then starts outside)
        cam = [{"do": "cam", "shot": "door_drop", "at": ["door_out", "lintel"], "rate": 1.0, "wait": 0.0}]
    back = []
    return [{"do": "fx", "fx": f"arrive:{h}", "wait": 0.0 if yard else 0.3},
            {"do": "say", "line": line, "segs": [0, 1]},
            tap,
            *cam,
            {"do": "fx", "fx": f"hide:{h}", "wait": 0.0},
            {"do": "say", "line": line, "segs": [2]},
            *back]


# ---------------------------------------------------------------- beats
BEATS = [
    {"id": "cover", "title": "팥죽할멈과 호랑이", "spread": None, "steps": [{"do": "cover", "prompt": "pj_n01"}]},
    # 1 -- the red-bean field: the granny weeding, the tiger, the promise
    {"id": "field", "title": "팥밭", "spread": _field(light="afternoon"),
     "enter": {"who": {"halmi": "hoe_up"}, "at": {"halmi": "granny_at"}, "hidden": {"tiger": "boulder"}},
     "steps": [
        {"do": "cam", "shot": "field_est", "at": "est", "from": "crane_high", "rate": 0.9, "wait": 0.9},
        {"do": "say", "line": "pj_r0100"},
        {"do": "cam", "shot": "field_med", "at": "field", "rate": 1.4, "wait": 0.6},  # pace: pj_r0101 cut (the field shows)
        {"do": "cam", "shot": "hoe", "at": "granny_at", "rate": 1.6, "wait": 0.2, "settle": 0.6},
        {"do": "tap_steps", "target": "halmi", "prompt": "pj_n03", "hint": "pj_n03",
         "steps": [{"fx": "hoe:1", "wait": 0.3}, {"fx": "hoe:2", "wait": 0.3}, {"fx": "hoe:3", "wait": 0.3}]},
        # pace: pj_r0102 cut (the three hoe taps are the weeding)
        {"do": "cam", "shot": "field_low", "at": "tiger_at", "rate": 3.0, "wait": 0.1, "settle": 0.7},
        {"do": "fx", "fx": "tiger_out:boulder:tiger_at", "wait": 0.1},
        {"do": "cam", "shot": "field_low", "at": "tiger_at", "rate": 3.0, "shake": 0.6, "wait": 0.1},
        {"do": "say", "line": "pj_r0201"},
        {"do": "fx", "fx": "hoe_drop", "wait": 0.1},
        {"do": "cam", "shot": "field_two", "at": ["granny_at", "tiger_at"], "rate": 2.0, "wait": 0.1, "settle": 0.5},
        {"do": "fx", "fx": "shiver:3.0", "wait": 0.0},
        {"do": "say", "line": "pj_r0202"},
        {"do": "say", "line": "pj_r0204", "segs": [0]},
        {"do": "walk", "who": "tiger", "to": "road_away", "dir": "away", "speed": 0.45, "follow": "tiger",
         "shot": "road_up", "line": "pj_r0204", "segs": [1], "exit": True,
         # wave 2: the camera lets him go up the road and turns back to the granny looking after him (the follow
         # ended on an empty road and his exit pop showed)
         "follow_for": 5.2, "release_shot": "field_two", "release_at": "granny_at"},
        {"do": "pose", "who": "halmi", "pose": "look_far", "wait": 0.8}]},  # pace: pj_r0205 cut (she looks after him)
    # 2 -- winter: the cottage under snow, the kitchen, the granny crying over the porridge
    {"id": "winter", "title": "동짓날", "spread": _home(light="dusk"),
     "enter": {"who": {"halmi": "cry_stir"}, "at": {"halmi": "granny_k"}},
     "steps": [
        {"do": "fx", "fx": "snow:on", "wait": 0.0},
        {"do": "cam", "shot": "snow_est", "at": "est", "from": "crane_high", "rate": 0.9, "wait": 0.6},
        {"do": "say", "line": "pj_r0300"},
        {"do": "cam", "shot": "kitchen", "at": "k_focus", "rate": 1.1, "wait": 0.3, "settle": 0.7},
        {"do": "fx", "fx": "steam:on", "wait": 0.0},
        {"do": "say", "line": "pj_r0301"},
        {"do": "cam", "shot": "kitchen_low", "at": "k_low_l", "rate": 1.8, "wait": 0.1},
        {"do": "say", "line": "pj_r0304"}]},
    # 3 -- the helpers come to the kitchen door one by one; a bowl of porridge each; each hides in its place
    {"id": "helpers", "title": "작은 친구들", "spread": _home(light="dusk"),
     "enter": {"who": {"halmi": "calm"}, "at": {"halmi": "granny_k"}, "keep": ["halmi"]},
     "steps": [
        {"do": "fx", "fx": "knock", "wait": 0.6},
        # pace: pj_r0400 cut (the knock is heard, she turns to the door)
        {"do": "pose", "who": "halmi", "pose": "calm", "wait": 0.1},
        {"do": "cam", "shot": "kitchen_help", "at": "k_floor2", "rate": 1.2, "wait": 0.1, "settle": 0.8},
        {"do": "fx", "fx": "door:open", "wait": 0.2},
        *helper("bam", "pj_r0401", first=True), *helper("jara", "pj_r0402"), *helper("ddong", "pj_r0501"),
        *helper("songgot", "pj_r0502"), *helper("jeolgu", "pj_r0503"),
        {"do": "fx", "fx": "door:close", "wait": 0.3}]},
    # 4 -- the yard: the straw mat and the carrier come; the granny whispers her plan
    {"id": "yard", "title": "마당", "spread": _home(light="dusk"),
     "enter": {"who": {"halmi": "calm"}, "at": {"halmi": "granny_k"}, "keep": ["halmi", *KITCHEN_HELP]},
     "steps": [
        # wave 2: she is already behind the door (an unseen move inside the closed house; the walk through the
        # kitchen left the yard empty for 3 s)
        {"do": "fx", "fx": "place:halmi:tiger_door", "wait": 0.0},
        {"do": "fx", "fx": "door:open", "wait": 0.0},
        {"do": "cam", "shot": "yard", "at": ["y_granny", "y_jige"], "rate": 1.0, "wait": 0.1, "settle": 0.4},
        {"do": "walk", "who": "halmi", "via": ["door"], "to": "y_granny", "speed": 0.45},
        {"do": "fx", "fx": "door:close", "wait": 0.0},
        # pace: pj_r0601 cut (the yard helpers come on screen)
        *helper("myeongseok", "pj_r0602", yard=True), *helper("jige", "pj_r0603", yard=True),
        {"do": "cam", "shot": "yard_low", "at": "y_granny", "rate": 1.6, "wait": 0.1, "settle": 0.5},
        {"do": "say", "line": "pj_r0605"},
        {"do": "say", "line": "pj_r0606"}]},
    # 5 -- night: the tiger comes; into the kitchen; the chestnut, the turtle
    {"id": "night", "title": "깜깜한 밤", "spread": _home(light="night", sky=SKY_NIGHT),
     "enter": {"who": {"halmi": "calm"}, "at": {"halmi": "y_granny"}, "keep": ["halmi", *HELP]},
     "steps": [
        {"do": "fx", "fx": "steam:off", "wait": 0.0},  # (r6: a steam puff floated into the door shot's lens)
        {"do": "fx", "fx": "door:open", "wait": 0.2},
        {"do": "walk", "who": "halmi", "via": ["door", "tiger_door"], "to": "granny_wait", "speed": 0.45},
        {"do": "fx", "fx": "door:close", "wait": 0.0},
        # wave 2: the night walk to the door seen from above the pines (a pine card filled the lens at road level)
        {"do": "cam", "shot": "night_arrive", "at": "front_focus", "rate": 1.4, "wait": 0.2},
        {"do": "walk", "who": "tiger", "from": "road_by", "to": "door_out", "speed": 0.55,
         "follow": "tiger", "shot": "night_arrive", "line": "pj_r0701"},
        {"do": "cam", "shot": "yard_low", "at": "door_out", "rate": 2.0, "wait": 0.1, "settle": 0.5},
        {"do": "say", "line": "pj_r0702"},
        {"do": "go_inside", "who": "tiger", "house": "cottage", "to": {"tiger": "tiger_fire"}, "speed": 0.6,
         "door_clear": True},
        {"do": "cam", "shot": "kitchen", "at": "k_focus", "rate": 1.3, "wait": 0.2, "settle": 0.6},
        {"do": "say", "line": "pj_r0703"},
        {"do": "fx", "fx": "tiger_crouch", "wait": 0.3},
        {"do": "walk", "who": "halmi", "to": "corner", "speed": 0.22, "end_pose": "hide"},
        # the traps: one tap each where the helper hides (the first voiced, the rest ring hints)
        {"do": "cam", "shot": "kitchen_low", "at": "k_low_l", "rate": 1.8, "wait": 0.1, "settle": 0.6},
        {"do": "tap_steps", "target": "hearth", "prompt": "pj_037", "hint": "pj_037",
         "steps": [{"fx": "trap:bam", "wait": 1.0}]},
        {"do": "say", "line": "pj_r0705"},
        {"do": "say", "line": "pj_r0706", "segs": [0]},
        # wave 2: the camera pans with him from the hearth to the jar (it held the hearth while he left the frame)
        {"do": "cam", "shot": "kitchen_low", "at": ["k_low_l", "k_low_r"], "rate": 1.6, "wait": 0.0},
        {"do": "walk", "who": "tiger", "to": "tiger_jar", "speed": 0.35, "line": "pj_r0706",
         "segs": [1]},
        {"do": "fx", "fx": "tiger_dip", "wait": 0.6},
        {"do": "cam", "shot": "kitchen_low", "at": "k_low_r", "rate": 2.0, "wait": 0.1, "settle": 0.5},
        {"do": "tap_steps", "target": "muldok", "steps": [{"fx": "trap:jara", "wait": 0.8}]},
        {"do": "say", "line": "pj_r0707"}]},
    # 6 -- the kitchen in uproar: back-step onto the dung, the awl, run for the door, the mortar
    {"id": "uproar", "title": "부엌 소동", "spread": _home(light="night", sky=SKY_NIGHT),
     "enter": {"who": {}, "keep": ["halmi", "tiger", "ddong", "songgot", "jeolgu", "myeongseok", "jige", "bam", "jara"]},
     "steps": [
        {"do": "say", "line": "pj_r0801"},
        {"do": "fx", "fx": "backstep", "wait": 1.0},
        # wave 2: higher and over the dung so its tap ring sits above the caption (it was cut by the frame edge)
        {"do": "cam", "shot": "kitchen_floor", "at": ["k_focus", "dung"], "rate": 2.0, "wait": 0.1, "settle": 0.5},
        {"do": "tap_steps", "target": "ddong", "steps": [{"fx": "trap:ddong", "wait": 1.2}]},
        {"do": "say", "line": "pj_r0802"},
        {"do": "tap_steps", "target": "crack", "steps": [{"fx": "trap:songgot", "wait": 0.9}]},
        {"do": "say", "line": "pj_r0804"},
        {"do": "say", "line": "pj_r0805"},
        {"do": "fx", "fx": "door:open", "wait": 0.0},
        # wave 2: he bursts out of the door; the camera goes out with him and the mortar drops from over the door
        {"do": "cam", "shot": "door_drop", "at": ["door_out", "lintel"], "rate": 1.0, "wait": 0.2},
        {"do": "walk", "who": "tiger", "via": ["tiger_door", "door"], "to": "door_out", "speed": 0.55,
         "pose": "run_cry"},
        {"do": "cam_settle", "frac": 0.85},
        {"do": "tap_steps", "target": "jeolgu", "steps": [{"fx": "trap:jeolgu", "wait": 0.8}]},
        {"do": "cam", "shot": "door_drop", "at": "door_out", "rate": 2.0, "wait": 0.1},
        {"do": "say", "line": "pj_r0806"},
        {"do": "pose", "who": "tiger", "pose": "dazed", "wait": 0.8}]},  # pace: pj_r0807 cut (the stagger shows)
    # 7 -- the yard at night: flat out, rolled up in the mat, carried off to the sea
    {"id": "sea", "title": "마당과 바다", "spread": _home(light="night", sky=SKY_NIGHT),
     "enter": {"who": {}, "keep": ["halmi", "tiger", "myeongseok", "jige", "bam", "jara", "ddong", "songgot", "jeolgu"]},
     "steps": [
        {"do": "cam", "shot": "yard", "at": "y_focus", "rate": 1.4, "wait": 0.3},
        {"do": "walk", "who": "tiger", "to": "y_tiger", "speed": 0.45, "pose": "run_cry", "line": "pj_r0900"},
        {"do": "fx", "fx": "door:close", "wait": 0.1},
        {"do": "fx", "fx": "tiger_flat", "wait": 0.5},
        {"do": "cam", "shot": "yard_low", "at": ["y_tiger", "y_mat"], "rate": 1.8, "wait": 0.1, "settle": 0.5},
        {"do": "tap_steps", "target": "myeongseok",
         "steps": [{"fx": "roll:1", "wait": 0.4}, {"fx": "roll:2", "wait": 0.4}, {"fx": "roll:3", "wait": 0.7}]},
        {"do": "say", "line": "pj_r0901"},
        {"do": "say", "line": "pj_r0903"},
        {"do": "tap_steps", "target": "jige", "steps": [{"fx": "jige_lift", "wait": 1.0}]},
        # wave 2: the carry is on screen (a tracking shot on the carrier while the line plays), then the throw into
        # the waves and a small splash rising from the water (a giant card used to pop up in an empty sea shot)
        {"do": "fx", "fx": "jige_carry", "wait": 0.0},
        {"do": "cam", "shot": "carry", "follow": "jige", "rate": 1.4, "wait": 0.2},
        {"do": "say", "line": "pj_r0904"},
        {"do": "cam", "shot": "sea_view", "at": ["shore", "sea_splash"], "rate": 1.6, "wait": 0.1},
        {"do": "fx", "fx": "throw", "wait": 1.6},
        {"do": "fx", "fx": "jige_home", "wait": 0.0},
        {"do": "fx", "fx": "swim", "wait": 0.2},
        {"do": "say", "line": "pj_r0905"}]},
    # 8 -- the porridge feast in the yard
    {"id": "feast", "title": "팥죽 잔치", "spread": _home(light="evening", sky=SKY_NIGHT),
     "enter": {"who": {"halmi": "cheer"}, "at": {"halmi": "y_granny"},
               "keep": ["bam", "jara", "ddong", "songgot", "jeolgu", "myeongseok", "jige"]},
     "steps": [
        {"do": "fx", "fx": "feast", "wait": 0.6},
        {"do": "cam", "shot": "yard", "at": "y_feast", "rate": 1.0, "wait": 0.3, "settle": 0.6},
        {"do": "say", "line": "pj_r1001"},
        {"do": "fx", "fx": "hop_all", "wait": 0.2},
        {"do": "cam", "shot": "yard_low", "at": ["y_granny", "y_feast"], "rate": 1.6, "wait": 0.1, "settle": 0.5},
        # pace: pj_r1002 cut (the hug shows)
        {"do": "say", "line": "pj_r1003"},
        {"do": "end", "after": "pj_n02", "close_book": True}]},
]

# ---------------------------------------------------------------- sound
SOUND = {
    "catalog": "res://audio/sound_catalog.json",
    "light_beds": {"": "day", "morning": "day", "afternoon": "afternoon", "late": "late", "dusk": "dusk",
                   "night": "night", "evening": "evening"},
    "fx": {"tiger_out": "sm.growl_cute", "hoe": "build.straw", "hoe_drop": "wg.stone", "knock": "wg.knock",
           "give": "sm.gulp", "hide": "wc.plop", "tiger_crouch": "fire.crackle_m",
           "trap:bam": "wc.boing", "trap:jara": "wc.bonk", "trap:ddong": "sm.slide", "trap:songgot": "sm.paper_poke",
           "trap:jeolgu": "wc.bonk", "tiger_dip": "kitchen.splash", "backstep": "wc.swoosh",
           "tiger_flat": "wolf.flop", "roll": "wc.roll", "jige_lift": "prop.ladder_raise", "splash": "wg.splash", "throw": "wc.swoosh",
           "swim": "wc.wave", "feast": "wc.chime", "hop_all": "wc.sparkle"},
    "steps": {"cover": {"on_open": {"music": "intro_cozy", "fade": 0.2}}, "page_turn": "paper.page_turn",
              "go_inside": {"door_open": "door.open", "door_shut": "door.shut"},
              "end": {"close_book": "paper.book_close", "music_fade_on_replay": 2.0}},
    "footsteps": {"halmi": "pig", "tiger": "wolf"},
}
_BEAT_SOUND = {"cover": {"music": None, "bed": None},
               "field": {"music": "home", "bed": "@light", "emitters": ["trees"]},
               "winter": {"music": "night", "bed": "room"},
               "helpers": {"music": "home", "bed": "room"},
               "yard": {"music": "home", "bed": "@light"},
               "night": {"music": "wolf", "bed": "room"},
               "uproar": {"music": "chimney", "bed": "room"},
               "sea": {"music": "chimney", "bed": "@light"},
               "feast": {"music": "ending", "bed": "@light"}}
for _b in BEATS:
    if _b["id"] in _BEAT_SOUND:
        _b["sound"] = _BEAT_SOUND[_b["id"]]
