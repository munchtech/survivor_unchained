import * as THREE from 'three';
import { noiseTexture } from './noiseTex';
import type { Terrain, TerrainPalette } from './terrain';
import { DEFAULT_PALETTE } from './terrain';

/* Grass, placed entirely on the GPU.
 *
 * One instanced blade, drawn tens of thousands of times. Each instance's id
 * maps to a cell of a grid that is snapped to world space around the focus,
 * so as the survivor walks the grid slides under them one cell at a time and
 * the blades never swim: a given patch of ground always grows the same
 * blades. Where each blade stands, how tall it is and whether it grows at all
 * come from hashes of its cell, the terrain's splat (no grass on roads,
 * flagstone, blight or mud) and a clumping noise.
 *
 * The blades lean with a travelling wind and part around the survivor (and
 * anything else passed in as a pusher), which is what makes a meadow feel
 * like it is being walked through. Lit with the terrain's up-facing normal so
 * the field shades as a surface, not as a thousand little cards. */

const MAX_PUSHERS = 8;

export class Grass {
  readonly mesh: THREE.Mesh;
  private uniforms: Record<string, THREE.IUniform>;
  private pushers: THREE.Vector4[] = [];
  readonly grid: number;
  readonly cell: number;

  constructor(terrain: Terrain, opts: { density?: number; cell?: number; grid?: number; palette?: Partial<TerrainPalette> } = {}) {
    const pal = { ...DEFAULT_PALETTE, ...opts.palette };
    this.cell = opts.cell ?? 0.21;
    this.grid = opts.grid ?? 270;
    for (let i = 0; i < MAX_PUSHERS; i++) this.pushers.push(new THREE.Vector4(1e5, 1e5, 0, 0));

    // A tapered, three-segment blade. x in [-0.5, 0.5] is width, y in [0, 1]
    // is how far up the blade the vertex sits.
    const verts = [
      -0.5, 0, 0, 0.5, 0, 0,
      -0.4, 0.34, 0, 0.4, 0.34, 0,
      -0.26, 0.68, 0, 0.26, 0.68, 0,
      0, 1, 0,
    ];
    const index = [0, 1, 2, 2, 1, 3, 2, 3, 4, 4, 3, 5, 4, 5, 6];
    const base = new THREE.BufferGeometry();
    base.setAttribute('position', new THREE.Float32BufferAttribute(verts, 3));
    base.setAttribute('normal', new THREE.Float32BufferAttribute(new Array(verts.length).fill(0).map((_, i) => (i % 3 === 1 ? 1 : 0)), 3));
    base.setIndex(index);
    const geo = new THREE.InstancedBufferGeometry();
    geo.index = base.index;
    geo.attributes.position = base.attributes.position;
    geo.attributes.normal = base.attributes.normal;
    geo.instanceCount = this.grid * this.grid;
    geo.boundingSphere = new THREE.Sphere(new THREE.Vector3(), 1e6);

    const mat = new THREE.MeshStandardMaterial({ roughness: 0.92, metalness: 0, side: THREE.DoubleSide });
    const col = (h: string) => new THREE.Color(h);
    this.uniforms = {
      uNoise: { value: noiseTexture() },
      uHeight: { value: terrain.heightTex },
      uSplat: { value: terrain.splatTex },
      uHRes: { value: terrain.res },
      uHalf: { value: terrain.half },
      uStep: { value: terrain.step },
      uSize: { value: terrain.size },
      uFocus: { value: new THREE.Vector2() },
      uCell: { value: this.cell },
      uGrid: { value: this.grid },
      uTime: { value: 0 },
      uDensity: { value: opts.density ?? 1 },
      uWind: { value: new THREE.Vector3(1, 0.35, 1) },
      uPush: { value: this.pushers },
      uGrassDark: { value: col(pal.grassDark) },
      uGrassLight: { value: col(pal.grassLight) },
      uGrassDry: { value: col(pal.grassDry) },
    };
    const u = this.uniforms;
    mat.onBeforeCompile = (shader) => {
      Object.assign(shader.uniforms, u);
      shader.vertexShader = shader.vertexShader
        .replace('#include <common>', `#include <common>
uniform sampler2D uNoise, uHeight, uSplat;
uniform float uHRes, uHalf, uStep, uSize, uCell, uGrid, uTime, uDensity;
uniform vec2 uFocus;
uniform vec3 uWind;
uniform vec4 uPush[${MAX_PUSHERS}];
uniform vec3 uGrassDark, uGrassLight, uGrassDry;
varying float vT;
varying vec3 vTint;
float gh(vec2 p) { vec3 p3 = fract(vec3(p.xyx) * 0.1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }
float terrainH(vec2 wp) {
  vec2 f = clamp((wp + uHalf) / uStep, vec2(0.0), vec2(uHRes - 1.001));
  vec2 i = floor(f);
  vec2 t = f - i;
  float a = texture(uHeight, (i + vec2(0.5, 0.5)) / uHRes).r;
  float b = texture(uHeight, (i + vec2(1.5, 0.5)) / uHRes).r;
  float c = texture(uHeight, (i + vec2(0.5, 1.5)) / uHRes).r;
  float d = texture(uHeight, (i + vec2(1.5, 1.5)) / uHRes).r;
  return mix(mix(a, b, t.x), mix(c, d, t.x), t.y);
}`)
        .replace('#include <beginnormal_vertex>', 'vec3 objectNormal = vec3(0.0, 1.0, 0.0);')
        .replace('#include <begin_vertex>', `
int id = gl_InstanceID;
int gi = int(uGrid);
vec2 g = vec2(float(id % gi), float(id / gi));
vec2 origin = floor(uFocus / uCell) * uCell - uGrid * 0.5 * uCell;
vec2 cw = origin + g * uCell;
vec2 ci = floor(cw / uCell + 0.5);
float h1 = gh(ci), h2 = gh(ci + 17.13), h3 = gh(ci + 41.71), h4 = gh(ci + 73.3);
vec2 wp = cw + (vec2(h1, h2) - 0.5) * uCell * 1.3;

vec4 sp = texture(uSplat, (wp + uHalf) / uSize);
vec4 nz = texture(uNoise, wp * 0.035);
vec4 nm = texture(uNoise, wp * 0.011 + 0.37);
float bare = max(max(sp.r, sp.g), max(sp.b, sp.a));
float dens = 1.0 - smoothstep(0.12, 0.45, bare + (nz.g - 0.5) * 0.35);
dens *= smoothstep(0.18, 0.5, nz.r + 0.22);
float d = length(wp - uFocus);
float span = uGrid * uCell * 0.5;
float fade = 1.0 - smoothstep(span * 0.62, span * 0.96, d);
float keep = step(h3, dens * uDensity);
float hgt = mix(0.32, 0.78, nz.b) * (0.65 + 0.7 * h4) * keep * mix(0.3, 1.0, fade) * step(0.001, fade);
float wid = 0.12 * (0.8 + 0.5 * h1) * keep;

float ang = h2 * 6.2831853;
vec2 dir = vec2(cos(ang), sin(ang));
float t = position.y;
vT = t;
vec3 p = vec3(dir.x * position.x * wid, t * hgt, dir.y * position.x * wid);

// Wind: a slow travelling swell plus gusty noise.
float swell = sin(uTime * 1.6 + dot(wp, uWind.xy) * 0.55 + nz.a * 5.0) * 0.5 + 0.5;
float gust = texture(uNoise, wp * 0.018 - uTime * vec2(0.035, 0.012)).r;
vec2 bend = normalize(uWind.xy) * (swell * 0.3 + gust * gust * 0.9) * uWind.z;
for (int k = 0; k < ${MAX_PUSHERS}; k++) {
  vec2 a = wp - uPush[k].xy;
  float pd = length(a);
  float s = (1.0 - smoothstep(0.0, uPush[k].z, pd)) * uPush[k].w;
  bend += (pd > 0.001 ? a / pd : vec2(0.0)) * s * 1.6;
}
float bl = min(length(bend), 1.4);
bend = bl > 0.0 ? normalize(bend) * bl : vec2(0.0);
float tt = t * t;
p.xz += bend * tt * hgt;
p.y -= bl * tt * hgt * 0.38;

vec3 transformed = p + vec3(wp.x, terrainH(wp) - 0.02, wp.y);

// Colour follows the same field the terrain uses, so the blade roots vanish
// into the ground and the tips carry the meadow's variation.
float gc = nm.r * 0.55 + texture(uNoise, wp * 0.061 + 0.37).g * 0.45;
vec3 gcol = mix(uGrassDark, uGrassLight, smoothstep(0.32, 0.72, gc));
gcol = mix(gcol, uGrassDry, smoothstep(0.58, 0.78, nm.b) * 0.6);
vTint = gcol * (0.85 + 0.3 * h4);
`)
        .replace('#include <project_vertex>', `
vec4 mvPosition = modelViewMatrix * vec4(transformed, 1.0);
gl_Position = projectionMatrix * mvPosition;`)
        .replace('#include <worldpos_vertex>', `
vec4 worldPosition = modelMatrix * vec4(transformed, 1.0);`);
      shader.fragmentShader = shader.fragmentShader
        .replace('#include <common>', '#include <common>\nvarying float vT;\nvarying vec3 vTint;')
        // Both faces of a blade share the ground's normal. The default
        // double-sided path flips it for back faces, which lit half the
        // meadow from below and turned it into black specks.
        .replace('#include <normal_fragment_begin>', 'float faceDirection = 1.0;\nvec3 normal = normalize(vNormal);\nvec3 nonPerturbedNormal = normal;')
        .replace('#include <map_fragment>', `
vec3 gb = vTint * mix(0.62, 1.12, pow(vT, 0.8));
gb = mix(gb, gb * vec3(1.12, 1.08, 0.78), smoothstep(0.7, 1.0, vT) * 0.5);
diffuseColor.rgb *= gb;`);
    };
    mat.customProgramCacheKey = () => 'grass-v1';
    this.mesh = new THREE.Mesh(geo, mat);
    this.mesh.frustumCulled = false;
    this.mesh.receiveShadow = true;
    this.mesh.castShadow = false;
    this.mesh.name = 'grass';
  }

  set density(v: number) { this.uniforms.uDensity.value = v; }

  /** Things that part the grass: x, z, radius, strength. */
  setPusher(i: number, x: number, z: number, radius: number, strength = 1) {
    if (i < MAX_PUSHERS) this.pushers[i].set(x, z, radius, strength);
  }
  clearPushers() { for (const p of this.pushers) p.set(1e5, 1e5, 0, 0); }

  update(t: number, focusX: number, focusZ: number) {
    this.uniforms.uTime.value = t;
    (this.uniforms.uFocus.value as THREE.Vector2).set(focusX, focusZ);
  }
}
