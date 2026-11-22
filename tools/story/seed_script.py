#!/usr/bin/env python3
"""Seed game/stories/<tale>/script.json from 톡톡 동화극장's voice script (READ-ONLY source) and copy the
recorded clips that the pop-up version still uses into game/audio/voice/<tale>/.

  python3 tools/story/seed_script.py [--tale sun_wind]          # writes script.json only if it does not exist yet
  python3 tools/story/seed_script.py --tale three_pigs --force  # overwrite (loses hand edits to script.json!)
  python3 tools/story/seed_script.py --tale three_pigs --audio  # (re)copy clips only, from the existing script.json
  python3 tools/story/seed_script.py --tale sun_wind --out /tmp/x.json --no-audio   # write elsewhere (diff check)

Per-tale tables (TITLE, PREFIX, CAST, MORAL, CHANGED, NEW_LINES, DROPPED, SEG_KEEP, BEATS, optional LINE_META) live in
tools/story/tales/<tale>.py (default tale: sun_wind). SEG_KEEP {source index: [seg indices]} trims a line to some of its
segs (their clips are reused, nothing to record). LINE_META {line id: {...}} adds fields (expr hints) to a line entry.

How 톡톡 names clips: tools/elevenlabs/gen_tale.py writes tales/<id>/narration_el.js, which maps the FULL line
text (as written in voice_script_el.json "text") to one clip path, or to a list of clip paths, one per seg, in
seg order (audio/el/<tale>/<speaker>_<hash10>.mp3). "extra" lines are keyed by name in VOICE_LINES.
We parse that file instead of re-hashing, so the mapping is exactly what 톡톡 plays.

Line status: "reuse" when the seg text is unchanged (its clip is copied), "changed-needs-recording" when the
pop-up version changed or added it (no clip; record with the same voice id from `voices`), "changed-recorded" once
tools/story/record_lines.py has recorded it with that voice id (game/audio/voice/<tale>/recorded.json).
MP3 is copied as is (Godot 4 imports MP3 natively, so no .ogg conversion is needed); originals are untouched.
"""
import importlib, json, re, shutil, sys
from pathlib import Path

SRC = Path("/Users/house_of_4k2b/projects/2026/patjuk-game")
REPO = Path(__file__).resolve().parents[2]
GAME = REPO / "game"
sys.path.insert(0, str(Path(__file__).resolve().parent))


def _arg(name, default=None):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


T = importlib.import_module("tales." + _arg("--tale", "sun_wind"))
TALE = SRC / "tales" / T.TALE_ID
OUT = Path(_arg("--out")) if _arg("--out") else GAME / f"stories/{T.TALE_ID}/script.json"
AUDIO_DIR = GAME / f"audio/voice/{T.TALE_ID}"
RES_AUDIO = f"res://audio/voice/{T.TALE_ID}/"
BEATS, CHANGED, NEW_LINES, DROPPED = T.BEATS, T.CHANGED, T.NEW_LINES, T.DROPPED
SEG_KEEP = getattr(T, "SEG_KEEP", {})
LINE_META = getattr(T, "LINE_META", {})

# r2: recordings made by tools/story/record_lines.py for changed / new lines (same voice ids), keyed by
# "speaker|tags|text"; the seed fills them in so reseeding keeps them.
RECORDED = AUDIO_DIR / "recorded.json"


def clip_map(fname: str = "narration_el.js") -> tuple[dict, dict]:
    """narration_el.js (or read_narration_el.js) -> {full text: [clip, ...]}, {extra key: clip}."""
    js = (TALE / fname).read_text(encoding="utf-8")
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


def _ids_in(v) -> list:
    """Every string in a step (nested dicts / lists) that looks like a line id of this tale (PREFIX_...)."""
    if isinstance(v, str):
        return [v] if v.startswith(T.PREFIX + "_") else []
    if isinstance(v, dict):
        return [r for x in v.values() for r in _ids_in(x)]
    if isinstance(v, list):
        return [r for x in v for r in _ids_in(x)]
    return []


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
                if r and isinstance(r, str):
                    where.setdefault(r, (b["id"], kind))
            # 2026-11-19 (witch_candy): branch verbs keep line ids in nested tables (results {strawberry: {...}}),
            # so any string value that is a line id of this tale marks it used (the fixed keys above come first)
            for r in _ids_in(st):
                where.setdefault(r, (b["id"], kind))
    out_lines = []
    for i, l in enumerate(vs["lines"]):
        lid = f"{T.PREFIX}_{i:03d}"
        cl = clips.get(l["text"], [])
        segs = []
        new = CHANGED.get(i)
        for j, s in enumerate(l["segs"]):
            if i in SEG_KEEP and j not in SEG_KEEP[i]:
                continue
            sp, text, emo, tags = s
            if new is not None:
                segs.append(seg(sp, new[j] if j < len(new) else text, emo, tags, cl[j] if j < len(cl) else "",
                                "changed-needs-recording"))
            else:
                segs.append(seg(sp, text, emo, tags, cl[j] if j < len(cl) else "", "reuse" if j < len(cl) else "changed-needs-recording"))
        beat, inter = where.get(lid, ("", ""))
        out_lines.append(line_entry(lid, segs, beat, inter, i in DROPPED or lid not in where, source_index=i, source_text=l["text"]))
    for k, segs_src in vs.get("extra", {}).items():
        lid = f"{T.PREFIX}_x_{k}"
        cl = extra_clips.get(k, [])
        segs = [seg(s[0], s[1], s[2], s[3], cl[j] if j < len(cl) else "", "reuse" if j < len(cl) else "changed-needs-recording")
                for j, s in enumerate(segs_src)]
        beat, inter = where.get(lid, ("", ""))
        out_lines.append(line_entry(lid, segs, beat, inter, lid not in where, source_extra=k))
    # 2026-11-22 (sunmoon): 톡톡's READ-MODE script (read_script_el.json, the quiz-free storytelling version) is recorded
    # too (read_narration_el.js, same voices). A tale with READ_SCRIPT = True also seeds every read line as
    # <PREFIX>_r<scene 1-based:02d><line:02d> (clips from the read map, else the play map); READ_SEG_KEEP {lid: [seg
    # indices]} trims one to some of its segs (clips reused). Tales without READ_SCRIPT are unchanged.
    if getattr(T, "READ_SCRIPT", False):
        rs = json.loads((TALE / "read_script_el.json").read_text(encoding="utf-8"))
        rclips, _ = clip_map("read_narration_el.js")
        rkeep = getattr(T, "READ_SEG_KEEP", {})
        for si, sc in enumerate(rs["scenes"]):
            for li, l in enumerate(sc["lines"]):
                lid = f"{T.PREFIX}_r{si + 1:02d}{li:02d}"
                cl = rclips.get(l["text"]) or clips.get(l["text"], [])
                segs = []
                for j, sg in enumerate(l["segs"]):
                    if lid in rkeep and j not in rkeep[lid]:
                        continue
                    sp, text, emo, tags = (list(sg) + [None, None])[:4]
                    segs.append(seg(sp, text, emo, tags, cl[j] if j < len(cl) else "",
                                    "reuse" if j < len(cl) else "changed-needs-recording"))
                beat, inter = where.get(lid, ("", ""))
                e = line_entry(lid, segs, beat, inter, lid not in where, source_text=l["text"])
                e["source_read"] = f"{sc['key']}#{li}"
                e["source_text"] = l["text"]
                if lid in rkeep:
                    e["trimmed_segs"] = rkeep[lid]
                out_lines.append(e)
    for lid, segs_src in NEW_LINES.items():
        segs = [seg(s[0], s[1], s[2], s[3], "", "changed-needs-recording") for s in segs_src]
        beat, inter = where.get(lid, ("", ""))
        out_lines.append(line_entry(lid, segs, beat, inter, lid not in where, new=True))  # new lines too: used only if a beat plays them
    return {
        "tale_id": T.TALE_ID,
        "title": T.TITLE,
        "seeded_from": str(TALE / "voice_script_el.json"),
        "clip_map_from": str(TALE / "narration_el.js") + (" + read_narration_el.js" if getattr(T, "READ_SCRIPT", False) else ""),
        "voices": vs["voices"], "models": vs.get("models", {}), "settings": vs.get("settings", {}),
        "voice_notes": vs.get("notes", ""),
        **({"handler": T.HANDLER} if getattr(T, "HANDLER", "") else {}),
        **({"shots": T.SHOTS} if getattr(T, "SHOTS", None) else {}),
        **({"ui": T.UI} if getattr(T, "UI", None) else {}),
        **({"backdrop": True} if getattr(T, "BACKDROP", False) else {}),
        **({"inside_framing": T.INSIDE_FRAMING} if getattr(T, "INSIDE_FRAMING", "") else {}),
        **({"sound": T.SOUND} if getattr(T, "SOUND", None) else {}),
        **getattr(T, "EXTRA", {}),  # further tale-level fields (witch_candy: spacing, overlap_check, overlap_ok)
        "cast": T.CAST,
        "moral": T.MORAL,
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
    if source_index is not None and source_index in SEG_KEEP:
        e["trimmed_segs"] = SEG_KEEP[source_index]
    e.update(LINE_META.get(lid, {}))
    for si, (au, prov) in getattr(T, "TRIM_SEG", {}).get(lid, {}).items():  # one seg's clip trimmed (no recording)
        if si < len(e["segs"]):
            e["segs"][si] = {**e["segs"][si], "audio": au, "trimmed_from": prov, "status": "reuse"}
    tr = getattr(T, "TRIM", {}).get(lid)
    if tr:  # an existing clip trimmed at a sentence pause (no new recording): (text, audio, provenance)
        e["segs"] = [{**e["segs"][0], "text": tr[0], "audio": tr[1], "trimmed_from": tr[2], "status": "reuse"}]
        if len(tr) > 3:  # a premixed chorus clip replaces per-voice segs: one seg, its own speaker key (witch_candy)
            e["segs"][0]["speaker"] = tr[3]
            e["speaker"] = tr[3]
        e["text"] = tr[0]
        e["trimmed_clip"] = True
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
    if "--no-audio" in sys.argv:
        sys.exit(0)
    copied, missing = copy_audio(script)
    used = [l for l in script["lines"] if l["used"]]
    print(f"lines {len(script['lines'])} used {len(used)} reuse {sum(l['status'] == 'reuse' for l in used)} "
          f"changed {sum(l['status'] != 'reuse' for l in used)}; clips copied {len(copied)}; needs recording: {missing}")
