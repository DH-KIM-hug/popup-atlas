class_name BookModel
extends Node3D
## One closed hardcover picture book (the cover of a tale), built from script.json `ui.cover`; used by CoverBook (the
## tale's cover / ending) and the bookshelf table (Shelf). Origin: the centre of the book's footprint on the table.
##  - back board with the back-cover epilogue art and a cut-paper "끝" on its underside (seen after turn_over),
##  - page block (page lines on head / tail / fore-edge), a cream title page with the title + a paper-cut spot vignette,
##  - rounded cloth spine, front board on `hinge` (key art, raised cut-paper title, cloth corners, "팝업 동화"),
##    a printed endpaper inside.
## set_open(deg) swings the front board about the spine; set_flip(u) turns the whole book over (0 face up .. 1 back up).

const SHADER := preload("res://story/cover_book.gdshader")
const FONT_PATH := "res://story/fonts/PretendardVariable.woff2"
const W := 1.5  ## spine -> fore-edge; depth D comes from the art's aspect
const T := 0.085
const BOARD := 0.012
const OVERHANG := 0.018
const LIFT := 0.006  ## everything sits this far above the table (the back-cover art lies under the back board)

var cfg: Dictionary = {}
var title_text := ""
var D := 1.0
var hinge: Node3D
var flip: Node3D  ## turn-over pivot at the book's mid thickness
var content: Node3D


func build(c: Dictionary, title: String) -> void:
	cfg = c
	title_text = title
	var art := tex(str(cfg.get("art", "")))
	if art:
		D = W * float(art.get_height()) / float(art.get_width())
	else:
		D = W * 0.72
	flip = Node3D.new()
	flip.name = "Flip"
	flip.position = Vector3(0, LIFT + T * 0.5, 0)
	add_child(flip)
	content = Node3D.new()
	content.position = Vector3(0, -T * 0.5, 0)
	flip.add_child(content)
	_build(art)


static func tex(p: String) -> Texture2D:
	if p == "" or not ResourceLoader.exists(p):
		return null
	return load(p) as Texture2D


func _col(key: String, def: String) -> Color:
	return Color(str(cfg.get(key, def)))


func mat(mode: int, tint := Color.WHITE, t: Texture2D = null) -> ShaderMaterial:
	var m := ShaderMaterial.new()
	m.shader = SHADER
	m.set_shader_parameter("mode", mode)
	m.set_shader_parameter("tint", tint)
	if t:
		m.set_shader_parameter("tex", t)
	return m


static func mesh(parent: Node3D, m: Mesh, material: Material, pos: Vector3, rot := Vector3.ZERO) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	mi.mesh = m
	mi.material_override = material
	mi.position = pos
	mi.rotation_degrees = rot
	parent.add_child(mi)
	return mi


static func plane(w: float, d: float) -> PlaneMesh:
	var p := PlaneMesh.new()
	p.size = Vector2(w, d)
	return p


static func quad(w: float, h: float) -> QuadMesh:
	var q := QuadMesh.new()
	q.size = Vector2(w, h)
	return q


static func box(x: float, y: float, z: float) -> BoxMesh:
	var b := BoxMesh.new()
	b.size = Vector3(x, y, z)
	return b


## The title page's centre in book space (where the camera looks down when the book is open).
func page_centre() -> Vector3:
	var pw := W - OVERHANG - 0.03
	return Vector3(-W * 0.5 + 0.03 + pw * 0.5, LIFT + T, 0.0)


func page_size() -> Vector2:
	return Vector2(W - OVERHANG - 0.03, D - OVERHANG * 2.0)


func _build(art: Texture2D) -> void:
	var cloth := _col("cloth", "3d3566")
	var cloth_dark := _col("cloth_dark", "2a2348")
	var page := _col("page", "f2e7cf")
	var x0 := -W * 0.5  # spine side
	# back board; its underside carries the back cover (the plane is turned about z so it reads upright after the flip)
	mesh(content, box(W, BOARD, D), mat(4, cloth_dark), Vector3(0, BOARD * 0.5, 0))
	var back_art := tex(str(cfg.get("back", "")))
	mesh(content, plane(W - 0.006, D - 0.006), mat(0, Color.WHITE, back_art) if back_art else mat(4, cloth),
		Vector3(0, -0.0012, 0), Vector3(0, 0, 180))
	var etex := tex(str(cfg.get("end_title", "")))
	if etex:
		var er: Array = cfg.get("end_rect", [0.5, 0.12, 0.3])
		decal(content, etex, float(er[2]) * W, Vector3(-(float(er[0]) - 0.5) * W, -0.0042, (float(er[1]) - 0.5) * D),
			Vector3(0, 0, 180))
	elif back_art == null:
		label(content, "끝", 0.3, Color("f3e2bd"), Vector3(0, -0.0024, -D * 0.2), Vector3(90, 0, 180))
	# page block
	var pw := W - OVERHANG - 0.03
	var pd := D - OVERHANG * 2.0
	var ph := T - BOARD * 2.0
	var py := BOARD + ph * 0.5
	var pcx := x0 + 0.03 + pw * 0.5
	var edge := mat(1, page.darkened(0.04))
	edge.set_shader_parameter("lines", 64.0)
	mesh(content, quad(pd, ph), edge, Vector3(pcx + pw * 0.5, py, 0), Vector3(0, 90, 0))
	mesh(content, quad(pw, ph), edge, Vector3(pcx, py, pd * 0.5))
	mesh(content, quad(pw, ph), edge, Vector3(pcx, py, -pd * 0.5), Vector3(0, 180, 0))
	# title page: the title, a small paper-cut spot vignette under it, the series mark
	var top := Node3D.new()
	top.position = Vector3(pcx, py + ph * 0.5, 0)
	content.add_child(top)
	mesh(top, plane(pw, pd), mat(4, page), Vector3.ZERO)
	var ttex := tex(str(cfg.get("title", "")))
	var spot := tex(str(cfg.get("spot", "")))
	# the open-book shot shows the middle ~64 % of the page height: title, vignette and mark all sit inside it
	var title_z := -pd * (0.15 if spot else 0.08)
	if ttex:
		var tw := pw * (0.52 if spot else 0.62)
		tw = minf(tw, pd * 0.16 * float(ttex.get_width()) / float(ttex.get_height())) if spot else tw
		decal(top, ttex, tw, Vector3(0, 0.0015, title_z))
	else:
		label(top, title_text, 0.14, Color("3b2a1c"), Vector3(0, 0.0015, title_z))
	if spot:
		var sw := minf(pw * 0.36, pd * 0.24 * float(spot.get_width()) / float(spot.get_height()))
		decal(top, spot, sw, Vector3(0, 0.0016, pd * 0.12))
	label(top, "팝업 동화", 0.05, Color(0.42, 0.3, 0.2, 0.8), Vector3(0, 0.0015, pd * (0.28 if spot else 0.4)))
	# rounded cloth spine
	var sp := CylinderMesh.new()
	sp.top_radius = T * 0.5 + 0.004
	sp.bottom_radius = sp.top_radius
	sp.height = D
	sp.radial_segments = 24
	mesh(content, sp, mat(4, cloth_dark), Vector3(x0 + 0.012, T * 0.5, 0), Vector3(90, 0, 0))
	# front board on its hinge
	hinge = Node3D.new()
	hinge.name = "Hinge"
	hinge.position = Vector3(x0, T - BOARD, 0)
	content.add_child(hinge)
	var board := Node3D.new()
	board.position = Vector3(W * 0.5, 0, 0)
	hinge.add_child(board)
	mesh(board, box(W, BOARD, D), mat(4, cloth_dark), Vector3(0, BOARD * 0.5, 0))
	var art_tex := tex(str(cfg.get("art", "")))
	mesh(board, plane(W - 0.006, D - 0.006), mat(0, Color.WHITE, art_tex) if art_tex else mat(4, cloth),
		Vector3(0, BOARD + 0.0012, 0))
	var endp := mat(2, _col("endpaper", "4b3a7a"))
	endp.set_shader_parameter("tint2", _col("endpaper_motif", "f2c14e"))
	endp.set_shader_parameter("motif", 7.0)
	mesh(board, plane(W - 0.01, D - 0.01), endp, Vector3(0, -0.0012, 0), Vector3(180, 0, 0))
	var cm := mat(4, cloth)
	mesh(board, _corner(0.16), cm, Vector3(W * 0.5, BOARD + 0.0024, -D * 0.5))
	mesh(board, _corner(0.16), cm, Vector3(W * 0.5, BOARD + 0.0024, D * 0.5), Vector3(0, -90, 0))
	mesh(board, plane(0.11, D), cm, Vector3(-W * 0.5 + 0.055, BOARD + 0.0024, 0))
	mesh(board, plane(0.006, D), mat(4, cloth_dark.darkened(0.3)), Vector3(-W * 0.5 + 0.112, BOARD + 0.0026, 0))
	if ttex:
		var r: Array = cfg.get("title_rect", [0.5, 0.2, 0.84])
		decal(board, ttex, float(r[2]) * W, Vector3((float(r[0]) - 0.5) * W, BOARD + 0.014, (float(r[1]) - 0.5) * D))
	else:
		label(board, title_text, 0.2, Color("fff3d6"), Vector3(0, BOARD + 0.003, -D * 0.3))
	var mk: Array = cfg.get("mark", [0.5, 0.955])
	if mk.size() == 2:
		label(board, "팝업 동화", 0.045, Color(1.0, 0.95, 0.84, 0.82),
			Vector3((float(mk[0]) - 0.5) * W, BOARD + 0.003, (float(mk[1]) - 0.5) * D))


## A right-triangle cloth corner lying flat, right angle at the origin, legs along -x and +z.
static func _corner(s: float) -> ArrayMesh:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	st.set_normal(Vector3.UP)
	for v in [Vector3(0, 0, 0), Vector3(0, 0, s), Vector3(-s, 0, 0)]:  # clockwise from above = faces up
		st.set_uv(Vector2(v.x, v.z))
		st.add_vertex(v)
	return st.commit()


static func decal(parent: Node3D, t: Texture2D, w: float, pos: Vector3, rot := Vector3.ZERO) -> MeshInstance3D:
	var h := w * float(t.get_height()) / float(t.get_width())
	var m := StandardMaterial3D.new()
	m.albedo_texture = t
	m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
	m.alpha_scissor_threshold = 0.5
	m.roughness = 0.9
	m.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS_ANISOTROPIC
	return mesh(parent, plane(w, h), m, pos, rot)


static func label(parent: Node3D, text: String, px_h: float, col: Color, pos: Vector3, rot := Vector3(-90, 0, 0)) -> void:
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
	l.rotation_degrees = rot
	parent.add_child(l)


func set_open(deg: float) -> void:
	if hinge:
		hinge.rotation_degrees = Vector3(0, 0, deg)


## Turn the book over about its long (depth) axis: 0 = front up, 1 = back up; a small lift arc in between.
func set_flip(u: float) -> void:
	if flip == null:
		return
	var e := u * u * (3.0 - 2.0 * u)
	flip.rotation_degrees = Vector3(0, 0, 180.0 * e)
	flip.position = Vector3(0, LIFT + T * 0.5 + 0.32 * sin(PI * e), 0)
