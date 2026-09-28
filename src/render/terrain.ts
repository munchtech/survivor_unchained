import * as THREE from 'three';
import { noiseTexture } from './noiseTex';
import { ownTextures } from './dispose';
import { clamp } from '@/core/math';

/* The ground, which from a top-down camera is most of every frame.
 *
 * A heightfield sampled from the zone's height function, painted from its
 * paint function into a splat texture (dirt, flagstone, blight, mud), and
 * shaded by one extended MeshStandardMaterial:
 *
 *   - grass is two greens and a dry straw broken up by noise at three scales,
 *     so no two metres of meadow are the same colour;
 *   - splat edges are pushed around by noise before they are thresholded, so
 *     a road frays into the grass instead of ending on a smooth gradient;
 *   - steep faces turn to layered rock whatever the paint says;
 *   - flagstone is laid in offset courses with mortar lines;
 *   - blight glows along ridged veins (it feeds the bloom pass);
 *   - a bump from fine noise gives every surface grain under a low light.
 *
 * heightAt() is the authority for where the ground is, for the simulation as
 * much as for rendering. */

export interface TerrainPaint { dirt: number; stone: number; blight: number; mud: number }

export interface TerrainPalette {
  grassDark: string; grassLight: string; grassDry: string;
  dirt: string; dirtDark: string; stone: string; mortar: string;
  rock: string; rockDark: string; blight: string; blightGlow: string; mud: string;
}

export const DEFAULT_PALETTE: TerrainPalette = {
  grassDark: '#2a4a1f', grassLight: '#4f7a2e', grassDry: '#8a8a42',
  dirt: '#6e5a3c', dirtDark: '#3a2e20', stone: '#66615a', mortar: '#221f19',
  rock: '#6f6b63', rockDark: '#35322e', blight: '#2a2530', blightGlow: '#8cff5a', mud: '#2a2419',
};

export interface TerrainSource {
  size: number; // metres per side, centred on the origin
  resolution: number; // vertices per side
  height(x: number, z: number): number;
  paint(x: number, z: number, out: TerrainPaint): void;
  palette?: Partial<TerrainPalette>;
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
    const col = (h: string) => new THREE.Color(h);
    const uniforms = this.uniforms = {
      uNoise: { value: noiseTexture() },
      uSplat: { value: this.splatTex },
      uSize: { value: this.size },
      uHalf: { value: this.half },
      uTime: { value: 0 },
      uGrassDark: { value: col(pal.grassDark) }, uGrassLight: { value: col(pal.grassLight) },
      uGrassDry: { value: col(pal.grassDry) }, uDirt: { value: col(pal.dirt) }, uDirtDark: { value: col(pal.dirtDark) },
      uStone: { value: col(pal.stone) }, uMortar: { value: col(pal.mortar) }, uRock: { value: col(pal.rock) },
      uRockDark: { value: col(pal.rockDark) }, uBlight: { value: col(pal.blight) },
      uBlightGlow: { value: col(pal.blightGlow) }, uMud: { value: col(pal.mud) },
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
uniform float uSize;
uniform float uHalf;
uniform float uTime;
uniform vec3 uGrassDark, uGrassLight, uGrassDry, uDirt, uDirtDark, uStone, uMortar, uRock, uRockDark, uBlight, uBlightGlow, uMud;
float gBump = 0.0;
float gRough = 0.95;
vec3 gEmissive = vec3(0.0);
float hash12(vec2 p) { vec3 p3 = fract(vec3(p.xyx) * 0.1031); p3 += dot(p3, p3.yzx + 33.33); return fract((p3.x + p3.y) * p3.z); }
`)
        .replace('#include <map_fragment>', `
vec2 w = vWorldP.xz;
vec4 nL = texture2D(uNoise, w * 0.011);
vec4 nM = texture2D(uNoise, w * 0.061 + 0.37);
vec4 nF = texture2D(uNoise, w * 0.29 + 0.71);
vec4 nX = texture2D(uNoise, w * 1.37);
vec4 sp = texture2D(uSplat, (w + uHalf) / uSize);

// Meadow.
float g = nL.r * 0.55 + nM.g * 0.45;
vec3 grass = mix(uGrassDark, uGrassLight, smoothstep(0.32, 0.72, g));
grass = mix(grass, uGrassDry, smoothstep(0.58, 0.78, nL.b) * 0.55);
grass *= 0.82 + 0.36 * nF.a;
grass = mix(grass, grass * vec3(0.78, 0.86, 0.7), smoothstep(0.55, 0.75, nX.r) * 0.35);
float grassBump = nF.a * 0.6 + nX.g * 0.4;

// Dirt, with pebbles.
vec3 dirt = mix(uDirtDark, uDirt, smoothstep(0.25, 0.8, nM.r * 0.7 + nF.b * 0.3));
float pebble = smoothstep(0.78, 0.84, nX.a) * smoothstep(0.4, 0.6, nF.r);
dirt = mix(dirt, uStone * 0.85, pebble * 0.7);
dirt *= 0.9 + 0.2 * nX.b;
float dirtBump = nF.b * 0.5 + pebble * 0.8 + nX.b * 0.3;

// Cobbles: jittered Voronoi cells, each a rounded stone set in dark,
// mossy mortar. Distance to the nearest cell border gives both the mortar
// line and a domed bump, so each stone catches the light on its crown.
vec2 cp = w * 1.3;
vec2 ci = floor(cp);
vec2 cf = fract(cp);
float d1 = 8.0, d2 = 8.0;
vec2 id1 = vec2(0.0);
for (int yy = -1; yy <= 1; yy++) {
  for (int xx = -1; xx <= 1; xx++) {
    vec2 o = vec2(float(xx), float(yy));
    vec2 hh = vec2(hash12(ci + o), hash12(ci + o + 19.19));
    vec2 rr = o + 0.12 + hh * 0.76 - cf;
    float dd = dot(rr, rr);
    if (dd < d1) { d2 = d1; d1 = dd; id1 = ci + o; }
    else if (dd < d2) { d2 = dd; }
  }
}
float edgeD = sqrt(d2) - sqrt(d1);
float mortarW = 1.0 - smoothstep(0.05, 0.17, edgeD + (nX.r - 0.5) * 0.08);
float tint = hash12(id1);
vec3 stone = mix(uStone * vec3(0.78, 0.8, 0.84), uStone * vec3(1.08, 1.02, 0.94), tint);
stone *= 0.82 + 0.3 * nF.g;
stone = mix(stone, stone * vec3(0.72, 0.84, 0.62), smoothstep(0.55, 0.8, nM.b + tint * 0.2) * 0.55);
vec3 mortar = mix(uMortar, uMortar * vec3(0.9, 1.25, 0.8), nF.r);
// Filth: soot, spilt ale, what the carts leave; the stones are not clean.
float filth = smoothstep(0.5, 0.85, nM.r * 0.7 + nF.b * 0.5);
stone = mix(stone, stone * vec3(0.55, 0.52, 0.46), filth * 0.7);
stone = mix(stone, mortar, mortarW);
float stoneBump = smoothstep(0.0, 0.3, edgeD) * (0.7 + 0.3 * tint) + nX.a * 0.12;

// Rock on steep faces.
float slope = 1.0 - clamp(vWorldN.y, 0.0, 1.0);
float strata = sin(vWorldP.y * 3.1 + nM.r * 4.0) * 0.5 + 0.5;
vec3 rock = mix(uRockDark, uRock, strata * 0.6 + nF.r * 0.4);
float rockBump = strata * 0.7 + nX.r * 0.4;

// Blight: dead ground veined with sick light.
float vein = 1.0 - abs(nM.g * 2.0 - 1.0);
vein = pow(vein, 10.0) + pow(1.0 - abs(nF.r * 2.0 - 1.0), 16.0) * 0.6;
vec3 blight = uBlight * (0.75 + 0.5 * nF.g);

// Mud: dark, wet, glossy.
vec3 mud = uMud * (0.8 + 0.4 * nF.b);

// Noise-frayed weights.
float wd = smoothstep(0.35, 0.65, sp.r + (nM.b - 0.5) * 0.45 + (nX.g - 0.5) * 0.12);
float ws = smoothstep(0.35, 0.65, sp.g + (nM.g - 0.5) * 0.35 + (nX.b - 0.5) * 0.15);
float wb = smoothstep(0.3, 0.7, sp.b + (nM.r - 0.5) * 0.5);
float wm = smoothstep(0.35, 0.65, sp.a + (nM.g - 0.5) * 0.4);
float wr = smoothstep(0.32, 0.5, slope + (nM.b - 0.5) * 0.15);

vec3 albedo = grass;
float bump = grassBump;
float rough = 0.96;
albedo = mix(albedo, dirt, wd); bump = mix(bump, dirtBump, wd); rough = mix(rough, 0.92, wd);
albedo = mix(albedo, mud, wm); bump = mix(bump, nF.b * 0.3, wm); rough = mix(rough, 0.38, wm);
albedo = mix(albedo, stone, ws); bump = mix(bump, stoneBump, ws); rough = mix(rough, 0.86, ws);
albedo = mix(albedo, blight, wb); bump = mix(bump, vein * 0.6 + nF.r * 0.3, wb);
albedo = mix(albedo, rock, wr); bump = mix(bump, rockBump, wr); rough = mix(rough, 0.9, wr);

// Soft contact darkening in hollows reads as ambient occlusion from above.
albedo *= 0.88 + 0.24 * smoothstep(0.2, 0.8, nL.g);

gEmissive = uBlightGlow * vein * wb * (0.55 + 0.45 * sin(uTime * 1.3 + nL.r * 12.0)) * 1.6;
gBump = bump;
gRough = rough;
diffuseColor.rgb *= albedo;
`)
        .replace('#include <roughnessmap_fragment>', 'float roughnessFactor = gRough;')
        .replace('#include <normal_fragment_maps>', `#include <normal_fragment_maps>
{
  vec3 dpdx = dFdx(-vViewPosition);
  vec3 dpdy = dFdy(-vViewPosition);
  float bh = gBump * 0.06;
  float dhdx = dFdx(bh);
  float dhdy = dFdy(bh);
  vec3 r1 = cross(dpdy, normal);
  vec3 r2 = cross(normal, dpdx);
  float det = dot(dpdx, r1);
  vec3 grad = sign(det) * (dhdx * r1 + dhdy * r2);
  normal = normalize(abs(det) * normal - grad);
}`)
        .replace('#include <emissivemap_fragment>', '#include <emissivemap_fragment>\ntotalEmissiveRadiance += gEmissive;');
    };
    mat.customProgramCacheKey = () => 'terrain-v1';
    ownTextures(mat, this.heightTex, this.splatTex);
    return mat;
  }
}
