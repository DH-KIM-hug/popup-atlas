# Tooling: Godot slot, imports, recording, probes, shell

## One Godot per project
- One Godot process per project at a time (import races mark files valid=false). Run every Godot command through
  `tools/story/with_godot.sh <command ...>` (a mkdir lock dir with pid + trap; it waits while another agent holds it).
- The shared slot: with four agents chaining Godot jobs, `with_godot.sh`'s 3 s poll lost the race for 30+ minutes; a
  waiter that polls the lock dir every 0.2 s and then takes it the same way (mkdir + pid + trap) gets a turn.
- Waiting on a background recording: wait on its PID; `pgrep -f "<script name>"` also matches the waiting shell itself
  and never ends. Never kill processes you didn't start, never kill by pattern.

## Imports
- After regenerating art (house bands, leg cards), import before recording (`--import`, or
  `gd_run.import_project("game")`): a run with stale imported textures and a new stages.json drew the bands scrambled.
- `.import` with `valid=false` (a webp rewritten while another agent's Godot imported): "Failed loading resource" in the
  run log; move the .import away and import again. Grep run logs for "Failed loading" after art changes.
- Never run the cast builder's standing pass while Godot imports: it rewrites every figure file and the import reads
  half-written webps (ERR_FILE_CORRUPT); import after the art jobs finish.

## Recording
- Record what the user will see at 1200x900 with an absolute `--write-movie` path, `--import` first after new assets.
  On this Mac (1920x1080, usable 960) a 1024-tall window is clamped to 928, stretch "expand" widens the view to
  1507x1024, and the top-left page tab and top-right subtitle button land outside the video (user, 2026-11-22: "왼쪽
  오른쪽 상단 글자 잘리는데"). 1200x900 keeps the 1366x1024 canvas whole. Per-tale wrappers: tools/story/tn_rec.sh,
  wg_rec.sh, pj_rec.sh, rp_rec.sh (import → record → mp4 → avi to Trash); single beats: `tools/story/rec_beat.sh TALE
  BEAT SEC out.mp4`; many beats: `tools/story/cap_beats.py TALE tag 40 <beats...>`.
- Movie maker (`--write-movie`, windowed) records audio+video but crops the frame edges slightly on this Mac; check UI
  layout with `gd_run.capture_scene` instead (but its stills do not follow story camera shots: camera.md).
- For capture, use a fixed step (`--fixed-fps 30`) so autoplay recordings are frame-identical across runs.
- Run-log flags: `--log-sound` (SFX lines), `--log-track` (StoryActor TRACK lines: foot point and on-screen height 8×/s
  while travelling), `--log-figs` (TRAVEL_FIG: the figure each travel uses). StoryActor prints MOVE lines for every
  travel segment (motion_review.py reads them).
- Motion tiles by hand: `tools/story/tiles.py IN.mp4 START DUR X Y W H OUT.jpg [cols]` (8 fps, crop, 2× scale);
  the gate's `tools/story/motion_review.py` cuts them per segment automatically.

## Probes
- `tools/story/probe_spots.gd` (ground map around the anchor), `tools/story/probe_spots_wide.gd` (roads for streets),
  `tools/story/probe_ground_tn.gd` (ground cover patch heights), `tools/story/house_orbit_all.sh` + `house_audit.py`
  (house solidity, sets.md).

## Shell
- Never `rm $VAR/*` — use literal paths or `"${VAR:?}"`; move old files to ~/.Trash.
- zsh does not word-split `$var`, so `run_jobs.py ... $group` passed one bogus id and exited silently; run loops under
  `bash -c`.
- Commit + push per milestone, only your own paths (`git commit -- <paths>`).
