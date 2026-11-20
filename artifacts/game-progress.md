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
- 2026-11-18 lead: integration loop single-critic rates r1 0 / r2 0 / r3 0.17 / r4 0.83 (reference pick rate; lower =
  ours preferred). Loop exit was flawed (critic "impressed" meant the weaker side, which was often the reference).
  Re-judged INT_r3 and INT_r4 with 3 independent blind critics (art director / pop-up paper engineer / picture-book
  editor), scored against the key: r3 ref-pick avg 0.50, ours-impressed 0.39; r4 ref-pick avg 0.44, ours-impressed
  0.72. → r4 KEPT (the r4 single-critic 0.83 was noise). Pass bar (≤0.6 ref pick, majority impressed) met on average.
  Consistent dissent (paper-engineer lens, prefers reference 6/6): pieces don't read as engineered paper — add fold
  tabs/glue feet, slotted mechanisms (cross-slot without the edge-on seam), V-fold hills/rocks, tiered folded ground,
  slight lean; less empty lawn; traveller must stay the focal point. Future loops: ≥3 critics per round, impressed asked
  per side.
- 2026-11-18 PE round 1 (paper-engineering integrator, branch `pe-loop`, commit 9b79a0a, from INT_r4). Answers the
  paper-engineer critic ("printed illustrations stood up, not a built pop-up").
  Changes:
  - Glue feet (`core/world/glue_feet.gd`, `glue_foot.gdshader`): every standing card >= 0.14 tall gets a single-ply
    tab of its own stock folded flat in front of its base. The width comes from the print's opaque base span and
    the colour from the bottom third of the print, skipping cream paper (`PaperCard.base_info`). The tab has a dark
    crease line at the fold and a print-tinted cut edge. Static cards >= 0.5 tall also get an easel strut behind.
    Two MultiMesh draws for the whole spread. Instance colours are converted sRGB -> linear in the shader; without
    that the tabs washed out to pale plaques.
  - Cross-slots are back (`CROSS_POOLS` conifer .45 / tree .35 / autumn .35 / blossom .3 / bush .25, h > 0.22).
    `PaperCard.slot` cuts real half-slots: A is notched from the top to mid height, B from the bottom, and the
    notch is one board thick, so the pair interlocks at the centre. Both faces are printed, and the cut edges are
    coloured from the print (`edge_from_print`). The pair is yawed to view-yaw +/-45 deg, so neither card is
    edge-on. `CrossCard` slides B into the slot as it opens. StaticCards batches the A and B cuts as their own groups.
  - V-folds: rock-pool cards are now two half-prints (`PaperCard.half`) folded 29-41 deg back about a centre crease
    that points at the lens, giving one lit face and one shadow face. Each half is shifted toward the crease so
    the two printed fronts meet on one fold line. Every third back-hill card is a shallow V-fold (0.34 rad).
  - Folded ground (`meadow_ground.gd`, `fold_riser.gdshader`): tier risers (now 6 mm) are folded stock: print colour
    darkened, with a cream cut-line lip at the top fold and a crease shadow at the foot. Before, they were cream
    slab walls. The bridge is now a box-pop: a thin deck card on two folded legs, open underneath so the water runs
    through, with a step-fold tread on each bank. New `add_box_pop` / `add_step_fold`: up to 4 step-fold / box-pop
    platforms dressed with hay or a fence plus flowers, and raised flower beds (box-pops with a soil top and
    flowers planted in rows).
  - Lawn: the r4 ground-cover pass is cut from 1800 to 600 tries, and rejected-site tufts from 60% to 35%. They are
    replaced by up to 64 purposeful clusters in open felt, away from the hero clearing and the lens line: fence runs
    across the view with flowers at the posts, hay groups, V-fold stone piles with pebbles and cairns, raised
    flower beds, and woodpiles with logs and mushrooms.
  - Draw calls: a card with a printed back now draws front and back in one surface (2 draws per print, was 3).
  - Lens: tilt_blur 0.58 -> 0.46.
  - Check rig: `scenes/world/cap/pe_closeup.tscn` plus `tools/world/capture_closeup.py`, which aims a free camera
    at the cross pair, V-fold or bed nearest the traveller.
  Metrics PE r1 v0-5 (settled, frame 170): lum .388-.440, p05 .076-.209, p95 .651-.670, sat .578-.612,
  warmth .259-.295, edge .054-.067, tiltshift v0 3.70, v1 3.27, v2 2.31, v3 2.92, v4 3.94, v5 4.77 (r4 3.72 / 1.96 /
  1.94 / 4.63 / 2.31 / 3.27). ~5260-5410 cards per spread (590-700 hinged).
  Profile (meadow.tscn walking, 1366x1024, 6 s): Metal p95 11.7 ms, 3629 draws; Vulkan p95 12.5 ms (GPU p95 ~12.2),
  3629 draws, 9.5M primitives, 0 hitches. The r4 baseline was re-measured in the same session: Metal 13.2 ms,
  Vulkan 13.9 ms, 4696 draws, 11.2M primitives.
  check_all: clean (32 scripts).
  Captures: `artifacts/world/pe_r1/` (meadow_pe1_v0..5, closeup_cross_slot, closeup_vfold_rock).
  Blind A/B: `artifacts/ab/PE_r1` (seed 11; refs v_01, 03, 04, 06, 12, 13).
  Open: tiltshift is above 3.5 on v0, v4 and v5 (v5 4.8; the crisp tabs raise mid-band sharpness and the thinner
  cover lowers it at the bottom). Tabs under small flowers can read as little plaques from far away. Hinged tall
  cards have no strut, because it would stand alone during the pop wave. Fence runs are rare in the 6 views.
  Box-pop beds and platforms are separate MeshInstances (~3 draws each).
- 2026-11-18 PE round 2 (paper-engineering integrator, branch `pe-loop`, commit afb7cbb). PE r1 scored worse than
  INT_r4 (ref-pick 0.83, ours impressed 0.06), so this round starts from INT_r4 (f6fe113) game/ + tools/ and takes
  back only r1's mechanisms (PaperCard slot/half cuts + merged print surface, CrossCard slide, StaticCards cut groups,
  GlueFeet, fold-riser shader, box-pop/step-fold builders).
  Diagnosis of r1: its new code used the shared layout RNG (cross dice, V-fold angles, clusters before the fill),
  and it changed ground heights (tier 6 mm, bridge deck +8.5 cm, step treads in surface_y). Heights feed the walk
  path length, so the traveller start moved and the r4 spread was reshuffled. Examples: a giant oak at the v0 lens
  and emptier lawns. The critics judged a different, weaker composition rather than the engineering.
  Changes (the r4 layout is card-for-card identical; verified by re-rendering r4 v0 from a worktree):
  - The cross-slot choice (conifer .6 / tree .4 / autumn .35 / blossom .3 / bush .22, h > 0.22) and the V-fold
    rock angle come from a site hash (`_hash01`), not the RNG. The cross and rock yaw overrides are applied after
    the RNG draw.
  - Ground heights are back to r4: tier 5 mm with the folded-riser look, the box-pop bridge deck at +3 cm, and the
    step treads are not registered in surface_y.
  - Glue feet only on cards 0.2 tall or more (r1 0.14: tabs under flowers read as plaques). Tab depth is 7.5% of h.
    Struts behind static cards 0.5 tall or more.
  - Built lawn clusters (fence runs, hay groups, V-fold stone piles, raised box-pop flower beds, woodpiles), plus
    step-fold platforms. They run after `_meadow_fill` on a side RNG seed and the RNG state is restored afterwards.
    Three of four sites are drawn from the band each camera actually sees (fov 20: about ±1.6 wide at the
    traveller). They are kept out of the hero clearing (1.6), off the road and stream, and away from cards 0.16 or
    larger (`_free_big`). Each cluster clears the uniform tufts under its footprint (`StaticCards.clear_area`,
    `ContactShadows.clear_area`, hinged tufts freed and taken out of `WindSway`), so it replaces the tufts rather
    than piling on them. 40 clusters per spread.
  - tilt_blur stays at the r4 value of 0.58.
  Metrics PE r2 v0-5 (settled, frame 170): lum .379-.449, p05 .095-.227, p95 .650-.674, sat .562-.631,
  warmth .240-.318, edge .048-.069, tiltshift v0 3.46, v1 1.95, v2 1.99, v3 4.58, v4 2.58, v5 3.17 (r4 3.72 / 1.96 /
  1.94 / 4.63 / 2.31 / 3.27). ~6130-6240 cards per spread (710-780 hinged).
  Profile (meadow.tscn walking, 1366x1024, 6 s): Metal p95 9.75 ms, max 1682 draws. Vulkan p95 13.75 ms
  (GPU max 13.8), 3693 draws (r4 4696).
  check_all: clean (32 scripts).
  Captures: `artifacts/world/pe_r2/` (meadow_pe2_v0..5, closeup_cross_slot, closeup_vfold_rock).
  Blind A/B: `artifacts/ab/PE_r2` (seed 12; refs v_01, 03, 04, 06, 12, 13).
  Open:
  - v1 and v2 look almost the same as r4: their lawn bands are already full, so no cluster fits in them.
  - v3 tiltshift is 4.6 (same as r4).
  - Beds read as plain brown slabs from far away.
  - Hinged tall cards have no strut.
  - The material notes (grain, curl) and the path strip (cut edge, lift) from the r1 critics are still not done.
- 2026-11-18 PE round 3 (paper-engineering integrator, branch `pe-loop`, commit e53be11). PE r2 still scored below
  INT_r4 (avg ref-pick 0.61, paper engineer 0.83, ours impressed 0.22). As instructed, game/ and tools/ were first
  restored from INT_r4 (f6fe113). The round then builds on r2's mechanism code (afb7cbb), because that code keeps
  the r4 layout card for card, and changes what the r2 critics and my own comparison of r4 and r2 flagged. In the r2
  views, the hay bales read as CG cylinders, the woodpile as 3D logs, the raised beds as brown slabs, and every card
  still faced the lens like a billboard.
  Changes (`core/world/meadow.gd`, `core/paper_card.gd`, `core/shaders/paper_print.gdshader`; 22 lines):
  - Lawn clusters: hay groups, woodpiles and raised beds are gone. They are replaced by layered flower patches: a back
    row of 2 bush or sapling cards, a middle row of 3 flowers and a front row of 3 low tufts, so the cards overlap and
    give depth. Fence runs and V-fold stone piles stay. Step-fold platforms are dressed with bush, flower and sapling
    instead of hay. Clusters still run on the side RNG, so the r4 layout is unchanged.
  - Cards turned off the print plane: low wide pools (hedge .6, fence .45, bush .4, mushroom .45, prop .35,
    bank .4, crop .35 rad) get an extra yaw from a site hash (`_hash01(q, 31)`). The layout RNG is not touched. Their
    cut edges and feet now show in perspective instead of every card facing the lens.
  - Tall static cards (0.5 or taller, not cross or V-fold, not hills) lean back about 3° onto their easel strut.
  - Glue-foot depth goes from 7.5% to 10% of the card height (clamp 0.03-0.07), so the tabs read at view distance.
  - Cut edge: the side-wall core is lighter (`edge.lerp(avg, 0.32)`, no longer darkened). The die-cut rim band is
    stronger (rim_width 0.0024 -> 0.003, rim_mix 0.35 -> 0.48). All three critics asked for a visible light cut-edge
    band in r1 and again in r2.
  - Kept from r2: half-slot cross trees (no seam), V-fold rocks and ridge hills, folded tier risers at r4 heights, the
    box-pop bridge, glue feet and struts, the hero clearing, and tilt_blur 0.58.
  Metrics PE r3 v0-5 (settled, frame 170): lum .384-.449, p05 .096-.225, p95 .651-.675, sat .559-.624,
  warmth .239-.311, edge .051-.071, tiltshift v0 3.65, v1 2.02, v2 1.95, v3 4.41, v4 2.63, v5 3.30 (r4 3.72 / 1.96 /
  1.94 / 4.63 / 2.31 / 3.27). About 6170-6290 cards per spread (720-810 hinged).
  Profile (meadow.tscn walking, 1366x1024, 6 s): Metal p95 10.45 ms, max 1733 draws, 0 hitches. Vulkan p95 14.48 ms
  (GPU p95 14.48), 3778 draws (r4 4696), 0 hitches.
  check_all: clean (32 scripts).
  Captures: `artifacts/world/pe_r3/` (meadow_pe3_v0..5, closeup_cross_slot, closeup_vfold_rock).
  Blind A/B: `artifacts/ab/PE_r3` (seed 13; refs v_01, 03, 04, 06, 12, 13).
  Open:
  - v3 tiltshift is still 4.4.
  - The stronger rim shows as a light outline on close-ups. Revert rim_mix if critics call it a sticker halo again.
  - Hinged tall cards still have no strut.
  - The cards have no curl (style rule).
  - Vulkan p95 is 0.8 ms above r4.
- 2026-11-18 lead: paper-engineering loop PE r1-r3 (branch `pe-loop`, commits 9b79a0a / afb7cbb / e53be11, NOT merged).
  3 blind critics per round vs the reference: avg ref-pick r1 0.83 / r2 0.61 / r3 0.83; paper-engineer 1.0 / 0.83 / 1.0;
  ours-impressed 0.06 / 0.22 / 0.00 (INT_r4 baseline 0.44 / 1.0 / 0.72, judged in an earlier session).
  Blind head-to-head INT_r4 vs PE_r2 at the same 6 camera stations (3 critics, sheets artifacts/ab/H2H_r4_pe2): PE_r2
  picked 0.50 / 0.33 / 0.17 (avg 0.33) → INT_r4 KEPT on main. Critics: hay bales, raised beds and woodpiles read as dropped-in
  3D props and clutter; cross-slot trees read as doubled/ghosted silhouettes at this camera; differences otherwise slight.
  Lesson: the gap to the reference is not mechanisms. Every critic cites lens and light: the reference reads as a
  photographed tabletop (lower camera, strong shallow DOF, contrasty low light, textured felt ground, dense tree rows),
  ours as crisp, evenly lit vector cards on a flat lawn. Worth keeping from pe-loop if revisited: merged print surfaces
  (Vulkan draws 4696 → 3629), glue feet. Next loop should target camera/lens/light/ground texture, not new props.
- 2026-11-18 cast library (new pop-up characters for 「해와 바람」; owner of `game/art/cast/**`, `art_src/cast/**`,
  `tools/cast/**`). User decision: characters are made new; the 톡톡 art in `game/art/chars/` is a design reference only.
  Generation: 4 magenta sheets through `tools/run_jobs.py tools/cast/cast_jobs.json` (prompts in `tools/cast/make_jobs.py`,
  same style block as the atlas sheets, no refs). Raw outputs in `art_src/cast/raw/`; md5 checked, unique against each
  other and all 16 atlas raws. All 4 sheets accepted on the first pass (no extra limbs, the wind faces left, no halo).
  They were sliced with `tools/atlas/slice_atlas.py --out art_src/cast/sliced` (16 sprites, 0 halo px).
  `tools/cast/build_cast.py` copies them to `game/art/cast/<id>.webp` and writes `game/art/cast/catalog.json`
  (category "cast", role, variant, tags, height_units, hanging, parts).
  Cast ids (16):
  - Traveller, generic and rigged (skin "traveller", parts in `game/art/cast/rig/`): cast_traveller_coat (0.36),
    cast_traveller_coat_nohat, cast_traveller_coat_hold (clutching the coat), cast_traveller_nocoat (shirt, suspenders,
    hat; the ending), cast_traveller_nocoat_nohat.
  - Clothes cards: cast_coat_hung, cast_coat_folded (in hand), cast_coat_ground, cast_hat, cast_hat_ground.
  - Sky (hanging): cast_sun_smile, cast_sun_proud, cast_sun_beaming; cast_wind_boast, cast_wind_blow, cast_wind_tired.
  Rig: `tools/cast/cut_cast_rig.py` cuts figures without a colour classifier. It takes the split from the gap between
  the feet and the crotch from the top of that gap. Legs are the bottom-touching components, trimmed where they widen
  into the coat hem. Leg tops are repainted in a flat trouser colour, tapered. A hips piece and brads are added. Output
  is `game/art/cast/rig/rig.json` in the chars_rig format.
  First capture bug: the soft alpha of the leg outline stayed in the body PNG. The body card was then stretched to full
  height, so the figure looked sunk into the ground. Fixed by giving the leg its 3 px soft rim and clearing faint body
  pixels below the crotch. QA: `art_src/cast/qa/cast_contact.png`, `rig_preview.png`.
  Walk-rig skin: new `CastPuppet extends PaperPuppet` (`game/art/cast/rig/cast_puppet.gd`), with `@export skin`
  ("traveller"; "" = legacy art). It uses the same pose names (walk, walk_nohat, hold, shirt; fan and sit map to
  nocoat_nohat), so story code is unchanged. `core/characters/paper_puppet.gd` is NOT modified, so the old puppet and
  the old bench are unchanged.
  Benches (mine): `art/cast/bench/cast_closeup{,_shirt}.tscn`, `cast_walk_bench.tscn` (extends walk_bench, with cast
  puppet, sun and wind, and expression swaps on the demo timeline), `cast_lineup.tscn`.
  Captures: `artifacts/cast/` (cast_closeup_walk, cast_closeup_shirt, cast_walk_bench 12 frames at 1366x1024,
  cast_lineup.png). The walk reads as a paper toy, the hold pose reads in the bench, and the cards key cleanly.
  check_all clean (36 scripts).
  Open:
  - No-coat figures: the trouser seat is part of the body card and has a straight bottom cut (it reads like
    lederhosen). The hips piece corner can show for a frame on wide swings.
  - The figures have no fan or sit art (they fall back to the shirt figure).
  - Lead: to make cast the default, swap `PaperPuppet.new()` for `CastPuppet.new()` in story or bench code (D's files),
    and point sun and wind at the cast ids.
- 2026-11-18 E story flow round 1 (component E, not committed). The whole 「해와 바람」 now plays start to end as a pop-up
  book. Main scene: `res://stories/sun_wind/story.tscn` (StoryRunner).
  - Script: `game/stories/sun_wind/script.json`, seeded by `tools/story/seed_script.py` from 톡톡's voice_script_el.json.
    It keeps the voices/models/settings tables. Per line: id, speaker, text, segs (emotion, tags, audio, source_audio,
    status), beat, interaction, used. Clip mapping is parsed from 톡톡's `tales/sun_wind/narration_el.js`: full line
    text -> one clip per seg, in seg order; extras come from VOICE_LINES. 55 MP3 clips were copied to
    `game/audio/voice/sun_wind/`. They stay MP3, since Godot imports MP3 natively. 54 lines are used: 48 reuse,
    6 changed-needs-recording.
    - Changed: sw_013/014/015, where the tap became a press-and-hold to blow ("꾹").
    - New: sw_n01 (cover), sw_n02 (ending walk), sw_n03 ("다시 보기").
    - Dropped (used=false): the clothes quiz 42-50, weather play 58-59, and 37/38, cut_pant, wrong_hot.
    - The stream rest now comes before the moral.
  - Runner (`game/story/`):
    - story_runner: beats -> spreads, step kinds say/walk/walk_to/pose/tap/blow/shine/quiz/gentle/fx/end/cover.
    - spread_stage: builds meadow.tscn by seed + view with its look untouched. It snaps the template's load wave and
      pops the spread after the page turn. It adds the sun and wind as SkyHanger cards on PopHinges inside the hero
      clearing, and hides hinged cards that block their sightline (4-6 per spread). It also handles the hat flight,
      the coat drop, leaf cards, gust sway, and warm key light + sun lamp.
    - page_turn: snapshot curl; the next spread is built under it.
    - story_ui: cover, paper caption strip with speaker chip, subtitle toggle, page tab, tap pointer + hold ring,
      ripples, and the end card with 다시 보기 (Pretendard font, OFL, in story/fonts).
    - cast_skins: looks up a cast id + variant in res://art/cast/catalog.json and falls back to the art/chars
      placeholders. The traveller is still D's PaperPuppet.
  - Spreads: cover -> sky v5 -> bet+wind_turn v0 -> sun_turn v1 -> stream v2 -> moral v3 -> ending v4. Each is the same
    seed-1 meadow, further along the road.
  - Verify mode: `-- --beat=<id> --autoplay --fixed --mute --nosubs`, or `--agent-args {"beat","autoplay","fixed",
    "mute"}`. `stories/sun_wind/cap/story_autoplay.tscn` sets autoplay + fixed + mute. Autoplay simulates the taps
    and holds, and in the quiz it taps the wrong answer once.
  - Autoplay total: 246.8 s of story time. Beat starts: sky 3.6, bet 33.0, wind 46.9, sun 101.3, stream 152.3,
    moral 185.2, ending 222.5 s. Missing audio: sw_013, sw_014, sw_015, sw_n01, sw_n02, sw_n03. Those lines are
    timed from their text.
  - Profile, busiest beat (wind_turn: pop wave + held blowing, 16 s, 1366x1024 Metal): p95 10.68 ms, p99 15.3 ms,
    1 hitch, max 1519 draws.
  - check_all: clean (39 scripts).
  - Captures: `artifacts/story/sun_wind_r1/` (60 frames, one every 250 frames = 4.2 s) and the contact sheet
    `artifacts/story/sun_wind_r1_sheet.jpg`.
  - Open:
    - The 6 changed lines need recording with the same voice ids.
    - The end card was widened after the capture (the moral wrapped "세\n요").
    - The traveller is small at the template camera (~60 px), so tapping him only gives a little reaction.
    - Hidden sightline cards leave their contact-shadow blobs on the ground.
    - The new cast library is not wired into PaperPuppet yet. The cast_skins hook covers sun, wind, hat and coat
      only.
    - Each page turn rebuilds the meadow, a 1-2 s hitch hidden under the snapshot.
- 2026-11-18 E story flow round 2 (fix round after 3 critics 5.5/5/5, not committed). Sheet:
  `artifacts/story/sun_wind_r2_sheet.jpg` (66 frames, one every 210 frames = 3.5 s, `artifacts/story/sun_wind_r2/`,
  with the run log `story_log.txt`). Autoplay total 224.1 s (r1 246.8). Beat starts: sky 3.5, bet 31.6,
  wind_turn 46.6, sun_turn 99.1, moral 144.0, stream 170.4, ending 202.7. Missing audio: none.
  - Voice: the 6 changed lines and a new sw_n04 ("나그네를 톡 눌러 볼까요?") were recorded with ElevenLabs. They use 톡톡's
    voice ids, models and settings, the same hash naming, and 톡톡's polish chain (log=False). The tool is
    `tools/story/record_lines.py`; the manifest is `game/audio/voice/sun_wind/recorded.json`. The seed fills them
    in as status "changed-recorded". Unused clip copies were removed (51 clips are in use).
  - Script (seed_script.py BEATS): sw_007, sw_039 (it gave the answer away), sw_061 (the moral said twice) and
    sw_x_cut_off are dropped.
    - The recap and quiz now come right after the coat comes off, on the same page (no page turn). Two paper-photo
      flashbacks are kept from the page itself during sw_034/035: the cold picture is taken at the end of the
      blowing, the warm one after the coat comes off.
    - The quiz uses two big bobbing picture cards. A wrong tap shakes the card, a cold gust blows and he shivers,
      and the child tries again. The right card grows and sparkles.
    - The bet beat now has a tap on the traveller (he hops). The hold to blow needs 3.0 s, down from 4.2.
  - Stage: the story camera shots work on the template rig: wide for the page pop, story at 3.3, and close at 2.85
    only on coat-off. The template's look and layout are unchanged.
    - The traveller is the cast library's CastPuppet, scaled to 0.47, about 25% of the frame height.
    - The sun and wind are cast cards (smile/proud/beaming, boast/blow/tired). They hang on strings in the top band
      of the story shot (laid out by project_position), on cream and pale-blue paper discs, and follow the
      traveller. They drop in when the page opens. For "friends" they slide together and turn toward each other.
    - The hat flies up and off the page, then flutters back down. Fanning shows the hat in his hand.
    - The coat drops to the ground, then he carries it on his arm (cast_coat_folded) to the end.
    - At the stream he leaves the road to the bank and stands in the water to the knees, with paper ring ripples and
      splash drops.
    - At the end the camera stops following and he walks off down the road.
    - The traveller pops with the page wave and folds with it. The new page lies flat under the page turn and rises
      after it lands. The contact-shadow blobs of hidden sightline cards are hidden too.
  - UI: the caption is 48 px in one ink colour, and the speaker chip has a face icon. Korean lines break between
    words only (a word joiner between letters). The toggle reads 자막 켜짐/꺼짐.
    - The tap ring goes around the whole card with the finger tab under it, and the wind's cheeks puff while held.
    - The end card shows sun and wind, "끝" and 다시 보기, with no moral text.
  - Profile, wind_turn (pop wave + held blowing, 16 s, 1366x1024 Metal, windowed): p95 10.1 ms, p99 14.3 ms,
    max 20.5 ms, 0 frames over 33 ms, max 1524 draws.
  - check_all: clean.
  - Open:
    - 224 s is still over the critics' ~3 min target.
    - There is no sit art (he wades standing).
    - The audio sync and the new recordings were not checked by ear.
    - Not yet tested on an iPad.

## 2026-11-18 Sun and wind cast cards regenerated without botanical prints
- The user asked why the sun and wind had leaf prints. Their prompts reused the shared STYLE block ("tiny repeated flower
  and leaf motifs"). `tools/cast/make_jobs.py` now has a SKY_STYLE (no green, no flowers/leaves/petals/plants/vines plus an
  explicit negative) for new jobs `cast_sun_v2` and `cast_wind_v2`. Sun detail is now stamped dots, dash lines, a scalloped
  dashed ring and radiating ticks. Wind detail is now stitched swirls, wavy air streaks and dots, and it still blows LEFT.
  The traveller jobs are unchanged.
- Raws: `art_src/cast/raw/cast_{sun,wind}_v2.png` (originals kept), sliced to `art_src/cast/sliced/cast_{sun,wind}_v2/`,
  `build_cast.py` sources the v2 sheets into the same ids (`game/art/cast/cast_sun_*`, `cast_wind_*`), catalog rebuilt, halo 0.
  Codex said FAILED only because the size was not 1536x1024 (it returns 2172x724), so the v2 jobs now accept any wide size.
- QA: `art_src/cast/qa/cast_contact.png`; the story frame (wind_turn, autoplay, 13 s) is `artifacts/cast/sun_wind_v2_story.png`.
  Import and check_all are clean.
- 2026-11-18 LOOKF round 1 (look pass, worktree `/Users/house_of_4k2b/orca/popup-atlas-look`, branch `look-fable`,
  commit 4df8cde, from INT_r4 on main b17a12c). Goal: the photographed-miniature look, with no new prop types.
  Changes:
  - Lens (`meadow.gd` VIEWS + rig): elevation 21-23° → 15-17° at the same 6 road stations, yaw, distance and fov.
    DOF is a thin slab around the traveller (near margin 0.7, far 1.1, amount 0.07 → 0.12), tilt_blur 0.5, plus a
    little global lens softness (0.14), sensor grain (0.035) and a shadow toe in `post_grade.gdshader`.
  - Light: key elevation 34° → 25°, yaw -60° → -70°, energy 2.05 → 2.7; fill 0.55 → 0.34; ambient 0.46 → 0.37;
    shadow opacity 0.8 → 0.93, softness 1.4 → 1.0; contact shadows 1.25x and darker; vignette 0.24. A small
    unshadowed warm omni ("HeroBounce") rides with the traveller so a long tree shadow never buries him.
  - Ground: `ground_layer.gdshader` fibre layers at unrelated angles warped by the mottling, plus a mid-scale wool
    clump term (`clump_strength`) on felt, tiers, cover patches and road; bump 0.9 → 1.5-1.6. Felt 7d9366 / 556b45.
    The blue-green cover patch is greener (it read as puddles).
  - Road: width 0.5 → 0.38, colour d9bf8a → c9ae7c.
  - Trees: new `_tree_rows()` places 40 rows of 5-9 mid-height trees (existing conifer/tree/autumn/blossom pools)
    with bush skirts. POOL_SCALE conifer 1.5 → 1.25, tree 1.25 → 1.08, autumn 1.05, blossom 1.02.
  - Lens keep-out: `_blocks_view` also rejects any card that rises into the camera-to-traveller sightline.
  - Back rows: ochre/orange hill cards 00, 02, 05, 07, 08, 09, 13, 24 excluded too; haze dcc49a → b4bd9c, 0.72.
  - Budget trades: ground-cover pass 1800 → 1150 tries; `pop_radius` 4.2 → 3.85 (fewer hinged cards = fewer draws).
  Metrics v0-5 (settled, frame 170): lum .341-.455, p05 .040-.189, p95 .595-.706, sat .573-.632, warmth .219-.317,
  edge .046-.066, tiltshift 2.25-3.14. ~5320-5490 cards per spread (493-630 hinged).
  Profile (meadow.tscn walking, 1366x1024, 6 s): Metal p95 10.56 ms, 1559 draws (INT_r4 re-measured in the same
  session: 9.86 ms, 1454). Vulkan p95 14.19 ms (GPU max 14.28), 5069 draws (INT_r4 13.79 ms, 4696): +3 % time,
  +8 % draws. Draw count swings about ±5 % with how many hinged cards the seed puts near the traveller.
  check_all: clean (30 scripts).
  Captures: `artifacts/world/look_f1/v0..v5.png`. Blind A/B: `artifacts/ab/LOOKF_r1` (seed 21; refs v_01, 03, 04,
  06, 12, 13). Head-to-head vs INT_r4: `artifacts/ab/H2HF_r1` (seed 21). Not judged yet.
  Open: the felt nap still shows a faint regular rib at mid distance; v1 p05 is 0.04 (dark conifers in shadow,
  below the reference 0.09); warmth and saturation sit at the top of the reference range; v0 has one large blurred
  pine in the near foreground; the story agent's spreads will inherit the narrower road and smaller pop radius.
- 2026-11-18 LOOKF round 2 (look pass, worktree `/Users/house_of_4k2b/orca/popup-atlas-look`, branch `look-fable`,
  commit 88fa45b; main merged in first, so the branch carries the story-flow commits). r1 was rejected head-to-head
  (0.39): critics liked its lower lens, tree layers and warm light, and disliked the blurred foreground clutter,
  foggy backdrop, overall softness and the small hero. r2 restarts the look values from INT_r4 and keeps it crisp.
  Changes (no new prop types):
  - Lens (`meadow.gd` VIEWS + rig): elevation 21-23° → 18-19.5°, distance 7.2-7.6 → 6.8-7.0 (traveller ~8 % larger),
    same stations, yaw and fov. DOF is a wide sharp slab (near margin 1.6, far 1.5, amount 0.075): blur falls on the
    far rows only. tilt_blur 0.58 → 0.36. No global lens softness, no grain. Shadow toe 0.2, contrast 1.06.
  - Light: key elevation 34° → 28°, yaw -60° → -66°, energy 2.05 → 2.5, colour ffdcb2; fill 88a6dc at 0.46; ambient
    0.43; shadow opacity 0.9; contact shadows 1.2x. The warm unshadowed "HeroBounce" omni rides with the traveller.
  - Shadow acne: the regular diagonal rib on the ground (r1 open issue, also faint in INT_r4) was shadow-map acne
    under the raking key, not the felt. Key `shadow_bias` 0.02 → 0.08 in `look_rig.gd` removes it.
  - Ground: r1's matted-wool shader kept (clump term), retuned: felt fibre 0.4 / grain 0.42 / clump 0.8, tiers
    0.36 / 0.4 / 0.75, road 0.14 / 0.2. Felt 7e9567 / 586e48. Road width 0.5 → 0.44, colour d9bf8a → d2b684.
  - Trees: `_tree_rows()` (44 tries, single-family rows of 5-9 mid-height trees) only beside and behind the
    traveller, never on the camera side. POOL_SCALE conifer 1.5 → 1.32, tree 1.25 → 1.1, autumn 1.08, blossom 1.05
    (the lower lens cropped the giants to trunks).
  - Lens keep-out (`_blocks_view`): cards over 0.3 are kept out of the band in front of the traveller, trees over
    0.5 out of everything nearer than him within 1.7, and nothing rises into the sightline.
  - Back rows: `hill_layer_terracotta`, `hills_clouds_24`, `hills_clouds_26` excluded (red slab, giant flowers);
    warm haze e0c69a at 0.5 (was dcc49a 0.62), begins 1.6 past the focus.
  Metrics v0-5 (settled, frame 170): lum .413-.464, p05 .098-.194, p95 .703-.735, sat .585-.654, warmth .269-.314,
  edge .085-.123 (v0 .123 and v1 .106 near/above the .11 top), tiltshift 1.83-3.05. 5545-5801 cards per spread
  (660-812 hinged).
  Profile (meadow.tscn walking, 1366x1024, 6 s): Metal p95 10.66 ms, 1572 draws. Vulkan p95 14.62 ms (GPU max
  14.73), 5061 draws: +6.7 % time and +7.8 % draws over INT_r4 (13.7 ms, 4696), inside the 10 % limit.
  check_all: clean (39 scripts).
  Captures: `artifacts/world/look_f2/v0..v5.png`. Blind A/B: `artifacts/ab/LOOKF_r2` (seed 22; refs v_01, 03, 04,
  06, 12, 13). Head-to-head vs INT_r4: `artifacts/ab/H2HF_r2` (seed 22). Not judged yet.
  Open: v4's back hill dome sits large behind the road; v0 is the busiest frame; draws are 2 % under the limit and
  swing about ±5 % with the seed; the narrower road, smaller trees and shadow bias are template defaults that the
  story spreads inherit on merge.
- 2026-11-18 LOOKF round 3 (look pass, worktree `/Users/house_of_4k2b/orca/popup-atlas-look`, branch `look-fable`,
  commit 2fa03ab, on top of r2 88fa45b). r2 was kept (head-to-head 0.89) but its blind A/B vs the reference got
  worse (ref-pick 0.56, impressed 0.33): critics called our cards flat digital decals, everything equally sharp,
  and the lower half empty lawn. r3 keeps r2's composition and light and adds physical paper and a graded lens.
  Changes (no new prop types):
  - Lens (`meadow.gd` VIEWS + rig): distance 6.8-7.0 → 6.5-6.6 at the same stations, elevation, yaw and fov
    (traveller ~6 % larger, less lawn in frame). DOF: near margin 1.6 → 1.25, far margin 1.5 → 1.15, far
    transition 3.4 → 2.8, amount 0.075 → 0.09, tilt_blur 0.36 → 0.5: the far rows melt clearly, the traveller's
    band stays crisp, the nearest strip softens only slightly. Still no global softness or grain.
  - Paper: card thickness 4 % → 5 % of height (min 0.014, max 0.05; `meadow.gd`, `static_cards.gd`); cut-edge core
    paler (`paper_card.gd` lerp to print colour 0.42 → 0.24, no darkening; `paper_edge` brightness 1.08 → 1.16);
    die-cut rim 0.0024 → 0.0032 wide, mix 0.35 → 0.5; print tooth `fibre_strength` 0.16 → 0.3 plus a broad
    ink-blotch term in `paper_print.gdshader`.
  - Hand-set cards: lean ±0.04 → ±0.065 rad, tilt -0.03..0.02 → -0.075..0.015 (most lean back a touch).
  - Foreground: `_lens_foreground()` adds up to 56 clumps of 3-6 low cover cards (all under 0.3 tall) in the
    meadow in front of and beside the traveller, so the lower half is a dense bed with no tall blurred card.
  - Budget trades: new `_hinge_r` override; the tiny ground-cover tufts are hinged only within 1.8 of the
    traveller and the new foreground bed within 2.6 (the rest are static MultiMesh); tuft pass 1800 → 1500 tries.
  Metrics v0-5 (settled, frame 170): lum .434-.493, p05 .119-.208, p95 .715-.760, sat .572-.630, warmth .281-.335,
  edge .092-.126 (v0 .115, v4 .126, v5 .116 above the .11 reference top), tiltshift 2.61-3.18 (above the 1.3-2.5
  reference range, inside the 2-3.5 brief target). 5590-5847 cards per spread (693-767 hinged).
  Profile (meadow.tscn walking, 1366x1024, 6 s): Vulkan p95 14.48 ms (max 14.65), 4957 draws max (4614 mean):
  +5.7 % time and +5.6 % draws over INT_r4 (13.7 ms, 4696), inside the 10 % limit; r2 re-measured in the same
  session: 14.62 ms, 5061. Metal p95 13.96 ms, 4957 draws. Metal now reports the same draw count as Vulkan and a
  higher frame time than the r2 log entry (10.66 ms, 1572); r2 was not re-measured on Metal this session, so the
  Metal numbers are not comparable to earlier entries.
  check_all: clean (39 scripts).
  Captures: `artifacts/world/look_f3/v0..v5.png`. Blind A/B: `artifacts/ab/LOOKF_r3` (seed 23; refs v_01, 03, 04,
  06, 12, 13). Head-to-head vs r2 (`look_f2`): `artifacts/ab/H2HF_r3` (seed 23). Not judged yet.
  Open: edge density is above the reference top in three views; v3 keeps a bare lawn patch on the right bank and
  a cropped cypress/oak pair at the right edge; the paper_print / paper_edge / thickness changes are shared
  defaults, so every card in the story spreads inherits them on merge.
- 2026-11-18 lead: Fable look loop LOOKF r1-r3 (branch look-fable, worktree ../popup-atlas-look). Scores (3 critics each):
  r1 vs-ref 0.28 / impressed 0.94 / h2h vs INT_r4 0.39; r2 0.56 / 0.33 / 0.89; r3 0.33 / 0.67 / 0.17 (vs r2).
  Signals conflicted (h2h critics prefer crisp clarity, vs-reference critics prefer the photographed miniature).
  USER chose Fable r1 → cherry-picked onto main (4f79cb0) + r2's shadow-acne fix (key shadow_bias 0.02 → 0.08).
  Story verified with the new template (wind_turn beat recorded, artifacts/video/sun_wind_wind_turn_v2.mp4).
  Note: --write-movie runs on this Mac crop the frame edges slightly (page tab / 자막 button cut); capture_scene and
  the r2 sheet show them in place, so it is a capture-window artefact, not a layout bug.
- 2026-11-18 traveller expressions + walking through the weather (cast/story owner; not committed). User: "걷는 거 제대로
  구현되는지? 나그네 오들오들 떨고 놀라고 … 계속 웃고만 있는 건 아닌지" + coordinator: he keeps walking on the road
  while the wind blows and the sun shines.
  - Art: 2 new Codex sheets (`tools/cast/make_jobs.py` jobs cast_traveller_expr_a/b, the old cast_traveller sheet as
    reference image, magenta key; raws `art_src/cast/raw/cast_traveller_expr_{a,b}.png`, md5 fca11b48…/805b6c4c…, fresh;
    old raws kept). Both accepted on the first pass (same face/coat/hat, no extra limbs, halo 0). 10 new rigged cast
    ids (catalog 16 → 26): cast_traveller_coat_surprised, _coat_nohat_surprised, _coat_nohat_cold (hugging himself,
    chattering teeth, icy blue cheeks, drip), _coat_calm, _coat_nohat_calm (neutral walking face), _coat_open_hot
    (unbuttoned, flushed, sweat drops, panting), _coat_open_fan (hat in hand, tongue out), _nocoat_relieved,
    _nocoat_nohat_relieved (eyes closed, content), _nocoat_calm. build_cast drops free-floating print bits (motion
    lines). cut_cast_rig gained ARM_PARTS: the fan figure's hat+hand is cut (polygon) into a hinged "fan" part.
  - CastPuppet (`game/art/cast/rig/cast_puppet.gd`): new pose names (walk_calm, walk_calm_nohat, surprised,
    surprised_nohat, cold, warm, hot_fan, relieved, relieved_nohat, shirt_calm; set_pose override accepts them);
    `shiver` (body card rocks ~12 Hz, ±3.4° about the hip brads, shoulder/teeth-chatter bob, hunch; legs stay planted;
    fast attack, ~1 s decay); `push_lean_deg` (lean into the wind at slow speed, solved through the base gait);
    hinged arm part animation (fanning flicks outward only, away from the face); `plant_exact` re-aims each leg with the
    exact shortest rotation to its footprint.
  - Story: new steps `stroll` / `stop` and per-spread `route` (script.json spread.route, offsets from the template
    start; sightlines cleared along the whole stretch, stroll clamped to it). bet + wind_turn route [-1.6, 3.6], he walks
    on through both beats (0.13 → 0.10, ×0.45 while the wind is held, leaning in 7°); sun_turn/moral route [-1.4, 1.8]
    (slows as he heats up, stops for the coat-off, picks the coat up (`walk_on`) and walks on, stops at the end).
    Expressions: walk/bet/sky/sun start → walk_calm; hat_off → surprised_nohat + startle hop + 2.2 s stop; flap → cold
    (shiver 0.7); clutch "으으, 추워!" → cold, shiver 1.3 (was the hold figure, which wrongly put the hat back on);
    gale → shiver 1.6 + shoved back half a step (no turn-around); wind_tired → shiver decays (0.25 for 3 s, then 0);
    hat_back → walk_calm; warm1 → warm; warm2 → hot_fan; coat_off → relieved; walk_on → shirt_calm; stream approach
    shirt_calm, at the bank relieved (keeps the hat: the old "sit" pose swapped to the no-hat figure = the hat flicker);
    ending keeps the smiling shirt figure ("다시 즐겁게 길을 떠나요"). Gust curls now aim over his head (they covered his
    face). The old ±6 mm random puppet jitter is gone (it also fed the gait's speed measurement).
  - Walk check (headless probe, story puppet, views 0/1, speeds 0.05-0.2): planted footprints never drift; sole vs
    footprint error ≤ 3.8 mm (≈2 px at the story camera) with plant_exact (was up to 32 mm on clamped frames).
  - Recordings (movie maker 1366x1024, 30 fps): `artifacts/video/trav_wind.mp4`, `trav_sun.mp4`, `trav_stream.mp4`;
    story-camera expression strip `artifacts/cast/trav_expressions_story.png`; contact `art_src/cast/qa/cast_contact.png`,
    rig `art_src/cast/qa/rig_preview.png`. Beat lengths unchanged (wind 55 s, sun 45 s; walking runs under the lines).
  - check_all clean (39 scripts).
  - Open: the warm grade washes the hot/fan flush toward pink at full warmth; the open-coat figures show a light notch
    at the crotch under the coat opening; --beat=wind_turn starts him at the route start (in the full flow he arrives
    from bet).
- 2026-11-18 traveller walks TOWARD the reader + front-facing step gait (cast/story owner; not committed). User on
  trav_wind/trav_sun: "뒤로 걷는 게 아니라 앞으로 걸어야 하지 않을까? 그리고 걷는 거 이상한데 괜찮니?" Lead decision:
  keep the front-facing figures (faces carry the story) and make him walk toward the camera.
  - Route (script.json): seed 1's road runs from the far edge (+Z offsets high) toward the camera side, so walking
    toward the camera = decreasing offset. bet/wind_turn route [-1.6, 3.6] → [2.8, -2.4]; sun_turn/moral [-1.4, 1.8] →
    [1.6, -1.6] (he comes over the bridge toward us); sky walk 0.4 → 0.6 (now toward us); stream view 2 → view 3 with
    route [0.5, -0.3] (he starts beyond the water and walks toward the camera to the camera-side bank); ending
    walk_away 1.6 → 3.2: the camera stops and he walks down the road toward the reader and out of the bottom of the
    frame (no back-view art exists, so he never walks away from the camera).
  - Road camera (spread_stage.gd `road_cam`): the rig yaw follows the road heading at his position (7-sample average
    from 0.3 behind to 1.2 ahead, clamped ±38° because every meadow card faces +Z; eased 0.9/s + 1.6/s), so the
    story camera stands ahead of him on the road looking back along it and the follow focus dollies it back as he
    comes on. `_stroll_dir` = road sign toward the camera side (`_toward_cam_sign`) when no route; walk_by(dist)
    walks along it. Sun / wind layout offsets are turned with the yaw (`_sky_rel`, anchors re-faced) so they keep
    their screen spots. Sightline clearing runs per stop with that stop's road yaw, and now also (a) hides any hinged
    card within 0.9 + half width of the camera on the ground (first full run: the camera backed through a big tree
    card at the end of the wind route = whole frame of blurred leaf) and (b) runs the same tests on the template's
    static MultiMesh cards (`_clear_statics_here`, collapsed instances) since the camera now travels past the pop
    radius. Log: hidden hinged/static per spread 34/4, 179/90, 95/53, 62/15, 38/3.
  - Gait (cast_puppet.gd `front_gait`, off by default so benches keep the base gait; the story turns it on): the
    base still owns phase, footprints, stepping SFX; `_front_step` rewrites body + legs in the unscaled turn frame:
    whole figure rolls (4°, 6° struggling) about the STANCE SOLE (legs stay parallel, no splay), hips solved so the
    straight stance leg reaches its print + a 0.009×scale bob on passing (the stance leg drops out from under the coat
    up to 16 % so the sole stays exactly on its print: headless probe stance sole y constant 0.032 through the stance,
    screen x drift ≤ 1 px), swing leg lifts (slides up behind the coat 70 % + shortens 30 %, a bent knee from the
    front), peak lift ≈ 0.06 world ≈ 25 px, and comes down ahead (toward the camera). Story puppet: step_period 0.46,
    stride 0.05-0.13 (≈ 2 steps/s strolling, ≈ 1/s pushing into the wind), walker speed 0.36 → 0.26. Wind:
    front_lift 0.8 + roll 6° while blowing (struggling, heavier), lean/shiver/fan layered on top unchanged.
  - Story runner: `--quit-on-done` (with --autoplay) quits 2 s after STORY_DONE, for movie-maker recordings.
  - Checks: leg close-ups at 8 fps over 2 s `artifacts/cast/walk_legs_closeup.png` (top: bet stroll, alternate boots
    clearly lift while the other stays planted, body rolls; bottom: wind, slow low steps with lean + shiver), also
    _calm / _wind separately. Full unattended run (no --beat): STORY_DONE 242 s, all 8 beats, no errors.
  - Videos: `artifacts/video/walk_wind.mp4` (21 MB), `walk_sun.mp4` (14 MB) at 1366x1024 crf 26;
    `walk_full_story.mp4` (24 MB, 1024x768 crf 30). check_all clean (39 scripts).
  - Open: the road meanders, so on the bends he drifts toward one side of the frame for a few seconds while the yaw
    catches up (card turns ≤ 20° toward the drift, never walks away); walk_wind/walk_sun were recorded before the
    static-card clearing (those --beat runs never reach the occluding card; the full run includes the fix); the
    ending shows ~10 s of empty road after he exits (narration still running); the toward-camera stride itself is
    mostly read through the lift/roll/bob, since depth motion is small on screen at the 15° lens.

## 2026-11-18 — Front-view boots (user: "팔자걸음인딩?")
  - Cause: every traveller figure was drawn standing with SIDE-view boots, toes pointing outward, so the walk toward
    the reader read as a duck walk. Fix in the leg art, not the gait (front_gait already rolls the whole figure about
    the stance sole, no per-leg yaw/outward roll; the lift stays a bent knee seen from the front).
  - New sheet `art_src/cast/raw/cast_traveller_legs_front.png` (Codex, job `cast_traveller_legs_front` in
    tools/cast/make_jobs.py, refs = `ref_traveller_legs.png` crop of the current lower bodies + the traveller sheet;
    fresh md5): 4 single legs, front view, boot toe cap facing the viewer: coat trousers L/R (plain chocolate, cuff),
    no-coat trousers L/R (ochre outer seam). Sliced to art_src/cast/sliced/cast_traveller_legs_front/.
  - `tools/cast/front_legs.py` (cut_cast_rig.py now calls it after cutting): for all 15 traveller figures, each leg_l /
    leg_r is replaced by the matching front leg, hip pivot unchanged, sole on the old sole line, width fitted to the
    first visible row below the coat hem / at the crotch (new rig.json `parts.leg_*.vis`), round top cap, per-channel
    colour match to that figure's own trouser and boot print (sampled from the figure). rig.json leg bboxes updated
    (`front: true`); body/hips PNGs byte-identical. Side-view legs kept in art_src/cast/legs_side/ (30 PNGs).
  - Checks: rest-pose sheet art_src/cast/qa/rig_preview.png; 8 fps leg close-ups over 2 s
    `artifacts/cast/walk_legs_closeup_v2.png` (rows: wind_turn, sun_turn, stream/no-coat): boots point at the reader
    in every frame, alternate lift reads as a knee bend, no 팔자. Video `artifacts/video/walk_feet_v2.mp4` (sun_turn,
    20 s, 6.8 MB). check_all clean (39 scripts).
  - Open: on the stream approach the card is yawed ~30° from the camera (_face_total ≈ 0.52 rad while the road
    camera lags), so the toward-the-card stride is seen obliquely and the legs open into an A-frame on screen
    (feet still face front). Probe showed the sideways foot offsets in the card frame are small (~0.03), so clamping
    them doesn't help (tried, reverted); the fix is to face the card at the camera / scale the stride pitch by the
    card-to-camera yaw. Front boots are a bit narrower than the side-view ones were (reads slimmer).

## 2026-11-18 — Stream walk A-frame fixed (billboard + screen-sideways compression)
  - Cause (probe): front_gait steps toward the CARD, but the base gait turns the card up to max_turn_deg (20°) toward
    the walk; on the diagonal stream approach the stride was seen obliquely and the legs opened sideways into an A on
    screen (sideways offsets in the card frame were only ~0.03, so a card-x clamp did nothing).
  - cast_puppet.gd (front_gait only): `front_turn_keep` 0.2: max_turn_deg is scaled around super._process, so the card
    turns at most ~4° off the camera (done at the source because the legs are top-level and the base gait places them
    against the turned card when standing); `_front_foot`: each foot's offset from under its hip along the true
    screen-sideways axis (horizontal perpendicular to puppet→camera, in the turn frame) is kept at `front_side_keep`
    0.35 and soft-limited (tanh) to `front_max_side` 0.012 × height/0.36; used for the stance pivot/height solve and
    both leg aims. The diagonal travel is carried by the body (small sole slip instead of an A).
  - Checks: `artifacts/cast/walk_legs_closeup_v3.png` (8 fps × 2 s; rows: stream, wind_turn, sun_turn): stream legs
    stay parallel, boots to the reader, no A; wind/sun unchanged in read. Videos: `artifacts/video/walk_stream_v3.mp4`
    (20 s, 5.3 MB), `walk_feet_v2.mp4` re-recorded (sun_turn, 6.8 MB) since the gait change applies to all walks.
    check_all clean (39). Supersedes the "Open: stream A-frame" note above.
  - Open: on the stream close-up a couple of frames show the legs drawing slightly together (feet nearly touching)
    mid-stride; sole slip sideways on diagonals is not visible at story distance but would show in a close camera.

## 2026-11-18 — Walk v4: no cut legs, swinging arms, loose child-like gait; stream feet in the WATER
  - User: "잘린 다리가 코트 위를 삐져나와서 이상해 그리고 군인처럼 걷는 거 같아" + stream bug (he sank his feet into the bank,
    not the water). Old rig backed up in art_src/cast/rig_backup_v3/ (all rig PNGs + rig.json).
  - Legs (no slide, no squash): new Codex sheets `cast_traveller_legs_half` (knee slightly bent) and `cast_traveller_legs_lift`
    (knee up, short foreshortened shin, boot toward us), refs = the front-legs sheet + ref_traveller_legs (fresh md5s).
    `tools/cast/lift_legs.py` fits them to every traveller figure like front_legs (same hidden top line, hip pivot, width at the
    visible row; natural length 0.90 / 0.76 of hip→sole; per-class mean/std colour transfer to that figure's straight leg) →
    `<fig>_leg_{l,r}_{half,lift}.png`, rig.json `parts.leg_*.alt`. CastPuppet swaps the swing leg to the variant nearest the
    hip→foot length and only stretches ≤8 % about the hidden hip; the top is never exposed.
  - Arms: `tools/cast/walk_arms.py` for coat_calm, coat_nohat_calm, nocoat_calm (= every calm walking figure; shirt_calm also
    carries the coat): arm cards are the figure's OWN sleeve+hand pixels cut along the sleeve seam, top capped by a disc around
    the shoulder pivot (rotation-invariant edge); the torso under the arm is filled from the Codex armless sheet
    `cast_traveller_walk_armless` (registered to the figure, colour-matched, used only under the arms). rig.json
    `parts.arm_l/arm_r {bbox, pivot}`. The Codex `cast_traveller_walk_arms` sheet was generated but not used (cut arms match
    exactly). Expression poses (cold hug, fan, hands on head, hot) keep baked arms. cut_cast_rig.py now runs front_legs →
    lift_legs → walk_arms (verified: a full re-cut reproduces the rig byte-identically).
  - Gait (cast_puppet.gd `_front_step`): continuous weight-shift roll (±4°, spring-lagged) about the ground point between the
    feet so the hips sway over the planted foot; pendulum bob + heel-strike dip/recover spring; body card (head/hat) trails the
    hips (lag spring), squashes ≤3 % on the dip, counter-twists ±2.5°; quick-lift swing profile; arms swing opposite to the
    legs (pitch toward the camera 20° forward / 6° back + 9° inward roll) on an underdamped spring (overlap); no arm shadows
    (they threw dark blocks on the coat). Story knobs (spread_stage): wind → front_lift 0.45, front_arm_swing 0.3, front_hunch 1
    (body squashed, arms tucked to the coat front); heat → front_droop = warmth while the coat is on (lower lift, heavier lag,
    smaller arms); carrying the coat → arm_hold = 1 (that arm doesn't swing).
  - Seams: light line at the no-coat crotch was the body card's EDGE WALL (proved by tinting it blue), not the rim. New
    game/art/cast/rig/cast_edge.gdshader (+ cast_print.gdshader: rim window, no texture wrap) swapped onto the puppet's own
    material copies: join edges (no-coat seat, hips piece, hidden leg tops, arm shoulder caps) take the garment colour.
  - Stream: `_find_stream` picks a spot INSIDE the felt cut polygon (≥0.13 from its edge) instead of the centreline-distance
    band at the bank; off the road the stage follows the real ground height (`_ground_dy`, steps down onto the water card),
    sink 0.13·H (shins), splash/ripple rings on the water surface. Opaque water hides the sunk legs; bank lip behind him.
  - Bench: game/art/cast/bench/cast_front_bench.tscn (`-- --pose=… --droop= --lift= --arms=`), close camera, front gait.
  - Checks: artifacts/cast/walk_body_closeup_v4.png (8 fps × 2 s full body; rows sun_turn, wind_turn blowing, stream),
    artifacts/cast/stream_feet_in_water.png; videos artifacts/video/walk_v4_{sun,wind,stream}.mp4 (6.9 / 7.7 / 5.0 MB).
    check_all clean (40). The "2 ObjectDB leaked" warning at exit in sun/wind recordings is pre-existing (same with HEAD
    cast_puppet.gd).
  - Open: the lifted coat leg shows mostly cuff + boot under the hem (the knee is behind the coat) — reads as a step but a
    little stubby; the swaps between straight/half/lift are discrete (paper-toy pops, visible on close inspection at 30 fps);
    the armless-torso fill under the arms is generated art and only shows as a sliver when an arm swings out; the in-wind
    "clutch" is only a tuck of the free arms (the real clutch is the baked cold/hold pose); head/hat lag is subtle because the
    head is on the body card (no separate head card).

## 2026-11-18 — Walk v7: legs stay under the coat with the steady (damped) gait
  - User (after the v6 damping, "좋은데"): "이번엔 또 다시 발이 코트를 벗어나" + "벗은 코트. 단추를 푼 코트" (same on the
    coat-off and the unbuttoned-coat figures). Upper body unchanged (roll 0.6°, v6 bob/bounce/lag/twist kept).
  - Cause (bench close-ups): the legs pitch toward the camera about the hip, but sat only ~1 cm behind the coat card. A leg
    pitched φ moves forward by d·sin φ at d below the hip, so above the hem it came THROUGH the coat plane and its flat top
    / cuff band drew over the hem (the "cut piece"); on the no-coat / open-coat figures the same happened through the
    hips (trouser-top) card, ~2 mm in front of the legs. Back-pitched swing legs (up to 40°) also foreshortened to a lone boot.
  - cast_puppet.gd (front gait only): legs hang deeper behind the hips card, depth from the rig (rig.json vis row − hip =
    covered length, hip − card top = hidden top) so a pitch up to `front_pitch_deg` 20° (back `front_pitch_back_deg` 24°)
    can't reach the coat/hips plane; `_clamp_pitch` limits each leg's pitch to what its depth allows; footprints are pushed
    back by the same depth (resting legs hang straight down). Open-coat figure (hip high, long coat) gets the deepest legs.
    A capped pitch leaves the sole a few mm off its print in depth only. Step width now scales with the roll
    (`front_roll_deg`/4, min 0.15) so at 0.6° the feet stay under their hips, inside the coat. `front_lift_frac`
    0.25 → 0.15 (lifted leg shows knee/shin + cuff + boot, not a boot hanging under the hem).
  - Checks: artifacts/cast/walk_hem_v7.png (8 fps, tracked hem/leg crops; rows sun coat walk, wind struggle, stream
    no-coat, open coat after sw_028, coat off carrying it); videos artifacts/video/walk_v7_{sun,wind,stream}.mp4 (sun
    = whole sun_turn + moral start, 50 s: coat → open coat → fan → coat off → carrying). check_all clean (40).
  - Still off: a swing leg pitched toward the camera is a little darker (its card faces down, less sun; was so in v4/v6
    too); on the no-coat figure the bottom edge of the hips (trouser-top) piece is faintly visible as a horizontal line
    at the crotch when the legs are lit differently (pre-existing art/rig seam, not a gap); the carrying walk is slow, so
    its steps are small.

## 2026-11-18 — 「아기 돼지 삼형제」 (three_pigs) phase 1: plan, script, tools by tale, shared cast + props (not committed)
  - Plan: game/stories/three_pigs/PLAN.md (beats, cast sheet with every pose per line, interactions, pop-up moments,
    asset list, phase-2 runner verbs). 10 beats on meadow seed 1: cover · home (tap each piglet → wave + its material
    pops up; they walk AWAY, back views) · straw_build (tap ×3, straw house folds up band by band; 첫째 carries straw in
    SIDE view) · wood_build (tap ×5, hammer) · brick_build (tap ×10 counted, 2 taps per band; brothers tease at tap 5) ·
    wolf_straw (wolf prowls in SIDE view; tap ×3 = 후~, bands fold down, blown-apart heap) · wolf_wood (tap ×5, wobble →
    collapse) · brick_wolf (tap ×8 counted, house only shivers; wolf sits 털썩) · chimney (SET PIECE: brick facade folds
    down into the kitchen; tap the fire ×3; wolf drops into the pot, 앗 뜨거워, runs off LEFT) · ending (tap plots ×2 →
    two brick cottages pop up). Estimated 3:20–3:30 (narration ≈ 165 s); further cuts listed in PLAN.md.
  - Script: tools/story/tales/three_pigs.py → game/stories/three_pigs/script.json (60 lines, 36 used: 34 reuse,
    2 new). Seg trims reuse clips (001 mom only, 023, 028, 032 without narrator lead-ins). `expr` per line (LINE_META).
    39 clips copied to game/audio/voice/three_pigs/. Recording dry-run: tp_n01 cover + tp_n02 replay, 86 chars — NOT
    recorded (needs the user's OK).
  - Tools by tale: seed_script.py / record_lines.py take `--tale` (default sun_wind); per-tale tables in
    tools/story/tales/<tale>.py. sun_wind's BEATS there are the LIVE beats of its script.json (the seeder's copy had
    gone stale: script.json beats were hand-edited after seeding), so `--tale sun_wind --out X` is byte-identical to
    game/stories/sun_wind/script.json (lines also identical to the old seeder's output).
  - Shared props (Codex, md5-unique): story_houses (11: straw / wood / brick facades, side walls, straw heap, wood ruin,
    2 extra brick cottages, chimney), story_build_props (23), story_hearth (19), catalogued in game/art/atlas/catalog.json
    under new categories story_building / story_prop / story_fx (the meadow template queries by category, e.g.
    query("building"), so these never enter sun_wind's spreads; old 419 entries unchanged). tools/atlas/house_stages.py
    cuts a facade into fold-up bands (cuts snapped to mortar / plank / straw lines; roof = last band) →
    game/art/atlas/story_houses/stages/ (+ stages.json with hinge heights).
  - Shared cast (Codex, refs = round-1 sheets, ANIMAL_STYLE block: prints only on clothing, peach-pink pigs): 3 piglets
    (11 figures each: front calm/happy/scared|brave/startled/defiant/…, side walk/run/carry, back walk), mother pig (3),
    wolf (12: front calm/shout/hungry/ouch/falling, side prowl/sniff/huff/exhausted/tiptoe/run_away, back). Walk parts:
    front legs + half + lift (8 legs each sheet), armless calm torsos, side legs. 74 cast cards in game/art/cast/catalog.json.
  - Rig tools generalised by character (tools/cast/characters.py registry, tools/cast/three_pigs_cast.py entries):
    front_legs / lift_legs per character; walk_arms auto mode (arm = figure minus the registered armless figure, rows
    0.40–0.84 H — first try picked a pig's ear as an arm); cut_cast_rig: per-figure min leg gap (piglets 7 %), leg
    column trim for front/back figures (the wolf's tail had joined his leg), hips clipped to the figure; new
    tools/cast/side_legs.py (side walkers: drawn side legs on ONE hip joint + a round joint cap). Traveller outputs
    verified byte-identical (all rig PNG/webp md5s, rig.json + catalog entries, rig_preview.png).
  - Contact sheets: artifacts/three_pigs/cast_contact.png, artifacts/three_pigs/props_contact.png;
    rig preview art_src/cast/qa/rig_preview_three_pigs.png. gd_run import + check_all clean (43 scripts).
  - Open: 6 figures unrigged (legs overlap: pig_a_carry_straw, pig_b_run, wolf_back_walk/tiptoe/run_away/hungry) —
    hop them as static cards or regenerate with a leg gap; wolf front: thin leg-top sliver beside the left thigh; house
    bands cut through windows/doors and wall bands keep tiny eave tips; no story.tscn yet (runner verbs are phase 2).

## 2026-11-18 — F perf: card batching, sliced spread prebuild, iOS export (no look change intended)
  - Profiled on this Mac (M4 Pro, 1366x1024, windowed; Metal has no GPU timer, so GPU = Vulkan/MoltenVK). Before =
    HEAD 6385db7 in a temp worktree, same harness (tools/perf/profile.py; rows in artifacts/perf/final_profiles.jsonl).
    | scene | draws (Vk max) | draws (Metal max) | primitives | Vk GPU p95 | Metal frame p95 | worst frame |
    |---|---|---|---|---|---|---|
    | meadow v0 before | 5069 | 1559 | 11.26 M | 14.16 ms | 10.53 ms | 10.7 ms |
    | meadow v0 after  | 466  | 432  | 4.25 M  | 9.15 ms  | 9.60 ms  | 11.1 ms |
    | wind_turn before | 3838 | 1348 | 11.1 M  | 13.46 ms | 13.78 ms (120 s run) | 3861 ms (page turn to sun_turn) |
    | wind_turn after  | 566  | 466  | 4.25 M  | 9.29 ms  | 9.37 ms  | 45 ms (startup frame; story frames ≤ 36 ms) |
    | sun_turn before  | 4494 | 1335 | 11.2 M  | 13.50 ms | 9.82 ms  | 44.9 ms |
    | sun_turn after   | 490  | 440  | 4.27 M  | 8.96 ms  | 9.64 ms  | 43.9 ms (startup) |
    Page turn wind_turn -> sun_turn: before one 2.0-3.9 s frame (synchronous spread build); after the next spread is
    prebuilt and moved in at the turn in 1.5 ms; no frame over 50 ms in the 120 s wind_turn->sun_turn->moral->stream run.
  - Cards (core/world/card_batch.gd, card_atlas.gd, shaders/card_batch|card_shadow|card_wind): every meadow card
    (static + hinged) is drawn from ONE MultiMesh per print with ONE shared material. PaperCard's print/back/wall
    surfaces became one indexed surface (UV2 = part, print index), print textures are copied texel-for-texel into a
    wrap-padded Texture2DArray atlas (no mips, like the lossless prints; params texture holds rect/size/edge colour);
    the shader is a line-by-line port of paper_print + paper_edge. Hinged cards keep their PopHinge nodes (springs,
    audio, visibility); a moving hinge marks itself and its instance is rewritten once per frame. WindSway rocking
    moved into the vertex shader (same formula, WindSway feeds t/strength/axis). Shadows: one SHADOWS_ONLY MultiMesh
    of quads (light-facing face plane, print alpha, mirrored on the back, inside the rasterized cut contour) instead
    of every card mesh in both splits (card shadows 4.5 ms -> 0.7 ms GPU). Vertex outputs trimmed (params fetched in
    the fragment), wall quads share corner vertices: the card pass is vertex-bound (6.2 M verts/frame -> 4.1 M).
    Static merging into chunk meshes was considered and not done: unique merged geometry would be ~150-200 MB of
    vertex data and a 1-2 s build; the per-print MultiMesh with one material gives the same draw-count win.
  - Ground: slabs batched per identical material (116 MeshInstances / 112 materials -> one surface per material).
  - Hitches: spreads build time-sliced (BuildSlicer, 3 ms/frame) in an off-screen SubViewport with its own World3D
    while the previous page plays, processing disabled until moved in (not in --fixed runs: captures/recordings build
    at the turn exactly as before, same RNG sequence). Exact speed-ups: road/stream distance grid (placement 1.5 s ->
    0.43 s, identical counts), PopWave.cover_pairs grid (60 ms -> 2 ms per pop/fold, identical pair list, verified by
    tools/perf/check_pairs.gd), PaperCard contour cache per texture, catalog JSON parsed once, traveller figure +
    cast prop prints traced/loaded ahead (pose-change hitches 33-46 ms gone).
  - Look check (tools/perf/capture.py + compare.py; 6 meadow views at frame 170 + wind_turn/sun_turn at frame 600;
    sheet artifacts/perf/before_after_sheet.png, PNGs in artifacts/perf/captures/): noise floor (same build twice,
    film grain) mean 2.83 / max 12. After vs before: mean 2.64-3.32 on 7 of 8 views (>24 diff on 0.07-0.94 % of pixels),
    view 1 mean 3.91 / 2.3 %. Main pass is at the noise floor (with old-style mesh shadows view 0 = 2.87 mean,
    0.003 % >24); all remaining difference is thin shadow edges: the quads do not cast the 1-4 mm cut-wall
    thickness, visible on cards lit almost edge-on (view 1). Exact mesh shadows: CARD_SHADOW_MODE=mesh env var
    (+2.5 ms GPU, ~+550 draws in view 1).
  - Not met: "< 8 ms Metal p95" (Metal frame p95 9.4-9.6 ms; Vulkan GPU p95 9.0-9.3 ms; the card pass is now
    vertex-bound, ~4 M visible-pass vertices for 5,400 cards). Next levers need sign-off (look-affecting): contour
    decimation for small/far cards, per-instance frustum culling (needs chunked MultiMeshes = more draws), fewer
    ground-cover tufts.
  - iOS: export preset "iOS" (game/export_presets.cfg: Xcode project only, bundle com.house4k2b.popupstorybook, team
    66DAQSBX4V from the Apple Development cert OU, iPad only). project.godot: import_etc2_astc=true, handheld
    orientation sensor-landscape. StoryRunner renders 3D at <=1024 px tall on mobile (iPad 2388x1668 -> 0.61, the
    approved 1366x1024 pixel density; UI native). Export -> build/ios (gitignored; pck 128 MB). Unsigned device
    build: BUILD SUCCEEDED. Simulator: Godot 4.7.2's template ships an x86_64-only simulator lib and the iOS 27
    simulators are arm64-only; retagged the arm64 device objects as iossim (+2 Metal error-domain stubs) -> build,
    install and launch OK, but Godot stops with "Apple GPU does not support image cube arrays" (simulator GPU limit,
    Metal and MoltenVK; GLES3 fallback crashes in the canvas renderer) -> artifacts/perf/ios_sim_ipadpro11.png.
    Signed device build stops at "No Accounts" (no Apple ID in Xcode). check_all clean (43).

## 2026-11-18 — 「아기 돼지 삼형제」 (three_pigs) phase 2: data-driven story engine, all 10 beats wired, plays start to end
  - Engine (commit 97fba7d, then this round): SpreadStage builds the cast from script.json `cast` by kind (walker =
    template road walker with a CastPuppet skin; hanger = SkyHanger in the story shot's sky band with backing disc;
    actor = StoryActor; prop), set pieces from `spread.set` (SetPiece: atlas cards on hinges, houses in fold-up bands
    with wobble / shiver / collapse / band_down / cutaway), named `spots` ([right, toward camera] from the page
    anchor), `focus`, `light: dusk`, tale `shots`, `ui` (cover / end pictures, speaker chips), and a per-tale
    `handler` (TaleHandler). sun_wind's effects moved verbatim to game/stories/sun_wind/fx.gd; three_pigs effects in
    game/stories/three_pigs/fx.gd. Page key = seed:view:place; same-page beats apply only their set / light / enter;
    a page started mid-way (--beat) merges the earlier beats' set pieces.
  - Walkers in any direction (StoryActor): camera-relative travel angle → front / back / side view (15° hysteresis
    each way), side figures mirrored for leftward travel (negative x scale on the tilt node), paper turn on view or
    facing change (CastPuppet.set_figure). Side gait: stance foot planted (angle = asin(stride·(½−s)/L)), swing leg
    through with lift, hips ride the stance leg. Unrigged figures hop as one card. Standing figures breathe.
    Bug found on the way: set_figure called every frame restarted the flip, so faces lagged a whole line.
  - Verbs: who/dir/to/from/exit on walk, who on pose, tap_each, tap_steps, build (bands per tap, counter), huff
    (blow_apart / collapse / hold + ruin), climb (waypoints off the ground), cam `at`, line `expr` applied per seg,
    `--tale=<id>`; guard so autoplay never waits forever on a missing tap target. Documented in
    .claude/skills/popup-tale/references/script_schema.md.
  - Art fixes: unriggable figures (pig_a_carry_straw, pig_b_run, wolf_back_walk / tiptoe / run_away / hungry) kept as
    static cards with a paper hop (no Codex spend). Wolf thigh sliver: tools/cast/trim_leg_tops.py trims front leg
    tops to the body / hips silhouette with a 46 px calf taper above the hem (artifacts/three_pigs/wolf_leg_tops_fixed.png).
    House bands: tools/atlas/house_stages.py now cuts rows that cross no window, steps around doors (door rises whole
    with band 0) and uses hand-picked rows for the brick / wood houses (OPENINGS / CUTS); eave tips go with the roof.
  - Voice: tp_n01 / tp_n02 status "pending" (not recorded, no ElevenLabs spend): caption-only with the estimated read
    time; STORY_DONE missing_audio=["tp_n01","tp_n02"], autoplay unaffected.
  - Verify: check_all clean (48 scripts). sun_wind same-view captures at the noise floor (mean 2.5-2.6, max 12, same
    hidden-card counts); full autoplay STORY_DONE 240.7 s after the refactor and 238.8 s at the end (cover page now
    builds the first spread at 10 ms/frame), missing_audio=[]. three_pigs full autoplay STORY_DONE 320.4 s.
    Videos: artifacts/video/three_pigs_full.mp4 (crf 30, 27.4 MB), three_pigs_build_brick.mp4, three_pigs_huff_wood.mp4,
    three_pigs_chimney.mp4; play sheet artifacts/three_pigs/play_sheet.jpg; 8 fps walk tiles artifacts/three_pigs/tiles/.
    Fixed from the tiles / frames: straw lot and wolf stood in the stream (view 2 anchor is on it; spots re-picked with
    tools/story/probe_spots.gd), stage camera ignored the focus spot, wolf entrances mostly off-frame, counter cut off
    at the top, roof climb / launch out of frame, steam hid the wolf in the pot, pig hid behind the straw pile, stale
    imports after recutting bands (reimport before recording).
  - Runtime 5:20 vs the ~3:15 target. Narration alone plays ~189 s (36 reused clips); 9 page turns ≈ 45 s; 37 taps at
    the 1 s autoplay pace + walks / fx ≈ 85 s. Proposed cuts (need the user's call; several need re-recording):
    one village page for all three houses (build and huff on the same spread with camera pans, −4 page turns ≈ −22 s);
    brick taps 10 → 5 and wolf huffs 8 → 4 (re-record tp_024 / 025 "열 장" and tp_046 "여덟 번", ≈ −12 s); drop tp_047
    (털썩: shown, −4 s), tp_023 narrator seg (−3.5 s), the tp_026 huff prompt (keep it as the idle hint, −5.5 s), tp_000
    (the cover title says it, −4.5 s). All together ≈ 4:30; reaching 3:15 also needs shorter narration lines.
  - Still off: the wolf in the pot is small and half behind the pot rim; the brothers' tease walk arrives late in
    their line; the first page still waits ~8 s behind the cover in recordings; nobody has listened to the reused
    clips in context.

## 2026-11-18 — three_pigs v2 fixes (user: houses across the road, odd wood-house start)
  - Lots moved onto open meadow beside the road (ground maps from tools/story/probe_spots.gd): view 3 wood lot
    [1.0, -0.62] right of the road, wolf comes up the road; view 4 brick lot [-0.85, -0.6] left of it, pile in front
    left, brothers tease in front, pigs peek out on the road side, kitchen spots keep their lot offsets, ending
    cottages left-back [-2.05, -1.3] and right of the road [1.2, -1.2] with a wider "village" shot. Home brick pile
    and straw pile nudged off the road. New SpreadStage footprint check: SET_CHECK road=0 water=0 for every set
    piece of all 9 beats.
  - Wood house: scale 1.0 (≈ the brick house's on-screen size); the "giant A-frame" was the roof band stretched to
    the floor by stray edge pixels the eave-tip rule had sent to it (fixed in tools/atlas/house_stages.py); first
    band = floor, sill, lower plank walls and the door (cut rows 211 / 172 / 140), standing when the page opens
    ("stage": 1), 5 taps raise the window row, the upper wall, the top strip and the roof (build counts from the
    standing bands). Build-beat opening lines (tp_019 / 021 / 024) now start after the story shot lands (cam wait
    1.2 s; tp_021 began mid-glide).
  - Counter moved to the upper left of the house (inside the frame), wolf_wood wolf spot nudged into frame.
  - Verify: check_all clean; full autoplay three_pigs STORY_DONE 322.2 s (missing_audio tp_n01 / tp_n02, pending),
    sun_wind STORY_DONE 238.5 s missing_audio=[]; artifacts/video/three_pigs_full.mp4 re-recorded (24.9 MB).
  - Videos: artifacts/video/three_pigs_wood_v2.mp4, three_pigs_brick_v2.mp4, three_pigs_wolf_wood_v2.mp4; tiles
    artifacts/three_pigs/tiles/v2_*.jpg (8 fps: wood build, brothers' tease walk, wolf entrance, pigs' run).

## 2026-11-18 — three_pigs v3: the pigs are at home; both tales tell the tale (no counting, quiz or moral)
  - User: "아기돼지들 집에 있어야하지 않겠니?" House facades now have die-cut window glass and a door leaf on its own
    side hinge (tools/atlas/house_stages.py GLASS / DOORS -> stages.json windows / door; SetPiece.open_door,
    window_spot, door_point). `enter.inside` puts a pig just behind the front wall with its eyes at a window (the
    frame overlaps it); speaking from inside it bobs; the straw / wood house falling reveals them where it stood
    (scared, hop) before they run. brick_wolf: 셋째 is home (left window), 첫째 and 둘째 run up the road and in
    through the door (door opens, back view through the doorway, door shuts) and peek from the right window; the
    chimney cutaway shows them in the kitchen. Straw build ends with 첫째 playing in his doorway; every wolf page opens
    with the pigs inside. Tiles: artifacts/three_pigs/tiles/v3_*.jpg/png.
  - User: "팝업북은 어떤 교육적인 요소보다는 그냥 동화의 전달에 좀 의미를 뒀으면". three_pigs: tap counters gone; 3 taps
    per build and per huff; tp_045 / tp_046 (counting) and tp_055 / tp_056 (plot taps, "하나, 둘, 셋") dropped; tp_042
    (셋째 "셋이서 함께라서 무섭지 않아!", existing clip) answers the huffs; tp_024 / tp_025 lose "열 장" by trimming the
    existing clips at their sentence pause (nar_506a46173c_s1.mp3, nar_33372fce4a_s2.mp3 — please listen); the
    ending is the brothers and mom safe in front of the brick house (tp_057), no moral. sun_wind: the moral beat is
    gone (flashback cards, the sw_036 quiz, sw_040 / sw_041), the sun's win flows into the stream. Both: voiced tap
    instructions only for the first tap of each kind, later taps show only the ring. All through the
    tools/story/tales/*.py tables (TRIM support added to seed_script.py).
  - Verify: check_all clean. three_pigs STORY_DONE 281.3 s (4:41, was 5:22; missing_audio tp_n01 / tp_n02 pending),
    sun_wind STORY_DONE 210.5 s (3:31, was ~3:59) missing_audio=[]. Videos: artifacts/video/three_pigs_full_v3.mp4
    (22.7 MB), sun_wind_full_v3.mp4 (25.5 MB, crf 32), three_pigs_wolf_straw_v3 / wolf_wood_v3 / brick_wolf_v3.mp4.

## 2026-11-18 — three_pigs v4: the wolf in frame, readable window faces, 첫째 hidden until the straw house falls
  - Coordinator review of brick_wolf_v3 (12 frames): the wolf was almost never visible. The three wolf beats now use
    the closer story shot focused between the wolf's mark and the house (`wolf_focus` spots), wolf marks moved in
    (straw [-1.72, 0.32], wood [0.38, -0.12], brick [-1.52, 0.02]); he stands fully in frame left of the house for his
    arrival, line, every huff (puffed cheeks + wind curls toward the house) and 털썩.
  - Window faces lit by a small warm shadowless fill between face and wall (OmniLight 0.45, range 0.22; 1.6 blew the
    windows out); they read as faces at iPad size (artifacts/three_pigs/tiles/*_v4_12frames.jpg).
  - Straw huffs: the first takes only the roof, the next ones rock the walls, the last blows it all away, so 첫째
    stays hidden until the collapse.
  - Videos: artifacts/video/three_pigs_wolf_straw_v4.mp4, three_pigs_wolf_wood_v4.mp4, three_pigs_brick_wolf_v4.mp4,
    three_pigs_full_v4.mp4.

## 2026-11-19 — three_pigs v5: the brick house gets a real pop-up room; bigger window faces
  - User: "벽돌집. 그럼 집 뒤편도 있어야하지않을까유" (the cutaway showed meadow through a house with no inside). New
    shared sheet story_room (Codex, BUILD_ANCHOR style block, tools/atlas/make_jobs.py; raw md5 76e43f20… unique;
    looked at before slicing; tools/atlas/labels/story_room.json, category story_building / story_prop): plastered back
    wall with a brick dado, two side walls with corner posts, plank floor, brick chimney flue, roof beam.
  - Cutaway room (KITCHEN in tools/story/tales/three_pigs.py): back wall behind the roof line, side walls angled in like
    a pop-up box, flat plank floor (SetPiece `flat`: lies on the page, pops with a paper bounce), the hearth against the
    back wall with the flue rising from it under the outside chimney, logs, fire (1.8× scale) and the pot raised over it
    (`lift`), table and shelf; everything folds up as the front wall folds down. The wolf drops from the chimney top
    down the flue into the pot; the fire grows small → medium → large under the pot. The chimney beat opens with the
    pigs at the windows (they're home), then inside the room.
  - Window faces: pigs behind windows scaled 1.45× so a face fills the opening, fill light lowered to 0.09 (0.22 /
    0.45 washed the faces out; 0 left them in shadow).
  - Videos: artifacts/video/three_pigs_chimney_v5.mp4 (12-frame tile
    artifacts/three_pigs/tiles/three_pigs_chimney_v5_12frames.jpg), three_pigs_full_v5.mp4.

## 2026-11-19 — three_pigs v6: new lines recorded, the wolf climbs a ladder, the room is open before he climbs
  - Voice (user approved ElevenLabs for these two only): tp_n01 "그림책을 톡 눌러서 펼쳐 볼까요?" and tp_n02 "또 보고 싶으면
    '다시 보기'를 톡!" recorded with tools/story/record_lines.py --tale three_pigs (narrator voice + settings from
    script.json, 86 characters) -> nar_63ae712910.mp3 (3.04 s), nar_643e01190e.mp3 (2.96 s), recorded.json; reseeded:
    status changed-recorded, missing_audio []. Nobody has listened to them yet.
  - Chimney beat (user: "늑대 굴뚝 올라갈때 이상", "굴뚝 내려올때 집 올라오는게 이상"): the cutaway opens first (front wall down,
    room up, pigs inside, fire lit) under a shot framing room + roof; a ladder (village_props_30, shared) leans against
    the left wall under the eave; the wolf walks to it (side view), climbs it (back view: StoryActor shows back_walk on
    near-vertical path segments with a rung bob), steps onto the eave and walks up the slope and along the ridge with
    the side gait, steps onto the chimney top and sinks into it (`climb sink`: the card squashes onto its feet). When he
    comes down the flue nothing pops; he drops into the pot.
  - Fire set inside the hearth opening behind the pot; a warm fire light (grows with the flame) lights the pot rim.
  - Tiles: artifacts/three_pigs/tiles/three_pigs_chimney_v6_12frames.jpg, three_pigs_chimney_v6_climb_8fps.jpg.
    Videos: artifacts/video/three_pigs_chimney_v6.mp4, three_pigs_full_v6.mp4. Full run STORY_DONE 286.9 s
    missing_audio=[] (reimport needed after recording: the first run still listed the two lines).

## 2026-11-19 — three_pigs v7: the brick house never opens; the camera goes inside after the wolf
  - User: "방이 열려도 앞 벽은 막혀있어야하는거아닌지" / "굴뚝으로 들어가면 그제서야 안을 보여주면 되자너". The front wall no longer
    folds. Chimney beat: closed house, the brothers' faces in the glowing windows, the wolf walks to the ladder, climbs
    (back view), walks the roof (side gait) and sinks into the chimney under a closer roof shot; only then the camera
    glides in through the front (SpreadStage hides a banded facade's wall bands only while the camera is within 0.16 of
    it or behind it; actors at its windows are hidden then) to an inside shot ([0.6, 5°, 0.26, fov 68]) of the room
    built inside the house footprint from the start of the beat (fx room_ready: back wall, side walls edge-on to the
    outside camera, two floor boards, a plank ceiling shown only while the camera is inside (`inside_only`), hearth
    with flue, fire, pot, table, shelf). Fire taps, the drop down the flue into the pot, splash, "앗, 뜨거워!", then the
    camera glides back out to the closed house and he shoots out of the chimney. The ending shows the closed house.
  - Still off: mid-glide, the widening lens briefly shows the dark sky above the template's back hills.
  - Videos: artifacts/video/three_pigs_chimney_v7.mp4 (tiles three_pigs_chimney_v7_12frames.jpg, _glide_in.jpg),
    three_pigs_full_v7.mp4 (full run STORY_DONE 288.3 s, missing_audio=[]).

## 2026-11-19 — three_pigs v8/v9: window peeks, firelit windows; the whole house story on one village spread
  - User: "바깥보여줄때 창문에 돼지들이 이상해". New shared cast sheet cast_tp_peek (Codex, ANIMAL_STYLE, refs the pig
    lineup; first job timed out, retry ok; raw md5 d16ae4e6… unique; looked at before slicing; contact
    artifacts/three_pigs/peek_contact.png): six peek figures (head + hands on the sill) — 첫째 scared / defiant,
    둘째 scared / defiant, 셋째 brave / defiant — catalogued as poses peek_* of skins pig_a / pig_b / pig_c. A pig at
    home now peeks: one per window, head 65 % of the opening (house_stages.py writes window_boxes), the same scale
    everywhere, a darker warm interior plane behind (SetPiece.window_backs "dim"), a slight warm fill (0.16), the peek
    expression follows the line (scared / defiant / brave), a bob when speaking. Three pigs and two windows (brick
    house): 셋째 and 첫째 peek, 둘째 is inside out of sight (two can't share a window at that scale without
    overlapping the frame). Chimney beat exterior: no faces; flickering firelight behind the glass ("fire") and steam
    from the chimney top. The window planes hide when a house falls.
  - User: "책장 안넘기고 한번에 처리하는게 좋을거같음 카메라 무빙으로". Views 2 / 3 / 4 of seed 1 were three camera
    stations on one road (probe: straw lot 1.8 and brick lot 2.6 from view 3's anchor, inside its pop radius), so
    straw_build … ending all play on one page (view 3, place "village"): spots converted into view 3's frame
    (`_to3` in tools/story/tales/three_pigs.py), every set piece of all three lots built with the page (SET_CHECK
    road=0 water=0 for all 29), camera stations listed in spread.sightlines (incl. tracking stretches along the road),
    `cam at` glides between lots, `walk via road` + `follow` tracking shots (StoryActor.follow on the ground,
    SpreadStage.road_route / follow_actor), `built` lists per beat (houses and ruins standing then) for `--beat`
    starts. The escape is continuous: straw house blown → 첫째 runs along the road to the wood house (camera follows),
    in through the door, peeks from a window → the wolf follows along the road → the wood house falls → both run to
    the brick house and in → the wolf follows. Page turns left: cover → home → village.
  - Verify: check_all clean. three_pigs full STORY_DONE 276.3 s (4:36; v7 288.3 s: 5 page turns gone, the road
    runs add time — runner speed 0.8, wolf 0.6) missing_audio=[]; sun_wind STORY_DONE 203.3 s missing_audio=[].
    Village spread perf (beat wolf_wood, Metal, 25 s): frame p50 8.4 / p95 9.8 / max 23.6 ms, 0 frames > 33 ms,
    draw calls max 463 / mean 429 (sun_wind wind_turn: 466), 4.19 M primitives; direct build 3.4 s (story start with
    --beat), in the normal flow the village is prebuilt behind the home page (PERF spread_prebuilt 1:3:village).
    Videos: artifacts/video/three_pigs_full_v9.mp4 (= _full_v8, 24.7 MB), three_pigs_escape_v9.mp4,
    three_pigs_wolf_straw_v8 / wolf_wood_v8 / brick_wolf_v8 / chimney_v8.mp4 (cut from the full run). Tiles:
    artifacts/three_pigs/tiles/v9_*.jpg.
  - Still off: with three pigs and two brick windows 둘째 is out of sight; the wolf stands next to the wood ruin while
    the brothers run past him; the run toward the brick house pans the brick house half out of frame for a moment.

## 2026-11-19 — three_pigs v10: houses have bodies (open doors show interiors), brick lot moved, ladder found
  - User: "문열때보면 뒷편이 없는곳으로 가다보니 이상한디?". Each house set entry gets a `box` (SetPiece.add_box): side walls
    in the house's own material (shared story_houses_01 straw / _04 plank / _07 brick side-wall cards), an inside
    back wall (straw rows / planks / the plaster-and-brick room wall story_room_00), a plank floor and ceiling
    (story_room_03), and the front's print turned round at the back, so a door opens onto a dim interior and side
    views show a closed volume. The box stands only while the house is whole. No new art needed. house_stages.py
    writes wall_x (the wall's own width) for the side walls.
  - Entries checked at 8 fps (tiles artifacts/three_pigs/tiles/v10_*): wood house — door opens on the plank interior,
    첫째 walks in (back view) and is hidden by the front, door shuts; brick house — the brothers go in the same way.
    Runners now stop in front of the door (w_front / b_front) instead of beside the house (첫째 had looped round it).
  - Camera settles on the house (cam at the house focus) before each door entry (the run had half-framed the brick
    house). Brick lot shifted [-0.5, -0.2] in the village frame with all its spots (it sat right behind the wood house);
    SET_CHECK still road=0 water=0 for every piece. The ladder lies in the grass until the wolf finds it and stands
    it up at the start of the chimney beat (fx ladder_up).
  - Verify: check_all clean; three_pigs STORY_DONE 275.0 s missing_audio=[]. Videos: artifacts/video/three_pigs_full_v10.mp4,
    three_pigs_escape_v10.mp4. Still off: inside the doorway the interior is a plain back wall (no furniture in the
    straw / wood houses); the first entry tile came from a run before the door-front fix (the final run uses it).

## 2026-11-19 — three_pigs v11: one clean door cycle at the brick house
  - Coordinator (2 fps crops of escape_v10): 둘째 turned to a front view in the doorway, the door closed over him and
    reopened. go_inside now queues the runners one behind the other in front of the door, opens it once, sends them
    in one after the other (back view through the doorway; the second steps sideways to the doorway in side view),
    and shuts it once after the last is inside. Doorway crops: artifacts/three_pigs/tiles/v11_brick_entry_2fps.jpg.
  - three_pigs STORY_DONE 275.7 s missing_audio=[]. Videos: artifacts/video/three_pigs_full_v11.mp4,
    three_pigs_escape_v11.mp4.

## 2026-11-19 — three_pigs v12: drawn run cycles for the pigs
  - User: "돼지 옆으로 달려가는 모습 이상해유" (a rigid scared card hopping sideways, an edge-on sliver at the turn). New
    shared cast sheets cast_pig_{a,b,c}_run_cycle (Codex, ANIMAL_STYLE, refs the lineup, run in parallel; raw md5s
    716f480e / ec7aa4f4 / d15f8eac, unique; contact artifacts/three_pigs/run_cycle_contact.png): per pig 4 side
    profile frames (contact, down, passing, flight; legs apart, arms pumping, scared face) and 2 back-view run frames,
    padded to one canvas per pig, catalogued as cycles run_cycle / run_back. CastPuppet plays a cycle as a flipbook
    advanced by ground distance (one cycle per 0.9 × height), bounce on the flight frame, mirrored for leftward runs;
    StoryActor uses the cycle for its view when a walk runs (pose run, speed ≥ 0.4). Paper turns narrow to 15 %
    (never edge-on). Tiles: artifacts/three_pigs/tiles/v12_*. three_pigs STORY_DONE 275.1 s missing_audio=[];
    videos artifacts/video/three_pigs_full_v12.mp4, three_pigs_escape_v12.mp4.

## 2026-11-19 — three_pigs v13: every walk is a drawn cycle
  - User: "늑대도 이상한디요?" / "이전 걸음 이상해요". New shared cast sheets (Codex, ANIMAL_STYLE, md5-unique, looked at
    before slicing; tools/cast/add_cycles.py slices a sheet into catalogued flipbook frames): wolf walk_cycle (4 side
    sneak frames, leaning forward, knees bent, paws up, tail swinging) + walk_back (2), wolf run_cycle (4, scalded
    'ouch' run), wolf walk_front (2) + run_front (2; the two run frames lift the same leg — weak alternation);
    per pig walk_cycle (4 side, calm happy face) + walk_back (2) + walk_front (2); 첫째 carry_straw_cycle (4 side,
    straw bundle in his arms). Contacts: artifacts/three_pigs/wolf_cycle_contact.png, run_cycle_contact.png.
  - Which move uses which cycle (StoryActor picks by the camera-relative travel view):
    pigs leaving mom's home → walk_back; 첫째 carrying straw → carry_straw_cycle; walks to doorways, the brothers'
    tease walk and walks home → walk_cycle (side) / walk_back / walk_front by direction; escapes → run_cycle /
    run_back; the second brother stepping to the brick door → walk_cycle. Wolf arrivals, road walks between houses and
    the ladder approach → walk_cycle / walk_back / walk_front, stopping in a standing sniff at the straw house
    (end_pose); the ladder climb → walk_back with a rung bob; the run-away → run_cycle. Mom does not walk. The
    leg-swapping rig is no longer used by any three_pigs walk.
  - Camera follows the wolf to his mark (straw arrival, ladder approach, run-away). three_pigs STORY_DONE 276.3 s
    missing_audio=[]. Videos: artifacts/video/three_pigs_full_v13.mp4, three_pigs_escape_v13.mp4; tiles
    artifacts/three_pigs/tiles/v13_*.

## 2026-11-19 — three_pigs v14: direction and camera pass (user-approved shot plan)
  - Engine (shared, sun_wind unchanged: walker pages keep the road camera): shots take a yaw offset; `cam` takes from
    (snap first: crane / push / pull / cut), rate, shake, follow; every stage shot drifts a little (hand-held);
    SpreadStage.shake(); light presets afternoon / late / dusk / night / evening (eased); tale `backdrop` gives the
    area behind the hills the haze colour (deep blue at night) so high / tilt-up / glide shots never show black;
    huff takes cam_result / shake; end takes close_book (the page folds shut into the end card); the cover builds
    the first spread at 28 ms/frame. Documented in references/script_schema.md; skill "Direction" section.
  - Shot plan (tools/story/tales/three_pigs.py): crane down into mom's home, close on mom, high-angle departure;
    village establishing crane over the empty lots; builds with their own rhythm (straw quick, wood camera bump per
    hammer, brick slow with late light) and a low-angle push-in at each completion; brothers' tease two-shot; the
    wolf's entrance low and menacing (a cut — a glide across the village flew through the straw roof), OTS toward
    the house, window close-up for "싫어요", cheeks close-up with a shake per huff and a wide cut for the result,
    the brick house frontal and steady at dusk; escapes tracked from a high angle; chimney at night, inside warm,
    "앗, 뜨거워!" with a shake, the camera following him up out of the chimney; ending in warm evening with lit
    windows, a slow pull-back and the book closing.
  - Verify: check_all clean. three_pigs STORY_DONE 279.0 s (v13 276.3 s, +2.7 s) missing_audio=[]; sun_wind STORY_DONE
    203.4 s missing_audio=[]. Videos: artifacts/video/three_pigs_full_v14.mp4 (25.7 MB, crf 32),
    three_pigs_wolf_entrance_v14.mp4, three_pigs_chimney_v14.mp4; tiles artifacts/three_pigs/tiles/v14_*.
  - Still off: the establishing shot shows the road and empty meadow more than the three lots; close-ups are tight
    on flat cards (no edge seen in the review, but faces are large paper cards); the ladder card has the meadow
    flower print.

## 2026-11-19 — three_pigs v15: review fixes on the camera pass
  - "Two wood fronts side by side" at the window close-up: one house in every full-res frame; the close-up cropped
    both gable ends so neighbouring 2.5 s tiles joined into a double front. Now a "front" shot (whole front, both
    windows, grass around it). Straw "싫어요": a "window" shot centred on the round window (spot s_win) — 첫째's peek
    fills it. Night backdrop lightened to navy (no near-black band on the launch / night village). Ending: the family
    in front of the lit house for "행복하게 살았어요", then the pull-back and the book closing. Ladder: a story copy
    story_build_props_23 with the flower print painted out (the shared meadow card is unchanged; faint dark stem
    traces remain). Full-res checks: artifacts/three_pigs/tiles/v15_fix_checks.jpg.
  - three_pigs STORY_DONE 281.5 s missing_audio=[]. Video: artifacts/video/three_pigs_full_v15.mp4.

## 2026-11-19 — three_pigs v16: user fixes (double 그럼, huff two-shot, smoke, tap framing, quote timing)
  - "그럼 두 번": the generated wolf clips wolf_2060345d9c (tp_028) and wolf_61e2f65ffa (tp_032 / tp_044) start with a
    faint first "그럼" (envelope 0.09-0.35 s / 0.09-0.40 s) before the loud one; nothing was double-played by the
    engine. Trimmed before the loud onset (0.52 s / 0.90 s, 40 ms fade-in) -> *_t.mp3, via TRIM_SEG in the tale table
    (seed_script supports per-seg trims). No new recording. The recorded wolf line now opens on the single "그럼".
  - Huff: a two-shot "huff_two" (wolf face left, house right, spot between them) instead of the cheeks close-up.
  - Brick chimney smoke: the template's chimney smoke under story houses is hidden; story chimney steam only once the
    pot boils. The inner flue is shown only while the camera is inside (it poked over the roof), the turned-round
    back copy of the front is gone (its plain back showed above the roof), wider meadow clear around the brick house.
  - Tap framing: every interactive step (tap, tap_each, build, huff, tap_steps) frames its targets before the prompt
    and holds (SpreadStage.frame_targets: all on screen, ≥ ~80 pt). sun_wind's walker pages keep their story shot
    (their targets are already framed).
  - Quotes at the mark: tp_027 / tp_031 / tp_043 split — the narrator seg plays during the walk, the wolf's
    "아기 돼지야, 문 열어라!" only once he stands at his mark (`segs` on say / walk).
  - Still off: a dark brick column stands behind the brick house's chimney in the night exterior (not a kitchen piece;
    likely the band card's cut edge seen at an angle).
  - three_pigs STORY_DONE 280.5 s, sun_wind 203.3 s, missing_audio=[] for both. Video: artifacts/video/three_pigs_full_v16.mp4.

## 2026-11-19 — three_pigs v17: staged sound wired in-engine; the wolf runs away
  - Sound (artifacts/audio_staging/WIRING.md): 81 sfx + 6 CC0 music tracks copied to game/audio/{sfx,music}
    (+ music/CREDITS.md), catalog game/audio/sound_catalog.json. New shared game/core/audio/sound_director.gd: one-shot
    pool (12 3D + 6 2D), music slots with crossfades, beds per spread light ("@light"), sprinkle scheduler (birds,
    cuckoo, dove, bee, frogs, owl) at tree crowns (MeadowWorld.trees) / the water, a stream emitter sliding along
    GroundLayers.stream_line_3d() nearest the camera focus, 3 leaf-rustle emitters at trees swelling with gusts,
    gusts from beds, the meadow sway envelope (≥ 7 s apart) and huffs (by tap), footsteps on drawn-cycle contact
    frames (CastPuppet.foot_contact → StoryActor → surface grass / road / bridge / roof / ladder), fx / step cues
    from the tale's `sound` blocks (seed table SOUND from tools/audio/three_pigs_sound_blocks.json + per-beat blocks).
    Buses Voice / Music / Ambience / SFX created in code, Master hard limiter -1 dB; ducking: Music -7 dB, Ambience
    -3 dB while a line plays (deterministic envelope from _say — the spec's fallback, chosen over sidechain
    compressors for predictability). PaperAudio on SFX, the voice player on Voice. Hooks: cover open, page turns,
    door open / shut, book close, counter tick (pitch scale), wolf sniff at his mark, landing thud. `--log-sound`
    prints SFX lines; STORY_DONE reports missing_sound. fx.gd: the cheer no longer fires on the straw / wood ruins.
    sun_wind adopted the ambience (day bed, stream + trees, page / book sounds; no music).
  - Bug found: contact frames from JSON are floats, Array.has(int) never matched → no drawn-cycle steps; fixed.
  - Wolf run-away (user: "마지막에 늑대가 도망가서 달려야 되지 않을까?"): he shoots out of the chimney, lands beside the
    house (thud, dust, hop, yelp), runs off in the scalded side-run cycle with smoke puffs from his bottom along
    explicit road waypoints past the brick house, turns to the back run and shrinks down the road; the camera follows
    from a high angle for 3.6 s, then holds down the road. (The first try started the run during the flight and
    the landing cancelled it.) Tiles: artifacts/three_pigs/tiles/v17_wolf_*.
  - Verify: check_all clean; three_pigs STORY_DONE 284.4 s missing_audio=[] missing_sound=[]; sun_wind 203.6 s,
    both []. v17 capture: integrated -16.1 LUFS, LRA 8.7 LU, true peak -0.4 dBFS (above the -1 dB target: the AAC
    encode overshoots the limiter; lower the ceiling to -2 dB next pass). 455 cues; cue times match the frames
    (straw blow, wood collapse, landing thud, door creak: artifacts/three_pigs/tiles/v17_cue_alignment.jpg).
    Video: artifacts/video/three_pigs_full_v17.mp4 (29.0 MB). Nobody has listened to it.

## 2026-11-19 — three_pigs v18: empty lots until each build, no materials at home, line-order guard
  - "둘째돼지집 짓기도 전에 있음": the wood house's foundation stood from the village page open (stage 1). Now every
    house, pile and the bucket starts hidden (stage 0) and rises at its own build (fx `up:<set>[:bands]`: straw pile at
    straw_build, wood pile + foundation at wood_build, brick pile + bucket at brick_build, ui.pop / hammer sound);
    `built` lists for later beats name everything standing by then. Frames: home, village arrival, straw / wood / brick
    starts all show empty lots (artifacts/three_pigs/tiles/v18_lots_before_builds.jpg).
  - "돼지 세 마리 갈 때 짚이랑 벽돌을 왜 가지고 있지?": the home page no longer has the straw / plank / brick cards that
    popped beside each piglet on its tap; a tap is a wave + hop. They leave in the plain back-walk cycle, empty-handed.
    Checked the other early poses: hammer, flute, violin, bricks and the straw-carry walk appear only in their builds.
  - "늑대 대사 사라진듯": not missing — v17's audio has the wolf's "아기 돼지야, 문 열어라!" at all three doors (envelope
    correlation with the clip 0.76 / 0.73 / 0.72), narration during the walk, quote at the mark.
  - Regression guard tools/story/check_lines.py: StoryRunner prints `SEG <line> <i> t=` per spoken segment; the checker
    walks the script's steps and fails on any missing, doubled or out-of-order segment and on used lines never played.
    It caught sun_wind's sw_n04 (tap prompt removed but still marked used: the seeder marked every NEW line used —
    now only when a beat plays it). three_pigs OK 39 segments, sun_wind OK 42.
  - three_pigs STORY_DONE 293.9 s, sun_wind 203.5 s, missing_audio=[] missing_sound=[]. Video
    artifacts/video/three_pigs_full_v18.mp4 (29.8 MB).

## 2026-11-19 — three_pigs v19: the wolf's quote follows his arrival; build taps framed with margins
  - The narrator part of tp_027 / tp_031 / tp_043 now plays late in the wolf's walk (`line_late`: started so it ends
    as he arrives, from the route length / speed); the walks to the wood and brick houses are faster (0.95); the
    camera cuts to the OTS 0.15 s after he stops and the quote follows (narration → quote 5.6 / 4.1 / 4.3 s apart, was
    ~9 s at the wood house; quote ~1.5-1.8 s after the narration ends). The step waits for a late line before going
    on, so narration and quote never overlap.
  - Tap framing: the whole tap ring must be inside the frame with a margin (5 % sides, 6 % top, 18 % bottom for the
    caption); build steps frame the target and the builder. straw_build's pile and 첫째 are fully in frame at the taps
    (artifacts/three_pigs/tiles/v19_straw_build_framing.jpg). Growing houses reframe between taps (+~5 s on the wood
    and brick builds).
  - three_pigs STORY_DONE 308.8 s, CHECK_LINES OK (39 segments), missing_audio=[] missing_sound=[].
    Video artifacts/video/three_pigs_full_v19.mp4.

## 2026-11-19 — three_pigs v20: each build framed once, held for every tap
  - New `frame` step / SpreadStage.frame_build(house, with): one shot that fits the FINISHED house (full width and
    height), the pile, the builder (and the brothers' tease spot for the brick build), set before the build's intro
    line and held for all three taps; build taps no longer reframe (`_wait_tap(..., reframe=false)`), the brothers'
    tease plays in the same shot (no two-shot cut mid-build).
  - The tap ring around a house mid-build sizes to the walls standing now (it used the finished height: the brick
    ring ran off the bottom of the frame at the first tap).
  - Checked every tap of all three builds (artifacts/three_pigs/tiles/v20_build_taps.jpg): houses uncut at all edges,
    including the finished straw roof, wood roof and brick chimney; every ring fully inside the frame.
  - Runtime: trimmed the establishing crane wait (2.6 → 1.8 s), the framing waits and two music_stop holds.
    three_pigs STORY_DONE 295.0 s (v19 308.8), CHECK_LINES OK 39; sun_wind 205.8 s, CHECK_LINES OK 42;
    missing_audio=[] missing_sound=[]. Video artifacts/video/three_pigs_full_v20.mp4 (26.4 MB).

## 2026-11-19 — witch_candy phase 1: plan, script, shared art, world prototype (not wired)
  - Plan game/stories/witch_candy/PLAN.md. User decisions: magic play, not a lesson; two rounds + the ghost candy
    finale; 다현이 kept (톡톡 recordings reused); 5-6 min. Branches: the shelf holds 9 ingredients in three colour groups
    (red / yellow / blue; green dropped), two picks auto-stir, the colour set picks one of 6 results (strawberry, duck,
    fish, pumpkin, bat, frog): every pick has its own result, all their lines are recorded, and the same six looks serve
    the finale (rabbit frog, bear duck, fox bat, cat fish, witch pumpkin, Dahyun strawberry). Autoplay: random pair with
    an unseen result.
  - Places: ONE spread. The Halloween street (night dress of the village on the meadow template, view 5's straight road)
    with the candy shop at its end; the shop is a house with a body and the room inside its footprint, so going in /
    out is a camera glide through the door (no page turn after the cover). The `interior` RoomBox template is designed
    to work inside a set piece's box or as its own spread (phase 2).
  - Script: tools/story/tales/witch_candy.py → game/stories/witch_candy/script.json: 96 used lines, 92 reuse (91 clips
    copied to game/audio/voice/witch_candy/), wc_039 trimmed (the colour-mixing sentence cut at its pauses, 0.42-3.62 s),
    the ghost / happy choruses from 톡톡's premixed clips, 4 NEW lines (cover, replay, catch-the-invitations, give
    candies: 75 characters) not recorded. Dropped: colour questions / answers / explanations, counting, chocolate /
    kiwi / crocodile, the friends' chorus lines. Narration ≈ 206 s per run; estimate 5:20-5:40.
    Seeder: nested line ids in step tables count as used (branch tables); TRIM takes an optional speaker (chorus).
    sun_wind / three_pigs reseeds byte-identical.
  - Art (Codex magenta pipeline, tools/art/witch_candy_jobs.py, 30 sheets incl. 8 regenerations, all raws md5-unique):
    shared cast dahyun / candy_witch / hobak_cat / rabbit_kid / bear_kid / fox_kid: 53 standing figures (expressions,
    side / back standing, ghost black lips, 6 Dahyun transformations + strawberry ball + bat wing frames, finale
    transformations of the friends, cat and witch) and 13 drawn cycle sheets (walk 8 for all six, ghost march 6 for all
    six, Dahyun's duck waddle 4) = 88 frames. Atlas: story_wc_ingredients / pot / candies / halloween / shop / room
    (75 cards + a derived full-height back wall), categories story_prop / story_fx / story_building, biome halloween.
    Contact sheets artifacts/witch_candy/*.png. Fixes on the way: friends' cycles first came out as Dahyun (lineup ref)
    → single-character ref crops; ghost lips needed "jet-black lipstick" wording; the keyer punched holes in purples
    and turned the witch's dress green → tools/atlas/fill_holes.py (enclosed holes + interior despill undo), run by
    add_sheet.py and add_cycles.py. New tools: tools/atlas/add_sheet.py (one sheet into the catalog, no rebuild),
    tools/cast/witch_candy_cast.py (merging cast builder), tools/atlas/wc_shop_door.py (door pasted into the drawn
    doorway; house_stages DOORS cuts the leaf above the steps), tools/atlas/wc_room_wall.py.
  - World prototype on the real engine: game/stories/witch_candy/proto/ (tools/story/wc_proto.py; --tale=witch_candy/proto):
    street + shop with its box + the room inside, warm omni lights from a proto handler. Stills
    artifacts/witch_candy/proto_street.jpg, proto_room.jpg. SET_CHECK: shop / houses road=0 water=0.
  - Still off (prototype): the street sky reads as grey-green haze, not a night sky, and the moon card stands over the
    stream far behind (needs the sky hanger + a night backdrop); lamp_l / p1 touch the road edge (SET_CHECK road 5 / 2);
    the room is warm but over-bright; Dahyun hides the shelf in the room still and the friends stand off-frame. The
    shop's open door / go-inside have not been exercised. Nobody has listened to the trimmed wc_039 clip.
  - Regression: three_pigs STORY_DONE 295.3 s, CHECK_LINES OK 39; sun_wind 206.0 s, CHECK_LINES OK 42; both
    missing_audio=[] missing_sound=[]. Skill: lessons for branching tales, refs, purples vs the key, safe catalog tools.

## 2026-11-20 — witch_candy phase 2 v1: a dressed Halloween village, night sky, the shop room, every beat wired
  - User on the prototype: "마을을 더 많이 각자 할로윈 장식". New Codex sheets (md5-unique, contact sheets in
    artifacts/witch_candy/): story_wc_houses_a / _b (14 night facades, each dressed differently: pumpkins on steps,
    bunting, cobwebs, lit windows with bat / cat / witch-hat silhouettes, wreath, scarecrow, lanterns, fence of
    jack-o'-lanterns, a pumpkin house) and story_wc_decor (18 add-ons incl. two light strings). 13 houses line view 5's
    street on both sides and down the road, each with its own add-ons; two light strings across the street; lamps and
    pumpkins on the verges (SET_CHECK road=0 water=0 for all but the light strings, whose cords cross by design).
  - Night: spread `sky` (deep-blue backdrop and haze, fog-free sky card with printed stars, the moon card and star cards
    far behind the street, not over the stream), paper_print `glow` (bright warm printed light emits: lit windows,
    lanterns), set `light` (warm pools at windows, lamps, flickering pumpkins / candles). Room: full-height back wall,
    raised plank floor, warmer and dimmer (beam lantern + fire light growing with the flames), Dahyun right of the
    shelf, the friends behind the pot (in the room shot).
  - Engine (generic; sun_wind / three_pigs unchanged): handler tale verbs (`run_step`), go_inside `to` + `queue`, walk
    `file` (single file), `<pose>_front/_back` cycles, set glow / light, spread sky, hit test prefers awaited targets,
    no outdoor reframing while the camera is inside a house, branch-aware check_lines (`PLAN brew<n>` lines).
  - Tale (game/stories/witch_candy/fx.gd): invitations to catch, shop lights on, three flames, the shelf of nine, `brew`
    (picks fly into the pot, colour swirl bands, magic stir, POOF, candy, eat, 뿅), the six actions (strawberry roll
    down the street to the pumpkin, duck waddle round the pot with 호박이, fish swim / bat flight over the street in
    front of the moon, frog hops onto the shop roof, pumpkin glow in the dimmed street), the ghost candy, the parade
    with a little ghost tagging along, the candy fountain and the finale transformations.
  - Sound: 25 wc.* placeholder SFX synthesised (tools/audio/wc_synth_sfx.py, WAV; nobody has listened), beds / music /
    footsteps in the tale's sound block. Voice: wc_n01–n04 unapproved → caption-only (pending).
  - All six results played in forced runs (--wc-results=a,b): duck + pumpkin, strawberry + fish (366.9 s), frog + bat
    (354.5 s); bugs fixed on the way: a glide fed its own hop back as height (Dahyun flew off into the sky), --beat
    starts left the cast at the anchor, outdoor actions hidden behind the house in front of the shop (now via the
    road), a tracking shot clipping through a roof (now above the roofs), the bat a speck in the sky (loop closer).
  - Official run (random results: fish, pumpkin, then the ghost candy): STORY_DONE 356.2 s (5:56), CHECK_LINES OK
    (56 segments, branch plans), missing_audio = the 4 pending new lines (caption-only), missing_sound=[], no script
    errors. Videos: artifacts/video/witch_candy_full_v1.mp4 (26.3 MB, 1024 px), witch_candy_round_v1.mp4 (round 1),
    witch_candy_village_v1.mp4 (slow street tour); beat sheets artifacts/witch_candy/beats_v1/, contact
    artifacts/witch_candy/full_v1_contact.jpg, tour artifacts/witch_candy/village_tour_v1.jpg.
  - Regression: three_pigs STORY_DONE 295.3 s (unchanged; the "no reframing inside" guard is opt-in per tale
    `inside_framing: manual`), sun_wind 206.1 s, both CHECK_LINES OK, missing_audio=[] missing_sound=[].
  - Still off: the candy fountain hardly reads; in the finale the friends stand behind Dahyun and the pot (their tap
    rings and frog / duck / bat looks are half hidden) and 호박이 is mostly hidden; the bat / fish flights are small
    against the sky; the shelf ingredients are small cards (tap rings OK in autoplay, not tried by hand); the
    transformation "뿅" is a star / smoke burst only; nobody has listened to the placeholder SFX or the mix.

## 2026-11-20 — witch_candy v2: houses face the road, the greeting in full view, clean door entries
  - User on v1: "처음 마녀가 인사할때 앞의 집때문에 안보여. 집 문이 길쪽으로 나있어야 미국식 집 구조 ... 카메라를 회전해서
    인사하면 ... 집으로 들어갈때 문에 겹친다던지 문 아래 돌지방을 통과하던지 이런게 없어야".
  - Houses face the road: every house turns toward the street (left side +50°, right side -50°, the candy shop -45°),
    facing each other across it, each first-row house with a stepping-stone path from its door to the road's edge (the
    shop's path runs to the road); decorations placed in each house's own frame; SET_CHECK road=0 water=0 for every
    piece except the two light strings across the street. The room, its spots and every interior shot turn with the
    shop (tale table `_rot`, shot yaw = SHOP_YAW).
  - Greeting: the camera turns round to face the shop door straight on from the road (`door_cam`); the lamp that then
    stood in the line moved beside the shop; the witch leads everyone in and the small cat waits last, so nobody fills
    the lens; entries and exits use a raised wide door shot (`door_wide`) with the path and the file in view.
  - Entries without clipping: the shop door swings INTO the house (`door_in`) and fully open before anyone moves
    (`door_clear`); characters climb in front of the wall to the drawn sill (`climb_steps`, SetPiece.door_sill), cross
    at sill height and step down inside, one at a time in a tidy file along the path; exits reverse it (tale verb
    `leave_shop`, Dahyun's own exits / returns too). The witch is sized to fit the doorway (0.42 tall) — her hat poked
    over the wall on the sill. Checked with 8 fps zoomed tiles of the entries.
  - Checklist (references/checklist.md): houses face the road; no set piece in front of a speaker (orbit the camera);
    entries climb the steps with no overlap of door or threshold stone.
  - Runs: witch_candy STORY_DONE 367.1 s (6:07; v1 356.2 s — the one-at-a-time door entries / exits and the
    parade's exit cost ~11 s after trimming walk speeds), CHECK_LINES OK (55 segments; pumpkin, frog, ghost), no
    script errors, SET_CHECK zero except the two light strings; three_pigs 295.3 s, sun_wind 206.1 s, both
    CHECK_LINES OK, missing_audio=[] missing_sound=[]. Videos: artifacts/video/witch_candy_full_v2.mp4 (27.0 MB),
    witch_candy_village_v2.mp4; beat sheets artifacts/witch_candy/beats_v2/, door tiles
    artifacts/witch_candy/tiles_v2/ (8 fps zoomed: entries and exits), tour artifacts/witch_candy/village_tour_v2.jpg.
  - Still off: 6:07 is just over 6 min; in the close door shot the queue's last two (fox, cat) stand large in the
    foreground while the others go in; turned houses seen from the down-street camera show as angled flat fronts (no
    side walls on the village houses; only the shop has a body); the finale friends still stand half behind
    Dahyun and the pot; placeholder SFX unheard; wc_n01-n04 caption-only.

## 2026-11-20 — witch_candy v3: flying invite, houses with bodies, the ghost set piece, an overlap pass
  - User on v2: "초대장이 날아왔으면 좋겠고, 사선으로 돼 있으니까 집도 집처럼"; then "유령 ... 극적으로", corrected to "유령이
    처음엔 나온지 몰라야지 나중에 놀라는거"; "물체랑 사람들끼리 자꾸 겹치잖아"; "유령 사탕먹은 입도 제대로 ... 집밖으로 나오는것도
    좀 더 극적으로 ... 다른 집들로 인해 시야가 안가리면". Runtime target relaxed to ~6–6.5 min ("6분 7초도 상관없어").
  - Invitation: four cards ride the wind in from the end of the street on curving paths, flipping and tumbling, the
    camera following one (handler `_track` drives the stage focus); flutter sounds; they hover over the kids with
    big tap rings; caught, each opens beside its catcher's shoulder toward the camera.
  - Houses with bodies: tools/atlas/wc_house_bodies.py (wall / roof split, side strip of the house's own wall, roof
    print, eaves + ridge; contact artifacts/witch_candy/house_bodies.png); SetPiece `box.body` builds side walls, a
    back, two roof slopes and the gable at the back. The village tour shows roofs running back over windowed sides.
  - Ghost candy round: the little ghost sneaks in with four glimpses nobody notices (out of the pot steam behind the
    friends, over the witch's shoulder, over the pot rim, mimicking the ghost pose at the back); build-up (lights dim
    and flicker, music drops, the pot glows green, smoke curls, the black candy rises slowly), the eat POOF with a
    shake, a black-lips close-up with white wisps puffing out on "오~우~", the friends' black lips close; then the
    surprise nose to nose (sting, snap zoom, shake, everyone jumps), the roam (round the room and the pot, past the
    shelf with the jars jumping, between the friends who hop, out of the door, a loop over the street in front of the
    moon, back in) and a 까꿍. New placeholder sounds wc.sting / eerie / swoosh / peekaboo / burst.
  - Dramatic exits: the door bursts open in a spill of warm light, a low hero shot on the doorstep, sparkles and a
    music lift, then the action with its camera move.
  - Overlaps: stage `spacing` solver and `overlap_check` (OVERLAP / OCCLUDE log lines, totals at the end). First
    measured run: OVERLAP 72, OCCLUDE 36 (OCCLUDE mostly false — fixed: only what the camera can see, upper body).
    Real sources fixed: the group walk converging (now by distance), file followers bunching / a tight U-turn (now
    snake-follow on the leader's trail and a wide two-lane loop), people cutting through the pot (via waypoints, who
    enters first), the door queue reaching the next house (queue along the shop front, house moved). Final run:
    OVERLAP 3, OCCLUDE 1 (listed below).
  - Runs: witch_candy STORY_DONE 401.8 s (6:42), CHECK_LINES OK (55 segments; pumpkin, fish, ghost), no script errors;
    three_pigs 295.4–296.9 s (the spread across runs is the cover's time-sliced first build), sun_wind 206.3 s, both
    CHECK_LINES OK. Videos: artifacts/video/witch_candy_full_v3.mp4 (28.5 MB), witch_candy_village_v3.mp4,
    witch_candy_invite_v3.mp4, witch_candy_ghost_v3.mp4; beat sheets artifacts/witch_candy/beats_v3/.
  - Still off: OVERLAP rabbit / fox and bear / house_7 for a moment while the door queue forms, witch / cat as they
    file out for the parade, OCCLUDE bear behind the pot in the low fire shot; a green smoke puff from the pot drifts
    over the rabbit's face in the black-lips shots; the ghost glimpses are small (not checked by a child's eye);
    the duck result stays inside (no doorstep exit); 6:42 is above the relaxed 6–6.5 min; placeholder sounds unheard;
    wc_n01-n04 caption-only.
