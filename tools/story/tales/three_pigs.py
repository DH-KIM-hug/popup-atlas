"""「아기 돼지 삼형제」 (three_pigs) adaptation tables for tools/story/seed_script.py (plan: game/stories/three_pigs/PLAN.md).

Phase 1 (2026-11-18): script + plan + art. Verbs marked NEW below are not in story_runner.gd yet (phase 2); the seeded
script.json is data the runner will grow into. Existing verbs used as is: cover, cam, say, pose, fx, end.
"""
TALE_ID = "three_pigs"
TITLE = "아기 돼지 삼형제"
PREFIX = "tp"
# role -> shared cast skin (game/art/cast/catalog.json role), views each role needs (front = toward the camera,
# back = walking away, side = profile drawn facing right, flipped for leftward travel)
CAST = {
    "pig_a": {"skin": "pig_a", "views": ["front", "side", "back"], "label": "첫째 (straw hat + scarf)"},
    "pig_b": {"skin": "pig_b", "views": ["front", "side", "back"], "label": "둘째 (blue overalls)"},
    "pig_c": {"skin": "pig_c", "views": ["front", "side", "back"], "label": "셋째 (white cap + red overalls)"},
    "mom": {"skin": "mother_pig", "views": ["front"], "label": "엄마 돼지"},
    "wolf": {"skin": "wolf", "views": ["front", "side", "back"], "label": "늑대"},
}
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
BEATS = [
    {"id": "cover", "title": "아기 돼지 삼형제", "spread": None, "steps": [{"do": "cover", "prompt": "tp_n01"}]},
    {"id": "home", "title": "엄마의 배웅", "spread": {"seed": 1, "view": 5, "place": "home",
     "set": [{"card": "village_houses_20", "at": "home_house"}]},
     "enter": {"who": {"mom": "calm", "pig_a": "calm", "pig_b": "calm", "pig_c": "calm"}},
     "steps": [
        {"do": "cam", "shot": "story"},
        {"do": "say", "line": "tp_000"},
        {"do": "pose", "who": "mom", "pose": "talk"},
        {"do": "say", "line": "tp_001"},
        # tap each piglet: it hops + waves (happy_wave) and its building material pops up above it on a little hinge
        # (straw sheaf / plank / brick) — foreshadows the three houses.
        {"do": "tap_each", "targets": ["pig_a", "pig_b", "pig_c"], "prompt": "tp_002", "hint": "tp_002",
         "react": {"pig_a": ["happy_wave", "pop:story_build_props_00"],
                   "pig_b": ["happy_wave", "pop:story_build_props_06"],
                   "pig_c": ["happy_wave", "pop:story_build_props_09"]}},
        {"do": "pose", "who": "mom", "pose": "wave"},
        # they walk off up the road AWAY from the camera (back views), mom waves at the gate
        {"do": "walk", "who": ["pig_a", "pig_b", "pig_c"], "dir": "away", "dist": 1.4, "line": "tp_003"},
    ]},
    {"id": "straw_build", "title": "첫째의 짚 집", "spread": {"seed": 1, "view": 2, "place": "straw_lot",
     "set": [{"card": HOUSE["straw"], "at": "lot", "stage": 0}, {"card": "story_build_props_01", "at": "pile"}]},
     "enter": {"who": {"pig_a": "side_walk"}},
     "steps": [
        {"do": "cam", "shot": "story"},
        {"do": "say", "line": "tp_019"},
        # tap the straw pile 3x: 첫째 carries a sheaf pile → house (side view, flips on the way back); each tap folds up
        # the next band of the straw house (3 bands: wall, wall+door top, thatch roof)
        {"do": "build", "house": "straw", "target": "pile", "taps": 3, "hint": "tp_018", "walker": "pig_a",
         "carry": "carry_straw", "fx": "straw_pop"},
        {"do": "fx", "fx": "star_burst"},
        {"do": "pose", "who": "pig_a", "pose": "flute"},
        {"do": "fx", "fx": "flute_notes"},
        {"do": "say", "line": "tp_020"},
    ]},
    {"id": "wood_build", "title": "둘째의 나무 집", "spread": {"seed": 1, "view": 3, "place": "wood_lot",
     "set": [{"card": HOUSE["wood"], "at": "lot", "stage": 0}, {"card": "story_build_props_05", "at": "pile"}]},
     "enter": {"who": {"pig_b": "hammer"}},
     "steps": [
        {"do": "cam", "shot": "story"},
        {"do": "say", "line": "tp_021"},
        # tap the house 5x: 둘째 hammers (hammer pose bobs), a plank band folds up per tap with a bang (5 bands)
        {"do": "build", "house": "wood", "target": "house", "taps": 5, "hint": "tp_018", "walker": "pig_b",
         "carry": "hammer", "fx": "hammer_bang"},
        {"do": "fx", "fx": "star_burst"},
        {"do": "pose", "who": "pig_b", "pose": "violin"},
        {"do": "fx", "fx": "violin_notes"},
        {"do": "say", "line": "tp_022"},
    ]},
    {"id": "brick_build", "title": "셋째의 벽돌 집", "spread": {"seed": 1, "view": 4, "place": "brick_lot",
     "set": [{"card": HOUSE["brick"], "at": "lot", "stage": 0}, {"card": "story_build_props_08", "at": "pile"}]},
     "enter": {"who": {"pig_c": "lay_brick"}},
     "steps": [
        {"do": "cam", "shot": "story"},
        {"do": "say", "line": "tp_024"},
        # 10 taps = 10 bricks (counter 1..10 on the page); every 2nd tap a brick band folds up (5 bands, the last = roof +
        # chimney). After tap 5 the two brothers stroll past sideways playing flute + violin and tease (tp_023).
        {"do": "build", "house": "brick", "target": "house", "taps": 10, "hint": "tp_018", "walker": "pig_c",
         "carry": "lay_brick", "fx": "brick_thunk", "counter": True,
         "steps": [{"at": 5, "fx": "brothers_tease", "lines": ["tp_023"]}]},
        {"do": "fx", "fx": "star_burst"},
        {"do": "pose", "who": "pig_c", "pose": "proud"},
        {"do": "say", "line": "tp_025"},
    ]},
    {"id": "wolf_straw", "title": "후~ 짚 집", "spread": {"seed": 1, "view": 2, "place": "straw_lot",
     "set": [{"card": HOUSE["straw"], "at": "lot", "stage": "full"}]},
     "enter": {"who": {"pig_a": "calm"}},
     "steps": [
        {"do": "cam", "shot": "wide"},
        # the wolf prowls in from the left in side view (facing his travel direction), sniffing
        {"do": "walk", "who": "wolf", "dir": "right", "pose": "sniff", "dist": 1.2, "line": "tp_027"},
        {"do": "pose", "who": "wolf", "pose": "shout"},
        {"do": "pose", "who": "pig_a", "pose": "defiant"},
        {"do": "say", "line": "tp_028"},
        # tap with the wolf: each tap = one 후~ (wolf huff pose + wind streams); straw tufts fly off, top band peels;
        # 3rd tap: every band folds DOWN and blows apart, the blown-apart straw heap card pops up in its place
        {"do": "huff", "house": "straw", "taps": 3, "prompt": "tp_026", "hint": "tp_026", "result": "blow_apart", "ruin": RUIN["straw"],
         "fx": "straw_fly"},
        {"do": "pose", "who": "pig_a", "pose": "scared"},
        {"do": "say", "line": "tp_029"},
        {"do": "walk", "who": "pig_a", "dir": "right", "pose": "run", "dist": 2.0, "speed": 0.5},
    ]},
    {"id": "wolf_wood", "title": "후~ 나무 집", "spread": {"seed": 1, "view": 3, "place": "wood_lot",
     "set": [{"card": HOUSE["wood"], "at": "lot", "stage": "full"}]},
     "enter": {"who": {"pig_a": "scared", "pig_b": "calm"}},
     "steps": [
        {"do": "cam", "shot": "wide"},
        {"do": "walk", "who": "wolf", "dir": "right", "pose": "side_prowl", "dist": 1.0, "line": "tp_031"},
        {"do": "pose", "who": "wolf", "pose": "shout"},
        {"do": "pose", "who": ["pig_a", "pig_b"], "pose": "defiant"},
        {"do": "say", "line": "tp_032"},
        # 5 taps: the house wobbles harder each time (흔들흔들), last tap: bands tumble down, collapsed plank pile pops up
        {"do": "huff", "house": "wood", "taps": 5, "hint": "tp_026", "result": "collapse", "ruin": RUIN["wood"], "fx": "wood_wobble"},
        {"do": "say", "line": "tp_033"},
        {"do": "walk", "who": ["pig_a", "pig_b"], "dir": "right", "pose": "run", "dist": 2.0, "speed": 0.5,
         "line": "tp_034"},
    ]},
    {"id": "brick_wolf", "title": "쿵쿵쿵!", "spread": {"seed": 1, "view": 4, "place": "brick_lot", "light": "dusk",
     "set": [{"card": HOUSE["brick"], "at": "lot", "stage": "full"}]},
     "enter": {"who": {"pig_a": "calm", "pig_b": "calm", "pig_c": "brave"}},
     "steps": [
        {"do": "cam", "shot": "wide"},
        {"do": "walk", "who": "wolf", "dir": "right", "pose": "side_prowl", "dist": 1.0, "line": "tp_043"},
        {"do": "pose", "who": "wolf", "pose": "shout"},
        {"do": "say", "line": "tp_044"},
        # 8 taps, counted 1..8 on the page; the house only shivers (no band moves), pigs cheer in the windows
        {"do": "huff", "house": "brick", "taps": 8, "prompt": "tp_045", "hint": "tp_045", "result": "hold",
         "fx": "house_shiver", "counter": True},
        {"do": "say", "line": "tp_046"},
        {"do": "pose", "who": "wolf", "pose": "exhausted"},
        {"do": "fx", "fx": "thud_dust"},
        {"do": "say", "line": "tp_047"},
    ]},
    {"id": "chimney", "title": "보글보글", "spread": {"seed": 1, "view": 4, "place": "brick_lot", "light": "dusk",
     "set": [{"card": HOUSE["brick"], "at": "lot", "stage": "full"}]},
     "enter": {"who": {"wolf": "tiptoe"}},
     "steps": [
        # the wolf tiptoes up the roof to the chimney (side view along the roof slope)
        {"do": "climb", "who": "wolf", "to": "chimney", "pose": "tiptoe", "line": "tp_048"},
        # BIG POP-UP SET PIECE: the brick facade folds DOWN toward the reader like a page flap and the kitchen pops up
        # behind it (hearth, cooking pot, three pigs)
        {"do": "fx", "fx": "cutaway_open"},
        {"do": "cam", "shot": "close"},
        {"do": "say", "line": "tp_049"},
        # tap the fire 3x: small → medium → large flame card, pot steam puffs grow, bubbles
        {"do": "tap_steps", "target": "fire", "prompt": "tp_050", "hint": "tp_050", "steps": [
            {"fx": "flame_m"}, {"fx": "flame_l"}, {"fx": "boil", "lines": []}]},
        {"do": "fx", "fx": "wolf_drop"},
        {"do": "say", "line": "tp_051"},
        {"do": "fx", "fx": "splash"},
        {"do": "pose", "who": "wolf", "pose": "ouch"},
        {"do": "say", "line": "tp_052"},
        # he shoots back up the flue, the facade folds up again, and he runs off LEFT (side card flipped) into the distance
        {"do": "fx", "fx": "wolf_launch"},
        {"do": "fx", "fx": "cutaway_close"},
        {"do": "cam", "shot": "wide"},
        {"do": "walk", "who": "wolf", "dir": "left", "pose": "run_away", "dist": 3.0, "speed": 0.6, "line": "tp_053"},
    ]},
    {"id": "ending", "title": "벽돌 마을", "spread": {"seed": 1, "view": 4, "place": "brick_lot",
     "set": [{"card": HOUSE["brick"], "at": "lot", "stage": "full"},
             {"card": "story_houses_08", "at": "lot_left", "stage": 0},
             {"card": "story_houses_09", "at": "lot_right", "stage": 0}]},
     "enter": {"who": {"pig_a": "happy_wave", "pig_b": "happy_wave", "pig_c": "proud"}},
     "steps": [
        {"do": "cam", "shot": "wide"},
        # tap the empty plots: each tap pops a whole new brick house up (full hinge fold)
        {"do": "tap_steps", "target": "plot", "prompt": "tp_055", "hint": "tp_055", "steps": [
            {"fx": "pop:story_houses_08"}, {"fx": "pop:story_houses_09"}]},
        {"do": "pose", "who": "pig_c", "pose": "cheer"},
        {"do": "say", "line": "tp_056"},
        {"do": "say", "line": "tp_057"},
        {"do": "end", "after": "tp_n02"},
    ]},
]
