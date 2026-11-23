#!/usr/bin/env python3
"""Shared building kit (2026-11-23): material tiles + kit presets for game/core/world/building.gd.

  python3 tools/atlas/building_kit.py

- tiles: every story_bk_materials swatch, its cut rim trimmed, mirrored 2x2 so it repeats without seams
  -> game/art/buildings/tiles/<name>.webp
- game/art/buildings/kit.json: {"materials": {name: {tex, tile (world size of one swatch at unit 1), colour}},
  "kit": {preset: spec}} (spec format: Building in game/core/world/building.gd; units = world units at scale 1)
Presets: octagon_pavilion (팔각정), round_hut, round_tower (conical), rapunzel_tower, hanok_l (L-shaped, curved giwa
eaves), two_storey (hipped), windmill_tower, pagoda (3 tiers), gazebo, castle (compound: keep, four corner towers,
curtain walls with battlements, gatehouse with portcullis + drawbridge, flags, a bridge between towers).
"""
import json, os
import numpy as np
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
OUT = os.path.join(ROOT, "game", "art", "buildings")
NAMES = ["plaster", "fieldstone", "ashlar", "brick", "planks", "halftimber", "hanok_wall", "terracotta", "slate", "thatch",
         "giwa", "dancheong", "lacquer", "shingle"]
TILE = {"plaster": 0.35, "fieldstone": 0.3, "ashlar": 0.34, "brick": 0.24, "planks": 0.3, "halftimber": 0.4,
        "hanok_wall": 0.42, "terracotta": 0.26, "slate": 0.26, "thatch": 0.3, "giwa": 0.26, "dancheong": 0.2,
        "lacquer": 0.25, "shingle": 0.22}
P = "res://art/atlas/story_bk_parts/story_bk_parts_%02d.webp"
CARD = {k: f"story_bk_parts_{i:02d}" for i, k in enumerate(
    ["door", "gate_door", "portcullis", "drawbridge", "castle_window", "cottage_window", "round_window", "lattice",
     "flag_red", "flag_blue", "railing", "railing_kr", "finial", "balcony", "bracket", "steps"])}


def tiles():
    os.makedirs(os.path.join(OUT, "tiles"), exist_ok=True)
    mats = {}
    for i, n in enumerate(NAMES):
        im = Image.open(os.path.join(ROOT, f"game/art/atlas/story_bk_materials/story_bk_materials_{i:02d}.webp")).convert("RGBA")
        a = np.asarray(im)
        ys, xs = np.nonzero(a[..., 3] > 200)
        m = 12  # the cut line and rim of the swatch
        a = a[ys.min() + m:ys.max() - m, xs.min() + m:xs.max() - m].copy()
        a[..., 3] = 255
        top = np.concatenate([a, a[:, ::-1]], 1)
        t = np.concatenate([top, top[::-1]], 0)
        Image.fromarray(t).save(os.path.join(OUT, "tiles", f"{n}.webp"), "WEBP", quality=92, method=6)
        col = a[..., :3].reshape(-1, 3).mean(0)
        mats[n] = {"tex": f"res://art/buildings/tiles/{n}.webp", "tile": TILE[n] * 2.0,
                   "colour": "#%02x%02x%02x" % tuple(int(c) for c in col)}
    return mats


def castle():
    T = 0.34  # tower radius
    W = 1.5  # half the curtain square
    parts = [
        # the keep: tall square block, arched windows, battlements, a steep slate hip roof behind them
        {"name": "keep", "type": "block", "shape": "rect", "size": [1.1, 0.9], "at": [0, -0.35], "h": 1.55, "wall": "ashlar",
         "thick": 0.06, "plinth": {"h": 0.06, "mat": "fieldstone", "out": 0.03},
         "openings": [{"edge": 0, "u": 0.5, "w": 0.22, "h": 0.36, "y": 0.0, "kind": "arch", "card": CARD["door"]},
                      {"edge": 0, "u": 0.22, "w": 0.12, "h": 0.22, "y": 0.75, "kind": "arch", "card": CARD["castle_window"]},
                      {"edge": 0, "u": 0.78, "w": 0.12, "h": 0.22, "y": 0.75, "kind": "arch", "card": CARD["castle_window"]},
                      {"edge": 0, "u": 0.5, "w": 0.12, "h": 0.22, "y": 1.1, "kind": "arch", "card": CARD["castle_window"]},
                      {"edge": 1, "u": 0.5, "w": 0.12, "h": 0.22, "y": 0.9, "kind": "arch", "card": CARD["castle_window"]},
                      {"edge": 3, "u": 0.5, "w": 0.12, "h": 0.22, "y": 0.9, "kind": "arch", "card": CARD["castle_window"]}],
         "crenel": {"h": 0.09, "w": 0.09, "gap": 0.07, "d": 0.06},
         "roof": {"type": "hip", "mat": "slate", "h": 0.55, "overhang": -0.045, "lift": 0.0}},
        {"name": "keep_flag", "type": "flag", "card": CARD["flag_blue"], "at": [0.0, -0.35], "base": 2.15, "h": 0.42},
        # the gatehouse in the middle of the front wall
        {"name": "gatehouse", "type": "gate", "shape": "rect", "size": [0.8, 0.42], "at": [0, W], "h": 0.95,
         "wall": "ashlar", "thick": 0.06, "gate_w": 0.34, "gate_h": 0.5, "plinth": {"h": 0.04, "mat": "fieldstone", "out": 0.02},
         "crenel": {"h": 0.09, "w": 0.09, "gap": 0.07, "d": 0.06}, "portcullis": CARD["portcullis"],
         "drawbridge": CARD["drawbridge"],
         "openings": [{"edge": 0, "u": 0.2, "w": 0.09, "h": 0.17, "y": 0.62, "kind": "arch", "card": CARD["castle_window"]},
                      {"edge": 0, "u": 0.8, "w": 0.09, "h": 0.17, "y": 0.62, "kind": "arch", "card": CARD["castle_window"]}]},
    ]
    corners = [(-W, W), (W, W), (W, -W), (-W, -W)]
    for i, (x, z) in enumerate(corners):
        parts.append({"name": f"tower{i}", "type": "tower", "shape": "round", "n": 20, "r": T, "at": [x, z], "h": 1.25,
                      "wall": "ashlar", "thick": 0.06, "plinth": {"h": 0.05, "mat": "fieldstone", "out": 0.03},
                      "openings": [{"edge": 0, "u": 0.5, "w": 0.1, "h": 0.2, "y": 0.8, "kind": "arch", "card": CARD["castle_window"]}],
                      "crenel": {"h": 0.08, "w": 0.07, "gap": 0.06, "d": 0.06},
                      "roof": {"type": "cone", "mat": "slate", "h": 0.75, "overhang": 0.03, "lift": 0.09}})
        parts.append({"name": f"flag{i}", "type": "flag", "card": CARD["flag_red"], "at": [x, z], "base": 2.05, "h": 0.32})
    # curtain walls between the towers (front split round the gatehouse)
    walls = [((-W + T * 0.7, W), (-0.4, W)), ((0.4, W), (W - T * 0.7, W)), ((W, W - T * 0.7), (W, -W + T * 0.7)),
             ((W - T * 0.7, -W), (-W + T * 0.7, -W)), ((-W, -W + T * 0.7), (-W, W - T * 0.7))]
    for k, (a, b) in enumerate(walls):
        parts.append({"name": f"wall{k}", "type": "wall_run", "from": list(a), "to": list(b), "h": 0.78, "thick": 0.16,
                      "wall": "ashlar", "crenel": {"h": 0.08, "w": 0.08, "gap": 0.06, "d": 0.05}})
    # a little bridge from the keep to the back-left tower
    parts.append({"name": "bridge", "type": "bridge", "from": [-0.55, -0.6], "to": [-W + T * 0.8, -W + T * 0.8],
                  "y": 0.95, "w": 0.14, "mat": "planks"})
    return {"scale": 1.0, "parts": parts, "state": {"portcullis": 1.0, "drawbridge": 1.0}}


def kit():
    K = {}
    K["octagon_pavilion"] = {"parts": [
        {"name": "pavilion", "type": "pavilion", "shape": "ngon", "n": 8, "r": 0.55, "h": 0.5, "platform": 0.14,
         "platform_mat": "fieldstone", "deck": "planks", "pillar": "lacquer", "pillar_r": 0.028, "beam": "dancheong",
         "beam_h": 0.07, "railing": CARD["railing_kr"], "railing_h": 0.09,
         "roof": {"type": "pyramid", "mat": "giwa", "h": 0.42, "overhang": 0.2, "curve": 0.9, "thick": 0.03,
                  "finial": CARD["finial"], "finial_h": 0.13}}]}
    K["gazebo"] = {"parts": [
        {"name": "gazebo", "type": "pavilion", "shape": "ngon", "n": 6, "r": 0.42, "h": 0.46, "platform": 0.08,
         "platform_mat": "fieldstone", "deck": "planks", "pillar": "planks", "pillar_r": 0.022, "beam": "planks",
         "beam_h": 0.05, "railing": CARD["railing"], "railing_h": 0.1,
         "roof": {"type": "pyramid", "mat": "shingle", "h": 0.36, "overhang": 0.08, "thick": 0.025,
                  "finial": CARD["finial"], "finial_h": 0.1}}]}
    K["round_hut"] = {"parts": [
        {"name": "hut", "type": "block", "shape": "round", "n": 18, "r": 0.4, "h": 0.42, "wall": "plaster", "thick": 0.04,
         "plinth": {"h": 0.04, "mat": "fieldstone", "out": 0.02},
         "openings": [{"edge": 0, "u": 0.5, "w": 0.16, "h": 0.3, "kind": "arch", "card": CARD["door"]},
                      {"edge": 4, "u": 0.5, "w": 0.1, "h": 0.1, "y": 0.2, "kind": "window", "card": CARD["round_window"]},
                      {"edge": 14, "u": 0.5, "w": 0.1, "h": 0.1, "y": 0.2, "kind": "window", "card": CARD["round_window"]}],
         "roof": {"type": "cone", "mat": "thatch", "h": 0.5, "overhang": 0.1, "thick": 0.04}}]}
    K["round_tower"] = {"parts": [
        {"name": "tower", "type": "tower", "shape": "round", "n": 20, "r": 0.32, "h": 1.2, "wall": "fieldstone",
         "thick": 0.05, "plinth": {"h": 0.05, "mat": "fieldstone", "out": 0.03},
         "openings": [{"edge": 0, "u": 0.5, "w": 0.15, "h": 0.28, "kind": "arch", "card": CARD["door"]},
                      {"edge": 0, "u": 0.5, "w": 0.1, "h": 0.18, "y": 0.75, "kind": "arch", "card": CARD["castle_window"]},
                      {"edge": 10, "u": 0.5, "w": 0.1, "h": 0.18, "y": 0.75, "kind": "arch", "card": CARD["castle_window"]}],
         "roof": {"type": "cone", "mat": "slate", "h": 0.7, "overhang": 0.06, "thick": 0.03}}]}
    # a slim shaft carrying an overhanging round room (corbelled out), a real window in a flat front chord: wide enough
    # for a girl to lean out (opening open, no glass card: Rapunzel, the braid), a stone sill ledge under it, a plank
    # floor inside so the room reads through the window and from inside (units = world units at scale 1)
    K["rapunzel_tower"] = {"parts": [
        {"name": "shaft", "type": "tower", "shape": "round", "n": 22, "r": 0.34, "h": 1.62, "wall": "ashlar",
         "thick": 0.05, "plinth": {"h": 0.06, "mat": "fieldstone", "out": 0.04}},
        {"name": "tower", "type": "tower", "shape": "round", "n": 28, "r": 0.56, "flat": 0.26, "h": 0.56, "base": 1.84,
         "wall": "ashlar", "thick": 0.06, "floor": "planks", "flare": {"h": 0.16, "r0": 0.34},
         "openings": [{"edge": 0, "u": 0.5, "w": 0.14, "h": 0.25, "y": 0.15, "kind": "arch", "card": CARD["castle_window"],
                       "open": True, "ledge": {"out": 0.05, "h": 0.03, "over": 0.03}}],
         "roof": {"type": "cone", "mat": "slate", "h": 0.95, "overhang": 0.08, "thick": 0.03}},
        {"name": "flag", "type": "flag", "card": CARD["flag_red"], "at": [0, 0], "base": 3.35, "h": 0.32}]}
    K["windmill_tower"] = {"parts": [
        {"name": "mill", "type": "tower", "shape": "ngon", "n": 8, "r": 0.36, "h": 0.95, "wall": "planks", "thick": 0.04,
         "plinth": {"h": 0.1, "mat": "fieldstone", "out": 0.04},
         "openings": [{"edge": 0, "u": 0.5, "w": 0.16, "h": 0.28, "kind": "arch", "card": CARD["door"]},
                      {"edge": 0, "u": 0.5, "w": 0.1, "h": 0.1, "y": 0.6, "kind": "window", "card": CARD["round_window"]}],
         "roof": {"type": "pyramid", "mat": "shingle", "h": 0.42, "overhang": 0.06, "thick": 0.03}},
        {"name": "sails", "type": "sails", "at": [0.0, 0.45], "base": 1.17, "shaft": 0.2, "len": 0.62, "w": 0.13, "cloth": "plaster",
         "frame": "planks"}]}
    K["two_storey"] = {"parts": [
        {"name": "house", "type": "block", "shape": "rect", "size": [1.0, 0.7], "h": 0.95, "wall": "halftimber",
         "thick": 0.04, "plinth": {"h": 0.05, "mat": "fieldstone", "out": 0.02},
         "openings": [{"edge": 0, "u": 0.5, "w": 0.17, "h": 0.3, "kind": "door", "card": CARD["door"]},
                      {"edge": 0, "u": 0.2, "w": 0.16, "h": 0.14, "y": 0.12, "kind": "window", "card": CARD["cottage_window"]},
                      {"edge": 0, "u": 0.8, "w": 0.16, "h": 0.14, "y": 0.12, "kind": "window", "card": CARD["cottage_window"]},
                      {"edge": 0, "u": 0.3, "w": 0.16, "h": 0.14, "y": 0.58, "kind": "window", "card": CARD["cottage_window"]},
                      {"edge": 0, "u": 0.7, "w": 0.16, "h": 0.14, "y": 0.58, "kind": "window", "card": CARD["cottage_window"]},
                      {"edge": 1, "u": 0.5, "w": 0.16, "h": 0.14, "y": 0.58, "kind": "window", "card": CARD["cottage_window"]},
                      {"edge": 3, "u": 0.5, "w": 0.16, "h": 0.14, "y": 0.58, "kind": "window", "card": CARD["cottage_window"]}],
         "roof": {"type": "hip", "mat": "terracotta", "h": 0.42, "overhang": 0.07, "thick": 0.03}}]}
    K["hanok_l"] = {"parts": [
        {"name": "main", "type": "block", "shape": "rect", "size": [1.3, 0.5], "h": 0.42, "wall": "hanok_wall",
         "thick": 0.04, "plinth": {"h": 0.1, "mat": "fieldstone", "out": 0.06},
         "openings": [{"edge": 0, "u": 0.3, "w": 0.18, "h": 0.28, "kind": "door", "card": CARD["lattice"]},
                      {"edge": 0, "u": 0.62, "w": 0.18, "h": 0.28, "kind": "door", "card": CARD["lattice"]}],
         "roof": {"type": "hip", "mat": "giwa", "h": 0.34, "overhang": 0.16, "curve": 0.8, "thick": 0.03}},
        {"name": "wing", "type": "block", "shape": "rect", "size": [0.5, 0.75], "at": [0.4, 0.545], "h": 0.4,
         "wall": "hanok_wall", "thick": 0.04, "plinth": {"h": 0.1, "mat": "fieldstone", "out": 0.06},
         "openings": [{"edge": 3, "u": 0.55, "w": 0.18, "h": 0.26, "kind": "door", "card": CARD["lattice"]},
                      {"edge": 0, "u": 0.5, "w": 0.18, "h": 0.2, "y": 0.05, "kind": "window", "card": CARD["lattice"]}],
         "roof": {"type": "hip", "mat": "giwa", "h": 0.3, "overhang": 0.16, "curve": 0.8, "thick": 0.03, "ridge": "z"}}]}
    K["pagoda"] = {"parts": [
        {"name": "tier0", "type": "block", "shape": "rect", "size": [0.8, 0.8], "h": 0.42, "wall": "lacquer", "thick": 0.04,
         "plinth": {"h": 0.1, "mat": "fieldstone", "out": 0.08},
         "openings": [{"edge": 0, "u": 0.5, "w": 0.2, "h": 0.3, "kind": "door", "card": CARD["lattice"]}],
         "roof": {"type": "skirt", "mat": "giwa", "h": 0.18, "overhang": 0.22, "curve": 0.8, "thick": 0.03,
                  "upper_r": True, "upper": {"size": [0.6, 0.6]}}},
        {"name": "tier1", "type": "block", "shape": "rect", "size": [0.6, 0.6], "base": 0.6, "h": 0.32, "wall": "lacquer",
         "thick": 0.04,
         "openings": [{"edge": 0, "u": 0.5, "w": 0.16, "h": 0.16, "y": 0.08, "kind": "window", "card": CARD["lattice"]}],
         "roof": {"type": "skirt", "mat": "giwa", "h": 0.15, "overhang": 0.2, "curve": 0.8, "thick": 0.03,
                  "upper_r": True, "upper": {"size": [0.42, 0.42]}}},
        {"name": "tier2", "type": "block", "shape": "rect", "size": [0.42, 0.42], "base": 1.0, "h": 0.26, "wall": "lacquer",
         "thick": 0.04,
         "roof": {"type": "pyramid", "mat": "giwa", "h": 0.3, "overhang": 0.18, "curve": 0.9, "thick": 0.03,
                  "finial": CARD["finial"], "finial_h": 0.18}}]}
    K["castle"] = castle()
    return K


def main():
    mats = tiles()
    # template cards replaced by a kit building on the page (an open pavilion card would need a closed body)
    swap = {"korean_village_04": {"preset": "octagon_pavilion", "h": 1.17}}
    data = {"materials": mats, "cards": CARD, "kit": kit(), "swap": swap}
    os.makedirs(OUT, exist_ok=True)
    json.dump(data, open(os.path.join(OUT, "kit.json"), "w"), indent=1, ensure_ascii=False)
    print("kit", list(data["kit"]), "materials", list(mats))


if __name__ == "__main__":
    main()
