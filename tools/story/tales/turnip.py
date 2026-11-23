"""「커다란 순무」 (turnip) adaptation tables for tools/story/seed_script.py (2026-11-23).

Source: 톡톡's turnip has the play script (voice_script_el.json: seed / sprout taps, choose who grandma calls, guess the
voice, order quiz, soup taps) and the READ-MODE script (read_script_el.json, scenes R01-R10, every line recorded in
read_narration_el.js, same voices). The pop-up book follows the READ script (story first: no quizzes, no counting, no
moral) and borrows only the play script's first-tap instructions, each voiced once (tn_002 seed, tn_005 sprout,
tn_014 pull, tn_034 the mouse hole, tn_060 the pot; it replaces the read line "순무국을 한 그릇씩 나눠 줘요.").
Extras voiced once: grandpa calling "할머니~!" (call_grandma), the puppy's growl at the glare (cut_glare), the mouse's
squeak (squeak_mouse), grandpa's "영~차!" on the last pull (cut_heave).

Cut (pace / tale-not-lesson):
- the scene-opening recaps the continuous camera already shows (r0200, r0300, r0400, r0500, r0600, r0700, r0800,
  r0900) and r0104 / r0202 / r0205 (time passing that the growth taps show), r0504, r0603;
- counting: r1005 "여섯 그릇, 여섯 명! 딱 맞아요." (a count-and-match); r1004 replaced by the play prompt tn_060;
- the moral r1007 "작은 힘도 모이면 커다란 힘이 된답니다." and r0904; r1003 (the smell; pace);
- v1 pace (5:40 -> shorter): r0101 (the seed in his palm shows), r0203 (the leaves grow on the taps), r0306 (grandpa's own "할머니~!" calls her), r0302
  (r0303 says it), r0605 / r0705 (the turnip not moving is shown), two heaves per pull instead of three (the last
  pull keeps three), two pot taps (three bowls each);
- r0502's "손녀야~!" seg (grandma already called her in r0404): READ_SEG_KEEP keeps the narration seg only.

One place, one spread (seed 3, view 4): the grandparents' long thatched farmhouse at the back, the red barn beside it,
the vegetable garden in front; camera moves only (no page turns). Light: spring morning -> summer day -> afternoon ->
late -> warm evening feast under paper lanterns.
"""
TALE_ID = "turnip"
TITLE = "커다란 순무"
PREFIX = "tn"
MORAL = ""  # no moral (user: the book tells the tale)
READ_SCRIPT = True

CHANGED = {}
SEG_KEEP = {}
READ_SEG_KEEP = {
    "tn_r0502": [1],   # "손녀가 할머니 허리를 잡았어요. 영차!" only (grandma's "손녀야~!" was r0404 already)
}
NEW_LINES = {
    # the narrator is the same ElevenLabs voice as witch_candy / wolf_goats (pFZP5JQG7iQjIQuC4Bku): their recorded
    # cover / replay clips (same text, same voice) are reused (game/audio/voice/turnip/recorded.json)
    "tn_n01": [["nar", "그림책을 톡 눌러서 펼쳐 볼까요?", None, "[cheerful, inviting, warm, cosy Halloween night]"]],
    "tn_n02": [["nar", "또 보고 싶으면 '다시 보기'를 톡!", None, "[cheerful, inviting]"]],
}
TRIM = {}
# one caption, one voice: the puppy's growl clip runs 10.5 s of repeated growls (speech blocks 0-0.91 s, 1.3-3.4 s, ...)
# and grandpa's "영~차!" says it twice (0-1.47 s, 1.82-3.2 s): the first take of each, faded (nothing recorded)
TRIM_SEG = {"tn_x_cut_glare": {0: ("res://audio/voice/turnip/dog_61fd5bc6f6_t.mp3",
                                   "audio/el/turnip/dog_61fd5bc6f6.mp3 (0-1.05 s: the first growl only)")},
            "tn_x_cut_heave": {0: ("res://audio/voice/turnip/grandpa_cc99ce5356_t.mp3",
                                   "audio/el/turnip/grandpa_cc99ce5356.mp3 (0-1.6 s: the first take only)")}}
DROPPED = set()
ALL6 = ["grandpa", "grandma", "girl", "dog", "cat", "mouse"]


def _all(pose, who=ALL6):
    return {k: pose for k in who}


LINE_META = {
    "tn_n01": {}, "tn_n02": {},
    "tn_r0100": {"expr": {"grandpa": "plant"}},
    "tn_r0101": {"expr": {"grandpa": "plant"}},
    "tn_r0102": {"expr": {"grandpa": "plant"}},
    "tn_r0201": {"expr": {"grandpa": "surprised"}},
    "tn_r0204": {"expr": {"grandpa": "surprised"}},
    "tn_r0301": {"expr": {"grandpa": "clap"}},
    "tn_r0305": {"expr": {"grandpa": "tumble"}},
    "tn_r0306": {"expr": {"grandpa": "call"}},
    "tn_x_call_grandma": {"expr": {"grandpa": "call"}},
    "tn_r0401": {"expr": {"grandma": ["calm", "encourage"]}},
    "tn_r0404": {"expr": {"grandma": "call"}},
    "tn_r0602": {"expr": {"dog": ["happy", "happy"]}},
    "tn_r0703": {"expr": {"dog": "growl", "cat": "glare"}},
    "tn_x_cut_glare": {"expr": {"dog": "growl"}},
    "tn_r0704": {"expr": {"cat": ["glare", "pull"]}},
    "tn_r0706": {"expr": _all("sit_tired", ALL6[:5])},
    "tn_r0803": {"expr": {"cat": "glare"}},
    "tn_r0804": {"expr": {"mouse": ["brave", "brave"]}},
    "tn_r0904": {"expr": _all("cheer", ALL6[:3]) | _all("happy", ALL6[3:])},
    "tn_r0905": {"expr": {"grandpa": "cheer"}},
    "tn_r1001": {"expr": {"grandpa": "clap", "grandma": "ladle"}},
    "tn_r1006": {"expr": _all("eat")},
}

# ---------------------------------------------------------------- stage
HANDLER = "res://stories/turnip/fx.gd"
BACKDROP = True
EXTRA = {"ground_style": "paper", "spacing": True, "overlap_check": True, "pop_in": False,
         # intended contacts (reason): the pulling line holds on, each one the waist / skirt / tail of the one ahead
         # (the story is the line itself); grandpa grips the turnip's leaves
         "overlap_ok": [["grandpa", "turnip"], ["grandma", "grandpa"], ["girl", "grandma"], ["dog", "girl"],
                        ["cat", "dog"], ["mouse", "cat"]],
         # the pullers are leaned / tumbled by the handler: the spacing solver must not push the line apart
         "no_spacing": ALL6}

SHOTS = {"story": [3.0, 12.0, 0.26, 22.0], "close": [2.4, 12.0, 0.28, 20.0],
         "crane_high": [8.5, 34.0, 0.3, 24.0, 0.0],
         "establish": [5.6, 24.0, 0.3, 24.0, -6.0],           # the garden plot, house and barn behind (v2: higher)
         "garden": [3.4, 17.0, 0.25, 24.0, 4.0],
         "medium": [2.2, 13.0, 0.2, 22.0, 6.0],
         "seed": [1.15, 16.0, 0.1, 24.0, -6.0],                # grandpa kneeling, the hole, the seed in his palm
         "sprout": [1.6, 14.0, 0.1, 24.0, 8.0],
         "grown": [2.4, 10.0, 0.28, 24.0, -4.0],                 # low: the leaves as tall as grandpa
         "line": [2.5, 13.0, 0.2, 24.0, 10.0],                 # the turnip and the line, from a little to the right
         "line_low": [2.1, 7.0, 0.22, 28.0, -12.0],           # low, from the turnip's side: effort
         "line_wide": [3.6, 15.0, 0.2, 24.0, 4.0],            # the whole line of six and the turnip
         "house": [3.2, 10.0, 0.4, 24.0, -10.0],               # the farmhouse door (grandma comes out)
         "yard": [3.0, 10.0, 0.3, 24.0, 18.0],                 # the girl from the yard
         "bush": [1.7, 7.0, 0.16, 26.0, 14.0],
         "barn": [4.4, 9.0, 0.62, 12.0, 6.0],                  # up at the barn roof: a long lens from far back, so the glide stays well in front of the line (v2)
         "glare": [1.5, 6.0, 0.1, 26.0, 14.0],                  # the dog and the cat nose to nose
         "hole": [1.05, 7.0, 0.05, 26.0, 16.0],                # down at the mouse hole
         "pop": [3.6, 15.0, 0.26, 26.0, 0.0],                  # the big pull: room above for the flying turnip
         "feast": [2.6, 15.0, 0.22, 24.0, 0.0],
         "pot": [1.4, 16.0, 0.18, 26.0, 6.0],
         "pull_back": [9.5, 26.0, 0.3, 24.0, 0.0]}

ROLES_LABEL = {"grandpa": "할아버지", "grandma": "할머니", "girl": "손녀", "dog": "강아지", "cat": "고양이", "mouse": "생쥐"}
CAST = {
    "grandpa": {"kind": "actor", "skin": "farm_grandpa", "height": 0.28, "views": ["front", "side", "back"], "label": "할아버지"},
    "grandma": {"kind": "actor", "skin": "farm_grandma", "height": 0.26, "views": ["front", "side", "back"], "label": "할머니"},
    "girl": {"kind": "actor", "skin": "farm_girl", "height": 0.2, "views": ["front", "side", "back"], "label": "손녀"},
    "dog": {"kind": "actor", "skin": "puppy", "height": 0.115, "views": ["side", "front", "back"], "label": "강아지"},
    "cat": {"kind": "actor", "skin": "tabby_cat", "height": 0.105, "views": ["side", "front", "back"], "label": "고양이"},
    "mouse": {"kind": "actor", "skin": "mouse", "height": 0.05, "views": ["side", "front", "back"], "label": "생쥐"},
}
UI = {
    "cover": [["cast_farm_grandpa_calm", 230], ["cast_farm_girl_calm", 160], ["cast_puppy_happy", 110]],
    "end": [["cast_farm_grandpa_cheer", 230], ["cast_farm_grandma_clap", 220], ["cast_tabby_cat_happy", 100]],
    "speakers": {"grandpa": ["할아버지", "3f7a4f", "cast_farm_grandpa_calm"],
                 "grandma": ["할머니", "d8642a", "cast_farm_grandma_calm"],
                 "girl": ["손녀", "c8322b", "cast_farm_girl_calm"],
                 "dog": ["강아지", "c9954a", "cast_puppy_happy"],
                 "cat": ["고양이", "e0a030", "cast_tabby_cat_happy"],
                 "mouse": ["생쥐", "8a8580", "cast_mouse_happy"]},
}


def _e(card, at, name, scale=1.0, **kw):
    e = {"card": card, "at": at, "stage": "full", "name": name, "scale": scale, "clear": 0.4}
    e.update(kw)
    return e


# ---------------------------------------------------------------- the farm (seed 3, view 4): spots [right, toward]
# The road (probed, tools/story/probe_spots_wide.gd seed=3 4) runs right of centre from (-0.6, 0.9) up to (0.3, -2.4)
# and (0.0, -3.0); the garden is the open meadow left of it. The turnip grows at TURNIP; the pullers line up to its
# right (screen right), each facing it (side figures mirrored), at LINE marks (holding the one ahead: contacts).
TX, TZ = -1.6, -0.95  # the turnip stands a step behind the line, so grandpa is in front of its leaves
LINE_X = {"grandpa": -1.34, "grandma": -1.2, "girl": -1.07, "dog": -0.95, "cat": -0.85, "mouse": -0.775}
LZ = -0.85
FARM = {"turnip": [TX, TZ], "est": [-1.6, -1.45], "garden_focus": [-1.55, -1.0], "line_focus": [-1.2, -0.85],
        "seed_focus": [-1.52, -0.8],
        "house": [-2.05, -2.75], "house_door": [-2.05, -2.5], "barn": [-0.55, -2.95],
        "barn_foot": [-0.35, -2.55], "barn_roof": [-0.55, -2.92],
        "bush": [0.02, -1.25], "bush_out": [-0.15, -1.08], "yard": [-0.15, -2.25], "yard_in": [-0.5, -1.6],
        "mouse_hole": [-0.5, -0.36], "hole_out": [-0.6, -0.3],
        # the feast stands off the plot, behind its open right half (v2): table between the garden and the barn
        "pot_spot": [-1.05, -1.98], "table": [-1.05, -2.0], "lanterns": [-1.05, -2.3], "bread": [-0.88, -1.98],
        "turnip_land": [-1.0, -1.22],    # the open bed behind the line (v2: was in the plot's rows; in front it hid the line)
        "turnip_rest": [-0.42, -2.02],   # the pulled turnip carried beside the table (v2)
        "feast_focus": [-1.05, -1.75],
        # the feast: grandpa and grandma at the table's ends, the girl and the animals in front with their bowls
        # (in line order left to right, so nobody's path crosses another's on the way from the line)
        "eat_grandpa": [-1.55, -1.95], "eat_grandma": [-1.38, -1.55], "eat_girl": [-1.18, -1.47],
        "eat_dog": [-0.96, -1.44], "eat_cat": [-0.78, -1.47], "eat_mouse": [-0.63, -1.52],
        "gp_side": [-1.3, -0.85],
        # the 텃밭 (v2, user: "순무는 텃밭이 없네용?"): the gate gap in the back fence and the path to the house door
        "gate_out": [-1.78, -1.62], "gate_in": [-1.72, -1.3], "plot_focus": [-1.75, -1.0]}
for _r, _x in LINE_X.items():
    FARM[f"line_{_r}"] = [_x, LZ]

# ---------------------------------------------------------------- the vegetable garden (v2, 2026-11-23)
# A tilled plot (story_veg_ground_00, laid flat, `floor`: people stand on its top) x -3.0..-0.6, z -1.36..-0.38;
# ridges run left-right. The left half holds five vegetable rows (front -> back: lettuce, carrots, the turnip row with
# small turnips, peas / tomatoes, cabbages / pumpkin / onions); the giant turnip grows at the right end of its row and
# the right half is its open working bed (the pulling line stands there; the turnip lands in front of the line; the
# walks to the feast cross it behind). Picket fence on the left and the back (the gate open, a gap where the stepping
# stones come from the house door), stone edging along the front of the rows. Shared kit: tools/art/garden_jobs.py.
PLOT = {"x0": -3.0, "x1": -0.6, "z_front": -0.38}


def _g(card, x, z, name, scale=1.0, **kw):
    FARM[name] = [x, z]
    return _e(card, name, name, scale, clear=0, **kw)


VEG = "story_veg_garden_"
SET_GARDEN = [
    {"card": "story_veg_ground_00", "at": [-1.8, PLOT["z_front"]], "stage": "full", "name": "plot", "scale": 0.98,
     "clear": 0.85, "flat": True, "floor": True, "lift": 0.016},
    {"card": "story_veg_ground_01", "at": [-1.92, -1.98], "stage": "full", "name": "stones", "scale": 0.72,
     "clear": 0.3, "flat": True, "lift": 0.004, "yaw": 74.0},
    # row 1 (front): lettuces
    _g(VEG + "02", -2.78, -0.52, "lettuce_a", 1.05), _g(VEG + "02", -2.45, -0.53, "lettuce_b", 1.12),
    _g(VEG + "08", -2.13, -0.52, "strawb_a", 1.15),
    # row 2: carrots + onions
    _g("story_tn_garden_11", -2.86, -0.72, "carrots_a", 1.05), _g("story_tn_garden_11", -2.66, -0.73, "carrots_b", 1.0),
    _g("story_tn_garden_11", -2.46, -0.72, "carrots_c", 1.08), _g(VEG + "03", -2.16, -0.73, "onions_a", 1.0),
    # row 3: the turnip row (small turnips; a bare sown ridge; the giant at its right end, handler card)
    _g(VEG + "04", -2.78, -0.94, "turnips_a", 1.05), _g(VEG + "04", -2.46, -0.95, "turnips_b", 0.98),
    _g(VEG + "00", -2.12, -0.94, "ridge_a", 1.1),
    # row 4: peas on a trellis, tomatoes
    _g(VEG + "06", -2.76, -1.14, "peas_a", 1.0), _g(VEG + "05", -2.42, -1.15, "tomatoes_a", 1.0),
    _g(VEG + "06", -2.12, -1.14, "peas_b", 0.92),
    # row 5 (back): cabbages, pumpkin, beans
    _g("story_tn_garden_10", -2.78, -1.31, "cabbages_a", 1.05), _g(VEG + "07", -2.44, -1.32, "pumpkin_a", 1.0),
    _g("story_tn_garden_12", -2.14, -1.32, "beans_a", 0.9),
    # fence: left side (turned), back (gate open), stone edging in front of the rows
    _g(VEG + "09", -3.1, -0.62, "fence_l1", 1.0, yaw=90.0), _g(VEG + "09", -3.1, -1.04, "fence_l2", 1.0, yaw=90.0),
    _g(VEG + "10", -3.1, -1.36, "fence_l3", 0.95, yaw=90.0),
    _g(VEG + "09", -2.83, -1.47, "fence_b1", 1.0), _g(VEG + "09", -2.42, -1.47, "fence_b2", 1.0),
    _g(VEG + "11", -2.08, -1.47, "gate", 1.0),
    _g(VEG + "18", -2.78, -0.36, "edging_a", 1.0), _g(VEG + "18", -2.5, -0.35, "edging_b", 1.0),
    _g(VEG + "18", -2.22, -0.36, "edging_c", 1.0),
    _g(VEG + "15", -1.98, -0.73, "marker_a", 1.0), _g(VEG + "17", -1.96, -1.15, "marker_b", 1.0),
    # around the plot: scarecrow, wheelbarrow, watering can, a basket of the day's vegetables, sunflowers
    _g("meadow_field_16", -3.32, -1.5, "scarecrow", 1.0), _g(VEG + "13", -3.42, -0.8, "wheelbarrow", 1.0),
    _g("story_tn_garden_06", -1.95, -0.26, "can", 1.0), _g(VEG + "14", -3.3, -0.3, "basket", 1.0),
    _g("meadow_field_27", -2.5, -1.62, "sunflowers", 1.0),
]
SET = [
    _e("village_houses_15", "house", "house", 1.15, clear=1.4),
    _e("village_houses_04", "barn", "barn", 0.95, clear=1.0),
    *SET_GARDEN,
    _e("bushes_hedges_26", "bush", "bush", 1.0, clear=0.35),
    _e("story_tn_garden_13", "mouse_hole", "mouse_hole", 1.0, clear=0.25),
    # the feast (popped in its beat)
    _e("story_tn_feast_00", "table", "table", 1.0, stage=0, clear=0),
    _e("story_tn_feast_08", "lanterns", "lanterns", 1.0, stage=0, clear=0, glow=0.8,
       light=[0.5, 0.3, 1.2, "#ffc060", True]),
]


def _farm(**kw):
    sp = {"seed": 3, "view": 4, "place": "farm", "light": "", "spots": FARM, "set": SET, "focus": "garden_focus"}
    sp.update(kw)
    return sp


LINE = {r: f"line_{r}" for r in ALL6}
L1 = ["grandpa"]


def _line(n):
    return ALL6[:n]


def _enter(n, pose="pull", extra=None):
    who = {r: pose for r in _line(n)}
    at = {r: LINE[r] for r in _line(n)}
    e = {"who": who, "at": at, "left": {r: 1 for r in _line(n)}}
    if extra:
        for k, v in extra.items():
            e.setdefault(k, {}).update(v)
    return e


def _pull(n, taps, prompt=None, lines=None, rise=0.035, last=None):
    """n pullers, taps heaves (the line leans back, the turnip wobbles / rises a little each heave)."""
    steps = []
    for k in range(taps):
        s = {"fx": f"heave:{n}:{rise if k == taps - 1 else rise * 0.4}", "wait": 0.45}
        if lines and k in lines:
            s["lines"] = lines[k]
        steps.append(s)
    if last:
        steps[-1].update(last)
    st = {"do": "tap_steps", "target": "turnip", "steps": steps}
    if prompt:
        st["prompt"] = prompt
        st["hint"] = prompt
    return st


BEATS = [
    {"id": "cover", "title": "커다란 순무", "spread": None, "steps": [{"do": "cover", "prompt": "tn_n01"}]},
    # 1 -- spring: grandpa digs a hole, a seed in his palm, into the soil
    {"id": "seed", "title": "봄", "spread": _farm(light=""), "tn": {"turnip": ""},
     "enter": {"who": {"grandpa": "plant"}, "at": {"grandpa": "gp_side"}, "left": {"grandpa": 1}},
     "steps": [
        {"do": "cam", "shot": "establish", "at": "est", "from": "crane_high", "rate": 0.9, "wait": 0.8},
        {"do": "fx", "fx": "dig", "wait": 0.1},
        {"do": "say", "line": "tn_r0100"},
        {"do": "cam", "shot": "seed", "at": "seed_focus", "rate": 1.3, "wait": 0.3, "settle": 0.6},
        {"do": "fx", "fx": "seed_palm", "wait": 0.2},
        {"do": "say", "line": "tn_r0102"},
        {"do": "tap_steps", "target": "seed", "prompt": "tn_002", "hint": "tn_002",
         "steps": [{"fx": "plant_seed", "wait": 0.6}]},
        {"do": "say", "line": "tn_r0103"}]},
    # 2 -- it grows: water, sun, the leaves, summer; the giant turnip's leaves as tall as grandpa
    {"id": "grow", "title": "무럭무럭", "spread": _farm(light=""), "tn": {"turnip": "hole"},
     "enter": {"who": {"grandpa": "side_walk"}, "at": {"grandpa": "gp_side"}, "left": {"grandpa": 1}},
     "steps": [
        {"do": "fx", "fx": "sprout", "wait": 0.6},
        {"do": "cam", "shot": "sprout", "at": "seed_focus", "rate": 1.2, "wait": 0.3, "settle": 0.5},
        {"do": "say", "line": "tn_r0201"},
        {"do": "tap_steps", "target": "sprout", "prompt": "tn_005", "hint": "tn_005",
         "steps": [{"fx": "water", "wait": 1.4},
                   {"fx": "sun", "wait": 1.2},
                   {"fx": "summer", "wait": 1.0}]},
        {"do": "cam", "shot": "grown", "at": "seed_focus", "rate": 1.2, "wait": 0.3, "settle": 0.5},
        {"do": "say", "line": "tn_r0204"}]},
    # 3 -- grandpa alone: 꿈쩍도 안 해요, 엉덩방아, he calls grandma; she comes running out of the kitchen
    {"id": "grandpa", "title": "영차!", "spread": _farm(light="afternoon"), "tn": {"turnip": "big"},
     "enter": {"who": {"grandpa": "side_walk"}, "at": {"grandpa": "gp_side"}, "left": {"grandpa": 1}},
     "steps": [
        {"do": "cam", "shot": "medium", "at": "line_focus", "rate": 1.2, "wait": 0.2},
        {"do": "say", "line": "tn_r0301"},
        {"do": "walk", "who": "grandpa", "to": "line_grandpa", "speed": 0.15},
        {"do": "pose", "who": "grandpa", "pose": "pull", "left": 1, "wait": 0.2},
        {"do": "cam", "shot": "line", "at": ["turnip", "line_grandpa"], "rate": 1.4, "wait": 0.2, "settle": 0.5},
        _pull(1, 2, prompt="tn_014", lines={0: ["tn_r0303"]}, rise=0.0),
        {"do": "say", "line": "tn_r0304"},
        {"do": "fx", "fx": "fall:grandpa", "wait": 0.2},
        {"do": "say", "line": "tn_r0305"},
        {"do": "pose", "who": "grandpa", "pose": "call", "wait": 0.1},
        {"do": "say", "line": "tn_x_call_grandma"},
        {"do": "cam", "shot": "house", "at": ["house_door", "line_grandpa"], "rate": 1.3, "wait": 0.2},
        {"do": "walk", "who": "grandma", "from": "house_door", "to": "line_grandma", "speed": 0.42, "pose": "run",
         "via": ["gate_out", "gate_in"], "follow": "grandma", "shot": "garden", "line": "tn_r0307"}]},
    # 4 -- grandma: 같이 해 봐요! two pull; a hand's width up; she calls the girl
    {"id": "grandma", "title": "할머니~!", "spread": _farm(light="afternoon"), "tn": {"turnip": "big"},
     "enter": _enter(2, extra={"who": {"grandma": "calm"}}),
     "steps": [
        {"do": "fx", "fx": "get_up:grandpa", "wait": 0.1},
        {"do": "cam", "shot": "line", "at": ["turnip", "line_grandma"], "rate": 1.4, "wait": 0.2, "settle": 0.5},
        {"do": "say", "line": "tn_r0401"},
        {"do": "pose", "who": "grandma", "pose": "pull", "left": 1, "wait": 0.1},
        {"do": "say", "line": "tn_r0402"},
        _pull(2, 2, rise=0.03),
        {"do": "say", "line": "tn_r0403"},
        {"do": "pose", "who": "grandma", "pose": "call", "wait": 0.1},
        {"do": "say", "line": "tn_r0404"},
        {"do": "pose", "who": "grandma", "pose": "pull", "left": 1, "wait": 0.1}]},
    # 5 -- the girl skips in from the yard: three pull, a little more
    {"id": "girl", "title": "손녀", "spread": _farm(light="afternoon"), "tn": {"turnip": "big", "rise": 0.042},
     "enter": _enter(2),
     "steps": [
        {"do": "cam", "shot": "yard", "at": ["yard_in", "line_grandma"], "rate": 1.2, "wait": 0.2},
        {"do": "walk", "who": "girl", "from": "yard", "to": "line_girl", "speed": 0.42, "pose": "run",
         "follow": "girl", "shot": "garden", "line": "tn_r0501"},
        {"do": "pose", "who": "girl", "pose": "pull", "left": 1, "wait": 0.1},
        {"do": "cam", "shot": "line_low", "at": ["turnip", "line_girl"], "rate": 1.4, "wait": 0.2, "settle": 0.5},
        {"do": "say", "line": "tn_r0502"},
        _pull(3, 2, rise=0.02),
        {"do": "say", "line": "tn_r0503"}]},
    # 6 -- 덤불 뒤에서 멍멍! the puppy jumps out of the bush
    {"id": "dog", "title": "멍멍!", "spread": _farm(light="late"), "tn": {"turnip": "big", "rise": 0.07},
     "enter": _enter(3, extra={"hidden": {"dog": "bush"}}),
     "steps": [
        {"do": "cam", "shot": "bush", "at": "bush", "rate": 1.2, "wait": 0.2, "settle": 0.5},
        {"do": "fx", "fx": "rustle:bush", "wait": 0.3},
        {"do": "say", "line": "tn_r0601"},
        {"do": "tap_steps", "target": "bush", "steps": [{"fx": "dog_out", "wait": 0.3}]},
        {"do": "walk", "who": "dog", "to": "line_dog", "speed": 0.4, "follow": "dog", "shot": "garden",
         "line": "tn_r0602", "segs": [0]},
        {"do": "pose", "who": "dog", "pose": "happy", "wait": 0.1},
        {"do": "say", "line": "tn_r0602", "segs": [1]},
        {"do": "pose", "who": "dog", "pose": "pull", "left": 1, "wait": 0.1},
        {"do": "cam", "shot": "line", "at": ["turnip", "line_dog"], "rate": 1.4, "wait": 0.2, "settle": 0.5},
        {"do": "say", "line": "tn_r0604"},
        _pull(4, 2, rise=0.02),
        ]},
    # 7 -- 헛간 지붕에서 야옹! the cat hops down; a glare; she holds the puppy's tail; they all sit down, tired
    {"id": "cat", "title": "야옹!", "spread": _farm(light="late"), "tn": {"turnip": "big", "rise": 0.098},
     "enter": _enter(4, extra={"hidden": {"cat": "barn_roof"}}),
     "steps": [
        {"do": "cam", "shot": "barn", "at": "barn", "rate": 1.1, "wait": 0.2, "settle": 0.4},
        {"do": "fx", "fx": "cat_roof", "wait": 0.5},
        {"do": "say", "line": "tn_r0701"},
        {"do": "fx", "fx": "cat_down", "wait": 0.15},
        {"do": "cam", "shot": "medium", "at": "barn_foot", "rate": 1.6, "wait": 0.85},
        {"do": "walk", "who": "cat", "from": "barn_foot", "to": "line_cat", "speed": 0.5,
         "follow": "cat", "shot": "garden", "line": "tn_r0702"},
        {"do": "fx", "fx": "glare", "wait": 0.1},
        {"do": "cam", "shot": "glare", "at": ["line_dog", "line_cat"], "rate": 1.4, "wait": 0.2, "settle": 0.5},
        {"do": "say", "line": "tn_r0703"},
        {"do": "say", "line": "tn_x_cut_glare"},
        {"do": "say", "line": "tn_r0704", "segs": [0]},
        {"do": "pose", "who": "dog", "pose": "pull", "left": 1, "wait": 0.0},
        {"do": "pose", "who": "cat", "pose": "pull", "left": 1, "wait": 0.1},
        {"do": "say", "line": "tn_r0704", "segs": [1]},
        {"do": "cam", "shot": "line_wide", "at": ["turnip", "line_cat"], "rate": 1.3, "wait": 0.2, "settle": 0.5},
        _pull(5, 2, rise=0.0),
        {"do": "fx", "fx": "sit_all:5", "wait": 0.3},
        {"do": "say", "line": "tn_r0706"}]},
    # 8 -- 찍찍: the mouse hole; the tiny mouse; "너무 작아서 안 될 거야~"; "나도 할래요!"; everyone up again
    {"id": "mouse", "title": "아주 작은 생쥐", "spread": _farm(light="late"), "tn": {"turnip": "big", "rise": 0.098},
     "enter": {**_enter(5, "sit_tired"), "hidden": {"mouse": "mouse_hole"}},
     "steps": [
        {"do": "cam", "shot": "hole", "at": "mouse_hole", "rate": 1.2, "wait": 0.2, "settle": 0.5},
        {"do": "say", "line": "tn_r0801"},
        {"do": "say", "line": "tn_x_squeak_mouse"},
        {"do": "tap_steps", "target": "mouse_hole", "prompt": "tn_034", "hint": "tn_034",
         "steps": [{"fx": "mouse_out", "wait": 0.3}]},
        {"do": "walk", "who": "mouse", "to": "line_mouse", "speed": 0.22, "follow": "mouse", "shot": "glare",
         "line": "tn_r0802"},
        {"do": "cam", "shot": "glare", "at": ["line_cat", "line_mouse"], "rate": 1.4, "wait": 0.2, "settle": 0.5},
        {"do": "say", "line": "tn_r0803"},
        {"do": "say", "line": "tn_r0804"},
        {"do": "fx", "fx": "stand_all:6", "wait": 0.2},
        {"do": "cam", "shot": "line_wide", "at": ["turnip", "line_cat"], "rate": 1.3, "wait": 0.2, "settle": 0.5},
        {"do": "say", "line": "tn_r0805"}]},
    # 9 -- all six: 영차, 영차! 쑥! everyone tumbles; 고맙다, 얘들아!
    {"id": "pop", "title": "다 함께 영차!", "spread": _farm(light="late"), "tn": {"turnip": "big", "rise": 0.098},
     "enter": _enter(6),
     "steps": [
        {"do": "cam", "shot": "pop", "at": ["turnip_land", "line_mouse"], "rate": 1.2, "wait": 0.2, "settle": 0.5},
        {"do": "say", "line": "tn_r0901"},
        _pull(6, 3, rise=0.05, lines={0: ["tn_x_cut_heave"], 1: ["tn_r0902"]},
              last={"fx": "turnip_out", "wait": 0.1, "lines": ["tn_r0903"]}),
        {"do": "fx", "fx": "cheer_all", "wait": 0.3},
        {"do": "cam", "shot": "medium", "at": ["turnip_land", "line_grandpa"], "rate": 1.3, "wait": 0.2, "settle": 0.5},
        {"do": "say", "line": "tn_r0905"}]},
    # 10 -- the feast: at the table in front of the house, the soup, a bowl each, everyone eats
    {"id": "feast", "title": "순무 잔치", "spread": _farm(light="evening"), "tn": {"turnip": "out"},
     "enter": {"who": _all("cheer", ALL6[:3]) | _all("happy", ALL6[3:]),
               "at": {"grandpa": "line_grandpa", "grandma": "line_grandma", "girl": "line_girl", "dog": "line_dog",
                      "cat": "line_cat", "mouse": "line_mouse"}},
     "steps": [
        {"do": "fx", "fx": "carry", "wait": 1.0},  # v2: the turnip rolls off to the table before anyone walks
        {"do": "fx", "fx": "pop:table", "wait": 0.15},
        {"do": "fx", "fx": "pop:lanterns", "wait": 0.15},
        {"do": "cam", "shot": "garden", "at": "feast_focus", "rate": 1.0, "wait": 0.2},
        {"do": "fx", "fx": "to_table", "wait": 0.1},
        {"do": "walk", "who": ALL6, "to": {r: f"eat_{r}" for r in ALL6}, "speed": 0.3, "line": "tn_r1000"},
        {"do": "cam", "shot": "feast", "at": "feast_focus", "rate": 1.2, "wait": 0.2, "settle": 0.5},
        {"do": "fx", "fx": "cook", "wait": 0.2},
        {"do": "say", "line": "tn_r1001"},
        {"do": "fx", "fx": "boil", "wait": 0.2},
        {"do": "say", "line": "tn_r1002"},
        {"do": "tap_steps", "target": "pot", "prompt": "tn_060", "hint": "tn_060", "shot": "pot",
         "steps": [{"fx": "bowls:0", "wait": 0.6}, {"fx": "bowls:1", "wait": 0.8}]},
        {"do": "cam", "shot": "feast", "at": "feast_focus", "rate": 1.2, "wait": 0.2, "settle": 0.5},
        {"do": "say", "line": "tn_r1006"},
        {"do": "end", "after": "tn_n02", "close_book": True}]},
]
for _b in BEATS:  # every page beat states where everyone stands (`--beat` starts, same-page changes)
    if _b["spread"] is not None:
        _b["enter"].setdefault("keep", [])

# ---------------------------------------------------------------- sound (SoundDirector ids; tn.* copied from 톡톡)
SOUND = {
    "catalog": "res://audio/sound_catalog.json",
    "light_beds": {"": "day", "afternoon": "afternoon", "late": "late", "evening": "evening"},
    "fx": {"dig": "tn.dig", "plant_seed": "tn.dig", "sprout": "tn.grow", "water": "tn.water", "sun": "tn.sun",
           "summer": "tn.grow", "heave": "tn.strain", "fall": "wolf.flop", "rustle": "tn.rustle",
           "dog_out": "tn.bark", "cat_roof": "tn.meow", "mouse_out": "tn.squeak", "turnip_out": "tn.pop",
           "cheer_all": "tn.cheer", "boil": "kitchen.boil", "bowls": "tn.slurp", "sit_all": "wolf.flop"},
    "steps": {"cover": {"on_open": {"music": "intro_cozy2", "fade": 0.2}}, "page_turn": "paper.page_turn",
              "end": {"close_book": "paper.book_close", "music_fade_on_replay": 2.0}},
    "footsteps": {"grandpa": "pig", "grandma": "pig", "girl": "pig", "dog": None, "cat": None, "mouse": None},
}
_BEAT_SOUND = {"cover": {"music": None, "bed": None},
               "seed": {"music": "turnip", "bed": "@light", "emitters": ["trees"]},
               "grow": {"music": "turnip", "bed": "@light", "emitters": ["trees"]},
               "grandpa": {"music": "turnip", "bed": "@light", "emitters": ["trees"]},
               "grandma": {"music": "turnip", "bed": "@light"}, "girl": {"music": "turnip", "bed": "@light"},
               "dog": {"music": "turnip", "bed": "@light"}, "cat": {"music": "turnip", "bed": "@light"},
               "mouse": {"music": "turnip", "bed": "@light"}, "pop": {"music": "turnip", "bed": "@light"},
               "feast": {"music": "finale_happy", "bed": "@light"}}
for _b in BEATS:
    if _b["id"] in _BEAT_SOUND:
        _b["sound"] = _BEAT_SOUND[_b["id"]]
