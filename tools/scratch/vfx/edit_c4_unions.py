from ed import edit
# The unions' own arts.
edit(r"logic\Content\Weapons.cs", [
    ("""            Art = "star", BossDamage = 1.6,""", """            Art = "frostfire", BossDamage = 1.6,"""),
    ("""            Art = "zone_plague", BossDamage = 2.4,""", """            Art = "zone_rot", BossDamage = 2.4,"""),
])
# A slow that is not the cold (a thicket's, a rot's) is drawn as no frost.
edit(r"logic\Sim\Entities.cs", [
    ("""    /// <summary>The last blow was a tick of something in it (a burn, a poison): drawn as no blow.</summary>
    public bool LastDot;""",
     """    /// <summary>The last blow was a tick of something in it (a burn, a poison): drawn as no blow.</summary>
    public bool LastDot;
    /// <summary>Until when (Battle.Time) a ground that is not the cold holds it slowed: its chill is
    /// drawn as no frost (a thicket's hold read as rime).</summary>
    public double HeldUntil;"""),
])
edit(r"logic\Sim\Battle.cs", [
    ("""                c.Stacks = Math.Max(c.Stacks, (1 - z.Slow) * 8);
            }""",
     """                c.Stacks = Math.Max(c.Stacks, (1 - z.Slow) * 8);
                if (z.School != School.Frost) e.HeldUntil = Time + z.Tick + 0.1;
            }"""),
])
edit(r"src\Actors\CrowdView.cs", [
    ("""        float frozen = e.Status.Has(StatusKind.Frozen) ? 1 : e.Status[StatusKind.Chill] is { } chill ? (float)Math.Min(0.5, chill.Stacks * 0.09) : 0;""",
     """        // (Held by a ground that is not the cold, a thicket's or a rot's: its slow is no rime.)
        bool held = battle != null && e.HeldUntil > battle.Time;
        float frozen = e.Status.Has(StatusKind.Frozen) ? 1 : !held && e.Status[StatusKind.Chill] is { } chill ? (float)Math.Min(0.5, chill.Stacks * 0.09) : 0;"""),
])
edit(r"src\Fx\BattleFx.cs", [
    ("""                case Ev.Explosion { Art: "firepot" } e:
                    PotBurst(e);
                    break;""",
     """                case Ev.Explosion { Art: "firepot" } e:
                    PotBurst(e);
                    break;
                case Ev.Explosion { Art: "frostfire" } e:
                    FrostfireBurst(e);
                    break;"""),
])
edit(r"src\Fx\BattleFx.Skills.cs", [
    # The cast.
    ("""            case "cinder" or "living_flame" or "star":
                // A puff of flame at the hand, orange (white-tinted, it was a cream ball at her side).""",
     """            case "cinder" or "living_flame" or "star" or "frostfire":
                // A puff of flame at the hand, orange (white-tinted, it was a cream ball at her side)."""),
    # The flight.
    ("""            case "cinder" or "living_flame" or "star":
            {
                // A burning coal: flame streaming off it, embers shed behind, a little smoke.
                bool star = art == "star", small = art == "living_flame";
                float s = (star ? 1.25f : small ? 0.55f : 0.85f) * g;
                // Its heart yellow-hot, not white: past the tone curve's knee a coal read as a cream pill.
                Shade(at, s * 2.2f, 0.5f);
                orbs.Add(new Transform3D(Godot.Basis.Identity.Scaled(Vector3.One * s * 0.3f), at), star ? Hdr("#ffd890", 2.0f) : Hdr("#ffa840", 1.7f));
                orbs.Add(new Transform3D(Godot.Basis.Identity.Scaled(Vector3.One * s * 1.5f), at), Hdr("#ff5a10", 1.6f) * 0.2f);
                Body(at, s * 0.75f, "ember_coal", star ? Hdr("#ffb060", 1.6f) : Hdr("#ff7a28", 1.5f), (float)now * 5 + p.Id);
                // Its flame streaming back, short and deep orange (long and bright, the coal read as
                // a pale beam behind it).
                Ribbons.Feed(key, at, 0.5f * s, star ? 0.3f : 0.18f, Hdr("#ff6a1a", 1f), 1.5f, Ribbons.Style.Flame);
                if (p.Weapon == "frostfire_comet") Ribbons.Feed(key ^ 0x55aa, at + Vector3.Up * 0.05f, 0.35f * s, 0.35f, Hdr("#a8dcff", 1f), 2f, Ribbons.Style.Frost);""",
     """            case "cinder" or "living_flame" or "star" or "frostfire":
            {
                // A burning coal: flame streaming off it, embers shed behind, a little smoke.
                // Frostfire Comet: a heart of ice in the fire, a tail of frost beside the flame, and
                // frost glinting off it with the embers. (Drawn as Fallen Star's, it had no cold in it
                // at all: a cream streak.)
                bool ice = art == "frostfire", star = art == "star" || ice, small = art == "living_flame";
                float s = (star ? 1.25f : small ? 0.55f : 0.85f) * g;
                // Its heart yellow-hot, not white: past the tone curve's knee a coal read as a cream pill.
                Shade(at, s * 2.2f, 0.5f);
                orbs.Add(new Transform3D(Godot.Basis.Identity.Scaled(Vector3.One * s * 0.3f), at), ice ? Hdr("#9fd4ff", 1.6f) : star ? Hdr("#ffd890", 2.0f) : Hdr("#ffa840", 1.7f));
                orbs.Add(new Transform3D(Godot.Basis.Identity.Scaled(Vector3.One * s * 1.5f), at), Hdr("#ff5a10", 1.6f) * (ice ? 0.14f : 0.2f));
                Body(at, s * 0.75f, "ember_coal", star ? Hdr("#ffb060", 1.6f) : Hdr("#ff7a28", 1.5f), (float)now * 5 + p.Id);
                if (ice) Body(at + Vector3.Up * 0.05f, s * 0.6f, "frost_star", Hdr("#8ac8ff", 1.5f), -(float)now * 4 + p.Id);
                // Its flame streaming back, short and deep orange (long and bright, the coal read as
                // a pale beam behind it).
                Ribbons.Feed(key, at, 0.5f * s, star ? 0.3f : 0.18f, Hdr("#ff6a1a", 1f), 1.5f, Ribbons.Style.Flame);
                // Its frost beside the flame, a deep cold blue (pale, the two summed to cream).
                if (ice) Ribbons.Feed(key ^ 0x55aa, at + Vector3.Up * 0.05f, 0.3f * s, 0.32f, Hdr("#3d8cff", 1f), 1.6f, Ribbons.Style.Frost);"""),
    ("""                    if (R() < 0.35f) Books.Spawn("fire_loop", at + new Vector3((R() - 0.5f) * 0.1f, 0, (R() - 0.5f) * 0.1f), 0.5f * s, 0.22f, new Color(1.35f, 0.78f, 0.36f, 0.85f), sizeEnd: 0.15f * s, v: Vector3.Up * 0.8f);
                    Sparks.Spawn(at, -fwd * (0.5f + R()) + new Vector3((R() - 0.5f) * 1.2f, 0.6f + R(), (R() - 0.5f) * 1.2f), 0.4f + R() * 0.3f, 0.04f + R() * 0.03f, Ember, EmberDeep, 0.01f, -1.2f, 1.5f);""",
     """                    if (R() < 0.35f) Books.Spawn("fire_loop", at + new Vector3((R() - 0.5f) * 0.1f, 0, (R() - 0.5f) * 0.1f), 0.5f * s, 0.22f, new Color(1.35f, 0.78f, 0.36f, 0.85f), sizeEnd: 0.15f * s, v: Vector3.Up * 0.8f);
                    if (ice && R() < 0.5f)
                        Sparks.Spawn(at, -fwd * (0.4f + R() * 0.8f) + new Vector3((R() - 0.5f) * 1.0f, 0.3f + R() * 0.6f, (R() - 0.5f) * 1.0f), 0.45f + R() * 0.3f, 0.09f + R() * 0.06f, Hdr("#a8dcff", 1.5f), IceDeep * 0.5f, 0.02f, 0.5f, 1.5f, sprite: Sprites.Of("frost_star"), spinV: 4);
                    else Sparks.Spawn(at, -fwd * (0.5f + R()) + new Vector3((R() - 0.5f) * 1.2f, 0.6f + R(), (R() - 0.5f) * 1.2f), 0.4f + R() * 0.3f, 0.04f + R() * 0.03f, Ember, EmberDeep, 0.01f, -1.2f, 1.5f);"""),
    # Butcher's Wheel: the cleavers read as steel, their wake as blood.
    ("""                float turn = (float)(now * 16 + p.Id), sz = 1.3f * Mathf.Sqrt(g);""",
     """                bool butcher = art == "axe_blood";
                float turn = (float)(now * 16 + p.Id), sz = (butcher ? 1.6f : 1.3f) * Mathf.Sqrt(g);"""),
    ("""                SpinArcs(at, 0.42f * sz, turn, 0.09f * sz, art == "axe_blood" ? Hdr("#ff5040", 1f) : art == "axe_storm" ? Hdr("#bfe0ff", 1f) : Hdr("#ffe6c8", 1f), 2f);""",
     """                // (Steel even on the butcher's wheel: arcs in blood red made the four heads one red ring.)
                SpinArcs(at, 0.42f * sz, turn, 0.09f * sz, art == "axe_storm" ? Hdr("#bfe0ff", 1f) : Hdr("#ffe6c8", 1f), butcher ? 2.4f : 2f);"""),
    ("""                else Ribbons.Feed(key, at, 0.4f * g, 0.16f, art == "axe_blood" ? Hdr("#ff3a2a", 1f) : Hdr("#fff0e0", 1f), art == "axe_blood" ? 1.8f : 1.3f, Ribbons.Style.Steel);
                if (art == "axe_blood" && R() < 0.25f) Sparks.Spawn(at, Vector3.Up * 0.5f, 0.5f, 0.06f, Blood, BloodDim, 0.02f, 9);""",
     """                else Ribbons.Feed(key, at, 0.4f * g, butcher ? 0.12f : 0.16f, butcher ? Hdr("#a8140c", 1f) : Hdr("#fff0e0", 1f), butcher ? 1.2f : 1.3f, Ribbons.Style.Steel);
                // The butcher's cleavers fling blood off their edges as they turn.
                if (butcher && R() < 0.5f)
                {
                    var outward = new Vector3(at.X - (float)p.X, 0, at.Z - (float)p.Z);
                    Sparks.Spawn(at, (outward.LengthSquared() > 0.01f ? outward.Normalized() : Vector3.Right) * (2 + R() * 2) + Vector3.Up * (1 + R()), 0.5f, 0.06f + R() * 0.04f, Blood, BloodDim, 0.02f, 9);
                }"""),
    # Rotwood's ground: thorns of rotten wood standing in the blight.
    ("""        "zone_thorn" or "zone_bloom" or "zone_root" => (Hdr("#4ec85a", 1.3f), Inside.Roots, 0.03f),""",
     """        "zone_thorn" or "zone_bloom" or "zone_root" => (Hdr("#4ec85a", 1.3f), Inside.Roots, 0.03f),
        // Rotwood: the blight grown thorns, its thicket rotten wood in a stain of rot.
        "zone_rot" => (Hdr("#a8c84a", 1.3f), Inside.Roots, 0.03f),
        // Frostfire Comet's: fire in its cracks inside a rim of frost.
        "frostfire_ground" => (Hdr("#8ad0ff", 1.5f), Inside.Embers, 0.2f),"""),
    ("""            var fill = Ground(z.X, z.Z, r, fillTex, edgeCol, 1e6f, 1.0f);""",
     """            var fill = Ground(z.X, z.Z, r, fillTex, FillOf(z.Art, edgeCol), 1e6f, 1.0f);"""),
    ("""            if (inside == Inside.Roots)
            {
                float stand = (float)Math.Max(0.6, z.Life - z.Age);
                Erupt(z.X, z.Z, 0, r * 0.95f, 14 + (int)(r * 7), SpikeKind.Thorn, 1.05f, stand, Hdr("#3fae4a", 1f));
                Erupt(z.X, z.Z, r * 0.7f, r * 1.0f, 8 + (int)(r * 3), SpikeKind.Thorn, 0.7f, stand, Hdr("#5ac85a", 1f));""",
     """            if (inside == Inside.Roots)
            {
                float stand = (float)Math.Max(0.6, z.Life - z.Age);
                bool rot = z.Art == "zone_rot";
                Erupt(z.X, z.Z, 0, r * 0.95f, 14 + (int)(r * 7), SpikeKind.Thorn, 1.05f, stand, rot ? Hdr("#6a7a2a", 1f) : Hdr("#3fae4a", 1f));
                Erupt(z.X, z.Z, r * 0.7f, r * 1.0f, 8 + (int)(r * 3), SpikeKind.Thorn, 0.7f, stand, rot ? Hdr("#8a9a3a", 1f) : Hdr("#5ac85a", 1f));
                if (rot) Scars.Add("blight", V(z.X, Y(z.X, z.Z), z.Z), r * 1.05f, stand + 0.6f, 0);"""),
    ("""        g.Fill.Decal.Modulate = Dim(edgeCol,""", """        g.Fill.Decal.Modulate = Dim(FillOf(z.Art, edgeCol),"""),
    ("""    readonly System.Collections.Generic.Dictionary<int, (Mark Edge, Mark Fill)> grounds = new();""",
     """    readonly System.Collections.Generic.Dictionary<int, (Mark Edge, Mark Fill)> grounds = new();

    /// <summary>The colour inside a ground: its edge's, but for frostfire's burning inside its frost.</summary>
    static Color FillOf(string art, Color edge) => art == "frostfire_ground" ? Hdr("#ff8a2a", 1.6f) : edge;"""),
    # Frostfire's burst.
    ("""    void GroundsGone(System.Collections.Generic.HashSet<int> alive)
    {""",
     """    /// <summary>Frostfire Comet breaking: fire and frost in one blow, side by side. Its burst half
    /// flame and half frost (the school's fireball alone, six metres across, swallowed her when it
    /// broke at her side), ice standing up round its rim, embers and frost thrown together, a scorch
    /// and a rime left.</summary>
    void FrostfireBurst(Ev.Explosion e)
    {
        float r = Mathf.Max(1.2f, (float)e.Radius), gy = Y(e.X, e.Z);
        var ground = V(e.X, gy, e.Z);
        Cam?.AddTrauma((float)Math.Min(0.3, 0.08 + e.Power * 0.1));
        float a = R() * Mathf.Tau;
        var side = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a)) * r * 0.22f;
        Sparks.Spawn(ground + Vector3.Up * 0.8f, Vector3.Zero, 0.08f, r * 0.3f, new Color(1.5f, 1.25f, 1.1f), new Color(0.6f, 0.5f, 0.7f), r * 0.6f, alpha: 0.7f);
        Books.Spawn("fire_blast", ground + Vector3.Up * 0.5f - side, r * 0.4f, 0.5f, new Color(1.25f, 0.55f, 0.18f, 1), flat: true, sizeEnd: r * 0.95f);
        Books.Spawn("frost_burst", ground + Vector3.Up * 0.55f + side, r * 0.42f, 0.6f, new Color(0.5f, 0.75f, 1.15f, 1), flat: true, sizeEnd: r * 1.0f);
        Erupt(e.X, e.Z, r * 0.35f, r * 0.85f, 7 + (int)(r * 2), SpikeKind.Ice, 0.75f, 1.3f, IceDeep);
        for (int i = 0; i < 26; i++)
        {
            float b = R() * Mathf.Tau, v = r * (1.6f + R() * 3);
            var dir = new Vector3(Mathf.Cos(b) * v, 2.5f + R() * 4, Mathf.Sin(b) * v);
            if (i % 2 == 0) Sparks.Spawn(ground + Vector3.Up * 0.5f, dir, 0.5f + R() * 0.5f, 0.05f + R() * 0.04f, new Color(2.4f, 1.1f, 0.28f), new Color(1.2f, 0.2f, 0.03f), 0.02f, 10, 1.3f);
            else Sparks.Spawn(ground + Vector3.Up * 0.5f, dir * 0.8f, 0.55f + R() * 0.4f, 0.08f + R() * 0.05f, Hdr("#a8dcff", 1.5f), IceDeep * 0.4f, 0.02f, 8, 1.6f, sprite: Sprites.Of("frost_star"), spinV: 6);
        }
        for (int i = 0; i < 3; i++)
            Smoke.Spawn(ground + new Vector3((R() - 0.5f) * r * 0.5f, 0.5f, (R() - 0.5f) * r * 0.5f), new Vector3(0, 0.9f + R() * 0.5f, 0), 0.9f, r * 0.3f, new Color(0.62f, 0.7f, 0.82f), new Color(0.4f, 0.45f, 0.55f), r * 0.7f, drag: 1.4f, alpha: 0.28f);
        Waves.Add(ground + Vector3.Up * 0.35f, r * 1.5f, 0.32f, Hdr("#8ad0ff", 1.4f), 1);
        Flash(ground + Vector3.Up * 1.4f, new Color("#ffb070"), 7, 0.3f, r * 2.2f + 3);
        Scars.Add("scorch", ground - side, r * 0.5f, 9);
        Scars.Add("frost", ground + side, r * 0.5f, 6);
    }

    void GroundsGone(System.Collections.Generic.HashSet<int> alive)
    {"""),
])
