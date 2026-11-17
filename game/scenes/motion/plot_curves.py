#!/usr/bin/env python3
"""Plot hinge angle vs time (curves.json from curve_job.gd) to PNG with PIL. usage: plot_curves.py curves.json out.png"""
import json, sys
from PIL import Image, ImageDraw, ImageFont

c = json.load(open(sys.argv[1])); out = sys.argv[2]
W, H = 1400, 760; L, R, T, B = 90, 30, 70, 230
im = Image.new("RGB", (W, H), (250, 246, 238)); d = ImageDraw.Draw(im)
try:
    f = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 20); fs = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 16)
except Exception:
    f = fs = ImageFont.load_default()
t = c["t"]; tmax = t[-1]; amin, amax = -5, 100
X = lambda x: L + (W - L - R) * x / tmax
Y = lambda a: T + (H - T - B) * (amax - a) / (amax - amin)
for a in range(0, 101, 10):
    d.line((L, Y(a), W - R, Y(a)), fill=(225, 218, 205)); d.text((L - 40, Y(a) - 9), f"{a}°", fill=(90, 80, 70), font=fs)
for s10 in range(0, int(tmax * 10) + 1, 2):
    x = X(s10 / 10); d.line((x, T, x, H - B), fill=(232, 226, 214)); d.text((x - 12, H - B + 6), f"{s10/10:.1f}", fill=(90, 80, 70), font=fs)
d.line((L, Y(90), W - R, Y(90)), fill=(150, 140, 125), width=2)
x0 = X(c["rise_s"]); d.line((x0, T, x0, H - B), fill=(120, 110, 100), width=2)
d.text((X(0.02), T - 30), "pop_up() at t=0", fill=(60, 50, 40), font=f); d.text((x0 + 8, T - 30), "fold_down()", fill=(60, 50, 40), font=f)
cols = {"small": (214, 120, 60), "medium": (70, 130, 110), "large": (60, 80, 150)}
for k, col in cols.items():
    pts = [(X(tt), Y(a)) for tt, a in zip(t, c[k]["angle"])]
    d.line(pts, fill=col, width=3)
    tw = [(X(tt), Y(45 + 4 * a)) for tt, a in zip(t, c[k]["twist"])]  # twist x4 around 45 for visibility
    d.line(tw, fill=tuple(int(v * 0.5 + 125) for v in col), width=1)
d.text((L, 20), "PopHinge angle vs time (90° = standing, 0° = flat on page); thin lines: twist wobble x4 around 45°", fill=(40, 35, 30), font=f)
y = H - B + 40
for k, col in cols.items():
    s = c["stats"][k]
    d.rectangle((L, y + 4, L + 28, y + 16), fill=col)
    d.text((L + 40, y), f"{k:6s} w {c[k]['weight']}: vertical at {s.get('reach_s',0):.2f} s, overshoot {s['overshoot_deg']:.1f}°, "
           f"±0.5° at {s['settle_s']:.2f} s (+{s.get('settle_after_vertical_s',0):.2f} s), twist ≤{s.get('twist_peak_deg',0):.1f}°;"
           f" fold: touches {s['first_touch_s']:.2f} s, air-cushion settle {s.get("fold_rebound_deg",0):.1f}°, rest {s['rest_s']:.2f} s", fill=(40, 35, 30), font=f)
    y += 34
d.text((L, y + 6), "time (s)", fill=(90, 80, 70), font=fs)
im.save(out); print(out)
