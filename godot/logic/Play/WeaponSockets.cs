using System;
using System.Collections.Generic;
using System.Text.Json;

namespace SurvivorUnchained.Play;

/// <summary>What sort of weapon a piece is: the socket it rides in when sheathed follows from the kind, never from the item,
/// so a new asset needs only its kind (Arms.Spec) and no socket code.</summary>
public enum WeaponKind { None, Blade1H, Blade2H, Blunt, Axe, Axe2H, Dagger, Wand, Staff, Shield, Crossbow }

/// <summary>The kind tables and the clearance file, without the engine (Actors/Arms.cs holds the geometry).</summary>
public static class WeaponSockets
{
    /// <summary>The named sockets (rows of Arms.Sockets, and the keys of the clearance file).</summary>
    public const string Back = "back", HipBlade = "hip_blade", HipLoop = "hip_loop", HipBelt = "hip_belt",
        BeltBack = "belt_back", Sling = "sling", BackDiag = "back_diag";
    public static readonly string[] All = { Back, HipBlade, HipLoop, HipBelt, BeltBack, Sling, BackDiag };

    /// <summary>The socket a kind rides in sheathed; null if it stays in her hand (a staff is a walking staff).</summary>
    public static string? SocketOf(WeaponKind kind) => kind switch
    {
        WeaponKind.Shield => Back,
        WeaponKind.Blade1H => HipBlade,
        WeaponKind.Blunt or WeaponKind.Axe => HipLoop,
        WeaponKind.Wand => HipBelt,
        WeaponKind.Dagger => BeltBack,
        WeaponKind.Crossbow => Sling,
        WeaponKind.Blade2H or WeaponKind.Axe2H => BackDiag,
        _ => null,
    };

    /// <summary>A kind from a tag: the glTF node extra "kind", or a name suffix ("longsword.blade1h", "kind=axe2h", "_staff");
    /// anything unknown is None.</summary>
    public static WeaponKind Parse(string? tag)
    {
        if (string.IsNullOrWhiteSpace(tag)) return WeaponKind.None;
        var t = tag.Trim().ToLowerInvariant();
        foreach (var sep in new[] { '=', '.', '_', ':', '-' })
        {
            int i = t.LastIndexOf(sep);
            if (i >= 0 && Enum.TryParse<WeaponKind>(t[(i + 1)..], true, out var k) && Enum.IsDefined(k) && k != WeaponKind.None) return k;
        }
        return Enum.TryParse<WeaponKind>(t, true, out var whole) && Enum.IsDefined(whole) ? whole : WeaponKind.None;
    }

    /// <summary>Length of a scabbard: from `guard` past the sheath point to the blade's tip, along the shaft. Tip and sheath
    /// point are on the piece's long axis (tip at Length * (1 - Grip) and the sheath point at the grip, 0, when no anchors say
    /// otherwise), so a longer blade gives a longer scabbard. Never under 5 cm.</summary>
    public static float BladeLength(float tipY, float sheathY, float guard) => Math.Max(0.05f, tipY - sheathY - guard);

    /// <summary>Metres to push a socket out of her body along its normal for an outfit: art/anim/socket_clearance.json, written by
    /// `armscheck.py --sockets` as {outfit: {socket: metres}}. Unknown outfit or socket: 0.</summary>
    public sealed class Clearance
    {
        readonly Dictionary<string, Dictionary<string, float>> table = new();

        public static Clearance Parse(string? json)
        {
            var c = new Clearance();
            if (string.IsNullOrWhiteSpace(json)) return c;
            try
            {
                using var doc = JsonDocument.Parse(json);
                if (doc.RootElement.ValueKind != JsonValueKind.Object) return c;
                foreach (var o in doc.RootElement.EnumerateObject())
                {
                    if (o.Value.ValueKind != JsonValueKind.Object) continue;
                    var row = new Dictionary<string, float>();
                    foreach (var s in o.Value.EnumerateObject())
                        if (s.Value.ValueKind == JsonValueKind.Number) row[s.Name] = (float)s.Value.GetDouble();
                    c.table[o.Name] = row;
                }
            }
            catch (JsonException) { }
            return c;
        }

        /// <summary>The outfit's name as the file has it: a calling ("stalker" is the ranger's), "" is none.</summary>
        public static string Outfit(string? calling) => string.IsNullOrEmpty(calling) ? "none" : calling == "stalker" ? "ranger" : calling;

        public float Metres(string? calling, string socket) =>
            table.TryGetValue(Outfit(calling), out var row) && row.TryGetValue(socket, out var m) ? m : 0f;
    }
}
