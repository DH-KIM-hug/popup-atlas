# Notes adopted from xikhar/papercraft (2026-11-21)

Source: github.com/xikhar/papercraft (MIT), an agent skill for pop-up papercraft scenes. The user pointed us to it. Below are only the parts that fit this app. Our look stays the one the user chose (photographed miniature, night skies when the story needs them), so its bans on sky and horizon do NOT apply here. Its felt ban DOES apply: the user dislikes the felt ground (2026-11-22); build grounds as paper.

## Process
- **Write a paper spec before building a new set or spread.** Put it in PLAN.md, one line per field:
  - SUBJECT: what the reader looks at first
  - PALETTE: 4–7 hex values from the brief, each with a role
  - LIGHT: key colour and direction, shadow tint, practical lights
  - LENS: fov, pitch, focus band
  - GROUND
  - LAYOUT: leading line, hero placement
  - MOTION
  - SOUND
  - BANNED: tells this set must not show
  - QA: which frames prove it

  Audit the spec: if it would fit any similar prompt, it is too generic.
- **Prove one test card first.** Put a single new card kind (a house with its body, the pot with its liquid) under the final light and lens before you dress a whole street with it. witch_candy's flat angled fronts and dark pot liquid would have shown up on one test card.
- **Measure, then critique.** Fix the top three problems per round, then stop and show the user.

## Motion of cards
- **Pop-up rise:** upright in 0.18–0.32 s, overshoot 8–15 %, a 2–3 cycle quiver at 4–6 Hz, still by about 1 s.
  - Stagger the parts of one piece by 0.2–0.35 s.
  - A whole set must never sit half-popped while the reader looks at it ("어떤 건 서 있고 어떤 건 안 서 있고"). Either everything stands when the page opens (`pop_in: false`), or the wave finishes before the first line.
- **Fold down:** a ~2° outward twitch, a soft fall and one small slap, done in 0.5–0.85 s.
- **Rigid things never sway:** walls, roofs, houses, rocks, and anything walked on (steps, decks, bridges). Idle sway is at most 2.5°, and only for plants, flags and hanging decorations, each on its own hinge.
- **Gait follows distance travelled, never time.** We already do this.

## Walkable structures (the doorstep and steps lesson)
- Build anything a character walks on as an open construction (treads, deck, rails), never as one standing card the walker passes through.
  - Stair rise is at most about 1/8 of character height per step, and the run is about 0.3 H.
  - Treads overlap the next surface by at least about 0.03 H, so feet never drop between them.
- Keep a walk field (a height per ground cell), where the highest surface wins. Actors take their y from it, so climbing steps and thresholds just works instead of being hand-keyed per door.

## Material (user 2026-11-22: "펠트 질감 싫은뎅", "다시 그려보자")
No felt anywhere; paper is the engine default. The full rule, the stream shader and the library redraw / reskin tools
(paper_jobs.py, paper_swap.py, paper_reskin.py) live in art.md ("The paper look").

## Building a world
- **Houses read from front, side and back.** Any piece the camera sees at an angle needs a body: side walls, roof slopes and a back. Build each part as a T of cards (a front card with a profile card behind) so it holds up at a diagonal.
- **No stamped repeats.** Use 4–6 variants per kind, keep identical twins at least 3 piece-widths apart, and leave no empty open patch larger than about 1/6 of the frame.
- **Every standing piece casts a contact shadow.**
- **Cut edges:** a dark line, with a pale highlight on the lit side only. Never an even white or glowing rim.
- **Colour:** the darkest 20 % of the frame is warm, never grey. Keep clipped pixels under about 1 %. Shadows take the world's colour, never neutral black.

## Camera
- Follow smoothing 0.28–0.4 s. Leave a still zone about 1.7 character-heights to each side before the camera starts to follow, and a hard edge at about 3.7 H.
- For capture, use a fixed step with dt clamped, so autoplay recordings are frame-identical across runs. We already use `--fixed-fps`.
