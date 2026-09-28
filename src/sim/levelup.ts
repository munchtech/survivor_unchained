import type { Battle, Offer } from './battle';
import { WEAPONS, WEAPON_POOL, MAX_WEAPONS, WEAPON_MAX_RANK, type Evolution } from '@/content/weapons';
import { BOONS, type BoonRequirement, type Rarity } from '@/content/boons';
import { statOf, tagsOf, schoolOf } from './weapons';
import type { StatusKind, Tag } from './types';

/* The ember draft: three cards (four, with the right gear) each time the
 * survivor's ember rises a level. Most of them are skills (a new weapon,
 * or a rank in one you carry); one is a passive (a boon, or a rule that
 * makes things interact).
 *
 * It leans, never forces. Cards that share tags with what the build already
 * does are likelier; synergies wait until the build has something for them
 * to work on; rarer cards get likelier with luck. Evolutions are never
 * random: a weapon at rank 8 whose catalyst is met is always offered, with
 * one card per branch the build has earned, so the choice of what a weapon
 * becomes is always the player's. */

const RARITY_WEIGHT: Record<Rarity, number> = { common: 10, uncommon: 6.5, rare: 3.6, epic: 1.7, legendary: 0.7 };

/** Statuses the build applies, from weapons, evolutions and triggers. */
export function buildStatuses(b: Battle): Set<StatusKind> {
  const out = new Set<StatusKind>();
  for (const w of b.weapons) {
    const s = statOf(w, 'status');
    if (s) out.add(s.kind);
  }
  for (const t of b.triggers) {
    for (const fx of t.def.effects) {
      if (fx.do === 'status' || (fx.do === 'explode' && fx.status)) {
        const k = fx.do === 'status' ? fx.status.kind : fx.status!.kind;
        out.add(k);
      }
    }
  }
  if (b.boons.serration) out.add('bleed');
  if (b.boons.chilling) out.add('chill');
  if (b.boons.searing) out.add('sear');
  for (const g of b.gearStatuses) out.add(g);
  return out;
}

export function buildTags(b: Battle): Set<Tag> {
  const out = new Set<Tag>();
  for (const w of b.weapons) for (const t of tagsOf(w)) out.add(t);
  for (const [id, r] of Object.entries(b.boons)) if (r > 0) for (const t of BOONS[id]?.tags ?? []) out.add(t);
  if (b.boons.spirit_companion || b.boons.grave_call || b.boons.soul_harvest) out.add('summon');
  return out;
}

function meets(b: Battle, req: BoonRequirement | undefined, statuses: Set<StatusKind>, tags: Set<Tag>): boolean {
  if (!req) return true;
  if ('any' in req) return req.any.some((r) => meets(b, r, statuses, tags));
  if ('status' in req) return statuses.has(req.status);
  if ('tag' in req) return tags.has(req.tag);
  if ('boon' in req) return (b.boons[req.boon] ?? 0) > 0;
  return true;
}

/** Evolution branches a weapon has earned. */
export function earnedBranches(b: Battle, weaponId: string): Evolution[] {
  const w = b.weapons.find((x) => x.id === weaponId);
  if (!w || w.evolution || w.rank < WEAPON_MAX_RANK) return [];
  const statuses = buildStatuses(b);
  return w.def.evolutions.filter((evo) => evo.catalysts.some((c) => {
    if (c.boon && (b.boons[c.boon] ?? 0) > 0) return true;
    if (c.synergy && (b.boons[c.synergy] ?? 0) > 0) return true;
    if (c.status && statuses.has(c.status)) return true;
    if (c.school && b.weapons.some((o) => o !== w && schoolOf(o) === c.school)) return true;
    if (c.item && b.gearIds.has(c.item)) return true;
    return false;
  }));
}

function affinity(cardTags: readonly string[], build: Set<Tag>) {
  let n = 0;
  for (const t of cardTags) if (build.has(t as Tag)) n++;
  return 1 + n * 0.6;
}

/** Weighted pick without replacement. */
function takeFrom(b: Battle, pool: Array<{ o: Offer; w: number }>): Offer | null {
  if (!pool.length) return null;
  let total = 0;
  for (const p of pool) total += p.w;
  let roll = b.rng.next() * total;
  let k = 0;
  for (; k < pool.length; k++) { roll -= pool[k].w; if (roll <= 0) break; }
  return pool.splice(Math.min(k, pool.length - 1), 1)[0].o;
}

export function draft(b: Battle, count = 3): Offer[] {
  const statuses = buildStatuses(b);
  const tags = buildTags(b);
  const luck = b.stats.get('luck');
  const offers: Offer[] = [];
  // Skills are the weapons: new ones and ranks in the ones you have. Boons
  // and rules are the passives. A draft is mostly skills, with one passive.
  const skills: Array<{ o: Offer; w: number }> = [];
  const passives: Array<{ o: Offer; w: number }> = [];

  // Evolutions come first and are not left to chance.
  for (const w of b.weapons) {
    for (const evo of earnedBranches(b, w.id)) {
      offers.push({
        kind: 'evolve', id: w.id, branch: evo.id, rarity: 'legendary', title: evo.name,
        text: `${w.def.name} becomes ${evo.name}. ${evo.description}`, icon: evo.art ?? w.def.art, tags: [...tagsOf(w)],
      });
    }
  }

  for (const w of b.weapons) {
    if (w.rank >= WEAPON_MAX_RANK) continue;
    const next = w.rank + 1;
    const extra = next === 4 || next === 7 ? ' One more projectile.' : '';
    const hint = next === WEAPON_MAX_RANK && !w.evolution ? ' At rank 8 it can evolve.' : '';
    skills.push({ o: { kind: 'rank', id: w.id, rarity: 'common', title: w.evolution?.name ?? w.def.name, text: `+20% damage (+${(next - 1) * 20}% in all).${extra}${hint}`, from: w.rank, to: next, icon: w.evolution?.art ?? w.def.art, tags: tagsOf(w) }, w: 9 * affinity(tagsOf(w), tags) });
  }
  if (b.weapons.length < MAX_WEAPONS) {
    // A small arsenal wants new weapons more than a full one does.
    const want = b.weapons.length < 3 ? 2.4 : b.weapons.length < 5 ? 1.4 : 1;
    for (const id of WEAPON_POOL) {
      if (b.weapons.some((w) => w.id === id) || b.bannedCards.has(id)) continue;
      const d = WEAPONS[id];
      // A calling's own kind of skill comes up far more often than another's.
      const own = !b.favours.size ? 1 : d.tags.some((t) => b.favours.has(t)) ? 2.6 : 0.3;
      skills.push({ o: { kind: 'weapon', id, rarity: 'uncommon', title: d.name, text: d.description, icon: d.art, tags: d.tags }, w: 3.2 * want * own * affinity(d.tags, tags) });
    }
  }
  for (const d of Object.values(BOONS)) {
    const r = b.boons[d.id] ?? 0;
    if (r >= d.max || b.bannedCards.has(d.id)) continue;
    if (!meets(b, d.requires, statuses, tags)) continue;
    let w = RARITY_WEIGHT[d.rarity];
    if (d.rarity !== 'common') w *= 1 + (luck - 1) * 0.6;
    w *= affinity(d.tags, tags);
    if (r > 0) w *= 1.35;
    if (d.kind === 'synergy') w *= 1.4;
    passives.push({ o: { kind: 'boon', id: d.id, rarity: d.rarity, title: d.name, text: d.text, from: r, to: r + 1, icon: d.icon, tags: d.tags }, w });
  }

  // All but one of the open places are skills; the last is a passive. When
  // one kind runs out, the other fills in.
  const open = Math.max(0, count - offers.length);
  const picks: Offer[] = [];
  const wantPassive = open >= 2 ? 1 : 0;
  for (let i = 0; i < open - wantPassive; i++) { const o = takeFrom(b, skills) ?? takeFrom(b, passives); if (o) picks.push(o); }
  for (let i = picks.length; i < open; i++) { const o = takeFrom(b, passives) ?? takeFrom(b, skills); if (o) picks.push(o); }
  // Shuffle, so the passive is not always the last card.
  for (let i = picks.length - 1; i > 0; i--) { const j = Math.floor(b.rng.next() * (i + 1)); [picks[i], picks[j]] = [picks[j], picks[i]]; }
  offers.push(...picks);
  if (offers.length === 0) {
    offers.push({ kind: 'heal', id: 'heal', rarity: 'common', title: 'Second Wind', text: 'Recover 35% of your health.', icon: 'heart', tags: [] });
    offers.push({ kind: 'gold', id: 'gold', rarity: 'common', title: 'Scavenged Coin', text: '+25 gold.', icon: 'coin', tags: [] });
  }
  return offers.slice(0, Math.max(count, offers.filter((o) => o.kind === 'evolve').length));
}

export function choose(b: Battle, o: Offer) {
  switch (o.kind) {
    case 'weapon': b.addWeapon(o.id, 1); break;
    case 'rank': b.rankWeapon(o.id); break;
    case 'boon': b.addBoon(o.id); break;
    case 'evolve': b.evolve(o.id, o.branch!); break;
    case 'heal': b.healPlayer(b.maxHp * 0.35, 'draft'); break;
    case 'gold': b.goldGained += 25; break;
  }
  b.pendingLevels = Math.max(0, b.pendingLevels - 1);
}
