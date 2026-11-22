#!/usr/bin/env python3
"""Evenly spaced contact sheet of an mp4 with timestamps (wolf_goats 2026-11-23):
  python3 tools/story/vsheet.py IN.mp4 OUT.jpg [N=12] [COLS=4] [START=0] [END=duration]"""
import subprocess, sys, tempfile, os
from PIL import Image, ImageDraw
src, out = sys.argv[1], sys.argv[2]
n = int(sys.argv[3]) if len(sys.argv) > 3 else 12
cols = int(sys.argv[4]) if len(sys.argv) > 4 else 4
dur = float(subprocess.check_output(["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", src]))
t0 = float(sys.argv[5]) if len(sys.argv) > 5 else 0.0
t1 = float(sys.argv[6]) if len(sys.argv) > 6 else dur - 0.2
tw, th = 400, 300
rows = (n + cols - 1) // cols
sheet = Image.new("RGB", (cols * tw, rows * th), (20, 20, 20))
d = ImageDraw.Draw(sheet)
with tempfile.TemporaryDirectory() as tmp:
    for i in range(n):
        t = t0 + (t1 - t0) * (i + 0.5) / n
        f = os.path.join(tmp, f"{i}.jpg")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", f"{t:.2f}", "-i", src, "-frames:v", "1",
                        "-vf", f"scale={tw}:{th}", f], check=True)
        if os.path.exists(f):
            sheet.paste(Image.open(f), ((i % cols) * tw, (i // cols) * th))
        d.text(((i % cols) * tw + 6, (i // cols) * th + 4), f"{t:.1f}s", fill=(255, 255, 0))
sheet.save(out, quality=85)
print(out)
