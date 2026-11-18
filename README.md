# 팝업 동화 (Pop-up Storybook)

An iPad storybook app in a pop-up-book style. Each scene folds up out of the page, and the characters walk through a papercraft diorama. Stories: 「해와 바람」 (The North Wind and the Sun) and 「아기 돼지 삼형제」 (The Three Little Pigs).

- Engine: **Godot 4.7.2** (standard build), Mobile renderer (Metal), Jolt physics
- Godot project: `game/` (the main scene is `res://stories/sun_wind/story.tscn`)
- Design brief, contracts and checklist: `docs/BRIEF.md`
- Work log (append-only): `artifacts/game-progress.md`
- The repo root (`src/`, `public/`, Vite) holds the older web prototype. It is kept for reference only.

## Run

```sh
# Editor
/Applications/Godot.app/Contents/MacOS/Godot --path game -e

# Play the story (iPad 4:3 landscape window)
/Applications/Godot.app/Contents/MacOS/Godot --path game --resolution 1366x1024
```

Controls:
- **Tap:** sun, wind or traveller.
- **Hold:** the wind, to blow.
- **Tap the sun:** to shine.
- **Tap anywhere:** to skip the current line.
- **Captions:** the button at the top right turns them on or off.

Story options (user args after `--`):

| arg | effect |
|---|---|
| `--tale=<id>` | play `game/stories/<id>/script.json` (`sun_wind` default, `three_pigs`); or open `res://stories/three_pigs/story.tscn` |
| `--beat=<id>` | start at a beat: sun_wind `sky`, `bet`, `wind_turn`, `sun_turn`, `moral`, `stream`, `ending`; three_pigs `home`, `straw_build`, `wood_build`, `brick_build`, `wolf_straw`, `wolf_wood`, `brick_wolf`, `chimney`, `ending` |
| `--autoplay` | play the whole story unattended (taps and holds are simulated) |
| `--quit-on-done` | quit when autoplay reaches the end |

```sh
# Record a beat to video (Godot movie maker, needs a window)
/Applications/Godot.app/Contents/MacOS/Godot --path game --resolution 1366x1024 --fixed-fps 30 \
  --write-movie /tmp/out.avi -- --beat=wind_turn --autoplay --quit-on-done
ffmpeg -i /tmp/out.avi -c:v libx264 -crf 24 -pix_fmt yuv420p -c:a aac out.mp4
```

Benches:
- `scenes/world/meadow.tscn`: world template
- `scenes/look/`
- `scenes/motion/`
- `scenes/chars/`
- `art/cast/bench/`

## Layout

| path | what |
|---|---|
| `game/core/paper_card.gd` | `PaperCard`: an image's alpha outline extruded into cut cardstock (print, plain back, cream core edge) |
| `game/core/pop_hinge.gd`, `pop_wave.gd`, `cross_card.gd` | hinge motion (pop up and fold down) and staggered pop waves |
| `game/core/world/` | `meadow.gd` world template (seeded, reusable across stories) |
| `game/core/look/` | light, grade, depth of field, ground layers |
| `game/art/atlas/` | **shared card library** (419 cards, `catalog.json`: category, biome, season and tags) |
| `game/art/cast/` | **shared cast library** (traveller with expressions and walk rig, sun, wind, props) |
| `game/stories/sun_wind/script.json` | the story's script: beats, steps, lines, voice ids, recording status |
| `game/story/` | story runner, spread stage (cast / set pieces / light from the script), story actors, set pieces, UI, page turn |
| `game/stories/<tale>/fx.gd` | the tale's own effects (TaleHandler) |
| `game/audio/voice/sun_wind/` | narration clips |
| `tools/` | asset pipelines (`atlas/`, `cast/`, `art/`), look metrics and blind A/B (`look/`), story tools (`story/`) |

## Adding a story

See `.claude/skills/popup-tale/` (pipeline, lessons, `references/script_schema.md` for every field and verb).

1. Create `game/stories/<tale_id>/script.json` and `story.tscn` (StoryRunner with `script_path`). Use `tools/story/seed_script.py` to seed it from a 톡톡 동화극장 voice script.
2. Dress a world template (`meadow`) using card ids from `game/art/atlas/catalog.json`.
3. Take characters from `game/art/cast/catalog.json`.
4. Make new art only when nothing in the catalog fits. Shared art goes into the library; art unique to the story goes into `game/stories/<tale_id>/art/`.

## Quality loop

- `python3 tools/look/look_metrics.py IMG`: look metrics, with the target ranges in `docs/BRIEF.md`.
- `tools/look/make_ab.py` / `make_h2h.py` build blind A/B sheets (our scene against the reference, or two of our versions against each other). The answer keys go to `artifacts/ab_keys/`, which critics must never read. `tools/look/score_ab.py` scores the picks.
