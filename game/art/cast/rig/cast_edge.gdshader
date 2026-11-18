shader_type spatial;
render_mode cull_back, diffuse_burley, specular_disabled;
// CastPuppet copy of core/shaders/paper_edge.gdshader (2026-11-18 walk v4): the cream cut core is drawn only for card
// local heights band_lo <= y <= band_hi; outside it the edge takes join_color (the garment colour), so the edge wall of a
// puppet JOIN (no-coat trouser seat over the legs, hips piece, shoulder cap of a swinging arm) reads as no seam.
// Cut edge of card stock / ground layers: cream core with fuzzy lips (B_look owns).

uniform vec4 edge_color : source_color = vec4(0.96, 0.92, 0.82, 1.0);
uniform sampler2D fibre_tex : hint_default_white, filter_linear_mipmap, repeat_enable;
uniform float brightness = 1.08;  // the core catches light: a touch brighter than the stock
uniform float band_lo = -100.0;
uniform float band_hi = 100.0;
uniform vec4 join_color : source_color = vec4(0.3, 0.15, 0.08, 1.0);
varying float ly;

void vertex() {
	ly = VERTEX.y;
}

void fragment() {
	// UV.x runs along the cut in world units, UV.y across the thickness.
	float f = texture(fibre_tex, vec2(UV.x * 9.0, UV.y * 0.08 + UV.x * 0.3)).r - 0.5;
	float lip = smoothstep(0.0, 0.25, UV.y) * smoothstep(1.0, 0.75, UV.y);
	ALBEDO = edge_color.rgb * brightness * (0.93 + f * 0.14) * mix(0.86, 1.0, lip);
	if (ly < band_lo || ly > band_hi) {
		ALBEDO = join_color.rgb;
	}
	ROUGHNESS = 1.0;
	SPECULAR = 0.05;
	BACKLIGHT = edge_color.rgb * 0.25;
}
