import * as THREE from 'three';
import type { Game } from '../game';
import type { ZoneRuntime, Interactable, MapMark } from '../zone';
import { buildLowFord, LOWFORD, riverZ, WATER_Y } from '@/world/zones/lowford';
import { WardenView } from '@/render/bossViews';
import { CharacterView } from '@/render/characterView';
import { PRESETS, blendPresets } from '@/render/atmosphere';
import type { Battle } from '@/sim/battle';
import type { Enemy } from '@/sim/entities';
import { ABILITIES } from '@/content/abilities';
import { hint, objectives, boss, say, announce, toast, overlay, zoneInfo, type Objective } from '@/ui/store';
import { Input } from '@/core/input';
import { clamp } from '@/core/math';

/* The prologue: one night on the Low Ford road.
 *
 * It is a tutorial that never stops to be one. Each thing the game needs
 * you to know arrives as the road puts it in front of you:
 *
 *   wake      the dead climb out of the ground around your fire     (move)
 *   rising    their stones hold light; the ember rises     (ember, the draft)
 *   road      up the road; shieldmen, bowmen             (build, positioning)
 *   ambush    the dead rise out of the ditch by a broken cart     (the horde)
 *   post      a Barrow Knight over a dead watchman's chest (elites, equipment)
 *   barrow    a Grave-Caller raising the dead                     (ability)
 *   ford      the Ford-Warden                                        (boss)
 *   dawn      what took the Warden's heart; the gate opens      (the world)
 *
 * Dying here is forgiven: the ember is not done with you, and you get up
 * again at the last place you were safe. That is the only place in the game
 * where that is true. */

type Stage = 'wake' | 'rising' | 'road' | 'ambush' | 'road2' | 'post' | 'barrow' | 'toford' | 'intro' | 'boss' | 'victory' | 'dawn' | 'exit';

interface WardenAI {
  mode: 'sleep' | 'wake' | 'walk' | 'windup' | 'cleave' | 'chargeWind' | 'charge' | 'stun' | 'channel' | 'dead';
  t: number;
  cleaveCd: number;
  chargeCd: number;
  channelCd: number;
  dirX: number; dirZ: number;
  travelled: number;
  channelHp: number;
  thresholds: number[];
  raiseT: number;
  contactT: number;
  hitX: number; hitZ: number;
}

export function prologue(g: Game): ZoneRuntime & { fire: { x: number; z: number } } {
  const built = buildLowFord(g.r.spec.grassDensity);
  const L = LOWFORD;
  const kit = built.kit;
  const col = built.zone.collision;
  let b: Battle | null = null;
  let stage: Stage = 'wake';
  let stageT = 0;
  let spawnT = 2;
  let checkpoint = { x: L.camp.x + 1.5, z: L.camp.z - 1.5 };
  const shown = new Set<string>();
  const litPylons = built.pylons.map(() => true);
  const pylonHp = built.pylons.map(() => 260);
  let warden: Enemy | null = null;
  let wardenGone = false;
  const wardenView = new WardenView(built.zone.root);
  const wardenHome = { x: L.ford.x + 1, z: L.ford.z - 2 };
  let wardenPos = { x: wardenHome.x, z: wardenHome.z, facing: 0 };
  const ai: WardenAI = { mode: 'sleep', t: 0, cleaveCd: 3, chargeCd: 6, channelCd: 30, dirX: 0, dirZ: 1, travelled: 0, channelHp: 0, thresholds: [0.7, 0.4], raiseT: 0, contactT: 0, hitX: 0, hitZ: 0 };
  let caller: Enemy | null = null;
  let knight: Enemy | null = null;
  let cutT = 0;
  let core: THREE.Mesh | null = null;
  let coreLight: THREE.PointLight | null = null;
  let grim: Enemy | null = null;
  let dawnK = 0;
  let envT = 0;
  let deadT = -1;
  let chestOpened = false;
  let finished = false;

  wardenView.setPose('sleep');

  /* ------------------------------------------------------------- scenery -- */

  // The dead watchman at the post, and his chest.
  const watchman = new CharacterView('knight');
  watchman.showOnly(['Knight_Helmet', 'Round_Shield']);
  watchman.tint('#9a9890');
  watchman.root.position.set(L.watchman.x, kit.y(L.watchman.x, L.watchman.z), L.watchman.z);
  watchman.face(2.2, true);
  watchman.loop('Death_A_Pose', 0);
  built.zone.root.add(watchman.root);

  /* ------------------------------------------------------------- helpers -- */

  const setObjective = (o: Objective | null) => { objectives.value = o ? [o] : []; };
  const tip = (id: string, title: string, text: string, keys?: string[], life = 9) => {
    if (shown.has(id)) return;
    shown.add(id);
    hint.value = { id, title, text, keys };
    if (life > 0) setTimeout(() => { if (hint.value?.id === id) hint.value = null; }, life * 1000);
  };
  const key = (a: Parameters<typeof Input.keyLabel>[0]) => Input.keyLabel(a);
  const go = (s: Stage) => { stage = s; stageT = 0; };

  const openGround = (x: number, z: number) => {
    if (!b) return false;
    if (b.collision.blocked(x, z, 0.6)) return false;
    if (Math.abs(z - riverZ(x)) < 9 && Math.abs(x) > 14) return false;
    return Math.abs(x) < 72 && Math.abs(z) < 122;
  };

  /** Some of the dead, somewhere around the survivor. `ahead` biases north. */
  const spawnAround = (def: string, n: number, rMin: number, rMax: number, ahead = 0, level = 1) => {
    if (!b) return;
    const p = b.player;
    for (let i = 0; i < n; i++) {
      for (let tries = 0; tries < 8; tries++) {
        let a = b.rng.next() * Math.PI * 2;
        if (ahead > 0 && b.rng.next() < ahead) a = -Math.PI / 2 + (b.rng.next() - 0.5) * 1.8;
        const d = rMin + b.rng.next() * (rMax - rMin);
        const x = p.x + Math.cos(a) * d, z = p.z + Math.sin(a) * d;
        if (!openGround(x, z)) continue;
        b.spawnEnemy(def, x, z, { style: def === 'risen' || def === 'risen_warrior' ? 'rise' : 'walk', level });
        break;
      }
    }
  };

  const hostiles = () => {
    let n = 0;
    b?.enemies.forEach((e) => { if (e.alive && e.state !== 'dying' && e.disposition === 'hostile') n++; });
    return n;
  };

  const clearAround = (x: number, z: number, r: number) => {
    b?.enemies.forEach((e) => {
      if (e.alive && !e.boss && e !== grim && Math.hypot(e.x - x, e.z - z) < r) b!.killEnemy(e, false, null);
    });
  };

  /* ---------------------------------------------------- the Ford-Warden -- */

  const litCount = () => litPylons.filter(Boolean).length;
  const WARD = [1, 0.7, 0.55, 0.4];

  const snuff = (i: number, how: 'charge' | 'broken') => {
    if (!litPylons[i] || !b) return;
    litPylons[i] = false;
    const p = built.pylons[i];
    kit.setLit(p.src, false);
    b.events.emit({ t: 'explosion', x: p.x, z: p.z, radius: 3.2, school: 'frost', power: 1.4 });
    b.events.emit({ t: 'shake', amount: 0.6 });
    b.events.emit({ t: 'bark', x: p.x, z: p.z, text: how === 'charge' ? 'The lamp shatters!' : 'The lamp goes dark' });
    const left = litCount();
    if (left > 0) toast('world', `A lamp goes out — ${left} still burn${left === 1 ? 's' : ''}`);
    else announce('The lamps are dark', 'The Warden is laid bare', 'boon', 3.2);
  };

  const relight = () => {
    const i = litPylons.findIndex((l) => !l);
    if (i < 0) return;
    litPylons[i] = true;
    pylonHp[i] = 200;
    kit.setLit(built.pylons[i].src, true);
    b?.events.emit({ t: 'nova', x: built.pylons[i].x, z: built.pylons[i].z, radius: 4, school: 'frost', duration: 0.8 });
    toast('warning', 'The drowned rekindle a lamp');
  };

  const wardenTick = (e: Enemy, dt: number): boolean => {
    if (!b) return true;
    const p = b.player;
    ai.t += dt;
    e.vx = e.vz = 0;
    const dx = p.x - e.x, dz = p.z - e.z;
    const dist = Math.hypot(dx, dz) || 0.001;
    const hpK = e.hp / e.maxHp;
    // The ward: the lamps take most of every blow.
    let mul = WARD[litCount()];
    if (ai.mode === 'stun') mul *= 1.5;
    e.takenMul = mul;
    ai.cleaveCd -= dt; ai.chargeCd -= dt; ai.channelCd -= dt;

    // Interrupted mid-channel (Battle.interrupt sets this).
    if (ai.mode === 'channel' && e.state === 'stunned') {
      ai.mode = 'stun'; ai.t = 0; e.stateT = 0;
      wardenView.setPose('stunned');
      b.events.emit({ t: 'announce', title: 'Channel broken', tone: 'boon' });
    }
    e.state = ai.mode === 'channel' ? 'casting' : ai.mode === 'windup' || ai.mode === 'chargeWind' ? 'windup' : 'active';

    switch (ai.mode) {
      case 'sleep':
      case 'wake':
        return true;
      case 'walk': {
        e.facing = Math.atan2(dz, dx);
        // Channel at thresholds, or when it has been a while.
        const th = ai.thresholds[0];
        if ((th !== undefined && hpK < th) || ai.channelCd <= 0) {
          if (th !== undefined && hpK < th) ai.thresholds.shift();
          ai.mode = 'channel'; ai.t = 0; ai.channelHp = e.hp; ai.channelCd = 34; ai.raiseT = 0.6;
          wardenView.setPose('channel');
          b.events.emit({ t: 'bark', x: e.x, z: e.z, text: 'RISE, YOU WHO DROWNED HERE.', speaker: 'The Ford-Warden' });
          return true;
        }
        if (dist < 5.2 && ai.cleaveCd <= 0) {
          ai.mode = 'windup'; ai.t = 0; ai.dirX = dx / dist; ai.dirZ = dz / dist;
          ai.hitX = e.x + ai.dirX * 3; ai.hitZ = e.z + ai.dirZ * 3;
          b.events.emit({ t: 'telegraph', id: e.id * 10 + 1, shape: 'circle', x: ai.hitX, z: ai.hitZ, radius: 3.4, duration: 1.05, hostile: true });
          wardenView.setPose('windup');
          return true;
        }
        if (dist > 6.5 && ai.chargeCd <= 0) {
          ai.mode = 'chargeWind'; ai.t = 0; ai.dirX = dx / dist; ai.dirZ = dz / dist;
          const len = Math.min(24, dist + 8);
          b.events.emit({ t: 'telegraph', id: e.id * 10 + 2, shape: 'line', x: e.x, z: e.z, x1: e.x + ai.dirX * len, z1: e.z + ai.dirZ * len, radius: 0, width: 3, duration: 1.3, hostile: true });
          ai.travelled = len;
          wardenView.setPose('charge-windup');
          b.events.emit({ t: 'bark', x: e.x, z: e.z, text: 'It lowers its head...' });
          return true;
        }
        if (dist > e.radius + 1.2) {
          const sp = e.speed * (litCount() === 0 ? 1.25 : 1);
          e.vx = (dx / dist) * sp; e.vz = (dz / dist) * sp;
          e.x += e.vx * dt; e.z += e.vz * dt;
          b.collision.resolve(e, e.radius);
        }
        wardenView.setPose('walk');
        // Contact.
        ai.contactT -= dt;
        if (dist < e.radius + p.radius + 0.4 && ai.contactT <= 0) {
          ai.contactT = 1.2;
          b.hurtPlayer(e.damage * 0.6, 'physical', 'The Ford-Warden', e);
        }
        return true;
      }
      case 'windup':
        if (ai.t >= 1.05) {
          ai.mode = 'cleave'; ai.t = 0;
          wardenView.setPose('cleave');
          if (Math.hypot(p.x - ai.hitX, p.z - ai.hitZ) < 3.4 + p.radius) b.hurtPlayer(e.damage * 1.5, 'physical', 'The Ford-Warden', e);
          b.events.emit({ t: 'explosion', x: ai.hitX, z: ai.hitZ, radius: 3.4, school: 'physical', power: 1.2 });
          b.events.emit({ t: 'shake', amount: 0.55 });
          b.forEachHostileInRadius(ai.hitX, ai.hitZ, 3.4, () => {});
        }
        return true;
      case 'cleave':
        if (ai.t > 0.8) { ai.mode = 'walk'; ai.cleaveCd = 3.2; wardenView.release(); }
        return true;
      case 'chargeWind':
        e.facing = Math.atan2(ai.dirZ, ai.dirX);
        if (ai.t >= 1.3) { ai.mode = 'charge'; ai.t = 0; wardenView.setPose('charge'); }
        return true;
      case 'charge': {
        const sp = 17;
        const step = Math.min(sp * dt, ai.travelled);
        const x0 = e.x, z0 = e.z;
        e.x += ai.dirX * step; e.z += ai.dirZ * step;
        e.vx = ai.dirX * sp; e.vz = ai.dirZ * sp;
        ai.travelled -= step;
        // A lamp in the way: it goes through it, and it hurts.
        for (let i = 0; i < built.pylons.length; i++) {
          const py = built.pylons[i];
          if (litPylons[i] && Math.hypot(py.x - e.x, py.z - e.z) < e.radius + 0.9) {
            snuff(i, 'charge');
            ai.mode = 'stun'; ai.t = -1.5;
            wardenView.setPose('stunned');
            b.events.emit({ t: 'bark', x: e.x, z: e.z, text: 'The Warden reels!' });
            return true;
          }
        }
        // Anything else solid stops it short.
        b.collision.resolve(e, e.radius);
        const moved = Math.hypot(e.x - x0, e.z - z0);
        if (moved < step * 0.4) {
          ai.mode = 'stun'; ai.t = 0.8;
          wardenView.setPose('stunned');
          b.events.emit({ t: 'shake', amount: 0.5 });
        } else if (Math.hypot(p.x - e.x, p.z - e.z) < e.radius + p.radius + 0.3 && p.iframes <= 0) {
          b.hurtPlayer(e.damage * 1.4, 'physical', 'The Ford-Warden', e);
        }
        if (ai.travelled <= 0.01 && ai.mode === 'charge') { ai.mode = 'walk'; ai.chargeCd = 8 + b.rng.next() * 3; wardenView.release(); }
        return true;
      }
      case 'stun':
        if (ai.t >= 2.5) { ai.mode = 'walk'; ai.chargeCd = Math.max(ai.chargeCd, 5); ai.cleaveCd = 1.5; wardenView.release(); }
        return true;
      case 'channel': {
        const k = ai.t / 6;
        boss.value = boss.value ? { ...boss.value, channel: { label: 'Calling the drowned — break it!', progress: Math.min(1, k) } } : boss.value;
        ai.raiseT -= dt;
        if (ai.raiseT <= 0) {
          ai.raiseT = 0.9;
          for (let i = 0; i < 2; i++) {
            const a = b.rng.next() * Math.PI * 2, d = 4 + b.rng.next() * 6;
            const x = e.x + Math.cos(a) * d, z = e.z + Math.sin(a) * d;
            if (openGround(x, z)) b.spawnEnemy('risen', x, z, { style: 'rise', level: 2 });
          }
        }
        // Hurt it badly enough and the channel breaks.
        if (ai.channelHp - e.hp > e.maxHp * 0.09) {
          ai.mode = 'stun'; ai.t = 0;
          wardenView.setPose('stunned');
          b.events.emit({ t: 'announce', title: 'Channel broken', tone: 'boon' });
        } else if (ai.t >= 6) {
          e.hp = Math.min(e.maxHp, e.hp + e.maxHp * 0.06);
          relight();
          ai.mode = 'walk';
          wardenView.release();
        }
        if (ai.mode !== 'channel' && boss.value) boss.value = { ...boss.value, channel: null };
        return true;
      }
      default:
        return true;
    }
  };

  /* ------------------------------------------------------------- stages -- */

  const director = (dt: number) => {
    if (!b) return;
    const p = b.player;
    stageT += dt;
    spawnT -= dt;
    const n = hostiles();
    switch (stage) {
      case 'wake':
        if (stageT > 1.2) tip('move', 'Move', 'The dead are climbing out of the ground around your fire. Keep moving — your weapon strikes on its own.', ['W', 'A', 'S', 'D'], 11);
        if (stageT > 3) { go('rising'); spawnT = 0; }
        break;
      case 'rising': {
        // Keep the clearing full: more of them the longer it goes on.
        const want = Math.min(40, 16 + stageT * 0.3);
        if (spawnT <= 0 && n < want) { spawnAround('risen', 2 + (stageT > 40 ? 1 : 0), 9, 14); spawnT = stageT > 30 ? 0.8 : 1.1; }
        if (stageT > 14) tip('dash', 'Dash', `${key('dash')}: a quick roll that nothing can touch. It has two charges, and they come back.`, [key('dash')]);
        if ((b.ember.level >= 4 && stageT > 70) || stageT > 110) {
          go('road');
          checkpoint = { x: p.x, z: p.z };
          say('The ground goes still. For now. The road runs north, toward the Waystation.', undefined, 5);
          setObjective({ id: 'pro', title: 'The Low Ford', tone: 'tutorial', steps: [{ text: 'Survive the night', done: true }, { text: 'Follow the road north' }] });
          tip('road', 'The road north', 'Follow the road. The dead keep coming; let them come to your weapons, and keep your feet moving.');
        }
        break;
      }
      case 'road':
      case 'road2': {
        if (spawnT <= 0 && n < 24) {
          const def = stage === 'road2' && b.rng.next() < 0.2 ? 'risen_warrior' : b.rng.next() < 0.12 ? 'risen_archer' : 'risen';
          spawnAround(def, 1 + (b.rng.next() < 0.5 ? 1 : 0), 10, 15, 0.55, stage === 'road2' ? 2 : 1);
          spawnT = 1.3;
          if (def === 'risen_warrior') tip('shield', 'Shieldmen', 'Bolts and arrows glance off a raised shield. Get to its side, or hit it with something that is not a projectile.');
        }
        if (stage === 'road' && p.z < L.cart.z + 7) {
          go('ambush');
          checkpoint = { x: L.cart.x - 3, z: L.cart.z + 8 };
          say('A wagon on its side, and the ditch beside it full of the drowned. They were waiting.', undefined, 5);
          setObjective({ id: 'pro', title: 'The Low Ford', tone: 'tutorial', steps: [{ text: 'Follow the road north', done: true }, { text: 'Survive the ambush at the wagon' }] });
          for (let i = 0; i < 10; i++) spawnAround(i % 4 === 0 ? 'risen_warrior' : 'risen', 1, 5, 9, 0, 2);
        }
        if (stage === 'road2' && Math.hypot(p.x - L.post.x, p.z - L.post.z) < 18) {
          go('post');
          checkpoint = { x: L.post.x - 6, z: L.post.z + 4 };
          knight = b.spawnEnemy('barrow_knight', L.post.x - 1, L.post.z - 1.5, { level: 1, tag: 'knight', style: 'rise' });
          for (let i = 0; i < 4; i++) spawnAround('risen', 1, 5, 9, 0, 2);
          say('Something in old armour is standing guard over the dead watchman. It turns to look at you.', undefined, 5);
          setObjective({ id: 'pro', title: 'The Low Ford', tone: 'tutorial', steps: [{ text: 'Survive the ambush at the wagon', done: true }, { text: 'Put down the Barrow Knight' }, { text: 'Search the old Watch-post' }] });
          tip('elite', 'Elites', 'Bigger, tougher, and worth it: elites carry better things. When a red line appears on the ground, it is about to come down it. Be off the line.', undefined, 12);
        }
        break;
      }
      case 'ambush': {
        const want = Math.min(46, 26 + stageT * 0.5);
        if (spawnT <= 0 && n < want) {
          const r = b.rng.next();
          spawnAround(r < 0.22 ? 'risen_warrior' : r < 0.32 ? 'risen_archer' : 'risen', 3 + (b.rng.next() < 0.5 ? 1 : 0), 8, 14, 0, 2);
          spawnT = 1.05;
        }
        if (stageT > 48) {
          go('road2');
          checkpoint = { x: p.x, z: p.z };
          say('The last of them falls back into the ditch and stays there.', undefined, 4);
          setObjective({ id: 'pro', title: 'The Low Ford', tone: 'tutorial', steps: [{ text: 'Survive the ambush at the wagon', done: true }, { text: 'Follow the road north' }] });
        }
        break;
      }
      case 'post': {
        if (stageT > 8 && spawnT <= 0 && n < 16) { spawnAround('risen', 1, 12, 16, 0.3, 2); spawnT = 2.5; }
        if (!knight && !chestOpened) {
          tip('chest', 'The Watch-post', 'The watchman\'s chest is unguarded now.', [key('interact')]);
          setObjective({ id: 'pro', title: 'The Low Ford', tone: 'tutorial', steps: [{ text: 'Put down the Barrow Knight', done: true }, { text: 'Search the old Watch-post' }] });
        }
        if (p.z < 21 && !knight) {
          go('barrow');
          checkpoint = { x: p.x, z: p.z };
          startBarrow();
        }
        break;
      }
      case 'barrow': {
        if (caller) {
          const d = Math.hypot(caller.x - p.x, caller.z - p.z);
          if (d < 16) {
            const ab = b.ability ? ABILITIES[b.ability] : null;
            if (ab) tip('ability', ab.name, `${ab.description} The Grave-Caller is raising the dead${ab.interrupts ? ' — this will break its channel' : ' — kill it before it raises too many'}.`, [key('ability')], 14);
          }
          if (spawnT <= 0 && n < 16 && stageT > 8) { spawnAround('risen', 1, 11, 15, 0, 2); spawnT = 2.5; }
        } else if (stageT > 1) {
          go('toford');
          checkpoint = { x: L.barrow.x + 10, z: L.barrow.z - 6 };
          setObjective({ id: 'pro', title: 'The Low Ford', tone: 'tutorial', steps: [{ text: 'Put down the Grave-Caller', done: true }, { text: 'Cross at the Low Ford' }] });
          say('The dead go quiet. Somewhere ahead, water, and a cold blue light.', undefined, 5);
        }
        break;
      }
      case 'toford': {
        if (spawnT <= 0 && n < 18) { spawnAround(b.rng.next() < 0.25 ? 'risen_archer' : 'risen', 1, 11, 15, 0.5, 2); spawnT = 2.4; }
        if (p.z < L.ford.z + 17) startIntro();
        break;
      }
      case 'intro':
        runIntro(dt);
        break;
      case 'boss': {
        if (warden && warden.alive) {
          const lit = litCount();
          boss.value = {
            name: 'The Ford-Warden', title: 'Keeper of the Low Crossing', hp: warden.hp, maxHp: warden.maxHp, phases: [0.7, 0.4],
            channel: boss.value?.channel ?? null, shielded: lit > 0,
          };
          if (stageT > 3) tip('lamps', 'The lamps', 'While the three lamps burn, the Warden shrugs off most of every blow. Stand in front of a lamp when it charges — or break the lamps yourself.', undefined, 14);
          if (ai.mode === 'channel') tip('channel', 'Break the channel', `It is calling up the drowned. ${b.ability && ABILITIES[b.ability].interrupts ? `${key('ability')} breaks it.` : 'Hurt it hard enough and it breaks.'} If it finishes, a lamp is lit again.`, [key('ability')], 10);
          if (stageT > 40 && lit === 3) { shown.delete('lamps2'); tip('lamps2', 'The lamps', 'Lure its charge into a lamp: stand before one, and step aside at the last moment.', [key('dash')], 10); }
        }
        if (p.hp < b.maxHp * 0.4) tip('quaff', 'Draughts', `${key('ultimate')}: drink a health draught.`, [key('ultimate')], 8);
        break;
      }
      case 'victory':
        runVictory(dt);
        break;
      case 'dawn': {
        dawnK = Math.min(1, dawnK + dt / 10);
        envT -= dt;
        const pre = blendPresets(PRESETS.night, PRESETS.dawn, dawnK * dawnK * (3 - 2 * dawnK));
        g.scene.atmo.set(pre, envT <= 0);
        if (envT <= 0) envT = 1.2;
        if (dawnK >= 1 && stageT > 10) go('exit');
        break;
      }
      case 'exit':
        if (p.z < L.exitZ && !finished) {
          finished = true;
          finishPrologue();
        }
        break;
    }
  };

  const startBarrow = () => {
    if (!b) return;
    setObjective({ id: 'pro', title: 'The Low Ford', tone: 'tutorial', steps: [{ text: 'Search the old Watch-post', done: true }, { text: 'Put down the Grave-Caller' }] });
    caller = b.spawnEnemy('grave_caller', L.barrow.x - 3, L.barrow.z, { level: 2, tag: 'caller', elite: true });
    for (let i = 0; i < 5; i++) {
      const a = (i / 5) * Math.PI * 2;
      b.spawnEnemy(i % 3 === 0 ? 'risen_warrior' : 'risen', L.barrow.x + Math.cos(a) * 4, L.barrow.z + Math.sin(a) * 4, { style: 'rise', level: 2 });
    }
    say('Past the fence, a figure in a tall hat is talking to the graves. The graves are listening.', undefined, 6);
  };

  /* ------------------------------------------------------------- intro -- */

  const startIntro = () => {
    if (!b) return;
    go('intro');
    cutT = 0;
    checkpoint = { x: 0, z: L.ford.z + 19 };
    Input.captured = true;
    clearAround(L.ford.x, L.ford.z, 30);
    b.worldRate = 0.001; b.worldRateT = 1e9;
    g.poseShowcase(new THREE.Vector3(wardenHome.x + 9, kit.y(wardenHome.x, wardenHome.z) + 7, wardenHome.z + 15), new THREE.Vector3(wardenHome.x, 0.4, wardenHome.z));
    hint.value = null;
  };

  const runIntro = (dt: number) => {
    if (!b) return;
    cutT += dt;
    if (cutT > 0.8 && !shown.has('intro1')) { shown.add('intro1'); say('Something lies in the ford, larger than any man, with a lamp in its fist.', undefined, 3.6); }
    if (cutT > 2.6 && !shown.has('intro2')) {
      shown.add('intro2');
      wardenView.setPose('wake');
      b.events.emit({ t: 'shake', amount: 0.5 });
      for (const py of built.pylons) b.events.emit({ t: 'nova', x: py.x, z: py.z, radius: 3, school: 'frost', duration: 0.9 });
    }
    if (cutT > 4.2 && !shown.has('intro3')) {
      shown.add('intro3');
      announce('The Ford-Warden', 'Keeper of the Low Crossing', 'danger', 3.4);
      b.events.emit({ t: 'bark', x: wardenPos.x, z: wardenPos.z, text: 'NONE CROSS AFTER DARK.', speaker: 'The Ford-Warden' });
    }
    if (cutT > 6.4) {
      g.poseShowcase(null);
      Input.captured = false;
      b.worldRate = 1; b.worldRateT = 0;
      warden = b.spawnEnemy('ford_warden', wardenPos.x, wardenPos.z, { level: 1, tag: 'warden' });
      if (warden) { warden.facing = Math.PI / 2; ai.mode = 'walk'; ai.t = 0; }
      wardenView.release();
      go('boss');
      setObjective({ id: 'pro', title: 'The Low Ford', tone: 'tutorial', steps: [{ text: 'Cross at the Low Ford' }, { text: 'Put out the lamps', optional: true }] });
    }
  };

  /* ----------------------------------------------------------- victory -- */

  const onWardenDown = (e: Enemy) => {
    if (!b) return;
    ai.mode = 'dead';
    wardenView.setPose('dead');
    wardenPos = { x: e.x, z: e.z, facing: Math.PI / 2 - e.facing };
    boss.value = null;
    b.events.emit({ t: 'shake', amount: 0.9 });
    announce('The Ford-Warden falls', undefined, 'boon', 3.2);
    for (let i = 0; i < built.pylons.length; i++) if (litPylons[i]) { litPylons[i] = false; kit.setLit(built.pylons[i].src, false); }
    clearAround(e.x, e.z, 40);
    // What it leaves.
    b.spawnPickup('item', e.x + 1.5, e.z + 1, 1, 'wardens_lampiron');
    b.spawnPickup('item', e.x - 1.2, e.z + 1.6, 3, 'ember_shard');
    for (let i = 0; i < 12; i++) b.spawnPickup('gold', e.x + (b.rng.next() - 0.5) * 4, e.z + (b.rng.next() - 0.5) * 4, 4);
    go('victory');
    cutT = 0;
    setObjective({ id: 'pro', title: 'The Low Ford', tone: 'tutorial', steps: [{ text: 'Cross at the Low Ford', done: true }] });
  };

  const runVictory = (dt: number) => {
    if (!b) return;
    cutT += dt;
    const cx = wardenPos.x, cz = wardenPos.z;
    const cy = Math.max(kit.y(cx, cz), WATER_Y);
    if (cutT > 1.6 && !core) {
      core = new THREE.Mesh(new THREE.IcosahedronGeometry(0.42, 1), new THREE.MeshBasicMaterial({ color: new THREE.Color('#bfe6ff').multiplyScalar(6) }));
      core.position.set(cx, cy + 0.8, cz);
      built.zone.root.add(core);
      coreLight = new THREE.PointLight(0x9ad8ff, 18, 14, 1.5);
      coreLight.position.copy(core.position);
      built.zone.root.add(coreLight);
      say('Where the Warden fell, its heart is still burning: a stone the size of a fist, full of cold light.', undefined, 5);
      g.poseShowcase(new THREE.Vector3(cx + 6, cy + 6, cz + 11), new THREE.Vector3(cx, cy + 1, cz));
      Input.captured = true;
    }
    if (core) {
      core.rotation.y += dt * 1.4;
      const pulse = 1 + Math.sin(cutT * 5) * 0.08;
      core.scale.setScalar(pulse);
      if (!grim) core.position.y = Math.min(cy + 1.6, core.position.y + dt * 0.3);
      if (coreLight) { coreLight.position.copy(core.position); coreLight.intensity = 16 + Math.sin(cutT * 7) * 3; }
    }
    if (cutT > 4.2 && !grim) {
      b.events.emit({ t: 'shake', amount: 0.7 });
      grim = b.spawnEnemy('grimtunnel', cx + 2.2, cz + 1.2, { style: 'burrow', disposition: 'neutral', tag: 'grim' });
      if (grim) { grim.state = 'surfacing'; grim.stateT = 0.55; }
      b.events.emit({ t: 'spawn', enemy: grim?.id ?? -1, x: cx + 2.2, z: cz + 1.2, def: 'grimtunnel', style: 'burrow' });
    }
    if (grim && grim.alive) {
      grim.facing = Math.atan2(cz - grim.z, cx - grim.x);
      if (grim.state === 'surfacing') { grim.stateT -= dt; if (grim.stateT <= 0) grim.state = 'active'; }
    }
    if (cutT > 5.4 && !shown.has('grim1')) { shown.add('grim1'); b.events.emit({ t: 'bark', x: cx + 2.2, z: cz + 1.2, text: 'Oho! A Warden\'s heart, still warm! Nobody\'s, is it? Nobody\'s!', speaker: 'Grimtunnel' }); }
    if (cutT > 8.4 && !shown.has('grim2')) { shown.add('grim2'); b.events.emit({ t: 'bark', x: cx + 2.2, z: cz + 1.2, text: 'Finders keepers, surface-meat. The Deep Dig thanks you!', speaker: 'Grimtunnel' }); }
    if (core && grim && cutT > 9.6) {
      core.position.lerp(new THREE.Vector3(grim.x, cy + 1.2, grim.z), Math.min(1, dt * 4));
    }
    if (cutT > 11 && grim && grim.alive && grim.state !== 'burrowed') {
      grim.state = 'burrowed';
      b.events.emit({ t: 'spawn', enemy: grim.id, x: grim.x, z: grim.z, def: 'grimtunnel', style: 'burrow' });
      b.events.emit({ t: 'shake', amount: 0.4 });
      if (core) { core.removeFromParent(); core = null; }
      if (coreLight) { coreLight.removeFromParent(); coreLight = null; }
    }
    if (cutT > 12 && grim) {
      if (grim.alive) b.enemies.release(grim);
      grim = null;
      g.apply([
        { learn: 'grimtunnel', text: 'You have seen Grimtunnel. The lamplings are digging for something.' },
        { history: { id: 'ford_warden_slain', text: 'put down the Ford-Warden at the Low Ford', tags: ['deed', 'undead'], spread: 2, sentiment: { respect: 10 } } },
        { history: { id: 'core_stolen', text: 'let a lampling steal the Warden\'s heart', tags: ['lampling'], spread: 1 } },
      ]);
      toast('lore', 'Grimtunnel took the Warden\'s heart', { sub: 'Whatever the diggers want it for, they went down, not away.', life: 8 });
    }
    if (cutT > 13) {
      g.poseShowcase(null);
      Input.captured = false;
      go('dawn');
      dawnK = 0;
      col.removeTagged('gate');
      say('Grey light, then gold. Up the road, the Waystation\'s gate is opening.', undefined, 6);
      setObjective({ id: 'pro', title: 'The Low Ford', tone: 'tutorial', steps: [{ text: 'Walk up the road to the Waystation' }] });
      g.world!.time = 'dawn';
      if (zoneInfo.value) zoneInfo.value = { ...zoneInfo.value, time: 'dawn' };
    }
  };

  const finishPrologue = () => {
    g.apply([{ set: { 'prologue.done': true } }, { quest: { id: 'prologue', status: 'resolved', outcome: 'resolved' } }]);
    hint.value = null;
    objectives.value = [];
    if (g.hasZone('waystation')) g.travel('waystation', 'The Waystation', 'Where the three roads meet');
    else { g.save('prologue'); overlay.value = 'chapter'; }
  };

  /* -------------------------------------------------------- interaction -- */

  const interactables: Interactable[] = [
    {
      id: 'chest', x: L.chest.x, z: L.chest.z, r: 2.6, verb: 'Open', name: 'Watch Chest',
      when: () => !chestOpened,
      locked: () => (knight ? 'The Barrow Knight stands over it' : null),
      act: () => {
        chestOpened = true;
        const ch = g.ch!;
        g.apply([{ give: 'padded_jerkin', rarity: 1 }, { give: 'health_draught', qty: 2 }, { gold: 15 }]);
        void ch;
        hint.value = null;
        setTimeout(() => tip('pack', 'Your pack', 'What you find, you keep. Ember fades when you rest; gear, gold and what you learn do not. Open your pack to wear the jerkin.', [key('inventory')], 14), 600);
        setObjective({ id: 'pro', title: 'The Low Ford', tone: 'tutorial', steps: [{ text: 'Search the old Watch-post', done: true }, { text: 'Wear what you found', optional: true }, { text: 'Follow the road north' }] });
      },
    },
    {
      id: 'watchman', x: L.watchman.x, z: L.watchman.z, r: 2.4, verb: 'Examine', name: 'Dead Watchman',
      act: () => {
        say('A Watchman, a long time dead. In his belt-book, the last line: "Lamps at the Low Ford lit again, and not by us. The Warden is walking."', undefined, 8);
        g.apply([{ learn: 'lore.warden', text: 'The lamps at the ford feed the Warden.' }]);
        // The devout hear the dead, a little.
        if (g.ch?.knowledge.includes('faith')) {
          setTimeout(() => say('...and for you alone, the dead man\'s jaw moves: "It shatters its own lamps when it charges. Make it charge."', 'The dead Watchman', 7), 8200);
        }
      },
    },
    {
      id: 'fire', x: L.fire.x, z: L.fire.z, r: 2.2, verb: 'Warm your hands', name: 'Campfire',
      when: () => stage === 'rising' || stage === 'wake',
      act: () => say('The fire is almost out. It will not hold them back.', undefined, 3.5),
    },
  ];

  /* ------------------------------------------------------------ runtime -- */

  return {
    id: 'lowford', name: 'The Low Ford Road', region: 'Thornhollow, south', build: built.zone, combat: true, fire: L.fire,
    // Back down the road from the Waystation: arrive at the north end, by the gate.
    arrival: (from) => (from === 'waystation' ? { x: L.gate.x + 0.5, z: L.exitZ + 9, facing: 0 } : { x: L.camp.x + 1.5, z: L.camp.z - 1.5, facing: Math.PI }),
    timeOf: () => (stage === 'dawn' || stage === 'exit' ? 'dawn' : 'night'),
    begin: (battle) => {
      b = battle;
      g.bridge.draftTip = 'Each time the ember rises, choose one. Weapons fire on their own; boons and rules change how everything works together.';
      if (g.world?.facts['prologue.done']) {
        // Loaded after the prologue: the road at dawn, the dead at rest.
        stage = 'exit'; stageT = 0; dawnK = 1;
        g.scene.atmo.set(PRESETS.dawn);
        col.removeTagged('gate');
        for (let i = 0; i < built.pylons.length; i++) kit.setLit(built.pylons[i].src, false);
        ai.mode = 'dead'; wardenGone = true;
        wardenView.view.root.visible = false;
        return;
      }
      setObjective({ id: 'pro', title: 'The Low Ford', tone: 'tutorial', steps: [{ text: 'Survive the night' }] });
      say('The fire has burned low. Out in the dark, the ground is moving.', undefined, 4.5);
      g.announceZone();
    },
    step: (dt) => director(dt),
    mapMarks: (): MapMark[] => [
      { x: L.camp.x, z: L.camp.z, label: 'Your camp', kind: 'place' },
      { x: L.cart.x, z: L.cart.z, label: 'Broken cart', kind: 'place' },
      { x: L.post.x, z: L.post.z, label: 'Watch-post', kind: 'place' },
      { x: L.barrow.x, z: L.barrow.z, label: 'The Barrow', kind: 'place' },
      { x: L.ford.x, z: L.ford.z, label: 'The Low Ford', kind: wardenGone ? 'place' : 'danger' },
      { x: L.gate.x, z: L.gate.z + 4, label: 'North, to the Waystation', kind: 'exit' },
    ],
    ambience: (x, z) => {
      const dawn = stage === 'dawn' || stage === 'exit';
      return {
        wind: 0.55, leaves: 0.35, fire: kit.warmth(x, z),
        water: clamp(1 - Math.abs(z - riverZ(x)) / 26, 0, 1),
        crickets: dawn ? 0.15 : 0.75, owl: dawn ? 0 : 0.6, birds: dawn ? 0.7 : 0,
      };
    },
    debug: () => ({
      stage, stageT, chestOpened, lit: litCount(), wardenHp: warden?.hp ?? null, wardenMax: warden?.maxHp ?? null, wardenMode: ai.mode,
      wardenX: warden?.x ?? null, wardenZ: warden?.z ?? null, pylons: built.pylons.map((p, i) => ({ x: p.x, z: p.z, lit: litPylons[i] })),
      caller: caller ? { x: caller.x, z: caller.z } : null, knight: knight ? { x: knight.x, z: knight.z } : null, checkpoint,
    }),
    frame: (dt) => {
      const t = g.scene.time;
      watchman.update(dt);
      if (!wardenGone) {
        if (warden && warden.alive && warden.state !== 'dying') wardenPos = { x: warden.x, z: warden.z, facing: Math.PI / 2 - warden.facing };
        const wy = Math.max(kit.y(wardenPos.x, wardenPos.z), WATER_Y - 0.25);
        wardenView.glow = clamp(0.3 + litCount() * 0.25, 0, 1);
        wardenView.update(warden && warden.alive ? warden : null, wardenPos.x, wy, wardenPos.z, wardenPos.facing, dt, t);
        if (ai.mode === 'dead') {
          if (deadT < 0) deadT = 0;
          deadT += dt;
          if (deadT > 9) { wardenView.view.root.visible = false; wardenView.light.intensity = 0; wardenGone = true; }
        }
      }
    },
    interactables,
    hooks: {
      bossTick: (e, dt) => (e.tag === 'warden' ? wardenTick(e, dt) : false),
      onKill: (e) => {
        // Pooled creatures are reused: forget them the moment they die.
        if (e.tag === 'warden') { onWardenDown(e); warden = null; }
        if (e.tag === 'caller') { caller = null; toast('world', 'The Grave-Caller is still', { sub: 'The graves have stopped listening.' }); }
        if (e.tag === 'knight') {
          knight = null;
          b?.spawnPickup('item', e.x, e.z, 2, 'ember_shard');
          b?.spawnPickup('item', e.x + 1, e.z - 0.5, 1, 'bone_amulet');
          for (let i = 0; i < 6; i++) b?.spawnPickup('gold', e.x + (Math.random() - 0.5) * 3, e.z + (Math.random() - 0.5) * 3, 3);
        }
      },
      onHitProp: (tag, _id, _school, dmg) => {
        const m = /^pylon:(\d)$/.exec(tag);
        if (!m || stage !== 'boss') return;
        const i = Number(m[1]);
        if (!litPylons[i]) return;
        pylonHp[i] -= dmg;
        if (pylonHp[i] <= 0) snuff(i, 'broken');
      },
    },
    onDeath: () => {
      // The ember is not done with you. Up again where you were last safe.
      if (!b) return true;
      const battle = b;
      setTimeout(() => {
        say('The ember will not let you go so easily.', undefined, 3.5);
        battle.over = null;
        const p = battle.player;
        p.alive = true;
        p.hp = battle.maxHp;
        p.iframes = 3;
        p.x = checkpoint.x; p.z = checkpoint.z;
        clearAround(p.x, p.z, 16);
        g.scene.player?.revive();
        g.scene.cam.snap(p.x, g.scene.heightAt(p.x, p.z), p.z);
        if (warden && warden.alive && stage === 'boss') {
          warden.hp = Math.min(warden.maxHp, warden.hp + warden.maxHp * 0.25);
          warden.x = wardenHome.x; warden.z = wardenHome.z;
          ai.mode = 'walk';
          boss.value = boss.value ? { ...boss.value, channel: null } : null;
        }
      }, 2600);
      return true;
    },
    dispose: () => {
      watchman.dispose();
      wardenView.dispose();
      hint.value = null;
      boss.value = null;
    },
  };
}
