class_name StoryActor
extends Node3D
## A story cast member that walks freely over the page (three_pigs and later tales): a CastPuppet skin from the
## shared cast catalog, moved by this node; the puppet reads the motion and walks (front/back figures: the front
## gait; side figures: the side gait; unrigged figures: a paper hop).
##
## Walkers may go any way. Every frame the travel direction relative to the camera picks the figure (toward the
## camera = front, away = back, across = side, mirrored for leftward), with ~30° hysteresis and a quick paper turn
## (the card flips edge-on and back) when the view changes, so a card always faces the way it travels.
## Standing, it shows `pose` (an expression figure); walking, `walk_pose` when that figure's view matches the
## travel direction, else the role's default walking figure for that view.

const DEFAULT_WALK := {"front": "calm", "back": "back_walk", "side": "side_walk"}

var role := ""
var puppet: CastPuppet
var pose := "calm"  ## standing figure
var walk_pose := ""  ## figure while walking (if its view fits)
var camera: Camera3D
var ground: MeadowGround
var view := "front"
var facing_left := false
var speed := 0.18
var spot := ""  ## spot name it stands at (stage bookkeeping)

var _target := Vector3.ZERO
var _path: Array[Vector3] = []  ## remaining waypoints (climb)
var _v := 0.0
var _va := 0.0
var _moving := false
var _fly := false  ## path waypoints may leave the ground (roof, chimney)
## pop (scale y), like the traveller: springs up after the page pops, folds flat with it
var pop_s := 0.02
var _pop_v := 0.0
var pop_target := 0.02
var pop_delay := -1.0
var hop := 0.0
var hop_v := 0.0
var lift := 0.0  ## extra height (falling, launched); set by tale fx
var _root: Node3D


func setup(role_: String, skin: String, height: float, cam: Camera3D, ground_: MeadowGround) -> void:
	role = role_
	camera = cam
	ground = ground_
	name = "Actor_" + role_
	_root = Node3D.new()
	_root.name = "Pop"
	add_child(_root)
	puppet = CastPuppet.new()
	puppet.name = "Puppet"
	puppet.skin = skin
	puppet.height = height
	puppet.camera = cam
	puppet.front_gait = true
	# little paper animals: short quick steps
	puppet.step_period = 0.3
	puppet.min_stride = 0.02
	puppet.max_stride = 0.07 * height / 0.31
	puppet.foot_lift = 0.02 * height / 0.31
	puppet.waddle_deg = 3.0
	puppet.pose = pose if puppet.has_pose(pose) else "calm"
	_root.add_child(puppet)
	_target = global_position if is_inside_tree() else position


func has_pose(p: String) -> bool:
	return puppet.has_pose(p)


func view_of(p: String) -> String:
	return puppet.pose_view(p)


## Standing figure (expression). Side poses keep the current facing unless `left` is given (0 / 1).
func set_pose(p: String, left := -1) -> void:
	if not puppet.has_pose(p):
		return
	pose = p
	if left >= 0:
		facing_left = left == 1
	if not _moving:
		puppet.set_figure(p, facing_left and view_of(p) == "side")


## Turn a standing side figure toward a world point (screen-left / right of it).
func face_point(p: Vector3) -> void:
	if camera == null:
		return
	var a := camera.unproject_position(global_position)
	var b := camera.unproject_position(p)
	facing_left = b.x < a.x
	if not _moving:
		puppet.set_figure(puppet.pose, facing_left and view_of(puppet.pose) == "side")


func place_at(p: Vector3) -> void:
	_path.clear()
	_moving = false
	_v = 0.0
	global_position = p
	_target = p


func walk_to(p: Vector3, spd := -1.0, wpose := "") -> void:
	_path.clear()
	_fly = false
	_target = p
	if spd > 0.0:
		speed = spd
	walk_pose = wpose
	_moving = true


## Waypoints (may leave the ground: roof, chimney).
func follow(points: Array, spd := -1.0, wpose := "") -> void:
	_path.clear()
	for q: Vector3 in points:
		_path.append(q)
	_fly = true
	if spd > 0.0:
		speed = spd
	walk_pose = wpose
	_target = _path.pop_front()
	_moving = true


func moving() -> bool:
	return _moving


func centre() -> Vector3:
	return global_position + Vector3(0, puppet.height * 0.55 * pop_s + hop + lift, 0)


func _process(dt: float) -> void:
	dt = PaperSpring.frame_dt(dt)
	if dt <= 0.0 or puppet == null:
		return
	# pop spring
	if pop_delay >= 0.0:
		pop_delay -= dt
	if pop_delay < 0.0:
		var w := TAU * 2.4
		_pop_v += (-w * w * (pop_s - pop_target) - 2.0 * 0.35 * w * _pop_v) * dt
		pop_s = clampf(pop_s + _pop_v * dt, 0.02, 1.3)
	hop_v -= 6.0 * dt
	hop = maxf(0.0, hop + hop_v * dt)
	if hop <= 0.0 and hop_v < 0.0:
		hop_v = 0.0
	_root.scale = Vector3(1, maxf(pop_s, 0.02), 1)
	_root.visible = pop_s > 0.05
	puppet.position = Vector3(0, hop + lift, 0)
	# movement
	var p := global_position
	var to := _target - p
	if not _fly:
		to.y = 0.0
	var dist := to.length()
	var want := 0.0
	if _moving:
		want = speed * clampf(dist / 0.1, 0.3, 1.0)
	var s := PaperSpring.step(_v, _va, want, 7.0, 1.0, dt)
	_v = maxf(0.0, s.x)
	_va = s.y
	if _moving:
		var step := minf(_v * dt, dist)
		if dist > 1e-5:
			p += to / dist * step
		if not _fly and ground:
			p.y = ground.surface_y(Vector2(p.x, p.z))
		global_position = p
		if dist - step < 0.004:
			if not _path.is_empty():
				_target = _path.pop_front()
			else:
				_moving = false
		_pick_view(to / maxf(dist, 1e-5))
	elif _v < 0.01 and puppet.pose != pose and _flip_ok():
		puppet.set_figure(pose, facing_left and view_of(pose) == "side")


func _flip_ok() -> bool:
	return true


## Travel direction (world) → view + facing, with hysteresis; then the figure for it.
func _pick_view(dir: Vector3) -> void:
	if camera == null:
		return
	var f := -camera.global_transform.basis.z
	f.y = 0.0
	if f.length() < 1e-4:
		return
	f = f.normalized()
	var r := Vector3(-f.z, 0, f.x)
	var d := Vector3(dir.x, 0, dir.z)
	if d.length() < 0.3:  # mostly vertical (climb drop): keep the view
		d = Vector3.ZERO
	var nv := view
	var left := facing_left
	if d != Vector3.ZERO:
		d = d.normalized()
		var a := rad_to_deg(atan2(d.dot(r), d.dot(-f)))  # 0 toward the camera, ±180 away, +90 screen right
		var aa := absf(a)
		var hy := 15.0
		match view:
			"front":
				if aa > 45.0 + hy:
					nv = "back" if aa > 135.0 else "side"
			"back":
				if aa < 135.0 - hy:
					nv = "front" if aa < 45.0 else "side"
			_:
				if aa < 45.0 - hy:
					nv = "front"
				elif aa > 135.0 + hy:
					nv = "back"
		if nv == "side" or (view == "side" and nv == view):
			if absf(a) > 20.0 and absf(a) < 160.0:
				left = a < 0.0
	# figure for the view (fall back to a view this role has)
	var fig := walk_pose
	if fig == "" or not puppet.has_pose(fig) or view_of(fig) != nv:
		fig = str(DEFAULT_WALK[nv])
		if not puppet.has_pose(fig):
			if puppet.has_pose(str(DEFAULT_WALK["side"])) and nv != "front":
				nv = "side"
				fig = str(DEFAULT_WALK["side"])
			else:
				nv = "front"
				fig = pose if view_of(pose) == "front" else "calm"
	view = nv
	facing_left = left
	puppet.set_figure(fig, facing_left and view_of(fig) == "side")
