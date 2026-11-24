# Gate: sunmoon

run: full_v15.log 1cd2a34e6f
video: /Users/house_of_4k2b/orca/popup-atlas/artifacts/sunmoon/rec/full_v15.mp4

Contact sheets (every 2.5 s): gate_contact_01.jpg, gate_contact_02.jpg, gate_contact_03.jpg, gate_contact_04.jpg, gate_contact_05.jpg, gate_contact_06.jpg

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

- OVERLAP_COUNT: one 0.2 s sample, boy / girl amt 0.01 at 27.8 s while they file up the steps into the cottage (go_inside pipeline): shoulders touching on the step, physical contact, nobody hidden (tile 03).
- MOTION_FLAG 31: the tiger's slips down the oiled trunk keep the drawn slip figure (a slide / fall, not travel); seen at the trunk in the whole-tree shot.

## Review notes (v15, full_v15.log)

- Looked at all 6 contact sheets and every motion tile sheet (38 rows, verdicts in motion/motion_review.md).
- houses: cottage front + body + the new back wall with its back door (closed volume), rich house solid; the tiled
  hanok reads solid in its wides.
- felt: ridges, pines, the zelkova and the sky clouds are paper prints (Gemini redraws + flatten); no stitch lines seen.
- empty: the escape is now on screen (camera out through the front wall, round the left side, the back door swings in,
  the kids step out); the run, the climbs, the tiger's walk-ins and the slips are in frame.
- Still weak but not failing: the sky kids pop up at the rope's foot as it lands; at pass 3 the low shot shows the
  tiger's big back as he steps out; a corner of the thatch shows for ~1 s in the crane to the tree.
