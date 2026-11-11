using System;
using System.Collections.Generic;
using System.Text.Json;
using SurvivorUnchained.Sim;
using SurvivorUnchained.World;

namespace SurvivorUnchained.Ui;

/// <summary>
/// (L1 l26 mini) The zone's own ink for the minimap and the full map: what the zone data names, drawn where it stands,
/// so no explored ground reads blank where there is no road (the camp yard, dropped from the road keep as a dirt
/// lump, and the stone square, which the road mask never saw). Plain C#, built once per zone: a square RGBA8 sheet
/// over the drawing's own extent (u = x / extent + 0.5), a channel per kind of ink:
/// R = hard props (the box colliders: tents, crates, stalls, fence runs; a fire's ring of stones),
/// G = soft props (hedges, brush: the map's 0.35 wash), B = buildings (Map.Buildings, the full map's hexes),
/// A = yards: the worked ground (dirt or stone) round each named place and fire that has no road under it,
/// flooded out from the place over that ground up to <see cref="YardCap"/> m, or a <see cref="YardMin"/> m disc
/// where the place stands on grass. The full map already inks R, G and B itself (MapScreen.Ink); it takes A from here.
/// </summary>
public static class ZoneInk
{
    public const int Prop = 0, Soft = 1, Building = 2, Yard = 3;
    /// <summary>Metres: how far a place's yard floods over its worked ground.</summary>
    public const double YardCap = 12;
    /// <summary>Metres: a place on grass (no worked ground to flood): a trodden disc this wide each way.</summary>
    public const double YardMin = 3;
    /// <summary>Metres a fire's ring of stones reaches past its flame.</summary>
    public const double FireRing = 0.45;

    /// <summary>A shape in metres: a box (half widths, turned by Rot as the map turns its colliders), a hex of radius Hw
    /// (a building, turned by Rot), or a disc of radius Hw; or a yard seed (a place's point).</summary>
    public readonly record struct Shape(int Channel, double X, double Z, double Hw, double Hd, double Rot, char Form);

    /// <summary>The zone data's ink: its colliders, buildings, fires and named places.</summary>
    public static List<Shape> From(ZoneMeta m)
    {
        var s = new List<Shape>();
        foreach (var c in m.Colliders)
        {
            if (c.Kind != ColliderKind.Box || c.PlayerOnly || c.Hw * c.Hd < 0.6) continue;
            s.Add(new Shape(c.Soft ? Soft : Prop, c.X, c.Z, c.Hw, c.Hd, c.Rot, 'b'));
        }
        foreach (var b in m.Map?.Buildings ?? new())
            if (b.TryGetProperty("x", out var bx) && b.TryGetProperty("z", out var bz) && b.TryGetProperty("r", out var br))
                s.Add(new Shape(Building, bx.GetDouble(), bz.GetDouble(), br.GetDouble(), 0, b.TryGetProperty("rot", out var r) ? r.GetDouble() : 0, 'h'));
        foreach (var f in m.Fires)
        {
            if (f.Ring) s.Add(new Shape(Prop, f.X, f.Z, f.Size + FireRing, 0, 0, 'd'));
            s.Add(new Shape(Yard, f.X, f.Z, 0, 0, 0, 'y'));
        }
        foreach (var p in m.Places.Values) Points(p, s);
        return s;
    }

    static void Points(JsonElement e, List<Shape> s)
    {
        if (e.ValueKind != JsonValueKind.Object) return;
        if (e.TryGetProperty("x", out var x) && e.TryGetProperty("z", out var z) && x.ValueKind == JsonValueKind.Number && z.ValueKind == JsonValueKind.Number)
        {
            s.Add(new Shape(Yard, x.GetDouble(), z.GetDouble(), 0, 0, 0, 'y'));
            return;
        }
        foreach (var p in e.EnumerateObject()) Points(p.Value, s);
    }

    /// <summary>The sheet, n by n RGBA8 over <paramref name="extent"/> metres. <paramref name="road"/> (x, z): a kept road
    /// is there (a place on its road needs no yard, and a yard never floods over road); <paramref name="ground"/> (x, z):
    /// worked ground (dirt or stone, not grass) a yard floods over. Either may be null (none, everywhere grass).</summary>
    public static byte[] Build(IReadOnlyList<Shape> shapes, int n, double extent, Func<double, double, bool>? road, Func<double, double, bool>? ground)
    {
        var o = new byte[n * n * 4];
        double m = extent / n;
        double X(int i) => ((i + 0.5) / n - 0.5) * extent;
        int I(double x) => (int)Math.Floor((x / extent + 0.5) * n);
        var solid = new bool[n * n];
        foreach (var sh in shapes)
        {
            if (sh.Form == 'y') continue;
            double reach = sh.Form == 'b' ? Math.Sqrt(sh.Hw * sh.Hw + sh.Hd * sh.Hd) : sh.Hw;
            int i0 = Math.Max(0, I(sh.X - reach)), i1 = Math.Min(n - 1, I(sh.X + reach)), j0 = Math.Max(0, I(sh.Z - reach)), j1 = Math.Min(n - 1, I(sh.Z + reach));
            double cs = Math.Cos(sh.Rot), sn = Math.Sin(sh.Rot);
            for (int j = j0; j <= j1; j++)
                for (int i = i0; i <= i1; i++)
                {
                    double dx = X(i) - sh.X, dz = X(j) - sh.Z;
                    bool inside = sh.Form switch
                    {
                        // the map draws a box's corner (x, z) at its centre + (x, z).Rotated(-rot): back by +rot
                        'b' => Math.Abs(dx * cs - dz * sn) <= sh.Hw && Math.Abs(dx * sn + dz * cs) <= sh.Hd,
                        'h' => Hex(dx, dz, sh.Hw, sh.Rot),
                        _ => dx * dx + dz * dz <= sh.Hw * sh.Hw,
                    };
                    if (!inside) continue;
                    o[(j * n + i) * 4 + sh.Channel] = 255;
                    if (sh.Channel != Soft) solid[j * n + i] = true;
                }
        }
        // the yards: flooded from each place over worked ground, never over road or under a building or prop
        var lab = new int[n * n];
        var stack = new Stack<int>();
        int seed = 0;
        int capPx = (int)Math.Ceiling(YardCap / m);
        foreach (var sh in shapes)
        {
            if (sh.Form != 'y') continue;
            int ci = I(sh.X), cj = I(sh.Z);
            if (ci < 0 || cj < 0 || ci >= n || cj >= n) continue;
            if (road?.Invoke(sh.X, sh.Z) == true || solid[cj * n + ci]) continue;
            seed++;
            int painted = 0;
            if (ground?.Invoke(sh.X, sh.Z) == true)
            {
                lab[cj * n + ci] = seed; stack.Push(cj * n + ci);
                while (stack.Count > 0)
                {
                    int p = stack.Pop(), pi = p % n, pj = p / n;
                    o[p * 4 + Yard] = 255; painted++;
                    for (int k = 0; k < 4; k++)
                    {
                        int qi = pi + (k == 0 ? 1 : k == 1 ? -1 : 0), qj = pj + (k == 2 ? 1 : k == 3 ? -1 : 0);
                        if (qi < 0 || qj < 0 || qi >= n || qj >= n) continue;
                        int q = qj * n + qi;
                        if (lab[q] == seed || (qi - ci) * (qi - ci) + (qj - cj) * (qj - cj) > capPx * capPx) continue;
                        lab[q] = seed;
                        double qx = X(qi), qz = X(qj);
                        if (solid[q] || !ground(qx, qz) || road?.Invoke(qx, qz) == true) continue;
                        stack.Push(q);
                    }
                }
            }
            if (painted * m * m >= Math.PI * YardMin * YardMin) continue;
            int rp = (int)Math.Ceiling(YardMin / m);
            for (int j = Math.Max(0, cj - rp); j <= Math.Min(n - 1, cj + rp); j++)
                for (int i = Math.Max(0, ci - rp); i <= Math.Min(n - 1, ci + rp); i++)
                {
                    double dx = X(i) - sh.X, dz = X(j) - sh.Z;
                    if (dx * dx + dz * dz <= YardMin * YardMin && !solid[j * n + i] && road?.Invoke(X(i), X(j)) != true) o[(j * n + i) * 4 + Yard] = 255;
                }
        }
        return o;
    }

    /// <summary>Inside the map's building hex: corners at rot + 30 deg + k 60 deg, so its edges face rot + k 60 deg.</summary>
    static bool Hex(double dx, double dz, double r, double rot)
    {
        double ap = r * 0.8660254;
        for (int k = 0; k < 3; k++)
        {
            double a = rot + k * Math.PI / 3;
            if (Math.Abs(dx * Math.Cos(a) + dz * Math.Sin(a)) > ap) return false;
        }
        return true;
    }
}
