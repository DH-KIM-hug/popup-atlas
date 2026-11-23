# Sets: houses, building kit, rooms, doors, props, overlaps, ground, gardens

Set entry fields: script_schema.md ("Data-driven stage", "Buildings from the kit"). Paper spec and test card before a
new set: papercraft_notes.md.

## Placement on the page
- Pick spots with `tools/story/probe_spots.gd` (ground map: water / road / grass around the anchor) before choosing
  spots: view 2's anchor sits on the stream — the first straw house and the wolf stood in the water. Streets: probe the
  road with `tools/story/probe_spots_wide.gd`.
- Houses go on open meadow beside the road, never across it (user: "the brick and wood houses are built across the
  road"). SpreadStage prints `SET_CHECK <name> road=<n> water=<n>` for every set piece (base-line samples against the
  path and stream); run all beats (`tools/story/cap_beats.py TALE tag 40 <beats...>`) and require zeros.
  `_check_footprint` samples along the piece's own base line (turned pieces).
- Adding cards to the shared library can change existing spreads (templates pick cards by category). Give
  story-specific set pieces their own categories (`story_building`, `story_prop`, `story_fx`) or check sun_wind's
  layout is unchanged.
- A template card (hill) in a close shot's lens on a new spread: a tiny set entry with a big `clear` opens a lawn.
- Ground terraces (raised meadow steps) are not set pieces: they can hide kids standing behind them and stand in a
  close shot's lens, and the overlap check cannot see them. Keep marks and close shots off the terrace edges.
- No half-popped scenery at a spread's start (user: "어떤 건 서 있고 어떤 건 안 서 있고"): unless a tale wants the wave,
  everything stands when the street first shows (tale `pop_in: false`); a house's walls / roof never stand without its
  front or the reverse. Check the first 10 s at 4 fps.

## Villages and streets
- A street needs many houses, each dressed differently (user: "마을을 더 많이 각자 할로윈 장식"): generate night
  facades with their own decorations drawn in, plus an add-on decoration sheet, and lay them out from the probed road
  in the tale table (x from the road edge, SET_CHECK zeros).
- Houses face the road from both sides (user: "집 문이 길쪽으로 나있어야 미국식 집 구조"): set `yaw` ±50° in the stage
  frame, each with a short stepping-stone path to the road's edge; offsets inside a turned house (room spots,
  decorations, door) are given in the house's own frame and rotated in the tale table; shots inside / at a turned
  house carry its yaw as their yaw offset.
- Night is not a light preset alone: the depth haze kept its daytime grey-green. Spread `sky` sets the backdrop / haze
  colour and adds a fog-free sky card (stars) + moon far behind; `glow` on set entries makes printed light emit (only
  bright warm texels) and `light` adds warm pools (flicker for candles / pumpkins).
- A non-western tale dresses the template with `theme` (engine.md).

## Houses solid from every angle (user rule 2026-11-23: "집들은 무조건 입체적으로 아주 잘 들어맞게")
- Every house / barn / shop / cottage in every tale (story set pieces AND the template village's houses) is a closed
  volume whose pieces fit tightly: no flat front cards, no slit between front, sides and roof, no background through
  corners, under eaves or along the ridge, roof neither floating nor sunk, chimney seated, back filled, door / window
  reveals, sides in the front's own material, readable from any story camera and from oblique orbit angles. Angled
  houses especially ("사선으로 돼 있으니까 집도 집처럼 보여줘야"); an open door must show an interior ("문열때보면 뒷편이
  없는곳으로 가다보니 이상한디?", "집 뒤편도 있어야하지않을까유").
- Drawn fronts get a BODY automatically: `tools/atlas/house_bodies.py [ids] --sheet <contact.jpg>` traces each card's
  outline (chimney cut off by a 1-D opening of the roof line, thin strings opened away, walls fitted as lines through
  the drawn wall edges, the eave line = the overhang's underside), writes `game/art/atlas/bodies.json` (merge) +
  crops of the house's own art (`<sheet>/bodies/<id>_side|roof|back|chimney.webp`: the most wall-like / roof-like
  patch, mirror-tiled; the back = its own gable over plain wall). `game/core/world/house_body.gd` (HouseBody)
  extrudes the outline back: side walls on the wall edges, the roof surface along the drawn roof line, soffits under
  the overhang, the outline filled at the back, the chimney as a box seated in the roof, every face doubled inward
  (darker) for cameras inside. It starts at the card's FRONT face, grown 0.8 mm: a PaperCard's own cut edge does not
  draw from above, and a body that started behind the card left a slit along the roof (found with the orbit probe).
- Where bodies attach: SetPiece `box` (enterable houses: rooms, refuges; floor / ceiling / `inner` back wall from the
  box cfg still apply; `body: true` and side / inner side cards are superseded) and AUTOMATICALLY on every set entry
  whose card has a bodies.json entry (turnip's farmhouse and barn, sunmoon's gate house, the goats' mill, the pigs'
  home); auto bodies are not `enterable` (house_of / overlap logic unchanged). Banded houses keep their build: the body
  stands only when the house is whole and folds with band 0. The template village's house cards get bodies too
  (meadow.gd `_add_house_body`: on the card's hinge, or at the static card's transform; the clean atlas copies are
  cropped: `clean_off`). Door / window reveals (`HouseBody.add_reveal`) line every door_box / window_box.
- The clean copy offset, the inner faces and the winding: Godot draws the clockwise side (HouseBody._wind keeps
  quads clockwise seen from their outward normal). Test a new body with the orbit probe, not a story still.
- AUDIT every tale's houses with `tools/story/house_orbit_all.sh OUT LABEL [tales]` (house_orbit.gd per beat: each set
  house + the nearest template houses, nine solo views on magenta: front, ±35°, ±70°, back-¾ both sides, high, low,
  plus the story shot; `tools/story/house_audit.py` paints background seen THROUGH the house red and counts it). Red in
  a closed house is a defect; in a pavilion, gateway or courtyard it is the real opening.
- Older body routes, still in use: a `box` (set entry: depth, side, inner, floor cards) gives an enterable house side
  walls in the house's material, an inside back wall, plank floor and ceiling, and the front turned round at the back;
  it stands only while the house is whole. tools/atlas/wc_house_bodies.py splits each front into wall / roof bands,
  crops a strip of its own wall (side walls, back) and roof print, finds eaves + ridge (SetPiece `box: {body: true}`:
  side walls, a back, two roof slopes and the gable repeated at the back). `tools/atlas/sm_cottage.py` shows how to
  merge fold bands + door leaf with a `wc_house_bodies` body in one entry.

## Buildings from the kit (non-box buildings)
- Buildings that are not one drawn front (팔각정, round towers, hanok with curved eaves, pagodas, castles) are built in
  3D from a spec, never a flat card: `game/core/world/building.gd` (Building) + `game/art/buildings/kit.json`
  (res://art/buildings/kit.json; presets and materials, written by `tools/atlas/building_kit.py`; paper swatches
  `story_bk_materials`, doors / windows / gate / portcullis / drawbridge / flags / railings / finial `story_bk_parts`;
  another agent owns that code). Place one with a set entry
  `{"build": "<preset>" | {spec}, "at", "yaw", "scale", "state": {"portcullis": 1, "drawbridge": 1}, "name", "clear"}`
  (SetPiece.setup_building: one hinge, pops with the page; `sp.set_state(key, v)` moves a portcullis / drawbridge).
  `stage: 0` + fx `pop:<name>` raises it. Spec format and presets: script_schema.md ("Buildings from the kit").
- To change a preset for one tale (an OPEN window without its glass card) read the preset at seed time, edit a copy
  and pass it as the spec (tools/story/tales/rapunzel.py `_tower_spec`); the handler reads `SetPiece.building.spec` /
  `.unit` for positions (window sill = opening y × unit, wall at r × unit along the building's own +z).
- A window someone leans out of / a room at the top (rapunzel v2, user: "탑에 있는 라푼젤...뭔가 이상한디", "탑 위에서
  만나는거 같지도 않자너"): on a round / ngon part an opening wider than one facet was silently clipped to the facet (a
  22-gon facet is a slot) and centred off the part's +z: give the part `flat: <width>` (a straight front chord, edge 0
  centred on +z), size the opening to the figure (the peek head ≈ 65 % of its width), `ledge` for the sill slab, `open`
  for no glass card, `floor` + the part's own walls for the room behind it, `flare` to corbel a wide top room out over
  a slim shaft. The window figure stands IN the reveal (behind the outer face, hands on the sill), not on the wall.
  The room is the building's own top storey: the camera follows the climber up and dollies in through the window
  (outside and inside shots share one focus deep in the room, elevation and height: only the distance changes, so
  the path is a straight line through the opening); `Building.room_at` makes `house_of` / `camera_inside` treat the
  room as inside (speaker / occlusion checks). Turn round inside by pivoting at the room's middle (shot distance
  ~0.1), never about a far focus (the lens swings through the cast). What the window shows from inside is staged:
  treetop cards beyond it, below the eye line, visible only while the camera is in the room (the template has
  nothing toward the reader but haze). Never a separate room page standing in a field.
- Kit sheet: house_orbit.sh with a 6th argument (presets) renders the solo orbit + a context shot on the meadow
  (castle: approach, gate, tower window).

## Fold-up houses (builds)
- Generate one finished front and cut it into layers along mortar/plank/straw lines (`tools/atlas/house_stages.py`);
  generating separate aligned pieces is unreliable.
- Fold bands: cut rows that cross no window, step the cut around doors (the door rises whole with the first band) and
  hand-pick rows when the windows leave no room (`OPENINGS` / `CUTS` in tools/atlas/house_stages.py).
  `house_stages.py` misreads fronts whose stone base is wider than the walls: give `ROOF_Y` / `WALL_X` per house.
- Stray pixels in a band image stretch its card: PaperCard sizes `height` to its contour bounds (specks dropped)
  while the stage positions by the image's opaque rect; the wood roof band carried a few edge pixels down to the floor
  and drew as a giant gable. Keep band images free of specks (house_stages.py eave-tip rule).
- A house's first build stage must read as a house beginning (floor, lower walls, door), not a lone door; stand it at
  the page open (`"stage": 1`) and let the taps raise the rest (the build verb counts from the bands standing).

## Doors and entries
- A drawn doorway is not a hole: paste the door art into the doorway, then cut the leaf with DOORS (5th value = the
  leaf's bottom row so the steps stay on the wall) — `tools/atlas/wc_shop_door.py`, `house_stages.py` (GLASS / DOORS
  for die-cut windows and doors).
- Entries climb the steps (user: "문에 겹친다던지 문 아래 돌지방을 통과"): the door swings INTO the house (`door_in`) and
  fully open before anyone moves (`door_clear`); characters climb to the drawn sill (`climb_steps`, SetPiece.door_sill)
  in front of the wall, cross at sill height (their card is parallel to the wall when the camera faces the door) and
  step down inside; exits reverse it (tale `leave_shop`). One at a time or a tidy file; nobody overlaps the door card
  or passes through the threshold stone; one door cycle per group, everyone enters seen from behind. A character
  taller than the doorway pokes its hat over the wall while on the sill: size it to fit. Walkable structures:
  papercraft_notes.md.

## Rooms and refuges
- A refuge's walls stay closed in-story; show interiors by moving the camera inside, not by opening the wall the
  threat could walk through (user: "방이 열려도 앞 벽은 막혀있어야하는거아닌지", "굴뚝으로 들어가면 그제서야 안을 보여주면
  되자너"). Build the room inside the house footprint from the start of the beat (hidden by the facade), glide the camera
  in only after the threat has entered (SpreadStage hides a facade's wall bands only while the camera is within 0.16 of
  it or behind it; `inside_only` pieces such as a ceiling show only then), and glide back out to the closed house.
  (Superseded for refuges: a facade folding open into a cutaway room — story_room sheet back wall, angled side walls,
  floor, furniture, hearth connected to the outside chimney with a flue.)
- One spread with a house that has a body + a room inside its footprint lets characters go in and out many times with
  camera glides only (no page turns). The room back wall must be the wall's full height (derive a taller card) or a
  gap shows the outside above it. The meadow can rise through a box floor: lay raised floor cards.
- Reusing another tale's house for a room people act in: size the house to the cast first. sunmoon's cottage room
  (0.62 deep) could not frame the 0.57-tall tiger (giant paws, cut-off heads); the cottage stands 1.3× with a 0.95
  body, its front line where it was (only door x and the inside scale). Room camera rules: camera.md "Interiors".
- A room on its own page as a ring of inside-wall cards (rapunzel v1) read as a cutaway box standing in a field
  (user: "탑 위에서 만나는거 같지도 않자너"): superseded; a room the story places somewhere (the top of the tower) is that
  building's own interior on the same spread ("Buildings from the kit").

## Props: appear, travel, leave
- Set pieces and props appear only when the story reaches them (stage 0 + fx `up:` at their beat; `built` for later
  beats): houses are empty lots until their build ("둘째 집 짓기도 전에 있음"), materials and tools appear only in their
  beat ("돼지 세마리 갈때 짚이랑 벽돌을 왜 가지고 있지"); props the story uses later are found or brought by whoever uses
  them (the wolf finds the ladder in the grass and stands it up).
- A prop the narration brings must travel on screen ("초대장이 날아왔으면 좋겠고"): the invitations ride a curving,
  flipping path from the far street to the kids with the camera tracking (handler `_track` node drives the stage
  focus), then open toward the camera when caught.
- A prop that leaves the story leaves the screen: the golden rope rises away (fx `rope_gone`) before the rotten one
  comes down, and the drop happens during its line, in shot.
- A rope / braid from a window: a column of tiled cards from the sill to the grass, offset along the building's own
  front normal beyond its wall + plinth (never through the wall), unrolled top to bottom; overlap contacts
  (climber / braid / tower) go in `overlap_ok`. Climbing: motion.md.
- A growing thing is ONE card sunk into the paper ground (the ground hides what is below it at any camera elevation we
  use): the giant turnip stands at its spot sunk to its violet shoulder and each heave raises it a little; measure the
  drawn bulb's height on the card first (the root tail is long: the first sink showed the whole bulb by the fourth
  pull). Growth stages before it are card swaps with a paper pop (sprout -> rosette -> crown -> sunk turnip).
- Things that land or are set down (the pulled turnip) go behind the actors, never between them and the camera
  (OCCLUDE), and leave with the story (carried to the table, cooked).

## Nothing overlaps (user: "최대한 겹치게 하지마라는 규칙은 없었나", "물체랑 사람들끼리 자꾸 겹치잖아")
- No character, set piece or fx prop (ropes, jars, baskets, flying props) may sit inside another or hide a speaker.
  OVERLAP_COUNT and OCCLUDE_COUNT must be 0 in the final run, or each remaining line listed as an intended contact
  (`overlap_ok`) with a reason. The sunmoon rope hung through the tree canopy ("동아줄이 나무에 걸려서 뭔가 이상하네융")
  until it was offset along the tree card's own normal in front of the trunk.
- Stage `overlap_check` logs OVERLAP (footprints: actor / actor, actor / set base line; open doorways excluded) and
  OCCLUDE (a nearer piece covering > 35 % of an actor, only pieces the camera can see: inside a house only its room)
  with OVERLAP_COUNT at the end; OVERLAP_COUNT / OCCLUDE_COUNT in the summary are run totals over every page (they used
  to be the last page's own counts, so a page-A overlap printed as "OVERLAP_COUNT 0"). `spacing` eases standing actors
  apart. fx props join the check: `stage.register_prop(name, node, r, h)` (moving props carry meta "moving"); it logs
  prop vs actor footprints, props inside set pieces and props hiding an actor.
- The big sources were not marks but movement: a group walking to one goal, followers bunching at the first waypoint
  of a file, a U-turn through the file, people cutting through furniture to their marks, a queue reaching the next
  house. Fixes: walk by distance (formation kept), snake-follow files (followers on the leader's trail at fixed
  spacing), two-lane loops, `via` waypoints round furniture (and who enters first), queues along the house front.

## Ground areas and gardens (turnip v2–v4)
- The place named in the story must read on screen (user: "순무는 텃밭이 없네용?"): a 텃밭 is tilled soil with rows, not
  meadow. v1 grew the turnip on plain green paper with one tiny raised-bed card far behind. Before wiring, list each
  place the lines name (텃밭, 부엌, 헛간 지붕, 쥐구멍) and check one wide and one close frame of each shows what makes it
  that place.
- A ground area is a FLAT card, not a standing one: set entry `"flat": true, "floor": true, "lift": 0.016` lays a
  top-down piece on the page (its `at` is the front edge; it runs away from the camera by its height) and registers
  its rectangle in `GroundLayers.floors`, so people, spots and later set pieces stand on its top (cover patches stay
  under it). Keep it a SHEET, not a slab (user on v2: "a thick brown slab / rug floating"): `"thick": 0.0015`,
  `"edge": "<soil colour>"` (the cut edge in the sheet's own dark colour, never the cream card rim) and the smallest
  lift that clears the ground's cover patches under it (probe them: tools/story/probe_ground_tn.gd res=0.005
  abs=0.022; 0.007 high), grass tufts / edging on the rim. Low shots flatten it: stand low cards on it (vegetable rows
  with their own soil ridge, fence, edging) and raise close-shot elevations a few degrees (8° → 13°) so soil and rows
  stay in frame.
- Shared kit: atlas sheets `story_veg_garden` (soil ridges, lettuce / onion / small-turnip / strawberry rows, tomatoes,
  peas trellis, pumpkin vine, picket fence + open gate, wheelbarrow, basket, row markers, stone edging) and
  `story_veg_ground` (tilled plot / dug patch / stepping-stone and earth paths, top-down, lay flat): jobs
  tools/art/garden_jobs.py; after `add_sheet.py` run `tools/atlas/veg_garden_fix.py` (fill_holes restores the magenta
  rims of REAL holes such as wheel spokes and trellis gaps; it clears them, tones the plot toward cocoa brown and
  writes mirrored copies `<id>m` of the row cards).
- No stamped rows: mix pieces in a row, use the mirrored copies, vary scale (0.85–1.12), turn ±3–6°, uneven gaps and a
  few mm of depth jitter. Tools lying around (a rake) lie FLAT (`flat: true`) when they sit near a walk: a standing
  tool card on a route counted OVERLAP / OCCLUDE in three places before it lay down.
- Lay out a garden around the action: rows on one side, an open bed where the line stands, nothing on the walk routes
  (house door → gate gap → line, line → feast table).
- Holes read as what the story says (user: "구멍을 그렇게 파니...?"): a planting hole is a dark dip laid FLAT in the
  furrow plus a low heap beside it, never a mound with an arch (that is a burrow); a mouse hole is a low bank tucked at
  an edge (tools/atlas/tn_holes.py derives all three from cards we had). Soil props get the soil cut edge (art.md).

## Stray effects (user: "이상한데서 김이 모락모락", "셋째집 연기뭐지?")
Steam only where something is hot, from its mouth. Look for smoke / puffs nobody asked for: the template's ChimneySmoke
keeps rising where its house was cleared (hide it in the handler for a set with its own houses), and background village
chimneys bleed through; figures drawn "huffing" carry a breath cloud (tools/cast/erase_puffs.py: cream component from
a seed, inside-silhouette part inpainted, the rest cleared); sparkle bursts on growth / cooking read as steam from
afar. Ambient butterflies / leaves hide whenever they would show over 4 % of the frame height (wide shots only).
