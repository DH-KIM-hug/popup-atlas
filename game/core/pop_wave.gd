class_name PopWave
extends RefCounted
## Pops a set of PopHinges in a staggered wave from an origin, and folds them back.
## delay = start + distance / speed + back-row lag + jitter. Back rows (smaller z than the
## origin, farther from the camera) come a little later, so a spread rises front-to-back
## like a page opening. Heavy pieces start a touch later than light ones around them.
##
##   var wave := PopWave.new()
##   var dur := wave.pop(PopWave.collect(page), Vector3.ZERO)
##   ...
##   wave.fold(hinges, Vector3.ZERO)

var speed := 5.5  ## world units per second the wave front travels
var jitter := 0.07  ## seconds of random spread per piece
var back_lag := 0.05  ## extra seconds per unit of depth behind the origin
var weight_lag := 0.03  ## extra seconds per unit of weight above 1
var fold_speed := 8.0  ## folding back is quicker than rising
var fold_jitter := 0.05
## A piece lying under another's flat footprint rises this long after the covering piece starts
## (so it never pushes up through it), and folds this long before it (so it is down in time).
var cover_gap := 0.12
var fold_cover_gap := 0.14


## All PopHinges under `root` (including root itself), depth first.
static func collect(root: Node) -> Array[PopHinge]:
	var out: Array[PopHinge] = []
	_collect(root, out)
	return out


static func _collect(n: Node, out: Array[PopHinge]) -> void:
	if n is PopHinge:
		out.append(n)
	for c in n.get_children():
		_collect(c, out)


## Delay (s) for one hinge in a rising wave from `origin`.
func delay_for(h: PopHinge, origin: Vector3, start := 0.0) -> float:
	var p := h.global_position - origin
	var d := Vector2(p.x, p.z).length()
	var back := maxf(0.0, -p.z)
	return start + d / speed + back * back_lag + maxf(0.0, h.weight - 1.0) * weight_lag + randf() * jitter


## Pops every hinge; returns the time (s) when the last one starts moving.
func pop(hinges: Array, origin: Vector3, start := 0.0) -> float:
	var d: Array[float] = []
	for h: PopHinge in hinges:
		d.append(delay_for(h, origin, start))
	_order(d, cover_pairs(hinges), cover_gap, true)
	var last := 0.0
	for i in hinges.size():
		(hinges[i] as PopHinge).pop_up(d[i])
		last = maxf(last, d[i])
	return last


## Pairs [a, b]: hinge b stands inside hinge a's flat footprint (a lies over b when folded).
## Footprint = the card's height along its fold side and half its width across; the height comes
## from meta "card_h" (else weight * 0.4) and the half width from meta "half_w" (else height * 0.5).
static func cover_pairs(hinges: Array) -> Array:
	var out := []
	for i in hinges.size():
		var a: PopHinge = hinges[i]
		var h: float = a.get_meta("card_h", a.weight * 0.4)
		var hw: float = a.get_meta("half_w", h * 0.5)
		var frame := (a.get_parent() as Node3D).global_transform.affine_inverse() if a.get_parent() is Node3D else Transform3D()
		var o := frame * a.global_position
		for j in hinges.size():
			if i == j:
				continue
			var p: Vector3 = frame * (hinges[j] as PopHinge).global_position - o
			var along := -p.z * float(a.fold)
			if along > 0.0 and along < h * 0.95 and absf(p.x) < hw * 0.9:
				out.append([i, j])
	return out


## Relaxes delays so covered pieces wait for (rise) / lead (fold) their covering piece.
static func _order(d: Array[float], pairs: Array, gap: float, rising: bool) -> void:
	for it in 4:
		var changed := false
		for pr in pairs:
			var a: int = pr[0]
			var b: int = pr[1]
			if rising and d[b] < d[a] + gap:
				d[b] = d[a] + gap
				changed = true
			elif not rising and d[a] < d[b] + gap:
				d[a] = d[b] + gap
				changed = true
		if not changed:
			return


## Folds every hinge back flat. outside_in = true folds the far pieces first (the wave closes
## toward the origin, like a book shutting); false folds outward from the origin.
func fold(hinges: Array, origin: Vector3, start := 0.0, outside_in := true) -> float:
	var maxd := 0.0
	var ds: Array[float] = []
	for h: PopHinge in hinges:
		var p := h.global_position - origin
		var d := Vector2(p.x, p.z).length()
		ds.append(d)
		maxd = maxf(maxd, d)
	var dl: Array[float] = []
	for i in hinges.size():
		var d: float = (maxd - ds[i]) if outside_in else ds[i]
		dl.append(start + d / fold_speed + randf() * fold_jitter)
	_order(dl, cover_pairs(hinges), fold_cover_gap, false)
	var last := 0.0
	for i in hinges.size():
		(hinges[i] as PopHinge).fold_down(dl[i])
		last = maxf(last, dl[i])
	return last


## Snaps all hinges to a state with no motion (scene setup).
static func snap_all(hinges: Array, up: bool) -> void:
	for h: PopHinge in hinges:
		h.snap(up)
