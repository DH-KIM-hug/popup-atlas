#!/usr/bin/env python3
"""Technical listen-check of staged audio (nobody has heard these files; this only proves they are sane).

  python3 tools/audio/verify_audio.py --staging artifacts/audio_staging

For every .ogg under sfx/ and music/ (decoded with ffmpeg): duration, EBU R128 integrated loudness and true peak
(ebur128), sample peak, clipped samples (|x| >= 0.999), silence-only (peak < -40 dBFS), and for loops the seam:
end->start jump and slope change relative to the clip's p95 sample-to-sample motion (< 1.0 = no click), plus the
level of the last vs first 200 ms. Writes verify.json and prints a table + failures.
"""
import argparse, json, os, subprocess, sys
import numpy as np
sys.path.insert(0, os.path.dirname(__file__))
from process_sfx import measure_file, seam  # noqa: E402

def dec(p):
    out = subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-f", "f32le", "-ac", "2", "-ar", "48000", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(out, dtype=np.float32).reshape(-1, 2)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--staging", required=True); a = ap.parse_args()
    loops = set()
    for mf in ("sfx/manifest.json", "music/manifest.json"):
        for r in json.load(open(os.path.join(a.staging, mf))):
            if r.get("loop"):
                loops.add(r["file"])
    rows, fails = [], []
    for sub in ("sfx", "music"):
        for f in sorted(os.listdir(os.path.join(a.staging, sub))):
            if not f.endswith(".ogg"):
                continue
            rel = f"{sub}/{f}"; p = os.path.join(a.staging, rel)
            x = dec(p); I, tp = measure_file(p)
            pk = float(np.abs(x).max()); r = {"file": rel, "dur": round(len(x) / 48000, 3),
                 "lufs_i": I if I is not None and I > -69 else None, "true_peak": tp,
                 "peak_dbfs": round(20 * np.log10(pk + 1e-12), 2), "clipped": int((np.abs(x) >= 0.999).sum()),
                 "silent": pk < 0.01, "loop": rel in loops}
            if r["loop"]:
                r["seam"] = seam(x)
                if r["seam"]["jump"] >= 1.0 or r["seam"]["slope"] >= 1.0:
                    fails.append(f"{rel}: seam click risk {r['seam']}")
            if r["clipped"]: fails.append(f"{rel}: {r['clipped']} clipped samples")
            if r["silent"]: fails.append(f"{rel}: silent")
            rows.append(r)
    json.dump(rows, open(os.path.join(a.staging, "verify.json"), "w"), indent=1)
    for r in rows:
        s = f" seam j={r['seam']['jump']} s={r['seam']['slope']} edge200={r['seam']['edge200_db']}" if r["loop"] else ""
        print(f"{r['file']:40s} {r['dur']:7.2f}s I={r['lufs_i']} TP={r['true_peak']} pk={r['peak_dbfs']} clip={r['clipped']}{s}")
    print(len(rows), "files;", "FAILS:" if fails else "no failures", *fails, sep="\n")

if __name__ == "__main__":
    main()
