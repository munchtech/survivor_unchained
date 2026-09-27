import * as THREE from 'three';
import type { Game } from '../game';
import type { ZoneRuntime, Interactable, MapMark } from '../zone';
import { NpcActor, PlateLayer } from '../actors';
import { buildWaystation, WAY } from '@/world/zones/waystation';
import { PRESETS } from '@/render/atmosphere';
import { NPCS, OUTSIDERS, GUARDS, type NpcDef } from '@/content/npcs';
import { CONVOS } from '@/content/dialogue';
import { markerOf } from '@/world/dialogue';
import { test, type Cond } from '@/world/logic';
import { QUESTS } from '@/content/quests';
import { objectives, say, toast, type Objective } from '@/ui/store';
import { hist } from '@/content/dialogue/town';
import { Folk, type FolkNode } from '../folk';
import { FOLK_LINES, FOLK_LOOKS } from '@/content/folk';

/* The Waystation, lived in.
 *
 * Everyone stands near their door. Doors lead to whoever keeps them. The
 * notice board reads out the town's troubles; the gates lead back down to
 * the Low Ford, out along the Old Road (for five gold), or nowhere at all
 * (north, past Keegan). At night Pell's warehouse can be got into, by
 * someone with a key or a light touch. Behind the shrine, a gap in the
 * hedge. */

const GUARD_DEF = (i: number): NpcDef => ({
  id: `guard${i}`, name: 'Watchman', title: 'The Waystation Watch', role: 'Watch',
  model: 'knight', show: ['Knight_Helmet', '1H_Sword', 'Rectangle_Shield'], tint: '#8a98b0', idle: 'Idle',
  spot: GUARDS[i], barks: [GUARDS[i].line],
});

/** What the stall-keepers shout. */
const STALL_CALLS: Record<string, string[]> = {
  produce: ['Apples! Aldo apples, crisp as frost!', 'Turnips, onions, the last of the beans!', 'Two for a copper, and I\'m robbing myself!'],
  cloth: ['Wool from the south, warm as a bed!', 'Mend your cloak, traveller? It needs it.', 'Dyed in the Morrow, never fades!'],
  herbs: ['Feverfew, woundwort, sleep-easy!', 'Wenna\'s not the only one who knows a leaf.', 'Something for the cough? Everyone\'s got the cough.'],
  pots: ['Pots! Pans! Things to put things in!', 'Fired in Low Kiln, sound as a bell. Hear that?', 'You look like someone who needs a pot.'],
};

/** Who is out and about, given what has happened. */
const PRESENT: Record<string, Cond> = {
  pell: { all: [{ not: { fact: 'caravan.pell', eq: 'exposed' } }, { not: { fact: 'caravan.pell', eq: 'fled' } }] },
  jory: { fact: 'caravan.survivors', eq: 'rescued' },
  // A farm boy goes home at night.
  tam: { not: { time: 'night' } },
  // Maeca hunts the Verge by day once you know her; she drinks here at night.
  maeca: { any: [{ not: { met: 'maeca' } }, { time: 'night' }, { time: 'dusk' }, { fact: 'beasts.outcome', eq: 'slaughtered' }] },
};

/** Where people are, by the hour and by what has happened to them. The
 *  first entry whose condition holds wins; none means their usual spot. */
const ROUTINE: Record<string, Array<{ when: Cond; spot?: { x: number; z: number; facing: number }; idle?: string }>> = {
  harlan: [
    // Nobody has found the caravan: by day he watches the road; once he
    // gives up, he sits outside the tavern.
    { when: { all: [{ fact: 'caravan.days', gte: 3 }, { not: { fact: 'caravan.survivors', exists: true } }] }, spot: { x: -12.3, z: -14.2, facing: Math.PI / 2 }, idle: 'Sit_Floor_Idle' },
    { when: { all: [{ fact: 'caravan.days', gte: 1 }, { not: { fact: 'caravan.survivors', exists: true } }, { not: { time: 'night' } }] }, spot: { x: 35.4, z: 1.4, facing: Math.PI / 2 } },
  ],
  // The smith stops at night.
  brannoc: [{ when: { time: 'night' }, idle: 'Idle' }],
  maeca: [{ when: { time: 'night' }, spot: { x: -11.6, z: -4.4, facing: Math.PI / 2 }, idle: 'Idle_B' }],
};

export function waystation(g: Game): ZoneRuntime {
  const built = buildWaystation(g.r.spec.grassDensity);
  const root = built.zone.root;
  const heightAt = (x: number, z: number) => built.kit.y(x, z);
  const actors = new Map<string, NpcActor>();
  const guards: NpcActor[] = [];
  const plates = new PlateLayer(document.getElementById('stage')!);
  const ctx = () => g.ctx!;

  for (const def of [...Object.values(NPCS), OUTSIDERS.jory]) {
    const a = new NpcActor(def, root, heightAt, g.barks);
    actors.set(def.id, a);
  }
  GUARDS.forEach((_, i) => guards.push(new NpcActor(GUARD_DEF(i), root, heightAt, g.barks)));

  // Behind every stall, someone selling; they pack up at dusk.
  const keepers = built.stalls.map((st, i) => {
    const look = FOLK_LOOKS[(i * 3 + 1) % FOLK_LOOKS.length];
    return new NpcActor({
      id: `keeper${i}`, name: 'Stall-keeper', title: '', role: '', model: look.model, show: look.show, tint: look.tint, scale: look.scale, idle: i % 2 ? 'Idle_B' : 'Idle',
      spot: { x: st.x - Math.sin(st.rot) * 0.35, z: st.z - Math.cos(st.rot) * 0.35, facing: st.rot }, barks: STALL_CALLS[st.kind] ?? ['Come and look!'],
    }, root, heightAt, g.barks);
  });

  // Where the town walks: the lanes, and what is at the end of them.
  const D = built.doors;
  const node = (id: string, x: number, z: number, kind: FolkNode['kind'] = 'path', extra: Partial<FolkNode> = {}): FolkNode => ({ id, x, z, kind, ...extra });
  const door = (id: string, key: string, extra: Partial<FolkNode> = {}, out = 0.5) => {
    const d = D[key];
    // Stand on the step, not in the wall: half a pace out from the door.
    const b = key.startsWith('home') ? null : (WAY as Record<string, { x: number; z: number }>)[key];
    let x = d.x, z = d.z;
    if (b) { const l = Math.hypot(d.x - b.x, d.z - b.z) || 1; x += ((d.x - b.x) / l) * out; z += ((d.z - b.z) / l) * out; }
    return node(id, x, z, 'door', { face: b ? { x: b.x, z: b.z } : undefined, ...extra });
  };
  const stallNodes = built.stalls.map((st, i) => node(`stall${i}`, st.x + Math.sin(st.rot) * 2.1, st.z + Math.cos(st.rot) * 2.1, 'stall', { face: { x: st.x, z: st.z }, square: true }));
  const folkNodes: FolkNode[] = [
    node('gS', 0, 33, 'gate'), node('s3', 0, 27.5), node('s1', 0, 20), node('s2', 0, 12),
    node('sL', -5, 25.3), node('sR', 5, 25.3), node('swL', -14.5, 25), node('seL', 14.5, 25),
    node('sqSW', -3.6, 3.2, 'path', { square: true }), node('sqSE', 4.4, 4.2, 'path', { square: true }),
    node('sqNW', -4.4, -4.6, 'path', { square: true }), node('board', 4.2, -3.2, 'board', { face: { x: WAY.board.x, z: WAY.board.z }, square: true }),
    node('well', -2.3, 1.2, 'well', { face: { x: 0, z: 0 }, square: true }),
    node('n1', 0, -12.5), node('n2', 0, -23.5), node('e1', 12, 0.6), node('e2', 24, 0.6), node('gE', 33, 0, 'gate'),
    node('innL', -6, 9.5), node('innN', -11.5, 15.5), node('tavL', -6, -9.5), node('wN', -9, -3), node('trS', 8.5, -15), node('smL', 6, 10.5), node('trL', 5, -10.2),
    node('w1', -18, 17.5), node('wW', -19, -5.5), node('sh0', -6, -16), node('sh1', -14, -19.5), node('shF', -20.5, -23.5), node('ne0', 10, -19), node('ne1', 17, -23.5), node('eS', 25, 5),
    door('inn', 'inn'), door('tavern', 'tavern', { tavern: true }), door('smithy', 'smithy'), door('trading', 'trading'), door('shrine', 'shrine', {}, 0),
    ...[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11].map((i) => door(`home${i}`, `home${i}`)),
    ...stallNodes,
  ];
  const folkEdges: Array<[string, string]> = [
    ['gS', 's3'], ['s3', 's1'], ['s3', 'sL'], ['s3', 'sR'], ['sL', 'home5'], ['sR', 'home4'], ['sL', 'swL'], ['swL', 'home7'], ['sR', 'seL'], ['seL', 'home8'], ['s1', 's2'],
    ['s2', 'sqSW'], ['s2', 'sqSE'], ['sqSW', 'well'], ['sqSW', 'sqNW'], ['well', 'sqNW'], ['sqSE', 'board'], ['sqSE', 'e1'], ['board', 'e1'], ['board', 'n1'], ['sqNW', 'n1'],
    ['n1', 'n2'], ['n2', 'home11'], ['e1', 'e2'], ['e2', 'gE'], ['e2', 'eS'], ['eS', 'home6'],
    ['s2', 'innL'], ['innL', 'inn'], ['inn', 'innN'], ['innN', 'w1'], ['w1', 'home9'], ['w1', 'home7'],
    ['sqNW', 'tavL'], ['tavL', 'tavern'], ['sqNW', 'wN'], ['wN', 'wW'], ['wW', 'home2'], ['wW', 'home3'],
    ['sqSE', 'smL'], ['s2', 'smL'], ['smL', 'smithy'], ['n1', 'trL'], ['trL', 'trading'], ['trading', 'trS'], ['trL', 'trS'], ['trS', 'ne0'], ['ne0', 'ne1'], ['ne1', 'home0'], ['ne1', 'home1'],
    ['n1', 'sh0'], ['sh0', 'sh1'], ['sh1', 'shF'], ['shF', 'shrine'], ['e2', 'home10'],
    ['innL', 'stall0'], ['smL', 'stall1'], ['tavL', 'stall2'], ['sqNW', 'stall2'], ['trL', 'stall3'],
  ];
  const hour = () => g.world?.time ?? 'day';
  const folk = new Folk({
    parent: root, nodes: folkNodes, edges: folkEdges, col: built.zone.collision, kit: built.kit, barks: g.barks, heightAt,
    plan: () => {
      const t = hour();
      return t === 'night' ? { adults: 2, children: 0, watch: true } : t === 'dusk' ? { adults: 5, children: 0, watch: true } : t === 'dawn' ? { adults: 3, children: 0, watch: false } : { adults: 8, children: 1, watch: false };
    },
    dark: () => hour() === 'night' || hour() === 'dusk',
    lines: (role) => {
      const c = g.ctx;
      if (!c) return [];
      const dark = hour() === 'night' || hour() === 'dusk';
      const died = (g.ch?.stats.deaths ?? 0) > 0;
      return FOLK_LINES.filter((l) => (role === 'child' ? l.child : role === 'watch' ? l.watch : !l.child && !l.watch)
        && (l.night === undefined || l.night === dark) && (!l.died || died) && test(l.when, c));
    },
    round: ['gS', 's2', 'sqSW', 'sqNW', 'n1', 'n2', 'n1', 'board', 'e1', 'e2', 'gE', 'e2', 'e1', 'sqSE', 's2', 's1'],
  });

  const interactables: Interactable[] = [];
  for (const [id, a] of actors) {
    interactables.push({
      id: `talk:${id}`, x: a.x, z: a.z, r: 2.8, verb: 'Talk', name: a.def.name,
      when: () => !a.hidden,
      act: () => g.talk(id),
    });
  }
  // Doors lead to whoever keeps them.
  const DOOR_OWNER: Record<string, [string, string]> = {
    inn: ['rook', 'The Last Lamp'], tavern: ['rav', 'The Crooked Flagon'], smithy: ['brannoc', 'Brannoc\'s Smithy'], trading: ['harlan', 'Coyle Trading Post'],
    shrine: ['chid', 'Shrine of the Morning Light'], wenna: ['wenna', 'Wenna\'s House'], barracks: ['holloway', 'Watch House'], toll: ['vonnra', 'The Toll Tower'],
  };
  for (const [door, [owner, label]] of Object.entries(DOOR_OWNER)) {
    const d = built.doors[door];
    if (!d) continue;
    interactables.push({ id: `door:${door}`, x: d.x, z: d.z, r: 2.2, verb: 'Visit', name: label, act: () => g.talk(owner) });
  }
  interactables.push(
    { id: 'board', x: WAY.board.x, z: WAY.board.z, r: 2.6, verb: 'Read', name: 'Notice Board', act: () => g.talk('board') },
    { id: 'well', x: 0, z: 0, r: 2.8, verb: 'Look into', name: 'The Well', act: () => say('The water is a long way down, and clean. Somebody has scratched "M. + J." into the stone.', undefined, 4) },
    {
      id: 'gate:south', x: WAY.south.x, z: WAY.south.z - 1.5, r: 3.4, verb: 'Travel', name: 'The Low Ford Road',
      act: () => g.travel('lowford', 'The Low Ford Road', 'South, toward the crossing'),
    },
    {
      id: 'gate:east', x: WAY.east.x - 1.5, z: WAY.east.z, r: 3.4, verb: 'Travel', name: 'The Old Road',
      hint: () => (g.world?.facts['toll.paid'] ? 'Thornhollow Verge' : 'Vonnra\'s toll: 5 gold'),
      locked: () => (!g.world?.facts['toll.paid'] && (g.ch?.gold ?? 0) < 5 ? 'The toll is five gold' : null),
      act: () => {
        if (!g.world!.facts['toll.paid']) { g.apply([{ gold: -5 }, { set: { 'toll.paid': true } }]); toast('gold', 'Five gold to Vonnra\'s toll'); }
        if (g.hasZone('verge')) g.travel('verge', 'Thornhollow Verge', 'East along the Old Road');
        else say('The Old Road runs east into the trees. (The Verge is not built yet.)', undefined, 3);
      },
    },
    {
      id: 'gate:north', x: WAY.north.x, z: WAY.north.z + 3, r: 3.2, verb: 'Pass', name: 'The North Gate',
      locked: () => 'Professor Keegan bars the way',
      act: () => {},
    },
    {
      id: 'warehouse', x: built.doors.warehouse.x, z: built.doors.warehouse.z, r: 2.4, verb: 'Enter', name: 'Pell\'s Warehouse',
      when: () => !g.world?.facts['warehouse.searched'],
      hint: () => (g.world?.time === 'night' ? undefined : 'Locked. Pell is watching.'),
      locked: () => {
        const c = ctx();
        if (!c) return 'Locked';
        if (test({ hasItem: 'clerks_key' }, c)) return null;
        if (g.world!.time !== 'night') return 'Locked, and Pell is watching the door';
        return test({ hasItem: 'lockpicks' }, c) ? null : 'Locked. You would need lockpicks, or a key';
      },
      act: () => {
        const night = g.world!.time === 'night';
        const withKey = test({ hasItem: 'clerks_key' }, ctx());
        g.apply([
          { set: { 'warehouse.searched': true } }, { give: 'pell_ledger' }, { quest: { id: 'caravan', entry: 'pell_ledger' } },
          hist('burgled_pell', 'broke into Pell Varrow\'s warehouse', ['theft', 'caravan'], night ? 0 : 1, undefined, { pell: { trust: -30, fear: 10 } }),
        ]);
        say(withKey ? 'The clerk\'s key turns sweetly. Inside: crates, dust, and a ledger Pell should have burned.' : 'The lock gives under your picks. Inside: crates, dust, and a ledger Pell should have burned.', undefined, 5);
      },
    },
    {
      id: 'garden', x: WAY.garden.x + 2.5, z: WAY.garden.z + 4.5, r: 2.2, verb: 'Open', name: 'An old trunk',
      when: () => !g.world?.zones.waystation?.garden,
      act: () => {
        g.apply([
          { zone: { id: 'waystation', key: 'garden', value: true } }, { give: 'ember_shard', qty: 2 }, { gold: 25 },
          { learn: 'lore.firstlamp', text: 'The Quiet Garden: where the first Watch-captain is buried, with his lamp.' },
        ]);
        say('Under the old captain\'s stone, a trunk the Watch forgot: ember shards, a purse, and a note: "Keep the lights lit. — C."', undefined, 6);
      },
    },
  );

  const presence = () => {
    const c = ctx();
    const p = g.scene.battle?.player;
    for (const [id, a] of actors) {
      const hide = c ? !!PRESENT[id] && !test(PRESENT[id], c) : false;
      a.night = g.world?.time === 'night' || g.world?.time === 'dusk';
      // Nobody vanishes in front of you: someone leaving waits until you look away.
      const watched = !!p && !a.hidden && Math.hypot(p.x - a.x, p.z - a.z) < 16;
      if (hide !== a.hidden && !(hide && (watched || a.talking) && placed.has(id))) a.hidden = hide;
      if (!c) continue;
      const r = ROUTINE[id]?.find((e) => test(e.when, c));
      const spot = r?.spot ?? a.def.spot, idle = r?.idle ?? a.def.idle;
      if (spot.x !== a.x || spot.z !== a.z || idle !== a.pose) {
        // Only while nobody is looking: never pop someone across the square mid-conversation.
        const near = p && (Math.hypot(p.x - a.x, p.z - a.z) < 16 || Math.hypot(p.x - spot.x, p.z - spot.z) < 16);
        if (a.talking || (near && placed.has(id))) continue;
        a.place(spot, idle);
        const it = interactables.find((i) => i.id === `talk:${id}`);
        if (it) { it.x = spot.x; it.z = spot.z; }
      }
      placed.add(id);
    }
  };
  const placed = new Set<string>();
  const atmosphereFor = (t: string) => PRESETS[t === 'night' ? 'nightTown' : t === 'dusk' ? 'dusk' : t === 'dawn' ? 'dawn' : 'day'];
  let nightNow = false;

  const tracker = (): Objective[] => {
    const w = g.world;
    if (!w) return [];
    const out: Objective[] = [];
    for (const id of ['beasts', 'caravan']) {
      const q = w.quests[id];
      if (!q || q.status !== 'active') continue;
      const last = q.entries.slice(-2).map((e) => QUESTS[id].entries[e]).filter(Boolean);
      out.push({ id, title: QUESTS[id].name, tone: 'main', steps: last.map((t) => ({ text: t.length > 90 ? `${t.slice(0, 88)}…` : t })) });
    }
    return out;
  };

  let trackT = 0;
  return {
    id: 'waystation', name: 'The Waystation', region: 'Where three roads meet', build: built.zone, combat: false,
    actors,
    arrival: (from) => {
      if (from === 'verge') return { x: WAY.east.x - 5, z: WAY.east.z, facing: -Math.PI / 2 };
      if (from === 'death') return { x: WAY.shrine.x + 6, z: WAY.shrine.z + 6, facing: Math.PI * 0.25 };
      return { x: WAY.south.x, z: WAY.south.z - 8, facing: Math.PI };
    },
    timeOf: (w) => w.time,
    atmosphereFor,
    // The town is seen whole from its gate; the corner behind the shrine is not.
    mapKnown: [{ x: 0, z: 2, r: 35 }, { x: 22, z: 20, r: 20 }, { x: -22, z: 20, r: 20 }, { x: 22, z: -20, r: 20 }, { x: -20, z: -18, r: 17 }],
    mapFocus: { x: 0, z: 3, zoom: 1.5 },
    mapMarks: () => {
      const c = ctx();
      const marks: MapMark[] = [
        { x: WAY.inn.x, z: WAY.inn.z, label: 'The Last Lamp', kind: 'place' },
        { x: WAY.tavern.x, z: WAY.tavern.z, label: 'The Tavern', kind: 'place' },
        { x: WAY.smithy.x, z: WAY.smithy.z, label: 'Smithy', kind: 'place' },
        { x: WAY.trading.x, z: WAY.trading.z, label: 'Coyle Trading', kind: 'place' },
        { x: WAY.warehouse.x, z: WAY.warehouse.z, label: 'Warehouse', kind: 'place' },
        { x: WAY.shrine.x, z: WAY.shrine.z, label: 'Shrine', kind: 'place' },
        { x: WAY.wenna.x, z: WAY.wenna.z, label: 'Wenna\'s', kind: 'place' },
        { x: WAY.barracks.x, z: WAY.barracks.z, label: 'The Watch', kind: 'place' },
        { x: 0, z: 0, label: 'The Square', kind: 'place' },
        { x: WAY.south.x, z: WAY.south.z + 4, label: 'To the Low Ford', kind: 'exit' },
        { x: WAY.east.x + 4, z: WAY.east.z, label: 'The Old Road, east', kind: 'exit' },
        { x: WAY.north.x, z: WAY.north.z - 4, label: 'North (barred)', kind: 'exit' },
      ];
      if (g.world?.zones.waystation?.garden) marks.push({ x: WAY.garden.x, z: WAY.garden.z, label: 'Quiet Garden', kind: 'place' });
      for (const [id, a] of actors) {
        if (a.hidden) continue;
        const convo = CONVOS[id];
        const m = convo && c ? markerOf(convo, c) : null;
        // On the map, a '?' (news to bring, something to turn in) is gold;
        // someone you have simply not met yet is just a name.
        if (m === '?') marks.push({ x: a.x, z: a.z, label: a.def.name, kind: 'quest' });
        else if (m) marks.push({ x: a.x, z: a.z, label: a.def.name, kind: 'person' });
      }
      return marks;
    },
    ambience: (x, z) => {
      const t = g.world?.time ?? 'day', dark = t === 'night', day = t === 'day' || t === 'dawn';
      const forge = Math.max(0, 1 - Math.hypot(x - WAY.smithy.x, z - WAY.smithy.z) / 26);
      return {
        wind: 0.3, leaves: 0.2, town: (dark ? 0.25 : 0.85) * (1 - Math.min(1, Math.hypot(x, z) / 60) * 0.6),
        fire: built.kit.warmth(x, z), smithy: day ? forge : 0,
        birds: day ? 0.45 : 0, crickets: dark ? 0.55 : t === 'dusk' ? 0.25 : 0, owl: dark ? 0.3 : 0,
      };
    },
    begin: () => {
      const w = g.world!;
      g.scene.atmo.set(atmosphereFor(w.time));
      built.setNight(w.time === 'night' || w.time === 'dusk');
      nightNow = w.time === 'night' || w.time === 'dusk';
      presence();
      objectives.value = tracker();
      g.announceZone();
      if (!w.facts['waystation.visited']) {
        w.facts['waystation.visited'] = true;
        setTimeout(() => say('The Waystation: walls, smoke, the smell of bread. People stop to look at you. News travels fast here.', undefined, 5), 2500);
      }
    },
    frame: (dt) => {
      const b = g.scene.battle;
      if (!b) return;
      const px = b.player.x, pz = b.player.z;
      for (const a of actors.values()) a.update(dt, px, pz);
      for (const a of guards) a.update(dt, px, pz);
      const dark = g.world?.time === 'night' || g.world?.time === 'dusk';
      for (const a of keepers) { a.hidden = dark; a.update(dt, px, pz); }
      folk.update(dt, px, pz);
      trackT -= dt;
      if (trackT <= 0) {
        trackT = 1; presence(); objectives.value = tracker();
        // The hour turned (a rest, waiting for night): light the braziers or put them out.
        const n = g.world?.time === 'night' || g.world?.time === 'dusk';
        if (n !== nightNow) { nightNow = n; built.setNight(n); }
      }
      const c = ctx();
      const items = [];
      for (const [id, a] of actors) {
        if (a.hidden) continue;
        const convo = CONVOS[id];
        const s = g.world?.npcs[id];
        items.push({
          id, x: a.x, y: heightAt(a.x, a.z) + 2.25 * (a.def.scale ?? 1) - (a.seated ? 0.5 : 0), z: a.z,
          info: { name: a.def.name, role: s?.flags.met ? a.def.role : undefined, marker: convo && c ? markerOf(convo, c) : null },
        });
      }
      const cam = g.r.camera;
      const zoom = 1;
      plates.update(items, px, pz, cam, g.r.width / zoom, g.r.height / zoom, g.barks.speakers());
      void THREE;
    },
    interactables,
    debug: () => ({ folk: folk.count, walkers: folk.debugState(), lanes: folk.validate(), lit: built.kit.sources.filter((x) => x.on).length, night: nightNow }),
    dispose: () => {
      for (const a of actors.values()) a.dispose();
      for (const a of guards) a.dispose();
      for (const a of keepers) a.dispose();
      folk.dispose();
      plates.clear();
      plates.root.remove();
      objectives.value = [];
    },
  };
}
