extends SceneTree
## (wide variant: z -4.8..1.0, x -3..3 step 0.3; witch_candy street layout)
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
		print("VIEW ", v, " yaw ", MeadowWorld.VIEWS[v][2], "  rows: z from -4.8 (far) to 0.9 step 0.3; cols x -3.0..3.0 step 0.3")
		for zi in range(-16, 4):
			var line := "%5.1f " % (zi * 0.3)
			for xi in range(-10, 11):
				var q := Vector2(a.x, a.z) + r * (xi * 0.3) + t * (zi * 0.3)
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
