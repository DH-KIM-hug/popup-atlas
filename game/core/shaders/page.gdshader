shader_type spatial;
render_mode cull_back, diffuse_burley, specular_disabled;

uniform sampler2D page_tex : source_color, filter_linear_mipmap_anisotropic, repeat_enable;
uniform sampler2D fibre_tex : hint_default_white, filter_linear_mipmap, repeat_enable;
uniform vec4 tint : source_color = vec4(1.0);
uniform float page_scale = 0.18;  // page texture repeats per world unit
uniform float fibre_density = 5.0;
varying vec3 wpos;

void vertex() { wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz; }

void fragment() {
	vec3 p = texture(page_tex, wpos.xz * page_scale).rgb;
	float f = texture(fibre_tex, wpos.xz * fibre_density).r - 0.5;
	ALBEDO = p * tint.rgb * (1.0 + f * 0.22);
	ROUGHNESS = 0.97;
	NORMAL_MAP = normalize(vec3(0.5 + f * 0.3, 0.5 + f * 0.2, 1.0));
	NORMAL_MAP_DEPTH = 0.5;
}
