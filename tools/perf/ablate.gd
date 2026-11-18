extends "res://addons/agentkit/agent_job.gd"
## Ablation bench (component F): build meadow (view arg), then for each variant toggle parts and measure
## gpu/cpu ms, draws, primitives over N frames (Vulkan for GPU times). Also a geometry audit by category.
##   gd_run.run_script(P, "/abs/tools/perf/ablate.gd", {"view":0,"variants":[...],"frames":120}, headless=False,
##                     extra_args=["--rendering-driver","vulkan"])

func run() -> Dictionary:
	var size := Vector2i(1366, 1024)
	var cap = load("res://addons/agentkit/agent_capture.gd").new()
	var vp: SubViewport = cap.make_viewport(self, size, false)
	var scene: PackedScene = load(str(arg("scene", "res://scenes/world/meadow.tscn")))
	var w = scene.instantiate()
	if "view" in w:
		w.view = int(arg("view", 0))
		w.walk = false
		w.pop_on_load = bool(arg("pop", false))
	var t0 := Time.get_ticks_usec()
	vp.add_child(w)
	var build_ms := (Time.get_ticks_usec() - t0) / 1000.0
	await wait_frames(30)
	var rid := vp.get_viewport_rid()
	RenderingServer.viewport_set_measure_render_time(rid, true)
	var out := {"build_ms": build_ms, "audit": _audit(w)}
	var res := {}
	for v in arg("variants", ["base"]):
		var undo := _apply(w, vp, str(v))
		await wait_frames(15)
		var g := []
		var c := []
		var d := 0.0
		var p := 0.0
		for i in int(arg("frames", 90)):
			await process_frame
			g.append(RenderingServer.viewport_get_measured_render_time_gpu(rid))
			c.append(RenderingServer.viewport_get_measured_render_time_cpu(rid))
			d = maxf(d, Performance.get_monitor(Performance.RENDER_TOTAL_DRAW_CALLS_IN_FRAME))
			p = maxf(p, Performance.get_monitor(Performance.RENDER_TOTAL_PRIMITIVES_IN_FRAME))
		g.sort()
		c.sort()
		res[str(v)] = {"gpu_med": snappedf(g[g.size() / 2], 0.01), "cpu_med": snappedf(c[c.size() / 2], 0.01), "draws": d, "prims": p}
		undo.call()
		await wait_frames(5)
	out["variants"] = res
	return out


func _geoms(n: Node, acc: Array) -> void:
	if n is GeometryInstance3D:
		acc.append(n)
	for ch in n.get_children():
		_geoms(ch, acc)


func _cat(g: Node) -> String:
	var p := g.get_parent()
	if g is ContactShadows:
		return "contact"
	if p and p.name == "StaticCards":
		return "statics"
	if p is PopHinge or (p and p.get_parent() is PopHinge):
		return "hinged"
	var q := g
	while q:
		if q.name == "Ground":
			return "ground"
		if q.name == "Traveller":
			return "traveller"
		if q.name == "Ambient":
			return "ambient"
		q = q.get_parent()
	return "other:" + g.get_class()


func _tris(m: Mesh) -> Array:
	var t := 0
	var surf := 0
	if m == null:
		return [0, 0]
	if m is ArrayMesh:
		for s in m.get_surface_count():
			var a: Array = m.surface_get_arrays(s)
			var idx = a[Mesh.ARRAY_INDEX]
			t += (idx.size() if idx != null and idx.size() > 0 else (a[Mesh.ARRAY_VERTEX] as PackedVector3Array).size()) / 3
		surf = m.get_surface_count()
	else:
		surf = m.get_surface_count()
		var fs := m.get_faces()
		t = fs.size() / 3
	return [t, surf]


func _audit(w: Node) -> Dictionary:
	var acc := []
	_geoms(w, acc)
	var cats := {}
	var mesh_tris := {}
	for g in acc:
		var k := _cat(g)
		if not cats.has(k):
			cats[k] = {"nodes": 0, "instances": 0, "surfaces": 0, "tris": 0, "shadow_nodes": 0, "materials": {}}
		var e: Dictionary = cats[k]
		e["nodes"] += 1
		var n := 1
		var m: Mesh = null
		if g is MultiMeshInstance3D:
			var mm: MultiMesh = g.multimesh
			if mm:
				n = mm.instance_count
				m = mm.mesh
		elif g is MeshInstance3D:
			m = g.mesh
		var key := str(m.get_rid()) if m else ""
		if not mesh_tris.has(key):
			mesh_tris[key] = _tris(m)
		var tr: Array = mesh_tris[key]
		e["instances"] += n
		e["surfaces"] += tr[1]
		e["tris"] += tr[0] * n
		if g.cast_shadow != GeometryInstance3D.SHADOW_CASTING_SETTING_OFF:
			e["shadow_nodes"] += 1
		if g is MeshInstance3D:
			for s in tr[1]:
				var mat = g.get_active_material(s)
				if mat:
					e["materials"][mat.get_rid()] = 1
	for k in cats:
		cats[k]["materials"] = cats[k]["materials"].size()
	return cats


func _apply(w: Node, vp: SubViewport, v: String) -> Callable:
	match v:
		"base":
			return func(): pass
		"noshadow":
			w.rig.key.shadow_enabled = false
			return func(): w.rig.key.shadow_enabled = true
		"halfres":
			vp.scaling_3d_scale = 0.5
			return func(): vp.scaling_3d_scale = 1.0
		"nostatics":
			w.statics.visible = false
			return func(): w.statics.visible = true
		"statics_noshadow":
			for c in w.statics.get_children():
				c.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			return func():
				for c in w.statics.get_children():
					c.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
		"nohinged":
			for h in w.hinges:
				h.get_parent().visible = false
			return func():
				for h in w.hinges:
					h.get_parent().visible = true
		"noground":
			w.ground.visible = false
			return func(): w.ground.visible = true
		"nocontact":
			w.contact.visible = false
			return func(): w.contact.visible = true
		"nopost":
			w.rig.post.visible = false
			w.rig.environment.glow_enabled = false
			w.rig.dof_enabled = false
			return func():
				w.rig.post.visible = true
				w.rig.environment.glow_enabled = true
				w.rig.dof_enabled = true
		"cardshadows_off":
			var smi = w.batch.get_node("Shadows")
			smi.visible = false
			return func(): smi.visible = true
		"cards_off":
			w.batch.visible = false
			return func(): w.batch.visible = true
		"nofog":
			w.rig.environment.fog_enabled = false
			return func(): w.rig.environment.fog_enabled = true
	return func(): pass
