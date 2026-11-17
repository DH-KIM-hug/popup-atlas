#!/usr/bin/env python3
"""Round 3 sheets -> tools/art/jobs_cards_r3.json.
STYLE_V3 = STYLE_V1 with the printed cream outline removed (critic r2: "uniform white sticker border screams vinyl
sticker sheet"; the 3D card edge already shows the cream core), plus the r2 print-grain addendum.
Targets the r2 critic: cap repeats at 2-3 per screen (more distinct silhouettes for the common fillers), a few big
hero trees to anchor compositions, mossy logs / big stones for the low-camera foreground."""
import json, sys
sys.path.insert(0, "/Users/house_of_4k2b/orca/popup-atlas/tools/art")
from mk_jobs_cards import STYLE_V1, ROOT, RAW
from mk_jobs_cards_r2 import GRAIN

STYLE_V3 = STYLE_V1.replace(
    "gentle hand-cut edges, a thin light cream paper rim visible around each piece)",
    "gentle hand-cut edges; NO outline and NO light rim around the pieces: the coloured print runs right up to the cut edge)")
assert STYLE_V3 != STYLE_V1
REF = [f"{ROOT}/art_src/cards/refs/sw_trav_walk.png", f"{RAW}/sh2_trees_green_b.png"]


def job(id_, subject, aspect="landscape 3:2"):
    return {"id": id_, "kind": "sprite", "pass": 3, "aspect": aspect, "out": f"{RAW}/{id_}.png", "refs": REF,
            "prompt": STYLE_V3 + "\n" + GRAIN + "\nReference 1 = paper material, palette family and friendliness only (do not draw the character). Reference 2 = an existing card sheet of this kit: match its printing style and palette, but draw NEW objects (do not copy its trees) and do NOT draw its light outline rim.\n\nSUBJECT: " + subject}


J = [
    job("sh3_hero_trees", "a sheet of 3 separate LARGE hero tree cards, each clearly different: (1) a huge old oak with a broad lumpy canopy in layered moss and olive greens with printed oak leaves and acorn dots, thick walnut trunk with printed bark, (2) a tall weeping willow in sage with long hanging printed leaf strands, (3) a big chestnut tree with a wide rounded canopy in ochre and terracotta with printed five-finger leaves. Each trunk ends in a straight flat bottom cut.", "any aspect ratio (square or landscape both acceptable)"),
    job("sh3_logs_stones", "a sheet of 8 separate low cards: (1) a fallen log lying sideways with a moss-green top and printed bark rings at the cut end, (2) a short mossy stump with a little mushroom, (3) a big rounded boulder in warm grey with printed lichen dots, (4) a pair of stacked flat stones, (5) a small log pile of three logs, (6) a grey stone with a fern growing beside it, (7) a low mossy rock mound, (8) a tree stump with printed rings and small ivy. Each with a straight flat bottom edge.", "any aspect ratio (square or landscape both acceptable)"),
    job("sh3_fillers_a", "a sheet of 10 separate SMALL low filler cards, each a clearly different silhouette: a spiky grass tuft in olive, a round clover mound, a fan of three broad leaves, a curly fern sprout, a clump of tiny blue bell flowers, a clump of orange marigold buds, a sprig of red berries, a tuft of feathery seed grass, a little patch of white star flowers, a low scalloped moss mound with dots. Each grows from a straight flat bottom edge.", "any aspect ratio (square or landscape both acceptable)"),
    job("sh3_fillers_b", "a sheet of 10 separate SMALL low filler cards in warm autumn-meadow colours, each a clearly different silhouette: a rust-red leafy weed, an ochre seed-head clump, a terracotta mushroom trio, a pale yellow buttercup sprig, a purple clover cluster, a tall stem of pink foxglove, a little bramble arch, a dry golden grass tuft, a mustard tansy cluster, a single tall cattail pair. Each grows from a straight flat bottom edge.", "any aspect ratio (square or landscape both acceptable)"),
    job("sh3_bushes_c", "a sheet of 6 separate NEW bush cards, each a clearly different outline: a tall columnar hedge bush in pine green with printed leaf chevrons, a low wide bramble bush with berries, a round bush in rust autumn colours, a flowering elder bush with cream flower plates, a lumpy olive bush with stitched leaf lines, a small spiky gorse bush with yellow flowers. Each grows from a straight flat bottom edge."),
    job("sh3_trees_mixed_c", "a sheet of 5 separate NEW medium tree cards with clearly different silhouettes: a slim birch with a cream trunk and black printed marks and a small yellow-green canopy, a lollipop-round fruit tree with red dots, a tall poplar in olive, a wind-bent hawthorn with a canopy leaning to one side in sage, a small rowan with orange berry clusters. Each trunk ends in a straight flat bottom cut.", "any aspect ratio (square or landscape both acceptable)"),
]

if __name__ == "__main__":
    p = f"{ROOT}/tools/art/jobs_cards_r3.json"
    json.dump(J, open(p, "w"), indent=1, ensure_ascii=False)
    print(len(J), "jobs ->", p)
