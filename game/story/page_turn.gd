class_name PageTurn
extends Control
## Paper page turn over the whole screen (component E). The old spread (a snapshot of the screen) is a sheet
## turned right-to-left about a vertical fold line that sweeps from the right edge to the left edge:
##  - left of the turned part: the old page, still lying,
##  - the turned-over back of the sheet (cream paper, the old print faintly showing through, mirrored),
##  - right of the fold: the new spread underneath, with a soft shadow cast by the lifted sheet.
## While `cover()` holds the snapshot full-screen, the next spread can be built behind it (hides the hitch).

signal finished

@export var paper := Color("efe3c8")
@export var paper_shade := Color("cdbb96")
@export var shadow := Color(0.08, 0.05, 0.02, 0.45)

var progress := 0.0  ## 0 = old page flat (covering), 1 = fully turned (new page visible)
var _tex: Texture2D  ## the old page (snapshot); null = the old page is the live view underneath
var _new: Texture2D  ## the new page drawn right of the fold; null = the live view underneath
var _dur := 1.0
var _t := -1.0


func _ready() -> void:
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	visible = false


## Live turn (2026-11-22, the pop-up rides the page): the old page stays the live view (its pieces fold as the sheet
## lifts); `new_tex` (a live SubViewport texture: the next page popping up, or the book's title page) shows right of
## the fold. Call turn() to start.
func reveal(new_tex: Texture2D, old_tex: Texture2D = null) -> void:
	cover(old_tex)
	_new = new_tex


## Show `tex` full screen (the page that is about to turn).
func cover(tex: Texture2D) -> void:
	_tex = tex
	_new = null
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	if size.x < 2.0:
		size = get_parent_area_size()
	progress = 0.0
	_t = -1.0
	visible = true
	queue_redraw()


## Turn the covering page over in `seconds` (eased like a hand: slow lift, quick sweep, soft landing).
func turn(seconds := 1.1) -> void:
	_dur = maxf(seconds, 0.05)
	_t = 0.0


## End the turn now (the caller swaps what is underneath in the same frame, so no frame shows the gap).
func finish_now() -> void:
	if _t < 0.0:
		return
	_t = -1.0
	progress = 1.0
	visible = false
	_tex = null
	_new = null
	finished.emit()


func is_turning() -> bool:
	return _t >= 0.0


func step(dt: float) -> void:
	if _t < 0.0:
		return
	_t += dt
	var u := clampf(_t / _dur, 0.0, 1.0)
	progress = u * u * (3.0 - 2.0 * u)
	progress = lerpf(progress, u, 0.25)
	queue_redraw()
	if u >= 1.0:
		_t = -1.0
		visible = false
		_tex = null
		_new = null
		finished.emit()


func _draw() -> void:
	if _tex == null and _new == null:
		return
	var W := size.x
	var H := size.y
	var ts := Vector2(_tex.get_width(), _tex.get_height()) if _tex else Vector2(W, H)
	var sx := ts.x / W
	# Fold line sweeps right -> left; it leans a little (a hand lifts the bottom corner first).
	var f := W * (1.0 - progress)
	var lean := 70.0 * sin(progress * PI)
	var f_top := f + lean * 0.5
	var f_bot := f - lean * 0.5
	# Old page still lying: x in [0, 2f - W] (mirror of the right edge across the fold).
	var a_top := 2.0 * f_top - W
	var a_bot := 2.0 * f_bot - W
	var a := maxf(a_top, a_bot)
	if a > 0.0 and _tex:
		# Lying part, clipped by the slanted back edge: draw the full strip, the back covers the slant.
		draw_texture_rect_region(_tex, Rect2(0, 0, a, H), Rect2(0, 0, a * sx, ts.y))
	if _new:
		# the new page right of the fold (live texture)
		var pts := PackedVector2Array([Vector2(f_top, 0), Vector2(W, 0), Vector2(W, H), Vector2(f_bot, H)])
		var uvs := PackedVector2Array()
		for q in pts:
			uvs.append(Vector2(q.x / W, q.y / H))
		draw_polygon(pts, PackedColorArray([Color.WHITE, Color.WHITE, Color.WHITE, Color.WHITE]), uvs, _new)
	# New page right of the fold: soft shadow of the lifted sheet (wider when the sheet is high).
	var sh_w := 30.0 + 110.0 * sin(progress * PI)
	var sc := shadow
	var clear := Color(sc.r, sc.g, sc.b, 0.0)
	draw_polygon(PackedVector2Array([Vector2(f_top, 0), Vector2(f_top + sh_w, 0), Vector2(f_bot + sh_w, H), Vector2(f_bot, H)]),
		PackedColorArray([sc, clear, clear, sc]))
	# Back of the turned sheet: from the mirrored right edge to the fold.
	var bt := maxf(a_top, 0.0)
	var bb := maxf(a_bot, 0.0)
	if f_top - bt > 0.5 or f_bot - bb > 0.5:
		var poly := PackedVector2Array([Vector2(bt, 0), Vector2(f_top, 0), Vector2(f_bot, H), Vector2(bb, H)])
		# Paper back: lighter toward the free edge, shaded into the fold (the sheet curls there).
		var lit := paper.lightened(0.06)
		draw_polygon(poly, PackedColorArray([lit, paper_shade, paper_shade, lit]))
		# Print-through: the old print, mirrored, very faint.
		var bw := maxf(f_top, f_bot) - minf(bt, bb)
		if bw > 2.0 and _tex:
			var x0 := minf(bt, bb)
			var src_x0 := (W - (2.0 * maxf(f_top, f_bot) - (x0 + bw))) * sx
			draw_texture_rect_region(_tex, Rect2(x0 + bw, 0, -bw, H), Rect2(clampf(src_x0, 0, ts.x), 0, minf(bw * sx, ts.x), ts.y),
				Color(1, 1, 1, 0.07))
		# Fold highlight + edge line.
		draw_line(Vector2(f_top, 0), Vector2(f_bot, H), Color(1, 0.97, 0.88, 0.6), 2.0)
		draw_line(Vector2(bt, 0), Vector2(bb, H), Color(0.45, 0.36, 0.25, 0.35), 1.5)
		# Shadow the back casts onto the lying old page.
		if bt > 1.0 or bb > 1.0:
			var s2 := Color(sc.r, sc.g, sc.b, 0.3)
			draw_polygon(PackedVector2Array([Vector2(bt - 26, 0), Vector2(bt, 0), Vector2(bb, H), Vector2(bb - 26, H)]),
				PackedColorArray([clear, s2, s2, clear]))
