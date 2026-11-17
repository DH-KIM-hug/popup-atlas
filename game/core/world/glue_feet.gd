class_name GlueFeet
extends Node3D
## PE r1: the paper engineering under every standing card, in two draws for the whole spread.
##  - Foot: a strip of the card's own stock folded flat onto the page at its base (glued tab), in front of
##    the card, with a cream cut edge and a dark crease line where it bends up into the card.
##  - Strut: an easel tab behind a tall card, from ~40% of its height down to the page.
## Colours come from the bottom band of each print (PaperCard.base_info), so a foot reads as the same stock.
##   var gf := GlueFeet.new(); gf.add_foot(pos, yaw, x0, x1, thick, depth, col); gf.add_strut(...); add_child(gf); gf.commit()

const SHADER := preload("res://core/shaders/glue_foot.gdshader")
const FIBRE := preload("res://art/tex/paper_fibre.jpg")

var _feet: Array = []  ## [Transform3D, Color]
var _struts: Array = []


## Foot in front of a card standing at pos (yaw = card yaw), spanning local x0..x1 at the base.
func add_foot(pos: Vector3, yaw: float, x0: float, x1: float, thick: float, depth: float, col: Color, extra_yaw := 0.0) -> void:
	var w := maxf(x1 - x0, 0.025) + thick
	var xc := (x0 + x1) * 0.5
	var b := Basis(Vector3.UP, yaw) * Basis(Vector3.UP, extra_yaw)
	var o := pos + b * Vector3(xc, 0.0004, thick * 0.5)
	# a single ply of stock: thin, so the tab reads as paper on the page, not a plinth
	_feet.append([Transform3D(b * Basis.from_scale(Vector3(w, minf(thick * 0.35, 0.006), depth)), o), col])


## Easel strut behind a card of height h (attached at `at` * h, landing `reach` * h behind).
func add_strut(pos: Vector3, yaw: float, h: float, thick: float, col: Color, at := 0.42, reach := 0.24) -> void:
	var a := h * at
	var r := h * reach
	var L := sqrt(a * a + r * r)
	var ws := clampf(h * 0.07, 0.02, 0.06)
	var zdir := Vector3(0, a, r) / L
	var ydir := Vector3(0, r, -a) / L
	var local := Basis(Vector3(ws, 0, 0), ydir * thick * 0.8, zdir * L)
	var b := Basis(Vector3.UP, yaw)
	var o := pos + b * Vector3(0, 0, -thick * 0.5 - r)
	_struts.append([Transform3D(b * local, o), col])


func commit() -> void:
	var mesh := _box()
	var mat := ShaderMaterial.new()
	mat.shader = SHADER
	mat.set_shader_parameter("fibre_tex", FIBRE)
	for set in [[_feet, "Feet", false], [_struts, "Struts", true]]:
		var items: Array = set[0]
		if items.is_empty():
			continue
		var mm := MultiMesh.new()
		mm.transform_format = MultiMesh.TRANSFORM_3D
		mm.use_custom_data = true
		mm.mesh = mesh
		mm.instance_count = items.size()
		for i in items.size():
			mm.set_instance_transform(i, items[i][0])
			var c: Color = items[i][1]
			mm.set_instance_custom_data(i, Color(c.r, c.g, c.b, 0.7))
		var mi := MultiMeshInstance3D.new()
		mi.name = set[1]
		mi.multimesh = mm
		mi.material_override = mat
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if set[2] else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(mi)


## Unit tab: x -0.5..0.5, y 0..1 (thickness), z 0..1 (away from the crease). Top UV = (x, z); walls UV.x = 2.
static func _box() -> ArrayMesh:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var v := func(x: float, y: float, z: float) -> Vector3: return Vector3(x, y, z)
	# top
	_q(st, v.call(-0.5, 1, 0), v.call(0.5, 1, 0), v.call(0.5, 1, 1), v.call(-0.5, 1, 1), Vector3.UP,
		[Vector2(0, 0), Vector2(1, 0), Vector2(1, 1), Vector2(0, 1)])
	# walls: front (z=1), sides, back (z=0, hidden against the card)
	_q(st, v.call(-0.5, 0, 1), v.call(0.5, 0, 1), v.call(0.5, 1, 1), v.call(-0.5, 1, 1), Vector3.BACK,
		[Vector2(2, 0), Vector2(2, 1), Vector2(2, 1), Vector2(2, 0)])
	_q(st, v.call(0.5, 0, 0), v.call(0.5, 0, 1), v.call(0.5, 1, 1), v.call(0.5, 1, 0), Vector3.RIGHT,
		[Vector2(2, 0), Vector2(2, 1), Vector2(2, 1), Vector2(2, 0)])
	_q(st, v.call(-0.5, 0, 1), v.call(-0.5, 0, 0), v.call(-0.5, 1, 0), v.call(-0.5, 1, 1), Vector3.LEFT,
		[Vector2(2, 0), Vector2(2, 1), Vector2(2, 1), Vector2(2, 0)])
	_q(st, v.call(0.5, 0, 0), v.call(-0.5, 0, 0), v.call(-0.5, 1, 0), v.call(0.5, 1, 0), Vector3.FORWARD,
		[Vector2(2, 0), Vector2(2, 1), Vector2(2, 1), Vector2(2, 0)])
	# underside (struts are seen from below at grazing angles)
	_q(st, v.call(-0.5, 0, 1), v.call(0.5, 0, 1), v.call(0.5, 0, 0), v.call(-0.5, 0, 0), Vector3.DOWN,
		[Vector2(0, 1), Vector2(1, 1), Vector2(1, 0), Vector2(0, 0)])
	return st.commit()


static func _q(st: SurfaceTool, a: Vector3, b: Vector3, c: Vector3, d: Vector3, n: Vector3, uv: Array) -> void:
	var ps := [a, b, c, d]
	for tri in [[0, 1, 2], [0, 2, 3]]:
		var p0: Vector3 = ps[tri[0]]
		var order: Array = tri
		if (ps[tri[1]] - p0).cross(ps[tri[2]] - p0).dot(n) > 0.0:
			order = [tri[0], tri[2], tri[1]]
		for k in order:
			st.set_normal(n)
			st.set_uv(uv[k])
			st.add_vertex(ps[k])
