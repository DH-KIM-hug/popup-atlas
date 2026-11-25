// Ports of the Godot spatial shaders the turnip spread uses, as patched MeshStandardMaterials so they keep three.js
// lights + PCF shadows. Each port keeps the Godot uniform names and defaults (game/core/shaders/*.gdshader,
// game/core/world/shaders/*.gdshader). Godot UVs are used as-is (v down) with textures uploaded un-flipped.
import * as THREE from 'three';

// uniforms declared `source_color` in Godot: sRGB values in the dump -> linear here
const SRGB_UNIFORMS = new Set(['rim_color', 'plain_color', 'glow_color', 'base_color', 'mottle_color', 'speckle_color',
  'tint', 'edge_color', 'albedo_color']);

export function linearColor(arr) {
  return new THREE.Color().setRGB(arr[0], arr[1], arr[2], THREE.SRGBColorSpace);
}

// shared per-frame uniforms (wind, key light direction for paper translucency)
export const shared = {
  time: { value: 0 },
  wind: { value: new THREE.Vector4(0, 1, 1.4, 0) },
  windAxis: { value: new THREE.Vector3(0.33, 0, 0.94) },
  windDir0: { value: new THREE.Vector2(0.944, -0.33) },
  keyDirView: { value: new THREE.Vector3(0, 1, 0) },
  keyColor: { value: new THREE.Color(1, 1, 1) },
};

const COMMON_PARS = /* glsl */ `
uniform vec3 keyDirView;
uniform vec3 keyColor;
varying vec2 vPUv;
varying vec3 vWPos;
varying float vLocalY;
varying vec4 vGT;  // Godot mesh tangent in view space (w = binormal sign); zero when the mesh has none
// Godot NORMAL_MAP: tangent frame from the mesh tangents (binormal = cross(N, T) * w) like Godot; meshes without
// tangents fall back to a cotangent frame from the UV derivatives
vec3 pPerturb(vec3 n, vec3 viewPos, vec2 uv, vec3 nm, float depth) {
  vec2 mxy = nm.xy * 2.0 - 1.0;
  float mz = sqrt(max(0.0, 1.0 - dot(mxy, mxy)));
  vec3 T, B;
  if (dot(vGT.xyz, vGT.xyz) > 0.25) {
    T = normalize(vGT.xyz - n * dot(n, vGT.xyz));
    // sign measured against Godot frames (turnip close-ups: puppet faces / coats match with -cross(N, T) * w)
    B = -cross(n, T) * (vGT.w < 0.0 ? -1.0 : 1.0);
    return normalize(mix(n, T * mxy.x + B * mxy.y + n * mz, depth));
  }
  vec3 dp1 = dFdx(viewPos); vec3 dp2 = dFdy(viewPos);
  vec2 duv1 = dFdx(uv); vec2 duv2 = dFdy(uv);
  vec3 dp2perp = cross(dp2, n); vec3 dp1perp = cross(n, dp1);
  T = dp2perp * duv1.x + dp1perp * duv2.x;
  B = dp2perp * duv1.y + dp1perp * duv2.y;
  float det = max(dot(T, T), dot(B, B));
  float s = det == 0.0 ? 0.0 : inversesqrt(det);
  // Godot's normal map is +Y up in a v-down UV space
  return normalize(mix(n, T * s * mxy.x - B * s * mxy.y + n * mz, depth));
}
`;

const WIND_PARS = /* glsl */ `
uniform vec4 wind;
uniform vec3 windAxis;
uniform vec2 windDir0;
attribute vec4 iCustom;
mat3 card_axis_rot(vec3 k, float a) {
  float c = cos(a); float s = sin(a); float t = 1.0 - c;
  return mat3(
    vec3(c + k.x * k.x * t, k.y * k.x * t + k.z * s, k.z * k.x * t - k.y * s),
    vec3(k.x * k.y * t - k.z * s, c + k.y * k.y * t, k.z * k.y * t + k.x * s),
    vec3(k.x * k.z * t + k.y * s, k.y * k.z * t - k.x * s, c + k.z * k.z * t));
}
mat3 card_sway(vec4 custom, vec3 origin) {
  float amp = custom.y;
  if (amp <= 0.0) return mat3(1.0);
  float along = dot(origin.xz, windDir0);
  float g = 0.5 + 0.5 * sin((wind.x * wind.z - along) * 0.9);
  g = g * g;
  float a = amp * wind.y * (0.35 + 0.65 * g) * (0.6 + 0.4 * sin(wind.x * custom.z * 6.283185307179586 + custom.w));
  return card_axis_rot(windAxis, a);
}
`;

// world-space sway around the instance origin (card_batch / card_shadow vertex())
const WIND_VERTEX = /* glsl */ `
  mat4 pModel = modelMatrix;
  #ifdef USE_INSTANCING
    pModel = modelMatrix * instanceMatrix;
  #endif
  vec3 pO = pModel[3].xyz;
  mat3 pR = card_sway(iCustom, pO);
  vec4 pW = pModel * vec4(transformed, 1.0);
  pW.xyz = pO + pR * (pW.xyz - pO);
`;

function inject(shader, { uniforms = {}, vertPars = '', vertMain = '', vertProject = null, normalFix = '', fragPars = '',
  map = null, rough = null, normal = null, emissive = null }) {
  Object.assign(shader.uniforms, uniforms, { keyDirView: shared.keyDirView, keyColor: shared.keyColor });
  shader.vertexShader = shader.vertexShader
    .replace('#include <common>', `#include <common>\nvarying vec2 vPUv;\nvarying vec3 vWPos;\nvarying float vLocalY;\nattribute vec4 gTangent;\nvarying vec4 vGT;\n${vertPars}`)
    .replace('#include <begin_vertex>', `#include <begin_vertex>\n vPUv = uv; vLocalY = position.y;
 { mat4 gtM = modelViewMatrix;
   #ifdef USE_INSTANCING
     gtM = modelViewMatrix * instanceMatrix;
   #endif
   mat3 gt3 = mat3(gtM); vGT = vec4(gt3 * gTangent.xyz, gTangent.w * sign(determinant(gt3))); }\n${vertMain}`);
  if (vertProject) {
    shader.vertexShader = shader.vertexShader
      .replace('#include <project_vertex>', vertProject)
      .replace('#include <worldpos_vertex>', 'vec4 worldPosition = pW; vWPos = pW.xyz;');
  } else {
    shader.vertexShader = shader.vertexShader.replace('#include <worldpos_vertex>',
      `#include <worldpos_vertex>\n { vec4 wp4 = modelMatrix * vec4(transformed, 1.0);\n #ifdef USE_INSTANCING\n wp4 = modelMatrix * instanceMatrix * vec4(transformed, 1.0);\n #endif\n vWPos = wp4.xyz; }`);
  }
  if (normalFix) shader.vertexShader = shader.vertexShader.replace('#include <defaultnormal_vertex>', `#include <defaultnormal_vertex>\n${normalFix}`);
  shader.fragmentShader = shader.fragmentShader.replace('#include <common>', `#include <common>\n${COMMON_PARS}\n${fragPars}`);
  if (map) shader.fragmentShader = shader.fragmentShader.replace('#include <map_fragment>', map);
  if (rough) shader.fragmentShader = shader.fragmentShader.replace('#include <roughnessmap_fragment>', rough);
  if (normal) shader.fragmentShader = shader.fragmentShader.replace('#include <normal_fragment_maps>', normal);
  if (emissive) shader.fragmentShader = shader.fragmentShader.replace('#include <emissivemap_fragment>', `#include <emissivemap_fragment>\n${emissive}`);
}

// Godot BACKLIGHT approximation: key light reaching the face from behind, through thin paper
const BACKLIGHT = (expr) => `
  { float bl = max(dot(-normal, keyDirView), 0.0);
    totalEmissiveRadiance += (${expr}) * keyColor * bl * 0.35; }`;

const PRINT_FRAG_PARS = /* glsl */ `
uniform sampler2D albedo_tex;
uniform sampler2D fibre_tex;
uniform vec2 card_size;
uniform float fibre_density, fibre_strength, translucency, rim_width, rim_mix, foot_ao_height, foot_ao_strength;
uniform float ink_saturation, ink_contrast, glow;
uniform bool plain;
uniform vec3 plain_color, rim_color, glow_color;
float alpha_at(vec2 uv) { return textureLod(albedo_tex, uv, 0.0).a; }
float pFibre; vec3 pCol;
`;

function texU(t) { return { value: t }; }

export function printMaterial(p, tex, side) {
  const u = {
    albedo_tex: texU(tex(p.albedo_tex)), fibre_tex: texU(tex(p.fibre_tex)),
    card_size: { value: new THREE.Vector2(...(p.card_size || [0.4, 0.4])) },
    fibre_density: { value: p.fibre_density ?? 7 }, fibre_strength: { value: p.fibre_strength ?? 0.16 },
    translucency: { value: p.translucency ?? 0.32 }, rim_width: { value: p.rim_width ?? 0.0024 },
    rim_mix: { value: p.rim_mix ?? 0.35 }, foot_ao_height: { value: p.foot_ao_height ?? 0.06 },
    foot_ao_strength: { value: p.foot_ao_strength ?? 0.42 }, ink_saturation: { value: p.ink_saturation ?? 1.12 },
    ink_contrast: { value: p.ink_contrast ?? 1.06 }, glow: { value: p.glow ?? 0 }, plain: { value: !!p.plain },
    plain_color: { value: linearColor(p.plain_color || [0.93, 0.89, 0.8]) },
    rim_color: { value: linearColor(p.rim_color || [0.97, 0.92, 0.8]) },
    glow_color: { value: linearColor(p.glow_color || [1, 0.72, 0.36]) },
  };
  const m = new THREE.MeshStandardMaterial({ roughness: 0.74, metalness: 0, side });
  // map + alphaTest so three's shadow pass alpha-tests the cut shape automatically
  if (!p.plain && u.albedo_tex.value) { m.map = u.albedo_tex.value; m.alphaTest = 0.5; }
  m.userData.u = u;
  m.onBeforeCompile = (s) => inject(s, {
    uniforms: u, fragPars: PRINT_FRAG_PARS,
    map: /* glsl */ `
      vec4 c = plain ? vec4(plain_color, 1.0) : texture(albedo_tex, vPUv);
      if (!plain && c.a < 0.5) discard;
      vec3 col = c.rgb;
      if (!plain) {
        float l = dot(col, vec3(0.299, 0.587, 0.114));
        col = mix(vec3(l), col, ink_saturation);
        col = clamp((col - 0.5) * ink_contrast + 0.5, 0.0, 1.0);
        float rw = rim_width * clamp(card_size.y / 0.35, 0.45, 1.0);
        vec2 r = vec2(rw) / max(card_size, vec2(0.01));
        float mm = 1.0;
        mm = min(mm, alpha_at(vPUv + vec2(r.x, 0.0))); mm = min(mm, alpha_at(vPUv - vec2(r.x, 0.0)));
        mm = min(mm, alpha_at(vPUv + vec2(0.0, r.y))); mm = min(mm, alpha_at(vPUv - vec2(0.0, r.y)));
        mm = min(mm, alpha_at(vPUv + r * 0.7071)); mm = min(mm, alpha_at(vPUv - r * 0.7071));
        mm = min(mm, alpha_at(vPUv + vec2(r.x, -r.y) * 0.7071)); mm = min(mm, alpha_at(vPUv + vec2(-r.x, r.y) * 0.7071));
        float not_bottom = step(vPUv.y, 0.985);
        col = mix(col, rim_color, (1.0 - smoothstep(0.25, 0.6, mm)) * not_bottom * rim_mix);
      }
      vec2 fuv = vPUv * card_size * fibre_density;
      float f = texture(fibre_tex, fuv).r;
      float f2 = texture(fibre_tex, fuv * 2.7 + 0.31).r;
      pFibre = mix(f, f2, 0.4) - 0.5;
      float h = (1.0 - vPUv.y) * card_size.y;
      float ao = mix(1.0 - foot_ao_strength, 1.0, smoothstep(0.0, foot_ao_height, h));
      pCol = col;
      diffuseColor.rgb = col * (1.0 + pFibre * fibre_strength * 2.0) * ao;`,
    rough: 'float roughnessFactor = 0.74 - pFibre * 0.2;',
    normal: 'normal = pPerturb(normal, -vViewPosition, vPUv * card_size * fibre_density, normalize(vec3(0.5 + pFibre * 0.35, 0.5 - pFibre * 0.25, 1.0)), 0.6);',
    emissive: BACKLIGHT('pCol * translucency'),
  });
  m.customProgramCacheKey = () => 'print';
  return m;
}

export function edgeMaterial(p, tex, side) {
  const u = {
    edge_color: { value: linearColor(p.edge_color || [0.96, 0.92, 0.82]) },
    fibre_tex: texU(tex(p.fibre_tex)), brightness: { value: p.brightness ?? 1.08 },
  };
  const m = new THREE.MeshStandardMaterial({ roughness: 1, metalness: 0, side });
  m.userData.u = u;
  m.onBeforeCompile = (s) => inject(s, {
    uniforms: u, fragPars: 'uniform vec3 edge_color; uniform sampler2D fibre_tex; uniform float brightness;',
    map: /* glsl */ `
      float f = texture(fibre_tex, vec2(vPUv.x * 9.0, vPUv.y * 0.08 + vPUv.x * 0.3)).r - 0.5;
      float lip = smoothstep(0.0, 0.25, vPUv.y) * smoothstep(1.0, 0.75, vPUv.y);
      diffuseColor.rgb = edge_color * brightness * (0.93 + f * 0.14) * mix(0.86, 1.0, lip);`,
    emissive: BACKLIGHT('edge_color * 0.25'),
  });
  m.customProgramCacheKey = () => 'edge';
  return m;
}

export function houseMaterial(p, tex, side) {
  const u = {
    albedo_tex: texU(tex(p.albedo_tex, true)), fibre_tex: texU(tex(p.fibre_tex)),
    fibre_density: { value: p.fibre_density ?? 7 }, fibre_strength: { value: p.fibre_strength ?? 0.16 },
    shade: { value: p.shade ?? 1 }, ink_saturation: { value: p.ink_saturation ?? 1.12 }, ink_contrast: { value: p.ink_contrast ?? 1.06 },
    foot_ao_height: { value: p.foot_ao_height ?? 0.05 }, foot_ao_strength: { value: p.foot_ao_strength ?? 0.35 },
    translucency: { value: p.translucency ?? 0.12 },
  };
  const m = new THREE.MeshStandardMaterial({ roughness: 0.78, metalness: 0, side });
  m.userData.u = u;
  m.onBeforeCompile = (s) => inject(s, {
    uniforms: u,
    fragPars: 'uniform sampler2D albedo_tex, fibre_tex; uniform float fibre_density, fibre_strength, shade, ink_saturation, ink_contrast, foot_ao_height, foot_ao_strength, translucency; float pFibre; vec3 pCol;',
    map: /* glsl */ `
      vec3 col = texture(albedo_tex, vPUv).rgb;
      float l = dot(col, vec3(0.299, 0.587, 0.114));
      col = mix(vec3(l), col, ink_saturation);
      col = clamp((col - 0.5) * ink_contrast + 0.5, 0.0, 1.0);
      vec2 fuv = vec2(vWPos.x + vWPos.z, vWPos.y) * fibre_density;
      float f = texture(fibre_tex, fuv).r;
      float f2 = texture(fibre_tex, fuv * 2.7 + 0.31).r;
      pFibre = mix(f, f2, 0.4) - 0.5;
      float ao = mix(1.0 - foot_ao_strength, 1.0, smoothstep(0.0, foot_ao_height, vLocalY));
      pCol = col;
      diffuseColor.rgb = col * (1.0 + pFibre * fibre_strength * 2.0) * ao * shade;`,
    rough: 'float roughnessFactor = 0.78 - pFibre * 0.2;',
    normal: 'normal = pPerturb(normal, -vViewPosition, vec2(vWPos.x + vWPos.z, vWPos.y) * fibre_density, normalize(vec3(0.5 + pFibre * 0.35, 0.5 - pFibre * 0.25, 1.0)), 0.5);',
    emissive: BACKLIGHT('pCol * translucency * shade'),
  });
  m.customProgramCacheKey = () => 'house';
  return m;
}

export function groundMaterial(p, tex, side) {
  const u = {
    base_color: { value: linearColor(p.base_color || [0.4, 0.5, 0.25]) },
    mottle_color: { value: linearColor(p.mottle_color || [0.32, 0.42, 0.2]) },
    felt_tex: texU(tex(p.felt_tex)),
    mottle_scale: { value: p.mottle_scale ?? 0.09 }, mottle_strength: { value: p.mottle_strength ?? 0.7 },
    fibre_scale: { value: p.fibre_scale ?? 0.9 }, fibre_strength: { value: p.fibre_strength ?? 0.13 },
    grain_strength: { value: p.grain_strength ?? 0.1 }, bump: { value: p.bump ?? 0.5 },
    clump_strength: { value: p.clump_strength ?? 0 }, clump_scale: { value: p.clump_scale ?? 0.31 },
    speckle: { value: p.speckle ?? 0 }, speckle_color: { value: linearColor(p.speckle_color || [0.55, 0.42, 0.28]) },
    paper: { value: p.paper ?? 0 },
  };
  const m = new THREE.MeshStandardMaterial({ roughness: 0.98, metalness: 0, side });
  m.userData.u = u;
  m.onBeforeCompile = (s) => inject(s, {
    uniforms: u,
    fragPars: `uniform vec3 base_color, mottle_color, speckle_color; uniform sampler2D felt_tex;
      uniform float mottle_scale, mottle_strength, fibre_scale, fibre_strength, grain_strength, bump, clump_strength, clump_scale, speckle, paper;
      float gFib, gFine, gClump, gCs;`,
    map: /* glsl */ `
      vec2 p = vWPos.xz;
      float mott = texture(felt_tex, p * mottle_scale).r - 0.5;
      float mott2 = texture(felt_tex, p * mottle_scale * 2.3 + 0.37).r - 0.5;
      vec2 pw = p + vec2(mott2, mott) * 0.5;
      vec2 pa = vec2(pw.x * 0.81 - pw.y * 0.59, pw.x * 0.59 + pw.y * 0.81);
      vec2 pb = vec2(pw.x * -0.33 - pw.y * 0.94, pw.x * 0.94 - pw.y * 0.33);
      gFib = (texture(felt_tex, pa * fibre_scale).g + texture(felt_tex, pb * fibre_scale * 0.73 + 0.21).g) * 0.5 - 0.5;
      gFib *= 1.25;
      gFine = texture(felt_tex, pb * fibre_scale * 3.1 + 0.11).b - 0.5;
      float ms = mix(mottle_strength, mottle_strength * 0.22, paper);
      float mm = clamp(0.5 + (mott * 1.6 + mott2 * 0.8) * ms, 0.0, 1.0);
      vec3 col = mix(base_color, mottle_color, mm);
      gClump = 0.0;
      gCs = clump_strength * (1.0 - paper);
      if (gCs > 0.0) {
        vec3 ct = texture(felt_tex, pa * clump_scale + 0.63).rgb;
        gClump = ct.g + ct.b - 1.0;
        col *= 1.0 + gClump * gCs;
        col = mix(col, col * vec3(1.06, 1.03, 0.9), clamp(gClump * 2.0, 0.0, 1.0) * gCs);
      }
      float fs = mix(fibre_strength, 0.035, paper);
      float gs = mix(grain_strength, 0.06, paper);
      col *= 1.0 + gFib * fs * 2.0 + gFine * gs * 2.0;
      if (speckle > 0.0) {
        float s1 = texture(felt_tex, p * 5.3).b;
        float s2 = texture(felt_tex, p * 2.1 + 0.5).g;
        float fleck = smoothstep(0.80, 0.86, s1) * smoothstep(0.55, 0.7, s2);
        col = mix(col, speckle_color, fleck * speckle);
      }
      diffuseColor.rgb = col;`,
    rough: 'float roughnessFactor = 0.98;',
    normal: 'normal = pPerturb(normal, -vViewPosition, vWPos.xz, normalize(vec3(0.5 + (gFib + gFine) * 0.4 + gClump * gCs * 0.5, 0.5 + (gFib - gFine) * 0.3 - gClump * gCs * 0.4, 1.0)), mix(bump, 0.25, paper));',
  });
  m.customProgramCacheKey = () => 'ground';
  return m;
}

// card_batch.gdshader: one InstancedMesh per print; the print's atlas page + rect come from the params texture.
export function batchMaterial(p, pr, pageTex, tex) {
  const u = {
    atlas: texU(pageTex), fibre_tex: texU(tex(p.fibre_tex)),
    vRect: { value: new THREE.Vector4(...pr.rect) }, vSize: { value: new THREE.Vector2(pr.size[0], pr.size[1]) },
    vEdge: { value: new THREE.Color(pr.edge[0], pr.edge[1], pr.edge[2]) },
    fibre_density: { value: p.fibre_density ?? 7 }, fibre_strength: { value: p.fibre_strength ?? 0.16 },
    translucency: { value: p.translucency ?? 0.32 }, rim_width: { value: p.rim_width ?? 0.0024 }, rim_mix: { value: p.rim_mix ?? 0.35 },
    rim_color: { value: linearColor(p.rim_color || [0.97, 0.92, 0.8]) },
    foot_ao_height: { value: p.foot_ao_height ?? 0.06 }, foot_ao_strength: { value: p.foot_ao_strength ?? 0.42 },
    ink_saturation: { value: p.ink_saturation ?? 1.12 }, ink_contrast: { value: p.ink_contrast ?? 1.06 },
    edge_brightness: { value: p.edge_brightness ?? 1.08 },
    wind: shared.wind, windAxis: shared.windAxis, windDir0: shared.windDir0,
  };
  const m = new THREE.MeshStandardMaterial({ roughness: 0.74, metalness: 0 });
  m.userData.u = u;
  m.onBeforeCompile = (s) => inject(s, {
    uniforms: u,
    vertPars: WIND_PARS + 'attribute vec2 uv1; varying float vPart; varying float vK;',
    vertMain: 'vPart = uv1.x; vK = iCustom.x;',
    vertProject: WIND_VERTEX + `vec4 mvPosition = viewMatrix * pW; gl_Position = projectionMatrix * mvPosition;`,
    normalFix: `{ mat4 nM = modelMatrix;
      #ifdef USE_INSTANCING
        nM = modelMatrix * instanceMatrix;
      #endif
      mat3 sR = card_sway(iCustom, nM[3].xyz);
      transformedNormal = normalize(mat3(viewMatrix) * sR * transpose(mat3(viewMatrix)) * transformedNormal); }`,
    fragPars: `uniform sampler2D atlas, fibre_tex; uniform vec4 vRect; uniform vec2 vSize; uniform vec3 vEdge, rim_color;
      uniform float fibre_density, fibre_strength, translucency, rim_width, rim_mix, foot_ao_height, foot_ao_strength, ink_saturation, ink_contrast, edge_brightness;
      varying float vPart; varying float vK; float pFibre; vec3 pCol; float pIsEdge;
      float alpha_at(vec2 uv) { return textureLod(atlas, vRect.xy + fract(uv) * vRect.zw, 0.0).a; }`,
    map: /* glsl */ `
      vec2 dux = dFdx(vPUv); vec2 duy = dFdy(vPUv);
      vec2 v_size = vSize * vK;
      pFibre = 0.0; pIsEdge = 0.0;
      if (vPart > 1.5) {
        pIsEdge = 1.0;
        vec2 euv = vec2(vPUv.x * vK * 9.0, vPUv.y * 0.08 + vPUv.x * vK * 0.3);
        float f = texture(fibre_tex, euv).r - 0.5;
        float lip = smoothstep(0.0, 0.25, vPUv.y) * smoothstep(1.0, 0.75, vPUv.y);
        pCol = vEdge * 0.25;
        diffuseColor.rgb = vEdge * edge_brightness * (0.93 + f * 0.14) * mix(0.86, 1.0, lip);
      } else {
        vec4 c = textureGrad(atlas, vRect.xy + fract(vPUv) * vRect.zw, dux * vRect.zw, duy * vRect.zw);
        if (c.a < 0.5) discard;
        vec3 col = c.rgb;
        float l = dot(col, vec3(0.299, 0.587, 0.114));
        col = mix(vec3(l), col, ink_saturation);
        col = clamp((col - 0.5) * ink_contrast + 0.5, 0.0, 1.0);
        float rw = rim_width * clamp(v_size.y / 0.35, 0.45, 1.0);
        vec2 r = vec2(rw) / max(v_size, vec2(0.01));
        float mm = 1.0;
        mm = min(mm, alpha_at(vPUv + vec2(r.x, 0.0))); mm = min(mm, alpha_at(vPUv - vec2(r.x, 0.0)));
        mm = min(mm, alpha_at(vPUv + vec2(0.0, r.y))); mm = min(mm, alpha_at(vPUv - vec2(0.0, r.y)));
        mm = min(mm, alpha_at(vPUv + r * 0.7071)); mm = min(mm, alpha_at(vPUv - r * 0.7071));
        mm = min(mm, alpha_at(vPUv + vec2(r.x, -r.y) * 0.7071)); mm = min(mm, alpha_at(vPUv + vec2(-r.x, r.y) * 0.7071));
        float not_bottom = step(vPUv.y, 0.985);
        col = mix(col, rim_color, (1.0 - smoothstep(0.25, 0.6, mm)) * not_bottom * rim_mix);
        vec2 fs = v_size * fibre_density;
        vec2 fuv = vPUv * fs;
        float f = texture(fibre_tex, fuv).r;
        float f2 = texture(fibre_tex, fuv * 2.7 + 0.31).r;
        pFibre = mix(f, f2, 0.4) - 0.5;
        float h = (1.0 - vPUv.y) * v_size.y;
        float ao = mix(1.0 - foot_ao_strength, 1.0, smoothstep(0.0, foot_ao_height, h));
        pCol = col * translucency;
        diffuseColor.rgb = col * (1.0 + pFibre * fibre_strength * 2.0) * ao;
      }`,
    rough: 'float roughnessFactor = pIsEdge > 0.5 ? 1.0 : 0.74 - pFibre * 0.2;',
    normal: 'if (pIsEdge < 0.5) normal = pPerturb(normal, -vViewPosition, vPUv * vSize * vK * fibre_density, normalize(vec3(0.5 + pFibre * 0.35, 0.5 - pFibre * 0.25, 1.0)), 0.6);',
    emissive: BACKLIGHT('pCol'),
  });
  m.customProgramCacheKey = () => 'batch';
  // shadow caster: same sway + the atlas alpha cut
  const d = new THREE.MeshDepthMaterial({ depthPacking: THREE.RGBADepthPacking });
  d.onBeforeCompile = (s) => {
    Object.assign(s.uniforms, { atlas: u.atlas, vRect: u.vRect, wind: shared.wind, windAxis: shared.windAxis, windDir0: shared.windDir0 });
    s.vertexShader = s.vertexShader
      .replace('#include <common>', '#include <common>\n' + WIND_PARS + 'attribute vec2 uv1; varying vec2 vPUv; varying float vPart;')
      .replace('#include <begin_vertex>', '#include <begin_vertex>\n vPUv = uv; vPart = uv1.x;')
      .replace('#include <project_vertex>', WIND_VERTEX + 'vec4 mvPosition = viewMatrix * pW; gl_Position = projectionMatrix * mvPosition;');
    s.fragmentShader = s.fragmentShader
      .replace('#include <common>', '#include <common>\nuniform sampler2D atlas; uniform vec4 vRect; varying vec2 vPUv; varying float vPart;')
      .replace('#include <alphatest_fragment>', 'if (vPart < 1.5 && texture(atlas, vRect.xy + fract(vPUv) * vRect.zw).a < 0.5) discard;');
  };
  d.customProgramCacheKey = () => 'batchdepth';
  return { m, d };
}

export function contactMaterial(p) {
  const u = { tint: { value: linearColor(p.tint || [0.1, 0.13, 0.07]) }, strength: { value: p.strength ?? 1 } };
  return new THREE.ShaderMaterial({
    uniforms: u, transparent: true, depthWrite: false, side: THREE.DoubleSide,
    vertexShader: /* glsl */ `attribute vec4 iCustom; varying vec2 vUv; varying vec2 cust;
      void main() { vUv = uv; cust = iCustom.xy;
        vec4 p = vec4(position, 1.0);
        #ifdef USE_INSTANCING
          p = instanceMatrix * p;
        #endif
        gl_Position = projectionMatrix * modelViewMatrix * p; }`,
    fragmentShader: /* glsl */ `uniform vec3 tint; uniform float strength; varying vec2 vUv; varying vec2 cust;
      void main() {
        vec2 q = (vUv - 0.5) * 2.0;
        float soft = 1.0 - smoothstep(0.0, 1.0, length(q)); soft *= soft;
        float crease = (1.0 - smoothstep(0.05, 0.16, abs(q.y))) * (1.0 - smoothstep(0.7, 0.95, abs(q.x)));
        float a = clamp((soft * 0.8 + crease * cust.y * 1.3) * cust.x * strength, 0.0, 1.0);
        gl_FragColor = vec4(tint, a * 0.85); }`,
  });
}

export function skirtMaterial(p) {
  const u = { tint: { value: linearColor(p.tint || [0.12, 0.13, 0.06]) }, strength: { value: p.strength ?? 0.55 } };
  return new THREE.ShaderMaterial({
    uniforms: u, transparent: true, depthWrite: false, side: THREE.DoubleSide,
    vertexShader: /* glsl */ `varying float vA; attribute vec4 color;
      void main() { vA = color.a; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }`,
    fragmentShader: /* glsl */ `uniform vec3 tint; uniform float strength; varying float vA;
      void main() { gl_FragColor = vec4(tint, vA * vA * strength); }`,
  });
}

export function standardMaterial(p, tex) {
  const c = p.albedo_color || [1, 1, 1, 1];
  const m = new THREE.MeshStandardMaterial({
    color: linearColor(c), roughness: p.roughness ?? 1, metalness: p.metallic ?? 0,
    map: p.albedo_texture ? tex(p.albedo_texture) : null,
    side: p.cull_mode === 2 ? THREE.DoubleSide : p.cull_mode === 1 ? THREE.BackSide : THREE.FrontSide,
  });
  if (p.transparency === 1 || p.transparency === 4) { m.transparent = true; m.opacity = c[3]; m.depthWrite = p.transparency === 4; }
  if (p.transparency === 2) m.alphaTest = p.alpha_scissor_threshold ?? 0.5;
  if (p.shading_mode === 0) {
    const b = new THREE.MeshBasicMaterial({ color: m.color, map: m.map, transparent: m.transparent, opacity: m.opacity, side: m.side, alphaTest: m.alphaTest });
    return b;
  }
  if (p.vertex_color_use_as_albedo) m.vertexColors = true;
  return m;
}

// Shaders of surfaces at the edge of / outside this shot (book table, page block, stream, paper rocks, bridge planks):
// flat ports with their main colour, enough for the pilot.
export const FLAT = {
  table_wood: (p) => [0.29, 0.17, 0.09],
  page_stack: (p) => p.page_color || [0.93, 0.88, 0.76],
  stream: (p) => [0.2, 0.54, 0.53],
  plank_deck: (p) => p.wood || [0.66, 0.53, 0.37],
  folded_rock: (p) => (p.base_color || [0.56, 0.6, 0.53]).map((c, i) => (i < 3 ? c * (p.value ?? 0.78) : c)),
};
export function flatMaterial(name, p) {
  const c = FLAT[name](p);
  return new THREE.MeshStandardMaterial({ color: linearColor(c), roughness: 0.95, metalness: 0,
    side: name === 'folded_rock' ? THREE.DoubleSide : THREE.FrontSide });
}

// cover_book.gdshader (game/story/cover_book.gd): the book on the table, one shader with a mode switch:
// 0 printed board (art), 1 page block fore-edge lines, 2 endpaper motif, 3 wooden table planks, 4 plain paper / cloth.
const NOISE_GLSL = /* glsl */ `
float cbH21(vec2 p) { return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453); }
float cbNoise(vec2 p) { vec2 i = floor(p); vec2 f = fract(p); f = f * f * (3.0 - 2.0 * f);
  return mix(mix(cbH21(i), cbH21(i + vec2(1, 0)), f.x), mix(cbH21(i + vec2(0, 1)), cbH21(i + vec2(1, 1)), f.x), f.y); }
float cbFbm(vec2 p) { float a = 0.5; float s = 0.0; for (int i = 0; i < 4; i++) { s += a * cbNoise(p); p *= 2.03; a *= 0.5; } return s; }`;
export function coverBookMaterial(p, tex) {
  const u = {
    cbMode: { value: p.mode ?? 0 }, cbTex: texU(p.tex ? tex(p.tex) : null), cbHasTex: { value: p.tex ? 1 : 0 },
    tint: { value: linearColor(p.tint || [1, 1, 1, 1]) }, tint2: { value: linearColor(p.tint2 || [0.8, 0.7, 0.5, 1]) },
    lines: { value: p.lines ?? 220 }, motif: { value: p.motif ?? 9 }, roughness_v: { value: p.roughness_v ?? 0.88 },
    uv_rect: { value: new THREE.Vector4(...(p.uv_rect || [0, 0, 1, 1])) },
  };
  const m = new THREE.MeshStandardMaterial({ roughness: 0.88, metalness: 0 });
  m.userData.u = u;
  m.onBeforeCompile = (s) => inject(s, {
    uniforms: u,
    fragPars: `uniform int cbMode; uniform sampler2D cbTex; uniform float cbHasTex; uniform vec3 tint, tint2;
      uniform float lines, motif, roughness_v; uniform vec4 uv_rect; float cbRough; ${NOISE_GLSL}`,
    map: /* glsl */ `
      vec2 UV = vPUv; vec3 c = tint; cbRough = roughness_v;
      float fib = cbFbm(UV * vec2(520.0, 360.0)) - 0.5;
      if (cbMode == 0) {
        c = (cbHasTex > 0.5 ? texture(cbTex, uv_rect.xy + UV * uv_rect.zw).rgb : vec3(1.0)) * tint;
        c *= 1.0 + fib * 0.05; cbRough = 0.74;
      } else if (cbMode == 1) {
        float v = UV.y * lines; float l = smoothstep(0.35, 0.5, abs(fract(v) - 0.5));
        float n = cbNoise(vec2(UV.x * 40.0, floor(v))) * 0.06;
        c = tint * (0.93 + 0.07 * (1.0 - l) - n);
      } else if (cbMode == 2) {
        vec2 q = UV * vec2(motif, motif * 0.66); vec2 cell = floor(q); vec2 f = fract(q) - 0.5;
        f.x += (mod(cell.y, 2.0) - 0.5) * 0.5; f = fract(f + 0.5) - 0.5;
        float star = smoothstep(0.17, 0.14, length(f) + 0.06 * sin(atan(f.y, f.x) * 5.0));
        c = mix(tint, tint2, star * 0.85); c *= 1.0 + fib * 0.08;
      } else if (cbMode == 3) {
        vec2 p = UV * 13.0; float plank = floor(p.y / 0.34); float py = fract(p.y / 0.34);
        float off = cbH21(vec2(plank, 3.0)) * 10.0;
        float g = cbFbm(vec2((p.x + off) * 0.9, p.y * 22.0 + plank * 7.0));
        float rings = sin((p.y * 30.0 + g * 6.0 + off)) * 0.5 + 0.5;
        vec3 base = mix(tint, tint2, cbH21(vec2(plank, 9.0)) * 0.5 + g * 0.5);
        c = base * (0.86 + 0.14 * rings);
        float seam = smoothstep(0.0, 0.025, py) * smoothstep(1.0, 0.975, py);
        c *= mix(0.55, 1.0, seam); cbRough = 0.62 + 0.2 * g;
      } else { c *= 1.0 + fib * 0.07; }
      diffuseColor.rgb = c;`,
    rough: 'float roughnessFactor = cbRough;',
  });
  m.customProgramCacheKey = () => 'coverbook';
  return m;
}
