shader_type spatial;
render_mode cull_back, diffuse_burley, specular_schlick_ggx, world_vertex_coords;
// Batched cut-paper card (component F, perf): core/shaders/paper_print.gdshader (print face + printed back) and
// core/shaders/paper_edge.gdshader (cut walls) in ONE surface and ONE material for every card print, so a print's
// MultiMesh is one draw. The prints live in an atlas (CardAtlas: Texture2DArray pages, same texels, wrap-padded so
// sampling matches the original repeat sampler); per-print values (atlas rect, card size, edge colour) come from a
// params texture indexed by UV2.y; UV2.x = part (0 print face, 1 back, 2 cut wall). INSTANCE_CUSTOM.x = k scales
// card_size / wall UV for cards built at another height than the print mesh (hinged cards). The fragment code is a
// line-by-line port of the two original shaders: keep it in step with them.
#include "res://core/world/shaders/card_wind.gdshaderinc"

uniform sampler2DArray atlas : source_color, filter_linear_mipmap_anisotropic, repeat_disable;
uniform sampler2D params : filter_nearest, repeat_disable;
uniform sampler2D fibre_tex : hint_default_white, filter_linear_mipmap, repeat_enable;
uniform float fibre_density = 7.0;
uniform float fibre_strength = 0.16;
uniform float translucency = 0.32;
uniform float rim_width = 0.0024;
uniform float rim_mix = 0.35;
uniform vec4 rim_color : source_color = vec4(0.97, 0.92, 0.80, 1.0);
uniform float foot_ao_height = 0.06;
uniform float foot_ao_strength = 0.42;
uniform float ink_saturation = 1.12;
uniform float ink_contrast = 1.06;
uniform float edge_brightness = 1.08;

// Flat varyings kept to the minimum (every vertex output costs memory traffic on tile-based GPUs): print index,
// part and k; the per-print values are fetched in the fragment shader.
varying flat int v_part;
varying flat int v_idx;
varying flat float v_k;

void vertex() {
	v_idx = int(UV2.y + 0.5);
	v_part = int(UV2.x + 0.5);
	v_k = INSTANCE_CUSTOM.x;
	if (INSTANCE_CUSTOM.y > 0.0) {
		vec3 o = MODEL_MATRIX[3].xyz;
		mat3 r = card_sway(INSTANCE_CUSTOM, o);
		VERTEX = o + r * (VERTEX - o);
		NORMAL = r * NORMAL;
		TANGENT = r * TANGENT;
		BINORMAL = r * BINORMAL;
	}
}

float alpha_at(vec2 uv, vec4 rect, float layer) {
	return textureLod(atlas, vec3(rect.xy + fract(uv) * rect.zw, layer), 0.0).a;
}

void fragment() {
	// Derivatives first (uniform control flow): the original shaders took them implicitly.
	vec2 dux = dFdx(UV);
	vec2 duy = dFdy(UV);
	vec4 v_rect = texelFetch(params, ivec2(v_idx, 0), 0);
	vec4 p1 = texelFetch(params, ivec2(v_idx, 1), 0);
	float v_layer = p1.x;
	vec2 v_size = p1.yz * v_k;
	if (v_part == 2) {
		vec3 v_edge = texelFetch(params, ivec2(v_idx, 2), 0).rgb;
		// paper_edge.gdshader. UV.x runs along the cut in world units, UV.y across the thickness.
		vec2 euv = vec2(UV.x * v_k * 9.0, UV.y * 0.08 + UV.x * v_k * 0.3);
		vec2 edx = vec2(dux.x * v_k * 9.0, dux.y * 0.08 + dux.x * v_k * 0.3);
		vec2 edy = vec2(duy.x * v_k * 9.0, duy.y * 0.08 + duy.x * v_k * 0.3);
		float f = textureGrad(fibre_tex, euv, edx, edy).r - 0.5;
		float lip = smoothstep(0.0, 0.25, UV.y) * smoothstep(1.0, 0.75, UV.y);
		ALBEDO = v_edge * edge_brightness * (0.93 + f * 0.14) * mix(0.86, 1.0, lip);
		ROUGHNESS = 1.0;
		SPECULAR = 0.05;
		BACKLIGHT = v_edge * 0.25;
	} else {
		// paper_print.gdshader with plain = false (meadow cards print both faces).
		vec4 c = textureGrad(atlas, vec3(v_rect.xy + fract(UV) * v_rect.zw, v_layer), dux * v_rect.zw, duy * v_rect.zw);
		if (c.a < 0.5) discard;
		vec3 col = c.rgb;
		float l = dot(col, vec3(0.299, 0.587, 0.114));
		col = mix(vec3(l), col, ink_saturation);
		col = clamp((col - 0.5) * ink_contrast + 0.5, 0.0, 1.0);
		float rw = rim_width * clamp(v_size.y / 0.35, 0.45, 1.0);
		vec2 r = vec2(rw) / max(v_size, vec2(0.01));
		float m = 1.0;
		m = min(m, alpha_at(UV + vec2(r.x, 0.0), v_rect, v_layer));
		m = min(m, alpha_at(UV - vec2(r.x, 0.0), v_rect, v_layer));
		m = min(m, alpha_at(UV + vec2(0.0, r.y), v_rect, v_layer));
		m = min(m, alpha_at(UV - vec2(0.0, r.y), v_rect, v_layer));
		m = min(m, alpha_at(UV + r * 0.7071, v_rect, v_layer));
		m = min(m, alpha_at(UV - r * 0.7071, v_rect, v_layer));
		m = min(m, alpha_at(UV + vec2(r.x, -r.y) * 0.7071, v_rect, v_layer));
		m = min(m, alpha_at(UV + vec2(-r.x, r.y) * 0.7071, v_rect, v_layer));
		float not_bottom = step(UV.y, 0.985);
		col = mix(col, rim_color.rgb, (1.0 - smoothstep(0.25, 0.6, m)) * not_bottom * rim_mix);
		vec2 fs = v_size * fibre_density;
		vec2 fuv = UV * fs;
		float f = textureGrad(fibre_tex, fuv, dux * fs, duy * fs).r;
		float f2 = textureGrad(fibre_tex, fuv * 2.7 + 0.31, dux * fs * 2.7, duy * fs * 2.7).r;
		float fibre = mix(f, f2, 0.4) - 0.5;
		float h = (1.0 - UV.y) * v_size.y;
		float ao = mix(1.0 - foot_ao_strength, 1.0, smoothstep(0.0, foot_ao_height, h));
		ALBEDO = col * (1.0 + fibre * fibre_strength * 2.0) * ao;
		ROUGHNESS = 0.74 - fibre * 0.2;
		SPECULAR = 0.22;
		NORMAL_MAP = normalize(vec3(0.5 + fibre * 0.35, 0.5 - fibre * 0.25, 1.0));
		NORMAL_MAP_DEPTH = 0.6;
		BACKLIGHT = col * translucency;
	}
}
