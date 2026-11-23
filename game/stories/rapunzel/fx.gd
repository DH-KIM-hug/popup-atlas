extends TaleHandler
## 「라푼젤」 effects (TaleHandler, 2026-11-23; v2 2026-11-24: the room at the top of the tower).
## The stage builds the two places from script.json (home: cottage, wall, gate, the witch's rampion garden; forest:
## the building kit's 3D tower -- kit preset rapunzel_tower: a slim shaft, the round room on top corbelled out, a real
## window in a flat front with a stone sill ledge, a plank floor --, the hiding tree, the field cottage); this handler
## adds what only this tale does:
##  - window figures: an actor leaning out of the tower window (upper-body win_* figure: hands on the sill, set back
##    in the reveal so the jambs frame her, a small shadowless fill on the face); `enter.rp.window` {role: pose} or
##    fx window:<role>:<pose> (empty pose = gone inside);
##  - THE ROOM: the tower's own top storey. Furniture cards stand on the kit floor (children of the building, so they
##    rise with it); `enter.rp.room` [roles] stand those roles on the room floor at their `at` spots; a warm light
##    comes on while the camera is inside; the shots dolly through the open window (same focus, only the distance
##    changes); fx room_swap:<out>:<in>:<spot>:<pose> changes who is in the room while the camera looks away;
##  - THE BRAID: a column of tiled braid cards from the sill ledge to the grass (in front of the ledge, along the tower's
##    own front normal), unrolling top to bottom (braid:down / braid:hook) and drawn up (braid:up); while it is down a
##    hook on the inner sill holds it (seen from inside); registered as a prop for the overlap check;
##  - climb_braid (tale verb): the climber goes up hand over hand (the drawn climb_cycle, story_actor) with the camera
##    following, and climbs in over the sill (or holds at the top: `hold`; or stops part way: `stop`);
##    climb_in (tale verb): from the top of the braid over the sill onto the room floor;
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
const SEG_H := 0.3  ## one braid card (0.045 wide, widened BRAID_X: reads as a thick braid in the wide shots)
const BRAID_X := 1.5
const HOOK_H := 0.06
const WIN_BRAID_X := 0.006  ## where the braid drawn on her win_letdown figure meets the sill (right of centre)
const ROOM_BRAID_X := 0.055  ## where the braid drawn on her standing figures ends by her feet (right of centre)

var _tex := {}
var _cards: Dictionary = {}
var _flyers: Array = []
var _grow: Array = []
var _braid: Array = []  ## braid cards top -> bottom
var _braid_anim := {}  ## {t, dir: 1 down / -1 up, life}
var _float := {}  ## the prince's soft descent {t, life, from, to, h0}
var _t := 0.0
var _win_role := {}  ## role -> pose of who is at the window
var _room_role := {}  ## role -> true: standing on the room floor
var _room_built := false
var _room_light: OmniLight3D
var _view: Node3D  ## treetops seen from the window (inside only)
var _hook: Array = []  ## the hook + the braid over the sill, down the inner wall and along the floor to her (inside)
var _bx := 0.0  ## the braid's line right of the window's centre (her drawn braid's end when she let it down)


func setup() -> void:
	pass


func build_async() -> void:
	enter_beat(stage.beat)


func enter_beat(b: Dictionary) -> void:
	_build_room()
	var en: Dictionary = b.get("enter", {})
	var hid: Dictionary = en.get("hidden", {})
	for r in hid:
		var a := stage.actor(str(r))
		if a:
			a.place_at(stage.spot_point(hid[r]))
			a.lift = 0.0
			a.pop_target = 0.02
			a.pop_delay = 0.0
			_room_role.erase(str(r))
	var rp: Dictionary = en.get("rp", {})
	for r in _win_role.keys():
		_leave_window(str(r))
	_win_role.clear()
	var win: Dictionary = rp.get("window", {})
	for r in win:
		at_window(str(r), str(win[r]))
	var who: Dictionary = en.get("who", {})
	for r in _room_role.keys():
		if not (en.get("keep", []) as Array).has(r) and not who.has(r):
			_room_role.erase(r)
	for r in rp.get("room", []):
		var a2 := stage.actor(str(r))
		if a2:
			var at: Dictionary = en.get("at", {})
			if at.has(r):
				a2.place_at(stage.spot_point(at[r]))
			a2.lift = 0.0
			a2.global_position.y = _floor_y()
			_room_role[str(r)] = true
	var id := str(b.get("id", ""))
	if str(rp.get("braid", "")) == "hooked":
		if _braid.is_empty():
			_make_braid()
			for c in _braid:
				(c as Node3D).visible = true
		else:
			_make_hook()  # she is in the room now: her braid runs from her along the floor to the window
	elif _braid.size() > 0 and id in ["song", "prince", "climb", "empty"]:
		_clear_braid()
	# --beat starts: the prince is at the top of the braid when the meet begins
	if id == "meet":
		var pr := stage.actor("prince")
		if pr and not _room_role.has("prince") and absf(pr.global_position.y - _top_feet(pr)) > 0.05:
			pr.place_at(_climb_foot(pr) + Vector3.UP * (_top_feet(pr) - _climb_foot(pr).y))
			pr.pop_target = 1.0
			pr.pop_delay = 0.0


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


# ------------------------------------------------------------------ the tower window and the room

func _tower() -> SetPiece:
	return stage.set_piece("tower")


func _unit() -> float:
	var t := _tower()
	if t and t.building:
		return t.building.unit
	return 1.0


## The tower spec numbers this tale relies on (kit preset rapunzel_tower: the part with the window = the room).
func _win_spec() -> Dictionary:
	var t := _tower()
	if t and t.building:
		for p: Dictionary in t.building.spec.get("parts", []):
			if (p.get("openings", []) as Array).is_empty():
				continue
			var op: Dictionary = (p["openings"] as Array)[0]
			var r := float(p.get("r", 0.56))
			var fl := float(p.get("flat", 0.0))
			var ledge: Dictionary = op.get("ledge", {})
			return {"r": r, "face": sqrt(maxf(r * r - fl * fl * 0.25, 0.0)), "thick": float(p.get("thick", 0.06)),
				"base": float(p.get("base", 0.0)), "y": float(p.get("base", 0.0)) + float(op.get("y", 0.15)),
				"h": float(op.get("h", 0.25)), "w": float(op.get("w", 0.14)), "ledge": float(ledge.get("out", 0.0)),
				"room_h": float(p.get("h", 0.56))}
	return {"r": 0.56, "face": 0.545, "thick": 0.06, "base": 1.84, "y": 1.99, "h": 0.25, "w": 0.14, "ledge": 0.05, "room_h": 0.56}


## The tower's front normal (its own +z: the window side) on the ground plane.
func _front() -> Vector3:
	var t := _tower()
	if t == null:
		return _toward()
	var z := t.global_transform.basis.z
	z.y = 0.0
	return z.normalized()


## A point on the window's axis: `out` world units in front of the wall's outer face (negative: into the reveal /
## the room), at height y above the tower base.
func _win_point(out: float, y: float) -> Vector3:
	var t := _tower()
	if t == null:
		return _spot("win_foot") + Vector3.UP * y
	var ws := _win_spec()
	return t.global_position + _front() * (float(ws["face"]) * _unit() + out) + Vector3.UP * y


func _sill() -> float:
	return float(_win_spec()["y"]) * _unit()


func _floor_y() -> float:
	var t := _tower()
	return (t.global_position.y if t else 0.0) + float(_win_spec()["base"]) * _unit() + 0.003


func _braid_out() -> float:
	return float(_win_spec()["ledge"]) * _unit() + 0.012


func at_window(role: String, pose: String) -> void:
	var a := stage.actor(role)
	if a == null:
		return
	if pose == "":
		_leave_window(role)
		_win_role.erase(role)
		a.pop_target = 0.02
		a.pop_delay = 0.0
		return
	# set back in the reveal (behind the outer face): the jambs frame her, her hands rest on the sill
	var p := _win_point(-float(_win_spec()["thick"]) * _unit() * 0.45, 0.0)
	a.place_at(p)
	a.lift = _sill() + 0.002
	a.facing_left = false
	a.set_pose(pose, 0)
	a.pop_target = 1.0
	a.pop_delay = 0.0
	_room_role.erase(role)
	_win_role[role] = pose
	# the window is in the wall's shade: a small shadowless warm fill just in front of the face (motion.md "Peeks")
	var lt := a.get_node_or_null("WinFill") as OmniLight3D
	if lt == null:
		lt = OmniLight3D.new()
		lt.name = "WinFill"
		lt.light_color = Color(1.0, 0.88, 0.7)
		lt.light_energy = 0.12
		lt.omni_range = 0.16
		lt.shadow_enabled = false
		a.add_child(lt)
	lt.position = Vector3(0, a.lift + a.puppet.height * 0.3, 0) + _front() * 0.07
	lt.visible = true


func _leave_window(role: String) -> void:
	var a := stage.actor(role)
	if a == null:
		return
	var lt := a.get_node_or_null("WinFill") as OmniLight3D
	if lt:
		lt.visible = false
	if _win_role.has(role):
		a.lift = 0.0


## The room's furniture: cards standing on the kit's plank floor, children of the building (they rise with it), in
## the building's own frame (+z = the window wall); a warm light inside that only burns while the camera is in.
func _build_room() -> void:
	if _room_built:
		return
	var t := _tower()
	if t == null or t.building == null:
		return
	_room_built = true
	var b := t.building
	var u := _unit()
	var fy := float(_win_spec()["base"]) * u + 0.003
	var items := [["story_rp_room_04", 0.2, Vector2(0.29, -0.3)], ["story_rp_room_06", 0.15, Vector2(-0.3, -0.31)],
		["story_rp_room_05", 0.09, Vector2(-0.06, -0.4)], ["story_rp_room_08", 0.21, Vector2(-0.39, 0.02)]]
	for it: Array in items:
		var n := Node3D.new()
		b.add_child(n)
		var tex := _texid(str(it[0]))
		if tex:
			var c := PaperCard.new()
			c.texture = tex
			c.height = float(it[1])
			c.thickness = 0.004
			n.add_child(c)
		n.position = Vector3((it[2] as Vector2).x, fy, (it[2] as Vector2).y)
	var rug := Node3D.new()
	b.add_child(rug)
	var rt := _texid("story_rp_room_07")
	if rt:
		var rc := PaperCard.new()
		rc.texture = rt
		rc.height = 0.42
		rc.thickness = 0.002
		rug.add_child(rc)
	rug.rotation.x = -PI * 0.5
	rug.position = Vector3(0.0, fy + 0.002, -0.08 + 0.21)
	# what the window shows from inside: treetops far below (cards out beyond the window, their tops under the eye
	# line, shown only while the camera is in the room; outside shots never see them)
	_view = Node3D.new()
	b.add_child(_view)
	var face := float(_win_spec()["face"]) * u
	var trees := [["forest_broadleaf_02", 1.5, Vector2(-0.3, 1.2)], ["forest_broadleaf_05", 1.4, Vector2(0.35, 1.5)],
		["forest_broadleaf_00", 1.6, Vector2(0.0, 1.9)], ["forest_broadleaf_07", 1.3, Vector2(-0.7, 1.8)],
		["forest_broadleaf_03", 1.5, Vector2(0.75, 2.2)], ["forest_broadleaf_09", 1.4, Vector2(-0.25, 2.5)],
		["forest_conifer_02", 1.6, Vector2(0.5, 2.8)], ["forest_broadleaf_11", 1.5, Vector2(-0.6, 3.0)]]
	for it: Array in trees:
		var n2 := Node3D.new()
		_view.add_child(n2)
		var tx := _texid(str(it[0]))
		if tx:
			var c2 := PaperCard.new()
			c2.texture = tx
			c2.height = float(it[1])
			c2.thickness = 0.01
			n2.add_child(c2)
		var q: Vector2 = it[2]
		n2.position = Vector3(q.x, fy - 0.03 - float(it[1]) - q.y * 0.05, face + q.y)
		n2.rotation.y = PI  # facing the window
	_view.visible = false
	_room_light = OmniLight3D.new()
	_room_light.light_color = Color(1.0, 0.84, 0.62)
	_room_light.light_energy = 1.1
	_room_light.omni_range = 0.95
	_room_light.shadow_enabled = false
	_room_light.position = Vector3(0.0, fy + float(_win_spec()["room_h"]) * u * 0.75, -0.05)
	_room_light.visible = false
	b.add_child(_room_light)


## A point on the window's axis shifted `x` along the tower's own right (the braid's line: her drawn braid's end).
func _wp(out: float, y: float, x: float) -> Vector3:
	var t := _tower()
	var r := t.global_transform.basis.x.normalized() if t else _right()
	return _win_point(out, y) + r * x


## A braid lying flat from p0 to p1 (on the floor / the sill), in SEG_H pieces, or standing up a wall (`up`: from p0
## straight up to p1, facing `yaw`).
func _braid_run(p0: Vector3, p1: Vector3, up := false, yaw := 0.0) -> void:
	var d := p1 - p0
	var L := d.length()
	if L < 0.005:
		return
	var n := int(ceilf(L / SEG_H))
	var seg := L / n
	for k in n:
		var a := p0 + d * (float(k) / n)
		var c: Node3D
		if up:
			c = _card(BRAID, seg * 1.04, yaw)
		else:
			var dn := d / L
			c = _card(BRAID, seg * 1.04, atan2(-dn.x, -dn.z))
			c.rotation.x = -PI * 0.5  # lying: its length runs from a toward p1
		c.scale = Vector3(BRAID_X, 1, 1)
		c.global_position = a
		_hook.append(c)


## The braid inside (seen from the room and through the window): over the sill, the hook under it on the inner wall,
## down the inner wall to the floor and, when Rapunzel is in the room with her long hair, along the floor to the end of
## the braid drawn on her figure (her braid runs from her head to the window: no gap at any angle).
func _make_hook() -> void:
	_clear_hook()
	var ws := _win_spec()
	var u := _unit()
	var inner := -float(ws["thick"]) * u
	var yaw_in := atan2(-_front().x, -_front().z)  # facing into the room
	# the hook and the braid's knot (the top of the hooked-braid card), on the inner wall just under the sill
	var hk := Node3D.new()
	hk.top_level = true
	stage.add_child(hk)
	var src := _texid(HOOKED)
	if src:
		var at := AtlasTexture.new()
		at.atlas = src
		var sz := src.get_size()
		at.region = Rect2(0, 0, sz.x, sz.y * 0.36)
		var c := PaperCard.new()
		c.texture = at
		c.height = HOOK_H
		c.thickness = 0.003
		hk.add_child(c)
	hk.rotation.y = yaw_in
	hk.global_position = _wp(inner - 0.006, _sill() - HOOK_H - 0.004, _bx)
	_hook.append(hk)
	# over the sill: from the ledge's front edge (where the hanging braid starts) back across the reveal; at the
	# window her drawn braid ends on it (her hands on the sill)
	var ov := _card(BRAID, float(ws["thick"]) * u + _braid_out() + 0.012, atan2(_front().x, _front().z))
	ov.rotation.x = -PI * 0.5
	ov.scale = Vector3(BRAID_X, 1, 1)
	ov.global_position = _wp(_braid_out(), _sill() + 0.004, _bx)
	_hook.append(ov)
	# down the inner wall to the floor
	var base := _tower().global_position.y if _tower() else 0.0
	var wall_foot := _wp(inner - 0.004, 0.0, _bx)
	wall_foot.y = _floor_y()
	var wall_top := wall_foot
	wall_top.y = base + _sill() + 0.004
	_braid_run(wall_foot, wall_top, true, yaw_in)
	# along the floor to the end of the braid drawn on her standing figure (it ends by her feet on her left: screen
	# right), when she is in the room with her long hair
	var r := stage.actor("rap")
	if r and _room_role.has("rap") and not r.pose.begins_with("short"):
		var p0 := r.global_position + _right() * ROOM_BRAID_X
		p0.y = _floor_y() + 0.012  # over the rug
		var p1 := wall_foot + _front() * -0.02
		p1.y = _floor_y() + 0.012
		_braid_run(p0, p1)


func _clear_hook() -> void:
	for c in _hook:
		if is_instance_valid(c):
			c.queue_free()
	_hook.clear()


# ------------------------------------------------------------------ the braid

func _clear_braid() -> void:
	for c in _braid:
		if is_instance_valid(c):
			c.queue_free()
	_braid.clear()
	_braid_anim = {}
	_clear_hook()
	stage.unregister_prop("braid")


func _make_braid() -> void:
	_clear_braid()
	_bx = WIN_BRAID_X if _win_role.has("rap") else 0.0
	var top := _sill() + 0.012  # the first piece tucks over the sill piece's front end
	var n := int(ceilf((top - 0.1) / (SEG_H * 0.97)))
	var y := top
	var yaw := atan2(_front().x, _front().z)
	for k in n:
		var c := _card(BRAID, SEG_H, yaw)
		c.scale = Vector3(BRAID_X, 1, 1)
		c.global_position = _wp(_braid_out() + 0.0005 * (k % 2), y - SEG_H, _bx)
		c.visible = false
		_braid.append(c)
		y -= SEG_H * 0.97
	var e := _card(BRAID_END, 0.2, yaw)
	e.scale = Vector3(BRAID_X, 1, 1)
	e.global_position = _wp(_braid_out() + 0.001, maxf(0.0, y - 0.2 + 0.04), _bx)
	e.visible = false
	_braid.append(e)
	_make_hook()
	stage.register_prop("braid", _braid[_braid.size() - 1], 0.03, top)


func braid_down() -> void:
	_make_braid()
	_braid_anim = {"t": 0.0, "dir": 1, "life": 1.5}
	_sfx("rp.slide", _win_point(0.03, _sill() * 0.5))


func braid_up() -> void:
	if _braid.is_empty():
		return
	_braid_anim = {"t": 0.0, "dir": -1, "life": 1.3}
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
			return _win_point(0.0, _sill() + float(_win_spec()["h"]) * _unit() * 0.4)
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
		return _win_point(0.0, _sill() + 0.08)
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
		"room_swap":  # room_swap:<out>:<in>:<spot>:<pose>: while the camera looks at the window, who is in the room changes
			var o := stage.actor(p[1])
			if o:
				o.pop_target = 0.02
				o.pop_delay = 0.0
				_room_role.erase(p[1])
			var n := stage.actor(p[2])
			if n:
				n.place_at(_spot(p[3]))
				n.global_position.y = _floor_y()
				n.lift = 0.0
				n.set_pose(p[4] if p.size() > 4 else "calm", 0)
				n.pop_target = 1.0
				n.pop_delay = 0.0
				_room_role[p[2]] = true
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
		"climb_in":
			await _climb_in(str(st.get("who", "")), str(st.get("to", "r_prince")), str(st.get("pose", "calm")), R)
		_:
			push_warning("rapunzel: unknown step " + str(st.get("do", "")))


## Where a climber's feet are at the braid (on the ground in front of it) and at the top (hands at the sill).
func _climb_foot(a: StoryActor) -> Vector3:
	var f := _win_point(_braid_out() + 0.045, 0.0)
	var t := _tower()
	f.y = t.global_position.y if t else a.global_position.y
	return f


func _top_feet(a: StoryActor) -> float:
	return _climb_foot(a).y + _sill() - a.puppet.height * 0.62


## The climber goes up the braid hand over hand (climb_cycle) with the camera following; at the top Rapunzel steps
## back from the window and the climber climbs in over the sill (or holds at the top: `hold`, the meet climbs in; or
## stops at `stop` of the way up: the empty tower).
func _climb(st: Dictionary, R: Node) -> void:
	var who := str(st.get("who", ""))
	var a := stage.actor(who)
	if a == null:
		return
	if st.has("cam"):
		stage.shot_to(str(st["cam"]), "climb_at", {"rate": 1.0, "follow": who})
	var stop := float(st.get("stop", 1.0))
	var foot := _climb_foot(a)
	foot.y = a.global_position.y
	var top_y := foot.y + (_top_feet(a) - foot.y) * stop
	if bool(st.get("hold", false)):
		top_y = foot.y + _sill() - a.puppet.height * 0.92  # his head just under the sill: the window stays clear
	a.place_at(foot)
	if bool(st.get("hold", false)):
		a.pose = "climb_cycle"  # when the climb stops he keeps hanging on the braid (not the standing figure)
	a.follow([foot + Vector3.UP * 0.01, Vector3(foot.x, top_y, foot.z)], float(st.get("speed", 0.18)), "")
	if st.has("line"):
		R._say.bind(str(st["line"])).call()
	if stop >= 1.0 and _win_role.has("rap"):
		# nearly up: she steps back into the room, out of the climber's way over the sill (the climb goes on)
		while a.moving() and a.global_position.y < top_y - 0.3:
			await get_tree().process_frame
		at_window("rap", "")
		var rr0 := stage.actor("rap")
		if rr0:
			rr0.place_at(_spot("r_rap"))
			rr0.global_position.y = _floor_y()
	await R._wait_actors([who])
	if st.has("cam") and stop >= 1.0:
		# let go of the follow with an eased move to a still frame at the sill (the climber turning in over the sill
		# jerked the followed focus: CAM_JERK)
		stage.shot_to("climb_top", "climb_at", {"rate": 1.2})
	if stop >= 1.0 and not bool(st.get("hold", false)):
		await _climb_in(who, "", "", R)
	elif bool(st.get("hold", false)):
		a.set_pose("climb_cycle", 0)  # hanging on the braid just under the sill (seen from behind) until he climbs in


## Over the sill: from the top of the braid into the window and down onto the room floor (to a spot: standing there
## in `pose`; no spot: gone from sight inside).
func _climb_in(who: String, to: String, pose: String, R: Node) -> void:
	var a := stage.actor(who)
	if a == null:
		return
	var base := _tower().global_position.y if _tower() else 0.0
	var ws := _win_spec()
	var u := _unit()
	var sill_out := _win_point(0.01, _sill())
	sill_out.y = base + _sill()
	var sill_in := _win_point(-float(ws["thick"]) * u - 0.03, 0.0)
	sill_in.y = base + _sill()
	var floor_in := _win_point(-float(ws["thick"]) * u - 0.1, 0.0)
	floor_in.y = _floor_y()
	var pts := [sill_out, sill_in, floor_in]
	if to != "":
		var q := _spot(to)
		q.y = _floor_y()
		pts.append(q)
	a.follow(pts, 0.22, "")
	_sfx("wc.plop")
	await R._wait_actors([who])
	if to == "":
		a.pop_target = 0.02
		a.pop_delay = 0.0
		await R._wait(0.3)
	else:
		a.global_position.y = _floor_y()
		a.set_pose(pose, 0)
		_room_role[who] = true


func step(dt: float) -> void:
	_t += dt
	if _room_light:
		_room_light.visible = stage.camera_inside == "tower"
		_view.visible = _room_light.visible
	for r in _room_role:  # nobody in the room sinks to the ground under the tower (spacing / pose swaps)
		var ra := stage.actor(str(r))
		if ra and not ra.moving() and absf(ra.global_position.y - _floor_y()) > 0.002:
			ra.global_position.y = _floor_y()
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
