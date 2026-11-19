# Sound wiring spec for the Godot agent (three_pigs first; sun_wind can adopt the same system)

Inputs (all staged, nothing is under `game/` yet):
- `artifacts/audio_staging/sfx/*.ogg` (81 files) and `music/*.ogg` (6) → copy to `game/audio/sfx/` and
  `game/audio/music/`.
- `tools/audio/sound_catalog.json` → copy to `game/audio/sound_catalog.json`. This is the shared, tale-agnostic
  catalog: sound ids, files, bus, gain, randomisation, beds, sprinkle sets, emitters, footsteps and buses.
- `tools/audio/three_pigs_sound_blocks.json` → the proposed `sound` blocks for three_pigs (tale level + per beat).
  Put them in the tale's seed tables (`tools/story/tales/three_pigs.py`) and have `tools/story/seed_script.py` copy
  `sound` into `script.json`. Don't hand-edit the generated script.json.
- Listen to `artifacts/audio_staging/preview_three_pigs.mp4` (and get the user's OK) before wiring. Cue times are in
  `SOUND_PLAN.md`.

Import: set `loop = true` in the `.import` of every catalog entry with `"loop": true`. That covers the `amb_*` beds
except `amb_gust_*`, plus `fire_crackle_m/l`, `kitchen_boil` and the music slots home, build, wolf and chimney.
Leave `loop_offset` at 0: each file is baked so that its end continues into its start. Ending and night play once.

## 1. Buses (`game/default_bus_layout.tres`)

| bus | send | effects | notes |
|---|---|---|---|
| Master | — | Limiter (ceiling -1.0 dB, threshold -2 dB) | |
| Voice | Master | none | `StoryRunner.player` (already named "Voice") → `bus = "Voice"`. Role lines and prompts all go here. |
| Music | Master | **Compressor, `sidechain = "Voice"`**: threshold -30 dB, ratio 2.0, attack 60 ms (`attack_us = 60000`), release 450 ms (`release_ms = 450`), gain 0, mix 1 | aim for about 6–7 dB of reduction under a line (the preview measured 5.8 dB). Tune the threshold against real playback: reduction ≈ (voice level − threshold) × (1 − 1/ratio). |
| Ambience | Master | **Compressor, `sidechain = "Voice"`**: threshold -30 dB, ratio 1.3, attack 80 ms, release 600 ms | about 3 dB of reduction under a line |
| SFX | Master | none | PaperAudio (hinge flaps) also moves here: `bus = "SFX"` on its pool players |

If the sidechain compressor pumps or is hard to tune, use the deterministic fallback. `_say()` knows exactly when a
segment plays, so it can call `SoundDirector.duck(true/false)`, which tweens the Music bus to -7 dB and the
Ambience bus to -3 dB (attack 60 ms, release 450 ms). The preview mix used this envelope.

Levels are pre-normalised:
- music files: -22 LUFS;
- beds: about -30 LUFS per layer, about -28 summed;
- one-shots: peaks at -4 dBFS.
The catalog `gain_db` is the playback offset on the sound's bus. Keep all bus volumes at 0 dB except for the user
volume.

## 2. SoundDirector (shared: `game/core/audio/sound_director.gd`, one per story scene)

Loads the catalog and owns the players. API:
```
play(id, at: Variant = null, gain_db := 0.0, delay := 0.0) -> void   # one-shot; at = Vector3 (3D) or null (2D)
loop_start(id, key, fade := 0.5, gain_db := 0.0); loop_stop(key, fade := 0.8)
set_bed(name, fade := 2.5)        # catalog.beds; null = silence; "@light" resolves via tale_sound.light_beds
set_music(slot, fade_in := 1.5, fade_out := 2.0)  # crossfade between two players; same slot = no restart
gust(amount: float)               # 0..1: one amb.gust + breeze swell (see §5)
footstep(actor, surface)          # called by StoryActor (see §4)
setup_spread(stage)               # builds the emitters (stream, trees) for the current spread
```
One-shot players come from a pool: 12 × AudioStreamPlayer3D on SFX/Ambience plus 6 × AudioStreamPlayer for 2D.
- Pick the file from `files`, never the same index twice in a row when `no_repeat` is set.
- `pitch_scale = 1 ± pitch_rand`, `volume_db = gain_db ± vol_rand_db/2`.
- Positional sounds use the same convention as PaperAudio: `ATTENUATION_INVERSE_DISTANCE`, unit_size ≈ 1.0 page
  unit, panning_strength 0.5, doppler off.
- Footsteps cull beyond 4 units, with at most 6 at once.

## 3. Triggers → sounds

Sources: `script.json` steps, the tale handler's fx names (`stories/three_pigs/fx.gd`), and the engine events.
Resolution order for an fx name:
1. the beat's `sound.fx[name]`;
2. `tale_sound.fx[name]`;
3. nothing.

A value can be:
- a sound id;
- `{sound, delay, gain_db}`;
- `{loop, key, fade}`, `{bed}` or `{music}`;
- a list of any of these;
- `{by_tap: [...]}`, which picks entry `build_ctx.tap - 1`.

Call it from `SpreadStage.fx(name)` before the handler runs, so the handler stays sound-free.

| engine event / step | hook point | sound |
|---|---|---|
| cover tap → book opens | `_step_cover` when the cover turns | `paper.page_turn` |
| page turn | `ui.page_turn.turn()` (story_runner ~l.1005) | `paper.page_turn` (alternate the 2 takes) |
| beat start | `_play_beat(b)` | `set_music(b.sound.music)`, `set_bed(b.sound.bed or tale light_beds[spread.light])`, `setup_spread` once per spread |
| light change (`_set_light`) | spread_stage ~l.716 | `set_bed(light_beds[name], 2.5)`, so the bed fades with the light |
| `tap_each` react `pop:story_build_props_*` | fx | `ui.pop` |
| `build` tap | `stage.fx(st.fx)` per tap | straw_pop → `build.straw`; hammer_bang → `build.hammer` ×2; brick_thunk → `build.brick` ×2 |
| `star_burst` | fx | `build.done` |
| `flute_notes` / `violin_notes` | fx | `music.flute` / `music.violin` (duck the Music bus a further -10 dB for 3.5 s: catalog `duck_music_db`) |
| `brothers_tease` | fx | flute -6 dB + violin -7 dB snippets |
| wolf stops at the straw house (`end_pose: sniff`) | `StoryActor` reaching its mark with end_pose sniff | `wolf.sniff` (at the wolf) |
| `huff` tap i | `stage.fx(st.fx)` | straw_fly / wood_wobble / brick_huff `by_tap` → `wolf.huff_1/2/3` (+ `house.wood_wobble` / `house.brick_hold`) and `gust(i/taps)` |
| huff result | `stage.fx("pop:" + ruin)` | `pop:story_houses_02` → `house.straw_blow`; `pop:story_houses_05` → `house.wood_collapse` |
| `counter` shown | `stage.show_counter(i)` | `ui.count` with `pitch_scale = 2^(step/12)`, steps 0, 2, 4, 5, 7, 9, 11, 12 |
| `thud_dust` | fx | `wolf.flop` |
| `go_inside` | `_step_go_inside`: door opens / shuts once | `door.open` at the door, `door.shut` after the last one is in |
| `ladder_up` | fx | `prop.ladder_raise` |
| `climb` | `_step_climb` path: the ladder segment (vertical) / roof segments | `foot.ladder_rung` per rung bob; `foot.roof_tile` per contact frame on the roof |
| `inside_view` / `outside_view` | fx | `set_bed("room")` / `set_bed("@light")`, stop the fire and boil loops |
| `flame_m` / `flame_l` / `boil` | fx | `fire.ignite` + `fire.crackle_m` (and `set_music("chimney", 0.4)`), then `fire.ignite` + `fire.crackle_l` (same key "fire", crossfaded), then `kitchen.boil` loop |
| `wolf_drop` / `splash` | fx | `wolf.chimney_slide` / `kitchen.splash` |
| `wolf_launch` | fx | `wolf.launch`; `wolf.yelp_far` at +1.8 s, positional on the wolf so it fades as he runs off |
| `pigs_cheer` | fx, **ending beat only** | `build.done` -3 dB, min gap 3 s |
| `end` with close_book | `_step_end` → `stage.fold()` | `paper.book_close`; the ending music runs on under the end card and `set_music(null, 2.0)` on "다시 보기" |

Note: `fx.gd` fires `pigs_cheer` for every `pop:story_houses_0*`, and that prefix also matches the straw and wood
ruins (02 and 05), so the pigs hop when their own house is blown away. That's why the cheer sound is mapped only in
the ending. Consider narrowing the prefix in fx.gd.

## 4. Footsteps (one per contact frame)

- `CastPuppet._cycle_step()` already advances drawn cycles by ground distance. When `f != _cyc_i` and the new frame
  is in the contact list for (skin, cycle), emit `foot_contact(frame)`. `StoryActor` forwards it as
  `SoundDirector.footstep(self, surface)`.
- Contact frames: `catalog.footsteps.contact_frames`.
  - Checked from the sheets: wolf walk [0, 2]; wolf back / front [0, 1]; pig run [0].
  - Default for any 4-frame cycle is [0, 2] and for 2-frame cycles [0, 1]. Check the pig walk and
    carry_straw cycles.
- Unrigged hop moves (wolf_tiptoe and the other static cards) emit a contact on each landing of the paper hop.
- Surface at the foot, using the GroundLayers queries:
  - `bridge` if on a bridge set piece's footprint, or on the road where `stream_distance(p) < 0.05`;
  - else `road` if `path_distance(p) < 0`;
  - else `grass`.
  - While `climb` runs: `ladder` on the ladder segment, `roof` on the slope.
- Sound id `foot.<pig|wolf>.<surface>`, `foot.ladder_rung` or `foot.roof_tile`. The skin → kind map is in
  `tale_sound.footsteps`; mom is null.
- Positional at the feet; +2 dB when the walk pose is a run.
- With several walkers, each emits its own steps, at -2 dB each (the preview staggered three piglets).

## 5. Living world: beds, sprinkles, emitters, gusts

Requested by the user ("새소리 물소리 풀잎소리") and the priority of this pass. All data is in the catalog.

**Beds** (`catalog.beds`):
- Each bed is 1–3 looping layers on Ambience, each started at a random point in its file.
- `set_bed` crossfades the layer sets over 2.5 s; a layer the new bed shares keeps playing and only re-gains.
- Mapping from the spread's `light`, in `tale_sound.light_beds`: "" or day → `day`; afternoon; late; dusk; night;
  evening. The inside cutaway uses `room`.

**Random sprinkle scheduler** (`catalog.sprinkle_sets`; it runs while the bed names a set):
```
next = now + rand(interval) * 0.5
on tick: if now >= next:
    pool = [it for it in set.items if now - last[it.id] >= it.min_gap]   # item = [id, weight, min_gap?]
    it = weighted_choice(pool)
    pos = random point in set.where:  trees -> a random tree set piece (top third of its card) on this spread;
                                      water -> a random stream point;  any -> random page point near the camera focus
    gain = rand(set.gain_db) + sound.gain_db - (6 if voice is speaking else 0)
    play(it.id, pos, gain, pitch ±set.pitch_rand)
    last[it.id] = now;  next = now + rand(set.interval)
```
Seed it from the run (or randi) so it never repeats. In `--fixed-step` captures, seed it from the beat id so takes
are reproducible.

**Stream emitter** (`catalog.emitters.stream`):
- Expose the stream centre line from GroundLayers (`stream_line_3d()`, like `path_centre_3d()`: `_stream_line` is
  already resampled every 0.08).
- Each frame, slide one looping AudioStreamPlayer3D (`amb.stream`, mono) to the point on that polyline nearest the
  listener. The listener is the camera's focus point on the page, not the camera position: closer framing means
  louder water.
- Attenuation: inverse-square, unit_size 0.9, max_distance 4.0.
- Smooth the position with a short lerp so the emitter can't jump across bends.
- Mute it on the `room` bed.

**Tree emitters** (`emitters.trees`):
- 2–4 looping `amb.breeze` players at the largest tree / forest set-piece clusters on the spread, at -6 dB.
- Their gain follows the local gust value (+6 dB at the gust peak).

**Gusts:**
- `gust(amount)` plays `amb.gust` at `-8 + 8 * amount` dB, positioned between the listener and the nearest trees.
  It also lifts the breeze layer +6 × amount dB for 1.5 s.
- Ambient gusts: on beds with `gusts`, call `gust(rand)` at random intervals within `gusts.every`. Also call it when
  the WindSway envelope at the listener crosses 0.85 upward. That envelope is the same formula `WindSway` uses for
  the cards: `g = 0.5 + 0.5 * sin((t * gust_speed - dot(p, wind_dir)) * 0.9); g = g * g`. Read `_t`, `gust_speed`
  and `wind_dir` from the meadow's `sway` node, so the swell is heard when the cards visibly rock.
- Huffs call `gust(tap / taps)`. On the brick house (`tap_soft`) scale it by 0.6.

## 6. Data format: the `sound` block

Tale level (`script.json` top level, `"sound"`), as in `three_pigs_sound_blocks.json`:
```json
"sound": {
  "catalog": "res://audio/sound_catalog.json",
  "light_beds": {"": "day", "afternoon": "afternoon", "late": "late", "dusk": "dusk", "night": "night", "evening": "evening"},
  "fx": {"hammer_bang": ["build.hammer", {"sound": "build.hammer", "delay": 0.28, "gain_db": -2}],
         "straw_fly": {"by_tap": ["wolf.huff_1", "wolf.huff_2", "wolf.huff_3"], "gust": "tap"}, "...": "..."},
  "steps": {"page_turn": "paper.page_turn", "go_inside": {"door_open": "door.open", "door_shut": "door.shut"}, "...": "..."},
  "footsteps": {"pig_a": "pig", "wolf": "wolf", "mom": null}
}
```
Per beat (`beats[i].sound`):
```json
"sound": {"music": "wolf", "bed": "@light", "emitters": ["stream", "trees"], "fx": {"pigs_cheer": {"sound": "build.done", "gain_db": -3}}}
```
Any step may also carry `"sfx": "<id>" | {...}` for a one-off sound that no fx covers. That is how a new tale adds a
sound without code.

Rules:
- Sound ids are shared: `foot.*`, `amb.*`, `spk.*`, `door.*`, `paper.*`, `ui.*` and `fire.*` are generic.
  Tale-specific ones (`wolf.*`, `house.*`, `build.*`) still live in the one catalog, so another tale can reuse a
  hammer or a door.
- A missing id logs `SOUND_MISSING <id>`. Add a `missing_sound=[]` line next to `missing_audio=[]` in the
  `STORY_DONE` summary.
- Log `SFX <t> <id> <file>` per play when `--log-sound` is set, so runs can be checked against the cue sheet.

## 7. sun_wind adoption (later)

- sun_wind's meadow has the same stream and bridge, the same GroundLayers and the same WindSway. It needs no new
  files to start:
  - beds `day` (and `late` near the end);
  - the stream and trees emitters;
  - `paper.page_turn` / `paper.book_close`;
  - pig footsteps for the traveller (`foot.pig.*` until it has its own takes).
- The wind beats should drive `gust()` from the wind's blow taps, the same way the huffs do. The sun beat can drop
  to the `afternoon` bed for warmth.
- Its own music can reuse `home` / `ending`, or new slots added to `catalog.music`.

## 8. Acceptance

1. three_pigs full run: `STORY_DONE … missing_audio=[] missing_sound=[]`, with no `SOUND_MISSING`.
2. Capture a run with sound and compare it against `preview_three_pigs.mp4`:
   - music changes at the same story points;
   - ducking audible under every line;
   - beds change with the light;
   - steps on every contact frame.
3. Measure the capture: Master true peak ≤ -1 dBFS, the music stem about 6 dB lower under lines than in gaps, SFX
   peaks ≤ -9 dBFS.
4. Perf: ≤ 24 concurrent players. The sprinkle scheduler and emitters cost nothing measurable; check the frame p95
   on the village spread again.
5. The user listens and approves. Nobody has heard these files yet.
