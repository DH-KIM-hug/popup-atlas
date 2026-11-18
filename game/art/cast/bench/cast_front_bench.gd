extends "res://scenes/chars/puppet_closeup.gd"
## Front-facing walk check (2026-11-18 walk v4): CastPuppet with front_gait walking toward a close camera (story
## parameters: front steps, step period 0.46). Args after `--`: --pose=<pose> --droop=<0..1> --lift=<x> --arms=<x>.
##   Godot --path game --write-movie out.avi --fixed-fps 30 --quit-after 150 res://art/cast/bench/cast_front_bench.tscn -- --pose=shirt_calm


func _ready() -> void:
	walk_dir = Vector3(0, 0, 1)
	var args := {}
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--") and "=" in a:
			args[a.substr(2).get_slice("=", 0)] = a.get_slice("=", 1)
	var cast_pose := str(args.get("pose", "walk_calm"))
	pose = "walk"
	PaperSpring.fixed_dt = 1.0 / 30.0
	super._ready()
	rig.elevation_deg = 14.0
	rig.distance = 1.6
	walker.speed = 0.2
	var old := puppet
	var cp := CastPuppet.new()
	cp.skin = "traveller"
	cp.pose = cast_pose
	cp.camera = rig.camera
	cp.height = 0.47
	cp.front_gait = true
	cp.step_period = 0.46
	cp.min_stride = 0.05
	cp.max_stride = 0.13
	cp.foot_lift = 0.03 * 0.47 / 0.36
	cp.waddle_deg = 4.0
	cp.front_droop = float(args.get("droop", "0"))
	cp.front_lift = float(args.get("lift", "1"))
	cp.front_arm_swing = float(args.get("arms", "1"))
	walker.add_child(cp)
	puppet = cp
	old.queue_free()
