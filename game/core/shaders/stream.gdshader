shader_type spatial;
render_mode cull_back, diffuse_burley;
// Cut-paper stream: teal card with printed cream ripple strips. UV.x along flow (world units), UV.y across 0..1.

uniform vec4 deep_color : source_color = vec4(0.10, 0.42, 0.44, 1.0);
uniform vec4 shallow_color : source_color = vec4(0.30, 0.66, 0.62, 1.0);
uniform vec4 ripple_color : source_color = vec4(0.86, 0.93, 0.86, 1.0);
uniform sampler2D felt_tex : hint_default_white, filter_linear_mipmap, repeat_enable;
uniform float flow_speed = 0.04;
uniform float ripple_amount = 1.0;

float band(float x, float w) { return smoothstep(w, 0.0, abs(fract(x) - 0.5) - 0.5 + w * 2.0); }

void fragment() {
	float across = UV.y;
	float edge = abs(across - 0.5) * 2.0;
	vec3 col = mix(deep_color.rgb, shallow_color.rgb, smoothstep(0.2, 1.0, edge));
	float n = texture(felt_tex, vec2(UV.x * 0.15, across * 0.3)).r - 0.5;
	float t = TIME * flow_speed;
	// Ripple strips: short cream dashes in a few lanes, wavy along the flow.
	float rip = 0.0;
	for (int i = 0; i < 3; i++) {
		float lane = 0.24 + float(i) * 0.26 + n * 0.12;
		float wv = sin((UV.x - t) * 5.0 + float(i) * 2.1) * 0.035;
		float d = abs(across - lane - wv);
		float dash = smoothstep(0.25, 0.45, sin((UV.x - t * (1.0 + float(i) * 0.3)) * (2.4 + float(i) * 0.7) + float(i) * 1.7) * 0.5 + 0.5);
		rip = max(rip, (1.0 - smoothstep(0.012, 0.022, d)) * dash);
	}
	// Bank shine strip close to each edge.
	rip = max(rip, (1.0 - smoothstep(0.015, 0.03, abs(edge - 0.78))) * 0.7);
	col = mix(col, ripple_color.rgb, rip * ripple_amount);
	float fib = texture(felt_tex, UV * vec2(1.2, 0.4)).g - 0.5;
	ALBEDO = col * (1.0 + fib * 0.25);
	ROUGHNESS = mix(0.45, 0.9, rip);
	SPECULAR = 0.35;
	NORMAL_MAP = normalize(vec3(0.5 + fib * 0.3, 0.5, 1.0));
}
