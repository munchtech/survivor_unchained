using System;
using System.Collections.Generic;
using System.Numerics;
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

    /// <summary>The piece's shaft (long) and side (mid) axes in model space. An anchor (anchor_grip, else anchor_sheath) says
    /// the shaft outright: its -Y runs down the blade or haft toward the tip, so `anchorDown` (that -Y) is the shaft, exactly,
    /// whatever else the mesh carries (a coil or a crossguard tilts the bounds' principal axis: 4 degrees on the bound staff).
    /// Without one, the bounds' principal axes stand. The side axis is the bounds' second axis made square to the shaft (the
    /// anchor's +Z then turns the piece about the shaft).</summary>
    public static (Vector3 Long, Vector3 Mid) ShaftAxes(Vector3 pcaLong, Vector3 pcaMid, Vector3? anchorDown)
    {
        if (anchorDown is not { } down || down.LengthSquared() < 1e-12f) return (pcaLong, pcaMid);
        var lng = Vector3.Normalize(down);
        foreach (var c in new[] { pcaMid, pcaLong, Vector3.UnitX, Vector3.UnitZ })
        {
            var m = c - lng * Vector3.Dot(c, lng);
            if (m.LengthSquared() > 1e-4f) return (lng, Vector3.Normalize(m));
        }
        return (lng, Vector3.UnitX);
    }

    /// <summary>The line her right `grip` fist closes round, in hand_r's space: the hollow of the fist the keyed clips close
    /// on a staff (tools/anim/keyed.py WRAP), its centre midway across the four fingers, and its direction, butt toward
    /// head (8.2 degrees off hand +Z: 6.6 toward the fingers, 5 toward the palm on the thumb's side, as her palm slopes).
    /// Fitted 13 October on her skin and the arcanist's glove: the palm and every finger's inner pads lie on the leather
    /// (13.65 mm round the line), the thumb over the forefinger. (The old pocket, -39, 58, 2 mm, lay at the thumb's root,
    /// 40 mm off the palm and 30-50 mm off the pads: the shaft ran beside the fist, not through it.) An anchored piece's
    /// grip point and shaft are laid on it.</summary>
    public static readonly Vector3 FistAtR = new(-0.0308f, 0.1188f, -0.0104f);
    public static readonly Vector3 FistDirR = Vector3.Normalize(new Vector3(-0.0863f, 0.1138f, 0.9898f));

    /// <summary>Where an anchored piece sits inside its mount so that its grip point (the anchor's origin, on the shaft's
    /// centreline) lands on the fist's pocket and its shaft (the piece's +Y, the anchor's -Y) runs along the fist's line:
    /// a turn (the least that takes +Y onto the line, so the anchor's +Z keeps its roll) and an offset, both in the mount's
    /// space. `mx, my, mz, origin`: the mount in the hand's space (unleaned; a Lean turns this seat with the mount).</summary>
    public static (Quaternion Turn, Vector3 At) FistSeat(Vector3 mx, Vector3 my, Vector3 mz, Vector3 origin)
    {
        Vector3 In(Vector3 v) => new(Vector3.Dot(v, mx), Vector3.Dot(v, my), Vector3.Dot(v, mz));
        var at = In(FistAtR - origin);
        var dir = Vector3.Normalize(In(FistDirR));
        var axis = Vector3.Cross(Vector3.UnitY, dir);
        float s = axis.Length(), c = Vector3.Dot(Vector3.UnitY, dir);
        var turn = s < 1e-7f ? Quaternion.Identity : Quaternion.CreateFromAxisAngle(axis / s, MathF.Atan2(s, c));
        return (turn, at);
    }

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
