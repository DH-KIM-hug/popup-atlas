class_name CardLibrary
extends RefCounted
## Shared card library query (integrator, round 1). Loads the shared atlas catalog (A0, game/art/atlas) and the
## 해와 바람 card kit (A, game/art/cards) into one index and answers queries by category / tags / biome / season,
## so scene templates name *kinds* of cards, never file paths.
##  - Atlas paths are remapped to the rim-stripped copies in game/art/atlas_clean/ (tools/world/clean_atlas.py)
##    when they exist; originals are untouched.
##  - Pools: a coarse grouping used by placers ("conifer", "tree", "autumn", "bush", "hedge", "flower", ...).
##  - pick(): least-used id from a pool (seeded RNG) so no single motif dominates a frame.

const CATALOGS := ["res://art/atlas/catalog.json", "res://art/cards/catalog.json"]
const EXCLUDE_SHEETS := ["winter_snow", "korean_village", "korean_nature", "fairytale_west"]

var cards := {}  ## id -> Dictionary (path, category, sheet, label, tags, biome, season, h, aspect, cross, pool)
var pools := {}  ## pool -> Array[String] ids
var used := {}  ## id -> times used
var rng: RandomNumberGenerator


func _init(rng_: RandomNumberGenerator, exclude_seasons := ["winter"]) -> void:
	rng = rng_
	for cpath in CATALOGS:
		var f := FileAccess.open(cpath, FileAccess.READ)
		if f == null:
			push_error("CardLibrary: no catalog " + cpath)
			continue
		for it in JSON.parse_string(f.get_as_text()):
			var d: Dictionary = it
			var sheet := str(d.get("sheet", d.get("src", "")))
			if str(d.get("season", "")) in exclude_seasons or sheet in EXCLUDE_SHEETS:
				continue
			var p := str(d["path"])
			if not p.begins_with("res://"):
				p = "res://" + p
			var clean := p.replace("res://art/atlas/", "res://art/atlas_clean/")
			if clean != p and ResourceLoader.exists(clean):
				p = clean
			var px: Array = d.get("px", [1, 1])
			var e := {
				"id": str(d["id"]), "path": p, "category": str(d["category"]), "sheet": sheet,
				"label": str(d.get("label", d["id"])), "tags": d.get("tags", []), "biome": str(d.get("biome", "")),
				"season": str(d.get("season", "any")), "h": float(d["height_units"]),
				"aspect": float(d.get("aspect", float(px[0]) / maxf(1.0, float(px[1])))),
				"cross": bool(d.get("cross_slot", false)),
			}
			e["pool"] = _pool_of(e)
			cards[e["id"]] = e
			if e["pool"] != "":
				if not pools.has(e["pool"]):
					pools[e["pool"]] = []
				pools[e["pool"]].append(e["id"])


## Ids matching every given filter (empty filter = any).
func query(category := "", tags: Array = [], biome := "", season := "") -> Array:
	var out := []
	for id in cards:
		var e: Dictionary = cards[id]
		if category != "" and e["category"] != category:
			continue
		if biome != "" and e["biome"] != biome:
			continue
		if season != "" and e["season"] != season and e["season"] != "any":
			continue
		var ok := true
		for t in tags:
			if not (t in e["tags"]):
				ok = false
				break
		if ok:
			out.append(id)
	out.sort()  # deterministic order regardless of dictionary history
	return out


## Least-used id from `pool_or_ids` (pool name or explicit id list); ties broken by the seeded RNG.
func pick(pool_or_ids) -> String:
	var ids: Array = pool_or_ids if pool_or_ids is Array else pools.get(pool_or_ids, [])
	if ids.is_empty():
		return ""
	var best := ""
	var bu := 1 << 30
	for k in 6:
		var id: String = ids[rng.randi() % ids.size()]
		var u: int = used.get(id, 0)
		if u < bu:
			bu = u
			best = id
	return best


func mark(id: String) -> void:
	used[id] = int(used.get(id, 0)) + 1


func has(id: String) -> bool:
	return cards.has(id)


func get_card(id: String) -> Dictionary:
	return cards.get(id, {})


static func _pool_of(d: Dictionary) -> String:
	var cat: String = d["category"]
	var sheet: String = d["sheet"]
	var label: String = d["label"]
	var id: String = d["id"]
	var h: float = d["h"]
	if cat == "conifer" or (cat == "tree" and (sheet == "forest_conifer" or "pine" in label or "cypress" in label or "fir" in label)):
		return "conifer" if h >= 0.6 else "sapling"
	if cat == "tree":
		if h < 0.55:
			return "sapling"
		if sheet == "autumn" or "terracotta" in label or "ochre" in id or "golden" in label or "orange" in label or "red" in label:
			return "autumn"
		if sheet == "spring_blossom" or "blossom" in label or "apple" in id:
			return "blossom"
		return "tree"
	match cat:
		"bush":
			return "bush"
		"hedge":
			return "hedge"
		"flower":
			return "flower"
		"grass", "foreground":
			return "grass"
		"mushroom":
			return "mushroom"
		"rock":
			return "rock"
		"reeds":
			return "reeds"
		"water":
			return "reeds" if id.begins_with("water_") and h > 0.2 else ""
		"bank":
			return "bank"
		"animal":
			for k in ["duck", "goose", "heron", "frog", "swan"]:
				if k in label or k in id:
					return "water_animal"
			for k in ["fox", "deer", "rabbit", "hedgehog", "squirrel", "owl", "bunny", "snail", "badger", "bird"]:
				if k in label or k in id:
					return "wild_animal"
			return "farm_animal"
		"prop", "village", "sign", "lantern":
			return "prop"
		"fence", "wall":
			return "fence"
		"crop", "field":
			return "crop"
		"building", "house":
			return "house" if h >= 0.5 else "prop"
		"hill":
			return "hill"
	return ""
