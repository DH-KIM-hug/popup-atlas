class_name CrossCard
extends Node3D
## A cross-slotted pop-up pair, like a real pop-up tree: card A stands in the hinge plane,
## card B is slotted through it at 90°. When the parent PopHinge folds flat, B swings about
## the vertical slot line until it lies flush on A's front; when the hinge rises, B swings
## open again, lagging the hinge a little and overshooting slightly (its own small spring).
## Put it as a child of a PopHinge (origin = bottom centre on the hinge line).
##
##   var h := PopHinge.new(); var t := CrossCard.new()
##   t.texture_a = tex; t.texture_b = tex2; t.height = 0.8; h.add_child(t)

@export var texture_a: Texture2D
@export var texture_b: Texture2D  ## null → the same print as A
@export var height := 0.8
@export var height_b := 0.0  ## 0 → same as A
@export var thickness := 0.012
@export var open_angle := 90.0  ## B's yaw when fully open (deg)
@export var closed_angle := 3.0  ## residual yaw when flat, so B lies on A without z-fighting
@export var follow_hz := 3.8
@export var follow_damping := 0.72

var card_a: PaperCard
var card_b: PaperCard
var slot: Node3D  ## B's pivot on the vertical slot line
var _hinge: PopHinge
var _yaw := 0.0
var _yaw_vel := 0.0


func _ready() -> void:
	card_a = PaperCard.new()
	card_a.texture = texture_a
	card_a.height = height
	card_a.thickness = thickness
	card_a.back_print = true
	add_child(card_a)
	slot = Node3D.new()
	slot.name = "Slot"
	# B sits a hair in front of A so that it lands on A's printed face when flat.
	# (Behind A for a forward-folding hinge, whose back faces up when flat.)
	var side := float((get_parent() as PopHinge).fold) if get_parent() is PopHinge else 1.0
	slot.position = Vector3(0, 0, thickness * 1.1 * side)
	add_child(slot)
	card_b = PaperCard.new()
	card_b.texture = texture_b if texture_b else texture_a
	card_b.height = height_b if height_b > 0.0 else height * 0.96
	card_b.thickness = thickness
	card_b.back_print = true
	slot.add_child(card_b)
	_hinge = get_parent() as PopHinge
	if _hinge:
		_hinge.snapped.connect(func(_up): snap())
	snap()


## Jump to the pose that matches the hinge, no motion.
func snap() -> void:
	_yaw = _target_yaw()
	_yaw_vel = 0.0
	_apply()


func _target_yaw() -> float:
	if _hinge == null:
		return deg_to_rad(open_angle)
	var o := clampf(_hinge.openness(), 0.0, 1.2)
	# B stays nearly closed while the hinge is low (the page squeezes it) and opens fast
	# over the last part of the rise, as a slotted pair does when the page pulls it.
	var k := smoothstep(0.12, 0.92, o)
	return deg_to_rad(lerpf(closed_angle, open_angle, k))


func _process(dt: float) -> void:
	if PopHinge.fixed_dt > 0.0:
		dt = PopHinge.fixed_dt
	var tgt := _target_yaw()
	if _hinge != null and not _hinge.is_moving() and absf(_yaw - tgt) < 0.002 and absf(_yaw_vel) < 0.01:
		if _yaw != tgt:
			_yaw = tgt
			_apply()
		return
	var w := TAU * follow_hz
	var steps := maxi(1, ceili(dt / (1.0 / 240.0)))
	var h := dt / steps
	for i in steps:
		var acc := -w * w * (_yaw - tgt) - 2.0 * follow_damping * w * _yaw_vel
		_yaw_vel += acc * h
		_yaw += _yaw_vel * h
		# B cannot pass through A.
		if _yaw < deg_to_rad(closed_angle) * 0.5:
			_yaw = deg_to_rad(closed_angle) * 0.5
			_yaw_vel = absf(_yaw_vel) * 0.2
	_apply()


func _apply() -> void:
	if slot:
		slot.rotation.y = _yaw
