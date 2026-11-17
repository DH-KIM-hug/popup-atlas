extends Node3D
## A0 atlas bench: proves the sliced atlas cards work as pop-up cards. Reads res://art/atlas/catalog.json,
## dresses a page around an S-curved path and a stream with ≥120 cards (cross-slotted trees/bushes as CrossCard).
## Not shipped; look-dev and lighting belong to component B.

@export var seed_value := 7
@export var focus_distance := 7.4
@export var seasons := ["summer", "any", "spring"]

var camera: Camera3D
var cat := {}  # category -> Array[Dictionary]
var placed: Array[Vector3] = []  # x, z, radius
var count := 0


func _ready() -> void:
	seed(seed_value)
	_load_catalog()
	_build_world()
	_build_page()
	_dress()
	print("atlas_bench cards placed: ", count)


func _load_catalog() -> void:
	var data = JSON.parse_string(FileAccess.get_file_as_string("res://art/atlas/catalog.json"))
	for e in data:
		if not (e.get("season", "any") in seasons):
			continue
		var tags: Array = e.get("tags", [])
		if "korean_traditional" in tags or "fairytale" in tags:
			continue
		var c: String = e["category"]
		if not cat.has(c):
			cat[c] = []
		cat[c].append(e)


func _pick(cats: Array) -> Dictionary:
	var pool := []
	for c in cats:
		pool.append_array(cat.get(c, []))
	if pool.is_empty():
		return {}
	return pool[randi() % pool.size()]


func _build_world() -> void:
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color("2a1a10")
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color("aebbd4")
	env.ambient_light_energy = 0.5
	env.tonemap_mode = Environment.TONE_MAPPER_AGX
	var we := WorldEnvironment.new()
	we.environment = env
	add_child(we)
	var key := DirectionalLight3D.new()
	key.light_color = Color("ffd29a")
	key.light_energy = 2.3
	key.shadow_enabled = true
	key.light_angular_distance = 2.0
	key.directional_shadow_max_distance = 16.0
	key.rotation_degrees = Vector3(-36, -40, 0)
	add_child(key)
	var fill := DirectionalLight3D.new()
	fill.light_color = Color("9fbbe0")
	fill.light_energy = 0.4
	fill.rotation_degrees = Vector3(-30, 140, 0)
	add_child(fill)
	camera = Camera3D.new()
	camera.fov = 26.0
	var el := deg_to_rad(44.0)
	camera.position = Vector3(0, sin(el), cos(el)) * focus_distance + Vector3(0, 0, 0.3)
	add_child(camera)
	camera.look_at(Vector3(0, 0.2, 0.3))
	var attr := CameraAttributesPractical.new()
	attr.dof_blur_far_enabled = true
	attr.dof_blur_far_distance = focus_distance + 1.2
	attr.dof_blur_far_transition = 2.5
	attr.dof_blur_near_enabled = true
	attr.dof_blur_near_distance = focus_distance - 1.8
	attr.dof_blur_near_transition = 1.4
	attr.dof_blur_amount = 0.16
	camera.attributes = attr
	camera.current = true


func _path_x(z: float) -> float:
	return 0.55 * sin(z * 0.9) + 0.1


func _stream_z(x: float) -> float:
	return -1.6 + 0.25 * sin(x * 1.3)


func _box(size: Vector3, pos: Vector3, col: Color, yaw := 0.0) -> void:
	var mi := MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = size
	mi.mesh = bm
	var m := StandardMaterial3D.new()
	m.albedo_color = col
	m.roughness = 0.95
	mi.material_override = m
	mi.position = pos
	mi.rotation.y = yaw
	add_child(mi)


func _build_page() -> void:
	var mi := MeshInstance3D.new()
	var pm := PlaneMesh.new()
	pm.size = Vector2(30, 30)
	mi.mesh = pm
	var mat := ShaderMaterial.new()
	mat.shader = preload("res://core/shaders/page.gdshader")
	mat.set_shader_parameter("page_tex", preload("res://art/tex/page_paper.png"))
	mat.set_shader_parameter("fibre_tex", preload("res://art/tex/paper_fibre.jpg"))
	mat.set_shader_parameter("tint", Color("8fb48a"))
	mi.material_override = mat
	add_child(mi)
	# Path: short cream strips along the S curve.
	var z := 4.0
	while z > -6.0:
		var z2 := z - 0.25
		var a := Vector2(_path_x(z), z)
		var b := Vector2(_path_x(z2), z2)
		var mid := (a + b) * 0.5
		var yaw := atan2(b.x - a.x, b.y - a.y)
		_box(Vector3(0.5, 0.006, 0.3), Vector3(mid.x, 0.003, mid.y), Color("eadcc0"), yaw)
		z = z2
	# Stream: teal strips across the page.
	var x := -6.0
	while x < 6.0:
		var x2 := x + 0.25
		var a2 := Vector2(x, _stream_z(x))
		var b2 := Vector2(x2, _stream_z(x2))
		var mid2 := (a2 + b2) * 0.5
		_box(Vector3(0.3, 0.008, 0.42), Vector3(mid2.x, 0.004, mid2.y), Color("3f8f8c"), atan2(b2.x - a2.x, b2.y - a2.y) + PI / 2)
		x = x2


func _free(p: Vector2, r: float) -> bool:
	if absf(p.x - _path_x(p.y)) < 0.36 + r * 0.5:
		return false
	if absf(p.y - _stream_z(p.x)) < 0.26 + r * 0.3:
		return false
	for q in placed:
		if Vector2(q.x, q.y).distance_to(p) < (q.z + r) * 0.5:
			return false
	return true


func _place(e: Dictionary, p: Vector2, scale := 1.0, yaw := 0.0) -> void:
	if e.is_empty():
		return
	var h: float = float(e["height_units"]) * scale * randf_range(0.9, 1.1)
	var tex: Texture2D = load("res://" + e["path"])
	var hinge := PopHinge.new()
	hinge.start_up = true
	hinge.weight = clampf(h / 0.4, 0.4, 2.5)
	var base := Node3D.new()
	base.position = Vector3(p.x, 0, p.y)
	base.rotation.y = yaw
	add_child(base)
	base.add_child(hinge)
	if e.get("cross_slot", false):
		var cc := CrossCard.new()
		cc.texture_a = tex
		cc.height = h
		hinge.add_child(cc)
	else:
		var card := PaperCard.new()
		card.texture = tex
		card.height = h
		card.thickness = clampf(h * 0.04, 0.005, 0.012)
		hinge.add_child(card)
	placed.append(Vector3(p.x, p.y, max(0.15, h * 0.6)))
	count += 1


func _scatter(cats: Array, n: int, xr: Vector2, zr: Vector2, r: float, scale := 1.0, near_path := -1.0) -> void:
	var tries := 0
	var made := 0
	while made < n and tries < n * 60:
		tries += 1
		var p := Vector2(randf_range(xr.x, xr.y), randf_range(zr.x, zr.y))
		if near_path > 0.0 and absf(p.x - _path_x(p.y)) > near_path:
			continue
		if not _free(p, r):
			continue
		_place(_pick(cats), p, scale, randf_range(-0.3, 0.3))
		made += 1


func _dress() -> void:
	# Back row: hills and clouds behind the village.
	for i in 6:
		_place(_pick(["hill"]), Vector2(-3.4 + i * 1.35 + randf_range(-0.2, 0.2), -4.3 + randf_range(-0.15, 0.15)), 1.0)
	for i in 3:
		_place(_pick(["cloud"]), Vector2(-2.6 + i * 2.6, -4.7), 1.0)
	# Bridge where the path crosses the stream.
	var bridges: Array = cat.get("bridge", [])
	if not bridges.is_empty():
		var bz := _stream_z(_path_x(-1.6))
		_place(bridges[0], Vector2(_path_x(bz), bz + 0.02), 1.0)
	# Reeds and water plants along the stream.
	var x := -3.4
	while x < 3.4:
		var side := 1.0 if randf() < 0.5 else -1.0
		var p := Vector2(x, _stream_z(x) + side * 0.3)
		if _free(p, 0.12):
			_place(_pick(["water", "reeds"]), p, 1.0, randf_range(-0.3, 0.3))
		x += randf_range(0.2, 0.36)
	# Village edge behind the stream, trees around it.
	_scatter(["building"], 7, Vector2(-3.2, 3.2), Vector2(-3.9, -2.2), 0.8)
	_scatter(["tree"], 12, Vector2(-3.6, 3.6), Vector2(-4.1, -2.0), 0.5)
	# Near side: meadow, field, trees, bushes, animals.
	_scatter(["tree"], 13, Vector2(-3.4, 3.4), Vector2(-1.1, 2.6), 0.5)
	_scatter(["bush", "hedge"], 20, Vector2(-3.4, 3.4), Vector2(-3.8, 2.8), 0.3)
	_scatter(["animal"], 8, Vector2(-2.8, 2.8), Vector2(-1.0, 2.2), 0.25)
	_scatter(["crop", "fence", "wall"], 10, Vector2(-3.2, 3.2), Vector2(-1.0, 2.8), 0.3)
	_scatter(["prop"], 10, Vector2(-3.2, 3.2), Vector2(-3.6, 2.6), 0.25)
	# Path edge: lanterns, signs, flowers, rocks, grass.
	_scatter(["sign", "lantern"], 6, Vector2(-3, 3), Vector2(-3.8, 2.8), 0.2, 1.0, 0.6)
	_scatter(["flower", "grass", "rock", "mushroom"], 60, Vector2(-3.2, 3.2), Vector2(-3.8, 3.0), 0.12, 1.0, 1.3)
	# Traveller on the path for scale.
	var tz := 0.3
	var trav := {"path": "art/chars/sw_trav_walk.webp", "height_units": 0.36}
	_place(trav, Vector2(_path_x(tz), tz), 1.0, 0.1)
