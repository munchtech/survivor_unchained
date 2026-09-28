import { describe, it, expect } from 'vitest';
import { createCharacter, makeItem, addToPack } from '@/rpg/character';
import { freshWorld } from '@/world/state';
import { apply, type Ctx } from '@/world/logic';
import { objectives } from '@/content/objectives';
import { ARCHETYPES } from '@/content/archetypes';

/* The corner of the screen: what it tells you to do, as the quests move. */

function setup() {
  const A = ARCHETYPES.warden;
  const ch = createCharacter({ name: 'Wren', archetype: 'warden', background: 'hunter', palette: A.palettes[0].id, weaponItem: A.weapons[0], ability: A.abilities[0], startBoon: 'might' }, 1, 5);
  const world = freshWorld(5);
  world.facts['prologue.done'] = true;
  const c: Ctx = { world, ch, notify: () => {} };
  return { ch, world, c };
}
const steps = (c: Ctx, id: string) => objectives(c).find((o) => o.id === id)?.steps.map((s) => s.text) ?? [];

describe('objectives', () => {
  it('point a newcomer at the inn, then at whoever the talk was about', () => {
    const { c } = setup();
    expect(steps(c, 'arrival')[0]).toMatch(/Rook/);
    // Rook's news: both stories heard, neither taken up.
    apply([{ quest: { id: 'beasts', entry: 'rumour' } }, { quest: { id: 'caravan', entry: 'harlan_plea' } }], c);
    expect(steps(c, 'arrival')).toEqual([]);
    expect(steps(c, 'beasts')).toEqual(expect.arrayContaining([expect.stringMatching(/Holloway, on the square/)]));
    expect(steps(c, 'caravan')).toEqual(expect.arrayContaining([expect.stringMatching(/Harlan Coyle, outside Coyle Trading/)]));
  });

  it('follow the Beast Problem whichever way it is walked', () => {
    const { c, ch } = setup();
    apply({ quest: { id: 'beasts', status: 'active', entry: 'holloway_bounty' } }, c);
    expect(steps(c, 'beasts')[0]).toMatch(/what is wrong with the wolves/);
    // The pipe first, before anyone asked for water.
    apply([{ learn: ['clue.pipe', 'clue.lampling_tracks'] }, { give: 'slurry_sample' }], c);
    expect(steps(c, 'beasts')[0]).toMatch(/Fill a bottle at the green water/);
    addToPack(ch, makeItem(ch, 'stream_sample'));
    expect(steps(c, 'beasts')[0]).toMatch(/to Wenna/);
    apply([{ take: 'stream_sample' }, { learn: ['clue.analysis', 'root_cause'] }], c);
    expect(steps(c, 'beasts')[0]).toMatch(/Stop the slurry at the Dig/);
    apply({ set: { 'dig.pump': 'broken' } }, c);
    expect(steps(c, 'beasts')[0]).toMatch(/a few days to run clear/);
  });

  it('say how long the cages will hold, and follow the caravan to its end', () => {
    const { c, world } = setup();
    apply({ quest: { id: 'caravan', status: 'active', entry: 'harlan_plea' } }, c);
    expect(steps(c, 'caravan')[0]).toMatch(/Search the Old Road/);
    apply({ quest: { id: 'caravan', entry: 'wreck' } }, c);
    expect(steps(c, 'caravan')[0]).toMatch(/wheel ruts/);
    world.facts['caravan.days'] = 3;
    apply({ quest: { id: 'caravan', entry: 'roost_found' } }, c);
    expect(steps(c, 'caravan')[0]).toMatch(/cages.*not last another night/);
    apply({ set: { 'caravan.survivors': 'rescued' } }, c);
    expect(steps(c, 'caravan')).toEqual(expect.arrayContaining([expect.stringMatching(/Tell Harlan/), expect.stringMatching(/strongbox is still in the Roost/)]));
    apply([{ set: { 'caravan.cargo': 'returned' } }, { quest: { id: 'caravan', status: 'resolved' } }], c);
    expect(objectives(c).find((o) => o.id === 'caravan')).toBeUndefined();
  });
});
