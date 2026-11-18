class_name SpreadStage
extends Node3D
## One pop-up spread of a story (component E): the meadow world template (scenes/world/meadow.tscn,
## MeadowWorld, built from seed + view, its look untouched) dressed with the story cast:
##  - the sun and the wind as SkyHanger cards hanging on strings in the sky band of the story shot, each on a paper
##    backing disc so it never melts into the trees; they drop in on their strings when the page opens,
##  - the traveller (the template's Walker; the puppet is swapped for the cast library's CastPuppet skin when it
##    exists), scaled up for the story so his poses read at iPad size,
##  - story props (hat, coat) and effects (gusts, leaves, warm light, splash),
##  - story camera shots on the template rig: wide (the template view, used for the page pop), story (pushed in,
##    traveller + sun + wind framed), close (punch-in on the traveller for the payoff moments).
## Cast prints come from CastSkins (cast id + variant), so new cast art drops in by id.

signal fx_done(name: String)

const MEADOW := preload("res://scenes/world/meadow.tscn")
const CAST_PUPPET_PATH := "res://art/cast/rig/cast_puppet.gd"
## r2: story traveller height (the 0.36 contract x1.3): critics 1-3 could not see the coat clutch / coat off.
const TRAV_H := 0.47
## Shots: [distance, elevation deg, focus height, fov]. "wide" uses the template view's own values.
const SHOTS := {
	"story": [3.3, 15.0, 0.34, 20.0],  ## feet clear of the caption strip
	"close": [2.85, 15.0, 0.34, 20.0],  ## same focus as "story": the sky cast stays in frame
}
## Where the sun / wind hang in the story shot (screen fractions) and their card height (fraction of frame height).
const SUN_SCREEN := Vector2(0.21, 0.26)
const WIND_SCREEN := Vector2(0.79, 0.26)
const SKY_FRAC := 0.27

var world: MeadowWorld
var sun: SkyHanger
var wind: SkyHanger
var gusts: WindGusts
var sky_hinges: Array[PopHinge] = []  ## kept for API compatibility (sky cast drops on strings, see _sky)
var extra_hinges: Array[PopHinge] = []
var wind_state := "default"
var sun_state := "default"
var stream_offset := -1.0
var seed_value := 1
var view := 0
var shot := "wide"
var follow_sky := true

var _t := 0.0
var _warm := 0.0
var _warm_target := 0.0
var _key_e0 := 1.0
var _key_c0 := Color.WHITE
var _sun_light: OmniLight3D
var _blowing := false
var _blow_power := 1.0
var _blow_t := 0.0
var _sway_target := 1.0
var _hat: Node3D
var _hat_anim: Dictionary = {}
var _leaves: Array = []  ## [node, age, life, from, to, spin, flutter, arc]
static var _leaf_tex: Array[Texture2D] = []
static var _drop_tex: Texture2D
static var _ring_tex: Texture2D
var _wiggle: Dictionary = {}  ## target -> seconds left
var _origin := Vector3.ZERO
var _coat_hinge: PopHinge
var _carry: PaperCard  ## coat over the arm
var _fan: PaperCard  ## hat in hand, fanning
var _wide: Array = []
var _cam := [0.0, 0.0, 0.0, 20.0]  ## current shot target
var _sky: Array = []  ## per hanger: {anchor, rel, drop, drop_v, target, delay, yaw, yaw_t}
var _trav_s := 1.0
var _trav_v := 0.0
var _trav_target := 1.0
var _trav_delay := -1.0
var _hop := 0.0
var _hop_v := 0.0
var _sink := 0.0
var _sink_target := 0.0
var _shiver := 0.0
var _rings: Array = []  ## [node, age, life, max]
var _cam_anchor: Node3D
var _bank := Vector3.ZERO
const BANK_MARGIN := 0.13  ## stream spot: min distance from the felt cut edge (both feet + ripples on the water)
var _ground_dy := 0.0  ## off the road: ground height under him minus the walker's road height (steps down into the water)
var _pull := 0.0  ## friends: the sun and wind slide toward each other (0..1 of the gap)
var _pull_t := 0.0
## Road stretch this spread's walking covers, offsets relative to the template start (route[0] is where he starts).
## Set before build(); sightlines are cleared along the whole stretch so the follow camera never looks through a card.
var route := Vector2.ZERO
## Stroll: he keeps walking along the road while a beat plays (the fable's traveller on his way). Speed eases to
## `_stroll_speed` x the weather factor; `_pause` stops him in place for a beat (startle, coat off).
var _stroll := false
var _stroll_speed := 0.0
var _stroll_dir := 1.0
var _pause := 0.0
var _push := 0.0  ## gale: pushed back a step
var _start_off := 0.0
## 2026-11-18 walk toward the reader: the traveller card faces the camera, so every walking stretch runs down the road
## TOWARD the camera (he walked away from it before and read as moonwalking). The story camera stands ahead of him
## on the road looking back along it: the rig yaw follows the road heading at his position (smoothed), the follow
## focus dollies it back as he comes on, and the sun / wind hang in the same screen spots (their layout turns with
## the yaw). `_stroll_dir` is the road direction (offset sign) that heads toward the camera side of the page.
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
## The story runner prebuilds the next spread this way while the current page plays (SpreadStage under an
## off-screen SubViewport with its own World3D, moved into the story when its page turns).
var perf_phases := {}
var build_frames := 0
var max_slice_ms := 0.0
var is_built := false
var _slicer: BuildSlicer


func build_async(seed_v: int, view_i: int, with_audio: bool, budget_ms: float) -> void:
	_slicer = BuildSlicer.new(budget_ms, get_tree())
	seed_value = seed_v
	view = view_i
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
	if route != Vector2.ZERO:
		var L := world.path.curve.get_baked_length()
		w.offset = clampf(w.offset + route.x, 0.0, L)
		w.target_offset = w.offset
		w.global_position = world.path.global_transform * world.path.curve.sample_baked(w.offset)
		world.focus.snap()
		_stroll_dir = signf(route.y - route.x) if route.y != route.x else 1.0
	else:
		_stroll_dir = _toward_cam_sign(w.offset)
	if road_cam:
		world.rig.yaw_deg = road_yaw(w.offset)
		_yaw_t = world.rig.yaw_deg
		world.rig.snap()
	_origin = w.global_position
	await _slicer.tick()
	_swap_puppet()
	await _slicer.tick()
	var rig := world.rig
	_wide = [rig.distance, rig.elevation_deg, rig.focus_height, rig.fov]
	_cam = _wide.duplicate()
	_build_sky()
	await _slicer.tick()
	_layout_sky()
	await _slicer.tick()
	_slicer.phase("sightlines")
	await _clear_sightlines()
	_slicer.phase("stream")
	await _slicer.tick()
	await _find_stream()
	await _slicer.tick()
	_slicer.phase("finish")
	if rig.key:
		_key_e0 = rig.key.light_energy
		_key_c0 = rig.key.light_color
	if _leaf_tex.is_empty():
		for col in [Color("7f9a4a"), Color("c99a3e"), Color("b8643a")]:
			_leaf_tex.append(_make_leaf_texture(col))
		_drop_tex = _make_drop_texture()
		_ring_tex = _make_ring_texture()
	_trav_s = 0.02
	_trav_target = 0.02
	_apply_trav()
	_slicer.finish()
	perf_phases = _slicer.phases.duplicate()
	build_frames = _slicer.frames
	max_slice_ms = _slicer.max_slice_ms
	is_built = true


## Cast library skin for the traveller (CastPuppet, same pose names) when it exists; scaled for the story.
func _swap_puppet() -> void:
	var old := world.puppet
	var pp: PaperPuppet
	if CastSkins.puppet_kind("traveller") == "cast_puppet":
		pp = (load(CAST_PUPPET_PATH) as GDScript).new() as PaperPuppet
	else:
		pp = PaperPuppet.new()
	pp.name = "Puppet"
	pp.height = TRAV_H
	pp.camera = old.camera
	pp.step_period = old.step_period * 1.12
	pp.max_stride = old.max_stride * TRAV_H / 0.36
	pp.min_stride = old.min_stride * TRAV_H / 0.36
	pp.foot_lift = old.foot_lift * TRAV_H / 0.36
	pp.hop = old.hop * TRAV_H / 0.36
	# Front-facing steps toward the camera (CastPuppet.front_gait): fewer, longer steps than the template walk so
	# each lift reads (≈2 steps/s at the stroll pace, ≈1/s pushing into the wind).
	if "front_gait" in pp:
		pp.set("front_gait", true)
		pp.step_period = 0.46
		pp.min_stride = 0.05
		pp.max_stride = 0.13
		pp.foot_lift = 0.03 * TRAV_H / 0.36
		pp.waddle_deg = 4.0
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


## Camera yaw (deg) that looks back along the road at offset `o` while he walks toward the camera (`_stroll_dir`):
## the walk heading averaged over the stretch just behind and ahead of him, clamped to the range the meadow's
## cards read from (they all face +Z, template views use -30..32).
func road_yaw(o: float) -> float:
	var c := world.path.curve
	var L := c.get_baked_length()
	var acc := Vector2.ZERO
	for j in 7:
		var a := clampf(o + _stroll_dir * (-0.3 + 0.25 * j), 0.0, L)
		var p0 := world.path.global_transform * c.sample_baked(clampf(a - 0.1 * _stroll_dir, 0.0, L))
		var p1 := world.path.global_transform * c.sample_baked(clampf(a + 0.1 * _stroll_dir, 0.0, L))
		var d := Vector2(p1.x - p0.x, p1.z - p0.z)
		if d.length() > 1e-4:
			acc += d.normalized()
	if acc.length() < 1e-4:
		return world.rig.yaw_deg
	return clampf(rad_to_deg(atan2(acc.x, acc.y)), -38.0, 38.0)


## Sky cast offset from the traveller, turned with the camera yaw since the layout.
func _sky_rel(i: int, yaw_deg: float = NAN) -> Vector3:
	var yw := world.rig.yaw_deg if is_nan(yaw_deg) else yaw_deg
	return Basis(Vector3.UP, deg_to_rad(yw - _yaw0)) * (_sky[i]["rel"] as Vector3)


func _ground_dirs() -> Array:
	var yw := deg_to_rad(world.rig.yaw_deg)
	return [Vector2(sin(yw), cos(yw)), Vector2(cos(yw), -sin(yw)), yw]  # to camera, camera right, yaw


func _build_sky() -> void:
	sun = SkyHanger.new()
	sun.name = "Sun"
	sun.texture = CastSkins.texture("sun")
	sun.hanging = true
	sun.sway_amount = 0.025
	sun.bob_amount = 0.012
	sun.seed_offset = 0.2 + view
	wind = SkyHanger.new()
	wind.name = "Wind"
	wind.texture = CastSkins.texture("wind")
	wind.hanging = true
	wind.sway_amount = 0.04
	wind.bob_amount = 0.016
	wind.seed_offset = 0.7 + view
	for h in [sun, wind]:
		var anchor := Node3D.new()
		anchor.name = h.name + "Anchor"
		anchor.top_level = true
		add_child(anchor)
		anchor.add_child(h)
		_sky.append({"anchor": anchor, "h": h, "rel": Vector3.ZERO, "drop": 1.6, "v": 0.0, "target": 1.6,
			"delay": -1.0, "yaw": 0.0, "yaw_t": 0.0})
	gusts = WindGusts.new()
	gusts.name = "Gusts"
	gusts.hanger = wind
	gusts.curl_height = 0.11
	add_child(gusts)
	_sun_light = OmniLight3D.new()
	_sun_light.light_color = Color(1.0, 0.78, 0.45)
	_sun_light.omni_range = 2.6
	_sun_light.light_energy = 0.0
	_sun_light.shadow_enabled = false
	add_child(_sun_light)


func _apply_shot_now(name: String) -> void:
	var s: Array = _wide if name == "wide" else SHOTS[name]
	var rig := world.rig
	rig.distance = s[0]
	rig.elevation_deg = s[1]
	rig.focus_height = s[2]
	rig.fov = s[3]
	rig.snap()


## Hang the sun and wind where the story shot frames them: upper left / upper right, a little in front of the
## traveller, in the sky band clear of the canopy. Positions are kept relative to the traveller (the sky follows
## him along the road), sizes from the frame height at their depth.
func _layout_sky() -> void:
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
	var hs := [sun, wind]
	var scr := [SUN_SCREEN, WIND_SCREEN]
	for i in 2:
		var h: SkyHanger = hs[i]
		var ch := frame_h * SKY_FRAC * (1.0 if i == 0 else 0.86)
		h.card_height = ch
		h.card().height = ch  # SkyHanger sized its card in _ready
		h.stem_height = 1.4
		var centre := cam.project_position(vs * (scr[i] as Vector2), depth)
		# anchor = card centre + half the card + the string
		var anchor := centre + Vector3(0, ch * 0.5 + h.stem_height, 0)
		_sky[i]["rel"] = anchor - tp
		_sky[i]["base"] = anchor
		(_sky[i]["anchor"] as Node3D).global_position = anchor + Vector3(0, 1.6, 0)
		var yaw := atan2(cam.global_position.x - centre.x, cam.global_position.z - centre.z)
		(_sky[i]["anchor"] as Node3D).rotation.y = yaw
		_sky[i]["face"] = yaw
		_add_backing(h, i == 0)
	_yaw0 = world.rig.yaw_deg
	_apply_shot_now("wide")


## A cut-paper sky disc behind the card (cream for the sun, pale blue for the wind) so the sky cast reads against
## orange trees and haze (critics 1-2).
func _add_backing(h: SkyHanger, is_sun: bool) -> void:
	await get_tree().process_frame  # SkyHanger builds its card in _ready
	if not is_instance_valid(h):
		return
	var c := h.card()
	var disc := PaperCard.new()
	disc.texture = _make_disc_texture(Color("fbf0cf") if is_sun else Color("d9e7ef"), Color("e2b85c") if is_sun else Color("7f9fb8"))
	disc.height = h.card_height * (1.12 if is_sun else 1.05)
	disc.thickness = 0.01
	disc.back_print = false
	# Child of the card itself so it always follows it (as a sibling it kept a stale position when a story
	# started mid-way with --beat, and the discs were left lying on the meadow).
	disc.name = "SkyDisc"
	disc.position = Vector3(0, -h.card_height * (0.06 if is_sun else 0.1), -0.03)
	for old in c.get_children():
		if old.name == "SkyDisc":
			old.queue_free()
	c.add_child(disc)


## Story dressing on top of the template: hinged meadow cards standing between the story camera and the sun /
## wind / traveller are left out of this spread (hidden, never popped), and so are their contact shadows.
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
	for o in stops:
		w.global_position = world.path.global_transform * world.path.curve.sample_baked(o)
		world.focus.snap()
		if road_cam:
			world.rig.yaw_deg = road_yaw(o)
		await _clear_sightlines_here(keep_all, hidden)
		await _slicer.tick()
	w.global_position = world.path.global_transform * world.path.curve.sample_baked(home)
	world.focus.snap()
	world.rig.yaw_deg = yaw_home
	var keep: Array[PopHinge] = []
	for hinge: PopHinge in world.hinges:
		if (hinge.get_parent() as Node3D).visible:
			keep.append(hinge)
	world.hinges = keep
	_hide_contact_blobs(hidden)
	_apply_shot_now("wide")
	print("SPREAD view=", view, " route=", route, " sightline cards hidden=", hidden.size(), " statics hidden=", _statics_hidden)


func _clear_sightlines_here(all: Array[PopHinge], hidden: Array[Vector3]) -> void:
	_apply_shot_now("story")
	var cam := camera()
	var cp := cam.global_position
	var rects: Array = []
	for i in 2:
		var h: SkyHanger = _sky[i]["h"]
		var anchor: Vector3 = traveller_pos() + _sky_rel(i)
		var c := anchor - Vector3(0, h.stem_height + h.card_height * 0.5, 0)
		var a := cam.unproject_position(c)
		var b := cam.unproject_position(c + Vector3(0, h.card_height * 0.7, 0))
		var r := a.distance_to(b)
		rects.append([Rect2(a - Vector2(r, r), Vector2(r, r) * 2.0).grow(10.0), cp.distance_to(c)])
	var tp := traveller_pos()
	var ta := cam.unproject_position(tp)
	var tb := cam.unproject_position(tp + Vector3(0, TRAV_H, 0))
	var tw := absf(ta.y - tb.y) * 0.45
	rects.append([Rect2(ta.x - tw, tb.y, tw * 2.0, ta.y - tb.y).abs().grow(12.0), cp.distance_to(tp)])
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


func _find_stream() -> void:
	var c := world.path.curve
	var L := c.get_baked_length()
	var best := INF
	var o := 0.0
	while o < L:
		await _slicer.tick()
		var p := world.path.global_transform * c.sample_baked(o)
		var d := absf(world.ground.stream_distance(Vector2(p.x, p.z)) + world.ground.stream_width * 0.5)
		if d < best:
			best = d
			stream_offset = o
		o += 0.05
	var here := world.walker.offset
	stream_offset = clampf(stream_offset + 0.55 * signf(here - stream_offset if absf(here - stream_offset) > 0.01 else -1.0), 0.0, L)
	# A spot IN the water channel (2026-11-18 user: "he sinks his feet into the ground, not the water"): the old spot
	# used the smooth centreline distance (-0.09..-0.02 = right at the wobbly cut edge), so he often stood on the felt bank
	# and sank through it. Now: a point inside the real cut polygon (the felt sheet's hole, see GroundLayers) at least
	# BANK_MARGIN from its edge, so both feet and the ripples are on the recessed water and the bank lip is behind/beside
	# him; the stage drops him to the water surface there (_ground_dy) and the opaque water hides his sunk legs.
	var p0 := world.path.global_transform * c.sample_baked(stream_offset)
	var to_cam: Vector2 = _ground_dirs()[0]
	var g := world.ground
	var poly: PackedVector2Array = g.get("_stream_poly")
	var bs := INF
	_bank = p0
	for ai in 48:
		await _slicer.tick()
		var ang := TAU * ai / 48.0
		for ri in 14:
			var r := 0.3 + ri * 0.06
			var q := Vector2(p0.x, p0.z) + Vector2(cos(ang), sin(ang)) * r
			if poly.size() < 3 or not Geometry2D.is_point_in_polygon(q, poly):
				continue
			var e := _poly_edge_dist(poly, q)
			if e < BANK_MARGIN or g.path_distance(q) < 0.3:
				continue
			# near the road, toward the camera, not too deep into the middle of the channel
			var score := r - 0.6 * (q - Vector2(p0.x, p0.z)).normalized().dot(to_cam) + 0.8 * maxf(0.0, e - BANK_MARGIN - 0.06)
			if score < bs:
				bs = score
				_bank = Vector3(q.x, p0.y, q.y)
	print("SPREAD stream spot ", _bank, " in_water=", poly.size() >= 3 and Geometry2D.is_point_in_polygon(Vector2(_bank.x, _bank.z), poly),
		" edge=", _poly_edge_dist(poly, Vector2(_bank.x, _bank.z)) if poly.size() >= 3 else -1.0)


static func _poly_edge_dist(poly: PackedVector2Array, q: Vector2) -> float:
	var best := INF
	for i in poly.size():
		var a := poly[i]
		var b := poly[(i + 1) % poly.size()]
		best = minf(best, q.distance_to(Geometry2D.get_closest_point_to_segment(q, a, b)))
	return best


# ------------------------------------------------------------------ page

## Raise the spread in a wave from the traveller; returns seconds until the last piece starts.
func pop(start := 0.0) -> float:
	var wave := PopWave.new()
	wave.speed = 4.0
	var end := wave.pop(world.hinges, _origin, start)
	_trav_delay = start + 0.12
	_trav_target = 1.0
	for i in _sky.size():
		_sky[i]["delay"] = start + minf(end, 0.9) + 0.2 + i * 0.25
		_sky[i]["target"] = 0.0
	return maxf(end, minf(end, 0.9) + 0.6)


## Fold everything back flat (outside-in, like the book closing); returns seconds until all are moving.
func fold() -> float:
	var all: Array = []
	all.append_array(world.hinges)
	all.append_array(extra_hinges)
	var wave := PopWave.new()
	var t := wave.fold(all, world.walker.global_position, 0.0, true)
	for i in _sky.size():
		_sky[i]["delay"] = 0.0
		_sky[i]["target"] = 1.8
	_trav_delay = maxf(t - 0.2, 0.0)
	_trav_target = 0.02
	shot_to("wide")
	return t


## Camera shot on the template rig: "wide" (template view) | "story" | "close".
func shot_to(name: String) -> void:
	shot = name
	_cam = _wide.duplicate() if name == "wide" else (SHOTS[name] as Array).duplicate()


# ------------------------------------------------------------------ traveller

func puppet() -> PaperPuppet:
	return world.puppet


func set_pose(p: String, instant := false) -> void:
	world.puppet.set_pose(p, instant)
	if _fan and p != "walk_nohat":
		_fan.visible = false


## `dist` > 0 = on along his way (down the road toward the camera, see road_cam).
func walk_by(dist: float) -> void:
	var w := world.walker
	w.target_offset = clampf(w.offset + _stroll_dir * dist, 0.0, world.path.curve.get_baked_length())


func walk_to_offset(o: float) -> void:
	world.walker.target_offset = o


## Leave the road to the stream bank spot (straight line), where he sits with his feet in the water.
func walk_to_bank() -> void:
	var w := world.walker
	w.path = null
	w.walk_to(_bank)


func walking() -> bool:
	var w := world.walker
	if w.path == null:
		return Vector2(w.global_position.x - _bank.x, w.global_position.z - _bank.z).length() > 0.015 or world.puppet.speed > 0.02
	return absf(w.target_offset - w.offset) > 0.006 or world.puppet.speed > 0.02


func traveller_pos() -> Vector3:
	return world.walker.global_position


## Ending: the camera stops following and he walks off down the road.
func walk_away(dist: float) -> void:
	_cam_anchor = Node3D.new()
	_cam_anchor.top_level = true
	add_child(_cam_anchor)
	_cam_anchor.global_position = world.focus.global_position
	world.rig.focus_target = _cam_anchor
	follow_sky = false
	walk_by(dist)


## Keep walking along the road at `speed` until stroll_stop() (camera and sky cast follow him).
func stroll(speed: float) -> void:
	_stroll = true
	_stroll_speed = speed


func stroll_stop() -> void:
	_stroll = false
	var w := world.walker
	w.target_offset = clampf(w.offset + _stroll_dir * 0.05, 0.0, world.path.curve.get_baked_length())


func strolling() -> bool:
	return _stroll


func _step_stroll(dt: float) -> void:
	var w := world.walker
	var pp := world.puppet
	if _push > 0.0:
		_push -= dt
		if _push <= 0.0:
			pp.max_turn_deg = 20.0
		return
	if not _stroll:
		return
	if _pause > 0.0:
		_pause -= dt
		w.target_offset = w.offset
		return
	var L := world.path.curve.get_baked_length()
	# Weather: pushing into the wind (slow, short steps, leaning in); heat (slowing as he gets hotter).
	var k := 1.0
	if _blowing:
		k = 0.45
	elif _shiver > 0.3:
		k = 0.7
	k *= 1.0 - 0.45 * clampf(_warm, 0.0, 1.0)
	w.speed = lerpf(w.speed, _stroll_speed * k, 1.0 - exp(-2.0 * dt))
	var lo := 0.0
	var hi := L
	if route != Vector2.ZERO:  # never past the stretch whose sightlines were cleared
		lo = clampf(_start_off + minf(route.x, route.y), 0.0, L)
		hi = clampf(_start_off + maxf(route.x, route.y), 0.0, L)
	w.target_offset = clampf(w.offset + _stroll_dir * 0.6, lo, hi)
	if "front_lift" in pp:  # struggling steps in the wind: low shuffling lift, heavier roll; light steps otherwise
		var struggle := 1.0 if _blowing else (0.5 if _shiver > 0.3 else 0.0)
		var e := 1.0 - exp(-3.0 * dt)
		pp.set("front_lift", lerpf(float(pp.get("front_lift")), 1.0 - 0.55 * struggle, e))
		pp.set("front_roll_deg", lerpf(float(pp.get("front_roll_deg")), 0.6 + 0.6 * struggle, e))
		pp.set("front_arm_swing", lerpf(float(pp.get("front_arm_swing")), 1.0 - 0.7 * struggle, e))
		pp.set("front_hunch", lerpf(float(pp.get("front_hunch")), struggle, e))  # hunched, arms tucked to the coat
		# heat: slow, droopy while he still has the coat on; light again once it is off
		var cool := pp.pose.begins_with("shirt") or pp.pose.begins_with("relieved")
		pp.set("front_droop", lerpf(float(pp.get("front_droop")), clampf(_warm, 0.0, 1.0) * (0.25 if cool else 1.0), e))
	if "push_lean_deg" in pp:
		pp.set("push_lean_deg", lerpf(float(pp.get("push_lean_deg")), 2.5 if _blowing else (1.0 if _shiver > 0.3 else 0.0), 1.0 - exp(-3.0 * dt)))


## Gale: the wind shoves him back half a step, he plants and leans in again.
func _shove() -> void:
	var w := world.walker
	var pp := world.puppet
	pp.max_turn_deg = 0.0  # stepping back, he keeps facing his way (no turn-around flip)
	w.speed = 0.16
	w.target_offset = clampf(w.offset - _stroll_dir * 0.07, 0.0, world.path.curve.get_baked_length())
	_push = 1.0


func _apply_trav() -> void:
	var w := world.walker
	w.scale = Vector3(1.0, maxf(_trav_s, 0.02), 1.0)
	world.puppet.visible = _trav_s > 0.05
	# Only vertical here: the puppet measures its own ground motion for the gait, so a sideways jitter on its
	# position made it take steps in place. The shiver is CastPuppet.shiver (body rocks, feet planted).
	world.puppet.position = Vector3(0, _hop - _sink + _ground_dy, 0)
	if "shiver" in world.puppet:
		world.puppet.set("shiver", _shiver)


# ------------------------------------------------------------------ taps

func camera() -> Camera3D:
	return world.rig.camera


func _card_centre(h: SkyHanger) -> Vector3:
	var c := h.card()
	return c.global_transform * Vector3(0, h.card_height * 0.5, 0)


## Screen position of a tap target ("sun", "wind", "traveller").
func target_screen(target: String) -> Vector2:
	var cam := camera()
	match target:
		"sun":
			return cam.unproject_position(_card_centre(sun))
		"wind":
			return cam.unproject_position(_card_centre(wind))
		"traveller":
			return cam.unproject_position(traveller_pos() + Vector3(0, TRAV_H * 0.5, 0))
	return Vector2(-1000, -1000)


func target_radius(target: String) -> float:
	var cam := camera()
	if target == "traveller":
		var a := cam.unproject_position(traveller_pos())
		var b := cam.unproject_position(traveller_pos() + Vector3(0, TRAV_H, 0))
		return maxf(80.0, a.distance_to(b) * 0.55)
	var h: SkyHanger = sun if target == "sun" else wind
	var c := _card_centre(h)
	var top := cam.unproject_position(c + Vector3(0, h.card_height * 0.5, 0))
	return maxf(90.0, cam.unproject_position(c).distance_to(top) * 1.1)


## Which story target a screen point hits ("" for none). Kids' taps are generous.
func hit_target(p: Vector2) -> String:
	var best := ""
	var bd := INF
	for t in ["sun", "wind", "traveller"]:
		var d := p.distance_to(target_screen(t)) / target_radius(t)
		if d < 1.0 and d < bd:
			bd = d
			best = t
	return best


## A little reaction when a cast member is tapped.
func wiggle(target: String) -> void:
	match target:
		"sun":
			sun.puff(1.16)
			sun.push(Vector3(0, 0.25, 0))
			_wiggle["sun"] = 0.4
		"wind":
			wind.puff(1.16)
			wind.push(Vector3(randf_range(-0.2, 0.2), 0.2, 0))
			_wiggle["wind"] = 0.4
		"traveller":
			_hop_v = 0.9


# ------------------------------------------------------------------ effects

## Held press on the wind (or a scripted blow). power 1 = normal, 2 = gale, 0.35 = gentle breeze.
func set_blowing(on: bool, power := 1.0) -> void:
	_blowing = on
	_blow_power = power


func gentle_gust() -> void:
	gusts.gust_every = 0.45
	gusts.blow(traveller_pos() + Vector3(0, TRAV_H * 0.6, 0), 0.8)
	_sway_target = 2.0
	_blow_t = 0.9
	wind_state = "blow"
	wind.puff(1.08)
	_spawn_leaves(3, 0.5)


func fx(name: String) -> void:
	match name:
		"sky_rise":
			pass
		"sun_proud":
			sun_state = "proud"
			sun.puff(1.18)
			_wiggle["sun"] = 0.6
		"wind_boast":
			wind_state = "default"
			wind.puff(1.15)
			_wiggle["wind"] = 0.5
		"show_coat":
			_hop_v = 1.1
		"wind_puff":
			sun_state = "default"
			wind_state = "blow"
			wind.puff(1.22)
			_wiggle["wind_relax"] = 1.4
		"leaves":
			_spawn_leaves(14)
			shot_to("story")
		"hat_off":
			# "앗, 내 모자!": startle hop, wide eyes, hands up to his bare head; he stops a moment.
			_hat_off()
			set_pose(_face("surprised_nohat", "walk_nohat"))
			_hop_v = 1.25
			_pause = 2.2
		"flap":
			_spawn_leaves(8)
			set_pose(_face("cold", "walk_nohat"))
			_shiver = 0.7
		"clutch":
			# "으으, 추워!": hugging himself (no hat: the hat is gone), teeth chattering, a hard shiver.
			set_pose(_face("cold", "hold"))
			_shiver = 1.3
			_hop_v = 0.5
		"gale":
			_spawn_leaves(16)
			_shiver = 1.6
			_shove()
		"wind_tired":
			_blowing = false
			gusts.tire()
			wind_state = "tired"
			_sway_target = 1.0
			_shiver = 0.25  # still shivering a little; dies away after the hat comes back
			_wiggle["shiver_off"] = 3.0
		"wind_calm":
			gusts.calm()
			wind_state = "default"
		"hat_back":
			_hat_back()
		"warm1":
			# "아, 따뜻하다~": coat unbuttoned, flushed, the first sweat drops.
			_warm_target = 0.4
			sun_state = "beaming"
			sun.puff(1.2)
			set_pose(_face("warm", "walk"))
		"warm2":
			# "아이, 더워!": hat off in his hand, fanning, tongue out, dripping.
			_warm_target = 0.75
			sun.puff(1.25)
			if _has_pose("hot_fan"):
				set_pose("hot_fan")  # the hat-in-hand is a hinged arm part; CastPuppet fans it
			else:
				set_pose("walk_nohat")
				_fan_hat(true)
		"coat_off":
			# "훌러덩!": he stops, the coat drops, a relieved breath.
			_warm_target = 1.0
			sun.puff(1.3)
			set_pose(_face("relieved", "shirt"))
			_drop_coat()
			_pause = 999.0
			shot_to("close")  # punch-in on the payoff (no tap is asked for while it lasts)
		"walk_on":
			# after the coat-off moment: picks the coat up and walks on carrying it.
			_pick_coat()
			set_pose(_face("shirt_calm", "shirt"))
			_pause = 0.6
			_stroll_speed = 0.2  # coat off, cool again: back to an easy pace (the heat factor still slows it)
		"sun_wins":
			sun_state = "proud"
			sun.puff(1.25)
			_wiggle["sun"] = 0.8
			_face_each_other(0.35)
			shot_to("story")
		"pick_coat":
			_pick_coat()
		"carry_coat":
			_carry_coat(true)
		"sun_glow":
			_warm_target = 1.0
			sun.puff(1.2)
		"quiz_wrong":
			gusts.blow(traveller_pos() + Vector3(0, TRAV_H * 1.3, 0), 1.2)
			wind_state = "blow"
			_blow_t = 1.2
			_sway_target = 3.0
			_shiver = 1.4
			_wiggle["shiver_off"] = 1.4
			_spawn_leaves(8)
		"quiz_right":
			_warm_target = 1.0
			sun_state = "beaming"
			sun.puff(1.3)
			_wiggle["sun"] = 0.8
		"splash":
			_sink_target = TRAV_H * 0.13  # shallow stream: the water comes up to his shins
			_splash()
		"cool":
			set_pose(_face("relieved", "shirt"))
		"friends":
			sun_state = "beaming"
			wind_state = "default"
			sun.puff(1.12)
			wind.puff(1.12)
			_face_each_other(0.5)
			_pull_t = 0.22
			sun.push(Vector3(0.3, 0.15, 0))
			wind.push(Vector3(-0.3, 0.15, 0))
	fx_done.emit(name)


func _has_pose(p: String) -> bool:
	var pp := world.puppet
	var scr := pp.get_script() as Script
	if scr == null or not scr.get_script_constant_map().has("SKINS"):
		return false
	var sk: Dictionary = (scr.get_script_constant_map()["SKINS"] as Dictionary).get(str(pp.get("skin")), {})
	return (sk.get("poses", {}) as Dictionary).has(p)


## Expression pose when the cast skin has it, else the old pose (legacy puppet).
func _face(p: String, fallback: String) -> String:
	return p if _has_pose(p) else fallback


func _face_each_other(a: float) -> void:
	_sky[0]["yaw_t"] = -a  # sun (left) turns right, toward the wind
	_sky[1]["yaw_t"] = a


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
	# Road camera: stands ahead of him on the road looking back along it (see road_cam); frozen once the ending
	# camera stops following or he leaves the road for the stream bank.
	if road_cam and _cam_anchor == null and world.walker.path != null:
		_yaw_t = lerpf(_yaw_t, road_yaw(world.walker.offset), 1.0 - exp(-0.9 * dt))
		rig.yaw_deg = lerpf(rig.yaw_deg, _yaw_t, 1.0 - exp(-1.6 * dt))
	# Sky cast: hangs relative to the traveller, drops in on its strings, turns toward each other for "friends".
	_pull = lerpf(_pull, _pull_t, 1.0 - exp(-1.5 * dt))
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
		var mid: Vector3 = (_sky_rel(0) + _sky_rel(1)) * 0.5
		var rel: Vector3 = rel0.lerp(Vector3(mid.x, rel0.y, mid.z), _pull)
		if follow_sky:
			base = base.lerp(trav + rel, 1.0 - exp(-2.0 * dt))
		s["base"] = base
		an.global_position = base + Vector3(0, float(s["drop"]), 0)
		if s.has("face"):
			an.rotation.y = float(s["face"]) + deg_to_rad(rig.yaw_deg - _yaw0)
		(s["h"] as SkyHanger).rotation.y = float(s["yaw"])
	# Traveller pop (scale on the walker, springy), hop, sink, shiver.
	if _trav_delay >= 0.0:
		_trav_delay -= dt
	if _trav_delay < 0.0:
		var w2 := TAU * 2.4
		_trav_v += (-w2 * w2 * (_trav_s - _trav_target) - 2.0 * 0.35 * w2 * _trav_v) * dt
		_trav_s = clampf(_trav_s + _trav_v * dt, 0.02, 1.3)
	_hop_v -= 6.0 * dt
	_hop = maxf(0.0, _hop + _hop_v * dt)
	if _hop <= 0.0 and _hop_v < 0.0:
		_hop_v = 0.0
	_sink = lerpf(_sink, _sink_target, 1.0 - exp(-3.0 * dt))
	# Off the road (stream spot): follow the real ground height under him, so he steps DOWN off the felt bank onto the
	# recessed water (GroundLayers: water card at 0.004, felt top 0.022) instead of floating at road height.
	var want_dy := 0.0
	if world.walker.path == null:
		var tq := Vector2(trav.x, trav.z)
		want_dy = world.ground.surface_y(tq) - world.walker.global_position.y
	_ground_dy = lerpf(_ground_dy, want_dy, 1.0 - exp(-10.0 * dt))
	_step_stroll(dt)
	_apply_trav()
	# Wind blowing while held: re-trigger gusts toward the traveller, the meadow leans downwind, cheeks puffed.
	if _blowing:
		if not gusts._blow_left > 0.05:
			gusts.gust_every = 0.28 / clampf(_blow_power, 0.5, 2.0)
			gusts.blow(trav + Vector3(0, TRAV_H * 1.3, 0), 0.6)  # over his head: the curls kept covering his face
		wind_state = "blow"
		wind.puff(1.12 + 0.05 * sin(_t * 9.0))
		_sway_target = 1.0 + 3.0 * _blow_power
		_blow_t = 0.5
		if randf() < dt * 4.0 * _blow_power:
			_spawn_leaves(1)
	elif _blow_t > 0.0:
		_blow_t -= dt
		if _blow_t <= 0.0:
			_sway_target = 1.0
			wind.puff(1.0)
			if wind_state == "blow":
				wind_state = "default"
	if world.sway:
		var wp := Vector2(wind.global_position.x, wind.global_position.z)
		var dir := (Vector2(trav.x, trav.z) - wp).normalized()
		if dir.length() > 0.1:
			world.sway.wind_dir = dir
		world.sway.strength = lerpf(world.sway.strength, _sway_target, 1.0 - exp(-3.0 * dt))
	# Prints from the cast skin lookup (WindGusts swaps to its own placeholder prints, we win: priority 100).
	var want_w := CastSkins.texture("wind", wind_state)
	if want_w and wind.texture != want_w:
		wind.set_texture(want_w)
	var want_s := CastSkins.texture("sun", sun_state)
	if want_s and sun.texture != want_s:
		sun.set_texture(want_s)
	for key in _wiggle.keys():
		_wiggle[key] -= dt
		if _wiggle[key] <= 0.0:
			_wiggle.erase(key)
			if key == "sun":
				sun.puff(1.0 + 0.06 * _warm)
			elif key == "wind":
				wind.puff(1.0)
			elif key == "wind_relax":
				wind.puff(1.0)
				if not _blowing:
					wind_state = "default"
			elif key == "shiver_off":
				_shiver = 0.0
	# Warm light: the key warms and brightens, a warm glow lamp sits at the sun card.
	_warm = lerpf(_warm, _warm_target, 1.0 - exp(-1.6 * dt))
	if rig.key:
		rig.key.light_energy = _key_e0 * (1.0 + 0.3 * _warm)
		rig.key.light_color = _key_c0.lerp(Color(1.0, 0.76, 0.48), 0.5 * _warm)
	_sun_light.global_position = trav.lerp(_card_centre(sun), 0.5) + Vector3(0, 0, 0.3)
	_sun_light.light_energy = 0.3 + 2.0 * _warm
	if _fan and _fan.visible:
		_fan.rotation.z = 0.5 * sin(_t * 11.0)
	_step_hat(dt)
	_step_leaves(dt)
	_step_rings(dt)


# ------------------------------------------------------------------ hat, coat, leaves

func _downwind() -> Vector3:
	var a := wind.global_position
	var b := traveller_pos()
	return Vector3(b.x - a.x, 0, b.z - a.z).normalized()


func _hat_card() -> void:
	if _hat != null:
		return
	_hat = Node3D.new()
	_hat.name = "Hat"
	_hat.top_level = true
	add_child(_hat)
	var c := PaperCard.new()
	c.texture = CastSkins.texture("hat")
	c.height = 0.1 * TRAV_H / 0.36
	c.thickness = 0.006
	c.position = Vector3(0, -c.height * 0.5, 0)
	_hat.add_child(c)


## sw_017 "모자가 훨훨 날아갔어요": the hat whirls up and away off the page (critic 1), back in sw_024.
func _hat_off() -> void:
	_hat_card()
	var head := traveller_pos() + Vector3(0, TRAV_H * 0.95, 0)
	var away := traveller_pos() + _downwind() * 1.5 + Vector3(0, 1.5, 0)
	_hat.visible = true
	_hat.global_position = head
	_hat_anim = {"from": head, "to": away, "t": 0.0, "dur": 2.2, "arc": 0.35, "back": false}


func _hat_back() -> void:
	_hat_card()
	var head := traveller_pos() + Vector3(0, TRAV_H * 0.95, 0)
	var from := traveller_pos() - _downwind() * 0.9 + Vector3(0, 1.2, 0)
	_hat.visible = true
	_hat.global_position = from
	_hat_anim = {"from": from, "to": head, "t": 0.0, "dur": 1.8, "arc": 0.15, "back": true}


func _step_hat(dt: float) -> void:
	if _hat_anim.is_empty() or _hat == null:
		return
	_hat_anim["t"] += dt
	var u: float = clampf(_hat_anim["t"] / _hat_anim["dur"], 0.0, 1.0)
	var back: bool = _hat_anim["back"]
	var e := u * u * (3.0 - 2.0 * u) if back else u * (0.6 + 0.4 * u)
	var p: Vector3 = (_hat_anim["from"] as Vector3).lerp(_hat_anim["to"], e)
	p.y += sin(u * PI) * float(_hat_anim["arc"])
	# flutter: side-to-side like a falling leaf on the way back, tumbling on the way out
	var side := Vector3(cos(deg_to_rad(world.rig.yaw_deg)), 0, -sin(deg_to_rad(world.rig.yaw_deg)))
	p += side * sin(u * TAU * (2.0 if back else 1.0)) * 0.12 * (1.0 - u if back else u)
	_hat.global_position = p
	var cam := camera()
	var face := atan2(cam.global_position.x - p.x, cam.global_position.z - p.z)
	var spin := (sin(u * TAU * 2.0) * 0.5) if back else u * TAU * 2.0
	_hat.global_rotation = Vector3(0, face, spin)
	_hat.scale = Vector3.ONE * (1.0 + 0.5 * sin(u * PI) * (0.0 if back else 1.0))
	if u >= 1.0:
		_hat.visible = false
		if back:
			set_pose(_face("walk_calm", "walk"))
			_hop_v = 0.7
		_hat_anim = {}


## warm2 "모자로 부채질": hat in his hand, fanning.
func _fan_hat(on: bool) -> void:
	if _fan == null:
		var pp := world.puppet
		var tilt: Node3D = pp.get("_tilt")
		if tilt == null:
			return
		_fan = PaperCard.new()
		_fan.texture = CastSkins.texture("hat")
		_fan.height = TRAV_H * 0.17
		_fan.thickness = 0.006
		_fan.position = Vector3(TRAV_H * 0.3, TRAV_H * 0.78, 0.02)
		tilt.add_child(_fan)
	_fan.visible = on


func _drop_coat() -> void:
	if _fan:
		_fan.visible = false
	var d := _ground_dirs()
	var right: Vector2 = d[1]
	var tp := traveller_pos()
	var q := Vector2(tp.x, tp.z) + right * 0.26 + (d[0] as Vector2) * 0.08
	var base := Node3D.new()
	base.position = Vector3(q.x, world.ground.surface_y(q), q.y)
	base.rotation.y = d[2] + 0.2
	add_child(base)
	_coat_hinge = PopHinge.new()
	_coat_hinge.fold = -1
	_coat_hinge.weight = 0.6
	base.add_child(_coat_hinge)
	var c := PaperCard.new()
	c.texture = CastSkins.texture("coat")
	c.height = 0.1 * TRAV_H / 0.36
	c.thickness = 0.007
	_coat_hinge.add_child(c)
	extra_hinges.append(_coat_hinge)
	_coat_hinge.pop_up(0.35)


## He picks the coat up off the road and carries it over his arm (sw_n02, critic 1: don't leave it on the road).
func _pick_coat() -> void:
	if _coat_hinge:
		_coat_hinge.fold_down(0.0)
		var hb := _coat_hinge
		get_tree().create_timer(0.5).timeout.connect(func():
			if is_instance_valid(hb):
				hb.get_parent().visible = false)
	_hop_v = 0.6
	_carry_coat(true)


func _carry_coat(on: bool) -> void:
	if _carry == null:
		var tilt: Node3D = world.puppet.get("_tilt")
		if tilt == null:
			return
		_carry = PaperCard.new()
		_carry.texture = CastSkins.texture("coat", "arm")
		_carry.height = TRAV_H * 0.26
		_carry.thickness = 0.008
		_carry.position = Vector3(TRAV_H * 0.22, TRAV_H * 0.3, 0.018)
		tilt.add_child(_carry)
	_carry.visible = on
	if "arm_hold" in world.puppet:  # the arm with the coat over it does not swing
		world.puppet.set("arm_hold", 1 if on else -1)


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


static func _make_leaf_texture(base: Color) -> Texture2D:
	var w := 48
	var h := 64
	var img := Image.create(w, h, false, Image.FORMAT_RGBA8)
	var vein := Color("d8cf8c")
	for y in h:
		for x in w:
			var u := (float(x) + 0.5) / w * 2.0 - 1.0
			var v := (float(y) + 0.5) / h  # 0 top (tip) .. 1 bottom (stem)
			var half := sin(clampf(v, 0.0, 0.92) / 0.92 * PI) * 0.92
			var stem := v > 0.9 and absf(u) < 0.08
			if absf(u) < half or stem:
				var c := base.darkened(0.12 * absf(u))
				if absf(u) < 0.05 or (absf(absf(u) - (0.92 - v) * 0.6) < 0.04 and v > 0.2 and v < 0.85):
					c = vein
				img.set_pixel(x, y, c)
			else:
				img.set_pixel(x, y, Color(0, 0, 0, 0))
	return ImageTexture.create_from_image(img)


static func _make_drop_texture() -> Texture2D:
	var w := 32
	var h := 44
	var img := Image.create(w, h, false, Image.FORMAT_RGBA8)
	for y in h:
		for x in w:
			var u := (float(x) + 0.5) / w * 2.0 - 1.0
			var v := (float(y) + 0.5) / h
			var half := sqrt(maxf(0.0, 1.0 - pow((v - 0.66) / 0.34, 2.0))) if v > 0.32 else v / 0.32 * 0.55
			if absf(u) < half:
				img.set_pixel(x, y, Color("9fd0e6") if not (u < -0.1 and u > -0.4 and v > 0.55 and v < 0.75) else Color("eaf6fb"))
			else:
				img.set_pixel(x, y, Color(0, 0, 0, 0))
	return ImageTexture.create_from_image(img)


static func _make_ring_texture() -> Texture2D:
	var n := 128
	var img := Image.create(n, n, false, Image.FORMAT_RGBA8)
	for y in n:
		for x in n:
			var d := Vector2(x + 0.5 - n * 0.5, y + 0.5 - n * 0.5).length() / (n * 0.5)
			img.set_pixel(x, y, Color("e8f4f8") if d > 0.8 and d < 0.97 else Color(0, 0, 0, 0))
	return ImageTexture.create_from_image(img)


## sw_052 "퐁당": a splash of paper drops and rings on the water around his feet.
func _splash() -> void:
	var tp := _water_pos()
	for i in 9:
		var node := Node3D.new()
		node.top_level = true
		add_child(node)
		var c := PaperCard.new()
		c.texture = _drop_tex
		c.height = 0.035
		c.thickness = 0.003
		c.position = Vector3(0, -0.017, 0)
		node.add_child(c)
		var a := TAU * i / 9.0
		var start := tp + Vector3(cos(a) * 0.05, 0.02, sin(a) * 0.05)
		var to := tp + Vector3(cos(a) * randf_range(0.18, 0.3), 0.0, sin(a) * randf_range(0.18, 0.3))
		node.global_position = start
		_leaves.append([node, 0.0, randf_range(0.7, 1.0), start, to, randf_range(-2.0, 2.0), 0.0, randf_range(0.18, 0.3)])
	for i in 3:
		_rings.append([null, -0.35 * i, 1.4, 0.35 + 0.12 * i])


## His position on the ground under him (the water surface at the stream spot; the walker itself stays at road height).
func _water_pos() -> Vector3:
	var tp := traveller_pos()
	return Vector3(tp.x, world.ground.surface_y(Vector2(tp.x, tp.z)), tp.z)


func _step_rings(dt: float) -> void:
	if _sink_target > 0.0 and fmod(_t, 2.2) < dt and _rings.size() < 4:
		_rings.append([null, 0.0, 1.6, 0.4])
	for i in range(_rings.size() - 1, -1, -1):
		var r: Array = _rings[i]
		r[1] += dt
		if r[1] < 0.0:
			continue
		if r[0] == null:
			var m := MeshInstance3D.new()
			var q := QuadMesh.new()
			q.size = Vector2.ONE
			m.mesh = q
			var mat := StandardMaterial3D.new()
			mat.albedo_texture = _ring_tex
			mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
			mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
			m.material_override = mat
			m.top_level = true
			m.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			add_child(m)
			m.global_position = _water_pos() + Vector3(0, 0.003, 0)  # on the water surface around his legs
			m.rotation.x = -PI * 0.5
			r[0] = m
		var u: float = r[1] / r[2]
		var m2 := r[0] as MeshInstance3D
		if u >= 1.0:
			m2.queue_free()
			_rings.remove_at(i)
			continue
		m2.scale = Vector3.ONE * lerpf(0.08, float(r[3]), sqrt(u))
		(m2.material_override as StandardMaterial3D).albedo_color = Color(1, 1, 1, 1.0 - u)


func _spawn_leaves(n: int, power := 1.0) -> void:
	var from := _card_centre(wind)
	var dw := _downwind()
	var trav := traveller_pos() + Vector3(0, TRAV_H * 0.5, 0)
	for i in n:
		var node := Node3D.new()
		node.top_level = true
		add_child(node)
		var c := PaperCard.new()
		c.texture = _leaf_tex[randi() % _leaf_tex.size()]
		c.height = [0.045, 0.055, 0.07][randi() % 3]
		c.thickness = 0.003
		c.position = Vector3(0, -c.height * 0.5, 0)
		node.add_child(c)
		var start := from.lerp(trav, randf_range(0.1, 0.6)) + Vector3(randf_range(-0.2, 0.2), randf_range(-0.15, 0.2), randf_range(-0.2, 0.2))
		var to := trav + dw * randf_range(0.9, 1.8) * power + Vector3(randf_range(-0.4, 0.4), randf_range(-0.1, 0.4), randf_range(-0.3, 0.3))
		node.global_position = start
		_leaves.append([node, 0.0, randf_range(1.4, 2.2) / maxf(power, 0.5), start, to, randf_range(-6.0, 6.0), randf() * TAU, 0.15])


func _step_leaves(dt: float) -> void:
	for i in range(_leaves.size() - 1, -1, -1):
		var l: Array = _leaves[i]
		var n: Node3D = l[0]
		l[1] += dt
		var u: float = l[1] / l[2]
		if u >= 1.0:
			n.queue_free()
			_leaves.remove_at(i)
			continue
		var p: Vector3 = (l[3] as Vector3).lerp(l[4], u)
		p.y += sin(u * PI) * float(l[7]) + sin(l[1] * 7.0 + l[6]) * 0.02
		n.global_position = p
		n.rotation = Vector3(sin(l[1] * 5.0 + l[6]) * 0.8, l[1] * 2.0, l[1] * float(l[5]))
		n.scale = Vector3.ONE * clampf(minf(u * 6.0, (1.0 - u) * 5.0), 0.01, 1.0)
