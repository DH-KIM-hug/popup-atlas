shader_type spatial;
render_mode unshaded, blend_mix, depth_draw_never, cull_disabled, shadows_disabled;
// Soft contact shadow skirt around a raised cut-paper layer (integrator r1). Vertex COLOR.a = strength
// (1 at the cut line, 0 at the outer rim), so the lower layer darkens right against each cut edge.
uniform vec4 tint : source_color = vec4(0.12, 0.13, 0.06, 1.0);
uniform float strength = 0.55;
void fragment() {
	float a = COLOR.a;
	ALBEDO = tint.rgb;
	ALPHA = a * a * strength;
}
