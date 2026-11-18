extends SceneTree
## Ground map around a template view's anchor in the view's camera frame (spots are [right, toward camera]):
## ~ water, = road, . grass. godot --headless --path game --script res://../tools/story/probe_spots.gd -- 2 3 4 5
func _init() -> void:
	var views := []
	for a in OS.get_cmdline_user_args():
		views.append(int(a))
	if views.is_empty():
		views = [2, 3, 4, 5]
	for v in views:
		var w := (load("res://scenes/world/meadow.tscn") as PackedScene).instantiate() as MeadowWorld
		w.view = v
		w.walk = false
		w.with_audio = false
		root.add_child(w)
		while not w.is_built:
			await process_frame
		var yw := deg_to_rad(float(MeadowWorld.VIEWS[v][2]))
		var r := Vector2(cos(yw), -sin(yw))
		var t := Vector2(sin(yw), cos(yw))
		var a := w.walker.global_position
		print("VIEW ", v, " yaw ", MeadowWorld.VIEWS[v][2], "  rows: z from -1.6 (far) to 0.6; cols x -1.6..1.6 step 0.2")
		for zi in range(-8, 4):
			var line := "%5.1f " % (zi * 0.2)
			for xi in range(-8, 9):
				var q := Vector2(a.x, a.z) + r * (xi * 0.2) + t * (zi * 0.2)
				var c := "."
				if w.ground.stream_distance(q) < 0.02:
					c = "~"
				elif w.ground.path_distance(q) < 0.12:
					c = "="
				line += c + " "
			print(line)
		w.queue_free()
		await process_frame
	quit()
