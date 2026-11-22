class_name GroundLayers
extends Node3D
## Layered cut-paper ground for a pop-up spread (component B).
## Stack, bottom to top: table -> book (cover board + page block) -> teal stream card ->
## green felt-paper sheet with the stream cut out (visible cut edge) -> low ground-cover patches ->
## cream path layer (raised, visible card edge).
## All 2D layout is in page XZ (Vector2(x, z)). Query helpers let props avoid path/stream and
## let characters walk the path: `path_distance()`, `stream_distance()`, `surface_y()`, `path_centre_3d()`.

const FELT_TEX := preload("res://art/tex/felt_noise.png")
const FIBRE := preload("res://art/tex/paper_fibre.jpg")
const GROUND_SHADER := preload("res://core/shaders/ground_layer.gdshader")
const EDGE_SHADER := preload("res://core/shaders/paper_edge.gdshader")
const STREAM_SHADER := preload("res://core/shaders/stream.gdshader")
const STACK_SHADER := preload("res://core/shaders/page_stack.gdshader")
const TABLE_SHADER := preload("res://core/shaders/table_wood.gdshader")
const ROCK_SHADER := preload("res://core/shaders/folded_rock.gdshader")

const FELT_T := 0.022  ## felt sheet thickness (top of felt = page + FELT_T)
const COVER_T := 0.007
const PATH_T := 0.010
const HILL_T := 0.06

@export var page_size := Vector2(22.0, 15.0)
@export var page_margin := 0.14  ## cream page visible around the felt
@export var book_thickness := 0.32
@export var with_book := true
@export var with_table := true
@export var path_points: PackedVector2Array  ## path centreline (XZ); empty = no path
@export var path_width := 0.62
@export var stream_points: PackedVector2Array  ## stream centreline (XZ); empty = no stream
@export var stream_width := 0.8
@export var cover_patches := 140
@export var seed_value := 11
@export var felt_color := Color("8aa97c")
@export var felt_mottle := Color("769a6c")
@export var path_color := Color("e6d6b4")
## Low stacked felt hill tiers: each entry [Vector2 centre, float radius, int tiers]. Tiers are cut card
## (HILL_T thick) with a visible cut edge; they never cover the path or the stream (clipped out).
@export var hill_specs: Array = []
@export var hill_colors: PackedColorArray = PackedColorArray([Color("6e8a66"), Color("8aa276"), Color("a3b384"), Color("b8bf8e")])
## Large low-frequency value mottling of the felt (±value), the "not one flat fill" fix.
@export var felt_mottle_strength := 0.95
## "" = felt (default, every tale so far); "paper" = matte cut-paper sheets (sunmoon 2026-11-22, user: "펠트 질감
## 싫은뎅"): the ground shader's `paper` mode and dark cut-line edges instead of cream felt lips.
@export var ground_style := ""

var _path_line := PackedVector2Array()
var _stream_line := PackedVector2Array()
var _path_poly := PackedVector2Array()
var _stream_poly := PackedVector2Array()
var _patches: Array[PackedVector2Array] = []
var _hills: Array = []  ## [PackedVector2Array poly, float top_y], highest first after build
var _patch_mats: Array = []
var _patch_edge: ShaderMaterial
var _rng := RandomNumberGenerator.new()
## perf: spreads built ahead of their page slice the ground build too (BuildSlicer; null = all at once).
var slicer: BuildSlicer
var is_built := false


signal ground_built


func _ready() -> void:
	await build()
	is_built = true
	ground_built.emit()


func _tick() -> void:
	if slicer:
		await slicer.tick()


func build() -> void:
	_slab_groups.clear()
	for c in get_children():
		c.queue_free()
	_rng.seed = seed_value
	_path_line = _resample(path_points, 0.08)
	_stream_line = _resample(stream_points, 0.08)
	var half := page_size * 0.5
	var felt_rect := _rect(half - Vector2(page_margin, page_margin))
	if with_table:
		_build_table()
	if with_book:
		_build_book(half)
	var top := FELT_T
	# Stream: teal card under the felt, a bit wider than the cut.
	if _stream_line.size() >= 2:
		_stream_poly = _clip_to(_ribbon(_stream_line, stream_width * 0.5, 0.05, 1.7), felt_rect)
		_add_stream_strip(_stream_line, stream_width * 0.5 + 0.12, 0.004)
	# Felt sheet with the stream cut out.
	var felt_parts: Array = [felt_rect]
	if _stream_poly.size() >= 3:
		var cut := _ribbon(_stream_line, stream_width * 0.5, 0.05, 1.7)
		felt_parts = Geometry2D.clip_polygons(felt_rect, cut)
	var felt_mat := _ground_mat(felt_color, felt_mottle, felt_mottle_strength, 0.0)
	felt_mat.set_shader_parameter("mottle_scale", 0.045)
	felt_mat.set_shader_parameter("fibre_strength", 0.2)
	felt_mat.set_shader_parameter("grain_strength", 0.16)
	var felt_edge := _edge_mat(felt_color.lerp(Color("e9e2c4"), 0.55))
	for part in felt_parts:
		if Geometry2D.is_polygon_clockwise(part) != Geometry2D.is_polygon_clockwise(felt_rect):
			continue  # hole, only if the stream is fully inside the page (avoid that layout)
		_add_slab(part, 0.0, FELT_T, felt_mat, felt_edge, "Felt")
	# Path on the felt.
	if _path_line.size() >= 2:
		_path_poly = _ribbon(_path_line, path_width * 0.5, 0.06, 3.1)
		for part in Geometry2D.intersect_polygons(_path_poly, felt_rect):
			var pm := _ground_mat(path_color, path_color.darkened(0.1), 0.35, 0.55)
			pm.set_shader_parameter("fibre_strength", 0.06)
			pm.set_shader_parameter("grain_strength", 0.06)
			_add_slab(part, top, PATH_T, pm, _edge_mat(Color("f3ead2")), "Path")
	# Stacked hill tiers (cut felt card, visible edges).
	_build_hills(top)
	# Ground cover: lobed felt patches, some stacked two deep.
	await _build_patches(half - Vector2(page_margin + 0.3, page_margin + 0.3), top)
	flush_slabs()


# ------------------------------------------------------------------ queries

func path_distance(p: Vector2) -> float:
	return _line_distance(_path_line, p) - path_width * 0.5


func stream_distance(p: Vector2) -> float:
	return _line_distance(_stream_line, p) - stream_width * 0.5


## Height of the walkable/placeable surface at p (page XZ).
func surface_y(p: Vector2) -> float:
	for h in _hills:
		if Geometry2D.is_point_in_polygon(p, h[0]):
			return h[1]
	if _path_poly.size() >= 3 and Geometry2D.is_point_in_polygon(p, _path_poly):
		return FELT_T + PATH_T
	if _stream_poly.size() >= 3 and Geometry2D.is_point_in_polygon(p, _stream_poly):
		return 0.004
	for poly in _patches:
		if Geometry2D.is_point_in_polygon(p, poly):
			return FELT_T + COVER_T
	return FELT_T


## Stream centre line on the page (sound: the stream emitter slides along it).
func stream_line_3d() -> PackedVector3Array:
	var out := PackedVector3Array()
	for p in _stream_line:
		out.append(Vector3(p.x, FELT_T, p.y))
	return out


func path_centre_3d() -> PackedVector3Array:
	var out := PackedVector3Array()
	for p in _path_line:
		out.append(Vector3(p.x, FELT_T + PATH_T, p.y))
	return out


func on_page(p: Vector2, margin := 0.3) -> bool:
	var h := page_size * 0.5 - Vector2(page_margin + margin, page_margin + margin)
	return absf(p.x) < h.x and absf(p.y) < h.y


## Height of the hill tier under p (0 if none): lets placers keep tall cards off hill edges.
func hill_level(p: Vector2) -> int:
	for h in _hills:
		if Geometry2D.is_point_in_polygon(p, h[0]):
			return int(h[2]) + 1
	return 0


## A loose ground-cover patch under a prop cluster (darker moss under groves anchors them).
## kind: 0 sage, 1 leaf, 2 olive, 3 blue-green, 4 moss, 5 dark moss.
func add_patch(c: Vector2, r: float, kind := 5) -> void:
	if _patch_mats.is_empty():
		_init_patch_mats()
	var poly := _blob(c, r, _rng.randf_range(0.6, 0.95))
	var y := surface_y(c)
	_patches.append(poly)
	_add_slab(poly, y, COVER_T, _patch_mats[clampi(kind, 0, _patch_mats.size() - 1)], _patch_edge, "Cover")


## A folded (tented) paper rock: two printed grey-green faces meeting on a crease ridge, triangular ends.
## size = ridge height in units. Returns the MeshInstance3D.
func add_folded_rock(p: Vector2, size: float, yaw: float, tint := Color("8f9886")) -> MeshInstance3D:
	var y := surface_y(p)
	var L := size * _rng.randf_range(1.5, 2.3)
	var w0 := size * _rng.randf_range(0.7, 1.0)
	var w1 := size * _rng.randf_range(0.55, 0.9)
	var ro := size * _rng.randf_range(-0.2, 0.2)  # ridge offset: asymmetric fold
	var hl := L * 0.5
	var a0 := Vector3(-hl, 0, w0)
	var a1 := Vector3(hl * 0.9, 0, w0 * 0.8)
	var b0 := Vector3(-hl, 0, -w1)
	var b1 := Vector3(hl * 0.9, 0, -w1 * 0.8)
	var r0 := Vector3(-hl * 0.8, size, ro)
	var r1 := Vector3(hl * 0.7, size * 0.82, ro * 0.6)
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var nf := (a1 - a0).cross(r0 - a0).normalized()
	if nf.z < 0.0:
		nf = -nf
	_quad(st, a0, a1, r1, r0, nf, [Vector2(0, 0), Vector2(L, 0), Vector2(L, size), Vector2(0, size)])
	var nb := (b1 - b0).cross(r0 - b0).normalized()
	if nb.z > 0.0:
		nb = -nb
	_quad(st, b0, b1, r1, r0, nb, [Vector2(0, 0), Vector2(L, 0), Vector2(L, size), Vector2(0, size)])
	var ne0 := (a0 - b0).cross(r0 - b0).normalized()
	if ne0.x > 0.0:
		ne0 = -ne0
	_tri(st, a0, b0, r0, ne0, [Vector2(0, 0), Vector2(1, 0), Vector2(0.5, 1)])
	var ne1 := (a1 - b1).cross(r1 - b1).normalized()
	if ne1.x < 0.0:
		ne1 = -ne1
	_tri(st, a1, b1, r1, ne1, [Vector2(0, 0), Vector2(1, 0), Vector2(0.5, 1)])
	st.generate_tangents()
	var mi := MeshInstance3D.new()
	mi.name = "FoldedRock"
	mi.mesh = st.commit()
	var m := ShaderMaterial.new()
	m.shader = ROCK_SHADER
	m.set_shader_parameter("base_color", tint)
	m.set_shader_parameter("felt_tex", FELT_TEX)
	m.set_shader_parameter("seed", _rng.randf() * 10.0)
	m.set_shader_parameter("ridge_h", size)
	mi.material_override = m
	mi.position = Vector3(p.x, y, p.y)
	mi.rotation.y = yaw
	add_child(mi)
	return mi


# ------------------------------------------------------------------ builders

func _build_hills(top: float) -> void:
	_hills.clear()
	if hill_specs.is_empty():
		return
	var keep_out: Array = []
	if _path_line.size() >= 2:
		keep_out.append(_ribbon(_path_line, path_width * 0.5 + 0.22, 0.04, 3.1))
	if _stream_line.size() >= 2:
		keep_out.append(_ribbon(_stream_line, stream_width * 0.5 + 0.3, 0.04, 1.7))
	var edge_mats := []
	var top_mats := []
	for i in hill_colors.size():
		var c: Color = hill_colors[i]
		var gm := _ground_mat(c, c.darkened(0.12), 0.8, 0.0)
		gm.set_shader_parameter("mottle_scale", 0.12)
		gm.set_shader_parameter("fibre_strength", 0.18)
		top_mats.append(gm)
		edge_mats.append(_edge_mat(c.lerp(Color("ece4c8"), 0.6)))
	var found: Array = []
	for spec in hill_specs:
		var c: Vector2 = spec[0]
		var r: float = spec[1]
		var tiers: int = spec[2]
		var off := Vector2.ZERO
		for k in tiers:
			var rr := r * (1.0 - 0.27 * k) * _rng.randf_range(0.92, 1.05)
			off += Vector2(_rng.randf_range(-0.12, 0.12), _rng.randf_range(-0.12, 0.02)) * r
			var parts: Array = [_blob(c + off, rr, _rng.randf_range(0.55, 0.75))]
			for ko in keep_out:
				var nxt: Array = []
				for pp in parts:
					for q in Geometry2D.clip_polygons(pp, ko):
						if not Geometry2D.is_polygon_clockwise(q) == Geometry2D.is_polygon_clockwise(pp):
							continue
						if absf(_signed_area(q)) > 0.05:
							nxt.append(q)
				parts = nxt
			var y0 := top + HILL_T * k
			for pp in parts:
				var ci := mini(k, top_mats.size() - 1)
				_add_slab(pp, y0, HILL_T, top_mats[ci], edge_mats[ci], "Hill")
				found.append([pp, y0 + HILL_T, k])
	found.reverse()  # highest tiers first for surface_y
	_hills = found


func _init_patch_mats() -> void:
	var palette := [
		[Color("6c8a64"), Color("5f7d58")],  # sage
		[Color("7a9970"), Color("6d8c63")],  # leaf
		[Color("939a6c"), Color("848b5e")],  # olive
		[Color("668564"), Color("587756")],  # blue-green (LOOKF r1: greener, the old one read as puddles)
		[Color("78905e"), Color("6a8252")],  # moss
		[Color("566f4c"), Color("4b6343")],  # dark moss (under groves)
	]
	_patch_mats.clear()
	for pc in palette:
		var pmat := _ground_mat(pc[0], pc[1], 0.6, 0.0)
		pmat.set_shader_parameter("clump_strength", 0.34)  # LOOKF r1: felt nap on cover patches too
		pmat.set_shader_parameter("fibre_strength", 0.3)
		pmat.set_shader_parameter("bump", 1.3)
		_patch_mats.append(pmat)
	_patch_edge = _edge_mat(Color("c3caa2"))


func _build_table() -> void:
	var mi := MeshInstance3D.new()
	mi.name = "Table"
	var pm := PlaneMesh.new()
	pm.size = Vector2(90, 90)
	mi.mesh = pm
	var m := ShaderMaterial.new()
	m.shader = TABLE_SHADER
	m.set_shader_parameter("felt_tex", FELT_TEX)
	mi.material_override = m
	mi.position.y = -book_thickness - COVER_T * 2.0
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(mi)


func _build_book(half: Vector2) -> void:
	# Cover board (dark cloth), slightly larger than the page block.
	var cover := MeshInstance3D.new()
	cover.name = "Cover"
	var cb := BoxMesh.new()
	cb.size = Vector3(page_size.x + 0.5, 0.05, page_size.y + 0.36)
	cover.mesh = cb
	var cm := _ground_mat(Color("5a2418"), Color("40170f"), 0.5, 0.0)
	cover.material_override = cm
	cover.position.y = -book_thickness - 0.025
	add_child(cover)
	# Page block: cream top + striped page-stack sides.
	var block := MeshInstance3D.new()
	block.name = "PageBlock"
	var bb := BoxMesh.new()
	bb.size = Vector3(page_size.x, book_thickness, page_size.y)
	block.mesh = bb
	var sm := ShaderMaterial.new()
	sm.shader = STACK_SHADER
	sm.set_shader_parameter("fibre_tex", FIBRE)
	sm.set_shader_parameter("thickness", book_thickness)
	block.material_override = sm
	block.position.y = -book_thickness * 0.5 - 0.0005
	add_child(block)


func _add_stream_strip(line: PackedVector2Array, hw: float, y: float) -> void:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var s := 0.0
	var prev_l := Vector3.ZERO
	var prev_r := Vector3.ZERO
	var prev_s := 0.0
	for i in line.size():
		var t := _tangent(line, i)
		var n := Vector2(-t.y, t.x)
		var p := line[i]
		if i > 0:
			s += line[i].distance_to(line[i - 1])
		var l := Vector3(p.x + n.x * hw, y, p.y + n.y * hw)
		var r := Vector3(p.x - n.x * hw, y, p.y - n.y * hw)
		if i > 0:
			_quad(st, prev_l, prev_r, r, l, Vector3.UP,
				[Vector2(prev_s, 0), Vector2(prev_s, 1), Vector2(s, 1), Vector2(s, 0)])
		prev_l = l
		prev_r = r
		prev_s = s
	var mi := MeshInstance3D.new()
	mi.name = "Stream"
	mi.mesh = st.commit()
	var m := ShaderMaterial.new()
	m.shader = STREAM_SHADER
	m.set_shader_parameter("felt_tex", FELT_TEX)
	mi.material_override = m
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(mi)


func _build_patches(h: Vector2, top: float) -> void:
	_init_patch_mats()
	var mats := _patch_mats
	var edge := _patch_edge
	var placed := 0
	var tries := 0
	while placed < cover_patches and tries < cover_patches * 30:
		tries += 1
		var c := Vector2(_rng.randf_range(-h.x, h.x), _rng.randf_range(-h.y, h.y))
		var r := _rng.randf_range(0.14, 0.5)
		if _path_line.size() > 1 and path_closer_than(c, r + 0.06):
			continue
		if _stream_line.size() > 1 and stream_closer_than(c, r + 0.1):
			continue
		if hill_level(c) > 0:
			continue
		var k := _rng.randi() % 4
		if _rng.randf() < 0.08:
			k = 4
		var poly := _blob(c, r, _rng.randf_range(0.6, 1.0))
		_patches.append(poly)
		_add_slab(poly, top, COVER_T, mats[k], edge, "Cover")
		if r > 0.3 and _rng.randf() < 0.5:
			var k2 := (k + 1 + _rng.randi() % 2) % 4
			var c2 := c + Vector2(_rng.randf_range(-0.15, 0.15), _rng.randf_range(-0.15, 0.15)) * r
			_add_slab(_blob(c2, r * _rng.randf_range(0.45, 0.65), 0.9), top + COVER_T, COVER_T, mats[k2], edge, "Cover2")
		placed += 1
		await _tick()


## Extrude a 2D polygon (XZ) into a slab [y0, y0 + t]: top face + side walls (bottom omitted).
func _add_slab(poly: PackedVector2Array, y0: float, t: float, top_mat: Material, side_mat: Material, nm: String) -> void:
	if poly.size() < 3:
		return
	var idx := Geometry2D.triangulate_polygon(poly)
	if idx.is_empty():
		idx = _robust_triangulate(poly)
	var y1 := y0 + t
	var st_top := SurfaceTool.new()
	st_top.begin(Mesh.PRIMITIVE_TRIANGLES)
	for i in range(0, idx.size(), 3):
		var a := poly[idx[i]]
		var b := poly[idx[i + 1]]
		var c := poly[idx[i + 2]]
		_tri(st_top, Vector3(a.x, y1, a.y), Vector3(b.x, y1, b.y), Vector3(c.x, y1, c.y), Vector3.UP,
			[a, b, c])
	var st_side := SurfaceTool.new()
	st_side.begin(Mesh.PRIMITIVE_TRIANGLES)
	var ccw := _signed_area(poly) > 0.0
	var u := 0.0
	for i in poly.size():
		var a := poly[i]
		var b := poly[(i + 1) % poly.size()]
		var d := b - a
		var seg := d.length()
		if seg < 1e-5:
			continue
		var n2 := Vector2(d.y, -d.x) / seg
		if not ccw:
			n2 = -n2
		var n3 := Vector3(n2.x, 0, n2.y)
		_quad(st_side, Vector3(a.x, y1, a.y), Vector3(b.x, y1, b.y), Vector3(b.x, y0 - 0.002, b.y),
			Vector3(a.x, y0 - 0.002, a.y), n3, [Vector2(u, 0), Vector2(u + seg, 0), Vector2(u + seg, 1), Vector2(u, 1)])
		u += seg
	st_top.generate_tangents()
	st_side.generate_tangents()
	# perf: no MeshInstance per slab; the triangles join the batch of every slab with an identical material
	# (flush_slabs draws one surface per batch), same vertices and materials as before.
	_slab_add(top_mat, st_top.commit_to_arrays())
	_slab_add(side_mat, st_side.commit_to_arrays())
	if is_built:
		_queue_flush()


# ------------------------------------------------------------------ perf: slab batches

var _slab_groups := {}  ## material key -> {"mat", "arrays", "mi", "dirty"}
var _flush_queued := false


func _slab_add(mat: Material, arrays: Array) -> void:
	if arrays.is_empty() or arrays[Mesh.ARRAY_VERTEX] == null or (arrays[Mesh.ARRAY_VERTEX] as PackedVector3Array).is_empty():
		return
	var key := _mat_key(mat)
	var g: Dictionary = _slab_groups.get(key, {})
	if g.is_empty():
		g = {"mat": mat, "arrays": arrays, "mi": null, "dirty": true}
		_slab_groups[key] = g
		return
	var dst: Array = g["arrays"]
	for i in Mesh.ARRAY_MAX:
		if arrays[i] != null and dst[i] != null:
			dst[i].append_array(arrays[i])
	g["dirty"] = true


## Same shader + same uniform values = same material for drawing.
static func _mat_key(m: Material) -> String:
	if not (m is ShaderMaterial) or (m as ShaderMaterial).shader == null:
		return str(m.get_instance_id())
	var sm := m as ShaderMaterial
	var parts := PackedStringArray([str(sm.shader.get_instance_id())])
	for u: Dictionary in sm.shader.get_shader_uniform_list():
		var v: Variant = sm.get_shader_parameter(u["name"])
		parts.append(str(v.get_instance_id()) if v is Object else var_to_str(v))
	return "|".join(parts)


func _queue_flush() -> void:
	if not _flush_queued:
		_flush_queued = true
		flush_slabs.call_deferred()


## Builds / refreshes one MeshInstance per slab batch (called at the end of build and after late add_patch).
func flush_slabs() -> void:
	_flush_queued = false
	var n := 0
	for key: String in _slab_groups:
		var g: Dictionary = _slab_groups[key]
		n += 1
		if not g["dirty"]:
			continue
		g["dirty"] = false
		var mesh := ArrayMesh.new()
		mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, g["arrays"])
		var mi: MeshInstance3D = g["mi"]
		if mi == null or not is_instance_valid(mi):
			mi = MeshInstance3D.new()
			mi.name = "Slabs%d" % n
			add_child(mi)
			g["mi"] = mi
		mi.mesh = mesh
		mi.set_surface_override_material(0, g["mat"])


# ------------------------------------------------------------------ geometry helpers

## Front faces are clockwise in Godot: the right-hand normal must point away from `n`.
func _tri(st: SurfaceTool, p0: Vector3, p1: Vector3, p2: Vector3, n: Vector3, uvs: Array) -> void:
	var order := [0, 1, 2]
	if (p1 - p0).cross(p2 - p0).dot(n) > 0.0:
		order = [0, 2, 1]
	var ps := [p0, p1, p2]
	for k in order:
		st.set_normal(n)
		st.set_uv(uvs[k])
		st.add_vertex(ps[k])


func _quad(st: SurfaceTool, a: Vector3, b: Vector3, c: Vector3, d: Vector3, n: Vector3, uvs: Array) -> void:
	_tri(st, a, b, c, n, [uvs[0], uvs[1], uvs[2]])
	_tri(st, a, c, d, n, [uvs[0], uvs[2], uvs[3]])


func _rect(h: Vector2) -> PackedVector2Array:
	return PackedVector2Array([Vector2(-h.x, -h.y), Vector2(h.x, -h.y), Vector2(h.x, h.y), Vector2(-h.x, h.y)])


func _clip_to(poly: PackedVector2Array, rect: PackedVector2Array) -> PackedVector2Array:
	var r := Geometry2D.intersect_polygons(poly, rect)
	return r[0] if r.size() > 0 else PackedVector2Array()


func _resample(pts: PackedVector2Array, step: float) -> PackedVector2Array:
	if pts.size() < 2:
		return PackedVector2Array()
	var c := Curve2D.new()
	for i in pts.size():
		var p := pts[i]
		var t := (pts[mini(i + 1, pts.size() - 1)] - pts[maxi(i - 1, 0)]) * 0.25
		c.add_point(p, -t, t)
	c.bake_interval = step
	return c.get_baked_points()


func _tangent(line: PackedVector2Array, i: int) -> Vector2:
	var a := line[maxi(i - 1, 0)]
	var b := line[mini(i + 1, line.size() - 1)]
	return (b - a).normalized()


## Closed outline of a ribbon around `line` with hand-cut wobble on both edges.
func _ribbon(line: PackedVector2Array, hw: float, wob: float, phase: float) -> PackedVector2Array:
	var left := PackedVector2Array()
	var right := PackedVector2Array()
	var s := 0.0
	for i in line.size():
		if i > 0:
			s += line[i].distance_to(line[i - 1])
		var t := _tangent(line, i)
		var n := Vector2(-t.y, t.x)
		var wl := hw * (1.0 + wob * (sin(s * 2.3 + phase) + 0.6 * sin(s * 5.7 + phase * 2.0) + 0.35 * sin(s * 13.0 + phase)))
		var wr := hw * (1.0 + wob * (sin(s * 1.9 + phase * 3.0) + 0.6 * sin(s * 6.3 + phase) + 0.35 * sin(s * 11.0 + phase * 1.3)))
		left.append(line[i] + n * wl)
		right.append(line[i] - n * wr)
	right.reverse()
	left.append_array(right)
	return left


## Lobed blob, like a hand-cut patch of ground cover.
func _blob(c: Vector2, r: float, squash: float) -> PackedVector2Array:
	var n := 40
	var lobes := _rng.randi_range(4, 8)
	var ph := _rng.randf() * TAU
	var ph2 := _rng.randf() * TAU
	var rot := _rng.randf() * TAU
	var out := PackedVector2Array()
	for i in n:
		var a := TAU * float(i) / float(n)
		var rr := r * (1.0 + 0.07 * sin(a * lobes + ph) + 0.05 * sin(a * (lobes * 2 + 1) + ph2) + 0.04 * sin(a * 2.0 + ph2))
		var v := Vector2(cos(a) * rr, sin(a) * rr * squash).rotated(rot)
		out.append(c + v)
	return out


## perf (placement): path_distance(p) < d, answered from a segment grid (only segments near p are measured).
## Same distance arithmetic as path_distance on the segments that can be closer than d, so the answer is identical.
func path_closer_than(p: Vector2, d: float) -> bool:
	return _line_closer(_path_line, 0, p, d, path_width * 0.5)


## stream_distance(p) < d (see path_closer_than).
func stream_closer_than(p: Vector2, d: float) -> bool:
	return _line_closer(_stream_line, 1, p, d, stream_width * 0.5)


const _SEG_CELL := 0.5
var _seg_grids := [{}, {}]  ## per line: {"n": size, "a": first point, "cells": {Vector2i: PackedInt32Array}}


func _line_closer(line: PackedVector2Array, which: int, p: Vector2, d: float, half_w: float) -> bool:
	if line.size() < 2:
		return INF - half_w < d
	var g: Dictionary = _seg_grids[which]
	if g.get("n", -1) != line.size() or g.get("a", Vector2.INF) != line[0]:
		g = _build_seg_grid(line)
		_seg_grids[which] = g
	var cells: Dictionary = g["cells"]
	var r := d + half_w + 0.01
	if r <= 0.0:
		return false
	var c0 := Vector2i(floori((p.x - r) / _SEG_CELL), floori((p.y - r) / _SEG_CELL))
	var c1 := Vector2i(floori((p.x + r) / _SEG_CELL), floori((p.y + r) / _SEG_CELL))
	var best := INF
	for cx in range(c0.x, c1.x + 1):
		for cy in range(c0.y, c1.y + 1):
			var ids: PackedInt32Array = cells.get(Vector2i(cx, cy), PackedInt32Array())
			for i in ids:
				var q := Geometry2D.get_closest_point_to_segment(p, line[i], line[i + 1])
				best = minf(best, q.distance_squared_to(p))
	return sqrt(best) - half_w < d


func _build_seg_grid(line: PackedVector2Array) -> Dictionary:
	var cells := {}
	for i in line.size() - 1:
		var a := line[i]
		var b := line[i + 1]
		var c0 := Vector2i(floori(minf(a.x, b.x) / _SEG_CELL), floori(minf(a.y, b.y) / _SEG_CELL))
		var c1 := Vector2i(floori(maxf(a.x, b.x) / _SEG_CELL), floori(maxf(a.y, b.y) / _SEG_CELL))
		for cx in range(c0.x, c1.x + 1):
			for cy in range(c0.y, c1.y + 1):
				var k := Vector2i(cx, cy)
				if not cells.has(k):
					cells[k] = PackedInt32Array()
				var arr: PackedInt32Array = cells[k]
				arr.append(i)
				cells[k] = arr
	return {"n": line.size(), "a": line[0], "cells": cells}


func _line_distance(line: PackedVector2Array, p: Vector2) -> float:
	if line.size() < 2:
		return INF
	var best := INF
	for i in line.size() - 1:
		var q := Geometry2D.get_closest_point_to_segment(p, line[i], line[i + 1])
		best = minf(best, q.distance_squared_to(p))
	return sqrt(best)


func _signed_area(p: PackedVector2Array) -> float:
	var a := 0.0
	for i in p.size():
		var j := (i + 1) % p.size()
		a += p[i].x * p[j].y - p[j].x * p[i].y
	return a * 0.5


func _robust_triangulate(poly: PackedVector2Array) -> PackedInt32Array:
	var tri := Geometry2D.triangulate_delaunay(poly)
	var out := PackedInt32Array()
	for t in range(0, tri.size(), 3):
		var c := (poly[tri[t]] + poly[tri[t + 1]] + poly[tri[t + 2]]) / 3.0
		if Geometry2D.is_point_in_polygon(c, poly):
			out.append_array([tri[t], tri[t + 1], tri[t + 2]])
	return out


# ------------------------------------------------------------------ materials

func _ground_mat(base: Color, mottle: Color, mottle_strength: float, speckle: float) -> ShaderMaterial:
	var m := ShaderMaterial.new()
	m.shader = GROUND_SHADER
	m.set_shader_parameter("base_color", base)
	m.set_shader_parameter("mottle_color", mottle)
	m.set_shader_parameter("mottle_strength", mottle_strength)
	m.set_shader_parameter("felt_tex", FELT_TEX)
	m.set_shader_parameter("speckle", speckle)
	if ground_style == "paper":
		m.set_shader_parameter("paper", 1.0)
	return m


func _edge_mat(c: Color) -> ShaderMaterial:
	var m := ShaderMaterial.new()
	m.shader = EDGE_SHADER
	m.set_shader_parameter("edge_color", c)
	m.set_shader_parameter("fibre_tex", FIBRE)
	if ground_style == "paper":  # a cut paper edge: a dark line (the lit side catches the key on its own), no cream lip
		m.set_shader_parameter("edge_color", c.darkened(0.42).lerp(Color("5a4630"), 0.25))
		m.set_shader_parameter("brightness", 1.0)
	return m
