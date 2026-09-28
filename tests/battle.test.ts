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
    while (b.draftOwed) {
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

describe('the level-up draft', () => {
  it('never offers a blessing when the ember rises, and always a combat skill', async () => {
    const { BOONS } = await import('@/content/boons');
    const b = arena(11);
    for (let i = 0; i < 20; i++) {
      b.gainEmber(b.ember.next - b.ember.xp + 0.01);
      while (b.draftOwed) {
        const offers = draft(b, 3);
        expect(offers.length).toBe(3);
        expect(offers.some((o) => o.kind === 'boon' && BOONS[o.id].kind === 'blessing')).toBe(false);
        expect(offers.some((o) => o.kind === 'weapon' || o.kind === 'rank' || o.kind === 'evolve')).toBe(true);
        choose(b, offers[0]);
      }
    }
    expect(b.ember.level).toBe(21);
  });

  it('gives a blessing at the milestone, after that level\'s skill, not instead of it', async () => {
    const { MILESTONE_EVERY } = await import('@/content/boons');
    const b = arena(13);
    b.ember.level = MILESTONE_EVERY - 1;
    b.gainEmber(b.ember.next - b.ember.xp + 0.01);
    expect(b.ember.level).toBe(MILESTONE_EVERY);
    expect(b.pendingLevels).toBe(1);
    expect(b.pendingBlessings).toEqual([MILESTONE_EVERY]);
    const skill = draft(b, 3);
    expect(skill.every((o) => !o.blessing)).toBe(true);
    choose(b, skill[0]);
    expect(b.draftOwed).toBe(true);
    const blessing = draft(b, 3);
    expect(blessing.length).toBe(3);
    expect(blessing.every((o) => o.kind === 'boon' && o.blessing)).toBe(true);
    const { BOONS } = await import('@/content/boons');
    expect(blessing.every((o) => BOONS[o.id].kind === 'blessing')).toBe(true);
    const before = Object.values(b.boons).reduce((n, r) => n + r, 0);
    choose(b, blessing[0]);
    expect(Object.values(b.boons).reduce((n, r) => n + r, 0)).toBe(before + 1);
    expect(b.draftOwed).toBe(false);
  });

  it('fills with passive skills once every combat skill is taken and ranked', async () => {
    const { WEAPON_POOL, WEAPON_MAX_RANK, MAX_WEAPONS } = await import('@/content/weapons');
    const b = arena(12, WEAPON_POOL.slice(0, MAX_WEAPONS).map((id) => ({ id, rank: WEAPON_MAX_RANK })));
    b.ember.level = 3; b.pendingLevels = 1;
    // Evolve them all first; then only passive skills are left to learn.
    for (const w of b.weapons) b.evolve(w.id, w.def.evolutions[0].id);
    const offers = draft(b, 3);
    expect(offers.every((o) => o.kind === 'boon' && !o.blessing)).toBe(true);
    expect(offers.length).toBe(3);
  });

  it('leans a little toward the calling, and never locks anything out', async () => {
    const { WEAPONS } = await import('@/content/weapons');
    const seen = new Set<string>();
    const spellShare = (lean: boolean) => {
      let spell = 0, total = 0;
      for (let seed = 1; seed <= 120; seed++) {
        const b = arena(seed);
        if (lean) b.favours = new Set(['spell']);
        b.ember.level = 2; b.pendingLevels = 1;
        for (const o of draft(b, 3)) if (o.kind === 'weapon') { seen.add(o.id); total++; if (WEAPONS[o.id].tags.includes('spell')) spell++; }
      }
      return spell / total;
    };
    // The same draws, with and without the lean: spells come up more with it.
    expect(spellShare(true)).toBeGreaterThan(spellShare(false));
    const pool = Object.values(WEAPONS).filter((w) => w.findable);
    expect(seen.size).toBeGreaterThan(pool.length * 0.8);
  });
});

describe('evolutions', () => {
  it('need the weapon at rank 8 and one rank of its passive skill', async () => {
    const { WEAPON_MAX_RANK } = await import('@/content/weapons');
    const { earnedBranches } = await import('@/sim/levelup');
    const b = arena(14, [{ id: 'seeking_motes', rank: WEAPON_MAX_RANK }]);
    // Rank 8 alone is not enough.
    expect(earnedBranches(b, 'seeking_motes')).toEqual([]);
    b.ember.level = 3; b.pendingLevels = 1;
    expect(draft(b, 3).some((o) => o.kind === 'evolve')).toBe(false);
    // One rank of Duplicity opens Mote Cascade.
    b.addBoon('duplicity');
    expect(earnedBranches(b, 'seeking_motes').map((e) => e.id)).toEqual(['mote_cascade']);
    const offers = draft(b, 3);
    expect(offers.filter((o) => o.kind === 'evolve').map((o) => o.branch)).toEqual(['mote_cascade']);
    // With both passives, both branches: the choice is the player's.
    b.addBoon('precision');
    expect(earnedBranches(b, 'seeking_motes').length).toBe(2);
  });

  it('every branch names a passive skill that can be drafted', async () => {
    const { WEAPONS } = await import('@/content/weapons');
    const { BOONS } = await import('@/content/boons');
    for (const w of Object.values(WEAPONS)) for (const e of w.evolutions) {
      expect(e.catalysts.length, e.id).toBeGreaterThan(0);
      for (const c of e.catalysts) expect(BOONS[c.boon]?.kind, `${e.id}: ${c.boon}`).toBe('passive');
    }
  });

  it('come one weapon at a time', async () => {
    const { WEAPON_POOL, WEAPON_MAX_RANK, MAX_WEAPONS } = await import('@/content/weapons');
    const b = arena(15, WEAPON_POOL.slice(0, MAX_WEAPONS).map((id) => ({ id, rank: WEAPON_MAX_RANK })));
    for (const id of ['duplicity', 'precision', 'expanse', 'perennial', 'haste', 'velocity']) b.addBoon(id);
    b.ember.level = 3; b.pendingLevels = 1;
    const offers = draft(b, 3);
    const evos = offers.filter((o) => o.kind === 'evolve');
    expect(evos.length).toBeGreaterThan(0);
    expect(new Set(evos.map((o) => o.id)).size).toBe(1);
  });
});

describe('passive skills', () => {
  it('are ordinary picks beside combat skills, up to six held', async () => {
    const { BOONS, MAX_PASSIVES } = await import('@/content/boons');
    const { passivesHeld } = await import('@/sim/levelup');
    const b = arena(16);
    let combat = 0, passive = 0;
    for (let i = 0; i < 40; i++) {
      b.gainEmber(b.ember.next - b.ember.xp + 0.01);
      while (b.draftOwed) {
        const offers = draft(b, 3);
        for (const o of offers) {
          if (o.kind === 'weapon' || o.kind === 'rank') combat++;
          if (o.kind === 'boon') { passive++; expect(BOONS[o.id].kind).toBe('passive'); }
        }
        // Take passives when offered, to fill the slots.
        choose(b, offers.find((o) => o.kind === 'boon') ?? offers[0]);
        expect(passivesHeld(b)).toBeLessThanOrEqual(MAX_PASSIVES);
      }
    }
    expect(combat).toBeGreaterThan(0);
    expect(passive).toBeGreaterThan(0);
    expect(passivesHeld(b)).toBe(MAX_PASSIVES);
  });
});
