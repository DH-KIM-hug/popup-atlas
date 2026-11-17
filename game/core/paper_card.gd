@tool
class_name PaperCard
extends MeshInstance3D
## A cut-paper card: the opaque outline of `texture` extruded to `thickness`.
## Origin = bottom centre of the cut shape (the hinge line), card stands in local XY facing +Z.
## Front shows the print, back shows plain stock (or the mirrored print when `back_print`),
## side walls show the cream paper core. Meshes are cached per (texture, params).

const PRINT_SHADER := preload("res://core/shaders/paper_print.gdshader")
const EDGE_SHADER := preload("res://core/shaders/paper_edge.gdshader")
const FIBRE := preload("res://art/tex/paper_fibre.jpg")

static var _mesh_cache := {}
static var _mat_cache := {}

@export var texture: Texture2D:
	set(v):
		texture = v
		_queue_rebuild()
@export var height := 0.4:  ## world height of the cut shape
	set(v):
		height = v
		_queue_rebuild()
@export var thickness := 0.012:
	set(v):
		thickness = v
		_queue_rebuild()
@export var back_print := false:
	set(v):
		back_print = v
		_queue_rebuild()
@export var edge_color := Color(0.96, 0.92, 0.82):
	set(v):
		edge_color = v
		_queue_rebuild()
@export_range(0.5, 6.0) var contour_epsilon := 1.6  ## px at contour resolution
## PE r1: paper-engineering cuts. slot: +1 notched from the top down to mid height (slot card A of a
## cross-slotted pair), -1 notched from the bottom up (card B), 0 none. half: -1 / +1 keeps only the left /
## right half of the print (one face of a V-fold, crease on the local Y axis), 0 the whole card.
@export var slot := 0
@export var half := 0
## PE r1: cut edge coloured from the print (slotted pairs: no pale seam), not the cream core.
@export var edge_from_print := false

var size_m := Vector2.ZERO  ## width, height of the cut shape in world units
var _pending := false


func _ready() -> void:
	_rebuild()


func _queue_rebuild() -> void:
	if not is_inside_tree() or _pending:
		return
	_pending = true
	_rebuild.call_deferred()


func _rebuild() -> void:
	_pending = false
	if texture == null:
		mesh = null
		return
	# PE r1: a printed back shares the front material, so front + back go in one surface (one draw less).
	var merge := back_print
	var key := "%s|%.4f|%.4f|%.2f|%s|%d|%d" % [texture.resource_path if texture.resource_path else str(texture.get_rid()), height, thickness, contour_epsilon, merge, slot, half]
	var entry: Dictionary = _mesh_cache.get(key, {})
	if entry.is_empty():
		entry = _build(texture, height, thickness, contour_epsilon, slot, half, merge)
		_mesh_cache[key] = entry
	mesh = entry.get("mesh")
	size_m = entry.get("size", Vector2.ZERO)
	if mesh == null:
		return
	var avg: Color = entry.get("avg", Color.WHITE)
	var mats := _materials(texture, back_print, edge_color, size_m, avg, edge_from_print)
	set_surface_override_material(0, mats[0])
	if merge:
		set_surface_override_material(1, mats[2])
	else:
		set_surface_override_material(1, mats[1])
		set_surface_override_material(2, mats[2])
	cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON


static func _materials(tex: Texture2D, back_print_: bool, edge: Color, size: Vector2, avg: Color, edge_print := false) -> Array:
	var key := "%s|%s|%s|%s" % [str(tex.get_rid()), back_print_, edge.to_html(), edge_print]
	if _mat_cache.has(key):
		return _mat_cache[key]
	var front := ShaderMaterial.new()
	front.shader = PRINT_SHADER
	front.set_shader_parameter("albedo_tex", tex)
	front.set_shader_parameter("fibre_tex", FIBRE)
	front.set_shader_parameter("card_size", size)
	var back := ShaderMaterial.new()
	back.shader = PRINT_SHADER
	back.set_shader_parameter("albedo_tex", tex)
	back.set_shader_parameter("fibre_tex", FIBRE)
	back.set_shader_parameter("card_size", size)
	back.set_shader_parameter("plain", not back_print_)
	# Plain back: the stock colour, a muted version of the print.
	back.set_shader_parameter("plain_color", avg.lerp(edge, 0.55).darkened(0.08))
	var side := ShaderMaterial.new()
	side.shader = EDGE_SHADER
	# INT r3: darker coloured core edge (r2: lerp 0.3). PE r1: slotted / folded cards take the print colour.
	side.set_shader_parameter("edge_color", avg.darkened(0.22) if edge_print else edge.lerp(avg, 0.42).darkened(0.1))
	side.set_shader_parameter("fibre_tex", FIBRE)
	var mats := [front, back, side]
	_mat_cache[key] = mats
	return mats


static func _source_image(tex: Texture2D) -> Image:
	var img := tex.get_image()
	if img == null:
		return null
	if img.is_compressed():
		img = img.duplicate()
		img.decompress()
	if img.get_format() != Image.FORMAT_RGBA8:
		img = img.duplicate()
		img.convert(Image.FORMAT_RGBA8)
	return img


static func _build(tex: Texture2D, h_m: float, thick: float, eps: float, slot_ := 0, half_ := 0, merge_back := false) -> Dictionary:
	var img := _source_image(tex)
	if img == null:
		push_warning("PaperCard: texture has no image data")
		return {}
	var full := Vector2(img.get_width(), img.get_height())
	# Contour at <= 320 px on the long side: enough for scissor-clean edges, cheap to triangulate.
	var cimg := img.duplicate() as Image
	var scale_c := minf(1.0, 320.0 / maxf(full.x, full.y))
	if scale_c < 1.0:
		cimg.resize(int(full.x * scale_c), int(full.y * scale_c), Image.INTERPOLATE_BILINEAR)
	var bm := BitMap.new()
	bm.create_from_image_alpha(cimg, 0.35)
	var polys := bm.opaque_to_polygons(Rect2i(Vector2i.ZERO, bm.get_size()), eps)
	if polys.is_empty():
		return {}
	# Bounds of the opaque shape (in full-res px).
	var mn := Vector2(INF, INF)
	var mx := Vector2(-INF, -INF)
	var keep: Array[PackedVector2Array] = []
	for p: PackedVector2Array in polys:
		if p.size() < 3 or absf(_area(p)) < 12.0:
			continue
		var q := PackedVector2Array()
		for v in p:
			var fv := v / scale_c
			q.append(fv)
			mn = mn.min(fv)
			mx = mx.max(fv)
		keep.append(q)
	if keep.is_empty():
		return {}
	var px_h := mx.y - mn.y
	var s := h_m / px_h
	var cx := (mn.x + mx.x) * 0.5
	var bottom := mx.y
	if slot_ != 0 or half_ != 0:
		keep = _cut(keep, mn, mx, cx, thick * 1.08 / s, slot_, half_)
		if keep.is_empty():
			return {}
	var to_local := func(v: Vector2) -> Vector2: return Vector2((v.x - cx) * s, (bottom - v.y) * s)

	var st_front := SurfaceTool.new()
	var st_back := SurfaceTool.new()
	var st_side := SurfaceTool.new()
	for st in [st_front, st_back, st_side]:
		st.begin(Mesh.PRIMITIVE_TRIANGLES)
	if merge_back:
		st_back = st_front
	var hz := thick * 0.5
	var edge_len_acc := 0.0
	for poly in keep:
		var cw := Geometry2D.is_polygon_clockwise(poly)
		var idx := Geometry2D.triangulate_polygon(poly)
		if idx.is_empty():
			idx = _robust_triangulate(poly)
			if idx.is_empty():
				continue
		for t in range(0, idx.size(), 3):
			var tri := [idx[t], idx[t + 1], idx[t + 2]]
			# Orient every triangle by its own signed area so the front always faces +Z.
			var sa := (poly[tri[1]] - poly[tri[0]]).cross(poly[tri[2]] - poly[tri[0]])
			var order_front := [tri[0], tri[2], tri[1]] if sa < 0.0 else tri
			for i in order_front:
				var v: Vector2 = poly[i]
				var l: Vector2 = to_local.call(v)
				st_front.set_normal(Vector3(0, 0, 1))
				st_front.set_uv(v / full)
				st_front.add_vertex(Vector3(l.x, l.y, hz))
			for i in [order_front[0], order_front[2], order_front[1]]:
				var v: Vector2 = poly[i]
				var l: Vector2 = to_local.call(v)
				st_back.set_normal(Vector3(0, 0, -1))
				st_back.set_uv(Vector2(1.0 - v.x / full.x, v.y / full.y))
				st_back.add_vertex(Vector3(l.x, l.y, -hz))
		# Side walls.
		var n := poly.size()
		for i in n:
			var a: Vector2 = to_local.call(poly[i])
			var b: Vector2 = to_local.call(poly[(i + 1) % n])
			var d := b - a
			if d.length_squared() < 1e-10:
				continue
			var nrm := Vector2(d.y, -d.x).normalized()
			if cw:
				nrm = -nrm
			var n3 := Vector3(nrm.x, nrm.y, 0)
			var u0 := edge_len_acc
			var u1 := edge_len_acc + d.length()
			edge_len_acc = u1
			var quad := [
				[Vector3(a.x, a.y, hz), Vector2(u0, 0)], [Vector3(b.x, b.y, hz), Vector2(u1, 0)],
				[Vector3(b.x, b.y, -hz), Vector2(u1, 1)], [Vector3(a.x, a.y, -hz), Vector2(u0, 1)],
			]
			var order := [0, 2, 1, 0, 3, 2] if cw else [0, 1, 2, 0, 2, 3]
			for k in order:
				st_side.set_normal(n3)
				st_side.set_uv(quad[k][1])
				st_side.add_vertex(quad[k][0])
	var mesh := ArrayMesh.new()
	for st in ([st_front, st_side] if merge_back else [st_front, st_back, st_side]):
		st.generate_tangents()
		st.commit(mesh)
	return {"mesh": mesh, "size": Vector2((mx.x - mn.x) * s, h_m), "avg": _average(img)}


## PE r1: cut a half-slot (width sw px at x = cx) or keep one half of the outline (V-fold faces).
static func _cut(polys: Array[PackedVector2Array], mn: Vector2, mx: Vector2, cx: float, sw: float, slot_: int, half_: int) -> Array[PackedVector2Array]:
	var big := (mx - mn).length() + 20.0
	var cuts: Array[PackedVector2Array] = []
	var my := (mn.y + mx.y) * 0.5
	if half_ != 0:
		var x0 := cx if half_ < 0 else cx - big
		cuts.append(PackedVector2Array([Vector2(x0, mn.y - 10), Vector2(x0 + big, mn.y - 10), Vector2(x0 + big, mx.y + 10), Vector2(x0, mx.y + 10)]))
	if slot_ != 0:
		var y0 := mn.y - 10.0 if slot_ > 0 else my
		var y1 := my if slot_ > 0 else mx.y + 10.0
		cuts.append(PackedVector2Array([Vector2(cx - sw * 0.5, y0), Vector2(cx + sw * 0.5, y0), Vector2(cx + sw * 0.5, y1), Vector2(cx - sw * 0.5, y1)]))
	var cur := polys
	for c in cuts:
		var nxt: Array[PackedVector2Array] = []
		for p in cur:
			var res := Geometry2D.clip_polygons(p, c)
			if res.is_empty():
				continue
			# Boolean results come back with their own winding: outlines share the largest piece's winding,
			# holes have the other one.
			var top: PackedVector2Array = res[0]
			for q: PackedVector2Array in res:
				if absf(_area(q)) > absf(_area(top)):
					top = q
			var cw := Geometry2D.is_polygon_clockwise(top)
			for q: PackedVector2Array in res:
				if q.size() >= 3 and Geometry2D.is_polygon_clockwise(q) == cw and absf(_area(q)) > 6.0:
					nxt.append(q)
		cur = nxt
	return cur


static var _base_cache := {}


## PE r1: where the print meets its hinge line, for glue feet. Returns {x0, x1} (per unit card height,
## relative to the hinge centre) and {col}: the average colour of the bottom band of the print.
static func base_info(tex: Texture2D) -> Dictionary:
	var key := tex.resource_path if tex.resource_path else str(tex.get_rid())
	if _base_cache.has(key):
		return _base_cache[key]
	var out := {"x0": -0.1, "x1": 0.1, "col": Color(0.5, 0.55, 0.4)}
	var img := _source_image(tex)
	if img != null:
		var sc := minf(1.0, 72.0 / maxf(img.get_width(), img.get_height()))
		if sc < 1.0:
			img.resize(maxi(4, int(img.get_width() * sc)), maxi(4, int(img.get_height() * sc)), Image.INTERPOLATE_BILINEAR)
		var w := img.get_width()
		var h := img.get_height()
		var mn := Vector2i(w, h)
		var mx := Vector2i(-1, -1)
		for y in h:
			for x in w:
				if img.get_pixel(x, y).a > 0.35:
					mn = mn.min(Vector2i(x, y))
					mx = mx.max(Vector2i(x, y))
		if mx.x >= 0:
			var ph := float(mx.y - mn.y + 1)
			var cx := (mn.x + mx.x + 1) * 0.5
			var band := maxi(1, int(ph * 0.05))
			var bx0 := w
			var bx1 := -1
			for y in range(mx.y - band + 1, mx.y + 1):
				for x in w:
					if img.get_pixel(x, y).a > 0.35:
						bx0 = mini(bx0, x)
						bx1 = maxi(bx1, x)
			var acc := Color(0, 0, 0, 0)
			var n := 0.0
			# bottom third of the print, skipping cream / white paper (rims, paper strips in the art)
			for y in range(maxi(mn.y, mx.y - int(ph * 0.33)), mx.y + 1):
				for x in range(mn.x, mx.x + 1):
					var c := img.get_pixel(x, y)
					if c.a > 0.5 and not (c.v > 0.78 and c.s < 0.32):
						acc += c
						n += 1.0
			if bx1 >= 0:
				out["x0"] = (bx0 - cx) / ph
				out["x1"] = (bx1 + 1 - cx) / ph
			if n > 0.0:
				out["col"] = Color(acc.r / n, acc.g / n, acc.b / n)
	_base_cache[key] = out
	return out


## Contours from BitMap can touch themselves, which triangulate_polygon rejects.
## Delaunay over the vertices, keeping triangles whose centroid lies inside the outline.
static func _robust_triangulate(poly: PackedVector2Array) -> PackedInt32Array:
	var tri := Geometry2D.triangulate_delaunay(poly)
	var out := PackedInt32Array()
	for t in range(0, tri.size(), 3):
		var c := (poly[tri[t]] + poly[tri[t + 1]] + poly[tri[t + 2]]) / 3.0
		if Geometry2D.is_point_in_polygon(c, poly):
			out.append_array([tri[t], tri[t + 1], tri[t + 2]])
	return out


static func _area(p: PackedVector2Array) -> float:
	var a := 0.0
	for i in p.size():
		var j := (i + 1) % p.size()
		a += p[i].x * p[j].y - p[j].x * p[i].y
	return a * 0.5


static func _average(img: Image) -> Color:
	var small := img.duplicate() as Image
	small.resize(16, 16, Image.INTERPOLATE_BILINEAR)
	var acc := Color(0, 0, 0, 0)
	var n := 0.0
	for y in 16:
		for x in 16:
			var c := small.get_pixel(x, y)
			if c.a > 0.5:
				acc += c
				n += 1.0
	return Color(acc.r / n, acc.g / n, acc.b / n, 1.0) if n > 0.0 else Color(0.9, 0.86, 0.78)
