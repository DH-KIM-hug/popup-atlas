#!/usr/bin/env python3
"""Re-skin a tale's shipped cast images from FELT to PAPER without rebuilding the cast (2026-11-22, felt -> paper).

  python3 tools/cast/paper_reskin.py <tale> [--only cast_x,cast_y] [--dry]

Every cast sheet of the tale was redrawn piece for piece as paper (tools/art/paper_jobs.py `castp_<sheet>` ->
art_src/cast/raw/<sheet>_paper.png; the felt raw is kept as <sheet>_felt.png). The shipped images (figures, padded
cycle frames, rig parts, peek figures ...) are 1:1 crops of the felt raws, cut / padded / trimmed by the cast tools,
so instead of re-running those tools (build_cast.py rewrites the whole catalog) each shipped image is located in its
felt raw (alpha + colour template match, mirrored too) and repainted from the paper raw WARPED INTO THE FELT RAW'S
FRAME (each paper piece scaled to its felt piece's height, bottom-centre aligned). Same canvas, same placement, same
catalog: nothing else changes.
- a whole figure takes the paper silhouette (within its canvas); a part (leg, body, hips) takes the paper pixels inside
  its own felt mask grown by 4 px, so the cut lines of the rig stay where they were;
- pixels a tool painted (torso fill under swinging arms, a recoloured mouth) differ from the felt raw: they are kept and
  counted (EDITED) — re-derive those variants from the paper art with their own tool afterwards (wc_mouth_v5.py);
- the felt original of every image is read from git (FELT_REV), so a re-skin can be redone after a better paper raw.
Writes art_src/cast/qa/<tale>_paper_reskin.png (felt | paper per image) and prints per-image IoU / edited counts.
"""
import json, os, shutil, subprocess, sys, tempfile
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
os.chdir(ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools", "art"))
import importlib.util
_spec = importlib.util.spec_from_file_location("paper_swap", os.path.join(ROOT, "tools/art/paper_swap.py"))
paper_swap = importlib.util.module_from_spec(_spec)
_argv = sys.argv
sys.argv = ["paper_swap"]
_spec.loader.exec_module(paper_swap)
sys.argv = _argv
_spec2 = importlib.util.spec_from_file_location("paper_jobs", os.path.join(ROOT, "tools/art/paper_jobs.py"))
paper_jobs = importlib.util.module_from_spec(_spec2)
_spec2.loader.exec_module(paper_jobs)

RAW = "art_src/cast/raw"
RAWDIR = [RAW]  # atlas mode switches it to art_src/atlas/raw
BACK = "art_src/cast/felt_backup"


def bg_alpha(rgb):
    r, g, b = rgb[..., 0].astype(int), rgb[..., 1].astype(int), rgb[..., 2].astype(int)
    m = np.minimum(r, b) - g
    return ~((m > 70) & (r > 140) & (b > 140))


def slice_pieces(path, tmpdir):
    name = os.path.basename(path)[:-4]
    subprocess.run([sys.executable, "tools/atlas/slice_atlas.py", path, "--out", tmpdir, "--join", "5"], check=True,
                   stdout=subprocess.DEVNULL)
    subprocess.run([sys.executable, "tools/atlas/fill_holes.py", path, f"{tmpdir}/{name}"], check=True,
                   stdout=subprocess.DEVNULL)
    meta = json.load(open(f"{tmpdir}/{name}/_slices.json"))["sprites"]
    out = []
    for m in meta:
        p = f"{tmpdir}/{name}/{m['id']}.webp"
        if os.path.exists(p):
            out.append((Image.open(p).convert("RGBA"), (m["bbox"][0] - 4, m["bbox"][1] - 4)))
    return out


def build_warped(sheet):
    """the paper raw warped into the felt raw's frame: RGBA canvas of the felt raw size"""
    RAW = RAWDIR[0]
    felt = f"{RAW}/{sheet}_felt.png"
    if not os.path.exists(felt):
        shutil.copy2(f"{RAW}/{sheet}.png", felt)
    paper = f"{RAW}/{sheet}_paper.png"
    tmp = tempfile.mkdtemp(prefix="reskin_")
    os.makedirs(f"{tmp}/f"); os.makedirs(f"{tmp}/p")
    shutil.copy2(felt, f"{tmp}/f/{sheet}.png")
    shutil.copy2(paper, f"{tmp}/p/{sheet}.png")
    cache = f"artifacts/paper/warp_cache/{RAW.split('/')[1]}_{sheet}.webp"  # git-ignored
    if os.path.exists(cache) and os.path.getmtime(cache) > os.path.getmtime(paper):
        shutil.rmtree(tmp, ignore_errors=True)
        return (np.asarray(Image.open(felt).convert("RGB")), np.asarray(Image.open(cache).convert("RGBA")),
                ["  (cached warp)"])
    fp = None
    for d in ("art_src/cast/slices", "art_src/cast/sliced"):  # the felt slicing the cast tools already made
        mp = f"{d}/{sheet}/_slices.json"
        if RAW.endswith("cast/raw") and os.path.exists(mp):
            fp = []
            for m in json.load(open(mp))["sprites"]:
                q = f"{d}/{sheet}/{m['id']}.webp"
                if os.path.exists(q):
                    fp.append((Image.open(q).convert("RGBA"), (m["bbox"][0] - 4, m["bbox"][1] - 4)))
            break
    if not fp:
        fp = slice_pieces(f"{tmp}/f/{sheet}.png", f"{tmp}/f")
    pp = slice_pieces(f"{tmp}/p/{sheet}.png", f"{tmp}/p")
    FW, FH = Image.open(felt).size
    PW, PH = Image.open(paper).size

    def box(im, xy):
        a = np.asarray(im)[..., 3] > 128
        ys, xs = np.nonzero(a)
        return (xy[0] + xs.min(), xy[1] + ys.min(), xy[0] + xs.max() + 1, xy[1] + ys.max() + 1)
    fb = [box(*p) for p in fp]
    pb = [box(*p) for p in pp]
    report = []
    amap, lost, acost = paper_swap.assign2([p[0] for p in fp], [paper_swap.norm(b, FW, FH) for b in fb],
                                           [p[0] for p in pp], [paper_swap.norm(b, PW, PH) for b in pb])
    for i, c in acost.items():
        if c > 0.75:
            report.append(f"  {sheet}: felt piece {i} matched with high cost {c:.2f} (check the QA sheet)")
    canvas = Image.new("RGBA", (FW, FH), (0, 0, 0, 0))
    for i, js in amap.items():
        if not js:
            report.append(f"  {sheet}: felt piece {i} has no paper piece")
            continue
        im, _ = paper_swap.composite([pp[j] for j in js])
        im = paper_swap.clean_fringe(im)
        x0 = min(pp[j][1][0] for j in js); y0 = min(pp[j][1][1] for j in js)
        nb = box(im, (x0, y0))
        ob = fb[i]
        s = (ob[3] - ob[1]) / max(1, nb[3] - nb[1])
        if abs(np.log(((ob[2] - ob[0]) / max(1, nb[2] - nb[0])) / s)) > 0.2:
            report.append(f"  {sheet}: piece {i} width ratio off ({(ob[2]-ob[0])}/{(nb[2]-nb[0])} vs height scale {s:.2f})")
        w2, h2 = max(1, round(im.width * s)), max(1, round(im.height * s))
        ims = im.resize((w2, h2), Image.LANCZOS)
        a = np.asarray(ims)[..., 3]
        ys, xs = np.nonzero(a > 128)
        # bottom-centre: alpha bbox bottom to the felt bottom, alpha centre x to the felt centre x
        cxn = (xs.min() + xs.max() + 1) / 2
        px = round((ob[0] + ob[2]) / 2 - cxn)
        py = round(ob[3] - (ys.max() + 1))
        canvas.alpha_composite(ims, (max(0, px), max(0, py)), (max(0, -px), max(0, -py)))
    for j in lost:
        report.append(f"  {sheet}: paper piece {j} unused")
    shutil.rmtree(tmp, ignore_errors=True)
    os.makedirs(os.path.dirname(cache), exist_ok=True)
    canvas.save(cache, "WEBP", lossless=True, quality=100, method=4)
    return np.asarray(Image.open(felt).convert("RGB")), np.asarray(canvas), report


def match(D, felt_rgb, felt_al_small, S=4):
    """locate D (RGBA array) in the felt raw. -> (x, y, flipped, mean colour error) or None"""
    best = None
    da = D[..., 3] > 128
    if da.sum() < 50:
        return None
    F = felt_al_small  # the felt raw, RGB 0..1 at 1/S scale
    H, W = F.shape[:2]
    fsq = np.fft.rfft2((F ** 2).sum(-1))
    fch = [np.fft.rfft2(F[..., c]) for c in range(3)]
    for flip in (False, True):
        Dd = D[:, ::-1] if flip else D
        sm = np.asarray(Image.fromarray(np.ascontiguousarray(Dd)).resize(
            (max(1, Dd.shape[1] // S), max(1, Dd.shape[0] // S)), Image.BOX)).astype(np.float32) / 255.0
        M = (sm[..., 3] > 0.95).astype(np.float32)
        T = sm[..., :3]
        h, w = M.shape
        if h > H or w > W or M.sum() < 4:
            continue
        # masked SSD at every offset via FFT: sum M F^2 - 2 sum M F T + sum M T^2
        cm = np.fft.irfft2(fsq * np.fft.rfft2(M[::-1, ::-1], s=(H, W)), s=(H, W))
        cft = sum(np.fft.irfft2(fch[c] * np.fft.rfft2((M * T[..., c])[::-1, ::-1], s=(H, W)), s=(H, W))
                  for c in range(3))
        ssd = (cm - 2 * cft)[h - 1:, w - 1:] + (M[..., None] * T ** 2).sum()
        valid = -ssd / M.sum()
        cand = np.argsort(valid.ravel())[-6:]
        # refine on a sub-grid with the colour error (interior pixels)
        inner = np.asarray(Image.fromarray(((Dd[..., 3] > 250) * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(5))) > 0
        if inner.sum() < 30:
            inner = Dd[..., 3] > 200
        ys, xs = np.nonzero(inner)
        if len(ys) > 3000:
            k = np.random.default_rng(0).choice(len(ys), 3000, replace=False)
            ys, xs = ys[k], xs[k]
        for c in cand:
            yy, xx = np.unravel_index(c, valid.shape)
            for dy in range(-S - 1, S + 2):
                for dx in range(-S - 1, S + 2):
                    x, y = xx * S + dx, yy * S + dy
                    if x < 0 or y < 0 or y + Dd.shape[0] > felt_rgb.shape[0] or x + Dd.shape[1] > felt_rgb.shape[1]:
                        continue
                    e = np.abs(felt_rgb[y + ys, x + xs].astype(int) - Dd[ys, xs, :3].astype(int)).mean()
                    if best is None or e < best[3]:
                        best = (x, y, flip, e)
    return best


def reskin_image(path, sheets_data, order):
    D = np.asarray(Image.open(path).convert("RGBA"))
    found = None
    for sh in order:
        frgb, warped, fal = sheets_data[sh]
        m = match(D, frgb, fal)
        if m and (found is None or m[3] < found[1][3]):
            found = (sh, m)
        if found and found[1][3] < 6:
            break
    if found is None or found[1][3] > 14:
        return None, found
    sh, (x, y, flip, err) = found
    frgb, warped, _ = sheets_data[sh]
    Dd = D[:, ::-1] if flip else D
    h, w = Dd.shape[:2]
    Fc = frgb[y:y + h, x:x + w].astype(int)
    Wc = warped[y:y + h, x:x + w].astype(np.float32)
    da = Dd[..., 3]
    inner = np.asarray(Image.fromarray(((da > 250) * 255).astype(np.uint8)).filter(ImageFilter.MinFilter(5))) > 0
    # a tool may have recoloured the crop (front_legs.py colour-matches leg cards to the body): fit D = a * felt + b per
    # channel on the interior and give the paper the same recolour
    gain = np.ones(3, np.float32)
    off = np.zeros(3, np.float32)
    if err > 3 and inner.sum() > 200:
        d0 = np.abs(Fc - Dd[..., :3].astype(int)).max(-1)
        ok = inner & (d0 < 90)
        for c in range(3):
            fx = Fc[..., c][ok].astype(np.float32)
            dy = Dd[..., c][ok].astype(np.float32)
            if fx.std() > 4:
                a_ = float(np.clip(np.cov(fx, dy)[0, 1] / fx.var(), 0.6, 1.6))
                gain[c], off[c] = a_, float(dy.mean() - a_ * fx.mean())
            else:
                off[c] = float(dy.mean() - fx.mean())
    Fcc = Fc * gain + off
    diff = np.abs(Fcc - Dd[..., :3].astype(np.float32)).max(-1)
    edited = inner & (diff > 70)
    # whole figure (its felt piece fills the canvas) or a part?
    fa = bg_alpha(frgb[y:y + h, x:x + w])
    part = (da > 128).sum() < 0.85 * fa.sum() and "--whole" not in sys.argv
    if part:
        region = np.asarray(Image.fromarray(((da > 8) * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(9))) / 255.0
    else:  # a whole figure takes the paper silhouette near it (not a neighbour's sliver in a padded cycle canvas)
        region = np.asarray(Image.fromarray(((da > 8) * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(31))) / 255.0
    out = Wc.copy()
    out[..., :3] = Wc[..., :3] * gain + off
    out[..., 3] = Wc[..., 3] * region
    out[edited] = Dd[edited].astype(np.float32)
    out = np.clip(out, 0, 255).astype(np.uint8)
    if flip:
        out = out[:, ::-1]
    na = out[..., 3] > 128
    oa = D[..., 3] > 128
    iou = (na & oa).sum() / max(1, (na | oa).sum())
    return Image.fromarray(np.ascontiguousarray(out), "RGBA"), (sh, err, int(edited.sum()), iou, part)


FELT_REV = "d03c0f7"  # the last commit before the felt -> paper conversion of the shared library and the tales
_TMP = tempfile.mkdtemp(prefix="felt_orig_")


def felt_original(path):
    """the felt version of a shipped image: from git at FELT_REV (the working copy may be paper already)"""
    try:
        blob = subprocess.check_output(["git", "show", f"{FELT_REV}:{path}"], stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError:
        return path
    out = os.path.join(_TMP, path.replace("/", "__"))
    open(out, "wb").write(blob)
    return out


def run(label, sheets, files, dry, backup_root, qa_path):
    """files: [(path, preferred sheet)]; every file is repainted from the warped paper raws"""
    data = {}
    for s in sheets:
        frgb, warped, rep = build_warped(s)
        fal_s = np.asarray(Image.fromarray(frgb).resize((frgb.shape[1] // 4, frgb.shape[0] // 4), Image.BOX)
                           ).astype(np.float32) / 255.0
        data[s] = (frgb, warped, fal_s)
        print(s, "warped", *rep, sep="\n" if rep else " ")
    seen, pairs, rows = set(), [], []
    for path, sh in files:
        if path in seen or not os.path.exists(path):
            continue
        seen.add(path)
        src = felt_original(path)   # always re-skin from the felt original (git, before the paper work)
        order = [sh] + [s for s in sheets if s != sh]
        im, info = reskin_image(src, data, order)
        if im is None:
            rows.append(f"NOMATCH {path} best={info}")
            continue
        sh2, err, ned, iou, part = info
        flag = (" LOWIOU" if iou < 0.88 else "") + (f" EDITED{ned}" if ned > 40 else "")
        rows.append(f"{os.path.basename(path)} <- {sh2} err {err:.1f} iou {iou:.2f}{' part' if part else ''}{flag}")
        pairs.append((os.path.basename(path).rsplit(".", 1)[0] + flag, Image.open(src).convert("RGBA"), im))
        if not dry:
            if path.endswith(".webp"):
                im.save(path, "WEBP", lossless=True, quality=100, method=6)
            else:
                im.save(path)
    print("\n".join(rows))
    print(label, "images", len(pairs), "nomatch", sum(r.startswith("NOMATCH") for r in rows),
          "lowiou", sum("LOWIOU" in r for r in rows), "edited", sum("EDITED" in r for r in rows))
    paper_swap.qa_sheet(pairs, qa_path, f"{label}: felt -> paper")
    return rows


def main():
    dry = "--dry" in sys.argv
    only = sys.argv[sys.argv.index("--only") + 1].split(",") if "--only" in sys.argv else None
    if sys.argv[1] == "atlas":
        # story set sheets with derived art (fold bands, doors, bodies): cards and every derived image under
        # game/art/atlas/<sheet>/ keep their canvas; atlas_clean copies are rebuilt from the new cards
        RAWDIR[0] = "art_src/atlas/raw"
        for sheet in sys.argv[2].split(","):
            files = []
            for dp, _, fs in os.walk(f"game/art/atlas/{sheet}"):
                for f in sorted(fs):
                    if "/stages" in dp and "--stages" not in sys.argv:
                        continue  # fold bands / doors / bodies: re-cut from the new card with their own tool
                    if f.endswith(".webp") and (not only or f[:-5] in only):
                        files.append((os.path.join(dp, f), sheet))
            run(sheet, [sheet], files, dry, "art_src/atlas/felt_backup", f"art_src/atlas/qa/{sheet}_paper_reskin.png")
            if not dry:
                from strip_rim import strip_rim
                for path, _ in files:
                    dst = path.replace("game/art/atlas/", "game/art/atlas_clean/")
                    if os.path.exists(dst) and "/stages/" not in path:
                        strip_rim(Image.open(path).convert("RGBA"))[0].save(dst, "WEBP", lossless=True)
                json.dump({"source": "paper (tools/cast/paper_reskin.py atlas)"},
                          open(f"art_src/atlas/qa/{sheet}_paper_reskin.json", "w"))
        return
    if sys.argv[1] == "files":
        # paper_reskin.py files <tale> <src dir> <out dir>: re-skin loose felt crops (e.g. the ghost figures' mouth
        # originals in art_src/cast/black_mouth_orig) into <out dir> under the same names
        tale, src_dir, out_dir = sys.argv[2], sys.argv[3], sys.argv[4]
        sheets = [s for s in paper_jobs.CAST_SHEETS[tale] if os.path.exists(f"{RAW}/{s}_paper.png")]
        os.makedirs(out_dir, exist_ok=True)
        files = []
        for f in sorted(os.listdir(src_dir)):
            if f.endswith((".webp", ".png")):
                dst = os.path.join(out_dir, f)
                shutil.copy2(os.path.join(src_dir, f), dst)
                files.append((dst, sheets[0]))
        run(tale + "_files", sheets, files, dry, BACK, f"art_src/cast/qa/{tale}_files_paper_reskin.png")
        return
    tale = sys.argv[1]
    sheets = [s for s in paper_jobs.CAST_SHEETS[tale] if os.path.exists(f"{RAW}/{s}_paper.png")]
    missing = [s for s in paper_jobs.CAST_SHEETS[tale] if s not in sheets]
    if missing:
        print("NO PAPER RAW (skipped, stays felt):", missing)
    cat = json.load(open("game/art/cast/catalog.json"))
    ents = [e for e in cat if e.get("sheet") in sheets and (not only or e["id"] in only)]
    files = []
    for e in ents:
        files.append((f"game/{e['path']}", e["sheet"]))
        for p in (e.get("parts") or {}).values():
            files.append((f"game/{p}", e["sheet"]))
    run(tale, sheets, files, dry, BACK, f"art_src/cast/qa/{tale}_paper_reskin.png")


if __name__ == "__main__":
    main()
