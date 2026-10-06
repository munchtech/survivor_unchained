W = "C:/Users/munch/Desktop/survivorsunchained/.claude/worktrees/agent-a1d4562f44c7f6feb/godot/"
FILES = {
    W + "logic/Play/Zones/ArenaRun.cs": [
        ("""    // Dusk: the tier's strength (and an oath's levels) comes in over the first three minutes,
    // so a night is not lost before the ember has given anything to choose.
    int Level() => Math.Max(1, Spec.Tier * 3 - 2 + levels + (int)(Minute / 2.5) + (int)(Beyond / 2) - Math.Max(0, (int)Math.Ceiling((Spec.Tier >= 3 ? DuskT3 : 3) - Minute)));
    /// <summary>What an ordinary creature's health is divided by at a minute.</summary>
    public static double FodderEase(double minute) => 1 + 0.08 * minute;
    static double K(string n, double d) => double.TryParse(Environment.GetEnvironmentVariable(n), System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out var v) ? v : d;
    static readonly double EaseT3 = K("EASE_T3", 1), DmgT3 = K("DMG_T3", 0), DuskT3 = K("DUSK_T3", 3), ChampT3 = K("CHAMP_T3", 1);
    double EaseFor(double m) => Spec.Tier >= 3 ? 1 + 0.08 * m * EaseT3 : FodderEase(m);
""", """    // Dusk: the tier's strength (and an oath's levels) comes in over the first three minutes (five
    // from the third tier), so a night is not lost before the ember has given anything to choose.
    int Level() => Math.Max(1, Spec.Tier * 3 - 2 + levels + (int)(Minute / 2.5) + (int)(Beyond / 2) - Math.Max(0, (int)Math.Ceiling(DuskMinutes - Minute)));
    double DuskMinutes => Asks ? 5 : 3;
    /// <summary>What an ordinary creature's health is divided by at a minute.</summary>
    public static double FodderEase(double minute) => 1 + 0.08 * minute;

    /// <summary>From the third tier the night asks the draft. The experience lead's brief: there a
    /// careless draft should lose noticeably more often than a planned one, while below it choice is
    /// expression (a random drafter won as often as a greedy one at tiers 1-3, 85% to 83%). So from
    /// the third tier the crowd softens less with the minutes (it tests the build's reach), its blows
    /// grow from the eighth minute to twice by the half hour (a build that cannot clear is touched
    /// more), and champions, heralds and minibosses come a quarter stronger from the sixth (they test
    /// what it does to one). Dusk is longer there too, so the night is lost to the draft, not to the
    /// first minutes. Measured (docs/team/combat.md): planned 87%, careless 70%, from 93% and 87%.</summary>
    bool Asks => Spec.Tier >= 3;
    double EaseFor(double m) => Asks ? 1 + 0.08 * m * 0.4 : FodderEase(m);
"""),
        ("""        if (!champion && !e.Elite && Spec.Tier >= 3 && DmgT3 > 0) e.Damage *= 1 + DmgT3 * Math.Max(0, Math.Min(Minute, 30) - 8) / 22;
        if ((champion || e.Elite) && Spec.Tier >= 3 && ChampT3 != 1 && Minute >= 6) { e.MaxHp = e.Hp = e.MaxHp * ChampT3; e.Damage *= ChampT3; }""",
         """        if (Asks && !champion && !e.Elite) e.Damage *= 1 + Math.Clamp((Math.Min(Minute, 30) - 8) / 22, 0, 1);
        // (Not the boss: its contract sets its own health.)
        if (Asks && (champion || e.Elite) && e.Def.Id != BossDef && Minute >= 6) { e.MaxHp = e.Hp = e.MaxHp * 1.25; e.Damage *= 1.25; }"""),
    ],
}
