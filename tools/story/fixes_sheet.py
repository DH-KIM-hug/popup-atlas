#!/usr/bin/env python3
"""Before / after sheet, one row per fix: fixes_sheet.py OUT.jpg BEFORE.mp4 AFTER.mp4 "label|t_before|t_after" ...
(t may be a comma list for several frames per side). Frames scaled to 400 px wide, label above each row."""
import io, subprocess, sys
from PIL import Image, ImageDraw

W = 400


def frame(v, t):
    b = subprocess.run(["ffmpeg", "-loglevel", "error", "-ss", str(t), "-i", v, "-frames:v", "1", "-f", "image2pipe",
                        "-vcodec", "png", "-"], capture_output=True).stdout
    im = Image.open(io.BytesIO(b)).convert("RGB")
    return im.resize((W, int(im.height * W / im.width)))


out, bv, av = sys.argv[1:4]
rows = []
for spec in sys.argv[4:]:
    label, tb, ta = spec.split("|")
    ims = [("before", bv, float(t)) for t in tb.split(",") if t] + [("after", av, float(t)) for t in ta.split(",") if t]
    fr = []
    for tag, v, t in ims:
        im = frame(v, t)
        d = ImageDraw.Draw(im)
        d.rectangle([0, 0, 150, 20], fill=(0, 0, 0) if tag == "after" else (120, 0, 0))
        d.text((4, 4), f"{tag} {int(t // 60)}:{t % 60:04.1f}", fill=(255, 255, 0))
        fr.append(im)
    h = fr[0].height
    row = Image.new("RGB", (W * len(fr), h + 26), (24, 24, 24))
    ImageDraw.Draw(row).text((6, 6), label, fill=(255, 255, 255))
    for i, im in enumerate(fr):
        row.paste(im, (i * W, 26))
    rows.append(row)
wmax = max(r.width for r in rows)
sheet = Image.new("RGB", (wmax, sum(r.height for r in rows)), (24, 24, 24))
y = 0
for r in rows:
    sheet.paste(r, (0, y))
    y += r.height
sheet.save(out, quality=82)
print(out, sheet.size)
