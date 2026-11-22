# 「늑대와 일곱 아기염소」 (wolf_goats) — pop-up tale plan

Phase 1 (2026-11-23): plan, script.json, shared art, first playable wiring. Source (READ-ONLY):
`~/projects/2026/patjuk-game/tales/wolf_goats/`. Seed table: `tools/story/tales/wolf_goats.py` →
`python3 tools/story/seed_script.py --tale wolf_goats [--out <tmp> to diff first]`. Art jobs:
`tools/art/wolf_goats_jobs.py` (+ cover jobs in `tools/art/cover_jobs.py`). Atlas sheets: `tools/atlas/add_sheet.py
story_wg_<cottage|room|hide|fx|meadow>` + `tools/atlas/wg_fixes.py` + `tools/atlas/wg_cottage.py` (door, bands, body).
Cast builder: `tools/cast/wolf_goats_cast.py [--cycles [--only <sheets>]]`; paw cards `tools/cast/wg_paws.py`.
Handler: `game/stories/wolf_goats/fx.gd`.

## Source and the story-first rule
톡톡's READ-MODE script (scenes R01–R10, all recorded, voices nar/mom/kid/wolf) is the tale told straight and already
softened (톡톡 TALES_PLAN_2.md): the swallowing is one line, the kids are unhurt in a warm belly, the mother's body
hides the cutting, the wolf falls into the well and runs away soaking wet. The book follows it; only the play script's
first-tap instructions are borrowed (wg_044, 046, 047, 049, 050, 051), each voiced once. Cut: every narrator tag the
picture shows (READ_SEG_KEEP), lead-ins (r0101, r0102, r0201, r0203, r0204, r0207, r0208, r0300, r0301, r0305, r0401,
r0404, r0502, r0505, r0600, r0602, r0606, r0700, r0702, r0800, r0805, r0806, r0900, r0903, r0905, r1000, r1002), the
semi-moral r1003 and the moral r1005. "하나, 둘, 셋…" (counting) is trimmed off r0802's clip at its pause (TRIM).
Nothing needs recording: the cover / replay prompts reuse witch_candy's clips (same narrator voice id).
Narration used: 229 s (55 lines). Story-start music: 톡톡's own (Schumann 〈만족〉, `intro_happiness`).

## Places (2 spreads, 1 page turn after the cover; seed-2 meadow, paper ground)
- A `home` (view 0): the goats' thatched half-timbered cottage right of the road, turned to face it (yaw −30), a real
  body (side walls, back, thatch slopes) and its room inside the footprint (floor, back wall, the front wall's inside
  face, clock, bed, table, chair, laundry basket, stove); die-cut windows (the kids show through them); a stepping-stone
  path. Up the road on the left the little market stall (chalk); over the bridge the windmill + flour sacks. Beats 1–6
  are camera moves on this one page (glide in / out through the closed front wall, tracking the wolf up the road).
- B `tree` (view 4): the big oak (the wolf asleep in its shade), the stone well beyond it, a hedge across the road
  (the family stands back there), two stones. Beats 7–10.

## Beats
| # | beat | place / shots | taps | ~s |
|---|---|---|---|---|
| 0 | cover | book, intro music | open the book | 8 |
| 1 | home 엄마의 당부 | crane → establish (kids in the windows) → glide into the room; kids hop; the mother out through the door and up the road (go_out) | the mother (wg_046) → her warning | 40 |
| 2 | knock 똑똑똑! | wolf up the path (track), low at the doorstep, knock (door rattles), OTS on the wolf / reverse in the room | — | 28 |
| 3 | chalk 분필과 늑대 | track up the road to the stall, two crunchy taps, voice ding, back to the door, OTS / room, the dark paw at the door gap seen from inside | the wolf ×2 (wg_050) | 45 |
| 4 | paw 하얀 발 | run over the bridge to the mill, the floury paw from inside, the sneeze outside, the kids fooled | the flour sack ×1 | 40 |
| 5 | hide 숨바꼭질 | the wolf bursts in (door inward); the kids dive under the quilt / into the basket / under the table (taps); the youngest into the clock (tap); search; the camera stays on the clock (eyes behind the glass) while we hear three gulps; the heavy wolf waddles out | bed, table, basket; the youngest (wg_047) | 50 |
| 6 | mother 엄마가 왔어요 | dusk; she comes home to the mess, calls; the youngest out of the clock | the clock | 32 |
| 7 | tree 나무 아래 | page turn; the snoring wolf under the oak (snore bubble); mother + youngest tiptoe in; two-shot whispers | — | 30 |
| 8 | belly 늑대 배 | she kneels in front of the belly (her body hides it), three taps → two kids hop out each; stones rolled in; stitched | belly ×3 (wg_049), stones ×2 (wg_051) | 45 |
| 9 | well 우물가 | the family stands back by the hedge; the wolf wakes, waddles to the well (heavy cycle), leans, tumbles in, splash, jumps out soaking wet, runs away (wet run cycle) | — | 35 |
| 10 | together 모두 모였어요 | everyone to the well, dancing hops; close the book | kids ×3 (wg_044) | 25 |

## Cast (shared library, game/art/cast)
- goat_mom (upright, red apron): calm, warn, wave, shocked, call, ready (scissors + needle), dance, hug, shush (side),
  kneel_cut / kneel_sew (side), side / back; walk cycle side 4 + back 2 + front 2 (basket on her arm).
- goat_kid_1..6 (one design, collar recoloured red / orange / yellow / green / blue / indigo, heights 1.12–0.94):
  calm, hop, scared, suspicious, shout, joy, dance, look_up, sit, push, pop, scared_side, side / back; walk 4+2+2,
  run 4+2.
- goat_baby (the youngest, no horns): calm, worried, cry, joy_jump, whisper, side / back; walk 4+2+2, run 4+2.
- wolf (three_pigs' shared wolf; new figures): knock, munch (chalk), sweet, paw_show, sneeze, search (floury paws),
  sleep_full, sleep_stones, groggy, peer_well, tumble, wet; cycles flour 4+2+2, heavy (full belly) 4+2+2, wet run 4+2.
  Existing: calm, shout, hungry, sniff, walk / run cycles.

## Props / sets (shared atlas, tagged wolf_goats + generic tags)
story_wg_cottage (front with door + windows, back, door leaf, room back wall, front wall from inside, floor),
story_wg_room (clock closed / open, bed, laundry basket, table with cloth, chair, messy variants, dresser, stove,
sewing basket, stool), story_wg_hide (hiding variants with the kids: lumpy quilt, basket with ears, table with hooves,
the youngest in the open clock, eyes behind the clock glass), story_wg_meadow (big oak, stone well + rim, hedge,
signpost, chalk stall), story_wg_fx (flour sack, flour puff, splash, chalk, stones, drops, snore bubble, grain,
sparkle). Reused: village_houses_05 windmill, village_props_27 sacks, stream stepping stones. Tale-only: the paw cards.
