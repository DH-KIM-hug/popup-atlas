extends Node3D
## Card-art bench (component A), round 2. One pop-up spread (22 x 15 units) on B's LookRig + GroundLayers,
## dressed densely with the 해와 바람 card kit (res://art/cards/catalog.json):
##   near-left  village edge (cottages, well, lanterns with real light, fences, yard props, hens)
##   near-right wheat field (broken rows of varied length, stooks, haystacks, bales, hay cart)
##   middle     stream with reed beds, lily pads, ducks, stepping stones, plank bridge at the path crossing
##   far-left   sheep meadow;  far-right  forest edge (mixed conifers + round trees, mushrooms, ferns)
##   back edge  three rows of layered hill cards, plus low hill layers in the middle distance.
## Props are planted in overlapping clusters of 3-7 with mixed scale (0.7-1.4x); free felt is then gap-filled.
## `view` picks one of five camera stations along the path; the traveller stands at that station.
## The r1 version (own lights/camera, flat page) is superseded; r1 fix of the lead bench's
## `_add_card` (position on the yawed base, not on the hinge) is kept by construction.

@export_range(0, 4) var view := 0
@export var seed_value := 7
@export var animate := false

const CATALOG := "res://art/cards/catalog.json"
const TRAVELLER := "res://art/chars/sw_trav_walk.webp"
## r3: brief says 0.36; r2 critic: "make the character ~1.8-2x larger, on a third" -> 0.6 in the bench only (proposal).
const TRAVELLER_H := 0.6
## focus (x, z), elevation, yaw, distance, fov, hero side (+1: hero on the left third, scene opens to the right)
## r3: closer and lower (r2 was 10-10.5 units away and read as a top-down map; the footage is a low macro camera
## with the horizon/backdrop in frame).
const VIEWS := [
	[Vector2(-0.6, 4.4), 22.0, 18.0, 6.4, 21.0, -1.0],   # village edge
	[Vector2(1.4, 2.4), 21.0, -24.0, 6.4, 21.0, 1.0],    # wheat field
	[Vector2(0.3, -0.6), 22.0, 58.0, 6.2, 21.0, -1.0],   # stream + bridge seen from the side
	[Vector2(-0.6, -2.7), 21.0, 22.0, 6.4, 21.0, 1.0],   # meadow with sheep, hills behind
	[Vector2(-0.6, -3.5), 22.0, -28.0, 6.2, 21.0, -1.0], # forest edge, hills behind
]

var rig: LookRig
var ground: GroundLayers
var traveller: Node3D
var card_count := 0
var _cat := {}
var _tex := {}
var _placed: Array = []  ## [Vector2 pos, float radius]
var _face := 0.0  ## view yaw (rad): cards face the reader's side of the page, like a pop-up spread
var contact: ContactShadows
var _used := {}  ## id -> times placed (r3: least-used picking, critic "cap repeats at 2-3 per screen")
var _cam_ground := Vector2(INF, INF)
var _focus2 := Vector2.ZERO
var _cur_h := 0.0


func _ready() -> void:
	seed(seed_value)
	_load_catalog()
	ground = GroundLayers.new()
	ground.name = "Ground"
	ground.seed_value = seed_value
	ground.cover_patches = 70
	ground.felt_color = Color("819a78")
	ground.felt_mottle = Color("6a8364")
	# stacked felt hill tiers (B's GroundLayers): relief in meadow, forest and behind the village
	ground.hill_specs = [
		[Vector2(-4.8, -3.9), 1.9, 3], [Vector2(4.8, -4.6), 2.0, 3], [Vector2(-8.0, 1.8), 1.6, 2],
		[Vector2(8.4, 0.6), 1.5, 2], [Vector2(-6.4, 6.0), 1.2, 2], [Vector2(-1.6, -6.2), 1.0, 2],
	]
	ground.path_width = 0.44  # r3: the close camera made the 0.56 path an empty cream band
	ground.path_points = PackedVector2Array([
		Vector2(2.2, 8.0), Vector2(1.0, 5.4), Vector2(0.1, 2.8), Vector2(0.6, 0.4),
		Vector2(0.1, -2.2), Vector2(-1.1, -4.4), Vector2(-0.4, -6.4), Vector2(-1.4, -8.0)])
	ground.stream_points = PackedVector2Array([
		Vector2(-12.0, -0.2), Vector2(-7.0, 0.6), Vector2(-3.4, -0.4), Vector2(0.4, -0.9),
		Vector2(4.0, -0.4), Vector2(7.6, -1.6), Vector2(12.0, -2.0)])
	ground.stream_width = 0.9
	add_child(ground)
	var v: Array = VIEWS[clampi(view, 0, VIEWS.size() - 1)]
	_face = deg_to_rad(float(v[2]))
	var tpos := _nearest_path(v[0])
	contact = ContactShadows.new()
	contact.name = "ContactShadows"
	traveller = _add_card(TRAVELLER, TRAVELLER_H, tpos, _face * 0.6, 0.012)
	contact.add(tpos, _face * 0.6, 0.2, 0.1, 1.3)
	_focus2 = Vector2(tpos.x, tpos.z)
	_reserve(_focus2, 0.75)  # breathing room around the hero
	var yw := deg_to_rad(float(v[2]))
	_cam_ground = _focus2 + Vector2(sin(yw), cos(yw)) * float(v[3]) * cos(deg_to_rad(float(v[1])))
	_hero_trees(v)
	_hills()
	_village()
	_wheat()
	_stream()
	_meadow()
	_forest()
	_verges()
	_rocks()
	_hero(v)
	_gap_fill()
	contact.commit()
	add_child(contact)
	rig = LookRig.new()
	rig.name = "LookRig"
	rig.elevation_deg = v[1]
	rig.yaw_deg = v[2]
	rig.distance = v[3]
	rig.fov = v[4]
	# r3 DOF: r2 critic "depth of field is close to zero ... single biggest reason"; narrow band on the hero,
	# strong near blur, softer far blur (bench-only overrides of B's defaults).
	rig.tilt_blur = 1.35
	rig.tilt_band_half = 0.11
	rig.tilt_band_soft = 0.3
	rig.tilt_top_bias = 0.75
	rig.dof_amount = 0.075
	rig.dof_near_margin = 0.6
	rig.dof_far_margin = 1.8
	var focus := Node3D.new()
	focus.name = "Focus"
	add_child(focus)
	# hero on a third: shift the look point sideways (camera-right) so the traveller sits off-centre
	var right := Vector3(cos(yw), 0, -sin(yw))
	focus.global_position = traveller.global_position + right * float(v[5]) * 0.62
	rig.focus_target = focus
	add_child(rig)
	if animate:
		for h in find_children("*", "PopHinge", true, false):
			var d := (h as Node3D).global_position.distance_to(traveller.global_position)
			(h as PopHinge).pop_up(0.2 + d * 0.15 + randf() * 0.1)
	await get_tree().process_frame
	await get_tree().process_frame
	var inf := 0
	for b in get_children():
		if b.has_meta("card") and rig.camera.is_position_in_frustum((b as Node3D).global_position + Vector3(0, 0.05, 0)):
			inf += 1
	print("ART_BENCH cards=", card_count, " in_frame=", inf, " view=", view)


# ------------------------------------------------------------------ catalog / placement helpers

func _load_catalog() -> void:
	var f := FileAccess.open(CATALOG, FileAccess.READ)
	if f == null:
		push_error("art_bench: no catalog")
		return
	for it in JSON.parse_string(f.get_as_text()):
		_cat[it["id"]] = it


func _has(id: String) -> bool:
	return _cat.has(id)


func _pool(ids: Array) -> Array:
	var out := []
	for id in ids:
		if _cat.has(id):
			out.append(id)
	return out


## r3: least-used id of the pool (random tie-break), so repeats spread out instead of piling up.
func _pick(ids: Array) -> String:
	var p := _pool(ids)
	if p.is_empty():
		return ""
	p.shuffle()
	var best: String = p[0]
	for id in p:
		if int(_used.get(id, 0)) < int(_used.get(best, 0)):
			best = id
	return best


func _nearest_path(p: Vector2) -> Vector3:
	var best := Vector3.ZERO
	var bd := INF
	for q in ground.path_centre_3d():
		var d := Vector2(q.x, q.z).distance_to(p)
		if d < bd:
			bd = d
			best = q
	return best


func _reserve(p: Vector2, r: float) -> void:
	_placed.append([p, r])


## overlap < 1 lets neighbouring cards crowd into each other's footprint (cards are thin; it reads as layering).
func _free(p: Vector2, r: float, overlap := 0.42, allow_water := false) -> bool:
	if not ground.on_page(p, 0.15):
		return false
	if ground.path_distance(p) < r * 0.45 + 0.03:
		return false
	if not allow_water and ground.stream_distance(p) < r * 0.35 + 0.03:
		return false
	# lens keep-out: no tall card on the line between the hero and the camera (it would wall off the view)
	if _cam_ground.x != INF and _cur_h > 0.22:
		var ax := _cam_ground - _focus2
		var t := (p - _focus2).dot(ax) / ax.length_squared()
		if t > 0.05 and t < 1.2:
			var lat := (p - (_focus2 + ax * t)).length()
			if lat < 0.45 + _cur_h * 0.6 + t * 0.8:
				return false
	for q in _placed:
		if (q[0] as Vector2).distance_to(p) < (r + float(q[1])) * overlap:
			return false
	return true


## Place catalog card `id` near c within spread; scale s0..s1 of its catalog height.
func _try(id: String, c: Vector2, spread: float, s0 := 0.8, s1 := 1.2, yaw := INF, overlap := 0.42, allow_water := false) -> Node3D:
	if id == "" or not _cat.has(id):
		return null
	var it: Dictionary = _cat[id]
	var h: float = float(it["height_units"]) * randf_range(s0, s1)
	var w: float = h * float(it.get("aspect", 1.0))
	var r := clampf(w * 0.55, 0.06, 1.2)
	_cur_h = h
	for t in 16:
		var q := c + Vector2(randf_range(-spread, spread), randf_range(-spread, spread) * 0.8)
		if _free(q, r, overlap, allow_water):
			_reserve(q, r)
			var yy := _face + randf_range(-0.45, 0.45) if yaw == INF else yaw + randf_range(-0.12, 0.12)
			return _place(id, h, q, yy)
	return null


func _place(id: String, h: float, q: Vector2, yaw: float, force_flat := false) -> Node3D:
	var it: Dictionary = _cat[id]
	var pos := Vector3(q.x, ground.surface_y(q), q.y)
	var thick := clampf(h * 0.024, 0.008, 0.035)  # ~2.4 % of height: the cream core reads on the rim
	_used[id] = int(_used.get(id, 0)) + 1
	var w: float = h * float(it.get("aspect", 0.8))
	if bool(it.get("cross_slot", false)) and not force_flat:
		contact.add_round(pos, clampf(w * 0.32, 0.06, 0.3), 1.0)
		return _add_cross(it["path"], h, pos, yaw, thick)
	if str(it.get("category", "")) != "hill":
		contact.add(pos, yaw, w, clampf(h * 0.35, 0.04, 0.16), 1.0)
	return _add_card(it["path"], h, pos, yaw, thick)


## A cluster of 3-7 overlapping cards with mixed scale.
func _cluster(c: Vector2, ids: Array, n: int, spread := 0.45, s0 := 0.7, s1 := 1.35) -> void:
	var p := _pool(ids)
	if p.is_empty():
		return
	for i in n:
		_try(_pick(p), c, spread, s0, s1)


func _grove(c: Vector2, trees: Array, skirt: Array, n: int, spread := 0.8) -> void:
	ground.add_patch(c + Vector2(0, 0.15), spread * randf_range(0.9, 1.2), 4 if randf() < 0.4 else 5)  # moss under groves
	for i in n:
		_try(_pick(trees), c, spread, 0.75, 1.3, INF, 0.36)
	for i in n * 2 + 3:
		_try(_pick(skirt), c + Vector2(0, 0.3), spread * 1.15, 0.7, 1.3)


# ------------------------------------------------------------------ zones

func _hills() -> void:
	# Three rows of hill cards along the back edge of the page, facing the camera, plus low hill layers
	# in the middle distance (like the stand-up hill cards of the reference).
	# r3: four rows spaced in depth with gaps inside each row (critic: "3-4 separated hill cards with visible
	# gaps, hinges and parallax, not flat painted bands")
	var rows := [
		[-7.1, ["hill_layer_far_teal", "hill_far_blue"], 1.1, 1.35, 0.85, 1.0],
		[-6.6, ["hill_layer_ochre", "hill_patchwork_gold", "hill_layer_olive"], 0.8, 1.0, 0.8, 1.05],
		[-6.05, ["hill_wooded_firs", "hill_wooded_grove", "hill_rolling_green"], 0.62, 0.8, 0.9, 1.2],
		[-5.5, ["hill_layer_moss", "hill_layer_sage"], 0.4, 0.52, 1.0, 1.4],
	]
	for row in rows:
		var ids := _pool(row[1])
		if ids.is_empty():
			continue
		var x := -11.2 + randf() * 1.6
		while x < 11.0:
			var id: String = ids[randi() % ids.size()]
			var h: float = randf_range(row[2], row[3])
			var w: float = h * float(_cat[id].get("aspect", 4.0))
			var q := Vector2(x + w * 0.5, float(row[0]) + randf_range(-0.12, 0.12))
			_place(id, h, q, _face * 0.5 + randf_range(-0.06, 0.06), true)
			_reserve(q, 0.6)
			x += w * randf_range(float(row[4]), float(row[5]))
	# low layered hills in the middle distance, behind meadow and forest
	var low := _pool(["hill_layer_moss", "hill_layer_sage", "hill_wooded_grove", "hill_wooded_firs", "hill_wooded_grove"])
	for c in [Vector2(-7.5, -4.6), Vector2(-4.2, -5.4), Vector2(5.6, -5.0), Vector2(8.8, -4.0), Vector2(-9.2, -2.2)]:
		if low.is_empty():
			break
		for k in 2:
			var id: String = low[randi() % low.size()]
			var wooded := id.begins_with("hill_wooded")
			var h := randf_range(0.5, 0.7) if wooded else randf_range(0.18, 0.26)
			var q: Vector2 = c + Vector2(randf_range(-0.8, 0.8), k * 0.28)
			var half_w: float = h * float(_cat[id].get("aspect", 4.0)) * 0.5
			if ground.path_distance(q) > half_w + 0.3 and ground.path_distance(q + Vector2(half_w, 0)) > 0.3 and ground.path_distance(q - Vector2(half_w, 0)) > 0.3:
				_place(id, h, q, randf_range(-0.2, 0.2), true)
				_reserve(q, 0.5)


func _village() -> void:
	# cottages facing the path, gardens, yard props, hens. Near-left quadrant.
	var houses := [
		[Vector2(-1.7, 3.9), "house_cottage_terracotta", 0.35],
		[Vector2(-3.2, 3.0), "house_cottage_thatch", 0.15],
		[Vector2(-2.5, 5.9), "house_stone_moss", 0.3],
		[Vector2(-4.6, 4.5), "house_barn_terracotta", 0.1],
		[Vector2(-4.0, 6.5), "house_round_thatch", 0.2],
		[Vector2(-5.8, 2.8), "house_tall_slate", 0.0],
	]
	for hs in houses:
		var id: String = hs[1] if _has(hs[1]) else _pick(["house_cottage_terracotta", "house_cottage_thatch", "house_tall_slate"])
		var h: float = float(_cat[id]["height_units"]) * randf_range(0.95, 1.05)
		var q: Vector2 = hs[0]
		_reserve(q, 0.9)
		_place(id, h, q, _face + float(hs[2]) * 0.6)
		_glow(Vector3(q.x + 0.05, h * 0.36, q.y + 0.12), 0.45, 0.55)
		# garden skirt in front of each house
		_cluster(q + Vector2(0, 0.55), ["flower_tulip_cream", "flower_marigold", "flower_poppy_red", "flower_lavender",
			"bush_wild_rose", "village_flower_pots", "bush_boxwood", "flower_daisy_white", "flower_foxglove"], 6, 0.55, 0.75, 1.2)
		_cluster(q + Vector2(randf_range(-0.6, 0.6), -0.55), ["tree_apple", "tree_round_moss", "tree_young_green",
			"tree_oak_moss", "tree_egg_spring", "tree_small_ochre"], 2, 0.5, 0.8, 1.1)
	# picket fence along the path side of the gardens, broken into short runs
	for i in 9:
		if randf() < 0.25:
			continue
		var fq := Vector2(-0.95 - (i % 3) * 0.02, 2.2 + i * 0.5)
		var fp := _nearest_path(fq)
		var q := Vector2(fp.x - 0.62, fq.y)
		if _free(q, 0.2, 0.3):
			_reserve(q, 0.2)
			_place(_pick(["fence_picket_cream", "fence_picket_cream", "fence_wattle"]), 0.17, q, PI * 0.5 + randf_range(-0.1, 0.1))
	# yard props
	var yard := ["village_well", "village_washing_line", "village_pump", "village_beehive", "village_coop", "village_barrel",
		"village_woodpile", "village_wheelbarrow", "village_bench", "village_trough", "field_hay_bale_square", "village_ladder"]
	for c in [Vector2(-2.4, 2.3), Vector2(-4.2, 2.0), Vector2(-5.4, 3.6), Vector2(-1.4, 5.2), Vector2(-3.3, 4.9), Vector2(-5.2, 5.8), Vector2(-1.3, 6.9)]:
		_cluster(c, yard, 3, 0.5, 0.9, 1.1)
		_cluster(c + Vector2(0.2, 0.3), ["animal_hen_brown", "animal_hen_white", "animal_cat", "flower_buttercup", "grass_tuft_sage"], 3, 0.5, 0.9, 1.1)
	# lanterns by the path with real warm light, and the signpost
	for z in [5.6, 2.2]:
		var pp := _nearest_path(Vector2(0, z))
		var q := Vector2(pp.x - 0.48, pp.z)
		if _try("village_lantern_post", q, 0.04, 0.95, 1.0, _face, 0.2):
			_glow(Vector3(q.x + 0.06, 0.4, q.y + 0.06), 0.35, 0.45)
	_try("village_signpost", Vector2(_nearest_path(Vector2(0, 1.6)).x + 0.5, 1.6), 0.06, 0.95, 1.05, _face, 0.2)
	# village backdrop trees
	_grove(Vector2(-6.6, 5.2), ["tree_round_moss", "tree_cloud_olive", "tree_oak_moss", "tree_twin_olive", "tree_poplar_olive"],
		["bush_hedge_dark", "bush_sage_leaf", "bush_boxwood", "flower_chamomile"], 4)


func _wheat() -> void:
	# broken rows of varied length across the near-right field; stooks, stacks and bales as focal points.
	var wheat := _pool(["field_wheat_row_a", "field_wheat_row_b", "field_wheat_clump_short", "field_wheat_clump_tall",
		"field_wheat_patch_poppy", "field_wheat_clump_pale", "field_wheat_stalks"])
	if wheat.is_empty():
		return
	var z := 1.35
	while z < 7.1:
		var x := _nearest_path(Vector2(1.0, z)).x + 0.75 + randf() * 0.3
		var x_end := randf_range(3.4, 6.6)
		while x < x_end:
			if randf() < 0.2:
				x += randf_range(0.35, 0.9)  # broken row
				continue
			var id: String = wheat[randi() % wheat.size()]
			var h: float = float(_cat[id]["height_units"]) * randf_range(0.8, 1.35)
			var w: float = h * float(_cat[id].get("aspect", 1.0))
			var q := Vector2(x + w * 0.5, z + randf_range(-0.07, 0.07))
			if ground.on_page(q, 0.15) and ground.stream_distance(q) > 0.25:
				_place(id, h, q, _face * 0.5 + randf_range(-0.12, 0.12))
				_reserve(q, 0.1)
			x += w * randf_range(0.55, 0.85)
		z += randf_range(0.48, 0.7)
	# focal points sit in clearings cut into the rows (placed on top; their own footprint)
	for c in [Vector2(3.2, 3.0), Vector2(5.4, 5.0), Vector2(2.2, 5.9), Vector2(6.0, 2.2)]:
		var ids := ["field_haystack", "field_haystack_pole", "field_wheat_stook", "field_hay_bales_stack", "field_hay_bale_round",
			"field_hay_bale_square", "field_wheat_sheaf", "field_hay_cart"]
		for k in randi_range(3, 4):
			var id := _pick(ids)
			if id != "":
				var h: float = float(_cat[id]["height_units"]) * randf_range(0.9, 1.25)
				_place(id, h, c + Vector2(randf_range(-0.5, 0.5), randf_range(-0.2, 0.3)), _face + randf_range(-0.25, 0.25))
	# a split-rail fence along the field's stream side and some hedgerow at the far edge
	for i in 10:
		var q := Vector2(1.6 + i * 0.62, 0.85 + randf_range(-0.05, 0.05))
		if ground.stream_distance(q) > 0.15 and ground.path_distance(q) > 0.2:
			_place(_pick(["fence_split_rail", "fence_split_rail", "fence_wattle"]), 0.17, q, randf_range(-0.08, 0.08))
	_cluster(Vector2(7.6, 4.0), ["tree_poplar_olive", "tree_oval_sage", "tree_egg_spring"], 3, 0.6, 0.8, 1.2)


func _stream() -> void:
	var line := _stream_line_pts()
	# reed beds and cattails along both banks in clumps (not a continuous hedge)
	var reeds := ["water_cattails_a", "water_reeds_olive", "water_reeds_teal", "water_rushes_seed", "water_cattails_b",
		"flower_forgetmenot", "grass_tuft_dark", "fg_foxtail", "water_cattail_pair"]
	for i in range(0, line.size(), 4):
		if randf() < 0.3:
			continue
		var p: Vector2 = line[i]
		for sd: float in [-1.0, 1.0]:
			if randf() < 0.35:
				continue
			var q := p + Vector2(0, sd * (ground.stream_width * 0.5 + 0.12))
			for k in randi_range(2, 4):
				_try(_pick(reeds), q, 0.18, 0.75, 1.25, INF, 0.3)
	# on the water: lily pads, ducks, stepping stones, willows on the banks
	for i in range(3, line.size() - 3, 6):
		var p: Vector2 = line[i] + Vector2(randf_range(-0.2, 0.2), randf_range(-0.12, 0.12))
		if ground.path_distance(p) < 1.0:
			continue
		_try(_pick(["water_lily_pads", "animal_duck_cream", "animal_duck_brown", "animal_duckling_a", "animal_duckling_b", "water_lily_pads", "animal_goose"]),
			p, 0.05, 0.85, 1.15, randf_range(-0.6, 0.6), 0.3, true)
	for x in [-4.6, 5.2]:
		var p := _stream_at(x)
		if p != Vector2.INF:
			_place(_pick(["water_stepping_stones", "rock_low_grey"]), 0.09, p, 0.0)
	for x in [-8.0, -2.4, 2.8, 8.6]:
		var p := _stream_at(x)
		if p != Vector2.INF:
			_try(_pick(["tree_willow_sage", "tree_willow_sage", "tree_poplar_olive"]), p + Vector2(0, -0.9), 0.3, 0.9, 1.15, INF, 0.35)
	# bridge where the path crosses the stream: card plane along the path, both rails
	var pl := ground.path_centre_3d()
	var bi := 0
	var bd := INF
	for i in pl.size():
		var d := absf(ground.stream_distance(Vector2(pl[i].x, pl[i].z)) + ground.stream_width * 0.5)
		if d < bd:
			bd = d
			bi = i
	var a := Vector2(pl[maxi(bi - 2, 0)].x, pl[maxi(bi - 2, 0)].z)
	var b := Vector2(pl[mini(bi + 2, pl.size() - 1)].x, pl[mini(bi + 2, pl.size() - 1)].z)
	var bt := (b - a).normalized()
	var byaw := atan2(bt.y, -bt.x)
	if cos(byaw - _face) < 0.0:
		byaw += PI  # print side toward the camera
	var bid := "bridge_plank" if _has("bridge_plank") else "bridge_arch_cream"
	for sd: float in [-1.0, 1.0]:
		var bq: Vector2 = Vector2(pl[bi].x, pl[bi].z) + Vector2(-bt.y, bt.x) * sd * ground.path_width * 0.48
		_reserve(bq, 0.5)
		_place(bid, 0.26, bq, byaw)
	if _has("bridge_jetty"):
		var jp := _stream_at(-6.2)
		if jp != Vector2.INF:
			_place("bridge_jetty", 0.16, jp + Vector2(0, 0.3), _face)


func _meadow() -> void:
	# far-left pasture: sheep in little flocks, a cow, rabbits, flowers in dense clumps, a few trees
	for c in [Vector2(-2.4, -2.6), Vector2(-4.4, -3.2), Vector2(-6.2, -2.0), Vector2(-3.4, -4.6)]:
		_cluster(c, ["animal_sheep_grazing", "animal_sheep_standing", "animal_sheep_lying", "animal_sheep_grazing"], randi_range(3, 5), 0.6, 1.3, 1.6)
	_cluster(Vector2(-5.2, -2.6), ["animal_cow_lying", "animal_rabbit"], 2, 0.4, 1.2, 1.4)
	for i in 6:
		var q := Vector2(-2.2 - i * 0.6, -1.6 + randf_range(-0.05, 0.05))
		if ground.stream_distance(q) > 0.15 and ground.path_distance(q) > 0.2:
			_place(_pick(["fence_split_rail", "fence_wattle"]), 0.17, q, randf_range(-0.08, 0.08))
	_try("fence_gate", Vector2(-1.7, -1.62), 0.05, 1.0, 1.0, _face * 0.5, 0.2)
	_try("animal_bird_red_post", Vector2(-5.9, -1.6), 0.1)
	_try("animal_bird_blue_post", Vector2(-2.9, -1.7), 0.1)
	for c in [Vector2(-6.4, -4.4), Vector2(-4.6, -5.6), Vector2(-2.4, -5.6), Vector2(-7.4, -1.0)]:
		_grove(c, ["tree_round_moss", "tree_birch_yellow", "tree_apple", "tree_twin_olive", "tree_flat_sage", "tree_round_ochre",
			"tree_lollipop_fruit", "tree_birch_slim", "tree_hawthorn_bent"],
			["bush_sage_leaf", "bush_teal_blossom", "flower_daisy_white", "flower_clover", "bush_wild_rose", "bush_elder_flower",
			"bush_gorse", "bush_lumpy_olive", "flower_clover_purple", "flower_star_white"], 3, 0.7)
	var flowers := ["flower_poppy_red", "flower_daisy_yellow", "flower_cornflower", "flower_buttercup", "flower_chamomile",
		"flower_clover", "flower_daisy_white", "flower_lavender", "flower_thistle", "grass_tuft_sage", "grass_tuft_olive",
		"flower_bluebell", "flower_marigold_buds", "flower_star_white", "flower_buttercup_sprig", "flower_tansy", "flower_ochre_seedhead",
		"grass_seed_feather", "grass_spiky_olive", "flower_clover_mound", "flower_foxglove_pink"]
	for k in 40:
		var c := Vector2(randf_range(-7.4, -0.8), randf_range(-6.2, -1.6))
		_cluster(c, [_pick(flowers), _pick(flowers), _pick(flowers)], randi_range(3, 6), 0.2, 0.75, 1.3)


func _forest() -> void:
	var conifers := ["conifer_spruce_blue", "conifer_fir_tall", "conifer_fir_green", "conifer_pine_bushy", "conifer_olive_redtrunk",
		"conifer_fir_dark_tall", "conifer_pine_tiered_olive", "conifer_fir_young", "conifer_fir_pair", "conifer_spruce_grey", "conifer_juniper"]
	var rounds := ["tree_round_ochre", "tree_layer_terracotta", "tree_spiral_terracotta", "tree_twotone_olive_ochre", "tree_oval_terracotta",
		"tree_mixed_rust", "tree_heart_orange", "tree_small_ochre", "tree_oak_moss", "tree_cloud_olive", "tree_rowan",
		"tree_hawthorn_bent", "tree_birch_slim", "tree_poplar_slim"]
	var skirt := ["rock_round_grey", "rock_mossy", "rock_low_grey", "bush_fern", "bush_hedge_dark", "mushroom_tan_cluster",
		"mushroom_red_cluster", "mushroom_red_pair", "rock_stump_mossy", "bush_blackberry", "fg_fern_big", "bush_mustard_autumn", "village_woodpile",
		"rock_log_mossy", "rock_stump_mushroom", "rock_boulder_lichen", "rock_stone_fern", "rock_moss_mound", "rock_stump_ivy",
		"mushroom_terracotta_trio", "grass_fern_sprout", "bush_bramble_low", "bush_rust_round", "bush_column_pine", "flower_bluebell"]
	for c in [Vector2(1.4, -2.8), Vector2(3.0, -2.2), Vector2(4.6, -3.0), Vector2(6.4, -2.8), Vector2(2.4, -4.2),
			Vector2(4.0, -4.8), Vector2(5.8, -4.4), Vector2(7.6, -3.8), Vector2(1.0, -5.4), Vector2(3.0, -6.0), Vector2(8.6, -1.6)]:
		var mix: Array = conifers if randf() < 0.55 else rounds
		_grove(c, mix + (rounds if randf() < 0.4 else []), skirt, randi_range(4, 6), 0.75)


func _verges() -> void:
	# little clumps along both path edges on alternating sides
	var pl := ground.path_centre_3d()
	var verge := ["flower_chamomile", "flower_buttercup", "grass_tuft_sage", "flower_poppy_red", "grass_tuft_olive",
		"flower_daisy_yellow", "mushroom_tan_cluster", "rock_low_grey", "flower_clover", "flower_daisy_white", "flower_forgetmenot",
		"grass_spiky_olive", "flower_star_white", "grass_moss_mound", "flower_buttercup_sprig", "rock_stacked_flat", "grass_broad_leaves"]
	for i in range(0, pl.size() - 1, 5):
		var a := Vector2(pl[i].x, pl[i].z)
		var b := Vector2(pl[i + 1].x, pl[i + 1].z)
		var tn := (b - a).normalized()
		var nn := Vector2(-tn.y, tn.x) * (1.0 if randf() < 0.5 else -1.0)
		var c := a + nn * (ground.path_width * 0.5 + 0.16)
		_cluster(c, verge, randi_range(2, 4), 0.14, 0.7, 1.1)


## r3: B's folded (tented) paper rocks in small clusters near the path and in the meadow/forest: real relief.
func _rocks() -> void:
	var tints := [Color("8f9886"), Color("9a9a88"), Color("7f8a74"), Color("a39d8a")]
	for c in [Vector2(-2.0, 1.4), Vector2(1.6, -1.8), Vector2(-3.2, -2.0), Vector2(2.8, -4.0), Vector2(-1.8, 6.0),
			Vector2(3.6, 0.4), Vector2(-5.2, -4.6), Vector2(0.9, 4.2), Vector2(-1.2, -4.6), Vector2(5.6, -2.2)]:
		for k in randi_range(2, 4):
			var q: Vector2 = c + Vector2(randf_range(-0.35, 0.35), randf_range(-0.25, 0.25))
			var sz := randf_range(0.05, 0.12)
			_cur_h = 0.0
			if _free(q, sz * 1.6, 0.6):
				_reserve(q, sz * 1.4)
				ground.add_folded_rock(q, sz, randf() * TAU, tints[randi() % tints.size()])
				contact.add_round(Vector3(q.x, ground.surface_y(q), q.y), sz * 1.3, 0.8)
		_cluster(c + Vector2(0, 0.2), ["grass_fern_sprout", "grass_moss_mound", "flower_star_white", "mushroom_tan_cluster", "grass_spiky_olive"], 2, 0.3, 0.8, 1.1)


## r3: a few big hero trees anchor each view (critic: "vary card height 0.6-1.6x so a few large hero trees anchor
## the composition"), placed first so the zones fill around them; behind/beside the hero on the open side.
func _hero_trees(v: Array) -> void:
	var yaw := deg_to_rad(v[2])
	var to_cam := Vector2(sin(yaw), cos(yaw))
	var right := Vector2(cos(yaw), -sin(yaw))
	var big := ["tree_hero_oak", "tree_hero_chestnut", "tree_hero_willow"]
	big = big.slice(view % 3) + big.slice(0, view % 3)  # each view leads with a different hero tree
	for b in big:
		_used[b] = big.find(b)
	var side := float(v[5])
	for k in 2:
		var q := _focus2 - to_cam * randf_range(1.7, 2.5) + right * side * (1.1 + k * 1.4) * randf_range(0.9, 1.15)
		if ground.path_distance(q) < 0.7 or ground.stream_distance(q) < 0.5 or not ground.on_page(q, 0.3):
			continue
		var id := _pick(big)
		_place(id, float(_cat[id]["height_units"]) * randf_range(0.85, 1.0), q, yaw + randf_range(-0.2, 0.2), true)
		_reserve(q, 0.55)


## Big near-foreground cards toward the camera so the near blur reads as a lens (r3: plus mossy logs/stumps).
func _hero(v: Array) -> void:
	var yaw := deg_to_rad(v[2])
	var to_cam := Vector2(sin(yaw), cos(yaw))
	var right := Vector2(cos(yaw), -sin(yaw))
	var f := _focus2
	var heroes := ["fg_fern_big", "fg_meadow_grass", "fg_dandelion", "fg_burdock", "fg_foxtail", "mushroom_red_cluster", "bush_fern",
		"rock_log_mossy", "rock_stump_ivy", "rock_stump_mushroom", "grass_fern_sprout"]
	for k in 5:
		var side := float(v[5]) * (1.0 if k % 2 == 0 else -1.0)
		var q := f + to_cam * randf_range(1.9, 3.0) + right * side * randf_range(1.0, 2.0)
		if ground.path_distance(q) < 0.3 or not ground.on_page(q, 0.1):
			continue
		var id := _pick(heroes)
		if id == "":
			continue
		var low: bool = id.begins_with("rock_")
		_place(id, randf_range(0.22, 0.3) if low else randf_range(0.42, 0.6), q, yaw + randf_range(-0.2, 0.2))
		_reserve(q, 0.5)


## Fill leftover open felt with tight single-species clumps (3-7, mixed scale), not an even sprinkle;
## some felt stays open between clumps.
func _gap_fill() -> void:
	var small := ["grass_tuft_sage", "grass_tuft_olive", "grass_tuft_dark", "flower_clover", "flower_buttercup", "flower_daisy_white",
		"flower_chamomile", "bush_sage_leaf", "flower_forgetmenot", "flower_poppy_red", "flower_cornflower", "fg_meadow_grass",
		"bush_boxwood", "bush_olive_berry", "flower_lavender", "grass_spiky_olive", "flower_clover_mound", "grass_broad_leaves",
		"grass_fern_sprout", "flower_bluebell", "flower_marigold_buds", "flower_red_berries", "grass_seed_feather", "flower_star_white",
		"grass_moss_mound", "flower_rust_weed", "flower_buttercup_sprig", "flower_clover_purple", "grass_dry_gold", "flower_tansy",
		"rock_moss_mound", "bush_bramble_low", "bush_lumpy_olive", "bush_gorse"]
	var tall := ["tree_round_moss", "tree_young_green", "tree_egg_spring", "tree_small_ochre", "conifer_fir_young", "conifer_juniper",
		"tree_heart_orange", "tree_apple", "tree_oval_sage", "tree_lollipop_fruit", "tree_rowan", "tree_birch_slim", "bush_column_pine"]
	for k in 420:
		var c := Vector2(randf_range(-7.5, 7.5), randf_range(-6.0, 7.3))
		var r := 0.0
		for q in _placed:
			if (q[0] as Vector2).distance_to(c) < 0.32:
				r += 1.0
		if r > 1.0:
			continue
		var base := _pick(small)
		var second := _pick(small)
		for j in randi_range(3, 7):
			_try(base if j % 3 != 2 else second, c, 0.18, 0.7, 1.4, INF, 0.5)
		if randf() < 0.22:
			_try(_pick(tall), c + Vector2(0, -0.25), 0.2, 0.7, 1.05, INF, 0.4)


# ------------------------------------------------------------------ stream helpers

func _stream_line_pts() -> PackedVector2Array:
	var out := PackedVector2Array()
	var x := -11.0
	while x < 11.0:
		var p := _stream_at(x)
		if p != Vector2.INF:
			out.append(p)
		x += 0.12
	return out


## Centre of the stream at x (searched along z).
func _stream_at(x: float) -> Vector2:
	var best := Vector2.INF
	var bd := INF
	var z := -4.0
	while z < 3.0:
		var d := ground.stream_distance(Vector2(x, z))
		if d < bd:
			bd = d
			best = Vector2(x, z)
		z += 0.03
	return best if bd < 0.0 else Vector2.INF


# ------------------------------------------------------------------ nodes

func _glow(p: Vector3, rng: float, energy: float) -> void:
	var l := OmniLight3D.new()
	l.light_color = Color("ffb35c")
	l.omni_range = rng
	l.light_energy = energy
	l.omni_attenuation = 1.6
	l.shadow_enabled = false
	l.position = p
	add_child(l)


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
	base.rotation.z = randf_range(-0.065, 0.065)  # hand-set cards lean a few degrees
	base.rotation.x = randf_range(-0.05, 0.03)
	base.set_meta("card", true)
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
