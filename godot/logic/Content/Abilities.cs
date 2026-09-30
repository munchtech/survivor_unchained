using SurvivorUnchained.Core;
using System.Collections.Generic;
using System.Linq;

namespace SurvivorUnchained.Content;

/* The part of the fight that IS the player's hands.
 *
 * Weapons fire themselves. These do not: a dash everyone has, and one art
 * in the hand. Arts are where skill lives - a well-timed bash stops a boss's
 * channel, a blink through a closing ring is the difference between a
 * scratch and a corpse, a mirror left in the right place pulls a pack off
 * you for the breath you need.
 *
 * A survivor knows a few arts and carries one. Most are ways of moving -
 * a sprint, a charge, a wraith's walk through the crowd - each with its own
 * flavour of survival: some are tanky, some heal, some deceive, some burn.
 * The rest belong to a calling. Arts are learned from manuals found in the
 * world, grow in rank with use, and every rank opens facets: small changes
 * to how the art works, chosen by the survivor (Rpg/ArtBook.cs). */

public enum AbilityKind
{
    ShieldBash, Bulwark, Leap, Warcry, Blink, TimeSlip, MarkPrey, SmokeBomb,
    Sprint, MirrorStep, BullRush, WraithWalk, CinderTrail, Grapple, EchoStep, Vault,
}

/// <summary>How it is aimed: toward the pointer or facing, around you, at a target.</summary>
public enum AbilityAim { Direction, Self, Target }

/// <summary>What an art does for survival, for the book and the choice.</summary>
public enum ArtRole { Tank, Damage, Healing, Utility, Control }

/// <summary>A change to how an art works, opened by rank and chosen.</summary>
public sealed record FacetDef(string Id, string Name, string Text);

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
    /// <summary>A way of moving: anyone may learn it.</summary>
    public bool Movement;
    public ArtRole Role;
    /// <summary>The calling it belongs to (only they may learn it), or anyone's.</summary>
    public string? Calling;
    public FacetDef[] Facets = [];
}

public static class Abilities
{
    public static readonly Dictionary<AbilityKind, AbilityDef> All = new AbilityDef[]
    {
        /* ---------------------------------------------------- the callings' -- */
        new() { Kind = AbilityKind.ShieldBash, Id = "shield_bash", Name = "Shield Bash", Icon = "shield", Cooldown = 7, Aim = AbilityAim.Direction, Interrupts = true,
            Role = ArtRole.Control, Calling = "warden",
            Description = "Drive your shield into everything in front of you: they are thrown back and stunned for 1.5 s. Breaks a channel.",
            Facets = [
                new("wide_arc", "Broad Swing", "The bash sweeps all the way round you, for a fifth less."),
                new("concussion", "Concussion", "Stuns last a second longer."),
                new("shield_wall", "Shield Wall", "A barrier of 8% of your health for each thing struck, up to 40%."),
                new("rebound", "Rebound", "Each thing struck takes half a second off the wait."),
            ] },
        new() { Kind = AbilityKind.Bulwark, Id = "bulwark", Name = "Bulwark", Icon = "aegis", Cooldown = 15, Aim = AbilityAim.Self, Interrupts = false,
            Role = ArtRole.Tank, Calling = "warden",
            Description = "Plant your feet for 3 s: blows are cut by 65%, arrows and bolts are turned back on whoever loosed them, and the horde turns on you.",
            Facets = [
                new("unmoving", "Unmoving", "Blows are cut by 80%."),
                new("retribution", "Retribution", "When it ends, holy light bursts from you, 5 m round."),
                new("rallying", "Rallying Stand", "Mend 4% of your health each second it holds."),
                new("marching_wall", "Marching Wall", "You move at your full pace behind it."),
            ] },
        new() { Kind = AbilityKind.Warcry, Id = "warcry", Name = "War Cry", Icon = "howl", Cooldown = 16, Aim = AbilityAim.Self, Interrupts = true,
            Role = ArtRole.Control, Calling = "reaver",
            Description = "A roar that sends lesser things fleeing for 2.5 s and drives you 25% harder for 6 s.",
            Facets = [
                new("terror", "Terror", "Champions flee too, for a second."),
                new("bloodlust", "Bloodlust", "You run 20% faster while it drives you."),
                new("battle_trance", "Battle Trance", "The roar mends 15% of your health."),
                new("echoing", "Echoing Roar", "It drives you for 10 s."),
            ] },
        new() { Kind = AbilityKind.TimeSlip, Id = "time_slip", Name = "Time Slip", Icon = "hourglass", Cooldown = 18, Aim = AbilityAim.Self, Interrupts = true,
            Role = ArtRole.Control, Calling = "arcanist",
            Description = "For 3.5 s everything but you moves at a third of its speed - their missiles too. Breaks a channel.",
            Facets = [
                new("deep_slip", "Deep Slip", "Everything moves at a fifth."),
                new("long_slip", "Long Slip", "It holds for 5.5 s."),
                new("borrowed_time", "Borrowed Time", "Dashes come back three times as fast while it holds."),
                new("stolen_moments", "Stolen Moments", "Mend 3% of your health each second it holds."),
            ] },
        new() { Kind = AbilityKind.MarkPrey, Id = "mark_prey", Name = "Mark Prey", Icon = "mark", Cooldown = 9, Aim = AbilityAim.Target, Interrupts = false,
            Role = ArtRole.Damage, Calling = "stalker",
            Description = "Mark the strongest thing in sight: it takes 50% more from everything for 8 s and dies outright below 20%. Kill it and half the cooldown comes back.",
            Facets = [
                new("twin_marks", "Two Marks", "The two strongest are marked."),
                new("executioner", "Executioner", "The prey dies outright below 30%."),
                new("blood_trail", "Blood Trail", "The prey bleeds while marked."),
                new("quarry", "Quarry", "Killing the prey brings the whole wait back and mends 10% of your health."),
            ] },
        new() { Kind = AbilityKind.SmokeBomb, Id = "smoke_bomb", Name = "Smoke Bomb", Icon = "smoke", Cooldown = 15, Aim = AbilityAim.Self, Interrupts = false,
            Role = ArtRole.Utility, Calling = "stalker",
            Description = "Vanish in smoke. For 3 s nothing can find you, and your next hits are sure to crit.",
            Facets = [
                new("choking", "Choking Smoke", "The smoke hangs where you threw it and poisons what breathes it."),
                new("thick_smoke", "Thick Smoke", "You stay hidden for 5 s."),
                new("ambush", "Ambush", "Sure crits last 2 s longer and hit 50% harder."),
                new("mist_step", "Mist Step", "You move 30% faster while hidden."),
            ] },

        /* ------------------------------------------------ ways of moving -- */
        new() { Kind = AbilityKind.Leap, Id = "leap", Name = "Crashing Leap", Icon = "leap", Cooldown = 9, Aim = AbilityAim.Direction, Interrupts = true,
            Movement = true, Role = ArtRole.Damage,
            Description = "Leap up to 7 m and come down hard: everything where you land is struck and thrown aside. Untouchable in the air.",
            Facets = [
                new("quake", "Quake", "Landing stuns what it strikes for a second."),
                new("long_leap", "Long Leap", "Leap up to 11 m."),
                new("aftershock", "Aftershock", "The ground heaves again half a second after you land, wider."),
                new("wind_at_back", "Wind at Your Back", "Landing gives back a dash and 30% pace for 3 s."),
            ] },
        new() { Kind = AbilityKind.Blink, Id = "blink", Name = "Blink", Icon = "blink", Cooldown = 7, Aim = AbilityAim.Direction, Interrupts = false,
            Movement = true, Role = ArtRole.Utility,
            Description = "Step 6 m through space. Where you stood erupts in frost that chills everything near it.",
            Facets = [
                new("far_step", "Far Step", "Step 9 m."),
                new("winters_wake", "Winter's Wake", "The frost freezes what it catches for 1.5 s."),
                new("arrival", "Arrival", "Frost erupts where you arrive as well."),
                new("quickening", "Quickening", "If the frost caught anything, the wait is 40% shorter."),
            ] },
        new() { Kind = AbilityKind.Sprint, Id = "sprint", Name = "Sprint", Icon = "boot", Cooldown = 12, Aim = AbilityAim.Self,
            Movement = true, Role = ArtRole.Utility,
            Description = "Run. For 4 s you are 70% faster, and nothing slows you.",
            Facets = [
                new("trample", "Trample", "What you run through is struck and thrown aside."),
                new("second_wind", "Second Wind", "Mend 3% of your health each second you run."),
                new("tailwind", "Tailwind", "Dashes come back twice as fast while you run."),
                new("long_road", "The Long Road", "Each kill while you run keeps you running half a second longer."),
            ] },
        new() { Kind = AbilityKind.MirrorStep, Id = "mirror_step", Name = "Mirror Step", Icon = "mirror", Cooldown = 11, Aim = AbilityAim.Direction,
            Movement = true, Role = ArtRole.Utility,
            Description = "Step 5 m and leave two reflections where you stood. What hunts you turns on them; when one breaks, it bursts.",
            Facets = [
                new("three_mirrors", "Hall of Mirrors", "Leave three."),
                new("cold_glass", "Cold Glass", "A breaking reflection chills everything it cuts."),
                new("fighting_reflections", "Fighting Reflections", "Your reflections strike at what comes for them."),
                new("glass_heart", "Glass Heart", "Each reflection that breaks mends 4% of your health."),
            ] },
        new() { Kind = AbilityKind.BullRush, Id = "bull_rush", Name = "Bull Rush", Icon = "horns", Cooldown = 10, Aim = AbilityAim.Direction, Interrupts = true,
            Movement = true, Role = ArtRole.Tank,
            Description = "Charge 9 m behind a barrier of 18% of your health. What stands in the way is struck and thrown aside; a champion stops you, stunned.",
            Facets = [
                new("iron_hide", "Iron Hide", "The barrier is 30% of your health."),
                new("pile_driver", "Pile Driver", "The charge ends in a slam that stuns everything 3 m round."),
                new("unbroken", "Unbroken", "Each thing you strike adds 2% of your health to the barrier."),
                new("gore", "Gore", "What you strike bleeds, and champions take half again as much."),
            ] },
        new() { Kind = AbilityKind.WraithWalk, Id = "wraith_walk", Name = "Wraith Walk", Icon = "wraith", Cooldown = 14, Aim = AbilityAim.Self,
            Movement = true, Role = ArtRole.Healing,
            Description = "For 2.5 s you are half a ghost: 25% faster, missiles pass through you, blows land at half. Everything you pass through is drained, and it mends you.",
            Facets = [
                new("hunger", "Hunger", "Each drain mends twice as much."),
                new("long_night", "The Long Night", "You walk as a wraith for 4 s."),
                new("grave_chill", "Grave Chill", "What you drain flees in terror."),
                new("soul_tithe", "Soul Tithe", "What dies drained mends 5% of your health."),
            ] },
        new() { Kind = AbilityKind.CinderTrail, Id = "cinder_trail", Name = "Cinder Trail", Icon = "embers", Cooldown = 12, Aim = AbilityAim.Self,
            Movement = true, Role = ArtRole.Damage,
            Description = "For 4 s you run 35% faster and the ground burns where you have been.",
            Facets = [
                new("wildfire", "Wildfire", "The trail is wider and burns longer."),
                new("backdraft", "Backdraft", "When the run ends, the whole trail goes up at once."),
                new("pyre_walker", "Pyre-Walker", "Each thing your fire kills mends 1.5% of your health."),
                new("hobbling", "Hobbling Flame", "What stands in the trail is slowed."),
            ] },
        new() { Kind = AbilityKind.Grapple, Id = "grapple", Name = "Grapple Chain", Icon = "chain", Cooldown = 8, Aim = AbilityAim.Direction, Interrupts = true,
            Movement = true, Role = ArtRole.Control,
            Description = "Throw a hooked chain up to 12 m. It bites the first thing in its way and hauls you to it, to land a stunning blow.",
            Facets = [
                new("whirling_chain", "Whirling Chain", "On landing the chain whirls, striking everything 3 m round."),
                new("anchor", "Anchor", "Landing gives a barrier of 12% of your health."),
                new("second_hook", "Second Hook", "If the hooked thing dies within 3 s, half the wait comes back."),
                new("reel", "Reel", "Lesser things are dragged to you instead, and stunned longer."),
            ] },
        new() { Kind = AbilityKind.EchoStep, Id = "echo_step", Name = "Echo Step", Icon = "echo", Cooldown = 16, Aim = AbilityAim.Self,
            Movement = true, Role = ArtRole.Healing,
            Description = "Leave an echo of yourself. Within 4 s, use it again to step back into it, and half the health you lost since comes back.",
            Facets = [
                new("full_echo", "Full Echo", "All of the health you lost comes back."),
                new("resonance", "Resonance", "Stepping back bursts at both ends."),
                new("long_echo", "Long Echo", "The echo lasts 7 s."),
                new("decoy_echo", "Speaking Echo", "The echo draws what hunts you, like a reflection."),
            ] },
        new() { Kind = AbilityKind.Vault, Id = "vault", Name = "Vault", Icon = "wing", Cooldown = 7, Aim = AbilityAim.Direction,
            Movement = true, Role = ArtRole.Control,
            Description = "Spring 6 m back from where you aim, untouchable in the air, and leave snares where you stood that slow and cut.",
            Facets = [
                new("volley", "Parting Volley", "In the air you loose a fan of knives at where you left."),
                new("snare_line", "Snare Line", "The snares hold fast: what steps in is stuck for 1.5 s."),
                new("light_feet", "Light Feet", "Landing gives back a dash and 40% pace for 2 s."),
                new("nimble", "Nimble", "The wait is a third shorter."),
            ] },
    }.ToDictionary(a => a.Kind);

    public static AbilityDef ById(string id) => All.Values.First(a => a.Id == id);
    public static AbilityDef? Find(string id) => All.Values.FirstOrDefault(a => a.Id == id);

    /// <summary>The way of moving each calling knows from the start, besides
    /// its own two arts and a sprint.</summary>
    public static readonly Dictionary<string, string> Kin = new()
    {
        ["warden"] = "bull_rush", ["reaver"] = "grapple", ["arcanist"] = "mirror_step", ["stalker"] = "vault",
    };

    /// <summary>What a calling may learn: its own arts and every way of moving.</summary>
    public static bool Learnable(AbilityDef a, string calling) => a.Calling == null || a.Calling == calling;

    /// <summary>The dash everyone has: a short, invulnerable burst. Its first
    /// moments are the perfect window (a telegraphed blow slipped there gives
    /// the dash back, cracks the air round you and makes the next strikes
    /// sure); out of it, a burst of pace so dashes chain.</summary>
    public static class Dash
    {
        public const double Distance = 5.5, Time = 0.2, Recharge = 2.6, Iframes = 0.3;
        public const double Perfect = 0.18, Riposte = 1.5, Crack = 3.2, Momentum = 0.8, MomentumSpeed = 0.25;
    }

    /* How an art grows. Rank comes from use: every use, and every kill made
     * while it is fresh. Each rank above the first makes it 6% stronger and
     * its wait 4% shorter; ranks 2 and 4 open a facet each. */

    public static readonly double[] RankXp = [0, 15, 45, 100, 190];
    public const int MaxRank = 5;

    public static int RankOf(double xp)
    {
        int r = 1;
        while (r < MaxRank && xp >= RankXp[r]) r++;
        return r;
    }

    public static int FacetSlots(int rank) => rank >= 4 ? 2 : rank >= 2 ? 1 : 0;
    public static double RankPower(int rank) => 1 + 0.06 * (rank - 1);
    public static double RankHaste(int rank) => 1 - 0.04 * (rank - 1);
}
