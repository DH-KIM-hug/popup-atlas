class_name Walker
extends Node3D
## Moves a character over the page (component D). Put a PaperPuppet (or anything) under it.
## - Path mode: follows `path` (Path3D on the page). Tap/click on the page → walks along the path to the
##   point of the path closest to the tap (first straight onto the path if it is off it).
## - Free mode: WASD / arrow keys (desktop testing) move relative to the camera; the next tap returns to the path.
## - `auto_walk` ping-pongs along the whole path (benches, attract mode).
## Speed ramps with a critically damped spring so starts/stops ease like a wind-up toy.

signal arrived

@export var path: Path3D
@export var camera: Camera3D
@export var speed := 0.32  ## cruise speed (world units / s); 0.36 = one body height per ~1.1 s
@export var accel_omega := 7.0
@export var auto_walk := false
@export var start_offset := 0.0
@export var tap_enabled := true
@export var keys_enabled := true

var offset := 0.0  ## distance along the path
var target_offset := 0.0
var _v := 0.0  ## current speed
var _va := 0.0
var _free := false
var _goal_point := Vector3.ZERO
var _to_path := false
var _dir_sign := 1.0
var _moving := false
var _last_dir := Vector3(0, 0, 1)


func _ready() -> void:
	offset = start_offset
	target_offset = offset
	if path and path.curve:
		global_position = _path_point(offset)
		if auto_walk:
			target_offset = path.curve.get_baked_length()


func _path_point(o: float) -> Vector3:
	return path.global_transform * path.curve.sample_baked(clampf(o, 0.0, path.curve.get_baked_length()))


## Walk to the path point nearest to `world_point` (or straight there when there is no path).
func walk_to(world_point: Vector3) -> void:
	_free = false
	if path and path.curve:
		var local := path.global_transform.affine_inverse() * world_point
		target_offset = path.curve.get_closest_offset(local)
		var here := path.curve.get_closest_offset(path.global_transform.affine_inverse() * global_position)
		var on := _path_point(here)
		_to_path = on.distance_to(global_position) > 0.04
		if _to_path:
			_goal_point = on
			offset = here
	else:
		_goal_point = Vector3(world_point.x, global_position.y, world_point.z)
		_to_path = true


func _unhandled_input(event: InputEvent) -> void:
	if not tap_enabled or camera == null:
		return
	var pos := Vector2.ZERO
	var hit := false
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		pos = event.position
		hit = true
	elif event is InputEventScreenTouch and event.pressed:
		pos = event.position
		hit = true
	if not hit:
		return
	var o := camera.project_ray_origin(pos)
	var d := camera.project_ray_normal(pos)
	if absf(d.y) < 1e-4:
		return
	var t := -o.y / d.y
	if t > 0.0:
		auto_walk = false
		walk_to(o + d * t)


func _process(dt: float) -> void:
	dt = PaperSpring.frame_dt(dt)
	if dt <= 0.0:
		return
	var key := Vector2.ZERO
	if keys_enabled:
		if Input.is_physical_key_pressed(KEY_W) or Input.is_physical_key_pressed(KEY_UP): key.y -= 1
		if Input.is_physical_key_pressed(KEY_S) or Input.is_physical_key_pressed(KEY_DOWN): key.y += 1
		if Input.is_physical_key_pressed(KEY_A) or Input.is_physical_key_pressed(KEY_LEFT): key.x -= 1
		if Input.is_physical_key_pressed(KEY_D) or Input.is_physical_key_pressed(KEY_RIGHT): key.x += 1
	if key != Vector2.ZERO:
		_free = true
		auto_walk = false
		_to_path = false
	var want := 0.0
	var dir := Vector3.ZERO
	if _free:
		if key != Vector2.ZERO:
			var fwd := Vector3(0, 0, -1)
			if camera:
				fwd = -camera.global_transform.basis.z
				fwd.y = 0.0
				fwd = fwd.normalized()
			var right := Vector3(-fwd.z, 0, fwd.x)
			dir = (right * key.x - fwd * key.y).normalized()
			want = speed
			_last_dir = dir
		_spring(want, dt)
		global_position += _last_dir * _v * dt
		return
	if _to_path:
		var to := _goal_point - global_position
		to.y = 0.0
		var dist := to.length()
		want = speed * clampf(dist / 0.12, 0.25, 1.0)
		_spring(want, dt)
		if dist < 0.01:
			_to_path = false
			if path == null:
				arrived.emit()
		else:
			global_position += to / dist * minf(_v * dt, dist)
		return
	if path == null or path.curve == null:
		_spring(0.0, dt)
		return
	var L := path.curve.get_baked_length()
	var remain := target_offset - offset
	if auto_walk and absf(remain) < 0.02:
		target_offset = 0.0 if target_offset > L * 0.5 else L
		remain = target_offset - offset
	want = speed * clampf(absf(remain) / 0.12, 0.0, 1.0)
	if absf(remain) < 0.004:
		want = 0.0
		if _moving:
			_moving = false
			arrived.emit()
	else:
		_moving = true
	_spring(want, dt)
	var step := minf(_v * dt, absf(remain))
	offset += signf(remain) * step
	var p := _path_point(offset)
	global_position = Vector3(p.x, global_position.y if path == null else p.y, p.z)


func _spring(want: float, dt: float) -> void:
	var w := accel_omega
	var s := PaperSpring.step(_v, _va, want, w, 1.0, dt)
	_v = maxf(0.0, s.x)
	_va = s.y
