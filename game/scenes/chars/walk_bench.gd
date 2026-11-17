extends Node3D
## Character bench (component D, round 2): the traveller walks a raised cut-card path across a felt meadow
## built with GroundLayers (component B), dressed in depth bands from the shared catalogs (A + A0):
##   foreground  tall trees / hedges close to the lens, cropped by the frame bottom and sides,
##   near verge  low hedges, a rail fence, hens and flowers along the path, small props on the verge,
##   path        the traveller (hero ≈ 9-10 % of frame height),
##   behind      a fenced sheep pasture, scarecrow, sun and wind on wire stems,
##   mid / far   stream with reeds and ducks, tree groves, two rows of layered card hills.
## Clusters with open felt between them, scale varied 2-3x. Animals bob and grass flaps in the wind (life).
## LookRig (B) gives light/grade/DOF; this bench softens the key shadow, shortens it and eases the vignette.
## Click/tap on the page to walk there along the path, WASD to walk freely.
## `demo` runs a short story timeline after the opening walk: wind blows → traveller clutches the coat →
## wind tires → sun shines → hat off → shirt only → fans with the hat → sits.

@export var demo := true
@export var seed_value := 5
@export var cam_elevation := 31.0
@export var cam_distance := 5.4
@export var cam_fov := 20.0
@export var cam_drift := 5.0  ## slow yaw drift (deg) so the layers slide against each other
@export var fixed_step := true  ## deterministic 1/60 s per frame (captures); off for interactive play

const CARDS := "res://art/cards/catalog.json"
const ATLAS := "res://art/atlas/catalog.json"

var rig: LookRig
var ground: GroundLayers
var walker: Walker
var puppet: PaperPuppet
var focus: FollowFocus
var sun: SkyHanger
var wind: SkyHanger
var gusts: WindGusts
var path: Path3D
var card_count := 0
var _cat := {}
var _tex := {}
var _placed: Array = []  ## [Vector2, radius]
var _life: Array = []  ## [node, kind, phase, amp]
var _t := 0.0
var _events: Array = []
var _hero := Vector2.ZERO
var _muted: Array = []  ## cards printed in the dusty variant (palette hierarchy)
const MUTED_EDGE := Color(0.955, 0.915, 0.815)


func _ready() -> void:
	seed(seed_value)
	if fixed_step:
		PaperSpring.fixed_dt = 1.0 / 60.0
		PopHinge.fixed_dt = 1.0 / 60.0
	_load_catalogs()
	_build_ground()
	_build_chars()
	_build_sky()
	_dress()
	_tune_light()
	rig.snap()
	_mute_cards.call_deferred()
	print("WALK_BENCH cards=", card_count, " life=", _life.size())
	if demo:
		_events = [
			[1.4, func(): gusts.blow(puppet.global_position + Vector3(0, 0.2, 0), 3.2)],
			[2.0, func(): puppet.set_pose("hold")],
			[5.2, func(): gusts.tire()],
			[6.0, func(): sun.puff(1.15); sun.push(Vector3(0, 0.15, 0))],
			[6.6, func(): sun.puff(1.0)],
			[7.4, func(): puppet.set_pose("walk")],
			[8.8, func(): puppet.set_pose("walk_nohat")],
			[10.2, func(): puppet.set_pose("shirt")],
			[11.8, func(): walker.auto_walk = false; walker.target_offset = walker.offset + 0.25],
			[12.8, func(): puppet.set_pose("fan")],
			[14.2, func(): puppet.set_pose("sit")],
		]


func _process(dt: float) -> void:
	dt = PaperSpring.frame_dt(dt)
	_t += dt
	if cam_drift > 0.0:
		rig.yaw_deg = -6.0 + cam_drift * sin(_t * 0.8)
	while not _events.is_empty() and _t >= _events[0][0]:
		var e: Array = _events.pop_front()
		(e[1] as Callable).call()
	# Life: animals bob/hop on their hinge, grass and flowers flap in a slow gusting wind.
	var gust := 0.55 + 0.45 * sin(_t * 0.9) * sin(_t * 0.37 + 1.0)
	for l in _life:
		var n: Node3D = l[0]
		var ph: float = l[2]
		var amp: float = l[3]
		if l[1] == 0:  # animal: little hop + head-dip rock, like a card on a spring
			var s := sin(_t * 2.6 + ph)
			n.position.y = (l[4] as float) + maxf(0.0, s) * amp
			n.rotation.z = 0.06 * sin(_t * 2.6 + ph + 0.8) * (amp / 0.012)
		else:  # grass / flower card flapping back on its hinge
			n.rotation.x = -amp * gust * (0.6 + 0.4 * sin(_t * 3.1 + ph))


# ---------------------------------------------------------------- catalog
func _load_catalogs() -> void:
	for f in [ATLAS, CARDS]:  # A's hand cards override A0 ids if they ever collide
		if not FileAccess.file_exists(f):
			continue
		var arr = JSON.parse_string(FileAccess.get_file_as_string(f))
		if arr is Array:
			for e: Dictionary in arr:
				if ResourceLoader.exists(e["path"]):
					_cat[e["id"]] = e


func _ids(cat: String, label_has := "") -> Array:
	var out := []
	for id in _cat:
		var e: Dictionary = _cat[id]
		if e["category"] == cat and (label_has == "" or String(e.get("label", id)).contains(label_has)):
			out.append(id)
	return out


func _tex_of(p: String) -> Texture2D:
	if not _tex.has(p):
		_tex[p] = load(p)
	return _tex[p]


# ---------------------------------------------------------------- ground + path
func _build_ground() -> void:
	ground = GroundLayers.new()
	ground.name = "Ground"
	ground.seed_value = seed_value
	ground.cover_patches = 90
	ground.path_width = 0.38
	ground.felt_color = Color("71895f")  # sage, -30% sat / -15% value vs r2 mint (critic r2)
	ground.felt_mottle = Color("627a52")
	ground.path_color = Color("dccaa2")
	ground.path_points = PackedVector2Array([
		Vector2(-8.5, 2.6), Vector2(-5.5, 1.7), Vector2(-3.0, 0.9), Vector2(-1.0, 0.55), Vector2(0.9, 0.6),
		Vector2(2.8, 0.15), Vector2(4.8, -0.7), Vector2(7.0, -1.2), Vector2(9.5, -1.0)])
	ground.stream_points = PackedVector2Array([
		Vector2(-12.0, -1.6), Vector2(-7.0, -2.4), Vector2(-3.0, -3.2), Vector2(0.5, -3.0),
		Vector2(4.0, -3.7), Vector2(8.0, -4.6), Vector2(12.0, -4.4)])
	add_child(ground)
	# Walk curve = the cut path's centreline, on top of the path card.
	path = Path3D.new()
	path.name = "WalkPath"
	var c := Curve3D.new()
	var pts := ground.path_centre_3d()
	var step := 4
	var sel := PackedVector3Array()
	for i in range(0, pts.size(), step):
		sel.append(pts[i])
	if (pts.size() - 1) % step != 0:
		sel.append(pts[pts.size() - 1])
	for i in sel.size():
		var a := sel[maxi(i - 1, 0)]
		var b := sel[mini(i + 1, sel.size() - 1)]
		var tan := (b - a) * 0.25
		c.add_point(sel[i], -tan, tan)
	c.bake_interval = 0.02
	path.curve = c
	add_child(path)


# ---------------------------------------------------------------- characters, camera
func _build_chars() -> void:
	rig = LookRig.new()
	rig.name = "LookRig"
	rig.elevation_deg = cam_elevation
	rig.distance = cam_distance
	rig.fov = cam_fov
	rig.follow_smooth = 0.0
	rig.focus_height = 0.2
	# Narrower, depth-driven blur (critic r1: the screen band was too strong): physical DOF does the work,
	# the post tilt band only adds a touch at the frame edges.
	rig.tilt_blur = 0.8
	rig.vignette = 0.17
	rig.dof_near_margin = 0.7
	rig.dof_far_margin = 1.3
	rig.dof_far_transition = 2.4
	rig.dof_amount = 0.1
	rig.dof_near_transition = 0.8
	# Warm low key from the side (critic r2): longer, darker directional shadows, less ambient.
	rig.key_elevation_deg = 36.0
	rig.key_yaw_deg = -62.0
	rig.shadow_opacity = 0.82
	rig.shadow_softness = 1.6
	rig.ambient_energy = 0.44
	rig.key_color = Color("ffe1bc")  # less orange: the r2 yellow grade fought the greens
	rig.exposure = 0.84
	rig.fill_energy = 0.45
	add_child(rig)
	walker = Walker.new()
	walker.name = "Traveller"
	walker.path = path
	walker.camera = rig.camera
	walker.speed = 0.38
	walker.start_offset = path.curve.get_closest_offset(Vector3(-1.4, 0.03, 0.62))
	walker.auto_walk = true
	add_child(walker)
	puppet = PaperPuppet.new()
	puppet.camera = rig.camera
	walker.add_child(puppet)
	focus = FollowFocus.new()
	focus.name = "CamFocus"
	focus.target = walker
	add_child(focus)
	focus.snap()
	rig.focus_target = focus
	_hero = Vector2(walker.global_position.x, walker.global_position.z)
	_reserve(_hero, 0.3)


func _build_sky() -> void:
	sun = SkyHanger.new()
	sun.name = "Sun"
	sun.texture = preload("res://art/chars/sw_sun.webp")
	sun.card_height = 0.5
	sun.stem_height = 0.55
	sun.lean = Vector3(0.08, 0, 0.05)
	sun.position = Vector3(_hero.x - 0.95, 0.03, _hero.y - 1.7)
	sun.seed_offset = 0.2
	add_child(sun)
	wind = SkyHanger.new()
	wind.name = "Wind"
	wind.texture = preload("res://art/chars/sw_wind.webp")
	wind.card_height = 0.36
	wind.stem_height = 0.62
	wind.lean = Vector3(-0.08, 0, 0.0)
	wind.position = Vector3(_hero.x + 1.25, 0.03, _hero.y - 1.9)
	wind.seed_offset = 0.7
	wind.sway_amount = 0.08
	add_child(wind)
	gusts = WindGusts.new()
	gusts.hanger = wind
	add_child(gusts)
	_reserve(Vector2(sun.position.x, sun.position.z), 0.25)
	_reserve(Vector2(wind.position.x, wind.position.z), 0.25)


func _tune_light() -> void:
	# Softer, shorter key shadow (critic r1: hard, long, uniform shadows): higher sun, wider source, more blur.
	if rig.key:
		rig.key.light_angular_distance = 3.0


# ---------------------------------------------------------------- placement
func _reserve(p: Vector2, r: float) -> void:
	_placed.append([p, r])


func _free(p: Vector2, r: float, path_clear := 0.06) -> bool:
	if not ground.on_page(p, 0.2):
		return false
	if ground.path_distance(p) < r * 0.5 + path_clear or ground.stream_distance(p) < r * 0.5 + 0.05:
		return false
	for q in _placed:
		if (q[0] as Vector2).distance_to(p) < (r + float(q[1])) * 0.32:  # nest/overlap (critic r2)
			return false
	return true


## Place catalog card `id` near c (relative to the hero when rel) within spread; scale s0..s1 of catalog height.
func _try(id: String, c: Vector2, spread: float, s0 := 0.85, s1 := 1.15, life := -1, path_clear := 0.06) -> Node3D:
	if not _cat.has(id):
		return null
	var it: Dictionary = _cat[id]
	var h: float = float(it["height_units"]) * randf_range(s0, s1)
	var asp: float = float(it.get("aspect", 1.0))
	if it.has("px"):
		var px: Array = it["px"]
		asp = float(px[0]) / maxf(1.0, float(px[1]))
	var r := clampf(h * asp * 0.6, 0.06, 0.9)
	for t in 16:
		var q := c + Vector2(randf_range(-spread, spread), randf_range(-spread, spread) * 0.7)
		if _free(q, r, path_clear):
			_reserve(q, r)
			var cross: bool = it["category"] in ["tree", "conifer"] and h > 0.5
			var n := _place(it["path"], h, q, randf_range(-0.3, 0.3), cross)
			if life >= 0:
				_add_life(n, life, h)
			return n
	return null


func _place(p: String, h: float, q: Vector2, yaw: float, cross := false) -> Node3D:
	var pos := Vector3(q.x, ground.surface_y(q), q.y)
	var thick := clampf(h * 0.024, 0.008, 0.03)
	var base := Node3D.new()
	base.position = pos
	base.rotation.y = yaw
	base.rotation.z = randf_range(-0.09, 0.09)
	base.rotation.x = randf_range(-0.05, 0.03)
	add_child(base)
	var hinge := PopHinge.new()
	hinge.start_up = true
	hinge.weight = clampf(h / 0.4, 0.4, 2.5)
	base.add_child(hinge)
	if cross:
		var cc := CrossCard.new()
		cc.texture_a = _tex_of(p)
		cc.height = h
		cc.thickness = thick
		hinge.add_child(cc)
		card_count += 2
	else:
		var card := PaperCard.new()
		if (p.contains("flower") or p.contains("bush")) and randf() < 0.6:
			card.edge_color = MUTED_EDGE  # own material set → dusty ink below
			_muted.append(card)
		card.texture = _tex_of(p)
		card.height = h
		card.thickness = thick
		hinge.add_child(card)
		card_count += 1
	return base


func _mute_cards() -> void:
	for c: PaperCard in _muted:
		if c.mesh == null:
			continue
		var m := c.get_surface_override_material(0) as ShaderMaterial
		if m:
			m.set_shader_parameter("ink_saturation", 0.82)
			m.set_shader_parameter("ink_contrast", 0.98)


func _add_life(n: Node3D, kind: int, h: float) -> void:
	if n == null:
		return
	# Animate the card under the hinge so the PopHinge spring keeps its own rotation.
	var hinge := (n.get_child(0) as Node3D).get_child(0) as Node3D
	if kind == 0:
		_life.append([hinge, 0, randf() * TAU, clampf(h * 0.07, 0.006, 0.016), hinge.position.y])
	else:
		_life.append([hinge, 1, randf() * TAU, randf_range(0.10, 0.22)])


func _cluster(c: Vector2, ids: Array, n: int, spread: float, s0 := 0.8, s1 := 1.25, life := -1) -> void:
	for i in n:
		_try(ids[randi() % ids.size()], c, spread, s0, s1, life)


func _pick(arr: Array) -> String:
	return arr[randi() % arr.size()] if not arr.is_empty() else ""


# ---------------------------------------------------------------- dressing in depth bands
func _dress() -> void:
	var H := _hero
	var trees := ["tree_round_moss", "tree_cloud_olive", "tree_oval_sage", "tree_young_green", "tree_apple", "tree_willow_sage", "tree_poplar_olive"]
	var conifers := ["conifer_fir_green", "conifer_fir_tall", "conifer_pine_bushy", "conifer_spruce_blue", "conifer_olive_redtrunk"]
	var bushes := ["bush_sage_leaf", "bush_olive_berry", "bush_fern", "bush_hedge_dark", "bush_teal_blossom"]
	var hedges := _ids("hedge")
	var flowers := ["flower_chamomile", "flower_buttercup", "flower_daisy_yellow", "flower_cornflower", "flower_foxglove", "flower_tulip_cream", "flower_poppy_red"]
	var grass := ["grass_tuft_sage", "grass_tuft_olive", "grass_tuft_dark"]
	var hens := ["farm_animals_09", "farm_animals_10", "farm_animals_11"]
	var sheep := ["animal_sheep_standing", "animal_sheep_grazing", "animal_sheep_lying", "farm_animals_02", "farm_animals_03"]

	# --- 1. Foreground band: tall trees reaching up into the frame, bases cropped by the bottom edge, plus
	#        bushes and hedges at the very front so the near blur reads as a lens.
	for fx: float in [-1.6, -1.05, 1.05, 1.6]:
		var q := H + Vector2(fx + randf_range(-0.1, 0.1), 1.75 + randf_range(-0.15, 0.2))
		var id: String = _pick(conifers) if randf() < 0.55 else _pick(["tree_round_moss", "tree_oval_sage", "tree_young_green", "tree_apple"])
		if _free(q, 0.3):
			_reserve(q, 0.3)
			var it: Dictionary = _cat[id]
			_place(it["path"], randf_range(0.6, 0.85), q, randf_range(-0.2, 0.2), true)
	for k in 16:
		_try(_pick(bushes + hedges), H + Vector2(randf_range(-1.8, 1.8), 1.7), 0.35, 1.1, 1.8)
	# Near occluder row: dark pines and hedges right in front of the lens, heavily blurred (miniature cue).
	for fx: float in [-1.35, -0.75, 0.7, 1.3]:
		var q := H + Vector2(fx + randf_range(-0.12, 0.12), 2.1 + randf_range(-0.1, 0.1))
		_reserve(q, 0.1)
		var id: String = _pick(["conifer_fir_green", "conifer_pine_bushy", "conifer_fir_tall", "bush_hedge_dark"])
		if _cat.has(id):
			_place(_cat[id]["path"], randf_range(0.85, 1.15), q, randf_range(-0.2, 0.2), id.begins_with("conifer"))
	for k in 8:
		_try(_pick(grass + flowers), H + Vector2(randf_range(-1.6, 1.6), 1.4), 0.3, 1.0, 1.4, 1)

	# --- 2. Near verge (between path and foreground): a scalloped hedge run with gaps, a split-rail fence with
	#        hens pecking beside it, flower clumps; small props right on the path edge.
	var pl := ground.path_centre_3d()
	for i in range(0, pl.size() - 1, 3):
		var a := Vector2(pl[i].x, pl[i].z)
		if absf(a.x - H.x) > 3.5:
			continue
		var b := Vector2(pl[i + 1].x, pl[i + 1].z)
		var tn := (b - a).normalized()
		var nn := Vector2(-tn.y, tn.x)
		if nn.y < 0.0:
			nn = -nn  # toward the camera
		var front := a + nn * (ground.path_width * 0.5 + 0.2)
		var back := a - nn * (ground.path_width * 0.5 + 0.2)
		if randf() < 0.7:
			_try(_pick(hedges) if not hedges.is_empty() else _pick(bushes), front, 0.06, 0.9, 1.2)
		if randf() < 0.45:
			_try(_pick(flowers + grass), front + nn * 0.15, 0.12, 0.8, 1.1, 1)
		if randf() < 0.45:
			_try(_pick(flowers + grass), back, 0.12, 0.8, 1.1, 1)
	# fence segment on the near verge left of the hero, hens on the path side of it.
	for i in 4:
		var fp := H + Vector2(-2.0 + i * 0.32, 0.72 + i * 0.03)
		if _free(fp, 0.2):
			_reserve(fp, 0.2)
			_place(_cat["fence_split_rail"]["path"], 0.17, fp, 0.05)
	for k in 5:
		_try(_pick(hens), H + Vector2(-1.4, 0.38), 0.45, 0.95, 1.15, 0, 0.0)
	# hens and pebbles right on the verge ahead of the walk (life on the path itself).
	for k in 4:
		_try(_pick(hens), H + Vector2(0.95, -0.36), 0.3, 1.0, 1.2, 0, 0.0)
	for k in 5:
		_try(_pick(["rock_low_grey", "rock_round_grey", "small_decor_14", "small_decor_15", "mushroom_tan_cluster"]), H + Vector2(randf_range(-0.6, 1.8), 0.32), 0.3, 0.4, 0.7, -1, -0.04)
	# verge props: milestone, signpost, wheelbarrow of hay, bird on post, beehive.
	_try("meadow_field_25", H + Vector2(0.9, -0.42), 0.08, 1.0, 1.1)
	_try("village_signpost", H + Vector2(-0.75, -0.5), 0.08, 0.9, 1.0)
	_try("meadow_field_26", H + Vector2(1.7, 0.75), 0.1, 1.0, 1.1, 0)
	_try("meadow_field_23", H + Vector2(2.3, 0.55), 0.15)
	_try("farm_animals_21", H + Vector2(-2.6, 1.1), 0.15)
	_try("farm_animals_16", H + Vector2(0.4, 1.0), 0.2, 1.0, 1.1, 0)

	# --- 3. Behind the path: a fenced sheep pasture (right), haystack + scarecrow; an orchard clump (left).
	var pc := H + Vector2(1.6, -1.05)
	for i in 6:
		var fp := pc + Vector2(-1.1 + i * 0.36, 0.55 - i * 0.05)
		if _free(fp, 0.2, 0.0):
			_reserve(fp, 0.2)
			_place(_cat["meadow_field_17"]["path"] if _cat.has("meadow_field_17") else _cat["fence_split_rail"]["path"], 0.17, fp, -0.05)
	for k in 6:
		_try(_pick(sheep), pc, 0.75, 0.95, 1.15, 0)
	_try("field_haystack", pc + Vector2(0.9, -0.35), 0.15)
	_try("meadow_field_16", pc + Vector2(-0.6, -0.4), 0.1, 1.0, 1.1)
	_cluster(H + Vector2(-1.7, -1.1), ["tree_apple", "tree_round_moss", "tree_young_green"], 3, 0.45, 0.85, 1.1)
	_cluster(H + Vector2(-1.7, -0.9), bushes + flowers, 6, 0.6, 0.8, 1.1)
	_cluster(H + Vector2(0.2, -1.2), bushes + grass + ["rock_mossy", "mushroom_red_pair"], 5, 0.5, 0.8, 1.2)

	# --- 4. Mid: stream banks with reeds and ducks, copses at varied scale.
	for k in 14:
		var x := H.x + randf_range(-4.5, 4.5)
		var q := _bank_point(x, 0.1)
		if q != Vector2.INF:
			_cluster(q, ["water_cattails_a", "water_reeds_olive", "water_reeds_teal", "water_rushes_seed"], 3, 0.18, 0.8, 1.15)
	for k in 4:
		var q := _bank_point(H.x + randf_range(-2.5, 2.5), 0.02)
		if q != Vector2.INF:
			_try(_pick(["stream_water_24", "farm_animals_12", "animal_goose"]), q, 0.1, 0.9, 1.1, 0)
	for c in [H + Vector2(-3.4, -2.0), H + Vector2(3.6, -2.3), H + Vector2(-0.6, -4.2), H + Vector2(2.2, -4.8), H + Vector2(-3.0, -5.0)]:
		_cluster(c, trees + conifers, randi_range(3, 5), 0.7, 0.7, 1.5)
		_cluster(c + Vector2(0, 0.4), bushes + grass, 5, 0.8, 0.8, 1.2)

	# --- 5. Back: two rows of layered card hills (largest at the very back) and a conifer line between them.
	var hills := _ids("hill")
	for row in 2:
		var z := H.y - 6.0 - row * 1.4
		var x := H.x - 6.5 + randf() * 0.6
		while x < H.x + 6.5 and not hills.is_empty():
			var it: Dictionary = _cat[_pick(hills)]
			var h: float = float(it["height_units"]) * (3.0 + row * 1.2) * randf_range(0.9, 1.1)
			_place(it["path"], h, Vector2(x, z + randf_range(-0.2, 0.2)), randf_range(-0.08, 0.08))
			x += h * 2.2
	for k in 16:
		_try(_pick(conifers), Vector2(H.x + randf_range(-6.0, 6.0), H.y - 5.3), 0.3, 0.9, 1.4)

	# --- 6. Meadow fill: small clumps with open felt between them (clusters, not wallpaper).
	for k in 150:
		var c := H + Vector2(randf_range(-5.0, 5.0), randf_range(-5.0, 2.5))
		var base := _pick(flowers + grass + bushes)
		var life := 1 if base.begins_with("grass") or base.begins_with("flower") else -1
		for j in randi_range(2, 5):
			_try(base if j < 2 else _pick(flowers + grass), c, 0.22, 0.6, 1.5, life)


func _bank_point(x: float, off: float) -> Vector2:
	for t in 60:
		var q := Vector2(x, randf_range(-6.0, 0.0))
		if absf(ground.stream_distance(q) - off) < 0.07:
			return q
	return Vector2.INF
