# Tooling: Godot slot, imports, recording, probes, shell

## One Godot per project
- One Godot process per project at a time (import races mark files valid=false). Run every Godot command through
  `tools/story/with_godot.sh <command ...>` (a mkdir lock dir with pid + trap; it waits while another agent holds it).
- The shared slot: with four agents chaining Godot jobs, `with_godot.sh`'s 3 s poll lost the race for 30+ minutes; a
  waiter that polls the lock dir every 0.2 s and then takes it the same way (mkdir + pid + trap) gets a turn:
  `tools/story/slot_wait.sh <command>`. It must do the mkdir itself on every poll: a waiter that only watched the dir
  and then exec'd with_godot.sh lost the race once and sat in with_godot's 3 s poll for 30 min. Never nest them
  (a script run under slot_wait that calls with_godot.sh — house_orbit.sh does — waits on its own lock forever).
- A full gate recording in one call: `tools/story/slot_wait.sh tools/story/full_rec.sh TALE /ABS/out.mp4 MAX_S`
  (--import, 1200x900, frame cap MAX_S·30 so the slot is never held forever, --log-sound --log-track, AVI to Trash).
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
- One beat at the gate's size: `tools/story/with_godot.sh tools/story/w1_beat.sh TALE BEAT SEC /ABS/out.mp4`
  (1200x900, --log-track --log-sound, the AVI to ~/.Trash); then `motion_review.py TALE out.log out.mp4`.
- Movie-maker runs build the next page in one go (StoryRunner `_movie`): the per-frame wall-time budget of the
  page prebuild turned into story time when the machine was slow (patjuk gate v1b froze 14 min on the cover with the
  disk 99 % full). Recordings need no `--fixed` for this.
- `RUNNER_OFF_TREE` in a log: a runner coroutine resumed after the runner left the tree (app quit / scene change);
  `_frame` now parks it. Before 2026-11-24 this spun `_wait` forever in one frame (`get_tree()` null, 0 s steps):
  patjuk gate v1 wrote 5 GB of errors and never ended. Never call `get_tree()` in a loop without an in-tree check.
- Run-log flags: `--log-sound` (SFX lines), `--log-track` (StoryActor TRACK lines: foot point and on-screen height 8×/s
  while travelling), `--log-figs` (TRAVEL_FIG: the figure each travel uses). StoryActor prints MOVE lines for every
  travel segment (motion_review.py reads them); the legacy Walker (sun_wind's traveller) prints them through
  WalkerLog (figures `<pose>:rig`). `CAPTION 1|0 t=` lines say when the caption strip shows (OFF_FRAME check).
- Motion tiles by hand: `tools/story/tiles.py IN.mp4 START DUR X Y W H OUT.jpg [cols]` (8 fps, crop, 2× scale);
  the gate's `tools/story/motion_review.py` cuts them per segment automatically.
- A full disk ruins a run silently (2026-11-25): the movie writer warned "available space is low", the AVI came out
  corrupt (ffmpeg mjpeg errors, a 61 s mp4 of a 361 s story) and the run log lost most lines (no SEG / MOVE, 2k
  PERF hitch lines) while STORY_DONE and the summary still printed. Moving AVIs to ~/.Trash does NOT free space. Check
  `df` before a full run (a 6 min run at 1200x900 is ~6 GB of AVI), and after it compare the mp4 duration with
  STORY_DONE and count MOVE lines before reviewing anything.

## Probes
- `tools/story/probe_spots.gd` (ground map around the anchor), `tools/story/probe_spots_wide.gd` (roads for streets),
  `tools/story/probe_ground_tn.gd` (ground cover patch heights), `tools/story/house_orbit_all.sh` + `house_audit.py`
  (house solidity, sets.md).

## Shell
- Never `rm $VAR/*` — use literal paths or `"${VAR:?}"`; move old files to ~/.Trash.
- zsh does not word-split `$var`, so `run_jobs.py ... $group` passed one bogus id and exited silently; run loops under
  `bash -c`.
- Commit + push per milestone, only your own paths (`git commit -- <paths>`).

- The shared slot under load (wolf_goats v2, 2026-11-25: five agents chaining 15-min full recordings): a beat test
  waited 30-45 min for its turn. Batch every beat you need into ONE slot hold (tools/story/wg_beats.sh TAG
  beat:sec ...), trust the full run for the rest, and never kill a waiter with with_godot.sh's own trap (it would
  remove the holder's lock dir): `kill -9` only your own waiting PID.
