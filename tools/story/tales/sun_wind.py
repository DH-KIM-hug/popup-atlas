"""「해와 바람」 (sun_wind) adaptation tables for tools/story/seed_script.py (moved out of the seeder 2026-11-18)."""
TALE_ID = "sun_wind"
TITLE = "해와 바람"
PREFIX = "sw"  # line ids sw_000.., sw_x_<extra>, new lines sw_nNN
HANDLER = "res://stories/sun_wind/fx.gd"  # tale effects (TaleHandler): gusts, hat, coat, warm light, stream
# cast by kind (SpreadStage): walker = the template's road walker with a CastPuppet skin; hanger = SkyHanger in the sky
# band of the story shot (screen fractions, card height as a fraction of the frame, paper backing disc); prop = prints
# the handler makes cards of.
CAST = {"traveller": {"kind": "walker", "skin": "traveller", "height": 0.47,
                      "gait": {"front_gait": True, "step_period": 0.46, "min_stride": 0.05, "max_stride": 0.13,
                               "foot_lift": 0.03, "waddle_deg": 4.0}},
        "sun": {"kind": "hanger", "skin": "sun", "screen": [0.21, 0.26], "frac": 0.27, "sway": 0.025, "bob": 0.012,
                "seed": 0.2, "backing": ["fbf0cf", "e2b85c"], "backing_scale": 1.12, "backing_drop": 0.06},
        "wind": {"kind": "hanger", "skin": "wind", "screen": [0.79, 0.26], "frac": 0.2322, "sway": 0.04, "bob": 0.016,
                 "seed": 0.7, "backing": ["d9e7ef", "7f9fb8"], "backing_scale": 1.05, "backing_drop": 0.1},
        "hat": {"kind": "prop", "skin": "hat"}, "coat": {"kind": "prop", "skin": "coat"}}
MORAL = "세게 미는 것보다 다정한 게 더 힘이 세요."
SEG_KEEP = {}  # source line index -> seg indices kept (reused clips, nothing to record)

# ---------------------------------------------------------------- pop-up adaptations
# Source line index -> new seg texts (None = keep). Every change is marked "changed-needs-recording".
CHANGED = {
    13: ["바람을 꾹 누르고 있으면 후~ 불어요!"],   # tap -> press-and-hold to blow (pop-up hold interaction)
    14: ["바람을 꾹 눌러 봐요!"],
    15: ["더 세게, 꾹~!"],
}
NEW_LINES = {
    "sw_n01": [["nar", "그림책을 톡 눌러서 펼쳐 볼까요?", None, "[cheerful, inviting, warm]"]],
    "sw_n02": [["nar", "외투를 팔에 걸고, 나그네는 다시 즐겁게 길을 떠나요.", None, "[calm, gentle, storytelling]"]],
    "sw_n03": [["nar", "또 보고 싶으면 '다시 보기'를 톡!", None, "[cheerful, inviting]"]],
    # r2: the bet beat gets a light interaction (critic 3): tap the traveller, he shows off his thick coat (sw_009).
    "sw_n04": [["nar", "나그네를 톡 눌러 볼까요?", None, "[cheerful, inviting, curious]"]],
}
# Lines from the source app's mini-games that the pop-up book does not use (kept out of the beats).
# r2 pacing (critics: under ~3 min, say the moral once): sw_007 (folded into the two tap lines), sw_039 (the hint
# gave the quiz answer away), sw_061 (moral said a second time) and the extra "휴우~" line are left out too.
DROPPED = {7, 37, 38, 39, 42, 43, 44, 45, 46, 47, 48, 49, 50, 58, 59, 61}

# ---------------------------------------------------------------- beats -> spreads
# 2026-11-18: BEATS = the live beats of game/stories/sun_wind/script.json (hand-tuned after the first seed: walk_calm
# poses, toward-camera routes, stroll steps), so `seed_script.py --tale sun_wind --force` reproduces script.json exactly.
# Consecutive beats with the same spread share one page (no page turn).
# spread: MeadowWorld seed + view (camera preset and where the traveller stands on the road; views 5,0,1,2,4
# walk the road forward: 0.28, 0.36, 0.46, 0.555, 0.72).
# step kinds (game/story/story_runner.gd):
#   say {line}                   narration/dialogue, auto-advance after the clip, tap to skip
#   walk {dist, line?}           traveller walks dist units along the road (optionally while a line plays)
#   walk_to {place, line?}       walk to a place on the spread ("stream": the stream bank, off the road)
#   pose {pose}                  traveller pose (walk, walk_nohat, hold, shirt, fan, sit)
#   cam {shot}                   camera shot: wide (the template view) | story (cast framed) | close (punch-in)
#   tap {target, prompt, hint, react?, lines}  wait for a tap on sun|wind|traveller, react fx, then play lines
#   blow {prompt, hint, more, steps:[{need, fx, lines}]}  press/hold the wind: it blows at the traveller
#   shine {prompt, steps:[{fx, lines, next}]}  tap the sun again and again: it warms the traveller
#   snap {key}                   keep a picture of the page for the recap flashbacks
#   flash {key, side, line}      show a kept picture as a paper photo while a line plays
#   quiz {prompt, answer, wrong:{target: [lines]}, right}  two big picture cards; tap the winner
#   gentle {prompt, hint, taps, lines}         soft taps on the wind (cool breeze)
#   fx {fx}                      one-shot effect (hat_back, wind_tired, wind_calm, friends, ...)
#   end {line?, after}           ending card (sun + wind, "끝", "다시 보기")
BEATS = [{'id': 'cover', 'title': '해와 바람', 'spread': None, 'steps': [{'do': 'cover', 'prompt': 'sw_n01'}]},
 {'id': 'sky',
  'title': '하늘 높이',
  'enter': {'pose': 'walk_calm'},
  'spread': {'seed': 1, 'view': 5},
  'steps': [{'do': 'cam', 'shot': 'story'},
            {'do': 'say', 'line': 'sw_000'},
            {'do': 'tap',
             'target': 'sun',
             'prompt': 'sw_001',
             'hint': 'sw_002',
             'react': 'sun_proud',
             'lines': ['sw_003']},
            {'do': 'tap',
             'target': 'wind',
             'prompt': 'sw_004',
             'hint': 'sw_005',
             'react': 'wind_puff',
             'lines': ['sw_006']},
            {'do': 'walk', 'dist': 0.6, 'line': 'sw_008'},
            {'do': 'tap', 'target': 'traveller', 'prompt': 'sw_n04', 'react': 'show_coat', 'lines': ['sw_009']}]},
 {'id': 'bet',
  'title': '내기',
  'enter': {'pose': 'walk_calm'},
  'spread': {'seed': 1, 'view': 0, 'route': [2.8, -2.4]},
  'steps': [{'do': 'cam', 'shot': 'story'},
            {'do': 'stroll', 'speed': 0.13},
            {'do': 'fx', 'fx': 'wind_boast'},
            {'do': 'say', 'line': 'sw_010'},
            {'do': 'fx', 'fx': 'sun_proud'},
            {'do': 'say', 'line': 'sw_011'}]},
 {'id': 'wind_turn',
  'title': '바람 차례',
  'enter': {'pose': 'walk_calm'},
  'spread': {'seed': 1, 'view': 0, 'route': [2.8, -2.4]},
  'steps': [{'do': 'cam', 'shot': 'story'},
            {'do': 'stroll', 'speed': 0.1},
            {'do': 'fx', 'fx': 'wind_puff'},
            {'do': 'say', 'line': 'sw_012'},
            {'do': 'blow',
             'prompt': 'sw_013',
             'hint': 'sw_014',
             'more': 'sw_015',
             'steps': [{'need': 0.6, 'fx': 'leaves', 'lines': ['sw_016']},
                       {'need': 1.2, 'fx': 'hat_off', 'lines': ['sw_017']},
                       {'need': 1.8, 'fx': 'flap', 'lines': ['sw_018']},
                       {'need': 2.4, 'fx': 'clutch', 'lines': ['sw_019', 'sw_020']},
                       {'need': 3.0, 'fx': 'gale', 'lines': ['sw_021']}]},
            {'do': 'snap', 'key': 'cold'},
            {'do': 'fx', 'fx': 'wind_tired'},
            {'do': 'cam', 'shot': 'story'},
            {'do': 'say', 'line': 'sw_022'},
            {'do': 'say', 'line': 'sw_023'},
            {'do': 'fx', 'fx': 'hat_back'},
            {'do': 'say', 'line': 'sw_024'},
            {'do': 'stop'}]},
 {'id': 'sun_turn',
  'title': '해님 차례',
  'enter': {'pose': 'walk_calm'},
  'spread': {'seed': 1, 'view': 1, 'route': [1.6, -1.6]},
  'steps': [{'do': 'cam', 'shot': 'story'},
            {'do': 'stroll', 'speed': 0.13},
            {'do': 'fx', 'fx': 'wind_calm'},
            {'do': 'say', 'line': 'sw_025'},
            {'do': 'shine',
             'prompt': 'sw_026',
             'hint': 'sw_027',
             'steps': [{'fx': 'warm1', 'lines': ['sw_028'], 'next': 'sw_029'},
                       {'fx': 'warm2', 'lines': ['sw_030'], 'next': 'sw_031'},
                       {'fx': 'coat_off', 'lines': ['sw_032']}]},
            {'do': 'snap', 'key': 'warm'},
            {'do': 'fx', 'fx': 'walk_on'},
            {'do': 'fx', 'fx': 'sun_wins'},
            {'do': 'say', 'line': 'sw_033'},
            {'do': 'stop'}]},
 {'id': 'moral',
  'title': '누가 이겼을까?',
  'enter': {'pose': 'shirt'},
  'spread': {'seed': 1, 'view': 1, 'route': [1.6, -1.6]},
  'steps': [{'do': 'fx', 'fx': 'pick_coat'},
            {'do': 'flash', 'key': 'cold', 'side': 'left', 'line': 'sw_034'},
            {'do': 'flash', 'key': 'warm', 'side': 'right', 'line': 'sw_035'},
            {'do': 'quiz',
             'prompt': 'sw_036',
             'answer': 'sun',
             'wrong': {'wind': ['sw_x_wrong_cold']},
             'right': ['sw_040', 'sw_041']}]},
 {'id': 'stream',
  'title': '개울가',
  'enter': {'pose': 'shirt_calm'},
  'spread': {'seed': 1, 'view': 3, 'route': [0.5, -0.3]},
  'steps': [{'do': 'cam', 'shot': 'story'},
            {'do': 'walk_to', 'place': 'stream', 'line': 'sw_051'},
            {'do': 'pose', 'pose': 'relieved'},
            {'do': 'fx', 'fx': 'splash'},
            {'do': 'say', 'line': 'sw_052'},
            {'do': 'gentle', 'prompt': 'sw_053', 'hint': 'sw_054', 'taps': 3, 'lines': ['sw_055']},
            {'do': 'fx', 'fx': 'friends'},
            {'do': 'say', 'line': 'sw_056'},
            {'do': 'say', 'line': 'sw_057'}]},
 {'id': 'ending',
  'title': '끝',
  'enter': {'pose': 'shirt'},
  'spread': {'seed': 1, 'view': 4},
  'steps': [{'do': 'cam', 'shot': 'story'},
            {'do': 'fx', 'fx': 'carry_coat'},
            {'do': 'fx', 'fx': 'friends'},
            {'do': 'walk_away', 'dist': 3.2, 'line': 'sw_n02'},
            {'do': 'say', 'line': 'sw_060'},
            {'do': 'end', 'after': 'sw_n03'}]}]
