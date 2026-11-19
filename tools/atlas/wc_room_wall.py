#!/usr/bin/env python3
"""witch_candy (2026-11-19): story_wc_room_09 = the shop's back wall (story_wc_room_00) made as tall as the shop's wall
(aspect 1.79 to fit the 1.27 x 0.71 room) by adding a cream plaster band with a wooden picture rail on top, so no gap
shows between the back wall and the ceiling. Catalogued under sheet "story_wc_room_extra" so tools/atlas/add_sheet.py
story_wc_room (which rewrites that sheet's entries) keeps it. Run after add_sheet.py story_wc_room."""
import json, os
import numpy as np
from PIL import Image
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
im = np.array(Image.open("game/art/atlas/story_wc_room/story_wc_room_00.webp").convert("RGBA"))
ys, xs = np.where(im[..., 3] > 128)
core = im[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
H, W = core.shape[:2]
add = max(0, int(round(W / 1.79)) - H)
col = np.median(core[2:8].reshape(-1, 4)[:, :3].astype(float), 0)
band = np.zeros((add, W, 4), np.uint8)
band[..., :3] = np.clip(col + np.random.default_rng(3).normal(0, 4, (add, W, 1)), 0, 255)
band[..., 3] = 255
band[-9:-3, :, :3] = (120, 78, 44)
band[-3:, :, :3] = np.clip(col * 0.92, 0, 255)
out = np.pad(np.concatenate([band, core], 0), ((4, 4), (4, 4), (0, 0)))
Image.fromarray(out).save("game/art/atlas/story_wc_room/story_wc_room_09.webp", "WEBP", lossless=True, quality=100, method=6)
cat = [e for e in json.load(open("game/art/atlas/catalog.json")) if e["id"] != "story_wc_room_09"]
e = dict(next(e for e in cat if e["id"] == "story_wc_room_00"))
e.update({"id": "story_wc_room_09", "sheet": "story_wc_room_extra", "path": "art/atlas/story_wc_room/story_wc_room_09.webp",
          "label": "shop back wall from inside, full height (room_00 + plaster band and rail on top)",
          "height_units": 0.71, "px": [out.shape[1], out.shape[0]]})
json.dump(cat + [e], open("game/art/atlas/catalog.json", "w"), indent=1, ensure_ascii=False)
print("story_wc_room_09", out.shape)
