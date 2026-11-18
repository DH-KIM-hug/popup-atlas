class_name CastPuppet
extends PaperPuppet
## PaperPuppet with a selectable SKIN from the shared cast library (game/art/cast). Same walk rig, same pose names
## (walk, walk_nohat, hold, shirt, fan, sit) so story code and set_pose() calls do not change.
## skin = "" keeps the legacy 톡톡 art exactly (PaperPuppet behaviour). A skin maps every pose name to a rigged
## cast figure cut by tools/cast/cut_cast_rig.py (parts body/hips/leg_l/leg_r + rig.json, same format as chars_rig).
## Poses a skin has no figure for (fan, sit) use the skin's nearest rigged figure, so a skin never mixes art styles.

const SKINS := {
	"traveller": {
		"dir": "res://art/cast/rig/",
		"poses": {
			"walk": "cast_traveller_coat", "walk_nohat": "cast_traveller_coat_nohat", "hold": "cast_traveller_coat_hold",
			"shirt": "cast_traveller_nocoat", "fan": "cast_traveller_nocoat_nohat", "sit": "cast_traveller_nocoat_nohat",
			# 2026-11-18 expression figures (same design, same standing stance, cut by cut_cast_rig.py):
			"walk_calm": "cast_traveller_coat_calm", "walk_calm_nohat": "cast_traveller_coat_nohat_calm",
			"surprised": "cast_traveller_coat_surprised", "surprised_nohat": "cast_traveller_coat_nohat_surprised",
			"cold": "cast_traveller_coat_nohat_cold", "warm": "cast_traveller_coat_open_hot",
			"hot_fan": "cast_traveller_coat_open_fan", "relieved": "cast_traveller_nocoat_relieved",
			"relieved_nohat": "cast_traveller_nocoat_nohat_relieved", "shirt_calm": "cast_traveller_nocoat_calm",
		},
	},
}

@export var skin := "traveller"
## Shiver amount (0 = still, 1 = cold, 1.5 = freezing). Paper-puppet shiver: the body card rocks fast (~12 Hz) about
## the hip brads with a shoulder bob and a small hunch while the legs stay planted (walk or stand). Rises fast,
## decays slowly when set back to 0 (the wind stops, he warms up).
@export var shiver := 0.0
## Extra forward lean into the walk (degrees), e.g. pushing into the wind. Applied through the base gait's lean so
## the legs are solved against the leaning body (no detached hips).
@export var push_lean_deg := 0.0

## Re-aim each leg with the exact shortest rotation from its rest direction to its footprint (the base gait splits
## the aim into a clamped in-plane swing + out-of-plane tilt, which misses the print by ~15 % of the travel when the
## walk goes into depth, read as skating). Story walks run mostly into depth.
@export var plant_exact := true
@export var max_leg_deg := 40.0

var _skin_rig := {}
var _arm: Node3D  ## pivot (wrist) of an extra hinged arm part, e.g. the hat fanning in his hand
var _arm_card: PaperCard
var _shv := 0.0
var _base_lean := -1.0


func _skin_ok() -> bool:
	return skin != "" and SKINS.has(skin)


func _aim_legs_exact() -> void:
	var tb := _tilt.global_transform.basis
	for i in 2:
		var hip_w := _tilt.global_transform * _hip_local[i]
		var rest := (tb * _leg_rest[i])
		var to_foot := _feet[i] - hip_w
		if to_foot.length() < 1e-4 or rest.length() < 1e-4:
			continue
		var a := rest.normalized()
		var b := to_foot.normalized()
		var ang := a.angle_to(b)
		var q := Quaternion.IDENTITY
		if ang > 1e-4:
			var axis := a.cross(b)
			if axis.length() > 1e-6:
				q = Quaternion(axis.normalized(), minf(ang, deg_to_rad(max_leg_deg)))
		_legs[i].global_transform = Transform3D(Basis(q) * tb, hip_w)


## Same as PaperPuppet.set_pose (animated card flip unless `instant`), but accepts every pose the skin maps.
func set_pose(p: String, instant := false) -> void:
	if not _skin_ok():
		super.set_pose(p, instant)
		return
	if not (SKINS[skin]["poses"] as Dictionary).has(p) or (p == pose and _flip_t < 0.0):
		return
	if instant or not is_inside_tree():
		_apply_pose(p)
		return
	_flip_to = p
	_flip_t = 0.0


func _process(dt: float) -> void:
	if _base_lean < 0.0:
		_base_lean = lean_deg
	# The base lean scales with speed/0.3; divide that back out so a slow, struggling walk still leans in.
	lean_deg = _base_lean + push_lean_deg / clampf(speed / 0.3, 0.12, 1.0)
	super._process(dt)
	var fdt := PaperSpring.frame_dt(dt)
	if fdt <= 0.0 or not _rigged:
		return
	if plant_exact and _walking:
		_aim_legs_exact()
	if _arm and _arm.visible:
		# fanning: quick flaps (out fast, back a bit slower), body pumps a touch with each stroke
		# swings only outward (away from his face): 0 .. 0.42 rad, a quick flick out and a softer return
		var fp := fmod(_t * 2.6, 1.0)
		var f := sin(fp * PI * 2.0) * 0.5 + 0.5
		f = f * f * (3.0 - 2.0 * f)
		_arm.rotation.z = 0.42 * f
		_body.position.y += height * 0.004 * f
	_shv = lerpf(_shv, shiver, 1.0 - exp(-(9.0 if shiver > _shv else 0.9) * fdt))
	if _shv < 0.003:
		_body.scale = Vector3.ONE
		return
	var ph := _t * TAU * 12.0 + 0.7 * sin(_t * 7.3)
	var roll := deg_to_rad(3.4) * _shv * sin(ph)
	var piv := (_hip_local[0] + _hip_local[1]) * 0.5
	piv.z = 0.0
	var rb := Basis(Vector3(0, 0, 1), roll)
	var side := height * 0.008 * _shv * sin(ph + 0.6)
	var chatter := height * 0.009 * _shv * (0.5 + 0.5 * sin(ph * 2.0))  # teeth-chatter shoulder bob
	_body.position = piv + rb * (_body.position - piv) + Vector3(side, chatter, 0.0)
	_body.rotation.z += roll
	_body.scale = Vector3(1.0 + 0.01 * _shv, 1.0 - 0.025 * _shv, 1.0)  # hunched


func _apply_pose(p: String) -> void:
	if not _skin_ok():
		super._apply_pose(p)
		return
	var sk: Dictionary = SKINS[skin]
	var dir: String = sk["dir"]
	if _skin_rig.is_empty():
		_skin_rig = JSON.parse_string(FileAccess.get_file_as_string(dir + "rig.json"))
	var key: String = sk["poses"].get(p, sk["poses"]["walk"])
	var r: Dictionary = _skin_rig.get(key, {})
	if r.is_empty():
		push_warning("CastPuppet: no rig for %s, falling back to legacy art" % key)
		super._apply_pose(p)
		return
	pose = p
	_rigged = true
	var fb: Array = r["full_bbox"]
	_scale_px = height / float(fb[3] - fb[1])
	var s := _scale_px
	var cxf := (float(fb[0]) + float(fb[2])) * 0.5
	var fy1 := float(fb[3])
	var bb: Array = r["parts"]["body"]["bbox"]
	_body.texture = load(dir + key + "_body.png")
	_body.height = (bb[3] - bb[1]) * s
	_body.position = Vector3(((bb[0] + bb[2]) * 0.5 - cxf) * s, (fy1 - bb[3]) * s, 0.0)
	_body_rest = _body.position
	_body.rotation = Vector3.ZERO
	var sb: Array = r["parts"]["hips"]["bbox"]
	_hips.texture = load(dir + key + "_hips.png")
	_hips.height = (sb[3] - sb[1]) * s
	_hips.position = Vector3(((sb[0] + sb[2]) * 0.5 - cxf) * s, (fy1 - sb[3]) * s, -thickness * 1.15)
	_hips.visible = true
	for i in 2:
		var side := "leg_l" if i == 0 else "leg_r"
		var part: Dictionary = r["parts"][side]
		var lb: Array = part["bbox"]
		var hip: Array = part["hip"]
		var lcx := (float(lb[0]) + float(lb[2])) * 0.5
		var z := -thickness * (2.3 + 1.0 * i)
		_hip_local[i] = Vector3((hip[0] - cxf) * s, (fy1 - hip[1]) * s, z)
		var c := _leg_cards[i]
		c.texture = load(dir + key + "_" + side + ".png")
		c.height = (lb[3] - lb[1]) * s
		c.position = Vector3((lcx - hip[0]) * s, -(lb[3] - hip[1]) * s, 0.0)
		_leg_rest[i] = c.position
		_sole_x[i] = (lcx - cxf) * s
		_legs[i].visible = true
	_apply_arm(r, s, bb)
	_fix_materials.call_deferred()
	pose_changed.emit(p)


## Optional hinged arm part (rig.json parts.<name> with bbox + pivot, see cut_cast_rig.ARM_PARTS): a card on the body
## card, swung about the wrist in _process. Hidden for poses without one.
func _apply_arm(r: Dictionary, s: float, bb: Array) -> void:
	var name_ := ""
	for k in (r["parts"] as Dictionary).keys():
		if not (k in ["body", "hips", "leg_l", "leg_r"]):
			name_ = k
	if name_ == "":
		if _arm:
			_arm.visible = false
		return
	if _arm == null:
		_arm = Node3D.new()
		_arm.name = "Arm"
		_arm_card = PaperCard.new()
		_arm_card.thickness = thickness
		_arm.add_child(_arm_card)
	if _arm.get_parent() != _body:
		if _arm.get_parent():
			_arm.get_parent().remove_child(_arm)
		_body.add_child(_arm)
	var part: Dictionary = r["parts"][name_]
	var ab: Array = part["bbox"]
	var pv: Array = part["pivot"]
	var key: String = SKINS[skin]["poses"].get(pose, "")
	_arm_card.texture = load(SKINS[skin]["dir"] + key + "_" + name_ + ".png")
	_arm_card.height = (ab[3] - ab[1]) * s
	# body card origin = bottom-centre of its bbox
	_arm.position = Vector3((pv[0] - (bb[0] + bb[2]) * 0.5) * s, (bb[3] - pv[1]) * s, thickness * 1.2)
	_arm_card.position = Vector3(((ab[0] + ab[2]) * 0.5 - pv[0]) * s, (pv[1] - ab[3]) * s, 0.0)
	_arm.rotation = Vector3.ZERO
	_arm.visible = true
