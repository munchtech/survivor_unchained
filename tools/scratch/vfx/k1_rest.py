from ed import edit

# ---------------------------------------------------------------- the sky's bolts and the moons
edit(r"src\Fx\BattleFx.Skills.cs", [
    ('''        if (art is not ("storm_bolt" or "storm_clap" or "storm_eye" or "arc_sky" or "moonfall" or "arrow_rain" or "slash_quake")) return false;
        float r = (float)e.Radius;''',
     '''        if (art is not ("storm_bolt" or "storm_clap" or "storm_eye" or "arc_sky" or "sky_bolt" or "moonfall" or "arrow_rain" or "slash_quake")) return false;
        float r = (float)e.Radius;
        // Skybreak's bolts come down one after another along the chain, as the sky answers each
        // leap in turn (all in the same frame, they stood as one white wall).
        if (art == "arc_sky" && e.Delay <= 0.05)
        {
            if (time - skyAt > 1e-4) { skyAt = time; skyN = 0; }
            var sky = e;
            pending.Add((time + 0.045 * skyN++, () => Landing(sky)));
            return true;
        }'''),
    ('''    void Landing(Ev.Strike e)
    {''',
     '''    /// <summary>When the last of Skybreak's bolts was told, and how many have come that frame.</summary>
    double skyAt = -1;
    int skyN;

    void Landing(Ev.Strike e)
    {'''),
    ('''            case "storm_bolt" or "storm_clap" or "storm_eye" or "arc_sky":
            {
                bool clap = art == "storm_clap", small = art == "arc_sky";''',
     '''            case "arc_sky" or "sky_bolt":
            {
                // Skybreak's answer to each leap, a blessing's bolt: a thin jagged thread straight down
                // out of the dark, struck twice as lightning strikes, its glow narrow and deep blue; a
                // crackle and a scorch where it lands. (With no art, the blessing's and Skybreak's own
                // bolts were sixteen-metre pillars of the storm's white over a ring: white columns
                // through the screen.)
                bool leap = art == "arc_sky";
                var top = ground + new Vector3((R() - 0.5f) * 1.5f, leap ? 8 : 11, (R() - 0.5f) * 1.5f);
                var foot = ground + Vector3.Up * 0.2f;
                var col = Hdr("#7aa6ff", 1f);
                Ribbons.Bolt(top, foot, 0.12f * g, 0.12f, col, 2.4f, 1, 0.2f);
                Ribbons.Bolt(top, foot, 0.36f * g, 0.1f, Hdr("#1e3cc0", 1f), 0.9f, 0, 0.18f);
                // The return stroke, a breath later down the same path.
                pending.Add((time + 0.07, () => Ribbons.Bolt(top, foot, 0.09f * g, 0.08f, col, 2.0f, 0, 0.22f)));
                for (int i = 0; i < 2; i++)
                {
                    float a = R() * Mathf.Tau, d = 0.7f + R() * 0.7f;
                    double x = e.X + Mathf.Cos(a) * d, z = e.Z + Mathf.Sin(a) * d;
                    Ribbons.Bolt(foot, V(x, Y(x, z) + 0.15, z), 0.08f * g, 0.12f, col, 2.2f, 0, 0.3f);
                }
                Sparks.Spawn(ground + Vector3.Up * 0.3f, Vector3.Zero, 0.1f, 0.6f * g, Hdr("#8ab4ff", 1.2f), Hdr("#2a50ff", 0.5f), 0.9f * g, sprite: Sprites.Of("spark"), spinV: 0);
                for (int i = 0; i < 6; i++)
                    Sparks.Spawn(ground + Vector3.Up * 0.3f, new Vector3((R() - 0.5f) * 7, 1 + R() * 3, (R() - 0.5f) * 7), 0.15f + R() * 0.1f, 0.035f, Hdr("#a8c8ff", 1.4f), Hdr("#2a50ff", 0.8f), 0.01f, 6, 4);
                Scars.Add("scorch", ground, 0.55f, 2.5f, 0);
                Flash(ground + Vector3.Up * 2.5f, new Color(0.45f, 0.6f, 1f), leap ? 3 : 5, 0.16f, 7);
                return;
            }
            case "storm_bolt" or "storm_clap" or "storm_eye":
            {
                bool clap = art == "storm_clap", small = false;'''),
    ('''            case "moonfall":
            {
                // A moon falling: a pale streak down out of the dark, and the burst where it breaks.
                var top = ground + new Vector3(-2.5f, 14, 1.5f);
                // Moonlight cold silver-blue, its breaking a deep violet: pale lilac streaks, stardust
                // and rings read pink-white, a field of lavender hoops.
                Ribbons.Line(new[] { top, top.Lerp(ground, 0.5f), ground + Vector3.Up * 0.3f }, 0.3f * g, 0.22f, Hdr("#a8bcff", 1f), 2.0f, Ribbons.Style.Glow, new[] { 0f, 0.6f, 1f });
                // The moon breaks into stardust (filmed, LTX), its light thrown out.
                Books.Spawn("moon_burst", ground + Vector3.Up * 0.6f, r * 0.7f, 0.65f, new Color(0.26f, 0.22f, 0.95f, 0.6f), flat: true, sizeEnd: r * 2.0f);
                Flash(ground + Vector3.Up * 1.5f, new Color(0.55f, 0.6f, 1f), 6, 0.3f, r * 3);
                Scars.Add("runes", ground, r * 0.6f, 1.2f, -0.7f);
                AddFront(ground, r * 1.2f, 0.3f, 0.16f * g, Hdr("#6a5aff", 1f), 1.2f, Ribbons.Style.Wisp, 0.2f);
                return;
            }''',
     '''            case "moonfall":
            {
                // A moon falling: a cold streak down out of the dark, and where it breaks its crescent
                // glints and shatters, silver thrown low and moonfire licking up off the ground in
                // Moonbrand's violet tongues, a dark scorch left. (Its ring, its rune circle and a
                // filmed burst under every moon read as lavender hoops round pink-white balls.)
                var top = ground + new Vector3(-2.5f, 14, 1.5f);
                Ribbons.Line(new[] { top, top.Lerp(ground, 0.5f), ground + Vector3.Up * 0.3f }, 0.26f * g, 0.2f, Hdr("#a8bcff", 1f), 1.8f, Ribbons.Style.Glow, new[] { 0f, 0.6f, 1f });
                var fire = MoonFire("moon");
                Smoke.Spawn(ground + Vector3.Up * 0.3f, Vector3.Zero, 0.55f, r * 0.55f, new Color(0.03f, 0.02f, 0.07f), null, r * 0.9f, alpha: 0.5f, sprite: -1);
                Sparks.Spawn(new Sparks.P
                {
                    At = ground + Vector3.Up * 0.5f, Life = 0.24f, Size = 0.9f * g, SizeEnd = 1.4f * g, Color = MoonSilver * 1.3f, ColorEnd = new Color(fire.R * 0.2f, fire.G * 0.2f, fire.B * 0.35f),
                    Alpha = 1, Sprite = Sprites.Range("crescent").First + 1, Spin = R() * Mathf.Tau + 0.001f, SpinV = 0.001f,
                });
                for (int i = 0; i < 14; i++)
                {
                    float a = R() * Mathf.Tau, v = r * (2 + R() * 2.5f);
                    Sparks.Spawn(ground + Vector3.Up * 0.4f, new Vector3(Mathf.Cos(a) * v, 1.5f + R() * 2.5f, Mathf.Sin(a) * v), 0.4f + R() * 0.3f, 0.07f + R() * 0.05f,
                        MoonSilver * 1.4f, fire * 0.3f, 0.02f, 9, 1.5f, sprite: Sprites.Of("star"), spinV: 6);
                }
                for (int i = 0; i < 9; i++)
                    MoonTongue(ground + new Vector3((R() - 0.5f) * r, 0.2f, (R() - 0.5f) * r), Vector3.Up * (1.2f + R() * 1.2f), (0.4f + R() * 0.2f) * g, fire);
                Flash(ground + Vector3.Up * 1.5f, new Color(0.55f, 0.6f, 1f), 5, 0.3f, r * 3);
                Scars.Add("scorch", ground, r * 0.4f, 3f, 0);
                return;
            }'''),
])

# ---------------------------------------------------------------- Ford Ice
edit(r"src\Fx\BattleFx.Skills.cs", [
    ('''            case "shard" or "shard_deep" or "spear_ice":
            {
                float s = (art == "spear_ice" ? 2.4f : art == "shard_deep" ? 1.2f : 1) * Mathf.Sqrt(g);''',
     '''            case "spear_ice":
                FordIce(p, at, heading, fwd, g, key);
                return true;
            case "shard" or "shard_deep":
            {
                float s = (art == "shard_deep" ? 1.2f : 1) * Mathf.Sqrt(g);'''),
    ('''                Ribbons.Feed(key, at - fwd * 0.3f * s, (art == "spear_ice" ? 0.6f : 0.26f) * s, art == "spear_ice" ? 0.3f : 0.15f, Hdr("#5ab8ff", 1f), 2f, Ribbons.Style.Frost);''',
     '''                Ribbons.Feed(key, at - fwd * 0.3f * s, 0.26f * s, 0.15f, Hdr("#5ab8ff", 1f), 2f, Ribbons.Style.Frost);'''),
    ('''    /// <summary>The spirit beasts of Spirit Herd: the crowd's wolf, drawn as a crowd of its own.</summary>''',
     '''    /// <summary>Where each Ford Ice last froze the ground it passed.</summary>
    readonly System.Collections.Generic.Dictionary<int, Vector3> fordLast = new();

    /// <summary>Ford Ice: a lance of black ice off the ford, running the length of the field. Dark
    /// glassy crystal, its facets and point catching cold light; behind it the ground it passes
    /// freezes, ice standing up in its wake and sinking, a cold breath low along its line. (A bright
    /// crystal on a metre-and-a-half ribbon of frost read as a white bar.)</summary>
    void FordIce(Projectile p, Vector3 at, float heading, Vector3 fwd, float g, long key)
    {
        float s = 2.2f * Mathf.Sqrt(g);
        var basis = new Godot.Basis(Vector3.Up, heading) * new Godot.Basis(Vector3.Right, Mathf.Pi / 2);
        Shade(at, 1.0f * s, 0.45f);
        shards.Add(new Transform3D(basis.Scaled(Vector3.One * 0.85f * s), at), Hdr("#0f2c66", 1f) with { A = 1 });
        orbs.Add(new Transform3D(Godot.Basis.Identity.Scaled(Vector3.One * 0.09f * s), at + fwd * 0.4f * s), Hdr("#bfe6ff", 1.6f));
        Ribbons.Feed(key, at - fwd * 0.35f * s, 0.14f * s, 0.2f, Hdr("#2a6cff", 1f), 1.1f, Ribbons.Style.Frost);
        if (fordLast.Count > 256) fordLast.Clear();
        if (!fordLast.TryGetValue(p.Id, out var last)) fordLast[p.Id] = last = at;
        if (new Vector2(at.X - last.X, at.Z - last.Z).Length() >= 1.4f)
        {
            fordLast[p.Id] = at;
            Erupt(at.X, at.Z, 0.15f, 0.7f, 3, SpikeKind.Ice, 0.75f * g, 1.1f, Hdr("#1c4aa8", 1f));
            Smoke.Spawn(V(at.X, Y(at.X, at.Z) + 0.3, at.Z), -fwd * 0.3f + Vector3.Up * 0.1f, 1.0f, 0.4f, new Color(0.6f, 0.78f, 1f), new Color(0.4f, 0.55f, 0.85f), 1.0f, drag: 1.5f, alpha: 0.13f);
        }
        if (R() < 0.35f) Sparks.Spawn(at, -fwd * (0.5f + R()) + new Vector3((R() - 0.5f) * 0.6f, (R() - 0.5f) * 0.4f, (R() - 0.5f) * 0.6f), 0.35f, 0.07f, Hdr("#dff4ff", 1.6f), Hdr("#5ab4ff", 1.0f), 0.02f, 2, 2, sprite: Sprites.Of("star"), spinV: 6);
    }

    /// <summary>The spirit beasts of Spirit Herd: the crowd's wolf, drawn as a crowd of its own.</summary>'''),
])

# ---------------------------------------------------------------- Sunlance
edit(r"src\Fx\BattleFx.Skills.cs", [
    ('''        if (sun)
        {
            Ribbons.Line(mid, w * 1.6f, life, col, 1.2f, Ribbons.Style.Glow, even);
            Ribbons.Line(mid, w * 0.45f, life * 0.9f, Hdr("#fff4d8", 1f), 3f, Ribbons.Style.Bolt, even);
        }''',
     '''        if (sun)
        {
            // Sunlance: a narrow lance of sunlight, a hot gold thread in a deep gold glow, held under
            // the tone curve's knee so it stays gold; what it sears goes up as ash. (Twice as wide
            // with a white heart, it read as a thick cream bar.)
            Ribbons.Line(mid, w * 0.7f, life, Hdr("#ff9a1e", 1f), 1.0f, Ribbons.Style.Glow, even);
            Ribbons.Line(mid, w * 0.16f, life * 0.9f, Hdr("#ffd27a", 1f), 2.2f, Ribbons.Style.Bolt, even);
            for (int i = 0; i < 16; i++)
            {
                var at = a.Lerp(b, 0.1f + R() * 0.9f) + new Vector3((R() - 0.5f) * w, -0.6f + R() * 0.8f, (R() - 0.5f) * w);
                Smoke.Spawn(at, new Vector3((R() - 0.5f) * 0.6f, 0.7f + R() * 0.8f, (R() - 0.5f) * 0.6f), 1.1f + R() * 0.7f, 0.05f + R() * 0.04f,
                    new Color(0.16f, 0.13f, 0.11f), new Color(0.08f, 0.07f, 0.06f), -1, gravity: -0.3f, drag: 0.8f, sprite: Sprites.Of("dirt"), spinV: 4);
                if (R() < 0.5f) Sparks.Spawn(at, new Vector3((R() - 0.5f) * 0.5f, 0.9f + R(), (R() - 0.5f) * 0.5f), 0.6f + R() * 0.5f, 0.035f, Ember, EmberDeep, 0.01f, -0.6f, 1.2f);
            }
        }'''),
    ('''        if (sun) Sparks.Spawn(a, Vector3.Zero, life * 0.6f, 0.9f * g, pal.Core * 0.7f, pal.Glow * 0.2f, 0.4f, sprite: Sprites.Of("flare"));''',
     '''        if (sun) Sparks.Spawn(a, Vector3.Zero, life * 0.6f, 0.5f * g, Hdr("#ffc060", 1.3f), pal.Glow * 0.2f, 0.3f, sprite: Sprites.Of("flare"));'''),
    ('''        Sparks.Spawn(b, Vector3.Zero, life * 0.6f, 0.7f * g, pal.Core * 0.5f, pal.Glow * 0.2f, 0.3f, sprite: Sprites.Of("flare"));''',
     '''        Sparks.Spawn(b, Vector3.Zero, life * 0.6f, (sun ? 0.4f : 0.7f) * g, sun ? Hdr("#ffb040", 1.2f) : pal.Core * 0.5f, pal.Glow * 0.2f, 0.3f, sprite: Sprites.Of("flare"));'''),
])

# ---------------------------------------------------------------- the Wild Hunt
edit(r"src\Fx\BattleFx.Skills.cs", [
    ('''    /// <summary>Frostfire Comet breaking: fire and frost in one blow, side by side.''',
     '''    /// <summary>The Wild Hunt: a spirit beast going up in the wild's green fire where it strikes.
    /// Tongues of it jet up and out, its embers climb, a puff of dark smoke, a small scorch. (The
    /// nature school's filmed burst under each read as a green ring, a dozen at once.)</summary>
    void HuntFire(Ev.Explosion e)
    {
        float r = Mathf.Max(0.9f, (float)e.Radius), g = Grow(e.Rank), gy = Y(e.X, e.Z);
        var ground = V(e.X, gy, e.Z);
        var fire = Hdr("#5cff2a", 1.25f);
        for (int i = 0; i < 9; i++)
        {
            float a = R() * Mathf.Tau;
            var dir = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
            MoonTongue(ground + dir * r * 0.25f * R() + Vector3.Up * 0.3f, dir * r * (0.6f + R()) + Vector3.Up * (1.6f + R() * 1.4f), (0.45f + R() * 0.25f) * g, fire);
        }
        for (int i = 0; i < 14; i++)
            Sparks.Spawn(ground + Vector3.Up * 0.5f, new Vector3((R() - 0.5f) * r * 3, 2 + R() * 3, (R() - 0.5f) * r * 3), 0.6f + R() * 0.5f, 0.05f + R() * 0.04f,
                Hdr("#b8ff6a", 1.6f), Hdr("#1a6a10", 0.6f), 0.01f, -1.2f, 1.5f);
        Smoke.Spawn(ground + Vector3.Up * 0.6f, Vector3.Up * 1.2f, 0.7f, r * 0.3f, new Color(0.08f, 0.12f, 0.05f), new Color(0.04f, 0.05f, 0.03f), r * 0.7f, drag: 1.4f, alpha: 0.45f);
        Flash(ground + Vector3.Up * 1.2f, new Color(0.5f, 1f, 0.35f), 4, 0.25f, r * 2.5f + 2);
        Scars.Add("scorch", ground, r * 0.35f, 2.5f, 0);
    }

    /// <summary>Frostfire Comet breaking: fire and frost in one blow, side by side.'''),
])
edit(r"src\Fx\BattleFx.cs", [
    ('''                case Ev.Explosion { Art: "frostfire" } e:
                    FrostfireBurst(e);
                    break;''',
     '''                case Ev.Explosion { Art: "frostfire" } e:
                    FrostfireBurst(e);
                    break;
                case Ev.Explosion { Art: "herd_hunt" } e:
                    HuntFire(e);
                    break;'''),
])

# ---------------------------------------------------------------- burning ground: fires in it, not round it
edit(r"src\Fx\BattleFx.Skills.cs", [
    ('''    readonly System.Collections.Generic.Dictionary<int, (MeshInstance3D Mesh, ShaderMaterial Mat)> firePatches = new();

    /// <summary>Ground left burning: low tongues of flame standing round its edge and lapping in
    /// (the rise's wall in small, shaders/fire_wall.gdshader), so it burns over a packed crowd's
    /// feet where its embers on the ground are hidden. (A firepot's burst alone was a soft orange
    /// blob.)</summary>
    void FirePatch(int id, Vector3 ground, float r, float strength)
    {
        if (!firePatches.TryGetValue(id, out var patch))
        {
            var mat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/fire_wall.gdshader") };
            mat.SetShaderParameter("seed", R() * 100);
            mat.SetShaderParameter("segs", 48f);
            mat.SetShaderParameter("cells", Mathf.Max(6, Mathf.Round(Mathf.Tau * r * 0.8f / 0.42f)));
            var mesh = new MeshInstance3D
            {
                Mesh = Kept("firecards48", () => FireCards(48)), MaterialOverride = mat, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off,
                CustomAabb = new Aabb(new Vector3(-1.5f, -0.5f, -1.5f), new Vector3(3, 2, 3)),
            };
            AddChild(mesh);
            firePatches[id] = patch = (mesh, mat);
        }
        patch.Mesh.Position = ground - Vector3.Up * 0.05f;
        patch.Mesh.Scale = new Vector3(r * 0.8f, 0.75f + 0.1f * r, r * 0.8f);
        patch.Mat.SetShaderParameter("burn", strength);
    }''',
     '''    readonly System.Collections.Generic.Dictionary<int, System.Collections.Generic.List<(MeshInstance3D Mesh, ShaderMaterial Mat, Vector2 Off, float Size)>> firePatches = new();

    /// <summary>Ground left burning: fires standing here and there in it, each a knot of low tongues
    /// (the rise's wall in small, shaders/fire_wall.gdshader), so it burns over a packed crowd's
    /// feet where its embers on the ground are hidden. (Its tongues stood all round its edge, a ring
    /// of fire: two grounds at once read as orange hoops. A firepot's burst alone was a soft orange
    /// blob.)</summary>
    void FirePatch(int id, Vector3 ground, float r, float strength)
    {
        if (!firePatches.TryGetValue(id, out var fires))
        {
            fires = new();
            int n = Math.Clamp((int)Mathf.Round(r * 1.6f), 2, 6);
            float a0 = R() * Mathf.Tau;
            for (int i = 0; i < n; i++)
            {
                var mat = new ShaderMaterial { Shader = GD.Load<Shader>("res://shaders/fire_wall.gdshader") };
                mat.SetShaderParameter("seed", R() * 100);
                mat.SetShaderParameter("segs", 12f);
                mat.SetShaderParameter("cells", 4f);
                var mesh = new MeshInstance3D
                {
                    Mesh = Kept("firecards12", () => FireCards(12)), MaterialOverride = mat, CastShadow = GeometryInstance3D.ShadowCastingSetting.Off,
                    CustomAabb = new Aabb(new Vector3(-1.5f, -0.5f, -1.5f), new Vector3(3, 2, 3)),
                };
                AddChild(mesh);
                // Spread through it, none at its very edge; one near its middle.
                float a = a0 + (i + (R() - 0.5f) * 0.7f) / n * Mathf.Tau, d = i == 0 ? r * 0.1f * R() : r * (0.3f + R() * 0.4f);
                fires.Add((mesh, mat, new Vector2(Mathf.Cos(a) * d, Mathf.Sin(a) * d), 0.26f + R() * 0.16f));
            }
            firePatches[id] = fires;
        }
        foreach (var f in fires)
        {
            double x = ground.X + f.Off.X, z = ground.Z + f.Off.Y;
            f.Mesh.Position = V(x, Y(x, z) - 0.05, z);
            f.Mesh.Scale = new Vector3(f.Size, 0.55f + f.Size * 0.8f, f.Size);
            f.Mat.SetShaderParameter("burn", strength);
        }
    }'''),
    ('''            foreach (var (id, patch) in firePatches)
                if (!alive.Contains(id)) { patch.Mesh.QueueFree(); out1.Add(id); }''',
     '''            foreach (var (id, fires) in firePatches)
                if (!alive.Contains(id)) { foreach (var f in fires) f.Mesh.QueueFree(); out1.Add(id); }'''),
])

# ---------------------------------------------------------------- the way out
edit(r"src\Fx\BattleFx.Story.cs", [
    ('''///   the way out   where a won night lets her go: a band of cold light lying on the ground,
///                 breathing (a pulsing cream decal with a hard edge read as a hoop);''',
     '''///   the way out   where a won night lets her go: the night thinning there, a pool of cold light
///                 lying soft on the ground with a faint veil of it standing and motes drifting up
///                 through it (a pulsing cream decal read as a hoop, and so did a soft band);'''),
    ('''    /// <summary>The way out's band of light, drawn in loot's batch as loot's light is (EndLoot).</summary>''',
     '''    /// <summary>The way out's light, drawn in loot's batch as loot's light is (EndLoot).</summary>'''),
    ('''        if (way > 0) Light(wayAt.X, wayAt.Y, wayAt.Z, Lit.Band, 0, wayReach, wayReach * 0.86f, WayCold, way * 0.5f);''',
     '''        if (way > 0) Light(wayAt.X, wayAt.Y, wayAt.Z, Lit.Band, 0, wayReach, wayReach * 1.5f, WayCold, way * 0.5f);'''),
])
edit(r"shaders\loot_beam.gdshader", [
    ('''//   8 Band: a band of light lying on the ground at its reach (the way out), breathing.''',
     '''//   8 Way: the way out, the night thinning where it lies: a pool of cold light soft on the ground,
//     a faint veil standing up off it, motes drifting up through it, breathing.'''),
    ('''	float down = half_w * 0.85;
	if (kind > 7.5) tall = down;''',
     '''	float down = half_w * 0.85;'''),
    ('''		// A band of light lying on the ground at its reach, soft on both sides, breathing; a faint
		// light within it. (A decal's band with a hard edge read as a cream hoop.)
		vec2 e = vec2(x / half_w, y / (half_w * 0.83));
		float r = length(e);
		float breath = 0.72 + 0.28 * sin(TIME * 2.2 + seed * 6.28);
		float band = exp(-pow((r - 0.92) / 0.075, 2.0)) * breath;
		float within = smoothstep(1.0, 0.2, r) * 0.1;
		light = mix(tint, deep, 0.35) * band + deep * within;
		veil = band * 0.05;''',
     '''		// The way out: the night thinning where what ruled it fell. A pool of cold light lying soft
		// on the ground, a faint veil of it standing up off the ground, and motes drifting slowly up
		// through it, all breathing. (A decal's band with a hard edge read as a cream hoop, and a
		// soft band of light round her as a pale-blue one.)
		vec2 e = vec2(x / half_w, y / (half_w * 0.83));
		float breath = 0.78 + 0.22 * sin(TIME * 1.7 + seed * 6.28);
		float lie = exp(-dot(e, e) * 1.7);
		float lift = max(y, 0.0) / H;
		float stand = g(x, half_w * 0.38) * smoothstep(-0.3 * half_w, 0.1 * half_w, y) * exp(-lift * 2.6);
		float up = (motes_of(half_w * 1.1, 0.45, 0.32, 0.035) + motes_of(half_w * 0.7, 0.3, 0.5, 0.03))
			* smoothstep(-0.2, 0.3, y) * (1.0 - smoothstep(0.35, 1.0, lift));
		light = deep * lie * 0.26 * breath + mix(tint, deep, 0.4) * stand * 0.2 * breath + tint * up * 1.3;
		veil = lie * 0.05 + stand * 0.04;'''),
])
