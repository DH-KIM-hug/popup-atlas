#!/usr/bin/env python3
"""M3.3 targeted art regeneration jobs for tools/run_jobs.py.

Generates high-resolution matte cut-paper replacements for:
  - m33_sm_tree: story_sm_tree_00 & _01 without yellow pine-needle stitch-fans
  - m33_sm_mountain: story_sm_mountain_00..03, 08 without pine stitch-fans or ridge stitch dashes
  - m33_korean_nature_6: korean_nature_00, 01, 02, 03, 10, 21 without pine-needle fans or ridge dots
  - m33_rp_rug: story_rp_room_07 flat layered cut-paper concentric rug (no braided wool/yarn)
  - m33_wg_rug_floor: story_wg_cottage_05 flat cut-paper floorboards + concentric rug
  - m33_hearth_rug: story_hearth_16 flat cut-paper concentric oval rug
  - m33_story_room_02: decorated kitchen right wall (oak brace, wall shelf/peg rack with stoneware plates/copper pan/herbs; NO window)
  - m33_pj_splash: story_pj_yard_04 crisp high-res single-piece night-readable cut-paper water splash
"""
import json
import os
import sys
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
os.chdir(ROOT)

sys.path.insert(0, HERE)
import paper_jobs as pj  # noqa: E402

REF_DIR = "art_src/atlas/raw/m3_3_refs"
OUT_DIR = "art_src/atlas/raw/m3_3_out"
os.makedirs(REF_DIR, exist_ok=True)
os.makedirs(OUT_DIR, exist_ok=True)


def on_magenta(card_rel: str, pad: int = 80, min_w: int = 0, min_h: int = 0) -> str:
    im = Image.open(card_rel).convert("RGBA")
    W = max(im.width + 2 * pad, min_w)
    H = max(im.height + 2 * pad, min_h)
    bg = Image.new("RGB", (W, H), (255, 0, 255))
    bg.paste(im, ((W - im.width) // 2, (H - im.height) // 2), im)
    name = os.path.basename(card_rel).rsplit(".", 1)[0] + "_mag.png"
    out = os.path.join(REF_DIR, name)
    bg.save(out)
    return out


def make_grid_ref(name: str, card_rels: list[str], cols: int = 3, W: int = 1536, H: int = 1024) -> str:
    rows = (len(card_rels) + cols - 1) // cols
    bg = Image.new("RGB", (W, H), (255, 0, 255))
    cw, ch = W // cols, H // rows
    pad = 40
    for idx, rel in enumerate(card_rels):
        im = Image.open(rel).convert("RGBA")
        r, c = divmod(idx, cols)
        s = min((cw - 2 * pad) / im.width, (ch - 2 * pad) / im.height)
        nw, nh = max(1, round(im.width * s)), max(1, round(im.height * s))
        im_r = im.resize((nw, nh), Image.LANCZOS)
        x = c * cw + (cw - nw) // 2
        y = r * ch + ch - pad - nh
        bg.paste(im_r, (x, y), im_r)
    out = os.path.join(REF_DIR, name)
    bg.save(out)
    return out


ref_kn6 = make_grid_ref(
    "ref_korean_nature_6.png",
    [
        "game/art/atlas/korean_nature/korean_nature_00.webp",
        "game/art/atlas/korean_nature/korean_nature_01.webp",
        "game/art/atlas/korean_nature/korean_nature_02.webp",
        "game/art/atlas/korean_nature/korean_nature_03.webp",
        "game/art/atlas/korean_nature/korean_nature_10.webp",
        "game/art/atlas/korean_nature/korean_nature_21.webp",
    ],
    cols=3,
)

ref_rp_rug = on_magenta("game/art/atlas/story_rp_room/story_rp_room_07.webp", pad=120, min_w=512, min_h=512)
ref_wg_rug = on_magenta("game/art/atlas/story_wg_floor/story_wg_floor_01.webp", pad=80)
ref_wg_cottage_05 = on_magenta("game/art/atlas/story_wg_cottage/story_wg_cottage_05.webp", pad=80)
ref_wg_floor_00 = on_magenta("game/art/atlas/story_wg_floor/story_wg_floor_00.webp", pad=80)
ref_hearth_16 = on_magenta("game/art/atlas/story_hearth/story_hearth_16.webp", pad=100, min_w=640, min_h=360)
ref_room_02 = on_magenta("game/art/atlas/story_room/story_room_02.webp", pad=100, min_w=512, min_h=768)
ref_room_00 = on_magenta("game/art/atlas/story_room/story_room_00.webp", pad=60)
ref_pj_splash = on_magenta("game/art/atlas/story_pj_yard/story_pj_yard_04.webp", pad=120, min_w=640, min_h=640)

NO_STITCH_BAN = (
    "CRITICAL BAN: ABSOLUTELY NO yellow radial pine-needle fan spokes, NO starburst needle lines, "
    "NO yellow spoke fans on green pine pads, NO dashed or dotted stitch lines on mountain ridges or hills, "
    "NO embroidery, NO sewing seams, NO felt, NO wool, NO white sticker border. "
    "Instead, draw pine foliage pads as SOLID layered matte cut-paper green scalloped tiers (each scalloped tier a "
    "different shade of dark-pine, forest, and olive green cut paper glued in overlapping layers with a thin darker "
    "cut edge and a faint lighter paper rim on the upper-left), and draw mountain ridges as SMOOTH solid layered "
    "cut-paper hills with clean solid paper-tier edges. "
)

JOBS = [
    {
        "id": "m33_sm_tree",
        "kind": "bg",
        "refs": ["art_src/atlas/raw/story_sm_tree.png"],
        "aspect": "landscape 3:2 at the largest available size (1536x1024)",
        "out": f"{OUT_DIR}/story_sm_tree_v2.png",
        "prompt": (
            pj.REDRAW
            + pj.BG
            + pj.PAPER
            + NO_STITCH_BAN
            + "Keep the EXACT layout, positions, silhouettes, sizes, and colours of the 6 pieces in the reference "
            "(1: tall big zelkova tree on the left, 2: trunk in the middle, 3: big tree crown top-right, "
            "4: oil streak, 5: axe notches, 6: side branch bottom-right). "
            "Keep the golden cut-paper leaf sprays on the zelkova tree, and replace EVERY green pine-needle fan "
            "with clean solid layered dark-and-light green cut-paper scalloped foliage clumps (zero yellow needle spokes!)."
        ),
    },
    {
        "id": "m33_sm_mountain",
        "kind": "bg",
        "refs": ["art_src/atlas/raw/story_sm_mountain.png"],
        "aspect": "landscape 3:2 at the largest available size (1536x1024)",
        "out": f"{OUT_DIR}/story_sm_mountain_v2.png",
        "prompt": (
            pj.REDRAW
            + pj.BG
            + pj.PAPER
            + NO_STITCH_BAN
            + "Keep the EXACT layout, positions, silhouettes, sizes, and colours of all 10 pieces in the reference. "
            "On all 4 large mountain ridges (top two rows) and the pine on a rock ledge (bottom right): "
            "REMOVE every yellow radial pine-needle fan/spoke and REMOVE every dashed/dotted ridge stitch seam "
            "(especially on the front-left pale-green hill of the top-right mountain ridge). "
            "Replace them with smooth solid cut-paper mountain ridge bands (clean darker/lighter paper layer edge) "
            "and solid layered dark-green/moss-green cut-paper pine foliage pads with zero yellow spoke lines."
        ),
    },
    {
        "id": "m33_korean_nature_6",
        "kind": "bg",
        "refs": [ref_kn6],
        "aspect": "landscape 3:2 at the largest available size (1536x1024)",
        "out": f"{OUT_DIR}/korean_nature_6_v2.png",
        "prompt": (
            "REDRAW the 6 Korean landscape pieces in the reference sheet PIECE FOR PIECE in the EXACT same 3x2 grid "
            "positions, sizes, silhouettes, trunks, rocks, and colours, "
            + pj.BG
            + pj.PAPER
            + NO_STITCH_BAN
            + "Top row (3 pine trees) and bottom-left (1 pine tree) and bottom-middle (pine on rock): keep the exact "
            "twisting warm brown cut-paper pine trunks and layered scalloped green foliage pads, but COMPLETELY REMOVE "
            "all yellow-green radial fan/spoke clusters inside the green pine pads — replace them with clean solid "
            "layered dark-green and moss-green scalloped cut-paper foliage tiers. "
            "Bottom-right (misty Korean mountains): keep the exact blue-teal mountain peaks and cream mist bands, but "
            "COMPLETELY REMOVE the rows of yellow/green vertical dots/dashes along the lower green ridges — replace "
            "with clean solid layered green cut-paper forested ridges and smooth scalloped dark-green tree silhouettes."
        ),
    },
    {
        "id": "m33_rp_rug",
        "kind": "bg",
        "refs": [ref_rp_rug, ref_wg_rug],
        "aspect": "square 1:1",
        "out": f"{OUT_DIR}/story_rp_room_07_v2.png",
        "prompt": (
            "A single die-cut pop-up storybook prop centered on the image, "
            + pj.BG
            + pj.PAPER
            + "REDRAW the round-oval rug from the FIRST reference image in the EXACT flat layered matte cut-paper style "
            "of the SECOND reference image. Keep the exact round-oval proportions and the concentric colour rings from "
            "the FIRST reference (golden-yellow centre, rust-red ring, honey-yellow ring, olive-green ring, cream-tan "
            "ring, terracotta-orange outer ring). Every ring is a smooth FLAT sheet of cut paper glued in tiers with "
            "a thin darker cut edge line and subtle handmade paper grain, with a few small flat cut-paper notches along "
            "the ring seams like the SECOND reference. "
            "ABSOLUTELY NO braided yarn, NO wool, NO twisted rope, NO knitted or woven fabric fibres, NO fuzzy texture, "
            "NO white sticker border."
        ),
    },
    {
        "id": "m33_wg_rug_floor",
        "kind": "bg",
        "refs": [ref_wg_cottage_05, ref_wg_floor_00, ref_wg_rug],
        "aspect": "landscape 16:9",
        "out": f"{OUT_DIR}/story_wg_cottage_05_v2.png",
        "prompt": (
            "A single die-cut pop-up storybook floor prop centered horizontally, "
            + pj.BG
            + pj.PAPER
            + "REDRAW the wide floorboard-with-oval-rug card from the FIRST reference image, keeping its EXACT wide "
            "slightly-trapezoid floor silhouette and proportions, using the EXACT flat matte cut-paper style of the "
            "SECOND reference (warm honey-brown cut-paper floorboards with thin darker cut seams and nail dots) and the "
            "THIRD reference (smooth flat layered cut-paper concentric oval rug: cream centre, gold, rust-red, cream, "
            "golden outer ring — smooth flat paper tiers with tiny cut paper notches, NO braided yarn, NO wool, NO rope)."
        ),
    },
    {
        "id": "m33_hearth_rug",
        "kind": "bg",
        "refs": [ref_hearth_16, ref_wg_rug],
        "aspect": "landscape 16:9",
        "out": f"{OUT_DIR}/story_hearth_16_v2.png",
        "prompt": (
            "A single die-cut pop-up storybook prop centered, "
            + pj.BG
            + pj.PAPER
            + "REDRAW the wide oval rug from the FIRST reference image in the EXACT flat layered matte cut-paper style "
            "of the SECOND reference image. Keep the exact wide flat-oval proportions and concentric colour rings from "
            "the FIRST reference (pale cream-yellow oval centre, warm rust-red ring, pale cream-yellow ring, warm rust-red "
            "outer ring). Smooth flat cut-paper rings with thin darker cut edge lines and subtle paper grain, NO braided "
            "yarn, NO wool, NO knitted pebbles, NO fuzzy texture, NO white sticker border."
        ),
    },
    {
        "id": "m33_story_room_02",
        "kind": "bg",
        "refs": [ref_room_02, ref_room_00],
        "aspect": "portrait 2:3",
        "out": f"{OUT_DIR}/story_room_02_v2.png",
        "prompt": (
            "REDRAW the single rectangular cottage interior wall panel from the FIRST reference image, centered on the canvas, "
            + pj.BG
            + pj.PAPER
            + "Preserve the EXACT architecture, proportions, and palette of the FIRST and SECOND references: "
            "cream plaster band at the very top, horizontal warm-oak beam (#b86b24) with 3 dark iron studs near the top, "
            "vertical warm-oak corner post along the entire RIGHT edge, 4 courses of terracotta-red cut-paper bricks "
            "(#c94d28) with cream mortar (#f3de9f) along the lower third, and oak baseboard at the bottom. "
            "DECORATE the large blank cream plaster area in the middle (to the left of the right corner post and between "
            "the top beam and the brick wainscoting) in matching matte cut-paper style using ONLY the same warm oak, "
            "terracotta, cream, dark iron (#4a3525), and muted herb-green/copper tones: "
            "add a slim vertical oak timber moulding/brace on the left side, a small rustic oak wall shelf / peg rack "
            "mounted across the middle of the cream plaster holding 2 simple cream stoneware plates and a stoneware jug, "
            "with a small hanging copper frying pan and a tied dried herb bundle hanging from iron pegs below the shelf. "
            "CRITICAL: NO window, NO glass, NO outdoor sky (the exterior brick wall is solid windowless brick). "
            "Keep the wall rectangular with crisp straight outer cut edges and zero white sticker border."
        ),
    },
    {
        "id": "m33_pj_splash",
        "kind": "bg",
        "refs": [ref_pj_splash],
        "aspect": "square 1:1",
        "out": f"{OUT_DIR}/story_pj_yard_04_v2.png",
        "prompt": (
            "A single die-cut pop-up storybook water-splash card centered with generous magenta margin, "
            + pj.BG
            + pj.PAPER
            + "REDRAW the dynamic upward wave splash plume from the reference image as ONE SINGLE CONNECTED matte "
            "cut-paper sculpture (ALL foam curls and wave tongues connected to the main splash body — NO detached floating "
            "specks or separated droplets!). "
            "STYLE & NIGHT-READABLE PALETTE: crisp stepped cut-paper wave tongues with sharp dark indigo-blue cut lines "
            "(#183f66) and thin bright lit rims; vivid BRIGHT SNOW-WHITE / ICE-WHITE foam crests (#f8fbff to #eef6ff, "
            "crisp clean white paper, NOT murky beige or grey) layered cleanly over vivid CERULEAN BLUE (#4a96cc) and "
            "DEEP INDIGO BLUE (#22578a) curved wave sheets. "
            "Sharp crisp die-cut edges, matte paper grain, high contrast so it reads brightly and crisply in a night scene. "
            "CRITICAL: ZERO magenta or purple tint anywhere inside the blue wave tips, NO soft painterly blur, NO detached "
            "droplets, NO white sticker border."
        ),
    },
]

if __name__ == "__main__":
    out = os.path.join(HERE, "m3_3_jobs.json")
    json.dump(JOBS, open(out, "w"), ensure_ascii=False, indent=1)
    print("wrote", out, len(JOBS), "jobs:", " ".join(j["id"] for j in JOBS))
