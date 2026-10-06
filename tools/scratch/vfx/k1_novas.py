from ed import edit
OLD_FROST = '''            case "nova_frost":
            {
                var f = Palette.Of(School.Frost);
                var ice = Hdr("#9fe0ff", 1f);
                AddFront(ground, r, 0.45f, 0.5f * g, ice, 2.2f, Ribbons.Style.Frost);
                if (rings > 1) AddFront(ground, r * 0.7f, 0.55f, 0.3f, ice, 1.4f, Ribbons.Style.Frost);
                // No filmed burst: the front, the ice and the cold it rolls out are the blow
                // (the burst, however faint, washed the whole crowd blue-white).
                Waves.Add(ground + Vector3.Up * 0.3f, r * 1.2f, 0.4f, f.Glow, 0.8f);
                // Ice flung low over the ground, and the cold rolling out after it.
                int n = Math.Min(40, (int)(14 * g + r * 3));
                for (int i = 0; i < n; i++)
                {
                    float a = R() * Mathf.Tau, v = r * (1.6f + R() * 1.4f);
                    var dir = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
                    Sparks.Spawn(ground + Vector3.Up * 0.4f + dir * 0.4f, dir * v + Vector3.Up * (0.5f + R() * 1.5f), 0.4f + R() * 0.25f, 0.07f + R() * 0.07f, f.Core, f.Glow * 0.4f, 0.02f, 8, 2.5f, sprite: Sprites.Of("star"), spinV: 9);
                }
                // The cold rolling out low behind the front: thin, so it never hides the crowd.
                for (int i = 0; i < 7; i++)
                {
                    float a = i / 7f * Mathf.Tau + R() * 0.5f;
                    var dir = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
                    Smoke.Spawn(ground + Vector3.Up * 0.2f + dir * r * 0.35f, dir * r * 1.3f + Vector3.Up * 0.1f, 0.7f, r * 0.16f, new Color(0.62f, 0.8f, 1f), new Color(0.45f, 0.62f, 0.9f), r * 0.4f, drag: 2.4f, alpha: 0.12f);
                }
                // The front leaves ice standing in it: a ring of crystal points, leaning out, gone in a second.
                Erupt(e.X, e.Z, r * 0.35f, r * 0.95f, 14 + rings * 5, SpikeKind.Ice, 1.0f * g, 0.95f, IceDeep);
                // Rime left on the ground, briefly (held for seconds it was a carpet of white).
                Scars.Add("frost", ground, r * 0.7f, 1.2f, 0);
                Flash(ground + Vector3.Up * 1.2f, f.Light, 6, 0.35f, r * 2.5f);
                return true;
            }'''
NEW_FROST = '''            case "nova_frost" or "nova_ward" or "nova_zero":
            {
                // The breath of cold drawn by what it does as it passes, never as a line: ice thrusting
                // up out of the ground in a wave racing out from her, frost flung low, the cold itself
                // rolling after in a thin bank. (Its front drawn as a ribbon round its reach read as a
                // hoop: two of them, pale, round Winter Ward and Absolute Zero.)
                bool ward = art == "nova_ward", zero = art == "nova_zero";
                var f = Palette.Of(School.Frost);
                float wave = (float)Math.Clamp(e.Duration, 0.25, 0.6);
                // Absolute Zero's is black ice, standing taller, thicker and longer: what it reaches freezes solid.
                var ice = zero ? Hdr("#1c4aa8", 1.0f) : IceDeep;
                Erupt(e.X, e.Z, r * 0.3f, r * 1.0f, (zero ? 30 : 16) + rings * 5, SpikeKind.Ice, (zero ? 1.45f : 0.95f) * g, zero ? 1.8f : 0.95f, ice, wave);
                if (rings > 1) Erupt(e.X, e.Z, r * 0.2f, r * 0.65f, 8, SpikeKind.Ice, 0.7f * g, 0.9f, ice, wave * 0.9f);
                Waves.Add(ground + Vector3.Up * 0.3f, r * 1.1f, 0.4f, f.Glow, 0.5f);
                // Frost flung low over the ground, glinting.
                int n = Math.Min(40, (int)(14 * g + r * 3));
                for (int i = 0; i < n; i++)
                {
                    float a = R() * Mathf.Tau, v = r * (1.6f + R() * 1.4f);
                    var dir = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
                    Sparks.Spawn(ground + Vector3.Up * 0.4f + dir * 0.4f, dir * v + Vector3.Up * (0.5f + R() * 1.5f), 0.4f + R() * 0.25f, 0.07f + R() * 0.07f, f.Core, f.Glow * 0.4f, 0.02f, 8, 2.5f, sprite: Sprites.Of("star"), spinV: 9);
                }
                // The cold rolling out low with its ice, broken into drifts so no edge of it is a line;
                // Absolute Zero's heavier, sinking and spreading.
                int banks = zero ? 14 : 10;
                for (int i = 0; i < banks; i++)
                {
                    float a = (i + R() * 0.7f) / banks * Mathf.Tau;
                    var dir = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
                    Smoke.Spawn(ground + Vector3.Up * 0.25f + dir * r * (0.25f + R() * 0.15f), dir * (r / wave) * (0.45f + R() * 0.2f) + Vector3.Up * (zero ? -0.05f : 0.08f),
                        zero ? 1.5f : 0.9f, r * 0.13f, new Color(0.6f, 0.78f, 1f), new Color(0.4f, 0.55f, 0.85f), r * (zero ? 0.42f : 0.32f), drag: 2.0f, alpha: zero ? 0.17f : 0.12f);
                }
                // Rime left on the ground, briefly (held for seconds it was a carpet of white).
                Scars.Add("frost", ground, r * (zero ? 0.7f : 0.5f), zero ? 2.2f : 0.9f, 0);
                if (zero)
                {
                    // The ground under it frozen hard and split, and the blow felt.
                    Scars.Add("crack", ground, r * 0.5f, 2.6f, 0);
                    Cam?.AddTrauma(0.1f);
                }
                if (ward) WardRime(e.X, e.Z, g);
                Flash(ground + Vector3.Up * 1.2f, f.Light, zero ? 7 : 5, 0.35f, r * 2.2f);
                return true;
            }'''
OLD_REAVE = '''            case "nova_blood" or "nova_rend" or "nova_harrow":
            {
                // The arc is swept round at the edge of its reach, twice, crimson in shadow.
                var at = ground + Vector3.Up * 1.0f;
                var glow = art == "nova_harrow" ? Hdr("#9a5cff", 2.4f) : Hdr("#c4142a", 2.4f);
                float facing = R() * Mathf.Tau;
                // A scythe swept all the way round at the edge of its reach: the blade's
                // crescent (Blades), crimson, with a darker one inside it a breath behind.
                var hue = art == "nova_harrow" ? Hdr("#8a4aff", 1.1f) : Hdr("#e01a2a", 1.1f);
                // Swept most of the way round, never closed: a full turn of its hot edge read as a hoop.
                Blades.Add(at, facing, r, Mathf.Tau * 0.82f, false, 0.16f, 0.24f, hue, 0.3f * Mathf.Min(g, 1.3f));
                Blades.Add(at + Vector3.Down * 0.1f, facing + Mathf.Pi, r * 0.8f, Mathf.Tau * 0.62f, false, 0.18f, 0.2f, hue * 0.55f, 0.3f, 0.04f);
                if (rings > 1) Blades.Add(at, facing + Mathf.Pi / 2, r * 0.6f, Mathf.Tau * 0.7f, true, 0.16f, 0.2f, hue * 0.7f, 0.35f, 0.08f);
                AddFront(ground, r, 0.3f, 0.3f * g, new Color(glow.R / 3, glow.G / 3, glow.B / 3), 1.8f, Ribbons.Style.Wisp, 0.6f);
                // What it takes, drawn back in to the survivor.
                int n = Math.Min(30, (int)(12 * g));
                for (int i = 0; i < n; i++)
                {
                    float a = R() * Mathf.Tau, d = r * (0.75f + R() * 0.3f);
                    var from = ground + new Vector3(Mathf.Cos(a) * d, 0.8f + R() * 0.6f, Mathf.Sin(a) * d);
                    Sparks.Spawn(from, (at - from) * (1.6f + R() * 0.6f), 0.55f, 0.09f + R() * 0.05f, art == "nova_harrow" ? Palette.Of(School.Shadow).Core : Blood, BloodDim, 0.03f, 0, 0.5f);
                }
                for (int i = 0; i < 6; i++)
                    Smoke.Spawn(ground + new Vector3((R() - 0.5f) * r, 0.5f, (R() - 0.5f) * r), Vector3.Up * 0.4f, 0.8f, r * 0.25f, new Color(0.25f, 0.06f, 0.1f), new Color(0.1f, 0.02f, 0.05f), r * 0.5f, drag: 1.5f, alpha: 0.4f);
                Flash(at, glow, 5, 0.3f, r * 2);
                return true;
            }'''
NEW_REAVE = '''            case "nova_blood" or "nova_rend" or "nova_harrow":
            {
                // A scythe seen to travel: the graveblade's head crossing most of a turn round her in
                // about a third of a second, a short smear behind it, its edge burning in its own hue.
                // (Swept at once with a wake three-quarters of the turn long and a white-hot edge, the
                // whole arc stood at the reach together and read as a hoop.)
                bool rend = art == "nova_rend", harrow = art == "nova_harrow";
                var at = ground + Vector3.Up * 1.0f;
                float facing = R() * Mathf.Tau, span = Mathf.Tau * 0.92f;
                bool turn = R() < 0.5f;
                float sweep = (float)Math.Clamp(e.Duration * 1.1, 0.24, 0.4);
                // Rend and Mend in fresh blood; the Harrowing in the grave's violet-black.
                var hue = harrow ? Hdr("#5a2ccc", 1.0f) : Hdr("#cc1028", 1.0f);
                float depth = 0.24f * Mathf.Min(g, 1.3f);
                Blades.Add(at, facing, r, span, turn, sweep, 0.14f, hue, depth, 0, tail: 0.2f, white: harrow ? 0.4f : 0.3f);
                // The evolutions cut twice: a darker blade inside the first, half a beat behind it.
                if (rend || harrow) Blades.Add(at + Vector3.Down * 0.12f, facing, r * 0.8f, span, turn, sweep * 1.08f, 0.12f, hue * 0.5f, depth * 0.7f, 0.05f, tail: 0.16f, white: 0.15f);
                if (rings > 1) Blades.Add(at, facing + Mathf.Pi, r * 0.62f, span * 0.8f, !turn, sweep * 0.9f, 0.12f, hue * 0.6f, depth * 0.8f, 0.08f, tail: 0.2f, white: 0.25f);
                // What the edge throws as it passes, along its way and in time with it.
                const int Steps = 10;
                for (int i = 0; i < Steps; i++)
                {
                    float h = (i + 0.5f) / Steps;
                    float when = sweep * (1 - Mathf.Pow(1 - h, 1 / 2.2f));
                    var dir = SwingAt(facing, turn, span, h);
                    var tan = (SwingAt(facing, turn, span, h + 0.02f) - dir).Normalized();
                    var cut = ground + dir * r * 0.88f + Vector3.Up * 0.9f;
                    pending.Add((time + when, () => Reaped(cut, tan, dir, g, harrow)));
                }
                // What it takes, drawn back in to her once the blade has passed: drops for the arc,
                // and for Rend and Mend threads of blood drunk in from all round and a pulse in her.
                var pull = harrow ? Palette.Of(School.Shadow).Core : Blood;
                pending.Add((time + sweep * 0.6f, () =>
                {
                    int n = Math.Min(30, (int)((rend ? 18 : 12) * g));
                    for (int i = 0; i < n; i++)
                    {
                        float a = R() * Mathf.Tau, d = r * (0.7f + R() * 0.3f);
                        var from = ground + new Vector3(Mathf.Cos(a) * d, 0.8f + R() * 0.6f, Mathf.Sin(a) * d);
                        Sparks.Spawn(from, (at - from) * (1.7f + R() * 0.5f), 0.5f, 0.09f + R() * 0.05f, pull, BloodDim, 0.03f, 0, 0.4f);
                    }
                    if (rend) Drink(ground, at, r, g);
                }));
                if (harrow) GraveStirs(ground, r, sweep);
                for (int i = 0; i < 5; i++)
                    Smoke.Spawn(ground + new Vector3((R() - 0.5f) * r, 0.5f, (R() - 0.5f) * r), Vector3.Up * 0.4f, 0.8f, r * 0.25f, harrow ? new Color(0.12f, 0.06f, 0.2f) : new Color(0.25f, 0.06f, 0.1f), new Color(0.06f, 0.02f, 0.08f), r * 0.5f, drag: 1.5f, alpha: 0.4f);
                Flash(at, harrow ? Hdr("#7a4cff", 1.6f) : Hdr("#c4142a", 1.6f), 4, 0.3f, r * 2);
                return true;
            }'''
edit(r"src\Fx\BattleFx.Skills.cs", [
    (OLD_FROST, NEW_FROST),
    (OLD_REAVE, NEW_REAVE),
    ('''    /// <summary>A ring of spikes round (x, z) between radii r0 and r1, leaning out.</summary>
    void Erupt(double x, double z, float r0, float r1, int n, SpikeKind kind, float height, float life, Color color)
    {''',
     '''    /// <summary>A ring of spikes round (x, z) between radii r0 and r1, leaning out (by `lean`
    /// radians and a little more, when given). With a `wave` each waits for a front racing out
    /// from the middle to reach it, `wave` seconds to the outer radius.</summary>
    void Erupt(double x, double z, float r0, float r1, int n, SpikeKind kind, float height, float life, Color color, float wave = 0, float lean = -1)
    {'''),
    ('''            float lean = (kind == SpikeKind.Stone ? 0.5f : 0.35f) + R() * 0.35f;''',
     '''            float tilt = lean >= 0 ? lean + R() * 0.15f : (kind == SpikeKind.Stone ? 0.5f : 0.35f) + R() * 0.35f;'''),
    ('''            var turn = new Godot.Basis(axis, -lean) * new Godot.Basis(Vector3.Up, R() * Mathf.Tau);''',
     '''            var turn = new Godot.Basis(axis, -tilt) * new Godot.Basis(Vector3.Up, R() * Mathf.Tau);'''),
    ('''                Life = life * (0.85f + R() * 0.3f), Kind = kind, Color = color, Age = -R() * 0.06f,''',
     '''                Life = life * (0.85f + R() * 0.3f), Kind = kind, Color = color, Age = -R() * 0.06f - wave * d / Mathf.Max(0.01f, r1),'''),
])
