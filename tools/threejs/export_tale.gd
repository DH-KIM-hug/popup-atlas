extends SceneTree
## three.js player (docs/THREEJS.md): READ-ONLY recorder of a whole tale.
## Runs the real StoryRunner (autoplay, the gate's settings) from the cover to the end card and writes everything
## the screen shows, so the web player uses the same meshes, prints, positions, camera, light, sound and timing as
## Godot instead of re-imagining them:
##   scene.json  textures, materials (shader + uniforms), meshes (surfaces -> ranges in geo.bin), nodes, and one entry
##               per 30 fps frame with what changed:
##               - views: "main" (the page on screen), "next" (the prebuilt page shown right of the fold during a live
##                 page turn), "book" (the cover / ending book, its own World3D); per view the camera, DOF, lights,
##                 Environment and look rig (post_grade) — diffs per key;
##               - geometry nodes (which view, transform, mesh / material swaps, MultiMesh buffers, instance uniforms),
##                 animated material uniforms;
##               - audio starts / stops / volumes per player, bus volumes;
##               - UI: caption, page tab, end card, page turn (progress, old page snapshot or live, new page view),
##                 snapshots (flashback cards), flash cards, the pointer ring, hold progress;
##               - story: beat, line, tap targets (world point + radius), ripples (= autoplay taps), runner mode.
##   geo.bin     vertex / index / instance arrays, identical blobs stored once (content hash).
##   tex/        runtime-built images (card atlas pages, ground maps) as webp named by content hash.
## Run (windowed: runtime textures need a renderer). Godot flags before `--`, always a frame cap:
##   tools/story/with_godot.sh /Applications/Godot.app/Contents/MacOS/Godot --path game --resolution 1366x1024 \
##     --fixed-fps 30 --quit-after 15000 --script res://../tools/threejs/export_tale.gd -- \
##     --tale=turnip --autoplay --log-sound --x-out=/ABS/dump [--x-ref=/ABS/frames --x-ref-every=90]
## Nothing in game/ is changed: the runner instance gets `_movie = true` (what a movie-maker recording sets: the next
## page is prebuilt in one go, so story timing matches the gate recordings).

var out_dir := ""
var ref_dir := ""
var ref_every := 90
var tale := "turnip"
var tail_sec := 1.2
var done_at := -1.0
var max_sec := 900.0

var runner: Node
var frame_i := 0
var done := false
var bin: FileAccess
var bin_off := 0
var blob_at := {}  # sha1 -> [off, size]
var tex_hash := {}  # sha1 -> file

var meshes := {}
var mesh_list: Array = []
var mats := {}
var mat_list: Array = []
var mat_objs: Array = []
var mat_sig: Array = []
var texs := {}
var tex_list: Array = []
var nodes := {}
var node_list: Array = []
var node_state := {}
var players := {}
var frames: Array = []
var unhandled := {}
var shader_files := {}
var uniform_names := {}  # shader instance id -> [names]
var inst_params := {}  # node instance id -> [names]

# tracked node sets (node_added / node_removed)
var geos := {}
var auds := {}
var lights_set := {}

var last := {}  # misc "last value" store: key -> json
var beat_log: Array = []
var line_log: Array = []
var tap_log: Array = []
var prev_ripples: Array = []
var snaps_seen := {}


func _init() -> void:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--x-out="):
			out_dir = a.get_slice("=", 1)
		elif a.begins_with("--x-ref="):
			ref_dir = a.get_slice("=", 1)
		elif a.begins_with("--x-ref-every="):
			ref_every = int(a.get_slice("=", 1))
		elif a.begins_with("--x-max="):
			max_sec = float(a.get_slice("=", 1))
		elif a.begins_with("--tale="):
			tale = a.get_slice("=", 1)
	if out_dir == "":
		push_error("--x-out=<dir> needed")
		quit(2)
		return
	DirAccess.make_dir_recursive_absolute(out_dir + "/tex")
	if ref_dir != "":
		DirAccess.make_dir_recursive_absolute(ref_dir)
	bin = FileAccess.open(out_dir + "/geo.bin", FileAccess.WRITE)
	node_added.connect(_on_added)
	node_removed.connect(_on_removed)
	_start.call_deferred()


func _on_added(n: Node) -> void:
	if n is GeometryInstance3D:
		geos[n.get_instance_id()] = n
	elif n is AudioStreamPlayer or n is AudioStreamPlayer3D:
		auds[n.get_instance_id()] = n
	elif n is Light3D:
		lights_set[n.get_instance_id()] = n


func _on_removed(n: Node) -> void:
	var k := n.get_instance_id()
	geos.erase(k)
	auds.erase(k)
	lights_set.erase(k)


func _start() -> void:
	var sc := (load("res://stories/%s/story.tscn" % tale) as PackedScene).instantiate()
	sc.set("_movie", true)
	runner = sc
	root.add_child(sc)
	current_scene = sc
	if sc.has_signal("story_finished"):
		sc.connect("story_finished", func(_t): done_at = frame_i / 30.0)
	process_frame.connect(_on_frame)


# ------------------------------------------------------------------ helpers

func _xf(t: Transform3D) -> Array:
	var b := t.basis
	return [snappedf(b.x.x, 1e-5), snappedf(b.x.y, 1e-5), snappedf(b.x.z, 1e-5), 0,
		snappedf(b.y.x, 1e-5), snappedf(b.y.y, 1e-5), snappedf(b.y.z, 1e-5), 0,
		snappedf(b.z.x, 1e-5), snappedf(b.z.y, 1e-5), snappedf(b.z.z, 1e-5), 0,
		snappedf(t.origin.x, 1e-5), snappedf(t.origin.y, 1e-5), snappedf(t.origin.z, 1e-5), 1]


func _ser(v: Variant) -> Variant:
	match typeof(v):
		TYPE_NIL, TYPE_BOOL, TYPE_INT, TYPE_STRING:
			return v
		TYPE_FLOAT:
			return snappedf(v, 1e-5)
		TYPE_VECTOR2, TYPE_VECTOR2I:
			return [snappedf(v.x, 1e-5), snappedf(v.y, 1e-5)]
		TYPE_VECTOR3, TYPE_VECTOR3I:
			return [snappedf(v.x, 1e-5), snappedf(v.y, 1e-5), snappedf(v.z, 1e-5)]
		TYPE_VECTOR4, TYPE_VECTOR4I, TYPE_QUATERNION:
			return [snappedf(v.x, 1e-5), snappedf(v.y, 1e-5), snappedf(v.z, 1e-5), snappedf(v.w, 1e-5)]
		TYPE_COLOR:
			return [snappedf(v.r, 1e-4), snappedf(v.g, 1e-4), snappedf(v.b, 1e-4), snappedf(v.a, 1e-4)]
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


func _sha(arr: PackedByteArray) -> String:
	var h := HashingContext.new()
	h.start(HashingContext.HASH_SHA1)
	h.update(arr)
	return h.finish().hex_encode()


## Store a blob once: identical vertex / index / instance arrays (a spread rebuilt, the same card on two pages) share
## one range.
func _write(arr: PackedByteArray) -> Array:
	var k := _sha(arr)
	if blob_at.has(k):
		return blob_at[k]
	var off := bin_off
	bin.store_buffer(arr)
	bin_off += arr.size()
	var pad := (4 - (bin_off % 4)) % 4
	for i in pad:
		bin.store_8(0)
	bin_off += pad
	blob_at[k] = [off, arr.size()]
	return blob_at[k]


func _changed(key: String, v: Variant) -> bool:
	var js := JSON.stringify(v)
	if last.get(key, null) == js:
		return false
	last[key] = js
	return true


## per-key diff of a dictionary against the last one stored under `key`
func _diff(key: String, d: Dictionary) -> Dictionary:
	var old: Dictionary = last.get(key, {})
	var out := {}
	for k in d:
		var js := JSON.stringify(d[k])
		if old.get(k, null) != js:
			out[k] = d[k]
			old[k] = js
	last[key] = old
	return out


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
	if t is ViewportTexture:
		e["viewport"] = true
		return id
	if t is Texture2DArray or t is Texture3D:
		var ta := t as Texture2DArray
		var files: Array = []
		for i in ta.get_layers():
			files.append(_save_img(ta.get_layer_data(i), e))
		e["layers"] = files
		e["size"] = [ta.get_width(), ta.get_height()]
		return id
	if t is Texture2D:
		var img := (t as Texture2D).get_image()
		if img == null:
			e["missing"] = true
			return id
		e["file"] = _save_img(img, e)
		e["size"] = [img.get_width(), img.get_height()]
	else:
		e["unsupported"] = true
	return id


func _save_img(img: Image, e: Dictionary) -> Variant:
	if img.is_compressed():
		img.decompress()
	var f := img.get_format()
	e["format"] = f
	e["mipmaps"] = img.has_mipmaps()
	if f in [Image.FORMAT_RF, Image.FORMAT_RGF, Image.FORMAT_RGBF, Image.FORMAT_RGBAF, Image.FORMAT_RH, Image.FORMAT_RGH,
			Image.FORMAT_RGBH, Image.FORMAT_RGBAH]:
		var im := img.duplicate() as Image
		im.convert(Image.FORMAT_RGBAF)
		return {"float": _write(im.get_data()), "w": im.get_width(), "h": im.get_height()}
	var im2 := img.duplicate() as Image
	if im2.has_mipmaps():
		im2.clear_mipmaps()
	if f == Image.FORMAT_L8 or f == Image.FORMAT_R8:
		im2.convert(Image.FORMAT_RGB8)
	elif f != Image.FORMAT_RGBA8 and f != Image.FORMAT_RGB8:
		im2.convert(Image.FORMAT_RGBA8)
	var k := _sha(im2.get_data())
	if tex_hash.has(k):
		return tex_hash[k]
	var p := "tex/%s.webp" % k.substr(0, 16)
	im2.save_webp(out_dir + "/" + p, false)
	tex_hash[k] = p
	return p


# ------------------------------------------------------------------ materials

func _uniforms(sh: Shader) -> Array:
	var k := sh.get_instance_id()
	if uniform_names.has(k):
		return uniform_names[k]
	var names: Array = []
	for u: Dictionary in sh.get_shader_uniform_list(true):
		var us := int(u.get("usage", 0))
		if us & PROPERTY_USAGE_GROUP or us & PROPERTY_USAGE_SUBGROUP:
			continue
		names.append(str(u["name"]))
	uniform_names[k] = names
	return names


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
				sp = "inline_%s.gdshader" % _sha(sh.code.to_utf8_buffer()).substr(0, 10)
				if not FileAccess.file_exists(out_dir + "/" + sp):
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
				"disable_receive_shadows", "shadow_to_opacity", "albedo_texture_force_srgb", "normal_enabled", "normal_texture",
				"disable_fog", "proximity_fade_enabled", "use_point_size", "point_size"]:
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
	for n: String in _uniforms(m.shader):
		var v: Variant = m.get_shader_parameter(n)
		if v == null:
			continue
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
		se["prim"] = (mesh as ArrayMesh).surface_get_primitive_type(s) if mesh is ArrayMesh else Mesh.PRIMITIVE_TRIANGLES
		var attrs := {}
		var v: PackedVector3Array = arr[Mesh.ARRAY_VERTEX]
		se["count"] = v.size()
		attrs["position"] = _write(v.to_byte_array())
		if arr[Mesh.ARRAY_NORMAL] != null and (arr[Mesh.ARRAY_NORMAL] as PackedVector3Array).size() > 0:
			attrs["normal"] = _write((arr[Mesh.ARRAY_NORMAL] as PackedVector3Array).to_byte_array())
		# tangents: the paper ports perturb normals in Godot's tangent frame (binormal = cross(N, T) * T.w)
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
			if c != null and typeof(c) == TYPE_PACKED_FLOAT32_ARRAY and (c as PackedFloat32Array).size() > 0:
				attrs["custom%d" % ci] = _write((c as PackedFloat32Array).to_byte_array())
			elif c != null and typeof(c) == TYPE_PACKED_BYTE_ARRAY and (c as PackedByteArray).size() > 0:
				unhandled["custom_bytes"] = true
		if arr[Mesh.ARRAY_BONES] != null and typeof(arr[Mesh.ARRAY_BONES]) != TYPE_NIL and (arr[Mesh.ARRAY_BONES] as Array).size() > 0:
			unhandled["skinned"] = true
		se["attrs"] = attrs
		var idx: PackedInt32Array
		if arr[Mesh.ARRAY_INDEX] != null and (arr[Mesh.ARRAY_INDEX] as PackedInt32Array).size() > 0:
			idx = arr[Mesh.ARRAY_INDEX]
		if se["prim"] == Mesh.PRIMITIVE_TRIANGLES:
			if idx.is_empty():
				idx.resize(v.size())
				for i in v.size():
					idx[i] = i
			for i in range(0, idx.size() - 2, 3):  # Godot front faces are clockwise; three.js counter-clockwise
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
	var e := {"id": id, "class": n.get_class(), "name": str(n.name)}
	if n.get_script():
		e["script"] = (n.get_script() as Script).resource_path.get_file()
	var p := n.get_parent()
	while p and not e.has("owner_script"):
		if p.get_script():
			e["owner_script"] = (p.get_script() as Script).resource_path.get_file()
			e["owner_name"] = str(p.name)
		p = p.get_parent()
	if n is MultiMeshInstance3D:
		e["mm"] = _mm_dump((n as MultiMeshInstance3D).multimesh)
	node_list.append(e)
	return id


func _mm_dump(mm: MultiMesh) -> Dictionary:
	if mm == null:
		return {}
	var d := {"mesh": _mesh_id(mm.mesh), "count": mm.instance_count, "visible": mm.visible_instance_count,
		"colors": mm.use_colors, "custom": mm.use_custom_data}
	var n := mm.instance_count if mm.visible_instance_count < 0 else mini(mm.visible_instance_count, mm.instance_count)
	d["n"] = n
	var xf := PackedFloat32Array()
	xf.resize(n * 16)
	var cu := PackedFloat32Array()
	var co := PackedFloat32Array()
	if mm.use_custom_data:
		cu.resize(n * 4)
	if mm.use_colors:
		co.resize(n * 4)
	for i in n:
		var t := mm.get_instance_transform(i)
		var b := t.basis
		var o := i * 16
		xf[o] = b.x.x; xf[o + 1] = b.x.y; xf[o + 2] = b.x.z; xf[o + 3] = 0
		xf[o + 4] = b.y.x; xf[o + 5] = b.y.y; xf[o + 6] = b.y.z; xf[o + 7] = 0
		xf[o + 8] = b.z.x; xf[o + 9] = b.z.y; xf[o + 10] = b.z.z; xf[o + 11] = 0
		xf[o + 12] = t.origin.x; xf[o + 13] = t.origin.y; xf[o + 14] = t.origin.z; xf[o + 15] = 1
		if mm.use_custom_data:
			var c := mm.get_instance_custom_data(i)
			cu[i * 4] = c.r; cu[i * 4 + 1] = c.g; cu[i * 4 + 2] = c.b; cu[i * 4 + 3] = c.a
		if mm.use_colors:
			var c2 := mm.get_instance_color(i)
			co[i * 4] = c2.r; co[i * 4 + 1] = c2.g; co[i * 4 + 2] = c2.b; co[i * 4 + 3] = c2.a
	d["xf"] = _write(xf.to_byte_array())
	if mm.use_custom_data:
		d["cu"] = _write(cu.to_byte_array())
	if mm.use_colors:
		d["co"] = _write(co.to_byte_array())
	d["hash"] = hash(mm.buffer)
	return d


func _geo_state(g: GeometryInstance3D, w: int) -> Dictionary:
	var s := {"v": true, "w": w, "x": g.global_transform, "sh": g.cast_shadow}
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
	elif g is Sprite3D:
		var sp := g as Sprite3D
		s["spr"] = {"tex": _tex_id(sp.texture) if sp.texture else -1, "px": sp.pixel_size, "bb": sp.billboard, "shaded": sp.shaded,
			"col": _ser(sp.modulate), "ds": sp.double_sided, "cen": sp.centered, "off": _ser(sp.offset), "fh": sp.flip_h,
			"fv": sp.flip_v, "alpha": sp.alpha_cut, "size": _ser(sp.texture.get_size()) if sp.texture else [1, 1]}
	elif g is Label3D:
		var lb := g as Label3D
		s["lbl"] = {"text": lb.text, "fs": lb.font_size, "px": lb.pixel_size, "col": _ser(lb.modulate), "shaded": lb.shaded,
			"ds": lb.double_sided, "bb": lb.billboard, "oc": _ser(lb.outline_modulate), "os": lb.outline_size,
			"ha": lb.horizontal_alignment, "va": lb.vertical_alignment, "w": lb.width, "ls": lb.line_spacing}
	else:
		unhandled["geo:" + g.get_class()] = true
	s["mo"] = _mat_id(g.material_override)
	s["ov"] = _mat_id(g.material_overlay)
	s["tr"] = snappedf(g.transparency, 0.001)
	var k := g.get_instance_id()
	if not inst_params.has(k):
		var names: Array = []
		for pr: Dictionary in g.get_property_list():
			var pn := str(pr["name"])
			if pn.begins_with("instance_shader_parameters/"):
				names.append(pn)
		inst_params[k] = names
	if not (inst_params[k] as Array).is_empty():
		var ip := {}
		for pn: String in inst_params[k]:
			ip[pn.get_slice("/", 1)] = _ser(g.get(pn))
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


# ------------------------------------------------------------------ views

## The 3D views the screen shows this frame: [name, camera, rig]. "main" = the page, "next" = the prebuilt page a
## live turn reveals, "book" = the cover / ending book.
func _views() -> Array:
	var out: Array = []
	var ui: Node = runner.get("ui")
	var pt: Control = ui.get("page_turn") if ui else null
	var new_tex: Variant = pt.get("_new") if pt and pt.visible else null
	var stage: Node = runner.get("stage")
	if stage and is_instance_valid(stage) and stage.get("world") != null and stage.get("world").get("rig") != null:
		var cam: Camera3D = stage.call("camera")
		if cam and cam.is_inside_tree():
			out.append(["main", cam, stage.get("world").get("rig")])
	var pre: Dictionary = runner.get("_prebuilt")
	for key in pre:
		var e: Dictionary = pre[key]
		var vp: SubViewport = e.get("vp")
		var ps: Node = e.get("stage")
		if vp and is_instance_valid(vp) and new_tex != null and new_tex == vp.get_texture() and ps and ps.get("world") \
				and ps.get("world").get("rig"):
			out.append(["next", ps.call("camera"), ps.get("world").get("rig")])
	var book: Node = ui.get("_book") if ui else null
	var cover: Control = ui.get("_cover") if ui else null
	if book and is_instance_valid(book) and book.get("vp") and (cover.visible or (new_tex != null and new_tex == (book.get("vp") as SubViewport).get_texture())):
		var bvp: SubViewport = book.get("vp")
		out.append(["book", bvp.get_camera_3d(), book.get("rig")])
	return out


func _view_index(name: String) -> int:
	return {"main": 0, "next": 1, "book": 2}[name]


# ------------------------------------------------------------------ frame

func _on_frame() -> void:
	if done:
		return
	frame_i += 1
	var t := frame_i / 30.0
	var fr := {"t": snappedf(t, 0.001), "clock": snappedf(float(runner.get("clock")), 0.001)}
	var ui: Node = runner.get("ui")
	var views := _views()
	var worlds := {}
	var vnames: Array = []
	for v: Array in views:
		var cam: Camera3D = v[1]
		if cam == null:
			continue
		var vn: String = v[0]
		vnames.append(vn)
		worlds[cam.get_world_3d()] = _view_index(vn)
		var cd := {"x": _xf(cam.global_transform), "fov": snappedf(cam.fov, 1e-4), "near": cam.near, "far": cam.far, "keep": cam.keep_aspect}
		var attr := cam.attributes as CameraAttributesPractical
		if attr:
			cd["dof"] = [attr.dof_blur_far_enabled, snappedf(attr.dof_blur_far_distance, 1e-4), snappedf(attr.dof_blur_far_transition, 1e-4),
				attr.dof_blur_near_enabled, snappedf(attr.dof_blur_near_distance, 1e-4), snappedf(attr.dof_blur_near_transition, 1e-4),
				snappedf(attr.dof_blur_amount, 1e-4)]
		var cdd := _diff("cam:" + vn, cd)
		if not cdd.is_empty():
			if not fr.has("cam"):
				fr["cam"] = {}
			fr["cam"][vn] = cdd
		_env_rig(fr, vn, v[2], cam)
	if _changed("views", vnames):
		fr["views"] = vnames
	# which view is the screen's base (the cover / end book covers the page view when shown)
	var cover: Control = ui.get("_cover") if ui else null
	var base := "book" if cover and cover.visible and vnames.has("book") else ("main" if vnames.has("main") else "")
	if _changed("base", base):
		fr["base"] = base
	# geometry
	var ch: Array = []
	var seen := {}
	for k in geos:
		var g: GeometryInstance3D = geos[k]
		if not is_instance_valid(g) or not g.is_inside_tree():
			continue
		var w: Variant = worlds.get(g.get_world_3d(), null)
		if w == null or not g.is_visible_in_tree():
			continue
		var nid := _node_id(g)
		seen[nid] = true
		var s := _geo_state(g, int(w))
		var c := _state_diff(node_state.get(nid, {}), s, nid)
		var had := node_state.has(nid)
		node_state[nid] = s
		if not c.is_empty():
			if c.has("mmh") and had and g is MultiMeshInstance3D:
				c["mm"] = _mm_dump((g as MultiMeshInstance3D).multimesh)
			ch.append(c)
	for nid in node_state.keys():
		if not seen.has(nid) and bool(node_state[nid].get("v", false)):
			ch.append({"n": nid, "v": false})
			node_state[nid] = {"v": false}
	if not ch.is_empty():
		fr["set"] = ch
	# animated material uniforms
	var mc: Array = []
	for i in mat_objs.size():
		var m: Material = mat_objs[i]
		if not is_instance_valid(m) or not m is ShaderMaterial:
			continue
		var p := _mat_params(m)
		var sig := JSON.stringify(p)
		if sig != mat_sig[i]:
			var old: Dictionary = JSON.parse_string(mat_sig[i]) if mat_sig[i] != "" else {}
			var d := {}
			for k in p:
				if not old.has(k) or JSON.stringify(old[k]) != JSON.stringify(p[k]):
					d[k] = p[k]
			mat_sig[i] = sig
			mc.append({"mat": i, "p": d})
	if not mc.is_empty():
		fr["mat"] = mc
	# lights
	var lc: Array = []
	for k in lights_set:
		var l: Light3D = lights_set[k]
		if not is_instance_valid(l) or not l.is_inside_tree():
			continue
		var w: Variant = worlds.get(l.get_world_3d(), null)
		if w == null or not l.is_visible_in_tree():
			continue
		var ld := {"class": l.get_class(), "w": w, "x": _xf(l.global_transform), "color": _ser(l.light_color), "energy": snappedf(l.light_energy, 1e-4),
			"indirect": l.light_indirect_energy, "spec": l.light_specular, "shadow": l.shadow_enabled, "bias": l.shadow_bias,
			"nbias": l.shadow_normal_bias, "blur": l.shadow_blur, "opacity": l.shadow_opacity, "name": str(l.name),
			"angular": l.light_angular_distance if l is DirectionalLight3D else 0.0}
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
		var dd := _diff("light:%d" % lid, ld)
		if not dd.is_empty():
			dd["n"] = lid
			dd["w"] = w
			lc.append(dd)
	if not lc.is_empty():
		fr["lights"] = lc
	var lv := []
	for k in lights_set:
		var l: Light3D = lights_set[k]
		if is_instance_valid(l) and l.is_inside_tree() and worlds.has(l.get_world_3d()) and l.is_visible_in_tree():
			lv.append(_node_id(l))
	lv.sort()
	if _changed("lights_on", lv):
		fr["lights_on"] = lv
	_audio(fr)
	_ui(fr, ui)
	_story(fr, ui)
	frames.append(fr)
	if ref_dir != "" and frame_i % ref_every == 0:
		root.get_viewport().get_texture().get_image().save_jpg(ref_dir + "/t%06.2f.jpg" % t, 0.88)
	if (done_at >= 0.0 and t > done_at + tail_sec) or t > max_sec:
		_finish()


func _env_rig(fr: Dictionary, vn: String, rig: Node, cam: Camera3D) -> void:
	var en: Environment = rig.get("environment") if rig else null
	if en == null and cam.environment:
		en = cam.environment
	if en == null:
		var wenv := cam.get_world_3d().environment
		en = wenv
	if en:
		var ed := {}
		for n in ["background_mode", "background_color", "ambient_light_source", "ambient_light_color", "ambient_light_energy",
				"tonemap_mode", "tonemap_exposure", "tonemap_white", "glow_enabled", "glow_intensity", "glow_bloom",
				"glow_hdr_threshold", "glow_strength", "adjustment_enabled", "adjustment_saturation", "adjustment_contrast",
				"adjustment_brightness", "fog_enabled", "fog_mode", "fog_light_color", "fog_light_energy", "fog_density",
				"fog_depth_curve", "fog_depth_begin", "fog_depth_end", "fog_sun_scatter", "fog_height", "fog_height_density",
				"ssao_enabled", "sdfgi_enabled", "ssil_enabled", "ssr_enabled", "volumetric_fog_enabled"]:
			ed[n] = _ser(en.get(n))
		var d := _diff("env:" + vn, ed)
		if not d.is_empty():
			if not fr.has("env"):
				fr["env"] = {}
			fr["env"][vn] = d
	if rig:
		var rd := {}
		for pr: Dictionary in rig.get_property_list():
			if int(pr["usage"]) & PROPERTY_USAGE_SCRIPT_VARIABLE and int(pr["usage"]) & PROPERTY_USAGE_STORAGE:
				var v: Variant = rig.get(pr["name"])
				if typeof(v) != TYPE_OBJECT:
					rd[str(pr["name"])] = _ser(v)
		var post: Variant = rig.get("post")
		if post and is_instance_valid(post) and (post as CanvasItem).material:
			var pp := _mat_params((post as CanvasItem).material as ShaderMaterial)
			for k in pp:
				rd["post." + k] = pp[k]
			rd["post_visible"] = (post as CanvasItem).is_visible_in_tree()
		var d2 := _diff("rig:" + vn, rd)
		if not d2.is_empty():
			if not fr.has("rig"):
				fr["rig"] = {}
			fr["rig"][vn] = d2


func _audio(fr: Dictionary) -> void:
	var ac: Array = []
	for k in auds:
		var p: Node = auds[k]
		if not is_instance_valid(p) or not p.is_inside_tree():
			continue
		var st: AudioStream = p.get("stream")
		var playing: bool = p.get("playing")
		var pos: float = p.call("get_playback_position") if playing else 0.0
		var prev: Dictionary = players.get(k, {})
		var path := st.resource_path if st else ""
		if st and path == "":
			path = _stream_path(st)
		var vol: float = p.get("volume_db")
		var restarted: bool = playing and (not bool(prev.get("playing", false)) or path != prev.get("path", "") or pos + 0.05 < float(prev.get("pos", 0.0)))
		if restarted:
			var pid := _node_id(p)
			var e := {"p": pid, "ev": "start", "path": path, "vol": snappedf(vol, 0.01), "pitch": p.get("pitch_scale"),
				"bus": str(p.get("bus")), "at": snappedf(pos, 0.001), "loop": _is_loop(st), "class": p.get_class()}
			if str(p.name) == "Voice" and p.get_parent() == runner:
				e["voice"] = true
			if p is AudioStreamPlayer3D:
				var p3 := p as AudioStreamPlayer3D
				e["pos"] = _ser(p3.global_position)
				e["model"] = p3.attenuation_model
				e["unit"] = p3.unit_size
				e["maxdb"] = p3.max_db
				e["maxdist"] = p3.max_distance
				e["pan"] = p3.panning_strength
			ac.append(e)
		elif not playing and bool(prev.get("playing", false)):
			ac.append({"p": _node_id(p), "ev": "stop"})
		elif playing and absf(vol - float(prev.get("vol", vol))) > 0.3:
			ac.append({"p": _node_id(p), "ev": "vol", "vol": snappedf(vol, 0.01)})
		else:
			vol = float(prev.get("vol", vol)) if playing else vol
		players[k] = {"playing": playing, "path": path, "pos": pos, "vol": vol}
	for k in players.keys():
		if not auds.has(k) and bool(players[k].get("playing", false)):
			ac.append({"p": nodes.get(k, -1), "ev": "stop"})
			players.erase(k)
	if not ac.is_empty():
		fr["audio"] = ac
	var buses := []
	for b in AudioServer.bus_count:
		buses.append([AudioServer.get_bus_name(b), snappedf(AudioServer.get_bus_volume_db(b), 0.1), AudioServer.is_bus_mute(b)])
	if _changed("buses", buses):
		fr["buses"] = buses


func _ui(fr: Dictionary, ui: Node) -> void:
	if ui == null:
		return
	# caption (chip | text)
	var cap: Node = ui.get("_caption")
	var txt := ""
	if cap and is_instance_valid(cap) and (cap as CanvasItem).is_visible_in_tree():
		for lb: Node in cap.find_children("*", "", true, false):
			if (lb is Label or lb is RichTextLabel) and (lb as CanvasItem).is_visible_in_tree():
				txt += ("|" if txt != "" else "") + (lb.get("text") as String)
	if _changed("caption", txt):
		fr["caption"] = txt
	var tab: Control = ui.get("_tab")
	var tl: Label = ui.get("_tab_label")
	var tab_txt := tl.text if tab and tab.is_visible_in_tree() and tl else ""
	if _changed("tab", tab_txt):
		fr["tab"] = tab_txt
	var endc: Control = ui.get("_end")
	var end_on := endc != null and endc.is_visible_in_tree()
	if _changed("end", end_on):
		fr["end"] = end_on
	# page turn
	var pt: Control = ui.get("page_turn")
	var ptd := {}
	if pt and pt.visible:
		var old_t: Variant = pt.get("_tex")
		var new_t: Variant = pt.get("_new")
		ptd = {"p": snappedf(float(pt.get("progress")), 1e-4), "old": (old_t as Object).get_instance_id() if old_t else 0,
			"new": _tex_view(new_t)}
	if _changed("pt", ptd):
		fr["pt"] = ptd
	# flash cards (sun_wind recap): side -> snapshot id, label, scale
	var fc: Dictionary = ui.get("_flash_cards")
	var fd := {}
	if fc:
		for side in fc:
			var f: Array = fc[side]
			var card: Control = f[0]
			if not is_instance_valid(card) or not card.is_visible_in_tree():
				continue
			var tr: TextureRect = card.find_children("*", "TextureRect", true, false)[0] if not card.find_children("*", "TextureRect", true, false).is_empty() else null
			var lb: Label = card.find_children("*", "Label", true, false)[0] if not card.find_children("*", "Label", true, false).is_empty() else null
			var r := card.get_global_rect()
			fd[str(side)] = {"snap": tr.texture.get_instance_id() if tr and tr.texture else 0, "label": lb.text if lb else "",
				"rect": [snappedf(r.position.x, 0.1), snappedf(r.position.y, 0.1), snappedf(r.size.x, 0.1), snappedf(r.size.y, 0.1)],
				"s": snappedf(card.scale.x, 0.01), "rot": snappedf(card.rotation, 0.001)}
	if _changed("flash", fd):
		fr["flash"] = fd
	var hp := snappedf(float(ui.get("hold_progress")), 0.02)
	if _changed("hold", hp):
		fr["hold"] = hp
	var ps: Callable = ui.get("pointer_source")
	var ptr: Variant = null
	if ps.is_valid():
		var v: Vector3 = ps.call()
		if v.x > -500.0:
			ptr = [snappedf(v.x, 0.5), snappedf(v.y, 0.5), snappedf(v.z, 0.5)]
	if _changed("ptr", ptr != null):
		fr["ptr"] = ptr != null
	# ripples: a new one = a tap (autoplay)
	var rips: Array = ui.get("_ripples")
	var newr: Array = []
	for r in rips:
		var known := false
		for q in prev_ripples:
			if is_same(q, r):
				known = true
				break
		if not known:
			newr.append([snappedf((r[0] as Vector2).x, 0.1), snappedf((r[0] as Vector2).y, 0.1)])
	prev_ripples = rips.duplicate()  # shallow: the same [pos, age] arrays
	if not newr.is_empty():
		fr["rip"] = newr


func _tex_view(t: Variant) -> String:
	if t == null:
		return ""
	var pre: Dictionary = runner.get("_prebuilt")
	for key in pre:
		var vp: SubViewport = pre[key].get("vp")
		if vp and is_instance_valid(vp) and vp.get_texture() == t:
			return "next"
	var ui: Node = runner.get("ui")
	var book: Node = ui.get("_book")
	if book and is_instance_valid(book) and book.get("vp") and (book.get("vp") as SubViewport).get_texture() == t:
		return "book"
	return "?"


func _story(fr: Dictionary, ui: Node) -> void:
	var bid := str(runner.get("_beat_id"))
	if _changed("beat", bid):
		fr["beat"] = bid
		beat_log.append([fr["t"], bid])
	var mode := str(runner.get("_mode"))
	if _changed("mode", mode):
		fr["mode"] = mode
	var press := bool(runner.get("_press"))
	if _changed("press", press):
		fr["press"] = press
	var ln := str(runner.get("_last_line"))
	if _changed("line", ln):
		fr["line"] = ln
		line_log.append([fr["t"], ln])
	# snapshots (flashback cards): record the frame each one is taken
	var snaps: Dictionary = runner.get("_snaps")
	for k in snaps:
		var tx: Texture2D = snaps[k]
		if tx and not snaps_seen.has(tx.get_instance_id()):
			snaps_seen[tx.get_instance_id()] = true
			if not fr.has("snap"):
				fr["snap"] = []
			fr["snap"].append(tx.get_instance_id())
	var ex: Array = runner.get("_expect")
	var exs := ",".join(PackedStringArray(ex.map(func(x): return str(x))))
	if _changed("expect", exs):
		fr["expect"] = exs
		tap_log.append([fr["t"], exs])
	var stage: Node = runner.get("stage")
	if exs != "" and stage and is_instance_valid(stage) and stage.get("world"):
		var tg := {}
		for tn in ex:
			var tp: Variant = stage.call("_target_point", str(tn))
			if tp != null:
				tg[str(tn)] = {"p": _ser(tp), "r": snappedf(float(stage.call("target_radius", str(tn))), 0.1),
					"s": _ser(stage.call("target_screen", str(tn)))}
		if _changed("targets", tg):
			fr["targets"] = tg


## SoundDirector duplicates looping ogg streams (loop = true), which drops resource_path: find the source in its cache.
func _stream_path(st: AudioStream) -> String:
	for sd: Node in runner.find_children("*", "", true, false):
		var cache: Variant = sd.get("_streams")
		if cache is Dictionary:
			for k in (cache as Dictionary):
				if (cache as Dictionary)[k] == st:
					return str(k).trim_suffix("#loop")
	# a generated clip (NameVoice: the name piece + fixed pieces joined): save its samples
	if st is AudioStreamWAV:
		var w := st as AudioStreamWAV
		var p := "gen/%s.wav" % _sha(w.data).substr(0, 16)
		DirAccess.make_dir_recursive_absolute(out_dir + "/gen")
		if not FileAccess.file_exists(out_dir + "/" + p):
			w.save_to_wav(out_dir + "/" + p)
		return "dump://" + p
	unhandled["stream:" + st.get_class()] = true
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
	var out := {"meta": {"tale": tale, "fps": 30, "frames": frames.size(), "viewport": _ser(vp.get_visible_rect().size),
			"godot": Engine.get_version_info()["string"], "made": Time.get_datetime_string_from_system(), "geo_bytes": bin_off,
			"done_at": done_at, "beats": beat_log, "lines": line_log, "taps": tap_log, "unhandled": unhandled.keys(),
			"shaders": shader_files},
		"textures": tex_list, "materials": mat_list, "meshes": mesh_list, "nodes": node_list, "frames": frames}
	var f := FileAccess.open(out_dir + "/scene.json", FileAccess.WRITE)
	f.store_string(JSON.stringify(out))
	f.close()
	print("TALE_EXPORT tale=", tale, " frames=", frames.size(), " meshes=", mesh_list.size(), " mats=", mat_list.size(),
		" tex=", tex_list.size(), " nodes=", node_list.size(), " geo_mb=", snappedf(bin_off / 1048576.0, 0.1),
		" unhandled=", unhandled.keys(), " shaders=", shader_files)
	quit()
