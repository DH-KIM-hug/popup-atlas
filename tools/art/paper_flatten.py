#!/usr/bin/env python3
"""Paper flatten: take the woolly felt nap out of shipped card / figure textures (wave 1, 2026-11-24).

The library was redrawn as paper once (paper_jobs.py / paper_swap.py / paper_reskin.py), but many shipped textures
still carry a fuzzy, wormy fibre grain that reads as wool felt in close-ups. This retexture keeps each file's size,
alpha and layout (ids, catalog px, rig anchors all stay valid) and only flattens the colour areas:

    upscale (default 2x LANCZOS) -> MedianFilter(7) -> MedianFilter(5) on RGB -> downscale back to the original size
    -> original alpha

Before filtering, transparent pixels are filled with the nearest opaque colour so no background bleeds into edges.
The engine shader (paper_print.gdshader) adds its own fine paper fibre on top.

Usage:
  tools/art/paper_flatten.py [--qa OUT.jpg] [--apply] [--scale 2] [--med 7,5] FILES/GLOBS...
    without --apply only the QA sheet is written (look at it first);
    with --apply each original is copied to art_src/prepaper/<path relative to the repo> and the file is rewritten in
    place (webp lossless or png); art_src/prepaper/manifest.json records the md5 of every flattened file, so a re-run
    skips files already flat and flattens files a builder rewrote since (the cast builder's standing pass, paper_swap's
    atlas_clean rebuild): re-run it after those. --redo re-flattens from the backups (other settings), --exclude SUBSTR.
"""
import argparse
import glob
import hashlib
import json
import multiprocessing
import os
import shutil
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
BACKUP = os.path.join(ROOT, "art_src", "prepaper")
MANIFEST = os.path.join(BACKUP, "manifest.json")  # repo path -> md5 of the flattened file we wrote


def save_manifest(man: dict) -> None:
    os.makedirs(BACKUP, exist_ok=True)
    tmp = MANIFEST + ".tmp"
    json.dump(man, open(tmp, "w"), indent=0, sort_keys=True)
    os.replace(tmp, MANIFEST)


def md5(path: str) -> str:
    return hashlib.md5(open(path, "rb").read()).hexdigest()


def box_blur(x: np.ndarray, r: int) -> np.ndarray:
    """Box blur (2r+1) of a float array (H, W[, C]) with edge padding, via cumulative sums."""
    k = 2 * r + 1
    pad = [(r, r), (r, r)] + [(0, 0)] * (x.ndim - 2)
    p = np.pad(x, pad, mode="edge")
    c = np.cumsum(p, axis=0)
    c = np.concatenate([np.zeros_like(c[:1]), c], 0)
    p = (c[k:] - c[:-k])
    c = np.cumsum(p, axis=1)
    c = np.concatenate([np.zeros_like(c[:, :1]), c], 1)
    return (c[:, k:] - c[:, :-k]) / (k * k)


def fill_transparent(im: Image.Image) -> Image.Image:
    """RGB with every pixel under alpha < 128 replaced by a smooth spread of nearby opaque colour."""
    a = np.asarray(im.getchannel("A"), dtype=np.float32) / 255.0
    rgb = np.asarray(im.convert("RGB"), dtype=np.float32)
    w = (a > 0.5).astype(np.float32)
    acc = rgb * w[..., None]
    out = rgb.copy()
    known = w > 0
    radius = 2
    cur_rgb, cur_w = acc, w
    # grow outward a few times with increasing blur so pixels near the edge get the edge colour
    for _ in range(6):
        bl = box_blur(cur_rgb, radius)
        bw = box_blur(cur_w, radius)
        fill = bl / np.maximum(bw, 1e-6)[..., None]
        newly = (~known) & (bw > 1e-4)
        out[newly] = fill[newly]
        known = known | newly
        cur_w = known.astype(np.float32)
        cur_rgb = out * cur_w[..., None]
        radius *= 2
        if known.all():
            break
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGB")


def flatten(im: Image.Image, scale: int = 2, meds=(7, 5)) -> Image.Image:
    im = im.convert("RGBA")
    w, h = im.size
    rgb = fill_transparent(im)
    if scale != 1:
        rgb = rgb.resize((w * scale, h * scale), Image.LANCZOS)
    for m in meds:
        rgb = rgb.filter(ImageFilter.MedianFilter(m))
    if scale != 1:
        rgb = rgb.resize((w, h), Image.LANCZOS)
    out = rgb.convert("RGBA")
    out.putalpha(im.getchannel("A"))
    return out


def on_bg(im: Image.Image, bg=(236, 228, 212)) -> Image.Image:
    b = Image.new("RGBA", im.size, bg + (255,))
    b.alpha_composite(im)
    return b.convert("RGB")


def qa_sheet(pairs, out_path: str, crop_zoom: int = 3) -> None:
    """Rows: before | after | 1:1-zoomed centre crop before | after."""
    rows = []
    for path, a, b in pairs:
        A, B = on_bg(a), on_bg(b)
        cw, ch = min(160, A.width), min(160, A.height)
        x0, y0 = (A.width - cw) // 2, (A.height - ch) // 2
        za = A.crop((x0, y0, x0 + cw, y0 + ch)).resize((cw * crop_zoom, ch * crop_zoom), Image.NEAREST)
        zb = B.crop((x0, y0, x0 + cw, y0 + ch)).resize((cw * crop_zoom, ch * crop_zoom), Image.NEAREST)
        tgt_h = max(za.height, 300)
        ims = []
        for x in (A, B, za, zb):
            s = tgt_h / x.height
            ims.append(x.resize((max(1, int(x.width * s)), tgt_h), Image.LANCZOS))
        row = Image.new("RGB", (sum(i.width for i in ims) + 10 * 5, tgt_h + 24), (40, 40, 40))
        x = 10
        for i in ims:
            row.paste(i, (x, 20))
            x += i.width + 10
        ImageDraw.Draw(row).text((10, 4), os.path.relpath(path, ROOT) + "   before | after | centre crop x%d" % crop_zoom,
                                 fill=(255, 255, 255))
        rows.append(row)
    W = max(r.width for r in rows)
    sheet = Image.new("RGB", (W, sum(r.height for r in rows)), (40, 40, 40))
    y = 0
    for r in rows:
        sheet.paste(r, (0, y))
        y += r.height
    if sheet.width > 2400:
        s = 2400 / sheet.width
        sheet = sheet.resize((2400, int(sheet.height * s)), Image.LANCZOS)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    sheet.save(out_path, quality=88)


def save_like(im: Image.Image, path: str) -> None:
    tmp = path + ".tmp_flatten"
    if path.lower().endswith(".webp"):
        im.save(tmp, "WEBP", lossless=True, quality=100, method=4)
    else:
        im.save(tmp, "PNG")
    os.replace(tmp, path)


def _work(job):
    p, rel, bk, src, cur, apply_, scale, meds = job
    out = flatten(Image.open(src).convert("RGBA"), scale, meds)
    if src == p:
        if os.path.exists(bk) and md5(bk) != cur:
            shutil.move(bk, bk + ".prev")  # keep the older original too, never delete
        os.makedirs(os.path.dirname(bk), exist_ok=True)
        shutil.copy2(p, bk)
    save_like(out, p)
    return rel, md5(p)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--qa", default="")
    ap.add_argument("--qa-max", type=int, default=12, help="rows in the QA sheet")
    ap.add_argument("--scale", type=int, default=2)
    ap.add_argument("--med", default="7,5")
    ap.add_argument("--jobs", type=int, default=max(1, (os.cpu_count() or 2) - 2))
    ap.add_argument("--redo", action="store_true", help="flatten already-flattened files again from their backup")
    ap.add_argument("--exclude", action="append", default=[], help="substring; matching paths are skipped")
    a = ap.parse_args()
    meds = tuple(int(x) for x in a.med.split(",") if x)
    paths = []
    for f in a.files:
        hits = sorted(glob.glob(f)) if any(c in f for c in "*?[") else [f]
        paths += [os.path.abspath(p) for p in hits if p.lower().endswith((".webp", ".png"))]
    paths = [p for p in dict.fromkeys(paths) if not any(x in p for x in a.exclude)]
    if not paths:
        print("no files")
        return 1
    man = {}
    if os.path.exists(MANIFEST):
        man = json.load(open(MANIFEST))
    plan, n_skip = [], 0
    for p in paths:
        rel = os.path.relpath(p, ROOT)
        bk = os.path.join(BACKUP, rel)
        cur = md5(p)
        if man.get(rel) == cur and not a.redo:
            n_skip += 1  # already flattened (this exact file); --redo flattens again from the backup
            continue
        if os.path.exists(bk) and (man.get(rel) == cur or (rel not in man and md5(bk) != cur)):
            src = bk  # ours (or an interrupted run wrote it before the manifest did): start again from the original
        elif os.path.exists(bk) and md5(bk) == cur:
            src = bk
        else:
            src = p  # a new or rebuilt original (e.g. the cast builder rewrote it): it becomes the backup
        plan.append((p, rel, bk, src, cur, a.apply, a.scale, meds))
    pairs, n_done = [], 0
    for p, rel, bk, src, cur, *_ in plan[:a.qa_max]:
        if a.qa:
            im = Image.open(src).convert("RGBA")
            pairs.append((p, im, flatten(im, a.scale, meds)))
    if a.apply:
        with multiprocessing.Pool(a.jobs) as pool:
            for rel, new_md5 in pool.imap_unordered(_work, plan, chunksize=2):
                man[rel] = new_md5
                n_done += 1
                if n_done % 25 == 0:
                    save_manifest(man)
                    print("..", n_done, "/", len(plan), flush=True)
    if a.apply:
        save_manifest(man)
    if a.qa:
        qa_sheet(pairs, a.qa)
        print("QA", a.qa)
    print(("flattened %d" % n_done) if a.apply else ("previewed %d" % len(plan)), "files, already flat:", n_skip)
    return 0


if __name__ == "__main__":
    sys.exit(main())
