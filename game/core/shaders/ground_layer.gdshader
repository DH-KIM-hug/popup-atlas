shader_type spatial;
render_mode cull_back, diffuse_burley, specular_disabled;
// Flat cut-paper ground layers (felt ground, path, ground-cover patches, book page). World-aligned.
// felt_tex: R low-freq mottling, G fibres, B fine grain.

uniform vec4 base_color : source_color = vec4(0.4, 0.5, 0.25, 1.0);
uniform vec4 mottle_color : source_color = vec4(0.32, 0.42, 0.2, 1.0);
uniform sampler2D felt_tex : hint_default_white, filter_linear_mipmap, repeat_enable;
uniform float mottle_scale = 0.09;
uniform float mottle_strength = 0.7;
uniform float fibre_scale = 0.9;
uniform float fibre_strength = 0.13;
uniform float grain_strength = 0.1;
uniform float bump = 0.5;
// Printed speckle (tiny ink flecks) for path / page cards.
uniform float speckle = 0.0;
uniform vec4 speckle_color : source_color = vec4(0.55, 0.42, 0.28, 1.0);
// Darken toward the polygon edge (UV.y = distance to edge in world units, 0 when unused).
uniform float edge_shade = 0.0;
varying vec3 wpos;

void vertex() { wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz; }

void fragment() {
	vec2 p = wpos.xz;
	float mott = texture(felt_tex, p * mottle_scale).r - 0.5;
	float mott2 = texture(felt_tex, p * mottle_scale * 2.3 + 0.37).r - 0.5;
	float fib = (texture(felt_tex, p * fibre_scale).g + texture(felt_tex, vec2(p.y, -p.x) * fibre_scale * 0.73 + 0.21).g) * 0.5 - 0.5;
	float fine = texture(felt_tex, p * fibre_scale * 3.1 + 0.11).b - 0.5;
	float m = clamp(0.5 + (mott * 1.6 + mott2 * 0.8) * mottle_strength, 0.0, 1.0);
	vec3 col = mix(base_color.rgb, mottle_color.rgb, m);
	col *= 1.0 + fib * fibre_strength * 2.0 + fine * grain_strength * 2.0;
	if (speckle > 0.0) {
		float s = texture(felt_tex, p * 5.3).b;
		float s2 = texture(felt_tex, p * 2.1 + 0.5).g;
		float fleck = smoothstep(0.80, 0.86, s) * smoothstep(0.55, 0.7, s2);
		col = mix(col, speckle_color.rgb, fleck * speckle);
	}
	ALBEDO = col;
	ROUGHNESS = 0.98;
	SPECULAR = 0.04;
	NORMAL_MAP = normalize(vec3(0.5 + (fib + fine) * 0.4, 0.5 + (fib - fine) * 0.3, 1.0));
	NORMAL_MAP_DEPTH = bump;
}
