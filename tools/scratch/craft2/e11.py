from ed import sub
sub('src/Ui/ItemModels.cs', [
("""        ["antidote"] = new(() => Flask("#2a7a1e", 0.12f, 1), new(Pitch: 0.15f, Turn: 0.2f, Tilt: 0.1f)),""",
"""        ["antidote"] = new(() => Flask("#2a7a1e", 0.12f, 1), new(Pitch: 0.15f, Turn: 0.2f, Tilt: 0.1f)),
        // Wenna's moonpetal draught: silver, faintly lit, in the same round bottle as the red.
        ["moon_draught"] = new(() => Flask("#aebfe0", 0.55f, 0), new(Pitch: 0.15f, Turn: -0.2f, Tilt: 0.12f)),
        ["flask"] = new(PewterFlask, new(Pitch: 0.2f, Turn: 0.55f, Tilt: -0.15f)),""",),
("""        ["moon"] = new(() => Amulet("moon"), new(Turn: 0.3f)),""",
"""        ["moon"] = new(() => Amulet("moon"), new(Turn: 0.3f)),
        ["fur_braid"] = new(FurBraid, new(Pitch: 0.25f, Turn: 0.25f)),"""),
("""    /// <summary>A hide pegged out flat the way a trapper stretches it:""",
"""    /// <summary>Maeca's braid: three strands of what the Pack shed, grey and grey and white, plaited
    /// into a loop to hang at the throat, and the end bitten off short in a tuft where it is tied.</summary>
    static Node3D FurBraid()
    {
        var root = new Node3D();
        Vector3 E(float t) => new(0.36f * Mathf.Sin(t * Mathf.Tau), 0.24f + 0.48f * Mathf.Cos(t * Mathf.Tau), 0);
        string[] tones = ["#8e8880", "#6c6660", "#ddd6ca"];
        const int Crossings = 15;
        for (int s = 0; s < 3; s++)
        {
            float phase = s * Mathf.Tau / 3;
            // Each strand winds round the loop's line, a third of a turn behind the last: a plait.
            var path = Path(260, t =>
            {
                var p = E(t);
                var T = (E(t + 0.002f) - E(t - 0.002f)).Normalized();
                var N = Vector3.Back.Cross(T);
                float a = t * Crossings * Mathf.Tau + phase;
                return p + N * (0.03f * Mathf.Cos(a)) + Vector3.Back * (0.022f * Mathf.Sin(a * 2) * 0.8f);
            }, true);
            var strand = new Build();
            Tube(strand, path, k => 0.026f + 0.004f * Mathf.Sin(k * 97f), 7, true);
            var (alb, nor) = Fur(new Color(tones[s]), new Color(tones[s]).Darkened(0.45f), 2.2f);
            Add(root, strand, new StandardMaterial3D { AlbedoTexture = alb, NormalEnabled = true, NormalTexture = nor, Roughness = 0.95f, Uv1Scale = new Vector3(6, 1, 1) }, tangents: true);
        }
        // The knot at the bottom, wrapped in sinew, and the bitten-off tuft below it.
        var knot = new Build();
        foreach (float y in new[] { -0.215f, -0.245f, -0.275f })
            Tube(knot, Circle(new Vector3(0, y, 0), 0.05f, Vector3.Right, Vector3.Back, 18), 0.011f, 5, true);
        Add(root, knot, Mat("#b8a27a", 0, 0.8f));
        var tuft = new Build();
        var rng = new Random(7);
        for (int k = 0; k < 22; k++)
        {
            float a = k * 2.39996f, r = 0.012f + 0.03f * (float)rng.NextDouble(), len = 0.08f + 0.06f * (float)rng.NextDouble();
            var from = new Vector3(Mathf.Cos(a) * 0.02f, -0.28f, Mathf.Sin(a) * 0.02f);
            var to = from + new Vector3(Mathf.Cos(a) * r, -len, Mathf.Sin(a) * r);
            Tube(tuft, Path(4, t => from.Lerp(to, t)), t => 0.009f * (1 - 0.7f * t), 5);
        }
        Add(root, tuft, Mat("#a8a29a", 0, 0.95f));
        return root;
    }

    /// <summary>Wenna's flask: pewter, flat to sit against the hip, a lid that fits, dented a little.</summary>
    static Node3D PewterFlask()
    {
        var root = new Node3D();
        var body = new Build();
        Lathe(body, Pts(0, -0.5f, 0.3f, -0.5f, 0.38f, -0.44f, 0.4f, -0.3f, 0.4f, 0.2f, 0.36f, 0.32f, 0.2f, 0.42f, 0.11f, 0.46f, 0.11f, 0.52f), 40,
            warp: p => new Vector3(p.X, p.Y, p.Z * 0.42f + (p.Z > 0 ? 0.012f * Mathf.Sin(p.Y * 9 + 1) : 0)));
        var pewter = Mat("#8f9497", 0.85f, 0.42f);
        Add(root, body, pewter);
        var lid = new Build();
        Lathe(lid, Pts(0, 0.5f, 0.125f, 0.5f, 0.13f, 0.53f, 0.13f, 0.62f, 0.115f, 0.65f, 0, 0.66f), 24);
        Add(root, lid, Mat("#a4a9ac", 0.9f, 0.32f));
        // A strap of leather round the waist, stitched.
        var strap = new Build();
        Tube(strap, Path(48, t => new Vector3(0.405f * Mathf.Sin(t * Mathf.Tau), -0.1f, 0.405f * 0.42f * Mathf.Cos(t * Mathf.Tau)), true), 0.03f, 4, true);
        Add(root, strap.Faceted(), Mat("#5a3a22", 0, 0.85f));
        return root;
    }

    /// <summary>A hide pegged out flat the way a trapper stretches it:"""),
])
