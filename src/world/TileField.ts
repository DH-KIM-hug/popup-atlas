import * as THREE from 'three';
import { VARIANTS } from './TileDefs';
import type { Kit } from './Kit';
import type { Wfc } from './Wfc';

/** A hinged piece of card. angle 0 = standing (rest pose), flat = lying on the page. */
interface Piece {
  node: THREE.Object3D;
  rest: THREE.Quaternion;
  flat: number;
  order: number;
  angle: number;
  vel: number;
  // per-piece spring character, so a field of folds never moves in lockstep
  k: number;
  c: number;
}

interface Tile {
  x: number;
  z: number;
  root: THREE.Object3D;
  pieces: Piece[];
  up: boolean;
  /** time when the current fold (up or down) started */
  since: number;
  /** obstacle rectangles in world XZ (min x, min z, max x, max z) while standing */
  blocks: [number, number, number, number][];
  sounded: boolean;
}

export interface FoldEvent {
  x: number;
  z: number;
  up: boolean;
  size: number;
}

const AXIS_X = new THREE.Vector3(1, 0, 0);
const tmpQ = new THREE.Quaternion();

export interface FieldTuning {
  /** natural frequency of the fold spring, Hz */
  freq: number;
  /** damping ratio (< 1 overshoots) */
  zeta: number;
  riseAhead: number;
  riseBehind: number;
  showRadius: number;
}

export class TileField {
  readonly group = new THREE.Group();
  private readonly tiles = new Map<string, Tile>();
  private time = 0;
  readonly tuning: FieldTuning = { freq: 2.1, zeta: 0.3, riseAhead: 6.2, riseBehind: 2.6, showRadius: 13 };
  events: FoldEvent[] = [];

  constructor(
    private readonly kit: Kit,
    private readonly wfc: Wfc,
    private readonly rng: () => number,
  ) {}

  /** Tiles whose standing card blocks the traveller at (x, z). */
  blocked(x: number, z: number, r: number): boolean {
    const cx = Math.round(x);
    const cz = Math.round(z);
    for (let dz = -1; dz <= 1; dz++) {
      for (let dx = -1; dx <= 1; dx++) {
        const t = this.tiles.get(`${cx + dx},${cz + dz}`);
        if (!t || !t.up) continue;
        for (const [ax, az, bx, bz] of t.blocks) {
          if (x > ax - r && x < bx + r && z > az - r && z < bz + r) return true;
        }
      }
    }
    return false;
  }

  /** How far up the tile at a cell stands, 0 flat .. 1 standing (for diagnostics/tests). */
  standing(): { up: number; total: number; moving: number } {
    let up = 0;
    let moving = 0;
    for (const t of this.tiles.values()) {
      if (t.up) up++;
      if (t.pieces.some((p) => Math.abs(p.vel) > 0.05)) moving++;
    }
    return { up, total: this.tiles.size, moving };
  }

  update(dt: number, px: number, pz: number, fx: number, fz: number): void {
    this.time += dt;
    const { riseAhead, riseBehind, showRadius } = this.tuning;
    this.wfc.generate(px, pz, showRadius + 3);

    // Spawn printed tiles within the visible radius; drop far ones.
    const r2 = showRadius * showRadius;
    for (let z = Math.floor(pz - showRadius); z <= Math.ceil(pz + showRadius); z++) {
      for (let x = Math.floor(px - showRadius); x <= Math.ceil(px + showRadius); x++) {
        const dx = x - px;
        const dz = z - pz;
        if (dx * dx + dz * dz > r2) continue;
        const k = `${x},${z}`;
        if (!this.tiles.has(k)) this.spawn(x, z);
      }
    }
    for (const [k, t] of this.tiles) {
      const dx = t.x - px;
      const dz = t.z - pz;
      if (dx * dx + dz * dz > (showRadius + 2) ** 2) {
        t.root.removeFromParent();
        this.tiles.delete(k);
      }
    }

    // Rise ahead, fold behind. Reach depends on where the traveller faces; hysteresis avoids flutter.
    for (const t of this.tiles.values()) {
      const dx = t.x - px;
      const dz = t.z - pz;
      const d = Math.hypot(dx, dz);
      const cos = d > 1e-3 ? (dx * fx + dz * fz) / d : 1;
      const reach = riseBehind + (riseAhead - riseBehind) * (0.5 + 0.5 * cos);
      if (!t.up && d < reach - 0.4) this.setUp(t, true, d);
      else if (t.up && d > reach + 0.6) this.setUp(t, false, d);
      this.step(t, dt);
    }
  }

  private setUp(t: Tile, up: boolean, d: number): void {
    t.up = up;
    // Nearer tiles go first; a little jitter so a row doesn't snap up like a fence.
    t.since = this.time + (up ? Math.max(0, d - 1.5) * 0.06 : 0) + this.rng() * 0.12;
    t.sounded = false;
  }

  private step(t: Tile, dt: number): void {
    const elapsed = this.time - t.since;
    let moving = false;
    for (const p of t.pieces) {
      const delay = p.order * 0.28;
      const target = t.up && elapsed > delay ? 0 : t.up ? p.flat : elapsed > delay * 0.5 ? p.flat : 0;
      if (elapsed < 0 && !t.up) continue;
      // Semi-implicit Euler, sub-stepped for stability at low frame rates.
      const n = Math.ceil(dt / (1 / 240));
      const h = dt / n;
      for (let i = 0; i < n; i++) {
        const acc = -p.k * (p.angle - target) - p.c * p.vel;
        p.vel += acc * h;
        p.angle += p.vel * h;
        // The page stops a falling card: slap and settle instead of passing through.
        if (Math.sign(p.flat) * (p.angle - p.flat) > 0) {
          p.angle = p.flat;
          p.vel = -p.vel * 0.22;
        }
      }
      if (Math.abs(p.vel) > 0.02 || Math.abs(p.angle - target) > 0.002) moving = true;
      tmpQ.setFromAxisAngle(AXIS_X, p.angle);
      p.node.quaternion.copy(p.rest).multiply(tmpQ);
    }
    if (!t.sounded && elapsed > 0 && t.pieces.length) {
      t.sounded = true;
      this.events.push({ x: t.x, z: t.z, up: t.up, size: t.pieces.length });
    }
    if (!moving && !t.up) {
      for (const p of t.pieces) p.vel = 0;
    }
  }

  private spawn(x: number, z: number): void {
    const v = this.wfc.get(x, z);
    if (v === undefined) return;
    this.wfc.lock(x, z);
    const variant = VARIANTS[v];
    const proto = this.kit.tiles.get(variant.type.name);
    if (!proto) return;
    const root = proto.clone(true);
    root.position.set(x, 0, z);
    root.rotation.y = -variant.rot * (Math.PI / 2);
    this.group.add(root);
    root.updateMatrixWorld(true);

    const pieces: Piece[] = [];
    const blocks: [number, number, number, number][] = [];
    const box = new THREE.Box3();
    root.traverse((o) => {
      const fold = o.userData?.fold;
      if (typeof fold !== 'number') return;
      // Footprint while standing: only top-level pieces block, and only where they rise above ankle height.
      if (!isInsidePiece(o)) {
        box.setFromObject(o);
        if (box.max.y > 0.05) blocks.push([box.min.x, box.min.z, box.max.x, box.max.z]);
      }
      const omega = 2 * Math.PI * this.tuning.freq * (0.88 + this.rng() * 0.24);
      const zeta = this.tuning.zeta * (0.85 + this.rng() * 0.3);
      const flat = Math.sign(fold || 1) * (Math.PI / 2 - 0.01);
      pieces.push({
        node: o,
        rest: o.quaternion.clone(),
        flat,
        order: Math.min(1, Math.max(0, Number(o.userData.order ?? 0))),
        angle: flat,
        vel: 0,
        k: omega * omega,
        c: 2 * zeta * omega,
      });
    });
    for (const p of pieces) {
      tmpQ.setFromAxisAngle(AXIS_X, p.angle);
      p.node.quaternion.copy(p.rest).multiply(tmpQ);
    }
    this.tiles.set(`${x},${z}`, { x, z, root, pieces, up: false, since: this.time, blocks, sounded: true });
  }
}

function isInsidePiece(o: THREE.Object3D): boolean {
  for (let p = o.parent; p; p = p.parent) if (typeof p.userData?.fold === 'number') return true;
  return false;
}
