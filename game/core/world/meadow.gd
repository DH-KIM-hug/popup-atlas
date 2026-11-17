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
@export var pop_radius := 4.2  ## cards within this distance of the traveller are hinged and rise in the wave
@export var walk := true
@export var with_audio := true

## road fraction, cam elevation, yaw, distance, fov
## r2: closer lens (distance ~7.3) so the traveller is the focal point, not a 20 px smudge.
const VIEWS := [
	## r3: lower lens (21-23°) for more overlap and a longer view into the haze, like the footage.
	[0.36, 22.0, 10.0, 7.4, 20.0],
	[0.46, 21.0, -24.0, 7.4, 20.0],
	[0.555, 23.0, 32.0, 7.2, 20.0],
	[0.62, 22.0, 26.0, 7.6, 20.0],
	[0.72, 21.0, 16.0, 7.4, 20.0],
	[0.28, 22.0, -30.0, 7.4, 20.0],
]
## r3: small props scaled down so the 0.36 traveller reads above the flowers (critic: "hero is the height of a flower")
const POOL_SCALE := {"conifer": 1.5, "tree": 1.25, "autumn": 1.2, "blossom": 1.15, "house": 1.0, "rock": 1.5,
	"flower": 0.72, "grass": 0.8, "mushroom": 0.75, "bush": 0.85, "sapling": 0.85, "hedge": 0.85}
const HERO_CLEAR := 1.3  ## r2: open clearing around the traveller (hierarchy, negative space)
## r4: no cross-slotted cards. The slotted second card, seen edge-on, read as a white seam through trees (critic).
## PE r2: back on a share of trees/bushes with real half-slots, print on both faces, print-coloured cut edges,
## the pair turned ~45° off the view axis. The choice is a hash of the site, NOT the layout RNG, so the r4
## spread (which the art director and editor liked) stays card-for-card identical (PE r1 reshuffled it).
const CROSS_POOLS: Array[String] = ["conifer", "tree", "autumn", "blossom", "bush"]
const CROSS_P := {"conifer": 0.6, "tree": 0.4, "autumn": 0.35, "blossom": 0.3, "bush": 0.22}
const FOOT_MIN_H := 0.2  ## PE r2: cards this tall get a glued foot tab (r1 0.14: tabs under flowers read as plaques)
const STRUT_MIN_H := 0.5  ## static cards this tall get an easel strut behind
## PE r3: low wide pieces turn off the print plane by a site hash (not the layout RNG), so their cut edges and
## glue feet show in perspective instead of every card facing the lens like a billboard.
const TURN_POOLS := {"hedge": 0.6, "fence": 0.45, "bush": 0.4, "mushroom": 0.45, "prop": 0.35, "bank": 0.4, "crop": 0.35}
const SWAY_POOLS := {"grass": 0.07, "flower": 0.06, "reeds": 0.08, "crop": 0.05, "tree": 0.018, "conifer": 0.014, "blossom": 0.02, "autumn": 0.018, "bush": 0.025}

var rng := RandomNumberGenerator.new()
var lib: CardLibrary
var ground: MeadowGround
var contact: ContactShadows
var statics: StaticCards
var feet: GlueFeet
var sway: WindSway
var rig: LookRig
var walker: Walker
var puppet: PaperPuppet
var focus: FollowFocus
var path: Path3D
var audio: PaperAudio
var hinges: Array[PopHinge] = []
var card_count := 0
var wave_end := 0.0

var _tex := {}
var _grid := {}  ## Vector2i -> Array of [Vector2 pos, float r]
var _start := Vector2.ZERO  ## traveller start on the page
var _cam_ground := Vector2.ZERO
var _cam_yaw := 0.0  ## view yaw (rad); cross pairs and V-folds are turned against it
var _small_hinged: Array = []  ## PE r2: [Vector2 q, Node3D base, PopHinge, float h] low hinged cards (clearable)
var _rej := [0, 0, 0, 0]
var _houses: Array = []  ## [pos, h, yaw] for chimney smoke
var _fill_mask: FastNoiseLite  ## r2: low-frequency density mask (clearings vs clumps)


func _ready() -> void:
	rng.seed = seed_value
	seed(seed_value * 7919 + view)
	if fixed_step:
		PopHinge.fixed_dt = 1.0 / 60.0
		PaperSpring.fixed_dt = 1.0 / 60.0
	lib = CardLibrary.new(rng)
	_build_ground()
	_build_walk_path()
	var v: Array = VIEWS[clampi(view, 0, VIEWS.size() - 1)]
	var off: float = path.curve.get_baked_length() * float(v[0])
	var sp := path.curve.sample_baked(off)
	_start = Vector2(sp.x, sp.z)
	var yw := deg_to_rad(float(v[2]))
	_cam_ground = _start + Vector2(sin(yw), cos(yw)) * float(v[3]) * cos(deg_to_rad(float(v[1])))
	_cam_yaw = yw
	feet = GlueFeet.new()
	feet.name = "GlueFeet"
	contact = ContactShadows.new()
	contact.name = "ContactShadows"
	statics = StaticCards.new()
	statics.name = "StaticCards"
	sway = WindSway.new()
	sway.name = "Wind"
	add_child(sway)
	_reserve(_start, HERO_CLEAR)
	_fill_mask = FastNoiseLite.new()
	_fill_mask.seed = seed_value * 17 + 3
	_fill_mask.frequency = 0.16
	_dress()
	contact.commit()
	add_child(contact)
	add_child(statics)
	statics.commit()
	add_child(feet)
	feet.commit()
	_build_camera_and_traveller(v, off)
	_build_life()
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
	print("MEADOW seed=", seed_value, " view=", view, " cards=", card_count, " hinged=", hinges.size(),
		" static=", statics.count, " ids=", lib.used.size(), " tiers=", ground.tier_count(), " wave_end=", snappedf(wave_end, 0.01))
	built.emit()


# ------------------------------------------------------------------ ground

func _build_ground() -> void:
	ground = MeadowGround.new()
	ground.name = "Ground"
	ground.seed_value = seed_value
	ground.page_size = Vector2(28.0, 20.0)
	ground.cover_patches = 28  # r2: fewer pale lobes (read as spilled paint)
	ground.felt_color = Color("7f9670")
	ground.felt_mottle = Color("5f7652")
	ground.felt_mottle_strength = 1.0
	ground.path_color = Color("d9bf8a")  # r2: warm sand road (cream cut edge now contrasts)
	ground.path_width = 0.5
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
	add_child(ground)
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
	if ground.path_distance(p) < r * 0.45 + road_gap or ground.stream_distance(p) < r * 0.45 + 0.06:
		return false
	var k := _cell(p)
	for dx in range(-2, 3):
		for dz in range(-2, 3):
			for q in _grid.get(k + Vector2i(dx, dz), []):
				if (q[0] as Vector2).distance_to(p) < (r + float(q[1])) * 0.5:
					return false
	return true


## PE r2: like _free, but ignores small reservations (tufts < 0.12) so built clusters can sit in the lawn.
func _free_big(p: Vector2, r: float) -> bool:
	if not ground.on_page(p, 0.4):
		return false
	var k := _cell(p)
	for dx in range(-2, 3):
		for dz in range(-2, 3):
			for q in _grid.get(k + Vector2i(dx, dz), []):
				if float(q[1]) >= 0.16 and (q[0] as Vector2).distance_to(p) < (r + float(q[1])) * 0.5:
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
			var cross: bool = pool in CROSS_POOLS and h > 0.22 and _hash01(q, 11) < float(CROSS_P.get(pool, 0.0))
			var yaw := rng.randf_range(-0.35, 0.35) + yaw_bias
			if cross:
				# both cards ~45° off the view axis (A to one side, B to the other), never edge-on
				yaw = _cam_yaw + (PI * 0.25 if yaw >= yaw_bias else -PI * 0.25) + (yaw - yaw_bias) * 0.25
			elif TURN_POOLS.has(pool):
				yaw += (_hash01(q, 31) - 0.5) * 2.0 * float(TURN_POOLS[pool])
			_place(it, h, q, yaw, cross, w)
			lib.mark(id)
			return true
	return false


func _place(it: Dictionary, h: float, q: Vector2, yaw: float, cross := false, w := -1.0, force_static := false, vfold := -1.0) -> void:
	var pos := Vector3(q.x, ground.surface_y(q), q.y)
	var lean := rng.randf_range(-0.04, 0.04)
	var tilt := rng.randf_range(-0.03, 0.02)
	if w < 0.0:
		w = h * float(it["aspect"])
	var pool: String = it["pool"]
	if vfold < 0.0:
		vfold = 0.0
		if pool == "rock" and h > 0.07:
			# PE r2: rocks are V-folded cards, a mountain crease toward the lens (one lit, one shadow face).
			# Angle and yaw from a site hash, so the layout RNG is untouched.
			vfold = lerpf(0.5, 0.72, _hash01(q, 23))
			yaw = _cam_yaw + clampf(yaw - _cam_yaw, -0.4, 0.4) * 0.6
	if vfold > 0.0:
		lean = 0.0
		tilt = 0.0
	if cross or vfold > 0.0:
		contact.add_round(pos, clampf(w * (0.32 if cross else 0.26), 0.05, 0.3), 1.0)
	else:
		contact.add(pos, yaw, w, clampf(h * 0.35, 0.04, 0.16), 1.0)
	card_count += 2 if (cross or vfold > 0.0) else 1
	var is_static := force_static or not pop_on_load or q.distance_to(_start) > pop_radius
	if is_static and h >= STRUT_MIN_H and not cross and vfold <= 0.0 and pool != "hill":
		tilt = -0.055 + tilt * 0.5  # PE r3: tall static cards rest back on their easel strut (not a vertical billboard)
	_add_feet(it, h, pos, yaw, cross, vfold, is_static, lean, tilt)
	if is_static:
		statics.add(it["path"], float(it["h"]), h, pos, yaw, lean, cross, tilt, vfold)
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
	if h < 0.26 and not cross and vfold <= 0.0:
		_small_hinged.append([q, base, hinge, h])
	var thick := clampf(h * 0.04, 0.011, 0.04)  # r3: thicker board
	if cross:
		var cc := CrossCard.new()
		cc.texture_a = _tex_of(it["path"])
		cc.height = h
		cc.thickness = thick
		hinge.add_child(cc)
	elif vfold > 0.0:
		for sd: int in [-1, 1]:
			var face := PaperCard.new()
			# shift each face toward the crease so the two printed faces meet on one fold line (no V gap)
			face.position.x = -sd * thick * 0.5 * sin(vfold)
			face.texture = _tex_of(it["path"])
			face.height = h
			face.thickness = thick
			face.back_print = true
			face.half = sd
			face.edge_from_print = true
			face.rotation.y = vfold * sd
			hinge.add_child(face)
	else:
		var card := PaperCard.new()
		card.texture = _tex_of(it["path"])
		card.height = h
		card.thickness = thick
		card.back_print = true
		hinge.add_child(card)
	if SWAY_POOLS.has(pool) and rng.randf() < 0.7:
		sway.add(base, float(SWAY_POOLS[pool]) * rng.randf_range(0.6, 1.2), rng.randf_range(0.35, 0.7), rng.randf() * TAU)


## Deterministic 0..1 from a site (does not touch the layout RNG).
func _hash01(q: Vector2, salt: int) -> float:
	var hv := hash(Vector3i(int(round(q.x * 1000.0)), int(round(q.y * 1000.0)), salt * 7919 + seed_value))
	return float(hv & 0xFFFFFF) / float(0xFFFFFF)


## Glue foot tab (and an easel strut behind tall static cards), coloured from the print's base.
func _add_feet(it: Dictionary, h: float, pos: Vector3, yaw: float, cross: bool, vfold: float, is_static: bool, lean := 0.0, tilt := 0.0) -> void:
	var pool: String = it["pool"]
	if h < FOOT_MIN_H or pool == "hill":
		return
	var bi := PaperCard.base_info(_tex_of(it["path"]))
	var col: Color = (bi["col"] as Color).darkened(0.12)
	var thick := clampf(h * 0.04, 0.011, 0.04)
	var depth := clampf(h * 0.1, 0.03, 0.07)  # PE r3: 7.5% -> 10% of h (tabs were too small to read at view distance)
	var x0: float = float(bi["x0"]) * h
	var x1: float = float(bi["x1"]) * h
	if vfold > 0.0:
		feet.add_foot(pos, yaw, minf(x0, -0.01), 0.0, thick, depth, col, -vfold)
		feet.add_foot(pos, yaw, 0.0, maxf(x1, 0.01), thick, depth, col, vfold)
		return
	feet.add_foot(pos, yaw, x0, x1, thick, depth, col)
	if cross:
		feet.add_foot(pos, yaw, -x1, -x0, thick, depth, col, PI)
		return
	if is_static and h >= STRUT_MIN_H:
		feet.add_strut(pos, yaw, h, thick, col.darkened(0.1))


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
	_bridge()
	_road_edges()
	_village(Vector2(-4.4, -4.2))
	_wheat_field(Vector2(5.6, 3.2))
	_forest_edge()
	_back_hills()
	_rocks_and_folds()
	_stream_banks()
	_meadow_groves()
	_foreground()
	_lens_foreground()
	_meadow_fill()
	# PE r2: built mechanisms go into the gaps the r4 layout left, on a side RNG (layout stays identical)
	var saved_state := rng.state
	rng.seed = seed_value * 977 + 5
	_folded_platforms()
	_purposeful_clusters()
	rng.state = saved_state


func _bridge() -> void:
	var line := ground.path_line()
	var bi := 0
	var bd := INF
	for i in line.size():
		var d := absf(ground.stream_distance(line[i]) + ground.stream_width * 0.5)
		if d < bd:
			bd = d
			bi = i
	var t := (line[mini(bi + 3, line.size() - 1)] - line[maxi(bi - 3, 0)]).normalized()
	var n := Vector2(-t.y, t.x)
	var yaw := atan2(-t.y, t.x)  # card plane along the road (rails)
	for sd: float in [-1.0, 1.0]:
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
		_try("reeds", line[bi] + n * rng.randf_range(-1.6, 1.6), 0.35, 0.8, 1.1)
	for k in 2:
		_try("water_animal", line[bi] + n * rng.randf_range(0.9, 2.0) * (1 if k == 0 else -1), 0.3)


## A raised verge runs along the road; low hedges, flowers and grass stand on it with gaps;
## milestones / signposts / lanterns now and then. Card planes run along the road.
func _road_edges() -> void:
	var line := ground.path_line()
	var step := 5
	for i in range(step, line.size() - step, step):
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
		var e := lib.get_card(id)
		if e["pool"] == "house" and not ("castle" in e["label"] or "tower" in e["label"] or "chapel" in e["label"] or "windmill" in e["label"] or "market" in e["label"] or "gatehouse" in e["label"]):
			keep.append(id)
	var spots := [Vector2(-1.4, -0.8), Vector2(0.2, -1.4), Vector2(1.6, -0.6), Vector2(-2.6, 0.4), Vector2(-0.4, 0.6), Vector2(2.2, 0.9), Vector2(-1.6, 1.8)]
	for s in spots:
		var id := lib.pick(keep)
		var e := lib.get_card(id)
		var h: float = float(e["h"]) * rng.randf_range(0.95, 1.1)
		var q: Vector2 = c + s + Vector2(rng.randf_range(-0.2, 0.2), rng.randf_range(-0.2, 0.2))
		var r := h * float(e["aspect"]) * 0.6
		if _free(q, r):
			_reserve(q, r)
			var yaw := rng.randf_range(-0.3, 0.3)
			_place(e, h, q, yaw, false)
			lib.mark(id)
			_houses.append([Vector3(q.x, ground.surface_y(q), q.y), h, yaw, h * float(e["aspect"])])
	# yard props, fences, lanterns, a well, washing line, garden flowers
	for k in 14:
		_try("prop", c + Vector2(rng.randf_range(-2.4, 2.6), rng.randf_range(-1.6, 2.2)), 0.3, 0.95, 1.1)
	for k in 6:
		_try("fence", c + Vector2(rng.randf_range(-2.4, 2.6), rng.randf_range(0.6, 2.4)), 0.2, 0.95, 1.05)
	for k in 6:
		_try("farm_animal", c + Vector2(rng.randf_range(-1.6, 2.6), rng.randf_range(0.4, 2.4)), 0.4, 1.0, 1.15)
	for k in 10:
		_try("blossom" if k % 3 == 0 else "tree", c + Vector2(rng.randf_range(-3.2, 3.0), rng.randf_range(-2.6, -0.6)), 0.6, 0.8, 1.1)
	for k in 24:
		_try("flower" if k % 2 == 0 else "bush", c + Vector2(rng.randf_range(-2.8, 2.8), rng.randf_range(-1.8, 2.6)), 0.4, 0.8, 1.05)


func _wheat_field(c: Vector2) -> void:
	# Broken rows of wheat cards on the field tier, with a haystack clearing and a cart.
	var rows := 7
	for rI in rows:
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
		if lib.has(id):
			_try(id, c + Vector2(rng.randf_range(-2.0, 2.0), rng.randf_range(-1.6, 1.6)), 0.4)
	for k in 6:
		_try("fence", c + Vector2(-3.0 + k * 0.5, 2.3), 0.05, 0.95, 1.05, 0.0, 0.8)
	_try("wild_animal", c + Vector2(0.4, 0.2), 1.0)
	_try("farm_animal", c + Vector2(-1.2, 1.4), 0.8)


func _forest_edge() -> void:
	# Right-back forest on the high tiers, left-back pine line, conifers fading into haze.
	for c in [Vector2(8.6, -3.0), Vector2(5.4, -6.6), Vector2(9.8, -6.8), Vector2(2.8, -8.4), Vector2(-9.8, -6.2), Vector2(-4.2, -8.8), Vector2(11.0, -1.0)]:
		ground.add_patch(c, 1.3, 5)
		for i in 16:
			_try("conifer" if i % 3 != 2 else "tree", c, 1.6, 0.8, 1.3, 0.0, 0.7)
		for i in 10:
			_try("bush" if i % 2 == 0 else "sapling", c + Vector2(0, 0.6), 1.7, 0.8, 1.1)
		for i in 4:
			_try("mushroom" if i % 2 == 0 else "wild_animal", c + Vector2(0, 0.8), 1.5)


func _back_hills() -> void:
	# Three rows of cut hill cards along the far edge: layered silhouettes for the haze to eat.
	var ids: Array = lib.pools.get("hill", []).filter(func(i): return not (i in ["hills_clouds_03", "hills_clouds_10", "hills_clouds_14", "hills_clouds_19", "hills_clouds_22"]))  # r2/r4: red fields too loud
	for row in 3:
		var z := -9.0 + row * 0.55
		var x := -13.0 + rng.randf_range(0.0, 1.0)
		while x < 13.0:
			var id := lib.pick(ids)
			var e := lib.get_card(id)
			var h: float = float(e["h"]) * rng.randf_range(1.2, 1.7) * (1.25 - row * 0.15)
			var w: float = h * float(e["aspect"])
			var q := Vector2(x + w * 0.5, z + rng.randf_range(-0.15, 0.15))
			_reserve(q, 0.3)
			# PE r2: every third hill card is a shallow V-fold (a folded ridge, not a flat print)
			var vf := 0.34 if (int(lib.used.get(id, 0)) + int(x * 3.0)) % 3 == 0 else 0.0
			_place(e, h, q, rng.randf_range(-0.08, 0.08), false, w, true, vf)
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
		if rng.randf() < 0.35:
			continue
		var tn := (line[i + 1] - line[i - 1]).normalized()
		var sd := 1.0 if rng.randf() < 0.5 else -1.0
		var q := line[i] + Vector2(-tn.y, tn.x) * sd * (ground.stream_width * 0.5 + 0.12)
		var pool := "reeds" if rng.randf() < 0.6 else ("bank" if rng.randf() < 0.5 else "grass")
		for j in rng.randi_range(1, 3):
			_try(pool, q, 0.12, 0.8, 1.1, atan2(-tn.y, tn.x) * 0.5)
	for k in 8:
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
		_try("farm_animal", Vector2(-6.4, 4.6) + Vector2(rng.randf_range(-1.4, 1.4), rng.randf_range(-0.8, 0.8)), 0.3)
	for k in 6:
		_try("wild_animal", Vector2(rng.randf_range(-6, 6), rng.randf_range(-6, 7)), 0.6)


## Tall near-lens cards along both sides of the road: whichever stretch the camera follows, some stand
## between it and the traveller's band and fall into the near blur (overlap, depth).
func _foreground() -> void:
	var line := ground.path_line()
	for i in range(6, line.size() - 6, 9):
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
		var side := -1.0 if k % 2 == 0 else 1.0
		var q := _start + to_cam * r2.randf_range(2.4, 3.2) + right * side * r2.randf_range(1.5, 2.4)
		_try(pools[r2.randi() % pools.size()], q, 0.2, 0.95, 1.15)
	rng = saved


func _meadow_fill() -> void:
	var pools := ["flower", "grass", "bush", "flower", "mushroom", "grass", "rock", "sapling", "flower"]
	for k in 1100:
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
	for k in 1800:
		var c := Vector2(rng.randf_range(-12.5, 12.5), rng.randf_range(-8.0, 9.0))
		if c.distance_to(_start) < HERO_CLEAR * 0.7:
			continue
		_try("grass" if rng.randf() < 0.65 else "flower", c, 0.05, 0.6, 0.9, 0.0, 0.7)


# ------------------------------------------------------------------ PE r2: engineered clusters (run AFTER the r4 layout, on its own RNG state)

const HAY_IDS := ["meadow_field_05", "meadow_field_06", "meadow_field_07", "field_hay_bale_round", "field_hay_bale_square",
	"field_hay_bales_stack", "field_haystack", "field_wheat_stook", "autumn_20"]
const WOOD_IDS := ["village_props_17", "forest_conifer_14", "stream_water_28", "meadow_field_23", "meadow_field_22"]
const STONE_IDS := ["small_decor_17", "small_decor_30"]


## Step-fold and box-pop platforms on the meadow, each dressed as a little scene (parallel-fold mechanisms).
func _folded_platforms() -> void:
	var spots := [Vector2(2.6, 4.4), Vector2(-3.6, 0.0), Vector2(4.4, -1.4), Vector2(-6.8, 2.2), Vector2(7.6, 3.4), Vector2(-1.2, 6.6)]
	var made := 0
	for c: Vector2 in spots:
		var cc := c + Vector2(rng.randf_range(-0.3, 0.3), rng.randf_range(-0.3, 0.3))
		if made >= 4 or cc.distance_to(_start) < HERO_CLEAR + 0.9 or _blocks_view(cc, 0.6):
			continue
		if ground.path_distance(cc) < 0.75 or ground.stream_distance(cc) < 0.7 or not _free_big(cc, 1.2):
			continue
		_clear(cc, 0.75)
		var yaw := _cam_yaw + rng.randf_range(-0.45, 0.45)
		var size := Vector2(rng.randf_range(0.9, 1.2), rng.randf_range(0.55, 0.75))
		var steps := 2 if made % 2 == 0 else 1
		var top := Color("8fa265") if steps == 2 else Color("9a8a5c")
		ground.add_step_fold(cc, yaw, size, 0.07 * steps, steps, top, Color("6d7f4c") if steps == 2 else Color("8a6e4a"))
		contact.add(Vector3(cc.x, ground.surface_y(cc + Vector2(0, 0.6).rotated(-yaw)) - 0.001, cc.y), yaw, size.x * 0.9, 0.12, 0.8)
		_reserve(cc, 0.9)
		made += 1
		var right := Vector2(1, 0).rotated(-yaw)
		var back := Vector2(0, -1).rotated(-yaw)
		# dress the top: a hay group or a fence + flowers on the upper step, flowers along the lower tread
		var top_c := cc + back * size.y * (0.25 if steps == 2 else 0.0)
		if made % 2 == 1:
			for k in 3:
				_place_on([["bush"], ["flower"], ["sapling"]][k], top_c + right * (k - 1) * size.x * 0.28, 0.8, yaw)
		else:
			var fid := lib.pick("fence")
			var fe := lib.get_card(fid)
			for k in 2:
				var fh: float = float(fe["h"]) * 0.95
				_place(fe, fh, top_c + back * 0.12 + right * (k - 0.5) * fh * float(fe["aspect"]) * 0.92, yaw, false)
			lib.mark(fid)
		for k in 5:
			_place_on(["flower"], cc + right * (float(k) / 4.0 - 0.5) * size.x * 0.8 + back * (-size.y * 0.32 if steps == 2 else -0.1), 0.6, yaw)


## PE r2: clear the uniform lawn tufts (cards < 0.26 tall) from a cluster's footprint, so a built group
## replaces them instead of being sprinkled over them.
func _clear(c: Vector2, r: float) -> void:
	statics.clear_area(c, r, 0.26)
	contact.clear_area(c, r, 0.3)
	for i in range(_small_hinged.size() - 1, -1, -1):
		var e: Array = _small_hinged[i]
		if (e[0] as Vector2).distance_to(c) < r:
			hinges.erase(e[2])
			sway.remove(e[1])
			(e[1] as Node3D).queue_free()
			_small_hinged.remove_at(i)


## Place one card (pool or id list) exactly at q, no spacing test (dressing on a platform / bed).
func _place_on(pool_or_ids: Array, q: Vector2, s: float, yaw: float) -> void:
	var ids: Array = []
	for x in pool_or_ids:
		if lib.has(x):
			ids.append(x)
		else:
			ids.append_array(lib.pools.get(x, []))
	if ids.is_empty():
		return
	var id := lib.pick(ids)
	var it := lib.get_card(id)
	var pool: String = it["pool"]
	var h: float = float(it["h"]) * s * rng.randf_range(0.9, 1.1) * float(POOL_SCALE.get(pool, 1.0))
	_place(it, h, q, yaw + rng.randf_range(-0.2, 0.2), false)
	_reserve(q, h * float(it["aspect"]) * 0.3)
	lib.mark(id)


## Open felt gets purposeful clusters (fence runs, hay, stone piles, raised flower beds, woodpiles)
## instead of uniform tufts: each one is a small built thing, with negative space around it.
func _purposeful_clusters() -> void:
	# PE r3: hay, woodpiles and raised beds dropped (read as CG cylinders / brown slabs); layered flower patches instead
	var kinds := ["fence", "patch", "stones", "patch", "fence", "patch", "stones"]
	var made := 0
	for k in 1600:
		if made >= 40:
			break
		var c := Vector2(rng.randf_range(-11.5, 11.5), rng.randf_range(-6.8, 8.6))
		if k % 4 != 0:
			# PE r2: three of four sites inside this view's frame, mostly the near/mid lawn the camera sees
			var fwd := (_start - _cam_ground).normalized()
			# (fov 20: the frame is only ~±1.6 wide at the traveller, ~±1.1 at the bottom edge)
			var f := rng.randf_range(-2.6, 4.5)
			c = _start + fwd * f + Vector2(-fwd.y, fwd.x) * rng.randf_range(-1.0, 1.0) * (1.55 + f * 0.2)
		if _fill_mask.get_noise_2d(c.x, c.y) > 0.5 or c.distance_to(_start) < HERO_CLEAR + 0.3:
			_rej[0] += 1
			continue
		if ground.path_distance(c) < 0.55 or ground.stream_distance(c) < 0.45:
			_rej[1] += 1
			continue
		# PE r2: the r4 cover pass already holds the lawn with tiny tufts; clusters may sit among tufts
		# (only cards >= 0.12 reserve count), beds need truly open felt (they would swallow a tuft).
		var kind: String = kinds[made % kinds.size()]
		if not _free_big(c, 0.6 if kind == "bed" else 0.45):
			_rej[2] += 1
			continue
		if _blocks_view(c, 0.4):
			_rej[3] += 1
			continue
		_clear(c, 0.42 if kind == "bed" else 0.3)
		var yaw := _cam_yaw + rng.randf_range(-0.5, 0.5)
		var right := Vector2(1, 0).rotated(-yaw)
		var back := Vector2(0, -1).rotated(-yaw)
		match kind:
			"fence":
				_fence_run(c)
			"hay":
				var n := rng.randi_range(3, 4)
				for j in n:
					_place_on(HAY_IDS, c + right * (j - (n - 1) * 0.5) * 0.17 + back * (0.07 if j % 2 == 0 else -0.05), 0.9, yaw)
				for j in 3:
					_place_on(["grass"], c + right * rng.randf_range(-0.35, 0.35) - back * 0.16, 0.65, yaw)
			"stones":
				var n := rng.randi_range(3, 4)
				for j in n:
					_place_on(["rock"], c + right * (j - (n - 1) * 0.5) * 0.13 + back * rng.randf_range(-0.06, 0.08), 0.7 if j != 1 else 0.95, yaw)
				_place_on(["small_decor_17", "small_decor_30"], c - back * 0.12 + right * 0.12, 1.0, yaw)
				_place_on(["flower"], c - back * 0.14 - right * 0.14, 0.65, yaw)
			"bed":
				_flower_bed(c)
			"patch":
				# layered group: taller back row, flowers in the middle, low tufts in front (overlap = depth)
				for j in 2:
					_place_on(["bush", "sapling"], c + right * (j - 0.5) * 0.24 + back * 0.13, 0.8, yaw)
				for j in 3:
					_place_on(["flower"], c + right * (j - 1) * 0.16 + back * rng.randf_range(-0.02, 0.03), 0.8, yaw)
				for j in 3:
					_place_on(["grass", "flower"], c + right * (j - 1) * 0.18 - back * 0.13, 0.62, yaw)
			"wood":
				for j in 3:
					_place_on(WOOD_IDS, c + right * (j - 1) * 0.16 + back * (0.05 if j == 1 else -0.03), 0.95, yaw)
				for j in 2:
					_place_on(["mushroom"], c - back * 0.13 + right * (j - 0.5) * 0.24, 0.8, yaw)
		_reserve(c, 0.55)
		if OS.get_environment("PE_DEBUG") != "":
			print("PE cl ", kind, " ", c, " f=", snappedf((c - _start).dot((_start - _cam_ground).normalized()), 0.1))
		made += 1
	if OS.get_environment("PE_DEBUG") != "":
		print("PE clusters=", made, " rejected [mask/hero, road/stream, occupied, lens]=", _rej)


func _fence_run(c: Vector2) -> void:
	var fid := lib.pick("fence")
	var e := lib.get_card(fid)
	if e.is_empty():
		return
	var h: float = float(e["h"]) * rng.randf_range(0.95, 1.05)
	var w: float = h * float(e["aspect"])
	var yaw := _cam_yaw + rng.randf_range(-0.55, 0.55)  # runs across the view, prints toward the lens
	var d := Vector2(cos(yaw), -sin(yaw))
	var n := rng.randi_range(3, 6)
	var p0 := c - d * w * 0.92 * (n - 1) * 0.5
	var placed := 0
	for i in n:
		var q := p0 + d * w * 0.92 * i
		if _blocks_view(q, h) or not _free_big(q, w * 0.4) or ground.path_distance(q) < 0.35 or ground.stream_distance(q) < 0.4:
			break
		_reserve(q, w * 0.4)
		_clear(q, w * 0.55)
		_place(e, h, q, yaw + rng.randf_range(-0.04, 0.04), false, w)
		placed += 1
	if placed == 0:
		return
	lib.mark(fid)
	var nn := Vector2(-d.y, d.x)
	for i in placed + 1:
		var t := (float(i) - placed * 0.5) * w * 0.92
		_place_on(["flower"] if i % 2 == 0 else ["grass"], p0 + d * t + nn * rng.randf_range(0.07, 0.12), 0.6, yaw)


## Raised flower bed: a low box-pop (soil-printed top, folded green faces) planted in rows.
func _flower_bed(c: Vector2) -> void:
	var yaw := _cam_yaw + rng.randf_range(-0.4, 0.4)
	var size := Vector2(rng.randf_range(0.55, 0.85), rng.randf_range(0.28, 0.38))
	ground.add_box_pop(c, yaw, size, rng.randf_range(0.045, 0.065), Color("7a5a3e"), Color("667a48"), "Bed")
	contact.add(Vector3(c.x, ground.surface_y(c + Vector2(0, size.y).rotated(-yaw)) , c.y), yaw, size.x, 0.1, 0.7)
	_reserve(c, size.x * 0.7)
	var right := Vector2(1, 0).rotated(-yaw)
	var back := Vector2(0, -1).rotated(-yaw)
	var rows := [lib.pick("flower"), lib.pick("flower")]
	for r in 2:
		var it := lib.get_card(rows[r])
		var n := 4 + r
		for i in n:
			var q := c + right * (float(i) / float(n - 1) - 0.5) * size.x * 0.82 + back * (r * 0.4 - 0.2) * size.y + Vector2(rng.randf_range(-0.01, 0.01), 0)
			var h: float = float(it["h"]) * 0.6 * rng.randf_range(0.9, 1.1)
			_place(it, h, q, yaw + rng.randf_range(-0.15, 0.15), false)
		lib.mark(rows[r])


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
	rig.dof_near_margin = 0.9
	rig.dof_far_margin = 2.0
	rig.dof_near_transition = 1.1
	rig.dof_far_transition = 3.2
	rig.dof_amount = 0.07
	rig.tilt_blur = 0.58  # r4: 0.66 -> 0.58 (v0/v1/v5 tiltshift above 3.5)
	rig.tilt_focus_y = 0.55
	rig.tilt_band_half = 0.16
	rig.tilt_band_soft = 0.36
	rig.key_elevation_deg = 34.0
	rig.key_yaw_deg = -60.0
	rig.key_color = Color("ffd9ae")
	rig.key_energy = 2.05
	rig.shadow_opacity = 0.8
	rig.shadow_softness = 1.4
	rig.ambient_energy = 0.46
	rig.exposure = 0.82
	rig.vignette = 0.14
	rig.post_saturation = 0.9
	rig.haze_color = Color("dcc49a")  # r3: warmer haze (was cfc3a0, read grey)
	rig.haze_begin = 1.0
	rig.haze_length = 6.0
	rig.haze_amount = 0.62
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
	for hz in _houses:
		var p: Vector3 = hz[0]
		var smoke := ChimneySmoke.new()
		smoke.position = p + Vector3(float(hz[3]) * 0.22, float(hz[1]) * 0.92, -0.02)
		add_child(smoke)
		if _houses.find(hz) >= 3:
			break
