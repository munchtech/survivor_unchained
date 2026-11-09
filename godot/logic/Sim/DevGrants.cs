using System;
using System.Collections.Generic;

namespace SurvivorUnchained.Sim;

/// <summary>Debug grants for testing the pressed skills, unions and the dash's steps (src/Game/Game.cs reads them
/// from the command line at the fight's start; the game has no dev console):
///   --grant id[,id:rank[:wait]...]   those skills in, at rank 1 or the rank given (one carried is ranked up to it), a
///                             wait before it may fire if given (a kindled skill held off the title card, for a clip);
///   --grant-union unionId     the union in at full rank holding two slots (its parts go if carried; no evolutions asked);
///   --dash-step id[,id...]    those dash steps taken for the fight (Content/DashSteps.cs).
/// Returns what it did, a line each, for the log.</summary>
public static class DevGrants
{
    public static List<string> Apply(Battle b, string? grant, string? union, string? steps)
    {
        var said = new List<string>();
        if (!string.IsNullOrWhiteSpace(grant))
            foreach (var raw in grant.Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries))
            {
                var parts = raw.Split(':');
                int rank = parts.Length > 1 && int.TryParse(parts[1], out var r) ? Math.Clamp(r, 1, Content.Weapons.MaxRank) : 1;
                string id = parts[0];
                if (b.Weapons.Find(w => w.Id == id) is { } held) { held.Rank = Math.Max(held.Rank, rank); said.Add($"grant: {id} ranked to {held.Rank}"); continue; }
                var w = b.AddWeapon(id, rank);
                if (w != null && parts.Length > 2 && double.TryParse(parts[2], System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out var wait)) w.Timer = wait;
                said.Add(w != null ? $"grant: {id} rank {rank} on slot {w.Slot + 1}" : $"grant: {id} not added (unknown, or no slot free: {b.SlotsUsed}/{Content.Weapons.MaxWeapons})");
            }
        if (!string.IsNullOrWhiteSpace(union))
        {
            var w = b.GrantUnion(union.Trim());
            said.Add(w != null ? $"grant-union: {union} on slots {w.Slot + 1} and {w.Slot2 + 1}" : $"grant-union: {union} not added (unknown, carried, or no two slots free)");
        }
        if (!string.IsNullOrWhiteSpace(steps))
            foreach (var id in steps.Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries))
                said.Add(b.GrantDashStep(id) ? $"dash-step: {id}" : $"dash-step: {id} not taken (unknown, or taken as often as it may be)");
        return said;
    }
}
