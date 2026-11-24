#!/usr/bin/env python3
"""Apply M3.3 regenerated cut-paper assets into game/art/atlas/, catalog.json, and atlas_clean/."""
import json
import os
import shutil
import sys
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
os.chdir(ROOT)

sys.path.insert(0, HERE)
import clean_atlas_rims as car  # noqa: E402

OUT_DIR = "art_src/atlas/raw/m3_3_out"


def fit_to_size(im: Image.Image, target_size: tuple[int, int], pad: int = 4) -> Image.Image:
    """Resize keyed sprite (which already has 4px transparent padding) to fit exact target_size
    while preserving 4px transparent padding and bleeding edge RGB."""
    tw, th = target_size
    bb = im.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox()
    crop = im.crop(bb) if bb else im
    cw, ch = max(1, tw - 2 * pad), max(1, th - 2 * pad)
    resized = crop.resize((cw, ch), Image.LANCZOS)
    canvas = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    canvas.paste(resized, (pad, pad), resized)
    arr = car.bleed_rgb(np.asarray(canvas).astype(np.float32), iters=4)
    out = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")
    return car.clean_fringe_rgb(out, band=5, iters=12, min_m=8)


def fit_aspect_height(im: Image.Image, target_h: int, pad: int = 4) -> Image.Image:
    """Resize keyed sprite cleanly to target_h preserving natural aspect ratio + 4px padding."""
    bb = im.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox()
    crop = im.crop(bb) if bb else im
    ch = max(1, target_h - 2 * pad)
    cw = max(1, round(crop.width * ch / crop.height))
    resized = crop.resize((cw, ch), Image.LANCZOS)
    canvas = Image.new("RGBA", (cw + 2 * pad, target_h), (0, 0, 0, 0))
    canvas.paste(resized, (pad, pad), resized)
    arr = car.bleed_rgb(np.asarray(canvas).astype(np.float32), iters=4)
    out = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")
    return car.clean_fringe_rgb(out, band=5, iters=12, min_m=8)


def replace_preserving_size(src_im: Image.Image, dst_path: str) -> None:
    old = Image.open(dst_path).convert("RGBA")
    out = fit_to_size(src_im, old.size)
    car.save_webp(out, dst_path)
    print("updated", dst_path, out.size)


def main() -> None:
    # 1. story_sm_tree_00 & story_sm_tree_01
    sm_tree = car.key_raw_sprites(f"{OUT_DIR}/story_sm_tree_v2.png")
    replace_preserving_size(sm_tree[0][0], "game/art/atlas/story_sm_tree/story_sm_tree_00.webp")
    replace_preserving_size(sm_tree[1][0], "game/art/atlas/story_sm_tree/story_sm_tree_01.webp")
    shutil.copy2(f"{OUT_DIR}/story_sm_tree_v2.png", "art_src/atlas/raw/story_sm_tree_paper_v2.png")

    # 2. story_sm_mountain_00, 01, 02, 03, 08
    sm_mtn = car.key_raw_sprites(f"{OUT_DIR}/story_sm_mountain_v2.png")
    assert len(sm_mtn) == 10, f"expected 10 mountain pieces, got {len(sm_mtn)}"
    for idx in (0, 1, 2, 3, 8):
        replace_preserving_size(sm_mtn[idx][0], f"game/art/atlas/story_sm_mountain/story_sm_mountain_{idx:02d}.webp")
    shutil.copy2(f"{OUT_DIR}/story_sm_mountain_v2.png", "art_src/atlas/raw/story_sm_mountain_paper_v2.png")

    # 3. korean_nature_00, 01, 02, 03, 10, 21
    kn6 = car.key_raw_sprites(f"{OUT_DIR}/korean_nature_6_v2.png")
    assert len(kn6) == 6, f"expected 6 korean_nature pieces, got {len(kn6)}"
    for piece_im, cid_idx in zip((x[0] for x in kn6), (0, 1, 2, 3, 10, 21)):
        replace_preserving_size(piece_im, f"game/art/atlas/korean_nature/korean_nature_{cid_idx:02d}.webp")

    # 4. Wool rugs: story_rp_room_07, story_wg_cottage_05, story_hearth_16
    rp_rug = car.key_raw_sprites(f"{OUT_DIR}/story_rp_room_07_v2.png")
    assert len(rp_rug) == 1
    replace_preserving_size(rp_rug[0][0], "game/art/atlas/story_rp_room/story_rp_room_07.webp")

    wg_rug = car.key_raw_sprites(f"{OUT_DIR}/story_wg_cottage_05_v2.png")
    assert len(wg_rug) == 1
    replace_preserving_size(wg_rug[0][0], "game/art/atlas/story_wg_cottage/story_wg_cottage_05.webp")

    ht_rug = car.key_raw_sprites(f"{OUT_DIR}/story_hearth_16_v2.png")
    assert len(ht_rug) == 1
    replace_preserving_size(ht_rug[0][0], "game/art/atlas/story_hearth/story_hearth_16.webp")

    # 5. story_room_02 (243x418): composite decorated plaster zone into exact structural frame
    rm02_v2 = car.key_raw_sprites(f"{OUT_DIR}/story_room_02_v2.png")
    assert len(rm02_v2) == 1
    rm_orig_p = "game/art/atlas/story_room/story_room_02.webp"
    rm_orig = Image.open(rm_orig_p).convert("RGBA")
    rm_v2_fit = fit_to_size(rm02_v2[0][0], rm_orig.size)

    # Preserve exact top plaster + beam (y=0..58), right corner post (x=202..243), brick dado + baseboard (y=264..418)
    # Composite decorated interior plaster (x=4..201, y=58..264) with 2px smooth blend at border
    orig_arr = np.asarray(rm_orig).astype(np.float32)
    new_arr = np.asarray(rm_v2_fit).astype(np.float32)
    mask = np.zeros((rm_orig.height, rm_orig.width), np.float32)
    mask[58:264, 4:202] = 1.0
    # Soft 2px blend along beam, right post, and brick top
    mask[57:59, 4:202] = 0.5
    mask[263:265, 4:202] = 0.5
    mask[58:264, 200:202] = 0.5
    # Keep original alpha everywhere (exact 243x418 silhouette!)
    comp_rgb = orig_arr[..., :3] * (1.0 - mask[..., None]) + new_arr[..., :3] * mask[..., None]
    comp = Image.fromarray(np.dstack([np.clip(comp_rgb, 0, 255), orig_arr[..., 3]]).astype(np.uint8), "RGBA")
    comp = car.clean_fringe_rgb(comp, band=4, iters=10, min_m=8)
    car.save_webp(comp, rm_orig_p)
    shutil.copy2(f"{OUT_DIR}/story_room_02_v2.png", "art_src/atlas/raw/story_room_02_v2.png")
    print("updated", rm_orig_p, comp.size)

    # 6. story_pj_yard_04 (~542x570, parts: 1)
    pj_sp = car.key_raw_sprites(f"{OUT_DIR}/story_pj_yard_04_v2.png")
    assert len(pj_sp) == 1, f"expected 1 connected splash piece, got {len(pj_sp)}"
    splash_im = fit_aspect_height(pj_sp[0][0], 570)
    pj_dst = "game/art/atlas/story_pj_yard/story_pj_yard_04.webp"
    car.save_webp(splash_im, pj_dst)
    shutil.copy2(f"{OUT_DIR}/story_pj_yard_04_v2.png", "art_src/atlas/raw/story_pj_yard_04_v2.png")

    # Update _slices.json and catalog.json for story_pj_yard_04
    sl_path = "game/art/atlas/story_pj_yard/_slices.json"
    sl = json.load(open(sl_path))
    for s in sl["sprites"]:
        if s["id"] == "story_pj_yard_04":
            s["size"] = list(splash_im.size)
            s["halo"] = 0
            s["parts"] = 1
    json.dump(sl, open(sl_path, "w"), indent=1)

    cat_path = "game/art/atlas/catalog.json"
    cat = json.load(open(cat_path))
    for e in cat:
        if e["id"] == "story_pj_yard_04":
            e["px"] = list(splash_im.size)
            # height_units stays 0.25!
    json.dump(cat, open(cat_path, "w"), indent=1, ensure_ascii=False)
    print("updated", pj_dst, splash_im.size, "+ catalog.json px")


if __name__ == "__main__":
    main()
