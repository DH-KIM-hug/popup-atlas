shader_type spatial;
render_mode cull_back, diffuse_burley, specular_disabled;
// Book page block: cream top, page-stack lines on the sides (B_look).
uniform vec4 page_color : source_color = vec4(0.93, 0.88, 0.76, 1.0);
uniform sampler2D fibre_tex : hint_default_white, filter_linear_mipmap, repeat_enable;
uniform float thickness = 0.3;
varying vec3 lpos;
varying vec3 lnrm;
void vertex() { lpos = VERTEX; lnrm = NORMAL; }
void fragment() {
	float f = texture(fibre_tex, (lpos.xz + lpos.y) * 3.0).r - 0.5;
	vec3 col = page_color.rgb * (1.0 + f * 0.12);
	if (abs(lnrm.y) < 0.5) {
		float y = (lpos.y / thickness + 0.5);
		float lines = sin(y * 260.0 + f * 6.0) * 0.5 + 0.5;
		col *= mix(0.86, 1.0, lines);
		col *= mix(0.78, 1.0, smoothstep(0.0, 0.25, y));
	}
	ALBEDO = col;
	ROUGHNESS = 0.95;
}
