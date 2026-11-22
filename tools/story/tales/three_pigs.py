"""「아기 돼지 삼형제」 (three_pigs) adaptation tables for tools/story/seed_script.py (plan: game/stories/three_pigs/PLAN.md).

Phase 1 (2026-11-18): script + plan + art. Verbs marked NEW below are not in story_runner.gd yet (phase 2); the seeded
script.json is data the runner will grow into. Existing verbs used as is: cover, cam, say, pose, fx, end.
"""
TALE_ID = "three_pigs"
TITLE = "아기 돼지 삼형제"
PREFIX = "tp"
# role -> shared cast skin (game/art/cast/catalog.json role), views each role needs (front = toward the camera,
# back = walking away, side = profile drawn facing right, flipped for leftward travel)
MORAL = "튼튼한 집은 하나씩 정성껏 쌓아서 만들어요."

# ---------------------------------------------------------------- line adaptations
CHANGED = {}
# Trim narrator lead-ins ("엄마 돼지가 말했어요.", "첫째가 말했어요." …) — the speaking character is on the page and
# changes face; the kept segs reuse 톡톡's clips (nothing to record). ~9 s shorter.
SEG_KEEP = {
    1: [1],        # mom only
    23: [1, 2],    # piga teasing + "그래도 셋째는 천천히 벽돌을 쌓았어요."
    28: [1, 3],    # piga "싫어요, 싫어요!" + wolf "그럼 후~ 불어서 날려 버릴 테야!"
    32: [1, 3],    # pigb + wolf
}
NEW_LINES = {
    # same narrator voice as 톡톡 three_pigs (Annie); sun_wind's cover/replay lines are another narrator voice
    "tp_n01": [["nar", "그림책을 톡 눌러서 펼쳐 볼까요?", None, "[cheerful, inviting, warm]"]],
    "tp_n02": [["nar", "또 보고 싶으면 '다시 보기'를 톡!", None, "[cheerful, inviting]"]],
}
# Not used in the pop-up book (pace: ≈3:20 target; 톡톡 mini-games that the pages show instead of saying):
#  4-12 clothes quiz (the tap-each-pig intro shows who wears what), 13-17 fan/wind shop test (the build + huff beats show
#  how strong each material is), 26 used only once as the huff prompt, 30 (첫째 runs: shown), 35-39 "which house?"
#  quiz (cut for time; optional beat in PLAN.md), 40-42 inside count, 54 (53 already says he never came back).
DROPPED = {4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 30, 35, 36, 37, 38, 39, 40, 41, 45, 46, 54, 55, 56}

# Expression per line (wiring as data): role -> pose name (PLAN.md cast sheet).
# 2026-11-18 (user: "팝업북은 어떤 교육적인 요소보다는 그냥 동화의 전달에"): the book tells the tale — no counting
# lines (45 "몇 번 부는지 세어 봐요", 46 "여덟 번이나", 56 "하나, 둘, 셋!"), no plot-tapping ending (55), and the brick
# lines lose their "열 장": the existing clips are trimmed at their sentence pause (no new recording):
#   tp_024 nar_506a46173c.mp3 0-3.05 s -> nar_506a46173c_s1.mp3 "셋째는 벽돌로 집을 짓기로 했어요."
#   tp_025 nar_33372fce4a.mp3 2.70 s-end -> nar_33372fce4a_s2.mp3 "튼튼한 벽돌 집이 완성됐어요!"
# (ffmpeg -t 3.05 + 0.15 s fade-out / -ss 2.70 + 0.08 s fade-in, 128 kbps). tp_042 (셋째: "셋이서 함께라서 무섭지
# 않아!") is the brothers' answer to the huffing instead of the counted tp_046.
TRIM = {
    "tp_024": ("셋째는 벽돌로 집을 짓기로 했어요.", "res://audio/voice/three_pigs/nar_506a46173c_s1.mp3",
               "audio/el/nar_506a46173c.mp3 (trimmed 0-3.05 s)"),
    "tp_025": ("튼튼한 벽돌 집이 완성됐어요!", "res://audio/voice/three_pigs/nar_33372fce4a_s2.mp3",
               "audio/el/nar_33372fce4a.mp3 (trimmed 2.70 s-end)"),
}
# 2026-11-19 (user: "늑대가 그럼을 두 번 말하고"): the generated wolf clips start with a faint first "그럼" before the
# loud one (envelope: 0.09-0.35 s / 0.09-0.40 s, then a pause). Trimmed just before the loud onset, 40 ms fade-in:
#   wolf_2060345d9c.mp3 from 0.52 s -> wolf_2060345d9c_t.mp3 (tp_028)
#   wolf_61e2f65ffa.mp3 from 0.90 s -> wolf_61e2f65ffa_t.mp3 (tp_032, tp_044)
TRIM_SEG = {
    "tp_028": {1: ("res://audio/voice/three_pigs/wolf_2060345d9c_t.mp3", "wolf_2060345d9c.mp3 trimmed from 0.52 s")},
    "tp_032": {1: ("res://audio/voice/three_pigs/wolf_61e2f65ffa_t.mp3", "wolf_61e2f65ffa.mp3 trimmed from 0.90 s")},
    "tp_044": {1: ("res://audio/voice/three_pigs/wolf_61e2f65ffa_t.mp3", "wolf_61e2f65ffa.mp3 trimmed from 0.90 s")},
}
LINE_META = {
    # NEW lines tp_n01 / tp_n02: recorded 2026-11-19 after the user's OK (ElevenLabs, narrator voice, recorded.json)
    "tp_000": {"expr": {"pig_a": "calm", "pig_b": "calm", "pig_c": "calm", "mom": "calm"}},
    "tp_001": {"expr": {"mom": "talk"}},
    "tp_003": {"expr": {"mom": "wave", "pig_a": "back_walk", "pig_b": "back_walk", "pig_c": "back_walk"}},
    "tp_019": {"expr": {"pig_a": "carry_straw"}},
    "tp_020": {"expr": {"pig_a": "flute"}},
    "tp_021": {"expr": {"pig_b": "hammer"}},
    "tp_022": {"expr": {"pig_b": "violin"}},
    "tp_024": {"expr": {"pig_c": "lay_brick"}},
    "tp_023": {"expr": {"pig_a": "tease", "pig_b": "violin", "pig_c": "lay_brick"}},
    "tp_025": {"expr": {"pig_c": "proud"}},
    "tp_027": {"expr": {"wolf": ["sniff", "shout"]}},
    "tp_028": {"expr": {"pig_a": "defiant", "wolf": "shout"}},
    "tp_029": {"expr": {"pig_a": "scared", "wolf": "huff"}},
    "tp_031": {"expr": {"wolf": ["side_prowl", "shout"], "pig_a": "scared", "pig_b": "scared"}},
    "tp_032": {"expr": {"pig_a": "defiant", "pig_b": "defiant", "wolf": "shout"}},
    "tp_033": {"expr": {"pig_a": "scared", "pig_b": "scared"}},
    "tp_034": {"expr": {"pig_a": "run", "pig_b": "run"}},
    "tp_043": {"expr": {"wolf": ["side_prowl", "shout"], "pig_c": "brave"}},
    "tp_044": {"expr": {"pig_c": "defiant", "wolf": "shout"}},
    "tp_046": {"expr": {"pig_a": "happy_wave", "pig_b": "happy_wave", "pig_c": "proud", "wolf": "huff"}},
    "tp_042": {"expr": {"pig_c": "brave", "pig_a": "defiant", "pig_b": "defiant"}},
    "tp_047": {"expr": {"wolf": "exhausted"}},
    "tp_048": {"expr": {}},
    "tp_049": {"expr": {"pig_c": "brave", "pig_a": "calm", "pig_b": "calm"}},
    "tp_051": {"expr": {"wolf": "falling", "pig_a": "scared", "pig_b": "scared", "pig_c": "startled"}},
    "tp_052": {"expr": {"wolf": "ouch"}},
    "tp_053": {"expr": {"wolf": "run_away", "pig_a": "happy_wave", "pig_b": "happy_wave", "pig_c": "cheer"}},
    "tp_056": {"expr": {"pig_a": "happy_wave", "pig_b": "happy_wave", "pig_c": "cheer"}},
    "tp_057": {"expr": {"pig_a": "calm", "pig_b": "calm", "pig_c": "proud", "mom": "wave"}},
}

# ---------------------------------------------------------------- beats -> spreads
# spread: MeadowWorld seed + view; NEW optional fields (phase 2): "place" (named anchor on the template: home = village
# edge, straw_lot = wheat field edge, wood_lot = forest edge, brick_lot = village green), "set" (story cards placed on the
# spread by catalog id, with "stage" for house cards built in bands) and "light" (dusk).
# NEW verbs (phase 2, see PLAN.md "Runner work"): who/dir on walk + pose (several cast members), tap_each, build, huff,
# tap_steps (generalised `shine`: tap a target, one fx + lines per tap), climb, run_off.
HOUSE = {"straw": "story_houses_00", "wood": "story_houses_03", "brick": "story_houses_06"}  # fold bands: tools/atlas/house_stages.py
RUIN = {"straw": "story_houses_02", "wood": "story_houses_05"}
# Phase 2 (2026-11-18): live beats. Spots are [right, toward camera] from the page anchor (the template's start point
# on the road) in the template view's frame; set pieces stand at spots ("off" = extra [right, toward]); "stage" = bands
# standing at the page pop (0 = empty lot, popped later by build / fx). Ruins / kitchen / new houses wait at stage 0.
HANDLER = "res://stories/three_pigs/fx.gd"
BACKDROP = True  # the backdrop behind the hills takes the haze colour (no black sky on high / tilt-up shots)
# 2026-11-19 direction pass (user approved): a shot vocabulary; [distance, elevation°, focus height, fov, yaw offset°]
SHOTS = {"stage": [4.6, 13.0, 0.3, 20.0], "story": [3.7, 13.0, 0.28, 20.0], "close": [2.9, 12.0, 0.32, 20.0],
         "roof": [3.9, 12.0, 0.52, 20.0], "village": [6.6, 13.0, 0.34, 20.0],
         "crane_high": [8.0, 34.0, 0.3, 22.0, 0.0],      # opening crane start (high above the page)
         "establish": [9.5, 21.0, 0.25, 24.0, -6.0],     # the whole village, three lots along the road
         "high": [6.2, 30.0, 0.2, 22.0, 4.0],             # high angle: departures, the escape route reads
         "medium": [3.4, 11.0, 0.3, 20.0, 6.0],           # medium, slightly turned
         "two_shot": [2.6, 10.0, 0.3, 20.0, -8.0],        # the brothers' tease
         "face": [1.5, 7.0, 0.3, 20.0, 0.0],              # close-up on a character / a window face
         "window": [0.95, 6.0, 0.27, 20.0, 0.0],          # tight on one window: the peeking face fills the frame
         "front": [2.3, 7.0, 0.3, 20.0, 0.0],             # a whole house front (both windows), grass around it
         "low_up": [2.7, 3.5, 0.48, 22.0, -10.0],         # completion: low angle looking up at the house
         "low_wolf": [2.3, 4.0, 0.36, 22.0, 12.0],        # menacing low angle on the wolf
         "ots": [2.0, 9.0, 0.34, 22.0, -28.0],            # over the wolf's shoulder toward the house
         "cheeks": [1.25, 6.0, 0.42, 20.0, 8.0],          # close on the wolf's puffed cheeks
         "huff_two": [2.2, 7.0, 0.36, 22.0, 10.0],        # huff two-shot: the wolf's face foreground left, the house right
         "pull_back": [10.5, 26.0, 0.3, 24.0, 0.0],       # ending: the whole village
         # inside the brick house (camera just behind the closed front wall, looking at the hearth)
         "inside": [0.6, 5.0, 0.26, 68.0]}
CAST = {
    "pig_a": {"kind": "actor", "skin": "pig_a", "views": ["front", "side", "back"], "label": "첫째 (straw hat + scarf)"},
    "pig_b": {"kind": "actor", "skin": "pig_b", "views": ["front", "side", "back"], "label": "둘째 (blue overalls)"},
    "pig_c": {"kind": "actor", "skin": "pig_c", "views": ["front", "side", "back"], "label": "셋째 (white cap + red overalls)"},
    "mom": {"kind": "actor", "skin": "mother_pig", "views": ["front"], "label": "엄마 돼지"},
    "wolf": {"kind": "actor", "skin": "wolf", "views": ["front", "side", "back"], "label": "늑대"},
}
UI = {  # cover / end card pictures (cast ids) and caption speaker chips
    "cover": [["cast_pig_a_happy_wave", 190], ["cast_pig_b_happy_wave", 190], ["cast_pig_c_happy_wave", 190]],
    "end": [["cast_pig_a_happy_wave", 170], ["cast_pig_c_cheer", 190], ["cast_pig_b_happy_wave", 170]],
    "speakers": {"mom": ["엄마", "b8566b", "cast_mother_pig_calm"], "piga": ["첫째", "c58a1e", "cast_pig_a_calm"],
                 "pigb": ["둘째", "4f7fb0", "cast_pig_b_calm"], "pigc": ["셋째", "b5402f", "cast_pig_c_calm"],
                 "wolf": ["늑대", "6f6a66", "cast_wolf_calm"]},
}
KITCHEN = [  # the room INSIDE the brick house footprint (user 2026-11-19: "방이 열려도 앞 벽은 막혀있어야하는거아닌지":
    # the front wall never opens; the camera goes inside). Back wall at the rear, side walls edge-on to the outside
    # camera, two floor boards, the hearth against the back wall with its flue under the outside chimney, fire inside
    # the hearth, pot over it, table and shelf. Stood up by fx room_ready at the start of the chimney beat (hidden by
    # the closed facade from outside).
    {"card": "story_room_03", "at": "b_lot", "off": [0.0, -0.04], "stage": 0, "flat": True, "name": "k_floor", "clear": 0, "scale": 1.3},
    {"card": "story_room_03", "at": "b_lot", "off": [0.0, -0.4], "stage": 0, "flat": True, "name": "k_floor2", "clear": 0, "scale": 1.3},
    {"card": "story_room_00", "at": "b_lot", "off": [0.0, -0.74], "stage": 0, "name": "k_back", "clear": 0},
    {"card": "story_room_01", "at": "b_lot", "off": [-0.5, -0.2], "stage": 0, "name": "k_side_l", "clear": 0, "yaw": 90},
    {"card": "story_room_01", "at": "b_lot", "off": [-0.5, -0.53], "stage": 0, "name": "k_side_l2", "clear": 0, "yaw": 90},
    {"card": "story_room_02", "at": "b_lot", "off": [0.5, -0.2], "stage": 0, "name": "k_side_r", "clear": 0, "yaw": -90},
    {"card": "story_room_02", "at": "b_lot", "off": [0.5, -0.53], "stage": 0, "name": "k_side_r2", "clear": 0, "yaw": -90},
    # plank ceiling over the room, shown only while the camera is inside (from outside it could peek over the roof)
    {"card": "story_room_03", "at": "b_lot", "off": [0.0, -0.02], "stage": 0, "flat": True, "name": "k_ceil", "clear": 0,
     "scale": 1.3, "lift": 0.56, "inside_only": True},
    {"card": "story_room_03", "at": "b_lot", "off": [0.0, -0.4], "stage": 0, "flat": True, "name": "k_ceil2", "clear": 0,
     "scale": 1.3, "lift": 0.56, "inside_only": True},
    {"card": "story_room_04", "at": "b_lot", "off": [0.33, -0.71], "stage": 0, "name": "k_flue", "clear": 0, "lift": 0.36,
     "inside_only": True},  # shown only while the camera is inside (from outside it poked above the roof)
    {"card": "story_hearth_00", "at": "b_lot", "off": [0.33, -0.7], "stage": 0, "name": "k_hearth", "clear": 0},
    {"card": "story_hearth_05", "at": "b_lot", "off": [0.33, -0.685], "stage": 0, "name": "k_logs", "clear": 0, "scale": 0.8},
    {"card": "story_hearth_02", "at": "b_lot", "off": [0.33, -0.68], "stage": 0, "name": "fire", "clear": 0, "scale": 1.8},
    {"card": "story_hearth_03", "at": "b_lot", "off": [0.33, -0.678], "stage": 0, "name": "fire_m", "clear": 0, "scale": 1.8},
    {"card": "story_hearth_04", "at": "b_lot", "off": [0.33, -0.676], "stage": 0, "name": "fire_l", "clear": 0, "scale": 1.8},
    {"card": "story_hearth_01", "at": "b_lot", "off": [0.33, -0.6], "stage": 0, "name": "k_pot", "clear": 0, "lift": 0.06, "scale": 1.2},
    {"card": "story_hearth_12", "at": "b_lot", "off": [-0.36, -0.71], "stage": 0, "name": "k_table", "clear": 0},
    {"card": "story_hearth_14", "at": "b_lot", "off": [-0.22, -0.72], "stage": 0, "name": "k_shelf", "clear": 0, "scale": 1.6, "lift": 0.3},
]
# view 2: the stream runs diagonally just behind the anchor; the straw lot is on the near-left grass
STRAW_SPOTS = {"lot": [-1.1, -0.05], "pile": [-0.64, 0.26], "pig_a": [-0.48, 0.42], "wolf": [-1.72, 0.32],
               "pig_a_door": [-1.02, 0.1], "focus": [-1.2, 0.1],
               "wolf_focus": [-1.25, 0.12]}
# view 3 (2026-11-18 v2, user: "houses built across the road"): the road runs straight up the middle (x -0.2..0.4),
# the stream crosses the front; the wood lot is on the meadow right of the road, the wolf comes up the road
WOOD_SPOTS = {"lot": [1.0, -0.62], "pile": [1.85, -0.38], "pig_b": [1.62, -0.3], "pig_a": [1.88, -0.18],
              "wolf": [0.38, -0.12], "focus": [0.98, -0.38],
              "wolf_focus": [0.86, -0.3]}
# view 4 v2: the road climbs from the middle to the right (x -0.2..0.6); the brick lot is on the open meadow left of
# it (house x -1.43..-0.27), the pile and the wolf further left, the brothers peek out on the road side; kitchen
# spots (in_*) keep their offsets from the lot
BRICK_SPOTS = {"lot": [-0.85, -0.6], "pile": [-1.22, -0.12], "pig_c": [-0.1, -0.45], "tease": [-0.85, 0.16],
               "wolf": [-1.52, 0.02], "pig_a": [-0.12, -0.72], "pig_b": [0.06, -0.74], "lot_left": [-2.05, -1.3],
               "lot_right": [1.2, -1.2], "in_a": [-1.18, -1.2], "in_b": [-1.0, -1.19], "in_c": [-0.82, -1.18],
               "in_focus": [-0.82, -1.24],
               "wolf_land": [-1.8, 0.1], "mom": [-0.2, 0.02], "focus": [-0.75, -0.42], "village": [-0.45, -0.9],
               "brothers_in": [0.55, 0.2], "wolf_focus": [-0.95, -0.3], "out_a": [-1.15, -0.25], "out_b": [-0.92, -0.2], "out_c": [-0.62, -0.22]}
# 2026-11-19 ONE VILLAGE SPREAD (user: "책장 안넘기고 한번에 처리하는게 좋을거같음 카메라 무빙으로"): the three lots lie on
# one road in seed 1's world (the old views 2 / 3 / 4 were only camera stations on it), so the whole build and wolf
# story plays on view 3's page and the camera glides from house to house. The spot tables above (made per view) are
# converted into view 3's frame: world = anchor_v + right_v * r + toward_v * t (anchors measured with
# tools/story/probe_spots.gd-style probe, 2026-11-19).
import math as _m
_ANCH = {2: (-0.099081, -1.068278, 32.0), 3: (-0.608278, -2.273701, 26.0), 4: (-0.789233, -4.241362, 16.0)}


def _to3(v, rt):
    ax, az, y = _ANCH[v]
    y = _m.radians(y)
    wx = ax + _m.cos(y) * rt[0] + _m.sin(y) * rt[1]
    wz = az - _m.sin(y) * rt[0] + _m.cos(y) * rt[1]
    bx, bz, y3 = _ANCH[3]
    y3 = _m.radians(y3)
    dx, dz = wx - bx, wz - bz
    return [round(dx * _m.cos(y3) - dz * _m.sin(y3), 3), round(dx * _m.sin(y3) + dz * _m.cos(y3), 3)]


VILLAGE = {}
for _k, _v in STRAW_SPOTS.items():
    VILLAGE["s_" + _k] = _to3(2, _v)
for _k, _v in WOOD_SPOTS.items():
    VILLAGE["w_" + _k] = _to3(3, _v)
BRICK_SHIFT = [-0.5, -0.2]  # v10 (coordinator: the brick house sat right behind the wood house): the whole brick lot moved
for _k, _v in BRICK_SPOTS.items():
    _p = _to3(4, _v)
    VILLAGE[("b_" + _k) if _k in ("lot", "pile", "pig_c", "pig_a", "pig_b", "wolf", "focus", "wolf_focus") else _k] = [
        round(_p[0] + BRICK_SHIFT[0], 3), round(_p[1] + BRICK_SHIFT[1], 3)]
# where a runner stops: in front of each door (the door sits at the middle of the front on both houses)
VILLAGE["w_front"] = [VILLAGE["w_lot"][0], VILLAGE["w_lot"][1] + 0.3]
VILLAGE["b_front"] = [VILLAGE["b_lot"][0] + 0.1, VILLAGE["b_lot"][1] + 0.35]
VILLAGE["s_door"] = VILLAGE["s_pig_a_door"]
VILLAGE["w_door"] = VILLAGE["w_pig_b"]
VILLAGE["s_win"] = [round(VILLAGE["s_lot"][0] - 0.23, 3), VILLAGE["s_lot"][1]]  # the straw house's round window
for _h in ("s", "w"):  # between the wolf's mark and the house: the huff two-shot looks at both
    VILLAGE[_h + "_huff"] = [round(VILLAGE[_h + "_wolf"][0] * 0.55 + VILLAGE[_h + "_lot"][0] * 0.45, 3),
                             round(VILLAGE[_h + "_wolf"][1] * 0.55 + VILLAGE[_h + "_lot"][1] * 0.45 + 0.1, 3)]
VILLAGE["wolf_exit"] = [0.9, -6.6]   # far along the road beyond the brick house (probed road line)
VILLAGE["wolf_watch"] = [1.25, -4.6]    # where the camera stays and lets him go
VILLAGE["est"] = [round((VILLAGE["s_lot"][0] + VILLAGE["b_lot"][0]) * 0.5 + 0.3, 3),
                 round((VILLAGE["s_lot"][1] + VILLAGE["b_lot"][1]) * 0.5, 3)]
VILLAGE["ladder_find"] = [VILLAGE["b_lot"][0] - 1.12, VILLAGE["b_lot"][1] + 0.3]
VILLAGE["s_wolf_from"] = [VILLAGE["s_wolf"][0] - 0.75, VILLAGE["s_wolf"][1]]
# every camera station of the page (sightlines): the build / wolf shots at each lot, the roof and the escape tracking
VILLAGE_SIGHT = [["establish", "est"], ["medium", "s_focus"], ["medium", "b_focus"], ["low_up", "s_lot"],
                 ["low_up", "w_lot"], ["low_up", "b_lot"], ["ots", "s_wolf_focus"], ["ots", "w_wolf_focus"],
                 ["ots", "b_wolf_focus"], ["window", "s_win"], ["front", "w_lot"], ["huff_two", "s_huff"], ["huff_two", "w_huff"],
                 ["low_wolf", "s_wolf_from"], ["high", "road", "s_door", "w_front"], ["high", "road", "w_front", "b_front"],
                 ["story", "s_focus"], ["story", "s_wolf_focus"], ["story", "w_focus"], ["story", "w_wolf_focus"],
                 ["story", "b_focus"], ["story", "b_wolf_focus"], ["roof", "b_lot"], ["stage", "b_focus"],
                 ["story", "road", "s_door", "w_door"], ["story", "road", "w_door", "b_front"]]
VILLAGE_SET = [
    {"card": "story_houses_00", "at": "s_lot", "stage": 0, "name": "straw_house",
     # the house's body behind the front (user: "문열때보면 뒷편이 없는곳으로 가다보니 이상한디?"): straw walls, plank floor
     "box": {"depth": 0.5, "side": "story_houses_01", "inner": "story_houses_01", "floor": "story_room_03"}},
    {"card": "story_build_props_01", "at": "s_pile", "stage": 0, "name": "straw_pile", "scale": 1.6},
    {"card": "story_houses_02", "at": "s_lot", "off": [0.0, -0.18], "stage": 0, "name": "straw_ruin", "scale": 1.3},
    # the wood house's foundation (floor, sill, lower walls, door) stands from the start; the taps raise the rest
    {"card": "story_houses_03", "at": "w_lot", "stage": 0, "name": "wood_house", "scale": 1.0,
     "box": {"depth": 0.5, "side": "story_houses_04", "inner": "story_houses_04", "floor": "story_room_03"}},
    {"card": "story_build_props_05", "at": "w_pile", "stage": 0, "name": "wood_pile", "scale": 1.5},
    {"card": "story_houses_05", "at": "w_lot", "off": [0.0, -0.18], "stage": 0, "name": "wood_ruin", "scale": 1.0},
    {"card": "story_houses_06", "at": "b_lot", "stage": 0, "name": "house", "clear": 1.8,
     "box": {"depth": 0.78, "side": "story_houses_07", "inner": "story_room_00", "floor": "story_room_03"}},
    {"card": "story_build_props_08", "at": "b_pile", "stage": 0, "name": "brick_pile", "scale": 1.5},
    {"card": "story_build_props_13", "at": "b_pile", "off": [0.22, 0.05], "stage": 0, "name": "bucket"},
    # a ladder against the brick house's left wall under the eave (the wolf's way up in the chimney beat)
    {"card": "story_build_props_23", "at": "b_lot", "off": [-0.56, 0.06], "stage": 0, "name": "ladder", "scale": 1.7, "clear": 0},
    # ...lying in the grass beside the brick pile until the wolf finds it and stands it up (chimney beat)
    {"card": "story_build_props_23", "at": "b_lot", "off": [-1.0, 0.18], "flat": True, "name": "ladder_flat",
     "scale": 1.7, "clear": 0},
] + KITCHEN


def _village(**kw):
    sp = {"seed": 1, "view": 3, "place": "village", "spots": VILLAGE, "set": []}
    sp.update(kw)
    return sp


BEATS = [
    {"id": "cover", "title": "아기 돼지 삼형제", "spread": None, "steps": [{"do": "cover", "prompt": "tp_n01"}]},
    {"id": "home", "title": "엄마의 배웅", "spread": {"seed": 1, "view": 5, "place": "home",
     "spots": {"home_house": [0.55, -0.6], "mom": [0.3, -0.12], "pig_a": [-0.78, 0.12], "pig_b": [-0.54, 0.2],
               "pig_c": [-0.3, 0.16], "focus": [-0.12, -0.15]},
     # (user: "돼지 세 마리 갈 때 짚이랑 벽돌을 왜 가지고 있지?") no building materials at home: they choose them later
     "set": [{"card": "village_houses_20", "at": "home_house", "name": "home_house"}]},
     "enter": {"who": {"mom": "calm", "pig_a": "calm", "pig_b": "calm", "pig_c": "calm"}},
     "steps": [
        # opening: the camera cranes down from high over the page into the scene as it pops up
        {"do": "cam", "shot": "story", "from": "crane_high", "rate": 1.1, "wait": 0.4},
        {"do": "say", "line": "tp_000"},
        {"do": "pose", "who": "mom", "pose": "talk"},
        {"do": "cam", "shot": "face", "at": "mom", "wait": 0.3},
        {"do": "say", "line": "tp_001"},
        {"do": "cam", "shot": "medium", "wait": 0.2},
        # tap each piglet: it hops + waves, its building material (straw sheaf / planks / bricks) pops up beside it
        {"do": "tap_each", "targets": ["pig_a", "pig_b", "pig_c"], "prompt": "tp_002", "hint": "tp_002",
         "react": {"pig_a": ["happy_wave"], "pig_b": ["happy_wave"], "pig_c": ["happy_wave"]}},
        {"do": "pose", "who": "mom", "pose": "wave"},
        # they set off AWAY up the page (back views), mom waves; a high angle as they go down the road
        {"do": "cam", "shot": "high", "rate": 1.2, "wait": 0.1},
        {"do": "walk", "who": ["pig_a", "pig_b", "pig_c"], "dir": "away", "dist": 1.3, "speed": 0.2, "line": "tp_003"},
    ]},
    {"id": "straw_build", "title": "첫째의 짚 집",
     "spread": _village(set=VILLAGE_SET, focus="s_focus", sightlines=VILLAGE_SIGHT),
     "enter": {"who": {"pig_a": "carry_straw"}, "at": {"pig_a": "s_pig_a"}, "left": {"pig_a": 1}},
     "steps": [
        # the village: a wide establishing crane over the three empty lots along the road
        {"do": "cam", "shot": "establish", "at": "est", "from": "crane_high", "rate": 0.9, "wait": 1.8},
        {"do": "frame", "house": "straw_house", "with": ["straw_pile", "pig_a"], "wait": 0.8},
        {"do": "fx", "fx": "up:straw_pile", "wait": 0.5},  # his straw arrives at his lot as his build begins
        {"do": "say", "line": "tp_019"},
        # tap the straw pile x3: 첫째 carries straw to the lot, one band of the straw house folds up per tap
        {"do": "build", "house": "straw_house", "pile": "straw_pile", "target": "straw_pile", "taps": 3, "hint": "tp_018",
         "walker": "pig_a", "fx": "straw_pop", "gap": 0.5},
        {"do": "walk", "who": "pig_a", "to": "s_door", "speed": 0.3},
        {"do": "cam", "shot": "low_up", "at": "s_lot", "rate": 0.8},
        {"do": "fx", "fx": "star_burst"},
        {"do": "pose", "who": "pig_a", "pose": "flute"},
        {"do": "fx", "fx": "flute_notes"},
        {"do": "say", "line": "tp_020"},
        {"do": "fx", "fx": "music_stop", "wait": 0.5},
    ]},
    {"id": "wood_build", "title": "둘째의 나무 집", "spread": _village(light="afternoon", built=["straw_house", "straw_pile"]),
     "enter": {"who": {"pig_b": "hammer"}, "at": {"pig_b": "w_pig_b"}, "keep": ["pig_a"]},
     "steps": [
        # the camera glides along the road to the wood lot (no page turn)
        {"do": "frame", "house": "wood_house", "with": ["wood_pile", "pig_b"], "wait": 1.0},
        {"do": "fx", "fx": "up:wood_pile", "wait": 0.3},
        {"do": "fx", "fx": "up:wood_house:1", "wait": 0.6},  # the foundation rises as his build begins
        {"do": "say", "line": "tp_021"},
        {"do": "build", "house": "wood_house", "pile": "wood_pile", "target": "wood_house", "taps": 3, "walker": "pig_b",
         "fx": "hammer_bang", "gap": 0.5},
        {"do": "cam", "shot": "low_up", "at": "w_lot", "rate": 0.8},
        {"do": "fx", "fx": "star_burst"},
        {"do": "pose", "who": "pig_b", "pose": "violin"},
        {"do": "fx", "fx": "violin_notes"},
        {"do": "say", "line": "tp_022"},
        {"do": "fx", "fx": "music_stop", "wait": 0.5},
    ]},
    {"id": "brick_build", "title": "셋째의 벽돌 집", "spread": _village(light="late", built=["straw_house", "straw_pile", "wood_house", "wood_pile"]),
     "enter": {"who": {"pig_c": "lay_brick"}, "at": {"pig_c": "b_pig_c"}, "keep": ["pig_a", "pig_b"]},
     "steps": [
        # brick: slower and careful, the light warming toward late afternoon
        {"do": "frame", "house": "house", "with": ["brick_pile", "pig_c", "tease"], "wait": 1.0},
        {"do": "fx", "fx": "up:brick_pile", "wait": 0.2},
        {"do": "fx", "fx": "up:bucket", "wait": 0.4},
        {"do": "say", "line": "tp_024"},
        # the brothers stroll along the road from their houses and tease (tp_023), then wander home
        {"do": "build", "house": "house", "pile": "brick_pile", "target": "house", "taps": 3, "walker": "pig_c",
         "fx": "brick_thunk", "gap": 0.6,
         "steps": [{"at": 1, "fx": "brothers_tease"}, {"at": 2, "wait_for": ["pig_a"], "lines": ["tp_023"]},
                   {"at": 3, "fx": "brothers_leave"}]},  # they stroll in during the 2nd brick, tease once in frame
        {"do": "cam", "shot": "low_up", "at": "b_lot", "rate": 0.6},
        {"do": "fx", "fx": "star_burst"},
        {"do": "pose", "who": "pig_c", "pose": "proud"},
        {"do": "say", "line": "tp_025"},
    ]},
    {"id": "wolf_straw", "title": "후~ 짚 집", "spread": _village(light="afternoon", built=["straw_house", "wood_house", "house", "straw_pile", "wood_pile", "brick_pile", "bucket"]),
     # at home: 첫째 at his round window, 둘째 at home in the wood house, 셋째 in the brick house
     "enter": {"who": {"pig_a": "calm", "pig_b": "calm", "pig_c": "brave"},
               "inside": {"pig_a": ["straw_house", 0], "pig_b": ["wood_house", 1], "pig_c": ["house", 0]}},
     "steps": [
        # the wolf's first entrance: low and menacing, he comes out of the trees
        # (2026-11-22, "시점이 뚝뚝 끊기는거 별로에요": no cut) a crane up over the roofs at the brick lot, across the
        # village high, and down low on the wolf (a low glide across the village flew through the straw roof)
        {"do": "cam", "shot": "high", "at": "b_lot", "rate": 2.0, "wait": 0.6},
        {"do": "cam", "shot": "high", "at": "s_wolf_from", "rate": 1.6, "wait": 1.1},
        {"do": "cam", "shot": "low_wolf", "at": "s_wolf_from", "rate": 1.6, "wait": 1.2},
        # he prowls in (drawn sneak cycle), the camera follows him to his mark; there he stops and sniffs (킁킁)
        {"do": "walk", "who": "wolf", "dir": "right", "to": "s_wolf", "from": "s_wolf_from", "pose": "side_prowl",
         "speed": 0.25, "follow": "wolf", "shot": "low_wolf", "line": "tp_027", "segs": [0], "line_late": True,
         "end_pose": "sniff"},
        # over his shoulder toward the straw house ("문 열어라")
        {"do": "cam", "shot": "ots", "at": "s_wolf_focus", "rate": 3.0, "wait": 0.15},
        {"do": "pose", "who": "wolf", "pose": "shout", "wait": 0.1},
        {"do": "say", "line": "tp_027", "segs": [1]},
        {"do": "pose", "who": "pig_a", "pose": "defiant"},
        # reverse: the face at the window ("싫어요")
        {"do": "cam", "shot": "window", "at": "s_win", "rate": 2.6, "wait": 0.1},
        {"do": "say", "line": "tp_028", "segs": [0]},
        # the huffs: close on his puffed cheeks, a shake on every tap, cut wide for the house blowing away
        # (SPEAKER_OFF 2026-11-22: his threat is said on his face, not on the window)
        {"do": "cam", "shot": "huff_two", "at": "s_huff", "rate": 3.0, "wait": 0.2, "settle": 0.5},
        {"do": "say", "line": "tp_028", "segs": [1]},
        # tap the wolf x3: the roof goes, the walls rock, the 3rd blows it all apart; 첫째 stands in the heap
        {"do": "huff", "house": "straw_house", "taps": 3, "prompt": "tp_026", "hint": "tp_026", "result": "blow_apart",
         "ruin": "story_houses_02", "fx": "straw_fly", "gap": 0.7, "cam_result": "story", "cam_result_at": "s_wolf_focus"},
        {"do": "say", "line": "tp_029"},
        # ESCAPE: he runs along the road to the wood house, the camera follows, in through the door, it shuts
        {"do": "walk", "who": "pig_a", "to": "w_front", "via": "road", "pose": "run", "speed": 0.8, "follow": "pig_a", "shot": "high"},
        {"do": "cam", "shot": "story", "at": "w_focus", "wait": 0.2},
        {"do": "go_inside", "who": ["pig_a"], "house": "wood_house", "windows": [0], "speed": 0.45},
    ]},
    {"id": "wolf_wood", "title": "후~ 나무 집", "spread": _village(light="late", built=["straw_ruin", "wood_house", "house", "straw_pile", "wood_pile", "brick_pile", "bucket"]),
     "enter": {"who": {}, "keep": ["pig_a", "pig_b", "pig_c", "wolf"]},
     "steps": [
        # the wolf follows along the road to the wood house
        {"do": "walk", "who": "wolf", "to": "w_wolf", "via": "road", "pose": "side_prowl", "speed": 0.95, "follow": "wolf",
         "line": "tp_031", "segs": [0], "line_late": True},
        {"do": "cam", "shot": "ots", "at": "w_wolf_focus", "rate": 3.0, "wait": 0.15},
        {"do": "pose", "who": "wolf", "pose": "shout", "wait": 0.1},
        {"do": "say", "line": "tp_031", "segs": [1]},
        {"do": "pose", "who": ["pig_a", "pig_b"], "pose": "defiant"},
        {"do": "cam", "shot": "front", "at": "w_lot", "rate": 2.6, "wait": 0.1},
        {"do": "say", "line": "tp_032", "segs": [0]},
        {"do": "cam", "shot": "huff_two", "at": "w_huff", "rate": 3.0, "wait": 0.2, "settle": 0.5},  # SPEAKER_OFF
        {"do": "say", "line": "tp_032", "segs": [1]},
        {"do": "huff", "house": "wood_house", "taps": 3, "result": "collapse", "ruin": "story_houses_05",
         "fx": "wood_wobble", "gap": 0.7, "cam_result": "story", "cam_result_at": "w_wolf_focus"},
        {"do": "say", "line": "tp_033"},
        # ESCAPE: both run along the road to the brick house, the camera follows; in through the door
        {"do": "walk", "who": ["pig_a", "pig_b"], "to": "b_front", "via": "road", "pose": "run", "speed": 0.8,
         "follow": "pig_a", "shot": "high", "line": "tp_034"},
        {"do": "cam", "shot": "story", "at": "b_focus", "wait": 0.2},
        {"do": "go_inside", "who": ["pig_a", "pig_b"], "house": "house", "windows": [1, -1], "speed": 0.45},
    ]},
    {"id": "brick_wolf", "title": "쿵쿵쿵!", "spread": _village(light="dusk", built=["straw_ruin", "wood_ruin", "house", "straw_pile", "wood_pile", "brick_pile", "bucket"]),
     "enter": {"who": {}, "keep": ["pig_a", "pig_b", "pig_c", "wolf"]},
     "steps": [
        {"do": "walk", "who": "wolf", "to": "b_wolf", "via": "road", "pose": "side_prowl", "speed": 0.95, "follow": "wolf",
         "line": "tp_043", "segs": [0], "line_late": True},
        {"do": "cam", "shot": "ots", "at": ["b_wolf_focus", "b_wolf_focus", "b_wolf"], "rate": 3.0, "wait": 0.15},  # his shoulder in frame (SPEAKER_OFF)
        {"do": "pose", "who": "wolf", "pose": "shout", "wait": 0.1},
        {"do": "say", "line": "tp_043", "segs": [1]},
        {"do": "say", "line": "tp_044"},
        # the brick house holds: a frontal, steady shot; the wolf huffs and puffs at the left edge
        {"do": "cam", "shot": "stage", "at": "b_focus", "rate": 2.0, "wait": 0.2},
        # tap the wolf x3: 후~ every time, the brick house only shivers; the brothers bob in the windows
        {"do": "huff", "house": "house", "taps": 3, "result": "hold", "fx": "brick_huff", "gap": 0.6, "shake": 0.25},
        {"do": "say", "line": "tp_042"},
        {"do": "pose", "who": "wolf", "pose": "exhausted"},
        {"do": "fx", "fx": "thud_dust"},
        {"do": "cam", "shot": "medium", "at": "b_wolf", "rate": 1.2, "wait": 0.1},
        {"do": "say", "line": "tp_047"},
    ]},
    {"id": "chimney", "title": "보글보글", "spread": _village(light="night", built=["straw_ruin", "wood_ruin", "house", "straw_pile", "wood_pile", "brick_pile", "bucket"]),
     # the house stays CLOSED (it protects them); the room stands behind the wall
     "enter": {"who": {"wolf": "side_prowl"}, "left": {"wolf": 0}, "keep": ["pig_a", "pig_b", "pig_c"]},
     "steps": [
        {"do": "fx", "fx": "room_ready", "wait": 0.1},
        {"do": "cam", "shot": "roof", "at": "b_lot", "wait": 0.6},
        # he finds the ladder lying in the grass and stands it up against the wall under the eave
        {"do": "walk", "who": "wolf", "to": "ladder_find", "dir": "right", "pose": "side_prowl", "speed": 0.3, "follow": "wolf",
         "shot": "roof"},
        {"do": "cam", "shot": "roof", "at": "b_lot", "wait": 0.3},
        {"do": "fx", "fx": "ladder_up", "wait": 0.7},
        # he walks to the ladder, climbs it (back view), walks up the roof slope and along the ridge (side view),
        # steps onto the chimney top and sinks into it
        {"do": "climb", "who": "wolf", "on": "house", "pose": "side_prowl", "speed": 0.16, "line": "tp_048", "sink": True,
         "path": [[-1.05, 0.0, 0.12], [-0.62, 0.0, 0.12], [-0.62, 0.53, 0.12], [-0.52, 0.64, 0.07],
                  [-0.33, 0.86, 0.07], [0.22, 0.86, 0.07], [0.33, 1.0, 0.03]]},
        # into the house only now: the camera glides in through the front (nothing folds or pops)
        {"do": "fx", "fx": "inside_view", "wait": 2.2},
        {"do": "say", "line": "tp_049"},
        {"do": "tap_steps", "target": "fire", "prompt": "tp_050", "hint": "tp_050", "steps": [
            {"fx": "flame_m"}, {"target": "fire_m", "fx": "flame_l"}, {"target": "fire_l", "fx": "boil"}]},
        {"do": "fx", "fx": "wolf_drop", "wait": 0.6},
        {"do": "say", "line": "tp_051"},
        {"do": "fx", "fx": "splash"},
        {"do": "pose", "who": "wolf", "pose": "ouch"},
        {"do": "cam", "shot": "inside", "at": "in_focus", "shake": 2.2, "wait": 0.1},
        {"do": "say", "line": "tp_052"},
        # back out to the closed house; he shoots out of the chimney and runs off LEFT
        {"do": "fx", "fx": "outside_view", "wait": 1.6},
        # he flies out of the chimney: the camera tilts up after him into the sky, far away
        {"do": "fx", "fx": "wolf_launch", "wait": 0.1},
        {"do": "cam", "shot": "high", "follow": "wolf", "rate": 2.2, "wait": 1.6},
        {"do": "fx", "fx": "", "wait": 0.45},  # he lands (thud, dust, hop) before he runs
        # (user: "마지막에 늑대가 도망가서 달려야 되지 않을까?") he lands beside the house (thud, dust, hop) and runs off
        # along the road away from the village, scalded and smoking; the camera follows him, then lets him go
        {"do": "walk", "who": "wolf", "to": "wolf_exit", "path": [[0.3, -2.05], [1.1, -2.3], [1.45, -3.05], [1.48, -3.9],
                                                                    [1.3, -4.7], [1.1, -5.6], [0.9, -6.6]],
         "pose": "run_away", "speed": 0.75, "line": "tp_053",
         "exit": True, "follow": "wolf", "shot": "high", "follow_for": 3.6, "release_shot": "village", "release_at": "wolf_watch"},
    ]},
    {"id": "ending", "title": "벽돌 집", "spread": _village(light="evening", built=["straw_ruin", "wood_ruin", "house", "ladder", "straw_pile", "wood_pile", "brick_pile", "bucket"]),
     # the wolf is gone: the brothers come out in front of the brick house, safe and happy, mom joins them
     "enter": {"who": {"pig_a": "happy_wave", "pig_b": "happy_wave", "pig_c": "cheer", "mom": "wave"},
               "at": {"pig_a": "out_a", "pig_b": "out_b", "pig_c": "out_c", "mom": "mom"}},
     "steps": [
        {"do": "fx", "fx": "windows_lit", "wait": 0.0},
        {"do": "cam", "shot": "medium", "at": "b_focus", "rate": 1.4},
        {"do": "fx", "fx": "pigs_cheer", "wait": 0.6},
        # the family stays readable in front of the lit house for the last line, then a slow pull-back to the whole
        # village, and the book closes into the end card
        {"do": "say", "line": "tp_057"},
        {"do": "fx", "fx": "pigs_cheer", "wait": 0.2},
        {"do": "cam", "shot": "pull_back", "at": "est", "rate": 0.5, "wait": 3.2},
        {"do": "end", "after": "tp_n02", "close_book": True},
    ]},
]


# ---------------------------------------------------------------- sound (2026-11-19, artifacts/audio_staging/WIRING.md)
# Tale-level `sound` and per-beat blocks come from tools/audio/three_pigs_sound_blocks.json (the sound pass's
# proposal, kept as the single source); ids refer to game/audio/sound_catalog.json.
import json as _json, os as _os
_SB = _json.load(open(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "..", "audio",
                                    "three_pigs_sound_blocks.json"), encoding="utf-8"))
SOUND = {k: v for k, v in _SB["tale_sound"].items() if not k.endswith("_note")}
for _b in BEATS:
    _blk = _SB["beats"].get(_b["id"])
    if _blk:
        _b["sound"] = {k: v for k, v in _blk.items() if k != "note"}
SOUND["fx"]["wolf_land"] = ["wolf.flop", {"sound": "wolf.yelp_far", "gain_db": 4, "delay": 0.1}]  # landing thud + yelp
SOUND["fx"].update({"up:straw_pile": "ui.pop", "up:wood_pile": "ui.pop", "up:brick_pile": "ui.pop", "up:bucket": "ui.pop",
                    "up:wood_house:1": "build.hammer"})
