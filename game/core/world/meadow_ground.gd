class_name MeadowGround
extends GroundLayers
## Relief ground for the meadow template (integrator r1). Replaces the "single flat plane" the critics
## objected to with stacked die-cut cardstock, bottom to top:
##   table → book → printed water card (recessed) → felt base sheet with the stream cut out →
##   cut stream banks → rolling terrain tiers (3-5 stacked, each `tier_t` thick, cream cut edge,
##   soft drop-shadow skirt) → raised paper verge strips along the road → the road as its own
##   die-cut layer with a deckled edge → plank deck where the road crosses the stream.
## All pieces are static merged meshes (one MeshInstance per slab). Query helpers from GroundLayers still
## work (`surface_y` knows tiers, verges, road, deck).

const SKIRT_SHADER := preload("res://core/shaders/drop_skirt.gdshader")

@export var tier_t := 0.05  ## terrain tier thickness (INT r3: 3.2 -> 5 mm so each cut step reads)
@export var verge_w := 0.15
@export var verge_t := 0.022
@export var deckle := 0.010  ## road edge jitter (world units)
@export var light_dir := Vector2(-0.7, -0.45)  ## key light direction on the page (from the light), for skirt weight
@export var tier_colors: PackedColorArray = PackedColorArray([
	Color("74905f"), Color("839b65"), Color("93a76b"), Color("a3ae72"), Color("aeb57c")])
@export var deck_color := Color("a98a62")

var _verges: Array[PackedVector2Array] = []
var _deck_poly := PackedVector2Array()
var _skirt_st: SurfaceTool
var _deck_y := 0.0
var tiers_built := 0


func build() -> void:
	for c in get_children():
		c.queue_free()
	_rng.seed = seed_value
	_skirt_st = SurfaceTool.new()
	_skirt_st.begin(Mesh.PRIMITIVE_TRIANGLES)
	_path_line = _resample(path_points, 0.04)
	_stream_line = _resample(stream_points, 0.08)
	var half := page_size * 0.5
	var felt_rect := _rect(half - Vector2(page_margin, page_margin))
	if with_table:
		_build_table()
	if with_book:
		_build_book(half)
	var top := FELT_T
	var stream_cut := PackedVector2Array()
	if _stream_line.size() >= 2:
		stream_cut = _ribbon(_stream_line, stream_width * 0.5, 0.05, 1.7)
		_stream_poly = _clip_to(stream_cut, felt_rect)
		_add_stream_strip(_stream_line, stream_width * 0.5 + 0.12, 0.004)
	# Felt base sheet, stream cut out.
	var felt_parts: Array = [felt_rect]
	if stream_cut.size() >= 3:
		felt_parts = Geometry2D.clip_polygons(felt_rect, stream_cut)
	var felt_mat := _ground_mat(felt_color, felt_mottle, felt_mottle_strength, 0.0)
	felt_mat.set_shader_parameter("mottle_scale", 0.04)
	felt_mat.set_shader_parameter("fibre_strength", 0.36)  # INT r3: visible felt tooth
	felt_mat.set_shader_parameter("grain_strength", 0.28)
	felt_mat.set_shader_parameter("bump", 0.9)
	var felt_edge := _edge_mat(felt_color.lerp(Color("e9e2c4"), 0.6))
	for part in felt_parts:
		if Geometry2D.is_polygon_clockwise(part) != Geometry2D.is_polygon_clockwise(felt_rect):
			continue
		_add_slab(part, 0.0, FELT_T, felt_mat, felt_edge, "Felt")
	# Cut stream banks: a narrow lighter card strip on each side of the cut, sitting on the felt.
	if _stream_line.size() >= 2:
		_build_banks(top, felt_rect)
	# Road: own die-cut layer with deckled edges; gap over the stream (deck instead).
	var road_keep := []
	if _path_line.size() >= 2:
		_path_poly = _deckled_ribbon(_path_line, path_width * 0.5, 0.05, 3.1)
		var deck_cut := PackedVector2Array()
		if stream_cut.size() >= 3:
			deck_cut = _ribbon(_stream_line, stream_width * 0.5 + 0.1, 0.0, 0.0)
		var road_parts: Array = Geometry2D.intersect_polygons(_path_poly, felt_rect)
		if deck_cut.size() >= 3:
			var nxt := []
			for rp in road_parts:
				nxt.append_array(_solid(Geometry2D.clip_polygons(rp, deck_cut)))
			road_parts = nxt
			var dk := Geometry2D.intersect_polygons(_ribbon(_path_line, path_width * 0.5 + 0.04, 0.0, 0.0), deck_cut)
			if dk.size() > 0:
				_deck_poly = dk[0]
		var pm := _ground_mat(path_color, path_color.darkened(0.12), 0.45, 0.6)
		pm.set_shader_parameter("fibre_strength", 0.1)
		pm.set_shader_parameter("grain_strength", 0.08)
		pm.set_shader_parameter("mottle_scale", 0.12)
		pm.set_shader_parameter("speckle", 0.45)  # INT r3: printed gravel / wear
		pm.set_shader_parameter("speckle_color", Color("8a6a48"))
		var pe := _edge_mat(Color("f4ecd6"))
		for part in road_parts:
			_add_slab(part, top, PATH_T, pm, pe, "Road")
			_add_skirt(part, top, 0.08, 0.85)  # r2: stronger cast shadow off the road lift
		road_keep = road_parts
		_build_verges(top, felt_rect, stream_cut)
		if _deck_poly.size() >= 3:
			_deck_y = top + 0.03
			var dm := ShaderMaterial.new()
			dm.shader = preload("res://core/shaders/plank_deck.gdshader")
			dm.set_shader_parameter("wood", deck_color)
			dm.set_shader_parameter("felt_tex", FELT_TEX)
			var ci := _path_line.size() / 2
			var bd := INF
			for i in _path_line.size():
				if Geometry2D.is_point_in_polygon(_path_line[i], _deck_poly) and absf(stream_distance(_path_line[i])) < bd:
					bd = absf(stream_distance(_path_line[i]))
					ci = i
			dm.set_shader_parameter("along", _tangent(_path_line, ci))
			_add_slab(_deck_poly, 0.004, _deck_y - 0.004, dm, _edge_mat(Color("d9c09a")), "BridgeDeck")
	# Rolling terrain tiers (cut cardstock, stacked).
	_build_tiers(top)
	_build_patches(half - Vector2(page_margin + 0.3, page_margin + 0.3), top)
	# Commit the shadow skirts (one draw).
	var sm := ShaderMaterial.new()
	sm.shader = SKIRT_SHADER
	var mi := MeshInstance3D.new()
	mi.name = "DropSkirts"
	mi.mesh = _skirt_st.commit()
	mi.material_override = sm
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(mi)


# ------------------------------------------------------------------ queries

func surface_y(p: Vector2) -> float:
	for h in _hills:
		if Geometry2D.is_point_in_polygon(p, h[0]):
			return h[1]
	if _deck_poly.size() >= 3 and Geometry2D.is_point_in_polygon(p, _deck_poly):
		return _deck_y
	for v in _verges:
		if Geometry2D.is_point_in_polygon(p, v):
			return FELT_T + verge_t
	if _path_poly.size() >= 3 and Geometry2D.is_point_in_polygon(p, _path_poly):
		return FELT_T + PATH_T
	if _stream_poly.size() >= 3 and Geometry2D.is_point_in_polygon(p, _stream_poly):
		return 0.004
	for poly in _patches:
		if Geometry2D.is_point_in_polygon(p, poly):
			return FELT_T + COVER_T
	return FELT_T


func path_centre_3d() -> PackedVector3Array:
	var out := PackedVector3Array()
	for p in _path_line:
		out.append(Vector3(p.x, surface_y(p), p.y))
	return out


func path_line() -> PackedVector2Array:
	return _path_line


func stream_line() -> PackedVector2Array:
	return _stream_line


func tier_count() -> int:
	return _hills.size()


# ------------------------------------------------------------------ builders

func _build_tiers(top: float) -> void:
	_hills.clear()
	var keep_out: Array = []
	if _path_line.size() >= 2:
		keep_out.append(_ribbon(_path_line, path_width * 0.5 + verge_w + 0.1, 0.05, 2.3))
	if _stream_line.size() >= 2:
		keep_out.append(_ribbon(_stream_line, stream_width * 0.5 + 0.34, 0.06, 1.1))
	for spec in hill_specs:
		var c: Vector2 = spec[0]
		var r: float = spec[1]
		var tiers: int = spec[2]
		var squash: float = spec[3] if spec.size() > 3 else _rng.randf_range(0.5, 0.75)
		var off := Vector2.ZERO
		var prev_parts: Array = []
		for k in tiers:
			var rr := r * (1.0 - 0.21 * k) * _rng.randf_range(0.92, 1.05)
			off += Vector2(_rng.randf_range(-0.14, 0.14), _rng.randf_range(-0.16, 0.0)) * r
			var parts: Array = [_rolling_blob(c + off, rr, squash)]
			for ko in keep_out:
				var nxt: Array = []
				for pp in parts:
					for q in _solid(Geometry2D.clip_polygons(pp, ko)):
						if absf(_signed_area(q)) > 0.08:
							nxt.append(q)
				parts = nxt
			if k > 0:
				# Stack inside the tier below (no overhanging slabs): clip to it, shrunk a little.
				var inside: Array = []
				for pp in parts:
					for lower in prev_parts:
						for sh in _solid(Geometry2D.offset_polygon(lower, -0.1)):
							for q in _solid(Geometry2D.intersect_polygons(pp, sh)):
								if absf(_signed_area(q)) > 0.08:
									inside.append(q)
				parts = inside
			prev_parts = parts
			var ci := mini(k, tier_colors.size() - 1)
			var col: Color = tier_colors[ci]
			# r3: stronger low-frequency print variation (flat tier tops read as one sage sheet)
			var gm := _ground_mat(col, col.darkened(0.2).lerp(Color("9c9450"), 0.3), 1.0, 0.0)
			gm.set_shader_parameter("mottle_scale", 0.11)
			gm.set_shader_parameter("fibre_strength", 0.34)
			gm.set_shader_parameter("grain_strength", 0.26)
			gm.set_shader_parameter("bump", 0.9)
			var em := _edge_mat(col.lerp(Color("efe6c8"), 0.5))  # r3: 0.68 read as white planks at grazing angles
			for pp in parts:
				var yb := _hill_y_at(pp, top)
				_add_slab(pp, yb, tier_t, gm, em, "Tier%d" % k)
				_add_skirt(pp, yb, 0.07 + 0.02 * k, 0.75)
				_hills.append([pp, yb + tier_t, k])
				tiers_built += 1
	_hills.sort_custom(func(a, b): return a[1] > b[1])  # highest first for surface_y


## Base height for a new tier polygon: the highest existing tier under its centroid (stacking).
func _hill_y_at(poly: PackedVector2Array, top: float) -> float:
	var c := Vector2.ZERO
	for v in poly:
		c += v
	c /= poly.size()
	var y := top
	for h in _hills:
		if Geometry2D.is_point_in_polygon(c, h[0]):
			y = maxf(y, h[1])
	return y


func _build_banks(top: float, felt_rect: PackedVector2Array) -> void:
	var bm := _ground_mat(Color("a7a77a"), Color("8e9468"), 0.7, 0.25)
	bm.set_shader_parameter("mottle_scale", 0.3)
	var be := _edge_mat(Color("eee5c6"))
	for sd: float in [-1.0, 1.0]:
		var strip := _side_strip(_stream_line, stream_width * 0.5 - 0.02, stream_width * 0.5 + 0.12, sd, 0.4 + sd)
		for part in Geometry2D.intersect_polygons(strip, felt_rect):
			_add_slab(part, top, 0.026, bm, be, "Bank")  # INT r3: bank lip 8 -> 26 mm, channel reads sunk
			_add_skirt(part, top, 0.06, 0.7)


func _build_verges(top: float, felt_rect: PackedVector2Array, stream_cut: PackedVector2Array) -> void:
	var vm := _ground_mat(felt_color.lerp(Color("a7ad6c"), 0.55), felt_mottle, 0.6, 0.0)  # r2: distinct verge card
	vm.set_shader_parameter("mottle_scale", 0.18)
	var ve := _edge_mat(Color("ece4c6"))
	var gap := PackedVector2Array()
	if stream_cut.size() >= 3:
		gap = _ribbon(_stream_line, stream_width * 0.5 + 0.2, 0.0, 0.0)
	for sd: float in [-1.0, 1.0]:
		var strip := _side_strip(_path_line, path_width * 0.5 + 0.015, path_width * 0.5 + verge_w, sd, 2.0 + sd)
		var parts: Array = Geometry2D.intersect_polygons(strip, felt_rect)
		if gap.size() >= 3:
			var nxt := []
			for p in parts:
				nxt.append_array(_solid(Geometry2D.clip_polygons(p, gap)))
			parts = nxt
		for part in parts:
			if absf(_signed_area(part)) < 0.01:
				continue
			_add_slab(part, top, verge_t, vm, ve, "Verge")
			_add_skirt(part, top, 0.06, 0.75)
			_verges.append(part)


## One-sided strip between offsets d0..d1 from the line (side = +1 left / -1 right), outer edge deckled.
func _side_strip(line: PackedVector2Array, d0: float, d1: float, side: float, phase: float) -> PackedVector2Array:
	var inner := PackedVector2Array()
	var outer := PackedVector2Array()
	var s := 0.0
	for i in line.size():
		if i > 0:
			s += line[i].distance_to(line[i - 1])
		var t := _tangent(line, i)
		var n := Vector2(-t.y, t.x) * side
		var wob := 0.5 * (sin(s * 2.1 + phase) + 0.5 * sin(s * 5.3 + phase * 1.7))
		var dout := d1 + (d1 - d0) * 0.35 * wob + _rng.randf_range(-1.0, 1.0) * deckle * 0.6
		inner.append(line[i] + n * d0)
		outer.append(line[i] + n * dout)
	outer.reverse()
	inner.append_array(outer)
	return inner


## Road outline: hand-cut wobble plus a fine deckle (torn-fibre jitter) on both edges.
func _deckled_ribbon(line: PackedVector2Array, hw: float, wob: float, phase: float) -> PackedVector2Array:
	var base := _ribbon(line, hw, wob, phase)
	var out := PackedVector2Array()
	var prev := 0.0
	for i in base.size():
		var a := base[(i - 1 + base.size()) % base.size()]
		var b := base[(i + 1) % base.size()]
		var t := (b - a).normalized()
		var n := Vector2(-t.y, t.x)
		prev = prev * 0.45 + _rng.randf_range(-1.0, 1.0) * 0.55
		out.append(base[i] + n * prev * deckle)
	return out


## Rolling tier outline: a broad lobed blob with long low-frequency swells (fields, not cookie cutters).
func _rolling_blob(c: Vector2, r: float, squash: float) -> PackedVector2Array:
	var n := 72
	var ph := _rng.randf() * TAU
	var ph2 := _rng.randf() * TAU
	var ph3 := _rng.randf() * TAU
	var rot := _rng.randf_range(-0.25, 0.25)
	var out := PackedVector2Array()
	for i in n:
		var a := TAU * float(i) / float(n)
		var rr := r * (1.0 + 0.13 * sin(a * 3.0 + ph) + 0.07 * sin(a * 5.0 + ph2) + 0.03 * sin(a * 11.0 + ph3))
		out.append(c + Vector2(cos(a) * rr, sin(a) * rr * squash).rotated(rot))
	return out


## Soft darkening ring just outside a raised layer's cut edge, stronger on the side away from the key.
func _add_skirt(poly: PackedVector2Array, y: float, w: float, s: float) -> void:
	var n := poly.size()
	if n < 3:
		return
	var ccw := _signed_area(poly) > 0.0
	var L := light_dir.normalized()
	var yy := y + 0.0015
	for i in n:
		var a := poly[i]
		var b := poly[(i + 1) % n]
		var d := b - a
		var seg := d.length()
		if seg < 1e-5:
			continue
		var nrm := Vector2(d.y, -d.x) / seg
		if not ccw:
			nrm = -nrm
		var k := s * (0.4 + 0.6 * clampf(nrm.dot(L) * 0.5 + 0.5, 0.0, 1.0))
		var a2 := a + nrm * w
		var b2 := b + nrm * w
		var pts := [Vector3(a.x, yy, a.y), Vector3(b.x, yy, b.y), Vector3(b2.x, yy, b2.y), Vector3(a2.x, yy, a2.y)]
		var cols := [Color(0, 0, 0, k), Color(0, 0, 0, k), Color(0, 0, 0, 0), Color(0, 0, 0, 0)]
		for idx in [0, 1, 2, 0, 2, 3]:
			_skirt_st.set_color(cols[idx])
			_skirt_st.set_normal(Vector3.UP)
			_skirt_st.add_vertex(pts[idx])


## Outer polygons of a Geometry2D boolean result (holes have the opposite winding to the largest piece).
func _solid(res: Array) -> Array:
	if res.size() <= 1:
		return res
	var big: PackedVector2Array = res[0]
	for q in res:
		if absf(_signed_area(q)) > absf(_signed_area(big)):
			big = q
	var cw := Geometry2D.is_polygon_clockwise(big)
	var out := []
	for q in res:
		if Geometry2D.is_polygon_clockwise(q) == cw:
			out.append(q)
	return out
