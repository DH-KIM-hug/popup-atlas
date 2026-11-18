#!/usr/bin/env python3
"""Shared cast entries made for 「아기 돼지 삼형제」 (2026-11-18): three piglets, a mother pig and a wolf. Generic
storybook animals for game/art/cast/ (catalogued by role / view / pose tags so any tale can reuse them).
Used by tools/cast/build_cast.py (catalog + webp) and tools/cast/cut_cast_rig.py (rigged figures).

Sheets are Codex sheets sliced into art_src/cast/sliced/<sheet>/ (tools/cast/make_jobs.py); pieces are picked by their
x order on the sheet (the slicer numbers by rows). height_units: piglet 0.24 standing, mother 0.31, wolf 0.40 (the
traveller is 0.36; a house facade 0.6–0.74, its door ~0.28). A figure's height_units = the character's standing height ×
its pixel height / the sheet's standing reference height (so a sitting or crouching figure comes out shorter).
"""
PIG_H, MOM_H, WOLF_H = 0.24, 0.31, 0.40
PIG_TAGS = ["pig", "piglet", "animal", "generic", "walker", "three_pigs"]
WOLF_TAGS = ["wolf", "animal", "generic", "walker", "villain", "three_pigs"]
MOM_TAGS = ["pig", "mother", "animal", "generic", "three_pigs"]
OUTFIT = {"pig_a": ["straw_hat", "scarf"], "pig_b": ["overalls", "blue"], "pig_c": ["cap", "overalls", "red"]}

# (sheet, x index, cast id, role, pose, view, rigged, label, extra tags)
_PIG_VIEWS = {
    "pig_a": [("side_walk", "side", True, "walking, side profile (faces right)"),
              ("back_walk", "back", True, "walking away, back view"),
              ("happy_wave", "front", True, "happy, waving"),
              ("scared", "front", True, "scared, hands at cheeks"),
              ("run", "side", True, "running away scared, side (faces right)")],
    "pig_b": [("side_walk", "side", True, "walking, side profile (faces right)"),
              ("back_walk", "back", True, "walking away, back view (crossed straps)"),
              ("happy_wave", "front", True, "happy, waving"),
              ("scared", "front", True, "scared, hands at cheeks"),
              ("run", "side", True, "running away scared, side (faces right)")],
    "pig_c": [("side_walk", "side", True, "walking, side profile (faces right)"),
              ("back_walk", "back", True, "walking away, back view"),
              ("happy_wave", "front", True, "happy, waving"),
              ("brave", "front", True, "brave, fist up"),
              ("startled", "front", True, "startled, hands up beside face")],
}
_PIG_EXPR = {
    "pig_a": [("defiant", "front", True, "defiant, hands on hips (싫어요!)"),
              ("flute", "front", False, "playing a flute"),
              ("panting", "front", True, "tired, panting, sweat drops"),
              ("carry_straw", "side", True, "carrying a straw bundle, side (faces right)"),
              ("tease", "front", True, "laughing, pointing (teasing)")],
    "pig_b": [("defiant", "front", True, "defiant, hands on hips (싫어요!)"),
              ("violin", "front", False, "playing a violin"),
              ("panting", "front", True, "tired, panting, sweat drop"),
              ("carry_planks", "side", True, "carrying planks on the shoulder, side (faces right)"),
              ("hammer", "front", True, "hammering, hammer raised")],
    "pig_c": [("defiant", "front", True, "defiant, hands on hips (싫어요!)"),
              ("lay_brick", "front", False, "laying a brick with a trowel"),
              ("proud", "front", True, "proud, hands on straps"),
              ("carry_bricks", "side", True, "carrying two bricks, side (faces right)"),
              ("cheer", "front", True, "cheering, both arms up")],
}
ENTRIES = []  # dicts: sheet, x, id, role, pose, view, rigged, label, tags, h_ref, ref_x (standing reference on sheet)
for i, role in enumerate(["pig_a", "pig_b", "pig_c"]):
    tags = PIG_TAGS + OUTFIT[role]
    ENTRIES.append(dict(sheet="cast_pigs", x=i, id=f"cast_{role}_calm", role=role, pose="calm", view="front",
                        rigged=True, label="calm walking face, front", tags=tags + ["calm"], h=PIG_H, ref_x=[0, 1, 2]))
    for sheet, table in ((f"cast_{role}_views", _PIG_VIEWS[role]), (f"cast_{role}_expr", _PIG_EXPR[role])):
        refs = [k for k, t in enumerate(table) if t[1] == "front"]
        for k, (pose, view, rigged, label) in enumerate(table):
            ENTRIES.append(dict(sheet=sheet, x=k, id=f"cast_{role}_{pose}", role=role, pose=pose, view=view,
                                rigged=rigged, label=label, tags=tags + [pose, view], h=PIG_H, ref_x=refs))
ENTRIES.append(dict(sheet="cast_pigs", x=3, id="cast_mother_pig_calm", role="mother_pig", pose="calm", view="front",
                    rigged=False, label="mother pig, gentle smile, hands folded", tags=MOM_TAGS + ["calm"], h=MOM_H,
                    ref_x=[3]))
for k, (pose, label) in enumerate([("wave", "waving goodbye"), ("talk", "talking warmly, palms up")]):
    ENTRIES.append(dict(sheet="cast_mom_expr", x=k, id=f"cast_mother_pig_{pose}", role="mother_pig", pose=pose,
                        view="front", rigged=False, label="mother pig, " + label, tags=MOM_TAGS + [pose], h=MOM_H,
                        ref_x=[0, 1]))
for k, (pose, view, label) in enumerate([("calm", "front", "calm sly walking face, front"),
                                         ("side_prowl", "side", "prowling walk, side (faces right)"),
                                         ("back_walk", "back", "walking away, back view")]):
    ENTRIES.append(dict(sheet="cast_wolf", x=k, id=f"cast_wolf_{pose}", role="wolf", pose=pose, view=view, rigged=True,
                        label=label, tags=WOLF_TAGS + [pose, view], h=WOLF_H, ref_x=[0, 1, 2]))
for k, (pose, rigged, label) in enumerate([("sniff", True, "sniffing the air, walking, side (faces right)"),
                                           ("huff", False, "huffing and puffing, cheeks puffed, side (faces right)"),
                                           ("exhausted", False, "sitting slumped, exhausted (털썩), side"),
                                           ("tiptoe", True, "sneaking on tiptoe, side (faces right)"),
                                           ("run_away", True, "running away, scorched tail, side (faces right)")]):
    ENTRIES.append(dict(sheet="cast_wolf_side", x=k, id=f"cast_wolf_{pose}", role="wolf", pose=pose, view="side",
                        rigged=rigged, label=label, tags=WOLF_TAGS + [pose, "side"], h=WOLF_H, ref_x=[0]))
for k, (pose, rigged, label) in enumerate([("shout", True, "shouting, fist raised (문 열어라!)"),
                                           ("hungry", True, "hungry, licking lips, rubbing paws"),
                                           ("ouch", False, "'앗, 뜨거워!' jumping, fur on end, scorched tail"),
                                           ("falling", False, "dropping feet first, arms up (down the chimney)")]):
    ENTRIES.append(dict(sheet="cast_wolf_front", x=k, id=f"cast_wolf_{pose}", role="wolf", pose=pose, view="front",
                        rigged=rigged, label=label, tags=WOLF_TAGS + [pose, "front"], h=WOLF_H, ref_x=[0, 1]))

RIGGED = [e["id"] for e in ENTRIES if e["rigged"]]
