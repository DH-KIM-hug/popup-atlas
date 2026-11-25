// One tale, played back from its export (tools/threejs/export_tale.gd -> tools/threejs/pack_tale.py).
// The export is a 30 fps recording of what the Godot runner showed: per view (the page, the next page during a live
// page turn, the cover / ending book) the camera, lights, environment and look rig; every geometry node's transform,
// mesh / material swaps and MultiMesh buffers; audio events; captions, page tab, page turn, flash cards; the tap
// targets and the autoplay taps. This module rebuilds the scenes and replays the frames; every tap step is a live
// wait point (the timeline holds just before the recorded tap until the child taps the target), a hold step (blow)
// only runs while the finger is down. Chunks (one per beat) stream: the first beat plays while the rest loads.
import * as THREE from 'three';
import { makePost } from './post.js';
import * as M from './materials.js';
import { makeTurn } from './turn.js';

const VIEW_NAMES = ['main', 'next', 'book'];
const FPS = 30;

export async function playTale(app, tale, opt = {}) {
  const { renderer, audio, Q } = app;
  const DATA = app.data;
  const TDIR = DATA + 'tales/' + tale + '/';
  const AUTO = !!opt.auto;
  const TUNE = { dof: Number(Q.get('dof') || 64), fog: Number(Q.get('fog') ?? 1), amb: Number(Q.get('amb') ?? 0.75),
    key: Number(Q.get('key') ?? 0.65), glow: Number(Q.get('glow') ?? 1), agx: Number(Q.get('agx') ?? 1.4), omni: Number(Q.get('omni') ?? 1) };
  const SHADOW = Number(Q.get('shadow') || 2048);
  const MSAA = Number(Q.get('msaa') ?? 4);
  const DPR = renderer.getPixelRatio();
  const T0 = performance.now();
  const $ = (id) => document.getElementById(id);
  const metrics = window.__pilot = {
    tale, ready: false, firstFrameMs: 0, loadMs: 0, bytes: {}, frames: [], info: null, gpuMB: 0, errors: app.errors, t: 0, state: 'loading',
    chunks: 0, chunksTotal: 0, waits: 0, tapped: [], lines: [], beat: '', stalls: 0, stallMs: 0,
  };
  const disposables = new Set();
  const track = (o) => { disposables.add(o); return o; };
  let alive = true;

  // ------------------------------------------------------------------ data
  const D = { textures: [], materials: [], meshes: [], nodes: [] };
  const BINS = [];
  const frames = [];
  let idx;
  async function fetchBuf(url, kind) {
    const r = await fetch(url);
    if (!(r.ok || r.status === 0)) throw new Error(url + ' ' + r.status);
    const b = await r.arrayBuffer();
    metrics.bytes[kind] = (metrics.bytes[kind] || 0) + b.byteLength;
    return b;
  }
  async function fetchGz(url, kind) {
    const b = await fetchBuf(url, kind);
    const h = new Uint8Array(b, 0, Math.min(2, b.byteLength));
    if (b.byteLength < 2 || h[0] !== 0x1f || h[1] !== 0x8b) return b; // a server that inflated it already
    return new Response(new Blob([b]).stream().pipeThrough(new DecompressionStream('gzip'))).arrayBuffer();
  }

  // ------------------------------------------------------------------ textures
  const texCache = new Map();
  let texBytes = 0;
  const maxAniso = Math.min(4, renderer.capabilities.getMaxAnisotropy());
  const pendingImgs = new Set();
  function imageTexture(url, repeat, linear) {
    const key = url + (repeat ? '#r' : '') + (linear ? '#l' : '');
    if (texCache.has(key)) return texCache.get(key);
    const t = track(new THREE.Texture());
    t.flipY = false;
    t.colorSpace = linear ? THREE.NoColorSpace : THREE.SRGBColorSpace;
    t.anisotropy = maxAniso;
    t.wrapS = t.wrapT = repeat ? THREE.RepeatWrapping : THREE.ClampToEdgeWrapping;
    t.minFilter = THREE.LinearMipmapLinearFilter;
    texCache.set(key, t);
    const srcKey = 'src:' + url;
    const base = texCache.get(srcKey);
    if (base) {
      base.then((bmp) => { if (bmp) { t.image = bmp; t.needsUpdate = true; } });
      return t;
    }
    const p = fetchBuf(DATA + url, 'tex')
      .then((b) => createImageBitmap(new Blob([b]), { premultiplyAlpha: 'none', colorSpaceConversion: 'none' }))
      .then((bmp) => { t.image = bmp; t.needsUpdate = true; texWarm.push(t); texBytes += bmp.width * bmp.height * 4 * 1.33; disposables.add({ dispose: () => bmp.close() }); return bmp; })
      .catch((e) => { console.warn('tex', url, e); return null; });
    texCache.set(srcKey, p);
    pendingImgs.add(p);
    p.finally(() => pendingImgs.delete(p));
    return t;
  }
  const LINEAR_TEX = /paper_fibre|felt|noise|grain/i;
  function texById(id, repeat = false) {
    const e = D.textures[id];
    if (!e || e.skip) return null;
    if (e.web) {
      const lin = LINEAR_TEX.test(e.res || '');
      return imageTexture(e.web, repeat || lin, lin);
    }
    return null;
  }
  const texParam = (p, repeat) => (p && typeof p === 'object' && 'tex' in p ? texById(p.tex, repeat) : null);
  function floatImage(id) {
    const e = D.textures[id];
    const f = e && e.file && e.file.float ? e.file : null;
    if (!f) return null;
    const r = f.float;
    return { w: f.w, h: f.h, data: new Float32Array(BINS[r[0]], r[1], r[2] / 4) };
  }

  // ------------------------------------------------------------------ geometry
  const attrCache = new Map();
  function attr(r, n, kind = 'f32') {
    const key = r.join(':') + ':' + n;
    let a = attrCache.get(key);
    if (a) return a;
    const buf = BINS[r[0]];
    if (r[3] === 'i8') a = new THREE.BufferAttribute(new Int8Array(buf, r[1], r[2]), n, true);
    else if (kind === 'u32') a = new THREE.BufferAttribute(new Uint32Array(buf, r[1], r[2] / 4), 1);
    else a = new THREE.BufferAttribute(new Float32Array(buf, r[1], r[2] / 4), n);
    attrCache.set(key, a);
    return a;
  }
  const geoCache = new Map();
  function surfaceGeometry(meshId, si) {
    const key = meshId + ':' + si;
    if (geoCache.has(key)) return geoCache.get(key);
    const s = D.meshes[meshId].surfaces[si];
    const g = track(new THREE.BufferGeometry());
    const A = s.attrs;
    g.setAttribute('position', attr(A.position, 3));
    if (A.normal) g.setAttribute('normal', attr(A.normal, 3)); else g.computeVertexNormals();
    if (A.uv) g.setAttribute('uv', attr(A.uv, 2)); else g.setAttribute('uv', new THREE.BufferAttribute(new Float32Array(s.count * 2), 2));
    if (A.uv2) g.setAttribute('uv1', attr(A.uv2, 2));
    if (A.color) g.setAttribute('color', attr(A.color, 4));
    if (A.tangent) g.setAttribute('gTangent', attr(A.tangent, 4));
    if (s.index) g.setIndex(attr(s.index, 1, 'u32'));
    g.computeBoundingSphere();
    geoCache.set(key, g);
    return g;
  }

  // ------------------------------------------------------------------ materials
  const matCache = new Map();
  const unknownShaders = new Set();
  const shaderName = (e) => (e && e.shader ? e.shader.split('/').pop().replace('.gdshader', '') : '');
  function material(id) {
    if (id < 0 || id === undefined) return null;
    if (matCache.has(id)) return matCache.get(id);
    const e = D.materials[id];
    if (!e) return null;
    const p = e.params || {};
    let m;
    const sh = shaderName(e);
    if (sh === 'paper_print' || sh === 'cast_print') m = M.printMaterial(p, texParam, THREE.FrontSide);
    else if (sh === 'paper_edge' || sh === 'cast_edge') m = M.edgeMaterial(p, texParam, THREE.FrontSide);
    else if (sh === 'house_body') m = M.houseMaterial(p, texParam, THREE.FrontSide);
    else if (sh === 'ground_layer') m = M.groundMaterial(p, texParam, THREE.FrontSide);
    else if (sh === 'contact_shadow') m = M.contactMaterial(p);
    else if (sh === 'drop_skirt') m = M.skirtMaterial(p);
    else if (sh === 'cover_book') m = M.coverBookMaterial(p, texParam);
    else if (sh === 'card_shadow') m = 'skip';
    else if (M.FLAT[sh]) m = M.flatMaterial(sh, p);
    else if (sh === 'card_batch') m = 'batch';
    else if (e.class && e.class.endsWith('Material3D')) m = M.standardMaterial(p, (q) => texParam(q));
    else {
      unknownShaders.add(sh || e.class);
      m = new THREE.MeshStandardMaterial({ color: 0xff00ff });
    }
    if (typeof m === 'object') track(m);
    matCache.set(id, m);
    return m;
  }
  function applyMatParams(id, p) {
    const m = matCache.get(id);
    if (!m || typeof m === 'string') {
      // not built yet: fold the change into its definition so a later build starts from it
      const e = D.materials[id];
      if (e && e.params) Object.assign(e.params, p);
      return;
    }
    const u = m.userData.u || m.uniforms;
    if (!u) return;
    for (const k in p) {
      const uk = u[k] ? k : (k === 'mode' ? 'cbMode' : k === 'tex' ? 'cbTex' : null);
      if (!uk || !u[uk]) continue;
      const v = p[k];
      if (v && typeof v === 'object' && 'tex' in v) u[uk].value = texById(v.tex);
      else if (u[uk].value && u[uk].value.isColor) u[uk].value.copy(M.linearColor(v));
      else if (u[uk].value && u[uk].value.isVector2) u[uk].value.set(v[0], v[1]);
      else if (u[uk].value && u[uk].value.isVector4) u[uk].value.set(v[0], v[1], v[2], v[3]);
      else u[uk].value = v;
    }
  }

  // card_batch: per-print material (the pack step cropped each print out of its atlas page)
  const batchInfos = new Map();
  const shadowOnlyMat = track(new THREE.MeshBasicMaterial({ colorWrite: false, depthWrite: false, side: THREE.DoubleSide }));
  function batchMats(matId, meshId) {
    const e = D.materials[matId];
    let bi = batchInfos.get(matId);
    if (!bi) { bi = { pimg: floatImage(e.params.params.tex), cache: new Map() }; batchInfos.set(matId, bi); }
    const uv2 = D.meshes[meshId].surfaces[0].attrs.uv2;
    const pidx = Math.round(new Float32Array(BINS[uv2[0]], uv2[1], 2)[1]);
    if (bi.cache.has(pidx)) return bi.cache.get(pidx);
    const { pimg } = bi;
    const px = (row) => { const o = (row * pimg.w + pidx) * 4; return Array.from(pimg.data.slice(o, o + 4)); };
    const r1 = px(1), r2 = px(2), r3 = px(3);
    const page = imageTexture(e.prints[pidx], false, false);
    const out = M.batchMaterial(e.params, { rect: [0, 0, 1, 1], size: [r1[1], r1[2]], edge: r2 }, page, texParam);
    track(out.m); track(out.d);
    // card_shadow.gdshader: the print's shadow is ONE quad at the face plane (row 3 = quad rect)
    const q = track(new THREE.BufferGeometry());
    const x0 = r3[0], y0 = r3[1], w = r3[2], h = r3[3], z = r1[3];
    q.setAttribute('position', new THREE.BufferAttribute(new Float32Array([x0, y0, z, x0 + w, y0, z, x0 + w, y0 - h, z, x0, y0 - h, z]), 3));
    q.setAttribute('uv', new THREE.BufferAttribute(new Float32Array([0, 0, 1, 0, 1, 1, 0, 1]), 2));
    q.setAttribute('uv1', new THREE.BufferAttribute(new Float32Array(8), 2));
    q.setAttribute('normal', new THREE.BufferAttribute(new Float32Array([0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1]), 3));
    q.setIndex([0, 2, 1, 0, 3, 2]);
    out.quad = q;
    bi.cache.set(pidx, out);
    return out;
  }

  // ------------------------------------------------------------------ views
  const views = VIEW_NAMES.map((name) => {
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(20, 1, 0.1, 80);
    const ambient = new THREE.AmbientLight(0xffffff, 1);
    const key = new THREE.DirectionalLight(0xffffff, 1);
    const fill = new THREE.DirectionalLight(0xffffff, 0);
    key.castShadow = true;
    key.shadow.mapSize.set(name === 'book' ? 1024 : SHADOW, name === 'book' ? 1024 : SHADOW);
    key.shadow.bias = -0.0004;
    key.shadow.normalBias = 0.01;
    key.shadow.radius = 3;
    key.shadow.camera.layers.enable(1);
    scene.add(ambient, key, key.target, fill, fill.target);
    const post = makePost();
    post.u.dofScale.value = TUNE.dof;
    post.u.agxK.value = TUNE.agx;
    track(post.mat);
    return { name, scene, camera, ambient, key, fill, keyDir: new THREE.Vector3(0, -1, 0), fillDir: new THREE.Vector3(0, -1, 0),
      keyColor: new THREE.Color(1, 1, 1), keyEnergy: 1, omnis: new Map(), post, rigDistance: 10, shadowOpacity: 0.86, clear: new THREE.Color(0x24160d),
      cam: { near: 0.1, far: 80 }, env: {}, rig: {}, track: [] };
  });
  const viewBy = Object.fromEntries(views.map((v) => [v.name, v]));
  let rt = null, rtNew = null;
  const turn = makeTurn();
  track(turn.mat);
  function resize() {
    const w = window.innerWidth, h = window.innerHeight;
    renderer.setSize(w, h, false);
    for (const v of views) { v.camera.aspect = w / h; v.camera.updateProjectionMatrix(); }
    const W = Math.round(w * DPR), H = Math.round(h * DPR);
    if (rt) { rt.depthTexture.dispose(); rt.dispose(); rtNew.dispose(); }
    rt = new THREE.WebGLRenderTarget(W, H, {
      type: THREE.HalfFloatType, samples: MSAA, generateMipmaps: true,
      minFilter: THREE.LinearMipmapLinearFilter, magFilter: THREE.LinearFilter, colorSpace: THREE.LinearSRGBColorSpace,
    });
    rt.depthTexture = new THREE.DepthTexture(W, H);
    rt.depthTexture.type = THREE.UnsignedIntType;
    rtNew = new THREE.WebGLRenderTarget(W, H, { colorSpace: THREE.LinearSRGBColorSpace });
    for (const v of views) {
      v.post.u.tColor.value = rt.texture; v.post.u.tDepth.value = rt.depthTexture; v.post.u.px.value.set(1 / W, 1 / H);
    }
    turn.u.size.value.set(W, H);
    turn.u.tNew.value = rtNew.texture;
  }
  resize();
  window.addEventListener('resize', resize);

  // ------------------------------------------------------------------ nodes
  const nodeObj = new Map(); // node id -> rec
  function getRec(n) {
    let rec = nodeObj.get(n);
    if (!rec) {
      rec = { obj: new THREE.Group(), variants: new Map(), cur: null, mesh: -1, mats: null, mo: -1, sh: 1, w: 0, visible: false, mm: null, lbl: null, x: null };
      rec.obj.matrixAutoUpdate = false;
      rec.obj.visible = false;
      views[0].scene.add(rec.obj);
      nodeObj.set(n, rec);
    }
    return rec;
  }

  function buildMeshGroup(meshId, mats, mo, shadowMode) {
    const g = new THREE.Group();
    const me = D.meshes[meshId];
    me.surfaces.forEach((s, i) => {
      const mid = mo >= 0 ? mo : (mats && mats[i] !== undefined && mats[i] >= 0 ? mats[i] : s.material);
      const m = material(mid);
      if (!m || typeof m === 'string') return;
      if (s.prim !== 3) return;
      const mesh = new THREE.Mesh(surfaceGeometry(meshId, i), m);
      mesh.castShadow = shadowMode !== 0;
      mesh.receiveShadow = !(m.isShaderMaterial || m.isMeshBasicMaterial);
      if (shadowMode === 3) { mesh.material = track(m.clone()); mesh.material.colorWrite = false; mesh.material.depthWrite = false; }
      mesh.matrixAutoUpdate = false;
      g.add(mesh);
    });
    g.matrixAutoUpdate = false;
    return g;
  }

  // MultiMesh: one InstancedMesh per surface sized for the most instances seen; the instance data is written in place
  function buildMulti(node, mm, mo, shadowMode) {
    const g = new THREE.Group();
    g.matrixAutoUpdate = false;
    g.userData.ims = [];
    if (!mm || mm.mesh < 0) return g;
    const me = D.meshes[mm.mesh];
    const cap = Math.max(mm.count || 0, mm.n || 0, 1);
    me.surfaces.forEach((s, i) => {
      const mid = mo >= 0 ? mo : s.material;
      let m = material(mid);
      if (!m || m === 'skip') return;
      if (m === 'batch') {
        const b = batchMats(mid, mm.mesh);
        const sq = track(b.quad.clone());
        sq.setAttribute('iCustom', new THREE.InstancedBufferAttribute(new Float32Array(cap * 4), 4));
        const sm = new THREE.InstancedMesh(sq, shadowOnlyMat, cap);
        sm.customDepthMaterial = b.d; sm.castShadow = true; sm.frustumCulled = false;
        sm.layers.set(1); // drawn by the shadow camera only
        g.add(sm); g.userData.ims.push(sm);
        m = b.m;
      }
      const geo = track(surfaceGeometry(mm.mesh, i).clone());
      geo.setAttribute('iCustom', new THREE.InstancedBufferAttribute(new Float32Array(cap * 4), 4));
      const im = new THREE.InstancedMesh(geo, m, cap);
      im.castShadow = m.isMeshStandardMaterial && !m.userData.u?.atlas ? shadowMode !== 0 && !m.transparent : false;
      im.receiveShadow = !m.isShaderMaterial;
      im.frustumCulled = false;
      g.add(im); g.userData.ims.push(im);
    });
    writeInstances(g, mm, null, 0);
    return g;
  }
  // a key stored as a delta (pack_tale.py): rebuilt in load order from the node's previous key
  const lastXf = new Map();
  function resolveMM(n, mm) {
    if (!mm || mm.xfArr) return;
    if (mm.xf) { mm.xfArr = new Float32Array(BINS[mm.xf[0]], mm.xf[1], mm.xf[2] / 4); lastXf.set(n, mm.xfArr); return; }
    if (!mm.dx) return;
    let base = lastXf.get(n);
    if (!base) { const nm = D.nodes[n].mm; resolveMM(n, nm); base = nm && nm.xfArr; }
    const arr = new Float32Array(mm.n * 16);
    if (base) arr.set(base.subarray(0, Math.min(base.length, arr.length)));
    const ix = new Uint32Array(BINS[mm.dx[0]], mm.dx[1], mm.dx[2] / 4);
    const v = new Float32Array(BINS[mm.dv[0]], mm.dv[1], mm.dv[2] / 4);
    for (let k = 0; k < ix.length; k++) arr.set(v.subarray(k * 16, k * 16 + 16), ix[k] * 16);
    mm.xfArr = arr;
    lastXf.set(n, arr);
  }
  function mmArrays(mm) {
    return { xf: mm.xfArr || new Float32Array(BINS[mm.xf[0]], mm.xf[1], mm.xf[2] / 4), cu: mm.cu ? new Float32Array(BINS[mm.cu[0]], mm.cu[1], mm.cu[2] / 4) : null };
  }
  function writeInstances(g, mm, mmB, k) {
    if (!mm || !g.userData.ims) return;
    const A = mmArrays(mm);
    const n = mm.n;
    const B = mmB && mmB.n === n ? mmArrays(mmB) : null;
    for (const im of g.userData.ims) {
      const cap = im.instanceMatrix.count;
      const nn = Math.min(n, cap);
      const dst = im.instanceMatrix.array;
      if (B && k > 0) { for (let i = 0; i < nn * 16; i++) dst[i] = A.xf[i] + (B.xf[i] - A.xf[i]) * k; }
      else dst.set(A.xf.subarray(0, nn * 16));
      im.count = nn;
      im.instanceMatrix.needsUpdate = true;
      const ic = im.geometry.getAttribute('iCustom');
      if (A.cu && ic && im.userData.cu !== mm.cu) { ic.array.set(A.cu.subarray(0, nn * 4)); ic.needsUpdate = true; im.userData.cu = mm.cu; }
    }
  }

  // Label3D (the book's title): canvas text on a plane
  function buildLabel(l) {
    const g = new THREE.Group();
    g.matrixAutoUpdate = false;
    if (!l || !l.text) return g;
    const fs = l.fs || 32, pad = 8;
    const cv = document.createElement('canvas');
    const ctx2 = cv.getContext('2d');
    const font = `700 ${fs}px Pretendard, "Apple SD Gothic Neo", sans-serif`;
    ctx2.font = font;
    const linesT = String(l.text).split('\n');
    const w = Math.ceil(Math.max(...linesT.map((s) => ctx2.measureText(s).width))) + pad * 2;
    const lh = fs * 1.25 + (l.ls || 0);
    const h = Math.ceil(lh * linesT.length) + pad * 2;
    cv.width = w; cv.height = h;
    ctx2.font = font; ctx2.textAlign = 'center'; ctx2.textBaseline = 'middle';
    const c = l.col || [1, 1, 1, 1];
    ctx2.fillStyle = `rgba(${c[0] * 255},${c[1] * 255},${c[2] * 255},${c[3]})`;
    linesT.forEach((s, i) => ctx2.fillText(s, w / 2, pad + lh * (i + 0.5)));
    const t = track(new THREE.CanvasTexture(cv));
    t.colorSpace = THREE.SRGBColorSpace;
    const px = l.px || 0.005;
    const geo = track(new THREE.PlaneGeometry(w * px, h * px));
    const mat = track(l.shaded ? new THREE.MeshStandardMaterial({ map: t, transparent: true, roughness: 0.9, side: l.ds ? THREE.DoubleSide : THREE.FrontSide, depthWrite: false })
      : new THREE.MeshBasicMaterial({ map: t, transparent: true, side: l.ds ? THREE.DoubleSide : THREE.FrontSide, depthWrite: false }));
    const mesh = new THREE.Mesh(geo, mat);
    mesh.matrixAutoUpdate = false;
    g.add(mesh);
    return g;
  }

  // Sprite3D (patjuk snow): a textured quad, turned to the camera when billboarded (Godot does it in the shader)
  const _bp = new THREE.Vector3(), _bs = new THREE.Vector3(), _bq = new THREE.Quaternion();
  function buildSprite(sp) {
    const g = new THREE.Group();
    g.matrixAutoUpdate = false;
    if (!sp || sp.tex < 0) return g;
    const px = sp.px || 0.01, w = sp.size[0] * px, h = sp.size[1] * px;
    const geo = track(new THREE.PlaneGeometry(w, h));
    if (!sp.cen) geo.translate(w / 2, h / 2, 0);
    const c = sp.col || [1, 1, 1, 1];
    const mat = track(new THREE.MeshBasicMaterial({ map: texById(sp.tex), transparent: true, alphaTest: sp.alpha ? 0.5 : 0.02,
      depthWrite: false, side: THREE.DoubleSide, color: M.linearColor(c), opacity: c[3] }));
    const mesh = new THREE.Mesh(geo, mat);
    mesh.matrixAutoUpdate = false;
    if (sp.bb) {
      mesh.onBeforeRender = (r, sc, cam) => {
        mesh.parent.matrixWorld.decompose(_bp, _bq, _bs);
        mesh.matrixWorld.compose(_bp, cam.quaternion, _bs);
        mesh.modelViewMatrix.multiplyMatrices(cam.matrixWorldInverse, mesh.matrixWorld);
        mesh.normalMatrix.getNormalMatrix(mesh.modelViewMatrix);
      };
    }
    g.add(mesh);
    return g;
  }

  function variantKey(node, st) {
    if (node.class === 'Sprite3D') return 'spr:' + JSON.stringify(st.spr);
    if (node.class === 'MultiMeshInstance3D') return 'mm:' + (st.mm ? st.mm.mesh : -1) + '|' + st.mo + '|' + st.sh;
    if (node.class === 'Label3D') return 'lbl:' + JSON.stringify(st.lbl);
    return st.mesh + '|' + (st.mats || []).join(',') + '|' + st.mo + '|' + st.sh;
  }
  function ensureVariant(nid, st) {
    const node = D.nodes[nid];
    const rec = getRec(nid);
    const key = variantKey(node, st);
    let v = rec.variants.get(key);
    if (!v) {
      if (node.class === 'MultiMeshInstance3D') v = buildMulti(node, st.mm, st.mo, st.sh);
      else if (node.class === 'Label3D') v = buildLabel(st.lbl);
      else if (node.class === 'Sprite3D') v = buildSprite(st.spr);
      else v = st.mesh >= 0 ? buildMeshGroup(st.mesh, st.mats, st.mo, st.sh) : new THREE.Group();
      rec.variants.set(key, v);
      warmQueue.push(v);
    }
    return v;
  }
  function stFrom(rec) { return { mesh: rec.mesh, mats: rec.mats, mo: rec.mo, sh: rec.sh, mm: rec.mm, lbl: rec.lbl, spr: rec.spr }; }

  function setNode(c) {
    const node = D.nodes[c.n];
    const rec = getRec(c.n);
    if (c.v === false) { rec.obj.visible = false; rec.visible = false; return; }
    if (c.v === true) { rec.obj.visible = true; rec.visible = true; }
    if ('w' in c && c.w !== rec.w) { rec.w = c.w; views[c.w].scene.add(rec.obj); }
    if (c.x) { rec.x = c.x; rec.obj.matrix.fromArray(c.x); rec.obj.matrixWorldNeedsUpdate = true; }
    let rebuild = !rec.cur;
    if ('m' in c) { rec.mesh = c.m; rebuild = true; }
    if ('mats' in c) { rec.mats = c.mats; rebuild = true; }
    if ('mo' in c) { rec.mo = c.mo; rebuild = true; }
    if ('sh' in c) { rec.sh = c.sh; rebuild = true; }
    if ('lbl' in c) { rec.lbl = c.lbl; rebuild = true; }
    if ('spr' in c) { rec.spr = c.spr; rebuild = true; }
    if (!rec.mm && node.mm) rec.mm = node.mm;
    if ('mm' in c && c.mm) { rec.mm = c.mm; if (rec.cur) writeInstances(rec.cur, rec.mm, null, 0); else rebuild = true; }
    if (rebuild) {
      const v = ensureVariant(c.n, stFrom(rec));
      if (rec.cur !== v) {
        if (rec.cur) rec.obj.remove(rec.cur);
        rec.obj.add(v);
        rec.cur = v;
        if (rec.mm && node.class === 'MultiMeshInstance3D') writeInstances(v, rec.mm, null, 0);
      }
    }
  }

  // prebuild: walk a chunk's frames with a shadow state per node and build every variant it will need
  const sim = new Map();
  function simChunk(frs) {
    for (const f of frs) for (const c of f.set || []) {
      if (c.v === false) continue;
      let s = sim.get(c.n);
      if (!s) { s = { mesh: -1, mats: null, mo: -1, sh: 1, mm: D.nodes[c.n].mm || null, lbl: null }; sim.set(c.n, s); }
      let ch = false;
      for (const k of ['mats', 'mo', 'sh', 'lbl', 'spr']) if (k in c) { s[k] = c[k]; ch = true; }
      if ('m' in c) { s.mesh = c.m; ch = true; }
      if ('mm' in c && c.mm) { if (!s.mm || s.mm.mesh !== c.mm.mesh) ch = true; s.mm = c.mm; }
      if (ch || !s.built) { ensureVariant(c.n, s); s.built = true; }
    }
  }

  // warm-up: new variants are drawn once into a tiny target (programs, geometry and textures go to the GPU then,
  // not on the frame they first appear), a few per frame
  const warmQueue = [];
  const texWarm = [];
  const warmRT = new THREE.WebGLRenderTarget(8, 8);
  const warmScene = new THREE.Scene();
  warmScene.add(new THREE.AmbientLight(0xffffff, 1));
  const warmCam = new THREE.PerspectiveCamera(60, 1, 0.01, 1000);
  function warm(budgetMs) {
    const t0 = performance.now();
    while (texWarm.length && performance.now() - t0 < budgetMs * 0.5) { const t = texWarm.shift(); if (t.image) renderer.initTexture(t); }
    if (!warmQueue.length) return;
    const holder = new THREE.Group();
    let n = 0;
    while (warmQueue.length && n < 24 && performance.now() - t0 < budgetMs) {
      const g = warmQueue.shift();
      g.traverse((o) => {
        if (!o.isMesh || o.layers.mask === 2) return;
        const c = o.isInstancedMesh ? new THREE.Mesh(o.geometry, o.material) : o.clone(false);
        c.frustumCulled = false;
        holder.add(c);
        n++;
      });
    }
    if (!n) return;
    warmScene.add(holder);
    warmScene.updateMatrixWorld(true);
    renderer.setRenderTarget(warmRT);
    renderer.render(warmScene, warmCam);
    renderer.setRenderTarget(null);
    warmScene.remove(holder);
  }

  // ------------------------------------------------------------------ timeline state
  const camTracks = { main: [], next: [], book: [] };
  const nodeTracks = new Map();
  const mmTracks = new Map(); // node -> [{t, mm}]
  const waits = [];
  let simExpect = '', simMode = '', simTargets = {}, simPress = false, holdOpen = null;
  const decompose = (x) => {
    const m = new THREE.Matrix4().fromArray(x);
    const p = new THREE.Vector3(), q = new THREE.Quaternion(), s = new THREE.Vector3();
    m.decompose(p, q, s);
    return { p, q, s };
  };
  const camX = {};
  // pack_tale.py writes 12-number transforms (the last column is 0,0,0,1)
  const ex = (x) => (x.length === 12 ? [x[0], x[1], x[2], 0, x[3], x[4], x[5], 0, x[6], x[7], x[8], 0, x[9], x[10], x[11], 1] : x);
  function prepareChunk(frs) {
    for (const f of frs) {
      for (const c of f.set || []) if (c.x) c.x = ex(c.x);
      if (f.cam) for (const vn in f.cam) if (f.cam[vn].x) f.cam[vn].x = ex(f.cam[vn].x);
      for (const l of f.lights || []) if (l.x) l.x = ex(l.x);
    }
    for (const f of frs) {
      if (f.cam) for (const vn in f.cam) {
        const c = f.cam[vn];
        if (c.x) camX[vn] = c.x;
        if (c.x || 'fov' in c) {
          const prev = camTracks[vn][camTracks[vn].length - 1];
          camTracks[vn].push({ t: f.t, ...decompose(camX[vn]), fov: c.fov ?? (prev ? prev.fov : 20) });
        }
      }
      for (const c of f.set || []) {
        if (c.x) {
          if (!nodeTracks.has(c.n)) nodeTracks.set(c.n, []);
          nodeTracks.get(c.n).push({ t: f.t, ...decompose(c.x), cut: 'm' in c || c.v === true });
        }
        if (c.mm) {
          if (!lastXf.has(c.n) && D.nodes[c.n].mm && D.nodes[c.n].mm !== c.mm) resolveMM(c.n, D.nodes[c.n].mm);
          resolveMM(c.n, c.mm);
          if (!mmTracks.has(c.n)) mmTracks.set(c.n, []);
          mmTracks.get(c.n).push({ t: f.t, mm: c.mm });
        }
      }
      // waits: a recorded tap (ripple) while the runner waited for a target or the cover
      const prevExpect = simExpect;
      const prevMode = simMode;
      if ('mode' in f) simMode = f.mode;
      if ('expect' in f) simExpect = f.expect;
      if (f.targets) simTargets = f.targets;
      if ('press' in f) {
        simPress = f.press;
        if (!f.press && holdOpen) { holdOpen.tEnd = f.t; holdOpen = null; }
      }
      const md = prevMode || simMode;
      if (f.rip && md !== 'end' && md !== 'curtain') {
        const rp = f.rip[0];
        if (md === 'blow') {
          const w = { t: f.t, kind: 'hold', target: null, info: null, tEnd: Infinity };
          let best = null, bd = 1e9;
          for (const k in simTargets) { const s = simTargets[k].s; const d = Math.hypot(s[0] - rp[0], s[1] - rp[1]); if (d < bd) { bd = d; best = k; } }
          w.target = best; w.info = best ? simTargets[best] : null;
          if (!w.info && waits.length) w.info = waits[waits.length - 1].info;
          waits.push(w); holdOpen = w;
        } else if (prevExpect !== '' || simExpect !== '' || md === 'cover') {
          const w = { t: f.t, kind: md === 'cover' ? 'cover' : 'tap', target: null, info: null, rip: rp };
          let best = null, bd = 1e9;
          for (const k in simTargets) { const s = simTargets[k].s; const d = Math.hypot(s[0] - rp[0], s[1] - rp[1]); if (d < bd) { bd = d; best = k; } }
          if (w.kind === 'tap') { w.target = best; w.info = best ? simTargets[best] : null; w.offscreen = bd > 200; }
          waits.push(w);
        }
      }
    }
    for (const [n, tr] of nodeTracks) if (tr.length < 2 && !tr.keep) { /* kept: a later chunk may add keys */ }
  }

  // ------------------------------------------------------------------ chunk loading
  const chunkState = []; // 'idle' | 'loading' | 'ready'
  const chunkFrameEnd = [];
  const chunkAudio = [];
  let loadedChunks = 0;
  async function loadChunk(i) {
    const c = idx.chunks[i];
    chunkState[i] = 'loading';
    const [js, bin] = await Promise.all([fetchBuf(TDIR + c.json, 'json'), fetchGz(TDIR + c.bin, 'geo')]);
    if (!alive) return;
    BINS[i] = bin;
    const d = JSON.parse(new TextDecoder().decode(js));
    for (const k of ['textures', 'materials', 'meshes', 'nodes']) for (const e of d[k]) D[k][e.id] = e;
    // textures this chunk introduces: start their downloads now
    for (const e of d.textures) if (e.web) texById(e.id);
    for (const m of d.materials) if (m.prints) for (const p of Object.values(m.prints)) imageTexture(p, false, false);
    const aud = audio.preload(c.audio.map((p) => p));
    for (const f of d.frames) frames.push(f);
    chunkFrameEnd[i] = frames.length;
    prepareChunk(d.frames);
    simChunk(d.frames);
    await aud;
    // the first chunk waits for its pictures; later ones may finish while they play (textures pop in at worst)
    if (i === 0) await Promise.all([...pendingImgs]);
    chunkState[i] = 'ready';
    loadedChunks = i + 1;
    metrics.chunks = loadedChunks;
  }
  async function loadAll(from) {
    for (let i = from; i < idx.chunks.length && alive; i++) {
      if (chunkState[i]) continue;
      await loadChunk(i);
    }
  }

  // ------------------------------------------------------------------ apply
  const lightState = new Map();
  let lightsOn = [];
  let baseView = 'book';
  let ptState = null;
  let ptOldTex = null;
  const snapCanvas = new Map(); // id -> canvas
  let flashState = {};
  let lastCaption = null;
  let tabText = '';
  let endOn = false;
  let ptrOn = false;
  let holdProg = -1;
  let curBeat = '';
  let lastVoicePath = null;
  function applyFrame(f, silent) {
    if (f.views) { /* views shown this frame: their scenes render on demand */ }
    if ('base' in f) baseView = f.base || baseView;
    for (const c of f.set || []) setNode(c);
    for (const mc of f.mat || []) applyMatParams(mc.mat, mc.p);
    if (f.cam) for (const vn in f.cam) {
      const c = f.cam[vn], v = viewBy[vn];
      if ('near' in c) v.cam.near = c.near;
      if ('far' in c) v.cam.far = c.far;
      if (c.dof) {
        v.post.u.dofFar.value.set(c.dof[0] ? 1 : 0, c.dof[1], c.dof[2], 0);
        v.post.u.dofNear.value.set(c.dof[3] ? 1 : 0, c.dof[4], c.dof[5], c.dof[6]);
      }
    }
    if (f.lights) for (const l of f.lights) { const s = lightState.get(l.n) || {}; Object.assign(s, l); lightState.set(l.n, s); }
    if (f.lights_on) lightsOn = f.lights_on;
    if (f.lights || f.lights_on) applyLights();
    if (f.env) for (const vn in f.env) { Object.assign(viewBy[vn].env, f.env[vn]); applyEnv(viewBy[vn]); }
    if (f.rig) for (const vn in f.rig) { Object.assign(viewBy[vn].rig, f.rig[vn]); applyRig(viewBy[vn]); }
    if (f.buses && !silent) audio.setBuses(f.buses);
    else if (f.buses) audio._busList = f.buses;
    if (f.audio) for (const a of f.audio) {
      if (a.ev === 'start' && a.voice) {
        lastVoicePath = a.path;
        const ln = idx.clip_line[a.path];
        if (!silent) metrics.lines.push([ln || a.path, !!audio.buffers.get(a.path), +(f.clock ?? f.t).toFixed(2), a.path]);
      }
      if (silent) audioSilent(a, f.t); else audio.event(a, viewBy[baseView === 'book' ? 'book' : 'main'].camera.position);
    }
    if ('caption' in f) showCaption(f.caption);
    if ('tab' in f) { tabText = f.tab; const el = $('tab'); el.textContent = f.tab; el.classList.toggle('on', !!f.tab); }
    if ('end' in f) endOn = f.end;
    if ('pt' in f) {
      ptState = f.pt && 'p' in f.pt ? f.pt : null;
      if (ptState && ptState.old) ptOldTex = snapTex(ptState.old);
    }
    if ('flash' in f) { flashState = f.flash || {}; showFlash(); }
    if ('ptr' in f) ptrOn = f.ptr;
    if ('hold' in f) holdProg = f.hold;
    if ('beat' in f) { curBeat = f.beat; metrics.beat = f.beat; }
  }

  // silent apply (seeking): remember what loops are running so they can be started where they would be
  const silentLoops = new Map();
  function audioSilent(a, t) {
    if (a.ev === 'start') { if (a.loop) silentLoops.set(a.p, { a, t }); else silentLoops.delete(a.p); }
    else if (a.ev === 'stop') silentLoops.delete(a.p);
    else if (a.ev === 'vol') { const s = silentLoops.get(a.p); if (s) s.a = { ...s.a, vol: a.vol }; }
  }

  function applyLights() {
    // per view: the key (shadowed directional), the fill (unshadowed directional), omni lights
    const perView = [[], [], []];
    for (const n of lightsOn) { const l = lightState.get(n); if (l) perView[l.w].push(l); }
    perView.forEach((ls, vi) => {
      const v = views[vi];
      let haveKey = false, haveFill = false;
      const seenOmni = new Set();
      for (const l of ls) {
        const x = l.x;
        if (l.class === 'OmniLight3D' || l.class === 'SpotLight3D') {
          let o = v.omnis.get(l.n);
          if (!o) { o = new THREE.PointLight(0xffffff, 1, 1, l.atten ?? 1); o.castShadow = false; v.scene.add(o); v.omnis.set(l.n, o); }
          o.visible = true;
          o.position.set(x[12], x[13], x[14]);
          o.color.copy(M.linearColor(l.color));
          o.distance = l.range || 5;
          o.decay = l.atten ?? 1;
          o.intensity = l.energy * Math.PI * TUNE.omni;
          seenOmni.add(l.n);
          continue;
        }
        const dir = new THREE.Vector3(-x[8], -x[9], -x[10]).normalize();
        const col = M.linearColor(l.color);
        if (/fill/i.test(l.name) || (haveKey && !l.shadow)) {
          v.fillDir.copy(dir); v.fill.color.copy(col); v.fill.intensity = l.energy * Math.PI; haveFill = true;
        } else {
          v.keyDir.copy(dir); v.key.color.copy(col); v.key.intensity = l.energy * Math.PI * TUNE.key;
          v.shadowOpacity = l.opacity ?? 1;
          v.key.castShadow = !!l.shadow;
          v.keyColor.copy(col); v.keyEnergy = l.energy;
          haveKey = true;
        }
      }
      if (!haveKey) v.key.intensity = 0;
      if (!haveFill) v.fill.intensity = 0;
      for (const [n, o] of v.omnis) if (!seenOmni.has(n)) o.visible = false;
    });
  }
  function applyEnv(v) {
    const e = v.env, u = v.post.u;
    if (e.ambient_light_color) { v.ambient.color.copy(M.linearColor(e.ambient_light_color)); v.ambient.intensity = (e.ambient_light_energy ?? 1) * Math.PI * TUNE.amb; }
    if (e.background_color) v.clear.copy(M.linearColor(e.background_color));
    u.exposure.value = e.tonemap_exposure ?? 1;
    u.adjust.value.set(e.adjustment_enabled ? e.adjustment_brightness : 1, e.adjustment_enabled ? e.adjustment_contrast : 1, e.adjustment_enabled ? e.adjustment_saturation : 1);
    u.fogOn.value = e.fog_enabled && TUNE.fog > 0 ? 1 : 0;
    if (e.fog_light_color) {
      u.fogBegin.value = e.fog_depth_begin; u.fogEnd.value = e.fog_depth_end;
      u.fogDensity.value = e.fog_density * TUNE.fog; u.fogCurve.value = e.fog_depth_curve;
      u.fogColor.value.copy(M.linearColor(e.fog_light_color)).multiplyScalar(e.fog_light_energy ?? 1);
    }
    u.glow.value.set(e.glow_enabled ? e.glow_intensity * TUNE.glow : 0, (e.glow_bloom ?? 0) * TUNE.glow, e.glow_hdr_threshold ?? 1);
  }
  function applyRig(v) {
    const r = v.rig, u = v.post.u;
    if (r.distance) v.rigDistance = r.distance;
    for (const k of ['focus_y', 'band_half', 'band_soft', 'max_lod', 'base_lod', 'top_bias', 'vignette', 'grade', 'saturation', 'contrast', 'lift', 'grain', 'toe']) {
      if (('post.' + k) in r) u[k].value = r['post.' + k];
    }
    if (r['post.shadow_tint']) u.shadow_tint.value.set(...r['post.shadow_tint'].slice(0, 3));
    if (r['post.highlight_tint']) u.highlight_tint.value.set(...r['post.highlight_tint'].slice(0, 3));
    u.postOn.value = r.post_visible === false || !('post_visible' in r) ? 0 : 1;
  }

  // ------------------------------------------------------------------ interpolation
  function sampleTrack(tr, t, out) {
    let lo = 0, hi = tr.length - 1;
    if (hi < 0) return null;
    if (t <= tr[0].t) return tr[0];
    if (t >= tr[hi].t) return tr[hi];
    while (hi - lo > 1) { const mid = (lo + hi) >> 1; if (tr[mid].t <= t) lo = mid; else hi = mid; }
    const a = tr[lo], b = tr[hi];
    if (b.t - a.t > 0.05 || b.cut) return a;
    const k = (t - a.t) / (b.t - a.t);
    out.p.lerpVectors(a.p, b.p, k); out.q.slerpQuaternions(a.q, b.q, k); out.s.lerpVectors(a.s, b.s, k);
    if (a.fov !== undefined) out.fov = a.fov + (b.fov - a.fov) * k;
    return out;
  }
  const tmp = { p: new THREE.Vector3(), q: new THREE.Quaternion(), s: new THREE.Vector3(), fov: 20 };
  const tmpN = { p: new THREE.Vector3(), q: new THREE.Quaternion(), s: new THREE.Vector3() };
  function updateMotion() {
    for (const v of views) {
      const c = sampleTrack(camTracks[v.name], T, tmp);
      if (!c) continue;
      v.camera.position.copy(c.p); v.camera.quaternion.copy(c.q);
      v.camera.fov = c.fov; v.camera.near = v.cam.near; v.camera.far = v.cam.far;
      v.camera.updateProjectionMatrix();
      v.camera.updateMatrixWorld(true);
    }
    for (const [n, tr] of nodeTracks) {
      if (tr.length < 2) continue;
      const rec = nodeObj.get(n);
      if (!rec || !rec.visible) continue;
      const s = sampleTrack(tr, T, tmpN);
      rec.obj.matrix.compose(s.p, s.q, s.s);
      rec.obj.matrixWorldNeedsUpdate = true;
    }
    // MultiMesh keys (10 fps during folds / pop-ups): instance matrices interpolated between kept dumps
    for (const [n, tr] of mmTracks) {
      const rec = nodeObj.get(n);
      if (!rec || !rec.visible || !rec.cur || tr.length < 2) continue;
      let lo = 0, hi = tr.length - 1;
      if (T <= tr[0].t || T >= tr[hi].t) continue;
      while (hi - lo > 1) { const mid = (lo + hi) >> 1; if (tr[mid].t <= T) lo = mid; else hi = mid; }
      const a = tr[lo], b = tr[hi];
      if (b.t - a.t > 0.11 || a.mm.n !== b.mm.n || a.mm.mesh !== b.mm.mesh) continue;
      writeInstances(rec.cur, a.mm, b.mm, (T - a.t) / (b.t - a.t));
    }
  }
  function fitShadow(v) {
    const cam = v.camera;
    const fwd = new THREE.Vector3(0, 0, -1).applyQuaternion(cam.quaternion);
    const focus = cam.position.clone().addScaledVector(fwd, v.rigDistance);
    const halfH = Math.tan(THREE.MathUtils.degToRad(cam.fov / 2)) * v.rigDistance;
    const r = Math.min(Math.max(halfH * cam.aspect * 1.6, 1.2), 9);
    v.key.target.position.copy(focus);
    v.key.position.copy(focus).addScaledVector(v.keyDir, -20);
    const sc = v.key.shadow.camera;
    sc.left = -r; sc.right = r; sc.top = r; sc.bottom = -r; sc.near = 1; sc.far = 45;
    sc.updateProjectionMatrix();
    v.fill.target.position.copy(focus);
    v.fill.position.copy(focus).addScaledVector(v.fillDir, -20);
    v.key.shadow.intensity = v.shadowOpacity;
  }

  // ------------------------------------------------------------------ UI
  function showCaption(txt) {
    if (txt === lastCaption) return;
    lastCaption = txt;
    const el = $('cap');
    if (!txt) { el.classList.remove('on'); return; }
    const bold = /\[b\]/.test(txt);
    const parts = txt.split('|').map((s) => s.replace(/\[[^\]]*\]/g, '').replace(/⁠/g, '').trim()).filter(Boolean);
    const text = parts.pop() || '';
    const chip = parts.join(' ');
    el.innerHTML = '';
    if (chip) { const s = document.createElement('span'); s.className = 'chip'; s.textContent = chip; el.appendChild(s); }
    const s2 = document.createElement(bold ? 'b' : 'span'); s2.className = 'txt'; s2.textContent = text; el.appendChild(s2);
    el.classList.add('on');
  }
  // Godot UI is laid out at 1366x1024 (keep height): map its px to CSS px
  const gscale = () => window.innerHeight / (idx ? idx.viewport[1] : 1024);
  const gx = (x) => (window.innerWidth - (idx ? idx.viewport[0] : 1366) * gscale()) / 2 + x * gscale();
  function showFlash() {
    const box = $('flash');
    box.innerHTML = '';
    for (const side in flashState) {
      const f = flashState[side];
      const card = document.createElement('div');
      card.className = 'flashcard';
      const sc = gscale();
      card.style.left = gx(f.rect[0]) + 'px'; card.style.top = f.rect[1] * sc + 'px';
      card.style.width = f.rect[2] * sc + 'px'; card.style.height = f.rect[3] * sc + 'px';
      card.style.transform = `rotate(${f.rot}rad)`;
      const cv = snapCanvas.get(f.snap);
      if (cv) { const img = document.createElement('canvas'); img.width = cv.width; img.height = cv.height; img.getContext('2d').drawImage(cv, 0, 0); card.appendChild(img); }
      const lb = document.createElement('div'); lb.className = side === 'left' ? 'lbl l' : 'lbl r'; lb.textContent = f.label; card.appendChild(lb);
      box.appendChild(card);
    }
  }
  function snapTex(id) {
    const cv = snapCanvas.get(id);
    if (!cv) return null;
    if (!cv._tex) { cv._tex = track(new THREE.CanvasTexture(cv)); cv._tex.colorSpace = THREE.NoColorSpace; cv._tex.flipY = true; }
    return cv._tex;
  }
  function captureSnap(id) {
    if (snapCanvas.has(id)) return;
    const src = renderer.domElement;
    const cv = document.createElement('canvas');
    cv.width = src.width; cv.height = src.height;
    cv.getContext('2d').drawImage(src, 0, 0);
    snapCanvas.set(id, cv);
  }

  const ring = $('ring');
  function ringTarget() {
    const w = waits[wi];
    if (!w || w.kind === 'cover') return null;
    if (holding === w || (ptrOn && w.t - T < 4 && w.t >= T)) return w;
    return null;
  }
  function updateRing() {
    const w = ringTarget();
    const info = w && w.info;
    if (!info || w.offscreen) { ring.style.display = 'none'; ring.dataset.r = 0; return; }
    const cam = viewBy.main.camera;
    const p = new THREE.Vector3(...info.p).project(cam);
    const x = (p.x * 0.5 + 0.5) * window.innerWidth, y = (-p.y * 0.5 + 0.5) * window.innerHeight;
    const r = Math.max(info.r * gscale() * (w.target === 'traveller' ? 1.0 : 1.3), 36);
    ring.style.display = 'block';
    ring.classList.toggle('hold', w.kind === 'hold');
    ring.style.left = x - r + 'px'; ring.style.top = y - r + 'px';
    ring.style.width = ring.style.height = 2 * r + 'px';
    ring.dataset.x = x; ring.dataset.y = y; ring.dataset.r = r;
    if (w.kind === 'hold' && holdProg >= 0) ring.style.setProperty('--fill', holdProg); else ring.style.setProperty('--fill', 0);
  }

  // ------------------------------------------------------------------ play loop
  let T = 0, fi = 0, wi = 0;
  let holding = null, holdStart = 0, pressed = false;
  let running = false, finished = false, stalled = false, stallT0 = 0;
  let tEnd = 0;
  function nextWait() { while (wi < waits.length && waits[wi].done) wi++; return waits[wi]; }
  function resolveWait(w, how) {
    if (!w || w.done) return;
    w.done = true;
    if (holding === w) holding = null;
    metrics.tapped.push([w.kind, w.target, how, +T.toFixed(2)]);
    metrics.tapAt = T;
    if (w.kind !== 'hold') nextWait();
  }
  function advance(dt) {
    if (finished) return;
    const w = nextWait();
    if (holding) {
      if (holding.kind === 'hold' && pressed) {
        holding.done = true; holding.active = true; metrics.tapped.push(['hold', holding.target, 'press', +T.toFixed(2)]); holding = null;
      } else {
        if (lastVoicePath && performance.now() - holdStart > 9000) { holdStart = performance.now(); audio.event({ ev: 'start', p: -7, path: lastVoicePath, vol: 0, bus: 'Voice' }); }
        return;
      }
    }
    // a hold step runs only while the finger is down
    const hw = waits.find((x) => x.kind === 'hold' && x.active && T >= x.t && T < x.tEnd);
    if (hw && !pressed && !AUTO) return;
    let nT = T + dt;
    if (w && !w.done && nT >= w.t - 1 / FPS) {
      nT = Math.max(T, w.t - 1 / FPS);
      holding = w; holdStart = performance.now();
      if (AUTO) setTimeout(() => { if (w.kind === 'hold') { pressed = true; setTimeout(() => { pressed = false; }, (w.tEnd - w.t) * 1000 + 50); } resolveWait(w, 'auto'); }, 0); // the recording already holds autoplay's pause before its tap
    }
    // never run past what is loaded
    const loadedEnd = frames.length ? frames[frames.length - 1].t : 0;
    if (loadedChunks < idx.chunks.length && nT > loadedEnd - 0.05) {
      if (!stalled) { stalled = true; stallT0 = performance.now(); metrics.stalls++; $('spin').classList.add('on'); }
      return;
    }
    if (stalled) { stalled = false; metrics.stallMs += performance.now() - stallT0; $('spin').classList.remove('on'); }
    T = nT;
    while (fi < frames.length && frames[fi].t <= T) applyFrame(frames[fi++], false);
    if (T >= tEnd) finish();
  }

  function finish() {
    if (finished) return;
    finished = true;
    metrics.state = 'done';
    metrics.doneAt = T;
    metrics.lineCheck = lineCheck();
    $('endcard').classList.add('on');
  }
  // every line the runner said in the export run (Godot's LINE list) must have started one of its voice clips, with a
  // decoded buffer, at the same story time (within 0.5 s); a line split over steps prints LINE per part: each part
  function lineCheck() {
    const voiced = [];
    for (const [ln, ok, t, path] of metrics.lines) voiced.push({ path, ok, t, used: false });
    const missing = [], noBuffer = [];
    let n = 0, unvoiced = 0;
    for (const [id, t] of idx.lines) {
      const clips = (idx.line_clips || {})[id];
      if (!clips) { unvoiced++; continue; }
      n++;
      const hit = voiced.find((v) => !v.used && clips.includes(v.path) && Math.abs(v.t - t) < 0.5);
      if (!hit) { missing.push(id + '@' + t); continue; }
      hit.used = true;
      if (!hit.ok) noBuffer.push(id);
    }
    const extra = voiced.filter((v) => !v.used && Math.abs(v.t) >= 0).length; // later segments of multi-seg lines
    return { godotLines: idx.lines.length, voicedLines: n, matched: n - missing.length, inOrder: missing.length === 0 && noBuffer.length === 0,
      webLines: n - missing.length, missing, noBuffer, unvoiced, otherVoiceStarts: extra };
  }

  function render(now) {
    const bv = viewBy[baseView] || viewBy.main;
    // the next page during a live turn: rendered (with its own grade) into rtNew, shown right of the fold
    const newView = ptState && ptState.new && viewBy[ptState.new] ? viewBy[ptState.new] : null;
    if (newView) renderView(newView, rtNew, now);
    renderView(bv, null, now);
    if (ptState) {
      turn.u.progress.value = ptState.p;
      turn.u.hasOld.value = ptOldTex ? 1 : 0;
      turn.u.tOld.value = ptOldTex;
      turn.u.hasNew.value = newView ? 1 : 0;
      turn.u.gscale.value = (window.innerHeight * DPR) / (idx ? idx.viewport[1] : 1024);
      renderer.autoClear = false;
      renderer.render(turn.scene, turn.cam);
      renderer.autoClear = true;
    }
  }
  function renderView(v, target, now) {
    fitShadow(v);
    M.shared.keyDirView.value.copy(v.keyDir).negate().transformDirection(v.camera.matrixWorldInverse);
    M.shared.keyColor.value.copy(v.keyColor).multiplyScalar(v.keyEnergy);
    renderer.setClearColor(v.clear, 1);
    renderer.setRenderTarget(rt);
    renderer.render(v.scene, v.camera);
    renderer.setRenderTarget(target);
    const th = Math.tan(THREE.MathUtils.degToRad(v.camera.fov / 2));
    v.post.u.tanHalf.value.set(th * v.camera.aspect, th);
    v.post.u.cNear.value = v.camera.near; v.post.u.cFar.value = v.camera.far; v.post.u.time.value = now / 1000;
    renderer.render(v.post.scene, v.post.cam);
    renderer.setRenderTarget(null);
  }

  let last = 0, raf = 0, firstFrame = false;
  function loop(now) {
    if (!alive) return;
    raf = requestAnimationFrame(loop);
    const dt = last ? Math.min((now - last) / 1000, 0.1) : 1 / 60;
    if (last && running && !holding && !stalled) metrics.frames.push(now - last);
    last = now;
    if (metrics.frames.length > 40000) metrics.frames.splice(0, 20000);
    renderer.info.reset();
    if (running) advance(dt);
    M.shared.time.value += dt;
    M.shared.wind.value.x += dt;
    metrics.t = T;
    updateMotion();
    warm(5);
    render(now);
    // snapshots the next frames need (the page about to turn, a flashback card): taken from this finished frame
    for (let k = fi; k < Math.min(frames.length, fi + 4); k++) {
      const f = frames[k];
      if (f.pt && f.pt.old && !snapCanvas.has(f.pt.old)) captureSnap(f.pt.old);
      if (f.snap) for (const id of f.snap) captureSnap(id);
    }
    updateRing();
    if (!firstFrame) { firstFrame = true; metrics.firstFrameMs = Math.round(performance.now() - T0); }
  }

  // ------------------------------------------------------------------ input
  function onDown(e) {
    audio.unlock();
    pressed = true;
    ripple(e.clientX, e.clientY);
    const w = holding;
    if (!w) return;
    if (w.kind === 'cover') { resolveWait(w, 'tap'); return; }
    if (w.kind === 'hold') return; // advance() sees `pressed`
    const x = Number(ring.dataset.x), y = Number(ring.dataset.y), r = Number(ring.dataset.r);
    if (w.offscreen || !r || Math.hypot(e.clientX - x, e.clientY - y) <= r * 1.35) resolveWait(w, 'tap');
  }
  function onUp() { pressed = false; }
  function ripple(x, y) {
    const d = document.createElement('div');
    d.className = 'ripple'; d.style.left = x + 'px'; d.style.top = y + 'px';
    document.body.appendChild(d);
    setTimeout(() => d.remove(), 650);
  }
  const canvas = renderer.domElement;
  canvas.addEventListener('pointerdown', onDown);
  window.addEventListener('pointerup', onUp);
  window.addEventListener('pointercancel', onUp);

  // ------------------------------------------------------------------ start
  function dispose() {
    alive = false;
    cancelAnimationFrame(raf);
    audio.stopAll();
    canvas.removeEventListener('pointerdown', onDown);
    window.removeEventListener('pointerup', onUp);
    window.removeEventListener('pointercancel', onUp);
    window.removeEventListener('resize', resize);
    for (const o of disposables) { try { o.dispose(); } catch (e) { /* gone */ } }
    for (const v of views) { v.key.shadow.map?.dispose(); }
    if (rt) { rt.depthTexture.dispose(); rt.dispose(); rtNew.dispose(); }
    warmRT.dispose();
    renderer.renderLists.dispose();
    for (const id of ['cap', 'tab', 'flash']) { const el = $(id); el.classList.remove('on'); if (id === 'flash') el.innerHTML = ''; }
    $('endcard').classList.remove('on');
    $('spin').classList.remove('on');
    ring.style.display = 'none';
  }

  idx = JSON.parse(new TextDecoder().decode(await fetchBuf(TDIR + 'index.json', 'json')));
  metrics.chunksTotal = idx.chunks.length;
  tEnd = Math.min((idx.done_at ?? idx.chunks[idx.chunks.length - 1].t1) + 0.8, idx.chunks[idx.chunks.length - 1].t1);
  metrics.timeline = { tEnd, chunks: idx.chunks.map((c) => [c.id, c.t0]) };
  // which chunk to start in (?beat=)
  let startChunk = 0;
  if (opt.beat) { const k = idx.chunks.findIndex((c) => c.id === opt.beat); if (k >= 0) startChunk = k; }
  for (let i = 0; i <= startChunk; i++) await loadChunk(i);
  if (!alive) return { dispose };
  loadAll(startChunk + 1).catch((e) => app.errors.push(String(e)));
  // apply up to the start: the opening frame, or silently up to the beat
  if (startChunk > 0) {
    const t0 = idx.chunks[startChunk].t0;
    while (fi < frames.length && frames[fi].t < t0) applyFrame(frames[fi++], true);
    T = t0 - 1 / FPS;
    for (const w of waits) if (w.t < t0) w.done = true;
    if (audio._busList) audio.setBuses(audio._busList);
  } else {
    T = frames[0].t;
    applyFrame(frames[fi++], true);
  }
  metrics.loadMs = Math.round(performance.now() - T0);
  metrics.ready = true;
  metrics.state = 'playing';
  metrics.waits = waits.length;
  metrics.unknownShaders = () => [...unknownShaders];
  raf = requestAnimationFrame(loop);
  running = true;
  // loops already running at a seek point start where they would be
  for (const { a, t } of silentLoops.values()) audio.event({ ...a, at: ((a.at || 0) + (T - t)) % Math.max(a.dur || 1, 0.1) }, viewBy.main.camera.position);
  silentLoops.clear();

  if (Q.has('debug')) window.__dbg = { views, nodeObj, D, matCache, THREE, renderer };
  metrics.waitList = () => waits.map((w) => [w.kind, w.target, +w.t.toFixed(2), !!w.done]);
  metrics.ringAt = () => ({ x: +ring.dataset.x, y: +ring.dataset.y, r: +ring.dataset.r, kind: holding && holding.kind, target: holding && holding.target });
  metrics.holding = () => (holding ? holding.kind : '');
  metrics.audioLog = () => audio.log;
  // tests / compare sheet: jump to a record time and hold there (no audio)
  metrics.seek = async (t) => {
    while (frames.length === 0 || (frames[frames.length - 1].t < t && loadedChunks < idx.chunks.length)) await new Promise((r) => setTimeout(r, 100));
    running = false;
    audio.stopAll();
    if (t < T) { return 'backward seek: reload the page'; }
    while (fi < frames.length && frames[fi].t <= t) applyFrame(frames[fi++], true);
    T = t;
    silentLoops.clear();
    for (const w of waits) if (w.t <= t) w.done = true;
    holding = null;
    await Promise.all([...pendingImgs]);
    for (let i = 0; i < 30 && warmQueue.length; i++) warm(30);
    return { T, base: baseView, pt: ptState };
  };
  setInterval(() => {
    if (!alive) return;
    const i = renderer.info;
    let geoBytes = 0;
    for (const a of attrCache.values()) geoBytes += a.array.byteLength;
    const rtBytes = rt ? rt.width * rt.height * (8 * 1.33 + 4) * (MSAA > 0 ? 1 + MSAA * 0.5 : 1) + rt.width * rt.height * 4 : 0;
    metrics.info = { calls: i.render.calls, triangles: i.render.triangles, textures: i.memory.textures, geometries: i.memory.geometries, programs: i.programs ? i.programs.length : 0 };
    metrics.gpuMB = Math.round((texBytes + geoBytes + rtBytes + SHADOW * SHADOW * 4 * 2 + 1024 * 1024 * 4) / 1048576);
    metrics.texMB = Math.round(texBytes / 1048576);
    metrics.geoMB = Math.round(geoBytes / 1048576);
    metrics.audio = { state: audio.ctx ? audio.ctx.state : 'none', started: audio.started, playing: audio.voices.size, bytes: audio.bytes };
    if (Q.has('hud')) $('hud').textContent = `${metrics.info.calls} calls  ${(metrics.info.triangles / 1000).toFixed(0)}k tris  ~${metrics.gpuMB} MB gpu  t=${T.toFixed(1)} ${curBeat} c${loadedChunks}/${idx.chunks.length}`;
  }, 1000);
  return { dispose, metrics };
}
