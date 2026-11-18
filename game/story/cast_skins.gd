class_name CastSkins
extends RefCounted
## Skin lookup for story cast members (component E). Stories ask for a cast id + variant
## ("wind", "blow") and never hard-code art paths, so the shared cast library (game/art/cast/**,
## made by the cast owner) drops in by id later without touching the story code.
##
## Lookup order for texture(cast, variant):
##  1. res://art/cast/catalog.json: an entry whose `cast` == cast and `variant` == variant, or whose id is
##     "<cast>_<variant>" / "cast_<cast>_<variant>" (variant "default" also matches the bare "<cast>" id).
##  2. The placeholder table below (톡톡 design-reference art in res://art/chars/, D's rig for the traveller).
## The traveller is a PaperPuppet (D's rig, poses walk/walk_nohat/hold/shirt/fan/sit). `puppet_kind()`
## reports which rig to build; a cast rig can be added here when the cast library ships one.

const CAST_CATALOG := "res://art/cast/catalog.json"
## r2: story cast member + variant -> shared cast library id (game/art/cast/catalog.json, 2026-11-18 cast owner).
## Checked by eye on the cast contact sheet; the lookup still falls back to the placeholders when an id is missing.
const CAST_IDS := {
	"sun": {"default": "cast_sun_smile", "proud": "cast_sun_proud", "beaming": "cast_sun_beaming"},
	"wind": {"default": "cast_wind_boast", "blow": "cast_wind_blow", "tired": "cast_wind_tired"},
	"hat": {"default": "cast_hat", "ground": "cast_hat_ground"},
	"coat": {"default": "cast_coat_ground", "arm": "cast_coat_folded", "hung": "cast_coat_hung"},
	"traveller": {"default": "cast_traveller_coat", "shirt": "cast_traveller_nocoat", "face": "cast_traveller_nocoat"},
}
const PLACEHOLDER := {
	"sun": {"default": "res://art/chars/sw_sun.webp"},
	"wind": {"default": "res://art/chars/sw_wind.webp", "blow": "res://art/chars/sw_wind_blow.webp",
		"tired": "res://art/chars/sw_wind_tired.webp"},
	"hat": {"default": "res://art/chars/sw_hat.webp"},
	"coat": {"default": "res://art/chars/sw_coat.webp"},
	"traveller": {"default": "res://art/chars/sw_trav_walk.webp"},
}

static var _catalog: Dictionary = {}  ## id -> entry
static var _loaded := false
static var _tex: Dictionary = {}


static func _load() -> void:
	if _loaded:
		return
	_loaded = true
	if not FileAccess.file_exists(CAST_CATALOG):
		return
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(CAST_CATALOG))
	var arr: Array = []
	if parsed is Array:
		arr = parsed
	elif parsed is Dictionary and (parsed as Dictionary).get("cards") is Array:
		arr = (parsed as Dictionary)["cards"]
	for e: Variant in arr:
		if e is Dictionary and (e as Dictionary).has("id") and (e as Dictionary).has("path"):
			_catalog[str(e["id"])] = e


## Resource path for a cast member's print, or "" when there is none.
static func path(cast: String, variant := "default") -> String:
	_load()
	var cid := str((CAST_IDS.get(cast, {}) as Dictionary).get(variant, ""))
	if cid != "" and _catalog.has(cid):
		var cp := str(_catalog[cid]["path"])
		cp = cp if cp.begins_with("res://") else "res://" + cp
		if ResourceLoader.exists(cp):
			return cp
	for id: String in _catalog:
		var e: Dictionary = _catalog[id]
		var p := str(e["path"])
		if not p.begins_with("res://"):
			p = "res://" + p
		var hit := (str(e.get("cast", "")) == cast and str(e.get("variant", "default")) == variant) \
			or id == cast + "_" + variant or id == "cast_" + cast + "_" + variant \
			or (variant == "default" and (id == cast or id == "cast_" + cast))
		if hit and ResourceLoader.exists(p):
			return p
	var tbl: Dictionary = PLACEHOLDER.get(cast, {})
	return str(tbl.get(variant, tbl.get("default", "")))


static func texture(cast: String, variant := "default") -> Texture2D:
	var p := path(cast, variant)
	if p == "":
		return null
	if not _tex.has(p):
		_tex[p] = load(p)
	return _tex[p]


## "cast" when the shared cast library supplies this member, else "placeholder".
static func source(cast: String, variant := "default") -> String:
	return "placeholder" if path(cast, variant).begins_with("res://art/chars/") else "cast"


## "cast_puppet" when the cast library ships a rigged skin for this member (CastPuppet, art/cast/rig), else
## "paper_puppet" (D's rig with the placeholder art).
static func puppet_kind(cast: String) -> String:
	if cast == "traveller" and ResourceLoader.exists("res://art/cast/rig/cast_puppet.gd") \
			and FileAccess.file_exists("res://art/cast/rig/rig.json"):
		return "cast_puppet"
	return "paper_puppet"


## Print of a cast catalog entry by id ("cast_pig_a_calm"), or null.
static func by_id(id: String) -> Texture2D:
	_load()
	if not _catalog.has(id):
		return null
	var p := str(_catalog[id]["path"])
	p = p if p.begins_with("res://") else "res://" + p
	if not _tex.has(p):
		_tex[p] = load(p)
	return _tex[p]
