class_name WindSway
extends Node3D
## Subtle wind on standing cards (integrator r1). Rigid cards rock about their base (no bending, per the style
## rules): a slow travelling gust field over the page, so neighbours move together and a gust rolls across.
## Register a card's base node with add(node, amp_rad, stiffness). Uses PopHinge.fixed_dt for captures.

@export var wind_dir := Vector2(1.0, -0.35)  ## gusts travel along this page direction
@export var gust_speed := 1.4  ## units / s
@export var strength := 1.0

var _items: Array = []  ## [node, rest_basis, amp, freq, phase, along]
var _t := 0.0


func add(n: Node3D, amp: float, freq: float, phase: float) -> void:
	var p := Vector2(n.global_position.x, n.global_position.z)
	_items.append([n, n.transform.basis, amp, freq, phase, p.dot(wind_dir.normalized())])


func _process(dt: float) -> void:
	if PopHinge.fixed_dt > 0.0:
		dt = PopHinge.fixed_dt
	_t += dt
	var wd := wind_dir.normalized()
	var axis := Vector3(-wd.y, 0, wd.x)  # roll about the axis across the wind (cards nod downwind)
	for it in _items:
		var n: Node3D = it[0]
		var along: float = it[5]
		var g := 0.5 + 0.5 * sin((_t * gust_speed - along) * 0.9)  # travelling gust envelope
		g = g * g
		var a: float = it[2] * strength * (0.35 + 0.65 * g) * (0.6 + 0.4 * sin(_t * float(it[3]) * TAU + float(it[4])))
		var rest: Basis = it[1]
		n.transform.basis = Basis(axis, a) * rest
