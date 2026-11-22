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
- **No felt anywhere: ground, set cards and characters are paper; no stitch lines.** Layered cut / torn paper sheets,
  fine paper-fibre grain, a dark cut line plus a lighter rim on the lit side, matte. Prompts name the material as cut
  paper and ban felt, wool, fuzz, stitches and dashed seams explicitly; prove the look on one test card (scenery + a
  character, final light and lens, next to the old look) before redrawing a cast.
- Paper is the engine default (2026-11-22): `ground_style` defaults to "paper" (ground, verges, road, stream banks);
  "felt" is opt-in for before/after cards only. The stream shader is layered cut paper (torn sheet steps, cut cream
  ripple slivers, fibre grain, a soft varnish sheen).
- Library redraw: `tools/art/paper_jobs.py` (felt raw = reference, PIECE FOR PIECE) → `tools/art/paper_swap.py
  atlas|cards <sheet>` maps each new piece onto the old card id by position (the slicer numbers by rows, so never by
  index), keeps `<sheet>_felt.png`, rebuilds atlas_clean, and writes a felt-vs-paper QA sheet
  (`art_src/<atlas|cards>/qa/<sheet>_felt_vs_paper.png`) to look at before committing.
  * Redraws re-flow pieces (village_props moved half its props): match by content + position (`assign2`), never by
    position alone; a felt card split by hand (`<nn>a/b`) is matched as its two halves.
  * Paper redraws carry a magenta halo on thin lit rims (needles, grass, plumes): `clean_fringe` refills magenta-
    tinted edge pixels from clean neighbours.
  * Keep the layout: the catalogs keep the felt `px` / aspect (`tools/art/card_aspect_lock.json` for the card kit).
    A 1 % aspect change cascaded through the template placement and re-dressed whole spreads.
  * Per-sheet slicer settings carry over (`JOIN`: village_props needs `--join 4`).
- Finished tales (cast and story sheets with derived art): `tools/cast/paper_reskin.py <tale>` /
  `paper_reskin.py atlas <sheets>` repaint every shipped image (figure, padded cycle frame, rig part, card) from the
  paper raw warped into the felt raw's frame, located by a masked-SSD template match; canvases, catalog and rig stay.
  Pixels a tool painted (pasted doors, recoloured mouths) are kept and counted EDITED; re-run that tool on the new
  art (wc_shop_door.py, house_stages.py for fold bands, wc_mouth_v5.py for ghost mouths).

## Building a world
- **Houses read from front, side and back.** Any piece the camera sees at an angle needs a body: side walls, roof slopes and a back. Build each part as a T of cards (a front card with a profile card behind) so it holds up at a diagonal.
- **No stamped repeats.** Use 4–6 variants per kind, keep identical twins at least 3 piece-widths apart, and leave no empty open patch larger than about 1/6 of the frame.
- **Every standing piece casts a contact shadow.**
- **Cut edges:** a dark line, with a pale highlight on the lit side only. Never an even white or glowing rim.
- **Colour:** the darkest 20 % of the frame is warm, never grey. Keep clipped pixels under about 1 %. Shadows take the world's colour, never neutral black.

## Camera
- Follow smoothing 0.28–0.4 s. Leave a still zone about 1.7 character-heights to each side before the camera starts to follow, and a hard edge at about 3.7 H.
- For capture, use a fixed step with dt clamped, so autoplay recordings are frame-identical across runs. We already use `--fixed-fps`.
