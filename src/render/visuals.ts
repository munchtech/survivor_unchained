import * as THREE from 'three';
import type { VatSpec } from './vat';
import { buildWolf, buildBoar, buildLampling, WOLF_LOOKS } from './creatures';
import { HUMAN_SCALE } from './characterView';
import { bakeablePerson, type BakeArms } from './bakePerson';
import { clipSync, type PersonSpec } from './people';
import { outfitFor } from '@/content/looks';

/* What each creature looks like: the model, the clips for each thing it
 * does, what it carries, and its colours. Keyed by EnemyDef.visual. */


let procCache: Record<string, ReturnType<typeof buildWolf>> = {};

/* The Kerchiefs are people (render/people.ts), baked for the crowd: dressed
 * in their red, armed with real weapons, moving by the animation libraries'
 * clips. */
const KERCHIEF = '#7a1a18', KERCHIEF_DARK = '#3a1412';
type Role = 'move' | 'idle' | 'attack' | 'die' | 'rise' | 'hit' | 'windup';
function person(key: string, spec: PersonSpec, arms: BakeArms, clips: Record<Role, string> & { cast?: string }, scale = 1): VatSpec {
  const c = Object.fromEntries(Object.entries(clips).map(([r, n]) => [r, clipSync(n) ?? clipSync('Idle_Loop')!]));
  return { key, model: () => bakeablePerson(spec, arms), scale: HUMAN_SCALE * scale, clips: c, proportions: false };
}
const FIGHT = { die: 'Death01', rise: 'Idle_Loop', hit: 'Hit_Chest' } as const;

/* The Risen are the dead got up: people gone grey-green, in clothes the
 * grave has had, shambling, clawing, climbing out of the ground. */
const ROT = '#8e9680', GRAVE = '#4a4638', GRAVE_DARK = '#24221c';
const SHAMBLE = { move: 'Zombie_Walk_Fwd_Loop', die: 'Death01', rise: 'LayToIdle', hit: 'Hit_Chest' } as const;

function proc(key: string, make: () => ReturnType<typeof buildWolf>) {
  if (!procCache[key]) procCache[key] = make();
  return procCache[key];
}

export function visualSpec(visual: string): VatSpec {
  switch (visual) {
    case 'skeleton_minion':
      return person(visual, { sex: 'male', outfit: outfitFor('male', 'peasant'), hair: 'Hair_Buzzed', hairColor: '#5a5448', skin: ROT, dye: { cloth: GRAVE, under: GRAVE_DARK } },
        {}, { ...SHAMBLE, idle: 'Zombie_Idle_Loop', attack: 'Zombie_Scratch', windup: 'Zombie_Idle_Loop' });
    case 'risen_ally':
      return person(visual, { sex: 'female', outfit: outfitFor('female', 'peasant'), hair: 'Hair_Long', hairColor: '#6a665e', skin: ROT, figure: 0.9, dye: { cloth: GRAVE, under: GRAVE_DARK } },
        {}, { ...SHAMBLE, idle: 'Zombie_Idle_Loop', attack: 'Zombie_Scratch', windup: 'Zombie_Idle_Loop' });
    case 'skeleton_warrior':
      return person(visual, { sex: 'male', outfit: outfitFor('male', 'ranger', { pauldron: true }), hair: null, beard: true, hairColor: '#4a4640', skin: ROT, dye: { cloth: '#3e4238' } },
        { right: 'viking_sword', forearm: 'shield_round' }, { ...SHAMBLE, idle: 'Idle_Shield_Loop', attack: 'Sword_Regular_A', windup: 'Idle_Shield_Loop' });
    case 'skeleton_warrior_elite':
      return person(visual, { sex: 'male', outfit: outfitFor('male', 'ranger', { pauldron: true, hood: true }), hair: null, beard: true, hairColor: '#3a3630', skin: ROT, dye: { cloth: '#2a2c2e' } },
        { right: 'zweihander' }, { ...SHAMBLE, move: 'Walk_Loop', idle: 'Sword_Idle', attack: 'Sword_Attack', windup: 'Sword_Idle' });
    case 'skeleton_rogue':
      return person(visual, { sex: 'female', outfit: outfitFor('female', 'ranger', { hood: true }), hair: null, skin: ROT, figure: 0.8, dye: { cloth: '#3a3e34' } },
        { right: 'crossbow' }, { ...SHAMBLE, idle: 'Pistol_Idle_Loop', attack: 'Pistol_Shoot', windup: 'Pistol_Idle_Loop' });
    case 'skeleton_mage':
      return person(visual, { sex: 'male', outfit: outfitFor('male', 'peasant', { hood: true }), hair: null, beard: true, hairColor: '#4a4640', skin: ROT, dye: { cloth: '#2e2a36', under: '#16141a' } },
        { right: 'short_staff' }, { ...SHAMBLE, idle: 'Zombie_Idle_Loop', attack: 'Spell_Simple_Shoot', windup: 'Spell_Simple_Idle_Loop', cast: 'Spell_Simple_Enter' });
    case 'kerchief_rogue':
      // A footpad: quick, hooded, a knife in each hand.
      return person(visual, { sex: 'female', outfit: outfitFor('female', 'ranger', { hood: true }), hair: null, skin: '#e0a47c', figure: 1.1, dye: { cloth: KERCHIEF } },
        { right: 'daggers', left: 'dagger_b' }, { ...FIGHT, move: 'Jog_Fwd_Loop', idle: 'Sword_Idle', attack: 'Sword_Regular_B', windup: 'Sword_Idle' });
    case 'kerchief_hooded':
      // A pillager: hooded, throwing what comes to hand.
      return person(visual, { sex: 'male', outfit: outfitFor('male', 'ranger', { hood: true }), hair: null, beard: true, hairColor: '#3a2618', skin: '#c4945e', dye: { cloth: KERCHIEF } },
        {}, { ...FIGHT, move: 'Jog_Fwd_Loop', idle: 'Idle_Loop', attack: 'OverhandThrow', windup: 'Idle_Loop' });
    case 'kerchief_brute':
      // A bruiser: bare-chested behind a round shield, an axe.
      return person(visual, { sex: 'male', outfit: outfitFor('male', 'bare', { pauldron: true }), hair: 'Hair_Buzzed', beard: true, hairColor: '#2a1a12', skin: '#946040', dye: { under: KERCHIEF_DARK } },
        { right: 'viking_axe', forearm: 'shield_round' }, { ...FIGHT, move: 'Walk_Loop', idle: 'Idle_Shield_Loop', attack: 'Sword_Regular_A', hit: 'Idle_Shield_Break', windup: 'Idle_Shield_Loop' }, 1.1);
    case 'kerchief_enforcer':
      // An enforcer: a big man in a red hood with a greataxe.
      return person(visual, { sex: 'male', outfit: outfitFor('male', 'bare', { hood: true }), hair: null, beard: true, hairColor: '#1a1410', skin: '#e0a47c', dye: { cloth: KERCHIEF, under: KERCHIEF_DARK } },
        { right: 'snake_axe' }, { ...FIGHT, move: 'Jog_Fwd_Loop', idle: 'Sword_Idle', attack: 'Sword_Attack', windup: 'Sword_Idle' }, 1.15);
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
