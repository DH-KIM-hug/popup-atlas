#!/usr/bin/env python3
"""Reusable M3.3 atlas chroma-key fringe, neon-green speckle & trapped magenta pocket cleaner.

Preserves exact image dimensions and alpha silhouettes for all bodies.json / stages.json cards
(RGB-only cleanup), while clearing trapped interior chroma-key magenta pockets on non-body props
and trees/foliage and rebuilding affected atlas_clean/ sheets cleanly.
"""
import argparse
import glob
import json
import os
import sys
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tools", "atlas"))
import slice_atlas as sa  # noqa: E402


def bleed_rgb(rgba: np.ndarray, iters: int = 5) -> np.ndarray:
    """Propagate opaque RGB into transparent pixels (alpha unchanged)."""
    out = rgba.copy()
    al = out[..., 3]
    known = al > 128
    col = out[..., :3] * known[..., None]
    for _ in range(iters):
        acc = np.zeros_like(col)
        cnt = np.zeros(al.shape, np.float32)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            acc += np.roll(np.roll(col, dy, 0), dx, 1)
            cnt += np.roll(np.roll(known, dy, 0), dx, 1)
        new = (~known) & (cnt > 0)
        if not new.any():
            break
        col[new] = acc[new] / cnt[new][:, None]
        known = known | new
    out[..., :3] = np.where((al > 128)[..., None], out[..., :3], col)
    return out


def clean_fringe_rgb(im: Image.Image, band: int = 6, iters: int = 14, min_m: int = 10, clean_green: bool = True, allow_blue_mag: bool = True, strict_pink_only: bool = False) -> Image.Image:
    """RGB-only edge cleanup: removes magenta chroma-key fringes (and optional neon-green despill
    speckles) within `band` px of alpha < 250 by filling from clean interior neighbors.
    Alpha channel and image dimensions are NEVER modified. Blue-violet (B > R + 15) is protected."""
    a = np.asarray(im.convert("RGBA")).astype(np.float32)
    al = a[..., 3]
    rgb = a[..., :3]
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    m = np.minimum(r, b) - g

    solid_arr = (al > 250).astype(np.uint8) * 255
    pad_b = band + 1
    solid_pad = Image.fromarray(np.pad(solid_arr, pad_b, constant_values=0))
    inner = (np.asarray(solid_pad.filter(ImageFilter.MinFilter(2 * band + 1)))[pad_b:-pad_b, pad_b:-pad_b]) > 0
    pad3 = 4
    solid_pad3 = Image.fromarray(np.pad(solid_arr, pad3, constant_values=0))
    inner3 = (np.asarray(solid_pad3.filter(ImageFilter.MinFilter(7)))[pad3:-pad3, pad3:-pad3]) > 0

    if strict_pink_only:
        hue_ok = ((r >= b - 15) & ((g < 95) | (m > 50))) | ((r > 155) & (b > 145) & (m > 46) & (np.abs(r - b) < 46))
    elif allow_blue_mag:
        hue_ok = (r >= b - 15) | ((np.abs(r - b) < 56) & (r > 110) & (b > 110))
    else:
        hue_ok = r >= b - 15
    mag_bad = (al > 0) & (~inner) & (m > min_m) & hue_ok
    if clean_green:
        grn_bad = (al > 0) & (~inner3) & ((g - np.maximum(r, b)) > 75) & (r < 55) & (b < 60)
        bad = mag_bad | grn_bad
    else:
        bad = mag_bad

    if not bad.any():
        return im

    good = (al > 200) & (~bad)
    col = rgb * good[..., None]
    w = good.astype(np.float32)
    for _ in range(iters):
        cs = np.zeros_like(col)
        ws = np.zeros_like(w)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dy == 0 and dx == 0:
                    continue
                cs += np.roll(np.roll(col, dy, 0), dx, 1)
                ws += np.roll(np.roll(w, dy, 0), dx, 1)
        fill = (w == 0) & (ws > 0)
        if not fill.any():
            break
        col[fill] = cs[fill] / ws[fill][:, None]
        w = np.where(fill, 1.0, w)

    out = rgb.copy()
    ok = bad & (w > 0)
    out[ok] = col[ok]
    left = bad & (~ok)
    if left.any():
        mm = np.clip(m[left], 0, None)[:, None]
        out[left] = out[left] - mm * np.array([1.0, 0.0, 1.0])
    rgba = np.dstack([np.clip(out, 0, 255), al]).astype(np.float32)
    rgba = bleed_rgb(rgba, iters=3)
    return Image.fromarray(np.clip(rgba, 0, 255).astype(np.uint8), "RGBA")


def clear_magenta_pockets(im: Image.Image, min_excess: int = 62, clear_alpha: bool = True, bleed_iters: int = 5, rim_excess: int = 35, fringe_band: int = 6) -> Image.Image:
    """Remove trapped chroma-key magenta/plum pockets inside a sprite (strictly R >= B - 20 and
    |R - B| < 95 and B > 80 so blue-violet & purple artwork is untouched).
    If clear_alpha=True: sets pocket pixels (plus 1px semi-magenta rim) alpha=0 and bleeds RGB.
    If clear_alpha=False: keeps alpha intact and inpaints RGB from clean neighbors (safe for bodies.json)."""
    a = np.asarray(im.convert("RGBA")).astype(np.float32)
    al = a[..., 3]
    rgb = a[..., :3]
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    m = np.minimum(r, b) - g
    pocket = (al > 0) & (m > min_excess) & (r >= b - 20) & (np.abs(r - b) < 95) & (b > 80)
    if not pocket.any():
        return im

    if clear_alpha:
        # Grow 1px into heavily magenta-tinted transition rim (m > rim_excess)
        pk_dil = np.asarray(Image.fromarray((pocket * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(3))) > 0
        rim = pk_dil & (al > 0) & (m > rim_excess) & (r >= b - 18)
        drop = pocket | rim
        al2 = al.copy()
        al2[drop] = 0.0
        rgba = np.dstack([rgb, al2]).astype(np.float32)
        rgba = bleed_rgb(rgba, iters=bleed_iters)
        out_im = Image.fromarray(np.clip(rgba, 0, 255).astype(np.uint8), "RGBA")
        return clean_fringe_rgb(out_im, band=fringe_band, iters=14, min_m=8)
    else:
        # RGB-only inpaint (preserves alpha 100%, safe for bodies.json windows)
        good = (al > 200) & (~pocket)
        col = rgb * good[..., None]
        w = good.astype(np.float32)
        for _ in range(18):
            cs = np.zeros_like(col)
            ws = np.zeros_like(w)
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    if dy == 0 and dx == 0:
                        continue
                    cs += np.roll(np.roll(col, dy, 0), dx, 1)
                    ws += np.roll(np.roll(w, dy, 0), dx, 1)
            fill = (w == 0) & (ws > 0)
            if not fill.any():
                break
            col[fill] = cs[fill] / ws[fill][:, None]
            w = np.where(fill, 1.0, w)
        out = rgb.copy()
        ok = pocket & (w > 0)
        out[ok] = col[ok]
        return Image.fromarray(np.dstack([np.clip(out, 0, 255), al]).astype(np.uint8), "RGBA")


def key_raw_sprites(path: str, min_area: int = 1500, merge_dist: int = 26, join_px: int = 5, pad: int = 4):
    """Key a magenta-background raw image into a list of (Image RGBA, bbox) sorted in reading order,
    avoiding fill_holes.py's floodfill bug and unmix_despill's neon-green boundary speckles."""
    im = Image.open(path).convert("RGB")
    rgb = np.asarray(im).astype(np.float32) / 255.0
    bg = sa.estimate_bg(rgb)
    a = sa.key(rgb, bg)
    a[a < 0.04] = 0.0
    solid = a > 0.5
    rgb_u, a, _ = sa.unmix_local(rgb, a, bg)
    a[a < 0.04] = 0.0

    # Gentle despill only (no bright neon green inversion!)
    edge = sa.dilate(a < 0.5, 3) & (a >= 0.02)
    r_, g_, b_ = rgb_u[..., 0], rgb_u[..., 1], rgb_u[..., 2]
    # Limit magenta spill without dropping R/B below G
    max_rb_to_g = np.maximum(g_, 0.0)
    spill = np.clip(np.minimum(r_, b_) - max_rb_to_g - 0.02, 0.0, None)
    fix = edge & (spill > 0) & (r_ > g_) & (b_ > g_) & (r_ >= b_ - 0.08)
    rgb2 = rgb_u.copy()
    rgb2[..., 0] = np.where(fix, np.maximum(g_, r_ - spill), r_)
    rgb2[..., 2] = np.where(fix, np.maximum(g_, b_ - spill), b_)

    lab, n = sa.label(sa.dilate(solid, join_px))
    lab = np.where(solid | (a > 0.04), lab, 0)
    comps = []
    for i in range(1, n + 1):
        m = lab == i
        area = int((m & solid).sum())
        if area < 30:
            continue
        comps.append({"ids": [i], "area": area, "box": sa.bbox(m), "main_box": sa.bbox(m)})
    comps.sort(key=lambda c: -c["area"])
    big = [c for c in comps if c["area"] >= min_area]
    small = [c for c in comps if c["area"] < min_area]
    for s in small:
        best, bd = None, 1e9
        for b in big:
            d = sa.box_dist(s["box"], b["box"])
            if d < bd:
                best, bd = b, d
        if best is not None and bd <= merge_dist and s["box"][3] <= best["main_box"][3] + 2:
            best["ids"] += s["ids"]
            best["area"] += s["area"]
            bb, sb = best["box"], s["box"]
            best["box"] = (min(bb[0], sb[0]), min(bb[1], sb[1]), max(bb[2], sb[2]), max(bb[3], sb[3]))

    big.sort(key=lambda c: (c["box"][1] + c["box"][3]) / 2)
    rows, cur = [], []
    for c in big:
        cy = (c["box"][1] + c["box"][3]) / 2
        if cur and cy - np.mean([(k["box"][1] + k["box"][3]) / 2 for k in cur]) > 60:
            rows.append(cur)
            cur = []
        cur.append(c)
    if cur:
        rows.append(cur)
    ordered = [c for row in rows for c in sorted(row, key=lambda c: c["box"][0])]

    out = []
    for c in ordered:
        x0, y0, x1, y1 = c["box"]
        x0, y0 = max(0, x0), max(0, y0)
        sub = np.isin(lab[y0:y1, x0:x1], c["ids"])
        alpha = np.where(sub, a[y0:y1, x0:x1], 0.0)
        col = rgb2[y0:y1, x0:x1]
        rgba = np.zeros((y1 - y0 + 2 * pad, x1 - x0 + 2 * pad, 4), np.float32)
        rgba[pad:-pad, pad:-pad, :3] = col
        rgba[pad:-pad, pad:-pad, 3] = alpha
        rgba = sa.bleed(rgba)
        im_out = Image.fromarray((np.clip(rgba, 0, 1) * 255 + 0.5).astype(np.uint8), "RGBA")
        im_out = clear_magenta_pockets(im_out, min_excess=58, clear_alpha=True)
        im_out = clean_fringe_rgb(im_out, band=6, iters=14, min_m=8)
        out.append((im_out, [int(x0), int(y0), int(x1), int(y1)]))
    return out


def load_protected_ids() -> set[str]:
    """All atlas card IDs belonging to bodies.json or any stages.json (alpha & dimensions immutable)."""
    prot = set()
    bp = os.path.join(ROOT, "game/art/atlas/bodies.json")
    if os.path.exists(bp):
        prot.update(json.load(open(bp)).keys())
    for sp in glob.glob(os.path.join(ROOT, "game/art/atlas/*/stages/stages.json")):
        d = json.load(open(sp))
        if isinstance(d, dict):
            prot.update(d.keys())
    return prot


def save_webp(im: Image.Image, path: str) -> None:
    tmp = path + ".tmp_clean.webp"
    im.save(tmp, "WEBP", lossless=True, quality=100, method=6)
    os.replace(tmp, path)


# Cards where dark/bright magenta is trapped inside genuine open background gaps (NOT solid purple/pink art)
OPEN_POCKET_CARDS = {
    "story_sm_cottage_03", "story_sm_cottage_07",
    "story_sm_field_00", "story_sm_field_01", "story_sm_field_02", "story_sm_field_03",
    "story_sm_field_04", "story_sm_field_05", "story_sm_field_06", "story_sm_field_07",
    "story_sm_mountain_05", "story_sm_mountain_07", "story_sm_mountain_08",
    "story_sm_paper_test_02",
    "story_sm_sky_04",
    "story_wg_hide_03", "story_wg_hide_04",
    "story_pj_field_00", "story_pj_field_01", "story_pj_field_02", "story_pj_field_03", "story_pj_field_07",
    "story_rp_room_06",
    "story_rp_garden_00", "story_rp_garden_01", "story_rp_garden_02", "story_rp_garden_03",
    "story_rp_garden_04", "story_rp_garden_05", "story_rp_garden_06", "story_rp_garden_07",
    "story_rp_garden_08", "story_rp_garden_09", "story_rp_garden_13", "story_rp_garden_15", "story_rp_garden_16",
    "story_tn_garden_02", "story_tn_garden_03",
    "story_tn_garden_04", "story_tn_garden_05", "story_tn_garden_06", "story_tn_garden_07",
    "story_tn_garden_08", "story_tn_garden_10", "story_tn_garden_11", "story_tn_garden_12",
    "story_tn_garden_13", "story_tn_garden_14", "story_tn_garden_16", "story_tn_garden_17",
    "story_tn_garden_10m", "story_tn_garden_11m", "story_tn_garden_12m",
    "story_veg_garden_01", "story_veg_garden_01m", "story_veg_garden_04", "story_veg_garden_04m",
    "story_veg_garden_05", "story_veg_garden_05m", "story_veg_garden_09",
    "story_tn_feast_03",
    "story_wg_room_12",
    "story_wc_ingredients_11",
    "story_bk_parts_00", "story_bk_parts_01", "story_bk_parts_02", "story_bk_parts_03",
    "story_bk_parts_04", "story_bk_parts_05", "story_bk_parts_06", "story_bk_parts_07",
    "story_bk_parts_08", "story_bk_parts_09", "story_bk_parts_10", "story_bk_parts_11",
    "story_bk_parts_12", "story_bk_parts_13", "story_bk_parts_14", "story_bk_parts_15",
    "story_bk_materials_00", "story_bk_materials_01", "story_bk_materials_02", "story_bk_materials_03",
    "story_bk_materials_04", "story_bk_materials_05", "story_bk_materials_06", "story_bk_materials_07",
    "story_bk_materials_08", "story_bk_materials_09", "story_bk_materials_10", "story_bk_materials_11",
    "story_bk_materials_12", "story_bk_materials_13",
    "meadow_field_11", "meadow_field_12", "meadow_field_18", "meadow_field_20", "meadow_field_28",
    "spring_blossom_02", "spring_blossom_03", "spring_blossom_04", "spring_blossom_07",
    "spring_blossom_09", "spring_blossom_10", "spring_blossom_13", "spring_blossom_15",
    "spring_blossom_16", "spring_blossom_19", "spring_blossom_20", "spring_blossom_21", "spring_blossom_23",
    "forest_broadleaf_16", "forest_broadleaf_22",
    "forest_conifer_10", "forest_conifer_11", "forest_conifer_15", "forest_conifer_16",
    "forest_conifer_24", "forest_conifer_25",
    "village_props_15", "village_props_16", "village_props_22", "village_props_31",
    "small_decor_12", "small_decor_13",
    "farm_animals_07", "farm_animals_10",
    "bushes_hedges_11", "bushes_hedges_12",
    "korean_village_19", "korean_village_20", "korean_village_21",
    "hills_clouds_08",
    "fairytale_west_14",
    "autumn_22", "autumn_26",
    "stream_water_00", "stream_water_01", "stream_water_02", "stream_water_04",
    "stream_water_06", "stream_water_13", "stream_water_17", "stream_water_29",
    "korean_nature_01", "korean_nature_02", "korean_nature_06", "korean_nature_07", "korean_nature_08", "korean_nature_09",
    "korean_nature_11", "korean_nature_12", "korean_nature_13", "korean_nature_18",
    "korean_nature_19", "korean_nature_20", "korean_nature_22",
}


def clean_all(dry: bool = False) -> None:
    prot = load_protected_ids()
    atlas_root = os.path.join(ROOT, "game/art/atlas")
    clean_root = os.path.join(ROOT, "game/art/atlas_clean")

    # 1. Clean game/art/atlas/**/*.webp (excl bodies/, stages/)
    changed_shared_sheets = set()
    n_fringe = 0
    n_pockets = 0
    for p in sorted(glob.glob(os.path.join(atlas_root, "**/*.webp"), recursive=True)):
        if "/bodies/" in p or "/stages/" in p:
            continue
        cid = os.path.splitext(os.path.basename(p))[0]
        sheet = os.path.basename(os.path.dirname(p))
        im = Image.open(p).convert("RGBA")
        out = im

        # Open pocket clearing only on verified non-protected cards
        if cid in OPEN_POCKET_CARDS and cid not in prot:
            rim_ex = 35
            fband = 6
            if cid in ("meadow_field_18", "village_props_22"):
                thr = 32
                rim_ex = 22
                fband = 8
            elif cid in (
                "story_wc_ingredients_11", "korean_nature_01", "korean_nature_02",
                "story_sm_mountain_08", "story_sm_field_03", "story_sm_field_04",
                "story_rp_room_06", "story_tn_garden_11", "story_tn_garden_12",
                "story_tn_garden_11m", "story_tn_garden_12m",
            ):
                thr = 42
            else:
                thr = 55
            out2 = clear_magenta_pockets(out, min_excess=thr, clear_alpha=True, rim_excess=rim_ex, fringe_band=fband)
            if out2 is not out:
                n_pockets += 1
                out = out2
        elif cid in prot:
            # RGB-only pocket despill for bodies.json houses with trapped window magenta (e.g. fairytale_west_05)
            out2 = clear_magenta_pockets(out, min_excess=62, clear_alpha=False)
            if out2 is not out:
                n_pockets += 1
                out = out2

        # Outer & hole fringe RGB-only cleanup
        if cid in ("meadow_field_18", "village_props_22"):
            # Inpaint remaining dark pink/magenta wood bleed without touching brown wood
            fa = np.asarray(out).astype(np.float32)
            fal, frgb = fa[..., 3], fa[..., :3]
            fr, fg, fb = frgb[..., 0], frgb[..., 1], frgb[..., 2]
            fpink = (fal > 0) & (fb > fg + 8) & (fr > fg + 12)
            if fpink.any():
                fgood = (fal > 200) & (~fpink)
                fcol = frgb * fgood[..., None]
                fw = fgood.astype(np.float32)
                for _ in range(14):
                    fcs = np.zeros_like(fcol)
                    fws = np.zeros_like(fw)
                    for dy in (-1, 0, 1):
                        for dx in (-1, 0, 1):
                            if dy == 0 and dx == 0:
                                continue
                            fcs += np.roll(np.roll(fcol, dy, 0), dx, 1)
                            fws += np.roll(np.roll(fw, dy, 0), dx, 1)
                    ffill = (fw == 0) & (fws > 0)
                    if not ffill.any():
                        break
                    fcol[ffill] = fcs[ffill] / fws[ffill][:, None]
                    fw = np.where(ffill, 1.0, fw)
                fout = frgb.copy()
                fok = fpink & (fw > 0)
                fout[fok] = fcol[fok]
                out = Image.fromarray(np.dstack([np.clip(fout, 0, 255), fal]).astype(np.uint8), "RGBA")

        if cid in ("story_tn_garden_00", "story_tn_garden_01", "story_tn_feast_03"):
            out2 = clean_fringe_rgb(out, band=6, iters=14, min_m=20, clean_green=True, allow_blue_mag=False, strict_pink_only=True)
        else:
            min_m = 14 if sheet.startswith("story_wc_") else 8
            allow_bm = not (sheet.startswith("story_wc_") or sheet == "story_rp_garden")
            out2 = clean_fringe_rgb(out, band=8 if cid in ("meadow_field_18", "village_props_22") else 6, iters=14, min_m=min_m, clean_green=True, allow_blue_mag=allow_bm)
        if np.any(np.asarray(out2) != np.asarray(im)):
            n_fringe += 1
            if not dry:
                save_webp(out2, p)
            if not os.path.exists(os.path.join(clean_root, sheet)):
                continue
            if not sheet.startswith("story_"):
                changed_shared_sheets.add(sheet)

    # 2. Also fix any remaining fringe/hole directly in atlas_clean/ for modified shared sheets + spring_blossom_24
    print(f"atlas/: cleaned={n_fringe} files (pockets={n_pockets}), modified shared sheets={sorted(changed_shared_sheets)}")
    if dry:
        return

    # Rebuild modified shared sheets in atlas_clean/ using strip_rim (never altering bodies.json clean_px!)
    sys.path.insert(0, os.path.join(ROOT, "tools", "art"))
    from strip_rim import strip_rim  # noqa: E402
    cat = json.load(open(os.path.join(atlas_root, "catalog.json")))
    bodies = json.load(open(os.path.join(atlas_root, "bodies.json")))
    rebuilt = 0
    for it in cat:
        sh = it.get("sheet", "")
        cid = it["id"]
        if sh not in changed_shared_sheets and cid != "spring_blossom_24":
            continue
        src = os.path.join(ROOT, "game", it["path"])
        dst = os.path.join(ROOT, "game", it["path"].replace("art/atlas/", "art/atlas_clean/"))
        if not os.path.exists(os.path.dirname(dst)):
            continue
        im = Image.open(src).convert("RGBA")
        out, _ = strip_rim(im)
        # Preserve exact bodies.json clean_px if this card is in bodies.json
        if cid in bodies and "clean_px" in bodies[cid]:
            expected = tuple(bodies[cid]["clean_px"])
            if out.size != expected:
                # Never alter clean_px for bodies.json cards: apply RGB-only clean_fringe to existing atlas_clean
                if os.path.exists(dst):
                    old_clean = Image.open(dst).convert("RGBA")
                    out = clean_fringe_rgb(old_clean, band=6, iters=14, min_m=8, clean_green=True)
                    # Also clear interior RGB pockets if any without altering alpha
                    out = clear_magenta_pockets(out, min_excess=62, clear_alpha=False)
                else:
                    out = out.resize(expected, Image.LANCZOS)
        out = clean_fringe_rgb(out, band=6, iters=14, min_m=8, clean_green=True)
        save_webp(out, dst)
        rebuilt += 1
    print(f"atlas_clean/: rebuilt/cleaned {rebuilt} files")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()
    clean_all(dry=args.dry)
