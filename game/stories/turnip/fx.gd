extends TaleHandler
## 「커다란 순무」 effects (TaleHandler, 2026-11-23).
## The stage builds the farm (seed 3, view 4), the house, barn, garden dressing and the six actors from script.json;
## this handler adds what only this tale does:
##  - the turnip as one growing card at its spot: the dug hole -> sprout -> young leaves -> leaf crown -> the giant
##    turnip sunk to its violet shoulder (the ground hides the bulb), rising a little with each pull, flying out on
##    the last one and landing on its side;
##  - the seed in grandpa's palm (tap target), water drops, sun sparkles, summer flowers popping;
##  - the pulling line: every heave leans the whole line back (a spring on each actor's pop node, pivot at the feet,
##    in the screen plane) with clods flying off the turnip; everyone tumbles back when it comes out;
##  - the hidden helpers: the puppy behind the bush, the cat on the barn's ridge (hops down on an arc), the mouse in
##    its hole;
##  - the feast: the pot, the bread and the chopping board on the table, steam, a bowl flying from the pot to each.
## Lines play through the runner, so captions, faces (line expr) and SEG logs stay generic.

const T_WHOLE := "story_tn_garden_00"
const T_CROWN := "story_tn_garden_01"
const T_SPROUT := "story_tn_garden_02"
const T_YOUNG := "story_tn_garden_03"
const SEED := "story_tn_garden_04"
const HOLE := "story_tn_garden_15"  ## v4: the planting hole, a small dark dip laid flat in the furrow
const HEAP := "story_tn_garden_16"  ## v4: the tiny heap of loose soil beside it (was 05, a burrow-like mound)
const DROPS := "story_tn_garden_07"
const CLODS := "story_tn_garden_08"
const POT := "story_tn_feast_01"
const BOWL := "story_tn_feast_02"
const BOARD := "story_tn_feast_03"
const STEAM := "story_tn_feast_05"
const BREAD := "story_tn_feast_06"
const SPARKLE := "story_wg_fx_15"
const FLOWERS := ["meadow_field_12", "small_decor_01", "meadow_field_11", "small_decor_05", "meadow_field_14"]
const LINE := ["grandpa", "grandma", "girl", "dog", "cat", "mouse"]

const BIG_H := 0.62  ## the whole turnip card (leaves + bulb + root)
const SINK0 := 0.31  ## how deep the giant turnip starts (the violet shoulder at the soil)

var _tex := {}
var _cards: Dictionary = {}  ## name -> Node3D
var _flyers: Array = []
var _grow: Array = []  ## [{node, t, from, to}] scale tweens (pop up / fold down)
var _lean := {}  ## role -> [angle, velocity]
var _turnip_state := ""
var _rise := 0.0
var _wob := 0.0
var _wob_v := 0.0
var _t := 0.0
var _hops: Array = []  ## [{role, t, life, from, to, h0, arc}] (the cat off the ridge)
var _out := {}  ## the turnip's flight: {t, from, to}
var _steam_t := -1.0
var _carry := {}  ## v2: the pulled turnip rolled from the garden to beside the table {t, from, node}


func setup() -> void:
	for r in LINE:
		if not stage.no_spacing.has(r):
			stage.no_spacing.append(r)  # the line holds on (contacts); the solver must not push it apart
	_no_smoke()


## v4 (user: "왜 자꾸 이상한데서 김이 모락모락 나는거???"): the template's chimney smoke kept rising where its houses had
## been cleared for the farm (over the thatched roof, in the garden): no smoke on this farm; the only steam is the pot's.
func _no_smoke() -> void:
	if stage.world == null:
		return
	for n in stage.world.get_children():
		if n is ChimneySmoke:
			(n as Node3D).visible = false
			n.process_mode = Node.PROCESS_MODE_DISABLED


func build_async() -> void:
	var tn: Dictionary = stage.beat.get("tn", {})
	_set_turnip(str(tn.get("turnip", "")), float(tn.get("rise", 0.0)))
	enter_beat(stage.beat)


func enter_beat(b: Dictionary) -> void:
	var hid: Dictionary = (b.get("enter", {}) as Dictionary).get("hidden", {})
	for r in hid:
		var a := stage.actor(str(r))
		if a:
			a.place_at(stage.spot_point(hid[r]) - _toward() * 0.14)
			a.pop_target = 0.02
			a.pop_delay = 0.0
	if str(b.get("id", "")) == "feast":
		for r in LINE:
			_lean[r] = [0.0, 0.0]


# ------------------------------------------------------------------ helpers

func _texid(id: String) -> Texture2D:
	if not _tex.has(id):
		var e := SpreadStage.atlas_entry(id)
		_tex[id] = load("res://" + str(e.get("path", ""))) if not e.is_empty() else null
	return _tex[id]


func _card(id: String, h: float) -> Node3D:
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
	node.rotation.y = _view_yaw()
	return node


## v4: soil pieces (hole, heap, seed) without the cream die-cut rim (it outlined the hole like a sticker) and with a
## soil-dark cut edge. PaperCard sets its (texture-cached) materials when its mesh is built: wait for them.
func _soil(c: PaperCard) -> void:
	if not is_instance_valid(c):
		return
	var m0 := c.get_surface_override_material(0) as ShaderMaterial
	var m2 := c.get_surface_override_material(2) as ShaderMaterial
	if m0 == null or m2 == null:
		get_tree().process_frame.connect(_soil.bind(c), CONNECT_ONE_SHOT)
		return
	m0.set_shader_parameter("rim_mix", 0.0)
	m2.set_shader_parameter("edge_color", Color("#3a281c"))


func _view_yaw() -> float:
	var t := stage.dir_vec("toward")
	return atan2(t.x, t.z)


func _toward() -> Vector3:
	return stage.dir_vec("toward")


func _right() -> Vector3:
	return stage.dir_vec("right")


func _sfx(id: String, at: Variant = null) -> void:
	if SoundDirector.current:
		SoundDirector.current.play(id, at)


func _spot(nm: String) -> Vector3:
	return stage.spot_point(nm)


func _free(nm: String) -> void:
	if _cards.has(nm):
		var n: Node3D = _cards[nm]
		if is_instance_valid(n):
			n.queue_free()
		_cards.erase(nm)
		stage.unregister_prop(nm)


## A card pops up out of the page (overshoot, quiver) or folds down and is freed.
func _pop(n: Node3D, up := true, free_after := false) -> void:
	if up:
		n.scale = Vector3(1, 0.02, 1)
	_grow.append({"node": n, "t": 0.0, "up": up, "free": free_after})


func fly(id: String, from: Vector3, to: Vector3, h: float, life := 0.7, arc := 0.18, keep := false) -> Node3D:
	var n := _card(id, h)
	n.global_position = from
	n.set_meta("moving", true)
	_flyers.append({"node": n, "age": 0.0, "life": life, "from": from, "to": to, "arc": arc, "keep": keep})
	return n


# ------------------------------------------------------------------ the turnip

func _turnip_base() -> Vector3:
	return _spot("turnip")


## The turnip's look for a state: "" nothing, hole (the dug heap), sprout, young, crown, big (sunk), out (pulled,
## lying on its side where it landed).
func _set_turnip(state: String, rise := 0.0) -> void:
	_turnip_state = state
	_rise = rise
	for k in ["heap", "turnip"]:
		_free(k)
	var p := _turnip_base()
	match state:
		"hole":  # v4: a shallow planting hole (a dark dip laid flat in the furrow) + a tiny heap of loose soil beside it
			var h := _card(HEAP, 0.026)
			h.global_position = p
			var hc := h.get_child(0) as Node3D
			if hc:
				hc.position = Vector3(-0.075, 0.0, -0.012)  # to the hole's left (away from grandpa), a little behind
				_soil(hc as PaperCard)
			var tex := _texid(HOLE)
			if tex:
				var d := PaperCard.new()
				d.texture = tex
				d.height = 0.055  # the dip's depth on the ground (front to back); ~0.073 wide
				d.thickness = 0.0012
				h.add_child(d)
				_soil(d)
				d.rotation = Vector3(-PI * 0.5, 0.0, 0.0)  # lies on the soil, print up, its top edge away from us
				d.position = Vector3(0.0, 0.003, 0.0275)  # centred on the turnip spot, just over the plot sheet
			_cards["heap"] = h
			stage.register_prop("heap", h, 0.05, 0.03)
		"sprout", "young", "crown":
			var id := {"sprout": T_SPROUT, "young": T_YOUNG, "crown": T_CROWN}[state] as String
			var hh := {"sprout": 0.05, "young": 0.13, "crown": 0.26}[state] as float
			var c := _card(id, hh)
			c.global_position = p
			_cards["turnip"] = c
			stage.register_prop("turnip", c, hh * 0.35, hh)
		"big":
			var t := _card(T_WHOLE, BIG_H)
			t.global_position = p + Vector3.UP * (rise - SINK0)
			_cards["turnip"] = t
			stage.register_prop("turnip", t, 0.12, BIG_H - SINK0)
		"out":
			var o := _card(T_WHOLE, BIG_H)
			_lay(o, _spot("turnip_land"))
			_cards["turnip"] = o
			stage.register_prop("turnip", o, 0.2, 0.3)


## Lying on its side, leaves to the left, the bulb resting on the ground.
func _lay(n: Node3D, at: Vector3) -> void:
	n.global_position = at + Vector3.UP * 0.15 + _right() * 0.32
	n.global_transform.basis = Basis(_toward(), deg_to_rad(80.0)) * Basis(Vector3.UP, _view_yaw())


func _grow_to(state: String) -> void:
	var old: Node3D = _cards.get("turnip")
	var oh: Node3D = _cards.get("heap")
	_cards.erase("turnip")
	_cards.erase("heap")
	stage.unregister_prop("turnip")
	stage.unregister_prop("heap")
	_set_turnip(state, 0.0)
	if old and is_instance_valid(old):
		_pop(old, false, true)
	if oh and is_instance_valid(oh):
		_pop(oh, false, true)
	if _cards.has("turnip"):
		_pop(_cards["turnip"])  # v4: no sparkle burst here (cream puffs over the garden read as stray steam)


# ------------------------------------------------------------------ tap targets

func targets() -> Array:
	var out: Array = []
	for k in ["seed", "turnip", "pot"]:
		if _cards.has(k):
			out.append(k)
	if _cards.has("turnip") and _turnip_state in ["sprout", "young", "crown"]:
		out.append("sprout")
	return out


func target_point(t: String) -> Variant:
	match t:
		"seed":
			if _cards.has("seed"):
				return (_cards["seed"] as Node3D).global_position + Vector3.UP * 0.02
		"sprout":
			if _cards.has("turnip"):
				return _turnip_base() + Vector3.UP * 0.07
		"turnip":
			if _cards.has("turnip"):
				return _turnip_base() + Vector3.UP * (0.16 if _turnip_state == "big" else 0.08)
		"pot":
			if _cards.has("pot"):
				return (_cards["pot"] as Node3D).global_position + Vector3.UP * 0.06
	return null


## SPEAKER_OFF: the mouse squeaks from inside its hole before it comes out.
func speaker_point(who: String) -> Variant:
	var a := stage.actor(who)
	if who == "mouse" and a and a.pop_target < 0.5:
		return _spot("mouse_hole") + Vector3.UP * 0.04
	return null


func target_radius(t: String) -> float:
	return 95.0 if target_point(t) != null else -1.0


func wiggle(t: String) -> bool:
	if t in ["seed", "sprout", "turnip", "pot"]:
		_wob_v += 1.2
		return true
	return false


# ------------------------------------------------------------------ fx

func fx(name: String) -> bool:
	var p := name.split(":")
	match p[0]:
		"dig":  # the hole grandpa digs (the heap with its hole pops up beside him)
			if _turnip_state == "":
				_set_turnip("hole")
				_pop(_cards["heap"])
			return true
		"seed_palm":  # a seed in grandpa's palm, just above the hole
			var s := _card(SEED, 0.022)
			_soil(s.get_child(0) as PaperCard)
			s.global_position = _spot("line_grandpa") - _right() * 0.1 + Vector3.UP * 0.05 + _toward() * 0.03
			_cards["seed"] = s
			_pop(s)
			return true
		"plant_seed":  # 또르르: the seed rolls off his palm into the hole
			if _cards.has("seed"):
				var s2: Node3D = _cards["seed"]
				_cards.erase("seed")
				fly(SEED, s2.global_position, _turnip_base() + Vector3.UP * 0.004, 0.022, 0.6, 0.05)  # into the dip
				s2.queue_free()
			var gp := stage.actor("grandpa")
			if gp:
				gp.set_pose("plant")
			return true
		"sprout":
			_grow_to("sprout")
			var g2 := stage.actor("grandpa")
			if g2:
				g2.set_pose("surprised")
			return true
		"water":
			var g3 := stage.actor("grandpa")
			if g3:
				g3.set_pose("water", 1)
			var c3 := _turnip_base()
			for k in 3:
				fly(DROPS, c3 + Vector3.UP * 0.2 + _right() * 0.02 * k, c3 + Vector3.UP * 0.02, 0.07, 0.6 + 0.15 * k, 0.0)
			get_tree().create_timer(0.9).timeout.connect(_grow_to.bind("young"))
			return true
		"sun":
			var g4 := stage.actor("grandpa")
			if g4:
				g4.set_pose("side_walk", 1)
			stage._set_light("afternoon", false)
			var c4 := _turnip_base() + Vector3.UP * 0.5
			for k in 10:
				fly(SPARKLE, c4 + Vector3(randf_range(-0.3, 0.3), randf_range(0.0, 0.3), 0.0),
					_turnip_base() + Vector3.UP * 0.1, 0.05, 0.9 + 0.05 * k, 0.0)
			get_tree().create_timer(0.6).timeout.connect(_grow_to.bind("crown"))
			return true
		"summer":  # 여름이 되었어요: the giant turnip, summer flowers round the garden
			_grow_to("big")
			_rise = 0.0
			(_cards["turnip"] as Node3D).global_position = _turnip_base() + Vector3.UP * -SINK0
			# round the garden plot, never in its rows (v2)
			var spots := [[-3.35, -1.1], [-0.35, -1.55], [-2.95, -1.75], [-1.55, -0.16], [-0.1, -0.7]]
			for k in spots.size():
				var f := _card(FLOWERS[k], 0.15)
				f.global_position = stage.spot_point(spots[k])
				_pop(f)
				_cards["flower%d" % k] = f
			var g5 := stage.actor("grandpa")
			if g5:
				g5.set_pose("surprised")
			return true
		"heave":  # heave:<n pullers>:<rise>: the line leans back, the turnip wobbles and comes up a little
			var n := int(p[1])
			var rise := float(p[2]) if p.size() > 2 else 0.0
			for i in mini(n, LINE.size()):
				var r: String = LINE[i]
				var a := stage.actor(r)
				if a and a.pop_target > 0.5:
					a.set_pose("pull", 1)
					var L: Array = _lean.get(r, [0.0, 0.0])
					L[1] = float(L[1]) + 0.9 + 0.08 * i
					_lean[r] = L
			_rise += rise
			_wob_v += 2.2
			stage.shake(0.35)
			var c5 := _turnip_base() + Vector3.UP * 0.02
			for k in 2:
				fly(CLODS, c5, c5 + _right() * randf_range(-0.25, -0.08) + Vector3.UP * 0.02 + _toward() * 0.08, 0.035, 0.5, 0.14)
			return true
		"fall":  # fall:<role>: 아이코! on his bottom
			var a2 := stage.actor(p[1])
			if a2:
				_lean[p[1]] = [0.0, 0.0]
				a2.set_pose("tumble", 1)
				a2.hop_v = 0.5
			return true
		"get_up":
			var a3 := stage.actor(p[1])
			if a3:
				a3.set_pose("pull", 1)
				a3.hop_v = 0.4
			return true
		"rustle":  # the bush shakes (someone behind it)
			var sp := stage.set_piece(p[1])
			if sp:
				sp.bounce()
				get_tree().create_timer(0.45).timeout.connect(sp.bounce)
			_sfx("tn.bark", _spot(p[1]))
			return true
		"dog_out":
			var d := stage.actor("dog")
			if d:
				d.place_at(_spot("bush_out"))
				d.pop_delay = 0.0
				d.pop_target = 1.0
				d.set_pose("happy")
				d.hop_v = 0.8
			var b := stage.set_piece("bush")
			if b:
				b.bounce()
			return true
		"cat_roof":  # the cat stands up on the barn's ridge
			var c := stage.actor("cat")
			var barn := stage.set_piece("barn")
			if c and barn:
				c.place_at(barn.global_position + _toward() * 0.03)
				c.lift = barn.height * 0.97
				c.pop_delay = 0.0
				c.pop_target = 1.0
				c.set_pose("calm", 1)
			return true
		"cat_down":  # 폴짝: off the ridge on an arc down to the barn's foot
			var c2 := stage.actor("cat")
			if c2:
				_hops.append({"role": "cat", "t": 0.0, "life": 0.9, "from": c2.global_position,
					"to": _spot("barn_foot"), "h0": c2.lift, "arc": 0.18})
			return true
		"glare":  # nose to nose: the puppy turns round to the cat
			var dg := stage.actor("dog")
			var ct := stage.actor("cat")
			if dg:
				_lean["dog"] = [0.0, 0.0]
				dg.set_pose("growl", 0)
			if ct:
				ct.set_pose("glare", 1)
			return true
		"sit_all":  # 털썩: everyone sits down where they stand
			for i in mini(int(p[1]), LINE.size()):
				var a4 := stage.actor(LINE[i])
				if a4:
					_lean[LINE[i]] = [0.0, 0.0]
					a4.set_pose("sit_tired")
					a4.hop_v = 0.3
			return true
		"mouse_out":
			var m := stage.actor("mouse")
			if m:
				m.place_at(_spot("hole_out"))
				m.pop_delay = 0.0
				m.pop_target = 1.0
				m.set_pose("calm", 1)
				m.hop_v = 0.6
			return true
		"stand_all":  # 벌떡: up again, each holding the one ahead
			for i in mini(int(p[1]), LINE.size()):
				var a5 := stage.actor(LINE[i])
				if a5:
					a5.set_pose("pull", 1)
					a5.hop_v = 0.5
			return true
		"turnip_out":  # 쑥! the turnip flies out and lands on its side; everyone tumbles back
			if _cards.has("turnip"):
				var t: Node3D = _cards["turnip"]
				t.set_meta("moving", true)
				_out = {"t": 0.0, "from": t.global_position, "node": t}
			for k in 8:
				var c6 := _turnip_base() + Vector3.UP * 0.03
				fly(CLODS, c6, c6 + Vector3(randf_range(-0.35, 0.35), 0.0, randf_range(-0.05, 0.15)), 0.04, 0.6 + 0.05 * k, 0.3)
			for i in LINE.size():
				var a6 := stage.actor(LINE[i])
				if a6 and a6.pop_target > 0.5:
					_lean[LINE[i]] = [0.0, 0.0]
					a6.set_pose("tumble", 1)
					a6.hop_v = 0.9
					# thrown back a little (a short slide on an arc; walk_to would show a walk cycle)
					_hops.append({"role": LINE[i], "t": 0.0, "life": 0.45, "from": a6.global_position,
						"to": a6.global_position + _right() * (0.05 + 0.012 * i), "h0": 0.0, "arc": 0.04})
			stage.shake(1.2)
			return true
		"cheer_all":
			for r in LINE:
				var a7 := stage.actor(r)
				if a7:
					a7.set_pose("cheer" if r in ["grandpa", "grandma", "girl"] else "happy")
					a7.hop_v = 0.7
			return true
		"to_table":  # everyone turns to walk to the table (the line breaks up)
			for r in LINE:
				_lean[r] = [0.0, 0.0]
			return true
		"carry":  # v2: the pulled turnip goes with them to the table (it does not stay lying in the garden)
			if _cards.has("turnip") and _turnip_state == "out":
				var tn2: Node3D = _cards["turnip"]
				tn2.set_meta("moving", true)
				_carry = {"t": 0.0, "from": tn2.global_position, "node": tn2}
			return true
		"cook":  # the pot, the bread and the chopping board on the table
			if _cards.has("turnip"):  # 썰고 끓이고: the turnip folds down into the cooking (v4: no sparkle puff beside the table)
				var tn3: Node3D = _cards["turnip"]
				_cards.erase("turnip")
				stage.unregister_prop("turnip")
				_carry = {}
				_pop(tn3, false, true)
			var tb := stage.set_piece("table")
			if tb:
				var top := tb.global_position + Vector3.UP * tb.height * 0.93 + _toward() * 0.015
				var pot := _card(POT, 0.12)
				pot.global_position = top
				_pop(pot)
				_cards["pot"] = pot
				var br := _card(BREAD, 0.06)
				br.global_position = top + _right() * 0.15
				_pop(br)
				_cards["bread"] = br
				var bd := _card(BOARD, 0.09)
				bd.global_position = top - _right() * 0.16
				_pop(bd)
				_cards["board"] = bd
			var g6 := stage.actor("grandpa")
			if g6:
				g6.set_pose("clap")
			return true
		"boil":
			_steam_t = 0.0
			return true
		"bowls":  # bowls:<k>: three bowls fly from the pot, one each; they eat
			var k2 := int(p[1])
			var pairs := [["grandpa", "grandma", "girl"], ["dog", "cat", "mouse"]]
			if _cards.has("pot") and k2 < pairs.size():
				var from: Vector3 = (_cards["pot"] as Node3D).global_position + Vector3.UP * 0.1
				for r in pairs[k2]:
					var a8 := stage.actor(str(r))
					if a8:
						fly(BOWL, from, a8.centre(), 0.045, 0.6, 0.2)
						get_tree().create_timer(0.62).timeout.connect(a8.set_pose.bind("eat", -1))
			return true
	return false


func step(dt: float) -> void:
	_t += dt
	# the line's lean: a spring per actor, the pop node turned in the screen plane about the feet
	var ax := _toward()
	for r in _lean.keys():
		var L: Array = _lean[r]
		var ang := float(L[0])
		var v := float(L[1])
		var w := TAU * 1.6
		v += (-w * w * ang - 2.0 * 0.45 * w * v) * dt
		ang += v * dt
		L[0] = ang
		L[1] = v
		var a := stage.actor(str(r))
		if a and a._root:
			a._root.quaternion = Quaternion(ax, -ang)
	# the turnip: wobble and its rise
	_wob_v += (-(TAU * 2.2) * (TAU * 2.2) * _wob - 2.0 * 0.3 * TAU * 2.2 * _wob_v) * dt
	_wob += _wob_v * dt
	if _cards.has("turnip") and _out.is_empty() and _turnip_state != "out":
		var tn: Node3D = _cards["turnip"]
		if is_instance_valid(tn):
			var base := _turnip_base()
			if _turnip_state == "big":
				var y := base.y + _rise - SINK0
				tn.global_position = Vector3(base.x, lerpf(tn.global_position.y, y, minf(1.0, dt * 6.0)), base.z)
			tn.global_transform.basis = Basis(ax, _wob * 0.05) * Basis(Vector3.UP, _view_yaw()) * Basis.from_scale(tn.scale)
	# the turnip flies out (쑥!) and lands on its side to the left
	if not _out.is_empty():
		var o: Node3D = _out["node"]
		_out["t"] = float(_out["t"]) + dt / 1.1
		var k := clampf(float(_out["t"]), 0.0, 1.0)
		var land := _spot("turnip_land") + Vector3.UP * 0.15 + _right() * 0.32
		var from: Vector3 = _out["from"]
		if is_instance_valid(o):
			o.global_position = from.lerp(land, k) + Vector3.UP * sin(k * PI) * 0.35
			o.global_transform.basis = Basis(ax, deg_to_rad(80.0) * k) * Basis(Vector3.UP, _view_yaw())
		if k >= 1.0:
			_out = {}
			_turnip_state = "out"
			if is_instance_valid(o):
				o.remove_meta("moving")
			stage.register_prop("turnip", o, 0.2, 0.3)
			stage.shake(0.6)
			_sfx("wolf.flop", land)
	# v2: the turnip carried to beside the table (rolled in small bumps, set down lying)
	if not _carry.is_empty():
		var cn: Node3D = _carry["node"]
		_carry["t"] = float(_carry["t"]) + dt / 2.2
		var kc := clampf(float(_carry["t"]), 0.0, 1.0)
		var ke := kc * kc * (3.0 - 2.0 * kc)
		var to := _spot("turnip_rest") + Vector3.UP * 0.15 + _right() * 0.32
		if is_instance_valid(cn):
			# rolled along the ground in little bumps (floating high it filled the lens at the walk to the table)
			cn.global_position = (_carry["from"] as Vector3).lerp(to, ke) + Vector3.UP * absf(sin(kc * PI * 4.0)) * 0.025
		if kc >= 1.0:
			_carry = {}
			if is_instance_valid(cn):
				cn.remove_meta("moving")
				stage.register_prop("turnip", cn, 0.2, 0.3)
	# the cat's hop off the ridge
	for h: Dictionary in _hops.duplicate():
		var a9 := stage.actor(str(h["role"]))
		h["t"] = float(h["t"]) + dt / float(h["life"])
		var k9 := clampf(float(h["t"]), 0.0, 1.0)
		if a9:
			# eased along the ground (v5 gate SPEED_JUMP: a linear slide started and stopped at full speed in one frame)
			a9.place_at((h["from"] as Vector3).lerp(h["to"], k9 * k9 * (3.0 - 2.0 * k9)))
			a9.lift = lerpf(float(h["h0"]), 0.0, k9 * k9) + sin(k9 * PI) * float(h["arc"])
		if k9 >= 1.0:
			_hops.erase(h)
			if a9:
				a9.lift = 0.0
				a9.hop_v = 0.4
	# pop-ups / fold-downs of the tale's cards
	for g: Dictionary in _grow.duplicate():
		var n: Node3D = g["node"]
		if not is_instance_valid(n):
			_grow.erase(g)
			continue
		g["t"] = float(g["t"]) + dt
		var tt := float(g["t"])
		var sy := 1.0
		if g["up"]:
			sy = 1.0 + 0.12 * sin(tt * TAU * 5.0) * exp(-tt * 4.0) if tt > 0.25 else lerpf(0.02, 1.1, tt / 0.25)
		else:
			sy = maxf(0.02, 1.0 - tt / 0.5)
		n.scale = Vector3(1, sy, 1)
		if (g["up"] and tt > 1.0) or (not g["up"] and tt > 0.5):
			_grow.erase(g)
			if not g["up"] and g["free"]:
				n.queue_free()
			elif g["up"]:
				n.scale = Vector3.ONE
	# steam over the pot: the only steam in the tale, small, rising straight from the pot's mouth (v4: 0.07 -> 0.045
	# tall, rises 0.12 instead of 0.22, from the rim, not above the lid)
	if _steam_t >= 0.0 and _cards.has("pot") and is_instance_valid(_cards["pot"]):
		_steam_t += dt
		if fmod(_steam_t, 1.1) < dt:
			var pp: Vector3 = (_cards["pot"] as Node3D).global_position + Vector3.UP * 0.075
			fly(STEAM, pp, pp + Vector3.UP * 0.12, 0.045, 1.5, 0.0)
	for f: Dictionary in _flyers.duplicate():
		var fn: Node3D = f["node"]
		if not is_instance_valid(fn):
			_flyers.erase(f)
			continue
		f["age"] = float(f["age"]) + dt
		var kf := clampf(float(f["age"]) / float(f["life"]), 0.0, 1.0)
		fn.global_position = (f["from"] as Vector3).lerp(f["to"], kf) + Vector3.UP * sin(kf * PI) * float(f["arc"])
		if kf >= 1.0:
			_flyers.erase(f)
			if not f.get("keep", false):
				fn.queue_free()
