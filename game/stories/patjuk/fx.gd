extends TaleHandler
## 「팥죽할멈과 호랑이」 effects (TaleHandler, 2026-11-23).
## The stage builds the bean field / the cottage spread and the cast from script.json; this handler adds:
##  - the tiger hidden behind the boulder until he steps out (enter.hidden), the hoe taps, the dropped hoe, the
##    granny's trembling, falling snow outside, steam over the cauldron;
##  - the helpers: arriving at the kitchen door (or the yard gate), a bowl of porridge each (flies from the cauldron),
##    hiding in their places (the chestnut in the fire, the turtle in the jar, the dung flat on the floor, the awl in
##    the crack, the mortar up on the lintel, the mat rolled in the yard, the carrier at the wall);
##  - the traps, one tap each (slapstick, nothing violent): the chestnut pops into his eye, the turtle nips his lip at
##    the jar, he backs onto the dung and slips, the awl pokes his bottom, the mortar drops on his head; in the yard the
##    mat rolls him up, the carrier lifts him and walks him off; far out at sea a splash and a small swimming head;
##  - the feast in the yard.
## Glides that keep a fixed figure (back-step, the carried roll) move the actor here, not by walking (a walk picks the
## figure from the travel direction).

const BOWL := "story_pj_kitchen_07"
const HOE := "story_pj_field_04"
const WEEDS := "story_pj_field_07"
const STEAM := ["story_hearth_06", "story_hearth_07"]
const BURST := "story_hearth_18"
const SPLASH := "story_pj_yard_04"
const SOBAN := "story_pj_kitchen_09"
const FLAKE := "story_pj_yard_09"
const HELP := ["bam", "jara", "ddong", "songgot", "jeolgu", "myeongseok", "jige"]
const YARD := ["myeongseok", "jige"]
## where each helper hides (spot) and what it does there
const HIDE := {"bam": "fire", "jara": "muldok", "ddong": "dung", "songgot": "crack", "jeolgu": "lintel",
	"myeongseok": "y_mat", "jige": "y_jige"}

var _tex := {}
var _flyers: Array = []
var _cards: Dictionary = {}
var _glides: Array = []  ## {a, from, to, t, dur, arc}
var _t := 0.0
var _shiver := 0.0
var _snow: Array = []  ## Sprite3D flakes
var _snow_on := false
var _steam_t := -1.0
var _carry := false  ## the rolled tiger rides on the carrier
var _swim: Node3D = null
var _swim_t := 0.0


func setup() -> void:
	pass


func enter_beat(b: Dictionary) -> void:
	var hid: Dictionary = (b.get("enter", {}) as Dictionary).get("hidden", {})
	for r in hid:
		var a := stage.actor(str(r))
		if a:
			a.place_at(stage.spot_point(hid[r]) - _toward() * 0.25)
			a.pop_target = 0.02


func build_async() -> void:
	enter_beat(stage.beat)


# ------------------------------------------------------------------ helpers

func _a(r: String) -> StoryActor:
	return stage.actor(r)


func _texid(id: String) -> Texture2D:
	if not _tex.has(id):
		var e := SpreadStage.atlas_entry(id)
		if e.is_empty():
			var p := "res://art/cast/%s.webp" % id
			_tex[id] = load(p) if ResourceLoader.exists(p) else null
		else:
			_tex[id] = load("res://" + str(e.get("path", "")))
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


func _view_yaw() -> float:
	var t := stage.dir_vec("toward")
	return atan2(t.x, t.z)


## Face a card toward the current camera (inside the kitchen the room is turned; the view yaw would show its edge).
func _face_cam(n: Node3D) -> void:
	var cam := stage.camera()
	if cam:
		var d := cam.global_position - n.global_position
		n.rotation.y = atan2(d.x, d.z)


func _toward() -> Vector3:
	return stage.dir_vec("toward")


func _right() -> Vector3:
	return stage.dir_vec("right")


func _sfx(id: String, at: Variant = null) -> void:
	if SoundDirector.current:
		SoundDirector.current.play(id, at)


func _ground(p: Vector3) -> Vector3:
	var g := stage.world.ground if stage.world else null
	if g:
		p.y = g.surface_y(Vector2(p.x, p.z))
	return p


func fly(id: String, from: Vector3, to: Vector3, h: float, life := 0.7, arc := 0.18, keep := false) -> Node3D:
	var n := _card(id, h)
	_face_cam(n)
	n.global_position = from
	_flyers.append({"node": n, "age": 0.0, "life": life, "from": from, "to": to, "arc": arc, "keep": keep})
	return n


## Move an actor along a straight / arced line keeping its current figure (no walk-cycle view picking).
func glide(a: StoryActor, to: Vector3, dur: float, arc := 0.0, lift_to := -1.0) -> void:
	if a == null:
		return
	if not stage.no_spacing.has(a.role):
		stage.no_spacing.append(a.role)
	_glides = _glides.filter(func(g): return g["a"] != a)
	_glides.append({"a": a, "from": a.global_position, "to": to, "t": 0.0, "dur": maxf(dur, 0.05), "arc": arc,
		"l0": a.lift, "l1": a.lift if lift_to < 0.0 else lift_to})


func _helper_point(h: String) -> Vector3:
	return stage.spot_point(HIDE[h])


# ------------------------------------------------------------------ tap targets

func targets() -> Array:
	return ["cauldron"]


func target_point(t: String) -> Variant:
	if t == "cauldron" and stage.spots.has("cauldron"):
		return stage.spot_point("cauldron") + Vector3.UP * 0.2
	return null


func target_radius(t: String) -> float:
	return 90.0 if target_point(t) != null else -1.0


func wiggle(t: String) -> bool:
	return t == "cauldron"


# ------------------------------------------------------------------ fx

func fx(name: String) -> bool:
	var p := name.split(":")
	var halmi := _a("halmi")
	var tig := _a("tiger")
	match p[0]:
		"knock":
			_sfx("wg.knock", stage.spot_point("door") if stage.spots.has("door") else null)
			return true
		"tiger_out":  # tiger_out:<hide spot>:<mark>
			if tig:
				tig.place_at(stage.spot_point(p[1]) - _toward() * 0.25)
				tig.pop_target = 1.0
				tig.set_pose("roar")
				tig.walk_to(stage.spot_point(p[2]), 0.45)
			return true
		"hoe":  # hoe:<k>: one stroke, a tuft of weeds hops out
			if halmi:
				halmi.set_pose("hoe_down")
				get_tree().create_timer(0.35).timeout.connect(func():
					if is_instance_valid(halmi):
						halmi.set_pose("hoe_up"))
				var at := halmi.global_position + _right() * (0.12 + 0.03 * float(p[1])) + _toward() * 0.06
				var w := fly(WEEDS, at, at + _right() * 0.1 + _toward() * 0.02, 0.06, 0.45, 0.12, true)
				_cards["weeds%s" % p[1]] = w
			return true
		"hoe_drop":
			if halmi:
				halmi.set_pose("scared")
				var from := halmi.centre() + _right() * 0.08
				var to := _ground(halmi.global_position + _right() * 0.16 + _toward() * 0.1)
				var h := fly(HOE, from, to + Vector3.UP * 0.01, 0.035, 0.4, 0.05, true)
				stage.register_prop("hoe", h, 0.03, 0.03)
			return true
		"shiver":
			_shiver = float(p[1]) if p.size() > 1 else 2.0
			return true
		"snow":
			_snow_on = p.size() < 2 or p[1] == "on"
			if _snow_on and _snow.is_empty():
				_make_snow()
			return true
		"steam":
			_steam_t = 0.0 if (p.size() < 2 or p[1] == "on") else -1.0
			return true
		"door":
			var sp := stage.set_piece("cottage")
			if sp and sp.has_door():
				sp.open_door(p[1] == "open")
				_sfx("door.open" if p[1] == "open" else "door.shut", sp.global_position)
			return true
		"arrive":  # arrive:<helper>: in at the kitchen door (or the yard gate), a hop-walk to the granny
			var h := _a(p[1])
			if h:
				var yard := p[1] in YARD
				h.place_at(stage.spot_point("y_help_in" if yard else "door_out"))
				h.pop_delay = 0.0
				h.pop_target = 1.0
				h.set_pose("calm")
				var goal := stage.spot_point("yard_c" if yard else "help_in")
				if yard:
					h.walk_to(goal, 0.32)
				else:
					h.follow([stage.spot_point("door"), goal], 0.5, "", false)
			return true
		"give":  # give:<helper>: a bowl of porridge flies from the cauldron to the helper
			var h2 := _a(p[1])
			if h2:
				var src := stage.spot_point("cauldron") + Vector3.UP * 0.2 if stage.spots.has("cauldron") else halmi.centre()
				if p[1] in YARD and halmi:
					src = halmi.centre()
				if halmi:
					halmi.set_pose("offer")
				var b := fly(BOWL, src, h2.centre() + Vector3.UP * 0.04, 0.08, 0.7, 0.18)
				b.set_meta("moving", true)
				get_tree().create_timer(0.65).timeout.connect(func():
					if is_instance_valid(h2):
						h2.hop_v = 0.8
						_sfx("sm.gulp", h2.centre()))
			return true
		"hide":  # hide:<helper>
			_hide(p[1])
			if halmi:
				halmi.set_pose("calm")
			return true
		"tiger_crouch":
			if tig:
				tig.set_pose("sit_fire", 1)
			return true
		"trap":
			_trap(p[1])
			return true
		"tiger_dip":
			if tig:
				tig.set_pose("peer_well", 0)
			return true
		"backstep":
			if tig:
				tig.set_pose("backstep", 0)
				glide(tig, stage.spot_point("dung") + _right() * 0.0, 1.0)
			return true
		"tiger_flat":
			if tig:
				tig.set_pose("flat_bump", 1)
				_burst(tig.centre(), 4)
			return true
		"roll":  # roll:<k>: the mat unrolls toward the tiger, then rolls him up
			_roll(int(p[1]))
			return true
		"jige_lift":
			var j := _a("jige")
			if j and tig:
				j.set_pose("act")
				j.walk_to(tig.global_position + _right() * 0.02 - _toward() * 0.03, 0.4)
				get_tree().create_timer(0.9).timeout.connect(func():
					tig.set_pose("rolled_cry", 1)
					_carry = true
					_sfx("prop.ladder_raise", tig.centre()))
			return true
		"jige_carry":  # the carrier walks off along the path to the road with the roll on its back
			var j2 := _a("jige")
			if j2:
				j2.follow([stage.spot_point("y_out"), stage.spot_point("shore")], 0.42, "", false)
			return true
		"splash":
			var at2 := stage.spot_point("sea_splash")
			var s := _card(SPLASH, 0.1)
			_face_cam(s)
			s.global_position = at2
			var tw := create_tween()
			tw.tween_property(s, "scale", Vector3.ONE * 9.0, 0.45).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
			tw.tween_interval(1.3)
			tw.tween_property(s, "scale", Vector3.ONE * 0.05, 0.5)
			tw.tween_callback(s.queue_free)
			var tg := _a("tiger")
			if tg:
				tg.pop_target = 0.02  # thrown: off the carrier's back into the waves
			_carry = false
			return true
		"swim":
			_swim = _card("cast_tiger_swim", 0.3)
			_face_cam(_swim)
			_swim.global_position = stage.spot_point("sea_splash") + Vector3.UP * 0.06
			_swim_t = 0.0
			return true
		"feast":
			_feast()
			return true
		"hop_all":
			for h3 in HELP:
				var a3 := _a(h3)
				if a3 and a3.pop_target > 0.5:
					a3.hop_v = 0.9
			if halmi:
				halmi.hop_v = 0.7
			return true
	return false


func _hide(h: String) -> void:
	var a := _a(h)
	if a == null:
		return
	var goal := _helper_point(h)
	match h:
		"bam":  # rolls to the hearth and into the fire mouth
			a.follow([stage.spot_point("bam_k"), goal], 0.3, "", false)
			get_tree().create_timer(1.6).timeout.connect(func(): a.pop_target = 0.02)
		"jara":  # crawls to the jar and plops in
			a.follow([stage.spot_point("jara_k")], 0.25, "", false)
			get_tree().create_timer(1.4).timeout.connect(func():
				glide(a, goal + Vector3.UP * 0.0, 0.5, 0.18)
				get_tree().create_timer(0.45).timeout.connect(func():
					a.pop_target = 0.02
					_sfx("kitchen.splash", goal)))
		"ddong":  # flops down flat on the floor
			a.walk_to(goal, 0.25)
			get_tree().create_timer(1.0).timeout.connect(func(): a.set_pose("act"))
		"songgot":  # into the crack between the boards
			a.walk_to(goal, 0.25)
			get_tree().create_timer(1.1).timeout.connect(func():
				a.pop_target = 0.02
				_sfx("sm.paper_poke", goal))
		"jeolgu":  # hops up onto the lintel above the door
			var up := stage.spot_point("lintel")
			a.follow([up], 0.3, "", false)
			get_tree().create_timer(0.9).timeout.connect(func(): glide(a, up, 0.5, 0.0, _lintel_h()))
		"myeongseok", "jige":
			a.walk_to(goal, 0.3)
	_sfx("wc.plop", goal)


func _lintel_h() -> float:
	var sp := stage.set_piece("cottage")
	return (sp.height * 0.48) if sp else 0.4


func _burst(at: Vector3, n := 5) -> void:
	for k in n:
		var b := fly(BURST, at, at + Vector3(randf_range(-0.12, 0.12), randf_range(0.04, 0.16), 0.0), 0.05, 0.5, 0.04)
		b.set_meta("moving", true)


func _trap(h: String) -> void:
	var tig := _a("tiger")
	var a := _a(h)
	if tig == null or a == null:
		return
	match h:
		"bam":  # out of the fire into his eye
			a.place_at(_helper_point("bam"))
			a.pop_delay = 0.0
			a.pop_target = 1.0
			a.set_pose("act")
			var eye := tig.global_position + Vector3.UP * tig.puppet.height * 0.55
			glide(a, eye, 0.35, 0.12)
			get_tree().create_timer(0.35).timeout.connect(func():
				tig.set_pose("eye_hurt")
				tig.hop_v = 0.8
				_burst(tig.centre() + Vector3.UP * 0.12, 4)
				glide(a, stage.spot_point("bam_k"), 0.5, 0.1, 0.0)
				get_tree().create_timer(0.5).timeout.connect(func(): a.set_pose("calm")))
			_sfx("wc.boing", a.centre())
		"jara":  # up out of the jar and onto his lip
			var rim := stage.spot_point("jara_rim") if stage.spots.has("jara_rim") else _helper_point("jara")
			a.place_at(rim)
			a.pop_delay = 0.0
			a.pop_target = 1.0
			a.set_pose("act", 1)
			a.lift = 0.12
			var mouth := tig.global_position + _right() * 0.06 + _toward() * 0.03
			glide(a, mouth, 0.3, 0.05, tig.puppet.height * 0.5)
			get_tree().create_timer(0.3).timeout.connect(func():
				tig.set_pose("mouth_ouch")
				tig.hop_v = 1.0
				_sfx("wc.bonk", tig.centre()))
			get_tree().create_timer(1.6).timeout.connect(func():
				glide(a, stage.spot_point("jara_k"), 0.5, 0.06, 0.0)
				a.set_pose("calm"))
		"ddong":  # his heel lands on it: whoosh, feet up, flat on his back
			tig.set_pose("slip_fall", 0)
			_sfx("sm.slide", tig.centre())
			glide(tig, tig.global_position - _right() * 0.1, 0.6, 0.12)
			get_tree().create_timer(0.6).timeout.connect(func():
				tig.set_pose("fallen", 1)
				_sfx("wolf.flop", tig.centre())
				_burst(tig.centre(), 3))
			a.hop_v = 0.6
		"songgot":  # up out of the crack under his bottom
			a.place_at(_helper_point("songgot"))
			a.pop_delay = 0.0
			a.pop_target = 1.0
			a.set_pose("act")
			get_tree().create_timer(0.2).timeout.connect(func():
				tig.set_pose("poked", 0)
				glide(tig, stage.spot_point("tiger_jar").lerp(stage.spot_point("dung"), 0.3), 0.6, 0.22)
				_sfx("sm.paper_poke", tig.centre())
				_burst(tig.global_position + Vector3.UP * 0.1, 3))
		"jeolgu":  # off the lintel onto his head
			var head := tig.global_position + Vector3.UP * 0.02
			glide(a, head + _right() * 0.08, 0.35, 0.0, tig.puppet.height * 0.85)
			a.set_pose("act")
			get_tree().create_timer(0.35).timeout.connect(func():
				tig.set_pose("dazed")
				_sfx("wc.bonk", tig.centre())
				_burst(tig.centre() + Vector3.UP * 0.2, 5)
				glide(a, stage.spot_point("jeolgu_land") if stage.spots.has("jeolgu_land") else stage.spot_point("help_in"), 0.45, 0.1, 0.0)
				get_tree().create_timer(0.45).timeout.connect(func(): a.set_pose("calm")))


func _roll(k: int) -> void:
	var m := _a("myeongseok")
	var tig := _a("tiger")
	if m == null or tig == null:
		return
	m.set_pose("act")
	m.hop_v = 0.7
	if k < 3:
		var goal := m.global_position.lerp(tig.global_position, 0.45 if k == 1 else 0.7)
		glide(m, goal, 0.4, 0.04)
		_sfx("wc.flap", m.centre())
	else:
		glide(m, tig.global_position, 0.3)
		get_tree().create_timer(0.3).timeout.connect(func():
			m.pop_target = 0.02
			tig.set_pose("rolled", 1)
			tig.hop_v = 0.7
			_sfx("wc.roll", tig.centre()))


func _feast() -> void:
	var c := stage.spot_point("y_feast")
	var t := _card(SOBAN, 0.12)
	t.global_position = c
	stage.register_prop("soban", t, 0.09, 0.08)
	var ring := {"bam": [-0.26, 0.12], "jara": [0.26, 0.12], "ddong": [-0.3, -0.06], "songgot": [0.3, -0.08],
		"jeolgu": [-0.16, -0.24], "myeongseok": [0.18, -0.26], "jige": [0.52, -0.2]}
	for h in HELP:
		var a := _a(h)
		if a == null:
			continue
		var o: Array = ring[h]
		a.lift = 0.0
		a.place_at(_ground(c + _right() * float(o[0]) + _toward() * float(o[1])))
		a.pop_delay = 0.1 * HELP.find(h)
		a.pop_target = 1.0
		a.set_pose("calm")
	_sfx("wc.chime", c)


func _make_snow() -> void:
	var tex := _texid(FLAKE)
	for k in 70:
		var s := Sprite3D.new()
		s.texture = tex
		s.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		s.pixel_size = 0.022 / maxf(1.0, float(tex.get_width()) if tex else 1.0) * randf_range(0.6, 1.3)
		s.shaded = false
		s.top_level = true
		s.set_meta("seed", Vector3(randf_range(-1, 1), randf(), randf_range(-1, 1)))
		stage.add_child(s)
		_snow.append(s)


func _step_snow(dt: float) -> void:
	var cam := stage.camera()
	if cam == null:
		return
	var inside := stage.camera_inside != ""
	var c := cam.global_position - cam.global_transform.basis.z * 1.1
	for s: Sprite3D in _snow:
		s.visible = _snow_on and not inside
		if not s.visible:
			continue
		var sd: Vector3 = s.get_meta("seed")
		var fall := fmod(sd.y + _t * 0.08 * (0.7 + 0.5 * absf(sd.x)), 1.0)
		var p := c + cam.global_transform.basis.x * (sd.x * 0.9 + sin(_t * 0.9 + sd.z * 6.0) * 0.04) \
			+ Vector3.UP * (0.6 - fall * 1.2) - cam.global_transform.basis.z * sd.z * 0.5
		s.global_position = p


func run_step(_st: Dictionary, _R: Node) -> void:
	pass


func step(dt: float) -> void:
	_t += dt
	if not _snow.is_empty():
		_step_snow(dt)
	var halmi := _a("halmi")
	if _shiver > 0.0 and halmi:
		_shiver -= dt
		halmi.puppet.rotation.z = sin(_t * 38.0) * 0.025 if _shiver > 0.0 else 0.0
	if _steam_t >= 0.0 and stage.spots.has("cauldron"):
		_steam_t += dt
		if _steam_t > 0.9:
			_steam_t = 0.0
			var at := stage.spot_point("cauldron") + Vector3.UP * 0.2
			var st := fly(STEAM[randi() % 2], at, at + Vector3.UP * 0.25 + _right() * randf_range(-0.05, 0.05), 0.05, 1.8, 0.0)
			st.set_meta("moving", true)
	for g: Dictionary in _glides.duplicate():
		var a: StoryActor = g["a"]
		if not is_instance_valid(a):
			_glides.erase(g)
			continue
		g["t"] = float(g["t"]) + dt
		var k := clampf(float(g["t"]) / float(g["dur"]), 0.0, 1.0)
		var e := k * k * (3.0 - 2.0 * k)
		var p: Vector3 = (g["from"] as Vector3).lerp(g["to"], e)
		a.place_at(_ground(p))
		a.lift = lerpf(float(g["l0"]), float(g["l1"]), e) + sin(k * PI) * float(g["arc"])
		if k >= 1.0:
			_glides.erase(g)
	if _carry:
		var j := _a("jige")
		var tig := _a("tiger")
		if j and tig:
			tig.place_at(j.global_position - _toward() * 0.02)
			tig.lift = j.puppet.height * 0.45
	if _swim and is_instance_valid(_swim):
		_swim_t += dt
		var cam2 := stage.camera()
		var away := -_toward()
		if cam2:
			away = cam2.global_transform.basis.x  # along the wave band (sideways), staying in front of it
			away.y = 0.0
			away = away.normalized()
		_face_cam(_swim)
		_swim.global_position = stage.spot_point("sea_splash") + away * _swim_t * 0.16 \
			+ Vector3.UP * (0.06 + sin(_swim_t * 5.0) * 0.012)
		_swim.scale = Vector3.ONE * maxf(0.25, 1.0 - _swim_t * 0.08)
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
