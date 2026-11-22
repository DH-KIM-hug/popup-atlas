#!/usr/bin/env python3
"""sunmoon set PROTOTYPE / look check (phase 1, 2026-11-22): writes game/stories/sunmoon/proto/script.json, still beats
on the real engine using the tale's own layouts (tools/story/tales/sunmoon.py SET_A / SET_B, korean theme): the
mountain road (late light, then night) and the cottage with its yard, well and tree (late light, then night), plus
the two camera tours. Capture:
  godot --path game --resolution 1366x1024 --fixed-fps 30 --write-movie /tmp/s.avi --quit-after 600 -- \\
        --tale=sunmoon/proto --autoplay --beat=road
"""
import json, os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tales.sunmoon as T

CAST = {r: {"kind": "actor", "skin": c["skin"]} for r, c in T.CAST.items() if c["kind"] == "actor"}
CAST["girl"] = {"kind": "actor", "skin": "hanbok_girl"}


def cams(*shots):
    return [{"do": "cam", "shot": s, "at": a, "rate": r, "wait": w} for s, a, r, w in shots]


BEATS = [
    {"id": "road", "title": "고갯길 (늦은 오후)", "spread": T._road(light="late"),
     "enter": {"who": {"mom": "tired_full", "tiger": "roar", "rich": "give_tray"},
               "at": {"mom": "mom_1", "tiger": "tiger_1", "rich": "rich_at"}},
     "steps": cams(("crane_high", "mid", 2.4, 3.0), ("establish", "rich_yard", 1.0, 3.0),
                   ("pass_track", "pass_1", 1.0, 3.0), ("pass_low", "tiger_1", 1.0, 3.0),
                   ("pass_two", "tiger_1", 1.0, 3.0))},
    {"id": "road_night", "title": "셋째 고개 (밤)", "spread": T._road(light="night", sky=T.SKY_NIGHT),
     "enter": {"who": {"mom": "scared_full", "tiger": "demand"}, "at": {"mom": "mom_3", "tiger": "tiger_3"}},
     "steps": cams(("pass3_track", "pass_3", 2.4, 3.0), ("pass_low", "tiger_3", 1.0, 3.0),
                   ("moon_cut", "pass_3", 1.0, 3.0))},
    {"id": "home", "title": "오막살이 (아침)", "spread": T._home(light=""),
     "enter": {"who": {"mom": "talk", "boy": "wave", "girl": "wave"},
               "at": {"mom": "mom_door", "boy": "boy_at", "girl": "girl_at"}},
     "steps": cams(("establish", "est", 2.4, 3.0), ("medium", "front_focus", 1.0, 3.0),
                   ("yard_high", "yard_focus", 1.0, 3.0), ("tree_low", "tree", 1.0, 3.0))},
    {"id": "home_night", "title": "오막살이 (밤)", "spread": T._home(light="night", sky=T.SKY_NIGHT),
     "enter": {"who": {"tiger": "dg_knock", "boy": "scared", "girl": "scared"},
               "at": {"tiger": "tiger_door", "boy": "in_boy", "girl": "in_girl"}},
     "steps": cams(("establish", "est", 2.4, 3.0), ("door_ots", "door", 1.0, 3.0), ("room", "in_focus", 1.0, 3.5), ("window_in", "window_inside", 1.0, 2.5),
                   ("yard_high", "yard_focus", 1.0, 3.0))},
    T.TOUR_ROAD, T.TOUR_HOME,
    # the ground test card (felt vs paper): the first pass under its own light and lens, the cast in place
    {"id": "groundtest", "title": "고갯길 (땅 시험)", "spread": T._road(light="late"),
     "enter": {"who": {"mom": "scared_full", "tiger": "demand"}, "at": {"mom": "mom_1", "tiger": "tiger_1"}},
     "steps": cams(("pass_track", "pass_1", 9.0, 5.0))},
]
out = {"tale_id": "sunmoon_proto", "title": "해님 달님 (prototype)", "backdrop": True, "theme": "korean",
       "ground_style": "paper",
       "pop_in": False, "inside_framing": "manual", "spacing": True, "overlap_check": True,
       "overlap_ok": T.EXTRA["overlap_ok"], "shots": T.SHOTS,
       "cast": CAST, "ui": {"speakers": {}}, "voices": {}, "beats": BEATS, "lines": []}
# 2026-11-22 paper test card: felt originals left of the road, the paper redraws right, on the pass-1 road
_tc = T._road_spot(-2.55)
_sp = dict(T.ROAD_A)
for _nm, (_dx, _dz) in {"tc": (0, 0), "tc_fr": (-0.95, -0.55), "tc_pr": (0.95, -0.55), "tc_fb": (-0.62, -0.1),
                        "tc_pb": (0.62, -0.1), "tc_fm": (-0.95, 0.05), "tc_pm": (0.95, 0.05), "tc_fmom": (-0.5, 0.35),
                        "tc_ftig": (-0.78, 0.25), "tc_fgirl": (-0.26, 0.42), "tc_pmom": (0.5, 0.35),
                        "tc_ptig": (0.78, 0.25), "tc_pgirl": (0.26, 0.42), "tc_chars": (0, 0.36)}.items():
    _sp[_nm] = [round(_tc[0] + _dx, 3), round(_tc[1] + _dz, 3)]
_tset = list(T.SET_A) + [
    {"card": "story_sm_mountain_01", "at": "tc_fr", "stage": "full", "name": "tc_fr", "scale": 0.36, "clear": 0.3},
    {"card": "story_sm_paper_test_00", "at": "tc_pr", "stage": "full", "name": "tc_pr", "scale": 0.36, "clear": 0.3},
    {"card": "story_sm_mountain_04", "at": "tc_fb", "stage": "full", "name": "tc_fb", "scale": 0.6, "clear": 0.2},
    {"card": "story_sm_paper_test_01", "at": "tc_pb", "stage": "full", "name": "tc_pb", "scale": 0.6, "clear": 0.2},
    {"card": "story_sm_mountain_07", "at": "tc_fm", "stage": "full", "name": "tc_fm", "scale": 1.0, "clear": 0.2},
    {"card": "story_sm_paper_test_02", "at": "tc_pm", "stage": "full", "name": "tc_pm", "scale": 1.0, "clear": 0.2}]
PAPER_TEST = {"id": "papertest", "title": "종이 시험 카드", "spread": T._road(light="late", spots=_sp, set=_tset,
                                                                       place="papertest"),
              "enter": {"who": {"mom": "calm", "tiger": "calm", "girl": "calm", "mom_p": "paper_calm",
                                "tiger_p": "paper_calm", "girl_p": "paper_calm"},
                        "at": {"mom": "tc_fmom", "tiger": "tc_ftig", "girl": "tc_fgirl", "mom_p": "tc_pmom",
                               "tiger_p": "tc_ptig", "girl_p": "tc_pgirl"}},
              "steps": cams(("tc_wide", "tc", 9.0, 4.0), ("tc_close", "tc_chars", 1.6, 4.0))}
SHOTS_TC = {"tc_wide": [4.4, 13.0, 0.32, 30.0, 0.0], "tc_close": [2.3, 6.0, 0.2, 30.0, 0.0]}
BEATS.append(PAPER_TEST)
CAST.update({"mom_p": {"kind": "actor", "skin": "hanbok_mom"}, "tiger_p": {"kind": "actor", "skin": "tiger"},
             "girl_p": {"kind": "actor", "skin": "hanbok_girl"}})
out["cast"] = CAST
out["shots"] = {**T.SHOTS, **SHOTS_TC}
for sub, style in (("proto", "paper"), ("proto_felt", "")):  # proto_felt: the same sets on the felt ground (test card)
    out["ground_style"] = style
    p = os.path.join(ROOT, "game", "stories", "sunmoon", sub, "script.json")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    json.dump(out, open(p, "w"), ensure_ascii=False, indent=1)
    print("wrote", p)
