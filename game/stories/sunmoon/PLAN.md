# 「해님 달님」 (sunmoon) — pop-up tale plan

Phase 1 (2026-11-22): plan, script.json, shared art, set prototypes. Phase 2: handler fx / verbs, wiring, sound, full
autoplay, critics. Source (READ-ONLY): `~/projects/2026/patjuk-game/tales/sunmoon/`. Seed table:
`tools/story/tales/sunmoon.py` → `python3 tools/story/seed_script.py --tale sunmoon [--force]`. Art jobs:
`tools/art/sunmoon_jobs.py`. Cast builder: `tools/cast/sunmoon_cast.py [--cycles]`. Prototype:
`tools/story/sm_proto.py` → `--tale=sunmoon/proto`.

## Source and the story-first rule
톡톡 has two recorded sunmoon scripts with the same six voices (nar Huelyn, mom Bella, rich Matilda, tiger Brian, boy
Sparkles, girl Kurumin Cute):
- the PLAY script (`voice_script_el.json`, 143 lines): plate choices, counting 1–10, ten "떡 n개 주면" rounds, voice and
  hand quizzes, two-rope choice;
- the READ-MODE script (`read_script_el.json`, scenes R01–R11): the tale told straight, already softened, **every line
  recorded** (`read_narration_el.js`).

The pop-up book follows the READ script (no quizzes, no counting, no moral) and borrows only the play script's
first-tap instructions, each voiced once. `seed_script.py` now seeds read lines when a tale sets `READ_SCRIPT = True`
(ids `sm_r<scene><line>`; the other three tales seed byte-identically).

Tone: the tiger is a chubby children's-book tiger (silly roar, round paws, no fangs or claws out). The mother's fate is
the source's single soft line ("호랑이는 엄마를 꿀꺽 잡아먹고 말았어요.", read script note: "화면에 보이지 않고 한 줄로
지나간다") over a cutaway of the moon slipping behind a cloud; nothing is shown and nothing darker is added. The tiger
falls into the sorghum with only a bump (no blood, as in the source) and runs off. The sky ending is bright.

## Places (3 spreads, 2 page turns after the cover)
All on the seed-1 meadow template dressed with the new **`theme: "korean"`** (CardLibrary: nature cards from every
sheet; houses, props, signs, lanterns, fences, crops only from the `korean_*` sheets; other tales unchanged), on a
**paper ground** (`ground_style: "paper"`, user 2026-11-22 "펠트 질감 싫은뎅"): the template's ground sheets render as
matte cut paper (no felt nap / clumps, a faint mottle, fine fibre tooth, dark cut-line edges, the existing contact
shadows); the other tales keep felt until the user approves. Test card: `artifacts/sunmoon/ground_felt_vs_paper.png`.

| spread | place key | template | what stands | why a page turn |
|---|---|---|---|---|
| A 고갯길 | `1:4:road` | view 4, the road from the bridge (z +0.9) to the page's far end (z −7.9) | the rich house (tiled hanok gate, outdoor stove, rice steamer) by the road; three passes, each a gap between two pop-up mountain ridges the road runs through, each with its own hiding place: mossy boulder (1), seonangdang cairn (2), pine on a rock ledge (3); a saddle ridge and a far ridge behind | the road is a different place from home |
| B 오막살이 | `1:0:home` | view 0, a hollow right of the path (world 1.6, 4.6) | the thatched cottage turned to face the path (yaw −40) with a body and a room in its footprint, stepping stones to the path; behind it the jar terrace, the open stone well and the big zelkova beside it, firewood, a brushwood fence, the sorghum patch | — (morning, door, back yard, tree, rope, old rope: all camera moves on this one spread) |
| C 하늘 나라 | `1:2:sky` | sky page (phase 2) | a floor of pop-up cloud bands, a golden day sky / deep-blue night sky, the sun and moon hangers with the children's faces | the children have left the earth |

Same-place moves are camera glides: morning → door → back yard → tree → rope → old rope all happen on spread B; the
rich house and the three passes on spread A (the mother walks the road; the camera tracks her and glides pass to pass
while the light moves late → dusk → night).

### Paper spec — A 고갯길 (mountain pass road)
- SUBJECT: the mother with her basket on the winding road, and the boulder / cairn / ledge the tiger comes out from.
- PALETTE: jade ridge `#4f8a6e` (near mountains), slate blue `#4a5f93` (far peaks), ochre road felt `#c9a15a`, mossy
  boulder grey `#a49c88`, maple rust `#d0582c` (accent at each pass), coral-peach `#f2a07b` (the mother's jacket,
  the warmest thing on the road).
- LIGHT: pass 1 `late` (low warm key from the left, long shadows), pass 2 `dusk` (red sky, cool fill), pass 3 `night`
  (moon key, deep-blue haze, the tiger's eyes the only warm points); no practical lights on the road.
- LENS: fov 22–30, crane 36° for the whole road (three passes stacked), low 3° for the tiger's entrance, 70° side
  track for the walk; focus band on the road edge between the mother and the hiding place.
- GROUND: the template's paper sheets (ground_style paper); the road verge with pampas and maple; no western props
  (theme).
- LAYOUT: the road is the leading line, zig-zagging back through three ridge gates; the hero (mother) right of
  centre walking away; each hiding place sits ON the road edge where she must pass it.
- MOTION: ridges and rocks are rigid (no sway); pampas and maple sway ≤ 2.5°; the tiger steps out from behind the
  rock (never pops up from nothing); the rich house props pop in only as the work line plays.
- SOUND: mountain wind bed (amb.breeze / gust), birds by day, a cuckoo at the first pass, crickets and owl at night;
  rope basket creak in her walk; the tiger's growl cute, low and short.
- BANNED: western houses, signposts, haystacks; a rock or ridge across the road (SET_CHECK road=0); a house standing
  on the road; the tiger visible before he steps out; anything violent at pass 3.
- QA: crane frame of the three passes; 8 fps tiles of her walk (back view, side view); the tiger's step-out frames at
  each pass; the night frame with the moon cutaway.

### Paper spec — B 오막살이 (cottage, yard, well, tree)
- SUBJECT: the cottage's lattice paper door and window (knock, paw, poked hole) and the big zelkova by the well (climb,
  oil, axe, rope).
- PALETTE: thatch gold `#e8b43a`, mud plaster cream `#e9cf9a`, timber brown `#8a5428`, onggi brown `#7a3a22`, zelkova
  green `#2f6b4a`, sorghum rust `#c0432a`, night blue `#1b2a5a`.
- LIGHT: morning day light for the departure; then `night` with a moon key from the back-left, the oil lamp as a warm
  practical inside (flickering pool, glow through the paper window), no other warm light outside.
- LENS: establish 24°, interior 62° behind the front wall, window close 40°, tree low-up 34° (2° elevation looking
  up the trunk), tree top 30° at fork height, rope tilt-up 40°.
- GROUND: paper sheets round the hollow; stepping stones from the door to the path; an ondol floor card in the room.
- LAYOUT: the cottage faces the path (front toward the road, yaw −40, with a body); the back door opens onto the yard;
  jars at the back corner (hide), the well a few steps on, the tree beside the well (its fork above the well), the
  sorghum beyond the tree (where the tiger falls).
- MOTION: the house and the well are rigid; the zelkova crown sways ≤ 1.5° (the trunk never); the door swings into the
  house, the paper window swaps to its poked twin; the kids climb in drawn frames with hands on the bark.
- SOUND: night bed (crickets, owl sprinkles at the zelkova crown, a soft wind), lamp flicker inside, knocks on wood,
  paper poke, well splash, oil glug, slide, axe chops (soft), rope creak / snap, sorghum rustle and a thud.
- BANNED: the front wall opening while the tiger is outside (refuge stays closed: interiors by camera glide only); the
  tiger inside the house; a flat cottage seen at an angle (body required); kids floating off the trunk; the tiger on the
  trunk without the axe notches / oil streak under him.
- QA: front 3/4 view showing the side wall and thatch slope; the room shot from behind the hidden front wall; the
  window close-up with the hole; low-up on the trunk; tree-top two-shot.

### Paper spec — C 하늘 나라 (sky)
- SUBJECT: the sun and the moon with the children's faces.
- PALETTE: day gold `#f6c445`, sky cream `#fff2cc`, cloud lemon `#ffe98a`, night blue `#14204a`, moon cream `#f5ecc4`.
- LIGHT: bright high key by day, soft blue with a cream moon glow by night; the swap crosses through a dawn.
- LENS: wide 34°, low (2°) so the cloud floor rims the bottom of the frame.
- MOTION: the discs bob slowly (hanger sway), the clouds drift; the swap is a slow cross with sparkles.
- BANNED: anything dark or scary; the tiger.
- QA: day and night frames, the mid-swap frame.

## Beats → shots, taps, lines (11 beats + cover)

| # | beat | spread / light | what happens (shots) | taps (voiced first time only) | lines |
|---|---|---|---|---|---|
| 0 | cover | — | book cover | tap the book (n01, new) | sm_n01 |
| 1 | morning 산골 오막살이 | B, day | crane down onto the cottage (establish); medium on the family at the door; two-shot on the mother; she walks down the stones and up the path (back walk, tracked); the kids go in (one door cycle, from behind), the door shuts and is barred (bolt sound) | tap 오빠, 동생: each waves (sm_002) | r0100, 002, r0103, r0104 (mom only) |
| 2 | rich_house 부잣집 | A, afternoon | crane onto the rich house by the road; the basin, the stove fire, the steamer pop up one after another as she works; two-shot with the rich lady; the basket close for the taps; she sets off up the road (track back) | tap the tray ×3: a rice cake hops into the basket each time, the basket card goes empty → full (sm_006) | r0204, 006, r0205 (mom + 서둘러) |
| 3 | pass1 첫째 고개 | A, late | crane over all three passes; side track as she walks into the first pass; the tiger steps out from behind the boulder (low, small shake); OTS from the tiger onto her | tap the mother ×1: she holds out one cake, it arcs into his mouth, belly1 (sm_130) | r0300, r0301, r0302, 130, r0304 |
| 4 | pass2 둘째 고개 | A, dusk | side track; out from behind the cairn (low); two-shot | tap ×2 (rings only): two cakes, belly bigger | r0400, r0402, r0404 |
| 5 | pass3 셋째 고개 | A, night | side track; two eye glints by the ledge first, then he steps out; the basket close; two-shot for his last line; cutaway: the moon slips behind a cloud for the soft line; back to the road: the tiger alone, a paper flip into her clothes, sneaks off toward home | tap ×1 (rings only): the basket tips, every cake into his mouth, belly2 | r0500, r0502, r0503, r0505 (tiger only), r0506, r0507 |
| 6 | door 문밖의 호랑이 | B, night | the dark cottage, the lamp-lit window (establish); glide into the room (kids by the lamp); the disguised tiger arrives at the door (walk toward); OTS over his shoulder onto the door for the knock; reverse inside for the boy; the paw slides in at the door's edge; window close-up from inside | tap the paper window ×1: a finger poke, the hole (sm_069); the eye blinks in it | r0602, r0604 (boy only), r0606, 069, r0609, r0610 (boy only) |
| 7 | backyard 뒷마당 | B, night | high wide over the yard (route reads); the kids tiptoe out of the back door (side walk); jars low; the tiger comes round the corner (side sneak), searches (paw over eyes), goes back | tap the big jar ×1: the kids run behind it and crouch (sm_074) | r0701, 074, r0704 (girl only), r0705, r0706 |
| 8 | tree 우물가 큰 나무 | B, night | the kids run to the tree (run cycle, high wide); low-up on the trunk for the climb; tree-top two-shot; the tiger walks to the well (medium); looking down into the well (their faces in the water); bucket splash; tree-top for the giggle; low-up from the tiger; tree top for the boy's trick; low-up for the oil and the slips; tree top for the girl's slip of the tongue and 쉿; the axe climb (notches appear under each chop) | tap the trunk ×3: one stretch per tap (drawn climb frames, hands on the bark), the third onto the fork (sm_079); tap the oil bottle ×1: oil pours, a glossy streak on the bark (sm_091) | 079, r0803, r0804 (tiger only), r0806, r0808, r0809, r0810 (tiger only), r0811 (boy only), 091, r0813, r0814 (girl only), r0815 (쉿 trimmed), r0816 |
| 9 | rope 하늘 동아줄 | B, night | the kids in the fork pray (face); the golden rope slides down from the sky with sparkles and a chime; tilt up the rope; each tap they climb a stretch and the camera rises past a cloud band | tap the rope ×3 (sm_104) | r0901, r0902, r0903, 104, r0907 (at tap 2), r0908 |
| 10 | old_rope 썩은 동아줄 | B, night | back on the tree: the tiger prays, the old rope slides down; he grabs it (grab_up), climbs (rope frames, creaks); tilt up; the snap; fast cut to the sorghum (shake, thud, rustle); dazed with a bump; he runs off into the hills (side run, tracked) | — | r1001, r1002 (tiger only), r1004, r1005, r1006, r1007 |
| 11 | sky 해님 달님 | C, day → night → day | wide sky: the sun (brother) and moon (sister) rise; night falls; the girl is afraid; the swap (the discs cross, sparkles) → the sun has her face, the moon his; the reader plays day and night; the book closes | tap the sun / the moon: day / night (sm_115) | r1101, r1103 (girl only), r1104, r1106, 115, r1107, n02 |

About 21 taps (cover 1, kids 2, cakes 3, passes 1+2+1, window 1, jar 1, trunk 3, oil 1, rope 3, sun/moon 2), nine voiced
instructions, each the first of its kind.

Characters are where the story puts them: the kids are inside the locked house from the morning until they slip out of
the back door (the room is shown only by gliding the camera through the closed front wall: the tiger never comes in
and the front never opens); the tiger is hidden behind his rock / cairn / ledge until he steps out; the rope comes
only after the prayer; the rich house props, the oil and the axe notches only when used.

## Cast (all SHARED, `game/art/cast/`, skin names generic for reuse)

Every walk and run is a drawn cycle (side 4 facing right, flipped for leftward travel; back 2; front 2), advanced by
distance. Climbing / rope / falling are single drawn frames flipped A ↔ B by the handler (no rig).

| role | skin | standing height | standing figures (pose) | drawn cycles / frames |
|---|---|---|---|---|
| 오빠 | `hanbok_boy` | 0.25 | calm, wave, scared, shush, clever, pray, giggle, side_walk, back_walk, pair_hold (with his sister), sit_hold, sit_giggle | walk_cycle 4 / walk_back 2 / walk_front 2, run_cycle 4 / run_back 2, climb_a/b (back, trunk), rope_a/b (front) |
| 동생 | `hanbok_girl` | 0.235 | calm, wave, scared, blurt, shy, giggle, wow, side_walk, back_walk, sit_scared, sit_giggle | walk 8, run 6, climb_a/b, rope_a/b |
| 엄마 | `hanbok_mom` | 0.36 | calm (empty basket), wave, talk, work (stirring), happy_full, scared_full, give (one cake out), tired_full, side_walk, back_walk, hurry (side) | walk 8 with the basket |
| 호랑이 | `tiger` | 0.44 upright | calm, roar, demand, gulp, belly1, belly2, sly, search, look_up, whisper, side_walk, back_walk, dazed (bump, stars); disguise: dg_calm, dg_knock, dg_sweet, dg_side, dg_back, dg_caught; tree: peer_well, pull_rope, smear_oil, slip, axe_a/b; rope: grab_up, rope_a/b (back), falling, run_bump (side) | walk 8, disguise sneak (dg_cycle 4 side, dg_front 2) |
| 부잣집 마님 | `rich_lady` | 0.355 | calm, smile, give_tray, thanks, side_walk | (does not walk) |
| 해 / 달 | `sunmoon_sky` (hangers) | 0.6 discs | sun_boy, moon_girl, sun_girl, moon_boy | — |

Line → expression map: `LINE_META` in the seed table (copied into script.json as `expr`).

## Props and set pieces (shared atlas, story_* categories, tags `sunmoon` / `korean_traditional`)
- `story_sm_cottage_00..07`: thatched cottage front (door leaf cut, body: own wall strip + thatch slopes,
  `stages/stages.json` via `tools/atlas/sm_cottage.py`), door leaf, paper window, poked window, gable end, back with the
  back door, room wall with shelf and quilt, oil lamp.
- `story_sm_yard_00..09`: open stone well with frame, rope and bucket; bucket; jar terrace; big onggi jar; sesame-oil
  bottle; axe; brushwood fence; firewood; straw mat; jige.
- `story_sm_tree_00..05`: the big zelkova (1.7: trunk clear from roots to the fork), trunk alone, crown alone, oil
  streak, axe notches (merged column), side branch.
- `story_sm_mountain_00..09`: four layered ridges (one with a saddle), boulder, seonangdang cairn, pampas, maple bush,
  pine on a ledge, small rocks.
- `story_sm_village_01..08`: hanok gate house, outdoor stove with cauldron, rice steamer with steam, tray of rice
  cakes, basket full / empty, one rice cake, rice basin.
- `story_sm_sky_00..09`: good rope (golden, 2.0), old rope (frayed), snapped end, three cloud bands, puffy cloud, sun
  disc, moon disc, star.
- `story_sm_field_00..07`: three sorghum clumps, sorghum band, wild grass, persimmon sapling, reeds, dark bush.
- Reused from the shared library through the korean theme: korean_village / korean_nature houses, pines, persimmon
  trees, jars, magpie, bamboo, stone lanterns, rice paddies (template dressing).

## Lines (script.json: 65 used — 63 reuse 톡톡 recordings, 2 new)
- Read-mode lines reused as is: r0100, r0103, r0204, r0300–r0302, r0304, r0400, r0402, r0404, r0500, r0502, r0503,
  r0506, r0507, r0602, r0606, r0609, r0701, r0705, r0706, r0803, r0806, r0808, r0813, r0816, r0901–r0903, r0907,
  r0908, r1001, r1004–r1007, r1101, r1104, r1106, r1107.
- Seg trims (clips reused, nothing recorded): r0104 mom only, r0205 without "떡을 바구니 가득 받았어요!", r0505 tiger
  only, r0604 boy only, r0610 boy only, r0704 girl only, r0804 / r0809 / r0810 tiger only, r0811 boy only, r0814 girl
  only, r1002 tiger only, r1103 girl only.
- **Doubled clip trimmed (one caption, one voice):** r0815's "쉿!" (boy_a18c6b958e.mp3) says it twice (two equal
  speech blocks 0.13–0.68 s and 1.00–1.59 s) → first take only, 0–0.84 s with a fade (`TRIM_SEG`). Audit table:
  `artifacts/sunmoon/clip_audit_p1.txt`; also flagged but natural: r0602 "똑똑똑." (knock rhythm, listen once), r0704
  "오빠, 무서워…" (two phrases).
- Play-script instructions (voiced once, first tap of each kind): 002, 006, 069, 074, 079, 091, 104, 115, 130.
- Cut from the read script (the picture tells it, or pace): r0101 (오빠는 씩씩하고…), r0102 (아침 해가…), r0105 (문을 꼭
  잠갔어요: the bar slides on screen), r0200, r0201, r0202, r0203 (the work is shown by the props), r0303, r0401, r0403,
  r0501, r0504 (shown), r0600, r0601, r0603, r0605, r0607, r0608 (the door scene keeps knock / hand / hole / eye),
  r0700, r0702 (the instruction 074 replaces it), r0703, r0800, r0801, r0802 (the climb taps), r0805, r0807 (the
  splash is shown), r0812 (the oil tap shows it), r0900, r0904 (didactic), r0905, r0906, r1000, r1003, r1100, r1102,
  r1105, **r1108 (the moral)**.
- Cut from the play script: every quiz, plate choice, counting line (133–142), "떡 n개" rounds 3–10, the voice and
  hand quizzes, the two-rope choice.
- **New, needs recording with the narrator voice (Huelyn) — ask the user first; caption placeholders until then
  (`status: pending`):**

| id | text | chars (with spaces) |
|---|---|---|
| sm_n01 | 그림책을 톡 눌러서 펼쳐 볼까요? | 18 |
| sm_n02 | 또 보고 싶으면 '다시 보기'를 톡! | 20 |
| | total | 38 |

## Runtime estimate
Narration of the 65 used lines: **263 s** (morning 16.6, rich house 9.8, pass1 19.4, pass2 13.4, pass3 24.6, door
29.6, back yard 19.7, tree 46.8, rope 23.1, old rope 29.1, sky 27.3, cover 3.7; the two new lines at caption-reading
time). Non-voice time: ~21 taps (~40 s with their payoffs), walks / glides / step-outs / climbs (~75 s), 2 page turns +
the cover (~15 s). **Estimate ≈ 6:15–6:40** (three_pigs carried 131 s of non-voice time, witch_candy 220 s; this tale
has fewer walks than witch_candy). If the first full run is over 6:30, next cuts: r0907 (구름을 뚫고 쑥쑥: the camera
shows it), r0705's narration seg, pass 2's taps down to 1, r1004 narration (the snap is heard).

## Sound (phase 2, SoundDirector)
Beds follow the light (day birds → afternoon → late → dusk → night crickets + owl sprinkles at the zelkova and pine
crowns + soft mountain wind; room bed with the lamp flicker). Music slots: home (morning, rich house), wolf → a lighter
"tiger" cue for the passes (kept playful), night (door, back yard), chimney (tree, old rope), ending (rope, sky).
New sm.* ids to make (synthesised, nobody has listened): growl_cute (low, short, never a real roar), gulp / gulp_big,
bolt, knock (wood), paper_rustle, paper_poke, blink, scurry, oil_glug, slide, chop (soft), rope_creak, rope_snap,
sorghum_rustle, twinkle (the eye glints). Footsteps on drawn contact frames: kids / mother light (pig set), tiger
heavy (wolf set).

## Engine work for phase 2 (reuse; no forks)
- Reused as is: `go_inside` + door cycle (`door_in`, `door_clear`, `climb_steps`), house bodies (`box.body`), rooms in
  the footprint with `inside_only` pieces and the facade hiding near the camera, `pop_in: false`, frame-first taps,
  `segs` + `expr`, OVERLAP / OCCLUDE / VOICE_DUP, SET_CHECK, check_lines, audit_clips, the night `sky` block, `glow` /
  `light` on set entries, CastPuppet cycles by distance, `walk follow` / `via: road`.
- New, small and generic: `theme` on MeadowWorld / CardLibrary (done in phase 1); `enter.hidden` (an actor placed
  behind a set piece and stepped out by fx); hanger poses for the sun / moon and a sky page (cloud floor, no meadow in
  frame); a `climb`-style handler path on a vertical card (trunk / rope) with A/B frames.
- Tale handler `game/stories/sunmoon/fx.gd`: door_bolt, cake_to_basket, cake_to_tiger, cakes_all_to_tiger, tiger_out,
  eyes_glow, moon_cloud, mom_gone, paw_in, poke_hole, eye_blink, hide_behind, climb_tree, bucket_splash (+ reflection),
  oil_smear, tiger_slip, axe_climb (notches), rope_down (good / old), rope_climb (camera rise + cloud bands),
  tiger_rope_climb, rope_snap, swap_sun_moon, day, night.
- The cottage's stepping stone and veranda rise 0.076 + 0.057 (30 % / 23 % of the kids' height): add an open walkable
  step (two treads, ≤ 1/8 H each) in front of the door before `go_inside` (papercraft walkable rule).

## Prototype (phase 1)
`tools/story/sm_proto.py` → `game/stories/sunmoon/proto/script.json` (paper ground) and `proto_felt/` (the same on
felt, for the test card): road (late) and road (night), cottage (day) and cottage (night) with the cast placed, the
ground test beat and two camera tours. Videos / sheets: `artifacts/sunmoon/sunmoon_set_tour_p2.mp4`,
`artifacts/sunmoon/proto/*_p2*`. Prototype fixes found on screen: the pass shots must stay inside the ridge gaps
(passes ~2.3 apart; pass 3 sits on the road's diagonal bend → its own yaw); an over-the-shoulder at a pass looks into
the rock (front-facing cards) → an angled two-shot; the night sky on a page that opened by day was never built and
then took the shot's yaw (engine fixes); room shots carry the cottage's yaw and a focus deep enough to put the camera
inside the front wall; the room needed the wall's inside face and an ondol floor (new art story_sm_cottage_in).

## Open / risks
- Glides between passes cut through ridge cards (OCCLUDE ridge_2_l on the pass-3 approach): phase 2 tracks the mother
  along the road through the gaps (waypoints) or hides set-piece cards on the camera path like meadow cards.
- The pop-up ridge / rock cards were generated with a felt print ("matte felt and cardstock"); on the paper ground they
  still read woolly up close. If the user wants paper everywhere, regenerate the scenery prompts as matte paper.
- A faint pink key fringe on one ridge card's edge (seen in the tour at close range): re-key / erode that card.
- The cottage body: the back gable card shows its blank back above the thatch; the back wall uses a wall strip, not
  the back-door card (story_sm_cottage_05) the escape needs.
- The stepping stones read too small (scale 0.5 of a stream stone).
- Spread C (sky page) is planned, not prototyped.
- The tiger's rope-climb frames draw their own light rope; the old-rope card is darker: recolour the drawn rope or
  hide it under the card in phase 2.
- Climb frames must be pinned to the trunk card's surface (handler path), or the kids float.
- Nobody has listened to the reused clips in this context except by envelope; r0602 "똑똑똑." flagged for listening.
