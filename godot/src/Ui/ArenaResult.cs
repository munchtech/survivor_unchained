using System.Linq;
using Godot;
using SurvivorUnchained.Arena;
using SurvivorUnchained.Content;
using SurvivorUnchained.Play;

namespace SurvivorUnchained.Ui;

/// <summary>An arena over (Arena/Arena.cs): how long, how many, and what
/// comes out of it (experience, gold, skills discovered) set against what
/// stays behind (the build the ember made). Then back to the story. The
/// end of half an hour is what the player remembers of it (the peak-end
/// rule), so the tally counts up rather than appearing, one after another.</summary>
public partial class ArenaResultScreen : Overlay
{
    readonly ArenaResult r;
    public override string Kind => "arena";
    public override bool Dismissable => false;

    public ArenaResultScreen(Game g, ArenaResult result) : base(g) => r = result;

    static string Clock(double s) => $"{(int)(s / 60)}:{(int)(s % 60):00}";

    // The numbers counting up: each label, its final value, how it is written, when it starts.
    readonly System.Collections.Generic.List<(Label L, double To, System.Func<double, string> Fmt, double At)> counts = new();
    double shownFor;

    public override void _Process(double delta)
    {
        base._Process(delta);
        shownFor += delta;
        foreach (var (l, to, fmt, at) in counts)
        {
            if (!IsInstanceValid(l)) continue;
            double k = System.Math.Clamp((shownFor - at) / 0.9, 0, 1);
            k = 1 - (1 - k) * (1 - k) * (1 - k);
            l.Text = fmt(to * k);
        }
    }

    protected override void Build()
    {
        AddChild(Style.Scrim(null, r.Won ? 0.62f : 0.74f));
        var wrap = Style.Centered(Style.V(12), new Vector2(1060, 720));
        AddChild(wrap);
        var tone = r.Won ? Style.EmberHi : Style.BloodHi;
        bool fell = G.Battle?.Player.Alive == false;
        wrap.AddChild(Style.Label(!r.Won ? "THE EMBER GUTTERS" : fell ? "WON, AND HELD TO THE LAST" : "THE ARENA IS WON", Style.UiHeavy, 15, tone, false, HorizontalAlignment.Center));
        wrap.AddChild(Style.Label(r.Spec.Name, Style.Display, 48, Style.GoldHi, false, HorizontalAlignment.Center));
        wrap.AddChild(Style.Flourish());
        double beyond = r.Seconds - r.Spec.Minutes * 60;
        counts.Clear();
        var tally = Style.H(36,
            Stat("hourglass", r.Seconds, Clock, r.Won ? "survived" : "held out", 0.2),
            Stat("skull", r.Kills, x => $"{x:N0}", "slain", 0.45),
            Stat("flame", r.EmberLevel, x => $"{x:0}", "ember", 0.7));
        if (r.Won && beyond >= 1) tally.AddChild(Stat("moon", beyond, Clock, "past the half hour", 0.95));
        tally.Alignment = BoxContainer.AlignmentMode.Center;
        wrap.AddChild(tally);
        if (r.Longest && r.Seconds > 120) wrap.AddChild(Style.Label("Your longest in any arena yet", Style.TextItalic, Style.Lead, Style.EmberHi, false, HorizontalAlignment.Center));

        var two = Style.H(18);
        two.SizeFlagsVertical = SizeFlags.ExpandFill;
        wrap.AddChild(two);

        // What comes out.
        var outv = Style.V(8, Style.SubLabel("What you take out"));
        outv.AddChild(Line("book", $"{r.Xp:N0} experience" + (r.LevelsGained > 0 ? $"  ·  you are level {G.Journey.Ch.Level} now" : ""), r.LevelsGained > 0 ? Style.Good : Style.Ink));
        if (r.Gold > 0) outv.AddChild(Line("coin", $"{r.Gold:N0} gold", Style.GoldHi));
        if (r.Tome is { } tome) outv.AddChild(Line("book", $"A tome: {Weapons.All[tome].Name}", new Color("#b8a8d8")));
        if (r.Taught is { } taught) outv.AddChild(Line("book", $"Your calling taught you {Weapons.All[taught].Name}", Style.Good));
        outv.AddChild(Style.Rule());
        outv.AddChild(Style.SubLabel(r.Discovered.Count > 0 ? "Discovered" : "Nothing new discovered"));
        foreach (var id in r.Discovered) outv.AddChild(Skill(id, true));
        if (r.Discovered.Count > 0)
            outv.AddChild(Style.Label("What was discovered here can be learned for the day: from tomes, and from your calling as you grow.", Style.TextItalic, Style.Caption, Style.InkDim, true));
        two.AddChild(Card(outv));

        // What stays.
        var stay = Style.V(8, Style.SubLabel("What stays in the arena"));
        if (G.Battle is { } b)
        {
            foreach (var w in b.Weapons)
                stay.AddChild(Style.H(8, Glyphs.Icon(w.Evolution?.Art ?? w.Def.Art, 20, Style.InkDim),
                    Style.Label($"{w.Evolution?.Name ?? w.Def.Name}  {Numeral(w.Rank)}", Style.Ui, Style.Small, Style.InkDim)));
            foreach (var (id, rank) in b.Boons)
                if (rank > 0 && Boons.Find(id) is { } bd)
                    stay.AddChild(Style.H(8, Glyphs.Icon(bd.Icon, 20, Style.InkDim), Style.Label(bd.Max > 1 ? $"{bd.Name}  {Numeral(rank)}" : bd.Name, Style.Ui, Style.Small, Style.InkDim)));
        }
        stay.AddChild(Style.Label("The ember goes out with the arena. The next one starts from nothing.", Style.TextItalic, Style.Caption, Style.InkFaint, true));
        two.AddChild(Card(stay));

        string after = r.Spec.Story
            ? r.Won ? "The story goes on." : "The story goes on without the win. The Wayfinder will let you take this fight again."
            : r.Won ? "The Wayfinder will want to hear of it." : "The Wayfinder's table will have other maps.";
        wrap.AddChild(Style.Label(after, Style.TextItalic, Style.Body, Style.Ink, true, HorizontalAlignment.Center));
        var go = Style.Button("", () => G.LeaveArena(r), true);
        var gr = Style.H(8, Style.Prompt(Act.Confirm), Style.Label("Back to the road", Style.UiBold, Style.Body, new Color("#ffe4b0")));
        gr.MouseFilter = MouseFilterEnum.Ignore;
        gr.Position = new Vector2(16, 7);
        go.AddChild(gr);
        go.CustomMinimumSize = new Vector2(gr.GetCombinedMinimumSize().X + 32, 42);
        var acts = Style.H(12, go);
        acts.Alignment = BoxContainer.AlignmentMode.Center;
        wrap.AddChild(acts);
    }

    static readonly string[] Numerals = ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII"];
    static string Numeral(int n) => n >= 0 && n < Numerals.Length ? Numerals[n] : n.ToString();

    Control Stat(string glyph, double value, System.Func<double, string> fmt, string label, double at)
    {
        var l = Style.Label(fmt(0), Style.Display, 34, Style.GoldHi);
        counts.Add((l, value, fmt, at));
        var h = Style.H(8, Glyphs.Icon(glyph, 24, Style.GoldHi), l);
        h.Alignment = BoxContainer.AlignmentMode.Center;
        return Style.V(0, h, Style.Label(label.ToUpperInvariant(), Style.UiHeavy, Style.Badge, Style.Gold, false, HorizontalAlignment.Center));
    }

    static Control Line(string glyph, string text, Color c) => Style.H(8, Glyphs.Icon(glyph, 20, c), Style.Label(text, Style.UiBold, Style.Body, c));

    static Control Skill(string id, bool fresh)
    {
        var (icon, name, what) = Weapons.All.TryGetValue(id, out var w) ? (w.Art, w.Name, "combat skill")
            : Boons.Find(id) is { } bd ? (bd.Icon, bd.Name, "passive skill") : ("scroll", id, "");
        var col = fresh ? new Color("#b8a8d8") : Style.InkDim;
        return Style.H(8, Glyphs.Icon(icon, 22, col), Style.V(0, Style.Label(name, Style.UiBold, Style.Small, col), Style.Label(what, Style.TextItalic, Style.Caption, Style.InkDim)));
    }

    static Control Card(Control inner)
    {
        var p = Style.Panel(Style.Plate(18), Style.Scroll(inner));
        p.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        inner.SizeFlagsHorizontal = SizeFlags.ExpandFill;
        return p;
    }

    public override bool Key(Act a)
    {
        if (a == Act.Confirm) { G.LeaveArena(r); return true; }
        // Nothing else leaves it: the arena's end is read, not skipped by a stray key.
        return a is not (Act.Up or Act.Down or Act.Left or Act.Right);
    }
}
