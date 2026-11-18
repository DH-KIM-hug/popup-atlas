class_name StaticCards
extends RefCounted
## Cards that never move (integrator, round 1; perf 2026-11-18). Kept as the placement API: the transforms are the
## same as before (print mesh built once at the catalog height h0, instanced with a uniform scale h/h0; cross-slotted
## pairs add a second instance at 90°), but the instances now go to CardBatch, which draws them together with the
## hinged cards of the same print in one MultiMesh and casts their shadows from one quad MultiMesh.
##   var sc := StaticCards.new(batch); sc.add(path, h0, h, pos, yaw, lean, cross, tilt); ...

var batch: CardBatch
var count := 0


func _init(b: CardBatch) -> void:
	batch = b


func add(path: String, h0: float, h: float, pos: Vector3, yaw: float, lean := 0.0, cross := false, tilt := 0.0) -> void:
	var s := h / h0
	var b := Basis(Vector3.UP, yaw) * Basis(Vector3.BACK, lean) * Basis(Vector3.RIGHT, tilt) * Basis.from_scale(Vector3.ONE * s)
	batch.add_static(path, h0, Transform3D(b, pos))
	count += 1
	if cross:
		var thick := CardAtlas.thickness_for(h0)
		var bb := b * Basis(Vector3.UP, PI * 0.5) * Basis.from_scale(Vector3(1, 0.96, 1))
		batch.add_static(path, h0, Transform3D(bb, pos + b * Vector3(0, 0, thick * 1.1)))
		count += 1
