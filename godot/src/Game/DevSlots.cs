using System;
using System.Collections.Generic;
using System.Linq;
using Godot;
using SurvivorUnchained.Sim;

namespace SurvivorUnchained.Play;

/// <summary>
/// M4 (docs/design/M4_HUD.md §1, the judge's build): --slots "sunder:hold,cleaver:channel,heroic_leap:press,..." puts
/// those skills on the slots in that order (slot 1 = LMB, 2 = RMB, 3-6 = the keys 1-4) in the form each names, through
/// the sim's public API (RemoveWeapon, AddWeapon, SetForm), once in each campaign fight. With --grant-union U it then
/// makes the union from its carried parts (Battle.GrantUnion: Bladestorm takes the Cleaver's key and the Sunder's), so
/// the union sits on the keys --slots gave its parts whichever of the two runs first. GameHud.Frame ticks it.
/// </summary>
public static class DevSlots
{
    static readonly string? Spec = Args.Get("slots");
    static Battle? done;

    public static void Tick(Battle b)
    {
        if (Spec == null || ReferenceEquals(done, b) || !b.Combat || !b.Campaign) return;
        done = b;
        foreach (var line in Apply(b, Spec, Args.Get("grant-union"))) GD.Print(line);
    }

    /// <summary>What it did, a line each, for the log.</summary>
    public static List<string> Apply(Battle b, string spec, string? union)
    {
        var said = new List<string>();
        var ranks = b.Weapons.ToDictionary(w => w.Id, w => w.Rank);
        int top = ranks.Count > 0 ? ranks.Values.Max() : 1;
        foreach (var id in b.Weapons.Select(w => w.Id).ToList()) b.RemoveWeapon(id);
        foreach (var raw in spec.Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries))
        {
            var parts = raw.Split(':');
            string id = parts[0], cast = parts.Length > 1 ? parts[1] : "";
            var w = b.AddWeapon(id, Math.Min(Content.Weapons.MaxRank, ranks.TryGetValue(id, out var r) ? r : top));
            if (w == null) { said.Add($"slots: {id} not added (unknown, or no slot free)"); continue; }
            bool formed = cast == "" || b.SetForm(id, cast);
            said.Add($"slots: {id} on slot {w.Slot + 1}{(cast == "" ? "" : formed ? $" as {cast}" : $" ({cast} refused by its record)")}");
        }
        if (!string.IsNullOrWhiteSpace(union))
        {
            var u = b.GrantUnion(union.Trim());
            said.Add(u != null ? $"slots: union {union} on slots {u.Slot + 1} and {u.Slot2 + 1}" : $"slots: union {union} not made");
        }
        return said;
    }
}
