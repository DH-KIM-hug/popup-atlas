extends SceneTree
## Ground map (height class + road) around a template view's anchor in the view frame, fine grid:
## godot --headless --path game --script res://../tools/story/probe_ground_tn.gd -- seed=3 view=4 x0=-3.2 x1=0.4 z0=-3.2 z1=0.3 step=0.1
func _init() -> void:
	var a := {"seed": 3, "view": 4, "x0": -3.2, "x1": 0.4, "z0": -3.2, "z1": 0.3, "step": 0.1}
	for s in OS.get_cmdline_user_args():
		var kv := s.split("=")
		if kv.size() == 2:
			a[kv[0]] = float(kv[1])
	var w := (load("res://scenes/world/meadow.tscn") as PackedScene).instantiate() as MeadowWorld
	w.view = int(a["view"])
	w.seed_value = int(a["seed"])
	w.walk = false
	w.with_audio = false
	root.add_child(w)
	while not w.is_built:
		await process_frame
	var yw := deg_to_rad(float(MeadowWorld.VIEWS[int(a["view"])][2]))
	var r := Vector2(cos(yw), -sin(yw))
	var t := Vector2(sin(yw), cos(yw))
	var an := w.walker.global_position
	var st := float(a["step"])
	var hdr := "       "
	var xi := float(a["x0"])
	while xi <= float(a["x1"]) + 1e-4:
		hdr += ("%d" % int(round(absf(xi) * 10)) % 10)
		xi += st
	print("cols x from ", a["x0"], " step ", st, " (digit = |x|*10 mod 10)")
	print(hdr)
	var z := float(a["z0"])
	while z <= float(a["z1"]) + 1e-4:
		var line := "%6.2f " % z
		var x := float(a["x0"])
		while x <= float(a["x1"]) + 1e-4:
			var q := Vector2(an.x, an.z) + r * x + t * z
			var c := "."
			if w.ground.stream_distance(q) < 0.02:
				c = "~"
			elif w.ground.path_distance(q) < 0.12:
				c = "="
			else:
				var y := w.ground.surface_y(q)
				var lv := int(round((y - (an.y if not a.has("abs") else float(a["abs"]))) / float(a.get("res", 0.05))))
				c = "." if lv == 0 else (str(clampi(lv, -9, 9)) if lv > 0 else "-")
			line += c
			x += st
		print(line)
		z += st
	quit()
