#!/usr/bin/env python3
"""Shared cast for 「라푼젤」 (rapunzel, 2026-11-23): Rapunzel (long braid + short-hair figures in one skin), the witch
Gothel, the prince, a peasant father and an expecting mother. Generic fairy-tale folk, so they live in game/art/cast/
(skins rapunzel, gothel, prince, peasant_father, peasant_mother) for later tales.

  python3 tools/cast/rapunzel_cast.py            # slice standing-figure sheets, copy, MERGE into catalog.json
  python3 tools/cast/rapunzel_cast.py --cycles   # (--reslice to slice again) also the drawn cycles (add_cycles.py)

Same rules as tools/cast/turnip_cast.py: replaces only standing entries whose skin is one of ROLES (never rebuilds the
catalog; drawn cycles are kept), pieces picked by x order, height = px x the sheet's per-role scale from its reference
figures. The catalog is re-read right before it is written (other agents write it too).
Window figures (win_*: the upper body leaning on a sill, cut flat at the waist) stand in the tower window; climb_cycle
(two back-view frames hanging on the braid) is a flipbook the actor plays while it climbs (story_actor: climbing).
"""
import json, os, subprocess, sys
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from characters import SLICED
from build_cast import drop_specks

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
os.chdir(ROOT)
RAP, GO, PR, FA, MO = "rapunzel", "gothel", "prince", "peasant_father", "peasant_mother"
H = {RAP: 0.25, GO: 0.27, PR: 0.3, FA: 0.3, MO: 0.28}
ROLES = set(H)
TAGS = {RAP: ["rapunzel", "girl", "person", "child", "western", "walker", "braid"],
        GO: ["witch", "old_woman", "person", "adult", "western", "walker"],
        PR: ["prince", "person", "young_man", "royal", "western", "walker"],
        FA: ["father", "man", "peasant", "person", "adult", "western", "walker"],
        MO: ["mother", "woman", "peasant", "person", "adult", "western"]}

SHEETS = {
    "cast_rp_rap_expr": [(0, RAP, "calm", "front", "calm, long golden braid over one shoulder", 1),
                         (1, RAP, "sing", "front", "singing, hands clasped, eyes closed", 1),
                         (2, RAP, "surprised", "front", "surprised, hands at her cheeks", 1),
                         (3, RAP, "joy", "front", "joyful, arms open", 1),
                         (4, RAP, "chatty", "front", "innocent, chatty, finger at her chin", 1),
                         (5, RAP, "sad", "front", "sad, holding her braid", 1),
                         (6, RAP, "wave", "front", "waving", 1)],
    "cast_rp_rap_short": [(0, RAP, "short_sad", "front", "short hair: sad, touching her hair", 0),
                          (1, RAP, "short_sing", "front", "short hair: singing", 0),
                          (2, RAP, "short_joy", "front", "short hair: surprised-joyful", 0),
                          (3, RAP, "short_hold", "side", "short hair: holding out a hand (faces right)", 0),
                          (4, RAP, "short_happy", "front", "short hair: happy, arms open", 0),
                          (5, RAP, "side_walk", "side", "short hair: standing, side (faces right)", 0),
                          (6, RAP, "back_walk", "back", "short hair: standing, back view", 0),
                          (7, RAP, "short_calm", "front", "short hair: calm", 0)],
    "cast_rp_rap_window": [(0, RAP, "win_smile", "front", "at the window (upper body on the sill): smiling", 0),
                           (1, RAP, "win_sing", "front", "at the window: singing", 0),
                           (2, RAP, "win_letdown", "front", "at the window: letting her braid down", 0),
                           (3, RAP, "win_surprised", "front", "at the window: surprised", 0),
                           (4, RAP, "win_wave", "front", "at the window: waving", 0)],
    "cast_rp_gothel_expr": [(0, GO, "calm", "front", "calm, hands on her stick", 1),
                            (1, GO, "point", "front", "pointing, scolding", 1),
                            (2, GO, "wand", "front", "stick raised, a star at its tip", 1),
                            (3, GO, "cradle", "front", "cradling a swaddled baby", 1),
                            (4, GO, "scissors", "front", "big scissors raised", 1),
                            (5, GO, "cross", "front", "startled and cross, hands up", 1),
                            (6, GO, "side_walk", "side", "standing, side (faces right)", 1),
                            (7, GO, "back_walk", "back", "standing, back view", 1)],
    "cast_rp_gothel_more": [(2, GO, "talk", "front", "stern talk, palm up", 1),
                            (3, GO, "smug", "front", "arms folded, small smirk", 1)],
    "cast_rp_gothel_window": [(0, GO, "win_stern", "front", "at the window: stern, scolding", 0),
                              (1, GO, "win_wand", "front", "at the window: stick raised", 0)],
    "cast_rp_prince_expr": [(0, PR, "calm", "front", "calm, friendly", 1),
                            (1, PR, "call", "front", "calling up, hands cupped", 1),
                            (2, PR, "listen", "front", "listening, hand at his ear", 1),
                            (3, PR, "delighted", "front", "delighted discovery, fist up", 1),
                            (4, PR, "hide", "side", "hiding, crouched, finger at lips (faces right)", 0),
                            (5, PR, "sad", "front", "sad", 1),
                            (6, PR, "happy", "front", "happy, arms open", 1),
                            (7, PR, "hold", "side", "holding out a hand (faces right)", 1)],
    "cast_rp_prince_more": [(2, PR, "side_walk", "side", "standing, side (faces right)", 1),
                            (3, PR, "back_walk", "back", "standing, back view", 1),
                            (4, PR, "float", "front", "floating gently, arms spread", 0),
                            (5, PR, "look_up", "front", "looking up, shading his eyes", 1)],
    "cast_rp_father_expr": [(0, FA, "calm", "front", "calm, kind", 1),
                            (1, FA, "promise", "front", "promising, fist at his chest", 1),
                            (2, FA, "pull", "side", "pulling a plant out (faces right)", 0),
                            (3, FA, "shock", "front", "shocked, hands up", 1),
                            (4, FA, "sorry", "front", "sorry, hands together", 1),
                            (5, FA, "side_walk", "side", "tiptoeing, side (faces right)", 0)],
    "cast_rp_mother_expr": [(0, MO, "calm", "front", "calm, hands on her tummy", 1),
                            (1, MO, "longing", "front", "longing, hands under her chin", 1),
                            (2, MO, "happy", "front", "happy, hands at her cheeks", 1),
                            (3, MO, "sad", "front", "sad", 1)],
}
# sheets without a full standing reference figure: the median piece is this fraction of the role's standing height
NOREF = {"cast_rp_rap_short": 1.0, "cast_rp_rap_window": 0.5, "cast_rp_gothel_window": 0.5}
# the climb frames (back view, arms up): two-frame flipbooks, padded to one canvas
CLIMB = {"cast_rp_gothel_more": (GO, [0, 1]), "cast_rp_prince_more": (PR, [0, 1])}
WALK = ["walk_cycle:4:side", "walk_back:2:back", "walk_front:2:front"]
CYCLES = {
    "cast_rp_rap_short_walk": (RAP, WALK), "cast_rp_gothel_walk": (GO, WALK), "cast_rp_prince_walk": (PR, WALK),
    "cast_rp_prince_run": (PR, ["run_cycle:4:side", "run_front:2:front"]), "cast_rp_father_walk": (FA, WALK),
}


def sliced_path(sheet, idx):
    """idx-th piece from the left among the real figures (specks under 1.5 % of the largest area are skipped)."""
    sl = json.load(open(os.path.join(SLICED, sheet, "_slices.json")))["sprites"]
    amax = max(m["size"][0] * m["size"][1] for m in sl)
    big = sorted((m for m in sl if m["size"][0] * m["size"][1] > 0.015 * amax), key=lambda m: m["bbox"][0])
    return os.path.join(SLICED, sheet, big[idx]["id"] + ".webp")


def opaque_h(path):
    a = np.array(Image.open(path).convert("RGBA"))[..., 3] > 128
    ys = np.where(a.any(1))[0]
    return float(ys[-1] - ys[0] + 1)


def _slice(sheet):
    raw = f"art_src/cast/raw/{sheet}.png"
    if "--reslice" in sys.argv or not os.path.exists(f"{SLICED}/{sheet}/_slices.json"):
        subprocess.run([sys.executable, "tools/atlas/slice_atlas.py", raw, "--out", SLICED], check=True,
                       capture_output=True)
        subprocess.run([sys.executable, "tools/atlas/fill_holes.py", raw, f"{SLICED}/{sheet}"], check=True,
                       capture_output=True)


def entry(cid, sheet, role, pose, view, label, h, px, extra=None):
    e = {"id": cid, "path": f"art/cast/{cid}.webp", "sheet": sheet, "category": "cast", "role": role,
         "variant": pose, "pose": pose, "view": view, "facing": "right" if view == "side" else view, "label": label,
         "height_units": round(h, 3), "cross_slot": False, "biome": "any", "season": "any",
         "tags": TAGS[role] + ["rapunzel", pose, view], "px": px, "hanging": False, "skin": role, "parts": {}}
    if extra:
        e.update(extra)
    return e


def main():
    new = []
    scale_of = {}
    for sheet, rows in SHEETS.items():
        if not os.path.exists(f"art_src/cast/raw/{sheet}.png"):
            print("missing", sheet)
            continue
        _slice(sheet)
        refs = [r for r in rows if r[5]]
        role_scale = {}
        for role in {r[1] for r in rows}:
            rr = [r for r in refs if r[1] == role]
            if rr:
                role_scale[role] = H[role] * len(rr) / sum(opaque_h(sliced_path(sheet, r[0])) for r in rr)
        for x, role, pose, view, label, _ in rows:
            cid = f"cast_{role}_{pose}"
            dst = f"game/art/cast/{cid}.webp"
            drop_specks(sliced_path(sheet, x), dst)
            w, h = Image.open(dst).size
            sc = role_scale.get(role)
            if sc is None:
                hs = sorted(opaque_h(sliced_path(sheet, r[0])) for r in rows if r[1] == role)
                sc = H[role] * NOREF.get(sheet, 1.0) / hs[len(hs) // 2]
                role_scale[role] = sc
            new.append(entry(cid, sheet, role, pose, view, label, opaque_h(dst) * sc, [w, h]))
        scale_of[sheet] = role_scale
    # climb flipbooks: scale from the sheet's standing front figures
    for sheet, (role, idx) in CLIMB.items():
        _slice(sheet)
        sc = scale_of.get(sheet, {}).get(role) or H[role] / opaque_h(sliced_path(sheet, 2))
        ims = [Image.open(sliced_path(sheet, i)).convert("RGBA") for i in idx]
        W, Hh = max(i.width for i in ims), max(i.height for i in ims)
        for f, im in enumerate(ims):
            c = Image.new("RGBA", (W, Hh), (0, 0, 0, 0))
            c.alpha_composite(im, ((W - im.width) // 2, Hh - im.height))
            cid = f"cast_{role}_climb_cycle_{f}"
            c.save(f"game/art/cast/{cid}.webp", "WEBP", lossless=True, quality=100, method=6)
            new.append(entry(cid, sheet, role, f"climb_cycle_{f}", "back", f"climbing the braid, frame {f} (back view)",
                             Hh * sc, [W, Hh], {"cycle": "climb_cycle", "frame": f,
                                                 "tags": TAGS[role] + ["rapunzel", "cycle", "climb"]}))
    cat = json.load(open("game/art/cast/catalog.json"))
    ids = {e["id"] for e in new}
    keep = [e for e in cat if not (e.get("role") in ROLES and not e.get("cycle")) and e["id"] not in ids]
    json.dump(keep + new, open("game/art/cast/catalog.json", "w"), ensure_ascii=False, indent=1)
    print(len(new), "figures;", len(keep) + len(new), "cast cards")
    if "--cycles" in sys.argv:
        for sheet, (skin, plan) in CYCLES.items():
            if not os.path.exists(f"art_src/cast/raw/{sheet}.png"):
                print("missing", sheet)
                continue
            args = [sys.executable, "tools/cast/add_cycles.py", sheet, skin, *plan, "--h", "0.97", "--tag", "rapunzel_tale"]  # (not "rapunzel": add_cycles removes the first arg equal to the tag, the skin)
            if "--noslice" in sys.argv:
                args.append("--noslice")
            subprocess.run(args, check=True)


if __name__ == "__main__":
    main()
