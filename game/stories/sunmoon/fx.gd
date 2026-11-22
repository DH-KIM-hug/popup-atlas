extends TaleHandler
## 「해님 달님」 effects (TaleHandler, phase 2 first pass, 2026-11-22).
## The stage builds the mountain road / the cottage spread and the cast from script.json; this handler adds:
##  - tap targets that are not actors or set pieces: the rice-cake tray, the paper window, the oil bottle, the rope;
##  - the tiger hidden behind his rock until he steps out (enter.hidden), rice cakes flying (basket / tiger's mouth),
##    the belly growing, the moon going behind a cloud, the mother simply gone (the source's soft line, nothing shown);
##  - the door (bolt, paw, poked window), hiding behind the jars, the climbs on drawn frames (hands on the trunk,
##    feet on the rope), the oil streak and slips, the axe climb with notches, the golden rope and the old rope (snap),
##    the fall into the sorghum, the sun / moon faces and their swap.
## Lines play through the runner, so captions, faces (line expr) and SEG logs stay generic.

const CAKE := "story_sm_village_08"
const ROPE_GOOD := "story_sm_sky_03"
const ROPE_OLD := "story_sm_sky_04"
const ROPE_END := "story_sm_sky_08"
const CLOUD := "story_sm_sky_00"
const OIL := "story_sm_yard_04"
const OIL_STREAK := "story_sm_tree_03"
const NOTCHES := "story_sm_tree_04"
const WINDOW_HOLE := "story_sm_cottage_03"
const STAR := "story_sm_sky_09"
const FORK_H := 1.12  ## the zelkova's fork above its base (1.7-unit card: the fork at ~66 %)

var _tex := {}
var _flyers: Array = []
var _cards: Dictionary = {}  ## name -> Node3D (rope, oil bottle, streak, window hole, eyes)
var _hidden: Dictionary = {}  ## role -> spot
var _rope_drop := {}  ## name -> {node, y0, y1, t}
var _t := 0.0


func setup() -> void:
	_sky_faces("sun_boy", "moon_girl")
	_sky_shown()


## The sun and the moon hang only in the sky ending (v1: they hung over the cottage from the first page).
func _sky_shown() -> void:
	var on := str(stage.beat.get("id", "")) == "sky"
	for r in ["sun", "moon"]:
		var h := stage.hanger(r)
		if h and h.get_parent():
			(h.get_parent() as Node3D).visible = on


func enter_beat(b: Dictionary) -> void:
	var hid: Dictionary = (b.get("enter", {}) as Dictionary).get("hidden", {})
	for r in hid:
		_hidden[r] = hid[r]
		var a := stage.actor(str(r))
		if a:
			a.place_at(stage.spot_point(hid[r]) - _toward() * 0.25)
			a.pop_target = 0.02  # folded flat behind the rock until he steps out


func build_async() -> void:
	enter_beat(stage.beat)
	_sky_shown()


# ------------------------------------------------------------------ helpers

func _texid(id: String) -> Texture2D:
	if not _tex.has(id):
		var e := SpreadStage.atlas_entry(id)
		if e.is_empty():  # cast cards (sun / moon faces)
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
	node.rotation.y = deg_to_rad(stage.world.rig.yaw_deg)
	return node


func _toward() -> Vector3:
	return stage.dir_vec("toward")


func _right() -> Vector3:
	return stage.dir_vec("right")


func _sfx(id: String, at: Variant = null) -> void:
	if SoundDirector.current:
		SoundDirector.current.play(id, at)


func _sky_faces(sun: String, moon: String) -> void:
	for pair in [["sun", sun], ["moon", moon]]:
		var h := stage.hanger(pair[0])
		var t := _texid("cast_sunmoon_sky_" + str(pair[1]))
		if h and t:
			h.set_texture(t)


func fly(id: String, from: Vector3, to: Vector3, h: float, life := 0.7, arc := 0.18) -> Node3D:
	var n := _card(id, h)
	n.global_position = from
	_flyers.append({"node": n, "age": 0.0, "life": life, "from": from, "to": to, "arc": arc})
	return n


func _tree_base() -> Vector3:
	var sp := stage.set_piece("tree")
	return sp.global_position if sp else stage.spot_point("tree")


## A point on the trunk's face toward the camera, k = 0 (roots) .. 1 (fork).
func _trunk(k: float, side := 0.0) -> Vector3:
	return _tree_base() + Vector3.UP * FORK_H * k + _toward() * 0.06 + _right() * side


# ------------------------------------------------------------------ tap targets

func targets() -> Array:
	var out := ["tray", "window"]
	for k in ["oil", "rope"]:
		if _cards.has(k):
			out.append(k)
	return out


func target_point(t: String) -> Variant:
	match t:
		"tray":
			var r := stage.actor("rich")
			return r.centre() if r and r.pop_target > 0.5 else null
		"window":
			if stage.spots.has("window_inside"):
				return stage.spot_point("window_inside") + Vector3.UP * 0.32
		"oil", "rope":
			if _cards.has(t):
				return (_cards[t] as Node3D).global_position + Vector3.UP * (0.04 if t == "oil" else 1.3)
	return null


func target_radius(t: String) -> float:
	return 90.0 if target_point(t) != null else -1.0


func wiggle(t: String) -> bool:
	return t in ["tray", "window", "oil", "rope"]


# ------------------------------------------------------------------ fx

func fx(name: String) -> bool:
	var p := name.split(":")
	var mom := stage.actor("mom")
	var tig := stage.actor("tiger")
	match p[0]:
		"door_bolt", "bucket_splash":
			return true
		"cake_to_basket":
			var rich := stage.actor("rich")
			if rich and mom:
				fly(CAKE, rich.centre(), mom.centre(), 0.03)
				if int(p[1]) >= 3:
					mom.set_pose("happy_full")
			return true
		"cake_to_tiger", "cakes_all_to_tiger":
			if mom and tig:
				var n := 1 if p[0] == "cake_to_tiger" else 5
				for k in n:
					fly(CAKE, mom.centre() + Vector3.UP * 0.02 * k, tig.centre() + Vector3.UP * 0.12, 0.03, 0.6 + 0.08 * k)
				mom.set_pose("give")
				tig.set_pose("gulp")
			return true
		"tiger_out":  # tiger_out:<hide spot>:<mark>
			if tig:
				tig.place_at(stage.spot_point(p[1]) - _toward() * 0.25)
				tig.pop_target = 1.0
				tig.set_pose("roar")
				tig.walk_to(stage.spot_point(p[2]), 0.45)
				_hidden.erase("tiger")
			return true
		"eyes_glow":  # two warm glints by the rock before he steps out
			var at := stage.spot_point(p[1]) + Vector3.UP * 0.3
			for s in [-1.0, 1.0]:
				var e := _card(STAR, 0.035)
				e.global_position = at + _right() * 0.035 * s
				_cards["eye%d" % int(s)] = e
			return true
		"moon_cloud":
			var c := _card(CLOUD, 0.3)
			c.global_position = stage.spot_point("pass_3") + Vector3.UP * 1.9 - _toward() * 4.0 - _right() * 1.2
			_flyers.append({"node": c, "age": 0.0, "life": 2.5, "from": c.global_position,
				"to": c.global_position + _right() * 1.6, "arc": 0.0, "keep": true})
			for k in _cards.keys():
				if str(k).begins_with("eye"):
					(_cards[k] as Node3D).queue_free()
					_cards.erase(k)
			return true
		"mom_gone":
			if mom:
				mom.pop_target = 0.02
			return true
		"paw_in", "eye_blink":
			return true  # phase 2b: paw / eye cards (art to make)
		"poke_hole":
			var w := _card(WINDOW_HOLE, 0.25)
			w.global_position = stage.spot_point("window_inside") + Vector3.UP * 0.2 - _toward() * 0.001
			w.rotation.y += PI
			_cards["window_hole"] = w
			return true
		"hide_behind":
			for r in ["boy", "girl"]:
				var a := stage.actor(r)
				if a:
					a.walk_to(stage.spot_point("jars_hide") + _right() * (0.07 if r == "boy" else -0.07), 0.5)
					a.set_pose("scared")
			return true
		"climb_tree":  # climb_tree:<1..3>: a stretch up the trunk per tap, the third onto the fork
			var k := int(p[1])
			for r in ["boy", "girl"]:
				var a := stage.actor(r)
				if a == null:
					continue
				var side := 0.07 if r == "boy" else -0.07
				var top := _trunk(1.0, side * 1.4)
				var goal := top if k >= 3 else _trunk(k / 3.0 - (0.08 if r == "girl" else 0.0), side)
				a.follow([goal], 0.35, "", true)
				a.set_pose(("sit_hold" if r == "boy" else "sit_scared") if k >= 3 else ("climb_a" if k % 2 == 1 else "climb_b"))
			return true
		"oil_smear":
			if tig:
				tig.set_pose("smear_oil")
			var s := _card(OIL_STREAK, 0.18)
			s.global_position = _trunk(0.12)
			_cards["streak"] = s
			if _cards.has("oil"):
				(_cards["oil"] as Node3D).queue_free()
				_cards.erase("oil")
			return true
		"tiger_slip":
			if tig:
				tig.set_pose("slip")
				var base := tig.global_position
				tig.follow([base + Vector3.UP * 0.22, base, base + Vector3.UP * 0.18, base], 0.5, "", true)
			return true
		"axe_climb":
			if tig:
				tig.set_pose("axe_a")
				tig.follow([_trunk(0.25, 0.1), _trunk(0.45, 0.1), _trunk(0.62, 0.1)], 0.12, "", true)
				for k in 3:
					var n := _card(NOTCHES, 0.1)
					n.global_position = _trunk(0.2 + 0.18 * k)
			return true
		"rope_down":  # rope_down:good|old — the rope slides down from the sky to the fork
			var id := ROPE_GOOD if p[1] == "good" else ROPE_OLD
			var r := _card(id, 2.0)
			var x := _trunk(1.0, 0.18 if p[1] == "good" else -0.2)
			r.global_position = x + Vector3.UP * 2.6
			_rope_drop[p[1]] = {"node": r, "y0": x.y + 2.6, "y1": x.y - 0.35, "t": 0.0}
			_cards["rope"] = r
			_sfx("wc.chime", x)
			return true
		"rope_climb":  # rope_climb:<1..3>
			var k2 := int(p[1])
			for r2 in ["boy", "girl"]:
				var a2 := stage.actor(r2)
				if a2 and _cards.has("rope"):
					var rp := (_cards["rope"] as Node3D).global_position
					a2.follow([rp + Vector3.UP * (0.55 * k2 + (0.0 if r2 == "boy" else -0.28)) + _toward() * 0.03], 0.4, "", true)
					a2.set_pose("rope_a" if k2 % 2 == 1 else "rope_b")
			return true
		"tiger_rope_climb":
			if tig and _cards.has("rope"):
				var rp2 := (_cards["rope"] as Node3D).global_position
				tig.set_pose("rope_a")
				tig.follow([rp2 + Vector3.UP * 0.5 + _toward() * 0.03, rp2 + Vector3.UP * 0.9 + _toward() * 0.03], 0.25, "", true)
			return true
		"rope_snap":
			if tig:
				tig.set_pose("falling")
				tig.follow([stage.spot_point("sorghum_fall")], 1.4, "", true)
			if _cards.has("rope"):
				(_cards["rope"] as Node3D).queue_free()
				_cards.erase("rope")
			return true
		"swap_sun_moon":
			_sky_faces("sun_girl", "moon_boy")
			return true
		"day", "night":
			stage._set_light("" if p[0] == "day" else "night", false)
			return true
	return false


func run_step(_st: Dictionary, _R: Node) -> void:
	pass


func step(dt: float) -> void:
	_t += dt
	for f: Dictionary in _flyers.duplicate():
		var n: Node3D = f["node"]
		if not is_instance_valid(n):
			_flyers.erase(f)
			continue
		f["age"] = float(f["age"]) + dt
		var k := clampf(float(f["age"]) / float(f["life"]), 0.0, 1.0)
		n.global_position = (f["from"] as Vector3).lerp(f["to"], k) + Vector3.UP * sin(k * PI) * float(f["arc"])
		if k >= 1.0:
			_flyers.erase(f)
			if not f.get("keep", false):
				n.queue_free()
	for key in _rope_drop.keys():
		var d: Dictionary = _rope_drop[key]
		d["t"] = minf(1.0, float(d["t"]) + dt / 2.2)
		var e := 1.0 - pow(1.0 - float(d["t"]), 3.0)
		var rn: Node3D = d["node"]
		if is_instance_valid(rn):
			rn.global_position.y = lerpf(float(d["y0"]), float(d["y1"]), e)
		if float(d["t"]) >= 1.0:
			_rope_drop.erase(key)
	# the oil bottle appears at the trunk's foot when the tiger asks how they got up (the tap after the boy's trick)
	if not _cards.has("oil") and not _cards.has("streak") and str(stage.beat.get("id", "")) == "tree" \
			and stage.spots.has("tree_foot") and _oil_due():
		var o := _card(OIL, 0.07)
		o.global_position = stage.spot_point("tree_foot") + _right() * 0.18
		_cards["oil"] = o


func _oil_due() -> bool:
	var tig := stage.actor("tiger")
	return tig != null and tig.pop_target > 0.5 and tig.pose in ["look_up", "sly"]
