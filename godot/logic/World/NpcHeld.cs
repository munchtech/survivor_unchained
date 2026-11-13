using System;
using System.Collections.Generic;
using System.Text.Json;

namespace SurvivorUnchained.World;

/// <summary>
/// What a package NPC holds of its own (a Marionette package's manifest "held" block), so a package carries its own prop
/// at its own size instead of only the game's weapon table (whose keeper_lamp is Corvane's 0.9 m lamp-iron: on a woman
/// it hung to the calf and 30 mm into the leg). The block:
///   "held": {"handslot.r": {"file": "props/hammer.glb", "carry": "hand"}, "handslot.l": {"file": "props/lamp.glb", "carry": "lamp"}}
/// SLOT is "handslot.r" or "handslot.l"; "file" is in the package (art/npc/NAME/FILE), drawn 1:1 (never rescaled), its own
/// origin and axes the grip: the origin where the fist closes, +Y along the shaft out of the fist (a hammer's head; a lamp's
/// hanging ring, the lamp below along -Y), +Z the face (a hammer's striking face; a lamp's front). "carry": "lamp" the lamp
/// carry (the arm brought up ahead of the shoulder, the fist closed, the thing hanging upright from it: NpcTorchArm), "hand"
/// (the default) the plain hand mount with the fist closed. A slot the NPC's own arms (npcs.json "arms", a shot's --held)
/// name is theirs; the manifest fills the rest.
/// </summary>
public static class NpcHeld
{
    public enum Carry { Hand, Lamp }

    public sealed record Prop(string File, Carry Carry);

    public static readonly string[] Slots = { "handslot.r", "handslot.l" };

    /// <summary>A manifest's "held" block by slot (empty when it has none; a slot that is not a hand, an entry without a
    /// file, or an unknown carry is left out, and the reason listed in `skipped`).</summary>
    public static Dictionary<string, Prop> Parse(string manifestJson, List<string>? skipped = null)
    {
        var o = new Dictionary<string, Prop>();
        using var doc = JsonDocument.Parse(manifestJson);
        if (!doc.RootElement.TryGetProperty("held", out var h) || h.ValueKind != JsonValueKind.Object) return o;
        foreach (var e in h.EnumerateObject())
        {
            if (Array.IndexOf(Slots, e.Name) < 0) { skipped?.Add($"{e.Name}: not a hand slot"); continue; }
            if (e.Value.ValueKind != JsonValueKind.Object || !e.Value.TryGetProperty("file", out var f) || f.ValueKind != JsonValueKind.String || f.GetString() is not { Length: > 0 } file)
            { skipped?.Add($"{e.Name}: no file"); continue; }
            var carry = Carry.Hand;
            if (e.Value.TryGetProperty("carry", out var c) && c.ValueKind == JsonValueKind.String)
            {
                if (ParseCarry(c.GetString()) is { } k) carry = k;
                else { skipped?.Add($"{e.Name}: carry \"{c.GetString()}\" is not lamp or hand"); continue; }
            }
            o[e.Name] = new Prop(file, carry);
        }
        return o;
    }

    public static Carry? ParseCarry(string? s) => s switch { "lamp" => Carry.Lamp, "hand" or null or "" => Carry.Hand, _ => null };

    /// <summary>How a held thing is mounted. Table: the game's weapon table (Arms.Hold, its own scale and seat). Lamp: the lamp
    /// carry, for a package's hand only (a kit body has no carry arm). Hand: a package's own prop on the plain hand mount.</summary>
    public enum Route { Table, Lamp, Hand, None }

    /// <summary>The route for a slot: a package's own prop (`own`, from its manifest) by its carry; else a table row by its
    /// Lamp flag (Arms.Spec.Lamp: a lamp carried in a package's fist; elsewhere held as any piece).</summary>
    public static Route RouteOf(bool package, string slot, Prop? own, bool inTable, bool tableLamp)
    {
        bool hand = Array.IndexOf(Slots, slot) >= 0;
        if (own != null) return package && hand ? (own.Carry == Carry.Lamp ? Route.Lamp : Route.Hand) : Route.None;
        if (!inTable) return Route.None;
        return tableLamp && package && hand ? Route.Lamp : Route.Table;
    }
}
