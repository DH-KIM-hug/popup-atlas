class_name Shelf
extends Control
## The bookshelf table (the app's entry screen and "다른 동화"): every ready tale's closed book lies on the same warm
## table as the covers (BookModel + CoverBook's rig / table). Tap a book: it slides to the middle, the others slide
## aside, the camera glides to the cover framing, and the tale opens straight away (its cover auto-opens).
## App shell (2026-11-23, docs/APP_UI_PLAN.md): the tales come from TaleList (res://app/tales.json + ready story
## folders, so new tales appear by themselves), laid out in a grid that fits landscape and portrait; a locked tale
## (Entitlements) carries a paper lock tag and opens the child-facing "어른에게 보여 주세요" card; AppUI adds the
## grown-up gear (hold 1 s -> parent gate -> 보호자 메뉴).
##
## Command-line runs keep working: any user args (--tale=, --beat=, --autoplay, --agent-args ...) go straight to the
## story scene, which parses them itself. Look test: `-- --shelf-pick=<tale_id>` picks that book after 2.5 s.
## App-shell test args (they keep the shelf): --app-locked (store build: locks on), --app-fresh (default state, not
## saved), --app-screen=<gate|menu|store|names|settings|info|locked|sheet> (open a screen for a screenshot).

const STORY_SCENE := "res://stories/%s/story.tscn"
## the approved four-book layout (landscape) is kept as is; other counts / portrait use the grid below
const SPOTS4 := [Vector3(-0.95, 0, -0.95), Vector3(0.95, 0, -0.98), Vector3(-0.92, 0, 0.98), Vector3(0.98, 0, 1.0)]
const TURNS := [4.0, -3.0, -2.5, 5.0, -4.0, 3.0, 2.0, -5.0]
const NUDGE := [Vector2(0.0, 0.0), Vector2(0.0, -0.03), Vector2(0.03, 0.0), Vector2(0.03, 0.02), Vector2(-0.02, 0.01), Vector2(0.01, -0.02)]
const SHOT := {"el": 64.0, "yaw": 4.0, "dist": 10.9, "fov": 22.0, "at": Vector3(0.05, 0.0, -0.12)}
const DX := 1.9
const DZ := 1.95

var vp: SubViewport
var rig: LookRig
var books: Array = []  ## [{id, model, tale, locked}]
var app: AppUI
var _tags: Control
var _root3d: Node3D
var _shot: Dictionary = SHOT.duplicate()
var _pick := -1
var _t := 0.0
var _pt := 0.0
var _auto := ""
var _screen := ""
var _from: Array = []


func _ready() -> void:
	var args := OS.get_cmdline_user_args()
	for a in args:
		if a.begins_with("--shelf-pick="):
			_auto = a.get_slice("=", 1)
		elif a.begins_with("--app-screen="):
			_screen = a.get_slice("=", 1)
	var from_story := Engine.has_meta("popup_from_story")
	if from_story:
		Engine.remove_meta("popup_from_story")
	var story_args := Array(args).filter(func(a): return not str(a).begins_with("--shelf-") and not str(a).begins_with("--app-"))
	if story_args.size() > 0 and not from_story:
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
	_root3d = CoverBook.make_table(vp, false)
	for e: Dictionary in TaleList.tales():
		var id: String = e["id"]
		var d := _load_tale(id)
		var m := BookModel.new()
		m.name = id
		_root3d.add_child(m)
		m.build(d.get("cover", {}), str(d.get("title", id)))
		books.append({"id": id, "model": m, "tale": e, "locked": not Entitlements.can_play(e)})
	_tags = Control.new()
	_tags.name = "LockTags"
	_tags.set_anchors_preset(Control.PRESET_FULL_RECT)
	_tags.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_tags.draw.connect(_draw_tags)
	add_child(_tags)
	app = AppUI.new()
	app.name = "AppUI"
	add_child(app)
	app.entitlements_changed.connect(_refresh_locks)
	_layout()
	rig.snap()
	get_viewport().size_changed.connect(_on_resize)
	if _screen != "":
		_open_test_screen.call_deferred()


func _open_test_screen() -> void:
	if _screen == "locked":
		for b in books:
			if b["locked"]:
				app.open_locked(str((b["tale"] as Dictionary).get("title", "")))
				return
		app.open_locked(str((books[1]["tale"] as Dictionary).get("title", "")) if books.size() > 1 else "")
	elif _screen == "gate":
		app.open_gate(func(): app.open_screen("menu"))
	else:
		app.open_screen(_screen)


func _refresh_locks() -> void:
	for b in books:
		b["locked"] = not Entitlements.can_play(b["tale"])
	_tags.queue_redraw()


func _on_resize() -> void:
	if vp == null:
		return
	vp.size = Vector2i(get_tree().root.size)
	if _pick < 0:
		_layout()
		rig.snap()


## Grid for the books: landscape 2 columns up to four books (the approved table), 3 columns for 5-6; portrait
## always 2 columns (up to three rows). The camera distance fits the grid with margins for the chrome.
func _layout() -> void:
	var n := books.size()
	var sz := Vector2(get_tree().root.size)
	var aspect := sz.x / maxf(sz.y, 1.0)
	var portrait := aspect < 1.0
	var cols := 2 if (portrait or n <= 4) else 3
	var rows := ceili(float(n) / cols)
	for i in n:
		var m: BookModel = books[i]["model"]
		var p: Vector3
		if n == 4 and not portrait:
			p = SPOTS4[i]
		else:
			var c := i % cols
			var r := i / cols
			var in_row := mini(cols, n - r * cols)  # a short last row is centred
			var nd: Vector2 = NUDGE[i % NUDGE.size()]
			p = Vector3((c - (in_row - 1) * 0.5) * DX + nd.x, 0, (r - (rows - 1) * 0.5) * DZ + nd.y)
		m.position = p
		m.rotation_degrees = Vector3(0, TURNS[i % TURNS.size()], 0)
	_shot = SHOT.duplicate()
	if not (n == 4 and not portrait):
		var hx := (cols - 1) * 0.5 * DX + 0.8
		var hz := (rows - 1) * 0.5 * DZ + 0.62
		var mh := 1.22 if portrait else 1.55  # horizontal margin (the books may come closer to the sides in portrait)
		var mv := 1.3 if portrait else 1.5
		var need := maxf(hz * sin(deg_to_rad(float(SHOT["el"]))) * mv, hx * mh / aspect)
		_shot["dist"] = need / tan(deg_to_rad(float(SHOT["fov"]) * 0.5))
		_shot["at"] = Vector3(0.0, 0.0, 0.02 * rows)
	_apply(_shot)
	_tags.queue_redraw()


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


func _book_screen(m: BookModel) -> Vector2:
	var c := rig.camera.unproject_position(m.global_position + Vector3(0, 0.05, 0))
	return c * (get_viewport_rect().size / Vector2(vp.size))


## A paper lock tag hanging over the corner of each locked book (store build only; the dev build has none).
func _draw_tags() -> void:
	if _pick >= 0:
		return
	var u := app.px_per_pt() if app else 1.0
	var f := AppTheme.font(700)
	for b in books:
		if not b["locked"]:
			continue
		var m: BookModel = b["model"]
		var corner := rig.camera.unproject_position(m.global_position + Vector3(BookModel.W * 0.36, 0.1, -m.D * 0.42))
		corner *= get_viewport_rect().size / Vector2(vp.size)
		var w := 92.0 * u
		var h := 46.0 * u
		var r := Rect2(corner - Vector2(w * 0.5, h * 0.5), Vector2(w, h))
		_tags.draw_rect(Rect2(r.position + Vector2(0, 4 * u), r.size), Color(0.1, 0.06, 0.02, 0.3))
		_tags.draw_rect(r, AppTheme.PAPER)
		_tags.draw_rect(r, AppTheme.EDGE, false, 2.0 * u)
		# a padlock: shackle arc + body
		var lc := r.position + Vector2(22 * u, h * 0.56)
		_tags.draw_arc(lc + Vector2(0, -6 * u), 7 * u, PI, TAU, 16, AppTheme.INK_SOFT, 3.0 * u, true)
		_tags.draw_rect(Rect2(lc + Vector2(-10 * u, -6 * u), Vector2(20 * u, 15 * u)), AppTheme.RED)
		_tags.draw_string(f, r.position + Vector2(38 * u, h * 0.5 + 8 * u), "잠김", HORIZONTAL_ALIGNMENT_LEFT, -1, int(21 * u), AppTheme.INK)


func _unhandled_input(event: InputEvent) -> void:
	if _pick >= 0 or vp == null or (app and app.modal_open()):
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
		if best >= 0 and best_d < vp.size.y * (0.3 if books.size() <= 4 else 0.2):
			if books[best]["locked"]:
				app.open_locked(str((books[best]["tale"] as Dictionary).get("title", "")))
			else:
				_choose(best)


func _choose(i: int) -> void:
	_pick = i
	_pt = 0.0
	_from = []
	app.close_all()
	app.set_chrome_visible(false)
	_tags.queue_redraw()
	for b in books:
		var m: BookModel = b["model"]
		_from.append([m.position, m.rotation_degrees.y])


func _process(dt: float) -> void:
	if vp == null:
		return
	_t += dt
	rig.camera.h_offset = sin(_t * 0.37) * 0.006
	if _auto != "" and _pick < 0 and _t > 2.5:
		var k := -1
		for j in books.size():
			if books[j]["id"] == _auto:
				k = j
		_choose(maxi(k, 0))
	if _pick < 0:
		# idle: each book's corner lifts in turn (they can be opened); locked books stay shut
		for i in books.size():
			var k := fmod(_t + i * 0.8, 3.2) / 0.9
			var a := 6.0 * sin(k * PI) if k < 1.0 else 0.0
			(books[i]["model"] as BookModel).set_open(0.0 if books[i]["locked"] else maxf(a, 0.0))
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
			var away := p0 if p0.length() > 0.3 else Vector3(0, 0, 1.0)
			m.position = p0.lerp(away * 2.6, u)  # the others slide off to the sides
	var cs := CoverBook.SHOT_CLOSED
	var s0 := _shot
	_apply({"el": lerpf(s0["el"], cs["el"], u), "yaw": lerpf(s0["yaw"], cs["yaw"], u),
		"dist": lerpf(s0["dist"], cs["dist"], u), "fov": 22.0, "at": (s0["at"] as Vector3).lerp(cs["at"], u)})
	if _pt >= 1.5:
		set_process(false)
		Engine.set_meta("popup_open_now", true)  # the tale's cover opens at once (the reader already chose it)
		Engine.set_meta("popup_app_launch", true)  # App adds the 책장 button in the story
		get_tree().change_scene_to_file(STORY_SCENE % str(books[_pick]["id"]))
