import { describe, it, expect } from 'vitest';
import { Battle } from '@/sim/battle';
import { CollisionWorld, FlowField } from '@/sim/collision';
import { StatBlock } from '@/sim/stats';
import { draft, choose } from '@/sim/levelup';

function baseStats() {
  const s = new StatBlock();
  s.setBase({ maxHealth: 140, regen: 0, armor: 2, moveSpeed: 5, pickupRadius: 2.4, critChance: 0.05, critDamage: 1.5, luck: 1 });
  return s;
}

function arena(seed = 1, weapons = [{ id: 'oathblade', rank: 1 }]) {
  const col = new CollisionWorld(120);
  for (let i = 0; i < 20; i++) col.addCircle(-30 + (i % 5) * 12, -30 + Math.floor(i / 5) * 12, 0.6, { tag: i === 0 ? 'barrel' : undefined });
  return new Battle({
    seed, collision: col, heightAt: () => 0, combat: true, stats: baseStats(), start: { x: 0, z: 0 },
    weapons, ability: 'shield_bash',
  });
}

/** Headless survivor: circles, spawns a ring of the dead, takes every draft. */
function simulate(b: Battle, seconds: number, spawnEvery = 1.2, def = 'risen') {
  const dt = 1 / 60;
  let spawnT = 0;
  for (let t = 0; t < seconds; t += dt) {
    spawnT -= dt;
    if (spawnT <= 0) {
      spawnT = spawnEvery;
      for (let k = 0; k < 3; k++) {
        const a = b.rng.next() * Math.PI * 2;
        b.spawnEnemy(def, b.player.x + Math.cos(a) * 14, b.player.z + Math.sin(a) * 14, { level: 1 + Math.floor(t / 30), style: 'rise' });
      }
    }
    // Drift slowly, the way a player holding ground does, rather than fleeing.
    const mx = Math.cos(t * 0.35) * 0.35, mz = Math.sin(t * 0.35) * 0.35;
    b.tick(dt, mx, mz);
    while (b.pendingLevels > 0) {
      const offers = draft(b, 3);
      choose(b, offers[0]);
    }
    b.events.drain();
    if (b.over) break;
  }
}

describe('battle', () => {
  it('runs a minute of fighting: kills, ember, levels, no NaNs', () => {
    const b = arena(3);
    simulate(b, 60);
    expect(b.player.alive).toBe(true);
    expect(b.killCount).toBeGreaterThan(40);
    expect(b.ember.level).toBeGreaterThan(3);
    for (const e of b.enemies.items) if (e.alive) { expect(Number.isFinite(e.x)).toBe(true); expect(Number.isFinite(e.z)).toBe(true); }
    expect(Number.isFinite(b.player.x)).toBe(true);
  });

  it('every weapon fires and kills something', async () => {
    const { WEAPONS } = await import('@/content/weapons');
    for (const id of Object.keys(WEAPONS)) {
      const b = arena(7, [{ id, rank: 3 }]);
      simulate(b, 20, 0.5);
      expect.soft(b.killCount, `${id} kills`).toBeGreaterThan(3);
    }
  });

  it('every evolution branch applies and still fights', async () => {
    const { WEAPONS } = await import('@/content/weapons');
    for (const w of Object.values(WEAPONS)) {
      for (const evo of w.evolutions) {
        const b = arena(11, [{ id: w.id, rank: 8 }]);
        b.evolve(w.id, evo.id);
        simulate(b, 12, 0.4);
        expect.soft(b.killCount, `${evo.id} kills`).toBeGreaterThan(3);
      }
    }
  });

  it('synergies chain: kindling + pyre burst + emberseekers set off more than one kill per hit', () => {
    const b = arena(5, [{ id: 'cinderfall', rank: 5 }]);
    b.addBoon('kindling');
    b.addBoon('pyre_burst');
    b.addBoon('emberseekers');
    simulate(b, 30, 0.3);
    const counts = Object.fromEntries(b.triggers.map((t) => [t.source, t.count]));
    expect(counts['boon:kindling']).toBeGreaterThan(0);
    expect(counts['boon:pyre_burst']).toBeGreaterThan(0);
    expect(counts['boon:emberseekers']).toBeGreaterThan(0);
  });

  it('a frontal shield turns projectiles, not blades', () => {
    const b = arena(9, []);
    const e = b.spawnEnemy('risen_warrior', 5, 0)!;
    e.facing = Math.PI; // facing the survivor at the origin
    const front = b.hitEnemy(e, 20, 'physical', ['projectile'], { projectile: true, fromX: 1, fromZ: 0, canCrit: false });
    const e2 = b.spawnEnemy('risen_warrior', 5, 3)!;
    e2.facing = Math.PI;
    const melee = b.hitEnemy(e2, 20, 'physical', ['melee'], { canCrit: false });
    expect(front).toBeLessThan(melee * 0.5);
  });

  it('the horde paths around a wall rather than into it', () => {
    const col = new CollisionWorld(60);
    col.addBox(0, 5, 8, 0.5, 0);
    const flow = new FlowField(col, 20);
    flow.update(0, 0);
    // From behind the wall, the path must be longer than the straight line.
    expect(flow.distanceAt(0, 10)).toBeGreaterThan(12);
    const d = { x: 0, z: 0 };
    expect(flow.dir(0, 10, d)).toBe(true);
    expect(Math.abs(d.x)).toBeGreaterThan(0.3);
  });

  it('emits hits, kills and ember pickups for the renderer and the world', () => {
    const b = arena(2);
    let hits = 0, kills = 0, pickups = 0;
    const dt = 1 / 60;
    for (let i = 0; i < 20; i++) b.spawnEnemy('risen', 2 + (i % 5), (i / 5) | 0, { style: 'walk' });
    for (let t = 0; t < 12; t += dt) {
      b.tick(dt, 0.2, 0);
      for (const ev of b.events.drain()) {
        if (ev.t === 'hit') hits++;
        if (ev.t === 'kill') kills++;
        if (ev.t === 'pickup') pickups++;
      }
    }
    expect(hits).toBeGreaterThan(10);
    expect(kills).toBeGreaterThan(5);
    expect(pickups).toBeGreaterThan(3);
  });
});

describe('neutral creatures', () => {
  it('are never hurt by accident, and a pack only turns when it is struck on purpose', () => {
    const b = arena(3, [{ id: 'oathblade', rank: 3 }]);
    const wolf = b.spawnEnemy('wolf', 1.2, 0, { level: 1 })!;
    wolf.disposition = 'neutral';
    const mate = b.spawnEnemy('wolf', 2, 1, { level: 1 })!;
    mate.disposition = 'neutral';
    const hp = wolf.hp;
    // Swings, auras and a shield bash right on top of them.
    for (let i = 0; i < 600; i++) b.tick(1 / 60, 0, 0);
    b.hitEnemy(wolf, 50, 'fire', ['area', 'fire']);
    expect(wolf.hp).toBe(hp);
    expect(wolf.provoked).toBe(false);
    // A deliberate blow starts it, and the pack answers.
    b.hitEnemy(wolf, 5, 'physical', ['physical'], { provoke: true });
    expect(wolf.hp).toBeLessThan(hp);
    expect(mate.provoked).toBe(true);
  });
});
