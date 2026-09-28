import * as THREE from 'three';
import type { Renderer } from '@/render/renderer';
import { Atmosphere, type AtmospherePreset } from '@/render/atmosphere';
import { FollowCamera } from '@/render/camera';
import type { Terrain } from '@/render/terrain';
import type { Grass } from '@/render/grass';
import { CrowdRenderer } from '@/render/crowd';
import { CombatFx } from '@/render/fx/combatFx';
import { disposeTree } from '@/render/dispose';
import { PlayerView, type Loadout } from '@/render/playerView';
import { floraUniforms, setOccluder, setFocus } from '@/render/flora';
import { tickWind } from '@/render/instancing';
import { Battle, type BattleSetup } from '@/sim/battle';
import type { CollisionWorld } from '@/sim/collision';
import type { CombatEvent } from '@/sim/events';
import { Input } from '@/core/input';
import { hitstopOn } from '@/render/motion';

/* A place, and whatever is happening in it.
 *
 * The scene owns the look of a zone (terrain, grass, props, lights, air) and
 * the fight or walk happening in it (the Battle). It steps the simulation at
 * a fixed 60 Hz no matter the frame rate, then brings every renderer up to
 * the simulation's state. Towns, the prologue and the outside zone are all
 * this, with different zone builds and combat switched on or off. */

export interface ZoneBuild {
  id: string;
  terrain: Terrain;
  grass: Grass | null;
  collision: CollisionWorld;
  root: THREE.Group;
  atmosphere: AtmospherePreset;
  start: { x: number; z: number; facing?: number };
  /** Per-frame animation for the zone itself (torches, water, banners). */
  tick?: (dt: number, time: number, focusX: number, focusZ: number) => void;
  /** What the map is drawn from, beyond the terrain and the colliders. */
  map?: {
    water?: (x: number, z: number) => boolean; flora?: Array<[string, number, number, number]>; extent?: number;
    /** Houses and towers, drawn as hexagonal footprints. */
    buildings?: Array<{ x: number; z: number; r: number; rot: number }>;
  };
  dispose?: () => void;
}

const STEP = 1 / 60;

export class WorldScene {
  readonly atmo: Atmosphere;
  readonly cam: FollowCamera;
  zone: ZoneBuild | null = null;
  battle: Battle | null = null;
  crowd: CrowdRenderer | null = null;
  fx: CombatFx | null = null;
  player: PlayerView | null = null;
  private acc = 0;
  time = 0;
  /** Hitstop: what is left, in real seconds, of the world holding still
   *  after a heavy blow; and how long until it may again. */
  private hitstop = 0;
  private hitstopCd = 0;
  /** The fight's own clock (it slows with hitstop; the camera does not). */
  private fightTime = 0;
  simPaused = false;
  /** Events drained this frame, for the HUD and the world layer. */
  frameEvents: CombatEvent[] = [];
  private damageFlash = 0;
  heightAt: (x: number, z: number) => number = () => 0;
  onEvents: (events: CombatEvent[]) => void = () => {};
  /** Game-level per-step hook (directors, quest logic). */
  onStep: (dt: number) => void = () => {};
  /** A posed camera (title, creation, cutscenes) instead of the follow cam. */
  showcase: { pos: THREE.Vector3; look: THREE.Vector3 } | null = null;

  constructor(readonly r: Renderer) {
    this.atmo = new Atmosphere(r);
    this.cam = new FollowCamera(r.camera);
  }

  setZone(z: ZoneBuild) {
    this.clearZone();
    this.zone = z;
    this.heightAt = (x, zz) => z.terrain.heightAt(x, zz);
    this.r.scene.add(z.root);
    this.atmo.set(z.atmosphere);
    this.crowd = new CrowdRenderer();
    this.r.scene.add(this.crowd.group);
    this.fx = new CombatFx(this.heightAt);
    this.fx.cam = this.cam;
    this.fx.onDamageFlash = (v) => { this.damageFlash = Math.max(this.damageFlash, v); };
    this.r.scene.add(this.fx.group);
  }

  clearZone() {
    if (!this.zone) return;
    this.r.scene.remove(this.zone.root);
    this.zone.dispose?.();
    // Give the GPU back what this zone uploaded.
    disposeTree(this.zone.root);
    this.zone.grass?.mesh && disposeTree(this.zone.grass.mesh);
    if (this.crowd) { this.r.scene.remove(this.crowd.group); disposeTree(this.crowd.group); }
    if (this.fx) { this.r.scene.remove(this.fx.group); disposeTree(this.fx.group); }
    if (this.player) { this.player.view.dispose(); this.r.scene.remove(this.player.light); }
    this.zone = null;
    this.battle = null;
    this.player = null;
  }

  startBattle(setup: Omit<BattleSetup, 'collision' | 'heightAt'>, loadout: Loadout) {
    if (!this.zone) throw new Error('no zone');
    this.battle = new Battle({ ...setup, collision: this.zone.collision, heightAt: this.heightAt });
    if (this.player) { this.player.view.dispose(); this.r.scene.remove(this.player.light); }
    this.player = new PlayerView(loadout, this.r.scene);
    const p = this.battle.player;
    this.cam.snap(p.x, this.heightAt(p.x, p.z), p.z);
    return this.battle;
  }

  /** Change what the survivor visibly carries. */
  setLoadout(loadout: Loadout) {
    if (!this.player) return;
    this.player.view.dispose();
    this.r.scene.remove(this.player.light);
    this.player = new PlayerView(loadout, this.r.scene);
  }

  update(dt: number) {
    const b = this.battle;
    this.time += dt;
    this.hitstopCd = Math.max(0, this.hitstopCd - dt);
    const held = this.hitstop > 0;
    if (held) this.hitstop -= dt;
    const fightDt = held ? dt * 0.08 : dt;
    this.fightTime += fightDt;
    if (b && !this.simPaused) {
      this.acc += Math.min(fightDt, 0.1);
      while (this.acc >= STEP) {
        this.acc -= STEP;
        if (Input.pressed('dash')) b.dash(Input.moveX, Input.moveZ);
        if (Input.pressed('ability')) b.useAbility(Input.moveX, Input.moveZ);
        this.onStep(STEP);
        b.tick(STEP, Input.moveX, Input.moveZ);
        const evs = b.events.drain();
        if (evs.length) {
          this.fx?.handle(evs, b);
          this.weigh(evs, b);
          for (const e of evs) this.frameEvents.push(e);
          if (evs.some((e) => e.t === 'levelUp')) this.player?.levelFlare();
        }
      }
    }
    this.render(dt, fightDt);
    if (this.frameEvents.length) {
      this.onEvents(this.frameEvents);
      this.frameEvents = [];
    }
  }

  /** Heavy blows hold the world still for a few frames: a boss or an elite
   *  going down, a critical that takes a third of what something had, a blow
   *  that really hurt, a shield bash landing. Never twice in quick
   *  succession, so a crowd going down does not stutter. */
  private weigh(evs: CombatEvent[], b: Battle) {
    if (this.hitstopCd > 0 || !hitstopOn()) return;
    let s = 0;
    for (const e of evs) {
      if (e.t === 'kill' && e.byPlayer && (e.boss || e.elite)) s = Math.max(s, e.boss ? 0.14 : 0.08);
      else if (e.t === 'hit' && e.crit && !e.dot && e.maxHp && e.amount >= e.maxHp * 0.35) s = Math.max(s, 0.045);
      else if (e.t === 'playerHit' && e.amount > b.maxHp * 0.12) s = Math.max(s, 0.07);
      else if (e.t === 'ability' && e.id === 'shield_bash') s = Math.max(s, 0.05);
    }
    if (s > 0) { this.hitstop = s; this.hitstopCd = s + 0.3; }
  }

  /** Bring every renderer up to the simulation. The fight (the survivor,
   *  the crowd, their sparks) runs on its own clock, which hitstop holds;
   *  the camera, its shake and the world around keep real time. */
  private render(dt: number, fightDt: number) {
    const b = this.battle;
    const z = this.zone;
    if (!z) return;
    const t = this.time;
    if (b) {
      const p = b.player;
      const y = this.heightAt(p.x, p.z);
      this.player?.update(b, fightDt, this.fightTime, this.heightAt);
      if (!this.showcase) this.cam.update(dt, p.x, y, p.z, p.vx, p.vz);
      this.crowd?.update(b, this.heightAt, this.fightTime);
      if (this.fx) {
        this.fx.playerPos.set(p.x, y, p.z);
        this.fx.update(b, fightDt, this.fightTime, this.r.camera, this.r.width, this.r.height);
      }
      z.grass?.setPusher(0, p.x, p.z, 1.1, 1);
      // Where the survivor is on screen, so trees in front of them dither.
      const sp = new THREE.Vector3(p.x, y + 1, p.z).project(this.r.camera);
      const buf = this.r.gl.getDrawingBufferSize(new THREE.Vector2());
      const depth = this.r.camera.position.distanceTo(new THREE.Vector3(p.x, y + 1, p.z));
      setOccluder((sp.x * 0.5 + 0.5) * buf.x, (sp.y * 0.5 + 0.5) * buf.y, depth, buf.y * 0.15, buf.x, buf.y);
      setFocus(p.x, y, p.z, this.r.camera.position.x, this.r.camera.position.z);
      // Taking a blow bruises the edges of the picture.
      this.damageFlash = Math.max(0, this.damageFlash - dt * 2.2);
      const lowHp = p.alive ? Math.max(0, 0.35 - p.hp / b.maxHp) * 1.2 : 0.6;
      this.r.grade.damage = Math.min(1, this.damageFlash * 0.7 + lowHp);
      this.r.grade.desaturate = p.alive ? 0 : 0.85;
    }
    if (!b || this.showcase) floraUniforms.uFocus.value.w = 0;
    if (this.showcase) {
      this.r.camera.position.copy(this.showcase.pos);
      this.r.camera.lookAt(this.showcase.look);
    }
    const f = this.showcase ? this.showcase.look : this.cam.focus;
    this.atmo.follow(f.x, f.y, f.z);
    this.atmo.update(t, this.r.camera.position);
    z.grass?.update(t, f.x, f.z);
    z.terrain.time = t;
    floraUniforms.uTime.value = t;
    tickWind(t);
    z.tick?.(dt, t, f.x, f.z);
  }
}
