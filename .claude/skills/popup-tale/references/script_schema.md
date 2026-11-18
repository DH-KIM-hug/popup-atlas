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
New tales will need new verbs/fx (e.g. build_house, huff_puff, collapse). Add generic verbs to the runner; put
tale-only fx in a per-tale handler instead of growing spread_stage.gd.

## lines[]
```json
{"id": "sw_012", "speaker": "nar", "text": "…", "status": "reuse", "beat": "wind_turn", "used": true,
 "segs": [{"speaker": "nar", "text": "…", "emotion": "toneup:1.2", "tags": "[playful, …]",
           "audio": "res://audio/voice/sun_wind/nar_5782294768.mp3", "source_audio": "audio/el/…", "status": "reuse"}],
 "source_index": 12, "source_text": "…"}
```
`status`: `reuse` (unchanged text, 톡톡 clip copied) | `changed-needs-recording` | `changed-recorded`.
Add an `expr`/`pose` hint per line when the speaker's face must change (surprised, cold, hot…), so wiring is data.
