extends TaleHandler
## 「해와 바람」 effects (moved out of SpreadStage, behaviour unchanged): the wind's gusts and blowing, sun / wind
## expression prints, the hat blown off and back, the coat opened / dropped / carried, the hat fan, warm light,
## leaves, the stream bank spot with the splash and ripples, the traveller's shiver / startle / shove.

var gusts: WindGusts
var sun: SkyHanger
var wind: SkyHanger
var wind_state := "default"
var sun_state := "default"
var stream_offset := -1.0

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
var _coat_hinge: PopHinge
var _carry: PaperCard  ## coat over the arm
var _fan: PaperCard  ## hat in hand, fanning
var _rings: Array = []  ## [node, age, life, max]
var _bank := Vector3.ZERO
const BANK_MARGIN := 0.13  ## stream spot: min distance from the felt cut edge (both feet + ripples on the water)
var _t := 0.0


func _trav_h() -> float:
	return stage.trav_h


func setup() -> void:
	sun = stage.hanger("sun")
	wind = stage.hanger("wind")
	gusts = WindGusts.new()
	gusts.name = "Gusts"
	gusts.hanger = wind
	gusts.curl_height = 0.11
	stage.add_child(gusts)
	_sun_light = OmniLight3D.new()
	_sun_light.light_color = Color(1.0, 0.78, 0.45)
	_sun_light.omni_range = 2.6
	_sun_light.light_energy = 0.0
	_sun_light.shadow_enabled = false
	stage.add_child(_sun_light)


func build_async() -> void:
	await _find_stream()
	await stage.slicer_tick()
	var rig := stage.world.rig
	if rig.key:
		_key_e0 = rig.key.light_energy
		_key_c0 = rig.key.light_color
	if _leaf_tex.is_empty():
		for col in [Color("7f9a4a"), Color("c99a3e"), Color("b8643a")]:
			_leaf_tex.append(_make_leaf_texture(col))
		_drop_tex = _make_drop_texture()
		_ring_tex = _make_ring_texture()


func traveller_pos() -> Vector3:
	return stage.traveller_pos()


func _find_stream() -> void:
	var world := stage.world
	var c := world.path.curve
	var L := c.get_baked_length()
	var best := INF
	var o := 0.0
	while o < L:
		await stage.slicer_tick()
		var p := world.path.global_transform * c.sample_baked(o)
		var d := absf(world.ground.stream_distance(Vector2(p.x, p.z)) + world.ground.stream_width * 0.5)
		if d < best:
			best = d
			stream_offset = o
		o += 0.05
	var here := world.walker.offset
	stream_offset = clampf(stream_offset + 0.55 * signf(here - stream_offset if absf(here - stream_offset) > 0.01 else -1.0), 0.0, L)
	# A spot IN the water channel (2026-11-18 user: "he sinks his feet into the ground, not the water"): a point inside
	# the real cut polygon (the felt sheet's hole, see GroundLayers) at least BANK_MARGIN from its edge, so both feet
	# and the ripples are on the recessed water and the bank lip is behind/beside him; the stage drops him to the water
	# surface there (ground_dy) and the opaque water hides his sunk legs.
	var p0 := world.path.global_transform * c.sample_baked(stream_offset)
	var to_cam: Vector2 = stage.ground_dirs()[0]
	var g := world.ground
	var poly: PackedVector2Array = g.get("_stream_poly")
	var bs := INF
	_bank = p0
	for ai in 48:
		await stage.slicer_tick()
		var ang := TAU * ai / 48.0
		for ri in 14:
			var r := 0.3 + ri * 0.06
			var q := Vector2(p0.x, p0.z) + Vector2(cos(ang), sin(ang)) * r
			if poly.size() < 3 or not Geometry2D.is_point_in_polygon(q, poly):
				continue
			var e := _poly_edge_dist(poly, q)
			if e < BANK_MARGIN or g.path_distance(q) < 0.3:
				continue
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


## Leave the road to the stream bank spot (straight line), where he sits with his feet in the water.
func walk_to_place(place: String) -> bool:
	if place != "stream":
		return false
	var w := stage.world.walker
	w.path = null
	stage.walk_goal = _bank
	w.walk_to(_bank)
	return true


func stroll_mod(dt: float, pp: PaperPuppet) -> float:
	# Weather: pushing into the wind (slow, short steps, leaning in); heat (slowing as he gets hotter).
	var k := 1.0
	if _blowing:
		k = 0.45
	elif stage.shiver > 0.3:
		k = 0.7
	k *= 1.0 - 0.45 * clampf(_warm, 0.0, 1.0)
	if "front_lift" in pp:  # struggling steps in the wind: low shuffling lift, heavier roll; light steps otherwise
		var struggle := 1.0 if _blowing else (0.5 if stage.shiver > 0.3 else 0.0)
		var e := 1.0 - exp(-3.0 * dt)
		pp.set("front_lift", lerpf(float(pp.get("front_lift")), 1.0 - 0.55 * struggle, e))
		pp.set("front_roll_deg", lerpf(float(pp.get("front_roll_deg")), 0.6 + 0.6 * struggle, e))
		pp.set("front_arm_swing", lerpf(float(pp.get("front_arm_swing")), 1.0 - 0.7 * struggle, e))
		pp.set("front_hunch", lerpf(float(pp.get("front_hunch")), struggle, e))  # hunched, arms tucked to the coat
		# heat: slow, droopy while he still has the coat on; light again once it is off
		var cool := pp.pose.begins_with("shirt") or pp.pose.begins_with("relieved")
		pp.set("front_droop", lerpf(float(pp.get("front_droop")), clampf(_warm, 0.0, 1.0) * (0.25 if cool else 1.0), e))
	if "push_lean_deg" in pp:
		pp.set("push_lean_deg", lerpf(float(pp.get("push_lean_deg")), 2.5 if _blowing else (1.0 if stage.shiver > 0.3 else 0.0), 1.0 - exp(-3.0 * dt)))
	return k


func wiggle(target: String) -> bool:
	match target:
		"sun":
			sun.puff(1.16)
			sun.push(Vector3(0, 0.25, 0))
			_wiggle["sun"] = 0.4
			return true
		"wind":
			wind.puff(1.16)
			wind.push(Vector3(randf_range(-0.2, 0.2), 0.2, 0))
			_wiggle["wind"] = 0.4
			return true
	return false


func set_blowing(on: bool, power: float) -> void:
	_blowing = on
	_blow_power = power


func gentle_gust() -> void:
	gusts.gust_every = 0.45
	gusts.blow(traveller_pos() + Vector3(0, _trav_h() * 0.6, 0), 0.8)
	_sway_target = 2.0
	_blow_t = 0.9
	wind_state = "blow"
	wind.puff(1.08)
	_spawn_leaves(3, 0.5)


func _set_pose(p: String) -> void:
	stage.set_pose(p)


func fx(name: String) -> bool:
	if name.begins_with("_pose:"):
		if _fan and name.substr(6) != "walk_nohat":
			_fan.visible = false
		return true
	match name:
		"gentle_gust":
			gentle_gust()
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
			stage.hop_v = 1.1
		"wind_puff":
			sun_state = "default"
			wind_state = "blow"
			wind.puff(1.22)
			_wiggle["wind_relax"] = 1.4
		"leaves":
			_spawn_leaves(14)
			stage.shot_to("story")
		"hat_off":
			# "앗, 내 모자!": startle hop, wide eyes, hands up to his bare head; he stops a moment.
			_hat_off()
			_set_pose(_face("surprised_nohat", "walk_nohat"))
			stage.hop_v = 1.25
			stage.pause = 2.2
		"flap":
			_spawn_leaves(8)
			_set_pose(_face("cold", "walk_nohat"))
			stage.shiver = 0.7
		"clutch":
			# "으으, 추워!": hugging himself (no hat: the hat is gone), teeth chattering, a hard shiver.
			_set_pose(_face("cold", "hold"))
			stage.shiver = 1.3
			stage.hop_v = 0.5
		"gale":
			_spawn_leaves(16)
			stage.shiver = 1.6
			stage.shove()
		"wind_tired":
			_blowing = false
			gusts.tire()
			wind_state = "tired"
			_sway_target = 1.0
			stage.shiver = 0.25  # still shivering a little; dies away after the hat comes back
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
			_set_pose(_face("warm", "walk"))
		"warm2":
			# "아이, 더워!": hat off in his hand, fanning, tongue out, dripping.
			_warm_target = 0.75
			sun.puff(1.25)
			if _has_pose("hot_fan"):
				_set_pose("hot_fan")  # the hat-in-hand is a hinged arm part; CastPuppet fans it
			else:
				_set_pose("walk_nohat")
				_fan_hat(true)
		"coat_off":
			# "훌러덩!": he stops, the coat drops, a relieved breath.
			_warm_target = 1.0
			sun.puff(1.3)
			_set_pose(_face("relieved", "shirt"))
			_drop_coat()
			stage.pause = 999.0
			stage.shot_to("close")  # punch-in on the payoff (no tap is asked for while it lasts)
		"walk_on":
			# after the coat-off moment: picks the coat up and walks on carrying it.
			_pick_coat()
			_set_pose(_face("shirt_calm", "shirt"))
			stage.pause = 0.6
			stage.stroll_speed = 0.2  # coat off, cool again: back to an easy pace (the heat factor still slows it)
		"sun_wins":
			sun_state = "proud"
			sun.puff(1.25)
			_wiggle["sun"] = 0.8
			_face_each_other(0.35)
			stage.shot_to("story")
		"pick_coat":
			_pick_coat()
		"carry_coat":
			_carry_coat(true)
		"sun_glow":
			_warm_target = 1.0
			sun.puff(1.2)
		"quiz_wrong":
			gusts.blow(traveller_pos() + Vector3(0, _trav_h() * 1.3, 0), 1.2)
			wind_state = "blow"
			_blow_t = 1.2
			_sway_target = 3.0
			stage.shiver = 1.4
			_wiggle["shiver_off"] = 1.4
			_spawn_leaves(8)
		"quiz_right":
			_warm_target = 1.0
			sun_state = "beaming"
			sun.puff(1.3)
			_wiggle["sun"] = 0.8
		"splash":
			stage.sink_target = _trav_h() * 0.13  # shallow stream: the water comes up to his shins
			_splash()
		"cool":
			_set_pose(_face("relieved", "shirt"))
		"friends":
			sun_state = "beaming"
			wind_state = "default"
			sun.puff(1.12)
			wind.puff(1.12)
			_face_each_other(0.5)
			stage.pull_t = 0.22
			sun.push(Vector3(0.3, 0.15, 0))
			wind.push(Vector3(-0.3, 0.15, 0))
		_:
			return false
	return true


func _has_pose(p: String) -> bool:
	var pp := stage.world.puppet
	if pp is CastPuppet:
		return (pp as CastPuppet).has_pose(p)
	return false


## Expression pose when the cast skin has it, else the old pose (legacy puppet).
func _face(p: String, fallback: String) -> String:
	return p if _has_pose(p) else fallback


func _face_each_other(a: float) -> void:
	stage._sky[0]["yaw_t"] = -a  # sun (left) turns right, toward the wind
	stage._sky[1]["yaw_t"] = a


func step(dt: float) -> void:
	_t += dt
	var trav := traveller_pos()
	var world := stage.world
	var rig := world.rig
	# Wind blowing while held: re-trigger gusts toward the traveller, the meadow leans downwind, cheeks puffed.
	if _blowing:
		if not gusts._blow_left > 0.05:
			gusts.gust_every = 0.28 / clampf(_blow_power, 0.5, 2.0)
			gusts.blow(trav + Vector3(0, _trav_h() * 1.3, 0), 0.6)  # over his head: the curls kept covering his face
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
				stage.shiver = 0.0
	# Warm light: the key warms and brightens, a warm glow lamp sits at the sun card.
	_warm = lerpf(_warm, _warm_target, 1.0 - exp(-1.6 * dt))
	if rig.key:
		rig.key.light_energy = _key_e0 * (1.0 + 0.3 * _warm)
		rig.key.light_color = _key_c0.lerp(Color(1.0, 0.76, 0.48), 0.5 * _warm)
	_sun_light.global_position = trav.lerp(stage.card_centre(sun), 0.5) + Vector3(0, 0, 0.3)
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
	stage.add_child(_hat)
	var c := PaperCard.new()
	c.texture = CastSkins.texture("hat")
	c.height = 0.1 * _trav_h() / 0.36
	c.thickness = 0.006
	c.position = Vector3(0, -c.height * 0.5, 0)
	_hat.add_child(c)


## sw_017 "모자가 훨훨 날아갔어요": the hat whirls up and away off the page (critic 1), back in sw_024.
func _hat_off() -> void:
	_hat_card()
	var head := traveller_pos() + Vector3(0, _trav_h() * 0.95, 0)
	var away := traveller_pos() + _downwind() * 1.5 + Vector3(0, 1.5, 0)
	_hat.visible = true
	_hat.global_position = head
	_hat_anim = {"from": head, "to": away, "t": 0.0, "dur": 2.2, "arc": 0.35, "back": false}


func _hat_back() -> void:
	_hat_card()
	var head := traveller_pos() + Vector3(0, _trav_h() * 0.95, 0)
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
	var yw := deg_to_rad(stage.world.rig.yaw_deg)
	var side := Vector3(cos(yw), 0, -sin(yw))
	p += side * sin(u * TAU * (2.0 if back else 1.0)) * 0.12 * (1.0 - u if back else u)
	_hat.global_position = p
	var cam := stage.camera()
	var face := atan2(cam.global_position.x - p.x, cam.global_position.z - p.z)
	var spin := (sin(u * TAU * 2.0) * 0.5) if back else u * TAU * 2.0
	_hat.global_rotation = Vector3(0, face, spin)
	_hat.scale = Vector3.ONE * (1.0 + 0.5 * sin(u * PI) * (0.0 if back else 1.0))
	if u >= 1.0:
		_hat.visible = false
		if back:
			_set_pose(_face("walk_calm", "walk"))
			stage.hop_v = 0.7
		_hat_anim = {}


## warm2 "모자로 부채질": hat in his hand, fanning.
func _fan_hat(on: bool) -> void:
	if _fan == null:
		var pp := stage.world.puppet
		var tilt: Node3D = pp.get("_tilt")
		if tilt == null:
			return
		_fan = PaperCard.new()
		_fan.texture = CastSkins.texture("hat")
		_fan.height = _trav_h() * 0.17
		_fan.thickness = 0.006
		_fan.position = Vector3(_trav_h() * 0.3, _trav_h() * 0.78, 0.02)
		tilt.add_child(_fan)
	_fan.visible = on


func _drop_coat() -> void:
	if _fan:
		_fan.visible = false
	var d := stage.ground_dirs()
	var right: Vector2 = d[1]
	var tp := traveller_pos()
	var q := Vector2(tp.x, tp.z) + right * 0.26 + (d[0] as Vector2) * 0.08
	var base := Node3D.new()
	base.position = Vector3(q.x, stage.world.ground.surface_y(q), q.y)
	base.rotation.y = d[2] + 0.2
	stage.add_child(base)
	_coat_hinge = PopHinge.new()
	_coat_hinge.fold = -1
	_coat_hinge.weight = 0.6
	base.add_child(_coat_hinge)
	var c := PaperCard.new()
	c.texture = CastSkins.texture("coat")
	c.height = 0.1 * _trav_h() / 0.36
	c.thickness = 0.007
	_coat_hinge.add_child(c)
	stage.extra_hinges.append(_coat_hinge)
	_coat_hinge.pop_up(0.35)


## He picks the coat up off the road and carries it over his arm (sw_n02, critic 1: don't leave it on the road).
func _pick_coat() -> void:
	if _coat_hinge:
		_coat_hinge.fold_down(0.0)
		var hb := _coat_hinge
		get_tree().create_timer(0.5).timeout.connect(func():
			if is_instance_valid(hb):
				hb.get_parent().visible = false)
	stage.hop_v = 0.6
	_carry_coat(true)


func _carry_coat(on: bool) -> void:
	if _carry == null:
		var tilt: Node3D = stage.world.puppet.get("_tilt")
		if tilt == null:
			return
		_carry = PaperCard.new()
		_carry.texture = CastSkins.texture("coat", "arm")
		_carry.height = _trav_h() * 0.26
		_carry.thickness = 0.008
		_carry.position = Vector3(_trav_h() * 0.22, _trav_h() * 0.3, 0.018)
		tilt.add_child(_carry)
	_carry.visible = on
	if "arm_hold" in stage.world.puppet:  # the arm with the coat over it does not swing
		stage.world.puppet.set("arm_hold", 1 if on else -1)


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
		stage.add_child(node)
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
	return Vector3(tp.x, stage.world.ground.surface_y(Vector2(tp.x, tp.z)), tp.z)


func _step_rings(dt: float) -> void:
	if stage.sink_target > 0.0 and fmod(_t, 2.2) < dt and _rings.size() < 4:
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
			stage.add_child(m)
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
	var from := stage.card_centre(wind)
	var dw := _downwind()
	var trav := traveller_pos() + Vector3(0, _trav_h() * 0.5, 0)
	for i in n:
		var node := Node3D.new()
		node.top_level = true
		stage.add_child(node)
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
