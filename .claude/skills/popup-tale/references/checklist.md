# Pre-delivery checklist (every user complaint from 「해와 바람」 and 「아기 돼지 삼형제」)

Run this on the LATEST full recording before sending anything to the user. Each item is something the user caught
by eye after we said "done". The quote is what they said; check it yourself first.

How to look:
- 12 evenly spaced frames per beat, plus a 2.5 s contact sheet of the whole run.
- 8 fps zoomed tiles of every walk, run, turn, climb and landing.
- Full-res crops of every window, door and tap moment.
- `tools/story/check_lines.py` on the autoplay log.

## Look: is it paper?
- [ ] **No felt anywhere** ("펠트 질감 싫은뎅", 2026-11-22): the ground, every set card and every character are matte cut
  paper (layered sheets, fine fibre grain, a dark cut line with a lighter lit-side rim); no wool fuzz, no fabric texture,
  no dashed stitch lines on hems, aprons, ridges or clouds. Tale `ground_style: "paper"`; art prompts use the PAPER
  style block (tools/art/sunmoon_jobs.py), never "felt" or "stitched". Check a 1:1 crop of ground, a set card and a face.

## Story logic: does it make sense?
- [ ] **No teaching.** No quizzes, counting, tallies or morals ("교육적인 요소보다는 동화의 전달"). Taps drive the story, about 3 per moment ("벽돌을 10번이나 누를 이유가 있냐").
- [ ] **Characters are where the story says.** People at home are inside the house, peeking from the windows, when the threat comes ("돼지들 집에 있어야하지 않겠니?").
- [ ] **A refuge stays closed.** The interior is shown only after the threat has entered, by moving the camera in, never by opening the wall ("앞 벽은 막혀있어야", "굴뚝으로 들어가면 그제서야 안을").
- [ ] **Nothing appears before its moment.**
  - Houses are empty lots until their build ("둘째 집 짓기도 전에 있음").
  - Materials and tools appear only in their beat ("돼지 세마리 갈때 짚이랑 벽돌을 왜 가지고 있지").
  - Later props (the ladder) are found or brought by whoever uses them.
- [ ] **Every action reaches its outcome on screen.**
  - Escapes are continuous on one spread with camera moves, not page turns ("책장 안넘기고 카메라 무빙으로").
  - The villain's defeat ends with him visibly running away ("늑대가 도망가서 달려야").
- [ ] **No stray effects.** No smoke or steam unless the story makes it ("셋째집 연기뭐지?"). Check background village chimneys, which bleed through.
- [ ] **Houses face the road** ("집 문이 길쪽으로 나있어야 미국식 집 구조"): every front door looks onto the street,
  houses on both sides face each other across it, none turns its back or side to the road; a short path or steps
  from each door to the road.
- [ ] **Story props move on screen** ("초대장이 날아왔으면 좋겠고"): what the narration says arrives (an invitation on the
  wind) visibly travels there, fluttering, with the camera following, then is caught / opened toward the camera.
- [ ] **Houses solid from every angle** ("집들은 무조건 입체적으로 아주 잘 들어맞게", 2026-11-23): every house, barn, shop,
  cottage (story set pieces AND the template village's houses) is a closed volume: side walls in its own material,
  roof following its drawn roof line with even eaves, chimney seated, back filled, door / window reveals; no slit
  between front and body, no background through corners, under eaves or along the ridge, no roof floating or sunk.
  Run `tools/story/house_orbit_all.sh OUT LABEL <tale>` and look at every sheet: red (background through a closed
  house) must be zero apart from real openings (pavilions, gateways, courtyards). Non-box buildings come from the kit
  (pavilion, round tower, hanok L, pagoda, castle), never a flat card.
- [ ] **Angled houses need bodies** ("사선으로 돼 있으니까 집도 집처럼 보여줘야"): a house turned to the road shows side walls,
  a roof running back and a back from every camera position (no flat cut-outs, no hollow backs).
- [ ] **No half-popped scenery at a spread's start** ("어떤 건 서 있고 어떤 건 안 서 있고"): unless a tale wants the wave,
  everything stands when the street first shows (tale `pop_in: false`); a house's walls / roof never stand without
  its front or the reverse. Check the first 10 s at 4 fps.
- [ ] **Interactive moments get their own framing, not the establishing wide** ("사탕 누를 때 카메라 화면이 너무 그냥
  똑같이 전경을 비추고 있어서 ... 선반으로 카메라를 옮기는 건 어때?"): before a tap prompt the camera goes to the targets
  (big, rings inside), follows the result, comes back for the next tap; vary the angle between repeated rounds.
- [ ] **Placement.** Set pieces are off the road and out of the water (SET_CHECK road=0 water=0). Wading characters stand in the water channel, not in the bank.

## Lines and voice
- [ ] **Branching tales:** every result branch has been played at least once (autoplay with each forced result), and
  check_lines accepts exactly one result's lines per round.
- [ ] Every used line and segment plays exactly once, in order (check_lines.py). If a viewer says a line is missing, check the log before assuming.
- [ ] **A quote plays when its speaker is in place.** The narrator plays during the walk, and the quote within about 1.5 s of arriving, with the speaker on camera ("도착 전에 문 열라고 하네", "대사가 아예 사라진듯": a 9 s gap read as missing).
- [ ] **No doubled words in reused clips** ("그럼을 두 번 말하고"). Check the envelope and trim. Don't re-record without approval.
- [ ] **One caption, one voice** ("말풍선에는 하나만 써있는데 두번 말하는 경우가 있어"): a clip must not contain its sentence
  twice (generated takes sometimes repeat; check duration vs text and transcribe), and a line must never start a second
  voice play or overlap another voice under the same caption (run log VOICE_DUP=0). Lines that recur across rounds
  are fine.
- [ ] Expressions match the words; never a grin over "앗!" or "추워!".

## Motion
- [ ] **No rigged cut-out or hopping card for any travel.**
  - Every walk and run is a drawn cycle: side 4, back 2, front 2 ("이전 걸음 이상해요", "옆으로 달려가는 모습 이상해유", "늑대도 이상한디요").
  - Frames advance by distance; no skating.
- [ ] **The card faces the travel direction**, with no moonwalk ("뒤로 걷는데?").
  - Turns narrow to 15 %, never edge-on.
  - Villains lean INTO a sneak and sniff while standing.
- [ ] **Feet are always on a surface.**
  - Climbs use a ladder or other support ("늑대 굴뚝 올라갈때 이상").
  - Landings have a thud and dust.
- [ ] **Walk details** (sun_wind rig, if used): front boots, so no splay feet ("팔자걸음"). Legs stay behind the garment, roll is about 0.6° so no "휘청", arms swing so no "soldier march".
- [ ] **Entries climb the steps** ("문에 겹친다던지 문 아래 돌지방을 통과"): the door swings fully clear first (into the
  house), each character walks up the steps onto the sill (feet follow the step height), through the open doorway and
  down inside, one at a time or in a tidy file; nobody overlaps the door card or passes through the threshold stone.
  Check every entry and exit with 8 fps zoomed tiles.
- [ ] **Doorways.** An open door shows an interior (the house has a body: side walls, back, floor, ceiling) ("뒷편이 없는곳으로").
  - One door cycle per group; everyone enters seen from behind.

## Camera and framing
- [ ] **Shots are varied** (wide, medium, close; OTS; low entrance; push-in on completion; light progressing). Not one frontal stage shot ("전체적으로 연출 고민해볼래? 카메라 워킹도").
- [ ] **No jerky viewpoint jumps** ("모든 동화 마찬가진데 시점이 뚝뚝 끊기는거 별로에요. 사탕마녀도 그렇고 썬문도 그러네"):
  the camera moves continuously; every move eases in and out, a new shot mid-move bends the path (velocity carried
  over), yaw goes the short way, and a cut happens only under a page turn. The run log's camera check prints
  `CAM_JUMP` (a frame turning > 3°) / `CAM_JERK` (a one-frame velocity change > 20°/s) with t, beat, shot, and the
  summary `CAM_JUMP=<n> CAM_JERK=<n>` next to VOICE_DUP: require 0 / 0 (shakes and page turns are not counted).
  No `from` cuts in cam steps (a spread's opening `from` is applied under the page turn); `"cut": true` only where a
  turn hides it. Look at 8 fps full-frame tiles of any flagged moment.
- [ ] **The speaker is in the frame** (SPEAKER_OFF check, 2026-11-22): every quote's speaker is inside the frame and
  not hidden behind a set piece (> 60 % of head and body) within 1.5 s of the segment starting, and stays so for most
  of it; the run log prints `SPEAKER_OFF <line:seg> who= t= beat= shot= why= at=` and `SPEAKER_OFF=<n>` in the summary.
  Fixes that worked: split a line's segs so the threat is said on the threatener (`say segs`), frame a two-shot
  between marks (`cam at: [spot, spot]`), `settle` on a cam step / `cam_settle` after an fx glide so the line waits for
  the camera, a build sub-step `wait_for` (speakers walk into the frame first), an interior shot instead of an outdoor
  one for someone inside. Deliberate inserts (the witch naming her jars over push-ins) go in the tale's
  `speaker_insert` list (logged as SPEAKER_INSERT); a speaker shown as something else (sunmoon's children as the sun
  and moon) is a handler `speaker_point`.
- [ ] **Interactive steps frame every target first** and hold still. Rings sit fully inside with margin, and each target is at least ~80 pt to tap ("화면이 거기로 안가서 못누름").
  - A build is framed once, for the finished size.
- [ ] **Nothing overlaps** ("물체랑 사람들끼리 자꾸 겹치잖아"): actors vs actors, actors vs props, props vs props; the run
  log's OVERLAP lines (stage `overlap_check`) are zero or whitelisted contacts (`overlap_ok`); marks spaced, spacing
  solver on; zoomed tiles of the room and the finale.
- [ ] **No house blocks the view** ("다른 집들로 인해 시야가 안가리면 좋겠어"): the OCCLUDE log lines are zero; choose camera
  angles that clear the houses before moving houses.
- [ ] **Dramatic irony before a surprise** ("유령이 처음엔 나온지 몰라야지 나중에 놀라는거"): a sneaking character shows in
  glimpses nobody reacts to; the reaction comes later, big (sting, snap zoom, surprised faces).
- [ ] **Effects the lines name are shown** ("유령 사탕먹은 입도 제대로"): a line about the mouth gets a face close-up with
  the black lips and wisps on each "우~".
- [ ] **No overlay on top of a drawn feature; states persist** ("검은 입술이 기존 입술위에 덮여서 이상한데? 그리고 계속 검은
  입술로 있는지 검토해봐"): a changed feature replaces the drawn one (the mouth itself drawn dark, nothing of the old
  mouth showing, no halo; full-res crops), and a state like the ghost-candy mouth is a CastPuppet state that every
  expression / walk change respects until the story ends it (run log BLACK_LIPS frames-with-wrong-variant=0).
- [ ] **Replace a feature by removing the original first, never paint over it** ("기존 입술 위에 덧칠하니깐 이상한데"): erase
  the old feature (inpaint with the surrounding material), then draw / composite the new one; check three-row crops
  (original / erased / new).
- [ ] **Big moments are staged** ("집밖으로 나오는것도 좀 더 극적으로"): a door bursting open with light, a low hero shot and
  a beat before the action.
- [ ] **No set piece in front of a speaker** ("앞의 집때문에 안보여"): check every exterior shot for a house, tree or
  prop between the camera and whoever speaks; turn (orbit) the camera to face them rather than leaving them hidden.
- [ ] **The acting character is in every frame of its beat.** The camera follows walkers to their mark, and no one exits mid-line.
- [ ] **Effort and result share the frame.** A huff close-up includes the house ("후 불때는 클로즈업 집까지").
- [ ] **Reverse shots show the answerer.** The window close-up must contain the peek face.
- [ ] **No exposed backdrop or black sky**, no card edges in close-ups, and no camera passing through cards.
- [ ] **Window faces are readable:** peek art, one per window, the same scale, a dark interior behind them ("창문에 돼지들이 이상해").

## Sound
- [ ] **Sound is wired in-engine and recorded from the latest build.** A preview laid over an older capture misses the newest fixes ("앞에 게 반영 안 된 것 같은데").
- [ ] **A living world:** birds, a stream (positional), leaves and grass in the breeze, accents (cuckoo, bee, frogs, owl), and beds that follow the light ("새소리 물소리 풀잎소리").
- [ ] **Every on-screen action has a cue,** including footsteps per contact frame by surface, and music per mood.
- [ ] **Mix:** voice on top, music and ambience ducked under lines, no clipping. Tell the user nobody has listened yet.

## Delivery
- [ ] **Runtime against the target.** Count narration, page turns and taps before promising a length, and report the change after each round.
- [ ] **Both tales** still play to STORY_DONE with `missing_audio=[]` and `missing_sound=[]`.
- [ ] **mp4 under 30 MB.** Say honestly what you haven't checked.
