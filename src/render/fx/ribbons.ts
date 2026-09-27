import * as THREE from 'three';

/* Shaped light: lightning, beams, sword arcs, novas and bolts from the sky.
 *
 * All additive, all short-lived, all driven by one small shader family.
 * Lightning is rebuilt every frame with fresh jitter so it crawls rather
 * than hangs; an arc sweeps from where the blade starts to where it ends;
 * a nova is a wavefront that leaves a fading wake. */

const ribbonVert = /* glsl */ `
attribute float aT;   // along the ribbon 0..1
attribute float aS;   // across -1..1
varying float vT;
varying float vS;
void main() {
  vT = aT; vS = aS;
  gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
}
`;

const ribbonFrag = /* glsl */ `
uniform vec3 uCore;
uniform vec3 uGlow;
uniform float uAlpha;
uniform float uTime;
uniform int uKind; // 0 lightning, 1 beam, 2 slash, 3 pillar
uniform float uHead;
varying float vT;
varying float vS;
void main() {
  float s = abs(vS);
  float core = smoothstep(0.35, 0.0, s);
  float glow = smoothstep(1.0, 0.0, s);
  float a = 0.0;
  if (uKind == 0) {
    a = core + glow * 0.55;
  } else if (uKind == 1) {
    float scroll = 0.6 + 0.4 * sin(vT * 60.0 - uTime * 40.0);
    a = core * 1.2 + glow * 0.5 * scroll;
    a *= smoothstep(0.0, 0.03, vT) * smoothstep(1.0, 0.9, vT);
  } else if (uKind == 2) {
    // A blade's smear: a thin, hot outer edge that leads the swing, and a
    // fading wake behind it that thins toward the inside of the arc.
    float behind = uHead - vT;
    if (behind < -0.02) discard;
    float wake = exp(-max(behind, 0.0) * 5.5);
    float lb = behind * 16.0;
    float lead = exp(-lb * lb);
    float across = (vS + 1.0) * 0.5;               // 0 inner .. 1 outer
    float edgeLine = smoothstep(0.78, 0.97, across) * smoothstep(1.0, 0.97, across);
    float body = pow(across, 2.2) * 0.55;
    a = (edgeLine * 1.2 + body) * (wake * 0.8 + lead * 0.9);
    gl_FragColor = vec4(mix(uGlow, uCore, edgeLine * (0.4 + lead * 0.6)), clamp(a * uAlpha, 0.0, 1.0));
    return;
  } else {
    a = core * 1.4 + glow * 0.4;
    a *= smoothstep(0.0, 0.1, vT) * (1.0 - vT * 0.6);
  }
  a *= uAlpha;
  if (a < 0.004) discard;
  gl_FragColor = vec4(mix(uGlow, uCore, core), a);
}
`;

const novaFrag = /* glsl */ `
uniform vec3 uCore;
uniform vec3 uGlow;
uniform float uFront;
uniform float uAlpha;
uniform float uRings;
varying vec2 vUv;
void main() {
  vec2 p = vUv * 2.0 - 1.0;
  float r = length(p);
  if (r > 1.0) discard;
  float wd = (r - uFront) * 14.0;
  float wave = exp(-wd * wd);
  float wake = smoothstep(uFront, uFront - 0.5, r) * step(r, uFront) * 0.18;
  float extra = 0.0;
  for (float i = 1.0; i <= 3.0; i++) {
    if (i > uRings) break;
    float f = uFront - i * 0.16;
    float ed = (r - f) * 22.0;
    extra += exp(-ed * ed) * 0.45 * step(0.0, f);
  }
  float a = (wave + wake + extra) * uAlpha;
  if (a < 0.004) discard;
  gl_FragColor = vec4(mix(uGlow, uCore, wave), a);
}
`;

interface Fx {
  mesh: THREE.Mesh;
  mat: THREE.ShaderMaterial;
  age: number;
  life: number;
  kind: 'lightning' | 'beam' | 'slash' | 'pillar' | 'nova';
  points?: number[];
  width?: number;
  y?: number;
  expand?: number;
}

export class RibbonLayer {
  readonly group = new THREE.Group();
  private list: Fx[] = [];
  private camPos = new THREE.Vector3();

  constructor() { this.group.name = 'ribbons'; }

  private material(kind: number, core: THREE.Color, glow: THREE.Color) {
    return new THREE.ShaderMaterial({
      vertexShader: ribbonVert, fragmentShader: ribbonFrag, transparent: true, depthWrite: false,
      blending: THREE.AdditiveBlending, side: THREE.DoubleSide,
      uniforms: { uCore: { value: core.clone() }, uGlow: { value: glow.clone() }, uAlpha: { value: 1 }, uTime: { value: 0 }, uKind: { value: kind }, uHead: { value: 0 } },
    });
  }

  /** A polyline ribbon facing the camera; `pts` are x,y,z triples. */
  private ribbon(geo: THREE.BufferGeometry, pts: THREE.Vector3[], width: number) {
    const n = pts.length;
    const pos = new Float32Array(n * 2 * 3);
    const t = new Float32Array(n * 2);
    const s = new Float32Array(n * 2);
    const idx: number[] = [];
    const tmp = new THREE.Vector3(), side = new THREE.Vector3(), view = new THREE.Vector3();
    let total = 0;
    const acc = [0];
    for (let i = 1; i < n; i++) { total += pts[i].distanceTo(pts[i - 1]); acc.push(total); }
    for (let i = 0; i < n; i++) {
      const a = pts[Math.max(0, i - 1)], b = pts[Math.min(n - 1, i + 1)];
      tmp.subVectors(b, a).normalize();
      view.subVectors(this.camPos, pts[i]).normalize();
      side.crossVectors(tmp, view).normalize().multiplyScalar(width);
      pos.set([pts[i].x + side.x, pts[i].y + side.y, pts[i].z + side.z], i * 6);
      pos.set([pts[i].x - side.x, pts[i].y - side.y, pts[i].z - side.z], i * 6 + 3);
      t[i * 2] = t[i * 2 + 1] = total > 0 ? acc[i] / total : 0;
      s[i * 2] = 1; s[i * 2 + 1] = -1;
      if (i < n - 1) idx.push(i * 2, i * 2 + 1, i * 2 + 2, i * 2 + 1, i * 2 + 3, i * 2 + 2);
    }
    geo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    geo.setAttribute('aT', new THREE.BufferAttribute(t, 1));
    geo.setAttribute('aS', new THREE.BufferAttribute(s, 1));
    geo.setIndex(idx);
    geo.computeBoundingSphere();
  }

  lightning(points: number[], y: number, core: THREE.Color, glow: THREE.Color, life = 0.22, width = 0.14) {
    const mat = this.material(0, core, glow);
    const mesh = new THREE.Mesh(new THREE.BufferGeometry(), mat);
    mesh.frustumCulled = false;
    mesh.renderOrder = 30;
    this.group.add(mesh);
    this.list.push({ mesh, mat, age: 0, life, kind: 'lightning', points, width, y });
    this.rebuildLightning(this.list[this.list.length - 1]);
  }

  private rebuildLightning(f: Fx) {
    const p = f.points!;
    const pts: THREE.Vector3[] = [];
    for (let k = 0; k + 3 < p.length; k += 2) {
      const ax = p[k], az = p[k + 1], bx = p[k + 2], bz = p[k + 3];
      const len = Math.hypot(bx - ax, bz - az);
      const steps = Math.max(3, Math.round(len / 0.55));
      for (let i = 0; i < steps; i++) {
        const t = i / steps;
        const j = i === 0 ? 0 : (Math.random() - 0.5) * 0.7;
        const nx = -(bz - az) / (len || 1), nz = (bx - ax) / (len || 1);
        pts.push(new THREE.Vector3(ax + (bx - ax) * t + nx * j, f.y! + (Math.random() - 0.5) * 0.4 * (i ? 1 : 0), az + (bz - az) * t + nz * j));
      }
    }
    pts.push(new THREE.Vector3(p[p.length - 2], f.y!, p[p.length - 1]));
    f.mesh.geometry.dispose();
    const g = new THREE.BufferGeometry();
    this.ribbon(g, pts, f.width!);
    f.mesh.geometry = g;
  }

  beam(x0: number, z0: number, x1: number, z1: number, y: number, width: number, core: THREE.Color, glow: THREE.Color, life = 0.35) {
    const mat = this.material(1, core, glow);
    const g = new THREE.BufferGeometry();
    const pts: THREE.Vector3[] = [];
    for (let i = 0; i <= 12; i++) pts.push(new THREE.Vector3(x0 + (x1 - x0) * i / 12, y, z0 + (z1 - z0) * i / 12));
    this.ribbon(g, pts, width);
    const mesh = new THREE.Mesh(g, mat);
    mesh.frustumCulled = false;
    mesh.renderOrder = 30;
    this.group.add(mesh);
    this.list.push({ mesh, mat, age: 0, life, kind: 'beam' });
  }

  /** A blade's arc: a curved band sweeping from one side to the other. */
  slash(x: number, y: number, z: number, angle: number, arc: number, reach: number, core: THREE.Color, glow: THREE.Color, life = 0.2) {
    const mat = this.material(2, core, glow);
    const segs = Math.max(8, Math.round(arc * 8));
    const inner = reach * 0.58, outer = reach * 1.02;
    const pos: number[] = [], t: number[] = [], s: number[] = [], idx: number[] = [];
    for (let i = 0; i <= segs; i++) {
      const u = i / segs;
      const a = angle - arc / 2 + arc * u;
      const lift = Math.sin(u * Math.PI) * 0.25;
      pos.push(x + Math.cos(a) * inner, y + lift * 0.4, z + Math.sin(a) * inner);
      pos.push(x + Math.cos(a) * outer, y + lift, z + Math.sin(a) * outer);
      t.push(u, u); s.push(-1, 1);
      if (i < segs) idx.push(i * 2, i * 2 + 1, i * 2 + 2, i * 2 + 1, i * 2 + 3, i * 2 + 2);
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
    g.setAttribute('aT', new THREE.Float32BufferAttribute(t, 1));
    g.setAttribute('aS', new THREE.Float32BufferAttribute(s, 1));
    g.setIndex(idx);
    // Drawn over the crowd: a blade's arc is read through the bodies it cuts.
    mat.depthTest = false;
    const mesh = new THREE.Mesh(g, mat);
    mesh.frustumCulled = false;
    mesh.renderOrder = 40;
    this.group.add(mesh);
    this.list.push({ mesh, mat, age: 0, life, kind: 'slash' });
  }

  /** A bolt straight down from the sky. */
  pillar(x: number, y: number, z: number, height: number, width: number, core: THREE.Color, glow: THREE.Color, life = 0.3) {
    const mat = this.material(3, core, glow);
    const g = new THREE.BufferGeometry();
    const pts: THREE.Vector3[] = [];
    for (let i = 0; i <= 10; i++) pts.push(new THREE.Vector3(x + (Math.random() - 0.5) * 0.2 * (i ? 1 : 0), y + height * (i / 10), z + (Math.random() - 0.5) * 0.2 * (i ? 1 : 0)));
    this.ribbon(g, pts, width);
    const mesh = new THREE.Mesh(g, mat);
    mesh.frustumCulled = false;
    mesh.renderOrder = 30;
    this.group.add(mesh);
    this.list.push({ mesh, mat, age: 0, life, kind: 'pillar' });
  }

  nova(x: number, y: number, z: number, radius: number, core: THREE.Color, glow: THREE.Color, life: number, rings = 1) {
    const mat = new THREE.ShaderMaterial({
      vertexShader: 'varying vec2 vUv; void main(){ vUv = uv; gl_Position = projectionMatrix * modelViewMatrix * vec4(position,1.0); }',
      fragmentShader: novaFrag, transparent: true, depthWrite: false, blending: THREE.AdditiveBlending,
      uniforms: { uCore: { value: core.clone() }, uGlow: { value: glow.clone() }, uFront: { value: 0 }, uAlpha: { value: 1 }, uRings: { value: rings } },
    });
    const g = new THREE.PlaneGeometry(radius * 2, radius * 2);
    g.rotateX(-Math.PI / 2);
    const mesh = new THREE.Mesh(g, mat);
    mesh.position.set(x, y, z);
    mesh.renderOrder = 29;
    this.group.add(mesh);
    this.list.push({ mesh, mat, age: 0, life: life + 0.35, kind: 'nova', expand: life });
  }

  update(dt: number, time: number, camera: THREE.Camera) {
    this.camPos.copy(camera.position);
    for (let i = this.list.length - 1; i >= 0; i--) {
      const f = this.list[i];
      f.age += dt;
      const k = f.age / f.life;
      const u = f.mat.uniforms;
      if (u.uTime) u.uTime.value = time;
      if (f.kind === 'lightning') {
        u.uAlpha.value = (1 - k) * (0.7 + Math.random() * 0.5);
        if (Math.random() < 0.5) this.rebuildLightning(f);
      } else if (f.kind === 'beam') {
        u.uAlpha.value = k < 0.15 ? k / 0.15 : 1 - (k - 0.15) / 0.85;
      } else if (f.kind === 'slash') {
        u.uHead.value = Math.min(1.1, f.age / (f.life * 0.55));
        u.uAlpha.value = 1 - Math.max(0, (k - 0.5) * 2);
      } else if (f.kind === 'pillar') {
        u.uAlpha.value = 1 - k;
      } else if (f.kind === 'nova') {
        const e = Math.min(1, f.age / f.expand!);
        u.uFront.value = 1 - (1 - e) * (1 - e);
        u.uAlpha.value = f.age < f.expand! ? 1 : Math.max(0, 1 - (f.age - f.expand!) / 0.35);
      }
      if (f.age >= f.life) {
        f.mesh.geometry.dispose();
        f.mat.dispose();
        this.group.remove(f.mesh);
        this.list.splice(i, 1);
      }
    }
  }
}
