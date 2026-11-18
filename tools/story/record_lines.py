#!/usr/bin/env python3
"""Record the changed / new lines of a tale's script.json with ElevenLabs, using the SAME voice ids, models and
voice settings as 톡톡 동화극장 (the `voices`, `models`, `settings` tables kept in script.json).

  python3 tools/story/record_lines.py [--tale sun_wind]   # record every used seg with status changed-needs-recording
  python3 tools/story/record_lines.py --tale three_pigs --dry      # list what would be recorded (and the character count)
  python3 tools/story/record_lines.py --redo sw_013,sw_n01   # record these lines again

Sent text follows 톡톡's gen_tale.py: the seg's acting tags ("[cheerful, ...]") + " " + text.
Clip name follows 톡톡 too: <speaker>_<md5(voice|model|sent|settings)[:10]>.mp3, so a changed text gets a new file.
After saving, each clip is polished with 톡톡's tools/elevenlabs/polish.py (log=False: nothing is written into the
read-only source app). Clips go to game/audio/voice/<tale>/ and are listed in recorded.json
("speaker|tags|text" -> file name); then tools/story/seed_script.py --tale <tale> --force fills them into script.json
(status "changed-recorded"). API key: ~/.config/elevenlabs/key (never stored in the repo).
"""
import hashlib, json, os, sys, time, urllib.error, urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TALE_ID = sys.argv[sys.argv.index("--tale") + 1] if "--tale" in sys.argv else "sun_wind"
SCRIPT = REPO / f"game/stories/{TALE_ID}/script.json"
OUT = REPO / f"game/audio/voice/{TALE_ID}"
MANIFEST = OUT / "recorded.json"
SRC_TOOLS = Path("/Users/house_of_4k2b/projects/2026/patjuk-game/tools/elevenlabs")
BASE_SETTINGS = {"stability": 0.5, "similarity_boost": 0.75, "style": 0.3}


def tts(path: Path, voice: str, text: str, model: str, settings: dict) -> None:
    key = (Path.home() / ".config/elevenlabs/key").read_text().strip()
    body = {"text": text, "model_id": model, "voice_settings": {**BASE_SETTINGS, **settings}}
    for attempt in range(6):
        r = urllib.request.Request(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice}?output_format=mp3_44100_128",
            json.dumps(body).encode(), {"xi-api-key": key, "Content-Type": "application/json"})
        try:
            data = urllib.request.urlopen(r, timeout=120).read()
            path.write_bytes(data)
            return
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503) and attempt < 5:
                time.sleep(3 * (attempt + 1))
                continue
            raise


def main() -> None:
    dry = "--dry" in sys.argv
    redo = set(sys.argv[sys.argv.index("--redo") + 1].split(",")) if "--redo" in sys.argv else set()
    sc = json.loads(SCRIPT.read_text(encoding="utf-8"))
    voices, models, sets = sc["voices"], sc.get("models", {}), sc.get("settings", {})
    man = json.loads(MANIFEST.read_text(encoding="utf-8")) if MANIFEST.exists() else {}
    if not dry:
        sys.path.insert(0, str(SRC_TOOLS))
        from polish import polish  # noqa: E402  (read-only import; polish(path, log=False) touches only `path`)
        OUT.mkdir(parents=True, exist_ok=True)
    chars = 0
    for l in sc["lines"]:
        if not l.get("used", True):
            continue
        for s in l["segs"]:
            if s["status"] == "reuse":
                continue
            if s["status"] == "changed-recorded" and l["id"] not in redo:
                continue
            sp, text, tags = s["speaker"], s["text"], s.get("tags") or ""
            model = models.get(sp, "eleven_v3")
            st = sets.get(sp)
            sent = (tags + " " + text) if tags else text
            h = hashlib.md5((f"{voices[sp]}|{model}|{sent}" + (f"|{json.dumps(st, sort_keys=True)}" if st else "")).encode()).hexdigest()[:10]
            name = f"{sp}_{h}.mp3"
            chars += len(sent)
            print(("DRY " if dry else "REC ") + l["id"], sp, model, name, sent)
            if dry:
                continue
            path = OUT / name
            if not path.exists() or l["id"] in redo:
                tts(path, voices[sp], sent, model, st or {})
                polish(str(path), log=False)
            man[f"{sp}|{tags}|{text}"] = name
    print("chars", chars)
    if not dry:
        MANIFEST.write_text(json.dumps(man, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print("wrote", MANIFEST, f"- now run: python3 tools/story/seed_script.py --tale {TALE_ID} --force")


if __name__ == "__main__":
    main()
