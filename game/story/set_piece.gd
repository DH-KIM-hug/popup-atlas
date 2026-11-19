class_name SetPiece
extends Node3D
## A story set piece standing on the page (three_pigs and later tales): a card from the shared atlas catalog by id,
## on its own PopHinge so it rises with the page wave. Houses with fold-up stages
## (game/art/atlas/<sheet>/stages/stages.json, tools/atlas/house_stages.py) are built from their bands: band k stands
## on a hinge at the top of band k-1, so a house can be built band by band (bands_up), blown apart (band_down from
## the top), knocked down (collapse), shivered or wobbled, and its whole facade folded down toward the reader
## (cutaway) like the front flap of a pop-up house.
## Story set pieces are separate PaperCards (not in the meadow's CardBatch): a page holds only a handful.

static var _stages_cache := {}

var id := ""
var piece_name := ""
var height := 0.5  ## world height of the whole card
var width := 0.5  ## world width of the whole card (base line)
var bands: Array[PopHinge] = []  ## bottom → top (banded houses); empty for a plain card
var band_cards: Array[PaperCard] = []
var hinge: PopHinge  ## plain card
var card: PaperCard
var facade: Node3D  ## parent of the bands / card; rocks for wobble and shiver
var walls: Node3D  ## the wall bands (not the roof): fold forward together for the cutaway, the roof stays up
var roof: Node3D  ## roof band root (banded houses)
var shown := 0  ## bands standing (or 1/0 for a plain card)
var door_pivot: Node3D  ## door leaf on its side hinge (child of band 0's hinge, so it rises / folds with it)
var _door := 0.0
var _door_v := 0.0
var _door_t := 0.0
var _px_scale := 0.0  ## world per facade px
var _px_w := 0.0
var _base_px := 0.0
var _windows: Array = []
var _wall_x: Array = []
var _roof_px := 0.0
var _full_path := ""
var box: Node3D  ## the house's volume behind the front (back, sides, floor, ceiling); stands while the house is whole
var _window_boxes: Array = []  ## [cx, cy] facade px of the die-cut windows
var _door_box: Dictionary = {}

var _wob := 0.0
var _wob_v := 0.0
var _wob_amp := 0.0
var _shiver := 0.0
var _cut := 0.0  ## 0 standing .. 1 lying forward (cutaway)
var _cut_v := 0.0
var _cut_t := 0.0
var _t := 0.0
var _bounce := 0.0
var _bounce_v := 0.0


static func stages_for(path: String) -> Dictionary:
	# path res://art/atlas/<sheet>/<id>.webp -> res://art/atlas/<sheet>/stages/stages.json
	var dir := path.get_base_dir()
	if not _stages_cache.has(dir):
		var p := dir + "/stages/stages.json"
		var d: Variant = null
		if FileAccess.file_exists(p):
			d = JSON.parse_string(FileAccess.get_file_as_string(p))
		_stages_cache[dir] = d if d is Dictionary else {}
	return _stages_cache[dir]


## entry: catalog entry {id, path, height_units}; scale: story scale on height_units; banded: use fold-up bands.
var flat := false  ## lies flat on the page (a floor): no hinge, it appears / disappears with a small paper bounce
var _flat_s := 0.0
var _flat_v := 0.0
var _flat_t := 0.0


func setup(entry: Dictionary, scale_: float, banded: bool, n_up: int, flat_ := false) -> void:
	flat = flat_
	id = str(entry["id"])
	var path := str(entry["path"])
	if not path.begins_with("res://"):
		path = "res://" + path
	height = float(entry.get("height_units", 0.4)) * scale_
	facade = Node3D.new()
	facade.name = "Facade"
	add_child(facade)
	walls = Node3D.new()
	walls.name = "Walls"
	facade.add_child(walls)
	var st: Dictionary = stages_for(path).get(id, {}) if banded else {}
	if st.is_empty() and flat:
		var fb := Node3D.new()
		fb.name = "Flat"
		fb.rotation.x = -PI * 0.5  # lies back: its bottom edge at the origin, the rest away from the camera
		fb.position.y = 0.003
		walls.add_child(fb)
		card = PaperCard.new()
		card.texture = load(path)
		card.height = height
		card.thickness = 0.004
		card.back_print = false
		fb.add_child(card)
		var ts0 := card.texture.get_size()
		width = height * ts0.x / maxf(ts0.y, 1.0)
		shown = 1 if n_up != 0 else 0
		_flat_t = float(shown)
		_flat_s = _flat_t
		facade.scale = Vector3.ONE * maxf(_flat_s, 0.001)
		facade.visible = shown > 0
		return
	if st.is_empty():
		var base := Node3D.new()
		walls.add_child(base)
		hinge = PopHinge.new()
		hinge.weight = clampf(height / 0.4, 0.5, 2.5)
		base.add_child(hinge)
		card = PaperCard.new()
		card.texture = load(path)
		var ts := card.texture.get_size()
		width = height * ts.x / maxf(ts.y, 1.0)
		card.height = height
		card.thickness = clampf(height * 0.035, 0.01, 0.03)
		card.back_print = false
		hinge.add_child(card)
		shown = 1 if n_up != 0 else 0
		return
	var px: Array = st["px"]
	var top_px := float(st["bands"][st["bands"].size() - 1]["y0"])
	var base_px := float(st["base_y"])
	var s := height / (base_px - top_px)  # world per facade px
	width = float(px[0]) * s
	_px_scale = s
	_px_w = float(px[0])
	_base_px = base_px
	_windows = st.get("windows", [])
	_wall_x = st.get("wall_x", [0, int(px[0])])
	_roof_px = float(st.get("roof_y", top_px))
	_full_path = path
	_window_boxes = st.get("window_boxes", [])
	_door_box = st.get("door", {})
	for k in (st["bands"] as Array).size():
		var b: Dictionary = st["bands"][k]
		var tex: Texture2D = load("res://" + str(b["file"]))
		var iy0 := int(b.get("img_y0", b["y0"]))
		var used := Rect2i(0, 0, int(px[0]), int(b.get("img_y1", b["y1"])) - iy0)
		var img := tex.get_image()
		if img:
			if img.is_compressed():
				img = img.duplicate()
				img.decompress()
			used = img.get_used_rect()
		var root := Node3D.new()
		root.name = "Band%d" % k
		# hinge at the band's straight cut row y1; the card's own origin is the bottom-centre of its opaque rect,
		# which sits at facade row img_y0 + used.end.y (a stepped band's tab around a door reaches above the cut)
		root.position = Vector3(((used.position.x + used.end.x) * 0.5 - float(px[0]) * 0.5) * s,
			(base_px - float(b["y1"])) * s, 0.002 * k)
		if bool(b.get("roof", false)):
			facade.add_child(root)
			roof = root
		else:
			walls.add_child(root)
		var h := PopHinge.new()
		h.weight = clampf(height / 0.5, 0.6, 1.6)
		root.add_child(h)
		var c := PaperCard.new()
		c.texture = tex
		c.height = float(used.size.y) * s
		c.thickness = clampf(height * 0.03, 0.01, 0.026)
		c.position = Vector3(0, (float(b["y1"]) - float(iy0 + used.end.y)) * s, 0)
		h.add_child(c)
		bands.append(h)
		band_cards.append(c)
		if k == 0 and not _door_box.is_empty():
			_add_door(h, root, s)
		root.visible = k < n_up
	shown = clampi(n_up, 0, bands.size())


## The door leaf: its own card, hinged on its left edge, a hair in front of the wall (the wall has the hole).
func _add_door(h: PopHinge, root: Node3D, s: float) -> void:
	var tex: Texture2D = load("res://" + str(_door_box["file"]))
	var x0 := float(_door_box["x0"])
	var x1 := float(_door_box["x1"])
	door_pivot = Node3D.new()
	door_pivot.name = "DoorHinge"
	door_pivot.position = Vector3((x0 - _px_w * 0.5) * s - root.position.x, (_base_px - float(_door_box["y1"])) * s, 0.004)
	h.add_child(door_pivot)
	var c := PaperCard.new()
	c.texture = tex
	c.height = (float(_door_box["y1"]) - float(_door_box["y0"])) * s
	c.thickness = 0.008
	c.position = Vector3((x1 - x0) * 0.5 * s, 0, 0)
	door_pivot.add_child(c)


func has_door() -> bool:
	return door_pivot != null


## Door swings open toward the reader (about its left edge) or shut.
func open_door(open: bool) -> void:
	_door_t = 1.0 if open else 0.0


## Ground point in front of / behind the door (a pig steps through it).
func door_point(front: bool, cam_toward: Vector3) -> Vector3:
	var cx := (float(_door_box.get("x0", _px_w * 0.5)) + float(_door_box.get("x1", _px_w * 0.5))) * 0.5
	var r := global_transform.basis.x.normalized()
	return global_position + r * (cx - _px_w * 0.5) * _px_scale + cam_toward * (0.12 if front else -0.08)


## Where a pig stands behind window i so its face shows in it: [ground point behind the wall, window centre height].
func window_spot(i: int, cam_toward: Vector3) -> Array:
	if _windows.is_empty():
		return [global_position - cam_toward * 0.08, height * 0.4]
	var w: Array = _windows[clampi(i, 0, _windows.size() - 1)]
	var r := global_transform.basis.x.normalized()
	var p := global_position + r * (float(w[0]) - _px_w * 0.5) * _px_scale - cam_toward * 0.07
	return [p, (_base_px - float(w[1])) * _px_scale]


var _glow: Array[MeshInstance3D] = []
var _glow_on := 0.0
var _glow_t := 0.0
var _backs: Array[MeshInstance3D] = []


## Warm interior behind each die-cut window: a soft orange plane a little behind the wall (firelight, flickers), or a
## darker warm plane when someone peeks (so a face reads against it). mode: "fire" | "dim" | "off".
func window_backs(mode: String) -> void:
	if _windows.is_empty() or (mode != "off" and shown < band_count() and not bands.is_empty() and shown < 2):
		return
	if _backs.is_empty():
		for i in _windows.size():
			var w: Array = _windows[i]
			var m := MeshInstance3D.new()
			var q := QuadMesh.new()
			q.size = Vector2(70.0, 70.0) * _px_scale
			m.mesh = q
			var mat := StandardMaterial3D.new()
			mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
			m.material_override = mat
			m.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			# a hand's breadth behind the wall, centred on the window (moves with the house's band 0... the walls node)
			m.position = Vector3((float(w[0]) - _px_w * 0.5) * _px_scale, (_base_px - float(w[1])) * _px_scale, -0.11)
			walls.add_child(m)
			_backs.append(m)
	_glow_on = 1.0 if mode == "fire" else (0.0 if mode == "dim" else -1.0)
	for m in _backs:
		m.visible = mode != "off"
		(m.material_override as StandardMaterial3D).albedo_color = Color(0.36, 0.2, 0.12) if mode == "dim" else Color(1.0, 0.62, 0.3)


## Window i's opening in world terms: [bottom-centre point on the wall plane, width, height] (facade px box).
func window_box(i: int) -> Array:
	var boxes: Array = _window_boxes
	if boxes.is_empty():
		return []
	var b: Array = boxes[clampi(i, 0, boxes.size() - 1)]
	var r := global_transform.basis.x.normalized()
	var cx := (float(b[0]) + float(b[2])) * 0.5
	var p := global_position + r * (cx - _px_w * 0.5) * _px_scale + Vector3(0, (_base_px - float(b[3])) * _px_scale, 0)
	return [p, (float(b[2]) - float(b[0])) * _px_scale, (float(b[3]) - float(b[1])) * _px_scale]


## A house is a front with a body behind it (user 2026-11-19: "문열때보면 뒷편이 없는곳으로 가다보니 이상한디?"): an
## interior back wall (its own finish), two side walls in the house's outside material, a plank floor, a ceiling under
## the roof and a copy of the front facing backwards (a closed volume from the side). cfg {depth, side, inner, floor}:
## card paths. Hidden while the house is not whole (being built, blown away).
func add_box(cfg: Dictionary) -> void:
	if bands.is_empty() or box != null:
		return
	var s := _px_scale
	var d := float(cfg.get("depth", 0.45))
	var x0 := (float(_wall_x[0]) - _px_w * 0.5) * s
	var x1 := (float(_wall_x[1]) - _px_w * 0.5) * s
	var wall_h := (_base_px - _roof_px) * s
	box = Node3D.new()
	box.name = "Box"
	add_child(box)
	var mk := func(path: String, h: float, w: float, pos: Vector3, yaw: float, back_print := false) -> PaperCard:
		var c := PaperCard.new()
		c.texture = load(path)
		c.height = h
		c.thickness = 0.008
		c.back_print = back_print
		var ts := c.texture.get_size()
		var nat_w := h * ts.x / maxf(ts.y, 1.0)
		var n := Node3D.new()
		n.position = pos
		n.rotation.y = yaw
		n.scale = Vector3(w / maxf(nat_w, 0.001), 1, 1)
		box.add_child(n)
		n.add_child(c)
		return c
	var side := str(cfg.get("side", ""))
	if side != "":
		mk.call(side, wall_h, d, Vector3(x0 - 0.006, 0, -d * 0.5), -PI * 0.5)
		mk.call(side, wall_h, d, Vector3(x1 + 0.006, 0, -d * 0.5), PI * 0.5)
	var inner := str(cfg.get("inner", ""))
	if inner != "":
		mk.call(inner, wall_h * float(cfg.get("inner_h", 1.0)), x1 - x0, Vector3((x0 + x1) * 0.5, 0, -d + 0.012), 0.0)
	# the back of the house: the front's own print turned round (a closed volume seen from the side / behind)
	mk.call(_full_path, height, width, Vector3(0, 0, -d - 0.004), PI)
	var floor := str(cfg.get("floor", ""))
	if floor != "":
		for k in 2:  # floor and ceiling: planks lying flat
			var c: PaperCard = mk.call(floor, d, x1 - x0, Vector3((x0 + x1) * 0.5, 0.004 + k * (wall_h - 0.01), 0), 0.0)
			c.get_parent().rotation.x = -PI * 0.5
			c.get_parent().scale = Vector3((x1 - x0) / maxf(d * c.texture.get_size().x / maxf(c.texture.get_size().y, 1.0), 0.001), 1, 1)
	box.visible = shown >= band_count()


func band_count() -> int:
	return bands.size() if not bands.is_empty() else 1


## Hinges that should rise with the page wave (the parts standing at this stage).
func wave_hinges() -> Array[PopHinge]:
	var out: Array[PopHinge] = []
	if flat:
		return out
	if hinge:
		if shown > 0:
			out.append(hinge)
		return out
	for k in shown:
		out.append(bands[k])
	return out


func all_hinges() -> Array[PopHinge]:
	var out: Array[PopHinge] = []
	if hinge:
		out.append(hinge)
	out.append_array(bands)
	return out


## Raise bands up to n (one after another, `gap` s apart). Returns the time the last one starts.
func bands_up(n: int, delay := 0.0, gap := 0.18) -> float:
	if flat:
		if n > 0:
			_flat_t = 1.0
			shown = 1
			facade.visible = true
		return delay
	if hinge:
		if n > 0 and shown == 0:
			hinge.get_parent().visible = true
			hinge.pop_up(delay)
			shown = 1
		return delay
	var t := delay
	for k in range(shown, mini(n, bands.size())):
		(bands[k].get_parent() as Node3D).visible = true
		bands[k].pop_up(t)
		t += gap
	shown = maxi(shown, mini(n, bands.size()))
	return t


## Fold band k down (blown off) and hide it once flat.
func band_down(k: int, delay := 0.0) -> void:
	if flat:
		_flat_t = 0.0
		shown = 0
		return
	if hinge:
		hinge.fold_down(delay)
		_hide_later(hinge, delay + 0.7)
		shown = 0
		return
	if k < 0 or k >= bands.size():
		return
	bands[k].fold_down(delay)
	_hide_later(bands[k], delay + 0.75)
	shown = mini(shown, k)


func _hide_later(h: PopHinge, t: float) -> void:
	var tm := get_tree().create_timer(t)
	tm.timeout.connect(func():
		if is_instance_valid(h) and not h.is_up:
			(h.get_parent() as Node3D).visible = false)


## Everything falls: top band first, staggered.
func collapse(delay := 0.0) -> float:
	window_backs("off")
	var t := delay
	if flat:
		band_down(0)
		return t
	if hinge:
		band_down(0, t)
		return t + 0.6
	for k in range(bands.size() - 1, -1, -1):
		band_down(k, t)
		t += 0.12
	return t + 0.6


func pop_card(delay := 0.0) -> void:
	bands_up(band_count(), delay)


func wobble(amount: float) -> void:
	_wob_amp = maxf(_wob_amp, amount)
	_wob_v += amount * 6.0


func shiver(sec: float) -> void:
	_shiver = maxf(_shiver, sec)


func bounce() -> void:
	_bounce_v = 1.4


## Facade folds down toward the reader (open) or back up (close).
func cutaway(open: bool) -> void:
	_cut_t = 1.0 if open else 0.0


func centre() -> Vector3:
	var hh := height
	if not bands.is_empty() and shown < bands.size():
		hh = height * float(shown) / float(bands.size()) * 0.8 + 0.06
	return global_position + Vector3(0, hh * 0.5, 0)


func _process(dt: float) -> void:
	dt = PaperSpring.frame_dt(dt)
	if dt <= 0.0 or facade == null:
		return
	_t += dt
	if box:
		box.visible = shown >= bands.size()
	if flat:
		var fs := PaperSpring.step(_flat_s, _flat_v, _flat_t, 8.0, 0.6, dt)
		_flat_s = fs.x
		_flat_v = fs.y
		facade.scale = Vector3.ONE * maxf(_flat_s, 0.001)
		facade.visible = _flat_s > 0.02
		return
	# wobble: an underdamped rock about the base (wood house: 흔들흔들)
	var w := TAU * 2.2
	_wob_v += (-w * w * _wob - 2.0 * 0.12 * w * _wob_v) * dt
	_wob += _wob_v * dt
	_wob = clampf(_wob, -0.35, 0.35)
	_wob_amp = maxf(0.0, _wob_amp - dt * 0.2)
	var rz := _wob * 0.25
	var ry := 0.0
	if _shiver > 0.0:
		_shiver -= dt
		rz += deg_to_rad(0.9) * sin(_t * TAU * 11.0) * clampf(_shiver * 2.0, 0.0, 1.0)
		ry += deg_to_rad(0.6) * sin(_t * TAU * 7.0) * clampf(_shiver * 2.0, 0.0, 1.0)
	var bs := PaperSpring.step(_bounce, _bounce_v, 0.0, 14.0, 0.3, dt)
	_bounce = bs.x
	_bounce_v = bs.y
	# cutaway: eased spring to lying forward (rotation about the base line, top toward the camera)
	var cs := PaperSpring.step(_cut, _cut_v, _cut_t, 4.2, 0.8, dt)
	_cut = cs.x
	_cut_v = cs.y
	facade.rotation = Vector3(0.0, ry, rz)
	if _glow_on > 0.0 and not _backs.is_empty():
		_glow_t += dt
		var f := 0.85 + 0.1 * sin(_glow_t * 7.3) + 0.05 * sin(_glow_t * 17.0 + 1.0)
		for m in _backs:
			(m.material_override as StandardMaterial3D).albedo_color = Color(1.0, 0.62, 0.3) * f
	if door_pivot:
		var ds := PaperSpring.step(_door, _door_v, _door_t, 9.0, 0.55, dt)
		_door = ds.x
		_door_v = ds.y
		door_pivot.rotation.y = -1.75 * _door
	walls.rotation = Vector3(_cut * PI * 0.5 * 0.97, 0.0, 0.0)
	facade.scale = Vector3(1.0 - 0.02 * _bounce, 1.0 + 0.04 * _bounce, 1.0)
