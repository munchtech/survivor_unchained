import type { Renderer } from '@/render/renderer';
import type { PresetName } from '@/render/atmosphere';
import { WorldScene } from '@/game/scene';
import { buildSandboxZone } from '@/world/zones/sandbox';
import { loadoutFor } from '@/game/loadout';
import { ARCHETYPES } from '@/content/archetypes';
import { StatBlock } from '@/sim/stats';
import { draft, choose } from '@/sim/levelup';
import { Input } from '@/core/input';
import { HudBridge } from '@/game/hudBridge';
import { BarkLayer } from '@/ui/hud/barks';
import { screen, zoneInfo, objectives, toast, announce } from '@/ui/store';
import type { AbilityKind } from '@/content/abilities';

/* Development arena for watching fights:
 *   ?dev=combat&weapons=oathblade:3,cinderfall:5&boons=kindling,pyre_burst
 *     &foes=risen,wolf&every=1.5&class=warden&time=night&walk=1 */

export function combatDev(r: Renderer, params: URLSearchParams) {
  const scene = new WorldScene(r);
  const zone = buildSandboxZone((params.get('time') as PresetName) || 'night', r.spec.grassDensity);
  scene.setZone(zone);
  const stats = new StatBlock();
  stats.setBase({ maxHealth: 160, regen: 0.3, armor: 3, moveSpeed: 5.2, pickupRadius: 2.6, critChance: 0.05, critDamage: 1.5, luck: 1 });
  const weapons = (params.get('weapons') || 'oathblade:1').split(',').map((s) => {
    const [id, rank] = s.split(':');
    return { id, rank: Number(rank || 1) };
  });
  if (params.get('cdmul')) stats.add({ stat: 'cooldown', kind: 'more', value: Number(params.get('cdmul')) - 1, source: 'dev' });
  const cls = params.get('class') || 'warden';
  const ability = (params.get('ability') as AbilityKind) || 'shield_bash';
  const b = scene.startBattle({ seed: 7, combat: true, stats, start: zone.start, weapons, ability }, loadoutFor({ archetype: cls as 'warden', weaponItem: ARCHETYPES[cls as 'warden'].weapons[0] }));
  for (const id of (params.get('boons') || '').split(',').filter(Boolean)) b.addBoon(id);
  for (const e of (params.get('evolve') || '').split(',').filter(Boolean)) {
    const [w, branch] = e.split(':');
    b.evolve(w, branch);
  }
  scene.crowd?.prepare(['skeleton_minion', 'skeleton_warrior', 'skeleton_rogue', 'skeleton_mage', 'wolf', 'kerchief_rogue', 'lampling']);

  const foes = (params.get('foes') || 'risen').split(',');
  const every = Number(params.get('every') || 1.4);
  const burst = Number(params.get('burst') || 4);
  const walk = params.get('walk');
  let spawnT = 0.5;
  let t = 0;
  // Pre-populate so a screenshot has a fight in it.
  const pre = Number(params.get('pre') || 0);
  for (let i = 0; i < pre; i++) {
    const a = (i / pre) * Math.PI * 2 + Math.random() * 0.4;
    const d = Number(params.get('near') || 5) + Math.random() * 9;
    b.spawnEnemy(foes[i % foes.length], b.player.x + Math.cos(a) * d, b.player.z + Math.sin(a) * d, { style: 'walk', level: 2 });
  }
  scene.onStep = (dt) => {
    t += dt;
    if (walk) { Input.moveX = Math.cos(t * 0.3) * 0.6; Input.moveZ = Math.sin(t * 0.3) * 0.6; }
    spawnT -= dt;
    if (spawnT <= 0) {
      spawnT = every;
      for (let k = 0; k < burst; k++) {
        const a = b.rng.next() * Math.PI * 2;
        const d = 13 + b.rng.next() * 4;
        const x = b.player.x + Math.cos(a) * d, z = b.player.z + Math.sin(a) * d;
        if (b.collision.blocked(x, z, 0.6)) continue;
        const f = foes[b.rng.int(0, foes.length - 1)];
        b.spawnEnemy(f, x, z, { style: f.startsWith('risen') || f === 'grave_caller' ? 'rise' : 'walk', level: 1 + Math.floor(t / 40) });
      }
    }
    if (autopick) while (b.draftOwed) choose(b, draft(b, 3)[0]);
  };

  const bridge = new HudBridge(scene, new BarkLayer(document.getElementById('stage')!));
  scene.onEvents = (evs) => bridge.events(evs);
  const autopick = params.has('autopick');
  screen.value = 'play';
  zoneInfo.value = { name: 'Proving Ground', region: 'Low Ford', day: 1, time: (params.get('time') as 'night') || 'night' };
  if (params.has('demo')) {
    // Fill every corner of the interface for layout work.
    objectives.value = [
      { id: 'q1', title: 'The Beast Problem', steps: [{ text: 'Ask Maeca about the wolves', done: true }, { text: 'Find where the pack is coming from' }, { text: 'Look for Greymuzzle at the Moon Grove', optional: true }] },
      { id: 't1', title: 'Survive the night', tone: 'tutorial', steps: [{ text: 'Hold out until dawn (2:41)' }] },
    ];
    toast('loot', 'Wolf Pelt ×3', { icon: 'pelt', rarity: 0 });
    toast('loot', 'Wolf-Fang Necklace', { icon: 'fang', rarity: 2, sub: 'Hits have a 12% chance to bleed.' });
    toast('relation', 'Maeca will remember that', { sub: 'Respect +15' });
    toast('quest', 'New lead: The Missing Caravan');
    announce('The Ford-Warden', 'It has kept this crossing for three hundred years', 'danger', 60);
    b.player.burnT = 3; b.player.burnDps = 0;
    b.player.shield = 30; b.player.shieldT = 20;
  }
  if (params.has('draft')) { b.pendingLevels = 1; b.ember.level = 7; }

  if (params.get('camdist')) { scene.cam.targetDistance = Number(params.get('camdist')); scene.cam.distance = scene.cam.targetDistance; }
  (window as unknown as { __scene: WorldScene }).__scene = scene;
  return (dt: number) => {
    Input.poll();
    if (walk) { Input.moveX = Math.cos(t * 0.3) * 0.6; Input.moveZ = Math.sin(t * 0.3) * 0.6; }
    scene.update(dt);
    bridge.update(dt);
  };
}
