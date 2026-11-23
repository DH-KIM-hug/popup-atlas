# Sound: voice lines, clip trims, SoundDirector, music

## Voice lines (seed, reuse, record)
- Seed: `tools/story/seed_script.py` (started hard-wired to sun_wind, now per tale id via tools/story/tales/<tale>.py).
  It parses 톡톡's `narration_el.js` (full line text → clip paths) instead of re-hashing, copies the used MP3s (Godot
  imports MP3) into `game/audio/voice/<tale_id>/`, and marks lines reuse / changed-needs-recording. Reseed rules
  (diff before copying, `--force` into a fresh temp): engine.md.
- Check 톡톡 for a READ-MODE script (`read_script_el.json` + `read_narration_el.js`): sunmoon's is the tale told
  straight, already free of quizzes and counting, and every line is recorded. `READ_SCRIPT = True` in the tale table
  seeds those lines (`<prefix>_r<scene><line>`, `READ_SEG_KEEP` for seg trims); borrow only the play script's tap
  instructions, voiced once. Measure: the read script ran 423 s of narration, trimmed to 263 s by dropping lead-ins the
  picture tells.
- Check the voices table before planning new lines: speakers marked `"tc"` (patjuk's granny and all seven helpers) are
  Typecast clips with no ElevenLabs voice id, so no new line can be recorded for them; every new line went to the
  narrator. Name the actor role after the voice script's speaker key ("halmi", "bam"…): the stage finds a speaker's
  actor by that name (SPEAKER_OFF, speaker chips, line `expr`).
- Check the read script's narrator voice id before reusing other tales' cover / replay clips: rapunzel's narrator is a
  different ElevenLabs voice (Annie), so its cover / replay prompts were recorded new.
- Record: `tools/story/record_lines.py --dry` first (lists lines + character count), then ask the user before the paid
  run (**never spend on ElevenLabs without asking**). It uses the same voice ids/models/settings as 톡톡, 톡톡's clip
  naming and polish step, key in `~/.config/elevenlabs/key` (never in the repo), and writes `recorded.json`; re-run seed
  with `--force` to fill them (status changed-recorded). Nothing is written into the read-only 톡톡 repo.
- Keep new lines few; prefer reusing 톡톡 recordings and changing visuals instead of words.
- Nobody has listened to generated clips unless the user did — say so; ask the user to listen to new lines.

## Clip trims (no re-recording)
- Cut counting / teaching: if a clip's count sits in its own sentence, trim the clip at the pause (`TRIM` in
  tools/story/tales/<tale>.py) and say so.
- Doubled words (user: "그럼을 두 번 말하고"): two wolf clips began with a faint extra "그럼"; find it on the envelope
  (silencedetect / RMS plot) and trim (`TRIM_SEG` in the tale table).
- One caption, one voice (user: "말풍선에는 하나만 써있는데 두번 말하는 경우가 있어"): a clip must not contain its sentence
  twice (generated takes sometimes repeat; check duration vs text and transcribe), and a line must never start a second
  voice play or overlap another voice under the same caption (run log VOICE_DUP=0). Lines that recur across rounds are
  fine.
- 톡톡 extra clips can hold repeated takes (the puppy's growl ran 10.5 s, grandpa's "영~차!" twice), even in the read
  script (the prince's 11 s "라푼젤…" said it five times): check every clip's envelope, not only the narration.
  ElevenLabs speech-to-text (word timings) + silencedetect find the take to keep (tools/story/rp_trim.py, TRIM_SEG).

## SoundDirector (2026-11-19, shared)
- `game/core/audio/sound_director.gd` + `game/audio/sound_catalog.json` (ids, beds, sprinkle sets, emitters,
  footstep contact frames, music slots); a tale maps fx / steps to ids in its `sound` block (seed table `SOUND` +
  per-beat `sound`: music, bed "@light", emitters). Buses Voice / Music / Ambience / SFX are created in code;
  Music -7 dB and Ambience -3 dB duck while a line plays (deterministic envelope from `_say`); Master limiter -1 dB.
- Footsteps come from drawn-cycle contact frames (CastPuppet.foot_contact); surfaces from GroundLayers; beds follow
  the spread's light; birds / frogs / owl sprinkle at tree crowns (MeadowWorld.trees) or the water; one stream
  emitter slides along the water line nearest the camera focus; leaf rustle swells with gusts and huffs.
- A living world (user: "새소리 물소리 풀잎소리"): birds, a stream (positional), leaves and grass in the breeze, accents
  (cuckoo, bee, frogs, owl), beds that follow the light; every on-screen action has a cue (landings a thud).
- `--log-sound` prints `SFX <t> <id>` per cue; STORY_DONE reports `missing_sound=[]`.
- Sound is wired in-engine and recorded from the latest build: a preview laid over an older capture misses the newest
  fixes (user: "앞에 게 반영 안 된 것 같은데").

## Story start music (user rule)
The cover opens with 톡톡's intro track for the tale (`sound.steps.cover.on_open =
{"music": "intro_<mood>", "fade": 0.2}`; catalog music entries with `"hold": true` play once and make the next
`set_music` wait until they end). The cover beat's own music is null. Moods so far: cozy (sun_wind), playful
(three_pigs), night (sunmoon), magic (witch_candy); look up which intro 톡톡 used for the tale first (the user rejected
every generated opening sound: "다 별루").
