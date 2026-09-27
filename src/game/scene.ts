import * as THREE from 'three';
import type { Renderer } from '@/render/renderer';
import { Atmosphere, type AtmospherePreset } from '@/render/atmosphere';
import { FollowCamera } from '@/render/camera';
import type { Terrain } from '@/render/terrain';
import type { Grass } from '@/render/grass';
import { CrowdRenderer } from '@/render/crowd';
import { CombatFx } from '@/render/fx/combatFx';
import { PlayerView, type Loadout } from '@/render/playerView';
import { floraUniforms, setOccluder } from '@/render/flora';
import { tickWind } from '@/render/instancing';
import { Battle, type BattleSetup } from '@/sim/battle';
import type { CollisionWorld } from '@/sim/collision';
import type { CombatEvent } from '@/sim/events';
import { Input } from '@/core/input';

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
    if (this.crowd) this.r.scene.remove(this.crowd.group);
    if (this.fx) this.r.scene.remove(this.fx.group);
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
    if (b && !this.simPaused) {
      this.acc += Math.min(dt, 0.1);
      while (this.acc >= STEP) {
        this.acc -= STEP;
        if (Input.pressed('dash')) b.dash(Input.moveX, Input.moveZ);
        if (Input.pressed('ability')) b.useAbility(Input.moveX, Input.moveZ);
        this.onStep(STEP);
        b.tick(STEP, Input.moveX, Input.moveZ);
        const evs = b.events.drain();
        if (evs.length) {
          this.fx?.handle(evs, b);
          for (const e of evs) this.frameEvents.push(e);
          if (evs.some((e) => e.t === 'levelUp')) this.player?.levelFlare();
        }
      }
    }
    this.render(dt);
    if (this.frameEvents.length) {
      this.onEvents(this.frameEvents);
      this.frameEvents = [];
    }
  }

  /** Bring every renderer up to the simulation. */
  private render(dt: number) {
    const b = this.battle;
    const z = this.zone;
    if (!z) return;
    const t = this.time;
    if (b) {
      const p = b.player;
      const y = this.heightAt(p.x, p.z);
      this.player?.update(b, dt, t, this.heightAt);
      if (!this.showcase) this.cam.update(dt, p.x, y, p.z, p.vx, p.vz);
      this.crowd?.update(b, this.heightAt, t);
      if (this.fx) {
        this.fx.playerPos.set(p.x, y, p.z);
        this.fx.update(b, dt, t, this.r.camera, this.r.width, this.r.height);
      }
      z.grass?.setPusher(0, p.x, p.z, 1.1, 1);
      // Where the survivor is on screen, so trees in front of them dither.
      const sp = new THREE.Vector3(p.x, y + 1, p.z).project(this.r.camera);
      const buf = this.r.gl.getDrawingBufferSize(new THREE.Vector2());
      const depth = this.r.camera.position.distanceTo(new THREE.Vector3(p.x, y + 1, p.z));
      setOccluder((sp.x * 0.5 + 0.5) * buf.x, (sp.y * 0.5 + 0.5) * buf.y, depth, buf.y * 0.13);
      // Taking a blow bruises the edges of the picture.
      this.damageFlash = Math.max(0, this.damageFlash - dt * 2.2);
      const lowHp = p.alive ? Math.max(0, 0.35 - p.hp / b.maxHp) * 1.2 : 0.6;
      this.r.grade.damage = Math.min(1, this.damageFlash * 0.7 + lowHp);
      this.r.grade.desaturate = p.alive ? 0 : 0.85;
    }
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
