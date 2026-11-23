# Web build (팝업 동화 in a browser)

Public link: **https://dh-kim-hug.github.io/popup-atlas/** (GitHub Pages, `gh-pages` branch). It opens on the
bookshelf; every tale is playable (`Entitlements.DEV_UNLOCK_ALL`).

## Make and publish

```sh
tools/web/export_web.sh          # copy game/ -> build/web_project, lossy textures, import + export -> build/web/
tools/web/deploy_pages.sh        # force-push build/web to the orphan gh-pages branch (one commit)
node tools/web/web_check.mjs https://dh-kim-hug.github.io/popup-atlas/ build/web_check ipad chromium 0.3,0.35
```

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
- **Shelf tap fix (all platforms):** the shelf's root Control now ignores the mouse, so a tap reaches
  `_unhandled_input` and opens the book (before, the root's default STOP filter swallowed it).
- **Code guarded by `OS.has_feature("web")`:** the 3D render scale (about 1024 px tall, like iPad) and the
  device-point scale of the 책장 / app buttons now also apply in a browser; `App` prints a `WEB_PERF` console line
  every 5 s (fps, video / texture memory) for the browser check. iOS and desktop runs are unchanged.

## Measured (2026-11-24, build from 9581b97 + these changes)

| | value |
| --- | --- |
| download (gzip as Pages serves it) | wasm 10 MB + pck 98 MB (raw: 39.5 + 104 MB, parts 90 + 10 MB) |
| boot to shelf (Mac, fast line) | 3.8 s local, 8.6 s from Pages (WebKit, iPad viewport) |
| GPU memory (Godot `RENDER_VIDEO_MEM_USED`) | shelf 195 MB at 1366x1024, 340 MB at iPad 2360x1640; tale 600-680 MB (was 900 at full size) |
| JS heap (Chrome) | 11-27 MB; the pck lives in the Emscripten file system on top (~100 MB) |
| fps (Mac Chrome / Playwright WebKit) | 60 / 50-60 after the first seconds of a tale |

Checked with `tools/web/web_check.mjs` on the Pages URL: desktop Chrome (1366x1024, sun_wind and three_pigs),
iPad viewport 1180x820 @2x with touch in Playwright WebKit (sun_wind) and Chrome (rapunzel): shelf loads, a tapped
book opens its tale, the first page plays, a tap advances. Not run on a physical iPad.

Loader note: `engine.preloadFile()` must get an ArrayBuffer, not a Uint8Array; a typed array is stringified as a
`fileSizes` key, which is "Out of memory" in Safari and a 700 MB heap spike in Chrome.
