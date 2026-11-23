#!/usr/bin/env python3
"""Motion tiles cut around a runner, from a recording + a run log made with --log-track (StoryActor TRACK lines).

  python3 tools/story/run_tiles.py VIDEO TRACK_LOG ROLE T0 T1 OUT.jpg [--shift S] [--n 8] [--size 220] [--label TXT] [--cols C]
  python3 tools/story/run_tiles.py --list TRACK_LOG          # every travel: role, t0..t1, figures, screen height

TRACK lines give the foot point (x, y) and the on-screen height h in viewport px; the video may be a different size
(scaled to it: the viewport is the project base size --vp WxH, default 1366x1024, whatever the window size). --shift adds S seconds to the log times (align a log
made in a quick run with an older movie: the beat start difference). Each tile is a square crop of 1.5 h (at least
60 px) centred on the figure's middle, so the cycle, facing and feet read; a strip of N tiles evenly over T0..T1.
"""
import argparse, os, re, subprocess, sys, tempfile
from PIL import Image, ImageDraw, ImageFont

TR = re.compile(r"^TRACK (\S+) (.*)$")


def tracks(log):
    out = []
    for l in open(log, errors="replace"):
        m = TR.match(l)
        if m:
            d = dict(re.findall(r"(\w+)=(\S+)", m.group(2)))
            d["role"] = m.group(1)
            for k in ("t", "v"):
                d[k] = float(d[k])
            for k in ("x", "y", "h"):
                d[k] = int(d[k])
            out.append(d)
    return out


def travels(rows, gap=1.0):
    segs = {}
    for d in rows:
        s = segs.setdefault(d["role"], [])
        if s and d["t"] - s[-1][-1]["t"] < gap:
            s[-1].append(d)
        else:
            s.append([d])
    return [(r, s) for r, ss in segs.items() for s in ss]


def font(sz):
    for p in ("/System/Library/Fonts/AppleSDGothicNeo.ttc", "/System/Library/Fonts/Supplemental/Arial.ttf"):
        if os.path.exists(p):
            return ImageFont.truetype(p, sz)
    return ImageFont.load_default()


def strip(video, rows, role, t0, t1, n=8, size=220, shift=0.0, vp=(1366, 1024), label="", cols=0):
    rs = [d for d in rows if d["role"] == role and t0 - 0.01 <= d["t"] <= t1 + 0.01]
    if not rs:
        raise SystemExit(f"no TRACK rows for {role} in {t0}..{t1}")
    pick = [rs[round(i * (len(rs) - 1) / max(1, n - 1))] for i in range(n)]
    probe = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                            "-of", "csv=p=0", video], capture_output=True, text=True).stdout.split(",")
    W, H = int(probe[0]), int(probe[1])
    sx, sy = W / vp[0], H / vp[1]
    lab_h = 22
    cols = cols or n
    nr = (n + cols - 1) // cols
    sheet = Image.new("RGB", (cols * size, nr * (size + lab_h)), (24, 24, 24))
    dr = ImageDraw.Draw(sheet)
    f = font(14)
    with tempfile.TemporaryDirectory() as td:
        for i, d in enumerate(pick):
            fn = os.path.join(td, f"{i}.png")
            subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{d['t'] + shift:.3f}", "-i", video,
                            "-frames:v", "1", fn], check=True)
            im = Image.open(fn).convert("RGB")
            h = max(60, d["h"] * 1.5) * sy
            cx, cy = d["x"] * sx, (d["y"] - d["h"] * 0.5) * sy
            box = (int(cx - h / 2), int(cy - h / 2), int(cx + h / 2), int(cy + h / 2))
            tile = Image.new("RGB", (box[2] - box[0], box[3] - box[1]), (0, 0, 0))
            cb = (max(0, box[0]), max(0, box[1]), min(W, box[2]), min(H, box[3]))
            if cb[2] > cb[0] and cb[3] > cb[1]:  # off-screen runners show black (and that is a finding)
                tile.paste(im.crop(cb), (max(0, -box[0]), max(0, -box[1])))
            ox, oy = (i % cols) * size, (i // cols) * (size + lab_h)
            sheet.paste(tile.resize((size, size)), (ox, oy + lab_h))
            dr.text((ox + 4, oy + 3), f"{d['t'] + shift:.2f}s {d['fig']}", fill=(235, 235, 235), font=f)
    if label:
        out = Image.new("RGB", (sheet.width, sheet.height + 26), (12, 12, 12))
        out.paste(sheet, (0, 26))
        ImageDraw.Draw(out).text((6, 4), label, fill=(255, 220, 120), font=font(17))
        sheet = out
    return sheet


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("args", nargs="*")
    ap.add_argument("--list")
    ap.add_argument("--shift", type=float, default=0.0)
    ap.add_argument("--n", type=int, default=8)
    ap.add_argument("--size", type=int, default=220)
    ap.add_argument("--vp", default="1366x1024")
    ap.add_argument("--label", default="")
    ap.add_argument("--cols", type=int, default=0)
    a = ap.parse_args()
    if a.list:
        for r, s in travels(tracks(a.list)):
            figs = []
            for d in s:
                if not figs or figs[-1] != d["fig"]:
                    figs.append(d["fig"])
            hs = [d["h"] for d in s]
            print(f"{r:8s} {s[0]['t']:7.2f}..{s[-1]['t']:7.2f}  h {min(hs)}-{max(hs)}  vmax {max(d['v'] for d in s):.2f}  "
                  f"{' > '.join(figs)}")
        return
    video, log, role, t0, t1, out = a.args
    vp = tuple(int(v) for v in a.vp.split("x"))
    strip(video, tracks(log), role, float(t0), float(t1), a.n, a.size, a.shift, vp, a.label, a.cols).save(out, quality=88)
    print(out)


if __name__ == "__main__":
    main()
