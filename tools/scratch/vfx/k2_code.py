from ed import edit

S = r"src\Fx\BattleFx.Skills.cs"

# ---------------------------------------------------------------- Moonfall: its hits in moonlight, not arcane pink
edit(S, [
    ('''        float flare = Mathf.Min(1.3f, (0.45f + share * 0.9f) * (e.Crit ? 1.4f : 1) * g);
        Sparks.Spawn(at, Vector3.Zero, e.Crit ? 0.1f : 0.07f, flare, pal.Glow * (e.Crit ? 0.75f : 0.55f), pal.Glow * 0.2f, flare * 0.4f, sprite: Sprites.Of("flare"), spinV: 0);''',
     '''        // A moon's blows in its own cold light, and small: Moonfall's heavy hits threw the arcane
        // school's pink flare a metre and more across, a pink ball under every moon.
        bool moon = art is "moon" or "moon_brand" or "moonfall";
        float flare = Mathf.Min(1.3f, (0.45f + share * 0.9f) * (e.Crit ? 1.4f : 1) * g) * (moon ? 0.55f : 1);
        var flareCol = moon ? new Color(0.42f, 0.46f, 1.0f) : pal.Glow;
        Sparks.Spawn(at, Vector3.Zero, e.Crit ? 0.1f : 0.07f, flare, flareCol * (e.Crit ? 0.75f : 0.55f), flareCol * 0.2f, flare * 0.4f, sprite: Sprites.Of("flare"), spinV: 0);'''),
    ('''                // Arcane: motes thrown off that hang and wink out.
                for (int i = 0; i < n; i++)
                    Sparks.Spawn(at, away * (1 + R() * 2.5f) + new Vector3((R() - 0.5f) * 3.5f, 0.5f + R() * 2.5f, (R() - 0.5f) * 3.5f), 0.45f + R() * 0.35f, 0.06f + R() * 0.05f, pal.Core, pal.Glow, 0.01f, -0.3f, 3.5f, sprite: R() < 0.35f ? Sprites.Of("star") : 0, spinV: 5);''',
     '''                // Arcane: motes thrown off that hang and wink out (a moon's in silver and violet).
                for (int i = 0; i < n; i++)
                    Sparks.Spawn(at, away * (1 + R() * 2.5f) + new Vector3((R() - 0.5f) * 3.5f, 0.5f + R() * 2.5f, (R() - 0.5f) * 3.5f), 0.45f + R() * 0.35f, 0.06f + R() * 0.05f,
                        moon ? MoonSilver : pal.Core, moon ? MoonFire(art) * 0.5f : pal.Glow, 0.01f, -0.3f, 3.5f, sprite: R() < 0.35f ? Sprites.Of("star") : 0, spinV: 5);'''),
])

# ---------------------------------------------------------------- burning ground: no lit rim, char under it, fires as short lines
edit(S, [
    ('''            var fill = Ground(z.X, z.Z, r, fillTex, FillOf(z.Art, edgeCol), 1e6f, 1.0f);
            var edge = Ground(z.X, z.Z, r, rimTex, edgeCol, 1e6f, 2.2f);
            g = (edge, fill);
            grounds[z.Id] = g;''',
     '''            var fill = Ground(z.X, z.Z, r, fillTex, FillOf(z.Art, edgeCol), 1e6f, 1.0f);
            var edge = Ground(z.X, z.Z, r, rimTex, edgeCol, 1e6f, 2.2f);
            g = (edge, fill);
            grounds[z.Id] = g;
            // Burning ground is charred where it burns: its reach is the char and the fires in it, not a
            // lit rim (two burning grounds' rims, with their flames round them, read as orange hoops).
            if (inside == Inside.Embers)
                Scars.Add("scorch", V(z.X, Y(z.X, z.Z), z.Z), r * 1.05f, (float)Math.Max(0.8, z.Life - z.Age) + 1.5f, 0);'''),
    ('''        g.Edge.Decal.Modulate = Dim(edgeCol, fade * breathe * (inside is Inside.Roots or Inside.Veins ? 0.22f : 0.34f) * hush);''',
     '''        g.Edge.Decal.Modulate = Dim(edgeCol, fade * breathe * (inside == Inside.Embers ? 0 : inside is Inside.Roots or Inside.Veins ? 0.22f : 0.34f) * hush);'''),
    ('''                // Spread through it, none at its very edge; one near its middle.
                float a = a0 + (i + (R() - 0.5f) * 0.7f) / n * Mathf.Tau, d = i == 0 ? r * 0.1f * R() : r * (0.3f + R() * 0.4f);
                fires.Add((mesh, mat, new Vector2(Mathf.Cos(a) * d, Mathf.Sin(a) * d), 0.26f + R() * 0.16f));''',
     '''                // Spread through it, none at its very edge; one near its middle. Each a short line of
                // flame turned its own way (a knot of cards round a point read from above as a small
                // orange ring).
                float a = a0 + (i + (R() - 0.5f) * 0.7f) / n * Mathf.Tau, d = i == 0 ? r * 0.1f * R() : r * (0.3f + R() * 0.4f);
                mesh.Rotation = new Vector3(0, R() * Mathf.Tau, 0);
                fires.Add((mesh, mat, new Vector2(Mathf.Cos(a) * d, Mathf.Sin(a) * d), 0.3f + R() * 0.2f));'''),
    ('''            f.Mesh.Scale = new Vector3(f.Size, 0.55f + f.Size * 0.8f, f.Size);''',
     '''            f.Mesh.Scale = new Vector3(f.Size, 0.55f + f.Size * 0.8f, f.Size * 0.14f);'''),
])

# ---------------------------------------------------------------- Ford Ice: black ice, a trail of its own each throw
edit(S, [
    ('''    /// <summary>Where each Ford Ice last froze the ground it passed.</summary>
    readonly System.Collections.Generic.Dictionary<int, Vector3> fordLast = new();''',
     '''    /// <summary>Where each Ford Ice last froze the ground it passed.</summary>
    readonly System.Collections.Generic.Dictionary<int, Vector3> fordLast = new();

    /// <summary>Black ice: deep, its glow held down so its facets and point catch the light and the
    /// rest stays dark (at full glow the crystal's white edges and tip made it read pale).</summary>
    static readonly Color BlackIce = Hdr("#1c4aa8", 1f) with { A = 0.5f };'''),
    ('''        shards.Add(new Transform3D(basis.Scaled(Vector3.One * 0.85f * s), at), Hdr("#0f2c66", 1f) with { A = 1 });
        orbs.Add(new Transform3D(Godot.Basis.Identity.Scaled(Vector3.One * 0.09f * s), at + fwd * 0.4f * s), Hdr("#bfe6ff", 1.6f));
        Ribbons.Feed(key, at - fwd * 0.35f * s, 0.14f * s, 0.2f, Hdr("#2a6cff", 1f), 1.1f, Ribbons.Style.Frost);
        if (fordLast.Count > 256) fordLast.Clear();
        if (!fordLast.TryGetValue(p.Id, out var last)) fordLast[p.Id] = last = at;''',
     '''        shards.Add(new Transform3D(basis.Scaled(Vector3.One * 0.85f * s), at), Hdr("#0f2c66", 1f) with { A = 0.42f });
        orbs.Add(new Transform3D(Godot.Basis.Identity.Scaled(Vector3.One * 0.07f * s), at + fwd * 0.4f * s), Hdr("#bfe6ff", 1.3f));
        Ribbons.Feed(key, at - fwd * 0.35f * s, 0.12f * s, 0.1f, Hdr("#1e50d0", 1f), 0.9f, Ribbons.Style.Frost);
        if (fordLast.Count > 256) fordLast.Clear();
        if (!fordLast.TryGetValue(p.Id, out var last) || p.Age < 0.05) fordLast[p.Id] = last = at;'''),
    ('''            Erupt(at.X, at.Z, 0.15f, 0.7f, 3, SpikeKind.Ice, 0.75f * g, 1.1f, Hdr("#1c4aa8", 1f));''',
     '''            Erupt(at.X, at.Z, 0.15f, 0.7f, 3, SpikeKind.Ice, 0.75f * g, 1.1f, BlackIce);'''),
    # A spike keeps the glow it was given (black ice is held down), fading as it sinks.
    ('''            var c = s.Color with { A = 1 - sink };''',
     '''            var c = s.Color with { A = s.Color.A * (1 - sink) };'''),
    # Absolute Zero's black ice.
    ('''                var ice = zero ? Hdr("#1c4aa8", 1.0f) : IceDeep;''',
     '''                var ice = zero ? BlackIce : IceDeep;'''),
])

# A thing in flight that reuses a body's number (the battle's pool) starts a trail of its own: a trail
# kept by that number joined the last throw's end, far off, to the new one at her hand.
edit(S, [
    ('''        long key = p.Id * 7919L + (long)(p.Art.GetHashCode() & 0xffff);''',
     '''        if (!flown.TryGetValue(p.Id, out var fl) || p.Age < fl.Age) fl = (p.Age, fl.Gen + 1);
        flown[p.Id] = (p.Age, fl.Gen);
        if (flown.Count > 4096) flown.Clear();
        long key = p.Id * 7919L + (long)(p.Art.GetHashCode() & 0xffff) + ((long)fl.Gen << 40);'''),
    ('''    /// <summary>The spirit beasts of Spirit Herd: the crowd's wolf, drawn as a crowd of its own.</summary>''',
     '''    /// <summary>Each body in flight's age when last drawn, and how many throws its number has carried.</summary>
    readonly System.Collections.Generic.Dictionary<int, (double Age, int Gen)> flown = new();

    /// <summary>The spirit beasts of Spirit Herd: the crowd's wolf, drawn as a crowd of its own.</summary>'''),
])

# ---------------------------------------------------------------- Sunlance's ash: going up off the dead as it passes
edit(S, [
    ('''            for (int i = 0; i < 16; i++)
            {
                var at = a.Lerp(b, 0.1f + R() * 0.9f) + new Vector3((R() - 0.5f) * w, -0.6f + R() * 0.8f, (R() - 0.5f) * w);
                Smoke.Spawn(at, new Vector3((R() - 0.5f) * 0.6f, 0.7f + R() * 0.8f, (R() - 0.5f) * 0.6f), 1.1f + R() * 0.7f, 0.05f + R() * 0.04f,
                    new Color(0.16f, 0.13f, 0.11f), new Color(0.08f, 0.07f, 0.06f), -1, gravity: -0.3f, drag: 0.8f, sprite: Sprites.Of("dirt"), spinV: 4);
                if (R() < 0.5f) Sparks.Spawn(at, new Vector3((R() - 0.5f) * 0.5f, 0.9f + R(), (R() - 0.5f) * 0.5f), 0.6f + R() * 0.5f, 0.035f, Ember, EmberDeep, 0.01f, -0.6f, 1.2f);
            }''',
     '''            // The dead it sears going up as ash after it: grey flakes lifting off them, their edges
            // still alight, drifting up and away. (Laid along its line at once, they read as dark
            // stitches down the beam.)
            var side = (b - a).Cross(Vector3.Up).Normalized();
            for (int i = 0; i < 22; i++)
            {
                var at = a.Lerp(b, 0.08f + R() * 0.92f) + side * (R() - 0.5f) * 1.6f + Vector3.Down * (0.5f + R() * 0.5f);
                pending.Add((time + 0.05 + R() * 0.35, () =>
                {
                    Smoke.Spawn(at, new Vector3((R() - 0.5f) * 0.5f, 0.6f + R() * 0.7f, (R() - 0.5f) * 0.5f), 1.4f + R() * 0.7f, 0.08f + R() * 0.05f,
                        new Color(0.34f, 0.31f, 0.28f), new Color(0.13f, 0.12f, 0.11f), 0.05f, gravity: -0.25f, drag: 0.7f, sprite: Sprites.Of("dirt"), spinV: 3);
                    if (R() < 0.6f) Sparks.Spawn(at, new Vector3((R() - 0.5f) * 0.5f, 0.8f + R(), (R() - 0.5f) * 0.5f), 0.7f + R() * 0.5f, 0.035f, Ember, EmberDeep, 0.01f, -0.5f, 1.2f);
                }));
            }'''),
])

# ---------------------------------------------------------------- Skybreak: fewer, thinner, never a white mass
edit(S, [
    ('''                bool leap = art == "arc_sky";
                var top = ground + new Vector3((R() - 0.5f) * 1.5f, leap ? 8 : 11, (R() - 0.5f) * 1.5f);
                var foot = ground + Vector3.Up * 0.2f;
                var col = Hdr("#7aa6ff", 1f);
                Ribbons.Bolt(top, foot, 0.12f * g, 0.12f, col, 2.4f, 1, 0.2f);
                Ribbons.Bolt(top, foot, 0.36f * g, 0.1f, Hdr("#1e3cc0", 1f), 0.9f, 0, 0.18f);''',
     '''                bool leap = art == "arc_sky";
                var foot = ground + Vector3.Up * 0.2f;
                var col = Hdr("#7aa6ff", 1f);
                // Where the sky has just answered a leap, its second blow is the crackle on the ground
                // only: two bolts to every body a leap touched stood as a white wall of them.
                bool struck = false;
                for (int i = skyStruck.Count - 1; i >= 0; i--)
                {
                    if (time - skyStruck[i].At > 0.6) { skyStruck.RemoveAt(i); continue; }
                    if (!leap && skyStruck[i].Where.DistanceTo(ground) < 1.5f) struck = true;
                }
                if (leap) skyStruck.Add((ground, time));
                if (!struck)
                {
                    var top = ground + new Vector3((R() - 0.5f) * 1.5f, leap ? 8 : 11, (R() - 0.5f) * 1.5f);
                    Ribbons.Bolt(top, foot, 0.1f * g, 0.12f, col, 1.7f, 1, 0.2f);
                    Ribbons.Bolt(top, foot, 0.3f * g, 0.1f, Hdr("#1e3cc0", 1f), 0.7f, 0, 0.18f);'''),
    ('''                // The return stroke, a breath later down the same path.
                pending.Add((time + 0.07, () => Ribbons.Bolt(top, foot, 0.09f * g, 0.08f, col, 2.0f, 0, 0.22f)));
                for (int i = 0; i < 2; i++)''',
     '''                    // The return stroke, a breath later down the same path.
                    pending.Add((time + 0.07, () => Ribbons.Bolt(top, foot, 0.08f * g, 0.08f, col, 1.5f, 0, 0.22f)));
                }
                for (int i = 0; i < 2; i++)'''),
    ('''    /// <summary>When the last of Skybreak's bolts was told, and how many have come that frame.</summary>
    double skyAt = -1;
    int skyN;''',
     '''    /// <summary>When the last of Skybreak's bolts was told, and how many have come that frame; and
    /// where the sky has struck in the last moment.</summary>
    double skyAt = -1;
    int skyN;
    readonly System.Collections.Generic.List<(Vector3 Where, double At)> skyStruck = new();'''),
])
