class_name PaperAmbient
extends Node3D
## Ambient life for a pop-up page (C_motion r3, critic r2: "nothing ambient moves between pops"):
## cut-paper butterflies (two die-cut wing cards hinged on a body line, flapping) wander over the
## page, and a few cut-paper leaves drift down, tumbling, and lie on the page a moment before
## lifting again. All rigid cards: wings hinge, leaves rotate; nothing bends.
## Uses PopHinge.fixed_dt when set, so captures are deterministic.

@export var area := Rect2(-2.5, -2.0, 5.0, 4.5)  ## XZ region (page units)
@export var butterflies := 6
@export var leaves := 10
@export var seed_value := 4

const TEX := "res://scenes/motion/tex/"
const WINGS := ["orange", "lemon", "blue", "rose"]
const LEAVES := ["ochre", "red", "orange", "sage"]

var _flies: Array = []  ## [root, wing_l, wing_r, params]
var _leaves: Array = []  ## [node, params]
var _t := 0.0
var _rng := RandomNumberGenerator.new()
var _mats := {}


func _ready() -> void:
	_rng.seed = seed_value
	for i in butterflies:
		_make_fly(i)
	for i in leaves:
		_make_leaf(i)


func _mat(path: String) -> StandardMaterial3D:
	if _mats.has(path):
		return _mats[path]
	var m := StandardMaterial3D.new()
	m.albedo_texture = load(path)
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
	m.alpha_scissor_threshold = 0.5
	m.cull_mode = BaseMaterial3D.CULL_DISABLED
	m.roughness = 0.95
	m.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
	_mats[path] = m
	return m


func _quad(size: Vector2, offset: Vector3, mat: Material) -> MeshInstance3D:
	var q := QuadMesh.new()
	q.size = size
	q.center_offset = offset
	var mi := MeshInstance3D.new()
	mi.mesh = q
	mi.material_override = mat
	return mi


func _make_fly(i: int) -> void:
	var root := Node3D.new()
	add_child(root)
	var s := _rng.randf_range(0.07, 0.09)  # wing length, a little under a flower card
	var mat := _mat(TEX + "wing_%s.png" % WINGS[i % WINGS.size()])
	var wings: Array = []
	for side in [-1, 1]:
		var pivot := Node3D.new()
		root.add_child(pivot)
		# Wing quad lies in the pivot's XZ plane (flat), extending to +X; body line = pivot Z axis.
		var w := _quad(Vector2(s, s), Vector3(s * 0.5, 0, 0), mat)
		w.rotation_degrees.x = -90.0
		pivot.add_child(w)
		pivot.scale.x = side
		wings.append(pivot)
	var body := _quad(Vector2(0.006, s * 0.8), Vector3.ZERO, _mat(TEX + "leaf_sage.png"))
	body.rotation_degrees.x = -90.0
	root.add_child(body)
	var c := Vector2(_rng.randf_range(area.position.x, area.end.x), _rng.randf_range(area.position.y, area.end.y))
	_flies.append([root, wings[0], wings[1], {
		"c": c, "rx": _rng.randf_range(0.25, 0.6), "rz": _rng.randf_range(0.2, 0.45),
		"a": _rng.randf_range(0.18, 0.32), "b": _rng.randf_range(0.22, 0.4), "p": _rng.randf() * TAU,
		"q": _rng.randf() * TAU, "h": _rng.randf_range(0.18, 0.42), "f": _rng.randf_range(7.0, 9.5),
		"ph": _rng.randf() * TAU}])


func _make_leaf(i: int) -> void:
	var n := Node3D.new()
	add_child(n)
	var s := _rng.randf_range(0.05, 0.07)
	var q := _quad(Vector2(s * 0.66, s), Vector3.ZERO, _mat(TEX + "leaf_%s.png" % LEAVES[i % LEAVES.size()]))
	n.add_child(q)
	var prm := {"y0": _rng.randf_range(0.9, 1.6), "fall": _rng.randf_range(0.09, 0.14),
		"sw": _rng.randf_range(0.6, 1.1), "amp": _rng.randf_range(0.08, 0.16), "ph": _rng.randf() * TAU,
		"rest": 0.0, "x": 0.0, "z": 0.0, "y": 0.0, "spin": _rng.randf_range(1.5, 3.0) * (1 if _rng.randf() < 0.5 else -1)}
	_respawn(prm, true)
	_leaves.append([n, prm])


func _respawn(p: Dictionary, anywhere := false) -> void:
	p["x"] = _rng.randf_range(area.position.x, area.end.x)
	p["z"] = _rng.randf_range(area.position.y, area.end.y)
	p["y"] = _rng.randf_range(0.05, p["y0"]) if anywhere else p["y0"]
	p["rest"] = 0.0


func _process(dt: float) -> void:
	if PopHinge.fixed_dt > 0.0:
		dt = PopHinge.fixed_dt
	_t += dt
	for f in _flies:
		var root: Node3D = f[0]
		var p: Dictionary = f[3]
		var c: Vector2 = p["c"]
		var t := _t
		var pos := Vector3(c.x + p["rx"] * sin(t * p["a"] * TAU + p["p"]),
			p["h"] + 0.04 * sin(t * 1.7 + p["ph"]) + 0.015 * sin(t * p["f"] * TAU),
			c.y + p["rz"] * sin(t * p["b"] * TAU + p["q"]))
		var vel := Vector3(p["rx"] * p["a"] * TAU * cos(t * p["a"] * TAU + p["p"]), 0,
			p["rz"] * p["b"] * TAU * cos(t * p["b"] * TAU + p["q"]))
		root.position = pos
		if vel.length() > 1e-4:
			root.rotation.y = atan2(vel.x, vel.z)
		# Flap: wings sweep up together (the body line is the hinge), mostly-up stroke like a real one.
		var fl := sin(t * p["f"] * TAU + p["ph"])
		var ang := deg_to_rad(20.0 + 55.0 * (0.5 + 0.5 * fl))
		(f[1] as Node3D).rotation.z = -ang  # mirrored (left) wing
		(f[2] as Node3D).rotation.z = ang
	for l in _leaves:
		var n: Node3D = l[0]
		var p: Dictionary = l[1]
		if p["y"] <= 0.004:
			# Lying on the page; after a moment it is lifted again (out of view, it respawns high).
			p["rest"] += dt
			if p["rest"] > 2.5:
				_respawn(p)
			n.position = Vector3(p["x"], 0.004, p["z"])
			n.rotation = Vector3(-PI * 0.5, p["ph"], 0)
			continue
		p["y"] = maxf(0.0, p["y"] - p["fall"] * dt)
		var sw := sin(_t * p["sw"] * TAU + p["ph"])
		p["x"] += p["amp"] * cos(_t * p["sw"] * TAU + p["ph"]) * p["sw"] * TAU * dt * 0.5 + 0.03 * dt
		n.position = Vector3(p["x"], p["y"] + 0.004, p["z"])
		# Falling leaf: rocks side to side (falling-leaf pendulum) and slowly spins.
		var near := clampf(p["y"] / 0.08, 0.0, 1.0)
		n.rotation = Vector3(lerpf(-PI * 0.5, -PI * 0.5 + 0.9 * sw, near), _t * p["spin"] + p["ph"], 0.6 * sw * near)
