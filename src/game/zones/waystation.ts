import * as THREE from 'three';
import type { Game } from '../game';
import type { ZoneRuntime, Interactable } from '../zone';
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

/** Who is out and about, given what has happened. */
const PRESENT: Record<string, Cond> = {
  pell: { all: [{ not: { fact: 'caravan.pell', eq: 'exposed' } }, { not: { fact: 'caravan.pell', eq: 'fled' } }] },
  jory: { fact: 'caravan.survivors', eq: 'rescued' },
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
    for (const [id, a] of actors) a.hidden = c ? !!PRESENT[id] && !test(PRESENT[id], c) : false;
  };

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
    begin: () => {
      const w = g.world!;
      g.scene.atmo.set(PRESETS[w.time === 'night' ? 'night' : w.time === 'dusk' ? 'dusk' : w.time === 'dawn' ? 'dawn' : 'day']);
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
      trackT -= dt;
      if (trackT <= 0) { trackT = 1; presence(); objectives.value = tracker(); }
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
      plates.update(items, px, pz, cam, g.r.width / zoom, g.r.height / zoom);
      void THREE;
    },
    interactables,
    dispose: () => {
      for (const a of actors.values()) a.dispose();
      for (const a of guards) a.dispose();
      plates.clear();
      plates.root.remove();
      objectives.value = [];
    },
  };
}
