#!/usr/bin/env python3
"""FELT -> PAPER redraw jobs for the shared library and the finished tales (2026-11-22, user: "펠트 질감 싫은뎅",
"다 종이로 변경 기존 동화도요"). Every felt sheet is redrawn PIECE FOR PIECE from itself (the felt raw is the reference:
same count, positions, silhouettes, colours), so tools/art/paper_swap.py can map each new piece onto the old card id.

  python3 tools/art/paper_jobs.py                      # writes tools/art/paper_jobs.json
  bash -c 'python3 tools/run_jobs.py tools/art/paper_jobs.json <ids>'

Outputs <raw dir>/<sheet>_paper.png next to the felt raw (the felt raw is copied to <sheet>_felt.png when the paper
version is swapped in). Groups (job id prefixes): atlas_* (shared atlas sheets), cards_* (the 해와 바람 card kit), and
the tale story sheets (three_pigs: story_houses / story_build_props / story_hearth / story_room; witch_candy: story_wc_*).
The PAPER block is the sunmoon one (tools/art/sunmoon_jobs.py) without the Korean setting words.
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))

BG = ("on a perfectly flat, uniform, solid pure MAGENTA background (#FF00FF, RGB 255,0,255) with no texture, no gradient, "
      "no vignette, no shadows on the background. Every piece is fully separate and isolated, with a clear empty magenta gap "
      "between pieces; pieces never touch or overlap each other and never touch the image border. "
      "No grid lines, no labels, no text, no letters, no numbers. ")
COLOUR = ("COLOUR RULE: keep the reference colours, but NO magenta-ish colour anywhere: every pink is a warm CORAL-PEACH or "
          "SALMON-ROSE (orange-leaning), any purple a deep BLUE-violet. ")
PAPER = ("STYLE (same for every piece): flat orthographic view, a die-cut pop-up book piece made of MATTE CUT PAPER and "
         "thin cardstock: every colour area is a separate cut or torn sheet of coloured paper glued in layers (a lighter "
         "or darker paper layer on top for shading and detail), crisp cut edges or softly torn deckled edges, each layer "
         "edge with a thin darker cut line and a faint lighter rim on its upper-left (lit) side, fine paper-fibre grain "
         "like handmade mulberry paper, matte, no gloss. ABSOLUTELY NO felt, NO wool, NO fuzz, NO fabric or "
         "knitted texture, NO stitches, NO dashed stitch lines, NO dotted seam lines, NO sewing seams, NO embroidery. "
         "Details are small cut paper shapes or a thin printed line, never stitching. Warm picture book for ages 3-7, "
         "no cast shadows, no drop shadows, no glow, no white sticker border around the pieces. " + COLOUR)
REDRAW = ("REDRAW the reference prop sheet for a children's pop-up storybook PIECE FOR PIECE: the SAME number of pieces in "
          "the SAME positions and the SAME left-to-right / top-to-bottom order, the same shapes, silhouettes, proportions, "
          "sizes and colours, the same objects and the same small motifs (flowers, leaves, windows) where they are cut "
          "shapes; ONLY the material changes from felt to paper. Every dashed or dotted stitch line in the reference is "
          "REMOVED (replace a stitched ridge or hem by a slightly lighter or darker paper layer edge). ")
MATERIALS = ("Objects keep their own material read in paper form: thatch and straw as layered cut straw-paper strips, "
             "plaster as cream paper, wood grain as cut brown paper strips, brick as small cut red-brown paper "
             "rectangles, stone as grey paper pieces, roof tiles as overlapping cut paper scales, water as layered "
             "teal / blue paper with cut cream ripple slivers, clouds as layered cut cream paper with NO dashed lines, "
             "plants and trees as layered cut paper leaves, fur and feathers as layered cut paper, faces simple. ")
CHAR = ("Characters and animals keep EXACTLY the reference design (face, eyes, mouth, expression, hair, clothes, colours, "
        "proportions, pose); only the material changes from felt to cut paper: clothes as cut paper panels, trims and "
        "ribbons as thin paper strips, fur and stripes as cut paper shapes. ")

RAW_A = "art_src/atlas/raw/"
RAW_K = "art_src/cards/raw/"
ATLAS_SHARED = ["hills_clouds", "meadow_field", "stream_water", "forest_broadleaf", "forest_conifer", "bushes_hedges",
                "spring_blossom", "autumn", "small_decor", "village_houses", "village_props", "farm_animals",
                "fairytale_west", "korean_nature", "korean_village", "winter_snow"]
TALE_SHEETS = {"three_pigs": ["story_houses", "story_build_props", "story_hearth", "story_room"],
               "witch_candy": ["story_wc_shop", "story_wc_room", "story_wc_pot", "story_wc_candies", "story_wc_ingredients",
                               "story_wc_halloween", "story_wc_decor", "story_wc_houses_a", "story_wc_houses_b"]}
CARD_SHEETS = sorted(f[:-4] for f in os.listdir(os.path.join(ROOT, RAW_K))
                     if f.endswith(".png") and not f.endswith(("_felt.png", "_paper.png")))


def felt_src(raw_dir, sheet):
    """the felt reference: <sheet>_felt.png once swapped, else <sheet>.png"""
    f = raw_dir + sheet + "_felt.png"
    return f if os.path.exists(os.path.join(ROOT, f)) else raw_dir + sheet + ".png"


JOBS = []


def job(jid, raw_dir, sheet, extra=""):
    JOBS.append({"id": jid, "kind": "bg", "refs": [felt_src(raw_dir, sheet)],
                 "aspect": "the SAME size and orientation as the reference image (any size the tool returns is fine, "
                           "save it as-is)",
                 "out": raw_dir + sheet + "_paper.png",
                 "prompt": REDRAW + BG + PAPER + MATERIALS + extra})


KOREAN_NATURE_EXTRA = (
    "BAN yellow radial pine-needle fan spokes, radial needle starbursts, and dashed or dotted ridge stitch lines: "
    "draw pine foliage pads as solid layered matte cut-paper green scalloped shapes with thin darker cut edges, "
    "and draw mountain ridges as smooth solid layered cut-paper hills with clean paper-tier edges (no dashes, no stitches). "
)

for s in ATLAS_SHARED:
    extra = CHAR if s in ("farm_animals",) else (KOREAN_NATURE_EXTRA if s == "korean_nature" else "")
    job("atlas_" + s, RAW_A, s, extra)
for s in CARD_SHEETS:
    job("cards_" + s, RAW_K, s, CHAR if "animals" in s else "")
for tale, sheets in TALE_SHEETS.items():
    for s in sheets:
        job(s, RAW_A, s)

# ---------------------------------------------------------------- casts of the finished tales (part B)
RAW_C = "art_src/cast/raw/"
CAST_REDRAW = ("REDRAW the reference CHARACTER SHEET for a children's pop-up storybook PIECE FOR PIECE: the SAME number of "
               "figures in the SAME positions and order, each figure the SAME character in EXACTLY the same pose (every "
               "arm, hand, leg, foot, head tilt and prop in the same place), the same facial expression, the same size, "
               "outline and proportions, the same clothes and colours, the same gaps between the legs; ONLY the material "
               "changes from felt to cut paper. Every dashed or dotted stitch line in the reference is REMOVED (a hem or "
               "seam becomes a paper layer edge or a thin printed line). ")
CAST_SHEETS = {
    "three_pigs": ["cast_pigs", "cast_mom_expr", "cast_tp_peek"] +
                  [f"cast_pig_{r}_{k}" for r in "abc" for k in ("views", "expr", "walk_cycle", "run_cycle")] +
                  ["cast_pig_a_carry_cycle", "cast_wolf", "cast_wolf_side", "cast_wolf_front", "cast_wolf_walk_cycle",
                   "cast_wolf_run_cycle", "cast_wolf_front_cycle",
                   "cast_tp_legs_front", "cast_tp_legs_half", "cast_tp_legs_lift", "cast_tp_legs_side", "cast_tp_walk_armless"],
    "sun_wind": ["cast_traveller", "cast_traveller_expr_a", "cast_traveller_expr_b", "cast_traveller_props", "cast_sun_v2",
                 "cast_wind_v2", "cast_traveller_legs_front", "cast_traveller_legs_half", "cast_traveller_legs_lift",
                 "cast_traveller_walk_armless", "cast_traveller_walk_arms"],
    "witch_candy": ["cast_wc_lineup", "cast_dahyun_expr_a", "cast_dahyun_expr_b", "cast_dahyun_tf_a", "cast_dahyun_tf_b",
                    "cast_dahyun_walk_cycle", "cast_dahyun_ghost_cycle", "cast_dahyun_duck_cycle", "cast_witch_expr_a",
                    "cast_witch_expr_b", "cast_witch_walk_cycle", "cast_witch_ghost_cycle", "cast_friends_expr_a",
                    "cast_friends_expr_b", "cast_cat_expr", "cast_cat_walk_cycle", "cast_cat_ghost_cycle",
                    "cast_rabbit_walk_cycle", "cast_rabbit_ghost_cycle", "cast_bear_walk_cycle", "cast_bear_ghost_cycle",
                    "cast_fox_walk_cycle", "cast_fox_ghost_cycle", "cast_wc_surprised_black", "cast_wc_ghost_lips"],
}
for tale, sheets in CAST_SHEETS.items():
    for s in sheets:
        JOBS.append({"id": "castp_" + s, "kind": "bg", "refs": [felt_src(RAW_C, s)],
                     "aspect": "the SAME size and orientation as the reference image (any size the tool returns is fine, "
                               "save it as-is)",
                     "out": RAW_C + s + "_paper.png",
                     "prompt": CAST_REDRAW + BG + PAPER + CHAR + MATERIALS})

# ---------------------------------------------------------------- new paper walk frames (2026-11-22, coordinator: no
# hopping card or straw that vanishes when 첫째 walks away from / toward the camera carrying straw)
JOBS.append({"id": "castnew_cast_pig_a_carry_views", "kind": "bg",
             "refs": [RAW_C + "cast_pig_a_carry_cycle_paper.png", RAW_C + "cast_pig_a_walk_cycle_paper.png"],
             "aspect": "wide landscape (any wide size the tool returns is fine, e.g. 2172x724; save it as-is)",
             "out": RAW_C + "cast_pig_a_carry_views.png",
             "prompt": "A CHARACTER SHEET for a children's pop-up storybook: FOUR separate full-body die-cut stand-up figures "
             "of the SAME little pig in one horizontal row, feet on one common baseline near the bottom, " + BG + PAPER + CHAR +
             "THE PIG: exactly the first reference's piglet (straw hat with a brown band, mustard knitted-look scarf drawn "
             "as cut paper strips, peach skin, curly tail) carrying the SAME golden straw bundle tied with a cord. Same size "
             "as the walking pig in the second reference. (1) BACK view walking AWAY from the viewer, LEFT foot forward: we "
             "see his hat from behind, the scarf ends, his back and curly tail, the straw bundle hugged in front of him so "
             "its golden ends stick out above both shoulders; (2) the same BACK view with the RIGHT foot forward; (3) FRONT "
             "view walking TOWARD the viewer, LEFT foot forward, hugging the straw bundle in both arms in front of his belly, "
             "a cheerful busy face; (4) the same FRONT view with the RIGHT foot forward. Every figure has a clearly VISIBLE "
             "open magenta GAP between the two legs; exactly two arms and two legs; no other character."})

if __name__ == "__main__":
    out = os.path.join(HERE, "paper_jobs.json")
    json.dump(JOBS, open(out, "w"), ensure_ascii=False, indent=1)
    print("wrote", out, len(JOBS), "jobs")
