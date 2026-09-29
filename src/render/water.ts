import * as THREE from 'three';
import { noiseTexture } from './noiseTex';

/* Still and slow water: a river ford, a stream, a well.
 *
 * One plane per body of water. The surface is mirror-smooth in the base
 * material (so it picks up the sky from the environment map and a long
 * glint from the moon or sun), and its normal is broken up in the fragment
 * shader by two layers of the shared noise drifting against each other,
 * which is what makes it read as moving water rather than glass. A fresnel
 * term darkens it looking straight down and brightens it at a grazing
 * angle; a `murk` colour decides whether it is clear, peaty or poisoned. */

export interface WaterOpts {
  width: number;
  depth: number;
  color?: string;
  murk?: string;
  flow?: [number, number];
  opacity?: number;
  glow?: number;
  /** The sky it reflects, added at grazing angles. */
  sky?: string;
  /** Streams only: the colour of the shallows and of the foam at the banks. */
  shallow?: string;
  foam?: string;
}

export const waterUniforms = { uTime: { value: 0 } };

export function createWater(o: WaterOpts): THREE.Mesh {
  const geo = new THREE.PlaneGeometry(o.width, o.depth, 1, 1);
  geo.rotateX(-Math.PI / 2);
  const m = finish(new THREE.Mesh(geo, waterMaterial(o)));
  // Its colours, for tools that read a zone (tools/godot/export_zone.mjs).
  m.userData.water = o;
  return m;
}

function finish(m: THREE.Mesh) {
  m.receiveShadow = true;
  m.renderOrder = 2;
  m.name = 'water';
  return m;
}

/** A stream: a ribbon of water that follows a path downhill.
 *
 *  Given the ground under it, the ribbon knows how deep it is at every
 *  vertex (several lanes across, not just two edges), so the shallows at
 *  the banks can clear to show the mud, scum can gather where it laps the
 *  edge, and the surface can flow along the stream rather than across the
 *  world. */
export function createStream(
  path: Array<[number, number]>, width: number, surface: (x: number, z: number) => number,
  o: Omit<WaterOpts, 'width' | 'depth'>, ground?: (x: number, z: number) => number, lanes = 6,
): THREE.Mesh {
  // Resample the path every metre or so.
  const pts: Array<[number, number]> = [];
  for (let i = 0; i < path.length - 1; i++) {
    const [x0, z0] = path[i], [x1, z1] = path[i + 1];
    const n = Math.max(1, Math.ceil(Math.hypot(x1 - x0, z1 - z0) / 1.2));
    for (let k = 0; k < n; k++) pts.push([x0 + ((x1 - x0) * k) / n, z0 + ((z1 - z0) * k) / n]);
  }
  pts.push(path[path.length - 1]);
  const pos: number[] = [], flow: number[] = [], depth: number[] = [], idx: number[] = [];
  const row = lanes + 1;
  let run = 0;
  let prevY = Infinity;
  for (let i = 0; i < pts.length; i++) {
    const [x, z] = pts[i];
    const [ax, az] = pts[Math.max(0, i - 2)], [bx, bz] = pts[Math.min(pts.length - 1, i + 2)];
    let tx = bx - ax, tz = bz - az;
    const l = Math.hypot(tx, tz) || 1;
    tx /= l; tz /= l;
    const nx = -tz, nz = tx;
    // Water never runs uphill.
    const y = Math.min(prevY, surface(x, z));
    prevY = y;
    if (i > 0) run += Math.hypot(x - pts[i - 1][0], z - pts[i - 1][1]);
    for (let j = 0; j <= lanes; j++) {
      const off = (0.5 - j / lanes) * width;
      const vx = x + nx * off, vz = z + nz * off;
      pos.push(vx, y, vz);
      flow.push(off, run);
      depth.push(ground ? Math.max(-1, Math.min(3, y - ground(vx, vz))) : 1);
    }
    if (i > 0) {
      for (let j = 0; j < lanes; j++) {
        const p = (i - 1) * row + j, q = i * row + j;
        idx.push(p, p + 1, q, p + 1, q + 1, q);
      }
    }
  }
  const geo = new THREE.BufferGeometry();
  geo.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  geo.setAttribute('aFlow', new THREE.Float32BufferAttribute(flow, 2));
  geo.setAttribute('aDepth', new THREE.Float32BufferAttribute(depth, 1));
  geo.setIndex(idx);
  geo.computeVertexNormals();
  const m = finish(new THREE.Mesh(geo, waterMaterial({ ...o, width, depth: run }, true)));
  m.userData.water = o;
  return m;
}

function waterMaterial(o: WaterOpts, stream = false) {
  const mat = new THREE.MeshStandardMaterial({
    color: o.color ?? '#0e1c20', roughness: 0.06, metalness: 0.0, transparent: true, opacity: o.opacity ?? 0.86,
    envMapIntensity: 1.6, depthWrite: false,
  });
  const flow = o.flow ?? [0.02, 0.35];
  const murk = new THREE.Color(o.murk ?? '#061012');
  mat.onBeforeCompile = (sh) => {
    sh.uniforms.uTime = waterUniforms.uTime;
    sh.uniforms.uNoise = { value: noiseTexture() };
    sh.uniforms.uFlow = { value: new THREE.Vector2(...flow) };
    sh.uniforms.uMurk = { value: murk };
    sh.uniforms.uGlow = { value: o.glow ?? 0 };
    sh.uniforms.uSky = { value: new THREE.Color(o.sky ?? '#1c2c3c') };
    sh.uniforms.uShallow = { value: new THREE.Color(o.shallow ?? '#4a4230') };
    sh.uniforms.uFoam = { value: new THREE.Color(o.foam ?? '#cfd8d4') };
    if (stream) sh.defines = { ...(sh.defines ?? {}), STREAM: '' };
    sh.vertexShader = sh.vertexShader
      .replace('#include <common>', `#include <common>
varying vec3 vWPos;
#ifdef STREAM
attribute vec2 aFlow;
attribute float aDepth;
varying vec2 vFlow;
varying float vDepth;
#endif`)
      .replace('#include <worldpos_vertex>', `#include <worldpos_vertex>
vWPos = (modelMatrix * vec4(transformed, 1.0)).xyz;
#ifdef STREAM
vFlow = aFlow;
vDepth = aDepth;
#endif`);
    sh.fragmentShader = sh.fragmentShader
      .replace('#include <common>', `#include <common>
varying vec3 vWPos;
uniform float uTime;
uniform sampler2D uNoise;
uniform vec2 uFlow;
uniform vec3 uMurk;
uniform float uGlow;
uniform vec3 uSky;
uniform vec3 uShallow;
uniform vec3 uFoam;
#ifdef STREAM
varying vec2 vFlow;
varying float vDepth;
#endif
float wh(vec2 p) {
  vec2 a = p * 0.045 + uFlow * uTime * 0.05;
  vec2 b = p * 0.11 - uFlow.yx * uTime * 0.07 + 3.7;
  return texture2D(uNoise, a).g * 0.6 + texture2D(uNoise, b).b * 0.4;
}`)
      .replace('#include <normal_fragment_maps>', `#include <normal_fragment_maps>
{
  float e = 0.35;
  #ifdef STREAM
  // Stream space: across in x, downstream in y, so the ripples travel
  // with the current however the stream bends.
  vec2 wp = vec2(vFlow.x, -vFlow.y);
  #else
  vec2 wp = vWPos.xz;
  #endif
  float h0 = wh(wp);
  float hx = wh(wp + vec2(e, 0.0));
  float hz = wh(wp + vec2(0.0, e));
  vec3 nW = normalize(vec3(-(hx - h0) * 1.3, 1.0, -(hz - h0) * 1.3));
  normal = normalize((viewMatrix * vec4(nW, 0.0)).xyz);
}`)
      .replace('#include <emissivemap_fragment>', `#include <emissivemap_fragment>
{
  float fres = pow(1.0 - clamp(dot(normalize(vViewPosition), normal), 0.0, 1.0), 3.0);
  diffuseColor.rgb = mix(uMurk, diffuseColor.rgb, 0.35 + fres * 0.65);
  totalEmissiveRadiance += uMurk * uGlow * (0.6 + 0.4 * wh(vWPos.xz * 2.0));
  float ripple = smoothstep(0.52, 0.7, wh(vWPos.xz * 1.7));
  totalEmissiveRadiance += uSky * (0.25 + fres * 1.1 + ripple * 0.35);
  #ifdef STREAM
  {
    // Shallows clear towards the mud; scum gathers where it laps the bank.
    float sh = 1.0 - smoothstep(0.0, 0.55, vDepth);
    diffuseColor.rgb = mix(diffuseColor.rgb, uShallow, sh * 0.6);
    totalEmissiveRadiance *= 1.0 - sh * 0.5;
    diffuseColor.a *= mix(1.0, 0.4, sh);
    vec2 fp = vec2(vFlow.x * 1.6, -vFlow.y * 0.9);
    float fn = wh(fp * 2.4) * 0.65 + wh(fp * 6.0 + 11.0) * 0.35;
    float edge = 1.0 - smoothstep(0.02, 0.22, vDepth);
    float streak = smoothstep(0.5, 0.66, fn) * (0.25 + 0.75 * edge);
    float foam = max(edge * smoothstep(0.35, 0.55, fn), streak * 0.35);
    diffuseColor.rgb = mix(diffuseColor.rgb, uFoam, foam * 0.75);
    totalEmissiveRadiance += uFoam * foam * 0.18;
    diffuseColor.a = max(diffuseColor.a, foam * 0.85);
  }
  #endif
}`);
  };
  mat.side = THREE.DoubleSide;
  return mat;
}
