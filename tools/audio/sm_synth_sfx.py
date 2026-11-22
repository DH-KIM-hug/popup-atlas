#!/usr/bin/env python3
"""「해님 달님」 SFX placeholders (2026-11-22): short cues synthesised with numpy (the witch_candy helpers), written as
game/audio/sfx/sm_<name>_1.wav and registered in game/audio/sound_catalog.json as sm.<name> (the ids the tale's SOUND
block uses). PLACEHOLDERS: nobody has listened; the tiger's growl is kept cute (a low purring rumble, never a roar).
Writes a shared catalog: run through tools/story/with_godot.sh.

  tools/story/with_godot.sh python3 tools/audio/sm_synth_sfx.py
"""
import json, os, sys, wave
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wc_synth_sfx import ROOT, SR, t, env, sweep, noise, lp, bell, at

S = {}
_g = t(0.7)
S["growl_cute"] = lp(sweep(95, 75, 0.7, "saw"), 6) * (0.6 + 0.4 * np.sin(2 * np.pi * 22 * _g)) * env(len(_g), 0.06, 0.3)
S["gulp"] = sweep(320, 120, 0.16) * env(len(t(0.16)), 0.003, 0.1) + 0.4 * at(sweep(200, 90, 0.12) * env(len(t(0.12)), 0.002, 0.08), 0.12, 0.3)[:len(t(0.16))]
S["gulp_big"] = np.concatenate([S["gulp"], np.zeros(1500), S["gulp"] * 0.9, np.zeros(1500), S["gulp"] * 1.1])
S["twinkle"] = sum(at(bell(f, 0.5, 7), dl, 0.7) for f, dl in [(2637, 0), (3136, .1)])
S["bolt"] = lp(noise(0.3), 10) * env(len(t(0.3)), 0.01, 0.1) * 0.6 + at(sweep(180, 120, 0.12) * env(len(t(0.12)), 0.001, 0.1), 0.26, 0.4)[:len(t(0.3))]
S["paper_rustle"] = lp(noise(0.6), 3) * (0.5 + 0.5 * np.abs(np.sin(2 * np.pi * 7 * t(0.6)))) * env(len(t(0.6)), 0.02, 0.2) * 0.5
S["paper_poke"] = at(sweep(1400, 600, 0.05) * env(len(t(0.05)), 0.001, 0.03), 0, 0.35) + 0.4 * at(lp(noise(0.25), 3) * env(len(t(0.25)), 0.002, 0.2), 0.03, 0.35)
S["blink"] = at(bell(1760, 0.25, 12), 0, 0.3) * 0.6
S["scurry"] = np.concatenate([lp(noise(0.04), 6) * env(len(t(0.04)), 0.002, 0.03), np.zeros(int(SR * 0.07))] * 6)
S["oil_glug"] = np.concatenate([sweep(260 + 40 * k, 140, 0.09) * env(len(t(0.09)), 0.003, 0.05) for k in range(4)] + [np.zeros(800)])
S["slide"] = lp(noise(0.9), 12) * np.linspace(1, 0.2, len(t(0.9))) + 0.3 * sweep(500, 180, 0.9)
S["chop"] = at(sweep(260, 140, 0.1) * env(len(t(0.1)), 0.001, 0.08), 0, 0.3) + 0.5 * at(lp(noise(0.06), 2) * env(len(t(0.06)), 0.001, 0.05), 0, 0.3)
S["rope_creak"] = lp(sweep(420, 380, 0.6, "saw"), 5) * (0.5 + 0.5 * np.sin(2 * np.pi * 9 * t(0.6))) * env(len(t(0.6)), 0.05, 0.2) * 0.6
S["rope_snap"] = lp(noise(0.25), 2) * env(len(t(0.25)), 0.0005, 0.2) + at(sweep(900, 200, 0.15) * env(len(t(0.15)), 0.001, 0.1), 0, 0.25)
GAIN = {"growl_cute": -12, "slide": -11, "paper_rustle": -12, "twinkle": -14, "blink": -14}


def main():
    cat_p = os.path.join(ROOT, "game", "audio", "sound_catalog.json")
    cat = json.load(open(cat_p))  # re-read right before writing (shared file)
    for name, x in S.items():
        x = x / max(1e-6, np.abs(x).max()) * 0.5
        out = os.path.join(ROOT, "game", "audio", "sfx", f"sm_{name}_1.wav")
        w = wave.open(out, "w")
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(SR)
        w.writeframes((x * 32767).astype(np.int16).tobytes())
        w.close()
        cat["sounds"][f"sm.{name}"] = {"files": [f"res://audio/sfx/sm_{name}_1.wav"], "bus": "SFX",
                                       "gain_db": GAIN.get(name, -10), "pitch_rand": 0.05, "vol_rand_db": 1,
                                       "no_repeat": False, "positional": False, "loop": False,
                                       "note": "sunmoon placeholder, synthesised (tools/audio/sm_synth_sfx.py)"}
    json.dump(cat, open(cat_p, "w"), ensure_ascii=False, indent=1)
    print(len(S), "sm sounds")


if __name__ == "__main__":
    main()
