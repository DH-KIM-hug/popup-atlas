#!/usr/bin/env python3
"""Book-cover art for every tale (2026-11-22, user: "책 표지 디자인 제대로 하자").

  python3 tools/art/cover_jobs.py            # writes tools/art/cover_jobs.json
  bash -c 'python3 tools/run_jobs.py tools/art/cover_jobs.json <ids>'

Each tale gets one full-bleed KEY-ART picture for the front board of a 3D hardcover (game/story/cover_book.gd) and,
optionally, cut-paper title lettering on magenta (keyed into a transparent decal). Material is PAPER (user:
"펠트 질감 싫은뎅"): layered cut / torn paper, no felt, no wool, no stitches. The title band (top ~32 %) stays quiet so
the lettering reads. Characters keep the shipped designs (single-character crops as refs, never a lineup).
"""
import json, os

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = "art_src/cover/raw/"
RC = "art_src/cast/raw/"
RA = "art_src/atlas/raw/"
PORT = "portrait, near-square, the largest size the tool offers (any size it returns is fine); save it as-is"

PAPER = ("MATERIAL: a photographed PAPER-CUT diorama illustration: every shape is a separate sheet of matte coloured "
         "paper or thin cardstock, cut with crisp edges or softly torn deckled edges, glued in overlapping LAYERS at "
         "slightly different depths so each layer casts a small soft shadow on the one behind; fine paper-fibre grain "
         "like Japanese washi / Korean hanji; each layer edge has a thin darker cut line and a faint lighter rim on the "
         "lit side. Matte, no gloss, no 3D-render plastic look. ABSOLUTELY NO felt, NO wool, NO fuzz, NO fabric or "
         "knitted texture, NO stitches, NO dashed stitch lines, NO sewing seams, NO embroidery: where the reference "
         "shows dashed stitching, draw a clean cut-paper edge instead. ")
COVER = ("A FRONT COVER ILLUSTRATION of a children's picture book for ages 3-7, full-bleed to all four edges (no border, "
         "no frame, no book shown, no mockup, just the flat cover artwork). " + PAPER +
         "FORMAT: a near-square portrait picture (slightly taller than wide). COMPOSITION: the TOP 40 PERCENT of the "
         "picture is calm open sky with NOTHING in it except a few tiny stars or soft cloud strips near the edges: no "
         "roof, no moon, no characters, no trees, no detail there; it is reserved for a big title that will be added "
         "later. The buildings and characters sit in the LOWER 60 percent only; the characters stand in front, big and close, faces toward the viewer, clearly readable at a glance. Warm, cosy, magical, never "
         "scary. ABSOLUTELY NO TEXT anywhere: no letters, no title, no words, no numbers, no signature, no logo. ")
REF_CHAR = ("Draw every character EXACTLY as its reference image (same face, hair, hat, clothes, colours, proportions) "
            "but the character references are made of FELT: do NOT copy their fuzzy felt surface. The LAST reference image "
            "is the MATERIAL reference: copy ITS look exactly: smooth matte cardstock, crisp clean scissor-cut edges, "
            "flat even colour per piece, folds and layers shown by small soft shadows, hair as overlapping cut paper "
            "locks. Every surface is SMOOTH PAPER, nothing fuzzy, nothing woolly. Draw each character ONCE. ")
MAT_REF = RC + "cast_sm_paper_girl.png"

LETTER = ("TITLE LETTERING for a children's picture book cover, on a perfectly flat, uniform, solid pure MAGENTA "
          "background (#FF00FF, RGB 255,0,255), no texture, no gradient, no shadow on the background. The lettering is "
          "made of LAYERED CUT PAPER: each Korean syllable cut from thick matte coloured paper, chunky rounded friendly "
          "letterforms for young children, a cream paper backing layer cut around the whole word with a margin (like a "
          "sticker cut-out), a soft drop of the top layer onto the backing, fine paper grain, crisp cut edges. "
          "Spell the Korean text EXACTLY, every jamo correct, nothing added, nothing missing. No other text. ")

JOBS = [
    # 사탕 마녀의 핼러윈 (witch_candy): the witch, 다현이 and 호박이 at the glowing candy shop on Halloween night
    {"id": "cover_wc_art", "kind": "bg", "aspect": PORT, "out": RAW + "cover_wc_art.png",
     "refs": [RC + "ref_wc_witch.png", RC + "ref_wc_dahyun.png", RC + "ref_wc_cat.png", RA + "ref_wc_shopfront.png", MAT_REF],
     "prompt": COVER + REF_CHAR +
     "SUBJECT: Halloween night in a little storybook village. In the middle stands THE CANDY SHOP from the reference "
     "(half-timbered cream walls, teal scalloped roof, an orange-and-cream striped awning, a big window glowing warm "
     "golden with candy jars, an arched door with warm light spilling out, a swirl-lollipop shop sign). In FRONT of the "
     "shop, on a cobbled street: THE CANDY WITCH (reference 1: mint-green curly hair, purple witch hat with a yellow "
     "star, purple puff-sleeve dress with an orange star sash, orange-cream striped socks) smiling and holding up a big "
     "swirl lollipop; beside her the little girl DAHYUN (reference 2: brown bob, purple witch hat with a star, purple "
     "cape with an orange bow, cream dress, striped socks, red shoes) looking up delighted, holding a small orange "
     "pumpkin candy bucket; and the orange tabby cat HOBAK (reference 3) sitting at their feet. Glowing jack-o'-lanterns "
     "on the steps (cut paper, crisp), a few wrapped candies scattered on the cobbles, tiny paper bats far away. SKY (top third): deep "
     "BLUE-violet indigo night paper with a big pale-cream paper moon at one upper corner, a few small cut-paper stars, "
     "soft layered cloud strips, calm and empty in the centre. LIGHT: warm golden lamplight from the shop window and door "
     "on the characters, cool indigo night around. The big pale moon, if any, is SMALL and sits low beside the roof, not in the top 40 percent. PALETTE: indigo night #2b2a5c, blue-violet #4b3a7a, pumpkin orange "
     "#e8862a, candy gold #f2c14e, cream #f4e6c8, teal roof #2f6f73, mint #8fd3c0. Every purple is BLUE-violet, never pink "
     "or magenta."},
    {"id": "cover_wc_title", "kind": "bg", "aspect": "wide landscape (any wide size, e.g. 1536x1024 or 2172x724); save it as-is",
     "out": RAW + "cover_wc_title.png",
     "prompt": LETTER + "The Korean title, on two lines, centred: line 1 '사탕 마녀의' (smaller), line 2 '핼러윈' (big). "
     "Letter colours: candy-striped and Halloween: pumpkin orange #e8862a, candy gold #f2c14e and blue-violet #4b3a7a "
     "letters alternating, a thin dark-plum cut line around each letter, a tiny cut-paper star and a swirl lollipop as "
     "decoration beside the words (not touching the letters). The cream backing layer is one connected shape behind both "
     "lines."},
]


# variants of the same job (pick the best by eye, keep the rest)
for _j in list(JOBS):
    if _j["id"].endswith("_art"):
        for _v in ("b", "c"):
            JOBS.append(dict(_j, id=_j["id"] + "_" + _v, out=_j["out"].replace(".png", "_" + _v + ".png")))

# paper pass: the character refs are felt and their nap leaks into the picture; redraw a chosen picture as smooth cut
# paper, composition kept (the sunmoon scenery redraw did the same piece for piece)
REPAPER = ("REDRAW the FIRST reference illustration EXACTLY: the same composition, the same characters in the same poses "
           "and places, the same buildings, colours, light and framing, the same size and aspect; ONLY the MATERIAL "
           "changes. The SECOND reference is the material to copy: smooth matte CARDSTOCK cut paper with crisp clean "
           "scissor-cut edges, each colour area a flat even sheet, layers separated by small soft drop shadows, folds as "
           "scored creases, hair as overlapping cut-paper locks, cobbles and roof tiles as individually cut paper shapes. "
           "REMOVE every felt / wool / fuzzy / nubby / fibrous surface texture: surfaces are smooth paper with only a very "
           "faint fine grain. No stitches, no dashed seams. Keep the top 40 percent calm empty night sky. No text. ")
for _src in ("cover_wc_art", "cover_wc_art_c"):
    JOBS.append({"id": _src + "_paper", "kind": "bg", "aspect": "the SAME size and aspect as the first reference; save it as-is",
                 "out": RAW + _src + "_paper.png", "refs": [RAW + _src + ".png", MAT_REF], "prompt": REPAPER})


if __name__ == "__main__":
    out = os.path.join(HERE, "cover_jobs.json")
    json.dump(JOBS, open(out, "w"), ensure_ascii=False, indent=1)
    print("wrote", out, len(JOBS), "jobs:", " ".join(j["id"] for j in JOBS))
