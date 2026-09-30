using SurvivorUnchained.Core;
using System.Collections.Generic;
using System.Linq;

namespace SurvivorUnchained.Content;

/* The part of the fight that IS the player's hands.
 *
 * Weapons fire themselves. These do not: a dash, and one ability chosen at
 * creation. They are where skill lives - a well-timed bash stops a boss's
 * channel, a blink through a closing ring is the difference between a
 * scratch and a corpse, a mark on the right elite shortens the fight by
 * half. Each calling has two to choose between. */

public enum AbilityKind { ShieldBash, Bulwark, Leap, Warcry, Blink, TimeSlip, MarkPrey, SmokeBomb }

/// <summary>How it is aimed: toward the pointer or facing, around you, at a target.</summary>
public enum AbilityAim { Direction, Self, Target }

public sealed class AbilityDef
{
    public AbilityKind Kind;
    /// <summary>The web game's id ('shield_bash').</summary>
    public string Id = "";
    public string Name = "", Icon = "", Description = "";
    public double Cooldown;
    public AbilityAim Aim;
    /// <summary>Can it interrupt a channel (a boss raising the dead, a caster)?</summary>
    public bool Interrupts;
}

public static class Abilities
{
    public static readonly Dictionary<AbilityKind, AbilityDef> All = new AbilityDef[]
    {
        new() { Kind = AbilityKind.ShieldBash, Id = "shield_bash", Name = "Shield Bash", Icon = "shield", Cooldown = 7, Aim = AbilityAim.Direction, Interrupts = true,
            Description = "Drive your shield into everything in front of you: they are thrown back and stunned for 1.5 s. Breaks a channel." },
        new() { Kind = AbilityKind.Bulwark, Id = "bulwark", Name = "Bulwark", Icon = "aegis", Cooldown = 15, Aim = AbilityAim.Self, Interrupts = false,
            Description = "Plant your feet for 3 s: blows are cut by 65%, arrows and bolts are turned back on whoever loosed them, and the horde turns on you." },
        new() { Kind = AbilityKind.Leap, Id = "leap", Name = "Crashing Leap", Icon = "leap", Cooldown = 9, Aim = AbilityAim.Direction, Interrupts = true,
            Description = "Leap up to 7 m and come down hard: everything where you land is struck and thrown aside." },
        new() { Kind = AbilityKind.Warcry, Id = "warcry", Name = "War Cry", Icon = "howl", Cooldown = 16, Aim = AbilityAim.Self, Interrupts = true,
            Description = "A roar that sends lesser things fleeing for 2.5 s and drives you 25% harder for 6 s." },
        new() { Kind = AbilityKind.Blink, Id = "blink", Name = "Blink", Icon = "blink", Cooldown = 7, Aim = AbilityAim.Direction, Interrupts = false,
            Description = "Step 6 m through space. Where you stood erupts in frost that chills everything near it." },
        new() { Kind = AbilityKind.TimeSlip, Id = "time_slip", Name = "Time Slip", Icon = "hourglass", Cooldown = 18, Aim = AbilityAim.Self, Interrupts = true,
            Description = "For 3.5 s everything but you moves at a third of its speed - their missiles too. Breaks a channel." },
        new() { Kind = AbilityKind.MarkPrey, Id = "mark_prey", Name = "Mark Prey", Icon = "mark", Cooldown = 9, Aim = AbilityAim.Target, Interrupts = false,
            Description = "Mark the strongest thing in sight: it takes 50% more from everything for 8 s and dies outright below 20%. Kill it and half the cooldown comes back." },
        new() { Kind = AbilityKind.SmokeBomb, Id = "smoke_bomb", Name = "Smoke Bomb", Icon = "smoke", Cooldown = 15, Aim = AbilityAim.Self, Interrupts = false,
            Description = "Vanish in smoke. For 3 s nothing can find you, and your next hits are sure to crit." },
    }.ToDictionary(a => a.Kind);

    public static AbilityDef ById(string id) => All.Values.First(a => a.Id == id);

    /// <summary>The dash everyone has: a short, invulnerable burst. Its first
    /// moments are the perfect window (a telegraphed blow slipped there gives
    /// the dash back, cracks the air round you and makes the next strikes
    /// sure); out of it, a burst of pace so dashes chain.</summary>
    public static class Dash
    {
        public const double Distance = 5.5, Time = 0.2, Recharge = 2.6, Iframes = 0.3;
        public const double Perfect = 0.18, Riposte = 1.5, Crack = 3.2, Momentum = 0.8, MomentumSpeed = 0.25;
    }
}
