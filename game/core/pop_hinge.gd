class_name PopHinge
extends Node3D
## A hinge on the page: its children stand when up and lie flat when folded.
## Rotation is about local X (the hinge line). Rest (up) angle = 0.
## fold = +1 lies back (top toward -Z, print facing up when flat), -1 lies forward (top toward +Z).
##
## Round 3 (2026-11-18, critic r2: "snappy spring-toy pop" / "falling door"): both directions are
## driven by the PAGE. The opening/closing page pulls the piece along an eased path and a stiff,
## well-damped spring follows it, so nothing is "sprung":
##  - Rising: ease-in-out pull, ~0.31 s (small) / 0.42 s (medium) / 0.58 s (large) to vertical,
##    overshoot 1.2-2.4 deg once, within ±0.5 deg ~0.1 s later; twist breath ≤ 1.5 deg.
##  - Folding: ease-in-out pull (slow start, fastest near 45 deg, decelerates into contact),
##    touches at ~0.42 / 0.53 / 0.70 s, then a soft 1-2 deg air-cushion settle (no slam, no bounce).
## Tuned with the sim in scenes/motion/curve_job.gd (plot: scenes/motion/plot_curves.py).

signal flapped(up: bool, weight: float)  ## emitted when a fold starts moving (after its delay)
signal landed(weight: float, speed: float)  ## falling piece first hits the page (speed rad/s)
signal settled(up: bool)
signal snapped(up: bool)  ## snap() was called (no motion, followers should jump too)

## When > 0 every hinge advances by this fixed step per frame instead of the frame delta
## (deterministic captures and offline curve dumps). 0 = real time.
static var fixed_dt := 0.0

@export_enum("Back:1", "Forward:-1") var fold := 1
@export var freq_hz := 5.2  ## follower spring frequency for weight 1 (scales weight^-0.15)
@export var damping := 0.75  ## follower zeta for weight 1 (heavier → more damped)
@export var rise_time := 0.45  ## page-pull duration for weight 1 (scales weight^0.4)
@export var fold_time := 0.55  ## page-pull duration when folding, weight 1 (scales weight^0.35)
@export var ease_share := 0.92  ## 1 = pure smoothstep path, 0 = linear (arrival speed → overshoot)
@export var weight := 1.0  ## 0.4 (tiny flower) … 2.5 (big tree); slower, lower sound when heavy
@export var start_up := false
## Peak of the twist breath (rad) for a light piece; heavy pieces breathe less. ≤ 2 deg.
@export var wobble := 0.033
@export var settle_lift := 3.0  ## air-cushion lift on landing (≈ 1.4 deg peak for weight 1; ∝ weight^-0.3)

var is_up := false
var _angle := 0.0
var _vel := 0.0
var _target := 0.0
var _delay := 0.0
var _moving := false
var _waiting := false
var _twist := 0.0
var _twist_vel := 0.0
var _freq_j := 1.0
var _landed_once := false
var _kick := 0.0  ## twist kick waiting for the piece to reach vertical
var _pull_t := 0.0  ## time since the rise started
var _pull_from := 0.0  ## angle the rise started from


func _ready() -> void:
	_freq_j = randf_range(0.94, 1.07)
	is_up = start_up
	_angle = 0.0 if start_up else flat_angle()
	_target = _angle
	_apply()
	set_process(false)


func flat_angle() -> float:
	return -PI * 0.5 * fold


## Current hinge angle (0 = standing, flat_angle() = lying on the page).
func angle() -> float:
	return _angle


## Current twist about the card's own vertical axis (rad).
func twist() -> float:
	return _twist


## 1 when standing, 0 when flat (may exceed 1 slightly during overshoot).
func openness() -> float:
	return 1.0 - _angle / flat_angle()


func is_moving() -> bool:
	return _moving


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
	_moving = false
	_waiting = false
	_kick = 0.0
	_apply()
	set_process(false)
	snapped.emit(up)


func _go(up: bool, delay: float) -> void:
	var tgt := 0.0 if up else flat_angle()
	if up == is_up and not _moving and absf(_angle - tgt) < 1e-3:
		return
	is_up = up
	_target = tgt
	_delay = delay
	_moving = true
	_waiting = true
	_landed_once = false
	set_process(true)
	if delay <= 0.0:
		_start()


func _start() -> void:
	_waiting = false
	flapped.emit(is_up, weight)
	var w := clampf(weight, 0.3, 3.0)
	_pull_t = 0.0
	_pull_from = _angle
	if is_up:
		# The paper takes a small breath at the top: a twist kick near vertical, smaller when heavy.
		_kick = randf_range(0.6, 1.0) * (1.0 if randf() < 0.5 else -1.0) * wobble / sqrt(w)
	else:
		# A breath of twist as the page starts to close (tiny: the page holds the base).
		_twist_vel += randf_range(-1.0, 1.0) * wobble * 2.0


func _process(dt: float) -> void:
	step(fixed_dt if fixed_dt > 0.0 else dt)


## Eased page pull: 0 → 1 over u in [0,1]; mostly smoothstep (slow start, fastest at the middle,
## slow arrival), with a little linear share so the piece arrives with a hint of momentum.
static func _pull(u: float, a: float) -> float:
	u = clampf(u, 0.0, 1.0)
	return a * u * u * (3.0 - 2.0 * u) + (1.0 - a) * u


static func _pull_rate(u: float, a: float) -> float:
	if u >= 1.0 or u < 0.0:
		return 0.0
	return a * 6.0 * u * (1.0 - u) + (1.0 - a)


## Advance the simulation by dt seconds (called from _process; callable directly for offline sims).
func step(dt: float) -> void:
	if not _moving:
		return
	if _waiting:
		_delay -= dt
		if _delay > 0.0:
			return
		dt = -_delay
		_start()
	var w8 := clampf(weight, 0.3, 3.0)
	var steps := maxi(1, ceili(dt / (1.0 / 240.0)))
	var h := dt / steps
	var flat := flat_angle()
	var s := signf(flat)  # direction of falling
	var w := TAU * freq_hz * _freq_j / pow(w8, 0.15)
	var z := damping * (0.88 + 0.12 * w8)
	# Pull duration scales with how far the piece still has to travel.
	var span := absf(_target - _pull_from) / absf(flat)
	var base_t := rise_time * pow(w8, 0.4) if is_up else fold_time * pow(w8, 0.35)
	var dur := base_t / _freq_j * maxf(0.25, span)
	var wt := TAU * 6.0  # twist breath frequency
	for i in steps:
		_pull_t += h
		var u := _pull_t / dur
		var tgt := _pull_from + (_target - _pull_from) * _pull(u, ease_share)
		var tv := (_target - _pull_from) * _pull_rate(u, ease_share) / dur
		var acc := -w * w * (_angle - tgt) - 2.0 * z * w * (_vel - tv)
		_vel += acc * h
		_angle += _vel * h
		if _kick != 0.0 and openness() > 0.9:
			_twist_vel += _kick * wt
			_kick = 0.0
		# The page stops the piece. First contact: the trapped air lifts the far edge a degree
		# or two and it settles (follower pulls it back); never a hard bounce.
		if (_angle - flat) * s > 0.0:
			var speed := absf(_vel)
			_angle = flat
			if not _landed_once and not is_up:
				_landed_once = true
				landed.emit(weight, speed)
				_vel = -s * deg_to_rad(settle_lift) * w * 1.7 / pow(w8, 0.3)
			else:
				_vel = 0.0
		# A lying piece cannot twist: the page holds it, so twist dies fast near flat.
		var tz := 0.38 if openness() > 0.2 else 1.0
		var twacc := -wt * wt * _twist - 2.0 * tz * wt * _twist_vel
		_twist_vel += twacc * h
		_twist += _twist_vel * h
	_apply()
	var done_angle := absf(_angle - _target) < 0.003 and absf(_vel) < 0.02 and _pull_t >= dur
	if done_angle and absf(_twist) < 0.002 and absf(_twist_vel) < 0.02:
		_angle = _target
		_vel = 0.0
		_twist = 0.0
		_twist_vel = 0.0
		_apply()
		_moving = false
		set_process(false)
		settled.emit(is_up)


func _apply() -> void:
	# Hinge first, then twist about the card's own (tilted) vertical, so a tilted card never
	# spins in the page plane (that read as sideways-sliding slivers in round 1).
	transform.basis = Basis(Vector3.RIGHT, _angle) * Basis(Vector3.UP, _twist)
