using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Core;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Content;

/* World tiers I-IV (docs/design/ARPG.md section 7.3) as data (data/content/world_tiers.json): foe health and damage, drop
 * levels and chances, and the telegraph kit's own scale. The chosen tier is the world fact "world.tier". */
public static class WorldTiers
{
    public sealed class Tier
    {
        public string Name = "";
        public double Health = 1, Damage = 1, Rare = 1, Legendary = 1, Kit = 1;
        /// <summary>(M3) The kit's cadence in story fights (champions' affixes, packs' tells): their waits x this (under 1, more marks).</summary>
        public double KitEvery = 1;
        /// <summary>(M3) The stand clock in story fights (H6's rule, Teeth.Director's stand fields; Encounters through
        /// StandClock): a woken pack's foe charges her when she has not moved StandMoved in StandFor s. Null: none.</summary>
        public Teeth.Director? Stand;
        /// <summary>(10 Nov) The tier's `stand` row as written, kept when the clock is retired (`standOn` false: Stand
        /// is null): what the clock's own tests, and a return of it, read.</summary>
        public Teeth.Director? StandRow { get; private set; }
        internal void Retire(bool on) { StandRow = Stand; if (!on) Stand = null; }
        public int ItemLevels;
        /// <summary>The world fact that opens this tier (null: always open).</summary>
        public string? Opens;
    }

    sealed class File
    {
        public int Default = 2;
        /// <summary>(10 Nov, the owner) The story and map stand clock is retired: "some builds like archers very much
        /// move into an area and then stand still while they shoot. so that rule isn't really a thing anymore." Off, every
        /// tier's `stand` row is kept as data and read as none (null). The arena's own director keeps its stand.</summary>
        public bool StandOn = true;
        public Dictionary<string, Tier> Tiers = new();
    }

    static File? file;
    static File F => file ??= Retire(Json.Parse<File>(Json.ReadContent("world_tiers.json")));

    static File Retire(File f)
    {
        foreach (var t in f.Tiers.Values) t.Retire(f.StandOn);
        return f;
    }

    /// <summary>(10 Nov) Whether the story and map stand clock is on (world_tiers.json `standOn`).</summary>
    public static bool StandOn => F.StandOn;

    public const string Key = "world.tier";

    public static void Reload() => file = null;

    public static int Default => F.Default;

    /// <summary>The tiers' numbers, in order (1-4).</summary>
    public static IEnumerable<int> Numbers => F.Tiers.Keys.Select(int.Parse).OrderBy(n => n);

    /// <summary>Tier n (1-4); an unknown n is the default tier.</summary>
    public static Tier Get(int n) => F.Tiers.TryGetValue(n.ToString(), out var t) ? t : F.Tiers[F.Default.ToString()];

    /// <summary>(M3 round 4) The row a Wayfinder's map of this chart tier presses with (its kit, kitEvery and stand only: a
    /// map keeps its own health and damage by level): the chart's tier, past the last row the last (the lead: a map's
    /// tier is the world tier's kit and stand rows).</summary>
    public static Tier ForMap(int chartTier) => Get(Math.Clamp(chartTier, Numbers.First(), Numbers.Last()));

    /// <summary>The world's tier: its fact, else the default.</summary>
    public static int Of(WorldState w)
    {
        var f = w.Fact(Key);
        int n = f.Truthy ? (int)f.Number : F.Default;
        return F.Tiers.ContainsKey(n.ToString()) ? n : F.Default;
    }

    /// <summary>Whether tier n is open to this world (its unlock fact is true, or it has none).</summary>
    public static bool Open(WorldState w, int n) => Get(n).Opens is not { } k || w.Fact(k).Truthy;

    /// <summary>Sets the world's tier; a locked or unknown one is refused (false).</summary>
    public static bool Set(WorldState w, int n)
    {
        if (!F.Tiers.ContainsKey(n.ToString()) || !Open(w, n)) return false;
        w.Facts[Key] = n;
        return true;
    }
}
