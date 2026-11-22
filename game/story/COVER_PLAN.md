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

## Title page
Cream paper; the tale's cut-paper title (upper third), a paper-cut spot vignette from the tale under it (witch_candy:
the jack-o'-lantern candy bucket and the witch's hat; sun_wind: the hat and coat on a rock with a sun and a wind
swirl; three_pigs: the three little houses; sunmoon: the straw rope under a crescent moon and a sun, a sorghum stalk),
"팝업 동화" small at the foot — all inside the middle ~64 % of the page that the open-book shot shows.

## Data
Each tale's book lives in game/stories/<tale>/cover.json ({cover: {art, back, title, spot, end_title, title_rect,
end_rect, light, cloth, cloth_dark, endpaper, endpaper_motif, page, mark}, curtain: {shot?, who}}), merged into
`ui` by StoryRunner and read by the bookshelf; the cover work never edits a tale's script.json.

## Art pipeline
tools/art/cover_jobs.py (Codex jobs: key art with single-character refs + a paper material ref, then a "paper pass"
that redraws the chosen picture as smooth cardstock — felt-made character refs leak their nap otherwise; the title
lettering on magenta) → tools/art/cover_build.py <tale> <art.png> [<title.png>] → game/stories/<tale>/art/cover_art.webp,
cover_title.webp. Config in tools/story/tales/<tale>.py `UI["cover"]` (copied into script.json `ui.cover`).

## Decisions
- 2026-11-22: the user chose the book lying on the table (the standing-on-an-easel alternative was dropped).
- Coordinator notes: frame the closed book bigger (55–65 % of the frame height, table + shadow still visible, caption
  clear); a paper-cut spot vignette under the title on the title page; the closing-book ending for all four tales.

# ENDING — paper spec (user: "그리고 끝났을때도 제대로 기획해줘")

- SUBJECT: the tale's last tableau, then its cast taking a bow, then the book itself: closed, turned over onto a back
  cover that shows what happened after.
- PALETTE: the tale's own (spread light, then the cover's cloth / endpaper / page colours); "끝" in brick red on cream.
- LIGHT: the last spread keeps its light (warm evening / night); the table under the warm raking key; the back cover lit
  like the front.
- LENS: the stage's wide for the curtain call (tale shots), the stage rig's fold-wide, then the table lens of the cover
  (60°, fov 22) with the book shifted left of centre for the tabs.
- LAYOUT: back cover = epilogue picture, calm top quarter with a cut-paper "끝" (raised layer); two paper tabs on the
  table at the right ("다시 보기", "다른 동화"), ≥ 300×96 pt each; the narrator's caption below the book.
- MOTION: hold 1.5 s → each cast member gestures in turn (pose + paper hop, 0.5 s apart; hangers swing) → the pop-up
  folds down in a wave (stage.fold: PopWave outside-in) → page turn back onto the title page → camera pulls back as
  the board swings shut (soft slap) → the book lifts and turns over (1.3 s, a lift arc) and lands back-up → tabs fade in.
- SOUND: ending music at the hold (catalog `music.ending`, plays once); page_turn cue on the turn back and on the
  turn-over; book_close thump when the board shuts and when the book lands; the outdoor bed fades out at the table and
  a quiet room tone (amb.room_fire, -16 dB) plays; stopped on replay / shelf. Nobody has listened to the mix yet.
- BANNED: a moral, a quiz, a count; text printed into the art; a flat UI end card over the scene; the "끝" tag covering
  the book; waiting on a choice in --autoplay.
- QA: frames of the hold, the curtain call (every listed member in frame), the fold, the title page, the close, the
  turn-over, the back cover with tabs; full autoplay of all four tales to STORY_DONE with missing_audio=[]
  missing_sound=[].

| # | Beat | Time (autoplay) | What happens | Tap |
|---|------|-----------------|--------------|-----|
| 1 | Hold | 1.5 s | the last line ends; the tableau stays; ending music starts | — |
| 2 | Curtain call | 0.9 + 0.5·n + 1.3 s (≤ 6 s) | camera to `ui.curtain.shot` (or stays); each `who` entry gestures in turn | a cast member: repeats its gesture (hold 3.5 s when interactive) |
| 3 | Fold | ~2.5 s | the pop-up folds down in a wave, camera rises to the wide | — |
| 4 | Back to the title page | 1.1 s | page turn from the folded spread onto the book's title page (title + spot vignette) | — |
| 5 | Close | 2.25 s | camera pulls back, the front board swings shut, soft slap + thump | — |
| 6 | Back cover | 1.9 s | the book lifts and turns over onto the epilogue picture with "끝" | — |
| 7 | Choices | — | tabs "다시 보기" / "다른 동화" beside the book; narrator "또 보고 싶으면 '다시 보기'를 톡!" | 다시 보기: replay from the cover (the book turns face up, glides back); 다른 동화: the bookshelf table |

Per tale (`ui.curtain.who`, back cover subject):
- 해와 바람: sun "beaming", wind "boast" swing in the sky; back cover — the traveller resting coatless in the sunshine
  under a tree, sun and wind content above.
- 아기 돼지 삼형제: pig_a / pig_b happy_wave, pig_c cheer, mom wave; back cover — the three pigs by the fire in the
  brick house, the wolf running off far away with a singed tail.
- 사탕 마녀의 핼러윈: 다현이 wave, the witch two_candies, 호박이 meow, rabbit / bear / fox cheer; back cover — the shop
  at night, everyone in costume eating candy on the steps, the ghost peeking.
- 해님 달님: the sun and the moon swing in the sky (the children became them); back cover — sun and moon over the
  quiet cottage, the sorghum field below.
Round 3 (coordinator): the fold is re-timed in the ending (story_runner._quick_fold: every visible hinge starts within
1.7 s, outside-in; the page turns as soon as everything is flat, ~2-3 s in all; spread_stage's camera code untouched);
the curtain shot (cover.json curtain.shot/at) is set at the start of the hold, so a tale that pulled back to a wide
comes back to its cast; a walker who left the page (sun_wind's traveller, curtain entry ["walker", pose, walk_away
dist]) re-enters from up the road onto a mark before the bow. `--end-choice=replay|other` presses an end tab after
STORY_DONE in autoplay (recordings of the replay and shelf paths).
Not done: the cast does not walk to new marks for the bow (they gesture where the story left them); no recorded word
on a curtain-call tap (no fitting short clips checked).

# BOOKSHELF TABLE (entry screen, "다른 동화")
game/story/shelf.tscn (now the project's main scene): the four closed books (BookModel) on the same table, each corner
lifting in turn; tap a book → it slides to the middle, the others slide aside, the camera glides to the cover framing,
the tale's scene loads and its cover opens at once (no prompt). Any command-line user args (--tale, --beat,
--autoplay, --agent-args) pass straight to the story scene, so recordings and probes are unchanged.
