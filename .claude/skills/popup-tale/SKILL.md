---
name: popup-tale
description: Make a new tale (or a big chunk of one) for the 팝업 동화 iPad pop-up storybook app in Godot (repo popup-atlas, game/). Covers script.json seeded from 톡톡 동화극장, beats and spreads on the shared world templates, reusing the shared card atlas and cast library, generating only missing art (Codex magenta pipeline), character expression sets and the front-facing paper-puppet walk, story verbs and taps, voice lines, recording beats with the Godot movie maker, and blind critic loops. Use it whenever the user asks to add or adapt a story/동화 in this app ("다른 동화도 만들자", "아기 돼지 삼형제 만들어줘", "새 동화 추가"), to add characters or scenes to a tale, or to judge/fix how a tale's characters move, emote or look — even if they don't say "skill".
---

# Pop-up tale production (팝업 동화)

This is how the first tale, 「해와 바람」 (sun_wind), was built, with every mistake that cost a round folded in, so the next tale goes right the first time. Read `docs/BRIEF.md` (contracts, style rules, asset-reuse policy) and the tail of `artifacts/game-progress.md` before starting; append a dated entry there after every round.

The user talks in Korean, wants to SEE results (send recordings and contact sheets with SendUserFile, not just numbers), and gives short, sharp feedback on motion ("뒤로 걷는데?", "팔자걸음", "휘청거려"). Treat each such remark as a bug report: reproduce it with an 8 fps zoomed frame tile first, find the cause, fix, re-record, show.

## What carries over and what is new (user decisions)

- From 톡톡 동화극장 (`~/projects/2026/patjuk-game`, READ-ONLY) only the **script** carries over, and even it is a draft to adapt to pop-up scenes. Characters, backgrounds and props are made new for the pop-up look; 톡톡 art is a design reference at most.
- **Reuse first**: shared card library `game/art/atlas/catalog.json` (419 cards, tags category/biome/season), shared cast `game/art/cast/catalog.json`, world template `scenes/world/meadow.tscn`. New generic art (a wolf, a pig, a straw house) goes into the shared libraries with tags so later tales reuse it; only truly tale-unique art goes in `game/stories/<tale_id>/art/`.
- The look is fixed (user chose the photographed-miniature look: low lens, shallow DOF, raking warm light, felt ground). Don't re-tune the template look per tale; dress it.

## Pipeline (one tale)

1. **Plan** (`references/planning.md`): list beats → spreads (which template, seed/view, route), the cast with every pose/expression each beat needs, props, the taps/holds per beat, and which lines change. Write `game/stories/<tale_id>/script.json` with `tools/story/seed_script.py` and edit it (schema: `references/script_schema.md`).
2. **Story engine generalisation** — the runner (`game/story/story_runner.gd`) is data-driven, but `spread_stage.gd` still hard-codes the sun_wind cast (sun/wind sky hangers, traveller, hat, coat, wind gusts). For a new tale, move cast/props/fx to data (cast entries in script.json → CastPuppet / SkyHanger / prop cards by catalog id; fx as small per-tale handler scripts in `game/stories/<tale_id>/`), keeping sun_wind working. Verify sun_wind still autoplays start to end after the refactor.
3. **Art** (`references/art_pipeline.md`): search the catalogs; generate only what's missing with the Codex pipeline; build full expression sets; cut walkers into the front-facing rig.
4. **Voice** (`references/voice.md`): reuse recordings for unchanged lines; changed/new lines need recording with the same voice ids — **ask the user before spending on ElevenLabs**, and mark status in script.json.
5. **Wire + verify**: autoplay every beat, record with the movie maker, look at frame tiles, fix. Full unattended run start → end with `--autoplay --quit-on-done`.
6. **Judge** (`references/critic_loop.md`): ≥3 lens-diverse blind critics; for motion, 8 fps zoom tiles reviewed by you before any critic.
7. **Deliver**: commit + push per milestone (on main unless told otherwise), send mp4s (< 30 MB, re-encode crf 26–30 if bigger) and a contact sheet, report honestly what still looks off.

Run long work through background agents/workflows with narrow ownership (one owner per file set, never two writers on the same Godot project files; use a git worktree for parallel look experiments). Brief every agent with the relevant lessons below — they don't know them.

## Lessons that cost rounds on sun_wind (apply up front)

**Characters and motion** (details: `references/walk_rig.md`)
- One smiling figure is not a character. Give every narrated emotion its own figure: calm walking face, surprised, cold/shivering, hot/sweating, relieved, sad/angry as the tale needs. Map line → expression in script.json; no beat may show a grin over "앗!" or "추워!".
- A card must face the way it travels, or it reads as moonwalking (sun_wind's first walk: a front-facing card moving away). Characters may walk in any direction — toward the camera, away, left, right — as long as the figure for that direction exists: front view (walking toward us), back view (walking away), side profile (left/right; flip the card for the other side). Pick the figure from the travel direction relative to the camera each frame (with a short turn when it changes). Plan which directions each walker needs and generate those views; front-only walkers are limited to walking toward the camera.
- Front-facing legs need front-view boots/feet (toes at the viewer). Side-view feet → 팔자걸음.
- Legs live behind the garment (per-figure depth deep enough for max leg tilt; cap tilt ~20° fwd/24° back); never shorten/slide a leg so its top shows; use pre-drawn half-bent and lifted leg cards; steps narrow (inside the coat width).
- Swinging arms (separate arm cards with a round shoulder cap) stop the "soldier march"; posed-arm expressions keep baked arms.
- Keep the body steady: weight-shift roll ≈ 0.6° (4° read as 휘청), small bob/bounce, tiny head lag. Narrow the step width when you reduce roll, or feet leave the coat.
- Characters keep doing things during weather/interaction beats (the traveller kept walking through wind and sun) — a story in motion, not a stage play of standing cards.
- Water: stand in the actual water channel, sink to the water line, hide legs below it, ripples on the water — never sink into the bank.

**Art**
- A shared style block leaks: "tiny flower and leaf motifs" printed leaves onto the sun and the wind. Use per-category style blocks (sky characters, animals, buildings) with explicit negatives.
- Codex image jobs: magenta #FF00FF background, md5-check every raw (another session's image once landed in our file), accept wide outputs (2172x724 was reported FAILED but was fine), keep old raws, contact-sheet and look before slicing.
- Card children: attach decoration (backing discs etc.) as a child of the card itself; siblings kept stale positions when a story started mid-way with `--beat`.
- Pose switches can flip hats/props on and off (hat flicker): check pose → figure mapping keeps worn props consistent.

**Look/quality loop**
- New prop types to "fix" engineering read as dropped-in 3D clutter; the look gap to the reference was lens/light/ground, not mechanisms.
- When vs-reference critics and vs-previous-version critics disagree, the user sided with vs-reference (photographed miniature). Show the user a comparison grid and let them pick.
- Single critics are noise (0.83 → 0.44 on re-judge). Use ≥3 lens-diverse critics and ask "impressed" per side.

**Tooling gotchas**
- Movie maker (`--write-movie`, windowed) records audio+video but crops the frame edges slightly on this Mac; check UI layout with `gd_run.capture_scene` instead.
- One Godot process per project at a time (import races mark files valid=false — delete the .import and reimport).
- A moving story camera can pass through cards: hide hinged AND static cards near the camera path (`_clear_sightlines`, `_clear_statics_here`).
- Never `rm $VAR/*` — use literal paths or `"${VAR:?}"`.

## Commands

```sh
G=/Applications/Godot.app/Contents/MacOS/Godot
$G --path game --resolution 1366x1024                                   # play
$G --path game --resolution 1366x1024 --fixed-fps 30 --write-movie /tmp/x.avi --quit-after 600 -- --beat=<id> --autoplay
$G --path game --resolution 1366x1024 --fixed-fps 30 --write-movie /tmp/full.avi -- --autoplay --quit-on-done
ffmpeg -i /tmp/x.avi -c:v libx264 -crf 26 -pix_fmt yuv420p -c:a aac out.mp4
ffmpeg -ss 6 -t 2 -i out.mp4 -vf "fps=8,crop=W:H:X:Y,tile=8x2" -frames:v 1 tile.jpg   # motion check
python3 -c 'import sys; sys.path.insert(0,"/Users/house_of_4k2b/.claude/skills/scenario-godot-expert/scripts"); import gd_run; print(gd_run.check_all("game"))'
```

The story scene takes the script via `StoryRunner.script_path`; make `game/stories/<tale_id>/story.tscn` point at the tale's script (and a tale picker later).
