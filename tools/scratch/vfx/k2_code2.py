from ed import edit

# ---------------------------------------------------------------- the wild's and the arcane's bursts, unfilmed
edit(r"src\Fx\BattleFx.cs", [
    ('''            Books.Spawn(BlastOf(school), ground + Vector3.Up * 0.55f, r * 1.1f, life * 0.8f, lt, flat: true, sizeEnd: r * 2.1f);
            for (int i = 0; i < 6; i++)''',
     '''            if (!Unfilmed(school, ground, r * 0.8f, life * 0.8f)) Books.Spawn(BlastOf(school), ground + Vector3.Up * 0.55f, r * 1.1f, life * 0.8f, lt, flat: true, sizeEnd: r * 2.1f);
            for (int i = 0; i < 6; i++)'''),
    ('''        if (On('b')) Books.Spawn(BlastOf(school), ground + Vector3.Up * 0.55f, r * 1.2f, life, tint, flat: true, sizeEnd: r * 2.4f);''',
     '''        if (On('b') && !Unfilmed(school, ground, r, life)) Books.Spawn(BlastOf(school), ground + Vector3.Up * 0.55f, r * 1.2f, life, tint, flat: true, sizeEnd: r * 2.4f);'''),
    ('''    /// <summary>A strike from the sky arriving: a thin hot pillar, its''',
     '''    /// <summary>The bursts of the schools whose filmed ones were rings: the wild's was a set of green
    /// rings and the arcane's a pink ring with rays (a champion falling to the Wild Hunt or under a
    /// moon left one, a dozen at once). Drawn instead as what each throws: the wild's green fire
    /// jetting up and its spores; the arcane's star of light and motes that hang and wink out. False
    /// for the schools whose film is kept.</summary>
    bool Unfilmed(School school, Vector3 ground, float r, float life)
    {
        if (school == School.Nature)
        {
            var fire = Hdr("#4cff3a", 1.1f);
            int jets = 4 + (int)Mathf.Min(6, r * 2);
            for (int i = 0; i < jets; i++)
            {
                float a = R() * Mathf.Tau;
                var dir = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
                MoonTongue(ground + dir * r * 0.3f * R() + Vector3.Up * 0.3f, dir * r * (0.5f + R()) + Vector3.Up * (1.4f + R() * 1.2f), (0.3f + R() * 0.2f) * Mathf.Max(1, r * 0.6f), fire);
            }
            for (int i = 0; i < 10 + (int)(r * 4); i++)
                Sparks.Spawn(ground + Vector3.Up * 0.5f, new Vector3((R() - 0.5f) * r * 3, 1.5f + R() * 2.5f, (R() - 0.5f) * r * 3), life + R() * 0.5f, 0.05f + R() * 0.04f,
                    Hdr("#b8ff6a", 1.5f), Hdr("#1a6a10", 0.6f), 0.01f, -0.8f, 1.8f);
            Smoke.Spawn(ground + Vector3.Up * 0.5f, Vector3.Up * 0.9f, 0.6f, r * 0.3f, new Color(0.07f, 0.11f, 0.05f), new Color(0.03f, 0.05f, 0.02f), r * 0.7f, drag: 1.4f, alpha: 0.4f);
            return true;
        }
        if (school == School.Arcane)
        {
            var pal = Palette.Of(School.Arcane);
            Sparks.Spawn(ground + Vector3.Up * 0.8f, Vector3.Zero, 0.12f, r * 0.45f, Hdr("#c890ff", 1.3f), Hdr("#4a1aa0", 0.4f), r * 0.75f, sprite: Sprites.Range("star").First + 1, spinV: 0);
            for (int i = 0; i < 10 + (int)(r * 4); i++)
            {
                float a = R() * Mathf.Tau, v = r * (1.2f + R() * 2);
                Sparks.Spawn(ground + Vector3.Up * 0.6f, new Vector3(Mathf.Cos(a) * v, 1 + R() * 2, Mathf.Sin(a) * v), life + R() * 0.4f, 0.06f + R() * 0.05f, pal.Core, pal.Glow * 0.6f, 0.01f, -0.3f, 3.5f,
                    sprite: R() < 0.4f ? Sprites.Of("star") : 0, spinV: 5);
            }
            Smoke.Spawn(ground + Vector3.Up * 0.5f, Vector3.Up * 0.5f, 0.6f, r * 0.35f, new Color(0.08f, 0.04f, 0.14f), new Color(0.03f, 0.02f, 0.06f), r * 0.8f, drag: 1.4f, alpha: 0.45f);
            return true;
        }
        return false;
    }

    /// <summary>A strike from the sky arriving: a thin hot pillar, its'''),
])

# ---------------------------------------------------------------- Dawn's Judgement: its own shields of morning
edit(r"logic\Content\Weapons.cs", [
    ('''            Art = "disc_reckon", BossDamage = 2.2,
            Description = "Two shields of morning that ricochet through the crowd, and break into light wherever they strike.",''',
     '''            Art = "disc_dawn", BossDamage = 2.2,
            Description = "Two shields of morning that ricochet through the crowd, and break into light wherever they strike.",'''),
])
# A weapon's burst tells the view whose it is (only a look: Dawn's Judgement breaking into light).
edit(r"logic\Sim\Battle.cs", [
    ('''                Events.Emit(new Ev.Nova { X = x, Z = z, Radius = fx.Radius, School = fx.School, Duration = 0.3 });''',
     '''                Events.Emit(new Ev.Nova { X = x, Z = z, Radius = fx.Radius, School = fx.School, Duration = 0.3, Art = ctx.Weapon?.Art });'''),
])
S = r"src\Fx\BattleFx.Skills.cs"
edit(S, [
    ('''            case "disc" or "disc_aegis" or "disc_reckon":
                if (e.Crit) Books.Spawn("gold_flare",''',
     '''            case "disc" or "disc_aegis" or "disc_reckon" or "disc_dawn":
                if (e.Crit) Books.Spawn("gold_flare",'''),
    ('''            case "dagger" or "dagger_blood" or "dagger_flurry" or "disc" or "disc_aegis" or "disc_reckon" or "chakram"''',
     '''            case "dagger" or "dagger_blood" or "dagger_flurry" or "disc" or "disc_aegis" or "disc_reckon" or "disc_dawn" or "chakram"'''),
    ('''            case "disc" or "disc_aegis" or "disc_reckon":
            {
                float s = 1.1f * Mathf.Sqrt(g) * (art == "disc_reckon" ? 1.15f : 1);
                bool aegis = art == "disc_aegis";''',
     '''            case "disc" or "disc_aegis" or "disc_reckon" or "disc_dawn":
            {
                float s = 1.1f * Mathf.Sqrt(g) * (art is "disc_reckon" or "disc_dawn" ? 1.15f : 1);
                bool aegis = art == "disc_aegis", dawn = art == "disc_dawn";'''),
    ('''                Body(at, 1.05f * s, aegis ? "ward_disc" : "sun_disc", gold * (0.6f * off), spin * 1.3f);''',
     '''                // Dawn's Judgement is a shield of morning: the dawn's own sigil, a sun rising, turning
                // slowly (Reckoning's sawblade, borrowed whole, made it Reckoning).
                if (dawn) Body(at, 1.1f * s, "dawn_sigil", Hdr("#ffb45a", 0.8f) * (0.65f * off), spin * 0.4f);
                else Body(at, 1.05f * s, aegis ? "ward_disc" : "sun_disc", gold * (0.6f * off), spin * 1.3f);'''),
    # Its break into light: rays, never a ball.
    ('''            case "nova_holy" or "nova_dawn" or "nova_sun":
            {''',
     '''            case "disc_dawn":
            {
                // Dawn's Judgement breaking into light where it strikes: a star of light at the blow and
                // short rays of dawn thrown out low along the ground from it, gold motes going up. (The
                // holy school's filmed burst under each read as a soft gold blob, a dozen at once.)
                float g2 = Mathf.Min(g, 1.3f);
                var gold = Hdr("#ffb84a", 1f);
                var heart = ground + Vector3.Up * 0.7f;
                Sparks.Spawn(heart, Vector3.Zero, 0.14f, 0.9f * g2, Hdr("#ffd890", 1.2f), Hdr("#ff9a30", 0.4f), 1.3f * g2, sprite: Sprites.Range("star").First + 3 + 1, spinV: 0);
                int n = 7;
                float a0 = R() * Mathf.Tau;
                for (int i = 0; i < n; i++)
                {
                    float a = a0 + (i + (R() - 0.5f) * 0.5f) / n * Mathf.Tau, len = r * (0.45f + R() * 0.35f);
                    var dir = new Vector3(Mathf.Cos(a), 0, Mathf.Sin(a));
                    var from = ground + Vector3.Up * 0.35f + dir * 0.25f;
                    Ribbons.Line(new[] { from, from + dir * len * 0.5f, from + dir * len }, 0.11f * g2, 0.2f, gold, 1.9f, Ribbons.Style.Glow, new[] { 0.2f, 1f, 0f });
                }
                for (int i = 0; i < 6; i++)
                    Sparks.Spawn(heart + new Vector3((R() - 0.5f) * 0.6f, 0, (R() - 0.5f) * 0.6f), Vector3.Up * (1 + R() * 1.2f), 0.6f + R() * 0.3f, 0.06f, Palette.Of(School.Holy).Core, Palette.Of(School.Holy).Glow, 0.02f, -0.4f, 1.5f,
                        sprite: R() < 0.4f ? Sprites.Of("star") : 0, spinV: 3);
                Flash(heart + Vector3.Up * 0.6f, Palette.Of(School.Holy).Light, 3, 0.2f, r * 2.5f);
                return true;
            }
            case "nova_holy" or "nova_dawn" or "nova_sun":
            {'''),
])
edit(r"src\Audio\Sfx.Skills.cs", [
    ('''            case "disc" or "disc_aegis" or "disc_reckon":
                if (!a.Gate("cast:disc", 2, 200)) return;''',
     '''            case "disc" or "disc_aegis" or "disc_reckon" or "disc_dawn":
                if (!a.Gate("cast:disc", 2, 200)) return;'''),
    ('''            case "disc" or "disc_aegis" or "disc_reckon" when a.Gate("hit:disc", 2, 120):''',
     '''            case "disc" or "disc_aegis" or "disc_reckon" or "disc_dawn" when a.Gate("hit:disc", 2, 120):'''),
])

# ---------------------------------------------------------------- the way out's motes, a little larger
edit(r"shaders\loot_beam.gdshader", [
    ('''		float up = (motes_of(half_w * 1.1, 0.45, 0.32, 0.035) + motes_of(half_w * 0.7, 0.3, 0.5, 0.03))''',
     '''		float up = (motes_of(half_w * 1.1, 0.45, 0.32, 0.055) + motes_of(half_w * 0.7, 0.3, 0.5, 0.045))'''),
])
