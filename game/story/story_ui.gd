class_name StoryUI
extends CanvasLayer
## Paper chrome for the story (component E): book cover, page turn, caption strip (optional Korean subtitles),
## page tab, tap pointer + ripples, subtitle toggle, ending card with "다시 보기".
## Everything is plain paper: cream stock, brown ink, soft shadow. Touch targets >= 88 px.

signal cover_tapped
signal replay_pressed
signal other_pressed  ## "다른 동화": back to the bookshelf table
signal subtitles_toggled(on: bool)

const FONT_PATH := "res://story/fonts/PretendardVariable.woff2"
const INK := Color("3b2a1c")
const PAPER := Color("f4ead3")
const PAPER_EDGE := Color("b89a6a")
const SPEAKERS_SW := {"sun": ["해님", Color("e08a2c")], "wind": ["바람", Color("5f8fb8")], "man": ["나그네", Color("a8432f")]}
## Speaker chips: name, colour (+ face cast id, script.json ui.speakers {sp: [name, colour, cast id]}). Default sun_wind.
var SPEAKERS: Dictionary = SPEAKERS_SW.duplicate()
var _speaker_faces := {}  ## speaker -> cast id (ui.speakers)
var _cover_cfg: Dictionary = {}  ## ui.cover: the 3D book (CoverBook config)
var _end_pics: HBoxContainer


## Tale-specific chrome from script.json `ui`: cover / end card pictures ([cast id, size] from the cast catalog) and
## speaker chips. Without `ui` the sun_wind chrome stays as it was.
func configure(ui_cfg: Dictionary) -> void:
	if ui_cfg.has("speakers"):
		SPEAKERS = {}
		for sp in ui_cfg["speakers"]:
			var e: Array = ui_cfg["speakers"][sp]
			SPEAKERS[sp] = [str(e[0]), Color(str(e[1]))]
			if e.size() > 2:
				_speaker_faces[sp] = str(e[2])
	if ui_cfg.get("cover") is Dictionary:
		_cover_cfg = ui_cfg["cover"]
	for pair in [[_end_pics, "end"]]:
		var box: HBoxContainer = pair[0]
		if box == null or not ui_cfg.has(pair[1]) or not ui_cfg[pair[1]] is Array:
			continue
		for c in box.get_children():
			c.queue_free()
		for e: Array in ui_cfg[pair[1]]:
			var tr := TextureRect.new()
			tr.texture = CastSkins.by_id(str(e[0]))
			tr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
			tr.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
			tr.custom_minimum_size = Vector2(float(e[1]), float(e[1]))
			tr.mouse_filter = Control.MOUSE_FILTER_IGNORE
			box.add_child(tr)

var subtitles := true:
	set(v):
		subtitles = v
		if _caption:
			_caption.visible = v and _caption_on
		if _subs_btn:
			_subs_btn.text = "자막 켜짐" if v else "자막 꺼짐"
			_subs_btn.modulate = Color.WHITE if v else Color(1, 1, 1, 0.75)
var page_turn: PageTurn
var pointer_source: Callable  ## () -> Vector3(x, y, radius): target circle to point at; x < -500 = hidden
var hold_progress := -1.0  ## 0..1 fill ring on the pointer while blowing, < 0 hidden

var _root: Control
var _font: Font
var _font_bold: Font
var _cover: Control
var _book: CoverBook
var _caption: PanelContainer
var _caption_on := false
var _cap_text: RichTextLabel
var _chip: Label
var _chip_box: PanelContainer
var _tab: PanelContainer
var _tab_label: Label
var _subs_btn: Button
var _end: Control
var _end_card: PanelContainer
var _overlay: Control  ## pointer + ripples (drawn)
var _ripples: Array = []  ## [pos, age]
var _t := 0.0
var _tab_t := -1.0
var _cap_fade := 0.0
var _cap_alpha := 0.0
var _end_t := -1.0
var _chip_icon: TextureRect
var _choices: Control
var _choice_cards: Dictionary = {}  ## target -> Control
var _choice_t := -1.0
var _choice_shake: Dictionary = {}  ## target -> seconds left
var _choice_glow := ""
var _flash: Control
var _flash_cards: Dictionary = {}  ## side -> [Control, age]
var _sparks: Array = []  ## [pos, age]


func _ready() -> void:
	layer = 20
	_font = load(FONT_PATH) if ResourceLoader.exists(FONT_PATH) else ThemeDB.fallback_font
	_font_bold = _weighted(650)
	_font = _weighted(520)
	_root = Control.new()
	_root.name = "Root"
	_root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_root.set_anchors_preset(Control.PRESET_FULL_RECT)
	var th := Theme.new()
	th.default_font = _font
	th.default_font_size = 30
	_root.theme = th
	add_child(_root)
	_build_cover()
	page_turn = PageTurn.new()
	page_turn.name = "PageTurn"
	_root.add_child(page_turn)
	_build_caption()
	_build_tab()
	_overlay = Control.new()
	_overlay.name = "Pointer"
	_overlay.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_overlay.set_anchors_preset(Control.PRESET_FULL_RECT)
	_overlay.draw.connect(_draw_overlay)
	_root.add_child(_overlay)
	_build_chrome()
	_build_end()


func _weighted(w: int) -> Font:
	var base: Font = load(FONT_PATH) if ResourceLoader.exists(FONT_PATH) else ThemeDB.fallback_font
	var fv := FontVariation.new()
	fv.base_font = base
	var ts := TextServerManager.get_primary_interface()
	fv.variation_opentype = {ts.name_to_tag("weight"): w}
	return fv


func _paper_box(bg := PAPER, edge := PAPER_EDGE, radius := 10, shadow := 8) -> StyleBoxFlat:
	var sb := StyleBoxFlat.new()
	sb.bg_color = bg
	sb.border_color = edge
	sb.set_border_width_all(2)
	sb.set_corner_radius_all(radius)
	sb.shadow_color = Color(0.1, 0.06, 0.02, 0.3)
	sb.shadow_size = shadow
	sb.shadow_offset = Vector2(0, 4)
	sb.content_margin_left = 30
	sb.content_margin_right = 30
	sb.content_margin_top = 14
	sb.content_margin_bottom = 16
	return sb


func _label(text: String, size: int, color := INK, bold := false) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_override("font", _font_bold if bold else _font)
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", color)
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return l


# ------------------------------------------------------------------ cover

func _build_cover() -> void:
	_cover = Control.new()
	_cover.name = "Cover"
	_cover.set_anchors_preset(Control.PRESET_FULL_RECT)
	_cover.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_cover.visible = false
	_root.add_child(_cover)


## The tale's book lying closed on the table (CoverBook, built on first show from ui.cover).
func show_cover(title: String) -> void:
	_set_tab("")
	if _book and not _book.is_closed():  # an end book still open: start fresh (a closed one carries over on replay)
		_book.queue_free()
		_book = null
	if _book == null:
		_book = CoverBook.new()
		_book.name = "Book"
		_cover.add_child(_book)
		_book.build(_cover_cfg, title)
	elif _book.is_closed():
		_book.idle()
	_cover.visible = true


## Tap: the board swings open and the camera pushes into the title page (await cover_opening() == false).
func open_cover() -> void:
	if _book:
		_book.open()


func cover_opening() -> bool:
	return _book != null and _book.is_animating()


func hide_cover() -> void:
	_cover.visible = false
	if _book:
		_book.queue_free()
		_book = null


func cover_visible() -> bool:
	return _cover.visible


func has_book() -> bool:
	return not _cover_cfg.is_empty()


## The end: the same book lies open on its title page (under a page turn from the folded last spread), then closes.
## Returns false when the tale has no book config (the old end card only).
func show_end_book(title: String, hidden := false) -> bool:
	if _cover_cfg.is_empty():
		return false
	if _book:
		_book.queue_free()
	_book = CoverBook.new()
	_book.name = "Book"
	_cover.add_child(_book)
	_book.build(_cover_cfg, title)
	_book.set_open()
	_cover.visible = not hidden  # hidden: the page turn draws its live view right of the fold until it lands
	return true


func book_texture() -> Texture2D:
	return _book.vp.get_texture() if _book else null


func show_book() -> void:
	_cover.visible = _book != null


func close_book(shift := 0.0) -> void:
	if _book:
		_book.close(shift)


func turn_over_book() -> void:
	if _book:
		_book.turn_over()


func book_animating() -> bool:
	return _book != null and _book.is_animating()


# ------------------------------------------------------------------ caption

func _build_caption() -> void:
	_caption = PanelContainer.new()
	_caption.name = "Caption"
	var sb := _paper_box(Color(PAPER, 0.97))
	_caption.add_theme_stylebox_override("panel", sb)
	_caption.anchor_left = 0.12
	_caption.anchor_right = 0.88
	_caption.anchor_top = 1.0
	_caption.anchor_bottom = 1.0
	_caption.offset_top = -170
	_caption.offset_bottom = -26
	_caption.grow_vertical = Control.GROW_DIRECTION_BEGIN
	_caption.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_caption.visible = false
	_root.add_child(_caption)
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", 18)
	h.alignment = BoxContainer.ALIGNMENT_CENTER
	h.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_caption.add_child(h)
	_chip_box = PanelContainer.new()
	var cb := StyleBoxFlat.new()
	cb.set_corner_radius_all(40)
	cb.content_margin_left = 8
	cb.content_margin_right = 20
	cb.content_margin_top = 4
	cb.content_margin_bottom = 4
	_chip_box.add_theme_stylebox_override("panel", cb)
	_chip_box.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	_chip_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	h.add_child(_chip_box)
	var ch := HBoxContainer.new()
	ch.add_theme_constant_override("separation", 8)
	ch.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_chip_box.add_child(ch)
	_chip_icon = TextureRect.new()
	_chip_icon.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_chip_icon.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	_chip_icon.custom_minimum_size = Vector2(72, 72)
	_chip_icon.mouse_filter = Control.MOUSE_FILTER_IGNORE
	ch.add_child(_chip_icon)
	_chip = _label("", 32, Color("fffaf0"), true)
	ch.add_child(_chip)
	_cap_text = RichTextLabel.new()
	_cap_text.bbcode_enabled = true
	_cap_text.fit_content = true
	_cap_text.scroll_active = false
	_cap_text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_cap_text.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_cap_text.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	_cap_text.add_theme_font_override("normal_font", _font)
	_cap_text.add_theme_font_override("bold_font", _font_bold)
	_cap_text.add_theme_font_size_override("normal_font_size", 48)
	_cap_text.add_theme_font_size_override("bold_font_size", 48)
	_cap_text.add_theme_color_override("default_color", INK)
	_cap_text.mouse_filter = Control.MOUSE_FILTER_IGNORE
	h.add_child(_cap_text)


## Show a script line; `seg_i` = the seg being spoken (its speaker gets the chip, its text the ink).
func show_line(line: Dictionary, seg_i := 0) -> void:
	var segs: Array = line.get("segs", [])
	var parts := PackedStringArray()
	for i in segs.size():
		var s: Dictionary = segs[i]
		var t := str(s["text"])
		if str(s["speaker"]) != "nar":
			t = "“" + t + "”"
		# r2: one solid ink colour (critic 2: the dimmed half-line was low contrast); spoken words in bold.
		parts.append("[b]" + t + "[/b]" if str(s["speaker"]) != "nar" else t)
	_cap_text.text = "[center]" + keep_all(" ".join(parts)) + "[/center]"
	var sp := str((segs[seg_i] as Dictionary)["speaker"]) if seg_i < segs.size() else "nar"
	if SPEAKERS.has(sp):
		_chip.text = SPEAKERS[sp][0]
		(_chip_box.get_theme_stylebox("panel") as StyleBoxFlat).bg_color = SPEAKERS[sp][1]
		_chip_icon.texture = _face(sp)
		_chip_box.visible = true
	else:
		_chip_box.visible = false
	_caption_on = true
	_cap_fade = -1.0
	_caption.visible = subtitles


func hide_line(delay := 0.0) -> void:
	if delay <= 0.0:
		_caption_on = false
		_caption.visible = false
		_cap_alpha = 0.0
	else:
		_cap_fade = delay


# ------------------------------------------------------------------ page tab + chrome

func _build_tab() -> void:
	_tab = PanelContainer.new()
	_tab.name = "PageTab"
	var sb := _paper_box(Color(PAPER, 0.95), PAPER_EDGE, 8, 5)
	sb.content_margin_top = 8
	sb.content_margin_bottom = 10
	sb.content_margin_left = 22
	sb.content_margin_right = 22
	_tab.add_theme_stylebox_override("panel", sb)
	_tab.position = Vector2(28, 24)
	_tab.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_tab.visible = false
	_root.add_child(_tab)
	_tab_label = _label("", 28, INK, true)
	_tab.add_child(_tab_label)


func _set_tab(text: String) -> void:
	_tab.visible = text != ""
	_tab_label.text = text
	_tab_t = 0.0 if text != "" else -1.0


func show_page_title(text: String) -> void:
	_set_tab(text)


func _build_chrome() -> void:
	_subs_btn = Button.new()
	_subs_btn.name = "Subtitles"
	_subs_btn.text = "자막 켜짐"
	_subs_btn.focus_mode = Control.FOCUS_NONE
	_subs_btn.add_theme_font_override("font", _font_bold)
	_subs_btn.add_theme_font_size_override("font_size", 26)
	for st in ["normal", "hover", "pressed", "focus"]:
		var sb := _paper_box(Color(PAPER, 0.92) if st != "pressed" else Color("e6d6b4"), PAPER_EDGE, 8, 4)
		sb.content_margin_top = 10
		sb.content_margin_bottom = 12
		_subs_btn.add_theme_stylebox_override(st, sb)
	for st in ["font_color", "font_hover_color", "font_pressed_color", "font_focus_color"]:
		_subs_btn.add_theme_color_override(st, INK)
	_subs_btn.anchor_left = 1.0
	_subs_btn.anchor_right = 1.0
	_subs_btn.offset_left = -210
	_subs_btn.offset_right = -28
	_subs_btn.offset_top = 24
	_subs_btn.offset_bottom = 88
	_subs_btn.pressed.connect(func():
		subtitles = not subtitles
		subtitles_toggled.emit(subtitles))
	_root.add_child(_subs_btn)


# ------------------------------------------------------------------ ending

func _build_end() -> void:
	_end = Control.new()
	_end.name = "End"
	_end.set_anchors_preset(Control.PRESET_FULL_RECT)
	_end.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_end.visible = false
	_root.add_child(_end)
	_end_card = PanelContainer.new()
	var sb := _paper_box(Color(PAPER, 0.98), PAPER_EDGE, 14, 16)
	sb.content_margin_left = 60
	sb.content_margin_right = 60
	sb.content_margin_top = 34
	sb.content_margin_bottom = 40
	_end_card.add_theme_stylebox_override("panel", sb)
	_end_card.anchor_left = 0.24
	_end_card.anchor_right = 0.76
	_end_card.anchor_top = 0.1
	_end_card.anchor_bottom = 0.1
	_end_card.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_end.add_child(_end_card)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 22)
	v.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_end_card.add_child(v)
	# r2: no moral text on the card (said once at the quiz, critic 2); the sun and wind side by side, friends.
	var pics := HBoxContainer.new()
	pics.alignment = BoxContainer.ALIGNMENT_CENTER
	pics.add_theme_constant_override("separation", 10)
	pics.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_end_pics = pics
	for c in [["sun", "beaming", 250], ["wind", "default", 230]]:
		var tr := TextureRect.new()
		tr.texture = CastSkins.texture(c[0], c[1])
		tr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		tr.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		tr.custom_minimum_size = Vector2(c[2], c[2])
		tr.mouse_filter = Control.MOUSE_FILTER_IGNORE
		pics.add_child(tr)
	v.add_child(pics)
	var fin := _label("끝", 92, Color("a8432f"), true)
	fin.name = "Fin"
	v.add_child(fin)
	var moral := _label("", 38, INK, true)
	moral.name = "Moral"
	moral.visible = false
	v.add_child(moral)
	var b := Button.new()
	b.name = "Replay"
	b.text = "다시 보기"
	b.focus_mode = Control.FOCUS_NONE
	b.custom_minimum_size = Vector2(300, 96)
	b.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	b.add_theme_font_override("font", _font_bold)
	b.add_theme_font_size_override("font_size", 38)
	for st in ["normal", "hover", "pressed", "focus"]:
		var bs := _paper_box(Color("b4553c") if st != "pressed" else Color("97412e"), Color("7a3424"), 14, 6)
		b.add_theme_stylebox_override(st, bs)
	for st in ["font_color", "font_hover_color", "font_pressed_color", "font_focus_color"]:
		b.add_theme_color_override(st, Color("fff3d6"))
	b.pressed.connect(func(): replay_pressed.emit())
	v.add_child(b)
	var o := b.duplicate() as Button
	o.name = "Other"
	o.text = "다른 동화"
	for st in ["normal", "hover", "pressed", "focus"]:
		var bs := _paper_box(Color("5f7f6a") if st != "pressed" else Color("4d6a57"), Color("3b5444"), 14, 6)
		o.add_theme_stylebox_override(st, bs)
	o.pressed.connect(func(): other_pressed.emit())
	v.add_child(o)


func show_end(moral: String) -> void:
	(_end_card.find_child("Moral", true, false) as Label).text = moral
	_end.visible = true
	_end_t = 0.0
	_end_card.modulate.a = 0.0
	var book := _book != null and _cover.visible
	# with the closed book on the table the card is a slim paper tag at the right (the book shows the characters)
	_end_pics.visible = not book
	(_end_card.find_child("Fin", true, false) as Control).visible = not book  # "끝" is on the back cover
	_end_card.anchor_left = 0.7 if book else 0.24
	_end_card.anchor_right = 0.965 if book else 0.76
	var sb := _end_card.get_theme_stylebox("panel") as StyleBoxFlat
	if sb:
		# beside the book the card itself vanishes: the two buttons are paper tabs lying on the table
		sb.content_margin_left = 26 if book else 60
		sb.content_margin_right = 26 if book else 60
		sb.draw_center = not book
		sb.set_border_width_all(0 if book else 2)
		sb.shadow_size = 0 if book else 16
	_end_card.anchor_top = 0.3 if book else 0.1
	_end_card.anchor_bottom = _end_card.anchor_top
	_end_card.offset_left = 0
	_end_card.offset_right = 0
	_end_card.set_meta("y_anchor", _end_card.anchor_top)


func hide_end() -> void:
	_end.visible = false
	_end_t = -1.0
	if _book and not _book.is_closed():
		hide_cover()


func other_button_pos() -> Vector2:
	return (_end_card.find_child("Other", true, false) as Control).get_global_rect().get_center()


func end_button_pos() -> Vector2:
	var b := _end_card.find_child("Replay", true, false) as Control
	return b.get_global_rect().get_center()


# ------------------------------------------------------------------ pointer + ripples

func ripple(p: Vector2) -> void:
	_ripples.append([p, 0.0])


func step(dt: float) -> void:
	_t += dt
	page_turn.step(dt)
	for r in _ripples:
		r[1] += dt
	_ripples = _ripples.filter(func(r): return r[1] < 0.6)
	if _book:
		_book.step(dt)
	if _tab_t >= 0.0:
		_tab_t += dt
		var u := clampf(_tab_t / 0.35, 0.0, 1.0)
		_tab.position.y = lerpf(-80.0, 24.0, 1.0 - pow(1.0 - u, 3.0))
	if _cap_fade > 0.0:
		_cap_fade -= dt
		if _cap_fade <= 0.0:
			hide_line()
	if _end_t >= 0.0:
		_end_t += dt
		var u2 := clampf(_end_t / 0.5, 0.0, 1.0)
		_end_card.modulate.a = u2
		var ya: float = _end_card.get_meta("y_anchor", 0.1)
		_end_card.position.y = lerpf(_end.size.y * ya + 60.0, _end.size.y * ya, 1.0 - pow(1.0 - u2, 3.0))
	if _choice_t >= 0.0:
		_choice_t += dt
		for k in _choice_cards:
			var cc: Control = _choice_cards[k]
			var u3 := clampf((_choice_t - (0.0 if k == "sun" else 0.15)) / 0.45, 0.0, 1.0)
			var bounce := sin(_t * 4.0 + (0.0 if k == "sun" else 1.6)) * 8.0
			var shake := 0.0
			if _choice_shake.has(k):
				_choice_shake[k] -= dt
				shake = sin(_t * 40.0) * 14.0 * clampf(_choice_shake[k], 0.0, 1.0)
				if _choice_shake[k] <= 0.0:
					_choice_shake.erase(k)
			cc.scale = Vector2.ONE * (1.0 - pow(1.0 - u3, 3.0)) * (1.12 if _choice_glow == k else 1.0)
			cc.rotation = deg_to_rad(shake * 0.3 + bounce * 0.25)
			cc.position.y = cc.get_meta("y0", cc.position.y) + bounce
	for side in _flash_cards:
		var f: Array = _flash_cards[side]
		f[1] += dt
		var u4 := clampf(f[1] / 0.4, 0.0, 1.0)
		(f[0] as Control).scale = Vector2.ONE * (1.0 - pow(1.0 - u4, 3.0))
	for sp in _sparks:
		sp[1] += dt
	_sparks = _sparks.filter(func(sp): return sp[1] < 1.2)
	_overlay.queue_redraw()


func _draw_overlay() -> void:
	var ink := Color(0.25, 0.16, 0.08, 0.85)
	var cream := Color(1.0, 0.97, 0.88, 0.95)
	if pointer_source.is_valid():
		var pv: Vector3 = pointer_source.call()
		var p := Vector2(pv.x, pv.y)
		if p.x > -500.0:
			# r2: the ring goes AROUND the target (outside its face, critic 1) and the finger tab sits below it.
			var k := 0.5 + 0.5 * sin(_t * 5.0)
			var r := maxf(pv.z, 60.0) + 12.0 + 8.0 * k
			_overlay.draw_arc(p, r + 3.0, 0, TAU, 48, ink, 7.0, true)
			_overlay.draw_arc(p, r, 0, TAU, 48, cream, 5.0, true)
			if hold_progress >= 0.0:
				_overlay.draw_arc(p, r + 14.0, -PI * 0.5, -PI * 0.5 + TAU * clampf(hold_progress, 0.0, 1.0), 48,
					Color("e08a2c"), 9.0, true)
			# A small paper finger tab pointing at the target from below-right.
			var tip := p + Vector2(0, r + 8.0) + Vector2(0, 10) * k
			var poly := PackedVector2Array([tip, tip + Vector2(26, 46), tip + Vector2(-26, 46)])
			_overlay.draw_colored_polygon(poly, cream)
			_overlay.draw_polyline(PackedVector2Array([poly[0], poly[1], poly[2], poly[0]]), ink, 3.0, true)
	for sp in _sparks:
		var a2: float = sp[1] / 1.2
		for i in 10:
			var ang := TAU * i / 10.0 + a2
			var q: Vector2 = sp[0] + Vector2(cos(ang), sin(ang)) * (60.0 + 160.0 * sqrt(a2))
			var sz := 16.0 * (1.0 - a2) + 4.0
			_overlay.draw_colored_polygon(PackedVector2Array([q + Vector2(0, -sz), q + Vector2(sz * 0.35, 0), q + Vector2(0, sz), q + Vector2(-sz * 0.35, 0)]), Color(1.0, 0.86, 0.4, 1.0 - a2))
			_overlay.draw_colored_polygon(PackedVector2Array([q + Vector2(-sz, 0), q + Vector2(0, sz * 0.35), q + Vector2(sz, 0), q + Vector2(0, -sz * 0.35)]), Color(1.0, 0.95, 0.75, 1.0 - a2))
	for rp in _ripples:
		var a: float = rp[1] / 0.6
		_overlay.draw_arc(rp[0], 20.0 + 70.0 * a, 0, TAU, 40, Color(1, 0.97, 0.88, 0.9 * (1.0 - a)), 6.0 * (1.0 - a) + 1.0, true)


# ------------------------------------------------------------------ r2: faces, quiz choice cards, flashbacks, sparkles

func _face(sp: String) -> Texture2D:
	if _speaker_faces.has(sp):
		var t2 := CastSkins.by_id(str(_speaker_faces[sp]))
		if t2 == null:
			return null
		var at2 := AtlasTexture.new()  # head only: the top third of the figure
		at2.atlas = t2
		var sz2 := t2.get_size()
		at2.region = Rect2(sz2.x * 0.1, 0, sz2.x * 0.8, sz2.y * 0.4)
		return at2
	match sp:
		"sun":
			return CastSkins.texture("sun")
		"wind":
			return CastSkins.texture("wind")
		"man":
			var t := CastSkins.texture("traveller", "face")
			if t == null:
				return null
			var at := AtlasTexture.new()
			at.atlas = t
			var sz := t.get_size()
			at.region = Rect2(sz.x * 0.18, 0, sz.x * 0.64, sz.y * 0.32)
			return at
	return null


## Two big picture cards to choose from (the quiz), each a paper card with the cast print, bobbing to invite.
func show_choices(targets: Array) -> void:
	hide_choices()
	_choices = Control.new()
	_choices.name = "Choices"
	_choices.set_anchors_preset(Control.PRESET_FULL_RECT)
	_choices.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_root.add_child(_choices)
	_root.move_child(_choices, _overlay.get_index())
	var vs := _root.get_viewport_rect().size
	for i in targets.size():
		var t := str(targets[i])
		var card := PanelContainer.new()
		var sb := _paper_box(Color(PAPER, 0.98), Color("e08a2c") if t == "sun" else Color("5f8fb8"), 24, 14)
		sb.set_border_width_all(7)
		sb.content_margin_left = 18
		sb.content_margin_right = 18
		sb.content_margin_top = 14
		sb.content_margin_bottom = 10
		card.add_theme_stylebox_override("panel", sb)
		card.mouse_filter = Control.MOUSE_FILTER_IGNORE
		card.custom_minimum_size = Vector2(320, 360)
		card.size = Vector2(320, 360)
		card.pivot_offset = Vector2(160, 180)
		var x := vs.x * (0.27 if i == 0 else 0.73) - 160.0
		card.position = Vector2(x, vs.y * 0.42 - 180.0)
		card.set_meta("y0", card.position.y)
		card.scale = Vector2.ZERO
		var v := VBoxContainer.new()
		v.mouse_filter = Control.MOUSE_FILTER_IGNORE
		card.add_child(v)
		var tr := TextureRect.new()
		tr.texture = CastSkins.texture(t)
		tr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
		tr.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
		tr.custom_minimum_size = Vector2(270, 260)
		tr.mouse_filter = Control.MOUSE_FILTER_IGNORE
		v.add_child(tr)
		v.add_child(_label(SPEAKERS[t][0] if SPEAKERS.has(t) else t, 48, INK, true))
		_choices.add_child(card)
		_choice_cards[t] = card
	_choice_t = 0.0
	_choice_glow = ""


func hide_choices() -> void:
	if _choices:
		_choices.queue_free()
	_choices = null
	_choice_cards.clear()
	_choice_shake.clear()
	_choice_t = -1.0


## Which choice card a screen point hits ("" for none).
func hit_choice(p: Vector2) -> String:
	for k in _choice_cards:
		var c: Control = _choice_cards[k]
		if Rect2(c.position, c.size).grow(20.0).has_point(p):
			return k
	return ""


func choice_pos(t: String) -> Vector2:
	if not _choice_cards.has(t):
		return Vector2(-1000, -1000)
	var c: Control = _choice_cards[t]
	return Vector2(c.position.x + c.size.x * 0.5, float(c.get_meta("y0", c.position.y)) + c.size.y * 0.5)


func choice_wrong(t: String) -> void:
	_choice_shake[t] = 0.8


func choice_right(t: String) -> void:
	_choice_glow = t
	sparkle(choice_pos(t))


func sparkle(p: Vector2) -> void:
	_sparks.append([p, 0.0])


## A kept picture of an earlier page as a tilted paper photo (recap flashback): side "left" (cold) / "right" (warm).
func show_flash(tex: Texture2D, side: String, label: String) -> void:
	if _flash == null:
		_flash = Control.new()
		_flash.name = "Flashbacks"
		_flash.set_anchors_preset(Control.PRESET_FULL_RECT)
		_flash.mouse_filter = Control.MOUSE_FILTER_IGNORE
		_root.add_child(_flash)
		_root.move_child(_flash, _caption.get_index())
	var vs := _root.get_viewport_rect().size
	var card := PanelContainer.new()
	var sb := _paper_box(Color("fbf6ea"), PAPER_EDGE, 6, 16)
	sb.content_margin_left = 14
	sb.content_margin_right = 14
	sb.content_margin_top = 14
	sb.content_margin_bottom = 8
	card.add_theme_stylebox_override("panel", sb)
	card.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var w := 500.0
	var v := VBoxContainer.new()
	v.mouse_filter = Control.MOUSE_FILTER_IGNORE
	card.add_child(v)
	var tr := TextureRect.new()
	tr.texture = tex
	tr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	tr.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
	tr.custom_minimum_size = Vector2(w, w * 0.62)
	tr.mouse_filter = Control.MOUSE_FILTER_IGNORE
	v.add_child(tr)
	v.add_child(_label(label, 40, Color("5f8fb8") if side == "left" else Color("d0702a"), true))
	card.size = Vector2(w + 28, w * 0.62 + 80)
	card.pivot_offset = card.size * 0.5
	card.position = Vector2(vs.x * (0.27 if side == "left" else 0.73) - card.size.x * 0.5, vs.y * 0.36 - card.size.y * 0.5)
	card.rotation = deg_to_rad(-4.0 if side == "left" else 3.5)
	card.scale = Vector2.ZERO
	_flash.add_child(card)
	_flash_cards[side] = [card, 0.0]


func hide_flashes() -> void:
	if _flash:
		_flash.queue_free()
	_flash = null
	_flash_cards.clear()


## Korean line breaks between words only (CSS word-break: keep-all): a WORD JOINER between the letters of each word,
## so "여몄어요." never splits into "여몄어" / "요." (critic 3). BBCode tags are left alone.
static func keep_all(t: String) -> String:
	var out := ""
	var in_tag := false
	var prev_letter := false
	for ch in t:
		if ch == "[":
			in_tag = true
		if in_tag:
			out += ch
			if ch == "]":
				in_tag = false
			continue
		var letter := ch != " " and ch != "\n"
		if letter and prev_letter:
			out += "\u2060"
		out += ch
		prev_letter = letter
	return out
