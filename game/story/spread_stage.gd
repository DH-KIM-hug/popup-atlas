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
	world.theme = str(tale.get("theme", ""))  # sunmoon: "korean" dressing of the template (2026-11-22)
	world.ground_style = str(tale.get("ground_style", "paper"))  # paper ground for every tale (2026-11-22); "felt" opt-in
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
		# MOVE / TRACK lines for the legacy Walker (gate audit v1: sun_wind's traveller was invisible to the gate)
		var wl := WalkerLog.new()
		wl.name = "WalkerLog"
		wl.walker = world.walker
		wl.puppet = world.puppet
		wl.role = walker_role
		wl.skin = str((cast[walker_role] as Dictionary).get("skin", walker_role))
		add_child(wl)
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
	_build_sky((beat.get("spread", {}) as Dictionary).get("sky", {}))
	_apply_built((beat.get("spread", {}) as Dictionary).get("built", []), false)
	if handler:
		_slicer.phase("tale")
		await _slicer.tick()
		await handler.build_async()
	await _slicer.tick()
	_slicer.phase("finish")
	_save_light()
	_set_light(str((beat.get("spread", {}) as Dictionary).get("light", "")), true)
	if tale.has("backdrop"):
		_apply_light()
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
	if not a.is_empty() and a[0] is String:  # a list of spots: their centre (a two-shot framed between its marks)
		var c := Vector3.ZERO
		for nm in a:
			c += spot_point(str(nm))
		return c / a.size()
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
		var nm := str(e.get("name", e.get("at", e.get("card", e.get("build", "building")))))
		if sets.has(nm):
			continue
		var ce := atlas_entry(str(e.get("card", "")))
		if ce.is_empty() and not e.has("build"):
			push_warning("SpreadStage: no catalog card " + str(e.get("card", "")))
			continue
		var sp := SetPiece.new()
		sp.name = "Set_" + nm
		sp.piece_name = nm
		add_child(sp)
		var stg: Variant = e.get("stage", "full")
		var n_up := 99 if str(stg) == "full" else int(stg)
		if e.has("build"):  # a 3D building from the kit (Building: pavilions, towers, castles, 2026-11-23)
			sp.setup_building(e["build"], float(e.get("scale", 1.0)), n_up, e.get("state", {}))
		else:
			sp.setup(ce, float(e.get("scale", SET_SCALE)), e.has("stage") and not e.get("flat", false), n_up, bool(e.get("flat", false)))
			if sp.flat and sp.card:  # a ground sheet (turnip v3): thin, its cut edge in its own colour so no slab shows
				if e.has("thick"):
					sp.card.thickness = float(e["thick"])
				if e.has("edge"):
					sp.card.edge_color = Color(str(e["edge"]))
		var p := spot_point(e.get("at", "anchor"))
		if e.has("off"):
			var o: Array = e["off"]
			p += dir_vec("right") * float(o[0]) + dir_vec("toward") * float(o[1])
			p.y = world.ground.surface_y(Vector2(p.x, p.z))
		p.y += float(e.get("lift", 0.0))  # raised pieces: a pot over the fire, a flue above the hearth
		sp.global_position = p
		sp.rotation.y = deg_to_rad(world.rig.yaw_deg) + deg_to_rad(float(e.get("yaw", 0.0)))
		for h in sp.all_hinges():
			h.snap(false)
			if not h in sp.wave_hinges():
				(h.get_parent() as Node3D).visible = false
		sets[nm] = sp
		if not sp.bands.is_empty():
			for n in world.get_children():
				if n is ChimneySmoke and Vector2(n.global_position.x - p.x, n.global_position.z - p.z).length() < maxf(sp.width, 0.8):
					(n as Node3D).visible = false  # a template house's smoke must not rise from a story house
		if e.has("box"):
			var bx: Dictionary = (e["box"] as Dictionary).duplicate()
			for k in ["side", "inner", "floor"]:
				if bx.has(k):
					var be := atlas_entry(str(bx[k]))
					var bp := str(be.get("path", ""))
					bx[k] = bp if bp.begins_with("res://") else "res://" + bp
			sp.add_box(bx)
		elif not e.get("flat", false) and e.has("card") and not HouseBody.spec_for(str(e["card"])).is_empty():
			sp.add_box({"auto": true})  # every house stands as a volume (2026-11-23)
		if e.get("inside_only", false):
			sp.set_meta("inside_only", true)
			sp.visible = false
		if e.get("door_in", false):
			sp.door_inward = true
		if e.has("glow"):  # night: the printed light on the card (lit windows, candles) emits (paper_print glow)
			_set_glow(sp, float(e["glow"]))
		if e.has("light"):  # a warm pool of light: [energy, height (units), range, colour, flicker]
			_add_light(sp, e["light"])
		if e.get("flat", false) and e.get("floor", false):
			# a flat piece people stand on (turnip's garden plot): its rectangle lifts the walk surface, and the spots
			# resolve again so marks / pieces on it stand on its top (turnip v2 2026-11-23)
			var fr := sp.global_transform.basis.x.normalized() * sp.width * 0.5
			var fa := -sp.global_transform.basis.z.normalized() * sp.height
			var fp := PackedVector2Array()
			for c3: Vector3 in [p - fr, p + fr, p + fr + fa, p - fr + fa]:
				fp.append(Vector2(c3.x, c3.z))
			world.ground.floors.append([fp, p.y + 0.003 + sp.card.thickness * 0.5])
			_build_spots()
			_clear_area(p + fa * 0.5, Vector2(sp.width, sp.height).length() * 0.5, float(e.get("clear", 1.0)))
		_check_footprint(sp, e)
		_clear_area(p, sp.height * 0.75 + 0.12, float(e.get("clear", 1.0)))
		await _slicer.tick()


## Night sky (spread.sky, witch_candy 2026-11-20): a huge cardstock sky card far behind the page (deep blue, lighter
## toward the horizon, printed stars), the moon card and star cards in front of it. Unshaded and fog-free, so the haze
## that turns the far hills night-blue does not grey them. {bg, fog, fog_energy, moon: card id, moon_at [right, away,
## up, size], stars: card id, n}
func _build_sky(sky: Dictionary) -> void:
	if sky.is_empty():
		return
	var root := Node3D.new()
	root.name = "NightSky"
	add_child(root)
	var r := dir_vec("right")
	var aw := dir_vec("away")
	# the template view's yaw (not the rig's: mid-page the rig carries a shot's yaw offset and the quads turned away)
	var yaw := atan2((_cam_basis[1] as Vector2).x, (_cam_basis[1] as Vector2).y)
	var mk := func(tex: Texture2D, w: float, h: float, pos: Vector3, energy: float) -> MeshInstance3D:
		var q := QuadMesh.new()
		q.size = Vector2(w, h)
		var m := StandardMaterial3D.new()
		m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		m.albedo_texture = tex
		m.albedo_color = Color(energy, energy, energy)
		m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
		m.alpha_scissor_threshold = 0.5
		m.disable_fog = true
		m.texture_filter = BaseMaterial3D.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS
		var mi := MeshInstance3D.new()
		mi.mesh = q
		mi.material_override = m
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		root.add_child(mi)
		mi.global_position = pos
		mi.rotation.y = yaw
		return mi
	var far := float(sky.get("far", 16.0))
	var draw_stars := int(sky.get("n", 14)) > 0
	mk.call(_sky_texture(Color(str(sky.get("top", "#0b1230"))), Color(str(sky.get("horizon", "#2b3d7a"))), draw_stars),
		far * 4.0, far * 1.1, _anchor + aw * far + Vector3.UP * far * 0.42, 1.0)
	var star := str(sky.get("stars", ""))
	var ce := atlas_entry(star)
	if not ce.is_empty():
		var tex: Texture2D = load("res://" + str(ce["path"]))
		var rng := RandomNumberGenerator.new()
		rng.seed = 77
		for i in int(sky.get("n", 14)):
			var d := far * rng.randf_range(0.55, 0.85)
			var sz := rng.randf_range(0.12, 0.28)
			mk.call(tex, sz, sz, _anchor + aw * d + r * rng.randf_range(-d * 0.8, d * 0.8) + Vector3.UP * rng.randf_range(d * 0.18, d * 0.42), 1.1)
	var me := atlas_entry(str(sky.get("moon", "")))
	if not me.is_empty():
		var ma: Array = sky.get("moon_at", [-2.0, 11.0, 3.4, 2.2])
		mk.call(load("res://" + str(me["path"])), float(ma[3]), float(ma[3]),
			_anchor + r * float(ma[0]) + aw * float(ma[1]) + Vector3.UP * float(ma[2]), 1.15)


static func _sky_texture(top: Color, hor: Color, draw_stars := true) -> Texture2D:
	var w := 1280
	var h := 400
	var rng := RandomNumberGenerator.new()
	rng.seed = 5
	# Smooth low-amplitude paper fibre tooth (coarse 8 px lattice, bilinearly interpolated: zero salt-and-pepper blocks).
	var step := 8
	var gw := (w >> 3) + 2
	var gh := (h >> 3) + 2
	var grid := PackedFloat32Array()
	grid.resize(gw * gh)
	for i in grid.size():
		grid[i] = rng.randf_range(-0.006, 0.006)
	var data := PackedByteArray()
	data.resize(w * h * 4)
	for y in h:
		var c := top.lerp(hor, pow(float(y) / h, 1.6))
		var gy := y >> 3
		var fy := float(y & 7) / float(step)
		var row0 := gy * gw
		var row1 := (gy + 1) * gw
		for x in w:
			var gx := x >> 3
			var fx := float(x & 7) / float(step)
			var n0 := lerpf(grid[row0 + gx], grid[row0 + gx + 1], fx)
			var n1 := lerpf(grid[row1 + gx], grid[row1 + gx + 1], fx)
			var n := lerpf(n0, n1, fy)
			var idx := (y * w + x) * 4
			data[idx] = int(clampf(c.r + n, 0.0, 1.0) * 255.0)
			data[idx + 1] = int(clampf(c.g + n, 0.0, 1.0) * 255.0)
			data[idx + 2] = int(clampf(c.b + n, 0.0, 1.0) * 255.0)
			data[idx + 3] = 255
	var img := Image.create_from_data(w, h, false, Image.FORMAT_RGBA8, data)
	if draw_stars:
		for i in 160:  # soft anti-aliased pin-prick stars, fewer near the horizon
			var sx := rng.randi_range(1, w - 2)
			var sy := clampi(int(pow(rng.randf(), 1.7) * h * 0.8), 1, h - 2)
			var b := rng.randf_range(0.55, 0.95)
			var sc := Color(1.0, 0.95, 0.8)
			img.set_pixel(sx, sy, img.get_pixel(sx, sy).lerp(sc, b))
			for d: Vector2i in [Vector2i(-1, 0), Vector2i(1, 0), Vector2i(0, -1), Vector2i(0, 1)]:
				var qx := sx + d.x
				var qy := sy + d.y
				img.set_pixel(qx, qy, img.get_pixel(qx, qy).lerp(sc, b * 0.35))
	img.generate_mipmaps()
	return ImageTexture.create_from_image(img)


# ------------------------------------------------------------------ spacing + overlap / occlusion checks
## witch_candy v3 (user: "물체랑 사람들끼리 자꾸 겹치잖아", "다른 집들로 인해 시야가 안가리면 좋겠어"). Opt-in per tale:
##  - `spacing`: every standing actor has a ground footprint (radius ~ a quarter of its height); actors that stand
##    (not walking, not lifted, not driven by the tale) are eased apart from each other and out of set-piece bases.
##  - `overlap_check`: every 0.2 s logs `OVERLAP <t> <a> <b> <kind> <amount>` for footprints that intersect (actor /
##    actor, actor / set piece base line) and `OCCLUDE <t> <subject> <by> <frac>` when something nearer the camera
##    covers more than 35 % of a visible actor's screen box (the speaker / subject must stay in view). Each pair is
##    printed when it starts; `OVERLAP_COUNT` / `OCCLUDE_COUNT` totals print at STORY_DONE time (runner). Pairs in
##    tale `overlap_ok` ([a, b] or [a, "*"]) are intentional contacts (holding the pot, sitting on the step).
var _overlap_t := 0.0
var overlap_live := {}
var talking := ""  ## the role whose quote is playing (runner, for the line-of-sight OCCLUDE check)
var _sight_on: bool = "--log-track" in OS.get_cmdline_user_args() or "--sight-check" in OS.get_cmdline_user_args() \
	or Engine.get_write_movie_path() != ""
var _sight_t := 0
var _sight_prev := {}
var _occlude_streak := {}
var overlap_count := 0
var occlude_count := 0
## run totals over every page (wolf_goats 2026-11-23: the per-stage counts only covered the last page in the summary)
static var run_overlaps := 0
static var run_occludes := 0
var no_spacing: Array = []  ## roles the tale moves itself (glides): the solver leaves them alone
## Story props a tale handler makes itself (wolf_goats 2026-11-23, user rule "no overlaps" covers fx props too): name ->
## {node, r (footprint radius), h (height)}. The overlap check tests each resting prop against the actors (footprints),
## the set pieces (a prop standing inside a house / tree card) and as an occluder of the actors.
var props: Dictionary = {}


func register_prop(nm: String, node: Node3D, r: float, h: float) -> void:
	props[nm] = {"node": node, "r": r, "h": h}


func unregister_prop(nm: String) -> void:
	props.erase(nm)


func _prop_live(nm: String) -> bool:
	var q: Dictionary = props[nm]
	var n: Variant = q["node"]
	if n == null or not is_instance_valid(n) or not (n as Node3D).is_visible_in_tree():
		return false
	return not (n as Node3D).has_meta("moving")


func actor_radius(a: StoryActor) -> float:
	return a.puppet.height * 0.22


func _ok_pair(a: String, b: String) -> bool:
	for q: Array in tale.get("overlap_ok", []):
		if (str(q[0]) == a and (str(q[1]) == b or str(q[1]) == "*")) or (str(q[0]) == b and (str(q[1]) == a or str(q[1]) == "*")):
			return true
	return false


func _piece_dist(sp: SetPiece, p: Vector3) -> float:
	var r := sp.global_transform.basis.x.normalized()
	var d := p - sp.global_position
	d.y = 0.0
	var along := clampf(d.dot(r), -sp.width * 0.5, sp.width * 0.5)
	return (d - r * along).length()


func _standing(a: StoryActor) -> bool:
	return a.pop_target > 0.5 and a.visible and not a.moving() and a.lift < 0.01 and not no_spacing.has(a.role) \
		and not a.has_meta("inside")


func _solid_piece(sp: SetPiece) -> bool:
	return sp.visible and sp.shown > 0 and not sp.flat and not sp.piece_name.begins_with("lights_") \
		and not sp.has_meta("inside_only") and not str(sp.piece_name).contains("_st") and sp.height > 0.08


func _spacing_step(dt: float) -> void:
	var list: Array = []
	for r in actors:
		var a: StoryActor = actors[r]
		if a.pop_target > 0.5 and a.visible:
			list.append(a)
	for i in list.size():
		var a: StoryActor = list[i]
		if not _standing(a):
			continue
		var push := Vector3.ZERO
		for j in list.size():
			if i == j:
				continue
			var b: StoryActor = list[j]
			var d := a.global_position - b.global_position
			d.y = 0.0
			var need := actor_radius(a) + actor_radius(b)
			if d.length() < need and not _ok_pair(a.role, b.role):
				push += (d.normalized() if d.length() > 1e-4 else dir_vec("right")) * (need - d.length())
		for k in sets:
			var sp: SetPiece = sets[k]
			if not _solid_piece(sp) or _ok_pair(a.role, sp.piece_name):
				continue
			var dd := _piece_dist(sp, a.global_position)
			var need2 := actor_radius(a) + 0.02
			if dd < need2:
				var t := sp.global_transform.basis.z.normalized()
				var side := signf((a.global_position - sp.global_position).dot(t))
				push += t * (side if side != 0.0 else 1.0) * (need2 - dd)
		if push.length() > 1e-4:
			var q := a.global_position + push * minf(1.0, dt * 4.0)
			q.y = world.ground.surface_y(Vector2(q.x, q.z))
			a.nudge(q)


## The house (set name) whose box holds point p, "" outside every house.
func house_of(p: Vector3) -> String:
	for k in sets:
		var sp: SetPiece = sets[k]
		if sp.building and sp.visible and sp.shown > 0 and sp.building.room_at(p):  # a kit building's room (rapunzel)
			return str(k)
		if sp.box == null or not sp.enterable:
			continue
		var l := sp.global_transform.affine_inverse() * p
		if l.z < 0.02 and l.z > -1.2 and absf(l.x) < sp.width * 0.5:
			return str(k)
	return ""


func _screen_box(pts: Array, edges: Array = []) -> Rect2:
	if pts.is_empty():
		return Rect2()
	var cam := camera()
	var origin := cam.global_position
	var fwd := -cam.global_transform.basis.z.normalized()
	var near_d := maxf(cam.near, 0.02)
	var dz := PackedFloat32Array()
	dz.resize(pts.size())
	var any_behind := false
	var any_front := false
	for i in pts.size():
		var d := ((pts[i] as Vector3) - origin).dot(fwd)
		dz[i] = d
		if d < near_d:
			any_behind = true
		else:
			any_front = true
	if not any_front:
		return Rect2()
	var proj: Array[Vector3] = []
	for i in pts.size():
		if dz[i] >= near_d:
			proj.append(pts[i] as Vector3)
	if any_behind:
		if not edges.is_empty():
			for e: Array in edges:
				var i0 := int(e[0])
				var i1 := int(e[1])
				var d0 := dz[i0]
				var d1 := dz[i1]
				if (d0 >= near_d) != (d1 >= near_d):
					var t := (near_d - d0) / (d1 - d0)
					proj.append((pts[i0] as Vector3).lerp(pts[i1] as Vector3, t))
		elif pts.size() <= 8:
			for i in pts.size():
				for j in range(i + 1, pts.size()):
					var d0 := dz[i]
					var d1 := dz[j]
					if (d0 >= near_d) != (d1 >= near_d):
						var t := (near_d - d0) / (d1 - d0)
						proj.append((pts[i] as Vector3).lerp(pts[j] as Vector3, t))
	if proj.is_empty():
		return Rect2()
	var r := Rect2(cam.unproject_position(proj[0]), Vector2.ZERO)
	for i in range(1, proj.size()):
		r = r.expand(cam.unproject_position(proj[i]))
	return r


func _actor_box(a: StoryActor) -> Rect2:
	var cr := camera().global_transform.basis.x
	var w := a.puppet.height * 0.42
	# the upper 60 % (head and body): legs behind a pot or a fence are fine, a hidden face is not
	var b := a.global_position + Vector3.UP * (a.hop + a.lift + a.puppet.height * 0.4)
	return _screen_box([b - cr * w * 0.5, b + cr * w * 0.5, b + Vector3.UP * a.puppet.height * 0.6 - cr * w * 0.5,
		b + Vector3.UP * a.puppet.height * 0.6 + cr * w * 0.5])


## SPEAKER_OFF check (runner): is the cast member who speaks `speaker` (a caption speaker id: a role, a role without
## its underscore — "piga" → pig_a —, a sky hanger, or the walker) in the frame and not hidden behind a set piece?
## Returns "" when visible, else why not ("off", "behind", "hidden", "occluded:<piece>"); "?" when nobody matches.
func speaker_state(speaker: String) -> String:
	var role := ""
	for r in actors:
		if str(r) == speaker or str(r).replace("_", "") == speaker:
			role = str(r)
	var cam := camera()
	var vs := get_viewport().get_visible_rect().size
	var screen := Rect2(vs * Vector2(0.02, 0.02), vs * Vector2(0.96, 0.96))
	var stand_in: Variant = handler.speaker_point(speaker) if handler else null
	if role == "" or (stand_in != null and (not (actors[role] as StoryActor).visible or (actors[role] as StoryActor).pop_s < 0.5)):
		var pt: Variant = stand_in
		if pt == null and hangers.has(speaker):
			pt = _target_point(speaker)
		elif pt == null and has_walker:
			pt = _target_point(walker_role)  # the walker's page: the one person in it
		if pt == null:
			return "?"
		if cam.is_position_behind(pt):
			return "behind"
		return "" if screen.has_point(cam.unproject_position(pt)) else "off"
	var a: StoryActor = actors[role]
	if not a.visible or a.pop_s < 0.5:
		return "hidden"
	if a.has_meta("inside"):  # answering from inside: the face at the window / door must be in the frame
		var c := a.centre()
		if cam.is_position_behind(c):
			return "behind"
		return "" if screen.has_point(cam.unproject_position(c)) else "off"
	var ab := _actor_box(a)
	if ab.size.x <= 1.0:
		return "behind"
	var inside := ab.intersection(screen).get_area() / maxf(ab.get_area(), 1.0)
	if inside < 0.5:
		return "off"
	var cam_house := house_of(cam.global_position)
	var a_house := house_of(a.global_position)
	if a_house != cam_house and a_house != "":
		var hs: SetPiece = sets[a_house]
		if hs.walls == null or hs.walls.visible:  # inside a house whose front stands between us
			return "occluded:wall"
	var ad := cam.global_position.distance_to(a.global_position)
	for k in sets:
		var sp: SetPiece = sets[k]
		if not _solid_piece(sp) or sp.walls and not sp.walls.visible or str(k) == cam_house:
			continue
		if house_of(sp.global_position) != cam_house:
			continue
		var rr := sp.global_transform.basis.x.normalized()
		var off := a.global_position - sp.global_position
		var near := sp.global_position + rr * clampf(off.dot(rr), -sp.width * 0.5, sp.width * 0.5)
		if cam.global_position.distance_to(near) > ad - 0.08:
			continue
		if ab.intersection(_piece_box(sp)).get_area() / maxf(ab.get_area(), 1.0) > 0.6:  # most of the head and body
			return "occluded:" + sp.piece_name
	return ""


## Where the speaker is on screen (for the SPEAKER_OFF log line): "x,y" of its centre in frame fractions.
func speaker_where(speaker: String) -> String:
	for r in actors:
		if str(r) == speaker or str(r).replace("_", "") == speaker:
			var c := (actors[r] as StoryActor).centre()
			var cam := camera()
			if cam.is_position_behind(c):
				return "behind"
			var q := cam.unproject_position(c) / get_viewport().get_visible_rect().size
			return "%.2f,%.2f" % [q.x, q.y]
	return "-"


func _piece_height(sp: SetPiece) -> float:
	if sp.shown <= 0:
		return 0.0
	if not sp.bands.is_empty() and sp.shown < sp.bands.size():
		var top := 0.0
		for k in mini(sp.shown, sp.band_cards.size()):
			var root := sp.bands[k].get_parent() as Node3D
			var c := sp.band_cards[k]
			if root and c:
				top = maxf(top, root.position.y + c.position.y + c.height)
		return top if top > 0.0 else sp.height * float(sp.shown) / float(sp.bands.size())
	return sp.height


func _building_bounds(sp: SetPiece) -> AABB:
	if sp.building_aabb.size.x > 0.0:
		return sp.building_aabb
	return AABB(Vector3(-sp.width * 0.5, 0.0, -sp.width * 0.5), Vector3(sp.width, sp.height, sp.width))


func _piece_box(sp: SetPiece) -> Rect2:
	var r := sp.global_transform.basis.x.normalized() * sp.width * 0.5
	var b := sp.global_position
	var h := Vector3.UP * _piece_height(sp) * 0.92
	return _screen_box([b - r, b + r, b - r + h, b + r + h])


func _piece_screen_box(sp: SetPiece) -> Rect2:
	if sp.body != null and (sp.box == null or sp.box.visible):
		var poly: Array = sp.body.spec.get("poly", [])
		if not poly.is_empty():
			var pts: Array = []
			var edges: Array = []
			var xf := sp.body.global_transform
			var d := sp.body.depth
			var n := poly.size()
			for i in n:
				var pt: Array = poly[i]
				var l := sp.body.to_local_px(Vector2(float(pt[0]), float(pt[1])))
				var ly := maxf(l.y, 0.0)
				pts.append(xf * Vector3(l.x, ly, 0.0))
				pts.append(xf * Vector3(l.x, ly, -d))
				var nxt := (i + 1) % n
				edges.append([2 * i, 2 * nxt])
				edges.append([2 * i + 1, 2 * nxt + 1])
				edges.append([2 * i, 2 * i + 1])
			return _screen_box(pts, edges)
	elif sp.building != null:
		var bb := _building_bounds(sp)
		var xf := sp.global_transform
		var p0 := bb.position
		var p1 := bb.end
		var pts := [
			xf * Vector3(p0.x, p0.y, p0.z), xf * Vector3(p1.x, p0.y, p0.z),
			xf * Vector3(p1.x, p1.y, p0.z), xf * Vector3(p0.x, p1.y, p0.z),
			xf * Vector3(p0.x, p0.y, p1.z), xf * Vector3(p1.x, p0.y, p1.z),
			xf * Vector3(p1.x, p1.y, p1.z), xf * Vector3(p0.x, p1.y, p1.z),
		]
		const BOX_EDGES := [
			[0, 1], [1, 2], [2, 3], [3, 0],
			[4, 5], [5, 6], [6, 7], [7, 4],
			[0, 4], [1, 5], [2, 6], [3, 7],
		]
		return _screen_box(pts, BOX_EDGES)
	return _piece_box(sp)


func _actor_occlude_box(b: StoryActor) -> Rect2:
	var cr := camera().global_transform.basis.x.normalized()
	var bw := b.puppet.height * 0.42
	var raw_bd: Variant = b.puppet.get("_body")
	if is_instance_valid(raw_bd) and raw_bd is PaperCard:
		var bd := raw_bd as PaperCard
		if bd.texture:
			var ts := bd.texture.get_size()
			bw = maxf(bw, bd.height * ts.x / maxf(ts.y, 1.0))
	var base := b.global_position + Vector3.UP * (b.hop + b.lift)
	var top := base + Vector3.UP * (b.puppet.height * b.pop_s)
	return _screen_box([base - cr * bw * 0.5, base + cr * bw * 0.5, top - cr * bw * 0.5, top + cr * bw * 0.5])


func _walker_box(wp: Vector3, wh: float) -> Rect2:
	var cr := camera().global_transform.basis.x
	var w := trav_h * 0.42
	var b := wp + Vector3.UP * wh * 0.4
	return _screen_box([b - cr * w * 0.5, b + cr * w * 0.5, b + Vector3.UP * wh * 0.6 - cr * w * 0.5,
		b + Vector3.UP * wh * 0.6 + cr * w * 0.5])


func _set_occludes_subject(cam: Camera3D, sp: SetPiece, pos: Vector3, centre: Vector3, h: float, ab: Rect2, ad: float) -> float:
	if sp.shown <= 0:
		return 0.0
	if sp._cut > 0.3 and sp.box == null:
		return 0.0
	if sp.has_door() and sp.door_open_amount() > 0.3 and absf(sp.door_offset(pos)) < sp.door_half_width() + 0.06:
		if (sp.global_transform.affine_inverse() * pos).z > -0.15:
			return 0.0
	if (sp.body != null and (sp.box == null or sp.box.visible)) or sp.building != null:
		var box_aabb: AABB
		if sp.body != null and (sp.box == null or sp.box.visible):
			var d := sp.body.depth
			box_aabb = AABB(Vector3(-sp.width * 0.5, 0.0, -d), Vector3(sp.width, sp.height * 0.96, d))
		else:
			var bb := _building_bounds(sp)
			box_aabb = AABB(bb.position, Vector3(bb.size.x, bb.size.y * 0.96, bb.size.z))
		var inv := sp.global_transform.affine_inverse()
		var l_c := inv * cam.global_position
		var cr := cam.global_transform.basis.x.normalized() * (h * 0.16)
		var any_hit := false
		for pt: Vector3 in [centre, centre - cr, centre + cr]:
			var hit: Variant = box_aabb.intersects_segment(l_c, inv * pt)
			if hit != null and cam.global_position.distance_to(sp.global_transform * (hit as Vector3)) < ad - 0.08:
				any_hit = true
				break
		if not any_hit:
			return 0.0
		var ov := ab.intersection(_piece_screen_box(sp))
		var frac := ov.get_area() / maxf(ab.get_area(), 1.0)
		return snappedf(frac, 0.01) if frac > 0.35 else 0.0
	var rr := sp.global_transform.basis.x.normalized()
	var off := pos - sp.global_position
	var near := sp.global_position + rr * clampf(off.dot(rr), -sp.width * 0.5, sp.width * 0.5)
	if cam.global_position.distance_to(near) > ad - 0.08:
		return 0.0
	var ov2 := ab.intersection(_piece_box(sp))
	var frac2 := ov2.get_area() / maxf(ab.get_area(), 1.0)
	return snappedf(frac2, 0.01) if frac2 > 0.35 else 0.0


func _overlap_check() -> void:
	var cam := camera()
	var vs := get_viewport().get_visible_rect().size
	var screen := Rect2(Vector2.ZERO, vs)
	var now := {}
	var occl_cand := {}
	var vis: Array = []
	var cam_house := house_of(cam.global_position) if camera_inside != "" else ""
	for r in actors:
		var a: StoryActor = actors[r]
		if a.pop_s > 0.5 and a.visible and not a.has_meta("inside"):
			vis.append(a)
	var walker_on := has_walker and trav_s > 0.5 and world.puppet != null and world.puppet.visible
	var wp := traveller_pos() + Vector3(0, hop - sink + ground_dy, 0) if walker_on else Vector3.ZERO
	var wr := trav_h * 0.22
	var wh := trav_h * trav_s
	for i in vis.size():
		var a: StoryActor = vis[i]
		for j in range(i + 1, vis.size()):
			var b: StoryActor = vis[j]
			var d := a.global_position - b.global_position
			d.y = 0.0
			var need := (actor_radius(a) + actor_radius(b)) * 0.8
			# climbers one above the other on a rope / trunk (moved by global y, lift 0) are not one footprint
			var dyh := absf(a.global_position.y - b.global_position.y) < 0.6 * minf(a.puppet.height, b.puppet.height)
			if d.length() < need and absf(a.lift - b.lift) < 0.1 and dyh and not _ok_pair(a.role, b.role):
				now["OVERLAP %s %s actor" % [a.role, b.role]] = snappedf(1.0 - d.length() / need, 0.01)
		for k in sets:
			var sp: SetPiece = sets[k]
			if not _solid_piece(sp) or _ok_pair(a.role, sp.piece_name) or a.lift > 0.05:
				continue
			var dd := _piece_dist(sp, a.global_position)
			if sp.has_door() and absf(sp.door_offset(a.global_position)) < sp.door_half_width():
				continue  # walking through an open doorway is not an overlap
			if dd < actor_radius(a) * 0.7:
				now["OVERLAP %s %s card" % [a.role, sp.piece_name]] = snappedf(1.0 - dd / (actor_radius(a) * 0.7), 0.01)
		# occlusion: something nearer the camera covering this actor on screen (only what the camera can see: inside a
		# house the room, outside everything but the rooms)
		if house_of(a.global_position) != cam_house:
			continue
		var ab := _actor_box(a)
		if ab.size.x <= 1.0 or not ab.intersects(screen):
			continue
		var ad := cam.global_position.distance_to(a.global_position)
		var area := ab.get_area()
		for b: StoryActor in vis:
			if b == a or house_of(b.global_position) != cam_house or _ok_pair(a.role, b.role):
				continue
			var bd := cam.global_position.distance_to(b.global_position)
			if bd >= ad - 0.12:
				continue
			var bb := _actor_occlude_box(b)
			if bb.size.x <= 1.0:
				continue
			var ov_frac := ab.intersection(bb).get_area() / maxf(area, 1.0)
			if ov_frac > 0.45:
				occl_cand["OCCLUDE %s %s" % [a.role, b.role]] = snappedf(ov_frac, 0.01)
		for k in sets:
			var sp: SetPiece = sets[k]
			if not _solid_piece(sp) or (sp.walls and not sp.walls.visible) or str(k) == cam_house or _ok_pair(a.role, sp.piece_name):
				continue
			if house_of(sp.global_position) != cam_house:
				continue
			var frac := _set_occludes_subject(cam, sp, a.global_position, a.centre(), a.puppet.height, ab, ad)
			if frac > 0.0:
				now["OCCLUDE %s %s" % [a.role, sp.piece_name]] = frac
	if walker_on:
		for a: StoryActor in vis:
			var d := wp - a.global_position
			d.y = 0.0
			var need := (wr + actor_radius(a)) * 0.8
			if d.length() < need and absf(hop - sink + ground_dy - a.lift) < 0.1 and not _ok_pair(walker_role, a.role):
				now["OVERLAP %s %s actor" % [walker_role, a.role]] = snappedf(1.0 - d.length() / need, 0.01)
		for k in sets:
			var sp: SetPiece = sets[k]
			if not _solid_piece(sp) or _ok_pair(walker_role, sp.piece_name):
				continue
			var dd := _piece_dist(sp, wp)
			if sp.has_door() and absf(sp.door_offset(wp)) < sp.door_half_width():
				continue
			if dd < wr * 0.7:
				now["OVERLAP %s %s card" % [walker_role, sp.piece_name]] = snappedf(1.0 - dd / (wr * 0.7), 0.01)
		if house_of(wp) == cam_house:
			var wb := _walker_box(wp, wh)
			if wb.size.x > 1.0 and wb.intersects(screen):
				var wd := cam.global_position.distance_to(wp)
				var wc := wp + Vector3.UP * wh * 0.55
				for k in sets:
					var sp: SetPiece = sets[k]
					if not _solid_piece(sp) or (sp.walls and not sp.walls.visible) or str(k) == cam_house or _ok_pair(walker_role, sp.piece_name):
						continue
					if house_of(sp.global_position) != cam_house:
						continue
					var frac := _set_occludes_subject(cam, sp, wp, wc, trav_h, wb, wd)
					if frac > 0.0:
						now["OCCLUDE %s %s" % [walker_role, sp.piece_name]] = frac
	for okey in occl_cand:
		_occlude_streak[okey] = int(_occlude_streak.get(okey, 0)) + 1
		if int(_occlude_streak[okey]) >= 2 and not now.has(okey):
			now[okey] = occl_cand[okey]
	for okey in _occlude_streak.keys():
		if not occl_cand.has(okey):
			_occlude_streak.erase(okey)
	# line of sight (wave 1): template lawn cards, roofs / house bodies, other actors' figures and props crossing the
	# rays to a MOVING or SPEAKING actor's head and body (SightCheck). Only in gate runs (--log-track / movie maker):
	# it costs a few ms per check. A blocker must hold for two checks in a row (0.4 s) to count.
	if _sight_on:
		_sight_t += 1
		var cand := {}
		if _sight_t % 2 == 0:
			for a: StoryActor in vis:
				if not (a.moving() or (talking != "" and (a.role == talking or a.role.replace("_", "") == talking))):
					continue
				if house_of(a.global_position) != cam_house:
					continue
				var ab3 := _actor_box(a)
				if ab3.size.x <= 1.0 or ab3.intersection(screen).get_area() < 0.5 * ab3.get_area():
					continue  # off the frame: MOTION_FLAG off_frame / SPEAKER_OFF report that
				var hid := SightCheck.hidden(self, cam, a, world)
				for bn: String in hid:
					var who := bn.get_slice(":", 1) if bn.contains(":") else bn
					if float(hid[bn]) >= 0.45 and not _ok_pair(a.role, bn) and not _ok_pair(a.role, who):
						var key := "OCCLUDE %s %s" % [a.role, bn]
						cand[key] = snappedf(float(hid[bn]), 0.01)
			if walker_on and (walking() or strolling_on or (talking != "" and (walker_role == talking or walker_role.replace("_", "") == talking))) and house_of(wp) == cam_house:
				var wb3 := _walker_box(wp, wh)
				if wb3.size.x > 1.0 and wb3.intersection(screen).get_area() >= 0.5 * wb3.get_area():
					var hid_w := SightCheck.hidden_at(self, cam, wp, wh, world.walker, world)
					for bn: String in hid_w:
						var who := bn.get_slice(":", 1) if bn.contains(":") else bn
						if float(hid_w[bn]) >= 0.45 and not _ok_pair(walker_role, bn) and not _ok_pair(walker_role, who):
							var key := "OCCLUDE %s %s" % [walker_role, bn]
							cand[key] = snappedf(float(hid_w[bn]), 0.01)
			for key in cand:
				if _sight_prev.has(key) and not now.has(key):
					now[key] = cand[key]
			_sight_prev = cand
		else:
			for key in _sight_prev:  # keep confirmed blockers live between sight passes (no re-print)
				if overlap_live.has(key):
					now[key] = _sight_prev[key]
	# handler props (wolf_goats): resting story props vs actors, vs set pieces, and props hiding an actor
	for nm in props.keys():
		if not _prop_live(nm):
			continue
		var q: Dictionary = props[nm]
		var pn: Node3D = q["node"]
		var pp := pn.global_position
		var pr := float(q["r"])
		if walker_on:
			var dw := wp - pp
			dw.y = 0.0
			var needw := wr * 0.7 + pr
			if dw.length() < needw and absf(wp.y - pp.y) < trav_h and not _ok_pair(walker_role, nm):
				now["OVERLAP %s %s prop" % [walker_role, nm]] = snappedf(1.0 - dw.length() / needw, 0.01)
			if house_of(wp) == cam_house and house_of(pp) == cam_house:
				var wb2 := _walker_box(wp, wh)
				if wb2.size.x > 1.0 and wb2.intersects(screen) and cam.global_position.distance_to(pp) <= cam.global_position.distance_to(wp) - 0.08:
					var crw := cam.global_transform.basis.x.normalized() * pr
					var pbw := _screen_box([pp - crw, pp + crw, pp - crw + Vector3.UP * float(q["h"]), pp + crw + Vector3.UP * float(q["h"])])
					if wb2.intersection(pbw).get_area() / maxf(wb2.get_area(), 1.0) > 0.35 and not _ok_pair(walker_role, nm):
						now["OCCLUDE %s %s" % [walker_role, nm]] = snappedf(wb2.intersection(pbw).get_area() / wb2.get_area(), 0.01)
		for a: StoryActor in vis:
			var d2 := a.global_position - pp
			d2.y = 0.0
			var need3 := actor_radius(a) * 0.7 + pr
			if d2.length() < need3 and absf(a.global_position.y + a.lift - pp.y) < a.puppet.height and not _ok_pair(a.role, nm):
				now["OVERLAP %s %s prop" % [a.role, nm]] = snappedf(1.0 - d2.length() / need3, 0.01)
			if house_of(a.global_position) != cam_house or house_of(pp) != cam_house:
				continue
			var ab2 := _actor_box(a)
			if ab2.size.x <= 1.0 or not ab2.intersects(screen):
				continue
			if cam.global_position.distance_to(pp) > cam.global_position.distance_to(a.global_position) - 0.08:
				continue
			var cr2 := cam.global_transform.basis.x.normalized() * pr
			var pb := _screen_box([pp - cr2, pp + cr2, pp - cr2 + Vector3.UP * float(q["h"]), pp + cr2 + Vector3.UP * float(q["h"])])
			if ab2.intersection(pb).get_area() / maxf(ab2.get_area(), 1.0) > 0.35 and not _ok_pair(a.role, nm):
				now["OCCLUDE %s %s" % [a.role, nm]] = snappedf(ab2.intersection(pb).get_area() / ab2.get_area(), 0.01)
		for k in sets:
			var sp: SetPiece = sets[k]
			if not _solid_piece(sp) or _ok_pair(nm, sp.piece_name):
				continue
			if _piece_dist(sp, pp) < pr * 0.7 and pp.y - sp.global_position.y < sp.height:
				now["OVERLAP %s %s prop_card" % [nm, sp.piece_name]] = snappedf(1.0 - _piece_dist(sp, pp) / (pr * 0.7), 0.01)
	for key in now:
		if not overlap_live.has(key):
			print(key, " t=", snappedf(_t, 0.01), " amt=", now[key], " shot=", shot)
			if OS.get_cmdline_user_args().has("--overlap-debug"):
				for r2 in actors:
					var a2: StoryActor = actors[r2]
					print("   ", r2, " ", a2.global_position.snapped(Vector3.ONE * 0.01), " moving=", a2.moving(), " path=", a2._path.size())
			if str(key).begins_with("OCCLUDE"):
				occlude_count += 1
				run_occludes += 1
			else:
				overlap_count += 1
				run_overlaps += 1
	overlap_live = now


func _set_glow(sp: SetPiece, g: float) -> void:
	var cards: Array = sp.band_cards.duplicate()
	if sp.card:
		cards.append(sp.card)
	for c: PaperCard in cards:
		_glow_pending.append([c, g])  # the card builds its materials deferred: applied in _process once they exist
	if sp.body:
		sp.body.set_glow(g)


var _glow_pending: Array = []
var _lights: Array = []  ## [OmniLight3D, base energy, flicker]


func _add_light(sp: SetPiece, cfg: Array) -> void:
	var o := OmniLight3D.new()
	o.light_energy = float(cfg[0])
	o.omni_range = float(cfg[2]) if cfg.size() > 2 else 0.8
	o.light_color = Color(str(cfg[3])) if cfg.size() > 3 else Color(1.0, 0.68, 0.36)
	o.omni_attenuation = 1.4
	o.shadow_enabled = false
	o.position = Vector3(0, float(cfg[1]) if cfg.size() > 1 else 0.2, 0.08)
	sp.add_child(o)
	_lights.append([o, o.light_energy, bool(cfg[4]) if cfg.size() > 4 else false])


## Set pieces stand on the meadow: none on the road (path felt) or in the stream. Samples the card's base line (and a
## little in front / behind it) and prints SET_CHECK <name> road=<n> water=<n> (both 0 = clear); `allow_road`
## in the set entry for pieces meant to sit on the road (none so far).
func _check_footprint(sp: SetPiece, e: Dictionary) -> void:
	var g := world.ground
	# sky / floating pieces (clouds, hanging lanterns, a flue lifted over the hearth) have no footprint on the page:
	# gate audit v1 counted sunmoon's 22 cloud bands as "on the road". Set entry `sky`, catalog tags sky / cloud /
	# hanging, or a base lifted clear of the ground.
	var ce := atlas_entry(str(e.get("card", "")))
	var tags: Array = ce.get("tags", [])
	var elev := sp.global_position.y - g.surface_y(Vector2(sp.global_position.x, sp.global_position.z))
	if e.get("sky", false) or bool(ce.get("hanging", false)) or tags.has("sky") or tags.has("cloud") or elev > 0.12:
		print("SET_CHECK ", sp.piece_name, " road=0 water=0 sky=1 elev=", snappedf(elev, 0.01))
		return
	var allow_road := bool(e.get("allow_road", false))
	var allow_water := bool(e.get("allow_water", false))
	var r: Vector3 = sp.global_transform.basis.x.normalized()  # the piece's own base line (turned pieces too)
	var t: Vector3 = sp.global_transform.basis.z.normalized()
	var road := 0
	var water := 0
	if not (allow_road and allow_water):
		for i in 9:
			for dz: float in [-0.04, 0.0, 0.06]:
				var q3: Vector3 = sp.global_position + r * (float(i) / 8.0 - 0.5) * sp.width * 0.92 + t * dz
				var q := Vector2(q3.x, q3.z)
				if not allow_road and g.path_distance(q) < 0.0:
					road += 1
				if not allow_water and g.stream_distance(q) < 0.0:
					water += 1
	print("SET_CHECK ", sp.piece_name, " road=", road, " water=", water, " w=", snappedf(sp.width, 0.01))
	if road > 0 or water > 0:
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
	for hc: Dictionary in world.house_cards:
		if hc.get("hinge") != null:
			continue
		var raw: Variant = hc.get("body_node")
		if not is_instance_valid(raw) or not (raw is Node3D):
			continue
		var bn := raw as Node3D
		if not bn.visible:
			continue
		var o: Vector3 = hc["pos"]
		if Vector2(o.x - p.x, o.z - p.z).length() < r + float(hc.get("w", 0.5)) * 0.5:
			bn.visible = false
			hidden.append(o)
	_hide_contact_blobs(hidden)


func set_piece(nm: String) -> SetPiece:
	if sets.has(nm):
		return sets[nm]
	for k in sets:
		if (sets[k] as SetPiece).id == nm:
			return sets[k]
	return null


## spread.built: set pieces already finished at this beat (a story started mid-page with --beat, or a page reached
## by a jump): all their bands stand. Standing pieces stay as they are (a house the wolf blew away is not rebuilt:
## list only what stands at this beat).
func _apply_built(names: Array, snap_now: bool) -> void:
	for n in names:
		var sp := set_piece(str(n))
		if sp == null or sp.shown >= sp.band_count():
			continue
		sp.bands_up(sp.band_count(), 0.0, 0.0)
		if snap_now:
			for h in sp.wave_hinges():
				h.snap(true)


## enter {who: {role: pose}, at: {role: spot}}: those actors stand at their spots in those poses (first: snapped,
## they pop with the page); others step off the page unless `keep` lists them.
func _enter_cast(enter: Dictionary, first: bool) -> void:
	var who: Dictionary = enter.get("who", {})
	var at: Dictionary = enter.get("at", {})
	var inside: Dictionary = enter.get("inside", {})
	var keep: Array = enter.get("keep", [])
	for role in actors:
		var a: StoryActor = actors[role]
		if who.has(role):
			var p := str(who[role])
			var left := int(enter.get("left", {}).get(role, -1))
			var visible_now := a.pop_target > 0.5
			if first or not visible_now or at.has(role):
				a.place_at(spot_point(at.get(role, role if spots.has(role) else "anchor")))
				clear_inside(a)
			a.pose = p
			if left >= 0:
				a.facing_left = left == 1
			a.puppet.set_figure(p, a.facing_left and a.view_of(p) == "side", first or not visible_now)
			if inside.has(role):
				var ins: Array = inside[role]
				put_inside(str(role), str(ins[0]), int(ins[1]) if ins.size() > 1 else 0)
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


## At home (2026-11-18 user: "아기돼지들 집에 있어야하지 않겠니?"): the actor stands just behind the house's front
## wall at window i, raised so its eyes are at the window's middle; the die-cut window frames its face, the wall hides
## the rest. Speaking from inside it bobs (runner); when the house falls (huff) reveal_inside() brings it out.
func put_inside(role: String, house: String, win: int) -> void:
	var a := actor(role)
	var sp := set_piece(house)
	if a == null or sp == null:
		return
	if win < 0:  # inside but not at a window (two windows, three pigs): out of sight until the house falls / opens
		a.set_meta("inside", house)
		a.pop_delay = 0.0
		a.pop_target = 0.02
		return
	var peek := "peek_" + ("defiant" if a.pose in ["defiant", "tease"] else ("brave" if a.pose in ["brave", "proud", "calm"] and a.has_pose("peek_brave") else "scared"))
	var wb: Array = sp.window_box(win)
	if a.has_pose(peek) and not wb.is_empty():
		_peek_in(a, sp, wb, peek, house, win)
		return
	var ws: Array = sp.window_spot(win, dir_vec("toward"))
	a.place_at(ws[0])
	# a bigger face behind the window so it fills the opening (the wall hides the rest)
	a.puppet.scale = Vector3.ONE * INSIDE_SCALE
	a.lift = float(ws[1]) - a.puppet.height * 0.74 * INSIDE_SCALE
	a.set_meta("inside", house)
	# a small warm fill in front of the face, between it and the wall: the wall's own shadow made faces read as dark
	# blobs in the windows (no shadow from this light, so it only brightens the face)
	var lt := a.get_node_or_null("InsideFill") as OmniLight3D
	if lt == null:
		lt = OmniLight3D.new()
		lt.name = "InsideFill"
		lt.light_color = Color(1.0, 0.86, 0.66)
		lt.light_energy = 0.09
		lt.omni_range = 0.2
		lt.omni_attenuation = 1.2
		lt.shadow_enabled = false
		lt.light_specular = 0.0
		lt.top_level = true
		a.add_child(lt)
	lt.visible = true
	lt.global_position = a.global_position + Vector3(0, float(ws[1]), 0) + dir_vec("toward") * 0.045
	if a.view_of(a.pose) != "front":
		a.set_pose("calm")


## Peek figure (head + hands, cast `peek_*`) behind window `wb` = [sill point, width, height]: the head about 65 % of
## the opening's height, eyes above the sill, hands on it, the rest hidden by the wall; the same scale in every window
## and house (set by the opening's height, all openings are about the same size). A darker warm plane behind it.
## Shares: `share` actors in one window stand side by side (slot = index).
const PEEK_HEAD := 0.65
const PEEK_HEAD_FRAC := 0.78  ## head height / peek card height (hands below)


func _peek_in(a: StoryActor, sp: SetPiece, wb: Array, peek: String, house: String, win: int) -> void:
	a.pose = peek
	a.puppet.set_figure(peek, false, true)
	a.puppet.scale = Vector3.ONE
	var card_h := float(wb[2]) * PEEK_HEAD / PEEK_HEAD_FRAC
	var base_h: float = a.puppet.get("_body").height if a.puppet.get("_body") else a.puppet.height
	var k := card_h / maxf(base_h, 0.001)
	a.puppet.scale = Vector3.ONE * k
	var p: Vector3 = wb[0]
	p -= dir_vec("toward") * 0.045
	a.place_at(Vector3(p.x, sp.global_position.y, p.z))
	# hands on the sill: the card's bottom a little below the sill line (the wall hides it)
	a.lift = (p.y - sp.global_position.y) - card_h * 0.12
	a.set_meta("inside", house)
	a.set_meta("peek", true)
	a.idle_amount_set(0.0)
	sp.window_backs("dim")
	# a slight warm fill on the face (the wall's shadow falls on it), not a glow: the face keeps the scene's light
	var lt := a.get_node_or_null("InsideFill") as OmniLight3D
	if lt == null:
		lt = OmniLight3D.new()
		lt.name = "InsideFill"
		lt.light_color = Color(1.0, 0.86, 0.66)
		lt.shadow_enabled = false
		lt.light_specular = 0.0
		lt.top_level = true
		a.add_child(lt)
	lt.light_energy = 0.16
	lt.omni_range = 0.2
	lt.visible = true
	lt.global_position = p + Vector3(0, float(wb[2]) * 0.55, 0) + dir_vec("toward") * 0.09


const INSIDE_SCALE := 1.45


func clear_inside(a: StoryActor) -> void:
	a.remove_meta("inside")
	a.lift = 0.0
	a.puppet.scale = Vector3.ONE
	if a.has_meta("peek"):
		a.remove_meta("peek")
		a.idle_amount_set(1.0)
		if a.view_of(a.pose) == "front" and a.pose.begins_with("peek_"):
			a.pose = "scared"
			a.puppet.set_figure("scared", false, true)
	var lt := a.get_node_or_null("InsideFill") as Node3D
	if lt:
		lt.visible = false


## The house is gone: whoever was inside is out in the open where it stood, with a startled hop.
func reveal_inside(house: String, pose := "scared") -> void:
	for r in actors:
		var a: StoryActor = actors[r]
		if str(a.get_meta("inside", "")) != house:
			continue
		clear_inside(a)
		a.pop_target = 1.0
		a.place_at(a.global_position + dir_vec("toward") * 0.1)
		a.hop_v = 1.1
		a.set_pose(pose)


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
	_apply_built(sp.get("built", []), true)
	# sunmoon (2026-11-22): night falls on a page that opened by day (the third pass shares the road page with the
	# first two): build its night sky now, or the sky behind the hills stays the black backdrop
	if not (sp.get("sky", {}) as Dictionary).is_empty() and get_node_or_null("NightSky") == null:
		_build_sky(sp["sky"])
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
## Light presets (spread.light): "" day, "afternoon", "late" (warm late afternoon), "dusk", "night", "evening" (warm
## night, lit windows). Each = [key energy ×, key colour, fill ×, ambient ×, ambient colour, exposure ×, backdrop].
const LIGHTS := {
	"": [1.0, Color(1, 1, 1, 0), 1.0, 1.0, Color(1, 1, 1, 0), 1.0],
	"afternoon": [1.0, Color(1.0, 0.86, 0.66), 1.0, 0.95, Color(1, 1, 1, 0), 1.0],
	"late": [0.95, Color(1.0, 0.74, 0.48), 1.1, 0.9, Color(0.85, 0.75, 0.7), 0.97],
	"dusk": [0.8, Color(1.0, 0.6, 0.38), 1.5, 0.8, Color(0.55, 0.6, 0.85), 0.9],
	"night": [0.45, Color(0.55, 0.62, 1.0), 1.8, 0.6, Color(0.35, 0.42, 0.75), 0.78],
	"evening": [0.55, Color(1.0, 0.66, 0.45), 1.6, 0.7, Color(0.45, 0.45, 0.75), 0.85],
}
var _light_from: Array = []
var _light_to: Array = []


func _set_light(name: String, instant: bool) -> void:
	light = name
	var tgt: Array = LIGHTS.get(name, LIGHTS[""])
	_light_from = _light_cur()
	_light_to = tgt
	_light_t = 1.0
	_light_k = 0.0
	if SoundDirector.current and is_built:
		SoundDirector.current.light_changed()
	if instant:
		_light_k = 1.0
		_apply_light()


func _light_cur() -> Array:
	if _light_to.is_empty():
		return LIGHTS[""]
	var a: Array = _light_from
	var b: Array = _light_to
	var k := _light_k
	var out: Array = []
	for i in a.size():
		if a[i] is Color:
			out.append((a[i] as Color).lerp(b[i], k))
		else:
			out.append(lerpf(float(a[i]), float(b[i]), k))
	return out


func _apply_light() -> void:
	if _rig0.is_empty():
		return
	var rig := world.rig
	var L := _light_cur()
	var kc: Color = L[1]
	var ac: Color = L[4]
	rig.key.light_energy = float(_rig0["key_e"]) * float(L[0])
	rig.key.light_color = (_rig0["key_c"] as Color).lerp(Color(kc.r, kc.g, kc.b), kc.a)
	if rig.fill:
		rig.fill.light_energy = float(_rig0["fill_e"]) * float(L[2])
	if rig.environment:
		rig.environment.ambient_light_energy = float(_rig0["amb_e"]) * float(L[3])
		rig.environment.ambient_light_color = (_rig0["amb_c"] as Color).lerp(Color(ac.r, ac.g, ac.b), ac.a * 0.7)
		rig.environment.tonemap_exposure = float(_rig0["exp"]) * float(L[5])
		if tale.has("backdrop"):
			# the backdrop behind the far hills takes the haze colour (darker at night): an exposed edge never reads
			# as black sky
			var hz := rig.environment.fog_light_color
			var night := clampf((1.0 - float(L[5])) / 0.22, 0.0, 1.0)  # 0 by day .. 1 at night
			rig.environment.background_color = hz.lerp(Color(0.36, 0.44, 0.66), night * 0.75)
		var sky: Dictionary = (beat.get("spread", {}) as Dictionary).get("sky", {})
		if not sky.is_empty():  # a night sky (witch_candy): deep-blue backdrop, the depth haze turns night blue
			rig.environment.background_color = Color(str(sky.get("bg", "#0d1433")))
			rig.environment.fog_light_color = Color(str(sky.get("fog", "#1a2550")))
			rig.environment.fog_light_energy = float(sky.get("fog_energy", 0.7))


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
	if not is_inside_tree() or get_tree() == null:
		return
	await get_tree().process_frame  # SkyHanger builds its card in _ready
	if not is_inside_tree() or not is_instance_valid(h):
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
		var lines: Array = (beat.get("spread", {}) as Dictionary).get("sightlines", [])
		if lines.is_empty():
			for sh in _shots_used():
				await _clear_sightlines_here(keep_all, hidden, sh)
				await _slicer.tick()
		else:
			# one spread, many camera stations (a village): [shot, spot] or [shot, "road", spot_a, spot_b] (a tracking
			# shot along the road: stations every 0.5)
			var home_focus := _focus_goal
			for e: Array in lines:
				var pts: Array = []
				if e.size() >= 4 and str(e[1]) == "road":
					var rt := road_route(spot_point(e[2]), spot_point(e[3]))
					for i in range(0, rt.size(), 2):
						pts.append(rt[i])
				else:
					pts.append(spot_point(e[1]))
				for q: Vector3 in pts:
					_cam_anchor.global_position = q
					_sight_focus = q
					await _clear_sightlines_here(keep_all, hidden, str(e[0]))
					await _slicer.tick()
			_cam_anchor.global_position = home_focus
			_sight_focus = Vector3(INF, 0, INF)
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
			if _sight_focus.x < INF and Vector2(p.x - _sight_focus.x, p.z - _sight_focus.z).length() > 1.6:
				continue
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
	var cp := cam.global_position
	if world.batch != null:
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
				for hc: Dictionary in world.house_cards:
					if hc.get("hinge") != null:
						continue
					var raw: Variant = hc.get("body_node")
					if not is_instance_valid(raw) or not (raw is Node3D):
						continue
					var bn := raw as Node3D
					if not bn.visible:
						continue
					var o: Vector3 = hc["pos"]
					if Vector2(o.x - p.x, o.z - p.z).length() < 0.05:
						bn.visible = false
	var hidden_buildings: Array[Vector3] = []
	for hc: Dictionary in world.house_cards:
		if not hc.get("building", false) or hc.get("hinge") != null:
			continue
		var raw: Variant = hc.get("body_node")
		if not is_instance_valid(raw) or not (raw is Node3D):
			continue
		var bn := raw as Node3D
		if not bn.visible:
			continue
		var p: Vector3 = hc.get("pos", bn.global_position)
		var hh := maxf(float(hc.get("h", 1.0)), 0.001)
		var hw := float(hc.get("w", 1.0)) * 0.5
		var hide := Vector2(p.x - cp.x, p.z - cp.z).length() < 0.9 + hw
		if not hide and not (cam.is_position_behind(p) or cam.is_position_behind(p + Vector3(0, hh, 0))):
			var a := cam.unproject_position(p)
			var b := cam.unproject_position(p + Vector3(0, hh, 0))
			var ppu := absf(a.y - b.y) / hh
			var rr := Rect2(a.x - hw * ppu, b.y, hw * ppu * 2.0, a.y - b.y).abs()
			for sr in rects:
				if cp.distance_to(p) < float(sr[1]) and rr.intersects(sr[0]):
					hide = true
		if hide:
			bn.visible = false
			_statics_hidden += 1
			hidden_buildings.append(p)
	if not hidden_buildings.is_empty():
		_hide_contact_blobs(hidden_buildings)


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
	var end := 0.0
	if tale.get("pop_in", true):
		end = wave.pop(all, _origin, start)
	else:
		# witch_candy v6 (user: "어떤 건 서 있고 어떤 건 안 서 있고 ... 그냥 처음부터 서 있어도"): the scenery is
		# already standing when the page opens (no staggered wave); a house's body and its front stand together
		for h in all:
			h.snap(true)
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


## Camera shot on the template rig: "wide" (template view) | "story" | "close" | tale shots
## [distance, elevation°, focus height, fov, (yaw offset° from the template view)]. `at`: focus spot.
## opts (cam step): rate (glide speed, default 2.4: lower = a slower move, higher = a quicker one; the move's length
## comes from how far the view travels, see _begin_move), shake (amplitude°, decays), follow (role: tracking shot),
## cut (true: a hard cut, to `from` when given, else to the shot itself; only where a page turn hides it).
## `from` without `cut` no longer snaps (2026-11-22, user: "시점이 뚝뚝 끊기는거 별로에요"): the glide starts where
## the camera is (a spread's opening `from` is applied under the page turn, see preset_open).
func shot_to(name: String, at: Variant = null, opts: Dictionary = {}) -> void:
	shot = name
	_cam = _wide.duplicate() if name == "wide" else (_shots[name] as Array).duplicate()
	if _cam.size() < 5:
		_cam.append(0.0)
	_cam_rate = float(opts.get("rate", 2.4))
	if opts.has("shake"):
		shake(float(opts["shake"]))
	_follow = null
	if opts.has("follow"):
		_follow = actor(str(opts["follow"]))
	if at != null and _cam_anchor:
		_focus_goal = spot_point(at)
	if bool(opts.get("cut", false)):
		var f: Array = _cam
		if opts.has("from") and _shots.has(str(opts["from"])):
			f = _shots[str(opts["from"])]
		_cut_to(f, _focus_goal if at != null else Vector3(INF, 0, 0))
	_begin_move(_cam_rate)


## Hard cut: the rig takes shot array `f` now (and the focus `at` unless INF), the glides restart from rest there.
func _cut_to(f: Array, at: Vector3) -> void:
	var rig := world.rig
	rig.distance = float(f[0])
	rig.elevation_deg = float(f[1])
	rig.focus_height = float(f[2])
	rig.fov = float(f[3])
	_yaw_off = float(f[4]) if f.size() > 4 else 0.0
	if at.x < INF and _cam_anchor:
		_cam_anchor.global_position = at
	_cs.clear()
	_cam_wrote.clear()
	_cs["yaw"] = [_yaw_off, 0.0, _yaw_off, 0.0]


## A spread opens: the beat's first camera step that asks for a `from` framing (a crane down from high) gets it now,
## while the page is still under the turning sheet, so the glide starts there with no visible cut.
func preset_open(b: Dictionary) -> void:
	for st: Dictionary in b.get("steps", []):
		if str(st.get("do", "")) != "cam":
			continue
		if st.has("from") and _shots.has(str(st["from"])) and _cam_anchor and not has_walker:
			var at := spot_point(st["at"]) if st.has("at") else _focus_goal
			_cam = (_shots[str(st["from"])] as Array).duplicate()
			if _cam.size() < 5:
				_cam.append(0.0)
			_focus_goal = at
			_cut_to(_cam, at)
		return


## Camera motion (2026-11-22, user: "시점이 뚝뚝 끊기는거 별로에요"): each shot parameter and the stage focus follow
## their goal through two critically damped springs in series, so a move eases in and out and a new goal mid-move
## bends the path with its velocity carried over (no frame starts, stops or turns at full speed). The length of a move
## comes from how far the view travels (CAM_MIN_S..CAM_MAX_S; a slow `rate` stretches it to CAM_SLOW_MAX_S, a quick
## one shortens it); once a move has had its time the focus tightens to a CAM_FOLLOW_S follow (tracked actors, props
## in flight). Yaw takes the short way round. The run log's CAM_JUMP / CAM_JERK check (story_runner) measures it.
const CAM_MIN_S := 0.8
const CAM_MAX_S := 2.5
const CAM_LONG_S := 4.2  ## the longest move a far traverse gets (peak speed kept under ~45°/s)
const CAM_SLOW_MAX_S := 6.0  ## a slow push-in a tale asks for (rate < 1)
const CAM_FOLLOW_S := 0.35
var _cs := {}  ## glide state per parameter: [value, velocity, pre-smoothed goal, its velocity]
var _cam_wrote := {}  ## what the glide last wrote (a value someone else set is taken over, at rest)
var _cam_w := 6.0  ## per-stage spring rate (1/s) of the current move
var _move_t := 0.0
var _move_d := 1.2


## Length of the move from the camera's state now to the shot goal: the view's travel in degrees (turn, tilt, zoom,
## lens, the focus shift seen from the camera) → 0.8–2.5 s (up to 3.5 s for a far traverse), scaled by the step's rate.
func _begin_move(rate: float) -> void:
	var rig := world.rig
	var d0 := maxf(rig.distance, 0.3)
	var dr := maxf(minf(d0, float(_cam[0])), 0.3)  # shifts seen from the nearer end of the move
	var yaw_g := float(_cam[4]) if _cam.size() > 4 else 0.0
	var dy := wrapf(yaw_g - _yaw_off, -180.0, 180.0) if not has_walker else 0.0
	var de := float(_cam[1]) - rig.elevation_deg
	var dz := 40.0 * absf(log(maxf(float(_cam[0]), 0.3) / d0))
	var df := float(_cam[3]) - rig.fov
	var dh := rad_to_deg((float(_cam[2]) - rig.focus_height) / dr)
	var dp := 0.0
	if _cam_anchor and not has_walker:
		dp = rad_to_deg(_cam_anchor.global_position.distance_to(_focus_goal) / dr)
	var mag := sqrt(dy * dy + de * de + dz * dz + df * df + dh * dh + dp * dp)
	var d := clampf(0.7 + mag / 30.0, CAM_MIN_S, CAM_MAX_S)  # peak speed ≈ 1.74·mag/d: under ~55°/s
	if rate > 2.4:
		d *= clampf(2.4 / rate, 0.85, 1.0)  # a quick move, never a whip
	elif rate > 0.0:
		d = maxf(d, minf(3.0 / rate, CAM_SLOW_MAX_S))
	d = maxf(d, minf(1.74 * mag / 45.0, CAM_LONG_S))  # a long way (out of a room to the street): longer, never a whip
	# a new shot mid-move never hurries the glide that is still under way (its speed carries into the new move)
	_move_d = maxf(maxf(d, CAM_MIN_S), minf(_move_d - _move_t, CAM_MAX_S))
	_move_t = 0.0
	_cam_w = 7.75 / _move_d  # two stages in series: ~95 % of the way at _move_d


## Seconds until the current move has gone `frac` of its time (0.85: nearly landed; the runner holds tap prompts
## that long, and a line after a quick move until it is well under way).
func cam_settle_left(frac := 0.85) -> float:
	return maxf(0.0, _move_d * frac - _move_t)


## One glide step of parameter `key` (current value `cur`, as found on the rig) toward `goal`.
func _glide(key: String, cur: float, goal: float, w: float, dt: float) -> float:
	var st: Array = _cs.get(key, [])
	if st.is_empty() or absf(cur - float(_cam_wrote.get(key, cur))) > 1e-4:
		st = [cur, 0.0, cur, 0.0]
		_cs[key] = st
	var e := exp(-w * dt)
	var x := float(st[2]) - goal
	var tmp := (float(st[3]) + w * x) * dt
	st[3] = (float(st[3]) - w * tmp) * e
	st[2] = goal + (x + tmp) * e
	x = float(st[0]) - float(st[2])
	tmp = (float(st[1]) + w * x) * dt
	st[1] = (float(st[1]) - w * tmp) * e
	st[0] = float(st[2]) + (x + tmp) * e
	return float(st[0])


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


var _walk_away_off := -1.0
var _walk_away_tilted := false


## Ending: the camera stops following and he walks off down the road.
func walk_away(dist: float) -> void:
	_walk_away_off = world.walker.offset
	_walk_away_tilted = false
	_cam_anchor = Node3D.new()
	_cam_anchor.top_level = true
	add_child(_cam_anchor)
	_cam_anchor.global_position = world.focus.global_position
	_focus_goal = _cam_anchor.global_position
	world.rig.focus_target = _cam_anchor
	follow_sky = false
	walk_by(dist)


func walker_in_frame() -> bool:
	var cam := camera()
	if cam == null or not has_walker:
		return false
	var foot := traveller_pos() + Vector3(0, hop - sink + ground_dy, 0)
	var head := foot + Vector3(0, trav_h * trav_s, 0)
	if cam.is_position_behind(foot) and cam.is_position_behind(head):
		return false
	var vs := get_viewport().get_visible_rect().size
	var fa := cam.unproject_position(foot)
	var fb := cam.unproject_position(head)
	var r := Rect2(fa, Vector2.ZERO).expand(fb)
	var w := maxf(r.size.y * 0.42, 4.0)
	var box := Rect2(r.get_center().x - w * 0.5, r.position.y, w, r.size.y)
	var scr := Rect2(Vector2.ZERO, vs)
	return box.intersection(scr).get_area() > box.get_area() * 0.15


func walk_stop() -> void:
	if not has_walker or world == null or world.walker == null:
		return
	world.walker.target_offset = world.walker.offset
	if "_moving" in world.walker:
		world.walker.set("_moving", false)


func walk_away_frame_sky() -> void:
	if _walk_away_tilted:
		return
	_walk_away_tilted = true
	_cam = [3.7, 9.5, 0.56, 21.5, 0.0]
	_begin_move(0.9)


func walk_away_back(fallback: float) -> float:
	if _walk_away_off >= 0.0 and has_walker and world and world.walker:
		return absf(world.walker.offset - _walk_away_off)
	return fallback


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
		# the part standing now (a house mid-build gets a ring around its walls so far, not its finished height)
		var b := cam.unproject_position(s.global_position + Vector3(0, maxf((s.centre().y - s.global_position.y) * 2.0, 0.12), 0))
		return maxf(70.0, a.distance_to(b) * 0.6)
	if handler:
		var r := handler.target_radius(target)
		if r > 0.0:
			return r
	return 80.0


## Which story target a screen point hits ("" for none). Kids' taps are generous.
func hit_target(p: Vector2, prefer: Array = []) -> String:
	var best := ""
	var bd := INF
	# the targets a step waits for win over set pieces behind them (witch_candy: an ingredient on the shelf card)
	for t in prefer:
		var sp0 := target_screen(str(t))
		if sp0.x < -999.0:
			continue
		var d0 := p.distance_to(sp0) / target_radius(str(t))
		if d0 < 1.0 and d0 < bd:
			bd = d0
			best = str(t)
	if best != "":
		return best
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
	if SoundDirector.current:
		SoundDirector.current.fx(name, null, build_ctx)
	if handler and handler.fx(name):
		fx_done.emit(name)
		return
	if name.begins_with("pop:"):
		var sp := set_piece(name.substr(4))
		if sp:
			sp.pop_card(0.0)
			sp.bounce()
	elif name.begins_with("up:"):  # up:<set name>[:bands] — a set piece rises on its hinges (a lot's pile, a foundation)
		var parts := name.split(":")
		var sp3 := set_piece(parts[1])
		if sp3:
			sp3.bands_up(int(parts[2]) if parts.size() > 2 else sp3.band_count(), 0.0)
			sp3.bounce()
	elif name.begins_with("fold:"):
		var sp2 := set_piece(name.substr(5))
		if sp2:
			sp2.collapse(0.0)
	fx_done.emit(name)


## On-page counter (a big printed number floating over a set piece), pops on each change.
func show_counter(n: int, over: String) -> void:
	if SoundDirector.current:  # a rising tick: 0, 2, 4, 5, 7, 9, 11, 12 semitones
		var steps := [0, 2, 4, 5, 7, 9, 11, 12]
		SoundDirector.current.play("ui.count", null, 0.0, 0.0, pow(2.0, float(steps[clampi(n - 1, 0, 7)]) / 12.0))
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
	# Camera shot glide (the rig itself snaps to the focus every frame; we glide its shot parameters, see _glide).
	var rig := world.rig
	_move_t += dt
	var cw := _cam_w
	var wf := cw
	if _move_t > _move_d:  # the move has landed: the focus tightens to a follow
		wf = lerpf(cw, maxf(cw, 4.0 / CAM_FOLLOW_S), clampf((_move_t - _move_d) / 0.8, 0.0, 1.0))
	# distance glides in log space: a dolly from 0.6 to 3.9 grows the view at an even rate (a linear glide pulled the
	# first half of the way out of a room at twice the speed of the rest)
	var ld := _glide("ldist", log(maxf(rig.distance, 0.05)), log(maxf(float(_cam[0]), 0.05)), cw, dt)
	_cam_wrote["ldist"] = ld
	rig.distance = exp(ld)
	var el_off := 0.0
	if not has_walker:
		# stage camera: yaw offset per shot, a hand-held miniature drift (never locked), shake
		if is_nan(_yaw_base):
			_yaw_base = rig.yaw_deg
		_drift_t += dt
		var yst: Array = _cs.get("yaw", [])
		if yst.is_empty():
			_cs["yaw"] = [_yaw_off, 0.0, _yaw_off, 0.0]
			yst = _cs["yaw"]
		var yg := float(_cam[4]) if (_cam as Array).size() > 4 else 0.0
		yg = float(yst[2]) + wrapf(yg - float(yst[2]), -180.0, 180.0)  # the short way round
		_yaw_off = _glide("yaw", _yaw_off, yg, cw, dt)
		_cam_wrote["yaw"] = _yaw_off
		_shake = maxf(0.0, _shake - dt * 2.5 * maxf(_shake, 0.3))
		var drift := 0.35 * sin(_drift_t * 0.31) + 0.2 * sin(_drift_t * 0.53 + 1.0)
		var sh := _shake * sin(_drift_t * 47.0)
		rig.yaw_deg = _yaw_base + _yaw_off + drift + sh
		el_off = 0.25 * sin(_drift_t * 0.41 + 0.5) + 0.6 * _shake * sin(_drift_t * 53.0) * 0.2
	# elevation: the glide state is kept without the drift; a value someone else set on the rig is taken over
	var el_cur := float(_cam_wrote.get("el_v", rig.elevation_deg))
	if absf(rig.elevation_deg - float(_cam_wrote.get("el", INF))) > 1e-4:
		el_cur = rig.elevation_deg
		_cs.erase("el_v")
	var el := _glide("el_v", el_cur, float(_cam[1]), cw, dt)
	rig.elevation_deg = el + el_off
	_cam_wrote["el"] = rig.elevation_deg
	_cam_wrote["el_v"] = el
	rig.focus_height = _glide("fh", rig.focus_height, float(_cam[2]), cw, dt)
	_cam_wrote["fh"] = rig.focus_height
	rig.fov = _glide("fov", rig.fov, float(_cam[3]), cw, dt)
	_cam_wrote["fov"] = rig.fov
	if _follow and is_instance_valid(_follow):
		_focus_goal = _follow.global_position
	if _cam_anchor and not has_walker:
		var ap := _cam_anchor.global_position
		var np := Vector3(_glide("fx", ap.x, _focus_goal.x, wf, dt), _glide("fy", ap.y, _focus_goal.y, wf, dt),
			_glide("fz", ap.z, _focus_goal.z, wf, dt))
		_cam_anchor.global_position = np
		_cam_wrote["fx"] = np.x
		_cam_wrote["fy"] = np.y
		_cam_wrote["fz"] = np.z
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
	if _light_k < 1.0 and not _light_to.is_empty():
		_light_k = move_toward(_light_k, 1.0, dt * 0.4)
		_apply_light()
	if _counter:
		var cs := PaperSpring.step(_counter.scale.x, _counter_v, _counter_s, 9.0, 0.35, dt)
		_counter_v = cs.y
		_counter.scale = Vector3.ONE * maxf(cs.x, 0.001)
		_counter.visible = cs.x > 0.02
	_camera_inside_check()
	if tale.get("spacing", false):
		_spacing_step(dt)
	if tale.get("overlap_check", false):
		_overlap_t += dt
		if _overlap_t >= 0.2:
			_overlap_t = 0.0
			_overlap_check()
	if not _glow_pending.is_empty():
		var left: Array = []
		for q: Array in _glow_pending:
			var c: PaperCard = q[0]
			if not is_instance_valid(c):
				continue
			var m := c.get_surface_override_material(0) as ShaderMaterial
			if m:
				m.set_shader_parameter("glow", float(q[1]))
			else:
				left.append(q)
		_glow_pending = left
	for q: Array in _lights:  # candles and jack-o'-lanterns flicker a little
		if q[2] and is_instance_valid(q[0]):
			(q[0] as OmniLight3D).light_energy = float(q[1]) * (0.88 + 0.08 * sin(_t * 9.1 + float(q[1]) * 7.0) + 0.05 * sin(_t * 23.7))
	if handler:
		handler.step(dt)


## The camera may go INSIDE a house (a refuge's walls stay closed in-story): while it is behind a banded facade or
## within a hand's breadth in front of it, that facade's wall bands (door included) and whoever stands at its windows
## are hidden, so the camera never shows a card edge or the back of a face. The roof is behind the camera then.
var camera_inside := ""
var _sight_focus := Vector3(INF, 0, INF)
var _cam_rate := 2.4
var _yaw_off := 0.0  ## current yaw offset from the template view (shots' 5th field), eased
var _yaw_base := NAN
var _shake := 0.0
var _drift_t := 0.0


## Interactive steps (2026-11-19 user: "처음에 돼지들 누를때 화면이 거기로 안가서 못누름"): before waiting for a tap, every
## target must be fully on screen and big enough to tap (≥ ~80 pt). If not, frame them all: focus on their centroid
## at a distance that fits their spread, and hold. Stage pages only (walker pages keep the road camera, whose sky
## cast / traveller targets are framed by the story shot). Returns true when the camera moved.
func frame_targets(targets: Array) -> bool:
	if has_walker or _cam_anchor == null:
		return false
	if camera_inside != "" and str(tale.get("inside_framing", "")) == "manual":
		return false  # (witch_candy: inside a big room the outdoor fit would pull the camera out; the tale frames it)
	var cam := camera()
	var vs := get_viewport().get_visible_rect().size
	var pts: Array[Vector3] = []
	var ok := true
	for t in targets:
		var p: Variant = _target_point(str(t))
		if p == null:
			continue
		pts.append(p)
		var sp := cam.unproject_position(p)
		var rr := target_radius(str(t))  # the whole tap ring inside the frame, with a margin
		if cam.is_position_behind(p) or sp.x - rr < vs.x * 0.05 or sp.x + rr > vs.x * 0.95 or sp.y - rr < vs.y * 0.06 \
				or sp.y + rr > vs.y * 0.82 or rr < 60.0:
			ok = false
	if ok or pts.is_empty():
		return false
	var c := Vector3.ZERO
	for p in pts:
		c += p
	c /= pts.size()
	var spread := 0.0
	for p in pts:
		spread = maxf(spread, Vector2(p.x - c.x, p.z - c.z).length())
	_follow = null
	_focus_goal = Vector3(c.x, world.ground.surface_y(Vector2(c.x, c.z)), c.z)
	_cam = [clampf(2.4 + spread * 3.2, 2.6, 6.0), 12.0, 0.28, 20.0, 0.0]
	_cam_rate = 2.6
	_begin_move(_cam_rate)
	return true


## Build framing (once per build): one shot that already fits the FINISHED house (full height and width), the pile
## and the builder with margins, held for every tap. Fit by the 20° lens: visible width ≈ 0.47·d, height ≈ 0.35·d.
func frame_build(house: String, others: Array) -> void:
	if has_walker or _cam_anchor == null:
		return
	var pts: Array[Vector3] = []
	var sp := set_piece(house)
	var r := dir_vec("right")
	var top := 0.3
	if sp:
		for sx in [-0.5, 0.5]:
			pts.append(sp.global_position + r * sp.width * sx)
		top = maxf(top, sp.height)
	for t in others:
		var p: Variant = spot_point(str(t)) if spots.has(str(t)) else _target_point(str(t))
		if p != null:
			pts.append(p)
	if pts.is_empty():
		return
	var lo := INF
	var hi := -INF
	var c := Vector3.ZERO
	for p in pts:
		var x: float = (p as Vector3).dot(r)
		lo = minf(lo, x)
		hi = maxf(hi, x)
		c += p
	c /= pts.size()
	var span := (hi - lo) + 0.5  # + a tap ring's width on each side
	var d := clampf(maxf(span * 2.9, top * 4.6), 2.6, 7.5)
	_follow = null
	_focus_goal = Vector3(c.x, world.ground.surface_y(Vector2(c.x, c.z)), c.z)
	_cam = [d, 11.0, top * 0.45, 20.0, 0.0]
	_cam_rate = 2.4
	_begin_move(_cam_rate)


## Camera shake (degrees of jitter, decays over ~0.4 s): a huff, a hammer bump, "앗, 뜨거워!".
func shake(amount: float) -> void:
	_shake = maxf(_shake, amount)  ## only spots near the station count for sightlines (INF: all)


## A shake is running (the camera check does not count its jitter as jumps).
func shaking() -> bool:
	return _shake > 0.05 and not has_walker
var _follow: StoryActor
var _follow_off := Vector3.ZERO


## Road route between two ground points: the nearest road points, the road between them (every 0.25), the goal.
func road_route(a: Vector3, b: Vector3) -> Array:
	var c := world.path.curve
	var xf := world.path.global_transform
	var oa := c.get_closest_offset(xf.affine_inverse() * a)
	var ob := c.get_closest_offset(xf.affine_inverse() * b)
	var out: Array = []
	var n := maxi(1, ceili(absf(ob - oa) / 0.25))
	for i in n + 1:
		var q := xf * c.sample_baked(lerpf(oa, ob, float(i) / n))
		out.append(Vector3(q.x, world.ground.surface_y(Vector2(q.x, q.z)), q.z))
	out.append(b)
	return out


## Tracking shot: the stage camera's focus follows an actor (ends with the next shot_to).
func follow_actor(role: String, shot_name: String) -> void:
	shot_to(shot_name)
	_follow = actor(role)


func _camera_inside_check() -> void:
	var cam := camera()
	if cam == null:
		return
	var now := ""
	var deep := false
	for k in sets:
		var sp: SetPiece = sets[k]
		if sp.bands.is_empty() or sp.walls == null:
			continue
		var l := sp.global_transform.affine_inverse() * cam.global_position
		# patjuk 2026-11-23: tale `inside_margin` (default 0.16): how far in front of the wall the facade already folds
		# away, so a glide into a deep room does not fill the frame with the door on its way through
		var inside := l.z < float(tale.get("inside_margin", 0.16)) and absf(l.x) < sp.width * 0.62 and l.z > -1.5
		sp.walls.visible = not inside
		# wolf_goats 2026-11-24 (tale `inside_door_hide`): the door leaf (not one of the walls) also folds away while the
		# camera passes the front wall, or a glide in / out fills the frame with the door; seen from deep in the room
		# (the turned-round door shot) it stands
		if sp.door_pivot and tale.get("inside_door_hide", false):
			sp.door_pivot.visible = not (inside and l.z > -0.12)
		if inside:
			now = str(k)
			deep = deep or l.z < 0.0
	# with an inside_margin the room's inside-only pieces (the front wall's inside face) wait until the camera is
	# really behind the front wall, or the glide in passes through that card (patjuk)
	if now == "":  # a kit building's room (no facade to fold: its walls are solid all round, rapunzel's tower room)
		for k in sets:
			var sp: SetPiece = sets[k]
			if sp.building and sp.visible and sp.shown > 0 and sp.building.room_at(cam.global_position):
				now = str(k)
	var inside_shown := now != "" and (not tale.has("inside_margin") or deep)
	for k in sets:
		if (sets[k] as SetPiece).has_meta("inside_only"):
			(sets[k] as SetPiece).visible = inside_shown
	if now != camera_inside:
		camera_inside = now
		for r in actors:
			var a: StoryActor = actors[r]
			if a.has_meta("inside"):
				a.visible = now == "" or str(a.get_meta("inside")) != now


static func _make_disc_texture(fill: Color, rim: Color) -> Texture2D:
	# cut-paper disc (2026-11-22 paper look): two stacked paper layers with a crisp deckled cut, a dark cut line at
	# each edge with a lit rim on the upper-left (lit) side, a faint fibre tooth; no stitch ring, no soft fringe
	var n := 512
	var img := Image.create(n, n, false, Image.FORMAT_RGBA8)
	var c := Vector2(n, n) * 0.5
	var cut := rim.darkened(0.45)
	var lit := fill.lightened(0.25)
	for y in n:
		for x in n:
			var p := Vector2(x + 0.5, y + 0.5) - c
			var a := atan2(p.y, p.x)
			var r := n * 0.47 + sin(a * 23.0) * 2.0 + sin(a * 7.0 + 1.0) * 3.2 + sin(a * 61.0) * 0.8  # deckled cut
			var r2 := r - 13.0 + sin(a * 17.0 + 2.0) * 1.6
			var d := p.length()
			var e := r - d  # px inside the outer cut
			if e <= -0.5:
				img.set_pixel(x, y, Color(0, 0, 0, 0))
				continue
			var col := fill if d < r2 else rim
			var upper_left := clampf(-(p.x + p.y) / (p.length() + 1.0) * 0.7, 0.0, 1.0)
			if e < 2.6 or absf(d - r2) < 1.4:
				col = col.lerp(cut, 0.7)
			elif e < 5.0 or (d < r2 and r2 - d < 3.5):
				col = col.lerp(lit, 0.45 * upper_left)
			var t := fmod(sin(x * 12.9898 + y * 78.233) * 43758.5453, 1.0)
			col = col.darkened(absf(t) * 0.035)
			col.a = clampf(e + 0.5, 0.0, 1.0)  # one-pixel antialiased cut, no fringe
			img.set_pixel(x, y, col)
	return ImageTexture.create_from_image(img)
