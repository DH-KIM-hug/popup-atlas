// Final screen pass: one full-screen triangle that does what Godot does after the 3D pass, in Godot's order:
//   depth fog (Environment FOG_MODE_DEPTH) -> camera DOF (CameraAttributesPractical near/far) -> glow -> exposure +
//   AgX tonemap -> sRGB -> Environment adjustments -> post_grade.gdshader (tilt-shift band, split-tone grade,
//   vignette, grain).
// Blur = mip LOD of the scene colour target (like post_grade's hint_screen_texture mip sampling), so DOF and tilt-shift
// cost 5 texture taps per pixel and no extra passes.
import * as THREE from 'three';

const vert = /* glsl */ `
precision highp float;
in vec3 position;
out vec2 vUv;
void main() { vUv = position.xy * 0.5 + 0.5; gl_Position = vec4(position.xy, 0.0, 1.0); }`;

const frag = /* glsl */ `
precision highp float;
in vec2 vUv;
out vec4 outColor;
uniform sampler2D tColor;
uniform sampler2D tDepth;
uniform vec2 px;            // 1 / render size
uniform float cNear, cFar;
uniform vec2 tanHalf;      // tan(fov/2) * (aspect, 1): view ray for the fog distance
uniform float time;
// fog
uniform float fogOn, fogBegin, fogEnd, fogDensity, fogCurve;
uniform vec3 fogColor;      // linear, * energy
// dof (world units along view z)
uniform vec4 dofFar;        // enabled, distance, transition, -
uniform vec4 dofNear;       // enabled, distance, transition, amount
uniform float dofScale;     // pixels of blur radius per unit amount at 1024 px height
// glow
uniform vec3 glow;          // intensity, bloom, threshold
// tonemap + adjustments
uniform float exposure;
uniform float agxK;         // Godot 4.5+ tonemap_agx_contrast (log-space contrast around mid grey)
uniform vec3 adjust;        // brightness, contrast, saturation
// post_grade
uniform float focus_y, band_half, band_soft, max_lod, base_lod, top_bias, vignette, grade, saturation, contrast, lift, grain, toe;
uniform vec3 shadow_tint, highlight_tint;
uniform float postOn;

float viewZ(float d) {
  float z = d * 2.0 - 1.0;
  return (2.0 * cNear * cFar) / (cFar + cNear - z * (cFar - cNear));
}

vec3 sample_blur(vec2 uv, float lod) {
  if (lod < 0.02) return textureLod(tColor, uv, 0.0).rgb;
  vec2 o = px * exp2(lod) * 0.6;
  vec3 c = textureLod(tColor, uv, lod).rgb * 0.36;
  c += textureLod(tColor, uv + vec2(o.x, o.y), lod).rgb * 0.16;
  c += textureLod(tColor, uv + vec2(-o.x, o.y), lod).rgb * 0.16;
  c += textureLod(tColor, uv + vec2(o.x, -o.y), lod).rgb * 0.16;
  c += textureLod(tColor, uv + vec2(-o.x, -o.y), lod).rgb * 0.16;
  return c;
}

// three.js AgX (Filament / Blender), same curve family as Godot 4 TONE_MAPPER_AGX
vec3 agxContrast(vec3 x) {
  vec3 x2 = x * x; vec3 x4 = x2 * x2;
  return 15.5 * x4 * x2 - 40.14 * x4 * x + 31.96 * x4 - 6.868 * x2 * x + 0.4298 * x2 + 0.1191 * x - 0.00232;
}
vec3 agx(vec3 color) {
  const mat3 toRec2020 = mat3(vec3(0.6274, 0.0691, 0.0164), vec3(0.3293, 0.9195, 0.0880), vec3(0.0433, 0.0113, 0.8956));
  const mat3 fromRec2020 = mat3(vec3(1.6605, -0.1246, -0.0182), vec3(-0.5876, 1.1329, -0.1006), vec3(-0.0728, -0.0083, 1.1187));
  const mat3 inset = mat3(vec3(0.856627153315983, 0.137318972929847, 0.11189821299995),
    vec3(0.0951212405381588, 0.761241990602591, 0.0767994186031903), vec3(0.0482516061458583, 0.101439036467562, 0.811302368396859));
  const mat3 outset = mat3(vec3(1.1271005818144368, -0.1413297634984383, -0.14132976349843826),
    vec3(-0.11060664309660323, 1.157823702216272, -0.11060664309660294), vec3(-0.016493938717834573, -0.016493938717834257, 1.2519364065950405));
  const float minEv = -12.47393; const float maxEv = 4.026069;
  color = toRec2020 * color;
  color = inset * color;
  color = log2(max(color, 1e-10));
  color = clamp((color - minEv) / (maxEv - minEv), 0.0, 1.0);
  color = clamp(0.6060606 + (color - 0.6060606) * agxK, 0.0, 1.0);
  color = agxContrast(color);
  color = outset * color;
  color = pow(max(vec3(0.0), color), vec3(2.2));
  color = fromRec2020 * color;
  return clamp(color, 0.0, 1.0);
}
vec3 toSRGB(vec3 c) {
  return mix(c * 12.92, 1.055 * pow(c, vec3(1.0 / 2.4)) - 0.055, step(vec3(0.0031308), c));
}

void main() {
  vec2 uv = vUv;
  float d = texture(tDepth, uv).r;
  float z = viewZ(d);
  bool sky = d >= 0.99999;
  // camera DOF -> blur radius in px (at a 1024 px tall frame) -> mip lod
  float coc = 0.0;
  if (!sky) {
    if (dofFar.x > 0.5) coc = max(coc, smoothstep(dofFar.y, dofFar.y + dofFar.z, z));
    if (dofNear.x > 0.5) coc = max(coc, 1.0 - smoothstep(max(dofNear.y - dofNear.z, 0.0), dofNear.y, z));
  } else if (dofFar.x > 0.5) coc = 1.0;
  float hScale = 1.0 / (px.y * 1024.0);
  float rpx = coc * dofNear.w * dofScale * hScale;
  float dofLod = rpx > 0.6 ? log2(rpx) + 0.6 : 0.0;
  // post_grade tilt-shift band (screen y, 0 at top)
  float sy = 1.0 - uv.y;
  float dy = sy - focus_y;
  float dd = max(abs(dy) - band_half, 0.0) / band_soft;
  float tiltLod = postOn > 0.5 ? base_lod + clamp(dd, 0.0, 1.0) * max_lod * (dy < 0.0 ? top_bias : 1.0) : 0.0;
  // the post pass blurs at the 1024-tall reference resolution: scale lods to this render size
  float lodScale = log2(max(hScale, 1.0));
  float lod = max(dofLod, tiltLod > 0.02 ? tiltLod + lodScale : 0.0);
  vec3 c = sample_blur(uv, lod);
  // depth fog
  if (fogOn > 0.5 && !sky) {
    // Godot 4 scene shader: fog_z = smoothstep(begin, end, length(vertex)); amount = pow(fog_z, curve) * density
    float dist = z * length(vec3((uv * 2.0 - 1.0) * tanHalf, 1.0));
    float f = pow(smoothstep(fogBegin, fogEnd, dist), fogCurve) * fogDensity;
    c = mix(c, fogColor, clamp(f, 0.0, 1.0));
  }
  // glow (cheap: a wide mip of what exceeds the threshold)
  if (glow.x > 0.0) {
    vec3 g = textureLod(tColor, uv, 5.0 + lodScale).rgb;
    c += max(g - glow.z, 0.0) * glow.x + g * glow.y;
  }
  c = agx(c * exposure);
  c = toSRGB(c);
  // Environment adjustments
  c *= adjust.x;
  c = mix(vec3(0.5), c, adjust.y);
  c = mix(vec3(dot(c, vec3(0.2126, 0.7152, 0.0722))), c, adjust.z);
  if (postOn > 0.5) {
    float l = dot(c, vec3(0.2126, 0.7152, 0.0722));
    vec3 g = c * mix(shadow_tint * 2.0 + 0.68, highlight_tint, smoothstep(0.05, 0.75, l));
    g = mix(vec3(l), g, saturation);
    g = (g - 0.45) * contrast + 0.45 + lift;
    g = mix(g, g * smoothstep(0.0, 0.35, l + 0.08), toe);
    c = mix(c, g, grade);
    if (grain > 0.0) {
      vec2 gp = floor(gl_FragCoord.xy * 0.75);
      float n = fract(sin(dot(gp, vec2(12.9898, 78.233)) + time * 7.0) * 43758.5453) - 0.5;
      c += n * grain * (0.6 + 0.8 * (1.0 - l));
    }
    vec2 v = uv - 0.5;
    float vig = 1.0 - vignette * smoothstep(0.25, 0.85, dot(v * vec2(1.1, 1.0), v * vec2(1.1, 1.0)) * 2.2);
    c *= vig;
  }
  outColor = vec4(max(c, 0.0), 1.0);
}`;

export function makePost() {
  const u = {
    tColor: { value: null }, tDepth: { value: null }, px: { value: new THREE.Vector2() },
    cNear: { value: 0.1 }, cFar: { value: 80 }, tanHalf: { value: new THREE.Vector2(1, 1) }, time: { value: 0 },
    fogOn: { value: 0 }, fogBegin: { value: 10 }, fogEnd: { value: 24 }, fogDensity: { value: 0.45 }, fogCurve: { value: 1.6 },
    fogColor: { value: new THREE.Color() },
    dofFar: { value: new THREE.Vector4() }, dofNear: { value: new THREE.Vector4() }, dofScale: { value: 160 },
    glow: { value: new THREE.Vector3(0.35, 0.03, 0.9) },
    exposure: { value: 0.8 }, agxK: { value: 1.0 }, adjust: { value: new THREE.Vector3(1, 1, 1) },
    focus_y: { value: 0.55 }, band_half: { value: 0.17 }, band_soft: { value: 0.32 }, max_lod: { value: 3.2 },
    base_lod: { value: 0 }, top_bias: { value: 1 }, vignette: { value: 0.38 }, grade: { value: 1 }, saturation: { value: 1 },
    contrast: { value: 1 }, lift: { value: 0.012 }, grain: { value: 0 }, toe: { value: 0 },
    shadow_tint: { value: new THREE.Vector3(0.15, 0.165, 0.12) }, highlight_tint: { value: new THREE.Vector3(1.0, 0.95, 0.84) },
    postOn: { value: 1 },
  };
  const mat = new THREE.RawShaderMaterial({
    glslVersion: THREE.GLSL3, uniforms: u, vertexShader: vert, fragmentShader: frag, depthTest: false, depthWrite: false,
  });
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.BufferAttribute(new Float32Array([-1, -1, 0, 3, -1, 0, -1, 3, 0]), 3));
  const quad = new THREE.Mesh(geo, mat);
  quad.frustumCulled = false;
  const scene = new THREE.Scene();
  scene.add(quad);
  const cam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
  return { u, mat, scene, cam };
}
