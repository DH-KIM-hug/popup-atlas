class_name HouseBody
extends MeshInstance3D
## A house card's body (2026-11-23, user: "집들은 무조건 입체적으로 아주 잘 들어맞게"): the front's own outline
## (tools/atlas/house_bodies.py -> res://art/atlas/bodies.json, facade px) extruded straight back from just inside the
## front card to `depth`, so every corner meets the front at its cut edge: side walls on the drawn wall edges, the roof
## surface along the drawn roof line (ridge, slopes, eave overhang with its soffit underneath), the outline filled at
## the back with the house's own gable over a plain wall, chimney stacks seated in the roof. Faces are printed with
## crops of the house's own art (house_body.gdshader, mirror-tiled) and every face is doubled inward (darker), so a
## camera inside the house (refuges, the shop, the cottage rooms) sees walls, not the meadow.
## Frame: the front card's frame (x right, y up from the base line, +z toward the reader); `to_local` maps facade px.

const SHADER := preload("res://core/shaders/house_body.gdshader")
const FIBRE := preload("res://art/tex/paper_fibre.jpg")
const BODIES := ["res://art/atlas/bodies.json"]

static var _specs := {}
static var _loaded := false
static var _mats := {}

var spec: Dictionary = {}
var depth := 0.4
var s := 0.001  ## world per facade px
var _to_local: Callable
var _glow_mats: Array[ShaderMaterial] = []
var _rim := 0.0  ## the clean (rim-stripped) print is smaller by this much per side: the body shrinks to fit inside it


static func spec_for(id: String) -> Dictionary:
	if not _loaded:
		_loaded = true
		for p in BODIES:
			if FileAccess.file_exists(p):
				var d: Variant = JSON.parse_string(FileAccess.get_file_as_string(p))
				if d is Dictionary:
					_specs.merge(d, true)
	return _specs.get(id, {})


## Wall width in world units at scale s.
static func wall_width(sp: Dictionary, s_: float) -> float:
	var wl: Array = sp.get("wall_lines", [[0, 0], [sp["px"][0], 0]])
	var ry := float(sp.get("roof_y", 0))
	return (float(wl[1][0]) + float(wl[1][1]) * ry - float(wl[0][0]) - float(wl[0][1]) * ry) * s_


## Body for a card standing as a PaperCard (origin = bottom centre of the traced outline, PaperCard._contour).
static func for_card(id: String, tex: Texture2D, card_h: float, card_thick: float, depth_: float = -1.0, skirt := 0.02) -> HouseBody:
	var sp := spec_for(id)
	if sp.is_empty() or tex == null:
		return null
	var c := PaperCard._contour(tex, 1.6)
	if c.is_empty():
		return null
	var full: Vector2 = c["full"]
	var mn: Vector2 = c["mn"]
	var mx: Vector2 = c["mx"]
	# the template draws the rim-stripped copy (art/atlas_clean, cropped by clean_off px)
	var off := Vector2.ZERO
	if "atlas_clean" in tex.resource_path and sp.has("clean_off"):
		off = Vector2(float(sp["clean_off"][0]), float(sp["clean_off"][1]))
	var s_ := card_h / (mx.y - mn.y)
	var cx := (mn.x + mx.x) * 0.5 + off.x
	var by := mx.y + off.y
	var f := func(p: Vector2) -> Vector2: return Vector2((p.x - cx) * s_, (by - p.y) * s_)
	var rim := float(sp.get("clean_rim", 0.0)) * s_ if off != Vector2.ZERO or "atlas_clean" in tex.resource_path else 0.0
	return make(sp, f, s_, depth_, card_thick, skirt, rim)


## Body for a banded facade (SetPiece): x from the facade's centre column, y up from base_px.
static func for_facade(id: String, px_w: float, base_px: float, s_: float, thick: float, depth_: float = -1.0, skirt := 0.02) -> HouseBody:
	var sp := spec_for(id)
	if sp.is_empty():
		return null
	var f := func(p: Vector2) -> Vector2: return Vector2((p.x - px_w * 0.5) * s_, (base_px - p.y) * s_)
	return make(sp, f, s_, depth_, thick, skirt)


static func make(sp: Dictionary, to_local_: Callable, s_: float, depth_: float, front_thick: float, skirt: float, rim := 0.0) -> HouseBody:
	var b := HouseBody.new()
	b.name = "HouseBody"
	b.spec = sp
	b.s = s_
	b._to_local = to_local_
	b.depth = depth_ if depth_ > 0.0 else float(sp.get("depth", 0.72)) * wall_width(sp, s_)
	b._rim = rim
	b._build(front_thick, skirt)
	return b


func to_local_px(p: Vector2) -> Vector2:
	return _to_local.call(p)


static func _mat(path: String, shade: float) -> ShaderMaterial:
	var key := "%s|%.2f" % [path, shade]
	if _mats.has(key):
		return _mats[key]
	var m := ShaderMaterial.new()
	m.shader = SHADER
	m.set_shader_parameter("albedo_tex", load(path))
	m.set_shader_parameter("fibre_tex", FIBRE)
	m.set_shader_parameter("shade", shade)
	_mats[key] = m
	return m


## Night: the printed light on the body glows like the front (lit windows on the back gable).
func set_glow(g: float) -> void:
	for i in mesh.get_surface_count() if mesh else 0:
		var m := get_surface_override_material(i)
		if m is ShaderMaterial:
			var mm := (m as ShaderMaterial).duplicate() as ShaderMaterial
			mm.set_shader_parameter("glow", g)
			set_surface_override_material(i, mm)


func _build(front_thick: float, skirt: float) -> void:
	var px: Array = spec["px"]
	var base_y := float(spec["base_y"])
	var pts: Array[Vector2] = []
	for p: Array in spec["poly"]:
		var l: Vector2 = _to_local.call(Vector2(float(p[0]), float(p[1])))
		if float(p[1]) >= base_y - 1.0:
			l.y = -skirt
		pts.append(l)
	var mats: Array = spec.get("mats", [])
	var n := pts.size()
	var area := 0.0
	for i in n:
		area += pts[i].cross(pts[(i + 1) % n])
	var ccw := area > 0.0  # y up
	# grow the outline a hair (mitred, 0.8 mm): the body skins the card's own cut edge, which does not draw from
	# every side (seen from above, its top edge left a slit between the front and the roof)
	var grown: Array[Vector2] = []
	for i in n:
		var pa := pts[(i - 1 + n) % n]
		var pb := pts[i]
		var pc := pts[(i + 1) % n]
		var n1 := Vector2((pb - pa).y, -(pb - pa).x).normalized()
		var n2 := Vector2((pc - pb).y, -(pc - pb).x).normalized()
		if not ccw:
			n1 = -n1
			n2 = -n2
		var bis := (n1 + n2)
		if bis.length() < 1e-4:
			bis = n1
		bis = bis.normalized()
		var cosh := maxf(bis.dot(n1), 0.35)
		grown.append(pb + bis * ((0.0008 - _rim) / cosh))
	for i in n:
		if pts[i].y > -skirt + 1e-5:
			pts[i] = grown[i]
	# from the card's front face (it covers the stock's cut edge) back to depth
	var z0 := front_thick * 0.5 - 0.002
	var z1 := -depth
	var root := "res://"
	var side_p := root + str(spec.get("side_file", ""))
	var roof_p := root + str(spec.get("roof_file", spec.get("side_file", "")))
	var back_p := root + str(spec.get("back_file", ""))
	var sw := 2.0 * float(spec["side_px"][0]) * s
	var sh := 2.0 * float(spec["side_px"][1]) * s
	var rw := 2.0 * float(spec["roof_px"][0]) * s
	var rh := 2.0 * float(spec["roof_px"][1]) * s
	var groups := {"wall": [], "roof": [], "soffit": [], "back": [], "inner": [], "chim": []}
	var arc := 0.0
	for i in n:
		var m := int(mats[i]) if i < mats.size() else 1
		var a := pts[i]
		var b := pts[(i + 1) % n]
		var d := b - a
		var L := d.length()
		if L < 1e-6:
			continue
		if m == 3:
			arc += L
			continue
		var on := Vector2(d.y, -d.x) / L  # outward for a ccw outline
		if not ccw:
			on = -on
		var nrm := Vector3(on.x, on.y, 0.0)
		var A0 := Vector3(a.x, a.y, z0)
		var B0 := Vector3(b.x, b.y, z0)
		var A1 := Vector3(a.x, a.y, z1)
		var B1 := Vector3(b.x, b.y, z1)
		var uv: Array
		if m == 0:
			uv = [Vector2(-z0 / sw, -a.y / sh), Vector2(-z0 / sw, -b.y / sh), Vector2(-z1 / sw, -b.y / sh), Vector2(-z1 / sw, -a.y / sh)]
		else:
			uv = [Vector2(-z0 / rw, arc / rh), Vector2(-z0 / rw, (arc + L) / rh), Vector2(-z1 / rw, (arc + L) / rh), Vector2(-z1 / rw, arc / rh)]
		arc += L
		var key := "wall" if m == 0 else ("roof" if m == 1 else "soffit")
		(groups[key] as Array).append([[A0, B0, B1, A1], uv, nrm])
		(groups["inner"] as Array).append([[A0, A1, B1, B0], [uv[0], uv[3], uv[2], uv[1]], -nrm])
	# back: the outline filled (its own gable over a plain wall), facing away; doubled inward
	var poly2 := PackedVector2Array(pts)
	var tri := Geometry2D.triangulate_polygon(poly2)
	if tri.is_empty():  # a pinched outline (the woodshed's posts): Delaunay inside the outline instead
		tri = PaperCard._robust_triangulate(poly2)
	var back_tris: Array = []
	var bpx := Vector2(float(px[0]), float(px[1]))
	var src: Array = spec["poly"]
	for t in range(0, tri.size(), 3):
		var ids := [tri[t], tri[t + 1], tri[t + 2]]
		var vs: Array = []
		var uvs: Array = []
		for k in ids:
			vs.append(Vector3(pts[k].x, pts[k].y, z1))
			uvs.append(Vector2(float(src[k][0]), float(src[k][1])) / bpx)
		back_tris.append([vs, uvs])
	# bottom: the foot closed (a low camera does not see up through the house, a slot does not show the hollow)
	var fx0 := INF
	var fx1 := -INF
	for q in pts:
		if q.y <= -skirt + 1e-5:
			fx0 = minf(fx0, q.x)
			fx1 = maxf(fx1, q.x)
	if fx1 > fx0:
		var fy := -skirt + 0.001
		(groups["inner"] as Array).append([[Vector3(fx0, fy, z0), Vector3(fx1, fy, z0), Vector3(fx1, fy, z1), Vector3(fx0, fy, z1)],
			[Vector2(0, 0), Vector2(1, 0), Vector2(1, 1), Vector2(0, 1)], Vector3.UP])
		(groups["soffit"] as Array).append([[Vector3(fx0, fy, z0), Vector3(fx1, fy, z0), Vector3(fx1, fy, z1), Vector3(fx0, fy, z1)],
			[Vector2(0, 0), Vector2(1, 0), Vector2(1, 1), Vector2(0, 1)], Vector3.DOWN])
	# chimney stacks: a box behind the drawn stack, down into the roof
	var chim: Array = spec.get("chimneys", [])
	var chim_quads: Array = []
	for c: Array in chim:
		var tl: Vector2 = _to_local.call(Vector2(float(c[0]), float(c[1])))
		var br: Vector2 = _to_local.call(Vector2(float(c[2]), float(c[3])))
		var cw := absf(br.x - tl.x)
		var cz1 := z0 - minf(cw, depth * 0.45)
		var x0 := tl.x
		var x1 := br.x
		var y0 := br.y
		var y1 := tl.y
		var hh := maxf(y1 - y0, 0.001)
		var u1 := (z0 - cz1) / cw
		chim_quads.append([[Vector3(x0, y1, z0), Vector3(x0, y0, z0), Vector3(x0, y0, cz1), Vector3(x0, y1, cz1)],
			[Vector2(1, 0), Vector2(1, 1), Vector2(1 - u1, 1), Vector2(1 - u1, 0)], Vector3(-1, 0, 0)])
		chim_quads.append([[Vector3(x1, y0, z0), Vector3(x1, y1, z0), Vector3(x1, y1, cz1), Vector3(x1, y0, cz1)],
			[Vector2(0, 1), Vector2(0, 0), Vector2(u1, 0), Vector2(u1, 1)], Vector3(1, 0, 0)])
		chim_quads.append([[Vector3(x0, y0, cz1), Vector3(x1, y0, cz1), Vector3(x1, y1, cz1), Vector3(x0, y1, cz1)],
			[Vector2(0, 1), Vector2(1, 1), Vector2(1, 0), Vector2(0, 0)], Vector3(0, 0, -1)])
		# its front too: a facade whose stack was cut away as its own card (three_pigs' brick house) shows it, and
		# behind a drawn stack it sits 2 mm inside the card's front face (the print wins)
		chim_quads.append([[Vector3(x0, y0, z0), Vector3(x1, y0, z0), Vector3(x1, y1, z0), Vector3(x0, y1, z0)],
			[Vector2(0, 1), Vector2(1, 1), Vector2(1, 0), Vector2(0, 0)], Vector3(0, 0, 1)])
		chim_quads.append([[Vector3(x0, y1, z0), Vector3(x0, y1, cz1), Vector3(x1, y1, cz1), Vector3(x1, y1, z0)],
			[Vector2(0, 0.02), Vector2(0, 0.08), Vector2(1, 0.08), Vector2(1, 0.02)], Vector3(0, 1, 0)])
	var am := ArrayMesh.new()
	var order: Array[Material] = []
	var add_quads := func(list: Array, mat: Material) -> void:
		if list.is_empty():
			return
		var st := SurfaceTool.new()
		st.begin(Mesh.PRIMITIVE_TRIANGLES)
		for q in list:
			var v: Array = q[0]
			var u: Array = q[1]
			var nn: Vector3 = q[2]
			for k in _wind([0, 1, 2, 0, 2, 3], v, nn):
				st.set_normal(nn)
				st.set_uv(u[k])
				st.add_vertex(v[k])
		st.generate_tangents()
		st.commit(am)
		order.append(mat)
	add_quads.call(groups["wall"], _mat(side_p, 1.0))
	add_quads.call(groups["roof"], _mat(roof_p, 1.0))
	add_quads.call(groups["soffit"], _mat(roof_p, 0.62))
	add_quads.call(groups["inner"], _mat(side_p, 0.42))
	if not back_tris.is_empty() and spec.has("back_file"):
		var st := SurfaceTool.new()
		st.begin(Mesh.PRIMITIVE_TRIANGLES)
		for t in back_tris:
			for pass_i in 2:  # 0 outside (facing -z), 1 inside (facing +z, darker material is separate below)
				if pass_i == 1:
					continue
				var nn := Vector3(0, 0, -1)
				for k in _wind([0, 1, 2], t[0], nn):
					st.set_normal(nn)
					st.set_uv(t[1][k])
					st.add_vertex(t[0][k])
		st.generate_tangents()
		st.commit(am)
		order.append(_mat(back_p, 1.0))
		var st2 := SurfaceTool.new()
		st2.begin(Mesh.PRIMITIVE_TRIANGLES)
		for t in back_tris:
			var nn := Vector3(0, 0, 1)
			for k in _wind([0, 1, 2], t[0], nn):
				st2.set_normal(nn)
				st2.set_uv(t[1][k])
				st2.add_vertex(t[0][k] + Vector3(0, 0, 0.0015))
		st2.generate_tangents()
		st2.commit(am)
		order.append(_mat(back_p, 0.42))
	if not chim_quads.is_empty() and spec.has("chimney_file"):
		add_quads.call(chim_quads, _mat(root + str(spec["chimney_file"]), 0.95))
	mesh = am
	for i in order.size():
		set_surface_override_material(i, order[i])
	cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON


## Index order for a polygon (fan indices) so its face points along nrm.
static func _wind(idx: Array, v: Array, nrm: Vector3) -> Array:
	var a: Vector3 = v[idx[0]]
	var b: Vector3 = v[idx[1]]
	var c: Vector3 = v[idx[2]]
	var fn := (b - a).cross(c - a)
	if fn.dot(nrm) > 0.0:  # counter-clockwise seen from nrm -> flip (Godot: clockwise front faces, checked on renders)
		var out := []
		for t in range(0, idx.size(), 3):
			out.append_array([idx[t], idx[t + 2], idx[t + 1]])
		return out
	return idx


## Door / window reveal: the wall's thickness inside an opening (facade px box x0, y0 (top), x1, y1 (bottom)).
## Thin quads from the front plane back `deep`, facing into the opening, printed with the wall (shaded).
func add_reveal(box: Array, deep: float, front_thick: float, sill := true) -> void:
	var tl: Vector2 = _to_local.call(Vector2(float(box[0]), float(box[1])))
	var br: Vector2 = _to_local.call(Vector2(float(box[2]), float(box[3])))
	var z0 := -front_thick * 0.5 + 0.001
	var z1 := z0 - deep
	var x0 := tl.x
	var x1 := br.x
	var yt := tl.y
	var yb := br.y
	var quads := [
		[[Vector3(x0, yb, z0), Vector3(x0, yt, z0), Vector3(x0, yt, z1), Vector3(x0, yb, z1)], Vector3(1, 0, 0)],
		[[Vector3(x1, yt, z0), Vector3(x1, yb, z0), Vector3(x1, yb, z1), Vector3(x1, yt, z1)], Vector3(-1, 0, 0)],
		[[Vector3(x0, yt, z0), Vector3(x1, yt, z0), Vector3(x1, yt, z1), Vector3(x0, yt, z1)], Vector3(0, -1, 0)]]
	if sill:
		quads.append([[Vector3(x1, yb, z0), Vector3(x0, yb, z0), Vector3(x0, yb, z1), Vector3(x1, yb, z1)], Vector3(0, 1, 0)])
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var sw := 2.0 * float(spec["side_px"][0]) * s
	for q in quads:
		var v: Array = q[0]
		var nn: Vector3 = q[1]
		for k in _wind([0, 1, 2, 0, 2, 3], v, nn):
			st.set_normal(nn)
			var p: Vector3 = v[k]
			st.set_uv(Vector2((p.x + p.z) / sw, -p.y / sw))
			st.add_vertex(p)
	st.generate_tangents()
	var mi := MeshInstance3D.new()
	mi.name = "Reveal"
	mi.mesh = st.commit()
	mi.material_override = _mat("res://" + str(spec.get("side_file", "")), 0.7)
	add_child(mi)
