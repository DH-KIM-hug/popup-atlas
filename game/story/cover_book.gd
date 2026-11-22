class_name CoverBook
extends TextureRect
## The tale's front cover as a real hardcover picture book (2026-11-22, user: "책 표지 디자인 제대로 하자").
## A 3D book (boards, rounded cloth spine, page block with fore-edge lines, cloth corners, the tale's key art on the
## front board, the cut-paper title raised on it as its own layer, a quiet "팝업 동화" mark) lies on a warm wooden table
## under the tales' look (LookRig: warm low raking key, cool fill, DOF, tilt-shift grade, grain), rendered in its own
## SubViewport/World3D and shown full screen behind the UI caption.
##
## Idle: every few seconds the front board's fore-edge lifts a little (a thumb at the corner) = "open me".
## open(): the board swings over the spine onto the table (hand-eased, a small slap), the camera rises and pushes into
## the title page until it fills the screen; then StoryRunner turns that page (PageTurn) onto the first pop-up spread.
## close(): the same book shown open on the title page, the camera pulls back and the board swings shut (end card).
##
## Config (script.json ui.cover, all optional; defaults give a plain cloth book):
##   art: res path of the key art (its aspect sets the book's shape), title: res path of the cut-paper title decal,
##   title_rect: [cx, cy, width] in cover UV (0..1, y down), cloth / cloth_dark / endpaper / endpaper_motif / page:
##   hex colours, light: "day" | "night" (lamp-lit table), mark: [cx, cy] of the series mark in cover UV ([] = none).

signal opened

const SHADER := preload("res://story/cover_book.gdshader")
const FONT_PATH := "res://story/fonts/PretendardVariable.woff2"
const W := 1.5  ## book width (spine -> fore-edge); depth comes from the art's aspect
const T := 0.085  ## closed thickness
const BOARD := 0.012
const OVERHANG := 0.018
const SHOT_CLOSED := {"el": 57.0, "yaw": 8.0, "dist": 5.8, "fov": 22.0, "at": Vector3(0.06, 0.0, 0.25)}

var cfg: Dictionary = {}
var title_text := ""
var D := 1.0  ## book depth (cover height on the art)
var vp: SubViewport
var rig: LookRig
var book: Node3D
var hinge: Node3D  ## front board pivot on the spine
var _t := 0.0
var _anim := ""  ## "" idle | open | close | done
var _at := 0.0
var _peek_t := 1.6
var _shot_a: Dictionary
var _shot_b: Dictionary
var _hinge_angle := 0.0
var tilt := 0.0  ## "stand" pose: the book leans back on a little easel, tilted this many degrees up from the table


func _init() -> void:
	expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	stretch_mode = TextureRect.STRETCH_SCALE
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	set_anchors_preset(Control.PRESET_FULL_RECT)


func build(c: Dictionary, title: String) -> void:
	cfg = c.duplicate()
	for a in OS.get_cmdline_user_args():  # look test: --cover-pose=stand
		if a.begins_with("--cover-pose="):
			cfg["pose"] = a.get_slice("=", 1)
	title_text = title
	if str(cfg.get("pose", "flat")) == "stand":
		tilt = 74.0
	var art := _tex(str(cfg.get("art", "")))
	if art:
		D = W * float(art.get_height()) / float(art.get_width())
	vp = SubViewport.new()
	vp.name = "CoverVP"
	vp.own_world_3d = true
	vp.msaa_3d = Viewport.MSAA_4X
	vp.size = _vp_size()
	vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	add_child(vp)
	texture = vp.get_texture()
	var night := str(cfg.get("light", "day")) == "night"
	rig = LookRig.new()
	rig.name = "Rig"
	rig.follow_smooth = 0.0
	rig.focus_height = 0.0
	rig.dof_near_margin = 1.0
	rig.dof_far_margin = 0.7
	rig.dof_near_transition = 1.4
	rig.dof_far_transition = 2.4
	rig.dof_amount = 0.1
	rig.tilt_blur = 0.55
	rig.tilt_focus_y = 0.44
	rig.tilt_band_half = 0.3
	rig.tilt_band_soft = 0.3
	rig.tilt_top_bias = 1.0
	rig.lens_soft = 0.05
	rig.grain = 0.03
	rig.toe = 0.25
	rig.post_contrast = 1.06
	rig.post_saturation = 0.94
	rig.vignette = 0.34
	rig.haze_enabled = false
	rig.key_elevation_deg = 38.0
	rig.key_yaw_deg = -48.0
	rig.key_color = Color("ffd2a0") if night else Color("ffdcb4")
	rig.key_energy = 2.4 if night else 2.6
	rig.shadow_opacity = 0.78
	rig.shadow_softness = 2.4
	rig.shadow_distance = 9.0
	rig.fill_color = Color("7f8fc4") if night else Color("a7b6d8")
	rig.fill_energy = 0.3 if night else 0.38
	rig.ambient_color = Color("8a6a58") if night else Color("b59c80")
	rig.ambient_energy = 0.42 if night else 0.5
	rig.exposure = 0.96
	rig.background = Color("24160d")
	vp.add_child(rig)
	_build_scene(art)
	_apply_shot(_shot_closed())
	rig.snap()


func _vp_size() -> Vector2i:
	var s := Vector2i(get_tree().root.size) if is_inside_tree() else Vector2i(1366, 1024)
	return Vector2i(maxi(s.x, 640), maxi(s.y, 480))


func _ready() -> void:
	if vp:
		vp.size = _vp_size()


func _tex(p: String) -> Texture2D:
	if p == "" or not ResourceLoader.exists(p):
		return null
	return load(p) as Texture2D


func _col(key: String, def: String) -> Color:
	return Color(str(cfg.get(key, def)))


func _mat(mode: int, tint := Color.WHITE, tex: Texture2D = null) -> ShaderMaterial:
	var m := ShaderMaterial.new()
	m.shader = SHADER
	m.set_shader_parameter("mode", mode)
	m.set_shader_parameter("tint", tint)
	if tex:
		m.set_shader_parameter("tex", tex)
	return m


func _mesh(parent: Node3D, mesh: Mesh, mat: Material, pos: Vector3, rot := Vector3.ZERO) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	mi.mesh = mesh
	mi.material_override = mat
	mi.position = pos
	mi.rotation_degrees = rot
	parent.add_child(mi)
	return mi


func _plane(w: float, d: float) -> PlaneMesh:
	var p := PlaneMesh.new()
	p.size = Vector2(w, d)
	return p


func _quad(w: float, h: float) -> QuadMesh:
	var q := QuadMesh.new()
	q.size = Vector2(w, h)
	return q


func _build_scene(art: Texture2D) -> void:
	var cloth := _col("cloth", "3d3566")
	var cloth_dark := _col("cloth_dark", "2a2348")
	var page := _col("page", "f2e7cf")
	# table
	var table := _mat(3, Color("7a5234"))
	table.set_shader_parameter("tint2", Color("553522"))
	var root := Node3D.new()
	root.name = "Scene"
	vp.add_child(root)
	_mesh(root, _plane(16.0, 16.0), table, Vector3(0, 0, 0), Vector3(0, 23, 0))
	if str(cfg.get("light", "day")) == "night":
		var lamp := OmniLight3D.new()
		lamp.light_color = Color("ffb870")
		lamp.light_energy = 1.4
		lamp.omni_range = 5.0
		lamp.omni_attenuation = 1.6
		lamp.position = Vector3(-2.4, 1.6, -1.2)
		lamp.shadow_enabled = false
		root.add_child(lamp)
	# soft contact / ambient-occlusion pad under the book (the key's shadow does the direction)
	var ao := ShaderMaterial.new()
	var sh := Shader.new()
	sh.code = "shader_type spatial;\nrender_mode unshaded, blend_mul, depth_draw_never, cull_disabled;\nuniform vec2 half_size;\n" + \
		"void fragment(){ vec2 p = (UV - 0.5) * 2.0; vec2 q = abs(p) - vec2(1.0 - 0.18 / half_size.x, 1.0 - 0.18 / half_size.y);\n" + \
		"float d = length(max(q, 0.0)) * min(half_size.x, half_size.y); float k = 1.0 - exp(-d * 14.0);\n" + \
		"ALBEDO = mix(vec3(0.62, 0.54, 0.48), vec3(1.0), k); }"
	ao.shader = sh
	ao.set_shader_parameter("half_size", Vector2(W * 0.5 + 0.2, D * 0.5 + 0.2))
	if tilt <= 0.0 and cfg.get("contact_pad", false):
		_mesh(root, _plane(W + 0.4, D + 0.4), ao, Vector3(0.02, 0.002, 0.03))

	book = Node3D.new()
	book.name = "Book"
	if tilt > 0.0:
		# standing: the near (bottom) edge rests in an easel's lip, the book leans back; the tale's own picture hangs
		# far behind, thrown out of focus (its world, softly)
		var stand := Node3D.new()
		stand.name = "Stand"
		stand.position = Vector3(0, 0.03, D * 0.5)
		stand.rotation_degrees = Vector3(tilt, 0, 0)
		root.add_child(stand)
		book.position = Vector3(0, 0, -D * 0.5)
		stand.add_child(book)
		var wood := _mat(4, Color("6e4a2e"))
		_mesh(root, _box(W + 0.3, 0.06, 0.16), wood, Vector3(0, 0.03, D * 0.5 + 0.08))
		_mesh(root, _box(W + 0.3, 0.1, 0.03), wood, Vector3(0, 0.08, D * 0.5 + 0.15))
		if art:
			# only the art's sky, roofs and lit windows (the characters' faces would loom as giants behind the book)
			var bd := _mat(0, Color(0.5, 0.46, 0.52), art)
			bd.set_shader_parameter("uv_rect", Vector4(0.0, 0.1, 1.0, 0.42))
			var bw := 16.0
			var bh := bw * D * 0.42 / W
			_mesh(root, _quad(bw, bh), bd, Vector3(0.0, bh * 0.5 - 0.6, -7.5))
		book.rotation_degrees = Vector3.ZERO
	else:
		root.add_child(book)
	var x0 := -W * 0.5  # spine side
	# back board
	_mesh(book, _box(W, BOARD, D), _mat(4, cloth_dark), Vector3(0, BOARD * 0.5 + 0.003, 0))
	# page block (inset from the boards' overhang), its fore-edge / head / tail with page lines
	var pw := W - OVERHANG - 0.03
	var pd := D - OVERHANG * 2.0
	var ph := T - BOARD * 2.0
	var py := BOARD + 0.003 + ph * 0.5
	var pcx := x0 + 0.03 + pw * 0.5
	var edge := _mat(1, page.darkened(0.04))
	edge.set_shader_parameter("lines", 64.0)
	_mesh(book, _quad(pd, ph), edge, Vector3(pcx + pw * 0.5, py, 0), Vector3(0, 90, 0))
	_mesh(book, _quad(pw, ph), edge, Vector3(pcx, py, pd * 0.5))
	_mesh(book, _quad(pw, ph), edge, Vector3(pcx, py, -pd * 0.5), Vector3(0, 180, 0))
	# title page on top of the block: cream paper, the title decal small, the series mark
	var top := Node3D.new()
	top.position = Vector3(pcx, py + ph * 0.5, 0)
	book.add_child(top)
	_mesh(top, _plane(pw, pd), _mat(4, page), Vector3.ZERO)
	var ttex := _tex(str(cfg.get("title", "")))
	if ttex:
		var tw := pw * 0.62
		_decal(top, ttex, tw, Vector3(0, 0.0015, -pd * 0.08))
	else:
		_label(top, title_text, 0.14, Color("3b2a1c"), Vector3(0, 0.0015, -pd * 0.08))
	_label(top, "팝업 동화", 0.05, Color(0.42, 0.3, 0.2, 0.8), Vector3(0, 0.0015, pd * 0.3))
	# rounded cloth spine
	var sp := CylinderMesh.new()
	sp.top_radius = T * 0.5 + 0.004
	sp.bottom_radius = sp.top_radius
	sp.height = D
	sp.radial_segments = 24
	_mesh(book, sp, _mat(4, cloth_dark), Vector3(x0 + 0.012, T * 0.5 + 0.003, 0), Vector3(90, 0, 0))
	# front board on its hinge
	hinge = Node3D.new()
	hinge.name = "Hinge"
	hinge.position = Vector3(x0, T - BOARD + 0.003, 0)
	book.add_child(hinge)
	var board := Node3D.new()
	board.position = Vector3(W * 0.5, 0, 0)
	hinge.add_child(board)
	_mesh(board, _box(W, BOARD, D), _mat(4, cloth_dark), Vector3(0, BOARD * 0.5, 0))
	var front := _mat(0, Color.WHITE, art) if art else _mat(4, cloth)
	_mesh(board, _plane(W - 0.006, D - 0.006), front, Vector3(0, BOARD + 0.0012, 0))
	var endp := _mat(2, _col("endpaper", "4b3a7a"))
	endp.set_shader_parameter("tint2", _col("endpaper_motif", "f2c14e"))
	endp.set_shader_parameter("motif", 7.0)
	_mesh(board, _plane(W - 0.01, D - 0.01), endp, Vector3(0, -0.0012, 0), Vector3(180, 0, 0))
	# cloth corners at the fore-edge (library-bound look) + a cloth strip along the spine side
	var cm := _mat(4, cloth)
	_mesh(board, _corner(0.16), cm, Vector3(W * 0.5, BOARD + 0.0024, -D * 0.5))
	_mesh(board, _corner(0.16), cm, Vector3(W * 0.5, BOARD + 0.0024, D * 0.5), Vector3(0, 90, 0))
	_mesh(board, _plane(0.11, D), cm, Vector3(-W * 0.5 + 0.055, BOARD + 0.0024, 0))
	_mesh(board, _plane(0.006, D), _mat(4, cloth_dark.darkened(0.3)), Vector3(-W * 0.5 + 0.112, BOARD + 0.0026, 0))
	# the cut-paper title, raised as its own layer (it casts a small shadow on the art under the raking key)
	if ttex:
		var r: Array = cfg.get("title_rect", [0.5, 0.2, 0.84])
		var cx := (float(r[0]) - 0.5) * W
		var cz := (float(r[1]) - 0.5) * D
		_decal(board, ttex, float(r[2]) * W, Vector3(cx, BOARD + 0.014, cz))
	else:
		_label(board, title_text, 0.2, Color("fff3d6"), Vector3(0, BOARD + 0.003, -D * 0.3))
	var mk: Array = cfg.get("mark", [0.5, 0.955])
	if mk.size() == 2:
		_label(board, "팝업 동화", 0.045, Color(1.0, 0.95, 0.84, 0.82),
			Vector3((float(mk[0]) - 0.5) * W, BOARD + 0.003, (float(mk[1]) - 0.5) * D))


func _box(x: float, y: float, z: float) -> BoxMesh:
	var b := BoxMesh.new()
	b.size = Vector3(x, y, z)
	return b


## A right-triangle cloth corner lying flat, right angle at the origin, legs along -x and +z (rotated per corner).
func _corner(s: float) -> ArrayMesh:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	st.set_normal(Vector3.UP)
	for v in [Vector3(0, 0, 0), Vector3(-s, 0, 0), Vector3(0, 0, s)]:
		st.set_uv(Vector2(v.x, v.z))
		st.add_vertex(v)
	return st.commit()


func _decal(parent: Node3D, tex: Texture2D, w: float, pos: Vector3) -> void:
	var h := w * float(tex.get_height()) / float(tex.get_width())
	var m := StandardMaterial3D.new()
	m.albedo_texture = tex
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
	m.alpha_scissor_threshold = 0.5
	m.roughness = 0.9
	m.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
	_mesh(parent, _plane(w, h), m, pos)


func _label(parent: Node3D, text: String, px_h: float, col: Color, pos: Vector3) -> void:
	var l := Label3D.new()
	l.text = text
	l.font = load(FONT_PATH) if ResourceLoader.exists(FONT_PATH) else null
	l.font_size = 96
	l.pixel_size = px_h / 96.0
	l.modulate = col
	l.outline_size = 0
	l.shaded = true
	l.double_sided = false
	l.position = pos
	l.rotation_degrees = Vector3(-90, 0, 0)
	parent.add_child(l)


# ------------------------------------------------------------------ animation

func _apply_shot(s: Dictionary) -> void:
	rig.elevation_deg = float(s["el"])
	rig.yaw_deg = float(s["yaw"])
	rig.distance = float(s["dist"])
	rig.fov = float(s["fov"])
	rig.focus_point = s["at"]


func _shot_closed() -> Dictionary:
	if tilt <= 0.0:
		return SHOT_CLOSED.duplicate()
	var c := book.global_transform * Vector3(0.0, T, 0.0)
	return {"el": 12.0, "yaw": 10.0, "dist": 6.9, "fov": 22.0, "at": c + Vector3(0.03, -0.3, 0.0)}


func _shot_open() -> Dictionary:
	# straight down onto the title page, close enough that the page fills the frame (it then turns like any page)
	var pcx := -W * 0.5 + 0.03 + (W - OVERHANG - 0.03) * 0.5
	var pd := D - OVERHANG * 2.0
	var aspect := float(vp.size.x) / float(vp.size.y)
	var need_h := minf(pd * 0.94, (W - OVERHANG - 0.03) * 0.94 / aspect)  # the page overfills the frame
	var dist := need_h * 0.5 / tan(deg_to_rad(22.0 * 0.5))
	if tilt > 0.0:
		return {"el": 90.0 - tilt, "yaw": 0.0, "dist": dist, "fov": 22.0, "at": book.global_transform * Vector3(pcx, T, 0.0)}
	return {"el": 88.5, "yaw": 0.0, "dist": dist, "fov": 22.0, "at": Vector3(pcx, T, 0.0)}


func _lerp_shot(a: Dictionary, b: Dictionary, u: float) -> Dictionary:
	return {"el": lerpf(a["el"], b["el"], u), "yaw": lerpf(a["yaw"], b["yaw"], u), "dist": lerpf(a["dist"], b["dist"], u),
		"fov": lerpf(a["fov"], b["fov"], u), "at": (a["at"] as Vector3).lerp(b["at"], u)}


func _current_shot() -> Dictionary:
	return {"el": rig.elevation_deg, "yaw": rig.yaw_deg, "dist": rig.distance, "fov": rig.fov, "at": rig.focus_point}


## A closed book shown again as the cover (replay): glide back to the cover framing, then the idle peek resumes.
func idle() -> void:
	_anim = "recenter"
	_at = 0.0
	_shot_a = _current_shot()
	_shot_b = _shot_closed()


func open() -> void:
	_anim = "open"
	_at = 0.0
	_shot_a = _current_shot()
	_shot_b = _shot_open()


## Close the open book; `shift` slides the closed framing so the book sits left of centre (room for the end tag).
func close(shift := 0.0) -> void:
	_anim = "close"
	_at = 0.0
	_shot_a = _shot_open()
	_shot_b = _shot_closed()
	_shot_b["at"] = (_shot_b["at"] as Vector3) + Vector3(shift, 0, 0)


func is_closed() -> bool:
	return _anim == "" or _anim == "closed"


func is_animating() -> bool:
	return _anim == "open" or _anim == "close"


const OPEN_MAX := 177.0  ## the board lies on the table, sloping from the spine
const T_SWING := 1.25
const T_OPEN := 2.35


func _set_hinge(deg: float) -> void:
	_hinge_angle = deg
	if hinge:
		hinge.rotation_degrees = Vector3(0, 0, deg)


func _ease_swing(u: float) -> float:
	# a hand: slow lift, quicker sweep over the top, soft fall
	return u * u * (3.0 - 2.0 * u) * 0.75 + (1.0 - pow(1.0 - u, 3.0)) * 0.25


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
			_set_hinge(maxf(a, 0.0))
		"open":
			_at += dt
			var u := clampf(_at / T_SWING, 0.0, 1.0)
			var ang := OPEN_MAX * _ease_swing(u)
			if _at > T_SWING:  # the slap: a little bounce off the table
				var k2 := (_at - T_SWING) / 0.35
				ang = OPEN_MAX - 4.0 * sin(clampf(k2, 0.0, 1.0) * PI) * (1.0 - clampf(k2, 0.0, 1.0))
			_set_hinge(ang)
			var uc := clampf((_at - 0.35) / (T_OPEN - 0.35), 0.0, 1.0)
			uc = uc * uc * (3.0 - 2.0 * uc)
			_apply_shot(_lerp_shot(_shot_a, _shot_b, uc))
			if _at >= T_OPEN:
				_anim = "done"
				opened.emit()
		"recenter":
			_at += dt
			var ur := clampf(_at / 0.9, 0.0, 1.0)
			_apply_shot(_lerp_shot(_shot_a, _shot_b, ur * ur * (3.0 - 2.0 * ur)))
			if ur >= 1.0:
				_anim = ""
		"close":
			_at += dt
			var uc2 := clampf(_at / 1.2, 0.0, 1.0)
			uc2 = uc2 * uc2 * (3.0 - 2.0 * uc2)
			_apply_shot(_lerp_shot(_shot_a, _shot_b, uc2))
			var us := clampf((_at - 0.5) / T_SWING, 0.0, 1.0)
			_set_hinge(OPEN_MAX * (1.0 - _ease_swing(us)))
			if _at >= 0.5 + T_SWING + 0.2:
				_set_hinge(0.0)
				_anim = "closed"
	# hand-held miniature drift (tiny)
	rig.camera.h_offset = sin(_t * 0.37) * 0.004
	rig.camera.v_offset = sin(_t * 0.29 + 1.3) * 0.003


## Show the book open on its title page (for close()).
func set_open() -> void:
	_set_hinge(OPEN_MAX)
	_apply_shot(_shot_open())
	_anim = "done"


func release() -> void:
	if vp:
		vp.render_target_update_mode = SubViewport.UPDATE_DISABLED
