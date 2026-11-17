import * as THREE from 'three';
import { FullScreenQuad } from 'three/examples/jsm/postprocessing/Pass.js';

/**
 * Tilt-shift macro look. Thin-lens circle of confusion from scene depth around a focus distance
 * (the traveller), then a separable, CoC-weighted gather blur. Final pass does tone mapping,
 * output colour space, a gentle warm grade, vignette and a whisper of photographic grain.
 */
export class TiltShift {
  readonly tuning = { aperture: 16, maxRadius: 9, focus: 8, grain: 0.035, vignette: 0.32 };
  private readonly scene: THREE.WebGLRenderTarget;
  private readonly blurH: THREE.WebGLRenderTarget;
  private readonly hMat: THREE.ShaderMaterial;
  private readonly vMat: THREE.ShaderMaterial;
  private readonly hQuad: FullScreenQuad;
  private readonly vQuad: FullScreenQuad;
  private width = 1;
  private height = 1;

  constructor(private readonly renderer: THREE.WebGLRenderer) {
    const opts = { type: THREE.HalfFloatType, samples: 4 } as const;
    this.scene = new THREE.WebGLRenderTarget(1, 1, { ...opts, depthTexture: new THREE.DepthTexture(1, 1) });
    this.blurH = new THREE.WebGLRenderTarget(1, 1, { type: THREE.HalfFloatType });

    const common = {
      tColor: { value: null as THREE.Texture | null },
      tDepth: { value: null as THREE.Texture | null },
      resolution: { value: new THREE.Vector2(1, 1) },
      near: { value: 0.1 },
      far: { value: 100 },
      focus: { value: 8 },
      aperture: { value: 16 },
      maxRadius: { value: 9 },
    };
    const header = /* glsl */ `
      uniform sampler2D tColor; uniform sampler2D tDepth; uniform vec2 resolution;
      uniform float near; uniform float far; uniform float focus; uniform float aperture; uniform float maxRadius;
      varying vec2 vUv;
      float linearDepth(vec2 uv) {
        float d = texture2D(tDepth, uv).x;
        return near * far / (far - d * (far - near));
      }
      float coc(vec2 uv) {
        float z = linearDepth(uv);
        return clamp(abs(1.0 / focus - 1.0 / z) * aperture, 0.0, 1.0);
      }`;
    const vert = /* glsl */ `varying vec2 vUv; void main() { vUv = uv; gl_Position = vec4(position.xy, 0.0, 1.0); }`;
    const blur = (dir: string, finalPass: boolean) => /* glsl */ `
      ${header}
      uniform sampler2D tSharp; uniform float time; uniform float grain; uniform float vignette;
      void main() {
        float c0 = coc(vUv);
        float r = c0 * maxRadius;
        vec4 sum = vec4(0.0);
        float wsum = 0.0;
        for (int i = -6; i <= 6; i++) {
          float t = float(i) / 6.0;
          vec2 off = ${dir} * t * r / resolution;
          vec2 uv = vUv + off;
          float ct = coc(uv);
          // Sharp pixels should not smear into blurred neighbours, and vice versa.
          float w = exp(-t * t * 2.0) * mix(1.0, smoothstep(0.0, 0.35, ct), step(0.001, abs(t)) * 0.75);
          sum += texture2D(tColor, uv) * w;
          wsum += w;
        }
        vec4 col = sum / max(wsum, 1e-4);
        ${
          finalPass
            ? /* glsl */ `
        // warm print grade: lift shadows toward warm brown, keep highlights creamy
        col.rgb = mix(col.rgb, col.rgb * vec3(1.03, 1.0, 0.94), 0.6);
        col.rgb += vec3(0.010, 0.006, 0.0);
        vec2 q = vUv - 0.5;
        col.rgb *= 1.0 - vignette * dot(q, q) * 2.2;
        gl_FragColor = vec4(col.rgb, 1.0);
        #include <tonemapping_fragment>
        #include <colorspace_fragment>
        float n = fract(sin(dot(vUv * resolution + time * 61.0, vec2(12.9898, 78.233))) * 43758.5453);
        gl_FragColor.rgb += (n - 0.5) * grain;`
            : `gl_FragColor = col;`
        }
      }`;
    this.hMat = new THREE.ShaderMaterial({ uniforms: { ...THREE.UniformsUtils.clone(common), tSharp: { value: null }, time: { value: 0 }, grain: { value: 0 }, vignette: { value: 0 } }, vertexShader: vert, fragmentShader: blur('vec2(1.0, 0.0)', false), depthTest: false, depthWrite: false });
    this.vMat = new THREE.ShaderMaterial({ uniforms: { ...THREE.UniformsUtils.clone(common), tSharp: { value: null }, time: { value: 0 }, grain: { value: 0 }, vignette: { value: 0 } }, vertexShader: vert, fragmentShader: blur('vec2(0.0, 1.0)', true), depthTest: false, depthWrite: false });
    this.vMat.toneMapped = true;
    this.hQuad = new FullScreenQuad(this.hMat);
    this.vQuad = new FullScreenQuad(this.vMat);
  }

  setSize(w: number, h: number): void {
    if (w === this.width && h === this.height) return;
    this.width = w;
    this.height = h;
    this.scene.setSize(w, h);
    this.blurH.setSize(w, h);
  }

  render(scene: THREE.Scene, camera: THREE.PerspectiveCamera, time: number): void {
    const size = this.renderer.getDrawingBufferSize(new THREE.Vector2());
    this.setSize(size.x, size.y);
    this.renderer.setRenderTarget(this.scene);
    this.renderer.render(scene, camera);

    const t = this.tuning;
    for (const m of [this.hMat, this.vMat]) {
      m.uniforms.tDepth.value = this.scene.depthTexture;
      m.uniforms.resolution.value.set(size.x, size.y);
      m.uniforms.near.value = camera.near;
      m.uniforms.far.value = camera.far;
      m.uniforms.focus.value = t.focus;
      m.uniforms.aperture.value = t.aperture;
      // radius is authored for 1080p-ish buffers; scale so the look holds at any size
      m.uniforms.maxRadius.value = t.maxRadius * (size.y / 1080);
    }
    this.hMat.uniforms.tColor.value = this.scene.texture;
    this.renderer.setRenderTarget(this.blurH);
    this.hQuad.render(this.renderer);

    this.vMat.uniforms.tColor.value = this.blurH.texture;
    this.vMat.uniforms.time.value = time % 100;
    this.vMat.uniforms.grain.value = t.grain;
    this.vMat.uniforms.vignette.value = t.vignette;
    this.renderer.setRenderTarget(null);
    this.vQuad.render(this.renderer);
  }

  dispose(): void {
    this.scene.dispose();
    this.blurH.dispose();
    this.hMat.dispose();
    this.vMat.dispose();
    this.hQuad.dispose();
    this.vQuad.dispose();
  }
}
