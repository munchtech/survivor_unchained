using System;
using System.Collections.Generic;
using System.Linq;

namespace SurvivorUnchained.Sim;

/// <summary>Debug grants for testing the pressed skills, unions and the dash's steps (src/Game/Game.cs reads them
/// from the command line at the fight's start; the game has no dev console):
///   --grant id[,id:rank[:wait]...]   those skills in, at rank 1 or the rank given (one carried is ranked up to it), a
///                             wait before it may fire if given (a kindled skill held off the title card, for a clip);
///   --grant-union unionId     the union in at full rank holding two slots (its parts go if carried; no evolutions asked);
///   --dash-step id[,id...]    those dash steps taken for the fight (Content/DashSteps.cs).
/// A grant the keys cannot hold takes the last key that is not the grip's nor the union's part (MakeRoom: a campaign
/// survivor's taught build fills all six keys before a grant is asked).
/// Returns what it did, a line each, for the log.</summary>
public static class DevGrants
{
    /// <param name="makeRoom">Off: a caller that made the room itself (the harness's MapSim, with its own grip).</param>
    public static List<string> Apply(Battle b, string? grant, string? union, string? steps, bool makeRoom = true)
    {
        var said = new List<string>();
        if (makeRoom) said.AddRange(MakeRoom(b, grant, union));
        if (!string.IsNullOrWhiteSpace(grant))
            foreach (var raw in grant.Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries))
            {
                var parts = raw.Split(':');
                int rank = parts.Length > 1 && int.TryParse(parts[1], out var r) ? Math.Clamp(r, 1, Content.Weapons.MaxRank) : 1;
                string id = parts[0];
                if (b.Weapons.Find(w => w.Id == id) is { } held) { held.Rank = Math.Max(held.Rank, rank); said.Add($"grant: {id} ranked to {held.Rank}"); continue; }
                var w = b.AddWeapon(id, rank);
                if (w != null && parts.Length > 2 && double.TryParse(parts[2], System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out var wait)) w.Timer = wait;
                // (what happened, said as it is: a union holds two keys; an unknown id is not "no slot free")
                said.Add(w != null ? $"grant: {id} rank {rank} on slot {w.Slot + 1}{(w.Slot2 >= 0 ? $" and {w.Slot2 + 1}" : "")}"
                    : !Content.Weapons.All.ContainsKey(id) ? $"grant: {id} not added (no such skill)"
                    : $"grant: {id} not added (needs {Content.Weapons.SlotCost(id)} of the keys, {b.KeyCount - b.SlotsUsed} free: {b.SlotsUsed}/{b.KeyCount} held)");
            }
        if (!string.IsNullOrWhiteSpace(union))
        {
            var u = Content.Unions.Find(union.Trim());
            var had = u == null ? null : b.Weapons.Find(x => x.Id == u.Into);
            var w = b.GrantUnion(union.Trim());
            said.Add(w != null ? $"grant-union: {union} on slots {w.Slot + 1} and {w.Slot2 + 1}"
                : u == null ? $"grant-union: {union} not added (no such union)"
                : had != null ? $"grant-union: {union} already carried on slots {had.Slot + 1} and {had.Slot2 + 1}"
                : $"grant-union: {union} not added (no two keys free once its parts give theirs: {b.SlotsUsed}/{b.KeyCount} held)");
        }
        if (!string.IsNullOrWhiteSpace(steps))
            foreach (var id in steps.Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries))
                said.Add(b.GrantDashStep(id) ? $"dash-step: {id}" : $"dash-step: {id} not taken (unknown, or taken as often as it may be)");
        return said;
    }

    /// <summary>Room for what is asked: while the granted skills and the union (less its parts carried, whose keys it
    /// takes) need more keys than are free, the last skill carried that is not kept gives up its key. Kept: what is
    /// granted, the union's parts, and the grip.</summary>
    /// <param name="grips">The grip's skill ids; null: the held swings (a hold record) and what is on the first key.</param>
    public static List<string> MakeRoom(Battle b, string? grant, string? union, IEnumerable<string>? grips = null)
    {
        var keep = new HashSet<string>();
        if (grips != null) foreach (var id in grips) keep.Add(id);
        else foreach (var w in b.Weapons) if (w.Hold || w.Slot == 0) keep.Add(w.Id);
        int need = 0;
        foreach (var raw in (grant ?? "").Split(',', StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries))
        {
            string id = raw.Split(':')[0];
            keep.Add(id);
            if (Content.Weapons.All.ContainsKey(id) && !b.Weapons.Exists(w => w.Id == id)) need += Content.Weapons.SlotCost(id);
        }
        if (union is { Length: > 0 } un && Content.Unions.Find(un.Trim()) is { } u && !b.Weapons.Exists(w => w.Id == u.Into))
        {
            keep.Add(u.A); keep.Add(u.B);
            need += Content.Weapons.SlotCost(u.Into) - b.Weapons.Count(w => w.Id == u.A || w.Id == u.B);
        }
        var said = new List<string>();
        while (need > 0 && b.SlotsUsed + need > b.KeyCount && b.Weapons.LastOrDefault(w => w.Slot < b.KeyCount && !keep.Contains(w.Id)) is { } give)
        {
            b.RemoveWeapon(give.Id);
            said.Add($"grant: {give.Id} gives up its key");
        }
        return said;
    }
}
