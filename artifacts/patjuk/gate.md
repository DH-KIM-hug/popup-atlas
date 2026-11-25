# Gate: patjuk

run: w3_r1.log cb1a2fbfd2
video: /Users/house_of_4k2b/orca/popup-atlas/artifacts/patjuk/rec/w3_r1.mp4

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

## Review notes (re-check on the current build, run w3_r1, 2026-11-25)

- Why re-run: patjuk passed on 2026-11-24 (w2_r6); runner / spread_stage / StoryActor changes landed since (fc90fcc0,
  42dab518, 54df5fff and other agents' uncommitted engine edits on disk), so the gate was re-run on today's build.
- The audit-v1 crash (RUNNER_OFF_TREE spin) does not come back: the run reached STORY_DONE 353.0 s, mp4 355.0 s,
  FROZEN_VIDEO 0, no SCRIPT ERROR / Failed loading.
- Looked at gate_contact_01..05, all 41 motion tile sheets (37 rows, verdicts written), a 1 fps sheet of the swim.
- rim: granny, tiger and the seven helpers are cut in their own colours; no cream edge on any figure.
- steam: only the cauldron in the kitchen; snow reads as snow.
- holes: none in this tale (the awl's floor crack is a flat dark slit).
- houses: house_orbit_all.sh (artifacts/houses/orbit_w3/patjuk/patjuk_audit.jpg) closed_red=0; the cottage and the
  korean template houses are closed volumes; the two open pavilions are open by design.
- empty: helpers enter along the floor mid-frame (each is under the caption for its first ~0.4 s); the swim line plays
  over the jige with the tiger small but in the water, swimming away; short camera glides with no line remain
  (empty yard at 3:07, the shore at 5:20, the camera passing the door frame edges as the tiger runs out at 4:25).
- place: bean field with rows, winter cottage on snow-paper ground, kitchen (hearth, cauldron, jar, shelf), yard, sea.
- felt: matte paper throughout.
