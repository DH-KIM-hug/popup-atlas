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
	var key := "%s|%.4f|%.4f|%.2f|%s" % [texture.resource_path if texture.resource_path else str(texture.get_rid()), height, thickness, contour_epsilon, back_print]
	var entry: Dictionary = _mesh_cache.get(key, {})
	if entry.is_empty():
		entry = _build(texture, height, thickness, contour_epsilon)
		_mesh_cache[key] = entry
	mesh = entry.get("mesh")
	size_m = entry.get("size", Vector2.ZERO)
	if mesh == null:
		return
	var mats := _materials(texture, back_print, edge_color, size_m, entry.get("avg", Color.WHITE))
	set_surface_override_material(0, mats[0])
	set_surface_override_material(1, mats[1])
	set_surface_override_material(2, mats[2])
	cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON


static func _materials(tex: Texture2D, back_print_: bool, edge: Color, size: Vector2, avg: Color) -> Array:
	var key := "%s|%s|%s" % [str(tex.get_rid()), back_print_, edge.to_html()]
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
	side.set_shader_parameter("edge_color", edge.lerp(avg, 0.42).darkened(0.1))  # INT r3: darker coloured core edge (r2: lerp 0.3)
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


## uber_idx >= 0 (perf, CardBatch): one indexed surface instead of three, UV2 = (part, uber_idx) with part 0 print face,
## 1 back, 2 cut walls; the entry also carries "quad" (local rect of the whole texture: x0, y_top, w, h) and "mask"
## (L8 image of the alpha bitmap the contour was traced from) for the batched shadow quads. Same vertices, same order.
static func _build(tex: Texture2D, h_m: float, thick: float, eps: float, uber_idx := -1) -> Dictionary:
	var c := _contour(tex, eps)
	if c.is_empty():
		return {}
	var full: Vector2 = c["full"]
	var mn: Vector2 = c["mn"]
	var mx: Vector2 = c["mx"]
	var keep: Array = c["keep"]
	var tris: Array = c["tris"]
	var cws: Array = c["cw"]
	var img: Image = _source_image(tex) if uber_idx >= 0 else null
	var drawn: Array = []  ## uber: contour polygons that got faces (full-res px), for the shadow mask
	for pi in keep.size():
		if not (tris[pi] as PackedInt32Array).is_empty():
			drawn.append(keep[pi])
	var px_h := mx.y - mn.y
	var s := h_m / px_h
	var cx := (mn.x + mx.x) * 0.5
	var bottom := mx.y
	var to_local := func(v: Vector2) -> Vector2: return Vector2((v.x - cx) * s, (bottom - v.y) * s)

	var st_front := SurfaceTool.new()
	var st_back := st_front if uber_idx >= 0 else SurfaceTool.new()
	var st_side := st_front if uber_idx >= 0 else SurfaceTool.new()
	var uber := uber_idx >= 0
	var ui := float(uber_idx)
	for st in ([st_front] if uber else [st_front, st_back, st_side]):
		st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var hz := thick * 0.5
	var edge_len_acc := 0.0
	for pi in keep.size():
		var poly: PackedVector2Array = keep[pi]
		var cw: bool = cws[pi]
		var idx: PackedInt32Array = tris[pi]
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
				if uber:
					st_front.set_uv2(Vector2(0.0, ui))
				st_front.add_vertex(Vector3(l.x, l.y, hz))
			for i in [order_front[0], order_front[2], order_front[1]]:
				var v: Vector2 = poly[i]
				var l: Vector2 = to_local.call(v)
				st_back.set_normal(Vector3(0, 0, -1))
				st_back.set_uv(Vector2(1.0 - v.x / full.x, v.y / full.y))
				if uber:
					st_back.set_uv2(Vector2(1.0, ui))
				st_back.add_vertex(Vector3(l.x, l.y, -hz))
		# Side walls.
		var n := poly.size()
		# uber (perf): neighbouring wall quads share their corner vertices (normal = mean of the two wall normals),
		# 2 instead of 4 vertices per contour point; the batched cards are vertex-bound.
		var en: Array[Vector3] = []
		if uber:
			for i in n:
				var d0: Vector2 = to_local.call(poly[(i + 1) % n]) - to_local.call(poly[i])
				var e := Vector2(d0.y, -d0.x).normalized() * (-1.0 if cw else 1.0)
				en.append(Vector3(e.x, e.y, 0) if d0.length_squared() >= 1e-10 else Vector3.ZERO)
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
			var na := n3
			var nb := n3
			if uber:
				na = _corner_normal(en, i, -1)
				nb = _corner_normal(en, i, 1)
			for k in order:
				st_side.set_normal(na if (k == 0 or k == 3) else nb)
				st_side.set_uv(quad[k][1])
				if uber:
					st_side.set_uv2(Vector2(2.0, ui))
				st_side.add_vertex(quad[k][0])
	var mesh := ArrayMesh.new()
	if uber:
		# The three parts were emitted in the same order into one tool: tangents per part are unchanged (no vertex is
		# shared across parts: their normals differ), index() only welds identical vertices.
		st_front.generate_tangents()
		st_front.index()
		st_front.commit(mesh)
		return {"mesh": mesh, "size": Vector2((mx.x - mn.x) * s, h_m), "avg": c["avg"], "hz": hz,
			"quad": Vector4(-cx * s, bottom * s, full.x * s, full.y * s), "image": img, "polys": drawn}
	for st in [st_front, st_back, st_side]:
		st.generate_tangents()
		st.commit(mesh)
	return {"mesh": mesh, "size": Vector2((mx.x - mn.x) * s, h_m), "avg": c["avg"]}


## perf: the traced outline of a print (full-res px), its triangulation and average colour do not depend on the card
## height or thickness, so they are computed once per (texture, eps) and reused by every card built from it.
static var _contour_cache := {}


static func _contour(tex: Texture2D, eps: float) -> Dictionary:
	var key := "%s|%.2f" % [tex.resource_path if tex.resource_path else str(tex.get_rid()), eps]
	if _contour_cache.has(key):
		return _contour_cache[key]
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
	var out := {}
	if not polys.is_empty():
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
		if not keep.is_empty():
			var tris := []
			var cws := []
			for poly in keep:
				cws.append(Geometry2D.is_polygon_clockwise(poly))
				var idx := Geometry2D.triangulate_polygon(poly)
				if idx.is_empty():
					idx = _robust_triangulate(poly)
				tris.append(idx)
			out = {"full": full, "mn": mn, "mx": mx, "keep": keep, "tris": tris, "cw": cws, "avg": _average(img),
				}
	_contour_cache[key] = out
	return out


## perf: trace a print ahead of time (story warm-up), so the first card built from it later costs no contour work.
static func warm(tex: Texture2D, eps := 1.6) -> void:
	if tex:
		_contour(tex, eps)


## Mean of wall normal i and its nearest non-degenerate neighbour on side `dir` (-1 previous, +1 next).
static func _corner_normal(en: Array[Vector3], i: int, dir: int) -> Vector3:
	var n := en.size()
	for k in range(1, n):
		var o: Vector3 = en[(i + dir * k + n * k) % n]
		if o != Vector3.ZERO:
			return (en[i] + o).normalized() if (en[i] + o).length_squared() > 1e-8 else en[i]
	return en[i]


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
