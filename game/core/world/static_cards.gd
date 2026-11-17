class_name StaticCards
extends Node3D
## Batches cards that never move into one MultiMesh per card print (integrator, round 1).
## Each print's PaperCard mesh (print face, back, cream cut walls) is built once at the catalog height and
## instanced with a uniform scale, so 1000+ standing cards cost ~2 draws per distinct print instead of 2 per card.
## PE r1: printed front + back share one surface (2 draws per print, was 3). Groups are keyed by print and cut:
##  - cross-slotted pairs: A (notched from the top) + B (notched from the bottom) interlocked at 90°, both
##    printed on both faces, cut edges coloured from the print (no pale seam);
##  - V-folds: the left and right halves of the print, each turned back by `vfold` rad about the centre
##    crease (a mountain fold pointing at the viewer: one lit face, one shadow face).
##   var sc := StaticCards.new(); sc.add(path, h0, h, pos, yaw, lean, cross, tilt, vfold); ...; add_child(sc); sc.commit()

var _groups := {}  ## "path|mode" -> {path, h0, slot, half, xforms: Array[Transform3D]}
var count := 0


func _group(path: String, h0: float, slot := 0, half := 0) -> Dictionary:
	var key := "%s|%d|%d" % [path, slot, half]
	if not _groups.has(key):
		_groups[key] = {"path": path, "h0": h0, "slot": slot, "half": half, "xforms": []}
	return _groups[key]


func add(path: String, h0: float, h: float, pos: Vector3, yaw: float, lean := 0.0, cross := false, tilt := 0.0, vfold := 0.0) -> void:
	var s := h / h0
	var b := Basis(Vector3.UP, yaw) * Basis(Vector3.BACK, lean) * Basis(Vector3.RIGHT, tilt) * Basis.from_scale(Vector3.ONE * s)
	if vfold > 0.0:
		# faces shifted toward the crease so their printed fronts meet on one fold line
		var sh := clampf(h0 * 0.04, 0.011, 0.04) * 0.5 * sin(vfold)
		_group(path, h0, 0, -1)["xforms"].append(Transform3D(b * Basis(Vector3.UP, -vfold), pos + b * Vector3(sh, 0, 0)))
		_group(path, h0, 0, 1)["xforms"].append(Transform3D(b * Basis(Vector3.UP, vfold), pos + b * Vector3(-sh, 0, 0)))
		count += 2
		return
	if cross:
		_group(path, h0, 1, 0)["xforms"].append(Transform3D(b, pos))
		var bb := b * Basis(Vector3.UP, PI * 0.5) * Basis.from_scale(Vector3(1, 0.96, 1))
		_group(path, h0, -1, 0)["xforms"].append(Transform3D(bb, pos))
		count += 2
		return
	_group(path, h0)["xforms"].append(Transform3D(b, pos))
	count += 1


func commit() -> void:
	for key: String in _groups:
		var g: Dictionary = _groups[key]
		var path: String = g["path"]
		var tex: Texture2D = load(path)
		if tex == null:
			continue
		var h0: float = g["h0"]
		var slot: int = g["slot"]
		var half: int = g["half"]
		var thick := clampf(h0 * 0.04, 0.011, 0.04)
		var mkey := "%s|%.4f|%.4f|%.2f|%s|%d|%d" % [tex.resource_path, h0, thick, 1.6, true, slot, half]
		var entry: Dictionary = PaperCard._mesh_cache.get(mkey, {})
		if entry.is_empty():
			entry = PaperCard._build(tex, h0, thick, 1.6, slot, half, true)
			PaperCard._mesh_cache[mkey] = entry
		if entry.is_empty() or entry.get("mesh") == null:
			continue
		var mats: Array = PaperCard._materials(tex, true, Color(0.96, 0.92, 0.82), entry["size"], entry.get("avg", Color.WHITE), slot != 0 or half != 0)
		var mesh: ArrayMesh = (entry["mesh"] as ArrayMesh).duplicate()
		if mesh.get_surface_count() >= 2:
			mesh.surface_set_material(0, mats[0])
			mesh.surface_set_material(1, mats[2])
		var mm := MultiMesh.new()
		mm.transform_format = MultiMesh.TRANSFORM_3D
		mm.mesh = mesh
		var xs: Array = g["xforms"]
		mm.instance_count = xs.size()
		for i in xs.size():
			mm.set_instance_transform(i, xs[i])
		var mmi := MultiMeshInstance3D.new()
		mmi.name = path.get_file().get_basename() + ("_s%d" % slot if slot != 0 else "") + ("_h%d" % half if half != 0 else "")
		mmi.multimesh = mm
		mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
		add_child(mmi)
