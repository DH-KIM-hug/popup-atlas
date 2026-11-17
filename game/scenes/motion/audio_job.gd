extends RefCounted
## Sound-density check: a bench with `cards` pieces pops up then folds; returns how many flaps were
## requested vs played and the played-event timeline (sim time, fixed 1/60 s frames).
## gd_run.run_script(P, "res://scenes/motion/audio_job.gd:run", args={"cards": 40})


func run(job) -> Dictionary:
	var cards: int = job.arg("cards", 40)
	var bench = load("res://scenes/motion/motion_bench.tscn").instantiate()
	bench.card_count = cards
	bench.fixed_dt = 1.0 / 60.0
	job.root.add_child(bench)
	var audio: PaperAudio = bench.audio
	audio.log_events = true
	var requested := [0]
	for h in bench.hinges:
		h.flapped.connect(func(_u, _w): requested[0] += 1)
		h.landed.connect(func(_w, _s): requested[0] += 1)
	await job.wait_frames(200)
	var rise := {"requested": requested[0], "played": audio.played, "skipped": audio.skipped, "events": audio.events.duplicate()}
	requested[0] = 0
	audio.played = 0
	audio.skipped = 0
	audio.events.clear()
	bench.wave.fold(bench.hinges, (bench.traveller.get_parent() as Node3D).position, 0.0)
	await job.wait_frames(200)
	var fold := {"requested": requested[0], "played": audio.played, "skipped": audio.skipped, "events": audio.events.duplicate()}
	return {"ok": true, "hinges": bench.hinges.size(), "rise": rise, "fold": fold}
