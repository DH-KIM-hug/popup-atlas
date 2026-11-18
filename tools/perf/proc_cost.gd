extends "res://addons/agentkit/agent_job.gd"
## Times per-frame script work in the meadow after it settles: WindSway._process, CardBatch._process, and counts
## nodes with processing enabled by class.
func run() -> Dictionary:
	var w = (load("res://scenes/world/meadow.tscn") as PackedScene).instantiate()
	w.walk = false
	root.add_child(w)
	await wait_frames(240)
	var out := {}
	var t0 := Time.get_ticks_usec()
	for i in 100:
		w.sway._process(1.0 / 60.0)
	out["sway_us"] = (Time.get_ticks_usec() - t0) / 100.0
	t0 = Time.get_ticks_usec()
	for i in 100:
		w.batch._process(1.0 / 60.0)
	out["batch_us"] = (Time.get_ticks_usec() - t0) / 100.0
	var counts := {}
	var stack: Array = [w]
	while not stack.is_empty():
		var n: Node = stack.pop_back()
		if n.is_processing() or n.is_physics_processing():
			var k := n.get_class() + ":" + str(n.get_script().get_global_name() if n.get_script() else "")
			counts[k] = counts.get(k, 0) + 1
		stack.append_array(n.get_children())
	out["processing"] = counts
	out["dirty"] = w.batch._dirty.size()
	return out
