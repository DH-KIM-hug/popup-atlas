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
		},
	},
}

@export var skin := "traveller"

var _skin_rig := {}


func _skin_ok() -> bool:
	return skin != "" and SKINS.has(skin)


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
	_fix_materials.call_deferred()
	pose_changed.emit(p)
