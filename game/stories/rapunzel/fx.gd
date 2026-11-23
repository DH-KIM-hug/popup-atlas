extends TaleHandler
## 「라푼젤」 effects (TaleHandler, 2026-11-23).
## The stage builds the three places from script.json (home: cottage, wall, gate, the witch's rampion garden; forest:
## the building kit's 3D round tower with an open high window, the hiding tree, the field cottage; room: a ring of
## inside-wall cards); this handler adds what only this tale does:
##  - window figures: an actor leaning out of the tower window (upper-body win_* figure, lifted to the sill, just in
##    front of the opening); `enter.rp.window` {role: pose} or fx window:<role>:<pose> (empty pose = gone inside);
##  - THE BRAID: a column of tiled braid cards from the sill to the grass in front of the tower wall (offset along the
##    tower's own front normal, never through the wall), unrolling top to bottom (braid:down / braid:hook) and drawn up
##    bottom to top (braid:up); registered as a prop for the overlap check;
##  - climb_braid (tale verb): the climber walks to the braid's foot and goes up hand over hand (the drawn climb_cycle,
##    story_actor) and disappears into the window (or stops part way: `stop`);
##  - sparkles, the tower rising with a shake, the rampion pulled, the witch appearing / vanishing, music notes drifting
##    out of the window, the snip, the soft magic wind that floats the prince down into the grass, petals.
## Lines play through the runner, so captions, faces (line expr) and SEG logs stay generic.

const SPARKLE := "story_rp_garden_08"
const NOTES := "story_rp_garden_09"
const PETALS := "story_rp_garden_10"
const WIND := "story_rp_garden_13"
const BRAID := "story_rp_garden_05"
const BRAID_END := "story_rp_garden_06"
const PULLED := "story_rp_garden_04"
const SCISSORS := "story_rp_garden_16"
const HOOKED := "story_rp_garden_07"
const SEG_H := 0.24  ## one braid card (about 0.036 wide: reads as a thick braid in the wide shots)
const BRAID_W := 0.022

var _tex := {}
var _cards: Dictionary = {}
var _flyers: Array = []
var _grow: Array = []
var _braid: Array = []  ## braid cards top -> bottom
var _braid_anim := {}  ## {t, dir: 1 down / -1 up, life}
var _float := {}  ## the prince's soft descent {t, life, from, to, h0}
var _t := 0.0
var _win_role := {}  ## role -> pose of who is at the window


func setup() -> void:
	pass


func build_async() -> void:
	enter_beat(stage.beat)


func enter_beat(b: Dictionary) -> void:
	var en: Dictionary = b.get("enter", {})
	var hid: Dictionary = en.get("hidden", {})
	for r in hid:
		var a := stage.actor(str(r))
		if a:
			a.place_at(stage.spot_point(hid[r]))
			a.lift = 0.0
			a.pop_target = 0.02
			a.pop_delay = 0.0
	var rp: Dictionary = en.get("rp", {})
	_win_role.clear()
	var win: Dictionary = rp.get("window", {})
	for r in win:
		at_window(str(r), str(win[r]))
	if str(b.get("id", "")) in ["tower", "hair", "song", "prince", "climb"]:
		pass
	if _braid.size() > 0 and str(b.get("id", "")) in ["song", "prince", "climb", "empty"]:
		_clear_braid()


# ------------------------------------------------------------------ helpers

func _texid(id: String) -> Texture2D:
	if not _tex.has(id):
		var e := SpreadStage.atlas_entry(id)
		_tex[id] = load("res://" + str(e.get("path", ""))) if not e.is_empty() else null
	return _tex[id]


func _card(id: String, h: float, yaw := INF) -> Node3D:
	var node := Node3D.new()
	node.top_level = true
	stage.add_child(node)
	var tex := _texid(id)
	if tex:
		var c := PaperCard.new()
		c.texture = tex
		c.height = h
		c.thickness = clampf(h * 0.03, 0.002, 0.008)
		node.add_child(c)
	node.rotation.y = _view_yaw() if yaw == INF else yaw
	return node


func _view_yaw() -> float:
	var t := stage.dir_vec("toward")
	return atan2(t.x, t.z)


func _toward() -> Vector3:
	return stage.dir_vec("toward")


func _right() -> Vector3:
	return stage.dir_vec("right")


func _spot(nm: String) -> Vector3:
	return stage.spot_point(nm)


func _sfx(id: String, at: Variant = null) -> void:
	if SoundDirector.current:
		SoundDirector.current.play(id, at)


func _pop(n: Node3D, up := true, free_after := false) -> void:
	if up:
		n.scale = Vector3(1, 0.02, 1)
	_grow.append({"node": n, "t": 0.0, "up": up, "free": free_after})


func fly(id: String, from: Vector3, to: Vector3, h: float, life := 0.7, arc := 0.18, keep := false, spin := 0.0) -> Node3D:
	var n := _card(id, h)
	n.global_position = from
	n.set_meta("moving", true)
	_flyers.append({"node": n, "age": 0.0, "life": life, "from": from, "to": to, "arc": arc, "keep": keep, "spin": spin})
	return n


func sparkle(at: Vector3, n := 7, spread := 0.18, h := 0.07) -> void:
	for k in n:
		var to := at + Vector3(randf_range(-spread, spread), randf_range(0.02, spread * 1.4), 0.0) + _toward() * 0.02
		fly(SPARKLE, at, to, h * randf_range(0.6, 1.1), 0.7 + 0.06 * k, 0.05)


# ------------------------------------------------------------------ the tower window

func _tower() -> SetPiece:
	return stage.set_piece("tower")


func _unit() -> float:
	var t := _tower()
	if t and t.building:
		return t.building.unit
	return 0.8


## The tower spec numbers this tale relies on (kit preset rapunzel_tower, opening 0 = the window on the front edge).
func _win_spec() -> Dictionary:
	var t := _tower()
	if t and t.building:
		var parts: Array = t.building.spec.get("parts", [])
		if not parts.is_empty():
			var p: Dictionary = parts[0]
			var op: Dictionary = (p.get("openings", [{}]) as Array)[0]
			return {"r": float(p.get("r", 0.3)), "y": float(op.get("y", 1.6)), "h": float(op.get("h", 0.24)),
				"w": float(op.get("w", 0.16)), "plinth": float((p.get("plinth", {}) as Dictionary).get("out", 0.04))}
	return {"r": 0.3, "y": 1.6, "h": 0.24, "w": 0.16, "plinth": 0.04}


## The tower's front normal (its own +z: the window side) on the ground plane.
func _front() -> Vector3:
	var t := _tower()
	if t == null:
		return _toward()
	var z := t.global_transform.basis.z
	z.y = 0.0
	return z.normalized()


## A point in front of the window: `out` world units beyond the wall surface, at height y above the tower base.
func _win_point(out: float, y: float) -> Vector3:
	var t := _tower()
	if t == null:
		return _spot("win_foot") + Vector3.UP * y
	var ws := _win_spec()
	return t.global_position + _front() * (float(ws["r"]) * _unit() + out) + Vector3.UP * y


func _sill() -> float:
	return float(_win_spec()["y"]) * _unit()


func at_window(role: String, pose: String) -> void:
	var a := stage.actor(role)
	if a == null:
		return
	if pose == "":
		a.pop_target = 0.02
		a.pop_delay = 0.0
		_win_role.erase(role)
		return
	var p := _win_point(0.012, 0.0)
	a.place_at(p)
	a.lift = _sill() - 0.012
	a.facing_left = false
	a.set_pose(pose, 0)
	a.pop_target = 1.0
	a.pop_delay = 0.0
	_win_role[role] = pose


# ------------------------------------------------------------------ the braid

func _clear_braid() -> void:
	for c in _braid:
		if is_instance_valid(c):
			c.queue_free()
	_braid.clear()
	_braid_anim = {}
	stage.unregister_prop("braid")


func _make_braid() -> void:
	_clear_braid()
	var top := _sill() + 0.01
	var n := int(ceilf((top - 0.1) / (SEG_H * 0.97)))
	var y := top
	for k in n:
		var c := _card(BRAID, SEG_H, atan2(_front().x, _front().z))
		c.global_position = _win_point(0.035 + 0.0005 * (k % 2), y - SEG_H)
		c.visible = false
		_braid.append(c)
		y -= SEG_H * 0.97
	var e := _card(BRAID_END, 0.16, atan2(_front().x, _front().z))
	e.global_position = _win_point(0.036, maxf(0.0, y - 0.16 + 0.03))
	e.visible = false
	_braid.append(e)
	stage.register_prop("braid", _braid[_braid.size() - 1], 0.025, top)


func braid_down() -> void:
	_make_braid()
	_braid_anim = {"t": 0.0, "dir": 1, "life": 1.3}
	_sfx("rp.slide", _win_point(0.03, _sill() * 0.5))


func braid_up() -> void:
	if _braid.is_empty():
		return
	_braid_anim = {"t": 0.0, "dir": -1, "life": 1.1}
	stage.unregister_prop("braid")


# ------------------------------------------------------------------ tap targets

func targets() -> Array:
	var out: Array = []
	if _tower() and _tower().visible:
		out.append("window")
	return out


func target_point(t: String) -> Variant:
	match t:
		"window":
			return _win_point(0.02, _sill() + float(_win_spec()["h"]) * _unit() * 0.4)
	return null


func target_radius(t: String) -> float:
	return 90.0 if t == "window" else -1.0


func wiggle(t: String) -> bool:
	if t == "window":
		for r in _win_role:
			var a := stage.actor(str(r))
			if a:
				a.hop_v = 0.6
		return true
	return false


## SPEAKER_OFF: a role at the window speaks from it (its actor is there, lifted).
func speaker_point(who: String) -> Variant:
	if _win_role.has(who):
		return _win_point(0.02, _sill() + 0.08)
	return null


# ------------------------------------------------------------------ fx

func fx(name: String) -> bool:
	var p := name.split(":")
	match p[0]:
		"sparkle":
			sparkle(_spot(p[1]) + Vector3.UP * 0.12)
			return true
		"gate":
			if p[1] == "open":
				stage.fx("fold:gate")
			else:
				stage.fx("pop:gate")
			return true
		"pull_rampion":  # 쑥: the father pulls the rampion; it comes up in his hands, root and all
			var f := stage.actor("father")
			if f:
				f.set_pose("pull", 0)
				f.hop_v = 0.4
			var sp := stage.set_piece("rampion")
			var at := _spot("rampion")
			if sp:
				at = sp.global_position
				sp.collapse(0.0)
			var c := fly(PULLED, at, at + Vector3.UP * 0.12 - _right() * 0.06 + _toward() * 0.03, 0.14, 0.5, 0.08, true)
			_cards["pulled"] = c
			return true
		"witch_appear":  # 반짝! the witch pops up in a burst of sparkles
			var g := stage.actor("gothel")
			if g:
				sparkle(g.global_position + Vector3.UP * 0.18, 10, 0.22)
				g.pop_target = 1.0
				g.pop_delay = 0.15
				g.set_pose("point", 1)
				g.hop_v = 0.6
			var f2 := stage.actor("father")
			if f2:
				f2.set_pose("shock", 0)
				f2.hop_v = 0.7
			stage.shake(0.5)
			return true
		"vanish":  # vanish:<role>: sparkles, gone
			var a := stage.actor(p[1])
			if a:
				sparkle(a.centre(), 10, 0.2)
				a.pop_target = 0.02
				a.pop_delay = 0.2
			return true
		"wand":  # 톡: the witch raises her stick, sparkles at its tip
			var g2 := stage.actor("gothel")
			if g2:
				g2.set_pose("wand", 1)
				g2.hop_v = 0.5
				sparkle(g2.global_position + Vector3.UP * g2.puppet.height * 1.1, 8, 0.12)
			return true
		"tower_rise":  # 쑥: the tower rises out of the page
			stage.fx("pop:tower")
			stage.shake(1.0)
			var t := _tower()
			if t:
				for k in 3:
					get_tree().create_timer(0.25 * k).timeout.connect(sparkle.bind(t.global_position + Vector3.UP * (0.3 + 0.5 * k), 8, 0.35, 0.1))
			var g3 := stage.actor("gothel")
			if g3:
				g3.set_pose("calm", 1)
			return true
		"window":  # window:<role>:<pose> (no pose: gone inside)
			at_window(p[1], p[2] if p.size() > 2 else "")
			return true
		"braid":
			match p[1]:
				"down":
					var r := stage.actor("rap")
					if r and _win_role.has("rap"):
						r.set_pose("win_letdown", 0)
					braid_down()
				"hook":  # the cut braid on the window hook, let down by the witch (nobody at the window)
					braid_down()
				"up":
					braid_up()
					var r2 := stage.actor("rap")
					if r2 and _win_role.has("rap"):
						get_tree().create_timer(1.0).timeout.connect(r2.set_pose.bind("win_smile", 0))
			return true
		"notes":  # notes[:role]: golden music notes drift out of the window (or from the singer)
			var from := _win_point(0.05, _sill() + 0.12)
			if p.size() > 1:
				var s := stage.actor(p[1])
				if s:
					from = s.centre() + Vector3.UP * 0.1
			for k in 5:
				get_tree().create_timer(0.55 * k).timeout.connect(func() -> void:
					fly(NOTES, from, from + _right() * randf_range(-0.5, 0.5) + Vector3.UP * randf_range(0.25, 0.5) + _toward() * 0.1,
						0.075, 2.2, 0.1))
			return true
		"in_window":  # the prince climbs in over the sill (a hop where he stands)
			var a2 := stage.actor(p[1])
			if a2:
				a2.hop_v = 0.9
			return true
		"snip":  # 싹둑: the scissors, the braid gone; short hair
			var g4 := stage.actor("gothel")
			var r3 := stage.actor("rap")
			if g4 and r3:
				var mid := (g4.centre() + r3.centre()) * 0.5 + Vector3.UP * 0.08
				fly(SCISSORS, g4.centre() + Vector3.UP * 0.1, mid, 0.06, 0.5, 0.06)
				get_tree().create_timer(0.6).timeout.connect(func() -> void:
					r3.set_pose("short_sad")
					r3.hop_v = 0.5
					stage.shake(0.4)
					_sfx("rp.snip"))
				get_tree().create_timer(2.6).timeout.connect(g4.set_pose.bind("wand", 1))
			return true
		"wind_float":  # 휘익~ the magic wind lifts the prince off the braid and sets him down softly in the grass
			var pr := stage.actor("prince")
			if pr:
				_float = {"t": 0.0, "life": 5.2, "from": pr.global_position, "to": _spot("land"), "h0": pr.lift}
				pr.set_pose("float")
				pr.set_meta("moving", true)
				for k in 6:
					get_tree().create_timer(0.4 * k).timeout.connect(func() -> void:
						var c0 := pr.centre()
						fly(WIND, c0 - _right() * 0.35 + Vector3.UP * 0.1, c0 + _right() * 0.35, 0.09, 1.2, 0.05))
			braid_up()
			return true
		"hold_hands":  # 꼭: they hold hands; petals
			var r4 := stage.actor("rap")
			var pr2 := stage.actor("prince")
			if r4 and pr2:
				var r_left := (pr2.global_position - r4.global_position).dot(_right()) < 0.0
				r4.set_pose("short_hold", 1 if r_left else 0)
				pr2.set_pose("hold", 0 if r_left else 1)
				r4.hop_v = 0.4
				pr2.hop_v = 0.4
				var c1 := (r4.centre() + pr2.centre()) * 0.5 + Vector3.UP * 0.2
				for k in 7:
					fly(PETALS, c1 + Vector3(randf_range(-0.3, 0.3), 0.25, 0.0),
						c1 + Vector3(randf_range(-0.4, 0.4), randf_range(-0.25, -0.1), 0.05), 0.06, 1.6 + 0.1 * k, 0.04)
			return true
	return false


# ------------------------------------------------------------------ tale verbs

func run_step(st: Dictionary, R: Node) -> void:
	match str(st.get("do", "")):
		"climb_braid":
			await _climb(st, R)
		_:
			push_warning("rapunzel: unknown step " + str(st.get("do", "")))


## The climber goes up the braid hand over hand (climb_cycle); at the sill it goes in (gone from the page), or it stops
## at `stop` of the way up (the empty tower: the witch at the window).
func _climb(st: Dictionary, R: Node) -> void:
	var who := str(st.get("who", ""))
	var a := stage.actor(who)
	if a == null:
		return
	if st.has("cam"):
		stage.shot_to(str(st["cam"]), "climb_at", {"rate": 1.0})
	var stop := float(st.get("stop", 1.0))
	var foot := _win_point(0.08, 0.0)
	foot.y = a.global_position.y
	var top_y := foot.y + (_sill() - a.puppet.height * 0.55) * stop
	a.place_at(foot)
	a.follow([foot + Vector3.UP * 0.01, Vector3(foot.x, top_y, foot.z)], float(st.get("speed", 0.18)), "")
	if st.has("line"):
		R._say.bind(str(st["line"])).call()
	await R._wait_actors([who])
	if stop >= 1.0:
		a.pop_target = 0.02
		a.pop_delay = 0.0
		_sfx("wc.plop")
		await R._wait(0.4)


func step(dt: float) -> void:
	_t += dt
	# braid unroll / draw up
	if not _braid_anim.is_empty() and not _braid.is_empty():
		_braid_anim["t"] = float(_braid_anim["t"]) + dt / float(_braid_anim["life"])
		var k := clampf(float(_braid_anim["t"]), 0.0, 1.0)
		var n := _braid.size()
		var shown := int(ceilf(k * n)) if int(_braid_anim["dir"]) > 0 else int(ceilf((1.0 - k) * n))
		for i in n:
			(_braid[i] as Node3D).visible = i < shown
		if k >= 1.0:
			if int(_braid_anim["dir"]) < 0:
				_clear_braid()
			_braid_anim = {}
	# the prince's soft descent on the magic wind
	if not _float.is_empty():
		var pr := stage.actor("prince")
		_float["t"] = float(_float["t"]) + dt / float(_float["life"])
		var k2 := clampf(float(_float["t"]), 0.0, 1.0)
		var e := k2 * k2 * (3.0 - 2.0 * k2)
		if pr:
			var from: Vector3 = _float["from"]
			var to: Vector3 = _float["to"]
			pr.place_at(from.lerp(to, e) + _right() * sin(k2 * TAU) * 0.04)
			pr.global_position.y = lerpf(from.y, to.y, e)
			pr.lift = lerpf(float(_float["h0"]), 0.0, e) + sin(k2 * PI) * 0.05
		if k2 >= 1.0:
			_float = {}
			if pr:
				pr.lift = 0.0
				pr.remove_meta("moving")
				pr.set_pose("sad")
				pr.hop_v = 0.3
				_sfx("wolf.flop", pr.global_position)
	for g: Dictionary in _grow.duplicate():
		var n2: Node3D = g["node"]
		if not is_instance_valid(n2):
			_grow.erase(g)
			continue
		g["t"] = float(g["t"]) + dt
		var tt := float(g["t"])
		var sy := 1.0
		if g["up"]:
			sy = 1.0 + 0.12 * sin(tt * TAU * 5.0) * exp(-tt * 4.0) if tt > 0.25 else lerpf(0.02, 1.1, tt / 0.25)
		else:
			sy = maxf(0.02, 1.0 - tt / 0.5)
		n2.scale = Vector3(1, sy, 1)
		if (g["up"] and tt > 1.0) or (not g["up"] and tt > 0.5):
			_grow.erase(g)
			if not g["up"] and g["free"]:
				n2.queue_free()
			elif g["up"]:
				n2.scale = Vector3.ONE
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
			else:
				fn.remove_meta("moving")
