"""witch_candy: remix the two premixed choruses (ghost_all "오~~우~~", happy_all "해피 핼러윈! 오~우~!") from 톡톡's current
per-voice clips (kid + witch + cat, no friends), same recipe as 톡톡 tales/witch_candy/mix_chorus_el.py, written into
game/audio/voice/witch_candy/. 2026-11-22: 톡톡 moved the girl to Kurumin Cute but did not remix these two.
The source repo is read only; nothing is written there."""
import json, re, hashlib, subprocess, sys
from pathlib import Path
SRC = Path("/Users/house_of_4k2b/projects/2026/patjuk-game")
OUT = Path(__file__).resolve().parents[2] / "game/audio/voice/witch_candy"
DELAY_MS, GAIN, MAIN_GAIN, TEMPO = [0, 70, 30, 120, 50], .30, 1.0, (.8, 1.25)
js = (SRC / "tales/witch_candy/narration_el.js").read_text()
vl = json.loads(re.search(r"Object\.assign\(VOICE_LINES, (\{.*?\n\})\);", js, re.S).group(1))
dur = lambda p: float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)], capture_output=True, text=True).stdout)
for key in ("ghost_all", "happy_all"):
    urls = [u for u in vl[key] if not re.search(r"/(rabbit|bear|fox)_[0-9a-f]{10}\.mp3$", u)]
    h = hashlib.md5(("|".join(urls) + f"|{DELAY_MS}|{GAIN}|{MAIN_GAIN}|{TEMPO}").encode()).hexdigest()[:10]
    dst = OUT / f"ch_{h}.mp3"
    ds = [dur(SRC / u) for u in urls]
    main = sorted(range(len(urls)), key=lambda i: ds[i])[len(urls) // 2]
    args = ["ffmpeg", "-loglevel", "error", "-y"] + [a for u in urls for a in ("-i", str(SRC / u))]
    parts = []
    for i in range(len(urls)):
        r = min(TEMPO[1], max(TEMPO[0], ds[i] / ds[main])) if i != main else 1.0
        tempo = f"atempo={r:.4f}," if abs(r - 1) > .01 else ""
        parts.append(f"[{i}:a]aresample=44100,{tempo}adelay={DELAY_MS[i % 5] if i != main else 0}:all=1,volume={MAIN_GAIN if i == main else GAIN}[a{i}];")
    f = "".join(parts) + "".join(f"[a{i}]" for i in range(len(urls))) + f"amix=inputs={len(urls)}:duration=longest:normalize=0,alimiter=limit=0.9[out]"
    subprocess.run(args + ["-filter_complex", f, "-map", "[out]", "-ac", "1", "-b:a", "96k", str(dst)], check=True)
    print(key, dst.name, urls)
