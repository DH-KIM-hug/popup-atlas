#!/usr/bin/env python3
"""Builds tools/art/jobs_cards_r1.json — 해와 바람 pop-up prop card sheets.
Each job is one SHEET with several separate die-cut cards on flat magenta; tools/art/key_cards.py
splits, keys and trims them into game/art/cards/<category>/<id>.webp.
Style anchor (STYLE_V1) is shared verbatim by every job.  Run from repo root."""
import json, os

ROOT = "/Users/house_of_4k2b/orca/popup-atlas"
RAW = f"{ROOT}/art_src/cards/raw"
REF = [f"{ROOT}/art_src/cards/refs/sw_trav_walk.png"]

STYLE_V1 = """STYLE (anchor v1, shared by every card sheet): handmade cut-paper storybook craft, the same friendly paper look as the reference character (matte coloured cardstock, soft rounded die-cut shapes, gentle hand-cut edges, a thin light cream paper rim visible around each piece). Each object is a FLAT, FRONT-ON, die-cut stand-up pop-up card: an orthographic flat view, no perspective, no 3D shading, no cast shadow, no drop shadow, no ground under it.
PRINTED DETAIL: every piece carries fine printed folk-art illustration detail like a letterpress/lino print on the card: leaf veins, little stamped dots, tiny dashed stitched lines along the inner edges, small folk motifs (petals, scallops, chevrons), subtle paper fibre. Detail is printed flat on the card, not sculpted. 1 piece = 1 base colour + printed detail in darker/lighter tones of the same family.
PALETTE: warm muted storybook palette — sage green, moss and olive green, deep pine green, mustard ochre, terracotta / brick red, warm cream, walnut brown, soft teal blue, stone grey. Matte, saturated but not neon.
CRITICAL RULE: OBJECTS ONLY, NO FACES, NO EYES on any object. Every object stands upright and its lowest part is a FLAT STRAIGHT HORIZONTAL BOTTOM EDGE (the fold hinge of the pop-up card) — trunks, posts and stems end in a straight cut at the bottom.
LAYOUT: the objects are arranged in a loose grid, each object fully separate with WIDE empty gaps between them (at least 6% of the image), none overlapping, none touching the image border.
BACKGROUND: perfectly flat pure magenta #FF00FF background everywhere around the objects, no gradient, no texture, no shadows on it. NO magenta or pink inside the objects.
NO: text, letters, labels, numbers, faces, eyes, people, glossy highlights, photo textures, 3D render look, perspective, cast shadows, ground plane, frames, borders."""


def job(id_, subject, aspect="square 1:1"):
    return {
        "id": id_,
        "kind": "sprite",
        "pass": 2,
        "aspect": aspect,
        "out": f"{RAW}/{id_}.png",
        "refs": REF,
        "prompt": STYLE_V1 + "\nUse the reference image ONLY for the paper material, palette family and friendliness; do not draw the character.\n\nSUBJECT: " + subject,
    }


J = [
    job("sh_trees_green", "a sheet of 4 separate round-canopy deciduous tree cards, each a different size and shape: (1) big round layered canopy in moss green with printed leaf-vein clusters and stamped darker dots, (2) tall oval canopy in sage green made of overlapping scalloped leaf layers, (3) wide cloud-like canopy in olive green with small printed folk leaf motifs, (4) small young tree with lollipop canopy in fresh green. Flat walnut-brown trunks with printed bark lines, each trunk ending in a straight flat bottom cut."),
    job("sh_trees_warm", "a sheet of 4 separate round-canopy autumn deciduous tree cards: (1) mustard ochre round canopy with printed leaf veins and stitched outline, (2) terracotta / brick-red layered canopy with stamped dot rows, (3) two-tone canopy of olive green and ochre leaf clusters, (4) small apple tree, green canopy with printed little red fruit dots. Flat walnut-brown trunks, straight flat bottom cut."),
    job("sh_conifers", "a sheet of 5 separate conifer tree cards of varied heights: tall layered fir trees in deep pine green with printed needle hatching and lighter green tips, one slim spruce in blue-green, one short bushy pine, one fir with a terracotta-red trunk. Each tree ends in a short flat trunk with a straight flat bottom cut."),
    job("sh_bushes", "a sheet of 6 separate low bush and shrub cards, wider than tall: round sage-green bush with printed leaf veins, dark green hedge bush with stamped dots, olive bush with little red berries, flowering bush with small cream-and-yellow blossoms, mustard autumn bush, layered fern-like bush. Each sits on a straight flat bottom edge."),
    job("sh_flowers", "a sheet of 8 separate small flower-clump cards: yellow daisies with green leaves, red poppies, white chamomile, blue cornflowers, orange marigolds, cream tulips, tall foxglove spike in terracotta, a clump of yellow buttercups. Printed petal lines and leaf veins. Each clump grows from a straight flat bottom edge."),
    job("sh_rocks_mush", "a sheet of 7 separate small cards: 3 rounded stone-grey paper rocks of different shapes with printed lichen dots and crack lines (one mossy with green on top), 2 clusters of red-capped mushrooms with cream spots and cream stems, 1 cluster of tan brown mushrooms, 1 mossy log stump cut short. Each with a straight flat bottom edge.", "landscape 3:2"),
    job("sh_grass_reeds", "a sheet of 8 separate small cards: 3 grass tufts in different greens (pointed blades with printed midribs), 2 clusters of cattails (brown velvet heads on tall green stems), 2 clumps of tall stream reeds in olive and teal-green, 1 clump of rushes with tiny cream seed heads. Each grows from a straight flat bottom edge."),
    job("sh_wheat_hay", "a sheet of 6 separate cards: 2 wide rows of golden wheat (a band of wheat stalks with printed ears, mustard ochre, wider than tall), 1 tall single wheat sheaf tied with a string, 2 round hay bales seen from the side (circular spiral printed straw lines), 1 small conical haystack. Each with a straight flat bottom edge.", "landscape 3:2"),
    job("sh_cottage_a", "a sheet of 2 separate village cottage cards, front-on: (1) a cosy cottage with warm cream walls, terracotta tiled roof with printed scallop tiles, a brick chimney, a round-top wooden door, two small windows glowing warm yellow, printed stitched outline and flower box; (2) a smaller cottage with a golden thatched roof with printed straw strokes, cream walls with timber beams, one glowing window. Each house sits on a straight flat bottom edge, no ground, no path.", "landscape 3:2"),
    job("sh_cottage_b", "a sheet of 2 separate village building cards, front-on: (1) a narrow two-storey cottage with slate blue-grey roof, cream walls, a dormer window, a green door, warm glowing windows; (2) a little wooden barn with a terracotta roof and a big plank door with printed wood grain and a stamped star motif. Each sits on a straight flat bottom edge, no ground.", "landscape 3:2"),
    job("sh_village_props", "a sheet of 6 separate village prop cards: a stone well with a small wooden roof and bucket, a wooden signpost with two blank arrow boards (no text), a lantern post with a hanging lantern glowing warm yellow, a wooden wheelbarrow, a small wooden bench, a wooden water trough. Printed wood grain, stone dots, stitched lines. Each with a straight flat bottom edge."),
    job("sh_fences_bridge", "a sheet of 5 separate cards: 3 wooden fence sections (picket fence in cream, rustic split-rail fence in walnut brown, woven wattle fence), 1 little wooden gate, 1 small arched footbridge in cream paper with railings seen from the side (wider than tall), its two feet resting on a straight flat bottom edge. Printed wood grain lines. Each with a straight flat bottom edge.", "landscape 3:2"),
    job("sh_animals", "a sheet of 6 separate tiny decorative animal cards as simple folk-art silhouettes: 3 fluffy cream sheep in different poses (grazing, standing, lying) with printed curl patterns, plain dark brown head shape without any eyes or facial features, 2 small songbirds perched on a short wooden post, 1 white goose. Each with a straight flat bottom edge under the feet.", "landscape 3:2"),
    job("sh_hills_green", "ONE single very wide back-row pop-up card: a layered rolling-hill silhouette made of 3 overlapping hill layers (front moss green, middle sage green, back soft blue-green), with printed hedgerow rows, tiny round tree silhouettes, stitched field-boundary lines and stamped dots across the hills. The card spans almost the full width and has a straight flat horizontal bottom edge along the full width.", "landscape 16:9"),
    job("sh_hills_gold", "ONE single very wide back-row pop-up card: a layered rolling-hill silhouette with patchwork fields — mustard ochre wheat field stripes, olive green pasture, terracotta ploughed strips — printed furrow lines, tiny hedgerows, dotted folk motifs. A straight flat horizontal bottom edge along the full width.", "landscape 16:9"),
    job("sh_hills_far", "ONE single very wide far-background pop-up card: distant layered hills and gentle mountains in soft muted teal blue, slate blue and pale sage, with a row of tiny conifer silhouettes printed on the ridge and faint printed hatching. A straight flat horizontal bottom edge along the full width.", "landscape 16:9"),
    job("sh_stream_bank", "a sheet of 3 separate low, very wide stream-bank strip cards: (1) a strip of reeds and cattails with a cream wavy water-ripple band printed along its bottom, (2) a strip of grass and small stones on a riverbank, (3) a strip of rounded pebbles with a teal ripple pattern. Each is wider than tall with a straight flat bottom edge.", "landscape 3:2"),
    job("sh_trees_mixed", "a sheet of 4 separate tree cards: a tall slim poplar in olive green with printed leaf rows, a weeping willow in sage green with long drooping printed fronds, a terracotta round tree with spiral folk-motif leaves, a pear-shaped birch with cream-white trunk with dark stripe marks and yellow-green canopy. Each trunk ends in a straight flat bottom cut.", "any aspect ratio (square or landscape both acceptable)"),
]

if __name__ == "__main__":
    p = f"{ROOT}/tools/art/jobs_cards_r1.json"
    json.dump(J, open(p, "w"), indent=1, ensure_ascii=False)
    print(len(J), "jobs ->", p)
