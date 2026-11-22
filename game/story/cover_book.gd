class_name CoverBook
extends TextureRect
## The tale's book on a warm wooden table (2026-11-22, user: "책 표지 디자인 제대로 하자"; "그리고 끝났을때도 제대로
## 기획해줘"). A BookModel lies on the table under the tales' look (LookRig: warm low raking key, cool fill, DOF,
## tilt-shift grade, grain), rendered in its own SubViewport / World3D and shown full screen under the UI.
##
## Cover: every 3.2 s the fore-edge lifts a little (a thumb at the corner = "open me"). open(): the board swings over
##   the spine onto the table (hand-eased, a small slap) while the camera rises and pushes onto the title page until
##   it fills the frame; StoryRunner then turns that page (PageTurn) onto the first spread.
## Ending: set_open() shows the book open on its title page; close(shift) pulls back and swings the board shut;
##   turn_over() lifts the book and turns it over onto its back cover (the epilogue picture + "끝").
## Config: script.json ui.cover (see BookModel): art, back, title, end_title, spot, title_rect, end_rect, light, cloth,
##   cloth_dark, endpaper, endpaper_motif, page, mark.

signal opened

const W := BookModel.W
const SHOT_CLOSED := {"el": 62.0, "yaw": 7.0, "dist": 6.0, "fov": 22.0, "at": Vector3(0.05, 0.0, 0.26)}
const OPEN_MAX := 177.0  ## the board lies on the table, sloping from the spine
const T_SWING := 1.25
const T_OPEN := 2.35
const T_FLIP := 1.3

var cfg: Dictionary = {}
var vp: SubViewport
var rig: LookRig
var model: BookModel
var shift := 0.0  ## framing offset (world x) that puts the book left of centre for the end tabs
var _t := 0.0
var _anim := ""  ## "" idle | open | done | close | closed | recenter | flip | back
var _at := 0.0
var _peek_t := 1.6
var _shot_a: Dictionary
var _shot_b: Dictionary


func _init() -> void:
	expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	stretch_mode = TextureRect.STRETCH_SCALE
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	set_anchors_preset(Control.PRESET_FULL_RECT)


## The tale's book data: game/stories/<tale>/cover.json {cover: {...BookModel config}, curtain: {...}} (its own file so
## the cover work never edits a tale's script.json); {} when the tale has none.
static func tale_data(tale_id: String) -> Dictionary:
	var p := "res://stories/%s/cover.json" % tale_id
	if not FileAccess.file_exists(p):
		return {}
	var d: Variant = JSON.parse_string(FileAccess.get_file_as_string(p))
	return d if d is Dictionary else {}


func build(c: Dictionary, title: String) -> void:
	cfg = c.duplicate()
	vp = SubViewport.new()
	vp.name = "CoverVP"
	vp.own_world_3d = true
	vp.msaa_3d = Viewport.MSAA_4X
	vp.size = _vp_size()
	vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	add_child(vp)
	texture = vp.get_texture()
	rig = make_rig(str(cfg.get("light", "day")) == "night")
	vp.add_child(rig)
	var root := make_table(vp, str(cfg.get("light", "day")) == "night")
	model = BookModel.new()
	model.name = "Book"
	root.add_child(model)
	model.build(cfg, title)
	_apply_shot(_shot_closed())
	rig.snap()


## The shared table look (also the bookshelf table): LookRig tuned for a book on a table.
static func make_rig(night: bool) -> LookRig:
	var r := LookRig.new()
	r.name = "Rig"
	r.follow_smooth = 0.0
	r.focus_height = 0.0
	r.dof_near_margin = 1.0
	r.dof_far_margin = 0.7
	r.dof_near_transition = 1.4
	r.dof_far_transition = 2.4
	r.dof_amount = 0.1
	r.tilt_blur = 0.55
	r.tilt_focus_y = 0.44
	r.tilt_band_half = 0.3
	r.tilt_band_soft = 0.3
	r.tilt_top_bias = 1.0
	r.lens_soft = 0.05
	r.grain = 0.03
	r.toe = 0.25
	r.post_contrast = 1.06
	r.post_saturation = 0.94
	r.vignette = 0.34
	r.haze_enabled = false
	r.key_elevation_deg = 38.0
	r.key_yaw_deg = -48.0
	r.key_color = Color("ffd2a0") if night else Color("ffdcb4")
	r.key_energy = 2.4 if night else 2.6
	r.shadow_opacity = 0.78
	r.shadow_softness = 2.4
	r.shadow_distance = 9.0
	r.fill_color = Color("7f8fc4") if night else Color("a7b6d8")
	r.fill_energy = 0.3 if night else 0.38
	r.ambient_color = Color("8a6a58") if night else Color("b59c80")
	r.ambient_energy = 0.42 if night else 0.5
	r.exposure = 0.96
	r.background = Color("24160d")
	return r


static func make_table(parent: Node, night: bool) -> Node3D:
	var root := Node3D.new()
	root.name = "Scene"
	parent.add_child(root)
	var table := ShaderMaterial.new()
	table.shader = BookModel.SHADER
	table.set_shader_parameter("mode", 3)
	table.set_shader_parameter("tint", Color("7a5234"))
	table.set_shader_parameter("tint2", Color("553522"))
	BookModel.mesh(root, BookModel.plane(16.0, 16.0), table, Vector3.ZERO, Vector3(0, 23, 0))
	if night:
		var lamp := OmniLight3D.new()
		lamp.light_color = Color("ffb870")
		lamp.light_energy = 1.4
		lamp.omni_range = 5.0
		lamp.omni_attenuation = 1.6
		lamp.position = Vector3(-2.4, 1.6, -1.2)
		lamp.shadow_enabled = false
		root.add_child(lamp)
	return root


func _vp_size() -> Vector2i:
	var s := Vector2i(get_tree().root.size) if is_inside_tree() else Vector2i(1366, 1024)
	return Vector2i(maxi(s.x, 640), maxi(s.y, 480))


# ------------------------------------------------------------------ shots

func _apply_shot(s: Dictionary) -> void:
	rig.elevation_deg = float(s["el"])
	rig.yaw_deg = float(s["yaw"])
	rig.distance = float(s["dist"])
	rig.fov = float(s["fov"])
	rig.focus_point = s["at"]


func _shot_closed() -> Dictionary:
	var s := SHOT_CLOSED.duplicate()
	s["at"] = (s["at"] as Vector3) + Vector3(shift, 0, 0)
	return s


func _shot_open() -> Dictionary:
	# straight down onto the title page, close enough that the page overfills the frame (it then turns like any page)
	var ps := model.page_size()
	var aspect := float(vp.size.x) / float(vp.size.y)
	var need_h := minf(ps.y * 0.94, ps.x * 0.94 / aspect)
	var dist := need_h * 0.5 / tan(deg_to_rad(22.0 * 0.5))
	return {"el": 88.5, "yaw": 0.0, "dist": dist, "fov": 22.0, "at": model.page_centre()}


func _current_shot() -> Dictionary:
	return {"el": rig.elevation_deg, "yaw": rig.yaw_deg, "dist": rig.distance, "fov": rig.fov, "at": rig.focus_point}


func _lerp_shot(a: Dictionary, b: Dictionary, u: float) -> Dictionary:
	return {"el": lerpf(a["el"], b["el"], u), "yaw": lerpf(a["yaw"], b["yaw"], u), "dist": lerpf(a["dist"], b["dist"], u),
		"fov": lerpf(a["fov"], b["fov"], u), "at": (a["at"] as Vector3).lerp(b["at"], u)}


# ------------------------------------------------------------------ states

func open() -> void:
	_anim = "open"
	_at = 0.0
	_shot_a = _current_shot()
	_shot_b = _shot_open()


## Show the book open on its title page (the ending starts here, under a page turn).
func set_open() -> void:
	model.set_open(OPEN_MAX)
	_apply_shot(_shot_open())
	_anim = "done"


## Close the open book; `shift_x` slides the closed framing so the book sits left of centre (room for the end tabs).
func close(shift_x := 0.0) -> void:
	shift = shift_x
	_anim = "close"
	_at = 0.0
	_shot_a = _current_shot()
	_shot_b = _shot_closed()


## The closed book turns over onto its back cover (epilogue picture + "끝").
func turn_over() -> void:
	_anim = "flip"
	_at = 0.0


## A closed (or back-up) book shown again as the cover (replay): turn it face up, glide to the cover framing.
func idle() -> void:
	shift = 0.0
	_anim = "recenter"
	_at = 0.0
	_shot_a = _current_shot()
	_shot_b = _shot_closed()


func is_animating() -> bool:
	return _anim in ["open", "close", "flip", "recenter"]


func is_closed() -> bool:
	return _anim in ["", "closed", "back", "recenter"]


func _ease_swing(u: float) -> float:
	# a hand: slow lift, quicker sweep over the top, soft fall
	return u * u * (3.0 - 2.0 * u) * 0.75 + (1.0 - pow(1.0 - u, 3.0)) * 0.25


func _smooth(u: float) -> float:
	u = clampf(u, 0.0, 1.0)
	return u * u * (3.0 - 2.0 * u)


var _flip_u := 0.0


func step(dt: float) -> void:
	if rig == null:
		return
	_t += dt
	match _anim:
		"":
			# thumb-lift hint at the fore-edge every 3.2 s
			_peek_t -= dt
			var a := 0.0
			if _peek_t < 0.0:
				var k := -_peek_t / 0.9
				if k >= 1.0:
					_peek_t = 3.2
				else:
					a = 7.0 * sin(k * PI) * (1.0 - 0.25 * k) + 1.2 * sin(k * PI * 3.0) * (1.0 - k)
			model.set_open(maxf(a, 0.0))
		"open":
			_at += dt
			var u := clampf(_at / T_SWING, 0.0, 1.0)
			var ang := OPEN_MAX * _ease_swing(u)
			if _at > T_SWING:  # the slap: a little bounce off the table
				var k2 := clampf((_at - T_SWING) / 0.35, 0.0, 1.0)
				ang = OPEN_MAX - 4.0 * sin(k2 * PI) * (1.0 - k2)
			model.set_open(ang)
			_apply_shot(_lerp_shot(_shot_a, _shot_b, _smooth((_at - 0.35) / (T_OPEN - 0.35))))
			if _at >= T_OPEN:
				_anim = "done"
				opened.emit()
		"close":
			_at += dt
			_apply_shot(_lerp_shot(_shot_a, _shot_b, _smooth(_at / 1.2)))
			var us := clampf((_at - 0.5) / T_SWING, 0.0, 1.0)
			var ang2 := OPEN_MAX * (1.0 - _ease_swing(us))
			if _at > 0.5 + T_SWING:  # a soft slap as it lands shut
				var k3 := clampf((_at - 0.5 - T_SWING) / 0.3, 0.0, 1.0)
				ang2 = 3.0 * sin(k3 * PI) * (1.0 - k3)
			model.set_open(ang2)
			if _at >= 0.5 + T_SWING + 0.3:
				model.set_open(0.0)
				_anim = "closed"
		"flip":
			_at += dt
			_flip_u = clampf(_at / T_FLIP, 0.0, 1.0)
			model.set_flip(_flip_u)
			if _at >= T_FLIP:
				_anim = "back"
		"recenter":
			_at += dt
			var ur := _smooth(_at / 0.9)
			_apply_shot(_lerp_shot(_shot_a, _shot_b, ur))
			if _flip_u > 0.0:
				_flip_u = maxf(0.0, 1.0 - _at / 0.9)
				model.set_flip(_flip_u)
			if _at >= 0.9:
				_anim = ""
	# hand-held miniature drift (tiny)
	rig.camera.h_offset = sin(_t * 0.37) * 0.004
	rig.camera.v_offset = sin(_t * 0.29 + 1.3) * 0.003


func release() -> void:
	if vp:
		vp.render_target_update_mode = SubViewport.UPDATE_DISABLED
