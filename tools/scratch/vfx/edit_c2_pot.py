from ed import edit
edit(r"src\Fx\BattleFx.cs", [
    ("""                case Ev.Explosion e:
                {
                    float gy = Y(e.X, e.Z), r = (float)e.Radius;""",
     """                case Ev.Explosion { Art: "firepot" } e:
                    PotBurst(e);
                    break;
                case Ev.Explosion e:
                {
                    float gy = Y(e.X, e.Z), r = (float)e.Radius;"""),
])
edit(r"src\Fx\BattleFx.Skills.cs", [
    ("""    void GroundsGone(System.Collections.Generic.HashSet<int> alive)
    {""",
     """    /// <summary>A firepot breaking: a pot of blasting ember, not a ball of fire. The crack of it
    /// (a yellow-hot instant), tongues of flame jetting out from where it broke and stopping short,
    /// its powder thrown out burning, the clay pot's sherds flung out dark and tumbling, char-black
    /// smoke punched up, the air thrown, its light, its scorch. (The school's filmed burst alone was a
    /// soft orange fireball; it is kept small, as the heart of it.)</summary>
    void PotBurst(Ev.Explosion e)
    {
        float r = Mathf.Max(1.2f, (float)e.Radius), gy = Y(e.X, e.Z);
        var ground = V(e.X, gy, e.Z);
        var cam = GetViewport()?.GetCamera3D();
        Vector3 right = cam?.GlobalTransform.Basis.X ?? Vector3.Right, up = cam?.GlobalTransform.Basis.Y ?? Vector3.Up;
        Cam?.AddTrauma((float)Math.Min(0.3, 0.08 + e.Power * 0.1));
        // The crack: yellow-hot, never white (a white instant over the pale dead read as a cream disc).
        Sparks.Spawn(ground + Vector3.Up * 0.6f, Vector3.Zero, 0.09f, r * 0.45f, new Color(2.1f, 1.15f, 0.3f), new Color(1.3f, 0.35f, 0.05f), r * 0.85f, alpha: 0.8f);
        // Its heart: the filmed burst, small, quick and deep orange.
        Books.Spawn("fire_blast", ground + Vector3.Up * 0.5f, r * 0.5f, 0.42f, new Color(1.25f, 0.55f, 0.18f, 1), flat: true, sizeEnd: r * 1.15f);
        // Tongues of flame jetting out from where it broke, each turned on the screen along its way.
        int jets = 9 + Math.Min(4, e.Rank / 2);
        float a0 = R() * Mathf.Tau;
        for (int i = 0; i < jets; i++)
        {
            float a = a0 + (i + (R() - 0.5f) * 0.6f) / jets * Mathf.Tau;
            var dir = new Vector3(Mathf.Cos(a), 0.12f, Mathf.Sin(a)).Normalized();
            float sx = dir.Dot(right), sy = dir.Dot(up);
            float hot = 0.85f + R() * 0.3f;
            Sparks.Spawn(new Sparks.P
            {
                At = ground + Vector3.Up * 0.35f + dir * 0.25f * r, V = dir * r * (2.6f + R() * 1.6f), Drag = 6, Life = 0.26f + R() * 0.12f,
                Size = r * (0.3f + R() * 0.12f), SizeEnd = r * (0.62f + R() * 0.2f), Color = new Color(2.0f, 0.92f, 0.26f) * hot, ColorEnd = new Color(0.7f, 0.12f, 0.02f),
                Alpha = 1, Sprite = Sprites.Range("muzzle").First + 1 + (int)(R() * 4.99f), Spin = Mathf.Atan2(-sx, sy) + 0.001f, SpinV = 0.001f,
            });
        }
        // The blasting ember thrown out burning: fast, falling, and some still alight on the ground.
        int n = 20 + (int)(r * 6);
        for (int i = 0; i < n; i++)
        {
            float a = R() * Mathf.Tau, v = r * (2 + R() * 3.5f);
            Sparks.Spawn(ground + Vector3.Up * 0.5f, new Vector3(Mathf.Cos(a) * v, 2.5f + R() * 4.5f, Mathf.Sin(a) * v), 0.5f + R() * 0.6f, 0.05f + R() * 0.05f,
                new Color(2.4f, 1.1f, 0.28f), new Color(1.2f, 0.2f, 0.03f), 0.02f, 11, 1.2f);
        }
        // The pot's sherds: dark fired clay, flung out and tumbling down.
        for (int i = 0; i < 9; i++)
        {
            float a = R() * Mathf.Tau, v = r * (1.4f + R() * 2.2f);
            Smoke.Spawn(ground + Vector3.Up * 0.45f, new Vector3(Mathf.Cos(a) * v, 3 + R() * 3.5f, Mathf.Sin(a) * v), 0.6f + R() * 0.3f, 0.08f + R() * 0.07f,
                new Color(0.2f, 0.09f, 0.05f), new Color(0.12f, 0.06f, 0.04f), -1, gravity: 16, sprite: Sprites.Of("dirt"), spinV: 9);
        }
        // Char-black smoke punched up out of it, soon gone (lingering, it hid the next fight).
        for (int i = 0; i < 4; i++)
            Smoke.Spawn(ground + new Vector3((R() - 0.5f) * r * 0.5f, 0.6f + R() * 0.4f, (R() - 0.5f) * r * 0.5f), new Vector3((R() - 0.5f) * 0.8f, 1.6f + R() * 0.8f, (R() - 0.5f) * 0.8f),
                0.75f + R() * 0.35f, r * 0.3f, new Color(0.1f, 0.08f, 0.07f), new Color(0.05f, 0.04f, 0.04f), r * 0.75f, drag: 1.4f, alpha: 0.55f);
        Waves.Add(ground + Vector3.Up * 0.35f, r * 1.6f, 0.3f, Palette.Of(School.Fire).Glow, 1);
        Flash(ground + Vector3.Up * 1.4f, Palette.Of(School.Fire).Light, 8, 0.28f, r * 2.4f + 3);
        Scars.Add("scorch", ground, r * 0.7f, 9);
    }

    void GroundsGone(System.Collections.Generic.HashSet<int> alive)
    {"""),
])
