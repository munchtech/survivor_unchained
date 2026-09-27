/* The part of the fight that IS the player's hands.
 *
 * Weapons fire themselves. These do not: a dash, and one ability chosen at
 * creation. They are where skill lives - a well-timed bash stops a boss's
 * channel, a blink through a closing ring is the difference between a scratch
 * and a corpse, a mark on the right elite shortens the fight by half. Each
 * class has two to choose between, and they ask different things of you. */

export type AbilityKind = 'shield_bash' | 'bulwark' | 'leap' | 'warcry' | 'blink' | 'time_slip' | 'mark_prey' | 'smoke_bomb';

export interface AbilityDef {
  id: AbilityKind;
  name: string;
  icon: string;
  cooldown: number;
  description: string;
  /** How it is aimed: toward the pointer / facing, or around you. */
  aim: 'direction' | 'self' | 'target';
  /** Can it interrupt a channel (a boss raising the dead, a caster)? */
  interrupts: boolean;
}

export const ABILITIES: Record<AbilityKind, AbilityDef> = {
  shield_bash: {
    id: 'shield_bash', name: 'Shield Bash', icon: 'shield', cooldown: 7, aim: 'direction', interrupts: true,
    description: 'Drive your shield into everything in front of you: they are thrown back and stunned for 1.5 s. Breaks a channel.',
  },
  bulwark: {
    id: 'bulwark', name: 'Bulwark', icon: 'aegis', cooldown: 15, aim: 'self', interrupts: false,
    description: 'Plant your feet for 3 s: blows are cut by 65%, arrows and bolts are turned back on whoever loosed them, and the horde turns on you.',
  },
  leap: {
    id: 'leap', name: 'Crashing Leap', icon: 'leap', cooldown: 9, aim: 'direction', interrupts: true,
    description: 'Leap up to 7 m and come down hard: everything where you land is struck and thrown aside.',
  },
  warcry: {
    id: 'warcry', name: 'War Cry', icon: 'howl', cooldown: 16, aim: 'self', interrupts: true,
    description: 'A roar that sends lesser things fleeing for 2.5 s and drives you 25% harder for 6 s.',
  },
  blink: {
    id: 'blink', name: 'Blink', icon: 'blink', cooldown: 7, aim: 'direction', interrupts: false,
    description: 'Step 6 m through space. Where you stood erupts in frost that chills everything near it.',
  },
  time_slip: {
    id: 'time_slip', name: 'Time Slip', icon: 'hourglass', cooldown: 18, aim: 'self', interrupts: true,
    description: 'For 3.5 s everything but you moves at a third of its speed - their missiles too. Breaks a channel.',
  },
  mark_prey: {
    id: 'mark_prey', name: 'Mark Prey', icon: 'mark', cooldown: 9, aim: 'target', interrupts: false,
    description: 'Mark the strongest thing in sight: it takes 50% more from everything for 8 s and dies outright below 20%. Kill it and half the cooldown comes back.',
  },
  smoke_bomb: {
    id: 'smoke_bomb', name: 'Smoke Bomb', icon: 'smoke', cooldown: 15, aim: 'self', interrupts: false,
    description: 'Vanish in smoke. For 3 s nothing can find you, and your next hits are sure to crit.',
  },
};

export const DASH = { distance: 5.5, time: 0.2, recharge: 2.6, iframes: 0.3 };
