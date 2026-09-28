import * as THREE from 'three';
import { keep } from './dispose';

/* One tiling texture of value noise, four octaves in four channels, shared by
 * every procedural material (terrain, grass tint, rock breakup, water). A
 * texture fetch is far cheaper than evaluating noise in a fragment shader,
 * and one 256px tile repeated at a few scales hides its own repetition. */

let cached: THREE.DataTexture | null = null;

function hash(x: number, y: number, s: number) {
  let h = (x * 374761393 + y * 668265263 + s * 982451653) | 0;
  h = Math.imul(h ^ (h >>> 13), 1274126177);
  h ^= h >>> 16;
  return (h >>> 0) / 4294967296;
}

function tileNoise(u: number, v: number, period: number, seed: number) {
  const x = u * period, y = v * period;
  const xi = Math.floor(x), yi = Math.floor(y);
  const xf = x - xi, yf = y - yi;
  const sx = xf * xf * (3 - 2 * xf), sy = yf * yf * (3 - 2 * yf);
  const w = (i: number) => ((i % period) + period) % period;
  const a = hash(w(xi), w(yi), seed), b = hash(w(xi + 1), w(yi), seed);
  const c = hash(w(xi), w(yi + 1), seed), d = hash(w(xi + 1), w(yi + 1), seed);
  return (a + (b - a) * sx) + ((c + (d - c) * sx) - (a + (b - a) * sx)) * sy;
}

function fbmTile(u: number, v: number, base: number, seed: number) {
  let sum = 0, amp = 0.5, norm = 0, p = base;
  for (let o = 0; o < 4; o++) {
    sum += tileNoise(u, v, p, seed + o * 17) * amp;
    norm += amp;
    amp *= 0.5;
    p *= 2;
  }
  return sum / norm;
}

export function noiseTexture(): THREE.DataTexture {
  if (cached) return cached;
  const N = 256;
  const data = new Uint8Array(N * N * 4);
  for (let y = 0; y < N; y++) {
    for (let x = 0; x < N; x++) {
      const u = x / N, v = y / N;
      const i = (y * N + x) * 4;
      data[i] = Math.round(fbmTile(u, v, 4, 1) * 255);
      data[i + 1] = Math.round(fbmTile(u, v, 8, 2) * 255);
      data[i + 2] = Math.round(fbmTile(u, v, 16, 3) * 255);
      data[i + 3] = Math.round(tileNoise(u, v, 64, 4) * 255);
    }
  }
  const t = new THREE.DataTexture(data, N, N, THREE.RGBAFormat);
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.magFilter = THREE.LinearFilter;
  t.minFilter = THREE.LinearMipmapLinearFilter;
  t.generateMipmaps = true;
  t.anisotropy = 8;
  t.needsUpdate = true;
  cached = keep(t); // shared by every zone's ground, grass and water
  return t;
}
