extends "res://addons/agentkit/agent_job.gd"
## Verifies PopWave.cover_pairs (grid) == the original all-pairs loop on a real meadow.

static func brute(hinges: Array) -> Array:
	var out := []
	for i in hinges.size():
		var a: PopHinge = hinges[i]
		var h: float = a.get_meta("card_h", a.weight * 0.4)
		var hw: float = a.get_meta("half_w", h * 0.5)
		var frame := (a.get_parent() as Node3D).global_transform.affine_inverse() if a.get_parent() is Node3D else Transform3D()
		var o := frame * a.global_position
		for j in hinges.size():
			if i == j:
				continue
			var p: Vector3 = frame * (hinges[j] as PopHinge).global_position - o
			var along := -p.z * float(a.fold)
			if along > 0.0 and along < h * 0.95 and absf(p.x) < hw * 0.9:
				out.append([i, j])
	return out

func run() -> Dictionary:
	var res := {}
	for v in [0, 1, 3]:
		var w = (load("res://scenes/world/meadow.tscn") as PackedScene).instantiate()
		w.view = v
		w.walk = false
		root.add_child(w)
		await wait_frames(1)
		var t0 := Time.get_ticks_usec()
		var b := brute(w.hinges)
		var t1 := Time.get_ticks_usec()
		var g := PopWave.cover_pairs(w.hinges)
		var t2 := Time.get_ticks_usec()
		res["view%d" % v] = {"same": b == g, "pairs": b.size(), "brute_ms": (t1 - t0) / 1000.0, "grid_ms": (t2 - t1) / 1000.0}
		w.queue_free()
		await wait_frames(2)
	return res
