#!/usr/bin/env python3
"""Lay the planned sound over a capture of the tale so the direction can be heard (preview only).

  python3 tools/audio/preview_mix.py --cues tools/audio/three_pigs_preview_cues.json \
      --catalog tools/audio/sound_catalog.json --staging artifacts/audio_staging \
      --out artifacts/audio_staging/preview_three_pigs.mp4

The capture's own track (narration + paper flaps) is the Voice bus. Music and Ambience are ducked under it with the
catalog's bus settings (an RMS sidechain, attack / release smoothing). Beds come from catalog.beds (layers +
random sprinkles from catalog.sprinkle_sets, seeded; gusts at random intervals plus the cue sheet's synced gusts);
the stream emitter is approximated by a per-time gain envelope (camera distance to the water read off the frames).
Footstep runs pick a random variation per step (no immediate repeat), ±pitch/volume from the catalog.
"""
import argparse
import json
import os
import random
import subprocess
import sys

import numpy as np

SR = 48000


def dec(path, ch=2):
    out = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", str(ch), "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(out, dtype=np.float32).reshape(-1, ch).copy()


class Mixer:
    def __init__(self, a):
        self.a = a
        self.cat = json.load(open(a.catalog))
        self.cache = {}

    def res(self, p):
        return os.path.join(self.a.staging, p.replace("res://audio/", ""))

    def load(self, p):
        if p not in self.cache:
            self.cache[p] = dec(self.res(p))
        return self.cache[p]


def db(x):
    return 10 ** (x / 20)


def place(buf, x, t, gain=1.0, pan=0.0):
    i = int(t * SR)
    if i >= len(buf) or i + len(x) <= 0:
        return
    x = x[: len(buf) - i]
    ang = (pan + 1) * np.pi / 4
    lr = np.array([np.cos(ang), np.sin(ang)]) * np.sqrt(2)
    buf[i: i + len(x)] += x * gain * lr[None, :]


def resample(x, ratio):
    if abs(ratio - 1) < 1e-4:
        return x
    n = int(len(x) / ratio)
    idx = np.arange(n) * ratio
    i0 = np.minimum(idx.astype(int), len(x) - 2)
    fr = (idx - i0)[:, None]
    return x[i0] * (1 - fr) + x[i0 + 1] * fr


def loop_fill(x, length):
    reps = int(np.ceil(length / len(x))) + 1
    return np.concatenate([x] * reps)[:length]


def ramp(n, fi, fo):
    g = np.ones(n)
    a, b = int(fi * SR), int(fo * SR)
    if a:
        g[: min(a, n)] = np.linspace(0, 1, a)[: min(a, n)]
    if b and b < n:
        g[-b:] *= np.linspace(1, 0, b)
    return g


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cues", required=True)
    ap.add_argument("--catalog", required=True)
    ap.add_argument("--staging", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    m = Mixer(a)
    cat = m.cat
    cues = json.load(open(a.cues))
    rng = random.Random(cues.get("seed", 1))
    voice = dec(cues["video"])
    N = len(voice)
    T = N / SR
    music = np.zeros((N, 2), np.float32)
    amb = np.zeros((N, 2), np.float32)
    sfx = np.zeros((N, 2), np.float32)
    last_pick = {}
    log = []

    def one(sid, t, extra_db=0.0, pan=None, bus=None):
        s = cat["sounds"][sid]
        files = s["files"]
        k = rng.randrange(len(files))
        if s.get("no_repeat") and len(files) > 1 and last_pick.get(sid) == k:
            k = (k + 1 + rng.randrange(len(files) - 1)) % len(files)
        last_pick[sid] = k
        x = m.load(files[k])
        pr = s.get("pitch_rand", 0)
        x = resample(x, 1 + rng.uniform(-pr, pr)) if pr else x
        g = s["gain_db"] + extra_db + rng.uniform(-s.get("vol_rand_db", 0) / 2, s.get("vol_rand_db", 0) / 2)
        target = bus or (amb if s["bus"] == "Ambience" else sfx)
        place(target, x, t, db(g), pan if pan is not None else rng.uniform(-0.25, 0.25))
        log.append((round(t, 2), sid, files[k].split("/")[-1], round(g, 1)))

    # --- voice sidechain (RMS 20 ms, attack/release smoothing)
    w = int(0.02 * SR)
    k = N // w
    vr = 20 * np.log10(np.sqrt((voice[: k * w].mean(1) ** 2).reshape(k, w).mean(1)) + 1e-9)

    def duck_curve(d):
        thr = d["threshold_db"]
        tgt = d["target_reduction_db"]
        raw = np.where(vr > thr, tgt, 0.0)
        out = np.zeros_like(raw)
        aa = np.exp(-0.02 / (d["attack_ms"] / 1000))
        rr = np.exp(-0.02 / (d["release_ms"] / 1000))
        v = 0.0
        for i, r in enumerate(raw):
            c = aa if r < v else rr
            v = c * v + (1 - c) * r
            out[i] = v
        g = np.repeat(db(out), w)
        return np.concatenate([g, np.full(N - len(g), g[-1])])[:, None]

    voice_active = np.repeat(vr > cat["buses"]["Music"]["duck"]["threshold_db"], w)

    # --- music
    for t0, t1, slot, fi, fo, gdb in cues["music"]:
        mu = cat["music"][slot]
        x = m.load(mu["file"])
        n = int((min(t1, T) - t0) * SR)
        y = loop_fill(x, n) if mu["loop"] else x[:n]
        y = y * ramp(len(y), fi, fo)[:, None] * db(mu["gain_db"] + gdb)
        place(music, y, t0, 1.0, 0.0)
        log.append((t0, "music." + slot, mu["file"].split("/")[-1], gdb))

    # --- beds: layers + sprinkles + gusts
    bf = cues.get("bed_fade", 2.0)
    for t0, t1, bed in cues["beds"]:
        b = cat["beds"][bed]
        t1 = min(t1, T)
        n = int((t1 - t0) * SR)
        env = ramp(n, bf if t0 > 0.5 else 0.5, bf)[:, None]
        for sid, ldb in b["layers"]:
            s = cat["sounds"][sid]
            x = m.load(s["files"][0])
            off = rng.randrange(len(x))  # start each layer at a random point of its loop
            y = loop_fill(np.roll(x, -off, axis=0), n) * env * db(s["gain_db"] + ldb)
            place(amb, y, t0, 1.0, 0.0)
        sp = b.get("sprinkles")
        if sp:
            st = cat["sprinkle_sets"][sp]
            lastt = {}
            t = t0 + rng.uniform(*st["interval"]) * 0.5
            while t < t1 - 3:
                items = st["items"]
                ok = [it for it in items if t - lastt.get(it[0], -1e9) >= (it[2] if len(it) > 2 else 0)]
                if ok:
                    wts = [it[1] for it in ok]
                    it = rng.choices(ok, wts)[0]
                    lastt[it[0]] = t
                    extra = rng.uniform(*st["gain_db"])
                    if voice_active[min(int(t * SR), N - 1)]:
                        extra -= 6  # under a line: quieter
                    one(it[0], t, extra, rng.uniform(-0.8, 0.8))
                t += rng.uniform(*st["interval"])
        gu = b.get("gusts")
        if gu:
            t = t0 + rng.uniform(*gu["every"]) * 0.5
            while t < t1 - 4:
                one("amb.gust", t, rng.uniform(*gu["gain_db"]), rng.uniform(-0.6, 0.6))
                t += rng.uniform(*gu["every"])

    # --- stream emitter (proximity envelope)
    st = cat["sounds"]["amb.stream"]
    x = m.load(st["files"][0])
    pts = np.array(cues["stream_db"], float)
    tt = np.arange(N) / SR
    g = db(np.interp(tt, pts[:, 0], pts[:, 1]) + st["gain_db"])[:, None]
    amb += loop_fill(x, N) * g

    for t, gdb in cues.get("gusts", []):
        one("amb.gust", t, gdb, rng.uniform(-0.3, 0.3))

    # --- continuous loops (fire / boil)
    for t0, t1, sid, fi, fo, gdb in cues["loops"]:
        s = cat["sounds"][sid]
        xx = m.load(s["files"][0])
        n = int((t1 - t0) * SR)
        y = loop_fill(xx, n) * ramp(n, fi, fo)[:, None] * db(s["gain_db"] + gdb)
        place(amb, y, t0, 1.0, 0.0)
        log.append((t0, sid, "loop", gdb))

    # --- footsteps
    for t0, t1, sid, iv, walkers, g0, g1 in cues["steps"]:
        for wk in range(walkers):
            t = t0 + wk * iv * 0.37 + rng.uniform(0, 0.05)
            pan = (wk - (walkers - 1) / 2) * 0.3
            while t < t1:
                f = (t - t0) / max(t1 - t0, 1e-3)
                one(sid, t, g0 + (g1 - g0) * f - (2 if walkers > 1 else 0), pan)
                t += iv * rng.uniform(0.94, 1.06)

    # --- one-shot cues
    for t, sid, gdb in cues["cues"]:
        one(sid, t, gdb)

    # --- buses
    music *= duck_curve(cat["buses"]["Music"]["duck"])
    amb *= duck_curve(cat["buses"]["Ambience"]["duck"])
    # instruments played on screen duck the music further while they sound
    for t, sid, _ in cues["cues"]:
        d = cat["sounds"][sid].get("duck_music_db")
        if d:
            i0, i1 = int(t * SR), int((t + 3.5) * SR)
            music[i0:i1] *= db(d)
    mix = voice + music + amb + sfx
    tmp = os.path.splitext(a.out)[0] + "_mix.wav"
    stems = {"music": music, "amb": amb, "sfx": sfx}
    with open(os.path.splitext(a.out)[0] + "_log.json", "w") as f:
        json.dump(sorted(log), f, indent=0)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-",
                    "-af", "alimiter=limit=0.89:attack=2:release=60:level=0:latency=1", "-c:a", "pcm_s16le", tmp],
                   input=mix.astype("<f4").tobytes(), check=True)
    for k2, v in stems.items():
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "2", "-i", "-",
                        "-c:a", "pcm_s16le", os.path.splitext(a.out)[0] + f"_stem_{k2}.wav"],
                       input=v.astype("<f4").tobytes(), check=True)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", cues["video"], "-i", tmp, "-map", "0:v", "-map", "1:a",
                    "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", a.out], check=True)
    print("wrote", a.out, "events", len(log))


if __name__ == "__main__":
    main()
