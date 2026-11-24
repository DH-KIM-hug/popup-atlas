class_name MeadowWorld
extends Node3D
## 「해와 바람」 meadow: the reusable world scene template (integrator round 1, 2026-11-18).
## A road through meadow and wheat field, a stream with a plank bridge, a village edge, a forest edge and
## back rows of layered hills, on MeadowGround's stacked cut-cardstock relief. Everything is placed from
## `seed_value` with one RandomNumberGenerator, so a seed always gives the same spread.
##
## Built from the components:
##  - B: LookRig (light, grade, DOF, haze), GroundLayers (subclassed by MeadowGround), ContactShadows, folded rocks.
##  - A0 + A: CardLibrary queries both catalogs by category/pool (atlas cards use rim-stripped copies).
##  - C: PopHinge / CrossCard on every card near the traveller, PopWave on load, PaperAudio, PaperAmbient.
##  - D: Walker + PaperPuppet (0.36 tall) on the road, FollowFocus camera.
## Cards that never move (outside `pop_radius`) are batched into MultiMeshes (StaticCards).
## Stories dress this template: add characters / key props after `ready`, query `ground` for the road.

signal built

@export var seed_value := 1
@export var view := 0  ## camera preset (VIEWS); also sets where the traveller starts on the road
@export var fixed_step := false  ## deterministic 1/60 s stepping (captures)
@export var pop_on_load := true
@export var pop_radius := 3.85  ## cards within this distance of the traveller are hinged and rise in the wave
@export var walk := true
@export var with_audio := true
@export var theme := ""  ## dressing theme (CardLibrary): "" western meadow village, "korean" Joseon countryside (sunmoon)
@export var ground_style := "paper"  ## "paper" (default, 2026-11-22) matte cut-paper ground sheets; "felt" the old felt (GroundLayers.ground_style)

## road fraction, cam elevation, yaw, distance, fov
## r2: closer lens (distance ~7.3) so the traveller is the focal point, not a 20 px smudge.
const VIEWS := [
	## r3: lower lens (21-23°) for more overlap and a longer view into the haze, like the footage.
	## LOOKF r1: tabletop macro lens: camera near ground level (15-17 deg), long view across the table.
	[0.36, 16.0, 10.0, 7.4, 20.0],
	[0.46, 15.0, -24.0, 7.4, 20.0],
	[0.555, 17.0, 32.0, 7.2, 20.0],
	[0.62, 16.0, 26.0, 7.6, 20.0],
	[0.72, 15.0, 16.0, 7.4, 20.0],
	[0.28, 16.0, -30.0, 7.4, 20.0],
]
## r3: small props scaled down so the 0.36 traveller reads above the flowers (critic: "hero is the height of a flower")
const POOL_SCALE := {"conifer": 1.25, "tree": 1.08, "autumn": 1.05, "blossom": 1.02,  # LOOKF r1: was 1.5/1.25/1.2/1.15 (few giant trees)
	 "house": 1.0, "rock": 1.5,
	"flower": 0.72, "grass": 0.8, "mushroom": 0.75, "bush": 0.85, "sapling": 0.85, "hedge": 0.85}
const HERO_CLEAR := 1.3  ## r2: open clearing around the traveller (hierarchy, negative space)
## r4: no cross-slotted cards. The slotted second card, seen edge-on, read as a white seam through trees (critic).
const CROSS_POOLS: Array[String] = []
const SWAY_POOLS := {"grass": 0.07, "flower": 0.06, "reeds": 0.08, "crop": 0.05, "tree": 0.018, "conifer": 0.014, "blossom": 0.02, "autumn": 0.018, "bush": 0.025}

var rng := RandomNumberGenerator.new()
var lib: CardLibrary
var ground: MeadowGround
var contact: ContactShadows
var statics: StaticCards
var batch: CardBatch  ## perf: draws every card (static + hinged) in per-print MultiMeshes + one shadow MultiMesh
var sway: WindSway
var rig: LookRig
var walker: Walker
var puppet: PaperPuppet
var focus: FollowFocus
var path: Path3D
var audio: PaperAudio
var hinges: Array[PopHinge] = []
var trees: Array[Vector3] = []  ## crown points of the bigger trees (sound emitters, bird sprinkles)
var card_count := 0
var wave_end := 0.0

var _tex := {}
var _grid := {}  ## Vector2i -> Array of [Vector2 pos, float r]
var _start := Vector2.ZERO  ## traveller start on the page
var _cam_ground := Vector2.ZERO
var _cam_h := 2.0  ## camera height above the page (lens keep-out)
var _houses: Array = []  ## [pos, h, yaw] for chimney smoke
var chimney_smoke := false  ## template chimney smoke (off: it rose from the wrong places)
## the village's house cards (2026-11-23 house bodies): {id, path, h0, h, pos, yaw, lean, tilt, hinge (or null), thick,
## body (HouseBody or null)}; the orbit probe (tools/story/house_orbit.gd) reads it
var house_cards: Array = []
var _last_place := {}
var _fill_mask: FastNoiseLite  ## r2: low-frequency density mask (clearings vs clumps)
## perf: set before add_child to spread the build over frames (BuildSlicer budget); null = build in _ready at once.
var slicer: BuildSlicer
var is_built := false
var perf_phases := {}


func _ready() -> void:
	if slicer == null:
		slicer = BuildSlicer.new()
	slicer.phase("ground")
	rng.seed = seed_value
	seed(seed_value * 7919 + view)
	if fixed_step:
		PopHinge.fixed_dt = 1.0 / 60.0
		PaperSpring.fixed_dt = 1.0 / 60.0
	slicer.phase("ground_lib")
	lib = CardLibrary.new(rng, ["winter"], theme)
	await slicer.tick()
	slicer.phase("ground")
	await _build_ground()
	await slicer.tick()
	_build_walk_path()
	await slicer.tick()
	var v: Array = VIEWS[clampi(view, 0, VIEWS.size() - 1)]
	var off: float = path.curve.get_baked_length() * float(v[0])
	var sp := path.curve.sample_baked(off)
	_start = Vector2(sp.x, sp.z)
	var yw := deg_to_rad(float(v[2]))
	_cam_ground = _start + Vector2(sin(yw), cos(yw)) * float(v[3]) * cos(deg_to_rad(float(v[1])))
	_cam_h = float(v[3]) * sin(deg_to_rad(float(v[1])))
	contact = ContactShadows.new()
	contact.strength = 1.25  # LOOKF r1: firmer contact (photographed cards sit in their own shadow)
	contact.tint = Color(0.07, 0.09, 0.04)
	contact.name = "ContactShadows"
	batch = CardBatch.new()
	batch.name = "Cards"
	statics = StaticCards.new(batch)
	sway = WindSway.new()
	sway.name = "Wind"
	add_child(sway)
	_reserve(_start, HERO_CLEAR)
	_fill_mask = FastNoiseLite.new()
	_fill_mask.seed = seed_value * 17 + 3
	_fill_mask.frequency = 0.16
	slicer.phase("dress")
	await _dress()
	slicer.phase("cards")
	ground.flush_slabs()  # patches added while dressing
	contact.commit()
	add_child(contact)
	_preload_catalog()
	await batch.atlas.build_sliced(slicer)
	await slicer.tick()
	add_child(batch)
	batch.commit()
	await slicer.tick()
	slicer.phase("life")
	batch.set_wind_dir0(sway.wind_dir.normalized())
	sway.batch = batch
	_build_camera_and_traveller(v, off)
	await slicer.tick()
	_build_life()
	await slicer.tick()
	if with_audio:
		audio = PaperAudio.new()
		audio.name = "PaperAudio"
		add_child(audio)
		audio.watch(self)
		puppet.stepped.connect(func(_f, s): audio.step(walker.global_position, s))
	if pop_on_load:
		var wave := PopWave.new()
		wave.speed = 4.0
		wave_end = wave.pop(hinges, Vector3(_start.x, 0, _start.y), 0.25)
	slicer.finish()
	perf_phases = slicer.phases
	print("MEADOW seed=", seed_value, " view=", view, " cards=", card_count, " hinged=", hinges.size(),
		" static=", statics.count, " ids=", lib.used.size(), " tiers=", ground.tier_count(), " wave_end=", snappedf(wave_end, 0.01))
	is_built = true
	built.emit()


# ------------------------------------------------------------------ ground

func _build_ground() -> void:
	ground = MeadowGround.new()
	ground.name = "Ground"
	ground.seed_value = seed_value
	ground.ground_style = ground_style
	ground.page_size = Vector2(28.0, 20.0)
	ground.cover_patches = 28  # r2: fewer pale lobes (read as spilled paint)
	ground.felt_color = Color("7d9366")  # LOOKF r1: a touch warmer/deeper felt (was 7f9670 / 5f7652)
	ground.felt_mottle = Color("556b45")
	ground.felt_mottle_strength = 1.0
	ground.path_color = Color("c9ae7c")  # LOOKF r1: deeper sand, narrower road (pale road dominated the frame)
	ground.path_width = 0.38
	ground.stream_width = 0.78
	var j := func(x: float, z: float) -> Vector2: return Vector2(x + rng.randf_range(-0.25, 0.25), z + rng.randf_range(-0.15, 0.15))
	ground.path_points = PackedVector2Array([
		j.call(2.2, 9.6), j.call(1.0, 6.8), j.call(-0.6, 4.4), j.call(0.4, 1.8), j.call(0.2, -0.9),
		j.call(-1.0, -3.4), j.call(-0.4, -5.6), j.call(-2.0, -7.6), j.call(-3.6, -9.6)])
	ground.stream_points = PackedVector2Array([
		j.call(-14.0, 1.2), j.call(-9.0, 0.8), j.call(-5.0, -0.8), j.call(-2.0, -1.2), j.call(1.6, -2.0),
		j.call(5.0, -2.6), j.call(9.0, -4.2), j.call(14.0, -4.6)])
	# Rolling tiers: [centre, radius, tiers, squash]. Back rows stack 4-5 high, the near meadow 1-2.
	ground.hill_specs = [
		[Vector2(-6.4, 4.4), 3.6, 2, 0.6], [Vector2(6.2, 3.6), 3.8, 2, 0.55], [Vector2(-3.2, 7.8), 2.2, 1, 0.5],
		[Vector2(-7.4, -3.4), 3.4, 3, 0.55], [Vector2(5.8, -0.4), 2.2, 2, 0.6], [Vector2(3.6, -5.0), 2.6, 3, 0.55],
		[Vector2(-6.6, -7.6), 4.2, 4, 0.45], [Vector2(5.6, -8.2), 4.8, 5, 0.42], [Vector2(0.6, -9.0), 2.8, 3, 0.4],
		[Vector2(10.6, 1.6), 2.6, 2, 0.6], [Vector2(-11.0, 2.6), 2.4, 2, 0.6],
		# r3: broad low plateaus over the near meadow, so the road and stream run in channels between
		# raised board and the floor reads stacked everywhere (critic: "kill the flat floor").
		[Vector2(-5.0, 7.6), 4.6, 2, 0.5], [Vector2(6.4, 7.4), 4.8, 2, 0.5], [Vector2(-1.6, 4.6), 2.6, 1, 0.55],
		[Vector2(3.6, 1.2), 2.6, 1, 0.55], [Vector2(-9.6, -1.4), 3.2, 2, 0.55], [Vector2(9.0, -2.6), 3.2, 2, 0.55],
		[Vector2(-2.6, -1.8), 2.0, 1, 0.6], [Vector2(-11.2, 7.0), 2.6, 1, 0.6], [Vector2(11.4, 6.8), 2.6, 1, 0.6],
	]
	ground.slicer = slicer
	add_child(ground)
	if not ground.is_built:
		await ground.ground_built
	_mute_stream()


func _mute_stream() -> void:
	var st := ground.get_node_or_null("Stream") as MeshInstance3D
	if st and st.material_override:
		var m := st.material_override as ShaderMaterial
		m.set_shader_parameter("deep_color", Color(0.13, 0.36, 0.37))
		m.set_shader_parameter("shallow_color", Color(0.33, 0.56, 0.5))
		m.set_shader_parameter("ripple_color", Color(0.85, 0.88, 0.78))
		m.set_shader_parameter("ripple_amount", 0.8)


func _build_walk_path() -> void:
	path = Path3D.new()
	path.name = "WalkPath"
	var c := Curve3D.new()
	var pts := ground.path_centre_3d()
	var sel := PackedVector3Array()
	for i in range(0, pts.size(), 8):
		sel.append(pts[i])
	sel.append(pts[pts.size() - 1])
	# trim the ends (off the page edge)
	var trimmed := PackedVector3Array()
	for p in sel:
		if ground.on_page(Vector2(p.x, p.z), 0.8):
			trimmed.append(p)
	for i in trimmed.size():
		var a := trimmed[maxi(i - 1, 0)]
		var b := trimmed[mini(i + 1, trimmed.size() - 1)]
		var tan := (b - a) * 0.25
		c.add_point(trimmed[i], -tan, tan)
	c.bake_interval = 0.02
	path.curve = c
	add_child(path)


# ------------------------------------------------------------------ placement core

func _cell(p: Vector2) -> Vector2i:
	return Vector2i(floori(p.x / 0.6), floori(p.y / 0.6))


func _reserve(p: Vector2, r: float) -> void:
	var k := _cell(p)
	if not _grid.has(k):
		_grid[k] = []
	_grid[k].append([p, r])


func _free(p: Vector2, r: float, road_gap := 0.05) -> bool:
	if not ground.on_page(p, 0.25):
		return false
	if ground.path_closer_than(p, r * 0.45 + road_gap) or ground.stream_closer_than(p, r * 0.45 + 0.06):
		return false
	var k := _cell(p)
	for dx in range(-2, 3):
		for dz in range(-2, 3):
			for q in _grid.get(k + Vector2i(dx, dz), []):
				if (q[0] as Vector2).distance_to(p) < (r + float(q[1])) * 0.5:
					return false
	return true


## Lens keep-out for the start view: no tall card between the camera and the traveller.
func _blocks_view(q: Vector2, h: float) -> bool:
	if h < 0.3:
		return false
	var a := _start
	var b := _cam_ground
	var t := clampf((q - a).dot(b - a) / (b - a).length_squared(), 0.0, 1.0)
	if t < 0.04:
		return false
	var d := q.distance_to(a.lerp(b, t))
	if t >= 0.4 and t < 0.85 and d < 1.4 and h > 0.22:
		return true
	# LOOKF r1: low lens - nothing may rise into the sightline to the traveller (feet to hat)
	if d < 0.45 + h * 0.5 and h > t * _cam_h * 0.8 + 0.04:
		return true  # r4: no big near-lens cards across the bottom third (critic: huge blurred bush)
	return d < 0.35 + h * 0.9 * t * 2.0 and t < 0.55


## Place one card from a pool (or explicit id) near c within `spread`. Returns true when placed.
func _try(pool_or_id: String, c: Vector2, spread: float, s0 := 0.85, s1 := 1.15, yaw_bias := 0.0, pack := 1.0, road_gap := 0.05) -> bool:
	var id := pool_or_id if lib.has(pool_or_id) else lib.pick(pool_or_id)
	if id == "":
		return false
	var it := lib.get_card(id)
	var pool: String = it["pool"]
	var h: float = float(it["h"]) * rng.randf_range(s0, s1) * float(POOL_SCALE.get(pool, 1.0))
	var w: float = h * float(it["aspect"])
	var r := clampf(w * 0.6 * pack, 0.06, 1.1)
	for t in 12:
		var q := c + Vector2(rng.randf_range(-spread, spread), rng.randf_range(-spread, spread) * 0.8)
		if _blocks_view(q, h):
			continue
		if _free(q, r, road_gap):
			_reserve(q, r)
			var cross: bool = pool in CROSS_POOLS
			var yaw := rng.randf_range(-0.35, 0.35) + yaw_bias
			_place(it, h, q, yaw, cross, w)
			lib.mark(id)
			return true
	return false


func _place(it: Dictionary, h: float, q: Vector2, yaw: float, cross := false, w := -1.0, force_static := false) -> void:
	var pos := Vector3(q.x, ground.surface_y(q), q.y)
	var lean := rng.randf_range(-0.04, 0.04)
	var tilt := rng.randf_range(-0.03, 0.02)
	if w < 0.0:
		w = h * float(it["aspect"])
	if cross:
		contact.add_round(pos, clampf(w * 0.32, 0.05, 0.3), 1.0)
	else:
		contact.add(pos, yaw, w, clampf(h * 0.35, 0.04, 0.16), 1.0)
	card_count += 2 if cross else 1
	var pool: String = it["pool"]
	if pool in ["tree", "conifer", "blossom", "autumn"] and h > 0.5:
		trees.append(pos + Vector3(0, h * 0.75, 0))  # sound: bird / leaf-rustle points (top of the crown)
	if force_static or not pop_on_load or q.distance_to(_start) > pop_radius:
		statics.add(it["path"], float(it["h"]), h, pos, yaw, lean, cross, tilt)
		_last_place = {"pos": pos, "yaw": yaw, "lean": lean, "tilt": tilt, "hinge": null, "thick": CardAtlas.thickness_for(float(it["h"])) * h / float(it["h"]), "parent": null}
		return
	var base := Node3D.new()
	base.position = pos
	base.rotation = Vector3(tilt, yaw, lean)
	add_child(base)
	var hinge := PopHinge.new()
	hinge.start_up = not pop_on_load
	hinge.weight = clampf(h / 0.4, 0.4, 2.5)
	hinge.set_meta("card_h", h)
	hinge.set_meta("half_w", w * 0.5)
	base.add_child(hinge)
	hinges.append(hinge)
	var thick := clampf(h * 0.04, 0.011, 0.04)  # r3: thicker board
	_last_place = {"pos": pos, "yaw": yaw, "lean": lean, "tilt": tilt, "hinge": hinge, "thick": thick, "parent": hinge}
	var rec := -1
	if cross:
		var cc := CrossCard.new()
		cc.texture_a = _tex_of(it["path"])
		cc.height = h
		cc.thickness = thick
		hinge.add_child(cc)
	else:
		# perf: the card (PaperCard at height h, printed back) is drawn by CardBatch; the hinge still animates it.
		rec = batch.add_hinged(hinge, it["path"], float(it["h"]), h, thick)
	if SWAY_POOLS.has(pool) and rng.randf() < 0.7:
		var amp := float(SWAY_POOLS[pool]) * rng.randf_range(0.6, 1.2)
		var freq := rng.randf_range(0.35, 0.7)
		var phase := rng.randf() * TAU
		if rec >= 0:
			batch.set_sway(rec, amp, freq, phase)  # same rocking, in the card shader
		else:
			sway.add(base, amp, freq, phase)


## perf: every print of the card library goes into the shared atlas on the first spread, so later spreads (other
## views pick a few other prints) never rebuild it during a page turn.
func _preload_catalog() -> void:
	for id in lib.cards:
		var e: Dictionary = lib.cards[id]
		batch.atlas.index_of(e["path"], float(e["h"]))


func _tex_of(path_: String) -> Texture2D:
	if not _tex.has(path_):
		_tex[path_] = load(path_)
	return _tex[path_]


func _road_at(f: float) -> Array:
	## [point, tangent] on the road at fraction f (0 = near end, 1 = far end)
	var line := ground.path_line()
	var i := clampi(int(f * (line.size() - 1)), 1, line.size() - 2)
	return [line[i], (line[i + 1] - line[i - 1]).normalized()]


# ------------------------------------------------------------------ dressing

func _dress() -> void:
	slicer.phase("dress_bridge")
	await _bridge()
	await slicer.tick()
	slicer.phase("dress_road_edges")
	await _road_edges()
	await slicer.tick()
	slicer.phase("dress_village")
	await _village(Vector2(-4.4, -4.2))
	await slicer.tick()
	slicer.phase("dress_wheat_field")
	await _wheat_field(Vector2(5.6, 3.2))
	await slicer.tick()
	slicer.phase("dress_forest_edge")
	await _forest_edge()
	await slicer.tick()
	slicer.phase("dress_back_hills")
	await _back_hills()
	await slicer.tick()
	slicer.phase("dress_rocks_and_folds")
	await _rocks_and_folds()
	await slicer.tick()
	slicer.phase("dress_stream_banks")
	await _stream_banks()
	await slicer.tick()
	slicer.phase("dress_meadow_groves")
	await _meadow_groves()
	await slicer.tick()
	slicer.phase("dress_tree_rows")
	await _tree_rows()
	await slicer.tick()
	slicer.phase("dress_foreground")
	await _foreground()
	await slicer.tick()
	slicer.phase("dress_lens_foreground")
	await _lens_foreground()
	await slicer.tick()
	slicer.phase("dress_meadow_fill")
	await _meadow_fill()
	await slicer.tick()


func _bridge() -> void:
	var line := ground.path_line()
	var bi := 0
	var bd := INF
	for i in line.size():
		await slicer.tick()
		var d := absf(ground.stream_distance(line[i]) + ground.stream_width * 0.5)
		if d < bd:
			bd = d
			bi = i
	var t := (line[mini(bi + 3, line.size() - 1)] - line[maxi(bi - 3, 0)]).normalized()
	var n := Vector2(-t.y, t.x)
	var yaw := atan2(-t.y, t.x)  # card plane along the road (rails)
	for sd: float in [-1.0, 1.0]:
		await slicer.tick()
		var q := line[bi] + n * sd * (ground.path_width * 0.5 + 0.05)
		_reserve(q, 0.4)
		# r2: rail cards (fence prints) standing along both edges of the deck
		for k in 2:
			var fid := lib.pick("fence")
			if fid != "":
				var qq := q + t * (float(k) - 0.5) * 0.42
				_place(lib.get_card(fid), 0.17, qq, yaw + (PI if sd < 0 else 0.0), false, 0.4)
	# reeds and a duck pair by the bridge
	for k in 6:
		await slicer.tick()
		_try("reeds", line[bi] + n * rng.randf_range(-1.6, 1.6), 0.35, 0.8, 1.1)
	for k in 2:
		await slicer.tick()
		_try("water_animal", line[bi] + n * rng.randf_range(0.9, 2.0) * (1 if k == 0 else -1), 0.3)


## A raised verge runs along the road; low hedges, flowers and grass stand on it with gaps;
## milestones / signposts / lanterns now and then. Card planes run along the road.
func _road_edges() -> void:
	var line := ground.path_line()
	var step := 5
	for i in range(step, line.size() - step, step):
		await slicer.tick()
		var tn := (line[i + 1] - line[i - 1]).normalized()
		var yaw := atan2(-tn.y, tn.x)
		for sd: float in [-1.0, 1.0]:
			if rng.randf() < 0.3:
				continue
			var nn := Vector2(-tn.y, tn.x) * sd
			var c := line[i] + nn * (ground.path_width * 0.5 + ground.verge_w * 0.55)
			var r := rng.randf()
			var pool := "hedge" if r < 0.4 else ("grass" if r < 0.65 else ("flower" if r < 0.88 else "bush"))
			_try(pool, c, 0.03, 0.75, 1.0, yaw * 0.25, 0.45, -0.2)
	for f in [0.12, 0.33, 0.52, 0.71, 0.9]:
		await slicer.tick()
		var ra := _road_at(f)
		var n := Vector2(-ra[1].y, ra[1].x) * (1.0 if rng.randf() < 0.5 else -1.0)
		var props := ["village_signpost", "meadow_field_25", "village_lantern_post", "forest_conifer_22", "village_props_04"]
		var id: String = props[rng.randi() % props.size()]
		if lib.has(id):
			_try(id, ra[0] + n * (ground.path_width * 0.5 + 0.35), 0.05, 0.9, 1.0, atan2(-ra[1].y, ra[1].x) * 0.3)


func _village(c: Vector2) -> void:
	ground.add_patch(c + Vector2(0.4, 0.4), 1.6, 2)
	var houses := lib.query("building", [], "", "") + lib.query("house")
	var keep := []
	for id in houses:
		await slicer.tick()
		var e := lib.get_card(id)
		if e["pool"] == "house" and not ("castle" in e["label"] or "tower" in e["label"] or "chapel" in e["label"] or "windmill" in e["label"] or "market" in e["label"] or "gatehouse" in e["label"]):
			keep.append(id)
	var spots := [Vector2(-1.4, -0.8), Vector2(0.2, -1.4), Vector2(1.6, -0.6), Vector2(-2.6, 0.4), Vector2(-0.4, 0.6), Vector2(2.2, 0.9), Vector2(-1.6, 1.8)]
	for s in spots:
		await slicer.tick()
		var id := lib.pick(keep)
		var e := lib.get_card(id)
		var h: float = float(e["h"]) * rng.randf_range(0.95, 1.1)
		var q: Vector2 = c + s + Vector2(rng.randf_range(-0.2, 0.2), rng.randf_range(-0.2, 0.2))
		var r := h * float(e["aspect"]) * 0.6
		if _free(q, r):
			_reserve(q, r)
			var yaw := rng.randf_range(-0.3, 0.3)
			var sw: Dictionary = (Building.kit().get("swap", {}) as Dictionary).get(id, {})
			if not sw.is_empty():  # 2026-11-23: an open pavilion card stands as the kit's 3D pavilion
				var pb := _place_building(str(sw["preset"]), h / float(sw.get("h", 1.0)), q, yaw, h * float(e["aspect"]))
				house_cards.append({"id": id, "path": e["path"], "h0": float(e["h"]), "h": h,
					"pos": Vector3(q.x, ground.surface_y(q), q.y), "yaw": yaw, "lean": 0.0, "tilt": 0.0, "hinge": null,
					"thick": 0.0, "body": pb,
					"body_node": pb.get_parent() if pb and not (pb.get_parent() is PopHinge) else null,
					"w": h * float(e["aspect"]), "building": true})
				lib.mark(id)
				_houses.append([Vector3(q.x, ground.surface_y(q), q.y), h, yaw, h * float(e["aspect"])])
				continue
			_place(e, h, q, yaw, false)
			var hb := _add_house_body(id, e, h)
			house_cards.append({"id": id, "path": e["path"], "h0": float(e["h"]), "h": h, "pos": _last_place["pos"],
				"yaw": yaw, "lean": _last_place["lean"], "tilt": _last_place["tilt"], "hinge": _last_place["hinge"],
				"thick": _last_place["thick"], "body": hb,
				"body_node": hb.get_parent() if hb and _last_place["hinge"] == null else null,
				"w": h * float(e["aspect"])})
			lib.mark(id)
			_houses.append([Vector3(q.x, ground.surface_y(q), q.y), h, yaw, h * float(e["aspect"])])
	# yard props, fences, lanterns, a well, washing line, garden flowers
	for k in 14:
		await slicer.tick()
		_try("prop", c + Vector2(rng.randf_range(-2.4, 2.6), rng.randf_range(-1.6, 2.2)), 0.3, 0.95, 1.1)
	for k in 6:
		await slicer.tick()
		_try("fence", c + Vector2(rng.randf_range(-2.4, 2.6), rng.randf_range(0.6, 2.4)), 0.2, 0.95, 1.05)
	for k in 6:
		await slicer.tick()
		_try("farm_animal", c + Vector2(rng.randf_range(-1.6, 2.6), rng.randf_range(0.4, 2.4)), 0.4, 1.0, 1.15)
	for k in 10:
		await slicer.tick()
		_try("blossom" if k % 3 == 0 else "tree", c + Vector2(rng.randf_range(-3.2, 3.0), rng.randf_range(-2.6, -0.6)), 0.6, 0.8, 1.1)
	for k in 24:
		await slicer.tick()
		_try("flower" if k % 2 == 0 else "bush", c + Vector2(rng.randf_range(-2.8, 2.8), rng.randf_range(-1.8, 2.6)), 0.4, 0.8, 1.05)


## A kit building (Building) standing where the template picked a card: on a hinge that rises in the page wave.
func _place_building(preset: String, sc: float, q: Vector2, yaw: float, w: float) -> Node3D:
	var pos := Vector3(q.x, ground.surface_y(q), q.y)
	contact.add(pos, yaw, w, 0.16, 1.0)
	var base := Node3D.new()
	base.position = pos
	base.rotation.y = yaw
	add_child(base)
	var b := Building.make(preset, sc)
	if b == null:
		return null
	if pop_on_load and q.distance_to(_start) <= pop_radius:
		var hinge := PopHinge.new()
		hinge.start_up = not pop_on_load
		hinge.weight = 2.0
		hinge.set_meta("card_h", 1.0)
		hinge.set_meta("half_w", w * 0.5)
		base.add_child(hinge)
		hinges.append(hinge)
		hinge.add_child(b)
	else:
		base.add_child(b)
	return b


## The house card's body (2026-11-23, HouseBody): the front's outline extruded back, on the card's hinge (it pops up
## and folds with the card) or, for a static far card, at the card's transform.
func _add_house_body(id: String, e: Dictionary, h: float) -> HouseBody:
	var tex := _tex_of(e["path"])
	var b := HouseBody.for_card(id, tex, h, float(_last_place["thick"]), -1.0, 0.05)
	if b == null:
		return null
	var hg: Variant = _last_place["hinge"]
	if hg != null:
		(hg as Node3D).add_child(b)
	else:
		var n := Node3D.new()
		n.name = "HouseBodyStatic"
		n.position = _last_place["pos"]
		n.basis = Basis(Vector3.UP, float(_last_place["yaw"])) * Basis(Vector3.BACK, float(_last_place["lean"])) * Basis(Vector3.RIGHT, float(_last_place["tilt"]))
		add_child(n)
		n.add_child(b)
	return b


func _wheat_field(c: Vector2) -> void:
	# Broken rows of wheat cards on the field tier, with a haystack clearing and a cart.
	var rows := 7
	for rI in rows:
		await slicer.tick()
		var z := c.y - 1.8 + rI * 0.55
		var x0 := c.x - 2.6 + rng.randf_range(-0.3, 0.4)
		var x1 := c.x + 2.4 + rng.randf_range(-0.6, 0.3)
		var x := x0
		while x < x1:
			if rng.randf() < 0.12:
				x += rng.randf_range(0.4, 0.9)
				continue
			_try("crop", Vector2(x, z + rng.randf_range(-0.06, 0.06)), 0.02, 0.85, 1.15, rng.randf_range(-0.1, 0.1), 0.55)
			x += rng.randf_range(0.18, 0.3)
	for id in ["meadow_field_05", "field_haystack", "field_hay_cart", "meadow_field_06", "field_wheat_stook", "village_props_04"]:
		await slicer.tick()
		if lib.has(id):
			_try(id, c + Vector2(rng.randf_range(-2.0, 2.0), rng.randf_range(-1.6, 1.6)), 0.4)
	for k in 6:
		await slicer.tick()
		_try("fence", c + Vector2(-3.0 + k * 0.5, 2.3), 0.05, 0.95, 1.05, 0.0, 0.8)
	_try("wild_animal", c + Vector2(0.4, 0.2), 1.0)
	_try("farm_animal", c + Vector2(-1.2, 1.4), 0.8)


func _forest_edge() -> void:
	# Right-back forest on the high tiers, left-back pine line, conifers fading into haze.
	for c in [Vector2(8.6, -3.0), Vector2(5.4, -6.6), Vector2(9.8, -6.8), Vector2(2.8, -8.4), Vector2(-9.8, -6.2), Vector2(-4.2, -8.8), Vector2(11.0, -1.0)]:
		await slicer.tick()
		ground.add_patch(c, 1.3, 5)
		for i in 16:
			_try("conifer" if i % 3 != 2 else "tree", c, 1.6, 0.8, 1.3, 0.0, 0.7)
		for i in 10:
			_try("bush" if i % 2 == 0 else "sapling", c + Vector2(0, 0.6), 1.7, 0.8, 1.1)
		for i in 4:
			_try("mushroom" if i % 2 == 0 else "wild_animal", c + Vector2(0, 0.8), 1.5)


func _back_hills() -> void:
	# Three rows of cut hill cards along the far edge: layered silhouettes for the haze to eat.
	var ids: Array = lib.pools.get("hill", []).filter(func(i): return not (i in ["hills_clouds_03", "hills_clouds_10", "hills_clouds_14", "hills_clouds_19", "hills_clouds_22",
		"hills_clouds_02", "hills_clouds_05", "hills_clouds_07", "hills_clouds_24", "hills_clouds_00", "hills_clouds_08", "hills_clouds_13", "hills_clouds_09"]))  # LOOKF r1: low lens shows the back rows; ochre/salmon slabs out  # r2/r4: red fields too loud
	for row in 3:
		await slicer.tick()
		var z := -9.0 + row * 0.55
		var x := -13.0 + rng.randf_range(0.0, 1.0)
		while x < 13.0:
			var id := lib.pick(ids)
			var e := lib.get_card(id)
			var h: float = float(e["h"]) * rng.randf_range(1.2, 1.7) * (1.25 - row * 0.15)
			var w: float = h * float(e["aspect"])
			var q := Vector2(x + w * 0.5, z + rng.randf_range(-0.15, 0.15))
			_reserve(q, 0.3)
			_place(e, h, q, rng.randf_range(-0.08, 0.08), false, w, true)
			lib.mark(id)
			x += w * rng.randf_range(0.55, 0.85)


func _rocks_and_folds() -> void:
	# r2: printed rock cards (critic: the grey folded triangles killed the frame).
	for c in [Vector2(-2.6, 2.0), Vector2(2.4, 0.6), Vector2(-4.0, -1.6), Vector2(2.2, -3.8), Vector2(-2.6, 5.6),
			Vector2(3.6, 6.8), Vector2(-9.0, 4.2), Vector2(8.6, 5.4), Vector2(-1.6, -6.4), Vector2(7.4, -1.6)]:
		for i in rng.randi_range(2, 4):
			_try("rock", c, 0.55, 0.9 if i > 0 else 1.3, 1.2 if i > 0 else 1.6)
		for i in 5:
			_try("grass" if i % 2 == 0 else "flower", c, 0.7)
	# Folded paper hillocks: big green V-folded tents, mid and back.
	var greens := [Color("6f8a58"), Color("7d955f"), Color("8a9a62"), Color("66804f")]
	for c in [Vector2(-3.4, -5.2), Vector2(1.8, -6.0), Vector2(-8.6, -0.6), Vector2(8.2, 0.6), Vector2(-5.0, 6.8), Vector2(7.8, -5.0), Vector2(-11.0, -4.0), Vector2(11.4, -3.6)]:
		await slicer.tick()
		var s := rng.randf_range(0.34, 0.52)
		if _free(c, s * 2.2):
			_reserve(c, s * 2.2)
			ground.add_folded_rock(c, s, rng.randf_range(-0.3, 0.3), greens[rng.randi() % greens.size()])
			contact.add_round(Vector3(c.x, ground.surface_y(c), c.y), s * 1.6, 0.9)
			for i in 4:
				_try("bush" if i % 2 == 0 else "sapling", c + Vector2(0, 0.6), 0.8)


func _stream_banks() -> void:
	var line := ground.stream_line()
	for i in range(2, line.size() - 2, 3):
		await slicer.tick()
		if rng.randf() < 0.35:
			continue
		var tn := (line[i + 1] - line[i - 1]).normalized()
		var sd := 1.0 if rng.randf() < 0.5 else -1.0
		var q := line[i] + Vector2(-tn.y, tn.x) * sd * (ground.stream_width * 0.5 + 0.12)
		var pool := "reeds" if rng.randf() < 0.6 else ("bank" if rng.randf() < 0.5 else "grass")
		for j in rng.randi_range(1, 3):
			_try(pool, q, 0.12, 0.8, 1.1, atan2(-tn.y, tn.x) * 0.5)
	for k in 8:
		await slicer.tick()
		var i := rng.randi_range(2, line.size() - 3)
		var tn := (line[i + 1] - line[i - 1]).normalized()
		_try("water_animal", line[i] + Vector2(-tn.y, tn.x) * (ground.stream_width * 0.5 + 0.08) * (1 if k % 2 == 0 else -1), 0.05)


func _meadow_groves() -> void:
	var groves := [
		[Vector2(-3.0, 3.2), ["blossom", "tree", "tree"]], [Vector2(2.8, -1.0), ["autumn", "tree"]],
		[Vector2(-8.2, 6.2), ["tree", "conifer", "autumn"]], [Vector2(9.2, 6.2), ["autumn", "conifer"]],
		[Vector2(-1.8, -2.6), ["tree", "autumn"]], [Vector2(-10.4, 1.4), ["conifer", "tree"]],
		[Vector2(3.0, 8.4), ["tree", "blossom"]], [Vector2(-5.2, 1.0), ["autumn", "tree"]],
		[Vector2(1.6, -4.4), ["conifer", "tree", "autumn"]], [Vector2(-1.6, 8.8), ["tree", "autumn"]],
	]
	for g in groves:
		await slicer.tick()
		var c: Vector2 = g[0]
		ground.add_patch(c + Vector2(0, 0.15), rng.randf_range(0.7, 1.0), 4 if rng.randf() < 0.4 else 5)
		var n := rng.randi_range(3, 6)
		for i in n:
			_try(g[1][rng.randi() % g[1].size()], c, 0.75, 0.75, 1.3, 0.0, 0.75)
		for i in n * 3:
			var skirt := ["bush", "grass", "flower", "mushroom", "sapling"]
			_try(skirt[rng.randi() % skirt.size()], c + Vector2(0, 0.35), 0.95, 0.8, 1.15)
	# sheep pasture, left meadow
	for k in 6:
		await slicer.tick()
		_try("farm_animal", Vector2(-6.4, 4.6) + Vector2(rng.randf_range(-1.4, 1.4), rng.randf_range(-0.8, 0.8)), 0.3)
	for k in 6:
		await slicer.tick()
		_try("wild_animal", Vector2(rng.randf_range(-6, 6), rng.randf_range(-6, 7)), 0.6)


## LOOKF r1: dense rows of mid-height trees (existing pools only) so a low lens sees stacked silhouettes
## row behind row, like the reference table, instead of a few giant trees on open lawn.
func _tree_rows() -> void:
	var r3 := RandomNumberGenerator.new()
	r3.seed = seed_value * 577 + 11
	for k in 40:
		await slicer.tick()
		var c := Vector2(r3.randf_range(-11.5, 11.5), r3.randf_range(-7.5, 8.0))
		if c.distance_to(_start) < 2.2:
			continue
		var ang := r3.randf_range(-0.45, 0.45)
		var dirv := Vector2(cos(ang), sin(ang))
		var n := r3.randi_range(5, 9)
		var conif := r3.randf() < 0.6
		for i in n:
			var q := c + dirv * (float(i) - n * 0.5) * r3.randf_range(0.34, 0.5) + Vector2(0, r3.randf_range(-0.22, 0.22))
			var pool: String = "conifer" if (conif and r3.randf() < 0.8) else (["tree", "autumn", "tree", "blossom"][r3.randi() % 4])
			_try(pool, q, 0.08, 0.6, 0.95, 0.0, 0.5)
		for i in n:
			_try("bush" if i % 2 == 0 else "grass", c + dirv * r3.randf_range(-n * 0.2, n * 0.2) + Vector2(0, 0.3), 0.3, 0.8, 1.1)


## Tall near-lens cards along both sides of the road: whichever stretch the camera follows, some stand
## between it and the traveller's band and fall into the near blur (overlap, depth).
func _foreground() -> void:
	var line := ground.path_line()
	for i in range(6, line.size() - 6, 9):
		await slicer.tick()
		var tn := (line[i + 1] - line[i - 1]).normalized()
		for sd: float in [-1.0, 1.0]:
			if rng.randf() < 0.35:
				continue
			var q := line[i] + Vector2(-tn.y, tn.x) * sd * rng.randf_range(1.1, 1.9)
			var pool: String = ["grass", "bush", "tree", "flower", "conifer"][rng.randi() % 5]
			_try(pool, q, 0.2, 1.1, 1.4)


## Camera dressing for the start view: 3-5 tall cards in the band just above the bottom frame edge,
## left and right of the traveller's line (they land in the near blur and overlap the meadow).
## Uses its own RNG (seed, view) so the shared layout stays identical across views.
func _lens_foreground() -> void:
	var r2 := RandomNumberGenerator.new()
	r2.seed = seed_value * 131 + view
	var to_cam := (_cam_ground - _start).normalized()
	var right := Vector2(-to_cam.y, to_cam.x)
	# r4: low cards at the frame edges only (r3's huge blurred bush blocked the bottom third)
	var pools := ["grass", "flower", "grass", "sapling"]
	var saved := rng
	rng = r2
	for k in 4:
		await slicer.tick()
		var side := -1.0 if k % 2 == 0 else 1.0
		var q := _start + to_cam * r2.randf_range(2.4, 3.2) + right * side * r2.randf_range(1.5, 2.4)
		_try(pools[r2.randi() % pools.size()], q, 0.2, 0.95, 1.15)
	rng = saved


func _meadow_fill() -> void:
	var pools := ["flower", "grass", "bush", "flower", "mushroom", "grass", "rock", "sapling", "flower"]
	for k in 1100:
		await slicer.tick()
		var c := Vector2(rng.randf_range(-12.5, 12.5), rng.randf_range(-8.0, 9.0))
		var base: String = pools[rng.randi() % pools.size()]
		# r2: clumps where the mask is high, open felt clearings where it is low (no even confetti)
		var m := _fill_mask.get_noise_2d(c.x, c.y)
		if m < -0.22 or rng.randf() > 0.6 + m * 1.4:
			# r3: open felt keeps a sparse ground cover (single low tufts) so clearings are not bare sheet
			if m > -0.6 and rng.randf() < 0.6:  # r4: denser low cover (critic: large empty green fields)
				for j in rng.randi_range(1, 3):
					_try("grass" if rng.randf() < 0.55 else "flower", c, 0.14, 0.55, 0.8)
			continue
		# r3: tight overlapping clumps of 3-7 (front/mid/back), not even scatter
		for j in rng.randi_range(3, 7):
			_try(base if j < 2 else pools[rng.randi() % pools.size()], c, 0.22, 0.8, 1.15, 0.0, 0.62)
	# r4: low ground-cover pass (tiny grass/flower tufts) so open felt reads as meadow, not an empty sheet
	for k in 1150:  # LOOKF r1: was 1800; the low lens + DOF hide the tiniest tufts, the budget goes to tree rows
		await slicer.tick()
		var c := Vector2(rng.randf_range(-12.5, 12.5), rng.randf_range(-8.0, 9.0))
		if c.distance_to(_start) < HERO_CLEAR * 0.7:
			continue
		_try("grass" if rng.randf() < 0.65 else "flower", c, 0.05, 0.6, 0.9, 0.0, 0.7)


# ------------------------------------------------------------------ traveller, camera, life

func _build_camera_and_traveller(v: Array, off: float) -> void:
	rig = LookRig.new()
	rig.name = "LookRig"
	rig.elevation_deg = v[1]
	rig.yaw_deg = v[2]
	rig.distance = v[3]
	rig.fov = v[4]
	rig.follow_smooth = 0.0
	rig.focus_height = 0.18
	# r3: more lens character (critic: "reads as a game camera"); r1 showed 30-40% smear is too much.
	# LOOKF r1: macro lens - thin sharp slab around the traveller, strong near and far blur.
	rig.dof_near_margin = 0.7
	rig.dof_far_margin = 1.1
	rig.dof_near_transition = 1.6
	rig.dof_far_transition = 3.0
	rig.dof_amount = 0.12
	rig.tilt_blur = 0.5
	rig.lens_soft = 0.14
	rig.grain = 0.035
	rig.toe = 0.3
	rig.post_contrast = 1.1
	rig.tilt_focus_y = 0.55
	rig.tilt_band_half = 0.16
	rig.tilt_band_soft = 0.36
	# LOOKF r1: low raking warm key from the side, weak fill: long cast shadows, dark shadow sides.
	rig.key_elevation_deg = 25.0
	rig.key_yaw_deg = -70.0
	rig.key_color = Color("ffdab0")
	rig.key_energy = 2.7
	rig.shadow_opacity = 0.93
	rig.shadow_softness = 1.0
	rig.fill_energy = 0.34
	rig.ambient_energy = 0.37
	rig.exposure = 0.86
	rig.vignette = 0.24
	rig.post_saturation = 0.84
	rig.haze_color = Color("b4bd9c")  # LOOKF r1: less orange haze (far rows went salmon under the low key)
	rig.haze_begin = 1.0
	rig.haze_length = 6.0
	rig.haze_amount = 0.72
	add_child(rig)
	walker = Walker.new()
	walker.name = "Traveller"
	walker.path = path
	walker.camera = rig.camera
	walker.speed = 0.3
	walker.start_offset = off
	walker.auto_walk = walk
	add_child(walker)
	puppet = PaperPuppet.new()
	puppet.name = "Puppet"
	puppet.height = 0.36
	puppet.camera = rig.camera
	walker.add_child(puppet)
	contact.add(walker.global_position, 0.0, 0.14, 0.07, 1.0)
	# LOOKF r1: a small warm bounce card for the hero (photographers flag a reflector at the subject):
	# keeps the traveller readable when a long tree shadow crosses the road.
	var hero := OmniLight3D.new()
	hero.name = "HeroBounce"
	hero.light_color = Color("ffe2b8")
	hero.light_energy = 0.55
	hero.omni_range = 1.5
	hero.omni_attenuation = 1.4
	hero.light_specular = 0.0
	hero.shadow_enabled = false
	hero.position = Vector3(-0.25, 0.55, 0.75)
	walker.add_child(hero)
	focus = FollowFocus.new()
	focus.name = "CamFocus"
	focus.target = walker
	add_child(focus)
	focus.snap()
	rig.focus_target = focus
	rig.snap()


func _build_life() -> void:
	var amb := PaperAmbient.new()
	amb.name = "Ambient"
	amb.area = Rect2(_start.x - 2.5, _start.y - 2.5, 5.0, 4.0)
	amb.butterflies = 4
	amb.leaves = 6
	amb.seed_value = seed_value
	amb.position.y = 0.03
	add_child(amb)
	# 2026-11-23 (user: "왜 자꾸 이상한데서 김이 모락모락", "또 라푼젤에도 김이 있네"): template chimney smoke guessed a
	# chimney spot from the card size and kept rising over cleared lots, thatch with no chimney, story houses. Off by
	# default in every world; steam/smoke only where a tale places it on something hot (e.g. turnip's pot).
	if not chimney_smoke:
		return
	for hz in _houses:
		var p: Vector3 = hz[0]
		var smoke := ChimneySmoke.new()
		smoke.position = p + Vector3(float(hz[3]) * 0.22, float(hz[1]) * 0.92, -0.02)
		add_child(smoke)
		if _houses.find(hz) >= 3:
			break
