# 「사탕 마녀의 핼러윈」 (witch_candy) — pop-up tale plan

Phase 1 (2026-11-19): plan, script.json, shared art, world prototype. Phase 2: engine verbs / fx, wiring, recording,
critics. Source (READ-ONLY): `~/projects/2026/patjuk-game/tales/witch_candy/` (voice_script_el.json 155 lines + extras;
voices nar Lily, kid Annie (다현이), witch Laura, cat Hopsi; friends rabbit / bear / fox only inside 톡톡's premixed
choruses). Seed table: `tools/story/tales/witch_candy.py` → `python3 tools/story/seed_script.py --tale witch_candy
[--force]`. Art jobs: `tools/art/witch_candy_jobs.py`.

## User decisions (2026-11-19)
- **Magic play, not a lesson.** Funny ingredients go in the pot; the candy and Dahyun's transformation depend on the
  colours that went in. No "무슨 색일까?", no colour explanations, no "맞아요", no counting, no quiz, no moral. The book
  says what came out only through lines that carry no colour lesson (Dahyun's "어? 맛있다! …딸기 사탕이다!").
- **Two rounds + the ghost candy finale**, about 5–6 min. Hero name 다현이 (톡톡 recordings reused).
- App rules from the skill: the book tells the tale; ~3 taps per moment, a voiced instruction only for the first tap of
  each kind; characters where the story puts them; props appear when used; same-place moves are camera moves; varied
  shots; tap targets framed first; every walk / run a drawn cycle facing its travel; sound through SoundDirector.

## Branches (proposal: build 6 results now)
The shelf holds **9 ingredients in three colour groups** (red: dragon snot, fire truck, ladybug / yellow: pumpkin
lantern, chick fart, rubber duck / blue: monster poo, fish, wave). The child taps two (any two, the same one twice is
fine); after the second pick the witch stirs by magic. The colour SET decides:

| set | candy | Dahyun becomes | action (one spread, camera follows) | lines (all recorded in 톡톡) |
|---|---|---|---|---|
| red | strawberry | strawberry, curls into a ball | rolls out of the door down the street, bumps a pumpkin lantern 통!, witch "어디 가!" | 082/089, 096, 102, 110, 117 |
| yellow | duck | duck feet | waddles round the pot (drawn waddle cycle), 호박이 waddles behind | 083/090, 097, 103, 111 |
| blue | fish | fish tail | floats out and swims a loop round the full moon (tilt up) | 084/091, 098, 104, 112 |
| red + yellow | pumpkin | glowing pumpkin tummy | the street lamps dim, she walks out and lights the dark street | 086/093, 099, 106, 114 |
| red + blue | bat | bat wings | flies out, circles in front of the moon with the paper bats | 087/094, 100, 107, 115 |
| yellow + blue | frog | frog legs | three hops out and up onto the shop roof, waves, hops down | 085/092, 154, 105, 113 |

Why 6 (of the original 9 + ghost):
- Three colours × two picks give exactly 6 colour sets, so **every pick has its own result**: no merged or "nothing
  happened" outcomes, nothing to explain.
- **Zero new voice**: every result's eat / transform / kid / action line is already recorded.
- **The finale needs the same six looks anyway** (line 139 names 딸기, 개구리, 오리, 박쥐, 물고기, 호박 for Dahyun,
  rabbit, bear, fox, cat, witch), so one design per result serves both the rounds and the finale.
- Dropping green removes kiwi, crocodile, chocolate and the green frog / dinosaur / leek ingredients: 3 more Dahyun
  transformation sets, 3 candies, 3 actions and their places that a run shows at most twice.
- Autoplay picks a random pair whose result has not been shown in this run; a child may repeat a result and it simply
  plays again (no "아까랑 같네?" correction).
- Ghost (round 3): one tap per colour group (ring hints on three ingredients, no new voice) → black candy.

## Places and world (decision: both, connected)
- **Street** (night dress of the village on the meadow template, `spread.night: "halloween"`, light evening → night):
  full moon hanger, pumpkin lanterns, paper cobwebs on fences, bunting between lamp posts, lit windows on the
  neighbour houses (`story_wc_shop_05/06` + `village_houses_*`), the candy shop at the end of the street. Warm light
  comes from the lanterns and windows (small warm omni lights), the key is cool moonlight.
- **Candy shop interior**: a reusable **`interior` RoomBox template** (back wall with night windows, side walls,
  plank floor, ceiling beam with bat mobile, furniture on spots). For this tale the room is built **inside the shop's
  footprint on the street spread** (the shop is a house with a body: side walls, roof side, its inside face, the room),
  so going in and out is a camera glide through the open door — **no page turn after the cover** (user rule: same-place
  moves are camera moves; Dahyun's transformations run out of the door and back many times). Other tales can use the
  same RoomBox as a stand-alone spread.
- Prototype stills: `artifacts/witch_candy/proto_street.jpg`, `artifacts/witch_candy/proto_room.jpg` (made with
  `game/stories/witch_candy/proto/`, see "Prototype" below).

## Beats → one spread (shot plan per the skill's Direction section)

| # | beat (tab) | what happens | shots | taps | lines |
|---|---|---|---|---|---|
| 0 | cover | book cover | — | tap the book | n01 (new) |
| 1 | invite (초대장) | crane down over the Halloween street; four pumpkin invitations flutter down on the wind; the child catches three (each lands in a friend's hands), the fourth lands in Dahyun's; the shop windows at the end of the street light up; the four walk up the street (back walk cycles), the door opens, the witch steps out (front walk), 호박이 on the step; all go in (one door cycle, seen from behind) | crane_high → establish; medium on the kids; face on Dahyun ("초대장이다!"); slow push down the street to the shop (street); medium on the witch at the door; story at the door as they go in | tap ×3 the flying cards (voiced first: n03) | 000, n03, 001, 002, 003, 004 |
| 2 | fire (뽀글뽀글 솥) | camera glides in through the door into the room; the witch at the pot; logs pop up under it; taps: flame small → medium → large, clear water rises, bubbles | inside_view glide; room (wide interior); pot_low on the fire for the taps; room for the boil; face on 호박이 "냐옹!" | tap ×3 the logs (voiced: 006) | 005, 006, 007, 008 |
| 3 | shelf (으엑, 재료!) | the shelf: nine ingredients pop up one by one with their own sound; Dahyun yucks, 호박이 holds his nose; the witch's secret; Dahyun volunteers | shelf (all nine framed); two_shot witch + Dahyun across the pot | — | 011, 038, 039 (trimmed), 040 |
| 4 | round1 (마법 사탕) | frame shelf + pot + Dahyun once; two picks fly in arcs into the pot (liquid takes the first colour, the second adds a swirl band); "A랑 B를 넣었어요!" (+ 으엑 for snot / poo); magic stir; POOF; the candy lands at Dahyun's hands; witch offers; she eats; 뿅 transformation; the action out of the door and back; giggle; 뿅 back; she walks in | frame (held for both taps); pot (looking down) for the swirl and POOF; face for the eat line; two_shot for 뿅; action shots per result (street / sky / low_up roof); door_out from inside as she comes back | 2 picks (voiced first: 041) | 041, 012–020 + 024–032, 036/037, 046, 079, 080, eat r1, tf, kid, act, (117), 109, 119 |
| 5 | round2 (한 번 더) | pot clears; second round, shorter: ring hints only, "냠…" eat line, no offer, 뿅 back by sound only | two_shot; frame; pot; action shots | 2 picks (rings only) | 120, 125, A랑/B를, 045, eat r2, tf, kid, act |
| 6 | ghost_candy (유령 사탕) | "everything in": one tap per colour group, the swirl turns three bands then black; POOF; black candy; Dahyun eats: black lips, "오~~우~~"; the witch too; black candies fly to the others, they hop into ghost play | two_shot; frame; pot; face on Dahyun's black lips; room for everyone | 3 taps (rings only) | 126, 127, 130, 131, 132, x_ghost_kid, 133, 134 |
| 7 | parade (오~우~ 행진) | out of the door in single file (drawn ghost-march cycles, black lips, arms up), down the street and round; a small friendly ghost tags along at the back unnoticed (no line), looks back and vanishes with a 뿅 | outside_view; high wide so the route reads; side tracking (street) for the chorus; tilt to the moon (sky) for the vanish | — | 135, x_ghost_all (chorus) |
| 8 | finale (다 같이 변신) | back in the room; the witch calls the leftover candies; they pour out of the pot; she takes two; tap each friend: they eat and transform (rabbit frog, bear duck, fox bat); with the third, Dahyun (strawberry), 호박이 (fish) and the witch (pumpkin) transform too; 뿅 all back; "해피 핼러윈!"; tap the witch to say goodbye; glide out, pull back over the street, the book closes | inside_view; room; pot (candy fountain); room for the tap_each (all three framed); room wide for the six transformations; two_shot; outside_view; pull_back | tap ×3 friends (voiced: n04), tap witch (voiced: 143) | 136, 137, 138, n04, 139, 140, x_happy_all, 141, 142, 143, n02 (new) |

Light: evening on the street at the start (warm windows), the shop interior warm (lanterns, fire), night for the
parade, warm evening for the finale; the street dims for the pumpkin glow. Camera always drifts slightly. Keep the
180° rule inside: shelf screen-left, pot centre, counter right; Dahyun stands between shelf and pot.

## Cast (shared, `game/art/cast/`, role = skin)
Views: front, back, side (drawn facing right, flipped for leftward travel). Every walk is a drawn cycle.

| role | design | standing figures (pose) | drawn cycles |
|---|---|---|---|
| dahyun 다현이 (0.26) | dark-brown bob with bangs, blue-violet pointed hat with a gold star, blue-violet cape with orange bow, cream dress, orange-cream striped stockings, red shoes | calm, excited (invitation), yuck, eager, eat, reach, wave, wow, ghost (black lips), side_walk, back_walk; tf_strawberry, tf_strawberry_ball, tf_duck, tf_fish (side), tf_frog_jump (side), tf_frog_sit, tf_pumpkin, tf_bat_up / tf_bat_down (side, wing flap) | walk (side 4, back 2, front 2), ghost march (side 4, front 2), duck waddle (side 4) |
| candy_witch 사탕 마녀 (0.38) | round, mint curly hair, plum hat with a dangling star, plum dress, orange star belt, striped stockings, round button nose (no warts, not pointy) | calm, welcome, magic (hands to the left, sparkles), giggle, surprised, offer, two_candies, ghost, tf_pumpkin, side_walk, back_walk | walk 8, ghost march 6 |
| hobak_cat 호박이 (0.13 sitting) | chubby orange tabby, cream chest | calm, sit, meow, nose, startled (side), ghost (hind legs), tf_fish (side) | walk on four legs 8, ghost march on hind legs 6 |
| rabbit_kid (0.28), bear_kid (0.26), fox_kid (0.27), non-speaking | white rabbit with a yellow star cape / bear in a pumpkin costume / fox with a moon hat and blue-violet cape | calm, cheer, ghost, side_walk; tf_frog / tf_duck / tf_bat | walk 8, ghost march 6 each |

Line → expression map: `LINE_META` in the seed table (copied into script.json as `expr`); transformation figures
come from `RESULTS[*].figure` / `move` (brew verb).

## Props and set pieces (shared atlas, categories story_prop / story_fx / story_building, biome "halloween")
- `story_wc_ingredients_00..11`: 9 ingredients (eyes only on the ladybug and fish; the rubber duck is a toy with
  dots), ladle, pumpkin invitation (flat + fluttering).
- `story_wc_pot_00..19`: cauldron, rear rim, 8 liquid discs (water, red, yellow, blue, orange, green, purple, black),
  spiral swirl band (merged from two slices), logs in a stone ring, 3 flames, POOF smoke, bubbles, star sparkle.
- `story_wc_candies_00..09`: strawberry, duck, fish, frog, pumpkin, bat, black ghost candy, candy jar, candy heap,
  candy basket.
- `story_wc_halloween_00..17`: pumpkin lanterns (3 sizes + stack), bunting, two paper cobwebs, 3 paper bats, full
  moon, 2 stars, lit lamp post, fence with pumpkin, broom, small friendly ghost, hay bale with pumpkin.
- `story_wc_shop_00..06`: shop facade (open arched doorway), door, side wall, roof side, the facade's inside face
  (doorway cut out), a townhouse and a cottage with lit windows.
- `story_wc_room_00..08`: back wall with two night windows, two side walls, plank floor, ingredient shelf (red /
  yellow / blue sections, empty), candy cabinet, counter, stone hearth ring, ceiling beam with bat mobile.
Props appear only when used: logs at the fire taps, ingredients pop onto the shelf in beat 3, candies at the POOF,
invitations in beat 1, the little ghost only in the parade.

## Sound cues (phase 2, SoundDirector ids to add)
Beds: night village (crickets, distant owl, soft wind), room (fire crackle, pot bubble loop once lit). Music: playful
night (invite), magic bubbles (rounds), silly march (parade), party (finale). SFX: one per ingredient (drip, siren
blip, buzz, chime, kazoo 뿡, quack, plop, splash, wave), card flutter, door creak / bell, flame whoosh ×3, magic stir
shimmer, POOF, candy pop, 뿅 boing per transformation, roll + 통 bonk, duck flaps, swim bubbles, ribbit hops, glow
hum, bat flaps, footsteps per drawn contact frame (street cobbles / wooden floor), ghost vanish 뿅, book close.

## Lines (script.json; 96 used: 92 reuse, 4 new; nothing recorded)
- Reused as is: 000–008, 011, 012–020, 024–032, 036–038, 040, 041, 045, 046, 079, 080, 082–087, 089–094, 096–100,
  102–107, 109–115, 117, 119, 120, 125–127, 130–143, 154, extras ghost_kid.
- Trimmed (no recording): **039** "히히, ~~색을 섞으면 다른 색 사탕이 돼.~~ 먹으면 어떻게 되는지는… 비밀! 같이 만들까?" (cut
  0.42–3.62 s at the pauses, 30 ms fades → witch_df120ff616_t.mp3, 5.04 s). **Chorus** ghost_all / happy_all use
  톡톡's premixed chorus clips (ch_48ac9f3898 / ch_672e05d93c: kid + witch + cat voices).
- Dropped: 9–10 (ingredients by colour), 21–23 / 33–35 (green, leek), 42–44 (rules), 47–78 (colour questions,
  answers, "맞아요", colour explanations), 81 (snot yuck at eating; the pick already yucks), 88 / 95 / 101 / 108 / 116 /
  118 (chocolate), 121–124 (second instruction, repeat, one more), 128 (colour-list instruction), 129 (counting),
  144–153 (lime / kiwi / crocodile), extras n1–n5 (counting), yuck, friends' chorus lines (friends non-speaking).
- **New, needs recording with the narrator voice (Lily) — ask the user first:**

| id | text | chars (with spaces) |
|---|---|---|
| wc_n01 | 그림책을 톡 눌러서 펼쳐 볼까요? | 18 |
| wc_n02 | 또 보고 싶으면 '다시 보기'를 톡! | 20 |
| wc_n03 | 날아오는 초대장을 톡 눌러 잡아요. | 19 |
| wc_n04 | 친구들을 톡 눌러 사탕을 건네요. | 18 |
| | total | 75 |

- Things to listen for (nobody has): 154 "청록 개구리" names a colour as a description (no lesson; flag for the user);
  120 "이번엔 다른 색으로 해 볼까?" and 142 "다음엔 다른 색으로요!" mention colour as play, not teaching.

## Runtime estimate
Narration per run (one round-1 and one round-2 branch, averaged): ≈ 206 s (invite 22, fire 15, shelf 13, round 1 ≈
42, round 2 ≈ 28, ghost 26, parade 11, finale 47, cover 3). Non-voice time: ~17 taps (~25 s), crane / walks /
door / glides / POOFs / transformation actions (~100 s), no page turns after the cover. **Estimate ≈ 5:20–5:40.**
If over 6:00: drop 138 ("나는 두 개!"), shorten round 2's action, play 125 under the pot-clear.

## Engine work for phase 2 (NOT implemented)
1. **`interior` RoomBox template** (`game/core/world/room_box.gd`): back / side walls, floor, ceiling beam from
   catalog ids, spots in room coordinates, warm interior lights (lantern omni, fire light that grows with the fire);
   usable inside a set piece's `box` (`"room": "interior"`) or as a stand-alone spread. Camera `inside_view` /
   `outside_view` made generic (three_pigs has them as tale fx): glide through the door, facade bands hidden while the
   camera is inside (existing rule), ceiling only inside.
2. **Night street dress** (`spread.night: "halloween"`): lit windows on houses (warm emissive planes behind window
   cut-outs or light cards), lamp posts with warm omni lights, the moon as a sky hanger, sprinkle decoration by tag
   (pumpkins, cobwebs on fences, bunting along the road) with SET_CHECK road / water = 0; a "dark" light preset for
   the pumpkin glow.
3. **House with a big body for the shop**: stages for `story_wc_shop_00` (one wall band with the doorway cut,
   `tools/atlas/house_stages.py` OPENINGS) so the door swings and the room shows through; `go_inside` with
   `room: true` (they walk on into the room instead of appearing at windows).
4. **`brew` verb (pick from shelf)**: shelf ingredients as tap targets (≥ 80 pt each in the `shelf` shot), a copy flies
   on an arc into the pot, liquid disc colour then swirl bands (rotating, clipped to the pot mouth), two picks →
   auto magic stir (witch `magic` pose, sparkles), POOF smoke, candy lands at Dahyun's hands, eat → 뿅 transform
   (figure swap with a star burst + paper hop), the result's action, 뿅 back. Lines: "A랑" + "B를 넣었어요!" joined
   (same ingredient twice: only the "넣었어요" clip), yuck lines for snot / poo, round-specific eat lines.
   Autoplay: random pair with an unseen result. Round 3 (`all_colors`) = one tap per colour group.
5. **Transformation actions** (handler fx in `game/stories/witch_candy/fx.gd`): roll (spin a ball card along a
   path, bonk + bounce back), waddle (duck cycle + cat follows), swim / fly (floating paths round the moon with bob and
   the two-frame wing flap), hop (arc jumps to the roof ridge with a land thud), glow (light dims, an omni light rides
   on her).
6. **Walk in single file** (`file: true` on walk: followers trail the leader along the path with spacing) and a
   ghost-march walk pose (`ghost_cycle` / `ghost_front` cycles exist).
7. **check_lines.py branch-aware**: branch lines are "used" but play only for the chosen result; the guard must accept
   any one result's set per round (seed already scans nested ids).
8. Sound ids listed above; the cat's footsteps (four paws) on its contact frames.

## Prototype (phase 1)
`game/stories/witch_candy/proto/` builds the two places from the new cards with the template look rig at a still:
the night street with the shop and its body, and the room inside it. Captures and notes are in
`artifacts/witch_candy/` (see the progress log entry for what still looks off).

## Open / risks
- Purple and the magenta key: blue-violet still keyed in places; `tools/atlas/fill_holes.py` restores enclosed
  pixels from the raw (purple candies, jars, the sign ribbon). Edges of the paper bats lost a little.
- First passes drew the friends' cycles as Dahyun (the six-figure lineup reference); fixed with single-character
  reference crops (`art_src/cast/raw/ref_wc_<who>.png`). Old raws kept as `_v1`.
- The witch is about 1.25× Dahyun on the sheets (source asked 1.6×); her height_units are set to 0.38 (1.45×).
- The shop facade's doorway is drawn dark, not cut: phase 2 cuts it in the stage band (the inside face has the cut).
