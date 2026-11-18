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

Spread fields: `place` (page key = seed:view:place; consecutive beats with the same key share the page and only
apply their `set` / `light` / `enter`), `spots` {name: [right, toward camera]} from the page anchor (template start,
template view frame; "anchor" = itself; also used as "focus"), `focus` (spot the stage camera looks at), `set`
[{card (atlas id), at (spot), off [right, toward], stage (bands standing at the pop: 0 = hidden until built /
popped, "full"), name, scale (× height_units, default 1.25), yaw, clear (× radius of meadow cards hidden around it,
0 = none)}], `light` ("dusk"). Use `tools/story/probe_spots.gd` (ground map: water / road / grass around the anchor)
before choosing spots — view 2's anchor sits on the stream.
`enter`: {who: {role: pose}, at: {role: spot}, left: {role: 0|1}, keep: [roles]}; actors not in `who` step off
the page on a same-page beat change unless kept.

## step verbs (generic, any tale)
| do | fields | meaning |
|---|---|---|
| walk | who (role / list), dir (toward / away / left / right), dist, to (spot), from (spot), pose, speed, line, exit, async, end_pose | actors walk; an actor not on the page steps in from `from` (or dist back along dir); figures follow the travel direction (front / back / side, side flipped), `pose` is used while walking when its view fits; exit = pops off at the end |
| pose | who, pose, left, hop, wait | standing figure of actors (no `who`: the walker) |
| climb | who, on (set piece), path [[x, y, z]] in set heights from its base centre, pose, speed, line | waypoints off the ground (roof, chimney) |
| tap_each | targets, prompt, hint, react {role: [pose, fx...]}, lines | every target once, any order |
| tap_steps | target, prompt, hint, steps [{target?, fx, lines, next, wait}] | one tap per step (generalised shine) |
| build | house (set name), target, taps, hint, walker, fx, counter, gap, steps [{at, fx, lines}] | band k folds up after k·taps/bands taps; fx sees stage.build_ctx {house, walker, tap, taps} |
| huff | house, taps, target (default wolf), who, prompt, hint, fx, counter, gap, result (blow_apart / collapse / hold), ruin (card id), huff_pose | each tap one 후~: blow_apart peels bands from the top, collapse rocks harder then tumbles, hold only shivers; the ruin set piece pops |
| cam | shot, at (spot), wait | shot + focus spot |
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
`status`: `reuse` (unchanged text, 톡톡 clip copied) | `changed-needs-recording` | `changed-recorded` | `pending`
(new line, recording not approved yet: plays caption-only for an estimated read time, listed in STORY_DONE
missing_audio; set via LINE_META in tools/story/tales/<tale>.py).
Add an `expr`/`pose` hint per line when the speaker's face must change (surprised, cold, hot…), so wiring is data.
