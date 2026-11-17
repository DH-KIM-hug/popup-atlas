import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { TILE_TYPES } from './TileDefs';

export interface Kit {
  tiles: Map<string, THREE.Object3D>;
  traveller: THREE.Object3D;
  source: 'glb' | 'placeholder';
}

/** Loads public/models/kit.glb (contract in artifacts/game-progress.md). Falls back to a bare placeholder kit. */
export async function loadKit(url = `${import.meta.env.BASE_URL}models/kit.glb`): Promise<Kit> {
  try {
    const gltf = await new GLTFLoader().loadAsync(url);
    const tiles = new Map<string, THREE.Object3D>();
    let traveller: THREE.Object3D | undefined;
    gltf.scene.traverse((o) => {
      if (o.name.startsWith('tile_') && !tiles.has(o.name.slice(5))) tiles.set(o.name.slice(5), o);
      if (o.name === 'traveller') traveller = o;
    });
    const missing = TILE_TYPES.filter((t) => !tiles.has(t.name)).map((t) => t.name);
    if (missing.length) console.warn('[kit] missing tiles, using placeholders:', missing);
    const fallback = placeholderKit();
    for (const name of missing) tiles.set(name, fallback.tiles.get(name)!);
    for (const [, root] of tiles) prepare(root);
    if (traveller) prepare(traveller);
    return { tiles, traveller: traveller ?? fallback.traveller, source: 'glb' };
  } catch (error) {
    console.warn('[kit] kit.glb not available, using placeholder kit', error);
    return placeholderKit();
  }
}

function prepare(root: THREE.Object3D): void {
  root.removeFromParent();
  root.position.set(0, 0, 0);
  root.traverse((o) => {
    const mesh = o as THREE.Mesh;
    if (!mesh.isMesh) return;
    const isPrint = o.name.startsWith('print') || o.parent?.name.startsWith('print');
    mesh.castShadow = !isPrint;
    mesh.receiveShadow = true;
    for (const m of Array.isArray(mesh.material) ? mesh.material : [mesh.material]) {
      const std = m as THREE.MeshStandardMaterial;
      if (std.isMeshStandardMaterial) {
        std.metalness = 0;
        std.roughness = Math.max(std.roughness, 0.82);
        if (isPrint) {
          std.polygonOffset = true;
          std.polygonOffsetFactor = -1;
          std.polygonOffsetUnits = -1;
        }
      }
    }
  });
}

// Bare placeholder so the engine runs before the Blender kit exists. Not the shipped art.
function placeholderKit(): Kit {
  const card = (c: string) => new THREE.MeshStandardMaterial({ color: c, roughness: 0.9 });
  const tiles = new Map<string, THREE.Object3D>();
  const flat = (color: string) => {
    const m = new THREE.Mesh(new THREE.PlaneGeometry(0.96, 0.96), card(color));
    m.rotation.x = -Math.PI / 2;
    m.position.y = 0.002;
    m.name = 'print';
    return m;
  };
  const pop = (w: number, h: number, color: string, z: number, order: number) => {
    const hinge = new THREE.Group();
    hinge.name = 'pop';
    hinge.userData = { fold: 1, order };
    hinge.position.z = z;
    const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, 0.012), card(color));
    m.position.y = h / 2;
    hinge.add(m);
    return hinge;
  };
  for (const t of TILE_TYPES) {
    const root = new THREE.Group();
    root.name = `tile_${t.name}`;
    const water = t.name.startsWith('river') || t.name === 'bridge';
    root.add(flat(water ? '#7fa7a4' : t.name.startsWith('path') ? '#d9c39a' : '#c9cf9d'));
    if (t.name === 'trees') root.add(pop(0.3, 0.5, '#7d9a6a', -0.1, 0), pop(0.25, 0.38, '#5f7d55', 0.15, 0.4));
    if (t.name === 'house') root.add(pop(0.45, 0.45, '#c46e4d', 0, 0));
    if (t.name === 'hill') root.add(pop(0.8, 0.3, '#a8b37a', 0, 0));
    if (t.name === 'bridge') root.add(pop(0.9, 0.18, '#a7764f', 0, 0));
    prepare(root);
    tiles.set(t.name, root);
  }
  const traveller = new THREE.Group();
  traveller.name = 'traveller';
  const body = new THREE.Mesh(new THREE.ConeGeometry(0.06, 0.15, 12), card('#b8613f'));
  body.position.y = 0.1;
  body.name = 'body';
  const head = new THREE.Mesh(new THREE.SphereGeometry(0.04, 12, 8), card('#efe3c8'));
  head.position.y = 0.2;
  head.name = 'head';
  traveller.add(body, head);
  prepare(traveller);
  return { tiles, traveller, source: 'placeholder' };
}
