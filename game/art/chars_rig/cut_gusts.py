"""Lift the paper wind-curl strips off sw_wind.webp into separate gust cards (gust_curl_*.png)."""
import os, sys
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cut_rig import label
HERE = os.path.dirname(os.path.abspath(__file__))
a = np.array(Image.open(os.path.join(HERE, "..", "chars", "sw_wind.webp")).convert("RGBA"))
ai = a.astype(int)
m = (a[..., 3] > 60) & (ai[..., 2] > ai[..., 0] + 12)
m[:, 118:] = False
lab, n = label(m)
comps = sorted(((int((lab == i).sum()), i) for i in range(1, n + 1)), reverse=True)
k = 0
for area, i in comps[:3]:
    if area < 800:
        continue
    ys, xs = np.where(lab == i)
    out = np.zeros_like(a)
    out[lab == i] = a[lab == i]
    out = out[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    Image.fromarray(out).save(os.path.join(HERE, f"gust_curl_{k}.png"))
    print(k, area, out.shape)
    k += 1
