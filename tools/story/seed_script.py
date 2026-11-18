#!/usr/bin/env python3
"""Seed game/stories/sun_wind/script.json from 톡톡 동화극장's voice script (READ-ONLY source) and copy the
recorded clips that the pop-up version still uses into game/audio/voice/sun_wind/.

  python3 tools/story/seed_script.py            # writes script.json only if it does not exist yet
  python3 tools/story/seed_script.py --force    # overwrite (loses hand edits to script.json!)
  python3 tools/story/seed_script.py --audio    # (re)copy clips only, from the existing script.json

How 톡톡 names clips: tools/elevenlabs/gen_tale.py writes tales/<id>/narration_el.js, which maps the FULL line
text (as written in voice_script_el.json "text") to one clip path, or to a list of clip paths, one per seg, in
seg order (audio/el/<tale>/<speaker>_<hash10>.mp3). "extra" lines are keyed by name in VOICE_LINES.
We parse that file instead of re-hashing, so the mapping is exactly what 톡톡 plays.

Line status: "reuse" when the seg text is unchanged (its clip is copied), "changed-needs-recording" when the
pop-up version changed or added it (no clip; record with the same voice id from `voices`), "changed-recorded" once
tools/story/record_lines.py has recorded it with that voice id (game/audio/voice/sun_wind/recorded.json).
MP3 is copied as is (Godot 4 imports MP3 natively, so no .ogg conversion is needed); originals are untouched.
"""
import json, re, shutil, sys
from pathlib import Path

SRC = Path("/Users/house_of_4k2b/projects/2026/patjuk-game")
TALE = SRC / "tales/sun_wind"
REPO = Path(__file__).resolve().parents[2]
GAME = REPO / "game"
OUT = GAME / "stories/sun_wind/script.json"
AUDIO_DIR = GAME / "audio/voice/sun_wind"
RES_AUDIO = "res://audio/voice/sun_wind/"

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
BEATS = [
    {"id": "cover", "title": "해와 바람", "spread": None, "steps": [{"do": "cover", "prompt": "sw_n01"}]},
    {"id": "sky", "title": "하늘 높이", "enter": {"pose": "walk"}, "spread": {"seed": 1, "view": 5}, "steps": [
        {"do": "cam", "shot": "story"},
        {"do": "say", "line": "sw_000"},
        {"do": "tap", "target": "sun", "prompt": "sw_001", "hint": "sw_002", "react": "sun_proud", "lines": ["sw_003"]},
        {"do": "tap", "target": "wind", "prompt": "sw_004", "hint": "sw_005", "react": "wind_puff", "lines": ["sw_006"]},
        {"do": "walk", "dist": 0.4, "line": "sw_008"},
        {"do": "tap", "target": "traveller", "prompt": "sw_n04", "react": "show_coat", "lines": ["sw_009"]},
    ]},
    {"id": "bet", "title": "내기", "enter": {"pose": "walk"}, "spread": {"seed": 1, "view": 0}, "steps": [
        {"do": "cam", "shot": "story"},
        {"do": "fx", "fx": "wind_boast"},
        {"do": "say", "line": "sw_010"},
        {"do": "fx", "fx": "sun_proud"},
        {"do": "say", "line": "sw_011"},
    ]},
    {"id": "wind_turn", "title": "바람 차례", "enter": {"pose": "walk"}, "spread": {"seed": 1, "view": 0}, "steps": [
        {"do": "fx", "fx": "wind_puff"},
        {"do": "say", "line": "sw_012"},
        {"do": "blow", "prompt": "sw_013", "hint": "sw_014", "more": "sw_015", "steps": [
            {"need": 0.6, "fx": "leaves", "lines": ["sw_016"]},
            {"need": 1.2, "fx": "hat_off", "lines": ["sw_017"]},
            {"need": 1.8, "fx": "flap", "lines": ["sw_018"]},
            {"need": 2.4, "fx": "clutch", "lines": ["sw_019", "sw_020"]},
            {"need": 3.0, "fx": "gale", "lines": ["sw_021"]},
        ]},
        {"do": "snap", "key": "cold"},
        {"do": "fx", "fx": "wind_tired"},
        {"do": "cam", "shot": "story"},
        {"do": "say", "line": "sw_022"},
        {"do": "say", "line": "sw_023"},
        {"do": "fx", "fx": "hat_back"},
        {"do": "say", "line": "sw_024"},
    ]},
    {"id": "sun_turn", "title": "해님 차례", "enter": {"pose": "walk"}, "spread": {"seed": 1, "view": 1}, "steps": [
        {"do": "cam", "shot": "story"},
        {"do": "fx", "fx": "wind_calm"},
        {"do": "say", "line": "sw_025"},
        {"do": "shine", "prompt": "sw_026", "hint": "sw_027", "steps": [
            {"fx": "warm1", "lines": ["sw_028"], "next": "sw_029"},
            {"fx": "warm2", "lines": ["sw_030"], "next": "sw_031"},
            {"fx": "coat_off", "lines": ["sw_032"]},
        ]},
        {"do": "snap", "key": "warm"},
        {"do": "fx", "fx": "sun_wins"},
        {"do": "say", "line": "sw_033"},
    ]},
    # r2: the recap + quiz follow the coat coming off on the same page (critic 2), as two paper photos (cold, warm)
    # and two big picture cards to choose from (critics 1-3).
    {"id": "moral", "title": "누가 이겼을까?", "enter": {"pose": "shirt"}, "spread": {"seed": 1, "view": 1}, "steps": [
        {"do": "fx", "fx": "pick_coat"},
        {"do": "flash", "key": "cold", "side": "left", "line": "sw_034"},
        {"do": "flash", "key": "warm", "side": "right", "line": "sw_035"},
        {"do": "quiz", "prompt": "sw_036", "answer": "sun", "wrong": {"wind": ["sw_x_wrong_cold"]},
         "right": ["sw_040", "sw_041"]},
    ]},
    {"id": "stream", "title": "개울가", "enter": {"pose": "shirt"}, "spread": {"seed": 1, "view": 2}, "steps": [
        {"do": "cam", "shot": "story"},
        {"do": "walk_to", "place": "stream", "line": "sw_051"},
        {"do": "pose", "pose": "sit"},
        {"do": "fx", "fx": "splash"},
        {"do": "say", "line": "sw_052"},
        {"do": "gentle", "prompt": "sw_053", "hint": "sw_054", "taps": 3, "lines": ["sw_055"]},
        {"do": "fx", "fx": "friends"},
        {"do": "say", "line": "sw_056"},
        {"do": "say", "line": "sw_057"},
    ]},
    {"id": "ending", "title": "끝", "enter": {"pose": "shirt"}, "spread": {"seed": 1, "view": 4}, "steps": [
        {"do": "cam", "shot": "story"},
        {"do": "fx", "fx": "carry_coat"},
        {"do": "fx", "fx": "friends"},
        {"do": "walk_away", "dist": 1.6, "line": "sw_n02"},
        {"do": "say", "line": "sw_060"},
        {"do": "end", "after": "sw_n03"},
    ]},
]

# r2: recordings made by tools/story/record_lines.py for changed / new lines (same voice ids), keyed by
# "speaker|tags|text"; the seed fills them in so reseeding keeps them.
RECORDED = GAME / "audio/voice/sun_wind/recorded.json"


def clip_map() -> tuple[dict, dict]:
    """narration_el.js -> {full text: [clip, ...]}, {extra key: clip}."""
    js = (TALE / "narration_el.js").read_text(encoding="utf-8")
    blocks = re.findall(r"Object\.assign\((NARRATION_CLIPS|VOICE_LINES),\s*(\{.*?\})\);", js, re.S)
    lines, extra = {}, {}
    for name, body in blocks:
        d = json.loads(body)
        for k, v in d.items():
            (lines if name == "NARRATION_CLIPS" else extra)[k] = v if isinstance(v, list) else [v]
    return lines, extra


def _recorded() -> dict:
    return json.loads(RECORDED.read_text(encoding="utf-8")) if RECORDED.exists() else {}


def seg(sp, text, emo, tags, src_clip, status):
    rec = _recorded().get(f"{sp}|{tags or ''}|{text}")
    if status != "reuse" and rec:
        return {"speaker": sp, "text": text, "emotion": emo, "tags": tags, "audio": RES_AUDIO + rec,
                "source_audio": "", "status": "changed-recorded"}
    return {"speaker": sp, "text": text, "emotion": emo, "tags": tags,
            "audio": (RES_AUDIO + Path(src_clip).name) if (src_clip and status == "reuse") else "",
            "source_audio": src_clip or "", "status": status}


def build() -> dict:
    vs = json.loads((TALE / "voice_script_el.json").read_text(encoding="utf-8"))
    clips, extra_clips = clip_map()
    where = {}  # line id -> (beat, interaction)
    for b in BEATS:
        for st in b["steps"]:
            kind = st["do"]
            refs = [st.get(k) for k in ("line", "prompt", "hint", "more", "after")]
            if kind == "flash":
                kind = "flashback"
            refs += st.get("lines", []) + st.get("right", [])
            for s in st.get("steps", []):
                refs += s.get("lines", []) + [s.get("next")]
            for ls in st.get("wrong", {}).values():
                refs += ls
            for r in refs:
                if r:
                    where.setdefault(r, (b["id"], kind))
    out_lines = []
    for i, l in enumerate(vs["lines"]):
        lid = f"sw_{i:03d}"
        cl = clips.get(l["text"], [])
        segs = []
        new = CHANGED.get(i)
        for j, s in enumerate(l["segs"]):
            sp, text, emo, tags = s
            if new is not None:
                segs.append(seg(sp, new[j] if j < len(new) else text, emo, tags, cl[j] if j < len(cl) else "",
                                "changed-needs-recording"))
            else:
                segs.append(seg(sp, text, emo, tags, cl[j] if j < len(cl) else "", "reuse" if j < len(cl) else "changed-needs-recording"))
        beat, inter = where.get(lid, ("", ""))
        out_lines.append(line_entry(lid, segs, beat, inter, i in DROPPED or lid not in where, source_index=i, source_text=l["text"]))
    for k, segs_src in vs.get("extra", {}).items():
        lid = f"sw_x_{k}"
        cl = extra_clips.get(k, [])
        segs = [seg(s[0], s[1], s[2], s[3], cl[j] if j < len(cl) else "", "reuse" if j < len(cl) else "changed-needs-recording")
                for j, s in enumerate(segs_src)]
        beat, inter = where.get(lid, ("", ""))
        out_lines.append(line_entry(lid, segs, beat, inter, lid not in where, source_extra=k))
    for lid, segs_src in NEW_LINES.items():
        segs = [seg(s[0], s[1], s[2], s[3], "", "changed-needs-recording") for s in segs_src]
        beat, inter = where.get(lid, ("", ""))
        out_lines.append(line_entry(lid, segs, beat, inter, False, new=True))
    return {
        "tale_id": "sun_wind",
        "title": "해와 바람",
        "seeded_from": str(TALE / "voice_script_el.json"),
        "clip_map_from": str(TALE / "narration_el.js"),
        "voices": vs["voices"], "models": vs.get("models", {}), "settings": vs.get("settings", {}),
        "voice_notes": vs.get("notes", ""),
        "cast": {"traveller": {"skin": "traveller"}, "sun": {"skin": "sun"}, "wind": {"skin": "wind"},
                 "hat": {"skin": "hat"}, "coat": {"skin": "coat"}},
        "moral": "세게 미는 것보다 다정한 게 더 힘이 세요.",
        "beats": BEATS,
        "lines": out_lines,
    }


def line_entry(lid, segs, beat, inter, unused, source_index=None, source_text=None, source_extra=None, new=False):
    sps = sorted({s["speaker"] for s in segs})
    sts = {s["status"] for s in segs}
    st = "reuse" if sts == {"reuse"} else ("changed-needs-recording" if "changed-needs-recording" in sts else "changed-recorded")
    e = {"id": lid, "speaker": sps[0] if len(sps) == 1 else "+".join(s["speaker"] for s in segs),
         "text": " ".join(('"%s"' % s["text"]) if s["speaker"] != "nar" else s["text"] for s in segs),
         "status": st, "beat": beat, "interaction": inter, "used": not unused, "segs": segs}
    if source_index is not None:
        e["source_index"] = source_index
        e["source_text"] = source_text
    if source_extra:
        e["source_extra"] = source_extra
    if new:
        e["new"] = True
    return e


def copy_audio(script: dict) -> list:
    AUDIO_DIR.mkdir(parents=True, exist_ok=True)
    copied, missing = [], []
    for l in script["lines"]:
        if not l["used"]:
            continue
        for s in l["segs"]:
            if s["status"] == "changed-recorded":
                continue
            if s["status"] != "reuse":
                missing.append(l["id"])
                continue
            src = SRC / s["source_audio"]
            dst = AUDIO_DIR / Path(s["source_audio"]).name
            if not src.exists():
                missing.append(l["id"])
                continue
            if not dst.exists() or dst.stat().st_size != src.stat().st_size:
                shutil.copy2(src, dst)
            copied.append(dst.name)
    return sorted(set(copied)), sorted(set(missing))


if __name__ == "__main__":
    force = "--force" in sys.argv
    if "--audio" in sys.argv and OUT.exists():
        script = json.loads(OUT.read_text(encoding="utf-8"))
    elif OUT.exists() and not force:
        print("script.json exists (hand-editable); use --force to reseed or --audio to recopy clips")
        script = json.loads(OUT.read_text(encoding="utf-8"))
    else:
        script = build()
        OUT.parent.mkdir(parents=True, exist_ok=True)
        OUT.write_text(json.dumps(script, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print("wrote", OUT)
    copied, missing = copy_audio(script)
    used = [l for l in script["lines"] if l["used"]]
    print(f"lines {len(script['lines'])} used {len(used)} reuse {sum(l['status'] == 'reuse' for l in used)} "
          f"changed {sum(l['status'] != 'reuse' for l in used)}; clips copied {len(copied)}; needs recording: {missing}")
