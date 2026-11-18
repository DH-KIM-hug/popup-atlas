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
SHOTS = {"stage": [4.6, 13.0, 0.3, 20.0], "story": [3.7, 13.0, 0.28, 20.0], "close": [2.9, 12.0, 0.32, 20.0],
         "roof": [5.0, 13.0, 0.62, 20.0], "village": [6.6, 13.0, 0.34, 20.0]}
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
KITCHEN = [  # brick house interior (chimney beat): a pop-up ROOM (story_room sheet) that folds up as the front wall
    # folds down (user 2026-11-19: "벽돌집. 그럼 집 뒤편도 있어야하지않을까유"): back wall, two side walls angled in like a
    # pop-up box, a plank floor, the hearth set against the back wall with its flue running up into the roof under the
    # outside chimney; logs, fire and the pot over it; table and shelf on the floor. Popped by cutaway_open (k_* / fire).
    {"card": "story_room_03", "at": "lot", "off": [0.0, -0.02], "stage": 0, "flat": True, "name": "k_floor", "clear": 0, "scale": 1.3},
    {"card": "story_room_00", "at": "lot", "off": [0.0, -0.36], "stage": 0, "name": "k_back", "clear": 0},
    {"card": "story_room_01", "at": "lot", "off": [-0.5, -0.2], "stage": 0, "name": "k_side_l", "clear": 0, "yaw": 62},
    {"card": "story_room_02", "at": "lot", "off": [0.5, -0.2], "stage": 0, "name": "k_side_r", "clear": 0, "yaw": -62},
    {"card": "story_room_04", "at": "lot", "off": [0.33, -0.31], "stage": 0, "name": "k_flue", "clear": 0, "lift": 0.36},
    {"card": "story_hearth_00", "at": "lot", "off": [0.33, -0.3], "stage": 0, "name": "k_hearth", "clear": 0},
    # logs and fire inside the hearth's arched opening (just in front of the hearth card), the pot hanging over them
    {"card": "story_hearth_05", "at": "lot", "off": [0.33, -0.285], "stage": 0, "name": "k_logs", "clear": 0, "scale": 0.8},
    {"card": "story_hearth_02", "at": "lot", "off": [0.33, -0.28], "stage": 0, "name": "fire", "clear": 0, "scale": 1.8},
    {"card": "story_hearth_03", "at": "lot", "off": [0.33, -0.278], "stage": 0, "name": "fire_m", "clear": 0, "scale": 1.8},
    {"card": "story_hearth_04", "at": "lot", "off": [0.33, -0.276], "stage": 0, "name": "fire_l", "clear": 0, "scale": 1.8},
    {"card": "story_hearth_01", "at": "lot", "off": [0.33, -0.2], "stage": 0, "name": "k_pot", "clear": 0, "lift": 0.06, "scale": 1.2},
    {"card": "story_hearth_12", "at": "lot", "off": [-0.3, -0.22], "stage": 0, "name": "k_table", "clear": 0},
    {"card": "story_hearth_14", "at": "lot", "off": [-0.22, -0.33], "stage": 0, "name": "k_shelf", "clear": 0, "scale": 1.6, "lift": 0.3},
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
               "lot_right": [1.2, -1.2], "in_a": [-1.17, -0.72], "in_b": [-0.97, -0.7], "in_c": [-0.79, -0.68],
               "wolf_land": [-1.8, 0.1], "mom": [-0.2, 0.02], "focus": [-0.75, -0.42], "village": [-0.45, -0.9],
               "brothers_in": [0.55, 0.2], "wolf_focus": [-0.95, -0.3], "out_a": [-1.15, -0.25], "out_b": [-0.92, -0.2], "out_c": [-0.62, -0.22]}
BEATS = [
    {"id": "cover", "title": "아기 돼지 삼형제", "spread": None, "steps": [{"do": "cover", "prompt": "tp_n01"}]},
    {"id": "home", "title": "엄마의 배웅", "spread": {"seed": 1, "view": 5, "place": "home",
     "spots": {"home_house": [0.55, -0.6], "mom": [0.3, -0.12], "pig_a": [-0.78, 0.12], "pig_b": [-0.54, 0.2],
               "pig_c": [-0.3, 0.16], "focus": [-0.12, -0.15]},
     "set": [{"card": "village_houses_20", "at": "home_house", "name": "home_house"},
             {"card": "story_build_props_00", "at": "pig_a", "off": [-0.13, -0.05], "stage": 0, "name": "mat_a", "scale": 0.9},
             {"card": "story_build_props_07", "at": "pig_b", "off": [-0.1, -0.06], "stage": 0, "name": "mat_b", "scale": 0.9},
             {"card": "story_build_props_08", "at": "pig_c", "off": [-0.12, -0.06], "stage": 0, "name": "mat_c", "scale": 0.9}]},
     "enter": {"who": {"mom": "calm", "pig_a": "calm", "pig_b": "calm", "pig_c": "calm"}},
     "steps": [
        {"do": "cam", "shot": "story"},
        {"do": "say", "line": "tp_000"},
        {"do": "pose", "who": "mom", "pose": "talk"},
        {"do": "say", "line": "tp_001"},
        # tap each piglet: it hops + waves, its building material (straw sheaf / planks / bricks) pops up beside it
        {"do": "tap_each", "targets": ["pig_a", "pig_b", "pig_c"], "prompt": "tp_002", "hint": "tp_002",
         "react": {"pig_a": ["happy_wave", "pop:story_build_props_00"], "pig_b": ["happy_wave", "pop:story_build_props_07"],
                   "pig_c": ["happy_wave", "pop:story_build_props_08"]}},
        {"do": "pose", "who": "mom", "pose": "wave"},
        # they set off AWAY up the page (back views), mom waves
        {"do": "walk", "who": ["pig_a", "pig_b", "pig_c"], "dir": "away", "dist": 1.3, "speed": 0.2, "line": "tp_003"},
    ]},
    {"id": "straw_build", "title": "첫째의 짚 집", "spread": {"seed": 1, "view": 2, "place": "straw_lot",
     "spots": STRAW_SPOTS,
     "set": [{"card": "story_houses_00", "at": "lot", "stage": 0, "name": "house"},
             {"card": "story_build_props_01", "at": "pile", "name": "pile", "scale": 1.6}]},
     "enter": {"who": {"pig_a": "carry_straw"}, "left": {"pig_a": 1}},
     "steps": [
        {"do": "cam", "shot": "story", "wait": 1.2},
        {"do": "say", "line": "tp_019"},
        # tap the straw pile x3: 첫째 carries straw to the lot, one band of the straw house folds up per tap
        {"do": "build", "house": "house", "target": "pile", "taps": 3, "hint": "tp_018", "walker": "pig_a",
         "fx": "straw_pop", "gap": 0.6},
        {"do": "walk", "who": "pig_a", "to": "pig_a_door", "speed": 0.3},
        {"do": "fx", "fx": "star_burst"},
        {"do": "pose", "who": "pig_a", "pose": "flute"},
        {"do": "fx", "fx": "flute_notes"},
        {"do": "say", "line": "tp_020"},
        {"do": "fx", "fx": "music_stop", "wait": 0.8},
    ]},
    {"id": "wood_build", "title": "둘째의 나무 집", "spread": {"seed": 1, "view": 3, "place": "wood_lot",
     "spots": WOOD_SPOTS,
     # the foundation (floor, sill and door frame) stands when the page opens; 5 taps raise the walls and roof
     "set": [{"card": "story_houses_03", "at": "lot", "stage": 1, "name": "house", "scale": 1.0},
             {"card": "story_build_props_05", "at": "pile", "name": "pile", "scale": 1.5}]},
     "enter": {"who": {"pig_b": "hammer"}},
     "steps": [
        {"do": "cam", "shot": "story", "wait": 1.2},
        {"do": "say", "line": "tp_021"},
        # tap the house x5: bang! a plank flies from the stack, a plank band folds up per tap
        {"do": "build", "house": "house", "target": "house", "taps": 3, "walker": "pig_b", "fx": "hammer_bang",
         "gap": 0.5},
        {"do": "fx", "fx": "star_burst"},
        {"do": "pose", "who": "pig_b", "pose": "violin"},
        {"do": "fx", "fx": "violin_notes"},
        {"do": "say", "line": "tp_022"},
        {"do": "fx", "fx": "music_stop", "wait": 0.8},
    ]},
    {"id": "brick_build", "title": "셋째의 벽돌 집", "spread": {"seed": 1, "view": 4, "place": "brick_lot",
     "spots": BRICK_SPOTS,
     "set": [{"card": "story_houses_06", "at": "lot", "stage": 0, "name": "house"},
             {"card": "story_build_props_08", "at": "pile", "name": "pile", "scale": 1.5},
             {"card": "story_build_props_13", "at": "pile", "off": [0.22, 0.05], "name": "bucket"}]},
     "enter": {"who": {"pig_c": "lay_brick"}},
     "steps": [
        {"do": "cam", "shot": "story", "wait": 1.2},
        {"do": "say", "line": "tp_024"},
        # tap x10, counted on the page: a brick flies onto the wall each tap, every 2nd tap a brick band folds up;
        # at tap 5 the brothers stroll in from the left and tease (tp_023), at 7 they wander off
        {"do": "build", "house": "house", "target": "house", "taps": 3, "walker": "pig_c", "fx": "brick_thunk",
         "gap": 0.45, "steps": [{"at": 2, "fx": "brothers_tease", "lines": ["tp_023"]}, {"at": 3, "fx": "brothers_leave"}]},
        {"do": "fx", "fx": "star_burst"},
        {"do": "pose", "who": "pig_c", "pose": "proud"},
        {"do": "say", "line": "tp_025"},
    ]},
    {"id": "wolf_straw", "title": "후~ 짚 집", "spread": {"seed": 1, "view": 2, "place": "straw_lot",
     "spots": STRAW_SPOTS,
     "set": [{"card": "story_houses_00", "at": "lot", "stage": "full", "name": "house"},
             {"card": "story_houses_02", "at": "lot", "off": [0.0, -0.18], "stage": 0, "name": "ruin", "scale": 1.3}]},
     # at home: 첫째 peeks out of the round window (he answers from inside); the heap lands behind him
     "enter": {"who": {"pig_a": "calm"}, "inside": {"pig_a": ["house", 0]}},
     "steps": [
        {"do": "cam", "shot": "story", "at": "wolf_focus"},
        # the wolf prowls in from the left, sniffing (side view, facing right)
        {"do": "walk", "who": "wolf", "dir": "right", "to": "wolf", "dist": 0.75, "pose": "sniff", "speed": 0.2, "line": "tp_027"},
        {"do": "pose", "who": "wolf", "pose": "shout"},
        {"do": "pose", "who": "pig_a", "pose": "defiant"},
        {"do": "say", "line": "tp_028"},
        # tap the wolf x3: each tap = one 후~; the straw bands peel off from the top, the 3rd blows it all apart
        {"do": "huff", "house": "house", "taps": 3, "prompt": "tp_026", "hint": "tp_026", "result": "blow_apart",
         "ruin": "story_houses_02", "fx": "straw_fly", "gap": 0.7},
        {"do": "say", "line": "tp_029"},
        # he runs off toward the reader (front view, scared face), out of the page
        {"do": "walk", "who": "pig_a", "dir": "toward", "pose": "scared", "dist": 1.3, "speed": 0.45, "exit": True},
    ]},
    {"id": "wolf_wood", "title": "후~ 나무 집", "spread": {"seed": 1, "view": 3, "place": "wood_lot",
     "spots": WOOD_SPOTS,
     "set": [{"card": "story_houses_03", "at": "lot", "stage": "full", "name": "house", "scale": 1.0},
             {"card": "story_houses_05", "at": "lot", "off": [0.0, -0.18], "stage": 0, "name": "ruin", "scale": 1.0}]},
     # at home: both brothers peek out of the two windows
     "enter": {"who": {"pig_a": "scared", "pig_b": "calm"}, "inside": {"pig_a": ["house", 0], "pig_b": ["house", 1]}},
     "steps": [
        {"do": "cam", "shot": "story", "at": "wolf_focus"},
        {"do": "walk", "who": "wolf", "dir": "right", "to": "wolf", "dist": 0.6, "pose": "side_prowl", "speed": 0.2, "line": "tp_031"},
        {"do": "pose", "who": "wolf", "pose": "shout"},
        {"do": "pose", "who": ["pig_a", "pig_b"], "pose": "defiant"},
        {"do": "say", "line": "tp_032"},
        # tap the wolf x5: the wood house rocks harder each time (흔들흔들), the 5th knocks it down
        {"do": "huff", "house": "house", "taps": 3, "result": "collapse", "ruin": "story_houses_05",
         "fx": "wood_wobble", "gap": 0.7},
        {"do": "say", "line": "tp_033"},
        {"do": "walk", "who": ["pig_a", "pig_b"], "dir": "right", "pose": "run", "dist": 1.8, "speed": 0.5,
         "line": "tp_034", "exit": True},
    ]},
    {"id": "brick_wolf", "title": "쿵쿵쿵!", "spread": {"seed": 1, "view": 4, "place": "brick_lot", "light": "dusk",
     "spots": BRICK_SPOTS,
     "set": [{"card": "story_houses_06", "at": "lot", "stage": "full", "name": "house"},
             # a ladder against the left wall under the eave (the wolf's way up in the chimney beat)
             {"card": "village_props_30", "at": "lot", "off": [-0.56, 0.06], "name": "ladder", "scale": 1.7, "clear": 0}]
            + KITCHEN},
     # 셋째 is at home (left window); his brothers come running up the road and in through the door (right window)
     "enter": {"who": {"pig_c": "brave"}, "inside": {"pig_c": ["house", 0]}},
     "steps": [
        {"do": "cam", "shot": "story", "at": "wolf_focus"},
        {"do": "go_inside", "who": ["pig_a", "pig_b"], "house": "house", "from": "brothers_in", "windows": [1, 1],
         "speed": 0.45},
        {"do": "walk", "who": "wolf", "dir": "right", "to": "wolf", "dist": 0.6, "pose": "side_prowl", "speed": 0.2, "line": "tp_043"},
        {"do": "pose", "who": "wolf", "pose": "shout"},
        {"do": "say", "line": "tp_044"},
        # tap the wolf x3: 후~ every time, the brick house only shivers; the brothers bob in the windows
        {"do": "huff", "house": "house", "taps": 3, "result": "hold", "fx": "brick_huff", "gap": 0.6},
        {"do": "say", "line": "tp_042"},
        {"do": "pose", "who": "wolf", "pose": "exhausted"},
        {"do": "fx", "fx": "thud_dust"},
        {"do": "say", "line": "tp_047"},
    ]},
    {"id": "chimney", "title": "보글보글", "spread": {"seed": 1, "view": 4, "place": "brick_lot", "light": "dusk",
     "spots": BRICK_SPOTS, "set": []},
     "enter": {"who": {"wolf": "side_prowl"}, "left": {"wolf": 0}},
     "steps": [
        # the page opens the house first (user: "그전에 집이 올라와있어도 문제없지않나"): the front wall folds down, the
        # room pops up with the pigs inside at the hearth; the camera frames the room and the roof together
        {"do": "cam", "shot": "roof", "at": "lot", "wait": 0.2},
        {"do": "fx", "fx": "cutaway_open", "wait": 1.4},
        # he walks to the ladder, climbs it (back view), tiptoes up the roof slope and along the ridge (side view),
        # steps onto the chimney top and sinks into it
        {"do": "climb", "who": "wolf", "on": "house", "pose": "side_prowl", "speed": 0.16, "line": "tp_048", "sink": True,
         "path": [[-1.05, 0.0, 0.12], [-0.62, 0.0, 0.12], [-0.62, 0.53, 0.12], [-0.52, 0.64, 0.07],
                  [-0.33, 0.86, 0.07], [0.22, 0.86, 0.07], [0.33, 1.0, 0.03]]},
        {"do": "cam", "shot": "close", "at": "lot"},
        {"do": "say", "line": "tp_049"},
        # tap the fire x3: small -> medium -> large flame, the pot steams and bubbles
        {"do": "tap_steps", "target": "fire", "prompt": "tp_050", "hint": "tp_050", "steps": [
            {"fx": "flame_m"}, {"target": "fire_m", "fx": "flame_l"}, {"target": "fire_l", "fx": "boil"}]},
        {"do": "fx", "fx": "wolf_drop", "wait": 0.6},
        {"do": "say", "line": "tp_051"},
        {"do": "fx", "fx": "splash"},
        {"do": "pose", "who": "wolf", "pose": "ouch"},
        {"do": "say", "line": "tp_052"},
        # he shoots back up the flue and out of the chimney, the wall folds back up, he runs off LEFT
        {"do": "cam", "shot": "roof", "at": "focus", "wait": 0.2},
        {"do": "fx", "fx": "wolf_launch", "wait": 1.0},
        {"do": "fx", "fx": "cutaway_close", "wait": 0.7},
        {"do": "walk", "who": "wolf", "dir": "left", "pose": "run_away", "dist": 1.6, "speed": 0.5, "line": "tp_053", "exit": True},
    ]},
    {"id": "ending", "title": "벽돌 집", "spread": {"seed": 1, "view": 4, "place": "brick_lot",
     "spots": BRICK_SPOTS, "set": []},
     # the wolf is gone: the brothers come out in front of the brick house, safe and happy, mom joins them
     "enter": {"who": {"pig_a": "happy_wave", "pig_b": "happy_wave", "pig_c": "cheer", "mom": "wave"},
               "at": {"pig_a": "out_a", "pig_b": "out_b", "pig_c": "out_c", "mom": "mom"}},
     "steps": [
        {"do": "cam", "shot": "stage", "at": "focus"},
        {"do": "fx", "fx": "pigs_cheer", "wait": 0.6},
        {"do": "say", "line": "tp_057"},
        {"do": "fx", "fx": "pigs_cheer", "wait": 0.8},
        {"do": "end", "after": "tp_n02"},
    ]},
]
