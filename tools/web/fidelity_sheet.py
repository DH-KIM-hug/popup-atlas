#!/usr/bin/env python3
"""Side-by-side sheet + numbers for the web-vs-native check (docs/WEB_BUILD.md, "Fidelity check").
   python3 tools/web/fidelity_sheet.py <out.jpg> <label>=<dir> [<label>=<dir> ...]
Rows = every <tale>_<beat>_<t>.png found in the first dir; columns = the dirs. Prints per frame and mean:
luma mean, contrast (luma std), saturation (mean HSV S), each 0..1, measured on the 3D area (the top-left / top-right
buttons and the caption box are masked out). Writes <out>.json with the numbers."""
import glob, json, os, sys
import numpy as np
from PIL import Image, ImageDraw

out = sys.argv[1]
cols = [a.split("=", 1) for a in sys.argv[2:]]
names = sorted(os.path.basename(p) for p in glob.glob(os.path.join(cols[0][1], "*.png")))
names = [n for n in names if all(os.path.exists(os.path.join(d, n)) for _, d in cols)]


def stats(im):
    a = np.asarray(im.convert("RGB").resize((683, 512)), dtype=np.float32) / 255.0
    a = a[70:400]  # skip the button row and the caption box
    l = a @ np.array([0.2126, 0.7152, 0.0722], dtype=np.float32)
    mx, mn = a.max(2), a.min(2)
    s = np.where(mx > 1e-4, (mx - mn) / np.maximum(mx, 1e-4), 0)
    return {"luma": float(l.mean()), "contrast": float(l.std()), "sat": float(s.mean()),
            "p05": float(np.percentile(l, 5)), "p95": float(np.percentile(l, 95))}


W, H = 560, 420
sheet = Image.new("RGB", (W * len(cols) + 8 * (len(cols) - 1), (H + 24) * len(names) + 30), (24, 24, 24))
d = ImageDraw.Draw(sheet)
for c, (lab, _) in enumerate(cols):
    d.text((c * (W + 8) + 6, 8), lab, fill=(255, 255, 255))
res = {}
for r, n in enumerate(names):
    res[n] = {}
    for c, (lab, dr) in enumerate(cols):
        im = Image.open(os.path.join(dr, n))
        st = stats(im)
        res[n][lab] = st
        x, y = c * (W + 8), 30 + r * (H + 24)
        sheet.paste(im.convert("RGB").resize((W, H), Image.LANCZOS), (x, y))
        d.text((x + 4, y + H + 4), f"{n[:-4]}  L {st['luma']:.3f}  C {st['contrast']:.3f}  S {st['sat']:.3f}", fill=(230, 230, 230))
sheet.save(out, quality=88)
mean = {lab: {k: float(np.mean([res[n][lab][k] for n in names])) for k in ("luma", "contrast", "sat", "p05", "p95")} for lab, _ in cols}
json.dump({"frames": res, "mean": mean}, open(os.path.splitext(out)[0] + ".json", "w"), indent=1)
for lab, m in mean.items():
    print(f"{lab:>12}: luma {m['luma']:.3f}  contrast {m['contrast']:.3f}  sat {m['sat']:.3f}  p05 {m['p05']:.3f}  p95 {m['p95']:.3f}  ({len(names)} frames)")
print(out)
