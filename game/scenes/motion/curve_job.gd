extends RefCounted
## Offline angle-vs-time dump for three PopHinges (small / medium / large) through one rise and one
## fold. Run: gd_run.run_script(P, "res://scenes/motion/curve_job.gd:curves", args={"dt": 1/240.})
## Returns {"t": [...], "small": {"angle": [...], "twist": [...]}, ...} angles in degrees,
## where 90 = standing upright and 0 = flat, plus measured overshoot / settle / landing stats.

const WEIGHTS := {"small": 0.5, "medium": 1.0, "large": 2.2}


func curves(job) -> Dictionary:
	var dt: float = job.arg("dt", 1.0 / 240.0)
	var rise_s: float = job.arg("rise_s", 1.6)
	var fold_s: float = job.arg("fold_s", 1.4)
	seed(5)
	var out := {"t": [], "rise_s": rise_s}
	var hs := {}
	for k in WEIGHTS:
		var h := PopHinge.new()
		h.weight = WEIGHTS[k]
		job.root.add_child(h)
		h._freq_j = 1.0
		h.set_process(false)
		h.pop_up(0.0)
		h.set_process(false)
		hs[k] = h
		out[k] = {"angle": [], "twist": [], "weight": WEIGHTS[k]}
	var n_rise := int(rise_s / dt)
	var n := n_rise + int(fold_s / dt)
	var landed := {}
	for k in hs:
		var kk: String = k
		hs[k].landed.connect(func(_w, sp): if not landed.has(kk): landed[kk] = sp)
	for i in n:
		if i == n_rise:
			for k in hs:
				hs[k].fold_down(0.0)
				hs[k].set_process(false)
		out["t"].append(i * dt)
		for k in hs:
			var h: PopHinge = hs[k]
			h.step(dt)
			out[k]["angle"].append(90.0 * h.openness())
			out[k]["twist"].append(rad_to_deg(h.twist()))
	# Stats.
	var stats := {}
	for k in hs:
		var a: Array = out[k]["angle"]
		var peak := 0.0
		var settle := 0.0
		var reach := -1.0
		var twist_peak := 0.0
		var rebounds := 0
		for i in n_rise:
			peak = maxf(peak, a[i])
			twist_peak = maxf(twist_peak, absf(out[k]["twist"][i]))
			if reach < 0.0 and a[i] >= 89.5:
				reach = out["t"][i]
			if absf(a[i] - 90.0) > 0.5 or absf(out[k]["twist"][i]) > 1.0:
				settle = out["t"][i]
			if reach >= 0.0 and i > 0 and i < n_rise - 1 and absf(a[i] - 90.0) > 0.3 \
					and (a[i] - a[i - 1]) * (a[i + 1] - a[i]) < 0.0:
				rebounds += 1
		var bounce_peak := 0.0
		var touched := false
		for i in range(n_rise, n):
			if a[i] <= 0.01:
				touched = true
			elif touched:
				bounce_peak = maxf(bounce_peak, a[i])
		var flat_t := -1.0
		for i in range(n_rise, n):
			if a[i] <= 0.01 and flat_t < 0.0:
				flat_t = out["t"][i] - rise_s
		var rest_t := 0.0
		for i in range(n_rise, n):
			if a[i] > 0.5:
				rest_t = out["t"][i] - rise_s
		stats[k] = {"overshoot_deg": peak - 90.0, "settle_s": settle, "reach_s": reach,
			"settle_after_vertical_s": settle - reach, "rebounds": rebounds, "twist_peak_deg": twist_peak,
			"fold_rebound_deg": bounce_peak, "first_touch_s": flat_t, "rest_s": rest_t,
			"land_speed": landed.get(k, 0.0)}
	out["stats"] = stats
	return {"ok": true, "curves": out}
