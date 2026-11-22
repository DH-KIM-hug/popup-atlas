#!/usr/bin/env python3
"""Shared cast for 「해님 달님」 (sunmoon, 2026-11-22): a hanbok brother and sister, their mother, a children's-book tiger
(with his disguise in the mother's clothes) and a rich lady; plus the sun / moon faces. Generic Joseon-era people and a
tiger, so they live in game/art/cast/ (skins hanbok_boy, hanbok_girl, hanbok_mom, tiger, rich_lady, sunmoon_sky).

  python3 tools/cast/sunmoon_cast.py            # slice standing-figure sheets, copy, MERGE into catalog.json
  python3 tools/cast/sunmoon_cast.py --cycles   # (--reslice to slice again) also the drawn cycles (add_cycles.py)

Same rules as tools/cast/witch_candy_cast.py: replaces only entries whose role is one of ROLES (never rebuilds the
catalog), pieces picked by x order, height = px × the sheet's per-role scale from its reference figures.
Standing heights: brother 0.25, sister 0.235, mother 0.36, tiger 0.44 (upright), rich lady 0.355; sun / moon discs 0.6.
Climbing / rope / treetop / falling figures are single cards flipped A <-> B by the tale handler (no rig).
"""
import json, os, subprocess, sys
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from characters import sliced_path
from build_cast import drop_specks

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
os.chdir(ROOT)
BOY, GIRL, MOM, TIG, RICH, SKY = "hanbok_boy", "hanbok_girl", "hanbok_mom", "tiger", "rich_lady", "sunmoon_sky"
H = {BOY: 0.25, GIRL: 0.235, MOM: 0.36, TIG: 0.44, RICH: 0.355, SKY: 0.6}
ROLES = set(H)
TAGS = {BOY: ["boy", "person", "child", "hanbok", "korean_traditional", "walker"],
        GIRL: ["girl", "person", "child", "hanbok", "korean_traditional", "walker"],
        MOM: ["woman", "person", "adult", "mother", "hanbok", "korean_traditional", "walker"],
        TIG: ["tiger", "animal", "korean_traditional", "villain", "walker"],
        RICH: ["woman", "person", "adult", "hanbok", "korean_traditional"],
        SKY: ["sun", "moon", "sky", "face"]}
# sheet -> [(x index, role, pose, view, label, is_reference)]
SHEETS = {
    "cast_sm_lineup": [(0, BOY, "calm", "front", "calm, front", 1), (1, GIRL, "calm", "front", "calm, front", 1),
                       (2, MOM, "calm", "front", "calm, empty basket in both hands", 1),
                       (3, TIG, "calm", "front", "standing upright, paws on belly, sly grin", 1),
                       (4, RICH, "calm", "front", "calm, hands folded", 1)],
    "cast_sm_boy_expr": [(0, BOY, "wave", "front", "waving goodbye (다녀오세요!)", 1),
                         (1, BOY, "scared", "front", "scared, fists at chest", 1),
                         (2, BOY, "shush", "front", "finger at lips (쉿!)", 1),
                         (3, BOY, "clever", "front", "clever grin, finger up (참기름!)", 1),
                         (4, BOY, "pray", "front", "praying, looking up (하늘님)", 1),
                         (5, BOY, "giggle", "front", "giggling, hands over mouth", 1)],
    "cast_sm_girl_expr": [(0, GIRL, "wave", "front", "waving goodbye", 1),
                          (1, GIRL, "scared", "front", "scared, hugging herself (오빠, 무서워)", 1),
                          (2, GIRL, "blurt", "front", "laughing, blurting it out (도끼로!)", 1),
                          (3, GIRL, "shy", "front", "shy, afraid of the dark", 1),
                          (4, GIRL, "giggle", "front", "giggling, hands over mouth", 1),
                          (5, GIRL, "wow", "front", "wow, hands at cheeks", 1)],
    "cast_sm_kids_views": [(0, BOY, "side_walk", "side", "standing, side (faces right)", 1),
                           (1, BOY, "back_walk", "back", "standing, back view", 1),
                           (2, GIRL, "side_walk", "side", "standing, side (faces right)", 1),
                           (3, GIRL, "back_walk", "back", "standing, back view", 1),
                           (4, BOY, "pair_hold", "front", "brother and sister holding hands (pair card)", 0)],
    "cast_sm_climb": [(0, BOY, "climb_a", "back", "climbing a trunk, from behind (frame A)", 0),
                      (1, BOY, "climb_b", "back", "climbing a trunk, from behind (frame B)", 0),
                      (2, GIRL, "climb_a", "back", "climbing a trunk, from behind (frame A)", 0),
                      (3, GIRL, "climb_b", "back", "climbing a trunk, from behind (frame B)", 0),
                      (4, BOY, "rope_a", "front", "climbing a rope (frame A)", 0),
                      (5, BOY, "rope_b", "front", "climbing a rope (frame B)", 0),
                      (6, GIRL, "rope_a", "front", "climbing a rope (frame A)", 0),
                      (7, GIRL, "rope_b", "front", "climbing a rope (frame B)", 0)],
    "cast_sm_treetop": [(0, BOY, "sit_hold", "front", "sitting on a branch, arm round his sister", 0),
                        (1, GIRL, "sit_scared", "front", "sitting on a branch, scared", 0),
                        (2, BOY, "sit_giggle", "front", "sitting on a branch, giggling", 0),
                        (3, GIRL, "sit_giggle", "front", "sitting on a branch, giggling", 0)],
    "cast_sm_mom_expr": [(0, MOM, "wave", "front", "waving goodbye, empty basket on arm", 1),
                         (1, MOM, "talk", "front", "finger up, reminding (문 꼭 잠그고)", 1),
                         (2, MOM, "work", "front", "working: stirring a pot, sleeves rolled", 0),
                         (3, MOM, "happy_full", "front", "hugging the full basket of rice cakes", 1),
                         (4, MOM, "scared_full", "front", "frightened, clutching the basket", 1),
                         (5, MOM, "give", "front", "holding out one rice cake, nervous", 1)],
    "cast_sm_mom_views": [(0, MOM, "side_walk", "side", "standing, side, full basket (faces right)", 1),
                          (1, MOM, "back_walk", "back", "standing, back view, basket", 1),
                          (2, MOM, "tired_full", "front", "tired but glad, full basket", 1),
                          (3, MOM, "hurry", "side", "hurrying, empty basket (faces right)", 0)],
    "cast_sm_rich_expr": [(0, RICH, "smile", "front", "kind smile", 1),
                          (1, RICH, "give_tray", "front", "holding out a tray of rice cakes (to the left)", 1),
                          (2, RICH, "thanks", "front", "thanking, hand up (수고했어요)", 1),
                          (3, RICH, "side_walk", "side", "standing, side (faces right)", 1)],
    "cast_sm_tiger_expr_a": [(0, TIG, "roar", "front", "roar 어흥! (silly, paws up)", 1),
                             (1, TIG, "demand", "front", "demanding, paw out (떡 주면 안 잡아먹지)", 1),
                             (2, TIG, "gulp", "front", "gulping a rice cake, eyes closed", 1),
                             (3, TIG, "belly1", "front", "belly bigger, satisfied", 1),
                             (4, TIG, "belly2", "front", "belly huge, dizzy happy", 1),
                             (5, TIG, "sly", "front", "sly, paw at chin", 1)],
    "cast_sm_tiger_expr_b": [(0, TIG, "search", "front", "searching, paw shading eyes (어디 갔니?)", 1),
                             (1, TIG, "look_up", "front", "looking up surprised (위에서 웃음소리가?)", 1),
                             (2, TIG, "whisper", "front", "sneaky, paw at mouth", 1),
                             (3, TIG, "side_walk", "side", "standing upright, side (faces right)", 1),
                             (4, TIG, "back_walk", "back", "standing upright, back view", 1),
                             (5, TIG, "dazed", "front", "sitting dazed, bump on the head, stars", 0)],
    "cast_sm_tiger_disguise": [(0, TIG, "dg_calm", "front", "disguised as the mother: fake sweet smile", 1),
                               (1, TIG, "dg_knock", "front", "disguised: knocking (똑똑똑)", 1),
                               (2, TIG, "dg_sweet", "front", "disguised: fake sweet voice (엄마 왔다~)", 1),
                               (3, TIG, "dg_side", "side", "disguised: standing, side (faces right)", 1),
                               (4, TIG, "dg_back", "back", "disguised: back view", 1),
                               (5, TIG, "dg_caught", "front", "disguised: caught, headscarf slipping", 1)],
    "cast_sm_tiger_tree": [(0, TIG, "peer_well", "side", "peering into the well (faces right)", 0),
                           (1, TIG, "pull_rope", "side", "pulling the bucket rope (faces right)", 0),
                           (2, TIG, "smear_oil", "side", "smearing sesame oil, bottle in paw (faces right)", 0),
                           (3, TIG, "slip", "side", "slipping down the trunk (faces right)", 0),
                           (4, TIG, "axe_a", "side", "climbing with an axe, axe high (frame A)", 0),
                           (5, TIG, "axe_b", "side", "climbing with an axe, axe low (frame B)", 0)],
    "cast_sm_tiger_rope": [(0, TIG, "grab_up", "front", "grabbing up eagerly (나도 올라가야지!)", 0),
                           (1, TIG, "rope_a", "back", "climbing a rope, from behind (frame A)", 0),
                           (2, TIG, "rope_b", "back", "climbing a rope, from behind (frame B)", 0),
                           (3, TIG, "falling", "front", "falling upside down with a snapped rope bit", 0),
                           (4, TIG, "run_bump", "side", "running away with a bump (faces right)", 0)],
    "cast_sm_sunmoon": [(0, SKY, "sun_boy", "front", "the sun with the brother's face", 1),
                        (1, SKY, "moon_girl", "front", "the moon with the sister's face", 1),
                        (2, SKY, "sun_girl", "front", "the sun with the sister's face, beaming", 1),
                        (3, SKY, "moon_boy", "front", "the moon with the brother's face, gentle", 1)],
    # 2026-11-22 paper look test (user: "펠트 질감 싫은뎅"): the same designs as cut paper, no stitching
    "cast_sm_paper_mom": [(0, MOM, "paper_calm", "front", "PAPER look test: calm, full basket", 1)],
    "cast_sm_paper_tiger": [(0, TIG, "paper_calm", "front", "PAPER look test: standing upright, sly grin", 1)],
    "cast_sm_paper_girl": [(0, GIRL, "paper_calm", "front", "PAPER look test: calm", 1)],
}
CYCLES = {
    "cast_sm_boy_walk": (BOY, ["walk_cycle:4:side", "walk_back:2:back", "walk_front:2:front"]),
    "cast_sm_girl_walk": (GIRL, ["walk_cycle:4:side", "walk_back:2:back", "walk_front:2:front"]),
    "cast_sm_mom_walk": (MOM, ["walk_cycle:4:side", "walk_back:2:back", "walk_front:2:front"]),
    "cast_sm_tiger_walk": (TIG, ["walk_cycle:4:side", "walk_back:2:back", "walk_front:2:front"]),
    "cast_sm_boy_run": (BOY, ["run_cycle:4:side", "run_back:2:back"]),
    "cast_sm_girl_run": (GIRL, ["run_cycle:4:side", "run_back:2:back"]),
    "cast_sm_tiger_sneak": (TIG, ["dg_cycle:4:side", "dg_front:2:front"]),
}
CYCLE_H = {}
# sheets without a standing reference: the median figure of a role on the sheet is this fraction of its standing height
NOREF = {"cast_sm_climb": 1.0, "cast_sm_treetop": 0.8, "cast_sm_tiger_tree": 0.92, "cast_sm_tiger_rope": 1.0}


def opaque_h(path):
    a = np.array(Image.open(path).convert("RGBA"))[..., 3] > 128
    ys = np.where(a.any(1))[0]
    return float(ys[-1] - ys[0] + 1)


def main():
    cat = json.load(open("game/art/cast/catalog.json"))
    keep = [e for e in cat if not (e.get("role") in ROLES and not e.get("cycle"))]
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
        refs = [r for r in rows if r[5]]
        role_scale = {}
        for role in {r[1] for r in rows}:
            rr = [r for r in refs if r[1] == role]
            if rr:
                role_scale[role] = H[role] * len(rr) / sum(opaque_h(sliced_path(sheet, r[0], "x")) for r in rr)
        for x, role, pose, view, label, _ in rows:
            cid = f"cast_{role}_{pose}"
            dst = f"game/art/cast/{cid}.webp"
            drop_specks(sliced_path(sheet, x, "x"), dst)
            w, h = Image.open(dst).size
            sc = role_scale.get(role)
            if sc is None:  # no reference on this sheet: NOREF fraction of the standing height for the median figure
                hs = sorted(opaque_h(sliced_path(sheet, r[0], "x")) for r in rows if r[1] == role)
                sc = H[role] * NOREF.get(sheet, 1.0) / hs[len(hs) // 2]
                role_scale[role] = sc
            new.append({"id": cid, "path": f"art/cast/{cid}.webp", "sheet": sheet, "category": "cast", "role": role,
                        "variant": pose, "pose": pose, "view": view,
                        "facing": "right" if view == "side" else view, "label": label,
                        "height_units": round(opaque_h(dst) * sc, 3), "cross_slot": False, "biome": "any",
                        "season": "any", "tags": TAGS[role] + ["sunmoon", pose, view], "px": [w, h],
                        "hanging": role == SKY, "skin": role, "parts": {}})
    json.dump(keep + new, open("game/art/cast/catalog.json", "w"), ensure_ascii=False, indent=1)
    print(len(new), "standing figures;", len(keep) + len(new), "cast cards")
    if "--cycles" in sys.argv:
        for sheet, (skin, plan) in CYCLES.items():
            if not os.path.exists(f"art_src/cast/raw/{sheet}.png"):
                print("missing", sheet)
                continue
            args = [sys.executable, "tools/cast/add_cycles.py", sheet, skin, *plan, "--h",
                    str(CYCLE_H.get(skin, 0.97)), "--tag", "sunmoon"]
            if "--noslice" in sys.argv:
                args.append("--noslice")
            subprocess.run(args, check=True)


if __name__ == "__main__":
    main()
