import * as THREE from 'three';
import { noiseTexture } from './noiseTex';
import { ownTextures } from './dispose';
import { clamp } from '@/core/math';
import { groundTextures, GROUND_LAYERS } from './ground';

/* The ground, which from a top-down camera is most of every frame.
 *
 * A heightfield sampled from the zone's height function, painted from its
 * paint function into a splat texture (dirt, flagstone, blight, mud), and
 * shaded by one extended MeshStandardMaterial with photoscanned materials
 * (render/ground.ts: meadow, forest floor, dirt, mud, setts, rock, burnt
 * ground; colour, normals, occlusion, roughness and height for each):
 *
 *   - the paint says how much of each material, its edges frayed by noise;
 *     then heights decide, so setts stand out of the mud between them and
 *     a path's stones show through its dust, instead of two photographs
 *     cross-fading;
 *   - meadow gives way to forest floor in drifts (more of it in a wood);
 *   - steep faces turn to rock whatever the paint says, the rock laid on
 *     the face rather than stretched down it from above;
 *   - every material is sampled twice, as laid and turned, and the two
 *     meet along a slow noise, so no tile repeats across the screen;
 *   - blight glows along ridged veins (it feeds the bloom pass).
 *
 * heightAt() is the authority for where the ground is, for the simulation as
 * much as for rendering. */

export interface TerrainPaint { dirt: number; stone: number; blight: number; mud: number }

export interface TerrainPalette { blightGlow: string }

export const DEFAULT_PALETTE: TerrainPalette = { blightGlow: '#8cff5a' };

export interface TerrainSource {
  size: number; // metres per side, centred on the origin
  resolution: number; // vertices per side
  height(x: number, z: number): number;
  paint(x: number, z: number, out: TerrainPaint): void;
  palette?: Partial<TerrainPalette>;
  /** How much of the meadow is forest floor instead (0..1; about 0.3). */
  leaves?: number;
  splatResolution?: number;
}

export class Terrain {
  readonly size: number;
  readonly res: number;
  readonly half: number;
  readonly step: number;
  readonly heights: Float32Array;
  readonly mesh: THREE.Mesh;
  readonly material: THREE.MeshStandardMaterial;
  readonly heightTex: THREE.DataTexture;
  readonly splatTex: THREE.DataTexture;
  readonly splatData: Uint8Array;
  readonly splatRes: number;
  /** The forest floor's share of the meadow (the grass thins there too). */
  readonly leaves: number;
  private uniforms: Record<string, THREE.IUniform> = {};

  constructor(src: TerrainSource) {
    this.size = src.size;
    this.res = src.resolution;
    this.half = src.size / 2;
    this.step = src.size / (src.resolution - 1);
    const n = this.res;

    // Heights.
    this.heights = new Float32Array(n * n);
    for (let j = 0; j < n; j++) {
      for (let i = 0; i < n; i++) {
        const x = -this.half + i * this.step, z = -this.half + j * this.step;
        this.heights[j * n + i] = src.height(x, z);
      }
    }

    // Geometry: an indexed grid in XZ.
    const geo = new THREE.BufferGeometry();
    const pos = new Float32Array(n * n * 3);
    const uv = new Float32Array(n * n * 2);
    for (let j = 0; j < n; j++) {
      for (let i = 0; i < n; i++) {
        const k = j * n + i;
        pos[k * 3] = -this.half + i * this.step;
        pos[k * 3 + 1] = this.heights[k];
        pos[k * 3 + 2] = -this.half + j * this.step;
        uv[k * 2] = i / (n - 1);
        uv[k * 2 + 1] = j / (n - 1);
      }
    }
    const idx = new Uint32Array((n - 1) * (n - 1) * 6);
    let p = 0;
    for (let j = 0; j < n - 1; j++) {
      for (let i = 0; i < n - 1; i++) {
        const a = j * n + i, b = a + 1, c = a + n, d = c + 1;
        // Alternate the diagonal so slopes do not all crease the same way.
        if ((i + j) & 1) { idx[p++] = a; idx[p++] = c; idx[p++] = b; idx[p++] = b; idx[p++] = c; idx[p++] = d; }
        else { idx[p++] = a; idx[p++] = c; idx[p++] = d; idx[p++] = a; idx[p++] = d; idx[p++] = b; }
      }
    }
    geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    geo.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
    geo.setIndex(new THREE.BufferAttribute(idx, 1));
    geo.computeVertexNormals();
    geo.computeBoundingSphere();

    // Height texture for the grass (float, sampled manually).
    this.heightTex = new THREE.DataTexture(this.heights, n, n, THREE.RedFormat, THREE.FloatType);
    this.heightTex.magFilter = this.heightTex.minFilter = THREE.NearestFilter;
    this.heightTex.needsUpdate = true;

    // Splat paint.
    const sr = src.splatResolution ?? 1024;
    this.splatRes = sr;
    this.splatData = new Uint8Array(sr * sr * 4);
    const paint: TerrainPaint = { dirt: 0, stone: 0, blight: 0, mud: 0 };
    for (let j = 0; j < sr; j++) {
      for (let i = 0; i < sr; i++) {
        const x = -this.half + (i + 0.5) / sr * this.size;
        const z = -this.half + (j + 0.5) / sr * this.size;
        paint.dirt = paint.stone = paint.blight = paint.mud = 0;
        src.paint(x, z, paint);
        const k = (j * sr + i) * 4;
        this.splatData[k] = clamp(paint.dirt, 0, 1) * 255;
        this.splatData[k + 1] = clamp(paint.stone, 0, 1) * 255;
        this.splatData[k + 2] = clamp(paint.blight, 0, 1) * 255;
        this.splatData[k + 3] = clamp(paint.mud, 0, 1) * 255;
      }
    }
    this.splatTex = new THREE.DataTexture(this.splatData, sr, sr, THREE.RGBAFormat);
    this.splatTex.magFilter = THREE.LinearFilter;
    this.splatTex.minFilter = THREE.LinearMipmapLinearFilter;
    this.splatTex.generateMipmaps = true;
    this.splatTex.needsUpdate = true;

    this.leaves = src.leaves ?? 0.3;
    this.material = this.buildMaterial({ ...DEFAULT_PALETTE, ...src.palette });
    this.mesh = new THREE.Mesh(geo, this.material);
    this.mesh.receiveShadow = true;
    this.mesh.castShadow = false;
    this.mesh.name = 'terrain';
  }

  /** Bilinear height at a world position. */
  heightAt(x: number, z: number) {
    const n = this.res;
    const fx = clamp((x + this.half) / this.step, 0, n - 1.0001);
    const fz = clamp((z + this.half) / this.step, 0, n - 1.0001);
    const i = Math.floor(fx), j = Math.floor(fz);
    const tx = fx - i, tz = fz - j;
    const h = this.heights;
    const a = h[j * n + i], b = h[j * n + i + 1], c = h[(j + 1) * n + i], d = h[(j + 1) * n + i + 1];
    return (a + (b - a) * tx) * (1 - tz) + (c + (d - c) * tx) * tz;
  }

  /** Paint weights at a world position (0..1 each). */
  paintAt(x: number, z: number, out: TerrainPaint) {
    const sr = this.splatRes;
    const i = clamp(Math.floor((x + this.half) / this.size * sr), 0, sr - 1);
    const j = clamp(Math.floor((z + this.half) / this.size * sr), 0, sr - 1);
    const k = (j * sr + i) * 4;
    out.dirt = this.splatData[k] / 255;
    out.stone = this.splatData[k + 1] / 255;
    out.blight = this.splatData[k + 2] / 255;
    out.mud = this.splatData[k + 3] / 255;
    return out;
  }

  /** Repaint a region at runtime (a spreading blight, a burnt clearing). */
  repaint(x0: number, z0: number, x1: number, z1: number, fn: (x: number, z: number, cur: TerrainPaint) => void) {
    const sr = this.splatRes;
    const cur: TerrainPaint = { dirt: 0, stone: 0, blight: 0, mud: 0 };
    const i0 = clamp(Math.floor((x0 + this.half) / this.size * sr), 0, sr - 1);
    const i1 = clamp(Math.ceil((x1 + this.half) / this.size * sr), 0, sr - 1);
    const j0 = clamp(Math.floor((z0 + this.half) / this.size * sr), 0, sr - 1);
    const j1 = clamp(Math.ceil((z1 + this.half) / this.size * sr), 0, sr - 1);
    for (let j = j0; j <= j1; j++) {
      for (let i = i0; i <= i1; i++) {
        const k = (j * sr + i) * 4;
        cur.dirt = this.splatData[k] / 255; cur.stone = this.splatData[k + 1] / 255;
        cur.blight = this.splatData[k + 2] / 255; cur.mud = this.splatData[k + 3] / 255;
        fn(-this.half + (i + 0.5) / sr * this.size, -this.half + (j + 0.5) / sr * this.size, cur);
        this.splatData[k] = clamp(cur.dirt, 0, 1) * 255; this.splatData[k + 1] = clamp(cur.stone, 0, 1) * 255;
        this.splatData[k + 2] = clamp(cur.blight, 0, 1) * 255; this.splatData[k + 3] = clamp(cur.mud, 0, 1) * 255;
      }
    }
    this.splatTex.needsUpdate = true;
  }

  set time(t: number) { if (this.uniforms.uTime) this.uniforms.uTime.value = t; }

  private buildMaterial(pal: TerrainPalette) {
    const mat = new THREE.MeshStandardMaterial({ color: 0xffffff, roughness: 0.95, metalness: 0 });
    const g = groundTextures();
    const uniforms = this.uniforms = {
      uNoise: { value: noiseTexture() },
      uSplat: { value: this.splatTex },
      uSize: { value: this.size },
      uHalf: { value: this.half },
      uTime: { value: 0 },
      uLeaves: { value: this.leaves },
      uBlightGlow: { value: new THREE.Color(pal.blightGlow) },
      uGAlb: { value: g.albedo },
      uGNor: { value: g.normal },
      uGArh: { value: g.arh },
      uGScale: { value: g.metres.map((m) => 1 / m) },
    };
    mat.onBeforeCompile = (shader) => {
      Object.assign(shader.uniforms, uniforms);
      shader.vertexShader = shader.vertexShader
        .replace('#include <common>', '#include <common>\nvarying vec3 vWorldP;\nvarying vec3 vWorldN;')
        .replace('#include <project_vertex>', '#include <project_vertex>\nvWorldP = (modelMatrix * vec4(transformed, 1.0)).xyz;\nvWorldN = normalize(mat3(modelMatrix) * objectNormal);');
      shader.fragmentShader = shader.fragmentShader
        .replace('#include <common>', `#include <common>
varying vec3 vWorldP;
varying vec3 vWorldN;
uniform sampler2D uNoise;
uniform sampler2D uSplat;
uniform sampler2DArray uGAlb, uGNor, uGArh;
uniform float uGScale[${GROUND_LAYERS.length}];
uniform float uSize, uHalf, uTime, uLeaves;
uniform vec3 uBlightGlow;
#define NL ${GROUND_LAYERS.length}
#define ROCK ${GROUND_LAYERS.indexOf('rock')}
float gRough = 0.95;
float gAO = 1.0;
vec3 gNormalW = vec3(0.0, 1.0, 0.0);
vec3 gEmissive = vec3(0.0);
float gTile = 0.0;
// Each photograph brought into the same light: the setts were shot clean
// and pale in the sun; this town's are not.
const float G_TONE[NL] = float[](1.0, 1.0, 1.0, 1.0, 0.72, 0.95, 1.0);
// The second, turned sampling (see the header).
const mat2 G_TURN = mat2(0.8, -0.6, 0.6, 0.8);
vec2 gUv(int i, vec3 p, vec3 n, out mat3 tbn) {
  if (i == ROCK) {
    // On the face: across it horizontally, and up it.
    vec2 h = normalize(n.xz + vec2(1e-4, 0.0));
    vec3 t = vec3(-h.y, 0.0, h.x);
    tbn = mat3(t, vec3(0.0, -1.0, 0.0), n);
    return vec2(dot(p.xz, vec2(-h.y, h.x)), p.y) * uGScale[i];
  }
  // Laid flat: u along +x, the image's top toward -z.
  vec3 t = normalize(vec3(1.0, 0.0, 0.0) - n * n.x);
  tbn = mat3(t, cross(n, t), n);
  return p.xz * uGScale[i];
}
vec4 gTex(sampler2DArray s, vec2 uv, int i) {
  vec4 a = texture(s, vec3(uv, float(i)));
  if (gTile <= 0.0) return a;
  vec4 b = texture(s, vec3(G_TURN * uv * 0.87 + vec2(0.37, 0.71), float(i)));
  return mix(a, b, gTile);
}
vec3 gNor(vec2 uv, int i) {
  vec3 a = texture(uGNor, vec3(uv, float(i))).xyz * 2.0 - 1.0;
  if (gTile <= 0.0) return a;
  vec3 b = texture(uGNor, vec3(G_TURN * uv * 0.87 + vec2(0.37, 0.71), float(i))).xyz * 2.0 - 1.0;
  b.xy = transpose(G_TURN) * b.xy;
  return normalize(mix(a, b, gTile));
}
void gOver(inout float w[NL], int i, float a) {
  for (int k = 0; k < NL; k++) w[k] *= 1.0 - a;
  w[i] += a;
}
`)
        .replace('#include <map_fragment>', `
vec2 w = vWorldP.xz;
vec4 nL = texture2D(uNoise, w * 0.011);
vec4 nM = texture2D(uNoise, w * 0.061 + 0.37);
vec4 nF = texture2D(uNoise, w * 0.29 + 0.71);
vec4 sp = texture2D(uSplat, (w + uHalf) / uSize);
vec3 nGeo = normalize(vWorldN);
gTile = smoothstep(0.46, 0.54, nL.b * 0.6 + nM.r * 0.4);

// How much of each material the paint asks for, edges frayed by noise.
float wd = smoothstep(0.35, 0.65, sp.r + (nM.b - 0.5) * 0.45 + (nF.g - 0.5) * 0.12);
float ws = smoothstep(0.35, 0.65, sp.g + (nM.g - 0.5) * 0.35 + (nF.b - 0.5) * 0.15);
float wb = smoothstep(0.3, 0.7, sp.b + (nM.r - 0.5) * 0.5);
float wm = smoothstep(0.35, 0.65, sp.a + (nM.g - 0.5) * 0.4);
float slope = 1.0 - clamp(nGeo.y, 0.0, 1.0);
float wr = smoothstep(0.32, 0.5, slope + (nM.b - 0.5) * 0.15);
float leafy = smoothstep(0.42, 0.78, nL.g * 0.7 + nM.a * 0.3 + uLeaves - 0.5);
float gw[NL];
for (int k = 0; k < NL; k++) gw[k] = 0.0;
gw[0] = 1.0 - leafy; gw[1] = leafy;
gOver(gw, 2, wd); gOver(gw, 3, wm); gOver(gw, 4, ws); gOver(gw, 6, wb); gOver(gw, ROCK, wr);

// Heights decide at the edges: the taller material shows.
const float DEPTH = 0.22;
float hs[NL];
float best = 0.0;
for (int k = 0; k < NL; k++) {
  hs[k] = -1.0;
  if (gw[k] < 0.003) continue;
  mat3 tbn;
  vec2 uv = gUv(k, vWorldP, nGeo, tbn);
  hs[k] = gw[k] + gTex(uGArh, uv, k).b * DEPTH;
  best = max(best, hs[k]);
}
float tot = 0.0;
for (int k = 0; k < NL; k++) { gw[k] = hs[k] < 0.0 ? 0.0 : max(hs[k] - best + DEPTH, 0.0); tot += gw[k]; }

vec3 albedo = vec3(0.0);
vec3 nW = vec3(0.0);
float rough = 0.0, ao = 0.0;
for (int k = 0; k < NL; k++) {
  float wk = gw[k] / tot;
  if (wk < 0.004) continue;
  mat3 tbn;
  vec2 uv = gUv(k, vWorldP, nGeo, tbn);
  vec4 arh = gTex(uGArh, uv, k);
  albedo += gTex(uGAlb, uv, k).rgb * G_TONE[k] * wk;
  nW += tbn * gNor(uv, k) * wk;
  rough += arh.g * wk;
  ao += arh.r * wk;
}
float wetMud = gw[3] / tot;
rough *= 1.0 - wetMud * 0.45;

// The photographs are of lighter country than this: a little darker, and
// slow variation over tens of metres, so a field is not one colour.
albedo *= 0.8 + 0.2 * nL.r;
albedo = mix(albedo, albedo * vec3(1.05, 1.0, 0.86), smoothstep(0.55, 0.8, nL.b) * 0.35);

// Blight: dead ground veined with sick light.
float wbl = gw[6] / tot;
float vein = 1.0 - abs(nM.g * 2.0 - 1.0);
vein = pow(vein, 10.0) + pow(1.0 - abs(nF.r * 2.0 - 1.0), 16.0) * 0.6;
gEmissive = uBlightGlow * vein * wbl * (0.55 + 0.45 * sin(uTime * 1.3 + nL.r * 12.0)) * 1.6;

gNormalW = normalize(nW);
gRough = clamp(rough, 0.3, 1.0);
gAO = mix(1.0, ao, 0.85);
diffuseColor.rgb *= albedo;
`)
        .replace('#include <roughnessmap_fragment>', 'float roughnessFactor = gRough;')
        .replace('#include <normal_fragment_maps>', `#include <normal_fragment_maps>
normal = normalize((viewMatrix * vec4(gNormalW, 0.0)).xyz);`)
        .replace('#include <aomap_fragment>', `
reflectedLight.indirectDiffuse *= gAO;
reflectedLight.indirectSpecular *= gAO;`)
        .replace('#include <emissivemap_fragment>', '#include <emissivemap_fragment>\ntotalEmissiveRadiance += gEmissive;');
    };
    mat.customProgramCacheKey = () => 'terrain-v2';
    ownTextures(mat, this.heightTex, this.splatTex);
    return mat;
  }
}
