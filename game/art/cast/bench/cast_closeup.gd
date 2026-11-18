extends "res://scenes/chars/puppet_closeup.gd"
## Close-up rig check for the cast traveller skin: same bench as scenes/chars/puppet_closeup, puppet swapped for a
## CastPuppet (skin "" = legacy art, for A/B).
@export var skin := "traveller"


func _ready() -> void:
	PaperSpring.fixed_dt = 1.0 / 60.0
	super._ready()
	var old := puppet
	var cp := CastPuppet.new()
	cp.skin = skin
	cp.pose = pose
	cp.camera = rig.camera
	walker.add_child(cp)
	puppet = cp
	old.queue_free()
