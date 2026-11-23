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
var _climb_t := 0.0


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
	puppet.foot_contact.connect(_on_foot)
	_target = global_position if is_inside_tree() else position


func idle_amount_set(v: float) -> void:
	puppet.idle_amount = v


## Footstep on a contact frame of the drawn cycle (catalog footsteps.contact_frames), surface from the ground /
## the climb (ladder: near-vertical path, roof: any other off-ground segment).
func _on_foot(cycle: String, frame: int) -> void:
	var sd := SoundDirector.current
	if sd == null or pop_target < 0.5:
		return
	var surf := ""
	if _fly:
		surf = "ladder" if view == "back" and _climb_t > 0.0 and absf((_target - global_position).normalized().y) > 0.9 else "roof"
	if cycle != "hop":
		var cf: Dictionary = (sd.cat.get("footsteps", {}) as Dictionary).get("contact_frames", {})
		var by_skin: Dictionary = cf.get(puppet.skin, {})
		var n := (puppet._def().get("cycles", {}) as Dictionary).get(cycle, []).size() as int
		var frames: Array = by_skin.get(cycle, (cf.get("default", {}) as Dictionary).get(str(n), [0]))
		var hit := false
		for f in frames:  # JSON numbers are floats
			if int(f) == frame:
				hit = true
		if not hit:
			return
	sd.footstep(self, surf)


func has_pose(p: String) -> bool:
	return puppet.has_pose(p)


func view_of(p: String) -> String:
	return puppet.pose_view(p)


## Standing figure (expression). Side poses keep the current facing unless `left` is given (0 / 1).
func set_pose(p: String, left := -1) -> void:
	if has_meta("peek") and not p.begins_with("peek_"):
		var pk := "peek_" + ("defiant" if p in ["defiant", "tease", "shout"] else ("brave" if p in ["brave", "proud", "calm"] and puppet.has_pose("peek_brave") else "scared"))
		if puppet.has_pose(pk):
			p = pk
	if not puppet.has_pose(p):
		return
	pose = p
	if left >= 0:
		facing_left = left == 1
	if not _moving:
		_swap_figure(p, facing_left and view_of(p) == "side")


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


## Waypoints (may leave the ground: roof, chimney); fly = false keeps the feet on the ground (a road route).
func follow(points: Array, spd := -1.0, wpose := "", fly := true) -> void:
	_path.clear()
	for q: Vector3 in points:
		_path.append(q)
	_fly = fly
	if spd > 0.0:
		speed = spd
	walk_pose = wpose
	_target = _path.pop_front()
	_moving = true


static var _log_figs: bool = "--log-figs" in OS.get_cmdline_user_args()
var _last_fig_logged := ""


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
		var dn := to / maxf(dist, 1e-5)
		if _fly and absf(dn.y) > 0.92 and puppet.has_pose("climb_cycle"):
			# climbing a rope / braid (rapunzel): the drawn hand-over-hand flipbook, seen from behind
			view = "back"
			puppet.set_figure("climb_cycle", false)
			puppet._hp += step / maxf(puppet.height * 0.4, 0.01)  # hand over hand by height climbed (the puppet measures ground speed only)
		elif _fly and absf(dn.y) > 0.92 and (puppet.has_pose("walk_back") or puppet.has_pose("back_walk")):
			# climbing straight up / down (a ladder): seen from behind (drawn back walk cycle), a rung-to-rung bob
			view = "back"
			puppet.set_figure("walk_back" if puppet.has_pose("walk_back") else "back_walk", false)
			puppet.position.y += absf(sin(_climb_t * 9.0)) * puppet.height * 0.025
			_climb_t += dt
		else:
			_pick_view(dn)
	elif _v < 0.01 and puppet.pose != pose and _flip_ok():
		_swap_figure(pose, facing_left and view_of(pose) == "side")
	if _log_track:
		_track_log(dt)
	_move_log(dt)


## MOVE log (always on; one line per travel segment, read by tools/story/motion_review.py and gate.py):
##   MOVE <t0> <t1> <role> <verb> <cycle|none> <dist> skin= hgt= figs= views= cyc= exp= vmax= dvmax= dg= dz= box= trk=
## verb: walk / run (walk_to / follow on the ground), climb (waypoints off the ground), fly (moved by a tale handler:
## hops, flights, lift arcs, rolls). cycle: the drawn cycle shown most while travelling, "none" = no drawn cycle
## (a static card hopping / gliding, or the old leg rig: figs= says which). dist: ground + vertical travel (world).
## figs: figure:view:frames (view "rig" = rigged legs). cyc: drawn cycles shown (frame flips / cycle frames; static
## cards: the hop phase); exp: ground distance / (0.9 · height), the cycles a no-skate walk needs
## (CastPuppet._cycle_step). vmax / dvmax: top ground speed and the largest one-frame ground-speed change (world / s);
## dg / dz: ground and vertical travel. box: screen box of the figure over the segment (viewport fractions
## x0,y0,x1,y1); trk: t,x,y,h at 4 Hz (foot point, on-screen height; viewport fractions) so tiles can follow the mover.
var _mv := {}
var _mv_last := Vector3.INF
var _mv_still := 0.0
var _mv_hp := 0.0
var _mv_ci := -1


func _move_log(dt: float) -> void:
	var p := global_position + Vector3(0, hop + lift, 0)
	var seen := is_visible_in_tree() and pop_s > 0.5 and camera != null
	if _mv_last == Vector3.INF or not seen:
		_mv_last = p
		_move_flush()
		return
	var d := p - _mv_last
	_mv_last = p
	var h := maxf(puppet.height, 0.01)
	if d.length() > maxf(0.5 * h, 0.1):  # place_at / a page change: a teleport, not travel
		_move_flush()
		return
	var v := d.length() / maxf(dt, 1e-4)
	if v < 0.02:
		_mv_still += dt
		if _mv_still > 0.3:
			_move_flush()
		return
	_mv_still = 0.0
	if _mv.is_empty():
		_mv = {"t0": StoryRunner.now, "dg": 0.0, "dv": 0.0, "vmax": 0.0, "dvmax": 0.0, "v": 0.0, "figs": {},
			"views": {}, "verbs": {}, "cyc": 0.0, "box": Rect2(), "has_box": false, "trk": [], "tk": -1.0}
		_mv_hp = puppet._hp
		_mv_ci = int(puppet._cyc_i)
	_mv["t1"] = StoryRunner.now
	_mv["dg"] = float(_mv["dg"]) + Vector2(d.x, d.z).length()
	_mv["dv"] = float(_mv["dv"]) + absf(d.y)
	var vg := Vector2(d.x, d.z).length() / maxf(dt, 1e-4)  # ground speed (a hop's rise is not a speed jump)
	_mv["n"] = int(_mv.get("n", 0)) + 1
	if int(_mv["n"]) > 1:
		_mv["dvmax"] = maxf(float(_mv["dvmax"]), absf(vg - float(_mv["v"])))
	_mv["v"] = vg
	_mv["vmax"] = maxf(float(_mv["vmax"]), vg)
	var cyc: Dictionary = puppet._def().get("cycles", {})
	var fig := str(puppet.pose)
	# cycles actually shown: every drawn-frame change of the flipbook counts 1 / frames (hops: the hop phase)
	var ci := int(puppet._cyc_i)
	if cyc.has(fig):
		if ci != _mv_ci:
			_mv["cyc"] = float(_mv["cyc"]) + 1.0 / maxf(float((cyc[fig] as Array).size()), 1.0)
	else:
		var hp := float(puppet._hp)
		_mv["cyc"] = float(_mv["cyc"]) + (hp - _mv_hp if hp >= _mv_hp else hp)
	_mv_hp = float(puppet._hp)
	_mv_ci = ci
	var fk := "%s:%s" % [fig, puppet.pose_view(fig) if (cyc.has(fig) or not puppet._rigged) else "rig"]
	_mv["figs"][fk] = int((_mv["figs"] as Dictionary).get(fk, 0)) + 1
	_mv["views"][view] = int((_mv["views"] as Dictionary).get(view, 0)) + 1
	var running := walk_pose.contains("run") or (walk_pose == "scared" and speed >= 0.4)
	var verb := ("climb" if _fly else ("run" if running else "walk")) if _moving else "fly"
	_mv["verbs"][verb] = int((_mv["verbs"] as Dictionary).get(verb, 0)) + 1
	if camera.is_position_behind(p):
		return
	var vs := get_viewport().get_visible_rect().size
	var a := camera.unproject_position(p) / vs
	var b := camera.unproject_position(p + Vector3(0, h * pop_s, 0)) / vs
	var r := Rect2(a, Vector2.ZERO).expand(b)
	_mv["box"] = r if not _mv["has_box"] else (_mv["box"] as Rect2).merge(r)
	_mv["has_box"] = true
	if StoryRunner.now - float(_mv["tk"]) >= 0.25:
		_mv["tk"] = StoryRunner.now
		(_mv["trk"] as Array).append("%.2f,%.3f,%.3f,%.3f" % [StoryRunner.now, a.x, a.y, a.distance_to(b)])


func _move_flush() -> void:
	_mv_still = 0.0
	if _mv.is_empty():
		return
	var m := _mv
	_mv = {}
	var h := maxf(puppet.height, 0.01)
	var dist := float(m["dg"]) + float(m["dv"])
	if int(m.get("n", 0)) < 4 or (float(m["dg"]) < 0.25 * h and float(m["dv"]) < h):
		return  # a nudge (spacing, a snap), a hop in place: not travel
	var best := func(dct: Dictionary) -> String:
		var k := ""
		for x: String in dct:
			if k == "" or int(dct[x]) > int(dct[k]):
				k = x
		return k
	var cyc: Dictionary = puppet._def().get("cycles", {})
	var cy := "none"
	var top := 0
	for fk: String in m["figs"]:
		var f := fk.get_slice(":", 0)
		if cyc.has(f) and int(m["figs"][fk]) > top:
			top = int(m["figs"][fk])
			cy = f
	var parts := []
	for fk: String in m["figs"]:
		parts.append("%s:%d" % [fk, m["figs"][fk]])
	var vparts := []
	for k: String in m["views"]:
		vparts.append("%s:%d" % [k, m["views"][k]])
	var bx: Rect2 = m["box"]
	print("MOVE %.2f %.2f %s %s %s %.3f skin=%s hgt=%.3f figs=%s views=%s cyc=%.2f exp=%.2f vmax=%.3f dvmax=%.3f dg=%.3f dz=%.3f box=%.3f,%.3f,%.3f,%.3f trk=%s" % [
		float(m["t0"]), float(m["t1"]), role, best.call(m["verbs"]), cy, dist, puppet.skin, h, ",".join(parts),
		",".join(vparts), float(m["cyc"]), float(m["dg"]) / (0.9 * h), float(m["vmax"]), float(m["dvmax"]),
		float(m["dg"]), float(m["dv"]), bx.position.x, bx.position.y, bx.end.x, bx.end.y, ";".join(m["trk"])])


func _exit_tree() -> void:
	_move_flush()


## --log-track: while travelling (and 0.4 s after), 8 times a second: the figure shown and its screen box (viewport
## px: foot point x, y and on-screen height) so motion tiles can be cut around the runner (tools/story/run_tiles.py).
static var _log_track: bool = "--log-track" in OS.get_cmdline_user_args()
var _trk_t := 0.0
var _trk_idle := 9.0
static var _trk_vp_logged := false


func _track_log(dt: float) -> void:
	_trk_idle = 0.0 if _moving else _trk_idle + dt
	if _trk_idle > 0.4 or camera == null or not is_visible_in_tree():
		return
	_trk_t -= dt
	if _trk_t > 0.0:
		return
	_trk_t += 0.125
	var cam := get_viewport().get_camera_3d()  # the camera that renders this frame (the page's own may differ)
	if cam == null:
		return
	var foot := global_position + Vector3(0, hop + lift, 0)
	var head := foot + Vector3(0, puppet.height * pop_s, 0)
	if cam.is_position_behind(foot):
		return
	var vs := get_viewport().get_visible_rect().size
	var a := cam.unproject_position(foot)
	var b := cam.unproject_position(head)
	if not _trk_vp_logged:
		_trk_vp_logged = true
		print("TRACK_VP ", int(vs.x), "x", int(vs.y), " same_cam=", int(cam == camera))
	print("TRACK ", role, " t=", snappedf(StoryRunner.now, 0.01), " x=", int(a.x), " y=", int(a.y), " h=", int(a.distance_to(b)),
		" fig=", puppet.pose, " view=", view, " v=", snappedf(_v, 0.01), " moving=", int(_moving))


## Travel figure changes: a paper turn only when the view or the facing changes. Standing profile -> side run cycle
## -> pull (same view, same facing) swaps in place: a flip there read as the card turning edge-on for nothing at every
## start and stop of a run (turnip v5).
func _swap_figure(fig: String, mirror: bool) -> void:
	var same := puppet.pose != fig and puppet._flip_t < 0.0 and view_of(puppet.pose) == view_of(fig) \
		and view_of(fig) == "side" and mirror == puppet._mirror and (_travel_fig(fig) or _travel_fig(str(puppet.pose)))
	puppet.set_figure(fig, mirror, same)


static func _travel_fig(f: String) -> bool:  # expression changes (pull -> tumble) keep their paper flip
	return f.contains("cycle") or f.contains("walk") or f.begins_with("run")


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
	# drawn cycles (side / back) when the cast has them: running (run pose or fast) or walking
	# turnip v5: small animals run at small speeds (a mouse's dash is 0.22/s): the run threshold scales with height
	var running := walk_pose in ["run", "run_cycle", "run_away", "scared"] and speed >= minf(0.4, puppet.height * 3.0)
	var rc := ""
	if nv == "side":
		rc = "run_cycle" if running else "walk_cycle"
		if walk_pose != "" and puppet.has_pose(walk_pose + "_cycle"):  # e.g. carry_straw -> carry_straw_cycle
			rc = walk_pose + "_cycle"
	elif nv == "back":
		rc = "run_back" if running and puppet.has_pose("run_back") else "walk_back"
		if walk_pose != "" and puppet.has_pose(walk_pose + "_back"):  # e.g. ghost -> ghost_back (witch_candy)
			rc = walk_pose + "_back"
	else:
		rc = "run_front" if running and puppet.has_pose("run_front") else "walk_front"
		if walk_pose != "" and puppet.has_pose(walk_pose + "_front"):  # e.g. ghost -> ghost_front (parade)
			rc = walk_pose + "_front"
	if rc != "" and not puppet.has_pose(rc) and rc.begins_with("run"):
		# no drawn run for this view: the walk cycle (a static card hopping reads as a sticker; turnip v4 cat / dog)
		rc = {"side": "walk_cycle", "back": "walk_back", "front": "walk_front"}[nv]
	if rc != "" and puppet.has_pose(rc):
		fig = rc
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
	_swap_figure(fig, facing_left and view_of(fig) == "side")
	if _log_figs and fig != _last_fig_logged:  # --log-figs: which figure each travel uses (hopping-card check)
		_last_fig_logged = fig
		print("TRAVEL_FIG ", role, " ", fig, " view=", nv, " puppet_fig=", puppet.get("pose"))
