extends TaleHandler
## 「늑대와 일곱 아기염소」 effects (TaleHandler, phase 1 first playable, 2026-11-23).
## The stage builds the goats' cottage page (house with a body and its room inside the footprint, the stall, the mill)
## and the oak / well page from script.json; this handler adds:
##  - the knock (the door leaf rattles), the chalk munch (crumbs) and the voice "ding", the paw through the door gap
##    seen from inside (dark, later floury white), the flour puff at the mill and the sneeze;
##  - hide and seek: the kids run to the bed / table / laundry basket and the furniture card turns into its hiding
##    variant (kids peeking out); the youngest into the clock; the swallowing happens off screen (the camera is on the
##    clock with the youngest's eyes behind its glass; we hear three gulps; the room is a mess afterwards);
##  - the youngest out of the clock; the snoring wolf, the kids popping out of his belly, the stones, the stitches;
##    the wake, the fall into the well with a splash, the soaking wet wolf jumping out; the dance;
##  - tale verb go_out (out through the door, down the steps, along the path).
## Story props it makes are registered with the stage overlap check (user rule: nothing overlaps, fx props too).

const PAW_GREY := "res://stories/wolf_goats/art/paw_grey.webp"
const PAW_WHITE := "res://stories/wolf_goats/art/paw_white.webp"
const PUFF := "story_wg_fx_01"
const SPLASH := "story_wg_fx_02"
const CHALK_BIT := "story_wg_fx_08"
const DROPS := "story_wg_fx_10"
const BUBBLE := "story_wg_fx_13"
const SPARKLE := "story_wg_fx_15"
const K6 := ["kid1", "kid2", "kid3", "kid4", "kid5", "kid6"]
# by row position; v2: kid3 runs to the basket with kid4 (from beside the table its dash was 0.2: no run reads)
const HIDE := {"bed": ["kid5", "kid6"], "table": ["kid1", "kid2"], "basket": ["kid3", "kid4"]}
const HIDE_VIA := {"basket": "basket_via"}  # kid4 goes round behind the row (nobody crosses anyone)

var _tex := {}
var _flyers: Array = []
var _cards: Dictionary = {}
var _t := 0.0
var _kid_voice := "kid1"
var _snore := false
var _dance := false
var _door_jig := 0.0
var _popped: Array = []


func setup() -> void:
	pass


func build_async() -> void:
	enter_beat(stage.beat)


func enter_beat(b: Dictionary) -> void:
	_kid_voice = str(b.get("kid_voice", stage.tale.get("kid_voice", "kid1")))
	var st := str((b.get("enter", {}) as Dictionary).get("state", ""))
	if st == "mess":
		for f in ["bed", "table", "basket", "chair"]:
			_show(f, false, true)
			_show(f + "_hide", false, true)
			_show(f + "_mess", true, true)
		_show("clock", true, true)
		if stage.set_piece("cottage"):
			stage.set_piece("cottage").open_door(true)
	var id := str(b.get("id", ""))
	_snore = id in ["tree", "belly"]
	if id == "belly" or id == "tree":
		_snore_card(true)
	if id == "well":
		_snore_card(false)


# ------------------------------------------------------------------ helpers

func _texid(id: String) -> Texture2D:
	if not _tex.has(id):
		if id.begins_with("res://"):
			_tex[id] = load(id)
		else:
			var e := SpreadStage.atlas_entry(id)
			_tex[id] = load("res://" + str(e.get("path", ""))) if not e.is_empty() else null
	return _tex[id]


func _card(id: String, h: float, yaw := NAN) -> Node3D:
	var node := Node3D.new()
	node.top_level = true
	stage.add_child(node)
	var tex := _texid(id)
	if tex:
		var c := PaperCard.new()
		c.texture = tex
		c.height = h
		c.thickness = clampf(h * 0.03, 0.002, 0.01)
		node.add_child(c)
	node.rotation.y = _view_yaw() if is_nan(yaw) else yaw
	return node


func _view_yaw() -> float:
	var t := stage.dir_vec("toward")
	return atan2(t.x, t.z)


func _toward() -> Vector3:
	return stage.dir_vec("toward")


func _right() -> Vector3:
	return stage.dir_vec("right")


func _a(r: String) -> StoryActor:
	return stage.actor(r)


func _sp(n: String) -> SetPiece:
	return stage.set_piece(n)


func _sfx(id: String, at: Variant = null) -> void:
	if SoundDirector.current:
		SoundDirector.current.play(id, at)


## A furniture variant shown / hidden: instantly (off camera) or as a paper fold / pop.
func _show(nm: String, on: bool, instant := false) -> void:
	var sp := _sp(nm)
	if sp == null or sp.hinge == null:
		return
	if on:
		if instant:
			(sp.hinge.get_parent() as Node3D).visible = true
			sp.hinge.snap(true)
			sp.shown = 1
		elif sp.shown == 0:
			sp.pop_card(0.0)
	else:
		if instant:
			sp.hinge.snap(false)
			(sp.hinge.get_parent() as Node3D).visible = false
			sp.shown = 0
		elif sp.shown > 0:
			sp.band_down(0, 0.0)


## The house's outward direction (its own front normal) and the door points.
func _out() -> Vector3:
	var sp := _sp("cottage")
	return sp.global_transform.basis.z.normalized() if sp else _toward()


func fly(id: String, from: Vector3, to: Vector3, h: float, life := 0.7, arc := 0.18, keep := false) -> Node3D:
	var n := _card(id, h)
	n.global_position = from
	n.set_meta("moving", true)
	_flyers.append({"node": n, "age": 0.0, "life": life, "from": from, "to": to, "arc": arc, "keep": keep})
	return n


func _puff_at(p: Vector3, h := 0.16) -> void:
	var n := _card(PUFF, h * 0.4)
	n.global_position = p
	n.set_meta("moving", true)
	var tw := create_tween()
	tw.tween_property(n, "scale", Vector3.ONE * 2.6, 0.5).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	tw.tween_property(n, "scale", Vector3.ONE * 0.01, 0.6).set_delay(0.5)
	tw.tween_callback(n.queue_free)


# ------------------------------------------------------------------ tap targets

func targets() -> Array:
	var out := []
	var w := _a("wolf")
	if w and w.pop_target > 0.5 and str(stage.beat.get("id", "")) == "belly":
		out.append("belly")
	if _stone_left() != "":
		out.append("stones")
	return out


func target_point(t: String) -> Variant:
	match t:
		"belly":
			var w := _a("wolf")
			return w.global_position + Vector3.UP * 0.07 if w else null
		"stones":
			var nm := _stone_left()
			return _sp(nm).centre() if nm != "" else null
	return null


func target_radius(t: String) -> float:
	return 80.0 if target_point(t) != null else -1.0


func _stone_left() -> String:
	for nm in ["stone_a", "stone_b"]:
		if _sp(nm) and _sp(nm).visible and not _sp(nm).has_meta("used"):
			return nm
	return ""


func wiggle(t: String) -> bool:
	return t in ["belly", "stones"]


## SPEAKER_OFF: the kids' lines are said by one kid (the eldest, the youngest in its own beats).
func speaker_point(who: String) -> Variant:
	if who == "kid":
		var a := _a(_kid_voice)
		if a and a.visible and a.pop_s > 0.5:
			return a.centre()
		for r in K6 + ["baby"]:
			var b := _a(r)
			if b and b.visible and b.pop_s > 0.5:
				return b.centre()
	return null


# ------------------------------------------------------------------ fx

func fx(name: String) -> bool:
	var p := name.split(":")
	var wolf := _a("wolf")
	var mom := _a("mom")
	match p[0]:
		"kids_hop":
			for i in K6.size() + 1:
				var r := (K6 + ["baby"])[i] as String
				var a := _a(r)
				if a:
					get_tree().create_timer(0.12 * i).timeout.connect(func(): a.hop_v = 0.8)
					get_tree().create_timer(0.12 * i + 0.55).timeout.connect(func(): a.hop_v = 0.6)
			return true
		"mom_warn":
			if mom:
				mom.set_pose("warn")
			return true
		"knock":
			if wolf:
				wolf.set_pose("knock")
				if _sp("cottage"):
					wolf.face_point(_sp("cottage").global_position)
			_door_jig = 0.9
			return true
		"show_paw":  # the dark paw held up at the door (side figure, turned to the door)
			if wolf:
				wolf.set_pose("knock")
				if _sp("cottage"):
					wolf.face_point(_sp("cottage").door_point(true, _out()))
			return true
		"munch":
			if wolf:
				wolf.set_pose("munch")
				for k in 4:
					fly(CHALK_BIT, wolf.centre() + Vector3.UP * 0.12, wolf.centre() + Vector3.UP * 0.02
						+ _right() * randf_range(-0.12, 0.12) + _toward() * 0.05, 0.02, 0.5, 0.06)
			return true
		"voice_ding":
			if wolf:
				wolf.set_pose("sweet")
				for k in 5:
					fly(SPARKLE, wolf.centre() + Vector3.UP * 0.1, wolf.centre() + Vector3.UP * 0.25
						+ _right() * randf_range(-0.12, 0.12), 0.05, 0.7, 0.08)
			return true
		"paw_in":  # the paw through the door gap, seen from inside (by the hinge side of the door)
			var white := p.size() > 1 and p[1] == "white"
			var d := stage.spot_point("door_in")
			var o := _out()
			var side := o.cross(Vector3.UP).normalized()  # along the wall
			var paw := _card(PAW_WHITE if white else PAW_GREY, 0.11, atan2(-o.x, -o.z))
			paw.global_position = d + o * 0.17 + Vector3.UP * 0.05 - side * 0.32
			paw.set_meta("moving", true)
			var to := d + o * 0.17 + Vector3.UP * 0.05 - side * 0.2
			_flyers.append({"node": paw, "age": 0.0, "life": 0.9, "from": paw.global_position, "to": to, "arc": 0.0,
				"keep": true})
			_cards["paw"] = paw
			stage.register_prop("paw", paw, 0.05, 0.11)
			return true
		"paw_out":
			if _cards.has("paw"):
				var pn: Node3D = _cards["paw"]
				_cards.erase("paw")
				stage.unregister_prop("paw")
				var tw := create_tween()
				tw.tween_property(pn, "global_position", pn.global_position - _out().cross(Vector3.UP).normalized() * 0.14, 0.5)
				tw.tween_callback(pn.queue_free)
			return true
		"flour":
			var sk := _sp("sack")
			if sk:
				_puff_at(sk.global_position + Vector3.UP * 0.12)
				sk.bounce()
			if wolf:
				wolf.set_pose("search")
			return true
		"sneeze":
			if wolf:
				wolf.set_pose("sneeze")
				_puff_at(wolf.global_position + Vector3.UP * wolf.puppet.height * 0.85 + _toward() * 0.05, 0.12)
			return true
		"wolf_in":
			for r in K6:
				if _a(r):
					_a(r).set_pose("scared")
			if _a("baby"):
				_a("baby").set_pose("worried")
			return true
		"hide":  # hide:<bed|table|basket>: its kids run to it, dive in; the card becomes the hiding variant
			_hide_run(p[1])
			return true
		"clock_hide":
			_clock_hide()
			return true
		"swallow":
			_swallow()
			return true
		"clock_out":
			_clock_out()
			return true
		"snore_on":
			_snore = true
			_snore_card(true)
			return true
		"snip", "sew":
			if mom:
				mom.hop_v = 0.25
			return true
		"belly_pop":
			_belly_pop(int(p[1]))
			return true
		"stone":
			_stone(int(p[1]))
			return true
		"stitched":
			if wolf:
				wolf.set_pose("sleep_stones")
			if mom:
				mom.set_pose("ready")
			return true
		"wake":
			_snore = false
			_snore_card(false)
			if wolf:
				wolf.set_pose("groggy")
				wolf.hop_v = 0.5
			return true
		"fall_well":
			_fall_well()
			return true
		"wet_out":
			_wet_out()
			return true
		"dance_on":
			_dance = true
			return true
	return false


func _snore_card(on: bool) -> void:
	if on and not _cards.has("bubble"):
		var w := _a("wolf")
		if w:
			var b := _card(BUBBLE, 0.07)
			b.global_position = w.global_position + Vector3.UP * 0.1 - _right() * 0.2 + _toward() * 0.02
			b.set_meta("moving", true)
			_cards["bubble"] = b
	elif not on and _cards.has("bubble"):
		(_cards["bubble"] as Node3D).queue_free()
		_cards.erase("bubble")


func _hide_run(f: String) -> void:
	var front := stage.spot_point(f + "_front")
	var kids: Array = HIDE.get(f, [])
	for i in kids.size():
		var a := _a(str(kids[i]))
		if a == null:
			continue
		a.set_pose("scared")
		var pts: Array = []
		if HIDE_VIA.has(f):  # two to the basket: the first (from further left) goes round a step deeper (no bump)
			pts.append(stage.spot_point(HIDE_VIA[f]) - _toward() * 0.12 * (kids.size() - 1 - i))
		pts.append(front + _right() * 0.11 * (i - 1) + _toward() * 0.04 * (i % 2))
		a.follow(pts, 0.6, "run_cycle", false)
	var g := 0.0
	while g < 4.0:
		var busy := false
		for r in kids:
			if _a(str(r)) and _a(str(r)).moving():
				busy = true
		if not busy:
			break
		g += get_process_delta_time()
		await get_tree().process_frame
	for r in kids:
		var a2 := _a(str(r))
		if a2:
			a2.hop_v = 0.6
			a2.pop_target = 0.02
	await get_tree().create_timer(0.15).timeout
	_show(f, false, true)
	_show(f + "_hide", true, true)
	if _sp(f + "_hide"):
		_sp(f + "_hide").bounce()


func _clock_hide() -> void:
	var b := _a("baby")
	if b == null:
		return
	b.set_pose("worried")
	_show("clock", false, true)
	_show("clock_open", true, true)
	b.follow([stage.spot_point("in_clock_front")], 0.5, "run_cycle", false)
	var g := 0.0
	while b.moving() and g < 4.0:
		g += get_process_delta_time()
		await get_tree().process_frame
	b.hop_v = 0.7
	await get_tree().create_timer(0.2).timeout
	b.pop_target = 0.02
	_show("clock_open", false, true)
	_show("clock_kid", true, true)
	await get_tree().create_timer(0.7).timeout
	_show("clock_kid", false, true)
	_show("clock", true, true)
	_sfx("door.shut")


## Off screen (the camera is on the clock): the hiding places are found one by one -- gulp -- and the room is a mess.
func _swallow() -> void:
	_show("clock", false, true)
	_show("clock_eyes", true, true)
	var wolf := _a("wolf")
	for k in 3:
		await get_tree().create_timer(0.9).timeout
		_sfx("wg.gulp" if k % 2 == 0 else "wg.gulp_2")
	for f in ["bed", "table", "basket", "chair"]:
		_show(f, false, true)
		_show(f + "_hide", false, true)
		_show(f + "_mess", true, true)
	if wolf:
		wolf.set_pose("heavy_front_0")


func _clock_out() -> void:
	var b := _a("baby")
	_show("clock_eyes", false, true)
	_show("clock", false, true)
	_show("clock_kid", true, true)
	if _sp("clock_kid"):
		_sp("clock_kid").bounce()
	await get_tree().create_timer(0.6).timeout
	_show("clock_kid", false, true)
	_show("clock_open", true, true)
	if b:
		b.place_at(stage.spot_point("in_clock") + _out() * 0.05)
		b.pop_delay = 0.0
		b.pop_target = 1.0
		b.set_pose("joy_jump")
		b.hop_v = 1.0
		b.follow([stage.spot_point("in_baby2")], 0.5, "", false)


func _belly_pop(k: int) -> void:
	var wolf := _a("wolf")
	if wolf == null:
		return
	var base := wolf.global_position + Vector3.UP * 0.06
	for j in 2:
		var r: String = K6[(k - 1) * 2 + j]
		var a := _a(r)
		if a == null:
			continue
		var goal := stage.spot_point("pop_" + r)
		var from := base + _right() * 0.04 * (j * 2 - 1)
		a.place_at(from)
		a.lift = 0.0
		a.pop_delay = 0.15 * j
		a.pop_target = 1.0
		a.set_pose("pop")
		# v2 (audit: "kids float out of the belly" -- a constant-speed walk cycle along two straight legs in the air):
		# a quick ballistic leap holding the drawn "pop" figure (the path height in the move's own state), a little
		# bounce and a thud on landing
		_leap(a, from, goal, 0.18, 0.55, 0.15 * j)
		_popped.append(r)
		get_tree().create_timer(1.1).timeout.connect(func():
			if is_instance_valid(a):
				a.set_pose("joy"))
		_sfx("wg.marimba_%d" % [1, 3, 5][(k - 1) % 3])


## A leap along a parabola (peak `h` over the higher end, `dur` s) holding the actor's current figure; lands with a bounce.
func _leap(a: StoryActor, from: Vector3, to: Vector3, h: float, dur: float, delay := 0.0) -> void:
	if delay > 0.0:
		await get_tree().create_timer(delay).timeout
	if not is_instance_valid(a):
		return
	var t := 0.0
	while t < dur and is_instance_valid(a):
		t += get_process_delta_time()
		var k := clampf(t / dur, 0.0, 1.0)
		var p := from.lerp(to, k)
		p.y = lerpf(from.y, to.y, k)
		a.nudge(p)
		a.lift = 4.0 * h * k * (1.0 - k)
		await get_tree().process_frame
	if is_instance_valid(a):
		a.lift = 0.0
		a.place_at(to)
		a.hop_v = 0.35
		_sfx("foot.pig.grass", to)


func _stone(k: int) -> void:
	var nm := _stone_left()
	var sp := _sp(nm) if nm != "" else null
	if sp:
		sp.set_meta("used", true)
	var kid := _a("kid6" if k == 1 else "kid5")  # the pair landed nearest the stones
	var wolf := _a("wolf")
	if sp == null or wolf == null:
		return
	var belly := wolf.global_position + Vector3.UP * 0.02 + _toward() * 0.05
	if kid:
		kid.set_pose("push")
		kid.follow([sp.global_position + _right() * 0.13 + _toward() * 0.02, belly + _right() * (0.32 if k == 1 else 0.5) + _toward() * (0.14 if k == 1 else 0.04)], 0.4, "push", false)
	var tw := create_tween()
	tw.tween_property(sp, "global_position", belly + _right() * 0.12, 0.9).set_delay(0.35)
	tw.tween_property(sp, "scale", Vector3.ONE * 0.01, 0.25)
	tw.tween_callback(func():
		sp.visible = false
		if kid:
			kid.set_pose("joy"))


func _fall_well() -> void:
	var wolf := _a("wolf")
	var w := _sp("well")
	if wolf == null or w == null:
		return
	no_spacing_add("wolf")
	var c := w.global_position
	var behind := c - _toward() * 0.05
	wolf.set_pose("tumble")
	wolf.follow([behind + Vector3.UP * 0.42, behind + Vector3.UP * 0.3, behind + Vector3.UP * -0.5], 0.9, "", true)
	await get_tree().create_timer(0.85).timeout
	_sfx("wg.splash", c)
	var s := _card(SPLASH, 0.2)
	s.global_position = c + Vector3.UP * 0.2 + _toward() * 0.01
	s.scale = Vector3.ONE * 0.2
	s.set_meta("moving", true)
	_cards["splash"] = s
	var tw := create_tween()
	tw.tween_property(s, "scale", Vector3.ONE * 1.1, 0.35).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
	tw.tween_interval(0.6)
	tw.tween_property(s, "scale", Vector3.ONE * 0.01, 0.4)
	tw.tween_callback(func():
		s.queue_free()
		_cards.erase("splash"))
	await get_tree().create_timer(0.3).timeout
	wolf.pop_target = 0.02


func no_spacing_add(r: String) -> void:
	if not stage.no_spacing.has(r):
		stage.no_spacing.append(r)


func _wet_out() -> void:
	var wolf := _a("wolf")
	var w := _sp("well")
	if wolf == null or w == null:
		return
	var c := w.global_position - _toward() * 0.05
	var goal := stage.spot_point("wolf_wet")
	wolf.place_at(c + Vector3.UP * 0.1)
	wolf.pop_delay = 0.0
	wolf.pop_target = 1.0
	wolf.set_pose("wet")
	wolf.follow([c + Vector3.UP * 0.55, goal + Vector3.UP * 0.25, goal], 1.0, "", true)
	for k in 6:
		fly(DROPS, c + Vector3.UP * 0.45, c + Vector3.UP * 0.2 + _right() * randf_range(-0.3, 0.3)
			+ _toward() * randf_range(0.0, 0.2), 0.05, 0.6, 0.2)
	await get_tree().create_timer(1.2).timeout
	stage.no_spacing.erase("wolf")


# ------------------------------------------------------------------ tale verbs

func run_step(st: Dictionary, R: Node) -> void:
	match str(st.get("do", "")):
		"go_out":
			await _go_out(st, R)
		_:
			push_warning("wolf_goats: unknown step " + str(st.get("do", "")))


## go_out {who, house, to (spot outside), pose, shot, line, keep_open, then {to, exit}}: the door opens (inward), each
## walks to the doorway, up onto the sill, out and down the steps, on to `to`; the door shuts behind them unless
## keep_open; `then` walks on (and off the page).
func _go_out(st: Dictionary, R: Node) -> void:
	var sp := _sp(str(st.get("house", "cottage")))
	if sp == null:
		return
	sp.open_door(true)
	_sfx("door.open", sp.global_position)
	var g := 0.0
	while sp.door_open_amount() < 0.95 and g < 2.0:
		g += await R._frame()
	if st.has("line"):
		R._say.bind(str(st["line"])).call()
	var o := _out()
	var sill := sp.door_sill()
	var fr := sp.door_point(true, o)
	var bk := sp.door_point(false, o)
	var to := stage.spot_point(st.get("to", "road_door"))
	var pose := str(st.get("pose", ""))
	var roles: Array = st.get("who", [])
	for i in roles.size():
		var a := _a(str(roles[i]))
		if a == null:
			continue
		var pts := [bk - o * 0.06 + Vector3.UP * 0.02, bk + Vector3.UP * sill, fr - o * 0.1 + Vector3.UP * sill,
			fr - o * 0.04 + Vector3.UP * sill * 0.5, fr + o * 0.06, to]
		a.follow(pts, float(st.get("speed", 0.4)), pose, true)
		if st.has("shot") and i == 0:
			stage.shot_to(str(st["shot"]), "door_view" if str(st["shot"]) == "house" else "in_focus", {"rate": 1.4})
		var g2 := 0.0
		while a.moving() and a._path.size() > 1 and g2 < 10.0:
			g2 += await R._frame()
	if not st.get("keep_open", false):
		sp.open_door(false)
		_sfx("door.shut", sp.global_position)
	for r in roles:
		var g3 := 0.0
		while _a(str(r)) and _a(str(r)).moving() and g3 < 10.0:
			g3 += await R._frame()
	var then: Dictionary = st.get("then", {})
	if not then.is_empty():
		for r in roles:
			var a2 := _a(str(r))
			if a2:
				a2.follow([stage.spot_point(then.get("to", "road_far"))], float(then.get("speed", 0.45)), pose, false)
		if then.has("follow") and not roles.is_empty():  # v2: the camera follows him off up the road
			stage.follow_actor(str(roles[0]), str(then["follow"]))
		var g4 := 0.0
		while g4 < 12.0:
			var busy := false
			for r in roles:
				if _a(str(r)) and _a(str(r)).moving():
					busy = true
			if not busy:
				break
			g4 += await R._frame()
		if then.get("exit", false):
			for r in roles:
				if _a(str(r)):
					_a(str(r)).pop_target = 0.02
	while R._line_busy:
		await R._frame()


# ------------------------------------------------------------------ per frame

func step(dt: float) -> void:
	_t += dt
	# the door rattles under the knock
	var sp := _sp("cottage")
	if sp and sp.door_pivot:
		if _door_jig > 0.0:
			_door_jig = maxf(0.0, _door_jig - dt)
			sp.door_pivot.rotation.x = sin(_t * 40.0) * 0.02 * minf(1.0, _door_jig * 3.0)
		else:
			sp.door_pivot.rotation.x = 0.0
	# the inside face of the front wall: the drawn closed door, or the doorway cut out while the door stands open
	var wi := _sp("wall_in")
	var wo := _sp("wall_in_open")
	if sp and wi and wo:
		var open := sp.door_open_amount() > 0.08
		var shown := wi.visible or wo.visible
		wi.visible = shown and not open
		wo.visible = shown and open
	if _cards.has("bubble"):
		var b: Node3D = _cards["bubble"]
		var k := 0.6 + 0.5 * (0.5 + 0.5 * sin(_t * 2.2))
		b.scale = Vector3.ONE * k
	if _dance:
		var i := 0
		for r in K6 + ["baby", "mom"]:
			var a := _a(str(r))
			if a and not a.moving() and fmod(_t + i * 0.23, 0.9) < dt:
				a.hop_v = 0.45 if r != "mom" else 0.3
			i += 1
	for f: Dictionary in _flyers.duplicate():
		var n: Node3D = f["node"]
		if not is_instance_valid(n):
			_flyers.erase(f)
			continue
		f["age"] = float(f["age"]) + dt
		var k2 := clampf(float(f["age"]) / float(f["life"]), 0.0, 1.0)
		n.global_position = (f["from"] as Vector3).lerp(f["to"], k2) + Vector3.UP * sin(k2 * PI) * float(f["arc"])
		if k2 >= 1.0:
			_flyers.erase(f)
			if f.get("keep", false):
				n.remove_meta("moving")
			else:
				n.queue_free()
