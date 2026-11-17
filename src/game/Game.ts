import * as THREE from 'three';
import { Input } from '../core/Input';
import { Loop } from '../core/Loop';
import { createRenderer, resizeRenderer } from '../core/Renderer';
import { TiltShift } from '../render/TiltShift';
import { PaperAudio } from '../systems/PaperAudio';
import { createSeededRandom } from '../utils/random';
import { loadKit, type Kit } from '../world/Kit';
import { Page } from '../world/Page';
import { TileField } from '../world/TileField';
import { Traveller } from '../world/Traveller';
import { Wfc } from '../world/Wfc';

const params = new URLSearchParams(location.search);

export class Game {
  private readonly renderer: THREE.WebGLRenderer;
  private readonly scene = new THREE.Scene();
  private readonly camera = new THREE.PerspectiveCamera(30, 1, 0.5, 60);
  private readonly post: TiltShift;
  private readonly audio = new PaperAudio();
  private readonly page = new Page();
  private readonly key = new THREE.DirectionalLight('#ffd29a', 3.1);
  private readonly fill = new THREE.DirectionalLight('#9fbbe0', 0.75);
  private readonly loop = new Loop(
    (dt, t) => this.update(dt, t),
    () => this.render(),
  );
  private input: Input;
  private rng = createSeededRandom(Number(params.get('seed') ?? 7));
  private kit?: Kit;
  private wfc?: Wfc;
  private field?: TileField;
  private traveller?: Traveller;
  private marker: THREE.Mesh;
  private markerLife = 0;
  private readonly camPos = new THREE.Vector3();
  private readonly camLook = new THREE.Vector3();
  private readonly camVel = new THREE.Vector3();
  private frame = 0;
  private elapsed = 0;
  private fps = 60;
  private paused = false;
  private flapsThisSecond = 0;
  private flapWindow = 0;
  readonly view = { elevation: 54, distance: 7.6, lead: 0.55 };

  constructor(canvas: HTMLCanvasElement) {
    this.renderer = createRenderer(canvas);
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    this.renderer.toneMapping = THREE.AgXToneMapping;
    this.renderer.toneMappingExposure = 1.0;
    this.post = new TiltShift(this.renderer);
    this.input = new Input(canvas, this.camera);
    this.input.onFirstGesture = () => this.audio.unlock();
    this.input.onTarget = (p) => {
      this.marker.position.set(p.x, 0.004, p.z);
      this.markerLife = 1;
    };
    this.marker = new THREE.Mesh(
      new THREE.RingGeometry(0.07, 0.085, 40),
      new THREE.MeshBasicMaterial({ color: '#7a4a2e', transparent: true, opacity: 0, depthWrite: false }),
    );
    this.marker.rotation.x = -Math.PI / 2;
    this.setupScene();
    this.installHooks();
  }

  async start(): Promise<void> {
    this.kit = await loadKit();
    this.wfc = new Wfc(this.rng);
    this.field = new TileField(this.kit, this.wfc, this.rng);
    this.scene.add(this.field.group);
    this.traveller = new Traveller(this.kit.traveller);
    this.traveller.onStep = (foot, s) => this.audio.step(foot, s);
    this.scene.add(this.traveller.group);
    this.placeStart();
    this.snapCamera();
    resizeRenderer(this.renderer, this.camera, 2);
    this.loop.start();
  }

  dispose(): void {
    this.loop.stop();
    this.input.dispose();
    this.audio.dispose();
    this.post.dispose();
    this.renderer.dispose();
  }

  private setupScene(): void {
    this.scene.background = new THREE.Color('#e9dcc0');
    this.scene.add(this.page.mesh);
    // Cool fill from the sky side, warm bounce from the page.
    this.scene.add(new THREE.HemisphereLight('#c7d6ea', '#d8c19a', 0.95));
    this.key.castShadow = true;
    this.key.shadow.mapSize.set(2048, 2048);
    const s = this.key.shadow.camera;
    s.left = -8;
    s.right = 8;
    s.top = 8;
    s.bottom = -8;
    s.near = 1;
    s.far = 40;
    this.key.shadow.bias = -0.0004;
    this.key.shadow.normalBias = 0.012;
    this.key.shadow.radius = 4;
    this.scene.add(this.key, this.key.target, this.fill, this.fill.target);
    this.scene.add(this.marker);
  }

  private placeStart(): void {
    // Start on a cell nothing stands on.
    const wfc = this.wfc!;
    wfc.generate(0, 0, 4);
    const t = this.traveller!;
    for (let r = 0; r < 4; r++) {
      for (let z = -r; z <= r; z++) {
        for (let x = -r; x <= r; x++) {
          this.field!.update(0, x, z, 0, -1);
          if (!this.field!.blocked(x, z, 0.12)) {
            t.position.set(x, 0, z);
            return;
          }
        }
      }
    }
  }

  private update(dt: number, t: number): void {
    this.frame += 1;
    this.fps += (1 / Math.max(dt, 1e-3) - this.fps) * 0.05;
    resizeRenderer(this.renderer, this.camera, Number(params.get('dpr') ?? 1.5));
    if (this.paused || !this.traveller || !this.field) return;
    this.elapsed += dt;
    const tr = this.traveller;
    tr.update(dt, this.input.direction(tr.position), (x, z, r) => this.field!.blocked(x, z, r));
    this.field.update(dt, tr.position.x, tr.position.z, tr.facing.x, tr.facing.y);
    this.page.follow(tr.position.x, tr.position.z);
    this.playFolds(dt);

    this.markerLife = Math.max(0, this.markerLife - dt * 1.4);
    (this.marker.material as THREE.MeshBasicMaterial).opacity = this.input.target ? 0.55 : this.markerLife * 0.55;

    // Lantern key from the upper left behind the camera's shoulder; follows so shadows stay crisp.
    const p = tr.position;
    this.key.position.set(p.x - 6, 9, p.z + 3.5);
    this.key.target.position.copy(p);
    this.fill.position.set(p.x + 7, 5, p.z - 2);
    this.fill.target.position.copy(p);
    this.followCamera(dt);
    void t;
  }

  private playFolds(dt: number): void {
    const tr = this.traveller!;
    this.flapWindow += dt;
    if (this.flapWindow > 1) {
      this.flapWindow = 0;
      this.flapsThisSecond = 0;
    }
    for (const e of this.field!.events) {
      // Sound only what's on screen-ish, and thin dense bursts so the room stays calm.
      const dx = e.x - tr.position.x;
      const dz = e.z - tr.position.z;
      const d = Math.hypot(dx, dz);
      if (d > 8 || this.flapsThisSecond > 9) continue;
      this.flapsThisSecond++;
      this.audio.flap({
        pitch: (e.size > 2 ? 0.82 : 1.0) * (0.9 + this.rng() * 0.25) * (e.up ? 1 : 0.92),
        gain: Math.max(0.15, 1 - d / 8) * (e.up ? 0.9 : 0.6),
        pan: Math.max(-1, Math.min(1, dx / 5)),
        up: e.up,
      });
    }
    this.field!.events.length = 0;
  }

  private cameraGoal(): { pos: THREE.Vector3; look: THREE.Vector3 } {
    const tr = this.traveller!;
    const look = new THREE.Vector3(tr.position.x, 0.08, tr.position.z);
    // Look a little ahead of where the traveller is heading.
    look.x += tr.velocity.x * this.view.lead;
    look.z += tr.velocity.y * this.view.lead;
    const el = THREE.MathUtils.degToRad(this.view.elevation);
    const pos = look.clone().add(new THREE.Vector3(0, Math.sin(el), Math.cos(el)).multiplyScalar(this.view.distance));
    return { pos, look };
  }

  private snapCamera(): void {
    const g = this.cameraGoal();
    this.camPos.copy(g.pos);
    this.camLook.copy(g.look);
    this.camera.position.copy(this.camPos);
    this.camera.lookAt(this.camLook);
  }

  private followCamera(dt: number): void {
    const g = this.cameraGoal();
    // Critically damped follow (no overshoot): smooth, never floaty.
    const omega = 3.2;
    const x = this.camLook.clone().sub(g.look);
    const accel = x.multiplyScalar(-omega * omega).sub(this.camVel.clone().multiplyScalar(2 * omega));
    this.camVel.addScaledVector(accel, dt);
    this.camLook.addScaledVector(this.camVel, dt);
    const offset = g.pos.clone().sub(g.look);
    this.camera.position.copy(this.camLook).add(offset);
    this.camera.lookAt(this.camLook);
    this.post.tuning.focus = this.camera.position.distanceTo(this.traveller!.position);
  }

  private render(): void {
    this.post.render(this.scene, this.camera, this.elapsed);
    this.publish();
  }

  private publish(): void {
    const info = this.renderer.info;
    const st = this.field?.standing();
    window.__THREE_GAME_DIAGNOSTICS__ = {
      frame: this.frame,
      elapsed: this.elapsed,
      fps: this.fps,
      kit: this.kit?.source ?? 'loading',
      player: {
        position: { x: this.traveller?.position.x ?? 0, y: 0, z: this.traveller?.position.z ?? 0 },
        speed: this.traveller?.velocity.length() ?? 0,
      },
      tiles: st ?? { up: 0, total: 0, moving: 0 },
      wfc: { cells: this.wfc?.cells.size ?? 0, repairs: this.wfc?.repairs ?? 0, fallbacks: this.wfc?.fallbacks ?? 0 },
      renderer: {
        calls: info.render.calls,
        triangles: info.render.triangles,
        geometries: info.memory.geometries,
        textures: info.memory.textures,
      },
    };
  }

  private installHooks(): void {
    window.__THREE_GAME_TEST_HOOKS__ = {
      setKeys: (keys: string[]) => this.input.setKeys(keys),
      walkTo: (x: number, z: number) => {
        this.input.target = new THREE.Vector3(x, 0, z);
      },
      setPaused: (p: boolean) => {
        this.paused = p;
      },
      setView: (v: Partial<Game['view']>) => Object.assign(this.view, v),
      tuning: () => ({ post: this.post.tuning, field: this.field?.tuning, view: this.view }),
      unlockAudio: () => this.audio.unlock(),
    };
  }
}
