shader_type spatial;
render_mode cull_back, diffuse_burley, specular_disabled;

uniform sampler2D albedo_tex : source_color, filter_linear_mipmap_anisotropic;
uniform sampler2D fibre_tex : hint_default_white, filter_linear_mipmap, repeat_enable;
uniform vec2 card_size = vec2(0.4);
uniform float fibre_density = 7.0;   // repeats per world unit
uniform float fibre_strength = 0.16;
uniform bool plain = false;
uniform vec4 plain_color : source_color = vec4(0.93, 0.89, 0.8, 1.0);
uniform float translucency = 0.18;   // light through thin paper from behind

void fragment() {
	vec4 c = plain ? plain_color : texture(albedo_tex, UV);
	if (!plain && c.a < 0.5) discard;
	vec2 fuv = UV * card_size * fibre_density;
	float f = texture(fibre_tex, fuv).r;
	float f2 = texture(fibre_tex, fuv * 2.7 + 0.31).r;
	float fibre = mix(f, f2, 0.4) - 0.5;
	ALBEDO = c.rgb * (1.0 + fibre * fibre_strength * 2.0);
	ROUGHNESS = 0.94;
	SPECULAR = 0.12;
	// Paper grain also roughens the shading normal a touch.
	NORMAL_MAP = normalize(vec3(0.5 + fibre * 0.35, 0.5 - fibre * 0.25, 1.0));
	NORMAL_MAP_DEPTH = 0.6;
	BACKLIGHT = c.rgb * translucency;
}
