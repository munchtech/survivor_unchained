using System.Linq;
using Godot;
using SurvivorUnchained.Arena;
using SurvivorUnchained.Content;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;

namespace SurvivorUnchained.Ui;

/// <summary>An arena over (Arena/Arena.cs): how long, how many, and what
/// comes out of it (experience, gold, skills discovered) set against what
/// stays behind (the build the ember made). Then back to the story.</summary>
public partial class ArenaResultScreen : Overlay
{
    readonly ArenaResult r;
    public override string Kind => "arena";
    public override bool Dismissable => false;

    public ArenaResultScreen(Game g, ArenaResult result) : base(g) => r = result;

    static string Clock(double s) => $"{(int)(s / 60)}:{(int)(s % 60):00}";

    protected override void Build()
    {
        AddChild(Style.Scrim(null, r.Won ? 0.62f : 0.74f));
        var wrap = Style.Centered(Style.V(12), new Vector2(1060, 720));
        AddChild(wrap);
        var tone = r.Won ? Style.EmberHi : Style.BloodHi;
        bool fell = G.Battle?.Player.Alive == false;
        wrap.AddChild(Style.Label(!r.Won ? "THE EMBER GUTTERS" : fell ? "WON, AND HELD TO THE LAST" : "THE ARENA IS WON", Style.UiHeavy, 15, tone, false, HorizontalAlignment.Center));
        wrap.AddChild(Style.Label(r.Spec.Name, Style.Display, 48, Style.GoldHi, false, HorizontalAlignment.Center));
        double beyond = r.Seconds - r.Spec.Minutes * 60;
        var tally = Style.H(28,
            Stat("hourglass", Clock(r.Seconds), r.Won ? "survived" : "held out"),
            Stat("skull", $"{r.Kills:N0}", "slain"),
            Stat("flame", $"{r.EmberLevel}", "ember"));
        if (r.Won && beyond >= 1) tally.AddChild(Stat("moon", Clock(beyond), "past the half hour"));
        tally.Alignment = BoxContainer.AlignmentMode.Center;
        wrap.AddChild(tally);
        if (r.Longest && r.Seconds > 120) wrap.AddChild(Style.Label("Your longest in any arena yet", Style.TextItalic, 15, Style.EmberHi, false, HorizontalAlignment.Center));

        var two = Style.H(18);
        two.SizeFlagsVertical = SizeFlags.ExpandFill;
        wrap.AddChild(two);

        // What comes out.
        var outv = Style.V(8, Style.SubLabel("What you take out"));
        outv.AddChild(Line("book", $"{r.Xp:N0} experience" + (r.LevelsGained > 0 ? $"  ·  level {G.Journey.Ch.Level}" : ""), r.LevelsGained > 0 ? Style.Good : Style.Ink));
        if (r.Gold > 0) outv.AddChild(Line("coin", $"{r.Gold:N0} gold", Style.GoldHi));
        // A tome won is the survivor's to write: one of what burned here.
        if (r.Inscribed is { } tome) outv.AddChild(Line("book", $"A tome: {Weapons.All[tome].Name}", new Color("#b8a8d8")));
        else if (r.TomeChoices.Count > 0)
        {
            outv.AddChild(Line("book", "A blank tome: write it with one of what burned", new Color("#b8a8d8")));
            var pick = Style.H(8);
            foreach (var id in r.TomeChoices)
            {
                var w = Weapons.All[id];
                var btn = Style.Button(w.Name, () => { if (Arenas.Inscribe(G.Journey, r, id)) Refresh(); }, false, true);
                btn.TooltipText = $"{w.Description} By day it asks {SkillBook.Need} {SkillBook.Attribute(id)}.";
                pick.AddChild(btn);
            }
            outv.AddChild(pick);
        }
        foreach (var made in r.Recorded)
            outv.AddChild(Line("scroll", made.StartsWith("evo:") ? $"In the codex: {EvolutionName(made[4..])}" : $"In the codex: the union {Unions.Find(made[6..])?.Name}", Style.GoldHi));
        if (r.Taught is { } taught) outv.AddChild(Line("book", $"Your calling taught you {Weapons.All[taught].Name}", Style.Good));
        outv.AddChild(Style.Rule());
        outv.AddChild(Style.SubLabel(r.Discovered.Count > 0 ? "Discovered" : "Nothing new discovered"));
        foreach (var id in r.Discovered) outv.AddChild(Skill(id, true));
        if (r.Discovered.Count > 0)
            outv.AddChild(Style.Label("What was discovered here can be learned for the day: from tomes, and from your calling as you grow.", Style.TextItalic, 14, Style.InkDim, true));
        two.AddChild(Card(outv));

        // What stays.
        var stay = Style.V(8, Style.SubLabel("What stays in the arena"));
        if (G.Battle is { } b)
        {
            foreach (var w in b.Weapons)
                stay.AddChild(Style.H(8, Glyphs.Icon(w.Evolution?.Art ?? w.Def.Art, 20, Style.InkDim),
                    Style.Label($"{w.Evolution?.Name ?? w.Def.Name}  {Numeral(w.Rank)}", Style.Ui, 15, Style.InkDim)));
            foreach (var (id, rank) in b.Boons)
                if (rank > 0 && Boons.Find(id) is { } bd)
                    stay.AddChild(Style.H(8, Glyphs.Icon(bd.Icon, 20, Style.InkDim), Style.Label(bd.Max > 1 ? $"{bd.Name}  {Numeral(rank)}" : bd.Name, Style.Ui, 15, Style.InkDim)));
        }
        stay.AddChild(Style.Label("The ember goes out with the arena. The next one starts from nothing.", Style.TextItalic, 14, Style.InkFaint, true));
        two.AddChild(Card(stay));

        string after = r.Spec.Story
            ? r.Won ? "The story goes on." : "The story goes on without the win. The Wayfinder will let you take this fight again."
            : r.Won ? "The Wayfinder will want to hear of it." : "The Wayfinder's table will have other maps.";
        wrap.AddChild(Style.Label(after, Style.TextItalic, 17, Style.Ink, true, HorizontalAlignment.Center));
        var acts = Style.H(12, Style.Button("Back to the road", () => G.LeaveArena(r), true));
        acts.Alignment = BoxContainer.AlignmentMode.Center;
        wrap.AddChild(acts);
    }

    static string EvolutionName(string id) => Weapons.All.Values.SelectMany(w => w.Evolutions).FirstOrDefault(e => e.Id == id)?.Name ?? id;

    static readonly string[] Numerals = ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII"];
    static string Numeral(int n) => n >= 0 && n < Numerals.Length ? Numerals[n] : n.ToString();

    static Control Stat(string glyph, string value, string label) =>
        Style.V(0, Style.H(6, Glyphs.Icon(glyph, 20, Style.GoldHi), Style.Label(value, Style.Display, 30, Style.GoldHi)),
            Style.Label(label.ToUpperInvariant(), Style.UiHeavy, 11, Style.Gold, false, HorizontalAlignment.Center));

    static Control Line(string glyph, string text, Color c) => Style.H(8, Glyphs.Icon(glyph, 20, c), Style.Label(text, Style.UiBold, 17, c));

    static Control Skill(string id, bool fresh)
    {
        var (icon, name, what) = Weapons.All.TryGetValue(id, out var w) ? (w.Art, w.Name, "combat skill")
            : Boons.Find(id) is { } bd ? (bd.Icon, bd.Name, "passive skill") : ("scroll", id, "");
        var col = fresh ? new Color("#b8a8d8") : Style.InkDim;
        return Style.H(8, Glyphs.Icon(icon, 22, col), Style.V(0, Style.Label(name, Style.UiBold, 16, col), Style.Label(what, Style.TextItalic, 13, Style.InkDim)));
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
        return true;
    }
}
