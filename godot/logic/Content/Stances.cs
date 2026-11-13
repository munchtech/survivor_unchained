using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using SurvivorUnchained.Core;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Content;

/* (bd-keys) The second weapon set as a stance (data/content/stances.json; BUILD_DIRECTION.md round 8). Same four keys:
 * the stance weapon flavors their blows and never turns one off; each stance has a price. One swap strike a set. */
public sealed class StanceMod
{
    public string Stat = "";
    public ModKind Kind;
    public double Value;
}

public sealed class StanceStatus
{
    public StatusKind Kind;
    public double Chance = 1, Power, Duration;
    public bool Stack;
    public StatusPayload Payload => new(Kind, Chance, Power, Duration, Stack);
}

/// <summary>What her key skills' landed blows carry in a stance: every Nth one stuns a creature (seconds) and staggers a
/// ruler; each bleeds; each brings her Warding light back sooner (seconds off its recharge).</summary>
public sealed class StanceBlow
{
    public int Every = 1;
    public double Stun, Stagger, Ward;
    public StanceStatus? Bleed;
}

/// <summary>A swap strike: around her as she takes up the set, on its own internal cooldown.</summary>
public sealed class SwapStrike
{
    public string Name = "";
    public double Radius = 3, Damage, Cooldown = 6, Knockback, Stun, Stagger;
    public StanceStatus? Bleed;
}

public sealed class StanceDef
{
    public string Id = "", Name = "", Weapon = "", Flavor = "";
    /// <summary>(bd-wire) The weapon kinds (an item's icon) that pick this stance when worn as her second set.</summary>
    public List<string> Kinds = new();
    public List<StanceMod> Mods = new();
    public StanceBlow Blow = new();
    public SwapStrike Strike = new();

    /// <summary>Its mods as the stat block takes them, credited to the stance.</summary>
    public IEnumerable<StatMod> StatMods => Mods.Select(m => new StatMod(m.Stat, m.Kind, m.Value, $"stance:{Id}"));
}

public sealed class CallingSet
{
    public SwapStrike Strike = new();
}

public sealed class StancesFile
{
    public Dictionary<string, CallingSet> Sets = new();
    public List<StanceDef> Stances = new();
}

public static class Stances
{
    static StancesFile? file;
    public static StancesFile File => file ??= JsonSerializer.Deserialize<StancesFile>(Json.ReadContent("stances.json"), Json.Options)!;

    public static IReadOnlyList<StanceDef> All => File.Stances;

    public static StanceDef? Find(string? id) => id == null ? null : File.Stances.FirstOrDefault(s => s.Id == id);

    /// <summary>(bd-wire) The stance a weapon of this kind picks (an item's icon: shield, sword, mace...), or null.</summary>
    public static string? ForKind(string? kind) =>
        string.IsNullOrEmpty(kind) ? null : File.Stances.FirstOrDefault(s => s.Kinds.Contains(kind))?.Id;

    /// <summary>Set A's swap strike (her calling weapon's), or null when the calling has none.</summary>
    public static SwapStrike? SetA(string? calling) => calling != null && File.Sets.TryGetValue(calling, out var s) ? s.Strike : null;
}
