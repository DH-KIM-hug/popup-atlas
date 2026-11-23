#!/usr/bin/env python3
"""THE GATE: a tale is not shown to the user until this prints GATE PASS for its latest full recording.

  python3 tools/story/gate.py <tale> <run.log> <full.mp4> [--no-tiles] [--offset S]

The run must be a full `--autoplay --quit-on-done --log-sound --log-track` recording (1200x900, with_godot.sh).
It checks, and FAILS on any of:
  1. check_lines.py: every used line / segment played exactly once, in order;
  2. run-log counters: STORY_DONE present, VOICE_DUP, CAM_JUMP, CAM_JERK, SPEAKER_OFF, OVERLAP_COUNT, OCCLUDE_COUNT,
     BLACK_LIPS (if printed), every SET_CHECK road=0 water=0, missing_audio=[], missing_sound=[], no SCRIPT ERROR /
     "Failed loading" lines;
  3. motion_review.py: MOTION_FLAGS=0, and artifacts/<tale>/motion/motion_review.md has a verdict (`ok`, with a note
     for any flagged row) in EVERY row - the reviewing agent must open every tile sheet; a `fix` verdict fails;
  4. artifacts/<tale>/gate.md: every box of the fixed visual checklist ticked ([x]) for THIS run (the file is
     written fresh, unticked, whenever the run log changes; the old one is kept as gate_<time>.md). Look at the
     contact sheets it points to (and the tiles / full-res crops) before ticking.
An item that is deliberately not 0 (an intended contact, a flagged hop that is a real jump) passes only with a line
under "## Accepted exceptions" in gate.md: `- <id>: <reason>` with the id gate.py printed (e.g. `- MOTION_FLAG 03:
the cat's roof hop is a jump, static card ok`, `- SET_CHECK lantern: ...`, `- OVERLAP_COUNT: ...`).
Exit 0 = GATE PASS, 1 = GATE FAIL.
"""
import argparse, hashlib, re, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PY = sys.executable

CHECKLIST = [
    ("rim", 'No white / cream die-cut rim on any puppet: cut edges in the figure\'s own darker colour, line art only '
            '(user: "흰색 테두리가 별로"). Full-res crops of every character.'),
    ("steam", 'Steam / smoke / puffs only where something is hot, rising from its mouth: no template chimney smoke over '
              'cleared houses, no breath clouds baked into figures, no sparkle bursts that read as steam (user: '
              '"이상한데서 김이 모락모락", "셋째집 연기뭐지?").'),
    ("holes", 'Holes read as what the story says: a planting hole is a dark dip laid flat in the furrow with a low heap '
              'beside it, a burrow / mouse hole is a low bank at an edge, never a mound with an arch for a planting hole '
              '(user: "구멍을 그렇게 파니...?").'),
    ("houses", 'No flat-card houses: every house / barn / shop / cottage is a closed solid volume that fits tightly '
               '(sides, roof, back, no slit, no background through it) from every story camera (user: "집들은 무조건 '
               '입체적으로 아주 잘 들어맞게"); house_orbit_all.sh red = 0 for closed houses.'),
    ("empty", 'No empty shots: the acting / speaking characters are in every frame of their beat; no shot of bare '
              'scenery while a line about someone plays, nobody leaves mid-line (12 frames per beat).'),
    ("place", 'The place named in the story reads on screen: every place a line names (텃밭, 부엌, 헛간 지붕, 쥐구멍...) '
              'shows what makes it that place in one wide and one close frame (user: "순무는 텃밭이 없네용?").'),
    ("felt", 'Paper, not felt: ground, set cards and characters are matte cut paper, no wool fuzz or stitch lines '
             '(user: "펠트 질감 싫은뎅").'),
]


def run_id(log: Path) -> str:
    return f"{log.name} {hashlib.sha1(log.read_bytes()).hexdigest()[:10]}"


def contact_sheets(tale, mp4, out):
    """Whole run every 2.5 s, 6 x 5 frames per sheet with the video time (for the visual checklist)."""
    from PIL import Image, ImageDraw
    for p in sorted(out.glob("gate_contact_*.jpg")):
        p.unlink()
    w, h = 400, 300
    raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", str(mp4), "-vf", f"fps=0.4,scale={w}:{h}", "-f", "rawvideo",
                          "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    n = len(raw) // (w * h * 3)
    got = []
    for s0 in range(0, n, 30):
        sheet = Image.new("RGB", (6 * w, 5 * h), (20, 20, 20))
        dr = ImageDraw.Draw(sheet)
        for i in range(s0, min(n, s0 + 30)):
            im = Image.frombuffer("RGB", (w, h), raw[i * w * h * 3:(i + 1) * w * h * 3])
            x, y = ((i - s0) % 6) * w, ((i - s0) // 6) * h
            sheet.paste(im, (x, y))
            t = i * 2.5
            dr.rectangle((x, y, x + 50, y + 14), fill=(0, 0, 0))
            dr.text((x + 3, y + 2), f"{int(t // 60)}:{t % 60:04.1f}", fill=(255, 255, 120))
        p = out / f"gate_contact_{s0 // 30 + 1:02d}.jpg"
        sheet.save(p, quality=82)
        got.append(p)
    return got


def gate_file(tale, log, mp4, out, rid):
    p = out / "gate.md"
    if p.exists() and f"run: {rid}" in p.read_text():
        return p, False
    if p.exists():
        p.rename(out / f"gate_{time.strftime('%Y%m%d_%H%M%S')}.md")
    sheets = contact_sheets(tale, mp4, out)
    body = [f"# Gate: {tale}", "", f"run: {rid}", f"video: {mp4}", "",
            "Contact sheets (every 2.5 s): " + ", ".join(s.name for s in sheets), "",
            "Tick each box ([x]) only after looking at this run's frames (contact sheets, 12 frames per beat, full-res",
            "crops of every character and set piece). Untick-able? Fix the tale, re-record, run the gate again.", "",
            "## Visual checklist", ""]
    body += [f"- [ ] {key}: {txt}" for key, txt in CHECKLIST]
    body += ["", "## Accepted exceptions", "", "<!-- - <id gate.py printed>: <reason> -->", ""]
    p.write_text("\n".join(body))
    return p, True


def accepted(gtext):
    out = {}
    sec = gtext.split("## Accepted exceptions", 1)
    if len(sec) < 2:
        return out
    for ln in sec[1].splitlines():
        m = re.match(r"^\s*-\s*([A-Z_]+(?: [\w.:-]+)?)\s*:\s*(.{10,})$", ln)
        if m:
            out[m.group(1).strip()] = m.group(2).strip()
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tale")
    ap.add_argument("log")
    ap.add_argument("mp4")
    ap.add_argument("--no-tiles", action="store_true", help="reuse the tile sheets already written for this run")
    ap.add_argument("--offset", type=float, default=None)
    ap.add_argument("--ref-log", default=None, help="motion only: the log recorded with the mp4 when <run.log> is a "
                    "movie-less re-run of the same build (see motion_review.py)")
    a = ap.parse_args()
    log, mp4 = Path(a.log).resolve(), Path(a.mp4).resolve()
    # counters always come from the log recorded WITH the mp4 (a movie-less re-run plays voices in real time against
    # a fixed-fps clock and reports false VOICE_DUP / overlaps); <run.log> then only feeds the motion review
    clog = Path(a.ref_log).resolve() if a.ref_log else log
    text = clog.read_text(errors="replace")
    out = ROOT / "artifacts" / a.tale
    out.mkdir(parents=True, exist_ok=True)
    rid = run_id(log)
    fails = []  # (id, message)

    # 1. lines
    r = subprocess.run([PY, str(ROOT / "tools/story/check_lines.py"), a.tale, str(clog)], capture_output=True, text=True)
    print((r.stdout + r.stderr).strip().splitlines()[-1] if (r.stdout + r.stderr).strip() else "check_lines: no output")
    if r.returncode != 0:
        fails.append(("CHECK_LINES", "check_lines.py failed (see above)"))

    # 2. counters
    def counter(pat, name):
        m = re.findall(pat, text)
        if not m:
            fails.append((name, f"{name} not printed (incomplete run?)"))
            return None
        v = int(m[-1])
        if v != 0:
            fails.append((name, f"{name}={v}"))
        return v

    if "STORY_DONE" not in text:
        fails.append(("STORY_DONE", "no STORY_DONE: the run did not reach the end"))
    vals = {
        "VOICE_DUP": counter(r"VOICE_DUP=(\d+)", "VOICE_DUP"),
        "CAM_JUMP": counter(r"CAM_JUMP=(\d+)", "CAM_JUMP"),
        "CAM_JERK": counter(r"CAM_JERK=(\d+)", "CAM_JERK"),
        "SPEAKER_OFF": counter(r"SPEAKER_OFF=(\d+)", "SPEAKER_OFF"),
        "OVERLAP_COUNT": counter(r"OVERLAP_COUNT (\d+)", "OVERLAP_COUNT"),
        "OCCLUDE_COUNT": counter(r"OCCLUDE_COUNT (\d+)", "OCCLUDE_COUNT"),
    }
    if "BLACK_LIPS" in text:
        vals["BLACK_LIPS"] = counter(r"BLACK_LIPS frames-with-wrong-variant=(\d+)", "BLACK_LIPS")
    sc_bad = {}
    for m in re.finditer(r"^SET_CHECK (\S+) road=(\d+) water=(\d+)", text, re.M):
        if int(m.group(2)) or int(m.group(3)):
            sc_bad[m.group(1)] = f"road={m.group(2)} water={m.group(3)}"
    for k, v in sc_bad.items():
        fails.append((f"SET_CHECK {k}", f"SET_CHECK {k} {v}"))
    vals["SET_CHECK"] = len(sc_bad)
    for key in ("missing_audio", "missing_sound"):
        m = re.findall(key + r"=(\[[^\]]*\])", text)
        if not m:
            fails.append((key, f"{key} not printed"))
        elif m[-1].strip() != "[]":
            fails.append((key, f"{key}={m[-1]}"))
    for pat, name in ((r"SCRIPT ERROR", "SCRIPT_ERROR"), (r"Failed loading", "FAILED_LOADING")):
        n = len(re.findall(pat, text))
        if n:
            fails.append((name, f"{n} '{pat}' lines in the log"))

    # 3. motion
    cmd = [PY, str(ROOT / "tools/story/motion_review.py"), a.tale, str(log), str(mp4)]
    if a.no_tiles:
        cmd.append("--no-tiles")
    if a.offset is not None:
        cmd += ["--offset", str(a.offset)]
    if a.ref_log:
        cmd += ["--ref-log", str(Path(a.ref_log).resolve())]
    r = subprocess.run(cmd, capture_output=True, text=True)
    mo = r.stdout
    for ln in mo.splitlines():
        if ln.startswith(("MOTION_FLAG ", "MOTION_NOLOG", "MOTION_NOTE", "MOTION_FLAGS", "MOTION_SEGMENTS", "MOTION_OFFSET")):
            print(ln)
    if r.returncode != 0:
        nolog = [ln for ln in mo.splitlines() if ln.startswith("MOTION_NOLOG")]
        fails.append(("MOTION_NOLOG", nolog[0]) if nolog else
                     ("MOTION_REVIEW", "motion_review.py failed: " + (r.stderr.strip().splitlines() or ["?"])[-1]))
    flagged = {}
    for ln in mo.splitlines():
        m = re.match(r"MOTION_FLAG (\d+) (\S+) (.*)", ln)
        if m:
            flagged.setdefault(m.group(1), []).append(m.group(2))
    for nn, kinds in flagged.items():
        fails.append((f"MOTION_FLAG {nn}", f"segment {nn}: {', '.join(kinds)}"))
    md = out / "motion" / "motion_review.md"
    if md.exists() and r.returncode == 0:
        empty, fix = [], []
        for ln in md.read_text().splitlines():
            if re.match(r"^\|\s*\d+\s*\|", ln):
                c = [x.strip() for x in ln.strip().strip("|").split("|")]
                v = c[8].lower() if len(c) > 8 else ""
                note = c[9] if len(c) > 9 else ""
                if v not in ("ok", "fix"):
                    empty.append(c[0])
                elif v == "fix":
                    fix.append(c[0])
                elif c[6] != "-" and len(note) < 4:
                    empty.append(c[0] + "(flagged: note needed)")
        if empty:
            fails.append(("MOTION_VERDICT", f"{len(empty)} segment(s) without a verdict: {' '.join(empty[:20])}"
                          + (" ..." if len(empty) > 20 else "") + f"  -> open the tiles, fill {md}"))
        for nn in fix:
            fails.append((f"MOTION_FIX {nn}", f"segment {nn} marked fix"))

    # 4. visual checklist
    gp, fresh = gate_file(a.tale, log, mp4, out, rid)
    gtext = gp.read_text()
    unticked = re.findall(r"^- \[ \] (\w+):", gtext, re.M)
    if fresh:
        print(f"GATE_FILE {gp} written for this run (unticked)")
    if unticked:
        fails.append(("VISUAL_CHECKLIST", f"unticked in {gp}: {', '.join(unticked)}"))

    acc = accepted(gtext)
    real = []
    for fid, msg in fails:
        if fid in acc and fid not in ("VISUAL_CHECKLIST", "MOTION_VERDICT", "CHECK_LINES", "STORY_DONE", "MOTION_NOLOG"):
            print(f"GATE_ACCEPTED {fid}: {msg}  ({acc[fid]})")
        else:
            real.append((fid, msg))
    print("GATE_COUNTERS " + " ".join(f"{k}={v}" for k, v in vals.items()))
    for fid, msg in real:
        print(f"GATE_FAIL {fid}: {msg}")
    if real:
        print(f"GATE FAIL ({len(real)}) - do not show {a.tale} to the user yet")
        sys.exit(1)
    print(f"GATE PASS {a.tale} ({rid})")


if __name__ == "__main__":
    main()
