extends Node3D
## PE r1 check rig: the meadow (view from PE_VIEW) seen from a free camera. PE_CAM = "ex,ey,ez,tx,ty,tz,fov".
## Or PE_FIND = "cross" | "vfold" | "box": aim at the nearest such piece to the traveller.

func _ready() -> void:
	var m := preload("res://scenes/world/meadow.tscn").instantiate() as MeadowWorld
	m.view = int(OS.get_environment("PE_VIEW")) if OS.get_environment("PE_VIEW") != "" else 0
	m.fixed_step = true
	add_child(m)
	var cam := Camera3D.new()
	cam.name = "PeCam"
	add_child(cam)
	var c := OS.get_environment("PE_CAM").split(",")
	var eye := Vector3(0, 2, 4)
	var tgt := Vector3.ZERO
	var fov := 30.0
	if c.size() >= 7:
		eye = Vector3(float(c[0]), float(c[1]), float(c[2]))
		tgt = Vector3(float(c[3]), float(c[4]), float(c[5]))
		fov = float(c[6])
	var find := OS.get_environment("PE_FIND")
	if find != "":
		var best: Node3D = null
		var bd := INF
		var start := m.walker.global_position
		for n in m.find_children("*", "", true, false):
			var ok := false
			if find == "cross":
				ok = n is CrossCard
			elif find == "vfold":
				ok = n is PopHinge and n.get_child_count() == 2 and n.get_child(0) is PaperCard and (n.get_child(0) as PaperCard).half != 0
			elif find == "box":
				ok = n is MeshInstance3D and n.name.begins_with("BedFaces")
			if ok:
				var p := (n as Node3D).global_position
				if n is MeshInstance3D:
					p = (n as MeshInstance3D).get_aabb().get_center()
				var d := p.distance_to(start)
				if d < bd:
					bd = d
					best = n
		if best:
			tgt = best.global_position if not (best is MeshInstance3D) else (best as MeshInstance3D).get_aabb().get_center()
			var hh := float(best.get_meta("card_h", 0.4)) if best is PopHinge else 0.4
			if best is CrossCard:
				hh = (best as CrossCard).height
			tgt.y += hh * 0.4
			var yaw := deg_to_rad(m.rig.yaw_deg)
			var dist := hh * 3.2 + 0.5
			eye = tgt + Vector3(sin(yaw), 0.0, cos(yaw)) * dist * 0.9 + Vector3(0, dist * 0.45, 0)
			print("PE_FIND ", find, " at ", tgt, " d=", bd)
	cam.fov = fov
	cam.position = eye
	cam.look_at(tgt)
	cam.current = true
	if m.rig and m.rig.camera:
		cam.environment = m.rig.camera.environment
		pass
