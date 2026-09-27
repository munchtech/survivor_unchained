import * as THREE from 'three';
import { noiseTexture } from '../noiseTex';

/* Things painted on the ground: telegraphs (where it is about to hurt) and
 * zones (where it is hurting now).
 *
 * Each decal is a small grid laid over the terrain and conformed to it, so a
 * warning circle on a hillside follows the hill instead of cutting through
 * it. One shader draws every kind; `kind` picks the pattern:
 *
 *   0 telegraph circle   the rim is sharp and the fill rises toward the rim
 *                        as the moment arrives, so you can read the timing
 *   1 telegraph lane     the same, for charges: a lane that fills end to end
 *   2 holy ground        slow-turning ring of glyph marks, warm light
 *   3 fire               licking flames and embers, bright at the centre
 *   4 blight / poison    bubbling sickly green, with dark rot
 *   5 frost              crystalline, cold light
 *   6 thorns / nature    a tangle of green-lit briars
 *   7 generic magic      school colour, soft swirling
 *   8 ring telegraph     only the rim (a caster's reach)
 *   9 elite aura         a gold ring under a champion
 *  10 shadow             a pool of dark with violet edges
 *
 * Hostile telegraphs are warm red; the player's zones are their school. */

const vertex = /* glsl */ `
varying vec2 vLocal;
varying vec3 vWorld;
void main() {
  vLocal = uv * 2.0 - 1.0;
  vec4 w = modelMatrix * vec4(position, 1.0);
  vWorld = w.xyz;
  gl_Position = projectionMatrix * viewMatrix * w;
}
`;

const fragment = /* glsl */ `
uniform int uKind;
uniform vec3 uColor;
uniform vec3 uColor2;
uniform float uTime;
uniform float uProgress;
uniform float uAlpha;
uniform float uAspect;
uniform float uSeed;
uniform sampler2D uNoise;
varying vec2 vLocal;
varying vec3 vWorld;

float ring(float r, float at, float w) { return smoothstep(w, 0.0, abs(r - at)); }

void main() {
  vec2 p = vLocal;
  float r = length(p);
  float a = atan(p.y, p.x);
  vec3 col = uColor;
  float alpha = 0.0;
  vec4 n = texture2D(uNoise, vWorld.xz * 0.21 + uSeed);
  vec4 n2 = texture2D(uNoise, vWorld.xz * 0.53 - uTime * 0.05 + uSeed);

  if (uKind == 0) {
    if (r > 1.0) discard;
    float rim = ring(r, 0.97, 0.05);
    float fill = step(r, uProgress) * 0.35 + smoothstep(uProgress - 0.04, uProgress, r) * step(r, uProgress) * 0.6;
    float inner = 0.12 * (1.0 - r);
    alpha = max(rim * 0.95, fill + inner);
    col = mix(uColor * 0.7, uColor * 1.6, rim);
  } else if (uKind == 1) {
    // Lane: p.y runs from start (-1) to end (+1).
    float ax = abs(p.x);
    if (ax > 1.0) discard;
    float edge = smoothstep(0.82, 0.96, ax);
    float t = (p.y + 1.0) * 0.5;
    float fill = step(t, uProgress) * 0.4;
    float chev = step(0.5, fract(t * 6.0 - uTime * 2.0 - ax * 0.6)) * 0.12;
    alpha = max(edge * 0.9, fill + chev) * smoothstep(1.0, 0.94, abs(p.y));
    col = mix(uColor * 0.7, uColor * 1.5, edge);
  } else if (uKind == 8) {
    if (r > 1.0) discard;
    alpha = ring(r, 0.97, 0.04) * 0.9 + ring(r, 0.97 - fract(uTime * 0.8) * 0.3, 0.03) * 0.4;
  } else if (uKind == 9) {
    if (r > 1.0) discard;
    float marks = step(0.8, fract(a / 6.2831853 * 12.0 + uTime * 0.1));
    alpha = ring(r, 0.86, 0.08) * 0.7 + ring(r, 0.72, 0.02) * marks * 0.6;
  } else {
    if (r > 1.0) discard;
    float edge = smoothstep(1.0, 0.86, r);
    if (uKind == 2) {
      float glyph = step(0.6, fract(a / 6.2831853 * 16.0 + uTime * 0.08)) * ring(r, 0.8, 0.07);
      float inner = ring(r, 0.55, 0.03) + ring(r, 0.93, 0.03);
      float rays = pow(max(0.0, cos(a * 8.0 + uTime * 0.6)), 12.0) * (1.0 - r) * 0.5;
      alpha = (glyph * 0.8 + inner * 0.7 + rays + 0.12 * (1.0 - r)) * edge;
    } else if (uKind == 3) {
      float flame = n2.r * 1.4 - r * 0.9 + n.g * 0.3;
      alpha = smoothstep(0.1, 0.5, flame) * edge;
      col = mix(uColor2, uColor, smoothstep(0.2, 0.7, flame));
    } else if (uKind == 4) {
      float bub = step(0.8, fract(n2.b * 5.0 + uTime * 0.4)) * 0.5;
      float rot = smoothstep(0.3, 0.7, n.r + n2.g * 0.3);
      alpha = (0.35 + bub + rot * 0.25) * edge;
      col = mix(uColor2, uColor, rot + bub);
    } else if (uKind == 5) {
      float cracks = pow(1.0 - abs(n.g * 2.0 - 1.0), 12.0);
      alpha = (0.25 + cracks * 0.8 + ring(r, 0.9, 0.06) * 0.6) * edge;
    } else if (uKind == 6) {
      float briar = pow(1.0 - abs(n.b * 2.0 - 1.0), 8.0) + pow(1.0 - abs(n2.r * 2.0 - 1.0), 10.0);
      alpha = (0.15 + briar * 0.7) * edge;
      col = mix(uColor2, uColor, briar);
    } else if (uKind == 10) {
      float swirl = n2.g;
      alpha = (0.55 + swirl * 0.3) * edge;
      col = mix(uColor2, uColor, smoothstep(0.8, 1.0, r) + swirl * 0.2);
    } else {
      float sw = sin(a * 3.0 + r * 8.0 - uTime * 2.0) * 0.5 + 0.5;
      alpha = (0.18 + sw * 0.25 + ring(r, 0.92, 0.05) * 0.6) * edge;
    }
  }
  alpha *= uAlpha;
  if (alpha < 0.004) discard;
  gl_FragColor = vec4(col, alpha);
}
`;

export interface Decal {
  mesh: THREE.Mesh;
  mat: THREE.ShaderMaterial;
  life: number;
  age: number;
  fadeIn: number;
  fadeOut: number;
  progress: boolean;
  follow: (() => { x: number; z: number }) | null;
  key?: number;
}

export class DecalLayer {
  readonly group = new THREE.Group();
  private list: Decal[] = [];
  private noise = noiseTexture();
  time = 0;

  constructor(private heightAt: (x: number, z: number) => number) { this.group.name = 'decals'; }

  private grid(cx: number, cz: number, hw: number, hd: number, rot: number, seg: number) {
    const g = new THREE.PlaneGeometry(hw * 2, hd * 2, seg, Math.max(2, Math.round(seg * (hd / hw))));
    g.rotateX(-Math.PI / 2);
    const pos = g.getAttribute('position');
    const c = Math.cos(rot), s = Math.sin(rot);
    for (let i = 0; i < pos.count; i++) {
      const lx = pos.getX(i), lz = pos.getZ(i);
      const x = cx + lx * c - lz * s, z = cz + lx * s + lz * c;
      pos.setXYZ(i, x, this.heightAt(x, z) + 0.07, z);
    }
    g.computeBoundingSphere();
    return g;
  }

  private make(geo: THREE.BufferGeometry, kind: number, color: THREE.Color, color2: THREE.Color, blending: THREE.Blending) {
    const mat = new THREE.ShaderMaterial({
      vertexShader: vertex, fragmentShader: fragment, transparent: true, depthWrite: false, blending,
      polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2,
      uniforms: {
        uKind: { value: kind }, uColor: { value: color.clone() }, uColor2: { value: color2.clone() },
        uTime: { value: 0 }, uProgress: { value: 0 }, uAlpha: { value: 0 }, uAspect: { value: 1 },
        uSeed: { value: Math.random() }, uNoise: { value: this.noise },
      },
    });
    const mesh = new THREE.Mesh(geo, mat);
    mesh.renderOrder = 5;
    mesh.frustumCulled = false;
    this.group.add(mesh);
    return { mesh, mat };
  }

  circle(x: number, z: number, radius: number, kind: number, color: THREE.Color, opts: { life: number; color2?: THREE.Color; progress?: boolean; additive?: boolean; fadeIn?: number; fadeOut?: number; follow?: Decal['follow']; key?: number } ) {
    const seg = Math.min(28, Math.max(8, Math.round(radius * 5)));
    const geo = this.grid(x, z, radius, radius, 0, seg);
    const { mesh, mat } = this.make(geo, kind, color, opts.color2 ?? color, opts.additive ? THREE.AdditiveBlending : THREE.NormalBlending);
    const d: Decal = { mesh, mat, life: opts.life, age: 0, fadeIn: opts.fadeIn ?? 0.12, fadeOut: opts.fadeOut ?? 0.25, progress: !!opts.progress, follow: opts.follow ?? null, key: opts.key };
    if (d.follow) {
      // A following decal is laid flat at the origin and moved each frame.
      geo.dispose();
      const flat = new THREE.PlaneGeometry(radius * 2, radius * 2, 1, 1);
      flat.rotateX(-Math.PI / 2);
      mesh.geometry = flat;
    }
    this.list.push(d);
    return d;
  }

  lane(x0: number, z0: number, x1: number, z1: number, width: number, color: THREE.Color, life: number, key?: number) {
    const len = Math.hypot(x1 - x0, z1 - z0);
    const rot = Math.atan2(x1 - x0, z1 - z0);
    const geo = this.grid((x0 + x1) / 2, (z0 + z1) / 2, width / 2, len / 2, -rot, 6);
    const { mesh, mat } = this.make(geo, 1, color, color, THREE.NormalBlending);
    const d: Decal = { mesh, mat, life, age: 0, fadeIn: 0.08, fadeOut: 0.15, progress: true, follow: null, key };
    this.list.push(d);
    return d;
  }

  removeKey(key: number) {
    for (const d of this.list) if (d.key === key) d.life = Math.min(d.life, d.age + d.fadeOut);
  }

  update(dt: number, time: number) {
    this.time = time;
    for (let i = this.list.length - 1; i >= 0; i--) {
      const d = this.list[i];
      d.age += dt;
      const u = d.mat.uniforms;
      u.uTime.value = time;
      if (d.progress) u.uProgress.value = Math.min(1, d.age / Math.max(0.01, d.life));
      const fi = Math.min(1, d.age / d.fadeIn);
      const fo = Math.min(1, (d.life - d.age) / d.fadeOut);
      u.uAlpha.value = Math.max(0, Math.min(fi, fo));
      if (d.follow) {
        const p = d.follow();
        d.mesh.position.set(p.x, this.heightAt(p.x, p.z) + 0.08, p.z);
      }
      if (d.age >= d.life) {
        d.mesh.geometry.dispose();
        d.mat.dispose();
        this.group.remove(d.mesh);
        this.list.splice(i, 1);
      }
    }
  }

  clear() {
    for (const d of this.list) { d.mesh.geometry.dispose(); d.mat.dispose(); this.group.remove(d.mesh); }
    this.list.length = 0;
  }
}
