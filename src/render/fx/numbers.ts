import * as THREE from 'three';

/* Damage numbers, the way the genre speaks them: they pop, rise and fade;
 * critical strikes are bigger and gold; what the survivor takes is red and
 * sits apart; damage over time is small and quiet so it does not bury the
 * big hits. Hundreds on screen at once, so they are instanced glyph quads
 * drawn from one canvas atlas, not DOM. Numbers near the same spot in the
 * same instant fan out instead of stacking into an unreadable blob. */

const GLYPHS = '0123456789.k+-!';
const CELL_W = 64, CELL_H = 96;

function atlas() {
  const c = document.createElement('canvas');
  c.width = CELL_W * GLYPHS.length;
  c.height = CELL_H;
  const g = c.getContext('2d')!;
  g.font = `800 ${CELL_H * 0.82}px 'Alegreya Sans', 'Segoe UI', sans-serif`;
  g.textAlign = 'center';
  g.textBaseline = 'middle';
  g.lineJoin = 'round';
  for (let i = 0; i < GLYPHS.length; i++) {
    const x = i * CELL_W + CELL_W / 2, y = CELL_H / 2 + 4;
    g.lineWidth = 14;
    g.strokeStyle = 'rgba(0,0,0,0.85)';
    g.strokeText(GLYPHS[i], x, y);
    g.fillStyle = '#ffffff';
    g.fillText(GLYPHS[i], x, y);
  }
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  t.minFilter = THREE.LinearMipmapLinearFilter;
  t.generateMipmaps = true;
  return t;
}

const vertex = /* glsl */ `
uniform float uTime;
uniform float uScale;
uniform vec2 uViewport;
attribute vec4 aPos;   // world x y z, birth
attribute vec4 aGlyph; // glyph index, x offset (glyph units), size, kind
attribute vec4 aColor; // rgb, fan offset (radians)
varying vec2 vUv;
varying vec4 vColor;
varying float vFade;
void main() {
  float age = uTime - aPos.w;
  float life = aGlyph.w > 1.5 ? 1.05 : 0.8;
  if (age < 0.0 || age > life) { gl_Position = vec4(2.0); return; }
  float k = age / life;
  // Pop: overshoot then settle; then drift up and out.
  float pop = 1.0 + 0.6 * exp(-age * 18.0) * sin(age * 30.0 + 1.5);
  vec3 p = aPos.xyz + vec3(0.0, 1.8 + age * 1.2 - age * age * 0.5, 0.0);
  vec4 clip = projectionMatrix * viewMatrix * vec4(p, 1.0);
  float size = aGlyph.z * uScale * pop;
  vec2 fan = vec2(cos(aColor.a), sin(aColor.a)) * min(age * 4.0, 1.0) * 0.045;
  vec2 offs = vec2(aGlyph.y * 0.46 + position.x * 0.667, position.y) * size;
  clip.xy += (offs / uViewport * 2.0 + fan) * clip.w;
  gl_Position = clip;
  vUv = vec2((aGlyph.x + position.x + 0.5) / ${GLYPHS.length.toFixed(1)}, position.y + 0.5);
  vColor = vec4(aColor.rgb, 1.0);
  vFade = 1.0 - smoothstep(0.65, 1.0, k);
}
`;

const fragment = /* glsl */ `
uniform sampler2D uAtlas;
varying vec2 vUv;
varying vec4 vColor;
varying float vFade;
void main() {
  vec4 t = texture2D(uAtlas, vUv);
  // White glyph over black outline: colour the white, keep the outline dark.
  vec3 c = mix(vec3(0.0), vColor.rgb, t.r);
  float a = t.a * vFade;
  if (a < 0.01) discard;
  gl_FragColor = vec4(c, a);
}
`;

export type NumberKind = 'hit' | 'crit' | 'dot' | 'player' | 'heal' | 'blocked';

export class DamageNumbers {
  readonly mesh: THREE.Mesh;
  private aPos: THREE.InstancedBufferAttribute;
  private aGlyph: THREE.InstancedBufferAttribute;
  private aColor: THREE.InstancedBufferAttribute;
  private head = 0;
  private mat: THREE.ShaderMaterial;
  private recent: Array<{ x: number; z: number; t: number; n: number }> = [];
  enabled = true;

  constructor(readonly capacity = 1600) {
    const quad = new THREE.PlaneGeometry(1, 1);
    const geo = new THREE.InstancedBufferGeometry();
    geo.index = quad.index;
    geo.setAttribute('position', quad.getAttribute('position'));
    this.aPos = new THREE.InstancedBufferAttribute(new Float32Array(capacity * 4).fill(-999), 4);
    this.aGlyph = new THREE.InstancedBufferAttribute(new Float32Array(capacity * 4), 4);
    this.aColor = new THREE.InstancedBufferAttribute(new Float32Array(capacity * 4), 4);
    for (const a of [this.aPos, this.aGlyph, this.aColor]) a.setUsage(THREE.DynamicDrawUsage);
    geo.setAttribute('aPos', this.aPos);
    geo.setAttribute('aGlyph', this.aGlyph);
    geo.setAttribute('aColor', this.aColor);
    geo.instanceCount = capacity;
    this.mat = new THREE.ShaderMaterial({
      vertexShader: vertex, fragmentShader: fragment, transparent: true, depthWrite: false, depthTest: false,
      uniforms: { uTime: { value: 0 }, uScale: { value: 1 }, uViewport: { value: new THREE.Vector2(1600, 900) }, uAtlas: { value: atlas() } },
    });
    this.mesh = new THREE.Mesh(geo, this.mat);
    this.mesh.frustumCulled = false;
    this.mesh.renderOrder = 100;
  }

  /** Text for a number: integers, and thousands as "1.2k". */
  static format(v: number) {
    if (v >= 10000) return `${Math.round(v / 1000)}k`;
    if (v >= 1000) return `${(v / 1000).toFixed(1)}k`;
    if (v < 1 && v > 0) return v.toFixed(1);
    return String(Math.round(v));
  }

  spawn(x: number, y: number, z: number, value: number, kind: NumberKind, time: number) {
    if (!this.enabled) return;
    let text = DamageNumbers.format(value);
    if (kind === 'heal') text = `+${text}`;
    if (kind === 'crit') text = `${text}!`;
    const size = kind === 'crit' ? 36 : kind === 'dot' ? 17 : kind === 'player' ? 30 : kind === 'heal' ? 24 : 24;
    const col = { hit: [1, 0.97, 0.9], crit: [1, 0.82, 0.25], dot: [0.78, 0.74, 0.7], player: [1, 0.32, 0.28], heal: [0.45, 1, 0.55], blocked: [0.6, 0.66, 0.75] }[kind];
    // Fan numbers born at the same spot at nearly the same time.
    this.recent = this.recent.filter((r) => time - r.t < 0.25);
    let fan = 0;
    const near = this.recent.find((r) => Math.abs(r.x - x) < 0.8 && Math.abs(r.z - z) < 0.8);
    if (near) { near.n++; fan = (near.n % 2 ? 1 : -1) * (0.6 + near.n * 0.35) + Math.PI / 2; }
    else { this.recent.push({ x, z, t: time, n: 0 }); fan = Math.PI / 2 + (Math.random() - 0.5) * 0.6; }
    const n = text.length;
    for (let i = 0; i < n; i++) {
      const g = GLYPHS.indexOf(text[i]);
      if (g < 0) continue;
      const k = this.head;
      this.head = (this.head + 1) % this.capacity;
      this.aPos.setXYZW(k, x, y, z, time);
      this.aGlyph.setXYZW(k, g, i - (n - 1) / 2, size, kind === 'crit' ? 2 : 1);
      this.aColor.setXYZW(k, col[0], col[1], col[2], near ? fan : fan);
    }
    this.aPos.needsUpdate = true;
    this.aGlyph.needsUpdate = true;
    this.aColor.needsUpdate = true;
  }

  update(time: number, width: number, height: number, scale = 1) {
    this.mat.uniforms.uTime.value = time;
    (this.mat.uniforms.uViewport.value as THREE.Vector2).set(width, height);
    this.mat.uniforms.uScale.value = scale;
  }
}
