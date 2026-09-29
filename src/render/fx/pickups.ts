import * as THREE from 'three';
import { Assets } from '../assets';
import type { Battle } from '@/sim/battle';
import type { ParticleSystem } from '../particles';

/* What lies on the ground to be taken.
 *
 * Ember is the stone the dead leave, light still in it: a crystal that spins,
 * bobs and glows hotter the more it holds. Gold is a coin. A potion is a red
 * flask. Gear gets what every ARPG player's eye is trained on - a column of
 * light the colour of its rarity, visible from across the field. */

export const RARITY_COLORS = ['#c8c0b0', '#6fd46a', '#5aa8ff', '#c070ff', '#ffb040', '#ff6a3a'];

const EMBER_TIERS = [
  { color: '#ff9a3a', size: 0.16 },
  { color: '#ffc85a', size: 0.21 },
  { color: '#fff0b0', size: 0.27 },
  { color: '#bfe4ff', size: 0.34 },
];

export class PickupRenderer {
  readonly group = new THREE.Group();
  private ember: THREE.InstancedMesh[] = [];
  private gold: THREE.InstancedMesh;
  private flask: THREE.InstancedMesh;
  private flaskGlow: THREE.InstancedMesh;
  private orb: THREE.InstancedMesh;
  private bag: THREE.InstancedMesh;
  private beams: THREE.InstancedMesh;
  private beamColor: THREE.InstancedBufferAttribute;
  private m = new THREE.Matrix4();
  private q = new THREE.Quaternion();
  private e = new THREE.Euler();
  private p = new THREE.Vector3();
  private s = new THREE.Vector3();
  private sparkleT = 0;

  constructor(private sparks: ParticleSystem) {
    this.group.name = 'pickups';
    const cap = 1400;
    const mk = (geo: THREE.BufferGeometry, mat: THREE.Material, n = cap, shadow = false) => {
      const im = new THREE.InstancedMesh(geo, mat, n);
      im.count = 0;
      im.frustumCulled = false;
      im.castShadow = shadow;
      im.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
      this.group.add(im);
      return im;
    };
    const crystal = new THREE.OctahedronGeometry(1, 0);
    crystal.scale(0.7, 1.25, 0.7);
    for (const t of EMBER_TIERS) {
      this.ember.push(mk(crystal, new THREE.MeshStandardMaterial({
        color: t.color, emissive: new THREE.Color(t.color).multiplyScalar(2.6), roughness: 0.25, metalness: 0.1, flatShading: true,
      })));
    }
    // A coin: a short cylinder of warm gold.
    const coin = new THREE.CylinderGeometry(0.16, 0.16, 0.04, 12);
    coin.rotateX(Math.PI / 2);
    this.gold = mk(coin, new THREE.MeshStandardMaterial({ color: '#ffcc55', emissive: '#6a4a10', metalness: 0.9, roughness: 0.3 }), cap, true);
    const flaskGeo = new THREE.SphereGeometry(0.16, 10, 8);
    flaskGeo.translate(0, 0.16, 0);
    const neck = new THREE.CylinderGeometry(0.05, 0.06, 0.12, 8);
    neck.translate(0, 0.36, 0);
    this.flask = mk(flaskGeo, new THREE.MeshStandardMaterial({ color: '#ff3a4a', emissive: '#aa1020', roughness: 0.15, transparent: true, opacity: 0.9 }), 200, true);
    this.flaskGlow = mk(neck, new THREE.MeshStandardMaterial({ color: '#d8c8b0', roughness: 0.5 }), 200, true);
    this.orb = mk(new THREE.IcosahedronGeometry(0.2, 1), new THREE.MeshBasicMaterial({ color: new THREE.Color('#8ad8ff').multiplyScalar(3) }), 50);
    const bagT = Assets.hasProp('hex_nature', 'sack') ? Assets.propTemplate('hex_nature', 'sack') : null;
    let bagGeo: THREE.BufferGeometry = new THREE.DodecahedronGeometry(0.2, 0);
    let bagMat: THREE.Material = new THREE.MeshStandardMaterial({ color: '#8a6a4a' });
    bagT?.traverse((o) => { const mm = o as THREE.Mesh; if (mm.isMesh) { bagGeo = mm.geometry.clone().scale(2.2, 2.2, 2.2); bagMat = mm.material as THREE.Material; } });
    this.bag = mk(bagGeo, bagMat, 200, true);
    // Loot columns.
    const beamGeo = new THREE.CylinderGeometry(0.28, 0.4, 7, 12, 1, true);
    beamGeo.translate(0, 3.5, 0);
    const beamMat = new THREE.ShaderMaterial({
      name: 'fx:beam',
      transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, side: THREE.DoubleSide,
      uniforms: { uTime: { value: 0 } },
      vertexShader: `attribute vec3 aColor; varying vec3 vC; varying float vY; varying vec3 vN; varying vec3 vV;
        void main(){ vC = aColor; vY = position.y / 7.0; vec4 w = modelMatrix * instanceMatrix * vec4(position,1.0);
        vN = normalize(mat3(modelMatrix * instanceMatrix) * normal); vV = normalize(cameraPosition - w.xyz); gl_Position = projectionMatrix * viewMatrix * w; }`,
      fragmentShader: `uniform float uTime; varying vec3 vC; varying float vY; varying vec3 vN; varying vec3 vV;
        void main(){ float edge = pow(1.0 - abs(dot(vN, vV)), 1.5); float a = (1.0 - vY) * (0.25 + 0.75 * (1.0 - edge)) * (0.7 + 0.3 * sin(uTime * 3.0 + vY * 6.0));
        a *= smoothstep(0.0, 0.05, vY); gl_FragColor = vec4(vC * 2.2, a * 0.55); }`,
    });
    this.beamColor = new THREE.InstancedBufferAttribute(new Float32Array(200 * 3), 3);
    beamGeo.setAttribute('aColor', this.beamColor);
    this.beams = mk(beamGeo, beamMat, 200);
  }

  update(b: Battle, dt: number, time: number, heightAt: (x: number, z: number) => number) {
    const counts = [0, 0, 0, 0];
    let gold = 0, flask = 0, orb = 0, bag = 0, beams = 0;
    this.sparkleT -= dt;
    const sparkle = this.sparkleT <= 0;
    if (sparkle) this.sparkleT = 0.12;
    const col = new THREE.Color();
    b.pickups.forEach((k) => {
      const ground = heightAt(k.x, k.z);
      const bob = Math.sin(time * 3 + k.id) * 0.08;
      const settle = Math.min(1, k.age * 3);
      if (k.kind === 'ember') {
        const tier = EMBER_TIERS[k.tier];
        const im = this.ember[k.tier];
        this.e.set(0.15, time * 2.2 + k.id, 0);
        this.q.setFromEuler(this.e);
        this.p.set(k.x, ground + 0.35 + bob + (1 - settle) * 0.6, k.z);
        this.s.setScalar(tier.size * (k.pulled ? 0.8 : 1));
        this.m.compose(this.p, this.q, this.s);
        im.setMatrixAt(counts[k.tier]++, this.m);
        if (sparkle && Math.random() < 0.08 + k.tier * 0.1) {
          this.sparks.spawn({ x: k.x, y: ground + 0.4, z: k.z, vy: 0.8, life: 0.6, size: 0.06 + k.tier * 0.02, sizeEnd: 0.01, color: new THREE.Color(tier.color), alpha: 0.9, shape: 3 });
        }
      } else if (k.kind === 'gold') {
        this.e.set(0, time * 4 + k.id, 0);
        this.q.setFromEuler(this.e);
        this.p.set(k.x, ground + 0.25 + bob * 0.5, k.z);
        this.s.setScalar(1 + Math.min(1, k.value / 10) * 0.4);
        this.m.compose(this.p, this.q, this.s);
        this.gold.setMatrixAt(gold++, this.m);
      } else if (k.kind === 'heal') {
        this.q.identity();
        this.p.set(k.x, ground + 0.05 + Math.abs(bob), k.z);
        this.s.setScalar(1);
        this.m.compose(this.p, this.q, this.s);
        this.flask.setMatrixAt(flask, this.m);
        this.flaskGlow.setMatrixAt(flask++, this.m);
      } else if (k.kind === 'magnet') {
        this.q.identity();
        this.p.set(k.x, ground + 0.5 + bob, k.z);
        this.s.setScalar(1 + Math.sin(time * 6) * 0.1);
        this.m.compose(this.p, this.q, this.s);
        this.orb.setMatrixAt(orb++, this.m);
      } else {
        // Gear, materials, quest things: a bag on the ground and a column
        // of light over it.
        this.e.set(0, k.id, 0);
        this.q.setFromEuler(this.e);
        this.p.set(k.x, ground, k.z);
        this.s.setScalar(1);
        this.m.compose(this.p, this.q, this.s);
        this.bag.setMatrixAt(bag++, this.m);
        if (k.kind === 'item' || k.kind === 'relic' || k.kind === 'quest' || k.kind === 'chest') {
          col.set(k.kind === 'quest' ? '#ffe070' : RARITY_COLORS[Math.min(5, k.tier)]);
          this.beamColor.setXYZ(beams, col.r, col.g, col.b);
          this.s.set(1, 0.6 + k.tier * 0.18, 1);
          this.m.compose(this.p, this.q, this.s);
          this.beams.setMatrixAt(beams++, this.m);
        }
      }
    });
    this.ember.forEach((im, i) => { im.count = counts[i]; im.instanceMatrix.needsUpdate = true; });
    for (const [im, n] of [[this.gold, gold], [this.flask, flask], [this.flaskGlow, flask], [this.orb, orb], [this.bag, bag], [this.beams, beams]] as const) {
      im.count = n;
      im.instanceMatrix.needsUpdate = true;
    }
    this.beamColor.needsUpdate = true;
    (this.beams.material as THREE.ShaderMaterial).uniforms.uTime.value = time;
  }
}
