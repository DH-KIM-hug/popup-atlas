class_name WalkerLog
extends Node
## MOVE / TRACK log for the template Walker (sun_wind's traveller, the legacy leg rig), in StoryActor's format, so the
## gate (tools/story/motion_review.py) can review his walks too (gate audit v1: sun_wind was MOTION_NOLOG).
##   MOVE <t0> <t1> <role> walk none <dist> skin= hgt= figs=<pose>:rig:<n> views= cyc=0 exp= vmax= dvmax= dg= dz= box= trk=
## The leg rig has no drawn cycle ("rig" view: motion_review counts it neither as a cycle nor as a static card).
## TRACK lines with --log-track (8 Hz while walking and 0.4 s after).

var walker: Node3D
var puppet: Node3D  ## PaperPuppet / CastPuppet (pose, height)
var role := "traveller"
var skin := "traveller"

static var _log_track: bool = "--log-track" in OS.get_cmdline_user_args()
var _last := Vector3.INF
var _still := 0.0
var _mv := {}
var _trk_t := 0.0
var _trk_idle := 9.0


func _h() -> float:
	return maxf(float(puppet.get("height")) if puppet else 0.4, 0.01)


func _cam() -> Camera3D:
	return get_viewport().get_camera_3d()


func _process(dt: float) -> void:
	dt = PaperSpring.frame_dt(dt)
	if dt <= 0.0 or walker == null or not is_instance_valid(walker):
		return
	var p := walker.global_position
	var seen := walker.is_visible_in_tree()
	if _last == Vector3.INF or not seen:
		_last = p
		_flush()
		return
	var d := p - _last
	_last = p
	var h := _h()
	var v := d.length() / maxf(dt, 1e-4)
	var moving := v >= 0.02
	if _log_track:
		_track(dt, moving)
	if d.length() > maxf(0.5 * h, 0.1):
		_flush()  # a teleport (page change), not travel
		return
	if not moving:
		_still += dt
		if _still > 0.3:
			_flush()
		return
	_still = 0.0
	if _mv.is_empty():
		_mv = {"t0": StoryRunner.now, "dg": 0.0, "dv": 0.0, "vmax": 0.0, "dvmax": 0.0, "v": 0.0, "n": 0, "figs": {},
			"views": {}, "box": Rect2(), "has_box": false, "trk": [], "tk": -1.0}
	_mv["t1"] = StoryRunner.now
	var vg := Vector2(d.x, d.z).length() / maxf(dt, 1e-4)
	_mv["dg"] = float(_mv["dg"]) + Vector2(d.x, d.z).length()
	_mv["dv"] = float(_mv["dv"]) + absf(d.y)
	_mv["n"] = int(_mv["n"]) + 1
	if int(_mv["n"]) > 1:
		_mv["dvmax"] = maxf(float(_mv["dvmax"]), absf(vg - float(_mv["v"])))
	_mv["v"] = vg
	_mv["vmax"] = maxf(float(_mv["vmax"]), vg)
	var fk := "%s:rig" % str(puppet.get("pose") if puppet and "pose" in puppet else "walk")
	_mv["figs"][fk] = int((_mv["figs"] as Dictionary).get(fk, 0)) + 1
	var cam := _cam()
	if cam == null or cam.is_position_behind(p):
		return
	var f := -cam.global_transform.basis.z
	f.y = 0.0
	var dd := Vector3(d.x, 0, d.z)
	var view := "front"
	if f.length() > 1e-4 and dd.length() > 1e-6:
		var a := rad_to_deg(dd.normalized().angle_to(-f.normalized()))
		view = "front" if a < 45.0 else ("back" if a > 135.0 else "side")
	_mv["views"][view] = int((_mv["views"] as Dictionary).get(view, 0)) + 1
	var vs := get_viewport().get_visible_rect().size
	var fa := cam.unproject_position(p) / vs
	var fb := cam.unproject_position(p + Vector3(0, h, 0)) / vs
	var r := Rect2(fa, Vector2.ZERO).expand(fb)
	_mv["box"] = r if not _mv["has_box"] else (_mv["box"] as Rect2).merge(r)
	_mv["has_box"] = true
	if StoryRunner.now - float(_mv["tk"]) >= 0.25:
		_mv["tk"] = StoryRunner.now
		(_mv["trk"] as Array).append("%.2f,%.3f,%.3f,%.3f" % [StoryRunner.now, fa.x, fa.y, fa.distance_to(fb)])


func _flush() -> void:
	_still = 0.0
	if _mv.is_empty():
		return
	var m := _mv
	_mv = {}
	var h := _h()
	if int(m.get("n", 0)) < 4 or float(m["dg"]) < 0.25 * h:
		return
	var parts := []
	for k: String in m["figs"]:
		parts.append("%s:%d" % [k, m["figs"][k]])
	var vparts := []
	for k: String in m["views"]:
		vparts.append("%s:%d" % [k, m["views"][k]])
	var bx: Rect2 = m["box"]
	print("MOVE %.2f %.2f %s walk none %.3f skin=%s hgt=%.3f figs=%s views=%s cyc=0.00 exp=%.2f vmax=%.3f dvmax=%.3f dg=%.3f dz=%.3f box=%.3f,%.3f,%.3f,%.3f trk=%s" % [
		float(m["t0"]), float(m["t1"]), role, float(m["dg"]) + float(m["dv"]), skin, h, ",".join(parts),
		",".join(vparts), float(m["dg"]) / (0.9 * h), float(m["vmax"]), float(m["dvmax"]), float(m["dg"]),
		float(m["dv"]), bx.position.x, bx.position.y, bx.end.x, bx.end.y, ";".join(m["trk"])])


func _track(dt: float, moving: bool) -> void:
	_trk_idle = 0.0 if moving else _trk_idle + dt
	if _trk_idle > 0.4:
		return
	_trk_t -= dt
	if _trk_t > 0.0:
		return
	_trk_t += 0.125
	var cam := _cam()
	if cam == null:
		return
	var foot := walker.global_position
	if cam.is_position_behind(foot):
		return
	var a := cam.unproject_position(foot)
	var b := cam.unproject_position(foot + Vector3(0, _h(), 0))
	print("TRACK ", role, " t=", snappedf(StoryRunner.now, 0.01), " x=", int(a.x), " y=", int(a.y), " h=", int(a.distance_to(b)),
		" fig=", str(puppet.get("pose") if puppet and "pose" in puppet else "walk"), " view=front v=0 moving=", int(moving))


func _exit_tree() -> void:
	_flush()
