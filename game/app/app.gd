extends Node
## Autoload "App" (docs/APP_UI_PLAN.md): the shell around a tale the reader opened from the bookshelf.
## In a story scene started from the shelf it adds the paper "책장" button (top right, beside 자막; back to the
## shelf at once) and applies the parent's settings (자막 / 배경 음악 / 효과음, AppState). Command-line story runs
## (another agent's recordings, regressions) are left exactly as they were: no button, no settings.

var _layer: CanvasLayer
var _runner: StoryRunner


func _ready() -> void:
	get_tree().scene_changed.connect(_on_scene)
	# screenshot hook for the app-shell sheets: --app-capture=<png> [--app-capture-at=<seconds>] saves the window, quits
	var cap := ""
	var at := 4.0
	for a in OS.get_cmdline_user_args():
		if str(a).begins_with("--app-capture="):
			cap = str(a).get_slice("=", 1)
		elif str(a).begins_with("--app-capture-at="):
			at = float(str(a).get_slice("=", 1))
	if cap != "":
		get_tree().create_timer(at).timeout.connect(func():
			await RenderingServer.frame_post_draw
			get_viewport().get_texture().get_image().save_png(cap)
			print("APP_CAPTURE ", cap)
			get_tree().quit())


func _on_scene() -> void:
	_runner = null
	if _layer:
		_layer.queue_free()
		_layer = null
	var launched := Engine.has_meta("popup_app_launch")
	if launched:
		Engine.remove_meta("popup_app_launch")
	if AppState.cli_story_run() or not launched:
		return
	var sc := get_tree().current_scene
	if sc == null:
		return
	_runner = _find_runner(sc)
	if _runner == null:
		return
	_add_home(sc)
	_apply_settings.call_deferred()
	get_tree().create_timer(0.6).timeout.connect(_apply_settings)


func _find_runner(n: Node) -> StoryRunner:
	if n is StoryRunner:
		return n
	for c in n.get_children():
		var r := _find_runner(c)
		if r:
			return r
	return null


func _apply_settings() -> void:
	if _runner == null or not is_instance_valid(_runner):
		return
	var subs := bool(AppState.get_v("subtitles", true))
	_runner.subtitles = subs
	if _runner.ui:
		_runner.ui.subtitles = subs
		if not _runner.ui.subtitles_toggled.is_connected(_on_subs):
			_runner.ui.subtitles_toggled.connect(_on_subs)
	for bus in ["Music"]:
		_mute(bus, not bool(AppState.get_v("music", true)))
	for bus in ["SFX", "Ambience"]:
		_mute(bus, not bool(AppState.get_v("sfx", true)))


func _on_subs(on: bool) -> void:
	AppState.set_v("subtitles", on)


func _mute(bus: String, m: bool) -> void:
	var i := AudioServer.get_bus_index(bus)
	if i >= 0:
		AudioServer.set_bus_mute(i, m)


func _add_home(sc: Node) -> void:
	_layer = CanvasLayer.new()
	_layer.name = "AppChrome"
	_layer.layer = 25
	sc.add_child(_layer)
	var b := AppTheme.button("책장", "plain", 128, 24)
	b.name = "Home"
	_layer.add_child(b)
	var place := func():
		if not is_instance_valid(b):
			return
		var vis := get_viewport().get_visible_rect().size
		var win := Vector2(DisplayServer.window_get_size())
		var sc_f := DisplayServer.screen_get_scale() if OS.has_feature("mobile") else 1.0
		var u := vis.x / maxf(1.0, win.x / sc_f)
		b.scale = Vector2(u, u)
		b.size = Vector2(128, AppTheme.TAP)
		# StoryUI's 자막 button spans x = W-210 .. W-28, y = 24 .. 88 (canvas px); this sits to its left
		b.position = Vector2(vis.x - 226.0 - 128.0 * u, 24.0)
	place.call()
	get_viewport().size_changed.connect(place)
	b.pressed.connect(func():
		if _runner and is_instance_valid(_runner) and _runner.ui:
			_runner.ui.other_pressed.emit())  # the runner's own way back to the shelf (stops the table loop)
