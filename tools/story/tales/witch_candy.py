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
SHOP_YAW = -45.0  # the candy shop turns to face the road (v2, 2026-11-20); shots inside it turn with it
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
    # v6: the witch names the ingredients while the camera shows each jar; her second line ends at "파란 생선," (its
    # tail "초록은 개구리랑 공룡!" names things not on this shelf): witch_7c64b77bc3.mp3 0-2.95 s, 0.15 s fade-out
    "wc_010": ("파란 건 괴물 응가랑 파란 생선,", "res://audio/voice/witch_candy/witch_7c64b77bc3_t.mp3",
               "audio/el/witch_candy/witch_7c64b77bc3.mp3 (0-2.95 s)"),
    # v8 (user: "말풍선에는 하나만 써있는데 두번 말하는 경우가 있어"): the witch's "어디 가!" clip says it, then again (two speech
    # blocks: 3 syllable nuclei, then 2 more): kept the first take, witch_ed8be17d8d.mp3 0-1.28 s, 0.12 s fade-out
    "wc_117": ("어디 가!", "res://audio/voice/witch_candy/witch_ed8be17d8d_t.mp3",
               "audio/el/witch_candy/witch_ed8be17d8d.mp3 (0-1.28 s: first take only)"),
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
    # NEW lines wc_n01-n04: recorded 2026-11-21 after the user's OK (narrator voice, eleven_v4; recorded.json)
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
    "strawberry": {"said": "wc_076", "candy": "story_wc_candies_00", "pot": "red", "eat": ["wc_082", "wc_089"], "tf": "wc_096",
                   "kid": "wc_102", "act": "wc_110", "extra": ["wc_117"], "figure": "tf_strawberry",
                   "move": "tf_strawberry_ball", "action": "roll_street",
                   "note": "she curls into a strawberry ball, rolls out of the door and down the street, bumps a pumpkin "
                           "lantern (통!), the witch calls from the door (어디 가!), she rolls back"},
    "duck": {"said": "wc_077", "candy": "story_wc_candies_01", "pot": "yellow", "eat": ["wc_083", "wc_090"], "tf": "wc_097",
             "kid": "wc_103", "act": "wc_111", "figure": "tf_duck", "move": "duck_cycle", "action": "waddle_room",
             "note": "duck feet: she waddles round the pot (drawn duck waddle cycle), 호박이 waddles behind her"},
    "fish": {"said": "wc_078", "candy": "story_wc_candies_02", "pot": "blue", "eat": ["wc_084", "wc_091"], "tf": "wc_098",
             "kid": "wc_104", "act": "wc_112", "figure": "tf_fish", "move": "tf_fish", "action": "swim_moon",
             "note": "fish tail: she floats out of the door and up over the roofs, swims a loop round the full moon "
                     "(camera tilts up to the sky), bubbles trail; floats back down to the door"},
    "frog": {"said": "wc_072", "candy": "story_wc_candies_03", "pot": "green", "eat": ["wc_085", "wc_092"], "tf": "wc_154",
             "kid": "wc_105", "act": "wc_113", "figure": "tf_frog_sit", "move": "tf_frog_jump", "action": "hop_roof",
             "note": "frog legs: three hops out of the door and up onto the shop roof (low angle), waves from the ridge, "
                     "hops down"},
    "pumpkin": {"said": "wc_071", "candy": "story_wc_candies_04", "pot": "orange", "eat": ["wc_086", "wc_093"], "tf": "wc_099",
                "kid": "wc_106", "act": "wc_114", "figure": "tf_pumpkin", "move": "walk", "action": "glow_street",
                "note": "her pumpkin tummy glows: the street lanterns dim (light 'dark'), she walks out (drawn walk "
                        "cycle; the glow rides on her) and lights the street around her (warm omni light)"},
    "bat": {"said": "wc_073", "candy": "story_wc_candies_05", "pot": "purple", "eat": ["wc_087", "wc_094"], "tf": "wc_100",
            "kid": "wc_107", "act": "wc_115", "figure": "tf_bat_up", "move": "tf_bat_flap", "action": "fly_moon",
            "note": "bat wings (two drawn wing frames flap): out of the door, up past the roofs, a circle in front of "
                    "the moon with the paper bat silhouettes"},
}
# Autoplay: random pair of ingredients whose result was not shown yet in this run (never a repeat). A child may repeat
# a result; it simply plays again (no correction line).

# ---------------------------------------------------------------- stage
HANDLER = "res://stories/witch_candy/fx.gd"   # phase 2
BACKDROP = True
INSIDE_FRAMING = "manual"
# v3 (user: "물체랑 사람들끼리 자꾸 겹치잖아"): stage spacing solver + OVERLAP / OCCLUDE log; intentional contacts listed
EXTRA = {"spacing": True, "overlap_check": True, "pop_in": False,
         "overlap_ok": [["kid", "logs"], ["witch", "pot"], ["kid", "room_floor"], ["kid", "room_floor2"]]}  # the stage does not reframe taps while the camera is inside the shop (rooms are framed here)
# Shots [distance, elevation°, focus height, fov, yaw offset°] (three_pigs vocabulary + interior shots)
SHOTS = {"story": [3.4, 12.0, 0.28, 20.0], "close": [2.9, 12.0, 0.32, 20.0],
         "crane_high": [8.0, 34.0, 0.3, 22.0, 0.0], "establish": [8.0, 17.0, 0.3, 24.0, -4.0],
         "street": [5.0, 11.0, 0.32, 22.0, 6.0], "medium": [2.6, 9.0, 0.3, 20.0, 6.0],
         "face": [1.5, 7.0, 0.3, 20.0, 0.0],
         "sky": [2.6, 3.0, 0.8, 34.0, 0.0],              # tilt up on her loop over the street, the moon behind
         "sky_wide": [5.5, 2.0, 1.1, 30.0, 0.0],         # the whole sky over the street (parade end, tour)
         "high": [6.0, 28.0, 0.2, 22.0, 4.0], "pull_back": [10.5, 24.0, 0.3, 24.0, 0.0],
         "tour": [3.2, 9.0, 0.3, 22.0, 0.0],             # the village tour: low along the street
         "track": [3.4, 27.0, 0.25, 22.0, 0.0],          # following an action outside: above the roofs (no clipping)
         # v2 (user: "처음 마녀가 인사할때 앞의 집때문에 안보여 ... 카메라를 회전해서"): the camera turns round to face the
         # shop door straight on from the road (the shop faces the road at SHOP_YAW), so nothing stands in between
         "door_cam": [1.6, 14.0, 0.3, 28.0, SHOP_YAW],  # straight on from the road: nothing in between
         "hero": [1.05, 2.0, 0.24, 36.0, SHOP_YAW],      # low on the doorstep: the transformed hero, the light behind
         "door_wide": [2.6, 24.0, 0.3, 26.0, SHOP_YAW],  # raised: the door, its path and a file of people on it
         "roof_cam": [2.6, 14.0, 0.75, 26.0, SHOP_YAW + 12.0],  # the shop roof from the road in front of it
         # inside the shop (camera just behind the front wall, which hides while the camera is inside), in the
         # shop's frame
         "room": [0.58, 22.0, 0.2, 62.0, SHOP_YAW],    # raised a little: the back row shows over the front row      # the whole room from just inside the front wall
         "shelf": [0.48, 9.0, 0.12, 64.0, SHOP_YAW],     # shelf + Dahyun: the pick taps (all 9 framed)
         "pot": [0.42, 18.0, 0.16, 46.0, SHOP_YAW],      # looking down into the pot: swirl, POOF, candy
         "pot_low": [0.42, 4.0, 0.1, 50.0, SHOP_YAW],    # low on the fire (tap the logs)
         "two_shot": [0.5, 6.0, 0.24, 58.0, SHOP_YAW + 8.0],  # witch + Dahyun across the pot
         "face_in": [0.4, 6.0, 0.24, 42.0, SHOP_YAW],
         "jar": [0.3, 6.0, 0.02, 36.0, SHOP_YAW],
         # the pick taps: the shelf close, all nine jars big (each round its own angle)
         "pick1": [0.78, 8.0, 0.02, 34.0, SHOP_YAW],         # straight on
         "pick2": [0.8, 12.0, 0.02, 34.0, SHOP_YAW + 20.0],  # over Dahyun's shoulder from the right
         "pick3": [0.76, 2.0, 0.06, 36.0, SHOP_YAW - 12.0],  # low, a little from the left (the ghost candy)       # push-in on one jar on the shelf as it is named
         # the parade: high enough to clear the roofs (low follow shots put the camera inside house cards)
         "parade_side": [2.6, 32.0, 0.22, 26.0, -25.0],   # the whole file and the back of the line, from above
         "parade_back": [2.4, 40.0, 0.22, 28.0, 30.0],    # following the last marcher closely (the ghost in view)
         "surprise": [1.4, 30.0, 0.25, 30.0, 0.0]}        # everyone turning to the ghost    # close on Dahyun inside
CAST = {
    "kid": {"kind": "actor", "skin": "dahyun", "views": ["front", "side", "back"], "label": "다현이 (little wizard)"},
    # 0.42 tall on the page (v2): she must fit the shop's doorway (0.44 above the sill) with her hat, no clipping on the way in
    "witch": {"kind": "actor", "skin": "candy_witch", "views": ["front", "side", "back"], "label": "사탕 마녀",
              "height": 0.325},  # × the stage actor scale 1.3 = 0.42 tall
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

# ONE spread for the whole tale (no page turn after the cover): the Halloween street on view 5 of the meadow template
# (its road runs straight away from the camera at x -0.3..0.15 from z 0.3 to -2.7, then bends left toward the stream;
# probed with tools/story/probe_spots_wide.gd) with the candy shop at its far end on the right. The shop is a house with
# a body and its room inside the footprint, so going in / out is a camera move through the open door.
# 2026-11-20 (user on the prototype: "마을을 더 많이 각자 할로윈 장식"): 13 houses line the street on both sides and down
# the road, every one dressed differently (story_wc_houses_a/b + story_wc_decor add-ons), lit windows glow, warm pools of
# light at windows, lamps and pumpkins, two strings of lights across the street, a deep-blue night sky with the moon.
import json as _json, os as _os
_CAT = {e["id"]: e for e in _json.load(open(_os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "..", "..",
                                                         "game", "art", "atlas", "catalog.json"), encoding="utf-8"))}
HOUSE_SCALE = 0.85


def _w(card, scale):
    e = _CAT[card]
    return e["height_units"] * scale * e["px"][0] / e["px"][1]


# 2026-11-20 v2 (user: "집 문이 길쪽으로 나있어야 미국식 집 구조"): every house turns to face the road (left side +50°,
# right side -50°, the shop -45°), with a stepping-stone path from its door to the road. Offsets inside a turned house
# (its room, its decorations, its door) are given in the house's own frame and turned here.
import math as _m


def _rot(c, dx, dz, yaw):
    """A point dx right / dz in front of centre c in a piece turned by yaw degrees (stage frame [right, toward])."""
    t = _m.radians(yaw)
    return [round(c[0] + dx * _m.cos(t) + dz * _m.sin(t), 3), round(c[1] - dx * _m.sin(t) + dz * _m.cos(t), 3)]


SHOP = [0.8, -2.9]
SHOP_DOOR_X = 0.16  # the doorway's centre right of the facade's centre (facade px 364 of 582 at 1.05 high)
_door = _rot(SHOP, SHOP_DOOR_X, 0.2, SHOP_YAW)
STREET = {"shop": SHOP, "door": _door, "est": [0.1, -1.2], "street_focus": [0.2, -1.6],
          "kids": [-0.05, 0.45], "kid_at": [-0.02, 0.42], "rabbit_at": [-0.22, 0.5], "bear_at": [0.17, 0.52],
          "fox_at": [-0.1, 0.66], "kids_mid": [-0.05, -1.7], "witch_door": _rot(SHOP, -0.02, 0.36, SHOP_YAW),
          "lantern_bump": [-0.38, -1.05], "moon_loop": [0.4, -3.6], "fly_loop": [0.45, -1.6], "roof": SHOP,
          "parade_a": [-0.22, -0.35], "parade_b": [-0.05, -2.2], "parade_l": [-0.2, -1.6], "parade_u1": [-0.12, 0.12], "parade_u3": [0.14, 0.02],
          "parade_u2": [0.1, -0.45], "parade_r": [0.04, -1.6], "tour_a": [-0.05, 0.6], "tour_b": [-0.05, -2.4],
          # the end of the shop's front path on the road, and halfway down the street (outdoor actions go via the road)
          "road_shop": _rot(SHOP, SHOP_DOOR_X, 1.05, SHOP_YAW), "road_mid": [-0.05, -1.25],
          # the greeting / entry camera stands on the road straight in front of the shop door
          "door_view": _rot(SHOP, SHOP_DOOR_X, 0.45, SHOP_YAW), "cat_door": _rot(SHOP, SHOP_DOOR_X + 0.22, 0.45, SHOP_YAW)}
# inside the shop, in the shop's frame (the facade plane at dz 0, the room 1.0 deep behind it)
for _k, (_dx, _dz) in {"in_back": (0.0, -0.97), "in_shelf": (-0.35, -0.9), "in_pot": (0.22, -0.62),
                       "in_counter": (0.47, -0.92), "in_focus": (0.05, -0.66), "in_beam": (0.0, -0.5),
                       "in_kid": (-0.05, -0.55), "in_witch": (0.5, -0.58), "in_cat": (0.36, -0.4),
                       "in_rabbit": (0.1, -0.88), "in_bear": (0.42, -0.86), "in_fox": (0.6, -0.84),
                       "in_floor": (0.0, -0.02), "in_floor2": (0.0, -0.52),
                       "in_door": (SHOP_DOOR_X, -0.18), "in_shelf_front": (-0.22, -0.66), "in_via": (-0.18, -0.76), "in_right": (0.56, -0.42), "in_right2": (0.5, -0.76)}.items():
    STREET[_k] = _rot(SHOP, _dx, _dz, SHOP_YAW)

LIT = [0.55, 0.32, 0.85, "#ffae5a", False]       # a lit house: warm pool in front of its windows
PUMP = [0.32, 0.06, 0.4, "#ff9a3c", True]        # a jack-o'-lantern / candle: small flickering pool
LAMP = [1.0, 0.43, 1.1, "#ffc070", False]
HOUSE_YAW = {"L": 50.0, "R": -50.0}
# (card, side, z or (x, z), decorations [(card, dx, dz in the house's frame, light)])
_HOUSES = [
    ("story_wc_houses_a_00", "L", 0.45, [("story_wc_decor_15", 0.22, 0.1, PUMP)]),
    ("story_wc_houses_b_02", "L", -0.25, [("story_wc_decor_03", -0.12, 0.12, PUMP)]),
    ("story_wc_houses_a_01", "L", -0.95, [("story_wc_decor_07", 0.3, 0.08, None)]),
    ("story_wc_houses_b_04", "L", -1.65, [("story_wc_decor_09", 0.22, 0.08, PUMP)]),
    ("story_wc_houses_a_02", "L", -2.35, [("story_wc_decor_16", -0.3, 0.1, PUMP)]),
    ("story_wc_houses_a_03", "R", 0.0, [("story_wc_decor_13", 0.3, 0.08, None)]),
    ("story_wc_houses_b_00", "R", -0.75, [("story_wc_decor_12", 0.3, 0.1, None)]),
    ("story_wc_houses_a_06", "R", -1.4, [("story_wc_decor_14", 0.32, 0.1, None)]),
    # second row (behind the first, still facing the road) and down the road
    ("story_wc_houses_b_05", "L2", -0.6, []),
    ("story_wc_houses_b_03", "R2", -0.35, [("story_wc_decor_10", -0.32, 0.08, PUMP)]),
    ("story_wc_houses_a_05", "R2", -1.3, []),
    ("story_wc_houses_b_01", ("R", 0.25, -4.05), None, []),
    ("story_wc_houses_a_04", ("R", 2.0, -3.2), None, [("story_wc_decor_11", -0.36, 0.08, None)]),
]
STONES = ["stream_water_21", "stream_water_22"]
VILLAGE_SET = []


def _path(prefix, door, yaw, n):
    """Stepping stones from a door straight out to the road (the house's facing)."""
    for k in range(n):
        nm = f"{prefix}_st{k}"
        STREET[nm] = _rot(door, 0.0, 0.08 + 0.12 * k, yaw)
        VILLAGE_SET.append({"card": STONES[k % 2], "at": nm, "stage": "full", "name": nm, "scale": 0.55, "clear": 0.08,
                            "yaw": yaw})


for _i, (_card, _side, _z, _dec) in enumerate(_HOUSES):
    _hw = _w(_card, HOUSE_SCALE) * 0.5
    if isinstance(_side, tuple):
        _side, _x, _z = _side
        _yaw = HOUSE_YAW[_side]
    else:
        _yaw = HOUSE_YAW[_side[0]]
        _ext = _hw * _m.cos(_m.radians(50))  # half the turned card's x extent
        _x = {"L": -0.52 - _ext, "R": 0.24 + _ext, "L2": -1.55 - _ext, "R2": 1.25 + _ext}[_side]
    _nm = f"house_{_i}"
    STREET[_nm] = [round(_x, 3), _z]
    VILLAGE_SET.append({"card": _card, "at": _nm, "stage": "full", "name": _nm, "scale": HOUSE_SCALE, "clear": 1.0,
                        "glow": 0.9, "light": LIT, "yaw": _yaw,
                        # v3 (user: "사선으로 돼 있으니까 집도 집처럼"): side walls, back and roof from the house itself
                        "box": {"depth": round(min(0.42, _hw * 1.1), 3), "body": True}})
    for _j, (_dc, _dx, _dz, _lt) in enumerate(_dec):
        _dn = f"{_nm}_d{_j}"
        STREET[_dn] = _rot([_x, _z], _dx, _dz, _yaw)
        _e = {"card": _dc, "at": _dn, "stage": "full", "name": _dn, "scale": 1.0, "clear": 0.15, "glow": 0.8, "yaw": _yaw}
        if _lt:
            _e["light"] = _lt
        VILLAGE_SET.append(_e)
    if _side in ("L", "R") and _i < 8:  # first-row houses: a path from the door to the road's edge (not onto it)
        _path(_nm, _rot([_x, _z], 0.0, 0.02, _yaw), _yaw, {5: 1}.get(_i, 3))
_path("shop", _rot(SHOP, SHOP_DOOR_X, 0.02, SHOP_YAW), SHOP_YAW, 6)
# street furniture: lamps on the verges, pumpkins along the road edges, two strings of lights across the street
for _nm, _card, _pt, _sc, _lt, _extra in [
        ("lamp_l", "story_wc_halloween_13", [-0.5, 0.12], 1.0, LAMP, {}),
        ("lamp_r", "story_wc_halloween_13", [0.33, -0.9], 1.0, LAMP, {}),
        ("lamp_r2", "story_wc_halloween_13", _rot(SHOP, -0.78, 0.12, SHOP_YAW), 1.0, LAMP, {"yaw": SHOP_YAW}),
        ("pump_1", "story_wc_halloween_01", [-0.47, -0.6], 1.0, PUMP, {}),
        ("pump_2", "story_wc_halloween_00", [-0.5, 0.75], 1.0, PUMP, {}),
        ("pump_3", "story_wc_halloween_03", [-0.52, -2.0], 1.0, PUMP, {}),
        ("pump_bump", "story_wc_halloween_02", [-0.47, -1.3], 1.0, PUMP, {}),
        ("shop_p1", "story_wc_halloween_02", _rot(SHOP, SHOP_DOOR_X - 0.34, 0.1, SHOP_YAW), 0.8, PUMP, {"yaw": SHOP_YAW}),
        ("broom", "story_wc_halloween_15", _rot(SHOP, 0.62, -0.02, SHOP_YAW), 1.0, None, {"yaw": SHOP_YAW}),
        ("lights_1", "story_wc_decor_00", [-0.08, -0.4], 1.45, None, {"allow_road": True}),
        ("lights_2", "story_wc_decor_01", [-0.1, -1.95], 1.25, None, {"allow_road": True}),
        ("hay_1", "story_wc_halloween_17", [-1.3, 0.75], 1.0, None, {})]:
    STREET[_nm] = _pt
    _e = {"card": _card, "at": _nm, "stage": "full", "name": _nm, "scale": _sc, "clear": 0.15, "glow": 0.8}
    if _lt:
        _e["light"] = _lt
    _e.update(_extra)
    VILLAGE_SET.append(_e)
SKY = {"bg": "#0b1230", "fog": "#1b2856", "fog_energy": 0.75, "top": "#0a1130", "horizon": "#2e4387",
       "stars": "story_wc_halloween_11", "n": 16, "moon": "story_wc_halloween_10", "moon_at": [0.9, 12.0, 3.1, 2.4],
       "far": 17.0}
ROOM_SET = [
    # plank floor lying flat over the whole room, a little above the meadow (its felt is higher toward the back)
    {"card": "story_wc_room_03", "at": "in_floor", "stage": "full", "flat": True, "name": "room_floor", "scale": 1.22,
     "clear": 0, "lift": 0.02},
    {"card": "story_wc_room_03", "at": "in_floor2", "stage": "full", "flat": True, "name": "room_floor2", "scale": 1.22,
     "clear": 0, "lift": 0.02},
    {"card": "story_wc_room_09", "at": "in_back", "stage": "full", "name": "room_back", "scale": 1.0, "clear": 0},
    {"card": "story_wc_room_04", "at": "in_shelf", "stage": "full", "name": "shelf", "scale": 1.0, "clear": 0},
    {"card": "story_wc_room_06", "at": "in_counter", "stage": "full", "name": "counter", "scale": 1.0, "clear": 0},
    {"card": "story_wc_room_07", "at": "in_pot", "stage": "full", "name": "hearth", "scale": 1.0, "clear": 0},
    {"card": "story_wc_pot_12", "at": "in_pot", "stage": 0, "name": "logs", "scale": 1.0, "clear": 0, "front": 0.01},
    {"card": "story_wc_pot_00", "at": "in_pot", "stage": "full", "name": "pot", "scale": 1.0,
     "clear": 0, "lift": 0.05, "front": 0.03, "light": [0.35, 0.05, 0.7, "#ff8a3a", True]},
    {"card": "story_wc_room_08", "at": "in_beam", "stage": "full", "name": "beam", "scale": 1.0, "clear": 0,
     "lift": 0.42, "inside_only": True, "light": [0.35, -0.05, 1.0, "#ffb870", True]},
]
for _e in ROOM_SET:  # the room turns with the shop; "front" = a hair toward the shop front (in the shop's frame)
    _e["yaw"] = SHOP_YAW
    if "front" in _e:
        STREET[_e["name"] + "_at"] = _rot(STREET[_e["at"]], 0.0, _e.pop("front"), SHOP_YAW)
        _e["at"] = _e["name"] + "_at"
SHOP_SET = [
    {"card": "story_wc_shop_00", "at": "shop", "stage": "full", "name": "shop", "scale": 1.0, "clear": 2.0,
     "glow": 0.9, "light": [0.7, 0.4, 1.0, "#ffae5a", False], "yaw": SHOP_YAW, "door_in": True,
     "box": {"depth": 1.0, "side": "story_wc_shop_02", "floor": "story_wc_room_03"}},
] + ROOM_SET + VILLAGE_SET


def _street(**kw):
    sp = {"seed": 1, "view": 5, "place": "street", "light": "night", "sky": SKY, "spots": STREET, "set": SHOP_SET}
    sp.update(kw)
    return sp


ROUND = {  # NEW verb `brew`: one round = pick two -> stir -> POOF -> candy -> eat -> transform -> action -> back
    "pick": {"shelf": "shelf", "pot": "pot", "picks": 2, "ingredients": INGREDIENTS, "combos": COMBOS,
             "results": RESULTS, "and_in": True, "autoplay": "random_new_result"},
}

ALL = ["kid", "witch", "cat", "rabbit", "bear", "fox"]
ROOM_AT = {"kid": "in_kid", "witch": "in_witch", "cat": "in_cat", "rabbit": "in_rabbit", "bear": "in_bear",
           "fox": "in_fox"}
ROOM_WHO = {"kid": "calm", "witch": "calm", "cat": "sit", "rabbit": "calm", "bear": "calm", "fox": "calm"}
KEEP = {"who": ROOM_WHO, "at": ROOM_AT}  # (also places the cast when a run starts at this beat with --beat)

BEATS = [
    {"id": "cover", "title": "사탕 마녀의 핼러윈", "spread": None, "steps": [{"do": "cover", "prompt": "wc_n01"}]},
    {"id": "invite", "title": "초대장", "spread": _street(),
     "enter": {"who": {"kid": "calm", "rabbit": "calm", "bear": "calm", "fox": "calm"},
               "at": {"kid": "kid_at", "rabbit": "rabbit_at", "bear": "bear_at", "fox": "fox_at"}},
     "steps": [
        # the Halloween street: a crane down over the lit houses, the shop glowing dimly at the far end
        {"do": "cam", "shot": "establish", "at": "est", "from": "crane_high", "rate": 0.9, "wait": 1.6},
        # four pumpkin invitations ride the wind in from the end of the street, the camera following one
        {"do": "fx", "fx": "invites_flutter", "wait": 0.2},
        {"do": "say", "line": "wc_000"},
        {"do": "fx", "fx": "", "wait": 1.2},
        {"do": "cam", "shot": "medium", "at": "kids", "rate": 1.6, "wait": 0.6},
        # tap the three cards hovering over the friends: each lands in its friend's hands
        {"do": "tap_each", "targets": ["invite_1", "invite_2", "invite_3"], "prompt": "wc_n03", "hint": "wc_n03",
         "react": {"invite_1": ["-", "catch:rabbit"], "invite_2": ["-", "catch:bear"], "invite_3": ["-", "catch:fox"]}},
        {"do": "fx", "fx": "catch:kid", "wait": 0.5},
        {"do": "cam", "shot": "face", "at": "kid_at", "wait": 0.2},
        {"do": "say", "line": "wc_001"},
        # the shop at the street's end lights up: a slow push down the street
        {"do": "cam", "shot": "street", "at": "street_focus", "rate": 1.0, "wait": 0.6},
        {"do": "fx", "fx": "shop_lights_on", "wait": 0.8},
        {"do": "say", "line": "wc_002"},
        # up the street (back walk cycles), the camera following them
        {"do": "walk", "who": ["kid", "rabbit", "bear", "fox"], "dist": 1.9, "dir": "away", "speed": 0.5,
         "follow": "kid", "shot": "street"},
        # the camera turns round on the road to face the shop door straight on: the witch in full view
        {"do": "cam", "shot": "door_cam", "at": "door_view", "rate": 1.4, "wait": 0.6},
        {"do": "fx", "fx": "door_open", "wait": 0.4},
        {"do": "walk", "who": "witch", "from": "in_door", "to": "witch_door", "dir": "toward", "speed": 0.28},
        {"do": "pose", "who": "witch", "pose": "welcome", "wait": 0.1},
        {"do": "say", "line": "wc_003"},
        {"do": "walk", "who": "cat", "from": "in_door", "to": "cat_door", "dir": "toward", "speed": 0.28, "async": True},
        {"do": "cam", "shot": "door_cam", "at": "door_view", "rate": 1.4, "wait": 0.1},
        # one door, everyone in (seen from behind), on into the room to their places
        # the witch leads them in; the small cat waits last (nearest the camera), nobody hides the door
        {"do": "go_inside", "who": ["rabbit", "bear", "fox", "witch", "kid", "cat"], "house": "shop",
         "to": ROOM_AT, "via": {"rabbit": ["in_right", "in_right2"], "bear": ["in_right"], "fox": ["in_right"]}, "queue": "front", "approach": "road_shop", "queue_gap": 0.16, "house_facing": True, "door_clear": True, "climb_steps": True, "speed": 0.62,
         "line": "wc_004"},
    ]},
    {"id": "fire", "title": "뽀글뽀글 솥", "spread": _street(),
     "enter": {"who": ROOM_WHO, "at": ROOM_AT},
     "steps": [
        {"do": "fx", "fx": "inside_view", "wait": 1.8},           # the camera glides in through the door
        {"do": "pose", "who": "witch", "pose": "welcome", "wait": 0.1},
        {"do": "say", "line": "wc_005"},
        {"do": "cam", "shot": "pot_low", "at": "in_pot", "rate": 1.8, "wait": 0.6},
        {"do": "fx", "fx": "up:logs", "wait": 0.5},
        # tap the logs x3: small, medium, big flame; then the water rises and bubbles
        {"do": "tap_steps", "target": "logs", "prompt": "wc_006", "hint": "wc_006",
         "steps": [{"fx": "flame_s"}, {"fx": "flame_m"}, {"fx": "flame_l"}]},
        {"do": "fx", "fx": "pot_water", "wait": 0.6},
        {"do": "cam", "shot": "room", "at": "in_focus", "rate": 1.4, "wait": 0.2},
        {"do": "say", "line": "wc_007"},
        {"do": "pose", "who": "cat", "pose": "meow"},
        {"do": "say", "line": "wc_008"},
    ]},
    {"id": "shelf", "title": "으엑, 재료!", "spread": _street(), "enter": KEEP,
     "steps": [
        {"do": "cam", "shot": "shelf", "at": "in_shelf_front", "rate": 1.4, "wait": 0.4},
        {"do": "fx", "fx": "shelf_pop", "wait": 2.6},              # the nine ingredients pop onto the shelf
        # v6 (user: "콧물이랑 응가요 하는 게 좀 뜬금없고"): the witch names them, the camera pushes in on each jar as it is
        # named (times from the clips' pauses), then straight to Dahyun's yuck
        {"do": "pose", "who": "witch", "pose": "welcome", "wait": 0.0},
        {"do": "name_jars", "line": "wc_009", "at": [[2.3, "snot"], [3.85, "firetruck"], [5.15, "lantern"], [6.4, "chickfart"]]},
        {"do": "name_jars", "line": "wc_010", "at": [[0.3, "poo"], [1.95, "fish"]], "then": "kid_yuck"},
        {"do": "pose", "who": "kid", "pose": "yuck", "wait": 0.0},
        {"do": "say", "line": "wc_011"},
        {"do": "say", "line": "wc_038"},
        {"do": "cam", "shot": "two_shot", "at": "in_pot", "rate": 1.8, "wait": 0.2},
        {"do": "say", "line": "wc_039"},
        {"do": "say", "line": "wc_040"},
    ]},
    {"id": "round1", "title": "마법 사탕", "spread": _street(), "enter": KEEP,
     "steps": [
        # brew: pick 2 (prompt voiced), "A랑 B를 넣었어요!" (+ 으엑 for snot / poo), magic stir, POOF, candy, offer,
        # eat, 뿅 transform, the action (out of the door and back), giggle, 뿅 back, she walks back in
        {"do": "brew", "round": 1, "prompt": "wc_041", "hint": "wc_041", **ROUND["pick"],
         "stir": "wc_046", "pop": "wc_079", "offer": "wc_080", "after": ["wc_109"], "back": "wc_119"},
    ]},
    {"id": "round2", "title": "한 번 더", "spread": _street(), "enter": KEEP,
     "steps": [
        {"do": "cam", "shot": "two_shot", "at": "in_pot", "rate": 1.6, "wait": 0.2},
        {"do": "pose", "who": "witch", "pose": "giggle"},
        {"do": "say", "line": "wc_120"},
        {"do": "fx", "fx": "pot_clear", "wait": 0.2},
        {"do": "say", "line": "wc_125"},
        # round 2: ring hint only (voiced once in round 1), no offer, "냠…" eat line, back with a 뿅 only
        {"do": "brew", "round": 2, **ROUND["pick"], "stir": "wc_045"},
    ]},
    {"id": "ghost_candy", "title": "유령 사탕", "spread": _street(), "enter": KEEP,
     # v3 (user: "유령을 좀 더 극적으로", then "유령이 처음엔 나온지 몰라야지 나중에 놀라는거"): the little ghost sneaks in
     # unnoticed (four glimpses a child can spot, each bolder, nobody reacts); the build-up (lights dim, pot glows,
     # candy rises), the ghost lips close-up with wisps; then the surprise nose to nose, the roam, and a 까꿍
     "steps": [
        {"do": "fx", "fx": "pot_clear", "wait": 0.2},
        {"do": "cam", "shot": "two_shot", "at": "in_pot", "rate": 1.6, "wait": 0.2},
        {"do": "pose", "who": "witch", "pose": "welcome"},
        {"do": "cam", "shot": "room", "at": "in_focus", "rate": 1.2, "wait": 0.1},
        {"do": "say", "line": "wc_126"},
        {"do": "pose", "who": "kid", "pose": "wow"},
        {"do": "cam", "shot": "two_shot", "at": "in_pot", "rate": 1.6, "wait": 0.1},
        {"do": "say", "line": "wc_127"},
        {"do": "brew", "round": 3, "all_colors": True, "ingredients": INGREDIENTS, "taps": ["snot", "lantern", "fish"],
         "result": "ghost", "candy": "story_wc_candies_06", "pot_color": "black", "stir": "wc_130", "pop": "wc_131",
         "eat": "wc_132", "ghost": "wc_x_ghost_kid"},
        {"do": "cam", "shot": "room", "at": "in_focus", "rate": 1.6, "wait": 0.1},
        {"do": "fx", "fx": "black_mouth:witch", "wait": 0.0},
        {"do": "pose", "who": "witch", "pose": "ghost"},
        {"do": "say", "line": "wc_133"},
        {"do": "fx", "fx": "candies_to_all", "wait": 0.8},
        {"do": "fx", "fx": "black_mouth:others", "wait": 0.0},
        {"do": "pose", "who": ["cat", "rabbit", "bear", "fox"], "pose": "ghost", "hop": True},
        {"do": "fx", "fx": "float_all", "wait": 0.1},
        {"do": "cam", "shot": "two_shot", "at": "in_rabbit", "rate": 1.4, "wait": 0.1},  # their black lips, close
        {"do": "say", "line": "wc_134"},
    ]},
    {"id": "parade", "title": "오~우~ 행진", "spread": _street(), "enter": KEEP,
     # v6 (user: "유령 흉내를 내면서 걸을 때 갑자기 뒤에 몰래 유령이 생기는 거야"): the real little ghost quietly joins the
     # back of the line while they play; nobody knows until the end of the walk; then the surprise and its flight
     "steps": [
        {"do": "fx", "fx": "outside_view", "wait": 0.6},
        {"do": "cam", "shot": "door_wide", "at": "door_view", "rate": 1.6, "wait": 0.4},
        {"do": "leave_shop", "who": ALL, "pose": "ghost", "to": "road_shop", "spacing": 0.21},
        {"do": "fx", "fx": "ghost_sneak", "wait": 0.0},
        {"do": "walk", "who": ALL, "pose": "ghost", "path": ["road_shop", "parade_l", "parade_a"], "file": True,
         "spacing": 0.17, "speed": 0.46, "follow": "fox", "shot": "parade_side", "line": "wc_135"},
        {"do": "walk", "who": ALL, "pose": "ghost", "path": ["parade_u1", "parade_u3", "parade_u2", "parade_r", "road_shop"],
         "file": True, "spacing": 0.17, "speed": 0.46, "follow": "fox", "shot": "parade_back", "line": "wc_x_ghost_all"},
        {"do": "parade_surprise"},
        {"do": "ghost_flight"},
        {"do": "fx", "fx": "ghost_vanish", "wait": 1.0},
        {"do": "cam", "shot": "door_wide", "at": "door_view", "rate": 1.4, "wait": 0.2},
        {"do": "go_inside", "who": ["kid", "witch", "cat", "rabbit", "bear", "fox"], "house": "shop", "to": ROOM_AT,
         "via": {"rabbit": ["in_right", "in_right2"], "bear": ["in_right"], "fox": ["in_right"]}, "queue": "front", "approach": "road_shop",
         "queue_gap": 0.16, "house_facing": True, "door_clear": True, "climb_steps": True, "speed": 0.65},
    ]},
    {"id": "finale", "title": "다 같이 변신", "spread": _street(),
     "enter": {"who": ROOM_WHO, "at": ROOM_AT},
     "steps": [
        {"do": "fx", "fx": "inside_view", "wait": 1.6},
        {"do": "pose", "who": "witch", "pose": "welcome"},
        {"do": "say", "line": "wc_136"},
        {"do": "cam", "shot": "pot", "at": "in_pot", "rate": 1.8, "wait": 0.1},
        {"do": "fx", "fx": "candy_fountain", "wait": 0.6},         # the leftover candies pour out of the pot
        {"do": "say", "line": "wc_137"},
        {"do": "cam", "shot": "room", "at": "in_focus", "rate": 1.6, "wait": 0.1},
        {"do": "pose", "who": "witch", "pose": "two_candies", "wait": 0.8},  # (wc_138 dropped for pace, 2026-11-20)
        # tap each friend: they eat their candy, 뿅, frog / duck / bat; then Dahyun, the cat and the witch
        {"do": "tap_each", "targets": ["rabbit", "bear", "fox"], "prompt": "wc_n04", "hint": "wc_n04",
         "react": {"rabbit": ["tf_frog", "poof:rabbit"], "bear": ["tf_duck", "poof:bear"], "fox": ["tf_bat", "poof:fox"]}},
        {"do": "fx", "fx": "all_transform", "wait": 0.6},
        {"do": "say", "line": "wc_139"},
        {"do": "fx", "fx": "all_back", "wait": 0.4},
        {"do": "say", "line": "wc_140"},
        {"do": "pose", "who": ALL, "pose": "cheer"},
        {"do": "say", "line": "wc_x_happy_all"},
        {"do": "cam", "shot": "two_shot", "at": "in_pot", "rate": 1.6, "wait": 0.1},
        {"do": "say", "line": "wc_141"},
        {"do": "say", "line": "wc_142"},
        {"do": "tap_steps", "target": "witch", "prompt": "wc_143", "hint": "wc_143", "steps": [{"fx": "witch_wave"}]},
        {"do": "fx", "fx": "outside_view", "wait": 1.2},
        {"do": "cam", "shot": "pull_back", "at": "est", "rate": 0.6, "wait": 2.4},
        {"do": "end", "after": "wc_n02", "close_book": True},
    ]},
]
# the village tour (a slow camera along the street, for the village clip; not part of the tale): --beat=tour
TOUR = {"id": "tour", "title": "할로윈 마을", "spread": _street(), "enter": {"who": {}},
        "steps": [{"do": "cam", "shot": "crane_high", "at": "tour_a", "wait": 0.5},
                  {"do": "cam", "shot": "tour", "at": "tour_a", "rate": 0.5, "wait": 4.0},
                  {"do": "cam", "shot": "tour", "at": "street_focus", "rate": 0.35, "wait": 6.0},
                  {"do": "cam", "shot": "tour", "at": "tour_b", "rate": 0.35, "wait": 6.0},
                  {"do": "cam", "shot": "sky_wide", "at": "moon_loop", "rate": 0.4, "wait": 5.0},
                  {"do": "cam", "shot": "establish", "at": "est", "rate": 0.4, "wait": 5.0}]}

# ---------------------------------------------------------------- sound (phase 2: shared SoundDirector ids)
SOUND = {
    "catalog": "res://audio/sound_catalog.json",
    "light_beds": {"": "night", "night": "night", "evening": "night", "dusk": "dusk"},
    "fx": {"invites_flutter": "wc.flutter", "shop_lights_on": "wc.chime", "up:logs": "ui.pop",
           "pot_water": "wc.bubble", "pot_clear": "wc.wave", "shelf_pop": "wc.sparkle",
           "candies_to_all": "wc.candy_pop", "candy_fountain": "wc.sparkle", "all_transform": "wc.boing",
           "all_back": "wc.boing", "witch_wave": "wc.giggle_bells", "ghost_vanish": "wc.vanish",
           "inside_view": {"bed": "room", "fade": 1.5}, "outside_view": {"bed": "@light", "fade": 1.5}},
    "steps": {"cover": {"on_open": "paper.page_turn"}, "page_turn": "paper.page_turn",
              "go_inside": {"door_open": "door.open", "door_shut": "door.shut"},
              "end": {"close_book": "paper.book_close", "music_fade_on_replay": 2.0}},
    # footsteps on drawn-cycle contact frames: light child steps (the pig set), the witch heavier (the wolf set)
    "footsteps": {"kid": "pig", "rabbit": "pig", "bear": "pig", "fox": "pig", "witch": "wolf", "cat": None},
    "fx_note": "wc.* are synthesised placeholders (tools/audio/wc_synth_sfx.py); nobody has listened yet",
}
_BEAT_SOUND = {"cover": {"music": "night", "bed": None},
               "invite": {"music": "night", "bed": "@light", "emitters": ["trees"]},
               "fire": {"music": "home", "bed": "room"}, "shelf": {"music": "home", "bed": "room"},
               "round1": {"music": "build", "bed": "room"}, "round2": {"music": "build", "bed": "room"},
               "ghost_candy": {"music": "build", "bed": "room"},
               "parade": {"music": "ending", "bed": "@light", "emitters": ["trees"]},
               "finale": {"music": "ending", "bed": "room"}}
for _b in BEATS:
    if _b["id"] in _BEAT_SOUND:
        _b["sound"] = _BEAT_SOUND[_b["id"]]
