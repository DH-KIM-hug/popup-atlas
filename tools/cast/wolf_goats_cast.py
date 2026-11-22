#!/usr/bin/env python3
"""Shared cast for 「늑대와 일곱 아기염소」 (wolf_goats, 2026-11-23): a mother goat (walks upright, red apron), six kid
goats (one design, recoloured collars), the youngest kid, and new figures for the shared three_pigs wolf (chalk, the
floury paws, the full belly, the well, soaking wet). Generic animals, so they live in game/art/cast/ (skins goat_mom,
goat_kid_1 .. goat_kid_6, goat_baby; the wolf keeps skin "wolf").

  python3 tools/cast/wolf_goats_cast.py            # slice standing-figure sheets, copy, MERGE into catalog.json
  python3 tools/cast/wolf_goats_cast.py --cycles   # (--reslice to slice again; --noslice for cycles) + drawn cycles

Merging rules (never rebuild the catalog): replaces only entries of THIS builder's sheets (the wolf keeps every three_pigs
figure), pieces picked by x order, height = px x the sheet's per-role scale from its reference figures.
The kids: every kid sheet is drawn once with a plain GREEN collar (template skin goat_kid); each figure / cycle frame is
cloned into goat_kid_1..6 with the collar recoloured (hue swap on the green pixels, shading kept) and a per-kid height
(the eldest tallest); the template entries are removed afterwards.
Standing heights: mother 0.36, kid 0.17 (x 1.12 .. 0.94 per kid), youngest 0.14, wolf 0.40 (as in three_pigs).
"""
import colorsys, json, os, subprocess, sys
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from characters import sliced_path
from build_cast import drop_specks

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
os.chdir(ROOT)
MOM, KID, BABY, WOLF = "goat_mom", "goat_kid", "goat_baby", "wolf"
H = {MOM: 0.36, KID: 0.17, BABY: 0.14, WOLF: 0.40}
TAGS = {MOM: ["goat", "animal", "mother", "adult", "walker", "farm"],
        KID: ["goat", "kid_goat", "animal", "child", "walker", "farm"],
        BABY: ["goat", "kid_goat", "animal", "child", "youngest", "walker", "farm"],
        WOLF: ["wolf", "animal", "villain", "walker"]}
# kid n: (collar colour, height factor); kid 4 keeps the drawn green
KIDS = {1: ("#d8463c", 1.12), 2: ("#ee8a2e", 1.08), 3: ("#e3bd2f", 1.04), 4: (None, 1.0), 5: ("#3f7fd0", 0.97),
        6: ("#5156b8", 0.94)}
# sheet -> [(x index, role, pose, view, label, is_reference)]
SHEETS = {
    "cast_wg_lineup": [(0, MOM, "calm", "front", "calm, basket on her arm", 1),
                       (1, KID, "calm", "front", "calm, front", 1),
                       (2, KID, "side_walk", "side", "standing, side (faces right)", 1),
                       (3, BABY, "calm", "front", "calm, shy smile", 1)],
    "cast_wg_mom_expr": [(0, MOM, "warn", "front", "warning kindly, finger up, basket (늑대가 오면 문 열어 주면 안 돼!)", 1),
                         (1, MOM, "wave", "front", "waving goodbye, basket", 1),
                         (2, MOM, "shocked", "front", "shocked, hooves at cheeks", 1),
                         (3, MOM, "call", "front", "calling, hooves round her mouth (얘들아, 어디 있니?)", 1),
                         (4, MOM, "ready", "front", "brave, scissors and needle (엄마가 꼭 구해 줄게!)", 1),
                         (5, MOM, "dance", "front", "joyful dance, one leg up", 1)],
    "cast_wg_mom_views": [(0, MOM, "side_walk", "side", "standing, side, basket (faces right)", 1),
                          (1, MOM, "back_walk", "back", "standing, back view, basket", 1),
                          (2, MOM, "shush", "side", "tiptoe, shush, sewing basket (faces right)", 1),
                          (3, MOM, "kneel_cut", "side", "kneeling, working with scissors (faces right)", 0),
                          (4, MOM, "kneel_sew", "side", "kneeling, sewing with needle and red thread (faces right)", 0),
                          (5, MOM, "hug", "front", "kneeling, arms open for a hug", 0)],
    "cast_wg_kid_expr": [(0, KID, "hop", "side", "happy hop, leaping (faces right)", 0),
                         (1, KID, "scared", "front", "scared, trembling", 1),
                         (2, KID, "suspicious", "front", "suspicious frown (우리 엄마가 아니야!)", 1),
                         (3, KID, "shout", "front", "shouting (저리 가요, 늑대!)", 1),
                         (4, KID, "joy", "front", "overjoyed, eyes closed (엄마다!)", 1),
                         (5, KID, "dance", "front", "dancing on hind legs", 0)],
    "cast_wg_kid_views": [(0, KID, "back_walk", "back", "standing, back view", 1),
                          (1, KID, "scared_side", "side", "scared, crouched (faces right)", 0),
                          (2, KID, "push", "side", "pushing with head down (faces right)", 0),
                          (3, KID, "look_up", "front", "looking up happily", 1),
                          (4, KID, "sit", "front", "sitting, attentive", 0),
                          (5, KID, "pop", "side", "springing up, 'mama!' (faces right)", 0)],
    "cast_wg_baby_expr": [(0, BABY, "worried", "front", "looking around, worried", 1),
                          (1, BABY, "cry", "front", "crying (훌쩍훌쩍)", 1),
                          (2, BABY, "joy_jump", "side", "joy jump (엄마!) (faces right)", 0),
                          (3, BABY, "whisper", "front", "whispering (조심조심이요)", 1),
                          (4, BABY, "back_walk", "back", "standing, back view", 1),
                          (5, BABY, "side_walk", "side", "standing, side (faces right)", 1)],
    "cast_wg_wolf_a": [(0, WOLF, "knock", "side", "knocking, fist raised (faces right)", 1),
                       (1, WOLF, "munch", "front", "munching chalk (와작와작)", 1),
                       (2, WOLF, "sweet", "front", "fake sweet voice, paws clasped (문 열어 줘~)", 1),
                       (3, WOLF, "paw_show", "side", "crouching, white floury paw out (faces right)", 0),
                       (4, WOLF, "sneeze", "front", "sneezing, white floury paws (에취!)", 1),
                       (5, WOLF, "search", "front", "sniffing, white paws up (다 찾아낼 테다!)", 1)],
    "cast_wg_wolf_b": [(0, WOLF, "sleep_full", "side", "asleep on his back, huge full belly (head left)", 0),
                       (1, WOLF, "sleep_stones", "side", "asleep, lumpy belly stitched shut (head left)", 0),
                       (2, WOLF, "groggy", "front", "sitting up groggy, holding his heavy belly", 0),
                       (3, WOLF, "peer_well", "side", "leaning over the well rim, thirsty (faces right)", 0),
                       (4, WOLF, "tumble", "front", "tumbling head first (into the well)", 0),
                       (5, WOLF, "wet", "front", "soaking wet, dripping, shocked", 1)],
}
CYCLES = {
    "cast_wg_mom_walk": (MOM, ["walk_cycle:4:side", "walk_back:2:back", "walk_front:2:front"]),
    "cast_wg_kid_walk": (KID, ["walk_cycle:4:side", "walk_back:2:back", "walk_front:2:front"]),
    "cast_wg_kid_run": (KID, ["run_cycle:4:side", "run_back:2:back"]),
    "cast_wg_baby_walk": (BABY, ["walk_cycle:4:side", "walk_back:2:back", "walk_front:2:front"]),
    "cast_wg_baby_run": (BABY, ["run_cycle:4:side", "run_back:2:back"]),
    "cast_wg_wolf_flour_walk": (WOLF, ["flour_cycle:4:side", "flour_back:2:back", "flour_front:2:front"]),
    "cast_wg_wolf_heavy_walk": (WOLF, ["heavy_cycle:4:side", "heavy_back:2:back", "heavy_front:2:front"]),
    "cast_wg_wolf_wet_run": (WOLF, ["wet_cycle:4:side", "wet_back:2:back"]),
}
CYCLE_H = {MOM: 0.97, KID: 0.97, BABY: 0.97, WOLF: 0.97}
# sheets without a standing reference for a role: the median figure of that role is this fraction of its standing height
NOREF = {"cast_wg_wolf_b": 0.95}
# a lying wolf is much lower than he is tall: its height from the sheet's wet (standing) figure scale (pieces are
# picked among all pieces by x, not only the tall ones)
X_ALL = {"cast_wg_wolf_b"}


def split_wide(sheet):
    """Cycle frames drawn close together slice as one piece (cast_wg_baby_walk: the two back frames): split every piece
    wider than 1.5x the median at its emptiest column in the middle third (in art_src/cast/slices/<sheet>)."""
    d = f"art_src/cast/slices/{sheet}"
    meta = json.load(open(f"{d}/_slices.json"))
    sl = meta["sprites"]
    med = sorted(m["size"][0] for m in sl)[len(sl) // 2]
    out = []
    for m in sl:
        if m["size"][0] < 1.5 * med:
            out.append(m)
            continue
        im = np.array(Image.open(f"{d}/{m['id']}.webp").convert("RGBA"))
        w = im.shape[1]
        col = (im[..., 3] > 40).sum(0)
        lo, hi = w // 3, 2 * w // 3
        cx = lo + int(np.argmin(col[lo:hi]))
        for k, (a, b) in enumerate([(0, cx), (cx, w)]):
            part = im[:, a:b].copy()
            xs = np.where((part[..., 3] > 0).any(0))[0]
            part = part[:, max(0, xs[0] - 4):xs[-1] + 5]
            nid = f"{m['id']}{'ab'[k]}"
            Image.fromarray(part).save(f"{d}/{nid}.webp", "WEBP", lossless=True, quality=100, method=6)
            x0 = int(m["bbox"][0] + a + max(0, int(xs[0]) - 4))
            out.append({**m, "id": nid, "bbox": [x0, m["bbox"][1], x0 + part.shape[1], m["bbox"][3]],
                        "size": [int(part.shape[1]), int(part.shape[0])]})
        os.remove(f"{d}/{m['id']}.webp")
        print("split", sheet, m["id"], "at", cx)
    meta["sprites"] = out
    json.dump(meta, open(f"{d}/_slices.json", "w"), indent=1)


def opaque_h(path):
    a = np.array(Image.open(path).convert("RGBA"))[..., 3] > 128
    ys = np.where(a.any(1))[0]
    return float(ys[-1] - ys[0] + 1)


def piece(sheet, x):
    if sheet in X_ALL:
        sl = json.load(open(f"art_src/cast/sliced/{sheet}/_slices.json"))["sprites"]
        big = sorted((m for m in sl if m["area"] > 0.08 * max(q["area"] for q in sl)), key=lambda m: m["bbox"][0])
        return f"art_src/cast/sliced/{sheet}/{big[x]['id']}.webp"
    return sliced_path(sheet, x, "x")


def recolour(src, dst, hexcol):
    """Green collar -> hexcol (hue + saturation of the target, the drawn value shading kept)."""
    im = np.array(Image.open(src).convert("RGBA")).astype(float) / 255.0
    rgb = im[..., :3]
    mx, mn = rgb.max(-1), rgb.min(-1)
    s = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    g = rgb[..., 1]
    green = (g >= mx - 1e-6) & (s > 0.3) & (mx > 0.2) & (rgb[..., 1] - rgb[..., 0] > 0.12) & (im[..., 3] > 0)
    if hexcol:
        tr, tg, tb = (int(hexcol[i:i + 2], 16) / 255.0 for i in (1, 3, 5))
        th, ts, tv = colorsys.rgb_to_hsv(tr, tg, tb)
        ys, xs = np.where(green)
        ref_v = np.median(mx[green]) if green.any() else 1.0
        for y, x in zip(ys, xs):
            v = min(1.0, tv * mx[y, x] / max(ref_v, 1e-6))
            im[y, x, :3] = colorsys.hsv_to_rgb(th, ts * min(1.0, s[y, x] / 0.55), v)
    Image.fromarray((im * 255).clip(0, 255).astype(np.uint8)).save(dst, "WEBP", lossless=True, quality=100, method=6)
    return int(green.sum())


def clone_kids(cat):
    """goat_kid template entries -> goat_kid_1..6 (recoloured files, per-kid heights); template entries removed."""
    tmpl = [e for e in cat if e.get("skin") == KID]
    out = [e for e in cat if e.get("skin") != KID and not str(e.get("skin", "")).startswith(KID + "_")]
    for n, (col, hf) in KIDS.items():
        for e in tmpl:
            skin = f"{KID}_{n}"
            cid = e["id"].replace(f"cast_{KID}_", f"cast_{skin}_")
            dst = f"game/art/cast/{cid}.webp"
            recolour("game/" + e["path"], dst, col)
            q = dict(e)
            q.update({"id": cid, "path": f"art/cast/{cid}.webp", "role": skin, "skin": skin,
                      "height_units": round(e["height_units"] * hf, 3),
                      "tags": sorted(set(e["tags"] + [skin])), "label": e["label"] + f" (kid {n})"})
            out.append(q)
    for e in tmpl:  # the green template files are not shipped
        p = "game/" + e["path"]
        for f in (p, p + ".import"):
            if os.path.exists(f):
                os.remove(f)
    return out


def main():
    cat = json.load(open("game/art/cast/catalog.json"))
    mine = set(SHEETS) | set(CYCLES)
    keep = [e for e in cat if not (e.get("sheet") in SHEETS)]
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
        refs = [r for r in rows if r[5]]
        role_scale = {}
        for role in {r[1] for r in rows}:
            rr = [r for r in refs if r[1] == role]
            if rr:
                role_scale[role] = H[role] * len(rr) / sum(opaque_h(piece(sheet, r[0])) for r in rr)
        for x, role, pose, view, label, _ in rows:
            cid = f"cast_{role}_{pose}"
            dst = f"game/art/cast/{cid}.webp"
            drop_specks(piece(sheet, x), dst)
            w, h = Image.open(dst).size
            sc = role_scale.get(role)
            if sc is None:
                hs = sorted(opaque_h(piece(sheet, r[0])) for r in rows if r[1] == role)
                sc = H[role] * NOREF.get(sheet, 1.0) / hs[len(hs) // 2]
                role_scale[role] = sc
            new.append({"id": cid, "path": f"art/cast/{cid}.webp", "sheet": sheet, "category": "cast", "role": role,
                        "variant": pose, "pose": pose, "view": view,
                        "facing": "right" if view == "side" else view, "label": label,
                        "height_units": round(opaque_h(dst) * sc, 3), "cross_slot": False, "biome": "any",
                        "season": "any", "tags": TAGS[role] + ["wolf_goats", pose, view], "px": [w, h],
                        "hanging": False, "skin": role, "parts": {}})
    # the kid template must exist before its cycles (add_cycles reads cast_goat_kid_calm): drop old clones first (the
    # green kid 4's cycle frames are kept aside: without --cycles they are the template's cycles again)
    k4 = [e for e in cat if e.get("skin") == f"{KID}_4" and e.get("cycle")]
    cat = [e for e in keep if not str(e.get("skin", "")).startswith(KID + "_")] + new
    only0 = sys.argv[sys.argv.index("--only") + 1].split(",") if "--only" in sys.argv else list(CYCLES)
    cat = [e for e in cat if not (e.get("sheet") in only0 and "--cycles" in sys.argv)]
    json.dump(cat, open("game/art/cast/catalog.json", "w"), ensure_ascii=False, indent=1)
    print(len(new), "standing figures")
    if "--cycles" in sys.argv:
        only = sys.argv[sys.argv.index("--only") + 1].split(",") if "--only" in sys.argv else list(CYCLES)
        for sheet, (skin, plan) in CYCLES.items():
            if sheet not in only:
                continue
            if not os.path.exists(f"art_src/cast/raw/{sheet}.png"):
                print("missing", sheet)
                continue
            if "--noslice" not in sys.argv:  # slice here so merged frames can be split before cataloguing
                subprocess.run([sys.executable, "tools/atlas/slice_atlas.py", f"art_src/cast/raw/{sheet}.png", "--out",
                                "art_src/cast/slices"], check=True, capture_output=True)
                split_wide(sheet)
            args = [sys.executable, "tools/cast/add_cycles.py", sheet, skin, *plan, "--h", str(CYCLE_H[skin]),
                    "--tag", "wolf_goats", "--noslice"]
            subprocess.run(args, check=True)
    cat = json.load(open("game/art/cast/catalog.json"))
    if "--cycles" not in sys.argv:  # the kid cycles already made: back into the template from kid 4 (green)
        for e in k4:
            q = dict(e)
            q.update({"id": e["id"].replace(f"cast_{KID}_4_", f"cast_{KID}_"), "role": KID, "skin": KID,
                      "height_units": e["height_units"]})
            q["path"] = f"art/cast/{q['id']}.webp"
            Image.open("game/" + e["path"]).save("game/" + q["path"], "WEBP", lossless=True, quality=100, method=6)
            cat.append(q)
    cat = clone_kids(cat)
    json.dump(cat, open("game/art/cast/catalog.json", "w"), ensure_ascii=False, indent=1)
    print("cast cards", len(cat), "kids", sum(1 for e in cat if str(e.get("skin", "")).startswith(KID + "_")))


if __name__ == "__main__":
    main()
