import * as THREE from 'three';
import { CharacterView, CHARACTER_SCALE } from './characterView';
import type { Enemy } from '@/sim/entities';

/* Bosses get a full skeleton, their own light and hand-picked motion, not a
 * crowd slot. The zone script says what the boss is doing (its pose); this
 * turns that into a clip and keeps the body where the simulation has it. */

export type WardenPose = 'sleep' | 'wake' | 'walk' | 'idle' | 'windup' | 'cleave' | 'charge-windup' | 'charge' | 'stunned' | 'channel' | 'dead';

export class WardenView {
  readonly view: CharacterView;
  readonly light: THREE.PointLight;
  private pose: WardenPose | '' = '';
  private eyes: THREE.MeshStandardMaterial[] = [];
  private lamp: THREE.Object3D | null = null;
  private lampAt = new THREE.Vector3();
  glow = 1;

  constructor(parent: THREE.Object3D, readonly scale = 2.6) {
    const v = new CharacterView('skeleton_warrior', { scale: CHARACTER_SCALE * scale });
    this.view = v;
    // Old Watch plate gone to rust: tint the whole frame a cold, wet grey.
    v.tint('#b8c0c4');
    v.socket('handslot.r', 'adventure_items', 'sword_2handed', { scale: 1.05 });
    this.lamp = v.socket('handslot.l', 'halloween', 'lantern_hanging', { scale: 0.55, offset: [0, -0.1, 0] });
    v.model.traverse((o) => {
      const m = o as THREE.Mesh;
      if (m.isMesh && /Eyes/.test(o.name)) {
        const mat = (m.material as THREE.MeshStandardMaterial);
        mat.emissive = new THREE.Color('#7ac8ff');
        mat.emissiveIntensity = 6;
        this.eyes.push(mat);
      }
    });
    parent.add(v.root);
    this.light = new THREE.PointLight(0x8ac8ff, 0, 16, 1.3);
    parent.add(this.light);
  }

  setPose(p: WardenPose) {
    if (p === this.pose) return;
    const v = this.view;
    this.pose = p;
    switch (p) {
      case 'sleep': v.loop('Skeletons_Inactive_Floor_Pose', 0); break;
      case 'wake': v.act('Skeletons_Awaken_Floor_Long', { clamp: true, blocksLegs: true, speed: 0.8 }); break;
      case 'walk': v.walkClip = 'Walking_D_Skeletons'; v.runClip = 'Walking_D_Skeletons'; v.idleClip = '2H_Melee_Idle'; break;
      case 'idle': v.idleClip = '2H_Melee_Idle'; break;
      case 'windup': v.loop('2H_Melee_Idle', 0.1, 0.5); break;
      case 'cleave': v.act('2H_Melee_Attack_Slice', { speed: 1.1, blocksLegs: true }); break;
      case 'charge-windup': v.loop('Block', 0.15); break;
      case 'charge': v.loop('Running_A', 0.1, 1.6); break;
      case 'stunned': v.act('Hit_B', { speed: 0.7, blocksLegs: true, clamp: true }); break;
      case 'channel': v.loop('Spellcasting', 0.3); break;
      case 'dead': v.act('Death_C_Skeletons', { clamp: true, blocksLegs: true, speed: 0.7 }); break;
    }
  }

  /** Back to walking after a held pose. */
  release() {
    this.pose = 'walk';
    this.view.loop('2H_Melee_Idle', 0.2);
  }

  update(e: Enemy | null, x: number, y: number, z: number, facing: number, dt: number, time: number) {
    const v = this.view;
    v.root.position.set(x, y, z);
    v.face(facing);
    if (e && (this.pose === 'walk' || this.pose === 'idle')) v.locomotion(Math.hypot(e.vx, e.vz) * 1.2);
    if (e && e.flash > 0.05) v.hitFlash(e.flash * 0.25);
    v.update(dt);
    const g = this.glow * (this.pose === 'sleep' ? 0.35 : 1) * (this.pose === 'dead' ? 0 : 1);
    for (const m of this.eyes) m.emissiveIntensity = 2 + g * 5 + Math.sin(time * 5) * g;
    // The light is the lamp in its fist, hung a little out from the body:
    // at the skull it burned the head white.
    this.light.intensity = g * (5 + Math.sin(time * 3.1) * 0.8 + (this.pose === 'channel' ? 4 + Math.sin(time * 14) * 2 : 0));
    if (this.lamp) {
      this.lamp.getWorldPosition(this.lampAt);
      this.light.position.set(this.lampAt.x, Math.max(this.lampAt.y, y + 1.2) + 0.8, this.lampAt.z);
    } else this.light.position.set(x, y + this.scale * 2.2, z);
    if (this.lamp) this.lamp.visible = this.pose !== 'dead' || g > 0.01;
  }

  dispose() {
    this.view.dispose();
    this.light.removeFromParent();
  }
}
