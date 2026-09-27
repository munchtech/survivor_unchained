import type { Game } from '../game';
import type { ZoneRuntime, Interactable, MapMark } from '../zone';
import { NpcActor, PlateLayer } from '../actors';
import { buildVerge, V } from '@/world/zones/verge';
import { PRESETS } from '@/render/atmosphere';
import { NPCS, OUTSIDERS } from '@/content/npcs';
import type { Battle } from '@/sim/battle';
import type { Enemy, PickupKind } from '@/sim/entities';
import type { School } from '@/sim/types';
import { test } from '@/world/logic';
import { boss, say, toast, announce, objectives, hint, type Objective } from '@/ui/store';
import { Input } from '@/core/input';
import { QUESTS } from '@/content/quests';
import { hist } from '@/content/dialogue/town';

/* Thornhollow Verge, alive.
 *
 * The wood is dangerous in proportion to what has been left undone: while
 * the Pack is sick and nobody has made peace with it, wolves come in packs;
 * the road east belongs to whoever has scared the Kerchiefs least; the
 * diggers mind their pump and nothing else unless you give them a reason.
 * Every group here reads the world before it decides what you are - the
 * same wolf is an enemy, a stranger or a friend depending on what you did
 * last week.
 *
 * The places the quests need are here too, each with the handful of things
 * a clever player might try. */

type Pickup = { kind: PickupKind; ref: string | null; value: number; persistent?: boolean };

export function verge(g: Game): ZoneRuntime {
  const built = buildVerge(g.r.spec.grassDensity);
  const kit = built.kit;
  const root = built.zone.root;
  const heightAt = (x: number, z: number) => kit.y(x, z);
  const w = () => g.world!;
  const F = (k: string) => w().facts[k];
  const ctx = () => g.ctx!;
  let b: Battle | null = null;
  const actors = new Map<string, NpcActor>();
  const plates = new PlateLayer(document.getElementById('stage')!);
  let spawnT = 4, surgeT = 70;
  const seen = new Set<string>();
  const cagesOpen = [false, false, false];
  const brambleHp = built.brambles.map(() => 260);
  let dispT = 0;
  let greymuzzle: Enemy | null = null, redcowl: Enemy | null = null, snib: Enemy | null = null, nemesis: Enemy | null = null;
  const roostCrew: Enemy[] = [], digCrew: Enemy[] = [];
  let hollowSpawned = false, roostSpawned = false, digSpawned = false, sinkSpawned = false;
  let chargeT = -1;
  let restUsed = false;

  /* ------------------------------------------------------ dispositions -- */

  const wolvesFriendly = () => !F('hollow.hostile') && (!!F('hollow.peace') || !!F('pack.allied') || F('beasts.outcome') === 'cured' || g.ch!.traits.includes('wolf_friend'));
  const kerchiefsFriendly = () => !F('roost.hostile') && (test({ hasTag: 'kerchief_colors' }, ctx()) || F('redcowl') === 'bargained' || F('caravan.pell') === 'ally' || (test({ knows: 'pass.redcowl' }, ctx()) && !!w().npcs.redcowl?.flags.met));
  const diggersFriendly = () => !F('dig.hostile');
  // At their own den, the Pack holds off for someone who knows how to come
  // to it (a hunter's lore, Maeca's advice, a wolf's fang worn openly):
  // long enough for Greymuzzle to come out and look.
  const hollowCalm = () => wolvesFriendly() || (!F('hollow.hostile') && test({ any: [{ knows: 'beastlore' }, { knows: 'hint.greymuzzle' }, { hasTag: 'wolf_fang' }] }, ctx()));
  const alive = (e: Enemy | null) => !!e && e.alive && e.state !== 'dying';

  const setDisposition = (e: Enemy) => {
    if (e.faction === 'pack' && e.disposition !== 'ally') {
      const den = e.tag === 'hollow' || e.tag === 'greymuzzle';
      e.disposition = (den ? hollowCalm() : wolvesFriendly()) ? 'neutral' : 'hostile';
    }
    if (e.faction === 'kerchief') e.disposition = kerchiefsFriendly() ? 'neutral' : 'hostile';
    if (e.faction === 'lampling' && e.tag?.startsWith('dig')) e.disposition = diggersFriendly() ? 'neutral' : 'hostile';
  };
  const turnHostile = (key: 'roost.hostile' | 'dig.hostile' | 'hollow.hostile', text?: string) => {
    if (F(key)) return;
    w().facts[key] = true;
    b?.enemies.forEach((e) => { if (e.alive) setDisposition(e); });
    if (text) announce(text, undefined, 'danger', 2.4);
  };

  const level = () => 2 + Math.floor(w().day / 2) + Math.floor((b?.ember.level ?? 1) / 6);

  /* ------------------------------------------------------------ spawns -- */

  const openGround = (x: number, z: number) => !!b && !b.collision.blocked(x, z, 0.7) && Math.abs(x) < 136 && Math.abs(z) < 136 && built.streamDist(x, z) > 3;

  const spawnGroup = (def: string, n: number, cx: number, cz: number, spread: number, o: { tag?: string; home?: number; style?: 'walk' | 'burrow' | 'rise' } = {}) => {
    const out: Enemy[] = [];
    for (let i = 0; i < n; i++) {
      for (let t = 0; t < 8; t++) {
        const a = Math.random() * Math.PI * 2, d = Math.random() * spread;
        const x = cx + Math.cos(a) * d, z = cz + Math.sin(a) * d;
        if (!openGround(x, z)) continue;
        const e = b!.spawnEnemy(def, x, z, { level: level(), style: o.style ?? 'walk', tag: o.tag, home: o.home ? { x: cx, z: cz, leash: o.home } : undefined });
        if (e) { setDisposition(e); out.push(e); }
        break;
      }
    }
    return out;
  };

  /** The wood's own pressure: what comes at you depends on where you are. */
  const director = (dt: number) => {
    if (!b) return;
    const p = b.player;
    spawnT -= dt; surgeT -= dt;
    // Quiet near the gate and around a lit fire.
    if (p.x < -112 || (Math.hypot(p.x - V.post.x, p.z - V.post.z) < 16 && built.postFire.on)) return;
    let hostile = 0;
    b.enemies.forEach((e) => { if (e.alive && e.disposition === 'hostile') hostile++; });
    const night = w().time === 'night';
    // More of them as the ember burns brighter: the wood notices.
    const ember = b.ember.level;
    const cap = (night ? 40 : 30) + Math.min(16, ember * 1.5);
    if (spawnT <= 0 && hostile < cap) {
      spawnT = (night ? 2.8 : 3.8) * Math.max(0.6, 1 - ember * 0.025);
      const a = Math.random() * Math.PI * 2, d = 17 + Math.random() * 5;
      const x = p.x + Math.cos(a) * d, z = p.z + Math.sin(a) * d;
      const pop = Number(F('beasts.population') ?? 60);
      const nearRoost = Math.hypot(x - V.roost.x, z - V.roost.z) < 60 || (x > 30 && Math.abs(z) < 20);
      const nearDig = Math.hypot(x - V.dig.x, z - V.dig.z) < 60;
      const nearVault = Math.hypot(x - V.vault.x, z - V.vault.z) < 45;
      const r = Math.random();
      if (night && nearVault) spawnGroup(r < 0.3 ? 'risen_warrior' : 'risen', 3 + Math.floor(Math.random() * 3), x, z, 4, { style: 'rise' });
      else if (nearRoost && !kerchiefsFriendly() && F('redcowl') !== 'tricked' && F('redcowl') !== 'dead') spawnGroup(r < 0.25 ? 'pillager' : r < 0.35 ? 'bruiser' : 'footpad', 2 + Math.floor(Math.random() * 3), x, z, 4);
      // The diggers mind their pump unless given a reason; then they come up out of the ground.
      else if (nearDig && !diggersFriendly() && Math.random() < 0.7) spawnGroup('lampling', 3 + Math.floor(Math.random() * 3), x, z, 4, { style: 'burrow', tag: 'dig:crew' });
      else if (!wolvesFriendly() && Math.random() < pop / 70) {
        const sick = F('beasts.outcome') !== 'cured' && built.streamDist(x, z) < 30;
        spawnGroup(sick && r < 0.35 ? 'wolf_blighted' : 'wolf', 3 + Math.floor(Math.random() * 3 * (pop / 60)) + Math.floor(ember / 5), x, z, 4);
      } else spawnGroup('boar', 1 + Math.floor(Math.random() * 2), x, z, 3);
    }
    // Now and then, a surge: the wood noticing you.
    if (surgeT <= 0) {
      surgeT = 60 + Math.random() * 35;
      if (!wolvesFriendly() && Number(F('beasts.population') ?? 60) > 20) {
        const a = Math.random() * Math.PI * 2;
        spawnGroup('wolf', 8 + Math.min(10, b.ember.level), p.x + Math.cos(a) * 18, p.z + Math.sin(a) * 18, 5);
        b.events.emit({ t: 'bark', x: p.x + Math.cos(a) * 14, z: p.z + Math.sin(a) * 14, text: 'Howling — close!' });
        b.events.emit({ t: 'shake', amount: 0.2 });
      }
    }
  };

  /* ------------------------------------------------------------ places -- */

  const approach = (dt: number) => {
    if (!b) return;
    const p = b.player;
    const near = (pt: { x: number; z: number }, r: number) => Math.hypot(p.x - pt.x, p.z - pt.z) < r;
    void dt;
    // Wolf Hollow.
    if (!hollowSpawned && near(V.hollow, 38) && F('greymuzzle') !== 'dead') {
      hollowSpawned = true;
      greymuzzle = b.spawnEnemy('wolf_alpha', V.hollow.x, V.hollow.z, { level: level(), tag: 'greymuzzle', home: { x: V.hollow.x, z: V.hollow.z, leash: 14 } });
      if (greymuzzle) setDisposition(greymuzzle);
      spawnGroup('wolf', 5, V.hollow.x, V.hollow.z, 9, { tag: 'hollow', home: 14 });
      if (F('beasts.outcome') !== 'cured') spawnGroup('wolf_blighted', 3, V.hollow.x, V.hollow.z, 6, { tag: 'hollow', home: 8 });
      if (hollowCalm()) say('The wolves watch you come. None of them move to stop you.', undefined, 4);
      else say('Low growling from every side of the Hollow.', undefined, 3);
    }
    // Redcowl's Roost.
    if (!roostSpawned && near(V.roost, 42) && F('redcowl') !== 'tricked' && !F('roost.cleared')) {
      roostSpawned = true;
      if (!seen.has('roost')) { seen.add('roost'); g.apply([{ quest: { id: 'caravan', status: 'active', entry: 'roost_found' } }, { learn: 'hint.roost' }]); }
      roostCrew.push(...spawnGroup('footpad', 4, V.roost.x, V.roost.z + 4, 10, { tag: 'roost', home: 16 }));
      roostCrew.push(...spawnGroup('pillager', 2, V.roost.x + 6, V.roost.z - 2, 6, { tag: 'roost', home: 14 }));
      roostCrew.push(...spawnGroup('bruiser', 2, V.roost.x - 4, V.roost.z + 8, 6, { tag: 'roost', home: 12 }));
      if (!kerchiefsFriendly() && F('redcowl') !== 'dead') promoteRedcowl();
      else if (F('redcowl') !== 'dead' && F('redcowl') !== 'furious') placeRedcowl();
      if (kerchiefsFriendly()) say('Red cloth at every tent. They see your colours and go back to their dice.', undefined, 4);
    }
    if (roostSpawned && !kerchiefsFriendly() && !F('roost.hostile') && near(V.roost, 26) && roostCrew.some(alive)) turnHostile('roost.hostile', 'The Roost has seen you');
    // The Dig.
    if (!digSpawned && near(V.dig, 44) && F('dig.pump') !== 'blown') {
      digSpawned = true;
      if (!F('snib.dead')) {
        snib = b.spawnEnemy('lampling', V.pump.x + 4, V.pump.z + 3, { level: level(), tag: 'dig:snib', home: { x: V.pump.x + 4, z: V.pump.z + 3, leash: 3 } });
        if (snib) { snib.named = { title: 'Snib, Foreman', carries: [], sourceHero: '' }; setDisposition(snib); }
      }
      digCrew.push(...spawnGroup('lampling', 6, V.dig.x - 4, V.dig.z + 4, 12, { tag: 'dig', home: 16 }));
      digCrew.push(...spawnGroup('lampling_sapper', 2, V.dig.x, V.dig.z, 8, { tag: 'dig', home: 14 }));
    }
    if (digSpawned && diggersFriendly() && near(V.pump, 5) && !w().npcs.snib?.flags.met && alive(snib)) {
      b.events.emit({ t: 'bark', x: V.pump.x + 4, z: V.pump.z + 3, text: 'OI! No surface-meat past the pump!', speaker: 'Snib' });
    }
    // The Sinkhole: the ground shakes the first time you look in.
    if (!sinkSpawned && near(V.sinkhole, 24)) {
      sinkSpawned = true;
      g.apply([{ quest: { id: 'below', status: 'active', entry: 'sinkhole' } }, { quest: { id: 'below', entry: 'tremor' } }]);
      b.events.emit({ t: 'shake', amount: 0.9 });
      say('The ground shivers. At the bottom of the pit lies something pale and segmented, bigger than a house, and — probably — dead.', undefined, 6);
      const s = b.spawnEnemy('lampling', V.sinkhole.x + 15, V.sinkhole.z + 12, { level: 1, tag: 'survivor', disposition: 'neutral', home: { x: V.sinkhole.x + 15, z: V.sinkhole.z + 12, leash: 1.5 } });
      if (s) s.named = { title: 'A babbling lampling', carries: [], sourceHero: '' };
    }
    // The Vault.
    if (near(V.vault, 16) && !seen.has('vault')) {
      seen.add('vault');
      g.apply({ quest: { id: 'vault', status: 'active', entry: 'seen' } });
    }
    // Clues that need only a look.
    if (near(V.wreck, 14) && !seen.has('wreck')) { seen.add('wreck'); say('Three wagons, dragged off the road into the trees. Wolves do not drive wagons.', undefined, 4); }
  };

  const placeRedcowl = () => {
    if (actors.has('redcowl')) return;
    const a = new NpcActor(OUTSIDERS.redcowl, root, heightAt, g.barks);
    actors.set('redcowl', a);
  };
  const promoteRedcowl = () => {
    if (!b || alive(redcowl) || F('redcowl') === 'dead') return;
    const a = actors.get('redcowl');
    const x = a?.x ?? V.redcowl.x, z = a?.z ?? V.redcowl.z;
    if (a) { a.dispose(); actors.delete('redcowl'); }
    redcowl = b.spawnEnemy('enforcer', x, z, { level: level() + 1, tag: 'redcowl', home: { x, z, leash: 18 } });
    if (redcowl) { redcowl.named = { title: 'Redcowl', carries: [], sourceHero: '' }; redcowl.disposition = 'hostile'; }
  };

  /* ------------------------------------------------------ interactables -- */

  const I: Interactable[] = [
    {
      id: 'exit', x: V.entry.x - 4, z: V.entry.z, r: 5, verb: 'Travel', name: 'The Waystation',
      act: () => g.travel('waystation', 'The Waystation', 'West along the Old Road'),
    },
    {
      id: 'wreck', x: V.wreck.x - 3, z: V.wreck.z - 1, r: 3.2, verb: 'Search', name: 'The Coyle Wagons',
      when: () => !test({ quest: { id: 'caravan', entry: 'wreck' } }, ctx()),
      act: () => {
        g.apply([{ quest: { id: 'caravan', status: 'active', entry: 'wreck' } }, { give: 'caravan_manifest' }, { quest: { id: 'caravan', entry: 'manifest' } }]);
        say('Kerchief arrows in the sideboards, red-fletched. The strongbox bolts are sprung, the box gone. Under the seat: a torn manifest.', undefined, 6);
      },
    },
    {
      id: 'ruts', x: -52, z: 40, r: 3.5, verb: 'Examine', name: 'Wheel Ruts',
      when: () => !test({ quest: { id: 'caravan', entry: 'ruts' } }, ctx()),
      act: () => { g.apply([{ quest: { id: 'caravan', status: 'active', entry: 'ruts' } }, { learn: 'hint.roost' }]); say('Deep ruts, heavy wagons, driven south-east into the trees. Toward the ravine.', undefined, 4); },
    },
    {
      id: 'postfire', x: V.post.x, z: V.post.z + 0.5, r: 3, verb: 'Light', name: 'The Old Watch Fire',
      when: () => !built.postFire.on,
      act: () => { kit.setLit(built.postFire, true); say('The old fire takes. For a little while, this is a safe place.', undefined, 3.5); },
    },
    {
      id: 'postrest', x: V.post.x, z: V.post.z + 0.5, r: 3, verb: 'Rest', name: 'By the Fire',
      when: () => built.postFire.on,
      hint: () => (restUsed ? 'Once per expedition' : 'Heal, and write it down'),
      locked: () => (restUsed ? 'You have rested here already' : null),
      act: () => {
        restUsed = true;
        if (b) b.player.hp = b.maxHp;
        g.save('fire');
        toast('world', 'You rest by the fire', { sub: 'Your wounds close. Your journey is saved.' });
      },
    },
    {
      id: 'carcass', x: V.carcass.x, z: V.carcass.z, r: 3, verb: 'Examine', name: 'A Dead Wolf',
      when: () => !test({ knows: 'clue.sick_wolf' }, ctx()) || !seen.has('carcass'),
      act: () => {
        seen.add('carcass');
        const lore = test({ knows: 'beastlore' }, ctx());
        g.apply([{ learn: 'clue.sick_wolf', text: 'The wolves are sick.' }, { quest: { id: 'beasts', status: 'active', entry: 'clue.sick_wolf' } }]);
        say(lore ? 'No wound. Black gums, milky eyes, ribs like a washboard, and the belly swollen hard. It drank something that rotted it from the inside.' : 'A wolf, dead, with no wound on it. Its eyes have gone milky.', undefined, 6);
      },
    },
    {
      id: 'sample', x: V.sample.x, z: V.sample.z, r: 3.2, verb: 'Fill a bottle', name: 'The Green Water',
      when: () => !test({ hasItem: 'stream_sample' }, ctx()) && !test({ knows: 'clue.analysis' }, ctx()),
      act: () => {
        g.apply([{ give: 'stream_sample' }, { learn: 'clue.green_stream' }, { quest: { id: 'beasts', status: 'active', entry: 'clue.green_stream' } }, { quest: { id: 'beasts', entry: 'sample' } }]);
        say('The water is warm, and faintly green, and smells like a chapel lamp.', undefined, 4);
      },
    },
    {
      id: 'pipe', x: V.pipe.x, z: V.pipe.z, r: 3.2, verb: 'Examine', name: 'An Iron Pipe',
      when: () => !seen.has('pipe'),
      act: () => {
        seen.add('pipe');
        g.apply([
          { learn: ['clue.pipe', 'clue.lampling_tracks'] }, { quest: { id: 'beasts', status: 'active', entry: 'clue.pipe' } }, { quest: { id: 'beasts', entry: 'clue.lampling_tracks' } },
          { if: { not: { hasItem: 'slurry_sample' } }, then: { give: 'slurry_sample' } },
          { if: { knows: 'clue.analysis' }, then: [{ learn: 'root_cause', text: 'The Dig is poisoning the stream.' }, { quest: { id: 'beasts', entry: 'root_cause' } }] },
        ]);
        say('Riveted iron, warm to the touch, spilling glowing slurry into the stream. Small clawed prints all round it, and the drag-marks of lamps.', undefined, 6);
      },
    },
    {
      id: 'greymuzzle', x: V.hollow.x, z: V.hollow.z, r: 6, verb: 'Approach', name: 'Greymuzzle',
      when: () => alive(greymuzzle) && greymuzzle!.disposition === 'neutral',
      act: () => g.talk('greymuzzle'),
    },
    {
      id: 'redcowl', x: V.redcowl.x, z: V.redcowl.z, r: 3.2, verb: 'Talk', name: 'Redcowl',
      when: () => actors.has('redcowl') && !F('roost.hostile'),
      act: () => g.talk('redcowl'),
    },
    ...[0, 1, 2].map((i): Interactable => ({
      id: `cage${i}`, x: V.cages.x + i * 3.2, z: V.cages.z - i * 0.8 - 1.6, r: 2.4, verb: 'Open', name: 'A Cage',
      when: () => !cagesOpen[i] && F('caravan.survivors') !== 'dead',
      locked: () => {
        const watching = roostCrew.some((e) => alive(e) && Math.hypot(e.x - V.cages.x, e.z - V.cages.z) < 16);
        if (!watching || F('redcowl') === 'tricked' || F('redcowl.releases')) return null;
        return kerchiefsFriendly() ? 'Redcowl\'s men are watching the cages' : 'Too many eyes. Deal with them first';
      },
      act: () => openCage(i),
    })),
    {
      id: 'strongbox', x: V.cargo.x + 2.2, z: V.cargo.z - 1.4, r: 2.4, verb: 'Take', name: 'The Coyle Strongbox',
      when: () => !F('caravan.box_taken'),
      act: () => {
        w().facts['caravan.box_taken'] = true;
        g.apply([{ give: 'coyle_strongbox' }]);
        if (kerchiefsFriendly() && F('redcowl') !== 'bargained' && roostCrew.some(alive)) turnHostile('roost.hostile', 'Thief!');
      },
    },
    {
      id: 'snib', x: V.pump.x + 4, z: V.pump.z + 3, r: 3.2, verb: 'Talk', name: 'Snib',
      when: () => alive(snib) && snib!.disposition === 'neutral',
      act: () => g.talk('snib'),
    },
    {
      id: 'pump', x: V.pump.x, z: V.pump.z, r: 3.4, verb: 'Break', name: 'The Pump',
      when: () => !F('dig.pump') || F('dig.pump') === 'running',
      locked: () => (digCrew.concat(snib ? [snib] : []).some((e) => alive(e) && Math.hypot(e.x - V.pump.x, e.z - V.pump.z) < 14) ? 'The crew would never let you' : null),
      act: () => breakPump('broken'),
    },
    {
      id: 'charge', x: V.pump.x - 2, z: V.pump.z + 2, r: 3.4, verb: 'Set a charge', name: 'Blasting Ember',
      when: () => (!F('dig.pump') || F('dig.pump') === 'running') && test({ hasItem: 'blasting_ember' }, ctx()) && chargeT < 0,
      act: () => {
        g.apply({ take: 'blasting_ember' });
        chargeT = 3.2;
        say('The fuse fizzes. You have a few seconds. Run.', undefined, 3);
        b?.events.emit({ t: 'telegraph', id: 9001, shape: 'circle', x: V.pump.x, z: V.pump.z, radius: 9, duration: 3.2, hostile: true });
      },
    },
    {
      id: 'survivor', x: V.sinkhole.x + 15, z: V.sinkhole.z + 12, r: 3, verb: 'Talk', name: 'A Lampling',
      when: () => sinkSpawned,
      act: () => g.talk('survivor'),
    },
    {
      id: 'vaultdoor', x: V.vault.x + 1.5, z: V.vault.z + 2.5, r: 3.4, verb: 'Examine', name: 'The Sealed Door',
      act: () => {
        const reads = test({ any: [{ knows: 'arcana' }, { hasTag: 'scholar_lens' }] }, ctx());
        g.apply([{ quest: { id: 'vault', status: 'active', entry: 'seen' } }, { if: { any: [{ knows: 'arcana' }, { hasTag: 'scholar_lens' }] }, then: { quest: { id: 'vault', entry: 'script' } } }]);
        if (test({ hasItem: 'sigil_fragment' }, ctx())) say('The fragment fits one notch of the sigil. The other six are empty. The door does not care how much you want it open.', undefined, 6);
        else say(reads ? 'Old-empire script over the door: "Here the Seventh Legion buried what it could not burn." Below it, a sigil with seven notches, all empty.' : 'A door of black stone, smooth as glass, and a violet sigil you cannot read. It hums against your teeth.', undefined, 6);
      },
    },
    {
      id: 'vaultbody', x: V.vault.x + 3.8, z: V.vault.z + 3.2, r: 2.4, verb: 'Search', name: 'Bones',
      when: () => !test({ quest: { id: 'vault', entry: 'fragment' } }, ctx()),
      act: () => { g.apply([{ give: 'sigil_fragment' }, { quest: { id: 'vault', status: 'active', entry: 'fragment' } }]); say('In the bones of one hand, a wedge of black stone cut to fit something.', undefined, 4); },
    },
    {
      id: 'vaultprints', x: V.vault.x + 0.5, z: V.vault.z + 5, r: 2.6, verb: 'Look at', name: 'The Ground',
      when: () => !test({ quest: { id: 'vault', entry: 'bootprints' } }, ctx()),
      act: () => { g.apply({ quest: { id: 'vault', status: 'active', entry: 'bootprints' } }); say('Bootprints in the mud, fresh, going up to the door. None coming away.', undefined, 4); },
    },
    {
      id: 'circlet', x: V.grove.x, z: V.grove.z - 1, r: 2.6, verb: 'Take', name: 'Something Silver',
      when: () => !F('grove.circlet'),
      act: () => {
        g.apply([
          { set: { 'grove.circlet': true } }, { give: 'moonsilver_circlet' },
          hist('found_grove', 'found the Moon Grove, and what was hidden in it', ['secret', 'wolves'], 0),
        ]);
        say('Under the brambles, where the wolves go when one of them is dying: a circlet of moonsilver, cold as snow.', undefined, 5);
      },
    },
    ...[0, 1, 2].map((i): Interactable => ({
      id: `petal${i}`, x: V.grove.x - 4 + i * 4, z: V.grove.z + 4 - i, r: 2.2, verb: 'Gather', name: 'Moonpetal',
      when: () => !w().zones.verge?.[`petal${i}`],
      locked: () => (w().time === 'night' ? null : 'Closed. It opens only at night'),
      act: () => { g.apply([{ zone: { id: 'verge', key: `petal${i}`, value: true } }, { give: 'moonpetal' }]); },
    })),
  ];

  /* ------------------------------------------------------------ events -- */

  const openCage = (i: number) => {
    cagesOpen[i] = true;
    built.cageBars[i].visible = false;
    say(['A teamster, thin and grey, stumbles out and grips your arm.', 'A woman who will not stop saying thank you.', 'A young man: "Jory. Jory Coyle. Is my uncle —? Is he —?"'][i], undefined, 4);
    if (cagesOpen.every(Boolean)) {
      g.apply([
        { set: { 'caravan.survivors': 'rescued' } }, { quest: { id: 'caravan', entry: 'survivors_freed' } },
        hist('freed_teamsters', 'freed the Coyle teamsters from the Kerchief cages', ['rescue', 'caravan'], 2, { affection: 10 }, { harlan: { affection: 40, trust: 30 }, holloway: { respect: 15 } }),
      ]);
    }
  };

  const breakPump = (how: 'broken' | 'blown') => {
    if (F('dig.pump') === 'broken' || F('dig.pump') === 'blown' || F('dig.pump') === 'moved') return;
    built.pumpWheel.userData.stopped = true;
    const src = kit.sources.find((s) => Math.hypot(s.x - V.pump.x, s.z - V.pump.z) < 1);
    if (src) kit.setLit(src, false);
    g.apply([
      { set: { 'dig.pump': how } }, { quest: { id: 'beasts', entry: how === 'blown' ? 'pump_blown' : 'pump_broken' } },
      hist(how === 'blown' ? 'blew_dig' : 'broke_pump', how === 'blown' ? 'blew the Dig\'s powder and half the hillside with it' : 'wrecked the Dig\'s pump', ['beasts', 'lampling'], 2, { respect: 10 }, { wenna: { respect: 20 }, maeca: { respect: 20 } }),
    ]);
    if (how === 'broken') say('Something snaps inside the pump with a sound like a bone. The wheel stops. The slurry stops.', undefined, 4);
  };

  const explode = (x: number, z: number, r: number) => {
    if (!b) return;
    b.events.emit({ t: 'explosion', x, z, radius: r, school: 'fire', power: 2.5 });
    b.events.emit({ t: 'shake', amount: 1 });
    b.explode(x, z, r, 120, 'fire', ['explosion', 'area'], null);
    if (Math.hypot(b.player.x - x, b.player.z - z) < r) b.hurtPlayer(40, 'fire', 'the blast', null);
  };

  const onHitProp = (tag: string, id: number, school: School, dmg: number, x: number, z: number) => {
    if (tag === 'powder' && school === 'fire') {
      b?.collision.remove(id);
      explode(x, z, 7);
      if (Math.hypot(x - V.dig.x, z - V.dig.z) < 20) { breakPump('blown'); turnHostile('dig.hostile'); }
      if (Math.hypot(x - V.roost.x, z - V.roost.z) < 30) {
        turnHostile('roost.hostile');
        if (!cagesOpen.every(Boolean) && F('caravan.survivors') !== 'rescued') {
          g.apply([{ set: { 'caravan.survivors': 'dead' } }, { quest: { id: 'caravan', entry: 'survivors_dead' } }, hist('burned_roost', 'set the Roost burning with the prisoners still in their cages', ['caravan'], 2, { trust: -10 }, { harlan: { trust: -60, affection: -60 } })]);
          say('The fire takes the tents, and the cages with them. There is screaming, and then there is not.', undefined, 6);
        }
      }
      return;
    }
    const m = /^bramble:(\d)$/.exec(tag);
    if (m) {
      const i = Number(m[1]);
      brambleHp[i] -= school === 'fire' ? 1e9 : dmg;
      if (brambleHp[i] <= 0 && built.brambles[i].mesh.visible) {
        const br = built.brambles[i];
        br.mesh.visible = false;
        b?.collision.remove(br.collider);
        b?.events.emit({ t: 'explosion', x: br.x, z: br.z, radius: 2.4, school: school === 'fire' ? 'fire' : 'nature', power: 0.8 });
        if (!seen.has('grove')) { seen.add('grove'); say(school === 'fire' ? 'The brambles go up like paper. Beyond them, a glade full of pale light.' : 'You hack a way through the brambles. Beyond them, a glade full of pale light.', undefined, 5); }
      }
    }
    void x; void z;
  };

  /* ---------------------------------------------------------- the dead -- */

  const onKill = (e: Enemy, byPlayer: boolean) => {
    if (!byPlayer) return;
    const f = w().facts;
    if (e.def.family === 'wolf') {
      f['beasts.population'] = Math.max(0, Number(f['beasts.population'] ?? 60) - (e.tag === 'greymuzzle' ? 20 : 1));
      f['verge.wolf_kills'] = Number(f['verge.wolf_kills'] ?? 0) + 1;
      if (Number(f['verge.wolf_kills']) === 15) g.apply(hist('wolf_slaughter', 'killed a great many wolves in the Verge', ['beasts', 'wolves'], 2, undefined, { maeca: { affection: -20 }, brannoc: { respect: 5 }, holloway: { respect: 10 } }));
      if (e.disposition === 'neutral' || e.provoked) turnHostile('hollow.hostile');
    }
    if (e.def.family === 'kerchief') f['verge.kerchief_kills'] = Number(f['verge.kerchief_kills'] ?? 0) + 1;
    if (e.tag === 'greymuzzle') {
      greymuzzle = null;
      g.apply([{ set: { greymuzzle: 'dead' } }, { quest: { id: 'beasts', entry: 'alpha_dead' } }, hist('killed_greymuzzle', 'killed Greymuzzle, the old alpha of the Pack', ['beasts', 'wolves'], 2, undefined, { maeca: { affection: -50, respect: -20 }, holloway: { respect: 20 } })]);
      boss.value = null;
    }
    if (e.tag === 'redcowl') {
      redcowl = null;
      g.apply([{ set: { redcowl: 'dead' } }, hist('killed_redcowl', 'killed Redcowl in his own camp', ['kerchief', 'caravan'], 2, { fear: 10 }, { holloway: { respect: 25 }, rav: { affection: -20 } })]);
      boss.value = null;
      if (!roostCrew.some(alive)) w().facts['roost.cleared'] = true;
    }
    if (e.tag === 'dig:snib') { snib = null; w().facts['snib.dead'] = true; turnHostile('dig.hostile'); }
    if (e.tag?.startsWith('dig')) turnHostile('dig.hostile');
    if (e.tag === 'roost' && e.disposition !== 'hostile') turnHostile('roost.hostile');
    if (e === nemesis) {
      const n = w().nemesis!;
      n.killed = true;
      for (const it of n.carries) g.giveItem(it.def, it.qty);
      g.apply(hist('nemesis_slain', `put down ${n.title}, and took back what it took`, ['revenge'], 2, { respect: 10 }));
      nemesis = null;
      boss.value = null;
      announce('Taken back', n.title, 'boon', 3.5);
    }
  };

  const onLoot = (e: Enemy): Pickup[] => {
    const out: Pickup[] = [];
    const r = Math.random();
    if (e.def.loot === 'wolf' && r < 0.55) out.push({ kind: 'material', ref: 'wolf_pelt', value: 1 });
    if (e.def.loot === 'alpha') out.push({ kind: 'item', ref: 'greymuzzle_fang', value: 1, persistent: true }, { kind: 'material', ref: 'wolf_pelt', value: 3 });
    if (e.def.loot === 'boar' && r < 0.5) out.push({ kind: 'material', ref: 'boar_hide', value: 1 });
    if (e.def.loot === 'kerchief' && r < 0.3) out.push({ kind: 'material', ref: 'kerchief_cloth', value: 1 });
    if (e.def.family === 'lampling' && r < 0.18) out.push({ kind: 'material', ref: 'ember_shard', value: 1 });
    if (e.def.family === 'undead' && r < 0.25) out.push({ kind: 'material', ref: 'bone_dust', value: 1 });
    if (e.elite && e.def.loot === 'elite') {
      const plain = ['iron_helm', 'chain_shirt', 'silver_ring', 'bone_amulet', 'travelers_cloak'];
      out.push({ kind: 'item', ref: plain[Math.floor(Math.random() * plain.length)], value: 1, persistent: true });
    }
    return out;
  };

  /* ------------------------------------------------------------ runtime -- */

  const tracker = (): Objective[] => {
    const out: Objective[] = [];
    for (const id of ['beasts', 'caravan']) {
      const q = w().quests[id];
      if (!q || q.status !== 'active') continue;
      const last = q.entries.slice(-1).map((e) => QUESTS[id].entries[e]).filter(Boolean);
      out.push({ id, title: QUESTS[id].name, tone: 'main', steps: last.map((t) => ({ text: t.length > 90 ? `${t.slice(0, 88)}…` : t })) });
    }
    return out;
  };

  let trackT = 0;
  return {
    id: 'verge', name: 'Thornhollow Verge', region: 'East of the Waystation', build: built.zone, combat: true,
    actors,
    arrival: (from) => (from === 'waystation' || !from ? { x: V.entry.x + 4, z: V.entry.z, facing: Math.PI / 2 } : { x: V.entry.x + 4, z: V.entry.z }),
    timeOf: (wd) => wd.time,
    begin: (battle) => {
      b = battle;
      const wd = w();
      g.scene.atmo.set(PRESETS[wd.time === 'night' ? 'night' : wd.time === 'dusk' ? 'dusk' : wd.time === 'dawn' ? 'dawn' : 'day']);
      // Who is out today.
      // Maeca hunts here by day, once you have met her in town.
      if (wd.time !== 'night' && F('beasts.outcome') !== 'slaughtered' && wd.npcs.maeca?.flags.met) {
        const m = new NpcActor({ ...NPCS.maeca, spot: { x: V.blind.x + 2.6, z: V.blind.z + 4.2, facing: 0.4 } }, root, heightAt, g.barks);
        actors.set('maeca', m);
        I.push({ id: 'talk:maeca', x: m.x, z: m.z, r: 2.8, verb: 'Talk', name: 'Maeca Barefoot', act: () => g.talk('maeca') });
      }
      if (F('dig.pump') && F('dig.pump') !== 'running') built.pumpWheel.userData.stopped = true;
      // Your wolves, if the Pack runs with you.
      if (F('pack.allied')) {
        for (let i = 0; i < 4; i++) {
          const e = battle.spawnEnemy('wolf', V.entry.x + 6 + i, V.entry.z + 2, { level: level(), disposition: 'ally', faction: 'ally', tag: 'packmate' });
          if (e) e.named = { title: 'Of the Pack', carries: [], sourceHero: '' };
        }
        say('Four grey shapes fall in beside you at the edge of the wood.', undefined, 4);
      }
      // What you left behind, and what took it.
      const c = wd.corpse;
      if (c && c.zone === 'verge') {
        kit.prop('halloween', 'gravemarker_B', c.x, c.z, { rot: 0.3, scale: 0.7 });
        const glow = kit.flameGlow(c.x, heightAt(c.x, c.z) + 0.5, c.z, 0.08, '#ffd890');
        kit.source(c.x, heightAt(c.x, c.z) + 1.4, c.z, 0xffc070, 6, 9, 0.1, [glow]);
        I.push({
          id: 'corpse', x: c.x, z: c.z, r: 2.6, verb: 'Recover', name: `${c.heroName}'s belongings`,
          when: () => !!w().corpse,
          act: () => {
            const cc = w().corpse!;
            g.apply([{ gold: cc.gold }]);
            for (const it of cc.items) g.giveItem(it.def, it.qty);
            w().corpse = null;
            glow.visible = false;
            say('Where you fell. The ground has kept your things for you, mostly.', undefined, 4);
          },
        });
      }
      const n = wd.nemesis;
      if (n && n.zone === 'verge' && !n.killed) {
        const at = c && c.zone === 'verge' ? c : { x: V.post.x + 20, z: V.post.z - 20 };
        nemesis = battle.spawnEnemy(n.def, at.x + 6, at.z + 6, { level: n.level, elite: true, tag: 'nemesis', home: { x: at.x, z: at.z, leash: 30 } });
        if (nemesis) nemesis.named = { title: n.title, carries: n.carries.map((i) => i.def), sourceHero: n.heroName };
      }
      g.announceZone();
      // The first time out here: the wood is big, and there is a map.
      if (!wd.facts['tip.verge_map']) {
        wd.facts['tip.verge_map'] = true;
        setTimeout(() => {
          hint.value = { id: 'verge_map', title: 'The map', text: 'The Verge is wide and the trees close in. The map fills in as you walk, and marks what you have found.', keys: [Input.keyLabel('map')] };
          setTimeout(() => { if (hint.value?.id === 'verge_map') hint.value = null; }, 10000);
        }, 5000);
      }
      objectives.value = tracker();
    },
    step: (dt) => {
      director(dt);
      approach(dt);
      // Peace made in a conversation reaches everyone already out there;
      // anyone you have struck stays angry.
      dispT -= dt;
      if (dispT <= 0 && b) {
        dispT = 0.5;
        b.enemies.forEach((e) => { if (e.alive && !e.provoked && e.disposition !== 'ally') setDisposition(e); });
      }
      if (chargeT > 0) {
        chargeT -= dt;
        if (chargeT <= 0) {
          explode(V.pump.x, V.pump.z, 9);
          breakPump('blown');
          turnHostile('dig.hostile');
          chargeT = -1;
        }
      }
    },
    frame: (dt) => {
      if (!b) return;
      const p = b.player;
      for (const a of actors.values()) a.update(dt, p.x, p.z);
      // Named creatures carry their names over their heads; the one you
      // are fighting gets a bar.
      const items = [] as Array<{ id: string; x: number; y: number; z: number; info: { name: string; role?: string } }>;
      for (const [id, a] of actors) items.push({ id, x: a.x, y: heightAt(a.x, a.z) + 2.3, z: a.z, info: { name: a.def.name, role: w().npcs[id]?.flags.met ? a.def.role : undefined } });
      let fight: Enemy | null = null;
      b.enemies.forEach((e) => {
        if (!e.alive || !e.named || e.state === 'dying') return;
        items.push({ id: `e${e.id}`, x: e.x, y: heightAt(e.x, e.z) + 1.6 * (e.def.scale ?? 1) + 0.6, z: e.z, info: { name: e.named.title, role: e.disposition === 'ally' ? 'Friend' : e.disposition === 'neutral' ? undefined : 'Hostile' } });
        if (e.elite && e.disposition === 'hostile' && Math.hypot(e.x - p.x, e.z - p.z) < 22) fight = e;
      });
      const f = fight as Enemy | null;
      if (f) boss.value = { name: f.named!.title, title: f === nemesis ? `Who took ${w().nemesis?.heroName}'s light` : f.def.name, hp: f.hp, maxHp: f.maxHp };
      else if (boss.value && !f) boss.value = null;
      plates.update(items, p.x, p.z, g.r.camera, g.r.width, g.r.height, g.barks.speakers());
      trackT -= dt;
      if (trackT <= 0) { trackT = 1.5; objectives.value = tracker(); }
    },
    interactables: I,
    hooks: { onKill, onLoot, onHitProp },
    mapMarks: () => {
      const c = ctx();
      const q = (id: string, entry: string) => test({ quest: { id, entry } }, c);
      const known = (k: string) => test({ knows: k }, c);
      const marks: MapMark[] = [
        { x: V.entry.x - 2, z: V.entry.z, label: 'The Waystation', kind: 'exit' },
        { x: V.exitEast.x - 8, z: V.exitEast.z, label: 'Road washed out', kind: 'place' },
        { x: V.post.x, z: V.post.z, label: 'Old Watch Fire', kind: 'place' },
        { x: V.wreck.x, z: V.wreck.z, label: 'Coyle Wagons', kind: q('caravan', 'wreck') ? 'place' : 'turn' },
        { x: V.blind.x, z: V.blind.z, label: 'Hunter\'s Blind', kind: 'place' },
        { x: V.hollow.x, z: V.hollow.z, label: 'Wolf Hollow', kind: wolvesFriendly() ? 'place' : 'danger' },
        { x: V.dig.x, z: V.dig.z, label: 'The Dig', kind: F('dig.hostile') ? 'danger' : 'place' },
        { x: V.roost.x, z: V.roost.z, label: 'Redcowl\'s Roost', kind: kerchiefsFriendly() || F('redcowl') === 'tricked' ? 'place' : 'danger' },
        { x: V.vault.x, z: V.vault.z, label: 'Sealed Door', kind: 'mystery' },
        { x: V.sinkhole.x, z: V.sinkhole.z, label: 'The Sinkhole', kind: 'mystery' },
        { x: V.grove.x, z: V.grove.z, label: 'Moon Grove', kind: 'place' },
      ];
      if (!known('clue.sick_wolf')) marks.push({ x: V.carcass.x, z: V.carcass.z, label: 'Something dead', kind: 'turn' });
      if (!known('clue.green_stream')) marks.push({ x: V.sample.x, z: V.sample.z, label: 'The green water', kind: 'turn' });
      if (!known('clue.pipe')) marks.push({ x: V.pipe.x, z: V.pipe.z, label: 'The pipe', kind: 'turn' });
      if (F('caravan.survivors') !== 'rescued' && F('caravan.survivors') !== 'dead' && (known('hint.roost') || q('caravan', 'roost_found'))) marks.push({ x: V.cages.x, z: V.cages.z, label: 'The cages', kind: 'quest' });
      return marks;
    },
    musicMood: (x, z) => (Math.hypot(x - V.vault.x, z - V.vault.z) < 22 || Math.hypot(x - V.sinkhole.x, z - V.sinkhole.z) < 26 || Math.hypot(x - V.grove.x, z - V.grove.z) < 16 ? 'mystery' : null),
    ambience: (x, z) => {
      const t = w().time, dark = t === 'night', day = t === 'day' || t === 'dawn';
      const pumping = !F('dig.pump') || F('dig.pump') === 'running';
      return {
        wind: 0.6, leaves: 0.7, fire: kit.warmth(x, z),
        water: Math.max(0, 1 - built.streamDist(x, z) / 24),
        hum: pumping ? Math.max(0, 1 - Math.hypot(x - V.pump.x, z - V.pump.z) / 40) : 0,
        birds: day && F('beasts.outcome') !== 'slaughtered' ? 0.8 : day ? 0.3 : 0,
        crickets: dark ? 0.7 : t === 'dusk' ? 0.35 : 0, owl: dark ? 0.55 : 0,
      };
    },
    debug: () => ({ roostHostile: F('roost.hostile'), digHostile: F('dig.hostile'), pop: F('beasts.population'), wolvesFriendly: wolvesFriendly(), kerchiefsFriendly: kerchiefsFriendly() }),
    dispose: () => {
      for (const a of actors.values()) a.dispose();
      plates.clear();
      plates.root.remove();
      boss.value = null;
      objectives.value = [];
    },
  };
}
