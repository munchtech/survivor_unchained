from ed import sub
sub('src/Ui/ItemViews.cs', [
("""                var text = Style.Label(x.Def!.Text(x.Tier), Style.UiBold, Style.Caption, x.Def.Kindled != null ? Style.EmberHi : new Color("#9ad8ff"), true);
                if (x.Def.Kindled != null || x.Def.Grants != null) return (Control)text;""",
"""                var text = Style.Label(x.Def!.Text(x.Tier), Style.UiBold, Style.Caption, x.Def.Kindled != null ? Style.EmberHi : x.Def.Slurry ? SlurryGreen : new Color("#9ad8ff"), true);
                if (x.Def.Kindled != null || x.Def.Grants != null || x.Def.Slurry) return (Control)text;"""),
("""        ["greymuzzle_fang"] = "The Pack knows it by sight.",""",
"""        ["greymuzzle_fang"] = "The Pack knows it by sight.",
        ["slurried"] = "Steeped: green-black veins run through it. It is set for good.","""),
("""    public static readonly Dictionary<string, string> TagLines = new()""",
"""    /// <summary>The slurry's sick green: what it put in a piece, and the veins.</summary>
    public static readonly Color SlurryGreen = new("#a8e08a");

    public static readonly Dictionary<string, string> TagLines = new()"""),
])
sub('src/Ui/Forge.cs', [
("""    static bool Plain(AffixDef? d) => d != null && d.Kindled == null && d.Grants == null;""",
"""    static bool Plain(AffixDef? d) => d != null && d.Kindled == null && d.Grants == null && !d.Slurry;"""),
("""        bool coal = ad?.Kindled != null, skill = ad?.Grants != null, on = k == seam;""",
"""        bool coal = ad?.Kindled != null, skill = ad?.Grants != null, slurry = ad?.Slurry == true, on = k == seam;"""),
("""        var badge = new GradeBadge(open ? GradeBadge.Mark.Open : coal ? GradeBadge.Mark.Coal : skill ? GradeBadge.Mark.Skill : GradeBadge.Mark.Grade, a?.Tier ?? 0, cap);""",
"""        var badge = new GradeBadge(open ? GradeBadge.Mark.Open : coal ? GradeBadge.Mark.Coal : skill ? GradeBadge.Mark.Skill : slurry ? GradeBadge.Mark.Slurry : GradeBadge.Mark.Grade, a?.Tier ?? 0, cap);"""),
("""            : skill ? $"{ad!.Name}: a worn skill, it has no grades\"""",
"""            : skill ? $"{ad!.Name}: a worn skill, it has no grades"
            : slurry ? $"{ad!.Name}: the slurry's, past its seams; it has no grades\""""),
("""        words.AddChild(Style.Label(title, Style.UiBold, Style.Body, open ? Style.GoldHi : coal ? Style.EmberHi : Style.Ink, true));""",
"""        words.AddChild(Style.Label(title, Style.UiBold, Style.Body, open ? Style.GoldHi : coal ? Style.EmberHi : slurry ? ItemViews.SlurryGreen : Style.Ink, true));"""),
("""    public enum Mark { Grade, Coal, Skill, Open }""",
"""    public enum Mark { Grade, Coal, Skill, Open, Slurry }"""),
("""        var col = mark switch { Mark.Coal => Style.Ember, Mark.Open => Style.GoldDim, Mark.Skill => Style.Day, _ => Style.RarityOf(tier) };""",
"""        var col = mark switch { Mark.Coal => Style.Ember, Mark.Open => Style.GoldDim, Mark.Skill => Style.Day, Mark.Slurry => ItemViews.SlurryGreen, _ => Style.RarityOf(tier) };"""),
("""        if (mark is Mark.Coal or Mark.Skill)
        {
            DrawRect(r.Grow(-2), col with { A = 0.12f });
            var tex = Glyphs.Texture(mark == Mark.Coal ? "flame" : "book", 30, col);""",
"""        if (mark is Mark.Coal or Mark.Skill or Mark.Slurry)
        {
            DrawRect(r.Grow(-2), col with { A = 0.12f });
            var tex = Glyphs.Texture(mark switch { Mark.Coal => "flame", Mark.Slurry => "drop", _ => "book" }, 30, col);"""),
])
