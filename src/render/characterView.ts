import * as THREE from 'three';
import { Assets, type CharacterModel, type PropPack } from './assets';
import { damp, dampAngle } from '@/core/math';

/* One animated humanoid: the survivor, an NPC, a boss.
 *
 * Wraps a cloned KayKit rig with an AnimationMixer bound to the shared clip
 * library, and gives it the verbs the game needs:
 *
 *   - locomotion(speed) blends idle / walk / run and syncs the stride to the
 *     actual ground speed so feet do not skate;
 *   - act(clip) plays a one-shot (attack, cast, hit, interact) layered over
 *     locomotion, then hands back;
 *   - loadout: every KayKit model ships with all of its weapon and hat
 *     variants attached; the loadout shows only what the character actually
 *     carries, and anything from the item packs can be socketed to a hand,
 *     the head or the back;
 *   - tint: cloth colours are recoloured per character (appearance and
 *     faction colours) without touching the shared texture.
 *
 * Crowds do not use this - see crowd.ts. It is for the handful of characters
 * that deserve a full skeleton. */

export const CHARACTER_SCALE = 0.8;
const _flash = new THREE.Color();

export type Socket = 'handslot.r' | 'handslot.l' | 'head' | 'chest';

interface PlayOpts { fade?: number; speed?: number; loop?: boolean; clamp?: boolean }

export class CharacterView {
  readonly root = new THREE.Group();
  readonly model: THREE.Group;
  readonly mixer: THREE.AnimationMixer;
  private actions = new Map<string, THREE.AnimationAction>();
  private bones = new Map<string, THREE.Object3D>();
  private optional = new Map<string, THREE.Object3D>();
  private sockets = new Map<string, THREE.Object3D[]>();
  private base: THREE.AnimationAction | null = null;
  private baseName = '';
  private oneShot: THREE.AnimationAction | null = null;
  private oneShotEnds = 0;
  heading = 0;
  private headingTarget = 0;
  idleClip = 'Idle';
  walkClip = 'Walking_A';
  runClip = 'Running_A';
  /** Metres per second at which the run clip's stride matches the ground. */
  runStride = 5.2;
  walkStride = 2.2;
  private flash = 0;
  private materials: THREE.MeshStandardMaterial[] = [];
  private baseEmissive: THREE.Color[] = [];

  constructor(readonly id: CharacterModel, opts: { scale?: number } = {}) {
    this.model = Assets.character(id);
    this.model.scale.setScalar(opts.scale ?? CHARACTER_SCALE);
    this.root.add(this.model);
    this.mixer = new THREE.AnimationMixer(this.model);
    this.model.traverse((o) => {
      if ((o as THREE.Bone).isBone) this.bones.set(o.name, o);
      const m = o as THREE.Mesh;
      if (m.isMesh) {
        if (!(m as THREE.SkinnedMesh).isSkinnedMesh) this.optional.set(o.name, o);
        const mat = m.material as THREE.MeshStandardMaterial;
        this.materials.push(mat);
        this.baseEmissive.push(mat.emissive.clone());
      }
    });
    this.mixer.addEventListener('finished', (e) => {
      if (e.action === this.oneShot) this.endOneShot();
    });
    this.setBase(this.idleClip, 0);
  }

  /** Show only these of the model's own optional parts (weapons, hats). */
  showOnly(names: string[]) {
    for (const [n, o] of this.optional) o.visible = names.includes(n);
  }

  /** Attach a prop from an item pack to a socket, replacing what was there. */
  socket(socket: Socket, pack: PropPack | null, prop: string | null, opts: { scale?: number; rot?: [number, number, number]; offset?: [number, number, number] } = {}) {
    for (const o of this.sockets.get(socket) ?? []) o.removeFromParent();
    this.sockets.set(socket, []);
    if (!pack || !prop) return null;
    const bone = this.bones.get(socket);
    if (!bone) return null;
    const o = Assets.prop(pack, prop);
    o.scale.setScalar(opts.scale ?? 1);
    if (opts.rot) o.rotation.set(...opts.rot);
    if (opts.offset) o.position.set(...opts.offset);
    o.traverse((c) => { if ((c as THREE.Mesh).isMesh) { c.castShadow = true; } });
    bone.add(o);
    this.sockets.get(socket)!.push(o);
    return o;
  }

  bone(name: string) { return this.bones.get(name); }

  private action(name: string) {
    let a = this.actions.get(name);
    if (!a) {
      a = this.mixer.clipAction(Assets.clip(name));
      this.actions.set(name, a);
    }
    return a;
  }

  private setBase(name: string, fade: number, speed = 1) {
    if (this.baseName === name) {
      if (this.base) this.base.timeScale = speed;
      return;
    }
    const next = this.action(name);
    next.enabled = true;
    next.setLoop(THREE.LoopRepeat, Infinity);
    next.timeScale = speed;
    next.setEffectiveWeight(1);
    next.reset().play();
    if (this.base && fade > 0) this.base.crossFadeTo(next, fade, false);
    else if (this.base) this.base.stop();
    this.base = next;
    this.baseName = name;
  }

  /** Drive idle / walk / run from ground speed in m/s. */
  locomotion(speed: number) {
    if (this.oneShot && this.oneShotBlocksLegs) return;
    if (speed < 0.35) this.setBase(this.idleClip, 0.25);
    else if (speed < 3.2) this.setBase(this.walkClip, 0.2, Math.max(0.6, speed / this.walkStride));
    else this.setBase(this.runClip, 0.18, Math.max(0.75, speed / this.runStride));
  }

  /** Play a looping pose (sitting, lying, channeling). */
  loop(name: string, fade = 0.3, speed = 1) {
    this.endOneShot();
    this.setBase(name, fade, speed);
  }

  private oneShotBlocksLegs = false;

  /** A one-shot over the top. Returns its duration in seconds. */
  act(name: string, opts: PlayOpts & { blocksLegs?: boolean } = {}) {
    const a = this.action(name);
    if (this.oneShot && this.oneShot !== a) this.oneShot.fadeOut(0.08);
    a.reset();
    a.setLoop(THREE.LoopOnce, 1);
    a.clampWhenFinished = opts.clamp ?? false;
    a.timeScale = opts.speed ?? 1;
    a.setEffectiveWeight(1);
    a.fadeIn(opts.fade ?? 0.08).play();
    this.oneShot = a;
    this.oneShotBlocksLegs = !!opts.blocksLegs;
    const dur = a.getClip().duration / a.timeScale;
    this.oneShotEnds = dur;
    return dur;
  }

  private endOneShot() {
    if (!this.oneShot) return;
    if (!this.oneShot.clampWhenFinished) this.oneShot.fadeOut(0.15);
    this.oneShot = null;
    this.oneShotBlocksLegs = false;
  }

  get busy() { return !!this.oneShot; }

  /** Face a direction (radians, 0 = +z). */
  face(angle: number, instant = false) {
    this.headingTarget = angle;
    if (instant) this.heading = angle;
  }

  hitFlash(v = 1) { this.flash = Math.max(this.flash, v); }

  /** Recolour: multiply the albedo of every part (faction colours, frost). */
  tint(color: THREE.ColorRepresentation) {
    const c = new THREE.Color(color);
    for (const m of this.materials) m.color.copy(c);
  }

  update(dt: number) {
    this.heading = dampAngle(this.heading, this.headingTarget, 14, dt);
    this.model.rotation.y = this.heading;
    this.mixer.update(dt);
    if (this.oneShot) {
      this.oneShotEnds -= dt;
      if (this.oneShotEnds <= 0 && !this.oneShot.clampWhenFinished) this.endOneShot();
    }
    if (this.flash > 0.001) {
      this.flash = damp(this.flash, 0, 14, dt);
      this.materials.forEach((m, i) => m.emissive.copy(this.baseEmissive[i]).add(_flash.setRGB(this.flash * 1.6, this.flash * 1.3, this.flash * 1.2)));
    } else if (this.flash !== 0) {
      this.flash = 0;
      this.materials.forEach((m, i) => m.emissive.copy(this.baseEmissive[i]));
    }
  }

  dispose() {
    this.mixer.stopAllAction();
    this.root.removeFromParent();
  }
}
