#!/usr/bin/env python3
"""Swap a FELT sheet for its PAPER redraw, keeping every card id (2026-11-22, felt -> paper; tools/art/paper_jobs.py).

  python3 tools/art/paper_swap.py atlas <sheet> [--dry]   # shared atlas / story sheet: game/art/atlas/<sheet>/
  python3 tools/art/paper_swap.py cards <sheet> [--dry] [--no-publish]   # 해와 바람 card kit: art_src/cards/keyed/
  python3 tools/art/paper_swap.py publish                 # ship the card kit once after several --no-publish swaps

The paper raw (<raw>/<sheet>_paper.png) is redrawn piece for piece from the felt raw, but pieces move a little and
the slicer numbers them by rows, so pieces are matched by position, not index: every new piece goes to the old piece
its box overlaps most (normalised sheet coordinates); an old card made of several new pieces gets them composited.
Then
- atlas: the new card is written under the old id (game/art/atlas/<sheet>/<id>.webp, _slices.json bbox / size in the
  paper raw), the cleaned copy in game/art/atlas_clean/ is rebuilt (strip_rim); catalog.json keeps the felt px so the
  template lays every spread out exactly as before;
- cards: keyed/<sheet>_<nn>.png are rewritten from the paper raw (split cards "<nn>a/b" re-split at the emptiest
  column near the old cut), then tools/art/publish_cards.py ships them (under the lock; aspects stay the felt ones,
  tools/art/card_aspect_lock.json).
The felt raw is kept as <sheet>_felt.png and the paper raw becomes <sheet>.png (derived tools read <sheet>.png).
QA: art_src/<atlas|cards>/qa/<sheet>_felt_vs_paper.png (every card: felt left, paper right) — look before committing.
"""
import json, os, shutil, subprocess, sys, tempfile
import numpy as np
from PIL import Image, ImageDraw

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools", "art"))
LOCK = [os.path.join(ROOT, "tools/story/with_godot.sh")]


def norm(b, W, H):
    return (b[0] / W, b[1] / H, b[2] / W, b[3] / H)


def inter(a, b):
    w = min(a[2], b[2]) - max(a[0], b[0])
    h = min(a[3], b[3]) - max(a[1], b[1])
    return max(0.0, w) * max(0.0, h)


def area(a):
    return max(1e-9, (a[2] - a[0]) * (a[3] - a[1]))


def assign(old, new):
    """old / new: lists of normalised boxes. -> {old index: [new indices]}, unassigned new list"""
    out = {i: [] for i in range(len(old))}
    lost = []
    for j, nb in enumerate(new):
        best, bs = None, 0.0
        for i, ob in enumerate(old):
            s = inter(nb, ob) / area(nb)
            if s > bs:
                best, bs = i, s
        if best is None or bs < 0.25:
            # fall back to the nearest centre when the redraw shifted a small piece off its old box
            cx, cy = (nb[0] + nb[2]) / 2, (nb[1] + nb[3]) / 2
            d = [((ob[0] + ob[2]) / 2 - cx) ** 2 + ((ob[1] + ob[3]) / 2 - cy) ** 2 for ob in old]
            k = int(np.argmin(d))
            ob = old[k]
            if d[k] ** 0.5 < 0.6 * max(ob[2] - ob[0], ob[3] - ob[1]) and area(nb) > 0.25 * area(ob):
                best = k
            else:
                lost.append(j)
                continue
        out[best].append(j)
    return out, lost


def composite(pieces):
    """pieces: [(Image RGBA, (x0, y0) in raw)] -> (Image, (x0, y0, x1, y1))"""
    x0 = min(p[1][0] for p in pieces)
    y0 = min(p[1][1] for p in pieces)
    x1 = max(p[1][0] + p[0].width for p in pieces)
    y1 = max(p[1][1] + p[0].height for p in pieces)
    c = Image.new("RGBA", (x1 - x0, y1 - y0), (0, 0, 0, 0))
    for im, (x, y) in pieces:
        c.alpha_composite(im, (x - x0, y - y0))
    return c, (x0, y0, x1, y1)


def qa_sheet(pairs, path, title):
    th, cw = 200, 230
    cols = 4
    rows = (len(pairs) + cols - 1) // cols
    sh = Image.new("RGB", (cols * cw * 2 + cols * 10, rows * (th + 26) + 30), (126, 122, 114))
    d = ImageDraw.Draw(sh)
    d.text((6, 6), title + "   (each pair: felt left, paper right)", fill=(255, 255, 255))
    for k, (name, a, b) in enumerate(pairs):
        x = (k % cols) * (cw * 2 + 10)
        y = 30 + (k // cols) * (th + 26)
        for n, im in enumerate((a, b)):
            if im is None:
                continue
            s = min(th / im.height, (cw - 8) / im.width)
            t = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
            sh.paste(t, (x + n * cw + 4, y + th - t.height), t)
        d.text((x + 4, y + th + 6), name[-28:], fill=(255, 255, 255))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    sh.save(path)
    print("qa", path)


def keep_felt_raw(raw_dir, sheet):
    felt = f"{raw_dir}/{sheet}_felt.png"
    if not os.path.exists(felt):
        shutil.copy2(f"{raw_dir}/{sheet}.png", felt)
    return felt


# ------------------------------------------------------------------ atlas
def swap_atlas(sheet, dry):
    raw_dir = "art_src/atlas/raw"
    paper = f"{raw_dir}/{sheet}_paper.png"
    felt = keep_felt_raw(raw_dir, sheet)
    sdir = f"game/art/atlas/{sheet}"
    meta = json.load(open(f"{sdir}/_slices.json"))
    cat = json.load(open("game/art/atlas/catalog.json"))
    ids = {e["id"] for e in cat if e.get("sheet") == sheet}
    FW, FH = Image.open(felt).size
    PW, PH = Image.open(paper).size
    old = [m for m in meta["sprites"]]
    oldb = [norm(m["bbox"], FW, FH) for m in old]
    tmp = tempfile.mkdtemp(prefix="paper_")
    shutil.copy2(paper, f"{tmp}/{sheet}.png")
    join = "5"
    lab = f"tools/atlas/labels/{sheet}.json"
    subprocess.run([sys.executable, "tools/atlas/slice_atlas.py", f"{tmp}/{sheet}.png", "--out", tmp, "--join", join],
                   check=True, stdout=subprocess.DEVNULL)
    subprocess.run([sys.executable, "tools/atlas/fill_holes.py", f"{tmp}/{sheet}.png", f"{tmp}/{sheet}"], check=True,
                   stdout=subprocess.DEVNULL)
    nm = json.load(open(f"{tmp}/{sheet}/_slices.json"))["sprites"]
    newb = [norm(m["bbox"], PW, PH) for m in nm]
    amap, lost = assign(oldb, newb)
    pairs, report, upd = [], [], {}
    for i, m in enumerate(old):
        if m["id"] not in ids:
            continue
        js = amap[i]
        fim = Image.open(f"{sdir}/{m['id']}.webp").convert("RGBA") if os.path.exists(f"{sdir}/{m['id']}.webp") else None
        if not js:
            report.append(f"MISSING {m['id']} (no paper piece)")
            pairs.append((m["id"] + " MISSING", fim, None))
            continue
        pcs = []
        for j in js:
            im = Image.open(f"{tmp}/{sheet}/{nm[j]['id']}.webp").convert("RGBA")
            pcs.append((im, (nm[j]["bbox"][0] - 4, nm[j]["bbox"][1] - 4)))
        im, box = composite(pcs)
        ar_o = (fim.width / fim.height) if fim else 1
        ar_n = im.width / im.height
        flag = " ASPECT" if abs(np.log(ar_n / ar_o)) > 0.25 else ""
        if len(js) > 1:
            flag += f" JOINED{len(js)}"
        report.append(f"{m['id']}: <- {[nm[j]['id'][-2:] for j in js]} aspect {ar_o:.2f}->{ar_n:.2f}{flag}")
        pairs.append((m["id"] + flag, fim, im))
        upd[m["id"]] = (im, [box[0] + 4, box[1] + 4, box[2] - 4, box[3] - 4])
    for j in lost:
        report.append(f"unused paper piece {nm[j]['id']} bbox {nm[j]['bbox']}")
    print("\n".join(report))
    qa_sheet(pairs, f"art_src/atlas/qa/{sheet}_felt_vs_paper.png", f"{sheet}: felt -> paper")
    if dry:
        return
    from strip_rim import strip_rim
    for m in meta["sprites"]:
        if m["id"] in upd:
            im, bb = upd[m["id"]]
            im.save(f"{sdir}/{m['id']}.webp", "WEBP", lossless=True, quality=100, method=6)
            m["bbox"] = bb
            m["size"] = [im.width, im.height]
            dst = f"game/art/atlas_clean/{sheet}/{m['id']}.webp"
            if os.path.exists(os.path.dirname(dst)):
                out, _ = strip_rim(im)
                out.save(dst, "WEBP", lossless=True)
    meta["source"] = paper
    json.dump(meta, open(f"{sdir}/_slices.json", "w"), indent=1)
    shutil.copy2(paper, f"{raw_dir}/{sheet}.png")
    # catalog.json is NOT touched: the layout keeps the felt card's px / aspect (a 1 % aspect change cascaded through
    # the template's placement and re-dressed whole spreads); the paper image is drawn into the same footprint.
    shutil.rmtree(tmp, ignore_errors=True)


def catalog_px(pf):
    """runs under the Godot slot lock: re-read the catalog right before writing"""
    px = json.load(open(pf))
    cat = json.load(open("game/art/atlas/catalog.json"))
    n = 0
    for e in cat:
        if e["id"] in px:
            e["px"] = px[e["id"]]
            n += 1
    json.dump(cat, open("game/art/atlas/catalog.json", "w"), indent=1, ensure_ascii=False)
    print("catalog px updated", n)


# ------------------------------------------------------------------ cards kit
def swap_cards(sheet, dry):
    import key_cards
    raw_dir = "art_src/cards/raw"
    kdir = "art_src/cards/keyed"
    paper = f"{raw_dir}/{sheet}_paper.png"
    felt = keep_felt_raw(raw_dir, sheet)
    FW, FH = Image.open(felt).size
    PW, PH = Image.open(paper).size
    ob, nb = [], []
    fcards = key_cards.split(key_cards.key(Image.open(felt)), sheet, ob)
    ncards = key_cards.split(key_cards.key(Image.open(paper)), sheet, nb)
    # the felt split must reproduce the shipped keyed files (else the indices are not the shipped ones)
    for i, c in enumerate(fcards):
        p = f"{kdir}/{sheet}_{i:02d}.png"
        if os.path.exists(p) and Image.open(p).size != c.size:
            print(f"WARN felt re-split differs at {sheet}_{i:02d}: {Image.open(p).size} vs {c.size}")
    amap, lost = assign([norm(b, FW, FH) for b in ob], [norm(b, PW, PH) for b in nb])
    from publish_cards import MAP
    m = dict(MAP)
    ex = "tools/art/card_map_extra.json"
    if os.path.exists(ex):
        m.update({k: tuple(v) for k, v in json.load(open(ex)).items()})
    shipped = sorted(k for k in m if k.startswith(sheet + "_") and k[len(sheet) + 1:len(sheet) + 3].isdigit())
    pairs, report, writes = [], [], {}
    for src in shipped:
        idx = int(src[len(sheet) + 1:len(sheet) + 3])
        suf = src[len(sheet) + 3:]
        js = amap.get(idx, [])
        fim = Image.open(f"{kdir}/{src}.png").convert("RGBA") if os.path.exists(f"{kdir}/{src}.png") else None
        if not js:
            report.append(f"MISSING {src}")
            pairs.append((src + " MISSING", fim, None))
            continue
        im, _ = composite([(ncards[j], (nb[j][0], nb[j][1])) for j in js])
        if suf:  # a card split by split_manual.py: cut the paper piece at the emptiest column near the old cut
            fa = Image.open(f"{kdir}/{sheet}_{idx:02d}a.png")
            fb = Image.open(f"{kdir}/{sheet}_{idx:02d}b.png")
            frac = fa.width / (fa.width + fb.width)
            a = np.asarray(im)
            col = (a[..., 3] > 40).sum(0)
            x0, x1 = int((frac - 0.1) * a.shape[1]), int((frac + 0.1) * a.shape[1])
            cut = x0 + int(np.argmin(col[x0:x1]))
            part = a[:, :cut] if suf == "a" else a[:, cut:]
            al = part[..., 3] > 20
            ys, xs = np.nonzero(al)
            im = Image.fromarray(np.ascontiguousarray(part[ys.min():ys.max() + 1, max(0, xs.min() - 4):xs.max() + 5]), "RGBA")
        flag = ""
        if fim is not None and abs(np.log((im.width / im.height) / (fim.width / fim.height))) > 0.25:
            flag = " ASPECT"
        if len(js) > 1:
            flag += f" JOINED{len(js)}"
        report.append(f"{src} ({m[src][0]}): <- {js}{flag}")
        pairs.append((f"{m[src][0]}{flag}", fim, im))
        writes[src] = im
    for j in lost:
        report.append(f"unused paper piece {j} box {nb[j]}")
    print("\n".join(report))
    qa_sheet(pairs, f"art_src/cards/qa/{sheet}_felt_vs_paper.png", f"{sheet}: felt -> paper")
    if dry:
        return
    for src, im in writes.items():
        im.save(f"{kdir}/{src}.png")
    shutil.copy2(paper, f"{raw_dir}/{sheet}.png")
    if "--no-publish" not in sys.argv:  # several sheets: swap each with --no-publish, then `paper_swap.py publish`
        subprocess.run(LOCK + [sys.executable, "tools/art/publish_cards.py"], check=True)


if __name__ == "__main__":
    if sys.argv[1] == "_catalog_px":
        catalog_px(sys.argv[2])
    elif sys.argv[1] == "atlas":
        swap_atlas(sys.argv[2], "--dry" in sys.argv)
    elif sys.argv[1] == "publish":
        subprocess.run(LOCK + [sys.executable, "tools/art/publish_cards.py"], check=True)
    elif sys.argv[1] == "cards":
        swap_cards(sys.argv[2], "--dry" in sys.argv)
