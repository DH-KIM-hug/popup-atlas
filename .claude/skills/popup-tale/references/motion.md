# Motion: walks, runs, cycles, facing, rig, peeks, climbs, flights

The gate (`tools/story/motion_review.py`, see SKILL.md) cuts an 8 fps tile sheet per travel segment; you look at every
one. Critics on stills miss gait bugs.

## Every travel is a drawn cycle (user rule, latest 2026-11-23)
- Every walk is a drawn cycle (user: "늑대도 이상한디요?", "이전 걸음 이상해요"): per character side walk (4) + back (2)
  + front (2) frames, run cycles, and special walks (carrying: `<walk_pose>_cycle`); `tools/cast/add_cycles.py` slices
  a sheet into catalogued frames. StoryActor picks the cycle for the travel view; the leg-swapping rig is not used
  since three_pigs.
- Runs need a drawn run cycle; rigid-card hops read as stickers (user: "돼지 옆으로 달려가는 모습 이상해유"). Generate
  per character 4 side frames (contact, down, passing, flight; legs apart, arms pumping, the line's face) + 2 back
  frames, pad each character's frames to one canvas (bottom-aligned), catalogue them with `cycle` / `frame`;
  CastPuppet plays them advanced by ground distance (one cycle per ~0.9 height, no skating), bounce on flight.
- A character with no drawn run cycle must walk with no `pose` ("run" falls back to its standing side card = a hopping
  card); give it speed instead (turnip's animals). A hopping static card on any travel is a defect (MOTION_FLAG).
- (superseded for travel, 2026-11-18 → 2026-11-23) Unrigged figures (legs drawn together) work as one card with a
  paper hop (CastPuppet hop_frac / hop_len_frac: one hop per hop_len_frac·height of travel, hop_frac·height high,
  rocking ±4°): cheaper than regenerating; use them now only for tiptoe, hungry and other standing poses, not runs.
- Villains lean INTO a sneak (never back), and do a sniff pose standing, not walking.

## Facing and view picking
Walkers can go toward the camera, away from it, or sideways (user, 2026-11-18: "앞뒤 왼쪽 오른쪽도 되긴 해"). A card must
face the way it travels, or it reads as moonwalking ("뒤로 걷는데?"; sun_wind's first walk: a front-facing card moving away):
- **front** figure when moving toward the camera,
- **back** figure (back of head/clothes, heels toward us) when moving away — same rig, mirrored logic: legs in front
  of nothing, feet show heels,
- **side profile** figure when moving across the frame (flip the card for the other side; side walkers read best and
  are the cheapest).
Plan which directions each walker needs and generate those views; front-only walkers are limited to walking toward the
camera. Expressions are needed per view the beat uses (side faces show emotion well too).

StoryActor / CastPuppet (2026-11-18 three_pigs):
- StoryActor moves itself; every frame the camera-relative travel angle picks the view (|a| < 45° front, > 135° back,
  else side; 15° hysteresis each way, a ~30° band; a quick paper turn over ~0.15 s when it changes), the figure for it (`walk_pose` if its catalog `view` matches, else
  calm / back_walk / side_walk), and `facing_left` for side figures. CastPuppet.set_figure(pose, mirror) does the
  paper turn (edge-on squash, swap, unsquash) for pose and mirror together. Paper turns narrow to 15 %, never edge-on.
- Mirroring is a negative x scale on the tilt node (never on the turn node: global_rotation on a negatively scaled
  node decomposes badly); the side gait writes the legs through the same mirrored frame.
- A pose call every frame must not restart a running paper flip (CastPuppet.set_figure compares with `_flip_to`):
  otherwise expressions lag a whole line behind the words.
- Pose switches can flip hats/props on and off (hat flicker): check pose → figure mapping keeps worn props consistent.
- Standing figures breathe (body card only, about the hips, so the planted legs don't slide).

- A beat's `enter` figure is shown for the beat's first frames: give it the figure the first line wants (turnip
  grandpa, 2026-11-24: enter `side_walk` between a surprised front and the next line's clap front showed a side card
  for 0.2 s, read as a thin turn at 0:47). Front → side → front within half a second reads as a glitch, not a turn.

## Expressions
One smiling figure is not a character. Give every narrated emotion its own figure: calm walking face, surprised,
cold/shivering, hot/sweating, relieved, sad/angry as the tale needs. Map line → expression in script.json (line `expr`);
no beat may show a grin over "앗!" or "추워!".
Characters keep doing things during weather/interaction beats (the traveller kept walking through wind and sun) — a
story in motion, not a stage play of standing cards.

## Legacy leg-swapping rig (sun_wind traveller; not used since three_pigs)
Cutting tools: art.md ("Front-facing walker rig"). Classic brad-jointed paper puppet in profile: leg swing ±20–25°,
knee-bend cards, arms swing opposite.

Front-facing walk (CastPuppet, game/art/cast/rig/cast_puppet.gd, `front_gait = true`) — what finally read as "a child
walking toward me" (sun_wind v7, user: "이 정도는 괜찮다"):
- Direction: walks toward the camera along a road; story camera ahead, looking back, dollying; card yaw toward the
  travel direction kept to 20 % (`front_turn_keep 0.2`), foot sideways offset on screen ≤ 35 % (`front_side_keep`).
- Legs: front-view boots/feet (toes at the viewer; side-view feet → 팔자걸음); per-figure leg depth behind the
  coat/trouser top so a tilted leg never crosses in front of it; tilt capped (~20° forward, 24° back); footprints set
  back by the same depth; step width scales with roll (narrow, inside the coat width); lift 15 % of leg length;
  pre-drawn half-bent / lifted leg cards swapped by needed length; never shorten/slide a leg so its top shows.
- Body: weight-shift roll 0.6° (4° read as 휘청; wind: 0.6 + 0.6·struggle), front_bob 0.003, front_bounce 0.04, head
  lag clamp 0.006 rad, counter-twist 0.5°, push lean 2.5° in wind. Keep the body steady: small bob/bounce, tiny head lag. Narrow the step width when you reduce roll, or feet
  leave the coat.
- Arms: separate cards with round shoulder caps swing opposite the legs (stops the "soldier march"), arm_roll 5°,
  shadows off on arms; posed-arm expressions keep baked arms.
- Joins: seam edges coloured from the garment (cream card cores showed as white lines at the crotch/shoulders).
- Shiver: ~12 Hz, ~3.4° body rock + shoulder bob, feet planted, decays over ~3 s when the cause stops.

Side gait (`_side_step`): stance leg angle = asin(stride·(½ − s) / L) so the foot stays planted while the body moves
stride per step; swing leg comes through ahead with a 12 % lift; hips ride the stance leg (L·cos θ − L); lean 3° at
speed; stride capped at 2·L·sin(24°).

Verification recipe for every motion change: record the beat, then
`ffmpeg -ss T -t 2 -i out.mp4 -vf "fps=8,crop=…,tile=8x2" -frames:v 1 tile.jpg` on (a) the whole figure and (b) the
hem/legs. Check: feet toward viewer, no leg tops/seams visible, legs inside the garment silhouette, planted foot
fixed, torso near-vertical, expression matches the line. Fix → re-record → show the user.

## Peeks: people at home
People at home show as PEEK figures at the windows (head + hands on the sill, cast `peek_*`): one per window, the
head about 65 % of the opening, same scale in every house, a darker interior plane behind, a slight warm fill; a
whole figure scaled into a window looked wrong (user: "바깥보여줄때 창문에 돼지들이 이상해"). When nobody is at a
window (they're at the hearth) show firelight behind the glass instead. Faces behind die-cut windows sit in the
wall's shadow: light them with a small shadowless fill between face and wall (too strong blows the window out; 0.45
at range 0.22 read well).
People at a high window are actors lifted to the sill showing an upper-body `win_*` figure (rapunzel); SPEAKER_OFF
measures an actor from the ground, so the handler's `speaker_point` returns the window for them.

## Climbs, roofs, flights, hops
- Feet are always on a surface: climbs use a ladder or other support (user: "늑대 굴뚝 올라갈때 이상"); landings have a
  thud and dust.
- A rope / braid climb: climbers stand in front of it and go up with a drawn two-frame back-view `climb_cycle`
  (story_actor picks it for vertical travel and advances it by height climbed: the puppet only measures ground speed).
  The rope itself: sets.md.
- Climb selection (wave 1, 2026-11-24, generalised from rapunzel's braid): a `follow(points, spd, wpose, true)` leg
  that rises or drops ≥ ¼ of the figure's height at more than 30° from level is a climb (ladder, tree, rope, braid);
  so is any off-ground leg whose walk pose is `climb` or names a `<x>_climb` cycle (runner `climb` step: `"pose":
  "climb"`). StoryActor shows `<walk_pose>_climb` if the skin has it (tiger `axe_climb`, `rope_climb`), else
  `climb_cycle`; a fast drop (> 0.9 /s) or a `fall` / `tumble` pose keeps the drawn falling figure. Handlers that
  `set_pose("climb_a")` then `follow(...)` get the cycle automatically; pass the walk pose to pick a variant
  (sunmoon tiger: `follow(pts, 0.12, "axe", true)` → axe_climb). Without any climb cycle a straight-up leg falls back
  to the back walk with a rung bob (old ladder behaviour).
- Shared climb / run cycles made in wave 1 (tools/art/wave1_jobs.py → tools/cast/wave1_cast.py): wolf `run_back`,
  `climb_cycle` (ladder); tiger `run_back`, `climb_cycle` (trunk, from behind), `dg_back` (the drawn walk-away in
  mother's clothes, replaces the static card while walking; `dg_front` is still a static card), aliases
  `rope_climb` (rope_a/b) and `axe_climb` (axe_a/b); goat_kid_1..6 `run_front`; hanbok_boy / hanbok_girl
  `climb_cycle` (alias of climb_a/b: hands up, from behind; their rope_a/b are a praying and a sitting figure, not
  climb frames); mother_pig, rich_lady, peasant_mother `walk_cycle` / `walk_back` / `walk_front`.
- Objects travel by their own paper motion, never a rigid slide (wave 1, patjuk's helpers): catalog field `gait` on
  the skin (CastPuppet._gait_step, phase by ground distance, a contact sound per landing): `hop` (chestnut, dung,
  awl: arcs with squash / stretch), `crawl` (turtle: low quick shuffle, faces its travel way), `roll` (straw mat:
  turns over about its middle, lowest corner on the ground), `thump` (stone mortar: rocks from bottom corner to
  corner with a dip), `stride` (A-frame jige: lighter rock on its legs). MOVE logs the figure as `<fig>:gait-<kind>`
  and motion_review does not count it as a static card. Look at the tiles: a gait reads only at a readable size.
- A pop-out jump (kids out of the wolf's belly, wolf_goats v2) is a handler leap: a parabola in the move's own state
  holding the drawn "pop" figure, a bounce and a soft thud on landing (fx.gd `_leap`). `follow(...)` through a mid-air
  point walked the walk cycle along two straight legs in the air at constant speed ("kids float out of the belly").
- A character on a roof: `lift` (not a raised position) keeps the overlap check off the building's base line; the hop
  down is a handler arc on lift (turnip's cat).
- Handler-driven moves that keep a fixed figure (roll, float, hop): keep the path height in the move's own state;
  reading the actor's lift (which includes the hop) back as height made Dahyun climb into the sky.
- A step that starts while a scripted flight (wolf_launch) still moves the actor is cancelled by the flight's
  landing (`place_at`): wait the flight out before the next walk.
- A prop the narration brings travels on screen (flying invitations): sets.md "Props".

- Rest poses on a climb are climb figures (`climb_a` / `climb_b`, back view): hanbok kids' `rope_a` / `rope_b` are a
  praying and a sitting FRONT figure and showed between every pull (sunmoon v14); a handler that `set_pose()`s every
  frame during a climb hides nothing while moving (the climb cycle wins) but shows its pose at every rest. Two climbers
  on one rope a body length apart (0.55 for 0.32-tall kids) and 0.06 in front of the rope card; the overlap check
  ignores two actors more than 0.6 h apart in height (2026-11-24). A climb shot frames the whole trunk, roots to the
  sitter's head in the fork (tree_climb: distance 3.4, el 5, focus 0.9, fov 38): a trunk close at focus 0.6 lost the
  kids at the top and a fork close lost the tiger climbing below them. A tiger that slips on an oiled trunk walks to the
  trunk first (the slips played in the air by the well).

- A throw is a glide on an arc from the carrier to the landing point, the splash grows UP from the water line where
  it lands (~a third of the actor's height) and sinks back; never a card scaled up out of nothing in mid-shot.
- A carried roll sits ACROSS the top of the carrier (lift ≈ 0.6 of the carrier's height, a hair behind it, a small
  bob with the stride); at hip height it read as two cards pasted side by side.

## Routes and groups
- Outdoor actions route via the road (houses in front of the shop hid her walking straight to the camera); tracking
  shots go above the roofs (camera.md).
- Runners stop in front of the door (not beside the house). Entries / exits up the steps: sets.md "Doors and entries".
- Group movement causes most overlaps: walk by distance (formation kept), snake-follow files, two-lane loops, `via`
  waypoints round furniture (sets.md "Overlaps").

## Pulling line (turnip)
Side `pull` figures mirrored toward the target, marks a hand's width apart, the contacts listed in `overlap_ok` and the
roles added to `stage.no_spacing` by the handler; each heave is a spring on the actor's pop node (`a._root.quaternion`
about the view axis, pivot at the feet), so the whole line leans back and settles. Put the pulled object a step BEHIND
the line (z) and the first puller clear of its widest part, or it hides him.

- Special drawn runs (`run_bump`, `run_cry`: a side `<pose>_cycle` only) count as runs for the view pick
  (StoryActor, wave 2): away from / toward the camera they take the shared `run_back` / `<pose>_front` / `run_front`
  instead of the walk (MOTION_FLAG RUN_WALK_CYCLE), at run speed (≥ 0.4 or 3 heights / s).

## Water
Wading characters stand in the actual water channel, sink to the water line, hide legs below it, ripples on the water —
never sink into the bank.

## Runs (turnip v5, 2026-11-23, user: "애들 달리는거 점검좀...")
- Measure travel speed only from real movement. A placement or a pop-out jump counted as movement made drawn cycles spin 2–3× too fast; MOTION_FLAGS catches it.
- Plan each helper's last stretch as a sideways run in the direction they face when they stop. They arrive with no flips and never pass behind the set piece or the line.
- A hole or entrance sits at the depth of its destination, so the exit is sideways. A hole in front of the goal makes the character walk away from the camera.
- Small animals need their own run cycles (side 4, back 2, front 2). The run threshold scales with figure height, and a missing run falls back to that view's walk cycle, never to a static card.
- Changing figure within the same side view and facing is instant. Paper turns narrow to 30% of the card width; 15% read as edge-on. Front and back cards never lean sideways.
- Template lawn cards such as flowers can hide a runner without OCCLUDE catching it. Look at the motion tiles and bend the route.
- Start a runner in view or bring them in from off-frame; never pop them in at a spot.
- Godot screen coordinates are in the 1366x1024 base viewport. Scale them to the video before cropping.
- A tale float / bob that writes `lift` every frame (witch_candy `_floating` from the ghost candy) runs until switched
  off: MOVE counts the bob as travel on the standing card, so every later walk start read STATIC_CARD and verb "fly".
  Switch such effects off (lift 0) before anyone walks.
- Small walkers (the 0.17-tall cat) on a fast stepped path (door sill) flag SPEED_JUMP at the corners: give them a
  slower speed than the file.
