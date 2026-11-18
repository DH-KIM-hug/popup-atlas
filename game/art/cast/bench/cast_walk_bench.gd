extends "res://scenes/chars/walk_bench.gd"
## The walk bench (scenes/chars/walk_bench) with the new cast library: CastPuppet traveller skin, cast sun and wind
## cards with expression swaps on the demo timeline (wind boast → blowing hard → tired, sun smile → proud → beaming).

const CAST := "res://art/cast/"
@export var skin := "traveller"


func _ready() -> void:
	super._ready()
	if demo:
		_events.append_array([
			[1.3, func(): wind.set_texture(load(CAST + "cast_wind_blow.webp"))],
			[5.0, func(): wind.set_texture(load(CAST + "cast_wind_tired.webp"))],
			[5.8, func(): sun.set_texture(load(CAST + "cast_sun_proud.webp"))],
			[6.4, func(): sun.set_texture(load(CAST + "cast_sun_beaming.webp"))],
		])
		_events.sort_custom(func(a, b): return a[0] < b[0])


func _build_chars() -> void:
	super._build_chars()
	var old := puppet
	var cp := CastPuppet.new()
	cp.skin = skin
	cp.camera = rig.camera
	walker.add_child(cp)
	puppet = cp
	old.queue_free()


func _build_sky() -> void:
	super._build_sky()
	sun.texture = load(CAST + "cast_sun_smile.webp")
	wind.texture = load(CAST + "cast_wind_boast.webp")
