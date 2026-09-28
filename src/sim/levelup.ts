import type { Battle, Offer } from './battle';
import { WEAPONS, WEAPON_POOL, MAX_WEAPONS, WEAPON_MAX_RANK, type Evolution } from '@/content/weapons';
import { BOONS, MILESTONE_EVERY, isMilestone, type BoonRequirement, type Rarity } from '@/content/boons';
import { statOf, tagsOf, schoolOf } from './weapons';
import type { StatusKind, Tag } from './types';

/* The ember draft: three cards (four, with the right gear) each time the
 * survivor's ember rises a level, all skills: a new one, or a rank in one
 * you carry; anyone can take any skill (a calling leans a little toward its
 * own). Blessings (boons, and the combos that make things interact) are
 * milestones: one at the start of every expedition, and one more when the
 * ember reaches a multiple of MILESTONE_EVERY, after that level's skill.
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

/** What a weapon at full rank can become: every branch, always. Nothing is
 *  needed to evolve; what the build already has (a blessing, a status,
 *  another school, a piece of gear) only marks a branch as fitting it. */
export function earnedBranches(b: Battle, weaponId: string): Evolution[] {
  const w = b.weapons.find((x) => x.id === weaponId);
  if (!w || w.evolution || w.rank < WEAPON_MAX_RANK) return [];
  return [...w.def.evolutions];
}

/** The branches the build already points toward. */
export function fittingBranches(b: Battle, weaponId: string): Evolution[] {
  const w = b.weapons.find((x) => x.id === weaponId);
  return w ? catalysed(b, w) : [];
}

function catalysed(b: Battle, w: Battle['weapons'][number]): Evolution[] {
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

export { MILESTONE_EVERY, isMilestone };
/** Is the next draft a milestone's blessing? (Skills owed come first.) */
export const blessingNext = (b: Battle) => b.pendingLevels === 0 && b.pendingBlessings.length > 0;
/** The level the next draft is for (several can be owed at once). */
export const draftLevel = (b: Battle) => (blessingNext(b) ? b.pendingBlessings[0] : b.ember.level - b.pendingLevels + 1);

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
  // Skills are the weapons: new ones and ranks in the ones you have.
  // Blessings (boons and combos) are for milestones.
  const skills: Array<{ o: Offer; w: number }> = [];
  const passives: Array<{ o: Offer; w: number }> = [];

  // Evolutions come first and are not left to chance: one weapon at a time,
  // every branch of it (the next weapon ready waits for the next draft).
  const ready = b.weapons.find((w) => earnedBranches(b, w.id).length > 0);
  if (ready && !blessingNext(b)) {
    const fit = new Set(fittingBranches(b, ready.id).map((e) => e.id));
    for (const evo of earnedBranches(b, ready.id)) {
      offers.push({
        kind: 'evolve', id: ready.id, branch: evo.id, rarity: 'legendary', title: evo.name,
        text: `${ready.def.name} becomes ${evo.name}. ${evo.description}`, icon: evo.art ?? ready.def.art, tags: [...tagsOf(ready)],
        fits: fit.has(evo.id),
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
      // A slight lean toward the calling's own style; anyone can take anything.
      const lean = b.favours.size && d.tags.some((t) => b.favours.has(t)) ? 1.35 : 1;
      skills.push({ o: { kind: 'weapon', id, rarity: 'uncommon', title: d.name, text: d.description, icon: d.art, tags: d.tags }, w: 3.2 * want * lean * affinity(d.tags, tags) });
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

  // A level's draft is skills; a milestone's blessing is boons and combos.
  // When skills have run out, blessings fill a level's draft instead.
  if (blessingNext(b)) {
    offers.length = 0;
    for (let i = 0; i < count; i++) { const o = takeFrom(b, passives); if (o) offers.push({ ...o, blessing: true }); }
    return offers;
  }
  const open = Math.max(0, count - offers.length);
  for (let i = 0; i < open; i++) { const o = takeFrom(b, skills) ?? takeFrom(b, passives); if (o) offers.push(o); }
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
  if (o.blessing) b.pendingBlessings.shift();
  else b.pendingLevels = Math.max(0, b.pendingLevels - 1);
}
