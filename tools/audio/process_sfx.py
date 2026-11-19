#!/usr/bin/env python3
"""Turn raw ElevenLabs SFX (s16le stereo 48 kHz .pcm, or .mp3) into staged game files + manifest.

  python3 tools/audio/process_sfx.py --jobs tools/audio/three_pigs_sfx_jobs.json --out artifacts/audio_staging

Per job (rules in RULES below):
  - one-shot: trim leading / trailing silence, 3 ms fade in, 40 ms fade out, mono, loudness to the class target
    (peak ceiling -3 dBFS wins over the loudness target).
  - slice: a take of several separate hits (footsteps, knocks, thunks, rungs) is cut at its onsets into N single
    hits (the most similar-loudness ones), each its own file -> random variations.
  - loop: seam check (end->start jump and slope against the clip's own sample-to-sample motion, level of the
    last vs first 50 ms); if it fails, an equal-power crossfade loop (the tail folded over the head) makes it
    seamless. Stereo kept for beds; mono for positional emitters.
Writes sfx/<category>_<name>_<n>.ogg (Vorbis q6, 48 kHz) and sfx/manifest.json (prompt, duration, loop, LUFS,
peak, seam numbers). Uses ffmpeg for decode / encode / EBU R128 measurement. Raw data is never executed.
"""
import argparse
import json
import os
import re
import subprocess
import tempfile

import numpy as np

SR = 48000

# job id -> (output stem "<category>_<name>", mode, channels, target LUFS, extra)
# targets: beds at their playback level (ambience ~ -28 LUFS, stream emitter a bit hotter because distance
# attenuation pulls it down), one-shots at -20 LUFS-ish (catalog gain sets the mix level).
RULES = {
    "amb_breeze_grass": ("amb_breeze_grass", "loop", 2, -30, {}),
    "amb_birds_day": ("amb_birds_day", "loop", 2, -30, {}),
    "amb_birds_afternoon": ("amb_birds_afternoon", "loop", 2, -31, {}),
    "amb_dusk": ("amb_dusk_crickets", "loop", 2, -29, {}),
    "amb_night": ("amb_night", "loop", 2, -30, {}),
    "amb_fireplace_room": ("amb_fireplace_room", "loop", 2, -28, {"ceil": -6}),
    "amb_stream": ("amb_stream", "loop", 1, -26, {"ceil": -6}),
    "amb_gust_1": ("amb_gust", "oneshot", 2, -28, {"n": 1}),
    "amb_gust_2": ("amb_gust", "oneshot", 2, -28, {"n": 2}),
    "spk_bird_robin": ("spk_bird_robin", "oneshot", 1, -26, {}),
    "spk_bird_finch": ("spk_bird_finch", "oneshot", 1, -26, {}),
    "spk_bird_blackbird": ("spk_bird_blackbird", "oneshot", 1, -26, {}),
    "spk_cuckoo": ("spk_cuckoo", "oneshot", 1, -28, {}),
    "spk_dove": ("spk_dove", "oneshot", 1, -28, {}),
    "spk_bee": ("spk_bee", "oneshot", 1, -28, {}),
    "spk_frog": ("spk_frog", "oneshot", 1, -27, {}),
    "spk_owl": ("spk_owl", "oneshot", 1, -28, {}),
    "foot_pig_grass": ("foot_pig_grass", "slice", 1, -22, {"count": 4}),
    "foot_pig_road": ("foot_pig_road", "slice", 1, -22, {"count": 4}),
    "foot_pig_bridge": ("foot_pig_bridge", "slice", 1, -22, {"count": 3}),
    "foot_wolf_grass": ("foot_wolf_grass", "slice", 1, -22, {"count": 4}),
    "foot_wolf_road": ("foot_wolf_road", "slice", 1, -22, {"count": 4}),
    "foot_wolf_bridge": ("foot_wolf_bridge", "slice", 1, -22, {"count": 3}),
    "foot_roof_tile": ("foot_roof_tile", "slice", 1, -22, {"count": 3}),
    "ladder_rungs": ("foot_ladder_rung", "slice", 1, -22, {"count": 3}),
    "door_open": ("door_creak_open", "oneshot", 1, -20, {}),
    "door_shut": ("door_shut", "oneshot", 1, -20, {}),
    "straw_rustle_1": ("build_straw_rustle", "oneshot", 1, -20, {"n": 1}),
    "straw_rustle_2": ("build_straw_rustle", "oneshot", 1, -20, {"n": 2}),
    "hammer_knocks": ("build_hammer_knock", "slice", 1, -20, {"count": 3}),
    "brick_thunks": ("build_brick_thunk", "slice", 1, -20, {"count": 3}),
    "build_done_chime": ("music_build_done_chime", "oneshot", 2, -20, {}),
    "pop_toy": ("ui_pop_toy", "oneshot", 1, -20, {}),
    "ui_count_tick": ("ui_count_tick", "oneshot", 1, -22, {}),
    "flute_phrase": ("music_flute_phrase", "oneshot", 1, -20, {}),
    "violin_phrase": ("music_violin_phrase", "oneshot", 1, -20, {}),
    "wolf_sniff": ("wolf_sniff", "oneshot", 1, -20, {}),
    "huff_1": ("wolf_huff_small", "oneshot", 1, -22, {}),
    "huff_2": ("wolf_huff_medium", "oneshot", 1, -20, {}),
    "huff_3": ("wolf_huff_large", "oneshot", 1, -18, {}),
    "straw_blow_apart": ("house_straw_blow_apart", "oneshot", 2, -18, {}),
    "wood_wobble": ("house_wood_wobble", "oneshot", 1, -20, {}),
    "wood_collapse": ("house_wood_collapse", "oneshot", 2, -18, {}),
    "brick_hold_thud": ("house_brick_hold_thud", "oneshot", 1, -20, {}),
    "wolf_flop": ("wolf_flop", "oneshot", 1, -20, {}),
    "ladder_raise": ("prop_ladder_raise", "oneshot", 1, -20, {}),
    "chimney_slide": ("wolf_chimney_slide", "oneshot", 1, -19, {}),
    "wolf_launch": ("wolf_launch_whoosh", "oneshot", 1, -18, {}),
    "wolf_yelp_far": ("wolf_yelp_far", "oneshot", 1, -22, {}),
    "fire_ignite": ("fire_ignite", "oneshot", 1, -20, {}),
    "fire_crackle_m": ("fire_crackle_m", "loop", 2, -26, {"ceil": -6}),
    "fire_crackle_l": ("fire_crackle_l", "loop", 2, -24, {"ceil": -6}),
    "boil_bubbles": ("kitchen_boil", "loop", 1, -24, {}),
    "splash_hiss": ("kitchen_splash_hiss", "oneshot", 2, -18, {}),
    "page_turn_1": ("paper_page_turn", "oneshot", 1, -20, {"n": 1}),
    "page_turn_2": ("paper_page_turn", "oneshot", 1, -20, {"n": 2}),
    "book_close": ("paper_book_close", "oneshot", 1, -20, {}),
}
CEIL_DB = -4.0  # one-shot / slice true-ish sample peak ceiling (voice peaks at -1.5)
BED_CEIL_DB = -10.0


def decode(path):
    if path.endswith(".pcm"):
        a = np.fromfile(path, dtype="<i2").astype(np.float32) / 32768.0
        return a.reshape(-1, 2)
    out = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(out, dtype=np.float32).reshape(-1, 2).copy()


def write_wav_f32(path, x):
    x = x if x.ndim == 2 else x[:, None]
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", str(x.shape[1]), "-i", "-",
                    path], input=x.astype("<f4").tobytes(), check=True)


def encode_ogg(x, path):
    """Vorbis q6 via oggenc (brew vorbis-tools; this ffmpeg build has no libvorbis). 24-bit WAV in between."""
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as t:
        w = t.name
    try:
        x = x if x.ndim == 2 else x[:, None]
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", str(x.shape[1]), "-i",
                        "-", "-map_metadata", "-1", "-fflags", "+bitexact", "-c:a", "pcm_s24le", w], input=x.astype("<f4").tobytes(), check=True)
        subprocess.run(["oggenc", "-Q", "-q", "6", "-o", path, w], check=True, stderr=subprocess.DEVNULL)
    finally:
        os.unlink(w)


def measure_file(path):
    """EBU R128 integrated loudness + true peak of a file (ffmpeg ebur128)."""
    r = subprocess.run(["ffmpeg", "-nostats", "-v", "info", "-i", path, "-af", "ebur128=peak=true:framelog=quiet",
                        "-f", "null", "-"], capture_output=True, text=True)
    t = r.stderr
    i = re.findall(r"I:\s+(-?[\d.]+|-inf) LUFS", t)
    tp = re.findall(r"Peak:\s+(-?[\d.]+|-inf) dBFS", t)
    f = lambda s: float("-inf") if s == "-inf" else float(s)
    return (f(i[-1]) if i else None), (f(tp[-1]) if tp else None)


def lufs(x):
    """Integrated loudness via ffmpeg; short clips (< 0.4 s gating block) fall back to a K-ish RMS estimate."""
    if len(x) < int(0.45 * SR):
        rms = np.sqrt(np.mean(np.square(x)) + 1e-12)
        return 20 * np.log10(rms) - 0.7
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as t:
        p = t.name
    try:
        write_wav_f32(p, x)
        i, _ = measure_file(p)
        if i is None or i == float("-inf") or i < -69:
            rms = np.sqrt(np.mean(np.square(x)) + 1e-12)
            return 20 * np.log10(rms) - 0.7
        return i
    finally:
        os.unlink(p)


def env_db(m, win=0.005):
    n = max(1, int(win * SR))
    k = len(m) // n
    e = np.sqrt(np.mean(np.square(m[: k * n]).reshape(k, n), axis=1) + 1e-12)
    return 20 * np.log10(e), n


def trim(x, head_db=-48, tail_db=-56):
    m = np.abs(x).max(axis=1) if x.ndim == 2 else np.abs(x)
    pk = m.max()
    if pk <= 0:
        return x
    e, n = env_db(x.mean(axis=1) if x.ndim == 2 else x)
    ref = e.max()
    on = np.where(e > max(head_db, ref - 40))[0]
    if len(on) == 0:
        return x
    s = max(0, on[0] * n - int(0.01 * SR))
    tail = np.where(e > max(tail_db, ref - 50))[0]
    t = min(len(x), (tail[-1] + 1) * n + int(0.06 * SR))
    return x[s:t]


def fades(x, fin=0.003, fout=0.04):
    x = x.copy()
    a, b = int(fin * SR), int(fout * SR)
    sh = (slice(None),) + ((None,) if x.ndim == 2 else ())
    if a:
        x[:a] *= np.linspace(0, 1, a)[sh]
    if b and b < len(x):
        x[-b:] *= np.linspace(1, 0, b)[sh] ** 2
    return x


def to_ch(x, ch):
    if ch == 1:
        return x.mean(axis=1) if x.ndim == 2 else x
    return x if x.ndim == 2 else np.stack([x, x], 1)


def norm(x, target, ceil_db):
    l = lufs(x)
    g = target - l
    pk = 20 * np.log10(np.abs(x).max() + 1e-12)
    if pk + g > ceil_db:
        g = ceil_db - pk
    return x * (10 ** (g / 20)), g


def limit_loop(y, target, ceil_db):
    """Loop-safe loudness: gain to the target, then ffmpeg alimiter at the ceiling, run over three copies end to end
    and the middle copy kept (the limiter state at the seam is the same as anywhere else, so the loop stays
    seamless). Used when a bed's transients (fire pops, water splashes) keep plain gain from reaching the target."""
    g = target - lufs(y)
    x3 = np.concatenate([y, y, y]) * (10 ** (g / 20))
    with tempfile.TemporaryDirectory() as td:
        a, b = os.path.join(td, "a.wav"), os.path.join(td, "b.wav")
        write_wav_f32(a, x3)
        lim = 10 ** (ceil_db / 20)
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", a, "-af",
                        f"alimiter=limit={lim:.4f}:attack=3:release=80:level=0", "-c:a", "pcm_f32le", b], check=True)
        out = subprocess.run(["ffmpeg", "-v", "error", "-i", b, "-f", "f32le", "-"], capture_output=True,
                             check=True).stdout
    z = np.frombuffer(out, dtype=np.float32)
    z = z.reshape(-1, y.shape[1]) if y.ndim == 2 else z
    n = len(y)
    return z[n: 2 * n].copy(), g


def seam(x):
    """Loop seam numbers on the mono mix: jump end->start and slope change, relative to the clip's own sample
    motion (p95 |diff|); level ratio of the last vs first 50 ms."""
    m = x.mean(axis=1) if x.ndim == 2 else x
    d = np.abs(np.diff(m))
    p95 = np.percentile(d, 95) + 1e-9
    jump = abs(m[0] - m[-1]) / p95
    slope = abs((m[1] - m[0]) - (m[-1] - m[-2])) / p95
    w = int(0.05 * SR)
    lvl = 20 * np.log10((np.sqrt(np.mean(m[-w:] ** 2)) + 1e-9) / (np.sqrt(np.mean(m[:w] ** 2)) + 1e-9))
    # spectral-ish continuity: rms of 200 ms blocks either side of the seam
    w2 = int(0.2 * SR)
    lvl2 = 20 * np.log10((np.sqrt(np.mean(m[-w2:] ** 2)) + 1e-9) / (np.sqrt(np.mean(m[:w2] ** 2)) + 1e-9))
    return {"jump": round(float(jump), 2), "slope": round(float(slope), 2), "edge_db": round(float(lvl), 2),
            "edge200_db": round(float(lvl2), 2)}


def seam_ok(s):
    return s["jump"] < 1.0 and s["slope"] < 1.0 and abs(s["edge200_db"]) < 3.0


def xfade_loop(x, xf=1.5):
    """Equal-power crossfade: the last xf seconds fade out over the first xf seconds; result length N - xf.
    Result end -> start continues the original signal (out[-1] = x[N-xf-1], out[0] ~ x[N-xf])."""
    n = int(xf * SR)
    sh = (slice(None),) + ((None,) if x.ndim == 2 else ())
    t = np.linspace(0, 1, n)
    fin, fout = np.sin(t * np.pi / 2), np.cos(t * np.pi / 2)
    out = x[: len(x) - n].copy()
    out[:n] = x[:n] * fin[sh] + x[len(x) - n:] * fout[sh]
    return out


def slice_hits(x, count, max_len=0.5):
    """Onsets: the 5 ms envelope crosses (loudest - 20 dB) after >= 60 ms below (loudest - 30 dB). Each hit runs to
    the next onset (or max_len), then its tail is cut where it stays 40 dB under the hit's own peak."""
    m = x.mean(axis=1) if x.ndim == 2 else x
    e, n = env_db(m, 0.005)
    ref = e.max()
    low = min(ref - 12, max(ref - 30, float(np.percentile(e, 30)) + 4))  # adaptive to the take's floor
    thr = min(ref - 6, low + 10)
    onsets, quiet, armed = [], 0, True
    for i, v in enumerate(e):
        if armed and v > thr:
            # back up to the start of the rise
            k = i
            while k > 0 and e[k - 1] < e[k] and e[k - 1] > low - 10:
                k -= 1
            onsets.append(k)
            armed, quiet = False, 0
            continue
        quiet = quiet + 1 if v < low else 0
        if quiet >= 8:
            armed = True
    segs = []
    for j, o in enumerate(onsets):
        end = onsets[j + 1] - 2 if j + 1 < len(onsets) else len(e)
        end = min(end, o + int(max_len / 0.005))
        seg = e[o:end]
        if len(seg) < 6:
            continue
        pk = seg.max()
        alive = np.where(seg > pk - 50)[0]
        stop = o + alive[-1] + 1
        a, b = max(0, o * n - int(0.005 * SR)), min(len(x), stop * n + int(0.04 * SR))
        segs.append((a, b, float(pk)))
    if not segs:
        return []
    med = np.median([p for _, _, p in segs])
    pick = sorted(sorted(segs, key=lambda s: abs(s[2] - med))[:count], key=lambda s: s[0])
    return [x[a:b] for a, b, _ in pick], len(segs)


def checks(x):
    pk = float(np.abs(x).max())
    clip = int(np.sum(np.abs(x) >= 0.999))
    return {"peak_dbfs": round(20 * np.log10(pk + 1e-12), 2), "clipped_samples": clip, "silent": pk < 0.01}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    jobs = {j["id"]: j for j in json.load(open(a.jobs))}
    raw = os.path.join(a.out, "raw")
    sfx = os.path.join(a.out, "sfx")
    os.makedirs(sfx, exist_ok=True)
    manifest = []
    for jid, (stem, mode, ch, target, extra) in RULES.items():
        src = [f for f in os.listdir(raw) if f.rsplit(".", 1)[0] == jid]
        if not src:
            print("missing raw", jid)
            continue
        x = decode(os.path.join(raw, src[0]))
        rawc = checks(x)
        job = jobs[jid]
        base = {"source_job": jid, "prompt": job["prompt"], "requested_s": job.get("duration"),
                "raw_peak_dbfs": rawc["peak_dbfs"], "raw_clipped": rawc["clipped_samples"]}
        outs = []
        if mode == "loop":
            y = to_ch(x, ch)
            s0 = seam(y)
            fixed = False
            if not seam_ok(s0):
                y = xfade_loop(y, 1.5 if len(y) > 8 * SR else 0.6)
                fixed = True
            ceil = extra.get("ceil", BED_CEIL_DB)
            y0, g = norm(y, target, ceil)
            limited = lufs(y0) < target - 1.5
            y = limit_loop(y, target, ceil)[0] if limited else y0
            outs.append((f"{stem}_1.ogg", y, {"loop": True, "seam_raw": s0, "seam": seam(y), "xfade_fixed": fixed, "limited": limited}))
        elif mode == "slice":
            res = slice_hits(x, extra["count"])
            if not res:
                print("no hits", jid)
                continue
            hits, found = res
            for k, h in enumerate(hits, 1):
                y = fades(to_ch(h, ch), 0.002, 0.03)
                y, g = norm(y, target, CEIL_DB)
                outs.append((f"{stem}_{k}.ogg", y, {"loop": False, "hits_found_in_take": found}))
        else:
            y = fades(trim(to_ch(x, ch)))
            y, g = norm(y, target, CEIL_DB)
            outs.append((f"{stem}_{extra.get('n', 1)}.ogg", y, {"loop": False}))
        for name, y, meta in outs:
            p = os.path.join(sfx, name)
            encode_ogg(y, p)
            I, tp = measure_file(p)
            c = checks(y)
            rec = dict(base)
            short = len(y) < int(0.45 * SR)
            rec.update({"file": f"sfx/{name}", "duration_s": round(len(y) / SR, 3), "channels": ch,
                        "lufs_i": round(float(lufs(y)), 1) if short else (None if I is None or I == float("-inf") else round(I, 1)),
                        "lufs_method": "rms_estimate_short_clip" if short else "ebur128_integrated",
                        "true_peak_dbfs": tp, "target_lufs": target, **c, **meta})
            manifest.append(rec)
            flag = "" if not c["silent"] and c["clipped_samples"] == 0 else "  <-- CHECK"
            sm = f" seam {meta['seam']} fixed={meta['xfade_fixed']}" if meta.get("loop") else ""
            print(f"{name:40s} {rec['duration_s']:6.2f}s I={rec['lufs_i']} TP={tp}{sm}{flag}")
    with open(os.path.join(sfx, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1, ensure_ascii=False)
    print(len(manifest), "files")


if __name__ == "__main__":
    main()
