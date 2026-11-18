#!/usr/bin/env python3
"""Perf harness (component F). Windowed runs through the scenario-godot-expert toolkit.

  python3 tools/perf/profile.py TAG meadow [metal|vulkan] [seconds]
  python3 tools/perf/profile.py TAG beat:<beat_id> [metal|vulkan] [seconds]     # story from that beat, autoplay, mute

Writes game/profile/perf_TAG_<what>_<driver>.csv and prints one summary JSON line:
frame p50/p95/p99/max, gpu p95/max (Vulkan only), draw calls max/mean, primitives max, objects max,
frames over 33/50 ms with their t_s, pipeline compiles, plus PERF/BEAT/SPREAD prints from the run.
Plain-engine equivalent: godot --path game --rendering-driver vulkan res://stories/sun_wind/story.tscn -- --beat=wind_turn --autoplay --mute
with RenderingServer.viewport_set_measure_render_time + Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME logged per frame.
"""
import sys, json, csv, statistics
sys.path.insert(0, "/Users/house_of_4k2b/.claude/skills/scenario-godot-expert/scripts")
import gd_run

P = "/Users/house_of_4k2b/orca/popup-atlas/game"


def pct(v, p):
    v = sorted(v)
    return v[min(len(v) - 1, int(p / 100.0 * (len(v) - 1)))] if v else 0.0


def summarise(path, skip_s=0.0):
    rows = list(csv.DictReader(open(path)))
    rows = [r for r in rows if float(r["t_s"]) >= skip_s]
    f = [float(r["frame_ms"]) for r in rows]
    g = [float(r["gpu_ms"]) for r in rows]
    c = [float(r["cpu_ms"]) for r in rows]
    d = [float(r["draw_calls"]) for r in rows]
    pr = [float(r["primitives"]) for r in rows]
    ob = [float(r["objects"]) for r in rows]
    pw = [float(r["process_wall_ms"]) for r in rows]
    pc = [float(r["pipeline_compiles"]) for r in rows]
    spikes = []
    for k, r in enumerate(rows):
        if float(r["frame_ms"]) > 33.0:
            dpc = int(float(r["pipeline_compiles"]) - float(rows[k - 1]["pipeline_compiles"])) if k else 0
            spikes.append((round(float(r["t_s"]), 2), round(float(r["frame_ms"]), 1), dpc))
    return {
        "frames": len(f), "p50": round(pct(f, 50), 2), "p95": round(pct(f, 95), 2), "p99": round(pct(f, 99), 2),
        "max": round(max(f), 1) if f else 0,
        "gpu_p95": round(pct(g, 95), 2), "gpu_max": round(max(g), 2) if g else 0, "cpu_p95": round(pct(c, 95), 2),
        "proc_p95": round(pct(pw, 95), 2),
        "draws_max": int(max(d)) if d else 0, "draws_mean": int(statistics.mean(d)) if d else 0,
        "prims_max": int(max(pr)) if pr else 0, "objects_max": int(max(ob)) if ob else 0,
        "over33": len(spikes), "over50": sum(1 for s in spikes if s[1] > 50), "spikes": spikes[:40],
        "pipeline_compiles_delta": int(pc[-1] - pc[0]) if pc else 0,
    }


def main():
    tag, what = sys.argv[1], sys.argv[2]
    drv = sys.argv[3] if len(sys.argv) > 3 else "metal"
    secs = float(sys.argv[4]) if len(sys.argv) > 4 else 8.0
    size = (1366, 1024)
    args = {}
    if what == "meadow":
        scene = "res://scenes/world/meadow.tscn"
    elif what.startswith("beat:"):
        scene = "res://stories/sun_wind/story.tscn"
        args = {"beat": what.split(":", 1)[1], "autoplay": True, "mute": True, "subtitles": False}
    else:
        raise SystemExit("what = meadow | beat:<id>")
    name = what.replace(":", "_")
    csvp = f"profile/perf_{tag}_{name}_{drv}.csv"
    xa = ["--disable-vsync"] if "novsync" in drv else None
    d = drv.replace("-novsync", "")
    r = gd_run.profile_scene(P, scene, seconds=secs, warmup=20, size=size, driver=None if d == "metal" else d,
                             csv=csvp, args=args, timeout=secs + 400, extra_args=xa)
    res = r.get("result") or {}
    out = {"tag": tag, "what": what, "driver": drv, "ok": bool(r.get("ok") and res.get("ok"))}
    if res.get("csv"):
        out.update(summarise(res["csv"]))
    out["prints"] = [p for p in r.get("prints", []) if p.startswith(("PERF", "BEAT", "SPREAD view", "MEADOW", "STORY_DONE"))][:80]
    errs = (r.get("script_errors", []) + r.get("engine_errors", []) + r.get("shader_errors", []))
    out["errors"] = [str(e)[:300] for e in errs[:8]]
    print(json.dumps(out, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
