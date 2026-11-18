extends Node3D
## Lineup of the whole cast library as cards in 3D (catalog-driven): sun + wind expressions on SkyHanger wires at the
## back, the five traveller figures (rigged CastPuppets at rest) and the coat/hat cards in front.
const CAT := "res://art/cast/catalog.json"


func _ready() -> void:
	PaperSpring.fixed_dt = 1.0 / 60.0
	var mi := MeshInstance3D.new()
	var pm := PlaneMesh.new()
	pm.size = Vector2(20, 20)
	mi.mesh = pm
	var m := StandardMaterial3D.new()
	m.albedo_color = Color("7a9468")
	mi.material_override = m
	add_child(mi)
	var rig := LookRig.new()
	rig.elevation_deg = 14.0
	rig.distance = 4.6
	rig.fov = 22.0
	rig.dof_enabled = false
	rig.follow_smooth = 0.0
	rig.focus_height = 0.55
	add_child(rig)
	var cat: Array = JSON.parse_string(FileAccess.get_file_as_string(CAT))
	var sky := cat.filter(func(e): return e.get("hanging", false))
	var figs := cat.filter(func(e): return e.has("skin"))
	var props := cat.filter(func(e): return not e.get("hanging", false) and not e.has("skin"))
	for i in sky.size():
		var e: Dictionary = sky[i]
		var h := SkyHanger.new()
		h.texture = load("res://" + e["path"])
		h.card_height = e["height_units"]
		h.stem_height = 0.5
		h.position = Vector3(-1.5 + i * 0.6, 0, -0.9)
		h.seed_offset = i * 0.37
		add_child(h)
	var poses := ["walk", "walk_nohat", "hold", "shirt", "fan"]
	for i in figs.size():
		var p := CastPuppet.new()
		p.pose = poses[i]
		p.camera = rig.camera
		p.position = Vector3(-0.9 + i * 0.3, 0, 0.1)
		add_child(p)
	for i in props.size():
		var e: Dictionary = props[i]
		var c := PaperCard.new()
		c.texture = load("res://" + e["path"])
		c.height = e["height_units"]
		c.position = Vector3(0.75 + (i % 3) * 0.28, 0, 0.0 + (i / 3) * 0.3)
		add_child(c)
	var focus := Node3D.new()
	focus.position = Vector3(0, 0, -0.2)
	add_child(focus)
	rig.focus_target = focus
	rig.snap()
