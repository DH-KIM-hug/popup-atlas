class_name ContactShadows
extends MultiMeshInstance3D
## Contact occlusion under standing cards in one draw call (component B).
## The Mobile renderer has no SSAO, and the soft key shadow alone leaves cards floating; this lays a
## soft multiply ellipse plus a 2-4 px dark crease line at every card base.
## Usage: var cs := ContactShadows.new(); add(pos, yaw, width, depth); ...; cs.commit(); add_child(cs)
## (or add_child first, then commit). `add_round()` for cross-slotted trees (no crease line).

const SHADER := preload("res://core/shaders/contact_shadow.gdshader")

@export var tint := Color(0.10, 0.13, 0.07)
@export var strength := 1.0

var _items: Array = []  ## [Vector3 pos, float yaw, float w, float d, float s, float crease]


func add(pos: Vector3, yaw: float, width: float, depth := -1.0, s := 1.0) -> void:
	if depth < 0.0:
		depth = clampf(width * 0.35, 0.05, 0.22)
	_items.append([pos, yaw, width * 1.15, depth, s, 0.55])


func add_round(pos: Vector3, radius: float, s := 1.0) -> void:
	_items.append([pos, 0.0, radius * 2.0, radius * 1.6, s, 0.0])


## PE r2: drop the shadows of small cards (width < max_w) within r of c (a built cluster replaced them).
func clear_area(c: Vector2, r: float, max_w: float) -> void:
	_items = _items.filter(func(it): return float(it[2]) >= max_w or Vector2((it[0] as Vector3).x, (it[0] as Vector3).z).distance_to(c) > r)


func commit() -> void:
	var mm := MultiMesh.new()
	mm.transform_format = MultiMesh.TRANSFORM_3D
	mm.use_custom_data = true
	var pm := PlaneMesh.new()
	pm.size = Vector2.ONE
	mm.mesh = pm
	mm.instance_count = _items.size()
	for i in _items.size():
		var it: Array = _items[i]
		var b := Basis(Vector3.UP, it[1]) * Basis.from_scale(Vector3(it[2], 1.0, it[3]))
		mm.set_instance_transform(i, Transform3D(b, it[0] + Vector3(0, 0.0025, 0)))
		mm.set_instance_custom_data(i, Color(it[4], it[5], 0, 0))
	multimesh = mm
	var m := ShaderMaterial.new()
	m.shader = SHADER
	m.set_shader_parameter("tint", tint)
	m.set_shader_parameter("strength", strength)
	material_override = m
	cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
