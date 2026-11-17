#!/usr/bin/env python3
"""Procedural paper SFX for pop-up motion (component C_motion). numpy only.
Writes game/audio/paper/{flap_up_*,fold_down_*,pat_*}.wav (44.1 kHz mono 16-bit) and prints a
JSON report per file: peak dBFS, audible duration (> -45 dB of peak envelope), spectral centroid.
  flap_up   : card snapping upright — band-passed noise burst (fast attack) + low thump + crinkle ticks
  fold_down : gentler — slow-swell low-passed air "fff" with a faint crinkle, no thump
  pat       : the piece landing on the page — soft low pat + tiny paper tick
usage: python3 game/audio/gen_paper_sfx.py [--seed 7]"""
import json, os, sys, wave
import numpy as np

SR = 44100
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "paper")


def band(x, lo, hi, soft=0.25):
    """Smooth FFT band-pass (log-gaussian skirts)."""
    n = len(x); X = np.fft.rfft(x, n * 2)
    f = np.fft.rfftfreq(n * 2, 1 / SR) + 1e-3
    g = np.ones_like(f)
    if lo > 0:
        g *= 1 / (1 + (lo / f) ** (2 / soft * 0.5))
    if hi < SR / 2:
        g *= 1 / (1 + (f / hi) ** (2 / soft * 0.5))
    return np.fft.irfft(X * g)[:n]


def env(n, attack, decay, curve=1.0):
    t = np.arange(n) / SR
    a = np.clip(t / max(attack, 1e-4), 0, 1) ** curve
    return a * np.exp(-np.maximum(t - attack, 0) / decay)


def fade_tail(x, ms=8):
    k = int(SR * ms / 1000); x[-k:] *= np.linspace(1, 0, k) ** 2; return x


def crinkle(rng, n, count, span, lo=2500, hi=9000, amp=0.5):
    y = np.zeros(n)
    for _ in range(count):
        p = int(rng.uniform(0, span) * SR)
        L = int(rng.uniform(0.0015, 0.006) * SR)
        if p + L >= n:
            continue
        y[p:p + L] += rng.normal(0, 1, L) * np.hanning(L) * rng.uniform(0.3, 1.0)
    return band(y, lo, hi) * amp


def flap_up(rng, i):
    dur = rng.uniform(0.13, 0.20); n = int(dur * SR)
    centre = [1100, 1600, 2200, 2900, 1350, 1900][i % 6] * rng.uniform(0.92, 1.08)
    noise = band(rng.normal(0, 1, n), centre * 0.45, centre * 2.2)
    body = noise * env(n, rng.uniform(0.002, 0.006), rng.uniform(0.025, 0.05), 0.7)
    # A second smaller flutter of the edge 20-40 ms later.
    d2 = int(rng.uniform(0.02, 0.045) * SR)
    fl = np.zeros(n); fl[d2:] = noise[: n - d2] * env(n - d2, 0.004, 0.03) * rng.uniform(0.35, 0.6)
    t = np.arange(n) / SR
    f0 = rng.uniform(75, 140)
    thump = np.sin(2 * np.pi * f0 * t * (1 - 0.25 * t / dur)) * env(n, 0.003, rng.uniform(0.018, 0.035)) * rng.uniform(0.5, 0.9)
    ck = crinkle(rng, n, rng.integers(4, 10), dur * 0.6, amp=rng.uniform(0.25, 0.5))
    return fade_tail(body + fl + thump + ck)


def fold_down(rng, i):
    dur = rng.uniform(0.18, 0.25); n = int(dur * SR)
    hi = [900, 1300, 1800, 2400][i % 4] * rng.uniform(0.9, 1.1)
    noise = band(rng.normal(0, 1, n), 180, hi)
    t = np.arange(n) / SR
    sw = np.sin(np.pi * np.clip(t / (dur * 0.9), 0, 1)) ** 1.6  # swell up and away
    ck = crinkle(rng, n, rng.integers(2, 5), dur * 0.8, lo=2000, hi=6000, amp=0.12)
    return fade_tail(noise * sw + ck)


def pat(rng, i):
    dur = rng.uniform(0.06, 0.10); n = int(dur * SR)
    t = np.arange(n) / SR
    f0 = [110, 150, 190][i % 3] * rng.uniform(0.9, 1.1)
    low = np.sin(2 * np.pi * f0 * t) * env(n, 0.002, 0.014)
    tap = band(rng.normal(0, 1, n), 300, [1800, 2600, 3500][i % 3]) * env(n, 0.001, 0.008) * 0.8
    tick = crinkle(rng, n, 2, 0.02, amp=0.15)
    return fade_tail(low + tap + tick)


def write(path, x, peak_db):
    x = x / np.max(np.abs(x)) * 10 ** (peak_db / 20)
    pcm = np.clip(np.round(x * 32767), -32768, 32767).astype("<i2")
    with wave.open(path, "wb") as w:
        w.setnchannels(1); w.setsampwidth(2); w.setframerate(SR); w.writeframes(pcm.tobytes())
    return pcm.astype(np.float64) / 32768


def report(path, x):
    peak = np.max(np.abs(x)); peak_db = 20 * np.log10(peak)
    k = int(SR * 0.004); e = np.sqrt(np.convolve(x ** 2, np.ones(k) / k, "same"))
    on = np.where(e > e.max() * 10 ** (-45 / 20))[0]
    aud = (on[-1] - on[0]) / SR if len(on) else 0
    X = np.abs(np.fft.rfft(x)); f = np.fft.rfftfreq(len(x), 1 / SR)
    cen = float((X * f).sum() / X.sum())
    return {"file": os.path.basename(path), "peak_dbfs": round(peak_db, 2), "clipped": bool(np.max(np.abs(x)) >= 0.999),
            "len_ms": round(len(x) / SR * 1000), "audible_ms": round(aud * 1000), "centroid_hz": round(cen)}


def main():
    seed = int(sys.argv[sys.argv.index("--seed") + 1]) if "--seed" in sys.argv else 7
    rng = np.random.default_rng(seed)
    os.makedirs(OUT, exist_ok=True)
    rows = []
    for name, fn, count, pk in (("flap_up", flap_up, 6, -3.0), ("fold_down", fold_down, 4, -6.0), ("pat", pat, 3, -4.0)):
        for i in range(count):
            p = os.path.join(OUT, f"{name}_{i + 1}.wav")
            rows.append(report(p, write(p, fn(rng, i), pk)))
    for r in rows:
        print(json.dumps(r))


if __name__ == "__main__":
    main()
