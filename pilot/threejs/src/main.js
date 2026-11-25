// 「커다란 순무」 spring beat in three.js, from the Godot dump (tools/threejs_pilot/export_scene.gd).
// The dump holds the meshes, prints, materials and a 30 fps recording of what changed each frame (camera, puppet
// frames, transforms, audio, captions, tap target). This file rebuilds the scene and replays it; the tap on the seed
// is live (the timeline waits there exactly like the Godot runner's tap_steps).
import * as THREE from 'three';
import { makePost } from './post.js';
import { AudioPlayer } from './audio.js';
import * as M from './materials.js';

const Q = new URLSearchParams(location.search);
const DATA = './data/turnip_seed/';
const DPR = Math.min(window.devicePixelRatio || 1, Number(Q.get('dpr') || 2));
const SHADOW = Number(Q.get('shadow') || 2048);
const MSAA = Number(Q.get('msaa') ?? 4);
const AUTO = Q.has('auto');
const TUNE = { dof: Number(Q.get('dof') || 64), fog: Number(Q.get('fog') ?? 1), amb: Number(Q.get('amb') ?? 0.75), key: Number(Q.get('key') ?? 1), glow: Number(Q.get('glow') ?? 1), agx: Number(Q.get('agx') ?? 1.4), omni: Number(Q.get('omni') ?? 1) }; // tests: no start overlay, the tap is simulated after 1 s (like Godot autoplay)
const T0 = performance.now();

const $ = (id) => document.getElementById(id);
const metrics = window.__pilot = { ready: false, loadMs: 0, bytes: {}, frames: [], info: null, gpuMB: 0, errors: [], t: 0, state: 'loading' };
window.addEventListener('error', (e) => metrics.errors.push(String(e.message)));

// ------------------------------------------------------------------ renderer
const canvas = $('c');
const renderer = new THREE.WebGLRenderer({ canvas, antialias: false, powerPreference: 'high-performance', stencil: false });
renderer.setPixelRatio(DPR);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFShadowMap;
renderer.outputColorSpace = THREE.LinearSRGBColorSpace; // the post pass writes display values itself
renderer.toneMapping = THREE.NoToneMapping;
renderer.info.autoReset = false; // one frame = scene + shadow + post renders
const maxAniso = Math.min(4, renderer.capabilities.getMaxAnisotropy());

const scene = new THREE.Scene();
const camera = new THREE.PerspectiveCamera(20, 1, 0.1, 80);
const ambient = new THREE.AmbientLight(0xffffff, 1);
scene.add(ambient);
const post = makePost();
post.u.dofScale.value = TUNE.dof;
post.u.agxK.value = TUNE.agx;
let rt = null;

function resize() {
  const w = window.innerWidth, h = window.innerHeight;
  renderer.setSize(w, h, false);
  canvas.style.width = w + 'px';
  canvas.style.height = h + 'px';
  camera.aspect = w / h;
  camera.updateProjectionMatrix();
  const W = Math.round(w * DPR), H = Math.round(h * DPR);
  if (rt) { rt.depthTexture.dispose(); rt.dispose(); }
  rt = new THREE.WebGLRenderTarget(W, H, {
    type: THREE.HalfFloatType, samples: MSAA, generateMipmaps: true,
    minFilter: THREE.LinearMipmapLinearFilter, magFilter: THREE.LinearFilter, colorSpace: THREE.LinearSRGBColorSpace,
  });
  rt.depthTexture = new THREE.DepthTexture(W, H);
  rt.depthTexture.type = THREE.UnsignedIntType;
  post.u.tColor.value = rt.texture;
  post.u.tDepth.value = rt.depthTexture;
  post.u.px.value.set(1 / W, 1 / H);
}

// ------------------------------------------------------------------ loading
async function fetchBuf(url, kind) {
  const r = await fetch(url);
  if (!(r.ok || r.status === 0)) throw new Error(url + ' ' + r.status);
  const b = await r.arrayBuffer();
  metrics.bytes[kind] = (metrics.bytes[kind] || 0) + b.byteLength;
  return b;
}

let D, BIN;
const texCache = new Map();
const imgLoads = [];
let texBytes = 0;

function setProgress(s) { const el = $('load'); if (el) el.textContent = s; }

function imageTexture(url, repeat) {
  const key = url + (repeat ? '#r' : '');
  if (texCache.has(key)) return texCache.get(key);
  const t = new THREE.Texture();
  t.flipY = false;
  t.colorSpace = THREE.SRGBColorSpace;
  t.anisotropy = maxAniso;
  t.wrapS = t.wrapT = repeat ? THREE.RepeatWrapping : THREE.ClampToEdgeWrapping;
  t.minFilter = THREE.LinearMipmapLinearFilter;
  texCache.set(key, t);
  const base = texCache.get('src:' + url);
  if (base) { t.source = base.source; t.needsUpdate = true; return t; }
  texCache.set('src:' + url, t);
  imgLoads.push(fetchBuf(url, 'tex').then((b) => createImageBitmap(new Blob([b]), { premultiplyAlpha: 'none', colorSpaceConversion: 'none' }))
    .then((bmp) => {
      t.image = bmp; t.needsUpdate = true;
      texBytes += bmp.width * bmp.height * 4 * 1.33;
      for (const [k, o] of texCache) if (o !== t && o.source === t.source) o.needsUpdate = true;
    }));
  return t;
}

const LINEAR_TEX = /paper_fibre|felt|noise|grain/i;
function texById(id, repeat = false) {
  const e = D.textures[id];
  if (!e) return null;
  if (e.web) {
    const t = imageTexture(DATA + e.web, repeat || LINEAR_TEX.test(e.res || ''));
    if (LINEAR_TEX.test(e.res || '')) { t.colorSpace = THREE.NoColorSpace; t.wrapS = t.wrapT = THREE.RepeatWrapping; }
    return t;
  }
  if (e.file) return imageTexture(DATA + e.file, repeat);
  return null;
}
const texParam = (p, repeat) => (p && typeof p === 'object' && 'tex' in p ? texById(p.tex, repeat) : null);

function floatImage(id) {
  const e = D.textures[id];
  const f = e.file && e.file.float ? e.file : null;
  if (!f) return null;
  return { w: f.w, h: f.h, data: new Float32Array(BIN, f.float[0], f.float[1] / 4) };
}

// ------------------------------------------------------------------ geometry + materials
const geoCache = new Map();
function surfaceGeometry(meshId, si) {
  const key = meshId + ':' + si;
  if (geoCache.has(key)) return geoCache.get(key);
  const s = D.meshes[meshId].surfaces[si];
  const g = new THREE.BufferGeometry();
  const A = s.attrs;
  const f32 = (r, n) => new THREE.BufferAttribute(new Float32Array(BIN, r[0], r[1] / 4), n);
  g.setAttribute('position', f32(A.position, 3));
  if (A.normal) g.setAttribute('normal', f32(A.normal, 3)); else g.computeVertexNormals();
  if (A.uv) g.setAttribute('uv', f32(A.uv, 2)); else g.setAttribute('uv', new THREE.BufferAttribute(new Float32Array(s.count * 2), 2));
  if (A.uv2) g.setAttribute('uv1', f32(A.uv2, 2));
  if (A.color) g.setAttribute('color', f32(A.color, 4));
  if (s.index) g.setIndex(new THREE.BufferAttribute(new Uint32Array(BIN, s.index[0], s.index[1] / 4), 1));
  g.computeBoundingSphere();
  geoCache.set(key, g);
  return g;
}

const matCache = new Map();
const unknownShaders = new Set();
function shaderName(e) { return e && e.shader ? e.shader.split('/').pop().replace('.gdshader', '') : ''; }

function material(id) {
  if (id < 0) return null;
  if (matCache.has(id)) return matCache.get(id);
  const e = D.materials[id];
  const p = e.params || {};
  const tex = texParam;
  let m;
  const sh = shaderName(e);
  if (sh === 'paper_print') m = M.printMaterial(p, tex, THREE.FrontSide);
  else if (sh === 'paper_edge') m = M.edgeMaterial(p, tex, THREE.FrontSide);
  else if (sh === 'house_body') m = M.houseMaterial(p, tex, THREE.FrontSide);
  else if (sh === 'ground_layer') m = M.groundMaterial(p, tex, THREE.FrontSide);
  else if (sh === 'contact_shadow') m = M.contactMaterial(p);
  else if (sh === 'drop_skirt') m = M.skirtMaterial(p);
  else if (sh === 'card_shadow') m = 'skip';
  else if (M.FLAT[sh]) m = M.flatMaterial(sh, p);
  else if (sh === 'card_batch') m = 'batch';
  else if (e.class && e.class.endsWith('Material3D')) m = M.standardMaterial(p, (q) => texParam(q));
  else {
    unknownShaders.add(sh || e.class);
    m = new THREE.MeshStandardMaterial({ color: 0xff00ff });
  }
  matCache.set(id, m);
  return m;
}

// apply recorded uniform changes to a ported material
function applyMatParams(id, p) {
  const m = matCache.get(id);
  if (!m || typeof m === 'string') return;
  const u = m.userData.u || m.uniforms;
  if (!u) return;
  for (const k in p) {
    if (!u[k]) continue;
    const v = p[k];
    if (v && typeof v === 'object' && 'tex' in v) u[k].value = texById(v.tex);
    else if (u[k].value && u[k].value.isColor) u[k].value.copy(M.linearColor(v));
    else if (u[k].value && u[k].value.isVector2) u[k].value.set(v[0], v[1]);
    else u[k].value = v;
  }
}

// card_batch: per-print atlas page + rect from the params texture
let batchInfo = null;
function batchMats(matId, meshId) {
  const e = D.materials[matId];
  if (!batchInfo || batchInfo.mat !== matId) {
    const pimg = floatImage(e.params.params.tex);
    batchInfo = { mat: matId, pimg, cache: new Map() };
  }
  const uv2 = D.meshes[meshId].surfaces[0].attrs.uv2;
  const idx = Math.round(new Float32Array(BIN, uv2[0], 2)[1]);
  if (batchInfo.cache.has(idx)) return batchInfo.cache.get(idx);
  const { pimg } = batchInfo;
  const px = (row) => { const o = (row * pimg.w + idx) * 4; return Array.from(pimg.data.slice(o, o + 4)); };
  const r1 = px(1), r2 = px(2), r3 = px(3);
  // the pack step cut this print out of its atlas page (tools/threejs_pilot/pack_assets.py)
  const page = imageTexture(DATA + D.prints[idx], false);
  const pr = { rect: [0, 0, 1, 1], size: [r1[1], r1[2]], edge: r2 };
  const out = M.batchMaterial(e.params, pr, page, texParam);
  // card_shadow.gdshader: the print's shadow is ONE quad at the face plane (row 3 = quad rect), not the full mesh
  const q = new THREE.BufferGeometry();
  const x0 = r3[0], y0 = r3[1], w = r3[2], h = r3[3], z = r1[3];
  q.setAttribute('position', new THREE.BufferAttribute(new Float32Array([x0, y0, z, x0 + w, y0, z, x0 + w, y0 - h, z, x0, y0 - h, z]), 3));
  q.setAttribute('uv', new THREE.BufferAttribute(new Float32Array([0, 0, 1, 0, 1, 1, 0, 1]), 2));
  q.setAttribute('uv1', new THREE.BufferAttribute(new Float32Array(8), 2));
  q.setAttribute('normal', new THREE.BufferAttribute(new Float32Array([0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1]), 3));
  q.setIndex([0, 2, 1, 0, 3, 2]);
  out.quad = q;
  batchInfo.cache.set(idx, out);
  return out;
}

// ------------------------------------------------------------------ nodes
const nodeObj = new Map(); // node id -> { obj, kind, variants: Map, cur }
const world = new THREE.Group();
scene.add(world);

function buildMeshGroup(meshId, mats, mo, shadowMode) {
  const g = new THREE.Group();
  const me = D.meshes[meshId];
  me.surfaces.forEach((s, i) => {
    const mid = mo >= 0 ? mo : (mats && mats[i] !== undefined && mats[i] >= 0 ? mats[i] : s.material);
    let m = material(mid);
    if (!m || m === 'skip') return;
    if (s.prim !== 3) return;
    const geo = surfaceGeometry(meshId, i);
    const mesh = new THREE.Mesh(geo, m);
    mesh.castShadow = shadowMode !== 0;
    mesh.receiveShadow = !(m.isShaderMaterial || m.isMeshBasicMaterial);
    if (shadowMode === 3) { mesh.material = m.clone(); mesh.material.colorWrite = false; mesh.material.depthWrite = false; }
    mesh.matrixAutoUpdate = false;
    g.add(mesh);
  });
  g.matrixAutoUpdate = false;
  return g;
}

function buildMulti(node, shadowMode) {
  const mm = node.mm;
  const g = new THREE.Group();
  g.matrixAutoUpdate = false;
  if (!mm || mm.mesh < 0 || !mm.n) return g;
  const me = D.meshes[mm.mesh];
  const xf = new Float32Array(BIN, mm.xf[0], mm.xf[1] / 4);
  const cu = mm.cu ? new Float32Array(BIN, mm.cu[0], mm.cu[1] / 4) : null;
  me.surfaces.forEach((s, i) => {
    const mid = node._mo >= 0 ? node._mo : s.material;
    let m = material(mid);
    if (!m || m === 'skip') return;
    let depth = null;
    if (m === 'batch') {
      const b = batchMats(mid, mm.mesh); m = b.m; depth = b.d;
      const sq = b.quad.clone();
      sq.setAttribute('iCustom', new THREE.InstancedBufferAttribute(cu ? new Float32Array(cu.subarray(0, mm.n * 4)) : new Float32Array(mm.n * 4), 4));
      const sm = new THREE.InstancedMesh(sq, shadowOnlyMat, mm.n);
      for (let k = 0; k < mm.n; k++) sm.instanceMatrix.array.set(xf.subarray(k * 16, k * 16 + 16), k * 16);
      sm.customDepthMaterial = depth; sm.castShadow = true; sm.frustumCulled = false;
      sm.layers.set(1); // drawn by the shadow camera only
      g.add(sm);
      depth = null;
    }
    const geo = surfaceGeometry(mm.mesh, i).clone();
    const custom = new Float32Array(mm.n * 4);
    if (cu) custom.set(cu.subarray(0, mm.n * 4));
    geo.setAttribute('iCustom', new THREE.InstancedBufferAttribute(custom, 4));
    const im = new THREE.InstancedMesh(geo, m, mm.n);
    for (let k = 0; k < mm.n; k++) im.instanceMatrix.array.set(xf.subarray(k * 16, k * 16 + 16), k * 16);
    im.instanceMatrix.needsUpdate = true;
    im.computeBoundingSphere();
    im.castShadow = m.isMeshStandardMaterial && !m.userData.u?.atlas ? shadowMode !== 0 && !m.transparent : false;
    im.receiveShadow = !(m.isShaderMaterial);
    im.frustumCulled = false;
    g.add(im);
  });
  return g;
}

const shadowOnlyMat = new THREE.MeshBasicMaterial({ colorWrite: false, depthWrite: false, side: THREE.DoubleSide });
const tmpM = new THREE.Matrix4();
function setNode(c) {
  const node = D.nodes[c.n];
  let rec = nodeObj.get(c.n);
  if (!rec) {
    rec = { obj: new THREE.Group(), variants: new Map(), cur: null, mesh: -1, mats: null, mo: -1, sh: 1, visible: false };
    rec.obj.matrixAutoUpdate = false;
    rec.obj.visible = false;
    world.add(rec.obj);
    nodeObj.set(c.n, rec);
  }
  if (c.v === false) { rec.obj.visible = false; rec.visible = false; return; }
  if (c.v === true) { rec.obj.visible = true; rec.visible = true; }
  if (c.x) { rec.x = c.x; rec.obj.matrix.fromArray(c.x); rec.obj.matrixWorldNeedsUpdate = true; }
  let rebuild = false;
  if ('m' in c) { rec.mesh = c.m; rebuild = true; }
  if ('mats' in c) { rec.mats = c.mats; rebuild = true; }
  if ('mo' in c) { rec.mo = c.mo; rebuild = true; }
  if ('sh' in c) { rec.sh = c.sh; rebuild = true; }
  if ('mm' in c) { node.mm = c.mm; rec.variants.clear(); rebuild = true; }
  if ('mmh' in c && !('mm' in c) && !rec.cur) rebuild = true;
  if (rebuild) {
    const isMM = node.class === 'MultiMeshInstance3D';
    const key = isMM ? 'mm:' + rec.mo + ':' + (node.mm && node.mm.hash) : rec.mesh + '|' + (rec.mats || []).join(',') + '|' + rec.mo + '|' + rec.sh;
    let v = rec.variants.get(key);
    if (!v) {
      node._mo = rec.mo;
      v = isMM ? buildMulti(node, rec.sh) : (rec.mesh >= 0 ? buildMeshGroup(rec.mesh, rec.mats, rec.mo, rec.sh) : new THREE.Group());
      rec.variants.set(key, v);
    }
    if (rec.cur !== v) {
      if (rec.cur) rec.obj.remove(rec.cur);
      rec.obj.add(v);
      rec.cur = v;
    }
  }
}

// ------------------------------------------------------------------ timeline
let frames, tWait = -1, tTap = -1, tEnd = 0, tapTarget = null, hintPath = null;
const tracks = new Map(); // node id -> [{t, p, q, s}]
const camTrack = [];
let fi = 0; // next frame to apply
let T = 0; // timeline seconds
let holding = false, holdStart = 0;
let lastCaption = '';
const keyLight = new THREE.DirectionalLight(0xffffff, 1);
const fillLight = new THREE.DirectionalLight(0xffffff, 1);
keyLight.castShadow = true;
keyLight.shadow.mapSize.set(SHADOW, SHADOW);
keyLight.shadow.bias = -0.0004;
keyLight.shadow.normalBias = 0.01;
keyLight.shadow.radius = 3;
keyLight.shadow.camera.layers.enable(1);
scene.add(keyLight, keyLight.target, fillLight, fillLight.target);
const keyDir = new THREE.Vector3(0, -1, 0), fillDir = new THREE.Vector3(0, -1, 0);
let rigDistance = 10;
let shadowOpacity = 0.86;

function decompose(x) {
  const m = new THREE.Matrix4().fromArray(x);
  const p = new THREE.Vector3(), q = new THREE.Quaternion(), s = new THREE.Vector3();
  m.decompose(p, q, s);
  return { p, q, s };
}

function prepareTimeline() {
  frames = D.frames;
  for (let i = 0; i < frames.length; i++) {
    const f = frames[i];
    f.i = i;
    if (f.cam) camTrack.push({ t: f.t, ...decompose(f.cam.x), fov: f.cam.fov });
    for (const c of f.set || []) {
      if (c.x) {
        if (!tracks.has(c.n)) tracks.set(c.n, []);
        tracks.get(c.n).push({ t: f.t, ...decompose(c.x), cut: 'm' in c });
      }
    }
    if ('expect' in f) {
      if (f.expect !== '' && tWait < 0) tWait = f.t;
      else if (f.expect === '' && tWait >= 0 && tTap < 0) tTap = f.t;
    }
    if (f.targets && f.targets.seed && !tapTarget) tapTarget = f.targets.seed;
    if (f.beat === 'grow' && !tEnd) tEnd = f.t;
  }
  if (!tEnd) tEnd = frames[frames.length - 1].t;
  // the hint voice: the last voice clip that started before the wait (the runner replays it after a quiet spell)
  for (const f of frames) {
    if (f.t > tWait) break;
    for (const a of f.audio || []) if (a.ev === 'start' && /voice/.test(a.path)) hintPath = a.path;
  }
  // only keep tracks that actually move
  for (const [n, tr] of tracks) if (tr.length < 2) tracks.delete(n);
}

function applyFrame(f) {
  for (const c of f.set || []) setNode(c);
  for (const mc of f.mat || []) applyMatParams(mc.mat, mc.p);
  if (f.lights) for (const l of f.lights) applyLight(l);
  if (f.env) applyEnv(f.env);
  if (f.rig) applyRig(f.rig);
  if (f.dof) { post.u.dofFar.value.set(f.dof[0] ? 1 : 0, f.dof[1], f.dof[2], 0); post.u.dofNear.value.set(f.dof[3] ? 1 : 0, f.dof[4], f.dof[5], f.dof[6]); }
  if (f.buses) audio.setBuses(f.buses);
  if (f.audio) for (const a of f.audio) audio.event(a, camera.position);
  if ('caption' in f) showCaption(f.caption);
}

const omnis = new Map();
function applyLight(l) {
  const x = l.x; // light shines along its -Z
  if (l.class === 'OmniLight3D') {
    let o = omnis.get(l.n);
    if (!o) { o = new THREE.PointLight(0xffffff, 1, 1, l.atten ?? 1); o.castShadow = false; scene.add(o); omnis.set(l.n, o); }
    o.position.set(x[12], x[13], x[14]);
    o.color.copy(M.linearColor(l.color));
    o.distance = l.range || 5;
    o.intensity = l.energy * Math.PI * TUNE.omni;
    return;
  }
  const dir = new THREE.Vector3(-x[8], -x[9], -x[10]).normalize();
  const col = M.linearColor(l.color);
  if (/fill/i.test(l.name)) { fillDir.copy(dir); fillLight.color.copy(col); fillLight.intensity = l.energy * Math.PI * (l.spec === 0 ? 1 : 1); }
  else {
    keyDir.copy(dir); keyLight.color.copy(col); keyLight.intensity = l.energy * Math.PI * TUNE.key;
    shadowOpacity = l.opacity ?? 1;
    keyLight.castShadow = !!l.shadow;
    M.shared.keyColor.value.copy(col).multiplyScalar(l.energy);
  }
}

function applyEnv(e) {
  if (e.ambient_light_color) { ambient.color.copy(M.linearColor(e.ambient_light_color)); ambient.intensity = (e.ambient_light_energy ?? 1) * Math.PI * TUNE.amb; }
  if (e.background_color) renderer.setClearColor(M.linearColor(e.background_color), 1);
  post.u.exposure.value = e.tonemap_exposure ?? 1;
  post.u.adjust.value.set(e.adjustment_enabled ? e.adjustment_brightness : 1, e.adjustment_enabled ? e.adjustment_contrast : 1, e.adjustment_enabled ? e.adjustment_saturation : 1);
  post.u.fogOn.value = e.fog_enabled && TUNE.fog > 0 ? 1 : 0;
  post.u.fogBegin.value = e.fog_depth_begin; post.u.fogEnd.value = e.fog_depth_end;
  post.u.fogDensity.value = e.fog_density * TUNE.fog; post.u.fogCurve.value = e.fog_depth_curve;
  post.u.fogColor.value.copy(M.linearColor(e.fog_light_color)).multiplyScalar(e.fog_light_energy ?? 1);
  post.u.glow.value.set(e.glow_enabled ? e.glow_intensity * TUNE.glow : 0, (e.glow_bloom ?? 0) * TUNE.glow, e.glow_hdr_threshold ?? 1);
}

function applyRig(r) {
  if (r.distance) rigDistance = r.distance;
  const p = r.post_params || {};
  for (const k of ['focus_y', 'band_half', 'band_soft', 'max_lod', 'base_lod', 'top_bias', 'vignette', 'grade', 'saturation', 'contrast', 'lift', 'grain', 'toe']) {
    if (k in p) post.u[k].value = p[k];
  }
  if (p.shadow_tint) post.u.shadow_tint.value.set(...p.shadow_tint.slice(0, 3));
  if (p.highlight_tint) post.u.highlight_tint.value.set(...p.highlight_tint.slice(0, 3));
  post.u.postOn.value = r.post_visible === false ? 0 : 1;
}

function sampleTrack(tr, t, out) {
  // binary search last key <= t
  let lo = 0, hi = tr.length - 1;
  if (t <= tr[0].t) return tr[0];
  if (t >= tr[hi].t) return tr[hi];
  while (hi - lo > 1) { const mid = (lo + hi) >> 1; if (tr[mid].t <= t) lo = mid; else hi = mid; }
  const a = tr[lo], b = tr[hi];
  if (b.t - a.t > 0.05 || b.cut) return a; // a hold or a figure swap: no blending across it
  const k = (t - a.t) / (b.t - a.t);
  out.p.lerpVectors(a.p, b.p, k); out.q.slerpQuaternions(a.q, b.q, k); out.s.lerpVectors(a.s, b.s, k);
  if (a.fov !== undefined) out.fov = a.fov + (b.fov - a.fov) * k;
  return out;
}
const tmp = { p: new THREE.Vector3(), q: new THREE.Quaternion(), s: new THREE.Vector3(), fov: 20 };

function advance(dt) {
  if (holding) {
    // the runner waits for the child's tap; the hint voice repeats after a quiet spell
    if (hintPath && performance.now() - holdStart > 9000) { holdStart = performance.now(); audio.event({ ev: 'start', p: -7, path: hintPath, vol: 0, bus: 'Master' }); }
    return;
  }
  T += dt;
  if (tWait >= 0 && tTap > 0 && T >= tTap - 1 / 30 && !tapped) {
    T = tTap - 1 / 30;
    holding = true; holdStart = performance.now();
    if (AUTO) setTimeout(() => doTap(true), 1000);
  }
  while (fi < frames.length && frames[fi].t <= T) applyFrame(frames[fi++]);
  if (T >= tEnd) finish();
}
let tapped = false;

function updateMotion() {
  // interpolated camera + moving nodes (recording is 30 fps, the display may be 60 / 120 Hz)
  const c = sampleTrack(camTrack, T, tmp);
  camera.position.copy(c.p); camera.quaternion.copy(c.q);
  camera.fov = c.fov; camera.updateProjectionMatrix();
  camera.updateMatrixWorld(true);
  for (const [n, tr] of tracks) {
    const rec = nodeObj.get(n);
    if (!rec || !rec.visible) continue;
    const s = sampleTrack(tr, T, { p: new THREE.Vector3(), q: new THREE.Quaternion(), s: new THREE.Vector3() });
    rec.obj.matrix.compose(s.p, s.q, s.s);
    rec.obj.matrixWorldNeedsUpdate = true;
  }
}

function fitShadow() {
  // the key light's ortho shadow box follows what the camera frames (Godot: 2 PSSM splits up to shadow_distance)
  const fwd = new THREE.Vector3(0, 0, -1).applyQuaternion(camera.quaternion);
  const focus = camera.position.clone().addScaledVector(fwd, rigDistance);
  const halfH = Math.tan(THREE.MathUtils.degToRad(camera.fov / 2)) * rigDistance;
  const r = Math.min(Math.max(halfH * camera.aspect * 1.6, 1.2), 9);
  keyLight.target.position.copy(focus);
  keyLight.position.copy(focus).addScaledVector(keyDir, -20);
  const sc = keyLight.shadow.camera;
  sc.left = -r; sc.right = r; sc.top = r; sc.bottom = -r; sc.near = 1; sc.far = 45;
  sc.updateProjectionMatrix();
  fillLight.target.position.copy(focus);
  fillLight.position.copy(focus).addScaledVector(fillDir, -20);
  M.shared.keyDirView.value.copy(keyDir).negate().transformDirection(camera.matrixWorldInverse);
  keyLight.shadow.intensity = shadowOpacity;
}

// ------------------------------------------------------------------ UI: caption, tap ring
function showCaption(txt) {
  if (txt === lastCaption) return;
  lastCaption = txt;
  const el = $('cap');
  if (!txt) { el.classList.remove('on'); return; }
  const bold = /\[b\]/.test(txt);
  const parts = txt.split('|').map((s) => s.replace(/\[[^\]]*\]/g, '').replace(/\u2060/g, '').trim()).filter(Boolean);
  const text = bold ? `<b>${parts.pop() || ''}</b>` : parts.pop() || '';
  const chip = parts.join(' ');
  el.innerHTML = (chip ? `<span class="chip">${chip}</span>` : '') + `<span class="txt">${text}</span>`;
  el.classList.add('on');
}

const ring = $('ring');
function updateRing() {
  if (!holding || !tapTarget) { ring.style.display = 'none'; return; }
  const p = new THREE.Vector3(...tapTarget.p).project(camera);
  const x = (p.x * 0.5 + 0.5) * window.innerWidth, y = (-p.y * 0.5 + 0.5) * window.innerHeight;
  const r = tapTarget.r * (window.innerHeight / D.meta.viewport[1]) * 1.3;
  ring.style.display = 'block';
  ring.style.left = x - r + 'px'; ring.style.top = y - r + 'px';
  ring.style.width = ring.style.height = 2 * r + 'px';
  ring.dataset.x = x; ring.dataset.y = y; ring.dataset.r = r;
}

function doTap(auto) {
  if (!holding || tapped) return false;
  tapped = true; holding = false;
  ring.style.display = 'none';
  metrics.tapAt = T;
  metrics.tapAuto = !!auto;
  return true;
}

canvas.addEventListener('pointerdown', (e) => {
  audio.unlock();
  if (!holding) return;
  const x = Number(ring.dataset.x), y = Number(ring.dataset.y), r = Number(ring.dataset.r);
  if (Math.hypot(e.clientX - x, e.clientY - y) <= r * 1.25) doTap(false);
});

// ------------------------------------------------------------------ main
const audio = new AudioPlayer(DATA);
let running = false;
let finished = false;

function finish() {
  if (finished) return;
  finished = true;
  metrics.state = 'done';
  $('again').classList.add('on');
}

function restart() {
  audio.stopAll();
  for (const rec of nodeObj.values()) { rec.obj.visible = false; rec.visible = false; }
  fi = 0; T = 0; tapped = false; holding = false; finished = false; lastCaption = '';
  showCaption('');
  $('again').classList.remove('on');
  metrics.state = 'playing';
}
$('subs').addEventListener('click', (e) => {
  e.stopPropagation();
  const off = $('cap').classList.toggle('off');
  $('subs').textContent = off ? '자막 꺼짐' : '자막 켜짐';
});
$('again').addEventListener('click', () => { audio.unlock(); restart(); });

let last = 0;
function loop(now) {
  requestAnimationFrame(loop);
  const dt = last ? Math.min((now - last) / 1000, 0.1) : 1 / 60;
  if (last) metrics.frames.push(now - last);
  last = now;
  if (metrics.frames.length > 20000) metrics.frames.splice(0, 10000);
  renderer.info.reset();
  if (running) advance(dt);
  M.shared.time.value += dt;
  M.shared.wind.value.x += dt;
  metrics.t = T;
  updateMotion();
  fitShadow();
  renderer.setRenderTarget(rt);
  renderer.render(scene, camera);
  renderer.setRenderTarget(null);
  { const th = Math.tan(THREE.MathUtils.degToRad(camera.fov / 2)); post.u.tanHalf.value.set(th * camera.aspect, th); }
  post.u.cNear.value = camera.near; post.u.cFar.value = camera.far; post.u.time.value = now / 1000;
  renderer.render(post.scene, post.cam);
  updateRing();
}

async function main() {
  setProgress('불러오는 중…');
  const geoGz = async () => {
    const b = await fetchBuf(DATA + 'geo.bin.gz', 'geo');
    const h = new Uint8Array(b, 0, 2);
    if (h[0] !== 0x1f || h[1] !== 0x8b) return b; // a server that sent Content-Encoding: gzip (vite dev): already inflated
    return new Response(new Blob([b]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer();
  };
  const [js, bin] = await Promise.all([fetchBuf(DATA + 'scene.json', 'json'), geoGz()]);
  D = JSON.parse(new TextDecoder().decode(js));
  BIN = bin;
  resize();
  window.addEventListener('resize', resize);
  prepareTimeline();
  // prebuild everything that ever appears (all node variants), so playback never compiles or uploads mid-shot
  for (const f of frames) for (const c of f.set || []) setNode(c);
  for (const rec of nodeObj.values()) { rec.obj.visible = false; rec.visible = false; }
  fi = 0;
  // apply the first frame so the page shows the opening shot behind the start card
  while (fi < frames.length && frames[fi].t <= 0.0001 + frames[0].t) applyFrame(frames[fi++]);
  T = frames[0].t;
  setProgress('그림 불러오는 중…');
  await Promise.all(imgLoads);
  audio.ctx = null;
  const ac = new (window.AudioContext || window.webkitAudioContext)();
  audio.ctx = ac; audio.master = ac.createGain(); audio.master.connect(ac.destination);
  const paths = new Set();
  for (const f of frames) for (const a of f.audio || []) if (a.ev === 'start' && !a.path.startsWith('<')) paths.add(a.path);
  setProgress('소리 불러오는 중…');
  await audio.preload([...paths]);
  metrics.bytes.audio = audio.bytes;
  renderer.compile(scene, camera);
  metrics.loadMs = Math.round(performance.now() - T0);
  metrics.texMB = Math.round(texBytes / 1048576);
  metrics.unknownShaders = [...unknownShaders];
  metrics.ready = true;
  metrics.state = 'ready';
  $('load').remove();
  requestAnimationFrame(loop);
  const start = () => {
    audio.unlock();
    $('start').classList.remove('on');
    restart();
    running = true;
  };
  if (AUTO) start();
  else { $('start').classList.add('on'); $('start').addEventListener('click', start, { once: true }); }
  // tests / compare sheet: jump to a record time and hold there (no audio)
  metrics.seek = (t) => {
    running = false;
    audio.stopAll();
    const ctx = audio.ctx; audio.ctx = null; // events skipped while seeking
    restart();
    tapped = t > tTap && tTap > 0;
    while (fi < frames.length && frames[fi].t <= t) applyFrame(frames[fi++]);
    T = t;
    holding = tWait >= 0 && t >= tWait && t < tTap;
    audio.ctx = ctx;
    $('start').classList.remove('on');
    return { tWait, tTap, tEnd };
  };
  metrics.audioLog = () => audio.log;
  metrics.timeline = { tWait, tTap, tEnd, t0: frames[0].t };
  setInterval(() => {
    const i = renderer.info;
    let geoBytes = 0;
    for (const g of geoCache.values()) for (const k in g.attributes) geoBytes += g.attributes[k].array.byteLength;
    const rtBytes = rt ? rt.width * rt.height * (8 * 1.33 + 4) * (MSAA > 0 ? 1 + MSAA * 0.5 : 1) : 0;
    metrics.info = { calls: i.render.calls, triangles: i.render.triangles, textures: i.memory.textures, geometries: i.memory.geometries, programs: i.programs ? i.programs.length : 0 };
    metrics.gpuMB = Math.round((texBytes + geoBytes + rtBytes + SHADOW * SHADOW * 4) / 1048576);
    metrics.geoMB = Math.round(geoBytes / 1048576);
    metrics.audio = { state: audio.ctx ? audio.ctx.state : 'none', started: audio.started, playing: audio.voices.size };
    metrics.holding = holding;
    if (Q.has('hud')) $('hud').textContent = `${metrics.info.calls} calls  ${(metrics.info.triangles / 1000).toFixed(0)}k tris  ~${metrics.gpuMB} MB gpu  t=${T.toFixed(1)}`;
  }, 1000);
}

main().catch((e) => { metrics.errors.push(String(e)); setProgress('오류: ' + e.message); console.error(e); });
