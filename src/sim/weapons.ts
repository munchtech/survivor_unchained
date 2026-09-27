import { WEAPONS, RANK, type WeaponDef, type WeaponStats, type Evolution, type WeaponBehavior } from '@/content/weapons';
import type { Battle } from './battle';
import type { Enemy } from './entities';
import type { School, Tag } from './types';
import { TAU } from '@/core/math';

/* A weapon in the hand: its definition, how far it has been ranked, what it
 * evolved into, and the behaviour that turns all of that into things on the
 * field. Nothing here aims or fires on input - the survivor's whole job is
 * where they stand. */

export interface WeaponInst {
  id: string;
  def: WeaponDef;
  rank: number;
  evolution: Evolution | null;
  timer: number;
  /** Mods from discoveries and items: multipliers and additions. */
  mods: { damage: number; area: number; cooldown: number; projectiles: number; pierce: number; speed: number; duration: number; homing: number };
  /** Burst shots still to go, and when. */
  burstLeft: number;
  burstT: number;
  burstTarget: number;
  /** Statistics for the damage meter and for ember mastery. */
  damageDealt: number;
  kills: number;
  slot: number;
  /** For beams and orbits: active until. */
  activeT: number;
  swing: number;
}

export function makeWeapon(id: string, rank: number, slot: number): WeaponInst {
  const def = WEAPONS[id];
  if (!def) throw new Error(`unknown weapon ${id}`);
  return {
    id, def, rank, evolution: null, timer: 0.4 + slot * 0.17,
    mods: { damage: 1, area: 1, cooldown: 1, projectiles: 0, pierce: 0, speed: 1, duration: 1, homing: 0 },
    burstLeft: 0, burstT: 0, burstTarget: -2, damageDealt: 0, kills: 0, slot, activeT: 0, swing: 0,
  };
}

/* ------------------------------------------------------------ derivation -- */

export function behaviorOf(w: WeaponInst): WeaponBehavior {
  return w.evolution?.behavior ?? w.def.behavior;
}
export function schoolOf(w: WeaponInst): School {
  return w.evolution?.school ?? w.def.school;
}
export function tagsOf(w: WeaponInst): Tag[] {
  const t = [...w.def.tags];
  if (w.evolution?.addTags) for (const a of w.evolution.addTags) if (!t.includes(a)) t.push(a);
  const s = schoolOf(w);
  if (!t.includes(s)) t.push(s);
  return t;
}
export function statOf<K extends keyof WeaponStats>(w: WeaponInst, k: K): WeaponStats[K] {
  const set = w.evolution?.set;
  if (set && set[k] !== undefined) return set[k];
  return w.def.base[k];
}
export function artOf(w: WeaponInst) { return w.evolution?.art ?? w.def.art; }

export function damageOf(b: Battle, w: WeaponInst) {
  let d = w.def.base.damage * (1 + RANK.damageStep * (w.rank - 1)) * w.mods.damage;
  if (w.evolution) d *= w.evolution.mods.damage ?? 1;
  return d;
  void b;
}

export function cooldownOf(b: Battle, w: WeaponInst) {
  let c = w.def.base.cooldown * b.stats.get('cooldown') * w.mods.cooldown;
  if (w.evolution) c *= w.evolution.mods.cooldown ?? 1;
  return Math.max(0.08, Math.min(20, c));
}

export function areaOf(b: Battle, w: WeaponInst, base: number) {
  let a = base * b.stats.get('area') * (1 + RANK.areaStep * (w.rank - 1)) * w.mods.area;
  if (w.evolution) a *= w.evolution.mods.area ?? 1;
  return a;
}

export function durationOf(b: Battle, w: WeaponInst, base: number) {
  let d = base * b.stats.get('duration') * (1 + RANK.durationStep * (w.rank - 1)) * w.mods.duration;
  if (w.evolution) d *= w.evolution.mods.duration ?? 1;
  return d;
}

export function countOf(b: Battle, w: WeaponInst, base = w.def.base.projectiles ?? 1) {
  let n = base;
  if (w.rank >= RANK.projRankA) n++;
  if (w.rank >= RANK.projRankB) n++;
  n += Math.round(b.stats.get('projectiles')) + w.mods.projectiles;
  if (w.evolution) n += w.evolution.mods.projectiles ?? 0;
  return Math.max(1, n);
}

export function speedOf(b: Battle, w: WeaponInst) {
  let s = (w.def.base.speed ?? 9) * b.stats.get('projectileSpeed') * w.mods.speed;
  if (w.evolution) s *= w.evolution.mods.speed ?? 1;
  return s;
}

function pierceOf(b: Battle, w: WeaponInst) {
  return (statOf(w, 'pierce') ?? 0) + Math.round(b.stats.get('pierce')) + w.mods.pierce + (w.evolution?.mods.pierce ?? 0);
}

/* ------------------------------------------------------------- firing -- */

export function tickWeapon(b: Battle, w: WeaponInst, dt: number) {
  w.timer -= dt;
  if (w.burstLeft > 0) {
    w.burstT -= dt;
    if (w.burstT <= 0) {
      w.burstLeft--;
      w.burstT = 0.07;
      fireAimedOne(b, w, w.burstTarget);
    }
  }
  if (w.timer > 0) return;
  const fired = fire(b, w);
  // Nothing in range: look again soon rather than waiting a whole cooldown.
  w.timer = fired ? cooldownOf(b, w) : 0.25;
  if (fired) b.onWeaponFired(w);
}

function fire(b: Battle, w: WeaponInst): boolean {
  switch (behaviorOf(w)) {
    case 'aimed': return fireAimed(b, w);
    case 'spray': return fireSpray(b, w);
    case 'ring': return fireRing(b, w);
    case 'nova': return fireNova(b, w);
    case 'zone': return fireZone(b, w);
    case 'chain': return fireChain(b, w);
    case 'orbit': return fireOrbit(b, w);
    case 'storm': return fireStorm(b, w);
    case 'bounce': return fireBounce(b, w);
    case 'beam': return fireBeam(b, w);
    case 'palm': return firePalm(b, w);
    case 'herd': return fireHerd(b, w);
    case 'chakram': return fireChakram(b, w);
    case 'slash': return fireSlash(b, w);
  }
  return false;
}

function range(w: WeaponInst) { return statOf(w, 'range') ?? 14; }

function fireAimed(b: Battle, w: WeaponInst) {
  const target = b.nearestHostile(b.player.x, b.player.z, range(w));
  if (!target) return false;
  const n = countOf(b, w);
  if (statOf(w, 'burst')) {
    w.burstLeft = n - 1;
    w.burstT = 0.07;
    w.burstTarget = target.id;
    fireAimedOne(b, w, target.id);
  } else {
    for (let i = 0; i < n; i++) fireAimedOne(b, w, target.id, (i - (n - 1) / 2) * 0.14);
  }
  return true;
}

function fireAimedOne(b: Battle, w: WeaponInst, targetId: number, angleOffset = 0) {
  const p = b.player;
  let t: Enemy | null = b.enemies.items[targetId];
  if (!t || !t.alive || t.state === 'dying') t = b.nearestHostile(p.x, p.z, range(w));
  if (!t) return;
  const homing = statOf(w, 'homing') ?? 0;
  const a = Math.atan2(t.z - p.z, t.x - p.x) + angleOffset + (homing ? (b.rng.next() - 0.5) * 0.9 : 0);
  launch(b, w, a, { target: t.id });
}

interface LaunchOpts { target?: number; x?: number; z?: number; speedMul?: number; life?: number; chakram?: boolean; herd?: boolean }

function launch(b: Battle, w: WeaponInst, angle: number, o: LaunchOpts = {}) {
  const p = b.player;
  const sp = speedOf(b, w) * (o.speedMul ?? 1);
  const pr = b.spawnProjectile({
    owner: 'player', x: o.x ?? p.x + Math.cos(angle) * 0.5, z: o.z ?? p.z + Math.sin(angle) * 0.5, y: 1.1,
    vx: Math.cos(angle) * sp, vz: Math.sin(angle) * sp, speed: sp,
    damage: damageOf(b, w), school: schoolOf(w), tags: tagsOf(w),
    radius: (statOf(w, 'radius') ?? 0.2) * Math.sqrt(b.stats.get('area')), pierce: pierceOf(b, w),
    bounces: (statOf(w, 'bounces') ?? 0) + (w.evolution?.mods.bounces ?? 0),
    life: o.life ?? durationOf(b, w, statOf(w, 'life') ?? 2.0) / (1 + RANK.durationStep * (w.rank - 1)),
    homing: (statOf(w, 'homing') ?? 0) + w.mods.homing, target: o.target ?? -2, weapon: w.id, art: artOf(w),
    status: statOf(w, 'status') ?? null, splash: statOf(w, 'splash') ? areaOf(b, w, statOf(w, 'splash')!) : 0,
    splitOnHit: statOf(w, 'splitOnHit') ?? 0, heal: statOf(w, 'heal') ?? 0,
    knockback: statOf(w, 'knockback') ?? 0, chakram: !!o.chakram, groundOnHit: statOf(w, 'groundOnHit') ?? null,
    rank: w.rank, bossDamage: w.def.bossDamage ?? 1,
  });
  if (pr && o.herd) pr.rehit = 0.6;
  b.events.emit({ t: 'muzzle', x: p.x, z: p.z, angle, school: schoolOf(w), weapon: w.id });
  return pr;
}

function fireSpray(b: Battle, w: WeaponInst) {
  const p = b.player;
  const t = b.nearestHostile(p.x, p.z, range(w));
  if (!t) return false;
  const n = countOf(b, w);
  const spread = statOf(w, 'spread') ?? 0.16;
  const a0 = Math.atan2(t.z - p.z, t.x - p.x);
  for (let i = 0; i < n; i++) launch(b, w, a0 + (i - (n - 1) / 2) * spread, { target: t.id });
  // Arrowfall: the volley also rains on the densest knot of the crowd.
  const strikes = statOf(w, 'strikes');
  if (strikes) stormAt(b, w, strikes, statOf(w, 'stormRadius') ?? 5, 1.3, damageOf(b, w) * 0.6);
  return true;
}

function fireRing(b: Battle, w: WeaponInst) {
  if (!b.nearestHostile(b.player.x, b.player.z, 9)) return false;
  const n = countOf(b, w);
  const rot = b.time * 1.7;
  for (let i = 0; i < n; i++) launch(b, w, rot + (i / n) * TAU);
  return true;
}

function fireNova(b: Battle, w: WeaponInst) {
  const p = b.player;
  const r = areaOf(b, w, statOf(w, 'radius') ?? 3.5);
  if (!b.nearestHostile(p.x, p.z, r + 1)) return false;
  const rings = 1 + (w.rank >= RANK.projRankA ? 1 : 0) + (w.rank >= RANK.projRankB ? 1 : 0);
  b.events.emit({ t: 'nova', x: p.x, z: p.z, radius: r, school: schoolOf(w), duration: statOf(w, 'expandTime') ?? 0.35, rings });
  const dmg = damageOf(b, w);
  const kb = statOf(w, 'knockback') ?? 0;
  const heal = statOf(w, 'heal') ?? 0;
  let hitAny = false;
  b.forEachHostileInRadius(p.x, p.z, r, (e, d) => {
    hitAny = true;
    // The ring reaches the far edge a moment after the near one.
    b.hitEnemy(e, dmg, schoolOf(w), tagsOf(w), {
      weapon: w, knockback: kb, dirX: (e.x - p.x) / (d || 1), dirZ: (e.z - p.z) / (d || 1),
      status: statOf(w, 'status') ?? null, bossDamage: w.def.bossDamage,
    });
  });
  if (heal && hitAny) b.healPlayer(heal, 'weapon');
  const g = statOf(w, 'groundOnHit');
  if (g) b.spawnZone({ owner: 'player', x: p.x, z: p.z, radius: areaOf(b, w, g.radius), life: durationOf(b, w, g.duration), dps: dmg * g.dpsPct, school: schoolOf(w), tags: tagsOf(w), art: artOf(w) + '_ground', weapon: w.id });
  return true;
}

function fireZone(b: Battle, w: WeaponInst) {
  const p = b.player;
  const r = areaOf(b, w, statOf(w, 'radius') ?? 3);
  let x = p.x, z = p.z;
  if (statOf(w, 'atTarget')) {
    const t = b.densestHostile(p.x, p.z, 11, r);
    if (!t) return false;
    x = t.x; z = t.z;
  } else if (!b.nearestHostile(p.x, p.z, r + 2)) return false;
  const tick = statOf(w, 'tickRate') ?? 0.5;
  b.spawnZone({
    owner: 'player', x, z, radius: r, life: durationOf(b, w, statOf(w, 'duration') ?? 4), dps: damageOf(b, w) / tick,
    tick, school: schoolOf(w), tags: tagsOf(w), slow: statOf(w, 'slow') ?? 0, status: statOf(w, 'status') ?? null,
    art: artOf(w), weapon: w.id, follow: !statOf(w, 'atTarget'), armor: w.evolution?.id === 'sanctified_earth' ? 6 : 0,
    bossDamage: w.def.bossDamage ?? 1,
  });
  return true;
}

function fireChain(b: Battle, w: WeaponInst) {
  const p = b.player;
  const first = b.nearestHostile(p.x, p.z, range(w));
  if (!first) return false;
  const jumps = countOf(b, w, (statOf(w, 'chains') ?? 5) - 1) + (w.evolution?.mods.chains ?? 0);
  const reach = areaOf(b, w, statOf(w, 'chainRange') ?? 6);
  const fork = !!statOf(w, 'fork');
  const skybreak = w.evolution?.id === 'skybreak';
  chainFrom(b, p.x, p.z, first, jumps, reach, damageOf(b, w), schoolOf(w), tagsOf(w), w, fork, skybreak);
  return true;
}

export function chainFrom(b: Battle, x0: number, z0: number, first: Enemy, jumps: number, reach: number, dmg: number,
  school: School, tags: readonly Tag[], w: WeaponInst | null, fork = false, sky = false, depth = 0) {
  const hit = new Set<number>();
  const points: number[] = [x0, z0];
  let cur: Enemy | null = first;
  const queue: Enemy[] = [];
  for (let j = 0; j <= jumps && cur; j++) {
    hit.add(cur.id);
    points.push(cur.x, cur.z);
    b.hitEnemy(cur, dmg * Math.pow(0.92, j), school, tags, {
      weapon: w ?? undefined, status: w ? statOf(w, 'status') ?? null : null, depth, bossDamage: w?.def.bossDamage,
    });
    if (sky) b.events.emit({ t: 'strike', x: cur.x, z: cur.z, radius: 0.9, school, delay: 0 });
    const next = b.nearestHostile(cur.x, cur.z, reach, (e) => !hit.has(e.id));
    if (fork && next && j < jumps - 1) {
      const second = b.nearestHostile(cur.x, cur.z, reach, (e) => !hit.has(e.id) && e.id !== next.id);
      if (second) queue.push(second);
    }
    cur = next;
  }
  b.events.emit({ t: 'chain', points, school });
  // Forks run a shorter chain of their own from where they split.
  for (const f of queue.slice(0, 3)) {
    if (hit.has(f.id)) continue;
    const pts = [points[points.length - 2], points[points.length - 1], f.x, f.z];
    b.hitEnemy(f, dmg * 0.7, school, tags, { weapon: w ?? undefined, depth });
    b.events.emit({ t: 'chain', points: pts, school });
  }
}

function fireOrbit(b: Battle, w: WeaponInst) {
  // Only one gyre at a time: the next begins when the last one ends.
  if (b.time < w.activeT) return false;
  if (!b.nearestHostile(b.player.x, b.player.z, 10)) return false;
  const n = countOf(b, w);
  const life = durationOf(b, w, statOf(w, 'duration') ?? 3);
  const radius = areaOf(b, w, statOf(w, 'orbitRadius') ?? 2);
  const speed = statOf(w, 'orbitSpeed') ?? 4;
  for (let i = 0; i < n; i++) {
    const pr = b.spawnProjectile({
      owner: 'player', x: b.player.x, z: b.player.z, y: 1, vx: 0, vz: 0, speed: 0,
      damage: damageOf(b, w), school: schoolOf(w), tags: tagsOf(w), radius: (statOf(w, 'radius') ?? 0.5) * Math.sqrt(b.stats.get('area')),
      pierce: 999, bounces: 0, life, homing: 0, target: -2, weapon: w.id, art: artOf(w), status: statOf(w, 'status') ?? null,
      splash: 0, splitOnHit: 0, heal: 0, knockback: 0.25, chakram: false, groundOnHit: null, rank: w.rank, bossDamage: w.def.bossDamage ?? 1,
    });
    if (!pr) continue;
    pr.orbitR = radius;
    pr.orbitW = speed;
    pr.orbitA = (i / n) * TAU;
    pr.rehit = 0.45;
    pr.slotId = w.slot;
  }
  w.activeT = b.time + life;
  return true;
}

function stormAt(b: Battle, w: WeaponInst, strikes: number, area: number, splash: number, dmg: number) {
  const p = b.player;
  const targets = b.hostilesInRadius(p.x, p.z, area * b.stats.get('area') + 3);
  if (!targets.length) return false;
  for (let i = 0; i < strikes; i++) {
    const t = targets[b.rng.int(0, targets.length - 1)];
    const x = t.x + (b.rng.next() - 0.5) * 1.2, z = t.z + (b.rng.next() - 0.5) * 1.2;
    b.scheduleStrike(x, z, areaOf(b, w, splash), dmg, schoolOf(w), tagsOf(w), 0.28 + i * 0.05, w);
  }
  return true;
}

function fireStorm(b: Battle, w: WeaponInst) {
  const strikes = (statOf(w, 'strikes') ?? 5) + (w.evolution?.mods.strikes ?? 0) + Math.round(b.stats.get('projectiles'));
  return stormAt(b, w, strikes, statOf(w, 'stormRadius') ?? 6, statOf(w, 'splash') ?? 1.5, damageOf(b, w));
}

function fireBounce(b: Battle, w: WeaponInst) {
  const p = b.player;
  const t = b.nearestHostile(p.x, p.z, range(w));
  if (!t) return false;
  const n = countOf(b, w);
  const a0 = Math.atan2(t.z - p.z, t.x - p.x);
  for (let i = 0; i < n; i++) {
    const pr = launch(b, w, a0 + (i - (n - 1) / 2) * 0.3, { target: t.id });
    if (pr) pr.homing = 7;
  }
  return true;
}

function fireBeam(b: Battle, w: WeaponInst) {
  const p = b.player;
  const t = b.nearestHostile(p.x, p.z, range(w));
  if (!t) return false;
  const a = Math.atan2(t.z - p.z, t.x - p.x);
  const len = range(w) * (1 + 0.04 * (w.rank - 1));
  const width = areaOf(b, w, statOf(w, 'beamWidth') ?? 0.6);
  const x1 = p.x + Math.cos(a) * len, z1 = p.z + Math.sin(a) * len;
  b.events.emit({ t: 'beam', x0: p.x, z0: p.z, x1, z1, width, school: schoolOf(w), duration: 0.35 });
  const dmg = damageOf(b, w);
  b.forEachHostileNearSegment(p.x, p.z, x1, z1, width, (e) => {
    b.hitEnemy(e, dmg, schoolOf(w), tagsOf(w), { weapon: w, status: statOf(w, 'status') ?? null, bossDamage: w.def.bossDamage });
  });
  return true;
}

function firePalm(b: Battle, w: WeaponInst) {
  const p = b.player;
  const reach = areaOf(b, w, statOf(w, 'reach') ?? 2.9);
  const targets = b.hostilesInRadius(p.x, p.z, reach + 0.6);
  if (!targets.length) return false;
  targets.sort((a, c) => (a.x - p.x) ** 2 + (a.z - p.z) ** 2 - ((c.x - p.x) ** 2 + (c.z - p.z) ** 2));
  const n = countOf(b, w);
  const arc = statOf(w, 'arc') ?? 1.25;
  for (let i = 0; i < n; i++) {
    const t = targets[i % targets.length];
    const a = Math.atan2(t.z - p.z, t.x - p.x) + (i >= targets.length ? (i - targets.length + 1) * 0.6 : 0);
    coneHit(b, w, a, arc, reach, damageOf(b, w));
  }
  return true;
}

function coneHit(b: Battle, w: WeaponInst, a: number, arc: number, reach: number, dmg: number) {
  const p = b.player;
  b.events.emit({ t: 'slash', x: p.x, z: p.z, angle: a, arc, reach, school: schoolOf(w) });
  const kb = statOf(w, 'knockback') ?? 0;
  let any = false;
  b.forEachHostileInRadius(p.x, p.z, reach, (e, d) => {
    let da = Math.atan2(e.z - p.z, e.x - p.x) - a;
    da = Math.atan2(Math.sin(da), Math.cos(da));
    if (Math.abs(da) > arc / 2 + Math.atan2(e.radius, Math.max(d, 0.1))) return;
    any = true;
    b.hitEnemy(e, dmg, schoolOf(w), tagsOf(w), {
      weapon: w, knockback: kb, dirX: (e.x - p.x) / (d || 1), dirZ: (e.z - p.z) / (d || 1),
      status: statOf(w, 'status') ?? null, bossDamage: w.def.bossDamage,
    });
  });
  return any;
}

function fireSlash(b: Battle, w: WeaponInst) {
  const p = b.player;
  const reach = areaOf(b, w, statOf(w, 'reach') ?? 2.6);
  const t = b.nearestHostile(p.x, p.z, reach + 1.2);
  if (!t) return false;
  const a = Math.atan2(t.z - p.z, t.x - p.x);
  const arc = statOf(w, 'arc') ?? 2.2;
  const n = countOf(b, w, 1);
  for (let i = 0; i < n; i++) {
    const ai = a + (i === 0 ? 0 : (i % 2 ? 1 : -1) * Math.ceil(i / 2) * arc * 0.85);
    coneHit(b, w, ai, arc, reach, damageOf(b, w));
  }
  // Blades hit things as well as creatures: barrels, brambles, a boss's lamps.
  for (const c of b.collision.within(p.x, p.z, reach)) {
    if (!c.tag) continue;
    let da = Math.atan2(c.z - p.z, c.x - p.x) - a;
    da = Math.atan2(Math.sin(da), Math.cos(da));
    if (Math.abs(da) <= arc / 2 + 0.3) b.hooks.onHitProp?.(c.tag, c.id, schoolOf(w), damageOf(b, w), c.x, c.z);
  }
  w.swing++;
  b.player.attackAnim = { weapon: w.id, angle: a, t: b.time, heavy: arc > 3 };
  // Oathkeeper: every swing throws a crescent onward.
  if (w.evolution?.id === 'oathkeeper') {
    const pr = launch(b, w, a, { speedMul: 1, life: 0.9 });
    if (pr) { pr.pierce = 99; pr.radius = 1.1; pr.art = 'crescent_holy'; pr.school = 'holy'; }
  }
  if (w.evolution?.id === 'bonesplitter') {
    b.scheduleStrike(p.x + Math.cos(a) * reach * 1.4, p.z + Math.sin(a) * reach * 1.4, 1.8, damageOf(b, w) * 0.8, 'physical', tagsOf(w), 0.12, w);
  }
  return true;
}

function fireHerd(b: Battle, w: WeaponInst) {
  const p = b.player;
  const t = b.nearestHostile(p.x, p.z, range(w));
  if (!t) return false;
  const n = countOf(b, w);
  const a = Math.atan2(t.z - p.z, t.x - p.x);
  for (let i = 0; i < n; i++) {
    const off = (i - (n - 1) / 2) * 1.1;
    const sx = p.x - Math.cos(a) * 3 + Math.cos(a + Math.PI / 2) * off;
    const sz = p.z - Math.sin(a) * 3 + Math.sin(a + Math.PI / 2) * off;
    launch(b, w, a, { x: sx, z: sz, herd: true, life: durationOf(b, w, statOf(w, 'life') ?? 1.8) });
  }
  return true;
}

function fireChakram(b: Battle, w: WeaponInst) {
  const p = b.player;
  const t = b.nearestHostile(p.x, p.z, range(w) + 2);
  if (!t) return false;
  const n = countOf(b, w);
  const a0 = Math.atan2(t.z - p.z, t.x - p.x);
  for (let i = 0; i < n; i++) {
    const pr = launch(b, w, a0 + (i - (n - 1) / 2) * 0.5, { chakram: true, life: durationOf(b, w, statOf(w, 'life') ?? 2.6) });
    if (pr) { pr.pierce = 999; pr.rehit = 0.5; }
  }
  return true;
}

/** What a weapon card should say it does at a rank. */
export function describeRank(b: Battle, w: WeaponInst) {
  return {
    damage: Math.round(damageOf(b, w) * b.stats.damageMult(schoolOf(w), tagsOf(w))),
    cooldown: cooldownOf(b, w),
    count: countOf(b, w),
  };
}
