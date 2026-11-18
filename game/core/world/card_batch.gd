class_name CardBatch
extends Node3D
## Draws every meadow card through a few batches (component F, perf, 2026-11-18). Replaces one MeshInstance3D
## per hinged card (3 surfaces, 3 materials, shadow-casting) and one 3-surface MultiMesh per static print.
##  - One MultiMesh per print holds that print's static AND hinged cards: single-surface mesh (CardAtlas index in
##    UV2), one shared material (card_batch.gdshader) for all prints -> 1 draw per print, cast_shadow off.
##  - One MultiMesh of quads (card_shadow.gdshader, SHADOWS_ONLY) casts every card's shadow -> 1 draw per split.
##  - Hinged cards keep their PopHinge nodes (pop/fold springs, audio signals, visibility): a hinge that moves marks
##    itself dirty (PopHinge.batch) and its instance is rewritten once per frame; a base that is hidden collapses.
##  - Wind sway runs in the vertex shaders (WindSway pushes t / strength / axis via set_wind) instead of writing
##    node transforms; INSTANCE_CUSTOM = (k, amp, freq, phase) (shadow: (print index, amp, freq, phase)).
## Usage (MeadowWorld): add_static(...) / add_hinged(...) while dressing, set_sway(...), then commit() in the tree.

const CARD_SHADER := preload("res://core/world/shaders/card_batch.gdshader")
const SHADOW_SHADER := preload("res://core/world/shaders/card_shadow.gdshader")
const FIBRE := preload("res://art/tex/paper_fibre.jpg")
const HIDDEN := Basis(Vector3(0.0001, 0, 0), Vector3(0, 0.0001, 0), Vector3(0, 0, 0.0001))

var atlas: CardAtlas
var _DBG_MESH_SHADOWS := OS.get_environment("CARD_SHADOW_MODE") == "mesh"  # perf A/B only
var material: ShaderMaterial
var shadow_material: ShaderMaterial
var static_count := 0
var hinged_count := 0
var committed := false

## Instance records: {idx, xf (rest, meadow space), custom (Color), hinge, base, scale (Basis), slot, sslot}
var _recs: Array[Dictionary] = []
var _statics: Array[int] = []  ## record ids of static cards (spread clearing)
var _by_print := {}  ## print index -> Array[int] record ids
var _mms := {}  ## print index -> MultiMesh
var _shadow_mm: MultiMesh
var _dirty := {}  ## record id -> true
var _hinge_rec := {}  ## PopHinge -> record id


func _init() -> void:
	atlas = CardAtlas.get_shared()
	process_priority = 1000  # after hinges, sway and the story stage
	set_process(false)


## A card that never moves. h0 = print's catalog height (mesh), xf = full instance transform (scale h/h0 included).
func add_static(path: String, h0: float, xf: Transform3D) -> int:
	var r := _add(path, h0, xf, Color(1, 0, 0, 0))
	_statics.append(r)
	static_count += 1
	return r


## A hinged card: mesh at the print height h0, shown at height h with board thickness `thick` (PaperCard at h).
func add_hinged(hinge: PopHinge, path: String, h0: float, h: float, thick: float) -> int:
	var s := h / h0
	var sc := Basis.from_scale(Vector3(s, s, thick / CardAtlas.thickness_for(h0)))
	var r := _add(path, h0, Transform3D.IDENTITY, Color(s, 0, 0, 0))
	_recs[r]["hinge"] = hinge
	_recs[r]["base"] = hinge.get_parent()
	_recs[r]["scale"] = sc
	_hinge_rec[hinge] = r
	hinged_count += 1
	return r


func set_sway(r: int, amp: float, freq: float, phase: float) -> void:
	var c: Color = _recs[r]["custom"]
	_recs[r]["custom"] = Color(c.r, amp, freq, phase)


func _add(path: String, h0: float, xf: Transform3D, custom: Color) -> int:
	var idx := atlas.index_of(path, h0)
	var r := _recs.size()
	_recs.append({"idx": idx, "xf": xf, "custom": custom})
	if not _by_print.has(idx):
		_by_print[idx] = []
	_by_print[idx].append(r)
	return r


func commit() -> void:
	atlas.ensure()
	material = ShaderMaterial.new()
	material.shader = CARD_SHADER
	material.set_shader_parameter("atlas", atlas.color)
	material.set_shader_parameter("params", atlas.params)
	material.set_shader_parameter("fibre_tex", FIBRE)
	shadow_material = ShaderMaterial.new()
	shadow_material.shader = SHADOW_SHADER
	shadow_material.set_shader_parameter("atlas", atlas.color)
	shadow_material.set_shader_parameter("mask_atlas", atlas.mask)
	shadow_material.set_shader_parameter("params", atlas.params)
	var total := 0
	var keys: Array = _by_print.keys()
	keys.sort()
	for idx: int in keys:
		var e := atlas.entry(idx)
		if not e.get("ok", false):
			continue
		var ids: Array = _by_print[idx]
		var mm := MultiMesh.new()
		mm.transform_format = MultiMesh.TRANSFORM_3D
		mm.use_custom_data = true
		mm.mesh = e["mesh"]
		mm.instance_count = ids.size()
		for k in ids.size():
			var r: int = ids[k]
			_recs[r]["slot"] = k
			_recs[r]["sslot"] = total
			total += 1
		_mms[idx] = mm
		var mmi := MultiMeshInstance3D.new()
		mmi.name = (e["path"] as String).get_file().get_basename()
		mmi.multimesh = mm
		mmi.material_override = material
		mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if _DBG_MESH_SHADOWS else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		mmi.extra_cull_margin = 0.2  # sway runs in the vertex shader
		add_child(mmi)
	_shadow_mm = MultiMesh.new()
	_shadow_mm.transform_format = MultiMesh.TRANSFORM_3D
	_shadow_mm.use_custom_data = true
	_shadow_mm.mesh = _quad_mesh()
	_shadow_mm.instance_count = total
	var smi := MultiMeshInstance3D.new()
	smi.name = "Shadows"
	smi.multimesh = _shadow_mm
	smi.material_override = shadow_material
	smi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY
	smi.extra_cull_margin = 0.2
	add_child(smi)
	smi.visible = not _DBG_MESH_SHADOWS
	for r in _recs.size():
		var rec := _recs[r]
		if not rec.has("slot"):
			continue
		var c: Color = rec["custom"]
		_mms[rec["idx"]].set_instance_custom_data(rec["slot"], c)
		_shadow_mm.set_instance_custom_data(rec["sslot"], Color(float(rec["idx"]), c.g, c.b, c.a))
		if rec.has("hinge"):
			var h: PopHinge = rec["hinge"]
			h.batch = self
			(rec["base"] as Node3D).visibility_changed.connect(mark.bind(h))
		_write(r)
	committed = true
	set_process(true)


static func _quad_mesh() -> ArrayMesh:
	var a := []
	a.resize(Mesh.ARRAY_MAX)
	a[Mesh.ARRAY_VERTEX] = PackedVector3Array([Vector3(0, 0, 0), Vector3(1, 0, 0), Vector3(1, 1, 0), Vector3(0, 1, 0)])
	a[Mesh.ARRAY_NORMAL] = PackedVector3Array([Vector3.BACK, Vector3.BACK, Vector3.BACK, Vector3.BACK])
	a[Mesh.ARRAY_TEX_UV] = PackedVector2Array([Vector2(0, 0), Vector2(1, 0), Vector2(1, 1), Vector2(0, 1)])
	a[Mesh.ARRAY_INDEX] = PackedInt32Array([0, 1, 2, 0, 2, 3])
	var m := ArrayMesh.new()
	m.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, a)
	# The quad is placed per instance from the params texture: give it the page-sized bounds of any card.
	m.custom_aabb = AABB(Vector3(-4, -1, -1), Vector3(8, 6, 2))
	return m


## PopHinge._apply / base visibility: rewrite this card's instance at the end of the frame.
func mark(h: PopHinge) -> void:
	var r: int = _hinge_rec.get(h, -1)
	if r >= 0:
		_dirty[r] = true


func _process(_dt: float) -> void:
	if _dirty.is_empty():
		return
	for r: int in _dirty:
		_write(r)
	_dirty.clear()


func _write(r: int) -> void:
	var rec := _recs[r]
	if not rec.has("slot"):
		return
	var xf: Transform3D = rec["xf"]
	if rec.has("hinge"):
		var base: Node3D = rec["base"]
		var h: PopHinge = rec["hinge"]
		if base.is_visible_in_tree():
			xf = base.transform * h.transform * Transform3D(rec["scale"], Vector3.ZERO)
		else:
			xf = Transform3D(HIDDEN, base.position)
	elif rec.get("hidden", false):
		xf = Transform3D(HIDDEN, xf.origin)
	_mms[rec["idx"]].set_instance_transform(rec["slot"], xf)
	_shadow_mm.set_instance_transform(rec["sslot"], xf)


func set_wind(t: float, strength: float, axis: Vector3, gust_speed: float) -> void:
	if material == null:
		return
	var w := Vector4(t, strength, gust_speed, 0.0)
	material.set_shader_parameter("wind", w)
	material.set_shader_parameter("wind_axis", axis)
	shadow_material.set_shader_parameter("wind", w)
	shadow_material.set_shader_parameter("wind_axis", axis)


func set_wind_dir0(d: Vector2) -> void:
	for m in [material, shadow_material]:
		if m:
			m.set_shader_parameter("wind_dir0", d)


# ------------------------------------------------------------------ static cards (story sightline clearing)

func static_ids() -> Array[int]:
	return _statics


func static_xform(r: int) -> Transform3D:
	return _recs[r]["xf"]


## Mesh bounds of the record's print at its catalog height (instance scale not applied).
func static_aabb(r: int) -> AABB:
	return atlas.entry(_recs[r]["idx"]).get("aabb", AABB())


func is_static_hidden(r: int) -> bool:
	return _recs[r].get("hidden", false)


func hide_static(r: int) -> void:
	_recs[r]["hidden"] = true
	if committed:
		_write(r)
