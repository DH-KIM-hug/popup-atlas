# Gate: three_pigs

run: t15.log 1ff0c8246c
video: /Users/house_of_4k2b/orca/popup-atlas/artifacts/three_pigs/rec/t15.mp4

Contact sheets (every 2.5 s): gate_contact_01.jpg, gate_contact_02.jpg, gate_contact_03.jpg, gate_contact_04.jpg, gate_contact_05.jpg

Tick each box ([x]) only after looking at this run's frames (contact sheets, 12 frames per beat, full-res
crops of every character and set piece). Untick-able? Fix the tale, re-record, run the gate again.

## Visual checklist

- [x] rim: No white / cream die-cut rim on any puppet: cut edges in the figure's own darker colour, line art only (user: "흰색 테두리가 별로"). Full-res crops of every character.
- [x] steam: Steam / smoke / puffs only where something is hot, rising from its mouth: no template chimney smoke over cleared houses, no breath clouds baked into figures, no sparkle bursts that read as steam (user: "이상한데서 김이 모락모락", "셋째집 연기뭐지?").
- [x] holes: Holes read as what the story says: a planting hole is a dark dip laid flat in the furrow with a low heap beside it, a burrow / mouse hole is a low bank at an edge, never a mound with an arch for a planting hole (user: "구멍을 그렇게 파니...?").
- [x] houses: No flat-card houses: every house / barn / shop / cottage is a closed solid volume that fits tightly (sides, roof, back, no slit, no background through it) from every story camera (user: "집들은 무조건 입체적으로 아주 잘 들어맞게"); house_orbit_all.sh red = 0 for closed houses.
- [x] empty: No empty shots: the acting / speaking characters are in every frame of their beat; no shot of bare scenery while a line about someone plays, nobody leaves mid-line (12 frames per beat).
- [x] place: The place named in the story reads on screen: every place a line names (텃밭, 부엌, 헛간 지붕, 쥐구멍...) shows what makes it that place in one wide and one close frame (user: "순무는 텃밭이 없네용?").
- [x] felt: Paper, not felt: ground, set cards and characters are matte cut paper, no wool fuzz or stitch lines (user: "펠트 질감 싫은뎅").

## Accepted exceptions

<!-- - <id gate.py printed>: <reason> -->
- OCCLUDE_COUNT: one line, pig_a pig_b t=150.73 at the wood house doorway: 첫째 steps in through the open door in front of 둘째, who is already inside at the window (doorway occlusion, 0.8 s, both read)
- MOTION_FLAG 21: the wolf's drop down the flue into the pot starts above the room shot by design (0.9 s fall; seen falling into the pot)
- MOTION_FLAG 22: SPEED_JUMP is the burst start of the escape run (ouch -> run_away -> run cycles); the run is followed by the chase shot to the forest

## Review notes (run t15, 2026-11-25)

- Looked at gate_contact_01..05, 1 fps sheets of the climb (224-242 s) and the room (241-250 s), every motion tile of t14
  (t15 differs from t14 only at 227-245 s: frame diff every 3 s) and the new climb tiles of t15.
- rim: pigs, mother, wolf cut in their own colours at full-res crops (pig_a in the room is pale straw in warm light, no rim).
- steam: only the boiling pot in the kitchen and the wolf's huff gusts; no chimney smoke on any house.
- holes: no holes in this tale.
- houses: house_orbit_all.sh (artifacts/houses/orbit_w3/three_pigs/three_pigs_audit.jpg) closed_red=0 for home, straw,
  wood, brick and the template houses; the half-timbered template house behind the brick lot has its roof and body.
- empty: the climb now frames the ladder and the wolf (roof_close at b_climb); the brothers leave the build shot in file;
  short camera travels with no line (0:37 empty meadow between home and the straw lot, ~1 s glide in through the brick
  front at 4:05) remain.
- place: the three lots, the road / bridge, the brick house's kitchen (hearth, pot, shelf, printed right wall).
- felt: matte paper throughout.
