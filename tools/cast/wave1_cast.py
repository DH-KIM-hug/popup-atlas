#!/usr/bin/env python3
"""Wave 1 (2026-11-24, gate audit v1): catalogue the shared cycles the tales were missing (art: tools/art/wave1_jobs.py).

  python3 tools/cast/wave1_cast.py            # slice the raws (4 in parallel), add_cycles --noslice, kid clones, aliases
  python3 tools/cast/wave1_cast.py --noslice  # reuse art_src/cast/slices/<sheet>

Cycles (skin: cycle ids; StoryActor picks them by view / verb):
  wolf: run_back (2, back), climb_cycle (2, back: a ladder)
  tiger: run_back (2, back), climb_cycle (2, back: up a trunk), dg_back (2, back: the drawn walk-away in mother's
         clothes; replaces the static dg_back card while walking), aliases rope_climb (rope_a/b), axe_climb (axe_a/b)
  goat_kid_1..6: run_front (2, front; drawn once on the green kid 4, recoloured per kid like wolf_goats_cast.py)
  hanbok_boy / hanbok_girl: alias climb_cycle (climb_a/b, back: hands up the trunk / rope; their rope_a/b are
                             a praying and a sitting figure, not climb frames)
  mother_pig, rich_lady, peasant_mother: walk_cycle (4, side), walk_back (2), walk_front (2)
Aliases are catalog entries pointing at the existing drawn frames (no new files).
"""
import json, os, subprocess, sys
from concurrent.futures import ThreadPoolExecutor
from PIL import Image

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
os.chdir(ROOT)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wolf_goats_cast import KIDS, recolour  # noqa: E402

PLAN = {
    "cast_w1_wolf_back": ("wolf", ["run_back:2:back", "climb_cycle:2:back"]),
    "cast_w1_tiger_back": ("tiger", ["run_back:2:back", "climb_cycle:2:back"]),
    "cast_w1_tiger_dg_back": ("tiger", ["dg_back:2:back"]),
    "cast_w1_kid_run_front": ("goat_kid_4", ["run_front:2:front"]),
    "cast_w1_mother_pig_walk": ("mother_pig", ["walk_cycle:4:side", "walk_back:2:back", "walk_front:2:front"]),
    "cast_w1_rich_lady_walk": ("rich_lady", ["walk_cycle:4:side", "walk_back:2:back", "walk_front:2:front"]),
    "cast_w1_peasant_mother_walk": ("peasant_mother", ["walk_cycle:4:side", "walk_back:2:back", "walk_front:2:front"]),
}
ALIASES = [  # skin, cycle, view, [existing figure variants in frame order]
    ("hanbok_boy", "climb_cycle", "back", ["climb_a", "climb_b"]),
    ("hanbok_girl", "climb_cycle", "back", ["climb_a", "climb_b"]),
    ("tiger", "rope_climb", "back", ["rope_a", "rope_b"]),
    ("tiger", "axe_climb", "side", ["axe_a", "axe_b"]),
]


# objects that travel by a paper motion of their own (CastPuppet._gait_step), catalog field `gait` on every figure
GAITS = {"pj_bam": "hop", "pj_ddong": "hop", "pj_songgot": "hop", "pj_jara": "crawl", "pj_myeongseok": "roll",
         "pj_jeolgu": "thump", "pj_jige": "stride"}


def set_gaits():
    cat = json.load(open("game/art/cast/catalog.json"))
    for e in cat:
        if e.get("skin") in GAITS:
            e["gait"] = GAITS[e["skin"]]
    json.dump(cat, open("game/art/cast/catalog.json", "w"), ensure_ascii=False, indent=1)


def slice_sheet(sheet):
    subprocess.run([sys.executable, "tools/atlas/slice_atlas.py", f"art_src/cast/raw/{sheet}.png", "--out",
                    "art_src/cast/slices"], check=True, capture_output=True)
    return sheet


def main():
    if "--gaits" in sys.argv:  # only the object gaits
        set_gaits()
        return
    if "--noslice" not in sys.argv:
        with ThreadPoolExecutor(4) as ex:
            for s in ex.map(slice_sheet, PLAN):
                print("sliced", s)
    for sheet, (skin, plan) in PLAN.items():
        subprocess.run([sys.executable, "tools/cast/add_cycles.py", sheet, skin, *plan, "--h", "0.97", "--tag", "wave1",
                        "--noslice"], check=True)
    cat = json.load(open("game/art/cast/catalog.json"))
    # the kids: kid 4 (green collar, as drawn) -> kids 1-3, 5, 6 recoloured, heights by the kid's own calm figure
    k4 = [e for e in cat if e.get("skin") == "goat_kid_4" and e.get("cycle") == "run_front"]
    h4 = next(e for e in cat if e["id"] == "cast_goat_kid_4_calm")["height_units"]
    for n, (col, _hf) in KIDS.items():
        if n == 4:
            continue
        skin = f"goat_kid_{n}"
        hn = next(e for e in cat if e["id"] == f"cast_{skin}_calm")["height_units"]
        for e in k4:
            cid = e["id"].replace("cast_goat_kid_4_", f"cast_{skin}_")
            recolour("game/" + e["path"], f"game/art/cast/{cid}.webp", col)
            q = dict(e)
            q.update({"id": cid, "path": f"art/cast/{cid}.webp", "role": skin, "skin": skin,
                      "height_units": round(e["height_units"] * hn / h4, 3), "tags": [skin, "wave1", "cycle"]})
            cat = [x for x in cat if x["id"] != cid] + [q]
    for skin, cyc, view, figs in ALIASES:
        for fr, v in enumerate(figs):
            src = next(e for e in cat if e["id"] == f"cast_{skin}_{v}")
            cid = f"cast_{skin}_{cyc}_{fr}"
            q = {k: src[k] for k in src if k not in ("id", "variant", "pose", "label", "cycle", "frame")}
            q.update({"id": cid, "variant": f"{cyc}_{fr}", "pose": f"{cyc}_{fr}", "view": view,
                      "facing": "right" if view == "side" else view, "cycle": cyc, "frame": fr,
                      "label": f"{cyc} frame {fr} (alias of {v}, wave 1)", "tags": [skin, "wave1", "cycle", "alias"]})
            cat = [x for x in cat if x["id"] != cid] + [q]
    json.dump(cat, open("game/art/cast/catalog.json", "w"), ensure_ascii=False, indent=1)
    set_gaits()
    print("catalog", len(cat))


if __name__ == "__main__":
    main()
