extends TaleHandler
## 「아기 돼지 삼형제」 effects (TaleHandler): the builders at work (straw carried, planks hammered, bricks flying onto
## the wall), music notes, the brothers' tease, the wolf's 후~ (wind curls, straw and splinters flying), dust, the
## brick kitchen cutaway with the fire, the boiling pot, the wolf dropping down the flue and shooting back out.
## The stage does the generic parts (cast, spots, houses in bands, build / huff / tap verbs); fx names come from
## script.json steps (and build / huff `fx`, which see stage.build_ctx {house, walker, tap, taps}).

const ATLAS := "res://art/atlas/"
const PROPS := {
	"straw": ["story_build_props/story_build_props_02.webp", "story_build_props/story_build_props_03.webp", "story_build_props/story_build_props_04.webp"],
	"plank": ["story_build_props/story_build_props_06.webp"],
	"brick": ["story_build_props/story_build_props_09.webp"],
	"splinter": ["story_build_props/story_build_props_20.webp", "story_build_props/story_build_props_21.webp"],
	"star": ["story_hearth/story_hearth_18.webp"],
	"steam": ["story_hearth/story_hearth_06.webp", "story_hearth/story_hearth_07.webp", "story_hearth/story_hearth_08.webp"],
	"splash": ["story_hearth/story_hearth_09.webp"],
	"soot": ["story_hearth/story_hearth_10.webp"],
}

var _flyers: Array = []  ## {node, age, life, from, to, arc, spin, grow, fade_in}
var _errands: Dictionary = {}  ## role -> [[point, walk_pose, end_pose, speed, left(-1/0/1)], ...]
var _music: Dictionary = {}  ## role -> seconds to the next note
var _boil := 0.0
var _t := 0.0
var _tex: Dictionary = {}
static var _note_tex: Texture2D
static var _curl_tex: Texture2D
var _launch: Dictionary = {}  ## wolf flight {from, to, t, dur, arc}
var _drop: Dictionary = {}


func setup() -> void:
	if _note_tex == null:
		_note_tex = _make_note_texture()
		_curl_tex = _make_curl_texture()


func _texp(rel: String) -> Texture2D:
	if not _tex.has(rel):
		_tex[rel] = load(ATLAS + rel)
	return _tex[rel]


func _cam() -> Camera3D:
	return stage.camera()


func _a(role: String) -> StoryActor:
	return stage.actor(role)


func _house() -> SetPiece:
	return stage.set_piece(str(stage.build_ctx.get("house", "house")))


## A paper card that flies from `from` to `to` on an arc, spinning, facing the camera, then fades (scales) away.
func fly(kind: String, from: Vector3, to: Vector3, h: float, life := 0.8, arc := 0.15, spin := 4.0, grow := 1.0, keep := 0.0) -> Node3D:
	var lst: Array = PROPS.get(kind, [])
	var tex: Texture2D
	if kind == "note":
		tex = _note_tex
	elif kind == "curl":
		tex = _curl_tex
	elif not lst.is_empty():
		tex = _texp(str(lst[randi() % lst.size()]))
	if tex == null:
		return null
	var node := Node3D.new()
	node.top_level = true
	stage.add_child(node)
	var c := PaperCard.new()
	c.texture = tex
	c.height = h
	c.thickness = clampf(h * 0.05, 0.002, 0.008)
	c.position = Vector3(0, -h * 0.5, 0)
	node.add_child(c)
	node.global_position = from
	node.scale = Vector3.ONE * 0.05
	_flyers.append({"node": node, "age": 0.0, "life": life, "from": from, "to": to, "arc": arc, "spin": spin,
		"grow": grow, "keep": keep, "ph": randf() * TAU})
	return node


func _step_flyers(dt: float) -> void:
	var cam := _cam()
	for i in range(_flyers.size() - 1, -1, -1):
		var f: Dictionary = _flyers[i]
		var n: Node3D = f["node"]
		f["age"] = float(f["age"]) + dt
		var life: float = f["life"]
		var keep: float = f["keep"]
		var u := clampf(float(f["age"]) / life, 0.0, 1.0)
		if float(f["age"]) >= life + keep:
			n.queue_free()
			_flyers.remove_at(i)
			continue
		var e := u * (2.0 - u)
		var p: Vector3 = (f["from"] as Vector3).lerp(f["to"], e)
		p.y += sin(u * PI) * float(f["arc"])
		n.global_position = p
		var face := atan2(cam.global_position.x - p.x, cam.global_position.z - p.z)
		n.global_rotation = Vector3(0, face, float(f["spin"]) * float(f["age"]) * 0.3 + sin(float(f["age"]) * 6.0 + float(f["ph"])) * 0.2)
		var s := minf(1.0, u * 6.0 + 0.05) * lerpf(1.0, float(f["grow"]), u)
		if keep <= 0.0:
			s *= clampf((1.0 - u) * 4.0, 0.0, 1.0)
		elif float(f["age"]) > life:
			s *= clampf(1.0 - (float(f["age"]) - life) / keep * 1.0, 0.0, 1.0) if float(f["age"]) > life + keep * 0.6 else 1.0
		n.scale = Vector3.ONE * maxf(s, 0.01)


# ------------------------------------------------------------------ errands (keep the builders moving)

func errand(role: String, list: Array) -> void:
	_errands[role] = list


func _step_errands() -> void:
	for role in _errands.keys():
		var a := _a(str(role))
		var q: Array = _errands[role]
		if a == null or q.is_empty():
			_errands.erase(role)
			continue
		if a.moving():
			continue
		var e: Array = q.pop_front()
		if e[0] == null:
			# a pause / pose change without moving
			if str(e[2]) != "":
				a.set_pose(str(e[2]), int(e[4]) if e.size() > 4 else -1)
			continue
		a.walk_to(e[0], float(e[3]), str(e[1]))
		if str(e[2]) != "":
			a.pose = str(e[2])


# ------------------------------------------------------------------ fx

func fx(name: String) -> bool:
	var ctx: Dictionary = stage.build_ctx
	match name:
		"straw_pop":
			# 첫째 carries a straw bundle from the pile to the house and trots back for the next
			var pig := _a(str(ctx.get("walker", "pig_a")))
			var house := _house()
			var pile := stage.set_piece("pile")
			if pig and house and pile:
				# drop spot: the house's corner on the pile's side, a little in front of the wall
				var to_pile := pile.global_position - house.global_position
				to_pile.y = 0.0
				var sgn := 1.0 if to_pile.dot(stage.dir_vec("right")) > 0.0 else -1.0
				var side := house.global_position + stage.dir_vec("right") * sgn * house.height * 0.62 + stage.dir_vec("toward") * 0.16
				var back := pile.global_position + stage.dir_vec("right") * sgn * 0.1 + stage.dir_vec("toward") * 0.18
				# there and back, then he turns to face the house again for the next bundle
				errand(pig.role, [[side, "carry_straw", "carry_straw", 0.32], [back, "side_walk", "carry_straw", 0.3],
					[null, "", "carry_straw", 0.0, 1 if sgn > 0.0 else 0]])
				for k in 3:
					fly("straw", pile.global_position + Vector3(0, 0.06, 0), house.centre() + Vector3(randf_range(-0.2, 0.2), randf_range(-0.05, 0.1), 0.05), 0.07, 0.6 + 0.1 * k, 0.25)
			_spark(house)
		"hammer_bang":
			var pig2 := _a(str(ctx.get("walker", "pig_b")))
			var house2 := _house()
			var pile2 := stage.set_piece("pile")
			if pig2:
				pig2.hop_v = 0.8
				pig2.set_pose("hammer")
			if house2 and pile2:
				fly("plank", pile2.global_position + Vector3(0, 0.08, 0), house2.centre() + Vector3(0, 0.05, 0.06), 0.16, 0.55, 0.3, 6.0)
			_spark(house2)
			if house2:
				house2.bounce()
		"brick_thunk":
			var pig3 := _a(str(ctx.get("walker", "pig_c")))
			var house3 := _house()
			var pile3 := stage.set_piece("pile")
			if pig3:
				pig3.hop_v = 0.6
			if house3 and pile3:
				fly("brick", pile3.global_position + Vector3(0, 0.06, 0), house3.centre() + Vector3(randf_range(-0.15, 0.15), 0.05, 0.06), 0.05, 0.5, 0.35, 8.0)
				house3.bounce()
		"star_burst":
			var h := _house() if _house() else stage.set_piece("house")
			if h:
				fly("star", h.global_position + Vector3(0, h.height * 0.6, 0.08), h.global_position + Vector3(0, h.height * 0.95, 0.12), 0.32, 0.5, 0.0, 0.5, 1.4, 0.6)
				h.bounce()
			for r in stage.actors:
				var a := _a(str(r))
				if a and a.pop_target > 0.5 and r != "wolf":
					a.hop_v = 0.9
		"flute_notes":
			_music["pig_a"] = 0.0
		"violin_notes":
			_music["pig_b"] = 0.0
		"music_stop":
			_music.clear()
		"brothers_tease":
			# 첫째 and 둘째 stroll in from the left (side view), stop by the house and call to their brother
			var a1 := _a("pig_a")
			var a2 := _a("pig_b")
			var at := stage.spot_point("tease")
			for k in 2:
				var p := a1 if k == 0 else a2
				if p == null:
					continue
				p.place_at(at + stage.dir_vec("left") * (1.1 + 0.22 * k))
				p.pop_delay = 0.0
				p.pop_target = 1.0
				p.puppet.set_figure("side_walk", false, true)
				var goal := at + stage.dir_vec("left") * 0.22 * k + stage.dir_vec("away") * 0.04 * k
				p.walk_to(goal, 0.32, "side_walk")
				p.pose = "tease" if k == 0 else "violin"
		"brothers_leave":
			for k in 2:
				var p2 := _a("pig_a" if k == 0 else "pig_b")
				if p2 and p2.pop_target > 0.5:
					errand(p2.role, [[p2.global_position + stage.dir_vec("right") * 2.4, "side_walk", "calm", 0.34]])
					var gone := func():
						if is_instance_valid(p2):
							p2.pop_target = 0.02
					get_tree().create_timer(4.5).timeout.connect(gone)
			_music.clear()
		"straw_fly", "wood_wobble", "brick_huff":
			_huff_wind(name)
		"thud_dust":
			var w := _a("wolf")
			if w:
				w.hop_v = 0.5
				for k in 5:
					var p0 := w.global_position + Vector3(0, 0.02, 0)
					fly("steam", p0, p0 + stage.dir_vec("right" if k % 2 == 0 else "left") * randf_range(0.12, 0.25) + Vector3(0, randf_range(0.03, 0.1), 0), 0.08, 0.8, 0.05, 1.0, 1.6)
		"room_ready":
			_room_ready()
		"inside_view":
			# into the house: the camera glides in through the front (the wall hides only while it passes); the
			# brothers are at the hearth when it arrives
			stage.shot_to("inside", "in_focus")
			get_tree().create_timer(1.0).timeout.connect(_pigs_to_room)
		"outside_view":
			stage.shot_to("roof", "focus")
			get_tree().create_timer(0.9).timeout.connect(_pigs_to_windows)
		"cutaway_open":
			_cutaway(true)
		"cutaway_close":
			_cutaway(false)
		"flame_m":
			_flame(1)
		"flame_l":
			_flame(2)
		"boil":
			_boil = 1.0
			var pot := stage.set_piece("k_pot")
			if pot:
				pot.bounce()
		"wolf_drop":
			_wolf_drop()
		"splash":
			var pot2 := stage.set_piece("k_pot")
			if pot2:
				var c := pot2.global_position + Vector3(0, pot2.height * 0.9, 0.04)
				fly("splash", c, c + Vector3(0, 0.12, 0), 0.22, 0.6, 0.0, 0.0, 1.4, 0.3)
				for k in 4:
					fly("steam", c, c + Vector3(randf_range(-0.25, 0.25), randf_range(0.25, 0.45), 0.05), 0.12, 1.0, 0.05, 1.0, 1.8)
				pot2.bounce()
			var w2 := _a("wolf")
			if w2:
				w2.hop_v = 1.2
		"wolf_launch":
			_wolf_launch()
		"pigs_cheer":
			for r in ["pig_a", "pig_b", "pig_c"]:
				var a3 := _a(r)
				if a3:
					a3.hop_v = 1.0
		_:
			if name.begins_with("pop:story_houses_0"):
				# a new brick cottage on its plot: stars and the brothers cheer (generic pop still runs)
				var sp := stage.set_piece(name.substr(4))
				if sp:
					sp.pop_card(0.0)
					sp.bounce()
					fly("star", sp.global_position + Vector3(0, sp.height * 0.6, 0.08), sp.global_position + Vector3(0, sp.height, 0.12), 0.28, 0.45, 0.0, 0.5, 1.4, 0.5)
				fx("pigs_cheer")
				return true
			if name.begins_with("pop:story_build_props_"):
				var mat := stage.set_piece(name.substr(4))
				if mat:
					mat.pop_card(0.0)
					mat.bounce()
				return true
			return false
	return true


func _spark(h: SetPiece) -> void:
	if h == null:
		return
	var top := h.global_position + Vector3(0, h.height * float(h.shown) / float(maxi(h.band_count(), 1)) * 0.8, 0.08)
	fly("star", top, top + Vector3(0, 0.08, 0.02), 0.12, 0.3, 0.0, 1.0, 1.3, 0.15)


## 후~: wind curls stream from the wolf's mouth to the house; straw tufts / splinters fly off it downwind.
func _huff_wind(kind: String) -> void:
	var w := _a("wolf")
	var h := _house()
	if w == null or h == null:
		return
	var face := stage.dir_vec("left") if w.facing_left else stage.dir_vec("right")
	var mouth := w.global_position + Vector3(0, w.puppet.height * 0.78, 0) + face * w.puppet.height * 0.25 + stage.dir_vec("toward") * 0.03
	var tgt := h.centre()
	for k in 4:
		fly("curl", mouth, tgt + Vector3(randf_range(-0.1, 0.1), randf_range(-0.15, 0.25), 0.1), 0.09, 0.45 + 0.08 * k, randf_range(-0.05, 0.08), 2.0, 1.6)
	var tap := int(stage.build_ctx.get("tap", 1))
	var taps := int(stage.build_ctx.get("taps", 1))
	var down := face  # downwind
	match kind:
		"straw_fly":
			for k in 6 + 4 * int(tap == taps):
				var p := tgt + Vector3(randf_range(-0.3, 0.3), randf_range(-0.1, 0.3), 0.05)
				fly("straw", p, p + down * randf_range(0.6, 1.4) + Vector3(0, randf_range(0.2, 0.7), randf_range(-0.2, 0.2)), 0.07, randf_range(0.9, 1.4), 0.2, 6.0)
		"wood_wobble":
			if tap == taps:
				for k in 7:
					var p2 := tgt + Vector3(randf_range(-0.3, 0.3), randf_range(-0.1, 0.3), 0.05)
					fly("splinter", p2, p2 + down * randf_range(0.3, 0.8) + Vector3(0, randf_range(0.05, 0.3), 0.1), 0.06, randf_range(0.6, 0.9), 0.25, 7.0)
				for k in 4:
					var p3 := h.global_position + Vector3(randf_range(-0.35, 0.35), 0.03, 0.05)
					fly("steam", p3, p3 + Vector3(0, 0.15, 0), 0.12, 1.0, 0.0, 1.0, 1.8)
		_:
			# brick house holds: the pigs cheer behind it
			for r in ["pig_a", "pig_b", "pig_c"]:
				var a := _a(r)
				if a and a.pop_target > 0.5 and randf() < 0.6:
					a.hop_v = 0.6


## Brick house cutaway: the front wall folds down toward the reader, the kitchen pops up behind it (hearth, fire,
## pot, table) and the brothers are inside; close: the wall folds back up, the kitchen folds away.
func _cutaway(open: bool) -> void:
	var h := stage.set_piece("house")
	if h:
		h.cutaway(open)
	if open:
		get_tree().create_timer(0.8).timeout.connect(_fire_glow.bind(0))
	elif _fire_light:
		_fire_light.visible = false
	var t := 0.25
	for k in stage.sets:
		var sp: SetPiece = stage.sets[k]
		if not str(k).begins_with("k_") and not str(k).begins_with("fire"):
			continue
		if open:
			if str(k).begins_with("fire") and str(k) != "fire":
				continue
			sp.pop_card(t)
			t += 0.12
		else:
			sp.collapse(0.0)
	var spots := {"pig_a": "in_a", "pig_b": "in_b", "pig_c": "in_c"}
	for r in spots:
		var a := _a(r)
		if a == null:
			continue
		if open:
			a.place_at(stage.spot_point(spots[r]))
			stage.clear_inside(a)
			a.pop_s = 0.02
			a.pop_delay = t
			a.pop_target = 1.0
			t += 0.1
		else:
			a.pop_target = 0.02
			a.pop_delay = 0.0


var _fire_light: OmniLight3D


## The fire's glow on the pot and the room (grows with the flame).
func _fire_glow(level: int) -> void:
	var f := stage.set_piece("fire")
	if f == null:
		return
	if _fire_light == null:
		_fire_light = OmniLight3D.new()
		_fire_light.light_color = Color(1.0, 0.62, 0.3)
		_fire_light.shadow_enabled = false
		_fire_light.light_specular = 0.0
		stage.add_child(_fire_light)
	_fire_light.global_position = f.global_position + Vector3(0, 0.12, 0) + stage.dir_vec("toward") * 0.12
	_fire_light.omni_range = 0.6
	_fire_light.light_energy = [0.5, 0.9, 1.3][clampi(level, 0, 2)]
	_fire_light.visible = true


## The room behind the closed front wall: every k_* piece and the small fire stand from the start of the beat
## (hidden by the facade from outside; nothing pops on screen later).
func _room_ready() -> void:
	for k in stage.sets:
		var sp: SetPiece = stage.sets[k]
		if str(k).begins_with("k_") or str(k) == "fire":
			sp.pop_card(0.0)
			for h in sp.all_hinges():
				h.snap(true)
	_fire_glow(0)


func _pigs_to_room() -> void:
	var spots := {"pig_a": "in_a", "pig_b": "in_b", "pig_c": "in_c"}
	for r in spots:
		var a := _a(r)
		if a == null:
			continue
		stage.clear_inside(a)
		a.visible = true
		a.place_at(stage.spot_point(spots[r]))
		a.set_pose("calm" if r != "pig_c" else "brave")


func _pigs_to_windows() -> void:
	var wins := {"pig_c": 0, "pig_a": 1, "pig_b": 1}
	for r in wins:
		if _a(r):
			stage.put_inside(r, "house", wins[r])


func _flame(level: int) -> void:
	_fire_glow(level)
	var names := ["fire", "fire_m", "fire_l"]
	for i in names.size():
		var sp := stage.set_piece(names[i])
		if sp == null:
			continue
		if i == level:
			sp.pop_card(0.0)
			sp.bounce()
		elif i < level and sp.shown > 0:
			sp.band_down(0, 0.15)
	var pot := stage.set_piece("k_pot")
	if pot:
		pot.bounce()
		for k in level + 1:
			var c := pot.global_position + Vector3(randf_range(-0.05, 0.05), pot.height, 0.02)
			fly("steam", c, c + Vector3(randf_range(-0.08, 0.08), 0.2 + 0.1 * level, 0), 0.05 + 0.03 * level, 1.0, 0.0, 0.5, 1.6)


func _chimney_top() -> Vector3:
	var h := stage.set_piece("house")
	if h == null:
		return stage.spot_point("anchor")
	return h.global_position + stage.dir_vec("right") * 0.36 * h.height + Vector3.UP * 1.0 * h.height


## He drops feet first down the flue (behind the roof) into the pot.
func _wolf_drop() -> void:
	var w := _a("wolf")
	var pot := stage.set_piece("k_pot")
	if w == null or pot == null:
		return
	_boil = 0.0  # the steam would hide him
	# down the flue: just in front of the flue card (behind the roof until he is below the eaves), into the pot
	var flue := stage.set_piece("k_flue")
	var top := _chimney_top() + stage.dir_vec("away") * 0.06
	if flue:
		var fp := flue.global_position + stage.dir_vec("toward") * 0.03
		top = Vector3(fp.x, top.y, fp.z)
	var goal := pot.global_position + stage.dir_vec("away") * 0.04
	goal.y = pot.global_position.y
	w.place_at(top)
	w.pop_s = 1.0  # he sank into the chimney top; now he comes down the flue whole
	w.pop_target = 1.0
	w.pop_delay = -1.0
	w.set_pose("falling")
	w.puppet.set_figure("falling", false, true)
	_drop = {"from": top, "to": goal + Vector3(0, pot.height * 0.3, 0), "t": 0.0, "dur": 0.9}


## "앗, 뜨거워!" — he shoots back up the flue and out of the chimney, arcs over and lands far to the left.
func _wolf_launch() -> void:
	var w := _a("wolf")
	if w == null:
		return
	var top := _chimney_top()
	var land := stage.spot_point("wolf_land")
	_launch = {"from": w.global_position, "top": top + Vector3(0, 0.9, 0), "to": land, "t": 0.0, "dur": 1.6}
	w.set_pose("ouch")
	for k in 4:
		fly("soot", top, top + Vector3(randf_range(-0.2, 0.2), randf_range(0.3, 0.6), 0), 0.12, 1.0, 0.0, 1.0, 1.6)


func _step_wolf_flight(dt: float) -> void:
	var w := _a("wolf")
	if w == null:
		return
	if not _drop.is_empty():
		_drop["t"] = float(_drop["t"]) + dt
		var u := clampf(float(_drop["t"]) / float(_drop["dur"]), 0.0, 1.0)
		w.global_position = (_drop["from"] as Vector3).lerp(_drop["to"], u * u)
		if u >= 1.0:
			_drop = {}
	if not _launch.is_empty():
		_launch["t"] = float(_launch["t"]) + dt
		var u2 := clampf(float(_launch["t"]) / float(_launch["dur"]), 0.0, 1.0)
		var p: Vector3
		if u2 < 0.3:
			var v := u2 / 0.3
			p = (_launch["from"] as Vector3).lerp(_launch["top"], v * (2.0 - v))
		else:
			var v2 := (u2 - 0.3) / 0.7
			var a: Vector3 = _launch["top"]
			var b: Vector3 = _launch["to"]
			p = a.lerp(b, v2)
			p.y = lerpf(a.y, b.y, v2 * v2) + sin(v2 * PI) * 0.3
		w.global_position = p
		w.puppet.rotation.z = (u2 * TAU * 1.5) if u2 < 0.95 else 0.0
		if u2 >= 1.0:
			_launch = {}
			w.puppet.rotation.z = 0.0
			w.hop_v = 0.8
			w.place_at(p)
			w.set_pose("run_away", 1)


func step(dt: float) -> void:
	_t += dt
	_step_errands()
	_step_flyers(dt)
	_step_wolf_flight(dt)
	for role in _music.keys():
		var a := _a(str(role))
		if a == null or a.pop_target < 0.5:
			continue
		_music[role] = float(_music[role]) - dt
		if float(_music[role]) <= 0.0:
			_music[role] = randf_range(0.35, 0.6)
			var p := a.global_position + Vector3(0, a.puppet.height * 0.85, 0.04)
			fly("note", p, p + Vector3(randf_range(-0.15, 0.25), randf_range(0.2, 0.35), 0.02), 0.05, 1.3, 0.04, 1.0, 1.0)
			a.hop_v = maxf(a.hop_v, 0.25)  # bouncing to the tune
	if _boil > 0.0:
		var pot := stage.set_piece("k_pot")
		if pot and fmod(_t, 0.35) < dt:
			var c := pot.global_position + Vector3(randf_range(-0.05, 0.05), pot.height * 0.95, 0.03)
			fly("steam", c, c + Vector3(randf_range(-0.06, 0.06), 0.25, 0), 0.07, 1.1, 0.0, 0.5, 1.8)
			if randf() < 0.5:
				pot.bounce()


func enter_beat(_b: Dictionary) -> void:
	_music.clear()


func wiggle(_target: String) -> bool:
	return false


# ------------------------------------------------------------------ printed bits

static func _make_note_texture() -> Texture2D:
	var w := 48
	var h := 64
	var img := Image.create(w, h, false, Image.FORMAT_RGBA8)
	img.fill(Color(0, 0, 0, 0))
	var ink := Color("4a2c1c")
	var rim := Color("fff4dc")
	for pass_i in 2:
		var col := rim if pass_i == 0 else ink
		var g := 3.0 if pass_i == 0 else 0.0
		for y in h:
			for x in w:
				var p := Vector2(x + 0.5, y + 0.5)
				var head := ((p - Vector2(16, 50)) * Vector2(1.0, 1.35)).length() < 10.0 + g
				var stem := x >= 23 - g and x <= 27 + g and y >= 8 - g and y <= 50
				var flag := y >= 8 - g and y <= 20 + g and x >= 25 - g and x <= 25 + (y - 8) * 1.2 + 4 + g
				if head or stem or flag:
					img.set_pixel(x, y, col)
	return ImageTexture.create_from_image(img)


static func _make_curl_texture() -> Texture2D:
	var w := 96
	var h := 64
	var img := Image.create(w, h, false, Image.FORMAT_RGBA8)
	img.fill(Color(0, 0, 0, 0))
	var c := Color("eef3f2")
	var e := Color("9fb5bd")
	# a wind stroke: a line that ends in a curl (printed paper wind, like the sun_wind gust cards)
	for i in 400:
		var u := i / 399.0
		var p: Vector2
		if u < 0.6:
			p = Vector2(6 + u / 0.6 * 60.0, 40 + sin(u * 9.0) * 3.0)
		else:
			var a := (u - 0.6) / 0.4 * TAU * 0.85
			var r := 14.0 * (1.0 - (u - 0.6) / 0.4 * 0.55)
			p = Vector2(66 + sin(a) * r, 26 + cos(a) * r)
		for dy in range(-5, 6):
			for dx in range(-5, 6):
				var d := Vector2(dx, dy).length()
				var q := Vector2i(int(p.x) + dx, int(p.y) + dy)
				if q.x < 0 or q.y < 0 or q.x >= w or q.y >= h:
					continue
				if d < 3.0:
					img.set_pixelv(q, c)
				elif d < 4.6 and img.get_pixelv(q).a < 0.5:
					img.set_pixelv(q, e)
	return ImageTexture.create_from_image(img)
