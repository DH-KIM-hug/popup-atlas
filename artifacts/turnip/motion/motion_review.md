# Motion review: turnip

run: turnip_v6.log 123eb39fcd
video: /Users/house_of_4k2b/orca/popup-atlas/artifacts/video/turnip_v6.mp4 (offset 0.04 s)

Open EVERY tile sheet (8 fps, zoomed on the mover, time in the corner) and fill `verdict` with `ok` or `fix`,
and a short note (what you saw: cycle reads, feet on the ground, faces the travel way, no hop / skate /
moonwalk / pop). gate.py fails while any verdict is empty or `fix`. Auto flags are in `flags`; a flagged row
marked ok also needs an accepted exception in gate.md.

| # | t (story s) | actor | verb | cycle | dist | flags | tiles | verdict | note |
|---|---|---|---|---|---|---|---|---|---|
| 01 | 79.50-85.00 | grandma | run | run_front | 2.23 (6.6 H) | - | 01_grandma_79.5.jpg | ok | grandma runs out of the kitchen door toward the camera in run_front, then turns side to the line; cycle reads, feet down |
| 02 | 106.43-110.93 | girl | run | run_front | 1.77 (6.8 H) | - | 02_girl_106.4.jpg | ok | the girl runs from the yard in run_front, sideways run into the line behind grandma; no flips |
| 03 | 126.33-129.17 | dog | run | run_cycle | 0.91 (6.0 H) | - | 03_dog_126.3.jpg | ok | puppy bursts from behind the bush in its side run_cycle, runs sideways into the line |
| 04 | 147.67-154.17 | cat | run | run_front | 3.39 (24.7 H) | - | 04_cat_147.7.jpg | ok | cat hops off the barn roof (story jump), runs toward us in run_front, then sideways run_cycle into the line; camera follows (v6 run checked frame by frame 2:27-2:34) |
| 05 | 185.53-187.57 | mouse | run | run_cycle | 0.35 (4.1 H) | - | 05_mouse_185.5.jpg | ok | mouse pops out of the low bank hole, short side run to the cat |
| 06 | 220.90-221.43 | girl | fly | none | 0.24 (0.9 H) | - | 06_girl_220.9.jpg | ok | pop: the whole line tumbles back (handler fall, drawn tumble figure) - intended |
| 07 | 220.90-221.43 | dog | fly | none | 0.25 (1.7 H) | - | 07_dog_220.9.jpg | ok | pop: tumble back with the line - intended |
| 08 | 220.90-221.43 | cat | fly | none | 0.27 (1.9 H) | - | 08_cat_220.9.jpg | ok | pop: tumble back with the line - intended |
| 09 | 220.90-221.43 | mouse | fly | none | 0.28 (3.2 H) | - | 09_mouse_220.9.jpg | ok | pop: tumble back with the line - intended |
| 10 | 234.53-236.73 | dog | walk | walk_back | 0.60 (4.0 H) | - | 10_dog_234.5.jpg | ok | feast walk to the house: puppy walk_back, steps by distance |
| 11 | 234.53-236.87 | girl | walk | walk_back | 0.64 (2.5 H) | - | 11_girl_234.5.jpg | ok | girl walk_back to the house with the family, cycle reads |
| 12 | 234.53-236.87 | cat | walk | walk_back | 0.64 (4.7 H) | - | 12_cat_234.5.jpg | ok | cat walk_back with the family |
| 13 | 234.53-237.07 | mouse | walk | walk_back | 0.70 (8.2 H) | - | 13_mouse_234.5.jpg | ok | mouse walk_back, small but its cycle steps |
| 14 | 234.53-237.20 | grandma | walk | walk_back | 0.74 (2.2 H) | - | 14_grandma_234.5.jpg | ok | grandma walk_back with the family |
| 15 | 234.53-238.50 | grandpa | walk | walk_back | 1.13 (3.1 H) | - | 15_grandpa_234.5.jpg | ok | grandpa walk_back leading the family to the table |
