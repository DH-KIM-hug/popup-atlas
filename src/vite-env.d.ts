/// <reference types="vite/client" />

interface Window {
  __THREE_GAME_DIAGNOSTICS__?: {
    frame: number;
    elapsed: number;
    fps: number;
    kit: string;
    player: { position: { x: number; y: number; z: number }; speed: number };
    tiles: { up: number; total: number; moving: number };
    wfc: { cells: number; repairs: number; fallbacks: number };
    renderer: { calls: number; triangles: number; geometries: number; textures: number };
  };
  // Test/capture hooks; shape is owned by src/game/Game.ts
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  __THREE_GAME_TEST_HOOKS__?: Record<string, (...args: any[]) => unknown>;
}
