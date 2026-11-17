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
- 2026-11-18 USER: "새 애셋을 많이 새로 만들어야" + reference `art_src/reference/step4_atlas_and_cards.jpg` (≈200-sprite
  generated atlas → printed onto hinged cards; crossed-card trees; book page visible; dim warm light). Asset target raised to
  ≥200 cards; new component A0 (atlas generation + auto-slicing) launched alongside the running loop. Component A should
  build on A0's library from its next round instead of generating one card per image.
- 2026-11-18 USER: reuse assets across stories wherever possible. BRIEF now defines a shared library (game/art/atlas +
  tagged catalog, queried by id/tags) vs story-only art (game/stories/<tale_id>/art), and reusable biome scene templates.
- 2026-11-18 USER: effectively only the script carries over from 톡톡, and it may change per situation. BRIEF updated:
  characters made new (톡톡 art = reference/placeholder; generic characters → shared cast library game/art/cast/),
  per-tale editable script at game/stories/<tale_id>/script.json seeded from 톡톡; unchanged lines reuse recordings,
  changed lines get re-recorded with the same voice IDs.
- 2026-11-18 C_motion r1 (pop-up motion + sound). Story stays 「해와 바람」 (user re-confirmed over 팥죽할멈 this round).
  Changed: `core/pop_hinge.gd` retuned (rise spring f=1.88 Hz/weight^0.32, zeta 0.54 scaled 0.94–1.1 by weight, twist kick
  at vertical; fall = toppling inverted pendulum + air drag + page bounce e=0.32; new signals `landed`, `snapped`; static
  `fixed_dt`, `step()`, `angle()`, `openness()`). New `core/cross_card.gd` (slotted pair, B yaws about slot with lagging spring),
  `core/pop_wave.gd` (distance/back-row/weight-lag + jitter waves, fold outside-in), `core/audio/paper_audio.gd` (token bucket
  14/s + min gap, crowd swell, pitch by weight, distance gain, pan 0.3), `audio/gen_paper_sfx.py` → 6 flap_up / 4 fold_down / 3 pat wavs,
  bench `scenes/motion/motion_bench.*` (150 cards, 75 % fold forward so the print is revealed as pieces rise), curve/audio jobs.
  Measured: overshoot 12.5/11.5/9.3 deg (w 0.5/1/2.2); settle ±1 deg 0.56/0.70/0.65 s, ±0.5 deg 0.60/0.75/0.97 s; fold first
  touch 0.40–0.52 s, at rest 0.49–0.62 s. SFX: peaks −3/−6/−4 dBFS, no clipping, 63–213 ms audible, centroids flap 3.1–5.0 kHz,
  fold 1.1–1.7 kHz, pat 1.4–1.9 kHz. 40-piece wave: 40 requested → 19 played over 1.15 s (~16/s, gaps ≥33 ms, irregular).
  Profile 150 cards looping (1366×1024): 60.0 fps mean, 0 hitches, frame p95 17.1 ms = vsync jitter (Metal caps at refresh);
  script process p95 0.32 ms; GPU p95 3.0 ms (Vulkan/MoltenVK). Blind A/B `C_motion_r1` made (ref video_seq s_157–172).
  Note for lead: `check_all` currently fails on `core/characters/paper_puppet.gd:257` (component D), not on C files.
- 2026-11-18 B_look round 1 (look-dev). Story check: the user's latest note prefers 「해와 바람」 over 팥죽할멈; BRIEF already
  says so, and the look-dev work does not depend on the story (it uses the sun_wind test props and the traveller).
  New: `core/look/look_rig.gd` (LookRig: AgX + adjustments, warm key with 2-split soft shadow, cool fill, camera orbit
  whose DOF follows `focus_target`, CanvasLayer post pass), `core/look/ground_layers.gd` (GroundLayers: walnut table,
  book cover + page block, teal stream card, felt sheet with the stream cut out and a visible cut edge, lobed
  ground-cover patches stacked two deep, raised cream path with a card edge; queries path_distance/stream_distance/
  surface_y/path_centre_3d), shaders ground_layer/stream/page_stack/table_wood/post_grade, `art/tex/felt_noise.png`.
  paper_print: cream die-cut rim inside the cut line, baked foot AO, ink sat/contrast, stronger translucency (uniform
  names that PaperCard uses are unchanged). Bench `scenes/look/look_bench(_v1..v4).tscn`: 1001 cards, ~150+ in frame.
  Metrics (r1c, views 0-4): lum_mean .37-.42 ok; p05 .074-.138 ok (v3 .074 slightly low); p95 .70-.76 ok;
  sat .63-.68 (v4 .677 slightly high); warmth .19-.25 ok; edge_density .097-.118 (v0/v1/v4 slightly high);
  tiltshift_ratio 3.0-3.7, OUT of range (the middle band renders much sharper than video footage; lowering DOF only
  weakens the look). Lead bench baseline: lum .62, sat .39. Profile (1366x1024, Mac): Vulkan GPU p95 7.7 ms,
  2387 draw calls (Metal 834), frame time capped at vsync. Draw calls need MultiMesh/merging (task for F/lead).
  Blind A/B: artifacts/ab/B_look_r1 (seed 1).
- 2026-11-18 D_chars round 1 (characters & walking). New: `game/art/chars_rig/` (cut_rig.py splits sw_trav_walk /
  walk_nohat / hold / shirt into body + leg_l + leg_r + seat layers, hidden leg tops repainted from the visible pants
  texture; cut_gusts.py lifts the wind card's own paper curls into gust cards; rig.json = bboxes + hip pivots).
  `game/core/characters/`: PaperPuppet (distance-driven gait: stride = speed × step period, stance foot planted in world,
  hips ride the stance leg + hop, waddle roll ±8°, smooth card yaw ±38° toward the walk, pose swap = edge-on flip + hop;
  fan/sit are single cards), Walker (Curve3D path follow, tap/click → nearest path point, WASD free walk, eased speed),
  FollowFocus (critically damped focus + eased lead; drives LookRig with follow_smooth=0), SkyHanger (sun/wind on a live
  bezier wire stem, sway/bob springs, push/puff), WindGusts (blow/tire/calm, puffed-cheek print, curl swooshes),
  PaperSpring (sub-stepped springs + fixed_dt for deterministic captures). Benches: `scenes/chars/walk_bench.tscn`
  (420 catalog cards, demo timeline wind→hold→sun→nohat→shirt→fan→sit), `puppet_closeup.tscn`.
  Fixed during the round: explicit-Euler roll spring blew up on capture frame hitches (figure spun) → sub-stepped springs;
  PaperCard foot-AO darkened whole leg cards → AO zeroed on body/seat, thin band on legs (materials of our own textures).
  Metrics walk frame 0/10: lum 0.44, p05 0.13, p95 0.72, sat 0.68 (high, LookRig-owned), warmth 0.34, tiltshift 3.0,
  edge 0.083. Ref s_210/216: lum 0.41-0.42, sat 0.50-0.54, tiltshift 1.8-2.2. A/B `artifacts/ab/D_chars_r1` (seed 1,
  strip, ours 16 frames every 3 vs ref s_206..s_221 meadow walk). Assumptions: the wire stem rises from the page behind
  the path (pop-up style) rather than a string from above (string mode exists: SkyHanger.hanging); arms stay on the
  body card this round.
- 2026-11-18 A0 atlas kit: 16 atlas sheets (Codex imagegen 1536×1024, magenta bg, shared style anchor in
  `tools/atlas/make_jobs.py`) → **419 clean cards** in `game/art/atlas/<sheet>/`, catalogue `game/art/atlas/catalog.json`
  (id, path, sheet, category, label, height_units, cross_slot, biome, season, tags, px). Sheets: meadow_field, village_houses,
  village_props, stream_water, forest_broadleaf, forest_conifer, farm_animals, hills_clouds, small_decor, bushes_hedges,
  autumn, winter_snow, spring_blossom, korean_village, korean_nature, fairytale_west. Pipeline: `slice_atlas.py`
  (distance + HSV-hue magenta key, local unmix of thin gaps, despill, run-length CC, fragment merge, base check, lossless webp),
  `contact.py` (QA sheets `art_src/atlas/qa/*_contact.png`), `build_catalog.py` (labels in `tools/atlas/labels/*.json`;
  dropped slices → `art_src/atlas/rejects/`), `qa.py` (halo px total 89 over 419 cards, all on a purple thistle).
  Bench `scenes/atlas_bench/atlas_bench.tscn` (179 cards from the catalogue, CrossCard for cross_slot) → `art_src/atlas/qa/atlas_bench.png`.
  Found: (1) codex image tool can save ANOTHER session's latest image (winter_snow came back as a copy of autumn) — check
  md5 duplicates + eyeball every raw; (2) Godot import sometimes leaves `valid=false` for webps written while another agent's
  editor imports — delete the .import and re-import; (3) paper_print rim (fixed 0.006 world units) turns thin leaves/grass of
  small cards fully cream — B should scale rim_width with card size or skip features narrower than ~2× rim.
