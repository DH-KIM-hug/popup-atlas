#!/usr/bin/env python3
"""Paste the shop's mint door card (story_wc_shop_01) into the facade's drawn dark doorway (story_wc_shop_00), so
tools/atlas/house_stages.py can cut it out as the hinged door leaf and leave a real opening into the shop's room
(witch_candy, 2026-11-19). Run after tools/atlas/add_sheet.py story_wc_shop, before house_stages.py.
Doorway in facade px (measured on a gridded crop): x 304..425, arch top 242, sill 443."""
import os
import numpy as np
from PIL import Image
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "game", "art", "atlas", "story_wc_shop")
X0, Y0, X1, Y1 = 304, 242, 425, 443
fac = Image.open(os.path.join(D, "story_wc_shop_00.webp")).convert("RGBA")
door = Image.open(os.path.join(D, "story_wc_shop_01.webp")).convert("RGBA")
a = np.array(door)[..., 3] > 128
ys, xs = np.where(a)
door = door.crop((xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)).resize((X1 - X0, Y1 - Y0), Image.LANCZOS)
under = Image.new("RGBA", door.size, (92, 52, 30, 255))  # the doorway's dark brown behind the door's arch corners
under.alpha_composite(door)
yy, xx = np.mgrid[0:Y1 - Y0, 0:X1 - X0]
r = (X1 - X0) / 2.0
arch = (yy >= r) | ((xx + 0.5 - r) ** 2 + (yy + 0.5 - r) ** 2 <= r * r)
m = Image.fromarray((arch * 255).astype(np.uint8))
fac.paste(under, (X0, Y0), m)
fac.save(os.path.join(D, "story_wc_shop_00.webp"), "WEBP", lossless=True, quality=100, method=6)
print("door pasted")
