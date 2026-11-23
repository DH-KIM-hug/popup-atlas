#!/usr/bin/env python3
"""wolf_goats room floor + rug as cut paper (wave 1 felt removal, 2026-11-24): the room floor was the old floorboards
card with a woolly braided rug baked in, laid twice, with the meadow showing through. Two separate top-down pieces:
a plain plank floor sheet (fills the room footprint) and a paper rag rug (laid on top).

  python3 tools/art/wg_floor_jobs.py && bash -c 'python3 tools/run_jobs.py tools/art/wg_floor_jobs.json'
  python3 tools/atlas/add_sheet.py story_wg_floor
"""
import json, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import paper_jobs as pj  # noqa: E402  (BG / PAPER blocks)

HERE = os.path.dirname(os.path.abspath(__file__))
TOP = ("Both pieces are seen STRAIGHT FROM ABOVE (top-down, orthographic, NO perspective, no vanishing lines, the "
       "rectangle is a true rectangle with square corners), to be laid flat on a pop-up page as a floor. ")
JOBS = [{
    "id": "story_wg_floor",
    "kind": "bg",
    "refs": ["game/art/atlas/story_wg_cottage/story_wg_cottage_05.webp"],
    "aspect": "landscape 3:2 (any size the tool returns is fine, save it as-is)",
    "out": "art_src/atlas/raw/story_wg_floor.png",
    "prompt": ("A prop sheet for a children's pop-up storybook with EXACTLY TWO separate pieces, " + pj.BG + TOP +
               "PIECE 1 (top, large, spanning most of the sheet width): a plain rectangular cottage FLOOR of honey-brown "
               "wooden floorboards, about twice as wide as it is deep, the boards running left to right, each board a "
               "separate strip of cut warm brown paper in slightly different honey / caramel shades, thin darker cut "
               "lines between boards, a few short board joints, a few tiny round nail dots, wood grain as a few thin "
               "lighter cut paper slivers. NO rug on it, nothing on it, the whole rectangle is floorboards edge to edge. "
               "PIECE 2 (below, smaller, about half the floor's width): an oval rag rug made of concentric rings of cut "
               "paper strips (cream centre, then golden yellow, rust red, honey yellow, a rust red outer ring), each ring "
               "a smooth flat paper band with a thin darker cut line, a few small cut paper notches along the rings to "
               "suggest braiding, NOT yarn, NOT rope, NOT knitted. Same colours as the rug in the reference image, but "
               "it is paper. " + pj.PAPER +
               "Never felt, never wool, never yarn or rope texture, no fuzzy fibres, no stitched edges.")}]

if __name__ == "__main__":
    out = os.path.join(HERE, "wg_floor_jobs.json")
    json.dump(JOBS, open(out, "w"), indent=1, ensure_ascii=False)
    print(out)


def compose_floor():
    """story_wg_floor_02: the plank sheet twice (back copy mirrored) as ONE sheet over the whole room footprint, so the
    floor is one plane at one height (two sheets laid at their own ground heights met in a step where a meadow tier
    crosses the house). Run after add_sheet.py story_wg_floor (which rewrites only _00 / _01 and their entries)."""
    from PIL import Image, ImageOps
    root = os.path.abspath(os.path.join(HERE, "..", ".."))
    d = os.path.join(root, "game/art/atlas/story_wg_floor")
    a = Image.open(os.path.join(d, "story_wg_floor_00.webp")).convert("RGBA")
    bb = a.getchannel("A").point(lambda v: 255 if v > 200 else 0).getbbox()  # the opaque sheet, no soft rim between
    bb = (bb[0], bb[1] + 4, bb[2], bb[3] - 4)  # shave the cut rim rows so no light seam shows between the copies
    p = a.crop(bb)
    out = Image.new("RGBA", (a.width, p.height * 2 + (a.height - p.height)), (0, 0, 0, 0))
    out.paste(ImageOps.mirror(p), (bb[0], bb[1]))
    out.paste(p, (bb[0], bb[1] + p.height))
    out.save(os.path.join(d, "story_wg_floor_02.webp"), "WEBP", lossless=True, quality=100, method=4)
    cp = os.path.join(root, "game/art/atlas/catalog.json")
    cat = [e for e in json.load(open(cp)) if e["id"] != "story_wg_floor_02"]
    base = next(e for e in cat if e["id"] == "story_wg_floor_00")
    e = dict(base, id="story_wg_floor_02", path="art/atlas/story_wg_floor/story_wg_floor_02.webp",
             label="honey plank floor, one sheet for a whole room (flat, top-down, paper; two plank sheets in one)",
             height_units=round(base["height_units"] * out.height / a.height, 3), px=list(out.size))
    cat.insert(cat.index(base) + 2, e)
    json.dump(cat, open(cp, "w"), indent=1, ensure_ascii=False)
    print("story_wg_floor_02", out.size, e["height_units"])


if __name__ == "__main__" and "--compose" in sys.argv:
    compose_floor()
