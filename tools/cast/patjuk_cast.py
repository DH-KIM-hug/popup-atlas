#!/usr/bin/env python3
"""Shared cast for 「팥죽할멈과 호랑이」 (patjuk, 2026-11-23): the granny (skin hanbok_granny), the seven helpers (skins
pj_bam, pj_jara, pj_ddong, pj_songgot, pj_jeolgu, pj_myeongseok, pj_jige: hop-cards with faces, a calm and an action
figure each) and new figures of sunmoon's shared tiger (skin tiger). Generic (a Joseon granny, a tiger, living
household things), so they live in game/art/cast/.

  python3 tools/cast/patjuk_cast.py            # slice standing-figure sheets, copy, MERGE into catalog.json
  python3 tools/cast/patjuk_cast.py --cycles   # also the drawn cycles (add_cycles.py: granny walk, tiger crying run)

MERGE ONLY (another tale's agent writes the same catalog): the catalog is re-read right before writing and only the
ids this builder makes are replaced; the tiger's sunmoon figures and cycles are untouched. Never build_cast.py.
Heights: the granny 0.30 standing; sheets with standing references scale by them, the others by explicit heights.
"""
import json, os, subprocess, sys
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from characters import sliced_path
from build_cast import drop_specks

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
os.chdir(ROOT)
GR, TIG = "hanbok_granny", "tiger"
H = {GR: 0.30, TIG: 0.43}
TAGS = {GR: ["granny", "grandmother", "person", "adult", "hanbok", "korean_traditional", "walker"],
        TIG: ["tiger", "animal", "korean_traditional", "villain", "walker"]}
# r2: the helpers read too small next to the granny in the kitchen shots (x1.35)
HELP = {"bam": ("chestnut", 0.1), "jara": ("soft-shell turtle", 0.1), "ddong": ("cow-dung patty", 0.095),
        "songgot": ("awl", 0.17), "jeolgu": ("stone mortar and pestle", 0.15),
        "myeongseok": ("rolled straw mat", 0.15), "jige": ("A-frame carrier", 0.32)}
for h, (what, ht) in HELP.items():
    H["pj_" + h] = ht
    TAGS["pj_" + h] = ["helper", "object", "living_object", "korean_traditional", h, what.split()[-1]]
# sheet -> [(x index, role, pose, view, label, is_reference, explicit height or None)]
SHEETS = {
    "cast_pj_granny_a": [(0, GR, "calm", "front", "calm, hands folded", 1, None),
                         (1, GR, "hoe_up", "front", "weeding: hand hoe raised, humming", 1, None),
                         (2, GR, "hoe_down", "front", "weeding: hand hoe down at the ground", 1, None),
                         (3, GR, "scared", "front", "scared, hands at cheeks", 1, None),
                         (4, GR, "plead", "front", "pleading, hands clasped, teary", 1, None),
                         (5, GR, "sad", "front", "worried, hand at cheek, a tear", 1, None)],
    "cast_pj_granny_b": [(0, GR, "cry_stir", "front", "stirring the porridge pot, crying", 1, None),
                         (1, GR, "offer", "front", "offering a bowl of red-bean porridge (to the right)", 1, None),
                         (2, GR, "whisper", "front", "whispering, hand at mouth", 1, None),
                         (3, GR, "call", "front", "calling sweetly, pointing down-left (the hearth)", 1, None),
                         (4, GR, "cheer", "front", "cheering, arms up, one foot kicked", 1, None),
                         (5, GR, "hug", "front", "arms open wide to hug", 1, None)],
    "cast_pj_granny_c": [(0, GR, "side_walk", "side", "standing, side (faces right)", 1, None),
                         (1, GR, "back_walk", "back", "standing, back view", 1, None),
                         (2, GR, "hide", "front", "crouching in a corner, hands over mouth", 0, None),
                         (3, GR, "look_far", "front", "gazing far away, hand shading eyes", 1, None)],
    "cast_pj_tiger_a": [(0, TIG, "sit_fire", "side", "crouching at the fire, warming paws (faces right)", 0, None),
                        (1, TIG, "eye_hurt", "front", "hurt eye: paw over one eye, stars, hopping (앗 뜨거워)", 1, None),
                        (2, TIG, "mouth_ouch", "front", "bitten lip, paws at mouth, comic tears (아야야)", 1, None),
                        (3, TIG, "backstep", "side", "backing away startled (faces right)", 0, None),
                        (4, TIG, "slip_fall", "side", "slipping, feet shooting up (faces right)", 0, None),
                        (5, TIG, "fallen", "side", "fallen flat on his back, dizzy", 0, None)],
    "cast_pj_tiger_b": [(0, TIG, "poked", "side", "poked in the bottom: jumping up, paws on bottom (faces right)", 0, 0.44),
                        (1, TIG, "flat_bump", "side", "sprawled flat on his tummy, bump, dizzy stars", 0, 0.2),
                        (2, TIG, "rolled", "side", "rolled up in a straw mat, head and tail out, grumpy", 0, 0.2),
                        (3, TIG, "rolled_cry", "side", "rolled up in a straw mat, wailing", 0, 0.22),
                        (4, TIG, "swim", "front", "swimming away: head and paws above sea waves", 0, 0.2)],
    "cast_pj_helpers_a": [(i, "pj_" + h, "calm", "side" if h == "jara" else "front",
                           f"{HELP[h][0]}, calm sweet face", 1, None) for i, h in enumerate(HELP)],
    "cast_pj_helpers_b": [(0, "pj_bam", "act", "front", "chestnut leaping, fierce", 0, 0.1),
                          (1, "pj_jara", "act", "side", "turtle snapping 'ANG!' (faces right)", 0, 0.08),
                          (2, "pj_ddong", "act", "front", "dung squashed flat, cheeky", 0, 0.055),
                          (3, "pj_songgot", "act", "front", "awl jumping up, spike up", 0, 0.17),
                          (4, "pj_jeolgu", "act", "front", "mortar tumbling upside down", 0, 0.135),
                          (5, "pj_myeongseok", "act", "front", "straw mat unrolled flat, excited", 0, 0.1),
                          (6, "pj_jige", "act", "front", "carrier striding, proud", 0, 0.32)],
}
CYCLES = {
    "cast_pj_granny_walk": (GR, ["walk_cycle:4:side", "walk_back:2:back", "walk_front:2:front"]),
    "cast_pj_tiger_run": (TIG, ["run_cry_cycle:4:side", "run_cry_front:2:front"]),
}
# tiger sheet a has no calm standing figure: its two FRONT standing figures (eye_hurt, mouth_ouch) are the scale ref
REF_H = {("cast_pj_tiger_a", TIG): 0.42}


def clean_fringe_file(path):
    """The paper look's thin lit rims keep magenta-tinted edge pixels after keying (grey hair, straw): refill them
    from clean neighbours (tools/art/paper_swap.clean_fringe, alpha untouched)."""
    src = open(os.path.join(ROOT, "tools/art/paper_swap.py")).read()
    a = src.index("def clean_fringe")
    ns = {}
    exec("import numpy as np\nfrom PIL import Image\n" + src[a:src.index("\ndef ", a + 10)], ns)
    im = Image.open(path).convert("RGBA")
    out = ns["clean_fringe"](im)
    if out is not im:
        out.save(path, "WEBP", lossless=True, quality=100, method=6)


def opaque_h(path):
    a = np.array(Image.open(path).convert("RGBA"))[..., 3] > 128
    ys = np.where(a.any(1))[0]
    return float(ys[-1] - ys[0] + 1)


def main():
    new = []
    for sheet, rows in SHEETS.items():
        raw = f"art_src/cast/raw/{sheet}.png"
        if not os.path.exists(raw):
            print("missing", raw)
            continue
        if "--reslice" in sys.argv or not os.path.exists(f"art_src/cast/sliced/{sheet}/_slices.json"):
            subprocess.run([sys.executable, "tools/atlas/slice_atlas.py", raw, "--out", "art_src/cast/sliced"],
                           check=True, capture_output=True)
            subprocess.run([sys.executable, "tools/atlas/fill_holes.py", raw, f"art_src/cast/sliced/{sheet}"],
                           check=True, capture_output=True)
        n = len(json.load(open(f"art_src/cast/sliced/{sheet}/_slices.json"))["sprites"])
        if n != len(rows):
            print(f"WARN {sheet}: {n} pieces, table has {len(rows)}")
        role_scale = {}
        for role in {r[1] for r in rows}:
            rr = [r for r in rows if r[5] and r[1] == role]
            if rr:
                hh = REF_H.get((sheet, role), H[role])
                role_scale[role] = hh * len(rr) / sum(opaque_h(sliced_path(sheet, r[0], "x")) for r in rr)
        for x, role, pose, view, label, _, hx in rows:
            cid = f"cast_{role}_{pose}"
            dst = f"game/art/cast/{cid}.webp"
            src = sliced_path(sheet, x, "x")
            drop_specks(src, dst)
            clean_fringe_file(dst)
            w, h = Image.open(dst).size
            hu = hx if hx else round(opaque_h(dst) * role_scale[role], 3)
            new.append({"id": cid, "path": f"art/cast/{cid}.webp", "sheet": sheet, "category": "cast", "role": role,
                        "variant": pose, "pose": pose, "view": view,
                        "facing": "right" if view == "side" else view, "label": label,
                        "height_units": hu, "cross_slot": False, "biome": "any",
                        "season": "any", "tags": TAGS[role] + ["patjuk", pose, view], "px": [w, h],
                        "hanging": False, "skin": role, "parts": {}})
    ids = {e["id"] for e in new}
    cat = json.load(open("game/art/cast/catalog.json"))  # re-read right before writing (shared file)
    out = [e for e in cat if e["id"] not in ids] + new
    json.dump(out, open("game/art/cast/catalog.json", "w"), ensure_ascii=False, indent=1)
    print(len(new), "standing figures;", len(out), "cast cards")
    if "--cycles" in sys.argv:
        for sheet, (skin, plan) in CYCLES.items():
            if not os.path.exists(f"art_src/cast/raw/{sheet}.png"):
                print("missing", sheet)
                continue
            args = [sys.executable, "tools/cast/add_cycles.py", sheet, skin, *plan, "--h", "0.97", "--tag", "patjuk"]
            if "--noslice" in sys.argv:
                args.append("--noslice")
            subprocess.run(args, check=True)
            n = sum(int(q.split(":")[1]) for q in plan)
            for q in plan:
                cyc, k = q.split(":")[0], int(q.split(":")[1])
                for fr in range(k):
                    clean_fringe_file(f"game/art/cast/cast_{skin}_{cyc}_{fr}.webp")


if __name__ == "__main__":
    main()
