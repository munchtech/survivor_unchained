using System;
using System.Text.Json;

namespace SurvivorUnchained.Cinema;

/// <summary>
/// Where a timeline's places are. A place is written as:
///   [x, h, z]                      h metres above the ground at (x, z)
///   [x, z]                         on the ground
///   {"abs": [x, y, z]}             exactly there (over water: the water's height)
///   {"mark": "fire", "off": [dx, dh, dz]}   from a mark, h above the ground where it lands
///   {"mark": "pool", "y": -0.95}   a mark at a given height
///   {"actor": "her", "bone": "head", "off": [dx, dy, dz]}   on someone, as they are now
/// An actor's place comes from the game (null in the tests: the actor's mark then).
/// </summary>
public sealed class CinePlaces
{
    readonly CineFile f;
    readonly Func<double, double, double> ground;
    readonly Func<string, string?, V3?> actor;

    public CinePlaces(CineFile f, Func<double, double, double> ground, Func<string, string?, V3?>? actor = null)
    {
        this.f = f;
        this.ground = ground;
        this.actor = actor ?? ((_, _) => null);
    }

    public V3 this[JsonElement e] => Resolve(e);

    public V3 Resolve(JsonElement e)
    {
        switch (e.ValueKind)
        {
            case JsonValueKind.Array:
            {
                int n = e.GetArrayLength();
                double x = e[0].GetDouble();
                if (n == 2) { double z2 = e[1].GetDouble(); return new V3(x, ground(x, z2), z2); }
                double h = e[1].GetDouble(), z = e[2].GetDouble();
                return new V3(x, ground(x, z) + h, z);
            }
            case JsonValueKind.Object:
            {
                if (e.TryGetProperty("abs", out var a)) return new V3(a[0].GetDouble(), a[1].GetDouble(), a[2].GetDouble());
                var off = e.TryGetProperty("off", out var o) ? new V3(o[0].GetDouble(), o[1].GetDouble(), o[2].GetDouble()) : default;
                if (e.TryGetProperty("actor", out var who))
                {
                    var name = who.GetString()!;
                    string? bone = e.TryGetProperty("bone", out var b) ? b.GetString() : null;
                    if (actor(name, bone) is V3 p) return p + off;
                    // No body to ask (the tests): where they stand, and a head's height.
                    var mk = f.Cast.TryGetValue(name, out var c) && c.Mark != null ? c.Mark : name;
                    var (ax, ah, az, _) = f.Mark(mk);
                    double headH = bone is "head" or "eyes" ? 1.6 : bone is "hand_r" or "hand_l" ? 1.0 : 0;
                    return new V3(ax + off.X, ground(ax + off.X, az + off.Z) + ah + headH + off.Y, az + off.Z);
                }
                if (e.TryGetProperty("mark", out var m))
                {
                    var (mx, mh, mz, _) = f.Mark(m.GetString()!);
                    double x = mx + off.X, z = mz + off.Z;
                    if (e.TryGetProperty("y", out var y)) return new V3(x, y.GetDouble() + off.Y, z);
                    return new V3(x, ground(x, z) + mh + off.Y, z);
                }
                throw new FormatException($"{f.Id}: a place needs abs, mark or actor: {e}");
            }
            default:
                throw new FormatException($"{f.Id}: not a place: {e}");
        }
    }
}
