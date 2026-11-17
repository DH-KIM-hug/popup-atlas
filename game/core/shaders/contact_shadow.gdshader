shader_type spatial;
render_mode unshaded, blend_mix, depth_draw_never, cull_disabled, shadows_disabled, fog_disabled;
// Contact occlusion decal under standing cards (B_look). Instanced (MultiMesh) unit quad in XZ.
// A soft ellipse plus a tight dark crease line along the card's base, alpha-blended dark over the felt.
// INSTANCE_CUSTOM.r = strength, .g = crease (0 for round footprints, e.g. cross-slotted trees).

uniform vec4 tint : source_color = vec4(0.10, 0.13, 0.07, 1.0);
uniform float strength = 1.0;
varying vec2 cust;

void vertex() { cust = INSTANCE_CUSTOM.rg; }

void fragment() {
	vec2 q = (UV - 0.5) * 2.0;  // -1..1, x along the card, y across
	float soft = 1.0 - smoothstep(0.0, 1.0, length(q));
	soft = soft * soft;
	float crease = (1.0 - smoothstep(0.05, 0.16, abs(q.y))) * (1.0 - smoothstep(0.7, 0.95, abs(q.x)));
	float a = clamp((soft * 0.8 + crease * cust.y * 1.3) * cust.x * strength, 0.0, 1.0);
	ALBEDO = tint.rgb;
	ALPHA = a * 0.85;
}
