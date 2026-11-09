using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Core;

namespace SurvivorUnchained.Content;

/* Champions (docs/design/ARPG.md 5 lesson 8, 7.1): named elites with affixes, as data (data/content/champions.json).
 * An affix is the telegraph kit cast on a cadence (Quaking a ring, Charging a charge, Grasping a pull, Hemming a
 * closing) or a number on the foe (Ironhide, Swift); nothing needs new engine behavior. Encounters crowns them
 * (a beat's "champion" field) and casts their kit. */
public static class Champions
{
    public sealed class Affix
    {
        public string Id = "", Label = "";
        /// <summary>The telegraph kind it casts (telegraphs.json), or null for a number on the foe.</summary>
        public string? Kind;
        public double[] Every = [8, 12];
        public double FirstAfter = 2, Scale = 1, Weight = 1;
        public double Health = 1, Damage = 1, Speed = 1;
        /// <summary>A closing's ring: this many of its pack's first kind on the band.</summary>
        public int Foes = 8;
    }

    sealed class File
    {
        public Dictionary<string, Affix> Affixes = new();
        public int[] PerTier = [1, 1, 2, 3];
        public string[] Names = [], Epithets = [];
    }

    static File? file;
    static File F
    {
        get
        {
            if (file != null) return file;
            var f = Json.Parse<File>(Json.ReadContent("champions.json"));
            foreach (var (id, a) in f.Affixes) a.Id = id;
            return file = f;
        }
    }

    public static void Reload() => file = null;

    public static IReadOnlyDictionary<string, Affix> All => F.Affixes;
    public static Affix? Get(string id) => F.Affixes.GetValueOrDefault(id);
    public static IReadOnlyList<int> PerTier => F.PerTier;
    public static IReadOnlyList<string> Names => F.Names;
    public static IReadOnlyList<string> Epithets => F.Epithets;

    /// <summary>A rolled champion's affix count at a world tier (1-4): asked (its tier I count) and the tier's rise.</summary>
    public static int Count(int asked, int tier)
    {
        var p = F.PerTier;
        int t = Math.Clamp(tier, 1, p.Length) - 1;
        return Math.Max(0, asked + p[t] - p[0]);
    }

    /// <summary>n affixes drawn by weight, none twice, with the fight's dice. fits: which may be drawn (null: all).</summary>
    public static List<Affix> Roll(int n, Func<double> r, Func<Affix, bool>? fits = null)
    {
        var pool = F.Affixes.Values.Where(a => fits == null || fits(a)).OrderBy(a => a.Id, StringComparer.Ordinal).ToList();
        var got = new List<Affix>();
        while (got.Count < n && pool.Count > 0)
        {
            double total = pool.Sum(a => a.Weight), roll = r() * total;
            int i = 0;
            for (; i < pool.Count - 1; i++) { roll -= pool[i].Weight; if (roll < 0) break; }
            got.Add(pool[i]);
            pool.RemoveAt(i);
        }
        return got;
    }

    /// <summary>A rolled title: "Hob Marrow the Drowned", "Ketch, Who Keeps the Ford".</summary>
    public static string Title(Func<double> r)
    {
        if (F.Names.Length == 0 || F.Epithets.Length == 0) return "";
        string n = F.Names[(int)(r() * F.Names.Length) % F.Names.Length], e = F.Epithets[(int)(r() * F.Epithets.Length) % F.Epithets.Length];
        return e.StartsWith("the ", StringComparison.Ordinal) ? $"{n} {e}" : $"{n}, {e}";
    }
}
