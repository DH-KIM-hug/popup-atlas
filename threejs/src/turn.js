// PageTurn (game/story/page_turn.gd) as one full-screen pass over the rendered page, per pixel:
//   the fold line sweeps right -> left and leans a little (a hand lifts the bottom corner first);
//   left of the mirrored back edge: the old page still lying (a snapshot, or the live page underneath);
//   between the back edge and the fold: the back of the turned sheet (cream paper, lighter at its free edge, shaded
//   into the fold, the old print faintly showing through mirrored), a fold highlight and an edge line;
//   right of the fold: the new page (the next page's live view, or the live page underneath) with the soft shadow of
//   the lifted sheet. Pixel sizes are Godot's (1024 px tall), scaled by `gscale`.
import * as THREE from 'three';

const frag = /* glsl */ `
precision highp float;
in vec2 vUv;
out vec4 outColor;
uniform sampler2D tOld, tNew;
uniform float hasOld, hasNew, progress, gscale;
uniform vec2 size;
const vec3 PAPER = vec3(0.937, 0.890, 0.784);
const vec3 SHADE = vec3(0.804, 0.733, 0.588);
const vec4 SHADOW = vec4(0.08, 0.05, 0.02, 0.45);
void main() {
  float W = size.x, H = size.y;
  float x = vUv.x * W, y = (1.0 - vUv.y) * H;
  float f = W * (1.0 - progress);
  float lean = 70.0 * gscale * sin(progress * 3.14159265);
  float fx = mix(f + lean * 0.5, f - lean * 0.5, y / H);     // the fold at this row
  float ax = 2.0 * fx - W;                                     // the mirrored right edge (the sheet's back edge)
  vec2 uv = vec2(vUv.x, vUv.y);
  vec4 c = vec4(0.0);
  float bx = max(ax, 0.0);
  if (x < bx) {
    // the back casts a shadow onto the lying old page
    float s = smoothstep(bx - 26.0 * gscale, bx, x) * 0.3 * step(1.0, bx);
    if (hasOld > 0.5) c = vec4(mix(texture(tOld, uv).rgb, SHADOW.rgb, s), 1.0);
    else c = vec4(SHADOW.rgb, s);
  } else if (x < fx) {
    float k = clamp((x - bx) / max(fx - bx, 1.0), 0.0, 1.0);
    vec3 lit = mix(PAPER, vec3(1.0), 0.06);
    vec3 col = mix(lit, SHADE, k);
    if (hasOld > 0.5) {
      vec2 m = vec2((2.0 * fx - x) / W, uv.y);  // mirrored across the fold
      if (m.x <= 1.0) col = mix(col, texture(tOld, m).rgb, 0.07);
    }
    c = vec4(col, 1.0);
    float hl = 1.0 - smoothstep(0.0, 2.0 * gscale, abs(x - fx));
    c.rgb = mix(c.rgb, vec3(1.0, 0.97, 0.88), hl * 0.6);
    float el = 1.0 - smoothstep(0.0, 1.5 * gscale, abs(x - bx));
    c.rgb = mix(c.rgb, vec3(0.45, 0.36, 0.25), el * 0.35);
  } else {
    float shw = (30.0 + 110.0 * sin(progress * 3.14159265)) * gscale;
    float s = (1.0 - smoothstep(fx, fx + shw, x)) * SHADOW.a;
    if (hasNew > 0.5) c = vec4(mix(texture(tNew, uv).rgb, SHADOW.rgb, s), 1.0);
    else c = vec4(SHADOW.rgb, s);
  }
  outColor = c;
}`;

const vert = /* glsl */ `
precision highp float;
in vec3 position;
out vec2 vUv;
void main() { vUv = position.xy * 0.5 + 0.5; gl_Position = vec4(position.xy, 0.0, 1.0); }`;

export function makeTurn() {
  const u = {
    tOld: { value: null }, tNew: { value: null }, hasOld: { value: 0 }, hasNew: { value: 0 }, progress: { value: 0 },
    gscale: { value: 1 }, size: { value: new THREE.Vector2(1, 1) },
  };
  const mat = new THREE.RawShaderMaterial({
    glslVersion: THREE.GLSL3, uniforms: u, vertexShader: vert, fragmentShader: frag, depthTest: false, depthWrite: false,
    transparent: true, blending: THREE.NormalBlending, premultipliedAlpha: false,
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
