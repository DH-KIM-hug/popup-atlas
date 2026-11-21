extends TaleHandler
## 「사탕 마녀의 핼러윈」 effects and tale verbs (TaleHandler, 2026-11-20 phase 2).
## The stage builds the street, the shop (house with a body + the room inside its footprint) and the cast from
## script.json; this handler adds what only this tale does:
##  - the invitations fluttering down (tap to catch), the shop lighting up, the fire under the pot (three flames),
##  - the shelf of nine ingredients (tap targets) and the `brew` verb: two picks fly into the pot, the liquid takes
##    their colours (a spinning swirl band per colour), the witch stirs by magic, POOF, the candy lands at Dahyun's
##    hands, she eats it and transforms; the result's action plays outside (camera follows her out of the door),
##  - the six transformation actions (roll, waddle, swim, hop, glow, fly), the ghost candy round, the parade's little
##    ghost, the candy fountain and the finale transformations.
## Lines are played through the runner (_say) so captions, faces (line expr) and SEG logs stay generic. Before each
## brew the planned line list is printed (PLAN <step> <ids>) for tools/story/check_lines.py (branch-aware guard).

const COLORS := {"r": Color(0.86, 0.22, 0.2), "y": Color(0.98, 0.78, 0.2), "b": Color(0.2, 0.42, 0.9),
	"water": Color(0.45, 0.72, 0.95), "red": Color(0.86, 0.22, 0.2), "yellow": Color(0.98, 0.78, 0.2),
	"blue": Color(0.2, 0.42, 0.9), "orange": Color(0.97, 0.5, 0.12), "purple": Color(0.42, 0.3, 0.7),
	"green": Color(0.38, 0.72, 0.3), "black": Color(0.08, 0.07, 0.09)}
const SHELF_ORDER := ["snot", "firetruck", "ladybug", "lantern", "chickfart", "duck", "poo", "fish", "wave"]
const SFX_ING := {"snot": "wc.drip", "firetruck": "wc.siren", "ladybug": "wc.buzz", "lantern": "wc.chime",
	"chickfart": "wc.kazoo", "duck": "wc.quack", "poo": "wc.plop", "fish": "wc.splash", "wave": "wc.wave"}

var _t := 0.0
var _tex := {}
var _flyers: Array = []  ## {node, age, life, from, to, arc, keep, spin}
var _floaters: Dictionary = {}  ## name -> {node, base, ph, amp}
var _ings: Dictionary = {}  ## ingredient key -> Node3D (card on the shelf)
var _picking := false
var _liquid: MeshInstance3D
var _swirls: Array = []  ## MeshInstance3D bands
var _swirl_speed := 0.6
var _glides: Dictionary = {}  ## role -> {pts, spd, mode, pose, dist}
var _flap := false
var _rolling := ""
var _kid_light: OmniLight3D
var _flames: Array = []
var _candy: Node3D
var _candies: Array = []
var _ghost: Node3D
var _ghost_follow := ""
var _seen_results: Array = []
var _forced: Array = []
var _track: Node3D  ## the camera follows this node (an invitation in flight, the ghost roaming)
var _shop_glow := -1.0  ## animated glow of the shop (lights on)
var _dim := 1.0  ## street lights factor (pumpkin glow)
var _dim_t := 1.0


func setup() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--wc-results="):  # recordings / branch checks: force the results of the rounds
			_forced = Array(a.get_slice("=", 1).split(","))


func build_async() -> void:
	var first := str(stage.beat.get("id", ""))
	if first in ["", "cover", "invite"]:
		_set_shop_lit(0.0)
	_make_liquid()
	if first in ["round1", "round2", "ghost_candy", "parade", "finale"]:
		_shelf_now(false)
		_fire_now(3)


func enter_beat(b: Dictionary) -> void:
	if str(b.get("id", "")) == "shelf" and _ings.is_empty():
		pass


# ------------------------------------------------------------------ helpers

func _texid(id: String) -> Texture2D:
	if not _tex.has(id):
		var e := SpreadStage.atlas_entry(id)
		_tex[id] = load("res://" + str(e.get("path", ""))) if not e.is_empty() else null
	return _tex[id]


func _card(id: String, h: float) -> Node3D:
	var tex := _texid(id)
	var node := Node3D.new()
	node.top_level = true
	stage.add_child(node)
	if tex == null:
		return node
	var c := PaperCard.new()
	c.texture = tex
	c.height = h
	c.thickness = clampf(h * 0.04, 0.002, 0.008)
	node.add_child(c)
	return node


func _yaw() -> float:
	return deg_to_rad(stage.world.rig.yaw_deg)


func _sfx(id: String, at: Variant = null) -> void:
	if SoundDirector.current:
		SoundDirector.current.play(id, at)


func _a(role: String) -> StoryActor:
	return stage.actor(role)


func _sp(nm: String) -> SetPiece:
	return stage.set_piece(nm)


func _right() -> Vector3:
	return stage.dir_vec("right")


func _toward() -> Vector3:
	return stage.dir_vec("toward")


## Along the shop's front (its own right), for moves inside the room.
func _sx() -> Vector3:
	var sp := _sp("shop")
	return sp.global_transform.basis.x.normalized() if sp else _right()


## Out of the shop's front (the shop faces the road, turned from the camera frame).
func _out() -> Vector3:
	var sp := _sp("shop")
	return sp.global_transform.basis.z.normalized() if sp else _toward()


## A card flying from `from` to `to` on an arc, facing the camera; keep > 0 holds it at the end (then it is removed
## with _drop_flyer or after keep seconds).
func fly(id: String, from: Vector3, to: Vector3, h: float, life := 0.8, arc := 0.15, keep := 0.0, spin := 0.0) -> Node3D:
	var node := _card(id, h)
	node.global_position = from
	node.scale = Vector3.ONE * 0.05
	_flyers.append({"node": node, "age": 0.0, "life": life, "from": from, "to": to, "arc": arc, "keep": keep,
		"spin": spin, "ph": randf() * TAU})
	return node


func _drop_flyer(n: Node3D) -> void:
	for f: Dictionary in _flyers:
		if is_instance_valid(f["node"]) and f["node"] == n:
			f["keep"] = minf(float(f["keep"]), float(f["age"]) - float(f["life"]) + 0.25)
			return
	if is_instance_valid(n):
		n.queue_free()


func _poof(at: Vector3, big := 1.0) -> void:
	fly("story_wc_pot_16", at, at + Vector3.UP * 0.06 * big, 0.12 * big, 0.45, 0.02, 0.15)
	for k in 4:
		var d := _right().rotated(Vector3.UP, k * PI * 0.5 + 0.4) * 0.12 * big
		fly("story_wc_pot_19", at, at + d + Vector3.UP * (0.08 + 0.04 * k) * big, 0.04 * big, 0.5, 0.05, 0.0, 6.0)
	_sfx("wc.boing", at)


# ------------------------------------------------------------------ tap targets (invitations, ingredients)

func targets() -> Array:
	var out: Array = []
	for k in _floaters:
		if str(k).begins_with("invite_"):
			out.append(k)
	if _picking:
		out.append_array(_ings.keys())
	return out


func target_point(t: String) -> Variant:
	if _floaters.has(t):
		return (_floaters[t]["node"] as Node3D).global_position + Vector3.UP * 0.03
	if _ings.has(t):
		return (_ings[t] as Node3D).global_position + Vector3.UP * 0.035
	return null


func target_radius(t: String) -> float:
	var p: Variant = target_point(t)
	if p == null:
		return -1.0
	var cam := stage.camera()
	var a := cam.unproject_position(p)
	var b := cam.unproject_position((p as Vector3) + Vector3.UP * 0.05)
	return maxf(90.0 if t.begins_with("invite") else 56.0, a.distance_to(b) * 1.4)


func wiggle(t: String) -> bool:
	if _ings.has(t) or _floaters.has(t):
		return true
	return false


# ------------------------------------------------------------------ fx by name

func fx(name: String) -> bool:
	var parts := name.split(":")
	match parts[0]:
		"invites_flutter":
			_invites()
		"catch":
			_catch(parts[1] if parts.size() > 1 else "kid")
		"shop_lights_on":
			_shop_glow = 0.0
			_sfx("wc.chime")
		"door_open":
			if _sp("shop"):
				_sp("shop").open_door(true)
				_sfx("door.open")
		"door_close":
			if _sp("shop"):
				_sp("shop").open_door(false)
				_sfx("door.shut")
		"inside_view":
			stage.shot_to("room", "in_focus", {"rate": 1.5})
			if SoundDirector.current:
				SoundDirector.current.set_bed("room", 1.5)
		"outside_view":
			stage.shot_to("door_cam", "door_view", {"rate": 1.5})
			if SoundDirector.current:
				SoundDirector.current.set_bed("@light", 1.5)
		"flame_s":
			_fire_now(1)
			_sfx("fire.ignite")
		"flame_m":
			_fire_now(2)
			_sfx("wc.flame")
		"flame_l":
			_fire_now(3)
			_sfx("wc.flame")
		"pot_water":
			_set_liquid(["water"])
			_sfx("wc.bubble")
		"pot_clear":
			_set_liquid(["water"])
			_sfx("wc.wave")
		"shelf_pop":
			_shelf_now(true)
		"candies_to_all":
			for r in ["witch", "cat", "rabbit", "bear", "fox"]:
				var a := _a(r)
				if a:
					fly("story_wc_candies_06", _pot_mouth(), a.centre() + Vector3.UP * 0.05, 0.04, 0.6, 0.15, 0.2)
			_sfx("wc.candy_pop")
		"candy_fountain":
			_fountain()
		"poof":
			pass
		"all_transform":
			for q in [["kid", "tf_strawberry"], ["cat", "tf_fish"], ["witch", "tf_pumpkin"]]:
				var a := _a(str(q[0]))
				if a:
					_poof(a.centre())
					a.set_pose(str(q[1]))
					a.hop_v = 0.8
		"all_back":
			for r in ["kid", "witch", "cat", "rabbit", "bear", "fox"]:
				var a := _a(r)
				if a:
					_poof(a.centre(), 0.8)
					a.set_pose("sit" if r == "cat" else "calm")
			for c in _candies:
				if is_instance_valid(c):
					(c as Node3D).queue_free()
			_candies.clear()
		"witch_wave":
			var w := _a("witch")
			if w:
				w.set_pose("welcome")
				w.hop_v = 0.8
			_sfx("wc.giggle_bells")
		"ghost_glimpse_1":
			_glimpse(1)
		"ghost_glimpse_2":
			_glimpse(2)
		"ghost_glimpse_4":
			_glimpse(4)
		"float_all":
			_floating = true
		"black_mouth":  # black_mouth:witch / black_mouth:others (match is on the part before the colon)
			var who := ["witch"] if parts.size() > 1 and parts[1] == "witch" else ["cat", "rabbit", "bear", "fox"]
			_black_mouth(who, true)
			for r in who:
				_black_expected[r] = true
		"ghost_sneak":
			_parade_ghost_start()
		"ghost_tagalong":
			_ghost = _ghost_card()
			_g = null  # from here on the parade code moves it (it follows the last marcher)
			_ghost_follow = "fox"
			var f := _a("fox")
			_ghost.global_position = (f.global_position if f else stage.spot_point("door")) + Vector3.UP * 0.12
			_ghost.scale = Vector3.ONE * 0.85
		"ghost_vanish":
			for gv in [_ghost, _g]:
				if gv and is_instance_valid(gv):
					_poof(gv.global_position + Vector3.UP * 0.1)
					_sfx("wc.vanish")
					gv.queue_free()
			_ghost = null
			_g = null
			_pg_on = false
			# 뿅: the ghost-candy mouths wear off as the little ghost goes
			for r in ["kid", "witch", "cat", "rabbit", "bear", "fox"]:
				var a := _a(r)
				if a:
					_poof(a.centre(), 0.7)
					a.pose = "sit" if r == "cat" else "calm"
			_black_mouth(["kid", "witch", "cat", "rabbit", "bear", "fox"], false)
		_:
			if parts[0] == "poof" and parts.size() > 1:
				var a := _a(parts[1])
				if a:
					_poof(a.centre())
				return true
			return false
	return true


# ------------------------------------------------------------------ invitations

## v3 (user: "초대장이 날아왔으면 좋겠고"): four pumpkin invitations ride the wind in from the far end of the street,
## fluttering along curving paths (paper flips and tumbles), the camera following the first; they settle hovering over
## Dahyun and the friends, big enough to tap.
func _invites() -> void:
	var roles := ["rabbit", "bear", "fox", "kid"]
	var far := stage.spot_point("road_shop") + Vector3.UP * 1.1 - _right() * 0.4
	for i in roles.size():
		var a := _a(roles[i])
		if a == null:
			continue
		var hover := a.global_position + Vector3.UP * (a.puppet.height * 1.3)
		var n := _card("story_wc_ingredients_11", 0.12)
		n.rotation.y = _yaw()
		var nm := "invite_%d" % (i + 1) if i < 3 else "invite_kid"
		var st := far + _right() * (0.25 * i - 0.3) + Vector3.UP * 0.15 * i
		n.global_position = st
		var mid := st.lerp(hover, 0.5) + _right() * (0.7 if i % 2 == 0 else -0.7) + Vector3.UP * 0.35
		_floaters[nm] = {"node": n, "base": hover, "ph": i * 1.3, "amp": 0.02, "from": st, "mid": mid,
			"t": -0.45 * i, "dur": 4.6, "flutter": 0.0}
	_track = (_floaters["invite_1"]["node"] as Node3D) if _floaters.has("invite_1") else null
	stage.shot_to("medium", null, {"rate": 1.6})  # close on the card in flight
	_sfx("wc.flutter")


func _catch(role: String) -> void:
	var nm := ""
	for k in _floaters:
		if str(k).begins_with("invite_"):
			var idx := {"rabbit": "invite_1", "bear": "invite_2", "fox": "invite_3", "kid": "invite_kid"}
			if str(k) == str(idx.get(role, "")):
				nm = str(k)
	var a := _a(role)
	if nm == "" or a == null:
		return
	var n: Node3D = _floaters[nm]["node"]
	var from := n.global_position
	_floaters.erase(nm)
	n.queue_free()
	# caught: the card opens toward the camera so the invitation reads (the pot and the candy on it), then is kept
	var cam := stage.camera()
	# beside the shoulder, a little toward the camera (never over a face)
	var side := cam.global_transform.basis.x * (0.12 if role in ["bear", "kid"] else -0.12)
	var to := a.centre() + side + (cam.global_position - a.centre()).normalized() * 0.08 + Vector3.UP * 0.02
	fly("story_wc_ingredients_10", from, to, 0.09, 0.45, 0.04, 1.4)
	a.set_pose("excited" if role == "kid" else "cheer")
	a.hop_v = 0.7
	_sfx("ui.pop", a.centre())


# ------------------------------------------------------------------ shop light / fire / pot

func _set_shop_lit(v: float) -> void:
	var sp := _sp("shop")
	if sp == null:
		return
	for c in sp.find_children("*", "OmniLight3D", true, false):
		(c as OmniLight3D).light_energy = 0.7 * v
	for c: PaperCard in sp.band_cards:
		stage._glow_pending.append([c, 0.9 * v])


func _fire_now(n: int) -> void:
	var hp := stage.spot_point("in_pot")
	for f in _flames:
		if is_instance_valid(f):
			(f as Node3D).queue_free()
	_flames.clear()
	var ids := ["story_wc_pot_13", "story_wc_pot_14", "story_wc_pot_15"]
	if n > 0:
		var f := _card(ids[n - 1], [0.045, 0.06, 0.075][n - 1])
		f.global_position = hp + _out() * 0.02 + Vector3.UP * 0.005
		f.rotation.y = _sp("shop").global_rotation.y if _sp("shop") else _yaw()
		_flames.append(f)
	var pot := _sp("pot")
	if pot:
		for c in pot.find_children("*", "OmniLight3D", true, false):
			(c as OmniLight3D).light_energy = 0.15 + 0.25 * n
	if n >= 1 and _sp("logs") and _sp("logs").shown == 0:
		stage.fx("up:logs")


func _pot_mouth() -> Vector3:  # the centre of the drawn opening (steam, drops, candies start here)
	var pot := _sp("pot")
	if pot == null:
		return stage.spot_point("in_pot") + Vector3.UP * 0.2
	return _pot_open()[0]


## v6 (user: "솥에서 물이 끓는 거랑 김 나오는 거랑 ... 솥 모양이랑 안 맞아"): the pot is a flat card with its opening drawn
## at the top (measured on story_wc_pot_00: an ellipse centred at 89.3 % of the card height, half axes 32.6 % of its
## width and 7.7 % of its height). The liquid is an elliptical card laid exactly over that drawn opening (a hair in
## front of the pot card, facing like it, 90 % of the opening so the dark rim shows round it); the colour swirls spin
## inside the same ellipse; steam and bubbles start from its centre.
const POT_OPEN := [0.0, 0.893, 0.326, 0.077]  ## centre x (of width), centre y (of height), half width, half height
var _liq_root: Node3D
var _liq_mat: StandardMaterial3D
static var _ell_tex: Texture2D


func _pot_open() -> Array:  # [centre (world), basis x, basis z, rx, ry]
	var pot := _sp("pot")
	var bx := pot.global_transform.basis.x.normalized()
	var bz := pot.global_transform.basis.z.normalized()
	var c := pot.global_position + bx * POT_OPEN[0] * pot.width + Vector3.UP * POT_OPEN[1] * pot.height + bz * 0.004
	return [c, bx, bz, POT_OPEN[2] * pot.width, POT_OPEN[3] * pot.height]


func _make_liquid() -> void:
	var pot := _sp("pot")
	if pot == null:
		return
	if _ell_tex == null:
		var n := 128
		var img := Image.create(n, n, false, Image.FORMAT_RGBA8)
		for y in n:
			for x in n:
				var d := Vector2(x + 0.5 - n * 0.5, y + 0.5 - n * 0.5).length() / (n * 0.5)
				img.set_pixel(x, y, Color(1, 1, 1, clampf((1.0 - d) * 20.0, 0.0, 1.0)))
		_ell_tex = ImageTexture.create_from_image(img)
	var o := _pot_open()
	_liq_root = Node3D.new()
	_liq_root.top_level = true
	stage.add_child(_liq_root)
	_liq_root.global_position = o[0]
	_liq_root.global_rotation = Vector3(0, pot.global_rotation.y, 0)
	var q := QuadMesh.new()
	q.size = Vector2(o[3] * 2.0 * 0.9, o[4] * 2.0 * 0.9)
	_liquid = MeshInstance3D.new()
	_liquid.mesh = q
	_liq_mat = StandardMaterial3D.new()
	_liq_mat.albedo_texture = _ell_tex
	_liq_mat.albedo_color = COLORS["water"]
	_liq_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
	_liq_mat.alpha_scissor_threshold = 0.5
	_liq_mat.roughness = 0.7
	_liq_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED  # lit from below by the fire it read black
	_liquid.material_override = _liq_mat
	_liq_root.add_child(_liquid)
	_liquid.visible = false


## The liquid takes the colours in: one colour fills the opening, more colours add a spinning swirl band each.
func _set_liquid(cols: Array) -> void:
	if _liquid == null:
		return
	_liquid.visible = true
	_liq_mat.albedo_color = COLORS.get(str(cols[0]), COLORS["water"])
	_liq_mat.emission_enabled = str(cols[0]) == "black" or _eerie_t > 0.5
	_liq_mat.emission = Color(0.3, 0.9, 0.45) * 0.6
	for sw in _swirls:
		(sw as Node3D).queue_free()
	_swirls.clear()
	var tex := _texid("story_wc_pot_10")
	var o := _pot_open()
	for i in range(1, cols.size()):
		# squash node (the opening's ellipse) > spinning node (rotates in its own plane) > the spiral card
		var squash := Node3D.new()
		squash.position = Vector3(0, 0, 0.001 * i)
		squash.scale = Vector3(1.0, float(o[4]) / float(o[3]), 1.0)
		_liq_root.add_child(squash)
		var spin := Node3D.new()
		spin.rotation.z = TAU * float(i) / maxf(cols.size() - 1, 1)
		squash.add_child(spin)
		var q := QuadMesh.new()
		q.size = Vector2(1, 1) * float(o[3]) * 1.6
		var mi := MeshInstance3D.new()
		mi.mesh = q
		var m := StandardMaterial3D.new()
		m.albedo_texture = tex
		m.albedo_color = COLORS.get(str(cols[i]), Color.WHITE)
		m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
		m.alpha_scissor_threshold = 0.5
		m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		mi.material_override = m
		spin.add_child(mi)
		_swirls.append(spin)


func _bubble() -> void:  # a bubble pops up from somewhere inside the opening
	if _liquid == null or not _liquid.visible:
		return
	var o := _pot_open()
	var ang := randf() * TAU
	var p: Vector3 = o[0] + (o[1] as Vector3) * cos(ang) * float(o[3]) * 0.6 * randf() + Vector3.UP * sin(ang) * float(o[4]) * 0.5 + (o[2] as Vector3) * 0.003
	fly("story_wc_pot_18", p, p + Vector3.UP * 0.03, 0.018, 0.5, 0.0, 0.0, 0.0)


# ------------------------------------------------------------------ shelf

func _shelf_now(animated: bool) -> void:
	var sh := _sp("shelf")
	if sh == null or not _ings.is_empty():
		return
	var w := sh.width
	for i in SHELF_ORDER.size():
		var key: String = SHELF_ORDER[i]
		var sec := i / 3
		var k := i % 3
		var dx := (float(sec) - 1.0) * w * 0.333 + (-0.042 if k == 0 else (0.042 if k == 1 else 0.0))
		var y := (0.5 if k < 2 else 0.1) * sh.height
		var id := "story_wc_ingredients_%02d" % i
		var n := _card(id, 0.062)
		var sx := sh.global_transform.basis.x.normalized()
		var sz := sh.global_transform.basis.z.normalized()
		n.global_position = sh.global_position + sx * dx + Vector3.UP * y + sz * 0.03
		n.rotation.y = sh.global_rotation.y
		_ings[key] = n
		stage.spots["ing_" + key] = n.global_position  # camera stations for the naming push-ins
		stage.spots["shelf_mid"] = sh.global_position + Vector3.UP * sh.height * 0.3
		if animated:
			n.scale = Vector3.ONE * 0.02
			var tw := create_tween()
			tw.tween_interval(0.25 * i)
			tw.tween_property(n, "scale", Vector3.ONE, 0.35).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
			tw.tween_callback(func(): _sfx(str(SFX_ING[key]), n.global_position))


# ------------------------------------------------------------------ the brew verb

## brew {round, prompt, hint, ingredients, combos, results, stir, pop, offer, after, back} (rounds 1 / 2)
## brew {round: 3, all_colors, taps, result: ghost, candy, pot_color, stir, pop, eat, ghost} (the ghost candy)
func run_step(st: Dictionary, R: Node) -> void:
	match str(st.get("do", "")):
		"leave_shop":
			await _leave_shop(st, R)
		"name_jars":
			await _name_jars(st, R)
		"parade_surprise":
			await _parade_surprise(R)
		"ghost_flight":
			await _ghost_flight(R)
		"ghost_surprise":
			await _ghost_surprise(R)
		"ghost_roam":
			await _ghost_roam(R)
		"ghost_peekaboo":
			await _ghost_peekaboo(R)
			_eerie_t = 0.0
			_floating = false
			for r in ["kid", "witch", "cat", "rabbit", "bear", "fox"]:
				var a := _a(r)
				if a:
					a.lift = 0.0
			if SoundDirector.current:
				SoundDirector.current.set_music("ending", 1.5)
		"brew":
			if st.get("all_colors", false):
				await _brew_ghost(st, R)
			else:
				await _brew(st, R)
		_:
			push_warning("witch_candy: unknown step " + str(st.get("do", "")))


func _choose_auto(st: Dictionary) -> Array:
	var ings: Dictionary = st["ingredients"]
	var combos: Dictionary = st["combos"]
	var want := ""
	var rnd := int(st.get("round", 1))
	if _forced.size() >= rnd:
		want = str(_forced[rnd - 1])
	var pairs: Array = []
	var keys: Array = SHELF_ORDER.duplicate()
	for a in keys:
		for b in keys:
			var cs := [str(ings[a]["color"]), str(ings[b]["color"])]
			cs.sort()
			var key: String = str(cs[0]) if cs[0] == cs[1] else str(cs[0]) + str(cs[1])
			var res := str(combos.get(key, ""))
			if (want != "" and res == want) or (want == "" and not _seen_results.has(res)):
				pairs.append([a, b])
	if pairs.is_empty():
		return [keys[randi() % keys.size()], keys[randi() % keys.size()]]
	return pairs[randi() % pairs.size()]


func _result_of(st: Dictionary, picks: Array) -> String:
	var ings: Dictionary = st["ingredients"]
	var cs := [str(ings[picks[0]]["color"]), str(ings[picks[1]]["color"])]
	cs.sort()
	var key: String = str(cs[0]) if cs[0] == cs[1] else str(cs[0]) + str(cs[1])
	return str((st["combos"] as Dictionary).get(key, "duck"))


func _brew(st: Dictionary, R: Node) -> void:
	var rnd := int(st.get("round", 1))
	var ings: Dictionary = st["ingredients"]
	var auto_pair: Array = _choose_auto(st)
	_picking = true
	# v6 (user: "사탕 누를 때 ... 선반으로 카메라를 옮기는 건 어때?"): the taps get their own framing, the shelf close
	# with every jar big; each round from another angle (straight on / over Dahyun's shoulder / low)
	var pick_shot := "pick%d" % clampi(rnd, 1, 3)
	stage.shot_to(pick_shot, "shelf_mid", {"rate": 2.0})
	await R._wait(1.2)
	if st.has("prompt"):
		await R._say(str(st["prompt"]))
	var picks: Array = []
	for n in 2:
		var hit: String = await R._wait_tap(SHELF_ORDER.duplicate(), str(st.get("hint", "")), [auto_pair[n]], true, false)
		picks.append(hit)
		_drop_in(hit)
		var cols: Array = []
		for p in picks:
			var c := str(ings[p]["color"])
			if not cols.has(c):
				cols.append(c)
		await R._wait(0.35)
		stage.shot_to("pot", "in_pot", {"rate": 4.0})  # cut to the pot as it splashes in
		await R._wait(0.45)
		_set_liquid(cols)
		await R._wait(0.6)
		if n == 0:
			stage.shot_to(pick_shot, "shelf_mid", {"rate": 4.0})  # back to the shelf for the next pick
			await R._wait(0.5)
	_picking = false
	var res := _result_of(st, picks)
	_seen_results.append(res)
	var rs: Dictionary = (st["results"] as Dictionary)[res]
	# the line plan for this round (branch-aware line guard)
	var plan: Array = []
	if picks[0] != picks[1]:
		plan.append(str(ings[picks[0]]["and"]))
	plan.append(str(ings[picks[1]]["in"]))
	var yuck := ""
	for p in picks:
		if (ings[p] as Dictionary).has("yuck") and yuck == "":
			yuck = str(ings[p]["yuck"])
	if yuck != "":
		plan.append(yuck)
	plan.append(str(st["stir"]))
	if st.has("pop"):
		plan.append(str(st["pop"]))
	if st.has("offer"):
		plan.append(str(st["offer"]))
	plan.append(str((rs["eat"] as Array)[mini(rnd - 1, 1)]))
	plan.append(str(rs["tf"]))
	plan.append(str(rs["kid"]))
	plan.append(str(rs["act"]))
	for x in rs.get("extra", []):
		plan.append(str(x))
	for x in st.get("after", []):
		plan.append(str(x))
	if st.has("back"):
		plan.append(str(st["back"]))
	print("PLAN brew", rnd, " ", ",".join(plan), " result=", res, " picks=", ",".join(picks))
	for x in plan.slice(0, 2 if picks[0] != picks[1] else 1):
		await R._say(x)
	if yuck != "":
		await R._say(yuck)
	# magic stir: the witch reaches out, sparkles, the swirl speeds up
	var w := _a("witch")
	if w:
		w.set_pose("magic")
	stage.shot_to("pot", "in_pot", {"rate": 2.0})
	_swirl_speed = 4.0
	_sfx("wc.stir", _pot_mouth())
	for k in 6:
		fly("story_wc_pot_19", (w.centre() if w else _pot_mouth()) - _right() * 0.08, _pot_mouth(), 0.03, 0.5, 0.06, 0.0, 5.0)
	await R._say(str(st["stir"]))
	# POOF: smoke, the liquid takes the result colour, the candy pops out and lands at Dahyun's hands
	_swirl_speed = 0.6
	_poof(_pot_mouth(), 1.6)
	_sfx("wc.poof", _pot_mouth())
	_set_liquid([str(rs.get("pot", "water"))])
	var kid := _a("kid")
	var hand := kid.centre() + _toward() * 0.05 + _right() * 0.05 if kid else _pot_mouth()
	_candy = fly(str(rs["candy"]), _pot_mouth(), hand, 0.06, 0.9, 0.25, 999.0, 0.0)
	_sfx("wc.candy_pop", _pot_mouth())
	stage.shot_to("two_shot", "in_pot", {"rate": 2.0})
	if kid:
		kid.set_pose("wow")
	if st.has("pop"):
		await R._say(str(st["pop"]))
	else:
		await R._wait(0.9)
	if st.has("offer"):
		if w:
			w.set_pose("offer")
		await R._say(str(st["offer"]))
	# eat
	stage.shot_to("face_in", "in_kid", {"rate": 2.4})
	if kid:
		kid.set_pose("eat")
	await R._wait(0.4)
	if _candy:
		_drop_flyer(_candy)
		_candy = null
	await R._say(str((rs["eat"] as Array)[mini(rnd - 1, 1)]))
	# 뿅: transformation
	stage.shot_to("two_shot", "in_pot", {"rate": 2.6})  # the whole transformed figure (a fish tail is long and low)
	if kid:
		_poof(kid.centre(), 1.2)
		kid.set_pose(str(rs["figure"]))
		kid.hop_v = 0.9
	await R._say(str(rs["tf"]))
	await R._say(str(rs["kid"]))
	await _action(str(rs["action"]), rs, R)
	for x in st.get("after", []):
		await R._say(str(x))
	# 뿅 back, and in through the door to her place
	if kid:
		_poof(kid.centre(), 1.2)
		kid.lift = 0.0
		kid.set_pose("calm")
		if _kid_light:
			_kid_light.queue_free()
			_kid_light = null
	if st.has("back"):
		await R._say(str(st["back"]))
	else:
		await R._wait(0.6)
	await _walk_home(R)
	if w:
		w.set_pose("calm")


## Dahyun goes back into the room (walk cycle), the camera follows her in.
func _walk_home(R: Node) -> void:
	var kid := _a("kid")
	if kid == null:
		return
	var home := stage.spot_point("in_kid")
	if kid.global_position.distance_to(home) > 0.25:
		fx("door_open")
		var pts: Array = []
		if kid.global_position.distance_to(stage.spot_point("door")) > 0.15:
			pts.append(stage.spot_point("road_shop") if kid.global_position.distance_to(stage.spot_point("road_shop")) < kid.global_position.distance_to(stage.spot_point("door")) else stage.spot_point("door") + _out() * 0.2)
		pts.append_array(_door_steps(true))
		pts.append(home)
		kid.follow(pts, 0.32, "", true)
		await R._wait(0.3)
		fx("inside_view")
		var g := 0.0
		while kid.moving() and g < 14.0:
			g += await R._frame()
		fx("door_close")
	else:
		fx("inside_view")
	kid.set_pose("calm", 0)
	await R._wait(0.6)


func _drop_in(key: String) -> void:
	var n: Node3D = _ings.get(key)
	if n == null:
		return
	fly("story_wc_ingredients_%02d" % SHELF_ORDER.find(key), n.global_position, _pot_mouth() + Vector3.UP * 0.01, 0.062, 0.7, 0.25, 0.0, 3.0)
	_sfx(str(SFX_ING.get(key, "ui.pop")), n.global_position)
	get_tree().create_timer(0.65).timeout.connect(func(): _sfx("wc.plop", _pot_mouth()))
	var tw := create_tween()  # the shelf copy bounces (it stays: the shelf never runs out)
	tw.tween_property(n, "scale", Vector3.ONE * 1.25, 0.08)
	tw.tween_property(n, "scale", Vector3.ONE, 0.2)


func _brew_ghost(st: Dictionary, R: Node) -> void:
	var taps: Array = st.get("taps", ["snot", "lantern", "fish"])
	var ings: Dictionary = st["ingredients"]
	var plan := [str(st["stir"]), str(st["pop"]), str(st["eat"]), str(st["ghost"])]
	print("PLAN brew3 ", ",".join(plan), " result=ghost picks=", ",".join(taps))
	_picking = true
	stage.shot_to("pick3", "shelf_mid", {"rate": 2.0})
	await R._wait(1.2)
	var cols: Array = []
	for key in taps:  # one tap per colour group (rings on those three; same kind of tap as before: no voice)
		var hit: String = await R._wait_tap([key], "", [key], true, false)
		_drop_in(hit)
		cols.append(str(ings[hit]["color"]))
		await R._wait(0.35)
		stage.shot_to("pot", "in_pot", {"rate": 4.0})
		await R._wait(0.45)
		_set_liquid(cols)
		await R._wait(0.5)
		if cols.size() < taps.size():
			stage.shot_to("pick3", "shelf_mid", {"rate": 4.0})
			await R._wait(0.5)
	_picking = false
	# v3 build-up: the room lights flicker and dim, the music drops, the pot glows an eerie green, smoke swirls up
	var w := _a("witch")
	if w:
		w.set_pose("magic")
	_eerie_t = 1.0
	if SoundDirector.current:
		SoundDirector.current.set_music("", 1.0)
	_sfx("wc.eerie", _pot_mouth())
	stage.shot_to("pot_low", "in_pot", {"rate": 1.2})
	_swirl_speed = 5.0
	_sfx("wc.stir", _pot_mouth())
	await R._say(str(st["stir"]))
	_swirl_speed = 0.6
	_poof(_pot_mouth(), 2.2)
	_sfx("wc.poof", _pot_mouth())
	_set_liquid([str(st.get("pot_color", "black"))])
	# the reveal: the black candy rises slowly out of the pot, then floats to Dahyun's hands
	var kid := _a("kid")
	var up := _pot_mouth() + Vector3.UP * 0.22
	var rise := fly(str(st["candy"]), _pot_mouth(), up, 0.08, 2.2, 0.0, 999.0, 0.0)
	stage.shot_to("pot", "in_pot", {"rate": 1.0})
	_sfx("wc.sparkle", _pot_mouth())
	if kid:
		kid.set_pose("wow")
	await R._say(str(st["pop"]))
	await R._wait(maxf(0.0, 2.3 - R.line_duration(str(st["pop"]))))
	_drop_flyer(rise)
	_candy = fly(str(st["candy"]), up, kid.centre() + _out() * 0.06 + _sx() * 0.05, 0.07, 0.8, 0.1, 999.0)
	await R._wait(0.6)
	stage.shot_to("face_in", "in_kid", {"rate": 3.0})
	if kid:
		kid.set_pose("eat")
	await R._wait(0.5)
	if _candy:
		_drop_flyer(_candy)
		_candy = null
	# eaten: a big POOF, the camera pushes in on the black lips
	if kid:
		_poof(kid.centre(), 2.0)
		_black_mouth(["kid"], true)
		kid.set_pose("ghost")
		kid.hop_v = 0.8
	_sfx("wc.burst", kid.centre() if kid else null)
	stage.shake(1.4)
	_eerie_t = 0.4
	await R._say(str(st["eat"]))
	_wisps = 1.0  # white wisps puff out of the black "oooh" mouth while she says it
	await R._say(str(st["ghost"]))
	_wisps = 0.0
	if w:
		w.set_pose("calm")


# ------------------------------------------------------------------ the little ghost (v3: sneaks in, then the surprise)
## user: "유령이 처음엔 나온지 몰라야지 나중에 놀라는거". Glimpses 1-4 while the scene goes on (nobody notices): rises out
## of the pot steam and drifts behind the friends, peeks over the witch's shoulder, peeks over the pot rim, mimics the
## friends' ghost pose at the back; then the surprise (nose to nose with Dahyun), the roam (round the room, past the
## shelf, between the friends, out of the door, over the roofs in front of the moon, back) and a 까꿍.
var _g: Node3D  ## the ghost card (its own node, not an actor: it floats)
var _gpath: Dictionary = {}  ## {pts, t, dur, bob}
var _eerie := 0.0
var _eerie_t := 0.0
var _wisps := 0.0
var _wisp_cd := 0.0
var _floating := false


func _room(dx: float, dz: float, y: float) -> Vector3:
	var sp := _sp("shop")
	var b := sp.global_position
	return Vector3(b.x, stage.world.ground.surface_y(Vector2(b.x, b.z)), b.z) + _sx() * dx + _out() * dz + Vector3.UP * y


## The ghost candy's black mouth as an expression STATE (CastPuppet.mouth_state): every later figure change keeps it
## until the story turns it off (at the end of the parade, with a 뿅).
var _black_expected := {}  ## roles the story says have the black mouth now (independent check of the puppet state)
var black_missing := 0  ## frames a role that should have the black mouth was showing without the state


func _black_mouth(roles: Array, on: bool) -> void:
	for r in roles:
		if on:
			_black_expected[str(r)] = true
		else:
			_black_expected.erase(str(r))
	for r in roles:
		var a := _a(str(r))
		if a == null:
			continue
		a.puppet.mouth_state = "black" if on else ""
		a.puppet.set_figure(a.pose, a.facing_left and a.view_of(a.pose) == "side", true)


func _ghost_card() -> Node3D:
	if _g == null or not is_instance_valid(_g):
		_g = _card("story_wc_halloween_16", 0.17)
		_g.scale = Vector3.ONE * 0.02
	return _g


func _gmove(pts: Array, dur: float, bob := 0.02) -> void:
	_gpath = {"pts": pts, "t": 0.0, "dur": dur, "bob": bob}


func _gwait(R: Node) -> void:
	var g := 0.0
	while not _gpath.is_empty() and g < 30.0:
		g += await R._frame()


func _gscale(v: float, sec: float) -> void:
	var tw := create_tween()
	tw.tween_property(_ghost_card(), "scale", Vector3.ONE * maxf(v, 0.02), sec).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)


## glimpse k: runs alongside the lines (not awaited by the beat)
func _glimpse(k: int) -> void:
	var gh := _ghost_card()
	match k:
		1:  # out of the pot steam, drifting slowly behind the friends at the back, ducking behind the shelf
			gh.global_position = _pot_mouth()
			_gscale(0.7, 0.8)
			_sfx("wc.eerie", _pot_mouth())
			_gmove([_pot_mouth() + Vector3.UP * 0.15, _room(0.45, -0.95, 0.24), _room(0.05, -0.96, 0.27),
				_room(-0.35, -0.96, 0.2), _room(-0.35, -0.96, 0.02)], 5.0, 0.015)
			await get_tree().create_timer(5.0).timeout
			_gscale(0.02, 0.3)
		2:  # peeks over the witch's shoulder, ducks when she turns
			var w := _a("witch")
			var p := w.global_position - _out() * 0.06 + _sx() * 0.06 if w else _room(0.5, -0.6, 0.0)
			gh.global_position = p + Vector3.UP * 0.25
			_gscale(0.8, 0.35)
			_gmove([p + Vector3.UP * 0.38, p + Vector3.UP * 0.38], 1.6, 0.01)
			await get_tree().create_timer(1.7).timeout
			if w:
				w.face_point(w.global_position - _sx())  # she half turns: it ducks down
			_gmove([p + Vector3.UP * 0.1], 0.35, 0.0)
			await get_tree().create_timer(0.35).timeout
			_gscale(0.02, 0.2)
		3:  # peeks over the pot rim from behind it, then sinks back in
			var m := _pot_mouth() - _out() * 0.05
			gh.global_position = m - Vector3.UP * 0.12
			_gscale(0.55, 0.3)
			_gmove([m + Vector3.UP * 0.02, m + Vector3.UP * 0.04, m - Vector3.UP * 0.12], 2.4, 0.01)
			await get_tree().create_timer(2.5).timeout
			_gscale(0.02, 0.2)
		4:  # at the back behind the friends, arms-up "oooh" like them (bobbing in time), bolder: almost in the open
			gh.global_position = _room(0.66, -0.95, 0.05)
			_gscale(0.85, 0.4)
			_gmove([_room(0.66, -0.95, 0.3), _room(0.66, -0.95, 0.3)], 3.0, 0.035)
			await get_tree().create_timer(3.0).timeout
			_gmove([_room(0.66, -0.95, 0.05)], 0.3, 0.0)
			await get_tree().create_timer(0.3).timeout
			_gscale(0.02, 0.2)


## The surprise: Dahyun turns round and it is right there, nose to nose: a sting, a snap zoom and shake, everyone
## jumps with surprised faces.
func _ghost_surprise(R: Node) -> void:
	var kid := _a("kid")
	_floating = false
	var face := kid.global_position + Vector3.UP * kid.puppet.height * 0.62 + _out() * 0.09 + _sx() * 0.07
	var gh := _ghost_card()
	gh.global_position = face + _sx() * 0.08
	stage.shot_to("face_in", "in_kid", {"rate": 2.0})
	await R._wait(0.8)
	_gscale(0.75, 0.25)
	_gmove([face], 0.25, 0.0)
	kid.face_point(face)
	await R._wait(0.3)
	_sfx("wc.sting", face)
	stage.shot_to("face_in", "in_kid", {"rate": 6.0, "shake": 2.5})
	for r in ["kid", "witch", "rabbit", "bear", "fox", "cat"]:
		var a := _a(r)
		if a:  # v5: surprised faces WITH the ghost-candy mouth (drawn natively), not the arms-up ghost pose
			a.set_pose("wow_black" if r == "kid" else "surprised_black")
			a.hop_v = 1.1
	await R._wait(1.6)


## The roam: loops round the room, a circle round the pot, past the shelf (the jars jump), weaving between the
## friends (they hop as it passes), out of the open door, a swoop over the roofs in front of the moon and back in.
func _ghost_roam(R: Node) -> void:
	var gh := _ghost_card()
	_track = gh
	stage.shot_to("room", null, {"rate": 2.4})
	_sfx("wc.swoosh", gh.global_position)
	var m := _pot_mouth()
	var pts: Array = [_room(-0.2, -0.45, 0.45), _room(-0.4, -0.7, 0.3)]
	for k in 7:  # round the pot
		var a := TAU * k / 6.0
		pts.append(m + _sx() * cos(a) * 0.2 + _out() * sin(a) * 0.14 + Vector3.UP * 0.08)
	pts.append_array([_room(-0.35, -0.82, 0.32), _room(-0.15, -0.8, 0.36), _room(0.2, -0.78, 0.4),
		_room(0.4, -0.72, 0.42), _room(0.6, -0.7, 0.38), _room(0.16, -0.3, 0.3), stage.spot_point("in_door") + Vector3.UP * 0.22])
	_gmove(pts, 7.5, 0.02)
	_shelf_wobble = 1.0
	for r in ["rabbit", "bear", "fox", "witch", "cat", "kid"]:
		var a := _a(r)
		if a:  # watching it whoosh round: still surprised (black mouths)
			a.set_pose("wow_black" if r == "kid" else "surprised_black")
	var t0 := 0.0
	while not _gpath.is_empty() and t0 < 10.0:
		t0 += await R._frame()
		for r in ["rabbit", "bear", "fox", "kid", "witch"]:  # they duck / hop as it passes close, and watch it
			var a := _a(r)
			if a and a.centre().distance_to(gh.global_position) < 0.16 and a.hop_v <= 0.0:
				a.hop_v = 0.6
				_sfx("wc.swoosh", gh.global_position)
	_shelf_wobble = 0.0
	# out of the door and over the roofs in front of the moon
	fx("door_open")
	stage.shot_to("door_wide", "door_view", {"rate": 3.0})
	var d0 := stage.spot_point("door") + _out() * 0.2 + Vector3.UP * 0.25
	var loop := stage.spot_point("fly_loop")
	var out: Array = [d0, d0 + Vector3.UP * 0.4]
	for k in 7:
		var a2 := TAU * k / 6.0
		out.append(loop + _right() * cos(a2) * 0.35 + Vector3.UP * (0.85 + sin(a2) * 0.22))
	out.append_array([d0 + Vector3.UP * 0.3, d0, stage.spot_point("in_door") + Vector3.UP * 0.22])
	_gmove(out, 7.0, 0.02)
	await R._wait(1.2)
	stage.shot_to("sky", "fly_loop", {"rate": 1.6})
	_sfx("wc.swoosh", loop)
	await R._wait(3.6)
	stage.shot_to("door_wide", "door_view", {"rate": 2.0})
	await _gwait(R)
	fx("door_close")
	_track = null


## 까꿍: it pops up right in front of Dahyun, giggling; everyone laughs; it settles beside the friends, friendly now.
func _ghost_peekaboo(R: Node) -> void:
	var kid := _a("kid")
	fx("inside_view")
	await R._wait(1.0)
	var face := kid.global_position + Vector3.UP * kid.puppet.height * 0.55 + _out() * 0.1
	var gh := _ghost_card()
	gh.global_position = face - Vector3.UP * 0.15
	_gmove([face], 0.3, 0.0)
	_sfx("wc.peekaboo", face)
	stage.shot_to("two_shot", "in_pot", {"rate": 3.0})
	await R._wait(0.5)
	for r in ["kid", "witch", "rabbit", "bear", "fox"]:
		var a := _a(r)
		if a:
			a.set_pose({"kid": "wave", "witch": "giggle"}.get(r, "cheer"))
			a.hop_v = 0.6
	_sfx("wc.giggle_bells", face)
	await R._wait(1.0)
	_gmove([_room(0.62, -0.62, 0.32)], 1.2, 0.02)
	await _gwait(R)
	_ghost_follow = ""


func _step_ghost(dt: float) -> void:
	for r in _black_expected:
		var ba := _a(str(r))
		if ba and ba.visible and ba.pop_s > 0.5 and (ba.puppet.mouth_state != "black" or not ba.puppet.mouth_ok(ba.puppet.pose)):
			black_missing += 1
	var cam := stage.camera()
	if _g and is_instance_valid(_g):
		if not _gpath.is_empty():
			_gpath["t"] = float(_gpath["t"]) + dt
			var pts: Array = _gpath["pts"]
			var u := clampf(float(_gpath["t"]) / float(_gpath["dur"]), 0.0, 1.0)
			if pts.size() == 1:
				_g.global_position = _g.global_position.lerp(pts[0], 1.0 - exp(-8.0 * dt))
			else:
				var f := u * (pts.size() - 1)
				var i := mini(int(f), pts.size() - 2)
				var k := f - i
				var p0: Vector3 = pts[maxi(i - 1, 0)]
				var p1: Vector3 = pts[i]
				var p2: Vector3 = pts[i + 1]
				var p3: Vector3 = pts[mini(i + 2, pts.size() - 1)]
				var k2 := k * k
				var k3 := k2 * k
				_g.global_position = 0.5 * ((2.0 * p1) + (-p0 + p2) * k + (2.0 * p0 - 5.0 * p1 + 4.0 * p2 - p3) * k2 + (-p0 + 3.0 * p1 - 3.0 * p2 + p3) * k3)
			_g.global_position.y += sin(_t * 3.0) * float(_gpath["bob"]) * dt * 6.0
			if u >= 1.0:
				_gpath = {}
		_g.rotation = Vector3(0, atan2(cam.global_position.x - _g.global_position.x, cam.global_position.z - _g.global_position.z), sin(_t * 2.3) * 0.12)
	# eerie room: the warm lights dim and flicker, the pot glows green
	_eerie = move_toward(_eerie, _eerie_t, dt * 0.7)
	for q: Array in stage._lights:
		if not is_instance_valid(q[0]):
			continue
		var o := q[0] as OmniLight3D
		var par := o.get_parent()
		if par == _sp("beam"):
			o.light_energy = float(q[1]) * (1.0 - 0.8 * _eerie) * (1.0 - 0.25 * _eerie * absf(sin(_t * 17.0)))
		elif par == _sp("pot"):
			o.light_color = Color(1.0, 0.55, 0.23).lerp(Color(0.45, 1.0, 0.55), _eerie)
			o.light_energy = float(q[1]) * (1.0 + 1.5 * _eerie)
	if _eerie > 0.6 and fmod(_t, 0.45) < dt:  # smoke only while the pot is brewing (not over faces later)
		var po := _pot_open()
		var st0: Vector3 = po[0] + (po[1] as Vector3) * randf_range(-0.5, 0.5) * float(po[3]) + Vector3.UP * float(po[4]) * 0.5
		fly("story_wc_pot_16", st0, st0 + Vector3.UP * 0.18 + _sx() * sin(_t) * 0.03, 0.045, 1.3, 0.0, 0.0, 1.0)
	# ghost-mouth wisps: little white puffs out of the "oooh" mouth
	if _wisps > 0.0:
		_wisp_cd -= dt
		var kid := _a("kid")
		if _wisp_cd <= 0.0 and kid:
			_wisp_cd = 0.4
			var mo := kid.global_position + Vector3.UP * kid.puppet.height * 0.6 + _out() * 0.03
			fly("story_wc_pot_17", mo, mo + Vector3.UP * 0.1 + _sx() * randf_range(-0.05, 0.05) + _out() * 0.04, 0.035, 0.9, 0.02, 0.0, 1.0)
	# everyone floats a little while they "oooh" (ghost candy)
	if _floating:
		for r in ["kid", "witch", "cat", "rabbit", "bear", "fox"]:
			var a := _a(r)
			if a:
				a.lift = 0.02 + sin(_t * 2.4 + r.length()) * 0.015
	# the shelf jars jump as the ghost whooshes past
	if _shelf_wobble > 0.0 and _g:
		for key in _ings:
			var n: Node3D = _ings[key]
			if n.global_position.distance_to(_g.global_position) < 0.2:
				n.rotation.z = sin(_t * 30.0) * 0.25
			else:
				n.rotation.z *= 0.9


var _shelf_wobble := 0.0


# ------------------------------------------------------------------ v6 parade ghost (user: "유령 흉내를 내면서 걸을 때
# 갑자기 뒤에 몰래 유령이 생기는 거야 ... 애들은 유령이 있는지 모르고 막 즐겁게 놀다가 마지막에 ... 놀라는 거야. 그 다음부터
# 유령은 막 히히 웃으면서 ... 마을을 엄청 날아다니고 ... 사라지는 거지")
var _pg_on := false
var _pg_t := 0.0
var _pg_last_pos := Vector3.ZERO
var _pg_dir := Vector3.FORWARD
var _pg_ducked := false


func _parade_ghost_start() -> void:
	_pg_on = true
	_pg_t = -3.0  # it appears a few seconds into the walk
	var gh := _ghost_card()
	gh.scale = Vector3.ONE * 0.02
	_gpath = {}


func _step_parade_ghost(dt: float) -> void:
	if not _pg_on:
		return
	_pg_t += dt
	var last := _a("fox")
	if last == null or _pg_t < 0.0:
		return
	var gh := _ghost_card()
	if _pg_t - dt < 0.0:  # quietly there, behind the last in line (no sting: a soft flutter only)
		gh.global_position = last.global_position + Vector3.UP * 0.5
		_gscale(0.8, 0.6)
		_sfx("wc.flutter", gh.global_position)
	var mv := last.global_position - _pg_last_pos
	mv.y = 0.0
	if mv.length() > 0.002:
		_pg_dir = _pg_dir.lerp(mv.normalized(), 0.1).normalized()
	_pg_last_pos = last.global_position
	var phase := fmod(_pg_t, 14.0)
	var tgt := last.global_position - _pg_dir * 0.22 + Vector3.UP * 0.13
	var amp := 0.015
	if phase > 3.0 and phase < 7.0:  # copying them: the ghost-play bob and sway
		amp = 0.04
		gh.rotation.z = sin(_t * 5.0) * 0.25
	elif phase >= 7.0 and phase < 10.0:  # peeking out between the last two
		var b := _a("bear")
		if b:
			tgt = last.global_position.lerp(b.global_position, 0.5) + _pg_dir.cross(Vector3.UP).normalized() * 0.09 + Vector3.UP * 0.16
	elif phase >= 10.0 and phase < 11.2:  # the rabbit almost turns round: it ducks down out of sight
		tgt = last.global_position - _pg_dir * 0.2 + Vector3.UP * 0.0
		if not _pg_ducked:
			_pg_ducked = true
			var r := _a("rabbit")
			if r:
				r.puppet.set_figure(r.puppet.pose, not r.facing_left)
				get_tree().create_timer(0.5).timeout.connect(func(): r.puppet.set_figure(r.puppet.pose, r.facing_left))
	else:
		_pg_ducked = false
	tgt.y += sin(_t * 3.0) * amp
	gh.global_position = gh.global_position.lerp(tgt, 1.0 - exp(-4.0 * dt))


## The end of the walk: someone turns round, they all see it right behind them: sting, snap zoom, everyone jumps.
func _parade_surprise(R: Node) -> void:
	_pg_on = false
	var gh := _ghost_card()
	var fox := _a("fox")
	gh.global_position = fox.global_position - _pg_dir * 0.16 + Vector3.UP * 0.14 if fox else gh.global_position
	stage.shot_to("surprise", null, {"rate": 2.0})
	stage._focus_goal = gh.global_position - Vector3.UP * 0.12
	await R._wait(0.7)
	for r in ["kid", "witch", "cat", "rabbit", "bear", "fox"]:
		var a := _a(r)
		if a:
			a.face_point(gh.global_position)
	await R._wait(0.35)
	_sfx("wc.sting", gh.global_position)
	stage.shot_to("surprise", null, {"rate": 7.0, "shake": 2.6})
	for r in ["kid", "witch", "cat", "rabbit", "bear", "fox"]:
		var a := _a(r)
		if a:
			a.set_pose("wow_black" if r == "kid" else "surprised_black")
			a.hop_v = 1.2
	await R._wait(1.3)
	_sfx("wc.giggle_bells", gh.global_position)  # 히히 (a giggle sound; no new voice recorded)
	_sfx("wc.peekaboo", gh.global_position)
	gh.rotation.z = 0.3
	await R._wait(0.9)


## Then, while they stand startled, it flies all over the village: down the street, round the lamp posts and along the
## strings of lights, over the roofs, past lit windows, a loop in front of the moon, back over the kids.
func _ghost_flight(R: Node) -> void:
	var gh := _ghost_card()
	var up := Vector3.UP
	var P := func(n: String, h: float) -> Vector3: return stage.spot_point(n) + up * h
	var pts: Array = [gh.global_position + up * 0.2, P.call("road_mid", 0.35), P.call("lights_1", 0.4)]
	for k in 5:  # round the lamp post on the left
		var a := TAU * k / 4.0
		pts.append(P.call("lamp_l", 0.38) + _right() * cos(a) * 0.14 + _toward() * sin(a) * 0.14)
	for hn in ["house_0", "house_1", "house_2"]:  # past their lit windows, then up over the roofs
		pts.append(P.call(hn, 0.3) + _right() * 0.3)
	pts.append_array([P.call("house_3", 0.85), P.call("house_6", 0.85), P.call("lights_2", 0.42)])
	for k in 5:  # round the lamp post on the right
		var a2 := TAU * k / 4.0
		pts.append(P.call("lamp_r", 0.38) + _right() * cos(a2) * 0.14 + _toward() * sin(a2) * 0.14)
	var loop := stage.spot_point("fly_loop")
	for k in 7:  # a loop in front of the moon
		var a3 := TAU * k / 6.0
		pts.append(loop + _right() * cos(a3) * 0.32 + up * (0.85 + sin(a3) * 0.22))
	var kid := _a("kid")
	pts.append((kid.global_position if kid else loop) + up * 0.45)
	_gmove(pts, 13.0, 0.03)
	_track = gh
	stage.shot_to("track", null, {"rate": 2.2})
	var t := 0.0
	var next_whoosh := 0.0
	var switched := false
	while not _gpath.is_empty() and t < 16.0:
		t += await R._frame()
		if t >= next_whoosh:
			next_whoosh = t + 1.3
			_sfx("wc.swoosh", gh.global_position)
		if not switched and float(_gpath.get("t", 0.0)) > 13.0 * 0.62:
			switched = true
			stage.shot_to("sky", null, {"rate": 1.6})
		for r in ["kid", "witch", "rabbit", "bear", "fox"]:  # they watch it go
			var a := _a(r)
			if a and fmod(t, 0.6) < 0.04:
				a.face_point(gh.global_position)
	stage.shot_to("track", null, {"rate": 2.0})
	await R._wait(0.6)
	_track = null
	for k in 8:  # sparkles as it vanishes (ghost_vanish: 뿅)
		var a4 := TAU * k / 8.0
		fly("story_wc_pot_19", gh.global_position, gh.global_position + _right() * cos(a4) * 0.15 + up * (0.1 + sin(a4) * 0.12), 0.035, 0.7, 0.05, 0.0, 6.0)


# ------------------------------------------------------------------ transformation actions

func _action(kind: String, rs: Dictionary, R: Node) -> void:
	var kid := _a("kid")
	if kid == null:
		return
	var act := str(rs["act"])
	match kind:
		"waddle_room":
			# duck feet: round the pot in the drawn waddle cycle, 호박이 waddling behind
			stage.shot_to("room", "in_focus", {"rate": 1.6})
			var p0 := stage.spot_point("in_kid")
			var pts := [p0 + _sx() * 0.32 + _out() * 0.12, p0 + _sx() * 0.5 + _out() * 0.05, p0 - _sx() * 0.06 + _out() * 0.1, p0]
			kid.follow(pts, 0.16, "duck", false)
			var cat := _a("cat")
			if cat:
				cat.follow([cat.global_position + _out() * 0.05 - _sx() * 0.1] + pts.slice(0, 2), 0.11, "", false)  # behind, slower
			R._say(act)
			await _wait_moving(R, ["kid", "cat"])
			if cat:
				cat.walk_to(stage.spot_point("in_cat"), 0.18, "")
			kid.set_pose(str(rs["figure"]))
			await _while_line(R)
		"roll_street":
			await _go_out(R, "door_cam")
			kid.set_pose("tf_strawberry_ball")
			_rolling = "kid"
			_sfx("wc.roll", kid.centre())
			var bump := stage.spot_point("pump_bump")
			_glide("kid", [stage.spot_point("door") + _out() * 0.15, stage.spot_point("road_shop"),
				stage.spot_point("road_mid") + _toward() * 0.1, bump + _right() * 0.14], 0.5, "roll", "tf_strawberry_ball")
			stage.follow_actor("kid", "track")
			R._say(act)
			await _wait_glide(R, "kid")
			_sfx("wc.bonk", bump)
			if _sp("pump_bump"):
				_sp("pump_bump").bounce()
			kid.hop_v = 1.0
			await _while_line(R)
			await R._say(str((rs.get("extra", [""]) as Array)[0]))
			_glide("kid", [stage.spot_point("road_mid"), stage.spot_point("road_shop"), stage.spot_point("door") + _out() * 0.2], 0.55, "roll", "tf_strawberry_ball")
			await _wait_glide(R, "kid")
			_rolling = ""
			kid.set_pose(str(rs["figure"]))
		"swim_moon", "fly_moon":
			await _go_out(R, "street")
			var up := stage.spot_point("door") + _out() * 0.2
			var loop := stage.spot_point("fly_loop")  # over the middle of the street: near the camera, the moon behind
			var pts: Array = [up + Vector3.UP * 0.25, Vector3(up.x, 0, up.z).lerp(Vector3(loop.x, 0, loop.z), 0.5) + Vector3.UP * 0.7]
			for k in 7:  # a loop high over the roofs, in front of the moon
				var a := TAU * k / 6.0
				pts.append(loop + _right() * cos(a) * 0.3 + Vector3.UP * (0.8 + sin(a) * 0.2))
			pts.append(up + Vector3.UP * 0.25)
			pts.append(up)
			var fig := str(rs["figure"])
			_flap = kind == "fly_moon"
			_glide("kid", pts, 0.55, "float", fig)
			stage.shot_to("sky", "fly_loop", {"rate": 1.2})  # on her loop, the moon behind
			if kind == "fly_moon":
				for i in 3:
					var b := _card("story_wc_halloween_%02d" % (7 + i), 0.06)
					b.rotation.y = _yaw()
					_floaters["bat_%d" % i] = {"node": b, "base": loop + Vector3.UP * 0.8, "ph": i * 2.1, "amp": 0.0, "orbit": 0.35 + 0.08 * i}
			_sfx("wc.flap" if kind == "fly_moon" else "wc.bubble", up)
			await R._wait(1.2)
			await R._say(act)
			await _wait_glide(R, "kid")
			for i in 3:
				if _floaters.has("bat_%d" % i):
					(_floaters["bat_%d" % i]["node"] as Node3D).queue_free()
					_floaters.erase("bat_%d" % i)
			_flap = false
			kid.lift = 0.0
			kid.set_pose(fig)
			stage.shot_to("door_cam", "door", {"rate": 1.6})
		"hop_roof":
			await _go_out(R, "door_cam")
			var shop := _sp("shop")
			var top := shop.global_position + Vector3.UP * shop.height * 0.98 + _out() * 0.02
			var d0 := stage.spot_point("door") + _out() * 0.25
			stage.shot_to("roof_cam", "door_view", {"rate": 1.4})
			R._say(act)
			for k in 3:  # three hops: the step, the awning, the ridge
				var to := d0.lerp(top, float(k + 1) / 3.0)
				_glide("kid", [to], 0.5, "hop", "tf_frog_jump")
				_sfx("wc.ribbit", to)
				await _wait_glide(R, "kid")
				await R._wait(0.15)
			kid.set_pose("tf_frog_sit")
			kid.hop_v = 0.6
			await _while_line(R)
			await R._wait(0.6)
			_glide("kid", [d0], 0.6, "hop", "tf_frog_jump")
			await _wait_glide(R, "kid")
			kid.lift = 0.0
			kid.set_pose("tf_frog_sit")
		"glow_street":
			await _go_out(R, "street")
			_dim_t = 0.25  # the street lamps and windows dim, her pumpkin tummy lights the way
			_kid_light = OmniLight3D.new()
			_kid_light.light_color = Color(1.0, 0.6, 0.25)
			_kid_light.light_energy = 2.2
			_kid_light.omni_range = 1.3
			_kid_light.position = Vector3(0, 0.18, 0.08)
			kid.add_child(_kid_light)
			_sfx("wc.glow", kid.centre())
			_glide("kid", [stage.spot_point("door") + _out() * 0.25, stage.spot_point("road_shop"), stage.spot_point("road_mid")], 0.34, "hop", "tf_pumpkin")
			stage.follow_actor("kid", "track")
			R._say(act)
			await _wait_glide(R, "kid")
			await _while_line(R)
			await R._wait(0.8)
			_dim_t = 1.0
			_glide("kid", [stage.spot_point("road_shop"), stage.spot_point("door") + _out() * 0.2], 0.4, "hop", "tf_pumpkin")
			await _wait_glide(R, "kid")
		_:
			await R._say(act)


## The witch names the ingredients; as each is named the camera pushes in on its jar on the shelf ({line, at:
## [[sec, key]...], then: "kid_yuck" = cut straight to Dahyun's face at the end).
func _name_jars(st: Dictionary, R: Node) -> void:
	var line := str(st["line"])
	var at: Array = st.get("at", [])
	R._say(line)
	var t0 := 0.0
	var i := 0
	var dur: float = R.line_duration(line)
	while t0 < dur - 0.3:
		if i < at.size() and t0 >= float(at[i][0]):
			var key := str(at[i][1])
			stage.shot_to("jar", "ing_" + key, {"rate": 5.0})
			var n: Node3D = _ings.get(key)
			if n:
				var tw := create_tween()
				tw.tween_property(n, "scale", Vector3.ONE * 1.18, 0.12)
				tw.tween_property(n, "scale", Vector3.ONE, 0.25)
			i += 1
		t0 += await R._frame()
	if str(st.get("then", "")) == "kid_yuck":
		stage.shot_to("face_in", "in_kid", {"rate": 9.0})
	while R._line_busy:
		await R._frame()


## Out of the shop one at a time (v2, user: "문 아래 돌지방을 통과 ... 이런게 없어야"): the door swings fully open
## (inward), each walks to the doorway, steps up onto the sill, over it and down the steps, then on to a place in a
## tidy file along the front path. {who, pose, to (spot), spacing}
func _leave_shop(st: Dictionary, R: Node) -> void:
	var sp := _sp("shop")
	fx("door_open")
	var g := 0.0
	while sp.door_open_amount() < 0.95 and g < 2.0:
		g += await R._frame()
	var roles: Array = st.get("who", [])
	var to := stage.spot_point(st.get("to", "road_shop"))
	var o := _out()
	for i in roles.size():
		var a := _a(str(roles[i]))
		if a == null:
			continue
		var pts := _door_steps(false)
		if str(roles[i]) in ["rabbit", "bear", "fox"]:  # from behind the pot: round it first
			pts.push_front(stage.spot_point("in_via"))
		var end := to + o * float(st.get("spacing", 0.15)) * float(roles.size() - 1 - i) * 0.0 - (to - stage.spot_point("door")).normalized() * float(st.get("spacing", 0.15)) * i
		pts.append(Vector3(end.x, stage.world.ground.surface_y(Vector2(end.x, end.z)), end.z))
		a.follow(pts, 0.55, str(st.get("pose", "")), true)
		var g2 := 0.0
		while a.moving() and a._path.size() > 1 and g2 < 8.0:  # the next one starts once this one is down the steps
			g2 += await R._frame()
	var g3 := 0.0
	while g3 < 8.0:  # everyone down the steps and in the file before the parade starts
		var busy := false
		for r in roles:
			if _a(str(r)) and _a(str(r)).moving():
				busy = true
		if not busy:
			break
		g3 += await R._frame()
	fx("door_close")


## The way over the shop's sill as world points: out (room → threshold → steps → ground) or in (reversed).
func _door_steps(going_in: bool) -> Array:
	var sp := _sp("shop")
	var o := _out()
	var sill := sp.door_sill()
	var fr := sp.door_point(true, o)
	var bk := sp.door_point(false, o)
	var pts := [stage.spot_point("in_door") + Vector3.UP * 0.02, bk + Vector3.UP * sill, fr - o * 0.1 + Vector3.UP * sill,
		fr - o * 0.06 + Vector3.UP * sill * 0.5, fr + o * 0.04]
	if going_in:
		pts.reverse()
	return pts


## Dahyun walks out of the room to the open door (camera outside, door opens), still in her transformed figure.
func _go_out(R: Node, shot := "story") -> void:
	var kid := _a("kid")
	# v3 (user: "다현이 사탕먹고 집밖으로 나오는것도 좀 더 극적으로"): the door bursts open in a spill of warm light,
	# a low hero shot on the doorstep, a beat of sparkles and a music lift, then she launches into the action
	stage.shot_to("hero", "door", {"rate": 2.2})
	await R._wait(0.6)
	fx("door_open")
	_sfx("wc.burst", stage.spot_point("door"))
	var spill := OmniLight3D.new()
	spill.light_color = Color(1.0, 0.8, 0.45)
	spill.light_energy = 3.5
	spill.omni_range = 1.2
	stage.add_child(spill)
	spill.global_position = stage.spot_point("in_door") + Vector3.UP * 0.2
	create_tween().tween_property(spill, "light_energy", 0.0, 2.2)
	get_tree().create_timer(2.4).timeout.connect(spill.queue_free)
	if SoundDirector.current:
		SoundDirector.current.set_bed("@light", 1.5)
	var fig := kid.pose
	var sp := _sp("shop")
	var g := 0.0
	while sp.door_open_amount() < 0.95 and g < 2.0:  # the door swings fully clear first
		g += await R._frame()
	_glide("kid", _door_steps(false), 0.36, "walk", fig)
	await _wait_glide(R, "kid")
	kid.hop_v = 0.9  # the hero pose on the doorstep: a hop, sparkles, a lift in the music
	for k in 6:
		var a := TAU * k / 6.0
		fly("story_wc_pot_19", kid.centre(), kid.centre() + _sx() * cos(a) * 0.14 + Vector3.UP * (0.1 + sin(a) * 0.08), 0.035, 0.7, 0.05, 0.0, 5.0)
	_sfx("wc.sparkle", kid.centre())
	_sfx("wc.stir", kid.centre())
	await R._wait(0.9)
	stage.shot_to(shot, "door", {"rate": 1.4})


func _while_line(R: Node) -> void:
	while R._line_busy:
		await R._frame()


func _wait_moving(R: Node, roles: Array) -> void:
	var g := 0.0
	await R._frame()
	while g < 20.0:
		var busy := false
		for r in roles:
			var a := _a(str(r))
			if a and a.moving():
				busy = true
		if not busy:
			return
		g += await R._frame()


## A handler-driven move that keeps a fixed figure (no walk cycle): hop (paper hop per step), float (path in the
## air, a gentle bob), roll (rocking ball). Points are world points; y above the ground becomes the actor's lift.
func _glide(role: String, pts: Array, spd: float, mode: String, pose: String) -> void:
	var a := _a(role)
	if a == null:
		return
	a.pose = pose
	a.puppet.set_figure(pose, false)
	var gy := stage.world.ground.surface_y(Vector2(a.global_position.x, a.global_position.z))
	# "y": the path height above the ground (kept apart from the hop / bob offset, which must not feed back)
	if not stage.no_spacing.has(role):
		stage.no_spacing.append(role)
	_glides[role] = {"pts": pts.duplicate(), "spd": spd, "mode": mode, "pose": pose, "dist": 0.0,
		"y": maxf(0.0, float(_glides.get(role, {}).get("y", a.lift if mode != "hop" else 0.0)))}


func _wait_glide(R: Node, role: String) -> void:
	var g := 0.0
	while _glides.has(role) and g < 25.0:
		g += await R._frame()


var _dbg := 0.0


func _step_glides(dt: float) -> void:
	_dbg += dt
	if _dbg > 1.0 and _glides.has("kid") and OS.get_cmdline_user_args().has("--wc-debug"):
		_dbg = 0.0
		var k := _a("kid")
		print("GLIDE kid at ", k.global_position, " lift ", k.lift, " pts ", (_glides["kid"]["pts"] as Array).size(), " to ", (_glides["kid"]["pts"] as Array).front(), " pop ", k.pop_s, " vis ", k.visible)
	for role in _glides.keys():
		var gd: Dictionary = _glides[role]
		var a := _a(str(role))
		var pts: Array = gd["pts"]
		if a == null or pts.is_empty():
			_glides.erase(role)
			stage.no_spacing.erase(role)
			if a:
				a.puppet.rotation.z = 0.0
			continue
		var tgt: Vector3 = pts[0]
		var gp := stage.world.ground.surface_y(Vector2(a.global_position.x, a.global_position.z))
		var cur := Vector3(a.global_position.x, gp + float(gd["y"]), a.global_position.z)
		var to := tgt - cur
		var d := to.length()
		var step := float(gd["spd"]) * dt
		var nxt := cur + to / maxf(d, 1e-5) * minf(step, d)
		if d <= step:
			pts.pop_front()
		gd["dist"] = float(gd["dist"]) + minf(step, d)
		var ground := stage.world.ground.surface_y(Vector2(nxt.x, nxt.z))
		a.place_at(Vector3(nxt.x, ground, nxt.z))
		var mode := str(gd["mode"])
		var lift := maxf(0.0, nxt.y - ground)
		gd["y"] = lift
		if mode == "hop":
			a.lift = lift + absf(sin(float(gd["dist"]) / 0.12 * PI)) * 0.06
		elif mode == "float":
			a.lift = lift + sin(_t * 3.0) * 0.015
		else:
			a.lift = lift
		if mode == "roll":
			a.puppet.rotation.z = sin(float(gd["dist"]) / 0.05) * 0.5
		# side figures face their travel (mirror for screen-left)
		var cam := stage.camera()
		var sx := cam.unproject_position(nxt + to.normalized() * 0.05).x - cam.unproject_position(nxt).x
		var pose := str(gd["pose"])
		if _flap and str(role) == "kid":
			pose = "tf_bat_up" if fmod(_t, 0.36) < 0.18 else "tf_bat_down"
		var left := sx < -0.5 and a.view_of(pose) == "side"
		if pose != a.puppet.pose or left != a.facing_left:
			a.facing_left = left
			a.puppet.set_figure(pose, left, true)


# ------------------------------------------------------------------ finale

func _fountain() -> void:
	var m := _pot_mouth()
	var ids := ["story_wc_candies_00", "story_wc_candies_01", "story_wc_candies_02", "story_wc_candies_03",
		"story_wc_candies_04", "story_wc_candies_05"]
	for i in 12:
		var ang := randf() * TAU
		var to := m + _sx() * cos(ang) * randf_range(0.1, 0.24) + _out() * (0.02 + absf(sin(ang)) * 0.06)
		to.y = stage.world.ground.surface_y(Vector2(to.x, to.z)) + 0.02
		var c := fly(ids[i % ids.size()], m, to, 0.065, 0.9 + randf() * 0.4, 0.3, 999.0, 4.0)
		_candies.append(c)
	_sfx("wc.candy_pop", m)
	_sfx("wc.sparkle", m)


# ------------------------------------------------------------------ per frame

func step(dt: float) -> void:
	_t += dt
	var cam := stage.camera()
	# flyers
	for i in range(_flyers.size() - 1, -1, -1):
		var f: Dictionary = _flyers[i]
		if not is_instance_valid(f["node"]):  # (freed by all_back / _drop_flyer)
			_flyers.remove_at(i)
			continue
		var n: Node3D = f["node"]
		f["age"] = float(f["age"]) + dt
		var life: float = f["life"]
		var u := clampf(float(f["age"]) / life, 0.0, 1.0)
		if float(f["age"]) >= life + float(f["keep"]):
			n.queue_free()
			_flyers.remove_at(i)
			continue
		var e := u * (2.0 - u)
		var p: Vector3 = (f["from"] as Vector3).lerp(f["to"], e)
		p.y += sin(u * PI) * float(f["arc"])
		n.global_position = p
		var face := atan2(cam.global_position.x - p.x, cam.global_position.z - p.z)
		n.global_rotation = Vector3(0, face, float(f["spin"]) * float(f["age"]) * 0.3)
		var s := minf(1.0, u * 5.0 + 0.05)
		if float(f["keep"]) <= 0.0:
			s *= clampf((1.0 - u) * 4.0, 0.0, 1.0)
		elif float(f["age"]) > life + float(f["keep"]) - 0.25:
			s *= clampf((life + float(f["keep"]) - float(f["age"])) / 0.25, 0.0, 1.0)
		n.scale = Vector3.ONE * maxf(s, 0.01)
	# floaters (invitations hovering, bats circling)
	for k in _floaters.keys():
		var fl: Dictionary = _floaters[k]
		if not is_instance_valid(fl["node"]):
			_floaters.erase(k)
			continue
		var n: Node3D = fl["node"]
		var base: Vector3 = fl["base"]
		if fl.has("dur") and float(fl["t"]) < float(fl["dur"]):
			# flying in on the wind: a curve from the far street through a wide swing to the hover point, the card
			# flipping over and tumbling like paper, a flutter sound now and then
			fl["t"] = float(fl["t"]) + dt
			var u := clampf(float(fl["t"]) / float(fl["dur"]), 0.0, 1.0)
			var e := u * u * (3.0 - 2.0 * u)
			var p0: Vector3 = fl["from"]
			var p1: Vector3 = fl["mid"]
			var p2: Vector3 = base
			var q := p0.lerp(p1, e).lerp(p1.lerp(p2, e), e)
			q += _right() * sin(float(fl["t"]) * 3.1 + float(fl["ph"])) * 0.06 * (1.0 - u) + Vector3.UP * sin(float(fl["t"]) * 4.3) * 0.04 * (1.0 - u)
			n.global_position = q
			n.scale = Vector3(maxf(0.15, absf(cos(float(fl["t"]) * 5.0 * (1.0 - u * 0.7)))), 1, 1)
			n.rotation.z = sin(float(fl["t"]) * 3.7 + float(fl["ph"])) * 0.6 * (1.0 - u * 0.6)
			fl["flutter"] = float(fl["flutter"]) - dt
			if float(fl["flutter"]) <= 0.0 and u < 0.9:
				fl["flutter"] = 0.9
				_sfx("wc.flutter", q)
			if u >= 1.0 and _track == n:
				_track = null
			continue
		if fl.has("orbit"):
			var a := _t * 1.6 + float(fl["ph"])
			n.global_position = base + _right() * cos(a) * float(fl["orbit"]) + Vector3.UP * sin(a) * float(fl["orbit"]) * 0.5
		else:
			n.global_position = n.global_position.lerp(base + Vector3.UP * sin(_t * 2.2 + float(fl["ph"])) * float(fl["amp"]), 1.0 - exp(-1.6 * dt))
			n.rotation.z = sin(_t * 1.7 + float(fl["ph"])) * 0.25
	if is_instance_valid(_track):
		stage._focus_goal = _track.global_position - Vector3.UP * 0.25
	# the pot: the swirl bands spin
	for i in _swirls.size():
		var sw := _swirls[i] as Node3D
		sw.rotation.z += _swirl_speed * dt * (1.0 if i % 2 == 0 else 1.15)
	if _liquid and _liquid.visible and randf() < dt * (2.0 + _swirl_speed * 1.5):
		_bubble()
	if _liquid and _liquid.visible and _eerie <= 0.6 and fmod(_t, 0.8) < dt:  # gentle steam off the boiling top
		var po := _pot_open()
		var s0: Vector3 = po[0] + (po[1] as Vector3) * randf_range(-0.4, 0.4) * float(po[3]) + Vector3.UP * float(po[4]) * 0.6
		fly("story_wc_pot_16", s0, s0 + Vector3.UP * 0.12, 0.03, 1.2, 0.0, 0.0, 0.6)
	_step_glides(dt)
	_step_ghost(dt)
	_step_parade_ghost(dt)
	# the little ghost floats behind the last marcher
	if _ghost and _ghost_follow != "":
		var f2 := _a(_ghost_follow)
		if f2:
			var tgt := f2.global_position - stage.dir_vec("toward") * 0.0 + Vector3.UP * (0.12 + sin(_t * 2.4) * 0.03)
			var back := f2.global_position - _ghost.global_position
			back.y = 0.0
			if back.length() > 0.22:
				_ghost.global_position = _ghost.global_position.lerp(tgt, 1.0 - exp(-1.8 * dt))
			_ghost.global_position.y = lerpf(_ghost.global_position.y, tgt.y, 1.0 - exp(-3.0 * dt))
			_ghost.rotation.y = atan2(cam.global_position.x - _ghost.global_position.x, cam.global_position.z - _ghost.global_position.z)
	# shop lights on (beat 1), the street dims for the pumpkin glow
	if _shop_glow >= 0.0 and _shop_glow < 1.0:
		_shop_glow = minf(1.0, _shop_glow + dt * 0.8)
		_set_shop_lit(_shop_glow)
	if absf(_dim - _dim_t) > 0.001:
		_dim = move_toward(_dim, _dim_t, dt * 0.8)
		for q: Array in stage._lights:
			if is_instance_valid(q[0]) and (q[0] as Node3D).get_parent() != _sp("pot") and (q[0] as Node3D).get_parent() != _sp("beam"):
				(q[0] as OmniLight3D).light_energy = float(q[1]) * _dim
	if _rolling == "":
		var k2 := _a("kid")
		if k2 and not _glides.has("kid") and absf(k2.puppet.rotation.z) > 0.001:
			k2.puppet.rotation.z = 0.0
