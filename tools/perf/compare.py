#!/usr/bin/env python3
"""Image compare for perf before/after. python3 tools/perf/compare.py A_TAG B_TAG [views...] [--sheet out.png]
Per view: mean abs diff (0-255), p99 abs diff, % pixels with diff > 8 and > 24 (max channel), PSNR; writes a diff
heat image game/captures/perf/diff_A_B_<v>.png and an optional before|after|diff contact sheet."""
import sys, math
import numpy as np
from PIL import Image
D = "/Users/house_of_4k2b/orca/popup-atlas/game/.agent_out/captures/perf"
args = [a for a in sys.argv[1:] if not a.startswith("--")]
sheet = None
if "--sheet" in sys.argv:
    sheet = sys.argv[sys.argv.index("--sheet") + 1]
    args = [a for a in args if a != sheet]
a_tag, b_tag = args[0], args[1]
views = args[2:] or ["0", "1", "2", "3", "4", "5"]
rows = []
for v in views:
    a = np.asarray(Image.open(f"{D}/{a_tag}_{v}.png").convert("RGB")).astype(np.int16)
    b = np.asarray(Image.open(f"{D}/{b_tag}_{v}.png").convert("RGB")).astype(np.int16)
    d = np.abs(a - b)
    m = d.max(axis=2)
    mse = float((d.astype(np.float64) ** 2).mean())
    psnr = 99.0 if mse == 0 else 10 * math.log10(255 ** 2 / mse)
    print(f"view {v}: mean {d.mean():.3f}  p99 {np.percentile(m, 99):.0f}  >8 {100*(m>8).mean():.3f}%  >24 {100*(m>24).mean():.3f}%  max {m.max()}  PSNR {psnr:.1f} dB")
    heat = np.clip(m * 8, 0, 255).astype(np.uint8)
    Image.fromarray(heat).save(f"{D}/diff_{a_tag}_{b_tag}_{v}.png")
    rows.append((a, b, heat))
if sheet:
    w = 456
    tiles = []
    for a, b, heat in rows:
        ims = [Image.fromarray(a.astype(np.uint8)), Image.fromarray(b.astype(np.uint8)), Image.fromarray(heat).convert("RGB")]
        ims = [im.resize((w, int(w * im.height / im.width))) for im in ims]
        row = Image.new("RGB", (w * 3 + 8, ims[0].height), (255, 255, 255))
        for i, im in enumerate(ims):
            row.paste(im, (i * (w + 4), 0))
        tiles.append(row)
    H = sum(t.height + 4 for t in tiles)
    out = Image.new("RGB", (tiles[0].width, H), (255, 255, 255))
    y = 0
    for t in tiles:
        out.paste(t, (0, y)); y += t.height + 4
    out.save(sheet)
    print("sheet", sheet)
