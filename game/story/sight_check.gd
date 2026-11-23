class_name SightCheck
extends RefCounted
## Line-of-sight occlusion for the OCCLUDE gate check (wave 1, 2026-11-24). The box test in SpreadStage only knew the
## story's own set pieces by their front-card rectangle, so the gate audit v1 missed a roof filling the frame over the
## witch_candy parade (5:36), Dahyun's big hat in the shop doorway (0:55) and turnip v4's template leaves over a
## runner. This one casts rays from the camera to a grid of points on the figure (head and body) and asks the
## renderer which instances they cross (RenderingServer.instances_cull_ray), then tests each candidate exactly:
##  - template lawn cards (CardBatch MultiMeshes): every card of that print, its cut shape (the print's alpha);
##  - PaperCards (set-piece cards and bands, other actors' figures, props): the card plane, the print's alpha;
##  - other meshes (house bodies, roofs, kit buildings): the mesh box in its own frame.
## The ground (page, road, stream, terraces), the actor itself and hidden / folded things never count.

const ALPHA_MIN := 0.5
static var _img_cache := {}  ## texture path / rid -> [Image, used Rect2i]


static func _alpha_img(tex: Texture2D) -> Array:
	if tex == null:
		return []
	var key: String = tex.resource_path if tex.resource_path != "" else str(tex.get_rid())
	if _img_cache.has(key):
		return _img_cache[key]
	var img := PaperCard._source_image(tex)
	var out := []
	if img != null:
		out = [img, img.get_used_rect()]
	_img_cache[key] = out
	return out


## Where the segment a -> b (card-local) crosses the card plane z = 0, or null.
static func _cross(a: Vector3, b: Vector3) -> Variant:
	if (a.z > 0.0) == (b.z > 0.0):
		return null
	var t := a.z / (a.z - b.z)
	return a.lerp(b, t)


## Does the segment (world) pass through the opaque part of this PaperCard?
static func paper_card_blocks(c: PaperCard, from: Vector3, to: Vector3) -> bool:
	if c.mesh == null or c.texture == null:
		return false
	var inv := c.global_transform.affine_inverse()
	var hit: Variant = _cross(inv * from, inv * to)
	if hit == null:
		return false
	var p: Vector3 = hit
	var bb := c.mesh.get_aabb()
	if p.x < bb.position.x or p.x > bb.end.x or p.y < bb.position.y or p.y > bb.end.y:
		return false
	var ai := _alpha_img(c.texture)
	if ai.is_empty():
		return true
	var img: Image = ai[0]
	var ur: Rect2i = ai[1]
	# the mesh spans the cut shape's bounds (PaperCard._build): x over the opaque columns, y from the bottom up
	var u := (p.x - bb.position.x) / maxf(bb.size.x, 1e-5)
	var v := (p.y - bb.position.y) / maxf(bb.size.y, 1e-5)
	var px := clampi(ur.position.x + int(u * ur.size.x), 0, img.get_width() - 1)
	var py := clampi(ur.end.y - 1 - int(v * ur.size.y), 0, img.get_height() - 1)
	return img.get_pixel(px, py).a > ALPHA_MIN


## Does the segment cross a plain mesh's box (house body, roof, kit part)? Thin card-like meshes use the plane.
static func mesh_blocks(m: MeshInstance3D, from: Vector3, to: Vector3) -> bool:
	if m.mesh == null:
		return false
	var inv := m.global_transform.affine_inverse()
	var bb := m.mesh.get_aabb()  # (no shrink: a thin card's box went negative, "AABB size is negative")
	if bb.size.x <= 0.0 or bb.size.y <= 0.0:
		return false
	var lf := inv * from
	var lt := inv * to
	# a box someone stands in (a room, a house body with its doorway) or the camera looks out of: its bounds say
	# nothing about the walls between them (wolf_goats room: every kid read as hidden by the cottage)
	if bb.has_point(lf) or bb.grow(0.05).has_point(lt):
		return false
	return bb.intersects_segment(lf, lt) != null  # Variant: the hit point or null


## Name of what blocks the segment, "" if nothing. `skip`: the actor (its own cards); `stage`: SpreadStage for names.
static func blocker(stage: Node3D, cam: Camera3D, from: Vector3, to: Vector3, skip: Node, world: MeadowWorld) -> String:
	var ids := RenderingServer.instances_cull_ray(from, to, cam.get_world_3d().scenario)
	for id in ids:
		var o := instance_from_id(id)
		if not (o is GeometryInstance3D):
			continue
		var g := o as GeometryInstance3D
		if not g.is_visible_in_tree() or skip.is_ancestor_of(g) or g.cast_shadow == GeometryInstance3D.SHADOW_CASTING_SETTING_SHADOWS_ONLY:
			continue
		if world and world.ground and world.ground.is_ancestor_of(g):
			continue  # the page itself: ground sheets, road, stream, verges
		if g is MultiMeshInstance3D:
			continue  # template lawn cards: CardBatch.blockers() tests all rays at once (hidden())
		if not (g is MeshInstance3D):
			continue
		var owner_name := _owner_name(stage, g)
		if owner_name == "":
			continue
		var hit := paper_card_blocks(g as PaperCard, from, to) if g is PaperCard else mesh_blocks(g as MeshInstance3D, from, to)
		if hit:
			return owner_name
	return ""


## Who a mesh belongs to: an actor role, a set piece name, "world:<node>" for template buildings, "fx:<node>" for
## story props; "" for things that never hide anyone (flat ground sheets, sky hangers' halos, the book).
static func _owner_name(stage: Node3D, n: Node) -> String:
	var p := n
	while p != null and p != stage:
		if p is StoryActor:
			return (p as StoryActor).role
		if p is SetPiece:
			var sp := p as SetPiece
			if sp.flat or sp.piece_name.begins_with("lights_") or sp.has_meta("inside_only"):
				return ""
			if sp.walls and not sp.walls.visible and sp.walls.is_ancestor_of(n):
				return ""
			return sp.piece_name
		if p is MeadowWorld:
			return "world:" + str(n.get_parent().name if n.get_parent() else n.name)
		p = p.get_parent()
	if p == stage:
		return "fx:" + str(n.name)
	return ""


## Fraction of the actor's head-and-body points hidden, per blocker: {name: frac}. 3 x 3 rays over the upper 70 %
## of the figure (legs behind a fence or a pot are fine, a hidden face / body is not).
static func hidden(stage: Node3D, cam: Camera3D, a: StoryActor, world: MeadowWorld) -> Dictionary:
	var out := {}
	var h := a.puppet.height * a.pop_s
	var w := a.puppet.height * 0.42
	var cr := cam.global_transform.basis.x.normalized()
	var base := a.global_position + Vector3.UP * (a.hop + a.lift)
	var from := cam.global_position
	var n := 0
	var tos: Array[Vector3] = []
	for fy: float in [0.4, 0.65, 0.88]:
		for fx: float in [-0.22, 0.0, 0.22]:
			var q := base + Vector3.UP * h * fy + cr * w * fx
			if cam.is_position_behind(q):
				continue
			n += 1
			tos.append(q + (from - q).normalized() * 0.03)  # stop short of the figure's own card
	var lawn: Array = world.batch.blockers(from, tos) if world and world.batch else []
	for i in tos.size():
		var b := blocker(stage, cam, from, tos[i], a, world)
		if b == "" and i < lawn.size():
			b = str(lawn[i])
		if b != "":
			out[b] = float(out.get(b, 0.0)) + 1.0
	for k in out:
		out[k] = float(out[k]) / maxf(float(n), 1.0)
	return out
