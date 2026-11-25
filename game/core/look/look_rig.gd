class_name LookRig
extends Node3D
## Reusable look rig (component B): environment + grade, warm low key light with one shadow map,
## cool fill, tilt-shift camera whose DOF follows a focus point, and a screen-space finishing pass.
## Usage: add a LookRig, set `focus_target` (e.g. the traveller) or `focus_point`; tweak `elevation_deg`,
## `yaw_deg`, `distance`. The camera is `rig.camera` (current). Mobile renderer safe: no SSAO/SSIL/SDFGI.

const POST_SHADER := preload("res://core/shaders/post_grade.gdshader")

@export var focus_target: Node3D
@export var focus_point := Vector3(0, 0.1, 0)
@export var focus_height := 0.15  ## added to the target's origin (look at the chest, not the feet)
@export_range(20.0, 70.0) var elevation_deg := 32.0
@export var yaw_deg := 0.0
@export var distance := 9.0
@export_range(14.0, 40.0) var fov := 20.0
@export var follow_smooth := 4.0  ## 1/s; 0 = snap

@export_group("Depth of field")
@export var dof_enabled := true
@export var dof_near_margin := 0.9  ## sharp range in front of the focus point
@export var dof_far_margin := 2.8  ## sharp range behind it
@export var dof_near_transition := 2.0
@export var dof_far_transition := 4.0
@export var dof_amount := 0.05

@export_group("Light")
@export var key_color := Color("ffd6a6")
@export var key_energy := 1.9
@export var key_elevation_deg := 44.0
@export var key_yaw_deg := -58.0  ## 0 = light from camera's back; negative = from the left
@export var fill_color := Color("8fa9d6")
@export var fill_energy := 0.55
@export var ambient_color := Color("b4bf9e")  ## warm sage: shadows go soft green, not black
@export var ambient_energy := 0.5
@export_range(0.0, 1.0) var shadow_opacity := 0.86
@export var shadow_softness := 1.1  ## PCF blur; lower = crisper, anchored shadows
@export var shadow_distance := 16.0

@export_group("Grade")
@export var exposure := 0.8
@export var env_saturation := 0.98
@export var env_contrast := 1.03
@export var env_brightness := 1.0
@export var background := Color("1c120b")
@export var post_enabled := true
@export var tilt_blur := 0.95  ## mip level at frame edges, 0 = off
@export var tilt_focus_y := 0.52
@export var tilt_band_half := 0.15
@export var tilt_band_soft := 0.34
@export var tilt_top_bias := 0.9  ## far (top) vs near (bottom) blur; the footage is about even
@export var vignette := 0.2
@export var post_saturation := 0.92
@export var post_contrast := 1.0
@export var lens_soft := 0.0  ## global mip softness (photo lens, not CG-crisp)
@export var grain := 0.0
@export var toe := 0.0
@export var fill_elevation_deg := 35.0

@export_group("Haze")
@export var haze_enabled := true  ## warm depth haze beyond the focus: depth reads past the DOF
@export var haze_color := Color("c9c2a2")
@export var haze_begin := 2.5  ## past the focus distance
@export var haze_length := 14.0
@export var haze_amount := 0.45

## Web build only (docs/WEB_BUILD.md "Look on the web"): the browser runs the Compatibility (WebGL 2) renderer, which
## draws the same rig with shadow acne ribs on flat ground ("corduroy": its depth bias is in other units) and a lifted,
## greyer tone (web ~ native^0.62). These overrides bring it back to the Mobile (iOS) look; tuned 2026-11-25 against
## native captures (tools/web/look_variants.sh, tools/web/fidelity_*). `--web-look` applies them on a desktop run too
## (with --rendering-method gl_compatibility) for tuning; iOS / desktop Mobile runs never take this path.
const WEB_SHADOW_BIAS := 2.0  ## 0.08 ribbed the ground, 1.0 halved it, 2.0 clean with contact shadows kept
const WEB_SHADOW_NORMAL_BIAS := 0.6
const WEB_POST_PRE_GAMMA := 1.8  ## post_grade pre_gamma: undoes the lifted tone curve
const WEB_POST_SATURATION := 1.14  ## multiplies post_saturation
const WEB_POST_CONTRAST := 0.92  ## multiplies post_contrast (the gamma alone overshoots contrast)


static func web_look() -> bool:
	return OS.has_feature("web") or OS.get_cmdline_user_args().has("--web-look")


var camera: Camera3D
var key: DirectionalLight3D
var fill: DirectionalLight3D
var environment: Environment
var post: ColorRect
var _attr: CameraAttributesPractical
var _look := Vector3.ZERO
var _built := false


func _ready() -> void:
	_build()
	_look = _target_point()
	_place_camera(1.0)


func _build() -> void:
	if _built:
		return
	_built = true
	environment = Environment.new()
	environment.background_mode = Environment.BG_COLOR
	environment.background_color = background
	environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	environment.ambient_light_color = ambient_color
	environment.ambient_light_energy = ambient_energy
	environment.tonemap_mode = Environment.TONE_MAPPER_AGX
	environment.tonemap_exposure = exposure
	environment.glow_enabled = true
	environment.glow_intensity = 0.35
	environment.glow_bloom = 0.03
	environment.glow_hdr_threshold = 0.9
	environment.adjustment_enabled = true
	environment.adjustment_saturation = env_saturation
	environment.adjustment_contrast = env_contrast
	environment.adjustment_brightness = env_brightness
	if haze_enabled:
		environment.fog_enabled = true
		environment.fog_mode = Environment.FOG_MODE_DEPTH
		environment.fog_light_color = haze_color
		environment.fog_light_energy = 1.0
		environment.fog_density = haze_amount
		environment.fog_sky_affect = 0.0
		environment.fog_sun_scatter = 0.0
		environment.fog_depth_curve = 1.6
		environment.fog_depth_begin = distance + haze_begin
		environment.fog_depth_end = distance + haze_begin + haze_length
	var we := WorldEnvironment.new()
	we.name = "WorldEnvironment"
	we.environment = environment
	add_child(we)

	# Soft but cheap shadows on Mobile.
	RenderingServer.directional_soft_shadow_filter_set_quality(RenderingServer.SHADOW_QUALITY_SOFT_LOW)
	RenderingServer.camera_attributes_set_dof_blur_quality(RenderingServer.DOF_BLUR_QUALITY_MEDIUM, true)

	key = DirectionalLight3D.new()
	key.name = "Key"
	key.light_color = key_color
	key.light_energy = key_energy
	key.shadow_enabled = true
	key.shadow_bias = 0.08  # LOOKF r2: 0.02 drew shadow acne as a diagonal rib on the felt
	key.shadow_normal_bias = 0.6
	key.shadow_blur = shadow_softness
	key.shadow_opacity = shadow_opacity
	key.light_angular_distance = 1.2
	key.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_2_SPLITS
	key.directional_shadow_max_distance = shadow_distance
	key.directional_shadow_blend_splits = true
	if web_look():
		key.shadow_bias = WEB_SHADOW_BIAS
		key.shadow_normal_bias = WEB_SHADOW_NORMAL_BIAS
	key.rotation_degrees = Vector3(-key_elevation_deg, yaw_deg + key_yaw_deg, 0)
	add_child(key)

	fill = DirectionalLight3D.new()
	fill.name = "Fill"
	fill.light_color = fill_color
	fill.light_energy = fill_energy
	fill.shadow_enabled = false
	fill.light_specular = 0.0
	fill.rotation_degrees = Vector3(-fill_elevation_deg, yaw_deg + key_yaw_deg + 160.0, 0)
	add_child(fill)

	camera = Camera3D.new()
	camera.name = "Camera"
	camera.fov = fov
	camera.near = 0.1
	camera.far = 80.0
	_attr = CameraAttributesPractical.new()
	camera.attributes = _attr
	add_child(camera)
	camera.current = true

	if post_enabled:
		var layer := CanvasLayer.new()
		layer.name = "Post"
		layer.layer = 10
		add_child(layer)
		post = ColorRect.new()
		post.name = "Grade"
		post.mouse_filter = Control.MOUSE_FILTER_IGNORE
		post.set_anchors_preset(Control.PRESET_FULL_RECT)
		var m := ShaderMaterial.new()
		m.shader = POST_SHADER
		m.set_shader_parameter("max_lod", tilt_blur)
		m.set_shader_parameter("focus_y", tilt_focus_y)
		m.set_shader_parameter("vignette", vignette)
		m.set_shader_parameter("band_half", tilt_band_half)
		m.set_shader_parameter("band_soft", tilt_band_soft)
		m.set_shader_parameter("top_bias", tilt_top_bias)
		var web := web_look()
		m.set_shader_parameter("saturation", post_saturation * (WEB_POST_SATURATION if web else 1.0))
		m.set_shader_parameter("contrast", post_contrast * (WEB_POST_CONTRAST if web else 1.0))
		if web:
			m.set_shader_parameter("pre_gamma", WEB_POST_PRE_GAMMA)
		m.set_shader_parameter("base_lod", lens_soft)
		m.set_shader_parameter("grain", grain)
		m.set_shader_parameter("toe", toe)
		post.material = m
		layer.add_child(post)


func _target_point() -> Vector3:
	if is_instance_valid(focus_target):
		return focus_target.global_position + Vector3(0, focus_height, 0)
	return focus_point


func _process(delta: float) -> void:
	var a := 1.0 if follow_smooth <= 0.0 else 1.0 - exp(-follow_smooth * delta)
	_place_camera(a)


## Snap the camera to the current focus (after teleporting the target).
func snap() -> void:
	_look = _target_point()
	_place_camera(1.0)


func _place_camera(a: float) -> void:
	if camera == null:
		return
	_look = _look.lerp(_target_point(), a)
	var el := deg_to_rad(elevation_deg)
	var yw := deg_to_rad(yaw_deg)
	var off := Vector3(sin(yw) * cos(el), sin(el), cos(yw) * cos(el)) * distance
	camera.fov = fov
	camera.global_position = _look + off
	camera.look_at(_look, Vector3.UP)
	_update_dof()


func _update_dof() -> void:
	if _attr == null:
		return
	var d := camera.global_position.distance_to(_look)
	_attr.dof_blur_far_enabled = dof_enabled
	_attr.dof_blur_near_enabled = dof_enabled
	_attr.dof_blur_far_distance = d + dof_far_margin
	_attr.dof_blur_far_transition = dof_far_transition
	_attr.dof_blur_near_distance = maxf(0.1, d - dof_near_margin)
	_attr.dof_blur_near_transition = dof_near_transition
	_attr.dof_blur_amount = dof_amount
	if environment and haze_enabled:
		environment.fog_depth_begin = d + haze_begin
		environment.fog_depth_end = d + haze_begin + haze_length
