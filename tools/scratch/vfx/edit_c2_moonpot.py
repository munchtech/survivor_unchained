from ed import edit
edit(r"src\Fx\BattleFx.Skills.cs", [
    # The hit: the brand stamped crisp on a dark bed, moonfire in jets; the stardust small and deep.
    ("""            "moon" or "moon_brand" => ("moon_burst", new Color(0.22f, 0.17f, 0.8f, 0.5f)),""",
     """            "moon" or "moon_brand" => ("moon_burst", new Color(0.16f, 0.12f, 0.75f, 0.32f)),"""),
    ("""                // The brand: the crescent stamped on what it struck, flaring and gone, and moonfire
                // licking up off it.
                var fire = MoonFire(art);
                Sparks.Spawn(at + Vector3.Up * 0.25f, Vector3.Up * 0.35f, 0.5f, 0.55f * g, Hdr("#9a8cff", 1.1f), new Color(fire.R * 0.3f, fire.G * 0.3f, fire.B * 0.3f), 0.95f * g, sprite: Sprites.Range("crescent").First + 1, spinV: 0.6f);
                for (int i = 0; i < 9; i++)
                    MoonTongue(at + new Vector3((R() - 0.5f) * 0.6f, (R() - 0.5f) * 0.4f, (R() - 0.5f) * 0.6f), Vector3.Up * (0.8f + R() * 1.2f) + away * R() * 0.6f, (0.38f + R() * 0.18f) * g, fire);
                break;""",
     """                // The brand: the crescent stamped on what it struck, cold silver on a dark bed,
                // flaring and gone, and moonfire licking up off it in violet tongues. (Pale violet
                // over the tan dead, with smoke-soft flames and a stardust haze, it read as a lavender
                // puff.)
                var fire = MoonFire(art);
                Smoke.Spawn(at + Vector3.Up * 0.2f, Vector3.Zero, 0.45f, 0.7f * g, new Color(0.03f, 0.02f, 0.07f), null, 1.0f * g, alpha: 0.55f, sprite: -1);
                Sparks.Spawn(new Sparks.P
                {
                    At = at + Vector3.Up * 0.3f, V = Vector3.Up * 0.3f, Life = 0.42f, Size = 0.5f * g, SizeEnd = 0.8f * g, Color = MoonSilver * 1.3f, ColorEnd = new Color(fire.R * 0.25f, fire.G * 0.25f, fire.B * 0.4f),
                    Alpha = 1, Sprite = Sprites.Range("crescent").First + 1, Spin = (R() - 0.5f) * 0.6f + 0.001f, SpinV = 0.001f,
                });
                for (int i = 0; i < 7; i++)
                    MoonTongue(at + new Vector3((R() - 0.5f) * 0.5f, (R() - 0.5f) * 0.3f, (R() - 0.5f) * 0.5f), Vector3.Up * (1.0f + R() * 1.2f) + away * R() * 0.5f, (0.34f + R() * 0.16f) * g, fire);
                break;"""),
    # The cast: a glint of the crescent at her hand, cold silver, not a lavender sigil.
    ("""            case "mote" or "mote_cascade" or "mote_star" or "moon" or "moon_brand":
                // A spell spoken: a turning glyph of light at the hand, in the spell's
                // colour (white, it read as a blob at her feet).
                Sparks.Spawn(hand + Vector3.Up * 0.1f, Vector3.Zero, 0.24f, 0.6f * g, (art.StartsWith("moon") ? Moon * 0.5f : art == "mote_cascade" ? FenLight * 0.45f : Hdr("#c070ff", 1.3f)), pal.Glow * 0.1f, 0.75f * g, sprite: Sprites.Of("magic"), spinV: 6);
                break;""",
     """            case "moon" or "moon_brand":
                // The moon drawn from her hand: a glint of its crescent, cold silver, gone in a breath.
                // (A turning sigil in moonlight's lilac, every cast, read as a lavender blot at her side.)
                Sparks.Spawn(new Sparks.P
                {
                    At = hand + Vector3.Up * 0.1f, Life = 0.2f, Size = 0.32f * g, SizeEnd = 0.5f * g, Color = MoonSilver * 1.2f, ColorEnd = MoonFire(art) * 0.3f,
                    Alpha = 1, Sprite = Sprites.Range("crescent").First + 1, Spin = (float)e.Angle + 0.001f, SpinV = 0.001f,
                });
                break;
            case "mote" or "mote_cascade" or "mote_star":
                // A spell spoken: a turning glyph of light at the hand, in the spell's
                // colour (white, it read as a blob at her feet).
                Sparks.Spawn(hand + Vector3.Up * 0.1f, Vector3.Zero, 0.24f, 0.6f * g, art == "mote_cascade" ? FenLight * 0.45f : Hdr("#c070ff", 1.3f), pal.Glow * 0.1f, 0.75f * g, sprite: Sprites.Of("magic"), spinV: 6);
                break;"""),
    # In flight: less violet haze round it (over the pale dead it was lilac).
    ("""                orbs.Add(new Transform3D(Godot.Basis.Identity.Scaled(Vector3.One * s * 1.9f), at), fire * 0.28f);""",
     """                orbs.Add(new Transform3D(Godot.Basis.Identity.Scaled(Vector3.One * s * 1.5f), at), fire * 0.16f);"""),
    # Moonlight is cold silver-blue, and moonfire a deep violet: never the two mixed to lilac.
    ("""    static Color MoonFire(string art) => art == "moon_brand" ? Hdr("#9050ff", 1.5f) : Hdr("#6a64ff", 1.5f);

    static readonly Color MoonSilver = Hdr("#c4c0ff", 1.2f);""",
     """    static Color MoonFire(string art) => art == "moon_brand" ? Hdr("#7a3cff", 1.5f) : Hdr("#5a50ff", 1.5f);

    /// <summary>Moonlight: cold silver-blue. (Silver-lilac read as lavender.)</summary>
    static readonly Color MoonSilver = Hdr("#d2deff", 1.2f);"""),
    # Moonfire's tongues: crisp jets, not the pack's smoke-soft flames (those read as lilac smoke).
    ("""            Alpha = 1, Drag = 2.5f, Sprite = Sprites.Range("flame").First + 1 + (int)(R() * 3), Spin = (R() - 0.5f) * 0.5f + 0.001f, SpinV = 0.001f,""",
     """            Alpha = 1, Drag = 2.5f, Sprite = Sprites.Range("muzzle").First + 1 + (int)(R() * 4.99f), Spin = (R() - 0.5f) * 0.5f + 0.001f, SpinV = 0.001f,"""),
])
