import * as THREE from 'three';

/**
 * The endless open book: one page plane that follows the traveller. Paper texture is world-aligned
 * so it never swims, and every SPREAD tiles along X a book gutter crease (soft valley shadow with a
 * lit lip) makes successive spreads read as turning pages.
 */
export const SPREAD = 14;

export class Page {
  readonly mesh: THREE.Mesh;
  private readonly material: THREE.MeshStandardMaterial;

  constructor() {
    this.material = new THREE.MeshStandardMaterial({ color: '#efe3c8', roughness: 0.93, metalness: 0 });
    const tex = new THREE.TextureLoader().load(`${import.meta.env.BASE_URL}tex/page_paper.jpg`, (t) => {
      t.colorSpace = THREE.SRGBColorSpace;
      this.material.color.set('#ffffff');
      this.material.needsUpdate = true;
    });
    tex.wrapS = tex.wrapT = THREE.RepeatWrapping;
    tex.anisotropy = 8;
    this.material.map = tex;
    this.material.onBeforeCompile = (shader) => {
      shader.uniforms.spread = { value: SPREAD };
      shader.vertexShader = shader.vertexShader
        .replace('#include <common>', '#include <common>\nvarying vec3 vPageWorld;')
        .replace('#include <worldpos_vertex>', '#include <worldpos_vertex>\nvPageWorld = (modelMatrix * vec4(transformed, 1.0)).xyz;')
        // world-aligned UVs, one texture repeat per 3 tiles
        .replace('#include <uv_vertex>', '#include <uv_vertex>\n#ifdef USE_MAP\nvMapUv = (modelMatrix * vec4(position, 1.0)).xz / 3.0;\n#endif');
      shader.fragmentShader = shader.fragmentShader
        .replace('#include <common>', '#include <common>\nvarying vec3 vPageWorld;\nuniform float spread;')
        .replace(
          '#include <map_fragment>',
          `#include <map_fragment>
          // gutter: distance to the nearest spine line
          float gx = vPageWorld.x - (floor(vPageWorld.x / spread + 0.5) * spread - 0.5);
          float g = abs(gx);
          float valley = exp(-g * g / 0.10);
          float lip = exp(-pow((g - 0.42) / 0.16, 2.0));
          diffuseColor.rgb *= 1.0 - 0.38 * valley;
          diffuseColor.rgb *= 1.0 + 0.05 * lip;
          // faint printed margin rule on each page, like a storybook frame line
          float rule = exp(-pow((g - 0.95) / 0.012, 2.0));
          diffuseColor.rgb = mix(diffuseColor.rgb, diffuseColor.rgb * vec3(0.78, 0.66, 0.52), rule * 0.35);`,
        );
    };
    this.mesh = new THREE.Mesh(new THREE.PlaneGeometry(64, 64), this.material);
    this.mesh.rotation.x = -Math.PI / 2;
    this.mesh.receiveShadow = true;
  }

  follow(x: number, z: number): void {
    this.mesh.position.set(Math.round(x), 0, Math.round(z));
  }
}
