#!/usr/bin/env python3
"""「늑대와 일곱 아기염소」 (wolf_goats) post-slice fixes for its atlas sheets (re-run after tools/atlas/add_sheet.py):
  python3 tools/atlas/wg_fixes.py
- story_wg_cottage_04o: the inside front wall with its doorway cut out (shown while the door stands open).
- story_wg_room_01 / story_wg_hide_01 (the open clocks): the door's glass pane came out lavender (the magenta keyer half-cleared it):
  magenta-hued pixels become a pale blue-grey glass, opaque.
"""
import os
import numpy as np
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))


def deglass(p):
    a = np.asarray(Image.open(p).convert("RGBA")).astype(float)
    r, g, b, al = a[..., 0], a[..., 1], a[..., 2], a[..., 3]
    m = (np.minimum(r, b) - g > 25) & (np.abs(r - b) < 60) & (al > 0)
    lum = (r + g + b) / 3
    a[m, 0], a[m, 1], a[m, 2] = lum[m] * 0.85, lum[m] * 0.92, np.minimum(255, lum[m] * 1.05)
    a[m, 3] = np.maximum(al[m], 230)
    Image.fromarray(a.clip(0, 255).astype("uint8")).save(p, "WEBP", lossless=True, quality=100, method=6)
    return int(m.sum())


def wall_in_open():
    """story_wg_cottage_04o: the front wall seen from inside with the doorway cut out (the door stands open: the
    real door leaf and the yard show through it). Catalogued next to story_wg_cottage_04 (merge-only write)."""
    import json
    src = os.path.join(ROOT, "game/art/atlas/story_wg_cottage/story_wg_cottage_04.webp")
    dst = src.replace("_04.webp", "_04o.webp")
    a = np.array(Image.open(src).convert("RGBA"))
    h, w = a.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    cx, top, r, x0, x1 = 346.0, 82.0, 64.0, 283, 410
    hole = (xx >= x0) & (xx <= x1) & ((yy >= top + r) | ((xx - cx) ** 2 + (yy - (top + r)) ** 2 <= r * r))
    a[hole, 3] = 0
    Image.fromarray(a).save(dst, "WEBP", lossless=True, quality=100, method=6)
    cp = os.path.join(ROOT, "game/art/atlas/catalog.json")
    cat = json.load(open(cp))  # re-read right before writing (another agent may share the catalog)
    base = next(e for e in cat if e["id"] == "story_wg_cottage_04")
    e = dict(base, id="story_wg_cottage_04o", path=base["path"].replace("_04.webp", "_04o.webp"),
             label=base["label"] + " -- doorway open (cut out)", tags=sorted(set(base["tags"] + ["open"])))
    cat = [q for q in cat if q["id"] != e["id"]] + [e]
    json.dump(cat, open(cp, "w"), indent=1, ensure_ascii=False)
    return int(hole.sum())


if __name__ == "__main__":
    print("wall_in_open", wall_in_open())
    for rel in ["game/art/atlas/story_wg_room/story_wg_room_01.webp", "game/art/atlas/story_wg_hide/story_wg_hide_01.webp"]:
        print(rel, deglass(os.path.join(ROOT, rel)))
