# 「아기 돼지 삼형제」 — sound plan (2026-11-19)

Status: **staged, not heard.** Every file here was checked by measurement only (loudness, peaks, clipping, silence,
loop seams). Nobody has listened to any of them, so the user has to listen to `preview_three_pigs.mp4` before
anything is wired.

Files: `sfx/` (81 files, 48 kHz Vorbis), `music/` (6 tracks + `CREDITS.md`), `sfx/manifest.json` and
`sfx/MANIFEST.md` (prompt, duration, loop, loudness for each file), `verify.json` (technical check),
`preview_three_pigs.mp4` (cues laid over `three_pigs_full_v15.mp4`), and the catalog
`tools/audio/sound_catalog.json`. Wiring is in `WIRING.md`.

## Direction

- **The world is alive, not one loop.** Each place gets a bed of 2–3 looping layers (breeze in the grass and
  leaves, a bird or cricket layer, room tone), plus **sprinkles**: one-shot birds, cuckoo, dove, bee, frogs and owl
  dropped at random gaps and places. The stream is a **positional emitter** that swells as the camera nears the
  water or the bridge. Leaf gusts follow the visible wind sway and swell with each 후~.
  (User, 2026-11-19: "새소리 물소리 풀잎소리 이런게 나야 되는 건 아닌지".)
- **Time of day carries the story.** The ambience follows the spread's `light`:
  - day → afternoon → late: fewer, lazier birds;
  - dusk: crickets and frogs, no birds;
  - night: soft crickets and a far owl;
  - inside: the fire room;
  - evening: crickets and a last blackbird.
- **Papercraft-cozy, never scary.**
  - The wolf is comic: a sneaky bassoon / vibraphone theme, sniffs, cartoon whooshes and a slide whistle, and a
    yelp that fades away.
  - Collapses are toy-sized clatters.
  - The brick house holds with a dull, soft thud.
- **SFX on screen, music under the voice.** Every visible action makes a small sound. Repeated actions (steps,
  knocks, thunks, rungs, tiles) pick from 3–4 variations with pitch and volume jitter and never repeat the same
  take twice in a row.
- **Instruments are diegetic.** 첫째's recorder phrase and 둘째's violin phrase play on the SFX bus, and the music
  dips 10 dB under them.

## Mix levels (targets → measured in the preview)

| layer | target | how | preview measurement |
|---|---|---|---|
| Voice (narration, roles) | -16 LUFS clips, peaks -1.5 dBFS (existing polish) | unchanged | capture track -13.8 LUFS, -1.0 dBFS TP (capture, not the clips) |
| Music | -22 LUFS in gaps, ducked about 6–7 dB under voice | files at -22 LUFS; Music bus sidechain from Voice | about -24 dB RMS in gaps, -30 under lines (duck 5.8 dB); stem -25.1 LUFS integrated |
| Ambience | about -28 LUFS, ducked 3 dB under voice | beds at -29 to -31 LUFS per layer, layers summed | stem -29.7 LUFS integrated |
| SFX | peaks well under the voice (≤ -9 dBFS) | files peak at -4 dBFS; catalog gain -6 to -16 dB | stem true peak -8.8 dBFS, 99.9th-percentile 10 ms peak -11.2 dBFS |
| Master | no clipping | limiter at -1 dBFS | mix true peak -0.9 dBFS, 0 clipped samples |

## Ambience beds and the living world

| bed (catalog `beds.*`) | used for (spread `light`) | layers (loop files) | sprinkles (one-shots, random) | positional / reactive |
|---|---|---|---|---|
| `day` | home, straw_build (no light) | `amb_breeze_grass_1` + `amb_birds_day_1` | every 3–8 s: robin, finch, blackbird (common); cuckoo (min gap 45 s), dove (30 s), bee passing near flowers (20 s) | stream emitter; leaf gusts every 9–20 s |
| `afternoon` | wood_build, wolf_straw | breeze + `amb_birds_afternoon_1` (sparse birds, far insects) | every 6–13 s, fewer birds; dove, cuckoo, bee | stream; gusts every 10–22 s |
| `late` | brick_build, wolf_wood | breeze -1 dB + afternoon birds -4 dB | every 9–18 s: blackbird, dove, a rare cuckoo | stream; gusts every 12–25 s |
| `dusk` | brick_wolf | breeze -4 dB + `amb_dusk_crickets_1` (crickets, far frogs) | every 6–14 s: frog croaks near the water; **no birds** | stream; gusts every 15–30 s, softer |
| `night` | chimney (outside), launch | `amb_night_1` + dusk -12 dB | every 14–30 s: distant owl (min gap 25 s), an odd frog | stream (low); gusts every 18–35 s, faint |
| `room` | chimney (inside view) | `amb_fireplace_room_1` (small fire + room tone) | none | outdoor emitters muted; fire layers add on taps |
| `evening` | ending (lit windows) | breeze -6 dB + dusk crickets -3 dB | every 10–20 s: frog, a last blackbird (40 s) | stream (rises with the pull-back over the water) |

- Beds crossfade over 2.5 s when the light changes. Every layer starts at a random point in its loop. Sprinkles
  pick a random point in their zone (birds in the trees, frogs at the water), so the stereo or 3D position, the
  timing and the take differ every run and nothing sounds like a 30-second loop.
- **Stream** (`amb_stream_1`, mono): one 3D emitter slides along the stream's centre line to the point nearest the
  listener, so it swells as the camera passes the water and the bridge (0 dB within about 0.9 units, about -30 dB
  at 4 units). In the preview this is a gain curve read off the frames: loudest at the straw lot, the wolf's walk
  along the bank, both bridge crossings, and the closing pull-back.
- **Leaves and grass:** the breeze layer's gain follows the same travelling gust value that `WindSway` uses to rock
  the cards, so a visible gust is also heard. `amb_gust_1/2` one-shots fire at random gust peaks. Each 후~ fires a
  gust whose size follows the tap (1/3, 2/3, 3/3), so the trees answer the wolf.

## Music

| slot | file | mood | use | loop |
|---|---|---|---|---|
| home | `music_home_1.ogg` (Happy Lullaby, cynicmusic, CC0) | bells and arpeggios, lullaby | cover → home → village establishing | 38.40 s loop (16 bars) |
| build | `music_build_1.ogg` (Full of Energy, code_box, CC0) | pizzicato, glockenspiel, vibraphone, tuba | the three builds | 34.76 s loop (20 bars). There is a rest before the seam; listen to it |
| wolf | `music_wolf_1.ogg` (Playful Music, dominictreis, CC0) | "playful/sneaky", bassoon and vibraphone | from the wolf's entrance through the three huffs and the sneaky climb | 31.36 s loop (16 bars) |
| chimney | `music_chimney_1.ogg` (Rabbit Bop, code_box, CC0) | quick cartoon marimba and double bass | first fire tap → boil → drop → splash → launch → run-away | 38.38 s loop (16 bars) |
| ending | `music_ending_1.ogg` (Snow Globe, Bobjt, CC0) | gentle classical arpeggios, "ending" | ending beat → end card | plays once, 69.8 s, fades out |
| night | `music_night_1.ogg` (Twinkle, Bigvegie, CC0) | piano lullaby chords | optional alternative for the night climb or the end card | plays once, 61.9 s |

Music changes crossfade (1.5–2.5 s fade in, 2–3 s fade out); the chimney cue comes in fast (0.4 s) on the first fire
tap. The ending track keeps playing under the end card and fades out when "다시 보기" is pressed.

## Cue sheet per beat

Times are the preview's (seconds in `three_pigs_full_v15.mp4`); the game triggers by step/fx (see WIRING.md).

### 0 cover (0–3.4)
- Music `home` fades in (0.3).
- Book opened by tap → `paper.page_turn` (3.3).

### 1 home — 엄마의 배웅 (3.4–33) · bed `day`
- Crane down into the cottage garden: breeze, birds, sprinkles (robin, finch, a far cuckoo).
- tap_each piglet → `ui.pop` (toy pop with a xylophone note) as its material card pops up (≈20.6 / 22.0 / 23.4).
- The three walk away up the road: `foot.pig.road` for each piglet, staggered, receding (−14 dB by the end).
- The page turns to the village → `paper.page_turn` (31.2).

### 2 straw_build (35–59) · bed `day`, stream close
- Establishing crane over the village; music changes to `build`. The stream swells here: the straw lot is on the
  bank.
- 첫째 carries the straw → `foot.pig.grass` per step (carry cycle).
- Each tap → `build.straw` (rustle, 2 takes alternating) as a band folds up (46.3 / 47.8 / 49.3).
- House done → `build.done` (sparkle chime) with the star burst (52.3).
- `music.flute` (recorder phrase, music −10 dB) on `flute_notes` (52.9), then tp_020.

### 3 wood_build (59–81) · bed `afternoon`
- The camera moves to the forest edge; birds thin out.
- Each tap → `build.hammer` ×2 (bang-bang, the second −2 dB) with the camera bump (69.3 / 71.0 / 72.3).
- `build.done` (73.5); `music.violin` (violin phrase, music −10 dB) on `violin_notes` (73.9).

### 4 brick_build (81–105) · bed `late`
- Each tap → `build.brick` ×2 (set + settle) (88.8 / 90.3 / 97.3).
- `brothers_tease` → the two walk up (`foot.pig.grass` ×2); flute and violin snippets at −6 dB (92.0 / 92.4)
  under tp_023.
- `brothers_leave` → their footsteps recede.
- `build.done` with the low-angle push-in (98.5).

### 5 wolf_straw (105–144) · bed `afternoon`
- The music changes to `wolf` at his entrance (104.6).
- Wolf prowl → `foot.wolf.grass` (slow, 0.52 s cadence); he stops → `wolf.sniff` (킁킁, 110.6).
- Huffs: tap 1/2/3 → `wolf.huff_1` / `_2` / `_3`, each with a synced leaf gust (−8 / −4 / 0 dB).
- 3rd tap → `house.straw_blow` (straw scattering whoosh, 131.3) as the ruin pops.
- 첫째 runs along the road → `foot.pig.road` (fast, +2 dB) → `foot.pig.bridge` on the planks (138.3–140.1) → road.
- `go_inside` → `door.open` (141.8) … `door.shut` after he is in (143.4).

### 6 wolf_wood (144–178) · bed `late`
- The wolf walks the road → `foot.wolf.road` → `foot.wolf.bridge` (147.3–150.3) → road. The stream is loud at the
  bridge.
- Huffs 1/2/3 with gusts; `house.wood_wobble` after huff 1 (−4 dB) and huff 2 (161.5–164.5); 3rd →
  `house.wood_collapse` (toy plank clatter, 165.0).
- Both pigs run → `foot.pig.road` ×2 (169.8–175.8); `door.open` (176.0), `door.shut` (178.0).

### 7 brick_wolf (178–206) · bed `dusk` (crickets come in, birds stop)
- Wolf on the road → `foot.wolf.road`.
- Huffs 1/2/3 + `house.brick_hold` (dull thud ≈0.4 s after each; the house only shivers). The gusts are smaller
  here.
- Optional `ui.count` tick per huff if the counter shows, with the pitch rising per count.
- He sits → `wolf.flop` (comic thump and dust, 203.2).

### 8 chimney (206–262) · bed `night` → `room` → `night`
- To the ladder → `foot.wolf.grass`; `ladder_up` → `prop.ladder_raise` (209.5).
- Climb → `foot.ladder_rung` per rung (210.6–213.8); along the roof → `foot.roof_tile` tiptoes (0.75 s cadence,
  214–226.5). The `wolf` music keeps going: he's sneaking.
- `inside_view` → crossfade to the `room` bed (fireplace crackle, room tone); the outdoor emitters mute.
- Fire taps:
  - 1 → `fire.ignite` + the `fire.crackle_m` layer (238.5); the music changes to `chimney` (236.6).
  - 2 → `fire.ignite` + `fire.crackle_l` (240.0).
  - 3 (`boil`) → the `kitchen.boil` loop (241.5).
- `wolf_drop` → `wolf.chimney_slide` (scramble and descending slide whistle, 242.6).
- `splash` → `kitchen.splash` (big comic splash and steam hiss, 249.0); "앗, 뜨거워!" follows.
- `outside_view` → back to `night`; fire and boil fade out (0.8 s).
- `wolf_launch` → `wolf.launch` (rising slide whistle and whoosh, 254.2); the run-away → `wolf.yelp_far` fading
  away (256.0) + `foot.wolf.grass` fast and receding to −16 dB.

### 9 ending (262–283) · bed `evening`
- Music `ending` (crossfade in); lit windows, crickets.
- `pigs_cheer` → `build.done` at −3 dB (263.3).
- The pull-back over the stream: the stream rises.
- `close_book` → `paper.book_close` (273.1).
- The end card; the ending track continues and fades out at "다시 보기".

## SFX coverage (requested → file)

| requested | file(s) |
|---|---|
| footsteps on grass / road / bridge (pig trotters) | `foot_pig_grass_1-4`, `foot_pig_road_1-4`, `foot_pig_bridge_1-3` |
| footsteps on grass / road / bridge (wolf paws) | `foot_wolf_grass_1-4`, `foot_wolf_road_1-4`, `foot_wolf_bridge_1-3` |
| door creak open / shut | `door_creak_open_1`, `door_shut_1` |
| straw rustle stacking | `build_straw_rustle_1-2` |
| hammer knocks | `build_hammer_knock_1-3` |
| brick thunks | `build_brick_thunk_1-3` |
| flute (첫째) / violin (둘째) | `music_flute_phrase_1` (recorder), `music_violin_phrase_1` |
| wolf sniffing | `wolf_sniff_1` |
| huff ×3 intensities | `wolf_huff_small_1`, `wolf_huff_medium_1`, `wolf_huff_large_1` |
| straw house blown apart | `house_straw_blow_apart_1` |
| wood house creak / wobble, collapse | `house_wood_wobble_1`, `house_wood_collapse_1` |
| brick house holding | `house_brick_hold_thud_1` |
| wolf's exhausted flop | `wolf_flop_1` |
| ladder raise, rung climbs | `prop_ladder_raise_1`, `foot_ladder_rung_1-3` |
| roof-tile steps | `foot_roof_tile_1-3` |
| chimney scramble / slide | `wolf_chimney_slide_1` |
| fire crackle small / medium / large | `amb_fireplace_room_1` (small, the room bed), `fire_crackle_m_1`, `fire_crackle_l_1` (loops), `fire_ignite_1` (flare per tap) |
| boiling bubbles | `kitchen_boil_1` (loop) |
| big splash + hiss | `kitchen_splash_hiss_1` |
| wolf launching out of the chimney | `wolf_launch_whoosh_1` |
| distant yelp fading | `wolf_yelp_far_1` |
| book closing, page turns | `paper_book_close_1`, `paper_page_turn_1-2` (the existing synthesized `audio/paper/` flaps stay for hinges) |
| extras | `music_build_done_chime_1` (star burst), `ui_pop_toy_1` (material pop), `ui_count_tick_1` (counter) |
| living world | beds `amb_breeze_grass`, `amb_birds_day`, `amb_birds_afternoon`, `amb_dusk_crickets`, `amb_night`, `amb_fireplace_room`, `amb_stream`; gusts `amb_gust_1-2`; sprinkles `spk_bird_robin`, `spk_bird_finch`, `spk_bird_blackbird`, `spk_cuckoo`, `spk_dove`, `spk_bee`, `spk_frog`, `spk_owl` |

## Technical check (verify.json, `tools/audio/verify_audio.py`)

- 87 files (81 sfx + 6 music): **0 clipped samples, 0 silent files, 0 loop seams over the click threshold.**
  - The seam test compares the end→start jump and the slope change against the clip's own 95th-percentile
    sample-to-sample motion; under 1.0 means no click.
  - The worst seam is `music_wolf_1` at jump 0.86. Every other loop is ≤ 0.47.
- Bed loops that failed the first seam test were rebuilt as equal-power crossfade loops:
  - 1.5 s crossfade: `amb_birds_day`, `amb_night`, `amb_stream`;
  - 0.6 s crossfade: `fire_crackle_m`, `fire_crackle_l`.
  `amb_fireplace_room`, `amb_stream` and both fire layers were also brought to level with a loop-safe limiter
  (three copies in a row, the middle one kept).
- 200 ms level jumps across seams (the music, and the crackle layers whose pops are sparse) are listed in
  verify.json:
  - `music_build` −77 dB: the written rest before the seam;
  - `music_home` −15 dB: the held last bar.
  These are musical, not clicks, but they need listening.
- Raw API takes with full-scale samples, turned down but with the flattened tops still there:
  - many: boil (796 samples), splash (559), wood collapse (308), wolf_launch (237), yelp (240), huff_3 (216),
    hammer take (193);
  - a few: frog, sniff, chimney slide, fire_l, violin, count tick.
  If any of these sounds crunchy, regenerate it.
- Loudness of clips under 0.45 s is an RMS estimate. Footsteps sit at -22 to -33 LUFS with peaks at -4 dBFS
  because they are transient; catalog gains put them at -12 to -16 dB on the SFX bus.

## Generation log

- ElevenLabs Sound Effects: **58 generations** (57 planned + 1 retry: `foot_pig_grass`, whose first take peaked at
  -41 dBFS with one usable step). The cap was 70. Ledger: `el_ledger.json`. Prompts: `sfx/manifest.json` /
  `sfx/MANIFEST.md`, jobs `tools/audio/three_pigs_sfx_jobs.json`.
- Footsteps, knocks, thunks, rungs and tiles were generated as one take of several separate hits each, then cut at
  the onsets into single hits (3–4 variations per surface from 1 generation).
- Output format: `pcm_48000` (16-bit stereo, 48 kHz). Encoding: oggenc q6 (`brew install vorbis-tools`; the local
  ffmpeg has no libvorbis).

## Still open

- **Listen.** Nothing is approved by ear. Watch for:
  - footsteps that sound like noise or feel too long (they are cut at a -50 dB tail);
  - whether the flute is a recorder and the violin is cheerful;
  - the music loop seams (`build` rest, `home` held bar);
  - the wolf music's character ("sneaky", not scary).
- The pig grass steps are soft and rustly. If they read as mush, regenerate them as single-step takes (budget left:
  12).
- The Freesound tracks are 128 kbps previews; fetch the original WAVs with a Freesound login before release.
- The preview times are approximate (from frames). The game triggers by event, so they only matter for the preview.
