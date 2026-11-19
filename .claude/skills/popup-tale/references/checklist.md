# Pre-delivery checklist (every user complaint from 「해와 바람」 and 「아기 돼지 삼형제」)

Run this on the LATEST full recording before sending anything to the user. Each item is something the user caught
by eye after we said "done". The quote is what they said; check it yourself first.

How to look:
- 12 evenly spaced frames per beat, plus a 2.5 s contact sheet of the whole run.
- 8 fps zoomed tiles of every walk, run, turn, climb and landing.
- Full-res crops of every window, door and tap moment.
- `tools/story/check_lines.py` on the autoplay log.

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
- [ ] **Placement.** Set pieces are off the road and out of the water (SET_CHECK road=0 water=0). Wading characters stand in the water channel, not in the bank.

## Lines and voice
- [ ] Every used line and segment plays exactly once, in order (check_lines.py). If a viewer says a line is missing, check the log before assuming.
- [ ] **A quote plays when its speaker is in place.** The narrator plays during the walk, and the quote within about 1.5 s of arriving, with the speaker on camera ("도착 전에 문 열라고 하네", "대사가 아예 사라진듯": a 9 s gap read as missing).
- [ ] **No doubled words in reused clips** ("그럼을 두 번 말하고"). Check the envelope and trim. Don't re-record without approval.
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
- [ ] **Doorways.** An open door shows an interior (the house has a body: side walls, back, floor, ceiling) ("뒷편이 없는곳으로").
  - One door cycle per group; everyone enters seen from behind.

## Camera and framing
- [ ] **Shots are varied** (wide, medium, close; OTS; low entrance; push-in on completion; light progressing). Not one frontal stage shot ("전체적으로 연출 고민해볼래? 카메라 워킹도").
- [ ] **Interactive steps frame every target first** and hold still. Rings sit fully inside with margin, and each target is at least ~80 pt to tap ("화면이 거기로 안가서 못누름").
  - A build is framed once, for the finished size.
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
