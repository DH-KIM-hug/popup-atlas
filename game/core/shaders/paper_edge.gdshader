shader_type spatial;
render_mode cull_back, diffuse_burley, specular_disabled;

uniform vec4 edge_color : source_color = vec4(0.96, 0.92, 0.82, 1.0);
uniform sampler2D fibre_tex : hint_default_white, filter_linear_mipmap, repeat_enable;

void fragment() {
	// UV.x runs along the cut in world units, UV.y across the thickness.
	float f = texture(fibre_tex, vec2(UV.x * 9.0, UV.y * 0.08 + UV.x * 0.3)).r - 0.5;
	// Slight fuzz darkening at the two cut lips.
	float lip = smoothstep(0.0, 0.25, UV.y) * smoothstep(1.0, 0.75, UV.y);
	ALBEDO = edge_color.rgb * (0.93 + f * 0.14) * mix(0.9, 1.0, lip);
	ROUGHNESS = 1.0;
	SPECULAR = 0.05;
}
