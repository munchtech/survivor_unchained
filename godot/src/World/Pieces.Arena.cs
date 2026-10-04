using System;
using System.Collections.Generic;
using Godot;
using static SurvivorUnchained.View.Made;
using static SurvivorUnchained.View.Shapes;

namespace SurvivorUnchained.View;

/// <summary>
/// The ember arenas' own pieces (Maps/Arenas/*.cs sets them down as
/// "arena/NAME"), made in code to their own size: the Dig's headframe over
/// its pit and the tubs on its rails.
/// </summary>
public static partial class Pieces
{
    static Node3D? Arena(string name, int seed, Func<Vector3, float>? ground)
    {
        Node3D? made = name switch
        {
            "headframe" => Headframe(ground),
            "tub" => Tub(seed),
            _ => null,
        };
        if (made != null) made.Name = "arena_" + name;
        return made;
    }

    /// <summary>A squared timber from a to c, w across (h deep, if given).</summary>
    static void Beam(Build b, Vector3 a, Vector3 c, float w, float h = 0)
    {
        var d = c - a;
        float len = d.Length();
        var z = d / len;
        var x = Mathf.Abs(z.Y) > 0.95f ? Vector3.Right : Vector3.Up.Cross(z).Normalized();
        var y = z.Cross(x);
        float hh = h > 0 ? h : w;
        Extrude(b, Pts(-w / 2, -hh / 2, w / 2, -hh / 2, w / 2, hh / 2, -w / 2, hh / 2), len, w * 0.08f, new Transform3D(new Basis(x, y, z), (a + c) / 2));
    }

    /// <summary>The Dig's headframe: a timber tower standing on the pit's lip
    /// over its throat, raked in to a platform eleven metres up, braced, its
    /// two winding wheels on top and their ropes running down into the glow.
    /// Its origin is the pit's middle on its floor; its feet find the lip
    /// (the ground probe). From thirty metres up it is the Dig's one tall
    /// thing, black against what burns below it.</summary>
    static Node3D Headframe(Func<Vector3, float>? ground)
    {
        float G(float x, float z) => ground?.Invoke(new Vector3(x, 0, z)) ?? 8f;
        var wood = new Build();
        var iron = new Build();
        float lip = Mathf.Max(G(0, 7.9f), Mathf.Max(G(0, -7.9f), Mathf.Max(G(7.9f, 0), G(-7.9f, 0))));
        float top = lip + 11f;
        var feet = new[] { new Vector3(-5.6f, 0, -5.6f), new Vector3(5.6f, 0, -5.6f), new Vector3(5.6f, 0, 5.6f), new Vector3(-5.6f, 0, 5.6f) };
        for (int k = 0; k < 4; k++) feet[k].Y = G(feet[k].X, feet[k].Z) - 0.3f;
        var heads = new Vector3[4];
        for (int k = 0; k < 4; k++) heads[k] = new Vector3(Mathf.Sign(feet[k].X) * 1.7f, top, Mathf.Sign(feet[k].Z) * 1.7f);
        // The four legs, raked in; girts round them twice; a cross on each face.
        for (int k = 0; k < 4; k++) Beam(wood, feet[k], heads[k], 0.42f);
        foreach (float t in new[] { 0.36f, 0.7f })
            for (int k = 0; k < 4; k++)
                Beam(wood, feet[k].Lerp(heads[k], t), feet[(k + 1) % 4].Lerp(heads[(k + 1) % 4], t), 0.26f);
        for (int k = 0; k < 4; k++)
        {
            int j = (k + 1) % 4;
            Beam(wood, feet[k].Lerp(heads[k], 0.36f), feet[j].Lerp(heads[j], 0.7f), 0.2f);
            Beam(wood, feet[j].Lerp(heads[j], 0.36f), feet[k].Lerp(heads[k], 0.7f), 0.2f);
        }
        // The platform: a frame of heavy timbers, planked.
        for (int k = 0; k < 4; k++) Beam(wood, heads[k] + Vector3.Up * 0.2f, heads[(k + 1) % 4] + Vector3.Up * 0.2f, 0.4f);
        for (float x = -1.5f; x <= 1.51f; x += 0.38f)
            Beam(wood, new Vector3(x, top + 0.45f, -1.9f), new Vector3(x, top + 0.45f, 1.9f), 0.32f, 0.08f);
        // The back-stays, out across the lip behind it, away from the working.
        foreach (float sx in new[] { -1f, 1f })
        {
            var foot = new Vector3(sx * 2.5f, 0, -13f);
            foot.Y = G(foot.X, foot.Z) - 0.3f;
            Beam(wood, foot, new Vector3(sx * 1.7f, top - 0.6f, -1.7f), 0.36f);
        }
        // The winding wheels on their bearers, the ropes down into the pit.
        foreach (float wz in new[] { -0.75f, 0.75f })
        {
            var c = new Vector3(0, top + 1.9f, wz);
            const float r = 1.35f;
            // The wheel stands in the XY plane, its axle along Z.
            Tube(iron, Path(32, a => c + new Vector3(r * Mathf.Cos(a * Mathf.Tau), r * Mathf.Sin(a * Mathf.Tau), 0), true), 0.07f, 6, true);
            for (int k = 0; k < 8; k++)
            {
                float a = k * Mathf.Pi / 4;
                Tube(iron, new List<Vector3> { c, c + new Vector3(Mathf.Cos(a), Mathf.Sin(a), 0) * r }, 0.035f, 4);
            }
            Tube(iron, new List<Vector3> { c + new Vector3(0, 0, -0.35f), c + new Vector3(0, 0, 0.35f) }, 0.09f, 6);
            foreach (float sz in new[] { -0.3f, 0.3f })
                Beam(wood, new Vector3(0, top + 0.5f, wz + sz), new Vector3(0, c.Y + 0.1f, wz + sz), 0.22f);
            // The rope off the wheel's lip, down the throat to the cage at the bottom.
            Tube(iron, new List<Vector3> { c + new Vector3(r, 0, 0), new Vector3(r, 1.6f, wz) }, 0.03f, 4);
        }
        // The cage the ropes hold, sat on the floor in the glow.
        var cage = new Vector3(1.35f, 0.9f, 0);
        foreach (float sx in new[] { -0.7f, 0.7f })
            foreach (float sz in new[] { -0.9f, 0.9f })
                Beam(iron, cage + new Vector3(sx, -0.9f, sz), cage + new Vector3(sx, 0.9f, sz), 0.08f);
        Beam(wood, cage + new Vector3(0, 0.9f, -0.95f), cage + new Vector3(0, 0.9f, 0.95f), 1.5f, 0.1f);
        return Hold((wood.Mesh(true), Surface("rough_wood", 1.4f, "#6e5e50")), (iron.Mesh(), Wrought()));
    }

    /// <summary>A mine tub: an iron box tapering to its floor, rusted, banded,
    /// on four small wheels at the rails' gauge, heaped with black spoil.
    /// Its length runs along +Z.</summary>
    static Node3D Tub(int seed)
    {
        var body = new Build();
        var iron = new Build();
        var spoil = new Build();
        const float L = 1.7f, W = 1.2f, H = 0.8f, y0 = 0.3f;
        // The box: four sides leaning out, a floor.
        var bot = new[] { new Vector3(-W * 0.4f, y0, -L * 0.42f), new Vector3(W * 0.4f, y0, -L * 0.42f), new Vector3(W * 0.4f, y0, L * 0.42f), new Vector3(-W * 0.4f, y0, L * 0.42f) };
        var topc = new[] { new Vector3(-W / 2, y0 + H, -L / 2), new Vector3(W / 2, y0 + H, -L / 2), new Vector3(W / 2, y0 + H, L / 2), new Vector3(-W / 2, y0 + H, L / 2) };
        for (int k = 0; k < 4; k++)
        {
            int j = (k + 1) % 4;
            var n = (bot[j] - bot[k]).Cross(topc[k] - bot[k]).Normalized();
            if (n.Dot((bot[k] + bot[j]) / 2 - new Vector3(0, y0, 0)) < 0) n = -n;
            body.Quad(body.V(bot[k], n), body.V(bot[j], n), body.V(topc[j], n), body.V(topc[k], n));
            body.Quad(body.V(topc[k], -n), body.V(topc[j], -n), body.V(bot[j], -n), body.V(bot[k], -n));
            // A band round the rim, another low.
            Beam(iron, topc[k], topc[j], 0.06f);
            Beam(iron, bot[k].Lerp(topc[k], 0.35f) + (topc[k] - bot[k]).Normalized() * 0.01f, bot[j].Lerp(topc[j], 0.35f), 0.05f);
        }
        body.Quad(body.V(bot[3], Vector3.Up), body.V(bot[2], Vector3.Up), body.V(bot[1], Vector3.Up), body.V(bot[0], Vector3.Up));
        // Spoil heaped in it, a lump over the rim.
        float hump = 0.15f + 0.15f * Hash(seed, 3);
        Lathe(spoil, Pts(0.55f, 0, 0.5f, hump * 0.6f, 0.3f, hump, 0, hump * 1.2f), 10,
            new Transform3D(Basis.Identity.Scaled(new Vector3(0.95f, 1, 1.3f)), new Vector3(0, y0 + H - 0.12f, 0)),
            warp: p => p + new Vector3(0, (Noise(p.X * 6 + seed, p.Z * 6) - 0.5f) * 0.12f, 0));
        // The wheels and axles, at the rails' gauge.
        foreach (float wz in new[] { -L * 0.3f, L * 0.3f })
        {
            Tube(iron, new List<Vector3> { new(-0.62f, 0.18f, wz), new(0.62f, 0.18f, wz) }, 0.04f, 6);
            foreach (float sx in new[] { -0.55f, 0.55f })
                Tube(iron, Path(16, a => new Vector3(sx, 0.18f + 0.17f * Mathf.Sin(a * Mathf.Tau), wz + 0.17f * Mathf.Cos(a * Mathf.Tau)), true), 0.045f, 5, true);
        }
        return Hold((body.Mesh(), Mat("#4c2f20", 0.45f, 0.72f)), (iron.Mesh(), Wrought()), (spoil.Mesh(), Mat("#141210", 0, 0.95f)));
    }
}
