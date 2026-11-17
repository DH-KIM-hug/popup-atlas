shader_type spatial;
render_mode cull_back, diffuse_burley, specular_disabled;
// PE r1: glue foot / easel strut of a standing card (one MultiMesh for the whole spread).
// Top face: the card's own stock colour (INSTANCE_CUSTOM.rgb), a dark crease line where it folds up into
// the card (UV.y = 0) and a faint lift at the free end. Cut walls (UV.x > 1.5): cream core tinted by the stock.

uniform sampler2D fibre_tex : hint_default_white, filter_linear_mipmap, repeat_enable;
uniform vec4 edge_color : source_color = vec4(0.95, 0.9, 0.79, 1.0);
uniform float crease_dark = 0.42;

varying vec3 stock;
varying float edge_k;

void vertex() {
	// custom data is raw sRGB (no source_color conversion): to linear, or the tabs wash out pale
	stock = pow(INSTANCE_CUSTOM.rgb, vec3(2.2));
	edge_k = INSTANCE_CUSTOM.a;
}

void fragment() {
	if (UV.x > 1.5) {
		float f = texture(fibre_tex, vec2(UV.y * 9.0, UV.x * 0.3)).r - 0.5;
		ALBEDO = mix(edge_color.rgb, stock, edge_k) * (1.0 + f * 0.14);
	} else {
		float f = texture(fibre_tex, UV * vec2(3.0, 1.0)).r - 0.5;
		float crease = mix(1.0 - crease_dark, 1.0, smoothstep(0.02, 0.2, UV.y));
		float lip = 1.0 + 0.07 * smoothstep(0.82, 1.0, UV.y);
		ALBEDO = stock * crease * lip * (1.0 + f * 0.22) * 0.85;  // flat on the page it catches more key light than the card
	}
	ROUGHNESS = 0.92;
}
