"""「해님 달님」 (sunmoon) adaptation tables for tools/story/seed_script.py (plan: game/stories/sunmoon/PLAN.md).

Phase 1 (2026-11-22): plan, script, shared art, set prototypes. NOT wired yet: steps marked NEW are phase-2 verbs / fx
(the handler game/stories/sunmoon/fx.gd does not exist yet); the seeded script.json is the data the runner grows into.

Source: 톡톡's sunmoon has two recorded scripts with the same voices: the play script (voice_script_el.json: quizzes,
plate choices, counting 1-10, voice / hand quizzes) and the READ-MODE script (read_script_el.json: the tale told
straight, scenes R01-R11, every line recorded in read_narration_el.js). The pop-up book follows the READ script
(user: story first, no quizzes / counting / morals) and borrows only the play script's first-tap instructions, each
voiced once (sm_002, 006, 068, 074, 078, 091, 104, 115, 130). seed_script.py READ_SCRIPT = True seeds every read line
as sm_r<scene><line> (R01 -> sm_r01xx).

Tone (user): a children's-book tiger, menacing but not horrifying; the mother's fate stays the source's one soft line
(sm_r0506, over a cutaway to the moon going behind a cloud, nothing shown); the sky ending bright and magical.
"""
import math as _m

TALE_ID = "sunmoon"
TITLE = "해님 달님"
PREFIX = "sm"
MORAL = ""  # no moral (user: the book tells the tale); the read script's closing moral sm_r1108 is not used
READ_SCRIPT = True

# ---------------------------------------------------------------- line adaptations
CHANGED = {}
SEG_KEEP = {}
# read lines trimmed to some of their segs (clips reused, nothing to record): the narrator lead-ins the picture shows
READ_SEG_KEEP = {
    "sm_r0505": [1],   # "떡이 다 떨어지자 호랑이가 말했어요." dropped: the tiger's "떡이 없으면 너를 잡아먹어야지!" only
    "sm_r0604": [1],   # "오빠가 말했어요." dropped: the boy's "우리 엄마 목소리가 아니에요! 손을 보여 주세요!"
    "sm_r0704": [0],   # the girl's "오빠, 무서워…" (she takes his hand on screen; the narration of it dropped)
    "sm_r0804": [1],   # "호랑이가 뒷마당에 왔어요." dropped (he walks in on screen): "옳지! 우물 속에 숨었구나!"
    "sm_r0809": [0],   # "어? 위에서 웃음소리가?" only (the look-up shows "고개를 번쩍 들었어요")
    "sm_r0810": [1],   # "얘들아, 거기 어떻게 올라갔니?" only
    "sm_r0814": [1],   # the girl's "도끼로 콕콕 찍고 올라왔지~" only (her laugh is on screen)
    "sm_r1002": [0],   # the tiger's "어흥, 나도 올라가야지!" only (he grabs the rope on screen)
    # pace (305 s of narration -> ~255 s): more lead-ins the picture already tells
    "sm_r0104": [1],   # the mother's "문 꼭 잠그고 엄마 기다려라~" only ("엄마가 말했어요." dropped)
    "sm_r0205": [1, 2],  # "떡을 바구니 가득 받았어요!" dropped (the basket fills on screen by the taps)
    "sm_r0610": [1],   # the boy's "쉿, 뒷문으로 살금살금 도망가자!" only
    "sm_r0811": [1],   # the boy's "참기름 바르고 올라왔지!" only
    "sm_r1103": [1],   # the girl's "오빠, 나는 밤이 무서워요." only
    # v2 pace (432 s -> <= 390 s): the picture tells these
    "sm_r0705": [0],   # the tiger's "얘들아~ 어디 갔니?" only (he searches and goes back on screen)
}
NEW_LINES = {
    # sunmoon's narrator is Huelyn (tc_6a21... / EL nar): the other tales' cover / replay recordings are other narrator
    # voices, so these need recording -- ASK THE USER FIRST (caption placeholders until then: status pending)
    "sm_n01": [["nar", "그림책을 톡 눌러서 펼쳐 볼까요?", None, "[warm, inviting, storytelling, once upon a time]"]],
    "sm_n02": [["nar", "또 보고 싶으면 '다시 보기'를 톡!", None, "[warm, cheerful, inviting]"]],
}
TRIM = {}
# one caption, one voice (audit_clips 2026-11-22, artifacts/sunmoon/clip_audit_p1.txt): the boy's "쉿!" clip says it
# twice (two equal speech blocks 0.13-0.68 s and 1.00-1.59 s): kept the first take, 0-0.84 s, 0.14 s fade-out
TRIM_SEG = {"sm_r0815": {1: ("res://audio/voice/sunmoon/boy_a18c6b958e_t.mp3",
                             "audio/el/sunmoon/boy_a18c6b958e.mp3 (0-0.84 s: first take only)")}}
DROPPED = set()
LINE_META = {
    # recorded 2026-11-22 after the user's OK ("네네네"): narrator voice, eleven_v4 (recorded.json)
    "sm_n01": {}, "sm_n02": {},
    # expression per line (roles: boy, girl, mom, tiger, rich)
    "sm_r0100": {"expr": {"boy": "calm", "girl": "calm", "mom": "calm"}},
    "sm_r0103": {"expr": {"boy": "wave", "girl": "wave", "mom": "wave"}},
    "sm_r0104": {"expr": {"mom": ["wave", "talk"]}},
    "sm_r0201": {"expr": {"mom": "work"}},
    "sm_r0204": {"expr": {"rich": "thanks"}},
    "sm_r0205": {"expr": {"mom": "happy_full", "rich": "smile"}},
    "sm_r0300": {"expr": {"mom": "tired_full"}},
    "sm_r0301": {"expr": {"mom": "scared_full", "tiger": "roar"}},
    "sm_r0302": {"expr": {"tiger": "demand", "mom": "scared_full"}},
    "sm_r0303": {"expr": {"mom": "give"}},
    "sm_r0304": {"expr": {"tiger": ["gulp", "belly1"]}},
    "sm_r0402": {"expr": {"tiger": "demand", "mom": "scared_full"}},
    "sm_r0404": {"expr": {"tiger": ["gulp", "belly1"]}},
    "sm_r0502": {"expr": {"tiger": "demand", "mom": "scared_full"}},
    "sm_r0503": {"expr": {"tiger": ["gulp", "belly2"]}},
    "sm_r0505": {"expr": {"tiger": "sly"}},
    "sm_r0507": {"expr": {"tiger": "dg_calm"}},
    "sm_r0600": {"expr": {"boy": "calm", "girl": "calm"}},
    "sm_r0602": {"expr": {"tiger": ["dg_knock", "dg_sweet", "dg_sweet"], "boy": "scared", "girl": "scared"}},
    "sm_r0604": {"expr": {"boy": "clever"}},
    "sm_r0606": {"expr": {"boy": "scared", "girl": "scared"}},
    "sm_r0609": {"expr": {"boy": "scared", "girl": "scared"}},
    "sm_r0610": {"expr": {"boy": "shush"}},
    "sm_r0704": {"expr": {"girl": "scared"}},
    "sm_r0705": {"expr": {"tiger": ["dg_caught", "dg_side"]}},
    "sm_r0706": {"expr": {"boy": "calm", "girl": "calm"}},
    "sm_r0803": {"expr": {"boy": "sit_hold", "girl": "sit_scared"}},
    "sm_r0804": {"expr": {"tiger": "sly"}},
    "sm_r0806": {"expr": {"tiger": "pull_rope"}},
    "sm_r0808": {"expr": {"boy": "sit_giggle", "girl": "sit_giggle"}},
    "sm_r0809": {"expr": {"tiger": "look_up", "boy": "sit_hold", "girl": "sit_scared"}},
    "sm_r0810": {"expr": {"tiger": "sly"}},
    "sm_r0811": {"expr": {"boy": "sit_giggle"}},
    "sm_r0812": {"expr": {"tiger": "smear_oil"}},
    "sm_r0813": {"expr": {"tiger": "slip", "boy": "sit_giggle", "girl": "sit_giggle"}},
    "sm_r0814": {"expr": {"girl": "sit_giggle"}},
    "sm_r0815": {"expr": {"boy": "sit_hold"}},
    "sm_r0816": {"expr": {"boy": "sit_hold", "girl": "sit_scared"}},
    "sm_r0901": {"expr": {"boy": "sit_hold", "girl": "sit_scared"}},
    "sm_r0902": {"expr": {"boy": "pray"}},
    "sm_r0903": {"expr": {"girl": "wow"}},
    "sm_r1002": {"expr": {"tiger": "grab_up"}},
    "sm_r1006": {"expr": {"tiger": "dazed"}},
    "sm_r1007": {"expr": {"tiger": "run_bump"}},
    "sm_r1103": {"expr": {"girl": "shy"}},
}

# ---------------------------------------------------------------- stage
HANDLER = "res://stories/sunmoon/fx.gd"   # phase 2
BACKDROP = True
INSIDE_FRAMING = "manual"
EXTRA = {"theme": "korean",              # the template dressed as a Joseon countryside (CardLibrary theme)
         # 2026-11-22 (user: "펠트 질감 싫은뎅"): matte cut-paper ground sheets instead of felt (opt-in; the other tales keep
         # felt until the user approves); test card artifacts/sunmoon/ground_felt_vs_paper.png
         "ground_style": "paper",
         "spacing": True, "overlap_check": True, "pop_in": False,
         "overlap_ok": [["boy", "tree"], ["girl", "tree"], ["tiger", "tree"], ["tiger", "well"], ["boy", "jars"],
                        ["girl", "jars"], ["tiger", "boulder_1"], ["tiger", "cairn_2"], ["tiger", "ledge_3"],
                        # v15: the jar terrace printed on both faces (seen from the back yard too); the tiger lands IN
                        # the sorghum (the story: "수수밭에 쿵!")
                        ["boy", "jars_b"], ["girl", "jars_b"], ["tiger", "sorghum_1"], ["tiger", "sorghum_2"], ["tiger", "well_b"], ["boy", "tree_b"], ["girl", "tree_b"],
                        ["tiger", "tree_b"]],
         # v15: the facade folds away a little earlier on the glides into the room (two cream frames at the wall)
         "inside_margin": 0.3}
# Shots [distance, elevation°, focus height, fov, yaw offset°]
SHOTS = {"story": [3.4, 12.0, 0.28, 20.0], "close": [2.9, 12.0, 0.32, 20.0],
         "crane_high": [9.0, 36.0, 0.3, 24.0, 0.0],      # the whole mountain road: three passes in a row
         "establish": [6.5, 18.0, 0.35, 24.0, -6.0],
         "medium": [2.4, 9.0, 0.3, 22.0, 6.0], "two_shot": [2.0, 8.0, 0.3, 24.0, -10.0],
         "face": [1.3, 6.0, 0.3, 22.0, 0.0],
         # the passes are ~2.3 apart and each is a gate of ridge cards: road shots stay INSIDE the gap (distance < 1.9)
         "track_side": [1.6, 16.0, 0.3, 30.0, 70.0],     # the mother on the road, tracked from the side
         "pass_track": [1.7, 22.0, 0.3, 28.0, 0.0],      # into a pass from behind her, over the near ridge's gap
         "track_back": [2.6, 16.0, 0.3, 24.0, 0.0],      # following her up the road
         "pass_low": [1.8, 3.0, 0.32, 30.0, 18.0],       # low: the tiger looming out from the rock
         # (v3: an over-the-shoulder from beyond the tiger looked into his rock; standing cards face the reader)
         "pass_two": [1.5, 14.0, 0.32, 30.0, 35.0],      # angled two-shot: the mother and the tiger across the road
         "pass3_track": [1.7, 22.0, 0.3, 28.0, 22.0],    # pass 3 sits on the road's diagonal bend: look along it
         "basket": [0.9, 30.0, 0.12, 30.0, 0.0],         # the tap: the basket big in frame
         "moon_cut": [1.4, -4.0, 1.1, 44.0, 0.0],        # cutaway up to the moon going behind a cloud (sm_r0506)
         "door_ots": [1.3, 9.0, 0.32, 30.0, 25.0],       # over the disguised tiger's shoulder onto the door
         # inside the cottage (its frame: turned COT_YAW): the camera just behind the hidden front wall
         "room": [0.4, 14.0, 0.18, 62.0, -40.0],         # focus 0.46 deep: the camera 0.06 inside the front wall
         "window_in": [0.34, 4.0, 0.4, 40.0, 140.0],     # turned round: the paper window from inside (hole, eye)
         "door_paw": [0.42, 4.0, 0.24, 56.0, 140.0],     # turned round to the door, the paw low at its edge
         "yard_front": [3.8, 14.0, 0.3, 28.0, -22.0],    # the cottage front, the path: she leaves, they go in
         "pass_low2": [1.8, 3.0, 0.32, 30.0, -18.0],     # pass 2 (sides swapped): the tiger clear of her
         "pass_low3": [1.8, 3.0, 0.32, 30.0, 40.0],      # pass 3 (the road's diagonal bend)
         "yard_high": [4.5, 30.0, 0.3, 26.0, -30.0],     # the back yard: jars, well, tree (route reads)
         "jars_low": [1.4, 4.0, 0.15, 30.0, 10.0],
         "tree_low": [2.6, 2.0, 0.6, 34.0, 0.0],         # low under the tree, tilted up to the fork
         "tree_top": [1.6, 12.0, 1.25, 30.0, -12.0],     # the kids in the fork
         "well_down": [0.9, 55.0, 0.1, 30.0, 0.0],       # looking down into the well (the reflection)
         "rope_up": [3.6, 2.0, 1.7, 46.0, 0.0],         # tilt up the rope into the clouds
         "sky_wide": [5.6, -9.0, 1.9, 44.0, 0.0],        # from the cloud tops up into the sky (the finale)
         "sky_high": [7.0, 18.0, 1.6, 40.0, 0.0],
         "sky_rope": [1.9, -3.0, 0.95, 40.0, 0.0],       # close on the rope: the children climbing out of the clouds
         "pull_back": [10.5, 26.0, 0.3, 24.0, 0.0],
         # v15 (gate audit: the escape never on screen, the roof filling the frame, the brother's face beside the big
         # tiger): yaw -40 looks into the cottage front, 140 from behind, -130 its left (jars) side, 50 its right
         "cot_rise": [3.2, 40.0, 0.3, 30.0, -60.0],       # out of the room through the front wall and up
         "back_left": [2.5, 22.0, 0.25, 30.0, -170.0],    # behind the cottage, from the back-left: back door, jars
         "jars_bl": [1.6, 14.0, 0.18, 30.0, -165.0],      # the jars close, the kids crouched on our side of them
         "corner_l": [2.9, 16.0, 0.25, 40.0, -130.0],     # from the left side: the tiger at the corner, the kids behind the jars
         "yard_crane": [3.6, 52.0, 0.2, 30.0, -20.0],     # high over the roof: jars -> well -> tree, the run reads
         "tree_climb": [3.4, 5.0, 0.9, 38.0, -10.0],
         "run_l": [3.0, 24.0, 0.25, 30.0, -125.0],        # from the left side: the run to the tree goes away from us
         "tree_high": [3.6, 45.0, 0.6, 32.0, -60.0],      # high round the front to the tree (over the roof line)     # the whole trunk: roots to the fork (climbers in frame)
         "well_side": [1.9, 12.0, 0.3, 30.0, 40.0]}      # the well from the tree side (no roof in the lens)

ROLES_LABEL = {"boy": "오빠", "girl": "동생", "mom": "엄마", "tiger": "호랑이", "rich": "부잣집 마님"}
CAST = {
    "boy": {"kind": "actor", "skin": "hanbok_boy", "views": ["front", "side", "back"], "label": "오빠 (brother)"},
    "girl": {"kind": "actor", "skin": "hanbok_girl", "views": ["front", "side", "back"], "label": "동생 (sister)"},
    "mom": {"kind": "actor", "skin": "hanbok_mom", "views": ["front", "side", "back"], "label": "엄마 (mother)"},
    "tiger": {"kind": "actor", "skin": "tiger", "views": ["front", "side", "back"], "label": "호랑이 (tiger)"},
    "rich": {"kind": "actor", "skin": "rich_lady", "views": ["front", "side"], "label": "부잣집 마님 (rich lady)"},
    "sun": {"kind": "hanger", "skin": "sunmoon_sky", "pose": "sun_boy", "screen": [0.3, 0.18], "frac": 0.3},
    "moon": {"kind": "hanger", "skin": "sunmoon_sky", "pose": "moon_girl", "screen": [0.7, 0.18], "frac": 0.3},
}
UI = {
    "cover": [["cast_hanbok_boy_calm", 170], ["cast_hanbok_girl_calm", 160], ["cast_tiger_sly", 260]],
    "end": [["cast_sunmoon_sky_sun_girl", 220], ["cast_sunmoon_sky_moon_boy", 220]],
    "speakers": {"boy": ["오빠", "3d5a9a", "cast_hanbok_boy_calm"], "girl": ["동생", "e8836b", "cast_hanbok_girl_calm"],
                 "mom": ["엄마", "c0604a", "cast_hanbok_mom_calm"], "tiger": ["호랑이", "e08a1e", "cast_tiger_calm"],
                 "rich": ["부잣집 마님", "3e8a5e", "cast_rich_lady_calm"]},
}

# ---------------------------------------------------------------- geometry (world x, z of the seed-1 template)
# the road of seed 1 (tools/story/probe_road.gd, every 4th point, near end z +9.5 -> far end z -9.5); the stream
# crosses it at z -1.8 (the template's plank bridge)
ROAD = [(2.11, 9.53), (1.92, 9.02), (1.74, 8.52), (1.58, 8.12), (1.42, 7.75), (1.24, 7.34), (1.0, 6.87), (0.75, 6.43),
        (0.49, 6.09), (0.24, 5.8), (0.0, 5.54), (-0.21, 5.29), (-0.38, 5.01), (-0.51, 4.68), (-0.59, 4.26),
        (-0.58, 3.85), (-0.51, 3.57), (-0.18, 3.1), (0.21, 2.65), (0.37, 2.35), (0.47, 1.96), (0.52, 1.52),
        (0.52, 1.15), (0.43, 0.6), (0.25, 0.07), (0.13, -0.26), (0.01, -0.68), (-0.12, -1.12), (-0.24, -1.48),
        (-0.44, -1.91), (-0.66, -2.4), (-0.79, -2.85), (-0.86, -3.23), (-0.89, -3.64), (-0.83, -4.09), (-0.67, -4.54),
        (-0.57, -4.87), (-0.56, -5.26), (-0.64, -5.63), (-0.76, -6.02), (-1.0, -6.46), (-1.32, -6.83), (-1.56, -7.11),
        (-1.79, -7.42), (-2.05, -7.78), (-2.29, -8.1), (-2.56, -8.46), (-2.95, -8.95), (-3.28, -9.35)]
VIEWS = {0: ((0.17, 2.70), 10.0), 4: ((-0.79, -4.24), 16.0)}  # template view: anchor (x, z), yaw°


def road_x(z):
    for (x0, z0), (x1, z1) in zip(ROAD, ROAD[1:]):
        if z1 <= z <= z0:
            return x0 + (x1 - x0) * (z0 - z) / max(1e-6, z0 - z1)
    return ROAD[-1][0]


def spot(view, x, z):
    """World (x, z) -> spot [right, toward camera] in a template view's frame."""
    (ax, az), yw = VIEWS[view]
    t = _m.radians(yw)
    dx, dz = x - ax, z - az
    return [round(dx * _m.cos(t) - dz * _m.sin(t), 3), round(dx * _m.sin(t) + dz * _m.cos(t), 3)]


def rot(c, dx, dz, yaw):
    """A point dx right / dz in front of c in a piece turned by yaw° (stage frame [right, toward])."""
    t = _m.radians(yaw)
    return [round(c[0] + dx * _m.cos(t) + dz * _m.sin(t), 3), round(c[1] - dx * _m.sin(t) + dz * _m.cos(t), 3)]


def _e(card, at, name, scale=1.0, **kw):
    e = {"card": card, "at": at, "stage": "full", "name": name, "scale": scale, "clear": 0.6}
    e.update(kw)
    return e


# ---------------------------------------------------------------- spread A: the mountain road (view 4)
# The rich house stands beside the road just past the bridge's near side; then three passes (고개), each a gap
# between two pop-up mountain ridges the road runs through, each with its own hiding place for the tiger:
# a mossy boulder (1, late afternoon), the seonangdang cairn (2, red dusk), a pine on a rock ledge (3, night).
PASS = {"rich": 0.9, "p1": -3.3, "p2": -5.65, "p3": -7.85}
ROAD_A = {}
SET_A = []


def _road_spot(z, side=0.0, ahead=0.0):
    x = road_x(z) + side
    return spot(4, x, z + ahead)


ROAD_A["rich_road"] = _road_spot(PASS["rich"])
ROAD_A["rich_house"] = _road_spot(PASS["rich"] - 0.2, 1.35)
ROAD_A["rich_yard"] = _road_spot(PASS["rich"] + 0.05, 0.62)
ROAD_A["stove"] = _road_spot(PASS["rich"] + 0.45, 0.95)
ROAD_A["siru"] = _road_spot(PASS["rich"] + 0.55, 0.62)
ROAD_A["basin"] = _road_spot(PASS["rich"] + 0.5, 1.25)
ROAD_A["mom_work"] = _road_spot(PASS["rich"] + 0.35, 0.72)
ROAD_A["rich_at"] = _road_spot(PASS["rich"] + 0.05, 1.0)
ROAD_A["tray_at"] = _road_spot(PASS["rich"] + 0.1, 0.82)
SET_A += [_e("story_sm_village_02", "rich_house", "rich_house", yaw=-55.0, clear=1.2),
          _e("story_sm_village_03", "stove", "stove", stage=0, yaw=-40.0),
          _e("story_sm_village_04", "siru", "siru", stage=0, yaw=-30.0),
          _e("story_sm_village_09", "basin", "basin", stage=0, yaw=-30.0)]
for k, pk in enumerate(["p1", "p2", "p3"], start=1):
    z = PASS[pk]
    ROAD_A[f"pass_{k}"] = _road_spot(z)
    ROAD_A[f"pass_{k}_in"] = _road_spot(z + 0.9)             # the mother's mark coming into the pass
    ROAD_A[f"pass_{k}_out"] = _road_spot(z - 0.9)
    # pass 3 sits on the road's last bend (it runs diagonally there): its ridges stand further out and back
    off = 2.6 if k == 3 else 2.05
    ROAD_A[f"ridge_{k}_l"] = _road_spot(z - (0.75 if k == 3 else 0.35), -off)
    ROAD_A[f"ridge_{k}_r"] = _road_spot(z - (0.15 if k == 3 else 0.45), off)
    ROAD_A[f"hide_{k}"] = _road_spot(z - 0.2, 0.66 if k != 2 else -0.66)   # the tiger's hiding place
    # where he stands after stepping out: ahead of her on the road, clear of his rock (v2: beside it he was half hidden)
    ROAD_A[f"tiger_{k}"] = _road_spot(z - 0.5, 0.12 if k != 2 else -0.12)
    ROAD_A[f"mom_{k}"] = _road_spot(z + 0.25, -0.12 if k != 2 else 0.12)
    ROAD_A[f"grass_{k}"] = _road_spot(z + 0.5, -0.75 if k != 2 else 0.8)
    ridges = [("story_sm_mountain_00", "story_sm_mountain_01"), ("story_sm_mountain_03", "story_sm_mountain_00"),
              ("story_sm_mountain_01", "story_sm_mountain_03")][k - 1]
    SET_A += [_e(ridges[0], f"ridge_{k}_l", f"ridge_{k}_l", clear=0.5),
              _e(ridges[1], f"ridge_{k}_r", f"ridge_{k}_r", clear=0.5),
              _e(["story_sm_mountain_04", "story_sm_mountain_05", "story_sm_mountain_08"][k - 1], f"hide_{k}",
                 ["boulder_1", "cairn_2", "ledge_3"][k - 1], clear=0.4),
              _e(["story_sm_mountain_06", "story_sm_mountain_07", "story_sm_mountain_06"][k - 1], f"grass_{k}",
                 f"grass_{k}", clear=0.2)]
ROAD_A["saddle"] = spot(4, -5.9, -9.5)
ROAD_A["far_ridge"] = spot(4, 1.2, -9.4)
ROAD_A["est"] = _road_spot(-3.0)
ROAD_A["mid"] = _road_spot(-5.6)
SET_A += [_e("story_sm_mountain_02", "saddle", "saddle", scale=1.3, clear=0.4),
          _e("story_sm_mountain_03", "far_ridge", "far_ridge", scale=1.2, clear=0.4)]
SKY_NIGHT = {"bg": "#101a3a", "fog": "#24305e", "fog_energy": 0.7, "top": "#0d1636", "horizon": "#34477f",
             "stars": "story_sm_sky_09", "n": 14, "moon": "story_sm_sky_05", "moon_at": [-0.6, 10.5, 2.6, 1.6],
             "far": 17.0}


def _road(**kw):
    sp = {"seed": 1, "view": 4, "place": "road", "light": "afternoon", "spots": ROAD_A, "set": SET_A,
          "focus": "est"}
    sp.update(kw)
    return sp


# ---------------------------------------------------------------- spread B: the cottage (view 0)
# The thatched cottage stands right of the path (world x 1.6, z 4.6), turned to face it (yaw -40), with a body (side
# walls, back, thatch slopes) and its room built inside the footprint (the camera glides in through the closed front
# wall: the refuge stays shut, the tiger never enters). Behind it the back yard: the jar terrace, the well and the big
# zelkova beside it (the kids climb to the fork), the sorghum field beyond (the tiger falls into it).
COT_YAW = -40.0
COT = spot(0, 1.6, 4.6)
HOME = {"cottage": COT}
for nm, (dx, dz) in {"door": (-0.22, 0.32), "door_in": (-0.22, -0.2), "path_end": (-0.22, 1.05),
                     "step": (-0.22, 0.12), "room_back": (0.0, -0.5), "room_floor": (0.0, -0.02),
                     "room_floor2": (0.0, -0.3), "lamp": (0.36, -0.38), "in_boy": (-0.1, -0.44),
                     "in_girl": (0.16, -0.45), "in_focus": (0.0, -0.46), "window_out": (0.2, 0.35),
                     "window_inside": (0.2, -0.02), "wall_in": (0.0, -0.014), "soban": (0.3, -0.22),
                     "door_inside": (-0.22, -0.02),
                     "back_door": (-0.45, -0.75), "back_door_g": (-0.22, -0.82), "mom_door": (-0.34, 0.5), "boy_at": (0.06, 0.52),
                     "girl_at": (0.36, 0.4), "tiger_door": (-0.18, 0.42), "tiger_window": (0.22, 0.4),
                     "jars": (-0.75, -1.05), "corner_g": (-0.78, 0.02), "jars_hide_g": (-0.85, -1.47), "jars_hide": (-0.72, -1.27), "well": (0.35, -1.55),
                     "tree": (0.98, -1.75), "tree_foot": (0.85, -1.45), "tiger_well": (0.12, -1.35),
                     "sorghum_1": (1.75, -2.1), "sorghum_2": (2.35, -2.05), "sorghum_3": (1.55, -2.5),
                     "sorghum_band": (1.9, -2.6), "sorghum_fall": (1.85, -1.9), "fence_1": (-1.25, -1.6),
                     "firewood": (0.62, -0.42), "side_front_l": (-0.95, 0.35), "side_back_l": (-1.0, -0.95),
                     "tree_foot_g": (0.62, -1.3), "hills_exit": (2.9, -0.55), "exit_mid": (1.45, -1.3), "side_back_r": (1.0, -0.9), "yard_focus": (0.3, -1.4), "corner": (-0.9, -0.3),
                     "kids_run": (0.55, -1.25),
                     # v15: the back wall card (cottage_08, the back door open at the house's left) and the escape
                     "back_wall": (0.0, -0.64), "bdoor": (-0.32, -0.66), "out_boy": (-0.27, -0.8),
                     "out_girl": (-0.4, -0.78), "yard_b": (-0.2, -1.12), "yard_g": (-0.42, -1.18),
                     "bk_focus": (-0.45, -0.95), "corner_jars": (-0.85, -0.75), "jars_twin": (-0.75, -1.06),
                     "run_mid": (0.05, -1.4), "tg_start": (-0.95, 0.12), "well_twin": (0.35, -1.56),
                     "tw_via0": (-1.02, -0.62), "tw_via": (-0.45, -0.85), "tiger_trunk": (0.68, -1.45), "tree_twin": (0.98, -1.76)}.items():
    HOME[nm] = rot(COT, dx, dz, COT_YAW)
HOME["front_focus"] = rot(COT, -0.1, 0.6, COT_YAW)
HOME["est"] = rot(COT, 0.1, -0.2, COT_YAW)
HOME["road_by"] = spot(0, road_x(4.6), 4.6)
SET_B = [
    _e("story_sm_cottage_00", "cottage", "cottage", yaw=COT_YAW, clear=1.5, door_in=True, glow=0.6,
       light=[0.6, 0.3, 0.9, "#ffb460", True], box={"depth": 0.62, "body": True}),
    {"card": "story_sm_cottage_06", "at": "room_back", "stage": "full", "name": "room_back", "scale": 1.0, "clear": 0,
     "yaw": COT_YAW},
    # v2 (prototype review): the room seen from inside needs the front wall's inside face (the poked window, the
    # paw at the door) and a floor (the felt showed through); both only while the camera is inside
    {"card": "story_sm_cottage_in_00", "at": "wall_in", "stage": "full", "name": "wall_in", "scale": 1.0, "clear": 0,
     "yaw": COT_YAW + 180.0, "inside_only": True},
    {"card": "story_sm_cottage_in_01", "at": "room_floor", "stage": "full", "name": "room_floor", "scale": 1.0,
     "clear": 0, "yaw": COT_YAW, "flat": True, "lift": 0.02},
    {"card": "story_sm_cottage_in_02", "at": "soban", "stage": "full", "name": "soban", "scale": 1.0, "clear": 0,
     "yaw": COT_YAW},
    {"card": "story_sm_cottage_07", "at": "lamp", "stage": "full", "name": "lamp", "scale": 1.0, "clear": 0,
     "yaw": COT_YAW, "inside_only": True, "light": [0.32, 0.3, 0.8, "#ffb060", True]},
    _e("story_sm_yard_02", "jars", "jars", yaw=COT_YAW, clear=0.5),
    # v15: the jars seen from the back yard (a card's back is plain stock): the same print on the far face
    {"card": "story_sm_yard_02", "at": "jars_twin", "stage": "full", "name": "jars_b", "scale": 1.0, "clear": 1.4,
     "yaw": COT_YAW + 180.0},
    # v15: the cottage's back wall with the back door (the escape is shown from outside: the door swings open, the
    # children step out); the leaf is a handler card (fx back_door)
    {"card": "story_sm_yard_00", "at": "well_twin", "stage": "full", "name": "well_b", "scale": 1.0, "clear": 0,
     "yaw": COT_YAW + 180.0},
    {"card": "story_sm_cottage_08", "at": "back_wall", "stage": "full", "name": "cot_back", "scale": 1.267, "clear": 0,
     "yaw": COT_YAW + 180.0},
    _e("story_sm_yard_00", "well", "well", yaw=COT_YAW, clear=0.5),
    _e("story_sm_tree_01", "tree", "tree", yaw=COT_YAW + 20.0, clear=0.9),
    {"card": "story_sm_tree_01", "at": "tree_twin", "stage": "full", "name": "tree_b", "scale": 1.0, "clear": 0,
     "yaw": COT_YAW + 200.0},
    _e("story_sm_yard_07", "firewood", "firewood", yaw=COT_YAW, clear=0.3),
    _e("story_sm_yard_06", "fence_1", "fence_1", yaw=COT_YAW + 70.0, clear=0.3),
    _e("story_sm_field_00", "sorghum_1", "sorghum_1", yaw=COT_YAW, clear=0.3),
    _e("story_sm_field_01", "sorghum_2", "sorghum_2", yaw=COT_YAW + 10.0, clear=0.3),
    _e("story_sm_field_02", "sorghum_3", "sorghum_3", yaw=COT_YAW - 8.0, clear=0.3),
    _e("story_sm_field_03", "sorghum_band", "sorghum_band", yaw=COT_YAW, clear=0.4),
]
# stepping stones from the door to the path (houses face the road; a short path from each door)
for k in range(4):
    nm = f"cot_st{k}"
    HOME[nm] = rot(COT, -0.22, 0.42 + 0.15 * k, COT_YAW)
    SET_B.append({"card": ["stream_water_21", "stream_water_22"][k % 2], "at": nm, "stage": "full", "name": nm,
                  "scale": 0.5, "clear": 0.08, "yaw": COT_YAW})


def _home(**kw):
    sp = {"seed": 1, "view": 0, "place": "home", "light": "", "spots": HOME, "set": SET_B, "focus": "front_focus"}
    sp.update(kw)
    return sp


# ---------------------------------------------------------------- spread C: the sky (heaven)
# NEW (phase 2): a sky page: the template far below under a floor of pop-up cloud bands (story_sm_sky_00/02/06/07),
# a golden backdrop by day / deep blue by night; the sun and moon are sky hangers with the children's faces.
_CLOUDS = ["story_sm_sky_00", "story_sm_sky_02", "story_sm_sky_06", "story_sm_sky_07"]
SKY_SPOTS = {"rise": [0.0, -0.35], "sun": [-0.9, -0.6], "moon": [0.9, -0.6], "focus": [0.0, -0.3]}
SET_C = []
# v2 (2026-11-22, "a real finale, not template + discs"): a floor of paper cloud bands over the whole view, four rows,
# staggered, the meadow cleared under them; the camera looks up over their tops into the sky
for _r, (_tw, _sc) in enumerate([(1.1, 1.1), (0.55, 1.3), (0.0, 1.5), (-0.7, 1.8), (-2.2, 3.4), (-3.4, 6.0)]):
    for _c in range(6):
        _x = round(-3.0 + _c * 1.2 + (0.6 if _r % 2 else 0.0), 2)
        _nm = f"cloud_{_r}{_c}"
        # v15 (gate audit: "blocky square pixel artifacts in the cloud backdrop"): the cards of one row stood at the
        # same depth and overlapped, z-fighting in blocks; each column now sits a few cm apart
        SKY_SPOTS[_nm] = [_x, round(_tw - 0.025 * _c, 3)]
        SET_C.append({"card": _CLOUDS[(_r + _c) % 4], "at": _nm, "stage": "full", "name": _nm, "scale": _sc,
                      "clear": 2.5, "allow_road": True})
SKY_DAY = {"bg": "#cfe9f7", "fog": "#e3f1f8", "fog_energy": 0.45, "top": "#7ec4ec", "horizon": "#fff0c4",
           "stars": "story_sm_sky_09", "n": 0, "moon": "", "far": 17.0}
SKY_C = {"seed": 1, "view": 2, "place": "sky", "light": "", "spots": SKY_SPOTS, "set": SET_C, "sky": SKY_DAY,
         "focus": "focus"}

# ---------------------------------------------------------------- beats
B_KIDS = {"boy": "boy_at", "girl": "girl_at"}
BEATS = [
    {"id": "cover", "title": "해님 달님", "spread": None, "steps": [{"do": "cover", "prompt": "sm_n01"}]},
    # 1 -- morning at the cottage: the mother goes to work, the children wave her off and lock the door
    {"id": "morning", "title": "산골 오막살이", "spread": _home(light=""),
     "enter": {"who": {"boy": "calm", "girl": "calm", "mom": "wave"},
               "at": {"boy": "boy_at", "girl": "girl_at", "mom": "mom_door"}},
     "steps": [
        {"do": "cam", "shot": "establish", "at": "est", "from": "crane_high", "rate": 1.2, "wait": 0.6},
        {"do": "say", "line": "sm_r0100"},
        {"do": "cam", "shot": "medium", "at": "front_focus", "rate": 1.4, "wait": 0.4},
        {"do": "tap_each", "targets": ["boy", "girl"], "prompt": "sm_002", "hint": "sm_002",
         "react": {"boy": ["wave"], "girl": ["wave"]}},
        {"do": "say", "line": "sm_r0103"},
        {"do": "cam", "shot": "two_shot", "at": "mom_door", "rate": 1.6, "wait": 0.3},
        {"do": "say", "line": "sm_r0104"},
        # she walks down the stepping stones to the path and away up it (back walk cycle), basket on her arm
        # v15: one held shot for both (the follow on her left the children's go-inside off the frame)
        {"do": "cam", "shot": "yard_front", "at": "front_focus", "rate": 1.6, "wait": 0.3},
        {"do": "walk", "who": "mom", "to": "road_by", "dir": "away", "speed": 0.42, "pose": "walk_empty", "async": True},
        # the children go in through the door (one door cycle, seen from behind), the door shuts and is bolted
        {"do": "go_inside", "who": ["boy", "girl"], "house": "cottage", "speed": 0.3},
        {"do": "fx", "fx": "door_bolt", "wait": 0.3},        # NEW fx: a wooden bar slides across (sound only + cam bump)
    ]},
    # 2 -- the rich house by the road: work, the rice cakes into the basket
    {"id": "rich_house", "title": "부잣집", "spread": _road(light="afternoon"),
     "enter": {"who": {"mom": "work", "rich": "smile"}, "at": {"mom": "mom_work", "rich": "rich_at"}},
     "steps": [
        {"do": "cam", "shot": "establish", "at": "rich_yard", "from": "crane_high", "rate": 1.0, "wait": 0.8},
        {"do": "fx", "fx": "pop:basin", "wait": 0.35},   # the rice basin (washing)
        {"do": "fx", "fx": "pop:stove", "wait": 0.35},   # the stove's fire
        {"do": "fx", "fx": "pop:siru", "wait": 0.35},   # the steamer, steam rising
        {"do": "cam", "shot": "two_shot", "at": "rich_yard", "rate": 1.6, "wait": 0.3},
        {"do": "pose", "who": "rich", "pose": "give_tray"},
        {"do": "say", "line": "sm_r0204"},
        {"do": "pose", "who": "mom", "pose": "calm"},
        # three taps: a rice cake hops from the tray into her basket each time (the basket fills: empty -> full)
        {"do": "tap_steps", "target": "tray", "prompt": "sm_006", "hint": "sm_006", "shot": "basket",
         "steps": [{"fx": "cake_to_basket:1"}, {"fx": "cake_to_basket:2"}, {"fx": "cake_to_basket:3"}]},  # NEW fx
        {"do": "say", "line": "sm_r0205"},
        {"do": "walk", "who": "mom", "dir": "away", "dist": 0.9, "speed": 0.45, "follow": "mom", "shot": "track_back", "exit": True}]},
    # 3 -- the first pass (late afternoon): out from behind the boulder
    {"id": "pass1", "title": "첫째 고개", "spread": _road(light="late"),
     "enter": {"who": {"mom": "tired_full"}, "at": {"mom": "pass_1_in"}, "hidden": {"tiger": "hide_1"}},
     "steps": [
        {"do": "cam", "shot": "crane_high", "at": "mid", "rate": 1.1, "wait": 0.3},      # the whole road: 3 passes
        {"do": "walk", "who": "mom", "to": "mom_1", "dir": "away", "speed": 0.34, "follow": "mom",
         "shot": "track_side", "line": "sm_r0300"},
        {"do": "cam", "shot": "pass_low", "at": "tiger_1", "rate": 3.0, "wait": 0.5},   # v15: the rock framed first
        {"do": "fx", "fx": "tiger_out:hide_1:tiger_1", "wait": 1.0},
        {"do": "cam", "shot": "pass_low", "at": "tiger_1", "rate": 3.0, "shake": 0.6, "wait": 0.1},
        {"do": "say", "line": "sm_r0301"},
        {"do": "cam", "shot": "pass_two", "at": ["mom_1", "tiger_1"], "rate": 2.4, "wait": 0.1},  # SPEAKER_OFF: both in
        {"do": "say", "line": "sm_r0302"},
        {"do": "tap_steps", "target": "mom", "prompt": "sm_130", "hint": "sm_130", "shot": "two_shot",
         "steps": [{"fx": "cake_to_tiger:1"}]},                          # NEW fx: a cake arcs into his mouth
        {"do": "say", "line": "sm_r0304"},
        {"do": "walk", "who": "mom", "dir": "away", "dist": 0.9, "speed": 0.45, "follow": "mom", "shot": "track_back", "exit": True}]},
    # 4 -- the second pass (red dusk): out from behind the cairn; two taps, rings only
    {"id": "pass2", "title": "둘째 고개", "spread": _road(light="dusk"),
     "enter": {"who": {"mom": "scared_full", "tiger": "belly1"}, "at": {"mom": "pass_2_in"},
               "hidden": {"tiger": "hide_2"}},
     "steps": [
        {"do": "cam", "shot": "track_side", "at": "pass_2_in", "rate": 1.6, "wait": 1.0},   # v15: land on her first
        {"do": "walk", "who": "mom", "to": "mom_2", "dir": "away", "speed": 0.34, "follow": "mom",
         "shot": "track_side"},  # v10 pace: sm_r0400 cut (the dusk and the second pass are on screen)
        {"do": "cam", "shot": "pass_low2", "at": "tiger_2", "rate": 3.0, "wait": 0.5},   # v15: the rock framed first
        {"do": "fx", "fx": "tiger_out:hide_2:tiger_2", "wait": 1.0},
        {"do": "cam", "shot": "pass_low2", "at": "tiger_2", "rate": 3.0, "shake": 0.4, "wait": 0.1},
        {"do": "say", "line": "sm_r0402"},
        {"do": "tap_steps", "target": "mom", "shot": "two_shot",
         "steps": [{"fx": "cake_to_tiger:2"}]},     # v2 pace: one tap hands over both
        {"do": "say", "line": "sm_r0404"},
        {"do": "walk", "who": "mom", "dir": "away", "dist": 0.9, "speed": 0.45, "follow": "mom", "shot": "track_back", "exit": True}]},
    # 5 -- the third pass (night): eyes in the dark, all the rice cakes, the soft line, the disguise
    {"id": "pass3", "title": "셋째 고개", "spread": _road(light="night", sky=SKY_NIGHT),
     "enter": {"who": {"mom": "scared_full", "tiger": "belly1"}, "at": {"mom": "pass_3_in"},
               "hidden": {"tiger": "hide_3"}},
     "steps": [
        {"do": "cam", "shot": "track_side", "at": "pass_3_in", "rate": 1.6, "wait": 0.8},   # v15: land on her first
        {"do": "walk", "who": "mom", "to": "mom_3", "dir": "away", "speed": 0.3, "follow": "mom",
         "shot": "track_side", "line": "sm_r0500"},
        {"do": "cam", "shot": "pass_low3", "at": "tiger_3", "rate": 2.6, "wait": 0.5},   # v15: the rock framed first
        {"do": "fx", "fx": "eyes_glow:hide_3", "wait": 0.8},           # two warm eye glints by the ledge first
        {"do": "fx", "fx": "tiger_out:hide_3:tiger_3", "wait": 1.0},
        {"do": "cam", "shot": "pass_low3", "at": "tiger_3", "rate": 2.6, "shake": 0.4, "wait": 0.1},
        {"do": "say", "line": "sm_r0502"},
        {"do": "tap_steps", "target": "mom", "shot": "basket", "steps": [{"fx": "cakes_all_to_tiger"}]},
        {"do": "say", "line": "sm_r0503"},
        {"do": "cam", "shot": "two_shot", "at": "mom_3", "rate": 1.6, "wait": 0.2},
        {"do": "say", "line": "sm_r0505"},
        # the source's soft line, over a cutaway: the moon slips behind a cloud; nothing else is shown
        {"do": "cam", "shot": "moon_cut", "at": "pass_3", "rate": 1.2, "wait": 0.4},
        {"do": "fx", "fx": "moon_cloud", "wait": 0.1},                 # NEW: a cloud band drifts over the moon
        {"do": "say", "line": "sm_r0506"},
        {"do": "fx", "fx": "mom_gone", "wait": 0.4},                   # NEW: the mother's card is simply not there
        {"do": "pose", "who": "tiger", "pose": "dg_calm", "hop": True},    # the disguise: a paper flip into her clothes
        # v15 (gate audit 2:23: the walk-away played while the camera was still on the moon, only his ears showed):
        # land on him first, then follow him off in the drawn dg_back cycle
        {"do": "cam", "shot": "medium", "at": "tiger_3", "rate": 1.6, "wait": 1.1},
        {"do": "walk", "who": "tiger", "to": "pass_3_out", "dir": "away", "speed": 0.4, "pose": "dg",
         "follow": "tiger", "shot": "track_back", "line": "sm_r0507", "exit": True}]},
    # 6 -- the door at night: the room, the knock, the paw, the hole, the eye
    {"id": "door", "title": "문밖의 호랑이", "spread": _home(light="night", sky=SKY_NIGHT),
     "enter": {"who": {"boy": "calm", "girl": "calm"}, "at": {"boy": "in_boy", "girl": "in_girl"}},
     "steps": [
        {"do": "cam", "shot": "establish", "at": "est", "rate": 1.0, "wait": 0.2},     # the dark cottage, lit window
        # v15 (gate audit: he arrived while the camera dollied through the door): he comes up the path ON screen
        {"do": "walk", "who": "tiger", "from": "road_by", "to": "tiger_door", "dir": "toward", "speed": 0.6,
         "pose": "dg", "follow": "tiger", "shot": "story"},
        {"do": "cam", "shot": "door_ots", "at": "door", "rate": 1.8, "wait": 0.1},
        {"do": "say", "line": "sm_r0602"},                     # 똑똑똑 / 얘들아~ 엄마 왔다 / 걸걸한 목소리예요
        {"do": "cam", "shot": "room", "at": "in_focus", "rate": 1.6, "wait": 1.0, "settle": 0.5},  # glide in, inside
        {"do": "say", "line": "sm_r0604"},
        # v15: wider, lower, so the floury paw the line names is in the frame (the window_in close showed lattice
        # only); the children stand deep in the room, behind the lens of the turned-round shots (the boy's head swept
        # through the frame)
        {"do": "cam", "shot": "door_paw", "at": "door_inside", "rate": 2.2, "wait": 0.1},   # turned to the door
        {"do": "fx", "fx": "paw_in", "wait": 0.8},             # a floury paw slides in at the door's edge
        {"do": "say", "line": "sm_r0606"},
        {"do": "cam", "shot": "window_in", "at": "window_inside", "rate": 1.8, "wait": 0.2},
        {"do": "tap_steps", "target": "window", "prompt": "sm_069", "hint": "sm_069",
         "steps": [{"fx": "poke_hole"}]},                     # NEW: the paper window card swaps to the poked one
        {"do": "fx", "fx": "eye_blink", "wait": 0.3},          # NEW: a big round eye blinks in the hole
        {"do": "say", "line": "sm_r0609"},
        # SPEAKER_OFF (camera agent 2026-11-22): turn round inside the room to the boy (a "face" shot backed the camera
        # out through the cottage wall and he spoke from behind it)
        {"do": "cam", "shot": "room", "at": "in_boy", "rate": 2.4, "wait": 0.1, "settle": 0.5},
        {"do": "say", "line": "sm_r0610"}]},
    # 7 -- the back yard: out of the back door, hide behind the jars
    # v15 (gate audit: "the escape out of the back door is never shown", the camera went out through the paper wall
    # and held on the lattice): the camera leaves the room through the front wall it came in by, rises and swings
    # round the left side to the back of the cottage; the back door swings in and the children tiptoe out (seen from
    # outside), hide on our side of the jars; the tiger comes round the corner on the far side of them (irony)
    {"id": "backyard", "title": "뒷마당", "spread": _home(light="night", sky=SKY_NIGHT),
     # the children stay in the room (keep) until the camera has left it; fx kids_in then folds them behind the back
     # door (it places them there too, so a --beat start works)
     "enter": {"who": {"boy": "calm", "girl": "calm", "tiger": "dg_calm"}, "keep": ["boy", "girl"],
               "at": {"tiger": "tg_start"}},
     "steps": [
        {"do": "fx", "fx": "door_cards_off", "wait": 0.0},   # the paw / eye cards off before the camera pulls back
        {"do": "cam", "shot": "cot_rise", "at": "est", "rate": 1.3, "wait": 1.4},
        {"do": "fx", "fx": "kids_in", "wait": 0.0},
        {"do": "cam", "shot": "back_left", "at": "bk_focus", "rate": 1.2, "wait": 1.6},
        {"do": "fx", "fx": "back_door:open", "wait": 0.9},
        {"do": "walk", "who": "girl", "to": "yard_g", "speed": 0.22, "async": True},
        {"do": "walk", "who": "boy", "to": "yard_b", "speed": 0.22, "line": "sm_r0701"},
        {"do": "fx", "fx": "back_door:shut", "wait": 0.1},
        {"do": "cam", "shot": "jars_bl", "at": "jars_hide", "rate": 1.6, "wait": 0.6},
        {"do": "tap_steps", "target": "jars", "prompt": "sm_074", "hint": "sm_074", "shot": "jars_bl",
         "steps": [{"fx": "hide_behind:jars"}]},                # they run behind the big jar and crouch
        {"do": "say", "line": "sm_r0704"},
        {"do": "cam", "shot": "corner_l", "at": "corner_jars", "rate": 1.6, "wait": 0.2},
        {"do": "walk", "who": "tiger", "to": "corner", "via": ["side_front_l"], "speed": 0.55, "pose": "dg"},
        {"do": "pose", "who": "tiger", "pose": "search"},
        {"do": "say", "line": "sm_r0705"},
        {"do": "walk", "who": "tiger", "to": "tg_start", "speed": 0.55, "pose": "dg", "exit": True},]},
    # 8 -- the tree by the well: climb, the well, the oil, the axe
    {"id": "tree", "title": "우물가 큰 나무", "spread": _home(light="night", sky=SKY_NIGHT),
     "enter": {"who": {"boy": "calm", "girl": "calm"}, "at": {"boy": "jars_hide", "girl": "jars_hide_g"}},
     "steps": [
        # v15: the run seen from the cottage's left side, away from us to the tree (run_back; the zelkova has a printed
        # back, tree_b): yard_high's follow and a crane over the roof both put the thatch across the lens
        {"do": "cam", "shot": "run_l", "at": "run_mid", "rate": 1.6, "wait": 1.0},
        {"do": "walk", "who": "girl", "to": "tree_foot_g", "speed": 0.7, "pose": "run_cycle", "async": True},
        {"do": "walk", "who": "boy", "to": "tree_foot", "speed": 0.7, "pose": "run_cycle"},
        {"do": "cam", "shot": "tree_high", "at": "tree", "rate": 1.8, "wait": 0.6},    # round the front high (no roof)
        {"do": "cam", "shot": "tree_climb", "at": "tree", "rate": 1.8, "wait": 0.3},   # roots to fork: climbers in frame
        # three taps: each a stretch up the trunk (drawn climb frames A/B, hands on the bark), then onto the fork
        {"do": "tap_steps", "target": "tree", "prompt": "sm_079", "hint": "sm_079", "shot": "tree_climb",
         "steps": [{"fx": "climb_tree:1"}, {"fx": "climb_tree:2"}, {"fx": "climb_tree:3"}]},   # NEW
        {"do": "cam", "shot": "tree_top", "at": "tree", "rate": 1.4, "wait": 0.1},
        {"do": "cam", "shot": "well_side", "at": "tiger_well", "rate": 1.6, "wait": 0.2},
        {"do": "walk", "who": "tiger", "from": "tw_via", "to": "tiger_well", "speed": 0.7,
         "pose": "walk_cycle"},
        {"do": "say", "line": "sm_r0804"},
        {"do": "pose", "who": "tiger", "pose": "peer_well"},
        {"do": "cam", "shot": "well_down", "at": "well", "rate": 1.6, "wait": 0.6},  # the faces in the water
        {"do": "pose", "who": "tiger", "pose": "pull_rope"},
        # SPEAKER_OFF (camera agent 2026-11-22): up from the water to the tiger hauling the rope for his line
        {"do": "cam", "shot": "medium", "at": ["tiger_well", "well"], "rate": 2.4, "wait": 0.1, "settle": 0.5},
        {"do": "say", "line": "sm_r0806"},
        {"do": "fx", "fx": "bucket_splash", "wait": 0.3},
        {"do": "cam", "shot": "tree_top", "at": "tree", "rate": 2.0, "wait": 0.1},  # v10b pace: sm_r0808 cut (their giggle shows; the tiger hears it)
        {"do": "cam", "shot": "tree_low", "at": "tree_foot", "rate": 2.6, "wait": 0.1},
        {"do": "say", "line": "sm_r0809"},
        {"do": "say", "line": "sm_r0810"},
        {"do": "cam", "shot": "tree_top", "at": "tree", "rate": 2.0, "wait": 0.1},
        {"do": "say", "line": "sm_r0811"},
        # v15: he goes to the trunk first (the slips played by the well, off the tree)
        {"do": "cam", "shot": "tree_climb", "at": "tree", "rate": 2.0, "wait": 1.2},
        {"do": "walk", "who": "tiger", "to": "tiger_trunk", "speed": 0.6, "pose": "walk_cycle"},
        {"do": "tap_steps", "target": "oil", "prompt": "sm_091", "hint": "sm_091", "shot": "tree_climb",
         "steps": [{"fx": "oil_smear"}]},                       # NEW: the bottle pours, a glossy streak on the bark
        {"do": "fx", "fx": "tiger_slip:2", "wait": 0.2},       # NEW: two tries, two slides down  # v10 pace: sm_r0813 cut (the slips are shown, with sound)
        {"do": "cam", "shot": "tree_top", "at": "tree", "rate": 2.2, "wait": 0.1},
        {"do": "say", "line": "sm_r0814"},
        {"do": "say", "line": "sm_r0815"},
        {"do": "cam", "shot": "tree_climb", "at": "tree", "rate": 1.8, "wait": 0.1},   # v15: the tiger AND the kids
        {"do": "fx", "fx": "axe_climb", "wait": 0.2},          # NEW: axe frames A/B, a notch per chop, he rises
        {"do": "say", "line": "sm_r0816"}]},
    # 9 -- the rope from the sky
    {"id": "rope", "title": "하늘 동아줄", "spread": _home(light="night", sky=SKY_NIGHT),
     "enter": {"who": {"boy": "sit_hold", "girl": "sit_scared", "tiger": "axe_a"}, "keep": ["boy", "girl", "tiger"]},
     "steps": [
        # v15 (gate audit 4:42: the boy's face floated beside the big tiger in a low "face" shot): the whole trunk
        {"do": "cam", "shot": "tree_climb", "at": "tree", "rate": 2.0, "wait": 0.3, "settle": 0.5},
        {"do": "say", "line": "sm_r0902"},
        {"do": "fx", "fx": "rope_down:good", "wait": 0.3},     # NEW: the golden rope slides down, sparkles, a chime
        {"do": "cam", "shot": "rope_up", "at": "tree", "rate": 1.2, "wait": 0.1},
        {"do": "say", "line": "sm_r0903"},
        {"do": "tap_steps", "target": "rope", "prompt": "sm_104", "hint": "sm_104", "shot": "rope_up",
         "steps": [{"fx": "rope_climb:1"}, {"fx": "rope_climb:2"},
                   {"fx": "rope_climb:3"}]},                    # NEW: up past the cloud bands, the camera rising
        {"do": "say", "line": "sm_r0908"}]},
    # 10 -- the rotten rope and the sorghum field
    {"id": "old_rope", "title": "썩은 동아줄", "spread": _home(light="night", sky=SKY_NIGHT),
     "enter": {"who": {"tiger": "axe_a"}, "keep": ["tiger"]},
     "steps": [
        {"do": "fx", "fx": "rope_gone", "wait": 0.1},          # the golden rope went up with the children
        {"do": "fx", "fx": "rope_down:old", "wait": 0.3},      # comes down while the line says it does
        # 2026-11-22: tree_top framed the canopy below the rope (the rotten rope only showed after the line); the sky
        # shot that showed the golden rope shows this one come down too
        {"do": "cam", "shot": "rope_up", "at": "tree", "rate": 1.2, "wait": 0.2},
        {"do": "say", "line": "sm_r1001"},
        {"do": "pose", "who": "tiger", "pose": "grab_up"},
        {"do": "cam", "shot": "pass_two", "at": "tree_foot", "rate": 2.0, "wait": 0.2, "settle": 0.5},  # SPEAKER_OFF: round the trunk to the tiger
        {"do": "say", "line": "sm_r1002"},
        {"do": "fx", "fx": "tiger_rope_climb", "wait": 0.4},   # NEW: rope_a/b frames, creaks
        {"do": "cam", "shot": "rope_up", "at": "tree", "rate": 1.6, "wait": 0.1},
        {"do": "fx", "fx": "rope_snap", "wait": 0.1},          # NEW: the rope snaps, he falls (falling frame)
        {"do": "cam", "shot": "medium", "at": "sorghum_fall", "rate": 3.0, "shake": 1.0, "wait": 0.1},
        {"do": "say", "line": "sm_r1005"},
        {"do": "pose", "who": "tiger", "pose": "dazed"},
        {"do": "say", "line": "sm_r1006"},
        {"do": "cam", "shot": "yard_high", "at": "exit_mid", "rate": 1.2, "wait": 0.2},  # held wide: the run reads
        {"do": "walk", "who": "tiger", "to": "hills_exit", "via": ["exit_mid"], "speed": 0.8, "pose": "run_bump",
         "exit": True, "line": "sm_r1007"}]},
    # 11 -- the sky: the brother becomes the sun, the sister the moon; they swap; day and night
    {"id": "sky", "title": "해님 달님", "spread": SKY_C,
     "enter": {"who": {}, "at": {"boy": "rise", "girl": "rise"}},
     "steps": [
        {"do": "fx", "fx": "sky_discs", "wait": 0.0},
        {"do": "cam", "shot": "sky_rope", "at": "rise", "from": "sky_rope", "rate": 1.0, "wait": 0.4},
        {"do": "fx", "fx": "sky_rise", "wait": 2.2},           # close: the golden rope, the children climbing out of the clouds
        {"do": "cam", "shot": "sky_wide", "at": "focus", "rate": 1.6, "wait": 0.3},
        {"do": "fx", "fx": "sun_moon_reveal", "wait": 0.6},    # a burst of stars: the sun and the moon grow in the sky
        {"do": "say", "line": "sm_r1101"},
        {"do": "fx", "fx": "night", "wait": 0.3},
        {"do": "say", "line": "sm_r1103"},
        {"do": "say", "line": "sm_r1104"},
        {"do": "fx", "fx": "swap_sun_moon", "wait": 0.8},
        {"do": "fx", "fx": "day", "wait": 0.6},
        {"do": "say", "line": "sm_r1106"},
        {"do": "tap_each", "targets": ["sun_disc", "moon_disc"], "prompt": "sm_115", "hint": "sm_115",
         "react": {"sun_disc": ["-", "day"], "moon_disc": ["-", "night"]}},
        {"do": "fx", "fx": "day", "wait": 0.4},
        {"do": "say", "line": "sm_r1107"},
        {"do": "end", "after": "sm_n02", "close_book": True}]},
]

# ---------------------------------------------------------------- sound (phase 2: SoundDirector ids; sm.* to make)
SOUND = {
    "catalog": "res://audio/sound_catalog.json",
    "light_beds": {"": "day", "morning": "day", "afternoon": "afternoon", "late": "late", "dusk": "dusk",
                   "night": "night"},
    "fx": {"pop:stove": "fire.ignite", "pop:siru": "kitchen.boil",
           "cake_to_basket": "ui.pop", "cake_to_tiger": "sm.gulp", "cakes_all_to_tiger": "sm.gulp_big",
           "tiger_out": "sm.growl_cute", "eyes_glow": "sm.twinkle", "moon_cloud": "amb.gust", "door_bolt": "sm.bolt",
           "paw_in": "sm.paper_rustle", "poke_hole": "sm.paper_poke", "eye_blink": "sm.blink",
           "hide_behind": "sm.scurry", "bucket_splash": "kitchen.splash", "oil_smear": "sm.oil_glug",
           "tiger_slip": "sm.slide", "axe_climb": "sm.chop", "rope_down": "wc.chime", "rope_climb": "sm.rope_creak",
           "tiger_rope_climb": "sm.rope_creak", "rope_snap": "sm.rope_snap", "swap_sun_moon": "wc.sparkle",
           "day": "wc.chime", "night": "wc.glow"},
    "steps": {"cover": {"on_open": {"music": "intro_night", "fade": 0.2}}, "page_turn": "paper.page_turn",
              "go_inside": {"door_open": "door.open", "door_shut": "door.shut"},
              "end": {"close_book": "paper.book_close", "music_fade_on_replay": 2.0}},
    "footsteps": {"boy": "pig", "girl": "pig", "mom": "pig", "tiger": "wolf", "rich": None},
    "fx_note": "sm.* are to be made (phase 2): a soft cute growl (never a real roar), rope creak / snap, paper poke, "
               "chop, slide, gulp; night bed: crickets + owl sprinkles at the tree crowns + mountain wind",
}
_BEAT_SOUND = {"cover": {"music": None, "bed": None},
               "morning": {"music": "home", "bed": "@light", "emitters": ["trees"]},
               "rich_house": {"music": "home", "bed": "@light"},
               "pass1": {"music": "wolf", "bed": "@light", "emitters": ["trees"]},
               "pass2": {"music": "wolf", "bed": "@light", "emitters": ["trees"]},
               "pass3": {"music": "wolf", "bed": "@light", "emitters": ["trees"]},
               "door": {"music": "night", "bed": "room"}, "backyard": {"music": "night", "bed": "@light"},
               "tree": {"music": "chimney", "bed": "@light", "emitters": ["trees"]},
               "rope": {"music": "ending", "bed": "@light"}, "old_rope": {"music": "chimney", "bed": "@light"},
               "sky": {"music": "ending", "bed": None}}
for _b in BEATS:
    if _b["id"] in _BEAT_SOUND:
        _b["sound"] = _BEAT_SOUND[_b["id"]]

# ---------------------------------------------------------------- prototype tour (tools/story/sm_proto.py)
TOUR_ROAD = {"id": "tour_road", "title": "고갯길", "spread": _road(light="late"), "enter": {"who": {}},
             "steps": [{"do": "cam", "shot": "crane_high", "at": "mid", "wait": 0.5},
                       {"do": "cam", "shot": "establish", "at": "rich_yard", "rate": 0.5, "wait": 4.0},
                       {"do": "cam", "shot": "pass_track", "at": "pass_1", "rate": 0.4, "wait": 5.0},
                       {"do": "cam", "shot": "pass_low", "at": "tiger_1", "rate": 0.5, "wait": 4.0},
                       {"do": "cam", "shot": "pass_track", "at": "pass_2", "rate": 0.4, "wait": 5.0},
                       {"do": "cam", "shot": "pass3_track", "at": "pass_3", "rate": 0.4, "wait": 5.0},
                       {"do": "cam", "shot": "crane_high", "at": "mid", "rate": 0.4, "wait": 4.0}]}
TOUR_HOME = {"id": "tour_home", "title": "오막살이", "spread": _home(light="late"), "enter": {"who": {}},
             "steps": [{"do": "cam", "shot": "establish", "at": "est", "wait": 0.5},
                       {"do": "cam", "shot": "medium", "at": "front_focus", "rate": 0.45, "wait": 4.5},
                       {"do": "cam", "shot": "yard_high", "at": "yard_focus", "rate": 0.4, "wait": 5.0},
                       {"do": "cam", "shot": "tree_low", "at": "tree", "rate": 0.4, "wait": 4.5},
                       {"do": "cam", "shot": "tree_top", "at": "tree", "rate": 0.4, "wait": 4.0},
                       {"do": "cam", "shot": "establish", "at": "est", "rate": 0.4, "wait": 4.0}]}
