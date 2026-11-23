# script.json (game/stories/<tale_id>/script.json)

Top level: `tale_id`, `title`, `seeded_from` (톡톡 voice_script_el.json path), `clip_map_from` (톡톡 narration_el.js),
`voices` (speaker → ElevenLabs voice id, copied from 톡톡 — never invent ids), `models`, `settings`, `voice_notes`,
`cast` (role → {skin: cast id or skin name}), `moral`, `beats[]`, `lines[]`.

## beats[]
```json
{"id": "wind_turn", "title": "바람 차례", "enter": {"pose": "walk_calm"},
 "spread": {"seed": 1, "view": 0, "route": [2.8, -2.4]},
 "steps": [ {"do": "cam", "shot": "story"}, {"do": "say", "line": "sw_012"}, ... ]}
```
- `spread`: world template seed + view station; `route` = road offsets [start, end] the walker covers (choose the
  direction that walks TOWARD the camera). `null` for the cover.
- `title` shows on the page tab.

## step verbs used by sun_wind (runner: game/story/story_runner.gd)
| do | fields | meaning |
|---|---|---|
| cover | prompt | book cover, tap to open |
| cam | shot (wide/story/close) | camera shot on the template rig |
| say | line | play a line (captions) |
| tap | target, prompt, hint, react, lines | wait for a tap on a cast member, react fx, then lines |
| blow / shine | prompt, hint, more, steps[{need, fx, lines}] | hold/tap-progress interaction with staged payoffs |
| walk / walk_to / walk_away / stroll / stop | dist / place / speed | walker movement (stroll = keeps walking under narration) |
| pose | pose | puppet pose/expression |
| fx | fx | tale-specific effect handler (hat_off, wind_puff, leaves...) |
| snap | key | screen photo kept for flashbacks |
| flash | key, side, line | show a kept photo while a line plays |
| quiz | prompt, answer, wrong{choice: lines}, right[lines] | picture-card choice |
| gentle | — | sun_wind specific (soft breeze) |
| end | — | end card + 다시 보기 |

## Data-driven stage (2026-11-18, three_pigs phase 2)
Top level: `handler` (res://stories/<tale>/fx.gd, a `TaleHandler`: tale-only fx), `shots` ({name: [distance,
elevation°, focus height, fov]}; "wide" = the template view), `ui` ({cover: [[cast id, px]...], end: [...],
speakers: {sp: [name, colour, cast id]}}), `cast` by `kind`:
| kind | node | fields |
|---|---|---|
| walker | the template road walker, CastPuppet skin | skin, height, gait{front_gait, step_period, min/max_stride, foot_lift, waddle_deg} |
| hanger | SkyHanger in the sky band of the story shot | skin, screen [x, y], frac (card h / frame h), sway, bob, seed, backing [fill, rim], backing_scale, backing_drop |
| actor | StoryActor: free walker, figure picked from travel direction | skin (cast catalog `skin`), height (default: calm figure height_units × 1.3) |
| prop | (handler makes cards) | skin |

Shots (`shots` top level): [distance, elevation°, focus height, fov, yaw offset° (optional)] — e.g. crane_high,
establish, high, medium, two_shot, face, low_up, low_wolf, ots (over the shoulder: yaw offset), cheeks, pull_back.
Walk steps take `follow` + `shot` for tracking; `huff` takes `cam_result` / `cam_result_at` (cut wide on the last tap)
and `shake` (per tap, default 0.9); `end` takes `close_book` (the page folds shut into the end card). Top-level
`backdrop: true` gives the area behind the far hills the haze colour (no black sky on high or tilt-up shots).
`spread.light`: "" | afternoon | late | dusk | night | evening (eased over ~2.5 s).
Spread fields: `place` (page key = seed:view:place; consecutive beats with the same key share the page and only
apply their `set` / `light` / `enter`), `spots` {name: [right, toward camera]} from the page anchor (template start,
template view frame; "anchor" = itself; also used as "focus"), `focus` (spot the stage camera looks at), `set`
[{card (atlas id), at (spot), off [right, toward], stage (bands standing at the pop: 0 = hidden until built /
popped, "full"), name, scale (× height_units, default 1.25), yaw, clear (× radius of meadow cards hidden around it,
0 = none)}], `light` ("dusk"). Use `tools/story/probe_spots.gd` (ground map: water / road / grass around the anchor)
before choosing spots — view 2's anchor sits on the stream.
`enter`: {who: {role: pose}, at: {role: spot}, inside: {role: [house set name, window index]}, left: {role: 0|1}, keep: [roles]};
`inside` actors stand just behind the front wall with their eyes at the window; they bob when they speak; a huff
that blows the house apart / collapses it reveals them (scared, hop) where it stood; actors not in `who` step off
the page on a same-page beat change unless kept.

## step verbs (generic, any tale)
| do | fields | meaning |
|---|---|---|
| walk | who (role / list), dir (toward / away / left / right), dist, to (spot), from (spot), pose, speed, line, exit, async, end_pose | actors walk; an actor not on the page steps in from `from` (or dist back along dir); figures follow the travel direction (front / back / side, side flipped), `pose` is used while walking when its view fits; exit = pops off at the end |
| pose | who, pose, left, hop, wait | standing figure of actors (no `who`: the walker) |
| go_inside | who, house, from (spot for actors not yet on the page), windows [index per actor], speed, line | each runs to the door, the door swings open, in through the doorway (back view), door shuts, the face appears in a die-cut window |
| climb | who, on (set piece), path [[x, y, z]] in set heights from its base centre, pose, speed, line | waypoints off the ground (roof, chimney) |
| tap_each | targets, prompt, hint, react {role: [pose, fx...]}, lines | every target once, any order |
| tap_steps | target, prompt, hint, steps [{target?, fx, lines, next, wait}] | one tap per step (generalised shine) |
| build | house (set name), target, taps, hint, walker, fx, counter, gap, steps [{at, fx, lines}] | band k folds up after k·taps/bands taps; fx sees stage.build_ctx {house, walker, tap, taps} |
| frame | house, with [targets / spots], wait | the build's one framing (finished house + pile + builder + extra spots), set before the build's intro; the next build of that house does not reframe |
| huff | house, taps, target (default wolf), who, prompt, hint, fx, counter, gap, result (blow_apart / collapse / hold), ruin (card id), huff_pose | each tap one 후~: blow_apart peels bands from the top, collapse rocks harder then tumbles, hold only shivers; the ruin set piece pops |
| cam_settle | frac (default 0.6) | wait until the camera move under way (e.g. an fx glide in through a door) has gone that fraction of its time; then the next line |
| cam | shot, at (spot, or a list of spots: their centre), settle (wait until the move has gone this fraction), from (shot: only on a spread's first cam step — the page opens on that framing under the turn, then glides; elsewhere ignored), cut (true: hard cut, only under a page turn), rate (default 2.4; <2.4 slower up to 3.2 s, >2.4 a bit quicker; the move's length comes from how far the view travels, 0.8–2.5 s), shake (°), follow (role: tracking shot), wait | camera move on a stage (non-walker) page: eased spring glide, velocity carried into the next move, yaw the short way; every stage shot drifts a little (hand-held) |
| fx | fx, wait | handler fx; generic `pop:<card id>` / `fold:<card id>` on set pieces |
| blow / shine / gentle / quiz | target / choices (default sun_wind's) | as before, targets from data |
`counter: true` on build / huff shows the tap count as a big printed number beside the house.
Line `expr` {role: pose | [pose per seg]} is applied by the runner as each seg starts (actors standing on the page).

## lines[]
```json
{"id": "sw_012", "speaker": "nar", "text": "…", "status": "reuse", "beat": "wind_turn", "used": true,
 "segs": [{"speaker": "nar", "text": "…", "emotion": "toneup:1.2", "tags": "[playful, …]",
           "audio": "res://audio/voice/sun_wind/nar_5782294768.mp3", "source_audio": "audio/el/…", "status": "reuse"}],
 "source_index": 12, "source_text": "…"}
```
Tale top level `theme` (sunmoon 2026-11-22): template dressing, "" (western meadow village) or "korean" (Joseon
countryside: man-made cards only from the korean_* sheets). `ground_style`: "" (felt) or "paper" (matte cut-paper
ground sheets; sunmoon). Read-mode lines (`READ_SCRIPT` in the seed table) carry
`source_read` "<scene key>#<line>" instead of `source_index`.
`status`: `reuse` (unchanged text, 톡톡 clip copied) | `changed-needs-recording` | `changed-recorded` | `pending`
(new line, recording not approved yet: plays caption-only for an estimated read time, listed in STORY_DONE
missing_audio; set via LINE_META in tools/story/tales/<tale>.py).
Add an `expr`/`pose` hint per line when the speaker's face must change (surprised, cold, hot…), so wiring is data.

## Buildings from the kit (2026-11-23)
Set entry: `{"build": "<preset>" | {spec}, "at": spot, "off", "yaw", "scale" (world units per spec unit, default 1),
"name", "clear", "stage" (0 = not yet standing), "state": {"portcullis": 0..1 (1 raised), "drawbridge": 0..1 (1 down)}}`.
A handler moves parts with `stage.set_piece(name).set_state("drawbridge", 0.0)` (eases at 0.6 / s).
Presets (game/art/buildings/kit.json, from tools/atlas/building_kit.py): octagon_pavilion (팔각정: curved giwa pyramid,
dancheong beams, red pillars, Korean railing, steps), gazebo (hexagonal, shingles), round_hut (thatch cone), round_tower
(slate cone), rapunzel_tower (2.1 tall, one high window + balcony, flag; reuse it alone), windmill_tower (octagonal
planks, shingle pyramid), two_storey (half-timber, terracotta hip, two floors of windows), hanok_l (two hip blocks in
an L, curved giwa eaves, lattice doors), pagoda (three tiers: skirt roofs onto the storey above, pyramid + finial),
castle (keep with battlements + slate hip, four round corner towers with cone roofs and flags, curtain walls with
battlements and a walkway, gatehouse with an arched passage, portcullis and drawbridge, a plank bridge).
Spec: `{"scale", "parts": [part...], "state"}`; every part has `type`, `name`, `at` [x, z], `yaw`, `base` (y of its
foot, to stack tiers) and:
| type | fields |
|---|---|
| block / tower | `shape` rect (`size` [w, d]) / ngon (`n`, `r`) / round (`r`, n 24) / poly (`pts`); `h`, `wall` (material), `thick`, `plinth` {h, mat, out}, `openings` [{edge (0 = front, then left, back, right / round the polygon), u (0..1 along the edge), w, h, y (sill), kind door / window / arch / gate, card (atlas id of the leaf, recessed in the reveal), open}], `crenel` {h, w, gap, d}, `roof` |
| pavilion | shape fields, `h` (pillar height), `platform`, `platform_mat`, `deck`, `pillar`, `pillar_r`, `beam`, `beam_h`, `railing` (card), `railing_h`, `steps` (front), `roof` |
| wall_run | `from` [x, z], `to`, `h`, `thick`, `wall`, `crenel` (both edges, walkway between) |
| gate | a rect block + `gate_w`, `gate_h` (arched passage through front and back with its vault and floor), `portcullis` (card), `drawbridge` (card) |
| stairs | `steps`, `w`, `rise`, `run`, `mat` |
| bridge | `from`, `to`, `y`, `w`, `thick`, `mat` |
| flag | `card`, `h` (sways) |
| card | `card`, `h`, `w` |
`roof`: {type gable / hip / pyramid / cone / skirt / flat / none, `h` (rise) or `pitch`, `overhang`, `mat`, `thick`,
`curve` (0..1 Korean upturned eaves + sagging slope), `ridge` "x" / "z", `lift`, `finial` (card), `finial_h`,
skirt: `upper_r` + `upper` {size / r of the storey above}}. The eave height is set so the roof surface passes the
wall tops (no slit); a gable's end walls follow the roof underside. Materials: plaster, fieldstone, ashlar, brick,
planks, halftimber, hanok_wall, terracotta, slate, thatch, giwa, dancheong, lacquer, shingle (`tile` = world size).
Compound buildings (castles) are parts placed relative to each other; parts that meet overlap a little inside each
other (a tower's wall cuts through the curtain wall's end) so no gap shows; never two coplanar faces (inset a wing
by a few mm).
