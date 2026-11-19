class_name PaperAudio
extends Node3D
## Paper sounds for pop-up motion. One node per scene; `watch(root)` hooks every PopHinge under
## root (flapped → flap/fold sound, landed → soft pat on the page).
## - flap (rising): 6 snap variants, pitch by weight (heavy = lower) ± random, never the same
##   variant twice in a row.
## - fold (falling): 4 gentler air "fff" variants, quieter; the landing adds a soft pat.
## - gain by distance from `listener_point` (the camera focus on the page); slight stereo pan
##   from the camera's point of view (AudioStreamPlayer3D, panning_strength low, no attenuation).
## - rate limit: a token bucket (~rate/s, small burst) plus a minimum gap; skipped events are
##   counted and swell the next sound a little, so a 40-piece wave reads as a flurry of paper,
##   not a machine gun.

const FLAPS := [
	preload("res://audio/paper/flap_up_1.wav"), preload("res://audio/paper/flap_up_2.wav"),
	preload("res://audio/paper/flap_up_3.wav"), preload("res://audio/paper/flap_up_4.wav"),
	preload("res://audio/paper/flap_up_5.wav"), preload("res://audio/paper/flap_up_6.wav"),
]
const FOLDS := [
	preload("res://audio/paper/fold_down_1.wav"), preload("res://audio/paper/fold_down_2.wav"),
	preload("res://audio/paper/fold_down_3.wav"), preload("res://audio/paper/fold_down_4.wav"),
]
const PATS := [
	preload("res://audio/paper/pat_1.wav"), preload("res://audio/paper/pat_2.wav"),
	preload("res://audio/paper/pat_3.wav"),
]

@export var voices := 10
@export var rate := 14.0  ## sustained sounds per second
@export var burst := 4.0  ## bucket size
@export var min_gap := 0.028  ## s between two starts
@export var flap_db := -4.0
@export var fold_db := -10.0
@export var pat_db := -13.0
@export var db_per_unit := 1.3  ## distance falloff on the page
@export var pan := 0.3  ## 0 mono … 1 full 3D pan
@export var listener_point := Vector3.ZERO

var played := 0  ## stats for benches
var skipped := 0
var _pool: Array[AudioStreamPlayer3D] = []
var _next := 0
var _tokens := 0.0
var _last_start := -1.0
var _crowd := 0.0
var _last_flap := -1
var _last_fold := -1
var _clock := 0.0  ## seconds, follows PopHinge.fixed_dt when set (deterministic benches)
var log_events := false
var events: Array = []  ## [time, kind, volume_db, pitch] when log_events


func _ready() -> void:
	_tokens = burst
	for i in voices:
		var p := AudioStreamPlayer3D.new()
		p.attenuation_model = AudioStreamPlayer3D.ATTENUATION_DISABLED
		p.panning_strength = pan
		p.max_polyphony = 1
		p.doppler_tracking = AudioStreamPlayer3D.DOPPLER_TRACKING_DISABLED
		if AudioServer.get_bus_index("SFX") >= 0:
			p.bus = "SFX"
		add_child(p)
		_pool.append(p)


func _process(dt: float) -> void:
	if PopHinge.fixed_dt > 0.0:
		dt = PopHinge.fixed_dt
	_clock += dt
	_tokens = minf(burst, _tokens + rate * dt)
	_crowd = maxf(0.0, _crowd - dt * 3.0)


## Hook every PopHinge under root.
func watch(root: Node) -> void:
	for h in PopWave.collect(root):
		if not h.flapped.is_connected(_on_flapped):
			h.flapped.connect(_on_flapped.bind(h))
			h.landed.connect(_on_landed.bind(h))


func _on_flapped(up: bool, weight: float, h: PopHinge) -> void:
	if up:
		flap(h.global_position, weight)
	else:
		fold(h.global_position, weight)


func _on_landed(weight: float, speed: float, h: PopHinge) -> void:
	pat(h.global_position, weight, clampf(speed / 1.8, 0.2, 1.0))


func flap(pos: Vector3, weight := 1.0) -> void:
	_last_flap = _pick(FLAPS.size(), _last_flap)
	_play(FLAPS[_last_flap], pos, flap_db, _pitch(weight, 0.09), true)


func fold(pos: Vector3, weight := 1.0) -> void:
	_last_fold = _pick(FOLDS.size(), _last_fold)
	_play(FOLDS[_last_fold], pos, fold_db, _pitch(weight, 0.07) * 0.95, false)


func pat(pos: Vector3, weight := 1.0, strength := 1.0) -> void:
	_play(PATS[randi() % PATS.size()], pos, pat_db + linear_to_db(strength), _pitch(weight, 0.06), false)


## A footstep on paper (for walking characters): a very quiet pat.
func step(pos: Vector3, speed01 := 0.5) -> void:
	_play(PATS[randi() % PATS.size()], pos, pat_db - 6.0 + 4.0 * speed01, randf_range(1.25, 1.5), false)


func _pitch(weight: float, spread: float) -> float:
	return clampf(pow(clampf(weight, 0.3, 3.0), -0.35) * randf_range(1.0 - spread, 1.0 + spread), 0.6, 1.7)


func _pick(n: int, last: int) -> int:
	var k := randi() % n
	if k == last:
		k = (k + 1 + randi() % (n - 1)) % n
	return k


func _play(stream: AudioStream, pos: Vector3, db: float, pitch: float, important: bool) -> void:
	var now := _clock
	var gap_ok := now - _last_start >= min_gap * randf_range(0.8, 1.4)
	if _tokens < 1.0 or not gap_ok:
		skipped += 1
		_crowd = minf(_crowd + (0.35 if important else 0.15), 3.0)
		return
	_tokens -= 1.0
	_last_start = now
	var p := _pool[_next]
	_next = (_next + 1) % _pool.size()
	var d := Vector2(pos.x - listener_point.x, pos.z - listener_point.z).length()
	var gain := db - db_per_unit * maxf(0.0, d - 1.0) + _crowd
	p.stream = stream
	p.volume_db = clampf(gain, -30.0, 0.0)
	p.pitch_scale = pitch
	p.global_position = pos
	p.play()
	played += 1
	if log_events:
		events.append([snappedf(now, 0.001), stream.resource_path.get_file().get_basename(), snappedf(p.volume_db, 0.1), snappedf(pitch, 0.01)])
	_crowd *= 0.5
