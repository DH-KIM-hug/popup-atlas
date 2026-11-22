# Book cover — paper spec (2026-11-22, user: "책 표지 디자인 제대로 하자")

The cover is a real picture book, not a UI card: a 3D hardcover lying on a wooden table under the tales' lens and
light (game/story/cover_book.gd, CoverBook), one key-art picture and one cut-paper title per tale, opened by a tap.
Test card: 「사탕 마녀의 핼러윈」 (witch_candy). Rollout to sun_wind, three_pigs, sunmoon after the user's OK.

- SUBJECT: the closed book and its cover picture: the tale's main characters together in its signature place, the
  title above them. Per tale:
  - 사탕 마녀의 핼러윈: the candy witch with a swirl lollipop, 다현이 with a pumpkin bucket, 호박이 sitting, in front of
    the glowing candy shop on Halloween night.
  - 아기 돼지 삼형제: the three pigs before the straw / wood / brick houses, the wolf peeking from behind a tree.
  - 해와 바람: the sun and the wind in the sky over the traveller in his coat on the road.
  - 해님 달님: 오누이 climbing the rope to the sky between sun and moon, the tiger below (current figure designs, paper).
- PALETTE (witch_candy): indigo night #2b2a5c (sky), blue-violet #4b3a7a (cloth, endpaper), pumpkin #e8862a and candy
  gold #f2c14e (title, lamplight), cream #f3e8d0 (pages, title backing), walnut #7a5234 / #553522 (table). Every tale
  sets cloth / endpaper / page colours in `ui.cover`.
- LIGHT: warm low key from upper left (#ffd2a0, 38°, yaw -48°) raking across the board so the raised title casts a
  small shadow; cool fill; warm ambient so the darkest 20 % stay brown, never grey. `light: "night"` adds a warm lamp
  pool on the table (Halloween, the sunmoon night).
- LENS: fov 22°, 57° above the table, 8° to the right so the fore-edge and the tail edge show the page block; DOF and
  tilt-shift keep the board sharp and soften the table; grain 0.03.
- GROUND: a warm wooden table (planks + grain, procedural), a soft contact pad and the key's shadow under the book.
- LAYOUT: the book fills ~60 % of the width, its bottom edge above the caption strip (the voiced prompt's caption never
  covers it); the title sits in the art's quiet top 40 % (`title_rect`); "팝업 동화" small and quiet at the foot.
- BOOK: back board, rounded cloth spine, cream page block with page lines on head / tail / fore-edge, front board
  with cloth corners and a cloth strip at the spine, the key art printed on it, the cut-paper title as a raised layer,
  a printed endpaper inside (tale colour + small motif), a cream title page with the title.
- MOTION: idle — every 3.2 s the fore-edge lifts ~7° and drops (a thumb at the corner: "open me"). Tap — the board
  swings over the spine (1.25 s, slow lift, quicker sweep, soft fall, a 4° slap off the table) while the camera rises
  to look straight down and pushes in until the title page fills the frame (2.35 s); then the existing page turn
  turns the title page onto the first spread, which pops up. Rigid boards never bend or sway. End — the last spread
  folds, the page turns onto the title page, the camera pulls back and the board swings shut; "끝" and "다시 보기" on a
  paper tag at the right. Replay glides back to the cover framing.
- SOUND: the tale's `cover.on_open` cue on the tap (paper page turn), the page-turn cue on the title page turn, the
  `end.close_book` cue when the board lands shut. The voiced prompt "그림책을 톡 눌러서 펼쳐 볼까요?" stays; the
  printed "톡 눌러서 책을 펼쳐요" is gone (voice + the lifting corner carry it).
- BANNED: felt, wool, fuzz, stitches or dashed seams anywhere in the art ("펠트 질감 싫은뎅"); an outlined UI font as the
  title; one look for every tale; text generated inside the key art; the caption over the book; a flat UI panel.
- QA: still of the closed book at 1.5 s (whole book above the caption, title legible, no clipped edge); 1:1 crop of the
  art (paper, not felt); frames at the board's mid-swing, landing and title page; the page turn into the first
  spread; the end close; full autoplay of every finished tale to STORY_DONE with missing_audio=[] missing_sound=[].

## Art pipeline
tools/art/cover_jobs.py (Codex jobs: key art with single-character refs + a paper material ref, then a "paper pass"
that redraws the chosen picture as smooth cardstock — felt-made character refs leak their nap otherwise; the title
lettering on magenta) → tools/art/cover_build.py <tale> <art.png> [<title.png>] → game/stories/<tale>/art/cover_art.webp,
cover_title.webp. Config in tools/story/tales/<tale>.py `UI["cover"]` (copied into script.json `ui.cover`).

## Alternative (look test, `--cover-pose=stand`)
The same book standing on a little wooden easel, seen low (12°) like a shelf display, with the tale's own picture far
behind it out of focus; opening pushes the camera straight onto the upright title page.
