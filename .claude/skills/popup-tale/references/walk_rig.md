# Paper-puppet walk (all directions)

Walkers can go toward the camera, away from it, or sideways (user, 2026-11-18: "앞뒤 왼쪽 오른쪽도 되긴 해"). The rule is only that the visible figure faces the travel direction:
- **front** figure when moving toward the camera (rig below),
- **back** figure (back of head/clothes, heels toward us) when moving away — same rig, mirrored logic: legs in front of nothing, feet show heels,
- **side profile** figure when moving across the frame: legs pivot fore/aft at the hip (classic brad-jointed paper puppet: leg swing ±20–25°, knee-bend cards, arms swing opposite), flip the card (scale.x = -1 or a mirrored print) for the other direction; side walkers read best and are the cheapest.
Choose the view each frame from the camera-relative travel direction with hysteresis (~30°) and a quick paper 'turn' (card yaw flip over ~0.15 s) when it changes. Expressions are needed per view the beat uses (side faces show emotion well too).

## Front-facing walk details (CastPuppet, game/art/cast/rig/cast_puppet.gd, `front_gait = true`)

What finally read as "a child walking toward me" (sun_wind v7, user: "이 정도는 괜찮다"):
- Direction: walks toward the camera along a road; story camera ahead, looking back, dollying; card yaw toward the
  travel direction kept to 20 % (`front_turn_keep 0.2`), foot sideways offset on screen ≤ 35 % (`front_side_keep`).
- Legs: front-view boots; per-figure leg depth behind the coat/trouser top so a tilted leg never crosses in front of
  it; tilt capped (~20° forward, 24° back); footprints set back by the same depth; step width scales with roll;
  lift 15 % of leg length; half-bent / lifted leg cards swapped by needed length; no shortening/sliding of a leg.
- Body: weight-shift roll 0.6° (wind: 0.6 + 0.6·struggle), front_bob 0.003, front_bounce 0.04, head lag clamp 0.006
  rad, counter-twist 0.5°, push lean 2.5° in wind.
- Arms: separate cards with round shoulder caps, swing opposite the legs, arm_roll 5°, shadows off on arms.
- Joins: seam edges coloured from the garment (cream card cores showed as white lines at the crotch/shoulders).
- Shiver: ~12 Hz, ~3.4° body rock + shoulder bob, feet planted, decays over ~3 s when the cause stops.

Verification recipe for every motion change: record the beat, then
`ffmpeg -ss T -t 2 -i out.mp4 -vf "fps=8,crop=…,tile=8x2" -frames:v 1 tile.jpg` on (a) the whole figure and (b) the
hem/legs. Check: feet toward viewer, no leg tops/seams visible, legs inside the garment silhouette, planted foot
fixed, torso near-vertical, expression matches the line. Fix → re-record → show the user.
