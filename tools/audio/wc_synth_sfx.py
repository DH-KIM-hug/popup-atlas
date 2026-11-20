#!/usr/bin/env python3
"""witch_candy SFX placeholders (2026-11-20): short cartoon cues synthesised with numpy (no licensed source needed),
written as game/audio/sfx/wc_<name>_1.wav and registered in game/audio/sound_catalog.json as wc.<name>.
They are PLACEHOLDERS: nobody has listened; replace with recorded / CC0 files later (same ids).

  python3 tools/audio/wc_synth_sfx.py
"""
import json, os, wave
import numpy as np

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
SR = 44100
rng = np.random.default_rng(7)


def t(d):
    return np.arange(int(SR * d)) / SR


def env(n, a=0.005, r=0.1):
    e = np.ones(n)
    na, nr = int(SR * a), int(SR * r)
    if na:
        e[:na] = np.linspace(0, 1, na)
    if nr:
        e[-nr:] *= np.linspace(1, 0, nr) ** 2
    return e


def sweep(f0, f1, d, shape="sin"):
    tt = t(d)
    f = f0 * (f1 / f0) ** (tt / d)
    ph = 2 * np.pi * np.cumsum(f) / SR
    if shape == "saw":
        return 2 * ((ph / (2 * np.pi)) % 1) - 1
    if shape == "sq":
        return np.sign(np.sin(ph))
    return np.sin(ph)


def noise(d):
    return rng.normal(0, 1, len(t(d)))


def lp(x, k=8):
    return np.convolve(x, np.ones(k) / k, mode="same")


def bell(f, d, decay=4.0):
    tt = t(d)
    return sum(a * np.sin(2 * np.pi * f * m * tt) * np.exp(-decay * m ** 0.5 * tt) for m, a in [(1, 1), (2.76, .4), (5.4, .2)])


def at(x, dl, total):
    """x delayed by dl seconds in a buffer of `total` seconds."""
    out = np.zeros(int(SR * total))
    i = int(SR * dl)
    n = min(len(x), len(out) - i)
    out[i:i + n] = x[:n]
    return out


S = {}
S["boing"] = sweep(260, 900, 0.32) * env(len(t(0.32)), 0.004, 0.12) * (1 + 0.3 * np.sin(2 * np.pi * 18 * t(0.32)))   # 뿅
S["sparkle"] = sum(at(bell(f, 0.6, 5), dl, 0.9) for f, dl in [(1568, 0), (2093, .08), (2637, .16), (3136, .24)])
S["poof"] = lp(noise(0.55), 30) * env(len(t(0.55)), 0.01, 0.4) * 2.5 + 0.4 * sweep(180, 60, 0.55) * env(len(t(0.55)), 0.005, 0.3)
S["bubble"] = np.concatenate([sweep(500 + 200 * k, 1400 + 300 * k, 0.06) * env(len(t(0.06)), 0.002, 0.03) for k in range(3)] + [np.zeros(400)])
S["candy_pop"] = at(sweep(900, 1600, 0.09) * env(len(t(0.09)), 0.001, 0.06), 0, 0.3) + 0.5 * at(bell(2400, 0.3, 9), 0, 0.3)
S["drip"] = sweep(1800, 500, 0.12) * env(len(t(0.12)), 0.001, 0.08)
S["siren"] = np.concatenate([sweep(700, 700, 0.18, "sq") * 0.3, sweep(950, 950, 0.18, "sq") * 0.3] * 2) * env(len(t(0.72)), 0.01, 0.05)
S["buzz"] = lp(sweep(180, 220, 0.5, "saw"), 4) * env(len(t(0.5)), 0.05, 0.2) * (0.7 + 0.3 * np.sin(2 * np.pi * 30 * t(0.5)))
S["chime"] = at(bell(1047, 1.0, 3), 0, 1.0) + 0.6 * at(bell(1319, 0.9, 3), .1, 1.0)
S["kazoo"] = lp(sweep(140, 110, 0.45, "saw"), 3) * env(len(t(0.45)), 0.02, 0.15) * (1 + 0.2 * np.sin(2 * np.pi * 7 * t(0.45)))  # 뿡
S["quack"] = lp(sweep(520, 380, 0.16, "saw") * (1 + 0.5 * np.sin(2 * np.pi * 1100 * t(0.16))), 3) * env(len(t(0.16)), 0.005, 0.06)
S["plop"] = sweep(320, 90, 0.18) * env(len(t(0.18)), 0.002, 0.12)
S["splash"] = lp(noise(0.5), 6) * env(len(t(0.5)), 0.003, 0.4)
S["wave"] = lp(noise(0.9), 14) * np.sin(np.pi * t(0.9) / 0.9) ** 1.5
S["whoosh"] = lp(noise(0.5), 10) * np.sin(np.pi * t(0.5) / 0.5) ** 2
S["flame"] = lp(noise(0.7), 5)[:len(t(0.7))] * env(len(t(0.7)), 0.08, 0.4) + 0.3 * sweep(90, 160, 0.7) * env(len(t(0.7)), 0.08, 0.4)
S["stir"] = sum(at(bell(f, 0.5, 6), dl, 1.4) for f, dl in [(1319, 0), (1568, .15), (1760, .3), (2093, .45), (2349, .6), (2637, .75)])
S["roll"] = lp(noise(1.2), 40) * (0.6 + 0.4 * np.sin(2 * np.pi * 6 * t(1.2))) * env(len(t(1.2)), 0.1, 0.3)
S["bonk"] = sweep(220, 110, 0.25) * env(len(t(0.25)), 0.001, 0.2) + 0.3 * lp(noise(0.25), 3) * env(len(t(0.25)), 0.001, 0.22)
S["flap"] = np.concatenate([lp(noise(0.07), 8) * env(len(t(0.07)), 0.005, 0.05), np.zeros(int(SR * 0.09))] * 3)
S["ribbit"] = np.concatenate([lp(sweep(300, 260, 0.08, "saw"), 3) * env(len(t(0.08)), 0.003, 0.03), np.zeros(1200),
                              lp(sweep(330, 280, 0.12, "saw"), 3) * env(len(t(0.12)), 0.003, 0.05)])
S["glow"] = (np.sin(2 * np.pi * 220 * t(1.4)) + 0.5 * np.sin(2 * np.pi * 330 * t(1.4))) * np.sin(np.pi * t(1.4) / 1.4)
S["flutter"] = np.concatenate([lp(noise(0.05), 12) * env(len(t(0.05)), 0.005, 0.03), np.zeros(int(SR * 0.06))] * 5)
S["giggle_bells"] = sum(at(bell(f, 0.4, 8), dl, 0.9) for f, dl in [(2093, 0), (2637, .12), (3136, .24), (2637, .36)])
S["vanish"] = sweep(1200, 3000, 0.35) * env(len(t(0.35)), 0.005, 0.25) * 0.6 + 0.4 * at(S["sparkle"], 0, 0.35)

GAIN = {"poof": -8, "wave": -9, "glow": -12, "roll": -10, "splash": -9, "flame": -9, "whoosh": -10}


def main():
    cat_p = os.path.join(ROOT, "game", "audio", "sound_catalog.json")
    cat = json.load(open(cat_p))
    for name, x in S.items():
        x = x / max(1e-6, np.abs(x).max()) * 0.5  # -6 dBFS peak before the catalog gain
        out = os.path.join(ROOT, "game", "audio", "sfx", f"wc_{name}_1.wav")  # 16-bit mono WAV (no vorbis encoder here)
        w = wave.open(out, "w")
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((x * 32767).astype(np.int16).tobytes())
        w.close()
        cat["sounds"][f"wc.{name}"] = {"files": [f"res://audio/sfx/wc_{name}_1.wav"], "bus": "SFX",
                                       "gain_db": GAIN.get(name, -10), "pitch_rand": 0.05, "vol_rand_db": 1,
                                       "no_repeat": False, "positional": False, "loop": False,
                                       "note": "witch_candy placeholder, synthesised (tools/audio/wc_synth_sfx.py)"}
    json.dump(cat, open(cat_p, "w"), ensure_ascii=False, indent=1)
    print(len(S), "wc sounds")


if __name__ == "__main__":
    main()
