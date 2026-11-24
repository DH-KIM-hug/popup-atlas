#!/usr/bin/env python3
"""Re-skin a tale's shipped cast images from FELT to PAPER without rebuilding the cast (2026-11-22, felt -> paper).

  python3 tools/cast/paper_reskin.py <tale> [--only cast_x,cast_y] [--dry]

Every cast sheet of the tale was redrawn piece for piece as paper (tools/art/paper_jobs.py `castp_<sheet>` ->
art_src/cast/raw/<sheet>_paper.png; the felt raw is kept as <sheet>_felt.png). The shipped images (figures, padded
cycle frames, rig parts, peek figures ...) are 1:1 crops of the felt raws, cut / padded / trimmed by the cast tools,
so instead of re-running those tools (build_cast.py rewrites the whole catalog) each shipped image is located in its
felt raw (alpha + colour template match, mirrored too) and repainted from the paper raw WARPED INTO THE FELT RAW'S
FRAME (each paper piece scaled to its felt piece's height, bottom-centre aligned). Same canvas, same placement, same
catalog: nothing else changes.
- a whole figure takes the paper silhouette (within its canvas); a part (leg, body, hips) takes the paper pixels inside
  its own felt mask grown by 4 px, so the cut lines of the rig stay where they were;
- pixels a tool painted (torso fill under swinging arms, a recoloured mouth) differ from the felt raw: they are kept and
  counted (EDITED) — re-derive those variants from the paper art with their own tool afterwards (wc_mouth_v5.py);
- the felt original of every image is read from git (FELT_REV), so a re-skin can be redone after a better paper raw.
Writes art_src/cast/qa/<tale>_paper_reskin.png (felt | paper per image) and prints per-image IoU / edited counts.
"""
import atexit, json, os, shutil, subprocess, sys, tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools", "art"))
import importlib.util
_spec = importlib.util.spec_from_file_location("paper_swap", os.path.join(ROOT, "tools/art/paper_swap.py"))
paper_swap = importlib.util.module_from_spec(_spec)
_argv = sys.argv
sys.argv = ["paper_swap"]
_spec.loader.exec_module(paper_swap)
sys.argv = _argv
_spec2 = importlib.util.spec_from_file_location("paper_jobs", os.path.join(ROOT, "tools/art/paper_jobs.py"))
paper_jobs = importlib.util.module_from_spec(_spec2)
_spec2.loader.exec_module(paper_jobs)

RAW = "art_src/cast/raw"
RAWDIR = [RAW]  # atlas mode switches it to art_src/atlas/raw
BACK = "art_src/cast/felt_backup"

CAST_SHEETS = {
    **paper_jobs.CAST_SHEETS,
    "sunmoon": [
        "cast_sm_lineup", "cast_sm_boy_expr", "cast_sm_boy_walk", "cast_sm_boy_run",
        "cast_sm_girl_expr", "cast_sm_girl_walk", "cast_sm_girl_run", "cast_sm_kids_views",
        "cast_sm_mom_empty", "cast_sm_mom_expr", "cast_sm_mom_views", "cast_sm_mom_walk",
        "cast_sm_rich_expr", "cast_sm_sunmoon", "cast_sm_tiger_disguise",
        "cast_sm_tiger_expr_a", "cast_sm_tiger_expr_b", "cast_sm_tiger_rope",
        "cast_sm_tiger_sneak", "cast_sm_tiger_tree", "cast_sm_tiger_walk",
        "cast_sm_climb", "cast_sm_treetop",
    ],
}


def is_magenta_bg(col):
    """True for #FF00FF chroma-key background (hue 275..342 deg, balanced R/B, not blue-violet cloth)."""
    r, g, b = col[..., 0], col[..., 1], col[..., 2]
    mx = np.maximum(np.maximum(r, g), b)
    mn = np.minimum(np.minimum(r, g), b)
    ch = mx - mn
    sat = ch / np.maximum(mx, 1e-4)
    hue = np.zeros_like(mx)
    rm = (mx == r) & (ch > 0)
    bm_ = (mx == b) & (ch > 0) & ~rm
    hue[rm] = (60.0 * (g[rm] - b[rm]) / ch[rm]) % 360.0
    hue[bm_] = 60.0 * (r[bm_] - g[bm_]) / ch[bm_] + 240.0
    return (hue >= 275.0) & (hue <= 342.0) & (sat > 0.24) & ((np.minimum(r, b) - g) > 0.14) & ((b - r) < 0.18)


def bg_alpha(rgb):
    col = rgb.astype(np.float32) / 255.0
    r, g, b = rgb[..., 0].astype(int), rgb[..., 1].astype(int), rgb[..., 2].astype(int)
    m = np.minimum(r, b) - g
    return ~(((m > 70) & (r > 140) & (b > 140)) | is_magenta_bg(col))


def safe_fill_holes(raw_p, sdir, tol=0.30):
    """In-process replacement for fill_holes.py with .copy() before floodfill and magenta bg exclusion."""
    raw = np.asarray(Image.open(raw_p).convert("RGB")).astype(np.float32) / 255.0
    b = np.concatenate([raw[:6].reshape(-1, 3), raw[-6:].reshape(-1, 3), raw[:, :6].reshape(-1, 3), raw[:, -6:].reshape(-1, 3)])
    bg = np.median(b, axis=0)
    meta = json.load(open(os.path.join(sdir, "_slices.json")))
    for m in meta["sprites"]:
        p = os.path.join(sdir, m["id"] + ".webp")
        if not os.path.exists(p):
            continue
        im = np.array(Image.open(p).convert("RGBA"))
        x0, y0 = int(m["bbox"][0]) - 4, int(m["bbox"][1]) - 4
        clear = im[..., 3] < 128
        mk = Image.fromarray(np.pad(clear, 1, constant_values=True).astype(np.uint8) * 255).copy()
        ImageDraw.floodfill(mk, (0, 0), 128)
        hole = (np.asarray(mk)[1:-1, 1:-1] == 255)
        ys, xs = np.where(hole)
        ry, rx = ys + y0, xs + x0
        ok = (ry >= 0) & (ry < raw.shape[0]) & (rx >= 0) & (rx < raw.shape[1])
        ys, xs, ry, rx = ys[ok], xs[ok], ry[ok], rx[ok]
        col = raw[ry, rx]
        far = (np.sqrt(((col - bg) ** 2).sum(-1)) > tol) & ~is_magenta_bg(col)
        im[ys[far], xs[far], :3] = (col[far] * 255).astype(np.uint8)
        im[ys[far], xs[far], 3] = 255
        fixed = int(far.sum())
        op = Image.fromarray(((im[..., 3] > 100) * 255).astype(np.uint8))
        inner = np.asarray(op.filter(ImageFilter.MinFilter(7))) > 0
        ys, xs = np.where(inner)
        ry, rx = ys + y0, xs + x0
        ok = (ry >= 0) & (ry < raw.shape[0]) & (rx >= 0) & (rx < raw.shape[1])
        ys, xs, ry, rx = ys[ok], xs[ok], ry[ok], rx[ok]
        col = raw[ry, rx]
        cur = im[ys, xs, :3].astype(np.float32) / 255.0
        chg = ((np.abs(col - cur).max(-1) > 0.04) | (im[ys, xs, 3] < 255)) & (np.sqrt(((col - bg) ** 2).sum(-1)) > tol) & ~is_magenta_bg(col)
        im[ys[chg], xs[chg], :3] = (col[chg] * 255).astype(np.uint8)
        im[ys[chg], xs[chg], 3] = 255
        fixed += int(chg.sum())
        if fixed:
            Image.fromarray(im).save(p, "WEBP", lossless=True, quality=100, method=6)


def slice_pieces(path, tmpdir):
    name = os.path.basename(path)[:-4]
    subprocess.run([sys.executable, "tools/atlas/slice_atlas.py", path, "--out", tmpdir, "--join", "5"], check=True,
                   stdout=subprocess.DEVNULL)
    safe_fill_holes(path, f"{tmpdir}/{name}")
    meta = json.load(open(f"{tmpdir}/{name}/_slices.json"))["sprites"]
    out = []
    for m in meta:
        p = f"{tmpdir}/{name}/{m['id']}.webp"
        if os.path.exists(p):
            out.append((Image.open(p).convert("RGBA"), (m["bbox"][0] - 4, m["bbox"][1] - 4)))
    return out


def bleed_rgba(arr, iters=4):
    """Push clean opaque RGB outward into transparent pixels (alpha stays 0) without edge wraparound."""
    out = arr.astype(np.float32).copy()
    a = out[..., 3]
    known = a > 127
    col = out[..., :3] * known[..., None]
    for _ in range(iters):
        pcol = np.pad(col, ((1, 1), (1, 1), (0, 0)))
        pk = np.pad(known.astype(np.float32), ((1, 1), (1, 1)))
        acc = (pcol[2:, 1:-1] + pcol[:-2, 1:-1] + pcol[1:-1, 2:] + pcol[1:-1, :-2])
        cnt = (pk[2:, 1:-1] + pk[:-2, 1:-1] + pk[1:-1, 2:] + pk[1:-1, :-2])
        new = (~known) & (cnt > 0)
        col[new] = acc[new] / cnt[new][:, None]
        known = known | new
    out[..., :3] = np.where((a > 127)[..., None], out[..., :3], col)
    return np.clip(out, 0, 255).astype(np.uint8)


def _hsv_hue(r, g, b):
    mx = np.maximum(np.maximum(r, g), b)
    mn = np.minimum(np.minimum(r, g), b)
    ch = mx - mn
    sat = ch / np.maximum(mx, 1e-4)
    hue = np.zeros_like(mx)
    rm = (mx == r) & (ch > 0)
    gm = (mx == g) & (ch > 0) & ~rm
    bm_ = (mx == b) & (ch > 0) & ~rm & ~gm
    hue[rm] = (60.0 * (g[rm] - b[rm]) / ch[rm]) % 360.0
    hue[gm] = 60.0 * (b[gm] - r[gm]) / ch[gm] + 120.0
    hue[bm_] = 60.0 * (r[bm_] - g[bm_]) / ch[bm_] + 240.0
    return hue, sat, mx


def _min_filter(mask_bool, k):
    pad = k // 2
    p = np.pad(mask_bool.astype(np.uint8) * 255, pad, constant_values=0)
    return np.asarray(Image.fromarray(p).filter(ImageFilter.MinFilter(k)))[pad:-pad, pad:-pad] > 0


def _max_filter(mask_bool, k):
    pad = k // 2
    p = np.pad(mask_bool.astype(np.uint8) * 255, pad, constant_values=0)
    return np.asarray(Image.fromarray(p).filter(ImageFilter.MaxFilter(k)))[pad:-pad, pad:-pad] > 0


def _dense_mask(mask_bool, min_count=55, radius=14):
    """Fast O(HW) 2D-cumsum density filter: keeps pixels with >= min_count mask pixels in local window."""
    if int(mask_bool.sum()) < min_count:
        return np.zeros_like(mask_bool)
    p = np.pad(mask_bool.astype(np.int32), ((radius + 1, radius), (radius + 1, radius)), constant_values=0)
    cs = p.cumsum(axis=0).cumsum(axis=1)
    win = 2 * radius + 1
    cnt = cs[win:, win:] - cs[:-win, win:] - cs[win:, :-win] + cs[:-win, :-win]
    return mask_bool & (cnt >= min_count)


def clean_cast_rim(im, strip_sticker=False):
    """Hue-aware cleanup of chroma-key magenta/dark-plum/dark-crimson rims, trapped chroma pockets,
    unmix_despill neon-green speckles, and (optionally) baked white/cream sticker halos bordering dark
    interiors, preserving exact (W, H), blue-violet cloth, and genuine rose/purple/maroon interiors."""
    arr = np.asarray(im.convert("RGBA")).copy()
    r = arr[..., 0].astype(np.float32)
    g = arr[..., 1].astype(np.float32)
    b = arr[..., 2].astype(np.float32)
    hue, sat, _ = _hsv_hue(r / 255.0, g / 255.0, b / 255.0)
    mag_ex = np.minimum(r, b) - g
    b_minus_r = b - r

    op0 = arr[..., 3] > 127
    inner2_0 = _min_filter(op0, 5)
    inner3_0 = _min_filter(op0, 7)
    violet_in0 = inner3_0 & (b > r + 25.0) & (mag_ex > 15.0)
    near_violet0 = _max_filter(violet_in0, 11)
    coral_in0 = inner3_0 & (r > b + 30.0) & (g > b - 5.0) & (r > g + 30.0) & (g < 140.0) & (b < 100.0)
    near_coral0 = _max_filter(coral_in0, 7)
    red_in0 = inner3_0 & (r >= 175.0) & (g < 90.0) & (b < 90.0) & (b < g + 12.0) & ((r - g) > 90.0)
    near_red0 = _max_filter(red_in0, 11)

    # 0. Open enclosed pure #FF00FF / warm-pink chroma-key background pockets (basket handles, armpits, coat gaps)
    pure_ck_def = (hue >= 285.0) & (hue <= 350.0) & (b_minus_r < 25.0) & (mag_ex > 62.0) & (sat > 0.75) & (g < 45.0)
    warm_pink_ck_def = (
        (hue >= 305.0) & (hue <= 354.0) & (r > g + 55.0) & (b > g + 20.0)
        & (
            ((r >= 234.0) & (b >= 145.0) & (sat >= 0.34))
            | ((g < 60.0) & (b > g + 45.0) & (r > 200.0) & (r > b + 50.0) & (sat > 0.55))
            | ((g < 45.0) & (b > g + 25.0) & (r > 175.0) & (r < b + 95.0) & (sat > 0.65))
        )
    )
    purple_cloth0_raw = (
        inner2_0 & (hue >= 250.0) & (hue <= 346.0) & ~pure_ck_def & ~warm_pink_ck_def
        & (
            ((sat <= 0.76) & (g >= 30.0) & (b >= 70.0) & (r <= 233.0))
            | ((sat <= 0.38) & (g >= 120.0) & (b >= 140.0))
        )
    )
    purple_cloth0 = _dense_mask(purple_cloth0_raw, min_count=55, radius=14)
    near_purple0 = _max_filter(purple_cloth0, 9)

    is_pure_ck = op0 & pure_ck_def & ~near_violet0
    is_pink_ck = op0 & warm_pink_ck_def & ~near_violet0 & ~near_purple0 & ~(near_red0 & (b < g + 20.0))
    opened0 = is_pure_ck | is_pink_ck
    if opened0.any():
        arr[opened0, 3] = 0

    # 1. Iterative outer-ring peel of true chroma-key magenta pixels & opened-pocket AA haloes (zero-padded)
    near_opened0 = _max_filter(opened0, 9) if opened0.any() else np.zeros_like(op0)
    thick_body0 = _max_filter(_min_filter(arr[..., 3] > 127, 7), 5)
    fuzz_pink_rim = (
        (hue >= 335.0) & (hue <= 354.0) & (r >= 172.0) & (b >= g + 13.0)
        & (r > g + 40.0) & (sat >= 0.22) & (g >= 42.0) & ~near_violet0 & ~near_purple0
    )
    pocket_halo = (
        near_opened0
        & (
            ((hue >= 295.0) & (hue <= 355.0) & (sat > 0.25) & (r > g + 25.0) & (b > g + 12.0))
            | (~thick_body0 & (hue >= 315.0) & (hue <= 358.0) & (sat > 0.30) & (r > g + 35.0) & (b > g + 10.0))
        )
        & ~near_violet0 & ~near_purple0
        & ~(near_coral0 & (b < g + 15.0)) & ~(near_red0 & (b < g + 15.0))
    )
    is_hue_mag = (hue >= 275.0) & (hue <= 346.0) & (b_minus_r < 45.0)
    strong_mag = (
        is_hue_mag
        & (mag_ex > 26.0)
        & (r > 80.0)
        & ((b > 80.0) | ((mag_ex > 35.0) & (b > 48.0)))
        & (sat > 0.20)
        & ~near_violet0
        & ~near_purple0
    )
    for _ in range(20):
        op = arr[..., 3] > 127
        if not op.any():
            break
        ring1 = op & ~_min_filter(op, 3)
        drop = ring1 & (strong_mag | pocket_halo | (fuzz_pink_rim & ~thick_body0) | (near_opened0 & fuzz_pink_rim))
        if not drop.any():
            break
        arr[drop, 3] = 0
    # Semi-transparent magenta fringe drops cleanly
    semi = (arr[..., 3] > 0) & (arr[..., 3] <= 127)
    arr[semi & ((is_hue_mag & (mag_ex > 16.0)) | pocket_halo | fuzz_pink_rim) & ~near_purple0 & ~near_violet0 & ~(near_red0 & (b < g + 15.0)), 3] = 0

    # 2. Optional baked white/cream sticker halo strip (wolf, traveller, tiger) bordering dark interior
    if strip_sticker:
        for _ in range(4):
            op = arr[..., 3] > 127
            if not op.any():
                break
            inner1 = _min_filter(op, 3)
            inner2 = _min_filter(op, 5)
            inner3 = _min_filter(op, 7)
            ring1 = op & ~inner1
            rr = arr[..., 0].astype(np.float32)
            gg = arr[..., 1].astype(np.float32)
            bb = arr[..., 2].astype(np.float32)
            lum = 0.299 * rr + 0.587 * gg + 0.114 * bb
            mxx = np.maximum(np.maximum(rr, gg), bb)
            mnn = np.minimum(np.minimum(rr, gg), bb)
            ssat = np.where(mxx > 0, (mxx - mnn) * 255.0 / np.maximum(mxx, 1.0), 0.0)
            bright = (rr >= 198) & (gg >= 188) & (bb >= 175) & (lum >= 198) & (ssat <= 62)
            near_dark = _max_filter((lum < 165.0) & inner3, 9)
            near_bright_in = _max_filter((lum >= 185.0) & (ssat <= 65.0) & inner2, 7)
            drop_st = ring1 & bright & near_dark & ~near_bright_in
            if not drop_st.any():
                break
            arr[drop_st, 3] = 0
        # Also drop semi-transparent bright sticker fringe bordering dark interior
        op = arr[..., 3] > 127
        inner3 = _min_filter(op, 7)
        inner2 = _min_filter(op, 5)
        rr = arr[..., 0].astype(np.float32); gg = arr[..., 1].astype(np.float32); bb = arr[..., 2].astype(np.float32)
        lum = 0.299 * rr + 0.587 * gg + 0.114 * bb
        mxx = np.maximum(np.maximum(rr, gg), bb); mnn = np.minimum(np.minimum(rr, gg), bb)
        ssat = np.where(mxx > 0, (mxx - mnn) * 255.0 / np.maximum(mxx, 1.0), 0.0)
        near_dark = _max_filter((lum < 165.0) & inner3, 9)
        near_bright_in = _max_filter((lum >= 185.0) & (ssat <= 65.0) & inner2, 7)
        semi_st = (arr[..., 3] > 0) & (arr[..., 3] <= 127) & (lum >= 198) & (ssat <= 62) & near_dark & ~near_bright_in
        arr[semi_st, 3] = 0

    # 3. Clean remaining soft magenta & dark-plum/dark-crimson chroma fringe + neon-green speckles via interior fill
    op = arr[..., 3] > 127
    inner2 = _min_filter(op, 5)
    inner3 = _min_filter(op, 7)
    inner4 = _min_filter(op, 9)
    inner6 = _min_filter(op, 13)
    band4 = (arr[..., 3] > 0) & ~inner4
    band6 = (arr[..., 3] > 0) & ~inner6
    rr = arr[..., 0].astype(np.float32); gg = arr[..., 1].astype(np.float32); bb = arr[..., 2].astype(np.float32)
    hue2, sat2, _ = _hsv_hue(rr / 255.0, gg / 255.0, bb / 255.0)
    mag_ex2 = np.minimum(rr, bb) - gg
    violet_in = inner3 & (bb > rr + 12.0) & (mag_ex2 > 15.0)
    near_violet_in = _max_filter(violet_in, 11)
    coral_in = inner3 & (rr > bb + 35.0) & (gg < 140.0) & (bb < 100.0)
    near_coral_in = _max_filter(coral_in, 9)
    purple_in_raw = (
        inner2 & (hue2 >= 250.0) & (hue2 <= 346.0)
        & (
            ((sat2 <= 0.76) & (gg >= 30.0) & (bb >= 70.0) & (rr <= 233.0))
            | ((sat2 <= 0.38) & (gg >= 120.0) & (bb >= 140.0))
        )
    )
    purple_in = _dense_mask(purple_in_raw, min_count=55, radius=14)
    near_purple_in = _max_filter(purple_in, 13)

    dark_plum_raw = (
        (hue2 >= 280.0)
        & (hue2 <= 346.0)
        & (sat2 > 0.40)
        & (bb > gg + 10.0)
        & (rr > gg + 24.0)
        & ((bb - rr) < 45.0)
    )
    plum_in = inner3 & dark_plum_raw
    if int(plum_in.sum()) < 40:
        near_plum_in = np.zeros_like(inner3)
    else:
        near_plum_in = _max_filter(plum_in, 11)
    dark_plum = dark_plum_raw & ~near_plum_in & ~near_violet_in & ~near_purple_in

    red_cloth_in = inner2 & ((hue2 >= 338.0) | (hue2 <= 12.0)) & (rr >= 175.0) & (rr > gg + 65.0) & (gg < 60.0) & (bb < 85.0) & (bb < gg + 12.0)
    near_red_in = np.zeros_like(inner2) if int(red_cloth_in.sum()) < 15 else _max_filter(red_cloth_in, 7)
    dark_rb_in = (
        inner2 & (gg >= 18.0) & (gg < 62.0) & (rr < 175.0) & ((rr - gg) > 35.0)
        & (gg >= bb - 3.0) & (gg <= bb + 14.0) & ((hue2 >= 340.0) | (hue2 <= 16.0))
    )
    near_dark_rb = _max_filter(dark_rb_in, 11) if int(dark_rb_in.sum()) >= 12 else np.zeros_like(inner2)

    dark_crimson_purp_raw = (
        (hue2 >= 335.0) & (hue2 <= 355.0) & (bb >= gg + 16.0)
        & (sat2 > 0.50) & (gg < 56.0) & (rr > gg + 42.0) & (rr < 195.0)
    )
    dark_crimson_neut_raw = (
        ((hue2 >= 335.0) | ((hue2 <= 8.5) & ((gg - bb) <= 13.0))) & (bb < gg + 16.0)
        & (sat2 > 0.50) & (gg < 56.0) & (rr > gg + 42.0) & (rr < 195.0)
    )
    crim_in = _dense_mask(inner4 & (dark_crimson_purp_raw | dark_crimson_neut_raw), min_count=75, radius=10)
    near_crim_in = _max_filter(crim_in, 13) if crim_in.any() else np.zeros_like(inner4)
    dark_crimson_purp = dark_crimson_purp_raw & ~near_crim_in & ~near_plum_in & ~near_violet_in & ~near_purple_in
    dark_crimson_neut = dark_crimson_neut_raw & ~near_crim_in & ~near_red_in & ~near_dark_rb & ~near_plum_in & ~near_violet_in & ~near_purple_in
    dark_crimson = dark_crimson_purp | dark_crimson_neut

    soft_mag = (
        ((hue2 >= 275.0) & (hue2 <= 346.0) & ((bb - rr) < 45.0) & (mag_ex2 > 10.0) & (rr > 55.0) & (bb > 55.0)
         & ~near_violet_in & ~near_purple_in & ~near_plum_in)
        | ((hue2 >= 268.0) & (hue2 <= 348.0) & ((bb - rr) < 40.0) & (mag_ex2 > 22.0) & (rr > 95.0) & (bb > 105.0)
           & ~near_violet_in & ~near_purple_in & ~near_plum_in & ~near_coral_in)
        | ((hue2 >= 310.0) & (hue2 <= 353.0) & (bb > gg + 25.0) & (rr > gg + 45.0) & (rr > 180.0)
           & ~near_violet_in & ~near_purple_in & ~near_plum_in & ~near_coral_in)
        | ((hue2 >= 335.0) & (hue2 <= 354.5) & (bb >= gg + 12.0) & (rr >= 172.0) & (rr > gg + 40.0) & (sat2 >= 0.22)
           & ~near_violet_in & ~near_purple_in & ~near_plum_in)
    )

    grn_ex = gg - np.maximum(rr, bb)
    is_grn_edge = (grn_ex > 22.0) & (gg > 75.0)
    green_in = inner3 & (grn_ex > 15.0) & (gg > 60.0)
    if int(green_in.sum()) < 25:
        near_green_in = np.zeros_like(inner3)
    else:
        near_green_in = _max_filter(green_in, 11)
    bad_grn = band4 & is_grn_edge & ~near_green_in
    # Also catch extreme neon-green unmix spikes even on green clothes (e.g. G-max(R,B) > 70 and min(R,B) < 30)
    neon_grn = band4 & (grn_ex > 65.0) & (np.minimum(rr, bb) < 35.0) & (gg > 120.0)
    bad = (band6 & (soft_mag | dark_plum)) | (band4 & dark_crimson) | bad_grn | neon_grn

    if bad.any():
        good = (arr[..., 3] > 200) & ~bad & ~soft_mag & ~dark_plum & ~dark_crimson & ~(is_grn_edge & ~near_green_in)
        col = arr[..., :3].astype(np.float32) * good[..., None]
        w = good.astype(np.float32)
        for _ in range(12):
            pcol = np.pad(col, ((1, 1), (1, 1), (0, 0)))
            pw = np.pad(w, ((1, 1), (1, 1)))
            cs = np.zeros_like(col); ws = np.zeros_like(w)
            H, W = w.shape
            for dy in (0, 1, 2):
                for dx in (0, 1, 2):
                    cs += pcol[dy:dy + H, dx:dx + W]
                    ws += pw[dy:dy + H, dx:dx + W]
            fill = (w == 0) & (ws > 0)
            col[fill] = cs[fill] / ws[fill][:, None]
            w = np.where(fill, 1.0, w)
        ok = bad & (w > 0)
        arr[..., :3][ok] = np.clip(col[ok], 0, 255).astype(np.uint8)
        left = bad & ~ok
        if (left & dark_crimson).any():
            arr[left & dark_crimson, 3] = 0
        if (left & ~dark_crimson & (soft_mag | dark_plum)).any():
            m_left = left & ~dark_crimson & (soft_mag | dark_plum)
            mm = np.clip(mag_ex2[m_left], 0, None)[:, None]
            arr[..., :3][m_left] = np.clip(arr[..., :3][m_left].astype(np.float32) - mm * np.array([1.0, 0.0, 1.0]), 0, 255).astype(np.uint8)

    # 4. Bleed clean RGB into transparent margin
    arr = bleed_rgba(arr, iters=4)
    return Image.fromarray(np.ascontiguousarray(arr), "RGBA")


def build_warped(sheet):
    """the paper raw warped into the felt raw's frame: RGBA canvas of the felt raw size"""
    RAW = RAWDIR[0]
    felt = f"{RAW}/{sheet}_felt.png"
    if not os.path.exists(felt):
        shutil.copy2(f"{RAW}/{sheet}.png", felt)
    paper = f"{RAW}/{sheet}_paper.png"
    tmp = tempfile.mkdtemp(prefix="reskin_")
    os.makedirs(f"{tmp}/f"); os.makedirs(f"{tmp}/p")
    shutil.copy2(felt, f"{tmp}/f/{sheet}.png")
    shutil.copy2(paper, f"{tmp}/p/{sheet}.png")
    cache = f"artifacts/paper/warp_cache/{RAW.split('/')[1]}_{sheet}.webp"  # git-ignored
    if os.path.exists(cache) and os.path.getmtime(cache) > os.path.getmtime(paper):
        shutil.rmtree(tmp, ignore_errors=True)
        return (np.asarray(Image.open(felt).convert("RGB")), np.asarray(Image.open(cache).convert("RGBA")),
                ["  (cached warp)"])
    fp = None
    for d in ("art_src/cast/slices", "art_src/cast/sliced"):  # the felt slicing the cast tools already made
        mp = f"{d}/{sheet}/_slices.json"
        if RAW.endswith("cast/raw") and os.path.exists(mp):
            fp = []
            for m in json.load(open(mp))["sprites"]:
                q = f"{d}/{sheet}/{m['id']}.webp"
                if os.path.exists(q):
                    fp.append((Image.open(q).convert("RGBA"), (m["bbox"][0] - 4, m["bbox"][1] - 4)))
            break
    if not fp:
        fp = slice_pieces(f"{tmp}/f/{sheet}.png", f"{tmp}/f")
    pp = slice_pieces(f"{tmp}/p/{sheet}.png", f"{tmp}/p")
    FW, FH = Image.open(felt).size
    PW, PH = Image.open(paper).size

    def box(im, xy):
        a = np.asarray(im)[..., 3] > 128
        ys, xs = np.nonzero(a)
        return (xy[0] + xs.min(), xy[1] + ys.min(), xy[0] + xs.max() + 1, xy[1] + ys.max() + 1)
    fb = [box(*p) for p in fp]
    pb = [box(*p) for p in pp]
    report = []
    amap, lost, acost = paper_swap.assign2([p[0] for p in fp], [paper_swap.norm(b, FW, FH) for b in fb],
                                           [p[0] for p in pp], [paper_swap.norm(b, PW, PH) for b in pb])
    for i, c in acost.items():
        if c > 0.75:
            report.append(f"  {sheet}: felt piece {i} matched with high cost {c:.2f} (check the QA sheet)")
    canvas = Image.new("RGBA", (FW, FH), (0, 0, 0, 0))
    for i, js in amap.items():
        if not js:
            report.append(f"  {sheet}: felt piece {i} has no paper piece")
            continue
        im, _ = paper_swap.composite([pp[j] for j in js])
        im = paper_swap.clean_fringe(im)
        x0 = min(pp[j][1][0] for j in js); y0 = min(pp[j][1][1] for j in js)
        nb = box(im, (x0, y0))
        ob = fb[i]
        s = (ob[3] - ob[1]) / max(1, nb[3] - nb[1])
        if abs(np.log(((ob[2] - ob[0]) / max(1, nb[2] - nb[0])) / s)) > 0.2:
            report.append(f"  {sheet}: piece {i} width ratio off ({(ob[2]-ob[0])}/{(nb[2]-nb[0])} vs height scale {s:.2f})")
        w2, h2 = max(1, round(im.width * s)), max(1, round(im.height * s))
        ims = im.resize((w2, h2), Image.LANCZOS)
        a = np.asarray(ims)[..., 3]
        ys, xs = np.nonzero(a > 128)
        # bottom-centre: alpha bbox bottom to the felt bottom, alpha centre x to the felt centre x
        cxn = (xs.min() + xs.max() + 1) / 2
        px = round((ob[0] + ob[2]) / 2 - cxn)
        py = round(ob[3] - (ys.max() + 1))
        canvas.alpha_composite(ims, (max(0, px), max(0, py)), (max(0, -px), max(0, -py)))
    for j in lost:
        report.append(f"  {sheet}: paper piece {j} unused")
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(os.path.dirname(cache), exist_ok=True)
    canvas.save(cache, "WEBP", lossless=True, quality=100, method=4)
    return np.asarray(Image.open(felt).convert("RGB")), np.asarray(canvas), report


def match(D, felt_rgb, felt_al_small, S=4):
    """locate D (RGBA array) in the felt raw. -> (x, y, flipped, mean colour error) or None"""
    best = None
    da = D[..., 3] > 128
    if da.sum() < 50:
        return None
    F = felt_al_small  # the felt raw, RGB 0..1 at 1/S scale
    H, W = F.shape[:2]
    fsq = np.fft.rfft2((F ** 2).sum(-1))
    fch = [np.fft.rfft2(F[..., c]) for c in range(3)]
    for flip in (False, True):
        Dd = D[:, ::-1] if flip else D
        sm = np.asarray(Image.fromarray(np.ascontiguousarray(Dd)).resize(
            (max(1, Dd.shape[1] // S), max(1, Dd.shape[0] // S)), Image.BOX)).astype(np.float32) / 255.0
        M = (sm[..., 3] > 0.95).astype(np.float32)
        T = sm[..., :3]
        h, w = M.shape
        if h > H or w > W or M.sum() < 4:
            continue
        # masked SSD at every offset via FFT: sum M F^2 - 2 sum M F T + sum M T^2
        cm = np.fft.irfft2(fsq * np.fft.rfft2(M[::-1, ::-1], s=(H, W)), s=(H, W))
        cft = sum(np.fft.irfft2(fch[c] * np.fft.rfft2((M * T[..., c])[::-1, ::-1], s=(H, W)), s=(H, W))
                  for c in range(3))
        ssd = (cm - 2 * cft)[h - 1:, w - 1:] + (M[..., None] * T ** 2).sum()
        valid = -ssd / M.sum()
        cand = np.argsort(valid.ravel())[-6:]
        # refine on a sub-grid with the colour error (interior pixels)
        inner = np.asarray(Image.fromarray(((Dd[..., 3] > 250) * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(5))) > 0
        if inner.sum() < 30:
            inner = Dd[..., 3] > 200
        ys, xs = np.nonzero(inner)
        if len(ys) > 3000:
            k = np.random.default_rng(0).choice(len(ys), 3000, replace=False)
            ys, xs = ys[k], xs[k]
        for c in cand:
            yy, xx = np.unravel_index(c, valid.shape)
            for dy in range(-S - 1, S + 2):
                for dx in range(-S - 1, S + 2):
                    x, y = xx * S + dx, yy * S + dy
                    if x < 0 or y < 0 or y + Dd.shape[0] > felt_rgb.shape[0] or x + Dd.shape[1] > felt_rgb.shape[1]:
                        continue
                    e = np.abs(felt_rgb[y + ys, x + xs].astype(int) - Dd[ys, xs, :3].astype(int)).mean()
                    if best is None or e < best[3]:
                        best = (x, y, flip, e)
    return best


def reskin_image(path, sheets_data, order):
    D = np.asarray(Image.open(path).convert("RGBA"))
    found = None
    for sh in order:
        frgb, warped, fal = sheets_data[sh]
        m = match(D, frgb, fal)
        if m and (found is None or m[3] < found[1][3]):
            found = (sh, m)
        if found and found[1][3] < 6:
            break
    if found is None or found[1][3] > 14:
        return None, found
    sh, (x, y, flip, err) = found
    frgb, warped, _ = sheets_data[sh]
    Dd = D[:, ::-1] if flip else D
    h, w = Dd.shape[:2]
    Fc = frgb[y:y + h, x:x + w].astype(int)
    Wc = warped[y:y + h, x:x + w].astype(np.float32)
    da = Dd[..., 3]
    inner = np.asarray(Image.fromarray(((da > 250) * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(5))) > 0
    # a tool may have recoloured the crop (front_legs.py colour-matches leg cards to the body): fit D = a * felt + b per
    # channel on the interior and give the paper the same recolour
    gain = np.ones(3, np.float32)
    off = np.zeros(3, np.float32)
    if err > 3 and inner.sum() > 200:
        d0 = np.abs(Fc - Dd[..., :3].astype(int)).max(-1)
        ok = inner & (d0 < 90)
        for c in range(3):
            fx = Fc[..., c][ok].astype(np.float32)
            dy = Dd[..., c][ok].astype(np.float32)
            if fx.std() > 4:
                a_ = float(np.clip(np.cov(fx, dy)[0, 1] / fx.var(), 0.6, 1.6))
                gain[c], off[c] = a_, float(dy.mean() - a_ * fx.mean())
            else:
                off[c] = float(dy.mean() - fx.mean())
    Fcc = Fc * gain + off
    diff = np.abs(Fcc - Dd[..., :3].astype(np.float32)).max(-1)
    edited = inner & (diff > 70)
    # whole figure (its felt piece fills the canvas) or a part?
    fa = bg_alpha(frgb[y:y + h, x:x + w])
    part = (da > 128).sum() < 0.85 * fa.sum() and "--whole" not in sys.argv
    if part:
        region = np.asarray(Image.fromarray(((da > 8) * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(9))) / 255.0
    else:  # a whole figure takes the paper silhouette near it (not a neighbour's sliver in a padded cycle canvas)
        region = np.asarray(Image.fromarray(((da > 8) * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(31))) / 255.0
    out = Wc.copy()
    out[..., :3] = Wc[..., :3] * gain + off
    out[..., 3] = Wc[..., 3] * region
    if "--ignore-edited" not in sys.argv:
        out[edited] = Dd[edited].astype(np.float32)
    out = np.clip(out, 0, 255).astype(np.uint8)
    if flip:
        out = out[:, ::-1]
    na = out[..., 3] > 128
    oa = D[..., 3] > 128
    iou = (na & oa).sum() / max(1, (na | oa).sum())
    return Image.fromarray(np.ascontiguousarray(out), "RGBA"), (sh, err, int(edited.sum()), iou, part)


FELT_REV = "d03c0f7"  # the last commit before the felt -> paper conversion of the shared library and the tales
_TMP = None


def felt_original(path):
    """the felt version of a shipped image: from git at FELT_REV (the working copy may be paper already)"""
    global _TMP
    try:
        blob = subprocess.check_output(["git", "show", f"{FELT_REV}:{path}"], stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        return path
    if _TMP is None:
        _TMP = tempfile.mkdtemp(prefix="felt_orig_")
        atexit.register(shutil.rmtree, _TMP, True)
    out = os.path.join(_TMP, path.replace("/", "__"))
    open(out, "wb").write(blob)
    return out


def run(label, sheets, files, dry, backup_root, qa_path):
    """files: [(path, preferred sheet)]; every file is repainted from the warped paper raws"""
    data = {}
    for s in sheets:
        frgb, warped, rep = build_warped(s)
        fal_s = np.asarray(Image.fromarray(frgb).resize((frgb.shape[1] // 4, frgb.shape[0] // 4), Image.BOX)
                           ).astype(np.float32) / 255.0
        data[s] = (frgb, warped, fal_s)
        print(s, "warped", *rep, sep="\n" if rep else " ")
    seen, pairs, rows = set(), [], []
    for path, sh in files:
        if path in seen or not os.path.exists(path):
            continue
        seen.add(path)
        src = felt_original(path)   # always re-skin from the felt original (git, before the paper work)
        order = [sh] + [s for s in sheets if s != sh]
        im, info = reskin_image(src, data, order)
        if im is None:
            rows.append(f"NOMATCH {path} best={info}")
            continue
        sh2, err, ned, iou, part = info
        flag = (" LOWIOU" if iou < 0.88 else "") + (f" EDITED{ned}" if ned > 40 else "")
        rows.append(f"{os.path.basename(path)} <- {sh2} err {err:.1f} iou {iou:.2f}{' part' if part else ''}{flag}")
        pairs.append((os.path.basename(path).rsplit(".", 1)[0] + flag, Image.open(src).convert("RGBA"), im))
        if not dry:
            if path.endswith(".webp"):
                im.save(path, "WEBP", lossless=True, quality=100, method=6)
            else:
                im.save(path)
    print("\n".join(rows))
    print(label, "images", len(pairs), "nomatch", sum(r.startswith("NOMATCH") for r in rows),
          "lowiou", sum("LOWIOU" in r for r in rows), "edited", sum("EDITED" in r for r in rows))
    paper_swap.qa_sheet(pairs, qa_path, f"{label}: felt -> paper")
    return rows


def _expand_targets(args, only=None):
    import glob
    targets = []
    for a in args:
        if a == "all-cast":
            targets.extend(sorted(glob.glob("game/art/cast/cast_*.webp")))
        elif a == "all-rig":
            targets.extend(sorted(glob.glob("game/art/cast/rig/*.png")))
        elif a == "all":
            targets.extend(sorted(glob.glob("game/art/cast/cast_*.webp")))
            targets.extend(sorted(glob.glob("game/art/cast/rig/*.png")))
        elif any(c in a for c in "*?["):
            targets.extend(sorted(glob.glob(a)))
        elif os.path.exists(a):
            targets.append(a)
    out = []
    seen = set()
    for p in targets:
        if p in seen or not p.lower().endswith((".webp", ".png")):
            continue
        seen.add(p)
        bn = os.path.basename(p).rsplit(".", 1)[0]
        if only and bn not in only and not any(bn.startswith(o) for o in only):
            continue
        out.append(p)
    return out


def _save_same(im, path, method=6):
    tmp = path + f".tmp_reskin_{os.getpid()}"
    if path.lower().endswith(".webp"):
        im.save(tmp, "WEBP", lossless=True, quality=100, method=method)
    else:
        im.save(tmp, "PNG")
    os.replace(tmp, path)


def _clean_worker(args):
    p, strip_st, dry = args
    im = Image.open(p).convert("RGBA")
    out = clean_cast_rim(im, strip_sticker=strip_st)
    if not np.array_equal(np.asarray(im), np.asarray(out)):
        if not dry:
            _save_same(out, p, method=6)
        return 1
    return 0


def run_clean(args, only, dry):
    import multiprocessing
    sticker_prefixes = []
    if "--sticker-on" in args:
        idx = args.index("--sticker-on")
        sticker_prefixes = [s for s in args[idx + 1].split(",") if s]
        args = args[:idx] + args[idx + 2:]
    paths = _expand_targets(args, only)
    jobs = [(p, any(os.path.basename(p).startswith(pref) or (f"cast_{pref}" in os.path.basename(p)) for pref in sticker_prefixes), dry)
            for p in paths]
    changed = 0
    with multiprocessing.Pool(max(1, (os.cpu_count() or 2) - 2)) as pool:
        for res in pool.imap_unordered(_clean_worker, jobs, chunksize=4):
            changed += res
    print(f"clean: processed {len(paths)} files, changed {changed}, dry={dry}")


def _flatten_worker(p):
    import importlib.util
    spec = importlib.util.spec_from_file_location("paper_flatten", os.path.join(ROOT, "tools/art/paper_flatten.py"))
    pf = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pf)
    im = Image.open(p).convert("RGBA")
    out = pf.flatten(im)
    _save_same(out, p, method=4)
    return p


def run_flatten(args, only, dry):
    import multiprocessing
    paths = _expand_targets(args, only)
    if dry:
        print(f"flatten (dry): {len(paths)} files")
        return
    n = 0
    with multiprocessing.Pool(max(1, (os.cpu_count() or 2) - 2)) as pool:
        for _ in pool.imap_unordered(_flatten_worker, paths, chunksize=4):
            n += 1
            if n % 50 == 0:
                print(f"flatten: {n}/{len(paths)}", flush=True)
    print(f"flatten: done {n} files")


def main():
    dry = "--dry" in sys.argv
    only = sys.argv[sys.argv.index("--only") + 1].split(",") if "--only" in sys.argv else None
    include_rig = "--include-rig" in sys.argv
    if sys.argv[1] == "clean":
        clean_args = [a for a in sys.argv[2:] if a not in ("--dry", "--include-rig", "--ignore-edited")]
        if "--only" in clean_args:
            i = clean_args.index("--only")
            clean_args = clean_args[:i] + clean_args[i + 2:]
        run_clean(clean_args, only, dry)
        return
    if sys.argv[1] == "flatten":
        fl_args = [a for a in sys.argv[2:] if a not in ("--dry", "--include-rig", "--ignore-edited")]
        if "--only" in fl_args:
            i = fl_args.index("--only")
            fl_args = fl_args[:i] + fl_args[i + 2:]
        run_flatten(fl_args, only, dry)
        return
    if sys.argv[1] == "atlas":
        # story set sheets with derived art (fold bands, doors, bodies): cards and every derived image under
        # game/art/atlas/<sheet>/ keep their canvas; atlas_clean copies are rebuilt from the new cards
        RAWDIR[0] = "art_src/atlas/raw"
        for sheet in sys.argv[2].split(","):
            files = []
            for dp, _, fs in os.walk(f"game/art/atlas/{sheet}"):
                for f in sorted(fs):
                    if "/stages" in dp and "--stages" not in sys.argv:
                        continue  # fold bands / doors / bodies: re-cut from the new card with their own tool
                    if f.endswith(".webp") and (not only or f[:-5] in only):
                        files.append((os.path.join(dp, f), sheet))
            run(sheet, [sheet], files, dry, "art_src/atlas/felt_backup", f"art_src/atlas/qa/{sheet}_paper_reskin.png")
            if not dry:
                from strip_rim import strip_rim
                for path, _ in files:
                    dst = path.replace("game/art/atlas/", "game/art/atlas_clean/")
                    if os.path.exists(dst) and "/stages/" not in path:
                        strip_rim(Image.open(path).convert("RGBA"))[0].save(dst, "WEBP", lossless=True)
                json.dump({"source": "paper (tools/cast/paper_reskin.py atlas)"},
                          open(f"art_src/atlas/qa/{sheet}_paper_reskin.json", "w"))
        return
    if sys.argv[1] == "files":
        # paper_reskin.py files <tale> <src dir> <out dir>: re-skin loose felt crops (e.g. the ghost figures' mouth
        # originals in art_src/cast/black_mouth_orig) into <out dir> under the same names
        tale, src_dir, out_dir = sys.argv[2], sys.argv[3], sys.argv[4]
        sheets = [s for s in CAST_SHEETS[tale] if os.path.exists(f"{RAW}/{s}_paper.png")]
        os.makedirs(out_dir, exist_ok=True)
        files = []
        for f in sorted(os.listdir(src_dir)):
            if f.endswith((".webp", ".png")):
                dst = os.path.join(out_dir, f)
                shutil.copy2(os.path.join(src_dir, f), dst)
                files.append((dst, sheets[0]))
        run(tale + "_files", sheets, files, dry, BACK, f"art_src/cast/qa/{tale}_files_paper_reskin.png")
        return
    tale = sys.argv[1]
    sheets = [s for s in CAST_SHEETS[tale] if os.path.exists(f"{RAW}/{s}_paper.png")]
    missing = [s for s in CAST_SHEETS[tale] if s not in sheets]
    if missing:
        print("NO PAPER RAW (skipped, stays felt):", missing)
    cat = json.load(open("game/art/cast/catalog.json"))
    ents = [e for e in cat if e.get("sheet") in sheets and (not only or e["id"] in only)]
    files = []
    for e in ents:
        files.append((f"game/{e['path']}", e["sheet"]))
        if include_rig:
            for p in (e.get("parts") or {}).values():
                files.append((f"game/{p}", e["sheet"]))
    run(tale, sheets, files, dry, BACK, f"art_src/cast/qa/{tale}_paper_reskin.png")


if __name__ == "__main__":
    main()
