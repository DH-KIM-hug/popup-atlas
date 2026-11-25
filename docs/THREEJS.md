# three.js player (web / app version of 팝업 동화)

Decision (user, 2026-11-25: "Three js가 괜찮아보임"): the web / app version plays the tales in three.js. Godot stays
the authoring tool and its gate stays the quality check; three.js does not re-implement the story engine. It plays
back an export of the real StoryRunner: the exporter runs the tale in Godot (autoplay) and records everything the
renderer sees, frame by frame; the browser rebuilds the scene from that and replays it. Taps are live: the
timeline waits at every tap step until the child taps the target.

## Stage 1: the pilot (one beat, 2026-11-25)

The turnip "seed" beat (봄, 19 s, one tap on the seed).

- `tools/threejs_pilot/export_scene.gd`: a `SceneTree` script. It instantiates the tale's story scene, lets the real
  runner play (autoplay), and every frame writes what changed:
  - geometry nodes: transform, mesh / material swaps, visibility, MultiMesh buffers, instance uniforms;
  - animated material uniforms, lights, Environment, the look rig and its post_grade uniforms, camera and DOF;
  - audio starts / stops / volume changes per player (path, bus, 3D position), bus volumes;
  - the caption text, the beat id, the tap targets (world point + radius) while the runner waits.
  Meshes go once into `geo.bin` (float32 / uint32, triangles re-wound counter-clockwise). Runtime-built textures
  (card atlas pages, ground maps) are saved as webp; file textures are listed by `res://` path.
- `tools/threejs_pilot/pack_assets.py`: turns the dump into the web data folder (geo gzipped, file textures to
  webp, each batched card print cropped out of its 4096² atlas page, ogg -> mp3 for Safari).
- `pilot/threejs/` (Vite): `src/main.js` rebuilds the nodes and replays the frames (30 fps recording, transforms
  and camera interpolated for 60 / 120 Hz), `src/materials.js` ports the paper shaders (paper_print, paper_edge,
  house_body, ground_layer, card_batch + card_shadow, contact_shadow, drop_skirt; the rest flat) as patched
  `MeshStandardMaterial`s so they keep three.js lights and PCF shadows, `src/post.js` is Godot's post chain in one
  pass (depth fog, DOF, glow, exposure + AgX, adjustments, post_grade tilt-shift / split tone / vignette / grain),
  `src/audio.js` replays the audio events in Web Audio (unlocked by the first tap).
- Look calibration against native: AgX contrast 1.4, ambient x0.75 (`?agx=`, `?amb=` to tune). DOF / tilt-shift
  blur samples mips of the colour target (5 taps), cheaper and a little softer than Godot's.

### Run

```sh
# export (windowed: runtime textures need a renderer); Godot flags before `--`, always a frame cap
tools/story/with_godot.sh /Applications/Godot.app/Contents/MacOS/Godot --path game --resolution 1366x1024 \
  --fixed-fps 30 --quit-after 2400 --script res://../tools/threejs_pilot/export_scene.gd -- \
  --tale=turnip --beat=seed --autoplay --pilot-out=/ABS/dump --pilot-until=grow
python3 tools/threejs_pilot/pack_assets.py /ABS/dump pilot/threejs/public/data/turnip_seed
cd pilot/threejs && npm install && npm run build      # dev: npm run dev (127.0.0.1:5199)
tools/threejs_pilot/deploy_three.sh                     # gh-pages/three/, the Godot web build at the root stays
```

### Measure

```sh
node tools/threejs_pilot/measure.mjs <url> <outdir> webkit ipad    # load, bytes, fps, GPU memory estimate
node tools/threejs_pilot/verify_tap.mjs <url> <outdir> webkit      # real taps: start card, the seed ring
python3 tools/threejs_pilot/compare.py out.jpg "label|godot.jpg|three.png" ...
```

### Pilot numbers (WebKit via Playwright, iPad viewport 1180x820 @2x, GitHub Pages)

| | |
|---|---|
| on the wire | 21.7 MB (geo 7.6 MB gz, textures 10 MB, scene.json 2.9 MB, audio 2 MB) |
| ready | 1.6 s |
| fps | 58.8 median, 55.6 p5 |
| GPU memory (estimate) | ~425 MB (textures 228 MB) |
| draw calls / triangles | 678 / 4.1 M |

Data (`public/data/`) is generated, not committed: re-run the export + pack to rebuild it.
