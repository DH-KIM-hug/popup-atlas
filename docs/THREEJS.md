# three.js player (web / app version of 팝업 동화)

Decision (user, 2026-11-25: "Three js가 괜찮아보임"): the web / app version plays the tales in three.js. Godot stays
the authoring tool and its gate stays the quality check; three.js does **not** re-implement the story engine. It plays
back an export of the real StoryRunner: the exporter runs the tale in Godot (autoplay, the gate's settings) and records
everything the screen shows, frame by frame; the browser rebuilds the scenes from that and replays them. Every tap
step is a live wait point.

Live: https://dh-kim-hug.github.io/popup-atlas/three/ (the Godot web build stays at the root).

## Architecture

```
game/ (Godot, unchanged)                tools/threejs/                         threejs/ (Vite app)
StoryRunner autoplay ── export_tale.gd ─► build/threejs_dump/<tale>/ ── pack_tale.py ─► public/data/tales/<tale>/
                        (SceneTree        scene.json  geo.bin  tex/                    index.json  c<i>.json  c<i>.bin.gz
                         script, reads    export.log (LINE / BEAT)                     public/data/shared/{res,tex,prints,audio,covers}
                         the live tree)                                  pack_shelf.py ─► public/data/tales.json
```

### Exporter (`tools/threejs/export_tale.gd`, run by `export.sh`)

A `SceneTree` script that instantiates `stories/<tale>/story.tscn` and lets the real runner play the whole tale with
`--autoplay` from the cover to the end card. It only reads the tree (one exception: it sets the runner instance's
`_movie = true`, what a movie-maker recording sets, so the next page is prebuilt in one go and the story timing matches
the gate recordings: turnip STORY_DONE 281.7 s vs 281.6 s in the gate log). Every 30 fps frame it writes what changed:

- **views**: `main` (the page on screen), `next` (the prebuilt page shown right of the fold during a live page turn),
  `book` (the cover / ending book, its own World3D). Per view: camera + DOF, lights, Environment, look rig + post_grade
  uniforms, as per-key diffs. `base` = which view is the screen (the book covers the page while it is shown).
- **geometry**: every visible GeometryInstance3D in a shown view: view, transform, mesh / material swaps, MultiMesh
  buffers, instance uniforms, Label3D text. Meshes and textures are written once; identical blobs share one range
  (content hash). Tangents are kept (Godot's normal-map frame).
- **animated material uniforms**, **audio** (starts / stops / volumes per player, 3D position, bus volumes; generated
  NameVoice clips saved as wav), **UI** (caption, page tab, end card, page turn progress + old page snapshot / live
  + new page view, flash cards, pointer ring, hold progress), **story** (beat, line, runner mode, press, tap targets
  with world point + radius, ripples = the autoplay taps, snapshots).

### Pack (`tools/threejs/pack_tale.py`, `pack_shelf.py`)

- One **chunk per beat** (`c<i>.json` + `c<i>.bin.gz`): each holds the textures / materials / meshes / nodes first
  needed in that beat and its frames, so the cover plays while the rest streams.
- **Shared across tales** (`data/shared/`): file textures by `res://` path (webp), runtime textures and card prints by
  content hash (each batched card print cropped out of its 4096² atlas page), sound by path (ogg -> mp3 128k: no
  Vorbis in Safari). A tale opened after another reuses what the browser already has.
- **Smaller geometry**: normals / tangents as int8; MultiMesh motion (pop-up waves, folds: every card of a batch moves
  each frame) kept as 10 fps keys and stored as deltas (only the cards that moved since the last key). sun_wind went
  from 69 MB to 10 MB of geometry this way.
- `index.json` carries the chunk list, Godot's LINE list from the same run, the voice clip -> line map, cover info.

### Player (`threejs/src`)

- `app.js` — the bookshelf (Godot shelf order from `game/app/tales.json`, each book = the BookModel board: cover art
  + cut-paper title at `title_rect`, cloth spine colour), tale open / back / replay, iOS audio unlock on the first tap
  (`navigator.audioSession.type = 'playback'`, AudioContext resume + a one-sample buffer inside the gesture).
- `player.js` — streams chunks, rebuilds nodes per view (three scenes: main / next / book), replays frames with the
  camera, node transforms and MultiMesh keys interpolated for 60 / 120 Hz, warms new meshes / textures on the GPU a
  few per frame before they appear, and handles waits:
  - **tap**: the timeline holds one frame before the recorded tap; the ring sits on the target (world point
    projected with the live camera); only a tap inside the ring goes on; after 9 s the last prompt replays;
  - **cover**: a tap anywhere opens the book;
  - **hold** (sun_wind blow): the story runs only while the finger is down.
  `?auto=1` resolves waits at once (the recording already holds autoplay's pause), `?beat=<id>` starts at a beat.
- `turn.js` — PageTurn (`game/story/page_turn.gd`) as one full-screen pass: old page (snapshot or live), back of the
  sheet with the print showing through, the new page (the `next` view rendered with its own grade), shadows.
- `materials.js` — ports of the paper shaders (paper_print / cast_print, paper_edge / cast_edge, house_body,
  ground_layer, card_batch + card_shadow, contact_shadow, drop_skirt, cover_book; table_wood, page_stack, stream,
  plank_deck, folded_rock flat), normal maps in Godot's tangent frame.
- `post.js` — Godot's post chain in one pass (depth fog, DOF, glow, exposure + AgX, adjustments, post_grade).
- `audio.js` — Web Audio replay of the recorded events (buses, 3D attenuation, loops without the mp3 padding).
- Look calibration against the Godot reference frames: AgX contrast 1.4, ambient x0.75, key x0.65 (`?agx= ?amb=
  ?key=`), binormal sign measured on turnip close-ups (puppet faces / coats).

## Run

```sh
# export one tale (windowed Godot, one process per project through the lock, frame cap, disk guard)
tools/story/with_godot.sh tools/threejs/export.sh turnip 340
python3 tools/threejs/pack_tale.py turnip         # -> threejs/public/data/tales/turnip + size report
python3 tools/threejs/pack_shelf.py                # -> tales.json + covers
cd threejs && npm install && npm run build         # dev: npm run dev; preview: npx vite preview --port 4199
tools/threejs/deploy.sh                            # gh-pages/three/ (one commit on top; the Godot build stays)
```

Data (`threejs/public/data/`) is generated and not committed.

## Check

```sh
node tools/threejs/check_tale.mjs <url> <tale> <outdir> webkit ipad   # whole tale in autoplay: end reached, lines,
                                                                       # audio meter, fps, GPU memory, bytes
node tools/threejs/verify_tap.mjs <url> <outdir> webkit                # real taps from the shelf: cover, rings
node tools/threejs/fps_probe.mjs "<url>?tale=X&beat=Y&auto=1" webkit 20
tools/threejs/compare_gate.sh artifacts/video/turnip_v6.mp4 "<url>?tale=turnip" out.jpg 3,12,22,...
```

The line check compares the voice clips the page actually started (with a decoded buffer) against the LINE list
the runner printed in the export run (a line split over steps counts once).

## Numbers (2026-11-25, local preview, Playwright WebKit, iPad landscape 1180x820 @2x, Mac M4 Pro)

Whole tale in autoplay (`check_tale.mjs`). Wire = what the page downloaded for that tale alone (a tale opened
after another downloads less: shared files are cached). First frame = the cover on screen after the page asked for
the tale. GPU memory is the player's estimate (textures + geometry + render targets + shadow maps).

| tale | story s | plays to end | lines (voice started, decoded, on time) | wire MB | first frame | fps median / p5 | GPU MB |
|---|---|---|---|---|---|---|---|
| turnip | 282 | yes | 51 / 51 | 29.4 | 0.19 s | 52.6 / 37.0 | 550 |
| sun_wind | 200 | yes | 35 / 35 | 33.0 | 0.18 s | 45.5 / 23.3 | 542 |
| three_pigs | 311 | yes | 37 / 37 | 35.9 | 0.24 s | 58.8 / 27.8 | 596 |
| witch_candy | 424 | yes | 63 / 63 | 38.3 | 0.18 s | 31.2 / 26.3 | 635 |
| sunmoon | 395 | yes | 57 / 57 | 38.9 | 0.18 s | 58.8 / 52.6 | 598 |
| wolf_goats | 348 | yes | 49 / 49 | 37.9 | 0.19 s | 58.8 / 52.6 | 673 |
| patjuk | 353 | yes | 48 / 48 | 40.2 | 0.18 s | 58.8 / 50.0 | 536 |
| rapunzel | 360 | yes | 47 / 47 | 36.2 | 0.19 s | 58.8 / 52.6 | 593 |

No playhead stalls (the next beat always finished loading in time) and no page errors in any run. Real taps
(`verify_tap.mjs`, WebKit): shelf tap -> cover wait -> tap opens; seed / sprout rings: a tap outside the ring is
ignored, a tap on it goes on; audio context running.

Known gaps:
- fps: witch_candy (31) lights up to 31 lantern omni lights at once (every paper fragment loops over all of them);
  sun_wind (45, p5 23) and three_pigs (p5 28) dip during page turns (two pages render) and big pop-up waves. Next:
  a fixed pool of ~8 point lights assigned per frame (Godot Mobile also caps omni lights per object), skip the
  `next` view's shadow pass during turns.
- Turnip compare sheet vs the gate video: `artifacts/threejs/turnip_v6_vs_threejs.jpg` (12 story times).
