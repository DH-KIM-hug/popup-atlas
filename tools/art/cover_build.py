#!/usr/bin/env python3
"""Ship a tale's cover art: key the cut-paper title (magenta) into a transparent decal, convert the key art.

  python3 tools/art/cover_build.py <tale_id> <art.png> [<title.png>]
  -> game/stories/<tale_id>/art/cover_art.webp (q 90, max 1600 px tall), cover_title.webp (lossless, trimmed)

Title keying: the slicer's soft magenta key (tools/atlas/slice_atlas.key + unmix/despill), then everything enclosed
by the sticker's outer outline is made opaque again with its raw colour (purple letters / ribbons sit in the keyer's
hue window), trimmed with a 6 px pad. Prints the decal's aspect so cover config can size it.
"""
import os, sys
import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "tools", "atlas"))
import slice_atlas as SA  # noqa: E402


def key_title(path):
    rgb = np.asarray(Image.open(path).convert("RGB")).astype(np.float32) / 255.0
    bg = SA.estimate_bg(rgb)
    a = SA.key(rgb, bg)
    out = SA.unmix_despill(rgb, a, bg)
    # outer silhouette: flood the background from the border on the binary mask; whatever is not reached is inside
    solid = (a > 0.5)
    m = Image.fromarray(np.where(solid, 255, 0).astype(np.uint8)).copy()
    pad = Image.new("L", (m.width + 2, m.height + 2), 0)
    pad.paste(m, (1, 1))
    ImageDraw.floodfill(pad, (0, 0), 128)
    outside = np.asarray(pad)[1:-1, 1:-1] == 128
    inside = ~outside
    # interior pixels (>= 3 px from the outline) take their raw colour fully opaque
    core = SA.erode(inside, 3)
    out[core] = rgb[core]
    alpha = a.copy()
    alpha[core] = 1.0
    rgba = np.dstack([out, alpha])
    ys, xs = np.where(alpha > 0.02)
    y0, y1, x0, x1 = max(ys.min() - 6, 0), ys.max() + 7, max(xs.min() - 6, 0), xs.max() + 7
    rgba = SA.bleed(rgba[y0:y1, x0:x1].copy())
    return Image.fromarray((np.clip(rgba, 0, 1) * 255).astype(np.uint8), "RGBA")


def main():
    tale, art = sys.argv[1], sys.argv[2]
    title = sys.argv[3] if len(sys.argv) > 3 else ""
    od = os.path.join(ROOT, "game", "stories", tale, "art")
    os.makedirs(od, exist_ok=True)
    im = Image.open(art).convert("RGB")
    if im.height > 1600:
        im = im.resize((round(im.width * 1600 / im.height), 1600), Image.LANCZOS)
    im.save(os.path.join(od, "cover_art.webp"), quality=90, method=6)
    print("art", im.size, "aspect h/w", round(im.height / im.width, 4))
    if title:
        t = key_title(title)
        t.save(os.path.join(od, "cover_title.webp"), lossless=True)
        print("title", t.size, "aspect h/w", round(t.height / t.width, 4))


if __name__ == "__main__":
    main()
