class_name WindGusts
extends Node3D
## The wind character's blowing (component D). Lives next to a SkyHanger holding the wind card.
## blow(toward, seconds): card swaps to the puffed-cheek print, puffs up, and sends paper curl swooshes
## (cut from the wind card's own curls) flying toward `toward`, each tumbling a little and shrinking away.
## Gusts also kick nearby SkyHangers and call `on_gust(strength)` on listeners (e.g. the traveller).

signal gust(strength: float)

const CURLS := ["res://art/chars_rig/gust_curl_0.png", "res://art/chars_rig/gust_curl_1.png",
	"res://art/chars_rig/gust_curl_2.png"]
const WIND_CALM := preload("res://art/chars/sw_wind.webp")
const WIND_BLOW := preload("res://art/chars/sw_wind_blow.webp")
const WIND_TIRED := preload("res://art/chars/sw_wind_tired.webp")

@export var hanger: SkyHanger
@export var gust_every := 0.32
@export var curl_height := 0.16
@export var travel_time := 1.5

var _blow_left := 0.0
var _spawn_t := 0.0
var _toward := Vector3.ZERO
var _curls: Array = []  ## [node, age, from, to, spin]
var _textures: Array[Texture2D] = []


func _ready() -> void:
	for p in CURLS:
		if ResourceLoader.exists(p):
			_textures.append(load(p))


func blow(toward: Vector3, seconds := 2.5) -> void:
	_toward = toward
	_blow_left = seconds
	_spawn_t = 0.0
	if hanger:
		hanger.set_texture(WIND_BLOW)
		hanger.puff(1.12)


func tire() -> void:
	_blow_left = 0.0
	if hanger:
		hanger.set_texture(WIND_TIRED)
		hanger.puff(1.0)


func calm() -> void:
	_blow_left = 0.0
	if hanger:
		hanger.set_texture(WIND_CALM)
		hanger.puff(1.0)


func _process(dt: float) -> void:
	dt = PaperSpring.frame_dt(dt)
	if _blow_left > 0.0:
		_blow_left -= dt
		_spawn_t -= dt
		if _spawn_t <= 0.0:
			_spawn_t = gust_every * randf_range(0.7, 1.3)
			_spawn()
			if hanger:
				hanger.puff(1.12 + randf() * 0.05)
				hanger.push(Vector3(randf_range(-0.12, 0.12), 0, 0))
		if _blow_left <= 0.0 and hanger:
			hanger.puff(1.0)
			hanger.set_texture(WIND_CALM)
	for i in range(_curls.size() - 1, -1, -1):
		var c: Array = _curls[i]
		var n: Node3D = c[0]
		c[1] += dt
		var u: float = c[1] / travel_time
		if u >= 1.0:
			n.queue_free()
			_curls.remove_at(i)
			continue
		var from: Vector3 = c[2]
		var to: Vector3 = c[3]
		var e := 1.0 - pow(1.0 - u, 2.2)  # fast out of the mouth, slowing as it spreads
		var p := from.lerp(to, e)
		p.y += sin(u * PI) * 0.18 + sin(c[1] * 9.0 + c[4] * 3.0) * 0.02
		n.global_position = p
		var sc := sin(minf(u * 4.0, 1.0) * PI * 0.5) * (1.0 - smoothstep(0.65, 1.0, u))
		n.scale = Vector3.ONE * maxf(sc, 0.01) * (0.8 + 0.4 * u)
		n.rotation = Vector3(0, 0, c[4] * u * 0.9 + 0.15 * sin(c[1] * 7.0))


func _spawn() -> void:
	if _textures.is_empty() or hanger == null:
		return
	var mouth := hanger.card().global_position + Vector3(0, hanger.card_height * 0.45, 0.05)
	var dir := (_toward - mouth)
	var n := Node3D.new()
	add_child(n)
	n.top_level = true
	var card := PaperCard.new()
	card.texture = _textures[randi() % _textures.size()]
	card.height = curl_height * randf_range(0.8, 1.25)
	card.thickness = 0.006
	card.position = Vector3(0, -card.height * 0.5, 0)
	n.add_child(card)
	n.global_position = mouth
	n.scale = Vector3.ONE * 0.01
	# Flip curls so their tails trail behind the motion.
	if dir.x < 0.0:
		card.scale = Vector3(-1, 1, 1)
	var spread := Vector3(randf_range(-0.25, 0.25), randf_range(-0.15, 0.2), randf_range(-0.3, 0.3))
	_curls.append([n, 0.0, mouth, _toward + spread, randf_range(-1.0, 1.0)])
	gust.emit(1.0)
