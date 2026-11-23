# Art: find, generate (Codex), slice, catalogue, rig, paper look

## Find before you make (reuse first)
- `game/art/atlas/catalog.json`: 419 cards at first count (trees 77, buildings 40, props 66, bushes 37, flowers 35,
  animals 33, hills 24) across meadow/village/stream/forest/autumn/winter/spring/korean/fairytale_west sheets. Query by
  category/tags/biome.
- `game/art/cast/catalog.json`: the shared cast (started as traveller (15 figures, rigged), sun, wind (3 faces each),
  coat, hat; now every tale's characters, cycles included).
- Contact sheets: `tools/atlas/contact.py`, `tools/cast/contact_cast.py`.
- New generic art (a wolf, a pig, a straw house) goes into the shared libraries with tags; only truly tale-unique art
  goes in `game/stories/<tale_id>/art/`. Catalog every new card with category/biome/season/tags/height_units.

## The paper look (user 2026-11-22: "펠트 질감 싫은뎅", "다시 그려보자")
- No felt anywhere: ground, set cards and characters are paper; no stitch lines. Layered cut / torn paper sheets,
  fine paper-fibre grain, a dark cut line plus a lighter rim on the lit side, matte; no wool fuzz, no fabric texture,
  no dashed stitch lines on hems, aprons, ridges or clouds. Prompts use the PAPER style block (tools/art/sunmoon_jobs.py),
  name the material as cut paper and ban felt, wool, fuzz, stitches and dashed seams explicitly, never "felt" or
  "stitched"; prove the look on one test card (scenery + a character, final light and lens, next to the old look)
  before redrawing a cast. Check a 1:1 crop of ground, a set card and a face.
- Paper is the engine default (2026-11-22): `ground_style` defaults to "paper" (ground, verges, road, stream banks;
  ground shader `paper` uniform, dark cut-line edges); "felt" is opt-in for before/after cards only. The stream shader
  is layered cut paper (torn sheet steps, cut cream ripple slivers, fibre grain, a soft varnish sheen).
- No cream die-cut rim on puppets (user, turnip v3: "흰색 테두리가 별로"): PaperCard gives every card under
  `res://art/cast/` `rim_mix` 0 and a cut wall in the figure's own colour (darkened); CastPuppet `_rim_window` keeps it
  0. Story props that should read as soil (a hole, a heap, a seed) get the same from the handler (turnip fx `_soil`).
  Check baked art before blaming a shader: measure the rings just inside the alpha edge (dark = line art, so the rim
  was the shader). Cut edges elsewhere: papercraft_notes.md (dark line, pale lit-side highlight, never an even white rim).
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

## Generate what is missing (Codex magenta pipeline)
- Jobs: `tools/atlas/make_jobs.py` (props/scenery sheets of ~20–30 sprites) or `tools/cast/make_jobs.py` (characters)
  → `*_jobs.json` → `python3 tools/run_jobs.py <jobs.json> [ids]` (runs `codex exec` with image_gen, waits out rate
  limits, skips existing outputs). Codex image jobs take ~1 min each; 4 in parallel worked without duplicates; seven
  parallel runners gave occasional "no accessible image" failures: retry. Run the runner loop under `bash -c` (zsh does
  not word-split `$var`: tooling.md).
- Prompt = background block (solid #FF00FF, 40 px gaps, no text) + a CATEGORY style block + subject. A shared style
  block leaks ("tiny flower and leaf motifs" printed leaves onto the sun and the wind): keep separate style blocks —
  scenery (folk-art flower/leaf print OK), sky characters (no botanical motifs, no green), characters/animals
  (clothing prints only), buildings — with explicit negatives at the end.
- Cover jobs can live in the tale's own jobs file (`import cover_jobs as _cj; _cj.art/title/back/spot`), so the shared
  tools/art/cover_jobs.py stays untouched while other tales edit it.
- After generation: md5 the raw and compare with all other raws (another session's image once landed in our file),
  accept any wide size (2172x724 was reported FAILED but was fine), key + slice (`tools/atlas/slice_atlas.py`;
  `--join N` for multi-part sprites), look at the contact sheet, regenerate bad ones (extra limbs, face drift, halo,
  wrong facing). Keep old raws.

## Reference images and prompts for characters
- Pass the existing figure sheet as the reference image so faces/clothes stay identical across expression sheets.
- A multi-character lineup as the only ref made the model draw its FIRST character on every friend's sheet (rabbit /
  bear / fox cycles came out as Dahyun). Use single-character crops of the lineup as refs plus "THIS SHEET SHOWS ONLY
  <X> ... do NOT draw <other>".
- A sub-variant of a character (the tiger in the mother's clothes) needs its OWN figure as the reference for its cycle
  sheet: with only the base character as ref, the sneak cycle invented rainbow sleeves and a blue ribbon.
- Walking / running prompts: ask for a visible gap between the legs (figures drawn with overlapping legs can't be
  rigged or read as a stride).
- "Black lips" came out as small dark "O" mouths until the prompt said "thick solid JET-BLACK lips like black
  lipstick, a big black ring around the 'oooh' mouth, NO sheet costume" (one figure came out in a ghost-sheet costume).
- Purples vs the magenta key: say "BLUE-violet indigo plum, never reddish purple or pink" in every block, and run
  `tools/atlas/fill_holes.py` after slicing (add_sheet.py and add_cycles.py do): it restores enclosed holes (purple
  candies, ribbons, jar contents) and undoes the keyer's half-transparency / green despill inside reddish-purple cloth.
- A group of look-alike characters (seven kids) is ONE design drawn with a plain marker colour (a green collar) on
  every expression / cycle sheet; the cast builder clones each figure per member with the marker recoloured and a
  per-member height (`tools/cast/wolf_goats_cast.py` recolour + clone_kids): 7 kids for the price of one sheet set.

## Slice and catalogue
- Never run `tools/atlas/build_catalog.py` or `tools/cast/build_cast.py` for one new sheet: the first moves every
  unlabelled piece of every sheet to rejects, the second rewrites the cast catalog and drops the drawn cycles. Use
  `tools/atlas/add_sheet.py <sheet>` (labels file + optional `merge` of split pieces) and a per-tale cast builder that
  merges (`tools/cast/witch_candy_cast.py`). Sheets with several characters need a per-role height scale.
- The slicer numbers pieces by rows, not left to right — map pieces by bbox, not by index.
- Cycle sheets slice slowly (~3 min each at 2172 px); slice once and use `add_cycles.py --noslice` after fixes. Cycle
  frames drawn close together slice as one piece; split pieces wider than 1.5× the median at their emptiest column
  before cataloguing (`split_wide` in wolf_goats_cast.py), then `add_cycles.py --noslice`. `add_cycles.py --tag X`
  removes the first argument equal to X: a tag equal to the skin name ("rapunzel") broke the call.
- characters.sliced_path(..., "x") drops pieces under 30 % of the tallest: a lineup with a mouse beside a grandpa needs
  an area filter (tools/cast/turnip_cast.py).
- Rig tools are per character (`tools/cast/characters.py`): tails join legs, ears get mistaken for arms (search arms
  between shoulders and hips), figures from different sheets come out at different scales (normalise per character).
- Never run the cast builder's standing pass while Godot imports (tooling.md).

## Changing a drawn feature (witch_candy v4–v5)
- A changed feature must replace the drawn one, not sit on it (user: "검은 입술이 기존 입술위에 덮여서 이상한데? 그리고 계속
  검은 입술로 있는지 검토해봐"; the ghost lips were a ring over a mouth): recolour the feature region
  (tools/cast/wc_black_mouth.py) or draw the variant. The state itself: engine.md ("Character states").
- "Replace" means erase then draw (user: "기존 입술 위에 덧칠하니깐 이상한데"): tools/cast/wc_mouth_v5.py erases a feature
  with a nearby patch of the same material (reject patches containing blush / hair / eyes, colour-match, feather) and
  composites the new feature lifted from a figure where the model drew it natively (same character, same design): a
  whole-figure sheet with the new feature (cast_wc_surprised_black) gave both the reveal figures and the decal source.
  Show three-row crops (original / erased / new). PIL ImageDraw.floodfill does nothing on an image made directly by
  Image.fromarray(numpy): `.copy()` it first.
- Remove drawn breath clouds / puffs the same way (tools/cast/erase_puffs.py; sets.md "Stray effects").

## Front-facing walker rig (legacy, sun_wind traveller)
`tools/cast/cut_cast_rig.py` cuts each full figure into body / hips / leg_l / leg_r (+ `front_legs.py` swaps in
front-view legs, `lift_legs.py` fits half-bent and lifted leg cards, `walk_arms.py` cuts swinging arms from calm
figures and fills the torso under them). Generate, per walker:
- full figures for every expression (same size/framing as the base figure),
- front-view legs (feet toward the viewer), half-bent and lifted leg variants, colour-matched,
- an armless torso sheet for the calm walking figures (arms are cut from the figure itself).
A front leg card wider than the thigh printed on the body card shows as a sliver beside the thigh; trim the hidden top
to the body/hips silhouette with a short taper above the hem (`tools/cast/trim_leg_tops.py`), not a straight cut (that
left a step). Gait parameters that work: motion.md. Drawn cycles replaced this rig for every tale since three_pigs.
