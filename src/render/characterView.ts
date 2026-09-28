import * as THREE from 'three';
import { Assets, type CharacterModel, type PropPack } from './assets';
import { applyProportions, legLift } from './proportions';
import { assembleSync, clipSync, type PersonSpec } from './people';
import { ARMS, arm } from './arms';
import { paintedAtlas, type Paint } from './recolor';
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
/** Quaternius people are authored in metres; a touch over life size so they
 *  stand right beside doors and walls built for the old figures. */
export const HUMAN_SCALE = 1.04;

/** The game names clips in KayKit's words; a person plays the library clip
 *  that does the same thing (Universal Animation Libraries 1 and 2). */
const HUMAN_CLIPS: Record<string, string> = {
  Idle: 'Idle_Loop', Idle_B: 'Idle_Loop', Idle_Combat: 'Sword_Idle', '2H_Melee_Idle': 'Sword_Idle', Unarmed_Idle: 'Idle_Loop',
  Walking_A: 'Walk_Loop', Walking_B: 'Walk_Loop', Walking_C: 'Walk_Formal_Loop', Walking_D_Skeletons: 'Zombie_Walk_Fwd_Loop',
  Running_A: 'Jog_Fwd_Loop', Running_B: 'Sprint_Loop',
  '1H_Melee_Attack_Chop': 'Sword_Regular_A', '1H_Melee_Attack_Slice_Diagonal': 'Sword_Regular_B', '1H_Melee_Attack_Slice_Horizontal': 'Sword_Regular_C',
  '1H_Melee_Attack_Stab': 'Sword_Regular_A', '2H_Melee_Attack_Chop': 'Sword_Attack', '2H_Melee_Attack_Slice': 'Sword_Attack',
  '2H_Melee_Attack_Spin': 'Sword_Heavy_Combo', Dualwield_Melee_Attack_Slice: 'Sword_Regular_Combo', Unarmed_Melee_Attack_Punch_A: 'Punch_Jab',
  Spellcast_Shoot: 'Spell_Simple_Shoot', Spellcast_Raise: 'Spell_Simple_Enter', Spellcast_Summon: 'Spell_Simple_Enter', Spellcasting: 'Spell_Simple_Idle_Loop',
  Throw: 'OverhandThrow', '1H_Ranged_Shoot': 'Pistol_Shoot', '2H_Ranged_Shoot': 'Pistol_Shoot',
  Sit_Floor_Idle: 'Crouch_Idle_Loop', Sit_Chair_Idle: 'Sitting_Idle_Loop', Interact: 'Interact', PickUp: 'PickUp_Table', Use_Item: 'Consume',
  Death_A: 'Death01', Death_B: 'Death01', Death_A_Pose: 'Death01', Death_C_Skeletons: 'Death01',
  Hit_A: 'Hit_Chest', Hit_B: 'Hit_Head', Cheer: 'Yes', Taunt: 'Punch_Cross', Block: 'Sword_Block', Blocking: 'Idle_Shield_Loop',
  Lie_StandUp: 'LayToIdle', Dodge_Forward: 'Roll', Jump_Full_Short: 'NinjaJump_Start', Wave: 'Yes',
};

/** Sockets on a person's rig (hand bones point differently from KayKit's
 *  hand slots; a fixed turn puts a prop the way the old slot held it). */
export const basis = (x: [number, number, number], y: [number, number, number]) => {
  const vx = new THREE.Vector3(...x), vy = new THREE.Vector3(...y);
  return new THREE.Quaternion().setFromRotationMatrix(new THREE.Matrix4().makeBasis(vx, vy, new THREE.Vector3().crossVectors(vx, vy)));
};
export const HUMAN_SOCKETS: Record<string, { bone: string; turn: THREE.Quaternion; pos: [number, number, number] }> = {
  // In the hand's own space the fingers run +Y and the thumb side is +Z: a
  // prop's shaft (its +Y) leaves the fist on the thumb side, its blade's
  // width (its +X) in line with the knuckles.
  'handslot.r': { bone: 'hand_r', turn: basis([0, 1, 0], [0, 0, 1]), pos: [-0.025, 0.075, 0] },
  'handslot.l': { bone: 'hand_l', turn: basis([0, 1, 0], [0, 0, 1]), pos: [-0.025, 0.075, 0] },
  // A shield on the left forearm, its face (+Z) out from the back of it.
  'forearm.l': { bone: 'lowerarm_l', turn: basis([0, 1, 0], [0, 0, -1]), pos: [0, 0.14, 0] },
  head: { bone: 'Head', turn: new THREE.Quaternion(), pos: [0, 0.12, 0] },
  chest: { bone: 'spine_03', turn: new THREE.Quaternion(), pos: [0, 0, 0] },
};
const PISTOL = new THREE.Quaternion().setFromRotationMatrix(new THREE.Matrix4().makeBasis(new THREE.Vector3(0, 0, 1), new THREE.Vector3(1, 0, 0), new THREE.Vector3(0, 1, 0)));
const _flash = new THREE.Color();

/** A weapon as a hand holds it, in a socket's frame (render/arms.ts sizes).
 *  The socket's frame is the fist's (its X along the fingers, Y out of the
 *  thumb side): a crossbow held pistol-fashion has its stock along X, its
 *  top along Y, sitting on the fist rather than through it. */
export function heldArm(id: string): THREE.Object3D | null {
  const o = arm(id);
  if (!o) return null;
  if (ARMS[id].hold === 'pistol') {
    o.quaternion.copy(PISTOL);
    o.position.set(0, 0.05, 0);
  }
  return o;
}

export type Socket = 'handslot.r' | 'handslot.l' | 'forearm.l' | 'head' | 'chest';

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

  /** A Quaternius person rather than a KayKit toy. */
  readonly human: boolean;
  private headScale = 1;

  constructor(readonly id: CharacterModel | PersonSpec, opts: { scale?: number } = {}) {
    this.human = typeof id !== 'string';
    if (typeof id === 'string') {
      this.model = Assets.character(id);
      this.model.scale.setScalar(opts.scale ?? CHARACTER_SCALE);
    } else {
      this.model = assembleSync(id).root;
      this.headScale = id.head ?? 1;
      this.model.scale.setScalar((opts.scale ?? CHARACTER_SCALE) / CHARACTER_SCALE * HUMAN_SCALE);
      this.idleClip = 'Idle'; this.walkClip = 'Walking_A'; this.runClip = 'Running_A';
      this.walkStride = 1.55; this.runStride = 3.9;
    }
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
    // Longer legs: stand the figure on them (see proportions.ts).
    if (!this.human) this.model.position.y = legLift(this.model, this.bones) * this.model.scale.y;
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
    const bone = this.mount(socket);
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

  /** Put one of the real weapons (arms.ts) in a socket, replacing what was
   *  there; null empties it. */
  wield(socket: Socket, id: string | null) {
    for (const o of this.sockets.get(socket) ?? []) o.removeFromParent();
    this.sockets.set(socket, []);
    const bone = this.mount(socket);
    const o = id ? heldArm(id) : null;
    if (!bone || !o) return null;
    // Weapons are in metres: sized with the person (the mount has undone it).
    o.scale.setScalar((this.human ? HUMAN_SCALE : 1) / CHARACTER_SCALE);
    bone.add(o);
    this.sockets.get(socket)!.push(o);
    return o;
  }

  /** Where a socket's props hang: KayKit's own slot bone, or on a person a
   *  fixed mount under the matching bone, turned to hold a prop the way
   *  KayKit's slot did. */
  private mount(socket: Socket) {
    if (!this.human) return this.bones.get(socket) ?? null;
    const hs = HUMAN_SOCKETS[socket];
    const b = hs && this.bones.get(hs.bone);
    if (!b) return null;
    let mount = b.getObjectByName(`mount:${socket}`);
    if (!mount) {
      mount = new THREE.Group();
      mount.name = `mount:${socket}`;
      mount.quaternion.copy(hs.turn);
      mount.position.set(...hs.pos);
      // Undo the person's scale so props keep their size.
      mount.scale.setScalar(1 / HUMAN_SCALE * CHARACTER_SCALE);
      b.add(mount);
    }
    return mount;
  }

  bone(name: string) { return this.bones.get(name); }

  private action(name: string) {
    let a = this.actions.get(name);
    if (!a) {
      const clip = this.human ? (clipSync(HUMAN_CLIPS[name] ?? name) ?? clipSync('Idle_Loop')!) : Assets.clip(name);
      a = this.mixer.clipAction(clip);
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
    // Two names can be one clip (a person plays the library's clip for
    // several of KayKit's): already playing, it only takes the new name.
    if (next === this.base) {
      this.baseName = name;
      next.timeScale = speed;
      return;
    }
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
    // The clip already looping underneath (see setBase): nothing to add.
    if (a === this.base) return 0;
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

  /** Dress the model: `body` repaints swatches of the atlas for every part
   *  (cloth, skin, hair); the cloak gets `body` and `cloak` on top, so it can
   *  differ from the tunic. See render/recolor.ts. */
  paint(body: Paint, cloak: Paint = {}) {
    if (typeof this.id !== 'string') return; // people are dressed by their spec
    const id = this.id;
    this.model.traverse((o) => {
      const m = o as THREE.Mesh;
      if (!m.isMesh) return;
      const mat = m.material as THREE.MeshStandardMaterial;
      const base = (mat.userData.atlas as THREE.Texture | undefined) ?? mat.map;
      if (!base) return;
      mat.userData.atlas = base;
      mat.map = paintedAtlas(base, id, /Cape/.test(o.name) ? { ...body, ...cloak } : body);
      mat.color.set('#ffffff');
    });
  }

  /** Recolour only the parts whose names match (cloth, not skin). */
  tintParts(color: THREE.ColorRepresentation, match: RegExp) {
    const c = new THREE.Color(color);
    this.model.traverse((o) => {
      const m = o as THREE.Mesh;
      if (m.isMesh && match.test(o.name)) (m.material as THREE.MeshStandardMaterial).color.copy(c);
    });
  }

  update(dt: number) {
    this.heading = dampAngle(this.heading, this.headingTarget, 14, dt);
    this.model.rotation.y = this.heading;
    this.mixer.update(dt);
    if (!this.human) applyProportions(this.bones);
    else if (this.headScale !== 1) this.bones.get('Head')?.scale.setScalar(this.headScale);
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
    this.mixer.uncacheRoot(this.model);
    this.root.removeFromParent();
    // Each copy's own materials (tinted) and skeletons (each holds a bone
    // texture on the GPU); geometry and atlas are shared.
    for (const m of this.materials) m.dispose();
    this.model.traverse((o) => { const sk = (o as THREE.SkinnedMesh).skeleton; if ((o as THREE.SkinnedMesh).isSkinnedMesh && sk) sk.dispose(); });
  }
}
