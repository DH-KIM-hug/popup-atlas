# 팝업 동화 (Pop-up Storybook) — brief, contracts, component checklist

Lead-owned. Components may propose changes to contracts in their report; only the lead edits this file.

## Product (user decisions, 2026-11-18)
- iPad app, **Godot 4.7.2**, Mobile renderer (Metal). Project at `game/`. The old web prototype at the repo root
  (`src/`, `public/`, Vite) is superseded and kept only for reference.
- A story app in a **pop-up-book concept**: each page/scene folds up out of the open book like a real pop-up book;
  characters can walk around the diorama.
- First story: **「해와 바람」** (sun_wind). Source app 톡톡 동화극장 (`~/projects/2026/patjuk-game`).
  Reuse **only** the voice script (`tales/sun_wind/voice_script_el.json`, recorded audio) and **character designs**
  (`assets/v3w/sw_trav_*`, `sw_sun`, `sw_wind*`, `sw_hat`, `sw_coat`). Everything else (backgrounds, props, scenes,
  code) is made new. Backgrounds may be shared across future stories.
- Quality bar: the user's screen recording `art_src/reference/video/v_*.jpg` (papercraft diorama world) and the
  6-frame sheet `art_src/reference/r1..r6`. Use them for look and density only; never copy their assets or layouts.
- Loop until a blind critic can't reliably pick the reference over ours and is impressed.

## Style rules for this app (supersede 톡톡 CLAUDE.md 7-1 where they conflict — dated 2026-11-18)
- Everything is **cut cardstock**: flat printed cards with visible thickness (cream core on the cut edge),
  standing on the page on hinges. Pop-up folds happen only at hinge lines; cards themselves never bend.
- Perspective comes from the 3D camera only. Cards are drawn flat, front-on, like die-cut pop-up pieces.
- Cards carry printed illustration detail (leaf veins, folk-art motifs, stitched/stamped texture) like the reference
  video, in the 톡톡 cut-paper character style. 1 piece = 1 base colour plus printed detail; no gloss, no photo texture.
- Trees/bushes may be **cross-slotted card pairs** (two cards at 90°, the second collapsing as the hinge folds).
- Characters keep their 톡톡 designs (faces, clothes, proportions).
- Light: warm low key light (late afternoon) + cool fill; glow from windows/lanterns allowed as light, not paint.

## World contracts
- Units: 1 unit = 10 cm of paper. Page surface y = 0, +X right, +Z toward camera.
- Traveller standing height 0.36. Small props 0.15–0.35, bushes 0.2–0.4, trees 0.6–1.1, houses 0.7–1.0.
- `PaperCard` (`core/paper_card.gd`): texture with alpha → extruded card, origin bottom-centre, faces +Z.
  Card art = RGBA PNG/WebP, transparent background, subject touching the bottom edge (that edge is the hinge).
- `PopHinge` (`core/pop_hinge.gd`): parent of cards; `pop_up(delay)`, `fold_down(delay)`, `snap(up)`;
  signal `flapped(up, weight)` for sound, `settled(up)`.
- Camera: high angle 40–55°, fov 20–28, focus on the traveller, DOF near+far for tilt-shift.
- Capture: `gd_run.capture_scene(game, scene, size=(1366,1024))` (iPad 4:3 landscape). Metrics:
  `python3 tools/look/look_metrics.py IMG`.

## Measurable look targets (from reference video daytime frames v_01,03,04,05,06,12,13,14)
| metric | reference range | look_v3 (2026-11-18 start) |
|---|---|---|
| lum_mean | 0.34 – 0.55 | 0.62 |
| lum_p05 (shadow depth) | 0.09 – 0.22 | 0.36 |
| lum_p95 | 0.56 – 0.81 | 0.83 |
| sat_mean | 0.49 – 0.66 | 0.39 |
| warmth (R−B) | 0.15 – 0.45 | 0.24 |
| tiltshift_ratio (mid sharp / top+bottom) | 1.3 – 2.5 | 2.24 |
| edge_density (prop busyness) | 0.06 – 0.11 | 0.057 |
| props in frame at default camera | ≥ 60 distinct cards | ~40 |

## Component checklist (one owner each; owner touches only its files)
| # | component | owns | done when |
|---|---|---|---|
| A | **Card art kit** — new pop-up prop cards for the 해와 바람 world (meadow, field, stream, hill, village edge, sky) | `game/art/cards/**`, `art_src/cards/**`, `tools/art/**` | ≥ 30 clean RGBA cards; blind critic rates kit ≥ reference-level on style/detail |
| B | **Look-dev** — lighting, colour grade, DOF, page/ground layering (felt green ground, cut-paper path & stream layers, book edge, table) | `game/core/shaders/**`, `game/scenes/look/**`, `game/core/look/**` | all metrics in range; blind A/B vs video ≤ 60 % pick rate for reference |
| C | **Pop-up motion + sound** — hinge spring feel, staggered waves, cross-slot collapse, paper flap/step SFX | `game/core/pop_hinge.gd`, `game/core/cross_card.gd`, `game/audio/**`, `game/core/audio/**` | critic on a capture sequence: overshoot+wobble reads as paper; 60 fps with 150 cards moving |
| D | **Characters & walking** — traveller paper puppet walk, tap-to-walk on the path, sun & wind hanging cards, follow camera | `game/core/characters/**`, `game/scenes/chars/**` | critic: walk reads as a paper toy, no foot sliding; camera follow smooth |
| E | **Story flow** — 해와 바람 scenes as pop-up spreads, narration playback, page turn, taps from the script | `game/story/**` | full story plays start→end with narration |
| F | **Performance** — iPad budget | profiling only, reports to lead | p95 frame ≤ 16.7 ms at 1366×1024 on Metal with the busiest scene |

## Critic protocol (every component)
- A separate critic agent that did not build the thing. It gets two images (or sequences) labelled X and Y in random
  order — one reference, one ours — with no hint which is which. It says which is better on each axis
  (paper feel, lighting, colour, density, detail, depth/DOF, charm) and lists concrete fixes for the worse one.
- Pass when, over ≥ 5 pairs, the critic picks the reference ≤ 60 % of the time and calls ours impressive.
- Revert any change that makes metrics or the critic verdict worse. Append every round to `artifacts/game-progress.md`.
