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
}

public readonly record struct LevelScale(double Health, double Damage, double Xp);

public static class Enemies
{
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
            Health = 22, Speed = 2.5, Damage = 7, Radius = 0.45, Xp = 4, Resists = Undead, Behavior = Behavior.Ranged,
            Ranged = new() { Range = 9, Cooldown = 2.8, Speed = 11, School = School.Physical, Art = "bolt_bone" },
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
            Health = 16, Speed = 3.6, Damage = 7, Radius = 0.38, Xp = 2, Behavior = Behavior.Tunneler, Resists = new() { [School.Fire] = 0.3, [School.Frost] = -0.3 },
            Note = "They dig toward light the way moths fly at it. A lampling will chew through a cellar wall to sit beside your candle, and then through you to keep it." },
        new() { Id = "grimtunnel", Name = "Grimtunnel", Family = Family.Lampling, Faction = Faction.Lampling, Visual = "grimtunnel", Scale = 1.9,
            Health = 400, Speed = 5, Damage = 10, Radius = 0.7, Xp = 0, Behavior = Behavior.Stationary, Resists = new() { [School.Fire] = 0.5 },
            Note = "The Boss of the Dig. Wears three lamps and a grudge. Took the Ford-Warden's heart out from under you and went back down the hole with it." },
        new() { Id = "grimtunnel_roused", Name = "Grimtunnel, Roused", Family = Family.Lampling, Faction = Faction.Lampling, Visual = "grimtunnel", Scale = 2.1,
            Health = 460, Speed = 3.3, Damage = 16, Radius = 0.8, Mass = 8, Xp = 40, Gold = 12, Behavior = Behavior.Chase, Resists = new() { [School.Fire] = 0.5, [School.Frost] = -0.2 },
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
            Health = 36, Speed = 4.2, Damage = 10, Radius = 0.48, Xp = 5, Gold = 2, Resists = Kerchief, Behavior = Behavior.Chase,
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
        }
        foreach (var id in ids) Visit(id);
        foreach (var d in All.Values.Where(d => d.Faction == Faction.Ally)) Visit(d.Id);
        return output;
    }
}
