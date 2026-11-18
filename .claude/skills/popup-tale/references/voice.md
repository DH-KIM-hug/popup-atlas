# Voice

- Seed: `tools/story/seed_script.py` (currently hard-wired to sun_wind — parametrise by tale id first). It parses 톡톡's
  `narration_el.js` (full line text → clip paths) instead of re-hashing, copies the used MP3s (Godot imports MP3) into
  `game/audio/voice/<tale_id>/`, and marks lines reuse / changed-needs-recording.
- Record: `tools/story/record_lines.py --dry` first (lists lines + character count), then ask the user before the paid
  run. It uses the same voice ids/models/settings as 톡톡, 톡톡's clip naming and polish step, key in
  `~/.config/elevenlabs/key` (never in the repo), and writes `recorded.json`; re-run seed with `--force` to fill them
  (status changed-recorded). Nothing is written into the read-only 톡톡 repo.
- Nobody has listened to generated clips unless the user did — say so; ask the user to listen to new lines.
- Keep new lines few; prefer reusing 톡톡 recordings and changing visuals instead of words.
