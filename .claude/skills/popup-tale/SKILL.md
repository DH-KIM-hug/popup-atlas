---
name: popup-tale
description: Make a new tale (or a big chunk of one) for the 팝업 동화 iPad pop-up storybook app in Godot (repo popup-atlas, game/). Covers script.json seeded from 톡톡 동화극장, beats and spreads on the shared world templates, reusing the shared card atlas and cast library, generating only missing art (Codex magenta pipeline), expression sets and drawn walk / run cycles, story verbs and taps, voice lines and sound, recording with the Godot movie maker, the mandatory gate (gate.py + motion tiles) and blind critic loops. Use it whenever the user asks to add or adapt a story/동화 in this app ("다른 동화도 만들자", "아기 돼지 삼형제 만들어줘", "새 동화 추가"), to add characters or scenes to a tale, or to judge/fix how a tale's characters move, emote or look — even if they don't say "skill".
---

# Pop-up tale production (팝업 동화)

Tales so far: 「해와 바람」 (sun_wind, the first), 「아기 돼지 삼형제」 (three_pigs), 사탕마녀 (witch_candy), 해님 달님
(sunmoon), 늑대와 일곱 아기 염소 (wolf_goats), 「커다란 순무」 (turnip), 「팥죽할멈과 호랑이」 (patjuk), 「라푼젤」
(rapunzel). Every mistake that cost a round is folded into the references so the next tale goes right the first time.
Read `docs/BRIEF.md` (contracts, style rules, asset-reuse policy) and the tail of `artifacts/game-progress.md` before
starting; append a dated entry there after every round.

The user talks in Korean, wants to SEE results (send recordings and contact sheets with SendUserFile, not just
numbers), and gives short, sharp feedback on motion ("뒤로 걷는데?", "팔자걸음", "휘청거려"). Treat each such remark as a
bug report: reproduce it with an 8 fps zoomed frame tile first, find the cause, fix, re-record, show.

## User rules (decided by the user; latest version only — details in the reference named)
Source and reuse
- From 톡톡 동화극장 (`~/projects/2026/patjuk-game`, READ-ONLY) only the **script** carries over, and even it is a draft
  to adapt to pop-up scenes. Characters, backgrounds and props are made new for the pop-up look; 톡톡 art is a design
  reference at most.
- **Reuse first**: shared card library `game/art/atlas/catalog.json`, shared cast `game/art/cast/catalog.json`, world
  template `scenes/world/meadow.tscn`; new generic art goes into the shared libraries with tags, only truly
  tale-unique art in `game/stories/<tale_id>/art/` (art.md).
Look
- The look is fixed: the photographed miniature (low lens, shallow DOF, raking warm light). Don't re-tune the
  template look per tale; dress it.
- **No felt anywhere** ("펠트 질감 싫은뎅", 2026-11-22): ground, set cards and characters are matte cut paper, no
  stitching; paper is the engine default (art.md; the old felt default is superseded).
- **No white / cream rim on puppets** ("흰색 테두리가 별로", 2026-11-23): cast cards cut in the figure's own colour (art.md).
- **Steam, smoke and puffs only from hot things** ("이상한데서 김이 모락모락", "셋째집 연기뭐지?") (sets.md "Stray effects").
- **Holes read as what the story says** ("구멍을 그렇게 파니...?"): planting hole flat dip + heap, mouse hole a low bank (sets.md).
- **Houses solid from every angle** ("집들은 무조건 입체적으로 아주 잘 들어맞게", 2026-11-23): every house, barn, shop,
  cottage — story and template — is a closed, tight 3D volume; non-box buildings come from the building kit; never a
  flat card (sets.md).
- **The place named in the story reads on screen** ("순무는 텃밭이 없네용?"): a 텃밭 is tilled soil with rows (sets.md).
The book tells the tale (2026-11-18: "팝업북은 어떤 교육적인 요소보다는 그냥 동화의 전달에 좀 의미를 뒀으면")
- No quizzes, no counting drills, no spoken or printed morals. Cut source lines that count ("열 장", "여덟 번",
  "하나, 둘, 셋") or teach; trim a count in its own sentence at the pause (sound.md), otherwise drop the line or list it
  for the user.
- Taps drive the story: a few natural taps per moment (about 3 to build a house, 3 huffs; "벽돌을 10번이나 누를 이유가
  있냐"), never a tally on screen. Voice a tap instruction only for the first tap of each kind; later taps show only
  the ring hint.
- Characters are where the story says they are ("아기돼지들 집에 있어야하지 않겠니?"): someone "at home" is in the house —
  peeking out of a die-cut window, answering from inside, running in through the door (house_stages.py GLASS / DOORS,
  `enter.inside`, `go_inside`); when the house falls they are revealed where it stood (motion.md "Peeks").
- A refuge stays closed ("앞 벽은 막혀있어야", "굴뚝으로 들어가면 그제서야 안을"): show the inside by moving the camera in
  after the threat entered, never by opening the wall (sets.md; the earlier fold-open cutaway is superseded).
- Things appear only when the story reaches them ("둘째 집 짓기도 전에 있음", "짚이랑 벽돌을 왜 가지고 있지") and a prop that
  leaves the story leaves the screen; what the narration brings travels on screen ("초대장이 날아왔으면 좋겠고") (sets.md).
- Every action reaches its outcome on screen: the villain's defeat ends with him visibly running away ("늑대가 도망가서
  달려야"); a surprise gets dramatic irony first ("처음엔 나온지 몰라야지 나중에 놀라는거") (camera.md).
Motion
- Every walk and run is a drawn cycle for the view it travels in ("이전 걸음 이상해요", "돼지 옆으로 달려가는 모습 이상해유",
  "늑대도 이상한디요?"); the card faces its travel direction ("뒤로 걷는데?", "앞뒤 왼쪽 오른쪽도 되긴 해"); no hopping
  static card for travel (motion.md).
- Entries climb the steps through a fully open door, nobody passes through door cards or sills ("문에 겹친다던지 문 아래
  돌지방을 통과") (sets.md "Doors and entries").
- **Nothing overlaps** ("최대한 겹치게 하지마라는 규칙은 없었나", "물체랑 사람들끼리 자꾸 겹치잖아"): OVERLAP_COUNT /
  OCCLUDE_COUNT 0 or listed in `overlap_ok` with a reason (sets.md).
Camera (2026-11-19 shot plan, camera.md)
- A page is a film: varied shots, wide establish, push-in on completion, light progressing, the book closes at the end.
- Same place = one spread with camera moves, no page turn ("책장 안넘기고 한번에 처리하는게 좋을거같음 카메라 무빙으로").
- No jerky viewpoint jumps ("시점이 뚝뚝 끊기는거 별로에요"): CAM_JUMP / CAM_JERK 0.
- Taps: frame every target first ("화면이 거기로 안가서 못누름"), ≥ ~80 pt; frame each build once for the finished house
  ("Frame each build once"); interactive moments get their own framing ("선반으로 카메라를 옮기는 건 어때?").
- The speaker is on screen and unhidden when the quote plays ("도착 전에 문 열라고 하네", "앞의 집때문에 안보여").
Sound
- The cover opens with 톡톡's intro track for the tale; no generated opening sounds ("다 별루") (sound.md).
- Never spend on ElevenLabs without asking; reuse 톡톡 clips, trim instead of re-recording (sound.md).
Delivery
- Full recordings at 1200x900 ("왼쪽 오른쪽 상단 글자 잘리는데") (tooling.md); mp4 < 30 MB; say what nobody checked.

## Pipeline (one tale)
1. **Plan** (`references/planning.md`): beats → spreads (template, seed/view, route), the cast with every
   pose/expression and travel direction per beat, props, taps/holds per beat, line changes, places named, length.
   Write `game/stories/<tale_id>/script.json` with `tools/story/seed_script.py` (schema: `references/script_schema.md`;
   reseed and diff rules: `references/engine.md`).
2. **Engine**: new cast / props / fx go to data and the tale's handler; keep sun_wind and the other tales playing
   (`references/engine.md`).
3. **Art** (`references/art.md`): search the catalogs; generate only what's missing with the Codex pipeline; full
   expression sets; drawn walk / run / back / front cycles per walker (`references/motion.md`).
4. **Voice + sound** (`references/sound.md`): reuse recordings; changed/new lines need the same voice ids — ask the
   user before recording; mark status in script.json; wire SoundDirector cues and the intro music.
5. **Sets + wire** (`references/sets.md`, `references/camera.md`): spots probed, houses solid, props in their beats,
   shots per line; autoplay every beat, record with the movie maker, look at frame tiles, fix. Full unattended run
   start → end with `--autoplay --quit-on-done`.
6. **Judge** (`references/critic_loop.md`): run THE GATE below; then ≥3 lens-diverse blind critics.
7. **Deliver**: commit + push per milestone (on main unless told otherwise), send mp4s (< 30 MB, re-encode crf 26–30 if
   bigger) and a contact sheet, report honestly what still looks off and what nobody has listened to.

Run long work through background agents/workflows with narrow ownership (one owner per file set, never two writers on
the same Godot project files; use a git worktree for parallel look experiments). Brief every agent with the relevant
reference files — they don't know them.

## Before showing the user anything — THE GATE
A tale is not shown to the user until `gate.py` prints GATE PASS. An accepted exception must be written in
`artifacts/<tale>/gate.md` with a reason.
1. Record the full run with `--log-track` (and `--log-sound`) at 1200x900 through `tools/story/with_godot.sh`
   (MOVE lines are always printed by StoryActor; TRACK lines with `--log-track` give tighter motion crops).
2. `python3 tools/story/motion_review.py <tale> <run.log> <full.mp4>` → `artifacts/<tale>/motion/<NN>_<actor>_<t>.jpg`
   tiles + `artifacts/<tale>/motion/motion_review.md` (one row per walk / run / climb / flight segment; MOTION_FLAG
   lines; MOTION_FLAGS=n). OFF_FRAME (wave 1): the mover is off the frame, not drawn or under the shown caption for
   more than 30 % of its segment — the camera lost the traveller (the commonest audit v1 failure); fix the shot,
   don't accept it.
3. Open EVERY tile and write a verdict (`ok` / `fix` + note) in each row of motion_review.md.
4. Tick the fixed visual checklist in `artifacts/<tale>/gate.md` (gate.py writes it the first time): no white / cream
   rim on puppets ("흰색 테두리가 별로"); steam / smoke / puffs only from hot things ("이상한데서 김이 모락모락"); holes read as
   what the story says ("구멍을 그렇게 파니...?"); no flat-card houses ("집들은 무조건 입체적으로"); no empty shots; the place
   named in the story reads on screen ("순무는 텃밭이 없네용?"); paper, not felt ("펠트 질감 싫은뎅").
5. `python3 tools/story/gate.py <tale> <run.log> <full.mp4>` must print GATE PASS. It runs check_lines.py and requires
   VOICE_DUP, CAM_JUMP, CAM_JERK, SPEAKER_OFF, OVERLAP_COUNT, OCCLUDE_COUNT, SET_CHECK road / water, missing_audio,
   missing_sound and MOTION_FLAGS all 0 / empty, every motion verdict filled and every gate.md box ticked.
   A deliberate non-zero item passes only as a line under "## Accepted exceptions" in gate.md: `- <id gate.py
   printed>: <reason>` (e.g. `- MOTION_FLAG 04: the cat's roof hop is a jump`). gate.md and the verdicts belong to
   one run: a new log starts them fresh. Logs from before 2026-11-23 have no MOVE lines (MOTION_NOLOG): re-record.
   Re-using a recording with a movie-less re-run of the same build: `--ref-log <log recorded with the mp4>` (counters
   are read from that log; a movie-less run reports false VOICE_DUP).

Then read the rest by eye with `references/checklist.md` (every complaint the user made, with their words: story logic,
lines, motion, camera, sound, delivery). Most rounds on 「아기 돼지 삼형제」 went on items we could have caught ourselves:
- a house standing before its build;
- pigs outside while the wolf knocked;
- a quote before the speaker arrived;
- tap targets off-screen;
- hopping-card runs;
- a sound preview made from an old capture.
Two rules guard against this:
- Review the newest build, never an earlier capture.
- When a fix touches timing or staging, re-check the neighbouring beats, because fixes caused regressions: framing
  added 15 s, and a split line read as missing.

## Read X when doing Y
| doing | read |
|---|---|
| planning a tale, length, places, branches | references/planning.md |
| script.json fields, step verbs, shots, kit specs | references/script_schema.md |
| seeding / reseeding, handlers, runner, branches, states | references/engine.md |
| walks, runs, cycles, facing, peeks, climbs, flights, pulls, water | references/motion.md |
| shots, framing, sightlines, taps, speakers, interiors, CAM_JUMP | references/camera.md |
| houses, bodies, building kit, rooms, doors, props, overlaps, gardens, ground, night | references/sets.md |
| finding / generating / slicing art, paper look, rims, reference images, feature edits | references/art.md |
| voice lines, clip trims, SoundDirector, intro music | references/sound.md |
| Godot slot, imports, recording, probes, shell gotchas | references/tooling.md |
| a new set or spread: paper spec, card motion, walkable steps, cut edges | references/papercraft_notes.md |
| eye review before delivery | references/checklist.md |
| critics, A/B against the reference | references/critic_loop.md |

## Commands
```sh
G=/Applications/Godot.app/Contents/MacOS/Godot
W=tools/story/with_godot.sh                                              # every Godot command goes through it
$W $G --path game --resolution 1366x1024                                 # play
$W $G --path game --resolution 1366x1024 --fixed-fps 30 --write-movie /tmp/x.avi --quit-after 600 -- --beat=<id> --autoplay
$W $G --path game --resolution 1200x900 --fixed-fps 30 --write-movie /ABS/full.avi -- --tale=<id> --autoplay --quit-on-done --log-sound --log-track
ffmpeg -i /tmp/x.avi -c:v libx264 -crf 26 -pix_fmt yuv420p -c:a aac out.mp4
ffmpeg -ss 6 -t 2 -i out.mp4 -vf "fps=8,crop=W:H:X:Y,tile=8x2" -frames:v 1 tile.jpg   # motion check by hand
python3 tools/story/check_lines.py <tale> <log>
python3 tools/story/motion_review.py <tale> <log> <mp4>      # then write the verdicts
python3 tools/story/gate.py <tale> <log> <mp4>               # must print GATE PASS
python3 -c 'import sys; sys.path.insert(0,"/Users/house_of_4k2b/.claude/skills/scenario-godot-expert/scripts"); import gd_run; print(gd_run.check_all("game"))'
```
`--write-movie` needs an ABSOLUTE path; `--import` first after new assets (tooling.md).
