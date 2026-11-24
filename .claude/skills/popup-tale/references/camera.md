# Camera: shots, framing, sightlines, taps

Shot / cam step fields: script_schema.md ("Data-driven stage", step verbs `cam`, `cam_settle`, `frame`, `walk follow`).

## Direction (user-approved shot plan, 2026-11-19)
- A page is a film, not a stage play: mix wide / medium / close, change angle every line or two; never one frontal
  medium for every beat (user: "전체적으로 연출 고민해볼래? 카메라 워킹도"). Establish a new place with a wide (crane)
  before the first action there.
- Each repeated set piece gets its own rhythm (straw quick, wood with a camera bump per hammer, brick slow and warm);
  completions get a slow low-angle push-in; threats enter low and menacing, then over the shoulder toward the target;
  dialogue across a wall is shot / reverse shot (OTS on the speaker, window close-up on the answer; the window
  close-up must contain the peek face); effort = close + a small shake per tap, the result cut wide, and effort and
  result share the frame (a huff close-up includes the house: "후 불때는 클로즈업 집까지"); the strong outcome holds
  frontal and steady.
- Big moments are staged ("집밖으로 나오는것도 좀 더 극적으로"): a door bursting open with light, a low hero shot and a beat
  before the action.
- Dramatic irony before a surprise ("처음엔 나온지 몰라야지 나중에 놀라는거"): glimpses nobody reacts to (out of the pot
  steam behind the friends, over a shoulder, over the pot rim, mimicking at the back), then the big reaction (sting,
  snap zoom, surprised faces).
- Effects the lines name are shown ("유령 사탕먹은 입도 제대로"): a line about the mouth gets a face close-up.
- Escapes: side tracking plus a high wide so the route reads. Keep the 180° rule (threat screen-left, heroes right).
- The camera always drifts slightly (hand-held miniature); the light progresses with the story (day → afternoon →
  late → dusk → night → warm evening) and the ending pulls back and closes the book.
- Never expose the backdrop: clamp shots or use `backdrop`; close-ups must not show card edges (sightline stations).
  No black sky; no camera passing through cards: hide hinged AND static cards near the camera path
  (`_clear_sightlines`, `_clear_statics_here`).

## One place = one spread, camera moves
Same-place story moves use camera moves on one spread, not page turns (user: "책장 안넘기고 한번에 처리하는게
좋을거같음 카메라 무빙으로"). Template views of one seed are only camera stations in one world: put every lot of a
place on one spread (spots converted into one view's frame), list the camera stations in `spread.sightlines`
(incl. `["story", "road", a, b]` for tracking shots), glide `cam at`, track runners with `walk follow` +
`via: "road"`, and give later beats `built` (what stands at that beat, ruins included) so `--beat` starts and
prebuilds are right. Page turns only where the place really changes.
- A place the story calls far away but that shares the spread (rapunzel v3: "먼 들판의 작은 오두막" next to the tower):
  its house stays a lot (`stage: 0`) until the story reaches it and pops up there (fx `pop:<name>`), and its shots
  turn off the landmark it is far from (field / reunion yaw 62-68: the tower leaves the frame). v2 had the cottage's
  thatch in the corner of every tower wide and the tower right behind the reunion.

## Smooth camera (user: "모든 동화 마찬가진데 시점이 뚝뚝 끊기는거 별로에요")
The camera moves continuously; every move eases in and out, a new shot mid-move bends the path (velocity carried
over), yaw goes the short way, and a cut happens only under a page turn. The run log prints `CAM_JUMP` (a frame
turning > 3°) / `CAM_JERK` (a one-frame velocity change > 20°/s) with t, beat, shot, and the summary
`CAM_JUMP=<n> CAM_JERK=<n>`: require 0 / 0 (shakes and page turns are not counted). No `from` cuts in cam steps (a
spread's opening `from` is applied under the page turn); `"cut": true` only where a turn hides it. Look at 8 fps
full-frame tiles of any flagged moment.
- Inside / outside 180-degree camera turns on a page with long errands came out at CAM_JUMP 3.0–3.05° even with slow
  rates; show the outside moment from outside (the wolf's floury paw at the door from a low doorstep shot) instead of
  turning round inside.
- Mid-page sky / light changes must not read the rig's current yaw (it carries the shot's offset).
- Story lines that open a beat start after the camera has landed (`cam` wait ≥ 1.2 s after a page pop).

## The acting character and the speaker are in frame
- Review a beat with ~12 evenly spaced frames and require the acting characters in every one: the wolf beats first
  used the wide stage shot and the wolf stood at the frame edge the whole time. Frame the shot between the actor's
  mark and the set piece (`cam at`), not on the set piece alone. The camera follows walkers to their mark, and no one
  exits mid-line.
- SPEAKER_OFF (2026-11-22): every quote's speaker is inside the frame and not hidden behind a set piece (> 60 % of
  head and body) within 1.5 s of the segment starting, and stays so for most of it; the run log prints
  `SPEAKER_OFF <line:seg> who= t= beat= shot= why= at=` and `SPEAKER_OFF=<n>` in the summary. Fixes that worked:
  split a line's segs so the threat is said on the threatener (`say segs`), frame a two-shot between marks
  (`cam at: [spot, spot]`), `settle` on a cam step / `cam_settle` after an fx glide so the line waits for the camera,
  a build sub-step `wait_for` (speakers walk into the frame first), an interior shot instead of an outdoor one for
  someone inside. Deliberate inserts (the witch naming her jars over push-ins) go in the tale's `speaker_insert` list
  (logged as SPEAKER_INSERT); a speaker shown as something else (sunmoon's children as the sun and moon) is a handler
  `speaker_point`. Group speakers ("kid") need a stand-in: handler `speaker_point("kid")` returns the beat's
  `kid_voice` member (a centred one, set per beat), otherwise SPEAKER_UNKNOWN skips the check. Name the actor role
  after the voice script's speaker key (sound.md).
- A speaker hidden by a house (user: "앞의 집때문에 안보여"): turn the camera to face them (a shot with the house's yaw
  from the road) instead of moving people; then check what stands between camera and speaker in the new direction
  (a lamp, the next house) and move that, and keep queues short so the last in line does not fill the lens. No house
  blocks the view ("다른 집들로 인해 시야가 안가리면 좋겠어"): OCCLUDE zero; choose camera angles that clear the houses
  before moving houses.
- Tracking shots go above the roofs (a medium follow clipped through a house).
- Shots for a set built from card "gates" (ridges either side of a road) must stay inside the gaps.
- A template card (hill) in a close shot's lens on a new spread: a tiny set entry with a big `clear` opens a lawn;
  keep marks and close shots off ground-terrace edges (sets.md).
- The shot of a roof must keep the camera in front of the cast (a long lens from further away): a close low shot of a
  building behind the line glides the camera through the line (turnip barn).

## Interactive steps (taps)
- Interactive steps frame their targets first (user: "화면이 거기로 안가서 못누름"): before a prompt, the stage camera
  settles on a shot with every target on screen, rings fully inside with margin, and ≥ ~80 pt to tap, and holds until
  the taps are done (SpreadStage.frame_targets, runner `_frame_first`).
- Interactive moments get their own framing, not the establishing wide ("사탕 누를 때 카메라 화면이 너무 그냥 똑같이
  전경을 비추고 있어서 ... 선반으로 카메라를 옮기는 건 어때?"): the camera goes to the targets (big, rings inside), follows
  the result, comes back for the next tap; vary the angle between repeated rounds.
- A build is framed ONCE (user: "Frame each build once"): before its intro line, a `frame` step (or the build itself)
  sets a shot that already fits the FINISHED house (full height and width), the pile, the builder and the tap rings,
  and holds it for every tap; no reframes between taps, and story beats inside the build (the brothers' tease) play
  in that same shot. The ring around a house mid-build sizes to the walls standing now, not the finished height.

- Exits and escapes stay on screen (2026-11-24, sun_wind / three_pigs gate audit): a walk-off that leaves the frame
  under a held camera, then an empty road under the closing line, then a return for the curtain call read as a hole
  ("the empty road at the ending"). The traveller now strolls on with the camera under the closing lines (stroll +
  say + stop), and the curtain call has no walker return. A fleeing villain is followed at a readable size (a
  `chase` shot, el ~22° to see over the trees, ~3.8 away) for most of the line; `follow_for` then releases to a shot
  that turns back to the home (he leaves the frame by the camera turning, not by shrinking to a speck in a static
  wide, and the exit pop happens off frame). A follow from the `high` shot (6+ away) kept him a dark speck in the
  night forest.

- Carries and throws are tracked: `cam` with `follow: <carrier>` while the line plays, then a shot that holds both
  the thrower and the landing; the carrier steps aside after (patjuk: the carry to the sea used to happen off frame
  and a splash popped up in an empty sea shot).
- A pine / hill card filling the lens on a tracking shot at road level: track from above the template's trees
  (el ~30°) instead of moving the trees (patjuk night arrival).

## Interiors
- Every room shot keeps the camera within ~0.5 of its focus (behind the hidden front wall); outdoor shot distances put
  the camera outside. Disable the stage's automatic tap reframing while the camera is inside (it pulls the camera out
  through the wall) and frame taps with an explicit room shot.
- Rooms: stand the family DEEP in the room (behind ~0.55 of a 1.1 box) and shoot from just inside the front wall
  looking down (el ~32°, fov 64–72); anyone within ~0.3 of the lens becomes a giant head. Someone in the doorway stays
  behind the lens; show the doorway with the turned-round `door_in` shot instead. Inside shots aim at DEEP spots
  (z ≈ -0.85 of the house frame) so the camera stays behind the front wall; a shot aimed at a mid-room spot put the
  camera outside the house and the facade filled the frame (patjuk).
- A glide into a deep room passes the facade close enough to fill the frame with the door; tale `inside_margin`
  (spread_stage, default 0.16) folds the facade away earlier (patjuk 0.8; the inside-face card waits until the camera
  is behind the wall). three_pigs' brick house (0.78 deep box, `inside` shot 0.6 at fov 68): 0.5 cut the "door and
  shutters fill the frame for a second" on the way in and out to a medium of the facade, then the room.
- Shots inside / at a turned house carry its yaw as their yaw offset.
- Room shots from just in front of the wall (wolf_goats v2): tale `inside_margin` (0.55) folds the facade away while
  the camera is that close, and `inside_door_hide` also folds the door leaf, the roof band (eave + door arch top) and
  the body's door / window reveals (else they frame the room like a tunnel and a glide in fills the frame with the
  door). A room shot can then stand ~0.4 in front of the wall with a longer lens (dist 1.25, el 24, fov 52): the
  kids read bigger and the wolf in the room stays clear of the lens. Never turn 180 degrees inside (door_in): show the
  entry from outside, then glide in after the threat (CAM_JUMP 3.03 and a glide through the side wall otherwise).
- A character leaving a house is followed outside (wolf_goats v2: go_out `then.follow`; the v1 clock close-up held
  18 s while the wolf left off screen). The reassurance line plays over his waddle, not over a still.

- Leaving a room for somewhere behind the house (sunmoon v15 back-door escape, gate audit: "the escape is never
  seen"): leave through the wall the camera came in by (a glide straight from the room to a back-yard shot crossed the
  back wall and room cards: full-frame cream), rise outside (el ~40), then swing round the side at distance >= 2.5;
  show the escape from outside (the back door swings in, the children step out). Keep the characters in the room
  (`enter.keep`) until the camera is out, then move them behind the door unseen, folded flat (`pop_s` / `pop_target`
  0.02); a beat change that teleports them out of a room the camera still shows reads as a vanish.
- A turned-round inside shot (camera just behind the door / window, looking out) has anyone standing mid-room beside
  the lens: stand people deeper than the lens or a head sweeps through the frame in the pivot. The prop the line names
  is in that shot (the floury paw at the door's edge: a 0.34 close at window height showed only lattice; low and wide
  instead, 0.42 / fov 56).
- Shot yaw offsets are from the template VIEW, not the house: for a house turned by Y, Y looks at its front, Y+180
  from behind, Y-90 its left side, Y+90 its right (sunmoon cottage -40: -130 left, 50 right, 140 back). A long yaw
  swing at low elevation passes through the house (the thatch filled the lens for 2 s twice): add a high step in
  between (el >= 45) or shoot from the side the house is not on; a crane at el 52 from the front still had the roof
  over the lower half of the frame.
- Far depth-of-field blur on big flat backdrops renders as a square mosaic (sunmoon's far sky cloud rows): turn the
  rig's DOF off on a page whose interest is one plane (`rig.dof_enabled = false`).

- Kitchen-sized rooms with a big actor (patjuk wave 2, "the tiger is too close in the kitchen"): the camera cannot
  back off past the front wall, so widen the lens (fov 68–78) and aim at the actor's middle (focus ≈ half his
  height) from just inside the front wall; a 62° lens at 0.5 cut the 0.57 tiger's head off in every trap shot.
  Small actors entering along the floor get a looking-down room shot (el ~30°, focus 0.1): at el 14° they crossed
  the bottom edge under the caption (OFF_FRAME). Floor tap targets near the lens: raise the shot until the ring sits
  above the caption.
- Never turn round inside to face the front wall: the inside of a front wall is one flat card (its stand strip, the
  outer door's reveal lines and the ceiling edge show) and the next glide out passes through it. Show what happens
  at the door from OUTSIDE (glide out facing the back wall: clean), and stage door moments outside (patjuk's mortar
  now hides over the outside of the door and drops on the tiger as he bursts out).

## Judging framing
`gd_run.capture_scene` stills do not follow the story camera shots; judge framing / focus from movie-maker recordings
(`tools/story/rec_beat.sh TALE BEAT SEC out.mp4`) and 8 fps tiles (`tools/story/tiles.py`).
Follow smoothing and still zones: papercraft_notes.md ("Camera").

## Lessons from witch_candy wave 2 (2026-11-24)
- A queue on the path straight toward the lens hides the doorway (Dahyun's hat over the friends going in): shoot an
  entry / exit file from the side and above (`door_entry` 30°, yaw 30° off the door axis toward the side with no near
  house; +34° put house_7's roof in the lens) with `at: [door, end of path]` so the whole queue is in frame (OFF_FRAME).
- The "broken blue roof" in the audit was the lens inside the near house's roof (a 27° track over a lined street), not
  the house body (house_orbit red 0): tracking shots over a street go 45°+; a low sky shot needs its focus over the road
  (a lens beside a chimney filled half the frame).
- A file followed by its LAST walker leaves the leaders off the frame bottom (OFF_FRAME on 4 of 6): follow the middle
  one and pull back; seen high from the side (58-60°, yaw -60°) the file reads as a file, not a totem pole.
- Glide in through a shut door: tale `inside_margin` (0.75 here) + `inside_door_hide` fold the facade and leaf away
  before the lens reaches them; otherwise every room entry passes a frame-filling door.
