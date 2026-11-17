import * as THREE from 'three';

export interface WalkInput {
  /** desired direction on the page (x east, z south), length 0..1 */
  x: number;
  z: number;
}

/**
 * The paper traveller. Paper toys have no knees: the walk is a side-to-side waddle that rocks the
 * whole cut-out from foot to foot, leg flaps swinging and a little bob on each step.
 */
export class Traveller {
  readonly group = new THREE.Group();
  readonly velocity = new THREE.Vector2();
  facing = new THREE.Vector2(0, -1);
  private heading = Math.PI; // yaw; model faces -Z at yaw 0, we keep yaw so that forward = facing
  private phase = 0;
  private lastFoot = 0;
  private readonly rig: THREE.Object3D;
  private readonly body?: THREE.Object3D;
  private readonly head?: THREE.Object3D;
  private readonly legL?: THREE.Object3D;
  private readonly legR?: THREE.Object3D;
  private legRest = new Map<THREE.Object3D, THREE.Quaternion>();
  onStep?: (foot: 0 | 1, speed01: number) => void;
  maxSpeed = 0.95;

  constructor(model: THREE.Object3D) {
    this.rig = model.clone(true);
    this.group.add(this.rig);
    this.body = this.rig.getObjectByName('body');
    this.head = this.rig.getObjectByName('head');
    this.legL = this.rig.getObjectByName('leg_l');
    this.legR = this.rig.getObjectByName('leg_r');
    for (const leg of [this.legL, this.legR]) if (leg) this.legRest.set(leg, leg.quaternion.clone());
    this.heading = 0;
  }

  get position(): THREE.Vector3 {
    return this.group.position;
  }

  update(dt: number, input: WalkInput, blocked: (x: number, z: number, r: number) => boolean): void {
    const want = new THREE.Vector2(input.x, input.z);
    if (want.lengthSq() > 1) want.normalize();
    want.multiplyScalar(this.maxSpeed);
    // Ease toward the wanted velocity: quick to start, a touch slower to stop.
    const rate = want.lengthSq() > this.velocity.lengthSq() ? 7 : 9;
    this.velocity.lerp(want, 1 - Math.exp(-rate * dt));

    const r = 0.07;
    const p = this.group.position;
    const nx = p.x + this.velocity.x * dt;
    const nz = p.z + this.velocity.y * dt;
    // Slide along standing card instead of stopping dead.
    if (!blocked(nx, nz, r)) {
      p.x = nx;
      p.z = nz;
    } else if (!blocked(nx, p.z, r)) {
      p.x = nx;
      this.velocity.y *= 0.5;
    } else if (!blocked(p.x, nz, r)) {
      p.z = nz;
      this.velocity.x *= 0.5;
    } else {
      this.velocity.multiplyScalar(0.3);
    }

    const speed = this.velocity.length();
    const speed01 = Math.min(1, speed / this.maxSpeed);
    if (speed > 0.05) {
      this.facing.copy(this.velocity).normalize();
      const target = Math.atan2(-this.facing.x, -this.facing.y);
      let d = target - this.heading;
      d = Math.atan2(Math.sin(d), Math.cos(d));
      this.heading += d * (1 - Math.exp(-12 * dt));
    }
    this.rig.rotation.y = this.heading;

    // Waddle. Stride ~0.09 per step; settle to rest smoothly when stopping.
    this.phase += (speed / 0.09) * Math.PI * dt;
    const amp = speed01;
    const s = Math.sin(this.phase);
    const settle = 1 - Math.exp(-10 * dt);
    const roll = s * 0.16 * amp;
    const bob = Math.abs(s) * 0.014 * amp;
    this.rig.rotation.z += (roll - this.rig.rotation.z) * settle * 3;
    this.rig.position.y += (bob - this.rig.position.y) * settle * 3;
    this.rig.rotation.x = -0.08 * amp; // lean into the walk
    if (this.head) this.head.rotation.z = -s * 0.08 * amp;
    if (this.body) this.body.rotation.z = s * 0.03 * amp;
    const swing = Math.sin(this.phase) * 0.55 * amp;
    for (const [leg, rest] of this.legRest) {
      const sign = leg === this.legL ? 1 : -1;
      leg.quaternion.copy(rest).multiply(new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(1, 0, 0), sign * swing));
    }

    const foot = Math.floor(this.phase / Math.PI);
    if (foot !== this.lastFoot) {
      this.lastFoot = foot;
      if (speed01 > 0.15) this.onStep?.((foot & 1) as 0 | 1, speed01);
    }
  }
}
