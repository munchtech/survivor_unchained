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

/// <summary>Degrees her left arm turns out from her side (Out, about her forward axis), forward (Fwd), at the elbow (Elbow) and at the wrist (Wrist).</summary>
public sealed class ArmCarry
{
    public double Out, Fwd, Elbow, Wrist;
}

public sealed class StanceDef
{
    public string Id = "", Name = "", Weapon = "", Flavor = "";
    /// <summary>(bd-wire) The weapon kinds (an item's icon) that pick this stance when worn as her second set.</summary>
    public List<string> Kinds = new();
    public List<StanceMod> Mods = new();
    public StanceBlow Blow = new();
    public SwapStrike Strike = new();
    /// <summary>(view only) What her off-hand shows in this stance, by slot ("forearm.l", "handslot.l"): an Arms piece id, "" for
    /// empty; a slot left out is as her loadout has it.</summary>
    [System.Text.Json.Serialization.JsonPropertyName("held")]
    public Dictionary<string, JsonElement> HeldRaw = new();

    /// <summary>"held" as piece ids by slot (its string entries; "carry_l" is the one object entry).</summary>
    [System.Text.Json.Serialization.JsonIgnore]
    public Dictionary<string, string> Held => held ??= HeldRaw.Where(kv => kv.Value.ValueKind == JsonValueKind.String).ToDictionary(kv => kv.Key, kv => kv.Value.GetString() ?? "");
    Dictionary<string, string>? held;

    /// <summary>(view only) How her left arm carries the off-hand piece out from her side in this stance ("held"."carry_l"), degrees; null: no carry.</summary>
    [System.Text.Json.Serialization.JsonIgnore]
    public ArmCarry? CarryL
    {
        get
        {
            if (carry != null || !HeldRaw.TryGetValue("carry_l", out var e) || e.ValueKind != JsonValueKind.Object) return carry;
            double N(string k) => e.TryGetProperty(k, out var v) && v.ValueKind == JsonValueKind.Number ? v.GetDouble() : 0;
            return carry = new ArmCarry { Out = N("out"), Fwd = N("fwd"), Elbow = N("elbow"), Wrist = N("wrist") };
        }
    }
    ArmCarry? carry;

    /// <summary>(view only) A turn of the off-hand piece in its mount about the grip point, degrees about the mount's X, Y and Z
    /// ("held"."grip_l": {x, y, z}, applied in that order of X then Y then Z); null: the plain seat. Twin Fangs' reverse grip.</summary>
    [System.Text.Json.Serialization.JsonIgnore]
    public double[]? GripL
    {
        get
        {
            if (grip != null || !HeldRaw.TryGetValue("grip_l", out var e) || e.ValueKind != JsonValueKind.Object) return grip;
            double N(string k) => e.TryGetProperty(k, out var v) && v.ValueKind == JsonValueKind.Number ? v.GetDouble() : 0;
            return grip = new[] { N("x"), N("y"), N("z") };
        }
    }
    double[]? grip;

    /// <summary>The piece shown in `slot` in this stance (null: empty); `loadoutPiece` is what her loadout has there, kept when the stance names none.</summary>
    public string? Piece(string slot, string? loadoutPiece) =>
        Held.TryGetValue(slot, out var id) ? (id == "" ? null : id) : loadoutPiece;

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

    /// <summary>The piece in `slot` of her off-hand with `stance` taken up (set A or no stance: the loadout's own).</summary>
    public static string? Piece(StanceDef? stance, string slot, string? loadoutPiece) => stance == null ? loadoutPiece : stance.Piece(slot, loadoutPiece);

    public static StanceDef? Find(string? id) => id == null ? null : File.Stances.FirstOrDefault(s => s.Id == id);

    /// <summary>(bd-wire) The stance a weapon of this kind picks (an item's icon: shield, sword, mace...), or null.</summary>
    public static string? ForKind(string? kind) =>
        string.IsNullOrEmpty(kind) ? null : File.Stances.FirstOrDefault(s => s.Kinds.Contains(kind))?.Id;

    /// <summary>Set A's swap strike (her calling weapon's), or null when the calling has none.</summary>
    public static SwapStrike? SetA(string? calling) => calling != null && File.Sets.TryGetValue(calling, out var s) ? s.Strike : null;
}
