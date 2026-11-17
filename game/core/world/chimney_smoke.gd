class_name ChimneySmoke
extends Node3D
## Cut-paper smoke puffs rising from a chimney (integrator r1): small cream card discs that rise, drift
## downwind, grow, then shrink away (paper never fades, it is cut smaller). Rigid flat cards, camera-facing yaw.

@export var puffs := 5
@export var rise := 0.55  ## height a puff climbs before it is gone
@export var period := 3.2  ## seconds per puff life
@export var size := 0.07
@export var drift := Vector3(0.18, 0, -0.05)

var _cards: Array[MeshInstance3D] = []
var _t := 0.0
static var _mat: StandardMaterial3D


func _ready() -> void:
	if _mat == null:
		_mat = StandardMaterial3D.new()
		_mat.albedo_texture = _disc_texture()
		_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
		_mat.alpha_scissor_threshold = 0.5
		_mat.cull_mode = BaseMaterial3D.CULL_DISABLED
		_mat.roughness = 1.0
		_mat.albedo_color = Color(0.95, 0.92, 0.84)
	for i in puffs:
		var q := QuadMesh.new()
		q.size = Vector2.ONE
		var mi := MeshInstance3D.new()
		mi.mesh = q
		mi.material_override = _mat
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(mi)
		_cards.append(mi)


static func _disc_texture() -> Texture2D:
	# Scalloped cloud-puff silhouette (3 overlapping lobes), with a soft printed grey core.
	var n := 64
	var img := Image.create(n, n, false, Image.FORMAT_RGBA8)
	for y in n:
		for x in n:
			var p := Vector2(x + 0.5, y + 0.5) / n
			var d := minf(p.distance_to(Vector2(0.5, 0.56)) / 0.3, minf(p.distance_to(Vector2(0.3, 0.62)) / 0.2, p.distance_to(Vector2(0.7, 0.62)) / 0.2))
			var a := 1.0 if d < 1.0 else 0.0
			var shade := 0.9 + 0.1 * (1.0 - p.y)
			img.set_pixel(x, y, Color(shade, shade * 0.98, shade * 0.93, a))
	img.generate_mipmaps()
	return ImageTexture.create_from_image(img)


func _process(dt: float) -> void:
	if PopHinge.fixed_dt > 0.0:
		dt = PopHinge.fixed_dt
	_t += dt
	var cam := get_viewport().get_camera_3d()
	for i in _cards.size():
		var u := fposmod(_t / period + float(i) / puffs, 1.0)
		var c := _cards[i]
		var s := size * (0.5 + 1.1 * u) * (1.0 - smoothstep(0.7, 1.0, u)) + 0.0001
		c.position = Vector3(0, u * rise, 0) + drift * u * u + Vector3(0.02 * sin(u * 9.0 + i), 0, 0)
		c.scale = Vector3(s, s, s)
		if cam:
			var to := cam.global_position - c.global_position
			c.rotation = Vector3(0, atan2(to.x, to.z), 0)
