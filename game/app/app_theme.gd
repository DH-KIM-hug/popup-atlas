class_name AppTheme
extends RefCounted
## The app shell's paper chrome (docs/APP_UI_PLAN.md "보기"): the same cut-paper stock as the story chrome (StoryUI):
## cream card, brown ink, thin kraft edge, soft drop shadow, no felt / stitching. Sizes are in POINTS: AppUI scales
## its root so 1 unit = 1 pt on the device (tap targets >= 80 pt hold in landscape and portrait).

const FONT_PATH := "res://story/fonts/PretendardVariable.woff2"
const INK := Color("3b2a1c")
const INK_SOFT := Color("6b5640")
const PAPER := Color("f4ead3")
const PAPER_DEEP := Color("e9dcbd")
const EDGE := Color("b89a6a")
const RED := Color("b4553c")
const RED_DARK := Color("7a3424")
const GREEN := Color("5f7f6a")
const GREEN_DARK := Color("3b5444")
const CREAM := Color("fff3d6")
const DIM := Color(0.10, 0.06, 0.03, 0.55)
const TAP := 80.0  ## minimum tap target (pt)

static var _fonts: Dictionary = {}


static func font(weight := 520) -> Font:
	if _fonts.has(weight):
		return _fonts[weight]
	var base: Font = load(FONT_PATH) if ResourceLoader.exists(FONT_PATH) else ThemeDB.fallback_font
	var fv := FontVariation.new()
	fv.base_font = base
	var ts := TextServerManager.get_primary_interface()
	fv.variation_opentype = {ts.name_to_tag("weight"): weight}
	_fonts[weight] = fv
	return fv


static func box(bg := PAPER, edge := EDGE, radius := 12, shadow := 8, pad := 24) -> StyleBoxFlat:
	var sb := StyleBoxFlat.new()
	sb.bg_color = bg
	sb.border_color = edge
	sb.set_border_width_all(2)
	sb.set_corner_radius_all(radius)
	sb.shadow_color = Color(0.1, 0.06, 0.02, 0.3)
	sb.shadow_size = shadow
	sb.shadow_offset = Vector2(0, 4)
	sb.content_margin_left = pad
	sb.content_margin_right = pad
	sb.content_margin_top = pad * 0.6
	sb.content_margin_bottom = pad * 0.7
	return sb


static func label(text: String, size := 22, color := INK, weight := 520, wrap := false) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_font_override("font", font(weight))
	l.add_theme_font_size_override("font_size", size)
	l.add_theme_color_override("font_color", color)
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	if wrap:
		l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	return l


## kind: "main" (red, the one action), "go" (green), "plain" (paper), "quiet" (paper, smaller text)
static func button(text: String, kind := "plain", min_w := 0.0, size := 24) -> Button:
	var b := Button.new()
	b.text = text
	b.focus_mode = Control.FOCUS_NONE
	b.custom_minimum_size = Vector2(min_w, TAP)
	b.add_theme_font_override("font", font(650))
	b.add_theme_font_size_override("font_size", size if kind != "quiet" else size - 2)
	var bg := PAPER
	var edge := EDGE
	var fg := INK
	match kind:
		"main":
			bg = RED
			edge = RED_DARK
			fg = CREAM
		"go":
			bg = GREEN
			edge = GREEN_DARK
			fg = CREAM
	for st in ["normal", "hover", "pressed", "focus", "disabled"]:
		var c := bg
		if st == "pressed":
			c = bg.darkened(0.14)
		elif st == "disabled":
			c = bg.lerp(PAPER_DEEP, 0.6)
		var sb := box(c, edge, 12, 5 if st != "pressed" else 2, 20)
		sb.content_margin_top = 10
		sb.content_margin_bottom = 12
		b.add_theme_stylebox_override(st, sb)
	for st in ["font_color", "font_hover_color", "font_pressed_color", "font_focus_color"]:
		b.add_theme_color_override(st, fg)
	b.add_theme_color_override("font_disabled_color", INK_SOFT)
	return b


static func rule() -> HSeparator:
	var s := HSeparator.new()
	var sb := StyleBoxLine.new()
	sb.color = Color(EDGE, 0.6)
	sb.thickness = 2
	s.add_theme_stylebox_override("separator", sb)
	s.add_theme_constant_override("separation", 10)
	return s
