extends "res://addons/agentkit/agent_job.gd"
## Build a SpreadStage twice (cold, then warm with another view) and report MeadowWorld/SpreadStage phase timings
## (MeadowWorld.perf_phases / SpreadStage.perf_phases).

func run() -> Dictionary:
	var out := {}
	for pass_i in 2:
		var st := SpreadStage.new()
		st.route = Vector2(2.8, -2.4) if pass_i == 0 else Vector2(1.6, -1.6)
		root.add_child(st)
		var t0 := Time.get_ticks_usec()
		await st.build_async(1, pass_i, false, float(arg("budget_ms", 0.0)))
		var ms := (Time.get_ticks_usec() - t0) / 1000.0
		out["pass%d" % pass_i] = {"total_ms": ms, "world": st.world.perf_phases, "stage": st.perf_phases, "frames": st.build_frames, "max_slice_ms": st.max_slice_ms}
		await wait_frames(3)
		if pass_i == 0:
			st.queue_free()
			await wait_frames(2)
	return out
