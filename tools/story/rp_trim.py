#!/usr/bin/env python3
"""「라푼젤」 trimmed takes (TRIM_SEG in tools/story/tales/rapunzel.py): one caption, one voice.
Read-only source clips (톡톡) -> game/audio/voice/rapunzel/<name>_t.mp3 with short fades. Spans from an ElevenLabs
speech-to-text word timing + silencedetect (2026-11-23):
  prince_8fbc9c7e0b  "라푼젤, 라푼젤, 라푼젤, 라푼젤, 라푼젤 어디로 갔을까? 라푼젤." (11.2 s)  -> 6.70-9.30 s
  rap_0433eb0505     "[웃음] 어머, 할머니가 아니네? 어머, 할머니가 아니네?" (5.3 s)        -> 0.00-2.85 s
"""
import os, subprocess
SRC = "/Users/house_of_4k2b/projects/2026/patjuk-game/audio/el/rapunzel/"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "game/audio/voice/rapunzel/")
SPANS = {"prince_8fbc9c7e0b": (6.70, 9.30), "rap_0433eb0505": (0.0, 2.85)}
os.makedirs(OUT, exist_ok=True)
for n, (a, b) in SPANS.items():
    d = b - a
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-ss", str(a), "-t", str(d), "-i", SRC + n + ".mp3", "-af",
                    f"afade=t=in:d=0.04,afade=t=out:st={d - 0.12:.2f}:d=0.12", "-b:a", "128k", OUT + n + "_t.mp3"], check=True)
    print(n, a, b)
