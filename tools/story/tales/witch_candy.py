"""「사탕 마녀의 핼러윈」 (witch_candy) adaptation tables for tools/story/seed_script.py (plan: game/stories/witch_candy/PLAN.md).

Phase 1 (2026-11-19): plan, script, art. NOT wired: verbs marked NEW are phase 2 (story_runner.gd / spread_stage.gd);
the seeded script.json is data the runner will grow into. Existing verbs used as is: cover, cam, say, walk, pose,
go_inside, tap_each, tap_steps, fx, frame, end.

User decisions (2026-11-19): magic play, not a lesson (no "무슨 색일까?", no colour names explained, no "맞아요", no
counting, no moral); two rounds + the ghost candy finale; hero name 다현이 (톡톡 recordings reused); 5-6 min.
Branch design (PLAN.md "Branches"): the shelf holds 9 ingredients in THREE colour groups (red / yellow / blue; the green
frog and dinosaur are left out). Two picks auto-stir. The colour SET picks the result:
    r -> strawberry, y -> duck, b -> fish, r+y -> pumpkin, r+b -> bat, y+b -> frog   (6 results)
Every result has all its 톡톡 lines recorded (eat / transform / kid / action), and every result's look is reused by
one character in the finale (frog->rabbit, duck->bear, bat->fox, fish->cat, pumpkin->witch, strawberry->Dahyun).
"""
TALE_ID = "witch_candy"
TITLE = "사탕 마녀의 핼러윈"
PREFIX = "wc"
MORAL = ""  # no moral (user: the book tells the tale)

# ---------------------------------------------------------------- line adaptations
CHANGED = {}
SEG_KEEP = {}
NEW_LINES = {
    # witch_candy's narrator is Lily (pFZP5JQG7iQjIQuC4Bku): sun_wind's / three_pigs' cover and replay recordings are
    # other narrator voices, so these need recording (ask the user first).
    "wc_n01": [["nar", "그림책을 톡 눌러서 펼쳐 볼까요?", None, "[cheerful, inviting, warm, cosy Halloween night]"]],
    "wc_n02": [["nar", "또 보고 싶으면 '다시 보기'를 톡!", None, "[cheerful, inviting]"]],
    # the opening taps: catch the invitations fluttering down (first tap of its kind -> voiced once)
    "wc_n03": [["nar", "날아오는 초대장을 톡 눌러 잡아요.", None, "[warm, playful, inviting]"]],
    # the finale taps: tap each friend, they eat their candy and transform (first tap of its kind -> voiced once)
    "wc_n04": [["nar", "친구들을 톡 눌러 사탕을 건네요.", None, "[warm, playful, inviting]"]],
}
# 2026-11-19 trims (no new recording):
#   wc_039 witch_df120ff616.mp3 "히히, 색을 섞으면 다른 색 사탕이 돼. 먹으면 어떻게 되는지는… 비밀! 같이 만들까?" -> the
#   colour-mixing sentence (0.37-3.62 s, between the pauses found with silencedetect -35 dB) is cut out; 0-0.42 s
#   ("히히,") + 3.62 s-end joined with 30 ms fades -> witch_df120ff616_t.mp3 "히히, 먹으면 어떻게 되는지는… 비밀! 같이 만들까?"
#   Chorus clips: 톡톡 premixed the six-voice "오~~우~~" / "해피 핼러윈! 오~우~!" (chorus_el.js, mix_chorus_el.py, kid +
#   witch + cat voices; the friends are non-speaking): one clip each replaces the per-voice segs.
TRIM = {
    "wc_039": ("히히, 먹으면 어떻게 되는지는… 비밀! 같이 만들까?", "res://audio/voice/witch_candy/witch_df120ff616_t.mp3",
               "audio/el/witch_candy/witch_df120ff616.mp3 (0-0.42 s + 3.62 s-end)"),
    "wc_x_ghost_all": ("오~~우~~", "res://audio/voice/witch_candy/ch_48ac9f3898.mp3",
                       "audio/el/witch_candy/chorus/ch_48ac9f3898.mp3 (톡톡 premixed chorus)", "all"),
    "wc_x_happy_all": ("해피 핼러윈! 오~우~!", "res://audio/voice/witch_candy/ch_672e05d93c.mp3",
                       "audio/el/witch_candy/chorus/ch_672e05d93c.mp3 (톡톡 premixed chorus)", "all"),
}
# Dropped (teaching, counting, colour talk, green / brown branches, friends' chorus lines, repeats):
#  9, 10 (ingredients introduced by colour), 21-23 / 33-35 (green + leek ingredients), 42-44 (rules: "하나든 여러 개든",
#  "세 가지는 맨 마지막에", "하나는 넣어야지"), 47-58 (colour questions), 59-66 (wrong / "맞아요"), 67-78 + 144-145 (colour
#  explanations "○○이랑 ○○을 섞었더니 ○색이 됐어요"), 88 / 95 / 101 / 108 / 116 / 118 (chocolate), 121 ("재료를 톡!": a
#  second voiced instruction of the same kind), 122-124 (repeat / one more round), 128 (colour list instruction), 129
#  (counting "하나, 둘, 셋!"), 146-153 (kiwi / crocodile), extras n1-n5 (counting), yuck, ch_* (friends' chorus; user:
#  friends non-speaking).
DROPPED = set()  # (unused lines are simply not referenced by a beat)

# Expression per line (wiring as data). Roles: kid (다현이), witch, cat (호박이), rabbit, bear, fox.
LINE_META = {
    "wc_000": {"expr": {"kid": "calm", "rabbit": "calm", "bear": "calm", "fox": "calm"}},
    "wc_001": {"expr": {"kid": "excited"}},
    "wc_003": {"expr": {"witch": "welcome"}},
    "wc_004": {"expr": {"kid": "calm"}},
    "wc_005": {"expr": {"witch": "calm"}},
    "wc_007": {"expr": {"kid": "wow", "rabbit": "cheer", "bear": "cheer", "fox": "cheer"}},
    "wc_008": {"expr": {"cat": "meow"}},
    "wc_011": {"expr": {"kid": "yuck"}},
    "wc_038": {"expr": {"cat": "nose"}},
    "wc_039": {"expr": {"witch": "giggle"}},
    "wc_040": {"expr": {"kid": "eager"}},
    "wc_036": {"expr": {"kid": "yuck"}},
    "wc_037": {"expr": {"kid": "yuck", "cat": "nose"}},
    "wc_045": {"expr": {"witch": "magic"}},
    "wc_046": {"expr": {"witch": "magic"}},
    "wc_079": {"expr": {"kid": "wow"}},
    "wc_080": {"expr": {"witch": "offer"}},
    "wc_109": {"expr": {"witch": "giggle"}},
    "wc_117": {"expr": {"witch": "surprised"}},
    "wc_119": {"expr": {"kid": "calm"}},
    "wc_120": {"expr": {"witch": "giggle"}},
    "wc_126": {"expr": {"witch": "welcome"}},
    "wc_127": {"expr": {"kid": "wow"}},
    "wc_130": {"expr": {"witch": "magic"}},
    "wc_131": {"expr": {"kid": "wow"}},
    "wc_132": {"expr": {"kid": ["eat", "ghost"]}},
    "wc_x_ghost_kid": {"expr": {"kid": "ghost"}},
    "wc_133": {"expr": {"witch": "ghost"}},
    "wc_134": {"expr": {"cat": "ghost", "rabbit": "ghost", "bear": "ghost", "fox": "ghost"}},
    "wc_136": {"expr": {"witch": "welcome"}},
    "wc_138": {"expr": {"witch": "two_candies"}},
    "wc_140": {"expr": {"kid": "calm", "witch": "calm", "cat": "sit", "rabbit": "calm", "bear": "calm", "fox": "calm"}},
    "wc_141": {"expr": {"witch": "welcome"}},
    "wc_142": {"expr": {"kid": "wave"}},
    "wc_x_happy_all": {"expr": {"kid": "wave", "witch": "welcome", "cat": "meow", "rabbit": "cheer", "bear": "cheer",
                                "fox": "cheer"}},
}
# transformation faces are set by the NEW brew verb (RESULTS[*]["figure"])

# ---------------------------------------------------------------- branches (NEW verb `pick` + `brew`, phase 2)
# Ingredient cards on the shelf (story_wc_ingredients_*), their colour, the "A랑" lead clip and the "B를 넣었어요!" clip.
INGREDIENTS = {
    "snot":      {"color": "r", "card": "story_wc_ingredients_00", "and": "wc_012", "in": "wc_024", "yuck": "wc_036", "sfx": "wc.drip"},
    "firetruck": {"color": "r", "card": "story_wc_ingredients_01", "and": "wc_013", "in": "wc_025", "sfx": "wc.siren"},
    "ladybug":   {"color": "r", "card": "story_wc_ingredients_02", "and": "wc_014", "in": "wc_026", "sfx": "wc.buzz"},
    "lantern":   {"color": "y", "card": "story_wc_ingredients_03", "and": "wc_015", "in": "wc_027", "sfx": "wc.chime"},
    "chickfart": {"color": "y", "card": "story_wc_ingredients_04", "and": "wc_016", "in": "wc_028", "sfx": "wc.kazoo"},
    "duck":      {"color": "y", "card": "story_wc_ingredients_05", "and": "wc_017", "in": "wc_029", "sfx": "wc.quack"},
    "poo":       {"color": "b", "card": "story_wc_ingredients_06", "and": "wc_018", "in": "wc_030", "yuck": "wc_037", "sfx": "wc.plop"},
    "fish":      {"color": "b", "card": "story_wc_ingredients_07", "and": "wc_019", "in": "wc_031", "sfx": "wc.splash"},
    "wave":      {"color": "b", "card": "story_wc_ingredients_08", "and": "wc_020", "in": "wc_032", "sfx": "wc.wave"},
}
# colour set (sorted letters) -> result
COMBOS = {"r": "strawberry", "y": "duck", "b": "fish", "ry": "pumpkin", "br": "bat", "by": "frog"}
# per result: candy card, Dahyun's figures, the eat line per round, transform / kid / action lines, where the action
# plays (stays on the shop-and-street spread: camera moves only) and the pot colour after the POOF
RESULTS = {
    "strawberry": {"candy": "story_wc_candies_00", "pot": "red", "eat": ["wc_082", "wc_089"], "tf": "wc_096",
                   "kid": "wc_102", "act": "wc_110", "extra": ["wc_117"], "figure": "tf_strawberry",
                   "move": "tf_strawberry_ball", "action": "roll_street",
                   "note": "she curls into a strawberry ball, rolls out of the door and down the street, bumps a pumpkin "
                           "lantern (통!), the witch calls from the door (어디 가!), she rolls back"},
    "duck": {"candy": "story_wc_candies_01", "pot": "yellow", "eat": ["wc_083", "wc_090"], "tf": "wc_097",
             "kid": "wc_103", "act": "wc_111", "figure": "tf_duck", "move": "duck_cycle", "action": "waddle_room",
             "note": "duck feet: she waddles round the pot (drawn duck waddle cycle), 호박이 waddles behind her"},
    "fish": {"candy": "story_wc_candies_02", "pot": "blue", "eat": ["wc_084", "wc_091"], "tf": "wc_098",
             "kid": "wc_104", "act": "wc_112", "figure": "tf_fish", "move": "tf_fish", "action": "swim_moon",
             "note": "fish tail: she floats out of the door and up over the roofs, swims a loop round the full moon "
                     "(camera tilts up to the sky), bubbles trail; floats back down to the door"},
    "frog": {"candy": "story_wc_candies_03", "pot": "green", "eat": ["wc_085", "wc_092"], "tf": "wc_154",
             "kid": "wc_105", "act": "wc_113", "figure": "tf_frog_sit", "move": "tf_frog_jump", "action": "hop_roof",
             "note": "frog legs: three hops out of the door and up onto the shop roof (low angle), waves from the ridge, "
                     "hops down"},
    "pumpkin": {"candy": "story_wc_candies_04", "pot": "orange", "eat": ["wc_086", "wc_093"], "tf": "wc_099",
                "kid": "wc_106", "act": "wc_114", "figure": "tf_pumpkin", "move": "walk", "action": "glow_street",
                "note": "her pumpkin tummy glows: the street lanterns dim (light 'dark'), she walks out (drawn walk "
                        "cycle; the glow rides on her) and lights the street around her (warm omni light)"},
    "bat": {"candy": "story_wc_candies_05", "pot": "purple", "eat": ["wc_087", "wc_094"], "tf": "wc_100",
            "kid": "wc_107", "act": "wc_115", "figure": "tf_bat_up", "move": "tf_bat_flap", "action": "fly_moon",
            "note": "bat wings (two drawn wing frames flap): out of the door, up past the roofs, a circle in front of "
                    "the moon with the paper bat silhouettes"},
}
# Autoplay: random pair of ingredients whose result was not shown yet in this run (never a repeat). A child may repeat
# a result; it simply plays again (no correction line).

# ---------------------------------------------------------------- stage
HANDLER = "res://stories/witch_candy/fx.gd"   # phase 2
BACKDROP = True
# Shots [distance, elevation°, focus height, fov, yaw offset°] (three_pigs vocabulary + interior shots)
SHOTS = {"story": [3.7, 13.0, 0.28, 20.0], "close": [2.9, 12.0, 0.32, 20.0],
         "crane_high": [8.0, 34.0, 0.3, 22.0, 0.0], "establish": [9.0, 18.0, 0.3, 24.0, -6.0],
         "street": [5.2, 12.0, 0.3, 22.0, 8.0], "medium": [3.2, 10.0, 0.3, 20.0, 6.0],
         "face": [1.5, 7.0, 0.3, 20.0, 0.0], "low_up": [2.7, 3.5, 0.5, 22.0, -10.0],
         "sky": [5.5, -4.0, 1.4, 26.0, 0.0],             # tilt up: the moon over the roofs (fish / bat / parade end)
         "high": [6.2, 30.0, 0.2, 22.0, 4.0], "pull_back": [10.5, 26.0, 0.3, 24.0, 0.0],
         # inside the shop (camera behind the hidden front wall, looking into the room)
         "room": [1.7, 9.0, 0.3, 46.0, 0.0],             # the whole room: shelf left, pot middle, counter right
         "shelf": [1.25, 7.0, 0.3, 40.0, -12.0],         # shelf + pot + Dahyun: the pick taps (all 9 ingredients framed)
         "pot": [0.9, 16.0, 0.2, 38.0, 6.0],             # looking down into the pot: swirl, POOF, candy
         "pot_low": [0.8, 3.0, 0.3, 40.0, -6.0],         # low on the fire (tap the logs)
         "two_shot": [1.1, 6.0, 0.32, 40.0, 14.0],       # witch + Dahyun across the pot
         "door_out": [1.4, 8.0, 0.3, 44.0, 180.0]}       # inside looking out through the open door to the street
CAST = {
    "kid": {"kind": "actor", "skin": "dahyun", "views": ["front", "side", "back"], "label": "다현이 (little wizard)"},
    "witch": {"kind": "actor", "skin": "candy_witch", "views": ["front", "side", "back"], "label": "사탕 마녀"},
    "cat": {"kind": "actor", "skin": "hobak_cat", "views": ["front", "side", "back"], "label": "호박이 (orange cat)"},
    "rabbit": {"kind": "actor", "skin": "rabbit_kid", "views": ["front", "side", "back"], "label": "토끼 (non-speaking)"},
    "bear": {"kind": "actor", "skin": "bear_kid", "views": ["front", "side", "back"], "label": "곰 (non-speaking)"},
    "fox": {"kind": "actor", "skin": "fox_kid", "views": ["front", "side", "back"], "label": "여우 (non-speaking)"},
}
UI = {
    "cover": [["cast_dahyun_calm", 190], ["cast_candy_witch_welcome", 250], ["cast_hobak_cat_sit", 120]],
    "end": [["cast_dahyun_wave", 180], ["cast_candy_witch_two_candies", 240], ["cast_hobak_cat_meow", 120]],
    "speakers": {"kid": ["다현이", "4b3a7a", "cast_dahyun_calm"], "witch": ["사탕 마녀", "3e9d8f", "cast_candy_witch_calm"],
                 "cat": ["호박이", "e8862a", "cast_hobak_cat_sit"], "all": ["다 같이", "c58a1e", "cast_candy_witch_ghost"]},
}

# ONE spread for the whole tale (no page turn after the cover): the Halloween street (night dress of the village on the
# meadow template) with the candy shop at its end; the shop is a house with a body and its room inside the footprint
# (interior RoomBox template, NEW), so going in / out is a camera move through the open door (three_pigs rule:
# same-place moves are camera moves). Spot coordinates: [right, toward camera] from the page anchor, finalised with
# tools/story/probe_spots.gd in phase 2 (phase-1 prototype values from tools/story/wc_proto.py).
STREET = {"shop": [0.2, -1.6], "door": [0.2, -1.22], "lamp_l": [-0.9, -0.3], "lamp_r": [1.0, -0.5],
          "kids": [-1.2, 0.5], "kids_mid": [-0.4, -0.2], "witch_door": [0.55, -1.15], "lantern_bump": [-1.6, 0.4],
          "moon_loop": [0.2, -3.0], "roof": [0.2, -1.6], "est": [0.0, -0.8], "parade_a": [-1.6, 0.2],
          "parade_b": [1.4, 0.1],
          # inside the shop (room box, origin = shop spot): shelf left, pot middle, counter right
          "in_shelf": [-0.55, -2.1], "in_pot": [0.15, -1.95], "in_counter": [0.75, -2.15], "in_kid": [-0.15, -1.75],
          "in_witch": [0.48, -1.85], "in_friends": [-0.75, -1.65], "in_cat": [0.05, -1.62], "in_focus": [0.0, -1.9]}
SHOP_SET = [
    {"card": "story_wc_shop_00", "at": "shop", "stage": "full", "name": "shop", "scale": 1.0, "clear": 2.0,
     "box": {"depth": 1.0, "side": "story_wc_shop_02", "inner": "story_wc_room_00", "floor": "story_wc_room_03",
             "room": "interior"}},   # NEW: "room" = build the interior RoomBox (walls / floor / beam) in the footprint
    {"card": "story_wc_room_04", "at": "in_shelf", "stage": "full", "name": "shelf", "clear": 0},
    {"card": "story_wc_room_07", "at": "in_counter", "stage": "full", "name": "counter", "clear": 0},
    {"card": "story_wc_room_07", "at": "in_pot", "stage": "full", "name": "hearth", "clear": 0},
    {"card": "story_wc_pot_00", "at": "in_pot", "stage": "full", "name": "pot", "clear": 0},
    {"card": "story_wc_pot_11", "at": "in_pot", "stage": 0, "name": "logs", "clear": 0},
    {"card": "story_wc_halloween_04", "at": "lamp_l", "stage": "full", "name": "bunting", "clear": 0.5},
    {"card": "story_wc_halloween_13", "at": "lamp_l", "stage": "full", "name": "lamp_l"},
    {"card": "story_wc_halloween_13", "at": "lamp_r", "stage": "full", "name": "lamp_r"},
    {"card": "story_wc_halloween_01", "at": "lantern_bump", "stage": "full", "name": "pumpkin_bump"},
]


def _street(**kw):
    sp = {"seed": 1, "view": 5, "place": "street", "light": "evening", "night": "halloween", "spots": STREET,
          "set": SHOP_SET}
    sp.update(kw)
    return sp


ROUND = {  # NEW verb `brew`: one round = pick two -> stir -> POOF -> candy -> eat -> transform -> action -> back
    "pick": {"shelf": "shelf", "pot": "pot", "picks": 2, "ingredients": INGREDIENTS, "combos": COMBOS,
             "results": RESULTS, "and_in": True, "autoplay": "random_new_result"},
}

BEATS = [
    {"id": "cover", "title": "사탕 마녀의 핼러윈", "spread": None, "steps": [{"do": "cover", "prompt": "wc_n01"}]},
    {"id": "invite", "title": "초대장", "spread": _street(),
     "enter": {"who": {"kid": "calm", "rabbit": "calm", "bear": "calm", "fox": "calm"},
               "at": {"kid": "kids", "rabbit": "kids", "bear": "kids", "fox": "kids"}},
     "steps": [
        {"do": "cam", "shot": "establish", "at": "est", "from": "crane_high", "rate": 0.9, "wait": 1.4},
        {"do": "fx", "fx": "invites_flutter", "wait": 0.2},          # NEW fx: four pumpkin cards drift down on the wind
        {"do": "say", "line": "wc_000"},
        {"do": "cam", "shot": "medium", "at": "kids", "wait": 0.2},
        # tap the three fluttering cards: each lands in a friend's hands (the 4th lands in Dahyun's)
        {"do": "tap_each", "targets": ["invite_1", "invite_2", "invite_3"], "prompt": "wc_n03", "hint": "wc_n03",
         "react": {"invite_1": ["catch:rabbit"], "invite_2": ["catch:bear"], "invite_3": ["catch:fox"]}},
        {"do": "fx", "fx": "catch:kid"},
        {"do": "cam", "shot": "face", "at": "kids", "wait": 0.1},
        {"do": "say", "line": "wc_001"},
        # the shop at the street's end lights up: a slow push down the street
        {"do": "cam", "shot": "street", "at": "shop", "rate": 1.0, "wait": 0.2},
        {"do": "fx", "fx": "shop_lights_on", "wait": 0.3},
        {"do": "say", "line": "wc_002"},
        {"do": "walk", "who": ["kid", "rabbit", "bear", "fox"], "to": "kids_mid", "dir": "away", "speed": 0.35,
         "follow": "kid", "shot": "street"},
        {"do": "fx", "fx": "door_open", "wait": 0.2},
        {"do": "walk", "who": "witch", "from": "door", "to": "witch_door", "dir": "toward", "speed": 0.3},
        {"do": "cam", "shot": "medium", "at": "witch_door", "wait": 0.1},
        {"do": "say", "line": "wc_003"},
        {"do": "walk", "who": "cat", "from": "door", "to": "witch_door", "dir": "toward", "speed": 0.3, "async": True},
        {"do": "cam", "shot": "story", "at": "door", "wait": 0.1},
        {"do": "go_inside", "who": ["kid", "rabbit", "bear", "fox", "witch", "cat"], "house": "shop", "room": True,
         "line": "wc_004"},   # NEW: room = they walk on into the room instead of appearing at windows
    ]},
    {"id": "fire", "title": "뽀글뽀글 솥", "spread": _street(),
     "enter": {"who": {"kid": "calm", "witch": "calm", "cat": "sit", "rabbit": "calm", "bear": "calm", "fox": "calm"},
               "at": {"kid": "in_kid", "witch": "in_witch", "cat": "in_cat", "rabbit": "in_friends",
                      "bear": "in_friends", "fox": "in_friends"}},
     "steps": [
        {"do": "fx", "fx": "inside_view", "wait": 1.6},              # NEW generic: camera glides in through the door
        {"do": "cam", "shot": "room", "at": "in_focus", "wait": 0.3},
        {"do": "say", "line": "wc_005"},
        {"do": "cam", "shot": "pot_low", "at": "in_pot", "wait": 0.2},
        {"do": "fx", "fx": "up:logs", "wait": 0.3},
        {"do": "tap_steps", "target": "logs", "prompt": "wc_006", "hint": "wc_006", "steps": [
            {"fx": "flame_s"}, {"target": "flame_s", "fx": "flame_m"}, {"target": "flame_m", "fx": "flame_l"}]},
        {"do": "fx", "fx": "pot_water", "wait": 0.4},                # clear water rises, bubbles
        {"do": "cam", "shot": "room", "at": "in_focus", "rate": 1.4},
        {"do": "say", "line": "wc_007"},
        {"do": "cam", "shot": "face", "at": "in_cat", "wait": 0.1},
        {"do": "say", "line": "wc_008"},
    ]},
    {"id": "shelf", "title": "으엑, 재료!", "spread": _street(),
     "enter": {"who": {}, "keep": ["kid", "witch", "cat", "rabbit", "bear", "fox"]},
     "steps": [
        {"do": "cam", "shot": "shelf", "at": "in_shelf", "rate": 1.2, "wait": 0.2},
        {"do": "fx", "fx": "shelf_pop", "wait": 2.4},                # NEW: the 9 ingredients pop onto the shelf, one sfx each
        {"do": "say", "line": "wc_011"},
        {"do": "say", "line": "wc_038"},
        {"do": "cam", "shot": "two_shot", "at": "in_pot", "wait": 0.1},
        {"do": "say", "line": "wc_039"},
        {"do": "say", "line": "wc_040"},
    ]},
    {"id": "round1", "title": "마법 사탕", "spread": _street(),
     "enter": {"who": {}, "keep": ["kid", "witch", "cat", "rabbit", "bear", "fox"]},
     "steps": [
        {"do": "frame", "with": ["shelf", "pot", "kid"], "wait": 0.6},
        # NEW `brew`: pick 2 (prompt voiced), "A랑 B를 넣었어요!" (+ 으엑 for snot / poo), stir (wc_046), POOF (wc_079),
        # candy lands at Dahyun's hands, witch offers (wc_080), eat (round 1 line), 뿅 transform (tf), kid line, the
        # action outside (camera follows out of the door, act line), witch giggles (wc_109), 뿅 back (wc_119), she walks
        # back in
        {"do": "brew", "round": 1, "prompt": "wc_041", "hint": "wc_041", **ROUND["pick"],
         "stir": "wc_046", "pop": "wc_079", "offer": "wc_080", "after": ["wc_109"], "back": "wc_119"},
    ]},
    {"id": "round2", "title": "한 번 더", "spread": _street(),
     "enter": {"who": {}, "keep": ["kid", "witch", "cat", "rabbit", "bear", "fox"]},
     "steps": [
        {"do": "cam", "shot": "two_shot", "at": "in_pot", "wait": 0.1},
        {"do": "say", "line": "wc_120"},
        {"do": "fx", "fx": "pot_clear", "wait": 0.2},
        {"do": "say", "line": "wc_125"},
        {"do": "frame", "with": ["shelf", "pot", "kid"], "wait": 0.4},
        # round 2: ring hint only (the instruction was voiced in round 1), shorter: no offer line, "냠…" eat line,
        # return with a 뿅 sfx only
        {"do": "brew", "round": 2, **ROUND["pick"], "stir": "wc_045"},
    ]},
    {"id": "ghost_candy", "title": "유령 사탕", "spread": _street(),
     "enter": {"who": {}, "keep": ["kid", "witch", "cat", "rabbit", "bear", "fox"]},
     "steps": [
        {"do": "fx", "fx": "pot_clear", "wait": 0.2},
        {"do": "cam", "shot": "two_shot", "at": "in_pot", "wait": 0.1},
        {"do": "say", "line": "wc_126"},
        {"do": "say", "line": "wc_127"},
        # every colour: one tap per colour group (ring hints on one ingredient of each; no new voice: same kind of tap)
        {"do": "frame", "with": ["shelf", "pot", "kid"], "wait": 0.3},
        {"do": "brew", "round": 3, "all_colors": True, "shelf": "shelf", "pot": "pot", "ingredients": INGREDIENTS,
         "taps": ["snot", "lantern", "fish"], "result": "ghost", "candy": "story_wc_candies_06", "pot_color": "black",
         "stir": "wc_130", "pop": "wc_131", "eat": "wc_132", "ghost": "wc_x_ghost_kid"},
        {"do": "cam", "shot": "room", "at": "in_focus", "wait": 0.1},
        {"do": "pose", "who": "witch", "pose": "ghost"},
        {"do": "say", "line": "wc_133"},
        {"do": "fx", "fx": "candies_to_all", "wait": 0.6},           # one black candy flies to each of the others
        {"do": "pose", "who": ["cat", "rabbit", "bear", "fox"], "pose": "ghost", "hop": True},
        {"do": "say", "line": "wc_134"},
    ]},
    {"id": "parade", "title": "오~우~ 행진", "spread": _street(light="night"),
     "enter": {"who": {}, "keep": ["kid", "witch", "cat", "rabbit", "bear", "fox"]},
     "steps": [
        # out of the door in a line (ghost march cycles), down the street and round; a high wide so the route reads,
        # then side tracking; a real little ghost tags along at the back (no line), looks back and vanishes (sfx)
        {"do": "fx", "fx": "outside_view", "wait": 1.2},
        {"do": "walk", "who": ["kid", "witch", "cat", "rabbit", "bear", "fox"], "pose": "ghost", "to": "parade_a",
         "path": ["door", "kids_mid", "parade_a"], "speed": 0.35, "follow": "kid", "shot": "high", "line": "wc_135",
         "file": True},                                              # NEW: `file` = walk in single file
        {"do": "fx", "fx": "ghost_tagalong", "wait": 0.1},
        {"do": "walk", "who": ["kid", "witch", "cat", "rabbit", "bear", "fox"], "pose": "ghost", "to": "parade_b",
         "via": "road", "speed": 0.35, "follow": "kid", "shot": "street", "line": "wc_x_ghost_all", "file": True},
        {"do": "cam", "shot": "sky", "at": "moon_loop", "wait": 0.6},
        {"do": "fx", "fx": "ghost_vanish", "wait": 0.6},
        {"do": "go_inside", "who": ["kid", "witch", "cat", "rabbit", "bear", "fox"], "house": "shop", "room": True},
    ]},
    {"id": "finale", "title": "다 같이 변신", "spread": _street(light="evening"),
     "enter": {"who": {"kid": "calm", "witch": "calm", "cat": "sit", "rabbit": "calm", "bear": "calm", "fox": "calm"},
               "at": {"kid": "in_kid", "witch": "in_witch", "cat": "in_cat", "rabbit": "in_friends",
                      "bear": "in_friends", "fox": "in_friends"}},
     "steps": [
        {"do": "fx", "fx": "inside_view", "wait": 1.2},
        {"do": "cam", "shot": "room", "at": "in_focus", "wait": 0.2},
        {"do": "say", "line": "wc_136"},
        {"do": "cam", "shot": "pot", "at": "in_pot", "wait": 0.1},
        {"do": "fx", "fx": "candy_fountain", "wait": 0.3},           # the leftover candies pour out of the pot
        {"do": "say", "line": "wc_137"},
        {"do": "pose", "who": "witch", "pose": "two_candies"},
        {"do": "say", "line": "wc_138"},
        {"do": "cam", "shot": "room", "at": "in_focus", "wait": 0.2},
        # tap each friend: they eat their candy, 뿅, transform (frog / duck / bat); Dahyun, the cat and the witch
        # transform with the third tap (strawberry / fish / pumpkin)
        {"do": "tap_each", "targets": ["rabbit", "bear", "fox"], "prompt": "wc_n04", "hint": "wc_n04",
         "react": {"rabbit": ["tf_frog", "poof"], "bear": ["tf_duck", "poof"], "fox": ["tf_bat", "poof"]}},
        {"do": "fx", "fx": "all_transform", "wait": 0.3},            # kid strawberry, cat fish, witch pumpkin
        {"do": "say", "line": "wc_139"},
        {"do": "fx", "fx": "all_back", "wait": 0.3},
        {"do": "say", "line": "wc_140"},
        {"do": "say", "line": "wc_x_happy_all"},
        {"do": "cam", "shot": "two_shot", "at": "in_pot", "wait": 0.1},
        {"do": "say", "line": "wc_141"},
        {"do": "say", "line": "wc_142"},
        {"do": "tap_steps", "target": "witch", "prompt": "wc_143", "hint": "wc_143", "steps": [{"fx": "witch_wave"}]},
        {"do": "fx", "fx": "outside_view", "wait": 1.0},
        {"do": "cam", "shot": "pull_back", "at": "est", "rate": 0.5, "wait": 3.0},
        {"do": "end", "after": "wc_n02", "close_book": True},
    ]},
]
# brew lines the seeder must see (nested in RESULTS / INGREDIENTS -> scanned recursively)

# ---------------------------------------------------------------- sound (phase 2: shared SoundDirector ids)
SOUND = {
    "beds": {"evening": "amb.night_village", "night": "amb.night_village", "room": "amb.room_fire"},
    "music": {"invite": "music.playful_night", "round1": "music.magic_bubbles", "round2": "music.magic_bubbles",
              "ghost_candy": "music.magic_bubbles", "parade": "music.silly_march", "finale": "music.party"},
    "fx_note": "NEW ids needed (phase 2): wc.drip wc.siren wc.buzz wc.chime wc.kazoo wc.quack wc.plop wc.splash wc.wave "
               "(one per ingredient), wc.bubble_loop, wc.stir_magic, wc.poof, wc.candy_pop, wc.boing (뿅), wc.roll, "
               "wc.bonk (통), wc.flap, wc.ribbit, wc.glow_hum, wc.oooh_wind, owl/cricket night sprinkle, fire crackle",
}
