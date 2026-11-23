extends SceneTree
## House orbit audit (2026-11-23, user: "집들은 무조건 입체적으로 아주 잘 들어맞게").
## Runs a tale at a beat, waits for the spread, then for every house on the page (story set pieces given by
## --houses=a,b,... plus the template village's house cards, --tmpl=N nearest the stage focus) renders an orbit of
## solo views (only the house's meshes, on a magenta background, sharp lens) and one story-camera still. A python pass
## (tools/story/house_audit.py) turns the magenta pixels enclosed by the house into the seam / light-leak count.
##   tools/story/house_orbit.sh TALE BEAT OUT_DIR [houses] [tmpl]
## Out: OUT_DIR/<tale>__<house>__<view>.png, OUT_DIR/<tale>__story.png, OUT_DIR/<tale>__meta.json

const LAYER := 1 << 19
const VIEWS := [  # name, yaw from the front (deg, + = camera to the house's right), elevation (deg)
	["front", 0.0, 10.0], ["r35", 35.0, 12.0], ["l35", -35.0, 12.0], ["r70", 70.0, 10.0], ["l70", -70.0, 10.0],
	["back_r", 145.0, 14.0], ["back_l", -145.0, 14.0], ["high", 30.0, 52.0], ["low", -25.0, 2.5]]

var out_dir := ""
var tale := ""
var beat := ""
var houses: Array = []
var kits: Array = []
var tmpl := 3
var settle := 6.0
var story_node: Node
var _t := 0.0
var _phase := 0
var _done := false


func _initialize() -> void:
	for a: String in OS.get_cmdline_user_args():
		if a.begins_with("--orbit-out="):
			out_dir = a.get_slice("=", 1)
		elif a.begins_with("--houses="):
			houses = Array(a.get_slice("=", 1).split(",", false))
		elif a.begins_with("--kit="):
			kits = Array(a.get_slice("=", 1).split(",", false))
		elif a.begins_with("--tmpl="):
			tmpl = int(a.get_slice("=", 1))
		elif a.begins_with("--tale="):
			tale = a.get_slice("=", 1)
		elif a.begins_with("--beat="):
			beat = a.get_slice("=", 1)
		elif a.begins_with("--settle="):
			settle = float(a.get_slice("=", 1))
	DirAccess.make_dir_recursive_absolute(out_dir)
	var ps: PackedScene = load("res://stories/%s/story.tscn" % tale)
	story_node = ps.instantiate()
	root.add_child.call_deferred(story_node)


func _process(dt: float) -> bool:
	if _done:
		return true
	if _phase == 0:
		var st: Variant = story_node.get("stage") if is_instance_valid(story_node) else null
		if st != null and is_instance_valid(st) and st.is_built:
			_t += dt
			if _t > settle:
				_phase = 1
				_run.call_deferred(st)
	return false


func _frames(n: int) -> void:
	for i in n:
		await process_frame
	await RenderingServer.frame_post_draw


func _snap(path: String) -> void:
	await _frames(3)
	var img := root.get_texture().get_image()
	img.save_png(path)


func _set_layers(n: Node, on: bool) -> void:
	if n is VisualInstance3D:
		var vi := n as VisualInstance3D
		if on:
			vi.set_meta("_orb_layers", vi.layers)
			vi.layers = LAYER
		elif vi.has_meta("_orb_layers"):
			vi.layers = int(vi.get_meta("_orb_layers"))
	for c in n.get_children():
		_set_layers(c, on)


func _canvas(n: Node, vis: bool) -> void:
	if n is CanvasLayer:
		(n as CanvasLayer).visible = vis
	for c in n.get_children():
		_canvas(c, vis)


func _run(st: Node) -> void:
	var meta := {"tale": tale, "houses": []}
	await _snap("%s/%s__story_%s.png" % [out_dir, tale, beat])
	story_node.process_mode = Node.PROCESS_MODE_DISABLED
	_canvas(root, false)
	var cam := Camera3D.new()
	cam.fov = 30.0
	cam.near = 0.02
	cam.far = 60.0
	var env := Environment.new()
	env.background_mode = Environment.BG_COLOR
	env.background_color = Color(1, 0, 1)
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(0.55, 0.55, 0.6)
	env.ambient_light_energy = 0.6
	env.tonemap_mode = Environment.TONE_MAPPER_LINEAR
	cam.environment = env
	cam.cull_mask = LAYER
	root.add_child(cam)
	cam.current = true
	var targets: Array = []  # [name, node, front basis (Basis), centre, size, depth, info]
	var sets: Dictionary = st.get("sets")
	for nm in houses:
		if not sets.has(nm):
			print("ORBIT no set piece ", nm)
			continue
		var sp: Node3D = sets[nm]
		if sp.has_method("bands_up"):
			sp.bands_up(99)
		sp.visible = true
		if sp.get("walls") != null:
			(sp.get("walls") as Node3D).visible = true  # the stage hides a front while its camera is inside
		targets.append([str(nm), sp, sp])
	# template village houses: a proxy card (the batch draws the real one) next to the body, nearest the focus first
	var world: Node = st.get("world")
	var focus: Vector3 = st.spot_point("anchor") if st.has_method("spot_point") else Vector3.ZERO
	var hc: Array = (world.get("house_cards") as Array).duplicate() if world and world.get("house_cards") != null else []
	hc.sort_custom(func(a, b): return (a["pos"] as Vector3).distance_to(focus) < (b["pos"] as Vector3).distance_to(focus))
	var n_t := 0
	for i in hc.size():
		if n_t >= tmpl:
			break
		var h: Dictionary = hc[i]
		var hg: Variant = h["hinge"]
		if hg != null and is_instance_valid(hg) and ((hg as PopHinge).openness() < 0.9 or not (hg as Node3D).is_visible_in_tree()):
			continue  # cleared for the story (folded down): not on the page
		n_t += 1
		var holder := Node3D.new()
		holder.name = "OrbitProxy%d" % i
		root.add_child(holder)
		var xf: Transform3D
		if h["hinge"] != null and is_instance_valid(h["hinge"]):
			xf = (h["hinge"] as Node3D).global_transform
		else:
			xf = Transform3D(Basis(Vector3.UP, float(h["yaw"])) * Basis(Vector3.BACK, float(h["lean"])) * Basis(Vector3.RIGHT, float(h["tilt"])), h["pos"])
		holder.global_transform = xf
		if not h.get("building", false):
			var c := PaperCard.new()
			c.texture = load(str(h["path"]))
			c.height = float(h["h"])
			c.thickness = float(h["thick"])
			c.back_print = true
			holder.add_child(c)
		var bd: Variant = h.get("body")
		var bx := ""
		if bd != null and is_instance_valid(bd):
			var dup: Node3D = (bd as Node3D).duplicate()
			holder.add_child(dup)
			dup.transform = Transform3D.IDENTITY
			bx = "body"
		var pp: Vector3 = h["pos"]
		targets.append(["tmpl_%s_%d_%d" % [str(h["id"]), int(pp.x * 10), int(pp.z * 10)], holder, holder])
	# kit buildings (Building): stood at the spread's anchor one at a time, solo orbit + context shots
	var kit_nodes := {}
	for kn in kits:
		var sp2 := SetPiece.new()
		sp2.name = "Kit_" + str(kn)
		(st as Node).add_child(sp2)
		sp2.setup_building(str(kn), 1.0, 1)
		sp2.global_position = focus
		sp2.rotation.y = deg_to_rad(float(world.get("rig").yaw_deg))
		for h in sp2.all_hinges():
			h.snap(true)
		sp2.visible = false
		kit_nodes[kn] = sp2
		targets.append(["kit_" + str(kn), sp2, sp2])
	await _frames(30)
	for tg in targets:
		if (tg[1] as Node3D).name.begins_with("Kit_"):
			for k2 in kit_nodes:
				(kit_nodes[k2] as Node3D).visible = kit_nodes[k2] == tg[1]
			if st.has_method("_clear_area"):
				st._clear_area((tg[1] as Node3D).global_position, 1.2, 2.2)
			await _frames(20)
		var nm: String = tg[0]
		var node: Node3D = tg[1]
		_set_layers(node, true)
		await _frames(2)
		var aabb := _aabb(node)
		var basis := Basis(Vector3.UP, node.global_rotation.y)
		var fwd := basis * Vector3(0, 0, 1)
		var right := basis * Vector3(1, 0, 0)
		var c := aabb.get_center()
		var r := maxf(aabb.size.length() * 0.5, 0.2)
		var d := r / tan(deg_to_rad(cam.fov * 0.5)) * 0.85
		var info := {"name": nm, "aabb": [aabb.position.x, aabb.position.y, aabb.position.z, aabb.size.x, aabb.size.y, aabb.size.z]}
		if node.get("width") != null:
			info["width"] = node.get("width")
			info["height"] = node.get("height")
			info["box"] = node.get("box") != null
		if node.get("body") != null and node.get("card") != null:
			var cd: Node3D = node.get("card")
			var bd: Node3D = node.get("body")
			info["card_vs_body"] = [str(cd.global_transform), str(bd.global_transform), str(cd.get("thickness")), str((bd as HouseBody).depth)]
		# local extents (front frame): width, height, depth
		info["local"] = _local_extent(node)
		for v in VIEWS:
			var yaw := deg_to_rad(float(v[1]))
			var el := deg_to_rad(float(v[2]))
			var dir := (fwd * cos(yaw) + right * sin(yaw)) * cos(el) + Vector3.UP * sin(el)
			cam.global_position = c + dir * d
			cam.look_at(c, Vector3.UP)
			await _snap("%s/%s__%s__%s.png" % [out_dir, tale, nm, v[0]])
		_set_layers(node, false)
		if node.name.begins_with("Kit_"):
			await _context_shots(node, nm, cam, env, c, r)
			node.visible = false
		(meta["houses"] as Array).append(info)
		print("ORBIT ", nm, " ", JSON.stringify(info))
	var f := FileAccess.open("%s/%s__meta.json" % [out_dir, tale], FileAccess.WRITE)
	f.store_string(JSON.stringify(meta, " "))
	f.close()
	print("ORBIT_DONE ", targets.size())
	_done = true
	quit()


## Full-scene shots of a kit building on the meadow (world light and haze, the look's grade on): a three-quarter
## establishing shot, and for the castle an approach along the road, the gate and a tower window.
func _context_shots(node: Node3D, nm: String, cam: Camera3D, env: Environment, c: Vector3, r: float) -> void:
	cam.environment = null
	cam.cull_mask = 0xFFFFF
	cam.attributes = null
	var post: Variant = null
	for cl in root.find_children("Post", "CanvasLayer", true, false):
		(cl as CanvasLayer).visible = true
		post = cl
	var basis := Basis(Vector3.UP, node.global_rotation.y)
	var shots := [["ctx", Vector3(0.55, 0.32, 1.0).normalized() * r * 2.6, Vector3(0, -r * 0.15, 0)]]
	var O := node.global_position
	if "castle" in nm:
		# castle-local [camera, look-at] from its origin on the ground (kit castle: gate front at z 1.5, tower1 at 1.5, 1.5)
		shots.append(["approach", Vector3(0.3, 0.62, 5.0), Vector3(0.0, 0.5, 1.4), true])
		shots.append(["gate", Vector3(0.35, 0.28, 2.55), Vector3(0.0, 0.3, 1.7), true])
		shots.append(["window", Vector3(2.0, 1.22, 2.5), Vector3(1.5, 0.9, 1.84), true])
		var st0: Node = node.get_parent()
		if st0.has_method("_clear_area"):
			for zz in [2.4, 3.4, 4.4]:
				st0._clear_area(O + basis * Vector3(0, 0, zz), 0.9, 1.0)
		await _frames(10)
	for sh in shots:
		var org := O if sh.size() > 3 else c
		cam.global_position = org + basis * (sh[1] as Vector3)
		cam.look_at(org + basis * (sh[2] as Vector3), Vector3.UP)
		await _snap("%s/%s__%s__%s.png" % [out_dir, tale, nm, sh[0]])
	cam.environment = env
	cam.cull_mask = LAYER
	if post:
		(post as CanvasLayer).visible = false


func _aabb(n: Node) -> AABB:
	var out := AABB()
	var first := true
	for vi in _vis(n):
		if not vi.is_visible_in_tree():
			continue
		var b: AABB = vi.global_transform * vi.get_aabb()
		if b.size.length() > 30.0:
			continue
		out = b if first else out.merge(b)
		first = false
	return out


func _local_extent(n: Node3D) -> Array:
	var inv := n.global_transform.affine_inverse()
	var mn := Vector3(INF, INF, INF)
	var mx := -mn
	for vi in _vis(n):
		if not vi.is_visible_in_tree():
			continue
		var b: AABB = vi.get_aabb()
		for k in 8:
			var p: Vector3 = inv * (vi.global_transform * b.get_endpoint(k))
			mn = mn.min(p)
			mx = mx.max(p)
	return [snappedf(mx.x - mn.x, 0.001), snappedf(mx.y - mn.y, 0.001), snappedf(mx.z - mn.z, 0.001)]


func _vis(n: Node) -> Array:
	var out: Array = []
	if n is VisualInstance3D:
		out.append(n)
	for c in n.get_children():
		out.append_array(_vis(c))
	return out
