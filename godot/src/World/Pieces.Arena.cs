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
            "rootplate" => RootPlate(ground),
            "reeds" => Reeds(seed),
            "deadfall" => Deadfall(seed),
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

    /// <summary>The Hollow's den: a giant oak come down in a storm long ago, its root plate torn up
    /// and standing on end over the pit it tore, the den under it. The plate is a great disc of
    /// earth seven metres across, its roots radiating over its face and broken off round its rim,
    /// fine roots hanging down over the hole like a curtain, stones held in it; the trunk lies
    /// back into the wood behind. Origin: the pit's middle, on its floor; +Z, toward the fight.
    /// From the arena camera it is the Hollow's one great shape, at the den floor's far edge.</summary>
    static Node3D RootPlate(Func<Vector3, float>? ground)
    {
        float G(float x, float z) => ground?.Invoke(new Vector3(x, 0, z)) ?? 0;
        var earth = new Build();
        var roots = new Build();
        var fine = new Build();
        var bark = new Build();
        var stone = new Build();
        // The plate: standing on its edge behind the pit, leaning back a little, its rim torn.
        const float R = 3.5f;
        var c = new Vector3(0, 3.5f, -0.6f);
        var tilt = new Basis(Vector3.Right, -0.2f);
        var face = tilt * Vector3.Back;
        Lathe(earth, Pts(0, -0.55f, R * 0.7f, -0.5f, R, -0.2f, R * 0.96f, 0.15f, R * 0.6f, 0.4f, 0, 0.45f), 40,
            new Transform3D(tilt * new Basis(Vector3.Right, Mathf.Pi / 2), c),
            warp: p =>
            {
                var q = p - c;
                float a = Mathf.Atan2(q.Y, q.X);
                float rim = 1 + 0.16f * (Noise(Mathf.Cos(a) * 2.2f + 5, Mathf.Sin(a) * 2.2f) - 0.5f) * 2 + 0.07f * (Noise(Mathf.Cos(a) * 7, Mathf.Sin(a) * 7 + 3) - 0.5f) * 2;
                var along = face * face.Dot(q);
                var flat = q - along;
                return c + along * (1 + 0.3f * (Noise(q.X * 1.3f, q.Y * 1.3f) - 0.5f)) + flat * rim;
            });
        // The roots: from the plate's middle out over its face, curving forward and down, broken
        // off past the rim; the great ones thick as a thigh.
        var rng = new RandomNumberGenerator { Seed = 71 };
        for (int k = 0; k < 30; k++)
        {
            float a = k / 30f * Mathf.Tau + rng.Randf() * 0.2f;
            bool great = k % 3 == 0;
            float reach = R * (great ? 1.25f : 0.9f + 0.4f * rng.Randf());
            float r0 = great ? 0.32f : 0.1f + 0.08f * rng.Randf();
            var dir = tilt * new Vector3(Mathf.Cos(a), Mathf.Sin(a), 0);
            var path = Path(10, t =>
            {
                var p = c + face * (0.5f + 0.4f * Mathf.Sin(t * Mathf.Pi)) + dir * reach * t;
                // Hanging down past the rim under their weight, the lower ones toward the pit.
                p.Y -= 0.9f * t * t * t * (1 + Mathf.Max(0, -dir.Y));
                return p + new Vector3(Noise(t * 3 + k, 1) - 0.5f, Noise(t * 3 + k, 7) - 0.5f, 0) * 0.35f;
            });
            Tube(roots, path, t => r0 * (1 - 0.8f * t), 6);
        }
        // Fine roots hanging off the plate's lower half over the hole, a ragged curtain.
        for (int k = 0; k < 70; k++)
        {
            float a = Mathf.Pi + rng.Randf() * Mathf.Pi;
            float rr = R * (0.35f + 0.65f * rng.Randf());
            var top = c + tilt * new Vector3(Mathf.Cos(a) * rr, Mathf.Sin(a) * rr, 0) + face * (0.45f + 0.2f * rng.Randf());
            float len = 0.8f + 2.4f * rng.Randf();
            float sway = rng.Randf() * 0.4f;
            Tube(fine, Path(6, t => top + new Vector3(sway * t, -len * t, 0.25f * t * t)), t => 0.035f * (1 - 0.85f * t), 3);
        }
        // Stones the roots tore up with them.
        for (int k = 0; k < 9; k++)
        {
            float a = rng.Randf() * Mathf.Tau, rr = R * rng.Randf() * 0.85f;
            var at = c + tilt * new Vector3(Mathf.Cos(a) * rr, Mathf.Sin(a) * rr, 0) + face * 0.45f;
            float s = 0.18f + 0.25f * rng.Randf();
            Lathe(stone, Pts(0, -s, s, -s * 0.3f, s * 0.9f, s * 0.4f, 0, s), 8, new Transform3D(Basis.Identity, at),
                warp: p => p + (p - at) * (Noise(p.X * 4 + k, p.Z * 4) - 0.5f) * 0.6f);
        }
        // The trunk, lying back into the wood behind the plate, its far end on the ground.
        var t0 = c - face * 0.4f + Vector3.Down * 0.6f;
        var t1 = new Vector3(1.8f, G(1.8f, -17f) + 0.9f, -17f);
        Tube(bark, Path(14, t => t0.Lerp(t1, t) + Vector3.Up * Mathf.Sin(t * Mathf.Pi) * 0.4f), t => 1.15f - 0.45f * t, 14);
        // Its branches, broken off short.
        for (int k = 0; k < 5; k++)
        {
            var at = t0.Lerp(t1, 0.35f + 0.13f * k);
            var d = new Vector3(k % 2 == 0 ? 1 : -1, 0.6f, -0.3f).Normalized();
            Tube(bark, new List<Vector3> { at, at + d * (1.2f + rng.Randf()) }, t => 0.28f - 0.18f * t, 6);
        }
        return Hold((earth.Mesh(true), Surface("forest_ground_04", 1.6f, "#5a4c40")), (roots.Mesh(true), Surface("rough_wood", 0.9f, "#6a5e52")),
            (fine.Mesh(), Mat("#3e3428", 0, 0.9f)), (bark.Mesh(true), Surface("rough_wood", 1.2f, "#5e544a")), (stone.Mesh(true), Surface("rock_boulder_dry", 0.8f, "#8a8478")));
    }

    /// <summary>A deadfall: a dead tree come down years ago, its bark gone and the wood weathered
    /// silver, its limbs snapped to stubs; the brash it dropped heaped at its crown end. Dry, and
    /// pale against the dark litter, so from thirty metres up it reads as the thing that will
    /// burn. Its length along X, the brash at +X; knee high.</summary>
    static Node3D Deadfall(int seed)
    {
        var wood = new Build();
        var brash = new Build();
        var rng = new RandomNumberGenerator { Seed = (ulong)(seed * 31 + 7) };
        float len = 3.4f + 0.6f * rng.Randf();
        var a = new Vector3(-len / 2, 0.24f, 0);
        var b = new Vector3(len / 2, 0.16f, 0.15f * (rng.Randf() - 0.5f));
        Tube(wood, Path(10, t => a.Lerp(b, t) + new Vector3(0, 0.04f * Mathf.Sin(t * 7), 0.06f * Mathf.Sin(t * 4 + seed))), t => 0.27f - 0.1f * t, 10);
        // The root end, snapped: a stump of splinters.
        for (int k = 0; k < 6; k++)
        {
            float ang = k * Mathf.Tau / 6 + rng.Randf() * 0.4f;
            var at = a + new Vector3(0, Mathf.Sin(ang) * 0.18f, Mathf.Cos(ang) * 0.18f);
            Tube(wood, new List<Vector3> { at, at + new Vector3(-0.25f - 0.2f * rng.Randf(), Mathf.Sin(ang) * 0.1f, Mathf.Cos(ang) * 0.1f) }, t => 0.06f * (1 - t), 4);
        }
        // Limbs snapped to stubs, up and out.
        for (int k = 0; k < 5; k++)
        {
            var at = a.Lerp(b, 0.25f + 0.15f * k);
            float side = k % 2 == 0 ? 1 : -1;
            var d = new Vector3(0.3f, 0.5f + 0.4f * rng.Randf(), side * (0.6f + 0.3f * rng.Randf())).Normalized();
            Tube(wood, new List<Vector3> { at, at + d * (0.35f + 0.5f * rng.Randf()) }, t => 0.08f * (1 - 0.7f * t), 5);
        }
        // The brash, heaped at the crown end: sticks every way, a heap knee high.
        for (int k = 0; k < 24; k++)
        {
            var c = b + new Vector3(0.2f + rng.Randf() * 0.8f, 0, (rng.Randf() - 0.5f) * 1.1f);
            float ang = rng.Randf() * Mathf.Tau, l = 0.5f + 0.9f * rng.Randf();
            var d = new Vector3(Mathf.Cos(ang), 0.1f + 0.3f * rng.Randf(), Mathf.Sin(ang));
            var s0 = c + new Vector3(0, 0.05f + 0.25f * rng.Randf(), 0) - d * l * 0.5f;
            Tube(brash, new List<Vector3> { s0, s0 + d * l }, t => 0.045f * (1 - 0.6f * t), 4);
        }
        return Hold((wood.Mesh(true), Surface("rough_wood", 0.8f, "#a29a8c")), (brash.Mesh(true), Surface("rough_wood", 0.6f, "#5a5248")));
    }

    /// <summary>A clump of reeds at the sick water's edge: forty-odd blades a metre to a metre
    /// and a half tall, leaning out, a few broken over, the year's last bulrush heads standing
    /// among them. Under the 2.2 m the fight is read over; the blighted come out of them.</summary>
    static Node3D Reeds(int seed)
    {
        var live = new Build();
        var dead = new Build();
        var heads = new Build();
        var rng = new RandomNumberGenerator { Seed = (ulong)(seed * 7919 + 13) };
        for (int k = 0; k < 60; k++)
        {
            float a = rng.Randf() * Mathf.Tau, rr = 0.5f * Mathf.Sqrt(rng.Randf());
            var foot = new Vector3(Mathf.Cos(a) * rr, 0, Mathf.Sin(a) * rr);
            float h = 0.9f + 0.6f * rng.Randf();
            var lean = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a)) * (0.1f + 0.35f * rng.Randf());
            bool broken = rng.Randf() < 0.12f;
            float w = 0.025f + 0.015f * rng.Randf();
            var across = new Vector3(-Mathf.Sin(a), 0, Mathf.Cos(a));
            var b = rng.Randf() < 0.25f ? dead : live;
            int n = 5;
            int prev = -1;
            for (int s = 0; s <= n; s++)
            {
                float t = s / (float)n;
                var p = foot + Vector3.Up * h * t + lean * h * t * t;
                if (broken && t > 0.6f) p = foot + Vector3.Up * h * 0.6f + lean * h * 0.36f + (lean.Normalized() + Vector3.Down * 0.6f) * h * (t - 0.6f);
                float ww = w * (1 - t * 0.9f);
                var nrm = across.Cross(Vector3.Up).Normalized();
                int l = b.V(p - across * ww, nrm), r = b.V(p + across * ww, nrm);
                if (prev >= 0) b.Quad(prev, prev + 1, r, l);
                prev = l;
            }
            if (!broken && rng.Randf() < 0.18f)
            {
                var top = foot + Vector3.Up * h * 0.85f + lean * h * 0.72f;
                Lathe(heads, Pts(0, -0.1f, 0.03f, -0.08f, 0.032f, 0.08f, 0, 0.1f), 6, new Transform3D(Basis.Identity, top));
            }
        }
        return Hold((live.Mesh(), Mat("#36422a", 0, 0.75f, true)), (dead.Mesh(), Mat("#5c5038", 0, 0.8f, true)), (heads.Mesh(), Mat("#3a2414", 0, 0.9f)));
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
