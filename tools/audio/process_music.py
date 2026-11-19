#!/usr/bin/env python3
"""Trim / loop-point / normalise the downloaded CC0 music for the pop-up storybook.

  python3 tools/audio/process_music.py --out artifacts/audio_staging

Downloads live in <out>/downloads/<slot>/<file> (one new empty directory per download; untrusted data, only ever
read through ffmpeg). Output: <out>/music/music_<slot>_1.ogg (Vorbis q6, 48 kHz stereo) + music/manifest.json.

Loop method (bar maths from a spectral-flux autocorrelation, see TRACKS):
  - "whole":  the file is a designed loop (its length is a whole number of bars) -> loop = the whole file, a 20 ms
              crossfade across the seam.
  - "fold":   the musical body is N bars from `start`, followed by a ring-out. Loop end = start + N * bar; the
              ring-out after the loop end is mixed back over the head (as a real repeat would overlap it).
  - "once":   not looped; leading silence trimmed, a short fade in, a fade out over the last `fade_out` seconds.
Loudness: -22 LUFS integrated (peak ceiling -3 dBFS).
"""
import argparse
import json
import os
import subprocess
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from process_sfx import SR, encode_ogg, measure_file, norm, seam  # noqa: E402

TRACKS = {
    "home": {"file": "home_song17/song17.mp3", "mode": "fold", "start": 0.0, "bar": 2.4, "bars": 16,
             "title": "Happy Lullaby (song17)", "author": "cynicmusic", "license": "CC0",
             "page": "https://opengameart.org/content/happy-lullaby-song17",
             "url": "https://opengameart.org/sites/default/files/song17.mp3",
             "page_words": "\"Beautiful bells and arpeggios\"; tags lullaby, happy, calm, relaxing, bells; \"Easy for perfect loop\""},
    "build": {"file": "build_full_of_energy/520192.mp3", "mode": "whole", "bar": 1.739, "bars": 20,
              "title": "Full of Energy", "author": "code_box", "license": "CC0 (Freesound: Creative Commons 0)",
              "page": "https://freesound.org/people/code_box/sounds/520192/",
              "url": "https://cdn.freesound.org/previews/520/520192_10962806-hq.mp3",
              "page_words": "tags glockenspiel, orchestra, pizzicato, plucked, strings, tuba, upbeat, vibraphone; called a loop",
              "note": "Freesound HQ preview mp3 (the original WAV needs a login)"},
    "wolf": {"file": "wolf_playful_music/381531.mp3", "mode": "fold", "start": 0.0, "bar": 1.96, "bars": 16,
             "title": "Playful Music", "author": "dominictreis", "license": "CC0 (Freesound: Creative Commons 0)",
             "page": "https://freesound.org/people/dominictreis/sounds/381531/",
             "url": "https://cdn.freesound.org/previews/381/381531_5058825-hq.mp3",
             "page_words": "\"playful/sneaky music\"; tags Bassoon, Vibraphone, Playful, Sneaky",
             "note": "Freesound HQ preview mp3"},
    "chimney": {"file": "chimney_rabbit_bop/575759.mp3", "mode": "whole", "bar": 2.4, "bars": 16,
                "title": "Rabbit Bop", "author": "code_box", "license": "CC0 (Freesound: Creative Commons 0)",
                "page": "https://freesound.org/people/code_box/sounds/575759/",
                "url": "https://cdn.freesound.org/previews/575/575759_10962806-hq.mp3",
                "page_words": "\"bunnies... need to be very quick, when they spot the fox!\"; tags cartoon, double-bass, marimba, energetic, hopping, loop",
                "note": "Freesound HQ preview mp3; the author says the preview is affected by compression and the WAV (login) is cleaner"},
    "ending": {"file": "ending_snow_globe/snow_globe.ogg", "mode": "once", "fade_out": 3.0,
               "title": "Snow Globe", "author": "Bobjt", "license": "CC0",
               "page": "https://opengameart.org/content/snow-globe",
               "url": "https://opengameart.org/sites/default/files/snow_globe_shorter_original.ogg",
               "page_words": "\"Could also make decent intro or ending music\"; tags Classical, arpeggios, ending, Wonderous"},
    "night": {"file": "night_twinkle/554160.mp3", "mode": "once", "fade_out": 3.0,
              "title": "Twinkle", "author": "Bigvegie", "license": "CC0 (Freesound: Creative Commons 0)",
              "page": "https://freesound.org/people/Bigvegie/sounds/554160/",
              "url": "https://cdn.freesound.org/previews/554/554160_11740799-hq.mp3",
              "page_words": "\"Simple piano lullaby style chord sequence\"", "note": "Freesound HQ preview mp3"},
}


def decode(path):
    out = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(out, dtype=np.float32).reshape(-1, 2).copy()


def lead_trim(x, db=-55):
    m = np.abs(x).max(axis=1)
    on = np.where(m > 10 ** (db / 20))[0]
    return x[max(0, on[0] - int(0.005 * SR)):] if len(on) else x


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    dl = os.path.join(a.out, "downloads")
    od = os.path.join(a.out, "music")
    os.makedirs(od, exist_ok=True)
    man = []
    for slot, t in TRACKS.items():
        x = decode(os.path.join(dl, t["file"]))
        src_dur = len(x) / SR
        info = {}
        if t["mode"] == "whole":
            y = x.copy()
            n = int(0.02 * SR)
            r = np.linspace(0, 1, n)[:, None]
            # 20 ms: fade the last samples into the first ones (end continues into start)
            y[:n] = y[:n] * r + y[-n:] * (1 - r)
            y = y[:-n]
            info = {"loop": True, "loop_start_s": 0.0, "loop_end_s": round(len(y) / SR, 3),
                    "bars": t["bars"], "bar_s": t["bar"]}
        elif t["mode"] == "fold":
            s = int(t["start"] * SR)
            e = s + int(round(t["bar"] * t["bars"] * SR))
            y = x[s:e].copy()
            tail = x[e:].copy()
            tl = min(len(tail), len(y))
            tail = tail[:tl]
            fo = int(0.3 * SR)
            if tl > fo:
                tail[-fo:] *= np.linspace(1, 0, fo)[:, None]
            y[:tl] += tail
            info = {"loop": True, "loop_start_s": 0.0, "loop_end_s": round(len(y) / SR, 3), "bars": t["bars"],
                    "bar_s": t["bar"], "source_cut_s": [t["start"], round(e / SR, 3)],
                    "ring_out_folded_s": round(tl / SR, 2)}
        else:
            y = lead_trim(x)
            fi, fo = int(0.01 * SR), int(t["fade_out"] * SR)
            y[:fi] *= np.linspace(0, 1, fi)[:, None]
            # trailing silence
            m = np.abs(y).max(axis=1)
            last = np.where(m > 10 ** (-60 / 20))[0][-1]
            y = y[: last + 1]
            y[-fo:] *= (np.linspace(1, 0, fo) ** 2)[:, None]
            info = {"loop": False, "in_s": 0.0, "out_s": round(len(y) / SR, 3), "fade_out_s": t["fade_out"]}
        y, g = norm(y, -22.0, -3.0)
        name = f"music_{slot}_1.ogg"
        p = os.path.join(od, name)
        encode_ogg(y, p)
        I, tp = measure_file(p)
        rec = {"file": f"music/{name}", "slot": slot, "duration_s": round(len(y) / SR, 3),
               "source_duration_s": round(src_dur, 3), "lufs_i": I, "true_peak_dbfs": tp,
               "clipped_samples": int(np.sum(np.abs(y) >= 0.999)), **info,
               **{k: t[k] for k in ("title", "author", "license", "page", "url", "page_words") if k in t}}
        if t.get("note"):
            rec["note"] = t["note"]
        if info.get("loop"):
            rec["seam"] = seam(y)
        man.append(rec)
        print(f"{name:24s} {rec['duration_s']:6.2f}s I={I} TP={tp} loop={info.get('loop')} seam={rec.get('seam')}")
    with open(os.path.join(od, "manifest.json"), "w") as f:
        json.dump(man, f, indent=1, ensure_ascii=False)


if __name__ == "__main__":
    main()
