class_name SkyHanger
extends Node3D
## A sky card (sun, wind cloud) held up on a thin paper-wrapped wire (component D).
## Origin = where the wire meets the page (stem mode) or the hanging point above (string mode).
## The wire is a live bezier tube; the card at its tip bobs and sways on a pair of damped springs driven by
## slow noise, plus `push(impulse)` for wind kicks. Swap the print with `set_texture()`.

@export var texture: Texture2D:
	set(v):
		texture = v
		if _card:
			_card.texture = v
@export var card_height := 0.7
@export var stem_height := 1.6  ## base → card bottom (stem) or anchor → card top (string, downward)
@export var hanging := false  ## true: string from above; false: wire stem from the page
@export var lean := Vector3.ZERO  ## static offset of the tip (world units)
@export var wire_radius := 0.0045
@export var wire_color := Color(0.42, 0.36, 0.3)
@export var sway_amount := 0.06  ## tip travel (units)
@export var sway_hz := 0.35
@export var bob_amount := 0.025
@export var spring_hz := 0.9
@export var damping := 0.18
@export var seed_offset := 0.0
@export var card_thickness := 0.014

var _card: PaperCard
var _card_pivot := Node3D.new()
var _wire := MeshInstance3D.new()
var _imesh := ImmediateMesh.new()
var _tip := Vector3.ZERO  ## spring state (offset)
var _tip_v := Vector3.ZERO
var _rot := 0.0
var _rot_v := 0.0
var _t := 0.0
var _scale_pulse := 1.0
var _pulse_v := 0.0
var _pulse_target := 1.0


func _ready() -> void:
	_t = seed_offset * 13.7
	add_child(_card_pivot)
	_card = PaperCard.new()
	_card.texture = texture
	_card.height = card_height
	_card.thickness = card_thickness
	_card.back_print = false
	_card_pivot.add_child(_card)
	_wire.mesh = _imesh
	var m := StandardMaterial3D.new()
	m.albedo_color = wire_color
	m.roughness = 0.9
	_wire.material_override = m
	_wire.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	add_child(_wire)
	_update(0.0)


func set_texture(t: Texture2D) -> void:
	texture = t


## Kick the card (world-space velocity, units/s).
func push(impulse: Vector3) -> void:
	_tip_v += impulse
	_rot_v += impulse.x * -1.5


## Squash-and-puff (e.g. wind filling its cheeks): scale target, eases with a springy overshoot.
func puff(target_scale: float) -> void:
	_pulse_target = target_scale


func card() -> PaperCard:
	return _card


func _process(dt: float) -> void:
	_update(PaperSpring.frame_dt(dt))


func _update(dt: float) -> void:
	_t += dt
	var w := TAU * spring_hz
	# Noise drive: two incommensurate sines per axis, like air moving in a room.
	var drive := Vector3(
		sin(_t * TAU * sway_hz) + 0.5 * sin(_t * TAU * sway_hz * 2.31 + 1.3),
		0.0,
		0.6 * sin(_t * TAU * sway_hz * 0.73 + 0.4)) * sway_amount
	if dt > 0.0:
		var ts := PaperSpring.step3(_tip, _tip_v, drive, w, damping, dt)
		_tip = ts[0]
		_tip_v = ts[1]
		var rw := w * 1.6
		var want_rot := -_tip.x * 1.2
		var rs := PaperSpring.step(_rot, _rot_v, want_rot, rw, 0.25, dt)
		_rot = rs.x
		_rot_v = rs.y
		var pw := 14.0
		var ps := PaperSpring.step(_scale_pulse, _pulse_v, _pulse_target, pw, 0.35, dt)
		_scale_pulse = ps.x
		_pulse_v = ps.y
	var bob := bob_amount * sin(_t * TAU * sway_hz * 0.9 + 2.0)
	var tip := lean + _tip + Vector3(0, bob, 0)
	var top := Vector3(0, stem_height, 0)
	if hanging:
		top = Vector3(0, -stem_height, 0)
	var end := top + tip
	# Card: stem holds it at the bottom centre; string holds it at the top centre.
	_card_pivot.position = end
	_card_pivot.rotation = Vector3(0.25 * _tip.z, 0.0, _rot)
	_card_pivot.scale = Vector3(_scale_pulse, 2.0 - _scale_pulse, 1.0) if absf(_scale_pulse - 1.0) > 1e-4 else Vector3.ONE
	_card.position = Vector3(0, -card_height if hanging else -0.02, -card_thickness)
	# Wire: quadratic bezier, base tangent straight up (stem) or down (string), tip follows the card.
	var ctrl := Vector3(0, end.y * 0.55, 0)
	_imesh.clear_surfaces()
	_imesh.surface_begin(Mesh.PRIMITIVE_TRIANGLES)
	var segs := 14
	var sides := 5
	var prev_ring: Array[Vector3] = []
	var prev_n: Array[Vector3] = []
	for i in segs + 1:
		var u := float(i) / segs
		var p := (1 - u) * (1 - u) * Vector3.ZERO + 2 * (1 - u) * u * ctrl + u * u * end
		var tan := (2 * (1 - u) * (ctrl - Vector3.ZERO) + 2 * u * (end - ctrl)).normalized()
		var side_a := tan.cross(Vector3(0, 0, 1)).normalized()
		if side_a.length() < 0.1:
			side_a = Vector3(1, 0, 0)
		var side_b := tan.cross(side_a).normalized()
		var ring: Array[Vector3] = []
		var ns: Array[Vector3] = []
		for k in sides:
			var a := TAU * k / sides
			var n := side_a * cos(a) + side_b * sin(a)
			ring.append(p + n * wire_radius)
			ns.append(n)
		if i > 0:
			for k in sides:
				var k2 := (k + 1) % sides
				for v in [[prev_ring[k], prev_n[k]], [ring[k], ns[k]], [ring[k2], ns[k2]],
						[prev_ring[k], prev_n[k]], [ring[k2], ns[k2]], [prev_ring[k2], prev_n[k2]]]:
					_imesh.surface_set_normal(v[1])
					_imesh.surface_add_vertex(v[0])
		prev_ring = ring
		prev_n = ns
	_imesh.surface_end()
