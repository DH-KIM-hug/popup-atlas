#!/usr/bin/env python3
"""Contact sheet of a story capture sequence (frame_###.png) as a JPEG, each tile labelled with its index and
story time.  python3 tools/story/sheet.py <capture_dir> <out.jpg> [--every-frames 210] [--cols 8]"""
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

src = Path(sys.argv[1])
out = Path(sys.argv[2])
every = int(sys.argv[sys.argv.index("--every-frames") + 1]) if "--every-frames" in sys.argv else 210
cols = int(sys.argv[sys.argv.index("--cols") + 1]) if "--cols" in sys.argv else 8
frames = sorted(src.glob("frame_*.png"))
tw, th, lab = 341, 256, 22
rows = (len(frames) + cols - 1) // cols
sheet = Image.new("RGB", (cols * tw, rows * (th + lab)), (28, 20, 16))
d = ImageDraw.Draw(sheet)
try:
    font = ImageFont.truetype("/System/Library/Fonts/Menlo.ttc", 15)
except OSError:
    font = ImageFont.load_default()
for i, f in enumerate(frames):
    im = Image.open(f).convert("RGB").resize((tw, th), Image.LANCZOS)
    x, y = (i % cols) * tw, (i // cols) * (th + lab)
    sheet.paste(im, (x, y))
    n = int(f.stem.split("_")[1])
    d.text((x + 4, y + th + 3), f"{n:03d} t={(n + 1) * every / 60.0:.0f}s", fill=(230, 220, 200), font=font)
out.parent.mkdir(parents=True, exist_ok=True)
sheet.save(out, quality=86)
print(out, len(frames), sheet.size)
