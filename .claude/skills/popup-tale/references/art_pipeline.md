# Art pipeline

## Find before you make
- `game/art/atlas/catalog.json`: 419 cards (trees 77, buildings 40, props 66, bushes 37, flowers 35, animals 33, hills 24)
  across meadow/village/stream/forest/autumn/winter/spring/korean/fairytale_west sheets. Query by category/tags/biome.
- `game/art/cast/catalog.json`: traveller (15 figures, rigged), sun, wind (3 faces each), coat, hat.
- Contact sheets: `tools/atlas/contact.py`, `tools/cast/contact_cast.py`.

## Generate what is missing (Codex)
- Jobs: `tools/atlas/make_jobs.py` (props/scenery sheets of ~20–30 sprites) or `tools/cast/make_jobs.py` (characters)
  → `*_jobs.json` → `python3 tools/run_jobs.py <jobs.json> [ids]` (runs `codex exec` with image_gen, waits out rate limits,
  skips existing outputs).
- Prompt = background block (solid #FF00FF, 40 px gaps, no text) + a CATEGORY style block + subject. Keep separate style
  blocks: scenery (folk-art flower/leaf print OK), sky characters (no botanical motifs, no green), characters/animals
  (clothing prints only), buildings. Put explicit negatives at the end.
- For a character, pass the existing figure sheet as the reference image so faces/clothes stay identical across
  expression sheets.
- After generation: md5 the raw and compare with all other raws (a foreign image once landed), accept any wide size,
  key + slice (`tools/atlas/slice_atlas.py`; `--join N` for multi-part sprites), look at the contact sheet, regenerate
  bad ones (extra limbs, face drift, halo, wrong facing). Keep old raws.
- Catalog every new card with category/biome/season/tags/height_units so later tales find it.

## Front-facing walker rig (characters that walk)
`tools/cast/cut_cast_rig.py` cuts each full figure into body / hips / leg_l / leg_r (+ `front_legs.py` swaps in
front-view legs, `lift_legs.py` fits half-bent and lifted leg cards, `walk_arms.py` cuts swinging arms from calm
figures and fills the torso under them). Generate, per walker:
- full figures for every expression (same size/framing as the base figure),
- front-view legs (feet toward the viewer), half-bent and lifted leg variants, colour-matched,
- an armless torso sheet for the calm walking figures (arms are cut from the figure itself).
See walk_rig.md for the gait parameters that work.
