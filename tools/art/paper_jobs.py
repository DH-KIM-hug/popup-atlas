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


for s in ATLAS_SHARED:
    job("atlas_" + s, RAW_A, s, CHAR if s in ("farm_animals",) else "")
for s in CARD_SHEETS:
    job("cards_" + s, RAW_K, s, CHAR if "animals" in s else "")
for tale, sheets in TALE_SHEETS.items():
    for s in sheets:
        job(s, RAW_A, s)

if __name__ == "__main__":
    out = os.path.join(HERE, "paper_jobs.json")
    json.dump(JOBS, open(out, "w"), ensure_ascii=False, indent=1)
    print("wrote", out, len(JOBS), "jobs")
