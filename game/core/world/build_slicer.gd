class_name BuildSlicer
extends RefCounted
## Time-slices a long build over several frames (component F, perf): the next spread is built while the current page
## plays, a few milliseconds per frame, instead of in one 2-5 s frame under the page turn.
## Builders call `await slicer.tick()` between units of work. budget_usec <= 0: never yields (synchronous build, the
## function still completes in the same call because no await is reached).

var budget_usec := 0
var frames := 0  ## frames the build was spread over
var max_slice_ms := 0.0
var phases := {}  ## name -> ms (wall time of each phase, including yields)
var _t0 := 0
var _tree: SceneTree
var _phase := ""
var _phase_t := 0


func _init(budget_ms := 0.0, tree: SceneTree = null) -> void:
	budget_usec = int(budget_ms * 1000.0)
	_tree = tree
	_t0 = Time.get_ticks_usec()


func tick() -> void:
	if budget_usec <= 0 or _tree == null:
		return
	var now := Time.get_ticks_usec()
	if now - _t0 < budget_usec:
		return
	var slice_ms := (now - _t0) / 1000.0
	if slice_ms > 12.0:
		print("PERF long_slice ms=", snappedf(slice_ms, 0.1), " phase=", _phase)
	max_slice_ms = maxf(max_slice_ms, slice_ms)
	frames += 1
	await _tree.process_frame
	_t0 = Time.get_ticks_usec()


## Phase bookkeeping (PERF prints): phase("ground") ... phase("") closes the last one.
func phase(name: String) -> void:
	var now := Time.get_ticks_usec()
	if _phase != "":
		phases[_phase] = snappedf(float(phases.get(_phase, 0.0)) + (now - _phase_t) / 1000.0, 0.1)
	_phase = name
	_phase_t = now


func finish() -> void:
	phase("")
	if budget_usec > 0:
		max_slice_ms = maxf(max_slice_ms, (Time.get_ticks_usec() - _t0) / 1000.0)
