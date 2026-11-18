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
DROPPED = {4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 30, 35, 36, 37, 38, 39, 40, 41, 42, 54}

# Expression per line (wiring as data): role -> pose name (PLAN.md cast sheet).
LINE_META = {
    # NEW lines, not recorded (ElevenLabs spend not approved): caption only with a timed pause, reported in missing_audio
    "tp_n01": {"status": "pending", "pending": "needs recording (user OK for ElevenLabs)"},
    "tp_n02": {"status": "pending", "pending": "needs recording (user OK for ElevenLabs)"},
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
    "tp_047": {"expr": {"wolf": "exhausted"}},
    "tp_048": {"expr": {"wolf": "tiptoe"}},
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
KITCHEN = [  # brick house interior (beat 8), behind the front wall, popped by cutaway_open
    {"card": "story_hearth_00", "at": "lot", "off": [0.32, -0.26], "stage": 0, "name": "k_hearth", "clear": 0},
    {"card": "story_hearth_02", "at": "lot", "off": [0.34, -0.17], "stage": 0, "name": "fire", "clear": 0},
    {"card": "story_hearth_03", "at": "lot", "off": [0.34, -0.165], "stage": 0, "name": "fire_m", "clear": 0},
    {"card": "story_hearth_04", "at": "lot", "off": [0.34, -0.16], "stage": 0, "name": "fire_l", "clear": 0},
    {"card": "story_hearth_01", "at": "lot", "off": [0.34, -0.1], "stage": 0, "name": "k_pot", "clear": 0},
    {"card": "story_hearth_12", "at": "lot", "off": [-0.3, -0.2], "stage": 0, "name": "k_table", "clear": 0},
    {"card": "story_hearth_14", "at": "lot", "off": [-0.25, -0.3], "stage": 0, "name": "k_shelf", "clear": 0, "scale": 1.6},
]
# view 2: the stream runs diagonally just behind the anchor; the straw lot is on the near-left grass
STRAW_SPOTS = {"lot": [-1.1, -0.05], "pile": [-0.64, 0.26], "pig_a": [-0.48, 0.42], "wolf": [-1.8, 0.28],
               "pig_a_door": [-0.42, 0.1], "focus": [-1.2, 0.1]}
# view 3 (2026-11-18 v2, user: "houses built across the road"): the road runs straight up the middle (x -0.2..0.4),
# the stream crosses the front; the wood lot is on the meadow right of the road, the wolf comes up the road
WOOD_SPOTS = {"lot": [1.0, -0.62], "pile": [1.85, -0.38], "pig_b": [1.62, -0.3], "pig_a": [1.88, -0.18],
              "wolf": [0.4, -0.2], "focus": [0.98, -0.38]}
# view 4 v2: the road climbs from the middle to the right (x -0.2..0.6); the brick lot is on the open meadow left of
# it (house x -1.43..-0.27), the pile and the wolf further left, the brothers peek out on the road side; kitchen
# spots (in_*) keep their offsets from the lot
BRICK_SPOTS = {"lot": [-0.85, -0.6], "pile": [-1.22, -0.12], "pig_c": [-0.1, -0.45], "tease": [-0.85, 0.16],
               "wolf": [-1.8, -0.08], "pig_a": [-0.12, -0.72], "pig_b": [0.06, -0.74], "lot_left": [-2.05, -1.3],
               "lot_right": [1.2, -1.2], "in_a": [-1.17, -0.72], "in_b": [-0.97, -0.7], "in_c": [-0.79, -0.68],
               "wolf_land": [-1.8, 0.1], "mom": [-0.2, 0.02], "focus": [-0.75, -0.42], "village": [-0.45, -0.9]}
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
        {"do": "build", "house": "house", "target": "house", "taps": 5, "hint": "tp_018", "walker": "pig_b",
         "fx": "hammer_bang", "gap": 0.5},
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
        {"do": "build", "house": "house", "target": "house", "taps": 10, "hint": "tp_018", "walker": "pig_c",
         "fx": "brick_thunk", "counter": True, "gap": 0.35,
         "steps": [{"at": 5, "fx": "brothers_tease", "lines": ["tp_023"]}, {"at": 7, "fx": "brothers_leave"}]},
        {"do": "fx", "fx": "star_burst"},
        {"do": "pose", "who": "pig_c", "pose": "proud"},
        {"do": "say", "line": "tp_025"},
    ]},
    {"id": "wolf_straw", "title": "후~ 짚 집", "spread": {"seed": 1, "view": 2, "place": "straw_lot",
     "spots": STRAW_SPOTS,
     "set": [{"card": "story_houses_00", "at": "lot", "stage": "full", "name": "house"},
             {"card": "story_houses_02", "at": "lot", "off": [0.0, 0.05], "stage": 0, "name": "ruin", "scale": 1.3}]},
     "enter": {"who": {"pig_a": "calm"}, "at": {"pig_a": "pig_a_door"}},
     "steps": [
        {"do": "cam", "shot": "stage"},
        # the wolf prowls in from the left, sniffing (side view, facing right)
        {"do": "walk", "who": "wolf", "dir": "right", "to": "wolf", "dist": 0.75, "pose": "sniff", "speed": 0.2, "line": "tp_027"},
        {"do": "pose", "who": "wolf", "pose": "shout"},
        {"do": "pose", "who": "pig_a", "pose": "defiant"},
        {"do": "say", "line": "tp_028"},
        # tap the wolf x3: each tap = one 후~; the straw bands peel off from the top, the 3rd blows it all apart
        {"do": "huff", "house": "house", "taps": 3, "prompt": "tp_026", "hint": "tp_026", "result": "blow_apart",
         "ruin": "story_houses_02", "fx": "straw_fly", "gap": 0.7},
        {"do": "pose", "who": "pig_a", "pose": "scared", "hop": True},
        {"do": "say", "line": "tp_029"},
        # he runs off toward the reader (front view, scared face), out of the page
        {"do": "walk", "who": "pig_a", "dir": "toward", "pose": "scared", "dist": 1.3, "speed": 0.45, "exit": True},
    ]},
    {"id": "wolf_wood", "title": "후~ 나무 집", "spread": {"seed": 1, "view": 3, "place": "wood_lot",
     "spots": WOOD_SPOTS,
     "set": [{"card": "story_houses_03", "at": "lot", "stage": "full", "name": "house", "scale": 1.0},
             {"card": "story_houses_05", "at": "lot", "off": [0.0, 0.05], "stage": 0, "name": "ruin", "scale": 1.0}]},
     "enter": {"who": {"pig_a": "scared", "pig_b": "calm"}},
     "steps": [
        {"do": "cam", "shot": "stage"},
        {"do": "walk", "who": "wolf", "dir": "right", "to": "wolf", "dist": 0.6, "pose": "side_prowl", "speed": 0.2, "line": "tp_031"},
        {"do": "pose", "who": "wolf", "pose": "shout"},
        {"do": "pose", "who": ["pig_a", "pig_b"], "pose": "defiant"},
        {"do": "say", "line": "tp_032"},
        # tap the wolf x5: the wood house rocks harder each time (흔들흔들), the 5th knocks it down
        {"do": "huff", "house": "house", "taps": 5, "hint": "tp_026", "result": "collapse", "ruin": "story_houses_05",
         "fx": "wood_wobble", "gap": 0.6},
        {"do": "pose", "who": ["pig_a", "pig_b"], "pose": "scared", "hop": True, "wait": 0.2},
        {"do": "say", "line": "tp_033"},
        {"do": "walk", "who": ["pig_a", "pig_b"], "dir": "right", "pose": "run", "dist": 1.8, "speed": 0.5,
         "line": "tp_034", "exit": True},
    ]},
    {"id": "brick_wolf", "title": "쿵쿵쿵!", "spread": {"seed": 1, "view": 4, "place": "brick_lot", "light": "dusk",
     "spots": BRICK_SPOTS,
     "set": [{"card": "story_houses_06", "at": "lot", "stage": "full", "name": "house"}] + KITCHEN},
     # the three brothers peek out from beside the brick house
     "enter": {"who": {"pig_a": "scared", "pig_b": "scared", "pig_c": "brave"}},
     "steps": [
        {"do": "cam", "shot": "stage"},
        {"do": "walk", "who": "wolf", "dir": "right", "to": "wolf", "dist": 0.6, "pose": "side_prowl", "speed": 0.2, "line": "tp_043"},
        {"do": "pose", "who": "wolf", "pose": "shout"},
        {"do": "say", "line": "tp_044"},
        # tap the house x8, counted: 후~ every time, the house only shivers, the pigs cheer
        {"do": "huff", "house": "house", "target": "house", "taps": 8, "prompt": "tp_045", "hint": "tp_045",
         "result": "hold", "fx": "brick_huff", "counter": True, "gap": 0.4},
        {"do": "say", "line": "tp_046"},
        {"do": "pose", "who": "wolf", "pose": "exhausted"},
        {"do": "fx", "fx": "thud_dust"},
        {"do": "say", "line": "tp_047"},
    ]},
    {"id": "chimney", "title": "보글보글", "spread": {"seed": 1, "view": 4, "place": "brick_lot", "light": "dusk",
     "spots": BRICK_SPOTS, "set": []},
     "enter": {"who": {"wolf": "tiptoe", "pig_a": "calm", "pig_b": "calm", "pig_c": "brave"}},
     "steps": [
        {"do": "cam", "shot": "roof", "at": "lot", "wait": 0.3},
        # he tiptoes up the roof slope to the chimney (side view, a paper hop: the tiptoe figure is one card)
        {"do": "climb", "who": "wolf", "on": "house", "pose": "tiptoe", "speed": 0.16, "line": "tp_048",
         "path": [[-0.82, 0.0, 0.06], [-0.68, 0.53, 0.06], [-0.34, 0.86, 0.06], [0.16, 0.86, 0.06], [0.26, 0.9, 0.06]]},
        # BIG POP-UP SET PIECE: the brick front wall folds DOWN toward the reader, the kitchen pops up behind it
        {"do": "fx", "fx": "cutaway_open", "wait": 1.0},
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
    {"id": "ending", "title": "벽돌 마을", "spread": {"seed": 1, "view": 4, "place": "brick_lot",
     "spots": BRICK_SPOTS,
     "set": [{"card": "story_houses_08", "at": "lot_left", "stage": 0, "name": "house_l"},
             {"card": "story_houses_09", "at": "lot_right", "stage": 0, "name": "house_r"},
             {"card": "story_build_props_08", "at": "lot_left", "off": [0.0, 0.25], "name": "plot_l", "scale": 1.3},
             {"card": "story_build_props_08", "at": "lot_right", "off": [0.0, 0.25], "name": "plot_r", "scale": 1.3}]},
     "enter": {"who": {"pig_a": "happy_wave", "pig_b": "happy_wave", "pig_c": "proud", "mom": "calm"},
               "at": {"pig_a": "in_a", "pig_b": "in_b", "pig_c": "in_c"}},
     "steps": [
        {"do": "cam", "shot": "village", "at": "village"},
        # tap the empty plots: each tap pops a whole new brick cottage up
        {"do": "tap_steps", "prompt": "tp_055", "hint": "tp_055", "steps": [
            {"target": "plot_l", "fx": "pop:story_houses_08"}, {"target": "plot_r", "fx": "pop:story_houses_09"}]},
        {"do": "pose", "who": "pig_c", "pose": "cheer"},
        {"do": "say", "line": "tp_056"},
        {"do": "say", "line": "tp_057"},
        {"do": "end", "after": "tp_n02"},
    ]},
]
