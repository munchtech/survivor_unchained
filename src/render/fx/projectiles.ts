import * as THREE from 'three';
import { Assets, type PropPack } from '../assets';
import { SCHOOL, schoolOfArt } from './palette';
import type { ParticleSystem } from '../particles';
import type { Battle } from '@/sim/battle';
import type { Projectile } from '@/sim/entities';
import { bakeVat, VatCrowd } from '../vat';
import { visualSpec } from '../visuals';

/* Everything in the air, drawn from the simulation's projectile pool.
 *
 * Magic is a hot core that blooms and a trail of its own light; steel is the
 * actual object - the arrow, the knife, the axe, the shield - turning the way
 * steel turns in flight; spirit beasts are the same baked wolves the horde
 * uses, glowing. Each style is one instanced draw. */

type Style =
  | { kind: 'orb'; size: number; trail: number; school?: string }
  | { kind: 'prop'; pack: PropPack; prop: string; scale: number; spin: 'none' | 'tumble' | 'flat' | 'orbit'; trail: number; along?: boolean }
  | { kind: 'shard'; size: number; trail: number }
  | { kind: 'chakram'; size: number }
  | { kind: 'crescent'; size: number }
  | { kind: 'herd' };

function styleOf(art: string): Style {
  if (art.startsWith('herd')) return { kind: 'herd' };
  if (art.startsWith('dagger')) return { kind: 'prop', pack: 'adventure_items', prop: 'dagger', scale: 0.9, spin: 'tumble', trail: 0.3 };
  if (art.startsWith('axe')) return { kind: 'prop', pack: 'adventure_items', prop: 'axe_1handed', scale: 1.1, spin: 'orbit', trail: 0.4 };
  if (art.startsWith('arrow')) return { kind: 'prop', pack: 'adventure_items', prop: 'arrow', scale: 1.1, spin: 'none', trail: 0.25, along: true };
  if (art === 'bolt_bone') return { kind: 'prop', pack: 'adventure_items', prop: 'Skeleton_Arrow', scale: 1.1, spin: 'none', trail: 0.2, along: true };
  if (art.startsWith('disc')) return { kind: 'prop', pack: 'adventure_items', prop: 'shield_round_color', scale: 0.8, spin: 'flat', trail: 0.5 };
  if (art === 'firepot') return { kind: 'prop', pack: 'dungeon', prop: 'bottle_A_brown', scale: 0.55, spin: 'tumble', trail: 0.6 };
  if (art.startsWith('chakram')) return { kind: 'chakram', size: 0.55 };
  if (art.startsWith('crescent')) return { kind: 'crescent', size: 1.4 };
  if (art.startsWith('shard') || art === 'spear_ice') return { kind: 'shard', size: art === 'spear_ice' ? 1.6 : 0.55, trail: 0.6 };
  if (art === 'mote' || art === 'mote_cascade' || art === 'mote_star') return { kind: 'orb', size: 0.13, trail: 0.8 };
  if (art === 'cinder' || art === 'star' || art === 'living_flame') return { kind: 'orb', size: art === 'star' ? 0.42 : 0.28, trail: 1.4 };
  if (art === 'ember_seeker') return { kind: 'orb', size: 0.12, trail: 0.9 };
  return { kind: 'orb', size: 0.2, trail: 1 };
}

interface Batch {
  style: Style;
  meshes: Array<{ mesh: THREE.InstancedMesh; local: THREE.Matrix4 }>;
  count: number;
  color?: THREE.Color;
}

export class ProjectileRenderer {
  readonly group = new THREE.Group();
  private batches = new Map<string, Batch>();
  private herd: VatCrowd | null = null;
  private m = new THREE.Matrix4();
  private m2 = new THREE.Matrix4();
  private q = new THREE.Quaternion();
  private e = new THREE.Euler();
  private p = new THREE.Vector3();
  private s = new THREE.Vector3();
  private c = new THREE.Color();
  private trailAcc = new Map<number, number>();

  constructor(private sparks: ParticleSystem, private smoke: ParticleSystem) { this.group.name = 'projectiles'; }

  private batch(art: string, school: string): Batch {
    const key = `${art}`;
    let b = this.batches.get(key);
    if (b) return b;
    const style = styleOf(art);
    const meshes: Batch['meshes'] = [];
    const cap = 400;
    const pal = SCHOOL[schoolOfArt(art)] ?? SCHOOL[school as keyof typeof SCHOOL];
    const add = (geo: THREE.BufferGeometry, mat: THREE.Material, local = new THREE.Matrix4()) => {
      const im = new THREE.InstancedMesh(geo, mat, cap);
      im.count = 0;
      im.frustumCulled = false;
      im.castShadow = false;
      im.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
      this.group.add(im);
      meshes.push({ mesh: im, local });
    };
    if (style.kind === 'orb') {
      add(new THREE.IcosahedronGeometry(1, 1), new THREE.MeshBasicMaterial({ color: pal.core, toneMapped: true }));
      add(new THREE.IcosahedronGeometry(1.9, 1), new THREE.MeshBasicMaterial({ color: pal.glow.clone().multiplyScalar(0.55), transparent: true, opacity: 0.35, blending: THREE.AdditiveBlending, depthWrite: false }));
    } else if (style.kind === 'shard') {
      const g = new THREE.OctahedronGeometry(1, 0);
      g.scale(0.35, 0.35, 1.4);
      add(g, new THREE.MeshStandardMaterial({ color: '#d8f2ff', emissive: pal.glow.clone().multiplyScalar(0.8), roughness: 0.1, metalness: 0.1, transparent: true, opacity: 0.92 }));
    } else if (style.kind === 'chakram') {
      const g = new THREE.TorusGeometry(1, 0.12, 5, 16);
      g.rotateX(Math.PI / 2);
      add(g, new THREE.MeshStandardMaterial({ color: '#d8dce8', metalness: 0.8, roughness: 0.25, emissive: pal.glow.clone().multiplyScalar(0.25) }));
      for (let k = 0; k < 4; k++) {
        const blade = new THREE.ConeGeometry(0.16, 0.5, 3);
        blade.rotateZ(-Math.PI / 2);
        blade.translate(1.1, 0, 0);
        blade.rotateY((k / 4) * Math.PI * 2);
        add(blade, new THREE.MeshStandardMaterial({ color: '#eef0f8', metalness: 0.9, roughness: 0.2 }));
      }
    } else if (style.kind === 'crescent') {
      const g = new THREE.RingGeometry(0.6, 1, 16, 1, -Math.PI / 2.2, Math.PI / 1.1);
      g.rotateX(-Math.PI / 2);
      add(g, new THREE.MeshBasicMaterial({ color: pal.core, transparent: true, opacity: 0.85, blending: THREE.AdditiveBlending, side: THREE.DoubleSide, depthWrite: false }));
    } else if (style.kind === 'prop') {
      const t = Assets.propTemplate(style.pack, style.prop);
      t.updateMatrixWorld(true);
      const inv = t.matrixWorld.clone().invert();
      t.traverse((o) => {
        const mm = o as THREE.Mesh;
        if (!mm.isMesh) return;
        add(mm.geometry, mm.material as THREE.Material, inv.clone().multiply(mm.matrixWorld));
      });
    }
    b = { style, meshes, count: 0, color: pal.glow };
    this.batches.set(key, b);
    return b;
  }

  update(bt: Battle, dt: number, time: number, heightAt: (x: number, z: number) => number) {
    for (const b of this.batches.values()) b.count = 0;
    if (this.herd) this.herd.begin();
    const items = bt.projectiles.items;
    for (let i = 0; i < items.length; i++) {
      const pr = items[i];
      if (!pr.alive) { this.trailAcc.delete(pr.id); continue; }
      this.drawOne(pr, dt, time, heightAt);
    }
    for (const b of this.batches.values()) {
      for (const part of b.meshes) {
        part.mesh.count = b.count;
        part.mesh.instanceMatrix.needsUpdate = true;
      }
    }
    if (this.herd) this.herd.end(time);
  }

  private drawOne(pr: Projectile, dt: number, time: number, heightAt: (x: number, z: number) => number) {
    const style = styleOf(pr.art);
    const ground = heightAt(pr.x, pr.z);
    const y = ground + (pr.lob ? pr.y : pr.orbitR > 0 ? 1.0 : pr.y);
    const heading = Math.atan2(pr.dirX, pr.dirZ);
    if (style.kind === 'herd') {
      if (!this.herd) {
        const asset = bakeVat(visualSpec('wolf_spirit'));
        this.herd = new VatCrowd(asset, 120);
        this.herd.mesh.castShadow = false;
        this.group.add(this.herd.mesh);
        this.herd.begin();
      }
      this.p.set(pr.x, ground, pr.z);
      this.q.setFromAxisAngle(new THREE.Vector3(0, 1, 0), heading);
      this.s.setScalar(1.05);
      this.m.compose(this.p, this.q, this.s);
      const k = pr.age / pr.life;
      this.herd.push(this.m, 'move', time * 1.6 + pr.id * 0.3, 0, k > 0.85 ? (k - 0.85) / 0.15 : 0, 0, 0, this.c.setRGB(0.9, 1.1, 1.3), 1.4);
      this.trail(pr, dt, 0.5, 'nature', ground + 0.6);
      return;
    }
    const b = this.batch(pr.art, pr.school);
    const i = b.count++;
    this.p.set(pr.x, y, pr.z);
    let sc = 1;
    switch (style.kind) {
      case 'orb': {
        sc = style.size * (1 + 0.12 * Math.sin(time * 30 + pr.id)) * (1 + (pr.rank - 1) * 0.05);
        this.q.identity();
        break;
      }
      case 'shard':
        sc = style.size;
        this.e.set(0, heading, 0);
        this.q.setFromEuler(this.e);
        break;
      case 'chakram':
        sc = style.size;
        this.q.setFromAxisAngle(new THREE.Vector3(0, 1, 0), time * 18 + pr.id);
        break;
      case 'crescent':
        sc = style.size;
        this.q.setFromAxisAngle(new THREE.Vector3(0, 1, 0), heading);
        break;
      case 'prop': {
        sc = style.scale;
        if (style.spin === 'tumble') this.e.set(time * 14 + pr.id, heading, 0, 'YXZ');
        else if (style.spin === 'flat') this.e.set(0, time * 16 + pr.id, 0);
        else if (style.spin === 'orbit') this.e.set(Math.PI / 2, 0, -pr.orbitA * 1 - time * 8, 'XYZ');
        else this.e.set(style.along ? Math.PI / 2 : 0, heading, 0, 'YXZ');
        this.q.setFromEuler(this.e);
        break;
      }
    }
    this.s.setScalar(sc);
    this.m.compose(this.p, this.q, this.s);
    for (const part of b.meshes) {
      this.m2.multiplyMatrices(this.m, part.local);
      part.mesh.setMatrixAt(i, this.m2);
    }
    const trail = 'trail' in style ? style.trail : 0.4;
    if (trail > 0) this.trail(pr, dt, trail, pr.school, y);
  }

  /** Light left in the air behind anything that flies. */
  private trail(pr: Projectile, dt: number, amount: number, school: string, y: number) {
    const acc = (this.trailAcc.get(pr.id) ?? 0) + dt * 60 * amount;
    const n = Math.floor(acc);
    this.trailAcc.set(pr.id, acc - n);
    if (!n) return;
    const pal = SCHOOL[school as keyof typeof SCHOOL] ?? SCHOOL.physical;
    for (let k = 0; k < n; k++) {
      this.sparks.spawn({
        x: pr.x + (Math.random() - 0.5) * 0.1, y: y + (Math.random() - 0.5) * 0.1, z: pr.z + (Math.random() - 0.5) * 0.1,
        vx: -pr.vx * 0.05 + (Math.random() - 0.5) * 0.4, vy: (Math.random() - 0.3) * 0.5, vz: -pr.vz * 0.05 + (Math.random() - 0.5) * 0.4,
        life: 0.25 + Math.random() * 0.25, size: 0.12 * (0.6 + amount * 0.5), sizeEnd: 0.02, color: pal.core, colorEnd: pal.glow, alpha: 0.8, drag: 2,
      });
      if (school === 'fire' && Math.random() < 0.35) {
        this.smoke.spawn({ x: pr.x, y, z: pr.z, vy: 0.6, life: 0.7, size: 0.18, sizeEnd: 0.5, color: 0x2a2220, colorEnd: 0x151210, alpha: 0.35, shape: 4, drag: 1 });
      }
    }
  }

}
