extends Node3D
## Close-up rig check for the paper puppet (component D): traveller walking a straight line, near camera.
@export var walk_dir := Vector3(1, 0, 0)
@export var pose := "walk"
var rig: LookRig
var walker: Walker
var puppet: PaperPuppet

func _ready() -> void:
	var mi := MeshInstance3D.new()
	var pm := PlaneMesh.new()
	pm.size = Vector2(20, 20)
	mi.mesh = pm
	var m := StandardMaterial3D.new()
	m.albedo_color = Color("7fa86f")
	mi.material_override = m
	add_child(mi)
	rig = LookRig.new()
	rig.elevation_deg = 12.0
	rig.distance = 1.3
	rig.dof_enabled = false
	rig.follow_smooth = 0.0
	rig.focus_height = 0.18
	add_child(rig)
	var path := Path3D.new()
	var c := Curve3D.new()
	c.add_point(-walk_dir * 3.0)
	c.add_point(walk_dir * 3.0)
	path.curve = c
	add_child(path)
	walker = Walker.new()
	walker.path = path
	walker.camera = rig.camera
	walker.start_offset = 2.6
	walker.auto_walk = true
	add_child(walker)
	puppet = PaperPuppet.new()
	puppet.pose = pose
	puppet.camera = rig.camera
	walker.add_child(puppet)
	rig.focus_target = walker
	rig.snap()
