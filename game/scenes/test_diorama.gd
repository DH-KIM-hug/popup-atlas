extends Node3D
## Look-dev bench: a patch of page with cut-paper cards, lights, tilt-shift camera.
## Not the shipped scene. `animate` pops everything up in a wave from the centre.

@export var animate := false
@export var seed_value := 3
@export var focus_distance := 8.5

const PROPS := [
	"res://art/test_props/sw_layer_tree_bent.webp",
	"res://art/test_props/sw_layer_snow_bush.webp",
	"res://art/test_props/sw_layer_reeds_stream.webp",
	"res://art/test_props/sw_layer_flowers_mid.webp",
	"res://art/test_props/sw_layer_fern_front.webp",
	"res://art/test_props/sw_layer_mushrooms.webp",
]
const PROP_H := [0.75, 0.32, 0.4, 0.22, 0.3, 0.2]

var camera: Camera3D


func _ready() -> void:
	seed(seed_value)
	_build_world()
	_build_page()
	_build_props()
	if animate:
		_pop_wave()


func _build_world() -> void:
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color("2a1a10")
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color("aebbd4")
	env.ambient_light_energy = 0.55
	env.tonemap_mode = Environment.TONE_MAPPER_AGX
	env.tonemap_exposure = 1.0
	env.glow_enabled = true
	env.glow_intensity = 0.25
	env.glow_bloom = 0.04
	var we := WorldEnvironment.new()
	we.environment = env
	add_child(we)

	var key := DirectionalLight3D.new()
	key.name = "Key"
	key.light_color = Color("ffd29a")
	key.light_energy = 2.2
	key.shadow_enabled = true
	key.light_angular_distance = 2.5
	key.shadow_blur = 1.5
	key.directional_shadow_max_distance = 14.0
	key.rotation_degrees = Vector3(-38, -42, 0)
	add_child(key)

	var fill := DirectionalLight3D.new()
	fill.name = "Fill"
	fill.light_color = Color("9fbbe0")
	fill.light_energy = 0.45
	fill.rotation_degrees = Vector3(-30, 140, 0)
	add_child(fill)

	camera = Camera3D.new()
	camera.name = "Camera"
	camera.fov = 24.0
	var el := deg_to_rad(48.0)
	camera.position = Vector3(0, sin(el), cos(el)) * focus_distance
	add_child(camera)
	camera.look_at(Vector3(0, 0.15, 0))
	var attr := CameraAttributesPractical.new()
	attr.dof_blur_far_enabled = true
	attr.dof_blur_far_distance = focus_distance + 0.8
	attr.dof_blur_far_transition = 2.2
	attr.dof_blur_near_enabled = true
	attr.dof_blur_near_distance = focus_distance - 1.4
	attr.dof_blur_near_transition = 1.2
	attr.dof_blur_amount = 0.22
	camera.attributes = attr
	camera.current = true


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
	# A cream path strip, cut paper lying on the page.
	var path := MeshInstance3D.new()
	var bm := BoxMesh.new()
	bm.size = Vector3(0.55, 0.006, 30)
	path.mesh = bm
	var pmat := StandardMaterial3D.new()
	pmat.albedo_color = Color("eadcc0")
	pmat.roughness = 0.95
	path.material_override = pmat
	path.position = Vector3(0.2, 0.003, 0)
	path.rotation.y = 0.25
	add_child(path)


func _build_props() -> void:
	var placed: Array[Vector2] = []
	var tries := 0
	while placed.size() < 140 and tries < 2000:
		tries += 1
		var p := Vector2(randf_range(-4.5, 4.5), randf_range(-5.0, 3.0))
		# Keep the path clear.
		var along := Vector2(sin(0.25), cos(0.25))
		var off := (p - Vector2(0.2, 0)) - along * (p - Vector2(0.2, 0)).dot(along)
		if off.length() < 0.42:
			continue
		var ok := true
		for q in placed:
			if q.distance_to(p) < 0.3:
				ok = false
				break
		if not ok:
			continue
		placed.append(p)
		var k := randi() % PROPS.size()
		if randf() < 0.3:
			k = 0
		_add_card(load(PROPS[k]), PROP_H[k] * randf_range(0.85, 1.15), Vector3(p.x, 0, p.y), randf_range(-0.35, 0.35))
	# The traveller on the path, the sun and wind hanging above the back.
	_add_card(load("res://art/chars/sw_trav_walk.webp"), 0.36, Vector3(0.05, 0, 0.55), 0.15, 0.008)


func _add_card(tex: Texture2D, h: float, pos: Vector3, yaw: float, thick := 0.012) -> PopHinge:
	var hinge := PopHinge.new()
	hinge.start_up = not animate
	hinge.weight = clampf(h / 0.4, 0.4, 2.5)
	hinge.position = pos
	var base := Node3D.new()
	base.rotation.y = yaw
	add_child(base)
	base.add_child(hinge)
	var card := PaperCard.new()
	card.texture = tex
	card.height = h
	card.thickness = thick
	hinge.add_child(card)
	return hinge


func _pop_wave() -> void:
	for base in get_children():
		for c in base.get_children():
			if c is PopHinge:
				var d := Vector2(base.position.x, base.position.z).length()
				c.pop_up(0.2 + d * 0.25 + randf() * 0.1)
