import type { School, Family, Tag } from './types';

/* Stats, and how modifiers fold into them.
 *
 * Every number the survivor fights with is a stat, and every source that
 * changes one - an attribute, a piece of gear, a boon taken on level-up, a
 * shrine's blessing, an injury - contributes StatMods. They fold in three
 * layers, the way ARPG players expect:
 *
 *   value = (base + sum of flat) * (1 + sum of increased) * product of (1 + more)
 *
 * "Increased" stacks additively with other increases; "more" multiplies.
 * Keeping the distinction is what makes a rare "more" modifier feel special
 * without letting ten common "increased" ones run away.
 *
 * Conditional modifiers (only while moving, only against beasts, only at
 * night) carry a `when` key the combat code evaluates at the moment of use. */

export type StatKey =
  | 'maxHealth' | 'regen' | 'armor' | 'moveSpeed' | 'pickupRadius' | 'dodge' | 'block'
  | 'damage' | 'cooldown' | 'area' | 'projectiles' | 'projectileSpeed' | 'duration' | 'pierce'
  | 'critChance' | 'critDamage' | 'luck' | 'xpGain' | 'goldGain' | 'healing' | 'lifesteal'
  | 'thorns' | 'summonDamage' | 'summonHaste' | 'statusChance' | 'statusDamage' | 'knockback'
  | 'dashCharges' | 'dashCooldown' | 'abilityCooldown' | 'abilityPower' | 'ultCharge'
  | 'lightRadius' | 'executeThreshold'
  | `damage.${School}` | `damage.${Tag}` | `resist.${School}` | `vs.${Family}` | `from.${Family}`;

export type ModKind = 'flat' | 'inc' | 'more';

/** When a conditional modifier applies. Evaluated by combat code. */
export type ModWhen = 'moving' | 'still' | 'night' | 'lowHealth' | 'fullHealth' | 'nearBeasts' | 'inBurning' | 'shapeshifted' | 'afterDash';

export interface StatMod {
  stat: StatKey;
  kind: ModKind;
  value: number;
  source: string;
  when?: ModWhen;
}

export interface StatBase {
  maxHealth: number; regen: number; armor: number; moveSpeed: number; pickupRadius: number;
  critChance: number; critDamage: number; luck: number;
}

/** Things with meaningful defaults when nobody has touched them. */
const DEFAULTS: Partial<Record<StatKey, number>> = {
  damage: 1, cooldown: 1, area: 1, projectileSpeed: 1, duration: 1, xpGain: 1, goldGain: 1,
  healing: 1, summonDamage: 1, summonHaste: 1, statusChance: 0, statusDamage: 1, knockback: 1,
  dashCharges: 1, dashCooldown: 1, abilityCooldown: 1, abilityPower: 1, ultCharge: 1, lightRadius: 1,
  projectiles: 0, pierce: 0, dodge: 0, block: 0, lifesteal: 0, thorns: 0, executeThreshold: 0,
};

export class StatBlock {
  private mods: StatMod[] = [];
  private cache = new Map<string, number>();
  private base: Partial<Record<StatKey, number>> = {};
  /** Evaluated per query for conditional mods; set by the owner each tick. */
  active = new Set<ModWhen>();
  private activeKey = '';

  setBase(b: Partial<Record<StatKey, number>>) {
    this.base = { ...b };
    this.cache.clear();
  }

  add(mod: StatMod) {
    this.mods.push(mod);
    this.cache.clear();
  }

  addAll(mods: StatMod[]) {
    for (const m of mods) this.mods.push(m);
    this.cache.clear();
  }

  removeSource(source: string) {
    const n = this.mods.length;
    this.mods = this.mods.filter((m) => m.source !== source);
    if (this.mods.length !== n) this.cache.clear();
  }

  hasSource(source: string) { return this.mods.some((m) => m.source === source); }

  setActive(conds: Iterable<ModWhen>) {
    const next = new Set(conds);
    const key = [...next].sort().join(',');
    if (key !== this.activeKey) {
      this.active = next;
      this.activeKey = key;
      this.cache.clear();
    }
  }

  get(stat: StatKey): number {
    const hit = this.cache.get(stat);
    if (hit !== undefined) return hit;
    let flat = this.base[stat] ?? DEFAULTS[stat] ?? 0;
    let inc = 0;
    let more = 1;
    for (const m of this.mods) {
      if (m.stat !== stat) continue;
      if (m.when && !this.active.has(m.when)) continue;
      if (m.kind === 'flat') flat += m.value;
      else if (m.kind === 'inc') inc += m.value;
      else more *= 1 + m.value;
    }
    // Multipliers that start at 1 (damage, area...) treat "increased" as a
    // percentage of their base; additive stats (armor, crit) do too.
    const v = flat * (1 + inc) * more;
    this.cache.set(stat, v);
    return v;
  }

  /** Damage multiplier for one hit: global damage, the school, every tag the
   *  source carries, and the family of what it hits. */
  damageMult(school: School, tags: readonly Tag[], vs?: Family) {
    let m = this.get('damage') * this.get(`damage.${school}`);
    for (const t of tags) if (t !== school) m *= this.get(`damage.${t}` as StatKey);
    if (vs) m *= 1 + this.getRaw(`vs.${vs}` as StatKey);
    return m;
  }

  /** For stats with no multiplicative default (vs.*, from.*, resist.*). */
  getRaw(stat: StatKey) {
    const hit = this.cache.get(stat);
    if (hit !== undefined) return hit;
    let flat = this.base[stat] ?? 0;
    let inc = 0, more = 1;
    for (const m of this.mods) {
      if (m.stat !== stat) continue;
      if (m.when && !this.active.has(m.when)) continue;
      if (m.kind === 'flat') flat += m.value;
      else if (m.kind === 'inc') inc += m.value;
      else more *= 1 + m.value;
    }
    const v = flat * (1 + inc) * more;
    this.cache.set(stat, v);
    return v;
  }

  list() { return this.mods; }
}

/** Armor's damage reduction: diminishing, never total. 10 armor ~ 33%. */
export function armorReduction(armor: number) {
  return armor <= 0 ? 0 : armor / (armor + 20);
}

/** Every per-school or per-tag damage stat defaults to 1 (no change). */
for (const s of ['physical', 'fire', 'frost', 'storm', 'nature', 'arcane', 'holy', 'shadow']) {
  (DEFAULTS as Record<string, number>)[`damage.${s}`] = 1;
}
for (const t of ['projectile', 'area', 'melee', 'summon', 'aura', 'beam', 'chain', 'orbit', 'nova', 'zone', 'storm',
  'bounce', 'ranged', 'dot', 'explosion', 'trap', 'heal', 'thrown', 'spell', 'steel']) {
  (DEFAULTS as Record<string, number>)[`damage.${t}`] = 1;
}
