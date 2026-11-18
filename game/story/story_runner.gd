class_name StoryRunner
extends Node
## Plays a tale's script.json as a pop-up book (component E).
## beats -> spreads: each beat names a spread (MeadowWorld seed + view). Entering a new spread folds the old one
## down, turns the page (PageTurn over a snapshot, the next spread is built under it) and pops the new one up in
## a wave. Consecutive beats on the same spread share the page. Steps play narration line by line (clip per seg,
## optional subtitles on a paper caption strip), wait for taps from the script, walk the traveller on the road,
## and end on the moral card with "다시 보기". Narration auto-advances; a tap on the page skips the line.
##
## Verify mode (command line after `--`, or `--agent-args {json}` from the gd_run toolkit, or the exports):
##   --beat=<id>     start at that beat (its spread is built directly, cover skipped)
##   --autoplay      plays the whole story unattended, taps/holds simulated (with ripples) so it can be captured
##   --fixed         deterministic 1/60 s per frame (PopHinge / PaperSpring fixed_dt)
##   --mute          no voice / paper audio      --nosubs   subtitles off
## Prints STORY lines: LINE <id> t=, BEAT <id> t=, STORY_DONE total=<s> missing_audio=[...].

signal story_finished(total_s: float)

@export_file("*.json") var script_path := "res://stories/sun_wind/script.json"
@export var autoplay := false
@export var start_beat := ""
@export var fixed_step := false
@export var mute := false
@export var subtitles := true
@export var auto_tap_delay := 1.0  ## autoplay: seconds before a simulated tap
@export var hint_after := 7.0  ## seconds of no input before a hint line

var data: Dictionary = {}
var lines: Dictionary = {}
var beats: Array = []
var ui: StoryUI
var stage: SpreadStage
var player: AudioStreamPlayer
var clock := 0.0
var missing_audio: Array[String] = []
var beat_times: Dictionary = {}

var _spread_key := ""
var _skip := false
var _press := false
var _tapped := ""
var _expect: Array = []  ## targets the current step waits for
var _mode := "idle"  ## idle | cover | tap | blow | end
var _line_busy := false
var _pose := "walk"
var quit_on_done := false
var _streams: Dictionary = {}
var _auto_press_t := 0.0
var _auto_cycle := 0.0
var _replay := false
var _snaps: Dictionary = {}  ## key -> Texture2D kept for the recap flashbacks
## perf: next spread built ahead, a few ms per frame, while the current page plays (key -> {stage, vp, beat}).
var _prebuilt: Dictionary = {}
var _last_line := ""
const PREBUILD_BUDGET_MS := 3.0
var _choosing := false


func _ready() -> void:
	_parse_args()
	_apply_render_scale()
	if fixed_step:
		PopHinge.fixed_dt = 1.0 / 60.0
		PaperSpring.fixed_dt = 1.0 / 60.0
	_load_script()
	player = AudioStreamPlayer.new()
	player.name = "Voice"
	add_child(player)
	ui = StoryUI.new()
	ui.name = "UI"
	add_child(ui)
	ui.subtitles = subtitles
	ui.replay_pressed.connect(func(): _replay = true)
	ui.pointer_source = Callable()
	_run.call_deferred()


## perf (device): the look was approved at 1366x1024; on a phone/tablet the 3D view renders at about that height
## (iPad Pro 11" 2388x1668 -> 3D scale 0.61, the depth-of-field / tilt-shift blur hides the upscale) while the UI
## stays at native resolution. Desktop windows are unchanged.
const RENDER_HEIGHT := 1024.0


func _apply_render_scale() -> void:
	if not OS.has_feature("mobile"):
		return
	var h := float(DisplayServer.window_get_size().y)
	if h > RENDER_HEIGHT:
		get_viewport().scaling_3d_scale = clampf(RENDER_HEIGHT / h, 0.5, 1.0)
	print("PERF render_scale=", get_viewport().scaling_3d_scale, " window=", DisplayServer.window_get_size())


func _parse_args() -> void:
	var ua := OS.get_cmdline_user_args()
	for i in ua.size():
		var a: String = ua[i]
		if a == "--agent-args" and i + 1 < ua.size():
			var d: Variant = JSON.parse_string(ua[i + 1])
			if d is Dictionary:
				start_beat = str(d.get("beat", start_beat))
				autoplay = bool(d.get("autoplay", autoplay))
				fixed_step = bool(d.get("fixed", fixed_step))
				mute = bool(d.get("mute", mute))
				subtitles = bool(d.get("subtitles", subtitles))
		elif a.begins_with("--beat="):
			start_beat = a.get_slice("=", 1)
		elif a == "--autoplay":
			autoplay = true
		elif a == "--fixed":
			fixed_step = true
		elif a == "--mute":
			mute = true
		elif a == "--nosubs":
			subtitles = false
		elif a == "--quit-on-done":  # recordings: quit 2 s after the story ends (movie maker writes the file)
			quit_on_done = true


func _load_script() -> void:
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(script_path))
	if not parsed is Dictionary:
		push_error("StoryRunner: cannot read " + script_path)
		return
	data = parsed
	beats = data.get("beats", [])
	for l: Dictionary in data.get("lines", []):
		lines[str(l["id"])] = l
		if not l.get("used", true):
			continue
		for s: Dictionary in l["segs"]:
			var p := str(s.get("audio", ""))
			if p == "" or not ResourceLoader.exists(p):
				if not missing_audio.has(str(l["id"])):
					missing_audio.append(str(l["id"]))
	print("STORY ", data.get("tale_id", "?"), " beats=", beats.size(), " lines=", lines.size(),
		" missing_audio=", missing_audio, " autoplay=", autoplay, " start=", start_beat)


# ------------------------------------------------------------------ clock + input

func _dt() -> float:
	return PaperSpring.frame_dt(get_process_delta_time())


func _frame() -> float:
	await get_tree().process_frame
	return _dt()


func _wait(sec: float, skippable := false) -> void:
	var t := 0.0
	while t < sec:
		t += await _frame()
		if skippable and _skip:
			return


func _process(dt: float) -> void:
	if dt > 0.03 and clock > 1.0:
		print("PERF hitch ms=", snappedf(dt * 1000.0, 0.1), " t=", snappedf(clock, 0.01), " mode=", _mode, " line=", _last_line)
	dt = PaperSpring.frame_dt(dt)
	clock += dt
	ui.step(dt)
	# Autoplay holds the wind in bursts while a blow step runs (lines keep playing over the gusts).
	if autoplay and _mode == "blow" and stage:
		_auto_cycle += dt
		var on := fmod(_auto_cycle, 2.2) < 1.6
		if on and not _press:
			ui.ripple(stage.target_screen("wind"))
		_press = on
	if stage and is_instance_valid(stage):
		stage.set_blowing(_press and _mode == "blow", 1.0)


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and (event as InputEventMouseButton).button_index == MOUSE_BUTTON_LEFT:
		var mb := event as InputEventMouseButton
		if mb.pressed:
			_pointer_down(mb.position)
		else:
			_press = false


func _pointer_down(p: Vector2) -> void:
	_press = true
	ui.ripple(p)
	if _mode == "cover":
		_tapped = "book"
		return
	if _choosing:
		var c := ui.hit_choice(p)
		if c != "" and _expect.has(c):
			_tapped = c
		elif _line_busy:
			_skip = true
		return
	var hit := ""
	if stage and is_instance_valid(stage) and stage.world:
		hit = stage.hit_target(p)
	if hit != "" and hit != "traveller":
		stage.wiggle(hit)
	if _expect.has(hit):
		_tapped = hit
		_skip = _line_busy  # tapping the asked-for target also cuts the prompt short
	elif _mode != "blow" and _line_busy:
		_skip = true


func _auto_tap(target: String) -> void:
	var p: Vector2
	if target == "replay":
		p = ui.end_button_pos()
	elif target == "book":
		p = Vector2(683, 512)
	elif _choosing:
		p = ui.choice_pos(target)
	else:
		p = stage.target_screen(target)
	_pointer_down(p)
	_press = false


# ------------------------------------------------------------------ lines

func _stream(path: String) -> AudioStream:
	if path == "" or not ResourceLoader.exists(path):
		return null
	if not _streams.has(path):
		_streams[path] = load(path)
	return _streams[path]


func _seg_duration(s: Dictionary) -> float:
	var st := _stream(str(s.get("audio", "")))
	if st:
		return st.get_length()
	# No recording yet (changed line): read-aloud estimate, ~7 syllables a second.
	var n := str(s["text"]).replace(" ", "").length()
	return 0.6 + n * 0.14


func line_duration(id: String) -> float:
	var l: Dictionary = lines.get(id, {})
	var t := 0.0
	for s: Dictionary in l.get("segs", []):
		t += _seg_duration(s) + 0.12
	return t + 0.35


func _say(id: String) -> void:
	if id == "" or not lines.has(id):
		if id != "":
			push_warning("StoryRunner: no line " + id)
		return
	var l: Dictionary = lines[id]
	_line_busy = true
	_skip = false
	print("LINE ", id, " t=", snappedf(clock, 0.01), " ", l["text"])
	_last_line = id
	var segs: Array = l["segs"]
	for i in segs.size():
		var s: Dictionary = segs[i]
		ui.show_line(l, i)
		var st := _stream(str(s.get("audio", "")))
		if st and not mute:
			player.stream = st
			player.play()
		await _wait(_seg_duration(s) + 0.08, true)
		if _skip:
			break
	if _skip:
		player.stop()
	_skip = false
	await _wait(0.25, true)
	_skip = false
	ui.hide_line(0.5)
	_line_busy = false


func _say_lines(ids: Array) -> void:
	for id in ids:
		await _say(str(id))


## Waits until one of `targets` is tapped (autoplay: simulated after a pause; `auto_order` picks which).
## Plays `hint` after a quiet spell. Returns the tapped target.
func _wait_tap(targets: Array, hint := "", auto_order: Array = [], show_pointer := true) -> String:
	_expect = targets
	_tapped = ""
	var idle := 0.0
	var auto_i := 0
	if show_pointer:
		var tg := str(targets[0])
		ui.pointer_source = func(): return _pointer_at(tg)
	while _tapped == "":
		var dt: float = await _frame()
		idle += dt
		if autoplay and idle > auto_tap_delay:
			var order: Array = auto_order if not auto_order.is_empty() else targets
			_auto_tap(str(order[mini(auto_i, order.size() - 1)]))
			auto_i += 1
		elif idle > hint_after and hint != "":
			idle = 0.0
			await _say(hint)
	var hit := _tapped
	_tapped = ""
	_expect = []
	ui.pointer_source = Callable()
	return hit


func _pointer_at(target: String) -> Vector3:
	if stage == null or not is_instance_valid(stage):
		return Vector3(-1000, -1000, 0)
	var p := stage.target_screen(target)
	# the ring goes around the whole card (the wind is wide), clear of the face
	return Vector3(p.x, p.y, stage.target_radius(target) * (1.0 if target == "traveller" else 1.3))


# ------------------------------------------------------------------ main loop

func _run() -> void:
	while true:
		var t0 := clock
		var i0 := 0
		if start_beat != "":
			for i in beats.size():
				if str(beats[i]["id"]) == start_beat:
					i0 = i
		if start_beat == "":
			_prebuild_after(i0 - 1)  # first spread builds behind the cover page
		_warm_cast()
		for i in range(i0, beats.size()):
			await _play_beat(beats[i])
		var total := clock - t0
		print("STORY_DONE total=", snappedf(total, 0.1), " missing_audio=", missing_audio, " beats=", beat_times)
		story_finished.emit(total)
		if autoplay:
			if quit_on_done:
				await _wait(2.0)
				get_tree().quit()
			return
		while not _replay:
			await _frame()
		_replay = false
		start_beat = ""
		ui.hide_end()
		_spread_key = ""
		_pose = "walk"


func _play_beat(b: Dictionary) -> void:
	beat_times[str(b["id"])] = snappedf(clock, 0.1)
	print("BEAT ", b["id"], " t=", snappedf(clock, 0.01))
	var enter: Dictionary = b.get("enter", {})
	if enter.has("pose"):
		_pose = str(enter["pose"])
	if b.get("spread") is Dictionary:
		await _enter_spread(b)
		if enter.has("pose") and stage.puppet().pose != _pose:
			stage.set_pose(_pose)
	for st: Dictionary in b.get("steps", []):
		await _step(st, b)


func _step(st: Dictionary, b: Dictionary) -> void:
	match str(st["do"]):
		"cover":
			await _step_cover(st, b)
		"say":
			await _say(str(st["line"]))
		"fx":
			stage.fx(str(st["fx"]))
			await _wait(0.4)
		"cam":
			stage.shot_to(str(st["shot"]))
			await _wait(float(st.get("wait", 0.6)))
		"snap":
			_snaps[str(st["key"])] = await _snapshot(true)
		"flash":
			var tex: Texture2D = _snaps.get(str(st["key"]))
			if tex:
				ui.show_flash(tex, str(st.get("side", "left")), "바람이 불 때" if str(st.get("side", "left")) == "left" else "해님이 비출 때")
			await _say(str(st.get("line", "")))
		"walk_away":
			stage.walk_away(float(st.get("dist", 1.2)))
			if st.has("line"):
				_say.bind(str(st["line"])).call()
			await _frame()
			var guard2 := 0.0
			while (stage.walking() or _line_busy) and guard2 < 30.0:
				guard2 += await _frame()
		"stroll":
			# he walks on along the road while the next steps play (wind, sun); "stop" ends it
			stage.stroll(float(st.get("speed", 0.12)))
		"stop":
			stage.stroll_stop()
			await _frame()
			var guard3 := 0.0
			while stage.walking() and guard3 < 5.0:
				guard3 += await _frame()
		"pose":
			_pose = str(st["pose"])
			stage.set_pose(_pose)
			await _wait(0.5)
		"walk", "walk_to":
			if str(st["do"]) == "walk_to" and str(st.get("place", "")) == "stream":
				stage.walk_to_bank()
			else:
				stage.walk_by(float(st.get("dist", 0.5)))
			if st.has("line"):
				_say.bind(str(st["line"])).call()
			await _frame()
			var guard := 0.0
			while (stage.walking() or _line_busy) and guard < 30.0:
				guard += await _frame()
		"tap":
			await _say(str(st.get("prompt", "")))
			var hit := await _wait_tap([str(st["target"])], str(st.get("hint", "")))
			stage.wiggle(hit)
			if st.has("react"):
				stage.fx(str(st["react"]))
			await _say_lines(st.get("lines", []))
		"blow":
			await _step_blow(st)
		"shine":
			await _step_shine(st)
		"quiz":
			await _step_quiz(st)
		"gentle":
			await _step_gentle(st)
		"end":
			await _step_end(st)
		_:
			push_warning("StoryRunner: unknown step " + str(st["do"]))
	_pose = stage.puppet().pose if stage and is_instance_valid(stage) else _pose


func _step_cover(st: Dictionary, b: Dictionary) -> void:
	_mode = "cover"
	ui.show_cover(str(data.get("title", b.get("title", ""))))
	await _wait(0.6)
	_say.bind(str(st.get("prompt", ""))).call()
	_tapped = ""
	var idle := 0.0
	while _tapped != "book":
		idle += await _frame()
		if autoplay and idle > 2.6:
			_auto_tap("book")
	_skip = true
	while _line_busy:
		await _frame()
	_mode = "idle"


func _step_blow(st: Dictionary) -> void:
	await _say(str(st.get("prompt", "")))
	_mode = "blow"
	_auto_cycle = 0.0
	var steps: Array = st.get("steps", [])
	var amount := 0.0
	var idle := 0.0
	var k := 0
	var hints := 0
	ui.pointer_source = func(): return _pointer_at("wind")
	while k < steps.size():
		var dt: float = await _frame()
		if _press:
			amount += dt
			idle = 0.0
		else:
			idle += dt
		var need := float(steps[k]["need"])
		var prev := float(steps[k - 1]["need"]) if k > 0 else 0.0
		ui.hold_progress = clampf((amount - prev) / maxf(need - prev, 0.01), 0.0, 1.0)
		if amount >= need:
			ui.hold_progress = -1.0
			stage.fx(str(steps[k].get("fx", "")))
			await _say_lines(steps[k].get("lines", []))
			k += 1
			idle = 0.0
		elif idle > hint_after * 0.8:
			idle = 0.0
			await _say(str(st.get("hint", "")) if hints % 2 == 0 or k == 0 else str(st.get("more", "")))
			hints += 1
	_mode = "idle"
	_press = false
	ui.hold_progress = -1.0
	ui.pointer_source = Callable()


func _step_shine(st: Dictionary) -> void:
	await _say(str(st.get("prompt", "")))
	for s: Dictionary in st.get("steps", []):
		await _wait_tap(["sun"], str(st.get("hint", "")))
		stage.wiggle("sun")
		stage.fx(str(s.get("fx", "")))
		await _say_lines(s.get("lines", []))
		if s.has("next"):
			await _say(str(s["next"]))


func _step_quiz(st: Dictionary) -> void:
	var answer := str(st.get("answer", "sun"))
	var wrong: Dictionary = st.get("wrong", {})
	ui.hide_flashes()
	var targets: Array = ["sun", "wind"]
	ui.show_choices(targets)
	_choosing = true
	await _say(str(st.get("prompt", "")))
	var order: Array = []
	if autoplay:
		order = wrong.keys() + [answer]  # autoplay shows the wrong path once, then answers
	var tried := 0
	while true:
		var hit := await _wait_tap(targets, "", [order[mini(tried, order.size() - 1)]] if autoplay else [], false)
		tried += 1
		if hit == answer:
			ui.choice_right(hit)
			stage.fx("quiz_right")
			await _say_lines(st.get("right", []))
			break
		# Wrong: the wind blows a cold gust on him again (shiver), "으으, 추워!", and the child tries again.
		ui.choice_wrong(hit)
		stage.fx("quiz_wrong")
		await _say_lines(wrong.get(hit, []))
	_choosing = false
	ui.hide_choices()


func _step_gentle(st: Dictionary) -> void:
	await _say(str(st.get("prompt", "")))
	for i in int(st.get("taps", 3)):
		await _wait_tap(["wind"], str(st.get("hint", "")))
		stage.gentle_gust()
		await _wait(0.6)
	await _say_lines(st.get("lines", []))


func _step_end(st: Dictionary) -> void:
	await _say(str(st.get("line", "")))
	_mode = "end"
	ui.show_end("")
	ui.sparkle(Vector2(683, 300))
	await _wait(0.6)
	await _say(str(st.get("after", "")))
	if autoplay:
		await _wait(2.5)
		ui.ripple(ui.end_button_pos())
		await _wait(0.4)
	_mode = "idle"


# ------------------------------------------------------------------ spreads + page turn

func _snapshot(without_ui := false) -> Texture2D:
	if without_ui:
		ui.visible = false
		await get_tree().process_frame
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	if without_ui:
		ui.visible = true
		img.resize(img.get_width() / 2, img.get_height() / 2, Image.INTERPOLATE_BILINEAR)
	return ImageTexture.create_from_image(img)


func _enter_spread(b: Dictionary) -> void:
	var sp: Dictionary = b["spread"]
	var key := "%d:%d" % [int(sp.get("seed", 1)), int(sp.get("view", 0))]
	if key == _spread_key and stage:
		return
	var had := stage != null and is_instance_valid(stage)
	var pre: Dictionary = _prebuilt.get(key, {})
	ui.hide_line()
	ui.pointer_source = Callable()
	ui.show_page_title("")
	ui.hide_flashes()
	ui.hide_choices()
	if had:
		var t := stage.fold()
		await _wait(t + 0.9)
	var cover_shown := ui.cover_visible()
	var tex: Texture2D = null
	if had or cover_shown:
		tex = await _snapshot()
		ui.page_turn.cover(tex)
		ui.hide_cover()
		await _frame()
	if had:
		stage.queue_free()
		stage = null
		await _frame()
	var t_build := Time.get_ticks_usec()
	if not pre.is_empty():
		var ps: SpreadStage = pre["stage"]
		while not ps.is_built:  # normally done long ago; otherwise it keeps slicing under the cover
			await _frame()
		var t_move := Time.get_ticks_usec()
		var vp: SubViewport = pre["vp"]
		vp.remove_child(ps)
		ps.name = "Spread_" + str(b["id"])
		add_child(ps)
		vp.queue_free()
		_prebuilt.erase(key)
		stage = ps
		print("PERF spread_prebuilt ", key, " frames=", ps.build_frames, " max_slice_ms=", snappedf(ps.max_slice_ms, 0.1),
			" phases=", ps.perf_phases, " move_ms=", snappedf((Time.get_ticks_usec() - t_move) / 1000.0, 0.1))
	else:
		stage = SpreadStage.new()
		stage.name = "Spread_" + str(b["id"])
		add_child(stage)
		var rt: Array = sp.get("route", [])
		if rt.size() == 2:
			stage.route = Vector2(float(rt[0]), float(rt[1]))
		stage.build(int(sp.get("seed", 1)), int(sp.get("view", 0)), not mute)
		print("PERF spread_build ", key, " ms=", snappedf((Time.get_ticks_usec() - t_build) / 1000.0, 0.1))
	stage.set_pose(_pose, true)
	_spread_key = key
	await _frame()
	await _frame()
	var wave_t := 0.0
	# r2: the new page lies flat under the turning sheet and pops up once it lands, so the rise is seen (critic 3).
	if tex:
		ui.page_turn.turn(1.1)
		while ui.page_turn.is_turning():
			await _frame()
	wave_t = stage.pop(0.0)
	ui.show_page_title(str(b.get("title", "")))
	_prebuild_after(beats.find(b))
	await _wait(clampf(wave_t * 0.6, 0.9, 1.8))


# ------------------------------------------------------------------ perf: spread prebuild

static func _key_of(sp: Dictionary) -> String:
	return "%d:%d" % [int(sp.get("seed", 1)), int(sp.get("view", 0))]


## Start building the first spread after beat index i that differs from the one on screen (no-op if already going).
## It lives in an off-screen SubViewport with its own World3D (its camera, lights and environment do not touch the
## page on screen; nothing is rendered there) until _enter_spread moves it into the story.
## Not in fixed-step runs (captures, recordings): there each spread is built at its page turn exactly as before, so
## the global RNG sequence (hinge jitter, gusts) and every frame stay reproducible.
func _prebuild_after(i: int) -> void:
	if fixed_step:
		return
	for j in range(i + 1, beats.size()):
		var sp: Variant = beats[j].get("spread")
		if not sp is Dictionary:
			continue
		var key := _key_of(sp)
		if key == _spread_key:
			continue  # later beats on the page on screen
		if _prebuilt.has(key):
			return
		var vp := SubViewport.new()
		vp.name = "Prebuild_" + key.replace(":", "_")
		vp.own_world_3d = true
		vp.size = Vector2i(get_viewport().get_visible_rect().size)
		vp.render_target_update_mode = SubViewport.UPDATE_DISABLED
		vp.audio_listener_enable_3d = false
		vp.process_mode = Node.PROCESS_MODE_DISABLED  # nothing in the waiting spread ticks (the build runs on process_frame)
		add_child(vp)
		var st := SpreadStage.new()
		var rt: Array = sp.get("route", [])
		if rt.size() == 2:
			st.route = Vector2(float(rt[0]), float(rt[1]))
		vp.add_child(st)
		_prebuilt[key] = {"stage": st, "vp": vp}
		st.build_async(int(sp.get("seed", 1)), int(sp.get("view", 0)), not mute, PREBUILD_BUDGET_MS)
		return


## perf: trace every traveller figure print ahead (a few ms per frame), so a pose change mid-page (coat open, fan,
## coat off, hat back) only builds its card meshes instead of tracing new outlines in that frame (30-45 ms hitches).
const CAST_RIG_DIR := "res://art/cast/rig/"
var _cast_textures: Array[Texture2D] = []  ## kept loaded: a pose swap must not decode its figure from disk either


func _warm_cast() -> void:
	if not _cast_textures.is_empty():
		return
	var sl := BuildSlicer.new(2.0, get_tree())
	for f in ResourceLoader.list_directory(CAST_RIG_DIR):
		if not (f.begins_with("cast_traveller") and f.ends_with(".png")):
			continue
		var tex := load(CAST_RIG_DIR + f) as Texture2D
		if tex:
			_cast_textures.append(tex)
			PaperCard.warm(tex)
		await sl.tick()
	for cast: String in CastSkins.CAST_IDS:
		for variant: String in CastSkins.CAST_IDS[cast]:
			var tex := CastSkins.texture(cast, variant)
			if tex:
				_cast_textures.append(tex)
				PaperCard.warm(tex)
			await sl.tick()
	print("PERF cast_warm textures=", _cast_textures.size(), " frames=", sl.frames)

