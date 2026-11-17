# Pop-up Atlas — progress (append-only log at the bottom)

## Intent
Browser 3D walking toy in Three.js. A tiny paper traveller walks across an endless open pop-up book. Tiles ahead
fold up out of the page on springs (overshoot, settle with a wobble); tiles behind fold back flat. Wave function
collapse keeps neighbours connected. Look target: real pop-up books / papercraft dioramas photographed tilt-shift.
Controls WASD or click to walk, smooth follow camera. No physical-looking UI, no external brand assets.
Deliver: Vite build + run instructions, 30 s gameplay capture, final side-by-sides and scores.

## Contracts (lead owns)
- World units: 1 tile = 1.0 square, page surface y = 0, +X east, +Z south (toward camera), north = -Z.
- Kit: `public/models/kit.glb`, one root node per tile type `tile_<type>` at the origin in canonical orientation.
  - `print`: flat printed square (1x1, y = 0.002) always visible, the tile's flat "page art".
  - `pop_*`: pop-up pieces. Node origin lies on its hinge line at y = 0, local X axis = hinge axis, rest pose = standing.
    glTF extras: `fold` = +1 or -1 (which way it lies flat), `order` 0..1 (stagger: 0 rises first).
  - Pieces may nest (a pop child of a pop) for two-stage folds.
  - Traveller: root `traveller`, origin at feet, faces -Z, children `body`, `head`, `pack`, `leg_l`, `leg_r` (leg origins at hip).
- Tile types and edge sockets (N,E,S,W; G grass, R river, P path), canonical orientation; engine rotates by 90° steps:
  grass GGGG · hill GGGG · trees GGGG · house GGGG (door south) · path_straight PGPG · path_corner PPGG ·
  path_tee PPPG · path_end PGGG · river_straight RGRG · river_corner RRGG · river_end RGGG (pond) · bridge RPRP.
- Audio: `src/systems/PaperAudio.ts` exports `class PaperAudio { unlock(); flap(opts:{pitch:number,gain:number,pan:number,up:boolean}); step(foot:0|1, speed01:number); dispose() }`.

## Assumptions (logged, not asked)
- "Endless book": one infinite page plane that follows the player, page texture world-aligned, with a book gutter
  crease every 14 tiles along X so it reads as successive spreads.
- Tilt-shift DOF is a screen-space depth-and-height blur pass (cheap, 60 fps) rather than BokehPass.
- Rise radius ~5.5 tiles ahead/around, fold-back beyond ~7 tiles behind; hysteresis avoids flicker.
- Fold spring: critically under-damped (zeta ~0.32), ~2.2 Hz, small random per-piece variation; second-order wobble.
- Traveller walk is procedural (waddle, leg flaps, bob) — paper toys have no knees.
- Real pop-up book photos are used only locally as critique reference (not shipped).

## Log
- 2026-11-18 scaffold created (create_threejs_game.py), git init. Concept frames c1–c5 queued via Codex imagegen.
- 2026-11-18 USER supplied reference sheet "Step 1: references" (6 frames) → `art_src/reference/step1_sheet.jpg`,
  split to `r1_book_overview … r6_flat_map.png`. These now take precedence over the earlier c1–c5 frames as the critic target
  (user's explicit input overrides). Observed targets, used by the component checklist:
  - Scene framing: open hardback on dark walnut table, lantern glow + bokeh in a corner, cream page-stack edges visible,
    warm graded light (screen-avg colour ≈ #9b6f3c–#ab7f4f under AgX), strong tilt-shift (top/bottom ~25% blurred).
  - Page: faint printed tile grid (r4, r6) — the WFC grid is meant to show; tiles are flat printed squares when folded.
  - Rising (r2): tiles stand up as A-frame / V-fold tents and box-steps; hinge creases + white folds visible.
  - Palette (limited, matte): sage green, olive, mustard/ochre, terracotta/brick, teal-blue water, cream paper; deckled white edges.
  - Kit: round layered-canopy trees (green/ochre/terracotta) on flat brown trunks, cream houses + terracotta roofs + glowing
    windows, arched bridges (cream or terracotta) with rails, cut-paper river with cream wave strips, lantern posts,
    cattails, grey paper rocks, layered hill silhouettes along the back.
  - Traveller (r3, r6): small, brown hair, bedroll rucksack, red/orange scarf, walking stick, boots; reads at ~6% frame height.
- 2026-11-18 USER direction change: this repo becomes a NEW iPad pop-up storybook app. Engine **Godot 4.7.2** (user
  chose after comparison with Swift/web), project `game/`, Mobile renderer. First story 「해와 바람」 (user's pick over
  팥죽할멈). Reuse only voice script + character designs from 톡톡 동화극장; all else new. Quality bar: user's screen
  recording (frames in `art_src/reference/video/`). Brief, contracts, component checklist: `docs/BRIEF.md`.
- 2026-11-18 lead: `PaperCard` (alpha contour → extruded card, print/back/edge materials, cached) + `PopHinge`
  (under-damped spring, page bounce, twist wobble) + look bench `scenes/test_diorama`. Fixed: contour triangulation
  fallback (Delaunay + inside test). look_v3 metrics vs reference logged in BRIEF (too bright, shallow shadows,
  low saturation, low density). Web prototype superseded.
