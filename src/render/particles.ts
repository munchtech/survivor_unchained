import * as THREE from 'three';

/* Particles, simulated entirely on the GPU.
 *
 * A spawn writes one slot of a ring buffer: where, how fast, which way
 * gravity pulls, how long it lives, how big and what colour at birth and at
 * death, and a shape. The vertex shader works out where that particle is
 * now from its birth time alone - there is no per-frame CPU work per
 * particle at all, so a screen full of sparks costs one draw and one uniform.
 *
 * Shapes are drawn in the fragment shader, no textures:
 *   0 soft glow   1 spark (stretched along its velocity)   2 ring
 *   3 star        4 smoke puff (noisy, alpha)              5 square shard
 *
 * Two instances of this system run: additive for light (sparks, embers,
 * glows, magic) and alpha-blended for matter (smoke, dust, dirt, blood). */

export interface ParticleOpts {
  x: number; y: number; z: number;
  vx?: number; vy?: number; vz?: number;
  gravity?: number;
  drag?: number;
  life: number;
  size: number;
  sizeEnd?: number;
  color: THREE.Color | number;
  colorEnd?: THREE.Color | number;
  alpha?: number;
  shape?: 0 | 1 | 2 | 3 | 4 | 5;
  spin?: number;
}

const vertex = /* glsl */ `
uniform float uTime;
uniform float uPixelScale;
attribute vec4 aPos;     // x y z birth
attribute vec4 aVel;     // vx vy vz life
attribute vec4 aPhys;    // gravity drag size sizeEnd
attribute vec4 aCol;     // rgb alpha
attribute vec4 aColEnd;  // rgb shape
attribute float aSpin;
varying vec4 vCol;
varying vec2 vUv;
varying float vShape;
varying float vAge;
varying vec2 vStretch;
void main() {
  float age = uTime - aPos.w;
  float life = aVel.w;
  float k = age / life;
  if (k < 0.0 || k > 1.0 || life <= 0.0) { gl_Position = vec4(2.0, 2.0, 2.0, 1.0); return; }
  float drag = aPhys.y;
  // Exponential drag, integrated: distance = v * (1 - e^-dt) / d.
  float dd = drag > 0.001 ? (1.0 - exp(-drag * age)) / drag : age;
  vec3 p = aPos.xyz + aVel.xyz * dd + vec3(0.0, -0.5 * aPhys.x * age * age, 0.0);
  vec3 vel = aVel.xyz * exp(-drag * age) + vec3(0.0, -aPhys.x * age, 0.0);
  float size = mix(aPhys.z, aPhys.w, k);
  vec4 mv = modelViewMatrix * vec4(p, 1.0);
  // Camera-facing quad; sparks stretch along their screen-space velocity.
  vec2 corner = position.xy;
  vUv = corner;
  vShape = aColEnd.a;
  vec2 dir = vec2(1.0, 0.0);
  float stretch = 1.0;
  if (vShape > 0.5 && vShape < 1.5) {
    vec4 mv2 = modelViewMatrix * vec4(p + vel * 0.05, 1.0);
    vec2 d = mv2.xy - mv.xy;
    float l = length(d);
    if (l > 1e-4) { dir = d / l; stretch = 1.0 + min(l * 40.0, 6.0); }
  }
  float c = cos(aSpin * age), s = sin(aSpin * age);
  if (vShape > 0.5 && vShape < 1.5) { c = dir.x; s = dir.y; }
  vec2 rc = vec2(corner.x * c - corner.y * s, corner.x * s + corner.y * c);
  if (vShape > 0.5 && vShape < 1.5) rc = dir * corner.x * stretch * size + vec2(-dir.y, dir.x) * corner.y * size * 0.35;
  else rc *= size;
  mv.xy += rc;
  gl_Position = projectionMatrix * mv;
  vec3 col = mix(aCol.rgb, aColEnd.rgb, k);
  float fade = smoothstep(0.0, 0.08, k) * (1.0 - smoothstep(0.55, 1.0, k));
  vCol = vec4(col, aCol.a * fade);
  vAge = k;
}
`;

const fragment = /* glsl */ `
varying vec4 vCol;
varying vec2 vUv;
varying float vShape;
varying float vAge;
float hash(vec2 p) { return fract(sin(dot(p, vec2(12.9898, 78.233))) * 43758.5453); }
float vnoise(vec2 p) {
  vec2 i = floor(p), f = fract(p);
  f = f * f * (3.0 - 2.0 * f);
  return mix(mix(hash(i), hash(i + vec2(1, 0)), f.x), mix(hash(i + vec2(0, 1)), hash(i + vec2(1, 1)), f.x), f.y);
}
void main() {
  vec2 uv = vUv;
  float r = length(uv);
  float a;
  if (vShape < 0.5) a = exp(-r * r * 5.5);
  else if (vShape < 1.5) a = exp(-r * r * 4.0) * smoothstep(1.0, 0.2, abs(uv.y) * 2.0);
  else if (vShape < 2.5) a = smoothstep(0.15, 0.0, abs(r - 0.7)) ;
  else if (vShape < 3.5) { float st = max(0.0, 1.0 - abs(uv.x * uv.y) * 22.0) * (1.0 - r); a = st + exp(-r * r * 14.0); }
  else if (vShape < 4.5) { float n = vnoise(uv * 3.0 + vAge * 2.0) * 0.5 + vnoise(uv * 7.0 - vAge) * 0.5; a = smoothstep(1.0, 0.2, r + n * 0.5) ; }
  else a = step(max(abs(uv.x), abs(uv.y)), 0.5);
  a *= vCol.a;
  if (a < 0.003) discard;
  gl_FragColor = vec4(vCol.rgb * (vShape < 4.5 && vShape > 3.5 ? 1.0 : 1.0), a);
}
`;

export class ParticleSystem {
  readonly mesh: THREE.Mesh;
  private geo: THREE.InstancedBufferGeometry;
  private aPos: THREE.InstancedBufferAttribute;
  private aVel: THREE.InstancedBufferAttribute;
  private aPhys: THREE.InstancedBufferAttribute;
  private aCol: THREE.InstancedBufferAttribute;
  private aColEnd: THREE.InstancedBufferAttribute;
  private aSpin: THREE.InstancedBufferAttribute;
  private head = 0;
  private dirtyFrom = Infinity;
  private dirtyTo = -1;
  private material: THREE.ShaderMaterial;
  private c0 = new THREE.Color();
  private c1 = new THREE.Color();
  time = 0;

  constructor(readonly capacity: number, additive: boolean) {
    const quad = new THREE.PlaneGeometry(2, 2);
    this.geo = new THREE.InstancedBufferGeometry();
    this.geo.index = quad.index;
    this.geo.setAttribute('position', quad.getAttribute('position'));
    const mk = (n: number) => {
      const a = new THREE.InstancedBufferAttribute(new Float32Array(capacity * n), n);
      a.setUsage(THREE.DynamicDrawUsage);
      return a;
    };
    this.aPos = mk(4); this.aVel = mk(4); this.aPhys = mk(4); this.aCol = mk(4); this.aColEnd = mk(4); this.aSpin = mk(1);
    this.geo.setAttribute('aPos', this.aPos);
    this.geo.setAttribute('aVel', this.aVel);
    this.geo.setAttribute('aPhys', this.aPhys);
    this.geo.setAttribute('aCol', this.aCol);
    this.geo.setAttribute('aColEnd', this.aColEnd);
    this.geo.setAttribute('aSpin', this.aSpin);
    this.geo.instanceCount = capacity;
    this.material = new THREE.ShaderMaterial({
      vertexShader: vertex, fragmentShader: fragment,
      uniforms: { uTime: { value: 0 }, uPixelScale: { value: 1 } },
      transparent: true, depthWrite: false,
      blending: additive ? THREE.AdditiveBlending : THREE.NormalBlending,
    });
    this.mesh = new THREE.Mesh(this.geo, this.material);
    this.mesh.frustumCulled = false;
    this.mesh.renderOrder = additive ? 20 : 10;
  }

  spawn(o: ParticleOpts) {
    const i = this.head;
    this.head = (this.head + 1) % this.capacity;
    this.aPos.setXYZW(i, o.x, o.y, o.z, this.time);
    this.aVel.setXYZW(i, o.vx ?? 0, o.vy ?? 0, o.vz ?? 0, o.life);
    this.aPhys.setXYZW(i, o.gravity ?? 0, o.drag ?? 0, o.size, o.sizeEnd ?? o.size);
    this.c0.set(o.color);
    this.c1.set(o.colorEnd ?? o.color);
    this.aCol.setXYZW(i, this.c0.r, this.c0.g, this.c0.b, o.alpha ?? 1);
    this.aColEnd.setXYZW(i, this.c1.r, this.c1.g, this.c1.b, o.shape ?? 0);
    this.aSpin.setX(i, o.spin ?? 0);
    if (i < this.dirtyFrom) this.dirtyFrom = i;
    if (i > this.dirtyTo) this.dirtyTo = i;
  }

  update(time: number) {
    this.time = time;
    this.material.uniforms.uTime.value = time;
    if (this.dirtyTo >= 0) {
      for (const a of [this.aPos, this.aVel, this.aPhys, this.aCol, this.aColEnd, this.aSpin]) {
        a.clearUpdateRanges();
        a.addUpdateRange(this.dirtyFrom * a.itemSize, (this.dirtyTo - this.dirtyFrom + 1) * a.itemSize);
        a.needsUpdate = true;
      }
      this.dirtyFrom = Infinity;
      this.dirtyTo = -1;
    }
  }
}
