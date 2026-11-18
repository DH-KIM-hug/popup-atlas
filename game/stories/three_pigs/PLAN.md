# 「아기 돼지 삼형제」 (three_pigs) — pop-up tale plan

Phase 1 (2026-11-18): plan, script.json, shared art. Phase 2: runner verbs/fx, spreads, wiring, recording, critics.
Source (READ-ONLY): `~/projects/2026/patjuk-game/tales/three_pigs/` (voice_script_el.json 58 lines; voices nar, mom,
piga, pigb, pigc, wolf). Seed tables: `tools/story/tales/three_pigs.py` → `python3 tools/story/seed_script.py --tale
three_pigs [--force]`.

## Pace
36 lines used (34 reuse 톡톡 clips, 2 new), narration ≈ 165 s (+ hints only when idle). With ~37 taps and 9 page turns
the run is estimated at **≈ 3:20–3:30**. Cuts already made: clothes quiz (4–12), fan/shop test (13–17), "어느 집으로?"
quiz (35–39), inside count (40–42), line 30, 54, narrator lead-ins of 1/23/28/32 (seg trims, clips reused). If the
first full run is over 3:15, next cuts: 47 (털썩 — show it, don't say it), 23 → piga seg only, brick taps 10 → 5 (would
change line 24 "열 장" → re-record).

## Beats → spreads (meadow template, seed 1; each beat one page)

| # | beat (tab title) | spread / place | walking (view) | interaction (payoff on the page) | lines |
|---|---|---|---|---|---|
| 0 | cover | — | — | tap the book | tp_n01 |
| 1 | home (엄마의 배웅) | view 5, village edge; mom's cottage `village_houses_20` | pigs walk AWAY up the road (back views), mom waves | **tap each piglet**: it hops + waves, its material (straw sheaf / plank / brick card) pops up above it on a hinge | 000, 001 (mom only), 002, 003 |
| 2 | straw_build (첫째의 짚 집) | view 2, wheat-field edge (straw lot) | 첫째 carries straw pile → house and back (SIDE view, flips facing) | **tap ×3**: each tap one band of the straw house folds up (wall, wall + door, thatch roof); star burst; flute + notes | 019, (018 hint), 020 |
| 3 | wood_build (둘째의 나무 집) | view 3, forest edge (wood lot) | 둘째 at the house, hammer pose bobs | **tap ×5**: hammer bang, a plank band folds up per tap (4 wall bands + roof); violin + notes | 021, (018), 022 |
| 4 | brick_build (셋째의 벽돌 집) | view 4, village green (brick lot) | brothers stroll past sideways (SIDE) playing flute/violin at tap 5 | **tap ×10**, counted 1–10: a brick flies onto the wall each tap, every 2nd tap a brick band folds up (4 wall + roof/chimney) | 024, 023 (at tap 5), 025 |
| 5 | wolf_straw (후~ 짚 집) | straw lot (house full) | wolf prowls in from the left (SIDE, facing right, sniff pose), 첫째 runs off right (SIDE run) | **tap with the wolf ×3** (each tap = one 후~: wolf huff pose + wind streams, straw tufts fly, the top band peels); 3rd tap: all bands fold DOWN, blown-apart heap card pops up | 027, 028 (trim), 026 prompt, 029 |
| 6 | wolf_wood (후~ 나무 집) | wood lot (house full) | wolf in (SIDE), the two pigs run off right (SIDE run) | **tap ×5**: house wobbles harder each tap (흔들흔들); 5th: bands tumble down, plank-pile ruin pops up, splinters fly | 031, 032 (trim), (026), 033, 034 |
| 7 | brick_wolf (쿵쿵쿵!) | brick lot, dusk light | wolf in (SIDE), three pigs at the windows | **tap ×8**, counter 1–8 on the page: the house only shivers (no band moves), pigs cheer; wolf sits down exhausted (static card, dust puff) | 043, 044, 045 prompt, 046, 047 |
| 8 | chimney (보글보글) — **set piece** | brick lot, dusk | wolf tiptoes up the roof slope to the chimney (SIDE tiptoe) | facade **folds DOWN toward the reader** and the kitchen pops up behind it (hearth, pot, pigs); **tap the fire ×3**: small → medium → large flame, steam puffs grow, pot bubbles; wolf drops down the flue (front "falling"), splash + steam, "앗 뜨거워" (front ouch), shoots back up, facade folds up again, he runs off LEFT (SIDE card flipped) into the distance | 048, 049, 050, 051, 052, 053 |
| 9 | ending (벽돌 마을) | brick lot + two empty plots | — | **tap the plots ×2**: a whole brick cottage pops up on each (full hinge rise); pigs cheer; end card | 055, 056, 057, end tp_n02 |

Pop-up moments: every house is built band by band on hinges (straw 3, wood 5, brick 5 bands —
`game/art/atlas/story_houses/stages/`), the straw/wood houses fold down into their ruins, and the big set piece is the
brick facade folding open into the kitchen (beat 8). Page turns as in sun_wind.

Places needed on the template (phase 2, `spread.place`): home (village edge with a cottage + gate), straw_lot (by the
wheat field), wood_lot (forest edge), brick_lot (village green, room for 3 houses: lot, lot_left, lot_right), plus a
pile spot next to each lot and a side path (left→right across the frame) for the side walkers. Dusk light for 7–8.

## Cast sheet (all SHARED in `game/art/cast/`, role = skin)

Views: front (toward camera), back (away), side (profile drawn facing RIGHT; flip the card for leftward travel —
never move a card the way it doesn't face).

| role | design | views used (beats) | poses / expressions (cast id `cast_<role>_<pose>`) |
|---|---|---|---|
| pig_a 첫째 | straw hat + mustard scarf, 0.24 | front 1,5,7,8,9; back 1; side 2,4,5,6 | calm, happy_wave, scared, defiant, flute, panting, tease, side_walk, run (side), carry_straw (side), back_walk |
| pig_b 둘째 | blue overalls, hair tuft | front 1,3,6–9; back 1; side 4,6 | calm, happy_wave, scared, defiant, violin, panting, hammer, side_walk, run (side), carry_planks (side), back_walk |
| pig_c 셋째 | cream cap + red overalls | front 1,4,7–9; back 1; side 4 | calm, happy_wave, brave, startled, defiant, lay_brick, proud, cheer, side_walk, carry_bricks (side), back_walk |
| mother_pig 엄마 | red polka-dot headscarf, sage dress, apron, 0.31 | front 1, 9 | calm, wave, talk (not a walker) |
| wolf 늑대 | upright grey wolf, patched mustard waistcoat, 0.40 | side 5–8 (prowl, sniff, tiptoe, run_away), front 5–8 (shout, hungry, ouch, falling) | calm, side_prowl, back_walk, sniff, huff (side), exhausted (side, sitting), tiptoe, run_away, shout, hungry, ouch, falling |

Line → expression map: `LINE_META` in `tools/story/tales/three_pigs.py` (copied into script.json as `expr`).

Rigs (`game/art/cast/rig/rig.json`): front walkers get front legs + half/lift variants (pig_a/b/c calm,
happy_wave, scared/brave/startled, defiant, panting, tease/hammer/proud/cheer; wolf calm, shout) and the calm
figures swinging arm cards (auto-cut). Side walkers (side_walk, run (pig_a), carry_planks, carry_bricks, wolf
side_prowl, sniff) get drawn side legs on one hip joint. Back walkers (pig back_walk) are cut from their own legs.
NOT rigged (legs drawn together / overlapping; static cards, move them with a paper hop): pig_a_carry_straw,
pig_b_run, wolf_back_walk, wolf_tiptoe, wolf_run_away, wolf_hungry, plus non-walkers (flute, violin, lay_brick,
huff, exhausted, ouch, falling, all mother_pig).

## Line changes (record only after the user OKs the spend)
- NEW `tp_n01` "그림책을 톡 눌러서 펼쳐 볼까요?" (cover), `tp_n02` "또 보고 싶으면 '다시 보기'를 톡!" (end) — 3pigs narrator
  voice (Annie); sun_wind's recordings of the same text are another narrator voice. 86 characters total.
- Seg trims (no recording): 001 mom only, 023 piga + "그래도 셋째는…", 028 piga + wolf, 032 pigb + wolf.

## Assets
Reused (catalog ids): `village_houses_20` thatched cottage (mom's house), meadow/forest/village dressing of the
template (wheat field, conifers, village houses, fences, flowers), `meadow_field_05/06/07` haystacks (straw lot),
`village_props_17` woodpile + `forest_conifer_14` log (wood lot), `village_props_22` picket fence, `village_props_21`
bucket. Rejected for this tale: `farm_animals_07` pig (side-view farm animal, not our characters), `korean_*` straw
houses (wrong culture/look).
New SHARED props (`game/art/atlas/`, categories `story_building` / `story_prop` / `story_fx` — never queried by the
meadow template, so sun_wind's layout is unchanged):
- `story_houses_00..10`: straw / wood / brick house facades (fold bands in `story_houses/stages/`), side walls,
  straw blown-apart heap, wood collapsed pile, two more brick cottages, chimney stack.
- `story_build_props_00..22`: straw sheaf, straw pile, 3 flying straw tufts, plank stack/plank/crossed planks, brick
  pile/brick/brick on end, hammer, trowel, mortar bucket, flute, violin, drum, wheelbarrow of bricks, loose door,
  broken roof, 2 splinters, sawhorse.
- `story_hearth_00..18`: fireplace hearth, cooking pot, 3 flames, logs, 3 steam puffs, splash, soot puff, chimney top
  with smoke, table, stool, shelf, curtained window, rug, ladle, star burst.
New SHARED cast: 26 pig figures, 3 mother pig, 12 wolf (above). Nothing tale-only.

## Runner work for phase 2 (NOT implemented; game/story/** belongs to phase 2)
Generic verbs (story_runner.gd):
- `who` on `walk` / `pose` / `enter` (several cast members, role ids from `cast`), `dir` on walk (toward / away / left /
  right → picks front / back / side figure, flips side cards, ~0.15 s paper turn), `speed`, `pose` per walk.
- `tap_each {targets, prompt, hint, react{role: [pose, fx]}}` — wait until every target was tapped once.
- `build {house, target, taps, hint, walker, carry, fx, counter, steps[{at, fx, lines}]}` — tap progress; band k of the
  house's stages.json folds up on its hinge every taps/bands taps; walker carries / hammers per tap.
- `huff {house, taps, prompt, hint, fx, counter, result: blow_apart|collapse|hold, ruin}` — tap progress with the wolf;
  result folds bands down and pops the ruin card, or only shivers the house.
- `tap_steps {target, prompt, hint, steps[{fx, lines}]}` — generalised `shine` (fire, new houses).
- `climb {who, to: chimney, pose, line}` — walk along a path up the roof slope (side view).
- spread fields `place`, `set[{card, at, stage}]`, `light: dusk`; cast entries data-driven (CastPuppet per role with
  front/back/side figure sets; side gait = fore/aft leg swing about one hip, ±20–25°, arms swing opposite).
- on-page counter cards (1–10) for `counter`.
Tale fx (per-tale handler `game/stories/three_pigs/fx.gd`): pop:<card id>, straw_pop, hammer_bang, brick_thunk,
star_burst, flute_notes, violin_notes, brothers_tease, straw_fly, wood_wobble, house_shiver, thud_dust, cutaway_open /
cutaway_close (facade folds down / up, kitchen set pops), flame_m, flame_l, boil, wolf_drop, splash, wolf_launch.
Sounds: straw rustle, hammer, brick thunk, wind huff, collapse, boil, splash, yelp (톡톡 has matching SFX names).

## Open / risks
- Wolf front figures: a thin sliver of the leg top shows beside the left thigh (the tail overlapped the leg; trimmed
  but not perfect). Wolf runs/tiptoe are unrigged (hop them).
- House bands cut straight through windows/doors (reads as die-cut layers; check on screen). Wall bands keep tiny
  eave tips at their top corners on the wood/brick houses.
- Nobody has listened to the reused clips in this context; the two new lines are unrecorded.
