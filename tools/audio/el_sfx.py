#!/usr/bin/env python3
"""ElevenLabs Sound Effects (text-to-sound-effects) batch generator for the pop-up storybook.

Reads a jobs JSON (list of {id, prompt, duration, loop?, influence?}), generates each job that has no raw file yet,
and writes raw audio to <out>/raw/<id>.<ext>. Every API call is counted in <out>/el_ledger.json; the run refuses to
go past --cap generations in total (retries included). The key is read from ~/.config/elevenlabs/key and is never
printed or written anywhere.

  python3 tools/audio/el_sfx.py --jobs tools/audio/three_pigs_sfx_jobs.json --out artifacts/audio_staging [--only id,id]
                                [--redo id] [--dry] [--cap 70]
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.request

API = "https://api.elevenlabs.io/v1/sound-generation"
MODEL = "eleven_text_to_sound_v2"
FORMATS = ["pcm_48000", "mp3_44100_192", "mp3_44100_128"]  # first one the account accepts wins


def key() -> str:
    p = os.path.expanduser("~/.config/elevenlabs/key")
    with open(p) as f:
        return f.read().strip()


def load_ledger(path):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {"count": 0, "calls": []}


def save_ledger(path, led):
    with open(path, "w") as f:
        json.dump(led, f, indent=1, ensure_ascii=False)


def call(job, fmt, k):
    body = {"text": job["prompt"], "model_id": MODEL, "prompt_influence": job.get("influence", 0.5)}
    if job.get("duration"):
        body["duration_seconds"] = float(job["duration"])
    if job.get("loop"):
        body["loop"] = True
    req = urllib.request.Request(f"{API}?output_format={fmt}", data=json.dumps(body).encode(),
                                 headers={"xi-api-key": k, "Content-Type": "application/json", "Accept": "*/*"})
    with urllib.request.urlopen(req, timeout=180) as r:
        return r.read()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--jobs", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--only", default="")
    ap.add_argument("--redo", default="", help="comma ids to regenerate (counts as a retry)")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--cap", type=int, default=70)
    a = ap.parse_args()
    jobs = json.load(open(a.jobs))
    raw = os.path.join(a.out, "raw")
    os.makedirs(raw, exist_ok=True)
    ledp = os.path.join(a.out, "el_ledger.json")
    led = load_ledger(ledp)
    only = set(filter(None, a.only.split(",")))
    redo = set(filter(None, a.redo.split(",")))
    todo = []
    for j in jobs:
        if only and j["id"] not in only:
            continue
        have = [f for f in os.listdir(raw) if f.rsplit(".", 1)[0] == j["id"]]
        if have and j["id"] not in redo:
            continue
        todo.append(j)
    print(f"ledger {led['count']} used, {len(todo)} to generate, cap {a.cap}")
    if a.dry:
        for j in todo:
            print(" ", j["id"], j.get("duration"), "loop" if j.get("loop") else "")
        return
    if led["count"] + len(todo) > a.cap:
        sys.exit(f"refusing: {led['count']} + {len(todo)} > cap {a.cap}")
    k = key()
    fmt_ok = led.get("format")
    for j in todo:
        fmts = [fmt_ok] if fmt_ok else FORMATS
        data = None
        for fmt in fmts:
            try:
                data = call(j, fmt, k)
                fmt_ok = fmt
                break
            except urllib.error.HTTPError as e:
                msg = e.read()[:300].decode("utf-8", "replace")
                print(f"  {j['id']} {fmt}: HTTP {e.code} {msg}")
                if e.code in (401, 429) or fmt == fmts[-1]:
                    break
        if data is None:
            continue
        led["count"] += 1
        led["format"] = fmt_ok
        led["calls"].append({"id": j["id"], "t": time.strftime("%Y-%m-%d %H:%M:%S"), "fmt": fmt_ok,
                             "retry": j["id"] in redo, "bytes": len(data)})
        save_ledger(ledp, led)
        ext = "pcm" if fmt_ok.startswith("pcm") else "mp3"
        for f in os.listdir(raw):
            if f.rsplit(".", 1)[0] == j["id"]:
                os.replace(os.path.join(raw, f), os.path.join(raw, "_old_" + f))
        with open(os.path.join(raw, f"{j['id']}.{ext}"), "wb") as f:
            f.write(data)
        print(f"  ok {j['id']} ({len(data)} B) total {led['count']}")
    print(f"done, ledger {led['count']}")


if __name__ == "__main__":
    main()
