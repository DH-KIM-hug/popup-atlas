class_name PaperPuppet
extends Node3D
## The traveller as a paper toy: a body card plus two leg cards pinned at the hips (component D).
## Origin = between the feet on the page. The node does NOT move itself: whoever owns it (Walker)
## moves this node; the puppet reads its own world motion every frame and walks to match it:
##  - phase advances by distance travelled / stride, so planted feet never slide (stride = speed × step period),
##  - stance foot is planted in world space, swing foot arcs to its next footprint,
##  - hips ride the stance leg (inverted pendulum) plus a small hop, body waddles (roll) over the stance foot,
##  - the card turns smoothly toward the walk direction (limited so the print stays readable),
##  - pose swaps flip the card edge-on and back with a hop (paper doll turning over).
## Poses with a rig in res://art/chars_rig/rig.json walk; others (fan, sit) are single cards.

signal stepped(foot: int, speed01: float)  ## a foot touched down (for step SFX)
signal pose_changed(pose: String)

const RIG_DIR := "res://art/chars_rig/"
const CHAR_DIR := "res://art/chars/"
const POSES := {
	"walk": "sw_trav_walk", "walk_nohat": "sw_trav_walk_nohat", "hold": "sw_trav_hold",
	"shirt": "sw_trav_shirt", "fan": "sw_trav_fan", "sit": "sw_trav_sit",
}

@export var pose := "walk"
@export var height := 0.36  ## standing height of the full figure (world units)
@export var thickness := 0.008
@export var step_period := 0.29  ## seconds per step at cruise speed
@export var min_stride := 0.035
@export var max_stride := 0.11
@export_range(0.0, 20.0) var waddle_deg := 8.0  ## roll over the stance foot
@export var hop := 0.012  ## extra hop height per step
@export var foot_lift := 0.024  ## swing foot arc height
@export var max_turn_deg := 20.0  ## card yaw toward the walk direction (relative to the camera)
@export var turn_omega := 9.0  ## turn spring (critically damped), 1/s
@export var max_swing_deg := 27.0  ## leg swing limit in the card plane (paper hinge)
@export var max_out_deg := 14.0  ## leg tilt out of the card plane (depth walking)
@export var lean_deg := 3.0  ## forward lean into the walk
@export var camera: Camera3D  ## the card turns relative to this camera; null = world -Z forward

var speed := 0.0  ## measured ground speed
var move_dir := Vector3(0, 0, 1)

var _rig := {}
var _scale_px := 0.0
var _turn := Node3D.new()  ## yaw (turning) + flip squash
var _tilt := Node3D.new()  ## bob, waddle, lean
var _body: PaperCard
var _hips: PaperCard  ## hip piece in front of the leg tops, brads drawn at the pivots
var _legs: Array[Node3D] = []
var _leg_cards: Array[PaperCard] = []
var _leg_rest: Array[Vector3] = []  ## hip → sole vector in tilt space
var _hip_local: Array[Vector3] = []  ## hip position in tilt space
var _sole_x: Array[float] = []  ## sole lateral offset in tilt space
var _rigged := false

var _last_pos := Vector3.ZERO
var _phase := 0.0  ## step phase: integer part = step count, fraction = progress
var _feet: Array[Vector3] = [Vector3.ZERO, Vector3.ZERO]
var _swing_from := Vector3.ZERO
var _walking := false
var _stride := 0.08
var _yaw := 0.0
var _yaw_v := 0.0
var _flip_t := -1.0
var _flip_to := ""
var _pose_hop := 0.0
var _t := 0.0
var _roll := 0.0
var _roll_v := 0.0
var _face_total := 0.0
var _lean := Vector2.ZERO  ## smoothed forward lean (x: in-plane roll, y: pitch toward depth)
var _hem := 0.0  ## coat lag (body card trails the hips roll)
var _hem_v := 0.0
var _body_rest := Vector3.ZERO


func _ready() -> void:
	var f := FileAccess.open(RIG_DIR + "rig.json", FileAccess.READ)
	if f:
		_rig = JSON.parse_string(f.get_as_text())
	add_child(_turn)
	_turn.add_child(_tilt)
	_body = PaperCard.new()
	_body.thickness = thickness
	_tilt.add_child(_body)
	_hips = PaperCard.new()
	_hips.thickness = thickness * 0.7
	_tilt.add_child(_hips)
	for i in 2:
		var leg := Node3D.new()
		leg.top_level = true
		add_child(leg)
		var c := PaperCard.new()
		c.thickness = thickness
		leg.add_child(c)
		_legs.append(leg)
		_leg_cards.append(c)
		_leg_rest.append(Vector3.ZERO)
		_hip_local.append(Vector3.ZERO)
		_sole_x.append(0.0)
	_apply_pose(pose)
	_last_pos = global_position
	_plant_rest()


## Story pose swap: walk, walk_nohat, hold, shirt, fan, sit. Animated flip unless `instant`.
func set_pose(p: String, instant := false) -> void:
	if not POSES.has(p) or (p == pose and _flip_t < 0.0):
		return
	if instant or not is_inside_tree():
		_apply_pose(p)
		return
	_flip_to = p
	_flip_t = 0.0


func is_rigged() -> bool:
	return _rigged


func _apply_pose(p: String) -> void:
	pose = p
	var key: String = POSES[p]
	var r: Dictionary = _rig.get(key, {})
	_rigged = not r.is_empty()
	if not _rigged:
		var tex: Texture2D = load(CHAR_DIR + key + ".webp")
		_body.texture = tex
		_body.height = height * (0.93 if p == "sit" else 1.0)
		_body.position = Vector3.ZERO
		for l in _legs:
			l.visible = false
		_hips.visible = false
		_fix_materials.call_deferred()
		pose_changed.emit(p)
		return
	var fb: Array = r["full_bbox"]
	_scale_px = height / float(fb[3] - fb[1])
	var s := _scale_px
	var cxf := (float(fb[0]) + float(fb[2])) * 0.5
	var fy1 := float(fb[3])
	var bb: Array = r["parts"]["body"]["bbox"]
	_body.texture = load(RIG_DIR + key + "_body.png")
	_body.height = (bb[3] - bb[1]) * s
	_body.position = Vector3(((bb[0] + bb[2]) * 0.5 - cxf) * s, (fy1 - bb[3]) * s, 0.0)
	_body_rest = _body.position
	_body.rotation = Vector3.ZERO
	var sb: Array = r["parts"]["hips"]["bbox"]
	_hips.texture = load(RIG_DIR + key + "_hips.png")
	_hips.height = (sb[3] - sb[1]) * s
	_hips.position = Vector3(((sb[0] + sb[2]) * 0.5 - cxf) * s, (fy1 - sb[3]) * s, -thickness * 1.15)
	_hips.visible = true
	for i in 2:
		var side := "leg_l" if i == 0 else "leg_r"
		var part: Dictionary = r["parts"][side]
		var lb: Array = part["bbox"]
		var hip: Array = part["hip"]
		var lcx := (float(lb[0]) + float(lb[2])) * 0.5
		var z := -thickness * (2.3 + 1.0 * i)  # behind body + hips, legs on separate layers
		_hip_local[i] = Vector3((hip[0] - cxf) * s, (fy1 - hip[1]) * s, z)
		var c := _leg_cards[i]
		c.texture = load(RIG_DIR + key + "_" + side + ".png")
		c.height = (lb[3] - lb[1]) * s
		c.position = Vector3((lcx - hip[0]) * s, -(lb[3] - hip[1]) * s, 0.0)
		_leg_rest[i] = Vector3((lcx - hip[0]) * s, -(lb[3] - hip[1]) * s, 0.0)
		_sole_x[i] = (lcx - cxf) * s
		_legs[i].visible = true
	_fix_materials.call_deferred()
	pose_changed.emit(p)


## PaperCard's print shader darkens the bottom of every card as ground contact. Puppet parts that are not on the
## ground (body hem, hips) get none, legs only a thin band at the sole. Our textures are unique to the puppet,
## so their cached materials are ours to tune.
func _fix_materials() -> void:
	if not _rigged:
		return
	for c: PaperCard in [_body, _hips]:
		_set_ao(c, 0.0, 0.0, 0.0028 if c == _body else 0.0016)
	for c in _leg_cards:
		_set_ao(c, 0.018, 0.3, 0.0016)


## Also thins the cream die-cut rim: on a 0.36-tall figure the default rim reads as a sticker keyline
## and outlines every joint (critic r1), so puppet parts keep only a hairline.
func _set_ao(c: PaperCard, h: float, strength: float, rim := 0.0028) -> void:
	if c.mesh == null:
		_fix_materials.call_deferred()
		return
	var m := c.get_surface_override_material(0) as ShaderMaterial
	if m:
		m.set_shader_parameter("foot_ao_height", h)
		m.set_shader_parameter("foot_ao_strength", strength)
		m.set_shader_parameter("rim_width", rim)


func _basis_turned() -> Basis:
	return Basis(Vector3.UP, _face_total)


func _rest_foot(i: int) -> Vector3:
	var b := _basis_turned()
	return global_position + b.x.normalized() * _sole_x[i]


func _plant_rest() -> void:
	for i in 2:
		_feet[i] = _rest_foot(i)


func _process(dt: float) -> void:
	dt = PaperSpring.frame_dt(dt)
	if dt <= 0.0:
		return
	_t += dt
	# --- measure own motion (owner moved us) ---
	var p := global_position
	var d := p - _last_pos
	d.y = 0.0
	_last_pos = p
	var dist := d.length()
	if dist > maxf(0.5 * height, 0.1):
		# a teleport (place_at at a walk's `from`, a pop-out at a bush / hole, a page change), not travel: measured as
		# travel it read as ~90 m/s for a few frames and spun drawn cycles 1.6-2.6x too fast (turnip v5 gate SKATE)
		dist = 0.0
		d = Vector3.ZERO
	var inst_speed := dist / dt
	speed = lerpf(speed, inst_speed, 1.0 - exp(-12.0 * dt))
	if dist > 1e-5:
		move_dir = d / dist
	# --- turning: critically damped spring toward the walk direction ---
	var fwd := Vector3(0, 0, -1)
	var right := Vector3(1, 0, 0)
	if camera:
		fwd = -camera.global_transform.basis.z
		fwd.y = 0.0
		fwd = fwd.normalized()
		right = Vector3(-fwd.z, 0, fwd.x)
	var want_yaw := _yaw
	if speed > 0.03:
		var lateral := clampf(move_dir.dot(right), -1.0, 1.0)
		want_yaw = deg_to_rad(max_turn_deg) * lateral
		# Root faces the camera; yaw is relative to that, applied in world.
	var face_yaw := atan2(-fwd.x, -fwd.z)  # card +Z toward the camera
	var w := turn_omega
	var ys := PaperSpring.step(_yaw, _yaw_v, want_yaw, w, 1.0, dt)
	_yaw = ys.x
	_yaw_v = ys.y
	_face_total = face_yaw + _yaw
	_turn.global_rotation = Vector3(0, _face_total, 0)
	# --- pose flip ---
	var squash := 1.0
	if _flip_t >= 0.0:
		_flip_t += dt
		var ft := 0.11
		if _flip_t < ft:
			squash = cos(_flip_t / ft * PI * 0.5)
		elif _flip_to != "":
			_apply_pose(_flip_to)
			_flip_to = ""
			_pose_hop = 1.0
		if _flip_t >= ft:
			var u := clampf((_flip_t - ft) / 0.16, 0.0, 1.0)
			squash = sin(u * PI * 0.5) + 0.08 * sin(u * PI) # small overshoot
			if u >= 1.0:
				_flip_t = -1.0
				squash = 1.0
	_turn.scale = Vector3(maxf(squash, 0.02), 1, 1)
	_pose_hop = maxf(0.0, _pose_hop - dt * 4.0)
	var pose_lift := 0.03 * sin(_pose_hop * PI)

	if not _rigged:
		_walking = false
		var bob := 0.0
		var roll := 0.0
		if speed > 0.02:  # single cards just bounce along
			var ph := _t * TAU / (step_period * 2.0)
			bob = absf(sin(ph)) * hop * 1.5
			roll = deg_to_rad(waddle_deg) * sin(ph)
		_tilt.position = Vector3(0, bob + pose_lift, 0)
		_tilt.rotation = Vector3(0, 0, roll)
		return

	# --- gait ---
	var cruise := speed > 0.025
	if cruise:
		_stride = clampf(speed * step_period, min_stride, max_stride)
	var b := _basis_turned()
	var right_w := b.x.normalized()
	if cruise or _walking:
		if not _walking:
			_walking = true
			_phase = 0.0
			_swing_from = _feet[0]
		var adv := dist / maxf(_stride, 1e-4)
		if not cruise:
			adv = dt / step_period  # finish the step in place, closing the feet
		var before := int(floorf(_phase))
		_phase += adv
		var after := int(floorf(_phase))
		if after != before:
			var landed := before % 2
			_feet[landed] = _swing_target(landed, 1.0, right_w, cruise)
			stepped.emit(landed, clampf(speed / 0.4, 0.0, 1.0))
			_swing_from = _feet[(landed + 1) % 2]
			if not cruise:
				_walking = false
				_phase = 0.0
		if _walking:
			var sw := int(floorf(_phase)) % 2
			var s: float = _phase - floorf(_phase)
			var tgt := _swing_target(sw, s, right_w, cruise)
			# Paper-toy swing: the foot hangs back, then snaps through (hinged card, not a tween).
			var u: float = clampf((s - 0.04) / 0.8, 0.0, 1.0)
			var e: float = u * u * u * (u * (u * 6.0 - 15.0) + 10.0)
			var fp := _swing_from.lerp(tgt, e)
			fp.y = global_position.y + foot_lift * sin(PI * s) * (1.0 if cruise else 0.5)
			_feet[sw] = fp
	var stance := 1 - (int(floorf(_phase)) % 2) if _walking else -1
	var sfrac: float = (_phase - floorf(_phase)) if _walking else 0.0
	# Waddle: lean over the stance foot (left foot is -X, so lean left = +Z roll).
	var want_roll := 0.0
	if _walking and stance >= 0:
		want_roll = deg_to_rad(waddle_deg) * sin(PI * sfrac) * (1.0 if stance == 0 else -1.0)
		want_roll *= clampf(speed / 0.2, 0.35, 1.0)
	var rw := 22.0
	var rs := PaperSpring.step(_roll, _roll_v, want_roll, rw, 0.55, dt)
	_roll = rs.x
	_roll_v = rs.y
	var breathe := 0.0 if _walking else 0.004 * sin(_t * 2.3)
	# Forward lean into the walk: in the card plane for sideways walking, a pitch for depth walking.
	var want_lean := Vector2.ZERO
	if _walking and speed > 0.03:
		var b_now := _basis_turned()
		var k := deg_to_rad(lean_deg) * clampf(speed / 0.3, 0.0, 1.0)
		want_lean = Vector2(-move_dir.dot(b_now.x.normalized()), move_dir.dot(b_now.z.normalized())) * k
	_lean = _lean.lerp(want_lean, 1.0 - exp(-6.0 * dt))
	_tilt.rotation = Vector3(_lean.y, deg_to_rad(3.0) * sin(_phase * PI) if _walking else 0.0, _roll + _lean.x)
	# Coat lag: the body card trails the waddle a beat (soft spring on the roll), pivoting at the hips.
	var hs := PaperSpring.step(_hem, _hem_v, _roll, 9.0, 0.45, dt)
	_hem = hs.x
	_hem_v = hs.y
	var lag := clampf((_hem - _roll) * 0.7, -0.05, 0.05)
	var piv := (_hip_local[0] + _hip_local[1]) * 0.5
	piv.z = 0.0
	var rb := Basis(Vector3(0, 0, 1), lag)
	_body.position = piv + rb * (_body_rest - piv)
	_body.rotation = Vector3(0, 0, lag)
	_tilt.position = Vector3.ZERO
	# Hips ride the stance leg: solve height so the stance sole touches its footprint.
	var lift := 0.0
	if _walking and stance >= 0:
		var h0 := _tilt.global_transform * _hip_local[stance]
		var f := _feet[stance]
		var L := _leg_rest[stance].length()
		var dh := Vector2(h0.x - f.x, h0.z - f.z).length()
		dh = minf(dh, L * 0.95)
		var need := f.y + sqrt(L * L - dh * dh)
		lift = need - h0.y + hop * sin(PI * sfrac)
	_tilt.position = Vector3(0, lift + pose_lift + breathe, 0)
	# Legs: aim each hip → sole at its foot.
	var tb := _tilt.global_transform.basis
	for i in 2:
		var hip_w := _tilt.global_transform * _hip_local[i]
		var rest_dir := (tb * _leg_rest[i]).normalized()
		var to_foot := _feet[i] - hip_w
		if not _walking:
			to_foot = rest_dir
		# Hinged paper leg: swing mostly in the card plane (about the card normal), only a little out of it,
		# both clamped, so a foot behind the walk never pokes out sideways (critic r2 "sideways kick").
		var ld := tb.inverse() * to_foot
		var lr := _leg_rest[i]
		var az := 0.0
		var ax := 0.0
		if _walking and ld.length() > 1e-4:
			az = clampf(atan2(ld.x, -ld.y) - atan2(lr.x, -lr.y), -deg_to_rad(max_swing_deg), deg_to_rad(max_swing_deg))
			ax = clampf(-atan2(ld.z, -ld.y), -deg_to_rad(max_out_deg), deg_to_rad(max_out_deg))
		_legs[i].global_transform = Transform3D(tb * Basis(Vector3(1, 0, 0), ax) * Basis(Vector3(0, 0, 1), az), hip_w)
	if not _walking and not cruise:
		_plant_rest()


## Where the swing foot of `i` should be at swing fraction `s`: half a stride ahead of the hips at touchdown.
func _swing_target(i: int, s: float, right_w: Vector3, cruise: bool) -> Vector3:
	var base := global_position + right_w * _sole_x[i]
	if not cruise:
		return base
	# Constant in world at steady speed: R0 + 1.5·stride, i.e. half a stride ahead of the hips at touchdown.
	return base + move_dir * _stride * (1.5 - s)
