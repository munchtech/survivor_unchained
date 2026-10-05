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
            "timber" => Timber(seed),
            "cookpot" => CookPot(),
            "winch" => Winch(),
            "knoll" => Knoll(seed, ground),
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
        return Hold((earth.Mesh(true), Surface("forest_ground_04", 1.6f, "#8a7a66")), (roots.Mesh(true), Surface("rough_wood", 0.9f, "#9a8a76")),
            (fine.Mesh(), Mat("#6a5a46", 0, 0.9f)), (bark.Mesh(true), Surface("rough_wood", 1.2f, "#5e544a")), (stone.Mesh(true), Surface("rock_boulder_dry", 0.8f, "#8a8478")));
    }

    /// <summary>The Roost's pot: "one pot big enough for all of them", forty-one mouths. A black
    /// iron cauldron as wide as a cart wheel, its lip rolled, hung from a chain off a tripod of
    /// rough poles over the cookfire (the fire is the camp's own, set by the place); a ladle
    /// in it, its stew catching the firelight. From above it reads as a dark ring with a
    /// gleaming middle under three crossing poles, not a ball.</summary>
    static Node3D CookPot()
    {
        var iron = new Build();
        var wood = new Build();
        var stew = new Build();
        var chain = new Build();
        const float R = 0.75f, y0 = 0.55f;
        // The pot: round-bellied, its lip rolled outward.
        Lathe(iron, Pts(0, y0, R * 0.55f, y0 + 0.04f, R * 0.92f, y0 + 0.25f, R, y0 + 0.5f, R * 0.93f, y0 + 0.78f, R * 0.95f, y0 + 0.84f, R * 1.02f, y0 + 0.86f,
            R * 0.98f, y0 + 0.82f, R * 0.88f, y0 + 0.8f), 28);
        // Three stubby legs.
        for (int k = 0; k < 3; k++)
        {
            float a = k * Mathf.Tau / 3;
            Tube(iron, new List<Vector3> { new(Mathf.Cos(a) * R * 0.5f, y0 + 0.05f, Mathf.Sin(a) * R * 0.5f), new(Mathf.Cos(a) * R * 0.62f, 0.25f, Mathf.Sin(a) * R * 0.62f) }, 0.05f, 5);
        }
        // The stew, a little below the lip.
        Lathe(stew, Pts(0, y0 + 0.72f, R * 0.88f, y0 + 0.72f), 28, warp: p => p + new Vector3(0, 0.02f * Mathf.Sin(p.X * 9) * Mathf.Cos(p.Z * 7), 0));
        // The tripod over it, its poles crossing at the top, the chain down to the bail.
        var top = new Vector3(0, 2.6f, 0);
        for (int k = 0; k < 3; k++)
        {
            float a = k * Mathf.Tau / 3 + 0.4f;
            var foot = new Vector3(Mathf.Cos(a) * 1.7f, 0, Mathf.Sin(a) * 1.7f);
            Beam(wood, foot, top + (top - foot).Normalized() * 0.35f, 0.11f);
        }
        Tube(chain, new List<Vector3> { top, new(0, y0 + 1.3f, 0) }, 0.025f, 4);
        Tube(chain, Path(12, t => new Vector3(Mathf.Cos(t * Mathf.Pi) * R * 0.95f, y0 + 0.86f + Mathf.Sin(t * Mathf.Pi) * 0.45f, 0)), 0.02f, 4);
        // The ladle.
        Tube(wood, new List<Vector3> { new(R * 0.3f, y0 + 0.7f, 0.1f), new(R * 1.1f, y0 + 1.25f, 0.35f) }, 0.025f, 4);
        return Hold((iron.Mesh(), Mat("#1e1c1a", 0.75f, 0.42f)), (wood.Mesh(true), Surface("rough_wood", 0.8f, "#6e5e4c")),
            (stew.Mesh(), Mat("#3a2412", 0, 0.18f)), (chain.Mesh(), Wrought()));
    }

    /// <summary>The Dig's timber, stacked where it was unloaded: squared props and sleepers in
    /// courses laid crosswise, a few askew, one leaning against the stack. Knee to waist high;
    /// from above, the crosshatch of pale sawn ends and dark sides reads as worked wood.</summary>
    static Node3D Timber(int seed)
    {
        var wood = new Build();
        var rng = new RandomNumberGenerator { Seed = (ulong)(seed * 977 + 5) };
        int courses = 3 + (int)(rng.Randf() * 3);
        float y = 0;
        for (int c = 0; c < courses; c++)
        {
            bool across = c % 2 == 1;
            int n = 4 - (c > 2 ? 1 : 0);
            for (int k = 0; k < n; k++)
            {
                float o = (k - (n - 1) / 2f) * 0.3f + (rng.Randf() - 0.5f) * 0.05f;
                float len = 2.2f + 0.4f * rng.Randf(), skew = (rng.Randf() - 0.5f) * 0.12f;
                var a = across ? new Vector3(o, y + 0.1f, -len / 2) : new Vector3(-len / 2, y + 0.1f, o);
                var b = across ? new Vector3(o + skew, y + 0.1f, len / 2) : new Vector3(len / 2, y + 0.1f, o + skew);
                Beam(wood, a, b, 0.22f, 0.18f);
            }
            y += 0.19f;
        }
        // One prop leant against the stack.
        Beam(wood, new Vector3(1.6f, 0.02f, 0.4f), new Vector3(0.7f, y + 0.1f, 0.2f), 0.2f);
        return Hold((wood.Mesh(true), Surface("rough_wood", 1.0f, "#8a7a64")));
    }

    /// <summary>A windlass at the pit's lip: two A-frame trestles, a drum between them wound with
    /// rope, an iron crank. It stands on the lip with the rope going down; under 2 m.
    /// Its axle along X; origin at its middle on the ground.</summary>
    static Node3D Winch()
    {
        var wood = new Build();
        var iron = new Build();
        var rope = new Build();
        foreach (float sx in new[] { -1.1f, 1.1f })
        {
            Beam(wood, new Vector3(sx, 0, -0.7f), new Vector3(sx, 1.25f, 0), 0.16f);
            Beam(wood, new Vector3(sx, 0, 0.7f), new Vector3(sx, 1.25f, 0), 0.16f);
            Beam(wood, new Vector3(sx, 0.45f, -0.48f), new Vector3(sx, 0.45f, 0.48f), 0.1f);
        }
        Tube(iron, new List<Vector3> { new(-1.35f, 1.2f, 0), new(1.35f, 1.2f, 0) }, 0.05f, 6);
        Lathe(wood, Pts(0.26f, -0.85f, 0.3f, -0.8f, 0.3f, 0.8f, 0.26f, 0.85f), 14, new Transform3D(new Basis(Vector3.Back, Mathf.Pi / 2), new Vector3(0, 1.2f, 0)));
        // The rope wound on the drum, and paid out over its front.
        for (int k = 0; k < 9; k++)
        {
            float x = -0.7f + k * 0.175f;
            Tube(rope, Path(16, t => new Vector3(x, 1.2f + 0.31f * Mathf.Sin(t * Mathf.Tau), 0.31f * Mathf.Cos(t * Mathf.Tau)), true), 0.025f, 4, true);
        }
        Tube(rope, new List<Vector3> { new(0.2f, 1.2f, 0.32f), new(0.25f, 0.2f, 1.6f), new(0.25f, -2.5f, 2.2f) }, 0.025f, 4);
        // The crank.
        Tube(iron, new List<Vector3> { new(1.35f, 1.2f, 0), new(1.35f, 1.55f, 0.15f), new(1.6f, 1.55f, 0.15f) }, 0.035f, 5);
        return Hold((wood.Mesh(true), Surface("rough_wood", 0.9f, "#7a6a56")), (iron.Mesh(), Wrought()), (rope.Mesh(), Mat("#8a7a5a", 0, 0.9f)));
    }

    /// <summary>A deadfall: a dead tree come down years ago, its bark gone and the wood weathered
    /// silver, its limbs snapped to stubs; the brash it dropped heaped at its crown end. Dry, and
    /// pale against the dark litter, so from thirty metres up it reads as the thing that will
    /// burn. Its length along X, the brash at +X; knee high.</summary>
    /// <summary>A knoll of bare rock, as Old Blue's three are in the clough: the ground's rise
    /// (HollowNight's relief) sheathed in stone, its top a worn table he stands up on to howl,
    /// its sides broken in ledges down into the litter, its rim ragged. Its origin is the
    /// rise's top; its foot finds the ground all round (the probe), sunk a hand into it. From
    /// above it reads as rock standing out of the leaves, never as a grey disc painted on them.</summary>
    static Node3D Knoll(int seed, Func<Vector3, float>? ground)
    {
        float G(float x, float z) => ground?.Invoke(new Vector3(x, 0, z)) ?? -0.8f;
        var rock = new Build();
        const float R = 2.5f;
        float s0 = seed * 0.37f;
        // The profile, from the middle of the top out and down; a height under 0 is how far down
        // toward the ground it goes (0 the top, -1 its foot in the ground).
        var prof = Pts(0, -1.05f, R * 1.08f, -1.05f, R * 1.02f, -0.75f, R * 0.93f, -0.5f, R * 0.88f, -0.28f, R * 0.74f, -0.1f, R * 0.5f, 0.03f, 0, 0.05f);
        Vector3 Shape(Vector3 p)
        {
            float a = Mathf.Atan2(p.Z, p.X), r = new Vector2(p.X, p.Z).Length();
            // A ragged rim, two scales of it.
            float rim = 1 + 0.2f * (Noise(Mathf.Cos(a) * 1.6f + s0, Mathf.Sin(a) * 1.6f) - 0.5f) * 2 + 0.07f * (Noise(Mathf.Cos(a) * 5 + s0, Mathf.Sin(a) * 5 + 3) - 0.5f) * 2;
            // Ledges: the sides step in where the stone splits along its bedding.
            float down = Mathf.Clamp(-p.Y, 0, 1.05f);
            float ledge = 1 - 0.07f * Mathf.Sin(down * 11 + Noise(p.X * 0.8f + s0, p.Z * 0.8f) * 4);
            var xz = new Vector2(p.X, p.Z) * rim * (down > 0.05f ? ledge : 1);
            float top = 0.05f * (Noise(p.X * 1.4f + s0, p.Z * 1.4f) - 0.5f) * Mathf.Min(1, r / R);
            float y = p.Y >= 0 ? p.Y + top : Mathf.Lerp(top, G(xz.X, xz.Y) - 0.12f, down);
            return new Vector3(xz.X, y, xz.Y);
        }
        Lathe(rock, prof, 36, warp: Shape);
        // (Darker than the boulders' scan as shot: pale, the three read as the brightest things
        // in the clough, over her.)
        return Hold((rock.Mesh(true), Surface("rock_boulder_dry", 1.4f, "#6c706c")));
    }

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
