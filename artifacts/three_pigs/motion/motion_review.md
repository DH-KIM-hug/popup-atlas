# Motion review: three_pigs

run: t15.log 1ff0c8246c
video: /Users/house_of_4k2b/orca/popup-atlas/artifacts/three_pigs/rec/t15.mp4 (offset 0.03 s)

Open EVERY tile sheet (8 fps, zoomed on the mover, time in the corner) and fill `verdict` with `ok` or `fix`,
and a short note (what you saw: cycle reads, feet on the ground, faces the travel way, no hop / skate /
moonwalk / pop). gate.py fails while any verdict is empty or `fix`. Auto flags are in `flags`; a flagged row
marked ok also needs an accepted exception in gate.md.

| # | t (story s) | actor | verb | cycle | dist | flags | tiles | verdict | note |
|---|---|---|---|---|---|---|---|---|---|
| 01 | 29.00-35.80 | pig_a | walk | walk_back | 1.35 (4.3 H) | - | 01_pig_a_29.0.jpg 01_pig_a_29.0_p2.jpg | ok | walk_back cycle reads, away from lens down the path, feet on ground |
| 02 | 29.00-35.80 | pig_b | walk | walk_back | 1.35 (4.5 H) | - | 02_pig_b_29.0.jpg 02_pig_b_29.0_p2.jpg | ok | walk_back with brothers, steady spacing, no skate |
| 03 | 29.00-35.80 | pig_c | walk | walk_back | 1.34 (4.3 H) | - | 03_pig_c_29.0.jpg 03_pig_c_29.0_p2.jpg | ok | walk_back, ok; enters road with the others |
| 04 | 48.33-53.30 | pig_a | walk | carry_straw_back | 1.29 (4.1 H) | - | 04_pig_a_48.3.jpg | ok | carry_straw_back to the pile, partly behind the tap ring / pile but readable; no hop |
| 05 | 89.73-93.47 | pig_b | walk | walk_cycle | 2.21 (7.4 H) | - | 05_pig_b_89.7.jpg | ok | side walk to the bucket, faces travel, cycle advances |
| 06 | 89.73-94.17 | pig_a | walk | walk_back | 2.65 (8.4 H) | - | 06_pig_a_89.7.jpg | ok | walk_back then side as the house rises; faces travel |
| 07 | 99.80-102.60 | pig_a | walk | walk_cycle | 1.31 (4.1 H) | - | 07_pig_a_99.8.jpg | ok | brothers leave in file (new wave-2 staging): side walk, faces travel, leaves the shot then folds |
| 08 | 100.37-103.17 | pig_b | walk | walk_cycle | 1.28 (4.3 H) | - | 08_pig_b_100.4.jpg | ok | follows 0.55 s behind 첫째 on the same road, no overlap, side cycle |
| 09 | 107.73-111.00 | wolf | walk | walk_cycle | 0.75 (1.4 H) | - | 09_wolf_107.7.jpg | ok | wolf side prowl into the straw lot, cycle reads |
| 10 | 143.63-150.90 | pig_a | run | run_back | 4.81 (15.2 H) | - | 10_pig_a_143.6.jpg 10_pig_a_143.6_p2.jpg | ok | run_back / side run to the wood house, cycle per view, into the door |
| 11 | 151.30-152.10 | pig_a | walk | walk_back | 0.20 (0.6 H) | - | 11_pig_a_151.3.jpg | ok | short step through the open wood door, seen from behind |
| 12 | 152.50-157.57 | wolf | walk | walk_back | 4.25 (8.2 H) | - | 12_wolf_152.5.jpg | ok | wolf walk_back up the road to the wood house, followed; cycle reads |
| 13 | 181.60-185.23 | pig_a | run | run_back | 2.58 (8.2 H) | - | 13_pig_a_181.6.jpg | ok | run in file round the wolf to the brick front; pig_b passes just in front of pig_a at the arrival (~185.1), brief |
| 14 | 185.60-186.33 | pig_a | walk | walk_back | 0.25 (0.8 H) | - | 14_pig_a_185.6.jpg | ok | short walk to the brick door, from behind |
| 15 | 181.63-186.40 | pig_b | run | run_back | 3.00 (10.0 H) | - | 15_pig_b_181.6.jpg | ok | run_back behind 첫째, side then back view; ok |
| 16 | 186.80-187.60 | pig_a | walk | walk_back | 0.20 (0.6 H) | - | 16_pig_a_186.8.jpg | ok | in through the brick door; inside a side step to his window spot seen through the doorway |
| 17 | 187.67-189.03 | pig_b | walk | walk_back | 0.36 (1.2 H) | - | 17_pig_b_187.7.jpg | ok | last one in, back view through the doorway, door closes after |
| 18 | 189.43-193.93 | wolf | walk | walk_cycle | 3.66 (7.0 H) | - | 18_wolf_189.4.jpg | ok | wolf side walk up to the brick house, faces travel |
| 19 | 222.77-224.83 | wolf | walk | walk_cycle | 0.44 (0.9 H) | - | 19_wolf_222.8.jpg | ok | wolf finds the ladder (side prowl), whole body in frame |
| 20 | 225.47-242.20 | wolf | climb | walk_cycle | 2.46 (4.7 H) | - | 20_wolf_225.5.jpg 20_wolf_225.5_p2.jpg 20_wolf_225.5_p3.jpg | ok | ladder climb in climb_cycle (back), then side walk up the slope and ridge to the chimney; t15 roof_close aimed at b_climb keeps him whole on the ladder (t14 had him half out of the left edge); head grazes the top edge on the ridge briefly |
| 21 | 257.53-258.40 | wolf | fly | none | 0.85 (1.6 H) | OFF_FRAME | 21_wolf_257.5.jpg | ok | drop from the flue into the pot: falling figure, starts above the frame by design (accepted exception) |
| 22 | 270.03-282.53 | wolf | run | run_back | 13.23 (25.4 H) | SPEED_JUMP | 22_wolf_270.0.jpg 22_wolf_270.0_p2.jpg 22_wolf_270.0_p3.jpg | ok | ouch -> run_away side -> run_cycle -> run_back into the forest, followed by the chase shot; SPEED_JUMP is the burst start (accepted exception) |
