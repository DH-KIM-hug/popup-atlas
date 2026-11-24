# Planning a tale

Write this plan into the progress log before building; it is what every agent gets as its brief.

0. Measure the 톡톡 clip durations (ffprobe) to know the narration length before cutting.
1. **Read the 톡톡 script** (`tales/<id>/voice_script_el.json`, `read_script_el.json`, `VISUAL_PLAN.md` if present) and
   list the story beats. Aim for 6–9 spreads, ~3–4 min total (sun_wind ran 3:40–4:00; critics wanted ≤ 3 min — trim
   prompts/hints that repeat).
2. **Spreads**: for each beat pick a world template (meadow today; add `village`, `forest`, `stream`, `snow` templates
   to `game/core/world/` as needed — reusable, seed-placed, catalogue-dressed) and a seed/view where every walking stretch
   has a figure facing its travel direction (front/back/side views per walker).
3. **Cast sheet** (one row per character): role, reusable? (→ shared `game/art/cast/`), walker (front-facing rig) or
   hanger/prop, every pose and expression per beat (start from the lines: each emotional line needs a face), props worn
   or carried, how they enter/exit. For each walker list the directions it travels in each beat (toward / away / left / right) and generate the
   matching views (front, back, side profile — flip for the other side). Never move a card in a direction it doesn't face.
4. **Interactions**: one meaningful tap/hold per beat for a 3–7-year-old (tap a character → line; hold to blow; tap to
   build). Each must have a visible payoff on the page, not only in the narration (critics: "the story cheats the child
   when key moments are only spoken").
5. **Line changes**: mark every changed/new line; count characters for recording and ask the user before recording.
6. **Pop-up moments**: what folds up on each page turn, and one big pop-up set piece per tale (a house rising, a roof
   folding down) — that is the format's charm.
7. **Asset list**: for each card, catalogue id if it exists, else "new (shared)" or "new (tale-only)".
8. **Length**: 톡톡 scripts run ~4+ min of narration; measure clip durations while planning and cut ~40% to reach
   ~3 min. Count narration + page turns + taps before promising a length, and report the change after each round:
   - three_pigs: 36 reused lines play ~189 s on their own; 9 page turns (~5 s each) and ~37 taps put the first full
     run at 5:21.
   - wolf_goats: the first full run was 7:32 (229 s of narration); errands placed a few steps away (stall, mill across
     the road), exits that fold out at the road instead of walking off-page, and dropping lines the taps show bring it
     down.
   - A refrain of seven arrivals (patjuk) is the tale (a line + quote + tap each) but costs ~13 s each: keep the taps
     for the ones the child needs (the kitchen helpers) and let the granny hand the bowls herself in the yard.
   - Measure the idle time before cutting lines (rapunzel v3): per SEG, `next event − start − clip length` from the
     run log; v2 had 182 s idle in 395 s. A pace pass in the tale table (`_pace`: cam rates ×1.4 up to 2.0, settles
     ≤ 0.45, waits ×0.6, walks ×1.4 up to 0.46, climbs ×1.45; the opening crane keeps its slow rate) took 395 → 361 s
     with every line kept, CAM_JUMP / CAM_JERK still 0. Long silent stretches were climbs and room pivots.
9. **Places**: list each place the lines name (텃밭, 부엌, 헛간 지붕, 쥐구멍) and what makes it that place on screen (sets.md).
10. **Branches** (if any): choice space and result tables (engine.md "Branching tales").
