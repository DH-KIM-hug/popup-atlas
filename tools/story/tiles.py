#!/usr/bin/env python3
"""8 fps motion tile from a recording: python3 tools/story/tiles.py IN.mp4 START DUR X Y W H OUT.jpg [cols]
(crop in 1366x1024 frame px, each tile scaled to 2x). Check walks / turns for moonwalking, splay feet, legs leaving
the garment, wobble, wrong-facing cards, cards in the lens."""
import subprocess, sys
src, t, d, x, y, w, h, out = sys.argv[1:9]
cols = int(sys.argv[9]) if len(sys.argv) > 9 else 8
n = int(round(float(d) * 8))
rows = max(1, (n + cols - 1) // cols)
subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", t, "-t", d, "-i", src, "-vf",
                f"fps=8,crop={w}:{h}:{x}:{y},scale={int(w)*2}:{int(h)*2},tile={cols}x{rows}", "-frames:v", "1", out],
               check=True)
print(out)
