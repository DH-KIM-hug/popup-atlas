shader_type spatial;
render_mode cull_back, diffuse_burley;
// Walnut table under the book (B_look): long flowing grain, ring figure, pores, and a varnish sheen
// (roughness varies with the grain so the key light picks out streaks). Procedural from the felt noise.
uniform vec4 wood_dark : source_color = vec4(0.16, 0.085, 0.045, 1.0);
uniform vec4 wood_light : source_color = vec4(0.42, 0.25, 0.13, 1.0);
uniform sampler2D felt_tex : hint_default_white, filter_linear_mipmap, repeat_enable;
uniform float plank_width = 2.6;
varying vec3 wpos;
void vertex() { wpos = (MODEL_MATRIX * vec4(VERTEX, 1.0)).xyz; }
void fragment() {
	vec2 p = wpos.xz;
	float plank = floor(p.y / plank_width);
	vec2 q = vec2(p.x + plank * 7.3, p.y);
	float warp = (texture(felt_tex, q * vec2(0.015, 0.05)).r - 0.5) * 2.0;
	float rings = fract((q.y + warp * 1.4 + texture(felt_tex, q * vec2(0.03, 0.12)).r * 0.8) * 3.2);
	float ring = smoothstep(0.0, 0.18, rings) * smoothstep(1.0, 0.55, rings);
	float streak = texture(felt_tex, q * vec2(0.05, 1.3)).g;
	float pores = smoothstep(0.62, 0.8, texture(felt_tex, q * vec2(0.25, 6.0)).b);
	float t = clamp(ring * 0.55 + streak * 0.45 - pores * 0.25, 0.0, 1.0);
	vec3 col = mix(wood_dark.rgb, wood_light.rgb, t);
	float seam = smoothstep(0.0, 0.025, abs(fract(p.y / plank_width) - 0.0)) * smoothstep(0.0, 0.025, abs(1.0 - fract(p.y / plank_width)));
	col *= mix(0.45, 1.0, seam);
	ALBEDO = col;
	ROUGHNESS = mix(0.22, 0.5, streak) + pores * 0.2;
	SPECULAR = 0.55;
	NORMAL_MAP = normalize(vec3(0.5, 0.5 + (streak - 0.5) * 0.25, 1.0));
	NORMAL_MAP_DEPTH = 0.6;
}
