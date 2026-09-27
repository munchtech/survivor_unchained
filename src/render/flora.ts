import * as THREE from 'three';
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js';
import { Rng } from '@/core/rng';
import { Noise2D } from '@/core/math';

/* Procedural vegetation and stone, generated once per variant at load.
 *
 * The rule for stylized foliage seen from above is that a canopy must shade
 * like one soft volume, not like the hundreds of facets it is built from. So
 * every canopy vertex gets a normal pointing out from the canopy's own
 * centre (or out from the trunk axis, for pines) instead of its face normal:
 * the moon then lights a tree as one rounded mass with a bright crown and a
 * dark underside, while the silhouette stays jagged and hand-cut.
 *
 * Colour is per vertex: darker toward the inside and bottom of a canopy,
 * lighter at tips, with a little hue drift between clumps, so a forest has
 * depth even under flat light.
 *
 * All flora share one material family with three extras: wind (sway grows
 * with height), a thin rim light so canopies separate from the grass beneath
 * them, and an occlusion cut-out that dithers away whatever stands between
 * the camera and the survivor. */

type Part = THREE.BufferGeometry;

function colorize(g: THREE.BufferGeometry, fn: (p: THREE.Vector3, n: THREE.Vector3, i: number) => THREE.Color) {
  const pos = g.getAttribute('position');
  const nor = g.getAttribute('normal');
  const col = new Float32Array(pos.count * 3);
  const p = new THREE.Vector3(), n = new THREE.Vector3();
  for (let i = 0; i < pos.count; i++) {
    p.fromBufferAttribute(pos, i);
    n.fromBufferAttribute(nor, i);
    const c = fn(p, n, i);
    col[i * 3] = c.r; col[i * 3 + 1] = c.g; col[i * 3 + 2] = c.b;
  }
  g.setAttribute('color', new THREE.BufferAttribute(col, 3));
  return g;
}

function strip(g: THREE.BufferGeometry) {
  // mergeGeometries needs identical attribute sets.
  for (const k of Object.keys(g.attributes)) if (k !== 'position' && k !== 'normal' && k !== 'color') g.deleteAttribute(k);
  return g.index ? g.toNonIndexed() : g;
}

function trunk(rng: Rng, h: number, r0: number, r1: number, bark: THREE.Color, lean = 0.12): Part {
  const g = new THREE.CylinderGeometry(r1, r0, h, 7, 4, true);
  g.translate(0, h / 2, 0);
  const pos = g.getAttribute('position');
  const lx = rng.range(-lean, lean), lz = rng.range(-lean, lean);
  for (let i = 0; i < pos.count; i++) {
    const y = pos.getY(i);
    const t = y / h;
    pos.setX(i, pos.getX(i) + lx * t * t * h + Math.sin(y * 3.1 + rng.next()) * 0.015);
    pos.setZ(i, pos.getZ(i) + lz * t * t * h);
  }
  g.computeVertexNormals();
  colorize(g, (p) => bark.clone().multiplyScalar(0.7 + 0.35 * Math.min(1, p.y / h) + (Math.sin(p.y * 17) * 0.05)));
  return strip(g);
}

/* ------------------------------------------------------------------ pine -- */
export function pineGeometry(seed: number, height = 9): THREE.BufferGeometry {
  const rng = new Rng(seed * 7919 + 13);
  const H = height * rng.range(0.85, 1.15);
  const parts: Part[] = [];
  const bark = new THREE.Color('#3a2a1f');
  parts.push(trunk(rng, H * 0.5, 0.34, 0.14, bark, 0.05));
  const tiers = rng.int(5, 7);
  const dark = new THREE.Color('#1b3324'), mid = new THREE.Color('#2e583c'), tip = new THREE.Color('#5a8a58');
  const hueDrift = rng.range(-0.02, 0.02);
  for (let t = 0; t < tiers; t++) {
    const f = t / tiers;
    const y0 = H * (0.16 + f * 0.7);
    const th = H * (0.3 - f * 0.1);
    const R = H * (0.27 - f * 0.2) * rng.range(0.9, 1.1);
    const k = 16 + (t < 2 ? 4 : 0);
    const pos: number[] = [], nor: number[] = [], col: number[] = [];
    const apex = new THREE.Vector3(rng.range(-0.08, 0.08), y0 + th, rng.range(-0.08, 0.08));
    const rim: THREE.Vector3[] = [];
    const rot = rng.next() * Math.PI * 2;
    for (let i = 0; i < k; i++) {
      const a = rot + (i / k) * Math.PI * 2;
      const jag = i % 2 === 0 ? rng.range(0.95, 1.15) : rng.range(0.62, 0.78);
      const rr = R * jag;
      const droop = (i % 2 === 0 ? 0.28 : 0.08) * R * rng.range(0.8, 1.2);
      rim.push(new THREE.Vector3(Math.cos(a) * rr, y0 - droop, Math.sin(a) * rr));
    }
    const inner = new THREE.Vector3(0, y0 + th * 0.12, 0);
    const c = new THREE.Color();
    const push = (v: THREE.Vector3, n: THREE.Vector3, cc: THREE.Color) => {
      pos.push(v.x, v.y, v.z); nor.push(n.x, n.y, n.z); col.push(cc.r, cc.g, cc.b);
    };
    const nrm = (v: THREE.Vector3, up: number) => {
      const r = new THREE.Vector3(v.x, 0, v.z);
      if (r.lengthSq() < 1e-6) r.set(0, 0, 0);
      else r.normalize();
      return r.multiplyScalar(0.85).add(new THREE.Vector3(0, up, 0)).normalize();
    };
    const shade = (v: THREE.Vector3, isTip: boolean) => {
      const hgt = (v.y - y0) / th;
      c.copy(dark).lerp(mid, 0.35 + 0.4 * f + hgt * 0.2);
      if (isTip) c.lerp(tip, 0.55 + 0.3 * f);
      c.offsetHSL(hueDrift, 0, 0);
      return c;
    };
    for (let i = 0; i < k; i++) {
      const a = rim[i], b = rim[(i + 1) % k];
      // Upper surface.
      push(apex, new THREE.Vector3(0, 1, 0), shade(apex, false).clone().lerp(tip, 0.25));
      push(b, nrm(b, 0.75), shade(b, (i + 1) % 2 === 0));
      push(a, nrm(a, 0.75), shade(a, i % 2 === 0));
      // Underside, up to a hidden inner point: dark, facing down and out.
      const dn = (v: THREE.Vector3) => nrm(v, -0.4);
      push(inner, new THREE.Vector3(0, -1, 0), dark.clone().multiplyScalar(0.6));
      push(a, dn(a), dark.clone().multiplyScalar(0.8));
      push(b, dn(b), dark.clone().multiplyScalar(0.8));
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
    g.setAttribute('normal', new THREE.Float32BufferAttribute(nor, 3));
    g.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
    parts.push(g);
  }
  const out = mergeGeometries(parts)!;
  out.computeBoundingSphere();
  return out;
}

/* ------------------------------------------------------------- broadleaf -- */
export function broadleafGeometry(seed: number, height = 7.5, palette: 'summer' | 'autumn' | 'sick' = 'summer'): THREE.BufferGeometry {
  const rng = new Rng(seed * 104729 + 7);
  const noise = new Noise2D(seed + 3);
  const H = height * rng.range(0.85, 1.15);
  const parts: Part[] = [];
  const bark = new THREE.Color('#3d2e22');
  parts.push(trunk(rng, H * 0.62, 0.42, 0.2, bark, 0.18));
  // Two short limbs toward the canopy.
  for (let b = 0; b < 2; b++) {
    const limb = new THREE.CylinderGeometry(0.08, 0.16, H * 0.3, 5, 1, true);
    limb.translate(0, H * 0.15, 0);
    limb.rotateZ(rng.range(0.5, 0.9) * (b ? 1 : -1));
    limb.rotateY(rng.next() * Math.PI * 2);
    limb.translate(0, H * 0.42, 0);
    limb.computeVertexNormals();
    colorize(limb, () => bark);
    parts.push(strip(limb));
  }
  const pal = {
    summer: ['#24421f', '#3f6e30', '#6e9a42'],
    autumn: ['#45291a', '#8a4e22', '#d08a34'],
    sick: ['#2a2a22', '#474e36', '#78804e'],
  }[palette].map((h) => new THREE.Color(h));
  const center = new THREE.Vector3(0, H * 0.72, 0);
  const canopyR = H * 0.36;
  const blobs = rng.int(6, 9);
  const c = new THREE.Color();
  for (let i = 0; i < blobs; i++) {
    const a = rng.next() * Math.PI * 2;
    const d = i === 0 ? 0 : rng.range(0.35, 0.8) * canopyR;
    const bc = new THREE.Vector3(Math.cos(a) * d, center.y + rng.range(-0.25, 0.35) * canopyR * (i === 0 ? 0 : 1), Math.sin(a) * d);
    const br = canopyR * rng.range(0.5, 0.75) * (i === 0 ? 1.15 : 1);
    const blob = new THREE.IcosahedronGeometry(br, 2);
    const pos = blob.getAttribute('position');
    for (let v = 0; v < pos.count; v++) {
      const x = pos.getX(v), y = pos.getY(v), z = pos.getZ(v);
      const len = Math.hypot(x, y, z);
      const n = 1 + noise.fbm(x * 0.9 + i * 3.1, z * 0.9 + y * 0.7, 3) * 0.28;
      const flat = y < 0 ? 0.72 : 1; // flatter underside
      pos.setXYZ(v, (x / len) * br * n, (y / len) * br * n * flat, (z / len) * br * n);
    }
    blob.translate(bc.x, bc.y, bc.z);
    // Normals from the canopy centre: one soft volume.
    const nor = blob.getAttribute('normal');
    for (let v = 0; v < pos.count; v++) {
      const dir = new THREE.Vector3(pos.getX(v), pos.getY(v), pos.getZ(v)).sub(center).normalize();
      nor.setXYZ(v, dir.x, dir.y, dir.z);
    }
    const drift = rng.range(-0.025, 0.025);
    colorize(blob, (p, n) => {
      const up = n.y * 0.5 + 0.5;
      c.copy(pal[0]).lerp(pal[1], Math.min(1, up * 1.2));
      c.lerp(pal[2], Math.max(0, up - 0.55) * 1.4 * rng.range(0.7, 1));
      const inner = Math.min(1, p.distanceTo(center) / (canopyR * 1.1));
      c.multiplyScalar(0.7 + 0.3 * inner);
      c.offsetHSL(drift, 0, 0);
      return c;
    });
    parts.push(strip(blob));
  }
  const out = mergeGeometries(parts)!;
  out.computeBoundingSphere();
  return out;
}

/* -------------------------------------------------------------- dead tree -- */
export function deadTreeGeometry(seed: number, height = 7): THREE.BufferGeometry {
  const rng = new Rng(seed * 15485863 + 5);
  const parts: Part[] = [];
  const bark = new THREE.Color('#403a36');
  const moss = new THREE.Color('#3a4430');
  const branch = (base: THREE.Vector3, dir: THREE.Vector3, len: number, r: number, depth: number) => {
    const seg = new THREE.CylinderGeometry(r * 0.62, r, len, 6, 3, true);
    seg.translate(0, len / 2, 0);
    // Gnarl it.
    const pos = seg.getAttribute('position');
    const kx = rng.range(-0.25, 0.25) * len, kz = rng.range(-0.25, 0.25) * len;
    for (let i = 0; i < pos.count; i++) {
      const t = pos.getY(i) / len;
      pos.setX(i, pos.getX(i) + Math.sin(t * Math.PI) * kx * 0.4);
      pos.setZ(i, pos.getZ(i) + Math.sin(t * Math.PI) * kz * 0.4);
    }
    const q = new THREE.Quaternion().setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir.clone().normalize());
    seg.applyQuaternion(q);
    seg.translate(base.x, base.y, base.z);
    seg.computeVertexNormals();
    colorize(seg, (_p, n) => bark.clone().lerp(moss, Math.max(0, n.y) * 0.5).multiplyScalar(0.8 + depth * 0.08));
    parts.push(strip(seg));
    const tip = base.clone().add(dir.clone().normalize().multiplyScalar(len));
    if (depth >= 3 || r < 0.04) return;
    const n = depth === 0 ? rng.int(2, 3) : rng.int(1, 3);
    for (let i = 0; i < n; i++) {
      const nd = dir.clone().normalize()
        .add(new THREE.Vector3(rng.range(-1, 1), rng.range(-0.1, 0.5), rng.range(-1, 1)).multiplyScalar(0.9))
        .normalize();
      const from = base.clone().lerp(tip, rng.range(0.55, 1));
      branch(from, nd, len * rng.range(0.45, 0.7), r * 0.55, depth + 1);
    }
  };
  branch(new THREE.Vector3(0, -0.2, 0), new THREE.Vector3(rng.range(-0.1, 0.1), 1, rng.range(-0.1, 0.1)), height * 0.55, 0.32, 0);
  const out = mergeGeometries(parts)!;
  out.computeBoundingSphere();
  return out;
}

/* ------------------------------------------------------------------- bush -- */
export function bushGeometry(seed: number, size = 1.2, palette: 'green' | 'bramble' | 'berry' = 'green'): THREE.BufferGeometry {
  const rng = new Rng(seed * 31337 + 11);
  const noise = new Noise2D(seed + 9);
  const parts: Part[] = [];
  const pal = {
    green: ['#1a3019', '#2f5226', '#52763a'],
    bramble: ['#1e1f16', '#3a3522', '#5a4a2a'],
    berry: ['#1c2f1c', '#2d4d2a', '#8a2a3a'],
  }[palette].map((h) => new THREE.Color(h));
  const center = new THREE.Vector3(0, size * 0.35, 0);
  const n = rng.int(3, 5);
  const c = new THREE.Color();
  for (let i = 0; i < n; i++) {
    const a = rng.next() * Math.PI * 2;
    const d = i === 0 ? 0 : rng.range(0.3, 0.6) * size;
    const r = size * rng.range(0.4, 0.6);
    const g = new THREE.IcosahedronGeometry(r, 1);
    const pos = g.getAttribute('position');
    for (let v = 0; v < pos.count; v++) {
      const x = pos.getX(v), y = pos.getY(v), z = pos.getZ(v);
      const k = 1 + noise.noise(x * 2 + i, z * 2 + y) * 0.25;
      pos.setXYZ(v, x * k, y * k * 0.8, z * k);
    }
    g.translate(Math.cos(a) * d, r * 0.55, Math.sin(a) * d);
    const nor = g.getAttribute('normal');
    for (let v = 0; v < pos.count; v++) {
      const dir = new THREE.Vector3(pos.getX(v), pos.getY(v), pos.getZ(v)).sub(center).normalize();
      nor.setXYZ(v, dir.x, dir.y, dir.z);
    }
    colorize(g, (_p, nn) => {
      const up = nn.y * 0.5 + 0.5;
      c.copy(pal[0]).lerp(pal[1], up);
      if (palette === 'berry' && rng.next() < 0.12) c.copy(pal[2]);
      else c.lerp(pal[2], Math.max(0, up - 0.6) * (palette === 'berry' ? 0.2 : 1.2));
      return c;
    });
    parts.push(strip(g));
  }
  const out = mergeGeometries(parts)!;
  out.computeBoundingSphere();
  return out;
}

/* ------------------------------------------------------------------- rock -- */
export function rockGeometry(seed: number, size = 1.5, opts: { flat?: number; moss?: number; tint?: string } = {}): THREE.BufferGeometry {
  const rng = new Rng(seed * 6700417 + 3);
  const noise = new Noise2D(seed + 21);
  const g0 = new THREE.IcosahedronGeometry(1, 1);
  const g = g0.toNonIndexed();
  const pos = g.getAttribute('position');
  const flat = opts.flat ?? rng.range(0.45, 0.75);
  const sx = rng.range(0.8, 1.3), sz = rng.range(0.8, 1.3);
  // Displace by position so duplicated vertices of neighbouring faces agree.
  for (let i = 0; i < pos.count; i++) {
    const x = pos.getX(i), y = pos.getY(i), z = pos.getZ(i);
    const k = 1 + noise.fbm(x * 1.3 + 5, z * 1.3 + y * 1.7, 3) * 0.35;
    pos.setXYZ(i, x * k * sx * size, Math.max(y * k * flat * size, -0.25 * size), z * k * sz * size);
  }
  g.computeVertexNormals(); // non-indexed: faceted, which is the point
  const base = new THREE.Color(opts.tint ?? '#8a857a').offsetHSL(rng.range(-0.02, 0.03), rng.range(-0.03, 0.03), rng.range(-0.06, 0.04));
  const moss = new THREE.Color('#4a6a30').offsetHSL(rng.range(-0.03, 0.03), 0, 0);
  const lichen = new THREE.Color('#9a9a6a');
  const mossAmt = opts.moss ?? 0.7;
  const c = new THREE.Color();
  colorize(g, (p, n) => {
    // Faces of one facet share a colour (the three vertices hash the same).
    const fh = Math.abs(Math.sin(Math.round(n.x * 7) * 12.9 + Math.round(n.z * 7) * 78.2 + Math.round(n.y * 7) * 37.7) * 43758.5) % 1;
    c.copy(base).multiplyScalar(0.72 + 0.22 * fh + Math.max(0, p.y / size) * 0.22);
    if (fh > 0.86) c.lerp(lichen, 0.35);
    c.lerp(moss, Math.max(0, n.y - 0.5) * 2.0 * mossAmt);
    return c;
  });
  g.translate(0, 0.05 * size, 0);
  g.computeBoundingSphere();
  return g;
}

/* ---------------------------------------------------------------- material -- */

export const floraUniforms = {
  uTime: { value: 0 },
  // Survivor on screen: pixel x, pixel y, view depth, radius in pixels.
  uOccluder: { value: new THREE.Vector4(0, 0, 0, 0) },
  // Survivor in the world (xyz, w = on) and the way to the camera across
  // the ground: whole trees standing in that lane thin out.
  uFocus: { value: new THREE.Vector4(0, 0, 0, 0) },
  uCamXZ: { value: new THREE.Vector2(0, 1) },
  uRim: { value: new THREE.Color('#6d86b8') },
};

/** Per frame: where the survivor is on screen (in drawing-buffer pixels) and
 *  how far from the camera, so whatever stands in front of them can be
 *  dithered away. */
export function setOccluder(px: number, py: number, viewDepth: number, radiusPx: number) {
  floraUniforms.uOccluder.value.set(px, py, viewDepth, radiusPx);
}

/** Per frame: the survivor's feet and the camera, for the tree lane. */
export function setFocus(x: number, y: number, z: number, camX: number, camZ: number, on = true) {
  floraUniforms.uFocus.value.set(x, y, z, on ? 1 : 0);
  const dx = camX - x, dz = camZ - z, l = Math.hypot(dx, dz) || 1;
  floraUniforms.uCamXZ.value.set(dx / l, dz / l);
}

/** Shared fragment code for the occlusion cut-out; buildings use it too. */
export const OCCLUDE_PARS = /* glsl */ `
uniform vec4 uOccluder;
float bayer4(vec2 p) {
  ivec2 i = ivec2(mod(p, 4.0));
  int idx = i.x + i.y * 4;
  int m[16] = int[16](0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5);
  return (float(m[idx]) + 0.5) / 16.0;
}`;
export const OCCLUDE_FRAG = /* glsl */ `
if (uOccluder.w > 0.0 && -vViewPosition.z < uOccluder.z - 1.2) {
  float dd = length(gl_FragCoord.xy - uOccluder.xy) / uOccluder.w;
  float fade = 1.0 - smoothstep(0.5, 1.0, dd);
  if (fade > 0.0 && bayer4(gl_FragCoord.xy) < fade * 0.82) discard;
}`;

export function floraMaterial(opts: { wind?: number; rim?: number; occlude?: boolean; flatShading?: boolean } = {}) {
  const mat = new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 0.88, metalness: 0, flatShading: !!opts.flatShading });
  const wind = opts.wind ?? 0;
  const rim = opts.rim ?? 0.35;
  const occlude = opts.occlude ?? true;
  mat.onBeforeCompile = (shader) => {
    Object.assign(shader.uniforms, floraUniforms);
    shader.vertexShader = shader.vertexShader
      .replace('#include <common>', `#include <common>
uniform float uTime;
uniform vec4 uFocus;
uniform vec2 uCamXZ;
varying float vLane;`)
      .replace('#include <begin_vertex>', `#include <begin_vertex>
{
  vec3 ip = vec3(0.0);
  vLane = 0.0;
  #ifdef USE_INSTANCING
  ip = vec3(instanceMatrix[3][0], instanceMatrix[3][1], instanceMatrix[3][2]);
  ${occlude ? `{
    // Standing between the survivor and the camera: thin the whole tree.
    vec2 d = ip.xz - uFocus.xz;
    float along = dot(d, uCamXZ);
    float lat = length(d - along * uCamXZ);
    float reach = length(instanceMatrix[0].xyz);
    vLane = uFocus.w * smoothstep(-2.5 * reach, 0.5, along) * (1.0 - smoothstep(13.0, 18.0, along))
          * (1.0 - smoothstep(4.0 * reach, 6.5 * reach, lat));
    // Anything standing close around the survivor thins a little too, so
    // the ground the fight is on stays readable.
    vLane = max(vLane, uFocus.w * 0.55 * (1.0 - smoothstep(5.0 * reach, 8.5 * reach, length(d))));
  }` : ''}
  #endif
  float h = max(position.y, 0.0);
  float ph = uTime * 1.1 + ip.x * 0.23 + ip.z * 0.19;
  float sway = (sin(ph) * 0.65 + sin(ph * 2.3 + 1.7) * 0.25 + sin(ph * 5.1 + ip.x) * 0.1) * ${wind.toFixed(4)} * h * h * 0.02;
  transformed.x += sway;
  transformed.z += sway * 0.5;
}`);
    shader.fragmentShader = shader.fragmentShader
      .replace('#include <common>', `#include <common>
uniform vec3 uRim;
varying float vLane;
${OCCLUDE_PARS}`)
      .replace('#include <clipping_planes_fragment>', `#include <clipping_planes_fragment>
${occlude ? OCCLUDE_FRAG : ''}
${occlude ? 'if (vLane > 0.0 && bayer4(gl_FragCoord.xy + 1.0) < vLane * 0.9) discard;' : ''}`)
      .replace('#include <emissivemap_fragment>', `#include <emissivemap_fragment>
{
  vec3 vdir = normalize(vViewPosition);
  float rimT = pow(1.0 - clamp(dot(normalize(normal), vdir), 0.0, 1.0), 3.0);
  totalEmissiveRadiance += uRim * rimT * ${rim.toFixed(3)} * diffuseColor.rgb * 2.0;
}`);
  };
  mat.customProgramCacheKey = () => `flora2-${wind}-${rim}-${occlude}-${!!opts.flatShading}`;
  return mat;
}
