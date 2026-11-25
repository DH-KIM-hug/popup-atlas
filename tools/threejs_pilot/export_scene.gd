extends SceneTree
## three.js pilot (docs/THREEJS_PILOT.md): READ-ONLY recorder of one story beat.
## Runs the real StoryRunner (autoplay) at a beat and writes everything the renderer sees, so the web scene uses the
## same meshes, prints, positions, camera and sound as Godot, not a re-imagining:
##   scene.json  meshes (once per Mesh), materials (shader + uniforms), textures, lights, environment, look rig,
##               then one entry per frame with what changed (node transforms / mesh / material swaps, material
##               uniforms, camera, DOF, audio starts / stops / volumes, caption text, tap targets).
##   geo.bin     vertex / index arrays (float32 / uint32, triangles re-wound counter-clockwise for three.js).
##   tex/        runtime-built images (card atlas pages, ground maps) as webp; file textures are listed by res path
##               and copied by tools/threejs_pilot/pack_assets.py.
## Run (windowed: runtime textures need a renderer), Godot flags before `--`:
##   tools/story/with_godot.sh /Applications/Godot.app/Contents/MacOS/Godot --path game --resolution 1366x1024 \
##     --fixed-fps 30 --quit-after 2400 --script res://../tools/threejs_pilot/export_scene.gd -- \
##     --tale=turnip --beat=seed --autoplay --pilot-out=<dir> --pilot-until=grow
## Nothing in game/ is changed.

var out_dir := ""
var until_beat := "grow"
var max_sec := 70.0
var tail_sec := 0.6

var runner: Node
var frame_i := 0
var done := false
var bin: FileAccess
var bin_off := 0

var meshes := {}  # mesh instance id -> int id
var mesh_list: Array = []
var mats := {}  # material instance id -> int id
var mat_list: Array = []
var mat_objs: Array = []
var mat_sig: Array = []  # last param signature per material id
var texs := {}  # texture instance id -> int id
var tex_list: Array = []
var nodes := {}  # node instance id -> int id
var node_list: Array = []
var node_state := {}  # node int id -> last state dict
var players := {}  # player instance id -> last state
var frames: Array = []
var unhandled := {}
var last_caption := ""
var last_rig := ""
var last_env := ""
var last_lights := {}
var last_buses := ""
var tap_log: Array = []
var beat_log: Array = []
var last_beat := ""
var last_expect := ""
var shader_files := {}


func _init() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--pilot-out="):
			out_dir = a.get_slice("=", 1)
		elif a.begins_with("--pilot-until="):
			until_beat = a.get_slice("=", 1)
		elif a.begins_with("--pilot-max="):
			max_sec = float(a.get_slice("=", 1))
	if out_dir == "":
		out_dir = ProjectSettings.globalize_path("res://../pilot/threejs/public/data/turnip_seed")
	DirAccess.make_dir_recursive_absolute(out_dir + "/tex")
	bin = FileAccess.open(out_dir + "/geo.bin", FileAccess.WRITE)
	_start.call_deferred()


func _start() -> void:
	var sc := (load("res://stories/turnip/story.tscn") as PackedScene).instantiate()
	root.add_child(sc)
	current_scene = sc
	runner = sc
	process_frame.connect(_on_frame)


# ------------------------------------------------------------------ helpers

func _xf(t: Transform3D) -> Array:
	var b := t.basis
	return [snappedf(b.x.x, 1e-6), snappedf(b.x.y, 1e-6), snappedf(b.x.z, 1e-6), 0,
		snappedf(b.y.x, 1e-6), snappedf(b.y.y, 1e-6), snappedf(b.y.z, 1e-6), 0,
		snappedf(b.z.x, 1e-6), snappedf(b.z.y, 1e-6), snappedf(b.z.z, 1e-6), 0,
		snappedf(t.origin.x, 1e-6), snappedf(t.origin.y, 1e-6), snappedf(t.origin.z, 1e-6), 1]


func _ser(v: Variant) -> Variant:
	match typeof(v):
		TYPE_NIL, TYPE_BOOL, TYPE_INT, TYPE_STRING:
			return v
		TYPE_FLOAT:
			return snappedf(v, 1e-6)
		TYPE_VECTOR2, TYPE_VECTOR2I:
			return [v.x, v.y]
		TYPE_VECTOR3, TYPE_VECTOR3I:
			return [v.x, v.y, v.z]
		TYPE_VECTOR4, TYPE_VECTOR4I, TYPE_QUATERNION:
			return [v.x, v.y, v.z, v.w]
		TYPE_COLOR:
			return [v.r, v.g, v.b, v.a]
		TYPE_TRANSFORM3D:
			return _xf(v)
		TYPE_BASIS:
			return _xf(Transform3D(v, Vector3.ZERO))
		TYPE_STRING_NAME:
			return str(v)
		TYPE_PACKED_FLOAT32_ARRAY, TYPE_PACKED_INT32_ARRAY:
			return Array(v) if v.size() <= 64 else "packed[%d]" % v.size()
		TYPE_OBJECT:
			if v == null:
				return null
			if v is Texture:
				return {"tex": _tex_id(v)}
			if v is Resource:
				return {"res": v.get_class(), "path": (v as Resource).resource_path}
			return {"obj": v.get_class()}
	return str(v)


func _write(arr: PackedByteArray) -> Array:
	var off := bin_off
	bin.store_buffer(arr)
	bin_off += arr.size()
	var pad := (4 - (bin_off % 4)) % 4
	for i in pad:
		bin.store_8(0)
	bin_off += pad
	return [off, arr.size()]


# ------------------------------------------------------------------ textures

func _tex_id(t: Texture) -> int:
	var k := t.get_instance_id()
	if texs.has(k):
		return texs[k]
	var id := tex_list.size()
	texs[k] = id
	var e := {"id": id, "class": t.get_class()}
	tex_list.append(e)
	var rp := t.resource_path
	if t is AtlasTexture:
		var at := t as AtlasTexture
		e["atlas"] = _tex_id(at.atlas) if at.atlas else -1
		e["region"] = _ser(at.region)
		e["margin"] = _ser(at.margin)
		return id
	if rp != "" and not rp.contains("::") and t is Texture2D:
		e["res"] = rp
		e["size"] = _ser((t as Texture2D).get_size())
		return id
	var fname := "t%03d" % id
	if t is Texture2DArray or t is Texture3D:
		var ta := t as Texture2DArray
		var n: int = ta.get_layers()
		var files: Array = []
		for i in n:
			var img := ta.get_layer_data(i)
			files.append(_save_img(img, "%s_l%d" % [fname, i], e))
		e["layers"] = files
		e["size"] = [ta.get_width(), ta.get_height()]
		return id
	if t is Texture2D:
		var img := (t as Texture2D).get_image()
		if img == null:
			e["missing"] = true
			return id
		e["file"] = _save_img(img, fname, e)
		e["size"] = [img.get_width(), img.get_height()]
	else:
		e["unsupported"] = true
	return id


func _save_img(img: Image, fname: String, e: Dictionary) -> Variant:
	if img.is_compressed():
		img.decompress()
	var f := img.get_format()
	e["format"] = f
	e["mipmaps"] = img.has_mipmaps()
	if f in [Image.FORMAT_RF, Image.FORMAT_RGF, Image.FORMAT_RGBF, Image.FORMAT_RGBAF, Image.FORMAT_RH, Image.FORMAT_RGH,
			Image.FORMAT_RGBH, Image.FORMAT_RGBAH]:
		var im := img.duplicate() as Image
		im.convert(Image.FORMAT_RGBAF)
		var r := _write(im.get_data())
		return {"float": r, "w": im.get_width(), "h": im.get_height()}
	var im2 := img.duplicate() as Image
	if im2.has_mipmaps():
		im2.clear_mipmaps()
	if f == Image.FORMAT_L8 or f == Image.FORMAT_R8:
		im2.convert(Image.FORMAT_RGB8)
	elif f != Image.FORMAT_RGBA8 and f != Image.FORMAT_RGB8:
		im2.convert(Image.FORMAT_RGBA8)
	var p := "tex/%s.webp" % fname
	im2.save_webp(out_dir + "/" + p, false)
	return p


# ------------------------------------------------------------------ materials

func _mat_id(m: Material) -> int:
	if m == null:
		return -1
	var k := m.get_instance_id()
	if mats.has(k):
		return mats[k]
	var id := mat_list.size()
	mats[k] = id
	var e := {"id": id, "class": m.get_class(), "priority": m.render_priority}
	mat_list.append(e)
	mat_objs.append(m)
	mat_sig.append("")
	if m is ShaderMaterial:
		var sh := (m as ShaderMaterial).shader
		if sh:
			var sp := sh.resource_path
			if sp == "" or sp.contains("::"):
				sp = "inline_%d.gdshader" % id
				var f := FileAccess.open(out_dir + "/" + sp, FileAccess.WRITE)
				f.store_string(sh.code)
			e["shader"] = sp
			shader_files[sp] = int(shader_files.get(sp, 0)) + 1
		e["params"] = _mat_params(m)
		mat_sig[id] = JSON.stringify(e["params"])
	elif m is BaseMaterial3D:
		var b := m as BaseMaterial3D
		var p := {}
		for n in ["albedo_color", "albedo_texture", "transparency", "alpha_scissor_threshold", "shading_mode", "cull_mode",
				"vertex_color_use_as_albedo", "roughness", "metallic", "emission_enabled", "emission", "emission_energy_multiplier",
				"billboard_mode", "no_depth_test", "depth_draw_mode", "blend_mode", "texture_filter", "uv1_scale", "uv1_offset",
				"disable_receive_shadows", "shadow_to_opacity", "albedo_texture_force_srgb", "normal_enabled", "normal_texture"]:
			p[n] = _ser(b.get(n))
		e["params"] = p
		mat_sig[id] = JSON.stringify(p)
	else:
		unhandled["material:" + m.get_class()] = true
	if m.next_pass:
		e["next_pass"] = _mat_id(m.next_pass)
	return id


func _mat_params(m: ShaderMaterial) -> Dictionary:
	var p := {}
	if m.shader == null:
		return p
	for u: Dictionary in m.shader.get_shader_uniform_list(true):
		var n := str(u["name"])
		if int(u.get("usage", 0)) & PROPERTY_USAGE_GROUP or int(u.get("usage", 0)) & PROPERTY_USAGE_SUBGROUP:
			continue
		var v: Variant = m.get_shader_parameter(n)
		if v == null:
			continue  # default from the shader source
		p[n] = _ser(v)
	return p


# ------------------------------------------------------------------ meshes

func _mesh_id(mesh: Mesh) -> int:
	if mesh == null:
		return -1
	var k := mesh.get_instance_id()
	if meshes.has(k):
		return meshes[k]
	var id := mesh_list.size()
	meshes[k] = id
	var e := {"id": id, "class": mesh.get_class(), "surfaces": [], "aabb": [_ser(mesh.get_aabb().position), _ser(mesh.get_aabb().size)]}
	mesh_list.append(e)
	for s in mesh.get_surface_count():
		var arr := mesh.surface_get_arrays(s)
		var se := {"material": _mat_id(mesh.surface_get_material(s))}
		if mesh is ArrayMesh:
			se["prim"] = (mesh as ArrayMesh).surface_get_primitive_type(s)
		else:
			se["prim"] = Mesh.PRIMITIVE_TRIANGLES
		var attrs := {}
		var v: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
		se["count"] = v.size()
		attrs["position"] = _write(v.to_byte_array())
		if arr[Mesh.ARRAY_NORMAL] != null and (arr[Mesh.ARRAY_NORMAL] as PackedVector3Array).size() > 0:
			attrs["normal"] = _write((arr[Mesh.ARRAY_NORMAL] as PackedVector3Array).to_byte_array())
		if arr[Mesh.ARRAY_TANGENT] != null and (arr[Mesh.ARRAY_TANGENT] as PackedFloat32Array).size() > 0:
			attrs["tangent"] = _write((arr[Mesh.ARRAY_TANGENT] as PackedFloat32Array).to_byte_array())
		if arr[Mesh.ARRAY_COLOR] != null and (arr[Mesh.ARRAY_COLOR] as PackedColorArray).size() > 0:
			attrs["color"] = _write((arr[Mesh.ARRAY_COLOR] as PackedColorArray).to_byte_array())
		if arr[Mesh.ARRAY_TEX_UV] != null and (arr[Mesh.ARRAY_TEX_UV] as PackedVector2Array).size() > 0:
			attrs["uv"] = _write((arr[Mesh.ARRAY_TEX_UV] as PackedVector2Array).to_byte_array())
		if arr[Mesh.ARRAY_TEX_UV2] != null and (arr[Mesh.ARRAY_TEX_UV2] as PackedVector2Array).size() > 0:
			attrs["uv2"] = _write((arr[Mesh.ARRAY_TEX_UV2] as PackedVector2Array).to_byte_array())
		for ci in 4:
			var c: Variant = arr[Mesh.ARRAY_CUSTOM0 + ci]
			if c != null and typeof(c) in [TYPE_PACKED_FLOAT32_ARRAY] and (c as PackedFloat32Array).size() > 0:
				attrs["custom%d" % ci] = _write((c as PackedFloat32Array).to_byte_array())
			elif c != null and typeof(c) == TYPE_PACKED_BYTE_ARRAY and (c as PackedByteArray).size() > 0:
				unhandled["custom_bytes"] = true
		se["attrs"] = attrs
		var idx: PackedInt32Array
		if arr[Mesh.ARRAY_INDEX] != null and (arr[Mesh.ARRAY_INDEX] as PackedInt32Array).size() > 0:
			idx = arr[Mesh.ARRAY_INDEX]
		if se["prim"] == Mesh.PRIMITIVE_TRIANGLES:
			if idx.is_empty():
				idx.resize(v.size())
				for i in v.size():
					idx[i] = i
			# Godot front faces are clockwise; three.js counter-clockwise
			for i in range(0, idx.size() - 2, 3):
				var t := idx[i + 1]
				idx[i + 1] = idx[i + 2]
				idx[i + 2] = t
		else:
			unhandled["prim:%d" % se["prim"]] = true
		if not idx.is_empty():
			se["index"] = _write(idx.to_byte_array())
			se["icount"] = idx.size()
		e["surfaces"].append(se)
	return id


# ------------------------------------------------------------------ nodes

func _node_id(n: Node) -> int:
	var k := n.get_instance_id()
	if nodes.has(k):
		return nodes[k]
	var id := node_list.size()
	nodes[k] = id
	var path := str(runner.get_path_to(n)) if runner and runner.is_ancestor_of(n) else str(n.get_path())
	var e := {"id": id, "class": n.get_class(), "name": str(n.name), "path": path}
	if n.get_script():
		e["script"] = (n.get_script() as Script).resource_path.get_file()
	var p := n.get_parent()
	while p and not e.has("owner_script"):
		if p.get_script():
			e["owner_script"] = (p.get_script() as Script).resource_path.get_file()
			e["owner_name"] = str(p.name)
		p = p.get_parent()
	if n is MultiMeshInstance3D:
		var mm := (n as MultiMeshInstance3D).multimesh
		e["mm"] = _mm_dump(mm)
	node_list.append(e)
	return id


func _mm_dump(mm: MultiMesh) -> Dictionary:
	if mm == null:
		return {}
	var d := {"mesh": _mesh_id(mm.mesh), "count": mm.instance_count, "visible": mm.visible_instance_count,
		"colors": mm.use_colors, "custom": mm.use_custom_data}
	var xf := PackedFloat32Array()
	var cu := PackedFloat32Array()
	var co := PackedFloat32Array()
	var n := mm.instance_count if mm.visible_instance_count < 0 else mini(mm.visible_instance_count, mm.instance_count)
	d["n"] = n
	for i in n:
		var t := mm.get_instance_transform(i)
		xf.append_array(PackedFloat32Array(_xf(t)))
		if mm.use_custom_data:
			var c := mm.get_instance_custom_data(i)
			cu.append_array(PackedFloat32Array([c.r, c.g, c.b, c.a]))
		if mm.use_colors:
			var c2 := mm.get_instance_color(i)
			co.append_array(PackedFloat32Array([c2.r, c2.g, c2.b, c2.a]))
	d["xf"] = _write(xf.to_byte_array())
	if mm.use_custom_data:
		d["cu"] = _write(cu.to_byte_array())
	if mm.use_colors:
		d["co"] = _write(co.to_byte_array())
	d["hash"] = hash(mm.buffer)
	return d


func _geo_state(g: GeometryInstance3D) -> Dictionary:
	var s := {"v": true, "x": g.global_transform}
	s["sh"] = g.cast_shadow
	if g is MeshInstance3D:
		var mi := g as MeshInstance3D
		s["m"] = _mesh_id(mi.mesh)
		var ms: Array = []
		if mi.mesh:
			for i in mi.mesh.get_surface_count():
				ms.append(_mat_id(mi.get_active_material(i)))
		s["mats"] = ms
	elif g is MultiMeshInstance3D:
		var mm := (g as MultiMeshInstance3D).multimesh
		s["mmh"] = hash(mm.buffer) if mm else 0
		s["mmv"] = mm.visible_instance_count if mm else 0
	else:
		unhandled["geo:" + g.get_class()] = true
	s["mo"] = _mat_id(g.material_override)
	s["ov"] = _mat_id(g.material_overlay)
	s["tr"] = snappedf(g.transparency, 0.001)
	var ip := {}
	for pr: Dictionary in g.get_property_list():
		var pn := str(pr["name"])
		if pn.begins_with("instance_shader_parameters/"):
			ip[pn.get_slice("/", 1)] = _ser(g.get(pn))
	if not ip.is_empty():
		s["ip"] = ip
	return s


func _state_diff(old: Dictionary, s: Dictionary, nid: int) -> Dictionary:
	var c := {}
	for k in s:
		var v: Variant = s[k]
		if not old.has(k):
			c[k] = v
		elif k == "x":
			if not (old[k] as Transform3D).is_equal_approx(v):
				c[k] = v
		elif typeof(v) == TYPE_DICTIONARY or typeof(v) == TYPE_ARRAY:
			if JSON.stringify(v) != JSON.stringify(old[k]):
				c[k] = v
		elif old[k] != v:
			c[k] = v
	if c.is_empty():
		return c
	if c.has("x"):
		c["x"] = _xf(c["x"])
	c["n"] = nid
	return c


# ------------------------------------------------------------------ frame

func _on_frame() -> void:
	if done:
		return
	frame_i += 1
	var t := frame_i / 30.0
	var stage: Node = runner.get("stage")
	if stage == null or not is_instance_valid(stage) or stage.get("world") == null:
		return
	var cam: Camera3D = stage.call("camera")
	if cam == null:
		return
	var world := cam.get_world_3d()
	var fr := {"t": snappedf(t, 0.001), "clock": snappedf(float(runner.get("clock")), 0.001)}
	# camera
	fr["cam"] = {"x": _xf(cam.global_transform), "fov": cam.fov, "near": cam.near, "far": cam.far, "keep": cam.keep_aspect}
	var attr := cam.attributes as CameraAttributesPractical
	if attr:
		fr["dof"] = [attr.dof_blur_far_enabled, attr.dof_blur_far_distance, attr.dof_blur_far_transition,
			attr.dof_blur_near_enabled, attr.dof_blur_near_distance, attr.dof_blur_near_transition, attr.dof_blur_amount]
	# geometry
	var ch: Array = []
	var seen := {}
	for g: GeometryInstance3D in root.find_children("*", "GeometryInstance3D", true, false):
		if not g.is_inside_tree() or g.get_world_3d() != world:
			continue
		if not g.is_visible_in_tree():
			continue
		var nid := _node_id(g)
		seen[nid] = true
		var s := _geo_state(g)
		var c := _state_diff(node_state.get(nid, {}), s, nid)
		node_state[nid] = s
		if not c.is_empty():
			if c.has("mmh") and node_state.has(nid) and g is MultiMeshInstance3D:
				c["mm"] = _mm_dump((g as MultiMeshInstance3D).multimesh)
			ch.append(c)
	for nid in node_state.keys():
		if not seen.has(nid) and bool(node_state[nid].get("v", false)):
			ch.append({"n": nid, "v": false})
			node_state[nid] = {"v": false}
	if not ch.is_empty():
		fr["set"] = ch
	# material uniforms that animate
	var mc: Array = []
	for i in mat_objs.size():
		var m: Material = mat_objs[i]
		if not is_instance_valid(m) or not (m is ShaderMaterial or m is BaseMaterial3D):
			continue
		var p: Dictionary
		if m is ShaderMaterial:
			p = _mat_params(m)
		else:
			continue
		var sig := JSON.stringify(p)
		if sig != mat_sig[i]:
			var old: Variant = JSON.parse_string(mat_sig[i]) if mat_sig[i] != "" else {}
			var d := {}
			for k in p:
				if not (old as Dictionary).has(k) or JSON.stringify(old[k]) != JSON.stringify(p[k]):
					d[k] = p[k]
			mat_sig[i] = sig
			mc.append({"mat": i, "p": d})
	if not mc.is_empty():
		fr["mat"] = mc
	# lights
	var lc: Array = []
	for l: Light3D in root.find_children("*", "Light3D", true, false):
		if l.get_world_3d() != world or not l.is_visible_in_tree():
			continue
		var ld := {"class": l.get_class(), "x": _xf(l.global_transform), "color": _ser(l.light_color), "energy": l.light_energy,
			"indirect": l.light_indirect_energy, "spec": l.light_specular, "shadow": l.shadow_enabled, "bias": l.shadow_bias,
			"nbias": l.shadow_normal_bias, "blur": l.shadow_blur, "opacity": l.shadow_opacity, "angular": l.light_angular_distance if l is DirectionalLight3D else 0.0,
			"name": str(l.name)}
		if l is DirectionalLight3D:
			ld["max_dist"] = (l as DirectionalLight3D).directional_shadow_max_distance
			ld["mode"] = (l as DirectionalLight3D).directional_shadow_mode
		elif l is OmniLight3D:
			ld["range"] = (l as OmniLight3D).omni_range
			ld["atten"] = (l as OmniLight3D).omni_attenuation
		elif l is SpotLight3D:
			ld["range"] = (l as SpotLight3D).spot_range
			ld["angle"] = (l as SpotLight3D).spot_angle
		var lid := _node_id(l)
		var js := JSON.stringify(ld)
		if last_lights.get(lid, "") != js:
			last_lights[lid] = js
			ld["n"] = lid
			lc.append(ld)
	if not lc.is_empty():
		fr["lights"] = lc
	# environment
	for we: WorldEnvironment in root.find_children("*", "WorldEnvironment", true, false):
		if we.get_viewport() != cam.get_viewport() or we.environment == null:
			continue
		var en := we.environment
		var ed := {}
		for n in ["background_mode", "background_color", "ambient_light_source", "ambient_light_color", "ambient_light_energy",
				"tonemap_mode", "tonemap_exposure", "tonemap_white", "glow_enabled", "glow_intensity", "glow_bloom",
				"glow_hdr_threshold", "glow_strength", "adjustment_enabled", "adjustment_saturation", "adjustment_contrast",
				"adjustment_brightness", "fog_enabled", "fog_mode", "fog_light_color", "fog_light_energy", "fog_density",
				"fog_depth_curve", "fog_depth_begin", "fog_depth_end", "fog_sun_scatter", "fog_height", "fog_height_density",
				"ssao_enabled", "sdfgi_enabled", "ssil_enabled", "ssr_enabled", "volumetric_fog_enabled"]:
			ed[n] = _ser(en.get(n))
		var js := JSON.stringify(ed)
		if js != last_env:
			last_env = js
			fr["env"] = ed
		break
	# look rig (script vars) + post material
	var rig: Node = stage.get("world").get("rig") if stage.get("world") else null
	if rig:
		var rd := {}
		for pr: Dictionary in rig.get_property_list():
			if int(pr["usage"]) & PROPERTY_USAGE_SCRIPT_VARIABLE and int(pr["usage"]) & PROPERTY_USAGE_STORAGE:
				var v: Variant = rig.get(pr["name"])
				if typeof(v) != TYPE_OBJECT:
					rd[str(pr["name"])] = _ser(v)
		var post: Variant = rig.get("post")
		if post and is_instance_valid(post) and (post as CanvasItem).material:
			rd["post_params"] = _mat_params((post as CanvasItem).material as ShaderMaterial)
			rd["post_visible"] = (post as CanvasItem).is_visible_in_tree()
		var js := JSON.stringify(rd)
		if js != last_rig:
			last_rig = js
			fr["rig"] = rd
	# audio
	var ac: Array = []
	for p: Node in root.find_children("*", "", true, false):
		if not (p is AudioStreamPlayer or p is AudioStreamPlayer3D):
			continue
		var st: AudioStream = p.get("stream")
		var playing: bool = p.get("playing")
		var pos: float = p.call("get_playback_position") if playing else 0.0
		var k := p.get_instance_id()
		var prev: Dictionary = players.get(k, {})
		var path := st.resource_path if st else ""
		if st and path == "":
			path = _stream_path(st)
		var vol: float = p.get("volume_db")
		var pid := _node_id(p)
		var restarted: bool = playing and (not bool(prev.get("playing", false)) or path != prev.get("path", "") or pos + 0.05 < float(prev.get("pos", 0.0)))
		if restarted:
			ac.append({"p": pid, "ev": "start", "path": path, "vol": snappedf(vol, 0.01), "pitch": p.get("pitch_scale"),
				"bus": str(p.get("bus")), "at": snappedf(pos, 0.001), "loop": _is_loop(st), "class": p.get_class()})
			if p is AudioStreamPlayer3D:
				var p3 := p as AudioStreamPlayer3D
				ac[-1]["pos"] = _ser(p3.global_position)
				ac[-1]["model"] = p3.attenuation_model
				ac[-1]["unit"] = p3.unit_size
				ac[-1]["maxdb"] = p3.max_db
				ac[-1]["maxdist"] = p3.max_distance
				ac[-1]["pan"] = p3.panning_strength
		elif not playing and bool(prev.get("playing", false)):
			ac.append({"p": pid, "ev": "stop"})
		elif playing and absf(vol - float(prev.get("vol", vol))) > 0.3:
			ac.append({"p": pid, "ev": "vol", "vol": snappedf(vol, 0.01)})
		else:
			vol = float(prev.get("vol", vol)) if playing else vol
		players[k] = {"playing": playing, "path": path, "pos": pos, "vol": vol}
	if not ac.is_empty():
		fr["audio"] = ac
	var buses := []
	for b in AudioServer.bus_count:
		buses.append([AudioServer.get_bus_name(b), snappedf(AudioServer.get_bus_volume_db(b), 0.1), AudioServer.is_bus_mute(b)])
	var bj := JSON.stringify(buses)
	if bj != last_buses:
		last_buses = bj
		fr["buses"] = buses
	# caption
	var ui: Node = runner.get("ui")
	if ui:
		var cap: Node = ui.get("_caption")
		var txt := ""
		if cap and is_instance_valid(cap) and (cap as CanvasItem).is_visible_in_tree():
			for lb: Node in cap.find_children("*", "", true, false):
				if (lb is Label or lb is RichTextLabel) and (lb as CanvasItem).is_visible_in_tree():
					txt += ("|" if txt != "" else "") + (lb.get("text") as String)
		if txt != last_caption:
			last_caption = txt
			fr["caption"] = txt
	# beat + taps
	var bid := str(runner.get("_beat_id"))
	if bid != last_beat:
		last_beat = bid
		fr["beat"] = bid
		beat_log.append([fr["t"], bid])
	var ex: Array = runner.get("_expect")
	var exs := ",".join(PackedStringArray(ex.map(func(x): return str(x))))
	if exs != last_expect:
		last_expect = exs
		fr["expect"] = exs
		tap_log.append([fr["t"], exs])
	if exs != "":
		var tg := {}
		for tn in ex:
			var tp: Variant = stage.call("_target_point", str(tn))
			if tp != null:
				tg[str(tn)] = {"p": _ser(tp), "r": stage.call("target_radius", str(tn)), "s": _ser(stage.call("target_screen", str(tn)))}
		fr["targets"] = tg
	frames.append(fr)
	# native reference frames (whole window: 3D + post grade + captions) every 2 s of record time
	if frame_i % 60 == 0:
		var img := root.get_viewport().get_texture().get_image()
		var shots := ProjectSettings.globalize_path("res://../artifacts/threejs_pilot/godot_frames")
		DirAccess.make_dir_recursive_absolute(shots)
		img.save_jpg(shots + "/t%05.1f.jpg" % t, 0.9)
	if (until_beat != "" and bid == until_beat) or t > max_sec:
		if not fr.has("end_mark"):
			tail_sec -= 1.0 / 30.0
			if tail_sec <= 0.0:
				_finish()


## SoundDirector duplicates looping ogg streams (loop = true), which drops resource_path: find the source in its cache.
func _stream_path(st: AudioStream) -> String:
	for sd: Node in root.find_children("*", "", true, false):
		var cache: Variant = sd.get("_streams")
		if cache is Dictionary:
			for k in (cache as Dictionary):
				if (cache as Dictionary)[k] == st:
					return str(k).trim_suffix("#loop")
	return "<" + st.get_class() + ">"


func _is_loop(st: AudioStream) -> bool:
	if st is AudioStreamOggVorbis:
		return (st as AudioStreamOggVorbis).loop
	if st is AudioStreamMP3:
		return (st as AudioStreamMP3).loop
	if st is AudioStreamWAV:
		return (st as AudioStreamWAV).loop_mode != AudioStreamWAV.LOOP_DISABLED
	return false


func _finish() -> void:
	done = true
	bin.close()
	var vp := root.get_viewport()
	var out := {"meta": {"tale": "turnip", "beat": "seed", "fps": 30, "frames": frames.size(), "viewport": _ser(vp.get_visible_rect().size),
			"godot": Engine.get_version_info()["string"], "made": Time.get_datetime_string_from_system(), "geo_bytes": bin_off,
			"beats": beat_log, "taps": tap_log, "unhandled": unhandled.keys(), "shaders": shader_files},
		"textures": tex_list, "materials": mat_list, "meshes": mesh_list, "nodes": node_list, "frames": frames}
	var f := FileAccess.open(out_dir + "/scene.json", FileAccess.WRITE)
	f.store_string(JSON.stringify(out))
	f.close()
	print("PILOT_EXPORT frames=", frames.size(), " meshes=", mesh_list.size(), " mats=", mat_list.size(), " tex=", tex_list.size(),
		" nodes=", node_list.size(), " geo_mb=", snappedf(bin_off / 1048576.0, 0.1), " unhandled=", unhandled.keys(), " shaders=", shader_files)
	quit()
