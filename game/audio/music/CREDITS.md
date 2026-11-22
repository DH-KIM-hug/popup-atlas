# Music credits — 「아기 돼지 삼형제」 (three_pigs)

Downloaded 2026-11-19. Each download went into its own new, empty directory
(`artifacts/audio_staging/downloads/<slot>/`) and was only read through ffmpeg. Processing for every track:
decoded to 48 kHz stereo, loop-pointed or trimmed (details per row), normalised to -22 LUFS integrated
(peak ceiling -3 dBFS), and encoded as Vorbis q6 (`tools/audio/process_music.py`).

All six are **CC0**, so no attribution is required. They are recorded here anyway, and a short line in the in-app
credits is a courtesy. No NonCommercial or ShareAlike material is used. The licences were checked on each item's
own page by the research pass on 2026-11-19. **Nobody has listened to these tracks.** The instrument and mood notes
are the pages' own words.

| file | slot | title (cut) | author | licence | source page | file URL |
|---|---|---|---|---|---|---|
| `music_home_1.ogg` | home / opening | Happy Lullaby (song17). Loop = 0–38.40 s (16 bars × 2.4 s); the ring-out (38.40–39.52 s) is mixed back over the head. | cynicmusic | CC0 | https://opengameart.org/content/happy-lullaby-song17 | https://opengameart.org/sites/default/files/song17.mp3 |
| `music_build_1.ogg` | building | Full of Energy. Whole file used as the loop (34.76 s, read as 20 bars × 1.74 s), with a 20 ms crossfade at the seam. | code_box | CC0 (Freesound "Creative Commons 0") | https://freesound.org/people/code_box/sounds/520192/ | https://cdn.freesound.org/previews/520/520192_10962806-hq.mp3 |
| `music_wolf_1.ogg` | wolf tension | Playful Music. Loop = 0–31.36 s (16 bars × 1.96 s); the ring-out (31.36–35.72 s) is mixed back over the head. | dominictreis | CC0 (Freesound "Creative Commons 0") | https://freesound.org/people/dominictreis/sounds/381531/ | https://cdn.freesound.org/previews/381/381531_5058825-hq.mp3 |
| `music_chimney_1.ogg` | chimney climax | Rabbit Bop. Whole file used as the loop (38.38 s = 16 bars × 2.4 s), with a 20 ms crossfade at the seam. | code_box | CC0 (Freesound "Creative Commons 0") | https://freesound.org/people/code_box/sounds/575759/ | https://cdn.freesound.org/previews/575/575759_10962806-hq.mp3 |
| `music_ending_1.ogg` | warm ending | Snow Globe (shorter original). Plays once: 0–69.76 s, 3 s fade-out. | Bobjt | CC0 | https://opengameart.org/content/snow-globe | https://opengameart.org/sites/default/files/snow_globe_shorter_original.ogg |
| `music_night_1.ogg` | night (optional) | Twinkle. Plays once: leading 0.79 s of silence trimmed, 61.9 s, 3 s fade-out. | Bigvegie | CC0 (Freesound "Creative Commons 0") | https://freesound.org/people/Bigvegie/sounds/554160/ | https://cdn.freesound.org/previews/554/554160_11740799-hq.mp3 |

Each page's own description (quoted, not checked by ear):
- **Happy Lullaby**: "Beautiful bells and arpeggios"; tags lullaby, happy, calm, relaxing, bells; "Easy for perfect loop".
- **Full of Energy**: tags glockenspiel, orchestra, pizzicato, plucked, strings, tuba, upbeat, vibraphone; the
  author calls it a loop.
- **Playful Music**: "playful/sneaky music"; tags Bassoon, Vibraphone, Playful, Sneaky.
- **Rabbit Bop**: "bunnies… need to be very quick, when they spot the fox!"; tags cartoon, double-bass, marimba,
  energetic, hopping, loop.
- **Snow Globe**: "Could also make decent intro or ending music"; tags Classical, arpeggios, ending, Wonderous.
- **Twinkle**: "Simple piano lullaby style chord sequence".

Notes:
- The four Freesound tracks are Freesound's public **HQ preview mp3s** (about 128 kbps). The original WAVs need a
  free Freesound login. code_box notes that Rabbit Bop's preview is degraded by the compression, so fetch the WAV
  before shipping if it sounds rough.
- Loop points come from tempo estimates (spectral-flux autocorrelation), not from listening:
  - Full of Energy ends in about 0.8 s of near-silence before its loop seam. This looks like a rest written into
    the loop, but it may sound like a gap.
  - In Happy Lullaby the last bar is quiet (a held chord) before the downbeat returns.
  Both need a listen.
- Rejected for licence by the research pass: GregorQuendel's pizzicato and music-box pieces (NC); AudioCoffee /
  DenKyschuk kids loops (NC); tyops "Orchestral Cartoon Suspense" (CC BY, a good wolf fit if credit is acceptable);
  "Comedy Funny Background Song" (CC-BY / BY-SA only). freepd.com is closed, and Pixabay returned 403 to automated
  fetches, so no Pixabay track was used.

## Sound effects and ambience (not music)

The files in `../sfx/` were generated with the ElevenLabs Sound Effects API (`eleven_text_to_sound_v2`) under the
user's ElevenLabs account. Each prompt is listed in `../sfx/manifest.json`. Check the account plan's commercial-use
terms before release. None are third-party recordings.

## Story-start music (2026-11-22, user: reuse 톡톡 동화극장's 시작 음악)

Copied from 톡톡 동화극장 (`sounds/sfx/intro_*.mp3`, credits in that project's `sounds/CREDITS.md`), renormalised to
-22 LUFS. All Pixabay Content License (no attribution required). Played once when the cover opens.

| file | source in 톡톡 | Pixabay title | author | tale |
|---|---|---|---|---|
| `intro_cozy_1.mp3` | `sfx/intro_cozy.mp3` (orig. 3–15 s) | Tender Lullaby (Acoustic Guitar Solo) | Musinova | sun_wind (as in 톡톡) |
| `intro_playful_1.mp3` | `sfx/intro_playful.mp3` (0–12 s) | Funny Ukulele | AtlasAudio | three_pigs (as in 톡톡) |
| `intro_night_1.mp3` | `sfx/intro_night.mp3` (3–15 s) | Music Box Sleep Lullaby | Tunetank | sunmoon (as in 톡톡) |
| `intro_magic_1.mp3` | `sfx/intro_magic.mp3` (0–12 s) | Magical Storytime | geoffharvey | witch_candy (톡톡 had none; chosen here) |

## turnip (커다란 순무, 2026-11-23, copied from 톡톡 동화극장 `sounds/`, credits in that project's `sounds/CREDITS.md`)

Music loudness-matched to -22 LUFS; sound effects copied unchanged into `../sfx/tn_*.mp3` (catalog ids `tn.*`, merged by
`tools/audio/turnip_sounds.py`). Pixabay Content License (no attribution required) unless noted; the `el_*` sounds and
the turnip music were generated for 톡톡 with the user's ElevenLabs account.

| file | source in 톡톡 | origin |
|---|---|---|
| `intro_cozy2_1.mp3` | `sfx/intro_cozy2.mp3` (톡톡's turnip intro, already 3–15 s of the original) | Pixabay "Light from the Hallway (Mbira Lullaby)", KonstantinPazuzuStudio |
| `music_turnip_1.mp3` | `music/el_turnip_bgm.mp3` | Eleven Music (톡톡): Russian village folk, balalaika / accordion / domra / tambourine |
| `finale_happy_1.mp3` | `sfx/finale_happy.mp3` | Pixabay "Happy Kids", HitsLab |
| `../sfx/tn_pop.mp3` | `sfx/el_turnip_pop.mp3` | ElevenLabs SFX (톡톡) |
| `../sfx/tn_strain.mp3` | `sfx/el_pull_strain.mp3` | ElevenLabs SFX (톡톡) |
| `../sfx/tn_sun.mp3` | `sfx/el_sun_warm.mp3` | ElevenLabs SFX (톡톡) |
| `../sfx/tn_squeak.mp3` | `sfx/mouse_squeak_1.mp3` | Pixabay "Mouse Squeak", TanwerAman |
| `../sfx/tn_bark.mp3` | `animals/dog_3.mp3` | Pixabay "Friendly Small dog bark (1)", Yodguard |
| `../sfx/tn_meow.mp3` | `animals/cat_2.mp3` | Pixabay "Cat Meow", SOUND_GARAGE |
| `../sfx/tn_water.mp3` | `sfx/water_pour_1.mp3` | Pixabay "Pouring Water", Universfield |
| `../sfx/tn_dig.mp3` | `sfx/dig_soil_1.mp3` | Pixabay "Digging with shovel", freesound_community |
| `../sfx/tn_rustle.mp3` | `sfx/rustle_1.mp3` | Pixabay "Bush Rustle", freesound_community |
| `../sfx/tn_grow.mp3` | `sfx/chime_up.mp3` | Pixabay "Fairy Dust Shimmer 1", floraphonic |
| `../sfx/tn_slurp.mp3` | `sfx/slurp_1.mp3` | Pixabay "Cartoon Slurp", freesound_community |
| `../sfx/tn_cheer.mp3` | `sfx/cheer.mp3` | Pixabay "Applause, small audience", freesound_community |
