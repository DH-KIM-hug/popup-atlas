import { COMPAT, DIRS, VARIANTS } from './TileDefs';

const N = VARIANTS.length;
const key = (x: number, z: number) => `${x},${z}`;

/**
 * Wave function collapse over an unbounded grid. Cells are collapsed on demand around the traveller,
 * always inside a generation radius that is larger than the visible radius, so a contradiction can be
 * repaired by un-collapsing nearby cells that nobody has seen yet. Cells that have been shown are locked.
 */
export class Wfc {
  readonly cells = new Map<string, number>();
  private readonly locked = new Set<string>();
  repairs = 0;
  fallbacks = 0;

  constructor(private readonly rng: () => number) {}

  get(x: number, z: number): number | undefined {
    return this.cells.get(key(x, z));
  }

  lock(x: number, z: number): void {
    this.locked.add(key(x, z));
  }

  /** Make sure every cell within radius of (cx, cz) is collapsed. */
  generate(cx: number, cz: number, radius: number): void {
    const want: [number, number][] = [];
    const r2 = radius * radius;
    for (let z = Math.floor(cz - radius); z <= Math.ceil(cz + radius); z++) {
      for (let x = Math.floor(cx - radius); x <= Math.ceil(cx + radius); x++) {
        const dx = x - cx;
        const dz = z - cz;
        if (dx * dx + dz * dz <= r2 && !this.cells.has(key(x, z))) want.push([x, z]);
      }
    }
    if (!want.length) return;
    this.solve(want);
  }

  private solve(initial: [number, number][]): void {
    let targets = initial;
    for (let attempt = 0; attempt < 12; attempt++) {
      const failed = this.attempt(targets);
      if (!failed) return;
      // Repair: forget unseen collapsed cells around the contradiction and solve them again.
      this.repairs += 1;
      const extra: [number, number][] = [];
      const radius = 1 + Math.min(attempt, 3);
      for (let dz = -radius; dz <= radius; dz++) {
        for (let dx = -radius; dx <= radius; dx++) {
          const x = failed[0] + dx;
          const z = failed[1] + dz;
          const k = key(x, z);
          if (this.cells.has(k) && !this.locked.has(k)) {
            this.cells.delete(k);
            extra.push([x, z]);
          }
        }
      }
      const seen = new Set(targets.map(([x, z]) => key(x, z)));
      targets = targets.concat(extra.filter(([x, z]) => !seen.has(key(x, z))));
    }
    // Last resort: place whatever fits best (counted, should stay at 0 in practice).
    for (const [x, z] of targets) {
      if (this.cells.has(key(x, z))) continue;
      this.fallbacks += 1;
      this.cells.set(key(x, z), this.bestEffort(x, z));
    }
  }

  /** Returns undefined on success, or the cell where a contradiction happened. */
  private attempt(targets: [number, number][]): [number, number] | undefined {
    const domains = new Map<string, Uint8Array>();
    for (const [x, z] of targets) {
      const d = new Uint8Array(N).fill(1);
      for (let dir = 0; dir < 4; dir++) {
        const nb = this.cells.get(key(x + DIRS[dir][0], z + DIRS[dir][1]));
        if (nb === undefined) continue;
        // Neighbour in direction dir is fixed: we must be allowed in direction (dir+2) of it.
        const row = COMPAT[(dir + 2) % 4][nb];
        for (let v = 0; v < N; v++) d[v] &= row[v];
      }
      domains.set(key(x, z), d);
    }
    const queue = targets.map(([x, z]) => [x, z] as [number, number]);
    const bad = this.propagate(domains, queue);
    if (bad) return bad;

    const pending = new Set(domains.keys());
    while (pending.size) {
      // Lowest weighted entropy, with a little noise to break ties.
      let best: string | undefined;
      let bestH = Infinity;
      for (const k of pending) {
        const d = domains.get(k)!;
        let sum = 0;
        let sumLog = 0;
        for (let v = 0; v < N; v++) {
          if (!d[v]) continue;
          const w = VARIANTS[v].weight;
          sum += w;
          sumLog += w * Math.log(w);
        }
        const h = Math.log(sum) - sumLog / sum + this.rng() * 1e-3;
        if (h < bestH) {
          bestH = h;
          best = k;
        }
      }
      const k = best!;
      pending.delete(k);
      const [x, z] = k.split(',').map(Number);
      const d = domains.get(k)!;
      const choice = this.pick(x, z, d);
      if (choice < 0) {
        for (const kk of domains.keys()) if (!pending.has(kk)) this.cells.delete(kk);
        return [x, z];
      }
      d.fill(0);
      d[choice] = 1;
      this.cells.set(k, choice);
      const fail = this.propagate(domains, [[x, z]]);
      if (fail) {
        for (const kk of domains.keys()) if (!pending.has(kk)) this.cells.delete(kk);
        return fail;
      }
    }
    return undefined;
  }

  private propagate(domains: Map<string, Uint8Array>, queue: [number, number][]): [number, number] | undefined {
    while (queue.length) {
      const [x, z] = queue.pop()!;
      const cur = domains.get(key(x, z))!;
      for (let dir = 0; dir < 4; dir++) {
        const nx = x + DIRS[dir][0];
        const nz = z + DIRS[dir][1];
        const nd = domains.get(key(nx, nz));
        if (!nd) continue;
        let changed = false;
        let left = 0;
        for (let b = 0; b < N; b++) {
          if (!nd[b]) continue;
          let ok = false;
          for (let a = 0; a < N && !ok; a++) if (cur[a] && COMPAT[dir][a][b]) ok = true;
          if (!ok) {
            nd[b] = 0;
            changed = true;
          } else left++;
        }
        if (!left) return [nx, nz];
        if (changed) queue.push([nx, nz]);
      }
    }
    return undefined;
  }

  /** Weighted choice with small neighbourhood biases so the land reads as places, not noise. */
  private pick(x: number, z: number, d: Uint8Array): number {
    const near = new Map<string, number>();
    for (let dz = -1; dz <= 1; dz++) {
      for (let dx = -1; dx <= 1; dx++) {
        const v = this.cells.get(key(x + dx, z + dz));
        if (v !== undefined) near.set(VARIANTS[v].type.name, (near.get(VARIANTS[v].type.name) ?? 0) + 1);
      }
    }
    const pathNear = [...near.keys()].some((n) => n.startsWith('path') || n === 'bridge');
    let total = 0;
    const w = new Float64Array(N);
    for (let v = 0; v < N; v++) {
      if (!d[v]) continue;
      const name = VARIANTS[v].type.name;
      let weight = VARIANTS[v].weight;
      if (name === 'trees') weight *= 1 + 0.6 * (near.get('trees') ?? 0);
      if (name === 'house') weight *= pathNear ? 3.2 : 0.5;
      if (name === 'house' && (near.get('house') ?? 0) > 1) weight *= 0.3;
      if (name === 'hill') weight *= 1 + 0.5 * (near.get('hill') ?? 0);
      w[v] = weight;
      total += weight;
    }
    if (total <= 0) return -1;
    let r = this.rng() * total;
    for (let v = 0; v < N; v++) {
      if (!w[v]) continue;
      r -= w[v];
      if (r <= 0) return v;
    }
    for (let v = N - 1; v >= 0; v--) if (w[v]) return v;
    return -1;
  }

  private bestEffort(x: number, z: number): number {
    let best = 0;
    let bestScore = -1;
    for (let v = 0; v < N; v++) {
      let score = 0;
      for (let dir = 0; dir < 4; dir++) {
        const nb = this.cells.get(key(x + DIRS[dir][0], z + DIRS[dir][1]));
        if (nb === undefined || COMPAT[dir][v][nb]) score++;
      }
      if (score > bestScore) {
        bestScore = score;
        best = v;
      }
    }
    return best;
  }
}
