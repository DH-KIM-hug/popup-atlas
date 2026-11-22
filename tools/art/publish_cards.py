#!/usr/bin/env python3
"""Keyed cards (art_src/cards/keyed/<sheet>_<nn>.png) -> shipped webp + catalog.
  python3 tools/art/publish_cards.py
MAP below names every kept card: keyed name -> (id, category, height_units, cross_slot). Cards not in MAP are
not shipped (rejects). Output: game/art/cards/<category>/<id>.webp, game/art/cards/catalog.json,
art_src/cards/_kit_contact.png (all shipped cards, labelled)."""
import json, os
from PIL import Image, ImageDraw
sys_path = os.path.dirname(os.path.abspath(__file__))
import sys
sys.path.insert(0, sys_path)
from strip_rim import strip_rim

STRIP_RIM = True

ROOT = "/Users/house_of_4k2b/orca/popup-atlas"
KEYED = f"{ROOT}/art_src/cards/keyed"
DST = f"{ROOT}/game/art/cards"

MAP = {
    # round-canopy deciduous trees (0.6-1.1)
    "sh_trees_green_00": ("tree_round_moss", "tree", 0.95, True),
    "sh_trees_green_01": ("tree_oval_sage", "tree", 1.0, False),
    "sh_trees_green_02": ("tree_cloud_olive", "tree", 0.8, True),
    "sh_trees_green_03": ("tree_young_green", "tree", 0.6, False),
    "sh_trees_warm_00": ("tree_round_ochre", "tree", 0.9, True),
    "sh_trees_warm_01": ("tree_layer_terracotta", "tree", 0.95, False),
    "sh_trees_warm_02": ("tree_twotone_olive_ochre", "tree", 0.85, True),
    "sh_trees_warm_03": ("tree_apple", "tree", 0.8, False),
    # conifers
    "sh_conifers_00": ("conifer_olive_redtrunk", "conifer", 0.8, False),
    "sh_conifers_01": ("conifer_spruce_blue", "conifer", 1.05, False),
    "sh_conifers_02": ("conifer_fir_tall", "conifer", 1.1, True),
    "sh_conifers_03": ("conifer_pine_bushy", "conifer", 0.6, False),
    "sh_conifers_04": ("conifer_fir_green", "conifer", 0.85, False),
    # bushes (0.2-0.4)
    "sh_bushes_00": ("bush_sage_leaf", "bush", 0.3, False),
    "sh_bushes_01": ("bush_hedge_dark", "bush", 0.28, False),
    "sh_bushes_02": ("bush_olive_berry", "bush", 0.3, False),
    "sh_bushes_03": ("bush_teal_blossom", "bush", 0.32, False),
    "sh_bushes_04": ("bush_mustard_autumn", "bush", 0.3, False),
    "sh_bushes_05": ("bush_fern", "bush", 0.34, False),
    # flower clumps (0.15-0.3)
    "sh_flowers_00": ("flower_daisy_yellow", "flower", 0.22, False),
    "sh_flowers_01": ("flower_poppy_red", "flower", 0.22, False),
    "sh_flowers_02": ("flower_chamomile", "flower", 0.2, False),
    "sh_flowers_03": ("flower_cornflower", "flower", 0.22, False),
    "sh_flowers_04": ("flower_marigold", "flower", 0.22, False),
    "sh_flowers_05": ("flower_tulip_cream", "flower", 0.22, False),
    "sh_flowers_06": ("flower_foxglove", "flower", 0.3, False),
    "sh_flowers_07": ("flower_buttercup", "flower", 0.2, False),
}
EXTRA = os.path.join(os.path.dirname(__file__), "card_map_extra.json")   # appended entries for later sheets
MAX_H, MAX_W = 640, 1024
MAX_W_HILL = 2048


_LOCK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "card_aspect_lock.json")
ASPECT_LOCK = json.load(open(_LOCK)) if os.path.exists(_LOCK) else {}


def main():
    m = dict(MAP)
    if os.path.exists(EXTRA):
        m.update({k: tuple(v) for k, v in json.load(open(EXTRA)).items()})
    cat = []
    for src, (cid, category, h, cross) in sorted(m.items(), key=lambda kv: (kv[1][1], kv[1][0])):
        p = f"{KEYED}/{src}.png"
        if not os.path.exists(p):
            print("missing", src)
            continue
        im = Image.open(p).convert("RGBA")
        if STRIP_RIM:
            im, _ = strip_rim(im)  # r3: drop the printed cream "sticker" outline (the 3D card edge shows the core)
        mw = MAX_W_HILL if category == "hill" else MAX_W
        s = min(1.0, MAX_H / im.height, mw / im.width)
        if s < 1.0:
            im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
        os.makedirs(f"{DST}/{category}", exist_ok=True)
        out = f"{DST}/{category}/{cid}.webp"
        import io
        buf = io.BytesIO()
        im.save(buf, "WEBP", quality=90, method=6)
        # Only rewrite changed files: rewriting triggers a Godot reimport that can race other runs.
        if not os.path.exists(out) or open(out, "rb").read() != buf.getvalue():
            open(out, "wb").write(buf.getvalue())
        # felt -> paper (2026-11-22): the layout aspect stays the felt card's (tools/art/card_aspect_lock.json), so the
        # template places every card exactly where it stood (a 1 % aspect change cascaded through the placement)
        asp = ASPECT_LOCK.get(src, round(im.width / im.height, 3))
        cat.append({"id": cid, "path": f"res://art/cards/{category}/{cid}.webp", "category": category,
                    "height_units": h, "cross_slot": cross, "aspect": asp, "src": src})
    json.dump(cat, open(f"{DST}/catalog.json", "w"), indent=1)
    # contact sheet of the whole kit
    cols, cw, th = 8, 200, 170
    rows = (len(cat) + cols - 1) // cols
    sh = Image.new("RGB", (cols * cw, rows * (th + 26)), (120, 132, 118))
    d = ImageDraw.Draw(sh)
    for i, e in enumerate(cat):
        im = Image.open(f"{DST}/{e['category']}/{e['id']}.webp")
        s = min(th / im.height, (cw - 8) / im.width)
        t = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
        x, y = (i % cols) * cw + 4, (i // cols) * (th + 26)
        sh.paste(t, (x, y + th - t.height), t)
        d.text((x, y + th + 4), e["id"][:30], fill=(255, 255, 255))
    sh.save(f"{ROOT}/art_src/cards/_kit_contact.png")
    cats = {}
    for e in cat:
        cats[e["category"]] = cats.get(e["category"], 0) + 1
    print(len(cat), "cards", cats)


if __name__ == "__main__":
    main()
