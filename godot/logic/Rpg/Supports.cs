using System;
using System.Collections.Generic;
using System.Linq;
using SurvivorUnchained.Content;
using SurvivorUnchained.Core;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Rpg;

/* Support gems: items that slot into a skill (BUILD_DIRECTION "Supports").
 *
 * A skill opens its sockets with rank, so a favored skill sockets before a
 * fresh one (BUILD_UNLOCKS: socket 1 at rank 3, socket 2 at rank 6). Gems
 * drop with bad-luck protection (the owner, round 7): every copy she owns
 * makes that gem rarer, so the ones she lacks come. A copy sits in one
 * socket at a time. A socket closed by a lower rank keeps its gem but adds
 * nothing until the rank comes back, so a respec never eats a gem. */

public sealed class SupportDef
{
    public string Id = "", Name = "", Text = "";
    /// <summary>The skill tags it takes (Content.Tag names); empty = any skill.</summary>
    public List<string> Fits = new();
    public double Weight = 1;
    public Dictionary<string, double> Effects = new();
}

public sealed class SupportsFile
{
    public sealed class SocketRule { public List<int> Ranks = new() { 3, 6 }; }
    public sealed class BadLuckRule { public double PerOwned = 0.5; }
    public SocketRule Sockets = new();
    public BadLuckRule BadLuck = new();
    public List<SupportDef> Gems = new();
    public sealed class DropRule { public int Level = 12; public Dictionary<string, double> Chance = new(); }
    public DropRule Drop = new();
}

/// <summary>Her gems: how many of each she owns, and what sits in each skill's sockets (index = socket).</summary>
public sealed class SupportState
{
    public Dictionary<string, int> Owned = new();
    public Dictionary<string, List<string?>> Sockets = new();
}

public static class Supports
{
    static SupportsFile? file;
    public static SupportsFile File => file ??= Json.Parse<SupportsFile>(Json.ReadContent("supports.json"));
    public static IReadOnlyList<SupportDef> All => File.Gems;
    public static SupportDef? Find(string id) => File.Gems.FirstOrDefault(g => g.Id == id);

    public const string ItemPrefix = "gem.";
    public static string ItemId(string gem) => ItemPrefix + gem;
    public static SupportDef? OfItem(string itemId) => itemId.StartsWith(ItemPrefix, StringComparison.Ordinal) ? Find(itemId[ItemPrefix.Length..]) : null;
    public static IEnumerable<ItemDef> ItemDefs() => All.Select(g => new ItemDef { Id = ItemId(g.Id), Name = g.Name, Kind = ItemKind.Gem, Rarity = 2, Description = g.Text });

    /// <summary>Open sockets at a skill's rank: one per threshold reached.</summary>
    public static int SocketsAt(int rank) => File.Sockets.Ranks.Count(r => rank >= r);

    /// <summary>Does the gem take this skill (by its tags; an empty list takes any).</summary>
    public static bool Fits(SupportDef gem, string skill)
    {
        if (gem.Fits.Count == 0) return true;
        if (!Weapons.All.TryGetValue(skill, out var w)) return false;
        return gem.Fits.Any(f => Enum.TryParse<Tag>(f, true, out var t) && w.Tags.Contains(t));
    }

    /// <summary>Bad-luck protection: each copy owned multiplies its weight by perOwned.</summary>
    public static double DropWeight(SupportDef gem, int owned) => gem.Weight * Math.Pow(File.BadLuck.PerOwned, Math.Max(0, owned));

    /// <summary>The gem a drop gives, from a roll in [0,1).</summary>
    public static SupportDef Roll(SupportState s, double roll)
    {
        var w = All.Select(g => DropWeight(g, s.Owned.GetValueOrDefault(g.Id))).ToArray();
        double t = Math.Clamp(roll, 0, 0.999999) * w.Sum();
        for (int i = 0; i < w.Length; i++) { if (t < w[i]) return All[i]; t -= w[i]; }
        return All[^1];
    }

    static int InUse(SupportState s, string gem) => s.Sockets.Values.Sum(l => l.Count(g => g == gem));

    /// <summary>Sets a gem in a skill's socket (null empties it). Refused when the socket is not open at that rank,
    /// the gem does not fit the skill, or every copy she owns is already set elsewhere.</summary>
    public static bool Socket(SupportState s, string skill, int rank, int index, string? gem)
    {
        if (index < 0 || index >= SocketsAt(rank)) return false;
        if (!s.Sockets.TryGetValue(skill, out var row)) s.Sockets[skill] = row = new();
        while (row.Count <= index) row.Add(null);
        if (gem != null)
        {
            var def = Find(gem);
            if (def == null || !Fits(def, skill)) return false;
            int free = s.Owned.GetValueOrDefault(gem) - InUse(s, gem) + (row[index] == gem ? 1 : 0);
            if (free <= 0) return false;
        }
        row[index] = gem;
        return true;
    }

    /// <summary>What a skill's open sockets add, summed by effect (a socket closed by rank adds nothing).</summary>
    public static Dictionary<string, double> EffectsFor(SupportState s, string skill, int rank)
    {
        var sum = new Dictionary<string, double>();
        if (!s.Sockets.TryGetValue(skill, out var row)) return sum;
        foreach (var id in row.Take(SocketsAt(rank)))
            if (id != null && Find(id) is { } g)
                foreach (var (k, v) in g.Effects) sum[k] = sum.GetValueOrDefault(k) + v;
        return sum;
    }
}
