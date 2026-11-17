class_name FollowFocus
extends Node3D
## Camera focus point for the follow camera (component D). Point LookRig.focus_target at this node and set
## LookRig.follow_smooth = 0: the rig then frames this node, which chases `target` with a critically damped
## spring (no overshoot, no jitter at frame-rate changes) and leads the walk slightly in the walk direction.

@export var target: Node3D
@export var omega := 2.6  ## spring stiffness (1/s); settle ≈ 4.7 / omega seconds
@export var lead_time := 0.55  ## seconds of velocity to look ahead
@export var max_lead := 0.35  ## world units
@export var lead_omega := 2.0  ## the lead itself eases in/out so starts/stops don't jerk the frame
@export var dead_zone := 0.0

var velocity := Vector3.ZERO
var _lead := Vector3.ZERO
var _last := Vector3.ZERO
var _tv := Vector3.ZERO


func _ready() -> void:
	process_priority = -10  # update before the LookRig reads us
	snap()


func snap() -> void:
	if is_instance_valid(target):
		global_position = target.global_position
		_last = target.global_position
	velocity = Vector3.ZERO
	_lead = Vector3.ZERO


func _process(dt: float) -> void:
	dt = PaperSpring.frame_dt(dt)
	if dt <= 0.0 or not is_instance_valid(target):
		return
	var tp := target.global_position
	var tv := (tp - _last) / dt
	_last = tp
	_tv = _tv.lerp(tv, 1.0 - exp(-6.0 * dt))
	var want_lead := _tv * lead_time
	want_lead.y = 0.0
	if want_lead.length() > max_lead:
		want_lead = want_lead.normalized() * max_lead
	_lead = _lead.lerp(want_lead, 1.0 - exp(-lead_omega * dt))
	var goal := tp + _lead
	# Critically damped spring, sub-stepped for stability at low frame rates.
	var n := maxi(1, ceili(dt / 0.008))
	var h := dt / n
	for i in n:
		var acc := (goal - global_position) * omega * omega - velocity * 2.0 * omega
		velocity += acc * h
		global_position += velocity * h
