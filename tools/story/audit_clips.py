#!/usr/bin/env python3
"""Clip audit (witch_candy v8, user: "말풍선에는 하나만 써있는데 두번 말하는 경우가 있어"): find voice clips that say their
caption twice. No local STT is installed, so two signals:
  rate   — Hangul syllables of the seg text / speech seconds (silences < -35 dB removed); a doubled take talks at about
           half its speaker's median rate,
  repeat — the clip's log-spectrogram correlated with itself shifted by every lag from 0.6 s to half its length: a
           take said twice peaks high at the repeat lag (normal speech stays low).
  python3 tools/story/audit_clips.py <tale> [<tale> ...]     -> a table; FLAG rows to listen to / trim
"""
import json, re, subprocess, sys
from pathlib import Path
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
SR = 16000


def load(p):
    out = subprocess.run(["ffmpeg", "-v", "error", "-i", str(p), "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True).stdout
    return np.frombuffer(out, np.float32)


def speech_secs(x):
    f = 400
    n = len(x) // f
    if n == 0:
        return 0.0
    rms = np.sqrt((x[: n * f].reshape(n, f) ** 2).mean(1) + 1e-12)
    db = 20 * np.log10(rms + 1e-9)
    return float((db > -35).sum() * f / SR)


def spec(x):
    hop, win = 160, 512
    n = 1 + (len(x) - win) // hop
    if n < 10:
        return None
    w = np.hanning(win)
    frames = np.stack([x[i * hop: i * hop + win] * w for i in range(n)])
    mag = np.abs(np.fft.rfft(frames, axis=1))[:, 4:160]
    s = np.log(mag + 1e-4)
    s -= s.mean(1, keepdims=True)
    energy = np.sqrt((frames ** 2).mean(1))
    return s, energy


def repeat_score(x):
    r = spec(x)
    if r is None:
        return 0.0, 0.0
    s, e = r
    voiced = e > np.percentile(e, 40)
    best, lag_best = 0.0, 0.0
    n = len(s)
    for lag in range(60, n // 2 + 1, 4):  # 0.6 s .. half the clip (hop 10 ms)
        a, b = s[:-lag], s[lag:]
        m = voiced[:-lag] & voiced[lag:]
        if m.sum() < 40:
            continue
        av, bv = a[m].ravel(), b[m].ravel()
        c = float(np.corrcoef(av, bv)[0, 1])
        if c > best:
            best, lag_best = c, lag / 100.0
    return best, lag_best


def main():
    rows = []
    for tale in sys.argv[1:]:
        sc = json.loads((ROOT / f"game/stories/{tale}/script.json").read_text(encoding="utf-8"))
        for l in sc["lines"]:
            if not l.get("used"):
                continue
            for i, sg in enumerate(l["segs"]):
                a = sg.get("audio", "")
                if not a:
                    continue
                p = ROOT / "game" / a.replace("res://", "")
                x = load(p)
                syl = len(re.findall(r"[가-힣]", sg["text"]))
                sp = speech_secs(x)
                rep, lag = repeat_score(x)
                rows.append([tale, l["id"], i, sg["speaker"], syl, sp, syl / max(sp, 0.1), rep, lag, sg["text"], p.name])
    by = {}
    for r in rows:
        by.setdefault((r[0], r[3]), []).append(r[6])
    print("tale       line          seg spk     syl speech rate  med   rep  lag  flag  text")
    for r in rows:
        med = float(np.median(by[(r[0], r[3])]))
        flag = []
        if r[4] >= 4 and r[6] < 0.55 * med:
            flag.append("SLOW")
        if r[7] > 0.62 and r[1] not in ("",):
            flag.append("REPEAT")
        print(f"{r[0]:10} {r[1]:13} {r[2]:3} {r[3]:7} {r[4]:3} {r[5]:5.2f} {r[6]:5.2f} {med:5.2f} {r[7]:5.2f} {r[8]:4.1f} "
              f"{'FLAG ' + '+'.join(flag) if flag else '':12} {r[9][:30]}  {r[10]}")


if __name__ == "__main__":
    main()


def blocks(x, thr_db=-32, min_gap=0.12):
    f = 160
    n = len(x) // f
    rms = np.sqrt((x[: n * f].reshape(n, f) ** 2).mean(1) + 1e-12)
    on = 20 * np.log10(rms + 1e-9) > thr_db
    out, start, gap = [], None, 0
    for i, v in enumerate(on):
        if v:
            if start is None:
                start = i
            gap = 0
        elif start is not None:
            gap += 1
            if gap * f / SR >= min_gap:
                out.append((start * f / SR, (i - gap + 1) * f / SR))
                start, gap = None, 0
    if start is not None:
        out.append((start * f / SR, n * f / SR))
    return [b for b in out if b[1] - b[0] > 0.25]


def block_pairs(x):
    """highest similarity between two speech blocks of similar length (a take said twice)"""
    bl = blocks(x)
    best = (0.0, None)
    for i in range(len(bl)):
        for j in range(i + 1, len(bl)):
            a, b = bl[i], bl[j]
            la, lb = a[1] - a[0], b[1] - b[0]
            if min(la, lb) < 0.4 or max(la, lb) / min(la, lb) > 1.5:
                continue
            s1 = spec(x[int(a[0] * SR):int(a[1] * SR)])
            s2 = spec(x[int(b[0] * SR):int(b[1] * SR)])
            if s1 is None or s2 is None:
                continue
            s1, s2 = s1[0], s2[0]
            n = min(len(s1), len(s2))
            c = float(np.corrcoef(s1[np.linspace(0, len(s1) - 1, n).astype(int)].ravel(),
                                  s2[np.linspace(0, len(s2) - 1, n).astype(int)].ravel())[0, 1])
            if c > best[0]:
                best = (c, (a, b))
    return best


if __name__ == "__main__" and "--pairs" in sys.argv:
    pass
