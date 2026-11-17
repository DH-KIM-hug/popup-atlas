// Tile types and edge sockets. Canonical orientation matches the kit (see artifacts/game-progress.md).
// Sockets per edge, order N, E, S, W:  G grass, R river, P path.
export type Socket = 'G' | 'R' | 'P';

export interface TileType {
  name: string;
  sockets: [Socket, Socket, Socket, Socket];
  weight: number;
}

export const TILE_TYPES: TileType[] = [
  { name: 'grass', sockets: ['G', 'G', 'G', 'G'], weight: 6 },
  { name: 'hill', sockets: ['G', 'G', 'G', 'G'], weight: 2.2 },
  { name: 'trees', sockets: ['G', 'G', 'G', 'G'], weight: 3.4 },
  { name: 'house', sockets: ['G', 'G', 'G', 'G'], weight: 1.1 },
  { name: 'path_straight', sockets: ['P', 'G', 'P', 'G'], weight: 2.4 },
  { name: 'path_corner', sockets: ['P', 'P', 'G', 'G'], weight: 1.2 },
  { name: 'path_tee', sockets: ['P', 'P', 'P', 'G'], weight: 0.35 },
  { name: 'path_end', sockets: ['P', 'G', 'G', 'G'], weight: 0.25 },
  { name: 'river_straight', sockets: ['R', 'G', 'R', 'G'], weight: 2.0 },
  { name: 'river_corner', sockets: ['R', 'R', 'G', 'G'], weight: 1.0 },
  { name: 'river_end', sockets: ['R', 'G', 'G', 'G'], weight: 0.2 },
  { name: 'bridge', sockets: ['R', 'P', 'R', 'P'], weight: 0.9 },
];

/** One placeable variant: a tile type rotated by rot quarter turns clockwise (seen from above). */
export interface Variant {
  id: number;
  type: TileType;
  rot: number;
  sockets: [Socket, Socket, Socket, Socket];
  weight: number;
}

function rotate(s: [Socket, Socket, Socket, Socket], rot: number): [Socket, Socket, Socket, Socket] {
  // Clockwise quarter turn: what faced N now faces E.
  const out = [...s] as [Socket, Socket, Socket, Socket];
  for (let i = 0; i < 4; i++) out[(i + rot) % 4] = s[i];
  return out;
}

export const VARIANTS: Variant[] = (() => {
  const list: Variant[] = [];
  for (const type of TILE_TYPES) {
    const seen = new Set<string>();
    const rots: number[] = [];
    for (let rot = 0; rot < 4; rot++) {
      const key = rotate(type.sockets, rot).join('');
      // Symmetric grass tiles still get all four rotations so the art varies; others dedupe by sockets.
      if (seen.has(key) && !type.sockets.every((s) => s === 'G')) continue;
      seen.add(key);
      rots.push(rot);
    }
    for (const rot of rots) {
      list.push({ id: list.length, type, rot, sockets: rotate(type.sockets, rot), weight: type.weight / rots.length });
    }
  }
  return list;
})();

// Direction index: 0 N (-z), 1 E (+x), 2 S (+z), 3 W (-x)
export const DIRS: [number, number][] = [
  [0, -1],
  [1, 0],
  [0, 1],
  [-1, 0],
];

/** compat[d][a] = set of variant ids that may sit in direction d of variant a. */
export const COMPAT: Uint8Array[][] = (() => {
  const n = VARIANTS.length;
  const table: Uint8Array[][] = [];
  for (let d = 0; d < 4; d++) {
    table.push([]);
    for (let a = 0; a < n; a++) {
      const row = new Uint8Array(n);
      for (let b = 0; b < n; b++) row[b] = VARIANTS[a].sockets[d] === VARIANTS[b].sockets[(d + 2) % 4] ? 1 : 0;
      table[d].push(row);
    }
  }
  return table;
})();
