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
var bands: Array[PopHinge] = []  ## bottom → top (banded houses); empty for a plain card
var band_cards: Array[PaperCard] = []
var hinge: PopHinge  ## plain card
var card: PaperCard
var facade: Node3D  ## parent of the bands / card; rocks for wobble and shiver
var walls: Node3D  ## the wall bands (not the roof): fold forward together for the cutaway, the roof stays up
var roof: Node3D  ## roof band root (banded houses)
var shown := 0  ## bands standing (or 1/0 for a plain card)

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
func setup(entry: Dictionary, scale_: float, banded: bool, n_up: int) -> void:
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
	if st.is_empty():
		var base := Node3D.new()
		walls.add_child(base)
		hinge = PopHinge.new()
		hinge.weight = clampf(height / 0.4, 0.5, 2.5)
		base.add_child(hinge)
		card = PaperCard.new()
		card.texture = load(path)
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
		root.visible = k < n_up
	shown = clampi(n_up, 0, bands.size())


func band_count() -> int:
	return bands.size() if not bands.is_empty() else 1


## Hinges that should rise with the page wave (the parts standing at this stage).
func wave_hinges() -> Array[PopHinge]:
	var out: Array[PopHinge] = []
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
	var t := delay
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
	walls.rotation = Vector3(_cut * PI * 0.5 * 0.97, 0.0, 0.0)
	facade.scale = Vector3(1.0 - 0.02 * _bounce, 1.0 + 0.04 * _bounce, 1.0)
