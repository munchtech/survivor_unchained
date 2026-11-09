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
        public int ItemLevels;
        /// <summary>The world fact that opens this tier (null: always open).</summary>
        public string? Opens;
    }

    sealed class File { public int Default = 2; public Dictionary<string, Tier> Tiers = new(); }

    static File? file;
    static File F => file ??= Json.Parse<File>(Json.ReadContent("world_tiers.json"));

    public const string Key = "world.tier";

    public static void Reload() => file = null;

    public static int Default => F.Default;

    /// <summary>The tiers' numbers, in order (1-4).</summary>
    public static IEnumerable<int> Numbers => F.Tiers.Keys.Select(int.Parse).OrderBy(n => n);

    /// <summary>Tier n (1-4); an unknown n is the default tier.</summary>
    public static Tier Get(int n) => F.Tiers.TryGetValue(n.ToString(), out var t) ? t : F.Tiers[F.Default.ToString()];

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
