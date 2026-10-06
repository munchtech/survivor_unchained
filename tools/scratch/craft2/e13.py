from ed import sub
sub('src/Audio/Sfx.cs', [
("""    public static void Discovery()
    {""",
"""    /* ------------------------------------------------------------ crafts --- */

    /// <summary>The hammer on the anvil: a count of blows for a temper (Brannoc tempers without a
    /// word, counting), one heavy blow for the rest, each ringing off into the smithy.</summary>
    public static void Anvil(int blows = 1)
    {
        if (A is not { } a) return;
        bool rec = Recordings.Pick("anvil") != null;
        for (int i = 0; i < blows; i++)
        {
            double t = Now + i * 0.26;
            if (rec) a.Play(new Clip { Of = "anvil", T = t, G = 0.42, Pitch = R(0.97, 1.03) - i * 0.015, Verb = 0.3, Bus = Bus.Ui });
            a.Play(new Clip { Of = "impactMetal_heavy", T = t, G = 0.16, Pitch = R(0.85, 0.95), Verb = 0.25, Bus = Bus.Ui });
            a.Play(new Fm { T = t, F = 1320 * R(0.98, 1.02), Ratio = 2.76, Index = 1.4, D = 1.1, G = 0.025, Verb = 0.6, Bus = Bus.Ui });
        }
    }

    /// <summary>A coal shut in its cage: a struck bell, and a hiss as the ember settles.</summary>
    public static void Cage()
    {
        if (A is not { } a) return;
        a.Play(new Clip { Of = "impactBell_heavy", G = 0.22, Pitch = R(0.8, 0.88), Verb = 0.5, Bus = Bus.Ui });
        a.Play(new Hiss { T = Now + 0.08, D = 0.9, G = 0.07, Bp = 3200, Bp2 = 900, Q = 1.2, Verb = 0.3, Bus = Bus.Ui });
        a.Play(new Fm { T = Now + 0.05, F = 660, Ratio = 3.01, Index = 0.8, D = 1.8, G = 0.03, Verb = 0.8, Bus = Bus.Ui });
    }

    /// <summary>A draught poured off the still: glass set down, a pour, a cork.</summary>
    public static void Pour()
    {
        if (A is not { } a) return;
        a.Play(new Clip { Of = "impactGlass_light", G = 0.22, Pitch = R(1.05, 1.15), Bus = Bus.Ui });
        a.Play(new Hiss { T = Now + 0.06, D = 0.5, G = 0.06, Bp = 1400, Bp2 = 700, Q = 3, Bus = Bus.Ui });
        for (int i = 0; i < 5; i++) a.Play(new Tone { T = Now + 0.1 + i * 0.07 + R(0, 0.03), F = R(500, 900), F2 = R(900, 1400), D = 0.05, G = 0.02, Bus = Bus.Ui });
        a.Play(new Clip { Of = "impactWood_medium", T = Now + 0.55, G = 0.12, Pitch = R(1.6, 1.8), Bus = Bus.Ui });
    }

    public static void Discovery()
    {"""),
])
