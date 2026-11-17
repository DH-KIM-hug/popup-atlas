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
- 2026-11-18 A_art round 1 (card art kit, 해와 바람 world). 18 Codex imagegen sheets (shared style anchor STYLE_V1 in
  `tools/art/mk_jobs_cards.py`, ref = sw_trav_walk for paper/palette only, magenta bg) → `tools/art/key_cards.py`
  (magenta key with band-limited soft alpha + hot-pink cleanup + despill, connected-component split, trim, hinge at
  bottom) → `tools/art/publish_cards.py` → **78 cards** in `game/art/cards/<cat>/` + `catalog.json`
  (tree 12, conifer 5, bush 6, flower 8, grass 3, water/reeds 5, bank 3, field 5, rock 3, mushroom 4, fence 4,
  bridge 1, house 4, village 6, animal 6, hill 3). Kit sheet: `art_src/cards/_kit_contact.png`. Codex refuses
  non-square output for "square" jobs → sheets use 3:2 / flexible aspect.
  Bench `game/scenes/art_bench/art_bench{,_v1..v4}.tscn` (copy of lead bench): path village→wheat→stream+bridge→
  meadow→forest, groves/field rows/hedgerows; 3055 cards, 88–140 in frame per view. Found bug in lead bench
  `_add_card`: hinge.position set under a yaw-rotated base swings every card around the origin (fixed in my copy).
  Bench look tweaks (mine only): focus 6.2, exposure 0.78, stronger DOF, ground tint 7fa477.
  Metrics r1 views v0..v4: lum_mean .47–.58, p05 .13–.27, p95 .77, sat .46–.53, warmth .21–.36,
  tiltshift 1.47–2.06, edge_density .074–.13. Blind A/B: artifacts/ab/A_art_r1 (refs v_09,01,06,03,04).
  Open: shadows long/hard + high camera vs ref low angle (look-dev/lead); no bank strips in bench (read edge-on).
- 2026-11-18 B_look round 2 (look-dev). Story stays 「해와 바람」 (user's note prefers it over 팥죽할멈; BRIEF agrees).
  Applied the r1 critic fixes. LookRig: lower camera (27-30 deg, fov 20-21, distance 8-9.5); key raised to 52 deg at
  1.75 energy; shadow_opacity 0.78 (new export), blur 2.0, angular size 2.5; warm-sage ambient 0.62; exposure 0.84;
  vignette .32->.14. Tilt-shift band is narrower (half .13, soft .26), the near foreground blurs more than the far
  (new export tilt_top_bias .4), and physical DOF is tighter around the focus point. Post grade shadow tint is now
  sage-warm, not brown. Ground felt is lighter sage with more visible fibre; the cover patches are darker greens
  with no ochre or pale blobs; the table shader now has walnut planks, rings, pores and a varnish sheen.
  paper_print rim_width .0035->.006, so the die-cut border is wider.
  Bench is rewritten on art/cards/catalog.json (component A). It is built as vignettes with open felt between them:
  an autumn grove, a blossom orchard, conifer edges with grey rocks, a sheep pasture (fence, gate, haystack, bale,
  wheelbarrow, well, trough), a bench, lantern and signpost by the traveller, reeds with geese, an arch bridge where
  the path crosses the stream, path-verge clumps, and a few windswept sun_wind trees. Trees and conifers are
  CrossCard (slotted pairs). Card thickness is about 2.4% of height. Scale ranges 0.7-1.3x and cards have a slight
  random lean. Each view has hero cards in the near foreground (a mushroom, a stump and a fern).
  1296 card meshes (CrossCard counts as 2); about 80-150 in frame.
  Metrics r2e v0-4: lum .50-.52 ok; p05 .19-.22 ok; p95 .66-.79 ok; sat .59-.64 ok; warmth .26-.33 ok;
  edge_density .031-.059 (low: the path and stream take up large areas); tiltshift_ratio 6.8-9.3 (OUT: the band
  blur is heavy because the critic asked for that; the metric and the critic disagree here).
  Profile on Metal: p95 frame 10.2 ms (vsync-capped), 879 draw calls. On Vulkan: max GPU 6.4 ms, 2565 draw calls.
  Blind A/B: artifacts/ab/B_look_r2 (seed 2; refs v_01, 03, 04, 05, 12).
- 2026-11-18 C_motion r2. Story still 「해와 바람」 (user's pick over 팥죽할멈; unchanged). Applied the r1 critic's motion fixes.
  `core/pop_hinge.gd` rise: an eased page pull (0.24/0.32/0.45 s to vertical for w 0.5/1/2.2) followed by a stiff spring
  (4.5 Hz·w^-0.15, zeta 0.75·(0.88+0.12w)). Measured: overshoot 4.4/3.5/2.4°, one rebound, ±0.5° reached +0.12/0.12/0.14 s
  after vertical (0.35/0.45/0.59 s total), twist ≤1.4/0.9/0.6°. Twist now turns about the card's own vertical (Basis X·Y);
  the r1 Euler order spun tilted cards in the page plane, which read as sideways slivers. Fold: same topple, page bounce
  e 0.32→0.12, rebound 0.5°, at rest 0.42–0.54 s. New `twist()` accessor. This deliberately departs from the brief's
  8–15° / 0.6–0.9 s spec, because the critic called that "jelly".
  `core/cross_card.gd`: B's follower is stiffer and better damped (3.8 Hz, zeta 0.72).
  `core/pop_wave.gd`: new `cover_pairs()` occlusion order. A piece standing inside another's flat footprint rises
  ≥0.12 s after it and folds ≥0.14 s before it, so nothing pushes up through a flat card. Footprints use metas `card_h`/`half_w`.
  Bench `scenes/motion/motion_bench.gd` rebuilt: 179 cards from art/cards/catalog.json (16 categories, clustered: groves
  with warm accents, a cottage, well, fence and lantern landmark, stream banks, animals, undergrowth) on B's GroundLayers
  (narrow 0.3 path, 6 cover patches) under B's LookRig (elev 37°, dist 6.8, narrow DOF, slow ±4° yaw drift).
  All pieces fold back with the print up, so the folded page shows the printed art and no plain-back "ghosts".
  The wave runs outward from the traveller at 3.2 u/s.
  Look metrics (rise frames 5/10/15): lum .45–.52, p05 .14–.30, sat .63–.66, warmth .30–.34, edge .065–.072 all in range;
  tiltshift 4.7–5.3 is high, as in B's r1 (a stronger DOF variant, sat .69, was reverted).
  Profile, 179 cards looping at 1366×1024: Metal frame p95 8.9 ms (120 Hz cap), 1 hitch; Vulkan GPU p95 4.5 ms; script p95 0.27 ms; 322 draw calls (Metal).
  Audio: 179-card rise, 179 requested → 31 played (15/s, gaps ≥33 ms); fold 358 → 38.
  Artifacts: `artifacts/motion/` (angle_curve_r2.png, curves_r2.json, rise_r2/, fold_r2/, still_up_r2.png).
  Blind A/B: `artifacts/ab/C_motion_r2` (seed 2, strip, ref video_seq s_157–172).
- 2026-11-18 D_chars round 2 (characters & walking). Story stays 「해와 바람」 (user's pick over 팥죽할멈).
  Puppet: `art/chars_rig/cut_rig.py` re-cut all 4 rigged poses as body + **hips** + leg_l + leg_r. The hips piece sits in
  front of the leg tops down to just below the crotch, with rounded hems. Hidden leg tops are now a flat median pants
  colour with a rounded cap (the r1 tiled repaint copied dark lining blotches). Brass **brads** are drawn at the leg
  pivots, which moved down onto the visible hip piece. Classifier holes are filled (hold pose), and the original
  die-cut alpha is used below the hem. Parts are **cropped to their alpha bbox**: with full-canvas textures,
  paper_print's UV rim (computed from card_size) covered whole leg cards in cream. That was the r1 "ghosting/double
  limb" and white-pants look. `seat` → `hips` in rig.json.
  PaperPuppet: hips z in front of the legs. Swing uses a snappy hold-then-snap smootherstep, so it reads as a hinged
  card, not a tween. foot_lift 0.035 → 0.024. Rim width is thinned on puppet materials (body 0.0028, joints 0.0016),
  so there is no sticker keyline around joints.
  Bench `scenes/chars/walk_bench.gd` rebuilt on B's GroundLayers: felt sheet, raised path card with edge, stream cut,
  ground-cover patches. It is dressed in depth bands from both catalogs (A + A0):
  - foreground side trees (0.6-0.85) and hedges, cropped at the bottom;
  - near verge: scalloped/berry hedge run with gaps, rail fence, hens on the verge ahead of the walk, pebbles,
    milestone, signpost;
  - behind the path: fenced sheep pasture, scarecrow, haystack, orchard clump;
  - stream with reeds and ducks, copses, conifer line, two rows of layered hills;
  - clustered meadow clumps with open felt between them.
  Life: animals hop/rock, and grass and flowers flap on a gusting wind (185 animated cards). The bench sets its own
  light: key 63° (shorter shadows), angular 7, shadow_blur 4, opacity 0.7, fill 0.7, vignette 0.07, tilt_blur 1.0,
  physical DOF near margin 1.5 / amount 0.07. Camera elevation 25°, distance 7, fov 21: the hero is ~11-12 % of frame
  height (r1 ~6 % in the bench). Demo events now start at 1.4 s, so the opening walk is clean.
  Metrics walk f0/f10: lum .50, p05 .15, p95 .80, sat .61, warmth .30, edge .065 (all in range).
  tiltshift 6.2 is OUT of range: the mid band is very sharp, sharp_bot 31 vs ref 108. It is lower than the 8.9 of the
  first r2 try, which had a big blurred foreground willow, and r1's 3.0 had no foreground layer.
  A/B `artifacts/ab/D_chars_r2` (seed 2, strip, ours 16 frames every 3 at 960x720 fixed 1/60 vs ref s_206..s_221).
  Proposals:
  - for B: paper_print's rim should use texel size, not rim_width/card_size, when a texture has big transparent margins.
  - for lead: PaperCard could auto-crop to the alpha bbox.
  - for A0: atlas animal heights are fine.
- 2026-11-18 D_chars round 3. Story stays 「해와 바람」 (user's pick over 팥죽할멈).
  PaperPuppet (`core/characters/paper_puppet.gd`):
  - Legs now swing as hinged paper cards. The swing is in the card plane, about the card normal, clamped to ±27°, with
    a small out-of-plane tilt for depth walking (±14°). This fixes the r2 "sideways kick": the leg used to aim straight
    at the world footprint, so on a yawed card the back foot poked out sideways.
  - Card yaw toward the walk is down from 38° to 20°, and the swing hang is shorter (it starts at s 0.04, was 0.1).
  - New forward lean into the walk, 3°: roll for sideways walking, pitch for depth walking.
  - New coat lag: the body card trails the waddle on a soft spring, pivoting at the hips, clamped to ±0.05 rad.
  - Close-up check: `.agent_out/captures/d3_close/`. The back foot now steps instead of kicking.
  Walk bench (`scenes/chars/walk_bench.gd`):
  - Camera: elevation 31°, distance 5.4, fov 20, plus a ±5° yaw drift, so the layers slide against each other.
    Walk speed is 0.38. The hero is about 13% of frame height.
  - Light: low warm key (36°, LookRig exports) with darker directional shadows (opacity 0.82). The r2 high-sun overrides
    are removed. Ambient 0.44, a less orange key colour, vignette 0.17.
  - Ground: sage felt (71895f) instead of mint, and the path is narrower (0.38).
  - Layout: placement overlap is allowed (radius factor 0.32), cards lean ±5° (critic asked for 3-10°), meadow clumps
    went from 70 to 150, and there is a near occluder row of dark pines and hedges.
  - Palette: 60% of flower and bush cards use a dusty print variant (own material set via edge_color, ink_saturation
    0.82). In total 699 cards, 357 of them animated.
  Metrics on walk frames f0/f15:
  - lum .43, p05 .19-.20, p95 .69, sat .51, warmth .22, edge .063-.064: all in range.
  - tiltshift 3.8-4.1 is still OUT of range (1.3-2.5), but better than r2's 6.2.
  - Versus r2 f10 (lum .50, sat .61), the frame is darker and less saturated, as the critic asked.
  A/B `artifacts/ab/D_chars_r3` (seed 3, strip, ours `.agent_out/captures/d3_walk_seq` 16 frames every 3 at 960x720,
  ref s_206..s_221).
  Proposals:
  - for lead/B: a lit-side cream edge band and a darker core on card side faces (PaperCard/paper_edge), which the critic
    asked for in r1 and r2;
  - for C: motion_bench.gd currently fails to parse (`_ambient_step` missing), which makes check_all fail.
- 2026-11-18 C_motion r3. Story still 「해와 바람」 (the user's pick over 팥죽할멈). Applied the r2 critic's motion fixes.
  `core/pop_hinge.gd`: rise AND fold are now page-driven. An eased path (92% smoothstep) is followed by a stiff spring
  (5.2 Hz·w^-0.15); the old topple physics and the `fall_hz`/`bounce` exports are removed, and new `fold_time`, `ease_share`
  and `settle_lift` exports are added. Rise measured (curve_job): vertical at 0.30/0.41/0.57 s (small/medium/large),
  overshoot 2.4/1.8/1.2°, one rebound, ±0.5° reached 0.10 s after vertical, twist ≤1.4°. Fold: slow start, fastest at 45°,
  decelerates into contact at 0.40/0.52/0.69 s, then a soft air-cushion settle of 1.8/1.4/1.0°; at rest by 0.47/0.60/0.76 s.
  PaperAudio pat gain is rescaled to the softer landing speed (speed/1.8).
  Bench: 360 hinges. Shared atlas small props are added (critters, props, crops, flowers, mushrooms, rocks) and the
  undergrowth is about 0.68x size and clustered. D's PaperPuppet (h 0.45) now strolls the path. New
  `scenes/motion/paper_ambient.gd` adds cut-paper butterflies (hinged wings) and falling leaves; textures are generated
  by `make_ambient_tex.py`. Reeds, grass and flowers sway rigidly about their base once standing. The camera has a
  continuous yaw and dolly drift (8–11 s periods) at elev 32°, dist 6.0, fov 22. Felt is shifted to yellow-sage 85995a.
  Tilt-shift: tilt_blur 1.4 and band 0.10. The 2.2/0.085 variant (tiltshift 50–64, edge .03) was too extreme and is not kept.
  Metrics still: lum .445, p05 .15, p95 .73, sat .57, warmth .27 (in range). tiltshift 13.5 and edge .034 are out of
  range: the critic asked for heavy DOF, and the metric and the critic disagree here.
  Profile (loop, 1366×1024): Metal frame p95 9.4 ms (120 Hz cap), 3 hitches in 953 frames; Vulkan GPU p95 4.5 ms; 586 draw calls on Metal.
  Audio: 150-card job, rise 149 requested → 27 played; fold 298 → 24. Samples unchanged: flap 132–174 ms at −3 dBFS,
  centroid 3.1–5.0 kHz; fold_down 201–243 ms at −6 dBFS, 1.1–1.7 kHz; pat 68–98 ms at −4 dBFS.
  Artifacts: artifacts/motion/{angle_curve_r3.png, curves_r3.json, rise_r3/, fold_r3/, still_up_r3.png}.
  Blind A/B: artifacts/ab/C_motion_r3 (seed 3, strip, ref video_seq s_157–172).
  Proposals for B: clamp the facing-ratio darkening in paper_print to ≤15% (the red-tree value pop). The look_metrics
  tiltshift target range likely needs re-baselining against the critic's DOF ask.
- 2026-11-18 B_look round 3 (look-dev). The story stays 「해와 바람」, as the user asked; the bench uses the traveller and the windswept sun_wind trees.
  Applied the r2 critic fixes:
  - Ground relief. `GroundLayers.hill_specs` adds stacked felt hill tiers (0.06 thick, cut edges, clipped off the path and stream; `surface_y` and `hill_level` know about them). New `add_folded_rock()` makes tented paper rocks with two printed faces and a crease (`shaders/folded_rock.gdshader`). New `add_patch()` lays dark moss under groves. The felt is desaturated (819a78), with large low-frequency mottling.
  - Anchoring. New `core/look/contact_shadows.gd` (ContactShadows, one MultiMesh draw) plus `shaders/contact_shadow.gdshader` put a soft ellipse and a dark crease at every card base. The key light is now 44°, with shadow blur 1.1, opacity 0.86 and angular size 1.2, so shadows are shorter and crisper.
  - Grade. Warm depth haze (FOG_MODE_DEPTH, past the focus), contrast 1.03, saturation 0.98 plus a 0.92 post pass, exposure 0.8, vignette 0.2. Tilt-shift is milder: max_lod 0.95, band ±0.15/0.34, bias 0.9, dof_amount 0.05. In r2 the bottom third was about 25x blurrier than the reference.
  - Cards. paper_print gets a weak satin sheen (roughness about 0.74, specular 0.22), and the rim width scales with card height, which is A0's note about thin leaves.
  - Bench. It now draws from both catalogs (cards plus atlas, no winter), about 270 distinct ids per view, picking the least-used id from each pool. Conifers are 1.55x and broad trees 1.25x, with conifer lines on the far hills. There are hedgerows along the path, 10 folded-rock clusters, and animals and props around every view's focus. A lens keep-out stops tall cards from landing in front of the camera. All single cards use back_print, which ends the plain-back ghosts. 2250-2380 card meshes.
  Metrics r3g v0-4: lum .41-.44, p05 .11-.16, p95 .61-.74, sat .50-.59, warmth .19-.29 (all in range); edge_density .055-.10
  (in range or close); tiltshift 3.7-7.4 (still above 2.5 but down from 6.8-9.3; the reference's top and bottom thirds are much sharper).
  Profile (1366x1024): Metal p95 9.0 ms (120 Hz cap), 1381 draw calls; Vulkan max GPU 6.1 ms.
  Blind A/B: artifacts/ab/B_look_r3 (seed 3; refs v_01, 03, 04, 12, 13).
  Proposals for the lead: (1) the BRIEF tree heights (0.6-1.1) are too short against bushes for the critic, and the bench scales conifers about 1.5x; (2) the critic keeps asking for a slight card bend, but the style rule says cards never bend, so the bench does not bend them.
- 2026-11-18 A_art round 2 (card kit + bench, 「해와 바람」 kept per user's pick). 14 new Codex sheets
  (`tools/art/mk_jobs_cards_r2.py`: STYLE_V1 anchor unchanged + "print grain" addendum against the r1 "vector sticker"
  note; reference 2 = r1 sheet sh_trees_green for kit consistency; launcher `tools/art/run_r2.sh`; 2 jobs were rejected
  as "portrait, not 3:2" and were rerun with flexible aspect). New `tools/art/split_manual.py` for touching objects.
  Catalog 78 -> **146 cards** (ids of r1 unchanged; new: 8 layered hill strips/wooded hills, 6 wheat patches incl. stook,
  hay square/stack/pole-stack/cart, woodpile, ladder, plank bridge, jetty, stepping stones, lily pads, ducks, ducklings,
  hens, cow, rabbit, cat, 8 trees, 6 conifers, 5 large foreground plants (new category `foreground`), lavender, thistle,
  clover, forget-me-not, white daisies, wild rose, blackberry, boxwood, stone and round cottages, flower pots, washing
  line, pump, beehive, coop, barrel). Hill webp max width raised 1600->2048.
  Bench `scenes/art_bench/art_bench.gd` rebuilt on B's LookRig + GroundLayers (was own lights/flat page): one 22x15
  spread, village (lit windows/lanterns via small warm OmniLights), wheat field of broken rows with varied lengths
  plus haystack/stook/cart clearings, stream with reed clumps, ducks, lily pads, side-on plank bridge, sheep meadow, forest edge,
  three rows of hill cards at the back and wooded hills mid-distance. Props are clustered (3-7, scale 0.7-1.4, overlap),
  gaps are filled with single-species clumps, cards lean ±3.7°/tilt ±2-3° and face the reader side of the view, and
  big foreground plants sit near the camera. The traveller is 0.44 tall in the bench only (critic asked ~1.3x; the brief
  contract is 0.36, so this is a proposal for the lead and D). ~1900 cards; 242-650 in frame per view. Cameras: elevation 24-27°.
  Metrics r2 v0-4: lum .41-.50, p05 .17-.25, p95 .66-.73, sat .57-.61, warmth .25-.32, edge .075-.083 (all in range);
  tiltshift_ratio 5.8-7.0 (out; it comes from LookRig's DOF/post. I tried tilt_blur 1.4 and it didn't move the
  ratio, so I reverted to B's default). r1 for comparison: sat .46-.53, edge .074-.13, tiltshift 1.5-2.1.
  Blind A/B: artifacts/ab/A_art_r2 (seed 2; ours art_src/cards/bench_r2/art_r2_v0..4; refs v_01,03,04,06,12).
- 2026-11-18 A_art round 3 (card kit + bench; story stays 「해와 바람」, as the user chose over 팥죽할멈).
  Kit:
  - New `tools/art/strip_rim.py`, wired into `publish_cards.py` (STRIP_RIM). It strips the printed cream outline from
    every card: ring-by-ring peeling while the ring is mostly cream, plus one transition ring, speck removal and a
    1 px antialiased re-cut. This answers r2's "uniform white sticker border". The paper_print shader rim still
    draws the thin cream core.
  - All 146 r1/r2 webps are republished in place with the same ids; the old ones are backed up in
    `art_src/cards/backup_r2_ship/` for revert.
  - 6 new Codex sheets (`mk_jobs_cards_r3.py`, `run_r3.sh`). STYLE_V3 = STYLE_V1 with "no outline/no light rim",
    plus the print-grain addendum and ref sh2_trees_green_b.
  - The catalog goes from 146 to **188 cards**:
    - 3 hero trees: oak, willow, chestnut (1.3-1.45 tall)
    - 8 logs/stumps/boulders/stacked stones
    - 20 small fillers with distinct silhouettes
    - 6 bushes
    - 5 trees: birch, lollipop fruit, poplar, wind-bent hawthorn, rowan
  Bench (`scenes/art_bench/art_bench.gd`):
  - Camera is closer and lower: distance 6.2-6.4 (r2: 10-10.5), elevation 20-22°, fov 21. The backdrop hills and the
    table now show in frame.
  - The traveller is 0.6 tall (bench only; proposal for lead/D) and placed on a third via a lateral focus offset.
    It has a 0.75 clear ring, and a lens keep-out keeps tall cards off the hero-camera line.
  - Stronger DOF overrides: tilt_blur 1.35, band 0.11/0.3, dof_amount 0.075, near 0.6, far 1.8.
  - Ground and relief: B's ContactShadows under every card, hill_specs felt tiers, moss patches under groves,
    10 folded-rock clusters.
  - Variety: least-used id picking. Each view gets 2 flat hero trees behind/beside the hero.
  - Back hills are 4 depth rows with gaps (parallax).
  - Density: wheat rows about 40% fewer and shorter; path 0.44 wide (was 0.56); gap-fill 420 clumps (was 520).
  - Totals: ~1650 cards in the spread, 161-286 in frame.
  Metrics r3 v0-4:
  - In range: lum .40-.47, p05 .15-.21, sat .53-.64, warmth .23-.31.
  - Out of range: edge .041-.058 (just below .06, from the blur and open felt) and tiltshift 7.6-12 (out, on
    purpose: the r2 critic asked for heavy DOF; the metric and the critic disagree, as B and C also logged).
  Blind A/B: artifacts/ab/A_art_r3 (seed 3; ours art_src/cards/bench_r3/art_r3_v0..4; refs v_01, 03, 04, 06, 12).
  Proposals: traveller 0.6 in benches; cards still can't bend under the style rule.
- 2026-11-18 INT round 1 (integrator: one unified world). Story stays 「해와 바람」.
  New reusable template `game/scenes/world/meadow.tscn` (script `core/world/meadow.gd`, class MeadowWorld, exports
  seed_value/view/fixed_step/pop_on_load/pop_radius/walk). Seed 1, page 28x20: winding road front→back, stream across
  with a plank bridge, village edge (cottages + barn, yard props, fences, chimney smoke), wheat field of broken crop
  rows with haystacks/cart, forest edges on the high tiers, 3 rows of hill cards at the back, groves, folded rocks.
  New files in `core/world/`:
  - `card_library.gd` (CardLibrary): loads atlas (A0) + card kit (A) catalogs, `query(category, tags, biome, season)`,
    pools, seeded least-used `pick()`. Excludes winter/korean/fairytale sheets for this meadow.
  - `meadow_ground.gd` (MeadowGround extends B's GroundLayers): stacked relief. Felt base, recessed printed water card,
    cut stream banks, 29 rolling terrain tiers (1-5 high, 3.2 mm each, each stacked inside the one below, cream cut
    edge), raised paper verges along the road, the road as its own die-cut layer with a deckled edge, plank deck over
    the stream (`shaders/plank_deck.gdshader`), and soft drop-shadow skirts outside every raised cut edge, stronger
    on the side away from the key (`shaders/drop_skirt.gdshader`, one draw).
  - `static_cards.gd` (StaticCards): batches non-moving cards into one MultiMesh per print, using PaperCard's mesh
    and materials (cross cards are 2 instances).
  - `wind_sway.gd`: a travelling gust rocks rigid cards about their base (grass/flowers/reeds/crops more, trees barely).
  - `chimney_smoke.gd`: cut-paper puff cards that rise, grow and shrink away.
  Integration: cards within pop_radius 4.2 of the traveller are PopHinge/CrossCard (C) and rise in a PopWave from
  the traveller on load (speed 4, wave ends ~1.7-2.2 s). Everything else is static MultiMesh. PaperAudio watches all
  hinges and steps. PaperAmbient (C) adds butterflies and leaves near the traveller. D's Walker + PaperPuppet
  (0.36 tall) auto-walks the road, and the FollowFocus camera follows. LookRig (B) is set to elevation 28-30, fov
  20-21, distance ~10, near/far DOF, post tilt 0.55, haze from focus+0.8, vignette 0.14, post saturation 0.9, and
  a muted stream.
  Per-view lens foreground: 6 tall cards just above the bottom edge use a separate RNG. A start-view keep-out
  stops tall cards from standing between the camera and the traveller.
  Card edges:
  - New `tools/world/clean_atlas.py` runs A's strip_rim over all 395 non-winter atlas cards and writes the results to
    `game/art/atlas_clean/` (originals untouched; CardLibrary uses the clean copies). Only 56 had a printed rim.
  - The main halo was the shader rim, so `paper_print.gdshader` rim_width goes from 0.006 to 0.0024, with a new
    rim_mix 0.5 (it lightens toward cream rather than replacing). This changes every bench that uses PaperCard.
  BRIEF "World contracts": camera line changed to 28-40°, fov 18-24, tiltshift target 2-3.5, and the template is listed.
  ~4700 cards per spread (550-650 hinged, ~4050 static), 386-397 distinct ids used.
  Metrics r1 v0-5 (settled, frame 170 @ fixed 1/60):
  - lum .365-.416, p05 .10-.17, p95 .63-.67, sat .56-.64, warmth .23-.28, edge .073-.095: all in range.
  - tiltshift 3.26-4.84 (v1-v4 are 3.3-4.0, v0 4.84). Above the 2-3.5 target, though down from 5-13 in the benches.
  Profile (meadow.tscn, walking, 1366x1024):
  - Metal frame p95 9.0 ms (120 Hz cap), 0 hitches, ~1600 draw calls.
  - Vulkan GPU p95 11.6 ms, 4569 draw calls.
  Captures: `artifacts/world/int_r1/` (meadow_r1_v0..5 + meadow_r1_midwave_v0 at frame 52).
  Tool: `tools/world/capture_meadow.py TAG [frames] [views]`; capture scenes `scenes/world/cap/meadow_v0..5.tscn`.
  Blind A/B: `artifacts/ab/INT_r1` (seed 1; refs v_01, 03, 04, 06, 12, 13).
  Open issues:
  - The lens keep-out and lens foreground draw from the shared RNG/attempts, so card counts differ slightly between views (seed+view is deterministic).
  - Back hills only show in views near the far end.
  - The camera is still higher and wider than the reference's close, low lens.
  - Flat felt still shows between clumps in places.
  - Vulkan GPU at 11.6 ms on the Mac leaves little iPad headroom; draw calls should be chunked by region.
- 2026-11-18 INT round 2 (integrator). Answers the r1 critic, whose fix list for our (crisp folk-art) side was:
  clearings and a hierarchy around a tiny hero, printed rocks instead of grey folded triangles, path with edge/lift/
  shadow instead of cream blobs, terrain lift, a coloured core edge, mild DOF and atmospheric falloff.
  Changes (r1 scripts backed up in the session scratchpad; all edits in game/core/world + 2 shared files):
  - Camera (`meadow.gd` VIEWS): distance 10 → 7.2-7.6, elevation 28-30 → 25-27, fov 20. The traveller is now
    ~110 px tall and the focal point of every view; views placed on vignettes (bridge, village edge, forest bend).
  - Hierarchy: HERO_CLEAR 1.3 clearing reserved around the traveller start; `_meadow_fill` now gated by a seeded
    low-frequency FastNoiseLite mask (clumps vs open felt clearings, no even confetti). Cards per spread 4700 → ~3100.
  - Rocks: grey folded-triangle rock clusters replaced by printed rock cards (`rock` pool, scale 1.5). Green folded
    hillocks kept, a bit smaller.
  - Road: warm sand print `d9bf8a` (cream cut edge now contrasts), stronger cast skirt (0.08 wide, 0.85); verges a
    distinct yellow-green card, 2.2 mm thick (was 1.6) with a stronger skirt. `cover_patches` 70 → 28 (the pale lobes
    read as spilled paint).
  - Bridge: the two edge-on bridge-image cards replaced by fence-print rail cards along both deck edges.
  - Card edge: thickness h*0.024 → h*0.03 (hinged + StaticCards); `paper_card.gd` side walls now tinted 30% toward
    the print's average colour (coloured core, not pure cream). Shared file: every PaperCard bench changes.
  - Grade/haze: key energy 1.85 → 2.05, dof_amount 0.06 → 0.05, haze length 8 → 5.5, amount 0.62 → 0.7;
    hills_clouds_03 (saturated red mountains) excluded from the back rows.
  - BRIEF "World contracts" camera line: 24-40°, distance ~7-10.
  Metrics r2 v0-5 (settled, frame 170): lum .382-.434, p05 .123-.187, p95 .643-.663, sat .537-.623,
  warmth .236-.257, edge .052-.082 (v3/v4 .052-.053 slightly under .06), tiltshift 2.28-4.08
  (v0 3.18, v1 3.19, v2 2.28, v3 3.53, v4 2.64, v5 4.08; r1 was 3.26-4.84).
  Profile (meadow.tscn walking, 1366x1024, 6 s): Metal p95 9.4 ms (120 Hz cap), Vulkan p95 9.2 ms, 0 hitches.
  Captures: `artifacts/world/int_r2/` (meadow_r2_v0..5 + meadow_r2_midwave_v0 at frame 52).
  Blind A/B: `artifacts/ab/INT_r2` (seed 2; refs v_01, 03, 04, 06, 12, 13).
  Open: felt still flat-coloured over large open areas; back-hill row still only in far views; rail cards thin when
  seen along the road; no card bow (style rule says cards never bend); v5 tiltshift 4.1 above target.
- 2026-11-18 INT round 3 (integrator). Answers the r2 critic, whose list for our (crisp folk-art) side was: flat floor,
  zero-thickness cards with white rims, no lens character ("game camera"), even scatter, hero the height of a flower,
  no paper tooth, flat water/paths. r2 scripts backed up in the session scratchpad (world_r2_backup).
  Changes:
  - Relief (`meadow_ground.gd`, `meadow.gd` hill_specs): tier_t 3.2 → 5 mm; 9 new broad low plateaus (1-2 tiers)
    over the near meadow, so road and stream now run in channels between raised board and every view shows
    stacked cut steps (43 tier slabs, was 29). Stream bank lip 8 → 26 mm (channel reads sunk). Tier cut edges
    less white (cream lerp 0.68 → 0.5; read as planks at grazing angles). Tier print mottle stronger and larger
    (strength 1.0, scale 0.11, darker/ochre mottle); felt + tier fibre 0.2 → 0.34-0.36, grain 0.16 → 0.26-0.28,
    bump 0.9. Road gets printed gravel speckle (0.45, umber).
  - Lens (`meadow.gd`): elevation 25-27 → 21-23° (more overlap, longer view into haze); DOF amount 0.05 → 0.07,
    near margin 1.2 → 0.9, near transition 1.4 → 1.1; tilt_blur 0.55 → 0.66; lens-foreground cards nearer the lens
    and 20% taller so one or two blurred cards frame the shot. Haze warmer (dcc49a, amount 0.62, length 6).
  - Scale/hierarchy: POOL_SCALE flower 0.72, grass 0.8, mushroom 0.75, bush/sapling/hedge 0.85 (traveller stays 0.36).
  - Clustering: meadow fill clumps of 3-7 at spread 0.22, pack 0.62 (overlapping front/mid/back); rejected sites in
    open felt get a sparse single low tuft (30%) so clearings are not bare sheet.
  - Card edges (shared files, every PaperCard bench changes): thickness h*0.03 → h*0.04 (min 11 mm, max 40 mm) in
    hinged + StaticCards; `paper_card.gd` side wall edge.lerp(avg, 0.42).darkened(0.1) (darker coloured core);
    `paper_print.gdshader` rim_mix 0.5 → 0.35 (less sticker outline).
  Metrics r3 v0-5 (settled, frame 170): lum .372-.453, p05 .111-.214, p95 .642-.670, sat .539-.638, warmth .256-.276,
  edge .043-.062, tiltshift 2.60-5.22 (v0 5.22, v1 4.04, v2 2.64, v3 3.46, v4 2.60, v5 4.31; r2 2.28-4.08).
  Tiltshift is above the 2-3.5 target on v0/v1/v5 on purpose: the r2 critic asked for more lens character; the crisp
  mid band of our prints inflates the ratio.
  Profile (meadow.tscn walking, 1366x1024, 6 s): Metal p95 8.8 ms (120 Hz cap), max 1355 draws; Vulkan p95 10.9 ms,
  4391 draws.
  Captures: `artifacts/world/int_r3/` (meadow_r3_v0..5 + meadow_r3_midwave_v0 at frame 52). ~4000-4200 cards per spread.
  Blind A/B: `artifacts/ab/INT_r3` (seed 3; refs v_01, 03, 04, 06, 12, 13).
  Open: atlas prints are low-res (~200 px), which limits mid-distance detail and can't be fixed without new art;
  no fold tabs at card bases (contact shadows only); no card bow (style rule); Vulkan draw calls ~4400 (region
  chunking still to do); tiltshift high on 3 views.
- 2026-11-18 INT round 4 (integrator). Answers the r3 critic. Our folk-print side won 5 of 6 pairs. It lost pair 2 to a
  vertical white seam through the foreground pine, a huge blurred foreground bush, and empty green fields. r3
  scripts are backed up in the session scratchpad (world_r3_backup). Only `core/world/meadow.gd` changed.
  Changes:
  - Seam: cross-slotted cards are off (`CROSS_POOLS` is empty and the catalog `cross_slot` flag is ignored). The
    slotted second card, seen edge-on, read as a pale vertical strip through every big tree. Trees are now single
    thick cards on contact shadows.
  - Lens foreground: 4 low cards (grass, flower, sapling) at the frame edges only (lateral 1.5-2.4). It was 6 cards
    of any pool, trees included. `_blocks_view` now also rejects any card taller than 0.22 in the near-lens band
    (t 0.4-0.85, within 1.4 of the line), so no big blurred bush covers the bottom third.
  - Empty fields: rejected open-felt sites get 1-3 low tufts (60%, was a single tuft at 30%). A new ground-cover
    pass adds 1800 tries of small grass and flower tufts (0.6-0.9 scale) everywhere except the hero clearing.
  - Back hills: the red/ochre field hill cards hills_clouds_10/14/19/22 are excluded (03 already was), because one
    filled the top of v4 with a flat salmon slab.
  - Lens: tilt_blur 0.66 → 0.58.
  Metrics r4 v0-5 (settled, frame 170): lum .379-.460, p05 .082-.242, p95 .651-.675, sat .555-.608, warmth .238-.284,
  edge .050-.066, tiltshift v0 3.72, v1 1.96, v2 1.94, v3 4.63, v4 2.31, v5 3.27 (r3 2.60-5.22). Mid-wave frame 52
  tiltshift 3.83. ~5400-5500 cards per spread (~700-760 hinged).
  Profile (meadow.tscn walking, 1366x1024, 6 s): Metal p95 9.9 ms (120 Hz cap), max 1454 draws; Vulkan p95 13.7 ms,
  4696 draws (r3 10.9 ms, 4391). The extra cost comes from the ground-cover pass.
  check_all: clean (30 scripts, 0 errors).
  Captures: `artifacts/world/int_r4/` (meadow_r4_v0..5 + meadow_r4_midwave_v0 at frame 52).
  Blind A/B: `artifacts/ab/INT_r4` (seed 4; refs v_01, 03, 04, 06, 12, 13).
  Open: atlas prints are still low-res (~200 px). There is no card bow (style rule) and no visible fold tabs. Vulkan
  draws are about 4700 (region chunking is still to do, and the cover pass could be cut for iPad). v3 tiltshift
  is 4.6, above the target.
