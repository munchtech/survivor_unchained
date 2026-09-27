import * as THREE from 'three';
import type { VatSpec } from './vat';
import { buildWolf, buildBoar, buildLampling, WOLF_LOOKS } from './creatures';
import { CHARACTER_SCALE } from './characterView';

/* What each creature looks like: the model, the clips for each thing it
 * does, what it carries, and its colours. Keyed by EnemyDef.visual. */

const SK = {
  move: 'Walking_D_Skeletons', idle: 'Idle_Combat', attack: '1H_Melee_Attack_Chop', die: 'Death_C_Skeletons',
  rise: 'Skeletons_Awaken_Floor', hit: 'Hit_A', windup: 'Block', cast: 'Spellcast_Summon',
} as const;

/** Rogue green and barbarian blue, turned Kerchief red. */
const kerchiefRed = (h: number, s: number, l: number): [number, number, number] | null => {
  if (s < 0.18) return null;
  if (h > 0.22 && h < 0.72) return [0.995 - (h - 0.22) * 0.02, Math.min(1, s * 1.1), l * 0.82];
  return null;
};

let procCache: Record<string, ReturnType<typeof buildWolf>> = {};

function proc(key: string, make: () => ReturnType<typeof buildWolf>) {
  if (!procCache[key]) procCache[key] = make();
  return procCache[key];
}

export function visualSpec(visual: string): VatSpec {
  const s = CHARACTER_SCALE;
  switch (visual) {
    case 'skeleton_minion':
      return { key: visual, model: 'skeleton_minion', scale: s, clips: { ...SK },
        attach: [{ bone: 'handslot.r', pack: 'adventure_items', prop: 'Skeleton_Blade' }] };
    case 'risen_ally':
      return { key: visual, model: 'skeleton_minion', scale: s, clips: { ...SK },
        attach: [{ bone: 'handslot.r', pack: 'adventure_items', prop: 'Skeleton_Axe' }] };
    case 'skeleton_warrior':
      return { key: visual, model: 'skeleton_warrior', scale: s, clips: { ...SK, move: 'Walking_B' },
        attach: [
          { bone: 'handslot.r', pack: 'adventure_items', prop: 'Skeleton_Axe' },
          { bone: 'handslot.l', pack: 'adventure_items', prop: 'Skeleton_Shield_Large_A' },
        ] };
    case 'skeleton_warrior_elite':
      return { key: visual, model: 'skeleton_warrior', scale: s, clips: { ...SK, move: 'Walking_B', attack: '2H_Melee_Attack_Chop', windup: '2H_Melee_Idle' },
        attach: [{ bone: 'handslot.r', pack: 'adventure_items', prop: 'axe_2handed' }] };
    case 'skeleton_rogue':
      return { key: visual, model: 'skeleton_rogue', scale: s, clips: { ...SK, attack: '2H_Ranged_Shoot' },
        attach: [{ bone: 'handslot.r', pack: 'adventure_items', prop: 'Skeleton_Crossbow' }] };
    case 'skeleton_mage':
      return { key: visual, model: 'skeleton_mage', scale: s, clips: { ...SK, attack: 'Spellcast_Shoot' },
        attach: [{ bone: 'handslot.r', pack: 'adventure_items', prop: 'Skeleton_Staff' }] };
    case 'kerchief_rogue':
      return { key: visual, model: 'rogue', scale: s, recolor: kerchiefRed, show: ['Knife', 'Knife_Offhand'],
        clips: { move: 'Running_A', idle: 'Idle', attack: 'Dualwield_Melee_Attack_Slice', die: 'Death_A', rise: 'Idle', hit: 'Hit_A', windup: 'Idle' } };
    case 'kerchief_hooded':
      return { key: visual, model: 'rogue_hooded', scale: s, recolor: kerchiefRed, show: ['Throwable'],
        clips: { move: 'Running_B', idle: 'Idle', attack: 'Throw', die: 'Death_B', rise: 'Idle', hit: 'Hit_A', windup: 'Idle' } };
    case 'kerchief_brute':
      return { key: visual, model: 'barbarian', scale: s * 1.1, recolor: kerchiefRed, show: ['1H_Axe', 'Barbarian_Round_Shield'],
        clips: { move: 'Walking_C', idle: 'Blocking', attack: '1H_Melee_Attack_Chop', die: 'Death_A', rise: 'Idle', hit: 'Block_Hit', windup: 'Blocking' } };
    case 'kerchief_enforcer':
      return { key: visual, model: 'barbarian', scale: s * 1.1, recolor: kerchiefRed, show: ['2H_Axe', 'Barbarian_Hat'],
        clips: { move: 'Running_A', idle: '2H_Melee_Idle', attack: '2H_Melee_Attack_Chop', die: 'Death_B', rise: 'Idle', hit: 'Hit_B', windup: '2H_Melee_Idle' } };
    case 'wolf': case 'wolf_alpha': case 'wolf_blighted': case 'wolf_spirit': {
      const w = proc(visual, () => buildWolf({ ...WOLF_LOOKS[visual], seed: visual.length * 7 }));
      // Long bodies read as spiders when a pack closes on you: smaller, and
      // centred on the body so the head does not reach through the survivor.
      return { key: visual, model: () => w.root, scale: visual === 'wolf_alpha' ? 0.92 : 0.82, fps: 20, offset: [0, 0, -0.22],
        clips: { move: w.clips.run, idle: w.clips.idle, attack: w.clips.attack, die: w.clips.die, rise: w.clips.idle, hit: w.clips.hit, windup: w.clips.windup } };
    }
    case 'boar': {
      const b = proc(visual, buildBoar);
      return { key: visual, model: () => b.root, scale: 0.95, fps: 20, offset: [0, 0, -0.12],
        clips: { move: b.clips.run, idle: b.clips.idle, attack: b.clips.attack, die: b.clips.die, rise: b.clips.idle, hit: b.clips.hit, windup: b.clips.windup } };
    }
    case 'lampling': case 'lampling_sapper': {
      const l = proc(visual, () => buildLampling(visual === 'lampling_sapper'));
      return { key: visual, model: () => l.root, scale: 1, fps: 20,
        clips: { move: l.clips.run, idle: l.clips.idle, attack: l.clips.attack, die: l.clips.die, rise: l.clips.rise, hit: l.clips.hit, burrow: l.clips.burrow, windup: l.clips.idle } };
    }
  }
  throw new Error(`no visual for ${visual}`);
}

/** Colour and glow a creature is drawn with, beyond its model. */
export function visualTint(visual: string, out: THREE.Color): number {
  out.setRGB(1, 1, 1);
  if (visual === 'risen_ally') { out.setRGB(0.7, 1.1, 0.8); return 0.12; }
  if (visual === 'wolf_spirit') { out.setRGB(0.9, 1.0, 1.3); return 0.7; }
  return 0;
}

export function resetVisualCache() { procCache = {}; }
