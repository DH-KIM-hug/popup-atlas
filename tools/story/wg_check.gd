extends SceneTree
func _init() -> void:
	for p in ["res://story/spread_stage.gd", "res://story/story_runner.gd", "res://stories/wolf_goats/fx.gd"]:
		var s: GDScript = load(p)
		print("CHECK ", p, " ", s != null and s.can_instantiate())
	quit()
