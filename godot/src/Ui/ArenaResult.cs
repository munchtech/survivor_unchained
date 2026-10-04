using System;
using System.Linq;
using Godot;
using SurvivorUnchained.Arena;
using SurvivorUnchained.Content;
using SurvivorUnchained.Play;
using SurvivorUnchained.Rpg;

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
    readonly System.Collections.Generic.List<(Medallion M, double To, System.Func<double, string> Fmt, double At)> counts = new();
    double shownFor;

    public override void _Process(double delta)
    {
        base._Process(delta);
        shownFor += delta;
        foreach (var (m, to, fmt, at) in counts)
        {
            if (!IsInstanceValid(m)) continue;
            double k = System.Math.Clamp((shownFor - at) / 0.9, 0, 1);
            k = 1 - (1 - k) * (1 - k) * (1 - k);
            var t = fmt(to * k);
            if (t != m.Text) { m.Text = t; m.Arc = (float)k; m.QueueRedraw(); }
        }
    }

    protected override void Build()
    {
        HideHud();
        AddChild(new Backdrop(null, r.Won ? 0.82f : 0.9f));
        var wrap = Style.Centered(Style.V(14), new Vector2(1240, 900));
        AddChild(wrap);
        var tone = r.Won ? Style.EmberHi : Style.BloodHi;
        bool fell = G.Battle?.Player.Alive == false;
        // The verdict on a banner, the arena's name under it.
        var banner = Style.Panel(OrnateBox.Make(OrnateBox.Kind.Banner, 30, r.Won ? Style.Gold : Style.BloodHi),
            Style.Label(!r.Won ? "THE EMBER GUTTERS" : fell ? "WON, AND HELD TO THE LAST" : "THE ARENA IS WON", Style.Display, 40, r.Won ? new Color("#ffe6b8") : Style.BloodHi, false, HorizontalAlignment.Center));
        banner.SizeFlagsHorizontal = SizeFlags.ShrinkCenter;
        wrap.AddChild(banner);
        wrap.AddChild(Style.Label(r.Spec.Name, Style.TextItalic, Style.Lead, Style.GoldHi, false, HorizontalAlignment.Center));
        double beyond = r.Seconds - r.Spec.Minutes * 60;
        counts.Clear();
        var tally = Style.H(48,
            Stat("hourglass", r.Seconds, Clock, r.Won ? "survived" : "held out", 0.2),
            Stat("skull", r.Kills, x => $"{x:N0}", "slain", 0.45),
            Stat("flame", r.EmberLevel, x => $"{x:0}", "ember", 0.7));
        if (r.Won && beyond >= 1) tally.AddChild(Stat("moon", beyond, Clock, "past the dead of night", 0.95));
        tally.Alignment = BoxContainer.AlignmentMode.Center;
        wrap.AddChild(tally);
        if (r.Longest && r.Seconds > 120) wrap.AddChild(Style.Label("Your longest in any arena yet", Style.TextItalic, Style.Lead, Style.EmberHi, false, HorizontalAlignment.Center));
        // How it ended, and how near it came (docs/feel S-16: the end tells the run's story).
        var story = Story();
        if (story != "") wrap.AddChild(Style.Label(story, Style.TextItalic, Style.Body, r.Won ? Style.Ink : Style.BloodHi, true, HorizontalAlignment.Center));

        var two = Style.H(18);
        two.SizeFlagsVertical = SizeFlags.ExpandFill;
        wrap.AddChild(two);

        // What comes out, on a forged plate; what stays, on a slab gone to ash.
        var outv = Style.V(8, new Section("What you take out"));
        outv.AddChild(Line("book", $"{r.Xp:N0} experience" + (r.LevelsGained > 0 ? $"  ·  you are level {G.Journey.Ch.Level} now" : ""), r.LevelsGained > 0 ? Style.Good : Style.Ink));
        if (r.Gold > 0) outv.AddChild(Line("coin", $"{r.Gold:N0} gold", Style.GoldHi));
        // What the night left in the fist, for the Waystation's hands; on a fall, what spilled.
        if (r.Carried.Count > 0 || r.Spilled.Count > 0) outv.AddChild(Haul(r));
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
            outv.AddChild(Style.Label("What was discovered here can be learned for the day: from tomes, and from your calling as you grow.", Style.TextItalic, Style.Caption, Style.InkDim, true));
        two.AddChild(Card(outv));

        // What stays.
        var stay = Style.V(8, new Section("What stays in the arena"));
        if (G.Battle is { } b)
        {
            // The build the ember made, as grey medallions: it does not leave with you.
            var ash = new GridContainer { Columns = 5, MouseFilter = MouseFilterEnum.Ignore };
            ash.AddThemeConstantOverride("h_separation", 10);
            ash.AddThemeConstantOverride("v_separation", 10);
            Control Faded(string glyph, string name)
            {
                var mc = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore };
                mc.AddChild(new Medallion(64, "", glyph) { Ring = Style.InkFaint, Ink = Style.InkDim, Core = new Color("#16131a") });
                var v = Style.V(2, mc, Style.Label(name, Style.Ui, Style.Caption, Style.InkDim, true, HorizontalAlignment.Center));
                v.CustomMinimumSize = new Vector2(100, 0);
                return v;
            }
            foreach (var w in b.Weapons) ash.AddChild(Faded(w.Evolution?.Art ?? w.Def.Art, $"{w.Evolution?.Name ?? w.Def.Name} {Numeral(w.Rank)}"));
            foreach (var (id, rank) in b.Boons)
                if (rank > 0 && Boons.Find(id) is { } bd) ash.AddChild(Faded(bd.Icon, bd.Max > 1 ? $"{bd.Name} {Numeral(rank)}" : bd.Name));
            stay.AddChild(ash);
        }
        stay.AddChild(Style.Label("The ember goes out with the arena. The next one starts from nothing.", Style.TextItalic, Style.Caption, Style.InkFaint, true));
        var stayCard = Card(stay, Style.Slab(18));
        stayCard.Modulate = new Color(1, 1, 1, 0.85f);
        two.AddChild(stayCard);

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

    static string EvolutionName(string id) => Weapons.All.Values.SelectMany(w => w.Evolutions).FirstOrDefault(e => e.Id == id)?.Name ?? id;

    /// <summary>The run's ending in a line: who brought you down and when, and how near the end was.</summary>
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

    static readonly string[] Numerals = ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII"];
    static string Numeral(int n) => n >= 0 && n < Numerals.Length ? Numerals[n] : n.ToString();

    /// <summary>A number of the night on a medallion, counting up with its ring filling, its name under it.</summary>
    Control Stat(string glyph, double value, System.Func<double, string> fmt, string label, double at)
    {
        var m = new Medallion(150, fmt(0)) { Ring = r.Won ? Style.Gold : Style.InkDim, ArcColor = r.Won ? Style.Ember : Style.BloodHi, Ink = Style.GoldHi };
        counts.Add((m, value, fmt, at));
        var mc = new CenterContainer { MouseFilter = MouseFilterEnum.Ignore };
        mc.AddChild(m);
        var name = Style.H(6, Glyphs.Icon(glyph, 16, Style.Gold), Style.Label(label.ToUpperInvariant(), Style.UiHeavy, Style.Caption, Style.Gold));
        name.Alignment = BoxContainer.AlignmentMode.Center;
        return Style.V(4, mc, name);
    }

    static Control Line(string glyph, string text, Color c) => Style.H(8, Glyphs.Icon(glyph, 20, c), Style.Label(text, Style.UiBold, Style.Body, c));

    /// <summary>What the night left in the fist (ember shards, the people's own), as the things
    /// themselves, for the Waystation's hands; on a fall, what spilled, greyed beside it
    /// (docs/CRAFTING_DESIGN.md 6.1: the run's last decision, shown as what it cost).</summary>
    static Control Haul(ArenaResult r)
    {
        static Control Things(System.Collections.Generic.Dictionary<string, int> d, bool lost)
        {
            var h = Style.H(Style.Gap2);
            foreach (var (m, n) in d)
            {
                var def = Rpg.Items.Get(m);
                var slot = ItemViews.Slot(new Rpg.ItemInstance { Def = m, Qty = n, Rarity = def.Rarity }, 60);
                slot.MouseFilter = MouseFilterEnum.Ignore;
                var name = Style.Label(lost ? (def.Plural ?? def.Name.ToLowerInvariant()) : (n == 1 ? def.Name.ToLowerInvariant() : def.Plural ?? def.Name.ToLowerInvariant()),
                    Style.Ui, Style.Caption, lost ? Style.InkFaint : Style.Ink, true, HorizontalAlignment.Center);
                var cell = Style.V(2, slot, name);
                cell.CustomMinimumSize = new Vector2(76, 0);
                if (lost) cell.Modulate = new Color(1, 1, 1, 0.45f);
                h.AddChild(cell);
            }
            return h;
        }
        var v = Style.V(4);
        var row = Style.H(Style.Gap4);
        if (r.Carried.Count > 0)
            row.AddChild(Style.V(4, Style.Label("CARRIED OUT, FOR THE WAYSTATION'S HANDS", Style.UiHeavy, Style.Badge, Style.EmberHi), Things(r.Carried, false)));
        if (r.Spilled.Count > 0)
            row.AddChild(Style.V(4, Style.Label("SPILLED WHEN YOU FELL", Style.UiHeavy, Style.Badge, Style.InkDim), Things(r.Spilled, true)));
        v.AddChild(row);
        return v;
    }

    static Control Skill(string id, bool fresh)
    {
        var (icon, name, what) = Weapons.All.TryGetValue(id, out var w) ? (w.Art, w.Name, "combat skill")
            : Boons.Find(id) is { } bd ? (bd.Icon, bd.Name, "passive skill") : ("scroll", id, "");
        var col = fresh ? new Color("#b8a8d8") : Style.InkDim;
        return Style.H(8, Glyphs.Icon(icon, 22, col), Style.V(0, Style.Label(name, Style.UiBold, Style.Small, col), Style.Label(what, Style.TextItalic, Style.Caption, Style.InkDim)));
    }

    static Control Card(Control inner, StyleBox? box = null)
    {
        var p = Style.Panel(box ?? Style.Plate(20), Style.Scroll(inner));
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
