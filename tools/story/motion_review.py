#!/usr/bin/env python3
"""Motion review sheets + automatic motion flags for one recorded run (part of the GATE, tools/story/gate.py).

  python3 tools/story/motion_review.py <tale> <run.log> <full.mp4> [--offset S] [--no-tiles]

Reads the `MOVE` lines StoryActor prints for every travel segment (walk / run / climb / fly; game/story/story_actor.gd
`_move_log`), plus `TRACK` lines when the run had `--log-track`, and the shared cast catalog
(game/art/cast/catalog.json, read-only) for which drawn cycles each skin has. Writes, per segment, an 8 fps tile sheet
cropped and zoomed around the mover into artifacts/<tale>/motion/<NN>_<actor>_<t>.jpg (longer than 6 s: _p2, _p3 ...)
and artifacts/<tale>/motion/motion_review.md with one row per segment and an EMPTY verdict cell: the reviewing agent
opens every tile and writes `ok` or `fix` plus a note (gate.py fails until every row has one).

Automatic flags (printed as `MOTION_FLAG <NN> <kind> <actor> t=<t0> ...`, then `MOTION_FLAGS=<n>`):
  STATIC_CARD      a walk / run / climb shows a figure with no drawn cycle (a static card hopping or sliding: the
                   "sticker" run, user: "돼지 옆으로 달려가는 모습 이상해유")
  CYCLE_MISSING    the catalog has no drawn cycle for a view the segment travels in (front / back / side)
  RUN_NO_RUN_CYCLE a run shows a walk cycle because the catalog has no run cycle for that view
  RUN_WALK_CYCLE   a run shows a walk cycle although a run cycle exists for the view (walk `pose` not "run"?)
  SKATE            drawn-cycle phase advanced vs ground distance (one cycle per 0.9 height) off by > 40 %
  GLIDE            a handler slid a figure with no cycle along the ground (> 1 height, little height change)
  SPEED_JUMP       the speed changed by more than ~2.5 heights / s within one frame (a pop start / stop)
  OFF_FRAME        the mover is off the frame (less than half its figure inside, or not drawn by the camera) or under
                   the caption strip (more than half its head-and-body box behind the shown caption) for more than
                   30 % of the segment (wave 1; gate audit v1: "the camera loses the traveller" in 5 of 7 tales).
                   From TRACK (8 Hz, the camera that renders) or MOVE trk (4 Hz); CAPTION 1|0 lines say when the caption
                   shows (older logs: the caption counts as always shown)
The offset between the story clock and the video is the video length minus the last logged t (fixed 30 fps runs);
pass --offset to override. A log without MOVE (and TRACK) lines cannot be reviewed: MOTION_NOLOG, exit 2.
"""
import argparse, json, re, subprocess, sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FPS = 8
COLS = 8
MAX_TILES = 48  # 6 s per sheet
TILE_H = 240


def log_hash(log: Path) -> str:
    import hashlib
    b = log.read_bytes()
    return hashlib.sha1(b).hexdigest()[:10]


def kv(tok):
    out = {}
    for t in tok:
        if "=" in t:
            k, v = t.split("=", 1)
            out[k] = v
    return out


def parse_moves(text):
    segs = []
    for ln in text.splitlines():
        if not ln.startswith("MOVE "):
            continue
        p = ln.split()
        if len(p) < 7:
            continue
        d = kv(p[7:])
        s = {"t0": float(p[1]), "t1": float(p[2]), "role": p[3], "verb": p[4], "cycle": p[5], "dist": float(p[6]),
             "skin": d.get("skin", ""), "hgt": float(d.get("hgt", 0.3)), "cyc": float(d.get("cyc", 0)),
             "exp": float(d.get("exp", 0)), "vmax": float(d.get("vmax", 0)), "dvmax": float(d.get("dvmax", 0)),
             "dg": float(d.get("dg", -1)), "dz": float(d.get("dz", -1)),
             "figs": [], "views": {}, "box": None, "trk": []}
        for f in filter(None, d.get("figs", "").split(",")):
            a = f.split(":")
            if len(a) == 3:
                s["figs"].append((a[0], a[1], int(a[2])))
        for v in filter(None, d.get("views", "").split(",")):
            a = v.split(":")
            if len(a) == 2:
                s["views"][a[0]] = int(a[1])
        if d.get("box"):
            s["box"] = [float(x) for x in d["box"].split(",")]
        for k in filter(None, d.get("trk", "").split(";")):
            a = [float(x) for x in k.split(",")]
            if len(a) == 4:
                s["trk"].append(a)
        segs.append(s)
    return segs


def parse_track(text):
    """TRACK <role> t= x= y= h= (viewport px) -> {role: [(t, x, y, h)]}"""
    tr = defaultdict(list)
    for ln in text.splitlines():
        if ln.startswith("TRACK "):
            p = ln.split()
            d = kv(p[2:])
            try:
                tr[p[1]].append((float(d["t"]), float(d["x"]), float(d["y"]), float(d["h"]), d.get("fig", ""),
                                 d.get("view", ""), d.get("moving", "1") == "1"))
            except (KeyError, ValueError):
                pass
    return tr


def segs_from_track(tr):
    """Fallback when a run has TRACK but no MOVE lines: runs of moving=1 samples per role (no cycle data)."""
    segs = []
    for role, pts in tr.items():
        cur = []
        for q in pts + [None]:
            if q is not None and q[6] and (not cur or q[0] - cur[-1][0] < 0.5):
                cur.append(q)
                continue
            if len(cur) >= 4:
                figs = defaultdict(int)
                for c in cur:
                    figs[(c[4], c[5])] += 1
                segs.append({"t0": cur[0][0], "t1": cur[-1][0], "role": role, "verb": "walk", "cycle": "?",
                             "dist": 0.0, "skin": "", "hgt": 0.3, "cyc": 0, "exp": 0, "vmax": 0, "dvmax": 0,
                             "figs": [(f, v, n) for (f, v), n in figs.items()], "views": {}, "box": None, "trk": [],
                             "track_only": True})
            cur = [q] if (q is not None and q[6]) else []
    return sorted(segs, key=lambda s: s["t0"])


def catalog_cycles():
    d = json.loads((ROOT / "game/art/cast/catalog.json").read_text())
    arr = d if isinstance(d, list) else d.get("cards", [])
    cyc = defaultdict(dict)  # skin -> {cycle: view}
    for e in arr:
        if "cycle" in e:
            cyc[e.get("skin", "")][e["cycle"]] = e.get("view", "side")
    return cyc


CAPTION_RECT = (0.12, 0.834, 0.88, 0.975)  # story_ui.gd caption strip (anchors 0.12-0.88, 170-26 px above the bottom)
OFF_FRAC = 0.30


def parse_captions(text):
    """[(t0, t1)] while the caption strip shows; None when the log has no CAPTION lines."""
    ev = [(float(m.group(2)), m.group(1) == "1") for m in re.finditer(r"^CAPTION ([01]) t=(\d+(?:\.\d+)?)", text, re.M)]
    if not ev:
        return None
    out, t0 = [], None
    for t, on in ev:
        if on and t0 is None:
            t0 = t
        elif not on and t0 is not None:
            out.append((t0, t))
            t0 = None
    if t0 is not None:
        out.append((t0, 1e9))
    return out


def frame_samples(s, tr, vp):
    """(t, x, y, h) in viewport fractions: TRACK if logged (finer, the rendering camera), else MOVE trk."""
    tt = [q for q in tr.get(s["role"], []) if s["t0"] <= q[0] <= s["t1"]]
    if len(tt) >= 2:
        return [(q[0], q[1] / vp[0], q[2] / vp[1], q[3] / vp[1]) for q in tt], 8.0
    return [(q[0], q[1], q[2], q[3]) for q in s["trk"] if s["t0"] <= q[0] <= s["t1"]], 4.0


def off_frame(s, tr, vp, caps):
    """("OFF_FRAME", why) when the mover is off the frame or under the caption for > 30 % of the segment."""
    dur = s["t1"] - s["t0"]
    if dur < 0.6 or s.get("track_only"):
        return None
    pts, hz = frame_samples(s, tr, vp)
    want = max(1, int(dur * hz))
    off = under = 0
    for t, x, y, h in pts:
        w = 0.45 * h  # a figure is about half as wide as tall
        x0, x1, y0, y1 = x - w / 2, x + w / 2, y - h, y
        area = max((x1 - x0) * (y1 - y0), 1e-6)
        ix = max(0.0, min(x1, 1.0) - max(x0, 0.0)) * max(0.0, min(y1, 1.0) - max(y0, 0.0))
        if ix / area < 0.5:
            off += 1
            continue
        if caps is None or any(a <= t <= b for a, b in caps):
            cx0, cy0, cx1, cy1 = CAPTION_RECT
            ub0 = y - 0.9 * h  # head and body (upper 60 %)
            ub1 = y - 0.3 * h
            cov = max(0.0, min(x1, cx1) - max(x0, cx0)) * max(0.0, min(ub1, cy1) - max(ub0, cy0))
            if cov / max((x1 - x0) * (ub1 - ub0), 1e-6) > 0.5:
                under += 1
    missing = max(0, want - len(pts))  # no sample: behind the camera / not drawn
    bad = (off + under + missing) / max(want, len(pts), 1)
    if bad > OFF_FRAC:
        return ("OFF_FRAME", f"{bad * 100:.0f}% of {dur:.1f} s off the frame / under the caption (off {off}, under "
                f"caption {under}, not drawn {missing} of {max(want, len(pts))} samples)")
    return None


def flags_for(s, cat, tr=None, vp=(1366.0, 1024.0), caps=None):
    out = []
    if tr is not None and s["verb"] in ("walk", "run", "climb", "fly"):
        of = off_frame(s, tr, vp, caps)
        if of:
            out.append(of)
    skin_c = cat.get(s["skin"], {})
    n = sum(f[2] for f in s["figs"]) or 1
    # "rig": the legacy leg rig (sun_wind); "gait-<kind>": an object's own paper motion (CastPuppet._gait_step:
    # hop / crawl / roll / thump / stride, patjuk's helpers) - neither is a static card
    static = [(f, v, c) for f, v, c in s["figs"] if v != "rig" and not v.startswith("gait") and f not in skin_c]
    nstatic = sum(c for _, _, c in static)
    h = max(s["hgt"], 0.01)
    if s.get("track_only"):
        return out
    if s["verb"] in ("walk", "run", "climb") and nstatic > 0.25 * n:
        out.append(("STATIC_CARD", "figs=" + ",".join(f"{f}:{v}:{c}" for f, v, c in static)))
        tv = {v for _, v, _ in static if v in ("front", "back", "side")} | {v for v, c in s["views"].items() if c > 0.2 * n}
        for v in sorted(tv):
            if not any(cv == v for cv in skin_c.values()):
                out.append(("CYCLE_MISSING", f"view={v} catalog cycles of {s['skin'] or '?'}: "
                            + (",".join(f"{c}:{cv}" for c, cv in sorted(skin_c.items())) or "none")))
    if s["verb"] == "run":
        for f, v, c in s["figs"]:
            if f in skin_c and "run" not in f and c > 0.25 * n:
                runs = [cn for cn, cv in skin_c.items() if cv == v and "run" in cn]
                out.append(("RUN_WALK_CYCLE" if runs else "RUN_NO_RUN_CYCLE",
                            f"shows {f} ({v})" + (f"; catalog has {','.join(runs)}" if runs else f"; no run cycle for view {v}")))
    cyc_frames = sum(c for f, v, c in s["figs"] if f in skin_c)
    dg = s["dg"] if s.get("dg", -1) >= 0 else s["exp"] * 0.9 * h
    dz = s["dz"] if s.get("dz", -1) >= 0 else max(0.0, s["dist"] - dg)
    if s["verb"] in ("walk", "run") and cyc_frames > 0.8 * n and dg > 0.5 * h and s["exp"] > 0:
        r = s["cyc"] / s["exp"]
        # (2026-11-24) the shown-cycle count moves in whole drawn frames (½ cycle for a 2-frame back / front cycle,
        # plus the frame the paper turn swaps in): on a sub-metre shuffle at a door that is ±0.5 by itself
        # (three_pigs pig_a: 1.00 for 0.70 = one frame); only a gap larger than one frame step is a skate
        if (r < 0.6 or r > 1.4) and abs(s["cyc"] - s["exp"]) > 0.5:
            out.append(("SKATE", f"cycles {s['cyc']:.2f} for {s['exp']:.2f} expected (x{r:.2f})"))
    if s["verb"] == "fly" and nstatic > 0.6 * n and dg > 1.0 * h and dz < 0.2 * dg:
        out.append(("GLIDE", f"{dg / h:.1f} heights along the ground with {static[0][0] if static else '?'}"))
    if s["dvmax"] > 2.5 * h and s["dvmax"] > 0.5 * s["vmax"]:
        out.append(("SPEED_JUMP", f"dv {s['dvmax']:.2f}/s in one frame (vmax {s['vmax']:.2f}, height {h:.2f})"))
    return out


def events(text):
    """(key, occurrence) -> t for LINE / SEG / BEAT prints (to map one run's clock onto another run's recording)."""
    out, seen = {}, defaultdict(int)
    for m in re.finditer(r"^((?:LINE|SEG|BEAT) \S+(?: \d+)?) t=(\d+(?:\.\d+)?)", text, re.M):
        k = m.group(1)
        out[(k, seen[k])] = float(m.group(2))
        seen[k] += 1
    return out


def clock_map(text, ref_text):
    """t in this log -> t in the reference log (the one recorded with the mp4): shift of the last shared event."""
    a, b = events(text), events(ref_text)
    pairs = sorted((a[k], b[k]) for k in a if k in b)
    if not pairs:
        return lambda t: t
    def f(t):
        sh = pairs[0][1] - pairs[0][0]
        for ta, tb in pairs:
            if ta > t:
                break
            sh = tb - ta
        return t + sh
    return f


def video_info(mp4):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "stream=width,height:format=duration", "-of", "json", str(mp4)], capture_output=True, text=True,
                       check=True)
    j = json.loads(r.stdout)
    st = j["streams"][0]
    return int(st["width"]), int(st["height"]), float(j["format"]["duration"])


def frames(mp4, t0, dur, w, h):
    cmd = ["ffmpeg", "-loglevel", "error", "-ss", f"{max(0.0, t0):.3f}", "-t", f"{dur:.3f}", "-i", str(mp4),
           "-vf", f"fps={FPS}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    n = len(raw) // (w * h * 3)
    from PIL import Image
    return [Image.frombuffer("RGB", (w, h), raw[i * w * h * 3:(i + 1) * w * h * 3]) for i in range(n)]


def interp(pts, t):
    """pts [(t, x, y, h)] sorted -> (x, y, h) at t (clamped)."""
    if not pts:
        return None
    if t <= pts[0][0]:
        return pts[0][1:4]
    for a, b in zip(pts, pts[1:]):
        if a[0] <= t <= b[0]:
            k = (t - a[0]) / max(b[0] - a[0], 1e-6)
            return tuple(a[i] + (b[i] - a[i]) * k for i in (1, 2, 3))
    return pts[-1][1:4]


def track_points(s, tr, W, H):
    """Foot point + on-screen height in VIDEO px over time: TRACK (viewport px, finer) if logged, else MOVE trk."""
    pts = []
    tt = [q for q in tr.get(s["role"], []) if s["t0"] - 0.5 <= q[0] <= s["t1"] + 0.5]
    if len(tt) >= 2:
        vw = 1366.0
        vh = 1024.0
        pts = [(q[0], q[1] / vw * W, q[2] / vh * H, q[3] / vh * H) for q in tt]
    elif s["trk"]:
        pts = [(q[0], q[1] * W, q[2] * H, q[3] * H) for q in s["trk"]]
    return pts


def make_sheet(mp4, s, tr, W, H, off, out_base, cmap=lambda t: t):
    from PIL import Image, ImageDraw
    pts = track_points(s, tr, W, H)
    box = s.get("box")
    if pts:
        hmax = max(p[3] for p in pts)
    elif box:
        hmax = (box[3] - box[1]) * H
    else:
        hmax = H / 2.4
    ch = int(min(H, max(160, 2.4 * hmax)))
    cw = int(min(W, ch * 1.25))
    t0 = s["t0"] - 0.25
    t1 = s["t1"] + 0.25
    imgs = frames(mp4, cmap(t0) + off, t1 - t0, W, H)
    tw = int(TILE_H * cw / ch)
    paths = []
    for part in range(0, max(1, len(imgs)), MAX_TILES):
        chunk = imgs[part:part + MAX_TILES]
        rows = max(1, (len(chunk) + COLS - 1) // COLS)
        sheet = Image.new("RGB", (COLS * tw, rows * TILE_H), (20, 20, 20))
        dr = ImageDraw.Draw(sheet)
        for i, im in enumerate(chunk):
            t = t0 + (part + i) / FPS
            ch_i, cw_i = ch, cw
            if pts:
                x, y, hh = interp(pts, t)
                cx, cy = x, y - hh * 0.5
                ch_i = int(min(H, max(140, 2.6 * hh)))  # zoom follows the mover's size in this frame
                cw_i = int(min(W, ch_i * cw / ch))
            elif box:
                cx, cy = (box[0] + box[2]) * 0.5 * W, (box[1] + box[3]) * 0.5 * H
            else:
                cx, cy = W / 2, H / 2
            x0 = int(min(max(0, cx - cw_i / 2), W - cw_i))
            y0 = int(min(max(0, cy - ch_i / 2), H - ch_i))
            tile = im.crop((x0, y0, x0 + cw_i, y0 + ch_i)).resize((tw, TILE_H))
            sx, sy = (i % COLS) * tw, (i // COLS) * TILE_H
            sheet.paste(tile, (sx, sy))
            dr.rectangle((sx, sy, sx + 52, sy + 14), fill=(0, 0, 0))
            dr.text((sx + 3, sy + 2), f"{t:.2f}", fill=(255, 255, 120))
        p = out_base if part == 0 else out_base.with_name(out_base.stem + f"_p{part // MAX_TILES + 1}.jpg")
        sheet.save(p, quality=85)
        paths.append(p)
    return paths


VERDICT_RE = re.compile(r"^\|\s*(\d+)\s*\|")


def old_verdicts(md: Path, run_id: str):
    """Keep verdicts of a previous review of the SAME run (keyed by segment number + actor + t0)."""
    if not md.exists():
        return {}
    txt = md.read_text()
    if f"run: {run_id}" not in txt:
        return None  # another run: archive, start fresh
    out = {}
    for ln in txt.splitlines():
        if VERDICT_RE.match(ln):
            c = [x.strip() for x in ln.strip().strip("|").split("|")]
            if len(c) >= 10:
                out[(c[2], c[1])] = (c[8], c[9])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tale")
    ap.add_argument("log")
    ap.add_argument("mp4")
    ap.add_argument("--offset", type=float, default=None)
    ap.add_argument("--no-tiles", action="store_true")
    ap.add_argument("--out", default=None, help="write tiles + motion_review.md here instead of artifacts/<tale>/motion "
                    "(a beat check that must not replace the tale's gate review)")
    ap.add_argument("--ref-log", default=None, help="the log recorded WITH the mp4, when <run.log> is a later re-run "
                    "of the same build (no movie): times are mapped through shared LINE / SEG / BEAT prints")
    a = ap.parse_args()
    log = Path(a.log)
    mp4 = Path(a.mp4)
    text = log.read_text(errors="replace")
    segs = parse_moves(text)
    tr = parse_track(text)
    if not segs and tr:
        segs = segs_from_track(tr)
        print("MOTION_NOTE no MOVE lines; segments from TRACK only (no cycle / skate checks)")
    if not segs:
        print(f"MOTION_NOLOG {log}: no MOVE (or TRACK) lines - this log predates StoryActor's MOVE print; record a new run")
        print("MOTION_FLAGS=?")
        sys.exit(2)
    W, H, dur = video_info(mp4)
    ref_text = Path(a.ref_log).read_text(errors="replace") if a.ref_log else text
    cmap = clock_map(text, ref_text) if a.ref_log else (lambda t: t)
    if a.offset is None:
        ts = [float(x) for x in re.findall(r"\bt=(\d+(?:\.\d+)?)", ref_text)]
        last = max(ts) if ts else dur
        off = max(0.0, min(3.0, dur - last - 1.0 / 30.0))
    else:
        off = a.offset
    print(f"MOTION_OFFSET {off:.2f} (video {dur:.1f} s, {W}x{H})")
    cat = catalog_cycles()
    out = Path(a.out) if a.out else ROOT / "artifacts" / a.tale / "motion"
    out.mkdir(parents=True, exist_ok=True)
    md = out / "motion_review.md"
    run_id = f"{log.name} {log_hash(log)}"
    prev = old_verdicts(md, run_id)
    if prev is None:
        md.rename(out / f"motion_review_{md.stat().st_mtime:.0f}.md")
        prev = {}
    rows = []
    nflags = 0
    caps = parse_captions(ref_text)
    m = re.search(r"^TRACK_VP (\d+)x(\d+)", text, re.M)
    vp = (float(m.group(1)), float(m.group(2))) if m else (1366.0, 1024.0)
    for i, s in enumerate(segs, 1):
        fl = flags_for(s, cat, tr, vp, caps)
        for k, why in fl:
            nflags += 1
            print(f"MOTION_FLAG {i:02d} {k} {s['role']} t={s['t0']:.2f}-{s['t1']:.2f} {s['verb']} {why}")
        name = f"{i:02d}_{s['role']}_{s['t0']:.1f}.jpg"
        tiles = [out / name]
        if not a.no_tiles:
            tiles = make_sheet(mp4, s, tr, W, H, off, out / name, cmap)
        figs = ", ".join(f"{f}({v})x{c}" for f, v, c in s["figs"])
        v, note = prev.get((s["role"], f"{s['t0']:.2f}-{s['t1']:.2f}"), ("", ""))
        rows.append(f"| {i:02d} | {s['t0']:.2f}-{s['t1']:.2f} | {s['role']} | {s['verb']} | {s['cycle']} | "
                    f"{s['dist']:.2f} ({s['dist'] / max(s['hgt'], 0.01):.1f} H) | {'; '.join(k for k, _ in fl) or '-'} | "
                    f"{' '.join(t.name for t in tiles)} | {v} | {note} |")
        print(f"MOTION_SEG {i:02d} {s['role']} {s['verb']} {s['cycle']} t={s['t0']:.2f}-{s['t1']:.2f} figs={figs}")
    md.write_text(
        f"# Motion review: {a.tale}\n\nrun: {run_id}\nvideo: {mp4} (offset {off:.2f} s)\n\n"
        "Open EVERY tile sheet (8 fps, zoomed on the mover, time in the corner) and fill `verdict` with `ok` or `fix`,\n"
        "and a short note (what you saw: cycle reads, feet on the ground, faces the travel way, no hop / skate /\n"
        "moonwalk / pop). gate.py fails while any verdict is empty or `fix`. Auto flags are in `flags`; a flagged row\n"
        "marked ok also needs an accepted exception in gate.md.\n\n"
        "| # | t (story s) | actor | verb | cycle | dist | flags | tiles | verdict | note |\n"
        "|---|---|---|---|---|---|---|---|---|---|\n" + "\n".join(rows) + "\n")
    print(f"MOTION_SEGMENTS={len(segs)}")
    print(f"MOTION_FLAGS={nflags}")
    print(f"MOTION_REVIEW {md}")


if __name__ == "__main__":
    main()
