# Critic loop

- Blind A/B vs the reference video (`art_src/reference/video/v_*.jpg`): `tools/look/make_ab.py --name X --seed N --ours …
  --ref …`; key → `artifacts/ab_keys/` (critics must never read it); score with a separate low-effort agent.
- Same-view head-to-head of two of our versions: `tools/look/make_h2h.py`.
- ≥3 critics per round with different lenses (papercraft game art director, pop-up paper engineer, picture-book editor;
  for story flow: picture-book editor, kids' touch-UX designer, pop-up animator). Ask per pair which side is better AND
  "would X / would Y wow you" separately. Average them; one critic alone swung 0.83 ↔ 0.44.
- Keep only rounds that beat the current best; revert otherwise (work on a branch/worktree so revert is a checkout).
- When signals conflict, show the user a comparison grid and let them choose.
- Story-flow critics read the play-through contact sheet + script.json and score /10 with fixes; apply the top fixes
  in one fix round.
- Motion is judged by you on 8 fps tiles first (cheap), then by the user on mp4s — critics on stills miss gait bugs.
- New prop types to "fix" engineering read as dropped-in 3D clutter; the look gap to the reference was lens/light/ground,
  not mechanisms.
- When vs-reference critics and vs-previous-version critics disagree, the user sided with vs-reference (photographed
  miniature). Show the user a comparison grid and let them pick.
