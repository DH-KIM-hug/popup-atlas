class_name AppState
extends RefCounted
## The app's own small saved state (docs/APP_UI_PLAN.md): settings, purchases, child names. One JSON file on this
## device (user://app/state.json); no login, no server, nothing personal leaves the device in this build.
##
## Command-line story runs (recordings, regressions, probes: any user args) never read or write it, so a name or a
## setting chosen while testing the app cannot change another agent's run. `--app-state=<path>` (shelf / screenshot
## runs) uses another file; `--app-fresh` starts from defaults without saving.

const PATH := "user://app/state.json"
const DEFAULTS := {
	"v": 1,
	"subtitles": true,
	"music": true,
	"sfx": true,
	"owned": false,  ## 모든 동화 열기 (non-consumable; restored from the store)
	"run_until": 0,  ## unix time: a bought 아이 이름 변경권 (it starts at once) lets the parent set / redo names in every creative tale until then (48 h)
	"first_used": [],  ## creative tales whose free first name setup (part of 모든 동화 열기) is used
	"names": {},  ## tale -> {"A": "지우", "on": true, "got": {line id: "user://..."}, "done": false}
}

static var _d: Dictionary = {}
static var _loaded := false
static var _path := PATH
static var _volatile := false


## True when the process runs a story from the command line (another agent's recording / regression), unless the
## run is an app-shell run (`--app-*` args only).
static func cli_story_run() -> bool:
	for a in OS.get_cmdline_user_args():
		var s := str(a)
		if not s.begins_with("--app-") and not s.begins_with("--shelf-"):
			return true
	return false


static func _load() -> void:
	if _loaded:
		return
	_loaded = true
	_d = DEFAULTS.duplicate(true)
	for a in OS.get_cmdline_user_args():
		var s := str(a)
		if s.begins_with("--app-state="):
			_path = s.get_slice("=", 1)
		elif s == "--app-fresh":
			_volatile = true
	if cli_story_run():
		_volatile = true
		return
	if _volatile or not FileAccess.file_exists(_path):
		return
	var v: Variant = JSON.parse_string(FileAccess.get_file_as_string(_path))
	if v is Dictionary:
		for k in v:
			_d[k] = v[k]


static func save() -> void:
	_load()
	if _volatile:
		return
	DirAccess.make_dir_recursive_absolute(_path.get_base_dir())
	var f := FileAccess.open(_path, FileAccess.WRITE)
	if f:
		f.store_string(JSON.stringify(_d, " "))


static func get_v(key: String, def: Variant = null) -> Variant:
	_load()
	return _d.get(key, DEFAULTS.get(key, def))


static func set_v(key: String, value: Variant) -> void:
	_load()
	_d[key] = value
	save()


static func tale_names(tale: String) -> Dictionary:
	_load()
	var n: Dictionary = _d.get("names", {})
	return n.get(tale, {})


static func set_tale_names(tale: String, cfg: Dictionary) -> void:
	_load()
	var n: Dictionary = _d.get("names", {})
	n[tale] = cfg
	_d["names"] = n
	save()
