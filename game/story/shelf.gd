class_name Shelf
extends Control
## The bookshelf table (the app's entry screen and "다른 동화"): the four tales' closed books lie on the same warm
## table as the covers (BookModel + CoverBook's rig / table). Tap a book: it slides to the middle, the others slide
## aside, the camera glides to the cover framing, and the tale opens straight away (its cover auto-opens).
##
## Command-line runs keep working: any user args (--tale=, --beat=, --autoplay, --agent-args ...) go straight to the
## story scene, which parses them itself. Look test: `-- --shelf-pick=<tale_id>` picks that book after 2.5 s.

const TALES := ["sun_wind", "three_pigs", "witch_candy", "sunmoon"]
const STORY_SCENE := "res://stories/%s/story.tscn"
const SPOTS := [Vector3(-0.95, 0, -0.95), Vector3(0.95, 0, -0.98), Vector3(-0.92, 0, 0.98), Vector3(0.98, 0, 1.0)]
const TURNS := [4.0, -3.0, -2.5, 5.0]
const SHOT := {"el": 64.0, "yaw": 4.0, "dist": 10.9, "fov": 22.0, "at": Vector3(0.05, 0.0, -0.12)}

var vp: SubViewport
var rig: LookRig
var books: Array = []  ## [{id, model}]
var _pick := -1
var _t := 0.0
var _pt := 0.0
var _auto := ""
var _from: Array = []


func _ready() -> void:
	var args := OS.get_cmdline_user_args()
	for a in args:
		if a.begins_with("--shelf-pick="):
			_auto = a.get_slice("=", 1)
	if _auto == "" and args.size() > 0:
		# a command-line story run (recordings, probes, autoplay): hand over to the story scene untouched
		get_tree().change_scene_to_file.call_deferred(STORY_SCENE % "sun_wind")
		return
	set_anchors_preset(Control.PRESET_FULL_RECT)
	var tr := TextureRect.new()
	tr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	tr.stretch_mode = TextureRect.STRETCH_SCALE
	tr.set_anchors_preset(Control.PRESET_FULL_RECT)
	tr.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(tr)
	vp = SubViewport.new()
	vp.own_world_3d = true
	vp.msaa_3d = Viewport.MSAA_4X
	vp.size = Vector2i(get_tree().root.size)
	add_child(vp)
	tr.texture = vp.get_texture()
	rig = CoverBook.make_rig(false)
	rig.shadow_distance = 16.0
	rig.dof_far_margin = 1.6
	rig.dof_near_margin = 1.6
	rig.tilt_band_half = 0.42
	vp.add_child(rig)
	var root := CoverBook.make_table(vp, false)
	for i in TALES.size():
		var id: String = TALES[i]
		var d := _load_tale(id)
		var m := BookModel.new()
		m.name = id
		root.add_child(m)
		m.build(d.get("cover", {}), str(d.get("title", id)))
		m.position = SPOTS[i]
		m.rotation_degrees = Vector3(0, TURNS[i], 0)
		books.append({"id": id, "model": m})
	_apply(SHOT)
	rig.snap()


func _load_tale(id: String) -> Dictionary:
	var p := "res://stories/%s/script.json" % id
	if not FileAccess.file_exists(p):
		return {}
	var d: Variant = JSON.parse_string(FileAccess.get_file_as_string(p))
	if not d is Dictionary:
		return {}
	var ui: Dictionary = (d as Dictionary).get("ui", {})
	var c: Variant = CoverBook.tale_data(id).get("cover", ui.get("cover", {}))
	return {"cover": c if c is Dictionary else {}, "title": (d as Dictionary).get("title", id)}


func _apply(s: Dictionary) -> void:
	rig.elevation_deg = float(s["el"])
	rig.yaw_deg = float(s["yaw"])
	rig.distance = float(s["dist"])
	rig.fov = float(s["fov"])
	rig.focus_point = s["at"]


func _unhandled_input(event: InputEvent) -> void:
	if _pick >= 0 or vp == null:
		return
	if event is InputEventMouseButton and (event as InputEventMouseButton).pressed:
		var p := (event as InputEventMouseButton).position * (Vector2(vp.size) / get_viewport_rect().size)
		var best := -1
		var best_d := 1e9
		for i in books.size():
			var m: BookModel = books[i]["model"]
			var c := rig.camera.unproject_position(m.global_position + Vector3(0, 0.05, 0))
			var d := c.distance_to(p)
			if d < best_d:
				best_d = d
				best = i
		if best >= 0 and best_d < vp.size.y * 0.3:
			_choose(best)


func _choose(i: int) -> void:
	_pick = i
	_pt = 0.0
	_from = []
	for b in books:
		var m: BookModel = b["model"]
		_from.append([m.position, m.rotation_degrees.y])


func _process(dt: float) -> void:
	if vp == null:
		return
	_t += dt
	rig.camera.h_offset = sin(_t * 0.37) * 0.006
	if _auto != "" and _pick < 0 and _t > 2.5:
		_choose(maxi(TALES.find(_auto), 0))
	if _pick < 0:
		# idle: each book's corner lifts in turn (they can be opened)
		for i in books.size():
			var k := fmod(_t + i * 0.8, 3.2) / 0.9
			var a := 6.0 * sin(k * PI) if k < 1.0 else 0.0
			(books[i]["model"] as BookModel).set_open(maxf(a, 0.0))
		return
	_pt += dt
	var u := clampf(_pt / 1.3, 0.0, 1.0)
	u = u * u * (3.0 - 2.0 * u)
	for i in books.size():
		var m: BookModel = books[i]["model"]
		m.set_open(0.0)
		var f: Array = _from[i]
		var p0: Vector3 = f[0]
		if i == _pick:
			m.position = p0.lerp(Vector3.ZERO, u)
			m.rotation_degrees.y = lerpf(float(f[1]), 0.0, u)
		else:
			m.position = p0.lerp(p0 * 2.6, u)  # the others slide off to the sides
	var cs := CoverBook.SHOT_CLOSED
	_apply({"el": lerpf(SHOT["el"], cs["el"], u), "yaw": lerpf(SHOT["yaw"], cs["yaw"], u),
		"dist": lerpf(SHOT["dist"], cs["dist"], u), "fov": 22.0, "at": (SHOT["at"] as Vector3).lerp(cs["at"], u)})
	if _pt >= 1.5:
		set_process(false)
		Engine.set_meta("popup_open_now", true)  # the tale's cover opens at once (the reader already chose it)
		get_tree().change_scene_to_file(STORY_SCENE % str(books[_pick]["id"]))
