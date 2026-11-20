#!/usr/bin/env python3
"""12 evenly spaced frames per beat from a full recording (checklist review): beat times from the run log's
STORY_DONE beats={...}.  python3 tools/story/beat_sheets.py <run.log> <video.mp4> <out_dir> [offset_s]
offset_s = video time of story clock 0 (the movie starts with the app; default 0)."""
import json, os, re, subprocess, sys
log, vid, out = sys.argv[1], sys.argv[2], sys.argv[3]
off = float(sys.argv[4]) if len(sys.argv) > 4 else 0.0
txt = open(log, errors="replace").read()
m = re.search(r"STORY_DONE total=([\d.]+) .*beats=(\{.*\})", txt)
total = float(m.group(1))
beats = sorted(json.loads(m.group(2)).items(), key=lambda kv: kv[1])
os.makedirs(out, exist_ok=True)
for i, (b, t0) in enumerate(beats):
    t1 = beats[i + 1][1] if i + 1 < len(beats) else total
    if t1 - t0 < 1:
        continue
    step = (t1 - t0) / 12.0
    sel = "+".join(f"between(t\\,{t0 + off + step * (k + 0.5):.2f}\\,{t0 + off + step * (k + 0.5) + 0.034:.2f})" for k in range(12))
    subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-ss", f"{max(0, t0 + off - 1):.2f}", "-t",
                    f"{t1 - t0 + 2:.2f}", "-i", vid, "-vf",
                    f"setpts=PTS+{max(0, t0 + off - 1):.2f}/TB,select='{sel}',scale=420:-1,tile=4x3", "-frames:v", "1",
                    "-fps_mode", "passthrough", os.path.join(out, f"{i:02d}_{b}.jpg")], check=False)
    print(b, round(t0, 1), round(t1, 1))
