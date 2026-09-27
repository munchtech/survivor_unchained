import type { School, Tag, StatusKind } from '@/sim/types';

/* The arsenal. Every weapon fires on its own; what the survivor does is
 * choose them, rank them and decide what they become.
 *
 * Ported from The Ember Watch (distances and speeds converted at 40 px to the
 * metre) with two changes that matter for an RPG:
 *
 *   - Tags and a school on everything, so gear and boons can say "your
 *     projectiles" or "your fire" and mean it.
 *   - Evolution BRANCHES. A rank-8 weapon does not have one destiny; it
 *     becomes whatever the rest of the build pulls it toward. Each branch
 *     names its catalyst - a boon, a synergy, a status the build applies -
 *     and a weapon with two catalysts met asks which it should become.
 *
 * Rank growth (applied by the runtime): +20% damage per rank, +4% area per
 * rank, +6% duration per rank, one more projectile at ranks 4 and 7. */

export type WeaponBehavior =
  | 'aimed' | 'spray' | 'ring' | 'nova' | 'zone' | 'chain' | 'orbit' | 'storm' | 'bounce' | 'beam'
  | 'palm' | 'herd' | 'chakram' | 'slash';

export interface StatusPayload { kind: StatusKind; chance: number; power: number; duration: number }

export interface WeaponStats {
  cooldown: number;
  damage: number;
  speed?: number;
  projectiles?: number;
  pierce?: number;
  range?: number;
  radius?: number; // projectile hit radius, or nova/zone radius
  life?: number;
  homing?: number; // turn rate, radians per second
  splash?: number;
  spread?: number;
  duration?: number;
  tickRate?: number;
  chains?: number;
  chainRange?: number;
  bounces?: number;
  orbitRadius?: number;
  orbitSpeed?: number;
  strikes?: number;
  stormRadius?: number;
  beamWidth?: number;
  reach?: number;
  arc?: number;
  knockback?: number;
  expandTime?: number;
  heal?: number;
  atTarget?: boolean;
  slow?: number;
  status?: StatusPayload;
  /** A burst of shots in quick succession instead of all at once. */
  burst?: boolean;
  /** The weapon also leaves burning/hallowed/blighted ground where it hits. */
  groundOnHit?: { radius: number; duration: number; dpsPct: number };
  /** Projectiles split into smaller ones on hit. */
  splitOnHit?: number;
  /** Chains fork into two at each jump. */
  fork?: boolean;
}

export interface Evolution {
  id: string;
  name: string;
  description: string;
  /** Any of these unlocks this branch. */
  catalysts: Array<{ boon?: string; synergy?: string; status?: StatusKind; school?: School; item?: string }>;
  /** Multiplicative on damage/cooldown/area/speed/duration; additive on counts. */
  mods: Partial<Record<'damage' | 'cooldown' | 'area' | 'speed' | 'duration', number>> &
    Partial<Record<'projectiles' | 'pierce' | 'bounces' | 'chains' | 'strikes', number>>;
  set?: Partial<WeaponStats>;
  behavior?: WeaponBehavior;
  school?: School;
  addTags?: Tag[];
  art?: string;
}

export interface WeaponDef {
  id: string;
  name: string;
  school: School;
  behavior: WeaponBehavior;
  tags: Tag[];
  base: WeaponStats;
  art: string;
  /** Bosses and elites: crowd weapons hit one big target softly. */
  bossDamage?: number;
  description: string;
  evolutions: Evolution[];
  /** Offered in the level-up pool? Starting-only weapons are not. */
  findable?: boolean;
}

const W = (d: WeaponDef) => d;

export const WEAPONS: Record<string, WeaponDef> = {
  oathblade: W({
    id: 'oathblade', name: 'Oathblade', school: 'physical', behavior: 'slash', tags: ['melee', 'steel', 'physical', 'area'],
    base: { cooldown: 1.05, damage: 24, reach: 2.8, arc: 2.3, knockback: 0.9, projectiles: 1 },
    art: 'slash_steel', bossDamage: 1.4,
    description: 'Your blade swings on its own at whatever is nearest, cutting everything in a wide arc in front of you.',
    evolutions: [
      { id: 'oathkeeper', name: 'Oathkeeper', description: 'Every swing throws a crescent of holy light that carries on through the crowd.',
        catalysts: [{ boon: 'ironhide' }, { school: 'holy' }], mods: { damage: 1.5, cooldown: 0.85, area: 1.2 }, addTags: ['holy', 'projectile'], art: 'slash_holy' },
      { id: 'graveedge', name: 'Grave-Edge', description: 'The edge drinks: every cut bleeds, and anything bleeding below a sixth of its life is simply finished.',
        catalysts: [{ boon: 'serration' }, { status: 'bleed' }], mods: { damage: 1.6, cooldown: 0.9 },
        set: { status: { kind: 'bleed', chance: 1, power: 0.35, duration: 3 } }, art: 'slash_blood' },
    ],
  }),
  cleaver: W({
    id: 'cleaver', name: 'Butcher\'s Cleaver', school: 'physical', behavior: 'slash', tags: ['melee', 'steel', 'physical', 'area'],
    base: { cooldown: 1.45, damage: 34, reach: 2.5, arc: 3.4, knockback: 1.3, projectiles: 1, status: { kind: 'bleed', chance: 0.35, power: 0.3, duration: 3 } },
    art: 'slash_heavy', bossDamage: 1.3,
    description: 'A heavy, wide chop all the way round the front of you. Opens wounds.',
    evolutions: [
      { id: 'whirlwind', name: 'Whirlwind', description: 'The chop becomes a full turn: everything around you, every time.',
        catalysts: [{ boon: 'fleetfoot' }, { boon: 'ferocity' }], mods: { damage: 1.4, cooldown: 0.8 }, set: { arc: 6.283 }, art: 'slash_spin' },
      { id: 'bonesplitter', name: 'Bonesplitter', description: 'Each chop sends a shockwave ahead of it that shatters the frozen and staggers the rest.',
        catalysts: [{ status: 'chill' }, { boon: 'might' }], mods: { damage: 1.7, area: 1.25 }, set: { knockback: 2.2 }, addTags: ['explosion'], art: 'slash_quake' },
    ],
  }),
  seeking_motes: W({
    id: 'seeking_motes', name: 'Seeking Motes', school: 'arcane', behavior: 'aimed', tags: ['projectile', 'spell', 'arcane'],
    base: { cooldown: 0.93, damage: 5.5, speed: 8.4, projectiles: 3, pierce: 2, range: 14, homing: 5.5, life: 2.2, radius: 0.18, burst: true },
    art: 'mote', bossDamage: 1.7, findable: true,
    description: 'A rapid volley of small seeking motes that curve through the crowd on their own.',
    evolutions: [
      { id: 'mote_cascade', name: 'Mote Cascade', description: 'The motes multiply beyond counting, and each one splits in two when it strikes.',
        catalysts: [{ boon: 'duplicity' }], mods: { damage: 1.4, projectiles: 3 }, set: { splitOnHit: 2 }, art: 'mote_cascade' },
      { id: 'starseeker', name: 'Starseeker', description: 'Motes hunt the strongest thing on the field, and they bite deeper for every critical strike.',
        catalysts: [{ boon: 'precision' }, { synergy: 'hunters_mark' }], mods: { damage: 1.9, cooldown: 0.85 }, set: { homing: 9 }, art: 'mote_star' },
    ],
  }),
  cinderfall: W({
    id: 'cinderfall', name: 'Cinderfall', school: 'fire', behavior: 'aimed', tags: ['projectile', 'spell', 'fire', 'explosion'],
    base: { cooldown: 1.75, damage: 31, speed: 8.6, projectiles: 1, pierce: 0, range: 15, splash: 1.8, life: 2.4, radius: 0.28,
      status: { kind: 'burn', chance: 0.5, power: 0.25, duration: 3 } },
    art: 'cinder', findable: true,
    description: 'A slow, heavy cinder that bursts on impact and sets what it touches alight.',
    evolutions: [
      { id: 'fallen_star', name: 'Fallen Star', description: 'The cinder becomes a falling star: a huge blast that leaves the ground burning.',
        catalysts: [{ boon: 'expanse' }], mods: { damage: 1.5, area: 1.45 }, set: { groundOnHit: { radius: 2.2, duration: 3, dpsPct: 0.25 } }, art: 'star' },
      { id: 'living_flame', name: 'Living Flame', description: 'Cinders burst into three seeking flames that hunt on after the blast.',
        catalysts: [{ synergy: 'kindling' }, { synergy: 'pyre_burst' }, { status: 'burn' }], mods: { damage: 1.35, cooldown: 0.85 },
        set: { splitOnHit: 3, homing: 4 }, art: 'living_flame' },
    ],
  }),
  rimeshard: W({
    id: 'rimeshard', name: 'Rimeshard', school: 'frost', behavior: 'aimed', tags: ['projectile', 'spell', 'frost'],
    base: { cooldown: 1.2, damage: 18, speed: 9.1, projectiles: 1, pierce: 2, range: 14.5, life: 2.2, radius: 0.22,
      status: { kind: 'chill', chance: 1, power: 1, duration: 2.5 } },
    art: 'shard', bossDamage: 1.1, findable: true,
    description: 'Bitter cold that pierces and chills. Enough chill and a thing freezes solid.',
    evolutions: [
      { id: 'deepwinter', name: 'Deepwinter', description: 'Winter takes the field: shards burst into a ring of smaller shards on the frozen.',
        catalysts: [{ boon: 'haste' }, { synergy: 'shatter' }], mods: { damage: 1.5, cooldown: 0.8, projectiles: 1 }, set: { splitOnHit: 4 }, art: 'shard_deep' },
      { id: 'glacier_spear', name: 'Glacier Spear', description: 'One enormous lance of ice that runs the length of the field and freezes all it passes.',
        catalysts: [{ boon: 'velocity' }], mods: { damage: 2.1, speed: 1.4, pierce: 20 },
        set: { radius: 0.5, status: { kind: 'chill', chance: 1, power: 3, duration: 3 } }, art: 'spear_ice' },
    ],
  }),
  arcweb: W({
    id: 'arcweb', name: 'Arcweb', school: 'storm', behavior: 'chain', tags: ['chain', 'spell', 'storm'],
    base: { cooldown: 1.65, damage: 27, chains: 5, chainRange: 6.25, range: 11, status: { kind: 'shock', chance: 0.5, power: 1, duration: 3 } },
    art: 'arc', bossDamage: 3.5, findable: true,
    description: 'Lightning that leaps from foe to foe.',
    evolutions: [
      { id: 'skybreak', name: 'Skybreak', description: 'The sky answers every call: each leap also brings a bolt straight down.',
        catalysts: [{ boon: 'precision' }], mods: { damage: 1.5, chains: 2 }, addTags: ['storm'], art: 'arc_sky' },
      { id: 'tempest_coil', name: 'Tempest Coil', description: 'The lightning forks at every leap. A crowd becomes a web.',
        catalysts: [{ boon: 'expanse' }, { synergy: 'static_charge' }], mods: { damage: 1.25 }, set: { fork: true }, art: 'arc_fork' },
    ],
  }),
  dawnpulse: W({
    id: 'dawnpulse', name: 'Dawnpulse', school: 'holy', behavior: 'nova', tags: ['nova', 'area', 'spell', 'holy'],
    base: { cooldown: 2.6, damage: 27, radius: 3.75, expandTime: 0.35, knockback: 0.65, status: { kind: 'sear', chance: 1, power: 1, duration: 3 } },
    art: 'nova_holy', bossDamage: 2.4, findable: true,
    description: 'A ring of Light erupts outward from you, throwing back what it touches. The dead hate it.',
    evolutions: [
      { id: 'circle_of_dawn', name: 'Circle of Dawn', description: 'Each dawn mends you as it burns them.',
        catalysts: [{ boon: 'vitality' }, { boon: 'recovery' }], mods: { damage: 1.5, area: 1.2 }, set: { heal: 4 }, art: 'nova_dawn' },
      { id: 'sunbreak', name: 'Sunbreak', description: 'The pulse leaves a ring of daylight on the ground that goes on burning.',
        catalysts: [{ boon: 'might' }, { synergy: 'consecration' }], mods: { damage: 1.4 }, set: { groundOnHit: { radius: 3.5, duration: 2.5, dpsPct: 0.3 } }, art: 'nova_sun' },
    ],
  }),
  hallowed_ring: W({
    id: 'hallowed_ring', name: 'Hallowed Ground', school: 'holy', behavior: 'zone', tags: ['zone', 'area', 'aura', 'holy'],
    base: { cooldown: 3.95, damage: 10, radius: 3, duration: 4, tickRate: 0.5, status: { kind: 'sear', chance: 0.4, power: 1, duration: 2 } },
    art: 'zone_holy', bossDamage: 1.7, findable: true,
    description: 'Hallows the ground beneath your feet. Whatever stands in it burns.',
    evolutions: [
      { id: 'sanctified_earth', name: 'Sanctified Earth', description: 'Sacred ground that shelters as it burns: stand in it and blows glance off you.',
        catalysts: [{ boon: 'ironhide' }], mods: { damage: 1.5, area: 1.25, duration: 1.3 }, art: 'zone_sanct' },
      { id: 'pyre_of_faith', name: 'Pyre of Faith', description: 'The ground catches fire as well as light. Everything in it burns twice.',
        catalysts: [{ school: 'fire' }, { status: 'burn' }], mods: { damage: 1.4 }, school: 'fire',
        set: { status: { kind: 'burn', chance: 0.6, power: 0.3, duration: 3 } }, addTags: ['fire'], art: 'zone_pyre' },
    ],
  }),
  umbral_bolt: W({
    id: 'umbral_bolt', name: 'Umbral Bolt', school: 'shadow', behavior: 'aimed', tags: ['projectile', 'spell', 'shadow'],
    base: { cooldown: 1.1, damage: 23.7, speed: 9.1, projectiles: 1, pierce: 2, range: 14.5, life: 2.4, radius: 0.22 },
    art: 'umbral', findable: true,
    description: 'Bolts of shadow that tear straight through ranks.',
    evolutions: [
      { id: 'ruin_bolt', name: 'Ruin Bolt', description: 'Ruin that nothing can stop: the bolt passes through everything and tears a wound behind it.',
        catalysts: [{ boon: 'might' }], mods: { damage: 1.6, pierce: 20, speed: 1.2 }, art: 'ruin' },
      { id: 'soul_siphon', name: 'Soul Siphon', description: 'Each bolt drinks a little of whatever it passes through and gives it to you.',
        catalysts: [{ boon: 'recovery' }, { synergy: 'soul_harvest' }], mods: { damage: 1.4, projectiles: 1 }, set: { heal: 0.6 }, art: 'siphon' },
    ],
  }),
  knifestorm: W({
    id: 'knifestorm', name: 'Knifestorm', school: 'physical', behavior: 'ring', tags: ['projectile', 'thrown', 'steel', 'physical'],
    base: { cooldown: 1.43, damage: 16.4, speed: 8.65, projectiles: 6, pierce: 1, life: 0.9, radius: 0.2,
      status: { kind: 'bleed', chance: 0.15, power: 0.3, duration: 3 } },
    art: 'dagger', bossDamage: 2.9, findable: true,
    description: 'A whirling ring of thrown steel in every direction.',
    evolutions: [
      { id: 'steel_flurry', name: 'Steel Flurry', description: 'The steel never stops moving: twice the knives, twice as often.',
        catalysts: [{ boon: 'fleetfoot' }], mods: { damage: 1.3, cooldown: 0.65, projectiles: 4 }, art: 'dagger_flurry' },
      { id: 'thousand_cuts', name: 'A Thousand Cuts', description: 'Every knife opens a wound, and wounds on the same body stack.',
        catalysts: [{ boon: 'serration' }, { status: 'bleed' }], mods: { damage: 1.4, projectiles: 2 },
        set: { status: { kind: 'bleed', chance: 1, power: 0.4, duration: 3.5 } }, art: 'dagger_blood' },
    ],
  }),
  axe_gyre: W({
    id: 'axe_gyre', name: 'Axe Gyre', school: 'physical', behavior: 'orbit', tags: ['orbit', 'melee', 'steel', 'physical', 'area'],
    base: { cooldown: 4.6, damage: 23.7, projectiles: 3, orbitRadius: 2.1, orbitSpeed: 4.2, duration: 3.2, radius: 0.5 },
    art: 'axe', findable: true,
    description: 'Axes circle you, shredding all who close in.',
    evolutions: [
      { id: 'gyrestorm', name: 'Gyrestorm', description: 'Become the storm of blades: more axes, spinning faster, never stopping.',
        catalysts: [{ boon: 'ferocity' }], mods: { damage: 1.5, projectiles: 3, duration: 1.8 }, set: { orbitSpeed: 5.2 }, art: 'axe_storm' },
      { id: 'reavers_wheel', name: 'Reaver\'s Wheel', description: 'The axes bite and stay bitten: every cut bleeds, and a bleeding kill flings the axe outward.',
        catalysts: [{ boon: 'serration' }, { status: 'bleed' }], mods: { damage: 1.5 },
        set: { status: { kind: 'bleed', chance: 1, power: 0.35, duration: 3 }, orbitRadius: 2.8 }, art: 'axe_blood' },
    ],
  }),
  volley: W({
    id: 'volley', name: 'Volley', school: 'physical', behavior: 'spray', tags: ['projectile', 'ranged', 'physical'],
    base: { cooldown: 1.54, damage: 15.5, speed: 10.5, projectiles: 3, pierce: 2, range: 15.5, spread: 0.16, life: 1.7, radius: 0.2 },
    art: 'arrow', bossDamage: 1.4, findable: true,
    description: 'A widening spread of hunting arrows loosed at the nearest foe.',
    evolutions: [
      { id: 'arrowfall', name: 'Arrowfall', description: 'The sky darkens with arrows: each volley also rains down on the thickest part of the crowd.',
        catalysts: [{ boon: 'velocity' }], mods: { damage: 1.4, projectiles: 2 }, set: { strikes: 6, stormRadius: 5 }, art: 'arrow_rain' },
      { id: 'predators_volley', name: 'Predator\'s Volley', description: 'Arrows fly straight to the marked and the wounded, and every one leaves its own mark.',
        catalysts: [{ synergy: 'hunters_mark' }, { boon: 'precision' }], mods: { damage: 1.6 },
        set: { homing: 3, status: { kind: 'mark', chance: 0.35, power: 1, duration: 4 } }, art: 'arrow_mark' },
    ],
  }),
  moonbrand: W({
    id: 'moonbrand', name: 'Moonbrand', school: 'arcane', behavior: 'aimed', tags: ['projectile', 'spell', 'arcane'],
    base: { cooldown: 1.32, damage: 21.8, speed: 7.3, projectiles: 1, pierce: 0, range: 14, homing: 4, life: 2.6, radius: 0.24,
      status: { kind: 'mark', chance: 0.25, power: 1, duration: 4 } },
    art: 'moon', findable: true,
    description: 'Moonlit flame that tracks its prey and leaves it marked.',
    evolutions: [
      { id: 'moonfall', name: 'Moonfall', description: 'Moons fall wherever the enemy gathers.',
        catalysts: [{ boon: 'greed' }, { boon: 'expanse' }], mods: { damage: 1.5 }, behavior: 'storm', set: { strikes: 5, stormRadius: 5.75, splash: 1.5 }, art: 'moonfall' },
      { id: 'lunar_brand', name: 'Lunar Brand', description: 'Every moon marks, and a marked thing that dies throws the mark to its neighbours.',
        catalysts: [{ synergy: 'hunters_mark' }], mods: { damage: 1.5, projectiles: 1 }, set: { status: { kind: 'mark', chance: 1, power: 1, duration: 6 } }, art: 'moon_brand' },
    ],
  }),
  judgement_disc: W({
    id: 'judgement_disc', name: 'Judgement Disc', school: 'holy', behavior: 'bounce', tags: ['projectile', 'thrown', 'bounce', 'holy'],
    base: { cooldown: 2.3, damage: 27.3, speed: 9.8, projectiles: 1, bounces: 5, range: 15, life: 3.0, radius: 0.28, knockback: 0.3 },
    art: 'disc', bossDamage: 2.45, findable: true,
    description: 'A hurled shield that ricochets between enemies.',
    evolutions: [
      { id: 'reckoning', name: 'Reckoning', description: 'Judgement finds every last one of them: endless ricochets that grow heavier with each.',
        catalysts: [{ boon: 'fortune' }, { boon: 'precision' }], mods: { damage: 1.4, bounces: 6 }, art: 'disc_reckon' },
      { id: 'aegis_wheel', name: 'Aegis Wheel', description: 'The shield comes home each time, and while it flies it guards you.',
        catalysts: [{ boon: 'ironhide' }, { boon: 'vitality' }], mods: { damage: 1.5, projectiles: 1 }, art: 'disc_aegis' },
    ],
  }),
  blightfield: W({
    id: 'blightfield', name: 'Blightfield', school: 'shadow', behavior: 'zone', tags: ['zone', 'area', 'dot', 'shadow'],
    base: { cooldown: 4.3, damage: 11.8, radius: 3.25, duration: 4.5, tickRate: 0.45, atTarget: true,
      status: { kind: 'poison', chance: 0.6, power: 0.2, duration: 4 } },
    art: 'zone_blight', findable: true,
    description: 'Corrupts the ground under the nearest crowd; anything standing in it rots.',
    evolutions: [
      { id: 'blighted_earth', name: 'Blighted Earth', description: 'The blight spreads wider the longer it feeds, and holds what it feeds on.',
        catalysts: [{ boon: 'chilling' }], mods: { damage: 1.4, area: 1.3, duration: 1.3 }, set: { slow: 0.5 }, art: 'zone_blight2' },
      { id: 'plaguebloom', name: 'Plaguebloom', description: 'Whatever dies in the blight bursts, and the blight goes on with them.',
        catalysts: [{ synergy: 'plague_bearer' }, { status: 'poison' }], mods: { damage: 1.4 }, set: { groundOnHit: { radius: 2, duration: 3, dpsPct: 0.3 } }, art: 'zone_plague' },
    ],
  }),
  reaving_arc: W({
    id: 'reaving_arc', name: 'Reaving Arc', school: 'shadow', behavior: 'nova', tags: ['nova', 'area', 'melee', 'shadow'],
    base: { cooldown: 2.4, damage: 31, radius: 3.25, expandTime: 0.28, knockback: 0.5, heal: 3 },
    art: 'nova_blood', bossDamage: 2.9, findable: true,
    description: 'A sweeping graveblade that carves health out of the wound it makes.',
    evolutions: [
      { id: 'rend_and_mend', name: 'Rend and Mend', description: 'The blade drinks deeper than any wound can hold.',
        catalysts: [{ boon: 'recovery' }, { boon: 'vitality' }], mods: { damage: 1.5, area: 1.15 }, set: { heal: 6 }, art: 'nova_rend' },
      { id: 'harrowing', name: 'The Harrowing', description: 'What the arc kills gets up again, briefly, on your side.',
        catalysts: [{ synergy: 'soul_harvest' }], mods: { damage: 1.4 }, addTags: ['summon'], art: 'nova_harrow' },
    ],
  }),
  grave_tether: W({
    id: 'grave_tether', name: 'Grave Tether', school: 'shadow', behavior: 'aimed', tags: ['projectile', 'spell', 'shadow', 'heal'],
    base: { cooldown: 1.6, damage: 25.5, speed: 9.5, projectiles: 1, pierce: 2, range: 15, life: 2.4, radius: 0.24, heal: 1.5 },
    art: 'tether', findable: true,
    description: 'A coil of dark magic that wounds the living and knits your own flesh back together.',
    evolutions: [
      { id: 'tether_of_anguish', name: 'Tether of Anguish', description: 'The tether takes more, and gives more back.',
        catalysts: [{ boon: 'wisdom' }, { boon: 'recovery' }], mods: { damage: 1.5, projectiles: 1 }, set: { heal: 3 }, art: 'tether2' },
      { id: 'deathcoil', name: 'Deathcoil', description: 'Each coil leaves the struck marked for the grave: they take more from everything.',
        catalysts: [{ synergy: 'hunters_mark' }, { status: 'mark' }], mods: { damage: 1.4 }, set: { status: { kind: 'mark', chance: 1, power: 1, duration: 4 } }, art: 'tether_mark' },
    ],
  }),
  iron_palms: W({
    id: 'iron_palms', name: 'Iron Palms', school: 'physical', behavior: 'palm', tags: ['melee', 'physical', 'area'],
    base: { cooldown: 0.95, damage: 15, projectiles: 3, reach: 2.95, arc: 1.25, knockback: 0.35 },
    art: 'palm', bossDamage: 1.15, findable: true,
    description: 'A flurry of open-handed strikes at whatever is closest, each a short cone that hits everything in it.',
    evolutions: [
      { id: 'temple_breaker', name: 'Temple Breaker', description: 'Every palm lands like the temple bell.',
        catalysts: [{ boon: 'evasion' }], mods: { damage: 1.6, area: 1.2 }, set: { knockback: 0.9 }, art: 'palm_temple' },
      { id: 'thunder_palm', name: 'Thunder Palm', description: 'The palms carry the storm into whatever they strike.',
        catalysts: [{ school: 'storm' }, { status: 'shock' }], mods: { damage: 1.45 }, school: 'storm',
        set: { status: { kind: 'shock', chance: 0.6, power: 1, duration: 3 } }, addTags: ['storm'], art: 'palm_storm' },
    ],
  }),
  spirit_herd: W({
    id: 'spirit_herd', name: 'Spirit Herd', school: 'nature', behavior: 'herd', tags: ['summon', 'nature', 'area'],
    base: { cooldown: 2.6, damage: 21, speed: 8.25, projectiles: 2, pierce: 99, range: 15.5, life: 1.8, radius: 0.4, knockback: 0.55 },
    art: 'herd', bossDamage: 1.8, findable: true,
    description: 'Spirit beasts stampede from behind you toward the nearest foe, trampling everything in the way.',
    evolutions: [
      { id: 'great_herd', name: 'The Great Herd', description: 'The herd does not end. It only thins.',
        catalysts: [{ boon: 'perennial' }], mods: { damage: 1.4, projectiles: 3, duration: 1.3 }, art: 'herd_great' },
      { id: 'wild_hunt', name: 'The Wild Hunt', description: 'The herd runs in green fire, and each beast goes up in it at the end of its run.',
        catalysts: [{ school: 'fire' }, { synergy: 'pack_leader' }], mods: { damage: 1.4 }, set: { splash: 1.9 }, addTags: ['explosion'], art: 'herd_hunt' },
    ],
  }),
  thornbloom: W({
    id: 'thornbloom', name: 'Thornbloom', school: 'nature', behavior: 'zone', tags: ['zone', 'area', 'nature'],
    base: { cooldown: 3.8, damage: 11, radius: 2.3, duration: 4, tickRate: 0.5, atTarget: true, slow: 0.55 },
    art: 'zone_thorn', findable: true,
    description: 'Brambles burst up under the nearest crowd, tearing at everything caught and holding it slow.',
    evolutions: [
      { id: 'everbloom', name: 'Everbloom', description: 'The brambles flower, and the flowers have thorns too.',
        catalysts: [{ boon: 'thorns' }], mods: { damage: 1.4, area: 1.3, duration: 1.3 }, art: 'zone_bloom' },
      { id: 'strangleroot', name: 'Strangleroot', description: 'The roots do not let go: what they hold is held still.',
        catalysts: [{ status: 'chill' }, { boon: 'chilling' }], mods: { damage: 1.3 }, set: { slow: 0.15, status: { kind: 'stun', chance: 0.25, power: 1, duration: 1 } }, art: 'zone_root' },
    ],
  }),
  gale_chakram: W({
    id: 'gale_chakram', name: 'Gale Chakram', school: 'physical', behavior: 'chakram', tags: ['projectile', 'thrown', 'steel', 'physical'],
    base: { cooldown: 1.7, damage: 16, speed: 9.5, projectiles: 1, range: 8.25, life: 2.6, radius: 0.3 },
    art: 'chakram', bossDamage: 1.4, findable: true,
    description: 'A bladed ring thrown out on the wind. It cuts everything on the way out, and on the way back.',
    evolutions: [
      { id: 'razorgale', name: 'Razorgale', description: 'The ring splits the wind in two and comes back sharper.',
        catalysts: [{ boon: 'serration' }], mods: { damage: 1.5, projectiles: 1 }, set: { status: { kind: 'bleed', chance: 0.5, power: 0.3, duration: 3 } }, art: 'chakram_razor' },
      { id: 'hailwheel', name: 'Hailwheel', description: 'A spinning edge through a hailstorm comes back cold.',
        catalysts: [{ school: 'frost' }, { status: 'chill' }], mods: { damage: 1.4, projectiles: 1 }, school: 'frost',
        set: { status: { kind: 'chill', chance: 1, power: 1, duration: 2.5 } }, addTags: ['frost'], art: 'chakram_hail' },
    ],
  }),
  verdant_lance: W({
    id: 'verdant_lance', name: 'Verdant Lance', school: 'nature', behavior: 'beam', tags: ['beam', 'spell', 'nature'],
    base: { cooldown: 1.43, damage: 20, range: 15.5, beamWidth: 0.65, duration: 0.35, status: { kind: 'poison', chance: 0.3, power: 0.15, duration: 3 } },
    art: 'beam_green', bossDamage: 2.45, findable: true,
    description: 'A lance of green fire that burns everything standing in its path.',
    evolutions: [
      { id: 'verdant_gaze', name: 'Verdant Gaze', description: 'The gaze widens until the world is a line of green fire.',
        catalysts: [{ boon: 'evasion' }, { boon: 'expanse' }], mods: { damage: 1.5, area: 1.8 }, art: 'beam_gaze' },
      { id: 'sunlance', name: 'Sunlance', description: 'The lance turns gold, and holy, and sears the dead to ash.',
        catalysts: [{ school: 'holy' }, { status: 'sear' }], mods: { damage: 1.5 }, school: 'holy',
        set: { status: { kind: 'sear', chance: 1, power: 1, duration: 3 } }, addTags: ['holy'], art: 'beam_sun' },
    ],
  }),
};

export const WEAPON_POOL = Object.values(WEAPONS).filter((w) => w.findable).map((w) => w.id);

export const WEAPON_MAX_RANK = 8;
export const MAX_WEAPONS = 6;

export const RANK = {
  damageStep: 0.2,
  areaStep: 0.04,
  durationStep: 0.06,
  projRankA: 4,
  projRankB: 7,
};
