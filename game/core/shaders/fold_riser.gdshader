shader_type spatial;
render_mode cull_back, diffuse_burley, specular_disabled;
// PE r1: riser face of a folded cardstock step (tiers, box-pops, step-folds). The step is one sheet folded
// down: the riser is printed stock (a little darker than the tread, it faces away from the sky), with a
// thin cream cut line + rounded crease highlight at the top fold and a crease shadow where it meets the
// level below. UV.x runs along the riser in world units, UV.y 0 = top fold .. 1 = bottom fold.

uniform vec4 stock_color : source_color = vec4(0.45, 0.55, 0.36, 1.0);
uniform vec4 lip_color : source_color = vec4(0.93, 0.89, 0.76, 1.0);
uniform sampler2D fibre_tex : hint_default_white, filter_linear_mipmap, repeat_enable;
uniform float lip = 0.14;  // share of the riser height taken by the cut line / crease highlight
uniform float foot_dark = 0.35;
uniform float stripe = 0.0;  // optional printed vertical score lines (box-pop faces)

void fragment() {
	float f = texture(fibre_tex, vec2(UV.x * 7.0, UV.y * 0.15 + UV.x * 0.21)).r - 0.5;
	vec3 c = stock_color.rgb * (0.86 + f * 0.2);
	float top = 1.0 - smoothstep(lip * 0.55, lip, UV.y);
	c = mix(c, lip_color.rgb * (0.95 + f * 0.1), top * 0.85);
	float bot = smoothstep(0.7, 1.0, UV.y);
	c *= 1.0 - foot_dark * bot;
	if (stripe > 0.0) {
		float s = abs(fract(UV.x * stripe) - 0.5);
		c *= 1.0 - 0.12 * (1.0 - smoothstep(0.0, 0.04, s));
	}
	ALBEDO = c;
	ROUGHNESS = 0.95;
}
