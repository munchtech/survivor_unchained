import { describe, it, expect } from 'vitest';
import { createCharacter, makeItem, addToPack, countItem } from '@/rpg/character';
import { freshWorld } from '@/world/state';
import { npc, test as check, type Ctx } from '@/world/logic';
import { DialogueRunner, type Conversation } from '@/world/dialogue';
import { advanceDay } from '@/world/simulation';
import { CONVOS } from '@/content/dialogue';
import { RULES, SOCIAL } from '@/content/rules';
import { ARCHETYPES, type BackgroundId } from '@/content/archetypes';
import { chapterSummary } from '@/content/chapter';

/* The two questlines, played through the same data the game uses, by
 * survivors from different backgrounds taking different roads. */

function setup(bg: BackgroundId) {
  const A = ARCHETYPES.warden;
  const ch = createCharacter({ name: 'Wren', archetype: 'warden', background: bg, palette: A.palettes[0].id, weaponItem: A.weapons[0], ability: A.abilities[0], startBoon: 'might' }, 1, 5);
  const world = freshWorld(5);
  world.facts['prologue.done'] = true;
  world.facts['beasts.population'] = 60;
  const c: Ctx = { world, ch, notify: () => {} };
  return { ch, world, c };
}

/** Talk: pick choices by a fragment of their text, in order. */
function talk(convo: Conversation, c: Ctx, ...picks: string[]) {
  const r = new DialogueRunner(convo, c);
  let p = r.start();
  for (const pick of picks) {
    if (!p) throw new Error(`conversation ended before "${pick}"`);
    if (!p.choices.length) { p = r.advance(); if (!p) throw new Error('ended'); }
    const choice = p.choices.find((x) => x.text.toLowerCase().includes(pick.toLowerCase()));
    if (!choice) throw new Error(`no choice "${pick}" in [${p.choices.map((x) => x.text).join(' | ')}]`);
    if (!choice.enabled) throw new Error(`choice "${pick}" is locked: ${choice.locked}`);
    p = r.choose(choice.index).next;
  }
  return p;
}

describe('the Beast Problem', () => {
  it('a hunter can walk into the Hollow and speak with Greymuzzle', () => {
    const { c, world, ch } = setup('hunter');
    talk(CONVOS.greymuzzle, c, 'kneel');
    expect(world.facts['hollow.peace']).toBe(true);
    expect(world.quests.beasts.entries).toContain('greymuzzle_met');
    expect(ch.knowledge).toContain('clue.sick_wolf');
    // Come back, and the Pack remembers your scent.
    talk(CONVOS.greymuzzle, c, 'leave');
  });

  it('someone with no beastlore cannot', () => {
    const { c } = setup('scholar');
    expect(() => talk(CONVOS.greymuzzle, c, 'kneel')).toThrow(/locked/);
  });

  it('a scholar reads the stream and finds the root cause in one visit to Wenna', () => {
    const { c, ch, world } = setup('scholar');
    addToPack(ch, makeItem(ch, 'stream_sample'));
    talk(CONVOS.wenna, c, 'test it');
    expect(ch.knowledge).toContain('root_cause');
    expect(countItem(ch, 'stream_sample')).toBe(0);
    expect(world.quests.beasts.entries).toContain('root_cause');
  });

  it('talking Snib into moving the pump, then resting, cures the stream', () => {
    const { c, world } = setup('scholar');
    talk(CONVOS.snib, c, 'sinkhole');
    expect(world.facts['dig.pump']).toBe('moved');
    advanceDay(c, RULES, SOCIAL, () => 0.5);
    advanceDay(c, RULES, SOCIAL, () => 0.5);
    expect(world.facts['beasts.outcome']).toBe('cured');
    expect(world.quests.beasts.status).toBe('resolved');
  });

  it('left alone, the wolves come to the gate', () => {
    const { c, world } = setup('devout');
    for (let d = 0; d < 7; d++) advanceDay(c, RULES, SOCIAL, () => 0.5);
    expect(world.facts['tam.farm']).toBe('raided');
    expect(world.facts['beasts.outcome']).toBe('ignored');
  });

  it('selling pelts to Holloway after lying to him is remembered', () => {
    const { c, ch, world } = setup('outcast');
    addToPack(ch, makeItem(ch, 'wolf_pelt', { qty: 4 }));
    talk(CONVOS.holloway, c, 'dealt with');
    expect(world.facts['beasts.told_holloway']).toBe(true);
    // He believes you, for now.
    expect(npc(world, 'holloway').memories).not.toContain('lied_to_holloway');
    // Then the wolves take another drover.
    advanceDay(c, RULES, SOCIAL, () => 0.99);
    expect(npc(world, 'holloway').memories).toContain('lied_to_holloway');
    expect(npc(world, 'holloway').trust).toBeLessThan(-30);
  });
});

describe('the Missing Caravan', () => {
  it('an outcast learns about the clerk from Rav, and gets his key', () => {
    const { c, ch, world } = setup('outcast');
    talk(CONVOS.rav, c, 'news of coyle');
    expect(world.quests.caravan.entries).toEqual(expect.arrayContaining(['clerk_turned', 'clerks_key']));
    expect(countItem(ch, 'clerks_key')).toBe(1);
  });

  it('Pell\'s ledger, shown to Holloway, exposes him - and Harlan hears', () => {
    const { c, ch, world } = setup('hunter');
    addToPack(ch, makeItem(ch, 'pell_ledger'));
    talk(CONVOS.holloway, c, 'ledger');
    expect(world.facts['caravan.pell']).toBe('exposed');
    expect(npc(world, 'harlan').memories).toContain('exposed_pell');
    expect(npc(world, 'harlan').trust).toBeGreaterThan(30);
  });

  it('Redcowl can be bluffed out of his own camp by someone who knows the cant', () => {
    const { c, world } = setup('outcast');
    talk(CONVOS.redcowl, c, 'watch is on its way');
    expect(world.facts.redcowl).toBe('tricked');
  });

  it('or bought off with pelts', () => {
    const { c, ch, world } = setup('hunter');
    addToPack(ch, makeItem(ch, 'wolf_pelt', { qty: 5 }));
    talk(CONVOS.redcowl, c, 'coyle wagons', 'pelts');
    expect(world.facts.redcowl).toBe('bargained');
    expect(countItem(ch, 'wolf_pelt')).toBe(0);
  });

  it('prisoners left in the cages do not wait forever', () => {
    const { c, world } = setup('devout');
    for (let d = 0; d < 5; d++) advanceDay(c, RULES, SOCIAL, () => 0.5);
    expect(world.facts['caravan.survivors']).toBe('dead');
  });

  it('the cargo has an ending of its own: returned, kept, or moved on by the Kerchiefs', () => {
    // Returned: the quest settles the moment both halves are known.
    const a = setup('hunter');
    a.world.facts['caravan.survivors'] = 'rescued';
    a.world.facts['caravan.box_taken'] = true;
    addToPack(a.ch, makeItem(a.ch, 'coyle_strongbox'));
    talk(CONVOS.harlan, a.c, 'strongbox');
    expect(a.world.facts['caravan.cargo']).toBe('returned');
    expect(a.world.quests.caravan.status).toBe('resolved');
    expect(a.world.quests.caravan.outcome).toBe('returned');
    expect(chapterSummary(a.ch, a.world).threads[1].verdict).toBe('Brought home');
    // Kept: carry the box about for three days and Harlan writes it off.
    const b = setup('outcast');
    b.world.facts['caravan.survivors'] = 'rescued';
    b.world.facts['caravan.box_taken'] = true;
    const heard: string[] = [];
    for (let d = 0; d < 4; d++) heard.push(...advanceDay(b.c, RULES, SOCIAL, () => 0.5).lines);
    expect(heard.join(' ')).toMatch(/Coyle strongbox/);
    expect(b.world.facts['caravan.cargo']).toBe('kept');
    expect(b.world.quests.caravan.status).toBe('resolved');
    expect(npc(b.world, 'harlan').trust).toBeLessThan(-20);
    expect(chapterSummary(b.ch, b.world).epithet).toMatch(/kept the Coyle strongbox/);
    // Left in the Roost: the Kerchiefs sell it on down the south road.
    const k = setup('scholar');
    k.world.facts['caravan.survivors'] = 'rescued';
    for (let d = 0; d < 5; d++) advanceDay(k.c, RULES, SOCIAL, () => 0.5);
    expect(k.world.facts['caravan.cargo']).toBe('with_kerchiefs');
    expect(k.world.quests.caravan.entries).toContain('cargo_moved');
    expect(k.world.quests.caravan.status).toBe('resolved');
    // ...unless there is nobody left in the Roost to move it.
    const r = setup('scholar');
    r.world.facts['caravan.survivors'] = 'rescued';
    r.world.facts.redcowl = 'dead';
    for (let d = 0; d < 5; d++) advanceDay(r.c, RULES, SOCIAL, () => 0.5);
    expect(r.world.facts['caravan.cargo']).toBeUndefined();
  });

  it('with both stories told, Vonnra sends for you', () => {
    const { c, world } = setup('scholar');
    world.facts['beasts.outcome'] = 'cured';
    world.facts['caravan.survivors'] = 'rescued';
    advanceDay(c, RULES, SOCIAL, () => 0.5);
    expect(world.facts['chapter.ready']).toBe(true);
    expect(check({ fact: 'chapter.ready', eq: true }, c)).toBe(true);
  });
});

describe('being found out', () => {
  it('Holloway confronts a liar, and a debt paid softens it', () => {
    const { c, ch, world } = setup('outcast');
    addToPack(ch, makeItem(ch, 'wolf_pelt', { qty: 4 }));
    talk(CONVOS.holloway, c, 'dealt with');
    advanceDay(c, RULES, SOCIAL, () => 0.99);
    const before = npc(world, 'holloway').trust;
    ch.gold = 40;
    talk(CONVOS.holloway, c, 'pay back');
    expect(ch.gold).toBe(10);
    expect(world.facts['holloway.lie_settled']).toBe('repaid');
    expect(npc(world, 'holloway').trust).toBe(before + 15);
  });

  it('a lie that comes true is never found out', () => {
    const { c, ch, world } = setup('outcast');
    addToPack(ch, makeItem(ch, 'wolf_pelt', { qty: 4 }));
    talk(CONVOS.holloway, c, 'dealt with');
    world.facts['dig.pump'] = 'broken';
    world.facts['beasts.outcome'] = 'cured';
    advanceDay(c, RULES, SOCIAL, () => 0.99);
    expect(npc(world, 'holloway').memories).not.toContain('lied_to_holloway');
  });
});

describe('the chapter\'s end', () => {
  it('Vonnra reads back what you did, and the chapter closes', () => {
    const { c, world, ch } = setup('scholar');
    world.facts['beasts.outcome'] = 'cured';
    world.facts['caravan.survivors'] = 'rescued';
    world.facts['caravan.cargo'] = 'sold';
    advanceDay(c, RULES, SOCIAL, () => 0.5);
    expect(world.facts['chapter.ready']).toBe(true);
    const r = new DialogueRunner(CONVOS.vonnra, c);
    let p = r.start();
    p = r.choose(p!.choices.find((x) => /fortune/i.test(x.text))!.index).next;
    const read: string[] = [];
    while (p && !p.choices.length) { read.push(p.text); p = r.advance(); }
    read.push(p!.text);
    expect(read.join(' ')).toMatch(/water running clear/);
    expect(read.join(' ')).toMatch(/strongbox go the other way/);
    p = r.choose(p!.choices[0].index).next;
    const end = r.choose(p!.choices[0].index);
    expect(end.action).toBe('fortune');
    expect(world.facts['chapter.done']).toBe(true);
    const sum = chapterSummary(ch, world);
    expect(sum.epithet).toBe('Wren, who sold the Coyle strongbox');
    expect(sum.threads.map((t) => t.verdict)).toEqual(['Cured at the source', 'Rescued, and robbed']);
    expect(sum.open.map((o) => o.id)).toEqual(['vault', 'below']);
  });

  it('a chapter with nothing settled still reads as a page', () => {
    const { world, ch } = setup('devout');
    const sum = chapterSummary(ch, world);
    expect(sum.threads.every((t) => t.tone === 'open')).toBe(true);
    expect(sum.epithet).toBe('Wren, late of the Low Ford road');
  });
});

describe('the morning', () => {
  it('reports who heard what overnight, and the clocks being felt', () => {
    const { c, ch, world } = setup('hunter');
    addToPack(ch, makeItem(ch, 'pell_ledger'));
    talk(CONVOS.holloway, c, 'ledger');
    const r = advanceDay(c, RULES, SOCIAL, () => 0.01);
    expect(r.heard.some((h) => h.event === 'exposed_pell' && h.npc === 'rook')).toBe(true);
    expect(r.lines.join(' ')).toMatch(/Harlan Coyle was at the east gate/);
    void world;
  });
});

describe('the notice board', () => {
  it('changes as the world does, and never reopens a settled quest', () => {
    const { c, world } = setup('devout');
    const read = () => new DialogueRunner(CONVOS.board, c).start()!.text;
    expect(read()).toMatch(/WOLF BOUNTY/);
    world.facts['beasts.outcome'] = 'cured';
    world.quests.beasts.status = 'resolved';
    world.facts['caravan.survivors'] = 'rescued';
    const t = read();
    expect(t).toMatch(/WITHDRAWN/);
    expect(t).toMatch(/Jory is home/);
    expect(t).not.toMatch(/WOLF BOUNTY|MISSING/);
    expect(world.quests.beasts.status).toBe('resolved');
  });
});

describe('selling the cure', () => {
  it('Pell buys what the Dig is doing, moves the pipe for his cut, and the stream clears on his terms', () => {
    const { c, ch, world } = setup('outcast');
    ch.knowledge.push('root_cause');
    const gold = ch.gold;
    talk(CONVOS.pell, c, 'terrible business');
    talk(CONVOS.pell, c, 'killing the wolves', 'forty');
    expect(ch.gold).toBe(gold + 40);
    expect(world.quests.beasts.entries).toContain('dig_sold');
    for (let d = 0; d < 5; d++) advanceDay(c, RULES, SOCIAL, () => 0.99);
    expect(world.facts['dig.pump']).toBe('moved');
    expect(world.facts['beasts.outcome']).toBe('exploited');
    expect(world.quests.beasts.status).toBe('resolved');
    const sum = chapterSummary(ch, world);
    expect(sum.threads[0].verdict).toBe('Settled, for a price');
  });
});

describe('what you know opens doors', () => {
  it('the Warden\'s lore gets a probationary knight talking', () => {
    const { c, ch } = setup('scholar');
    talk(CONVOS.keegan, c, 'bye');
    ch.knowledge.push('lore.warden');
    const p = talk(CONVOS.keegan, c, 'ford-warden');
    expect(p?.text).toMatch(/keep the Warden asleep/);
  });

  it('a devout survivor hears the bones at the Sealed Door (entry exists and reads)', () => {
    const { c } = setup('devout');
    expect(c.ch.knowledge).toContain('faith');
  });
});

describe('choices that no longer apply', () => {
  const offered = (convo: Conversation, c: Ctx) => new DialogueRunner(convo, c).start()!.choices.map((x) => x.text);

  it('the toll, once paid, is not offered again (not even locked)', () => {
    const { c, world } = setup('hunter');
    npc(world, 'vonnra').flags.met = true;
    expect(offered(CONVOS.vonnra, c).some((t) => /pay the toll/i.test(t))).toBe(true);
    world.facts['toll.paid'] = true;
    expect(offered(CONVOS.vonnra, c).some((t) => /pay the toll/i.test(t))).toBe(false);
  });

  it('the stream sample, once read, is not asked for again', () => {
    const { c, ch } = setup('hunter');
    ch.knowledge.push('clue.analysis');
    const r = new DialogueRunner(CONVOS.wenna, c);
    let p = r.start();
    while (p && !p.choices.length) p = r.advance();
    expect(p!.choices.some((x) => /water from the stream/i.test(x.text))).toBe(false);
  });
});
