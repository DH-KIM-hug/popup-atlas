extends Node3D
## Motion bench (component C_motion, round 3; r2 header below)
## r3: denser, smaller set dressing (adds shared atlas small props), stronger tilt-shift, slow
## dolly+yaw camera drift, D's paper puppet strolling, cut-paper butterflies and leaves
## (PaperAmbient), and rigid sway on reeds/grass/flowers once they stand.
## Motion bench (component C_motion, round 2): ~150 cut-paper cards from the shared card kit
## (art/cards/catalog.json) pop up in a staggered wave that runs outward from the traveller, on
## component B's layered ground (GroundLayers) under B's light/DOF rig (LookRig). The camera
## drifts slowly (a few degrees) like a hand-held look at a real diorama.
## Every piece folds BACK (print facing up when flat), so a folded page shows the printed art
## lying on the page instead of plain card backs.
## Options (exports, or JSON under "bench" in --agent-args, e.g. {"bench": {"mode": "fold"}}):
##   mode: "rise" (start flat, pop wave) | "fold" (start up, fold wave) | "loop" (rise/fold forever)
##        | "up" (everything standing, no motion)
##   fixed_dt: seconds per frame for deterministic captures (0 = real time)
##   start: seconds before the wave starts
##   drift: camera drift amplitude (deg)

@export var mode := "rise"
@export var fixed_dt := 1.0 / 60.0
@export var start := 0.15
@export var seed_value := 7
@export var card_count := 360
@export var drift := 4.0
@export var tilt_blur := 1.4
@export var tilt_band := 0.1

const CATALOG := "res://art/cards/catalog.json"
const ATLAS := "res://art/atlas/catalog.json"
## Atlas categories folded into the bench pools (small set dressing).
const ATLAS_CATS := {"flower": "flower", "mushroom": "mushroom", "rock": "rock", "prop": "prop",
	"animal": "critter", "crop": "crop", "sign": "prop", "lantern": "prop"}
const TRAV := Vector2(0.15, 0.9)  ## traveller on the path (page XZ)

var rig: LookRig
var ground: GroundLayers
var hinges: Array[PopHinge] = []
var audio: PaperAudio
var wave := PopWave.new()
var traveller: Node3D
var puppet: PaperPuppet
var ambient: PaperAmbient
var _sway: Array = []  ## [card node, phase, amp, hinge]
var by_cat := {}  ## category -> Array[Dictionary]
var by_id := {}
var _tex := {}
var _placed: Array = []  ## [Vector2, radius]
var _t := 0.0
var _clock := 0.0
var _phase_end := 0.0
var _up := false


func _ready() -> void:
	_read_args()
	seed(seed_value)
	wave.speed = 3.2
	wave.jitter = 0.08
	wave.back_lag = 0.05
	wave.fold_speed = 4.0
	PopHinge.fixed_dt = fixed_dt
	_load_catalog()
	_build_ground()
	_build_props()
	_build_rig()
	audio = PaperAudio.new()
	audio.listener_point = Vector3(TRAV.x, 0, TRAV.y + 1.0)
	add_child(audio)
	audio.watch(self)
	var origin := Vector3(TRAV.x, 0, TRAV.y)
	if mode == "fold":
		PopWave.snap_all(hinges, true)
		_phase_end = wave.fold(hinges, origin, start) + 1.0
		_up = false
	elif mode == "up":
		PopWave.snap_all(hinges, true)
		_up = true
	else:
		PopWave.snap_all(hinges, false)
		_phase_end = wave.pop(hinges, origin, start) + 1.2
		_up = true
	print("MOTION_BENCH hinges=", hinges.size(), " mode=", mode)


func _exit_tree() -> void:
	PopHinge.fixed_dt = 0.0


func _read_args() -> void:
	var a := OS.get_cmdline_user_args()
	var i := a.find("--agent-args")
	if i < 0 or i + 1 >= a.size():
		return
	var j = JSON.parse_string(a[i + 1])
	if not (j is Dictionary) or not j.has("bench"):
		return
	var b: Dictionary = j["bench"]
	mode = str(b.get("mode", mode))
	fixed_dt = float(b.get("fixed_dt", fixed_dt))
	start = float(b.get("start", start))
	card_count = int(b.get("cards", card_count))
	drift = float(b.get("drift", drift))
	tilt_blur = float(b.get("tilt_blur", tilt_blur))
	tilt_band = float(b.get("tilt_band", tilt_band))


func _process(dt: float) -> void:
	var step := fixed_dt if fixed_dt > 0.0 else dt
	_clock += step
	if rig:
		# Slow drift: a few degrees of orbit and a breath of elevation, like leaning over a diorama.
		# r3: continuous dolly + yaw (a few degrees over ~8 s) so parallax reads between pops.
		rig.yaw_deg = -10.0 + drift * sin(_clock * TAU / 8.0)
		rig.elevation_deg = 32.0 + drift * 0.3 * sin(_clock * TAU / 11.0 + 1.1)
		rig.distance = 6.0 - 0.35 * sin(_clock * TAU / 9.0 + 0.4)
	_ambient_step(step)
	if mode != "loop":
		return
	_t += step
	if _t < _phase_end:
		return
	_t = 0.0
	var origin := Vector3(TRAV.x, 0, TRAV.y)
	if _up:
		_phase_end = wave.fold(hinges, origin, 0.0) + 1.0
	else:
		_phase_end = wave.pop(hinges, origin, 0.0) + 1.2
	_up = not _up


## Traveller stroll + reed sway (deterministic with fixed_dt).
func _ambient_step(dt: float) -> void:
	if traveller:
		# Ping-pong along the path between TRAV and a point 0.45 up the path, 0.11 u/s with eased turns.
		var a := Vector3(TRAV.x, 0, TRAV.y)
		var b := Vector3(0.32, 0, 0.35)
		var u := 0.5 - 0.5 * cos(_clock * 0.11 / a.distance_to(b) * PI)
		var p := a.lerp(b, u)
		p.y = ground.surface_y(Vector2(p.x, p.z))
		traveller.position = p
	for e in _sway:
		var hg: PopHinge = e[3]
		var card: Node3D = e[0]
		var k := clampf(hg.openness(), 0.0, 1.0)
		card.rotation.z = e[2] * k * k * sin(_clock * TAU * e[4] + e[1])


func _load_catalog() -> void:
	var j = JSON.parse_string(FileAccess.get_file_as_string(CATALOG))
	for it: Dictionary in j:
		var cat: String = it["category"]
		if not by_cat.has(cat):
			by_cat[cat] = []
		by_cat[cat].append(it)
		by_id[it["id"]] = it
	var ja = JSON.parse_string(FileAccess.get_file_as_string(ATLAS))
	for a: Dictionary in ja:
		var cat: String = ATLAS_CATS.get(a["category"], "")
		if cat == "" or float(a["height_units"]) > 0.3 or a.get("season", "") == "winter":
			continue
		var px: Array = a["px"]
		var it := {"id": a["id"], "path": "res://" + a["path"], "category": cat,
			"height_units": float(a["height_units"]) * 1.15, "cross_slot": false,
			"aspect": float(px[0]) / float(px[1])}
		if not by_cat.has(cat):
			by_cat[cat] = []
		by_cat[cat].append(it)
		by_id[it["id"]] = it


func _build_ground() -> void:
	ground = GroundLayers.new()
	ground.name = "Ground"
	ground.seed_value = seed_value
	ground.page_size = Vector2(14.0, 10.0)
	ground.path_width = 0.3
	ground.cover_patches = 24
	# r3: base green desaturated ~15% and shifted to yellow-sage to sit inside the warm grade.
	ground.felt_color = Color("85995a")
	ground.felt_mottle = Color("74874d")
	ground.path_points = PackedVector2Array([
		Vector2(1.4, 5.0), Vector2(0.6, 2.6), Vector2(0.1, 0.9), Vector2(0.7, -0.8),
		Vector2(0.2, -2.4), Vector2(-1.0, -3.8), Vector2(-1.8, -5.0)])
	ground.stream_points = PackedVector2Array([
		Vector2(-7.5, 1.6), Vector2(-4.2, 0.9), Vector2(-2.4, -0.6), Vector2(-0.9, -1.5),
		Vector2(1.8, -1.9), Vector2(4.0, -3.0), Vector2(7.5, -3.6)])
	ground.stream_width = 0.55
	add_child(ground)


func _build_rig() -> void:
	rig = LookRig.new()
	rig.name = "LookRig"
	rig.elevation_deg = 32.0
	rig.yaw_deg = -10.0
	rig.distance = 6.0
	rig.fov = 22.0
	rig.follow_smooth = 0.0
	# Narrow in-focus band on the traveller, blur both ways (critic r1: "far field as legible as subject").
	rig.dof_near_margin = 1.2
	rig.dof_far_margin = 1.4
	rig.dof_near_transition = 1.2
	rig.dof_far_transition = 2.0
	rig.dof_amount = 0.13
	rig.env_saturation = 0.9
	# r3 (critic r2: "single biggest miniature cue"): narrow band ~18% of the frame, heavy both ways.
	rig.tilt_blur = tilt_blur
	rig.tilt_band_half = tilt_band
	rig.tilt_band_soft = 0.2
	rig.tilt_top_bias = 0.75
	rig.tilt_focus_y = 0.52
	var focus := Node3D.new()
	focus.name = "Focus"
	add_child(focus)
	focus.position = Vector3(TRAV.x, 0, TRAV.y - 0.3)
	rig.focus_target = focus
	add_child(rig)
	# The traveller: D's paper puppet (r3, critic r2: "low-res sprite pasted on"), ~1.4x scale,
	# strolling slowly up and down a short stretch of the path.
	puppet = PaperPuppet.new()
	puppet.height = 0.45
	puppet.camera = rig.camera
	traveller = Node3D.new()
	traveller.name = "Traveller"
	add_child(traveller)
	traveller.position = Vector3(TRAV.x, ground.surface_y(TRAV), TRAV.y)
	traveller.add_child(puppet)
	ambient = PaperAmbient.new()
	ambient.area = Rect2(-2.2, -1.6, 4.6, 3.6)
	add_child(ambient)


## Free spot test against path, stream and placed footprints.
func _free(p: Vector2, r: float, path_clear := 0.06) -> bool:
	if not ground.on_page(p, 0.25):
		return false
	if ground.path_distance(p) < path_clear or ground.stream_distance(p) < 0.06:
		return false
	for q in _placed:
		if (q[0] as Vector2).distance_to(p) < r + float(q[1]) * 0.45:
			return false
	return true


func _pick(cat: String) -> Dictionary:
	var arr: Array = by_cat[cat]
	return arr[randi() % arr.size()]


## Drops `n` cards of weighted categories around centre c (radius rx, rz).
func _cluster(cats: Dictionary, c: Vector2, rx: float, rz: float, n: int, scale := 1.0) -> void:
	var total := 0.0
	for k in cats:
		total += float(cats[k])
	for i in n:
		if hinges.size() >= card_count - 1:
			return
		var r := randf() * total
		var cat := ""
		for k in cats:
			r -= float(cats[k])
			if r <= 0.0:
				cat = k
				break
		var it := _pick(cat)
		var h: float = float(it["height_units"]) * scale * randf_range(0.88, 1.12)
		var half: float = h * float(it["aspect"]) * 0.5
		for t in 14:
			var p := c + Vector2(randf_range(-rx, rx), randf_range(-rz, rz))
			if _free(p, maxf(half * 0.55, 0.06)):
				_placed.append([p, half * 0.55])
				_add(it, h, p, randf_range(-0.22, 0.22))
				break


func _build_props() -> void:
	# The traveller is D's PaperPuppet (added in _build_rig, it needs the camera); keep his spot
	# and a stretch of path clear. Small set dressing right beside him (critic r2).
	_placed.append([TRAV, 0.1])
	_cluster({"flower": 2.0, "mushroom": 1.0, "critter": 0.6, "rock": 0.6}, TRAV + Vector2(-0.32, 0.05), 0.12, 0.2, 6, 0.75)
	_cluster({"flower": 2.0, "prop": 0.8, "grass": 1.0}, TRAV + Vector2(0.38, 0.1), 0.14, 0.22, 6, 0.75)
	# Landmark: a cottage, its well, fence and lantern, back right of the traveller.
	_add(by_id["house_cottage_terracotta"], 0.82, Vector2(1.9, -0.9), -0.15)
	_placed.append([Vector2(1.9, -0.9), 0.5])
	_add(by_id["village_well"], 0.36, Vector2(1.15, -0.35), 0.1)
	_placed.append([Vector2(1.15, -0.35), 0.16])
	_add(by_id["village_lantern_post"], 0.46, Vector2(0.62, 0.15), 0.0)
	_placed.append([Vector2(0.62, 0.15), 0.1])
	_add(by_id["village_signpost"], 0.38, Vector2(-0.38, 1.45), 0.2)
	_placed.append([Vector2(-0.38, 1.45), 0.1])
	for k in 3:
		var p := Vector2(2.0 + k * 0.42, -0.25 + k * 0.05)
		_add(by_id["fence_picket_cream"], 0.16, p, -0.1)
		_placed.append([p, 0.18])
	# Accent groves: warm autumn trees against green, cross-slotted where the kit allows.
	_cluster({"tree": 3.0, "conifer": 1.2}, Vector2(-1.5, -1.8), 1.1, 0.4, 8)
	_cluster({"tree": 2.0, "conifer": 2.0}, Vector2(2.6, -2.0), 0.9, 0.45, 8)
	_cluster({"tree": 2.0, "conifer": 1.0}, Vector2(0.4, -2.4), 0.7, 0.25, 4)
	_cluster({"tree": 3.0}, Vector2(-2.5, 0.4), 0.5, 0.5, 5, 0.8)
	_cluster({"tree": 1.0, "bush": 2.0}, Vector2(2.9, 1.6), 0.5, 0.6, 5, 0.75)
	# Hills along the back.
	_add(by_id["hill_rolling_green"], 1.0, Vector2(-1.6, -3.0), 0.05)
	_add(by_id["hill_patchwork_gold"], 0.95, Vector2(1.7, -3.1), -0.1)
	_add(by_id["hill_far_blue"], 1.15, Vector2(0.0, -3.5), 0.0)
	# Stream banks: cattails, reeds, a goose; sheep on the near meadow.
	for i in 10:
		var x := randf_range(-3.2, 3.2)
		var best := Vector2(x, 0)
		for t in 24:
			var q := Vector2(x, randf_range(-3.5, 1.8))
			if absf(ground.stream_distance(q) - 0.12) < absf(ground.stream_distance(best) - 0.12):
				best = q
		var it := _pick("water")
		var h: float = float(it["height_units"]) * randf_range(0.8, 1.1)
		if _free(best, 0.08):
			_placed.append([best, 0.09])
			_add(it, h, best, randf_range(-0.25, 0.25))
	_add(by_id["animal_goose"], 0.15, Vector2(-1.2, -0.85), 0.3)
	_cluster({"animal": 1.0}, Vector2(-1.4, 1.8), 0.6, 0.35, 3)
	# Clustered undergrowth (r3: about twice the pieces at ~65% of r2 size, set dressing in clumps
	# so no bare felt patch is bigger than a few percent of the frame).
	var small := 0.68
	_cluster({"flower": 3.0, "grass": 1.0, "mushroom": 0.6}, Vector2(-0.55, 0.6), 0.35, 0.5, 14, small)
	_cluster({"flower": 2.0, "bush": 1.0, "critter": 0.5}, Vector2(0.95, 1.4), 0.45, 0.45, 14, small)
	_cluster({"bush": 2.0, "mushroom": 1.0, "rock": 1.0}, Vector2(-1.2, -0.2), 0.5, 0.35, 12, small)
	_cluster({"crop": 2.0, "field": 1.0, "prop": 0.6}, Vector2(1.7, 0.7), 0.6, 0.35, 10, 0.8)
	_cluster({"mushroom": 1.0, "rock": 1.0, "grass": 1.0, "critter": 0.4}, Vector2(-1.9, -1.0), 0.6, 0.4, 10, small)
	_cluster({"bush": 1.0, "grass": 1.0, "flower": 1.0, "prop": 0.4}, Vector2(0.4, -1.5), 0.6, 0.4, 12, small)
	_cluster({"flower": 2.0, "grass": 1.0, "bush": 1.2, "mushroom": 0.5}, Vector2(-0.9, 2.6), 0.9, 0.6, 14, 0.85)
	_cluster({"flower": 2.0, "grass": 1.0, "bush": 1.2, "rock": 0.5}, Vector2(1.6, 2.7), 1.0, 0.6, 14, 0.85)
	_cluster({"bush": 1.0, "tree": 0.6}, Vector2(-2.3, 3.2), 0.5, 0.4, 3, 0.8)
	_cluster({"prop": 1.0, "critter": 1.0, "flower": 1.0}, Vector2(1.3, -0.1), 0.3, 0.25, 7, small)
	_cluster({"critter": 1.0, "rock": 1.0, "grass": 1.0}, Vector2(-0.9, -1.1), 0.5, 0.25, 7, small)
	# Near foreground left/right of the path (was bare felt in r3 first pass).
	_cluster({"flower": 2.0, "bush": 1.0, "mushroom": 0.6, "rock": 0.5}, Vector2(-1.0, 1.9), 0.55, 0.35, 12, 0.8)
	_cluster({"flower": 2.0, "bush": 1.0, "crop": 0.5, "critter": 0.4}, Vector2(1.3, 2.0), 0.55, 0.35, 12, 0.8)
	# Fill the rest of the view, densest near the traveller.
	var tries := 0
	while hinges.size() < card_count and tries < 6000:
		tries += 1
		var c := Vector2(randf_range(-3.0, 3.2), randf_range(-2.4, 3.0))
		if Vector2((c.x - TRAV.x) / 3.0, (c.y - 0.8) / 2.6).length() > 1.0:
			continue
		var cats := {"flower": 2.5, "grass": 2.0, "bush": 1.2, "mushroom": 0.8, "rock": 0.8, "critter": 0.4,
			"prop": 0.3, "tree": 0.4}
		_cluster(cats, c, 0.2, 0.14, 4, small)
	print("MOTION_BENCH placed=", hinges.size(), " tries=", tries)


func _add(it: Dictionary, h: float, p: Vector2, yaw: float) -> PopHinge:
	var path: String = it["path"]
	if not _tex.has(path):
		_tex[path] = load(path)
	var pos := Vector3(p.x, ground.surface_y(p), p.y)
	if bool(it.get("cross_slot", false)):
		return _add_cross(_tex[path], h, pos, yaw)
	var hg := _add_tex(_tex[path], h, pos, yaw, 0.012, 1)
	var cat: String = it["category"]
	if cat in ["grass", "water", "flower", "field", "crop"]:
		# Rigid sway about the card's base (the card never bends), only once it stands.
		_sway.append([hg.get_child(0), randf() * TAU, deg_to_rad(randf_range(1.2, 2.4)), hg, randf_range(0.45, 0.7)])
	return hg


## Layer flat pieces so the nearer piece lies on top (no z-fighting between overlapping flats):
## a tiny lift that grows toward the camera.
func _lift(pos: Vector3) -> Vector3:
	return pos + Vector3(0, 0.0015 + clampf((pos.z + 6.0) * 0.0016, 0.0, 0.022), 0)


func _hinge(h: float, pos: Vector3, yaw: float, fold: int) -> PopHinge:
	var base := Node3D.new()
	base.position = _lift(pos)
	base.rotation.y = yaw
	add_child(base)
	var hinge := PopHinge.new()
	hinge.fold = fold
	hinge.weight = clampf(h / 0.4, 0.4, 2.5)
	hinge.set_meta("card_h", h)
	base.add_child(hinge)
	hinges.append(hinge)
	return hinge


func _add_tex(tex: Texture2D, h: float, pos: Vector3, yaw: float, thick := 0.012, fold := 1) -> PopHinge:
	var hinge := _hinge(h, pos, yaw, fold)
	hinge.set_meta("half_w", h * float(tex.get_width()) / float(tex.get_height()) * 0.5)
	var card := PaperCard.new()
	card.texture = tex
	card.height = h
	card.thickness = thick
	hinge.add_child(card)
	return hinge


func _add_cross(tex: Texture2D, h: float, pos: Vector3, yaw: float) -> PopHinge:
	var hinge := _hinge(h, pos, yaw, 1)
	hinge.weight = clampf(h / 0.4 * 1.15, 0.4, 2.5)  # two cards: heavier
	hinge.set_meta("half_w", h * float(tex.get_width()) / float(tex.get_height()) * 0.5)
	var cc := CrossCard.new()
	cc.texture_a = tex
	cc.texture_b = tex
	cc.height = h
	cc.height_b = h * 0.94
	hinge.add_child(cc)
	return hinge
