class_name TaleList
extends RefCounted
## The tales on the bookshelf (res://app/tales.json + every story folder that is ready). A tale is ready when
## res://stories/<id>/story.tscn and script.json both exist, so a tale another agent is still building appears by
## itself once those land (or set "hidden": true in tales.json to hold it back). Order: tales.json, then the rest.

const LIST := "res://app/tales.json"
const STORIES := "res://stories"

static var _cfg: Array = []


static func _entries() -> Array:
	if _cfg.is_empty():
		var v: Variant = JSON.parse_string(FileAccess.get_file_as_string(LIST)) if FileAccess.file_exists(LIST) else null
		_cfg = (v as Dictionary).get("tales", []) if v is Dictionary else []
	return _cfg


static func ready_id(id: String) -> bool:
	return ResourceLoader.exists("%s/%s/story.tscn" % [STORIES, id]) and FileAccess.file_exists("%s/%s/script.json" % [STORIES, id])


## [{id, title, kind, free, name_slots, default_names, ...}] in shelf order.
static func tales() -> Array:
	var out: Array = []
	var seen := {}
	for e: Dictionary in _entries():
		var id := str(e.get("id", ""))
		seen[id] = true
		if id == "" or bool(e.get("hidden", false)) or not ready_id(id):
			continue
		out.append(_with_title(e.duplicate()))
	var d := DirAccess.open(STORIES)
	if d:
		var extra: Array = []
		for sub in d.get_directories():
			if not seen.has(sub) and ready_id(sub):
				extra.append(sub)
		extra.sort()
		for id in extra:
			out.append(_with_title({"id": id, "kind": "classic", "free": false}))
	return out


static func _with_title(e: Dictionary) -> Dictionary:
	if not e.has("title"):
		var p := "%s/%s/script.json" % [STORIES, e["id"]]
		var v: Variant = JSON.parse_string(FileAccess.get_file_as_string(p))
		e["title"] = str((v as Dictionary).get("title", e["id"])) if v is Dictionary else str(e["id"])
	return e


static func entry(id: String) -> Dictionary:
	for e: Dictionary in _entries():
		if str(e.get("id", "")) == id:
			return e
	return {}


static func default_names(id: String) -> Dictionary:
	return entry(id).get("default_names", {})


static func originals() -> Array:
	return tales().filter(func(e): return str(e.get("kind", "")) == "original")
