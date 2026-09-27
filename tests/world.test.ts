import { describe, it, expect } from 'vitest';
import { createCharacter, deriveKit, equip, makeItem, addToPack, countItem, worldTags, gainXp, compareStats, itemName } from '@/rpg/character';
import { freshWorld } from '@/world/state';
import { test as check, apply, npc, attitude, type Ctx, type Notice } from '@/world/logic';
import { advanceDay } from '@/world/simulation';
import { ARCHETYPES } from '@/content/archetypes';
import { DialogueRunner, type Conversation } from '@/world/dialogue';
import { Saves } from '@/world/save';

function ctx(bg: 'hunter' | 'scholar' | 'outcast' | 'devout' = 'hunter') {
  const ch = createCharacter({ name: 'Ashe', archetype: 'warden', background: bg, palette: 'steel', weaponItem: 'worn_oathblade', ability: 'shield_bash', startBoon: 'might' }, 1, 42);
  const world = freshWorld(42);
  const notices: Notice[] = [];
  const c: Ctx = { world, ch, notify: (n) => notices.push(n) };
  return { c, ch, world, notices };
}

describe('character', () => {
  it('starts with its archetype weapon and its background kit', () => {
    const { ch } = ctx('hunter');
    expect(ch.equipment.weapon?.def).toBe('worn_oathblade');
    expect(ch.equipment.cloak?.def).toBe('old_hunters_cloak');
    expect(ch.knowledge).toContain('beastlore');
    const kit = deriveKit(ch);
    expect(kit.weapons).toEqual([{ id: 'oathblade', rank: 1 }]);
    // The cloak's beast protection reaches the stat block.
    expect(kit.stats.getRaw('from.wolf')).toBeCloseTo(0.25);
    expect(worldTags(ch).has('beastscent')).toBe(true);
  });

  it('equipping swaps the old item back into the pack', () => {
    const { ch } = ctx();
    const staff = makeItem(ch, 'ember_staff');
    addToPack(ch, staff);
    expect(equip(ch, staff, 'weapon')).toBe(true);
    expect(ch.equipment.weapon?.def).toBe('ember_staff');
    expect(ch.pack.some((p) => p?.def === 'worn_oathblade')).toBe(true);
    expect(deriveKit(ch).weapons[0].id).toBe('cinderfall');
  });

  it('plain gear rolls affixes and names itself; compare reports differences', () => {
    const { ch } = ctx();
    const ring = makeItem(ch, 'silver_ring', { rarity: 3, seed: 7 });
    expect(ring.affixes.length).toBeGreaterThan(1);
    expect(itemName(ring)).not.toBe('Silver Ring');
    expect(compareStats(ch, ring, 'ring1').length).toBeGreaterThan(0);
  });

  it('levels grant attribute points and trait picks', () => {
    const { ch } = ctx();
    const gained = gainXp(ch, 5000);
    expect(gained).toBeGreaterThan(2);
    expect(ch.points).toBe(gained * 2);
    expect(ch.traitPicks).toBeGreaterThan(0);
  });

  it('stacks materials', () => {
    const { ch } = ctx();
    addToPack(ch, makeItem(ch, 'wolf_pelt', { qty: 3 }));
    addToPack(ch, makeItem(ch, 'wolf_pelt', { qty: 4 }));
    expect(countItem(ch, 'wolf_pelt')).toBe(7);
    expect(ch.pack.filter((p) => p?.def === 'wolf_pelt').length).toBe(1);
  });
});

describe('world logic', () => {
  it('evaluates conditions over facts, knowledge, items, relations and background', () => {
    const { c } = ctx('outcast');
    c.world.facts['beasts.population'] = 70;
    expect(check({ fact: 'beasts.population', gte: 50 }, c)).toBe(true);
    expect(check({ bg: 'outcast' }, c)).toBe(true);
    expect(check({ hasTag: 'kerchief_colors' }, c)).toBe(true);
    expect(check({ hasItem: 'lockpicks' }, c)).toBe(true);
    expect(check({ all: [{ knows: 'underworld' }, { not: { knows: 'beastlore' } }] }, c)).toBe(true);
    apply({ rel: { npc: 'rav', trust: 30 } }, c);
    expect(check({ rel: { npc: 'rav', axis: 'trust', gte: 30 } }, c)).toBe(true);
  });

  it('effects give items, gold, journal entries and traits, with notices', () => {
    const { c, ch, notices } = ctx();
    apply([{ give: 'wolf_pelt', qty: 2 }, { gold: 30 }, { quest: { id: 'beasts', entry: 'rumour' } }, { trait: 'wolf_friend' }], c);
    expect(countItem(ch, 'wolf_pelt')).toBe(2);
    expect(ch.gold).toBe(55);
    expect(c.world.quests.beasts.status).toBe('active');
    expect(ch.traits).toContain('wolf_friend');
    expect(notices.length).toBeGreaterThanOrEqual(4);
  });

  it('history reaches witnesses at once, and everyone else through gossip', () => {
    const { c } = ctx();
    apply({ history: { id: 'stole_cargo', text: 'kept the Coyle cargo', tags: ['theft'], spread: 2, sentiment: { trust: -20 }, reactions: { harlan: { trust: -60, affection: -40 } } }, witnesses: ['jory'] }, c);
    expect(npc(c.world, 'jory').memories).toContain('stole_cargo');
    expect(npc(c.world, 'harlan').trust).toBe(0);
    const social = { harlan: ['jory', 'rook'], rook: ['harlan', 'holloway'], holloway: ['rook'] };
    let r = 0.1;
    for (let d = 0; d < 6; d++) advanceDay(c, [], social, () => (r = (r * 9301 + 49297) % 233280 / 233280));
    expect(npc(c.world, 'harlan').memories).toContain('stole_cargo');
    expect(npc(c.world, 'harlan').trust).toBe(-60);
    expect(attitude(npc(c.world, 'harlan'))).toMatch(/distrusts/);
  });

  it('scheduled consequences and daily rules fire on the day', () => {
    const { c } = ctx();
    apply({ later: { days: 2, id: 'survivors_die', effect: { set: { 'caravan.survivors': 'dead' } } } }, c);
    const rules = [{ id: 'escalate', when: { fact: 'beasts.outcome', exists: false }, effect: { add: { 'beasts.severity': 1 } } }];
    advanceDay(c, rules, {});
    expect(c.world.facts['caravan.survivors']).toBeUndefined();
    advanceDay(c, rules, {});
    expect(c.world.facts['caravan.survivors']).toBe('dead');
    expect(c.world.facts['beasts.severity']).toBe(2);
  });
});

describe('dialogue', () => {
  const convo: Conversation = {
    npc: 'maeca',
    entry: [{ when: { met: 'maeca' }, node: 'again' }, { node: 'hello' }],
    nodes: {
      hello: { id: 'hello', text: 'Who are you, {name}?', choices: [
        { text: 'I read the tracks. Something drove them out.', when: { knows: 'beastlore' }, badge: 'Beastlore', effects: [{ rel: { npc: 'maeca', respect: 15 } }], goto: 'agree' },
        { text: 'Tell me about the old empire.', when: { knows: 'arcana' }, locked: 'Requires: Arcana' },
        { text: 'Goodbye.', end: true },
      ] },
      agree: { id: 'agree', text: 'Then you see it too.', choices: [{ text: 'I do.', end: true }] },
      again: { id: 'again', text: 'Back again.', choices: [{ text: 'Bye.', end: true }] },
    },
  };

  it('shows background choices with badges, locks others with reasons, remembers meeting', () => {
    const { c } = ctx('hunter');
    const run = new DialogueRunner(convo, c);
    const p = run.start()!;
    expect(p.text).toBe('Who are you, Ashe?');
    const beast = p.choices.find((x) => x.badge === 'Beastlore')!;
    expect(beast.enabled).toBe(true);
    const arcana = p.choices.find((x) => x.locked)!;
    expect(arcana.enabled).toBe(false);
    const next = run.choose(beast.index).next!;
    expect(next.text).toBe('Then you see it too.');
    expect(npc(c.world, 'maeca').respect).toBe(15);
    const again = new DialogueRunner(convo, c).start()!;
    expect(again.text).toBe('Back again.');
  });
});

describe('save', () => {
  it('round-trips character, world and location', () => {
    const { c, ch, world } = ctx();
    apply([{ set: { 'caravan.cargo': 'kept' } }, { give: 'wolf_fang_necklace' }, { rel: { npc: 'harlan', trust: -40 } }], c);
    world.day = 4;
    Saves.write(1, { playtime: 123, character: ch, world, location: { zone: 'thornhollow', x: 3, z: -7, facing: 1 } });
    const back = Saves.read(1)!;
    expect(back.character.name).toBe('Ashe');
    expect(back.world.day).toBe(4);
    expect(back.world.facts['caravan.cargo']).toBe('kept');
    expect(back.world.npcs.harlan.trust).toBe(-40);
    expect(back.character.pack.some((p) => p?.def === 'wolf_fang_necklace')).toBe(true);
    expect(back.location).toEqual({ zone: 'thornhollow', x: 3, z: -7, facing: 1 });
  });
});


describe('quest status', () => {
  it('a settled quest is never reopened by a late "active"', () => {
    const w = freshWorld(3);
    const A = ARCHETYPES.warden;
    const ch = createCharacter({ name: 'X', archetype: 'warden', background: 'hunter', palette: A.palettes[0].id, weaponItem: A.weapons[0], ability: A.abilities[0], startBoon: 'might' }, 1, 3);
    const c = { world: w, ch, notify: () => {} };
    apply({ quest: { id: 'beasts', status: 'resolved', outcome: 'cured' } }, c);
    apply({ quest: { id: 'beasts', status: 'active', entry: 'holloway_bounty' } }, c);
    expect(w.quests.beasts.status).toBe('resolved');
    expect(w.quests.beasts.entries).toContain('holloway_bounty');
  });
});

describe('standing', () => {
  it('reads the powers of the Verge from what the world holds', async () => {
    const { standings, wolvesFriendly, kerchiefsFriendly } = await import('@/content/standing');
    const { c } = ctx('hunter');
    const find = (id: string) => standings(c).find((s) => s.id === id);
    // Nothing started: only the Watch knows you.
    expect(find('pack')).toBeUndefined();
    apply([{ quest: { id: 'beasts', entry: 'rumour', status: 'active' } }, { quest: { id: 'caravan', entry: 'wreck', status: 'active' } }], c);
    expect(find('pack')?.tone).toBe('hostile');
    expect(find('kerchief')?.word).toBe('Hostile');
    expect(wolvesFriendly(c)).toBe(false);
    // Greymuzzle's peace, then the Pack's company.
    apply([{ set: { 'hollow.peace': true } }], c);
    expect(wolvesFriendly(c)).toBe(true);
    expect(find('pack')?.word).toBe('Let you pass');
    apply([{ set: { 'pack.allied': true } }], c);
    expect(find('pack')?.tone).toBe('ally');
    // A bargain with Redcowl holds until the Roost is crossed.
    apply([{ set: { redcowl: 'bargained' } }], c);
    expect(kerchiefsFriendly(c)).toBe(true);
    expect(find('kerchief')?.word).toBe('Tolerated');
    apply([{ set: { 'roost.hostile': true } }], c);
    expect(kerchiefsFriendly(c)).toBe(false);
    expect(find('kerchief')?.word).toBe('At war');
    // The Coyle Company remembers who kept its cargo.
    apply([{ set: { 'caravan.survivors': 'rescued', 'caravan.cargo': 'kept' } }], c);
    expect(find('coyle')?.word).toBe('Cheated');
  });

  it('grades how people feel, loudest first', () => {
    const { c } = ctx();
    const s = npc(c.world, 'maeca');
    s.flags.met = true;
    expect(attitude(s)).toBe('unsure of you');
    s.affection = 20; s.respect = 45;
    expect(attitude(s)).toBe('respects you, likes you');
    s.fear = 25; s.trust = -50;
    expect(attitude(s)).toBe('distrusts you, respects you');
  });
});
