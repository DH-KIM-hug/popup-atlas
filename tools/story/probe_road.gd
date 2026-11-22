extends SceneTree
## (sunmoon 2026-11-22) The whole page's road / stream map (world x, z; 0.4 step) and each template view's anchor,
## so a tale can lay out a long route (three mountain passes) on one spread.
## godot --headless --path game --script res://../tools/story/probe_road.gd [-- <seed>]  (wolf_goats: seed arg)
func _init() -> void:
	var w := (load("res://scenes/world/meadow.tscn") as PackedScene).instantiate() as MeadowWorld
	w.view = 0
	var ua := OS.get_cmdline_user_args()
	if ua.size() > 0:
		w.seed_value = int(ua[0])
	w.walk = false
	w.with_audio = false
	root.add_child(w)
	while not w.is_built:
		await process_frame
	var line := w.ground.path_line()
	var s := "ROAD"
	for i in range(0, line.size(), 4):
		s += " %.2f,%.2f" % [line[i].x, line[i].y]
	print(s)
	for v in MeadowWorld.VIEWS.size():
		var vv: Array = MeadowWorld.VIEWS[v]
		var off: float = w.path.curve.get_baked_length() * float(vv[0])
		var sp := w.path.curve.sample_baked(off)
		print("VIEW %d anchor %.2f,%.2f yaw %.1f" % [v, sp.x, sp.z, vv[2]])
	for zi in range(-25, 26):
		var row := "%5.1f " % (zi * 0.4)
		for xi in range(-35, 36):
			var q := Vector2(xi * 0.4, zi * 0.4)
			var c := "."
			if w.ground.stream_distance(q) < 0.02:
				c = "~"
			elif w.ground.path_distance(q) < 0.15:
				c = "="
			row += c
		print(row)
	quit()
