class_name PaperSpring
## Damped spring helpers (component D). Semi-implicit Euler, sub-stepped to <= 1/240 s and dt clamped to
## 0.1 s so frame hitches (captures, loading) never blow up the motion.

const MAX_H := 1.0 / 240.0

## When > 0, every component-D node advances by this fixed step per frame (deterministic captures),
## same idea as PopHinge.fixed_dt.
static var fixed_dt := 0.0


static func frame_dt(dt: float) -> float:
	return fixed_dt if fixed_dt > 0.0 else dt


## Returns Vector2(x, v) after dt toward `target` with angular frequency `omega` (rad/s) and damping ratio `zeta`.
static func step(x: float, v: float, target: float, omega: float, zeta: float, dt: float) -> Vector2:
	dt = minf(dt, 0.1)
	var n := maxi(1, ceili(dt / MAX_H))
	var h := dt / n
	for i in n:
		v += ((target - x) * omega * omega - v * 2.0 * zeta * omega) * h
		x += v * h
	return Vector2(x, v)


## Vector3 version; returns [x, v].
static func step3(x: Vector3, v: Vector3, target: Vector3, omega: float, zeta: float, dt: float) -> Array:
	dt = minf(dt, 0.1)
	var n := maxi(1, ceili(dt / MAX_H))
	var h := dt / n
	for i in n:
		v += ((target - x) * omega * omega - v * 2.0 * zeta * omega) * h
		x += v * h
	return [x, v]
