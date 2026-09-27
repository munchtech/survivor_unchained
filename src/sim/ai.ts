import type { Battle } from './battle';
import type { Enemy } from './entities';
import { TAU } from '@/core/math';

/* How each creature decides what to do this tick.
 *
 * Everything shares one skeleton - statuses, knockback, choosing a target,
 * wanting to be somewhere, not standing inside its neighbours, hitting what
 * it touches - and each behaviour only changes where it wants to be and
 * what it does about it. Targets are not always the survivor: creatures of
 * factions at war go for each other, allies go for whatever threatens you,
 * and something neutral minds its own business until it is hurt. */

export const DIE_TIME = 1.25;
/** Status ticks can kill mid-update; TypeScript cannot see that. */
const isDying = (e: Enemy) => (e.state as string) === 'dying';
const scratch: number[] = [];
const dir = { x: 0, z: 0 };

interface Tgt { x: number; z: number; r: number; enemy: Enemy | null; player: boolean }
const tgt: Tgt = { x: 0, z: 0, r: 0, enemy: null, player: false };

export function updateEnemy(b: Battle, e: Enemy, dt: number) {
  e.animT += dt;
  if (e.flash > 0) e.flash = Math.max(0, e.flash - dt * 11);

  if (e.state === 'dying') {
    e.dieT += dt;
    if (e.dieT >= DIE_TIME) b.enemies.release(e);
    return;
  }
  if (e.lifeT > 0) {
    e.lifeT -= dt;
    if (e.lifeT <= 0) { b.killEnemy(e, false, null); return; }
  }
  b.tickStatus(e, dt);
  if (!e.alive || isDying(e)) return;

  // Knockback slides, then settles.
  if (e.kbx || e.kbz) {
    e.x += e.kbx * dt;
    e.z += e.kbz * dt;
    const k = Math.exp(-dt * 9);
    e.kbx *= k; e.kbz *= k;
    if (Math.abs(e.kbx) + Math.abs(e.kbz) < 0.05) e.kbx = e.kbz = 0;
  }

  const s = e.status;
  if (s.frozen || s.stun || e.state === 'stunned') {
    if (e.state === 'stunned') { e.stateT -= dt; if (e.stateT <= 0) e.state = 'active'; }
    e.vx = e.vz = 0;
    e.anim = 'idle';
    b.collision.resolve(e, e.radius);
    return;
  }

  // Rising from the ground: helpless for a moment. Hit them while they rise.
  if (e.state === 'rising') {
    e.stateT -= dt;
    if (e.stateT <= 0) { e.state = 'active'; e.anim = 'move'; }
    return;
  }

  if (e.boss && b.hooks.bossTick?.(e, dt)) {
    finishMove(b, e, dt);
    return;
  }

  if (e.state === 'burrowed' || e.state === 'surfacing') { tunnel(b, e, dt); return; }

  // Choosing a target.
  e.retargetT -= dt;
  if (e.retargetT <= 0) {
    e.retargetT = 0.45 + b.rng.next() * 0.35;
    e.target = chooseTarget(b, e);
  }
  if (!resolveTarget(b, e)) { idle(b, e, dt); return; }

  const dx = tgt.x - e.x, dz = tgt.z - e.z;
  const dist = Math.hypot(dx, dz) || 0.001;
  const def = e.def;
  let speed = e.speed * slowFactor(e);
  let wantX = dx / dist, wantZ = dz / dist;
  e.facing = Math.atan2(dz, dx);

  // Fear: away from the survivor.
  if (s.fear) {
    const p = b.player;
    const a = Math.atan2(e.z - p.z, e.x - p.x);
    move(b, e, Math.cos(a), Math.sin(a), speed * 1.1, dt);
    return;
  }

  // Charges and lunges: plant, mark the lane, run exactly that lane.
  const lunge = def.charge ?? def.lunge;
  if (lunge) {
    if (e.state === 'windup') {
      e.stateT -= dt;
      e.anim = 'windup';
      e.facing = Math.atan2(e.lungeZ, e.lungeX);
      if (e.stateT <= 0) { e.state = 'lunging'; e.stateT = lunge.time; }
      e.vx = e.vz = 0;
      return;
    }
    if (e.state === 'lunging') {
      e.stateT -= dt;
      e.anim = 'attack';
      e.x += e.lungeX * lunge.speed * dt;
      e.z += e.lungeZ * lunge.speed * dt;
      e.vx = e.lungeX * lunge.speed; e.vz = e.lungeZ * lunge.speed;
      const p = b.player;
      if (tgt.player && Math.hypot(p.x - e.x, p.z - e.z) < e.radius + p.radius + 0.2 && e.attackT <= 0) {
        b.hurtPlayer(e.damage * 1.5, 'physical', def.name, e);
        e.attackT = 0.8;
      } else if (tgt.enemy && Math.hypot(tgt.enemy.x - e.x, tgt.enemy.z - e.z) < e.radius + tgt.enemy.radius + 0.2 && e.attackT <= 0) {
        strike(b, e, tgt.enemy, 1.5);
      }
      e.attackT -= dt;
      // A charge that ends in a tree ends the charger for a while.
      if (b.collision.resolve(e, e.radius)) {
        if (def.charge) {
          e.state = 'stunned';
          e.stateT = 1.8;
          b.events.emit({ t: 'shake', amount: 0.25 });
          b.events.emit({ t: 'bark', x: e.x, z: e.z, text: 'Thud' });
          b.applyStatus(e, { kind: 'stun', chance: 1, power: 1, duration: 1.8 }, 0);
          b.hitEnemy(e, e.maxHp * 0.12, 'physical', ['physical'], { canCrit: false, noProcs: true });
          return;
        }
        e.stateT = 0;
      }
      if (e.stateT <= 0) { e.state = 'recover'; e.stateT = 0.55; }
      return;
    }
    if (e.state === 'recover') {
      e.stateT -= dt;
      e.anim = 'idle';
      e.vx *= 0.8; e.vz *= 0.8;
      if (e.stateT <= 0) { e.state = 'active'; e.rangedT = lunge.cooldown; }
      return;
    }
    e.rangedT -= dt;
    if (e.rangedT <= 0 && dist < lunge.range && dist > 2 && !b.collision.raycast(e.x, e.z, tgt.x, tgt.z, 0.3)) {
      e.state = 'windup';
      e.stateT = lunge.windup;
      e.lungeX = dx / dist; e.lungeZ = dz / dist;
      const reach = lunge.speed * lunge.time;
      b.events.emit({ t: 'telegraph', id: e.id, shape: 'line', x: e.x, z: e.z, x1: e.x + e.lungeX * reach, z1: e.z + e.lungeZ * reach, radius: e.radius, width: e.radius * 2.2, duration: lunge.windup, hostile: e.disposition !== 'ally' });
      e.vx = e.vz = 0;
      return;
    }
  }

  // Casters raise the fallen.
  if (def.raise) {
    if (e.state === 'casting') {
      e.stateT -= dt;
      e.anim = 'cast';
      e.vx = e.vz = 0;
      if (e.stateT <= 0) {
        e.state = 'active';
        let n = 0;
        for (let i = b.graves.length - 1; i >= 0 && n < def.raise.count; i--) {
          const g = b.graves[i];
          if (Math.hypot(g.x - e.x, g.z - e.z) > def.raise.range) continue;
          b.graves.splice(i, 1);
          b.spawnEnemy(def.raise.into, g.x, g.z, { level: e.level, style: 'rise', faction: e.faction });
          n++;
        }
      }
      return;
    }
    e.raiseT -= dt;
    if (e.raiseT <= 0) {
      e.raiseT = def.raise.every;
      const any = b.graves.some((g) => Math.hypot(g.x - e.x, g.z - e.z) < def.raise!.range);
      if (any) {
        e.state = 'casting';
        e.stateT = 1.5;
        b.events.emit({ t: 'telegraph', id: e.id, shape: 'ring', x: e.x, z: e.z, radius: def.raise.range, duration: 1.5, hostile: true });
        b.events.emit({ t: 'bark', x: e.x, z: e.z, text: 'Rise...' });
        return;
      }
    }
  }

  // Where it wants to be.
  switch (def.behavior) {
    case 'pack': {
      // Fan out to a slot around the target, then close together.
      if (dist > 5.5 && tgt.player) {
        const ox = tgt.x + Math.cos(e.slot) * 4, oz = tgt.z + Math.sin(e.slot) * 4;
        const d2 = Math.hypot(ox - e.x, oz - e.z) || 1;
        wantX = (ox - e.x) / d2; wantZ = (oz - e.z) / d2;
        speed *= 1.1;
      }
      break;
    }
    case 'ranged':
    case 'caster': {
      const r = def.ranged?.range ?? 8;
      if (dist < r * 0.55) { wantX = -wantX; wantZ = -wantZ; speed *= 0.9; }
      else if (dist < r * 0.85) {
        // Strafe, so standing and shooting at them is not free.
        const side = e.seed > 0.5 ? 1 : -1;
        wantX = -dz / dist * side * 0.8; wantZ = dx / dist * side * 0.8;
        speed *= 0.6;
      }
      break;
    }
    case 'guard':
      speed *= 0.85;
      break;
    case 'stationary':
      speed = 0;
      break;
    case 'orbit': {
      e.slot += dt * 0.9;
      const ox = tgt.x + Math.cos(e.slot) * 6, oz = tgt.z + Math.sin(e.slot) * 6;
      const d2 = Math.hypot(ox - e.x, oz - e.z) || 1;
      wantX = (ox - e.x) / d2; wantZ = (oz - e.z) / d2;
      break;
    }
    case 'tunneler':
      e.rangedT -= dt;
      if (tgt.player && dist > 6 && e.rangedT <= 0) {
        e.state = 'burrowed';
        e.stateT = 0;
        e.anim = 'burrow';
        b.events.emit({ t: 'spawn', enemy: e.id, x: e.x, z: e.z, def: def.id, style: 'burrow' });
        return;
      }
      break;
    default:
      break;
  }

  // Follow the flow field around obstacles when chasing the survivor.
  if (tgt.player && def.behavior !== 'ranged' && def.behavior !== 'caster' && dist > 1.2) {
    if (b.flow.dir(e.x, e.z, dir)) {
      const flowW = def.behavior === 'pack' && dist > 5.5 ? 0.35 : 0.85;
      wantX = wantX * (1 - flowW) + dir.x * flowW;
      wantZ = wantZ * (1 - flowW) + dir.z * flowW;
      const m = Math.hypot(wantX, wantZ) || 1;
      wantX /= m; wantZ /= m;
    }
  }

  // Ranged attack.
  if (def.ranged) {
    e.rangedT -= dt;
    if (e.rangedT <= 0 && dist < def.ranged.range && !b.collision.raycast(e.x, e.z, tgt.x, tgt.z, 0.1)) {
      shoot(b, e);
      e.rangedT = def.ranged.cooldown * (0.85 + b.rng.next() * 0.3);
    }
  }

  // Trails left behind.
  if (def.trail) {
    e.raiseT -= dt;
    if (e.raiseT <= 0) {
      e.raiseT = def.trail.interval;
      b.spawnZone({ owner: 'enemy', x: e.x, z: e.z, radius: def.trail.radius, life: def.trail.life, dps: e.damage * def.trail.dpsPct, school: def.trail.school, tags: ['zone'], art: 'zone_venom' });
    }
  }

  const reach = e.radius + tgt.r + 0.15;
  if (dist > reach * 0.9) move(b, e, wantX, wantZ, speed, dt);
  else { e.vx *= 0.7; e.vz *= 0.7; e.anim = 'idle'; finishMove(b, e, dt); }

  // Contact.
  e.attackT -= dt;
  if (dist <= reach + 0.25 && e.attackT <= 0) {
    if (tgt.player) b.hurtPlayer(e.damage, 'physical', def.name, e);
    else if (tgt.enemy) strike(b, e, tgt.enemy, 1);
    let every = def.attackEvery ?? 1.0;
    if (e.disposition === 'ally') every /= b.stats.get('summonHaste');
    e.attackT = every;
    e.anim = 'attack';
    e.animT = 0;
  }
}

function slowFactor(e: Enemy) {
  const c = e.status.chill;
  let f = c ? Math.max(0.4, 1 - 0.1 * c.stacks) : 1;
  if (e.status.poison && e.status.poison.stacks >= 5) f *= 0.9;
  return f;
}

function chooseTarget(b: Battle, e: Enemy): number {
  const p = b.player;
  if (e.disposition === 'ally') {
    const t = b.nearestHostile(e.x, e.z, 11);
    // Do not wander off: only fight what is near the survivor.
    if (t && Math.hypot(t.x - p.x, t.z - p.z) < 16) return t.id;
    return -2;
  }
  let best = -2;
  let bd = Infinity;
  const hostileToPlayer = e.disposition === 'hostile' || e.provoked;
  if (hostileToPlayer && p.alive && p.invisibleT <= 0) {
    const d = Math.hypot(p.x - e.x, p.z - e.z);
    const aggro = e.def.aggroRange ?? 60;
    if (d < aggro && (!e.leash || Math.hypot(p.x - e.homeX, p.z - e.homeZ) < e.leash * 1.6)) { best = -1; bd = d * 0.8; }
  }
  // Rivals and the survivor's allies nearby.
  b.spatial.query(e.x, e.z, 9, scratch);
  for (const id of scratch) {
    const o = b.enemies.items[id];
    if (!o.alive || o === e || o.state === 'dying') continue;
    const war = o.disposition === 'ally' ? hostileToPlayer : b.factionsAtWar(e.faction, o.faction);
    if (!war) continue;
    const d = Math.hypot(o.x - e.x, o.z - e.z);
    if (d < bd) { bd = d; best = o.id; }
  }
  return best;
}

function resolveTarget(b: Battle, e: Enemy) {
  if (e.target === -1) {
    const p = b.player;
    if (!p.alive || p.invisibleT > 0) { e.target = -2; return false; }
    tgt.x = p.x; tgt.z = p.z; tgt.r = p.radius; tgt.enemy = null; tgt.player = true;
    return true;
  }
  if (e.target >= 0) {
    const o = b.enemies.items[e.target];
    if (!o.alive || o.state === 'dying' || o.state === 'burrowed') { e.target = -2; e.retargetT = 0; return false; }
    tgt.x = o.x; tgt.z = o.z; tgt.r = o.radius; tgt.enemy = o; tgt.player = false;
    return true;
  }
  return false;
}

/** Nothing to fight: allies heel, neutrals graze, guards go home. */
function idle(b: Battle, e: Enemy, dt: number) {
  const p = b.player;
  if (e.disposition === 'ally') {
    const ox = p.x + Math.cos(e.slot) * 2.4, oz = p.z + Math.sin(e.slot) * 2.4;
    const d = Math.hypot(ox - e.x, oz - e.z);
    if (d > 0.8) move(b, e, (ox - e.x) / d, (oz - e.z) / d, e.speed * Math.min(1.4, d / 3), dt);
    else { e.anim = 'idle'; e.vx = e.vz = 0; }
    return;
  }
  // Home, or a slow wander around it.
  e.stateT -= dt;
  if (e.stateT <= 0) {
    e.stateT = 3 + b.rng.next() * 4;
    const r = e.leash ? e.leash * 0.6 : 5;
    e.lungeX = e.homeX + (b.rng.next() - 0.5) * r;
    e.lungeZ = e.homeZ + (b.rng.next() - 0.5) * r;
  }
  const d = Math.hypot(e.lungeX - e.x, e.lungeZ - e.z);
  if (d > 0.6) {
    move(b, e, (e.lungeX - e.x) / d, (e.lungeZ - e.z) / d, e.speed * 0.35, dt);
    e.facing = Math.atan2(e.lungeZ - e.z, e.lungeX - e.x);
  } else {
    e.vx = e.vz = 0;
    e.anim = 'idle';
    finishMove(b, e, dt);
  }
}

function move(b: Battle, e: Enemy, wx: number, wz: number, speed: number, dt: number) {
  const accel = 1 - Math.exp(-dt * 8);
  e.vx += (wx * speed - e.vx) * accel;
  e.vz += (wz * speed - e.vz) * accel;
  e.x += e.vx * dt;
  e.z += e.vz * dt;
  e.anim = e.anim === 'attack' && e.animT < 0.45 ? 'attack' : 'move';
  finishMove(b, e, dt);
}

/** Keep out of each other, out of the survivor, and out of the walls. */
function finishMove(b: Battle, e: Enemy, _dt: number) {
  b.spatial.query(e.x, e.z, e.radius + 1.0, scratch);
  for (const id of scratch) {
    if (id === e.id) continue;
    const o = b.enemies.items[id];
    if (!o.alive || o.state === 'dying') continue;
    const dx = e.x - o.x, dz = e.z - o.z;
    const min = e.radius + o.radius;
    const d2 = dx * dx + dz * dz;
    if (d2 >= min * min || d2 < 1e-6) continue;
    const d = Math.sqrt(d2);
    const push = (min - d) * (o.mass / (o.mass + e.mass));
    e.x += (dx / d) * push * 0.8;
    e.z += (dz / d) * push * 0.8;
  }
  const p = b.player;
  if (p.alive && e.disposition !== 'ally') {
    const dx = e.x - p.x, dz = e.z - p.z;
    const min = e.radius + p.radius;
    const d2 = dx * dx + dz * dz;
    if (d2 < min * min && d2 > 1e-6) {
      const d = Math.sqrt(d2);
      e.x += (dx / d) * (min - d);
      e.z += (dz / d) * (min - d);
    }
  }
  b.collision.resolve(e, e.radius);
  if (e.leash && e.disposition !== 'ally') {
    const hd = Math.hypot(e.x - e.homeX, e.z - e.homeZ);
    if (hd > e.leash * 1.8) {
      e.target = -2;
      e.retargetT = 1.5;
    }
  }
}

/** One creature striking another. The survivor's allies strike for the
 *  survivor, so their damage runs through the survivor's pipeline. */
function strike(b: Battle, e: Enemy, o: Enemy, mult: number) {
  if (e.disposition === 'ally') {
    b.hitEnemy(o, e.damage * mult, 'physical', ['summon', 'melee', 'physical'], { summon: true, canCrit: true, knockback: 0.3, dirX: Math.cos(e.facing), dirZ: Math.sin(e.facing) });
    return;
  }
  // Rival factions: real damage, no credit, and it draws attention.
  o.hp -= e.damage * mult;
  o.flash = 1;
  b.events.emit({ t: 'hit', x: o.x, z: o.z, amount: e.damage * mult, crit: false, school: 'physical', target: o.id });
  if (o.target !== e.id && b.rng.next() < 0.6) o.target = e.id;
  if (o.hp <= 0) b.killEnemy(o, false, null);
}

function shoot(b: Battle, e: Enemy) {
  const r = e.def.ranged!;
  const p = b.player;
  const tx = tgt.x, tz = tgt.z;
  e.anim = 'attack';
  e.animT = 0;
  const n = r.count ?? 1;
  for (let i = 0; i < n; i++) {
    if (r.lob) {
      // Lead the target a little; lobs are slow.
      const lead = tgt.player ? 0.45 : 0;
      const lx = tx + p.vx * lead + (b.rng.next() - 0.5) * 1.2;
      const lz = tz + p.vz * lead + (b.rng.next() - 0.5) * 1.2;
      const d = Math.hypot(lx - e.x, lz - e.z);
      const life = Math.max(0.5, d / r.speed);
      const pr = b.spawnProjectile({
        owner: 'enemy', ownerId: e.id, x: e.x, z: e.z, y: 1, vx: (lx - e.x) / life, vz: (lz - e.z) / life, speed: r.speed,
        damage: e.damage * (r.damagePct ?? 1), school: r.school, radius: 0.3, life, lob: true, art: r.art ?? 'firepot',
        groundOnHit: r.zone ? { radius: r.zone.radius, duration: r.zone.duration, dpsPct: r.zone.dpsPct } : null,
      });
      if (pr) {
        pr.landX = lx; pr.landZ = lz;
        b.events.emit({ t: 'telegraph', id: pr.id, shape: 'circle', x: lx, z: lz, radius: 1.6, duration: life, hostile: true });
      }
    } else {
      const a = Math.atan2(tz - e.z, tx - e.x) + (i - (n - 1) / 2) * (r.spread ?? 0.15);
      b.spawnProjectile({
        owner: 'enemy', ownerId: e.id, x: e.x + Math.cos(a) * 0.5, z: e.z + Math.sin(a) * 0.5, y: 1.1,
        vx: Math.cos(a) * r.speed, vz: Math.sin(a) * r.speed, speed: r.speed,
        damage: e.damage * (r.damagePct ?? 1), school: r.school, radius: 0.28, life: (r.range * 1.3) / r.speed,
        art: r.art ?? 'bolt_enemy',
        status: r.slow ? { kind: 'chill', chance: 1, power: 1, duration: r.slow.duration } : null,
      });
    }
  }
}

/** Lamplings: under the ground, then up beside you. */
function tunnel(b: Battle, e: Enemy, dt: number) {
  const p = b.player;
  if (e.state === 'burrowed') {
    e.anim = 'burrow';
    const dx = p.x - e.x, dz = p.z - e.z;
    const d = Math.hypot(dx, dz) || 1;
    const sp = e.speed * 1.8;
    e.x += (dx / d) * sp * dt;
    e.z += (dz / d) * sp * dt;
    b.collision.resolve(e, e.radius);
    e.stateT += dt;
    if (d < 2.4 || e.stateT > 6) {
      e.state = 'surfacing';
      e.stateT = 0.55;
      b.events.emit({ t: 'telegraph', id: e.id, shape: 'circle', x: e.x, z: e.z, radius: 1.1, duration: 0.55, hostile: true });
    }
    return;
  }
  e.stateT -= dt;
  if (e.stateT <= 0) {
    e.state = 'active';
    e.anim = 'attack';
    e.animT = 0;
    e.rangedT = 4 + b.rng.next() * 3;
    if (Math.hypot(p.x - e.x, p.z - e.z) < 1.3) b.hurtPlayer(e.damage * 1.2, 'physical', e.def.name, e);
    b.events.emit({ t: 'spawn', enemy: e.id, x: e.x, z: e.z, def: e.def.id, style: 'rise' });
  }
}

export const _TAU = TAU;
