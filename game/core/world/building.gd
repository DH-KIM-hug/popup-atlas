class_name Building
extends Node3D
## Buildings built in 3D from a spec (2026-11-23, user: "육면체뿐만 아니라 팔각정 등 팔각 집도", "성은 단순 육면체가 아닐거라고").
## A building is an assembly of PARTS placed relative to each other; every part is a closed paper volume whose faces
## are printed with the shared paper material swatches (story_bk_materials, mirror-tiled) and whose pieces are built
## from the same edges, so corners, eaves, ridges and apexes meet exactly:
##   block     walls on a footprint (rect, ngon, round, poly) with real thickness, openings cut through them (door /
##             window / arch with reveals, an arch's spandrels and intrados), optional crenellations, plinth and roof
##   pavilion  stone platform, pillars on the footprint's corners, a painted beam band, railings, a roof (팔각정, gazebo)
##   wall_run  a curtain wall from a to b: a solid slab with a walkway on top and battlements on its outer edge
##   gate      a block with a gateway through it (arched passage with depth), a portcullis and a drawbridge that move
##   stairs / bridge / flag / card   steps, a deck between two points, a pole with a flag card, any atlas card
## Roofs: gable, hip, pyramid (any polygon: 팔각 roof meets in one apex), cone (round), skirt (a lean-to ring for a
## lower tier of a pagoda / two-storey house), flat; `curve` turns the eaves up at the corners and sags the slope
## (Korean 처마), `overhang` is even all round, the eave line is set so the roof meets the wall tops with no slit.
## Specs live in res://art/buildings/kit.json ("kit" presets + "materials"); a tale places one with a set entry
## {"build": "<preset>" | {spec}, "at", "yaw", "scale", "state": {...}} (SpreadStage -> SetPiece.setup_building).

const KIT_PATH := "res://art/buildings/kit.json"
const SHADER := preload("res://core/shaders/house_body.gdshader")
const FIBRE := preload("res://art/tex/paper_fibre.jpg")

static var _kit := {}
static var _mat_cache := {}

var spec: Dictionary = {}
var unit := 1.0  ## world scale of the spec's units
var movers := {}  ## state name -> [Node3D, kind, cfg]
var _groups := {}  ## material key -> [verts, normals, uvs]
var _state := {}
var _state_t := {}
var _flags: Array[Node3D] = []
var _spin: Array[Node3D] = []
var _t := 0.0


static func kit() -> Dictionary:
	if _kit.is_empty() and FileAccess.file_exists(KIT_PATH):
		var d: Variant = JSON.parse_string(FileAccess.get_file_as_string(KIT_PATH))
		if d is Dictionary:
			_kit = d
	return _kit


static func preset(name: String) -> Dictionary:
	return (kit().get("kit", {}) as Dictionary).get(name, {})


## spec_or_name: a kit preset name or a spec {parts: [...]}; scale_: world units per spec unit.
static func make(spec_or_name: Variant, scale_ := 1.0, overrides: Dictionary = {}) -> Building:
	var sp: Dictionary = preset(str(spec_or_name)) if spec_or_name is String else spec_or_name
	if sp.is_empty():
		push_warning("Building: no kit preset " + str(spec_or_name))
		return null
	sp = sp.duplicate(true)
	sp.merge(overrides, true)
	var b := Building.new()
	b.name = "Building"
	b.spec = sp
	b.unit = scale_ * float(sp.get("scale", 1.0))
	b._build()
	return b


# ------------------------------------------------------------------ materials

static func _material(name: String, shade: float) -> Material:
	var key := "%s|%.2f" % [name, shade]
	if _mat_cache.has(key):
		return _mat_cache[key]
	var mats: Dictionary = kit().get("materials", {})
	var m := ShaderMaterial.new()
	m.shader = SHADER
	var info: Dictionary = mats.get(name, {})
	var p := str(info.get("tex", ""))
	var tex: Texture2D = load(p) if p != "" and ResourceLoader.exists(p) else null
	if tex == null:
		var img := Image.create(4, 4, false, Image.FORMAT_RGBA8)
		img.fill(Color(str(info.get("colour", "#c8b89a"))))
		tex = ImageTexture.create_from_image(img)
	m.set_shader_parameter("albedo_tex", tex)
	m.set_shader_parameter("fibre_tex", FIBRE)
	m.set_shader_parameter("shade", shade)
	m.set_shader_parameter("foot_ao_strength", 0.25)
	_mat_cache[key] = m
	return m


func _tile(mat: String) -> float:
	return float(((kit().get("materials", {}) as Dictionary).get(mat, {}) as Dictionary).get("tile", 0.3)) * unit


# ------------------------------------------------------------------ mesh accumulation

func _g(mat: String, shade: float) -> Array:
	var key := "%s|%.2f" % [mat, shade]
	if not _groups.has(key):
		_groups[key] = [[], [], [], mat, shade]  # plain Arrays: packed arrays inside an Array are copied on access
	return _groups[key]


## A planar polygon (3 or 4 points, fan) facing nrm.
func _poly(mat: String, shade: float, v: Array, uv: Array, nrm: Vector3) -> void:
	if nrm.length_squared() < 1e-12:
		return
	var g := _g(mat, shade)
	var idx := []
	for k in range(1, v.size() - 1):
		idx.append_array([0, k, k + 1])
	for k in HouseBody._wind(idx, v, nrm):
		(g[0] as Array).append(v[k])
		(g[1] as Array).append(nrm.normalized())
		(g[2] as Array).append(uv[k])


## Quad (a b c d in order round its edge) facing its own normal flipped toward `out` (a direction or a point test).
func _quad(mat: String, shade: float, a: Vector3, b: Vector3, c: Vector3, d: Vector3, out: Vector3, uv: Array, two_sided := false, inner_shade := 0.45) -> void:
	var n := (b - a).cross(d - a)
	if n.length_squared() < 1e-14:
		n = (c - b).cross(a - b)
	if n.dot(out) < 0.0:
		n = -n
	_poly(mat, shade, [a, b, c, d], uv, n)
	if two_sided:
		_poly(mat, inner_shade, [a, b, c, d], uv, -n)


func _tri(mat: String, shade: float, a: Vector3, b: Vector3, c: Vector3, out: Vector3, uv: Array, two_sided := false) -> void:
	var n := (b - a).cross(c - a)
	if n.dot(out) < 0.0:
		n = -n
	_poly(mat, shade, [a, b, c], uv, n)
	if two_sided:
		_poly(mat, 0.45, [a, b, c], uv, -n)


func _commit() -> void:
	var am := ArrayMesh.new()
	var mats: Array[Material] = []
	for key in _groups:
		var g: Array = _groups[key]
		if (g[0] as Array).is_empty():
			continue
		var arr := []
		arr.resize(Mesh.ARRAY_MAX)
		arr[Mesh.ARRAY_VERTEX] = PackedVector3Array(g[0])
		arr[Mesh.ARRAY_NORMAL] = PackedVector3Array(g[1])
		arr[Mesh.ARRAY_TEX_UV] = PackedVector2Array(g[2])
		var st := SurfaceTool.new()
		st.create_from_arrays(arr)
		st.generate_tangents()
		st.commit(am)
		mats.append(_material(str(g[3]), float(g[4])))
	var mi := MeshInstance3D.new()
	mi.name = "Shell"
	mi.mesh = am
	for i in mats.size():
		mi.set_surface_override_material(i, mats[i])
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	add_child(mi)
	_groups.clear()


# ------------------------------------------------------------------ footprints

## Footprint polygon (part-local x, z), counter-clockwise seen from above with +z toward the reader... normalised
## so that edge normals computed by _edge_out point outward.
func _footprint(p: Dictionary) -> PackedVector2Array:
	var u := unit
	var shape := str(p.get("shape", "rect"))
	var pts := PackedVector2Array()
	match shape:
		"rect":
			var s: Array = p.get("size", [1.0, 1.0])
			var w := float(s[0]) * u * 0.5
			var d := float(s[1]) * u * 0.5
			pts = PackedVector2Array([Vector2(-w, d), Vector2(w, d), Vector2(w, -d), Vector2(-w, -d)])
		"ngon", "round":
			var n := int(p.get("n", 8 if shape == "ngon" else 24))
			var r := float(p.get("r", 0.5)) * u
			var off := PI / n if shape == "ngon" else 0.0  # flat edge to the front
			for i in n:
				var a := PI * 0.5 + off + TAU * i / n
				pts.append(Vector2(cos(a) * r, sin(a) * r))
		"poly":
			for q: Array in p.get("pts", []):
				pts.append(Vector2(float(q[0]), float(q[1])) * u)
	# orient: shoelace in (x, z); make it positive
	var area := 0.0
	for i in pts.size():
		area += pts[i].x * pts[(i + 1) % pts.size()].y - pts[(i + 1) % pts.size()].x * pts[i].y
	if area < 0.0:
		pts.reverse()
	# edge 0 faces the reader (+z); then round the left side, the back, the right side
	var best := 0
	for i in pts.size():
		if _edge_out(pts[i], pts[(i + 1) % pts.size()]).y > _edge_out(pts[best], pts[(best + 1) % pts.size()]).y + 1e-6:
			best = i
	var rot := PackedVector2Array()
	for i in pts.size():
		rot.append(pts[(best + i) % pts.size()])
	return rot


static func _edge_out(a: Vector2, b: Vector2) -> Vector2:
	var d := (b - a).normalized()
	return Vector2(d.y, -d.x)  # outward for a positive (shoelace) polygon in (x, z)


static func _offset(pts: PackedVector2Array, o: float) -> PackedVector2Array:
	var out := PackedVector2Array()
	var n := pts.size()
	for i in n:
		var n1 := _edge_out(pts[(i - 1 + n) % n], pts[i])
		var n2 := _edge_out(pts[i], pts[(i + 1) % n])
		var bis := (n1 + n2).normalized()
		var c := maxf(bis.dot(n1), 0.3)
		out.append(pts[i] + bis * (o / c))
	return out


static func _centroid(pts: PackedVector2Array) -> Vector2:
	var c := Vector2.ZERO
	for q in pts:
		c += q
	return c / maxf(1.0, pts.size())


static func _inradius(pts: PackedVector2Array) -> float:
	var c := _centroid(pts)
	var r := INF
	for i in pts.size():
		var a := pts[i]
		var b := pts[(i + 1) % pts.size()]
		r = minf(r, absf(_edge_out(a, b).dot(c - a)))
	return r


# ------------------------------------------------------------------ build

func _build() -> void:
	for p: Dictionary in spec.get("parts", []):
		var node := Node3D.new()
		node.name = str(p.get("name", p.get("type", "part")))
		var at: Array = p.get("at", [0.0, 0.0])
		node.position = Vector3(float(at[0]), float(p.get("base", 0.0)), float(at[1])) * unit
		node.rotation.y = deg_to_rad(float(p.get("yaw", 0.0)))
		add_child(node)
		match str(p.get("type", "block")):
			"block", "tower":
				_block(p)
			"pavilion":
				_pavilion(p)
			"wall_run":
				_wall_run(p)
			"gate":
				_gate(p, node)
			"stairs":
				_stairs(p)
			"bridge":
				_bridge(p)
			"flag":
				_flag(p, node)
			"card":
				_card(p, node)
			"sails":
				_sails(p)
				_spin.append(node)
		if not _groups.is_empty():
			var before := get_child_count()
			_commit()
			var shell := get_child(before)
			remove_child(shell)
			node.add_child(shell)
	for k in spec.get("state", {}):
		set_state(str(k), float(spec["state"][k]), true)


## Walls with thickness on footprint pts from y0 to y1; openings cut through. Returns nothing.
## openings: [{edge, u (0..1 along the edge), w, h, y, kind: door|window|arch|gate, card, depth, through}]
func _walls(pts: PackedVector2Array, y0: float, y1: float, thick: float, mat: String, openings: Array, cap := false, inner := true) -> void:
	var n := pts.size()
	var inn := _offset(pts, -thick)
	var tile := _tile(mat)
	var arc := 0.0
	for i in n:
		var a := pts[i]
		var b := pts[(i + 1) % n]
		var ai := inn[i]
		var bi := inn[(i + 1) % n]
		var L := a.distance_to(b)
		var dir := (b - a) / maxf(L, 1e-6)
		var o2 := _edge_out(a, b)
		var out := Vector3(o2.x, 0, o2.y)
		# along-edge coordinates of the inner corners
		var sai := (ai - a).dot(dir)
		var sbi := (bi - a).dot(dir)
		var holes: Array = []  # [s0, s1, v0, v1, kind]
		for op: Dictionary in openings:
			if int(op.get("edge", 0)) != i:
				continue
			var w := float(op.get("w", 0.2)) * unit
			var s0 := float(op.get("u", 0.5)) * L - w * 0.5
			var v0 := y0 + float(op.get("y", 0.0)) * unit
			var v1 := minf(v0 + float(op.get("h", 0.3)) * unit, y1 - 0.004)
			holes.append([s0, s0 + w, v0, v1, str(op.get("kind", "window")), op])
		var P := func(s: float, y: float, inner_: bool) -> Vector3:
			var q := (a + dir * s - o2 * thick) if inner_ else (a + dir * s)
			return Vector3(q.x, y, q.y)
		var faces := [[false, 0.0, L, 1.0]]
		if inner:
			faces.append([true, sai, sbi, 0.55])
		for f in faces:
			var isin: bool = f[0]
			var sx := [float(f[1]), float(f[2])]
			var vy := [y0, y1]
			for h: Array in holes:
				sx.append_array([h[0], h[1]])
				vy.append_array([h[2], h[3]])
			sx.sort()
			vy.sort()
			for ci in sx.size() - 1:
				var s0: float = sx[ci]
				var s1: float = sx[ci + 1]
				if s1 - s0 < 1e-5 or s0 < float(f[1]) - 1e-5 or s1 > float(f[2]) + 1e-5:
					continue
				for ri in vy.size() - 1:
					var v0: float = vy[ri]
					var v1: float = vy[ri + 1]
					if v1 - v0 < 1e-5:
						continue
					var sm := (s0 + s1) * 0.5
					var vm := (v0 + v1) * 0.5
					var in_hole := false
					for h: Array in holes:
						if sm > h[0] and sm < h[1] and vm > h[2] and vm < h[3]:
							in_hole = true
					if in_hole:
						continue
					var uv := [Vector2((arc + s0) / tile, -v0 / tile), Vector2((arc + s1) / tile, -v0 / tile),
						Vector2((arc + s1) / tile, -v1 / tile), Vector2((arc + s0) / tile, -v1 / tile)]
					_quad(mat, float(f[3]), P.call(s0, v0, isin), P.call(s1, v0, isin), P.call(s1, v1, isin), P.call(s0, v1, isin),
						-out if isin else out, uv)
		# reveals through the wall thickness (jambs, lintel, sill) and arches
		for h: Array in holes:
			var s0: float = h[0]
			var s1: float = h[1]
			var v0: float = h[2]
			var v1: float = h[3]
			var kind: String = h[4]
			var arch := kind in ["arch", "gate", "door_arch"]
			var r := (s1 - s0) * 0.5
			var spring := v1 - r if arch else v1
			var rv := func(sa: float, sb: float, ya: float, yb: float, facing: Vector3) -> void:
				_quad(mat, 0.72, P.call(sa, ya, false), P.call(sb, yb, false), P.call(sb, yb, true), P.call(sa, ya, true), facing,
					[Vector2(0, 0), Vector2(thick / tile, 0), Vector2(thick / tile, (yb - ya + sb - sa) / tile), Vector2(0, (yb - ya + sb - sa) / tile)])
			rv.call(s0, s0, v0, spring, Vector3(dir.x, 0, dir.y))  # left jamb faces along +dir
			rv.call(s1, s1, v0, spring, -Vector3(dir.x, 0, dir.y))
			if v0 > y0 + 0.001:
				rv.call(s0, s1, v0, v0, Vector3.UP)  # sill
			if not arch:
				rv.call(s0, s1, v1, v1, Vector3.DOWN)
			else:
				var segs := 10
				var c := (s0 + s1) * 0.5
				for k in segs:
					var a0 := PI - PI * k / segs
					var a1 := PI - PI * (k + 1) / segs
					var p0 := Vector2(c + cos(a0) * r, spring + sin(a0) * r)
					var p1 := Vector2(c + cos(a1) * r, spring + sin(a1) * r)
					var inward := Vector3(-(cos(a0) + cos(a1)) * 0.5 * dir.x, -(sin(a0) + sin(a1)) * 0.5, -(cos(a0) + cos(a1)) * 0.5 * dir.y)
					rv.call(p0.x, p1.x, p0.y, p1.y, inward)
					# spandrels on both faces: from the arc to the hole's top corners
					var corner := Vector2(s0, v1) if k < segs / 2 else Vector2(s1, v1)
					for isin in [false, true]:
						var uv3 := [Vector2((arc + p0.x) / tile, -p0.y / tile), Vector2((arc + p1.x) / tile, -p1.y / tile), Vector2((arc + corner.x) / tile, -corner.y / tile)]
						_tri(mat, 0.55 if isin else 1.0, P.call(p0.x, p0.y, isin), P.call(p1.x, p1.y, isin), P.call(corner.x, corner.y, isin), -out if isin else out, uv3)
					if k == segs / 2 - 1:
						for isin in [false, true]:
							var top := Vector2(c, v1)
							_tri(mat, 0.55 if isin else 1.0, P.call(p1.x, p1.y, isin), P.call(s0, v1, isin), P.call(s1, v1, isin), -out if isin else out,
								[Vector2(0, 0), Vector2(0.1, 0), Vector2(0.05, 0.1)])
			# the opening's card (a door / window / gate leaf) recessed in the reveal
			var op: Dictionary = h[5]
			if op.has("card") and not op.get("open", false):
				var cn := Node3D.new()
				var mid := a + dir * ((s0 + s1) * 0.5) - o2 * (thick * float(op.get("recess", 0.5)))
				cn.position = Vector3(mid.x, v0, mid.y)
				cn.rotation.y = atan2(o2.x, o2.y)
				var card := _atlas_card(str(op["card"]), v1 - v0, s1 - s0)
				if card:
					cn.add_child(card)
					_pending_nodes.append(cn)
		# top cap (battlement walkways, roofless towers, and under every roof's eave line)
		if true:  # top cap: under a roof it closes the wall stock, on battlements it is the walkway
			var uvc := [Vector2(0, 0), Vector2(L / tile, 0), Vector2(L / tile, thick / tile), Vector2(0, thick / tile)]
			_quad(mat, 0.9, Vector3(a.x, y1, a.y), Vector3(b.x, y1, b.y), Vector3(bi.x, y1, bi.y), Vector3(ai.x, y1, ai.y), Vector3.UP, uvc)
		arc += L


var _pending_nodes: Array[Node3D] = []


## A card from the shared atlas (doors, windows, flags, railings), height h; squeezed to width w when w > 0.
func _atlas_card(id: String, h: float, w := -1.0) -> Node3D:
	var e := SpreadStage.atlas_entry(id)
	if e.is_empty():
		return null
	var path := str(e["path"])
	if not path.begins_with("res://"):
		path = "res://" + path
	if not ResourceLoader.exists(path):
		return null
	var c := PaperCard.new()
	c.texture = load(path)
	c.height = h
	c.thickness = clampf(h * 0.03, 0.004, 0.012)
	c.back_print = true
	var hold := Node3D.new()
	if w > 0.0:
		var ts := c.texture.get_size()
		var nat := h * ts.x / maxf(ts.y, 1.0)
		hold.scale = Vector3(w / maxf(nat, 0.001), 1, 1)
	hold.add_child(c)
	return hold


func _flush_nodes(parent: Node3D) -> void:
	for n in _pending_nodes:
		parent.add_child(n)
	_pending_nodes.clear()


## Merlons along the outer edge of pts at y (battlements).
func _crenel(pts: PackedVector2Array, y: float, thick: float, cfg: Dictionary, mat: String) -> void:
	var mh := float(cfg.get("h", 0.08)) * unit
	var mw := float(cfg.get("w", 0.08)) * unit
	var gap := float(cfg.get("gap", 0.06)) * unit
	var depth := minf(float(cfg.get("d", 0.05)) * unit, thick)
	var tile := _tile(mat)
	var n := pts.size()
	for i in n:
		var a := pts[i]
		var b := pts[(i + 1) % n]
		var L := a.distance_to(b)
		var dir := (b - a) / maxf(L, 1e-6)
		var o2 := _edge_out(a, b)
		var count := maxi(1, int(floor((L + gap) / (mw + gap))))
		var used := count * mw + (count - 1) * gap
		var s := (L - used) * 0.5
		for k in count:
			var s0 := s + k * (mw + gap)
			var s1 := s0 + mw
			var q := [a + dir * s0, a + dir * s1, a + dir * s1 - o2 * depth, a + dir * s0 - o2 * depth]
			var B := []
			var T := []
			for v: Vector2 in q:
				B.append(Vector3(v.x, y - 0.002, v.y))
				T.append(Vector3(v.x, y + mh, v.y))
			var c3: Vector3 = ((T[0] as Vector3) + (T[2] as Vector3)) * 0.5
			for e in 4:
				var e1 := (e + 1) % 4
				var fo: Vector3 = ((B[e] + B[e1]) * 0.5 - Vector3(c3.x, y, c3.z))
				var lw: float = (B[e] as Vector3).distance_to(B[e1])
				_quad(mat, 1.0, B[e], B[e1], T[e1], T[e], fo, [Vector2(0, 0), Vector2(lw / tile, 0), Vector2(lw / tile, -mh / tile), Vector2(0, -mh / tile)])
			_quad(mat, 0.92, T[0], T[1], T[2], T[3], Vector3.UP, [Vector2(0, 0), Vector2(mw / tile, 0), Vector2(mw / tile, depth / tile), Vector2(0, depth / tile)])


## A roof over footprint pts whose wall tops are at y_w. cfg: {type, h | pitch, overhang, mat, curve, thick, ridge}
func _roof(pts: PackedVector2Array, y_w: float, cfg: Dictionary, upper: PackedVector2Array = PackedVector2Array()) -> float:
	var typ := str(cfg.get("type", "pyramid"))
	if typ == "none":
		return y_w
	var mat := str(cfg.get("mat", "terracotta"))
	var o := float(cfg.get("overhang", 0.06)) * unit
	var th := float(cfg.get("thick", 0.025)) * unit
	var curve := float(cfg.get("curve", 0.0))
	var E := _offset(pts, o)
	var c := _centroid(pts)
	var tile := _tile(mat)
	if typ == "flat":
		var y := y_w
		var ctr := Vector3(c.x, y + th, c.y)
		for i in E.size():
			var a := E[i]
			var b := E[(i + 1) % E.size()]
			_tri(mat, 0.95, Vector3(a.x, y + th, a.y), Vector3(b.x, y + th, b.y), ctr, Vector3.UP, [a / tile, b / tile, c / tile])
			_tri(mat, 0.55, Vector3(a.x, y, a.y), Vector3(b.x, y, b.y), Vector3(c.x, y, c.y), Vector3.DOWN, [a / tile, b / tile, c / tile])
			var o3 := Vector3(_edge_out(a, b).x, 0, _edge_out(a, b).y)
			_quad(mat, 0.8, Vector3(a.x, y, a.y), Vector3(b.x, y, b.y), Vector3(b.x, y + th, b.y), Vector3(a.x, y + th, a.y), o3,
				[Vector2(0, 0), Vector2(a.distance_to(b) / tile, 0), Vector2(a.distance_to(b) / tile, th / tile), Vector2(0, th / tile)])
		return y + th
	# rise: explicit h, else pitch * inradius
	var run := _inradius(pts)
	var H := float(cfg.get("h", float(cfg.get("pitch", 0.8)) * run / unit)) * unit
	var faces: Array = []  # [eave a, eave b, top c (over a), top d (over b)] in xz + heights
	var top_y := y_w + H
	match typ:
		"pyramid", "cone":
			for i in E.size():
				faces.append([E[i], E[(i + 1) % E.size()], c, c, top_y, top_y])
		"hip", "gable":
			# rect footprint: ridge along the longer axis (or cfg.ridge "x" / "z")
			var mn := Vector2(INF, INF)
			var mx := -mn
			for q in E:
				mn = mn.min(q)
				mx = mx.max(q)
			var along_x := (mx.x - mn.x) >= (mx.y - mn.y)
			if cfg.has("ridge"):
				along_x = str(cfg["ridge"]) == "x"
			var half := ((mx.y - mn.y) if along_x else (mx.x - mn.x)) * 0.5
			var hip_in := half if typ == "hip" else 0.0
			var r0: Vector2
			var r1: Vector2
			if along_x:
				r0 = Vector2(mn.x + hip_in, (mn.y + mx.y) * 0.5)
				r1 = Vector2(mx.x - hip_in, (mn.y + mx.y) * 0.5)
				if r1.x < r0.x:
					r0.x = (mn.x + mx.x) * 0.5
					r1.x = r0.x
				faces.append([Vector2(mx.x, mx.y), Vector2(mn.x, mx.y), r1, r0, top_y, top_y])  # front (+z)
				faces.append([Vector2(mn.x, mn.y), Vector2(mx.x, mn.y), r0, r1, top_y, top_y])  # back
				if typ == "hip":
					faces.append([Vector2(mn.x, mx.y), Vector2(mn.x, mn.y), r0, r0, top_y, top_y])
					faces.append([Vector2(mx.x, mn.y), Vector2(mx.x, mx.y), r1, r1, top_y, top_y])
			else:
				r0 = Vector2((mn.x + mx.x) * 0.5, mn.y + hip_in)
				r1 = Vector2((mn.x + mx.x) * 0.5, mx.y - hip_in)
				if r1.y < r0.y:
					r0.y = (mn.y + mx.y) * 0.5
					r1.y = r0.y
				faces.append([Vector2(mx.x, mn.y), Vector2(mx.x, mx.y), r0, r1, top_y, top_y])  # right
				faces.append([Vector2(mn.x, mx.y), Vector2(mn.x, mn.y), r1, r0, top_y, top_y])  # left
				if typ == "hip":
					faces.append([Vector2(mx.x, mx.y), Vector2(mn.x, mx.y), r1, r1, top_y, top_y])
					faces.append([Vector2(mn.x, mn.y), Vector2(mx.x, mn.y), r0, r0, top_y, top_y])
			run = half
			if typ == "gable":
				# gable ends: wall triangles from the wall tops up under the ridge (the building's wall material)
				var wm := str(cfg.get("gable_mat", cfg.get("wall_mat", "plaster")))
				var wt := _tile(wm)
				var pm := Vector2(INF, INF)
				var px := -pm
				for q in pts:
					pm = pm.min(q)
					px = px.max(q)
				for end in [0, 1]:
					var a3: Vector3
					var b3: Vector3
					var t3: Vector3
					var outd: Vector3
					if along_x:
						var x := pm.x if end == 0 else px.x
						a3 = Vector3(x, y_w, px.y)
						b3 = Vector3(x, y_w, pm.y)
						t3 = Vector3(x, top_y - th, (pm.y + px.y) * 0.5)
						outd = Vector3(-1 if end == 0 else 1, 0, 0)
					else:
						var z := pm.y if end == 0 else px.y
						a3 = Vector3(pm.x, y_w, z)
						b3 = Vector3(px.x, y_w, z)
						t3 = Vector3((pm.x + px.x) * 0.5, top_y - th, z)
						outd = Vector3(0, 0, -1 if end == 0 else 1)
					# the gable's foot follows the roof underside: y_w at the wall line, top_y - th under the ridge
					_tri(wm, 1.0, a3, b3, t3, outd, [Vector2(0, 0), Vector2(a3.distance_to(b3) / wt, 0), Vector2(a3.distance_to(b3) * 0.5 / wt, -(t3.y - y_w) / wt)], true)
		"skirt":
			# lower tier: from the eaves up to the upper storey's footprint (its wall foot), a lean-to ring
			var U := upper if upper.size() == E.size() else _offset(pts, -run * 0.45)
			for i in E.size():
				faces.append([E[i], E[(i + 1) % E.size()], U[i], U[(i + 1) % U.size()], top_y, top_y])
	# eave height so the roof surface passes the wall line at the wall top (+ thickness): no slit under the roof
	var slope := H / maxf(run + o, 1e-4)
	var y_e := y_w + th - o * slope
	var R := 6 if curve > 0.0 else 1
	var M := 8 if curve > 0.0 else 1
	for f: Array in faces:
		var A: Vector2 = f[0]
		var B: Vector2 = f[1]
		var C: Vector2 = f[2]
		var D: Vector2 = f[3]
		var eave_len := A.distance_to(B)
		var grid := []  # [row][col] -> Vector3 (top surface)
		for ri in R + 1:
			var t := float(ri) / R
			var row := []
			for ci in M + 1:
				var w := float(ci) / M
				var e2 := A.lerp(B, w)
				var t2 := C.lerp(D, w)
				var q := e2.lerp(t2, t)
				var ft := t if curve <= 0.0 else pow(t, 1.0 + curve * 0.9)
				var y := y_e + (float(f[4]) - y_e) * ft
				if curve > 0.0:
					var corner := pow(absf(w * 2.0 - 1.0), 3.0)
					y += curve * H * 0.22 * corner * (1.0 - t) * (1.0 - t)
				row.append(Vector3(q.x, y, q.y))
			grid.append(row)
		var fo := Vector3(_edge_out(A, B).x, 0.0, _edge_out(A, B).y) + Vector3.UP * 0.5
		var slope_len := ((A + B) * 0.5).distance_to((C + D) * 0.5)
		for ri in R:
			for ci in M:
				var p00: Vector3 = grid[ri][ci]
				var p01: Vector3 = grid[ri][ci + 1]
				var p11: Vector3 = grid[ri + 1][ci + 1]
				var p10: Vector3 = grid[ri + 1][ci]
				var u0 := eave_len * float(ci) / M / tile
				var u1 := eave_len * float(ci + 1) / M / tile
				var v0 := slope_len * float(ri) / R / tile
				var v1 := slope_len * float(ri + 1) / R / tile
				var uv := [Vector2(u0, -v0), Vector2(u1, -v0), Vector2(u1, -v1), Vector2(u0, -v1)]
				if p11.distance_to(p10) < 1e-5:
					_tri(mat, 1.0, p00, p01, p11, fo, [uv[0], uv[1], uv[2]])
					_tri(mat, 0.5, p00 - Vector3.UP * th, p01 - Vector3.UP * th, p11 - Vector3.UP * th, -fo, [uv[0], uv[1], uv[2]])
				else:
					_quad(mat, 1.0, p00, p01, p11, p10, fo, uv)
					_quad(mat, 0.5, p00 - Vector3.UP * th, p01 - Vector3.UP * th, p11 - Vector3.UP * th, p10 - Vector3.UP * th, -fo, uv)
		# fascia along the eave (the roof's cut edge)
		for ci in M:
			var p0: Vector3 = grid[0][ci]
			var p1: Vector3 = grid[0][ci + 1]
			var oo := Vector3(_edge_out(A, B).x, -0.2, _edge_out(A, B).y)
			_quad(mat, 0.7, p0, p1, p1 - Vector3.UP * th, p0 - Vector3.UP * th, oo, [Vector2(0, 0), Vector2(p0.distance_to(p1) / tile, 0), Vector2(p0.distance_to(p1) / tile, th / tile), Vector2(0, th / tile)])
		# gable verge (rake) for gable roofs: the slope's cut edge at both ends
		if typ == "gable":
			for side in [0, M]:
				for ri in R:
					var p0: Vector3 = grid[ri][side]
					var p1: Vector3 = grid[ri + 1][side]
					var d2 := (B - A).normalized() * (-1.0 if side == 0 else 1.0)
					_quad(mat, 0.7, p0, p1, p1 - Vector3.UP * th, p0 - Vector3.UP * th, Vector3(d2.x, 0, d2.y), [Vector2(0, 0), Vector2(0.1, 0), Vector2(0.1, 0.05), Vector2(0, 0.05)])
	# ridge / hip caps: a thin rounded strip along the ridge for gable / hip (paper ridge roll)
	if typ in ["gable", "hip"] and faces.size() >= 2:
		var r0: Vector2 = faces[0][3]
		var r1: Vector2 = faces[0][2]
		if r0.distance_to(r1) > 1e-4:
			var w := th * 1.4
			var a3 := Vector3(r0.x, top_y + th * 0.6, r0.y)
			var b3 := Vector3(r1.x, top_y + th * 0.6, r1.y)
			var side := (b3 - a3).cross(Vector3.UP).normalized() * w
			_quad(mat, 0.85, a3 + side, b3 + side, b3 - side, a3 - side, Vector3.UP, [Vector2(0, 0), Vector2(a3.distance_to(b3) / tile, 0), Vector2(a3.distance_to(b3) / tile, 0.05), Vector2(0, 0.05)])
			for sgn in [1.0, -1.0]:
				_quad(mat, 0.75, a3 + side * sgn, b3 + side * sgn, b3 + side * sgn - Vector3.UP * th * 1.6, a3 + side * sgn - Vector3.UP * th * 1.6, side * sgn,
					[Vector2(0, 0), Vector2(a3.distance_to(b3) / tile, 0), Vector2(a3.distance_to(b3) / tile, 0.05), Vector2(0, 0.05)])
	return top_y


## Simple solid prism (plinth, platform, pillar): footprint pts from y0 to y1, sides + top.
func _prism(pts_in: PackedVector2Array, y0: float, y1: float, mat: String, shade := 1.0, top := true) -> void:
	var pts := pts_in.duplicate()
	var area := 0.0
	for i in pts.size():
		area += pts[i].x * pts[(i + 1) % pts.size()].y - pts[(i + 1) % pts.size()].x * pts[i].y
	if area < 0.0:
		pts.reverse()
	var tile := _tile(mat)
	var arc := 0.0
	var c := _centroid(pts)
	for i in pts.size():
		var a := pts[i]
		var b := pts[(i + 1) % pts.size()]
		var L := a.distance_to(b)
		var o2 := _edge_out(a, b)
		_quad(mat, shade, Vector3(a.x, y0, a.y), Vector3(b.x, y0, b.y), Vector3(b.x, y1, b.y), Vector3(a.x, y1, a.y), Vector3(o2.x, 0, o2.y),
			[Vector2(arc / tile, -y0 / tile), Vector2((arc + L) / tile, -y0 / tile), Vector2((arc + L) / tile, -y1 / tile), Vector2(arc / tile, -y1 / tile)])
		if top:
			_tri(mat, shade * 0.95, Vector3(a.x, y1, a.y), Vector3(b.x, y1, b.y), Vector3(c.x, y1, c.y), Vector3.UP, [a / tile, b / tile, c / tile])
		arc += L


func _block(p: Dictionary) -> void:
	var pts := _footprint(p)
	var h := float(p.get("h", 0.6)) * unit
	var thick := float(p.get("thick", 0.04)) * unit
	var mat := str(p.get("wall", "plaster"))
	var y0 := 0.0
	if p.has("plinth"):
		var pl: Dictionary = p["plinth"]
		var ph := float(pl.get("h", 0.05)) * unit
		_prism(_offset(pts, float(pl.get("out", 0.02)) * unit), -0.03 * unit, ph, str(pl.get("mat", "fieldstone")), 1.0)
		y0 = ph
	_walls(pts, y0, y0 + h, thick, mat, p.get("openings", []), not p.has("roof"))
	var y_top := y0 + h
	if p.has("crenel"):
		_crenel(pts, y_top, thick, p["crenel"], mat)
	if p.has("roof"):
		var rc: Dictionary = (p["roof"] as Dictionary).duplicate()
		rc["wall_mat"] = mat
		var up := PackedVector2Array()
		if rc.has("upper_r"):  # skirt roof: the upper storey's footprint (same shape, smaller)
			var q := p.duplicate()
			q.merge(rc.get("upper", {}), true)
			up = _footprint(q)
		var ry := y_top + float(rc.get("lift", 0.0)) * unit
		var top := _roof(pts, ry, rc, up)
		if rc.has("finial"):
			_finial(_centroid(pts), top, str(rc["finial"]), float(rc.get("finial_h", 0.12)) * unit)
	if not p.has("roof") and not p.has("crenel"):
		pass
	_flush_nodes(get_child(get_child_count() - 1) as Node3D)


func _finial(c: Vector2, y: float, card: String, h: float) -> void:
	var cd := _atlas_card(card, h)
	if cd:
		var n := Node3D.new()
		n.position = Vector3(c.x, y - h * 0.15, c.y)
		n.add_child(cd)
		var n2 := Node3D.new()  # a crossed second card so it reads from the side
		n2.position = n.position
		n2.rotation.y = PI * 0.5
		n2.add_child(_atlas_card(card, h))
		_pending_nodes.append(n)
		_pending_nodes.append(n2)


func _pavilion(p: Dictionary) -> void:
	var pts := _footprint(p)
	var hp := float(p.get("platform", 0.1)) * unit
	var pmat := str(p.get("platform_mat", "fieldstone"))
	_prism(_offset(pts, float(p.get("platform_out", 0.06)) * unit), -0.03 * unit, hp, pmat)
	var deck := str(p.get("deck", "planks"))
	if deck != "":
		var c := _centroid(pts)
		var D := _offset(pts, 0.0)
		var tile := _tile(deck)
		for i in D.size():
			var a := D[i]
			var b := D[(i + 1) % D.size()]
			_tri(deck, 1.0, Vector3(a.x, hp + 0.002, a.y), Vector3(b.x, hp + 0.002, b.y), Vector3(c.x, hp + 0.002, c.y), Vector3.UP, [a / tile, b / tile, c / tile])
	var h := float(p.get("h", 0.5)) * unit
	var pr := float(p.get("pillar_r", 0.025)) * unit
	var pmat2 := str(p.get("pillar", "lacquer"))
	var inset := _offset(pts, -pr * 1.5)
	for q in inset:
		var col := PackedVector2Array()
		for k in 8:
			var a := TAU * k / 8.0
			col.append(q + Vector2(cos(a), sin(a)) * pr)
		_prism(col, hp, hp + h, pmat2, 1.0, false)
	# beam band under the eaves (painted)
	var bh := float(p.get("beam_h", 0.06)) * unit
	var bmat := str(p.get("beam", "dancheong"))
	var outer := _offset(pts, -pr * 0.3)
	var innr := _offset(pts, -pr * 2.8)
	var tile := _tile(bmat)
	for i in outer.size():
		var a := outer[i]
		var b := outer[(i + 1) % outer.size()]
		var ai := innr[i]
		var bi := innr[(i + 1) % innr.size()]
		var o2 := _edge_out(a, b)
		var y0 := hp + h - bh
		var y1 := hp + h
		var L := a.distance_to(b)
		var uv := [Vector2(0, 0), Vector2(L / tile, 0), Vector2(L / tile, -bh / tile), Vector2(0, -bh / tile)]
		_quad(bmat, 1.0, Vector3(a.x, y0, a.y), Vector3(b.x, y0, b.y), Vector3(b.x, y1, b.y), Vector3(a.x, y1, a.y), Vector3(o2.x, 0, o2.y), uv)
		_quad(bmat, 0.7, Vector3(ai.x, y0, ai.y), Vector3(bi.x, y0, bi.y), Vector3(bi.x, y1, bi.y), Vector3(ai.x, y1, ai.y), -Vector3(o2.x, 0, o2.y), uv)
		_quad(bmat, 0.5, Vector3(a.x, y0, a.y), Vector3(b.x, y0, b.y), Vector3(bi.x, y0, bi.y), Vector3(ai.x, y0, ai.y), Vector3.DOWN, uv)
	# railing cards along the edges, a gap on the front edge (the steps)
	var rail := str(p.get("railing", ""))
	if rail != "":
		var rh := float(p.get("railing_h", 0.09)) * unit
		var R := _offset(pts, -pr * 0.2)
		for i in R.size():
			var a := R[i]
			var b := R[(i + 1) % R.size()]
			var o2 := _edge_out(a, b)
			if o2.y > 0.9 and p.get("steps", true):
				continue
			var cd := _atlas_card(rail, rh, a.distance_to(b) - pr * 2.0)
			if cd:
				var n := Node3D.new()
				var m := (a + b) * 0.5
				n.position = Vector3(m.x, hp, m.y)
				n.rotation.y = atan2(o2.x, o2.y)
				n.add_child(cd)
				_pending_nodes.append(n)
	if p.get("steps", true):
		var front := -1
		for i in pts.size():
			if _edge_out(pts[i], pts[(i + 1) % pts.size()]).y > 0.9:
				front = i
		if front >= 0:
			var a := pts[front]
			var b := pts[(front + 1) % pts.size()]
			var m := (a + b) * 0.5
			var sw := minf(a.distance_to(b) * 0.6, 0.3 * unit)
			var po := float(p.get("platform_out", 0.06)) * unit
			var nsteps := 3
			for k in nsteps:
				var y1 := hp * float(nsteps - k) / nsteps
				var z0 := m.y + po + k * hp * 0.9
				var z1 := z0 + hp * 0.9
				var st := PackedVector2Array([Vector2(m.x - sw * 0.5, z1), Vector2(m.x + sw * 0.5, z1), Vector2(m.x + sw * 0.5, z0 - 0.01 * unit), Vector2(m.x - sw * 0.5, z0 - 0.01 * unit)])
				_prism(st, -0.02 * unit, y1, pmat)
	var rc: Dictionary = (p.get("roof", {"type": "pyramid"}) as Dictionary).duplicate()
	var top := _roof(pts, hp + h, rc)
	if rc.has("finial"):
		_finial(_centroid(pts), top, str(rc["finial"]), float(rc.get("finial_h", 0.12)) * unit)
	_flush_nodes(get_child(get_child_count() - 1) as Node3D)


func _wall_run(p: Dictionary) -> void:
	var a: Array = p.get("from", [0, 0])
	var b: Array = p.get("to", [1, 0])
	var A := Vector2(float(a[0]), float(a[1])) * unit
	var B := Vector2(float(b[0]), float(b[1])) * unit
	var t := float(p.get("thick", 0.12)) * unit
	var d := (B - A).normalized()
	var nrm := Vector2(d.y, -d.x)
	var side := float(p.get("outer", 1.0))  # which side the battlements face: +1 = right of a->b
	var pts := PackedVector2Array([A + nrm * t * 0.5, B + nrm * t * 0.5, B - nrm * t * 0.5, A - nrm * t * 0.5])
	var area := 0.0
	for i in 4:
		area += pts[i].x * pts[(i + 1) % 4].y - pts[(i + 1) % 4].x * pts[i].y
	if area < 0.0:
		pts.reverse()
	var h := float(p.get("h", 0.5)) * unit
	var mat := str(p.get("wall", "ashlar"))
	_prism(pts, -0.03 * unit, h, mat)
	if p.has("crenel"):
		# battlements on both long sides (the outer face higher), a walkway between
		var cfg: Dictionary = p["crenel"]
		for sgn in [1.0, -1.0]:
			var off: Vector2 = nrm * (t * 0.5) * float(sgn) * side
			var run := PackedVector2Array([A + off, B + off, B + off - nrm * sgn * side * float(cfg.get("d", 0.04)) * unit, A + off - nrm * sgn * side * float(cfg.get("d", 0.04)) * unit])
			var ar := 0.0
			for i in 4:
				ar += run[i].x * run[(i + 1) % 4].y - run[(i + 1) % 4].x * run[i].y
			if ar < 0.0:
				run.reverse()
			_crenel_line(A + off, B + off, -nrm * sgn * side, h, cfg, mat)


## Merlons along one line (a->b) on its inward side `inw`.
func _crenel_line(a: Vector2, b: Vector2, inw: Vector2, y: float, cfg: Dictionary, mat: String) -> void:
	var mh := float(cfg.get("h", 0.08)) * unit
	var mw := float(cfg.get("w", 0.08)) * unit
	var gap := float(cfg.get("gap", 0.06)) * unit
	var depth := float(cfg.get("d", 0.04)) * unit
	var tile := _tile(mat)
	var L := a.distance_to(b)
	var dir := (b - a) / maxf(L, 1e-6)
	var count := maxi(1, int(floor((L + gap) / (mw + gap))))
	var s := (L - (count * mw + (count - 1) * gap)) * 0.5
	for k in count:
		var s0 := s + k * (mw + gap)
		var q := [a + dir * s0, a + dir * (s0 + mw), a + dir * (s0 + mw) + inw * depth, a + dir * s0 + inw * depth]
		var Bv := []
		var Tv := []
		for v: Vector2 in q:
			Bv.append(Vector3(v.x, y - 0.002, v.y))
			Tv.append(Vector3(v.x, y + mh, v.y))
		var c3 := ((Tv[0] as Vector3) + (Tv[2] as Vector3)) * 0.5
		for e in 4:
			var e1 := (e + 1) % 4
			var fo: Vector3 = ((Bv[e] as Vector3) + (Bv[e1] as Vector3)) * 0.5 - Vector3(c3.x, y, c3.z)
			var lw: float = (Bv[e] as Vector3).distance_to(Bv[e1])
			_quad(mat, 1.0, Bv[e], Bv[e1], Tv[e1], Tv[e], fo, [Vector2(0, 0), Vector2(lw / tile, 0), Vector2(lw / tile, -mh / tile), Vector2(0, -mh / tile)])
		_quad(mat, 0.92, Tv[0], Tv[1], Tv[2], Tv[3], Vector3.UP, [Vector2(0, 0), Vector2(mw / tile, 0), Vector2(mw / tile, depth / tile), Vector2(0, depth / tile)])


func _gate(p: Dictionary, node: Node3D) -> void:
	var q := p.duplicate(true)
	var s: Array = q.get("size", [0.6, 0.4])
	var gw := float(q.get("gate_w", 0.26))
	var gh := float(q.get("gate_h", 0.36))
	var ops: Array = q.get("openings", [])
	# front edge index of a rect footprint is 0 (from (-w, d) to (w, d)), back is 2
	ops.append({"edge": 0, "u": 0.5, "w": gw, "h": gh, "kind": "gate"})
	ops.append({"edge": 2, "u": 0.5, "w": gw, "h": gh, "kind": "gate"})
	q["openings"] = ops
	_block(q)
	# the passage: walls and vault through the depth (a tunnel joining the two arches)
	var mat := str(q.get("wall", "ashlar"))
	var tile := _tile(mat)
	var hw := gw * 0.5 * unit
	var d := float(s[1]) * 0.5 * unit
	var spring := (gh - gw * 0.5) * unit
	var r := hw
	var y0 := 0.0
	if q.has("plinth"):
		y0 = float((q["plinth"] as Dictionary).get("h", 0.05)) * unit
	var thick := float(q.get("thick", 0.04)) * unit
	var z0 := d - thick
	var z1 := -d + thick
	for sgn in [-1.0, 1.0]:
		var x: float = hw * float(sgn)
		_quad(mat, 0.6, Vector3(x, y0, z0), Vector3(x, y0, z1), Vector3(x, y0 + spring, z1), Vector3(x, y0 + spring, z0), Vector3(-sgn, 0, 0),
			[Vector2(0, 0), Vector2((z0 - z1) / tile, 0), Vector2((z0 - z1) / tile, -spring / tile), Vector2(0, -spring / tile)])
	var segs := 10
	for k in segs:
		var a0 := PI * k / segs
		var a1 := PI * (k + 1) / segs
		var p0 := Vector3(cos(a0) * r, y0 + spring + sin(a0) * r, 0)
		var p1 := Vector3(cos(a1) * r, y0 + spring + sin(a1) * r, 0)
		var inward := -Vector3((cos(a0) + cos(a1)) * 0.5, (sin(a0) + sin(a1)) * 0.5, 0)
		_quad(mat, 0.55, p0 + Vector3(0, 0, z0), p1 + Vector3(0, 0, z0), p1 + Vector3(0, 0, z1), p0 + Vector3(0, 0, z1), inward,
			[Vector2(0, 0), Vector2(0.1, 0), Vector2(0.1, (z0 - z1) / tile), Vector2(0, (z0 - z1) / tile)])
	# floor of the passage (the road through)
	_quad(str(q.get("floor", "fieldstone")), 0.8, Vector3(-hw, y0 + 0.002, d), Vector3(hw, y0 + 0.002, d), Vector3(hw, y0 + 0.002, -d), Vector3(-hw, y0 + 0.002, -d), Vector3.UP,
		[Vector2(0, 0), Vector2(gw * unit / tile, 0), Vector2(gw * unit / tile, 2 * d / tile), Vector2(0, 2 * d / tile)])
	# portcullis: a card in the passage just inside the front arch, slides up (state "portcullis": 0 down .. 1 up)
	if q.has("portcullis"):
		var pc := _atlas_card(str(q["portcullis"]), gh * unit, gw * unit + 0.004)
		if pc:
			var holder := Node3D.new()
			holder.name = "Portcullis"
			holder.position = Vector3(0, y0, d - thick - 0.012 * unit)
			holder.add_child(pc)
			_pending_nodes.append(holder)
			movers["portcullis"] = [holder, "lift", {"h": gh * unit * 0.85, "y0": y0}]
	# drawbridge: a plank card hinged at the gate sill, up = closing the gateway, down = lying across the moat
	if q.has("drawbridge"):
		var db := _atlas_card(str(q["drawbridge"]), gh * unit * 1.05, gw * unit + 0.02 * unit)
		if db:
			var hinge := Node3D.new()
			hinge.name = "Drawbridge"
			hinge.position = Vector3(0, y0, d + 0.006 * unit)
			hinge.add_child(db)
			_pending_nodes.append(hinge)
			movers["drawbridge"] = [hinge, "fold", {}]
	_flush_nodes(node)


func _stairs(p: Dictionary) -> void:
	var n := int(p.get("steps", 5))
	var w := float(p.get("w", 0.2)) * unit
	var rise := float(p.get("rise", 0.04)) * unit
	var run := float(p.get("run", 0.05)) * unit
	var mat := str(p.get("mat", "fieldstone"))
	for k in n:
		var z0 := k * run
		var pts := PackedVector2Array([Vector2(-w * 0.5, -z0 - run), Vector2(w * 0.5, -z0 - run), Vector2(w * 0.5, 0.0), Vector2(-w * 0.5, 0.0)])
		var area := 0.0
		for i in 4:
			area += pts[i].x * pts[(i + 1) % 4].y - pts[(i + 1) % 4].x * pts[i].y
		if area < 0.0:
			pts.reverse()
		_prism(pts, -0.02 * unit, rise * (k + 1), mat)


func _bridge(p: Dictionary) -> void:
	var a: Array = p.get("from", [0, 0])
	var b: Array = p.get("to", [1, 0])
	var A := Vector2(float(a[0]), float(a[1])) * unit
	var B := Vector2(float(b[0]), float(b[1])) * unit
	var y := float(p.get("y", 0.4)) * unit
	var w := float(p.get("w", 0.12)) * unit
	var th := float(p.get("thick", 0.04)) * unit
	var d := (B - A).normalized()
	var nrm := Vector2(d.y, -d.x) * w * 0.5
	var pts := PackedVector2Array([A + nrm, B + nrm, B - nrm, A - nrm])
	var area := 0.0
	for i in 4:
		area += pts[i].x * pts[(i + 1) % 4].y - pts[(i + 1) % 4].x * pts[i].y
	if area < 0.0:
		pts.reverse()
	_prism(pts, y - th, y, str(p.get("mat", "planks")))
	# underside
	var mat := str(p.get("mat", "planks"))
	_quad(mat, 0.5, Vector3(pts[0].x, y - th, pts[0].y), Vector3(pts[1].x, y - th, pts[1].y), Vector3(pts[2].x, y - th, pts[2].y), Vector3(pts[3].x, y - th, pts[3].y), Vector3.DOWN,
		[Vector2(0, 0), Vector2(1, 0), Vector2(1, 1), Vector2(0, 1)])


func _flag(p: Dictionary, node: Node3D) -> void:
	var h := float(p.get("h", 0.3)) * unit
	var card := _atlas_card(str(p.get("card", "")), h)
	if card == null:
		return
	var sway := Node3D.new()
	sway.name = "Flag"
	sway.add_child(card)
	node.add_child(sway)
	var n2 := _atlas_card(str(p.get("card", "")), h)  # crossed copy: reads from the side too
	if n2:
		n2.rotation.y = PI * 0.5
		sway.add_child(n2)
	_flags.append(sway)


## Windmill sails: four blades (a frame of `frame` and a cloth panel of `cloth`) round a hub, turning about the part's
## local z (place the part on the cap's front, `base` at the hub height).
func _sails(p: Dictionary) -> void:
	var L := float(p.get("len", 0.6)) * unit
	var w := float(p.get("w", 0.13)) * unit
	var t := 0.012 * unit
	var cloth := str(p.get("cloth", "plaster"))
	var frame := str(p.get("frame", "planks"))
	for k in 4:
		var b := Basis(Vector3.BACK, TAU * k / 4.0 + PI * 0.25)
		var pts := [Vector2(0.03 * unit, -w * 0.5), Vector2(L, -w * 0.5), Vector2(L, w * 0.5), Vector2(0.03 * unit, w * 0.5)]
		var q := []
		var qb := []
		for v: Vector2 in pts:
			q.append(b * Vector3(v.x, v.y, t))
			qb.append(b * Vector3(v.x, v.y, -t))
		var tile := _tile(cloth)
		var uv := [Vector2(0, 0), Vector2(L / tile, 0), Vector2(L / tile, w / tile), Vector2(0, w / tile)]
		_quad(cloth, 1.0, q[0], q[1], q[2], q[3], b * Vector3.BACK, uv)
		_quad(cloth, 0.8, qb[0], qb[1], qb[2], qb[3], b * Vector3.FORWARD, uv)
		for e in 4:
			var e1 := (e + 1) % 4
			var mid: Vector3 = ((q[e] as Vector3) + (q[e1] as Vector3)) * 0.5
			_quad(frame, 0.9, q[e], q[e1], qb[e1], qb[e], mid, [Vector2(0, 0), Vector2(0.5, 0), Vector2(0.5, 0.05), Vector2(0, 0.05)])
		# the spar down the blade's middle, a little proud of the cloth
		var s0 := b * Vector3(0.0, -0.008 * unit, t * 1.6)
		var s1 := b * Vector3(L * 1.02, -0.008 * unit, t * 1.6)
		var s2 := b * Vector3(L * 1.02, 0.008 * unit, t * 1.6)
		var s3 := b * Vector3(0.0, 0.008 * unit, t * 1.6)
		_quad(frame, 1.0, s0, s1, s2, s3, b * Vector3.BACK, [Vector2(0, 0), Vector2(1, 0), Vector2(1, 0.05), Vector2(0, 0.05)])
	var hub := PackedVector2Array()
	for k in 10:
		var a := TAU * k / 10.0
		hub.append(Vector2(cos(a), sin(a)) * 0.04 * unit)
	for k in 10:
		var a2 := hub[k]
		var b2 := hub[(k + 1) % 10]
		_quad(frame, 0.9, Vector3(a2.x, a2.y, -float(p.get("shaft", 0.18)) * unit), Vector3(b2.x, b2.y, -float(p.get("shaft", 0.18)) * unit), Vector3(b2.x, b2.y, 0.04 * unit), Vector3(a2.x, a2.y, 0.04 * unit),
			Vector3(a2.x + b2.x, a2.y + b2.y, 0), [Vector2(0, 0), Vector2(0.2, 0), Vector2(0.2, 0.2), Vector2(0, 0.2)])
		_tri(frame, 1.0, Vector3(a2.x, a2.y, 0.04 * unit), Vector3(b2.x, b2.y, 0.04 * unit), Vector3(0, 0, 0.04 * unit), Vector3.BACK, [Vector2(0, 0), Vector2(0.2, 0), Vector2(0.1, 0.2)])


func _card(p: Dictionary, node: Node3D) -> void:
	var c := _atlas_card(str(p.get("card", "")), float(p.get("h", 0.2)) * unit, float(p.get("w", -1.0)) * unit if p.has("w") else -1.0)
	if c:
		node.add_child(c)


# ------------------------------------------------------------------ moving parts

## Movable parts: "portcullis" (0 down .. 1 raised), "drawbridge" (0 up, closing the gate .. 1 down across the moat).
func set_state(key: String, v: float, snap := false) -> void:
	_state_t[key] = v
	if snap or not _state.has(key):
		_state[key] = v
		_apply(key)


func _apply(key: String) -> void:
	if not movers.has(key):
		return
	var m: Array = movers[key]
	var n: Node3D = m[0]
	var v := float(_state[key])
	match str(m[1]):
		"lift":
			n.position.y = float(m[2]["y0"]) + float(m[2]["h"]) * v
		"fold":
			n.rotation.x = PI * 0.5 * v


func _process(dt: float) -> void:
	_t += dt
	for k in _state_t:
		var cur := float(_state.get(k, 0.0))
		var tgt := float(_state_t[k])
		if absf(cur - tgt) > 1e-4:
			_state[k] = move_toward(cur, tgt, dt * 0.6)
			_apply(k)
	for n in _spin:
		n.rotation.z -= dt * 0.5
	for i in _flags.size():
		_flags[i].rotation.y = sin(_t * 2.3 + i) * 0.18
