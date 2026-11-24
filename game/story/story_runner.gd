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
##   --tale=<id>     play game/stories/<id>/script.json (default: the scene's script_path)
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
static var now := 0.0  ## the story clock, for logs from other nodes (StoryActor --log-track)
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
var sound: SoundDirector
var log_sound := false
var _blow_target := "wind"

## Camera continuity check (user 2026-11-22: "시점이 뚝뚝 끊기는거 별로에요"): every frame the stage camera's view
## motion (view-direction turn + position shift seen from the focus distance + half the fov change, deg) is compared
## with the frame before. A frame moving more than CAM_JUMP_DEG is a cut (CAM_JUMP), a one-frame velocity change above
## CAM_JERK_DPS a jerk (CAM_JERK: a move starting / stopping / turning at full speed). Not counted: page turns (hidden
## under the sheet), the cover, other cameras (the ending book) and shakes (an intended jolt).
const CAM_JUMP_DEG := 3.0
const CAM_JERK_DPS := 20.0
var cam_jumps := 0
var cam_jerks := 0
var _cam_last: Dictionary = {}
var _beat_id := ""
## SPEAKER_OFF check (2026-11-22): a quote's speaker must be in the frame and not hidden behind a set piece within
## SPEAKER_GRACE s of its segment starting, and stay so for most of the rest of it (stage.speaker_state).
const SPEAKER_GRACE := 1.5
var speaker_off := 0
var _spk: Dictionary = {}
var _spk_unknown := {}
var _late_pending := false
var _framed_house := ""  # a "frame" step already set up the coming build's shot
var _walker_role := "traveller"
var _exiting := false
var _leaving := false


func _ready() -> void:
	tree_exiting.connect(func(): _exiting = true)
	_parse_args()
	_apply_render_scale()
	if fixed_step:
		PopHinge.fixed_dt = 1.0 / 60.0
		PaperSpring.fixed_dt = 1.0 / 60.0
	_load_script()
	if data.has("sound"):
		sound = SoundDirector.new()
		sound.name = "Sound"
		sound.tale = data["sound"]
		sound.log_sound = log_sound
		if fixed_step:
			sound.rng.seed = hash(str(data.get("tale_id", "")))  # reproducible captures
		else:
			sound.rng.randomize()
		add_child(sound)
	player = AudioStreamPlayer.new()
	player.name = "Voice"
	add_child(player)
	if AudioServer.get_bus_index("Voice") >= 0:
		player.bus = "Voice"
	ui = StoryUI.new()
	ui.name = "UI"
	add_child(ui)
	ui.subtitles = subtitles
	var ui_cfg: Dictionary = (data.get("ui", {}) as Dictionary).duplicate()
	var book_cfg := CoverBook.tale_data(str(data.get("tale_id", "")))  # stories/<tale>/cover.json: the book + ending
	for k in book_cfg:
		ui_cfg[k] = book_cfg[k]
	data["ui"] = ui_cfg
	ui.configure(ui_cfg)
	ui.replay_pressed.connect(func(): _replay = true)
	ui.other_pressed.connect(_go_shelf)
	ui.pointer_source = Callable()
	_run.call_deferred()


## perf (device): the look was approved at 1366x1024; on a phone/tablet the 3D view renders at about that height
## (iPad Pro 11" 2388x1668 -> 3D scale 0.61, the depth-of-field / tilt-shift blur hides the upscale) while the UI
## stays at native resolution. Desktop windows are unchanged.
const RENDER_HEIGHT := 1024.0


func _apply_render_scale() -> void:
	if not (OS.has_feature("mobile") or OS.has_feature("web")):  # web: the browser canvas is device pixels too
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
				if d.has("tale"):
					script_path = "res://stories/%s/script.json" % str(d["tale"])
				autoplay = bool(d.get("autoplay", autoplay))
				fixed_step = bool(d.get("fixed", fixed_step))
				mute = bool(d.get("mute", mute))
				subtitles = bool(d.get("subtitles", subtitles))
		elif a.begins_with("--tale="):  # play another tale from the main scene (res://stories/<id>/script.json)
			script_path = "res://stories/%s/script.json" % a.get_slice("=", 1)
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
		elif a == "--log-sound":
			log_sound = true
		elif a == "--quit-on-done":  # recordings: quit 2 s after the story ends (movie maker writes the file)
			quit_on_done = true
		elif a.begins_with("--end-choice="):  # recordings: after STORY_DONE press "replay" or "other" (the shelf)
			end_choice = a.get_slice("=", 1)


func _load_script() -> void:
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(script_path))
	if not parsed is Dictionary:
		push_error("StoryRunner: cannot read " + script_path)
		return
	data = parsed
	beats = data.get("beats", [])
	for role in (data.get("cast", {}) as Dictionary):
		if str((data["cast"][role] as Dictionary).get("kind", "")) == "walker":
			_walker_role = str(role)
	_names_setup()
	for l: Dictionary in data.get("lines", []):
		lines[str(l["id"])] = l
		if not l.get("used", true):
			continue
		for s: Dictionary in l["segs"]:
			var p := str(s.get("audio", ""))
			if s.has("pieces"):  # creative-tale name line: name piece + fixed pieces (NameVoice)
				if not NameVoice.pieces_exist(s) and not missing_audio.has(str(l["id"])):
					missing_audio.append(str(l["id"]))
				continue
			if p == "" or not ResourceLoader.exists(p):
				if not missing_audio.has(str(l["id"])):
					missing_audio.append(str(l["id"]))
	print("STORY ", data.get("tale_id", "?"), " beats=", beats.size(), " lines=", lines.size(),
		" missing_audio=", missing_audio, " autoplay=", autoplay, " start=", start_beat)


# ------------------------------------------------------------------ clock + input

func _enter_tree() -> void:
	if not _leaving:
		_exiting = false


func _exit_tree() -> void:
	_exiting = true


func _notification(what: int) -> void:
	if what == NOTIFICATION_PREDELETE:
		_leaving = true
		_exiting = true


func _alive() -> bool:
	return not _exiting and is_inside_tree() and get_tree() != null


func _dt() -> float:
	return PaperSpring.frame_dt(get_process_delta_time()) if _alive() else 0.0


## A coroutine that resumes while the runner is out of the tree (the app quitting or the scene changing during a
## line / tween / timer) must not spin: get_tree() is null there and `await null.process_frame` returns at once with
## a 0 s step, so every `_wait` loop ran forever in one frame (patjuk gate v1: 5 GB of errors, the run never ended).
## When exiting, `_alive()` returns false so every coroutine unwinds cleanly; if detached temporarily, it parks.
static var _off_tree_logged := false
var _cap_logged := false


func _frame() -> float:
	if not _alive():
		if not _exiting and not is_inside_tree():
			if not _off_tree_logged:
				_off_tree_logged = true
				print("RUNNER_OFF_TREE t=", snappedf(clock, 0.01), " line=", _last_line, " (a coroutine resumed after the runner left the tree; parked)")
			await tree_entered
		return 0.0
	var tree := get_tree()
	if tree == null:
		_exiting = true
		return 0.0
	await tree.process_frame
	if not _alive():
		return 0.0
	return _dt()


func _wait(sec: float, skippable := false) -> void:
	var t := 0.0
	while t < sec and _alive():
		t += await _frame()
		if skippable and _skip:
			return


func _process(dt: float) -> void:
	if _exiting or not is_inside_tree():
		return
	if dt > 0.03 and clock > 1.0:
		print("PERF hitch ms=", snappedf(dt * 1000.0, 0.1), " t=", snappedf(clock, 0.01), " mode=", _mode, " line=", _last_line)
	dt = PaperSpring.frame_dt(dt)
	clock += dt
	now = clock
	ui.step(dt)
	_cam_monitor(dt)
	_speaker_monitor()
	# CAPTION 1|0 t=: when the caption strip shows / hides (motion_review.py: a mover under the caption)
	var cap_on: bool = ui._caption != null and ui._caption.visible
	if cap_on != _cap_logged:
		_cap_logged = cap_on
		print("CAPTION ", int(cap_on), " t=", snappedf(clock, 0.01))
	# Autoplay holds the wind in bursts while a blow step runs (lines keep playing over the gusts).
	if autoplay and _mode == "blow" and stage:
		_auto_cycle += dt
		var on := fmod(_auto_cycle, 2.2) < 1.6
		if on and not _press:
			ui.ripple(stage.target_screen(_blow_target))
		_press = on
	if stage and is_instance_valid(stage):
		stage.set_blowing(_press and _mode == "blow", 1.0)


func _unhandled_input(event: InputEvent) -> void:
	if _exiting or not is_inside_tree():
		return
	if event is InputEventMouseButton and (event as InputEventMouseButton).button_index == MOUSE_BUTTON_LEFT:
		var mb := event as InputEventMouseButton
		if mb.pressed:
			_pointer_down(mb.position)
		else:
			_press = false


func _pointer_down(p: Vector2) -> void:
	if _exiting or not is_inside_tree():
		return
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
		hit = stage.hit_target(p, _expect)
	if hit != "" and hit != _walker_role:
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

## Creative-tale name lines (app shell 2026-11-23, docs/APP_UI_PLAN.md): segs with `pieces` play as the name piece +
## fixed pieces joined into one clip (NameVoice, 톡톡's method). A parent's name (AppState, never in command-line
## runs) replaces the name in the captions and the name piece once all its recordings are on the device.
var _custom_names := false


func _names_setup() -> void:
	var tale := str(data.get("tale_id", ""))
	var defaults := TaleList.default_names(tale)
	if defaults.is_empty():
		return
	var names := NameVoice.active_names(tale, defaults)
	_custom_names = names != defaults
	for l: Dictionary in data.get("lines", []):
		var segs: Array = l.get("segs", [])
		for i in segs.size():
			var s: Dictionary = segs[i]
			if not s.has("pieces"):
				continue
			s["_nv"] = [str(l["id"]), i]
			if _custom_names:
				var quoted := str(s["text"]).strip_edges().begins_with("\"")
				var t := NameVoice.seg_text(s, names)
				s["text"] = ("\"%s\"" % t) if quoted else t
				if segs.size() == 1:
					l["text"] = ("\"%s\"" % t) if str(l["text"]).strip_edges().begins_with("\"") else t


func _seg_stream(s: Dictionary) -> AudioStream:
	if s.has("_nv"):
		var nv: Array = s["_nv"]
		var st := NameVoice.stream_for(str(data.get("tale_id", "")), nv[0], nv[1], s, _custom_names)
		if st:
			return st
	return _stream(str(s.get("audio", "")))


func _stream(path: String) -> AudioStream:
	if path == "" or not ResourceLoader.exists(path):
		return null
	if not _streams.has(path):
		_streams[path] = load(path)
	return _streams[path]


func _seg_duration(s: Dictionary) -> float:
	var st := _seg_stream(s)
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


var _voiced := {}
var _last_voice := ""
var voice_dup := 0
var _hint_ids := {}  ## lines that are idle hints (they may legitimately replay)


func _say(id: String, only: Array = []) -> void:
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
		if not only.is_empty() and not only.has(i) and not only.has(float(i)):
			continue  # a line split across steps (narration during a walk, the quote at the mark)
		print("SEG ", id, " ", i, " t=", snappedf(clock, 0.01))
		var s: Dictionary = segs[i]
		_speaker_begin(id, i, s)
		ui.show_line(l, i)
		_apply_expr(l, i)
		var st := _seg_stream(s)
		if st and not mute:
			# one caption, one voice (witch_candy v8): count a segment voiced twice in the run and a voice that starts
			# while another is still sounding (it would be cut or doubled)
			var key := "%s:%d" % [id, i]
			# branch-aware (2026-11-22): a line legitimately replayed in a later round (another beat: the same ingredient
			# picked twice) is not a dup; a segment voiced twice within one beat is
			var bkey := _beat_id + "/" + key
			if _voiced.has(bkey) and not _hint_ids.has(id):
				voice_dup += 1
				print("VOICE_DUP ", key, " t=", snappedf(clock, 0.01))
			_voiced[bkey] = true
			if player.playing and player.get_playback_position() < player.stream.get_length() - 0.15:
				voice_dup += 1
				print("VOICE_OVERLAP ", key, " over ", _last_voice, " t=", snappedf(clock, 0.01))
			_last_voice = key
			player.stream = st
			player.play()
		if sound:
			sound.duck(true)
		await _wait(_seg_duration(s) + 0.08, true)
		_speaker_end()
		if not _alive():
			_line_busy = false
			return
		if _skip:
			break
	if _skip:
		player.stop()
	if sound:
		sound.duck(false)
	_skip = false
	await _wait(0.25, true)
	_skip = false
	if _alive():
		ui.hide_line(0.5)
	_line_busy = false


func _say_lines(ids: Array) -> void:
	for id in ids:
		if not _alive():
			return
		await _say(str(id))


## Waits until one of `targets` is tapped (autoplay: simulated after a pause; `auto_order` picks which).
## Plays `hint` after a quiet spell. Returns the tapped target.
func _wait_tap(targets: Array, hint := "", auto_order: Array = [], show_pointer := true, reframe := true) -> String:
	if not _alive():
		return ""
	if reframe and not _choosing and stage and is_instance_valid(stage) and stage.frame_targets(targets):
		await _wait(1.2)  # the camera settles on every target before the child is asked to tap
	if not _alive():
		return ""
	_expect = targets
	_tapped = ""
	var idle := 0.0
	var auto_i := 0
	if show_pointer:
		var tg := str(targets[0])
		ui.pointer_source = func(): return _pointer_at(tg)
	while _tapped == "" and _alive():
		var dt: float = await _frame()
		if not _alive():
			break
		idle += dt
		if autoplay and idle > 8.0 and not _choosing and stage and stage.target_screen(str(targets[0])).x < -999.0:
			push_warning("StoryRunner: tap target not on the page: " + str(targets))
			_tapped = str(targets[0])
			break
		if autoplay and idle > auto_tap_delay:
			var order: Array = auto_order if not auto_order.is_empty() else targets
			_auto_tap(str(order[mini(auto_i, order.size() - 1)]))
			auto_i += 1
		elif idle > hint_after and hint != "":
			idle = 0.0
			_hint_ids[hint] = true  # an idle replay of the prompt: allowed (a reminder, not a doubled clip)
			await _say(hint)
	var hit := _tapped
	_tapped = ""
	_expect = []
	if is_instance_valid(ui):
		ui.pointer_source = Callable()
	return hit


func _pointer_at(target: String) -> Vector3:
	if stage == null or not is_instance_valid(stage):
		return Vector3(-1000, -1000, 0)
	var p := stage.target_screen(target)
	# the ring goes around the whole card (the wind is wide), clear of the face
	return Vector3(p.x, p.y, stage.target_radius(target) * (1.0 if target == _walker_role else 1.3))


# ------------------------------------------------------------------ main loop

func _run() -> void:
	while _alive():
		var t0 := clock
		var i0 := 0
		if start_beat != "":
			for i in beats.size():
				if str(beats[i]["id"]) == start_beat:
					i0 = i
		if start_beat == "":
			_prebuild_after(i0 - 1, COVER_BUILD_MS)  # first spread builds behind the cover page
		_warm_cast()
		for i in range(i0, beats.size()):
			if not _alive():
				return
			await _play_beat(beats[i])
		if not _alive():
			return
		var total := clock - t0
		if stage and is_instance_valid(stage) and stage.tale.get("overlap_check", false):
			# totals over every page of the run (the last page's own counts in brackets)
			print("OVERLAP_COUNT ", SpreadStage.run_overlaps, " OCCLUDE_COUNT ", SpreadStage.run_occludes, " (last page ",
				stage.overlap_count, " / ", stage.occlude_count, ")")
		if stage and is_instance_valid(stage):
			var wrong := 0
			var used := false
			for r in stage.actors:
				var pp: Variant = (stage.actors[r] as StoryActor).puppet
				if pp is CastPuppet:
					wrong += (pp as CastPuppet).mouth_wrong
					used = used or (pp as CastPuppet).mouth_seen
			if used:
				var miss := int(stage.handler.get("black_missing")) if stage.handler and "black_missing" in stage.handler else 0
				print("BLACK_LIPS frames-with-wrong-variant=", wrong + miss, " (puppet ", wrong, ", story-expected ", miss, ")")
		print("VOICE_DUP=", voice_dup)
		print("CAM_JUMP=", cam_jumps, " CAM_JERK=", cam_jerks, " SPEAKER_OFF=", speaker_off)
		print("STORY_DONE total=", snappedf(total, 0.1), " missing_audio=", missing_audio,
			" missing_sound=", sound.missing if sound else [], " beats=", beat_times)
		story_finished.emit(total)
		if autoplay and end_choice != "":
			await _wait(1.0)
			if not _alive():
				return
			if end_choice == "other":
				ui.ripple(ui.other_button_pos())
				await _wait(0.3)
				if _alive():
					_go_shelf()
				return
			ui.ripple(ui.end_button_pos())
			await _wait(0.3)
			if not _alive():
				return
			_replay = true
			end_choice = ""
		elif autoplay:
			if quit_on_done:
				await _wait(2.0)
				if _alive():
					get_tree().quit()
			return
		while not _replay and _alive():
			await _frame()
		if not _alive():
			return
		_replay = false
		start_beat = ""
		if sound:
			sound.loop_stop("table", 0.6)
		ui.hide_end()
		_spread_key = ""
		_pose = "walk"


func _play_beat(b: Dictionary) -> void:
	if not _alive():
		return
	beat_times[str(b["id"])] = snappedf(clock, 0.1)
	print("BEAT ", b["id"], " t=", snappedf(clock, 0.01))
	_beat_id = str(b["id"])
	var enter: Dictionary = b.get("enter", {})
	if enter.has("pose"):
		_pose = str(enter["pose"])
	var key0 := _spread_key
	if sound and not b.get("spread") is Dictionary:
		sound.enter_beat(b, null, false)
	if b.get("spread") is Dictionary:
		await _enter_spread(b)
		if not _alive():
			return
		if sound:
			sound.enter_beat(b, stage, _spread_key != key0)
		if enter.has("pose") and stage and is_instance_valid(stage) and stage.puppet().pose != _pose:
			stage.set_pose(_pose)
	var prev: Dictionary = {}
	for st: Dictionary in b.get("steps", []):
		if not _alive():
			return
		# a quick cam move right before a line: the line starts once the glide is well under way (the eased moves land
		# later than the old exponential chase did, and a quote must not start before its speakers are in frame)
		if str(st.get("do", "")) == "say" and str(prev.get("do", "")) == "cam" and float(prev.get("rate", 2.4)) >= 2.0 \
				and stage and is_instance_valid(stage):
			await _wait(stage.cam_settle_left(0.4))
		if not _alive():
			return
		await _step(st, b)
		prev = st


func _speaker_monitor() -> void:
	if _spk.is_empty() or stage == null or not is_instance_valid(stage) or not stage.is_built or ui.page_turn.visible:
		return
	var st := stage.speaker_state(str(_spk["who"]))
	if st == "?":
		if not _spk_unknown.has(_spk["who"]):
			_spk_unknown[_spk["who"]] = true
			print("SPEAKER_UNKNOWN ", _spk["who"])
		_spk = {}
		return
	var el := clock - float(_spk["t0"])
	if el <= float(_spk["grace"]):
		if st == "":
			_spk["seen"] = true
		else:
			_spk["why"] = st
			_spk["at"] = stage.speaker_where(str(_spk["who"]))
	else:
		_spk["n"] = int(_spk["n"]) + 1
		if st == "":
			_spk["on"] = int(_spk["on"]) + 1
		else:
			_spk["why"] = st
			_spk["at"] = stage.speaker_where(str(_spk["who"]))


func _speaker_begin(id: String, i: int, s: Dictionary) -> void:
	_speaker_end()
	var who := str(s.get("speaker", "nar"))
	if who == "nar" or who == "all" or who == "":
		return
	if (data.get("speaker_insert", []) as Array).has(id):
		print("SPEAKER_INSERT ", id, ":", i, " who=", who)  # a deliberate cutaway (the tale lists it): not checked
		return
	var dur := _seg_duration(s)
	if stage and is_instance_valid(stage):
		stage.talking = who
	_spk = {"who": who, "key": "%s:%d" % [id, i], "t0": clock, "grace": minf(SPEAKER_GRACE, dur * 0.6), "seen": false,
		"n": 0, "on": 0, "why": ""}


func _speaker_end() -> void:
	if stage and is_instance_valid(stage):
		stage.talking = ""
	if _spk.is_empty():
		return
	var n := int(_spk["n"])
	var frac := float(_spk["on"]) / n if n > 0 else 1.0
	if not bool(_spk["seen"]) or frac < 0.6:
		speaker_off += 1
		print("SPEAKER_OFF ", _spk["key"], " who=", _spk["who"], " t=", snappedf(float(_spk["t0"]), 0.01), " beat=", _beat_id,
			" shot=", stage.shot if stage and is_instance_valid(stage) else "", " seen=", _spk["seen"], " on=",
			snappedf(frac, 0.01), " why=", _spk["why"], " at=", _spk.get("at", ""))
	_spk = {}


func _cam_monitor(dt: float) -> void:
	var cam: Camera3D = null
	if stage and is_instance_valid(stage) and stage.is_built and stage.world and not ui.page_turn.visible \
			and not ui.cover_visible():  # page_turn.visible: the old page covers the screen or is turning
		cam = stage.camera()
	if cam == null or get_viewport().get_camera_3d() != cam or dt <= 0.0:
		_cam_last = {}
		return
	var f := -cam.global_transform.basis.z
	var p := cam.global_position
	var d := maxf(stage.world.rig.distance, 0.3)
	var now := {"cam": cam, "f": f, "p": p, "fov": cam.fov, "v": PackedFloat32Array(), "flag": false}
	if _cam_last.is_empty() or _cam_last["cam"] != cam or stage.shaking():
		_cam_last = now
		return
	var tv: Vector3 = (f - (_cam_last["f"] as Vector3)) * (180.0 / PI)
	var sv: Vector3 = (p - (_cam_last["p"] as Vector3)) / d * (180.0 / PI)
	var z := (cam.fov - float(_cam_last["fov"])) * 0.5
	var v := PackedFloat32Array([tv.x / dt, tv.y / dt, tv.z / dt, sv.x / dt, sv.y / dt, sv.z / dt, z / dt])
	var mag := 0.0
	for x in v:
		mag += x * x
	mag = sqrt(mag) * dt
	var dv := 0.0
	var pv: PackedFloat32Array = _cam_last["v"]
	if pv.size() == v.size():
		for i in v.size():
			dv += (v[i] - pv[i]) * (v[i] - pv[i])
		dv = sqrt(dv)
	var jump := mag > CAM_JUMP_DEG
	var jerk := not jump and dv > CAM_JERK_DPS
	if (jump or jerk) and not bool(_cam_last["flag"]):
		if jump:
			cam_jumps += 1
		else:
			cam_jerks += 1
		print("CAM_JUMP " if jump else "CAM_JERK ", "t=", snappedf(clock, 0.01), " beat=", _beat_id, " shot=", stage.shot,
			" deg=", snappedf(mag, 0.01), " dv=", snappedf(dv, 0.1))
	now["v"] = v
	now["flag"] = jump or jerk
	_cam_last = now


## Cast members a step names (`who`: role or list).
func _who(st: Dictionary) -> Array:
	var w: Variant = st.get("who", null)
	if w == null:
		return []
	return w if w is Array else [w]


## Line → expression map (script.json lines[].expr, {role: pose | [pose per seg]}): the faces change with the words.
## Only cast standing on the page; a walking actor keeps its walking figure and shows the face when it stops.
func _apply_expr(l: Dictionary, seg_i: int) -> void:
	if stage == null or not is_instance_valid(stage) or not l.get("expr") is Dictionary:
		return
	var ex: Dictionary = l["expr"]
	for role in ex:
		var a := stage.actor(str(role))
		if a == null or a.pop_target < 0.5:
			continue
		var v: Variant = ex[role]
		var p := ""
		if v is Array:
			if (v as Array).is_empty():
				continue
			p = str(v[mini(seg_i, (v as Array).size() - 1)])
		else:
			p = str(v)
		if a.has_pose(p) and a.view_of(p) != "back":
			a.set_pose(p)
			if a.has_meta("inside") and seg_i < (l["segs"] as Array).size() and str(l["segs"][seg_i]["speaker"]) != "nar":
				a.hop_v = maxf(a.hop_v, 0.45)  # speaking from inside: a little bob in the window


func _wait_actors(roles: Array, guard_s := 30.0) -> void:
	var g := 0.0
	await _frame()
	while g < guard_s and _alive():
		var busy := _line_busy
		if stage and is_instance_valid(stage):
			for r in roles:
				var a := stage.actor(str(r))
				if a and a.moving():
					busy = true
		if not busy:
			return
		g += await _frame()


func _step(st: Dictionary, b: Dictionary) -> void:
	match str(st["do"]):
		"cover":
			await _step_cover(st, b)
		"say":
			await _say(str(st["line"]), st.get("segs", []))
		"fx":
			stage.fx(str(st["fx"]))
			await _wait(float(st.get("wait", 0.4)))
		"cam":
			var opts: Dictionary = {}
			for k in ["from", "rate", "shake", "follow", "cut"]:
				if st.has(k):
					opts[k] = st[k]
			stage.shot_to(str(st["shot"]), st.get("at", null), opts)
			await _wait(float(st.get("wait", 0.6)))
			if st.has("settle"):  # hold until the glide has gone this fraction of its time (a line follows)
				await _wait(stage.cam_settle_left(float(st["settle"])))
		"cam_settle":  # wait for a camera move a tale fx started (a glide in through the door) before the next line
			await _wait(stage.cam_settle_left(float(st.get("frac", 0.6))))
		"snap":
			_snaps[str(st["key"])] = await _snapshot(true)
		"flash":
			var tex: Texture2D = _snaps.get(str(st["key"]))
			if tex:
				var left := str(st.get("side", "left")) == "left"
				ui.show_flash(tex, str(st.get("side", "left")), str(st.get("label", "바람이 불 때" if left else "해님이 비출 때")))
			await _say(str(st.get("line", "")))
		"walk_away":
			stage.walk_away(float(st.get("dist", 1.2)))
			if st.has("line"):
				_say.bind(str(st["line"])).call()
			await _frame()
			var guard2 := 0.0
			var exited := false
			while _alive() and (stage.walking() or _line_busy) and guard2 < 30.0:
				if not exited and not stage.walker_in_frame():
					exited = true
					stage.walk_stop()
					stage.walk_away_frame_sky()
				guard2 += await _frame()
		"stroll":
			# he walks on along the road while the next steps play (wind, sun); "stop" ends it
			stage.stroll(float(st.get("speed", 0.12)))
		"stop":
			stage.stroll_stop()
			await _frame()
			var guard3 := 0.0
			while _alive() and stage.walking() and guard3 < 5.0:
				guard3 += await _frame()
		"pose":
			if st.has("who"):
				for r in _who(st):
					var a := stage.actor(str(r))
					if a:
						a.set_pose(str(st["pose"]), int(st.get("left", -1)))
						if st.get("hop", false):
							a.hop_v = 0.7
				await _wait(float(st.get("wait", 0.3)))
			else:
				_pose = str(st["pose"])
				stage.set_pose(_pose)
				await _wait(float(st.get("wait", 0.5)))
		"walk", "walk_to":
			if st.has("who"):
				await _step_walk_actors(st)
			else:
				if str(st["do"]) == "walk_to":
					stage.walk_to_place(str(st.get("place", "")))
				else:
					stage.walk_by(float(st.get("dist", 0.5)))
				if st.has("line"):
					_say.bind(str(st["line"])).call()
				await _frame()
				var guard := 0.0
				while _alive() and (stage.walking() or _line_busy) and guard < 30.0:
					guard += await _frame()
		"climb":
			await _step_climb(st)
		"go_inside":
			await _step_go_inside(st)
		"tap":
			await _frame_first([str(st["target"])])
			await _say(str(st.get("prompt", "")))
			var hit := await _wait_tap([str(st["target"])], str(st.get("hint", "")))
			stage.wiggle(hit)
			if st.has("react"):
				stage.fx(str(st["react"]))
			await _say_lines(st.get("lines", []))
		"tap_each":
			await _step_tap_each(st)
		"tap_steps":
			await _step_tap_steps(st)
		"frame":
			# the build's one framing (finished house + pile + builder), set before its intro so the build never reframes
			_framed_house = str(st.get("house", "house"))
			stage.frame_build(_framed_house, st.get("with", []))
			await _wait(float(st.get("wait", 1.0)))
		"build":
			await _step_build(st)
		"huff":
			await _step_huff(st)
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
			# tale verbs (witch_candy: brew, ...): the tale's handler runs the step with the runner's helpers
			if stage and stage.handler and stage.handler.has_method("run_step"):
				await stage.handler.run_step(st, self)
			else:
				push_warning("StoryRunner: unknown step " + str(st["do"]))
	_pose = stage.puppet().pose if stage and is_instance_valid(stage) else _pose


## walk {who, dir (toward | away | left | right), dist, to (spot), from (spot), pose, speed, line, wait}:
## several actors keep their formation; an actor not on the page yet steps in from `from` (or dist back along dir).
func _step_walk_actors(st: Dictionary) -> void:
	var roles := _who(st)
	var d := stage.dir_vec(str(st.get("dir", "right")))
	var dist := float(st.get("dist", 0.6))
	var spd := float(st.get("speed", 0.2))
	var lead := Vector3.ZERO
	var has_to := st.has("to")
	if st.has("follow"):  # tracking shot on this walker
		stage.follow_actor(str(st["follow"]), str(st.get("shot", "story")))
		if st.has("follow_for"):  # follow briefly, then let him go (the camera holds, he runs off into the distance)
			var rel := func():
				if _alive() and stage and is_instance_valid(stage):
					stage.shot_to(str(st.get("release_shot", "stage")), st.get("release_at", null), {"rate": 1.2})
			if _alive():
				get_tree().create_timer(float(st["follow_for"])).timeout.connect(rel)
	# wolf_goats 2026-11-23: `to` may map each role to its own mark ({kid1: "watch_kid1", mom: "watch_mom"})
	var to_map: Dictionary = st["to"] if has_to and st["to"] is Dictionary else {}
	if has_to and to_map.is_empty():
		lead = stage.spot_point(st["to"])
	for i in roles.size():
		var a := stage.actor(str(roles[i]))
		if a == null:
			continue
		if not to_map.is_empty():
			lead = stage.spot_point(to_map.get(str(roles[i]), to_map.values()[0]))
		if a.pop_target < 0.5:
			var start: Vector3
			if st.has("from"):
				start = stage.spot_point(st["from"]) - d * 0.12 * i
			elif has_to:
				start = lead - d * dist - d * 0.12 * i
			else:
				start = a.global_position - d * dist
			a.place_at(start)
			a.pop_delay = 0.0
			a.pop_target = 1.0
			a.puppet.set_figure(str(st.get("pose", "calm")) if a.has_pose(str(st.get("pose", ""))) else "calm", d.dot(stage.dir_vec("left")) > 0.5, true)
		var goal := a.global_position + d * dist
		if has_to:
			goal = lead if not to_map.is_empty() else lead - d * 0.14 * i + stage.dir_vec("away") * 0.05 * (i % 2)
		if st.has("path"):  # explicit waypoints (spots), feet on the ground
			var pts: Array = []
			for q in st["path"]:
				pts.append(stage.spot_point(q))
			if st.get("file", false) and i > 0:
				continue  # followers trail the leader (_file_follow below)
			a.follow(pts, spd, str(st.get("pose", "")), false)
		elif str(st.get("via", "")) == "road":
			# along the road (a village spread): the route bends with it, the figure faces each stretch
			var rt := stage.road_route(a.global_position, goal)
			for j in i:  # followers keep a step behind
				if rt.size() > 2:
					rt.pop_back()
			rt.append(goal)
			a.follow(rt, spd, str(st.get("pose", "")), false)
		elif st.get("via") is Array:  # sunmoon 2026-11-22: waypoints by spot name (round a house, not through it)
			var pts: Array = []
			for v in (st["via"] as Array):
				pts.append(stage.spot_point(v))
			pts.append(goal)
			a.follow(pts, spd, str(st.get("pose", "")), false)
		else:
			a.walk_to(goal, spd, str(st.get("pose", "")))
		if st.has("end_pose"):
			a.pose = str(st["end_pose"])
	if st.get("file", false) and roles.size() > 1:
		_file_busy = true
		var ff := func():
			await _file_follow(roles, float(st.get("spacing", 0.17)), spd, str(st.get("pose", "")))
			_file_busy = false
		ff.call()
	if st.has("line"):
		if st.get("line_late", false):
			# the narration ends as the walker arrives (the quote that follows comes right after he stops)
			var a0 := stage.actor(str(roles[0]))
			var est := 0.0
			if a0:
				var prev := a0.global_position
				for q in a0._path:
					est += prev.distance_to(q)
					prev = q
				est += prev.distance_to(a0._target) if a0._path.is_empty() else 0.0
				est /= maxf(spd, 0.05)
			var dur := 0.0
			var segs_l: Array = st.get("segs", [])
			var ln: Dictionary = lines.get(str(st["line"]), {})
			for i in (ln.get("segs", []) as Array).size():
				if segs_l.is_empty() or segs_l.has(i) or segs_l.has(float(i)):
					dur += _seg_duration(ln["segs"][i]) + 0.12
			var late := maxf(0.0, est - dur - 0.2)
			_late_pending = true
			var go := func():
				_late_pending = false
				if _alive():
					_say(str(st["line"]), segs_l)
			if _alive():
				get_tree().create_timer(late).timeout.connect(go)
			else:
				_late_pending = false
		else:
			_say.bind(str(st["line"]), st.get("segs", [])).call()
	if st.get("async", false):
		return
	await _wait(0.1)
	if not _alive():
		return
	await _wait_actors(roles)
	while _file_busy and _alive():
		await _frame()
	while (_late_pending or _line_busy) and _alive():  # the late narration has played before the next step (the quote)
		await _frame()
	if not _alive():
		return
	if sound and str(st.get("end_pose", "")) == "sniff" and stage.actor("wolf"):
		sound.play("wolf.sniff", stage.actor("wolf").centre())
	if st.get("exit", false):
		for r in roles:
			var a2 := stage.actor(str(r))
			if a2:
				a2.pop_target = 0.02


var _file_busy := false


## Single file (v3, "물체랑 사람들끼리 자꾸 겹치잖아"): followers walk the leader's actual trail, follower i always
## i·spacing of trail behind the leader, so nobody catches up at a corner or cuts across. Runs until the leader stops
## and everyone stands at their trail point.
func _file_follow(roles: Array, spacing: float, spd: float, pose: String) -> void:
	var lead := stage.actor(str(roles[0]))
	if lead == null:
		return
	var trail: Array = [lead.global_position]
	var lens: Array = [0.0]
	# the line as it stands now (behind the leader, toward each follower) seeds the trail
	for i in range(1, roles.size()):
		var a := stage.actor(str(roles[i]))
		if a:
			trail.push_front(a.global_position)
	lens = [0.0]
	for k in range(1, trail.size()):
		lens.append(float(lens[k - 1]) + (trail[k] as Vector3).distance_to(trail[k - 1]))
	var g := 0.0
	while g < 60.0 and _alive():
		g += await _frame()
		if not _alive() or lead == null or not is_instance_valid(lead):
			return
		var p := lead.global_position
		if p.distance_to(trail[trail.size() - 1]) > 0.02:
			lens.append(float(lens[lens.size() - 1]) + p.distance_to(trail[trail.size() - 1]))
			trail.append(p)
		var total := float(lens[lens.size() - 1])
		var busy := lead.moving()
		for i in range(1, roles.size()):
			var a := stage.actor(str(roles[i]))
			if a == null:
				continue
			var want := maxf(0.0, total - spacing * i)
			var k := 1
			while k < lens.size() - 1 and float(lens[k]) < want:
				k += 1
			var u := clampf((want - float(lens[k - 1])) / maxf(float(lens[k]) - float(lens[k - 1]), 1e-4), 0.0, 1.0)
			var tgt: Vector3 = (trail[k - 1] as Vector3).lerp(trail[k], u)
			if a.global_position.distance_to(tgt) > 0.03:
				a.walk_to(tgt, spd * 1.15, pose)
				busy = true
		if not busy:
			return


## go_inside {who, house, from (spot, for actors not on the page yet), windows [index per actor], line, speed}:
## each runs to the door, the door swings open, in they go (back view through the doorway), the door shuts, and
## their face appears in a window.
func _step_go_inside(st: Dictionary) -> void:
	var house := str(st.get("house", "house"))
	var sp := stage.set_piece(house)
	var roles := _who(st)
	var wins: Array = st.get("windows", [])
	if st.has("line"):
		_say.bind(str(st["line"])).call()
	if sp == null or not sp.has_door():
		for i in roles.size():
			stage.put_inside(str(roles[i]), house, int(wins[i]) if i < wins.size() else 0)
		return
	var toward := stage.dir_vec("toward")
	if st.get("house_facing", false):  # a house turned to face the road: in front of its own door (witch_candy)
		toward = sp.global_transform.basis.z.normalized()
	var spd := float(st.get("speed", 0.4))
	var front := sp.door_point(true, toward)
	# one queue in front of the door: the first at the door, the others a step further out toward the camera, so
	# nobody walks back toward the camera (a front view) while waiting; then the door opens ONCE, everyone goes in
	# one after the other (back view through the doorway) and it shuts ONCE after the last is inside
	for i in roles.size():
		var a := stage.actor(str(roles[i]))
		if a == null:
			continue
		if a.pop_target < 0.5:
			var fr := stage.spot_point(st.get("from", "anchor")) + stage.dir_vec("right") * 0.15 * i
			a.place_at(fr)
			a.lift = 0.0
			a.pop_delay = 0.0
			a.pop_target = 1.0
		# where the queue waits: "front" out along the path, "along" beside the door along the house front (v3: a long
		# line out of the path reached the next house)
		var qd := toward if str(st.get("queue", "")) == "front" else stage.dir_vec(str(st.get("queue", "toward")))
		if str(st.get("queue", "")) == "along":
			qd = -sp.global_transform.basis.x.normalized() + toward * 0.35
		elif str(st.get("queue", "")) == "along_right":  # v7: the free side of the shop (no pumpkin, no neighbour)
			qd = sp.global_transform.basis.x.normalized() + toward * 0.35
		var qspot := front + qd * float(st.get("queue_gap", 0.16)) * i + (toward * 0.05 if st.has("queue") else Vector3.ZERO)
		if st.has("approach"):
			# round by the end of the path (v7: walking straight to the queue cut across the neighbour house's front)
			# from the end of the path straight in along it: each stops behind the one before (nobody passes anyone)
			var near := a.global_position.distance_to(stage.spot_point(st["approach"])) < 0.25
			var apts: Array = ([qspot] if near else [stage.spot_point(st["approach"]), qspot]) if str(st.get("queue", "")) == "front" \
				else [stage.spot_point(st["approach"]) + stage.dir_vec("right") * 0.08 * (i - 2), qspot]
			if i == 0:
				a.follow(apts, spd, "", false)
			else:  # one after another (setting off together they crossed each other's paths)
				var aa := a
				if _alive():
					get_tree().create_timer(0.8 * i).timeout.connect(func():
						if _alive() and is_instance_valid(aa):
							aa.follow(apts, spd, "", false))
		else:
			a.walk_to(qspot, spd, "")
	var piped := bool(st.get("pipeline", false)) and bool(st.get("climb_steps", false))
	if st.has("approach") and not piped:
		await _wait(0.85 * roles.size())
	for i in roles.size():
		if not _alive():
			return
		if piped and i > 0:
			break  # pipelined: the first at the door opens it; the others finish queueing in _enter_one
		var a := stage.actor(str(roles[i]))
		if a == null:
			continue
		var g := 0.0
		while a.moving() and g < 12.0 and _alive():
			g += await _frame()
	if not _alive():
		return
	sp.open_door(true)
	if sound:
		sound.step("go_inside", "door_open", sp.door_point(true, toward))
	await _wait(0.35)
	if not _alive():
		return
	if st.get("door_clear", false):  # the door swings fully clear before anyone steps in
		var gd := 0.0
		while sp.door_open_amount() < 0.95 and gd < 2.0 and _alive():
			gd += await _frame()
	if st.get("pipeline", false) and st.get("climb_steps", false):
		# (2026-11-24 witch_candy pace) the next one steps up while the one before is over the sill: a tidy file
		# through the door, no one standing still waiting for the last to reach its mark
		for i in roles.size():
			if not _alive():
				return
			var a := stage.actor(str(roles[i]))
			if a == null:
				continue
			_enter_one(a, str(roles[i]), st, sp, toward, front, spd, i)
			var gp := 0.0
			while _alive() and gp < 8.0 and not a.get_meta("entered_sill", false):
				gp += await _frame()
		var gw := 0.0
		while _alive() and gw < 10.0:
			var busy := false
			for r in roles:
				var ar := stage.actor(str(r))
				if ar and not ar.get_meta("entered_door", true):
					busy = true
			if not busy:
				break
			gw += await _frame()
		if not _alive():
			return
		sp.open_door(false)
		if sound:
			sound.step("go_inside", "door_shut", sp.door_point(true, toward))
		await _wait(0.35)
		while _line_busy and _alive():
			await _frame()
		return
	for i in roles.size():
		if not _alive():
			return
		var a := stage.actor(str(roles[i]))
		if a == null:
			continue
		if i > 0:  # step up to the doorway (moving away from the camera: back view)
			a.walk_to(front, spd * 0.8, "")
			var g2 := 0.0
			while a.moving() and g2 < 6.0 and _alive():
				g2 += await _frame()
		if not _alive():
			return
		if st.get("climb_steps", false):
			# up the steps onto the sill (feet follow the step height), over the threshold, a step down inside
			var sill := sp.door_sill()
			var fr: Vector3 = sp.door_point(true, toward)
			var bk: Vector3 = sp.door_point(false, toward)
			a.follow([fr - toward * 0.06 + Vector3.UP * sill * 0.5, fr - toward * 0.1 + Vector3.UP * sill,
				bk + Vector3.UP * sill, bk - toward * 0.08 + Vector3.UP * 0.02], spd * 0.7, "", true)
		else:
			a.walk_to(sp.door_point(false, toward), spd * 0.8, "")
		var g3 := 0.0
		while a.moving() and g3 < 6.0 and _alive():
			g3 += await _frame()
		if not _alive():
			return
		if st.has("to"):  # room: true (witch_candy): they walk on into the room to their spots (no window faces)
			var tos: Dictionary = st["to"]
			if tos.has(str(roles[i])):
				var vias: Dictionary = st.get("via", {})
				if vias.has(str(roles[i])):  # round the furniture (the pot) to the mark: one spot or a list
					var vv: Variant = vias[str(roles[i])]
					var vp: Array = []
					for q in (vv if vv is Array else [vv]):
						vp.append(stage.spot_point(q))
					vp.append(stage.spot_point(tos[str(roles[i])]))
					a.follow(vp, spd * 0.8, "", false)
				else:
					a.walk_to(stage.spot_point(tos[str(roles[i])]), spd * 0.8, "")
			continue
		stage.put_inside(str(roles[i]), house, int(wins[i]) if i < wins.size() else 0)
	if st.get("keep_open", false):  # wolf_goats: the wolf leaves the door standing open behind him
		while _line_busy and _alive():
			await _frame()
		return
	if not _alive():
		return
	sp.open_door(false)
	if sound:
		sound.step("go_inside", "door_shut", sp.door_point(true, toward))
	await _wait(0.35)
	while _line_busy and _alive():
		await _frame()


## One actor of a pipelined go_inside: up to the doorway, up the steps, over the sill, on to its mark in the room.
## Meta entered_sill: over the threshold (the next may step up); entered_door: inside and walking to its mark.
func _enter_one(a: StoryActor, role: String, st: Dictionary, sp: SetPiece, toward: Vector3, front: Vector3, spd: float, i: int) -> void:
	a.set_meta("entered_sill", false)
	a.set_meta("entered_door", false)
	if i > 0:
		var gq := 0.0
		while (a.moving() or gq < 0.1) and gq < 8.0 and _alive() and is_instance_valid(a):  # done queueing first
			gq += await _frame()
		if not _alive() or not is_instance_valid(a):
			return
		a.walk_to(front, spd * 0.8, "")
		var g2 := 0.0
		while a.moving() and g2 < 6.0 and _alive():
			g2 += await _frame()
	if not _alive() or not is_instance_valid(a):
		return
	var sill := sp.door_sill()
	var fr: Vector3 = sp.door_point(true, toward)
	var bk: Vector3 = sp.door_point(false, toward)
	a.follow([fr - toward * 0.06 + Vector3.UP * sill * 0.5, fr - toward * 0.1 + Vector3.UP * sill,
		bk + Vector3.UP * sill, bk - toward * 0.08 + Vector3.UP * 0.02], spd * 0.7, "", true)
	var g3 := 0.0
	while a.moving() and g3 < 6.0 and _alive() and is_instance_valid(a):
		if a._path.size() <= 1:
			a.set_meta("entered_sill", true)
		g3 += await _frame()
	if not _alive() or not is_instance_valid(a):
		return
	a.set_meta("entered_sill", true)
	a.set_meta("entered_door", true)
	var tos: Dictionary = st.get("to", {})
	if tos.has(role):
		var vias: Dictionary = st.get("via", {})
		if vias.has(role):
			var vv: Variant = vias[role]
			var vp: Array = []
			for q in (vv if vv is Array else [vv]):
				vp.append(stage.spot_point(q))
			vp.append(stage.spot_point(tos[role]))
			a.follow(vp, spd * 0.8, "", false)
		else:
			a.walk_to(stage.spot_point(tos[role]), spd * 0.8, "")
	else:
		stage.put_inside(role, str(st.get("house", "house")), 0)


## climb {who, on (set piece), path [[x, y] in set heights from its base centre], pose, speed, line}.
func _step_climb(st: Dictionary) -> void:
	var a := stage.actor(str(st["who"]))
	var sp := stage.set_piece(str(st.get("on", "house")))
	if a == null or sp == null:
		return
	var pts: Array = []
	var right := stage.dir_vec("right")
	var toward := stage.dir_vec("toward")
	for q: Array in st.get("path", []):
		var z := float(q[2]) if q.size() > 2 else 0.04
		pts.append(sp.global_position + right * float(q[0]) * sp.height + Vector3.UP * float(q[1]) * sp.height + toward * z)
	a.follow(pts, float(st.get("speed", 0.14)), str(st.get("pose", "")))
	if st.has("pose"):
		a.pose = str(st["pose"])
	if st.has("line"):
		_say.bind(str(st["line"])).call()
	await _wait_actors([str(st["who"])])
	if st.get("sink", false):
		# into the chimney: the card squashes down onto its feet (its base stays on the chimney top), gone
		a.pop_delay = 0.0
		a.pop_target = 0.02
		await _wait(0.7)


## tap_each {targets, prompt, hint, react{role: [pose, fx]}, lines}: every target once, in any order.
func _frame_first(targets: Array) -> void:
	if stage and is_instance_valid(stage) and stage.frame_targets(targets):
		await _wait(maxf(1.2, stage.cam_settle_left()))  # the camera lands on the targets before the prompt


func _step_tap_each(st: Dictionary) -> void:
	await _frame_first(st.get("targets", []))
	await _say(str(st.get("prompt", "")))
	var left: Array = (st.get("targets", []) as Array).duplicate()
	var react: Dictionary = st.get("react", {})
	while not left.is_empty() and _alive():
		var hit := await _wait_tap(left, str(st.get("hint", "")))
		if not _alive():
			return
		left.erase(hit)
		var a := stage.actor(hit)
		var r: Array = react.get(hit, [])
		if a:
			a.hop_v = 0.9
			if r.size() > 0:
				a.set_pose(str(r[0]))
		for k in range(1, r.size()):
			stage.fx(str(r[k]))
		await _wait(0.3)
	await _say_lines(st.get("lines", []))


## tap_steps {target, prompt, hint, steps[{target?, fx, lines, next}]}: one tap per step (generalised shine).
func _step_tap_steps(st: Dictionary) -> void:
	var first: Array = st.get("steps", [{}])
	await _frame_first([str((first[0] as Dictionary).get("target", st.get("target", "")))] if not first.is_empty() else [])
	await _say(str(st.get("prompt", "")))
	for s: Dictionary in st.get("steps", []):
		if not _alive():
			return
		var tg := str(s.get("target", st.get("target", "")))
		var hit := await _wait_tap([tg], str(st.get("hint", "")))
		if not _alive():
			return
		stage.wiggle(hit)
		stage.fx(str(s.get("fx", "")))
		await _wait(float(s.get("wait", 0.5)))
		await _say_lines(s.get("lines", []))
		if s.has("next"):
			await _say(str(s["next"]))


## build {house, target, taps, hint, walker, fx, counter, steps[{at, fx, lines}]}: tap by tap the house's bands fold up
## (band k after k·taps/bands taps); the tale fx shows the work (carrying, hammering, a brick flying on).
func _step_build(st: Dictionary) -> void:
	var house := str(st.get("house", "house"))
	var sp := stage.set_piece(house)
	var taps := int(st.get("taps", 3))
	var at_steps: Dictionary = {}
	for s: Dictionary in st.get("steps", []):
		at_steps[int(s["at"])] = s
	stage.build_ctx = {"house": house, "walker": str(st.get("walker", "")), "tap": 0, "taps": taps,
		"target": str(st.get("target", house)), "pile": str(st.get("pile", "pile"))}
	# frame once for the whole build (the finished house, pile and builder), held for every tap
	if _framed_house != house:
		stage.frame_build(house, [str(st.get("target", house)), str(st.get("pile", "pile"))] + ([str(st["walker"])] if st.has("walker") else []))
		await _wait(1.2)
	_framed_house = ""
	if st.has("prompt"):
		await _say(str(st["prompt"]))
	var shown0 := sp.shown if sp else 0  # bands already standing (a foundation) are not rebuilt
	for i in range(1, taps + 1):
		if not _alive():
			return
		await _wait_tap([str(st.get("target", house))], str(st.get("hint", "")), [], true, false)
		if not _alive():
			return
		stage.build_ctx["tap"] = i
		if sp:
			var n := shown0 + ceili(float(i) * (sp.band_count() - shown0) / taps)
			sp.bands_up(n, 0.08)
		stage.fx(str(st.get("fx", "")))
		if st.get("counter", false):
			stage.show_counter(i, house)
		if at_steps.has(i):
			var s2: Dictionary = at_steps[i]
			stage.fx(str(s2.get("fx", "")))
			if s2.has("wait_for"):  # the speakers walk into the frame first (SPEAKER_OFF: no line from off the frame)
				var g := 0.0
				while g < 8.0 and _alive():
					var all_in := true
					for r in s2["wait_for"]:
						if stage.speaker_state(str(r)) != "":
							all_in = false
					if all_in:
						break
					g += await _frame()
			await _say_lines(s2.get("lines", []))
		await _wait(float(st.get("gap", 0.45)))
	if st.get("counter", false):
		await _wait(0.6)
		stage.hide_counter()


## huff {house, taps, target (wolf), prompt, hint, fx, counter, result: blow_apart | collapse | hold, ruin}:
## each tap is one 후~ from the wolf; blow_apart peels the bands off from the top, collapse rocks the house harder
## and harder until it tumbles, hold only shivers it. The ruin card pops up where the house stood.
func _step_huff(st: Dictionary) -> void:
	var house := str(st.get("house", "house"))
	var sp := stage.set_piece(house)
	var taps := int(st.get("taps", 3))
	var who := str(st.get("who", "wolf"))
	var wolf := stage.actor(who)
	var result := str(st.get("result", "hold"))
	if wolf and sp:
		wolf.face_point(sp.global_position)
	await _frame_first([str(st.get("target", who))])
	if st.has("prompt"):
		await _say(str(st["prompt"]))
	stage.build_ctx = {"house": house, "walker": who, "tap": 0, "taps": taps, "result": result}
	for i in range(1, taps + 1):
		if not _alive():
			return
		await _wait_tap([str(st.get("target", who))], str(st.get("hint", "")))
		if not _alive():
			return
		stage.build_ctx["tap"] = i
		if wolf:
			wolf.set_pose(str(st.get("huff_pose", "huff")))
			wolf.hop_v = 0.35
		stage.fx(str(st.get("fx", "")))
		stage.shake(float(st.get("shake", 0.9)))
		if i == taps and st.has("cam_result"):
			stage.shot_to(str(st["cam_result"]), st.get("cam_result_at", null), {"rate": 3.5})
		if sp:
			match result:
				"blow_apart":
					if i < taps:
						# the roof goes first; after that the walls only rock (whoever is inside stays hidden
						# until the last huff blows everything away)
						if sp.shown >= sp.band_count() and sp.band_count() > 1:
							sp.band_down(sp.shown - 1, 0.1)
						sp.wobble(0.12 + 0.05 * i)
					else:
						sp.collapse(0.05)
						stage.fx("pop:" + str(st.get("ruin", "")))
						if _alive():
							get_tree().create_timer(0.45).timeout.connect(func():
								if _alive() and stage and is_instance_valid(stage):
									stage.reveal_inside(house))
				"collapse":
					if i < taps:
						sp.wobble(0.05 + 0.06 * i)
					else:
						sp.wobble(0.4)
						sp.collapse(0.25)
						stage.fx("pop:" + str(st.get("ruin", "")))
						if _alive():
							get_tree().create_timer(0.7).timeout.connect(func():
								if _alive() and stage and is_instance_valid(stage):
									stage.reveal_inside(house))
				_:
					sp.shiver(0.6)
		if st.get("counter", false):
			stage.show_counter(i, house)
		await _wait(float(st.get("gap", 0.55)))
	if st.get("counter", false):
		await _wait(0.6)
		stage.hide_counter()


func _step_cover(st: Dictionary, b: Dictionary) -> void:
	_mode = "cover"
	ui.show_cover(str(data.get("title", b.get("title", ""))))
	# picked on the bookshelf table: the reader already chose this book, it opens at once (no prompt)
	var picked := Engine.has_meta("popup_open_now")
	if picked:
		Engine.remove_meta("popup_open_now")
	await _wait(0.6)
	if not picked:
		_say.bind(str(st.get("prompt", ""))).call()
	_tapped = ""
	var idle := 0.0
	while _tapped != "book" and _alive():
		idle += await _frame()
		if not _alive():
			return
		if (autoplay and idle > 2.6) or (picked and idle > 0.15):
			_auto_tap("book")
	if not _alive():
		return
	_skip = true
	if sound:
		sound.step("cover", "on_open")
	_mode = "opening"
	ui.open_cover()  # the board swings over the spine, the camera pushes into the title page
	while (_line_busy or ui.cover_opening()) and _alive():
		await _frame()
	_mode = "idle"


func _step_blow(st: Dictionary) -> void:
	await _say(str(st.get("prompt", "")))
	_blow_target = str(st.get("target", "wind"))
	_mode = "blow"
	_auto_cycle = 0.0
	var steps: Array = st.get("steps", [])
	var amount := 0.0
	var idle := 0.0
	var k := 0
	var hints := 0
	ui.pointer_source = func(): return _pointer_at(_blow_target)
	while k < steps.size() and _alive():
		var dt: float = await _frame()
		if not _alive():
			return
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
	var tg := str(st.get("target", "sun"))
	for s: Dictionary in st.get("steps", []):
		if not _alive():
			return
		await _wait_tap([tg], str(st.get("hint", "")))
		if not _alive():
			return
		stage.wiggle(tg)
		stage.fx(str(s.get("fx", "")))
		await _say_lines(s.get("lines", []))
		if s.has("next"):
			await _say(str(s["next"]))


func _step_quiz(st: Dictionary) -> void:
	var answer := str(st.get("answer", "sun"))
	var wrong: Dictionary = st.get("wrong", {})
	ui.hide_flashes()
	var targets: Array = st.get("choices", ["sun", "wind"])
	ui.show_choices(targets)
	_choosing = true
	await _say(str(st.get("prompt", "")))
	var order: Array = []
	if autoplay:
		order = wrong.keys() + [answer]  # autoplay shows the wrong path once, then answers
	var tried := 0
	while _alive():
		var hit := await _wait_tap(targets, "", [order[mini(tried, order.size() - 1)]] if autoplay else [], false)
		if not _alive():
			return
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
		if not _alive():
			return
		await _wait_tap([str(st.get("target", "wind"))], str(st.get("hint", "")))
		if not _alive():
			return
		stage.fx(str(st.get("fx", "gentle_gust")))
		await _wait(0.6)
	await _say_lines(st.get("lines", []))


func _step_end(st: Dictionary) -> void:
	await _say(str(st.get("line", "")))
	var book := ui.has_book() and stage != null and is_instance_valid(stage)
	if book:
		await _ending_book()
	elif st.get("close_book", false) and stage and is_instance_valid(stage):
		if sound:
			sound.step("end", "close_book")
		var t := stage.fold()
		await _wait(t + 0.8)
	_mode = "end"
	ui.show_end("")
	if not book:
		ui.sparkle(Vector2(683, 300))
	await _wait(0.6)
	await _say(str(st.get("after", "")))
	if autoplay:
		await _wait(2.5)
		ui.ripple(ui.end_button_pos())
		await _wait(0.4)
	_mode = "idle"


## The ending (game/story/COVER_PLAN.md "ENDING"): hold the last tableau, a curtain call of the cast, the pop-up folds
## down, the page turns back onto the title page, the book closes and turns over onto its back cover (the epilogue
## picture with a cut-paper "끝"); then the end tabs ("다시 보기", "다른 동화") lie beside it.
func _ending_book() -> void:
	ui.hide_line()
	ui.pointer_source = Callable()
	# 1. hold: the last tableau stays a moment, no prompt
	if sound:
		sound.set_music("ending")  # the settle / closing music (plays once, fades on replay)
	var cc: Dictionary = data.get("ui", {}).get("curtain", {})
	if cc.has("shot"):  # the camera eases onto the cast during the hold (the tale may have pulled back to a wide)
		stage.shot_to(str(cc["shot"]), cc.get("at", null), {"rate": 1.4})
	elif stage.has_walker:
		stage.shot_to("story", null, {"rate": 1.4})
	await _wait(1.5)
	if not _alive():
		return
	# 2. curtain call
	await _curtain_call()
	if not _alive():
		return
	# 3. the page closes: the pieces fold down as the sheet lifts over them, the title page comes round under it
	ui.show_page_title("")
	ui.show_end_book(str(data.get("title", "")), true)  # built hidden: its live view is the page under the sheet
	await _frame()
	if not _alive():
		return
	_fold_by_turn(stage, stage.camera(), TURN_S, TURN_LEAD)
	_squash_unhinged(TURN_LEAD * 0.5)
	await _wait(TURN_LEAD)
	if not _alive():
		return
	ui.page_turn.reveal(ui.book_texture())
	ui.page_turn.turn(TURN_S)
	if sound:
		sound.step("page_turn")
		sound.set_bed(null)  # out of the world: only a quiet room tone at the table
		sound.loop_start("amb.room_fire", "table", 1.5, -16.0)
	while _alive() and ui.page_turn.is_turning() and ui.page_turn.progress < 0.985:
		await _frame()
	if not _alive():
		return
	ui.show_book()  # the same frame the sheet goes: the book (already drawn under the sheet) takes over
	ui.page_turn.finish_now()
	await _wait(0.3)
	ui.close_book(0.42)
	await _wait(1.75)  # the board lands shut at 0.5 + 1.25 s
	if sound:
		sound.step("end", "close_book")
	await _wait(0.5)
	# 4. back cover: the book turns over onto the epilogue picture
	ui.turn_over_book()
	if sound:
		sound.step("page_turn")
	await _wait(1.3)
	if sound:
		sound.step("end", "close_book")
	await _wait(0.6)


func _page_hinges() -> Array:
	return _page_hinges_of(stage)


func _page_hinges_of(st: SpreadStage) -> Array:
	var all: Array = []
	all.append_array(st.world.hinges)
	all.append_array(st.extra_hinges)
	for k in st.sets:
		all.append_array((st.sets[k] as SetPiece).all_hinges())
	return all.filter(func(h): return is_instance_valid(h))


## Set-piece parts that hang on no hinge (house bodies / boxes, rooms, roofs added by tale fx) squash flat with the
## fold wave instead of being left standing on the closed page (user: "마지막에 집 접힐때 왜 안접히는게 있는지").
func _squash_unhinged(delay: float) -> void:
	var nodes: Array = []
	for k in stage.sets:
		_collect_unhinged(stage.sets[k], nodes)
	for n: Node3D in nodes:
		if not n.is_visible_in_tree():
			continue
		var tw := create_tween()
		tw.tween_interval(delay + randf() * 0.3)
		tw.tween_property(n, "scale:y", 0.01, 0.45).set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN)
		tw.tween_callback(n.hide)


func _collect_unhinged(n: Node, out: Array) -> void:
	for c in n.get_children():
		if c is PopHinge:
			continue
		if c is VisualInstance3D:
			out.append(c)
		elif c is Node3D:
			_collect_unhinged(c, out)


## True when every hinge on the page (world, extra, set pieces) has folded down and stopped.
func _all_flat() -> bool:
	for h in _page_hinges():
		var ph := h as PopHinge
		if ph and ph.is_visible_in_tree() and (ph.is_moving() or ph.openness() > 0.03):
			return false
	return true


## Curtain call (ui.curtain {shot, at, who: [[role, pose or cast figure id], ...]}): a wide of the last spread, each
## of the cast does its signature gesture in turn (actors: pose + paper hop; sky hangers: their figure + a bob); a tap
## on one repeats its gesture. ≤ 6 s in autoplay.
func _curtain_call() -> void:
	var cc: Dictionary = data.get("ui", {}).get("curtain", {})
	if cc.is_empty():
		return
	var who: Array = cc.get("who", [])
	for e: Array in who:  # someone who has left the page (the traveller down the road) comes back for the bow
		if str(e[0]) == "walker" and e.size() > 2:
			await _walker_return(float(e[2]))
	var roles: Array = []
	for e: Array in who:
		roles.append(str(e[0]))
		_curtain_gesture(e)
		await _wait(0.5)
	_mode = "curtain"
	_expect = roles
	_tapped = ""
	var left := 1.3 if autoplay else float(cc.get("hold", 3.5))
	while left > 0.0 and _alive():
		left -= await _frame()
		if _tapped != "":
			for e: Array in who:
				if str(e[0]) == _tapped:
					_curtain_gesture(e)
			_tapped = ""
	_expect = []
	_mode = "idle"


## The walker walked `back` along the road out of the shot (walk_away): he re-enters from up the road and stops on a
## mark just in front of where the camera waits.
func _walker_return(back: float) -> void:
	var w: Walker = stage.world.walker
	if w == null or w.path == null:
		return
	var walked := stage.walk_away_back(back)
	var L := w.path.curve.get_baked_length()
	var anchor := w.offset - stage.stroll_dir * walked
	var mark := clampf(anchor + stage.stroll_dir * 0.22, 0.0, L)
	w.offset = clampf(anchor - stage.stroll_dir * 0.75, 0.0, L)
	w.target_offset = w.offset
	await _frame()
	if not _alive():
		return
	stage.walk_to_offset(mark)
	var g := 0.0
	await _frame()
	while _alive() and stage.walking() and g < 5.0:
		g += await _frame()


func _curtain_gesture(e: Array) -> void:
	var r := str(e[0])
	var p := str(e[1]) if e.size() > 1 else ""
	var a := stage.actor(r)
	if a:
		if p != "" and a.has_pose(p):
			a.set_pose(p)
		a.hop_v = 0.7
		return
	var h := stage.hanger(r)
	if h:
		if p.begins_with("cast_"):
			var tx := CastSkins.by_id(p)
			if tx:
				h.set_texture(tx)
		h.push(Vector3(0, 0, 0.35))
		return
	if r == "walker" and p != "":
		stage.set_pose(p)


# ------------------------------------------------------------------ spreads + page turn

func _snapshot(without_ui := false) -> Texture2D:
	if not _alive() or DisplayServer.get_name() == "headless":
		return null
	if without_ui:
		ui.visible = false
		await _frame()
		if not _alive():
			return null
	await RenderingServer.frame_post_draw
	if not _alive() or get_viewport() == null:
		return null
	var tex_vp := get_viewport().get_texture()
	if tex_vp == null:
		return null
	var img := tex_vp.get_image()
	if without_ui:
		ui.visible = true
		if img:
			img.resize(img.get_width() / 2, img.get_height() / 2, Image.INTERPOLATE_BILINEAR)
	return ImageTexture.create_from_image(img) if img else null


func _enter_spread(b: Dictionary) -> void:
	if not _alive():
		return
	var sp: Dictionary = b["spread"]
	var key := _key_of(sp)
	if key == _spread_key and stage:
		await stage.enter_beat(b)  # same page: the next beat's set pieces / light / cast
		if _alive():
			ui.show_page_title(str(b.get("title", "")))
		return
	var had := stage != null and is_instance_valid(stage)
	var pre: Dictionary = _prebuilt.get(key, {})
	ui.hide_line()
	ui.pointer_source = Callable()
	ui.show_page_title("")
	ui.hide_flashes()
	ui.hide_choices()
	# 2026-11-22 (user: "근데 뒤집혀있다 일어서는 이유가 뭐지?" -> a real pop-up tied to the page): the pieces stand up
	# WHILE the page opens and fold down WHILE it closes, each timed to the moment the turning sheet uncovers / covers
	# it on screen; no frame shows a page lying flat or half-popped at rest.
	if had and not pre.is_empty():
		await _turn_live(b, key, pre)
		return
	if had:
		var t := stage.fold()
		await _wait(t + 0.9)
		if not _alive():
			return
	var cover_shown := ui.cover_visible()
	var tex: Texture2D = null
	if had or cover_shown:
		tex = await _snapshot()
		if not _alive():
			return
		if tex:
			ui.page_turn.cover(tex)
		ui.hide_cover()
		await _frame()
		if not _alive():
			return
	if had:
		if stage and is_instance_valid(stage):
			stage.queue_free()
		stage = null
		await _frame()
		if not _alive():
			return
	var t_build := Time.get_ticks_usec()
	if not pre.is_empty():
		var ps: SpreadStage = pre["stage"]
		var wait_t0 := Time.get_ticks_usec()
		var warned := false
		while _alive() and is_instance_valid(ps) and not ps.is_built:  # normally done long ago; otherwise it keeps slicing under the cover
			if not warned and (Time.get_ticks_usec() - wait_t0) > 30_000_000:
				warned = true
				push_warning("StoryRunner: prebuild_wait >30s for %s phases=%s" % [key, str(ps.perf_phases)])
			await _frame()
		if not _alive() or not is_instance_valid(ps):
			return
		var t_move := Time.get_ticks_usec()
		_adopt_prebuilt(ps, pre["vp"], key, b)
		print("PERF spread_prebuilt ", key, " frames=", ps.build_frames, " max_slice_ms=", snappedf(ps.max_slice_ms, 0.1),
			" phases=", ps.perf_phases, " move_ms=", snappedf((Time.get_ticks_usec() - t_move) / 1000.0, 0.1))
	else:
		stage = SpreadStage.new()
		stage.name = "Spread_" + str(b["id"])
		stage.tale = data
		stage.beat = _page_beat(beats.find(b))
		add_child(stage)
		var rt: Array = sp.get("route", [])
		if rt.size() == 2:
			stage.route = Vector2(float(rt[0]), float(rt[1]))
		stage.build(int(sp.get("seed", 1)), int(sp.get("view", 0)), not mute)
		if not _alive():
			return
		print("PERF spread_build ", key, " ms=", snappedf((Time.get_ticks_usec() - t_build) / 1000.0, 0.1))
	stage.set_pose(_pose, true)
	if stage.is_built:
		stage.preset_open(b)  # the opening crane's first framing, set while the page is still hidden (no cut later)
	_spread_key = key
	await _frame()
	await _frame()
	if not _alive():
		return
	var wave_t := 0.0
	if tex:
		# the page rises as the sheet turns: each piece starts so that it stands by the time the fold uncovers it
		wave_t = _pop_by_turn(stage, stage.camera(), TURN_S, TURN_LEAD)
		await _wait(TURN_LEAD)
		if not _alive():
			return
		ui.page_turn.turn(TURN_S)
		if sound and not cover_shown:
			sound.step("page_turn")
		while _alive() and ui.page_turn.is_turning():
			await _frame()
		if not _alive():
			return
	else:
		wave_t = stage.pop(0.0)
	ui.show_page_title(str(b.get("title", "")))
	_prebuild_after(beats.find(b))
	await _wait(clampf(wave_t * 0.6, 0.9, 1.8) if not tex else 0.9)


## Move a prebuilt page out of its waiting SubViewport onto the main stage.
func _adopt_prebuilt(ps: SpreadStage, vp: SubViewport, key: String, b: Dictionary) -> void:
	vp.remove_child(ps)
	ps.name = "Spread_" + str(b["id"])
	add_child(ps)
	vp.queue_free()
	_prebuilt.erase(key)
	stage = ps


## A page turn in the middle of a tale with both pages live: the old page (main view) folds down under the lifting
## sheet, the next page (its prebuild SubViewport, shown right of the fold) pops up as it is uncovered.
func _turn_live(b: Dictionary, key: String, pre: Dictionary) -> void:
	var ps: SpreadStage = pre["stage"]
	var vp: SubViewport = pre["vp"]
	var wait_t0 := Time.get_ticks_usec()
	var warned := false
	while _alive() and is_instance_valid(ps) and not ps.is_built:
		if not warned and (Time.get_ticks_usec() - wait_t0) > 30_000_000:
			warned = true
			push_warning("StoryRunner: turn_live prebuild_wait >30s for %s phases=%s" % [key, str(ps.perf_phases)])
		await _frame()
	if not _alive() or not is_instance_valid(ps) or not is_instance_valid(vp):
		return
	vp.process_mode = Node.PROCESS_MODE_INHERIT
	vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	ps.set_pose(_pose, true)
	ps.preset_open(b)
	await _frame()
	if not _alive():
		return
	_fold_by_turn(stage, stage.camera(), TURN_S, TURN_LEAD)
	_squash_unhinged(TURN_LEAD * 0.5)
	var wave_t := _pop_by_turn(ps, ps.camera(), TURN_S, TURN_LEAD)
	await _wait(TURN_LEAD)
	if not _alive():
		return
	ui.page_turn.reveal(vp.get_texture())
	ui.page_turn.turn(TURN_S)
	if sound:
		sound.step("page_turn")
	while _alive() and ui.page_turn.is_turning() and ui.page_turn.progress < 0.985:
		await _frame()
	if not _alive():
		return
	# swap in one frame: the next page leaves its SubViewport for the main view as the sheet is lifted away
	stage.queue_free()
	stage = null
	_adopt_prebuilt(ps, vp, key, b)
	ui.page_turn.finish_now()
	_spread_key = key
	await _frame()
	ui.show_page_title(str(b.get("title", "")))
	_prebuild_after(beats.find(b))
	await _wait(clampf(wave_t * 0.3, 0.6, 0.9))


const TURN_S := 1.3  ## page turn duration when the pop / fold rides on it
const TURN_LEAD := 0.4  ## pieces start this long before the sheet starts moving (under the full cover)
const RISE_LEAD := 0.38  ## a piece starts rising this long before the fold uncovers it (it stands when seen)
const FOLD_LEAD := 0.5  ## a piece starts folding this long before the sheet's back covers it


## Time into a PageTurn of `dur` s when its progress reaches p (PageTurn.step's easing, inverted numerically).
static func _turn_time(p: float, dur: float) -> float:
	p = clampf(p, 0.0, 1.0)
	var lo := 0.0
	var hi := 1.0
	for it in 18:
		var u := (lo + hi) * 0.5
		var e := u * u * (3.0 - 2.0 * u)
		if lerpf(e, u, 0.25) < p:
			lo = u
		else:
			hi = u
	return lo * dur


static func _sx(cam: Camera3D, p: Vector3, w: float) -> float:
	if cam == null or cam.is_position_behind(p):
		return w * 0.5
	return clampf(cam.unproject_position(p).x / w, 0.0, 1.0)


## Pop a page in step with the page turn about to start (TURN_LEAD from now, `dur` long): a piece at screen x is
## uncovered when the fold line (right -> left) passes it; it starts RISE_LEAD before that. pop_in:false pages stand
## at once (stage.pop snaps them). Returns the last start.
func _pop_by_turn(st: SpreadStage, cam: Camera3D, dur: float, lead: float) -> float:
	st.pop(0.0)
	if not st.tale.get("pop_in", true):
		return 0.5
	var w := float(st.get_viewport().get_visible_rect().size.x)
	var last := 0.0
	var hs: Array = st.world.hinges.duplicate()
	for k in st.sets:
		hs.append_array((st.sets[k] as SetPiece).wave_hinges())
	for h: PopHinge in hs:
		var x := _sx(cam, h.global_position, w)
		var d := maxf(0.0, lead + _turn_time(1.0 - x, dur) - RISE_LEAD + randf() * 0.04)
		h.pop_up(d)
		last = maxf(last, d)
	for role in st.actors:
		var a: StoryActor = st.actors[role]
		if a.has_meta("in_page"):
			a.pop_delay = maxf(0.0, lead + _turn_time(1.0 - _sx(cam, a.global_position, w), dur) - 0.2)
	st.trav_delay = lead + _turn_time(0.5, dur) - 0.3
	return last


## Fold a page in step with the page turn about to start: a piece at screen x is covered by the sheet's back when
## its edge (2f - W) passes x, i.e. at progress (1 - x) / 2; it starts FOLD_LEAD before that. The camera holds its
## shot (stage.fold() would glide to the wide).
func _fold_by_turn(st: SpreadStage, cam: Camera3D, dur: float, lead: float) -> void:
	var keep := st.shot
	st.fold()
	st.shot_to(keep)
	var w := float(st.get_viewport().get_visible_rect().size.x)
	for h in _page_hinges_of(st):
		var ph := h as PopHinge
		if not ph.is_visible_in_tree():
			continue
		var x := _sx(cam, ph.global_position, w)
		ph.fold_down(maxf(0.0, lead + _turn_time((1.0 - x) * 0.5, dur) - FOLD_LEAD))
	for role in st.actors:
		var a: StoryActor = st.actors[role]
		a.pop_delay = maxf(0.0, lead + _turn_time((1.0 - _sx(cam, a.global_position, w)) * 0.5, dur) - 0.4)
		a.pop_target = 0.02
	st.trav_delay = 0.0
	if st.world and st.world.walker and st.world.walker.visible:
		st.trav_delay = maxf(0.0, lead + _turn_time((1.0 - _sx(cam, st.traveller_pos(), w)) * 0.5, dur) - 0.4)


# ------------------------------------------------------------------ perf: spread prebuild

## The beat a page is built for, with the set pieces and spots of the earlier beats on the same page merged in
## (a story started with --beat in the middle of a shared page still has the house the first beat put there).
func _page_beat(i: int) -> Dictionary:
	var b: Dictionary = beats[i]
	if not b.get("spread") is Dictionary:
		return b
	var key := _key_of(b["spread"])
	var j := i
	while j > 0 and beats[j - 1].get("spread") is Dictionary and _key_of(beats[j - 1]["spread"]) == key:
		j -= 1
	if j == i:
		return b
	var m: Dictionary = b.duplicate(true)
	var sets: Array = []
	var spots: Dictionary = {}
	for k in range(j, i + 1):
		var sp: Dictionary = beats[k]["spread"]
		sets.append_array(sp.get("set", []))
		spots.merge(sp.get("spots", {}), true)
	m["spread"]["set"] = sets
	m["spread"]["spots"] = spots
	return m


## Page key: consecutive beats with the same key share one page (sun_wind: seed:view; tales with places add it).
static func _key_of(sp: Dictionary) -> String:
	var k := "%d:%d" % [int(sp.get("seed", 1)), int(sp.get("view", 0))]
	if sp.has("place"):
		k += ":" + str(sp["place"])
	return k


## Start building the first spread after beat index i that differs from the one on screen (no-op if already going).
## It lives in an off-screen SubViewport with its own World3D (its camera, lights and environment do not touch the
## page on screen; nothing is rendered there) until _enter_spread moves it into the story.
## Not in fixed-step runs (captures, recordings): there each spread is built at its page turn exactly as before, so
## the global RNG sequence (hinge jitter, gusts) and every frame stay reproducible.
const SHELF_SCENE := "res://story/shelf.tscn"
var _movie: bool = Engine.get_write_movie_path() != ""
var end_choice := ""  ## --end-choice=replay|other (recordings of the end tabs)


func _go_shelf() -> void:
	if _exiting:
		return
	_leaving = true
	_exiting = true
	if sound:
		sound.loop_stop("table", 0.3)
	Engine.set_meta("popup_from_story", true)  # the shelf stays (command-line args would send it back to a story)
	var tree := get_tree()
	if tree:
		tree.change_scene_to_file(SHELF_SCENE)
const COVER_BUILD_MS := 28.0  ## the cover is a still page: build the first spread fast behind it


func _prebuild_after(i: int, budget_ms := PREBUILD_BUDGET_MS) -> void:
	if fixed_step:
		return
	if _movie:
		# movie maker (recordings): a frame's wall time never reaches the video, so build the next page in one go.
		# A wall-time budget per frame made the build take story time when the machine was slow: the patjuk gate v1b
		# recording froze 14 min on the cover (disk 99 % full, every 28 ms slice did almost nothing).
		budget_ms = 0.0
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
		st.tale = data
		st.beat = _page_beat(j)
		var rt: Array = sp.get("route", [])
		if rt.size() == 2:
			st.route = Vector2(float(rt[0]), float(rt[1]))
		vp.add_child(st)
		_prebuilt[key] = {"stage": st, "vp": vp}
		st.build_async(int(sp.get("seed", 1)), int(sp.get("view", 0)), not mute, budget_ms)
		return


## perf: trace every traveller figure print ahead (a few ms per frame), so a pose change mid-page (coat open, fan,
## coat off, hat back) only builds its card meshes instead of tracing new outlines in that frame (30-45 ms hitches).
const CAST_RIG_DIR := "res://art/cast/rig/"
var _cast_textures: Array[Texture2D] = []  ## kept loaded: a pose swap must not decode its figure from disk either


func _warm_cast() -> void:
	if not _cast_textures.is_empty() or not _alive():
		return
	var sl := BuildSlicer.new(2.0, get_tree())
	var prefixes: Array = []
	for role in (data.get("cast", {}) as Dictionary):
		var cfg: Dictionary = data["cast"][role]
		if str(cfg.get("kind", "")) in ["walker", "actor"]:
			prefixes.append("cast_" + str(cfg.get("skin", role)) + "_" if str(cfg.get("kind")) == "actor" else "cast_" + str(cfg.get("skin", role)))
	for f in ResourceLoader.list_directory(CAST_RIG_DIR):
		if not _alive():
			return
		var ok := false
		for pf in prefixes:
			if f.begins_with(str(pf)) and f.ends_with(".png"):
				ok = true
		if not ok:
			continue
		var tex := load(CAST_RIG_DIR + f) as Texture2D
		if tex:
			_cast_textures.append(tex)
			PaperCard.warm(tex)
		await sl.tick()
		if not _alive():
			return
	for cast: String in (CastSkins.CAST_IDS if data.get("cast", {}).has("sun") else {}):
		for variant: String in CastSkins.CAST_IDS[cast]:
			if not _alive():
				return
			var tex := CastSkins.texture(cast, variant)
			if tex:
				_cast_textures.append(tex)
				PaperCard.warm(tex)
			await sl.tick()
			if not _alive():
				return
	for role in (data.get("cast", {}) as Dictionary):
		var cfg: Dictionary = data["cast"][role]
		if str(cfg.get("kind", "")) != "actor":
			continue
		var d := CastPuppet.skin_def(str(cfg.get("skin", role)))
		for id in (d.get("paths", {}) as Dictionary):
			if not _alive():
				return
			var tex := load(str(d["paths"][id])) as Texture2D
			if tex:
				_cast_textures.append(tex)
				PaperCard.warm(tex)
			await sl.tick()
			if not _alive():
				return
	print("PERF cast_warm textures=", _cast_textures.size(), " frames=", sl.frames)

