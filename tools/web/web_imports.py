#!/usr/bin/env python3
"""Web-only texture import settings, applied to the throwaway copy build/web_project (never to game/).
   python3 tools/web/web_imports.py <project dir> [quality 0.82] [scale 0.75]
- compress/mode=1 (lossy WebP at `quality`): the pck is ~1/4 the size (Godot web keeps the whole pck in memory);
- process/size_limit = longest side * `scale` (textures over 256 px): GPU memory ~scale^2 (all textures are
  uncompressed RGBA, so a tale holds ~850 MB at full size, too close to an iPad Safari tab's limit).
- writes res://web_src_sizes.json {res path: [w, h]} of every downscaled texture: art data in pixels (bodies.json
  house outlines, stages.json facade bands) is in full-size px, and PaperCard.src_px_scale() (web only) uses this map
  to bring traced / used rects of the smaller image back to those px (else house bodies come out 1/scale too big)."""
import glob, json, os, re, sys
from PIL import Image

root = sys.argv[1]
q = float(sys.argv[2]) if len(sys.argv) > 2 else 0.82
scale = float(sys.argv[3]) if len(sys.argv) > 3 else 0.75
n = 0
sizes = {}
for imp in glob.glob(os.path.join(root, "**", "*.import"), recursive=True):
    if "/.godot/" in imp:
        continue
    s = open(imp, encoding="utf-8").read()
    if 'importer="texture"' not in s:
        continue
    s = re.sub(r"(?m)^compress/mode=0$", "compress/mode=1", s)
    s = re.sub(r"(?m)^compress/lossy_quality=.*$", f"compress/lossy_quality={q}", s)
    try:
        w, h = Image.open(imp[: -len(".import")]).size
        m = max(w, h)
        if scale < 1.0 and m > 256:
            s = re.sub(r"(?m)^process/size_limit=.*$", f"process/size_limit={int(round(m * scale))}", s)
            sizes["res://" + os.path.relpath(imp[: -len(".import")], root).replace(os.sep, "/")] = [w, h]
    except Exception:
        pass
    open(imp, "w", encoding="utf-8").write(s)
    n += 1
json.dump(sizes, open(os.path.join(root, "web_src_sizes.json"), "w"), separators=(",", ":"))
print(f"web imports: {n} textures, lossy q={q}, scale={scale}")
