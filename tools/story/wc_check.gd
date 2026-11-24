extends SceneTree
## Load-check the shared runner / stage and witch_candy's handler (prints CHECK <path> true|false).
func _init() -> void:
	for p in ["res://story/spread_stage.gd", "res://story/story_runner.gd", "res://story/story_actor.gd", "res://stories/witch_candy/fx.gd"]:
		var s: GDScript = load(p)
		print("CHECK ", p, " ", s != null and s.can_instantiate())
	quit()
