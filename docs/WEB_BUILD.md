# Web build (팝업 동화 in a browser)

Public link: **https://dh-kim-hug.github.io/popup-atlas/** (GitHub Pages, `gh-pages` branch). It opens on the
bookshelf; every tale is playable (`Entitlements.DEV_UNLOCK_ALL`).

## Make and publish

```sh
tools/web/export_web.sh          # copy game/ -> build/web_project, lossy textures, import + export -> build/web/
tools/web/deploy_pages.sh        # force-push build/web to the orphan gh-pages branch (one commit), keeping three/
node tools/web/web_check.mjs https://dh-kim-hug.github.io/popup-atlas/ build/web_check ipad chromium 0.3,0.35
```

The export publishes what is **committed**: game/ files with uncommitted edits (another agent's tale in progress) go
back to their HEAD version in the copy (it prints `export uses HEAD: ...`); `WEB_DIRTY=1` keeps the working tree.
So commit a change before exporting it. `deploy_pages.sh` copies `three/` (the three.js pilot,
`tools/threejs_pilot/deploy_three.sh`) from the current gh-pages into the new commit, so
https://dh-kim-hug.github.io/popup-atlas/three/ survives a deploy.

Test jump: `index.html?tale=turnip&beat=seed&autoplay=1&mute=1` (also `logsound=1`) starts a beat directly with the
same user args as a desktop story run; without a query the shelf opens.

Local / fallback hosting: `tools/web/serve.sh` starts `tools/web/serve.py` (port 8765) and a Cloudflare quick
tunnel (`cloudflared`), prints a `https://*.trycloudflare.com` URL and writes the PIDs to `build/web/serve_pids.txt`;
`tools/web/serve.sh stop` stops exactly those PIDs. That URL only works while this Mac is awake.

## How the build differs from iOS

- **Preset "Web"** in `game/export_presets.cfg`: no threads (GitHub Pages cannot send COOP/COEP headers), no
  GDExtension. The iOS preset is unchanged.
- **Lighter textures, web only.** All ~3,200 textures import lossless and full size for iOS (pck ~405 MB, a tale
  holds ~850 MB of RGBA textures). Godot web keeps the whole pck in browser memory and an iPad Safari tab dies
  somewhere past 1-1.5 GB, so `export_web.sh` exports from a throwaway copy (`build/web_project/`, gitignored)
  where `tools/web/web_imports.py` sets lossy WebP (`WEB_Q`, 0.82) and `size_limit` = longest side x `WEB_SCALE`
  (0.75). The real project is never re-imported.
- **Split pck.** Pages refuses files over 100 MB, so `tools/web/split_pck.py` cuts `index.pck` into 90 MB parts
  (`index.pck.0`, `.1`, ...) and patches `index.html` to fetch them into one buffer and start the engine with it.
- **Renderer.** The project uses Mobile; the web runs Compatibility (WebGL 2). Camera depth of field
  (`CameraAttributesPractical`) does not exist there, so the blur that remains is the screen-space tilt-shift
  pass (`post_grade.gdshader`), and near-camera silhouettes the DOF used to soften can show hard edges.
- **Pixel data vs smaller textures (houses).** bodies.json house outlines and stages.json facade bands are in source
  px, but the web textures are 0.75x. `web_imports.py` writes `res://web_src_sizes.json` (source w/h of every
  downscaled texture) and `PaperCard.src_px_scale(tex)` (web only, 1.0 elsewhere) scales `HouseBody.for_card`'s traced
  outline and `SetPiece`'s band used rect back to source px. Before (2026-11-24 build) house bodies came out 1/0.75
  too big and banded facades were misplaced ("집이 완전 잘못되어 있다").
- **Sound.** Godot 4.7.2's web "Sample" playback mis-orders buses added at runtime (`AudioServer.add_bus()` ->
  `godot_audio_sample_bus_add(-1)` splices the bus one slot early), so the sends `SoundDirector._setup_buses` sets
  wire Master into a loop and nothing is heard. `export_web.sh` writes a `default_bus_layout.tres` (Voice, Music,
  Ambience, SFX -> Master) into the copy, so the buses exist from the start and `add_bus()` is never called. The
  loader also sets `navigator.audioSession.type = 'playback'` and plays a silent `<audio>` on the first touch, so an
  iPad's silent switch does not mute the book. Check: `node tools/web/web_audio_check.mjs <url> [chromium|webkit]
  [desktop|ipad]` taps a book and meters the Web Audio output (exit 1 when silent).
- **Look on the web** (`LookRig.web_look()`: `OS.has_feature("web")`, or `--web-look` on a desktop run with
  `--rendering-method gl_compatibility` for tuning). Compatibility draws shadow acne as ribs on the flat paper ground
  ("골덴", corduroy: its depth bias works in other units) and lifts the tone curve (web ~ native^0.62, washed out). Web
  only: key light `shadow_bias` 2.0 (native 0.08: 0.08 ribbed, 1.0 halved it, 2.0 clean with contact shadows kept),
  post_grade `pre_gamma` 1.7, post contrast x0.86, post saturation x1.10 (`WEB_*` constants in look_rig.gd).
  `tools/web/look_variants.sh` captures one still per variant (Mobile vs desktop Compatibility) in one slot hold;
  desktop Compatibility shows the same lift and ribs as the browser, so tune there, then confirm on the web.
- **Shelf tap fix (all platforms):** the shelf's root Control now ignores the mouse, so a tap reaches
  `_unhandled_input` and opens the book (before, the root's default STOP filter swallowed it).
- **Code guarded by `OS.has_feature("web")`:** the 3D render scale (about 1024 px tall, like iPad) and the
  device-point scale of the 책장 / app buttons now also apply in a browser; `App` prints a `WEB_PERF` console line
  every 5 s (fps, video / texture memory) for the browser check. iOS and desktop runs are unchanged.

## Fidelity check (web vs native)

```sh
tools/web/fidelity_native.sh artifacts/web_fidelity/native                 # Mobile renderer, movie maker, 1366x1024
node tools/web/web_fidelity.mjs http://localhost:8766/ artifacts/web_fidelity/web_after chromium desktop
python3 tools/web/fidelity_sheet.py artifacts/web_fidelity/sheet.jpg native=artifacts/web_fidelity/native \
  web_before=artifacts/web_fidelity/web_before web_after=artifacts/web_fidelity/web_after
```

Moments are in `tools/web/fidelity_moments.json` (26 frames over all 8 tales, t = seconds after the beat's first
spoken line). The sheet prints mean luma / contrast / saturation over the 3D area (buttons and caption masked).
2026-11-25 (build 46cf0fa7..64dbeaab): native 0.471 / 0.178 / 0.585; web before 0.579 / 0.190 / 0.491; web after
0.466 / 0.186 / 0.581. House bodies and facades now match native, and the ground ribs are gone. What is left: the
browser has no camera DOF, so far backgrounds read crisper than on iOS (the tilt-shift pass is the only blur), and
the very darkest scenes sit a little darker (rapunzel home 0.33 vs 0.36 luma).

## Measured (2026-11-25, build 64dbeaab)

| | value |
| --- | --- |
| download (gzip as Pages serves it) | wasm 10.1 MB + pck 88 MB (raw: 39.5 + 95 MB, parts 94.4 + 0.6 MB) |
| boot to shelf (Mac, fast line) | 4.2 s from Pages (Chrome, 1366x1024); a tale's first line ~8-12 s after opening by URL |
| GPU memory (Godot `RENDER_VIDEO_MEM_USED`) | shelf ~200 MB at 1366x1024; tale ~630 MB at iPad 2360x1640 (sun_wind) |
| JS heap (Chrome) | 12-19 MB; the pck lives in the Emscripten file system on top (~95 MB) |
| fps (Mac Chrome / Playwright WebKit) | 60 / 50-60 after the first seconds of a tale |
| sound (`web_audio_check.mjs`, Pages + local) | Chrome desktop and WebKit iPad: context running, 35-39 sources after the tap, 6 voice-length buffers, output peak RMS ~0.39, ~20 s of audible output in 25 s |

Checked with `tools/web/web_check.mjs` on the Pages URL: desktop Chrome (1366x1024, sun_wind and three_pigs),
iPad viewport 1180x820 @2x with touch in Playwright WebKit (sun_wind) and Chrome (rapunzel): shelf loads, a tapped
book opens its tale, the first page plays, a tap advances. Not run on a physical iPad.

Loader note: `engine.preloadFile()` must get an ArrayBuffer, not a Uint8Array; a typed array is stringified as a
`fileSizes` key, which is "Out of memory" in Safari and a 700 MB heap spike in Chrome.
