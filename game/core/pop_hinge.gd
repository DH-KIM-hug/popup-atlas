class_name PopHinge
extends Node3D
## A hinge on the page: its children stand when up and lie flat when folded.
## Rotation is about local X (the hinge line). Rest (up) angle = 0.
## fold = +1 lies back (top toward -Z), -1 lies forward (top toward +Z).
## Motion is an under-damped spring: overshoots on the way up, settles with a wobble,
## and bounces softly off the page on the way down.

signal flapped(up: bool, weight: float)  ## emitted when a fold starts moving
signal settled(up: bool)

@export_enum("Back:1", "Forward:-1") var fold := 1
@export var freq_hz := 2.2
@export var damping := 0.32  ## zeta; < 1 overshoots
@export var weight := 1.0  ## bigger pieces are slower and sound lower
@export var start_up := false
## Second-order wobble: a small lateral twist that rings and fades as the piece settles.
@export var wobble := 0.05

var is_up := false
var _angle := 0.0
var _vel := 0.0
var _target := 0.0
var _delay := 0.0
var _moving := false
var _twist := 0.0
var _twist_vel := 0.0
var _freq_j := 1.0


func _ready() -> void:
	_freq_j = randf_range(0.9, 1.12)
	is_up = start_up
	_angle = 0.0 if start_up else flat_angle()
	_target = _angle
	_apply()
	set_process(false)


func flat_angle() -> float:
	return -PI * 0.5 * fold


func pop_up(delay := 0.0) -> void:
	_go(true, delay)


func fold_down(delay := 0.0) -> void:
	_go(false, delay)


func snap(up: bool) -> void:
	is_up = up
	_angle = 0.0 if up else flat_angle()
	_target = _angle
	_vel = 0.0
	_twist = 0.0
	_twist_vel = 0.0
	_apply()
	set_process(false)


func _go(up: bool, delay: float) -> void:
	if up == is_up and _moving == false and absf(_angle - (0.0 if up else flat_angle())) < 1e-3:
		return
	is_up = up
	_target = 0.0 if up else flat_angle()
	_delay = delay
	_moving = true
	set_process(true)


func _process(dt: float) -> void:
	if _delay > 0.0:
		_delay -= dt
		if _delay <= 0.0:
			flapped.emit(is_up, weight)
			# A kick of twist when the paper snaps open.
			_twist_vel += randf_range(-1.0, 1.0) * wobble * 14.0
		return
	var w := TAU * freq_hz * _freq_j / sqrt(maxf(weight, 0.2))
	var z := damping if is_up else minf(damping * 1.8, 0.9)
	# Semi-implicit Euler in substeps for stability at low frame rates.
	var steps := ceili(dt / (1.0 / 240.0))
	var h := dt / steps
	for i in steps:
		var acc := -w * w * (_angle - _target) - 2.0 * z * w * _vel
		_vel += acc * h
		_angle += _vel * h
		# The page stops a falling piece: soft bounce.
		var flat := flat_angle()
		if (fold > 0 and _angle < flat) or (fold < 0 and _angle > flat):
			_angle = flat
			_vel = -_vel * 0.28
		var tacc := -w * w * 1.6 * _twist - 2.0 * 0.22 * w * _twist_vel
		_twist_vel += tacc * h
		_twist += _twist_vel * h
	_apply()
	if absf(_angle - _target) < 0.002 and absf(_vel) < 0.01 and absf(_twist) < 0.002 and absf(_twist_vel) < 0.01:
		_angle = _target
		_twist = 0.0
		_apply()
		_moving = false
		set_process(false)
		settled.emit(is_up)


func _apply() -> void:
	rotation = Vector3(_angle, _twist, 0.0)
