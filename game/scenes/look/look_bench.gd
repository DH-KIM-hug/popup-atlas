extends Node3D
## B_look bench (round 3): a tabletop pop-up spread on LookRig + GroundLayers, dressed from BOTH card
## catalogs (component A's art/cards + the shared art/atlas library). Round-3 changes after the r2 critic:
## ground relief (stacked felt hill tiers + folded tented paper rocks), contact shadows under every card,
## tall slim conifers (2.5-4x bush height) with tree lines on the far hills, dark moss patches under groves,
## hedgerow strips along the path, least-used picking so no motif repeats much, animals near every view.
## Not a shipped scene.

@export var view := 0
@export var seed_value := 4
@export var animate := false

const CATALOGS := ["res://art/cards/catalog.json", "res://art/atlas/catalog.json"]
const WIND_TREE := "res://art/test_props/sw_layer_tree_bent.webp"
## elevation, yaw, distance, fov, focus offset (from the traveller), hero side (+1 right / -1 left)
const VIEWS := [
	[29.0, 0.0, 7.6, 21.0, Vector3(0.0, 0, 0.0), -1.0],
	[26.0, 22.0, 7.4, 21.0, Vector3(-1.6, 0, -0.4), 1.0],
	[31.0, -14.0, 8.2, 21.0, Vector3(1.8, 0, -1.6), -1.0],
	[27.0, -34.0, 7.6, 20.0, Vector3(0.6, 0, -3.6), 1.0],
	[30.0, 10.0, 7.8, 21.0, Vector3(3.2, 0, 2.0), -1.0],
]
## Height multipliers per pool: conifers and big trees stand far above bushes (critic: 2.5-4x).
const POOL_SCALE := {"conifer": 1.55, "tree": 1.25, "autumn": 1.2, "blossom": 1.15}

var rig: LookRig
var ground: GroundLayers
var contact: ContactShadows
var traveller: Node3D
var card_count := 0
var _cat := {}
var _pools := {}  ## pool name -> Array of ids
var _used := {}  ## id -> times used
var _tex := {}
var _placed: Array = []  ## [Vector2 pos, float radius]
var _cam_ground := Vector2(INF, INF)  ## camera position on the page; tall cards keep out of the lens


func _ready() -> void:
	seed(seed_value)
	_load_catalogs()
	ground = GroundLayers.new()
	ground.name = "Ground"
	ground.seed_value = seed_value
	ground.cover_patches = 60
	ground.felt_color = Color("819a78")
	ground.felt_mottle = Color("6a8364")
	ground.path_points = PackedVector2Array([
		Vector2(1.6, 8.0), Vector2(0.4, 4.6), Vector2(-0.2, 1.8), Vector2(0.9, -1.2),
		Vector2(0.2, -4.2), Vector2(-1.6, -6.4), Vector2(-2.4, -8.0)])
	ground.stream_points = PackedVector2Array([
		Vector2(-12.0, 2.6), Vector2(-6.5, 1.2), Vector2(-3.4, -1.8), Vector2(-0.6, -2.9),
		Vector2(3.5, -3.6), Vector2(7.0, -6.0), Vector2(12.0, -7.0)])
	ground.hill_specs = [
		[Vector2(-4.6, -5.0), 2.4, 3], [Vector2(4.6, -6.0), 2.2, 3], [Vector2(7.6, -1.6), 1.9, 2],
		[Vector2(-7.8, -1.0), 1.8, 2], [Vector2(3.4, 0.4), 1.25, 2], [Vector2(-3.2, 3.4), 1.3, 2],
		[Vector2(5.6, 4.6), 1.6, 2], [Vector2(-1.4, -4.6), 0.9, 2], [Vector2(-6.4, 5.0), 1.4, 2],
	]
	add_child(ground)
	contact = ContactShadows.new()
	contact.name = "ContactShadows"
	var tpos := _on_path(1.2)
	traveller = _add_card("res://art/chars/sw_trav_walk.webp", 0.36, tpos, 0.12, 0.008)
	contact.add(tpos, 0.12, 0.16, 0.08, 1.2)
	_reserve(Vector2(tpos.x, tpos.z), 0.3)
	var v: Array = VIEWS[clampi(view, 0, VIEWS.size() - 1)]
	var yw := deg_to_rad(v[1])
	_cam_ground = Vector2(tpos.x, tpos.z) + Vector2(v[4].x, v[4].z) + Vector2(sin(yw), cos(yw)) * float(v[2]) * cos(deg_to_rad(v[0]))
	_dress()
	_life()
	_hero(v)
	contact.commit()
	add_child(contact)
	rig = LookRig.new()
	rig.name = "LookRig"
	rig.elevation_deg = v[0]
	rig.yaw_deg = v[1]
	rig.distance = v[2]
	rig.fov = v[3]
	var focus := Node3D.new()
	focus.name = "Focus"
	add_child(focus)
	focus.global_position = traveller.global_position + v[4]
	rig.focus_target = focus
	add_child(rig)
	print("LOOK_BENCH cards=", card_count, " view=", view, " ids_used=", _used.size(), " hills=", ground._hills.size())
	if animate:
		for h in find_children("*", "PopHinge", true, false):
			var d := Vector2(h.global_position.x, h.global_position.z).length()
			(h as PopHinge).pop_up(0.2 + d * 0.15 + randf() * 0.1)


# ------------------------------------------------------------------ catalog pools

func _load_catalogs() -> void:
	for cpath in CATALOGS:
		var f := FileAccess.open(cpath, FileAccess.READ)
		if f == null:
			push_error("look_bench: no catalog " + cpath)
			continue
		for it in JSON.parse_string(f.get_as_text()):
			var d: Dictionary = it
			if str(d.get("season", "")) == "winter":
				continue
			var p := str(d["path"])
			if not p.begins_with("res://"):
				p = "res://" + p
			d["path"] = p
			if not d.has("aspect"):
				var px: Array = d.get("px", [1, 1])
				d["aspect"] = float(px[0]) / maxf(1.0, float(px[1]))
			_cat[d["id"]] = d
			var pool := _pool_of(d)
			if pool != "":
				if not _pools.has(pool):
					_pools[pool] = []
				_pools[pool].append(d["id"])


func _pool_of(d: Dictionary) -> String:
	var cat := str(d["category"])
	var sheet := str(d.get("sheet", ""))
	var label := str(d.get("label", d["id"]))
	if cat == "conifer" or (cat == "tree" and (sheet == "forest_conifer" or "pine" in label or "cypress" in label)):
		return "conifer" if float(d["height_units"]) >= 0.6 else "sapling"
	if cat == "tree":
		if float(d["height_units"]) < 0.55:
			return "sapling"
		if "bamboo" in label or "willow" in label:
			return "tree"
		if sheet == "autumn" or "terracotta" in label or "ochre" in str(d["id"]) or "golden" in label:
			return "autumn"
		if sheet == "spring_blossom" or "blossom" in label or "apple" in str(d["id"]):
			return "blossom"
		return "tree"
	match cat:
		"bush":
			return "bush"
		"hedge":
			return "hedge"
		"flower":
			return "flower"
		"grass":
			return "grass"
		"mushroom":
			return "mushroom"
		"rock":
			return "rock"
		"reeds":
			return "reeds"
		"water":
			return "reeds" if str(d["id"]).begins_with("water_") else ""
		"animal":
			if "duck" in label or "goose" in label or "heron" in label or "frog" in label or "goose" in str(d["id"]):
				return "water_animal"
			if "fox" in label or "deer" in label or "rabbit" in label or "hedgehog" in label or "squirrel" in label or "owl" in label or "bunny" in label or "snail" in label:
				return "wild_animal"
			return "farm_animal"
		"prop":
			return "prop"
		"fence":
			return "fence"
		"crop", "field":
			return "crop"
	return ""


## Least-used id from a pool (ties broken at random) so no one motif dominates a frame.
func _pick(pool: String) -> String:
	var ids: Array = _pools.get(pool, [])
	if ids.is_empty():
		return ""
	var best := ""
	var bu := 1 << 30
	for k in 6:
		var id: String = ids[randi() % ids.size()]
		var u: int = _used.get(id, 0)
		if u < bu:
			bu = u
			best = id
	return best


# ------------------------------------------------------------------ placement

func _on_path(z: float) -> Vector3:
	var best := Vector3.ZERO
	var bd := INF
	for p in ground.path_centre_3d():
		if absf(p.z - z) < bd:
			bd = absf(p.z - z)
			best = p
	return best


func _reserve(p: Vector2, r: float) -> void:
	_placed.append([p, r])


func _free(p: Vector2, r: float) -> bool:
	if not ground.on_page(p, 0.2):
		return false
	if ground.path_distance(p) < r * 0.5 + 0.04 or ground.stream_distance(p) < r * 0.5 + 0.05:
		return false
	for q in _placed:
		if (q[0] as Vector2).distance_to(p) < (r + float(q[1])) * 0.5:
			return false
	return true


## Place a card from `pool` (or an explicit id) near c within spread.
func _try(pool_or_id: String, c: Vector2, spread: float, s0 := 0.8, s1 := 1.2, yaw_bias := 0.0, pack := 1.0) -> bool:
	var id := pool_or_id if _cat.has(pool_or_id) else _pick(pool_or_id)
	if id == "" or not _cat.has(id):
		return false
	var it: Dictionary = _cat[id]
	var pool := _pool_of(it)
	var h: float = float(it["height_units"]) * randf_range(s0, s1) * float(POOL_SCALE.get(pool, 1.0))
	var w: float = h * float(it.get("aspect", 1.0))
	var r := clampf(w * 0.6 * pack, 0.07, 0.9)
	for t in 14:
		var q := c + Vector2(randf_range(-spread, spread), randf_range(-spread, spread) * 0.8)
		var cd := q.distance_to(_cam_ground)
		if (h > 0.42 and cd < 5.2) or (h > 0.25 and cd < 3.9):
			continue
		if _free(q, r):
			_reserve(q, r)
			var cross: bool = bool(it.get("cross_slot", false)) or pool in ["conifer", "tree", "autumn", "blossom"]
			_place(it["path"], h, q, randf_range(-0.4, 0.4) + yaw_bias, cross, w)
			_used[id] = int(_used.get(id, 0)) + 1
			return true
	return false


func _place(path: String, h: float, q: Vector2, yaw: float, cross := false, w := -1.0) -> Node3D:
	var pos := Vector3(q.x, ground.surface_y(q), q.y)
	var thick := clampf(h * 0.024, 0.008, 0.03)  # ~2.4 % of height: the cream core reads on the rim
	if w < 0.0:
		w = h * 0.8
	if cross:
		contact.add_round(pos, clampf(w * 0.32, 0.06, 0.3), 1.0)
		return _add_cross(path, h, pos, yaw, thick)
	contact.add(pos, yaw, w, clampf(h * 0.35, 0.04, 0.16), 1.0)
	return _add_card(path, h, pos, yaw, thick)


func _dress() -> void:
	# --- folded paper rock clusters (tented card), the strongest relief motif in the footage.
	for c in [Vector2(-3.6, -3.4), Vector2(2.6, -1.2), Vector2(-5.6, 1.6), Vector2(6.2, -3.0), Vector2(-2.4, 4.8),
			Vector2(4.4, 2.2), Vector2(0.9, -6.2), Vector2(-7.2, -4.2), Vector2(2.0, 6.2), Vector2(-1.4, -1.6)]:
		_rock_cluster(c, randi_range(3, 5))
	# --- rest stop by the traveller: bench, lantern, signpost, a few flowers.
	var t := Vector2(traveller.position.x, traveller.position.z)
	var side := Vector2(0.62, -0.1)
	_try("village_bench", t + side, 0.05, 1.0, 1.1)
	_try("village_lantern_post", t + side + Vector2(0.35, -0.3), 0.05, 0.95, 1.0)
	_try("village_signpost", t + Vector2(-0.6, -0.5), 0.05, 0.9, 1.0)
	for k in 5:
		_try("flower", t + Vector2(-0.6, 0.3), 0.4, 0.8, 1.1)
		_try("grass", t + side + Vector2(0.2, 0.4), 0.35, 0.8, 1.1)
	# --- tall conifer tree lines on the far hills (silhouettes in the top third).
	for c in [Vector2(-4.6, -5.4), Vector2(4.6, -6.3), Vector2(7.6, -1.8), Vector2(-7.8, -1.2), Vector2(-1.4, -4.8)]:
		ground.add_patch(c + Vector2(0, 0.2), 1.0, 5)
		for i in 14:
			_try("conifer", c, 1.7, 0.8, 1.35, 0.0, 0.7)
		for i in 10:
			_try("sapling" if i % 3 == 0 else "bush", c + Vector2(0, 0.5), 1.8, 0.8, 1.2)
	# --- autumn grove, blossom orchard, mixed copses: each on a dark moss patch, with a skirt.
	_grove(Vector2(2.7, -0.4), ["autumn", "autumn", "tree"], ["bush", "mushroom", "grass", "flower"], 6)
	_grove(Vector2(5.6, 0.8), ["autumn", "conifer"], ["bush", "crop", "rock"], 4)
	_grove(Vector2(-2.6, 2.6), ["blossom", "blossom", "tree"], ["bush", "flower", "flower", "grass"], 5)
	_grove(Vector2(-5.2, 4.4), ["blossom", "tree", "conifer"], ["bush", "flower", "farm_animal"], 4)
	for c in [Vector2(-1.6, -0.6), Vector2(1.6, 1.6), Vector2(-3.4, 0.4), Vector2(3.4, -2.2), Vector2(-0.4, 4.0),
			Vector2(-3.0, -3.0), Vector2(1.0, -5.4), Vector2(5.4, -1.4), Vector2(-6.2, 2.6), Vector2(-1.0, 6.0),
			Vector2(3.0, 5.6), Vector2(6.8, 2.8), Vector2(-7.0, 0.0), Vector2(-4.4, -1.4)]:
		_grove(c, ["conifer", "tree", "conifer", "autumn", "blossom"], ["bush", "grass", "mushroom", "flower", "rock", "sapling"], randi_range(3, 6))
	# --- pasture behind a fence (right, near).
	var pc := Vector2(3.6, 3.4)
	for i in 5:
		var fp := pc + Vector2(-1.4 + i * 0.48, -0.8 + i * 0.04)
		if _free(fp, 0.22):
			_reserve(fp, 0.22)
			_place(_cat["fence_split_rail"]["path"], 0.17, fp, 0.05)
	for k in 7:
		_try("farm_animal", pc + Vector2(0, 0.2), 0.8, 0.95, 1.1)
	for k in 3:
		_try("crop", pc + Vector2(0.4, 0.6), 0.7, 0.9, 1.1)
	_try("village_well", Vector2(1.7, 4.0), 0.25, 0.95, 1.05)
	_try("village_trough", Vector2(2.2, 4.3), 0.2)
	_try("fence_gate", Vector2(1.9, 2.75), 0.1)
	# --- stream banks: reed clumps; water birds on the edge.
	for k in 22:
		var q := _bank_point(randf_range(-9.5, 9.5), 0.12)
		if q == Vector2.INF:
			continue
		for j in randi_range(2, 4):
			_try("reeds", q, 0.22, 0.8, 1.15)
	# --- the windswept 해와 바람 trees: a short windbreak upstream (keeps the r1 tree style).
	for k in 4:
		var q := Vector2(-5.5 + k * 0.75, -0.2 + randf_range(-0.3, 0.3))
		var h := 0.95 * randf_range(0.9, 1.2)
		if _free(q, 0.55):
			_reserve(q, 0.55)
			_place(WIND_TREE, h, q, randf_range(-0.2, 0.2), true, h * 0.7)
	# --- hedgerow strips along the path, with gaps (footage: low scalloped hedges line the path).
	var pl := ground.path_centre_3d()
	for i in range(0, pl.size() - 1, 4):
		if randf() < 0.35:
			continue
		var a := Vector2(pl[i].x, pl[i].z)
		var b := Vector2(pl[i + 1].x, pl[i + 1].z)
		var tn := (b - a).normalized()
		for sd: float in [-1.0, 1.0]:
			if randf() < 0.4:
				continue
			var nn := Vector2(-tn.y, tn.x) * sd
			var c := a + nn * (ground.path_width * 0.5 + 0.16)
			var yaw := atan2(-tn.y, tn.x)  # card plane along the path
			var pool := "hedge" if randf() < 0.55 else ("bush" if randf() < 0.6 else "flower")
			_try(pool, c, 0.04, 0.9, 1.1, yaw, 0.5)
	# --- the arch bridge where the path crosses the stream.
	_bridge()
	# --- meadow: small clumps scattered with open felt between them.
	for k in 480:
		var c := Vector2(randf_range(-9.0, 9.0), randf_range(-6.8, 6.8))
		var pools := ["flower", "grass", "bush", "flower", "mushroom", "grass", "rock", "sapling"]
		var base: String = pools[randi() % pools.size()]
		for j in randi_range(2, 5):
			_try(base if j < 2 else pools[randi() % pools.size()], c, 0.3, 0.8, 1.15)


func _rock_cluster(c: Vector2, n: int) -> void:
	var tints := [Color("7a8670"), Color("6d7c66"), Color("848b72"), Color("75816c"), Color("8a8670")]
	for i in n:
		var s := randf_range(0.14, 0.42) * (1.3 if i == 0 else 1.0)
		for t in 10:
			var q := c + Vector2(randf_range(-0.7, 0.7), randf_range(-0.5, 0.5))
			if _free(q, s * 1.8):
				_reserve(q, s * 1.8)
				ground.add_folded_rock(q, s, randf() * TAU, tints[randi() % tints.size()])
				contact.add_round(Vector3(q.x, ground.surface_y(q), q.y), s * 1.3, 0.8)
				break
	for i in n + 2:
		_try("grass" if i % 2 == 0 else "bush", c, 0.8, 0.8, 1.1)


func _bridge() -> void:
	var pl0 := ground.path_centre_3d()
	var bi := 0
	var bd := INF
	for i in pl0.size():
		var d := absf(ground.stream_distance(Vector2(pl0[i].x, pl0[i].z)) + ground.stream_width * 0.5)
		if d < bd:
			bd = d
			bi = i
	var bt := Vector2(pl0[mini(bi + 1, pl0.size() - 1)].x - pl0[maxi(bi - 1, 0)].x, pl0[mini(bi + 1, pl0.size() - 1)].z - pl0[maxi(bi - 1, 0)].z).normalized()
	var byaw := atan2(bt.y, -bt.x)
	if cos(byaw) < 0.0:
		byaw += PI
	for sd: float in [-1.0, 1.0]:
		var bq: Vector2 = Vector2(pl0[bi].x, pl0[bi].z) + Vector2(-bt.y, bt.x) * sd * ground.path_width * 0.45
		_reserve(bq, 0.5)
		_add_card(_cat["bridge_arch_cream"]["path"], 0.3, Vector3(bq.x, 0.03, bq.y), byaw, 0.016)


## Animals and small life near every camera focus so each view has 5-10 things to find.
func _life() -> void:
	var t := Vector2(traveller.position.x, traveller.position.z)
	for v in VIEWS:
		var f: Vector2 = t + Vector2(v[4].x, v[4].z)
		for k in 3:
			_try("wild_animal", f + Vector2(randf_range(-1.6, 1.6), randf_range(-1.2, 0.6)), 0.5, 1.0, 1.25)
		for k in 3:
			_try("farm_animal", f + Vector2(randf_range(-1.8, 1.8), randf_range(-1.0, 1.0)), 0.5, 1.0, 1.2)
		for k in 3:
			_try("prop", f + Vector2(randf_range(-1.8, 1.8), randf_range(-1.2, 1.0)), 0.5, 0.95, 1.1)
	for k in 10:
		var q := _bank_point(randf_range(-6.0, 6.0), 0.03)
		if q != Vector2.INF:
			_try("water_animal", q, 0.08, 1.0, 1.2)


func _bank_point(x: float, off: float) -> Vector2:
	for t in 60:
		var q := Vector2(x, randf_range(-7.0, 7.0))
		if absf(ground.stream_distance(q) - off) < 0.08:
			return q
	return Vector2.INF


func _grove(c: Vector2, trees: Array, skirt: Array, n: int) -> void:
	ground.add_patch(c + Vector2(0, 0.15), randf_range(0.7, 1.0), 4 if randf() < 0.4 else 5)
	var lean := randf_range(-0.15, 0.15)
	for i in n:
		_try(trees[randi() % trees.size()], c, 0.75, 0.7, 1.35, lean + randf_range(-0.3, 0.3), 0.75)
	for i in n * 3 + 4:
		_try(skirt[randi() % skirt.size()], c + Vector2(0, 0.35), 0.95, 0.8, 1.2)


## Big near-foreground cards toward the camera so the near blur reads as a lens, not a filter.
func _hero(v: Array) -> void:
	var yaw := deg_to_rad(v[1])
	var to_cam := Vector2(sin(yaw), cos(yaw))
	var right := Vector2(cos(yaw), -sin(yaw))
	var f := Vector2(traveller.position.x, traveller.position.z) + Vector2(v[4].x, v[4].z)
	var q := f + to_cam * 1.9 + right * float(v[5]) * 1.0
	if ground.path_distance(q) < 0.4:
		q += right * float(v[5]) * 0.6
	_place(_cat["mushroom_red_cluster"]["path"], 0.5, q, yaw + 0.15)
	var q2 := f + to_cam * 2.0 - right * float(v[5]) * 1.25
	if ground.path_distance(q2) > 0.3:
		_place(_cat["forest_conifer_04"]["path"], 0.75, q2 - to_cam * 0.3, yaw - 0.2, true, 0.3)
	var q3 := f + to_cam * 1.6 + right * float(v[5]) * 1.7
	if ground.path_distance(q3) > 0.3:
		_place(_cat["bush_fern"]["path"], 0.45, q3, yaw)


func _hinge(base: Node3D, h: float) -> PopHinge:
	var hinge := PopHinge.new()
	hinge.start_up = not animate
	hinge.weight = clampf(h / 0.4, 0.4, 2.5)
	base.add_child(hinge)
	return hinge


func _base(pos: Vector3, yaw: float) -> Node3D:
	var base := Node3D.new()
	base.position = pos
	base.rotation.y = yaw
	base.rotation.z = randf_range(-0.035, 0.035)  # hand-set cards never stand perfectly plumb
	add_child(base)
	return base


func _tex_of(path: String) -> Texture2D:
	if not _tex.has(path):
		_tex[path] = load(path)
	return _tex[path]


func _add_card(path: String, h: float, pos: Vector3, yaw: float, thick := 0.012) -> Node3D:
	var base := _base(pos, yaw)
	var hinge := _hinge(base, h)
	var card := PaperCard.new()
	card.texture = _tex_of(path)
	card.height = h
	card.thickness = thick
	card.back_print = true  # hedgerows/props are seen from both sides across the five views
	hinge.add_child(card)
	card_count += 1
	return base


func _add_cross(path: String, h: float, pos: Vector3, yaw: float, thick: float) -> Node3D:
	var base := _base(pos, yaw)
	var hinge := _hinge(base, h)
	var cc := CrossCard.new()
	cc.texture_a = _tex_of(path)
	cc.height = h
	cc.thickness = thick
	hinge.add_child(cc)
	card_count += 2
	return base
