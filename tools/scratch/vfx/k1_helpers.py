from ed import edit
ANCHOR = '''    /* ------------------------------------------------------ from the sky -- */'''
HELPERS = '''    /// <summary>Which way a swing's blade lies from its middle when it has come `head` of the way
    /// round (Blades' own geometry), as a unit direction on the ground.</summary>
    static Vector3 SwingAt(float facing, bool mirror, float span, float head)
    {
        float a = (head - 0.5f) * span;
        var p = new Godot.Basis(Vector3.Up, facing) * new Vector3(Mathf.Sin(a), 0, Mathf.Cos(a));
        if (mirror) p.X = -p.X;
        return p;
    }

    /// <summary>What the graveblade throws where its edge is passing: blood flung on along its way;
    /// for the Harrowing, the grave's dark torn up behind it and pale motes with it.</summary>
    void Reaped(Vector3 cut, Vector3 tan, Vector3 outward, float g, bool harrow)
    {
        if (harrow)
        {
            Smoke.Spawn(cut + Vector3.Down * 0.6f, Vector3.Up * (0.9f + R() * 0.6f) + tan * 0.6f, 0.9f + R() * 0.4f, 0.35f * g, new Color(0.14f, 0.08f, 0.24f), new Color(0.04f, 0.02f, 0.07f), 0.9f * g, drag: 1.4f, alpha: 0.5f);
            for (int i = 0; i < 3; i++)
                Sparks.Spawn(cut + new Vector3((R() - 0.5f) * 0.5f, -0.4f, (R() - 0.5f) * 0.5f), tan * (1.5f + R() * 2) + Vector3.Up * (0.6f + R()), 0.5f + R() * 0.3f, 0.07f,
                    Hdr("#a88cff", 1.4f), Hdr("#3a1a7a", 0.6f), 0.02f, -0.5f, 1.5f);
            return;
        }
        for (int i = 0; i < 5; i++)
            Sparks.Spawn(cut + new Vector3((R() - 0.5f) * 0.3f, (R() - 0.5f) * 0.4f, (R() - 0.5f) * 0.3f), tan * (4 + R() * 4) + outward * (1 + R() * 1.5f) + Vector3.Up * (1 + R() * 1.5f),
                0.35f + R() * 0.25f, 0.05f + R() * 0.05f, Blood, BloodDim, 0.02f, 9, 1.2f);
        if (R() < 0.5f) Sparks.Spawn(cut, tan * 3 + Vector3.Up, 0.4f, 0.16f * g, Blood * 0.8f, BloodDim, 0.1f * g, 9, 1, sprite: Sprites.Of("blood_drop"), spinV: 4);
    }

    /// <summary>Rend and Mend drinking: threads of blood drawn in to her from all round what it cut,
    /// and a dark-red pulse in her as they arrive. (Drops alone read as the arc's sparks.)</summary>
    void Drink(Vector3 ground, Vector3 at, float r, float g)
    {
        const int N = 9;
        float a0 = R() * Mathf.Tau;
        for (int i = 0; i < N; i++)
        {
            float a = a0 + (i + (R() - 0.5f) * 0.6f) / N * Mathf.Tau, d = r * (0.7f + R() * 0.25f);
            var from = ground + new Vector3(Mathf.Cos(a) * d, 0.7f + R() * 0.5f, Mathf.Sin(a) * d);
            var side = new Vector3(-Mathf.Sin(a), 0, Mathf.Cos(a)) * (R() - 0.5f) * r * 0.5f;
            var mid = from.Lerp(at, 0.5f) + side + Vector3.Up * (0.3f + R() * 0.4f);
            Ribbons.Line(new[] { from, mid, at + (from - at).Normalized() * 0.35f }, 0.07f * g, 0.3f + R() * 0.1f, Hdr("#b0101e", 1f), 1.5f, Ribbons.Style.Glow, new[] { 0.3f, 1f, 0.15f });
        }
        pending.Add((time + 0.22f, () => Sparks.Spawn(at, Vector3.Zero, 0.28f, 0.7f * g, Hdr("#ff2a3a", 1.2f), Hdr("#5a0610", 0.5f), 1.1f * g, sprite: Sprites.Of("flare"), spinV: 0)));
    }

    /// <summary>The Harrowing: the grave stirring where its blade has passed. Grave-dark hooks claw up
    /// out of the ground and sink, and pale souls rise slow out of it in the blade's wake.</summary>
    void GraveStirs(Vector3 ground, float r, float sweep)
    {
        for (int i = 0; i < 5; i++)
        {
            float a = R() * Mathf.Tau, d = r * (0.4f + R() * 0.5f);
            double x = ground.X + Mathf.Cos(a) * d, z = ground.Z + Mathf.Sin(a) * d;
            pending.Add((time + sweep * (0.4f + R() * 0.8f), () => Erupt(x, z, 0, 0.3f, 4, SpikeKind.Thorn, 0.55f, 0.7f, Hdr("#4a3a62", 1f))));
        }
        for (int i = 0; i < 12; i++)
        {
            float a = R() * Mathf.Tau, d = r * (0.35f + R() * 0.6f);
            var foot = ground + new Vector3(Mathf.Cos(a) * d, 0.15f, Mathf.Sin(a) * d);
            pending.Add((time + sweep * (0.3f + R() * 0.9f), () =>
                Sparks.Spawn(foot, Vector3.Up * (0.7f + R() * 0.5f), 0.9f + R() * 0.5f, 0.12f, Hdr("#c8b8ff", 1.3f), Hdr("#4a2a9a", 0.4f), 0.05f, -0.2f, 1.2f, sprite: Sprites.Of("wisp"), spinV: 1)));
        }
    }

    /// <summary>Winter Ward: the cold wrapping her in rime as it goes out. Crystals of ice grow up close
    /// round her and stand a moment, and frost glints as it climbs round her.</summary>
    void WardRime(double x, double z, float g)
    {
        Erupt(x, z, 0.5f, 0.8f, 9, SpikeKind.Ice, 0.8f * g, 1.3f, Hdr("#7cc4ff", 1.1f), 0.12f, 0.12f);
        var foot = V(x, Y(x, z), z);
        for (int i = 0; i < 16; i++)
        {
            float a = i / 16f * Mathf.Tau + R() * 0.3f;
            var rim = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
            Sparks.Spawn(foot + rim * 0.6f + Vector3.Up * (0.1f + R() * 0.3f), new Vector3(-rim.Z, 0, rim.X) * 1.6f + Vector3.Up * (1.0f + R() * 0.6f) - rim * 0.3f,
                0.9f + R() * 0.3f, 0.1f + R() * 0.05f, Hdr("#cfeeff", 1.5f), Hdr("#3d8cff", 0.6f), 0.03f, 0, 1.2f, sprite: Sprites.Of("frost_star"), spinV: 3);
        }
    }

''' + ANCHOR
edit(r"src\Fx\BattleFx.Skills.cs", [(ANCHOR, HELPERS)])
