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
## Front-facing step gait (story, 2026-11-18; v4 the same day after "잘린 다리가 코트 위를 삐져나와서 이상해 그리고
## 군인처럼 걷는 거 같아"). The card faces the camera and he walks toward it. Replaces the base gait's leg/body solve
## while walking (the base still owns the phase, the footprints and the stepping):
##  - weight shift: the whole figure rolls a few degrees toward the stance foot about the ground point between the feet
##    (hips sway over the planted foot), driven by a continuous signal through a soft spring, so it lags and settles;
##  - hips: inverted pendulum (highest on passing) + a small heel-strike dip-and-recover (bounce spring);
##  - body card (head/hat) trails the hips a beat (lag spring), squashes a touch on each heel strike, counter-twists;
##  - legs are NEVER slid or squashed: the stance leg is aimed at its footprint and stretched about the hidden hip
##    (≤ 8 %); the swing leg swaps to a pre-drawn bent-knee card (rig.json parts.leg_*.alt half/lift, front view, foot
##    coming toward us) matched to the hip→foot length, so no leg top or cuff band is ever exposed under the hem;
##  - arms (rig.json parts.arm_l/arm_r, calm walking figures): swing opposite to the legs, forward = toward the camera
##    (pitch) and a little inward, on a lagging spring (overlap). Off = the base gait (old benches).
@export var front_gait := false
@export var front_roll_deg := 0.6  ## weight-shift roll toward the stance foot per step
@export var front_bob := 0.003  ## extra hip rise at the passing position (world units, before height scaling)
@export var front_bounce := 0.04  ## heel-strike dip impulse (world units / s, before height scaling)
@export var front_lift := 1.0  ## swing foot lift multiplier (story sets it lower for struggling steps)
@export var front_lift_frac := 0.15  ## full swing-foot lift as a fraction of the leg length
@export var front_droop := 0.0  ## 0..1 heat: lower lift, smaller arm swing, slower and heavier body lag
@export var front_arm_swing := 1.0  ## arm swing multiplier (story: less while pushing into the wind)
@export var arm_roll_deg := 5.0  ## in-plane part of the arm swing (forward hand moves in toward the body)
@export var arm_pitch_deg := 20.0  ## out-of-plane part (forward hand comes toward the camera)
## 0..1 pushing into the wind: hunched (body card squashed, a little lower), arms tucked in toward the coat front
## (as if clutching it shut), their swing damped. Story: spread_stage sets it while the wind blows.
@export var front_hunch := 0.0
@export var arm_hold := -1  ## arm index (0 = image-left, 1 = image-right) that holds something: no swing
## Billboard (front_gait only): keep only this fraction of the base gait's card turn toward the walk direction
## (max_turn_deg), so the card faces the camera. 2026-11-18: on diagonal stretches (stream) the card was turned up to
## 20° toward the walk, the toward-the-card stride was seen obliquely and the legs opened into an A-frame on screen.
@export var front_turn_keep := 0.2
## Screen-sideways part of each foot's offset from under its hip (see _front_foot): kept at
## this fraction and soft-limited to front_max_side (world, at height 0.36), so legs stay near-parallel; the sideways
## travel of a diagonal walk is carried by the body (a few mm of sole slip instead of an A).
@export var front_side_keep := 0.35
@export var front_max_side := 0.012
## Leg depth vs the coat (2026-11-18 walk v7, "이번엔 또 다시 발이 코트를 벗어나"). The legs hang behind the body/hips
## cards and pitch toward the camera about the hip; a leg pitched by φ moves its card forward by d·sin φ at a distance d
## below the hip, so where it is still covered (down to the hem, rig.json leg vis row; the trouser seat for the no-coat and
## the opening of an open coat) it would come through the coat plane and draw its top/cuff band OVER the hem. In the front
## gait each leg sits deep enough behind the hips card that a pitch up to front_pitch_deg never reaches it there, the pitch
## is clamped to what that depth allows (forward: the covered length below the hip, back: the hidden top above it), and the
## footprints are pushed back by the same depth so a resting leg hangs straight down. A capped pitch leaves the sole a few
## mm off its print in DEPTH only (invisible from the front camera).
@export var front_pitch_deg := 20.0
@export var front_pitch_back_deg := 24.0

const CAST_PRINT := preload("res://art/cast/rig/cast_print.gdshader")
const CAST_EDGE := preload("res://art/cast/rig/cast_edge.gdshader")

var _skin_rig := {}
var _arm: Node3D  ## pivot (wrist) of an extra hinged arm part, e.g. the hat fanning in his hand
var _arm_card: PaperCard
var _shv := 0.0
var _base_lean := -1.0
## per leg: [{card, rest (hip→sole), ratio}], [0] = straight (the base _leg_cards[i]), then half / lift if the rig has them
var _leg_vars: Array = [[], []]
var _leg_shown := [0, 0]
var _arms: Array[Node3D] = []  ## shoulder pivots of the swinging arm cards (children of the body card)
var _arm_cards: Array[PaperCard] = []
var _arm_a := [0.0, 0.0]  ## arm swing (-1 back .. 1 forward), spring state
var _arm_v := [0.0, 0.0]
var _roll_f := 0.0  ## front gait weight-shift roll (spring)
var _roll_fv := 0.0
var _bounce := 0.0  ## heel-strike dip (spring)
var _bounce_v := 0.0
var _hl := 0.0  ## lagged hip height (body card trails it)
var _hl_v := 0.0
var _hl_ok := false
var _rl := 0.0  ## lagged roll (body card trails it)
var _rl_v := 0.0
var _last_step := -1
var _squash := 1.0
var _front_on := false
var _rim_retry := 0
var _occ_d := [0.0, 0.0]  ## covered length of each leg below its hip (hip → hem / seat), world
var _top_d := [0.0, 0.0]  ## hidden leg top above its hip, world
var _occ_back := 0.0  ## back face of the hips card (tilt z): every leg pixel that is covered must stay behind it
var _side_rig := false  ## side-profile figure: both legs on one hip joint, swung fore/aft in the card plane
var _mirror := false  ## side figure facing left (drawn facing right): the tilt node is mirrored in x
var _mirror_to := false
var _th := [0.0, 0.0]  ## side gait: leg angles (rad, + = foot forward), smoothed
var _hp := 0.0  ## unrigged hop phase
## Side gait (2026-11-18, three_pigs): classic brad-jointed paper puppet seen in profile. The stance leg sweeps back
## under the hip exactly as far as the body moves (no slide: x = stride·(½ − s), angle = asin(x / L)), the hips ride
## it (inverted pendulum), the swing leg comes through ahead with a small lift, the body leans into the walk.
@export var side_max_deg := 24.0
@export var side_lean_deg := 3.0
## Standing figures keep breathing / bobbing a little (no stage play of frozen cards). Story sets more for lively ones.
@export var idle_amount := 1.0
## Unrigged figure hop height (fraction of the height) and hop length (fraction of the height per hop).
@export var hop_frac := 0.07
@export var hop_len_frac := 0.42


func _skin_ok() -> bool:
	return skin != "" and not skin_def(skin).is_empty()


## Skins built from the shared cast catalog (game/art/cast/catalog.json, entries with `skin` == the skin id): every
## variant becomes a pose (cast id), rigged when rig.json has the id, else a single printed card that hops along.
## `hu` = catalog height_units per id (figures of one character are drawn at different heights: sitting, tiptoe).
static var _dyn_skins := {}


static func skin_def(s: String) -> Dictionary:
	if SKINS.has(s):
		return SKINS[s]
	if _dyn_skins.has(s):
		return _dyn_skins[s]
	var d := {"dir": "res://art/cast/rig/", "poses": {}, "paths": {}, "hu": {}, "views": {}}
	var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string("res://art/cast/catalog.json"))
	var arr: Array = []
	if parsed is Array:
		arr = parsed
	elif parsed is Dictionary:
		arr = (parsed as Dictionary).get("cards", [])
	for e: Dictionary in arr:
		if str(e.get("skin", "")) != s:
			continue
		var v := str(e.get("variant", e.get("pose", "")))
		d["poses"][v] = str(e["id"])
		var pth := str(e["path"])
		d["paths"][str(e["id"])] = pth if pth.begins_with("res://") else "res://" + pth
		d["hu"][str(e["id"])] = float(e.get("height_units", 0.0))
		d["views"][v] = str(e.get("view", "front"))
		if e.has("cycle"):  # flipbook frame of a drawn cycle (run): cycles[pose] = [paths in order]
			if not d.has("cycles"):
				d["cycles"] = {}
			var cy := str(e["cycle"])
			if not (d["cycles"] as Dictionary).has(cy):
				d["cycles"][cy] = []
			var fl: Array = d["cycles"][cy]
			while fl.size() <= int(e.get("frame", 0)):
				fl.append("")
			fl[int(e.get("frame", 0))] = d["paths"][str(e["id"])]
			d["views"][cy] = str(e.get("view", "side"))
			d["poses"][cy] = str(e["id"]) if not (d["poses"] as Dictionary).has(cy) or int(e.get("frame", 0)) == 0 else d["poses"][cy]
	if (d["poses"] as Dictionary).is_empty():
		d = {}
	_dyn_skins[s] = d
	return d


func _def() -> Dictionary:
	return skin_def(skin)


## View of a pose ("front" | "back" | "side"); traveller poses are all front.
func pose_view(p: String) -> String:
	return str((_def().get("views", {}) as Dictionary).get(p, "front"))


func has_pose(p: String) -> bool:
	return (_def().get("poses", {}) as Dictionary).has(p)


func is_side() -> bool:
	return _side_rig or (not _rigged and pose_view(pose) == "side")


## Pose + mirror in one paper turn (the card flips edge-on, swaps, flips back). mirror = side figure facing left.
## Expression state that every figure change respects (witch_candy v4, user: "계속 검은 입술로 있는지"): while
## mouth_state is "black" (ghost candy eaten) a figure without the black mouth maps to the black-mouth variant —
## <pose>_black if the catalog has one, the ghost cycles for walks, the ghost figure for standing poses; back views
## (no mouth) stay. mouth_wrong counts frames that still showed a normal mouth (BLACK_LIPS check).
var mouth_state := ""
var mouth_wrong := 0
var mouth_seen := false  ## the state was used in this run (the runner prints BLACK_LIPS only then)


func mouth_ok(p: String) -> bool:
	return mouth_state == "" or p.contains("ghost") or p.ends_with("_" + mouth_state) or pose_view(p) == "back"


func _mouth_map(p: String) -> String:
	if mouth_ok(p):
		return p
	if has_pose(p + "_" + mouth_state):
		return p + "_" + mouth_state
	if p in ["wow", "surprised", "startled", "scared"] and has_pose(("wow" if has_pose("wow_black") else "surprised") + "_" + mouth_state):
		return ("wow" if has_pose("wow_black") else "surprised") + "_" + mouth_state
	if pose_view(p) == "side" and has_pose("ghost_cycle") and (p.contains("cycle") or p.contains("walk")):
		return "ghost_cycle"
	if pose_view(p) == "front" and has_pose("ghost_front") and (p.contains("walk") or p.contains("front")):
		return "ghost_front"
	return "ghost" if has_pose("ghost") else p


func set_figure(p: String, mirror: bool, instant := false) -> void:
	if not has_pose(p):
		return
	if mouth_state != "":
		p = _mouth_map(p)
		if pose_view(p) != "side":
			mirror = false
	if p == pose and mirror == _mirror and (_flip_t < 0.0 or _flip_to == ""):
		return  # already showing it (or the flip back is finishing on it)
	if _flip_t >= 0.0 and p == _flip_to and mirror == _mirror_to:
		return  # this flip is already under way
	_mirror_to = mirror
	if instant or not is_inside_tree():
		_apply_pose(p)
		return
	_flip_to = p
	_flip_t = 0.0


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


## Foot position in the turn frame with its SCREEN-sideways offset from under hip i compressed (see front_side_keep).
## Screen-sideways = horizontal perpendicular to the puppet→camera direction (not the card x: the card may be turned a
## little toward the walk, and he may stand off the camera axis), so a toward-the-camera stride stays a depth stride.
func _front_foot(i: int, Ti: Transform3D, hip_x: float) -> Vector3:
	var f := Ti * _feet[i]
	var sv := Vector3(1, 0, 0)
	if camera:
		var c := Ti.basis * (camera.global_position - global_position)
		c.y = 0.0
		if c.length() > 1e-4:
			c = c.normalized()
			sv = Vector3(c.z, 0, -c.x)
	var a := (f - Vector3(hip_x, f.y, 0.0)).dot(sv)
	# step width follows the weight shift: with the damped roll (v6, 0.6°) the hips no longer travel over the stance
	# foot, so the feet stay under their hips (legs hang straight down inside the coat) instead of a wide-roll track
	var rf := clampf(front_roll_deg / 4.0, 0.15, 1.0)
	var ms := front_max_side * (height / 0.36) * rf
	f -= sv * (a - ms * tanh(a * front_side_keep * rf / ms))
	f.z += _hip_local[i].z  # footprint straight under the (deep) hip, see front_pitch_deg
	return f


## See `front_gait`. Works in the unscaled turn frame (x = card right, y = up, z = toward the camera) and writes the
## tilt node (local to the turn node), the body card (lag/squash/twist, local to the tilt) and the top-level legs
## (through the turn node's transform, so a pose-flip squash still applies on top).
func _front_step(dt: float) -> void:
	var T := Transform3D(Basis(Vector3.UP, _face_total), global_position)
	var Ti := T.affine_inverse()
	var n := int(floorf(_phase))
	var sw := n % 2
	var st := 1 - sw
	var s: float = _phase - floorf(_phase)
	var k := clampf(speed / 0.12, 0.45, 1.0)
	var dr := clampf(front_droop, 0.0, 1.0)
	var hs := height / 0.36
	if n != _last_step:  # heel strike of the foot that just landed: dip, recover with a little overshoot
		if _last_step >= 0:
			_bounce_v -= front_bounce * hs * k * (1.0 - 0.4 * dr)
		_last_step = n
	var bs := PaperSpring.step(_bounce, _bounce_v, 0.0, 15.0, 0.42, dt)
	_bounce = bs.x
	_bounce_v = bs.y
	# Weight shift: continuous (passes 0 at each heel strike), toward the stance foot (foot 0 is -X: roll +Z), lagged.
	var want_roll := -deg_to_rad(front_roll_deg) * sin(PI * _phase) * k
	var rs := PaperSpring.step(_roll_f, _roll_fv, want_roll, 11.0 - 3.0 * dr, 0.6, dt)
	_roll_f = rs.x
	_roll_fv = rs.y
	var B := Basis(Vector3(0, 0, 1), _roll_f) * Basis(Vector3(1, 0, 0), _lean.y) * Basis(Vector3(0, 0, 1), _lean.x)
	var f_st := _front_foot(st, Ti, _hip_local[st].x + _leg_rest[st].x)
	var piv := Vector3((_sole_x[0] + _sole_x[1]) * 0.5, 0.0, f_st.z)
	var P := piv - B * piv
	# Stance hip height: the straight stance leg reaches its footprint (inverted pendulum: highest on passing).
	var L_st := _leg_rest[st].length()
	var v := P + B * _hip_local[st] - f_st
	var hz := v.x * v.x + v.z * v.z
	var h := -v.y + sqrt(maxf(L_st * L_st - hz, L_st * L_st * 0.8))
	h += front_bob * hs * sin(PI * s) * k * (1.0 - 0.5 * dr) + _bounce - 0.006 * hs * dr
	_tilt.transform = Transform3D(B, P + Vector3(0, h, 0))
	# Body card (head, hat, coat): trails the hips' bob and roll a beat, squashes on the dip, shoulders counter-twist.
	if not _hl_ok:
		_hl = h
		_rl = _roll_f
		_hl_ok = true
	var w_lag := 17.0 - 6.0 * dr
	var hl := PaperSpring.step(_hl, _hl_v, h, w_lag, 0.55, dt)
	_hl = hl.x
	_hl_v = hl.y
	var rl := PaperSpring.step(_rl, _rl_v, _roll_f, w_lag * 0.7, 0.45, dt)
	_rl = rl.x
	_rl_v = rl.y
	var dy := clampf(_hl - h, -0.006 * hs, 0.006 * hs)
	var lag := clampf(_rl - _roll_f, -0.006, 0.006)
	var hp := (_hip_local[0] + _hip_local[1]) * 0.5
	hp.z = 0.0
	var bb := Basis(Vector3(0, 0, 1), lag) * Basis(Vector3.UP, deg_to_rad(0.5) * cos(PI * _phase) * k)
	_body.position = hp + bb * (_body_rest - hp) + Vector3(0, dy, 0)
	_body.rotation = bb.get_euler()
	_squash = 1.0 + clampf(_bounce / maxf(height, 0.01) * 1.3, -0.03, 0.02) - 0.035 * clampf(front_hunch, 0.0, 1.0)
	# Legs.
	var tb := _turn.global_transform
	var lift := front_lift_frac * front_lift * (1.0 - 0.35 * dr) * (0.7 + 0.3 * k)
	for i in 2:
		var hip := P + Vector3(0, h, 0) + B * _hip_local[i]
		var foot := _front_foot(i, Ti, hip.x + _leg_rest[i].x)
		var L := _leg_rest[i].length()
		if i == sw:
			# quick lift, then it comes down ahead of him (toward the camera)
			foot.y = lift * L * sin(PI * pow(s, 0.75))
		var to := _clamp_pitch(i, foot - hip, B)
		var ratio := to.length() / maxf(L, 1e-4)
		var vi := 0
		var vars: Array = _leg_vars[i]
		if i == sw:
			var best := 9.0
			for j in vars.size():
				var d := absf(ratio - float(vars[j]["ratio"])) - (0.03 if j == _leg_shown[i] else 0.0)
				if d < best:
					best = d
					vi = j
		_show_leg(i, vi)
		var vr: Dictionary = vars[vi] if vars.size() > vi else {"rest": _leg_rest[i], "ratio": 1.0}
		var rest := B * _leg_rest[i]
		var q := Quaternion.IDENTITY
		var ang := rest.angle_to(to)
		if ang > 1e-4:
			var ax := rest.cross(to)
			if ax.length() > 1e-6:
				q = Quaternion(ax.normalized(), minf(ang, deg_to_rad(max_leg_deg)))
		# stretch about the hip (the top stays hidden), never slide
		var sy := clampf(ratio / float(vr["ratio"]), 0.92, 1.08)
		var R := Basis(q) * B
		_legs[i].global_transform = tb * Transform3D(R * Basis.from_scale(Vector3(1, sy, 1)), hip)
	# Arms: opposite to the legs (arm 0 goes with leg 1). Leg forwardness: swing leg -1 → +1, stance +1 → -1.
	var fw := [0.0, 0.0]
	fw[sw] = -cos(PI * s)
	fw[st] = cos(PI * s)
	_step_arms(dt, [fw[1], fw[0]], k * (1.0 - 0.5 * dr) * front_arm_swing)


## Limit the leg's pitch out of the coat plane (tilt frame B) so no covered part of it comes through the hips/body
## cards (see front_pitch_deg). Keeps the hip→foot length and the in-plane direction.
func _clamp_pitch(i: int, to: Vector3, B: Basis) -> Vector3:
	var l := B.inverse() * to
	var yz := Vector2(-l.y, l.z)
	var r := yz.length()
	if r < 1e-5:
		return to
	var room := maxf(_occ_back - (_hip_local[i].z + thickness * 0.5) - thickness * 0.25, 0.0)
	var cf := minf(deg_to_rad(front_pitch_deg), asin(clampf(room / maxf(_occ_d[i], 1e-4), 0.0, 1.0)))
	var cb := minf(deg_to_rad(front_pitch_back_deg), asin(clampf(room / maxf(_top_d[i], 1e-4), 0.0, 1.0)))
	var ph := clampf(atan2(yz.y, yz.x), -cb, cf)
	l.y = -r * cos(ph)
	l.z = r * sin(ph)
	return B * l


func _step_arms(dt: float, want: Array, amp: float) -> void:
	if _arms.is_empty() or not _arms[0].visible:
		return
	for j in 2:
		var tgt: float = 0.0 if j == arm_hold else float(want[j]) * amp
		var r := PaperSpring.step(_arm_a[j], _arm_v[j], tgt, 10.0, 0.5, dt)
		_arm_a[j] = r.x
		_arm_v[j] = r.y
		var a: float = _arm_a[j]
		var tuck := clampf(front_hunch, 0.0, 1.0) if _front_on else 0.0
		var pitch := -a * deg_to_rad(arm_pitch_deg) * (1.0 if a > 0.0 else 0.3) - deg_to_rad(14.0) * tuck
		var roll := (a * deg_to_rad(arm_roll_deg) + deg_to_rad(9.0) * tuck) * (1.0 if j == 0 else -1.0)
		_arms[j].rotation = Vector3(pitch, 0.0, roll)


func _show_leg(i: int, vi: int) -> void:
	if _leg_shown[i] == vi:
		return
	_leg_shown[i] = vi
	var vars: Array = _leg_vars[i]
	for j in vars.size():
		(vars[j]["card"] as PaperCard).visible = j == vi


## Same as PaperPuppet.set_pose (animated card flip unless `instant`), but accepts every pose the skin maps.
func set_pose(p: String, instant := false) -> void:
	if not _skin_ok():
		super.set_pose(p, instant)
		return
	if not (_def()["poses"] as Dictionary).has(p) or (p == pose and _flip_t < 0.0):
		return
	if instant or not is_inside_tree():
		_apply_pose(p)
		return
	_flip_to = p
	_flip_t = 0.0


func _process(dt: float) -> void:
	if mouth_state != "":
		mouth_seen = true
		if is_visible_in_tree() and not mouth_ok(pose):
			mouth_wrong += 1
	if _base_lean < 0.0:
		_base_lean = lean_deg
	# The base lean scales with speed/0.3; divide that back out so a slow, struggling walk still leans in.
	lean_deg = _base_lean + push_lean_deg / clampf(speed / 0.3, 0.12, 1.0)
	# Billboard: the base turns the card max_turn_deg toward the walk direction; front_gait keeps only a fraction,
	# side figures none (the profile is drawn in the card plane, it faces the camera square on).
	var mt := max_turn_deg
	if front_gait:
		max_turn_deg = mt * front_turn_keep
	if is_side():
		max_turn_deg = 0.0
	super._process(dt)
	max_turn_deg = mt
	if _turn.scale.x < 0.3:  # paper turn: narrow to 30 %, swap there; never a card edge-on sliver (15 % still read as
		_turn.scale.x = 0.3   # a sliver in 8 fps tiles of runs turning at their marks, turnip v5)
	var fdt := PaperSpring.frame_dt(dt)
	if fdt <= 0.0:
		return
	if not _rigged:
		if _skin_ok() and _def().has("paths"):
			_hop_step(fdt)
		return
	_squash = 1.0
	if _side_rig:
		_side_step(fdt)
	elif front_gait and _walking and _flip_t < 0.0:
		_front_step(fdt)
		_front_on = true
	else:
		if _front_on:  # back to the straight legs, arms relax
			_front_on = false
			_hl_ok = false
			_last_step = -1
			for i in 2:
				_show_leg(i, 0)
		if plant_exact and _walking:
			_aim_legs_exact()
		_step_arms(fdt, [0.0, 0.0], 0.0)
		if not _walking and idle_amount > 0.0 and _def().has("paths"):
			# standing: a slow breath and a little weight shift (story cast keeps moving between lines)
			# (body card only, about the hips, so the planted legs stay put)
			var ip := (_hip_local[0] + _hip_local[1]) * 0.5
			ip.z = 0.0
			var ib := Basis(Vector3(0, 0, 1), deg_to_rad(0.7) * idle_amount * sin(_t * 1.3 + 0.7))
			_body.position = ip + ib * (_body.position - ip) + Vector3(0, height * 0.005 * idle_amount * (0.5 + 0.5 * sin(_t * 2.6)), 0)
			_body.rotation.z += ib.get_euler().z
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
		_body.scale = Vector3(1.0 + 0.5 * (1.0 - _squash), _squash, 1.0)
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


## Unrigged figure (one card): a paper hop per step along the ground, rocking a little forward/back; standing, a
## slow breathing bob. Mirrored for side figures facing left.
signal foot_contact(cycle: String, frame: int)  ## a drawn-cycle frame came up (footsteps) / a paper hop landed
var _cyc_tex: Dictionary = {}  ## path -> Texture2D
var _cyc_i := -1


## Drawn cycle (run): the frame advances with the ground travelled (one cycle per stride length, so the feet don't
## skate), a small bounce on the flight frame.
func _cycle_step(frames: Array, dt: float) -> void:
	var m := -1.0 if _mirror else 1.0
	var n := frames.size()
	var stride := height * 0.9  # ground covered per cycle
	if speed > 0.03:
		_hp += speed * dt / maxf(stride, 0.01)
	var f := int(floorf(fposmod(_hp, 1.0) * n)) % n
	if f != _cyc_i:
		_cyc_i = f
		if speed > 0.03:
			foot_contact.emit(pose, f)
		var pth := str(frames[f])
		if not _cyc_tex.has(pth):
			_cyc_tex[pth] = load(pth)
		_body.texture = _cyc_tex[pth]
	var flight := (n == 4 and f == 3) or (n == 2 and false)
	var y := height * (0.05 if flight else (0.015 if f == 0 else 0.0))
	var pl := 0.03 * sin(_pose_hop * PI)
	# the forward lean is for profiles only: a front / back card tilted 4° reads as leaning sideways (휘청; turnip v5)
	var lean := -deg_to_rad(4.0) * m if pose_view(pose) == "side" else 0.0
	_tilt.transform = Transform3D(Basis.from_scale(Vector3(m, 1, 1)) * Basis(Vector3(0, 0, 1), lean), Vector3(0, y + pl, 0))
	_body.position = Vector3.ZERO
	_body.rotation = Vector3.ZERO


func _hop_step(dt: float) -> void:
	var cyc: Dictionary = _def().get("cycles", {})
	if cyc.has(pose):
		_cycle_step(cyc[pose], dt)
		return
	var m := -1.0 if _mirror else 1.0
	var moving := speed > 0.03
	var y := 0.0
	var rz := 0.0
	if moving:
		var hp0 := floorf(_hp)
		_hp += speed * dt / maxf(height * hop_len_frac, 0.01)
		if floorf(_hp) != hp0:
			foot_contact.emit("hop", 0)  # a paper hop landed
		var amp := height * hop_frac * clampf(speed / 0.25, 0.5, 1.2)
		y = absf(sin(PI * _hp)) * amp
		rz = -deg_to_rad(4.0) * cos(TAU * _hp)  # leans into each hop, tips back on landing
	else:
		_hp = 0.0
		y = height * 0.008 * idle_amount * (0.5 + 0.5 * sin(_t * 2.6))
		rz = deg_to_rad(1.0) * idle_amount * sin(_t * 1.3 + 0.7)
	var pl := 0.03 * sin(_pose_hop * PI)
	_tilt.transform = Transform3D(Basis.from_scale(Vector3(m, 1, 1)) * Basis(Vector3(0, 0, 1), rz), Vector3(0, y + pl, 0))
	_body.position = Vector3.ZERO
	_body.rotation = Vector3.ZERO
	_shv = lerpf(_shv, shiver, 1.0 - exp(-(9.0 if shiver > _shv else 0.9) * dt))
	if _shv > 0.003:
		_body.rotation.z = deg_to_rad(3.4) * _shv * sin(_t * TAU * 12.0)


## See side_max_deg. Turn frame: x = the way the figure faces (mirrored for leftward), y up, z toward the camera.
func _side_step(dt: float) -> void:
	var m := -1.0 if _mirror else 1.0
	var L := maxf(_leg_rest[0].length(), 1e-4)
	var walking := _walking and speed > 0.01
	var S := minf(_stride, 2.0 * L * sin(deg_to_rad(side_max_deg))) if walking else 0.0
	var n := int(floorf(_phase))
	var sw := n % 2
	var s: float = _phase - floorf(_phase)
	var e := s * s * (3.0 - 2.0 * s)
	var want := [0.0, 0.0]
	var lift := 0.0
	if walking:
		want[1 - sw] = asin(clampf(S * (0.5 - s) / L, -0.9, 0.9))  # stance: sweeps back as the body moves on
		want[sw] = asin(clampf(S * (e - 0.5) / L, -0.9, 0.9))  # swing: comes through ahead
		lift = 0.12 * L * sin(PI * s)
	var k := 1.0 - exp(-(40.0 if walking else 10.0) * dt)
	for i in 2:
		_th[i] = lerpf(_th[i], want[i], k)
	var st := 1 - sw
	var h := L * cos(_th[st]) - L if walking else 0.0  # hips ride the stance leg
	var lean := deg_to_rad(side_lean_deg) * clampf(speed / 0.2, 0.0, 1.0)
	var breathe := 0.0 if walking else height * 0.006 * idle_amount * (0.5 + 0.5 * sin(_t * 2.6))
	var pl := 0.03 * sin(_pose_hop * PI)
	var B := Basis(Vector3(0, 0, 1), -lean)
	var off := Vector3(0, h + breathe + pl, 0)
	_tilt.transform = Transform3D(Basis.from_scale(Vector3(m, 1, 1)), Vector3.ZERO) * Transform3D(B, off)
	_body.position = _body_rest
	_body.rotation = Vector3.ZERO
	var M := _turn.global_transform * Transform3D(Basis.from_scale(Vector3(m, 1, 1)), Vector3.ZERO)
	for i in 2:
		var hip := B * _hip_local[i] + off + (Vector3(0, lift, 0) if (walking and i == sw) else Vector3.ZERO)
		_legs[i].global_transform = M * Transform3D(Basis(Vector3(0, 0, 1), _th[i]) * B, hip)


func _apply_pose(p: String) -> void:
	if not _skin_ok():
		super._apply_pose(p)
		return
	var sk: Dictionary = _def()
	var dir: String = sk["dir"]
	if _skin_rig.is_empty():
		_skin_rig = JSON.parse_string(FileAccess.get_file_as_string(dir + "rig.json"))
	var poses: Dictionary = sk["poses"]
	var key: String = poses.get(p, poses.get("walk", poses.get("calm", "")))
	_mirror = _mirror_to
	var r: Dictionary = _skin_rig.get(key, {})
	# figure height relative to the skin's reference (calm) figure, from the catalog's height_units
	var hu: Dictionary = sk.get("hu", {})
	var href := float(hu.get(poses.get("calm", key), 0.0))
	var hk := float(hu.get(key, 0.0))
	var hscale := hk / href if href > 0.0 and hk > 0.0 else 1.0
	if r.is_empty():
		if not (sk.get("paths", {}) as Dictionary).has(key):
			push_warning("CastPuppet: no rig for %s, falling back to legacy art" % key)
			super._apply_pose(p)
			return
		# Unrigged figure (legs drawn together): one printed card that hops along like a paper doll.
		pose = p
		_rigged = false
		_side_rig = false
		_body.texture = load(str(sk["paths"][key]))
		_body.height = height * hscale
		_body.position = Vector3.ZERO
		_body.rotation = Vector3.ZERO
		_body_rest = Vector3.ZERO
		for l in _legs:
			l.visible = false
		_hips.visible = false
		for a in _arms:
			a.visible = false
		if _arm:
			_arm.visible = false
		pose_changed.emit(p)
		return
	pose = p
	_rigged = true
	_side_rig = bool((r["parts"]["leg_l"] as Dictionary).get("side", false))
	var fb: Array = r["full_bbox"]
	_scale_px = height * hscale / float(fb[3] - fb[1])
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
		_occ_back = -thickness * 1.15 - thickness * 0.35
		_occ_d[i] = maxf(float(part.get("vis", [hip[1]])[0]) - float(hip[1]), 0.0) * s
		_top_d[i] = maxf(float(hip[1]) - float(lb[1]), 0.0) * s
		_hip_local[i] = Vector3((hip[0] - cxf) * s, (fy1 - hip[1]) * s, z)
		var c := _leg_cards[i]
		c.texture = load(dir + key + "_" + side + ".png")
		c.height = (lb[3] - lb[1]) * s
		c.position = Vector3((lcx - hip[0]) * s, -(lb[3] - hip[1]) * s, 0.0)
		_leg_rest[i] = c.position
		_sole_x[i] = (lcx - cxf) * s
		_legs[i].visible = true
		_setup_leg_vars(i, part, dir + key + "_" + side, s)
	if front_gait and not _side_rig:  # deep enough that a front_pitch_deg pitch keeps the covered part behind the hips card
		var dmax := 0.0
		for i in 2:
			dmax = maxf(dmax, maxf(_occ_d[i] * sin(deg_to_rad(front_pitch_deg)), _top_d[i] * sin(deg_to_rad(front_pitch_back_deg))))
		for i in 2:
			_hip_local[i].z = _occ_back - thickness * (0.75 + 1.0 * i) - dmax
	_apply_arm(r, s, bb)
	_apply_swing_arms(r, s, bb, dir + key)
	_fix_materials.call_deferred()
	pose_changed.emit(p)


## Optional hinged arm part (rig.json parts.<name> with bbox + pivot, see cut_cast_rig.ARM_PARTS): a card on the body
## card, swung about the wrist in _process. Hidden for poses without one.
func _apply_arm(r: Dictionary, s: float, bb: Array) -> void:
	var name_ := ""
	for k in (r["parts"] as Dictionary).keys():
		if not (k in ["body", "hips", "leg_l", "leg_r", "arm_l", "arm_r"]):
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
	var key: String = _def()["poses"].get(pose, "")
	_arm_card.texture = load(_def()["dir"] + key + "_" + name_ + ".png")
	_arm_card.height = (ab[3] - ab[1]) * s
	# body card origin = bottom-centre of its bbox
	_arm.position = Vector3((pv[0] - (bb[0] + bb[2]) * 0.5) * s, (bb[3] - pv[1]) * s, thickness * 1.2)
	_arm_card.position = Vector3(((ab[0] + ab[2]) * 0.5 - pv[0]) * s, (pv[1] - ab[3]) * s, 0.0)
	_arm.rotation = Vector3.ZERO
	_arm.visible = true


## Leg variants (rig.json parts.leg_*.alt, tools/cast/lift_legs.py): extra cards on the same top-level leg node,
## hip pivot shared, each with its own hip→sole rest and natural length ratio. Only one is visible at a time.
func _setup_leg_vars(i: int, part: Dictionary, base: String, s: float) -> void:
	var vars: Array = _leg_vars[i]
	for j in range(1, vars.size()):
		(vars[j]["card"] as PaperCard).queue_free()
	vars.clear()
	var hip: Array = part["hip"]
	vars.append({"card": _leg_cards[i], "rest": _leg_rest[i], "ratio": 1.0})
	var alt: Dictionary = part.get("alt", {})
	for vname in ["half", "lift"]:
		if not alt.has(vname):
			continue
		var lb: Array = alt[vname]["bbox"]
		var c := PaperCard.new()
		c.thickness = thickness
		c.texture = load(base + "_" + vname + ".png")
		c.height = (lb[3] - lb[1]) * s
		c.position = Vector3(((float(lb[0]) + float(lb[2])) * 0.5 - hip[0]) * s, -(lb[3] - hip[1]) * s, 0.0)
		c.visible = false
		_legs[i].add_child(c)
		vars.append({"card": c, "rest": c.position, "ratio": float(alt[vname]["ratio"])})
	_leg_cards[i].visible = true
	_leg_shown[i] = 0


## Swinging arm cards (rig.json parts.arm_l / arm_r with bbox + shoulder pivot, tools/cast/walk_arms.py): children of
## the body card, in front of it, rotated about the shoulder in _step_arms. Hidden for figures with baked arms.
func _apply_swing_arms(r: Dictionary, s: float, bb: Array, base: String) -> void:
	var has: bool = (r["parts"] as Dictionary).has("arm_l")
	if _arms.is_empty():
		if not has:
			return
		for j in 2:
			var pv := Node3D.new()
			pv.name = "Arm%d" % j
			var c := PaperCard.new()
			c.thickness = thickness
			pv.add_child(c)
			_body.add_child(pv)
			_arms.append(pv)
			_arm_cards.append(c)
	for j in 2:
		_arms[j].visible = has
		_arm_a[j] = 0.0
		_arm_v[j] = 0.0
		_arms[j].rotation = Vector3.ZERO
		if not has:
			continue
		var part: Dictionary = r["parts"]["arm_l" if j == 0 else "arm_r"]
		var ab: Array = part["bbox"]
		var pv: Array = part["pivot"]
		var c := _arm_cards[j]
		c.texture = load(base + ("_arm_l.png" if j == 0 else "_arm_r.png"))
		c.height = (ab[3] - ab[1]) * s
		_arms[j].position = Vector3((pv[0] - (bb[0] + bb[2]) * 0.5) * s, (bb[3] - pv[1]) * s, thickness * 1.3)
		c.position = Vector3(((ab[0] + ab[2]) * 0.5 - pv[0]) * s, (pv[1] - ab[3]) * s, 0.0)


## Base materials + the cast print shader's rim window (see cast_print.gdshader): no cream rim on the hips piece, on
## the shoulder cap of a swinging arm, on the hidden leg tops, or (no-coat figures) along the trouser seat where the
## legs join. Puppet textures are unique to the puppet, so their cached materials are ours to tune.
func _fix_materials() -> void:
	super._fix_materials()
	if not _rigged or not _skin_ok():
		return
	var key: String = _def()["poses"].get(pose, "")
	var r: Dictionary = _skin_rig.get(key, {})
	if r.is_empty():
		return
	var parts: Dictionary = r["parts"]
	var bb: Array = parts["body"]["bbox"]
	var body_min := 0.0
	var body_max := 1.0
	if "_nocoat" in key:
		var hy := float(parts["leg_l"]["hip"][1])
		body_max = clampf((hy - 0.04 * (bb[3] - bb[1]) - bb[1]) / float(bb[3] - bb[1]), 0.0, 1.0)
	_rim_window(_body, body_min, body_max, 0.0028)
	if body_max < 1.0:
		_join_edge(_body, 0.0, body_max, body_max, 1.0)
	_rim_window(_hips, 0.0, -1.0, 0.0)
	_join_edge(_hips, 2.0, 2.0, 0.0, 1.0)
	for i in 2:
		var vars: Array = _leg_vars[i]
		var p: Dictionary = parts["leg_l" if i == 0 else "leg_r"]
		for j in vars.size():
			var c: PaperCard = vars[j]["card"]
			var lb: Array = p["bbox"] if j == 0 else p["alt"]["half" if j == 1 else "lift"]["bbox"]
			var vis_y := float(p.get("vis", [lb[1]])[0])
			var vmin := clampf((vis_y + 6.0 - lb[1]) / float(lb[3] - lb[1]), 0.0, 1.0)
			_rim_window(c, vmin, 1.0, 0.0016)
			_join_edge(c, vmin, 1.0, 0.0, vmin)
			_set_ao(c, 0.018, 0.3, 0.0016)
	for j in _arm_cards.size():
		if not _arms[j].visible:
			continue
		var part: Dictionary = parts["arm_l" if j == 0 else "arm_r"]
		var ab: Array = part["bbox"]
		var py := float(part["pivot"][1]) + 20.0
		var vmin := clampf((py - ab[1]) / float(ab[3] - ab[1]), 0.0, 1.0)
		_rim_window(_arm_cards[j], vmin, 1.0, 0.0016)
		_join_edge(_arm_cards[j], vmin, 1.0, vmin, minf(vmin + 0.15, 1.0))
		_set_ao(_arm_cards[j], 0.0, 0.0, 0.0016)
		# no shadow from the arms: swung toward the camera they threw dark blocks over the coat / trousers
		_arm_cards[j].cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF


## Edge wall (card side, surface 2) of a puppet join: cream cut core only for texture rows v_lo..v_hi (UV.y, 0 = top);
## outside it the wall takes the card's own average colour of rows s_lo..s_hi, so a join shows no light line.
## (The no-coat body's bottom edge over the legs read as a cream line at the crotch, 2026-11-18.)
func _join_edge(c: PaperCard, v_lo: float, v_hi: float, s_lo: float, s_hi: float) -> void:
	if c.mesh == null or c.texture == null:
		return
	var m := c.get_surface_override_material(2) as ShaderMaterial
	if m == null:
		return
	if m.shader != CAST_EDGE:
		m = m.duplicate() as ShaderMaterial
		m.shader = CAST_EDGE
		c.set_surface_override_material(2, m)
	var h := c.height
	m.set_shader_parameter("band_lo", (1.0 - v_hi) * h)  # card local y: 0 at the bottom, h at the top
	m.set_shader_parameter("band_hi", (1.0 - v_lo) * h)
	m.set_shader_parameter("join_color", _avg_color(c.texture, s_lo, s_hi).darkened(0.1))


static func _avg_color(tex: Texture2D, v0: float, v1: float) -> Color:
	var img := tex.get_image()
	if img == null:
		return Color(0.3, 0.15, 0.08)
	if img.is_compressed():
		img = img.duplicate()
		img.decompress()
	var w := img.get_width()
	var h := img.get_height()
	var acc := Vector3.ZERO
	var n := 0
	var y0 := clampi(int(v0 * h), 0, h - 1)
	var y1 := clampi(int(v1 * h), y0 + 1, h)
	for y in range(y0, y1, maxi(1, (y1 - y0) / 24)):
		for x in range(w / 6, w - w / 6, maxi(1, w / 24)):
			var c := img.get_pixel(x, y)
			if c.a > 0.9:
				acc += Vector3(c.r, c.g, c.b)
				n += 1
	if n == 0:
		return Color(0.3, 0.15, 0.08)
	acc /= n
	return Color(acc.x, acc.y, acc.z)


func _rim_window(c: PaperCard, vmin: float, vmax: float, rim: float) -> void:
	if c.mesh == null:
		if c.texture != null and _rim_retry < 30:
			_rim_retry += 1
			_fix_materials.call_deferred()
		return
	var m := c.get_surface_override_material(0) as ShaderMaterial
	if m == null:
		return
	if m.shader != CAST_PRINT:
		# own copy (PaperCard's static material cache must not end up holding this shader)
		m = m.duplicate() as ShaderMaterial
		m.shader = CAST_PRINT
		c.set_surface_override_material(0, m)
	m.set_shader_parameter("rim_v_min", vmin)
	m.set_shader_parameter("rim_v_max", vmax)
	m.set_shader_parameter("rim_width", rim)
	m.set_shader_parameter("rim_mix", 0.0)  # no cream die-cut rim on any puppet (2026-11-23, see PaperCard._materials)
