# Engine: script.json, seeding, runner, handlers, branches

Schema and every verb / field: script_schema.md. Runner: `game/story/story_runner.gd`; stage:
`game/story/spread_stage.gd`; actors: `game/story/story_actor.gd`; puppets: `game/art/cast/rig/cast_puppet.gd`.

## Seeding and the source of truth
- Write `game/stories/<tale_id>/script.json` with `tools/story/seed_script.py`; after seeding, `script.json` is the
  source of truth; hand-edited beats live in `tools/story/tales/<tale>.py` so a `--force` reseed reproduces them.
- After a tale-file edit, regenerate into a fresh temp with `--force` (`seed_script.py --out <file>` does NOT
  overwrite an existing file without `--force`: a stale temp silently survives and the "diff before copying" compares
  old with old), e.g. `--out <scratch>.json --no-audio`, **diff it against script.json and copy it only if the diff is your change**
  (`tools/story/wg_seed.sh` does temp → diff count → copy). The seeder re-reads the 톡톡 source, so upstream text /
  clip renames come along (2026-11-22: witch_candy lost 10 voice clips that way); otherwise patch script.json by hand.
- A tale-file edit that never reached script.json plays nothing (the sunmoon rope reorder sat unapplied through three
  test runs): a hand reorder in the tale .py only reaches the game after a reseed.
- Line `status` and LINE_META (pending lines play caption-only): script_schema.md.

## The engine is data
- The runner is data-driven; the stage started with sun_wind's cast hard-coded (sun/wind sky hangers, traveller, hat,
  coat, wind gusts). It is data now (three_pigs phase 2): `cast` kinds walker / hanger / actor / prop,
  `spread.spots/set/light/focus`, tale `shots`, `ui` (cover / end pictures, speaker chips) and a per-tale `handler`
  (TaleHandler, `game/stories/<tale_id>/fx.gd`) for fx. For a new tale move any new cast/props/fx to data (cast
  entries → CastPuppet / SkyHanger / prop cards by catalog id; fx in the tale's handler) and keep sun_wind working.
  Moving sun_wind's fx out verbatim and checking same-view captures (noise floor, identical hidden-card counts) + a
  full autoplay run kept it safe; verify sun_wind still autoplays start to end after any engine refactor.
- Tale top level `theme` (sunmoon 2026-11-22): a non-western tale dresses the template (MeadowWorld / CardLibrary):
  "korean" keeps nature cards from every sheet and takes man-made cards only from `korean_*`; default "" leaves other
  tales untouched. `ground_style`: paper by default (art.md, 2026-11-22).
- The story scene takes the script via `StoryRunner.script_path`; `game/stories/<tale_id>/story.tscn` points at the
  tale's script (the shelf / tale picker lists tales; `--tale=<id>` picks one from the command line).
- Card children: attach decoration (backing discs etc.) as a child of the card itself; siblings kept stale positions
  when a story started mid-way with `--beat`.
- `--beat=<id>` starts need `enter.at` on every beat (a `keep`-only beat leaves the cast at the anchor, popped down).
- Engine extensions so far: walk `to` may map each role to its own mark; go_inside `keep_open` (the intruder leaves the
  door standing open); `inside_margin`, `inside_only`, `overlap_ok`, `speaker_insert`, `pop_in`. After editing a shared
  engine script, load-check it (`tools/story/wg_check.gd`): one untyped `for a in vis` broke every tale's runner until
  fixed.
- The movie maker runs time-sliced builds per frame at 30 fps: the first page behind the cover took 21 s of story time
  at 3 ms/frame; it now builds at 10 ms/frame (the cover is a still page).

## Handlers (TaleHandler)
- Tale verbs: an unknown step goes to the handler's `run_step(st, runner)`; the handler uses the runner's _say /
  _wait / _wait_tap so captions, faces and SEG logs stay generic, and prints `PLAN <verb><n> <ids>` for check_lines.
- Handler fx names with ":" match on the part before it. Generic `pop:<card id>` / `fold:<card id>` on set pieces.
- `speaker_point` (window, group stand-in, symbolic speaker): camera.md.
- fx props register with the overlap check (`stage.register_prop`): sets.md.

## Lines in time
- Split a line across steps when its parts belong to different moments (`say`/`walk` take `segs`): narration while
  the wolf walks, his quote only once he stands at the door (user: "도착 전에 문 열라고 하네"). A quote plays within
  about 1.5 s of its speaker arriving, with the speaker on camera; a 9 s gap read as missing ("대사가 아예 사라진듯").
- After every full autoplay run `python3 tools/story/check_lines.py <tale> <log>` (gate.py runs it): every used line
  and segment exactly once, in order (a "missing line" report from a viewer can then be answered from the log, and a
  real gap is caught before the user hears it).

## Character states
A story state on a character (a black mouth) is a CastPuppet state every figure change maps through, checked by a
run-log counter that also counts the roles the story expects in that state (run log BLACK_LIPS
frames-with-wrong-variant=0; a check that only watches puppets already in the state reported 0 while the state was
never set).

## Branching tales (witch_candy)
- Pick the choice space so every combination has its own result and nothing needs explaining (three colour groups ×
  two picks = 6 colour sets = 6 results), every result's lines already recorded, and each result's look reused
  elsewhere (the finale's six transformations). Put branch tables (ingredients, combos, results) in the tale table;
  the seeder marks any nested line id used (`_ids_in`), and check_lines is branch-aware: it accepts exactly one
  result's lines per round.
- Branch coverage: force results with a tale arg (`--wc-results=a,b`) and run every result at least once.
- go_inside `pipeline: true` (with `climb_steps`): the next steps up while the one before is over the sill, no fixed
  queue wait, and an actor already nearer its queue place than the end of the path walks straight there (the host at
  her door); witch_candy's entry went from ~21 s to ~12 s.
- Pace: `python3 tools/story/silence_map.py <tale> <log>` lists every stretch > 3 s with no line playing, per beat;
  trim those (camera waits, slow walks / glides, long silent flights), never the lines.
