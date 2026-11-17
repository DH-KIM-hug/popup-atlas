import * as THREE from 'three';

/** WASD / arrows, or click (tap) on the page to walk there. Camera always looks north, so W is -Z. */
export class Input {
  private readonly keys = new Set<string>();
  target: THREE.Vector3 | null = null;
  onFirstGesture?: () => void;
  onTarget?: (p: THREE.Vector3) => void;
  private gestured = false;
  private readonly ray = new THREE.Raycaster();
  private readonly plane = new THREE.Plane(new THREE.Vector3(0, 1, 0), 0);

  constructor(
    private readonly canvas: HTMLCanvasElement,
    private readonly camera: THREE.Camera,
  ) {
    window.addEventListener('keydown', this.down);
    window.addEventListener('keyup', this.up);
    window.addEventListener('blur', this.clear);
    canvas.addEventListener('pointerdown', this.pointer);
  }

  private gesture(): void {
    if (this.gestured) return;
    this.gestured = true;
    this.onFirstGesture?.();
  }

  private readonly down = (e: KeyboardEvent) => {
    const k = e.key.toLowerCase();
    if (['w', 'a', 's', 'd', 'arrowup', 'arrowdown', 'arrowleft', 'arrowright'].includes(k)) {
      this.keys.add(k);
      this.target = null;
      e.preventDefault();
      this.gesture();
    }
  };

  private readonly up = (e: KeyboardEvent) => {
    this.keys.delete(e.key.toLowerCase());
  };

  private readonly clear = () => this.keys.clear();

  private readonly pointer = (e: PointerEvent) => {
    this.gesture();
    const r = this.canvas.getBoundingClientRect();
    const ndc = new THREE.Vector2(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1);
    this.ray.setFromCamera(ndc, this.camera);
    const hit = new THREE.Vector3();
    if (this.ray.ray.intersectPlane(this.plane, hit)) {
      this.target = hit;
      this.onTarget?.(hit);
    }
  };

  /** Desired walk direction (unit or zero) given where the traveller stands. */
  direction(from: THREE.Vector3): { x: number; z: number } {
    let x = 0;
    let z = 0;
    if (this.keys.has('w') || this.keys.has('arrowup')) z -= 1;
    if (this.keys.has('s') || this.keys.has('arrowdown')) z += 1;
    if (this.keys.has('a') || this.keys.has('arrowleft')) x -= 1;
    if (this.keys.has('d') || this.keys.has('arrowright')) x += 1;
    if (x || z) {
      const l = Math.hypot(x, z);
      return { x: x / l, z: z / l };
    }
    if (this.target) {
      const dx = this.target.x - from.x;
      const dz = this.target.z - from.z;
      const d = Math.hypot(dx, dz);
      if (d < 0.06) {
        this.target = null;
        return { x: 0, z: 0 };
      }
      // arrive gently over the last ~0.3
      const s = Math.min(1, d / 0.3);
      return { x: (dx / d) * s, z: (dz / d) * s };
    }
    return { x: 0, z: 0 };
  }

  /** Scripted input for capture/bot runs. */
  setKeys(list: string[]): void {
    this.keys.clear();
    for (const k of list) this.keys.add(k);
  }

  dispose(): void {
    window.removeEventListener('keydown', this.down);
    window.removeEventListener('keyup', this.up);
    window.removeEventListener('blur', this.clear);
    this.canvas.removeEventListener('pointerdown', this.pointer);
  }
}
