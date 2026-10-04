using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Content;

/* The things that come out of the dark.
 *
 * Every creature is data: stats at level 1, a behaviour, and optional verbs
 * (a lunge, a ranged attack, ground left behind, a death burst, a split).
 * Behaviours are what stop two hundred creatures from being one creature two
 * hundred times - each asks the survivor a different question:
 *
 *   chase       the baseline: come at you along the flow field
 *   pack        wolves: fan out to surround, then close together
 *   charger     boars: plant, paw the ground, run a straight line; a charge
 *               that ends in a tree stuns the boar
 *   ranged      keep a distance and shoot; step toward them
 *   orbit       hold a ring and walk it, so circling away stops working
 *   tunneler    lamplings: go under, come up beside you
 *   caster      stand behind the others and raise the dead / hurl frost
 *   guard       a shield toward you: projectiles from the front mostly glance
 *               off - go around, or use something that is not a projectile
 *   stationary  totems, turrets, lanterns
 *
 * Levels scale health and damage (ScaleFor); the zone and the night's
 * threat decide the level. */

public enum Behavior { Chase, Pack, Charger, Ranged, Orbit, Tunneler, Caster, Guard, Stationary, Boss, Flee }

public sealed class RangedSpec
{
    public double Range, Cooldown, Speed;
    public School School;
    public int? Count;
    public double? Spread, DamagePct;
    public bool Lob;
    /// <summary>A lobbed pot leaves burning ground where it lands.</summary>
    public GroundSpec? Zone;
    public (double Factor, double Duration)? Slow;
    public string? Art;
}

public sealed record LungeSpec(double Range, double Cooldown, double Windup, double Time, double Speed);
public sealed record TrailSpec(double Interval, double Radius, double Life, double DpsPct, School School);
public sealed record BurstSpec(double Radius, double DamagePct, double Fuse, School School, StatusKind? Status = null);
public sealed record SplitSpec(string Into, int Count);
/// <summary>Raises fallen dead nearby as fresh risen.</summary>
public sealed record RaiseSpec(double Every, int Count, string Into, double Range);
public sealed record GuardSpec(double Arc, double Reduction);
/// <summary>A pulse that quickens or wards its own kind round it (a howl, a drum, a bell):
/// Haste on their pace and blows, Ward off what they take, for Duration. Word: said over
/// it as it pulses, so the eye finds the one to kill.</summary>
public sealed record AuraSpec(double Every, double Radius, double Duration, double Haste = 1, double Ward = 0, string Word = "");
/// <summary>Calls its own: a cast with a word, then Count of Into come up or in, round the
/// one it hunts (AtTarget: an ambush from the dark, the ground opening under them) or round
/// itself; never more than Max in its life.</summary>
public sealed record SummonSpec(double Every, int Count, string Into, double Cast, SpawnStyle Style, double Range = 6, bool AtTarget = false, int Max = 12, string Word = "");
/// <summary>A blow on the ground: a disc that fills where the survivor stood (or round
/// itself), then the blow.</summary>
public sealed record SlamSpec(double Range, double Cooldown, double Windup, double Radius, double DamagePct, School School = School.Physical, bool Self = false, string Word = "");

public sealed class EnemyDef
{
    public string Id = "", Name = "";
    public Family Family;
    public Faction Faction;
    /// <summary>View key: which model or creature, and its colouring.</summary>
    public string Visual = "";
    public double? Scale;
    public double Health, Speed, Damage, Radius;
    public double? Mass;
    public double Xp;
    public double? Gold;
    public Resists? Resists;
    public Behavior Behavior;
    public RangedSpec? Ranged;
    public LungeSpec? Lunge;
    public LungeSpec? Charge;
    public TrailSpec? Trail;
    public BurstSpec? Burst;
    public SplitSpec? Split;
    public RaiseSpec? Raise;
    public GuardSpec? Guard;
    /// <summary>Contact attack rhythm.</summary>
    public double? AttackEvery;
    public bool Elite, Boss;
    public double? AggroRange;
    /// <summary>Tags it carries for items and procs.</summary>
    public Tag[]? Tags;
    public string? Loot;
    /// <summary>What the bestiary says once it has been put down.</summary>
    public string Note = "";

    /* The encounters' verbs (docs/SKILLS_DESIGN.md, "Encounters"). */
    public AuraSpec? Aura;
    public SummonSpec? Summon;
    public SlamSpec? Slam;
    /// <summary>Runs its charge or lunge again this many times, a shorter wind-up each.</summary>
    public int Chain;
    /// <summary>Its run ends in its own burst (a lit crate carried down a lane).</summary>
    public bool RunBursts;
    /// <summary>Its blows chill (Chill) or poison (Poison) the survivor.</summary>
    public StatusKind? Bite;
    /// <summary>Takes this much less from blows that are not critical (the Ironbound Sign).</summary>
    public double IronSkin;
    /// <summary>A people's miniboss: the stretch it opens shows its verb first on it.</summary>
    public bool Miniboss;
    /// <summary>What it teaches, said under its name as it comes.</summary>
    public string Lesson = "";
    /// <summary>Its colour over its model's (above 1 brightens), and a glow, so a kind on a
    /// shared rig reads as itself until it has its own (the model briefs in SKILLS_DESIGN).</summary>
    public (double R, double G, double B)? Tint;
    public double? Glow;
    /// <summary>The champion Signs it wears (Content/Signs.cs), if any.</summary>
    public string[] Signs = [];

    /// <summary>A copy to change (a signed champion's own def).</summary>
    public EnemyDef Clone() => (EnemyDef)MemberwiseClone();
}

public readonly record struct LevelScale(double Health, double Damage, double Xp);

public static class Enemies
{
    /// <summary>A foe as a sentence names it, for "Brought down by ...": a named one by its name
    /// ("Whitethroat", "the Pack-Mother", "the Herald of the Pack"), any other as one of its kind
    /// ("a Kerchief Footpad", "an Ironbound Risen").</summary>
    public static string Called(string? title, string name)
    {
        if (!string.IsNullOrEmpty(title))
        {
            if (title.StartsWith("Herald of ")) return "the " + title;
            foreach (var lead in new[] { "The ", "A ", "An " })
                if (title.StartsWith(lead)) return char.ToLowerInvariant(title[0]) + title[1..];
            return title;
        }
        if (name.Length == 0) return "the dark";
        if (name.StartsWith("The ")) return "the " + name[4..];
        return ("AEIOU".Contains(char.ToUpperInvariant(name[0])) ? "an " : "a ") + name;
    }

    static readonly Resists Undead = new() { [School.Frost] = 0.25, [School.Shadow] = 0.35, [School.Holy] = -0.5, [School.Fire] = -0.15 };
    static readonly Resists Beast = new() { [School.Fire] = -0.25, [School.Nature] = 0.2 };
    static readonly Resists Kerchief = new();

    public static readonly Dictionary<string, EnemyDef> All = new EnemyDef[]
    {
        /* ------------------------------------------------------------ the dead -- */
        new() { Id = "risen", Name = "Risen", Family = Family.Undead, Faction = Faction.Dead, Visual = "skeleton_minion",
            Health = 20, Speed = 2.7, Damage = 8, Radius = 0.45, Xp = 2, Resists = Undead, Behavior = Behavior.Chase,
            Note = "The dead of the Low Ford, still marching. They do not hurry. They do not have to." },
        new() { Id = "risen_warrior", Name = "Risen Shieldman", Family = Family.Undead, Faction = Faction.Dead, Visual = "skeleton_warrior",
            Health = 46, Speed = 2.4, Damage = 11, Radius = 0.5, Mass = 1.6, Xp = 4, Resists = Undead, Behavior = Behavior.Guard,
            Guard = new(1.4, 0.75),
            Note = "Buried with his shield, and he has not let go of it. Arrows and bolts glance off the face of it; take him from the side." },
        new() { Id = "risen_archer", Name = "Risen Bowman", Family = Family.Undead, Faction = Faction.Dead, Visual = "skeleton_rogue",
            Health = 22, Speed = 2.5, Damage = 6, Radius = 0.45, Xp = 4, Resists = Undead, Behavior = Behavior.Ranged,
            Ranged = new() { Range = 9, Cooldown = 3.3, Speed = 11, School = School.Physical, Art = "bolt_bone" },
            Note = "Still keeps the ford the way it was taught: from behind the others, at a distance. Close it." },
        new() { Id = "grave_caller", Name = "Grave-Caller", Family = Family.Undead, Faction = Faction.Dead, Visual = "skeleton_mage",
            Health = 34, Speed = 2.2, Damage = 9, Radius = 0.45, Xp = 7, Resists = Undead, Behavior = Behavior.Caster,
            Ranged = new() { Range = 10, Cooldown = 3.4, Speed = 7, School = School.Frost, Slow = (0.6, 1.4), Art = "frost_orb" },
            Raise = new(7, 2, "risen", 7),
            Note = "Wherever one of these walks, the fallen get up again. Kill it first, or you will be killing the same dead twice." },
        new() { Id = "barrow_knight", Name = "Barrow Knight", Family = Family.Undead, Faction = Faction.Dead, Visual = "skeleton_warrior_elite", Scale = 1.45,
            Health = 420, Speed = 2.6, Damage = 22, Radius = 0.8, Mass = 5, Xp = 40, Gold = 12, Resists = Undead, Behavior = Behavior.Chase,
            Lunge = new(8, 5.5, 0.75, 0.5, 17),
            Elite = true, Loot = "elite", AttackEvery = 1.1,
            Note = "A knight once, still standing a knight's watch over the wrong side. Plants, picks you, and comes down the line. Be off the line." },
        new() { Id = "ford_warden", Name = "The Ford-Warden", Family = Family.Undead, Faction = Faction.Dead, Visual = "view:warden", Scale = 2.6,
            Health = 2600, Speed = 2.4, Damage = 26, Radius = 1.4, Mass = 30, Xp = 90, Gold = 40, Resists = Undead, Behavior = Behavior.Boss,
            Boss = true, AttackEvery = 1.4,
            Note = "The Watch set it to keep the Low Ford, when there was a Watch. It kept the ford. It is keeping it still, from everyone. The lamps around the crossing feed it; while they burn, it is hard to hurt." },

        /* ------------------------------------------------------------ lamplings -- */
        new() { Id = "lampling", Name = "Lampling Tunneler", Family = Family.Lampling, Faction = Faction.Lampling, Visual = "lampling",
            Health = 20, Speed = 3.6, Damage = 8, Radius = 0.38, Xp = 2, Behavior = Behavior.Tunneler, Resists = new() { [School.Fire] = 0.3, [School.Frost] = -0.3 },
            Note = "They dig toward light the way moths fly at it. A lampling will chew through a cellar wall to sit beside your candle, and then through you to keep it." },
        new() { Id = "grimtunnel", Name = "Grimtunnel", Family = Family.Lampling, Faction = Faction.Lampling, Visual = "grimtunnel", Scale = 1.9,
            Health = 400, Speed = 5, Damage = 10, Radius = 0.7, Xp = 0, Behavior = Behavior.Stationary, Resists = new() { [School.Fire] = 0.5 },
            Note = "The Boss of the Dig. Wears three lamps and a grudge. Took the Ford-Warden's heart out from under you and went back down the hole with it." },
        new() { Id = "grimtunnel_roused", Name = "Grimtunnel, Roused", Family = Family.Lampling, Faction = Faction.Lampling, Visual = "grimtunnel", Scale = 2.4,
            Health = 460, Speed = 3.3, Damage = 16, Radius = 1.0, Mass = 14, Xp = 40, Gold = 12, Behavior = Behavior.Chase, Resists = new() { [School.Fire] = 0.5, [School.Frost] = -0.2 },
            Ranged = new() { Range = 11, Cooldown = 4.5, Speed = 8, School = School.Fire, Lob = true, Zone = new(2.2, 3.5, 0.4), Art = "firepot" },
            Elite = true, AttackEvery = 1.2,
            Note = "Out of his hole and in a temper. The three lamps swing as he comes, and every one of them is lit." },
        new() { Id = "lampling_sapper", Name = "Lampling Sapper", Family = Family.Lampling, Faction = Faction.Lampling, Visual = "lampling_sapper",
            Health = 24, Speed = 2.9, Damage = 8, Radius = 0.4, Xp = 4, Behavior = Behavior.Ranged, Resists = new() { [School.Fire] = 0.5, [School.Frost] = -0.3 },
            Ranged = new() { Range = 8, Cooldown = 4.4, Speed = 8, School = School.Fire, Lob = true, Zone = new(1.6, 3, 0.35), Art = "firepot" },
            Burst = new(2.2, 1.2, 0.6, School.Fire, StatusKind.Burn),
            Note = "Carries a satchel of the Boss's blasting ember and throws it at whatever looks brightest. Dies loudly. Stand clear." },

        /* --------------------------------------------------------------- beasts -- */
        new() { Id = "wolf", Name = "Longtooth Wolf", Family = Family.Wolf, Faction = Faction.Pack, Visual = "wolf",
            Health = 30, Speed = 5.3, Damage = 9, Radius = 0.5, Xp = 4, Resists = Beast, Behavior = Behavior.Pack, AttackEvery = 0.9,
            Tags = [Tag.Nature], Loot = "wolf",
            Note = "Never alone. If you have counted one, count again. They come at you from every side at once, and they know which side you are not watching." },
        new() { Id = "wolf_blighted", Name = "Blight-Sick Wolf", Family = Family.Wolf, Faction = Faction.Pack, Visual = "wolf_blighted",
            Health = 38, Speed = 4.4, Damage = 10, Radius = 0.5, Xp = 5, Resists = new(Beast) { [School.Shadow] = 0.3 }, Behavior = Behavior.Chase,
            Burst = new(2.4, 0.6, 0.5, School.Nature, StatusKind.Poison),
            Loot = "wolf",
            Note = "Its eyes are wrong and its breath is green. Something in the water. It is not hunting you; it is running from what hurts, and you are in the way." },
        new() { Id = "wolf_alpha", Name = "Greymuzzle", Family = Family.Wolf, Faction = Faction.Pack, Visual = "wolf_alpha", Scale = 1.5,
            Health = 520, Speed = 5.4, Damage = 18, Radius = 0.85, Mass = 5, Xp = 55, Resists = Beast, Behavior = Behavior.Pack,
            Lunge = new(9, 4.8, 0.6, 0.45, 19),
            Elite = true, Loot = "alpha", AttackEvery = 0.8,
            Note = "The pack's oldest. Grey to the eyes and in no hurry. The others follow him because he has never once been wrong about where to go." },
        new() { Id = "boar", Name = "Thicket Tusker", Family = Family.Boar, Faction = Faction.Wild, Visual = "boar",
            Health = 44, Speed = 3.2, Damage = 12, Radius = 0.6, Mass = 2.5, Xp = 5, Resists = Beast, Behavior = Behavior.Charger,
            Charge = new(10, 4.5, 0.9, 1.0, 13),
            Loot = "boar",
            Note = "Charges whatever moved last. It paws the ground first, which is your warning. A tusker that runs into a tree does not get up quickly." },

        /* ------------------------------------------------------------ Kerchiefs -- */
        new() { Id = "footpad", Name = "Kerchief Footpad", Family = Family.Kerchief, Faction = Faction.Kerchief, Visual = "kerchief_rogue",
            // (36 health and 10 a blow made the Kerchiefs the hardest people by a distance: at the third
            // tier half the nights against them fell, against one in ten for the Lamplings.)
            Health = 31, Speed = 4.2, Damage = 9, Radius = 0.48, Xp = 5, Gold = 2, Resists = Kerchief, Behavior = Behavior.Chase,
            Loot = "kerchief",
            Note = "Red cloth over the face and quick hands under it. They rob the dead first and the living second, which is at least an order." },
        new() { Id = "pillager", Name = "Kerchief Pillager", Family = Family.Kerchief, Faction = Faction.Kerchief, Visual = "kerchief_hooded",
            Health = 30, Speed = 3.4, Damage = 9, Radius = 0.48, Xp = 6, Gold = 3, Behavior = Behavior.Ranged,
            Ranged = new() { Range = 9, Cooldown = 4.2, Speed = 8.5, School = School.Fire, Lob = true, Zone = new(1.7, 3.5, 0.3), Art = "firepot" },
            Loot = "kerchief",
            Note = "The ones who throw. Firepots, bottles, once a boot: whatever the last wagon had in it." },
        new() { Id = "bruiser", Name = "Kerchief Bruiser", Family = Family.Kerchief, Faction = Faction.Kerchief, Visual = "kerchief_brute", Scale = 1.15,
            Health = 90, Speed = 3.0, Damage = 15, Radius = 0.62, Mass = 3, Xp = 9, Gold = 5, Behavior = Behavior.Guard,
            Guard = new(1.6, 0.8),
            Loot = "kerchief",
            Note = "What the Kerchiefs send when the footpads come back empty-handed. Carries a barn door for a shield. Arrows do not bother him from the front." },
        new() { Id = "enforcer", Name = "Kerchief Enforcer", Family = Family.Kerchief, Faction = Faction.Kerchief, Visual = "kerchief_enforcer", Scale = 1.35,
            Health = 480, Speed = 3.4, Damage = 22, Radius = 0.8, Mass = 5, Xp = 45, Gold = 20, Behavior = Behavior.Chase,
            Lunge = new(8.5, 5.0, 0.7, 0.45, 18),
            Elite = true, Loot = "elite", AttackEvery = 1.0,
            Note = "Plants its feet, picks you, and comes straight down the line. Step off the line." },

        /* ------------------------------------------- the night's other kinds --
         * The owner: "variety of minion types elites and mini bosses instead of all just the
         * same models of wolves". Each people's kinds and minibosses below are on the rigs we
         * have, told apart by size, colour and above all by what they do; each has a model
         * brief for the art pass (docs/SKILLS_DESIGN.md, "Encounters"). A miniboss opens a
         * stretch of the night and wears its verb first; its kinds join the horde after it
         * (Play/Zones/Escalation.cs). */

        // The Pack.
        new() { Id = "wolf_runner", Name = "Ridge-Runner", Family = Family.Wolf, Faction = Faction.Pack, Visual = "wolf", Scale = 0.88, Tint = (1.18, 1.1, 0.92),
            Health = 26, Speed = 5.6, Damage = 8, Radius = 0.45, Xp = 4, Resists = Beast, Behavior = Behavior.Orbit, AttackEvery = 0.9,
            Lunge = new(7, 5, 0.7, 0.35, 16), Tags = [Tag.Nature], Loot = "wolf",
            Note = "A yearling, pale along the back. The young run the ring while the old ones close, and cut in when you turn to the old ones." },
        new() { Id = "boar_slurry", Name = "Slurry Sow", Family = Family.Boar, Faction = Faction.Wild, Visual = "boar", Scale = 1.22, Tint = (0.72, 0.95, 0.55), Glow = 0.06,
            Health = 70, Speed = 2.6, Damage = 12, Radius = 0.68, Mass = 3, Xp = 7, Resists = Beast, Behavior = Behavior.Chase,
            Trail = new(0.6, 1.2, 3, 0.25, School.Nature), Loot = "boar",
            Note = "She drank at the Dig's outflow and carries it with her. Where she walks the ground goes green and bites." },
        new() { Id = "wolf_howler", Name = "Howler", Family = Family.Wolf, Faction = Faction.Pack, Visual = "wolf", Scale = 1.1, Tint = (0.72, 0.76, 0.9),
            Health = 60, Speed = 4.0, Damage = 8, Radius = 0.55, Xp = 9, Resists = Beast, Behavior = Behavior.Ranged,
            Aura = new(8, 9, 4, Haste: 1.25, Word: "Howl"), Tags = [Tag.Nature], Loot = "wolf",
            Note = "The Pack's caller. It hangs back and gives tongue, and the others run faster for it. Kill it and the hunt loses its voice." },
        new() { Id = "mb_old_tusk", Name = "Old Tusk", Family = Family.Boar, Faction = Faction.Wild, Visual = "boar", Scale = 1.9, Tint = (0.82, 0.76, 0.7),
            Health = 560, Speed = 3.3, Damage = 16, Radius = 1.0, Mass = 8, Xp = 40, Gold = 10, Resists = Beast, Behavior = Behavior.Charger,
            Charge = new(11, 5.5, 1.0, 1.0, 14), Chain = 2, Elite = true, Miniboss = true, Loot = "miniboss", AttackEvery = 1.1,
            Lesson = "It runs its lane three times over. Put a tree in its way.",
            Note = "The oldest tusker in the Verge, scarred to the snout. It does not stop at one run, and it does not stop for you." },
        new() { Id = "mb_whitethroat", Name = "Whitethroat", Family = Family.Wolf, Faction = Faction.Pack, Visual = "wolf", Scale = 1.5, Tint = (1.25, 1.18, 1.0), Glow = 0.05,
            Health = 480, Speed = 5.8, Damage = 14, Radius = 0.8, Mass = 5, Xp = 40, Resists = Beast, Behavior = Behavior.Orbit, AttackEvery = 0.85,
            Lunge = new(8, 4, 0.65, 0.4, 18), Summon = new(14, 4, "wolf_runner", 1.2, SpawnStyle.Walk, 7, Word: "Yip! Yip!"),
            Elite = true, Miniboss = true, Loot = "miniboss", Tags = [Tag.Nature],
            Lesson = "The young run a ring round you, then cut in. Break the ring.",
            Note = "A pale she-wolf who leads the yearlings. She circles, and they circle with her, and when she cuts in so do they." },
        new() { Id = "mb_blight_mother", Name = "Greenbelly", Family = Family.Wolf, Faction = Faction.Pack, Visual = "wolf_blighted", Scale = 1.75, Tint = (0.75, 1.05, 0.6), Glow = 0.12,
            Health = 600, Speed = 4.0, Damage = 14, Radius = 0.95, Mass = 6, Xp = 40, Resists = new(Beast) { [School.Shadow] = 0.3 }, Behavior = Behavior.Chase,
            Trail = new(0.5, 1.4, 3.5, 0.3, School.Nature), Burst = new(3.2, 1.2, 0.9, School.Nature, StatusKind.Poison), Split = new("wolf_blighted", 3), Bite = StatusKind.Poison,
            Elite = true, Miniboss = true, Loot = "miniboss", AttackEvery = 1.0,
            Lesson = "Sick to bursting, and so are hers. Do not be beside them when they die.",
            Note = "Heavy with a litter, and with the slurry that got into the litter. Everything about her is green, and everything she leaves behind is worse." },
        new() { Id = "mb_outflow_sow", Name = "The Outflow Sow", Family = Family.Boar, Faction = Faction.Wild, Visual = "boar", Scale = 2.0, Tint = (0.62, 0.88, 0.45), Glow = 0.1,
            Health = 700, Speed = 2.8, Damage = 15, Radius = 1.05, Mass = 9, Xp = 40, Gold = 10, Resists = Beast, Behavior = Behavior.Charger,
            Charge = new(10, 6, 1.1, 1.1, 12), Trail = new(0.35, 1.5, 4, 0.3, School.Nature), Elite = true, Miniboss = true, Loot = "miniboss", AttackEvery = 1.2,
            Lesson = "Where it runs, the ground goes bad. Off the lane, and not into the slurry.",
            Note = "The sow that lives in the Dig's outflow and has grown to its size. Its lanes stay green long after it has gone down them." },
        new() { Id = "mb_caller", Name = "Old Blue", Family = Family.Wolf, Faction = Faction.Pack, Visual = "wolf_alpha", Scale = 1.35, Tint = (0.68, 0.72, 0.9),
            Health = 520, Speed = 4.4, Damage = 12, Radius = 0.8, Mass = 5, Xp = 40, Resists = Beast, Behavior = Behavior.Ranged,
            Aura = new(7, 11, 4.5, Haste: 1.35, Word: "Howl"), Summon = new(12, 5, "wolf", 1.4, SpawnStyle.Walk, 9, AtTarget: true, Max: 20, Word: "Awoooo"),
            Elite = true, Miniboss = true, Loot = "miniboss", Tags = [Tag.Nature],
            Lesson = "While it howls the Pack runs faster, and more come. Find it behind them.",
            Note = "Grey-blue and old, and never at the front. It calls the Pack in from the trees and sets it running." },

        // The Risen.
        new() { Id = "bone_heap", Name = "Bone-Heap", Family = Family.Undead, Faction = Faction.Dead, Visual = "skeleton_minion", Scale = 1.45, Tint = (1.12, 1.06, 0.9),
            Health = 70, Speed = 2.0, Damage = 12, Radius = 0.72, Mass = 2.5, Xp = 6, Resists = Undead, Behavior = Behavior.Chase,
            Split = new("risen", 3),
            Note = "The Legion buried its dead by the file, in one barrow, and they get up the same way. Break it and it comes apart into three that walk on." },
        new() { Id = "drowned", Name = "Drowned", Family = Family.Undead, Faction = Faction.Dead, Visual = "skeleton_minion", Scale = 1.05, Tint = (0.6, 0.82, 0.88), Glow = 0.05,
            Health = 50, Speed = 2.0, Damage = 10, Radius = 0.55, Xp = 5, Resists = Undead, Behavior = Behavior.Chase,
            Trail = new(0.8, 1.3, 3.5, 0.2, School.Frost), Bite = StatusKind.Chill,
            Note = "The Low Ford keeps what it drowns. They come up weed-hung and cold, and leave the cold where they walk." },
        new() { Id = "risen_bell", Name = "Horn-Blower", Family = Family.Undead, Faction = Faction.Dead, Visual = "skeleton_mage", Tint = (1.15, 0.98, 0.72),
            Health = 40, Speed = 2.2, Damage = 6, Radius = 0.5, Xp = 9, Resists = Undead, Behavior = Behavior.Ranged,
            Aura = new(9, 9, 4, Haste: 1.25, Word: "Horn"),
            Note = "The Legion marched to the horn. One of them still blows his, and the dead come quicker to it. Silence it first." },
        new() { Id = "legionary", Name = "Legion Shield-Rusher", Family = Family.Undead, Faction = Faction.Dead, Visual = "skeleton_warrior", Scale = 1.12, Tint = (1.05, 0.82, 0.68),
            Health = 52, Speed = 2.5, Damage = 12, Radius = 0.52, Mass = 2, Xp = 6, Resists = Undead, Behavior = Behavior.Guard,
            Guard = new(1.2, 0.6), Lunge = new(6.5, 6, 0.8, 0.4, 13),
            Note = "Older than the ford's dead, in bronze gone green. It sets its shield and comes behind it at a run. Off the line, then round the shield." },
        new() { Id = "mb_old_quarrel", Name = "The Scorpion", Family = Family.Undead, Faction = Faction.Dead, Visual = "skeleton_rogue", Scale = 1.55, Tint = (1.0, 0.95, 0.85),
            // (Measured: 52 s to kill, 126 at the slowest; a kiter that long is a chase, not a fight.)
            Health = 300, Speed = 2.4, Damage = 10, Radius = 0.75, Mass = 4, Xp = 40, Resists = Undead, Behavior = Behavior.Ranged,
            Ranged = new() { Range = 11, Cooldown = 2.6, Speed = 12, School = School.Physical, Count = 5, Spread = 0.2, Art = "bolt_bone" },
            Elite = true, Miniboss = true, Loot = "miniboss",
            Lesson = "Five bolts in a fan. Stand in a gap, or close on it.",
            Note = "The Legion called its bolt-engine a scorpion. This one has carried his for two thousand years and no longer needs it: he looses five where it loosed one, and he has not forgotten how to keep his distance." },
        new() { Id = "mb_decurion", Name = "The Decurion", Family = Family.Undead, Faction = Faction.Dead, Visual = "skeleton_warrior", Scale = 1.65, Tint = (1.05, 0.85, 0.7),
            // (Measured: 49 s, 123 at the slowest, behind a three-quarter shield: now three fifths, as a champion's;
            // still 43 s at 560 and 54 s at 460 once the third tier's minibosses came a quarter stronger.)
            Health = 380, Speed = 2.4, Damage = 16, Radius = 0.95, Mass = 8, Xp = 40, Resists = Undead, Behavior = Behavior.Guard,
            Guard = new(1.6, 0.6), Lunge = new(7, 6, 0.8, 0.45, 14), Summon = new(14, 4, "risen_warrior", 1.4, SpawnStyle.Rise, 3, Word: "Scuta!"),
            Elite = true, Miniboss = true, Loot = "miniboss", AttackEvery = 1.2,
            Lesson = "Shields to the front. Go round them.",
            Note = "A decurion of the Seventh, still dressing his line. Where he stands, shields come up out of the ground beside him." },
        new() { Id = "mb_the_heap", Name = "The Heap", Family = Family.Undead, Faction = Faction.Dead, Visual = "skeleton_minion", Scale = 2.1, Tint = (1.15, 1.08, 0.88),
            Health = 720, Speed = 1.9, Damage = 16, Radius = 1.05, Mass = 9, Xp = 40, Resists = Undead, Behavior = Behavior.Chase,
            Split = new("bone_heap", 3), Slam = new(3.5, 6, 1.0, 2.6, 1.5, Self: true), Elite = true, Miniboss = true, Loot = "miniboss", AttackEvery = 1.3,
            Lesson = "Many dead in one body. It comes apart, and its parts come apart.",
            Note = "A whole barrow walking. It falls on what is near it, and when it is broken it is not finished." },
        new() { Id = "mb_drowned_reeve", Name = "The Weed-Wife", Family = Family.Undead, Faction = Faction.Dead, Visual = "skeleton_mage", Scale = 1.6, Tint = (0.55, 0.8, 0.9), Glow = 0.08,
            // (Measured: 44 s, 173 at the slowest: a caster that keeps its distance is a chase at 560.)
            Health = 400, Speed = 2.1, Damage = 12, Radius = 0.85, Mass = 6, Xp = 40, Resists = Undead, Behavior = Behavior.Caster,
            Ranged = new() { Range = 10, Cooldown = 2.8, Speed = 7, School = School.Frost, Count = 3, Spread = 0.35, Slow = (0.6, 1.4), Art = "frost_orb" },
            Trail = new(0.6, 1.5, 4, 0.25, School.Frost), Bite = StatusKind.Chill, Elite = true, Miniboss = true, Loot = "miniboss",
            Lesson = "The river's cold walks with her. Keep off her wet ground.",
            Note = "The river has had her longer than the ford's new dead, and the weed has grown through her. She brings the cold up out of the water with her, and it stays where she walks." },
        new() { Id = "mb_ford_bell", Name = "The Signifer", Family = Family.Undead, Faction = Faction.Dead, Visual = "skeleton_mage", Scale = 1.5, Tint = (1.2, 1.0, 0.7), Glow = 0.1,
            Health = 520, Speed = 2.2, Damage = 9, Radius = 0.8, Mass = 5, Xp = 40, Resists = Undead, Behavior = Behavior.Ranged,
            Aura = new(7, 11, 4.5, Haste: 1.3, Ward: 0.25, Word: "Signa!"), Raise = new(8, 3, "risen", 8), Elite = true, Miniboss = true, Loot = "miniboss",
            Lesson = "While the standard stands, the dead are quicker and harder to hurt. Bring it down.",
            Note = "The Legion's signifer, who carried its standard: VII on a rag that was red once. The dead quicken and harden where it goes, and the fallen get up to follow it." },

        // The Lamplings.
        new() { Id = "lampling_wick", Name = "Wick", Family = Family.Lampling, Faction = Faction.Lampling, Visual = "lampling", Scale = 0.72, Tint = (1.3, 1.12, 0.8), Glow = 0.3,
            Health = 10, Speed = 4.6, Damage = 5, Radius = 0.32, Xp = 1.5, Behavior = Behavior.Pack, AttackEvery = 0.8, Resists = new() { [School.Fire] = 0.3, [School.Frost] = -0.3 },
            Note = "The youngest of the Dig, a candle-stub on the head. Sent up first, because they run fastest and the Dig has more." },
        new() { Id = "lampling_fuse", Name = "Fuse-Runner", Family = Family.Lampling, Faction = Faction.Lampling, Visual = "lampling_sapper", Scale = 1.08, Tint = (1.3, 0.75, 0.5), Glow = 0.18,
            Health = 26, Speed = 3.2, Damage = 9, Radius = 0.42, Xp = 5, Behavior = Behavior.Charger, Resists = new() { [School.Fire] = 0.5, [School.Frost] = -0.3 },
            Charge = new(11, 5, 1.0, 0.9, 12), RunBursts = true, Burst = new(2.6, 1.6, 0.6, School.Fire, StatusKind.Burn),
            Note = "Carries a lit crate of the Dig's blasting ember at a run, straight down a lane, and goes up where the lane ends. Kill it far off." },
        new() { Id = "lampling_lamp", Name = "Lamp-Thrower", Family = Family.Lampling, Faction = Faction.Lampling, Visual = "lampling", Scale = 1.05, Tint = (0.85, 0.98, 1.35), Glow = 0.35,
            Health = 28, Speed = 2.7, Damage = 7, Radius = 0.4, Xp = 5, Behavior = Behavior.Ranged, Resists = new() { [School.Fire] = 0.5, [School.Frost] = -0.3 },
            Ranged = new() { Range = 9, Cooldown = 3.6, Speed = 9, School = School.Fire, Count = 3, Spread = 0.3, Art = "cinder" },
            Note = "Shakes three flames out of its lamp at once, in a fan. The gaps are there to be stood in." },
        new() { Id = "mb_wick_mother", Name = "The Wick-Mother", Family = Family.Lampling, Faction = Faction.Lampling, Visual = "lampling", Scale = 1.6, Tint = (1.3, 1.15, 0.8), Glow = 0.3,
            Health = 420, Speed = 3.6, Damage = 10, Radius = 0.8, Mass = 4, Xp = 40, Behavior = Behavior.Pack, Resists = new() { [School.Fire] = 0.3, [School.Frost] = -0.3 },
            Summon = new(10, 6, "lampling_wick", 1.0, SpawnStyle.Burrow, 6, AtTarget: true, Max: 30, Word: "Up, up, up!"),
            Elite = true, Miniboss = true, Loot = "miniboss", AttackEvery = 1.0,
            Lesson = "She sends the little ones up first, all round you. They run fast and die quick.",
            Note = "Mother of every wick in her tunnel, and she has a great many tunnels. She calls; the ground answers." },
        new() { Id = "mb_bombardier", Name = "The Chucker", Family = Family.Lampling, Faction = Faction.Lampling, Visual = "lampling_sapper", Scale = 1.6, Tint = (1.2, 0.85, 0.65),
            // (Measured: 47 s at 420, 102 at the slowest.)
            Health = 300, Speed = 2.7, Damage = 10, Radius = 0.8, Mass = 4, Xp = 40, Behavior = Behavior.Ranged, Resists = new() { [School.Fire] = 0.5, [School.Frost] = -0.3 },
            Ranged = new() { Range = 10, Cooldown = 3.4, Speed = 8, School = School.Fire, Lob = true, Count = 3, Spread = 0.45, Zone = new(1.8, 3.5, 0.35), Art = "firepot" },
            Burst = new(3, 1.2, 0.8, School.Fire, StatusKind.Burn), Elite = true, Miniboss = true, Loot = "miniboss",
            Lesson = "Three pots at a time. Where they land, it burns.",
            Note = "The Dig's best thrower, which is to say its worst neighbour. Three pots in the air before the first has landed." },
        new() { Id = "mb_lamplighter", Name = "The Lamplighter", Family = Family.Lampling, Faction = Faction.Lampling, Visual = "lampling", Scale = 1.7, Tint = (0.8, 0.95, 1.4), Glow = 0.45,
            // (Measured: 35 s at 480.)
            Health = 380, Speed = 2.6, Damage = 9, Radius = 0.85, Mass = 5, Xp = 40, Behavior = Behavior.Ranged, Resists = new() { [School.Fire] = 0.5, [School.Frost] = -0.3 },
            Ranged = new() { Range = 10, Cooldown = 3.0, Speed = 9, School = School.Fire, Count = 5, Spread = 0.22, Art = "cinder" },
            Aura = new(8, 9, 4, Ward: 0.3, Word: "Light!"), Elite = true, Miniboss = true, Loot = "miniboss",
            Lesson = "Five flames in a fan, and its light wards the diggers near it.",
            Note = "Keeper of the Dig's great lamp, which it carries lit. The diggers in its light are harder to hurt. Put it out." },
        new() { Id = "mb_fuse_boss", Name = "The Perfect of Fuses", Family = Family.Lampling, Faction = Faction.Lampling, Visual = "lampling_sapper", Scale = 1.9, Tint = (1.35, 0.7, 0.45), Glow = 0.2,
            Health = 620, Speed = 3.0, Damage = 14, Radius = 0.95, Mass = 7, Xp = 40, Behavior = Behavior.Charger, Resists = new() { [School.Fire] = 0.5, [School.Frost] = -0.3 },
            Charge = new(12, 6, 1.1, 1.0, 12), Chain = 2, Trail = new(0.3, 1.3, 3, 0.3, School.Fire), Burst = new(4, 1.6, 1.2, School.Fire, StatusKind.Burn),
            Elite = true, Miniboss = true, Loot = "miniboss", AttackEvery = 1.2,
            Lesson = "Blasting ember carried at a run, three lanes a time. Off the lane, and away when it falls.",
            Note = "It carries the biggest crate in the Dig, and it has never once put it down. Its title is older than the Dig. Its lanes burn behind it." },
        new() { Id = "mb_gaffer", Name = "The Gaffer", Family = Family.Lampling, Faction = Faction.Lampling, Visual = "lampling", Scale = 2.0, Tint = (0.95, 0.9, 0.8), Glow = 0.15,
            Health = 640, Speed = 3.2, Damage = 14, Radius = 1.0, Mass = 7, Xp = 40, Behavior = Behavior.Tunneler, Resists = new() { [School.Fire] = 0.3, [School.Frost] = -0.3 },
            Slam = new(3.2, 7, 1.0, 3, 1.4, Self: true), Summon = new(12, 4, "lampling", 1.2, SpawnStyle.Burrow, 5, AtTarget: true, Max: 24, Word: "Dig!"),
            Elite = true, Miniboss = true, Loot = "miniboss", AttackEvery = 1.1,
            Lesson = "The ground is the Dig's. Where it comes up, it brings the rest.",
            Note = "A tunnel-gang's gaffer, as broad as the tunnels. It goes under, comes up beside you, and brings its gang up with it." },

        // The Kerchiefs.
        new() { Id = "levy_crossbow", Name = "Levy Crossbow", Family = Family.Kerchief, Faction = Faction.Kerchief, Visual = "kerchief_hooded", Scale = 0.98, Tint = (0.8, 0.85, 0.95),
            Health = 28, Speed = 3.0, Damage = 7, Radius = 0.48, Xp = 6, Gold = 2, Resists = Kerchief, Behavior = Behavior.Ranged,
            Ranged = new() { Range = 10, Cooldown = 3.6, Speed = 12, School = School.Physical, Count = 3, Spread = 0.22, Art = "bolt_bone" }, Loot = "kerchief",
            Note = "The levy kept its crossbows when it lost everything else. Three bolts in a fan, and gaps between them wide enough to stand in." },
        new() { Id = "levy_pike", Name = "Levy Pikeman", Family = Family.Kerchief, Faction = Faction.Kerchief, Visual = "kerchief_rogue", Scale = 1.08, Tint = (1.1, 0.95, 0.72),
            Health = 40, Speed = 3.8, Damage = 11, Radius = 0.5, Xp = 6, Gold = 2, Resists = Kerchief, Behavior = Behavior.Chase,
            Lunge = new(8, 5.5, 0.75, 0.4, 16), Loot = "kerchief",
            Note = "The levy still drills with its pikes in the ruts below the Roost, every morning, as if it had a town to march for." },
        new() { Id = "kerchief_drummer", Name = "Levy Drummer", Family = Family.Kerchief, Faction = Faction.Kerchief, Visual = "kerchief_hooded", Scale = 1.12, Tint = (1.2, 0.72, 0.7),
            Health = 45, Speed = 2.6, Damage = 6, Radius = 0.5, Xp = 9, Gold = 3, Resists = Kerchief, Behavior = Behavior.Ranged,
            Aura = new(8, 9, 4, Haste: 1.2, Word: "Drum"), Loot = "kerchief",
            Note = "The levy marched to a drum. They still do, to rob a wagon, and they come quicker for it. The drumming stops when it dies." },
        new() { Id = "mb_firepot_nan", Name = "Firepot Nan", Family = Family.Kerchief, Faction = Faction.Kerchief, Visual = "kerchief_hooded", Scale = 1.5, Tint = (1.1, 0.85, 0.75),
            // (Measured: 35 s at 400, 134 at the slowest: the third minute's build has little to reach her with.)
            Health = 300, Speed = 3.2, Damage = 10, Radius = 0.75, Mass = 4, Xp = 40, Gold = 15, Resists = Kerchief, Behavior = Behavior.Ranged,
            Ranged = new() { Range = 10, Cooldown = 3.2, Speed = 8.5, School = School.Fire, Lob = true, Count = 3, Spread = 0.45, Zone = new(1.7, 3.5, 0.3), Art = "firepot" },
            Elite = true, Miniboss = true, Loot = "miniboss",
            Lesson = "Three pots at once, and the throwers follow her. Close on her through the gaps.",
            Note = "She cooked for forty-one mouths on the road, and she throws the way she cooks: three pots at a time and none of them cold." },
        new() { Id = "mb_pike_captain", Name = "The Pike-Captain", Family = Family.Kerchief, Faction = Faction.Kerchief, Visual = "kerchief_rogue", Scale = 1.55, Tint = (1.15, 0.92, 0.7),
            Health = 520, Speed = 4.0, Damage = 15, Radius = 0.8, Mass = 6, Xp = 40, Gold = 15, Resists = Kerchief, Behavior = Behavior.Chase,
            Lunge = new(9, 5, 0.8, 0.45, 17), Chain = 1, Summon = new(14, 4, "levy_pike", 1.2, SpawnStyle.Walk, 11, AtTarget: true, Word: "Pikes!"),
            Elite = true, Miniboss = true, Loot = "miniboss", AttackEvery = 1.0,
            Lesson = "It runs at you twice, and calls pikes in from the dark to do the same.",
            Note = "Led the levy's pikes the one time it mattered, against something pikes are no use against, and came back. Not many did. It has not let the rest stop drilling since." },
        new() { Id = "mb_barn_door", Name = "Barn-Door", Family = Family.Kerchief, Faction = Faction.Kerchief, Visual = "kerchief_brute", Scale = 1.7, Tint = (1.05, 0.9, 0.85),
            Health = 760, Speed = 2.8, Damage = 18, Radius = 1.0, Mass = 10, Xp = 40, Gold = 15, Resists = Kerchief, Behavior = Behavior.Guard,
            Guard = new(1.8, 0.8), Slam = new(4.5, 6, 1.1, 2.4, 1.6, Word: "Down!"), Elite = true, Miniboss = true, Loot = "miniboss", AttackEvery = 1.3,
            Lesson = "Nothing goes through that door from the front. Go round it, and off the ground it brings down.",
            Note = "Carries a barn door. The barn it came off is gone, with the farm and the rest of the street, and he will not put down what is left." },
        new() { Id = "mb_levy_sergeant", Name = "The Levy Sergeant", Family = Family.Kerchief, Faction = Faction.Kerchief, Visual = "kerchief_hooded", Scale = 1.55, Tint = (0.85, 0.85, 1.0),
            Health = 480, Speed = 3.0, Damage = 10, Radius = 0.78, Mass = 5, Xp = 40, Gold = 15, Resists = Kerchief, Behavior = Behavior.Ranged,
            Ranged = new() { Range = 11, Cooldown = 2.8, Speed = 13, School = School.Physical, Count = 5, Spread = 0.18, Art = "bolt_bone" },
            Summon = new(15, 3, "levy_crossbow", 1.2, SpawnStyle.Walk, 12, AtTarget: true, Max: 9, Word: "Loose!"), Elite = true, Miniboss = true, Loot = "miniboss",
            Lesson = "Volleys of five, and a file of crossbows behind. Stand in the gaps, or close.",
            Note = "Still drills the levy's crossbows by the old count, and still calls the loose. The bolts have only got better." },
        new() { Id = "mb_drum_major", Name = "The Drum-Major", Family = Family.Kerchief, Faction = Faction.Kerchief, Visual = "kerchief_enforcer", Scale = 1.45, Tint = (1.25, 0.7, 0.7), Glow = 0.08,
            Health = 600, Speed = 3.2, Damage = 15, Radius = 0.85, Mass = 6, Xp = 40, Gold = 15, Resists = Kerchief, Behavior = Behavior.Ranged,
            Aura = new(6, 12, 4.5, Haste: 1.3, Word: "Drum"), Summon = new(12, 6, "footpad", 1.2, SpawnStyle.Walk, 13, AtTarget: true, Max: 30, Word: "To me!"),
            Elite = true, Miniboss = true, Loot = "miniboss", AttackEvery = 1.0,
            Lesson = "It beats the levy in from every side and quickens them. Find the drum.",
            Note = "The levy's drum-major, in red to the elbows, the old colour. Where the drum goes the Kerchiefs go, quicker than you would think." },

        /* ------------------------------------- what rules a people, at the half hour -- */
        // The arena's bosses (Play/Bosses/ArenaBosses.cs): their people's champion's body made
        // half again as big, so the thing the fight is about is the thing the eye finds; health
        // as the champion's, multiplied by the boss contract (ArenaBoss.HealthMul).
        new() { Id = "boss_pack", Name = "The Pack-Mother", Family = Family.Wolf, Faction = Faction.Pack, Visual = "wolf_alpha", Scale = 2.15,
            Health = 520, Speed = 5.4, Damage = 18, Radius = 1.2, Mass = 14, Xp = 55, Resists = Beast, Behavior = Behavior.Pack,
            Lunge = new(9, 4.8, 0.6, 0.45, 19),
            Elite = true, Loot = "alpha", AttackEvery = 0.8,
            Note = "She does not chase. She howls, the Pack wheels round behind you, and she runs the gap they leave. Go through the wolves, never the gap. Fire stops her howling." },
        new() { Id = "boss_dead", Name = "The Barrow Lord", Family = Family.Undead, Faction = Faction.Dead, Visual = "skeleton_warrior_elite", Scale = 2.05,
            // Not the dead's frost and shadow: every school can lay him down in time; holy twice as fast.
            Health = 420, Speed = 2.6, Damage = 22, Radius = 1.1, Mass = 14, Xp = 40, Gold = 12, Resists = new() { [School.Holy] = -0.5, [School.Fire] = -0.15 }, Behavior = Behavior.Chase,
            Lunge = new(8, 5.5, 0.75, 0.5, 17),
            Elite = true, Loot = "elite", AttackEvery = 1.1,
            Note = "A legion's officer who heard the order to stand and never heard another. He fights in walls of his dead. Put down, he gets up again, unless someone stands over him until he stays down." },
        new() { Id = "boss_lamplings", Name = "Gutterwick", Family = Family.Lampling, Faction = Faction.Lampling, Visual = "lampling_sapper", Scale = 2.2,
            Health = 460, Speed = 3.3, Damage = 16, Radius = 0.95, Mass = 12, Xp = 40, Gold = 12, Behavior = Behavior.Chase, Resists = new() { [School.Fire] = 0.5, [School.Frost] = -0.2 },
            Ranged = new() { Range = 11, Cooldown = 4.5, Speed = 8, School = School.Fire, Lob = true, Zone = new(2.2, 3.5, 0.4), Art = "firepot" },
            Elite = true, AttackEvery = 1.2,
            Note = "Foreman of a Dig gang, the biggest of them and the loudest. Where it stands the ground is not to be trusted: it goes under, comes up under you, and leaves holes. Frost catches it in the dirt." },
        new() { Id = "boss_kerchiefs", Name = "The Red Hand", Family = Family.Kerchief, Faction = Faction.Kerchief, Visual = "kerchief_enforcer", Scale = 1.9,
            Health = 480, Speed = 3.4, Damage = 22, Radius = 1.1, Mass = 14, Xp = 45, Gold = 20, Behavior = Behavior.Chase,
            Lunge = new(8.5, 5.0, 0.7, 0.45, 18),
            Elite = true, Loot = "elite", AttackEvery = 1.0,
            Note = "He takes a toll: your best weapon, for a while, and a runner to carry it off. Catch the runner. Lightning makes him drop it." },

        // The Lamplings' champion, until the Blasting-Cart has its art: a ganger of the Dig. Their
        // heralds were a lampling's body at twenty health, down in four seconds (every other people's
        // herald took twenty to forty), so their nights asked nothing of a draft's single-target reach.
        new() { Id = "lampling_ganger", Name = "Ganger of the Dig", Family = Family.Lampling, Faction = Faction.Lampling, Visual = "lampling", Scale = 1.35, Tint = (1.15, 1.02, 0.86), Glow = 0.12,
            Health = 460, Speed = 3.4, Damage = 14, Radius = 0.75, Mass = 5, Xp = 40, Behavior = Behavior.Tunneler, Resists = new() { [School.Fire] = 0.3, [School.Frost] = -0.3 },
            Slam = new(3, 7, 1.0, 2.6, 1.2, Self: true), Elite = true, AttackEvery = 1.1, Loot = "elite",
            Note = "One of the Dig's gangers: a pick, a lamp, and a gang under the ground behind it." },

        /* ------------------------------------------- the Kindling (minute 15) -- */
        // (docs/bosses/SURVIVORS_BOSSES.md 9.) The heart of the ember scar the arena was opened from,
        // and round it what rules the people's own creature, with one of its ruler's verbs: the
        // night's first verse of its boss. Drawn by the zone (an orb and its light), not the crowd.
        new() { Id = "ember_core", Name = "The Ember-Core", Family = Family.Elemental, Faction = Faction.Wild, Visual = "view:ember_core",
            Health = 100, Speed = 0, Damage = 0, Radius = 1.2, Mass = 999, Xp = 0, Behavior = Behavior.Stationary, AttackEvery = 1e9,
            Note = "Raw ember the size of a cart wheel, come up out of the scar the arena was opened from. Broken quickly, it gives more than it takes." },
        new() { Id = "lt_pack", Name = "The Pack-Mother's Yearling", Family = Family.Wolf, Faction = Faction.Pack, Visual = "wolf_alpha", Scale = 1.2, Tint = (1.12, 0.98, 0.86),
            Health = 400, Speed = 5.0, Damage = 14, Radius = 0.75, Mass = 4, Xp = 30, Resists = Beast, Behavior = Behavior.Pack,
            Lunge = new(10, 5, 0.8, 0.45, 18), Summon = new(13, 5, "wolf", 1.3, SpawnStyle.Walk, 10, AtTarget: true, Max: 15, Word: "A rising howl"),
            Elite = true, Tags = [Tag.Nature], AttackEvery = 0.9,
            Lesson = "She herds as her mother will: the wolves close round you, and she runs the gap. Go through the wolves.",
            Note = "Her mother's eldest, and as sure as her already of where you will run." },
        new() { Id = "lt_dead", Name = "The Barrow Lord's Hornblower", Family = Family.Undead, Faction = Faction.Dead, Visual = "skeleton_warrior_elite", Scale = 1.3, Tint = (0.95, 1.02, 0.84),
            Health = 420, Speed = 2.4, Damage = 16, Radius = 0.85, Mass = 6, Xp = 30, Resists = Undead, Behavior = Behavior.Guard,
            Guard = new(1.6, 0.5), Summon = new(13, 4, "risen_warrior", 1.3, SpawnStyle.Rise, 8, AtTarget: true, Max: 12, Word: "Iungite!"),
            Elite = true, AttackEvery = 1.2,
            Lesson = "A horn, and shields rise in a line. Go round the line's end.",
            Note = "He blew the Seventh's calls at the ford, and he blows them still. The dead dress their line to him." },
        new() { Id = "lt_lamplings", Name = "The Sapper-Foreman", Family = Family.Lampling, Faction = Faction.Lampling, Visual = "lampling_sapper", Scale = 1.4, Tint = (0.92, 0.98, 1.3), Glow = 0.35,
            Health = 380, Speed = 3.4, Damage = 12, Radius = 0.8, Mass = 5, Xp = 30, Behavior = Behavior.Tunneler, Resists = new() { [School.Fire] = 0.3, [School.Frost] = -0.3 },
            Slam = new(3.2, 6, 1.0, 3, 1.3, Self: true, Word: "Up!"), Elite = true, AttackEvery = 1.1,
            Lesson = "A mound runs at you, and it bursts up where it stops. Be gone from there.",
            Note = "One lamp, and the Dig's way of coming up out of the ground. Gutterwick taught it, and it shows." },
        new() { Id = "lt_kerchiefs", Name = "The Toll-Taker", Family = Family.Kerchief, Faction = Faction.Kerchief, Visual = "kerchief_enforcer", Scale = 1.3, Tint = (1.08, 1.06, 0.8),
            Health = 420, Speed = 3.8, Damage = 15, Radius = 0.8, Mass = 6, Xp = 30, Gold = 15, Resists = Kerchief, Behavior = Behavior.Chase,
            Lunge = new(8, 5, 0.8, 0.4, 16), Summon = new(13, 3, "footpad", 1.2, SpawnStyle.Walk, 10, AtTarget: true, Max: 9, Word: "Toll!"),
            Elite = true, AttackEvery = 1.0,
            Lesson = "It takes the Red Hand's toll before he does, and its runners come for what you carry.",
            Note = "Keeps the Red Hand's tally of who has paid. Everyone owes." },

        /* ---------------------------------------------------- your own, raised -- */
        new() { Id = "spirit_wolf", Name = "Spirit Wolf", Family = Family.Wolf, Faction = Faction.Ally, Visual = "wolf_spirit",
            Health = 60, Speed = 6.2, Damage = 14, Radius = 0.45, Xp = 0, Behavior = Behavior.Pack, AttackEvery = 0.7,
            Note = "A wolf made of the ember you carry. It hunts beside you, and it does not stay." },
        new() { Id = "mirror", Name = "Reflection", Family = Family.Human, Faction = Faction.Ally, Visual = "view:mirror",
            Health = 40, Speed = 0, Damage = 0, Radius = 0.45, Xp = 0, Behavior = Behavior.Stationary,
            Note = "You, in glass. Everything that hunts you wants it more." },
        new() { Id = "ghoul_ally", Name = "Risen Servant", Family = Family.Undead, Faction = Faction.Ally, Visual = "risen_ally",
            Health = 90, Speed = 3.0, Damage = 24, Radius = 0.5, Xp = 0, Behavior = Behavior.Chase, AttackEvery = 1.3,
            Note = "Something you killed, got up again on your side. It will not thank you." },
        new() { Id = "knight_ally", Name = "Bone Knight", Family = Family.Undead, Faction = Faction.Ally, Visual = "skeleton_warrior_elite", Scale = 1.25,
            Health = 240, Speed = 2.9, Damage = 34, Radius = 0.6, Mass = 3, Xp = 0, Behavior = Behavior.Chase, AttackEvery = 1.2,
            Note = "A knight of the barrows, in the iron it was buried in, keeping a watch for you now." },
    }.ToDictionary(e => e.Id);

    public static EnemyDef Get(string id) => All.TryGetValue(id, out var d) ? d : throw new KeyNotFoundException($"unknown enemy {id}");

    /// <summary>Health and damage multipliers at a creature level. Gentle enough
    /// that a zone revisited a few levels later is easier, steep enough that
    /// the night deepening is felt.</summary>
    public static LevelScale ScaleFor(int level)
    {
        double l = System.Math.Max(1, level) - 1;
        return new LevelScale(1 + l * 0.38 + l * l * 0.035, 1 + l * 0.14, 1 + l * 0.12);
    }

    /// <summary>The crowd visuals a zone needs ready before play: its creatures,
    /// what they raise and split into, and the survivor's own summons. Boss
    /// views (view:) are drawn otherwise and not listed.</summary>
    public static List<string> CrowdVisuals(IEnumerable<string> ids)
    {
        var seen = new HashSet<string>();
        var output = new List<string>();
        void Visit(string id)
        {
            if (!seen.Add(id)) return;
            var d = Get(id);
            if (!d.Visual.StartsWith("view:") && !output.Contains(d.Visual)) output.Add(d.Visual);
            if (d.Raise != null) Visit(d.Raise.Into);
            if (d.Split != null) Visit(d.Split.Into);
            if (d.Summon != null) Visit(d.Summon.Into);
        }
        foreach (var id in ids) Visit(id);
        foreach (var d in All.Values.Where(d => d.Faction == Faction.Ally)) Visit(d.Id);
        return output;
    }
}
