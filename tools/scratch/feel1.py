R = r'C:\Users\munch\Desktop\survivorsunchained\.claude\worktrees\agent-ad1a039caf3923eec\godot\src'
def edit(name, pairs):
    p = R + '\\' + name
    s = open(p, encoding='utf-8').read()
    for old, new in pairs:
        assert old in s, (name, old[:90])
        s = s.replace(old, new, 1)
    open(p, 'w', encoding='utf-8', newline='').write(s)

edit(r'Ui\GameHud.cs', [
# fields
("""    // What matters off the screen; where the prompt's thing is on it; the arena's clock and its word.""",
"""    // The bar eased every frame toward its true value (docs/feel S-06): shown, wanted, the level's flash.
    float barShown, barWant, barFlash;
    bool barEmber = true;
    ColorRect barGlow = null!;
    double killPop;
    int killsShown;
    // What matters off the screen; where the prompt's thing is on it; the arena's clock and its word."""),
# glow overlay in BuildEmber after barTip
("""        barTip = new ColorRect { Color = Colors.White, Size = new Vector2(4, 10), Position = new Vector2(1, 1), MouseFilter = Control.MouseFilterEnum.Ignore };
        track.AddChild(barTip);""",
"""        barTip = new ColorRect { Color = Colors.White, Size = new Vector2(4, 10), Position = new Vector2(1, 1), MouseFilter = Control.MouseFilterEnum.Ignore };
        track.AddChild(barTip);
        // Near the level the whole bar breathes.
        barGlow = new ColorRect { Color = Style.EmberHi with { A = 0 }, Position = new Vector2(1, 1), Size = new Vector2(0, 10), MouseFilter = Control.MouseFilterEnum.Ignore };
        track.AddChild(barGlow);"""),
# Frame: set want instead of sizes
("""        float fw = (760 * K - 32) * e;
        (ember ? emberFill : growFill).Size = new Vector2(fw, 10);
        barTip.Position = new Vector2(Math.Max(1, fw - 3), 1);
        barTip.Color = (ember ? Style.EmberHi : Style.DayHi) with { A = 0.3f + 0.7f * Mathf.SmoothStep(0.6f, 1f, e) };
        barTip.Visible = e > 0.01f;""",
"""        // The fill is eased every frame (_Process); a new level fills it, flashes, and drains to what carried over.
        if (ember != barEmber) { barEmber = ember; barShown = e; }
        barWant = e;"""),
("""        if (lv != shownLevel || ember != shownEmber)
        {
            if (lv > shownLevel && ember == shownEmber) levelPop = 1;""",
"""        if (lv != shownLevel || ember != shownEmber)
        {
            if (lv > shownLevel && ember == shownEmber) { levelPop = 1; barShown = 1; barFlash = 1; }"""),
("""        tallyKills.Text = b.KillCount.ToString();""",
"""        tallyKills.Text = b.KillCount.ToString();
        // The count pops when it climbs, at most ten times a second.
        if (b.KillCount > killsShown && killPop <= 0.05) killPop = 0.15;
        killsShown = b.KillCount;"""),
# _Process: ease the bar
("""        // The prompt over the thing it is for, where the eye already is; at the bottom when that is off screen.""",
"""        // The bar flows toward its value; a level's flash fades over a tenth of a second.
        barShown = barShown > barWant + 0.5f ? Mathf.MoveToward(barShown, barWant, dt * 6) : barShown + (barWant - barShown) * (1 - Mathf.Exp(-18 * dt));
        float fw = (760 * K - 32) * Mathf.Clamp(barShown, 0, 1);
        (barEmber ? emberFill : growFill).Size = new Vector2(fw, 10);
        barFlash = Mathf.MoveToward(barFlash, 0, dt / 0.08f);
        (barEmber ? emberFill : growFill).Modulate = Colors.White.Lerp(new Color(3, 3, 3), barFlash);
        barTip.Position = new Vector2(Math.Max(1, fw - 3), 1);
        barTip.Color = (barEmber ? Style.EmberHi : Style.DayHi) with { A = 0.3f + 0.7f * Mathf.SmoothStep(0.6f, 1f, barShown) };
        barTip.Visible = barShown > 0.01f;
        float t2 = Time.GetTicksMsec() / 1000f;
        barGlow.Size = new Vector2(fw, 10);
        barGlow.Color = (barEmber ? Style.EmberHi : Style.DayHi) with { A = barShown >= 0.85f ? 0.25f + 0.25f * Mathf.Sin(t2 * 8) : 0 };
        killPop = Math.Max(0, killPop - delta);
        float kp = 1 + (float)(killPop / 0.15) * 0.15f;
        killsChip.PivotOffset = killsChip.Size / 2;
        killsChip.Scale = new Vector2(kp, kp);
        // The prompt over the thing it is for, where the eye already is; at the bottom when that is off screen."""),
# phase word colour
("""    /// <summary>In an arena: seconds until what rules it comes (negative: past it), and the word for it; null elsewhere.</summary>
    public void ArenaClock(double? left, string word)
    {
        arenaLeft = left;
        tallyWord.Text = left == null ? "" : word;
    }""",
"""    /// <summary>In an arena: seconds until what rules it comes (negative: past it), the night's phase and its colour; null elsewhere.</summary>
    public void ArenaClock(double? left, string word, Color? tone = null)
    {
        arenaLeft = left;
        // A new phase pops in (docs/feel S-21: escalation as a story).
        if (left != null && word != tallyWord.Text) { tallyWord.PivotOffset = new Vector2(200, 9); tallyWord.Scale = new Vector2(1.35f, 1.35f); }
        tallyWord.Text = left == null ? "" : word;
        tallyWord.AddThemeColorOverride("font_color", tone ?? Style.Ember);
    }"""),
("""        killPop = Math.Max(0, killPop - delta);""",
"""        killPop = Math.Max(0, killPop - delta);
        tallyWord.Scale = tallyWord.Scale.Lerp(Vector2.One, 1 - Mathf.Exp(-8 * dt));"""),
])

edit(r'Game\Game.cs', [
("""            if (zone is ArenaRun ar && Battle is { } cb2)
            {
                double left = ar.Spec.Minutes * 60 - cb2.Time;
                hud.ArenaClock(ar.Won ? -(cb2.Time - ar.Spec.Minutes * 60) : left > 0 ? left : 0, ar.Won ? "PAST THE HALF HOUR" : left > 0 ? "BEFORE WHAT RULES IT COMES" : "IT HAS COME");
            }""",
"""            if (zone is ArenaRun ar && Battle is { } cb2)
            {
                double end = ar.Spec.Minutes * 60, left = end - cb2.Time;
                var (phase, tone) = Phase(cb2.Time / end, ar.Won, left);
                hud.ArenaClock(ar.Won ? -(cb2.Time - end) : left > 0 ? left : 0, phase, tone);
            }"""),
("""    /// <summary>What matters and is off the screen: what rules the fight, the nearest elites, chests.</summary>""",
"""    /// <summary>The night's phases, named on the clock (docs/feel S-21), as shares of the arena's length.</summary>
    static (string, Color) Phase(double k, bool won, double left)
    {
        if (won) return ("BEYOND  ·  PAST WHAT RULED IT", new Color("#c8b0ff"));
        if (left <= 0) return ("IT HAS COME", Style.BloodHi);
        return k switch
        {
            < 1 / 6.0 => ("DUSK  ·  BEFORE WHAT RULES IT COMES", new Color("#e8b878")),
            < 1 / 3.0 => ("GLOAMING  ·  BEFORE WHAT RULES IT COMES", new Color("#ff9a50")),
            < 2 / 3.0 => ("THE WITCHING  ·  BEFORE WHAT RULES IT COMES", new Color("#ff7a3a")),
            < 28 / 30.0 => ("ASHFALL  ·  BEFORE WHAT RULES IT COMES", new Color("#ff5a3a")),
            _ => ("THE COMING", Style.BloodHi),
        };
    }

    /// <summary>What last brought the survivor down, and when (the arena's end tells it).</summary>
    public (string Name, double At)? LastFall { get; private set; }

    /// <summary>What matters and is off the screen: what rules the fight, the nearest elites, chests.</summary>"""),
("""    void OnDeath(string killer)
    {""",
"""    void OnDeath(string killer)
    {
        LastFall = (killer, Battle?.Time ?? 0);"""),
])

edit(r'Ui\ArenaResult.cs', [
("""        if (r.Longest && r.Seconds > 120) wrap.AddChild(Style.Label("Your longest in any arena yet", Style.TextItalic, Style.Lead, Style.EmberHi, false, HorizontalAlignment.Center));""",
"""        if (r.Longest && r.Seconds > 120) wrap.AddChild(Style.Label("Your longest in any arena yet", Style.TextItalic, Style.Lead, Style.EmberHi, false, HorizontalAlignment.Center));
        // How it ended, and how near it came (docs/feel S-16: the end tells the run's story).
        var story = Story();
        if (story != "") wrap.AddChild(Style.Label(story, Style.TextItalic, Style.Body, r.Won ? Style.Ink : Style.BloodHi, true, HorizontalAlignment.Center));"""),
("""    static readonly string[] Numerals = ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII"];""",
"""    /// <summary>The run's ending in a line: who brought you down and when, and how near the end was.</summary>
    string Story()
    {
        string boss = r.Spec.BossName ?? SurvivorUnchained.Maps.MapOffers.People(r.Spec.People).BossName;
        double end = r.Spec.Minutes * 60;
        var parts = new System.Collections.Generic.List<string>();
        if (G.LastFall is var (killer, at) && G.Battle?.Player.Alive == false) parts.Add($"Brought down by {killer} at {Clock(at)}");
        if (!r.Won)
        {
            if (r.Seconds < end) { int m = (int)Math.Ceiling((end - r.Seconds) / 60); parts.Add($"{m} minute{(m == 1 ? "" : "s")} before {boss} would have come"); }
            else parts.Add($"{boss} still stands");
        }
        return string.Join(";  ", parts) + (parts.Count > 0 ? "." : "");
    }

    static readonly string[] Numerals = ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII"];"""),
])
print('done')
