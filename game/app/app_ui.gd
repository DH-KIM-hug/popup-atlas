class_name AppUI
extends CanvasLayer
## The app shell's 2D screens over the bookshelf (docs/APP_UI_PLAN.md): the grown-up gear (hold 1 s), parent gate,
## parent menu, 이용권 (purchase / restore over Entitlements + StoreBridge), 우리 아이 이름 (name setup), 설정, 앱 정보,
## and the child-facing "locked tale" card. Parent-facing text is 합쇼체, child-facing text 해요체 (톡톡 51939c3b).
##
## Layout in points: the root is scaled so 1 unit = 1 pt on the device (px_per_pt), so tap targets stay >= 80 pt in
## landscape and portrait; cards are at most 680 pt wide and fill the width (16 pt gutters) on narrow screens.
## Test hooks (shelf screenshots): open_screen("gate" | "menu" | "store" | "names" | "settings" | "info" | "locked" |
## "sheet" | "toast").

signal entitlements_changed

const CARD_W := 680.0
const GATE_HOLD := 1.5
const GEAR_HOLD := 1.0

var store: StoreBridge
var root: Control
var _chrome: Control
var _gear: Control
var _modal: Control
var _toast: PanelContainer
var _toast_t := 0.0
var _gear_down := -1.0
var _gate_ok: Callable
var _gate_answer := 0
var _gate_hold := -1.0
var _gate_btn: Button
var _gate_bar: ColorRect
var _stack: Array[String] = []
var _name_edit: LineEdit
var _name_preview: Label
var _t := 0.0


func _ready() -> void:
	layer = 30
	store = StoreBridge.new()
	store.name = "Store"
	add_child(store)
	store.finished.connect(_on_purchase)
	store.restored.connect(_on_restored)
	root = Control.new()
	root.name = "AppRoot"
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var th := Theme.new()
	th.default_font = AppTheme.font(520)
	th.default_font_size = 22
	root.theme = th
	add_child(root)
	_chrome = Control.new()
	_chrome.name = "Chrome"
	_chrome.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_chrome.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.add_child(_chrome)
	_build_chrome()
	_modal = Control.new()
	_modal.name = "Modal"
	_modal.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_modal.set_anchors_preset(Control.PRESET_FULL_RECT)
	root.add_child(_modal)
	_toast = PanelContainer.new()
	_toast.add_theme_stylebox_override("panel", AppTheme.box(Color(AppTheme.PAPER, 0.97), AppTheme.EDGE, 12, 8, 22))
	_toast.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_toast.visible = false
	var tl := AppTheme.label("", 22, AppTheme.INK, 600, true)
	tl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	tl.name = "Text"
	_toast.add_child(tl)
	root.add_child(_toast)
	get_viewport().size_changed.connect(_fit)
	_fit()


## Virtual-canvas pixels per device point (desktop: per window pixel).
func px_per_pt() -> float:
	var vis := get_viewport().get_visible_rect().size
	var win := Vector2(DisplayServer.window_get_size())
	var sf := DisplayServer.screen_get_scale() if (OS.has_feature("mobile") or OS.has_feature("web")) else 1.0
	if win.x <= 0:
		return 1.0
	return vis.x / (win.x / sf)


func size_pt() -> Vector2:
	return root.size


func _fit() -> void:
	var u := px_per_pt()
	root.scale = Vector2(u, u)
	root.position = Vector2.ZERO
	root.size = get_viewport().get_visible_rect().size / u
	_place_toast()
	if _stack.size() > 0:
		var top: String = _stack[-1]
		_stack.pop_back()
		_show(top)


# ------------------------------------------------------------------ chrome (on the shelf)

func _build_chrome() -> void:
	_gear = Control.new()
	_gear.name = "Gear"
	_gear.custom_minimum_size = Vector2(AppTheme.TAP, AppTheme.TAP)
	_gear.size = Vector2(AppTheme.TAP, AppTheme.TAP)
	_gear.anchor_left = 1.0
	_gear.anchor_right = 1.0
	_gear.offset_left = -AppTheme.TAP - 20
	_gear.offset_right = -20
	_gear.offset_top = 20
	_gear.offset_bottom = 20 + AppTheme.TAP
	_gear.mouse_filter = Control.MOUSE_FILTER_STOP
	_gear.draw.connect(_draw_gear)
	_gear.gui_input.connect(_gear_input)
	_chrome.add_child(_gear)


func _gear_input(e: InputEvent) -> void:
	if e is InputEventMouseButton and (e as InputEventMouseButton).button_index == MOUSE_BUTTON_LEFT:
		if e.pressed:
			_gear_down = 0.0
		else:
			if _gear_down >= 0.0 and _gear_down < GEAR_HOLD:
				toast("보호자 메뉴는 톱니를 1초 동안 꾹 눌러 주세요.")
			_gear_down = -1.0
		_gear.queue_redraw()


func _draw_gear() -> void:
	var c := _gear.size * 0.5
	var r := _gear.size.x * 0.46
	_gear.draw_circle(c + Vector2(0, 3), r, Color(0.1, 0.06, 0.02, 0.25))
	_gear.draw_circle(c, r, AppTheme.PAPER)
	_gear.draw_arc(c, r, 0, TAU, 48, AppTheme.EDGE, 2.0, true)
	var pts := PackedVector2Array()
	var teeth := 8
	for i in teeth * 4:
		var a := TAU * i / (teeth * 4.0)
		var rr := 19.0 if (i % 4) < 2 else 14.5
		pts.append(c + Vector2(cos(a), sin(a)) * rr)
	_gear.draw_colored_polygon(pts, AppTheme.INK_SOFT)
	_gear.draw_circle(c, 6.0, AppTheme.PAPER)
	if _gear_down >= 0.0:
		_gear.draw_arc(c, r - 4, -PI * 0.5, -PI * 0.5 + TAU * clampf(_gear_down / GEAR_HOLD, 0, 1), 40, AppTheme.RED, 6.0, true)


func set_chrome_visible(v: bool) -> void:
	_chrome.visible = v


func modal_open() -> bool:
	return _stack.size() > 0


func _process(dt: float) -> void:
	_t += dt
	if _gear_down >= 0.0:
		_gear_down += dt
		_gear.queue_redraw()
		if _gear_down >= GEAR_HOLD:
			_gear_down = -1.0
			_gear.queue_redraw()
			open_gate(func(): open_screen("menu"))
	if _gate_hold >= 0.0 and _gate_btn:
		_gate_hold += dt
		_gate_bar.size.x = _gate_btn.size.x * clampf(_gate_hold / GATE_HOLD, 0, 1)
		if _gate_hold >= GATE_HOLD:
			_gate_hold = -1.0
			var ok := _gate_ok
			_stack.clear()
			if ok.is_valid():
				ok.call()
	if _toast.visible:
		_toast_t -= dt
		_toast.modulate.a = clampf(_toast_t / 0.4, 0, 1)
		if _toast_t <= 0:
			_toast.visible = false


func toast(text: String, secs := 3.2) -> void:
	(_toast.get_node("Text") as Label).text = text
	_toast.visible = true
	_toast_t = secs
	_place_toast()


func _place_toast() -> void:
	if not _toast:
		return
	_toast.custom_minimum_size.x = minf(560.0, root.size.x - 32.0)
	_toast.size = Vector2.ZERO
	_toast.reset_size()
	_toast.position = Vector2((root.size.x - _toast.size.x) * 0.5, root.size.y - _toast.size.y - 36.0)


# ------------------------------------------------------------------ modal frame

func _clear_modal() -> void:
	for c in _modal.get_children():
		c.queue_free()
	_gate_btn = null
	_gate_hold = -1.0


func close_all() -> void:
	_stack.clear()
	_clear_modal()


func _back() -> void:
	if _stack.size() > 0:
		_stack.pop_back()
	if _stack.is_empty():
		_clear_modal()
	else:
		var top: String = _stack[-1]
		_stack.pop_back()
		_show(top)


## A dimmed table + one paper card; returns the card's VBox. `back` shows "뒤로" instead of "닫기".
func _card(title: String, back := false, width := CARD_W) -> VBoxContainer:
	_clear_modal()
	var dim := ColorRect.new()
	dim.color = AppTheme.DIM
	dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	dim.mouse_filter = Control.MOUSE_FILTER_STOP
	_modal.add_child(dim)
	var w := minf(width, root.size.x - 32.0)
	var scroll := ScrollContainer.new()
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	scroll.set_anchors_preset(Control.PRESET_FULL_RECT)
	scroll.offset_top = 16
	scroll.offset_bottom = -16
	_modal.add_child(scroll)
	var center := CenterContainer.new()
	center.custom_minimum_size = Vector2(root.size.x, root.size.y - 32.0)
	center.mouse_filter = Control.MOUSE_FILTER_IGNORE
	scroll.add_child(center)
	var card := PanelContainer.new()
	card.custom_minimum_size.x = w
	card.add_theme_stylebox_override("panel", AppTheme.box(AppTheme.PAPER, AppTheme.EDGE, 16, 18, 30 if w > 500 else 22))
	center.add_child(card)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 16)
	card.add_child(v)
	var head := HBoxContainer.new()
	head.add_theme_constant_override("separation", 12)
	v.add_child(head)
	var tl := AppTheme.label(title, 32, AppTheme.INK, 700)
	tl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	tl.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	head.add_child(tl)
	var x := AppTheme.button("뒤로" if back else "닫기", "plain", 112, 22)
	x.name = "Close"
	x.pressed.connect(_back if back else close_all)
	head.add_child(x)
	v.add_child(AppTheme.rule())
	return v


func _text(v: VBoxContainer, t: String, size := 21, color := AppTheme.INK_SOFT) -> Label:
	var l := AppTheme.label(t, size, color, 500, true)
	l.custom_minimum_size.x = 10
	v.add_child(l)
	return l


func open_screen(id: String) -> void:
	_stack.clear()
	_show(id)


func _push(id: String) -> void:
	_show(id)


func _show(id: String) -> void:
	_stack.append(id)
	match id:
		"menu":
			_build_menu()
		"store":
			_build_store()
		"names":
			_build_names()
		"settings":
			_build_settings()
		"info":
			_build_info()
		"gate":
			_build_gate()
		"locked":
			_build_locked()
		"sheet":
			_build_sheet("unlockall")
		"sheet_rename":
			_build_sheet("rename")
		"toast":
			_stack.pop_back()
			toast("구매를 마쳤습니다. 모든 동화가 열렸습니다.", 30.0)


# ------------------------------------------------------------------ parent gate

## Grown-ups only: a multiplication question; the right answer must be HELD for 1.5 s (톡톡's gate). `then` runs on
## success (the stack is cleared first, so it opens its own screen).
func open_gate(then: Callable) -> void:
	_gate_ok = then
	_stack.clear()
	_show("gate")


func _build_gate() -> void:
	var v := _card("보호자 확인")
	_text(v, "보호자만 들어갈 수 있습니다. 정답을 1.5초 동안 꾹 눌러 주세요.")
	var a := randi_range(3, 9)
	var b := randi_range(3, 9)
	if OS.get_cmdline_user_args().has("--app-shot"):
		a = 6
		b = 7
	_gate_answer = a * b
	var q := AppTheme.label("%d × %d = ?" % [a, b], 54, AppTheme.INK, 700)
	q.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	v.add_child(q)
	var opts := [_gate_answer]
	var rng := RandomNumberGenerator.new()
	rng.seed = a * 31 + b
	while opts.size() < 4:
		var o := _gate_answer + rng.randi_range(-12, 12)
		if o > 4 and not opts.has(o):
			opts.append(o)
	opts.sort()
	var grid := GridContainer.new()
	grid.columns = 2 if root.size.x < 560 else 4
	grid.add_theme_constant_override("h_separation", 14)
	grid.add_theme_constant_override("v_separation", 14)
	v.add_child(grid)
	for o in opts:
		var btn := AppTheme.button(str(o), "plain", 0, 34)
		btn.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		btn.custom_minimum_size.y = 96
		var bar := ColorRect.new()
		bar.color = Color(AppTheme.GREEN, 0.45)
		bar.mouse_filter = Control.MOUSE_FILTER_IGNORE
		bar.position = Vector2(0, 0)
		bar.size = Vector2(0, 96)
		btn.add_child(bar)
		btn.button_down.connect(func():
			if o == _gate_answer:
				_gate_btn = btn
				_gate_bar = bar
				_gate_hold = 0.0
			else:
				toast("다시 해 주세요.", 1.6)
				_build_gate_again())
		btn.button_up.connect(func():
			if _gate_btn == btn and _gate_hold >= 0.0:
				_gate_hold = -1.0
				bar.size.x = 0.0
				toast("정답을 1.5초 동안 꾹 눌러 주세요.", 2.0))
		grid.add_child(btn)


func _build_gate_again() -> void:
	_regate.call_deferred()


func _regate() -> void:
	if _stack.size() > 0 and _stack[-1] == "gate":
		_stack.pop_back()
		_show("gate")


# ------------------------------------------------------------------ parent menu

func _row(v: VBoxContainer, title: String, sub: String, on_press: Callable) -> Button:
	var b := AppTheme.button("", "plain")
	b.custom_minimum_size.y = 96
	b.alignment = HORIZONTAL_ALIGNMENT_LEFT
	var h := VBoxContainer.new()
	h.mouse_filter = Control.MOUSE_FILTER_IGNORE
	h.set_anchors_preset(Control.PRESET_FULL_RECT)
	h.offset_left = 24
	h.offset_right = -60
	h.alignment = BoxContainer.ALIGNMENT_CENTER
	h.add_theme_constant_override("separation", 2)
	h.add_child(AppTheme.label(title, 25, AppTheme.INK, 680))
	var s := AppTheme.label(sub, 18, AppTheme.INK_SOFT, 500)
	s.clip_text = true
	h.add_child(s)
	b.add_child(h)
	var arrow := AppTheme.label("›", 40, AppTheme.EDGE, 500)
	arrow.set_anchors_preset(Control.PRESET_CENTER_RIGHT)
	arrow.offset_left = -44
	arrow.offset_right = -18
	arrow.offset_top = -30
	arrow.offset_bottom = 26
	b.add_child(arrow)
	b.pressed.connect(on_press)
	v.add_child(b)
	return b


func _build_menu() -> void:
	var v := _card("보호자 메뉴")
	var free_n := TaleList.tales().filter(func(e): return bool(e.get("free", false))).size()
	var p: Dictionary = Entitlements.product("unlockall")
	var own := "모든 동화가 열려 있습니다"
	if Entitlements.dev_unlocked() and not Entitlements.purchased_all():
		own = "개발용 빌드: 모든 동화가 열려 있습니다"
	elif not Entitlements.owns_all():
		own = "무료 동화 %d편 · 모든 동화 열기 %s" % [free_n, p.get("display_price", "")]
	_row(v, "이용권", own, func(): _push("store"))
	_row(v, "우리 아이 이름", "창작 동화에서 주인공을 아이 이름으로 불러 줍니다", func(): _push("names"))
	_row(v, "설정", "자막 · 배경 음악 · 효과음", func(): _push("settings"))
	_row(v, "앱 정보", "광고·로그인 없음 · 개인정보 처리 방침", func(): _push("info"))


# ------------------------------------------------------------------ 이용권

func _product_card(v: VBoxContainer, key: String) -> void:
	var p: Dictionary = Entitlements.product(key)
	var ko: Dictionary = p.get("ko", {})
	var pc := PanelContainer.new()
	pc.add_theme_stylebox_override("panel", AppTheme.box(AppTheme.PAPER_DEEP, AppTheme.EDGE, 12, 0, 20))
	v.add_child(pc)
	var h := VBoxContainer.new()
	h.add_theme_constant_override("separation", 8)
	pc.add_child(h)
	var nm := AppTheme.label(str(ko.get("name", key)), 24, AppTheme.INK, 700, true)
	h.add_child(nm)
	var d := AppTheme.label(str(ko.get("desc", "")), 19, AppTheme.INK_SOFT, 500, true)
	h.add_child(d)
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 12)
	h.add_child(row)
	var note := ""
	if key == "unlockall":
		note = "한 번 구매 · 가족 공유"
	else:
		note = "구매하면 바로 %d시간 동안 이름을 정하거나 바꿀 수 있습니다" % int(p.get("run_hours", 48))
	var nl := AppTheme.label(note, 17, AppTheme.INK_SOFT, 500, true)
	nl.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	nl.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	row.add_child(nl)
	var b: Button
	if key == "unlockall" and Entitlements.purchased_all():
		b = AppTheme.button("구매함", "plain", 200)
		b.disabled = true
	else:
		b = AppTheme.button("%s  %s" % ["구매하기", p.get("display_price", "")], "main" if key == "unlockall" else "go", 210)
		b.pressed.connect(func(): _buy(key))
	b.name = "Buy_" + key
	row.add_child(b)


func _build_store() -> void:
	var v := _card("이용권", true)
	if Entitlements.dev_unlocked():
		var dev := PanelContainer.new()
		dev.add_theme_stylebox_override("panel", AppTheme.box(Color("fbe7c4"), Color("d9a65b"), 10, 0, 16))
		dev.add_child(AppTheme.label("개발용 빌드: 모든 동화가 열려 있고, 결제는 시험용입니다(실제 결제 없음).", 18, AppTheme.INK, 600, true))
		v.add_child(dev)
	_product_card(v, "unlockall")
	_product_card(v, "rename")
	var r := AppTheme.button("구매 복원", "plain")
	r.name = "Restore"
	r.pressed.connect(func(): store.restore())
	v.add_child(r)
	_text(v, "결제는 Apple 계정으로 진행됩니다. '모든 동화 열기'는 한 번 사면 계속 쓸 수 있고 가족 공유로 가족도 함께 볼 수 있습니다. 아이 이름 변경권은 소모성 상품이라 구매 복원으로 되돌아오지 않습니다.", 17)


func _buy(key: String) -> void:
	if store.is_stub():
		_push("sheet" if key == "unlockall" else "sheet_rename")
	else:
		store.purchase(key)


func _build_sheet(key: String) -> void:
	var p: Dictionary = Entitlements.product(key)
	var v := _card("시험 결제", true, 520)
	var n := AppTheme.label(str((p.get("ko", {}) as Dictionary).get("name", key)), 24, AppTheme.INK, 700, true)
	v.add_child(n)
	var pr := AppTheme.label(str(p.get("display_price", "")), 40, AppTheme.RED, 700)
	v.add_child(pr)
	_text(v, "실제 결제가 아닙니다. 확인을 누르면 이 기기에 구매한 것으로 기록됩니다. 정식 빌드에서는 이 자리에 Apple 결제 창이 뜹니다.", 18)
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 14)
	v.add_child(row)
	var c := AppTheme.button("취소", "plain")
	c.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	c.pressed.connect(func():
		store.busy = true
		store.confirm_stub(key, false))
	row.add_child(c)
	var ok := AppTheme.button("확인", "main")
	ok.name = "Confirm"
	ok.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	ok.pressed.connect(func():
		store.busy = true
		store.confirm_stub(key, true))
	row.add_child(ok)


func _on_purchase(key: String, ok: bool, _msg: String) -> void:
	if _stack.size() > 0 and _stack[-1].begins_with("sheet"):
		_stack.pop_back()
	if ok:
		entitlements_changed.emit()
		if key == "unlockall":
			toast("구매를 마쳤습니다. 모든 동화가 열렸습니다.")
		else:
			toast("아이 이름 변경권을 쓰기 시작했습니다. 48시간 동안 이름을 정하거나 바꿀 수 있습니다.", 4.0)
	if _stack.is_empty():
		_clear_modal()
		return
	var top: String = _stack[-1]
	_stack.pop_back()
	_show(top)


func _on_restored(ok: bool, owned_all: bool) -> void:
	entitlements_changed.emit()
	if not ok:
		toast("구매 복원에 실패했습니다. 잠시 뒤에 다시 해 주세요.")
	elif owned_all:
		toast("구매를 복원했습니다. 모든 동화가 열렸습니다.")
		_stack.pop_back()
		_show("store")
	else:
		toast("복원할 구매가 없습니다.")


# ------------------------------------------------------------------ 우리 아이 이름

func _build_names() -> void:
	var v := _card("우리 아이 이름", true)
	_text(v, "창작 동화에서 주인공을 아이 이름으로 불러 줍니다. 이름 앞뒤 문장은 원래 녹음 그대로 두고, 이름 부분만 새로 녹음해 기기에서 한 문장으로 이어 붙입니다.", 18)
	if Entitlements.run_active():
		var pass_l := AppTheme.label("아이 이름 변경권 사용 중 · %d시간 남음" % ceili(Entitlements.run_left_hours()), 19, AppTheme.GREEN_DARK, 650, true)
		v.add_child(pass_l)
	for e: Dictionary in TaleList.originals():
		_name_tale(v, e)
	_text(v, "이름은 녹음을 만드는 데만 쓰이고 서버에 저장되지 않습니다. 녹음이 모두 도착하기 전에는 원래 이름으로 들려 드립니다.", 16)


func _name_tale(v: VBoxContainer, e: Dictionary) -> void:
	var id := str(e["id"])
	var defaults: Dictionary = e.get("default_names", {})
	var slot := "A"
	var def_name := str(defaults.get(slot, ""))
	var cfg := AppState.tale_names(id)
	var pc := PanelContainer.new()
	pc.add_theme_stylebox_override("panel", AppTheme.box(AppTheme.PAPER_DEEP, AppTheme.EDGE, 12, 0, 18))
	v.add_child(pc)
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", 18)
	pc.add_child(h)
	var cover: Dictionary = CoverBook.tale_data(id).get("cover", {})
	var thumb := TextureRect.new()
	thumb.texture = BookModel.tex(str(cover.get("art", "")))
	thumb.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	thumb.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	var narrow := root.size.x < 560
	thumb.custom_minimum_size = Vector2(104, 130) if narrow else Vector2(150, 190)
	thumb.size_flags_vertical = Control.SIZE_SHRINK_BEGIN
	h.add_child(thumb)
	var col := VBoxContainer.new()
	col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	col.add_theme_constant_override("separation", 10)
	h.add_child(col)
	col.add_child(AppTheme.label(str(e.get("title", id)), 24, AppTheme.INK, 700, true))
	var now_name := str(cfg.get(slot, ""))
	var typed := str(_pending.get(id, now_name))
	var status := "지금: %s (원래 이름)" % def_name
	if now_name != "" and bool(cfg.get("on", false)):
		status = "지금: %s · %s" % [now_name, "녹음 완료" if bool(cfg.get("done", false)) else "녹음 준비 중 (그동안 원래 이름 %s)" % def_name]
	col.add_child(AppTheme.label(status, 18, AppTheme.INK_SOFT, 550, true))
	var le := LineEdit.new()
	le.name = "NameEdit"
	le.placeholder_text = "아이 이름 (한글 1~4자)"
	le.text = typed
	le.max_length = 4
	le.custom_minimum_size.y = AppTheme.TAP
	le.add_theme_font_override("font", AppTheme.font(600))
	le.add_theme_font_size_override("font_size", 26)
	le.add_theme_color_override("font_color", AppTheme.INK)
	le.add_theme_color_override("font_placeholder_color", Color(AppTheme.INK_SOFT, 0.6))
	var ls := AppTheme.box(Color.WHITE.lerp(AppTheme.PAPER, 0.35), AppTheme.EDGE, 10, 0, 16)
	le.add_theme_stylebox_override("normal", ls)
	le.add_theme_stylebox_override("focus", AppTheme.box(Color.WHITE, AppTheme.RED, 10, 0, 16))
	col.add_child(le)
	var prev := AppTheme.label("", 18, AppTheme.INK, 520, true)
	col.add_child(prev)
	var sample := _sample_seg(id)
	var upd := func(t: String):
		var n := t.strip_edges()
		if n == "":
			n = def_name
		prev.text = "미리 보기: " + (NameVoice.seg_text(sample, {slot: n}) if not sample.is_empty() else n)
		prev.add_theme_color_override("font_color", AppTheme.INK if NameVoice.valid_name(n) else AppTheme.RED)
	le.text_changed.connect(upd)
	le.text_changed.connect(func(t: String): _pending[id] = t)
	upd.call(le.text)
	_name_edit = le
	_name_preview = prev
	var right := Entitlements.name_right(id)
	var label := "이름 정하기"
	if right == "first":
		label = "이름 정하기 (첫 설정 무료)"
	elif right == "":
		label = "이름 정하기 (변경권 %s)" % Entitlements.product("rename").get("display_price", "")
	var b := AppTheme.button(label, "main" if right != "" else "go")
	b.name = "SetName"
	b.pressed.connect(func(): _set_name(id, slot, le.text))
	col.add_child(b)
	if now_name != "":
		var o := AppTheme.button("원래 이름으로 듣기" if bool(cfg.get("on", false)) else "아이 이름으로 듣기", "plain")
		o.pressed.connect(func():
			var c2 := AppState.tale_names(id)
			c2["on"] = not bool(c2.get("on", false))
			AppState.set_tale_names(id, c2)
			_stack.pop_back()
			_show("names"))
		col.add_child(o)


func _sample_seg(tale: String) -> Dictionary:
	var p := "res://audio/voice/%s/name/pieces.json" % tale
	if not FileAccess.file_exists(p):
		return {}
	var d: Variant = JSON.parse_string(FileAccess.get_file_as_string(p))
	if not d is Dictionary:
		return {}
	for lid in (d["lines"] as Dictionary):
		return d["lines"][lid]
	return {}


func _set_name(tale: String, slot: String, raw: String) -> void:
	var n := raw.strip_edges()
	if not NameVoice.valid_name(n):
		toast("이름은 한글 1~4자로 적어 주세요.")
		return
	if Entitlements.name_right(tale) == "":
		_push("sheet_rename")  # buy a pass first; its window opens at once and this screen comes back
		return
	Entitlements.use_name_right(tale)
	# The name server records the name pieces (docs/APP_UI_PLAN.md "이름 녹음"); not connected in this build, so the
	# tale keeps its original recordings (done = false) until the pieces arrive under user://app/names/<tale>/.
	AppState.set_tale_names(tale, {slot: n, "on": true, "done": false, "got": {}, "asked": int(Time.get_unix_time_from_system())})
	_pending.erase(tale)
	toast("'%s'(으)로 정했습니다. 녹음 서버 연결 전이라 지금은 원래 이름으로 들려 드립니다." % n, 4.5)
	_stack.pop_back()
	_show("names")


# ------------------------------------------------------------------ 설정 / 앱 정보

func _toggle_row(v: VBoxContainer, title: String, key: String) -> void:
	var h := HBoxContainer.new()
	h.add_theme_constant_override("separation", 14)
	v.add_child(h)
	var l := AppTheme.label(title, 25, AppTheme.INK, 650)
	l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	h.add_child(l)
	var on := bool(AppState.get_v(key, true))
	var b := AppTheme.button("켜짐" if on else "꺼짐", "go" if on else "plain", 150)
	b.name = "Toggle_" + key
	b.pressed.connect(func():
		AppState.set_v(key, not bool(AppState.get_v(key, true)))
		_stack.pop_back()
		_show("settings"))
	h.add_child(b)


func _build_settings() -> void:
	var v := _card("설정", true)
	_toggle_row(v, "자막", "subtitles")
	_toggle_row(v, "배경 음악", "music")
	_toggle_row(v, "효과음", "sfx")
	_text(v, "목소리는 늘 켜져 있습니다. 기기 옆 소리 단추로 전체 크기를 맞춰 주세요.", 17)


func _build_info() -> void:
	var v := _card("앱 정보", true)
	for t in ["광고가 없습니다.", "로그인과 계정 만들기가 없습니다.", "이용 기록·분석 도구를 쓰지 않습니다.",
			"아이 이름은 이 기기에만 저장되고, 녹음을 만들 때만 서버로 보내며 서버에 남지 않습니다.",
			"동화 목소리는 미리 녹음한 것이고, 기기에서 글을 읽어 만드는 음성(TTS)은 쓰지 않습니다."]:
		_text(v, "· " + t, 19, AppTheme.INK)
	_text(v, "팝업 동화 %s" % str(ProjectSettings.get_setting("application/config/version", "개발용")), 16)


# ------------------------------------------------------------------ locked tale (child-facing)

var locked_title := ""
var _pending := {}  ## tale -> name typed but not set yet (kept across a pass purchase)


func open_locked(title: String) -> void:
	locked_title = title
	open_screen("locked")


func _build_locked() -> void:
	var v := _card("잠긴 동화", false, 560)
	var t := AppTheme.label("「%s」" % (locked_title if locked_title != "" else "동화"), 30, AppTheme.INK, 700, true)
	t.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	v.add_child(t)
	var s := AppTheme.label("이 동화는 아직 잠겨 있어요. 어른에게 보여 주세요!", 24, AppTheme.INK, 550, true)
	s.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	v.add_child(s)
	var b := AppTheme.button("어른에게 보여 주기", "main")
	b.pressed.connect(func(): open_gate(func(): open_screen("store")))
	v.add_child(b)
