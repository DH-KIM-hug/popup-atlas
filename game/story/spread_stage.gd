class_name SpreadStage
extends Node3D
## One pop-up spread of a story (component E): the meadow world template (scenes/world/meadow.tscn, MeadowWorld,
## built from seed + view, its look untouched) dressed from the tale's script.json:
##  - cast (`cast` in script.json, by kind):
##      walker  — the template's Walker on the road, its puppet swapped for a CastPuppet skin (sun_wind traveller),
##      hanger  — SkyHanger cards on strings in the sky band of the story shot (sun, wind), on paper backing discs,
##      actor   — StoryActor: a CastPuppet that walks freely in any direction, figure picked from the travel
##                direction (front / back / side, flipped), placed at named spots (three_pigs pigs, wolf, mother),
##      prop    — a cast print the tale's handler makes cards of (hat, coat);
##  - set pieces (`spread.set`): atlas catalog cards on hinges at named spots, houses in fold-up bands (SetPiece);
##  - light (`spread.light`: "dusk"), camera shots on the template rig (wide = the template view, story, close, and
##    any tale `shots`), spots (`spread.spots`: name -> [right, toward camera] from the page anchor);
##  - tale effects in the tale's handler (`handler`: game/stories/<tale>/fx.gd, a TaleHandler).
## Cast prints come from CastSkins / the cast catalog (cast id + variant), so new cast art drops in by id.

signal fx_done(name: String)

const MEADOW := preload("res://scenes/world/meadow.tscn")
const CAST_PUPPET_PATH := "res://art/cast/rig/cast_puppet.gd"
const ATLAS_CATALOG := "res://art/atlas/catalog.json"
## Shots: [distance, elevation deg, focus height, fov]. "wide" uses the template view's own values.
const SHOTS := {
	"story": [3.3, 15.0, 0.34, 20.0],  ## feet clear of the caption strip
	"close": [2.85, 15.0, 0.34, 20.0],  ## same focus as "story": the sky cast stays in frame
}
## Story scale on catalog height_units for set pieces (the cast is scaled 1.3 for iPad reading, see TRAV_H).
const SET_SCALE := 1.25
const ACTOR_SCALE := 1.3

var tale: Dictionary = {}  ## the script (cast, handler, shots)
var beat: Dictionary = {}  ## the beat this spread was built for (spread fields)
var handler: TaleHandler
var world: MeadowWorld
var hangers: Dictionary = {}  ## role -> SkyHanger
var actors: Dictionary = {}  ## role -> StoryActor
var sets: Dictionary = {}  ## name -> SetPiece
var spots: Dictionary = {}  ## name -> Vector3 (ground point)
var has_walker := false
var walker_role := ""
var trav_h := 0.47
var extra_hinges: Array[PopHinge] = []
var seed_value := 1
var view := 0
var shot := "wide"
var follow_sky := true
var light := ""
var build_ctx := {}  ## build / huff verbs: {house, walker, tap, taps, result} for the tale fx

var _t := 0.0
var _wide: Array = []
var _cam := [0.0, 0.0, 0.0, 20.0]  ## current shot target
var _shots: Dictionary = {}
var _sky: Array = []  ## per hanger: {role, anchor, h, rel, drop, v, target, delay, yaw, yaw_t, cfg}
var _origin := Vector3.ZERO
var _cam_anchor: Node3D
var _focus_goal := Vector3.ZERO
var _anchor := Vector3.ZERO  ## page anchor: the template start point (spots are relative to it)
var _cam_basis := [Vector2.ZERO, Vector2.ZERO]  ## ground: right, toward camera (the template view yaw)
var _counter: Label3D
var _counter_s := 0.0
var _counter_v := 0.0
var _light_k := 0.0
var _light_t := 0.0
var _rig0 := {}
## walker (traveller) state, shared with the tale handler
var trav_s := 1.0
var _trav_v := 0.0
var trav_target := 1.0
var trav_delay := -1.0
var hop := 0.0
var hop_v := 0.0
var sink := 0.0
var sink_target := 0.0
var shiver := 0.0
var ground_dy := 0.0  ## off the road: ground height under him minus the walker's road height
var walk_goal := Vector3.ZERO  ## off-road goal (handler: the stream bank)
var pull := 0.0  ## hangers slide toward each other (0..1 of the gap)
var pull_t := 0.0
## Road stretch this spread's walking covers, offsets relative to the template start (route[0] is where he starts).
## Set before build(); sightlines are cleared along the whole stretch so the follow camera never looks through a card.
var route := Vector2.ZERO
## Stroll: he keeps walking along the road while a beat plays. `pause` stops him in place (startle, coat off).
var strolling_on := false
var stroll_speed := 0.0
var stroll_dir := 1.0
var pause := 0.0
var push := 0.0  ## shoved back a step
var _start_off := 0.0
## 2026-11-18 walk toward the reader (sun_wind): the walker card faces the camera, so every walking stretch runs down
## the road TOWARD the camera. The story camera stands ahead of him on the road looking back along it.
var road_cam := true
var _yaw0 := 0.0  ## rig yaw the sky layout was made at
var _yaw_t := 0.0
var _statics_hidden := 0


func _init() -> void:
	process_priority = 100  # after WindGusts, so our cast skin wins on the wind card


## Build the spread synchronously (the caller hides the hitch under a page turn).
func build(seed_v: int, view_i: int, with_audio: bool) -> void:
	await build_async(seed_v, view_i, with_audio, 0.0)


## perf: build over several frames, at most ~budget_ms of work per frame (0 = all at once, same result).
var perf_phases := {}
var build_frames := 0
var max_slice_ms := 0.0
var is_built := false
var _slicer: BuildSlicer


func slicer_tick() -> void:
	await _slicer.tick()


func build_async(seed_v: int, view_i: int, with_audio: bool, budget_ms: float) -> void:
	_slicer = BuildSlicer.new(budget_ms, get_tree())
	seed_value = seed_v
	view = view_i
	_shots = SHOTS.duplicate()
	for k in (tale.get("shots", {}) as Dictionary):
		_shots[k] = tale["shots"][k]
	var cast: Dictionary = tale.get("cast", {})
	for role in cast:
		if str((cast[role] as Dictionary).get("kind", "")) == "walker":
			has_walker = true
			walker_role = str(role)
			trav_h = float(cast[role].get("height", trav_h))
	if not has_walker:
		road_cam = false
	world = MEADOW.instantiate() as MeadowWorld
	world.seed_value = seed_v
	world.view = view_i
	world.fixed_step = false  # the runner owns the global fixed step
	world.pop_on_load = true
	world.walk = false
	world.with_audio = with_audio
	world.slicer = _slicer
	add_child(world)
	if not world.is_built:
		await world.built
	_slicer.phase("stage")
	PopWave.snap_all(world.hinges, false)  # cancel the template's own load wave; the page turn pops it
	var w := world.walker
	w.tap_enabled = false
	w.keys_enabled = false
	w.auto_walk = false
	w.target_offset = w.offset
	w.speed = 0.26
	_start_off = w.offset
	_anchor = w.global_position
	if route != Vector2.ZERO:
		var L := world.path.curve.get_baked_length()
		w.offset = clampf(w.offset + route.x, 0.0, L)
		w.target_offset = w.offset
		w.global_position = world.path.global_transform * world.path.curve.sample_baked(w.offset)
		world.focus.snap()
		stroll_dir = signf(route.y - route.x) if route.y != route.x else 1.0
	else:
		stroll_dir = _toward_cam_sign(w.offset)
	if road_cam:
		world.rig.yaw_deg = road_yaw(w.offset)
		_yaw_t = world.rig.yaw_deg
		world.rig.snap()
	_origin = w.global_position
	var yw := deg_to_rad(world.rig.yaw_deg)
	_cam_basis = [Vector2(cos(yw), -sin(yw)), Vector2(sin(yw), cos(yw))]
	await _slicer.tick()
	if has_walker:
		_swap_puppet(cast[walker_role])
	else:
		world.puppet.visible = false
		world.puppet.process_mode = Node.PROCESS_MODE_DISABLED
	await _slicer.tick()
	var rig := world.rig
	_wide = [rig.distance, rig.elevation_deg, rig.focus_height, rig.fov]
	_cam = _wide.duplicate()
	_build_spots()
	_build_hangers(cast)
	_build_actors(cast)
	await _slicer.tick()
	var hp := str(tale.get("handler", ""))
	if hp != "" and ResourceLoader.exists(hp):
		handler = (load(hp) as GDScript).new() as TaleHandler
	if handler:
		handler.name = "TaleFx"
		handler.stage = self
		add_child(handler)
		handler.setup()
	_layout_sky()
	await _slicer.tick()
	_slicer.phase("sightlines")
	await _clear_sightlines()
	_slicer.phase("set")
	await _build_set((beat.get("spread", {}) as Dictionary).get("set", []))
	if handler:
		_slicer.phase("tale")
		await _slicer.tick()
		await handler.build_async()
	await _slicer.tick()
	_slicer.phase("finish")
	_save_light()
	_set_light(str((beat.get("spread", {}) as Dictionary).get("light", "")), true)
	_enter_cast(beat.get("enter", {}), true)
	trav_s = 0.02
	trav_target = 0.02
	_apply_trav()
	_slicer.finish()
	perf_phases = _slicer.phases.duplicate()
	build_frames = _slicer.frames
	max_slice_ms = _slicer.max_slice_ms
	is_built = true


## Cast library skin for the walker (CastPuppet, same pose names) when it exists; scaled for the story.
func _swap_puppet(cfg: Dictionary) -> void:
	var old := world.puppet
	var pp: PaperPuppet
	var skin := str(cfg.get("skin", walker_role))
	if CastSkins.puppet_kind(skin) == "cast_puppet":
		pp = (load(CAST_PUPPET_PATH) as GDScript).new() as PaperPuppet
	else:
		pp = PaperPuppet.new()
	pp.name = "Puppet"
	pp.height = trav_h
	pp.camera = old.camera
	pp.step_period = old.step_period * 1.12
	pp.max_stride = old.max_stride * trav_h / 0.36
	pp.min_stride = old.min_stride * trav_h / 0.36
	pp.foot_lift = old.foot_lift * trav_h / 0.36
	pp.hop = old.hop * trav_h / 0.36
	# Front-facing steps toward the camera (CastPuppet.front_gait): fewer, longer steps than the template walk so
	# each lift reads (≈2 steps/s at the stroll pace, ≈1/s pushing into the wind).
	var g: Dictionary = cfg.get("gait", {})
	if "front_gait" in pp and bool(g.get("front_gait", false)):
		pp.set("front_gait", true)
		pp.step_period = float(g.get("step_period", 0.46))
		pp.min_stride = float(g.get("min_stride", 0.05))
		pp.max_stride = float(g.get("max_stride", 0.13))
		pp.foot_lift = float(g.get("foot_lift", 0.03)) * trav_h / 0.36
		pp.waddle_deg = float(g.get("waddle_deg", 4.0))
	var parent := old.get_parent()
	parent.remove_child(old)
	old.queue_free()
	parent.add_child(pp)
	world.puppet = pp
	if world.audio:
		pp.stepped.connect(func(_f, s): world.audio.step(world.walker.global_position, s))


## Road offset sign that walks toward the camera side of the page (cards face +Z, the template cameras sit at +Z).
func _toward_cam_sign(o: float) -> float:
	var c := world.path.curve
	var L := c.get_baked_length()
	var a := world.path.global_transform * c.sample_baked(clampf(o - 0.3, 0.0, L))
	var b := world.path.global_transform * c.sample_baked(clampf(o + 0.3, 0.0, L))
	return 1.0 if b.z > a.z else -1.0


## Camera yaw (deg) that looks back along the road at offset `o` while he walks toward the camera (`stroll_dir`).
func road_yaw(o: float) -> float:
	var c := world.path.curve
	var L := c.get_baked_length()
	var acc := Vector2.ZERO
	for j in 7:
		var a := clampf(o + stroll_dir * (-0.3 + 0.25 * j), 0.0, L)
		var p0 := world.path.global_transform * c.sample_baked(clampf(a - 0.1 * stroll_dir, 0.0, L))
		var p1 := world.path.global_transform * c.sample_baked(clampf(a + 0.1 * stroll_dir, 0.0, L))
		var d := Vector2(p1.x - p0.x, p1.z - p0.z)
		if d.length() > 1e-4:
			acc += d.normalized()
	if acc.length() < 1e-4:
		return world.rig.yaw_deg
	return clampf(rad_to_deg(atan2(acc.x, acc.y)), -38.0, 38.0)


## Hanger offset from the walker, turned with the camera yaw since the layout.
func _sky_rel(i: int, yaw_deg: float = NAN) -> Vector3:
	var yw := world.rig.yaw_deg if is_nan(yaw_deg) else yaw_deg
	return Basis(Vector3.UP, deg_to_rad(yw - _yaw0)) * (_sky[i]["rel"] as Vector3)


func ground_dirs() -> Array:
	var yw := deg_to_rad(world.rig.yaw_deg)
	return [Vector2(sin(yw), cos(yw)), Vector2(cos(yw), -sin(yw)), yw]  # to camera, camera right, yaw


# ------------------------------------------------------------------ spots, cast, set

## Named ground points: spread.spots {name: [right, toward camera]} from the page anchor in the template view's
## frame; "anchor" is the anchor itself.
func _build_spots() -> void:
	spots["anchor"] = _anchor
	var sp: Dictionary = (beat.get("spread", {}) as Dictionary).get("spots", {})
	for k in sp:
		spots[str(k)] = spot_point(sp[k])


func spot_point(v: Variant) -> Vector3:
	if v is String:
		return spots.get(v, _anchor)
	var a: Array = v
	var q := Vector2(_anchor.x, _anchor.z) + (_cam_basis[0] as Vector2) * float(a[0]) + (_cam_basis[1] as Vector2) * float(a[1])
	return Vector3(q.x, world.ground.surface_y(q), q.y)


## Ground vector for a direction word in the template view's frame.
func dir_vec(d: String) -> Vector3:
	var r: Vector2 = _cam_basis[0]
	var t: Vector2 = _cam_basis[1]
	var v := Vector2.ZERO
	match d:
		"right":
			v = r
		"left":
			v = -r
		"toward":
			v = t
		"away":
			v = -t
	return Vector3(v.x, 0, v.y)


func _build_hangers(cast: Dictionary) -> void:
	for role in cast:
		var cfg: Dictionary = cast[role]
		if str(cfg.get("kind", "")) != "hanger":
			continue
		var h := SkyHanger.new()
		h.name = str(role).capitalize()
		h.texture = CastSkins.texture(str(cfg.get("skin", role)))
		h.hanging = true
		h.sway_amount = float(cfg.get("sway", 0.03))
		h.bob_amount = float(cfg.get("bob", 0.012))
		h.seed_offset = float(cfg.get("seed", 0.0)) + view
		var anchor := Node3D.new()
		anchor.name = h.name + "Anchor"
		anchor.top_level = true
		add_child(anchor)
		anchor.add_child(h)
		hangers[str(role)] = h
		_sky.append({"role": str(role), "anchor": anchor, "h": h, "rel": Vector3.ZERO, "drop": 1.6, "v": 0.0,
			"target": 1.6, "delay": -1.0, "yaw": 0.0, "yaw_t": 0.0, "cfg": cfg})


func _build_actors(cast: Dictionary) -> void:
	for role in cast:
		var cfg: Dictionary = cast[role]
		if str(cfg.get("kind", "")) != "actor":
			continue
		var a := StoryActor.new()
		add_child(a)
		var skin := str(cfg.get("skin", role))
		var hu := float(cfg.get("height", 0.0))
		if hu <= 0.0:
			var d := CastPuppet.skin_def(skin)
			hu = float((d.get("hu", {}) as Dictionary).get(str((d.get("poses", {}) as Dictionary).get("calm", "")), 0.25))
		a.global_position = _anchor
		a.setup(str(role), skin, hu * ACTOR_SCALE, world.rig.camera, world.ground)
		a.pop_s = 0.02
		a.pop_target = 0.02
		actors[str(role)] = a


func actor(role: String) -> StoryActor:
	return actors.get(role)


static var _atlas := {}


static func atlas_entry(id: String) -> Dictionary:
	if _atlas.is_empty():
		var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(ATLAS_CATALOG))
		var arr: Array = parsed if parsed is Array else (parsed as Dictionary).get("cards", [])
		for e: Dictionary in arr:
			_atlas[str(e["id"])] = e
	return _atlas.get(id, {})


## Set pieces from spread.set [{card, at, stage, name, scale, z}]: stage = bands standing at the page pop
## (0 = an empty lot, "full" = all), a plain card always stands unless stage == 0.
func _build_set(list: Array) -> void:
	for e: Dictionary in list:
		var nm := str(e.get("name", e.get("at", e["card"])))
		if sets.has(nm):
			continue
		var ce := atlas_entry(str(e["card"]))
		if ce.is_empty():
			push_warning("SpreadStage: no catalog card " + str(e["card"]))
			continue
		var sp := SetPiece.new()
		sp.name = "Set_" + nm
		sp.piece_name = nm
		add_child(sp)
		var stg: Variant = e.get("stage", "full")
		var n_up := 99 if str(stg) == "full" else int(stg)
		sp.setup(ce, float(e.get("scale", SET_SCALE)), e.has("stage"), n_up)
		var p := spot_point(e.get("at", "anchor"))
		if e.has("off"):
			var o: Array = e["off"]
			p += dir_vec("right") * float(o[0]) + dir_vec("toward") * float(o[1])
			p.y = world.ground.surface_y(Vector2(p.x, p.z))
		sp.global_position = p
		sp.rotation.y = deg_to_rad(world.rig.yaw_deg) + deg_to_rad(float(e.get("yaw", 0.0)))
		for h in sp.all_hinges():
			h.snap(false)
			if not h in sp.wave_hinges():
				(h.get_parent() as Node3D).visible = false
		sets[nm] = sp
		_check_footprint(sp, e)
		_clear_area(p, sp.height * 0.75 + 0.12, float(e.get("clear", 1.0)))
		await _slicer.tick()


## Set pieces stand on the meadow: none on the road (path felt) or in the stream. Samples the card's base line (and a
## little in front / behind it) and prints SET_CHECK <name> road=<n> water=<n> (both 0 = clear); `allow_road`
## in the set entry for pieces meant to sit on the road (none so far).
func _check_footprint(sp: SetPiece, e: Dictionary) -> void:
	var g := world.ground
	var r: Vector3 = dir_vec("right")
	var t: Vector3 = dir_vec("toward")
	var road := 0
	var water := 0
	for i in 9:
		for dz: float in [-0.04, 0.0, 0.06]:
			var q3: Vector3 = sp.global_position + r * (float(i) / 8.0 - 0.5) * sp.width * 0.92 + t * dz
			var q := Vector2(q3.x, q3.z)
			if g.path_distance(q) < 0.0:
				road += 1
			if g.stream_distance(q) < 0.0:
				water += 1
	print("SET_CHECK ", sp.piece_name, " road=", road, " water=", water, " w=", snappedf(sp.width, 0.01))
	if (road > 0 and not e.get("allow_road", false)) or water > 0:
		push_warning("SpreadStage: set piece %s on the road / in the water (road %d, water %d)" % [sp.piece_name, road, water])


## Hide meadow cards standing inside a set piece / spot (hinged ones and the batched statics), with their blobs.
func _clear_area(p: Vector3, r: float, k := 1.0) -> void:
	r *= k
	if r <= 0.0:
		return
	var hidden: Array[Vector3] = []
	for hinge: PopHinge in world.hinges:
		var base := hinge.get_parent() as Node3D
		if not base.visible:
			continue
		var q := base.global_position
		var hw := float(hinge.get_meta("half_w", 0.0))
		if Vector2(q.x - p.x, q.z - p.z).length() < r + hw * 0.6:
			base.visible = false
			hidden.append(q)
	if world.batch:
		var bt := world.batch
		for rr in bt.static_ids():
			if bt.is_static_hidden(rr):
				continue
			var xf := bt.static_xform(rr)
			var o := xf.origin
			if Vector2(o.x - p.x, o.z - p.z).length() < r:
				bt.hide_static(rr)
	var keep: Array[PopHinge] = []
	for hinge: PopHinge in world.hinges:
		if (hinge.get_parent() as Node3D).visible:
			keep.append(hinge)
	world.hinges = keep
	_hide_contact_blobs(hidden)


func set_piece(nm: String) -> SetPiece:
	if sets.has(nm):
		return sets[nm]
	for k in sets:
		if (sets[k] as SetPiece).id == nm:
			return sets[k]
	return null


## enter {who: {role: pose}, at: {role: spot}}: those actors stand at their spots in those poses (first: snapped,
## they pop with the page); others step off the page unless `keep` lists them.
func _enter_cast(enter: Dictionary, first: bool) -> void:
	var who: Dictionary = enter.get("who", {})
	var at: Dictionary = enter.get("at", {})
	var keep: Array = enter.get("keep", [])
	for role in actors:
		var a: StoryActor = actors[role]
		if who.has(role):
			var p := str(who[role])
			var left := int(enter.get("left", {}).get(role, -1))
			var visible_now := a.pop_target > 0.5
			if first or not visible_now or at.has(role):
				a.place_at(spot_point(at.get(role, role if spots.has(role) else "anchor")))
			a.pose = p
			if left >= 0:
				a.facing_left = left == 1
			a.puppet.set_figure(p, a.facing_left and a.view_of(p) == "side", first or not visible_now)
			if not first and not visible_now:
				a.pop_delay = 0.1
				a.pop_target = 1.0
		elif not keep.has(role) and not first:
			a.pop_target = 0.02
			a.pop_delay = 0.0
	if first:
		for role in who:
			if actors.has(role):
				(actors[role] as StoryActor).set_meta("in_page", true)


## Same page, next beat: new set pieces pop, light changes, cast steps in / out.
func enter_beat(b: Dictionary) -> void:
	beat = b
	var sp: Dictionary = b.get("spread", {})
	for k in (sp.get("spots", {}) as Dictionary):
		spots[str(k)] = spot_point(sp["spots"][k])
	var before := sets.keys()
	await _build_set(sp.get("set", []))
	for k in sets:
		if not before.has(k):
			var s: SetPiece = sets[k]
			for h in s.wave_hinges():
				(h.get_parent() as Node3D).visible = true
				h.pop_up(0.1)
	_set_light(str(sp.get("light", "")), false)
	if _cam_anchor and not has_walker and spots.has("focus"):
		_focus_goal = spots["focus"]
	_enter_cast(b.get("enter", {}), false)
	if handler:
		handler.enter_beat(b)


# ------------------------------------------------------------------ light

func _save_light() -> void:
	var rig := world.rig
	if rig.key:
		_rig0 = {"key_e": rig.key.light_energy, "key_c": rig.key.light_color,
			"fill_e": rig.fill.light_energy if rig.fill else 0.0,
			"amb_e": rig.environment.ambient_light_energy if rig.environment else 0.0,
			"amb_c": rig.environment.ambient_light_color if rig.environment else Color.WHITE,
			"exp": rig.environment.tonemap_exposure if rig.environment else 1.0}


## "dusk": the key drops low and orange-red, the fill and ambient go cool blue, a touch darker (brick_wolf, chimney).
func _set_light(name: String, instant: bool) -> void:
	light = name
	_light_t = 1.0 if name == "dusk" else 0.0
	if instant:
		_light_k = _light_t
		_apply_light()


func _apply_light() -> void:
	if _rig0.is_empty():
		return
	var rig := world.rig
	var k := _light_k
	rig.key.light_energy = lerpf(float(_rig0["key_e"]), float(_rig0["key_e"]) * 0.8, k)
	rig.key.light_color = (_rig0["key_c"] as Color).lerp(Color(1.0, 0.6, 0.38), k)
	if rig.fill:
		rig.fill.light_energy = lerpf(float(_rig0["fill_e"]), float(_rig0["fill_e"]) * 1.5, k)
	if rig.environment:
		rig.environment.ambient_light_energy = lerpf(float(_rig0["amb_e"]), float(_rig0["amb_e"]) * 0.8, k)
		rig.environment.ambient_light_color = (_rig0["amb_c"] as Color).lerp(Color(0.55, 0.6, 0.85), k * 0.7)
		rig.environment.tonemap_exposure = lerpf(float(_rig0["exp"]), float(_rig0["exp"]) * 0.9, k)


# ------------------------------------------------------------------ sky layout

func _apply_shot_now(name: String) -> void:
	var s: Array = _wide if name == "wide" else _shots[name]
	var rig := world.rig
	rig.distance = s[0]
	rig.elevation_deg = s[1]
	rig.focus_height = s[2]
	rig.fov = s[3]
	rig.snap()


## Hang the sky cast where the story shot frames it (cast `screen` fractions, card height `frac` of the frame),
## a little in front of the walker, in the sky band clear of the canopy. Positions are kept relative to the walker
## (the sky follows him along the road), sizes from the frame height at their depth.
func _layout_sky() -> void:
	if _sky.is_empty():
		return
	_apply_shot_now("story")
	var cam := camera()
	var vs := Vector2(1366, 1024)
	var vp := get_viewport()
	if vp:
		vs = vp.get_visible_rect().size
	var tp := traveller_pos()
	var fwd := -cam.global_transform.basis.z
	var depth := (tp + Vector3(0, 0.3, 0) - cam.global_position).dot(fwd) - 0.3
	var frame_h := 2.0 * depth * tan(deg_to_rad(cam.fov * 0.5))
	for i in _sky.size():
		var h: SkyHanger = _sky[i]["h"]
		var cfg: Dictionary = _sky[i]["cfg"]
		var scr: Array = cfg.get("screen", [0.5, 0.25])
		var ch := frame_h * float(cfg.get("frac", 0.27))
		h.card_height = ch
		h.card().height = ch  # SkyHanger sized its card in _ready
		h.stem_height = 1.4
		var centre := cam.project_position(vs * Vector2(float(scr[0]), float(scr[1])), depth)
		# anchor = card centre + half the card + the string
		var anchor := centre + Vector3(0, ch * 0.5 + h.stem_height, 0)
		_sky[i]["rel"] = anchor - tp
		_sky[i]["base"] = anchor
		(_sky[i]["anchor"] as Node3D).global_position = anchor + Vector3(0, 1.6, 0)
		var yaw := atan2(cam.global_position.x - centre.x, cam.global_position.z - centre.z)
		(_sky[i]["anchor"] as Node3D).rotation.y = yaw
		_sky[i]["face"] = yaw
		if cfg.has("backing"):
			_add_backing(h, cfg)
	_yaw0 = world.rig.yaw_deg
	_apply_shot_now("wide")


## A cut-paper sky disc behind the card (cast `backing`: [fill, rim]) so the sky cast reads against orange trees
## and haze (sun_wind critics 1-2).
func _add_backing(h: SkyHanger, cfg: Dictionary) -> void:
	await get_tree().process_frame  # SkyHanger builds its card in _ready
	if not is_instance_valid(h):
		return
	var c := h.card()
	var disc := PaperCard.new()
	var cols: Array = cfg["backing"]
	disc.texture = _make_disc_texture(Color(str(cols[0])), Color(str(cols[1])))
	disc.height = h.card_height * float(cfg.get("backing_scale", 1.1))
	disc.thickness = 0.01
	disc.back_print = false
	# Child of the card itself so it always follows it (as a sibling it kept a stale position when a story
	# started mid-way with --beat, and the discs were left lying on the meadow).
	disc.name = "SkyDisc"
	disc.position = Vector3(0, -h.card_height * float(cfg.get("backing_drop", 0.06)), -0.03)
	for old in c.get_children():
		if old.name == "SkyDisc":
			old.queue_free()
	c.add_child(disc)


# ------------------------------------------------------------------ sightlines

## Story dressing on top of the template: hinged meadow cards standing between the story camera and the cast are
## left out of this spread (hidden, never popped), and so are their contact shadows.
func _clear_sightlines() -> void:
	var w := world.walker
	var home := w.offset
	var stops: Array[float] = [home]
	if route != Vector2.ZERO:
		var L := world.path.curve.get_baked_length()
		var n := maxi(1, ceili(absf(route.y - route.x) / 0.25))
		for i in n + 1:
			stops.append(clampf(_start_off + lerpf(route.x, route.y, float(i) / n), 0.0, L))
	var keep_all: Array[PopHinge] = world.hinges.duplicate()
	var hidden: Array[Vector3] = []
	var yaw_home := world.rig.yaw_deg
	if has_walker:
		for o in stops:
			w.global_position = world.path.global_transform * world.path.curve.sample_baked(o)
			world.focus.snap()
			if road_cam:
				world.rig.yaw_deg = road_yaw(o)
			await _clear_sightlines_here(keep_all, hidden, "story")
			await _slicer.tick()
		w.global_position = world.path.global_transform * world.path.curve.sample_baked(home)
		world.focus.snap()
		world.rig.yaw_deg = yaw_home
	else:
		# fixed stage: the anchor focus, every shot the tale uses
		_cam_anchor = Node3D.new()
		_cam_anchor.name = "StageFocus"
		_cam_anchor.top_level = true
		add_child(_cam_anchor)
		_focus_goal = spot_point((beat.get("spread", {}) as Dictionary).get("focus", "focus" if spots.has("focus") else "anchor"))
		_cam_anchor.global_position = _focus_goal
		world.rig.focus_target = _cam_anchor
		for sh in _shots_used():
			await _clear_sightlines_here(keep_all, hidden, sh)
			await _slicer.tick()
	var keep: Array[PopHinge] = []
	for hinge: PopHinge in world.hinges:
		if (hinge.get_parent() as Node3D).visible:
			keep.append(hinge)
	world.hinges = keep
	_hide_contact_blobs(hidden)
	_apply_shot_now("wide")
	print("SPREAD view=", view, " route=", route, " sightline cards hidden=", hidden.size(), " statics hidden=", _statics_hidden)


func _shots_used() -> Array:
	var out := ["wide"]
	for st: Dictionary in beat.get("steps", []):
		if str(st.get("do", "")) == "cam" and not out.has(str(st["shot"])):
			out.append(str(st["shot"]))
	if not out.has("story"):
		out.append("story")
	return out


## Screen rects (+ camera distance) the camera must see clearly: sky cast, walker, spots and set pieces.
func _sight_rects(cam: Camera3D) -> Array:
	var cp := cam.global_position
	var rects: Array = []
	for i in _sky.size():
		var h: SkyHanger = _sky[i]["h"]
		var anchor: Vector3 = traveller_pos() + _sky_rel(i)
		var c := anchor - Vector3(0, h.stem_height + h.card_height * 0.5, 0)
		var a := cam.unproject_position(c)
		var b := cam.unproject_position(c + Vector3(0, h.card_height * 0.7, 0))
		var r := a.distance_to(b)
		rects.append([Rect2(a - Vector2(r, r), Vector2(r, r) * 2.0).grow(10.0), cp.distance_to(c)])
	if has_walker:
		var tp := traveller_pos()
		var ta := cam.unproject_position(tp)
		var tb := cam.unproject_position(tp + Vector3(0, trav_h, 0))
		var tw := absf(ta.y - tb.y) * 0.45
		rects.append([Rect2(ta.x - tw, tb.y, tw * 2.0, ta.y - tb.y).abs().grow(12.0), cp.distance_to(tp)])
	else:
		# every named spot (cast stands / walks there) and the set (houses ~0.9 tall)
		for k in spots:
			var p: Vector3 = spots[k]
			var hh := 0.95
			var a := cam.unproject_position(p)
			var b := cam.unproject_position(p + Vector3(0, hh, 0))
			var tw := absf(a.y - b.y) * 0.5
			rects.append([Rect2(a.x - tw, b.y, tw * 2.0, a.y - b.y).abs().grow(8.0), cp.distance_to(p)])
	return rects


func _clear_sightlines_here(all: Array[PopHinge], hidden: Array[Vector3], shot_name: String) -> void:
	_apply_shot_now(shot_name)
	var cam := camera()
	var cp := cam.global_position
	var rects := _sight_rects(cam)
	for hinge: PopHinge in all:
		var base := hinge.get_parent() as Node3D
		if not base.visible:
			continue
		var p := base.global_position
		var hh := float(hinge.get_meta("card_h", 0.0))
		var hw := float(hinge.get_meta("half_w", 0.0))
		var a := cam.unproject_position(p)
		var b := cam.unproject_position(p + Vector3(0, hh, 0))
		var ppu := absf(a.y - b.y) / maxf(hh, 0.001)
		var r := Rect2(a.x - hw * ppu, b.y, hw * ppu * 2.0, a.y - b.y).abs()
		var blocks := false
		# The road camera walks backwards down the road: a card it passes through (or that stands right at the
		# lens, base just behind it) fills the frame with a blurred leaf. Anything that close goes.
		if Vector2(p.x - cp.x, p.z - cp.z).length() < 0.9 + hw:
			base.visible = false
			hidden.append(p)
			continue
		if cam.is_position_behind(p) or cam.is_position_behind(p + Vector3(0, hh, 0)):
			continue
		for sr in rects:
			if cp.distance_to(p) < float(sr[1]) and r.intersects(sr[0]):
				blocks = true
		if blocks:
			base.visible = false
			hidden.append(p)
	await _slicer.tick()
	await _clear_statics_here(cam, rects)


## Same test for the template's static cards (CardBatch), which lie beyond the pop radius: the road camera now
## travels with him, so it can reach them. Hidden instances are collapsed to zero size.
func _clear_statics_here(cam: Camera3D, rects: Array) -> void:
	if world.batch == null:
		return
	var cp := cam.global_position
	var bt := world.batch
	var n := 0
	for r in bt.static_ids():
		n += 1
		if n % 256 == 0:
			await _slicer.tick()
		if bt.is_static_hidden(r):
			continue
		var xf := bt.static_xform(r)
		var ab := bt.static_aabb(r)
		var sc := xf.basis.get_scale()
		var p := xf.origin
		var hh := ab.end.y * sc.y
		var hw := maxf(absf(ab.position.x), absf(ab.end.x)) * sc.x
		var hide := Vector2(p.x - cp.x, p.z - cp.z).length() < 0.9 + hw
		if not hide and not (cam.is_position_behind(p) or cam.is_position_behind(p + Vector3(0, hh, 0))):
			var a := cam.unproject_position(p)
			var b := cam.unproject_position(p + Vector3(0, hh, 0))
			var ppu := absf(a.y - b.y) / maxf(hh, 0.001)
			var rr := Rect2(a.x - hw * ppu, b.y, hw * ppu * 2.0, a.y - b.y).abs()
			for sr in rects:
				if cp.distance_to(p) < float(sr[1]) and rr.intersects(sr[0]):
					hide = true
		if hide:
			bt.hide_static(r)  # collapsed to zero size, shadow quad too (was: MultiMesh instance scaled to 0.0001)
			_statics_hidden += 1


func _hide_contact_blobs(points: Array[Vector3]) -> void:
	var cs := world.contact
	if cs == null or cs.multimesh == null or points.is_empty():
		return
	var mm := cs.multimesh
	var n := 0
	for i in mm.instance_count:
		var o := mm.get_instance_transform(i).origin
		for p in points:
			if Vector2(o.x - p.x, o.z - p.z).length() < 0.06:
				mm.set_instance_transform(i, Transform3D(Basis.from_scale(Vector3(0.0001, 1, 0.0001)), o))
				n += 1
				break
	print("SPREAD contact blobs hidden=", n)


# ------------------------------------------------------------------ page

## Raise the spread in a wave from the walker; returns seconds until the last piece starts.
func pop(start := 0.0) -> float:
	var wave := PopWave.new()
	wave.speed = 4.0
	var all: Array[PopHinge] = world.hinges.duplicate()
	for k in sets:
		for h in (sets[k] as SetPiece).wave_hinges():
			(h.get_parent() as Node3D).visible = true
			all.append(h)
	var end := wave.pop(all, _origin, start)
	trav_delay = start + 0.12
	trav_target = 1.0
	for i in _sky.size():
		_sky[i]["delay"] = start + minf(end, 0.9) + 0.2 + i * 0.25
		_sky[i]["target"] = 0.0
	var j := 0
	for role in actors:
		var a: StoryActor = actors[role]
		if a.has_meta("in_page"):
			a.pop_delay = start + 0.2 + 0.12 * j
			a.pop_target = 1.0
			j += 1
	return maxf(end, minf(end, 0.9) + 0.6)


## Fold everything back flat (outside-in, like the book closing); returns seconds until all are moving.
func fold() -> float:
	var all: Array = []
	all.append_array(world.hinges)
	all.append_array(extra_hinges)
	for k in sets:
		for h in (sets[k] as SetPiece).all_hinges():
			if (h.get_parent() as Node3D).visible:
				all.append(h)
	var wave := PopWave.new()
	var t := wave.fold(all, _origin, 0.0, true)
	for i in _sky.size():
		_sky[i]["delay"] = 0.0
		_sky[i]["target"] = 1.8
	trav_delay = maxf(t - 0.2, 0.0)
	trav_target = 0.02
	for role in actors:
		var a: StoryActor = actors[role]
		a.pop_delay = maxf(t - 0.25, 0.0)
		a.pop_target = 0.02
	if _counter:
		_counter_s = 0.0
	shot_to("wide")
	return t


## Camera shot on the template rig: "wide" (template view) | "story" | "close" | tale shots. `at`: focus spot.
func shot_to(name: String, at: Variant = null) -> void:
	shot = name
	_cam = _wide.duplicate() if name == "wide" else (_shots[name] as Array).duplicate()
	if at != null and _cam_anchor:
		_focus_goal = spot_point(at)


# ------------------------------------------------------------------ walker

func puppet() -> PaperPuppet:
	return world.puppet


func set_pose(p: String, instant := false) -> void:
	world.puppet.set_pose(p, instant)
	if handler:
		handler.fx("_pose:" + p)


## `dist` > 0 = on along his way (down the road toward the camera, see road_cam).
func walk_by(dist: float) -> void:
	var w := world.walker
	w.target_offset = clampf(w.offset + stroll_dir * dist, 0.0, world.path.curve.get_baked_length())


func walk_to_offset(o: float) -> void:
	world.walker.target_offset = o


func walk_to_place(place: String) -> void:
	if handler and handler.walk_to_place(place):
		return
	if spots.has(place):
		var w := world.walker
		w.path = null
		walk_goal = spots[place]
		w.walk_to(walk_goal)


func walking() -> bool:
	var w := world.walker
	if w.path == null:
		return Vector2(w.global_position.x - walk_goal.x, w.global_position.z - walk_goal.z).length() > 0.015 or world.puppet.speed > 0.02
	return absf(w.target_offset - w.offset) > 0.006 or world.puppet.speed > 0.02


func traveller_pos() -> Vector3:
	return world.walker.global_position


## Ending: the camera stops following and he walks off down the road.
func walk_away(dist: float) -> void:
	_cam_anchor = Node3D.new()
	_cam_anchor.top_level = true
	add_child(_cam_anchor)
	_cam_anchor.global_position = world.focus.global_position
	_focus_goal = _cam_anchor.global_position
	world.rig.focus_target = _cam_anchor
	follow_sky = false
	walk_by(dist)


## Keep walking along the road at `speed` until stroll_stop() (camera and sky cast follow him).
func stroll(speed: float) -> void:
	strolling_on = true
	stroll_speed = speed


func stroll_stop() -> void:
	strolling_on = false
	var w := world.walker
	w.target_offset = clampf(w.offset + stroll_dir * 0.05, 0.0, world.path.curve.get_baked_length())


func strolling() -> bool:
	return strolling_on


func _step_stroll(dt: float) -> void:
	var w := world.walker
	var pp := world.puppet
	if push > 0.0:
		push -= dt
		if push <= 0.0:
			pp.max_turn_deg = 20.0
		return
	if not strolling_on:
		return
	if pause > 0.0:
		pause -= dt
		w.target_offset = w.offset
		return
	var L := world.path.curve.get_baked_length()
	var k := handler.stroll_mod(dt, pp) if handler else 1.0
	w.speed = lerpf(w.speed, stroll_speed * k, 1.0 - exp(-2.0 * dt))
	var lo := 0.0
	var hi := L
	if route != Vector2.ZERO:  # never past the stretch whose sightlines were cleared
		lo = clampf(_start_off + minf(route.x, route.y), 0.0, L)
		hi = clampf(_start_off + maxf(route.x, route.y), 0.0, L)
	w.target_offset = clampf(w.offset + stroll_dir * 0.6, lo, hi)


## Shoved back half a step, he plants and leans in again (he keeps facing his way, no turn-around flip).
func shove() -> void:
	var w := world.walker
	var pp := world.puppet
	pp.max_turn_deg = 0.0
	w.speed = 0.16
	w.target_offset = clampf(w.offset - stroll_dir * 0.07, 0.0, world.path.curve.get_baked_length())
	push = 1.0


func _apply_trav() -> void:
	if not has_walker:
		return
	var w := world.walker
	w.scale = Vector3(1.0, maxf(trav_s, 0.02), 1.0)
	world.puppet.visible = trav_s > 0.05
	# Only vertical here: the puppet measures its own ground motion for the gait, so a sideways jitter on its
	# position made it take steps in place. The shiver is CastPuppet.shiver (body rocks, feet planted).
	world.puppet.position = Vector3(0, hop - sink + ground_dy, 0)
	if "shiver" in world.puppet:
		world.puppet.set("shiver", shiver)


# ------------------------------------------------------------------ taps

func camera() -> Camera3D:
	return world.rig.camera


func hanger(role: String) -> SkyHanger:
	return hangers.get(role)


func _card_centre(h: SkyHanger) -> Vector3:
	var c := h.card()
	return c.global_transform * Vector3(0, h.card_height * 0.5, 0)


func card_centre(h: SkyHanger) -> Vector3:
	return _card_centre(h)


## Every tap target on this page: hangers, the walker, actors on the page, set pieces, the handler's own.
func targets() -> Array:
	var out: Array = []
	for i in _sky.size():
		out.append(_sky[i]["role"])
	if has_walker:
		out.append(walker_role)
	for r in actors:
		if (actors[r] as StoryActor).pop_target > 0.5:
			out.append(r)
	for k in sets:
		out.append(k)
	if handler:
		out.append_array(handler.targets())
	return out


func _target_point(target: String) -> Variant:
	if hangers.has(target):
		return _card_centre(hangers[target])
	if has_walker and target == walker_role:
		return traveller_pos() + Vector3(0, trav_h * 0.5, 0)
	if actors.has(target):
		return (actors[target] as StoryActor).centre()
	if sets.has(target):
		return (sets[target] as SetPiece).centre()
	if handler:
		return handler.target_point(target)
	return null


## Screen position of a tap target.
func target_screen(target: String) -> Vector2:
	var p: Variant = _target_point(target)
	if p == null:
		return Vector2(-1000, -1000)
	return camera().unproject_position(p)


func target_radius(target: String) -> float:
	var cam := camera()
	if has_walker and target == walker_role:
		var a := cam.unproject_position(traveller_pos())
		var b := cam.unproject_position(traveller_pos() + Vector3(0, trav_h, 0))
		return maxf(80.0, a.distance_to(b) * 0.55)
	if hangers.has(target):
		var h: SkyHanger = hangers[target]
		var c := _card_centre(h)
		var top := cam.unproject_position(c + Vector3(0, h.card_height * 0.5, 0))
		return maxf(90.0, cam.unproject_position(c).distance_to(top) * 1.1)
	if actors.has(target):
		var ac: StoryActor = actors[target]
		var a := cam.unproject_position(ac.global_position)
		var b := cam.unproject_position(ac.global_position + Vector3(0, ac.puppet.height, 0))
		return maxf(70.0, a.distance_to(b) * 0.6)
	if sets.has(target):
		var s: SetPiece = sets[target]
		var a := cam.unproject_position(s.global_position)
		var b := cam.unproject_position(s.global_position + Vector3(0, maxf(s.height, 0.12), 0))
		return maxf(70.0, a.distance_to(b) * 0.6)
	if handler:
		var r := handler.target_radius(target)
		if r > 0.0:
			return r
	return 80.0


## Which story target a screen point hits ("" for none). Kids' taps are generous.
func hit_target(p: Vector2) -> String:
	var best := ""
	var bd := INF
	for t in targets():
		var sp := target_screen(str(t))
		if sp.x < -999.0:
			continue
		var d := p.distance_to(sp) / target_radius(str(t))
		if d < 1.0 and d < bd:
			bd = d
			best = str(t)
	return best


## A little reaction when a cast member is tapped.
func wiggle(target: String) -> void:
	if handler and handler.wiggle(target):
		return
	if has_walker and target == walker_role:
		hop_v = 0.9
	elif actors.has(target):
		(actors[target] as StoryActor).hop_v = 0.7
	elif sets.has(target):
		(sets[target] as SetPiece).bounce()


# ------------------------------------------------------------------ effects

## Held press on a blow target. power 1 = normal, 2 = gale, 0.35 = gentle breeze.
func set_blowing(on: bool, power := 1.0) -> void:
	if handler:
		handler.set_blowing(on, power)


func fx(name: String) -> void:
	if name == "":
		return
	if handler and handler.fx(name):
		fx_done.emit(name)
		return
	if name.begins_with("pop:"):
		var sp := set_piece(name.substr(4))
		if sp:
			sp.pop_card(0.0)
			sp.bounce()
	elif name.begins_with("fold:"):
		var sp2 := set_piece(name.substr(5))
		if sp2:
			sp2.collapse(0.0)
	fx_done.emit(name)


## On-page counter (a big printed number floating over a set piece), pops on each change.
func show_counter(n: int, over: String) -> void:
	if _counter == null:
		_counter = Label3D.new()
		_counter.name = "Counter"
		_counter.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		_counter.font_size = 160
		_counter.outline_size = 36
		_counter.modulate = Color("fff4dc")
		_counter.outline_modulate = Color("8a3b1f")
		_counter.pixel_size = 0.0011
		_counter.no_depth_test = true
		_counter.fixed_size = false
		_counter.shaded = false
		_counter.top_level = true
		add_child(_counter)
	_counter.text = str(n)
	var sp := set_piece(over)
	# beside the house, upper left (above it the roof / chimney run out of the frame)
	var p := sp.global_position + Vector3(0, sp.height * 0.8, 0) + dir_vec("left") * sp.height * 0.42 + dir_vec("toward") * 0.1 if sp else _anchor + Vector3(0, 0.6, 0)
	_counter.global_position = p
	_counter_s = 1.0
	_counter_v = 6.0


func hide_counter() -> void:
	_counter_s = 0.0


func _process(dt: float) -> void:
	dt = PaperSpring.frame_dt(dt)
	if world == null or not is_built:
		return
	_t += dt
	var trav := traveller_pos()
	# Camera shot glide (the rig itself snaps to the focus every frame; we ease its shot parameters).
	var rig := world.rig
	var k := 1.0 - exp(-2.4 * dt)
	rig.distance = lerpf(rig.distance, float(_cam[0]), k)
	rig.elevation_deg = lerpf(rig.elevation_deg, float(_cam[1]), k)
	rig.focus_height = lerpf(rig.focus_height, float(_cam[2]), k)
	rig.fov = lerpf(rig.fov, float(_cam[3]), k)
	if _cam_anchor and not has_walker:
		_cam_anchor.global_position = _cam_anchor.global_position.lerp(_focus_goal, k)
	# Road camera: stands ahead of him on the road looking back along it (see road_cam); frozen once the ending
	# camera stops following or he leaves the road.
	if road_cam and _cam_anchor == null and world.walker.path != null:
		_yaw_t = lerpf(_yaw_t, road_yaw(world.walker.offset), 1.0 - exp(-0.9 * dt))
		rig.yaw_deg = lerpf(rig.yaw_deg, _yaw_t, 1.0 - exp(-1.6 * dt))
	# Sky cast: hangs relative to the walker, drops in on its strings, turns toward each other (pull / yaw_t).
	pull = lerpf(pull, pull_t, 1.0 - exp(-1.5 * dt))
	var mid := Vector3.ZERO
	for i in _sky.size():
		mid += _sky_rel(i)
	if not _sky.is_empty():
		mid /= _sky.size()
	for i in _sky.size():
		var s: Dictionary = _sky[i]
		if float(s["delay"]) >= 0.0:
			s["delay"] = float(s["delay"]) - dt
		var tgt: float = s["target"] if float(s["delay"]) < 0.0 else float(s["drop"]) + 0.0
		var w := TAU * 1.6
		s["v"] = float(s["v"]) + (-w * w * (float(s["drop"]) - tgt) - 2.0 * 0.42 * w * float(s["v"])) * dt
		s["drop"] = float(s["drop"]) + float(s["v"]) * dt
		s["yaw"] = lerpf(float(s["yaw"]), float(s["yaw_t"]), 1.0 - exp(-3.0 * dt))
		var an := s["anchor"] as Node3D
		var rel0 := _sky_rel(i)
		var base: Vector3 = s.get("base", trav + rel0)
		var rel: Vector3 = rel0.lerp(Vector3(mid.x, rel0.y, mid.z), pull)
		if follow_sky:
			base = base.lerp(trav + rel, 1.0 - exp(-2.0 * dt))
		s["base"] = base
		an.global_position = base + Vector3(0, float(s["drop"]), 0)
		if s.has("face"):
			an.rotation.y = float(s["face"]) + deg_to_rad(rig.yaw_deg - _yaw0)
		(s["h"] as SkyHanger).rotation.y = float(s["yaw"])
	if has_walker:
		# Walker pop (scale on the walker, springy), hop, sink.
		if trav_delay >= 0.0:
			trav_delay -= dt
		if trav_delay < 0.0:
			var w2 := TAU * 2.4
			_trav_v += (-w2 * w2 * (trav_s - trav_target) - 2.0 * 0.35 * w2 * _trav_v) * dt
			trav_s = clampf(trav_s + _trav_v * dt, 0.02, 1.3)
		hop_v -= 6.0 * dt
		hop = maxf(0.0, hop + hop_v * dt)
		if hop <= 0.0 and hop_v < 0.0:
			hop_v = 0.0
		sink = lerpf(sink, sink_target, 1.0 - exp(-3.0 * dt))
		# Off the road (stream spot): follow the real ground height under him, so he steps DOWN off the felt bank onto
		# the recessed water instead of floating at road height.
		var want_dy := 0.0
		if world.walker.path == null:
			var tq := Vector2(trav.x, trav.z)
			want_dy = world.ground.surface_y(tq) - world.walker.global_position.y
		ground_dy = lerpf(ground_dy, want_dy, 1.0 - exp(-10.0 * dt))
		_step_stroll(dt)
		_apply_trav()
	if not is_equal_approx(_light_k, _light_t):
		_light_k = move_toward(_light_k, _light_t, dt * 0.5)
		_apply_light()
	if _counter:
		var cs := PaperSpring.step(_counter.scale.x, _counter_v, _counter_s, 9.0, 0.35, dt)
		_counter_v = cs.y
		_counter.scale = Vector3.ONE * maxf(cs.x, 0.001)
		_counter.visible = cs.x > 0.02
	if handler:
		handler.step(dt)


static func _make_disc_texture(fill: Color, rim: Color) -> Texture2D:
	var n := 192
	var img := Image.create(n, n, false, Image.FORMAT_RGBA8)
	var c := Vector2(n, n) * 0.5
	for y in n:
		for x in n:
			var p := Vector2(x + 0.5, y + 0.5) - c
			var a := atan2(p.y, p.x)
			var r := n * 0.47 + sin(a * 23.0) * 0.8 + sin(a * 7.0 + 1.0) * 1.2  # deckled cut
			var d := p.length()
			if d < r:
				var col := fill if d < r - 5.0 else rim
				if d < r * 0.9 and fmod(a * 12.0 / TAU + 0.5, 1.0) < 0.03 and d > r * 0.84:
					col = fill.lerp(rim, 0.4)  # faint printed stitch ring
				img.set_pixel(x, y, col)
			else:
				img.set_pixel(x, y, Color(0, 0, 0, 0))
	return ImageTexture.create_from_image(img)
