#!/usr/bin/env python3
"""Walker registry for the cast rig tools (cut_cast_rig.py, front_legs.py, lift_legs.py, walk_arms.py) — 2026-11-18.

The rig tools were written for the traveller only (figure ids starting with "cast_traveller", leg pieces coat/nocoat).
Each walker character now has an entry here: which figures are FRONT figures (they get the front-view leg cards and the
half / lift variants), which leg sheets to use and which piece of a sheet belongs to which figure, and which calm
figures get swinging arm cards. The traveller entry reproduces the old behaviour exactly (same pieces, same order,
same colour matching, same hand-drawn arm seams) so his rig stays byte-identical.

Side and back figures are cut by cut_cast_rig.py too (body / hips / leg_l / leg_r from their own drawn legs: the near
and far leg of a side stride, the heels of a back view) but keep their drawn legs (no front-leg swap).
"""
import json, os

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
SLICED = os.path.join(ROOT, "art_src", "cast", "sliced")


def sliced_path(sheet, idx, order="index"):
    """Path of piece `idx` of a sliced sheet. order "index" = slicer numbering (reading order); "x" = idx-th piece
    from the left among the big pieces (the slicer numbers by rows, so a taller piece further right can come first)."""
    if order == "index":
        return os.path.join(SLICED, sheet, f"{sheet}_{idx:02d}.webp")
    sl = json.load(open(os.path.join(SLICED, sheet, "_slices.json")))["sprites"]
    hmax = max(m["size"][1] for m in sl)
    big = sorted((m for m in sl if m["size"][1] > 0.3 * hmax), key=lambda m: m["bbox"][0])
    return os.path.join(SLICED, sheet, big[idx]["id"] + ".webp")


TRAV_PIECES = {("coat", "leg_l"): 0, ("coat", "leg_r"): 1, ("nocoat", "leg_l"): 2, ("nocoat", "leg_r"): 3}

# three_pigs piglets + wolf: one leg sheet each for straight / half / lift, 8 pieces left to right:
# pig_a L R, pig_b L R, pig_c L R, wolf L R (tools/cast/make_jobs.py cast_tp_legs_*).
TP_LEGS = {"front": "cast_tp_legs_front", "half": "cast_tp_legs_half", "lift": "cast_tp_legs_lift"}


def _tp(slot, front, calm, armless_idx):
    return {"legs": TP_LEGS, "order": "x", "pieces": {("x", "leg_l"): 2 * slot, ("x", "leg_r"): 2 * slot + 1},
            "kind": lambda fid: "x", "match": False, "front": front, "arms_auto": {calm: armless_idx},
            "armless": "cast_tp_walk_armless"}


PIG_FRONT = ["calm", "happy_wave", "defiant", "panting"]
CHARS = {
    "traveller": {"legs": {"front": "cast_traveller_legs_front", "half": "cast_traveller_legs_half",
                           "lift": "cast_traveller_legs_lift"},
                  "order": "index", "pieces": TRAV_PIECES,
                  "kind": lambda fid: "nocoat" if "_nocoat" in fid else "coat", "match": True,
                  "front": None},  # None = every rigged cast_traveller* figure (all are front figures)
    "pig_a": _tp(0, [f"cast_pig_a_{p}" for p in PIG_FRONT + ["scared", "tease"]], "cast_pig_a_calm", 0),
    "pig_b": _tp(1, [f"cast_pig_b_{p}" for p in PIG_FRONT + ["scared", "hammer"]], "cast_pig_b_calm", 1),
    "pig_c": _tp(2, [f"cast_pig_c_{p}" for p in PIG_FRONT[:3] + ["brave", "startled", "proud", "cheer"]],
                 "cast_pig_c_calm", 2),
    "wolf": _tp(3, ["cast_wolf_calm", "cast_wolf_shout", "cast_wolf_hungry"], "cast_wolf_calm", 3),
}


def char_of(fid):
    if fid.startswith("cast_traveller"):
        return "traveller"
    for c in ("pig_a", "pig_b", "pig_c", "wolf"):
        if fid.startswith(f"cast_{c}_"):
            return c
    return None


def is_front(fid):
    c = char_of(fid)
    if c is None:
        return False
    fr = CHARS[c]["front"]
    return fr is None or fid in fr
