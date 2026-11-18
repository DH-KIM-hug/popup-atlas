class_name StaticCards
extends Node3D
## Batches cards that never move into one MultiMesh per card print (integrator, round 1).
## Each print's PaperCard mesh (print face, back, cream cut walls) is built once at the catalog height and
## instanced with a uniform scale, so 1000+ standing cards cost ~3 draws per distinct print instead of 3 per card.
## Cross-slotted pairs add two instances (A in the hinge plane, B slotted at 90°).
##   var sc := StaticCards.new(); sc.add(path, h0, h, pos, yaw, lean, cross); ...; add_child(sc); sc.commit()

var _groups := {}  ## path -> {h0, xforms: Array[Transform3D]}
var count := 0


func add(path: String, h0: float, h: float, pos: Vector3, yaw: float, lean := 0.0, cross := false, tilt := 0.0) -> void:
	if not _groups.has(path):
		_groups[path] = {"h0": h0, "xforms": []}
	var g: Dictionary = _groups[path]
	var s := h / float(g["h0"])
	var b := Basis(Vector3.UP, yaw) * Basis(Vector3.BACK, lean) * Basis(Vector3.RIGHT, tilt) * Basis.from_scale(Vector3.ONE * s)
	g["xforms"].append(Transform3D(b, pos))
	count += 1
	if cross:
		var thick := clampf(float(g["h0"]) * 0.05, 0.014, 0.05)
		var bb := b * Basis(Vector3.UP, PI * 0.5) * Basis.from_scale(Vector3(1, 0.96, 1))
		g["xforms"].append(Transform3D(bb, pos + b * Vector3(0, 0, thick * 1.1)))
		count += 1


func commit() -> void:
	for path: String in _groups:
		var g: Dictionary = _groups[path]
		var tex: Texture2D = load(path)
		if tex == null:
			continue
		var h0: float = g["h0"]
		var thick := clampf(h0 * 0.05, 0.014, 0.05)
		var key := "%s|%.4f|%.4f|%.2f|%s" % [tex.resource_path, h0, thick, 1.6, true]
		var entry: Dictionary = PaperCard._mesh_cache.get(key, {})
		if entry.is_empty():
			entry = PaperCard._build(tex, h0, thick, 1.6)
			PaperCard._mesh_cache[key] = entry
		if entry.is_empty() or entry.get("mesh") == null:
			continue
		var mats: Array = PaperCard._materials(tex, true, Color(0.96, 0.92, 0.82), entry["size"], entry.get("avg", Color.WHITE))
		var mesh: ArrayMesh = (entry["mesh"] as ArrayMesh).duplicate()
		for i in mini(3, mesh.get_surface_count()):
			mesh.surface_set_material(i, mats[i])
		var mm := MultiMesh.new()
		mm.transform_format = MultiMesh.TRANSFORM_3D
		mm.mesh = mesh
		var xs: Array = g["xforms"]
		mm.instance_count = xs.size()
		for i in xs.size():
			mm.set_instance_transform(i, xs[i])
		var mmi := MultiMeshInstance3D.new()
		mmi.name = path.get_file().get_basename()
		mmi.multimesh = mm
		mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
		add_child(mmi)
